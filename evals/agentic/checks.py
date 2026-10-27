"""Mechanical discovery checks, never human/editorial ground truth.

References are read after adapter completion. Failed and missing opportunities
remain in denominators. Passing the runtime contract is not an independent
factual correctness assessment.
"""
from collections import Counter
from statistics import median


def check_result(case, row):
    package = row.get('package')
    expected = case.reference['expected_story']
    checks = {
        'expected_opportunity_delivered': bool(package) if expected else None,
        'ineligible_opportunity_withheld': not bool(package) if not expected else None,
        'runtime_contract_valid': None,
        'input_cutoff_respected': None,
        'source_evidence_was_visible': None,
        'reference_actor_attribution': None,
        'team_retention_not_individual_control': None,
        'audience_variant_matrix_complete': None,
        'reference_context_status': None,
        'reference_context_relation': None,
        'reference_comparator_identity': None,
        'seeded_fault_policy_not_violated': None,
    }
    if package:
        from engine.contracts import PublicationPackage
        try:
            PublicationPackage.model_validate(package)
            checks['runtime_contract_valid'] = True
        except Exception:
            checks['runtime_contract_valid'] = False
        checks['input_cutoff_respected'] = (
            package.get('metrics', {}).get('input_cutoff_ms', float('inf')) <= case.runtime.cutoff_ms
            and all(c.get('input_cutoff_ms', float('inf')) <= case.runtime.cutoff_ms for c in package.get('claims', [])))
        visible_ids = {row.get('message_id') for row in case.runtime.observations}
        source_ids = {message_id for claim in package.get('claims', [])
                      for message_id in claim.get('source_message_ids', [])}
        checks['source_evidence_was_visible'] = bool(source_ids) and source_ids <= visible_ids

        metrics = package.get('metrics', {})
        claims = {claim.get('id'): claim for claim in package.get('claims', [])}
        receiver_id = case.reference.get('receiver_id')
        attribution_ok = True
        if receiver_id is not None:
            attribution_ok = metrics.get('receiver_id') == receiver_id
            reception = claims.get('c-reception')
            zone = claims.get('c-zone')
            if reception is not None:
                attribution_ok = attribution_ok and reception.get('subject_id') == receiver_id
            if zone is not None:
                attribution_ok = attribution_ok and zone.get('subject_id') == receiver_id
        if expected:
            attribution_ok = attribution_ok and metrics.get('retained') is True
        checks['reference_actor_attribution'] = attribution_ok

        retention = claims.get('c-retain')
        if case.reference.get('team_retention_not_individual_control'):
            checks['team_retention_not_individual_control'] = bool(
                retention
                and retention.get('predicate') == 'team_retained'
                and retention.get('subject_id') == metrics.get('team_id')
                and retention.get('subject_id') != metrics.get('receiver_id')
                and retention.get('qualification')
            )
        elif expected:
            checks['team_retention_not_individual_control'] = bool(
                retention and retention.get('predicate') == 'team_retained'
                and retention.get('subject_id') == metrics.get('team_id')
            )

        variants = package.get('variants', [])
        actor_ids = set(metrics.get('actor_names', {}))
        expected_matrix = {(language, detail, focus)
                           for language in ('en', 'es')
                           for detail in ('simple', 'detail')
                           for focus in (None, *actor_ids)}
        actual_matrix = {(variant.get('language'), variant.get('detail'), variant.get('focus'))
                         for variant in variants}
        known_claim_ids = set(claims)
        checks['audience_variant_matrix_complete'] = (
            actual_matrix == expected_matrix
            and len(variants) == len(expected_matrix)
            and all(variant.get('factual_check_status') == 'valid'
                    and set(variant.get('claim_ids', ())) <= known_claim_ids
                    for variant in variants)
        )
        context = package.get('metrics', {}).get('context', {})
        if 'context_status' in case.reference:
            checks['reference_context_status'] = context.get('status') == case.reference['context_status']
            checks['reference_context_relation'] = context.get('relation') == case.reference['relation']
            checks['reference_comparator_identity'] = [p.get('pass_id') for p in context.get('comparators', [])] == case.reference['comparator_ids']
        fault = case.reference.get('seeded_fault')
        if fault:
            angle = (package.get('narrative_plan') or {}).get('angle')
            checks['seeded_fault_policy_not_violated'] = angle != fault['initial_angle']
    trace = row.get('trace') or (package or {}).get('trace', [])
    reviews = [t for t in trace if t.get('action') in {'claim_verdicts', 'self_review_verdicts'}]
    repair_requested = any(t.get('status') == 'revise' for t in reviews)
    fault = case.reference.get('seeded_fault')
    seeded_fault_handling = None
    if fault:
        angle = (package or {}).get('narrative_plan', {}).get('angle')
        if row.get('outcome') == 'ai_composed' and package and angle != fault['initial_angle']:
            seeded_fault_handling = 'corrected_by_model'
        elif row.get('outcome') == 'fallback' and package and angle != fault['initial_angle']:
            seeded_fault_handling = 'safe_template_fallback'
        elif row.get('outcome') == 'ai_composed' and angle == fault['initial_angle']:
            seeded_fault_handling = 'seeded_plan_left_in_ai_output'
        elif row.get('outcome') in {'rejected', 'abstention'}:
            seeded_fault_handling = 'no_story_output'
        else:
            seeded_fault_handling = 'other_failure'
    return {
        'checks': checks,
        'mechanical_checks_pass': all(value is not False for value in checks.values()),
        'missing_expected_opportunity': bool(expected and not package),
        'false_rejection_candidate': bool(expected and not package and row['outcome'] in {'rejected', 'abstention'}),
        'reviewer_or_self_review_repair_requested': repair_requested,
        'repair_returned_package': bool(repair_requested and package),
        'seeded_fault_handling': seeded_fault_handling,
        'correction_correctness': None,
        'editorial_usefulness': None,
        'false_rejection_confirmed': None,
        'human_grading_status': 'pending',
    }


