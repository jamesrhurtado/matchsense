"""Independent observation/kinematic checks for constrained-episodes-v1.

No scene definitions, interpolation, story detectors, model or reference answers.
Legacy feed checks remain intact; new checks only govern the new profile.
"""
from __future__ import annotations
from collections import Counter
import json
import math
from pathlib import Path

from engine.contracts import MatchMetadata, OBSERVATION
from simulator.validate import validate_feed

PROFILE_PATH = Path(__file__).resolve().parents[1]/'data/provenance/episode-profile-v1.json'


def validate(metadata, messages, *, cutoff=None, _projected=False):
    profile = json.loads(PROFILE_PATH.read_text())
    failures, incomplete = [], []
    def fail(code, **context):
        if len(failures)<100:failures.append({'code':code,**context})
    try:
        MatchMetadata.model_validate(metadata)
        for row in messages:OBSERVATION.validate_python(row)
    except ValueError as exc:
        return {'passed':False,'failures':[{'code':'schema','detail':str(exc)}]}
    if cutoff is not None and any(max(r['timeline_ms'],r['available_at_ms'])>cutoff for r in messages):
        fail('future_observation',cutoff_ms=cutoff)
    if metadata['tracking_hz']!=profile['tracking_hz']:fail('sampling_profile_mismatch')
    roster={p['id']:p for p in metadata['players']}
    teams={t['id'] for t in metadata['teams']}
    for team in teams:
        players=[p for p in roster.values() if p['team_id']==team]
        if len(players)!=11 or sum(p['role']=='keeper' for p in players)!=1:
            fail('roster_profile',team_id=team)
    for period in metadata['periods']:
        if set(period['attack_direction'])!=teams or set(period['attack_direction'].values())!={'left','right'}:
            fail('attack_direction',period=period['period'])
    try:
        legacy=validate_feed(metadata,messages)
    except (AssertionError,ValueError) as exc:
        fail('legacy_feed',detail=str(exc));legacy=None
    if legacy is None:
        return {'passed':False,'profile_version':profile['version'],'failures':failures,
                'incomplete_observation_checks':incomplete,'football_review':'pending'}
    unique={r['message_id']:r for r in messages}
    # Physical occurrence order is deliberately independent of arrival order.
    frames=sorted((r for r in unique.values() if r['kind']=='tracking_frame' and r['revision']==1),key=lambda r:r['timeline_ms'])
    by_time={r['timeline_ms']:r for r in frames}
    events=[r for r in unique.values() if r['kind']=='event']
    source_events=[r for r in events if r['revision']==1]
    max_speed=max_acceleration=max_turn=0
    previous=None;velocities={};overlap_frames=0
    keeper_positions={p['id']:[] for p in roster.values() if p['role']=='keeper'}
    period_by_id={p['period']:p for p in metadata['periods']}
    tol=profile['derivative_tolerance']
    for frame in frames:
        t,p=frame['timeline_ms'],frame['payload']
        declared=period_by_id[frame['period']]
        active=max((period for period in metadata['periods'] if period['timeline_offset_ms']<=t),key=lambda period:period['timeline_offset_ms'])
        if declared!=active:fail('period_assignment',timeline_ms=t)
        positions={q['player_id']:q for q in p['players']}
        if p['ball_status'] in ('unknown','loose','out_of_play') and (p['possession_team_id'] or p['controlling_player_id']):
            fail('uncontrolled_possession',timeline_ms=t)
        for pid in keeper_positions:
            if pid in positions:keeper_positions[pid].append((positions[pid]['x_m'],positions[pid]['y_m']))
        all_positions=list(positions.values())
        if any(math.dist((a['x_m'],a['y_m']),(b['x_m'],b['y_m']))<profile['overlap_diagnostic_distance_m']
               for i,a in enumerate(all_positions) for b in all_positions[i+1:]):overlap_frames+=1
        if previous:
            old,old_positions=previous
            dt=(t-old['timeline_ms'])/1000
            midpoint=(t+old['timeline_ms'])/2000
            for pid,q in positions.items():
                if pid not in old_positions:
                    velocities.pop(pid,None);continue
                previous_q=old_positions[pid]
                v=tuple((q[a]-previous_q[a])/dt for a in ('x_m','y_m'))
                speed=math.hypot(*v);max_speed=max(max_speed,speed)
                if speed>profile['player_max_speed_mps']+tol:fail('player_speed',player_id=pid,timeline_ms=t,value=speed)
                if pid in velocities:
                    pv,pm=velocities[pid]
                    acceleration=math.dist(v,pv)/(midpoint-pm)
                    max_acceleration=max(max_acceleration,acceleration)
                    if acceleration>profile['player_max_acceleration_mps2']+tol:
                        fail('player_acceleration',player_id=pid,timeline_ms=t,value=acceleration)
                    old_speed=math.hypot(*pv)
                    if min(speed,old_speed)>=profile['turn_check_min_speed_mps']:
                        cosine=max(-1,min(1,sum(a*b for a,b in zip(v,pv))/(speed*old_speed)))
                        turn=math.acos(cosine)/(midpoint-pm);max_turn=max(max_turn,turn)
                        if turn>profile['player_max_turn_radians_per_s']+tol:
                            fail('player_turn',player_id=pid,timeline_ms=t,value=turn)
                velocities[pid]=v,midpoint
            for pid in set(old_positions)-set(positions):velocities.pop(pid,None)
        previous=frame,positions

    def contact(frame,pid):
        point=next((p for p in frame['payload']['players'] if p['player_id']==pid),None)
        ball=frame['payload']['ball']
        return None if point is None or ball is None else math.dist((point['x_m'],point['y_m']),(ball['x_m'],ball['y_m']))
    def event_at(row):
        frame=by_time.get(row['timeline_ms'])
        if frame is None:incomplete.append({'kind':'missing_event_frame','message_id':row['message_id']})
        return frame
    shot_starts={r['payload']['details']['shot_id']:r for r in source_events if r['payload']['type']=='shot_started'}
    for row in source_events:
        event,kind=row['payload'],row['payload']['type']
        d=event['details'];frame=event_at(row)
        if not frame:continue
        if event['player_id'] and roster[event['player_id']]['team_id']!=event['team_id']:
            fail('event_actor_team',message_id=row['message_id'])
        ball=frame['payload']['ball']
        if kind in ('pass_started','shot_started'):
            pid=event['player_id']
            if pid:
                distance=contact(frame,pid)
                if distance is not None and distance>profile['contact_distance_m']:
                    fail('release_actor_ball_alignment',message_id=row['message_id'])
            location=d.get('start_position',d.get('location'))
            if location and ball and math.dist((location['x_m'],location['y_m']),(ball['x_m'],ball['y_m']))>profile['position_tolerance_m']:
                fail('release_location',message_id=row['message_id'])
            before=by_time.get(row['timeline_ms']-100)
            if pid and before and before['payload']['controlling_player_id']!=pid:
                fail('release_without_prior_control',message_id=row['message_id'])
        if kind in ('ball_recovered','possession_changed'):
            team=event['team_id'] if kind=='ball_recovered' else d['new_team_id']
            if team!=frame['payload']['possession_team_id']:fail('acquisition_team_alignment',message_id=row['message_id'])
            pid=event['player_id'] if kind=='ball_recovered' else d['controlling_player_id']
            if pid and frame['payload']['controlling_player_id']!=pid:fail('acquisition_actor_alignment',message_id=row['message_id'])
            if d.get('previous_team_id')==team:fail('acquisition_without_team_change',message_id=row['message_id'])
        if kind=='shot_resolved':
            start=shot_starts.get(d['shot_id'])
            if not start or start['timeline_ms']>=row['timeline_ms']:
                fail('shot_without_prior_start',message_id=row['message_id']);continue
            if event['team_id']!=start['payload']['team_id']:fail('shot_team_mismatch',message_id=row['message_id'])
            if d['outcome'] in ('saved','blocked'):
                role='keeper' if d['outcome']=='saved' else 'outfield'
                defenders=[p for p in roster.values() if p['team_id']!=event['team_id'] and p['role']==role]
                distances=[contact(frame,p['id']) for p in defenders]
                known=[v for v in distances if v is not None]
                if known and min(known)>profile['contact_distance_m']:
                    fail('shot_intervention_alignment',message_id=row['message_id'])
                elif not known:incomplete.append({'kind':'unobserved_shot_intervention','message_id':row['message_id']})
            if d['outcome']=='goal' and ball:
                goal_x=105 if period_by_id[row['period']]['attack_direction'][event['team_id']]=='right' else 0
                if abs(ball['x_m']-goal_x)>profile['position_tolerance_m'] or abs(ball['y_m']-34)>3.66:
                    fail('reported_goal_geometry',message_id=row['message_id'])
        if kind=='goal_status_changed' and d.get('shot_id') and d['shot_id'] not in shot_starts:
            fail('goal_missing_linked_shot',message_id=row['message_id'])
        if kind=='goal_status_changed' and d.get('scorer_id'):
            scorer=roster.get(d['scorer_id'])
            if not scorer or (not d.get('own_goal') and scorer['team_id']!=event['team_id']):
                fail('goal_scorer_team',message_id=row['message_id'])
    diagnostics={'maximum_player_speed_mps':round(max_speed,5),
                 'maximum_player_acceleration_mps2':round(max_acceleration,5),
                 'maximum_player_turn_radians_per_s':round(max_turn,5),
                 'overlap_frames':overlap_frames,'frame_count':len(frames),
                 'frame_intervals_ms':dict(Counter(b['timeline_ms']-a['timeline_ms'] for a,b in zip(frames,frames[1:]))),
                 'keeper_ranges':{pid:{'x_m':[round(min(p[0] for p in points),3),round(max(p[0] for p in points),3)],
                                        'y_m':[round(min(p[1] for p in points),3),round(max(p[1] for p in points),3)]}
                                  for pid,points in keeper_positions.items() if points}}
    # A corrected tracking sample must satisfy the new movement profile too,
    # not only the older speed-only final-view check. Lineage itself was checked
    # above; normalize a separate final projection without modifying sources.
    corrected=None
    if not _projected and any(r['revision']>1 for r in unique.values()):
        from copy import deepcopy
        superseded={r['supersedes_message_id'] for r in unique.values() if r['supersedes_message_id']}
        final=deepcopy(sorted((r for key,r in unique.items() if key not in superseded),key=lambda r:(r['timeline_ms'],r['sequence_no'])))
        for i,row in enumerate(final):
            row.update(revision=1,supersedes_message_id=None,sequence_no=i)
        corrected=validate(metadata,final,cutoff=cutoff,_projected=True)
        failures.extend({**f,'view':'latest_correction'} for f in corrected['failures'])
    return {'passed':not failures,'profile_version':profile['version'],'failures':failures,
            'incomplete_observation_checks':incomplete,'diagnostics':diagnostics,
            'latest_corrected_profile':({'passed':corrected['passed'],'diagnostics':corrected.get('diagnostics')} if corrected else None),
            'legacy_feed':legacy,'football_review':'pending'}
