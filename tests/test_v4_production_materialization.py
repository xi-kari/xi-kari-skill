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


def test_semantic_materialization_rebuilds_the_actual_formal_instance_registry():
    from tests.test_p04_instance_results_v4 import packet_inputs
    from xi_kari_runtime.validation_v4 import build_semantic_phase_artifacts_v4

    semantic, contract = packet_inputs()
    packet = build_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT)
    documents = build_semantic_phase_artifacts_v4(packet, contract=contract, repository_root=ROOT)
    claim = documents['XK7']['authoring/XK07-claim-mechanism-graph.json']['result']['claims'][0]
    assert claim['formal_qualification']['status'] == 'qualified'
    assert claim['formal_qualification']['result_status'] == 'supported'
    packet['empirical_instances'][0]['evaluation']['prerequisite_claim_ids'] = {}
    with pytest.raises(ValueError, match='recomputed|qualification|instance'):
        build_semantic_phase_artifacts_v4(packet, contract=contract, repository_root=ROOT)


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


def test_foreign_validator_exception_cannot_expose_protected_raw_text(tmp_path, monkeypatch):
    from xi_kari_runtime import validation_v4

    secret = 'protected-raw-user-text'
    atomic_write_json(tmp_path / 'run-contract.json', {'run_id': 'privacy-error'})
    monkeypatch.setattr(validation_v4, 'require_run_contract_v4', lambda *args, **kwargs: ROOT)

    def foreign_failure(*args, **kwargs):
        raise ValueError('version-four evidence validation failed: ' + secret)

    monkeypatch.setattr(validation_v4, 'validate_preparation_v4', foreign_failure)
    report = validation_v4.validate_run_v4(tmp_path, repository_root=ROOT, require_complete=False)
    assert report['valid'] is False
    assert secret not in json.dumps(report)


def test_recognized_source_protocol_cannot_be_relocated_to_an_unknown_path(tmp_path):
    from xi_kari_runtime.validation_v4 import validate_json_artifact_ownership_v4

    atomic_write_json(tmp_path / 'unowned-source.json', {'schema_id': 'xi-kari.v4.source-lock', 'schema_version': 4, 'complete': True})
    errors = validate_json_artifact_ownership_v4(tmp_path, ROOT)
    assert 'artifact path has no runtime owner: unowned-source.json' in errors


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


def test_root_registry_resolves_only_local_references_reachable_from_artifact_root(tmp_path):
    from xi_kari_runtime.validation_v4 import schema_registry_v4

    atomic_write_json(tmp_path / 'schemas' / 'branch.json', {
        '$schema': 'https://json-schema.org/draft/2020-12/schema', '$id': 'urn:branches',
        'oneOf': [{'$ref': '#/$defs/left'}, {'$ref': '#/$defs/right'}],
        '$defs': {
            'left': {'properties': {'schema_id': {'const': 'xi-kari.v4.left'}}},
            'right': {'properties': {'schema_id': {'const': 'xi-kari.v4.right'}, 'nested': {'properties': {'schema_id': {'const': 'xi-kari.v3.nested'}}}}},
            'unreferenced': {'properties': {'schema_id': {'const': 'xi-kari.v4.unreferenced'}}},
        },
    })
    owners, errors = schema_registry_v4(tmp_path)
    assert errors == []
    assert set(owners) == {'xi-kari.v4.left', 'xi-kari.v4.right'}


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


