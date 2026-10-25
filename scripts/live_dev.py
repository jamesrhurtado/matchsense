"""Run the synthetic live desk against the existing Azure model; never provision.

Preflight verifies model identity, current retail rates and Azure CLI credentials.
No model request is made until a producer starts an AI session. Budget reservation
is conservative: at most 96 model calls per live session (edits excluded).
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import httpx

ROOT=Path(__file__).resolve().parents[1]

def preflight():
    deployment=json.loads(subprocess.check_output(['az','cognitiveservices','account','deployment','show','-g','rg-whynow-demo','-n','whynow-foundry-jh1020','--deployment-name','story-model','-o','json'],text=True))
    model=deployment['properties']['model']
    if (model['name'],model['version'],deployment['sku']['name'])!=('gpt-4o-mini','2024-07-18','GlobalStandard'):raise RuntimeError('Deployment changed; review before starting AI mode.')
    query="productName eq 'Azure OpenAI' and armRegionName eq 'eastus' and (skuName eq 'gpt-4o-mini-0718-Inp-glbl' or skuName eq 'gpt-4o-mini-0718-Outp-glbl')"
    response=httpx.get('https://prices.azure.com/api/retail/prices',params={'$filter':query,'currencyCode':'USD'},timeout=30);response.raise_for_status()
    rows=response.json()['Items']
    if len(rows)!=2 or any(r['unitOfMeasure']!='1K' or r['currencyCode']!='USD' for r in rows):raise RuntimeError('Unrecognized retail rates.')
    rates={r['skuName']:r['retailPrice']*1000 for r in rows}
    reservation=48*(32000*rates['gpt-4o-mini-0718-Inp-glbl']+6600*rates['gpt-4o-mini-0718-Outp-glbl'])/1e6
    if reservation>.5:raise RuntimeError('Per-session conservative reservation exceeds $0.50; review rates.')
    # Capture privately. Never print or persist the bearer token.
    subprocess.run(['az','account','get-access-token','--resource','https://cognitiveservices.azure.com/','--output','none'],check=True,capture_output=True)
    from datetime import datetime,timezone
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'model':model,'sku':deployment['sku']['name'],'rates_per_million':rates,'source':'https://prices.azure.com/api/retail/prices','session_reservation_usd':reservation,'max_calls_per_live_session':96,'note':'Conservative reservation, not invoice. Producer-triggered edits are separate existing workflows.'}
    import hashlib
    paths=['services/api/main.py','engine/structured_workflow.py','engine/event_workflow.py','engine/event_metrics.py','engine/pressure.py','apps/web/app/page.tsx','apps/web/components/match-desk.tsx','apps/web/components/match-stage.tsx']
    report['source']={'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),'sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}
    env={**os.environ,'WHY_NOW_MODEL_MODE':'foundry','WHY_NOW_MATCH_MODEL':'1','WHY_NOW_MATCH_COVERAGE':'1','AZURE_OPENAI_ENDPOINT':'https://whynow-foundry-jh1020.openai.azure.com/','FOUNDRY_MODEL_DEPLOYMENT':'story-model','FOUNDRY_MODEL_NAME':model['name'],'FOUNDRY_MODEL_VERSION':model['version'],'AZURE_OPENAI_API_VERSION':'2024-10-21','WHY_NOW_AZURE_ENVIRONMENT':'development','WHY_NOW_DB':os.getenv('WHY_NOW_DB',str(ROOT/'.run/live-match.db'))}
    env.pop('AZURE_CLIENT_ID',None)
    return env,report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-only',action='store_true');parser.add_argument('--api-port',type=int,default=8100);parser.add_argument('--web-port',type=int,default=3100);parser.add_argument('--preflight-only',action='store_true')
    args=parser.parse_args();env,report=preflight()
    (ROOT/'.run').mkdir(exist_ok=True)
    (ROOT/'.run/live-model-preflight.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f"Verified {report['model']['name']} {report['model']['version']}; conservative reservation ${report['session_reservation_usd']:.3f}/live session (not a bill).",flush=True)
    if args.preflight_only:return
    if args.api_only:
        os.execvpe(sys.executable,[sys.executable,'-m','uvicorn','services.api.main:app','--host','127.0.0.1','--port',str(args.api_port)],env)
    import signal
    import time
    children=[]
    try:
        children.append(subprocess.Popen([sys.executable,'-m','uvicorn','services.api.main:app','--host','127.0.0.1','--port',str(args.api_port)],cwd=ROOT,env=env,start_new_session=True))
        children.append(subprocess.Popen(['npm','run','start','--','--port',str(args.web_port)],cwd=ROOT/'apps/web',env={**env,'API_URL':f'http://127.0.0.1:{args.api_port}'},start_new_session=True))
        print(f'Live desk: http://127.0.0.1:{args.web_port}',flush=True)
        while all(child.poll() is None for child in children):time.sleep(.5)
        raise SystemExit(next((child.returncode or 1 for child in children if child.poll() is not None),1))
    except KeyboardInterrupt:pass
    finally:
        for child in children:
            if child.poll() is None:os.killpg(child.pid,signal.SIGTERM)
        for child in children:
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:child.kill()

if __name__=='__main__':main()
