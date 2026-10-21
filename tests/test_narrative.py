from copy import deepcopy

import pytest
from pydantic import ValidationError

from engine.contracts import PublicationPackage
from engine.narrative import build_structured_package, check_plan, default_plan, spatial_context
from engine.workflow import EvidenceTools, run_workflow
from simulator.generate import generate


def package(reverse=False):
    meta, rows = generate(reverse=reverse)
    return build_structured_package(EvidenceTools(meta, rows, 25000)), meta, rows


def test_v2_and_legacy_packages_are_readable_with_different_schemas():
    p, meta, rows = package()
    assert PublicationPackage.model_validate(p).schema_version == '2.0.0'
    assert len(p['variants']) == 100
    assert PublicationPackage.model_validate(run_workflow(EvidenceTools(meta, rows, 25000))).schema_version == '1.0.0'
    assert p['metrics']['forward_pass_m'] > p['metrics']['progression_m']


@pytest.mark.parametrize('bad', [
    'The pass split the defensive line and left the defence exposed.',
    'The pass failed and possession was lost.',
])
def test_valid_claim_id_cannot_bind_arbitrary_false_prose(bad):
    p, _, _ = package()
    p['variants'][0]['clauses'][0]['text'] = bad
    p['variants'][0]['text'] = ' '.join(c['text'] for c in p['variants'][0]['clauses'])
    with pytest.raises(ValidationError, match='unbound_audience_text'):
        PublicationPackage.model_validate(p)


@pytest.mark.parametrize('field,bad', [('subject_id','blue-10'),('unit','s'),('value',999),('predicate','team_retained')])
def test_actor_units_predicate_and_values_are_bound(field,bad):
    p, _, _ = package()
    next(c for c in p['claims'] if c['id']=='c-forward')[field] = bad
    with pytest.raises(ValidationError):
        PublicationPackage.model_validate(p)


def test_exact_clause_references_replace_all_claims_on_every_variant():
    p, _, _ = package()
    simple = p['variants'][0]
    assert simple['claim_ids'] == ['c-bypass','c-retain']
    assert 'c-progress' not in simple['claim_ids']
    focused = next(v for v in p['variants'] if v['focus']==p['metrics']['receiver_id'] and v['language']=='es' and v['detail']=='simple')
    assert focused['claim_ids'] == ['c-bypass','c-retain','c-reception']
    assert 'recibió el pase.' in focused['text']


def test_unknown_claims_and_missing_outcome_are_rejected_before_composition():
    p, _, _ = package()
    bad = default_plan();bad['simple_claim_ids']=['c-goal','c-retain']
    with pytest.raises(ValueError,match='unsupported_narrative_claim'):check_plan(bad,p['claims'])
    bad = default_plan();bad['simple_claim_ids']=['c-forward','c-zone']
    with pytest.raises(ValueError,match='missing_team_outcome'):check_plan(bad,p['claims'])


def test_mirrored_geometry_and_missing_outcome():
    a, _, _ = package(); b, _, _ = package(True)
    assert a['metrics']['forward_pass_m'] == pytest.approx(b['metrics']['forward_pass_m'])
    assert a['metrics']['reception_zone'] == b['metrics']['reception_zone']
    meta, rows = generate(family='failed')
    assert build_structured_package(EvidenceTools(meta,rows,25000)) is None


@pytest.mark.parametrize('x,zone', [(34.999,'defensive'),(35,'middle'),(69.999,'middle'),(70,'attacking'),(105,'attacking')])
def test_reception_zone_has_explicit_boundaries(x,zone):
    p, meta, rows = package()
    m=deepcopy(p['metrics']);m['pass_end']['x_m']=x
    assert spatial_context(m,meta,rows,25000)['reception_zone']==zone


def test_numeric_canonical_hash_survives_v2_roundtrip():
    from engine.core import digest
    p, _, _ = package()
    assert digest({k:v for k,v in p.items() if k!='package_hash'}) == p['package_hash']
    p['claims'][0]['input_cutoff_ms']=0
    with pytest.raises(ValidationError,match='claim_source_mismatch'):PublicationPackage.model_validate(p)


def test_corrected_endpoint_changes_geometry_only_after_delivery():
    p,meta,rows=package()
    old=next(r for r in rows if r['kind']=='event' and r['payload']['type']=='pass_resolved')
    correction=deepcopy(old)
    correction.update(message_id='corrected-endpoint',supersedes_message_id=old['message_id'],
                      revision=2,sequence_no=9999,available_at_ms=26000)
    correction['payload']['details']['end_position']['x_m']+=.1
    before=build_structured_package(EvidenceTools(meta,rows+[correction],25000))
    after=build_structured_package(EvidenceTools(meta,rows+[correction],27000))
    assert before['evidence_revision']==p['evidence_revision']
    assert after['evidence_revision']!=before['evidence_revision']
    assert after['metrics']['forward_pass_m']==pytest.approx(before['metrics']['forward_pass_m']+.1)
    assert 'corrected-endpoint' in after['claims'][0]['source_message_ids']


@pytest.mark.parametrize('field,bad',[('subject_name','Invented Player'),('window_start_ms',1),('qualification','A guaranteed goal.')])
def test_names_windows_and_qualifications_cannot_be_rebound(field,bad):
    p,_,_=package()
    next(c for c in p['claims'] if c['id']=='c-retain')[field]=bad
    with pytest.raises(ValidationError,match='claim_scope_mismatch'):PublicationPackage.model_validate(p)
