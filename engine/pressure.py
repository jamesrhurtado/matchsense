"""Pressure Swing v1: observed nearby-opponent change, never tactical causation."""
import math
from engine.core import available, digest, pass_metrics
from engine.context import contextual_metrics


def proximity_window(meta, messages, cutoff, start, end, actor, team):
    """Integrate left-observed counts; absent/gapped intervals remain uncovered.

    Both endpoints need positions; only the left endpoint needs control because
    the right endpoint may be the release boundary of the half-open window.
    """
    frames=sorted((m for m in available(messages,cutoff) if m['kind']=='tracking_frame' and start<=m['timeline_ms']<=end),key=lambda m:m['timeline_ms'])
    opponents={p['id'] for p in meta['players'] if p['team_id']!=team}
    known=weighted=0;dependencies={}
    for a,b in zip(frames,frames[1:]):
        left=max(start,a['timeline_ms']);right=min(end,b['timeline_ms']);dt=right-left
        if dt<=0:continue
        dependencies[a['message_id']]=a;dependencies[b['message_id']]=b
        positions={p['player_id']:p for p in a['payload']['players']}
        next_positions={p['player_id']:p for p in b['payload']['players']}
        if a['period']!=b['period'] or dt>200 or not ({actor}|opponents)<=positions.keys() or not ({actor}|opponents)<=next_positions.keys():continue
        f=a['payload']
        if f['ball_status']!='controlled' or f['controlling_player_id']!=actor or f['possession_team_id']!=team:continue
        p=positions[actor]
        count=sum(math.hypot(p['x_m']-positions[pid]['x_m'],p['y_m']-positions[pid]['y_m'])<=6 for pid in opponents)
        known+=dt;weighted+=count*dt
    return {'start_ms':start,'end_ms':end,'known_ms':known,'coverage':known/(end-start),'mean':weighted/known if known else None},dependencies


def pressure_metrics(meta,messages,cutoff):
    """Publish no insight unless the existing pass and both windows qualify."""
    result=[];observed={m['message_id']:m for m in available(messages,cutoff)}
    for m in pass_metrics(messages,cutoff,meta):
        if not m['eligible']:continue
        context=contextual_metrics(m,meta,messages,cutoff)['context']
        release=context['release_ms'];
        period_start=max(p['timeline_offset_ms'] for p in meta['periods'] if p['timeline_offset_ms']<=release)
        if release-2000<period_start:continue
        reception=m['retention_confirmed_at_ms']-3000;team=m['team_id']
        forward=context['current_forward_m']
        before,bs=proximity_window(meta,messages,cutoff,release-2000,release,m['passer_id'],team)
        after,as_=proximity_window(meta,messages,cutoff,reception,reception+2000,m['receiver_id'],team)
        if min(before['coverage'],after['coverage'])<.95 or before['mean'] is None or after['mean'] is None:continue
        drop=before['mean']-after['mean']
        if before['mean']<1 or drop<1 or (forward is None or forward<10):continue
        sources={**bs,**as_,**{id:observed[id] for id in m['source_message_ids'] if id in observed}}
        for id in context['source_message_ids']:
            if id in observed:sources[id]=observed[id]
        comparators=[{'pass_id':c['pass_id'],'forward_m':c['forward_m'],'resolution_ms':c['resolution_ms']} for c in context['comparators']]
        ready=max(m['available_from_ms'],*[r['available_at_ms'] for r in sources.values()])
        facts={'before':before,'after':after,'radius_m':6,'drop':drop,'forward_m':forward,
               'pass_id':m['pass_id'],'release_ms':release,'reception_ms':reception,'retained_ms':3000,
               'retained_progression_m':m['progression_m'],'comparators':comparators,
               'comparison_status':context['status'],'stands_out':context['relation']=='greater_than_each'}
        value={'family':'pressure','subject_id':m['pass_id'],'incident_id':f'story-{m["pass_id"]}','team_id':team,
               'participants':{'passer':m['passer_id'],'receiver':m['receiver_id']},'occurrence_ms':release,
               'evidence_ready_ms':ready,'input_cutoff_ms':ready,'window_start_ms':release-2000,'window_end_ms':m['retention_confirmed_at_ms'],
               'source_message_ids':sorted(sources),'source_hashes':[digest(sources[id]) for id in sorted(sources)],
               'facts':facts,'eligible':True,'definition_version':'nearby-pressure-swing-v1','expires_at_ms':ready+30000}
        value['evidence_revision']=digest(value)[:16];result.append(value)
    return result
