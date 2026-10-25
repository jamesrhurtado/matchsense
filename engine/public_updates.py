"""Public withdrawal notices: identities and timing, never withdrawn copy or traces."""
import json

from engine.dispositions import record


def record_source_withdrawal(repo, sid, package, at_ms):
    """Call before invalidation so a retry can recover the same durable notice."""
    record(repo, sid, 'disposition', ['source_withdrawn', package['id'], package['revision'], package['package_hash']],
           state='source_withdrawn', story_id=package['id'], revision=package['revision'],
           package_hash=package['package_hash'], replay_ms=at_ms,
           story_at_ms=package['metrics'].get('occurrence_ms', package['eligible_from_ms']),
           family=package.get('family', 'pass'))


def public_updates(repo, sid, now, language='en', focus=None, start=0, end=None):
    end = now if end is None else end
    events = [dict(e, kind='source_changed') for e in repo.lifecycle_events(sid)
              if e.get('state') == 'source_withdrawn']
    for row in repo.audit(sid):
        if row['action'] != 'retract':
            continue
        data = json.loads(row['data']) if isinstance(row['data'], str) else row['data']
        events.append({'id': f'retract:{data.get("story_id")}:{data.get("revision")}:{row["at_ms"]}',
                       'story_id': data.get('story_id'), 'revision': data.get('revision'),
                       'replay_ms': row['at_ms'], 'kind': 'producer_retracted'})
    result = []
    for event in events:
        at = event.get('replay_ms')
        if at is None or at > now:
            continue
        package = repo.stored_package(sid, event['story_id'], event['revision'])
        if not package:
            continue
        decision = repo.decision(sid, package['id'])
        # A record written just before a crash must not announce a withdrawal
        # until the corresponding exact approval actually becomes invalid.
        if event['kind'] == 'source_changed' and decision and decision['status'] == 'approved' and decision['revision'] == package['revision'] and decision['package_hash'] == package['package_hash']:
            continue
        m = package['metrics']
        actors = {m.get('team_id'), m.get('passer_id'), m.get('receiver_id')} | set(m.get('participants', {}).values())
        if m.get('family') == 'possession':
            actors |= set(m['facts']['team_ms'])
        if focus and focus not in actors:
            continue
        occurred = m.get('occurrence_ms', package['eligible_from_ms'])
        # Current corrections to stories in an older requested interval remain
        # visible even if the source correction arrived after that interval.
        if not (start <= occurred <= end or start <= at <= end):
            continue
        es = language == 'es'
        family = package.get('family', 'pass')
        topic = {'goal': ('un gol', 'goal'), 'shot': ('un remate', 'shot'),
                 'pass': ('un pase', 'pass'), 'pressure': ('rivales cercanos', 'nearby-opponent'),
                 'recovery': ('un cambio de control', 'control-change'),
                 'possession': ('un intervalo de posesión', 'possession-window')}.get(family, ('el juego', 'match'))
        text = (f'La explicación aprobada sobre {topic[0]} se retiró porque cambió la fuente.' if es else
                f'An approved {topic[1]} explanation was withdrawn after its source changed.') if event['kind'] == 'source_changed' else (
                'El productor retiró una explicación aprobada.' if es else
                'The producer withdrew an approved explanation.')
        result.append({'notice_id': event['id'], 'story_id': package['id'], 'at_ms': at,
                       'story_at_ms': occurred, 'family': package.get('family', 'pass'),
                       'kind': event['kind'], 'text': text})
    return sorted(result, key=lambda e: (e['at_ms'], e['notice_id']), reverse=True)
