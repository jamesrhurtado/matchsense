from copy import deepcopy
import hashlib
import json
from pathlib import Path
import pytest
from engine.core import available,load_match,metric
from engine.workflow import EvidenceTools,ToolError,run_workflow
from simulator.generate import generate
from simulator.validate import validate

@pytest.mark.parametrize('match_id',['match-001','match-002','match-003'])
def test_fixtures_have_consistent_physics_and_contracts(match_id):
    meta,messages=load_match(match_id)
    assert validate(meta,messages)['active_players']==22

@pytest.mark.parametrize('family,expected',[('escape',True),('ordinary',False),('failed',False)])
def test_detector_on_distinct_scenarios(family,expected):
    meta,messages=generate(11,907,family)
    assert metric(messages,23000,meta)['eligible'] is expected

def test_metric_matches_hand_checked_geometry():
    meta,messages=generate(12,101,'escape')
    m=metric(messages,23000,meta)
    # At release x=35, three opponent x values are 37, 38 and 40; the endpoint is beyond 52.
    assert m['bypassed_count']==3
    assert m['pressure_opponents_max']==2  # distances sqrt(5), sqrt(18), sqrt(41), radius 6m
    assert m['progression_m']==5.2 or m['progression_m']==5.3
    assert m['retained'] is True

@pytest.mark.parametrize('cutoff',[0,17999,18000,19199,19200,22000,22199])
def test_retention_not_available_before_window(cutoff):
    meta,messages=generate()
    m=metric(messages,cutoff,meta)
    assert m is None or not m['eligible']

def test_delayed_outcome_cannot_leak_or_revive_an_expired_story():
    meta,messages=generate()
    messages=deepcopy(messages)
    end=next(m for m in messages if m['kind']=='event' and m['payload']['type']=='pass_resolved')
    end['available_at_ms']=58000
    assert metric(messages,25000,meta) is None
    p=run_workflow(EvidenceTools(meta,messages,59000))
    # Eligibility may be investigated late; original observation confirmation controls the display deadline.
    assert p is not None
    assert p['expires_at_ms']==52200
    assert p['expires_at_ms']<59000


def test_reversed_attack_direction_keeps_metrics():
    meta,msgs=generate(9,101,'escape',False);rev,rmsgs=generate(10,101,'escape',True)
    a=metric(msgs,23000,meta);b=metric(rmsgs,23000,rev)
    assert (a['bypassed_count'],a['progression_m'],a['eligible'])==(b['bypassed_count'],b['progression_m'],b['eligible'])

def test_missing_opponents_cause_abstention():
    meta,messages=generate();messages=deepcopy(messages)
    for m in messages:
        if m['kind']=='tracking_frame' and 16000<=m['timeline_ms']<=18000:
            p=m['payload'];p['players']=[p for p in p['players'] if p['player_id']!='amber-06'];p['missing_player_ids']=['amber-06']
    assert metric(messages,23000,meta) is None


def test_brief_possession_loss_cannot_claim_continuous_retention():
    meta,messages=generate();messages=deepcopy(messages)
    next(m for m in messages if m['kind']=='tracking_frame' and m['timeline_ms']==20500)['payload']['possession_team_id']='amber'
    assert metric(messages,23000,meta)['eligible'] is False


def test_gap_in_confirmation_window_causes_abstention():
    meta,messages=generate();messages=[m for m in messages if not( m['kind']=='tracking_frame' and 20000<=m['timeline_ms']<=20500)]
    assert metric(messages,23000,meta)['retained'] is None


def test_retransmission_deduplicated():
    meta,messages=generate();a=metric(messages,23000,meta);b=metric(messages+messages[:250],23000,meta)
    assert a==b


def test_delivered_correction_invalidates_evidence_hash():
    meta,messages=generate();old=next(m for m in messages if m['kind']=='tracking_frame' and m['timeline_ms']==17000)
    correction=deepcopy(old);correction.update(message_id='correction-1',revision=2,supersedes_message_id=old['message_id'],available_at_ms=26000,sequence_no=10000)
    correction['payload']['players'][0]['x_m']+=.1
    m1=metric(messages+[correction],25000,meta);m2=metric(messages+[correction],27000,meta)
    assert m1['evidence_revision']!=m2['evidence_revision']
    assert old['message_id'] not in m2['source_message_ids']
    assert 'correction-1' in m2['source_message_ids']


