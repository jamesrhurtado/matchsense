"""Version 3 realization; v1/v2 readers and their approved text stay unchanged."""
from time import perf_counter

from engine.context import contextual_metrics
from engine.contracts import NarrativePlan, PublicationPackage, RecentPassContext
from engine.core import digest
from engine.narrative import build_claims, spatial_context, render_claim, FACT_IDS

RENDERER_VERSION = 'context-claims-v3'


def default_plan(context=None):
    if context and context['relation'] == 'greater_than_each':
        return {'angle': 'historical_contrast', 'simple_claim_ids': ['c-context', 'c-retain'],
                'detail_claim_ids': ['c-context', *FACT_IDS]}
    return {'angle': 'progression', 'simple_claim_ids': ['c-forward', 'c-retain'],
            'detail_claim_ids': FACT_IDS.copy()}


def context_claim(metrics):
    ctx = metrics['context']
    return {'id': 'c-context', 'type': 'scoped_fact', 'predicate': 'previous_pass_comparison',
            'subject_id': metrics['team_id'], 'subject_name': metrics['actor_names'][metrics['team_id']],
            'value': ctx['current_forward_m'], 'unit': 'm',
            'evidence_revision': metrics['evidence_revision'],
            'source_message_ids': ctx['source_message_ids'],
            'window_start_ms': ctx['window_start_ms'], 'window_end_ms': metrics['reception_ms'],
            'input_cutoff_ms': metrics['input_cutoff_ms'], 'coverage': 1,
            'qualification': ctx['limitation']}


def canonical_claims(metrics):
    claims = build_claims(metrics, {'players': [{'id': k, 'name': v} for k, v in metrics['actor_names'].items()],
                                   'teams': []}, metrics)
    if metrics['context']['relation'] == 'greater_than_each':
        claims.append(context_claim(metrics))
    return claims


def check_plan(plan, claims):
    parsed = NarrativePlan.model_validate(plan).model_dump()
    allowed = {c['id'] for c in claims} - {'c-release', 'c-reception'}
    for key in ['simple_claim_ids', 'detail_claim_ids']:
        ids = parsed[key]
        if len(set(ids)) != len(ids) or not set(ids) <= allowed:
            raise ValueError('unsupported_narrative_claim')
    if 'c-retain' not in parsed['simple_claim_ids']:
        raise ValueError('missing_team_outcome')
    if not {'c-bypass', 'c-retain', 'c-progress', 'c-pressure'} <= set(parsed['detail_claim_ids']):
        raise ValueError('missing_evidence_detail')
    lead = {'progression': 'c-forward', 'reception': 'c-zone', 'proximity': 'c-pressure',
            'historical_contrast': 'c-context'}[parsed['angle']]
    if lead not in allowed:
        raise ValueError('angle_requires_evidence')
    # Angle changes the lead mechanically; the model cannot choose an angle and
    # deliver unrelated content. Keep a confirmed outcome in the short view.
    for key in ['simple_claim_ids', 'detail_claim_ids']:
        ids = parsed[key]
        if lead not in ids:
            ids = [lead, *ids]
        else:
            ids = [lead, *(cid for cid in ids if cid != lead)]
        parsed[key] = ids[:3] if key == 'simple_claim_ids' else ids
        if key == 'simple_claim_ids' and 'c-retain' not in parsed[key]:
            parsed[key][-1] = 'c-retain'
    return parsed


def render(claim, language, metrics):
    if claim['id'] == 'c-context':
        if language == 'en':
            return (f'The pass advanced the ball {metrics["forward_pass_m"]:g} m, farther forward than each '
                    f'of {claim["subject_name"]}’s previous three completed passes in this replay.')
        return (f'El pase desplazó el balón {metrics["forward_pass_m"]:g} m hacia adelante, más que cada uno '
                f'de los tres pases completados anteriores de {claim["subject_name"]} en esta repetición.')
    return render_claim(claim, language, metrics)


