"""Acceptance ledger durability across interrupted writes and exact retries."""
from copy import deepcopy

import pytest

from engine.cloud_repository import CosmosRepository, RepositoryConflict
from engine.dispositions import package_events, reconcile_acceptances
from engine.outcomes import create_outcome, finish_outcome, start_outcome
from engine.repository import Repository
from services.api import main
from tests.test_cloud import Client, package


@pytest.fixture(params=['sqlite', 'cosmos'])
def repository(request, tmp_path, monkeypatch):
    repo = Repository(tmp_path / 'recovery.db') if request.param == 'sqlite' else CosmosRepository(client=Client())
    repo.save_session({'id': 'session'})
    monkeypatch.setattr(main, 'repo', repo)
    return repo


def completed(repo, revision=1, package_hash=None):
    candidate = package(revision)
    if package_hash:
        candidate['package_hash'] = package_hash
    outcome = create_outcome(repo, 'session', 'story', 'evidence', revision, 22000, 'test')
    outcome = start_outcome(repo, outcome)
    outcome = finish_outcome(repo, outcome, 'produced', package=candidate,
                             usage={'calls': 2, 'input_tokens': 500, 'output_tokens': 50,
                                    'total_tokens': 550, 'usage_complete': True},
                             trace=[{'role': 'Director'}, {'role': 'Reviewer'}])
    return candidate, outcome


def acceptances(repo):
    return [e for e in repo.lifecycle_events('session') if e.get('state') == 'accepted']


def test_package_and_acceptance_roll_back_together(repository, monkeypatch):
    candidate, outcome = completed(repository)
    events = package_events(repository, 'session', candidate, 'accepted', 23000)
    if isinstance(repository, Repository):
        with repository.connect() as c:
            c.execute("CREATE TRIGGER fail_acceptance BEFORE INSERT ON lifecycle_events BEGIN SELECT RAISE(ABORT, 'injected_crash'); END")
    else:
        original = repository.stories.create_item
        def fail_acceptance(body):
            if body.get('type') == 'lifecycle_event':
                raise RuntimeError('injected_crash')
            return original(body)
        monkeypatch.setattr(repository.stories, 'create_item', fail_acceptance)
    with pytest.raises(Exception, match='injected_crash'):
        repository.store_package('session', candidate, 23000, 0, acceptance_events=events)
    assert repository.latest_package('session') is None
    assert repository.stored_package('session', 'story', 1) is None
    assert repository.audit('session') == []
    assert acceptances(repository) == []
    assert repository.workflow_outcomes('session') == [outcome]
    assert reconcile_acceptances(repository) == 0


def test_restart_repairs_old_gap_even_after_revision_superseded(repository):
    first, first_outcome = completed(repository)
    # Simulate the former two-step implementation crashing after package storage.
    repository.store_package('session', first, 23000, 0)
    second, second_outcome = completed(repository, 2)
    main.accept_package('session', second, 24000, 1)
    repository.commit_review('session', 'approve-second', 'request', 2,
                            second['package_hash'], second, 'approved', 24500, {'revision': 2})
    before_decision = deepcopy(repository.decision('session'))
    before_audit = deepcopy(repository.audit('session'))
    assert reconcile_acceptances(repository) == 1
    assert reconcile_acceptances(repository) == 0
    recovered = next(e for e in acceptances(repository) if e['run_id'] == first_outcome['run_id'])
    assert recovered['recovered'] is True and recovered['replay_ms'] == 23000
    assert recovered['package_ref']['revision'] == 1
    assert repository.latest_package('session') == second
    assert repository.decision('session') == before_decision
    assert repository.audit('session') == before_audit
    assert repository.workflow_outcomes('session') == [first_outcome, second_outcome]


def test_response_loss_and_exact_retry_do_not_duplicate_or_reset_approval(repository, monkeypatch):
    candidate, outcome = completed(repository)
    original = repository.store_package
    def lose_response(*args, **kwargs):
        original(*args, **kwargs)
        raise TimeoutError('response_lost_after_commit')
    monkeypatch.setattr(repository, 'store_package', lose_response)
    main.accept_package('session', candidate, 23000, 0)
    repository.commit_review('session', 'approve', 'request', 1, candidate['package_hash'],
                            candidate, 'approved', 23500, {'revision': 1})
    main.accept_package('session', candidate, 24000, 0)
    assert len(acceptances(repository)) == 1
    assert not any(e.get('state') == 'persistence_failed' for e in repository.lifecycle_events('session'))
    assert len([e for e in repository.audit('session') if e['action'] == 'package_ready']) == 1
    assert repository.decision('session')['status'] == 'approved'
    assert repository.workflow_outcomes('session') == [outcome]


def test_recovery_never_accepts_unstored_or_hash_mismatched_workflows(repository):
    candidate, stored = completed(repository)
    repository.store_package('session', candidate, 23000, 0)
    _, unstored = completed(repository, 2)
    _, wrong_hash = completed(repository, 1, 'f' * 64)
    assert reconcile_acceptances(repository) == 1
    assert [e['run_id'] for e in acceptances(repository)] == [stored['run_id']]
    assert repository.workflow_outcomes('session') == [stored, unstored, wrong_hash]
    assert repository.decision('session') is None


def test_stale_acceptance_cannot_republish_or_mark_new_outcome_accepted(repository):
    first, _ = completed(repository)
    main.accept_package('session', first, 23000, 0)
    second, _ = completed(repository, 2)
    main.accept_package('session', second, 24000, 1)
    repository.commit_review('session', 'approve-new', 'request', 2, second['package_hash'],
                            second, 'approved', 24500, {'revision': 2})
    before_events = deepcopy(repository.lifecycle_events('session'))
    with pytest.raises(RepositoryConflict, match='stale_revision'):
        main.accept_package('session', first, 25000, 0)
    assert repository.latest_package('session') == second
    assert repository.decision('session')['revision'] == 2
    assert repository.lifecycle_events('session') == before_events
