"""Hand-authored references independent of production metric/generator functions."""
from copy import deepcopy
import json
import time
import uuid
import pytest
from fastapi.testclient import TestClient
from engine.core import load_match, digest
from engine.contracts import OBSERVATION
from engine.match_state import match_state
from engine.event_metrics import possession_window, event_metrics
from engine.event_narrative import build_event_package, EventPackage, read_package
from engine.repository import Repository
from engine.cloud_repository import CosmosRepository
from test_cloud import Client
from services.api import main

MID='match-0c0a000000000001'
META=load_match('match-001')[0]
HEAD={'X-Producer-Token':main.TOKEN}


def event(t,kind,details,team='blue',player=None,identity=None,revision=1,supersedes=None,ready=None):
    identity=identity or f'{kind}-{t}-{revision}'
    return {'schema_version':'1.0.0','match_id':META['match_id'],'message_id':identity,'sequence_no':t+revision,
            'timeline_ms':t,'period':1,'period_elapsed_ms':t,'available_at_ms':ready if ready is not None else t,
            'revision':revision,'supersedes_message_id':supersedes,'kind':'event',
            'payload':{'event_id':identity,'type':kind,'team_id':team,'player_id':player,'possession_id':None,'details':details}}


def goal(status='confirmed',team='blue',scorer=None,**kw):
    return event(1000,'goal_status_changed',{'goal_id':'g1','status':status,'scorer_id':scorer,'shot_id':None,'own_goal':bool(scorer and scorer.startswith('amber'))},team,**kw)


def frame(t,team='blue',status='in_flight',period=1):
    return {'schema_version':'1.0.0','match_id':META['match_id'],'message_id':f'f-{t}','sequence_no':t,
            'timeline_ms':t,'period':period,'period_elapsed_ms':t,'available_at_ms':t,'revision':1,'supersedes_message_id':None,
            'kind':'tracking_frame','payload':{'frame_id':f'f-{t}','players':[],'missing_player_ids':[],
            'ball':None,'ball_status':status,'controlling_player_id':None,'possession_team_id':team}}


def family(rows,cutoff,name):return [m for m in event_metrics(META,rows,cutoff) if m['family']==name]


@pytest.mark.parametrize('status,expected',[('pending',0),('confirmed',1),('cancelled',0)])
def test_goal_status_never_depends_on_editorial_approval(status,expected):
    rows=[goal(status)]
    OBSERVATION.validate_python(rows[0])
    assert match_state(META,rows,999)['score']['blue']==0
    assert match_state(META,rows,1000)['score']['blue']==expected
    assert bool(family(rows,1000,'goal'))==(status=='confirmed')


def test_goal_duplicate_reorder_team_correction_cancellation():
    first=goal(identity='first')
    changed=goal(team='amber',identity='changed',revision=2,supersedes='first',ready=2000)
    cancelled=goal('cancelled',team='amber',identity='cancelled',revision=3,supersedes='changed',ready=3000)
    rows=[cancelled,changed,first,first,changed]
    assert match_state(META,rows,1500)['score']=={'blue':1,'amber':0}
    assert match_state(META,rows,2500)['score']=={'blue':0,'amber':1}
    assert match_state(META,list(reversed(rows)),3500)['score']=={'blue':0,'amber':0}
    assert not family(rows,3500,'goal')


def test_own_goal_unknown_scorer_and_no_shot():
    for scorer in ['amber-09',None]:
        m=family([goal(scorer=scorer)],1000,'goal')[0]
        assert m['participants']['scorer']==scorer
        p=build_event_package(m,META)
        assert ('Own goal' in p['variants'][0]['text'])==bool(scorer)
        assert match_state(META,[goal(scorer=scorer)],1000)['score']['blue']==1


