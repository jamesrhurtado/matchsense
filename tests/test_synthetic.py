"""Independent data and feed checks; no detector-derived scenario labels."""
from copy import deepcopy
import hashlib
import json

import pytest
from engine.contracts import MatchMetadata, OBSERVATION
from simulator.scenarios import FAMILIES, PARENTS, cases, get_case
from simulator.suite import export_case, generate_case, serialize
from simulator.validate import validate, validate_feed


@pytest.mark.parametrize('case',cases('development')[:len(FAMILIES)],ids=lambda c:c.family)
def test_every_family_has_coherent_clean_and_observed_trajectories(case):
    ds=generate_case(case)
    assert validate(ds.metadata,ds.clean)['active_players']==22
    assert validate_feed(ds.metadata,ds.observations)['duration_ms']==ds.reference['duration_ms']


@pytest.mark.parametrize('case',[c for c in cases() if c.family=='escape'],ids=lambda c:c.id)
def test_parent_variations_cover_direction_team_roster_and_timing(case):
    ds=generate_case(case)
    validate(ds.metadata,ds.clean)
    assert ds.reference['plays'][0]['release_ms']==case.parent.release_ms
    assert ds.reference['plays'][0]['passer_id'].startswith(case.parent.team)


def test_same_case_is_byte_reproducible_and_parent_changes_actual_data():
    a=generate_case(get_case('p01-01'))
    b=generate_case(get_case('p01-01'))
    c=generate_case(get_case('p02-01'))
    assert a==b
    assert serialize(a.observations)==serialize(b.observations)
    assert a.metadata['players']!=c.metadata['players']
    assert a.observations[0]['payload']['players']!=c.observations[0]['payload']['players']


def test_splits_are_disjoint_at_whole_parent_level():
    assert len({p.id for p in PARENTS})==len(PARENTS)
    assert len({(p.x,p.y,p.distance,p.reverse,p.team,p.release_ms,p.seed) for p in PARENTS})==len(PARENTS)
    assert len({c.match_id for c in cases()})==len(cases())
    for parent in PARENTS:
        assert {c.parent.split for c in cases() if c.parent.id==parent.id}=={parent.split}
        assert len([c for c in cases() if c.parent.id==parent.id])==len(FAMILIES)


def test_runtime_export_excludes_truth_faults_and_revealing_configuration(tmp_path):
    ds=generate_case(get_case('p01-22'))
    record=export_case(ds,tmp_path)
    folder=tmp_path/'runtime'/ds.metadata['match_id']
    meta=json.loads((folder/'match.json').read_text())
    rows=[json.loads(x) for x in (folder/'stream.jsonl').read_text().splitlines()]
    MatchMetadata.model_validate(meta)
    for row in rows: OBSERVATION.validate_python(row)
    raw=(folder/'match.json').read_text()+(folder/'stream.jsonl').read_text()
    for secret in ('expected_pass_ids','case_id','family','fault_plan','reference_basis','parent','seed','correction_withdraws'):
        assert f'"{secret}"' not in raw
    assert ds.reference['case_id'] not in meta['match_id']
    assert hashlib.sha256((folder/'stream.jsonl').read_bytes()).hexdigest()==record['observations_sha256']
    assert hashlib.sha256((folder/'match.json').read_bytes()).hexdigest()==record['metadata_sha256']
    assert len(list(folder.iterdir()))==2
    assert (tmp_path/'evaluation-only'/f'{meta["match_id"]}.clean.jsonl').exists()


def test_faults_do_not_mutate_clean_reference():
    ds=generate_case(next(c for c in cases() if c.family=='correction_restores'))
    at=ds.reference['plays'][0]['confirmation_ms']
    clean=next(m for m in ds.clean if m['kind']=='tracking_frame' and m['timeline_ms']==at)
    observed=next(m for m in ds.observations if m['message_id']==clean['message_id'])
    assert clean['payload']['ball'] is not None
    assert observed['payload']['ball'] is None
    assert all(m['revision']==1 for m in ds.clean)


def test_delivery_validation_allows_exact_duplicates_but_rejects_changed_content():
    ds=generate_case(next(c for c in cases() if c.family=='duplicates'))
    assert validate_feed(ds.metadata,ds.observations)['exact_retransmissions']>0
    corrupt=deepcopy(ds.observations)
    corrupt[1]['payload']['ball']['z_m']=1
    with pytest.raises(AssertionError,match='conflicting_retransmission'):
        validate_feed(ds.metadata,corrupt)


@pytest.mark.parametrize('mutation,error',[
    ('orphan','orphan_correction'),('logical','correction_logical_id_mismatch'),
    ('clock','correction_clock_mismatch'),('revision','correction_revision_gap'),
])
def test_delivery_validator_rejects_broken_correction_lineage(mutation,error):
    ds=generate_case(next(c for c in cases() if c.family=='correction_withdraws'))
    correction=next(m for m in ds.observations if m['revision']==2)
    if mutation=='orphan': correction['supersedes_message_id']='nonexistent'
    if mutation=='logical': correction['payload']['frame_id']='another-frame'
    if mutation=='clock': correction['timeline_ms']+=100; correction['period_elapsed_ms']+=100
    if mutation=='revision': correction['revision']=3
    with pytest.raises(AssertionError,match=error): validate_feed(ds.metadata,ds.observations)


def test_validator_rejects_teleporting_player_and_contradictory_event():
    ds=generate_case(get_case('p01-01'))
    bad=deepcopy(ds.clean)
    bad[1]['payload']['players'][0]['x_m']+=10
    with pytest.raises(AssertionError,match='player_speed_over_10_mps'): validate(ds.metadata,bad)
    bad=deepcopy(ds.clean)
    end=next(m for m in bad if m['kind']=='event' and m['payload']['type']=='pass_resolved')
    end['payload']['details']['controlling_player_id']='amber-01'
    with pytest.raises(AssertionError,match='resolution_controller_mismatch'): validate(ds.metadata,bad)


def test_authored_boundary_and_receiver_expectations_are_not_detector_outputs():
    boundary=generate_case(next(c for c in cases() if c.family=='rounding_boundary'))
    assert boundary.reference['plays'][0]['continuation_distance_m']==4.96
    assert all(not check['expected_pass_ids'] for check in boundary.reference['checks'])
    receiver=generate_case(next(c for c in cases() if c.family=='different_receiver'))
    start=next(m for m in receiver.clean if m['kind']=='event' and m['payload']['type']=='pass_started')
    assert start['payload']['details']['intended_receiver_id']!=receiver.reference['plays'][0]['actual_receiver_id']


def test_jitter_reference_uses_a_known_confirmation_arrival():
    ds=generate_case(next(c for c in cases() if c.family=='reordered_delivery'))
    at=ds.reference['plays'][0]['confirmation_ms']
    endpoint=next(m for m in ds.observations if m['kind']=='tracking_frame' and m['timeline_ms']==at)
    assert endpoint['available_at_ms']==at+700
    assert all(m['available_at_ms']<at+700 for m in ds.observations if m['timeline_ms']<at)
    assert any(a['sequence_no']>b['sequence_no'] for a,b in zip(ds.observations,ds.observations[1:]))
