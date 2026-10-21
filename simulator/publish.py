"""Publish validated observation-only v2 replays into the application catalogue.

Reference labels, seeds and provenance remain outside data/runtime. Compression
has fixed timestamps so repeated publication produces identical deployed bytes.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from simulator.scenarios import VERSION, cases
from simulator.suite import generate_case, serialize
from simulator.validate import validate, validate_feed

ROOT = Path(__file__).resolve().parents[1]


def publish(root=ROOT / 'data'):
    runtime = root / 'runtime'
    runtime.mkdir(parents=True, exist_ok=True)
    catalog = [{'match_id':f'match-{i:03d}', 'label':f'Original segment {i} · 1 min',
                'duration_ms':60000, 'synthetic':True} for i in range(1, 4)]
    records = []
    generated = cases()
    for number, case in enumerate(generated, 1):
        dataset = generate_case(case)
        validate(dataset.metadata, dataset.clean)
        result = validate_feed(dataset.metadata, dataset.observations)
        folder = runtime / case.match_id
        folder.mkdir(parents=True, exist_ok=True)
        metadata = (json.dumps(dataset.metadata, indent=2) + '\n').encode()
        raw = serialize(dataset.observations).encode()
        compressed = gzip.compress(raw, compresslevel=9, mtime=0)
        (folder / 'match.json').write_bytes(metadata)
        (folder / 'stream.jsonl.gz').write_bytes(compressed)
        duration = dataset.reference['duration_ms']
        catalog.append({'match_id':case.match_id, 'label':f'Synthetic segment {number:03d} · {duration / 60000:g} min',
                        'duration_ms':duration, 'synthetic':True})
        records.append({'case_id':case.id, 'match_id':case.match_id,
                        'metadata_sha256':hashlib.sha256(metadata).hexdigest(),
                        'observations_sha256':hashlib.sha256(raw).hexdigest(),
                        'compressed_sha256':hashlib.sha256(compressed).hexdigest(),
                        'validation':result})
        if number % 28 == 0:
            print(f'Published validated replay {number}/{len(generated)}', flush=True)
    # Put a longer replay near the beginning for demo discovery; labels disclose
    # duration only, never future event counts, outcomes or reference answers.
    preferred = [generated[27].match_id, generated[26].match_id]
    catalog.sort(key=lambda row: (0, int(row['match_id'][-3:])) if row['match_id'] in {'match-001','match-002','match-003'}
                 else (1, preferred.index(row['match_id'])) if row['match_id'] in preferred
                 else (2, row['label']))
    (runtime / 'catalog.json').write_text(json.dumps(catalog, indent=2) + '\n')
    provenance = root / 'provenance'
    provenance.mkdir(parents=True, exist_ok=True)
    (provenance / 'runtime-v2.json').write_text(json.dumps({'generator_version':VERSION,
        'source':'Original fictional scripted trajectories; no real match records.',
        'runtime_contains':'Match metadata and delivered observations only; no reference checks or seeds.',
        'cases':records}, indent=2) + '\n')
    return catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'data')
    args = parser.parse_args()
    catalog = publish(args.output)
    print(f'Runtime catalogue contains {len(catalog)} synthetic segments.')


if __name__ == '__main__':
    main()