@pytest.mark.parametrize('outcome',['saved','blocked','off_target','unknown','goal'])
def test_shot_cutoff_outcomes_and_missing_confirmation(outcome):
    start=event(100,'shot_started',{'shot_id':'s1','location':None},player=None)
    end=event(200,'shot_resolved',{'shot_id':'s1','outcome':outcome},ready=300)
    assert not family([start,end],299,'shot')
    m=family([end,start,end],300,'shot')[0]
    assert m['facts']['outcome']==('unknown' if outcome=='goal' else outcome)
    assert m['participants']['shooter'] is None
    assert match_state(META,[start,end],300)['score']=={'blue':0,'amber':0}
    assert not family([end],300,'shot')


def test_shot_correction_changes_only_its_revision():
    start=event(100,'shot_started',{'shot_id':'s1','location':{'x_m':10,'y_m':20}},player='blue-09')
    end=event(200,'shot_resolved',{'shot_id':'s1','outcome':'saved'},identity='end')
    correction=event(200,'shot_resolved',{'shot_id':'s1','outcome':'blocked'},identity='corrected',revision=2,supersedes='end',ready=500)
    before=family([start,end,correction],400,'shot')[0];after=family([start,end,correction],500,'shot')[0]
    assert before['facts']['outcome']=='saved' and after['facts']['outcome']=='blocked'
    assert before['evidence_revision']!=after['evidence_revision']


def test_time_integration_irregular_cadence_inflight_and_denominators():
    # Hand reference: 40 s blue + 20 s amber; no frame counting weighting.
    rows=[frame(t,'blue' if t<40000 else 'amber') for t in range(0,60001,100)]
    rows=[r for r in rows if not (r['timeline_ms']<40000 and r['timeline_ms']%200==100)]
    w=possession_window(META,rows,60000,60000)
    assert w['team_ms']=={'blue':40000,'amber':20000}
    assert w['coverage']==1 and w['assigned_ms']==60000
    assert w['percentages']['blue']==pytest.approx(200/3)


def test_possession_dead_loose_unknown_gaps_duration_and_correction():
    rows=[frame(t,'blue','out_of_play' if t<10000 else 'loose' if t<15000 else 'in_flight') for t in range(0,60001,100)]
    w=possession_window(META,rows,60000,60000)
    assert (w['assigned_ms'],w['dead_ms'],w['loose_ms'],w['unknown_ms'])==(45000,10000,5000,0)
    assert w['percentages']=={'blue':100,'amber':0}
    assert possession_window(META,rows,60000,29000)['percentages'] is None
    # Missing 20000 through 23900 leaves a 4100ms gap (left interval not inherited).
    missing=[r for r in rows if not 20000<=r['timeline_ms']<24000]
    gap=possession_window(META,missing,60000,60000)
    assert gap['unknown_ms']==4100 and gap['percentages'] is None
    corrected=deepcopy(rows[200]);corrected.update(message_id='fixed',revision=2,supersedes_message_id=rows[200]['message_id'],available_at_ms=65000);corrected['payload']['possession_team_id']='amber'
    assert possession_window(META,rows+[corrected],65000,60000)['team_ms']['amber']==100


def test_period_boundary_no_extrapolation_and_stopped_clock():
    meta=deepcopy(META);meta['periods'].append({'period':2,'timeline_offset_ms':60000,'attack_direction':{'blue':'left','amber':'right'}})
    rows=[frame(t,period=2) for t in range(60000,75001,100)]
    w=possession_window(meta,rows,75000,75000)
    assert w['window_start_ms']==60000 and w['assigned_ms']==15000 and w['percentages'] is None
    assert possession_window(meta,rows[:-1],75000,75000)['unknown_ms']==100
    ended=event(500,'period_state_changed',{'status':'ended'},team=None)
    assert match_state(meta,[ended],1000)['period_elapsed_ms']==500
    assert match_state(meta,[ended],1000)['period_status']=='ended'


