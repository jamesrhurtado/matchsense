"""Evaluation scheduling/accounting checks; no provider calls."""
import asyncio
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

import pytest

from evals.agentic.dataset import discovery_cases
from evals.agentic.run import BudgetLedger, WorkflowBudget, evaluate, validate_live


def config():
    return {'max_model_calls':6,'max_input_tokens':32000,'max_output_tokens':6600,
            'max_estimated_cost':1,'input_per_million':1,'output_per_million':2,
            'rate_source':'test fixture, not a price quote','rate_date':'2026-10-21', 'currency':'USD',
            'deadline_utc':(datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat(),
            'model':'fake','model_version':'fixture','deployment':'fake','api_version':'fake','prompt_version':'test',
            'tool_version':'test','renderer_version':'test','schema_version':'test'}


def test_discovery_inputs_are_cutoff_bounded_and_label_free():
    cases = discovery_cases()
    assert len(cases)==4
    assert len({case.lineage for case in cases})==1  # Shared backbone is explicit.
    for case in cases:
        assert set(asdict(case.runtime))=={'metadata','observations','cutoff_ms','pass_id'}
        assert all(m['timeline_ms']<=case.runtime.cutoff_ms and m['available_at_ms']<=case.runtime.cutoff_ms for m in case.runtime.observations)
        assert 'reference' not in case.runtime.metadata
    relay=cases[0]
    controllers={m['payload']['controlling_player_id'] for m in relay.runtime.observations if m['kind']=='tracking_frame' and m['timeline_ms']>=relay.reference['handover_ms']}
    assert controllers=={relay.reference['next_controller_id']}
    late=cases[-1]
    assert not any(m['kind']=='event' and m['payload']['type']=='pass_resolved' for m in late.runtime.observations)
    assert late.reference['expected_story'] is False


def test_unknown_usage_keeps_reservation():
    ledger=BudgetLedger(config())
    policy=WorkflowBudget()
    assert ledger.reserve(policy)
    assert ledger.reconcile(policy,{'model_calls':1,'input_tokens':None,'output_tokens':3})=='unknown_reserved'
    assert ledger.calls==6 and ledger.input_tokens==32000 and ledger.output_tokens==6600
    assert not ledger.reserve(policy)


def test_complete_usage_releases_unused_reservation_and_detects_overrun():
    ledger=BudgetLedger(config()); policy=WorkflowBudget()
    assert ledger.reserve(policy)
    assert ledger.reconcile(policy,{'model_calls':2,'input_tokens':100,'output_tokens':20})=='complete'
    assert ledger.calls==2 and ledger.input_tokens==100
    larger=config(); larger['max_model_calls']=12
    ledger=BudgetLedger(larger); assert ledger.reserve(policy)
    assert ledger.reconcile(policy,{'model_calls':7,'input_tokens':100,'output_tokens':20})=='overrun'


def test_every_scheduled_attempt_is_retained_when_provider_fails_or_budget_ends():
    async def fails(request,policy):
        raise RuntimeError('sensitive provider text must not be copied')
    rows,ledger=asyncio.run(evaluate(discovery_cases(),{'S2':fails},config(),True))
    assert len(rows)==4
    assert [row['outcome'] for row in rows].count('failure')==1
    assert [row['outcome'] for row in rows].count('budget_exhausted')==3
    assert ledger.unknown_workflows==1
    assert 'sensitive' not in str(rows)


def test_abstention_is_an_outcome_with_usage_not_a_missing_row():
    async def abstain(request,policy):
        return {'outcome':'abstention','package':None,'usage':{'model_calls':0,'input_tokens':0,'output_tokens':0}}
    rows,_=asyncio.run(evaluate(discovery_cases(),{'S2':abstain},{'trials':2}))
    assert len(rows)==8 and all(row['outcome']=='abstention' for row in rows)
    assert all(row['human_rating'] is None for row in rows)


def test_live_requires_complete_explicit_budget_and_rate_metadata():
    with pytest.raises(ValueError,match='explicit configuration'):
        validate_live({})
    bad=config(); bad['deadline_utc']='2000-01-01T00:00:00Z'
    with pytest.raises(ValueError,match='future'):
        validate_live(bad)


def test_fair_inputs_are_copied_and_template_is_not_repeated_per_model_trial():
    observed=[]
    async def mutate(request,policy):
        observed.append(request.metadata['players'][0]['name'])
        request.metadata['players'][0]['name']='mutated'
        return {'outcome':'template','package':None,'usage':{'model_calls':0,'input_tokens':0,'output_tokens':0}}
    cases=discovery_cases()[:1]
    original=cases[0].runtime.metadata['players'][0]['name']
    rows,_=asyncio.run(evaluate(cases,{'T2':mutate,'S2':mutate},{'trials':2}))
    assert len(rows)==3 and observed==[original]*3
    assert cases[0].runtime.metadata['players'][0]['name']==original


def test_real_adapter_forwards_limits_and_preserves_usage_after_final_validation_failure(monkeypatch):
    import engine.structured_workflow
    from evals.agentic.run import agent_adapter
    seen=[]
    def fake(tools,*,strategy,outcome_callback,limits):
        seen.append((strategy,limits.model_calls,limits.token_budget))
        outcome_callback({'state':'produced','usage':{'calls':2,'input_tokens':100,'output_tokens':20,'usage_complete':True},'trace':[]})
        raise ValueError('private validation detail')
    monkeypatch.setattr(engine.structured_workflow,'run_structured_workflow',fake)
    response=asyncio.run(agent_adapter('single')(discovery_cases()[0].runtime,WorkflowBudget()))
    assert seen==[('single',6,32000)]
    assert response['outcome']=='failure' and response['package'] is None
    assert response['usage']=={'model_calls':2,'input_tokens':100,'output_tokens':20}
    assert response['reason']=='ValueError'


def test_authored_context_reference_values_and_scope_match_aggregate_without_leaking_labels():
    from evals.agentic.context_cases import context_cases
    from engine.workflow import EvidenceTools
    cases=context_cases()
    assert len(cases)==8 and len({c.lineage for c in cases})==1
    for case in cases:
        context=EvidenceTools(case.runtime.metadata,case.runtime.observations,case.runtime.cutoff_ms,case.runtime.pass_id).get_recent_pass_context()
        assert context['status']==case.reference['context_status']
        assert context['relation']==case.reference['relation']
        assert [p['pass_id'] for p in context['comparators']]==case.reference['comparator_ids']
        assert set(asdict(case.runtime))=={'metadata','observations','cutoff_ms','pass_id'}


def test_live_manifest_rejects_stale_renderer_or_unknown_provider_version():
    from evals.agentic.run import validate_runtime_identifiers
    settings={'schema_version':'3.0.0','renderer_version':'context-claims-v3',
              'prompt_version':'director-critic-v3.0','tool_version':'evidence-tools-v3',
              'deployment':'fixture','model':'fake','model_version':'fixture','api_version':'2024-10-21'}
    env={'FOUNDRY_MODEL_DEPLOYMENT':'fixture','FOUNDRY_MODEL_NAME':'fake','FOUNDRY_MODEL_VERSION':'fixture'}
    validate_runtime_identifiers(settings,env)
    with pytest.raises(ValueError,match='renderer_version'):
        validate_runtime_identifiers({**settings,'renderer_version':'claim-blocks-v2'},env)
    with pytest.raises(ValueError,match='model_version'):
        validate_runtime_identifiers(settings,{})
