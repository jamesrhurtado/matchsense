"""Versioned presentation fixture: authored movement, never a renderer animation.

The earlier discovery/correction exports remain immutable. This is a scripted
segment, not a tactical/physics simulation or evidence of football usefulness.
"""
from copy import deepcopy
import gzip
import hashlib
import json
import math
from pathlib import Path
from simulator.match_coverage import build as legacy_build
from simulator.suite import serialize
from engine.contracts import OBSERVATION

ROOT = Path(__file__).resolve().parents[1]
DEMO_IDS = ('match-0c0a000000000003', 'match-0c0a000000000004')


def interpolate(knots, t):
    if t <= knots[0][0]: return knots[0][1:]
    for a, b in zip(knots, knots[1:]):
        if t <= b[0]:
            r = (t-a[0])/(b[0]-a[0])
            return tuple(x+(y-x)*r for x,y in zip(a[1:],b[1:]))
    return knots[-1][1:]


def build(correction=False):
    meta, rows = legacy_build(correction)
    meta = deepcopy(meta)
    mid = DEMO_IDS[int(correction)]
    meta['match_id'] = mid
    meta['provenance_id'] = 'matchday-demo-v2'
    paths = {
        'blue-11': [(0,20,31),(6,26,30),(12,26,30),(18,36,26),(30,42,22),(50,48,20),(60,38,28),(74,26,30),(80,26,30),(88,36,26),(100,65,18),(110,60,25),(130,44,32),(145,34,32),(154,26,30),(160,26,30),(170,38,27),(185,46,24),(204,26,30),(210,26,30),(225,43,36),(240,56,30)],
        'blue-09': [(0,38,34),(6,44,33),(13.2,44,33),(16.2,51,33),(29,52,36),(35,62,34),(40,72,29),(45,82,30),(47,86,32),(60,62,30),(74,51,33),(81.2,51,33),(84.2,58,33),(94,76,32),(100,88,34),(104,95,34),(110,70,32),(130,60,30),(154,48,33),(161.2,48,33),(164.2,55,33),(179,66,38),(180,70,35),(190,56,40),(204,56,33),(211.3,56,33),(214.3,63,33),(240,80,37)],
        'blue-08': [(0,38,49),(20,45,44),(30,52,36),(33,56,35),(35,60,32),(50,58,42),(64,48,34),(70,42,32),(73,38,32),(90,60,43),(110,48,42),(140,43,48),(160,40,42),(200,45,43),(240,60,43)],
        'blue-06': [(0,40,43),(30,52,48),(60,45,50),(100,65,45),(130,48,42),(145,42,40),(150,48,36),(170,42,45),(200,38,45),(240,60,43)],
        'amber-08': [(0,60,40),(22,55,35),(47,84,35),(50,82,35),(64,58,42),(68,48,34),(70,46,32),(90,58,40),(110,52.5,34),(130,35,30),(145,40,40),(170,52,30),(180,70,35),(184,77,36),(190,90,60),(200,72,40),(240,48,40)],
    }
    formations = [(5,34),(20,14),(21,54),(30,20),(32,54),(42,44),(45,14),(48,46),(60,32),(62,51),(38,29)]
    def ambient(pid, t):
        team, number = pid.split('-'); i = int(number)-1
        x,y = formations[i]
        if team == 'amber': x = 105-x
        phase = i*.73 + (1.1 if team == 'amber' else 0)
        return (x+5*math.sin(t/9+phase), y+4*math.sin(t/7+phase))
    # Pressure anchors preserve the authored pass evidence windows, with continuous
    # approaches/exits. Other play moves independently between those windows.
    for number, point in [(6,(28,29)),(7,(29,33)),(8,(31,35))]:
        pid=f'amber-{number:02d}'
        anchors = {t:(x,y) for t,x,y in paths.get(pid, [(t,*ambient(pid,t)) for t in range(0,241,10)])}
        for start in (12,80,160,210):
            for t in list(anchors):
                if start-2 <= t <= start+8: del anchors[t]
            anchors[start-2] = point; anchors[start] = point
            anchors[start+8] = ambient(pid,start+8)
        paths[pid] = [(t,*p) for t,p in sorted(anchors.items())]
    def player_position(pid,t):
        if pid.endswith('-01'):
            # Scripted goalkeeper lanes, close to their own goal; not tactics.
            return (5+1.5*math.sin(t/11), 34+5*math.sin(t/9)) if pid.startswith('blue') else (100+1.5*math.sin(t/12),34+5*math.sin(t/10))
        return interpolate(paths[pid],t) if pid in paths else ambient(pid,t)
    def between(t,a,b,pa,pb):
        r=(t-a)/(b-a);return tuple(x+(y-x)*r for x,y in zip(pa,pb))
    def ball_state(t,positions):
        # Explicit authored intervals. Events below and tracking use this same script.
        control = None; owner = None; status = 'loose'; ball = None
        for start,end,actor in [(0,12,'blue-11'),(13.2,29,'blue-09'),(30,35,'blue-08'),(40,45,'blue-09'),(50,64,'amber-08'),(70,73,'blue-08'),(74,80,'blue-11'),(81.2,100,'blue-09'),(110,145,'amber-08'),(145,150,'blue-06'),(154,160,'blue-11'),(161.2,180,'blue-09'),(180,184,'amber-08'),(190,200,'amber-08'),(204,210,'blue-11'),(211.3,241,'blue-09')]:
            if start <= t < end:
                control=actor;owner=actor.split('-')[0];status='controlled';ball=positions[actor];break
        if ball is None:
            routes=[(12,13.2,(26,30),(44,33),'in_flight','blue'),(29,30,player_position('blue-09',29),player_position('blue-08',30),'loose',None),
                    (35,40,player_position('blue-08',35),player_position('blue-09',40),'in_flight','blue'),(45,46,(82,30),(102,30),'in_flight','blue'),
                    (46,47,(102,30),(96,32),'loose',None),(47,50,(96,32),player_position('amber-08',50),'loose',None),
                    (64,70,player_position('amber-08',64),player_position('blue-08',70),'loose',None),
                    (73,74,player_position('blue-08',73),(26,30),'loose',None),(80,81.2,(26,30),(51,33),'in_flight','blue'),
                    (100,101,(88,34),(105,34),'in_flight','blue'),(101,110,(105,34),(52.5,34),'out_of_play',None),
                    (150,154,player_position('blue-06',150),(26,30),'loose',None),(160,161.2,(26,30),(48,33),'in_flight','blue'),
                    (200,204,player_position('amber-08',200),(26,30),'loose',None),(210,211.3,(26,30),(56,33),'in_flight','blue')]
            for a,b,pa,pb,state,team in routes:
                if a <= t < b:ball=between(t,a,b,pa,pb);status=state;owner=team;break
            if 184 <= t < 190: status='unknown'
        return ball,status,control,owner
    # Keep the original event identities/availability policy, but use new match IDs.
    # Old incidental reset events described the old frame script and are removed.
    rows = [r for r in rows if not (r['kind']=='event' and (r['payload']['type']=='play_state_changed' or (r['payload']['type']=='possession_changed' and 'incident_id' not in r['payload']['details'])))]
    for row in rows:
        row['match_id'] = mid
        if row['kind'] != 'tracking_frame':continue
        t=row['timeline_ms']/1000;f=row['payload']
        positions={p['id']:player_position(p['id'],t) for p in meta['players']}
        for p in f['players']:
            p['x_m'],p['y_m']=(round(v,4) for v in positions[p['player_id']])
        ball,status,controller,owner=ball_state(t,positions)
        f.update(ball={'x_m':round(ball[0],4),'y_m':round(ball[1],4),'z_m':0,'quality':'simulated_observation'} if ball else None,
                 ball_status=status,controlling_player_id=controller,possession_team_id=owner)
    for t,previous,new,controller in [(74000,None,'blue','blue-11'),(154000,None,'blue','blue-11'),(180000,'blue','amber','amber-08'),(204000,None,'blue','blue-11')]:
        rows.append({'schema_version':'1.0.0','match_id':mid,'message_id':f'demo-control-{t}','sequence_no':len(rows)+1,'timeline_ms':t,'period':1,'period_elapsed_ms':t,'available_at_ms':t,'revision':1,'supersedes_message_id':None,'kind':'event','payload':{'event_id':f'demo-control-{t}','type':'possession_changed','team_id':new,'player_id':controller,'possession_id':None,'details':{'incident_id':f'demo-control-{t}','previous_team_id':previous,'new_team_id':new,'controlling_player_id':controller,'reason':'observed control'}}})
    rows.sort(key=lambda r:(r['timeline_ms'],r['kind']=='event',r['sequence_no']))
    for i,row in enumerate(rows):row['sequence_no']=i;OBSERVATION.validate_python(row)
    rows.sort(key=lambda r:(r['available_at_ms'],r['sequence_no']))
    return meta, rows


