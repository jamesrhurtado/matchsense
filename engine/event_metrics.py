"""Event-neutral facts; no model, reference labels or future data access."""
from engine.core import available, digest
from engine.match_state import latest_events, match_state

FAMILY_PRIORITY={'goal':0,'shot':1,'pressure':2,'recovery':3,'possession':4,'pass':5}


def possession_window(meta,messages,cutoff,end,start=None):
    start=max(0,end-60000) if start is None else start
    if end>cutoff or end<start:raise ValueError('future_or_invalid_window')
    obs=available(messages,cutoff)
    # Only within the period containing this boundary. Preceding time is unknown.
    period=max((p for p in meta['periods'] if p['timeline_offset_ms']<=end),key=lambda p:p['timeline_offset_ms'])
    start=max(start,period['timeline_offset_ms'])
    ended=[m for m in obs if m['kind']=='event' and m['period']==period['period'] and m['payload']['type']=='period_state_changed' and m['payload']['details']['status']=='ended' and m['timeline_ms']<=end]
    if ended:end=max(start,min(end,min(m['timeline_ms'] for m in ended)))
    frames=[m for m in obs if m['kind']=='tracking_frame' and m['period']==period['period'] and start-200<=m['timeline_ms']<=end]
    by_time={}
    for m in frames:
        old=by_time.get(m['timeline_ms'])
        if old is None or (m['revision'],m['sequence_no'],m['message_id'])>(old['revision'],old['sequence_no'],old['message_id']):by_time[m['timeline_ms']]=m
    frames=sorted(by_time.values(),key=lambda m:m['timeline_ms'])
    team_ms={t['id']:0 for t in meta['teams']};dead=loose=known=0
    dependencies=list(ended)
    for a,b in zip(frames,frames[1:]):
        left=max(start,a['timeline_ms']);right=min(end,b['timeline_ms'])
        if right<=left:continue
        dependencies.extend([a,b])
        if b['timeline_ms']-a['timeline_ms']>200:continue
        f=a['payload'];dt=right-left
        if f['ball_status']=='out_of_play':dead+=dt
        elif f['ball_status']=='loose':loose+=dt
        elif f['ball_status'] in {'controlled','in_flight'} and f['possession_team_id'] in team_ms:
            team_ms[f['possession_team_id']]+=dt;known+=dt
    unknown=end-start-known-dead-loose
    coverage=known/(known+unknown) if known+unknown else 0
    sufficient=known>=30000 and coverage>=.95
    sources={m['message_id']:m for m in dependencies}
    return {'window_start_ms':start,'window_end_ms':end,'team_ms':team_ms,'assigned_ms':known,'unknown_ms':unknown,'dead_ms':dead,'loose_ms':loose,
            'coverage':coverage,'percentages':{t:v/known*100 for t,v in team_ms.items()} if sufficient else None,
            'status':'available' if sufficient else 'insufficient_evidence','period':period['period'],
            'source_message_ids':sorted(sources),'source_hashes':[digest(sources[k]) for k in sorted(sources)],
            'input_cutoff_ms':max([end]+[m['available_at_ms'] for m in sources.values()])}