def _source_prepared(tmp_path):
    from tests.test_p04_v4_authoring import _authoring_input
    from xi_kari_runtime.canonical_json import atomic_write_bytes, atomic_write_text, canonical_bytes
    from xi_kari_runtime.contracts import EXECUTE_OWNED_BINDING_FIELDS
    from xi_kari_runtime.ontology_read_trace import build_ontology_read_trace
    from xi_kari_runtime.phase_chain import append_phase, load_phase_records
    from xi_kari_runtime.problem_contract import contract_hash, stance_neutrality_key
    from xi_kari_runtime.semantic_read_trace import build_semantic_read_trace
    from xi_kari_runtime.terminal_authority import generate_terminal_authority
    from xi_kari_runtime.validation_v4 import expected_phase_paths_v4, phase_input_sha256_v4, provider_environment_sha256, validator_set_sha256_v4

    value, problem, ontology_plan, lock, events = _authoring_input()
    _, adapter = _provider_pair()
    run_id = lock['run_id']
    execute = {field: 'a' * 64 for field in EXECUTE_OWNED_BINDING_FIELDS}
    execute.update(protocol='xi-kari.v3.execute-owned-binding/v1', owner='execute_authored_run', run_id=run_id, parent_pid=1, child_pid=2, exit_status=0)
    authority, key = generate_terminal_authority(run_id)
    contract = {
        'schema_id': 'xi-kari.v4.run-contract', 'schema_version': 4, 'runtime_version': '4.0.0',
        'source_version': 'v9.0', 'contract_profile': 'production-authoring-v4', 'run_id': run_id,
        'question': problem['question'], 'mode': 'open-world', 'problem_contract': problem,
        'problem_contract_sha256': contract_hash(problem), 'evidence_cutoff': problem['evidence_cutoff'],
        'repository_root': str(ROOT), 'validator_set_sha256': validator_set_sha256_v4(ROOT),
        'provider_environment_sha256': provider_environment_sha256(), 'created_at': '2026-09-30T05:00:00Z',
        'privacy_contract': {'purpose': 'bounded source-scope analysis', 'delivery_audience': 'requesting-user', 'classification_scheme': ['public', 'context_limited', 'sensitive', 'highly_sensitive', 'refused_disclosure'], 'fail_closed': True},
        'continuation': {'kind': 'original', 'generation': 0, 'parent_run_id': None, 'parent_chain_head_sha256': None},
        'dynamic_applicability': 'pending', 'stance_neutrality_key': stance_neutrality_key(problem, mode='open-world'),
        'terminal_authority': authority,
        'capability_snapshot': {'contract_profile': 'production-authoring-v4', 'network_retrieval': True, 'full_source_read_required': True, 'source_unit_count': 4418, 'reader_unit_count': 21, 'semantic_authoring_adapter': adapter, 'execute_owned_binding': execute},
    }
    atomic_write_json(tmp_path / 'run-contract.json', contract)
    atomic_write_json(tmp_path / 'capability-snapshot.json', {'schema_id': 'xi-kari.v4.capability-snapshot', 'schema_version': 4, 'run_id': run_id, 'mode': 'open-world', **contract['capability_snapshot'], 'captured_at': contract['created_at']})
    xk0 = append_phase(tmp_path, run_id=run_id, phase='XK0', artifact_path=expected_phase_paths_v4('XK0', mode='open-world'), input_sha256=sha256_json({key: contract[key] for key in ('question', 'mode', 'problem_contract', 'privacy_contract')}), created_at=contract['created_at'])
    atomic_write_json(tmp_path / 'source-lock.json', lock)
    atomic_write_text(tmp_path / 'authoring/XK01-read-events.jsonl', ''.join(json.dumps(event) + '\n' for event in events))
    atomic_write_json(tmp_path / 'authoring/XK01-read-plan.json', {'schema_id': 'xi-kari.v4.read-plan', 'schema_version': 4, 'run_id': run_id, 'framework_version': 'v9.0', **{field: lock[field] for field in ('reader_sequence', 'reader_unit_count', 'paragraph_count', 'table_count', 'source_unit_count')}, 'requires_complete_semantic_read': True})
    raw_path = tmp_path / 'authoring/XK01-semantic-read-trace-input.json'
    atomic_write_json(raw_path, value['semantic_read_trace'])
    trace = build_semantic_read_trace(raw_path, repository_root=ROOT, run_contract=contract, source_lock=lock, source_events=events, xk0_record_sha256=xk0['record_sha256'], imported_at=contract['created_at'])
    atomic_write_json(tmp_path / 'authoring/XK01-semantic-read-trace.json', trace)
    atomic_write_json(tmp_path / 'authoring/XK04-ontology-read-plan.json', ontology_plan)
    atomic_write_json(tmp_path / 'authoring/XK04-ontology-read-trace-input.json', value['ontology_read_trace'])
    ontology = build_ontology_read_trace(value['ontology_read_trace'], plan=ontology_plan, run_id=run_id, repository_root=ROOT, problem_contract_sha256=contract_hash(problem))
    atomic_write_json(tmp_path / 'authoring/XK04-ontology-read-trace.json', ontology)
    for relative, raw in (
        ('authoring/XK01-base-authoring-events.jsonl', b'{"type":"synthetic-preparation-only"}\n'),
        ('authoring/XK01-base-authoring-request.json', b'{"fixture":"synthetic-preparation-only"}\n'),
        ('authoring/XK01-base-authoring-prompt.txt', b'Synthetic preparation skeleton; no provider execution.'),
        ('authoring/XK01-base-authoring-output.bin', b'Synthetic preparation skeleton; no provider execution.'),
        ('authoring/XK01-base-authoring-receipt.json', b'{"fixture":"synthetic-preparation-only"}\n'),
        ('authoring/XK01-base-authoring-stderr.bin', b''),
    ):
        atomic_write_bytes(tmp_path / relative, raw)
    append_phase(tmp_path, run_id=run_id, phase='XK1', artifact_path=expected_phase_paths_v4('XK1', mode='open-world'), input_sha256=phase_input_sha256_v4(xk0, {'source_lock': lock, 'semantic_read_trace': trace}), created_at=contract['created_at'])
    return contract, load_phase_records(tmp_path)


