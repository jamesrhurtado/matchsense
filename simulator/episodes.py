"""Observation-only exports from constrained authored episodes (SD01–SD04).

World definitions, profiles and case ancestry are authoring inputs. Neither
references nor production story detectors are imported. Runtime reads only the
two exported observation files and an opt-in display catalogue.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import gzip
import hashlib
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from engine.contracts import MatchMetadata, OBSERVATION
from simulator.episode_scenes import scene_for

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'constrained-episodes-v1'
PROFILE = ROOT / 'data/provenance/episode-profile-v1.json'


@dataclass(frozen=True)
class Case:
    parent: int
    paired: bool = False

    @property
    def case_id(self):
        return f'd{self.parent:02}-{ "b" if self.paired else "a"}'

    def match_id(self, faults=False):
        return 'match-' + uuid5(NAMESPACE_URL, f'why-now/{VERSION}/{self.case_id}/{int(faults)}').hex[:16]


CASES = tuple(Case(parent, paired) for parent in range(1,7) for paired in (False,True))


def interpolate(knots, t):
    """Quintic rest-to-rest interpolation; C2 at authored knots."""
    if t <= knots[0][0]:
        return tuple(knots[0][1:])
    for left, right in zip(knots, knots[1:]):
        if t <= right[0]:
            u = (t-left[0])/(right[0]-left[0])
            weight = u*u*u*(10+u*(-15+6*u))
            return tuple(a+(b-a)*weight for a,b in zip(left[1:],right[1:]))
    return tuple(knots[-1][1:])


def world_state(scene, position, t):
    """One ball/control state shared by support targets and source export."""
    segment=next((s for s in scene.segments if s['start']<=t<s['end']),scene.segments[-1])
    if segment['actor']:
        return segment,position(segment['actor'],t)
    a,b=segment['points']
    start=position(a,segment['start']) if isinstance(a,str) else a
    end=position(b,segment['end']) if isinstance(b,str) else b
    u=(t-segment['start'])/(segment['end']-segment['start'])
    return segment,tuple(x+(y-x)*u for x,y in zip(start,end))


def _paths(scene):
    # Distinct support lanes respond to the authored ball corridor. Keepers use
    # ball-relative depth/angle. Explicit contact participants override a lane.
    formation = [(5,34),(20,15),(21,54),(33,22),(34,49),(45,15),
                 (46,53),(52,22),(57,35),(57,54),(65,34)]
    paths = {}
    for team in ('blue','amber'):
        for number,(x,y) in enumerate(formation,1):
            pid = f'{team}-{number:02}'
            knots = []
            for seconds,_,_ in scene.shape:
                # Use the actual episode ball at these support knots, not an
                # unrelated ambient oscillation or a separate approximate route.
                _,(bx,by)=world_state(scene,lambda actor,t:interpolate(scene.paths[actor],t),int(seconds*1000))
                if number == 1:
                    depth = 4 + (bx if team=='blue' else 105-bx)*.07
                    px = depth if team=='blue' else 105-depth
                    py = 34+(by-34)*.22
                else:
                    px = (x if team=='blue' else 105-x)+(bx-52.5)*.16
                    py = y+(by-34)*.12
                knots.append((int(seconds*1000),max(1,min(104,px)),max(1,min(67,py))))
            paths[pid] = knots
    paths.update(scene.paths)
    return paths


def _metadata(mid, scene, paths):
    names = ['Santi Ibarra','Leo Navarro','Nico Salas','Tomi Rios','Alex Soler',
             'Emi Duarte','Luca Mena','Ari Vela','Beni Vidal','Ciro Prado','Dani Luna']
    players = [{'id':pid,'team_id':pid.split('-')[0],
                'name':names[int(pid[-2:])-1] if pid.startswith('blue') else names[(int(pid[-2:])+3)%11],
                'number':int(pid[-2:]),'role':'keeper' if pid.endswith('-01') else 'outfield'} for pid in paths]
    return {'schema_version':'1.0.0','match_id':mid,'synthetic':True,'scope':'segment',
            'pitch':{'length_m':105,'width_m':68,'convention':'x right, y down'},
            'teams':[{'id':'blue','name':'Harbor City','color':'#3b82f6'},
                     {'id':'amber','name':'Alder Rovers','color':'#f59e0b'}],
            'players':players,'tracking_hz':10,'provenance_id':VERSION,
            'periods':[{'period':1,'timeline_offset_ms':0,
                        'attack_direction':{'blue':'right','amber':'left'}}],
            'initial_state':{'period':1,'period_elapsed_ms':0,'score':scene.initial_score,
                             'active_player_ids':list(paths),'ball_status':scene.segments[0]['status'],
                             'possession_team_id':scene.segments[0]['team']}}


@dataclass
class Dataset:
    metadata: dict
    observations: list[dict]


def build(case: Case, faults=False):
    scene = scene_for(case.parent,case.paired)
    paths = _paths(scene)
    mid = case.match_id(faults)
    meta = _metadata(mid,scene,paths)
    def pos(pid,t):
        return interpolate(paths[pid],t)
    def world(t):
        return world_state(scene,pos,t)
    def location(p):
        return {'x_m':round(p[0],4),'y_m':round(p[1],4)}
    rows = []
    for t in range(0,scene.duration+1,100):
        segment,ball = world(t)
        rows.append({'schema_version':'1.0.0','match_id':mid,'message_id':'',
                     'sequence_no':0,'timeline_ms':t,'period':1,'period_elapsed_ms':t,
                     'available_at_ms':t,'revision':1,'supersedes_message_id':None,
                     'kind':'tracking_frame','payload':{
                         'frame_id':f'f{t:06}','players':[{'player_id':pid,'team_id':pid.split('-')[0],
                            **location(pos(pid,t)),'quality':'simulated_observation'} for pid in paths],
                         'missing_player_ids':[],
                         'ball':{**location(ball),'z_m':0,'quality':'simulated_observation'},
                         'ball_status':segment['status'],'controlling_player_id':segment['actor'],
                         'possession_team_id':segment['team']}})
    source_events = [{'time':0,'kind':'period_state_changed','team':None,'actor':None,
                      'details':{'status':'started'},'key':'start','delay':0,
                      'revision':1,'supersedes':None},*deepcopy(scene.events)]
    keys = {e['key']:f'o{i:03}' for i,e in enumerate(source_events)}
    for event in source_events:
        t,details = event['time'],event['details']
        if event['kind']=='pass_started':
            details['start_position'] = location(world(t)[1])
        elif event['kind']=='pass_resolved':
            details['end_position'] = location(world(t)[1])
        elif event['kind']=='shot_started':
            details['location'] = location(world(t)[1])
        prior = event['supersedes']
        logical = prior
        while logical and next(e for e in source_events if e['key']==logical)['supersedes']:
            logical = next(e for e in source_events if e['key']==logical)['supersedes']
        rows.append({'schema_version':'1.0.0','match_id':mid,'message_id':keys[event['key']],
                     'sequence_no':0,'timeline_ms':t,'period':1,'period_elapsed_ms':t,
                     'available_at_ms':t+event['delay'],'revision':event['revision'],
                     'supersedes_message_id':keys[prior] if prior else None,
                     'kind':'event','payload':{'event_id':keys[logical or event['key']],
                         'type':event['kind'],'team_id':event['team'],'player_id':event['actor'],
                         'possession_id':None,'details':details}})
    # Controlled observation changes never modify the underlying player paths.
    if case.paired and case.parent == 1:
        for row in rows:
            if row['kind']=='tracking_frame' and 18000<=row['timeline_ms']<=20000:
                row['payload']['players'] = [p for p in row['payload']['players'] if p['player_id']!='amber-06']
                row['payload']['missing_player_ids'] = ['amber-06']
    if case.paired and case.parent == 2:
        rows = [r for r in rows if not (r['kind']=='event' and r['payload']['type'] in ('pass_started','pass_resolved') and r['payload']['details']['pass_id']=='p01')]
        for row in rows:
            t,p = row['timeline_ms'],row['payload']
            if row['kind']=='tracking_frame' and 13000<=t<17000:
                p.update(ball_status='unknown' if t<15000 else 'loose',controlling_player_id=None,possession_team_id=None)
                if t<15000:p['ball']=None
            if row['kind']=='event' and p['type']=='ball_recovered':
                p['player_id']=None
                p['details'].update(previous_team_id=None,cause='loose_ball')
            if row['kind']=='event' and p['type']=='possession_changed' and t==17000:
                p['details']['previous_team_id']=None
    if case.paired and case.parent == 5:
        rows = [r for r in rows if not (r['kind']=='tracking_frame' and 45000<=r['timeline_ms']<49000)]
        for row in rows:
            if row['kind']=='tracking_frame' and 65000<=row['timeline_ms']<68000:
                row['payload'].update(ball=None,ball_status='unknown',controlling_player_id=None,possession_team_id=None)
    if case.paired and case.parent == 6:
        for row in rows:
            if row['kind']!='event':continue
            p = row['payload']
            if p['type']=='pass_resolved' and p['details']['pass_id']=='p01':row['available_at_ms']=26000
            if p['type']=='shot_started':p.update(player_id=None);p['details']['location']=None
            if p['type']=='shot_resolved':
                p['player_id']=None;p['details']['outcome']='unknown';row['available_at_ms']=40000
    rows.sort(key=lambda r:(r['timeline_ms'],r['kind']=='event',r['revision']))
    for i,row in enumerate(rows):
        row['sequence_no']=i
        if row['kind']=='tracking_frame':row['message_id']=f'm{i:05}'
    if faults:
        rows = [r for r in rows if not (r['kind']=='tracking_frame' and r['timeline_ms'] in (10000,10100))]
        for row in rows:
            if row['kind']=='event' and row['payload']['type'] in ('pass_resolved','shot_resolved'):
                row['available_at_ms']+=800
        first = next(r for r in rows if r['kind']=='event' and r['payload']['type']!='period_state_changed')
        rows.append(deepcopy(first))
    rows.sort(key=lambda r:(r['available_at_ms'],r['sequence_no']))
    MatchMetadata.model_validate(meta)
    for row in rows:OBSERVATION.validate_python(row)
    return Dataset(meta,rows)


def encoded(dataset):
    metadata = (json.dumps(dataset.metadata,indent=2)+'\n').encode()
    raw = ''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in dataset.observations).encode()
    return metadata,gzip.compress(raw,mtime=0)


def export(root=ROOT):
    from simulator.episode_validation import validate
    catalogue,manifest = [],[]
    for number,case in enumerate(CASES,1):
        for faults in (False,True):
            dataset=build(case,faults)
            report=validate(dataset.metadata,dataset.observations)
            if not report['passed']:
                raise ValueError((case.case_id,faults,report['failures']))
            metadata,stream=encoded(dataset)
            folder=Path(root)/'data/runtime'/case.match_id(faults)
            folder.mkdir(parents=True,exist_ok=True)
            for filename,content in [('match.json',metadata),('stream.jsonl.gz',stream)]:
                target=folder/filename
                if target.exists() and target.read_bytes()!=content:
                    raise ValueError(f'immutable_export_conflict:{target}')
                target.write_bytes(content)
            catalogue.append({'match_id':case.match_id(faults),'label':f'Development passage {number:02}'+(' · delivery checks' if faults else ''),
                              'duration_ms':90000,'synthetic':True})
            manifest.append({'case_id':case.case_id,'parent':f'd{case.parent:02}',
                             'parent_structure_sha256':hashlib.sha256(json.dumps(asdict(scene_for(case.parent)),sort_keys=True).encode()).hexdigest(),
                             'split':'development','delivery_faults':faults,'match_id':case.match_id(faults),
                             'metadata_sha256':hashlib.sha256(metadata).hexdigest(),
                             'compressed_sha256':hashlib.sha256(stream).hexdigest()})
    (Path(root)/'data/runtime/synthetic-development-catalog.json').write_text(json.dumps(catalogue,indent=2)+'\n')
    record={'version':VERSION,'profile_sha256':hashlib.sha256(PROFILE.read_bytes()).hexdigest(),
            'authoring_files_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                                      for p in (Path(__file__),ROOT/'simulator/episode_scenes.py')},
            'generator_seed':None,'randomness':'none; explicit authored paths',
            'structural_parents':6,'specification_cases':12,'delivery_views':24,
            'held_out_parents':0,'independent_football_review':'pending',
            'ancestry_note':'Each a/b pair and clean/fault view shares one development parent. All share interpolation/export code, not an authored episode skeleton.',
            'cases':manifest}
    target=Path(root)/'data/provenance/episodes-v1.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(record,indent=2)+'\n')
    return record


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT)
    args=parser.parse_args()
    result=export(args.output)
    print(f"Exported {result['specification_cases']} development cases / {result['delivery_views']} views; no held-out cases or model calls.")
