"""Append-only delivery events, separate from immutable workflow completions."""
from engine.core import digest
from engine.outcomes import utc_now

KINDS = {'opportunity', 'disposition', 'browser_ack', 'approval_received'}


def record(repo, session_id, kind, identity, **data):
    if kind not in KINDS:
        raise ValueError('invalid_lifecycle_kind')
    event = {'id': digest([kind, identity]), 'session_id': session_id, 'kind': kind,
             'recorded_at': utc_now(), **data}
    return repo.append_lifecycle(session_id, event)


def validate_event(session_id, event):
    if event['session_id'] != session_id or event['kind'] not in KINDS or len(event['id']) != 64:
        raise ValueError('invalid_lifecycle_event')


def disposition(repo, sid, outcome, state, package=None, at_ms=None):
    return record(repo, sid, 'disposition', [outcome['run_id'], state],
                  run_id=outcome['run_id'], story_id=outcome['story_id'],
                  revision=outcome['revision'], evidence_revision=outcome['evidence_revision'],
                  state=state, package_ref={k:package[k] for k in ('id','revision','package_hash')} if package else outcome.get('package_ref'),
                  replay_ms=at_ms)


def package_disposition(repo, sid, package, state, at_ms):
    matches = [o for o in repo.workflow_outcomes(sid) if o.get('package_ref', {}) and
               o['package_ref']['package_hash'] == package['package_hash']]
    for outcome in matches:
        disposition(repo, sid, outcome, state, package, at_ms)