def summarize(rows):
    result = {}
    for arm in sorted({row['arm'] for row in rows}):
        group = [r for r in rows if r['arm'] == arm]
        usage = [r.get('usage', {}) for r in group]
        unknown = any(any(u.get(k) is None for k in ('model_calls','input_tokens','output_tokens')) for u in usage)
        timings = [r['elapsed_ms'] for r in group if r.get('accounting') != 'not_dispatched']
        checks = sorted({key for r in group for key in r['assessment']['checks']})
        result[arm] = {
            'scheduled_outcomes': len(group),
            'unique_cases': len({r['case_id'] for r in group}),
            'lineage_groups': dict(Counter(r['lineage'] for r in group)),
            'outcomes': dict(Counter(r['outcome'] for r in group)),
            'packages': sum(bool(r.get('package')) for r in group),
            'expected_opportunities': sum(r['expected_story'] for r in group),
            'missing_expected_opportunities': sum(r['assessment']['missing_expected_opportunity'] for r in group),
            'false_rejection_candidates': sum(r['assessment']['false_rejection_candidate'] for r in group),
            'repair_requests': sum(r['assessment']['reviewer_or_self_review_repair_requested'] for r in group),
            'repair_returned_packages': sum(r['assessment']['repair_returned_package'] for r in group),
            'confirmed_correct_repairs': None,
            'confirmed_false_rejections': None,
            'human_graded_outcomes': 0,
            'usage_complete': not unknown,
            'known_usage_subtotals': {k:sum(u.get(k) or 0 for u in usage) for k in ('model_calls','input_tokens','output_tokens')},
            'observed_elapsed_ms': {'count':len(timings),'median':median(timings) if timings else None,
                                    'min':min(timings) if timings else None,'max':max(timings) if timings else None},
            'checks': {key:{'passed':sum(r['assessment']['checks'].get(key) is True for r in group),
                           'failed':sum(r['assessment']['checks'].get(key) is False for r in group),
                           'not_applicable':sum(r['assessment']['checks'].get(key) is None for r in group)} for key in checks},
        }
        fault_outcomes = Counter(r['assessment'].get('seeded_fault_handling') for r in group
                                 if r['assessment'].get('seeded_fault_handling'))
        if fault_outcomes:
            result[arm]['seeded_fault_handling'] = dict(fault_outcomes)
    result['paired_comparison_M3_vs_S3'] = paired_comparison(rows)
    return result


