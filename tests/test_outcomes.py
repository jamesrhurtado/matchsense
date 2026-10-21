"""SQLite/Cosmos workflow lifecycle accounting without cloud or model calls."""
from copy import deepcopy
import pytest

from engine.cloud_repository import CosmosRepository, RepositoryConflict
from engine.outcomes import create_outcome, start_outcome, finish_outcome, TERMINAL_STATES
from engine.repository import Repository
from tests.test_cloud import Client, Container


class OutcomeContainer(Container):
    """Extend the transaction emulator's SQL subset for workflow documents."""
    def query_items(self, query, partition_key=None, **kwargs):
        if '"workflow_outcome"' not in query:
            return super().query_items(query, partition_key, **kwargs)
        return [deepcopy(doc) for (sid, _), doc in self.items.items()
                if (partition_key is None or sid == partition_key)
                and doc.get('type') == 'workflow_outcome']


class OutcomeClient(Client):
    def get_container_client(self, name):
        return self.containers.setdefault(name, OutcomeContainer())


@pytest.fixture(params=['sqlite', 'cosmos'])
def repo(request, tmp_path):
    return (Repository(tmp_path / 'outcomes.db') if request.param == 'sqlite'
            else CosmosRepository(client=OutcomeClient()))


def scheduled(repo, sid='s'):
    return create_outcome(repo, sid, 'story-pass-2', 'source-hash', 1, 76200, 'agentic')


def test_lifecycle_preserves_all_attempts_and_independent_package_reference(repo):
    outcome = scheduled(repo)
    assert repo.workflow_outcomes('s') == [outcome]
    assert outcome['model_usage']['calls'] is None
    assert not outcome['model_usage']['usage_complete']
    active = start_outcome(repo, outcome)
    attempts = [{'attempt_id': 'a', 'status': 'malformed', 'input_tokens': 20},
                {'attempt_id': 'b', 'status': 'timeout', 'input_tokens': None}]
    usage = {'calls': 2, 'input_tokens': 20, 'output_tokens': None,
             'total_tokens': None, 'usage_complete': False}
    package = {'id': 'story-pass-2', 'revision': 1, 'package_hash': 'package-hash',
               'trace': attempts, 'model_usage': usage}
    done = finish_outcome(repo, active, 'fallback', package, reason='timeout')
    assert repo.workflow_outcomes('s') == [done]
    assert done['trace'] == attempts
    assert done['model_usage'] == usage
    assert done['package_ref']['package_hash'] == 'package-hash'
    assert done['timing']['job_started'] == done['started_at']
    assert done['timing']['candidate_ready'] == done['finished_at']
    assert repo.latest_package('s') is None  # Ledger never publishes a package.
    assert finish_outcome(repo, done, 'fallback', package, reason='timeout') == done


@pytest.mark.parametrize('state', sorted(TERMINAL_STATES))
def test_terminal_states_are_immutable_but_identical_retries_are_safe(repo, state):
    outcome = start_outcome(repo, scheduled(repo))
    done = finish_outcome(repo, outcome, state)
    repo.save_workflow_outcome('s', deepcopy(done))
    changed = deepcopy(done)
    changed['reason'] = 'replacement'
    with pytest.raises(RepositoryConflict, match='workflow_outcome_conflict'):
        repo.save_workflow_outcome('s', changed)
    with pytest.raises(RepositoryConflict):
        repo.save_workflow_outcome('s', outcome)
    assert repo.workflow_outcomes('s') == [done]


