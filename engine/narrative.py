"""Scoped claim selection and exact bilingual realization, independent of models.

The model chooses content/order; measurements, actors and semantic relations are
rendered from a closed claim vocabulary. Legacy v1 packages remain readable.
"""
from __future__ import annotations

from time import perf_counter

from engine.contracts import NarrativePlan, PublicationPackage
from engine.core import available, digest

RENDERER_VERSION = 'claim-blocks-v2'
FACT_IDS = ['c-forward', 'c-bypass', 'c-retain', 'c-progress', 'c-zone', 'c-pressure']


def default_plan():
    return {'angle': 'progression', 'simple_claim_ids': ['c-bypass', 'c-retain'],
            'detail_claim_ids': FACT_IDS.copy()}


def spatial_context(metrics, metadata, messages, cutoff):
    obs = available(messages, cutoff)
    start = next(row for row in obs if row['kind'] == 'event'
                 and row['payload']['type'] == 'pass_started'
                 and row['payload']['details']['pass_id'] == metrics['pass_id'])
    end = next(row for row in obs if row['kind'] == 'event'
               and row['payload']['type'] == 'pass_resolved'
               and row['payload']['details']['pass_id'] == metrics['pass_id'])
    if end['payload']['details']['outcome'] != 'received':
        raise ValueError('no_successful_reception')
    period = next(p for p in metadata['periods'] if p['period'] == start['period'])
    sign = 1 if period['attack_direction'][metrics['team_id']] == 'right' else -1
    length = metadata['pitch']['length_m']
    sx, ex = metrics['pass_start']['x_m'], metrics['pass_end']['x_m']
    if not 0 <= sx <= length or not 0 <= ex <= length:
        raise ValueError('invalid_pass_endpoint')
    normalized = ex if sign == 1 else length - ex
    zone = 'defensive' if normalized < length / 3 else 'middle' if normalized < 2 * length / 3 else 'attacking'
    return {'forward_pass_m': sign * (ex - sx), 'reception_zone': zone,
            'release_ms': start['timeline_ms'], 'reception_ms': end['timeline_ms'],
            'geometry_version': 'forward-zone-v1'}


def build_claims(metrics, metadata, geometry):
    m = metrics
    names = {entity['id']: entity['name'] for entity in metadata['players'] + metadata['teams']}
    rows = [
        ('c-pressure', 'nearby_opponents', m['passer_id'], m['pressure_opponents_max'], 'players',
         m['pressure_window_ms'][0], m['pressure_window_ms'][1], 'Proximity only, not calibrated pressure.'),
        ('c-bypass', 'longitudinal_bypass', m['team_id'], m['bypassed_count'], 'players',
         geometry['release_ms'], geometry['reception_ms'], 'Longitudinal positions do not prove a defensive line was broken.'),
        ('c-retain', 'team_retained', m['team_id'], m['retention_window_ms'] / 1000, 's',
         geometry['reception_ms'], m['retention_confirmed_at_ms'], 'Team possession, not continuous individual control.'),
        ('c-progress', 'team_progression', m['team_id'], m['progression_m'], 'm',
         geometry['reception_ms'], m['retention_confirmed_at_ms'], 'Forward ball displacement after reception.'),
        ('c-forward', 'forward_pass_displacement', m['team_id'], geometry['forward_pass_m'], 'm',
         geometry['release_ms'], geometry['reception_ms'], 'Forward displacement, not pass difficulty or causal value.'),
        ('c-zone', 'reception_zone', m['receiver_id'], geometry['reception_zone'], 'zone',
         geometry['reception_ms'], geometry['reception_ms'], 'Reception location, not a chance or a formal final-third entry.'),
        ('c-reception', 'pass_reception', m['receiver_id'], m['receiver_id'], 'player',
         geometry['reception_ms'], geometry['reception_ms'], 'Reception only; later possession is attributed to the team.'),
        ('c-release', 'pass_release', m['passer_id'], m['passer_id'], 'player',
         geometry['release_ms'], geometry['release_ms'], 'Recorded pass release, not tactical intent.'),
    ]
    return [{'id': cid, 'type': 'scoped_fact', 'predicate': predicate,
             'subject_id': subject, 'subject_name': names[subject], 'value': value, 'unit': unit,
             'evidence_revision': m['evidence_revision'], 'source_message_ids': m['source_message_ids'],
             'window_start_ms': max(0, start), 'window_end_ms': end,
             'input_cutoff_ms': m['input_cutoff_ms'], 'coverage': m['coverage'],
             'qualification': qualification}
            for cid, predicate, subject, value, unit, start, end, qualification in rows]


