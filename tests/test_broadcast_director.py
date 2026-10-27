import json
import time
import uuid

from fastapi.testclient import TestClient

from engine.broadcast_director import recommend
from engine.repository import Repository
from services.api import main


def candidate(identity, family='pass', status='ready'):
    return {'id': identity, 'family': family, 'status': status, 'revision': 1,
            'package_hash': 'a' * 64, 'eligible_from_ms': 1000,
            'expires_at_ms': 5000, 'occurrence_ms': 2000, 'title': identity}


class FakeProvider:
    def __init__(self, decision): self.decision = decision
    async def complete(self, role, instructions, payload, schema, max_tokens):
        assert role == 'Broadcast Producer'
        assert payload['stories']
        return json.dumps(self.decision), {'total_token_count': 10}


def test_director_restricts_model_to_live_candidates_and_labels_fallback():
    snap = {'clock_ms': 3000, 'overlay_story_id': None,
            'stories': [candidate('pass'), candidate('expired') | {'expires_at_ms': 2000}]}
    valid = FakeProvider({'action': 'show', 'story_id': 'pass', 'reason': 'Available pass.'})
    assert recommend(snap, [], True, valid)['mode'] == 'ai'
    forged = FakeProvider({'action': 'show', 'story_id': 'expired', 'reason': 'Choose old story.'})
    result = recommend(snap, [], True, forged)
    assert result['mode'] == 'fallback' and result['story_id'] == 'pass'
    assert recommend(snap | {'clock_ms': 6000}, [], False)['action'] == 'wait'


def test_question_requires_exact_approved_story_and_disappears_on_retraction(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'repo', Repository(tmp_path / 'test.db'))
    headers = {'X-Producer-Token': main.TOKEN}
    with TestClient(main.app) as client:
        sid = client.post('/api/replay-sessions', headers=headers, json={'match_id': 'match-001'}).json()['session_id']
        session = main.repo.get_session(sid)
        session.update(clock_ms=25000, running=False, updated_at=time.time())
        main.repo.save_session(session)
        story = client.get(f'/api/replay-sessions/{sid}/stories/story-pass-1/evidence', headers=headers).json()['story']
        selection = {'story_id': story['id'], 'expected_revision': story['revision'],
                     'package_hash': story['package_hash'], 'audience_group_id': 'g1'}
        session = main.repo.get_session(sid)
        session['audience'] = {'groups': [{'id': 'g1', 'question': 'What changed on the pass?',
            'state': 'open', 'association_confirmed': True, 'story_id': story['id'], 'story_revision': story['revision'],
            'story_hash': story['package_hash']}]}
        main.repo.save_session(session)
        url = f'/api/replay-sessions/{sid}/selection'
        assert client.post(url, json=selection, headers=headers).status_code == 409
        review = {'action': 'approve', 'expected_revision': story['revision'],
                  'package_hash': story['package_hash'], 'idempotency_key': str(uuid.uuid4())}
        assert client.post(f'/api/replay-sessions/{sid}/stories/{story["id"]}/review', json=review, headers=headers).status_code == 200
        assert client.post(url, json=selection, headers=headers).status_code == 200
        assert client.get(f'/api/replay-sessions/{sid}/snapshot').json()['overlay_question'] == 'What changed on the pass?'
        review.update(action='retract', idempotency_key=str(uuid.uuid4()))
        assert client.post(f'/api/replay-sessions/{sid}/stories/{story["id"]}/review', json=review, headers=headers).status_code == 200
        assert client.get(f'/api/replay-sessions/{sid}/snapshot').json()['overlay_question'] is None
        assert client.post(f'/api/replay-sessions/{sid}/broadcast/director').status_code == 401


def test_audience_rehearsal_to_approved_broadcast(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'repo', Repository(tmp_path / 'test.db'))
    headers = {'X-Producer-Token': main.TOKEN}
    with TestClient(main.app) as client:
        sid = client.post('/api/replay-sessions', headers=headers, json={'match_id': 'match-001'}).json()['session_id']
        session = main.repo.get_session(sid)
        session.update(clock_ms=25000, running=False, updated_at=time.time())
        main.repo.save_session(session)
        story = client.get(f'/api/replay-sessions/{sid}/stories/story-pass-1/evidence', headers=headers).json()['story']
        base = f'/api/replay-sessions/{sid}'
        response = client.post(base + '/audience/rehearsal', headers=headers, json={'messages': [
            {'text': 'What changed on the pass?', 'author_id': 'one'},
            {'text': 'What changed on the pass?', 'author_id': 'two'}]})
        assert response.status_code == 200, response.text
        group = response.json()['groups'][0]
        assert (group['message_count'], group['participant_count']) == (2, 2)
        association = {'story_id': story['id'], 'expected_revision': story['revision'],
                       'package_hash': story['package_hash']}
        selection = association | {'audience_group_id': group['id']}
        assert client.post(base + '/selection', headers=headers, json=selection).status_code == 409
        assert client.post(base + f'/audience/groups/{group["id"]}/associate', headers=headers, json=association).status_code == 200
        review = {'action': 'approve', 'expected_revision': story['revision'],
                  'package_hash': story['package_hash'], 'idempotency_key': str(uuid.uuid4())}
        assert client.post(base + f'/stories/{story["id"]}/review', headers=headers, json=review).status_code == 200
        assert client.post(base + '/selection', headers=headers, json=selection).status_code == 200
        public = client.get(base + '/snapshot').json()
        assert public['overlay_question'] == 'What changed on the pass?'
        assert public['overlay'] and public['overlay_story_id'] == story['id']
