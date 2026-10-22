"""Bounded previous-pass context. No generator labels or unrestricted raw history.

The feed contract requires paired events and continuous tracking as a conservative
availability witness. It cannot detect an upstream source silently omitting both
events; that remains an explicit incoming-feed assumption.
"""
from engine.core import CONFIG, available, digest

CONTEXT_VERSION = 'recent-completed-three-v1'
LOOKBACK_MS = 120_000


def recent_pass_context(metadata, messages, cutoff_ms, current_pass_id):
    obs = available(messages, cutoff_ms)
    events = [m for m in obs if m['kind'] == 'event' and m['payload']['type'] in
              {'pass_started', 'pass_resolved'}]
    starts = [m for m in events if m['payload']['type'] == 'pass_started'
              and m['payload']['details']['pass_id'] == current_pass_id]
    if len(starts) != 1:
        raise ValueError('ambiguous_or_missing_current_pass')
    current = starts[0]
    team, period, release = current['payload']['team_id'], current['period'], current['timeline_ms']
    lower = max(0, release - LOOKBACK_MS)
    # Include all earlier team events, even exclusions. A corrected failed pass or
    # late insertion must change the population fingerprint, not only selected IDs.
    population = [e for e in events if e['period'] == period and e['timeline_ms'] < release
                  and e['payload']['team_id'] == team
                  and e['payload']['details']['pass_id'] != current_pass_id]
    by_id = {}
    for event in population:
        by_id.setdefault(event['payload']['details']['pass_id'], []).append(event)
    relevant_ids = {pid for pid, rows in by_id.items() if
                    any(r['timeline_ms'] >= lower for r in rows) or
                    not any(r['payload']['type']=='pass_resolved' for r in rows)}
    population = [r for r in population if r['payload']['details']['pass_id'] in relevant_ids]
    by_id = {pid:rows for pid,rows in by_id.items() if pid in relevant_ids}
    frames = [m for m in obs if m['kind'] == 'tracking_frame' and m['period'] == period
              and lower <= m['timeline_ms'] <= release]
    period_start = next(p['timeline_offset_ms'] for p in metadata['periods'] if p['period'] == period)
    lower = max(lower, period_start)
    frames = [m for m in frames if m['timeline_ms'] >= lower]
    times = sorted(set(m['timeline_ms'] for m in frames))
    complete = bool(times and times[0] <= lower and times[-1] == release and
                    all(b - a <= CONFIG['maximum_gap_ms'] for a, b in zip(times, times[1:])))
    direction = next(p for p in metadata['periods'] if p['period'] == period)['attack_direction'][team]
    sign = 1 if direction == 'right' else -1
    comparators = []
    for pid, rows in by_id.items():
        ends = [r for r in rows if r['payload']['type'] == 'pass_resolved'
                and lower <= r['timeline_ms'] < release]
        if not ends:
            # A pass still in flight is a valid exclusion only if its resolution
            # is already available at the investigation cutoff.
            pending = [r for r in rows if r['payload']['type'] == 'pass_started'
                       and r['timeline_ms'] >= lower]
            if pending and not any(e['period'] == period and e['payload']['type'] == 'pass_resolved'
                                   and e['payload']['details']['pass_id'] == pid
                                   and e['timeline_ms'] >= release for e in events):
                complete = False
            continue
        releases = [r for r in rows if r['payload']['type'] == 'pass_started']
        if len(ends) != 1 or len(releases) != 1:
            complete = False
            continue
        start, end = releases[0], ends[0]
        details = end['payload']['details']
        if start['timeline_ms'] >= end['timeline_ms']:
            complete = False
            continue
        if details['outcome'] != 'received':
            continue
        if (details['controlling_team_id'] != team or
                details['controlling_player_id'] not in {p['id'] for p in metadata['players'] if p['team_id'] == team}):
            complete = False
            continue
        a, b = start['payload']['details']['start_position'], details['end_position']
        if not all(0 <= p['x_m'] <= metadata['pitch']['length_m'] and
                   0 <= p['y_m'] <= metadata['pitch']['width_m'] for p in (a, b)):
            complete = False
            continue
        comparators.append({'pass_id': pid, 'release_ms': start['timeline_ms'],
                            'resolution_ms': end['timeline_ms'], 'forward_m': sign * (b['x_m'] - a['x_m']),
                            'release_position': dict(a), 'reception_position': dict(b),
                            'source_message_ids': [start['message_id'], end['message_id']],
                            'source_hashes': [digest(start), digest(end)]})
    selected = sorted(comparators, key=lambda p: (-p['resolution_ms'], p['pass_id']))[:3]
    current_ends = [e for e in events if e['payload']['type'] == 'pass_resolved'
                    and e['payload']['details']['pass_id'] == current_pass_id and e['period'] == period]
    current_forward = (sign * (current_ends[0]['payload']['details']['end_position']['x_m'] -
                              current['payload']['details']['start_position']['x_m'])
                       if len(current_ends) == 1 else None)
    status = 'incomplete_history' if not complete else 'insufficient_history' if len(selected) < 3 else 'available'
    relation = ('greater_than_each' if status == 'available' and current_forward is not None
                and all(current_forward > p['forward_m'] for p in selected) else 'no_comparative_claim')
    # Cutoff records actual availability of dependencies, so advancing the replay
    # alone cannot create revisions. Corrections are frozen by available().
    source_rows = sorted(population + [current] + current_ends, key=lambda e: e['message_id'])
    record = {'version': CONTEXT_VERSION, 'current_pass_id': current_pass_id, 'team_id': team,
              'period': period, 'attack_direction':direction, 'release_ms': release, 'window_start_ms': lower,
              'lookback_ms': LOOKBACK_MS, 'cutoff_ms': max([e['available_at_ms'] for e in source_rows] +
                                                       [f['available_at_ms'] for f in frames] + [release]),
              'status': status, 'sample_count': len(selected), 'comparators': selected,
              'current_forward_m': current_forward, 'unit': 'm', 'relation': relation,
              'source_message_ids': [e['message_id'] for e in source_rows],
              'source_hashes': [digest(e) for e in source_rows],
              'coverage_complete': complete,
              'limitation': 'Previous completed passes by this team in this replay only; event-complete feed assumed. No claim of tactical value or match-wide ranking.'}
    record['revision'] = digest({k:v for k,v in record.items() if k!='cutoff_ms'})[:16]
    return record


def contextual_metrics(metrics, metadata, messages, cutoff_ms):
    if not metrics or not metrics['eligible']:
        return metrics
    try:
        context = recent_pass_context(metadata, messages, cutoff_ms, metrics['pass_id'])
    except ValueError as exc:
        if str(exc)!='ambiguous_or_missing_current_pass':raise
        return {**metrics,'eligible':False,'context_error':str(exc)}
    return {**metrics, 'current_evidence_revision': metrics['evidence_revision'],
            'context': context, 'evidence_revision': digest([metrics['evidence_revision'], context['revision']])[:16],
            'input_cutoff_ms': max(metrics['input_cutoff_ms'], context['cutoff_ms']),
            'available_from_ms': max(metrics['available_from_ms'], context['cutoff_ms'])}
