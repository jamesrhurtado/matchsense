"""Add two varied synthetic discovery replays. No references in runtime export."""
from copy import deepcopy
import gzip
import json
import hashlib
from pathlib import Path
from simulator.scenarios import Case, Parent
from simulator.suite import generate_case, serialize
from engine.contracts import OBSERVATION

ROOT=Path(__file__).resolve().parents[1]
DISCOVERY_ID='match-0c0a000000000001'
CORRECTION_ID='match-0c0a000000000002'


def build(correction=False):
    case=Case('coverage-corrections' if correction else 'coverage-discovery',Parent('coverage-parent','discovery',26,30,30,False,'blue',12000,9111),'long_session')
    data=generate_case(case,passage_schedule=[{'release_ms':t,'forward_m':d} for t,d in [(12000,18),(80000,25),(160000,22),(210000,30)]])
    mid=CORRECTION_ID if correction else DISCOVERY_ID
    meta=deepcopy(data.metadata);meta['match_id']=mid
    rows=deepcopy(data.observations)
    for m in rows:
        m['match_id']=mid
        if m['kind']=='tracking_frame':
            t=m['timeline_ms'];f=m['payload']
            if 50000<=t<70000 or 110000<=t<145000:
                f['possession_team_id']='amber'
                if f['ball_status']=='controlled':f.update(ball_status='in_flight',controlling_player_id=None)
            if 29000<=t<30000:f.update(ball_status='loose',possession_team_id=None,controlling_player_id=None)
            if 103000<=t<110000:f.update(ball_status='out_of_play',possession_team_id=None,controlling_player_id=None)
    seq=len(rows)+1
    def event(t,kind,details,team='blue',player=None,available=None,identity=None,revision=1,supersedes=None):
        nonlocal seq
        identity=identity or f'{kind}-{t}-r{revision}'
        row={'schema_version':'1.0.0','match_id':mid,'message_id':identity,'sequence_no':seq,'timeline_ms':t,
             'period':1,'period_elapsed_ms':t,'available_at_ms':available or t,'revision':revision,'supersedes_message_id':supersedes,
             'kind':'event','payload':{'event_id':f'{kind}-{t}','type':kind,'team_id':team,'player_id':player,'possession_id':None,'details':details}}
        OBSERVATION.validate_python(row);rows.append(row);seq+=1;return identity
    event(0,'period_state_changed',{'status':'started'},None)
    event(30000,'ball_recovered',{'incident_id':'loose-1','previous_team_id':None,'cause':'loose_ball'},player='blue-08')
    event(45000,'shot_started',{'shot_id':'attempt-1','location':{'x_m':82,'y_m':30}},player='blue-09')
    event(46000,'shot_resolved',{'shot_id':'attempt-1','outcome':'saved'},player='blue-09')
    event(50000,'possession_changed',{'incident_id':'change-1','previous_team_id':'blue','new_team_id':'amber','controlling_player_id':None,'reason':'observed control'},'amber')
    event(70000,'ball_recovered',{'incident_id':'change-2','previous_team_id':'amber','cause':'interception'},player='blue-08')
    event(70000,'possession_changed',{'incident_id':'change-2','previous_team_id':'amber','new_team_id':'blue','controlling_player_id':'blue-08','reason':'observed control'})
    event(100000,'shot_started',{'shot_id':'attempt-2','location':{'x_m':88,'y_m':34}},player='blue-09')
    event(101000,'shot_resolved',{'shot_id':'attempt-2','outcome':'goal'},player='blue-09')
    first=event(101000,'goal_status_changed',{'goal_id':'goal-1','status':'pending','scorer_id':'blue-09','shot_id':'attempt-2'},available=102000)
    confirmed=event(101000,'goal_status_changed',{'goal_id':'goal-1','status':'confirmed','scorer_id':'blue-09','shot_id':'attempt-2'},available=104000,revision=2,supersedes=first)
    event(110000,'possession_changed',{'incident_id':'restart-1','previous_team_id':None,'new_team_id':'amber','controlling_player_id':None,'reason':'restart'},'amber')
    event(145000,'ball_recovered',{'incident_id':'recovery-3','previous_team_id':'amber','cause':'tackle'},player='blue-06')
    event(185000,'shot_started',{'shot_id':'attempt-3','location':None},'amber',None)
    event(186000,'shot_resolved',{'shot_id':'attempt-3','outcome':'off_target'},'amber',None)
    if correction:
        event(101000,'goal_status_changed',{'goal_id':'goal-1','status':'cancelled','scorer_id':None,'shot_id':'attempt-2'},available=135000,revision=3,supersedes=confirmed)
    rows.sort(key=lambda m:(m['timeline_ms'],m['sequence_no']))
    for i,m in enumerate(rows):m['sequence_no']=i;OBSERVATION.validate_python(m)
    rows.sort(key=lambda m:(m['available_at_ms'],m['sequence_no']))
    return meta,rows


def main():
    path=ROOT/'data/runtime/match-coverage-catalog.json';catalog=json.loads(path.read_text()) if path.exists() else [];manifest=[]
    for correction in [False,True]:
        meta,rows=build(correction);mid=meta['match_id'];folder=ROOT/'data/runtime'/mid;folder.mkdir(exist_ok=True)
        raw=serialize(rows).encode();compressed=gzip.compress(raw,mtime=0)
        (folder/'match.json').write_text(json.dumps(meta,indent=2)+'\n');(folder/'stream.jsonl.gz').write_bytes(compressed)
        row={'match_id':mid,'label':('Mixed-event correction replay' if correction else 'Mixed-event discovery · goals, shots, possession, recoveries'),'duration_ms':240000,'synthetic':True}
        catalog=[r for r in catalog if r['match_id']!=mid]+[row]
        manifest.append({'match_id':mid,'sha256':hashlib.sha256(compressed).hexdigest(),'observations':len(rows)})
    path.write_text(json.dumps(catalog,indent=2)+'\n')
    (ROOT/'data/provenance/match-coverage.json').write_text(json.dumps({'generator':'simulator.match_coverage','status':'Developer discovery; football review pending; original 173 entries unchanged','cases':manifest},indent=2)+'\n')
    print('Exported two 4-minute observation-only mixed replays.')

if __name__=='__main__':main()
