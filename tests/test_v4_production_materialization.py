from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from xi_kari_runtime.canonical_json import atomic_write_json, read_json, sha256_json
from tests.test_p04_v4_packet import _packet_inputs
from xi_kari_runtime.packet_v4 import build_analysis_packet_v4


def _packet():
    semantic, contract = _packet_inputs()
    return build_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT), contract


def test_v4_production_entry_points_are_independent_of_active_v3():
    from xi_kari_runtime.materialization_v4 import materialize_run_v4
    from xi_kari_runtime.validation_v4 import validate_run_v4
    from xi_kari_runtime.source_profile import RUNTIME_VERSION, SOURCE_VERSION

    assert callable(materialize_run_v4) and callable(validate_run_v4)
    assert (RUNTIME_VERSION, SOURCE_VERSION) == ('3.0.0', 'v8.3')


def test_static_v4_phase_artifacts_preserve_real_claims_and_no_world_invention():
    from xi_kari_runtime.validation_v4 import build_semantic_phase_artifacts_v4

    packet, contract = _packet()
    documents = build_semantic_phase_artifacts_v4(packet, contract=contract, repository_root=ROOT)
    graph = documents['XK7']['authoring/XK07-claim-mechanism-graph.json']
    assert graph['payload'] == packet['claim_mechanism_graph']
    assert graph['result']['claims'][0]['statement'] == packet['claim_mechanism_graph']['claims'][0]['statement']
    assert graph['input_packet_sha256'] == sha256_json(packet)
    world = documents['XK5']['authoring/XK05-local-world-model.json']
    assert world['payload'] is None
    assert world['result']['applicability'] == packet['applicability']['world_state']
    assert world['result']['evaluated'] is False


def test_materializer_rejects_v3_source_and_never_mutates_it(tmp_path):
    from xi_kari_runtime.materialization_v4 import materialize_run_v4

    path = tmp_path / 'run-contract.json'
    original = b'{"schema_id":"xi-kari.v3.run-contract","schema_version":3,"source_version":"v8.3"}\n'
    path.write_bytes(original)
    with pytest.raises(ValueError, match='version-four|v9.0|incompatible'):
        materialize_run_v4(tmp_path, repository_root=ROOT)
    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]


def test_fresh_validation_rejects_unprepared_physical_inputs_read_only(tmp_path):
    from xi_kari_runtime.validation_v4 import validate_run_v4

    atomic_write_json(tmp_path / 'run-contract.json', {'schema_id': 'xi-kari.v4.run-contract', 'schema_version': 4})
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    report = validate_run_v4(tmp_path, repository_root=ROOT, require_complete=False)
    assert report['schema_id'] == 'xi-kari.v4.validator-report'
    assert report['valid'] is report['complete'] is False
    assert report['errors']
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


def test_v4_phase_input_recomputes_exact_disk_values_and_predecessor():
    from xi_kari_runtime.validation_v4 import phase_input_sha256_v4

    predecessor = {'record_sha256': 'a' * 64}
    value = {'packet_sha256': 'b' * 64, 'phase': 'XK3', 'artifacts': [{'path': 'evidence', 'sha256': 'c' * 64}]}
    digest = phase_input_sha256_v4(predecessor, value)
    assert digest == sha256_json({'predecessor': 'a' * 64, 'value': value})
    assert digest != phase_input_sha256_v4(None, value)
    value['artifacts'][0]['sha256'] = 'd' * 64
    assert digest != phase_input_sha256_v4(predecessor, value)


def test_marker_or_empty_dynamic_inputs_cannot_materialize_a_stage():
    from xi_kari_runtime.validation_v4 import build_semantic_phase_artifacts_v4

    packet, contract = _packet()
    packet['applicability']['world_state']['status'] = 'applicable'
    packet['claim_mechanism_graph']['applicability']['world_state']['status'] = 'applicable'
    packet['local_world_model'] = {'status': 'validated'}
    with pytest.raises(ValueError, match='world|state|consumer|schema'):
        build_semantic_phase_artifacts_v4(packet, contract=contract, repository_root=ROOT)


def test_unknown_root_schema_is_rejected_without_leaking_its_values(tmp_path):
    from xi_kari_runtime.validation_v4 import validate_json_artifact_ownership_v4

    secret = 'protected-content-do-not-echo'
    atomic_write_json(tmp_path / 'unknown.json', {'schema_id': 'xi-kari.v4.unregistered', 'raw': secret})
    errors = validate_json_artifact_ownership_v4(tmp_path, ROOT)
    assert any('unknown' in error or 'owner' in error for error in errors)
    assert all(secret not in error for error in errors)