def test_tools_reject_future_and_large_windows():
    meta,messages=generate();tools=EvidenceTools(meta,messages,18000)
    with pytest.raises(ToolError):tools.get_sequence(17000,19000)
    with pytest.raises(ToolError):tools.get_sequence(0,18000)
    with pytest.raises(ToolError):tools.get_positions(17000,18000,['cross-session-player'])
    assert all(m['available_at_ms']<=18000 for m in tools.get_sequence(16000,18000))


def test_frozen_packages_do_not_change_expiry_as_clock_moves():
    meta,messages=generate();p1=run_workflow(EvidenceTools(meta,messages,23000));p2=run_workflow(EvidenceTools(meta,messages,50000))
    assert p1['expires_at_ms']==p2['expires_at_ms']==52200
    assert p1['evidence_revision']==p2['evidence_revision']


def test_reviewer_changes_unsupported_edit_in_one_cycle():
    meta,messages=generate();p=run_workflow(EvidenceTools(meta,messages,25000),proposed_text='Harbor City now controls the match.')
    assert p['review']['status']=='revised'
    assert p['review']['cycles']==1
    assert 'controls the match' not in p['review']['revised_text']
    assert any(t['status']=='needs_evidence' for t in p['trace'])
    assert len(p['variants'])==100


def test_seeds_are_reproducible_and_change_realized_positions():
    a=generate(1,101);b=generate(1,101);c=generate(1,102)
    assert a==b and a[1]!=c[1]


def test_provenance_hashes_match_committed_runtime():
    root=Path(__file__).resolve().parents[1]
    for record in json.loads((root/'data/provenance/fixtures.json').read_text()):
        raw=(root/'data/runtime'/record['match_id']/'stream.jsonl').read_bytes()
        assert hashlib.sha256(raw).hexdigest()==record['sha256']


def test_variant_numeric_mutation_is_rejected():
    from engine.workflow import render_variants,validate_variants
    meta,msgs=generate();m=metric(msgs,23000,meta);variants=render_variants(m,meta)
    variants[0]['text']=variants[0]['text'].replace('3 opponents','7 opponents')
    with pytest.raises(ValueError,match='variant_numeric_mismatch'):validate_variants(variants,m,meta)


def test_output_schema_rejects_claims_from_another_revision():
    from engine.contracts import PublicationPackage
    from pydantic import ValidationError
    meta,msgs=generate();package=run_workflow(EvidenceTools(meta,msgs,23000))
    package['claims'][0]['evidence_revision']='different-revision'
    with pytest.raises(ValidationError):PublicationPackage.model_validate(package)


def test_contract_rejects_future_fields_and_early_availability():
    from engine.contracts import OBSERVATION
    from pydantic import ValidationError
    _,msgs=generate();start=deepcopy(next(m for m in msgs if m['kind']=='event' and m['payload']['type']=='pass_started'))
    start['payload']['details']['outcome']='received'
    with pytest.raises(ValidationError):OBSERVATION.validate_python(start)
    del start['payload']['details']['outcome'];start['available_at_ms']=start['timeline_ms']-1
    with pytest.raises(ValidationError):OBSERVATION.validate_python(start)


def test_content_hash_survives_cosmos_integral_float_serialization():
    import json
    from engine.core import digest,load_match
    from engine.workflow import EvidenceTools,run_workflow
    meta,rows=load_match('match-001')
    def cosmos_roundtrip(value):
        return json.loads(json.dumps(value),parse_float=lambda text:int(float(text)) if float(text).is_integer() else float(text))
    assert digest(rows)==digest(cosmos_roundtrip(rows))
    package=run_workflow(EvidenceTools(meta,rows,25000))
    stored=cosmos_roundtrip(package)
    stored_hash=stored.pop('package_hash')
    assert digest(stored)==stored_hash
    assert digest({'x':1})==digest({'x':1.0})
    assert digest({'x':1})!=digest({'x':'1'})
    assert digest({'x':1.1})!=digest({'x':1})
