"""Shared accounting wrapper for v5 generation; paid mode is separately opt-in."""
from engine.event_narrative import build_event_package
from engine.outcomes import create_outcome, start_outcome, finish_outcome
from engine.workflow import EvidenceTools


def generate_event(repo,sid,m,meta,messages,at,revision,model=False,outcome=None):
    outcome=outcome or create_outcome(repo,sid,f'story-{m["family"]}-{m["subject_id"]}',m['evidence_revision'],revision,at,
                           'Microsoft Agent Framework + Azure OpenAI' if model else 'local deterministic template')
    outcome=start_outcome(repo,outcome);last={}
    def observe(event):
        nonlocal outcome,last
        last=event
        if event['state']=='started':
            outcome={**outcome,'model_usage':event['usage'],'trace':event['trace']}
            repo.save_workflow_outcome(sid,outcome)
    try:
        if model:
            from engine.structured_workflow import run_event_workflow
            p=run_event_workflow(EvidenceTools(meta,messages,at),m['family'],m['subject_id'],revision,outcome_callback=observe)
        else:p=build_event_package(m,meta,revision)
        finish_outcome(repo,outcome,last.get('state') or ('produced' if p else 'abstained'),package=p,usage=last.get('usage') or ({'calls':0,'input_tokens':0,'output_tokens':0,'total_tokens':0,'usage_complete':True} if not model else None),trace=last.get('trace'),reason=last.get('reason'))
        return p
    except Exception:
        finish_outcome(repo,outcome,'failed',usage=last.get('usage'),reason='event_workflow_failure')
        raise