def check_plan(plan, claims):
    parsed = NarrativePlan.model_validate(plan).model_dump()
    catalog = {claim['id']: claim for claim in claims}
    for key in ['simple_claim_ids', 'detail_claim_ids']:
        ids = parsed[key]
        if len(set(ids)) != len(ids) or not set(ids).issubset(FACT_IDS) or not set(ids).issubset(catalog):
            raise ValueError('unsupported_narrative_claim')
    # A short view must convey observed progress and the confirmed team outcome.
    if 'c-retain' not in parsed['simple_claim_ids']:
        raise ValueError('missing_team_outcome')
    if not set(parsed['simple_claim_ids']) & {'c-forward', 'c-bypass', 'c-progress', 'c-zone'}:
        raise ValueError('missing_observed_change')
    if not {'c-bypass', 'c-retain', 'c-progress', 'c-pressure'}.issubset(parsed['detail_claim_ids']):
        raise ValueError('missing_evidence_detail')
    return parsed


def _number(value):
    return f'{float(value):.1f}'


def render_claim(claim, language, metrics):
    name, value, predicate = claim['subject_name'], claim['value'], claim['predicate']
    if language == 'en':
        texts = {
            'longitudinal_bypass': f'{name} passed beyond {int(value) if isinstance(value,(int,float)) else value} opponents in the attacking direction.',
            'team_retained': f'{name} retained possession for {float(value):g} s after reception.' if isinstance(value,(int,float)) else '',
            'team_progression': f'The team progressed {_number(value)} m after reception.' if isinstance(value,(int,float)) else '',
            'forward_pass_displacement': f'The pass moved the ball {_number(value)} m forward.' if isinstance(value,(int,float)) else '',
            'reception_zone': f'{name} received in the {value} third.',
            'pass_reception': f'{name} received the pass.',
            'pass_release': f'{name} made the pass.',
            'nearby_opponents': f'Before release, up to {int(value) if isinstance(value,(int,float)) else value} opponents were within {metrics["pressure_radius_m"]:g} m of the passer over {((metrics["pressure_window_ms"][1]-metrics["pressure_window_ms"][0])/1000):g} s.',
        }
    else:
        zone = {'defensive': 'defensivo', 'middle': 'medio', 'attacking': 'ofensivo'}.get(str(value), '')
        texts = {
            'longitudinal_bypass': f'{name} superó a {int(value) if isinstance(value,(int,float)) else value} rivales con el pase en dirección de ataque.',
            'team_retained': f'{name} conservó la posesión durante {float(value):g} s después de la recepción.' if isinstance(value,(int,float)) else '',
            'team_progression': f'El equipo avanzó {_number(value)} m después de la recepción.' if isinstance(value,(int,float)) else '',
            'forward_pass_displacement': f'El pase desplazó el balón {_number(value)} m hacia adelante.' if isinstance(value,(int,float)) else '',
            'reception_zone': f'{name} recibió en el tercio {zone}.',
            'pass_reception': f'{name} recibió el pase.',
            'pass_release': f'{name} dio el pase.',
            'nearby_opponents': f'Antes del pase, hasta {int(value) if isinstance(value,(int,float)) else value} rivales estaban a {metrics["pressure_radius_m"]:g} m del pasador en una ventana de {((metrics["pressure_window_ms"][1]-metrics["pressure_window_ms"][0])/1000):g} s.',
        }
    text = texts[predicate]
    if not text:
        raise ValueError('invalid_claim_value')
    return text


def realize_variants(claims, plan, metrics, focuses):
    plan = check_plan(plan, claims)
    catalog = {c['id']: c for c in claims}
    variants = []
    for language in ['en', 'es']:
        for detail in ['simple', 'detail']:
            ids = plan[f'{detail}_claim_ids']
            base = [{'id': cid, 'claim_ids': [cid], 'text': render_claim(catalog[cid], language, metrics)} for cid in ids]
            if detail == 'detail':
                base.append({'id': 'qualification', 'claim_ids': ['c-bypass'], 'text':
                    'Longitudinal positions do not prove a defensive line was broken.' if language == 'en' else
                    'Las posiciones longitudinales no demuestran que se rompiera una línea defensiva.'})
            for focus in focuses:
                clauses = list(base)
                role = 'c-release' if focus == metrics['passer_id'] else 'c-reception' if focus == metrics['receiver_id'] else None
                if role:
                    clauses.append({'id': 'focus', 'claim_ids': [role], 'text': render_claim(catalog[role], language, metrics)})
                elif focus is not None and focus != metrics['team_id']:
                    clauses.append({'id': 'focus-none', 'claim_ids': [], 'text':
                        'No direct contribution by this player or team is verified in this sequence.' if language == 'en' else
                        'No hay una contribución directa verificada de este jugador o equipo en la secuencia.'})
                variants.append({'id': f'{language}_{detail}_{focus or "general"}', 'language': language,
                                 'detail': detail, 'focus': focus, 'text': ' '.join(c['text'] for c in clauses),
                                 'claim_ids': list(dict.fromkeys(cid for c in clauses for cid in c['claim_ids'])),
                                 'factual_check_status': 'valid', 'clauses': clauses})
    return variants


