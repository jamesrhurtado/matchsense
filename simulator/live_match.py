"""Additive live-feed stress scenes, derived from the authored flagship.

These are transformed/delivery-fault variants of one trajectory backbone, not
independent football matches or expert tactical ground truth. References live in
the offline evaluation directory and are never loaded here or at runtime.
"""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
from simulator.flagship import build as flagship
from simulator.suite import serialize
from simulator.validate import validate_feed
ROOT=Path(__file__).resolve().parents[1]
IDS=('match-0c0a000000000007','match-0c0a000000000008')

def build(faults=False):
    meta,rows=flagship(faults);meta=deepcopy(meta);rows=deepcopy(rows)
    mid=IDS[int(faults)];meta.update(match_id=mid,provenance_id='live-match-v1')
    def reflect(item):
        if isinstance(item,dict):
            if 'x_m' in item and not faults:item['x_m']=round(105-item['x_m'],4)
            if 'y_m' in item:item['y_m']=round(68-item['y_m'],4)
            for value in item.values():reflect(value)
        elif isinstance(item,list):
            for value in item:reflect(value)
    if not faults:
        for period in meta['periods']:
            period['attack_direction']={team:'left' if value=='right' else 'right' for team,value in period['attack_direction'].items()}
    for row in rows:
        row['match_id']=mid;reflect(row['payload'])
        if faults and row['kind']=='event' and row['payload']['type']=='shot_resolved' and row['payload']['details']['shot_id']=='attempt-1':row['available_at_ms']+=2000
    if faults:
        rows=[r for r in rows if not(r['kind']=='tracking_frame' and r['timeline_ms'] in {20000,20100})]
        rows.append(deepcopy(next(r for r in rows if r['kind']=='event' and r['payload']['type']=='shot_started')))
    rows.sort(key=lambda r:(r['available_at_ms'],r['sequence_no']))
    validate_feed(meta,rows)
    return meta,rows

def main():
    path=ROOT/'data/runtime/match-coverage-catalog.json';catalog=json.loads(path.read_text());cases=[]
    for faults in (False,True):
        meta,rows=build(faults);mid=meta['match_id'];folder=ROOT/'data/runtime'/mid;folder.mkdir(exist_ok=True)
        raw=gzip.compress(serialize(rows).encode(),mtime=0)
        (folder/'match.json').write_text(json.dumps(meta,indent=2)+'\n');(folder/'stream.jsonl.gz').write_bytes(raw)
        catalog=[c for c in catalog if c['match_id']!=mid]+[{'match_id':mid,'label':'Live simulation · '+('delayed shot, duplicate, missing frames and score correction' if faults else 'mirrored pressure sequence'),'duration_ms':240000,'synthetic':True}]
        cases.append({'match_id':mid,'sha256':hashlib.sha256(raw).hexdigest(),'observations':len(rows)})
    path.write_text(json.dumps(catalog,indent=2)+'\n')
    (ROOT/'data/provenance/live-match-v1.json').write_text(json.dumps({'generator':'simulator.live_match','scope':__doc__,'cases':cases},indent=2)+'\n')

if __name__=='__main__':main()
