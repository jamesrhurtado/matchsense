"""Deploy revisioned images with managed identities and a private producer key.
The local QA access file is owner-readable and ignored by Git and Docker.
"""
from provision import az,put
from configure import S,RG,resource,wait_ready
from pathlib import Path
import json,secrets,os,time

def deploy():
    env=wait_ready(resource('Microsoft.App/managedEnvironments',S['environment']),'2024-03-01')
    insights=az('rest','--method','get','--url','https://management.azure.com'+resource('Microsoft.Insights/components',S['insights'])+'?api-version=2020-02-02')
    access_path=Path('.azure/qa-access.json')
    existing=json.loads(access_path.read_text()) if access_path.exists() else {}
    token=existing.get('producer_key') or secrets.token_urlsafe(36)
    access_path.write_text(json.dumps({'producer_key':token},indent=2)+'\n');os.chmod(access_path,0o600)
    tag=os.getenv('WHY_NOW_IMAGE_TAG','cloud-v1')
    registry=S['registry']+'.azurecr.io'
    api_env={
      'WHY_NOW_ENVIRONMENT':'azure','WHY_NOW_AZURE_ENVIRONMENT':'production','WHY_NOW_MODEL_MODE':'foundry',
      'AZURE_CLIENT_ID':S['identity_client_id'],'AZURE_OPENAI_ENDPOINT':'https://'+S['foundry']+'.openai.azure.com/',
      'FOUNDRY_MODEL_DEPLOYMENT':S['model'],'FOUNDRY_PROJECT_ENDPOINT':'https://'+S['foundry']+'.services.ai.azure.com/api/projects/'+S['project'],
      'WHY_NOW_COSMOS_ENDPOINT':'https://'+S['cosmos']+'.documents.azure.com:443/','WHY_NOW_COSMOS_DATABASE':'whynow',
      'WHY_NOW_EVENTHUB_NAMESPACE':S['events']+'.servicebus.windows.net','WHY_NOW_EVENTHUB_NAME':'match-observations',
      'WHY_NOW_EVENTHUB_CONSUMER_GROUP':'whynow-state','WHY_NOW_CHECKPOINT_ACCOUNT_URL':'https://'+S['storage']+'.blob.core.windows.net',
      'WHY_NOW_CHECKPOINT_CONTAINER':'eventhub-checkpoints','APPLICATIONINSIGHTS_CONNECTION_STRING':insights['properties']['ConnectionString'],
      'OTEL_SERVICE_NAME':'whynow-api','OTEL_TRACES_SAMPLER_ARG':'0.1',
    }
    domain=env['properties']['defaultDomain'];api_url='https://'+S['api']+'.internal.'+domain
    api_env['WHY_NOW_ORIGINS']='https://'+S['web']+'.'+domain
    def app(name,image,port,external,environ,secret=None):
        app_identity=S.get('web_identity_id',S['identity_id']) if external else S['identity_id']
        configuration={'activeRevisionsMode':'Single','ingress':{'external':external,'targetPort':port,'transport':'auto','allowInsecure':False},'registries':[{'server':registry,'identity':app_identity}]}
        variables=[{'name':k,'value':v} for k,v in environ.items()]
        if secret:
            configuration['secrets']=[{'name':'producer-key','value':secret}]
            variables.append({'name':'WHY_NOW_PRODUCER_TOKEN','secretRef':'producer-key'})
        body={'location':S['location'],'tags':{'project':'why-now','environment':'demo','expiry':'2026-11-20'},'identity':{'type':'UserAssigned','userAssignedIdentities':{app_identity:{}}},'properties':{'managedEnvironmentId':env['id'],'workloadProfileName':'Consumption','configuration':configuration,'template':{'revisionSuffix':os.getenv('WHY_NOW_WEB_IMAGE_TAG',tag) if external else tag,'containers':[{'name':name,'image':registry+'/'+image+':'+(os.getenv('WHY_NOW_WEB_IMAGE_TAG',tag) if external else tag),'env':variables,'resources':{'cpu':.5 if external else 1,'memory':'1Gi' if external else '2Gi'},'probes':[{'type':'Liveness','httpGet':{'path':'/healthz' if external else '/api/health','port':port},'initialDelaySeconds':30,'periodSeconds':30,'timeoutSeconds':5},{'type':'Readiness','httpGet':{'path':'/healthz' if external else '/api/ready','port':port},'initialDelaySeconds':15,'periodSeconds':15,'timeoutSeconds':5,'failureThreshold':10}]}],'scale':{'minReplicas':1,'maxReplicas':1}}}}
        put(resource('Microsoft.App/containerApps',name),body,'2024-03-01')
        print('Deployment requested:',name,flush=True)
        revision=name+'--'+(os.getenv('WHY_NOW_WEB_IMAGE_TAG',tag) if external else tag)
        for attempt in range(100):
            status=az('rest','--method','get','--url','https://management.azure.com'+resource('Microsoft.App/containerApps',name)+'?api-version=2024-03-01')
            if status['properties'].get('latestReadyRevisionName')==revision:
                print('Healthy revision:',revision,flush=True)
                break
            time.sleep(3)
        else:raise RuntimeError('Revision did not become healthy: '+revision)
    app(S['api'],'whynow-api',8000,False,api_env,token)
    app(S['web'],'whynow-web',3000,True,{'API_URL':api_url})
    url='https://'+S['web']+'.'+domain
    access_path.write_text(json.dumps({'url':url,'producer_key':token},indent=2)+'\n');os.chmod(access_path,0o600)
    S['url']=url;S['api_url']=api_url
    Path('.azure/deployment.json').write_text(json.dumps(S,indent=2)+'\n')
    print('Web URL:',url,flush=True)
    print('Producer key stored privately in .azure/qa-access.json',flush=True)

if __name__=='__main__':deploy()
