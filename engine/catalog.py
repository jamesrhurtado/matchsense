"""Allowlisted runtime observations; no generator, labels or reference imports."""
from __future__ import annotations
from functools import lru_cache
import gzip
import json
from pathlib import Path
import re

from engine.contracts import MatchMetadata, OBSERVATION

RUNTIME = Path(__file__).resolve().parents[1] / 'data/runtime'
MATCH_ID = re.compile(r'match-(?:00[1-3]|[a-f0-9]{16})\Z')


@lru_cache(maxsize=1)
def _catalog():
    rows = json.loads((RUNTIME / 'catalog.json').read_text())
    seen = set()
    for row in rows:
        if set(row) != {'match_id', 'label', 'duration_ms', 'synthetic'}:
            raise ValueError('invalid_catalog_fields')
        mid = row['match_id']
        if not isinstance(mid, str) or not MATCH_ID.fullmatch(mid) or mid in seen:
            raise ValueError('invalid_catalog_match_id')
        if (row['synthetic'] is not True or type(row['duration_ms']) is not int
                or not 0 < row['duration_ms'] <= 5400000
                or not isinstance(row['label'], str) or not row['label']):
            raise ValueError('invalid_catalog_entry')
        seen.add(mid)
    return rows


def list_matches(include_coverage=False):
    """Return only display metadata, never authored scenario expectations."""
    rows=[dict(row) for row in _catalog()]
    extra=RUNTIME/'match-coverage-catalog.json'
    if include_coverage and extra.exists():
        additions=json.loads(extra.read_text())
        seen={r['match_id'] for r in rows}
        for row in additions:
            if (set(row)!={'match_id','label','duration_ms','synthetic'} or not isinstance(row['match_id'],str)
                    or not MATCH_ID.fullmatch(row['match_id']) or row['match_id'] in seen or row['synthetic'] is not True
                    or type(row['duration_ms']) is not int or not 0<row['duration_ms']<=5400000
                    or not isinstance(row['label'],str) or not row['label']):raise ValueError('invalid_coverage_catalog_entry')
            seen.add(row['match_id'])
        rows+=additions
    return rows


def duration_for_match(match_id):
    return next((r['duration_ms'] for r in list_matches(True) if r['match_id'] == match_id), 60000)


@lru_cache(maxsize=8)
def load_runtime_match(match_id):
    if (not isinstance(match_id, str) or not MATCH_ID.fullmatch(match_id)
            or match_id not in {r['match_id'] for r in list_matches(True)}):
        raise ValueError('unknown_match')
    folder = RUNTIME / match_id
    metadata = json.loads((folder / 'match.json').read_text())
    MatchMetadata.model_validate(metadata)
    if metadata['match_id'] != match_id:
        raise ValueError('catalog_metadata_mismatch')
    compressed = folder / 'stream.jsonl.gz'
    opener = gzip.open if compressed.exists() else open
    source = compressed if compressed.exists() else folder / 'stream.jsonl'
    with opener(source, 'rt', encoding='utf-8') as stream:
        observations = [json.loads(line) for line in stream if line.strip()]
    for observation in observations:
        OBSERVATION.validate_python(observation)
        if observation['match_id'] != match_id:
            raise ValueError('catalog_observation_mismatch')
    return metadata, observations