def test_recovery_team_change_restart_and_incident_dedup():
    recovery=event(1000,'ball_recovered',{'incident_id':'i1','previous_team_id':'amber','cause':'interception','pass_id':'p1'},player='blue-08')
    transition=event(1000,'possession_changed',{'incident_id':'i1','pass_id':'p1','previous_team_id':'amber','new_team_id':'blue','controlling_player_id':'blue-08','reason':'observed'})
    ms=family([recovery,transition,transition],1000,'recovery')
    assert len(ms)==1 and ms[0]['participants']=={'recovering_player':'blue-08'}
    team_only=family([transition],1000,'recovery')[0]
    assert team_only['facts']['kind']=='control_change' and team_only['participants']['recovering_player'] is None
    restart=deepcopy(transition);restart['payload']['details']['previous_team_id']=None
    assert family([restart],1000,'recovery')[0]['facts']['kind']=='restart'
    same=deepcopy(transition);same['payload']['details']['previous_team_id']='blue'
    assert not family([same],1000,'recovery')


def test_immediate_loss_never_claims_retention_and_recovery_correction():
    recovery=event(1000,'ball_recovered',{'incident_id':'i','previous_team_id':None,'cause':'loose_ball'},player='blue-08',identity='recovery')
    frames=[frame(t,'blue' if t<1500 else 'amber') for t in range(1000,4001,100)]
    m=family([recovery]+frames,4000,'recovery')[0]
    assert m['facts']['kind']=='recovery' and not m['facts']['sustained']
    retained=family([recovery]+[frame(t) for t in range(1000,4001,100)],4000,'recovery')[0]
    assert retained['facts']['sustained']
    revised=deepcopy(recovery);revised.update(message_id='new',revision=2,supersedes_message_id='recovery',available_at_ms=5000);revised['payload']['player_id']='blue-06'
    assert family([recovery,revised]+frames,5000,'recovery')[0]['participants']['recovering_player']=='blue-06'


@pytest.fixture(params=['sqlite','cosmos'])
def store(request,tmp_path):return Repository(tmp_path/'events.db') if request.param=='sqlite' else CosmosRepository(client=Client())


def test_v5_roundtrip_immutable_hashes_and_exact_decisions(store):
    m=family([goal()],1000,'goal')[0];p=build_event_package(m,META)
    store.store_package('s',p,1000,expected_revision=0)
    restored=store.latest_package('s',p['id']);assert restored==p
    read_package(restored)
    store.commit_review('s','approve-1','hash',1,p['package_hash'],p,'approved',1000,{'ok':True})
    assert store.decision('s',p['id'])['status']=='approved'
    store.invalidate('s',p['id']);assert store.stored_package('s',p['id'],1)==p
    assert store.decision('s',p['id'])['status']=='superseded'


def test_v5_tampering_cannot_cross_realizer_and_unknown_version_rejected():
    p=build_event_package(family([goal()],1000,'goal')[0],META)
    forged=deepcopy(p);forged['variants'][0]['text']='Invented assist and score 9-0.'
    forged['package_hash']=digest({k:v for k,v in forged.items() if k!='package_hash'})
    with pytest.raises(ValueError):EventPackage.model_validate(forged)
    forged=deepcopy(p);forged['claims'][0]['value']['status']='pending'
    with pytest.raises(ValueError):EventPackage.model_validate(forged)
    with pytest.raises(ValueError):read_package(p|{'schema_version':'6.0.0'})


@pytest.fixture
def client(store,monkeypatch):
    monkeypatch.setattr(main,'repo',store);monkeypatch.setattr(main,'COVERAGE',True);monkeypatch.setattr(main,'FOUNDRY',False)
    main.JOBS.clear()
    with TestClient(main.app) as c:yield c


def create(c,mid=MID):
    response=c.post('/api/replay-sessions',headers=HEAD,json={'match_id':mid});assert response.status_code==200,response.text
    return response.json()['session_id']


def at(sid,t):
    s=main.repo.get_session(sid);s.update(clock_ms=t,running=False,updated_at=time.time());main.repo.save_session(s)


def review(c,sid,p,action='approve',key=None):
    return c.post(f'/api/replay-sessions/{sid}/stories/{p["id"]}/review',headers=HEAD,json={'action':action,'expected_revision':p['revision'],'package_hash':p['package_hash'],'idempotency_key':key or str(uuid.uuid4())})


