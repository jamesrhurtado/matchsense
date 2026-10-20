"""Seeded fictional 11-a-side segments. Evaluation labels never enter runtime data."""
import argparse, hashlib, json, math, random
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def make_fixture(number: int, seed: int, family: str):
    rng = random.Random(seed)
    match_id = f"match-{number:03d}"
    teams = [{"id":"blue","name":"Harbor City","color":"#3b8cfa"},{"id":"amber","name":"Alder Rovers","color":"#f4b84b"}]
    players = [{"id":f"{team}-{i:02d}","team_id":team,"name":f"{name} {i}","number":i,"role":"keeper" if i==1 else "outfield"} for team,name in [("blue","Harbor"),("amber","Alder")] for i in range(1,12)]
    initial = {"period":1,"period_elapsed_ms":0,"score":{"blue":0,"amber":0},"active_player_ids":[p["id"] for p in players],"ball_status":"controlled","possession_team_id":"blue"}
    meta = {"schema_version":"1.0.0","match_id":match_id,"synthetic":True,"scope":"segment","pitch":{"length_m":105,"width_m":68,"convention":"x right, y down"},"teams":teams,"players":players,"periods":[{"period":1,"timeline_offset_ms":0,"attack_direction":{"blue":"right","amber":"left"}}],"initial_state":initial,"tracking_hz":10,"provenance_id":f"provenance-{number:03d}"}
    messages=[]
    def add(kind,t,payload,delay=0):
        n=len(messages)+1
        messages.append({"schema_version":"1.0.0","match_id":match_id,"message_id":f"m-{n:05d}","sequence_no":n,"kind":kind,"timeline_ms":t,"period":1,"period_elapsed_ms":t,"available_at_ms":t+delay,"revision":1,"supersedes_message_id":None,"payload":payload})
    start=18000; resolved=19200
    start_x=35; end_x=54 if family!='failed' else 43
    for t in range(0,45001,100):
        # All 22 players are generated from one smooth state transition.
        drift=t/45000*8
        pos={}
        for i in range(1,12):
            x=5+(i%5)*8+drift+(0.15*math.sin(t/1700+i))
            y=7+((i*13)%54)+0.4*math.sin(t/2100+i)
            pos[f"blue-{i:02d}"]=(x,y)
            ax=90-(i%5)*8-drift*0.6
            ay=7+((i*11)%54)+0.4*math.sin(t/2000+i)
            pos[f"amber-{i:02d}"]=(ax,ay)
        # The press is visible before the pass only in the hero and failed cases.
        press=family!='ordinary'
        for j,(x,y) in enumerate([(37,31),(38,35),(40,28)]):
            pos[f"amber-{j+6:02d}"]=(x if press and 15000<=t<=19000 else 55+j*4, y)
        pos['blue-08']=(start_x-2,32)
        pos['blue-10']=(end_x if t>=resolved else end_x-1,34)
        if t<start: ball=(start_x,32); controller='blue-08'; status='controlled'
        elif t<=resolved:
            frac=(t-start)/(resolved-start)
            ball=(start_x+(end_x-start_x)*frac,32+2*frac); controller=None; status='in_flight'
        else:
            ball=(end_x+min((t-resolved)/4000,1)*7,34); controller='blue-10' if family!='failed' else 'amber-07'; status='controlled'
        if family=='failed' and t>resolved: ball=(end_x,34)
        frame={"frame_id":f"f-{t:05d}","players":[{"player_id":p["id"],"team_id":p["team_id"],"x_m":round(pos[p["id"]][0],2),"y_m":round(pos[p["id"]][1],2),"quality":"simulated_observation"} for p in players],"missing_player_ids":[],"ball":{"x_m":round(ball[0],2),"y_m":round(ball[1],2),"z_m":0,"quality":"simulated_observation"},"ball_status":status,"controlling_player_id":controller,"possession_team_id":"amber" if family=='failed' and t>resolved else "blue"}
        add('tracking_frame',t,frame)
        if t==start:
            add('event',t,{"event_id":"e-pass-start","type":"pass_started","team_id":"blue","player_id":"blue-08","possession_id":"pos-1","details":{"pass_id":"pass-1","start_position":{"x_m":start_x,"y_m":32},"intended_receiver_id":"blue-10"}})
        if t==resolved:
            ok=family!='failed'
            add('event',t,{"event_id":"e-pass-end","type":"pass_resolved","team_id":"blue","player_id":"blue-10" if ok else "amber-07","possession_id":"pos-1","details":{"pass_id":"pass-1","outcome":"received" if ok else "intercepted","end_position":{"x_m":end_x,"y_m":34},"controlling_team_id":"blue" if ok else "amber","controlling_player_id":"blue-10" if ok else "amber-07"}})
            if not ok: add('event',t,{"event_id":"e-turnover","type":"possession_changed","team_id":"amber","player_id":"amber-07","possession_id":"pos-2","details":{"previous_team_id":"blue","new_team_id":"amber","controlling_player_id":"amber-07","reason":"interception"}})
    messages.sort(key=lambda m:(m['available_at_ms'],m['sequence_no']))
    out=ROOT/'data'/'runtime'/match_id; out.mkdir(parents=True,exist_ok=True)
    (out/'match.json').write_text(json.dumps(meta,indent=2)+'\n')
    raw=''.join(json.dumps(m,separators=(',',':'))+'\n' for m in messages)
    (out/'stream.jsonl').write_text(raw)
    (ROOT/'data'/'evaluation-only'/f'{match_id}.json').write_text(json.dumps({"match_id":match_id,"family":family,"expected_candidate":family=='escape'},indent=2)+'\n')
    return {"match_id":match_id,"sha256":hashlib.sha256(raw.encode()).hexdigest(),"seed":seed,"generator":"simulator/generate.py","source":"original fictional simulation"}

if __name__=='__main__':
    fixtures=[make_fixture(1,101,'escape'),make_fixture(2,202,'ordinary'),make_fixture(3,303,'failed')]
    (ROOT/'data'/'provenance'/'fixtures.json').write_text(json.dumps(fixtures,indent=2)+'\n')
    print(json.dumps(fixtures,indent=2))
