"""Bounded, explicit evaluation runner. Default command makes zero model calls."""
from __future__ import annotations
import argparse
from copy import deepcopy
import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
import os
import hashlib
from pathlib import Path
import random
import subprocess
import time

from .dataset import discovery_cases, fingerprint
from .checks import check_result, summarize

OUTCOMES = {'ai_composed', 'template', 'fallback', 'abstention', 'rejected', 'timeout', 'failure', 'stale', 'budget_exhausted'}


@dataclass(frozen=True)
class WorkflowBudget:
    max_calls: int = 6
    input_tokens: int = 32000
    output_tokens: int = 6600


class BudgetLedger:
    """Reserve before dispatch; unknown usage keeps the entire reservation."""
    def __init__(self, config):
        self.config = config
        self.calls = self.input_tokens = self.output_tokens = 0
        self.estimated_cost = 0.0
        self.unknown_workflows = 0

    def cost(self, inputs, outputs):
        return (inputs*self.config['input_per_million']+outputs*self.config['output_per_million'])/1_000_000

    def reserve(self, policy):
        price = self.cost(policy.input_tokens, policy.output_tokens)
        proposed = (self.calls+policy.max_calls, self.input_tokens+policy.input_tokens,
                    self.output_tokens+policy.output_tokens, self.estimated_cost+price)
        limits = ('max_model_calls', 'max_input_tokens', 'max_output_tokens', 'max_estimated_cost')
        if any(value > self.config[key] for value,key in zip(proposed, limits)):
            return False
        self.calls,self.input_tokens,self.output_tokens,self.estimated_cost = proposed
        return True

    def reconcile(self, policy, usage):
        if not isinstance(usage,dict):
            self.unknown_workflows += 1
            return 'invalid_reserved'
        keys = ('model_calls', 'input_tokens', 'output_tokens')
        if any(usage.get(key) is None for key in keys):
            self.unknown_workflows += 1
            return 'unknown_reserved'
        actual = tuple(usage[key] for key in keys)
        if any(type(value) is not int or value < 0 for value in actual):
            self.unknown_workflows += 1
            return 'invalid_reserved'
        reserved = (policy.max_calls, policy.input_tokens, policy.output_tokens)
        self.calls += actual[0]-reserved[0]
        self.input_tokens += actual[1]-reserved[1]
        self.output_tokens += actual[2]-reserved[2]
        self.estimated_cost += self.cost(actual[1],actual[2])-self.cost(reserved[1],reserved[2])
        return 'overrun' if any(a>b for a,b in zip(actual,reserved)) else 'complete'


async def template_adapter(request, policy):
    from engine.editorial_narrative import build_editorial_package as build_structured_package
    from engine.workflow import EvidenceTools
    package = build_structured_package(EvidenceTools(request.metadata,request.observations,request.cutoff_ms,request.pass_id))
    return {'outcome':'template' if package else 'abstention','package':package,
            'usage':{'model_calls':0,'input_tokens':0,'output_tokens':0}}


def agent_adapter(strategy, seeded_plans=None):
    seeded_plans = seeded_plans or {}
    async def run(request, policy):
        from engine.structured_workflow import run_structured_workflow
        from engine.foundry_workflow import Limits
        from engine.workflow import EvidenceTools
        outcomes = []
        error = None
        seeded_plan = seeded_plans.get(fingerprint(asdict(request)))
        try:
            options = {'evaluation_only': True} if strategy == 'director_only' or seeded_plan else {}
            if seeded_plan:
                options['seeded_initial_plan'] = seeded_plan
            package = await asyncio.to_thread(
                run_structured_workflow,
                EvidenceTools(request.metadata, request.observations, request.cutoff_ms, request.pass_id),
                strategy=strategy, outcome_callback=outcomes.append,
                limits=Limits(deadline_s=15, model_calls=policy.max_calls, token_budget=32000),
                **options)
        except Exception as exc:
            package, error = None, type(exc).__name__
        terminal = outcomes[-1] if outcomes else {}
        state = terminal.get('state','failure')
        if error or (state=='produced' and package is None):
            state = 'failure'
        mapping = {'produced':'ai_composed','failed':'failure','approved':'ai_composed','accepted':'ai_composed','ai_composed':'ai_composed',
                   'fallback':'fallback','abstained':'abstention','abstention':'abstention'}
        observed = terminal.get('usage',{})
        usage = {'model_calls':observed.get('calls'),
                 'input_tokens':observed.get('input_tokens') if observed.get('usage_complete') else None,
                 'output_tokens':observed.get('output_tokens') if observed.get('usage_complete') else None}
        return {'outcome':mapping.get(state,state if state in OUTCOMES else 'failure'),
                'package':package,'usage':usage,'trace':terminal.get('trace',[]),'reason':error or terminal.get('reason')}
    return run


