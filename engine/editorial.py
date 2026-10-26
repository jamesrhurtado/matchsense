"""Public summaries of observable selections and review verdicts."""
from engine.contextual_narrative import render


def observable_decision(package):
    """Summarize recorded actions, without treating a model's reasons as facts."""
    trace = package.get('trace', [])
    director = next((t for t in reversed(trace) if t.get('role') == 'Story Director' and t.get('action') == 'model_decision'), {})
    reviewer = next((t for t in reversed(trace) if t.get('role') == 'Claim Reviewer' and t.get('action') == 'model_decision'), {})
    fallback = 'fallback' in package.get('mode', '')
    ids = [c['id'] for c in package['claims']]
    return {'director': 'selected' if director.get('status') == 'propose' else 'factual_template',
            'reviewer': 'supported' if reviewer.get('status') == 'supported' and not fallback else 'factual_template',
            'claim_ids': ids, 'fallback': fallback}


def decision_summary(package, outcomes):
    if package and package.get('schema_version') in {'5.0.0','6.0.0','7.0.0'}:
        return {'angle':package['family'],'lead':package['variants'][0]['text'],'context':'Source observations only; no tactical causation.',
                'review':package['review']['reason'],'changes':[],'fallback':None,'outcome':'candidate produced'}
    latest = outcomes[-1] if outcomes else {}
    trace = package['trace'] if package else latest.get('trace', [])
    selected = next((t for t in reversed(trace) if t['action']=='select_claims'), {})
    verdicts = [t for t in trace if t['action'] in {'claim_verdicts','self_review_verdicts'}]
    plan = package.get('narrative_plan') if package else selected.get('plan')
    metrics = package['metrics'] if package else {}
    context = metrics.get('context')
    scope = 'No previous-pass context was recorded.'
    if context:
        scope = (f'{context["status"].replace("_", " ")}: {context["sample_count"]} completed team passes, '
                 f'period {context["period"]}, prior {context["lookback_ms"]/1000:g} s in this replay. '
                 + ('Current pass is farther forward than each of the selected three.'
                    if context['relation']=='greater_than_each' else 'No comparative wording selected.'))
    lead = 'No publishable candidate was produced.'
    if package and plan:
        cid = plan['simple_claim_ids'][0]
        claim = next(c for c in package['claims'] if c['id']==cid)
        if package['schema_version']=='4.0.0':
            from engine.editorial_narrative import render as selected_render
        else:
            selected_render=render
        lead = selected_render(claim, 'en', metrics)
    changes = [f'Reviewer requested a repair: {t.get("reason", "No reason recorded.")}'
               for t in verdicts if t['status']=='revise']
    if changes and package:
        changes.append('The revised selection was rendered and reviewed again: '+', '.join(plan['simple_claim_ids'])+'.')
    fallback = next((t['status'] for t in trace if t['action']=='template_fallback'), None)
    if package and 'fallback' in package['mode']:
        fallback = 'Scoped factual rendering used; '+(fallback or 'model selection unavailable')+'. Producer approval is still required.'
    return {'angle': (plan or {}).get('angle','none').replace('_',' '), 'lead': lead, 'context': scope,
            'review': package['review']['reason'] if package else latest.get('reason') or 'No completed review.',
            'changes': changes, 'fallback': fallback,
            'outcome': latest.get('state') or ('candidate produced' if package else 'no candidate')}
