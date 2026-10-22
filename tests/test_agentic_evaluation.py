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
    assert len(cases)==11 and len({c.lineage for c in cases})==1
    for case in cases:
        context=EvidenceTools(case.runtime.metadata,case.runtime.observations,case.runtime.cutoff_ms,case.runtime.pass_id).get_recent_pass_context()
        assert context['status']==case.reference['context_status']
        assert context['relation']==case.reference['relation']
        assert [p['pass_id'] for p in context['comparators']]==case.reference['comparator_ids']
        assert set(asdict(case.runtime))=={'metadata','observations','cutoff_ms','pass_id'}


def test_live_manifest_rejects_stale_renderer_or_unknown_provider_version():
    from evals.agentic.run import validate_runtime_identifiers
    settings={'schema_version':'4.0.0','renderer_version':'editorial-claims-v4',
              'prompt_version':'director-critic-v4.1','tool_version':'evidence-tools-v3',
              'deployment':'fixture','model':'fake','model_version':'fixture','api_version':'2024-10-21'}
    env={'FOUNDRY_MODEL_DEPLOYMENT':'fixture','FOUNDRY_MODEL_NAME':'fake','FOUNDRY_MODEL_VERSION':'fixture'}
    validate_runtime_identifiers(settings,env)
    with pytest.raises(ValueError,match='renderer_version'):
        validate_runtime_identifiers({**settings,'renderer_version':'claim-blocks-v2'},env)
    with pytest.raises(ValueError,match='model_version'):
        validate_runtime_identifiers(settings,{})


def test_subset_and_arm_selection_reject_silent_mistakes():
    from evals.agentic.run import select_cases,select_adapters
    cases=discovery_cases()
    assert select_cases(cases,cases[1].case_id)==[cases[1]]
    with pytest.raises(ValueError,match='known'):
        select_cases(cases,'typo')
    with pytest.raises(ValueError,match='unique'):
        select_adapters('T3,T3',True)
    with pytest.raises(ValueError,match='explicit --live'):
        select_adapters('D3',False)
    assert list(select_adapters('T3,S3,M3,D3',True))==['T3','S3','M3','D3']


def test_director_ablation_is_explicit_evaluator_only(monkeypatch):
    import engine.structured_workflow
    from evals.agentic.run import agent_adapter
    seen=[]
    def fake(tools,**kwargs):
        seen.append(kwargs)
        kwargs['outcome_callback']({'state':'abstained','usage':{'calls':1,'input_tokens':12,'output_tokens':4,'usage_complete':True}})
    monkeypatch.setattr(engine.structured_workflow,'run_structured_workflow',fake)
    result=asyncio.run(agent_adapter('director_only')(discovery_cases()[0].runtime,WorkflowBudget()))
    assert seen[0]['evaluation_only'] is True
    assert seen[0]['strategy']=='director_only'
    assert result['usage']['model_calls']==1


def test_mechanical_summary_keeps_failed_and_rejected_opportunities_in_denominator():
    from evals.agentic.checks import summarize
    async def reject(request,policy):
        return {'outcome':'rejected','package':None,'usage':{'model_calls':1,'input_tokens':None,'output_tokens':None}}
    rows,_=asyncio.run(evaluate(discovery_cases(),{'M3':reject},{'trials':1}))
    summary=summarize(rows)['M3']
    assert summary['scheduled_outcomes']==4
    assert summary['expected_opportunities']==3
    assert summary['missing_expected_opportunities']==3
    assert summary['false_rejection_candidates']==3
    assert summary['confirmed_false_rejections'] is None
    assert summary['usage_complete'] is False
    assert summary['known_usage_subtotals']['model_calls']==4
    assert summary['checks']['ineligible_opportunity_withheld']['passed']==1
    assert summary['human_graded_outcomes']==0


def test_blinded_packets_cover_missing_outputs_and_do_not_invent_ratings(tmp_path):
    import csv,json
    from evals.agentic.run import write_rating_materials
    rows=[{'case_id':'x','arm':'D3','trial':1,'package':{'title':'A pass','mode':'ai_composed','trace':['private'],
           'narrative_plan':{'angle':'progression'},'variants':[],'claims':[],'metrics':{}}},
          {'case_id':'y','arm':'M3','trial':0,'package':None}]
    write_rating_materials(tmp_path,rows,3)
    packets=json.loads((tmp_path/'rating-packets.json').read_text())
    assert len(packets)==2
    assert sum(p['status']=='no_output' for p in packets)==1
    assert all('arm' not in p and 'trial' not in p for p in packets)
    text=(tmp_path/'rating-packets.json').read_text()
    assert 'ai_composed' not in text and 'narrative_plan' not in text and 'private' not in text
    with (tmp_path/'rating-instrument.csv').open() as handle:
        instrument=list(csv.DictReader(handle))
    assert len(instrument)==2
    assert all(row['factual_correctness_1_5']==row['rater_id']=='' for row in instrument)
    mapping=json.loads((tmp_path/'rating-mapping-private.json').read_text())
    assert {m['arm'] for m in mapping.values()}=={'D3','M3'}
    assert (tmp_path/'rating-mapping-private.json').stat().st_mode & 0o777==0o600


def test_context_reference_checks_detect_changed_population():
    from copy import deepcopy
    from evals.agentic.checks import check_result
    from evals.agentic.context_cases import context_cases
    from engine.contextual_narrative import build_contextual_package
    from engine.workflow import EvidenceTools
    case=context_cases()[0]
    package=build_contextual_package(EvidenceTools(case.runtime.metadata,case.runtime.observations,case.runtime.cutoff_ms,case.runtime.pass_id))
    good=check_result(case,{'package':package,'outcome':'template'})
    assert good['mechanical_checks_pass']
    changed=deepcopy(package)
    changed['metrics']['context']['comparators'].reverse()
    bad=check_result(case,{'package':changed,'outcome':'template'})
    assert not bad['checks']['reference_comparator_identity']
    assert not bad['mechanical_checks_pass']
