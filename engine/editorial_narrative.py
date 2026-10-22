"""Version 4 editorial rendering. Versions 1–3 remain immutable readers.

Distance significance is an explicit provisional editorial policy, not a football
quality score. Raw comparisons remain authoritative; rounding is display-only.
"""
from copy import deepcopy

from engine import contextual_narrative as legacy
from engine.contracts import PublicationPackage
from engine.core import digest

SCHEMA_VERSION = '4.0.0'
RENDERER_VERSION = 'editorial-claims-v4'
POLICY_VERSION = 'distance-emphasis-v1'


def editorial_policy(metrics):
    context = metrics['context']
    valid = context['relation'] == 'greater_than_each'
    strongest = max((p['forward_m'] for p in context['comparators']), default=0)
    gap = metrics['forward_pass_m'] - strongest if valid else None
    relative = gap / abs(strongest) if gap is not None and abs(strongest) >= 1 else None
    recommended = bool(valid and gap >= 3 and (relative is None or relative >= .2))
    return {'version': POLICY_VERSION, 'comparison_fact_supported': valid,
            'comparison_recommended': recommended, 'gap_to_largest_prior_m': gap,
            'relative_gap': relative, 'minimum_gap_m': 3.0, 'minimum_relative_gap': .2,
            'status': 'provisional_editorial_policy_not_football_validated',
            'reason': ('Visible distance contrast; no claim of tactical superiority.' if recommended else
                       'Prefer current-play facts; history is incomplete, does not exceed all comparators, or the difference is small.')}


def default_plan(metrics):
    return legacy.default_plan(metrics['context'] if editorial_policy(metrics)['comparison_recommended'] else None)


def render(claim, language, metrics):
    if claim['id'] == 'c-context':
        distance = f'{metrics["forward_pass_m"]:.1f}'
        text = (f'The pass advanced the ball {distance} m, farther forward than each '
                f'of {claim["subject_name"]}’s previous three completed passes in this replay.' if language == 'en' else
                f'El pase desplazó el balón {distance} m hacia adelante, más que cada uno '
                f'de los tres pases completados anteriores de {claim["subject_name"]} en esta repetición.')
        # A legitimate producer may explicitly select a marginal true contrast.
        # Do not imply rounded equal values establish the strict relation.
        if any(f'{p["forward_m"]:.1f}' == distance for p in metrics['context']['comparators']):
            text += (' The difference is smaller than the displayed precision; the comparison uses unrounded measurements.'
                     if language == 'en' else ' La diferencia es menor que la precisión mostrada; la comparación usa las mediciones sin redondear.')
        return text
    return legacy.render(claim, language, metrics)


def title_for(plan, metrics, language='en'):
    if plan['angle'] == 'historical_contrast':
        passer = metrics['actor_names'][metrics['passer_id']]
        return (f'{passer}: farther forward than the previous three passes' if language == 'en' else
                f'{passer}: más adelante que los tres pases anteriores')
    return legacy.title_for(plan, metrics, language)


def realize(claims, plan, metrics):
    catalog = {c['id']: c for c in claims}
    variants = []
    for language in ['en', 'es']:
        for detail in ['simple', 'detail']:
            for focus in [None, *metrics['actor_names']]:
                ids = list(plan[f'{detail}_claim_ids'])
                # The comparison already states the current forward distance.
                if 'c-context' in ids:
                    ids = [cid for cid in ids if cid != 'c-forward']
                clauses = []
                if focus == metrics['passer_id']:
                    clauses.append({'id': 'focus-release', 'claim_ids': ['c-release'],
                                    'text': render(catalog['c-release'], language, metrics)})
                elif focus == metrics['receiver_id']:
                    # One sentence establishes both reception and its location.
                    clauses.append({'id': 'focus-reception', 'claim_ids': ['c-zone', 'c-reception'],
                                    'text': render(catalog['c-zone'], language, metrics)})
                    ids = [cid for cid in ids if cid != 'c-zone']
                clauses.extend({'id': cid, 'claim_ids': [cid], 'text': render(catalog[cid], language, metrics)} for cid in ids)
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
    if metrics.get('editorial_policy') != editorial_policy(metrics):
        raise ValueError('editorial_policy_mismatch')
    # Reuse frozen v3 source/actor/context/population checks against its exact
    # realization, then validate the v4 title/clauses independently.
    original = deepcopy(package)
    original['schema_version'] = '3.0.0'
    original['renderer_version'] = legacy.RENDERER_VERSION
    original['title'] = legacy.title_for(package['narrative_plan'], metrics)
    original['variants'] = legacy.realize(package['claims'], package['narrative_plan'], metrics)
    legacy.validate_realization(original)
    if package['title'] != title_for(package['narrative_plan'], metrics):
        raise ValueError('unbound_narrative_title')
    if package['variants'] != realize(package['claims'], package['narrative_plan'], metrics):
        raise ValueError('unbound_audience_text')


def build_editorial_package(tools, revision=1, proposed_text=None, plan=None, editorial_angle=None):
    package = legacy.build_contextual_package(tools, revision, proposed_text, plan, editorial_angle)
    if package is None:
        return None
    metrics = package['metrics']
    metrics['editorial_policy'] = editorial_policy(metrics)
    selected = plan or default_plan(metrics)
    if editorial_angle:
        selected = {**selected, 'angle': editorial_angle}
    selected = legacy.check_plan(selected, package['claims'])
    package.update(schema_version=SCHEMA_VERSION, renderer_version=RENDERER_VERSION,
                   narrative_plan=selected, title=title_for(selected, metrics),
                   variants=realize(package['claims'], selected, metrics))
    base = package['variants'][0]['text']
    revised = proposed_text is not None and proposed_text.strip() != base
    package['review'].update(revised_text=base, cycles=int(revised), status='revised' if revised else 'supported',
                            reason='Selected observed '+selected['angle'].replace('_', ' ')+'. '+metrics['editorial_policy']['reason'])
    package.pop('package_hash', None)
    package['package_hash'] = digest(package)
    PublicationPackage.model_validate(package)
    return package