def validate_live(config):
    required = ('max_model_calls','max_input_tokens','max_output_tokens','max_estimated_cost',
                'input_per_million','output_per_million','rate_source','rate_date','currency',
                'deadline_utc','model','model_version','deployment','api_version','prompt_version','tool_version','renderer_version','schema_version')
    missing = [key for key in required if not config.get(key)]
    if missing:
        raise ValueError('Live run requires explicit configuration: '+', '.join(missing))
    for key in ('max_model_calls','max_input_tokens','max_output_tokens','max_estimated_cost','input_per_million','output_per_million'):
        if type(config[key]) not in (int,float) or not math.isfinite(config[key]) or config[key]<=0:
            raise ValueError(f'{key} must be positive')
    deadline = datetime.fromisoformat(config['deadline_utc'].replace('Z','+00:00'))
    if deadline.tzinfo is None or deadline <= datetime.now(timezone.utc):
        raise ValueError('deadline_utc must be a future timezone-aware timestamp')


def validate_runtime_identifiers(config, environ):
    expected=implementation_identifiers()
    expected.pop('context_version')
    expected.update(deployment=environ.get('FOUNDRY_MODEL_DEPLOYMENT'),
                    api_version=environ.get('AZURE_OPENAI_API_VERSION','2024-10-21'),
                    model=environ.get('FOUNDRY_MODEL_NAME'),model_version=environ.get('FOUNDRY_MODEL_VERSION'))
    mismatch=[key for key,value in expected.items() if not value or config.get(key)!=value]
    if mismatch:
        raise ValueError('Live manifest does not match configured implementation/provider: '+', '.join(mismatch))


def source_fingerprints():
    root=Path(__file__).resolve().parents[2]
    patterns=['engine/*.py','services/api/*.py','evals/agentic/*.py','simulator/*.py',
              'apps/web/components/*.tsx','apps/web/hooks/*.ts','apps/web/lib/api.ts']
    files=sorted({p for pattern in patterns for p in root.glob(pattern)})
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


async def evaluate(cases, adapters, config, live=False):
    if type(config.get('trials',1)) is not int or config.get('trials',1)<1:
        raise ValueError('trials must be a positive integer')
    policy = WorkflowBudget()
    if live:
        validate_live(config)
    ledger = BudgetLedger(config) if live else None
    rows = []
    jobs = [(case,arm,trial) for case in cases for arm in adapters for trial in range(1 if arm in {'T2','T3'} else config.get('trials',1))]
    random.Random(config.get('order_seed',1041)).shuffle(jobs)
    stopped = False
    for case,arm,trial in jobs:
        start = time.monotonic()
        row = {'case_id':case.case_id,'lineage':case.lineage,'arm':arm,'trial':trial,
               'input_hash':fingerprint(asdict(case.runtime)), 'reference_hash':fingerprint(case.reference),
               'expected_story':case.reference['expected_story'], 'human_rating':None,
               'usage':{'model_calls':None,'input_tokens':None,'output_tokens':None}}
        if case.reference.get('seeded_fault'):
            row['fault_injection'] = deepcopy(case.reference['seeded_fault'])
        is_model = arm not in {'T2','T3'}
        expired = live and datetime.now(timezone.utc)>=datetime.fromisoformat(config['deadline_utc'].replace('Z','+00:00'))
        reserved = False
        if is_model and live:
            reserved = not stopped and not expired and ledger.reserve(policy)
            if not reserved:
                row.update(outcome='budget_exhausted',reason='Scheduling stopped: budget or deadline.',accounting='not_dispatched',
                           usage={'model_calls':0,'input_tokens':0,'output_tokens':0})
        if not (is_model and live and not reserved):
            try:
                remaining = 120.0
                if live:
                    remaining = max(.001,min(remaining,(datetime.fromisoformat(config['deadline_utc'].replace('Z','+00:00'))-datetime.now(timezone.utc)).total_seconds()))
                response = await asyncio.wait_for(adapters[arm](deepcopy(case.runtime),policy),timeout=remaining)
                if response.get('outcome') not in OUTCOMES:
                    raise ValueError('Adapter returned an invalid terminal outcome')
                row.update(response)
            except asyncio.TimeoutError:
                row.update(outcome='timeout',reason='Workflow deadline elapsed; dispatched consumption remains reserved.')
            except Exception as error:
                # No exception text: provider errors may contain secrets/URLs.
                row.update(outcome='failure',reason=type(error).__name__)
            if live and reserved:
                row['accounting'] = ledger.reconcile(policy,row['usage'])
                stopped = stopped or row['accounting'] in ('overrun','invalid_reserved')
            else:
                row['accounting'] = 'offline' if not live else 'non_model'
        row['elapsed_ms'] = round((time.monotonic()-start)*1000,3)
        row['assessment'] = check_result(case,row)
        rows.append(row)
    return rows, ledger


