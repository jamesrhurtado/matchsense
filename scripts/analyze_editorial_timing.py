"""Read retained live-run evidence; never contact a model or change a gate.

Replay timestamps are compared only to replay timestamps. Wall-clock stage
durations are compared only within one recorded workflow attempt.
"""
import argparse
from collections import defaultdict
from datetime import datetime
import json
from pathlib import Path
from statistics import median


def milliseconds(start, end):
    if not start or not end:
        return None
    return round((datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()*1000, 3)


def analyze(data):
    families = defaultdict(list)
    for story_id, candidate in data['first_candidates'].items():
        outcome = next((o for o in data['outcomes'] if o.get('package_ref', {}) and
                        o['package_ref']['id'] == story_id and
                        o['package_ref']['revision'] == candidate['revision'] and
                        o['package_ref']['package_hash'] == candidate['package_hash']), {})
        timing = outcome.get('timing', {})
        families[candidate['family']].append({
            'story_id': story_id,
            'evidence_eligibility_to_ready_replay_ms': candidate['ready_replay_ms']-candidate['eligible_ms'],
            'review_remaining_s': candidate['review_remaining_s'],
            'worker_queue_wall_ms': milliseconds(timing.get('job_enqueued'), timing.get('job_started')),
            'workflow_wall_ms': milliseconds(timing.get('job_started'), timing.get('candidate_ready')),
        })
    stats = {}
    for family, rows in families.items():
        stats[family] = {'candidates': len(rows)}
        for key in ('evidence_eligibility_to_ready_replay_ms', 'review_remaining_s', 'worker_queue_wall_ms', 'workflow_wall_ms'):
            values = [r[key] for r in rows if r[key] is not None]
            stats[family][key] = {'known': len(values), 'median': median(values) if values else None,
                                  'min': min(values) if values else None, 'max': max(values) if values else None}
    return {'session_id': data['session_id'], 'operating_run_valid': data['operating_run_valid'],
            'expected': data['expected_count'], 'found': len(data['first_candidates']),
            'timely_ai_count': data['timely_ai_count'], 'original_gate_passed': data['gate_passed'],
            'missing': data['missing'], 'families': stats,
            'shortest_review_windows': sorted([r for rows in families.values() for r in rows], key=lambda r:r['review_remaining_s'])[:8],
            'unmeasured': ['durable source receipt to evidence readiness', 'human review duration', 'complete source-to-browser latency'],
            'note': 'Reanalysis of retained runs, not a new trial. No clock-domain subtraction or gate/expiry changes.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs', nargs='+', type=Path)
    args = parser.parse_args()
    print(json.dumps([analyze(json.loads(path.read_text())) for path in args.runs], indent=2))
