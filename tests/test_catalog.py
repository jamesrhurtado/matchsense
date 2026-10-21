"""The deployed catalogue is allowlisted, observation-only and reproducible."""
import gzip
import hashlib
import json

import pytest

from engine.catalog import RUNTIME, duration_for_match, list_matches, load_runtime_match


def test_runtime_catalogue_contains_originals_and_all_added_cases():
    rows = list_matches()
    assert len(rows) == 171
    assert [r['match_id'] for r in rows[:3]] == ['match-001','match-002','match-003']
    assert len({r['match_id'] for r in rows}) == len(rows)
    assert all(set(r) == {'match_id','label','duration_ms','synthetic'} for r in rows)
    assert all(r['synthetic'] is True for r in rows)
    assert duration_for_match(rows[3]['match_id']) == 180000
    assert duration_for_match(rows[4]['match_id']) == 90000
    rows[0]['label'] = 'changed'
    assert list_matches()[0]['label'] != 'changed'


@pytest.mark.parametrize('match_id', ['../evaluation-only/match-001', '/tmp/match-001', 'match-004', 'match-0000000000000000', None])
def test_runtime_loader_rejects_nonallowlisted_identifiers(match_id):
    with pytest.raises(ValueError, match='unknown_match'):
        load_runtime_match(match_id)


def test_compressed_runtime_is_reproducible_and_matches_provenance():
    manifest = json.loads((RUNTIME.parent / 'provenance/runtime-v2.json').read_text())
    assert len(manifest['cases']) == 168
    for row in manifest['cases']:
        folder = RUNTIME / row['match_id']
        encoded = (folder / 'stream.jsonl.gz').read_bytes()
        assert encoded[4:8] == b'\0\0\0\0'
        assert hashlib.sha256(encoded).hexdigest() == row['compressed_sha256']
        raw = gzip.decompress(encoded)
        assert hashlib.sha256(raw).hexdigest() == row['observations_sha256']
        assert hashlib.sha256((folder / 'match.json').read_bytes()).hexdigest() == row['metadata_sha256']
        assert set(p.name for p in folder.iterdir()) == {'match.json','stream.jsonl.gz'}
        assert not any(word in raw for word in (b'expected_pass_ids', b'fault_plan', b'positive_claim_bounds', b'parent_seed'))


def test_runtime_loads_long_segment_with_schema_validation():
    row = list_matches()[3]
    metadata, observations = load_runtime_match(row['match_id'])
    assert metadata['match_id'] == row['match_id']
    assert max(m['timeline_ms'] for m in observations) == row['duration_ms']
    assert len([m for m in observations if m['kind']=='event' and m['payload']['type']=='pass_started']) == 3
    assert load_runtime_match.cache_info().maxsize == 8


def test_runtime_id_consistency_is_checked(tmp_path, monkeypatch):
    import engine.catalog as catalog
    row = list_matches()[0]
    metadata, observations = load_runtime_match(row['match_id'])
    folder = tmp_path / row['match_id']
    folder.mkdir()
    (folder / 'match.json').write_text(json.dumps(metadata | {'match_id':'match-002'}))
    (folder / 'stream.jsonl').write_text(json.dumps(observations[0])+'\n')
    monkeypatch.setattr(catalog, 'RUNTIME', tmp_path)
    catalog.load_runtime_match.cache_clear()
    with pytest.raises(ValueError, match='catalog_metadata_mismatch'):
        catalog.load_runtime_match(row['match_id'])
    catalog.load_runtime_match.cache_clear()
