"""Independent authored reference checks against exported development sources.

No scene/generator import. Keys stay offline; actual facts use production paths.
This is deterministic regression/evidence checking, not an agent comparison or
human football usefulness evaluation.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from engine.core import available, pass_metrics
from engine.event_metrics import event_metrics, possession_window
from engine.match_state import match_state
from engine.pressure import pressure_metrics
from simulator.episode_validation import validate

ROOT=Path(__file__).resolve().parents[1]


def load(case_id, faults=False):
    manifest=json.loads((ROOT/'data/provenance/episodes-v1.json').read_text())
    row=next(r for r in manifest['cases'] if r['case_id']==case_id and r['delivery_faults']==faults)
    folder=ROOT/'data/runtime'/row['match_id']
    metadata=(folder/'match.json').read_bytes();encoded=(folder/'stream.jsonl.gz').read_bytes()
    if hashlib.sha256(metadata).hexdigest()!=row['metadata_sha256'] or hashlib.sha256(encoded).hexdigest()!=row['compressed_sha256']:
        raise ValueError('export_hash_mismatch')
    return json.loads(metadata),[json.loads(r) for r in gzip.decompress(encoded).splitlines()]


def actual(check,metadata,rows):
    cutoff,kind=check['at'],check['kind']
    if kind=='score':return match_state(metadata,rows,cutoff)['score']
    if kind=='controller':
        frames=[r for r in available(rows,cutoff) if r['kind']=='tracking_frame']
        return frames[-1]['payload']['controlling_player_id']
    if kind in ('eligible_passes','pass_absent','pass_fact'):
        passes=pass_metrics(rows,cutoff,metadata)
        if kind=='eligible_passes':return sorted(p['pass_id'] for p in passes if p['eligible'])
        if kind=='pass_absent':return not any(p['pass_id']==check['subject'] for p in passes)
        p=next(p for p in passes if p['pass_id']==check['subject'])
        start,end=p['pass_start'],p['pass_end']
        return {'forward_m':round(end['x_m']-start['x_m'],4),
                'progression_m':p['progression_m'],'receiver_id':p['receiver_id']}
    if kind=='pressure_ids':return sorted(p['subject_id'] for p in pressure_metrics(metadata,rows,cutoff))
    if kind=='possession':
        w=possession_window(metadata,rows,cutoff,cutoff)
        return {**w,'blue_ms':w['team_ms']['blue'],'has_percentages':w['percentages'] is not None}
    family=kind.removesuffix('_absent')
    metrics=[m for m in event_metrics(metadata,rows,cutoff) if m['family']==family and m['subject_id']==check['subject']]
    if kind.endswith('_absent'):return not metrics
    if not metrics:return None
    m=metrics[0]
    return {**m['facts'],**m['participants']}


def evaluate():
    reference=json.loads((ROOT/'data/evaluation-only/episodes-v1.json').read_text())
    cache={};results=[]
    for check in reference['checks']:
        case=check['case']
        if case not in cache:cache[case]=load(case)
        try:
            value=actual(check,*cache[case]);expected=check['expected']
            value={key:value.get(key) for key in expected} if isinstance(expected,dict) and isinstance(value,dict) else value
            results.append({**check,'actual':value,'passed':value==expected})
        except Exception as exc:
            results.append({**check,'passed':False,'error':str(exc)})
    source=[]
    for number in range(1,7):
        for paired in ('a','b'):
            case=f'd{number:02}-{paired}'
            for faults in (False,True):
                metadata,rows=load(case,faults)
                report=validate(metadata,rows)
                source.append({'case':case,'delivery_faults':faults,**report})
    family_cases={family:[] for family in ('pass','pressure','shot','goal','recovery','possession')}
    for case,(metadata,rows) in cache.items():
        present={m['family'] for m in event_metrics(metadata,rows,90000)}
        if any(m['eligible'] for m in pass_metrics(rows,90000,metadata)):present.add('pass')
        if pressure_metrics(metadata,rows,90000):present.add('pressure')
        for family in present:family_cases[family].append(case)
    return {'source_profile':'constrained-episodes-v1','model_calls':0,
            'reference_sha256':hashlib.sha256((ROOT/'data/evaluation-only/episodes-v1.json').read_bytes()).hexdigest(),
            'structural_parents':6,'specification_cases':12,'source_views':24,
            'held_out_parents':0,'human_review':'pending',
            'reference_checkpoints':len(results),'reference_passed':sum(r['passed'] for r in results),
            'source_views_passed':sum(r['passed'] for r in source),
            'family_cases':family_cases,
            'family_coverage_cutoff_ms':90000,
            'references':results,'source_validation':source}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'evals/synthetic-vnext/results.json')
    args=parser.parse_args();report=evaluate()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(f"Development reference checks: {report['reference_passed']}/{report['reference_checkpoints']}; source views: {report['source_views_passed']}/24; 6 parents; zero model calls.")
    if report['reference_passed']!=report['reference_checkpoints'] or report['source_views_passed']!=24:raise SystemExit(1)
