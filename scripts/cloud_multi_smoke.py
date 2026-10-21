"""Verify deployed multi-pass replay, actual AI, independent approvals and recap.

Uses the existing private access file without printing credentials. This explicit
QA run makes bounded billable model calls. --restart-check verifies stored state
and retracts the final live QA story after an externally requested API restart.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import time
import uuid

import httpx

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine.core import available,digest,load_match
from simulator.scenarios import get_case


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restart-check',action='store_true')
    args=parser.parse_args()
    access=json.loads((ROOT/'.azure/qa-access.json').read_text())
    client=httpx.Client(base_url=access['url'],timeout=90)
    headers={'X-Producer-Token':access['producer_key']}
    artifact=ROOT/'.run/cloud-multi-smoke.json'
    def request(method,path,body=None,producer=False):
        response=client.request(method,path,json=body,headers=headers if producer else {})
        response.raise_for_status()
        return response.json()
    def snapshot(sid,producer=True,story=None):
        return request('GET',f'/api/replay-sessions/{sid}/snapshot'+(f'?story_id={story}' if story else ''),producer=producer)
    def decide(sid,package,action):
        return request('POST',f'/api/replay-sessions/{sid}/stories/{package["id"]}/review',{
            'action':action,'expected_revision':package['revision'],'package_hash':package['package_hash'],
            'idempotency_key':str(uuid.uuid4())},True)
    if args.restart_check:
        record=json.loads(artifact.read_text());sid=record['session_id']
        public=snapshot(sid,False)
        assert [p['id'] for p in public['stories']]==['story-pass-1','story-pass-3'],'Stored independent approvals did not survive'
        assert public['overlay_story_id']=='story-pass-3'
        assert len(request('POST',f'/api/replay-sessions/{sid}/recaps',{} )['moments'])==2
        package=request('GET',f'/api/replay-sessions/{sid}/stories/story-pass-3/evidence',producer=True)['story']
        decide(sid,package,'retract')
        assert snapshot(sid,False)['overlay'] is None
        assert [p['story_id'] for p in request('POST',f'/api/replay-sessions/{sid}/recaps',{})['moments']]==['story-pass-1']
        record['restart_verified']=True;record['final_live_story_retracted']=True
        artifact.write_text(json.dumps(record,indent=2)+'\n')
        print('PASS durable independent approvals after restart; selected retraction leaves earlier archive intact')
        return
    health=request('GET','/api/health')
    assert health['azure_deployed'] and health['version']=='0.3.0'
    assert request('GET','/api/ready')['ok']
    catalogue=request('GET','/api/matches')['matches']
    assert len(catalogue)==171
    assert client.post('/api/replay-sessions',json={'match_id':'match-001'}).status_code==401
    assert client.post('/api/replay-sessions',json={'match_id':'../private'},headers=headers).status_code==422
    mid=get_case('p01-28').match_id
    sid=request('POST','/api/replay-sessions',{'match_id':mid},True)['session_id']
    print('Testing new deployed three-minute replay:',sid,flush=True)
    packages=[]
    for index,cutoff in enumerate([20000,80000,140000],1):
        wanted=f'story-pass-{index}'
        request('POST',f'/api/replay-sessions/{sid}/control',{'action':'seek','clock_ms':cutoff},True)
        for attempt in range(100):
            snap=snapshot(sid)
            if any(p['id']==wanted for p in snap['stories']):break
            if attempt%10==0:
                print(f'Awaiting moment {index}: {snap["delivered_count"]} observations; AI pending={snap["workflow_pending"]}',flush=True)
            time.sleep(1)
        else:raise AssertionError(f'No package for {wanted}')
        assert snap['duration_ms']==180000 and snap['clock_ms']==cutoff
        assert wanted not in [p['id'] for p in snapshot(sid,False)['stories']], 'Unapproved story reached viewer'
        package=request('GET',f'/api/replay-sessions/{sid}/stories/{wanted}/evidence',producer=True)['story']
        assert package['metrics']['pass_id']==f'pass-{index}'
        assert package['id']==wanted and package['revision']==1
        assert package['mode']=='Microsoft Agent Framework + Azure OpenAI',{'story':wanted,'mode':package['mode'],'reason':package['review']['reason']}
        assert package['model_usage']['calls']>=3 and package['model_usage']['usage_complete']
        assert not any(t['action']=='template_fallback' for t in package['trace'])
        assert digest({k:v for k,v in package.items() if k!='package_hash'})==package['package_hash']
        assert package['metrics']['input_cutoff_ms']<=cutoff
        assert all(not(set(package['metrics']['source_message_ids'])&set(old['metrics']['source_message_ids'])) for old in packages)
        decide(sid,package,'approve');packages.append(package)
        public=snapshot(sid,False)
        assert public['overlay_story_id']==wanted and public['overlay']
        assert len(public['stories'])==index and all(p['approved'] for p in public['stories'])
        assert all('package_hash' not in p for p in public['stories'])
        receiver=package['metrics']['receiver_id']
        name=next(p['name'] for p in snap['players'] if p['id']==receiver)
        variant=request('GET',f'/api/replay-sessions/{sid}/stories/{wanted}/variants?language=es&detail=detail&focus={receiver}')
        assert name in variant['text'] and 'recibió' in variant['text']
        recap=request('POST',f'/api/replay-sessions/{sid}/recaps',{})
        assert [p['story_id'] for p in recap['moments']]==[f'story-pass-{i}' for i in range(1,index+1)]
        print(json.dumps({'moment':index,'mode':package['mode'],'workflow_ms':package['workflow_ms'],'usage':package['model_usage']}),flush=True)
    selected=snapshot(sid,False,'story-pass-1')
    assert selected['story']['id']=='story-pass-1' and selected['story_status']=='expired'
    assert selected['story']['approved'] is True and selected['overlay_story_id']=='story-pass-3'
    assert len(request('POST',f'/api/replay-sessions/{sid}/recaps',{'through_ms':30000})['moments'])==1
    decide(sid,packages[1],'retract')
    public=snapshot(sid,False,'story-pass-2')
    assert [p['id'] for p in public['stories']]==['story-pass-1','story-pass-3']
    assert public['overlay_story_id']=='story-pass-3'
    assert client.get(f'/api/replay-sessions/{sid}/stories/story-pass-2/evidence').status_code==404
    assert len(request('POST',f'/api/replay-sessions/{sid}/recaps',{'language':'es'})['moments'])==2
    diagnostics=request('GET',f'/api/replay-sessions/{sid}/diagnostics?story_id=story-pass-3',producer=True)
    assert diagnostics['transport']['mode']=='azure-event-hubs' and not diagnostics['transport']['last_error']
    # Verify the actual deployed rounding fix only after all required observations
    # are durable; a quiet result before ingestion completes is insufficient.
    boundary=get_case('p01-08').match_id
    quiet=request('POST','/api/replay-sessions',{'match_id':boundary},True)['session_id']
    request('POST',f'/api/replay-sessions/{quiet}/control',{'action':'seek','clock_ms':25000},True)
    _,source=load_match(boundary);expected=len(available(source,25000))
    for attempt in range(60):
        quiet_state=snapshot(quiet)
        if quiet_state['delivered_count']>=expected:break
        time.sleep(1)
    else:raise AssertionError('Boundary case did not ingest fully')
    assert quiet_state['stories']==[] and quiet_state['workflow_pending'] is False
    assert request('GET',f'/api/replay-sessions/{quiet}/diagnostics',producer=True)['model_calls']==0
    record={'session_id':sid,'boundary_session_id':quiet,'catalogue_count':len(catalogue),
            'mode':'Microsoft Agent Framework + Azure OpenAI','duration_ms':180000,
            'moments':[{'id':p['id'],'revision':p['revision'],'workflow_ms':p['workflow_ms'],'usage':p['model_usage']} for p in packages],
            'verified':['catalogue','forward seek','Event Hubs ingestion','Cosmos scoped revisions','three actual AI investigations',
                        'independent approvals','Spanish actual receiver','archived story selection','multi-moment recap',
                        'isolated retraction','original expiry','deployed distance boundary'],
            'restart_verified':False}
    artifact.parent.mkdir(parents=True,exist_ok=True);artifact.write_text(json.dumps(record,indent=2)+'\n')
    print('PASS deployed multi-pass workflow, independent publication, history, recap, and rounding boundary',flush=True)


if __name__=='__main__':main()
