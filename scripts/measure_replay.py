"""Small continuous-1x replay timing check, without automatic publication.

Default uses local templates. --cloud explicitly uses the private QA access file
and starts at most two billable investigations (six-call ceiling each). This is
integration evidence, not the final 20-opportunity latency study or a load test.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import time

import httpx

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cloud',action='store_true')
    parser.add_argument('--sessions',type=int,choices=[1,2],default=1)
    parser.add_argument('--url',default='http://127.0.0.1:8120')
    parser.add_argument('--output',default='.run/continuous-replay.json')
    args=parser.parse_args()
    access=json.loads((ROOT/'.azure/qa-access.json').read_text()) if args.cloud else {
        'url':args.url,'producer_key':'local-demo-producer'}
    client=httpx.Client(base_url=access['url'],timeout=30)
    headers={'X-Producer-Token':access['producer_key']}

    def request(method,path,body=None,protected=True):
        response=client.request(method,path,json=body,headers=headers if protected else {})
        response.raise_for_status()
        return response.json()

    states=[]
    for _ in range(args.sessions):
        sid=request('POST','/api/replay-sessions',{'match_id':'match-001'})['session_id']
        states.append({'session_id':sid,'candidate_observed':False})
    for state in states:
        request('POST',f'/api/replay-sessions/{state["session_id"]}/control',{'action':'start'})
    started=time.monotonic()
    try:
        while time.monotonic()-started<80 and any(not s['candidate_observed'] for s in states):
            for state in states:
                if state['candidate_observed']:continue
                sid=state['session_id'];base=f'/api/replay-sessions/{sid}'
                snapshot=request('GET',base+'/snapshot')
                if not snapshot['story']:continue
                state.update(candidate_observed=True,first_candidate_replay_ms=snapshot['clock_ms'],
                             remaining_display_ms=snapshot['story']['expires_at_ms']-snapshot['clock_ms'],
                             mode=snapshot['mode'])
                outcomes=request('GET',base+'/diagnostics')['workflow_outcomes']
                outcome=next(o for o in reversed(outcomes) if o['story_id']==snapshot['story']['id'])
                state.update(outcome_state=outcome['state'],usage=outcome['model_usage'],
                             source_observed_at=outcome['scheduled_at'],candidate_ready_at=outcome['timing']['candidate_ready'])
                if outcome['timing']['candidate_ready']:
                    state['observed_evidence_to_candidate_ms']=round((
                        datetime.fromisoformat(outcome['timing']['candidate_ready'])-
                        datetime.fromisoformat(outcome['scheduled_at'])).total_seconds()*1000,3)
                assert request('GET',base+'/snapshot',protected=False)['story'] is None,'Unapproved story leaked'
            if any(not s['candidate_observed'] for s in states):time.sleep(.4)
    finally:
        # Freeze only after the timing observation or timeout, never to aid readiness.
        server_commit=None
        for state in states:
            base=f'/api/replay-sessions/{state["session_id"]}'
            try:
                request('POST',base+'/control',{'action':'pause'})
                outcomes=request('GET',base+'/diagnostics')['workflow_outcomes']
                if outcomes:
                    last=outcomes[-1]
                    state.setdefault('outcome_state',last['state'])
                    state.setdefault('usage',last['model_usage'])
                    server_commit=last.get('implementation',{}).get('release_commit')
            except Exception as exc:
                state['cleanup_or_diagnostic_error']=type(exc).__name__
        result={'mode':'bounded cloud integration' if args.cloud else 'local template integration',
                'continuous_speed':1,'paused_only_after_measurement':True,
                'server_commit':server_commit,
                'sessions':states,'sample_scope':'one known scripted parent, not independent football opportunities',
                'timing_scope':'server evidence observed at scheduling to candidate completion; not exact ingestion durability, human approval or browser display',
                'misses_retained':True,'automatic_approvals':0}
        output=ROOT/args.output;output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if not all(s['candidate_observed'] and s['remaining_display_ms']>0 for s in states):
        raise SystemExit('One or more opportunities missed; full results retained.')


if __name__=='__main__':main()
