"""Pure availability-scoped source state. Editorial actions never affect score."""
from engine.core import available


def latest_events(messages, cutoff, kind, key):
    rows={}
    for m in available(messages,cutoff):
        if m['kind']!='event' or m['payload']['type']!=kind:continue
        identity=m['payload']['details'][key]
        rank=lambda x:(x['revision'],x['available_at_ms'],x['sequence_no'],x['message_id'])
        if identity not in rows or rank(m)>rank(rows[identity]):rows[identity]=m
    return rows


def match_state(meta,messages,cutoff):
    obs=available(messages,cutoff)
    teams={t['id'] for t in meta['teams']}
    score=dict(meta['initial_state']['score'])
    goals=latest_events(messages,cutoff,'goal_status_changed','goal_id')
    for m in goals.values():
        p=m['payload']
        if p['team_id'] in teams and p['details']['status']=='confirmed':score[p['team_id']]+=1
    # Source period observations take precedence; latest clock observation supplies
    # clock context. Never extrapolate beyond an explicit period end.
    anchor=max(obs,key=lambda m:(m['timeline_ms'],m['revision'],m['sequence_no']),default=None)
    period=anchor['period'] if anchor else meta['initial_state']['period']
    state=next((m for m in reversed(obs) if m['kind']=='event' and m['payload']['type']=='period_state_changed' and m['period']==period),None)
    running=not state or state['payload']['details']['status']=='started'
    if not running:anchor=state
    elapsed=(anchor['period_elapsed_ms']+max(0,cutoff-anchor['timeline_ms']) if running else anchor['period_elapsed_ms']) if anchor else meta['initial_state']['period_elapsed_ms']+cutoff
    return {'score':score,'period':period,'period_elapsed_ms':elapsed,'period_status':'running' if running else 'ended',
            'source_status':'Source-confirmed state · explanations require approval','cutoff_ms':cutoff}
