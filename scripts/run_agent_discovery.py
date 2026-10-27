"""Explicit bounded local model evaluation using existing Azure CLI identity.

No resource provisioning or application deployment. Retail prices are checked for
this exact text model/SKU before dispatch. Account discounts are not assumed.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

import httpx


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=['smoke','comparison','fault-probe'],required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--cases',help='Optional exact discovery case IDs for a targeted verification')
    args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(root))
    deployment=json.loads(subprocess.check_output([
        'az','cognitiveservices','account','deployment','show','-g','rg-whynow-demo',
        '-n','whynow-foundry-jh1020','--deployment-name','story-model','-o','json'],text=True))
    model=deployment['properties']['model']
    if (model['name'],model['version'],deployment['sku']['name'])!=('gpt-4o-mini','2024-07-18','GlobalStandard'):
        raise SystemExit('Deployment changed: review the model/rate contract before running.')
    query="productName eq 'Azure OpenAI' and armRegionName eq 'eastus' and (skuName eq 'gpt-4o-mini-0718-Inp-glbl' or skuName eq 'gpt-4o-mini-0718-Outp-glbl')"
    response=httpx.get('https://prices.azure.com/api/retail/prices',params={'$filter':query,'currencyCode':'USD'},timeout=30)
    response.raise_for_status()
    rows=response.json()['Items']
    if len(rows)!=2 or any(x['unitOfMeasure']!='1K' or x['currencyCode']!='USD' for x in rows):
        raise SystemExit('Retail price response is ambiguous; no model work dispatched.')
    rates={x['skuName']:x['retailPrice']*1000 for x in rows}
    now=datetime.now(timezone.utc)
    from engine.structured_workflow import PROMPT_VERSION
    from engine.editorial_narrative import SCHEMA_VERSION, RENDERER_VERSION
    if args.stage == 'fault-probe':
        if args.cases:
            raise SystemExit('The bounded fault-probe stage uses three fixed authored cases.')
        from evals.agentic.fault_probes import fault_probe_cases
        default_cases=','.join(case.case_id for case in fault_probe_cases())
        default_trials=2
        maximum_cases=3
        model_arms=2
    else:
        default_cases='history-contrast,history-marginal,history-ordinary,early-late-outcome' if args.stage=='smoke' else None
        default_trials=1
        maximum_cases=4 if args.stage=='smoke' else 15
        model_arms=3
    selected_cases=args.cases or default_cases
    count=len(selected_cases.split(',')) if selected_cases else maximum_cases
    if count < 1 or count > maximum_cases:
        raise SystemExit('Selected case count exceeds the bounded stage.')
    trials=default_trials
    cap=count*model_arms*trials*6
    workflows=cap//6
    config={'trials':trials,'order_seed':1041,'max_model_calls':cap,
            'max_input_tokens':workflows*32000,'max_output_tokens':workflows*6600,
            'max_estimated_cost':1.5 if args.stage=='comparison' else .5,
            'input_per_million':rates['gpt-4o-mini-0718-Inp-glbl'],
            'output_per_million':rates['gpt-4o-mini-0718-Outp-glbl'],
            'rate_source':'https://prices.azure.com/api/retail/prices',
            'rate_date':now.date().isoformat(),'currency':'USD',
            'deadline_utc':(now+timedelta(minutes=25)).isoformat(),
            'model':model['name'],'model_version':model['version'],'deployment':'story-model',
            'api_version':'2024-10-21','prompt_version':PROMPT_VERSION,'tool_version':'evidence-tools-v3',
            'renderer_version':RENDERER_VERSION,'schema_version':SCHEMA_VERSION}
    args.output.mkdir(parents=True,exist_ok=False)
    config_path=args.output/'run-config.json';config_path.write_text(json.dumps(config,indent=2)+'\n')
    (args.output/'verified-retail-rates.json').write_text(json.dumps({'retrieved_at':now.isoformat(),'filter':query,'items':rows},indent=2)+'\n')
    env={**os.environ,'AZURE_OPENAI_ENDPOINT':'https://whynow-foundry-jh1020.openai.azure.com/',
         'FOUNDRY_MODEL_DEPLOYMENT':'story-model','FOUNDRY_MODEL_NAME':model['name'],
         'FOUNDRY_MODEL_VERSION':model['version'],'AZURE_OPENAI_API_VERSION':'2024-10-21',
         'WHY_NOW_AZURE_ENVIRONMENT':'development'}
    # User-assigned cloud identity must not override local Azure CLI credentials.
    env.pop('AZURE_CLIENT_ID',None)
    arms='S3,M3' if args.stage=='fault-probe' else 'T3,S3,M3,D3'
    command=[sys.executable,'-m','evals.agentic.run','--live','--arms',arms,
             '--config',str(config_path),'--output',str(args.output)]
    if args.stage=='fault-probe':
        command += ['--fault-probe']
    if args.stage=='fault-probe':
        command += ['--trials',str(trials)]
    if selected_cases and args.stage!='fault-probe':command+=['--cases',selected_cases]
    if args.dry_run:command+=['--dry-run']
    print(f"Verified rates: ${config['input_per_million']}/M input, ${config['output_per_million']}/M output. Stage ceiling ${config['max_estimated_cost']}; {cap} calls.",flush=True)
    subprocess.run(command,cwd=root,env=env,check=True)


if __name__=='__main__':main()
