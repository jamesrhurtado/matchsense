"""Multiple delivered passes remain independently scoped through publication."""
from concurrent.futures import Future
from copy import deepcopy
import time
import uuid

from fastapi.testclient import TestClient
import pytest

from engine.cloud_repository import CosmosRepository
from engine.core import load_match, metric, pass_metrics
from engine.repository import Repository
from engine.workflow import EvidenceTools, ToolError, run_workflow
from services.api import main
from simulator.scenarios import get_case
from tests.test_cloud import Client


HEAD={'X-Producer-Token':main.TOKEN}
MID=get_case('p01-28').match_id


@pytest.fixture(params=['sqlite','cosmos'])
def client(request,tmp_path,monkeypatch):
    monkeypatch.setattr(main,'repo',Repository(tmp_path/'multiple.db') if request.param=='sqlite' else CosmosRepository(client=Client()))
    monkeypatch.setattr(main,'FOUNDRY',False)
    monkeypatch.setattr(main,'transport',None)
    monkeypatch.setattr(main,'JOBS',{})
    with TestClient(main.app) as c:yield c


def create(client,mid=MID):
    r=client.post('/api/replay-sessions',headers=HEAD,json={'match_id':mid})
    assert r.status_code==200,r.text
    return r.json()['session_id']


def seek(client,sid,at):
    r=client.post(f'/api/replay-sessions/{sid}/control',headers=HEAD,json={'action':'seek','clock_ms':at})
    assert r.status_code==200,r.text
    assert r.json()['clock_ms']==at
    return client.get(f'/api/replay-sessions/{sid}/snapshot',headers=HEAD).json()


def decide(client,sid,story,action='approve'):
    return client.post(f'/api/replay-sessions/{sid}/stories/{story["id"]}/review',headers=HEAD,json={
        'action':action,'expected_revision':story['revision'],'package_hash':story['package_hash'],
        'idempotency_key':str(uuid.uuid4()),
    })


def test_three_passes_preserve_prior_approval_recap_and_selected_history(client):
    sid=create(client);base=f'/api/replay-sessions/{sid}'
    assert seek(client,sid,16199)['stories']==[]
    first=seek(client,sid,20000)
    assert first['duration_ms']==180000
    assert [p['id'] for p in first['stories']]==['story-pass-1']
    assert decide(client,sid,first['story']).status_code==200
    second=seek(client,sid,80000)
    assert [p['revision'] for p in second['stories']]==[1,1]
    assert second['stories'][0]['status']=='expired'
    assert second['story']['id']=='story-pass-2'
    assert decide(client,sid,second['story']).status_code==200
    public=client.get(base+'/snapshot').json()
    assert public['overlay_story_id']=='story-pass-2'
    old=client.get(base+'/snapshot',params={'story_id':'story-pass-1'}).json()
    assert old['story']['id']=='story-pass-1' and old['story_status']=='expired'
    assert old['overlay_story_id']=='story-pass-2'
    assert all('package_hash' not in p for p in old['stories'])
    ev=client.get(base+'/stories/story-pass-1/evidence').json()
    assert ev['story']['metrics']['pass_id']=='pass-1'
    assert len(client.post(base+'/recaps',json={}).json()['moments'])==2
    assert len(client.post(base+'/recaps',json={'through_ms':30000}).json()['moments'])==1
    assert decide(client,sid,first['story'],'retract').status_code==200
    public=client.get(base+'/snapshot',params={'story_id':'story-pass-1'}).json()
    assert [p['id'] for p in public['stories']]==['story-pass-2']
    assert public['overlay_story_id']=='story-pass-2' and public['overlay']
    assert client.get(base+'/stories/story-pass-1/evidence').status_code==404
    third=seek(client,sid,140000)
    assert third['story']['id']=='story-pass-3'
    assert decide(client,sid,third['story']).status_code==200
    recap=client.post(base+'/recaps',json={'language':'es'}).json()
    assert [p['story_id'] for p in recap['moments']]==['story-pass-2','story-pass-3']
    assert main.repo.decision(sid,'story-pass-2')['status']=='approved'
    assert main.repo.decision(sid,'story-pass-3')['status']=='approved'


def test_correction_of_one_pass_does_not_revoke_another(client,monkeypatch):
    sid=create(client);base=f'/api/replay-sessions/{sid}'
    first=seek(client,sid,20000)['story'];assert decide(client,sid,first).status_code==200
    second=seek(client,sid,80000)['story'];assert decide(client,sid,second).status_code==200
    metadata,rows=load_match(MID);rows=deepcopy(rows)
    old=next(m for m in rows if m['kind']=='tracking_frame' and m['timeline_ms']==16200)
    correction=deepcopy(old)
    correction.update(message_id='correction-first',sequence_no=10000,revision=2,
                      supersedes_message_id=old['message_id'],available_at_ms=81000)
    correction['payload']['ball']=None;rows.append(correction)
    monkeypatch.setattr(main,'load_match',lambda _:(metadata,rows))
    snap=seek(client,sid,82000)
    assert [p['id'] for p in snap['stories']]==['story-pass-2']
    assert snap['overlay_story_id']=='story-pass-2'
    assert main.repo.decision(sid,'story-pass-1')['status']=='superseded'
    assert main.repo.decision(sid,'story-pass-2')['status']=='approved'
    assert [p['story_id'] for p in client.post(base+'/recaps',json={}).json()['moments']]==['story-pass-2']


