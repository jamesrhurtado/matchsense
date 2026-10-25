"""Live simulation contract: processing is independent of browser reads."""
import time
from concurrent.futures import Future
import pytest
from fastapi.testclient import TestClient
from engine.repository import Repository
from engine.outcomes import create_outcome, start_outcome, finish_outcome
from services.api import main

HEAD={'X-Producer-Token':main.TOKEN}
@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'repo',Repository(tmp_path/'live.db'))
    monkeypatch.setattr(main,'FOUNDRY',False)
    monkeypatch.setattr(main,'EVENT_MODEL',False)
    monkeypatch.setattr(main,'COVERAGE',True)
    monkeypatch.setattr(main,'JOBS',{})
    with TestClient(main.app) as c:yield c

def create(c,execution='template'):
    r=c.post('/api/replay-sessions',headers=HEAD,json={'match_id':'match-0c0a000000000005','mode':'live','execution':execution})
    assert r.status_code==200,r.text
    return r.json()['session_id']

def advance(sid,at):
    # Test-only clock injection, never used by continuous measurement scripts.
    with main.LOCK:
        s=main.repo.get_session(sid);s.update(clock_ms=at,running=True,updated_at=time.time());main.repo.save_session(s)
    main.live_tick()

def test_live_requires_explicit_template_when_ai_unavailable(client):
    r=client.post('/api/replay-sessions',headers=HEAD,json={'mode':'live'})
    assert r.status_code==503
    assert client.get('/api/health').json()['live_ai_configured'] is False

def test_session_mode_persisted_and_clock_is_protected(client):
    sid=create(client);base=f'/api/replay-sessions/{sid}'
    assert client.post(base+'/control',json={'action':'start'},headers=HEAD).status_code==200
    for body in [{'action':'pause'},{'action':'speed','speed':8},{'action':'seek','clock_ms':240000},{'action':'start','speed':8}]:
        assert client.post(base+'/control',json=body,headers=HEAD).status_code==409
    s=main.repo.get_session(sid)
    assert s['session_mode']=='live' and s['execution']=='template' and s['speed']==1
    fresh=client.post(base+'/control',json={'action':'reset'},headers=HEAD).json()['session_id']
    assert fresh!=sid and main.repo.get_session(fresh)['session_mode']=='live'
    assert client.post(base+'/control',json={'action':'start'}).status_code==401

def test_background_materializes_without_snapshot_and_survives_repository_reopen(client):
    sid=create(client)
    # Simulate restarting persistence at an eligible point, then leave no page open.
    s=main.repo.get_session(sid);s.update(clock_ms=17000,running=True,updated_at=time.time());main.repo.save_session(s)
    main.repo=Repository(main.repo.path)
    deadline=time.monotonic()+10
    while time.monotonic()<deadline and not main.repo.get_session(sid).get('last_processed_ms'):time.sleep(.1)
    packages=main.repo.list_packages(sid)
    assert packages and main.repo.get_session(sid)['last_processed_ms']>=17000
    assert all(p['metrics'].get('input_cutoff_ms',p['eligible_from_ms'])<=main.clock(main.repo.get_session(sid)) for p in packages)
    assert not any(p.get('family')=='goal' for p in packages)
    assert not main.repo.decision(sid,packages[0]['id'])
    snap=client.get(f'/api/replay-sessions/{sid}/snapshot').json()
    assert not snap['overlay'] and snap['session_mode']=='live'

def test_end_stops_without_new_session_and_never_invents_approval(client):
    sid=create(client);advance(sid,240000)
    snap=client.get(f'/api/replay-sessions/{sid}/snapshot').json()
    assert snap['live_status']=='complete' and not snap['running'] and snap['clock_ms']==240000
    assert snap['score']['blue']==1 and not snap['overlay']
    assert len(main.repo.list_sessions())==1

def test_restart_preserves_rejections_and_bounds_interrupted_retry(client):
    sid=create(client);s=main.repo.get_session(sid)
    o=start_outcome(main.repo,create_outcome(main.repo,sid,'story-pass-1','e',1,17000,'AI'))
    finish_outcome(main.repo,o,'rejected')
    assert main.live_attempt_blocked(s,'story-pass-1','e',18000)
    o=start_outcome(main.repo,create_outcome(main.repo,sid,'story-pass-2','e2',1,17000,'AI'))
    main.repo.interrupt_workflow_outcomes()
    assert not main.live_attempt_blocked(s,'story-pass-2','e2',18000)
    o=start_outcome(main.repo,create_outcome(main.repo,sid,'story-pass-2','e2',1,18000,'AI'))
    main.repo.interrupt_workflow_outcomes()
    assert main.live_attempt_blocked(s,'story-pass-2','e2',19000)

