"""Additive pressure flagship. Authored observations, not simulated tactics."""
from copy import deepcopy
import gzip
import hashlib
import json
from simulator.matchday_demo import build as moving_build, interpolate, ROOT
from simulator.suite import serialize
from engine.contracts import OBSERVATION

IDS=('match-0c0a000000000005','match-0c0a000000000006')


def build(correction=False):
    meta,rows=moving_build(correction);meta=deepcopy(meta)
    meta.update(match_id=IDS[int(correction)],provenance_id='pressure-flagship-v1')
    frames={r['timeline_ms']/1000:deepcopy(r['payload']) for r in rows if r['kind']=='tracking_frame'}
    def original(pid,t):
        p=next(p for p in frames[round(t,1)]['players'] if p['player_id']==pid)
        return p['x_m'],p['y_m']
    paths={}
    def patch(pid,start,end,knots):
        paths.setdefault(pid,[]).append([(start,*original(pid,start)),*knots,(end,*original(pid,end))])
    for release,reception,receive_x in [(37,38.2,51),(62,63.2,48),(87,88.3,56)]:
        patch('blue-11',release-8,release+6,[(release-2,26,30),(release,26,30)])
        patch('blue-09',release-4,reception+5.7,[(reception,receive_x,33),(reception+3,receive_x+7,33)])
        for n,point in [(6,(28,29)),(7,(29,33)),(8,(31,35))]:
            patch(f'amber-{n:02d}',release-8,release+6,[(release-2,*point),(release,*point)])
    # The passer is waiting at the authored acquisition location before control.
    for segments in paths['blue-11']:
        if segments[0][0]==54:segments.insert(1,(58,26,30))
    def position(pid,t):
        for knots in paths.get(pid,[]):
            if knots[0][0]<=t<=knots[-1][0]:return interpolate(knots,t)
        return original(pid,t)
    for row in rows:
        row['match_id']=meta['match_id']
        if row['kind']=='event':
            e=row['payload']
            if e['type'] in ('pass_started','pass_received','pass_completed','pass_resolved'):
                # Source passes retain identities but now form a two-minute comparison.
                for old,new in [(80000,37000),(160000,62000),(210000,87000)]:
                    if old<=row['timeline_ms']<=old+1300:
                        delta=new-old
                        for key in ('timeline_ms','period_elapsed_ms','available_at_ms'):row[key]+=delta
                        break
            if row['timeline_ms']==70000 and e['type']=='ball_recovered':
                e['details'].update(previous_team_id=None,cause='loose_ball')
            continue
        if row['kind']!='tracking_frame':continue
        t=row['timeline_ms']/1000;f=row['payload']
        for p in f['players']:
            p['x_m'],p['y_m']=(round(v,4) for v in position(p['player_id'],t))
        actor=f['controlling_player_id'];ball=None;status=f['ball_status'];team=f['possession_team_id']
        # Replace only the new authored possession/pass intervals.
        for a,b,release,reception,x in [(33,44,37,38.2,51),(56,70,62,63.2,48),(83,94,87,88.3,56)]:
            if not a<=t<b:continue
            actor=None;team=None;status='loose'
            if t<release-2:
                oldball=frames[a]['ball']
                oldpoint=position(frames[a]['controlling_player_id'],a) if frames[a]['controlling_player_id'] else (oldball['x_m'],oldball['y_m'])
                ball=interpolate([(a,*oldpoint),(release-2,26,30)],t)
            elif t<release:
                actor='blue-11'
            elif t<reception:
                ball=interpolate([(release,26,30),(reception,x,33)],t);status='in_flight';team='blue'
            elif t<=reception+3:
                actor='blue-09'
            else:
                target=frames[b]['ball']
                ball=interpolate([(reception+3,x+7,33),(b,target['x_m'],target['y_m'])],t)
            if actor:team='blue';status='controlled';ball=position(actor,t)
            f.update(ball_status=status,controlling_player_id=actor,possession_team_id=team)
            break
        else:
            if actor:ball=position(actor,t)
        if ball is not None:f['ball']={'x_m':round(ball[0],4),'y_m':round(ball[1],4),'z_m':0,'quality':'simulated_observation'}
    # The old 70s possession switch is no longer part of this version's script.
    rows=[r for r in rows if not(r['kind']=='event' and r['timeline_ms']==70000 and r['payload']['type']=='possession_changed')]
    template=deepcopy(next(r for r in rows if r['kind']=='event' and r['payload']['type']=='ball_recovered'))
    template.update(message_id='flagship-recovery-60000',timeline_ms=60000,period_elapsed_ms=60000,available_at_ms=60000,sequence_no=len(rows))
    template['payload'].update(event_id='flagship-recovery-60000',player_id='blue-11')
    template['payload']['details'].update(incident_id='flagship-recovery-60000',previous_team_id='amber',cause='unknown')
    rows.append(template)
    rows.sort(key=lambda r:(r['timeline_ms'],r['kind']=='event',r['sequence_no']))
    for i,r in enumerate(rows):r['sequence_no']=i;OBSERVATION.validate_python(r)
    rows.sort(key=lambda r:(r['available_at_ms'],r['sequence_no']))
    return meta,rows


def main():
    path=ROOT/'data/runtime/match-coverage-catalog.json';catalog=json.loads(path.read_text());cases=[]
    for correction in (False,True):
        meta,rows=build(correction);mid=meta['match_id'];folder=ROOT/'data/runtime'/mid;folder.mkdir(exist_ok=True)
        raw=gzip.compress(serialize(rows).encode(),mtime=0)
        (folder/'match.json').write_text(json.dumps(meta,indent=2)+'\n');(folder/'stream.jsonl.gz').write_bytes(raw)
        catalog=[r for r in catalog if r['match_id']!=mid]+[{'match_id':mid,'label':'Pressure Swing flagship'+(' · score correction' if correction else ' · guided mixed-event pitch'),'duration_ms':240000,'synthetic':True}]
        cases.append({'match_id':mid,'sha256':hashlib.sha256(raw).hexdigest(),'observations':len(rows)})
    path.write_text(json.dumps(catalog,indent=2)+'\n')
    (ROOT/'data/provenance/pressure-flagship-v1.json').write_text(json.dumps({'generator':'simulator.flagship','status':'Authored demonstration; football review pending; old exports unchanged','cases':cases},indent=2)+'\n')

if __name__=='__main__':main()
