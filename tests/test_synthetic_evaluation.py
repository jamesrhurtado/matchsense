"""Check report accounting and ensure known product gaps stay visible."""
from evals.synthetic import build_report, evaluate_case, signature, summarize
from simulator.scenarios import get_case


def test_report_counts_false_alerts_and_detects_later_passes():
    rows=[evaluate_case(get_case(c)) for c in ('p01-01','p01-08','p01-27','p01-28')]
    report=build_report(rows,'template')
    assert report['summary']['cases']==4
    assert report['summary']['cases_passed']==4
    assert report['summary']['false_alert_distinct_moments']==0
    assert report['summary']['missed_distinct_moments']==0
    assert report['by_family']['rounding_boundary']['cases_failed']==0
    assert report['model_usage']['calls']==0
    assert report['workflows']['variants_checked']>=100
    assert len(signature(report)['cases'])==4
    assert report['input_integrity']=={'source_commit':'b9bc99f','cases_checked':4,'unchanged':True}


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


def test_false_alert_accounting_does_not_inflate_true_moment_count():
    row=evaluate_case(get_case('p01-01'))
    row['checks'][0].update(detected_pass_ids=['pass-1'],passed=False)
    row['passed']=False
    summary=summarize([row])
    assert summary['checkpoint_false_positive']==1
    assert summary['false_alert_distinct_moments']==1
    assert summary['expected_distinct_moments']==1
    assert summary['detected_expected_moments']==1
    assert summary['false_alerts_per_simulated_minute']==1


def test_regression_inputs_match_snapshot_from_before_multipass_fix():
    import json
    from evals.synthetic import ROOT
    frozen=json.loads((ROOT/'evals/synthetic-v2/input-baseline.json').read_text())
    current=json.loads((ROOT/'evals/synthetic-v2/baseline.json').read_text())
    assert frozen['source_commit']=='b9bc99f'
    assert len(frozen['cases'])==len(current['cases'])==168
    for case_id, hashes in frozen['cases'].items():
        assert all(current['cases'][case_id][key]==value for key,value in hashes.items())
