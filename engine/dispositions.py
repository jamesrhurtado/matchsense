"""Append-only delivery events, separate from immutable workflow completions."""
from engine.core import digest
from engine.outcomes import utc_now

KINDS = {'opportunity', 'disposition', 'browser_ack', 'approval_received'}


def event_for(session_id, kind, identity, **data):
    if kind not in KINDS:
        raise ValueError('invalid_lifecycle_kind')
    event = {'id': digest([kind, identity]), 'session_id': session_id, 'kind': kind,
             'recorded_at': utc_now(), **data}
    return event


def record(repo, session_id, kind, identity, **data):
    return repo.append_lifecycle(session_id, event_for(session_id, kind, identity, **data))


def validate_event(session_id, event):
    if event['session_id'] != session_id or event['kind'] not in KINDS or len(event['id']) != 64:
        raise ValueError('invalid_lifecycle_event')


def disposition_event(sid, outcome, state, package=None, at_ms=None):
    return event_for(sid, 'disposition', [outcome['run_id'], state],
                  run_id=outcome['run_id'], story_id=outcome['story_id'],
                  revision=outcome['revision'], evidence_revision=outcome['evidence_revision'],
                  state=state, package_ref={k:package[k] for k in ('id','revision','package_hash')} if package else outcome.get('package_ref'),
                  replay_ms=at_ms)


def disposition(repo, sid, outcome, state, package=None, at_ms=None):
    return repo.append_lifecycle(sid, disposition_event(sid, outcome, state, package, at_ms))


def package_events(repo, sid, package, state, at_ms):
    reference = {k: package[k] for k in ('id', 'revision', 'package_hash')}
    return [disposition_event(sid, outcome, state, package, at_ms)
            for outcome in repo.workflow_outcomes(sid)
            if outcome.get('package_ref') == reference]


def package_disposition(repo, sid, package, state, at_ms):
    for event in package_events(repo, sid, package, state, at_ms):
        repo.append_lifecycle(sid, event)


def validate_acceptance_events(sid, package, events):
    reference = {k: package[k] for k in ('id', 'revision', 'package_hash')}
    for event in events:
        validate_event(sid, event)
        if (event['kind'] != 'disposition' or event.get('state') != 'accepted'
                or event.get('package_ref') != reference):
            raise ValueError('invalid_package_acceptance_event')


def reconcile_acceptances(repo, sid=None):
    """Repair old acceptance gaps from durable facts; never publish or edit outcomes.

    A stored historical revision proves acceptance even after supersession. A
    workflow completion alone does not. The original package_ready audit supplies
    replay time; recorded_at is recovery time, never a fabricated acceptance time.
    New writes include these events in the package transaction.
    """
    import json
    sessions = [sid] if sid is not None else [s['id'] for s in repo.list_sessions()]
    repaired = 0
    for session_id in sessions:
        existing = {e['id'] for e in repo.lifecycle_events(session_id)}
        ready_times = {}
        for row in repo.audit(session_id):
            if row['action'] == 'package_ready':
                detail = json.loads(row['data']) if isinstance(row['data'], str) else row['data']
                ready_times[(detail.get('story_id'), detail['revision'])] = row['at_ms']
        for outcome in repo.workflow_outcomes(session_id):
            reference = outcome.get('package_ref')
            if not reference or outcome['state'] not in {'produced', 'fallback'}:
                continue
            event_id = digest(['disposition', [outcome['run_id'], 'accepted']])
            if event_id in existing:
                continue
            package = repo.stored_package(session_id, reference['id'], reference['revision'])
            if not package or package['package_hash'] != reference['package_hash']:
                continue
            event = disposition_event(session_id, outcome, 'accepted', package,
                                      ready_times.get((reference['id'], reference['revision'])))
            event['recovered'] = True
            repo.append_lifecycle(session_id, event)
            existing.add(event_id)
            repaired += 1
    return repaired
