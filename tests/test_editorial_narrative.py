"""Versioned editorial policy, concise realization and immutable old readers."""
from copy import deepcopy

import pytest
from pydantic import ValidationError

from engine.contextual_narrative import build_contextual_package
from engine.editorial_narrative import build_editorial_package
from engine.contracts import PublicationPackage
from engine.workflow import EvidenceTools
from engine.structured_workflow import run_structured_workflow
from tests.test_context import scene
from tests.test_foundry import FakeProvider
from tests.test_structured_workflow import director


def package(distances=(5,7,10), angle=None):
    meta, rows=scene(distances)
    return build_editorial_package(EvidenceTools(meta,rows,25000,'pass-1'),editorial_angle=angle)


def test_tiny_true_comparison_does_not_automatically_become_headline():
    p=package((17.8,17.9,18.0))
    assert p['metrics']['context']['relation']=='greater_than_each'
    assert p['metrics']['editorial_policy']['comparison_recommended'] is False
    assert p['narrative_plan']['angle']=='progression'
    assert 'previous three' not in p['title']
    assert p['metrics']['editorial_policy']['status'].startswith('provisional')


def test_clear_contrast_is_concise_and_consistently_rounded():
    p=package()
    assert p['schema_version']=='4.0.0'
    assert p['narrative_plan']['angle']=='historical_contrast'
    assert 'farther forward than the previous three passes' in p['title']
    v=next(v for v in p['variants'] if v['id']=='en_detail_general')
    assert '18.1 m' in v['text'] and '18.084' not in v['text']
    assert 'c-forward' not in v['claim_ids'] and 'c-context' in v['claim_ids']
    assert p['metrics']['forward_pass_m']!=18.1  # display rounding cannot change raw evidence
    PublicationPackage.model_validate(p)


def test_focused_reception_binds_location_and_actor_once():
    p=package()
    v=next(v for v in p['variants'] if v['id']==f'en_simple_{p["metrics"]["receiver_id"]}')
    assert v['clauses'][0]['claim_ids']==['c-zone','c-reception']
    assert v['text'].count('received')==1
    assert 'retained possession' in v['text']


def test_rounded_tie_is_disclosed_for_explicit_supported_editorial_selection():
    # Current 18.084 and comparator18.08 both display18.1; relation remains raw.
    p=package((5,7,18.08),'historical_contrast')
    assert p['metrics']['editorial_policy']['comparison_recommended'] is False
    assert 'smaller than the displayed precision' in p['variants'][0]['text']
    assert 'sin redondear' in next(v['text'] for v in p['variants'] if v['id']=='es_simple_general')


def test_v4_cannot_forge_policy_or_rendering_and_v3_keeps_its_text():
    p=package();bad=deepcopy(p)
    bad['metrics']['editorial_policy']['minimum_gap_m']=0
    with pytest.raises(ValidationError,match='editorial_policy_mismatch'):
        PublicationPackage.model_validate(bad)
    bad=deepcopy(p);bad['variants'][0]['text']='Guaranteed goal'
    with pytest.raises(ValidationError,match='unbound_audience_text'):
        PublicationPackage.model_validate(bad)
    meta,rows=scene();old=build_contextual_package(EvidenceTools(meta,rows,25000,'pass-1'))
    text=old['variants'][0]['text'];old_hash=old['package_hash']
    PublicationPackage.model_validate(old)
    assert old['schema_version']=='3.0.0' and '18.084' in text
    assert old['package_hash']==old_hash and old['variants'][0]['text']==text


def test_reviewer_ablation_is_explicit_and_never_selected_by_production_default():
    meta,rows=scene();tools=EvidenceTools(meta,rows,25000,'pass-1')
    with pytest.raises(ValueError,match='evaluation_only'):
        run_structured_workflow(tools,strategy='director_only')
    p=run_structured_workflow(tools,provider=FakeProvider([director()]),
                              strategy='director_only',evaluation_only=True)
    assert p['model_usage']['calls']==1
    assert any(t['action']=='evaluation_no_reviewer' for t in p['trace'])


def test_public_decision_summary_uses_the_exact_versioned_display_precision():
    from engine.editorial import decision_summary
    p=package()
    summary=decision_summary(p,[])
    assert summary['lead']==p['variants'][0]['clauses'][0]['text']
    assert '18.084' not in summary['lead']
