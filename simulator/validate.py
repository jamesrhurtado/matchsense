"""Structural, temporal and physical validation independent of story detection."""
from __future__ import annotations
import json
import math
from engine.contracts import MatchMetadata, OBSERVATION


def validate(metadata, messages, *, source_sequence=True):
    """Validate a chronological source view; gaps/explicit unknowns are legal."""
    MatchMetadata.model_validate(metadata)
    active = set(metadata['initial_state']['active_player_ids'])
    roster = {p['id']:p for p in metadata['players']}
    teams = {t['id'] for t in metadata['teams']}
    periods = {p['period']:p for p in metadata['periods']}
    assert len(roster)==len(metadata['players']), 'duplicate_roster_id'
    assert active==set(roster), 'active_roster_mismatch'
    assert len(active)==22, 'expected_22_players'
    assert len({m['message_id'] for m in messages})==len(messages), 'duplicate_source_ids'
    assert all(p['team_id'] in teams for p in roster.values()), 'unknown_roster_team'
    last = None
    starts = {}
    last_seq = -1
    logical = set()
    for raw in messages:
        OBSERVATION.validate_python(raw)
        assert raw['match_id']==metadata['match_id'], 'cross_match_observation'
        assert raw['period'] in periods, 'unknown_period'
        assert raw['timeline_ms']==periods[raw['period']]['timeline_offset_ms']+raw['period_elapsed_ms'], 'period_clock_mismatch'
        if source_sequence:
            assert raw['sequence_no']>last_seq, 'source_sequence_not_increasing'
        last_seq = raw['sequence_no']
        p = raw['payload']
        identity = (raw['kind'],p.get('frame_id',p.get('event_id')))
        assert identity not in logical, 'duplicate_logical_observation'
        logical.add(identity)
        if raw['kind']=='tracking_frame':
            positions = {x['player_id']:x for x in p['players']}
            assert len(set(p['missing_player_ids']))==len(p['missing_player_ids']), 'duplicate_missing_player'
            assert set(positions)|set(p['missing_player_ids'])==active, 'active_coverage_mismatch'
            assert p['possession_team_id'] is None or p['possession_team_id'] in teams, 'unknown_possession_team'
            for key,pos in positions.items():
                assert roster[key]['team_id']==pos['team_id'], 'wrong_team'
            if p['controlling_player_id']:
                pid = p['controlling_player_id']
                assert pid in roster, 'unknown_controller'
                assert p['ball_status']=='controlled', 'controller_without_controlled_state'
                assert roster[pid]['team_id']==p['possession_team_id'], 'controller_wrong_possession'
                controller = positions.get(pid)
                if controller and p['ball']:
                    assert math.dist((controller['x_m'],controller['y_m']),(p['ball']['x_m'],p['ball']['y_m']))<1.1, 'controller_far_from_ball'
            if last:
                dt = (raw['timeline_ms']-last['timeline_ms'])/1000
                assert dt>0, 'frame_time_not_increasing'
                prev = {x['player_id']:x for x in last['payload']['players']}
                for key,pos in positions.items():
                    if key in prev:
                        assert math.dist((pos['x_m'],pos['y_m']),(prev[key]['x_m'],prev[key]['y_m']))/dt<=10, 'player_speed_over_10_mps'
                if p['ball'] and last['payload']['ball']:
                    a,b = p['ball'],last['payload']['ball']
                    assert math.dist((a['x_m'],a['y_m']),(b['x_m'],b['y_m']))/dt<=30, 'ball_speed_over_30_mps'
            last = raw
        else:
            assert p['team_id'] is None or p['team_id'] in teams, 'unknown_event_team'
            assert p['player_id'] is None or p['player_id'] in roster, 'unknown_event_player'
            if p['type']=='pass_started':
                assert p['details']['pass_id'] not in starts, 'reused_pass_id'
                starts[p['details']['pass_id']] = raw
                intended = p['details']['intended_receiver_id']
                assert intended is None or intended in roster, 'unknown_intended_receiver'
                assert not {'outcome','end_position','controlling_team_id'}&set(p['details']), 'future_pass_outcome'
            elif p['type']=='pass_resolved':
                assert p['details']['pass_id'] in starts, 'resolution_without_start'
                assert starts[p['details']['pass_id']]['timeline_ms']<raw['timeline_ms'], 'resolution_before_start'
                assert last and last['timeline_ms']==raw['timeline_ms'], 'resolution_not_aligned_to_frame'
                ball,end = last['payload']['ball'],p['details']['end_position']
                if ball:
                    assert math.dist((ball['x_m'],ball['y_m']),(end['x_m'],end['y_m']))<.01, 'resolution_endpoint_mismatch'
                details = p['details']
                assert details['controlling_team_id']==last['payload']['possession_team_id'], 'resolution_possession_mismatch'
                assert details['controlling_player_id']==last['payload']['controlling_player_id'], 'resolution_controller_mismatch'
            elif p['type']=='possession_changed':
                assert last and p['details']['new_team_id']==last['payload']['possession_team_id'], 'possession_event_mismatch'
            elif p['type']=='play_state_changed':
                assert last and p['details']['ball_status']==last['payload']['ball_status'], 'play_state_event_mismatch'
    return {'frames':sum(m['kind']=='tracking_frame' for m in messages), 'messages':len(messages),
            'duration_ms':max((m['timeline_ms'] for m in messages),default=0), 'active_players':len(active)}


