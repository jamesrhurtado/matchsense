"""Presentation motion gates, separate from the original numerical references."""
import gzip
import hashlib
import json
import math
from pathlib import Path
import pytest
from simulator.matchday_demo import build, DEMO_IDS
from simulator.suite import serialize
from simulator.validate import validate_feed
from engine.core import pass_metrics
from engine.event_metrics import event_metrics
from engine.match_state import match_state

ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('correction',[False,True])
def test_demo_source_physics_and_reproducible_export(correction):
    meta,rows=build(correction)
    result=validate_feed(meta,rows)
    assert result['frames']==2401 and result['active_players']==22
    assert gzip.compress(serialize(rows).encode(),mtime=0)==(ROOT/'data/runtime'/meta['match_id']/'stream.jsonl.gz').read_bytes()


def test_legacy_mixed_exports_keep_original_hashes():
    manifest=json.loads((ROOT/'data/provenance/match-coverage.json').read_text())
    for case in manifest['cases']:
        assert hashlib.sha256((ROOT/'data/runtime'/case['match_id']/'stream.jsonl.gz').read_bytes()).hexdigest()==case['sha256']


def test_visible_motion_throughout_and_keeper_lanes():
    meta,rows=build();frames={r['timeline_ms']:r['payload'] for r in rows if r['kind']=='tracking_frame'}
    for t in range(0,230001,10000):
        a,b=frames[t]['players'],frames[t+10000]['players']
        # Independent presentation criterion: a majority move >2m in each 10s span.
        assert sum(math.dist((p['x_m'],p['y_m']),(q['x_m'],q['y_m']))>2 for p,q in zip(a,b))>=12
    for frame in frames.values():
        for p in frame['players']:
            if p['player_id']=='blue-01':assert 2<=p['x_m']<=10 and 22<=p['y_m']<=46
            if p['player_id']=='amber-01':assert 95<=p['x_m']<=103 and 22<=p['y_m']<=46


def test_authored_shots_and_source_score_availability():
    meta,rows=build();frames={r['timeline_ms']:r['payload'] for r in rows if r['kind']=='tracking_frame'}
    for t,x,y in [(45000,82,30),(100000,88,34),(101000,105,34)]:
        assert (frames[t]['ball']['x_m'],frames[t]['ball']['y_m'])==(x,y)
    assert frames[185000]['ball'] is None
    assert match_state(meta,rows,103999)['score']=={'blue':0,'amber':0}
    assert match_state(meta,rows,104000)['score']=={'blue':1,'amber':0}
    cm,cr=build(True)
    assert match_state(cm,cr,135000)['score']=={'blue':0,'amber':0}


def test_every_required_family_and_pass_geometry_survive_new_motion():
    meta,rows=build()
    assert len([m for m in pass_metrics(rows,240000,meta) if m['eligible']])==4
    for t,family in [(33000,'recovery'),(47000,'shot'),(60000,'possession'),(105000,'goal')]:
        assert any(m['family']==family and m['eligible'] for m in event_metrics(meta,rows,t))


def test_regenerating_legacy_discovery_keeps_new_catalogue_entries(tmp_path,monkeypatch):
    from simulator import match_coverage
    runtime=tmp_path/'data/runtime';runtime.mkdir(parents=True)
    (tmp_path/'data/provenance').mkdir(parents=True)
    path=runtime/'match-coverage-catalog.json'
    existing=json.loads((ROOT/'data/runtime/match-coverage-catalog.json').read_text())
    path.write_text(json.dumps(existing))
    monkeypatch.setattr(match_coverage,'ROOT',tmp_path)
    match_coverage.main()
    assert {r['match_id'] for r in json.loads(path.read_text())}=={r['match_id'] for r in existing}
