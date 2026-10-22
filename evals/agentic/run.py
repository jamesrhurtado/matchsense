"""Bounded, explicit evaluation runner. Default command makes zero model calls."""
from __future__ import annotations
import argparse
import csv
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


def agent_adapter(strategy):
    async def run(request, policy):
        from engine.structured_workflow import run_structured_workflow
        from engine.foundry_workflow import Limits
        from engine.workflow import EvidenceTools
        outcomes = []
        error = None
        try:
            package = await asyncio.to_thread(run_structured_workflow, EvidenceTools(request.metadata,request.observations,request.cutoff_ms,request.pass_id),
                                              strategy=strategy, outcome_callback=outcomes.append,
                                              **({'evaluation_only':True} if strategy=='director_only' else {}),
                                              limits=Limits(deadline_s=15, model_calls=policy.max_calls,token_budget=32000))
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


def select_adapters(selected, live):
    arms = [a.strip() for a in selected.split(',')] if selected else (['T3','S3','M3'] if live else ['T3'])
    if not arms or len(arms)!=len(set(arms)) or set(arms)-{'T3','S3','M3','D3'}:
        raise ValueError('Arms must be unique choices from T3,S3,M3,D3')
    if not live and set(arms)-{'T3'}:
        raise ValueError('Model arms require explicit --live configuration')
    available = {'T3':template_adapter, 'S3':agent_adapter('single'),
                 'M3':agent_adapter('collaborative'),'D3':agent_adapter('director_only')}
    return {arm:available[arm] for arm in arms}


def report(rows, live):
    summary=summarize(rows)
    lines = ['# Agent evaluation run','',f"Mode: {'explicit model discovery' if live else 'offline template smoke (zero model calls)' }.",
             '',f'Scheduled outcomes: {len(rows)}. Human grading pending.', '',
             '| Arm | Scheduled | Packages | Missing expected | Rejection candidates | Repairs returning packages | Known calls | Median observed ms |',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    for arm,s in summary.items():
        lines.append(f"| {arm} | {s['scheduled_outcomes']} | {s['packages']} | {s['missing_expected_opportunities']} | {s['false_rejection_candidates']} | {s['repair_returned_packages']} | {s['known_usage_subtotals']['model_calls']} | {s['observed_elapsed_ms']['median']} |")
    lines += ['', 'All scheduled jobs, including failures, timeouts and budget skips, remain in opportunity denominators.',
              'Known usage is a subtotal when any usage is unknown; manifest reservations remain the billing bound.',
              'A repair returning a package is observed behavior, not proof that the repair was correct. Rejection candidates are not confirmed errors.',
              'Contract validation and handwritten context references are mechanical checks, not independent football accuracy or usefulness grades.',
              'T3 is run once per case; model trials are repeated observations, not additional independent cases.',
              'D3 removes review only inside this evaluation; production approval and validation stay required.',
              'These developer-visible challenge compositions share existing trajectory backbones and current-play recordings.',
              'They are not a blind final set or independent evidence of real-match accuracy.',
              'No agent superiority, usefulness, human acceptance, or Grand Prize score is established.',
              'Unknown usage retains its full reservation. Provider cancellation does not guarantee zero billing.',
              'Use rating-instrument.csv with rating-packets.json; preserve blank ratings until real reviewers complete them.',
              'Results and rating-mapping-private.json identify arms and must not be supplied to blinded raters.']
    return '\n'.join(lines)+'\n'


def write_rating_materials(output, rows, seed):
    # IDs are allocated after a fresh shuffle, unrelated to scheduling order.
    order=list(enumerate(rows))
    random.Random(seed+1).shuffle(order)
    blinded=[]
    mapping={}
    for i, (source_index,row) in enumerate(order,1):
        rating_id=f'R{i:03d}'
        package=row.get('package')
        # Rendered content and evidence only: no mode, trace, plan or provider labels.
        presentation=None if not package else {key:package[key] for key in ('title','claims','variants','eligible_from_ms','expires_at_ms') if key in package}
        if presentation:
            presentation['evidence']={key:package.get('metrics',{}).get(key) for key in ('passer_id','receiver_id','team_id','forward_pass_m','reception_zone','retention_confirmed_at_ms','context')}
        blinded.append({'rating_id':rating_id,'case_id':row['case_id'],'presentation':presentation,
                        'status':'output_available' if package else 'no_output'})
        mapping[rating_id]={'row_index':source_index,'case_id':row['case_id'],'arm':row['arm'],'trial':row['trial']}
    (output/'rating-packets.json').write_text(json.dumps(blinded,indent=2)+'\n')
    private=output/'rating-mapping-private.json'
    private.write_text(json.dumps(mapping,indent=2)+'\n')
    private.chmod(0o600)
    fields=['rating_id','case_id','rater_id','factual_correctness_1_5','editorial_usefulness_1_5',
            'clarity_1_5','comparison_scope_understood_yes_no','would_publish_yes_no',
            'withholding_appropriate_yes_no','preferred_angle','notes']
    with (output/'rating-instrument.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields)
        writer.writeheader()
        writer.writerows({'rating_id':packet['rating_id'],'case_id':packet['case_id']} for packet in blinded)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('.run/agentic'))
    parser.add_argument('--config',type=Path)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--arms',help='Comma-separated T3,S3,M3,D3; D3 is evaluator-only reviewer removal')
    parser.add_argument('--cases',help='Comma-separated exact case IDs; omitted means all discovery cases')
    parser.add_argument('--trials',type=int,help='Override model trials; T3 remains once per case')
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
    adapters = select_adapters(args.arms,args.live)
    from .context_cases import context_cases
    cases = select_cases(discovery_cases()+context_cases(),args.cases)
    revision = subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
    manifest = {'schema_version':'1.0.0','commit':revision,'started_at':datetime.now(timezone.utc).isoformat(),
                'mode':'live' if args.live else 'offline','split':'developer-visible discovery',
                'final_split_status':'pending independent QA authorship and sealing',
                'arms':list(adapters),'configuration':config,'implementation':implementation_identifiers(),
                'source_file_sha256':source_fingerprints(),
                'working_tree_diff_sha256':fingerprint(subprocess.run(['git','diff','HEAD'],capture_output=True,text=True,check=True).stdout),
                'workflow_reservation':asdict(WorkflowBudget()),
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
    write_rating_materials(args.output,rows,config.get('order_seed',1041))
    print(f"Recorded {len(rows)} outcomes at {args.output}; human grading pending.")


if __name__=='__main__':
    main()