def test_restart_interrupts_active_runs_and_preserves_known_usage(repo):
    queued = scheduled(repo)
    active = start_outcome(repo, scheduled(repo, 'other-session'))
    active['model_usage'] = {'calls': 1, 'input_tokens': 9, 'output_tokens': 3,
                             'total_tokens': 12, 'usage_complete': True}
    active['trace'] = [{'attempt_id': 'a', 'status': 'completed'}]
    repo.save_workflow_outcome('other-session', active)
    done = finish_outcome(repo, start_outcome(repo, scheduled(repo)), 'abstained')
    assert repo.interrupt_workflow_outcomes() == 2
    assert repo.interrupt_workflow_outcomes() == 0
    by_id = {o['run_id']: o for o in repo.workflow_outcomes('s')}
    assert by_id[done['run_id']] == done
    assert by_id[queued['run_id']]['state'] == 'interrupted'
    assert by_id[queued['run_id']]['model_usage']['total_tokens'] is None
    interrupted = repo.workflow_outcomes('other-session')[0]
    assert interrupted['model_usage']['total_tokens'] == 12
    assert interrupted['model_usage']['usage_complete'] is False
    assert interrupted['trace'] == active['trace']


def test_identity_and_session_isolation(repo):
    active = start_outcome(repo, scheduled(repo))
    with pytest.raises(ValueError, match='session mismatch'):
        repo.save_workflow_outcome('wrong-session', active)
    for field, value in [('story_id', 'different'), ('evidence_revision', 'different'),
                         ('cutoff_ms', 80000), ('revision', 2)]:
        changed = deepcopy(active)
        changed[field] = value
        with pytest.raises(RepositoryConflict):
            repo.save_workflow_outcome('s', changed)
    assert repo.workflow_outcomes('wrong-session') == []
    assert repo.workflow_outcomes('s') == [active]


def test_active_state_cannot_regress(repo):
    queued = scheduled(repo)
    start_outcome(repo, queued)
    with pytest.raises(RepositoryConflict):
        repo.save_workflow_outcome('s', queued)


def test_attempt_checkpoint_cannot_discard_known_consumption(repo):
    active = start_outcome(repo, scheduled(repo))
    active['trace'] = [{'attempt_id': 'first', 'status': 'completed'}]
    active['model_usage'] = {'calls': 1, 'input_tokens': 9, 'output_tokens': 3,
                             'total_tokens': 12, 'usage_complete': True}
    repo.save_workflow_outcome('s', active)
    dropped_trace = deepcopy(active)
    dropped_trace['trace'] = []
    with pytest.raises(RepositoryConflict):
        repo.save_workflow_outcome('s', dropped_trace)
    dropped_usage = deepcopy(active)
    dropped_usage['model_usage']['total_tokens'] = None
    with pytest.raises(RepositoryConflict):
        repo.save_workflow_outcome('s', dropped_usage)
    assert repo.workflow_outcomes('s') == [active]


def test_cosmos_terminal_completion_race_cannot_be_overwritten():
    repo = CosmosRepository(client=OutcomeClient())
    active = start_outcome(repo, scheduled(repo))
    done = finish_outcome(repo, active, 'produced')
    # Restore active in the emulator to arrange two writers who read it together.
    item = 'run:' + active['run_id']
    repo.stories.upsert_item(repo._doc('s', item, 'workflow_outcome', active))
    def competing_completion():
        repo.stories.upsert_item(repo._doc('s', item, 'workflow_outcome', done))
    repo.stories.before_batch = competing_completion
    with pytest.raises(RepositoryConflict):
        finish_outcome(repo, active, 'failed', reason='losing worker')
    assert repo.workflow_outcomes('s') == [done]


def test_cosmos_identical_completion_race_is_idempotent():
    repo = CosmosRepository(client=OutcomeClient())
    active = start_outcome(repo, scheduled(repo))
    done = finish_outcome(repo, active, 'produced')
    item = 'run:' + active['run_id']
    repo.stories.upsert_item(repo._doc('s', item, 'workflow_outcome', active))
    def competing_completion():
        repo.stories.upsert_item(repo._doc('s', item, 'workflow_outcome', done))
    repo.stories.before_batch = competing_completion
    repo.save_workflow_outcome('s', done)
    assert repo.workflow_outcomes('s') == [done]