def title_for(plan, metrics, language='en'):
    names = metrics['actor_names']
    passer, receiver = names[metrics['passer_id']], names[metrics['receiver_id']]
    distance = f'{metrics["forward_pass_m"]:.1f}'
    if plan['angle'] == 'historical_contrast':
        return (f'{passer}: {distance} m, beyond the previous three' if language == 'en' else
                f'{passer}: {distance} m, más que los tres anteriores')
    if plan['angle'] == 'reception':
        zone = metrics['reception_zone']
        return (f'{receiver} receives in the {zone} third' if language == 'en' else
                f'{receiver} recibe en el tercio '+{'defensive':'defensivo','middle':'medio','attacking':'ofensivo'}[zone])
    if plan['angle'] == 'proximity':
        return (f'{passer}: {metrics["pressure_opponents_max"]} nearby opponents before release' if language == 'en' else
                f'{passer}: {metrics["pressure_opponents_max"]} rivales cercanos antes del pase')
    return f'{passer} → {receiver} · {distance} m '+('forward' if language == 'en' else 'hacia adelante')


def realize(claims, plan, metrics):
    catalog = {c['id']: c for c in claims}
    variants = []
    for language in ['en', 'es']:
        for detail in ['simple', 'detail']:
            for focus in [None, *metrics['actor_names']]:
                ids = list(plan[f'{detail}_claim_ids'])
                if focus == metrics['passer_id']:
                    ids = ['c-release', *ids]
                elif focus == metrics['receiver_id']:
                    ids = ['c-zone', 'c-reception', *(cid for cid in ids if cid != 'c-zone')]
                clauses = [{'id': cid, 'claim_ids': [cid], 'text': render(catalog[cid], language, metrics)} for cid in ids]
                if detail == 'detail':
                    clauses.append({'id': 'qualification', 'claim_ids': ['c-bypass'], 'text':
                        'Longitudinal positions do not prove a defensive line was broken.' if language == 'en' else
                        'Las posiciones longitudinales no demuestran que se rompiera una línea defensiva.'})
                if focus and focus not in {metrics['passer_id'], metrics['receiver_id'], metrics['team_id']}:
                    clauses.append({'id': 'focus-none', 'claim_ids': [], 'text':
                        'No direct contribution by this player or team is verified in this sequence.' if language == 'en' else
                        'No hay una contribución directa verificada de este jugador o equipo en la secuencia.'})
                variants.append({'id': f'{language}_{detail}_{focus or "general"}', 'language': language,
                                 'detail': detail, 'focus': focus, 'text': ' '.join(c['text'] for c in clauses),
                                 'claim_ids': list(dict.fromkeys(cid for c in clauses for cid in c['claim_ids'])),
                                 'factual_check_status': 'valid', 'clauses': clauses})
    return variants


