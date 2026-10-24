"""Exercise two versioned demos continuously at real 1x speed, without seeks.

Engineering continuity/source checks only; no usefulness or model claims.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import time
from pathlib import Path
import httpx


def run(base, correction, flagship=False):
    with httpx.Client(base_url=base,headers={'X-Producer-Token':'local-demo-producer'},timeout=60) as client:
        mid=f'match-0c0a00000000000{(6 if correction else 5) if flagship else (4 if correction else 3)}'
        response=client.post('/api/replay-sessions',json={'match_id':mid});response.raise_for_status()
        sid=response.json()['session_id'];path=f'/api/replay-sessions/{sid}'
        client.post(path+'/control',json={'action':'start'}).raise_for_status()
        started=time.monotonic();last=-1;families=set();samples=[];errors=[]
        while time.monotonic()-started<265:
            r=client.get(path+'/snapshot');r.raise_for_status();s=r.json();at=s['clock_ms']
            if at<last:errors.append('clock moved backwards')
            last=at
            families.update(story.get('family','pass') for story in s['stories'])
            if at<104000 and s['score']['blue']!=0:errors.append('goal before source confirmation')
            if 105000<=at<135000 and s['score']['blue']!=1:errors.append('confirmed goal absent')
            if correction and at>=136000 and s['score']['blue']!=0:errors.append('cancelled goal still counted')
            if not samples or at-samples[-1]['clock_ms']>=10000 or at>=240000:
                samples.append({'clock_ms':at,'score':s['score'],'players':s['frame']['players'],'ball':s['frame']['ball']})
            if at>=240000:break
            time.sleep(1)
        if last<240000:errors.append('did not reach end')
        if families!=({'pass','shot','goal','recovery','possession','pressure'} if flagship else {'pass','shot','goal','recovery','possession'}):errors.append('missing family')
        return {'session_id':sid,'match_id':mid,'elapsed_s':round(time.monotonic()-started,2),'last_clock_ms':last,'families':sorted(families),'samples':samples,'errors':errors}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--base',default='http://127.0.0.1:3100');parser.add_argument('--output',default='evals/match-coverage/moving-demo/continuous.json');parser.add_argument('--flagship',action='store_true');args=parser.parse_args()
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda c:run(args.base,c,args.flagship),[False,True]))
    report={'speed':1,'continuous':True,'seeks':0,'model_calls':0,'scope':'Real elapsed API playback; UI guided pauses disabled because this client does not invoke them. Not a browser animation, human usefulness or latency benchmark.','results':results,'passed':not any(r['errors'] for r in results)}
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'sessions':[{k:v for k,v in r.items() if k!='samples'} for r in results]},indent=2))
    if not report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