def package(c,sid,story):
    r=c.get(f'/api/replay-sessions/{sid}/stories/{story}/evidence',headers=HEAD);assert r.status_code==200,r.text
    return r.json()['story']


def test_api_all_families_approval_evidence_variants_history_recap_and_archive(client):
    sid=create(client)
    for t,story in [(25000,'story-pass-1'),(33000,'story-recovery-loose-1'),(47000,'story-shot-attempt-1'),(60000,'story-possession-60000'),(105000,'story-goal-goal-1')]:
        at(sid,t);p=package(client,sid,story)
        assert client.get(f'/api/replay-sessions/{sid}/stories/{story}/evidence').status_code==404
        response=review(client,sid,p);assert response.status_code==200,response.text
        assert review(client,sid,p,key='retry-key-'+str(t)).status_code==200
        assert client.get(f'/api/replay-sessions/{sid}/stories/{story}/evidence').status_code==200
        assert client.get(f'/api/replay-sessions/{sid}/stories/{story}/variants?language=es&detail=detail').status_code==200
    snap=client.get(f'/api/replay-sessions/{sid}/snapshot').json()
    assert snap['score']=={'blue':1,'amber':0}
    assert {s['family'] for s in snap['stories']}=={'pass','recovery','shot','possession','goal'}
    assert snap['overlay_story_id']=='story-goal-goal-1'
    recap=client.post(f'/api/replay-sessions/{sid}/recaps',json={}).json()
    assert len(recap['moments'])==5 and recap['match_state']['score']['blue']==1
    at(sid,150000);p=package(client,sid,'story-shot-attempt-2')
    assert review(client,sid,p).status_code==409
    assert review(client,sid,p,'approve_archive').status_code==200
    snap=client.get(f'/api/replay-sessions/{sid}/snapshot').json()
    assert snap['overlay_story_id'] is None
    # linked shot+goal collapse into one viewer incident while both packages persist.
    assert sum(s['incident_id']=='shot:attempt-2' for s in snap['stories'])==1
    assert len(client.post(f'/api/replay-sessions/{sid}/recaps',json={}).json()['moments'])==5


def test_api_score_cancellation_and_reapproval_unrelated_isolation(client):
    sid=create(client,'match-0c0a000000000002');at(sid,105000)
    shot=package(client,sid,'story-shot-attempt-1');assert review(client,sid,shot,'approve_archive').status_code==200
    goal_package=package(client,sid,'story-goal-goal-1');assert review(client,sid,goal_package).status_code==200
    attempt=package(client,sid,'story-shot-attempt-2');assert review(client,sid,attempt).status_code==200
    at(sid,136000);snap=client.get(f'/api/replay-sessions/{sid}/snapshot').json()
    assert snap['score']=={'blue':0,'amber':0}
    assert 'story-goal-goal-1' not in [s['id'] for s in snap['stories']]
    assert 'story-shot-attempt-2' not in [s['id'] for s in snap['stories']]
    assert 'story-shot-attempt-1' in [s['id'] for s in snap['stories']]
    assert review(client,sid,attempt).status_code==409
    new=package(client,sid,attempt['id']);assert new['revision']==attempt['revision']+1
    assert 'cancelled' in new['variants'][0]['text']
    assert review(client,sid,new).status_code==200
    assert main.repo.stored_package(sid,attempt['id'],attempt['revision'])==attempt
    recap=client.post(f'/api/replay-sessions/{sid}/recaps',json={}).json()
    assert not any(m['story_id']=='story-goal-goal-1' for m in recap['moments'])


