import pytest

from engine.foundry_workflow import Limits
from engine.contextual_narrative import default_plan, check_plan
from engine.structured_workflow import run_structured_workflow
from tests.test_foundry import FakeProvider, tools, request


def director(plan=None, action='propose', requests=None):
    return {'action':action,'plan':plan or default_plan() if action=='propose' else None,
            'reason':'Explain observed progression and confirmed team retention.',
            'evidence_requests':requests or []}


def critic(action='supported', ids=None):
    return {'action':action,'reason':'Scoped facts support the selected final output.',
            'verdicts':[{'claim_id':cid,'verdict':'supported','reason':'Matches the scoped observation.'}
                        for cid in (ids if ids is not None else ['c-pressure','c-bypass','c-retain','c-progress','c-forward','c-zone','c-reception','c-release'])],
            'evidence_requests':[]}


def test_two_role_workflow_changes_fact_selection_with_two_real_provider_attempts():
    plan=default_plan();plan['simple_claim_ids']=['c-forward','c-retain']
    provider=FakeProvider([director(plan),critic()]);events=[]
    p=run_structured_workflow(tools(),provider=provider,outcome_callback=events.append)
    assert p['schema_version']=='4.0.0'
    assert p['mode']=='Microsoft Agent Framework + Azure OpenAI'
    assert p['variants'][0]['claim_ids']==['c-forward','c-retain']
    assert p['variants'][0]['text'].startswith('The pass moved the ball')
    assert p['model_usage']['calls']==2
    assert [call[0] for call in provider.calls]==['Story Director','Claim Reviewer']
    assert events[-1]['state']=='produced' and events[-1]['usage']['total_tokens']==280


@pytest.mark.parametrize('stage',['analyst','reviewer'])
def test_abstentions_and_rejections_report_attempts_without_a_package(stage):
    answers=[director(action='abstain')] if stage=='analyst' else [director(),critic('reject')]
    events=[];provider=FakeProvider(answers)
    assert run_structured_workflow(tools(),provider=provider,outcome_callback=events.append) is None
    assert events[-1]['state']==('abstained' if stage=='analyst' else 'rejected')
    assert events[-1]['usage']['calls']==len(answers)
    assert events[-1]['usage']['total_tokens']==140*len(answers)


def test_unknown_claim_never_reaches_permissive_reviewer():
    plan=default_plan();plan['simple_claim_ids']=['c-goal','c-retain']
    provider=FakeProvider([director(plan),director(plan)])
    p=run_structured_workflow(tools(),provider=provider)
    assert p['mode']=='template fallback'
    assert p['variants'][0]['claim_ids']==['c-forward','c-retain']
    assert len(provider.calls)==2
    assert all(call[0]=='Story Director' for call in provider.calls)


def test_incomplete_review_cannot_approve_package():
    p=run_structured_workflow(tools(),provider=FakeProvider([director(),critic(ids=['c-retain'])]))
    assert p['mode']=='template fallback'
    assert p['trace'][-1]['status']=='incomplete_claim_review'


@pytest.mark.parametrize('strategy',['single','collaborative'])
def test_both_architectures_get_a_bounded_meaningful_repair(strategy):
    plan=default_plan();plan['simple_claim_ids']=['c-zone','c-retain']
    provider=FakeProvider([director(),critic('revise'),director(plan),critic()])
    p=run_structured_workflow(tools(),provider=provider,strategy=strategy)
    assert p['mode']=='Microsoft Agent Framework + Azure OpenAI'
    assert p['narrative_plan']==check_plan(plan,p['claims'])
    assert p['review']['cycles']==1
    assert len(provider.calls)==4
    if strategy=='single':assert all(c[0]=='Story Director' for c in provider.calls)
    else:assert provider.calls[1][0]=='Claim Reviewer'


def test_future_evidence_request_is_blocked_and_usage_retained():
    provider=FakeProvider([director(action='needs_evidence',requests=[request('get_sequence',22000,40000)])])
    p=run_structured_workflow(tools(),provider=provider)
    assert p['mode']=='template fallback' and len(provider.calls)==1
    assert p['model_usage']['total_tokens']==140