def paired_comparison(rows):
    """Compare Director+Reviewer with the strong single-agent arm per case.

    These are paired engineering observations, not independent samples or an
    editorial-quality grade. Deterministic checks only establish invariants.
    """
    by_key = {}
    for row in rows:
        if row.get('arm') in {'M3', 'S3'}:
            by_key.setdefault((row['case_id'], row.get('trial', 0)), {})[row['arm']] = row
    pairs = [arms for arms in by_key.values() if {'M3', 'S3'} <= set(arms)]
    both_pass = m3_only = s3_only = neither_pass = same_plan = different_plan = 0
    reviewer_actions = Counter()
    seeded_pairs = []
    for arms in pairs:
        m3, s3 = arms['M3'], arms['S3']
        m3_pass = m3['assessment']['mechanical_checks_pass']
        s3_pass = s3['assessment']['mechanical_checks_pass']
        if m3_pass and s3_pass:
            both_pass += 1
        elif m3_pass:
            m3_only += 1
        elif s3_pass:
            s3_only += 1
        else:
            neither_pass += 1
        mp, sp = (m3.get('package') or {}).get('narrative_plan'), (s3.get('package') or {}).get('narrative_plan')
        if mp is not None and sp is not None:
            if mp == sp:
                same_plan += 1
            else:
                different_plan += 1
        for item in m3.get('trace', []):
            if item.get('action') == 'claim_verdicts':
                reviewer_actions[item.get('status', 'unknown')] += 1
        if m3['assessment'].get('seeded_fault_handling') and s3['assessment'].get('seeded_fault_handling'):
            seeded_pairs.append((m3['assessment']['seeded_fault_handling'],
                                 s3['assessment']['seeded_fault_handling']))
    seeded_pairing = None
    if seeded_pairs:
        seeded_pairing = {
            'matched_fault_trials': len(seeded_pairs),
            'both_corrected_by_model': sum(m == s == 'corrected_by_model' for m, s in seeded_pairs),
            'M3_corrected_S3_did_not': sum(m == 'corrected_by_model' and s != 'corrected_by_model' for m, s in seeded_pairs),
            'S3_corrected_M3_did_not': sum(s == 'corrected_by_model' and m != 'corrected_by_model' for m, s in seeded_pairs),
            'neither_corrected_by_model': sum(m != 'corrected_by_model' and s != 'corrected_by_model' for m, s in seeded_pairs),
            'raw_pair_outcomes': [{'M3': m, 'S3': s} for m, s in seeded_pairs],
        }
    result = {
        'matched_case_trial_pairs': len(pairs),
        'mechanical_check_pairing': {
            'both_pass': both_pass,
            'M3_pass_S3_fail': m3_only,
            'S3_pass_M3_fail': s3_only,
            'both_fail': neither_pass,
        },
        'narrative_plan': {'same': same_plan, 'different': different_plan},
        'reviewer_decisions': dict(reviewer_actions),
        'interpretation_limit': 'Mechanical checks measure contract, evidence, attribution, cutoff and audience-variant invariants; they do not grade editorial usefulness or prove multi-agent superiority.',
    }
    if seeded_pairing:
        result['seeded_fault_pairing'] = seeded_pairing
    return result
