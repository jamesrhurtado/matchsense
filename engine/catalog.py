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


def development_matches():
    """Opt-in display catalogue only; never scene labels, profiles or references."""
    path=RUNTIME/'synthetic-development-catalog.json'
    return json.loads(path.read_text()) if path.exists() else []


def list_matches(include_coverage=False, include_development=False):
    """Return only display metadata, never authored scenario expectations."""
    rows=[dict(row) for row in _catalog()]
    extra=RUNTIME/'match-coverage-catalog.json'
    if (include_coverage and extra.exists()) or include_development:
        additions=(json.loads(extra.read_text()) if include_coverage and extra.exists() else [])
        if include_development:additions+=development_matches()
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
    original=next((r['duration_ms'] for r in list_matches(True) if r['match_id']==match_id),None)
    if original is not None:return original
    return next((r['duration_ms'] for r in list_matches(False,True) if r['match_id']==match_id),60000)


@lru_cache(maxsize=8)
def load_runtime_match(match_id):
    if (not isinstance(match_id, str) or not MATCH_ID.fullmatch(match_id)):
        raise ValueError('unknown_match')
    known={r['match_id'] for r in list_matches(True)}
    if match_id not in known and match_id not in {r['match_id'] for r in list_matches(False,True)}:
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