def test_api_preconfirmation_score_and_protected_candidates_restart(client):
    sid=create(client);at(sid,102000)
    snap=client.get(f'/api/replay-sessions/{sid}/snapshot').json()
    assert snap['score']['blue']==0 and snap['stories']==[]
    at(sid,105000);p=package(client,sid,'story-goal-goal-1');assert review(client,sid,p).status_code==200
    # Restart recovery reuses immutable package and exact approval, no rewriting.
    main.repo.interrupt_workflow_outcomes()
    assert package(client,sid,p['id'])==p
    assert client.get(f'/api/replay-sessions/{sid}/snapshot').json()['score']['blue']==1
    assert review(client,sid,p,'retract').status_code==200
    assert client.get(f'/api/replay-sessions/{sid}/snapshot').json()['score']['blue']==1


def test_api_actor_team_focus_and_overlay_override(client):
    sid=create(client);at(sid,105000)
    ps=[package(client,sid,id) for id in ['story-goal-goal-1','story-shot-attempt-2']]
    for p in ps:assert review(client,sid,p).status_code==200
    p=ps[-1]
    assert client.post(f'/api/replay-sessions/{sid}/selection',headers=HEAD,json={'story_id':p['id'],'expected_revision':p['revision'],'package_hash':p['package_hash']}).status_code==200
    snap=client.get(f'/api/replay-sessions/{sid}/snapshot').json();assert snap['overlay_story_id']==p['id']
    assert len(snap['stories'])==1
    related=client.get(f'/api/replay-sessions/{sid}/stories/story-goal-goal-1/evidence').json()['related_stories']
    assert [row['id'] for row in related]==['story-shot-attempt-2']
    assert client.post(f'/api/replay-sessions/{sid}/recaps',json={'focus':'blue-09'}).json()['approved_count']==1
    assert client.post(f'/api/replay-sessions/{sid}/recaps',json={'focus':'blue-01'}).json()['approved_count']==0


@pytest.mark.parametrize('bad',[False,True])
def test_bounded_event_model_adapter_fake_reviewer_cannot_invent_facts(bad):
    from engine.structured_workflow import run_event_workflow
    from engine.workflow import EvidenceTools
    class Provider:
        async def complete(self,role,instructions,payload,schema,max_tokens):
            if bad and role=='Story Director':
                return {'action':'propose','claim_ids':['invented-assist'],'reason':'unsupported'},{}
            return {'action':'propose' if role=='Story Director' else 'supported','claim_ids':['c-event'],'reason':'supplied observations only'},{'input_token_count':20,'output_token_count':20,'total_token_count':40}
    tools=EvidenceTools(META,[goal()],1000)
    p=run_event_workflow(tools,'goal','g1',provider=Provider())
    assert p['mode']==('template fallback' if bad else 'Microsoft Agent Framework + Azure OpenAI')
    assert p['variants']==build_event_package(family([goal()],1000,'goal')[0],META)['variants']
    assert p['model_usage']['calls']==(1 if bad else 2)
    EventPackage.model_validate(p)


def test_model_correction_in_flight_cannot_commit_old_event(client,monkeypatch):
    from concurrent.futures import Future
    pending=[]
    class Worker:
        def submit(self,fn,*args):
            future=Future();pending.append((future,args));return future
    monkeypatch.setattr(main,'EVENT_MODEL',True);monkeypatch.setattr(main,'WORKERS',Worker())
    sid=create(client,'match-0c0a000000000002');at(sid,105000)
    assert client.get(f'/api/replay-sessions/{sid}/snapshot',headers=HEAD).status_code==200
    target=next((f,args) for f,args in pending if args[2]['family']=='goal')
    future,args=target;future.set_result(build_event_package(args[2],args[3],args[6]))
    at(sid,136000)
    snap=client.get(f'/api/replay-sessions/{sid}/snapshot',headers=HEAD).json()
    assert snap['score']['blue']==0
    assert all(s['id']!='story-goal-goal-1' for s in snap['stories'])
    assert main.repo.latest_package(sid,'story-goal-goal-1') is None