def test_seek_is_protected_forward_only_and_bounded(client):
    sid=create(client);base=f'/api/replay-sessions/{sid}'
    assert client.post(base+'/control',json={'action':'seek','clock_ms':20000}).status_code==401
    seek(client,sid,20000)
    assert client.post(base+'/control',headers=HEAD,json={'action':'seek','clock_ms':10000}).status_code==409
    response=client.post(base+'/control',headers=HEAD,json={'action':'seek','clock_ms':999999})
    assert response.status_code==200 and response.json()['clock_ms']==180000
    assert client.get(base+'/snapshot').json()['running'] is False
    assert client.post('/api/replay-sessions',headers=HEAD,json={'match_id':'../../etc/passwd'}).status_code==422


def test_later_pass_after_a_negative_first_is_investigated(client):
    mid=get_case('p01-27').match_id
    sid=create(client,mid)
    assert seek(client,sid,20000)['stories']==[]
    snapshot=seek(client,sid,52000)
    assert [p['id'] for p in snapshot['stories']]==['story-pass-2']
    assert snapshot['duration_ms']==90000


def test_investigation_tools_and_publication_ids_are_scoped_to_each_pass():
    metadata,rows=load_match(MID)
    measures=pass_metrics(rows,140000,metadata)
    assert [m['pass_id'] for m in measures]==['pass-1','pass-2','pass-3']
    for pass_id in ['pass-1','pass-2','pass-3']:
        tools=EvidenceTools(metadata,rows,140000,pass_id=pass_id)
        assert tools.compute_pass_metrics()['pass_id']==pass_id
        assert run_workflow(tools)['id']=='story-'+pass_id
        with pytest.raises(ToolError):tools.compute_pass_metrics('other-pass')
    assert metric(rows,140000,metadata,pass_id='unknown') is None
    assert [m['pass_id'] for m in pass_metrics(rows,76200-1,metadata)]==['pass-1','pass-2']
    assert pass_metrics(rows,76200-1,metadata)[-1]['eligible'] is False


def test_completed_out_of_order_model_jobs_commit_to_their_own_stories(client,monkeypatch):
    sid=create(client);session=main.repo.get_session(sid)
    meta,rows=load_match(MID)
    pending=[]
    class Worker:
        def submit(self,fn,tools,**kwargs):
            future=Future();pending.append((future,tools,kwargs));return future
    monkeypatch.setattr(main,'FOUNDRY',True)
    monkeypatch.setattr(main,'WORKERS',Worker())
    # Deliberately overlapping original deadlines for this scheduling-only test.
    monkeypatch.setattr(main,'pass_metrics',lambda messages,at,metadata:[m|{'retention_confirmed_at_ms':at} for m in pass_metrics(messages,at,metadata)])
    session.update(clock_ms=80000,running=False,updated_at=time.time());main.repo.save_session(session)
    assert main.materialize_all(session,80000)==[] and len(pending)==2
    future,tools,kwargs=pending[1];future.set_result(run_workflow(tools,revision=kwargs['revision']))
    result=main.materialize_all(session,80000)
    assert [p['id'] for p in result]==['story-pass-2']
    future,tools,kwargs=pending[0];future.set_result(run_workflow(tools,revision=kwargs['revision']))
    assert [p['id'] for p in main.materialize_all(session,80000)]==['story-pass-1','story-pass-2']
    assert main.repo.latest_package(sid,'story-pass-1')['revision']==1
    assert main.repo.latest_package(sid,'story-pass-2')['revision']==1


@pytest.mark.parametrize('pass_id',['pass-2','pass-3'])
def test_agent_tool_recheck_remains_on_selected_later_pass(pass_id):
    from engine.foundry_workflow import run_foundry_workflow
    from tests.test_foundry import FakeProvider,decision,editor,request
    meta,rows=load_match(MID)
    tools=EvidenceTools(meta,rows,140000,pass_id=pass_id)
    provider=FakeProvider([
        decision('needs_evidence',requests=[request('compute_pass_metrics',0,0)]),
        decision(),decision('supported'),editor(tools),decision('supported'),
    ])
    package=run_foundry_workflow(tools,provider=provider)
    assert package['mode']=='Microsoft Agent Framework + Azure OpenAI'
    assert package['id']=='story-'+pass_id
    assert provider.calls[1][2]['analyst_evidence'][0]['result']['pass_id']==pass_id
    assert all(call[2].get('metrics',{'pass_id':pass_id})['pass_id']==pass_id for call in provider.calls)
