"""Idempotent test-environment provisioning. Uses the caller's Azure CLI login.
No application credentials are printed or written to version control.
"""
from __future__ import annotations
import concurrent.futures
import json
import subprocess
from pathlib import Path

GROUP='rg-whynow-demo'
LOCATION='eastus'
SUFFIX='jh1020'
NAMES={'group':GROUP,'location':LOCATION,'cosmos_location':'eastus2','identity':'whynow-api-identity','web_identity':'whynow-web-identity','registry':'whynowregistry'+SUFFIX,'cosmos':'whynow-state-'+SUFFIX,'events':'whynow-events-'+SUFFIX,'storage':'whynowcheckpoints'+SUFFIX,'foundry':'whynow-foundry-'+SUFFIX,'project':'whynow-project','model':'story-model','logs':'whynow-logs','insights':'whynow-insights','environment':'whynow-env','api':'whynow-api','web':'whynow-web'}

def az(*args,quiet=False):
    result=subprocess.run(['az',*args,'-o','json'],capture_output=True,text=True)
    if result.returncode:raise RuntimeError(' '.join(args[:4])+': '+result.stderr[-3000:])
    return json.loads(result.stdout) if result.stdout.strip() else None

def put(path,body,version):
    return az('rest','--method','put','--url','https://management.azure.com'+path+'?api-version='+version,'--body',json.dumps(body))

def main():
    subscription=az('account','show')['id']
    root=f'/subscriptions/{subscription}/resourceGroups/{GROUP}'
    tags={'project':'why-now','environment':'demo','owner':'james','expiry':'2026-11-20'}
    az('group','create','--name',GROUP,'--location',LOCATION,'--tags',*[f'{k}={v}' for k,v in tags.items()])
    identity=az('identity','create','-g',GROUP,'-n',NAMES['identity'],'-l',LOCATION,'--tags',*[f'{k}={v}' for k,v in tags.items()])
    web_identity=az('identity','create','-g',GROUP,'-n',NAMES['web_identity'],'-l',LOCATION,'--tags',*[f'{k}={v}' for k,v in tags.items()])
    def resource(provider,name,version,**kwargs):
        value=put(root+'/providers/'+provider+'/'+name,{'location':LOCATION,'tags':tags,**kwargs},version)
        print('Provisioned',provider,name,flush=True);return value
    jobs={
      'registry':lambda:resource('Microsoft.ContainerRegistry/registries',NAMES['registry'],'2023-07-01',sku={'name':'Basic'},properties={'adminUserEnabled':False,'publicNetworkAccess':'Enabled'}),
      'logs':lambda:resource('Microsoft.OperationalInsights/workspaces',NAMES['logs'],'2023-09-01',properties={'sku':{'name':'PerGB2018'},'retentionInDays':30,'workspaceCapping':{'dailyQuotaGb':.2}}),
      'cosmos':lambda:resource('Microsoft.DocumentDB/databaseAccounts',NAMES['cosmos'],'2024-05-15',kind='GlobalDocumentDB',location=NAMES['cosmos_location'],properties={'databaseAccountOfferType':'Standard','locations':[{'locationName':NAMES['cosmos_location'],'failoverPriority':0,'isZoneRedundant':False}],'capabilities':[{'name':'EnableServerless'}],'disableLocalAuth':True,'publicNetworkAccess':'Enabled','minimalTlsVersion':'Tls12'}),
      'events':lambda:resource('Microsoft.EventHub/namespaces',NAMES['events'],'2024-01-01',sku={'name':'Standard','tier':'Standard','capacity':1},properties={'minimumTlsVersion':'1.2','isAutoInflateEnabled':False,'disableLocalAuth':True,'publicNetworkAccess':'Enabled'}),
      'storage':lambda:resource('Microsoft.Storage/storageAccounts',NAMES['storage'],'2023-05-01',kind='StorageV2',sku={'name':'Standard_LRS'},properties={'minimumTlsVersion':'TLS1_2','allowBlobPublicAccess':False,'allowSharedKeyAccess':False,'supportsHttpsTrafficOnly':True}),
      'foundry':lambda:resource('Microsoft.CognitiveServices/accounts',NAMES['foundry'],'2025-06-01',kind='AIServices',sku={'name':'S0'},identity={'type':'SystemAssigned'},properties={'customSubDomainName':NAMES['foundry'],'allowProjectManagement':True,'publicNetworkAccess':'Enabled','disableLocalAuth':True}),
    }
    outputs={}
    errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures={pool.submit(task):name for name,task in jobs.items()}
        for future in concurrent.futures.as_completed(futures):
            name=futures[future]
            try:outputs[name]=future.result()
            except Exception as e:
                print('FAILED',name,str(e),flush=True);errors.append(name)
    state=NAMES|{'subscription':subscription,'identity_id':identity['id'],'identity_client_id':identity['clientId'],'identity_principal_id':identity['principalId'],'web_identity_id':web_identity['id'],'web_identity_principal_id':web_identity['principalId']}
    Path('.azure').mkdir(exist_ok=True)
    state_path=Path('.azure/deployment.json')
    prior=json.loads(state_path.read_text()) if state_path.exists() else {}
    state_path.write_text(json.dumps(prior|state,indent=2)+'\n')
    print('Base provision requests completed; state in .azure/deployment.json',flush=True)
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