def test_ai_session_does_not_silently_become_template_after_restart(client):
    sid=create(client);s=main.repo.get_session(sid);s.update(execution='ai',running=True,clock_ms=17000);main.repo.save_session(s)
    main.live_tick()
    assert not main.repo.list_packages(sid)
    snap=client.get(f'/api/replay-sessions/{sid}/snapshot').json()
    assert snap['live_status']=='ai_unavailable' and snap['score']['blue']==0
    assert snap['mode']=='AI unavailable'

def test_stop_and_reset_end_old_work_preserving_history(client):
    sid=create(client);advance(sid,17000)
    original=main.repo.list_packages(sid)
    base=f'/api/replay-sessions/{sid}'
    assert client.post(base+'/control',headers=HEAD,json={'action':'stop'}).status_code==200
    assert not main.repo.get_session(sid)['running']
    assert client.get(base+'/snapshot').json()['live_status']=='stopped'
    assert client.post(base+'/control',headers=HEAD,json={'action':'start'}).status_code==409
    assert main.repo.list_packages(sid)==original
    fresh=client.post(base+'/control',headers=HEAD,json={'action':'reset'}).json()['session_id']
    assert main.repo.get_session(fresh)['running']
    assert not main.repo.get_session(sid)['running']

def test_explicit_template_on_ai_server_never_calls_model(client,monkeypatch):
    monkeypatch.setattr(main,'FOUNDRY',True);monkeypatch.setattr(main,'EVENT_MODEL',True)
    class Forbidden:
        def submit(self,*args,**kwargs):raise AssertionError('Template session invoked AI')
    monkeypatch.setattr(main,'WORKERS',Forbidden())
    sid=create(client);advance(sid,17000)
    assert main.repo.list_packages(sid)
    assert all(p['mode']=='local deterministic template' for p in main.repo.list_packages(sid))
    assert all(o['model_usage'].get('calls')==0 for o in main.repo.workflow_outcomes(sid))

def test_live_goal_correction_withdraws_exact_approval_and_recap(client):
    r=client.post('/api/replay-sessions',headers=HEAD,json={'match_id':'match-0c0a000000000006','mode':'live','execution':'template'});sid=r.json()['session_id'];base=f'/api/replay-sessions/{sid}'
    advance(sid,105000)
    p=main.repo.latest_package(sid,'story-goal-goal-1')
    body={'action':'approve','expected_revision':p['revision'],'package_hash':p['package_hash'],'idempotency_key':'live-goal-approve'}
    assert client.post(base+'/stories/'+p['id']+'/review',headers=HEAD,json=body).status_code==200
    advance(sid,136000)
    snap=client.get(base+'/snapshot').json()
    assert snap['score']['blue']==0
    assert all(story['id']!=p['id'] for story in snap['stories'])
    assert main.repo.stored_package(sid,p['id'],p['revision'])==p
    assert not any(row['story_id']==p['id'] for row in client.post(base+'/recaps',json={}).json()['moments'])

def test_backpressure_is_recorded_without_stalling_source_score(client,monkeypatch):
    monkeypatch.setattr(main,'FOUNDRY',True);monkeypatch.setattr(main,'EVENT_MODEL',True)
    monkeypatch.setenv('AZURE_OPENAI_ENDPOINT','https://example.invalid/');monkeypatch.setenv('FOUNDRY_MODEL_DEPLOYMENT','fake')
    monkeypatch.setattr(main,'JOBS',{('other',str(i),'e'):Future() for i in range(4)})
    sid=create(client,execution='ai');advance(sid,105000)
    s=client.get(f'/api/replay-sessions/{sid}/snapshot',headers=HEAD).json()
    assert s['score']['blue']==1 and s['running']
    assert any(n['state']=='capacity_deferred' for n in s['workflow_notices'])
    assert not main.repo.list_packages(sid)
    assert any(e.get('state')=='capacity_deferred' for e in main.repo.lifecycle_events(sid))

def test_live_correction_discards_a_completed_job_for_withdrawn_goal(client,monkeypatch):
    from engine.event_workflow import generate_event
    pending=[]
    class Worker:
        def submit(self,fn,*args,**kwargs):
            f=Future();pending.append((f,args));return f
    monkeypatch.setattr(main,'FOUNDRY',True);monkeypatch.setattr(main,'EVENT_MODEL',True)
    monkeypatch.setenv('AZURE_OPENAI_ENDPOINT','https://example.invalid/');monkeypatch.setenv('FOUNDRY_MODEL_DEPLOYMENT','fake')
    monkeypatch.setattr(main,'WORKERS',Worker())
    r=client.post('/api/replay-sessions',headers=HEAD,json={'match_id':'match-0c0a000000000006','mode':'live','execution':'ai'});sid=r.json()['session_id']
    advance(sid,105000)
    future,args=next((f,args) for f,args in pending if args[2].get('family')=='goal')
    # Inject a completed, source-rendered result. This is a scheduling test, not AI.
    future.set_result(generate_event(*args[:7],model=False,outcome=args[8]))
    advance(sid,136000)
    assert main.repo.latest_package(sid,'story-goal-goal-1') is None
    assert any(e.get('state')=='discarded_stale' and e.get('story_id')=='story-goal-goal-1' for e in main.repo.lifecycle_events(sid))