def implementation_identifiers():
    from engine.editorial_narrative import RENDERER_VERSION, SCHEMA_VERSION
    from engine.structured_workflow import PROMPT_VERSION
    return {'schema_version':SCHEMA_VERSION, 'renderer_version':RENDERER_VERSION,
            'prompt_version':PROMPT_VERSION, 'tool_version':'evidence-tools-v3',
            'context_version':'recent-completed-three-v1'}


def select_cases(cases, selected):
    if not selected:
        return cases
    identifiers = [c.strip() for c in selected.split(',')]
    unknown = set(identifiers)-{case.case_id for case in cases}
    if unknown or len(set(identifiers)) != len(identifiers):
        raise ValueError('Case IDs must be unique and known: '+', '.join(sorted(unknown)))
    return [case for case in cases if case.case_id in identifiers]


def select_adapters(selected, live, seeded_plans=None):
    arms = [a.strip() for a in selected.split(',')] if selected else (['T3','S3','M3'] if live else ['T3'])
    if not arms or len(arms)!=len(set(arms)) or set(arms)-{'T3','S3','M3','D3'}:
        raise ValueError('Arms must be unique choices from T3,S3,M3,D3')
    if not live and set(arms)-{'T3'}:
        raise ValueError('Model arms require explicit --live configuration')
    available = {'T3':template_adapter, 'S3':agent_adapter('single', seeded_plans),
                 'M3':agent_adapter('collaborative', seeded_plans),
                 'D3':agent_adapter('director_only')}
    return {arm:available[arm] for arm in arms}


