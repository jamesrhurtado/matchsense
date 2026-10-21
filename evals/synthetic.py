"""Evaluate authored synthetic checkpoints; report failures without tuning labels.

Default is offline and makes zero model calls. --mode foundry is a separate,
explicit small sample using existing configured credentials and deployment.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import statistics
from time import perf_counter

from engine.contracts import PublicationPackage
from engine.core import available, digest, pass_metrics
from engine.workflow import EvidenceTools, run_workflow, validate_variants
from simulator.scenarios import VERSION, cases, get_case
from simulator.suite import generate_case, serialize
from simulator.validate import validate, validate_feed


ROOT = Path(__file__).resolve().parents[1]


def evaluate_case(case, *, workflow_runner=run_workflow, budget=None):
    dataset = generate_case(case)
    validate(dataset.metadata,dataset.clean)
    validation = validate_feed(dataset.metadata,dataset.observations)
    findings = []
    packages = {}
    workflow_rows = []
    timings = []
    checks = []
    plays = {p['pass_id']:p for p in dataset.reference['plays']}
    for check in dataset.reference['checks']:
        cutoff = check['at_ms']
        started = perf_counter()
        measurements = pass_metrics(dataset.observations,cutoff,dataset.metadata)
        timings.append((perf_counter()-started)*1000)
        # This is the application's original overlay deadline, not an extension
        # when a late observation finally arrives. The core metric alone does not
        # decide whether a live overlay is still displayable.
        predicted = []
        for measured in measurements:
            if not (measured['eligible'] and measured['available_from_ms']<=cutoff<measured['retention_confirmed_at_ms']+30000):
                continue
            predicted.append(measured['pass_id'])
            revision = measured['evidence_revision']
            if revision not in packages:
                if budget is not None and budget['remaining']<=0:
                    packages[revision] = None
                    workflow_rows.append({'cutoff_ms':cutoff,'status':'not_run_budget','evidence_revision':revision})
                else:
                    if budget is not None: budget['remaining'] -= 1
                    began = perf_counter()
                    package = workflow_runner(EvidenceTools(dataset.metadata,dataset.observations,cutoff,pass_id=measured['pass_id']))
                    packages[revision] = package
                    row = {'cutoff_ms':cutoff,'evidence_revision':revision,
                           'wall_ms':round((perf_counter()-began)*1000,3),
                           'mode':package['mode'] if package else 'abstained',
                           'status':'produced' if package else 'abstained',
                           'usage':package.get('model_usage') if package else None}
                    if package:
                        PublicationPackage.model_validate(package)
                        validate_variants(package['variants'],package['metrics'],dataset.metadata)
                        assert digest({k:v for k,v in package.items() if k!='package_hash'})==package['package_hash'], 'invalid_package_hash'
                        visible_ids = {m['message_id'] for m in available(dataset.observations,cutoff)}
                        assert set(package['metrics']['source_message_ids']).issubset(visible_ids), 'future_or_replaced_evidence'
                        assert package['eligible_from_ms']<=cutoff, 'premature_package'
                        assert package['expires_at_ms']==plays[measured['pass_id']]['expires_at_ms'], 'shifted_expiry'
                        if measured['pass_id'] in expected_at_cutoff(dataset.reference,cutoff):
                            bounds = plays[measured['pass_id']]['positive_claim_bounds']
                            assert all(bounds[c['id']][0]<=c['value']<=bounds[c['id']][1] for c in package['claims']), 'authored_claim_mismatch'
                            assert package['metrics']['receiver_id']==plays[measured['pass_id']]['actual_receiver_id'], 'incorrect_actual_receiver'
                        row['variants_checked'] = len(package['variants'])
                        row['trace_actions'] = [{'role':t['role'],'action':t['action'],'status':t['status']} for t in package['trace']]
                    workflow_rows.append(row)
        expected = check['expected_pass_ids']
        row = check | {'detected_pass_ids':predicted,'passed':set(expected)==set(predicted)}
        checks.append(row)
        if not row['passed']:
            findings.append({'at_ms':cutoff,'expected':expected,'detected':predicted,
                             'metrics':[{key:m[key] for key in ('pass_id','coverage','pressure_opponents_max','bypassed_count','retained','progression_m','eligible')} for m in measurements]})
    return {'case_id':case.id,'match_id':case.match_id,'split':case.parent.split,'parent':case.parent.id,
            'family':case.family,'duration_ms':dataset.reference['duration_ms'],
            'observations_sha256':hashlib.sha256(serialize(dataset.observations).encode()).hexdigest(),
            'reference_sha256':hashlib.sha256(json.dumps(dataset.reference,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            'validation':validation,'checks':checks,'passed':not findings,'findings':findings,
            'workflows':workflow_rows,'metric_timings_ms':timings}


def expected_at_cutoff(reference,cutoff):
    return {pid for check in reference['checks'] if check['at_ms']==cutoff for pid in check['expected_pass_ids']}


def summarize(rows):
    checks = [c for row in rows for c in row['checks']]
    tp = sum(len(set(c['expected_pass_ids']) & set(c['detected_pass_ids'])) for c in checks)
    fp = sum(len(set(c['detected_pass_ids']) - set(c['expected_pass_ids'])) for c in checks)
    fn = sum(len(set(c['expected_pass_ids']) - set(c['detected_pass_ids'])) for c in checks)
    expected_moments = {(r['case_id'],pid) for r in rows for c in r['checks'] for pid in c['expected_pass_ids']}
    detected_moments = {(r['case_id'],pid) for r in rows for c in r['checks'] for pid in c['detected_pass_ids']}
    false_alerts = {(r['case_id'],pid) for r in rows for c in r['checks'] for pid in set(c['detected_pass_ids'])-set(c['expected_pass_ids'])}
    minutes = sum(r['duration_ms'] for r in rows)/60000
    return {'cases':len(rows),'parents':len({r['parent'] for r in rows}),
            'cases_passed':sum(r['passed'] for r in rows),'cases_failed':sum(not r['passed'] for r in rows),
            'checks':len(checks),'checks_passed':sum(c['passed'] for c in checks),
            'checkpoint_true_positive':tp,'checkpoint_false_positive':fp,'checkpoint_false_negative':fn,
            'checkpoint_precision':tp/(tp+fp) if tp+fp else None,
            'checkpoint_recall':tp/(tp+fn) if tp+fn else None,
            'expected_distinct_moments':len(expected_moments),
            'detected_expected_moments':len(expected_moments & detected_moments),
            'missed_distinct_moments':len(expected_moments-detected_moments),
            'false_alert_distinct_moments':len(false_alerts),
            'simulated_minutes':minutes,'false_alerts_per_simulated_minute':len(false_alerts)/minutes if minutes else None,
            'candidate_case_coverage':sum(any(c['detected_pass_ids'] for c in r['checks']) for r in rows)/len(rows) if rows else None}


def build_report(rows, mode):
    timings = [t for r in rows for t in r.pop('metric_timings_ms')]
    workflows = [w for r in rows for w in r['workflows']]
    usages = [w['usage'] for w in workflows if w.get('usage')]
    input_baseline = json.loads((ROOT/'evals/synthetic-v2/input-baseline.json').read_text())
    input_checks = [all(r[key] == input_baseline['cases'][r['case_id']][key] for key in ('observations_sha256','reference_sha256')) for r in rows]
    assert all(input_checks), 'regression_inputs_changed_review_required'
    report = {
        'input_integrity': {'source_commit':input_baseline['source_commit'],'cases_checked':len(input_checks),'unchanged':all(input_checks)},
        'generator_version':VERSION,'generated_at':datetime.now(timezone.utc).isoformat(),
        'mode':mode,'metric_version':'pressure-escape-v1','scope':'Pre-model live-candidate checkpoints; workflow abstentions/fallbacks are separate. Producer approval is checked separately by API integration tests.',
        'summary':summarize(rows),
        'by_split':{s:summarize([r for r in rows if r['split']==s]) for s in sorted({r['split'] for r in rows})},
        'by_family':{f:summarize([r for r in rows if r['family']==f]) for f in sorted({r['family'] for r in rows})},
        'metric_latency_ms':{'median':round(statistics.median(timings),3),'maximum':round(max(timings),3),
                             'scope':'Warm-process metric computation only; excludes generation, validation, workflows, replay, network and human approval.'},
        'workflows':{'attempted':sum(w['status']!='not_run_budget' for w in workflows),
                     'produced':sum(w['status']=='produced' for w in workflows),
                     'abstained':sum(w['status']=='abstained' for w in workflows),
                     'skipped_budget':sum(w['status']=='not_run_budget' for w in workflows),
                     'modes':dict(Counter(w['mode'] for w in workflows if 'mode' in w)),
                     'variants_checked':sum(w.get('variants_checked',0) for w in workflows)},
        'model_usage':{'calls':sum(u['calls'] for u in usages),
                       'input_tokens':sum(u['input_tokens'] for u in usages),
                       'output_tokens':sum(u['output_tokens'] for u in usages),
                       'total_tokens':sum(u['total_tokens'] for u in usages),
                       'usage_complete':all(u['usage_complete'] for u in usages) and not (mode=='foundry' and any(w['status']!='produced' for w in workflows)),
                       'calls_are_lower_bound':mode=='foundry' and any(w['status']!='produced' for w in workflows),
                       'cost_usd':0 if mode=='template' else None,
                       'cost_note':'Offline mode makes no model requests.' if mode=='template' else 'Tokens are actual reported usage; monetary cost is not estimated here.'},
        'limitations':[
            'Six scripted parent configurations, with correlated scenario/fault variants; not independent real matches.',
            'References are authored engineering expectations; football expert review and audience usefulness studies are pending.',
            'Checkpoint precision/recall counts predefined time decisions, not continuous full-match detection accuracy.',
            'Distinct false alerts are deduplicated by case/pass; simulated minutes include scripted quiet time.',
            'Candidate coverage includes false alerts; quiet cases combine deliberate negatives and missing-evidence abstentions.',
            'Variant checks cover schema, evidence references, numeric consistency and hash integrity; free-form semantic correctness is not established.',
            'Local execution does not exercise Azure transport, durable production load, web presentation or human approval latency.',
            'Held-out parents were fixed before the first run; after inspection they are regression data. Fresh final parents are required after tuning.',
        ],
        'rows':rows,
    }
    return report


def markdown(report):
    s = report['summary']
    lines = ['# Expanded synthetic evaluation', '',
             f"Generator {VERSION}; mode `{report['mode']}`; metric `{report['metric_version']}`.", '',
             f"**{s['cases_passed']}/{s['cases']} cases passed every checkpoint; {s['cases_failed']} cases have mismatches.** "
             f"{s['checks_passed']}/{s['checks']} checkpoint decisions matched their authored expectations.", '',
             'A passing case means every availability, candidate and expiry checkpoint matched. All exported original and corrected feeds passed structural and physical validation.', '',
             '| Split | Parents | Cases passed / total | Checkpoint TP / FP / FN | Expected moments detected / total |',
             '|---|---:|---:|---:|---:|']
    for split, v in report['by_split'].items():
        lines.append(f"| {split} | {v['parents']} | {v['cases_passed']} / {v['cases']} | {v['checkpoint_true_positive']} / {v['checkpoint_false_positive']} / {v['checkpoint_false_negative']} | {v['detected_expected_moments']} / {v['expected_distinct_moments']} |")
    lines += ['', '## Failures to prioritize', '', '| Family | Cases with mismatch |', '|---|---:|']
    for family,v in report['by_family'].items():
        if v['cases_failed']: lines.append(f"| {family} | {v['cases_failed']} / {v['cases']} |")
    if not any(v['cases_failed'] for v in report['by_family'].values()):
        lines.append('| No checkpoint mismatches | 0 |')
    lines += ['', 'Raw clocks, expected/detected IDs and metric operands are in `results.json`. Failures are reported even when they reflect a documented MVP scope limit. The first run caught six false alerts from rounding distance before the gate; eligibility now uses the original measurement. No threshold or reference label was changed. The original first-pass restriction has been resolved: all authored later-pass checkpoints are now evaluated. Observation and reference hashes remain identical to commit b9bc99f, as checked against input-baseline.json. These inspected parents are regression data; final blind evaluation requires new parents.', '',
              '## Family coverage', '', '| Family | Passed / total |', '|---|---:|']
    for family,v in report['by_family'].items(): lines.append(f"| {family} | {v['cases_passed']} / {v['cases']} |")
    lines += ['', '## Measurement scope', '',
              f"Distinct expected moments: {s['detected_expected_moments']}/{s['expected_distinct_moments']} detected; "
              f"distinct false alerts: {s['false_alert_distinct_moments']} across {s['simulated_minutes']:.1f} simulated minutes "
              f"({s['false_alerts_per_simulated_minute']:.4f}/minute). These are correlated scripted examples.", '',
              f"Median metric computation: {report['metric_latency_ms']['median']} ms; maximum {report['metric_latency_ms']['maximum']} ms. {report['metric_latency_ms']['scope']}", '',
              f"Workflows attempted: {report['workflows']['attempted']}; packages produced: {report['workflows']['produced']}; "
              f"variants structurally/numerically checked: {report['workflows']['variants_checked']}. "
              f"Actual model calls: {report['model_usage']['calls']}; reported tokens: {report['model_usage']['total_tokens']}.", '',
              'The default run uses deterministic templates. AI evaluation is a separately requested, budgeted run and must report actual model mode, fallbacks, abstentions and usage. Factual templates passing does not establish model semantic quality.', '',
              '## Limitations', '']
    lines += ['- '+x for x in report['limitations']]
    lines += ['', 'Reproduce with `make synthetic-evaluate`. Use `--strict` to return a failing exit code on any authored mismatch. `--check-baseline` fails on any changed case/check outcome, including changed detections when capabilities improve.', '']
    return '\n'.join(lines)


def signature(report):
    return {'generator_version':report['generator_version'],
            'cases':{r['case_id']:{'observations_sha256':r['observations_sha256'],
                                   'reference_sha256':r['reference_sha256'],
                                   'outcomes':[{'at_ms':c['at_ms'],'expected':c['expected_pass_ids'],
                                                'detected':c['detected_pass_ids']} for c in r['checks']]}
                     for r in report['rows']}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',action='append',dest='case_ids')
    parser.add_argument('--split',choices=['development','validation','held_out'])
    parser.add_argument('--output',type=Path)
    parser.add_argument('--mode',choices=['template','foundry'],default='template')
    parser.add_argument('--max-investigations',type=int,default=4)
    parser.add_argument('--strict',action='store_true')
    parser.add_argument('--check-baseline',action='store_true')
    parser.add_argument('--write-baseline',action='store_true',help='Explicitly freeze/review a new regression baseline, including known failures.')
    args = parser.parse_args()
    selected = [get_case(c) for c in args.case_ids] if args.case_ids else cases(args.split)
    workflow_runner = run_workflow
    budget = None
    if args.mode=='foundry':
        if not args.case_ids or len(selected)>6 or not 1<=args.max_investigations<=6:
            parser.error('Foundry requires 1–6 explicit --case selections and --max-investigations between 1 and 6.')
        if not os.getenv('AZURE_OPENAI_ENDPOINT') or not os.getenv('FOUNDRY_MODEL_DEPLOYMENT'):
            parser.error('Set AZURE_OPENAI_ENDPOINT and FOUNDRY_MODEL_DEPLOYMENT for the existing deployment.')
        from engine.foundry_workflow import run_foundry_workflow
        workflow_runner = run_foundry_workflow
        budget = {'remaining':args.max_investigations}
    if (args.check_baseline or args.write_baseline) and (args.case_ids or args.split or args.mode!='template'):
        parser.error('Baseline checks require the full offline template suite.')
    rows = []
    for i,case in enumerate(selected,1):
        rows.append(evaluate_case(case,workflow_runner=workflow_runner,budget=budget))
        if i%28==0 or args.mode=='foundry':
            print(f'Validated and evaluated {i}/{len(selected)} cases',flush=True)
    report = build_report(rows,args.mode)
    out = args.output or (ROOT/'evals/synthetic-v2' if args.mode=='template' and not args.case_ids and not args.split else ROOT/'.run/synthetic-evaluation')
    out.mkdir(parents=True,exist_ok=True)
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'REPORT.md').write_text(markdown(report))
    baseline = ROOT/'evals/synthetic-v2/baseline.json'
    if args.write_baseline:
        baseline.parent.mkdir(parents=True,exist_ok=True)
        baseline.write_text(json.dumps(signature(report),indent=2)+'\n')
    changed = False
    if args.check_baseline:
        changed = not baseline.exists() or json.loads(baseline.read_text())!=signature(report)
    print(json.dumps({'summary':report['summary'],'workflow':report['workflows'],'model_usage':report['model_usage'],
                      'baseline_changed':changed,'report':str(out/'REPORT.md')},indent=2))
    if changed: raise SystemExit('Synthetic regression outcomes changed; review results and baseline explicitly.')
    if args.strict and report['summary']['cases_failed']: raise SystemExit(1)


if __name__=='__main__': main()
