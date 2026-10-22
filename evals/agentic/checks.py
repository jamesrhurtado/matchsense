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
        'reference_context_status': None,
        'reference_context_relation': None,
        'reference_comparator_identity': None,
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
        context = package.get('metrics', {}).get('context', {})
        if 'context_status' in case.reference:
            checks['reference_context_status'] = context.get('status') == case.reference['context_status']
            checks['reference_context_relation'] = context.get('relation') == case.reference['relation']
            checks['reference_comparator_identity'] = [p.get('pass_id') for p in context.get('comparators', [])] == case.reference['comparator_ids']
    trace = row.get('trace') or (package or {}).get('trace', [])
    reviews = [t for t in trace if t.get('action') in {'claim_verdicts', 'self_review_verdicts'}]
    repair_requested = any(t.get('status') == 'revise' for t in reviews)
    return {
        'checks': checks,
        'mechanical_checks_pass': all(value is not False for value in checks.values()),
        'missing_expected_opportunity': bool(expected and not package),
        'false_rejection_candidate': bool(expected and not package and row['outcome'] in {'rejected', 'abstention'}),
        'reviewer_or_self_review_repair_requested': repair_requested,
        'repair_returned_package': bool(repair_requested and package),
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
    return result
