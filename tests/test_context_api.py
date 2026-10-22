"""Context corrections cross producer/viewer boundaries without collateral revocation."""
from copy import deepcopy
import json
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from engine.core import load_match
from engine.repository import Repository
from engine.cloud_repository import CosmosRepository
from engine.narrative import build_structured_package
from engine.workflow import EvidenceTools
from services.api import main
from tests.test_cloud import Client
from tests.test_context import scene


@pytest.fixture(params=['sqlite','cosmos'])
def client(request,tmp_path,monkeypatch):
    monkeypatch.setattr(main,'repo', Repository(tmp_path/'context-api.db') if request.param=='sqlite' else CosmosRepository(client=Client()))
    monkeypatch.setattr(main,'FOUNDRY',False)
    monkeypatch.setattr(main,'STRUCTURED',True)
    monkeypatch.setattr(main,'transport',None)
    monkeypatch.setattr(main,'JOBS',{})
    with TestClient(main.app) as c:yield c

HEAD={'X-Producer-Token':main.TOKEN}


def approve(client,base,package):
    return client.post(f'{base}/stories/{package["id"]}/review',headers=HEAD,json={
        'action':'approve','expected_revision':package['revision'],'package_hash':package['package_hash'],
        'idempotency_key':str(uuid.uuid4())})


def seek(client,base,at):
    r=client.post(base+'/control',headers=HEAD,json={'action':'seek','clock_ms':at})
    assert r.status_code==200,r.text
    return client.get(base+'/snapshot',headers=HEAD).json()


def test_historical_correction_withdraws_context_story_preserves_unrelated_and_recap(client,monkeypatch):
    meta, rows=scene()
    _,original=load_match('match-001')
    for source in original:
        row=deepcopy(source)
        row.update(message_id='later-'+source['message_id'],timeline_ms=source['timeline_ms']+160000,
                   available_at_ms=source['available_at_ms']+160000,period_elapsed_ms=source['period_elapsed_ms']+160000,
                   sequence_no=source['sequence_no']+20000)
        if row['kind']=='event' and 'pass_id' in row['payload']['details']:
            row['payload']['details']['pass_id']='pass-2'
        rows.append(row)
    monkeypatch.setattr(main,'load_match',lambda _:(meta,rows))
    sid=client.post('/api/replay-sessions',headers=HEAD,json={'match_id':'match-001'}).json()['session_id']
    session=main.repo.get_session(sid);session['duration_ms']=240000;main.repo.save_session(session)
    base=f'/api/replay-sessions/{sid}'
    first=seek(client,base,25000)['story']
    assert 'previous three' in first['title']
    assert approve(client,base,first).status_code==200
    ev=client.get(base+'/stories/story-pass-1/evidence').json()
    assert [p['forward_m'] for p in ev['story']['metrics']['context']['comparators']]==[10,7,5]
    second=seek(client,base,185000)['story']
    assert second['id']=='story-pass-2'
    assert approve(client,base,second).status_code==200
    old=next(r for r in rows if r['message_id']=='history-2-end')
    correction=deepcopy(old)
    correction.update(message_id='late-history-fix',supersedes_message_id=old['message_id'],
                      revision=2,sequence_no=999999,available_at_ms=186000)
    correction['payload']['details']['end_position']['x_m']=60
    rows.append(correction)
    seek(client,base,187000)
    public=client.get(base+'/snapshot').json()
    assert [p['id'] for p in public['stories']]==['story-pass-2']
    assert main.repo.decision(sid,'story-pass-1')['status']=='superseded'
    assert main.repo.decision(sid,'story-pass-2')['status']=='approved'
    assert client.get(base+'/stories/story-pass-1/evidence').status_code==404
    recap=client.post(base+'/recaps',json={}).json()
    assert recap['approved_count']==1 and recap['moments'][0]['story_id']=='story-pass-2'
    assert approve(client,base,first).status_code==409
    events=main.repo.lifecycle_events(sid)
    assert any(e['kind']=='disposition' and e['state']=='superseded' for e in events)