def test_call_ceiling_includes_critic_and_fallback_attempts():
    provider=FakeProvider([director(),critic()])
    p=run_structured_workflow(tools(),provider=provider,limits=Limits(model_calls=1))
    assert p['mode']=='template fallback' and len(provider.calls)==1
    assert p['model_usage']['calls']==1


def test_provider_failure_does_not_claim_complete_usage():
    events=[]
    p=run_structured_workflow(tools(),provider=FakeProvider([RuntimeError('private endpoint body')]),outcome_callback=events.append)
    assert p['mode']=='template fallback' and not p['model_usage']['usage_complete']
    assert 'private endpoint body' not in str(events)


def test_ineligible_observations_do_not_create_billable_work():
    provider=FakeProvider([]);events=[]
    assert run_structured_workflow(tools('ordinary'),provider=provider,outcome_callback=events.append) is None
    assert not provider.calls and events[-1]['usage']['calls']==0


def test_api_outcome_keeps_abstention_usage_and_session_identity(tmp_path,monkeypatch):
    from engine.repository import Repository
    from engine import structured_workflow
    from services.api import main
    repository=Repository(tmp_path/'api-outcome.db')
    monkeypatch.setattr(main,'repo',repository);monkeypatch.setattr(main,'FOUNDRY',True)
    monkeypatch.setattr(main,'STRUCTURED',True)
    provider=FakeProvider([director(action='abstain')])
    monkeypatch.setattr(structured_workflow,'AgentFrameworkProvider',lambda:provider)
    assert main.workflow(tools(),session_id='test-session') is None
    outcomes=repository.workflow_outcomes('test-session')
    assert len(outcomes)==1 and outcomes[0]['state']=='abstained'
    assert outcomes[0]['model_usage']['calls']==1
    assert outcomes[0]['model_usage']['total_tokens']==140
    assert outcomes[0]['package_ref'] is None
    assert not repository.workflow_outcomes('local')


def test_context_tool_and_labeled_repair_use_exact_comparator_facts():
    from tests.test_context import scene
    from engine.workflow import EvidenceTools
    meta,rows=scene();t=EvidenceTools(meta,rows,25000,'pass-1')
    ids=['c-pressure','c-bypass','c-retain','c-progress','c-forward','c-zone','c-reception','c-release','c-context']
    plan=default_plan(t.get_recent_pass_context())
    # Deliberately injected editorial challenge, not an observed spontaneous error.
    repair=critic('revise',ids);repair['reason']='Prefer the independently supported historical contrast over routine spatial detail.'
    request_context=director(action='needs_evidence',requests=[request('get_recent_pass_context',0,0)])
    provider=FakeProvider([request_context,director(),repair,director(plan),critic(ids=ids)])
    p=run_structured_workflow(t,provider=provider)
    assert p['mode']=='Microsoft Agent Framework + Azure OpenAI'
    assert p['narrative_plan']['angle']=='historical_contrast' and p['review']['cycles']==1
    assert p['model_usage']['calls']==5
    independent=provider.calls[2][2]['historical_context']
    assert [c['forward_m'] for c in independent['comparators']]==[10,7,5]
    assert independent['relation']=='greater_than_each'
    assert 'c-context' in p['variants'][0]['claim_ids']
    assert any(t['action']=='claim_verdicts' and t['status']=='revise' for t in p['trace'])


def test_missing_comparison_review_verdict_cannot_approve_context():
    from tests.test_context import scene
    from engine.workflow import EvidenceTools
    meta,rows=scene();t=EvidenceTools(meta,rows,25000,'pass-1')
    p=run_structured_workflow(t,provider=FakeProvider([director(default_plan(t.get_recent_pass_context())),critic()]))
    assert p['mode']=='template fallback'
    assert p['trace'][-1]['status']=='incomplete_claim_review'
    assert p['model_usage']['calls']==2