def validate_feed(metadata, messages):
    """Check a delivered feed without mistaking retransmission for source data.

Physical validation uses occurrence order, never arrival order. Corrections must
preserve logical identity and clock and form an explicit increasing lineage.
Both the original view and the final corrected view must remain coherent.
"""
    unique = {}
    duplicates = 0
    for raw in messages:
        OBSERVATION.validate_python(raw)
        old = unique.get(raw['message_id'])
        if old is not None:
            assert old==raw, 'conflicting_retransmission'
            duplicates += 1
        else:
            unique[raw['message_id']] = raw
    assert len({m['sequence_no'] for m in unique.values()})==len(unique), 'reused_source_sequence'
    superseded = set()
    for raw in unique.values():
        prior_id = raw['supersedes_message_id']
        if not prior_id:
            assert raw['revision']==1, 'initial_revision_not_one'
            continue
        assert prior_id in unique, 'orphan_correction'
        old = unique[prior_id]
        assert raw['revision']==old['revision']+1, 'correction_revision_gap'
        assert raw['match_id']==old['match_id'] and raw['kind']==old['kind'], 'correction_identity_mismatch'
        assert (raw['timeline_ms'],raw['period'],raw['period_elapsed_ms'])==(old['timeline_ms'],old['period'],old['period_elapsed_ms']), 'correction_clock_mismatch'
        identity = 'frame_id' if raw['kind']=='tracking_frame' else 'event_id'
        assert raw['payload'][identity]==old['payload'][identity], 'correction_logical_id_mismatch'
        assert raw['available_at_ms']>=old['available_at_ms'], 'correction_arrives_before_parent'
        assert prior_id not in superseded, 'forked_correction_lineage'
        superseded.add(prior_id)
    order = lambda m:(m['timeline_ms'],m['sequence_no'])
    original = sorted((m for m in unique.values() if m['revision']==1),key=order)
    result = validate(metadata,original,source_sequence=False)
    latest = sorted((m for mid,m in unique.items() if mid not in superseded),key=order)
    validate(metadata,latest,source_sequence=False)
    return result | {'delivery_rows':len(messages),'unique_observations':len(unique),
                     'exact_retransmissions':duplicates,'corrections':sum(m['revision']>1 for m in unique.values()),
                     'maximum_delivery_delay_ms':max((m['available_at_ms']-m['timeline_ms'] for m in messages),default=0)}


if __name__=='__main__':
    from engine.core import load_match
    for mid in ['match-001','match-002','match-003']:
        metadata,messages = load_match(mid)
        print(mid,json.dumps(validate(metadata,messages)))