def test_preparation_checks_actual_v90_source_and_ontology_without_claiming_execution(tmp_path):
    from xi_kari_runtime.validation_v4 import require_run_contract_v4, validate_preparation_v4

    contract, records = _source_prepared(tmp_path)
    assert require_run_contract_v4(contract, repository_root=ROOT) == ROOT
    validate_preparation_v4(tmp_path, contract=contract, repository_root=ROOT, records=records)
    assert len(records) == 2
    assert not (tmp_path / 'continuation/terminal-record.json').exists()


@pytest.mark.parametrize('relative,field', [
    ('source-lock.json', 'source_unit_count'),
    ('authoring/XK01-read-plan.json', 'framework_version'),
    ('authoring/XK01-semantic-read-trace.json', 'source_manifest_sha256'),
    ('authoring/XK04-ontology-read-trace.json', 'ontology_read_plan_sha256'),
])
def test_preparation_recomputes_source_and_ontology_tamper_even_without_event_hash_check(tmp_path, relative, field):
    from xi_kari_runtime.validation_v4 import validate_preparation_v4

    contract, records = _source_prepared(tmp_path)
    value = read_json(tmp_path / relative)
    value[field] = 'tampered-binding'
    atomic_write_json(tmp_path / relative, value)
    before = (tmp_path / relative).read_bytes()
    with pytest.raises(ValueError, match='source|read|ontology|trace|plan'):
        validate_preparation_v4(tmp_path, contract=contract, repository_root=ROOT, records=records)
    assert (tmp_path / relative).read_bytes() == before


def test_frozen_provider_environment_change_is_rejected(tmp_path, monkeypatch):
    from xi_kari_runtime.validation_v4 import require_run_contract_v4

    contract, _ = _source_prepared(tmp_path)
    monkeypatch.setenv('XI_KARI_PROVIDER_BASE_URL', 'https://changed.invalid')
    with pytest.raises(ValueError, match='environment'):
        require_run_contract_v4(contract, repository_root=ROOT)


def test_unsigned_complete_chain_does_not_gain_v4_terminal_authority(tmp_path):
    from xi_kari_runtime.terminal_authority import generate_terminal_authority
    from xi_kari_runtime.validation_v4 import validate_terminal_closure_v4

    authority, _ = generate_terminal_authority('unsigned-test')
    contract = {'run_id': 'unsigned-test', 'terminal_authority': authority}
    records = [{'phase': 'XK' + str(index), 'record_sha256': str(index).zfill(64)} for index in range(13)]
    terminal, errors = validate_terminal_closure_v4(tmp_path, contract, records, required=True)
    assert terminal is None
    assert errors == ['version-four signed terminal authority is missing']


def test_real_lamport_signature_requires_v4_fresh_completion_disk_closure(tmp_path):
    from xi_kari_runtime.terminal_authority import KEY_RELATIVE, commit_terminal_record, generate_terminal_authority
    from xi_kari_runtime.validation_v4 import validate_terminal_closure_v4

    authority, key = generate_terminal_authority('signature-test')
    contract = {'run_id': 'signature-test', 'terminal_authority': authority, 'repository_root': str(ROOT)}
    atomic_write_json(tmp_path / KEY_RELATIVE, key)
    records = [{'phase': 'XK' + str(index), 'record_sha256': str(index).zfill(64)} for index in range(13)]
    record = commit_terminal_record(tmp_path, contract, {'run_id': 'signature-test', 'terminal_state': 'complete', 'phase_count': 13, 'chain_head_sha256': records[-1]['record_sha256'], 'completion_sha256': 'a' * 64})
    assert record['schema_id'] == 'xi-kari.v3.terminal-record'
    assert not (tmp_path / KEY_RELATIVE).exists()
    terminal, errors = validate_terminal_closure_v4(tmp_path, contract, records, required=True)
    assert terminal is None
    assert errors == ['version-four signed completion closure is unreadable or invalid']