def validate_realization(package):
    """Reference membership alone cannot approve arbitrary or contradictory prose."""
    claims, metrics = package['claims'], package['metrics']
    expected_predicates = {'c-pressure': 'nearby_opponents', 'c-bypass': 'longitudinal_bypass',
        'c-retain': 'team_retained', 'c-progress': 'team_progression', 'c-forward': 'forward_pass_displacement',
        'c-zone': 'reception_zone', 'c-reception': 'pass_reception', 'c-release': 'pass_release'}
    if {c['id']: c['predicate'] for c in claims} != expected_predicates:
        raise ValueError('unsupported_claim_predicate')
    expected_subjects = {cid: metrics['team_id'] for cid in expected_predicates}
    expected_subjects.update({'c-pressure': metrics['passer_id'], 'c-release': metrics['passer_id'],
                              'c-zone': metrics['receiver_id'], 'c-reception': metrics['receiver_id']})
    expected_values = {'c-pressure': metrics['pressure_opponents_max'], 'c-bypass': metrics['bypassed_count'],
        'c-retain': metrics['retention_window_ms']/1000, 'c-progress': metrics['progression_m'],
        'c-forward': metrics['forward_pass_m'], 'c-zone': metrics['reception_zone'],
        'c-reception': metrics['receiver_id'], 'c-release': metrics['passer_id']}
    expected_units = {'c-pressure': 'players', 'c-bypass': 'players', 'c-retain': 's',
        'c-progress': 'm', 'c-forward': 'm', 'c-zone': 'zone', 'c-reception': 'player', 'c-release': 'player'}
    for c in claims:
        if c['subject_id'] != expected_subjects[c['id']] or c['value'] != expected_values[c['id']] or c['unit'] != expected_units[c['id']]:
            raise ValueError('claim_scope_mismatch')
        if c['source_message_ids'] != metrics['source_message_ids'] or c['window_end_ms'] > c['input_cutoff_ms']:
            raise ValueError('claim_source_mismatch')
    names=metrics['actor_names']
    canonical_claims=build_claims(metrics,{'players':[{'id':key,'name':name} for key,name in names.items()], 'teams':[]},metrics)
    if {c['id']:c for c in claims}!={c['id']:c for c in canonical_claims}:
        raise ValueError('claim_scope_mismatch')
    if (package['id']!=f'story-{metrics["pass_id"]}' or package['evidence_revision']!=metrics['evidence_revision']
            or package['eligible_from_ms']!=metrics['available_from_ms']
            or package['expires_at_ms']!=metrics['retention_confirmed_at_ms']+30000):
        raise ValueError('package_scope_mismatch')
    if not metrics['eligible'] or metrics['retained'] is not True:
        raise ValueError('unsupported_retention')
    variants = package['variants']
    focus_sets = [{v['focus'] for v in variants if v['language'] == lang and v['detail'] == detail}
                  for lang in ['en','es'] for detail in ['simple','detail']]
    if focus_sets[0]!={None,*names} or any(s != focus_sets[0] for s in focus_sets):
        raise ValueError('variant_set_incomplete')
    expected = realize_variants(claims, package['narrative_plan'], metrics,
                                sorted(focus_sets[0], key=lambda x:x or ''))
    actual_map = {v['id']: v for v in variants}
    if len(actual_map) != len(variants) or actual_map != {v['id']:v for v in expected}:
        raise ValueError('unbound_audience_text')


def build_structured_package(tools, revision=1, proposed_text=None, plan=None):
    started = perf_counter()
    m = tools.compute_pass_metrics()
    if not m or not m['eligible']:
        return None
    m = {**m, **spatial_context(m, tools.metadata, tools.messages, tools.cutoff_ms)}
    m['actor_names']={p['id']:p['name'] for p in tools.metadata['players']+tools.metadata['teams']}
    claims = build_claims(m, tools.metadata, m)
    selected = check_plan(plan or default_plan(), claims)
    focuses = [None] + [p['id'] for p in tools.metadata['players']] + [t['id'] for t in tools.metadata['teams']]
    variants = realize_variants(claims, selected, m, focuses)
    base = variants[0]['text']
    revised = proposed_text is not None and proposed_text.strip() != base
    package = {'schema_version': '2.0.0', 'id': f'story-{m["pass_id"]}', 'revision': revision,
        'title': 'The forward passage, explained', 'claims': claims, 'metrics': m, 'variants': variants,
        'narrative_plan': selected, 'renderer_version': RENDERER_VERSION,
        'review': {'status': 'revised' if revised else 'supported', 'mode': 'deterministic_template',
                   'reason': 'Actor, time, units and wording resolve from scoped observed claims.',
                   'proposed_text': proposed_text, 'revised_text': base, 'cycles': int(revised)},
        'evidence_revision': m['evidence_revision'], 'eligible_from_ms': m['available_from_ms'],
        'expires_at_ms': m['retention_confirmed_at_ms']+30000,
        'trace': [{'role': 'Evidence Builder', 'action': 'bind_claims', 'status': 'supported', 'elapsed_ms': 0}],
        'workflow_ms': round((perf_counter()-started)*1000,3), 'mode': 'local deterministic template'}
    package['package_hash'] = digest(package)
    PublicationPackage.model_validate(package)
    return package
