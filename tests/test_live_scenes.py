"""New live variants: independent feed/geometry checks, not tactical validation."""
import gzip
from pathlib import Path
import pytest
from simulator.live_match import build
from simulator.suite import serialize
from simulator.validate import validate_feed
from engine.core import available
from engine.match_state import match_state

ROOT=Path(__file__).resolve().parents[1]
@pytest.mark.parametrize('faults',[False,True])
def test_new_live_exports_are_reproducible_and_physically_valid(faults):
    meta,rows=build(faults)
    result=validate_feed(meta,rows)
    assert result['active_players']==22
    exported=(ROOT/'data/runtime'/meta['match_id']/'stream.jsonl.gz').read_bytes()
    assert gzip.compress(serialize(rows).encode(),mtime=0)==exported
    starts={r['payload']['details']['pass_id']:r for r in rows if r['kind']=='event' and r['payload']['type']=='pass_started'}
    ends=[r for r in rows if r['kind']=='event' and r['payload']['type']=='pass_resolved']
    sign=1 if meta['periods'][0]['attack_direction']['blue']=='right' else -1
    assert [round(sign*(r['payload']['details']['end_position']['x_m']-starts[r['payload']['details']['pass_id']]['payload']['details']['start_position']['x_m'])) for r in ends]==[18,25,22,30]
    assert match_state(meta,rows,103999)['score']['blue']==0
    assert match_state(meta,rows,104000)['score']['blue']==1
    assert match_state(meta,rows,136000)['score']['blue']==(0 if faults else 1)

def test_delayed_shot_and_duplicates_are_not_visible_before_delivery():
    meta,rows=build(True)
    assert not any(r['kind']=='event' and r['payload']['type']=='shot_resolved' for r in available(rows,47999))
    assert len([r for r in available(rows,48000) if r['kind']=='event' and r['payload']['type']=='shot_started'])==1
    assert not any(r['kind']=='tracking_frame' and r['timeline_ms'] in {20000,20100} for r in rows)