def event_metrics(meta,messages,cutoff):
    obs=available(messages,cutoff);teams={t['id'] for t in meta['teams']};players={p['id']:p for p in meta['players']}
    result=[]
    def actor(pid,team,own=False):
        return pid if pid in players and (own or players[pid]['team_id']==team) else None
    def add(family,subject,incident,team,roles,rows,facts,occur=None,ready=None,expires=None):
        sources={m['message_id']:m for m in rows}
        hashes=[digest(sources[k]) for k in sorted(sources)]
        ready=max([m['available_at_ms'] for m in rows]+[ready or 0])
        occur=min(m['timeline_ms'] for m in rows) if occur is None else occur
        value={'family':family,'subject_id':subject,'incident_id':incident,'team_id':team,'participants':roles,
               'occurrence_ms':occur,'evidence_ready_ms':ready,'input_cutoff_ms':ready,
               'window_start_ms':min(m['timeline_ms'] for m in rows),'window_end_ms':max(m['timeline_ms'] for m in rows),
               'source_message_ids':sorted(sources),'source_hashes':hashes,'facts':facts,'eligible':True,
               'definition_version':'match-events-v1','expires_at_ms':expires if expires is not None else ready+30000}
        value['evidence_revision']=digest(value)[:16]
        result.append(value)
    starts=latest_events(messages,cutoff,'shot_started','shot_id')
    goals=latest_events(messages,cutoff,'goal_status_changed','goal_id')
    # A shot goal is incomplete until source goal confirmation. Include the
    # available linked goal dependency, so confirmation/cancellation revises prose.
    for sid,end in latest_events(messages,cutoff,'shot_resolved','shot_id').items():
        start=starts.get(sid)
        if not start:continue
        p=end['payload'];d=p['details'];team=start['payload']['team_id']
        if team not in teams or p['team_id']!=team:continue
        linked=sorted([g for g in goals.values() if g['payload']['details'].get('shot_id')==sid],key=lambda m:(m['available_at_ms'],m['message_id']))
        goal=linked[-1] if linked else None
        status=goal['payload']['details']['status'] if goal else None
        outcome=d['outcome']
        if outcome=='goal' and status!='confirmed':outcome='unknown'
        add('shot',sid,f'shot:{sid}',team,{'shooter':actor(start['payload']['player_id'],team)},[start,end]+([goal] if goal else []),
            {'outcome':outcome,'reported_outcome':d['outcome'],'goal_status':status,'location':start['payload']['details'].get('location')})
    for gid,g in goals.items():
        p=g['payload'];d=p['details'];team=p['team_id']
        if d['status']!='confirmed' or team not in teams:continue
        scorer=actor(d.get('scorer_id'),team,d.get('own_goal',False))
        # score transition is scoped to this goal's occurrence, independent of approval.
        state=match_state(meta,messages,min(cutoff,g['available_at_ms']))
        before=dict(state['score']);before[team]-=1
        score_sources=list(latest_events(messages,min(cutoff,g['available_at_ms']),'goal_status_changed','goal_id').values())
        add('goal',gid,f'shot:{d["shot_id"]}' if d.get('shot_id') else f'goal:{gid}',team,{'scorer':scorer},score_sources,
            {'status':'confirmed','own_goal':d.get('own_goal',False),'score':state['score'],'score_before':before,'shot_id':d.get('shot_id')},occur=g['timeline_ms'])
    changes={}
    for m in obs:
        if m['kind']!='event' or m['payload']['type'] not in {'possession_changed','ball_recovered'}:continue
        p=m['payload'];d=p['details']
        incident=f'pass:{d["pass_id"]}' if d.get('pass_id') else d.get('incident_id') or p['event_id']
        changes.setdefault(incident,[]).append(m)
    for incident,rows in changes.items():
        recovery=next((m for m in reversed(rows) if m['payload']['type']=='ball_recovered'),None)
        m=recovery or rows[-1];p=m['payload'];d=p['details'];team=p['team_id'] if recovery else d['new_team_id'];previous=d['previous_team_id']
        if team not in teams or previous==team:continue
        pid=actor(p['player_id'],team) if recovery else None
        sustained=False;extra=[]
        target=m['timeline_ms']+3000
        if cutoff>=target:
            window=possession_window(meta,messages,cutoff,target,m['timeline_ms'])
            sustained=window['team_ms'].get(team,0)>=3000 and window['unknown_ms']==0 and window['loose_ms']==0 and window['dead_ms']==0
            # Freeze dependencies even for failed confirmation to detect corrections.
            extra=[r for r in obs if r['message_id'] in window['source_message_ids']]
        add('recovery',incident,f'control:{incident}',team,{'recovering_player':pid},rows+extra,
            {'previous_team_id':previous,'new_team_id':team,'cause':d.get('cause','unknown') if recovery else 'unknown',
             'kind':'recovery' if recovery else ('control_change' if previous else 'restart'), 'sustained':sustained},
            occur=m['timeline_ms'])
    for end in range(15000,cutoff+1,15000):
        w=possession_window(meta,messages,cutoff,end)
        rows=[m for m in obs if m['message_id'] in w['source_message_ids']]
        if not rows:continue
        add('possession',str(end),f'possession:{end}',None,{},rows,w,occur=end,ready=max(end,w['input_cutoff_ms']),expires=max(end+15000,w['input_cutoff_ms']))
    return sorted(result,key=lambda m:(FAMILY_PRIORITY[m['family']],-m['occurrence_ms'],m['subject_id']))