def validate_realization(package):
    metrics = package['metrics']
    ctx = metrics['context']
    RecentPassContext.model_validate(ctx)
    if ctx['version'] != 'recent-completed-three-v1' or ctx['current_pass_id'] != metrics['pass_id'] or ctx['team_id'] != metrics['team_id']:
        raise ValueError('context_scope_mismatch')
    if ctx['release_ms'] != metrics['release_ms'] or ctx['cutoff_ms'] > metrics['input_cutoff_ms']:
        raise ValueError('context_scope_mismatch')
    original = {k: v for k, v in ctx.items() if k not in {'revision', 'cutoff_ms'}}
    if digest(original)[:16] != ctx['revision']:
        raise ValueError('context_hash_mismatch')
    if package['evidence_revision'] != digest([metrics['current_evidence_revision'], ctx['revision']])[:16]:
        raise ValueError('context_revision_mismatch')
    if ctx['relation'] == 'greater_than_each':
        selected = ctx['comparators']
        if (ctx['status'] != 'available' or not ctx['coverage_complete'] or len(selected) != 3 or
                ctx['sample_count'] != 3 or len({p['pass_id'] for p in selected}) != 3 or
                ctx['unit'] != 'm' or ctx['team_id'] != metrics['team_id'] or
                ctx['current_forward_m'] != metrics['forward_pass_m'] or
                any(p['pass_id'] == metrics['pass_id'] or
                    not ctx['window_start_ms'] <= p['resolution_ms'] < ctx['release_ms'] or
                    not metrics['forward_pass_m'] > p['forward_m'] for p in selected)):
            raise ValueError('unsupported_context_relation')
    claims = canonical_claims(metrics)
    if package['claims'] != claims:
        raise ValueError('claim_scope_mismatch')
    plan = check_plan(package['narrative_plan'], claims)
    if package['narrative_plan'] != plan or package['title'] != title_for(plan, metrics):
        raise ValueError('unbound_narrative_title')
    if package['variants'] != realize(claims, plan, metrics):
        raise ValueError('unbound_audience_text')
    if (package['id'] != f'story-{metrics["pass_id"]}' or not metrics['eligible'] or
            metrics['retained'] is not True or package['eligible_from_ms'] != metrics['available_from_ms'] or
            package['expires_at_ms'] != metrics['retention_confirmed_at_ms'] + 30000):
        raise ValueError('package_scope_mismatch')


def build_contextual_package(tools, revision=1, proposed_text=None, plan=None, editorial_angle=None):
    started = perf_counter()
    metrics = contextual_metrics(tools.compute_pass_metrics(), tools.metadata, tools.messages, tools.cutoff_ms)
    if not metrics or not metrics['eligible']:
        return None
    metrics.update(spatial_context(metrics, tools.metadata, tools.messages, tools.cutoff_ms))
    entities = tools.metadata['players'] + tools.metadata['teams']
    names = [p['name'] for p in entities]
    teams = {t['id']:t['name'] for t in tools.metadata['teams']}
    metrics['actor_names'] = {
        p['id']: (f'{p["name"]} ({teams[p["team_id"]]} #{p["number"]})' if 'number' in p else f'{p["name"]} ({p["id"]})')
        if names.count(p['name'])>1 else p['name'] for p in entities}

    claims = canonical_claims(metrics)
    requested = plan or default_plan(metrics['context'])
    if editorial_angle:
        requested = {**requested, 'angle':editorial_angle}
    selected = check_plan(requested, claims)
    variants = realize(claims, selected, metrics)
    base = variants[0]['text']
    revised = proposed_text is not None and proposed_text.strip() != base
    package = {'schema_version': '3.0.0', 'id': f'story-{metrics["pass_id"]}', 'revision': revision,
               'title': title_for(selected, metrics), 'claims': claims, 'metrics': metrics, 'variants': variants,
               'narrative_plan': selected, 'renderer_version': RENDERER_VERSION,
               'review': {'status': 'revised' if revised else 'supported', 'mode': 'deterministic_template',
                          'reason': 'Selected observed '+selected['angle'].replace('_', ' ')+'. '+
                                    ('Custom wording cannot be represented by the selected facts; the supported explanation is shown.' if revised else
                                     'Actors, measurements and comparison scope are rendered from evidence.'),
                          'proposed_text': proposed_text, 'revised_text': base, 'cycles': int(revised)},
               'evidence_revision': metrics['evidence_revision'], 'eligible_from_ms': metrics['available_from_ms'],
               'expires_at_ms': metrics['retention_confirmed_at_ms'] + 30000,
               'trace': [{'role': 'Evidence Builder', 'action': 'recent_pass_context',
                          'status': metrics['context']['status'], 'sample_count': metrics['context']['sample_count'],
                          'relation': metrics['context']['relation'], 'elapsed_ms': 0}],
               'workflow_ms': round((perf_counter()-started)*1000, 3), 'mode': 'local deterministic template'}
    package['package_hash'] = digest(package)
    PublicationPackage.model_validate(package)
    return package
