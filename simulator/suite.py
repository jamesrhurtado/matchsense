"""Seeded, continuous scripted trajectories and separately applied feed faults.

Only match.json and stream.jsonl are runtime inputs. Catalogue, reference state,
checks, seeds and fault plans are offline evaluation material.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import random

from simulator.scenarios import VERSION, Case, cases, get_case


@dataclass
class Dataset:
    metadata: dict
    clean: list[dict]
    observations: list[dict]
    reference: dict


def _interpolate(knots, t):
    if t <= knots[0][0]:
        return knots[0][1]
    for (a, pa), (b, pb) in zip(knots, knots[1:]):
        if t <= b:
            ratio = (t - a) / (b - a)
            return tuple(x + (y - x) * ratio for x, y in zip(pa, pb))
    return knots[-1][1]


def generate_case(case: Case) -> Dataset:
    parent, family = case.parent, case.family
    rng = random.Random(parent.seed)
    team = parent.team
    opponent = 'amber' if team == 'blue' else 'blue'
    passer, receiver, intended = [f'{team}-{i:02d}' for i in rng.sample(range(2, 12), 3)]
    interceptor = f'{opponent}-09'
    first_names = ['Ari', 'Beni', 'Ciro', 'Dani', 'Eren', 'Feli', 'Gabi', 'Hugo', 'Ilan', 'Jori', 'Kian']
    last_names = ['Marin', 'Paz', 'Luna', 'Rocha', 'Vidal', 'Costa', 'Roca', 'Vela', 'Prado', 'Sierra', 'Neri']
    players = []
    for offset, tid in enumerate(('blue', 'amber')):
        names = rng.sample(last_names, len(last_names))
        for i in range(1, 12):
            players.append({'id': f'{tid}-{i:02d}', 'team_id': tid,
                            'name': f'{first_names[(i + parent.seed + offset) % 11]} {names[i-1]}',
                            'number': i, 'role': 'keeper' if i == 1 else 'outfield'})
    metadata = {
        'schema_version': '1.0.0', 'match_id': case.match_id, 'synthetic': True, 'scope': 'segment',
        'pitch': {'length_m': 105, 'width_m': 68, 'convention': 'x right, y down'},
        'teams': [{'id': 'blue', 'name': 'Harbor City', 'color': '#3b82f6'},
                  {'id': 'amber', 'name': 'Alder Rovers', 'color': '#f59e0b'}],
        'players': players,
        'periods': [{'period': 1, 'timeline_offset_ms': 0,
                     'attack_direction': {team: 'left' if parent.reverse else 'right',
                                          opponent: 'right' if parent.reverse else 'left'}}],
        'initial_state': {'period': 1, 'period_elapsed_ms': 0, 'score': {'blue': 0, 'amber': 0},
                          'active_player_ids': [p['id'] for p in players],
                          'ball_status': 'controlled', 'possession_team_id': team},
        'tracking_hz': 10, 'provenance_id': 'prov-' + case.match_id.removeprefix('match-'),
    }
    duration = 180000 if family == 'long_session' else 90000 if family == 'multiple_passes' else 60000
    releases = [parent.release_ms + i * 60000 for i in range(3)] if family == 'long_session' else [parent.release_ms, parent.release_ms + 35000] if family == 'multiple_passes' else [parent.release_ms]
    plans = []
    for index, start in enumerate(releases):
        sx, cy, distance = parent.x, parent.y, parent.distance
        ex, ey = sx + distance, cy + 3
        if family == 'backward_pass': ex = sx - 12
        if family == 'lateral_pass': ex = sx; ey = cy + 14
        if family == 'out_of_play': ex = sx + 5; ey = 0
        carry = 4 if family == 'insufficient_progression' else 4.96 if family == 'rounding_boundary' else 7
        outcome = {'intercepted': 'intercepted', 'uncontrolled': 'uncontrolled', 'out_of_play': 'out_of_play'}.get(family, 'received')
        controller = interceptor if outcome == 'intercepted' else receiver if outcome == 'received' else None
        owner = opponent if outcome == 'intercepted' else team if outcome == 'received' else None
        if outcome != 'received': carry = 0
        plans.append({'pass_id': f'pass-{index+1}', 'start': start, 'end': start+max(1200, math.ceil(math.hypot(ex-sx, ey-cy)/25*10)*100),
                      'sx': sx, 'cy': cy, 'ex': ex, 'ey': ey, 'carry': carry,
                      'outcome': outcome, 'controller': controller, 'owner': owner,
                      'pressured': family != 'unpressured' and not (family == 'multiple_passes' and index == 0)})

    # Keyframes specify actual trajectories, not independent frame perturbations.
    # All transitions interpolate continuously; off-ball motion stays below 10 m/s.
    base = {p['id']: ((10 + (i % 5)*6, 6 + (i*9)%55) if p['team_id'] == team
                      else (78 + (i % 4)*4, 5 + (i*7)%58)) for i, p in enumerate(players)}
    knots = {pid: [] for pid in base}
    for plan in plans:
        sx, cy, ex, ey = (plan[k] for k in ('sx', 'cy', 'ex', 'ey'))
        for t in [max(0, plan['start']-6000), plan['start'], plan['end'], plan['end']+3000]:
            positions = dict(base)
            positions[passer] = (sx, cy)
            positions[receiver] = (ex + (plan['carry'] if t == plan['end']+3000 else 0), ey)
            offsets = [(2, -1), (3, 3), (5, 5)]
            if family == 'insufficient_bypass': offsets = [(2, -1), (-3, 3), (-5, 5)]
            if plan['pressured']:
                for j, (dx, dy) in enumerate(offsets):
                    positions[f'{opponent}-{j+6:02d}'] = (sx + dx, cy + dy)
            if plan['outcome'] == 'intercepted': positions[interceptor] = (ex, ey)
            for pid in knots:
                knots[pid].append((t, positions[pid]))
    motion = {pid:(rng.uniform(0,6),rng.uniform(0,6)) for pid in knots}
    # Holding the first state before the first anchor is intentional prior context.
    def canonical_point(x, y):
        return {'x_m': round(105-x if parent.reverse else x, 4), 'y_m': round(y, 4)}

    messages = []
    def add(kind, t, payload):
        n = len(messages)+1
        messages.append({'schema_version': '1.0.0', 'match_id': case.match_id,
                         'message_id': f'm-{n:07d}', 'sequence_no': n, 'kind': kind,
                         'timeline_ms': t, 'period': 1, 'period_elapsed_ms': t,
                         'available_at_ms': t, 'revision': 1, 'supersedes_message_id': None,
                         'payload': payload})
    for t in range(0, duration+1, 100):
        plan = max((p for p in plans if t >= p['start']-6000), key=lambda p:p['start'], default=plans[0])
        positions = {pid: _interpolate(path, t) for pid, path in knots.items()}
        for pid,(x,y) in positions.items():
            if pid not in (passer,receiver,interceptor):
                phase_x,phase_y = motion[pid]
                positions[pid] = (x+.25*math.sin(t/3000+phase_x),
                                  y+.25*math.cos(t/3500+phase_y))
        if t < plan['start']:
            ball = positions[passer]; status = 'controlled'; control = passer; possession = team
        elif t < plan['end']:
            ratio = (t-plan['start'])/(plan['end']-plan['start'])
            ball = (plan['sx']+(plan['ex']-plan['sx'])*ratio, plan['cy']+(plan['ey']-plan['cy'])*ratio)
            status = 'in_flight'; control = None; possession = team
        else:
            ball = positions[plan['controller']] if plan['controller'] else (plan['ex'], plan['ey'])
            status = {'received':'controlled', 'intercepted':'controlled', 'uncontrolled':'loose', 'out_of_play':'out_of_play'}[plan['outcome']]
            control = plan['controller']; possession = plan['owner']
        # Between separate plays a loose-ball reset gives both ball and players
        # enough time to move. It lies far outside all evaluated pass windows.
        upcoming = next((p for p in plans[1:] if p['start']-8000 <= t < p['start']-6000), None)
        if upcoming:
            previous = plans[plans.index(upcoming)-1]
            ratio = (t-(upcoming['start']-8000))/2000
            a = _interpolate(knots[previous['controller']], upcoming['start']-8000)
            b = (upcoming['sx'], upcoming['cy'])
            ball = tuple(x+(y-x)*ratio for x,y in zip(a,b))
            status = 'loose'; control = None; possession = None
        if family in ('possession_interruption', 'unknown_possession') and plan['end']+1000 <= t < plan['end']+1400:
            status = 'loose' if family == 'possession_interruption' else 'unknown'
            control = None; possession = None
        add('tracking_frame', t, {
            'frame_id': f'f-{t:07d}',
            'players': [{'player_id': p['id'], 'team_id': p['team_id'],
                         **canonical_point(*positions[p['id']]), 'quality': 'simulated_observation'} for p in players],
            'missing_player_ids': [], 'ball': {**canonical_point(*ball), 'z_m': 0, 'quality':'simulated_observation'},
            'ball_status': status, 'controlling_player_id': control, 'possession_team_id': possession,
        })
        if t == plan['start']:
            add('event', t, {'event_id': f'e-{plan["pass_id"]}-start', 'type':'pass_started',
                            'team_id':team, 'player_id':passer, 'possession_id':f'pos-{plan["pass_id"]}',
                            'details':{'pass_id':plan['pass_id'], 'start_position':canonical_point(plan['sx'],plan['cy']),
                                       'intended_receiver_id':intended if family=='different_receiver' else receiver}})
        if t == plan['end']:
            add('event', t, {'event_id':f'e-{plan["pass_id"]}-end', 'type':'pass_resolved',
                            'team_id':team, 'player_id':control, 'possession_id':f'pos-{plan["pass_id"]}',
                            'details':{'pass_id':plan['pass_id'], 'outcome':plan['outcome'],
                                       'end_position':canonical_point(plan['ex'],plan['ey']),
                                       'controlling_team_id':possession, 'controlling_player_id':control}})
        # Derive observed state transitions from the same state that emitted frames.
        current = (possession, status)
        if t and current != previous_state and status != 'in_flight':
            if possession != previous_state[0]:
                add('event', t, {'event_id':f'e-pos-{t}', 'type':'possession_changed', 'team_id':possession,
                                'player_id':control, 'possession_id':f'pos-at-{t}',
                                'details':{'previous_team_id':previous_state[0], 'new_team_id':possession,
                                           'controlling_player_id':control, 'reason':'observed transition'}})
            add('event', t, {'event_id':f'e-state-{t}', 'type':'play_state_changed', 'team_id':possession,
                            'player_id':control, 'possession_id':None,
                            'details':{'ball_status':status, 'reason':'observed transition'}})
        previous_state = current

    clean = messages
    observations = deepcopy(clean)
    first = plans[0]
    release, end, confirm = first['start'], first['end'], first['end']+3000
    faults = []
    for message in observations:
        if message['kind'] != 'tracking_frame': continue
        t, p = message['timeline_ms'], message['payload']
        missing = []
        if family == 'missing_pressure' and release-2000 <= t <= release: missing = [f'{opponent}-06']
        if family == 'sparse_pressure' and t in (release-1600,release-1000,release-400): missing = [f'{opponent}-06']
        if family == 'missing_release' and t == release: missing = [x['player_id'] for x in p['players'] if x['team_id']==opponent]
        if missing:
            p['players'] = [x for x in p['players'] if x['player_id'] not in missing]
            p['missing_player_ids'] = missing
        if family in ('missing_ball_confirmation','correction_restores') and t == confirm: p['ball'] = None
        if family == 'noisy_tracking':
            # Smooth shared observation bias, <=0.08m; preserves controller/ball alignment.
            dx, dy = .08*math.sin(t/1700+parent.seed), .08*math.cos(t/2100+parent.seed)
            for point in p['players'] + ([p['ball']] if p['ball'] else []):
                point['x_m'] = round(point['x_m']+dx,4); point['y_m'] = round(point['y_m']+dy,4)
                point['quality'] = 'noisy_observation'
    if family == 'noisy_tracking':
        for message in observations:
            if message['kind']=='event' and message['payload']['type'] in ('pass_started','pass_resolved'):
                t = message['timeline_ms']
                details = message['payload']['details']
                point = details.get('start_position', details.get('end_position'))
                point['x_m'] = round(point['x_m']+.08*math.sin(t/1700+parent.seed),4)
                point['y_m'] = round(point['y_m']+.08*math.cos(t/2100+parent.seed),4)
    if family == 'retention_gap':
        observations = [m for m in observations if not (m['kind']=='tracking_frame' and end+800 <= m['timeline_ms'] <= end+1300)]
        faults.append({'kind':'drop_frames','from_ms':end+800,'through_ms':end+1300})
    if family == 'no_pass_events':
        observations = [m for m in observations if not (m['kind']=='event' and m['payload']['type'] in ('pass_started','pass_resolved'))]
    if family in ('delayed_outcome','expired_outcome'):
        outcome = next(m for m in observations if m['kind']=='event' and m['payload']['type']=='pass_resolved')
        outcome['available_at_ms'] = confirm+(5000 if family=='delayed_outcome' else 31000)
        faults.append({'kind':'delay','message_id':outcome['message_id'],'available_at_ms':outcome['available_at_ms']})
    if family == 'reordered_delivery':
        jitter = random.Random(parent.seed+991)
        for m in observations: m['available_at_ms'] += jitter.choice([0,100,300,700])
        # Guarantee a known earliest confirmation without implementing a second
        # detector in the reference evaluator. All earlier frames arrive first.
        endpoint = next(m for m in observations if m['kind']=='tracking_frame' and m['timeline_ms']==confirm)
        endpoint['available_at_ms'] = confirm+700
        faults.append({'kind':'jitter','maximum_delay_ms':700,'confirmation_delay_ms':700})
    if family in ('correction_withdraws','correction_restores'):
        old = next(m for m in observations if m['kind']=='tracking_frame' and m['timeline_ms']==confirm)
        correction = deepcopy(old)
        correction.update(message_id='m-correction-1',sequence_no=len(clean)+1,revision=2,
                          supersedes_message_id=old['message_id'],available_at_ms=confirm+4000)
        correction['payload']['ball'] = None if family=='correction_withdraws' else deepcopy(next(m['payload']['ball'] for m in clean if m['kind']=='tracking_frame' and m['timeline_ms']==confirm))
        observations.append(correction)
        faults.append({'kind':'correction','message_id':correction['message_id'],'supersedes_message_id':old['message_id'],'available_at_ms':confirm+4000})
    observations.sort(key=lambda m:(m['available_at_ms'],m['timeline_ms'],m['sequence_no']))
    if family == 'duplicates':
        delivery = []
        for i,m in enumerate(observations):
            delivery.append(m)
            if i%37==0: delivery.append(deepcopy(m))
        observations = delivery
        faults.append({'kind':'exact_retransmission','every_source_rows':37})
    if family in ('missing_pressure','sparse_pressure','missing_release','missing_ball_confirmation','correction_restores','noisy_tracking','no_pass_events'):
        faults.append({'kind':family})

    intent = case.record()['intent']
    checks = []
    for i, plan in enumerate(plans):
        confirmed = plan['end']+3000
        good = intent in ('candidate','candidate_late','expired','withdraw','restore','multiple') and not (family=='multiple_passes' and i==0)
        ready = confirmed
        if family=='delayed_outcome': ready += 5000
        if family=='expired_outcome': ready += 31000
        if family=='reordered_delivery': ready += 700
        if family=='correction_restores': ready += 4000
        expires = confirmed+30000
        def check(at, expected, reason):
            checks.append({'at_ms':at,'expected_pass_ids':[plan['pass_id']] if expected else [],'reason':reason})
        check(confirmed-1,False,'Future confirmation must remain inaccessible.')
        if good and ready>confirmed: check(ready-1,False,'Required observation or correction is not yet delivered.')
        check(ready,good and ready<expires,'Authored candidate, subject to observation quality and original expiry.')
        if family=='correction_withdraws':
            check(confirmed+3999,True,'Original confirmation is still available.')
            check(confirmed+4000,False,'Delivered correction withdraws required ball position.')
        check(expires,False,'Live overlay has expired; later delivery must not revive it.')
    reference = case.record() | {'duration_ms':duration, 'fault_plan':faults, 'checks':sorted(checks,key=lambda c:c['at_ms']),
                                'plays':[{'pass_id':p['pass_id'],'release_ms':p['start'],'resolution_ms':p['end'],
                                          'confirmation_ms':p['end']+3000,'expires_at_ms':p['end']+33000,
                                          'passer_id':passer,'actual_receiver_id':p['controller'],
                                          'continuation_distance_m':p['carry'],
                                          'positive_claim_bounds':{'c-pressure':[2,2],'c-bypass':[3,3],
                                                                   'c-retain':[3,3],
                                                                   'c-progress':[6.8,7.2] if family=='noisy_tracking' else [7,7]}}
                                         for p in plans],
                                'reference_basis':'Authored play/outcome and explicit observation-fault plan; not detector output.',
                                'football_expert_review':'pending'}
    return Dataset(metadata,clean,observations,reference)


def serialize(messages):
    return ''.join(json.dumps(m,separators=(',',':'),allow_nan=False)+'\n' for m in messages)


def export_case(dataset, root):
    mid = dataset.metadata['match_id']
    runtime = root/'runtime'/mid
    reference = root/'evaluation-only'
    provenance = root/'provenance'
    for folder in (runtime,reference,provenance): folder.mkdir(parents=True,exist_ok=True)
    raw = serialize(dataset.observations)
    (runtime/'match.json').write_text(json.dumps(dataset.metadata,indent=2)+'\n')
    (runtime/'stream.jsonl').write_text(raw)
    # Truth contains future clean observations. Never mount it in an agent runtime.
    (reference/f'{mid}.json').write_text(json.dumps(dataset.reference,indent=2)+'\n')
    (reference/f'{mid}.clean.jsonl').write_text(serialize(dataset.clean))
    record = {'generator_version':VERSION,'case_id':dataset.reference['case_id'],'match_id':mid,
              'source':'Original fictional scripted trajectories; no real match records.',
              'metadata_sha256':hashlib.sha256((runtime/'match.json').read_bytes()).hexdigest(),
              'observations_sha256':hashlib.sha256(raw.encode()).hexdigest(),
              'clean_sha256':hashlib.sha256(serialize(dataset.clean).encode()).hexdigest()}
    (provenance/f'{mid}.json').write_text(json.dumps(record,indent=2)+'\n')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list',action='store_true')
    parser.add_argument('--case',action='append',dest='case_ids',help='Repeat for selected cases, e.g. p01-01.')
    parser.add_argument('--split',choices=['development','validation','held_out'])
    parser.add_argument('--output',type=Path,default=Path('.run/synthetic'))
    args = parser.parse_args()
    selected = [get_case(x) for x in args.case_ids] if args.case_ids else cases(args.split)
    if args.list:
        for c in selected: print(f'{c.id:8} {c.parent.split:12} {c.family:26} {c.match_id}')
        return
    from simulator.validate import validate_feed
    records = []
    for case in selected:
        dataset = generate_case(case)
        validation = validate_feed(dataset.metadata,dataset.observations)
        record = export_case(dataset,args.output)
        record['validation'] = validation
        records.append(record)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'manifest.json').write_text(json.dumps({'generator_version':VERSION,'cases':records},indent=2)+'\n')
    print(f'Exported {len(records)} cases to {args.output.resolve()} (runtime and evaluation-only folders).')


if __name__=='__main__': main()