def report(rows, live):
    summary=summarize(rows)
    fault_probe = any(r['assessment'].get('seeded_fault_handling') for r in rows)
    mode = ('explicit seeded fault-injection probe' if live and fault_probe else
            'explicit model discovery' if live else 'offline template smoke (zero model calls)')
    lines = ['# Agent evaluation run','',f'Mode: {mode}.',
             '',f'Scheduled outcomes: {len(rows)}. No human review was included in this run.', '',
             '| Arm | Scheduled | Packages | Missing expected | Rejection candidates | Repairs returning packages | Known calls | Median observed ms |',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    for arm,s in summary.items():
        if arm.startswith('paired_comparison_'):
            continue
        lines.append(f"| {arm} | {s['scheduled_outcomes']} | {s['packages']} | {s['missing_expected_opportunities']} | {s['false_rejection_candidates']} | {s['repair_returned_packages']} | {s['known_usage_subtotals']['model_calls']} | {s['observed_elapsed_ms']['median']} |")
    pair=summary['paired_comparison_M3_vs_S3']
    pairing=pair['mechanical_check_pairing']
    plans=pair['narrative_plan']
    check_label='All-control checks, including seeded policy rule' if fault_probe else 'Deterministic checks'
    lines += ['', '## Paired M3 versus S3', '',
              f"Matched case/trial pairs: {pair['matched_case_trial_pairs']}.",
              f"{check_label}: both passed {pairing['both_pass']}; M3-only pass {pairing['M3_pass_S3_fail']}; S3-only pass {pairing['S3_pass_M3_fail']}; neither passed {pairing['both_fail']}.",
              f"Where both produced a package, selected narrative plans matched in {plans['same']} pairs and differed in {plans['different']}.",
              f"M3 reviewer decisions: {json.dumps(pair['reviewer_decisions'], sort_keys=True)}.",
              '', pair['interpretation_limit'], '',
              'All scheduled jobs, including failures, timeouts and budget skips, remain in opportunity denominators.',
              'Known usage is a subtotal when any usage is unknown; manifest reservations remain the billing bound.',
              'A repair returning a package is observed behavior, not proof that the repair was correct. Rejection candidates are not confirmed errors.',
              'Deterministic checks cover runtime contract, allowed evidence, cutoff, actor attribution, team-versus-player retention, audience variant coverage and authored context references. They are not independent football accuracy or usefulness grades.',
              'T3 is run once per case; model trials are repeated observations, not additional independent cases.',
              'D3 removes review only inside this evaluation; production approval and validation stay required.',
              'These developer-visible challenge compositions share existing trajectory backbones and current-play recordings.',
              'They are not a blind final set or independent evidence of real-match accuracy.',
              'This benchmark can show contract-level reliability and observed selection differences; it cannot establish usefulness, human acceptance, broad accuracy, or agent superiority on its own.',
              'Unknown usage retains its full reservation. Provider cancellation does not guarantee zero billing.']
    if fault_probe:
        pair_probe = pair.get('seeded_fault_pairing') or {}
        lines += ['', '## Seeded editorial-policy challenge', '',
                  'Each S3/M3 pair received the same fixed initial Director plan: `historical_contrast` on a replay where the current provisional editorial policy did not recommend leading with history. The facts remain supported; this probe tests whether the review step corrects that policy-weak emphasis. The seeded plan replaces the first Director model response, so this isolates reviewer versus self-review behavior rather than measuring spontaneous Director selection.',
                  '', 'This policy is provisional and is not a football-quality ground truth. “Corrected” means the model-produced package no longer led with the seeded historical angle; a deterministic template fallback is counted separately.',
                  '', 'Ordinary package, evidence-source, cutoff, attribution, context and audience checks passed for all six trials in each arm. The seeded-policy check was the only failed deterministic control.', '',
                  '| Arm | Model correction | Safe template fallback | Seeded angle remained | No story |',
                  '|---|---:|---:|---:|---:|']
        for arm in ('M3','S3'):
            counts=summary.get(arm,{}).get('seeded_fault_handling',{})
            lines.append(f"| {arm} | {counts.get('corrected_by_model',0)} | {counts.get('safe_template_fallback',0)} | {counts.get('seeded_plan_left_in_ai_output',0)} | {counts.get('no_story_output',0)} |")
        if pair_probe:
            lines += ['', f"Matched case/trial probes: {pair_probe['matched_fault_trials']}; both corrected {pair_probe['both_corrected_by_model']}; M3-only corrected {pair_probe['M3_corrected_S3_did_not']}; S3-only corrected {pair_probe['S3_corrected_M3_did_not']}; neither corrected {pair_probe['neither_corrected_by_model']}.", '',
                      '| Case | Trial | M3 handling | M3 final angle | S3 handling | S3 final angle |',
                      '|---|---:|---|---|---|---|']
            paired = {}
            for row in rows:
                if row['arm'] in {'M3','S3'}:
                    paired.setdefault((row['case_id'],row['trial']),{})[row['arm']]=row
            for (case_id,trial),arms in sorted(paired.items()):
                if not {'M3','S3'} <= set(arms):
                    continue
                m3,s3=arms['M3'],arms['S3']
                m3_angle=(m3.get('package') or {}).get('narrative_plan',{}).get('angle','—')
                s3_angle=(s3.get('package') or {}).get('narrative_plan',{}).get('angle','—')
                lines.append(f"| {case_id} | {trial} | {m3['assessment']['seeded_fault_handling']} | {m3_angle} | {s3['assessment']['seeded_fault_handling']} | {s3_angle} |")
        lines += ['', 'This is controlled fault-injection evidence only. It does not establish that the model makes this error spontaneously, that viewers prefer the correction, or that the provisional policy is right.']
    return '\n'.join(lines)+'\n'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('.run/agentic'))
    parser.add_argument('--config',type=Path)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--arms',help='Comma-separated T3,S3,M3,D3; D3 is evaluator-only reviewer removal')
    parser.add_argument('--cases',help='Comma-separated exact case IDs; omitted means all discovery cases')
    parser.add_argument('--trials',type=int,help='Override model trials; T3 remains once per case')
    parser.add_argument('--fault-probe',action='store_true',help='Run only the matched evaluation-only seeded proposal probe for S3/M3')
    args = parser.parse_args()
    config = json.loads(args.config.read_text()) if args.config else {'trials':1,'order_seed':1041}
    if args.trials is not None:
        if args.trials < 1:
            raise ValueError('--trials must be positive')
        config['trials']=args.trials
    allowed_config = {'trials','order_seed','max_model_calls','max_input_tokens','max_output_tokens','max_estimated_cost', 'input_per_million','output_per_million','rate_source','rate_date','currency','deadline_utc','model','model_version','deployment','api_version','prompt_version','tool_version','renderer_version','schema_version'}
    if set(config)-allowed_config:
        raise ValueError('Unknown configuration fields; credentials belong only in the environment.')
    if args.live:
        validate_live(config)
        validate_runtime_identifiers(config,os.environ)
    seeded_plans = None
    if args.fault_probe:
        if not args.live:
            raise ValueError('--fault-probe requires --live')
        if args.cases:
            raise ValueError('--fault-probe uses its fixed authored cases; --cases is not accepted')
        if args.arms and set(a.strip() for a in args.arms.split(',')) != {'S3','M3'}:
            raise ValueError('--fault-probe compares exactly S3 and M3')
        from .fault_probes import fault_probe_cases
        cases = fault_probe_cases()
        seeded_plans = {fingerprint(asdict(case.runtime)):case.reference['seeded_fault']['initial_plan']
                        for case in cases}
        adapters = select_adapters('S3,M3',True,seeded_plans)
    else:
        adapters = select_adapters(args.arms,args.live)
        from .context_cases import context_cases
        cases = select_cases(discovery_cases()+context_cases(),args.cases)
    revision = subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
    manifest = {'schema_version':'1.0.0','commit':revision,'started_at':datetime.now(timezone.utc).isoformat(),
                'mode':'live' if args.live else 'offline','split':'developer-visible fault-injection probe' if args.fault_probe else 'developer-visible discovery',
                'final_split_status':'pending independent QA authorship and sealing',
                'arms':list(adapters),'configuration':config,'implementation':implementation_identifiers(),
                'source_file_sha256':source_fingerprints(),
                'working_tree_diff_sha256':fingerprint(subprocess.run(['git','diff','HEAD'],capture_output=True,text=True,check=True).stdout),
               'workflow_reservation':asdict(WorkflowBudget()),
               'deterministic_controls':['runtime_contract_valid','input_cutoff_respected','source_evidence_was_visible','reference_actor_attribution','team_retention_not_individual_control','audience_variant_matrix_complete','reference_context_status','reference_context_relation','reference_comparator_identity'],
               'paired_comparison':'M3 Director+Reviewer versus S3 strong single agent; same case input and workflow limits; deterministic invariant outcomes are not editorial-quality grades',
               'fault_probe_protocol':('Same fixed policy-weak initial angle is injected for both M3/S3; first Director model response replaced to isolate reviewer/self-review; current editorial policy is provisional.' if args.fault_probe else None),
                'scheduled_outcomes':len(cases)*sum(1 if arm in {'T2','T3'} else config.get('trials',1) for arm in adapters),
                'cases':[{'case_id':c.case_id,'lineage':c.lineage,'description':c.description,
                          'input_hash':fingerprint(asdict(c.runtime)),'reference_hash':fingerprint(c.reference)} for c in cases]}
    if args.dry_run:
        print(json.dumps(manifest,indent=2))
        return
    rows,ledger = asyncio.run(evaluate(cases,adapters,config,args.live))
    manifest['finished_at'] = datetime.now(timezone.utc).isoformat()
    if ledger:
        manifest['accounting'] = {key:getattr(ledger,key) for key in ('calls','input_tokens','output_tokens','estimated_cost','unknown_workflows')}
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (args.output/'results.jsonl').write_text(''.join(json.dumps(row,sort_keys=True)+'\n' for row in rows))
    (args.output/'REPORT.md').write_text(report(rows,args.live))
    (args.output/'summary.json').write_text(json.dumps(summarize(rows),indent=2)+'\n')
    print(f"Recorded {len(rows)} outcomes at {args.output}; no human ratings were collected.")


if __name__=='__main__':
    main()