def test_live_injected_unsupported_selection_is_labeled_fallback_never_auto_published(client,monkeypatch):
    import engine.structured_workflow as structured
    class Provider:
        async def complete(self,*args,**kwargs):return {'action':'propose','claim_ids':['invented'],'reason':'disclosed injected invalid claim'}, {'input_token_count':10,'output_token_count':10,'total_token_count':20}
        async def close(self):pass
    monkeypatch.setattr(structured,'AgentFrameworkProvider',Provider)
    monkeypatch.setattr(main,'FOUNDRY',True);monkeypatch.setattr(main,'EVENT_MODEL',True)
    monkeypatch.setenv('AZURE_OPENAI_ENDPOINT','https://example.invalid/');monkeypatch.setenv('FOUNDRY_MODEL_DEPLOYMENT','fake')
    monkeypatch.setattr(main,'pass_metrics',lambda *args:[])
    sid=create(client,execution='ai');advance(sid,17000)
    deadline=time.monotonic()+10
    while time.monotonic()<deadline and not main.repo.list_packages(sid):time.sleep(.1)
    packages=main.repo.list_packages(sid)
    assert packages and all(p['mode']=='template fallback' for p in packages)
    assert all('invented' not in v['text'] for p in packages for v in p['variants'])
    assert all(o['state']=='fallback' for o in main.repo.workflow_outcomes(sid))
    assert client.get(f'/api/replay-sessions/{sid}/snapshot').json()['overlay'] is None

def test_live_state_works_through_cosmos_contract_adapter(client,monkeypatch):
    from engine.cloud_repository import CosmosRepository
    from test_cloud import Client
    store=Client();monkeypatch.setattr(main,'repo',CosmosRepository(client=store))
    sid=create(client);advance(sid,17000)
    assert main.repo.list_packages(sid)
    monkeypatch.setattr(main,'repo',CosmosRepository(client=store))
    snap=client.get(f'/api/replay-sessions/{sid}/snapshot',headers=HEAD).json()
    assert snap['session_mode']=='live' and snap['running'] and snap['stories']
    assert snap['execution']=='template' and not snap['overlay']
    assert client.post(f'/api/replay-sessions/{sid}/control',headers=HEAD,json={'action':'stop'}).status_code==200

def test_source_correction_withdraws_approval_even_when_ai_connection_is_lost(client):
    r=client.post('/api/replay-sessions',headers=HEAD,json={'match_id':'match-0c0a000000000006','mode':'live','execution':'template'});sid=r.json()['session_id'];base=f'/api/replay-sessions/{sid}'
    advance(sid,105000);p=main.repo.latest_package(sid,'story-goal-goal-1')
    body={'action':'approve','expected_revision':p['revision'],'package_hash':p['package_hash'],'idempotency_key':'before-ai-outage'}
    assert client.post(base+'/stories/'+p['id']+'/review',headers=HEAD,json=body).status_code==200
    s=main.repo.get_session(sid);s['execution']='ai';main.repo.save_session(s)
    advance(sid,136000)
    snap=client.get(base+'/snapshot').json()
    assert snap['live_status']=='ai_unavailable' and snap['score']['blue']==0
    assert snap['mode']=='AI unavailable'
    assert all(x['id']!=p['id'] for x in snap['stories'])
    assert main.repo.decision(sid,p['id'])['status']=='superseded'

def test_live_recovery_waits_for_existing_followup_without_new_model_revisions(client):
    sid=create(client);advance(sid,30000)
    assert main.repo.latest_package(sid,'story-recovery-loose-1') is None
    advance(sid,33000)
    p=main.repo.latest_package(sid,'story-recovery-loose-1')
    assert p and p['metrics']['facts']['sustained']
    assert len([o for o in main.repo.workflow_outcomes(sid) if o['story_id']==p['id']])==1

def test_pending_shot_deferral_does_not_delay_confirmed_source_score(client):
    sid=create(client);advance(sid,102000)
    assert main.repo.latest_package(sid,'story-shot-attempt-2') is None
    advance(sid,104000)
    assert main.repo.latest_package(sid,'story-shot-attempt-2')
    assert client.get(f'/api/replay-sessions/{sid}/snapshot').json()['score']['blue']==1
