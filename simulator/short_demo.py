"""Publish a one-minute, moving presentation demo with role-aware keepers.

This additive derivative preserves all established source fixtures and their
hashes. It uses the authored matchday scene and publishes only its first minute.
"""
import gzip
import hashlib
import json
from pathlib import Path

from simulator.matchday_demo import build as build_matchday
from simulator.suite import serialize
from engine.contracts import OBSERVATION

ROOT = Path(__file__).resolve().parents[1]
MATCH_ID = 'match-0c0a000000000009'
DURATION_MS = 60_000


def build():
    metadata, source_rows = build_matchday(False)
    metadata['match_id'] = MATCH_ID
    metadata['provenance_id'] = 'short-presentation-demo-v1'
    rows = [row for row in source_rows if row['timeline_ms'] <= DURATION_MS]
    for sequence, row in enumerate(rows):
        row['match_id'] = MATCH_ID
        row['sequence_no'] = sequence
        OBSERVATION.validate_python(row)
    rows.sort(key=lambda row: (row['available_at_ms'], row['sequence_no']))
    return metadata, rows


def main():
    metadata, rows = build()
    folder = ROOT / 'data/runtime' / MATCH_ID
    folder.mkdir(parents=True, exist_ok=True)
    raw = serialize(rows).encode()
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    (folder / 'match.json').write_text(json.dumps(metadata, indent=2) + '\n')
    (folder / 'stream.jsonl.gz').write_bytes(compressed)

    catalog_path = ROOT / 'data/runtime/match-coverage-catalog.json'
    catalog = json.loads(catalog_path.read_text())
    catalog = [entry for entry in catalog if entry['match_id'] != MATCH_ID]
    catalog.insert(0, {
        'match_id': MATCH_ID,
        'label': 'One-minute moving demo · role-aware keepers',
        'duration_ms': DURATION_MS,
        'synthetic': True,
    })
    catalog_path.write_text(json.dumps(catalog, indent=2) + '\n')

    provenance = {
        'generator': 'simulator.short_demo',
        'version': '1',
        'source_match_id': 'match-0c0a000000000003',
        'status': 'Versioned one-minute presentation excerpt; authored movement; football review pending; source demo unchanged',
        'duration_ms': DURATION_MS,
        'observations': len(rows),
        'sha256_gzip_stream': hashlib.sha256(compressed).hexdigest(),
        'keeper_motion': 'Inherited from matchday-demo-v2; scripted near-own-goal lanes, not tactical ground truth.',
    }
    (ROOT / 'data/provenance/short-demo-v1.json').write_text(
        json.dumps(provenance, indent=2) + '\n'
    )
    print(f'Published {MATCH_ID} with {len(rows)} observations.')


if __name__ == '__main__':
    main()
