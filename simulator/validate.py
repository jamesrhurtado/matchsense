"""Structural, temporal and physical validation independent of story detection."""
from __future__ import annotations
import json
import math
from pathlib import Path
from engine.contracts import MatchMetadata,OBSERVATION

def validate(metadata,messages):
    MatchMetadata.model_validate(metadata)
    active=set(metadata['initial_state']['active_player_ids']);roster={p['id']:p for p in metadata['players']}
    assert active==set(roster),'active_roster_mismatch'
    assert len(active)==22,'expected_22_players'
    assert len({m['message_id'] for m in messages})==len(messages),'duplicate_source_ids'
    last=None;starts={};last_seq=-1
    for raw in messages:
        OBSERVATION.validate_python(raw)
        assert raw['match_id']==metadata['match_id'],'cross_match_observation'
        assert raw['sequence_no']>last_seq,'source_sequence_not_increasing'
        last_seq=raw['sequence_no']
        p=raw['payload']
        if raw['kind']=='tracking_frame':
            positions={x['player_id']:x for x in p['players']}
            assert set(positions)|set(p['missing_player_ids'])==active,'active_coverage_mismatch'
            for key,pos in positions.items():assert roster[key]['team_id']==pos['team_id'],'wrong_team'
            if p['controlling_player_id']:
                controller=positions.get(p['controlling_player_id'])
                if controller and p['ball']:
                    assert math.dist((controller['x_m'],controller['y_m']),(p['ball']['x_m'],p['ball']['y_m']))<1.1,'controller_far_from_ball'
                    assert controller['team_id']==p['possession_team_id'],'controller_wrong_possession'
            if last:
                dt=(raw['timeline_ms']-last['timeline_ms'])/1000
                assert dt>0,'frame_time_not_increasing'
                prev={x['player_id']:x for x in last['payload']['players']}
                for key,pos in positions.items():
                    if key in prev:assert math.dist((pos['x_m'],pos['y_m']),(prev[key]['x_m'],prev[key]['y_m']))/dt<=10,'player_speed_over_10_mps'
                if p['ball'] and last['payload']['ball']:
                    a=p['ball'];b=last['payload']['ball']
                    assert math.dist((a['x_m'],a['y_m']),(b['x_m'],b['y_m']))/dt<=30,'ball_speed_over_30_mps'
            last=raw
        elif p['type']=='pass_started':
            starts[p['details']['pass_id']]=raw
            assert not {'outcome','end_position','controlling_team_id'}&set(p['details']),'future_pass_outcome'
        elif p['type']=='pass_resolved':
            assert p['details']['pass_id'] in starts,'resolution_without_start'
            assert last and last['timeline_ms']==raw['timeline_ms'],'resolution_not_aligned_to_frame'
            ball=last['payload']['ball'];end=p['details']['end_position']
            assert math.dist((ball['x_m'],ball['y_m']),(end['x_m'],end['y_m']))<.01,'resolution_endpoint_mismatch'
    return {'frames':sum(m['kind']=='tracking_frame' for m in messages),'messages':len(messages),'duration_ms':messages[-1]['timeline_ms'],'active_players':len(active)}

if __name__=='__main__':
    from engine.core import load_match
    for mid in ['match-001','match-002','match-003']:
        metadata,messages=load_match(mid);print(mid,json.dumps(validate(metadata,messages)))
