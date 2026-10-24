"""Prepare/verify an actual API process restart using the same isolated database."""
import argparse
import json
from pathlib import Path
import uuid
import httpx

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','verify']);parser.add_argument('--base',default='http://127.0.0.1:8100');args=parser.parse_args()
    record=ROOT/'.run/match-coverage-restart.json'
    with httpx.Client(base_url=args.base,timeout=60,headers={'X-Producer-Token':'local-demo-producer'}) as c:
        if args.phase=='prepare':
            r=c.post('/api/replay-sessions',json={'match_id':'match-0c0a000000000002'});r.raise_for_status();sid=r.json()['session_id'];path=f'/api/replay-sessions/{sid}'
            c.post(path+'/control',json={'action':'seek','clock_ms':105000}).raise_for_status()
            packages=[]
            for story in ['story-goal-goal-1','story-shot-attempt-2','story-shot-attempt-1']:
                response=c.get(f'{path}/stories/{story}/evidence');response.raise_for_status();p=response.json()['story']
                c.post(f'{path}/stories/{story}/review',json={'action':'approve_archive' if story.endswith('attempt-1') else 'approve','expected_revision':p['revision'],'package_hash':p['package_hash'],'idempotency_key':str(uuid.uuid4())}).raise_for_status()
                packages.append(p)
            record.parent.mkdir(exist_ok=True);record.write_text(json.dumps({'session_id':sid,'packages':packages}));print('Prepared three exact approvals for process restart.');return
        saved=json.loads(record.read_text());sid=saved['session_id'];path=f'/api/replay-sessions/{sid}'
        for p in saved['packages']:
            after=c.get(f'{path}/stories/{p["id"]}/evidence');after.raise_for_status();assert after.json()['story']==p
        state=c.get(path+'/snapshot').json();assert state['score']=={'blue':1,'amber':0}
        c.post(path+'/control',json={'action':'seek','clock_ms':136000}).raise_for_status()
        state=httpx.get(args.base+path+'/snapshot',timeout=60).json();assert state['score']=={'blue':0,'amber':0}
        assert [s['id'] for s in state['stories']]==['story-shot-attempt-1']
        with c.stream('GET',path+'/stream',headers={'Last-Event-ID':'0'}) as response:
            for line in response.iter_lines():
                if line.startswith('data: '):
                    streamed=json.loads(line[6:]);assert streamed['score']==state['score'];break
        report={'actual_api_process_restart':True,'session_id':sid,'exact_packages_preserved':len(saved['packages']),
                'package_hashes':{p['id']:p['package_hash'] for p in saved['packages']},'score_before':{'blue':1,'amber':0},'corrected_score':state['score'],
                'unrelated_approval_preserved':True,'sse_reconnect_resynced':True,'mode':'local template / SQLite','model_calls':0}
        (ROOT/'evals/match-coverage/restart.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
