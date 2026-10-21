"""Deterministic, versioned evidence calculations; runtime reads no labels or seeds."""
from __future__ import annotations
import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONFIG={'version':'pressure-escape-v1','pressure_radius_m':6,'pressure_window_ms':2000,'minimum_coverage':.9,'minimum_bypassed':2,'minimum_progression_m':5,'retention_window_ms':3000,'maximum_gap_ms':200,'overlay_ttl_ms':30000}

def load_match(match_id):
    from engine.catalog import load_runtime_match
    return load_runtime_match(match_id)


def digest(value):
    # Cosmos/JavaScript JSON serializers may return 1.0 as 1. Numeric equality
    # must survive persistence without weakening string, array or field identity.
    def canonical(item):
        if isinstance(item,float):
            if not math.isfinite(item):raise ValueError('nonfinite_hash_operand')
            return int(item) if item.is_integer() else item
        if isinstance(item,dict):return {key:canonical(v) for key,v in item.items()}
        if isinstance(item,(list,tuple)):return [canonical(v) for v in item]
        return item
    return hashlib.sha256(json.dumps(canonical(value),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def available(messages,cutoff):
    # Deduplicate exact retransmissions and apply only delivered correction lineages.
    delivered={m['message_id']:m for m in messages if m['available_at_ms']<=cutoff and m['timeline_ms']<=cutoff}
    replaced={m['supersedes_message_id'] for m in delivered.values() if m.get('supersedes_message_id')}
    return sorted((m for key,m in delivered.items() if key not in replaced),key=lambda m:(m['timeline_ms'],m['sequence_no']))

def frame_at(messages,t):
    return max((m for m in messages if m['kind']=='tracking_frame' and m['timeline_ms']<=t),key=lambda m:(m['timeline_ms'],m['revision']),default=None)

def metric(messages,cutoff,meta,pass_id=None):
    """One explicitly scoped investigation; legacy default is the first pass."""
    obs=available(messages,cutoff)
    start=next((m for m in obs if m['kind']=='event' and m['payload']['type']=='pass_started'
                and (pass_id is None or m['payload']['details']['pass_id']==pass_id)),None)
    return _pass_metric(obs,cutoff,meta,start) if start else None


def pass_metrics(messages,cutoff,meta):
    """Investigate every delivered pass, without exposing any future outcome."""
    obs=available(messages,cutoff)
    starts=[m for m in obs if m['kind']=='event' and m['payload']['type']=='pass_started']
    values=[_pass_metric(obs,cutoff,meta,start) for start in starts]
    return [value for value in values if value is not None]


def _pass_metric(obs,cutoff,meta,start):
    team=start['payload']['team_id']; pass_id=start['payload']['details']['pass_id']
    end=next((m for m in obs if m['kind']=='event' and m['payload']['type']=='pass_resolved' and m['payload']['details']['pass_id']==pass_id),None)
    if not end:return None
    period=next(p for p in meta['periods'] if p['period']==start['period'])
    sign=1 if period['attack_direction'][team]=='right' else -1
    active={p['id'] for p in meta['players'] if p['team_id']!=team}
    pre=[m for m in obs if m['kind']=='tracking_frame' and start['timeline_ms']-CONFIG['pressure_window_ms']<=m['timeline_ms']<=start['timeline_ms']]
    valid=[]; counts=[]
    for m in pre:
        ps={p['player_id']:p for p in m['payload']['players']}
        passer=ps.get(start['payload']['player_id'])
        if not passer or not active.issubset(ps):continue
        counts.append(sum(math.hypot(passer['x_m']-ps[key]['x_m'],passer['y_m']-ps[key]['y_m'])<=CONFIG['pressure_radius_m'] for key in active))
        valid.append(m)
    expected=CONFIG['pressure_window_ms']*meta['tracking_hz']/1000+1
    coverage=min(1,len(valid)/expected)
    if not valid:return None
    sf=frame_at(obs,start['timeline_ms'])
    sx=start['payload']['details']['start_position']['x_m']; ex=end['payload']['details']['end_position']['x_m']
    bypass=[p['player_id'] for p in sf['payload']['players'] if p['team_id']!=team and sign*(p['x_m']-sx)>0 and sign*(ex-p['x_m'])>0]
    target=end['timeline_ms']+CONFIG['retention_window_ms']
    after=[m for m in obs if m['kind']=='tracking_frame' and end['timeline_ms']<=m['timeline_ms']<=target]
    times=[m['timeline_ms'] for m in after]
    complete=bool(times and times[0]==end['timeline_ms'] and times[-1]==target and all(b-a<=CONFIG['maximum_gap_ms'] for a,b in zip(times,times[1:])))
    confirmation=after[-1] if complete else None
    retained=all(m['payload']['possession_team_id']==team for m in after) and end['payload']['details']['outcome']=='received' if complete else None
    progression_raw=sign*(confirmation['payload']['ball']['x_m']-ex) if confirmation and confirmation['payload']['ball'] else None
    progression=round(progression_raw,1) if progression_raw is not None else None
    sources={m['message_id']:m for m in valid+after+[start,end,sf]}
    evidence_hash=digest(list(sources.values()))[:16]
    available_from=max([target]+[m['available_at_ms'] for m in sources.values()])
    return {'definition_version':CONFIG['version'],'input_cutoff_ms':max(m['available_at_ms'] for m in sources.values()),'pass_id':pass_id,'team_id':team,'passer_id':start['payload']['player_id'],'receiver_id':end['payload']['details']['controlling_player_id'] if end['payload']['details']['outcome']=='received' else None,'pressure_opponents_max':max(counts),'pressure_samples':len(valid),'pressure_radius_m':CONFIG['pressure_radius_m'],'pressure_window_ms':[start['timeline_ms']-CONFIG['pressure_window_ms'],start['timeline_ms']],'bypassed_count':len(bypass),'bypassed_player_ids':bypass,'pass_start':start['payload']['details']['start_position'],'pass_end':end['payload']['details']['end_position'],'retained':retained,'retention_window_ms':CONFIG['retention_window_ms'],'retention_confirmed_at_ms':target if complete else None,'progression_m':progression,'source_message_ids':sorted(sources),'evidence_revision':evidence_hash,'coverage':round(coverage,3),'available_from_ms':available_from,'limitations':['Pressure is opponent proximity, not a calibrated probability.','Bypassed counts longitudinal positions at release; it does not prove a defensive line was broken.','This sequence does not establish intent or sustained match control.'],'eligible':coverage>=CONFIG['minimum_coverage'] and max(counts)>=1 and len(bypass)>=CONFIG['minimum_bypassed'] and retained is True and progression_raw is not None and progression_raw>=CONFIG['minimum_progression_m']}

def visual_snapshot(messages,cutoff):
    obs=available(messages,cutoff); f=frame_at(obs,cutoff)
    return {'frame':f['payload'] if f else None,'frame_time_ms':f['timeline_ms'] if f else None,'delivered_count':len(obs)}