def main():
    catalog_path=ROOT/'data/runtime/match-coverage-catalog.json'
    catalog=json.loads(catalog_path.read_text())
    manifest=[]
    for correction in (False,True):
        meta,rows=build(correction);mid=meta['match_id'];folder=ROOT/'data/runtime'/mid;folder.mkdir(exist_ok=True)
        raw=gzip.compress(serialize(rows).encode(),mtime=0)
        (folder/'match.json').write_text(json.dumps(meta,indent=2)+'\n');(folder/'stream.jsonl.gz').write_bytes(raw)
        catalog=[r for r in catalog if r['match_id']!=mid]+[{'match_id':mid,'label':'Guided matchday demo'+(' · score correction' if correction else ' · moving play and mixed events'),'duration_ms':240000,'synthetic':True}]
        manifest.append({'match_id':mid,'sha256':hashlib.sha256(raw).hexdigest(),'observations':len(rows)})
    catalog_path.write_text(json.dumps(catalog,indent=2)+'\n')
    (ROOT/'data/provenance/matchday-demo-v2.json').write_text(json.dumps({'generator':'simulator.matchday_demo','status':'Authored presentation segment; football review pending; legacy fixtures unchanged','cases':manifest},indent=2)+'\n')
    print('Exported versioned moving matchday demos; legacy observations unchanged.')

if __name__=='__main__':main()
