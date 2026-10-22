"""Verify deployed multi-pass replay, model attempts, independent approvals and recap.

Uses the existing private access file without printing credentials. This explicit
QA run makes bounded billable model calls and records factual fallbacks explicitly.
--require-all-ai additionally fails if any moment falls back; results are retained.
--session-id resumes a partial QA replay without regenerating existing outputs.
--restart-check verifies stored state
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
    parser.add_argument('--session-id',help='Resume an interrupted QA replay without regenerating existing model output.')
    parser.add_argument('--require-all-ai',action='store_true',help='Additionally fail if any moment used the explicit factual fallback.')
    parser.add_argument('--artifact',default='.run/cloud-multi-smoke.json',help='Nonsecret result file; use a separate path for each release.')
    args=parser.parse_args()
    access=json.loads((ROOT/'.azure/qa-access.json').read_text())
    client=httpx.Client(base_url=access['url'],timeout=90)
    headers={'X-Producer-Token':access['producer_key']}
    artifact=ROOT/args.artifact
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
    assert health['azure_deployed'] and health['version'] in {'0.3.0','0.4.0'}
    assert request('GET','/api/ready')['ok']
    catalogue=request('GET','/api/matches')['matches']
    assert len(catalogue)==171
    assert client.post('/api/replay-sessions',json={'match_id':'match-001'}).status_code==401
    assert client.post('/api/replay-sessions',json={'match_id':'../private'},headers=headers).status_code==422
    mid=get_case('p01-28').match_id
    sid=args.session_id or request('POST','/api/replay-sessions',{'match_id':mid},True)['session_id']
    print('Testing new deployed three-minute replay:',sid,flush=True)
    packages=[]
    for index,cutoff in enumerate([20000,80000,140000],1):
        wanted=f'story-pass-{index}'
        before=snapshot(sid)
        if before['clock_ms']<cutoff:
            request('POST',f'/api/replay-sessions/{sid}/control',{'action':'seek','clock_ms':cutoff},True)
        for attempt in range(100):
            snap=snapshot(sid)
            if any(p['id']==wanted for p in snap['stories']):break
            if attempt%10==0:
                print(f'Awaiting moment {index}: {snap["delivered_count"]} observations; AI pending={snap["workflow_pending"]}',flush=True)
            time.sleep(1)
        else:raise AssertionError(f'No package for {wanted}')
        assert snap['duration_ms']==180000 and snap['clock_ms']>=cutoff
        selected=next(p for p in snap['stories'] if p['id']==wanted)
        previously_approved=selected['approved']
        if not previously_approved:
            assert wanted not in [p['id'] for p in snapshot(sid,False)['stories']], 'Unapproved story reached viewer'
        package=request('GET',f'/api/replay-sessions/{sid}/stories/{wanted}/evidence',producer=True)['story']
        assert package['metrics']['pass_id']==f'pass-{index}'
        assert package['id']==wanted and package['revision']==1
        assert package['mode'] in ('Microsoft Agent Framework + Azure OpenAI','template fallback')
        assert package['model_usage']['calls']>=1 and package['model_usage']['usage_complete']
        if package['mode']=='Microsoft Agent Framework + Azure OpenAI':
            assert package['model_usage']['calls']>=(2 if package['schema_version'] in {'2.0.0','3.0.0','4.0.0'} else 3)
            assert not any(t['action']=='template_fallback' for t in package['trace'])
        else:
            assert any(t['action']=='template_fallback' for t in package['trace'])
        assert digest({k:v for k,v in package.items() if k!='package_hash'})==package['package_hash']
        if package['schema_version'] in {'2.0.0','3.0.0','4.0.0'}:
            from engine.contracts import PublicationPackage
            PublicationPackage.model_validate(package)
            assert all('clauses' in v for v in package['variants'])
            outcomes=request('GET',f'/api/replay-sessions/{sid}/diagnostics?story_id={wanted}',producer=True)['workflow_outcomes']
            assert any(o['state'] in {'produced','fallback'} and o['model_usage']['calls']==package['model_usage']['calls'] for o in outcomes)
        assert package['metrics']['input_cutoff_ms']<=cutoff
        assert all(not(set(package['metrics']['source_message_ids'])&set(old['metrics']['source_message_ids'])) for old in packages)
        if not previously_approved:decide(sid,package,'approve')
        packages.append(package)
        public=snapshot(sid,False)
        if snap['clock_ms']<package['expires_at_ms']:
            assert public['overlay_story_id']==wanted and public['overlay']
        assert len(public['stories'])>=index and all(p['approved'] for p in public['stories'])
        assert all('package_hash' not in p for p in public['stories'])
        receiver=package['metrics']['receiver_id']
        name=next(p['name'] for p in snap['players'] if p['id']==receiver)
        variant=request('GET',f'/api/replay-sessions/{sid}/stories/{wanted}/variants?language=es&detail=detail&focus={receiver}')
        assert name in variant['text'] and 'recibió' in variant['text']
        recap=request('POST',f'/api/replay-sessions/{sid}/recaps',{})
        assert {f'story-pass-{i}' for i in range(1,index+1)}.issubset({p['story_id'] for p in recap['moments']})
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
    actual=sum(p['mode']=='Microsoft Agent Framework + Azure OpenAI' for p in packages)
    assert actual>=1,'No model-composed package was verified'
    record={'session_id':sid,'boundary_session_id':quiet,'catalogue_count':len(catalogue),
            'actual_ai_packages':actual,'template_fallback_packages':len(packages)-actual,'duration_ms':180000,
            'moments':[{'id':p['id'],'revision':p['revision'],'mode':p['mode'],'workflow_ms':p['workflow_ms'],'usage':p['model_usage'],
                        'fallback_reason':next((t.get('reason') or t.get('status') for t in p['trace'] if t['action']=='template_fallback'),None)} for p in packages],
            'verified':['catalogue','forward seek','Event Hubs ingestion','Cosmos scoped revisions','three bounded model workflows with per-moment modes recorded',
                        'independent approvals','Spanish actual receiver','archived story selection','multi-moment recap',
                        'isolated retraction','original expiry','deployed distance boundary'],
            'restart_verified':False}
    artifact.parent.mkdir(parents=True,exist_ok=True);artifact.write_text(json.dumps(record,indent=2)+'\n')
    print(f'PASS deployed multi-pass workflow: {actual} AI-composed packages, {len(packages)-actual} explicit factual fallbacks; independent publication/history/recap and rounding boundary verified',flush=True)
    if args.require_all_ai and actual!=len(packages):
        raise SystemExit('Strict AI wording check failed; full report retains fallback outcomes.')


if __name__=='__main__':main()