def test_feature_flag_disables_new_sessions_without_reinterpreting_existing_ones(client,monkeypatch):
    sid=create(client);at(sid,105000);p=package(client,sid,'story-goal-goal-1');assert review(client,sid,p).status_code==200
    monkeypatch.setattr(main,'COVERAGE',False)
    assert package(client,sid,p['id'])==p
    assert client.get(f'/api/replay-sessions/{sid}/snapshot').json()['story']['id']==p['id']
    assert client.post('/api/replay-sessions',headers=HEAD,json={'match_id':MID}).status_code==422


def test_snapshot_correction_invalidates_exact_approval_but_not_other_family(client,monkeypatch):
    sid=create(client);at(sid,60000)
    possession=package(client,sid,'story-possession-60000');shot=package(client,sid,'story-shot-attempt-1')
    assert review(client,sid,possession).status_code==200
    assert review(client,sid,shot).status_code==200
    meta,rows=load_match(MID);base=next(m for m in rows if m['kind']=='tracking_frame' and m['timeline_ms']==20000)
    corrected=deepcopy(base);corrected.update(message_id='corrected-frame',revision=2,supersedes_message_id=base['message_id'],available_at_ms=61000)
    corrected['payload'].update(ball_status='in_flight',controlling_player_id=None,possession_team_id='amber')
    original=main.inputs
    monkeypatch.setattr(main,'inputs',lambda session,at:(meta,rows+[corrected]) if session['id']==sid else original(session,at))
    at(sid,61000);updated=package(client,sid,possession['id'])
    assert updated['revision']==possession['revision']+1
    assert main.repo.decision(sid,possession['id'])['status']=='superseded'
    assert main.repo.decision(sid,shot['id'])['status']=='approved'
    assert main.repo.stored_package(sid,possession['id'],1)==possession


def test_archive_request_cannot_restore_overlay_and_is_idempotent(client):
    sid=create(client);at(sid,47000);p=package(client,sid,'story-shot-attempt-1')
    assert review(client,sid,p,'approve_archive').status_code==409
    at(sid,100000)
    first=review(client,sid,p,'approve_archive',key='archive-idempotent')
    second=review(client,sid,p,'approve_archive',key='archive-idempotent')
    assert first.status_code==200 and first.json()==second.json()
    assert client.get(f'/api/replay-sessions/{sid}/snapshot').json()['overlay'] is None


def test_possession_clips_explicit_period_end_instead_of_extrapolating():
    rows=[frame(t) for t in range(0,1001,100)]
    rows.append(event(500,'period_state_changed',{'status':'ended'},team=None))
    w=possession_window(META,rows,1000,1000)
    assert w['window_end_ms']==500 and w['assigned_ms']==500 and w['unknown_ms']==0


@pytest.mark.parametrize('action',['abstain','reject','fail','missing_verdict'])
def test_new_family_bounded_workflow_terminal_accounting(action):
    from engine.structured_workflow import run_event_workflow
    from engine.workflow import EvidenceTools
    events=[]
    class Provider:
        async def complete(self,role,instructions,payload,schema,max_tokens):
            if action=='fail':raise RuntimeError('provider unavailable')
            if action=='abstain' and role=='Story Director':return {'action':'abstain','claim_ids':[],'reason':'No editorial story'},{}
            if role=='Story Director':return {'action':'propose','claim_ids':['c-event'],'reason':'observed'},{}
            return {'action':'reject' if action=='reject' else 'supported','claim_ids':[] if action=='missing_verdict' else ['c-event'],'reason':'source review'},{}
    p=run_event_workflow(EvidenceTools(META,[goal()],1000),'goal','g1',provider=Provider(),outcome_callback=events.append)
    terminal=events[-1]
    assert terminal['state']=={'abstain':'abstained','reject':'rejected','fail':'fallback','missing_verdict':'fallback'}[action]
    assert terminal['usage']['calls']<=2
    assert (p is None)==(action in {'abstain','reject'})
    if p:
        assert p['mode']=='template fallback'
        assert p['variants'][0]['text']=='Confirmed goal for Harbor City. Scorer unidentified.'


