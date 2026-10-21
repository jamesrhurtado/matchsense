"""Exercise the deployed system without printing its producer credential.
Run after infra/deploy_apps.py. Optional --retract checks the persisted QA session.
"""
from pathlib import Path
import json,time,uuid,sys
import httpx
access=json.loads(Path('.azure/qa-access.json').read_text())
client=httpx.Client(base_url=access['url'],timeout=90)
headers={'X-Producer-Token':access['producer_key']}
def request(method,path,body=None,producer=False):
    r=client.request(method,path,json=body,headers=headers if producer else {})
    r.raise_for_status();return r.json()
def snap(sid,producer=True):return request('GET',f'/api/replay-sessions/{sid}/snapshot',producer=producer)
def decide(sid,action,p):
    return request('POST',f'/api/replay-sessions/{sid}/stories/{p["id"]}/review',{'action':action,'expected_revision':p['revision'],'package_hash':p['package_hash'],'idempotency_key':str(uuid.uuid4())},True)
if '--retract' in sys.argv:
    sid=json.loads(Path('.azure/smoke-session.json').read_text())['session_id']
    assert snap(sid,False)['overlay'],'Published state did not survive restart'
    p=snap(sid)['story'];decide(sid,'retract',p)
    assert snap(sid,False)['story'] is None
    assert not request('POST',f'/api/replay-sessions/{sid}/recaps',{})['moments']
    print('PASS persisted approval after restart, retraction and recap invalidation');sys.exit()
health=request('GET','/api/health');assert health['azure_deployed']
assert client.post('/api/replay-sessions',json={}).status_code==401
sid=request('POST','/api/replay-sessions',{},True)['session_id']
path=f'/api/replay-sessions/{sid}'
request('POST',path+'/control',{'action':'speed','speed':4},True)
request('POST',path+'/control',{'action':'start'},True)
for i in range(100):
    s=snap(sid)
    if s['clock_ms']>=25000:
        request('POST',path+'/control',{'action':'pause'},True);break
    time.sleep(.3)
else:raise AssertionError('Replay did not advance')
for i in range(100):
    s=snap(sid)
    if s['story']:break
    time.sleep(1)
else:raise AssertionError('No reviewed story produced')
p=request('GET',path+'/stories/story-pass-1/evidence',producer=True)['story']
assert p['mode']=='Microsoft Agent Framework + Azure OpenAI',p.get('fallback_reason',p['mode'])
assert p['model_usage']['calls']>=3
assert snap(sid,False)['story'] is None
assert client.get(access['url']+path+'/diagnostics').status_code==401
r=decide(sid,'approve',s['story']);assert r['status']=='approved'
assert snap(sid,False)['overlay']
variant=request('GET',path+'/stories/story-pass-1/variants?language=es&detail=detail&focus=blue-08')
assert variant['language']=='es' and 'Theo Vega' in variant['text']
assert request('POST',path+'/recaps',{})['moments']
with client.stream('GET',path+'/stream',timeout=15) as stream:
    lines=[]
    for line in stream.iter_lines():
        lines.append(line)
        if line.startswith('data:'):break
    assert any('event: resync' in line for line in lines)
diag=request('GET',path+'/diagnostics',producer=True)
assert diag['transport']['persisted_this_process']>0
assert not diag['transport']['last_error'],diag['transport']
Path('.azure/smoke-session.json').write_text(json.dumps({'session_id':sid,'diagnostics':diag},indent=2))
print(json.dumps({'result':'PASS','session_id':sid,'mode':p['mode'],'workflow_ms':p['workflow_ms'],'usage':p['model_usage'],'transport':diag['transport'],'verified':['authorization','Event Hubs ingestion','Cosmos persistence','actual model workflow','producer approval','Spanish player variant','recap','SSE reconnect']},indent=2))
