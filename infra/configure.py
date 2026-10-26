"""Provision child resources, model, managed identity roles and Container Apps environment."""
from provision import az,put
import json,concurrent.futures,time
from pathlib import Path
OPERATOR=az('ad','signed-in-user','show')['id']
S=json.loads(Path('.azure/deployment.json').read_text());RG=S['group'];SUB=S['subscription'];ROOT=f'/subscriptions/{SUB}/resourceGroups/{RG}'
def resource(provider,name):return ROOT+'/providers/'+provider+'/'+name

def wait_ready(path,version):
    for attempt in range(90):
        d=az('rest','--method','get','--url','https://management.azure.com'+path+'?api-version='+version)
        state=d.get('properties',{}).get('provisioningState','Succeeded')
        if state=='Succeeded':return d
        if state=='Failed':raise RuntimeError(path+' failed')
        time.sleep(5)
    raise RuntimeError(path+' provisioning timeout')

def cosmos():
    path=resource('Microsoft.DocumentDB/databaseAccounts',S['cosmos']);wait_ready(path,'2024-05-15')
    put(path+'/sqlDatabases/whynow',{'properties':{'resource':{'id':'whynow'}}},'2024-05-15')
    for name in ['session-state','story-state','observations']:
        put(path+'/sqlDatabases/whynow/containers/'+name,{'properties':{'resource':{'id':name,'partitionKey':{'paths':['/session_id'],'kind':'Hash','version':2},'indexingPolicy':{'indexingMode':'consistent','automatic':True,'includedPaths':[{'path':'/*'}],'excludedPaths':[{'path':'/data/*'}]}}}},'2024-05-15')
    for principal in [S['identity_principal_id'],OPERATOR]:
        az('cosmosdb','sql','role','assignment','create','-g',RG,'-a',S['cosmos'],'--principal-id',principal,'--scope',path,'--role-definition-id',path+'/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002')
    print('Cosmos database, containers and data roles ready',flush=True)

def events():
    path=resource('Microsoft.EventHub/namespaces',S['events']);wait_ready(path,'2024-01-01')
    put(path+'/eventhubs/match-observations',{'properties':{'partitionCount':2,'messageRetentionInDays':1}},'2024-01-01')
    put(path+'/eventhubs/match-observations/consumergroups/whynow-state',{'properties':{}},'2024-01-01')
    storage=resource('Microsoft.Storage/storageAccounts',S['storage']);wait_ready(storage,'2023-05-01')
    put(storage+'/blobServices/default/containers/eventhub-checkpoints',{'properties':{'publicAccess':'None'}},'2023-05-01')
    for role,scope in [('Azure Event Hubs Data Sender',path),('Azure Event Hubs Data Receiver',path),('Storage Blob Data Contributor',storage)]:
        az('role','assignment','create','--assignee-object-id',S['identity_principal_id'],'--assignee-principal-type','ServicePrincipal','--role',role,'--scope',scope)
    print('Event Hubs, checkpoint storage and roles ready',flush=True)

def model():
    path=resource('Microsoft.CognitiveServices/accounts',S['foundry']);wait_ready(path,'2025-06-01')
    put(path+'/projects/'+S['project'],{'location':S['location'],'identity':{'type':'SystemAssigned'},'properties':{'displayName':'MatchSense engineering test','description':'Evidence-grounded football storytelling'}},'2025-06-01')
    az('cognitiveservices','account','deployment','create','-g',RG,'-n',S['foundry'],'--deployment-name',S['model'],'--model-name','gpt-4o-mini','--model-version','2024-07-18','--model-format','OpenAI','--sku-name','GlobalStandard','--sku-capacity','50')
    az('role','assignment','create','--assignee-object-id',S['identity_principal_id'],'--assignee-principal-type','ServicePrincipal','--role','Cognitive Services OpenAI User','--scope',path)
    az('role','assignment','create','--assignee-object-id',OPERATOR,'--assignee-principal-type','User','--role','Cognitive Services OpenAI User','--scope',path)
    print('Foundry project, model and invocation roles ready',flush=True)

def hosting():
    logs=resource('Microsoft.OperationalInsights/workspaces',S['logs']);d=wait_ready(logs,'2023-09-01')
    keys=az('rest','--method','post','--url','https://management.azure.com'+logs+'/sharedKeys?api-version=2023-09-01')
    put(resource('Microsoft.Insights/components',S['insights']),{'location':S['location'],'kind':'web','properties':{'Application_Type':'web','WorkspaceResourceId':logs,'RetentionInDays':30,'IngestionMode':'LogAnalytics'}},'2020-02-02')
    put(resource('Microsoft.App/managedEnvironments',S['environment']),{'location':S['location'],'tags':{'project':'why-now','environment':'demo','expiry':'2026-11-20'},'properties':{'appLogsConfiguration':{'destination':'log-analytics','logAnalyticsConfiguration':{'customerId':d['properties']['customerId'],'sharedKey':keys['primarySharedKey']}},'workloadProfiles':[{'name':'Consumption','workloadProfileType':'Consumption'}]}},'2024-03-01')
    for principal in {S['identity_principal_id'],S.get('web_identity_principal_id',S['identity_principal_id'])}:
        az('role','assignment','create','--assignee-object-id',principal,'--assignee-principal-type','ServicePrincipal','--role','AcrPull','--scope',resource('Microsoft.ContainerRegistry/registries',S['registry']))
    print('Hosting environment requested; observability and image roles ready',flush=True)

if __name__=='__main__':
    errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:
        futures=[p.submit(fn) for fn in [cosmos,events,model,hosting]]
        for f in concurrent.futures.as_completed(futures):
            try:f.result()
            except Exception as e:print('FAILED',e,flush=True);errors.append(str(e))
    if errors:raise SystemExit(1)
