"""Durable workflow lifecycle, independent of publishable story packages.

Timestamps are UTC wall clock values. Replay cutoffs remain in ``cutoff_ms``;
wall clock values must never be subtracted from replay times. Missing provider
usage is unknown (null), never an inferred zero. No credentials belong here.
"""
from copy import deepcopy
from datetime import datetime, timezone
import uuid

ACTIVE_STATES = frozenset({'scheduled', 'started'})
TERMINAL_STATES = frozenset({'produced', 'abstained', 'rejected', 'fallback',
                             'failed', 'cancelled', 'stale', 'interrupted'})
_IDENTITY = ('run_id', 'session_id', 'story_id', 'evidence_revision', 'revision',
             'cutoff_ms', 'mode', 'scheduled_at')


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def validate_outcome(session_id, outcome, previous=None):
    """Validate lifecycle writes in both adapters, including immutable terminals."""
    from engine.cloud_repository import RepositoryConflict
    if outcome.get('session_id') != session_id:
        raise ValueError('workflow outcome session mismatch')
    uuid.UUID(outcome['run_id'])
    if outcome.get('state') not in ACTIVE_STATES | TERMINAL_STATES:
        raise ValueError('invalid workflow outcome state')
    for key in _IDENTITY:
        if key not in outcome:
            raise ValueError('missing workflow outcome field: ' + key)
    if previous:
        if any(outcome[key] != previous[key] for key in _IDENTITY):
            raise RepositoryConflict('workflow_outcome_conflict')
        if previous['state'] in TERMINAL_STATES and outcome != previous:
            raise RepositoryConflict('workflow_outcome_conflict')
        if previous['state'] == 'started' and outcome['state'] == 'scheduled':
            raise RepositoryConflict('workflow_outcome_conflict')
        if previous.get('started_at') and outcome.get('started_at') != previous['started_at']:
            raise RepositoryConflict('workflow_outcome_conflict')
        prior_trace = previous.get('trace', [])
        if prior_trace and outcome.get('trace', [])[:len(prior_trace)] != prior_trace:
            raise RepositoryConflict('workflow_outcome_conflict')
        for field in ('calls', 'input_tokens', 'output_tokens', 'total_tokens'):
            known = previous.get('model_usage', {}).get(field)
            incoming = outcome.get('model_usage', {}).get(field)
            if known is not None and (incoming is None or incoming < known):
                raise RepositoryConflict('workflow_outcome_conflict')


def create_outcome(repo, session_id, story_id, evidence_revision, revision, cutoff_ms, mode):
    now = utc_now()
    outcome = {
        'run_id': str(uuid.uuid4()), 'session_id': session_id, 'story_id': story_id,
        'evidence_revision': evidence_revision, 'revision': revision,
        'cutoff_ms': cutoff_ms, 'mode': mode, 'state': 'scheduled',
        'scheduled_at': now, 'started_at': None, 'finished_at': None,
        'timing': {'job_enqueued': now, 'job_started': None, 'candidate_ready': None},
        'model_usage': {'calls': None, 'input_tokens': None, 'output_tokens': None,
                        'total_tokens': None, 'usage_complete': False},
        'trace': [], 'reason': None, 'package_ref': None,
    }
    repo.save_workflow_outcome(session_id, outcome)
    return outcome


def start_outcome(repo, outcome):
    if outcome['state'] != 'scheduled':
        if outcome['state'] == 'started':
            repo.save_workflow_outcome(outcome['session_id'], outcome)
            return deepcopy(outcome)
        raise ValueError('only scheduled outcomes can start')
    updated = deepcopy(outcome)
    updated['state'] = 'started'
    updated['started_at'] = utc_now()
    updated['timing']['job_started'] = updated['started_at']
    repo.save_workflow_outcome(updated['session_id'], updated)
    return updated


def finish_outcome(repo, outcome, state, package=None, usage=None, reason=None, trace=None):
    if state not in TERMINAL_STATES:
        raise ValueError('workflow finish requires terminal state')
    updated = deepcopy(outcome)
    # Retrying the same finish with the returned outcome preserves its timestamp.
    if updated['state'] in ACTIVE_STATES:
        updated['finished_at'] = utc_now()
    updated['state'] = state
    if package is not None:
        updated['package_ref'] = {k: package[k] for k in ('id', 'revision', 'package_hash')}
        if usage is None:
            usage = package.get('model_usage')
        if trace is None:
            trace = package.get('trace')
    if usage is not None:
        updated['model_usage'] = {
            'calls': None, 'input_tokens': None, 'output_tokens': None,
            'total_tokens': None, 'usage_complete': False, **deepcopy(usage),
        }
    if trace is not None:
        updated['trace'] = deepcopy(trace)
    if reason is not None:
        updated['reason'] = reason
    if state in {'produced', 'fallback'}:
        updated['timing']['candidate_ready'] = updated['finished_at']
    repo.save_workflow_outcome(updated['session_id'], updated)
    return updated


def interrupted_outcome(outcome):
    """A restarted process cannot know charges for in-flight provider requests."""
    updated = deepcopy(outcome)
    updated.update(state='interrupted', finished_at=utc_now(), reason='process_restart')
    updated['model_usage']['usage_complete'] = False
    return updated
