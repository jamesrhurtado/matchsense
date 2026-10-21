"""Check report accounting and ensure known product gaps stay visible."""
from evals.synthetic import build_report, evaluate_case, signature, summarize
from simulator.scenarios import get_case


def test_report_counts_false_alerts_and_missed_later_passes():
    rows=[evaluate_case(get_case(c)) for c in ('p01-01','p01-08','p01-27','p01-28')]
    report=build_report(rows,'template')
    assert report['summary']['cases']==4
    assert report['summary']['cases_passed']==1
    assert report['summary']['false_alert_distinct_moments']==1
    assert report['summary']['missed_distinct_moments']==3
    assert report['by_family']['rounding_boundary']['cases_failed']==1
    assert report['model_usage']['calls']==0
    assert report['workflows']['variants_checked']>=100
    assert len(signature(report)['cases'])==4


def test_counts_are_at_checkpoints_and_moments_not_tracking_rows():
    rows=[evaluate_case(get_case('p01-22'))]
    summary=summarize(rows)
    assert summary['cases_passed']==1
    assert summary['checks']==5
    assert summary['checkpoint_true_positive']==2
    assert summary['expected_distinct_moments']==1
    assert summary['detected_expected_moments']==1
    assert summary['false_alert_distinct_moments']==0


def test_optional_model_budget_and_incomplete_abstention_usage_are_visible():
    calls=[]
    def abstain(tools):
        calls.append(tools.cutoff_ms)
        return None
    budget={'remaining':1}
    rows=[evaluate_case(get_case(c),workflow_runner=abstain,budget=budget) for c in ('p01-01','p02-01')]
    report=build_report(rows,'foundry')
    assert len(calls)==1
    assert report['workflows']['abstained']==1
    assert report['workflows']['skipped_budget']==1
    assert report['model_usage']['calls_are_lower_bound'] is True
    assert report['model_usage']['usage_complete'] is False
    assert report['model_usage']['cost_usd'] is None
