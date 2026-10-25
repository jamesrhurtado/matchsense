"""Interval and public-withdrawal checks on both persistence adapters."""
from copy import deepcopy
import pytest

from engine.editorial import observable_decision
from services.api import main
from test_match_coverage import client, store, create, at, package, review, HEAD


def test_interval_filters_occurrence_and_preserves_default_and_hashes(client):
    sid = create(client)
    base = f'/api/replay-sessions/{sid}'
    at(sid, 25000)
    first = package(client, sid, 'story-pass-1')
    assert review(client, sid, first).status_code == 200
    at(sid, 33000)
    second = package(client, sid, 'story-recovery-loose-1')
    assert review(client, sid, second).status_code == 200
    before = deepcopy(main.repo.list_packages(sid))
    all_ = client.post(base+'/recaps', json={}).json()
    recent = client.post(base+'/recaps', json={'from_ms': 30000, 'language': 'es'}).json()
    assert {m['story_id'] for m in all_['moments']} == {first['id'], second['id']}
    assert [m['story_id'] for m in recent['moments']] == [second['id']]
    assert recent['from_ms'] == 30000 and recent['through_ms'] == 33000
    assert recent['evaluated_at_ms'] == 33000
    boundary = second['metrics']['occurrence_ms']
    assert client.post(base+'/recaps', json={'from_ms': boundary}).json()['moments'][0]['story_id'] == second['id']
    assert main.repo.list_packages(sid) == before
    assert 'editorial_decision' not in client.get(base+'/snapshot').json()['story']
    producer = client.get(base+'/snapshot', headers=HEAD).json()['story']
    assert producer['editorial_decision']['director'] == 'factual_template'


def test_empty_future_invalid_focus_and_late_approval_intervals(client):
    sid = create(client); base = f'/api/replay-sessions/{sid}'
    at(sid, 25000); p = package(client, sid, 'story-pass-1')
    assert client.post(base+'/recaps', json={'from_ms': 0}).json()['moments'] == []
    assert review(client, sid, p).status_code == 200
    assert client.post(base+'/recaps', json={'through_ms': 20000}).json()['moments'] == []
    assert client.post(base+'/recaps', json={'from_ms': 25001}).status_code == 400
    assert client.post(base+'/recaps', json={'from_ms': -1}).status_code == 422
    assert client.post(base+'/recaps', json={'focus': 'not-a-player'}).status_code == 400
    result = client.post(base+'/recaps', json={'from_ms': 24000, 'through_ms': 999999}).json()
    assert result['through_ms'] == 25000 and result['moments'] == []


def test_correction_after_requested_interval_removes_copy_and_persists_notice(client):
    sid = create(client, 'match-0c0a000000000002'); base = f'/api/replay-sessions/{sid}'
    at(sid, 105000)
    goal = package(client, sid, 'story-goal-goal-1')
    assert review(client, sid, goal).status_code == 200
    assert client.post(base+'/recaps', json={'from_ms': 90000, 'through_ms': 110000}).json()['moments']
    at(sid, 136000)
    result = client.post(base+'/recaps', json={'from_ms': 90000, 'through_ms': 110000}).json()
    assert result['moments'] == [] and result['match_state']['score']['blue'] == 0
    assert result['correction_count'] == 1
    notice = result['corrections'][0]
    assert notice['at_ms'] > result['through_ms'] and notice['kind'] == 'source_changed'
    assert set(notice) == {'notice_id', 'story_id', 'at_ms', 'story_at_ms', 'family', 'kind', 'text'}
    assert 'Scorer' not in notice['text'] and 'Beni' not in notice['text']
    again = client.get(base+'/snapshot').json()['corrections']
    assert again == result['corrections']
    from engine.repository import Repository
    from engine.cloud_repository import CosmosRepository
    original = main.repo
    main.repo = Repository(original.path) if isinstance(original, Repository) else CosmosRepository(client=original.client)
    assert client.get(base+'/snapshot').json()['corrections'] == again
    assert main.repo.stored_package(sid, goal['id'], goal['revision']) == goal
    assert client.post(base+'/recaps', json={'from_ms': 0, 'through_ms': 10000}).json()['corrections'] == []
    assert client.post(base+'/recaps', json={'focus': 'amber-01'}).json()['corrections'] == []


def test_never_approved_source_changes_do_not_leak_candidates(client):
    sid = create(client, 'match-0c0a000000000002'); base = f'/api/replay-sessions/{sid}'
    at(sid, 105000); package(client, sid, 'story-goal-goal-1')
    at(sid, 136000)
    assert client.post(base+'/recaps', json={}).json()['corrections'] == []
    assert client.get(base+'/snapshot').json()['corrections'] == []


def test_manual_retraction_notice_does_not_claim_source_changed(client):
    sid = create(client); base = f'/api/replay-sessions/{sid}'
    at(sid, 25000); p = package(client, sid, 'story-pass-1')
    assert review(client, sid, p).status_code == 200
    assert review(client, sid, p, 'retract').status_code == 200
    result = client.post(base+'/recaps', json={'language': 'es'}).json()
    assert result['moments'] == [] and result['corrections'][0]['kind'] == 'producer_retracted'
    assert 'productor' in result['corrections'][0]['text']


def test_observable_agent_actions_do_not_publish_unvalidated_reasons():
    p = {'mode': 'Microsoft Agent Framework + Azure OpenAI', 'claims': [{'id': 'c-event'}],
         'trace': [{'role': 'Story Director', 'action': 'model_decision', 'status': 'propose', 'output': {'reason': 'invented cause'}},
                   {'role': 'Claim Reviewer', 'action': 'model_decision', 'status': 'supported'}]}
    summary = observable_decision(p)
    assert summary['director'] == 'selected' and summary['reviewer'] == 'supported'
    assert 'invented cause' not in str(summary)
    assert observable_decision(p | {'mode': 'template fallback'})['reviewer'] == 'factual_template'
