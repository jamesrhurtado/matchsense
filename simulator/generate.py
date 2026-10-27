"""Original fictional, seeded segments; evaluation labels are written separately."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIRST_NAMES = ['Milo','Eli','Nico','Luca','Noah','Rafi','Leo','Theo','Ivo','Sami','Alex']
LAST_NAMES = ['Vale','Reed','Silva','Mora','Blake','Cruz','Dale','Vega','Solis','Rios','Lane']


def generate(number=1, seed=101, family='escape', reverse=False, parameters=None):
    rng = random.Random(seed)
    match_id = f'match-{number:03d}'
    teams = [{'id':'blue','name':'Club del Faro','color':'#3b82f6'}, {'id':'amber','name':'Puerto Lumbre FC','color':'#f59e0b'}]
    players = [{'id':f'{team}-{i:02d}', 'team_id':team, 'name':f'{FIRST_NAMES[i-1]} {LAST_NAMES[(i-1+offset)%11]}', 'number':i, 'role':'keeper' if i==1 else 'outfield'} for team,offset in [('blue',0),('amber',3)] for i in range(1,12)]
    metadata = {'schema_version':'1.0.0','match_id':match_id,'synthetic':True,'scope':'segment','pitch':{'length_m':105,'width_m':68,'convention':'x right, y down'},'teams':teams,'players':players,'periods':[{'period':1,'timeline_offset_ms':0,'attack_direction':{'blue':'left' if reverse else 'right','amber':'right' if reverse else 'left'}}],'initial_state':{'period':1,'period_elapsed_ms':0,'score':{'blue':0,'amber':0},'active_player_ids':[p['id'] for p in players],'ball_status':'controlled','possession_team_id':'blue'},'tracking_hz':10,'provenance_id':f'provenance-{number:03d}'}
    messages = []
    def point(x,y): return {'x_m':round(105-x if reverse else x,3),'y_m':round(y,3)}
    def add(kind,t,payload):
        n=len(messages)+1
        messages.append({'schema_version':'1.0.0','match_id':match_id,'message_id':f'm-{n:05d}','sequence_no':n,'kind':kind,'timeline_ms':t,'period':1,'period_elapsed_ms':t,'available_at_ms':t,'revision':1,'supersedes_message_id':None,'payload':payload})
    phase = rng.uniform(0,6)
    parameters=parameters or {}
    release_x=parameters.get('release_x',35)
    center_y=parameters.get('center_y',32)
    distance=parameters.get('pass_distance_m',19)
    end_x=release_x+distance+rng.uniform(-1.5,1.5) if family!='failed' else release_x+8
    start,resolved = 18000,19200
    for t in range(0,60001,100):
        positions={}
        drift=t/60000*8
        for i in range(1,12):
            positions[f'blue-{i:02d}']=(8+(i%5)*8+drift,7+((i*13)%54)+.3*math.sin(t/2000+i+phase))
            positions[f'amber-{i:02d}']=(92-(i%5)*8-drift*.6,7+((i*11)%54)+.3*math.sin(t/2000+i+phase))
        factor=max(0,min(1,(t-8000)/7000,(30000-t)/11000)) if family!='ordinary' else 0
        for j,(x,y) in enumerate([(release_x+2,center_y-1),(release_x+3,center_y+3),(release_x+5,center_y-4)]):
            base=release_x+23+j*5
            positions[f'amber-{j+6:02d}']=(base+(x-base)*factor,y)
        carry=max(0,min(7,(t-resolved)/4000*7))
        positions['blue-08']=(release_x,center_y)
        positions['blue-10']=(end_x+carry,center_y+2)
        if family=='failed': positions['amber-07']=(end_x,center_y+2)
        if t<start:
            ball=(release_x,center_y); controller='blue-08'; status='controlled'; possession='blue'
        elif t<resolved:
            ratio=(t-start)/(resolved-start)
            ball=(release_x+(end_x-release_x)*ratio,center_y+2*ratio); controller=None; status='in_flight'; possession='blue'
        else:
            ball=(end_x+carry,center_y+2) if family!='failed' else (end_x,center_y+2)
            controller='blue-10' if family!='failed' else 'amber-07'; status='controlled'; possession='blue' if family!='failed' else 'amber'
        add('tracking_frame',t,{'frame_id':f'f-{t:05d}','players':[{'player_id':p['id'],'team_id':p['team_id'],**point(*positions[p['id']]),'quality':'simulated_observation'} for p in players],'missing_player_ids':[],'ball':{**point(*ball),'z_m':0,'quality':'simulated_observation'},'ball_status':status,'controlling_player_id':controller,'possession_team_id':possession})
        if t==start:
            add('event',t,{'event_id':'e-pass-start','type':'pass_started','team_id':'blue','player_id':'blue-08','possession_id':'pos-1','details':{'pass_id':'pass-1','start_position':point(release_x,center_y),'intended_receiver_id':'blue-10'}})
        if t==resolved:
            ok=family!='failed'
            add('event',t,{'event_id':'e-pass-end','type':'pass_resolved','team_id':'blue','player_id':controller,'possession_id':'pos-1','details':{'pass_id':'pass-1','outcome':'received' if ok else 'intercepted','end_position':point(end_x,center_y+2),'controlling_team_id':possession,'controlling_player_id':controller}})
            if not ok:
                add('event',t,{'event_id':'e-turnover','type':'possession_changed','team_id':'amber','player_id':controller,'possession_id':'pos-2','details':{'previous_team_id':'blue','new_team_id':'amber','controlling_player_id':controller,'reason':'interception'}})
    return metadata,messages


def write_fixture(number,seed,family,reverse=False):
    meta,messages=generate(number,seed,family,reverse)
    out=ROOT/'data/runtime'/meta['match_id']; out.mkdir(parents=True,exist_ok=True)
    (out/'match.json').write_text(json.dumps(meta,indent=2)+'\n')
    raw=''.join(json.dumps(m,separators=(',',':'))+'\n' for m in messages)
    (out/'stream.jsonl').write_text(raw)
    (ROOT/'data/evaluation-only'/f'{meta["match_id"]}.json').write_text(json.dumps({'match_id':meta['match_id'],'family':family,'expected_candidate':family=='escape'},indent=2)+'\n')
    return {'match_id':meta['match_id'],'sha256':hashlib.sha256(raw.encode()).hexdigest(),'seed':seed,'generator_version':'1.0.0','source':'original fictional simulation'}

if __name__=='__main__':
    records=[write_fixture(1,101,'escape'),write_fixture(2,202,'ordinary'),write_fixture(3,303,'failed')]
    (ROOT/'data/provenance/fixtures.json').write_text(json.dumps(records,indent=2)+'\n')
    print('Generated three 60-second synthetic fixtures.')