def test_root_schema_registry_ignores_nested_compatible_protocol_owner(tmp_path):
    from xi_kari_runtime.validation_v4 import schema_registry_v4

    schemas = tmp_path / 'schemas'
    schemas.mkdir()
    atomic_write_json(schemas / 'owner.json', {'$schema': 'https://json-schema.org/draft/2020-12/schema', '$id': 'urn:owner', 'type': 'object', 'properties': {'schema_id': {'const': 'xi-kari.v4.owner'}, 'nested': {'properties': {'schema_id': {'const': 'xi-kari.v3.aux'}}}}})
    atomic_write_json(schemas / 'aux.json', {'$schema': 'https://json-schema.org/draft/2020-12/schema', '$id': 'urn:aux', 'type': 'object', 'properties': {'schema_id': {'const': 'xi-kari.v3.aux'}}})
    registry, errors = schema_registry_v4(tmp_path)
    assert errors == []
    assert registry['xi-kari.v4.owner'].name == 'owner.json'
    assert registry['xi-kari.v3.aux'].name == 'aux.json'


def test_two_actual_root_schema_owners_are_rejected(tmp_path):
    from xi_kari_runtime.validation_v4 import schema_registry_v4

    for name in ('one.json', 'two.json'):
        atomic_write_json(tmp_path / 'schemas' / name, {'$schema': 'https://json-schema.org/draft/2020-12/schema', '$id': 'urn:' + name, 'properties': {'schema_id': {'const': 'xi-kari.v4.owner'}}})
    _, errors = schema_registry_v4(tmp_path)
    assert any('duplicate' in error for error in errors)


def test_v4_run_schema_fixes_profile_source_and_real_unit_count():
    schema = read_json(ROOT / 'schemas/xk-v4-production-run.schema.json')
    assert schema['properties']['source_version'] == {'const': 'v9.0'}
    assert schema['properties']['contract_profile'] == {'const': 'production-authoring-v4'}
    capability = schema['properties']['capability_snapshot']
    assert capability['properties']['source_unit_count'] == {'const': 4418}
    assert capability['properties']['reader_unit_count'] == {'const': 21}


def _provider_pair():
    from xi_kari_runtime.authoring import bind_base_authoring_provider, bind_semantic_authoring_adapter

    base = bind_base_authoring_provider(Path(sys.executable).resolve(), mode='open-world', repository_root=ROOT, timeout_seconds=120)
    adapter = bind_semantic_authoring_adapter(ROOT / 'scripts/xi_kari_codex_authoring_adapter.py', codex_provider_executable=Path(sys.executable).resolve(), repository_root=ROOT, profile='production-codex', timeout_seconds=120)
    return base, adapter


def test_actual_base_and_probe_web_policy_difference_is_preserved():
    from xi_kari_runtime.validation_v4 import validate_provider_pair_v4

    base, adapter = _provider_pair()
    assert base['web_search'] == 'live'
    assert adapter['provider_binding']['web_search'] == 'disabled'
    validate_provider_pair_v4(base, adapter, mode='open-world')


@pytest.mark.parametrize('field', ['model', 'reasoning_effort', 'executable_sha256', 'sandbox'])
def test_actual_base_and_probe_identity_mismatch_is_rejected(field):
    from xi_kari_runtime.validation_v4 import validate_provider_pair_v4

    base, adapter = _provider_pair()
    adapter['provider_binding'][field] = 'unmatched-identity'
    adapter['provider_binding_sha256'] = sha256_json(adapter['provider_binding'])
    with pytest.raises(ValueError, match='provider|binding|identity'):
        validate_provider_pair_v4(base, adapter, mode='open-world')


def test_fresh_process_validator_reports_its_own_pid_and_retains_failure(tmp_path):
    from xi_kari_runtime.validation_v4 import run_fresh_validator_v4
    import os

    atomic_write_json(tmp_path / 'run-contract.json', {'schema_id': 'xi-kari.v4.run-contract', 'schema_version': 4})
    report = run_fresh_validator_v4(tmp_path, repository_root=ROOT, require_complete=False)
    assert report['fresh_process'] is True
    assert report['validator_pid'] != os.getpid()
    assert report['valid'] is False
    attempts = list((tmp_path / 'validation/attempts').glob('final-*/execution.json'))
    assert len(attempts) == 1
    record = read_json(attempts[0])
    assert record['child_pid'] == report['validator_pid']
    assert record['exit_status'] == 2
    assert read_json(attempts[0].parent / 'validator-report.json') == report
