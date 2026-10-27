from copy import deepcopy
import time
import uuid
import pytest
from fastapi.testclient import TestClient
from engine.repository import Repository
from services.api import main

HEAD={'X-Producer-Token':main.TOKEN}
@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'repo',Repository(tmp_path/'test.db'))
    with TestClient(main.app) as c:yield c

def create(c,match_id='match-001'):
    r=c.post('/api/replay-sessions',json={'match_id':match_id},headers=HEAD)
    assert r.status_code==200,r.text
    return r.json()['session_id']

def at(sid,t):
    s=main.repo.get_session(sid);s['clock_ms']=t;s['running']=False;s['updated_at']=time.time();main.repo.save_session(s)

def evidence(c,sid):return c.get(f'/api/replay-sessions/{sid}/stories/story-pass-1/evidence',headers=HEAD).json()['story']

def decision(c,sid,action='approve',package=None,key=None,text=None):
    p=package or evidence(c,sid)
    body={'action':action,'expected_revision':p['revision'],'package_hash':p['package_hash'],'idempotency_key':key or str(uuid.uuid4())}
    if text:body['text']=text
    return c.post(f'/api/replay-sessions/{sid}/stories/story-pass-1/review',json=body,headers=HEAD)

def test_viewer_cannot_create_reset_review_or_read_diagnostics(client):
    assert client.post('/api/replay-sessions',json={}).status_code==401
    sid=create(client);at(sid,25000)
    for url,body in [(f'/api/replay-sessions/{sid}/control',{'action':'reset'}),(f'/api/replay-sessions/{sid}/stories/story-pass-1/review',{'action':'approve','expected_revision':1,'package_hash':'a'*64,'idempotency_key':'not-authorized'})]:
        assert client.post(url,json=body).status_code==401
    assert client.get(f'/api/replay-sessions/{sid}/diagnostics').status_code==401
    assert client.get(f'/api/replay-sessions/{sid}/snapshot').json()['story'] is None
    assert client.get(f'/api/replay-sessions/{sid}/stories/story-pass-1/evidence').status_code==404


def test_complete_publication_variants_and_recap(client):
    sid=create(client);at(sid,25000);p=evidence(client,sid)
    assert decision(client,sid,package=p).status_code==200
    snap=client.get(f'/api/replay-sessions/{sid}/snapshot').json()
    assert snap['overlay'] and snap['story']['revision']==1
    variants=f'/api/replay-sessions/{sid}/stories/story-pass-1/variants'
    simple=client.get(variants).json();spanish=client.get(variants,params={'language':'es','detail':'detail','focus':'blue-08'}).json()
    assert '18.1 m forward' in simple['text'] and '3 rivales' in spanish['text']
    assert 'Theo Vega' in spanish['text']
    assert client.get(f'/api/replay-sessions/{sid}/snapshot').json()['overlay']==snap['overlay']
    recap=client.post(f'/api/replay-sessions/{sid}/recaps',json={}).json()
    assert len(recap['moments'])==1 and recap['through_ms']==25000
    unrelated=client.get(variants,params={'focus':'blue-01'}).json()
    assert 'No direct contribution' in unrelated['text']


def test_expiry_retraction_and_recap_invalidation(client):
    sid=create(client);at(sid,25000);assert decision(client,sid).status_code==200
    at(sid,53000);snap=client.get(f'/api/replay-sessions/{sid}/snapshot').json()
    assert snap['overlay'] is None and snap['story']['status']=='expired'
    assert len(client.post(f'/api/replay-sessions/{sid}/recaps',json={}).json()['moments'])==1
    assert decision(client,sid,'retract').status_code==200
    assert not client.post(f'/api/replay-sessions/{sid}/recaps',json={}).json()['moments']
    assert client.get(f'/api/replay-sessions/{sid}/snapshot').json()['story'] is None


def test_late_approval_is_rejected(client):
    sid=create(client);at(sid,54000)
    assert decision(client,sid).status_code==409


def test_edit_invalidates_approval_and_stale_requests(client):
    sid=create(client);at(sid,25000);old=evidence(client,sid);assert decision(client,sid,package=old).status_code==200
    edited=decision(client,sid,'edit',package=old,text='Club del Faro now controls the match.')
    assert edited.status_code==200 and edited.json()['review']['status']=='revised'
    assert client.get(f'/api/replay-sessions/{sid}/snapshot').json()['story'] is None
    stale=decision(client,sid,package=old)
    assert stale.status_code==409 and stale.json()['detail']['code']=='stale_revision'
    assert not client.post(f'/api/replay-sessions/{sid}/recaps',json={}).json()['moments']
    assert decision(client,sid).status_code==200
    assert client.get(f'/api/replay-sessions/{sid}/snapshot').json()['story']['revision']==2


