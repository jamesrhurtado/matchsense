"""New feeds through the existing approval/variant/recap APIs in local mode.

The harness registers an opaque session directly, because the deployed fixture
allowlist remains the original three demos. It does not provision Azure or alter
that public registry. HTTP routes, repository state and publication code are real.
"""
import time
import uuid

from fastapi.testclient import TestClient
import pytest

from engine.repository import Repository
from services.api import main
from simulator.scenarios import cases
from simulator.suite import generate_case


@pytest.mark.parametrize('family',[
    'escape','different_receiver','noisy_tracking','duplicates','delayed_outcome',
    'expired_outcome','reordered_delivery','correction_withdraws','correction_restores',
    'missing_pressure','unknown_possession','retention_gap','rounding_boundary',
])
def test_synthetic_feed_obeys_live_publication_boundaries(family,tmp_path,monkeypatch):
    case=next(c for c in cases('development') if c.family==family)
    ds=generate_case(case)
    monkeypatch.setattr(main,'repo',Repository(tmp_path/'state.db'))
    monkeypatch.setattr(main,'FOUNDRY',False)
    monkeypatch.setattr(main,'transport',None)
    monkeypatch.setattr(main,'JOBS',{})
    def load(mid):
        assert mid==ds.metadata['match_id']
        return ds.metadata,ds.observations
    monkeypatch.setattr(main,'load_match',load)
    session=main.new_session(ds.metadata['match_id'])
    sid=session['id']
    base=f'/api/replay-sessions/{sid}'
    headers={'X-Producer-Token':main.TOKEN}
    with TestClient(main.app) as client:
        assert client.get(base+'/diagnostics').status_code==401
        for check in ds.reference['checks']:
            session=main.repo.get_session(sid)
            session.update(clock_ms=check['at_ms'],running=False,updated_at=time.time())
            main.repo.save_session(session)
            producer=client.get(base+'/snapshot',headers=headers).json()
            public=client.get(base+'/snapshot').json()
            if check['expected_pass_ids']:
                assert producer['story'] and producer['story_status'] in ('ready','approved')
                story=producer['story']
                response=client.post(base+f'/stories/{story["id"]}/review',headers=headers,json={
                    'action':'approve','expected_revision':story['revision'],'package_hash':story['package_hash'],
                    'idempotency_key':str(uuid.uuid4()),
                })
                assert response.status_code==200,response.text
                assert client.get(base+'/snapshot').json()['overlay']
                assert client.post(base+'/recaps',json={}).json()['moments']
                player=ds.reference['plays'][0]['actual_receiver_id']
                actual_name=next(p['name'] for p in ds.metadata['players'] if p['id']==player)
                variant=client.get(base+f'/stories/{story["id"]}/variants',params={
                    'language':'es','detail':'detail','focus':player,
                }).json()
                assert actual_name in variant['text'] and 'recibió' in variant['text']
            else:
                assert public['overlay'] is None,(family,check,public)
                if check['at_ms']<ds.reference['plays'][0]['expires_at_ms']:
                    assert producer['story'] is None,(family,check,producer)
                if family=='correction_withdraws' and check['at_ms']>=ds.reference['plays'][0]['confirmation_ms']+4000:
                    assert not client.post(base+'/recaps',json={}).json()['moments']
                    assert main.repo.decision(sid)['status']=='superseded'