def test_linked_incident_preserves_different_approved_shooter_and_scorer_roles(client,monkeypatch):
    sid=create(client);meta,rows=load_match(MID);changed=deepcopy(rows)
    for row in changed:
        if row['kind']=='event' and row['payload']['type']=='goal_status_changed':row['payload']['details']['scorer_id']='blue-08'
    original=main.inputs
    monkeypatch.setattr(main,'inputs',lambda s,t:(meta,changed) if s['id']==sid else original(s,t))
    at(sid,105000);goal=package(client,sid,'story-goal-goal-1');shot=package(client,sid,'story-shot-attempt-2')
    assert review(client,sid,goal).status_code==200
    snap=client.get(f'/api/replay-sessions/{sid}/snapshot').json();assert snap['stories'][0]['related_stories']==[]
    assert review(client,sid,shot).status_code==200
    snap=client.get(f'/api/replay-sessions/{sid}/snapshot').json();assert len(snap['stories'])==1
    assert snap['stories'][0]['participants']['scorer']=='blue-08'
    assert snap['stories'][0]['related_stories'][0]['participants']['shooter']=='blue-09'
    selected=client.get(f'/api/replay-sessions/{sid}/snapshot?story_id=story-shot-attempt-2').json()
    assert selected['story']['id']==shot['id']
    assert client.post(f'/api/replay-sessions/{sid}/recaps',json={'focus':'blue-09'}).json()['moments'][0]['story_id']==shot['id']


def test_goal_evidence_preserves_exact_historical_score_sources_after_other_goal_correction(client,monkeypatch):
    sid=create(client);meta,_=load_match(MID)
    first=goal(identity='first')
    second=event(2000,'goal_status_changed',{'goal_id':'g2','status':'confirmed'})
    cancelled=goal('cancelled',identity='cancel',revision=2,supersedes='first',ready=3000)
    rows=[first,second,cancelled]
    for row in rows:row['match_id']=MID
    original=main.inputs
    monkeypatch.setattr(main,'inputs',lambda s,t:(meta,rows) if s['id']==sid else original(s,t))
    at(sid,2500);p=package(client,sid,'story-goal-g2');assert review(client,sid,p).status_code==200
    at(sid,3500)
    state=client.get(f'/api/replay-sessions/{sid}/snapshot').json();assert state['score']['blue']==1
    evidence=client.get(f'/api/replay-sessions/{sid}/stories/{p["id"]}/evidence').json()
    assert evidence['cutoff_ms']==2000
    assert {row['message_id'] for row in evidence['events']}=={'first',second['message_id']}
    assert package(client,sid,p['id'])==p

@pytest.mark.parametrize('mid',['match-0c0a000000000003','match-0c0a000000000004'])
def test_versioned_moving_demo_uses_real_approval_pipeline_and_corrections(client,mid):
    sid=create(client,mid)
    assert client.get(f'/api/replay-sessions/{sid}/snapshot').json()['guided_demo'] is True
    stored=[]
    for t,story in [(25000,'story-pass-1'),(33000,'story-recovery-loose-1'),(47000,'story-shot-attempt-1'),(60000,'story-possession-60000'),(105000,'story-goal-goal-1')]:
        at(sid,t);p=package(client,sid,story);assert review(client,sid,p).status_code==200
        stored.append((p['id'],p['revision'],p['package_hash']))
    public=client.get(f'/api/replay-sessions/{sid}/snapshot').json()
    assert public['score']=={'blue':1,'amber':0}
    assert {s['family'] for s in public['stories']}=={'pass','recovery','shot','possession','goal'}
    recap=client.post(f'/api/replay-sessions/{sid}/recaps',json={}).json()
    assert len(recap['moments'])==5
    if mid.endswith('4'):
        at(sid,136000);corrected=client.get(f'/api/replay-sessions/{sid}/snapshot').json()
        assert corrected['score']=={'blue':0,'amber':0}
        assert all(s['family']!='goal' for s in corrected['stories'])
    for identity,revision,hash_ in stored:
        assert main.repo.stored_package(sid,identity,revision)['package_hash']==hash_
