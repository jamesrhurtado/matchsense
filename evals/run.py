"""Offline evaluation: parent geometry configurations are split, never tracking rows."""
import json
import statistics
from pathlib import Path
from time import perf_counter
from engine.core import metric
from engine.workflow import EvidenceTools,run_workflow
from simulator.generate import generate
from simulator.validate import validate

# Frozen before this report's first run. Families share a parent geometry and split.
PARENTS={
 'development':[(35,32,19,False),(34,30,18,True)],
 'validation':[(32,26,20,False),(39,34,21,True)],
 'held_out':[(30,22,23,False),(40,42,17,True),(38,24,24,True),(31,40,22,False)]
}

def evaluate():
    rows=[];timings=[];n=0
    for split,parents in PARENTS.items():
        for parent,(x,y,d,reverse) in enumerate(parents):
            for j,family in enumerate(['escape','ordinary','failed']):
                n+=1;seed=7000+n
                meta,msgs=generate(100+n,seed,family,reverse,{'release_x':x,'center_y':y,'pass_distance_m':d})
                validate(meta,msgs)
                # Independent reference geometry: press two opponents within radius 6 at release;
                # all three x offsets 2/3/5 lie between the supplied kick and observed receive.
                # Possession and endpoint values are checked from realized observations, not detector output.
                start=next(m for m in msgs if m['kind']=='event' and m['payload']['type']=='pass_started')
                end=next(m for m in msgs if m['kind']=='event' and m['payload']['type']=='pass_resolved')
                start_frame=next(m['payload'] for m in msgs if m['kind']=='tracking_frame' and m['timeline_ms']==start['timeline_ms'])
                passer=next(p for p in start_frame['players'] if p['player_id']==start['payload']['player_id'])
                nearby=[p for p in start_frame['players'] if p['team_id']!=start['payload']['team_id'] and (p['x_m']-passer['x_m'])**2+(p['y_m']-passer['y_m'])**2<=36]
                forward=abs(end['payload']['details']['end_position']['x_m']-start['payload']['details']['start_position']['x_m'])>10
                reference=end['payload']['details']['outcome']=='received' and len(nearby)>0 and forward
                expected=family=='escape'
                assert reference==expected,'realized_reference_disagrees_with_scenario_intent'
                then=perf_counter();m=metric(msgs,23000,meta);p=run_workflow(EvidenceTools(meta,msgs,23000));timings.append((perf_counter()-then)*1000)
                predicted=bool(m and m['eligible']);naive=end['payload']['details']['outcome']=='received' and forward
                rows.append({'split':split,'parent_configuration':f'{split}-{parent+1}','family':family,'seed':seed,'expected':reference,'detected':predicted,'naive_forward_pass_baseline':naive,'variants_validated':len(p['variants']) if p else 0})
    summary={}
    for split in PARENTS:
        group=[r for r in rows if r['split']==split]
        tp=sum(r['detected'] and r['expected'] for r in group);fp=sum(r['detected'] and not r['expected'] for r in group);fn=sum(not r['detected'] and r['expected'] for r in group)
        summary[split]={'segments':len(group),'parent_configurations':len(PARENTS[split]),'true_positive':tp,'false_positive':fp,'false_negative':fn,'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None,'alert_coverage':sum(r['detected'] for r in group)/len(group),'false_alerts_per_simulated_minute':fp/len(group),'naive_false_positive':sum(r['naive_forward_pass_baseline'] and not r['expected'] for r in group)}
    report={'mode':'deterministic local templates','metric_version':'pressure-escape-v1','scenario_matching_tolerance_ms':100,'latency_scope':'metric calculation plus local template workflow, one warm process, excludes replay/network/human time','median_processing_ms':round(statistics.median(timings),3),'max_processing_ms':round(max(timings),3),'model_calls':0,'model_cost_usd':0,'summary':summary,'rows':rows,'limitations':['Small, constructed synthetic test, not a measure of professional football accuracy.','Thresholds are heuristic. Every parent still uses the same simulator mechanics.','Model-backed workflow and fair single-agent comparison were not run.','Variant generation is restricted to deterministic approved phrases; no free-form semantic quality claim is made.','No human comprehension or editorial timing study was conducted.']}
    out=Path(__file__).with_name('results.json');out.write_text(json.dumps(report,indent=2)+'\n')
    lines=['# Local evaluation results','',f"Measured median processing: {report['median_processing_ms']} ms; maximum: {report['max_processing_ms']} ms. Scope: {report['latency_scope']}.",'','| Split | Parent configurations | Segments | TP / FP / FN | Precision | Recall | Alert coverage |','|---|---:|---:|---|---:|---:|---:|']
    for split,s in summary.items():lines.append(f"| {split} | {s['parent_configurations']} | {s['segments']} | {s['true_positive']} / {s['false_positive']} / {s['false_negative']} | {s['precision']:.0%} | {s['recall']:.0%} | {s['alert_coverage']:.0%} |")
    lines+=['','Each segment lasts one simulated minute. A detected moment must match the reference pass; its first confirmation time is 22,200 ms (100 ms tolerance). Negative families are ordinary unpressured passes and intercepted passes.','', 'The simple baseline alerts on every completed forward pass. It produces '+str(summary['held_out']['naive_false_positive'])+' false alerts on the held-out segments. This baseline is disclosed as a narrow deterministic comparison, not a single-agent model baseline.','', '## Limitations','']+['- '+x for x in report['limitations']]+['','Reproduce with `python -m evals.run`. Labels/configurations are offline-only; runtime code does not import this module. Thresholds/configurations were fixed before this report run; further tuning requires a new held-out split.','']
    Path(__file__).with_name('REPORT.md').write_text('\n'.join(lines))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':evaluate()
