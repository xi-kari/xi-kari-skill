from __future__ import annotations

from pathlib import Path
import shutil
import sys
import json

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from xi_kari_runtime.canonical_json import read_json
from xi_kari_runtime.retrieval import build_full_source_lock, validate_full_source_lock
from xi_kari_runtime.semantic_read_trace import (
    build_semantic_read_trace, validate_semantic_read_trace, validate_semantic_read_trace_input,
)


def test_versioned_source_lock_reads_v90_units_in_manifest_order() -> None:
    lock, events = build_full_source_lock(ROOT, run_id='v90-read', source_version='v9.0')
    manifest = read_json(ROOT / 'references/source/v9.0/source-manifest.json')
    assert lock['framework_version'] == 'v9.0'
    assert lock['paragraph_count'] == 4298
    assert lock['table_count'] == 120
    assert lock['source_unit_count'] == 4418
    assert [row['source_anchor'] for row in events] == manifest['source_unit_sequence']
    assert {row['reader_unit'] for row in events} == set(manifest['reader_units'])
    assert validate_full_source_lock(lock, events, ROOT) == []


def test_v90_read_lock_rejects_a_different_raw_source_revision(tmp_path: Path) -> None:
    source = tmp_path / 'source'
    source.mkdir()
    (source / '跨尺度多圈层结构推演框架v9.0.docx').write_bytes(b'different source revision')
    snapshot = tmp_path / 'references/source/v9.0'
    snapshot.mkdir(parents=True)
    shutil.copyfile(ROOT / 'references/source/v9.0/source-manifest.json', snapshot / 'source-manifest.json')
    with pytest.raises(ValueError, match='source revision'):
        build_full_source_lock(tmp_path, run_id='v90-read', source_version='v9.0')


def _trace_input() -> dict:
    manifest = read_json(ROOT / 'references/source/v9.0/source-manifest.json')
    records = []
    for index, division in enumerate(manifest['divisions']):
        unit = division['reader_file']
        anchor = division['source_unit_anchors'][0]
        title = division['title']
        records.append({
            'reader_unit': unit,
            'synthesis': f'This fixture binds the actual source volume titled {title}; it tests source-version and membership verification, not a claim of semantic understanding.',
            'semantic_observations': [{'proposition': title, 'role': 'source-scope', 'source_anchor_refs': [anchor]}],
            'continuity_with_previous': {
                'previous_reader_unit': None if index == 0 else manifest['reader_units'][index-1],
                'relation': 'root' if index == 0 else 'extends',
                'explanation': f'{title} follows the actual manifest sequence.',
            },
            'problem_relation': {'status': 'boundary_only', 'rationale': f'The {title} scope constrains this fixture.'},
            'source_undefined_refs': [],
        })
    return {'schema_id': 'xi-kari.v4.semantic-read-trace-input', 'schema_version': 1, 'records': records}


def test_v90_semantic_read_trace_uses_manifest_membership_and_source_version() -> None:
    lock, events = build_full_source_lock(ROOT, run_id='v90-trace', source_version='v9.0')
    manifest = read_json(ROOT / 'references/source/v9.0/source-manifest.json')
    payload = _trace_input()
    validate_semantic_read_trace_input(payload, repository_root=ROOT, source_lock=lock, source_events=events)
    payload['records'][0]['semantic_observations'][0]['source_anchor_refs'] = [manifest['divisions'][1]['source_unit_anchors'][0]]
    with pytest.raises(ValueError, match='crosses reader units'):
        validate_semantic_read_trace_input(payload, repository_root=ROOT, source_lock=lock, source_events=events)


def test_v90_imported_semantic_trace_survives_fresh_source_validation(tmp_path: Path) -> None:
    lock, events = build_full_source_lock(ROOT, run_id='v90-trace', source_version='v9.0')
    source_input = tmp_path / 'source-reading.json'
    source_input.write_text(json.dumps(_trace_input(), ensure_ascii=False), encoding='utf-8')
    contract = {'run_id': 'v90-trace', 'problem_contract_sha256': 'a' * 64, 'contract_profile': 'production-authoring-v4'}
    artifact = build_semantic_read_trace(
        source_input, repository_root=ROOT, run_contract=contract,
        source_lock=lock, source_events=events, xk0_record_sha256='b' * 64,
        imported_at='2026-09-30T05:00:00Z',
    )
    assert validate_semantic_read_trace(
        artifact, repository_root=ROOT, run_contract=contract,
        source_lock=lock, source_events=events, xk0_record_sha256='b' * 64,
    ) == []
