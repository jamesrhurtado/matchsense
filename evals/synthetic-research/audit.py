"""Read-only diagnostics for the existing flagship and live synthetic exports.

Run from the repository root with its Python environment. This does not export
fixtures, alter reference answers, run models, or certify football realism.
"""
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from simulator.validate import validate_feed


def audit(number):
    folder = ROOT / 'data/runtime' / f'match-0c0a00000000000{number}'
    metadata = json.loads((folder / 'match.json').read_text())
    compressed = (folder / 'stream.jsonl.gz').read_bytes()
    rows = [json.loads(line) for line in gzip.decompress(compressed).splitlines()]
    try:
        validation = {'passed': True, 'result': validate_feed(metadata, rows)}
    except (AssertionError, ValueError) as exc:
        validation = {'passed': False, 'error': str(exc)}
    # First source revisions only: do not differentiate correction arrivals or
    # retransmissions as if they were new physical movement.
    original = {r['message_id']: r for r in rows if r['revision'] == 1}
    frames = sorted((r for r in original.values() if r['kind'] == 'tracking_frame'),
                    key=lambda r: r['timeline_ms'])
    previous = None
    velocities = {}
    max_speed = {'mps': 0}
    max_acceleration = {'mps2': 0}
    for frame in frames:
        positions = {p['player_id']: p for p in frame['payload']['players']}
        if previous:
            old_frame, old_positions = previous
            dt = (frame['timeline_ms'] - old_frame['timeline_ms']) / 1000
            for pid, position in positions.items():
                if pid not in old_positions:
                    velocities.pop(pid, None)
                    continue
                old = old_positions[pid]
                velocity = tuple((position[a] - old[a]) / dt for a in ('x_m', 'y_m'))
                speed = math.hypot(*velocity)
                if speed > max_speed['mps']:
                    max_speed = {'mps': round(speed, 6), 'player_id': pid,
                                 'timeline_ms': frame['timeline_ms']}
                midpoint = (frame['timeline_ms'] + old_frame['timeline_ms']) / 2000
                if pid in velocities:
                    old_velocity, old_midpoint = velocities[pid]
                    acceleration = math.dist(velocity, old_velocity) / (midpoint - old_midpoint)
                    if acceleration > max_acceleration['mps2']:
                        max_acceleration = {'mps2': round(acceleration, 6), 'player_id': pid,
                                            'timeline_ms': frame['timeline_ms']}
                velocities[pid] = velocity, midpoint
            for pid in set(old_positions) - set(positions):
                velocities.pop(pid, None)
        previous = frame, positions
    return {
        'match_id': metadata['match_id'],
        'stream_sha256': hashlib.sha256(compressed).hexdigest(),
        'existing_validator': validation,
        'frame_intervals_ms': dict(Counter(b['timeline_ms'] - a['timeline_ms']
                                         for a, b in zip(frames, frames[1:]))),
        'source_event_types': dict(Counter(r['payload']['type'] for r in original.values()
                                          if r['kind'] == 'event')),
        'maximum_sampled_player_speed': max_speed,
        'maximum_finite_difference_player_acceleration': max_acceleration,
    }


if __name__ == '__main__':
    print(json.dumps({
        'purpose': 'Research audit only; no new realism threshold or certification.',
        'acceleration_method': 'Vector velocity over consecutive observed intervals, '
            'then vector change divided by interval-midpoint spacing. '
            'Piecewise-linear knots and rounding can produce spikes. '
            'Missing-player gaps reset velocity history.',
        'lineage': 'All four exports derive from simulator.flagship; mirrors and '
            'delivery-fault variants are not independent football trajectories.',
        'cases': [audit(number) for number in (5, 6, 7, 8)],
    }, indent=2))
