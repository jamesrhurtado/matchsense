"""Bounded existing-deployment smoke: five source families, at most ten calls.

No provisioning/publication. Verify exact deployment/rates before dispatch.
Worst-case token reservation is under $0.10 at the verified retail rates.
This checks one model execution per family, not usefulness or model superiority.
"""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import httpx


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
    deployment=json.loads(subprocess.check_output(['az','cognitiveservices','account','deployment','show','-g','rg-whynow-demo','-n','whynow-foundry-jh1020','--deployment-name','story-model','-o','json'],text=True))
    model=deployment['properties']['model']
    if (model['name'],model['version'],deployment['sku']['name'])!=('gpt-4o-mini','2024-07-18','GlobalStandard'):raise SystemExit('Deployment contract changed; no calls dispatched.')
    query="productName eq 'Azure OpenAI' and armRegionName eq 'eastus' and (skuName eq 'gpt-4o-mini-0718-Inp-glbl' or skuName eq 'gpt-4o-mini-0718-Outp-glbl')"
    response=httpx.get('https://prices.azure.com/api/retail/prices',params={'$filter':query,'currencyCode':'USD'},timeout=30);response.raise_for_status();items=response.json()['Items']
    if len(items)!=2 or any(i['unitOfMeasure']!='1K' or i['currencyCode']!='USD' for i in items):raise SystemExit('Ambiguous rates; no calls dispatched.')
    rates={i['skuName']:i['retailPrice']*1000 for i in items}
    inp=rates['gpt-4o-mini-0718-Inp-glbl'];out=rates['gpt-4o-mini-0718-Outp-glbl']
    reservation=5*(32000*inp+2200*out)/1e6
    if reservation>.1:raise SystemExit('Reservation exceeds $0.10; no calls dispatched.')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'rates.json').write_text(json.dumps({'retrieved_at':datetime.now(timezone.utc).isoformat(),'source':'https://prices.azure.com/api/retail/prices','items':items,'reserved_usd':reservation},indent=2)+'\n')
    os.environ.update(AZURE_OPENAI_ENDPOINT='https://whynow-foundry-jh1020.openai.azure.com/',FOUNDRY_MODEL_DEPLOYMENT='story-model',AZURE_OPENAI_API_VERSION='2024-10-21',WHY_NOW_AZURE_ENVIRONMENT='development');os.environ.pop('AZURE_CLIENT_ID',None)
    from engine.structured_workflow import run_event_workflow
    from engine.workflow import EvidenceTools
    from simulator.flagship import build
    from engine.event_narrative import EventPackage,build_event_package
    from engine.foundry_workflow import Limits
    meta,rows=build();tools=EvidenceTools(meta,rows,105000);results=[]
    for family,subject in [('pressure','pass-4'),('shot','attempt-1'),('goal','goal-1'),('recovery','loose-1'),('possession','60000')]:
        outcomes=[]
        package=run_event_workflow(tools,family,subject,limits=Limits(deadline_s=15,model_calls=2,token_budget=32000),outcome_callback=outcomes.append)
        valid=False
        if package:
            EventPackage.model_validate(package)
            valid=package['variants']==build_event_package(tools.get_event_facts(family,subject),meta)['variants']
            (args.output/f'{family}-package.json').write_text(json.dumps(package,ensure_ascii=False,indent=2)+'\n')
        terminal=outcomes[-1] if outcomes else {'state':'no_evidence','usage':{}}
        passed=bool(package and valid and package['mode']=='Microsoft Agent Framework + Azure OpenAI' and terminal['state']=='produced' and terminal['usage'].get('usage_complete'))
        result={'family':family,'subject_id':subject,'passed':passed,'exact_source_rendering':valid,'mode':package['mode'] if package else None,'terminal':terminal};results.append(result)
        print(json.dumps({'family':family,'passed':passed,'state':terminal['state'],'usage':terminal['usage']}),flush=True)
    usage={key:sum(r['terminal']['usage'].get(key,0) for r in results) for key in ['calls','input_tokens','output_tokens','total_tokens']}
    report={'scope':'One bounded real execution per family; no claim of usefulness, quality distribution or multi-agent superiority. No publication/deployment.','model':model,'sku':deployment['sku']['name'],'api_version':'2024-10-21','usage':usage,'retail_estimate_usd':(usage['input_tokens']*inp+usage['output_tokens']*out)/1e6,'results':results,'passed':all(r['passed'] for r in results)}
    (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if not report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
