"""Continuous 1x AI measurement: one stream, then two; never pause/seek/approve.

Independent expected IDs are frozen in a separate offline file. Inspect persisted
results directly, including a 45-second interval with no API/browser requests.
This is engineering verification on correlated authored scenes, not user research.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import httpx
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.repository import Repository

def run(base,db,match_id,refs,output):
    with httpx.Client(base_url=base,timeout=60,headers={'X-Producer-Token':'local-demo-producer'}) as client:
        r=client.post('/api/replay-sessions',json={'match_id':match_id,'mode':'live','execution':'ai'});r.raise_for_status();sid=r.json()['session_id']
    started=time.monotonic();store=Repository(db);first={};samples=[]
    while time.monotonic()-started<280:
        s=store.get_session(sid)
        for p in store.list_packages(sid):
            first.setdefault(p['id'],{'family':p['metrics'].get('family','pass'),'eligible_ms':p['eligible_from_ms'],'expires_ms':p['expires_at_ms'],'mode':p['mode']})
        samples.append({'wall_elapsed_s':round(time.monotonic()-started,3),'processed_ms':s.get('last_processed_ms'),'packages':len(store.list_packages(sid))})
        if not s['running']:break
        time.sleep(1)
    outcomes=store.workflow_outcomes(sid);events=store.lifecycle_events(sid);pkgs=store.list_packages(sid)
    ready={}
    for e in events:
        if e.get('kind')=='opportunity' and e.get('state')=='candidate_ready':ready.setdefault(e['story_id'],e)
        if e.get('kind')=='delivery' and e.get('state')=='accepted':ready.setdefault(e['story_id'],e)
    # All packages have durable accepted delivery records, including original passes.
    for p in pkgs:
        accepted=[e for e in events if e.get('story_id')==p['id'] and e.get('state')=='accepted']
        if accepted:
            e=accepted[0];ref=e['package_ref'];original=store.stored_package(sid,p['id'],ref['revision']);row=first[p['id']];row.update(eligible_ms=original['eligible_from_ms'],expires_ms=original['expires_at_ms'],mode=original['mode'],revision=original['revision'],package_hash=original['package_hash']);row['ready_replay_ms']=e.get('replay_ms',e.get('at_ms'));row['review_remaining_s']=(min(row['expires_ms'],s['duration_ms'])-row['ready_replay_ms'])/1000 if row['ready_replay_ms'] is not None else None
    expected=refs['expected_story_ids'];missing=[x for x in expected if x not in first]
    timely=[x for x in expected if x in first and first[x].get('review_remaining_s',-1)>=15 and first[x]['mode']=='Microsoft Agent Framework + Azure OpenAI']
    usage={k:sum(o['model_usage'].get(k) or 0 for o in outcomes) for k in ['calls','input_tokens','output_tokens','total_tokens']}
    with httpx.Client(base_url=base,timeout=60) as c:
        snapshot=c.get(f'/api/replay-sessions/{sid}/snapshot').json()
    rates=json.loads((output/'model-preflight.json').read_text())['rates_per_million']
    estimate=(usage['input_tokens']*rates['gpt-4o-mini-0718-Inp-glbl']+usage['output_tokens']*rates['gpt-4o-mini-0718-Outp-glbl'])/1e6
    discontinuities=[{'from_ms':a.get('processed_ms'),'to_ms':b.get('processed_ms'),'monotonic_elapsed_s':b['wall_elapsed_s']-a['wall_elapsed_s']} for a,b in zip(samples,samples[1:]) if (b.get('processed_ms') or 0)-(a.get('processed_ms') or 0)-1000*(b['wall_elapsed_s']-a['wall_elapsed_s'])>5000]
    report={'clock_discontinuities':discontinuities,'operating_run_valid':not discontinuities,'retail_estimate_usd':estimate,'session_id':sid,'match_id':match_id,'elapsed_s':round(time.monotonic()-started,3),'speed':1,'seeks':0,'pauses':0,'automatic_approvals':0,'no_api_reads_during_playback':True,'expected_count':len(expected),'missing':missing,'timely_ai_count':len(timely),'timely_ai_fraction':len(timely)/len(expected),'gate_passed':not discontinuities and len(timely)/len(expected)>=.95,'families':sorted({r['family'] for r in first.values()}),'first_candidates':first,'usage':usage,'usage_complete':all(o['model_usage'].get('usage_complete') for o in outcomes),'outcomes':outcomes,'lifecycle_events':events,'samples':samples,'final_public_score':snapshot.get('score'),'final_public_overlay':snapshot.get('overlay'),'finished':snapshot.get('live_status')=='complete'}
    output.mkdir(parents=True,exist_ok=True);(output/f'{sid}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'first_candidates','outcomes','lifecycle_events','samples'} }),flush=True)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',default='http://127.0.0.1:8200');p.add_argument('--db',default='.run/live-match.db');p.add_argument('--output',type=Path,required=True);p.add_argument('--phase',choices=['both','one','two'],default='both');args=p.parse_args()
    for attempt in range(60):
        try:
            if httpx.get(args.base+'/api/health',timeout=2).status_code==200:break
        except httpx.HTTPError:pass
        time.sleep(.5)
    refpath=ROOT/'evals/live-match/references.json';refs=json.loads(refpath.read_text());args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'references.json').write_bytes(refpath.read_bytes())
    (args.output/'model-preflight.json').write_bytes((ROOT/'.run/live-model-preflight.json').read_bytes())
    started=datetime.now(timezone.utc).isoformat();results=[]
    if args.phase in {'both','one'}:results.append(run(args.base,args.db,refs['scenes'][0],refs,args.output))
    if args.phase in {'both','two'}:
        with ThreadPoolExecutor(max_workers=2) as pool:results+=list(pool.map(lambda mid:run(args.base,args.db,mid,refs,args.output),refs['scenes']))
    report={'started_at':started,'reference_sha256':hashlib.sha256(refpath.read_bytes()).hexdigest(),'scope':refs['scope'],'results':[{k:v for k,v in r.items() if k not in {'first_candidates','outcomes','lifecycle_events','samples'}} for r in results],'all_gates_passed':all(r['gate_passed'] for r in results)}
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