def test_old_approved_v2_is_read_without_migration_or_hash_changes(client,monkeypatch):
    meta,rows=load_match('match-001')
    sid=client.post('/api/replay-sessions',headers=HEAD,json={'match_id':'match-001'}).json()['session_id']
    base=f'/api/replay-sessions/{sid}'
    legacy=build_structured_package(EvidenceTools(meta,rows,25000,'pass-1'))
    main.repo.store_package(sid,legacy,25000,expected_revision=0)
    p=seek(client,base,25000)['story']
    assert p['package_hash']==legacy['package_hash'] and p['revision']==1
    assert approve(client,base,p).status_code==200
    public=client.get(base+'/stories/story-pass-1/variants').json()
    assert public['text']==legacy['variants'][0]['text']
    assert main.repo.latest_package(sid,'story-pass-1')==legacy


def test_render_ack_is_bounded_deduplicated_and_has_no_publication_authority(client):
    sid=client.post('/api/replay-sessions',headers=HEAD,json={'match_id':'match-001'}).json()['session_id']
    base=f'/api/replay-sessions/{sid}'
    p=seek(client,base,25000)['story']
    body={'revision':p['revision'],'evidence_revision':p['evidence_revision'],'event_id':str(uuid.uuid4()),'paint_interval_ms':16.7}
    endpoint=base+'/stories/story-pass-1/render-ack'
    assert client.post(endpoint,json=body).status_code==404
    assert main.repo.decision(sid,p['id']) is None
    assert approve(client,base,p).status_code==200
    first=client.post(endpoint,json=body)
    assert first.status_code==200
    duplicate=client.post(endpoint,json={**body,'event_id':str(uuid.uuid4()),'paint_interval_ms':33})
    assert duplicate.json()==first.json()
    assert client.post(endpoint,json={**body,'revision':2}).status_code==409
    assert client.post(endpoint,json={**body,'paint_interval_ms':-1}).status_code==422
    assert client.post(base+'/stories/story-other/render-ack',json=body).status_code==404
    acks=[e for e in main.repo.lifecycle_events(sid) if e['kind']=='browser_ack']
    assert len(acks)==1 and acks[0]['paint_interval_ms']==16.7
    diag=client.get(base+'/diagnostics',headers=HEAD).json()
    assert diag['decision_summary']['angle']=='progression'
    assert 'insufficient history' in diag['decision_summary']['context']
    assert client.get(base+'/diagnostics').status_code==401


def test_editor_emphasis_creates_exact_reviewable_revision_and_rejects_unsupported_angle(client):
    sid=client.post('/api/replay-sessions',headers=HEAD,json={'match_id':'match-001'}).json()['session_id']
    base=f'/api/replay-sessions/{sid}';p=seek(client,base,25000)['story']
    assert approve(client,base,p).status_code==200
    endpoint=base+'/stories/story-pass-1/review'
    request={'action':'edit','angle':'reception','expected_revision':p['revision'],
             'package_hash':p['package_hash'],'idempotency_key':str(uuid.uuid4())}
    changed=client.post(endpoint,headers=HEAD,json=request)
    assert changed.status_code==200 and changed.json()['revision']==2
    assert client.get(base+'/snapshot').json()['story'] is None
    proposed=client.get(base+'/snapshot',headers=HEAD).json()['story']
    assert 'Sami Rios receives in the middle third'==proposed['title']
    assert approve(client,base,p).status_code==409
    assert approve(client,base,proposed).status_code==200
    impossible={**request,'angle':'historical_contrast','expected_revision':proposed['revision'],
                'package_hash':proposed['package_hash'],'idempotency_key':str(uuid.uuid4())}
    assert client.post(endpoint,headers=HEAD,json=impossible).status_code==422
    assert main.repo.decision(sid,'story-pass-1')['status']=='approved'
    assert client.post(endpoint,json=request).status_code==401
