"""Real elapsed 1x polling, two isolated sessions; no seeks or model calls.

The authored opportunity schedule is independent of production metric functions.
Consumer-ready time conservatively adds HTTP duration to source snapshot clock.
This measures local template load, not model latency or production P95.
"""
import argparse
import hashlib
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import time
import httpx

ROOT=Path(__file__).resolve().parents[1]


def expected(correction):
    rows=[]
    def add(family,subject,ready,ttl=30000):rows.append({'family':family,'story_id':f'story-{family}-{subject}','evidence_ready_ms':ready,'expires_at_ms':ready+ttl})
    for t in range(15000,240001,15000):add('possession',str(t),t,15000)
    for n,t in enumerate([16200,84200,164200,214300],1):add('pass',str(n),t)
    # Legacy pass IDs are story-pass-1, not story-pass-pass-1.
    for subject,times in [('loose-1',[30000,33000]),('change-1',[50000,53000]),('change-2',[70000,73000]),('e-pos-74000',[74000,77000]),('e-pos-154000',[154000,157000]),('e-pos-204000',[204000,207000]),('restart-1',[110000,113000]),('recovery-3',[145000,148000])]:
        for t in times:add('recovery',subject,t)
    for subject,times in [('attempt-1',[46000]),('attempt-2',[101000,102000,104000]+([135000] if correction else [])),('attempt-3',[186000])]:
        for t in times:add('shot',subject,t)
    add('goal','goal-1',104000)
    return rows


def run_session(base,correction):
    headers={'X-Producer-Token':'local-demo-producer'}
    with httpx.Client(base_url=base,headers=headers,timeout=60) as c:
        r=c.post('/api/replay-sessions',json={'match_id':f'match-0c0a00000000000{2 if correction else 1}'});r.raise_for_status();sid=r.json()['session_id'];path=f'/api/replay-sessions/{sid}'
        c.post(path+'/control',json={'action':'start'}).raise_for_status()
        observations={};polls=[];errors=[];started=time.monotonic()
        while time.monotonic()-started<247:
            before=time.monotonic()
            try:
                response=c.get(path+'/snapshot');response.raise_for_status();snap=response.json()
                duration_ms=(time.monotonic()-before)*1000
                for s in snap['stories']:
                    key=(s['id'],s['eligible_from_ms'])
                    observations.setdefault(key,{'candidate_at_ms':min(240000,snap['clock_ms']+duration_ms),'http_duration_ms':duration_ms,
                                                 'revision':s['revision'],'status':s['status'],'expires_at_ms':s['expires_at_ms'],'family':s.get('family','pass')})
                polls.append(duration_ms)
                if snap['clock_ms']>=240000:break
            except Exception as exc:errors.append(type(exc).__name__)
            time.sleep(.75)
        diagnostics=c.get(path+'/diagnostics').json()
        rows=[]
        for opportunity in expected(correction):
            found=observations.get((opportunity['story_id'],opportunity['evidence_ready_ms']))
            ready=found['candidate_at_ms'] if found else None
            rows.append({**opportunity,'candidate_at_ms':ready,'queue_wait_ms':max(0,ready-opportunity['evidence_ready_ms']) if ready is not None else None,
                         'review_time_available_ms':max(0,opportunity['expires_at_ms']-ready) if ready is not None else 0,
                         'target_met':ready is not None and opportunity['expires_at_ms']-ready>=10000,
                         'found':bool(found)})
        states=[e for e in diagnostics['lifecycle_events'] if e['kind']=='opportunity' and e['state'] in {'capacity_deferred','expired_unscheduled','expired_archive_candidate'}]
        actual_keys=set(observations);expected_keys={(r['story_id'],r['evidence_ready_ms']) for r in rows}
        # Include every observed opportunity even if the authored schedule missed
        # one. Missing timing must never disappear from the acceptance denominator.
        unexpected=[]
        for id,t in sorted(actual_keys-expected_keys):
            found=observations[(id,t)];ready=found['candidate_at_ms'];expiry=found['expires_at_ms']
            extra={'story_id':id,'family':found['family'],'evidence_ready_ms':t,'expires_at_ms':expiry,
                   'candidate_at_ms':ready,'queue_wait_ms':max(0,ready-t),'review_time_available_ms':max(0,expiry-ready),
                   'target_met':expiry-ready>=10000,'found':True,'unplanned':True}
            rows.append(extra);unexpected.append(extra)
        return {'session_id':sid,'correction':correction,'elapsed_s':time.monotonic()-started,'polls':len(polls),'http_max_ms':max(polls,default=0),
                'opportunities':rows,'unexpected_observed_opportunities':unexpected,
                'deferrals_and_expiry':states,'errors':errors,'usage':[o['model_usage'] for o in diagnostics['workflow_outcomes']]}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--base',default='http://127.0.0.1:8100');args=parser.parse_args()
    fingerprints={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for pattern in ['engine/*.py','services/api/*.py','apps/web/components/*.tsx','apps/web/lib/*.ts','apps/web/hooks/*.ts','apps/web/app/page.tsx'] for p in ROOT.glob(pattern)}
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda correction:run_session(args.base,correction),[False,True]))
    opportunities=[r for result in results for r in result['opportunities']]
    report={'source_sha256':fingerprints,'mode':'local deterministic template','speed':1,'simultaneous_sessions':2,'continuous':True,
            'scope':'Full 4-minute replay. Poll consumer; conservative readiness upper bound, no producer approval timing. No model/cloud claims.',
            'missing_telemetry':['Exact durable ingestion timestamp','Human review duration','Browser first-paint for every opportunity','Provider/model latency (zero calls)'],
            'attempted':len(opportunities),'found':sum(r['found'] for r in opportunities),'target_met':sum(r['target_met'] for r in opportunities),
            'target_fraction':sum(r['target_met'] for r in opportunities)/len(opportunities),'results':results}
    out=ROOT/'evals/match-coverage/continuous-play.json';out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'results','source_sha256'}},indent=2))
    if report['target_fraction']<.9 or report['found']!=report['attempted']:raise SystemExit(1)

if __name__=='__main__':main()
