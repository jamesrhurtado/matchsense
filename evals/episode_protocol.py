"""QA-only real-clock period excerpt; never in the playable demo catalogue.

Derived from d05-a. Explicitly omits a 15-minute halftime: it is not continuous
playback or a seventh independent scene. Checks direction and clock conventions
without describing a 45-second period as a real football half.
"""
from copy import deepcopy
from evals.episodes import load


def period_excerpt():
    metadata,source=load('d05-a')
    metadata=deepcopy(metadata)
    metadata['initial_state']['period_elapsed_ms']=2690000
    metadata['periods'].append({'period':2,'timeline_offset_ms':3600000,
                                'attack_direction':{'blue':'left','amber':'right'}})
    rows=[]
    for original in source:
        t=original['timeline_ms']
        if not (t<=10000 or t>=60000):continue
        if original['kind']=='event' and original['payload']['type']=='period_state_changed':continue
        row=deepcopy(original)
        if t<=10000:
            row.update(timeline_ms=t+2690000,period_elapsed_ms=t+2690000,available_at_ms=t+2690000)
            if t==10000 and row['kind']=='tracking_frame':
                row['payload'].update(ball_status='out_of_play',controlling_player_id=None,possession_team_id=None)
        else:
            row.update(timeline_ms=t-60000+3600000,period=2,period_elapsed_ms=t-60000,available_at_ms=t-60000+3600000)
            def reflect(item):
                if isinstance(item,dict):
                    if 'x_m' in item:item['x_m']=round(105-item['x_m'],4)
                    for value in item.values():reflect(value)
                elif isinstance(item,list):
                    for value in item:reflect(value)
            reflect(row['payload'])
        rows.append(row)
    def state(t,period,elapsed,status,identity):
        return {'schema_version':'1.0.0','match_id':metadata['match_id'],'message_id':identity,
                'sequence_no':0,'timeline_ms':t,'period':period,'period_elapsed_ms':elapsed,
                'available_at_ms':t,'revision':1,'supersedes_message_id':None,'kind':'event',
                'payload':{'event_id':identity,'type':'period_state_changed','team_id':None,
                           'player_id':None,'possession_id':None,'details':{'status':status}}}
    rows.extend([state(2700000,1,2700000,'ended','boundary-end'),state(3600000,2,0,'started','boundary-start')])
    rows.sort(key=lambda r:(r['timeline_ms'],r['kind']=='event'))
    for i,row in enumerate(rows):row['sequence_no']=i
    return metadata,rows