def test_idempotency_does_not_duplicate_publications(client):
    sid=create(client);at(sid,25000);p=evidence(client,sid);key=str(uuid.uuid4())
    a=decision(client,sid,package=p,key=key);at(sid,55000);b=decision(client,sid,package=p,key=key)
    assert a.json()==b.json()
    assert [a['action'] for a in main.repo.audit(sid)].count('approve')==1
    assert decision(client,sid,'suppress',package=p,key=key).status_code==409


def test_sessions_reset_and_decisions_survive_repository_restart(client):
    a=create(client);b=create(client);at(a,25000);decision(client,a)
    assert client.get(f'/api/replay-sessions/{b}/snapshot').json()['story'] is None
    path=main.repo.path;main.repo=Repository(path)
    assert client.get(f'/api/replay-sessions/{a}/snapshot').json()['overlay']
    new=client.post(f'/api/replay-sessions/{a}/control',json={'action':'reset'},headers=HEAD).json()['session_id']
    assert new!=a and client.get(f'/api/replay-sessions/{new}/snapshot').json()['clock_ms']==0


def test_correction_supersedes_exact_approved_revision(client,monkeypatch):
    sid=create(client);at(sid,25000);decision(client,sid)
    meta,msgs=main.load_match('match-001');msgs=deepcopy(msgs)
    old=next(m for m in msgs if m['kind']=='tracking_frame' and m['timeline_ms']==17000)
    revised=deepcopy(old);revised.update(message_id='correction',supersedes_message_id=old['message_id'],revision=2,sequence_no=9000,available_at_ms=26000);revised['payload']['players'][0]['x_m']+=.1;msgs.append(revised)
    monkeypatch.setattr(main,'load_match',lambda _: (meta,msgs));at(sid,27000)
    public=client.get(f'/api/replay-sessions/{sid}/snapshot').json()
    assert public['overlay'] is None and public['story'] is None
    assert evidence(client,sid)['revision']==2
    assert not client.post(f'/api/replay-sessions/{sid}/recaps',json={}).json()['moments']


def test_suppression_and_invalid_preferences(client):
    sid=create(client);at(sid,25000);decision(client,sid,'suppress')
    assert client.get(f'/api/replay-sessions/{sid}/snapshot').json()['overlay'] is None
    decision(client,sid)
    assert client.get(f'/api/replay-sessions/{sid}/stories/story-pass-1/variants',params={'focus':'intruder'}).status_code==400
    assert client.get(f'/api/replay-sessions/{sid}/stories/story-pass-1/variants',params={'language':'xx'}).status_code==422


def test_negative_cases_stay_quiet(client):
    for mid in ['match-002','match-003']:
        sid=create(client,mid);at(sid,30000)
        assert client.get(f'/api/replay-sessions/{sid}/snapshot',headers=HEAD).json()['story'] is None


def test_recap_is_bounded_by_available_time(client):
    sid=create(client);at(sid,25000);decision(client,sid)
    early=client.post(f'/api/replay-sessions/{sid}/recaps',json={'through_ms':22000}).json()
    assert early['moments']==[]
    future=client.post(f'/api/replay-sessions/{sid}/recaps',json={'through_ms':60000}).json()
    assert future['through_ms']==25000


def test_correction_hides_approval_while_ai_review_is_pending(client,monkeypatch):
    from concurrent.futures import Future
    sid=create(client);at(sid,25000)
    old=evidence(client,sid)
    assert decision(client,sid,package=old).status_code==200
    meta,rows=main.load_match('match-001')
    changed=deepcopy(rows)
    source=next(m for m in changed if m['kind']=='tracking_frame' and m['timeline_ms']==18000)
    source['payload']['ball']['z_m']=.01
    assert main.metric(changed,25000,meta)['evidence_revision']!=old['evidence_revision']
    class Pending:
        def submit(self,*args,**kwargs):return Future()
    monkeypatch.setattr(main,'FOUNDRY',True)
    monkeypatch.setattr(main,'WORKERS',Pending())
    monkeypatch.setattr(main,'JOBS',{})
    monkeypatch.setattr(main,'inputs',lambda session,cutoff:(meta,changed))
    public=client.get(f'/api/replay-sessions/{sid}/snapshot').json()
    assert public['story'] is None and public['overlay'] is None
    assert public['workflow_pending'] is True
    assert decision(client,sid,package=old).status_code==404
