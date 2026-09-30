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
    from xi_kari_runtime.packet_v4 import prepare_analysis_packet_v4
    from xi_kari_runtime.semantic_projection import semantic_atom_paths
    pending = prepare_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT)
    finalization = {'reader_sections': semantic['reader_sections'], 'visibility_ledger': {'entries': [
        {'canonical_path': path, 'classification': 'public', 'disclosure': 'include',
         'purpose': 'bounded source-scope analysis', 'authority_refs': [], 'protection_reason': None}
        for path in semantic_atom_paths(pending)
    ]}}
    packet = build_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT, reader_finalization=finalization)
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


def test_explicit_v4_static_production_rebuilds_base_packet_and_seals_actual_disk_chain(tmp_path):
    from tests.test_v4_pipeline_e2e_fixtures import BODY, CLOSED_MATERIALS, deterministic_provider, static_author_output
    from xi_kari_runtime import execution
    from xi_kari_runtime.validation_v4 import run_fresh_validator_v4

    _, problem, _, _, _ = static_author_output(mode='closed-input')
    problem['evidence_cutoff'] = '2030-01-01T00:00:00Z'
    transport = tmp_path / 'synthetic-production'
    transport.mkdir()
    provider, observation = deterministic_provider(transport)
    program = provider.read_text('utf-8').replace('prompt = sys.stdin.read()', "prompt = sys.stdin.buffer.read().decode('utf-8')")
    program = program.replace('运行时请求（只读绑定）：\\n', '运行时请求：\\n')
    program = program.replace('request = json.loads(', '''if 'REQUEST_JSON\\n' in prompt:
    request = json.loads(prompt.split('REQUEST_JSON\\n', 1)[1])
    from copy import deepcopy
    from xi_kari_runtime.semantic_projection import semantic_atom_paths, substantive_semantic_atoms
    view = deepcopy(request['task']['readonly_packet'])
    view['visibility_ledger'] = {'entries': [
        {'canonical_path': path, 'classification': 'public', 'disclosure': 'include', 'purpose': request['reader_requirements']['purpose'], 'authority_refs': [], 'protection_reason': None}
        for path in semantic_atom_paths(view)
    ]}
    section = {'section_id': 'synthetic-final-reader', 'heading': '合成条文与执行材料', 'local_judgment': '条文解释不产生现实执行资格。', 'paragraphs': list(BODY), 'source_bindings': []}
    for atom in substantive_semantic_atoms(view):
        excerpt = atom['public_text']
        section['paragraphs'].append('本题合成记录明确写明：' + excerpt + '。这一范围只用于合成条文程序验证，不证明现实执行或正式实例成立。')
        section['source_bindings'].append({'source_path': atom['canonical_path'], 'paragraph_index': len(section['paragraphs']), 'excerpt': excerpt})
    graph = request['material_context']['claim_mechanism_graph']
    result = {'semantic_response': {'reader_sections': [section], 'visibility_ledger': view['visibility_ledger']}, 'source_bindings': [{'claim_id': row['claim_id'], 'material_refs': row['claim_basis']['material_refs']} for row in graph['claims']]}
    pathlib.Path('semantic-output.json').write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
    pathlib.Path(sys.argv[sys.argv.index('--output-last-message') + 1]).write_text('SEMANTIC_OUTPUT_READY', encoding='utf-8')
    for event in ({'type': 'thread.started', 'thread_id': 'synthetic-final-reader'}, {'type': 'turn.started'}, {'type': 'turn.completed', 'usage': {'input_tokens': 11, 'output_tokens': 17}}):
        print(json.dumps(event), flush=True)
    raise SystemExit(0)
request = json.loads(''')
    program = program.replace('from tests.test_v4_pipeline_e2e_fixtures import static_author_output', 'from tests.test_v4_pipeline_e2e_fixtures import BODY, static_author_output')
    program = program.replace('if PROTECTED:', '''for index, assessment in enumerate(value["semantic_packet"]["retrieval"]["assessments"]):
    for field, statement in {"cannot_prove": "该合成条文只供程序验证，不能证明现实执行、经验效果或正式实例资格。", "affected_positions": "补偿安排涉及者的具体身份没有在给定合成条文中说明。", "low_power_positions": "给定合成条文未提供识别具体低权力位置所需的事实。"}.items():
        assessment[field] = [statement]
        value["semantic_packet"]["visibility_ledger"]["entries"].append({"canonical_path": "retrieval.assessments[" + str(index) + "]." + field + "[0]", "classification": "public", "disclosure": "include", "purpose": request["privacy_contract"]["purpose"], "authority_refs": [], "protection_reason": None})
for claim in value["semantic_packet"]["evidence"]["claims"]:
    for support in claim["support"]:
        if support.get("summary") == "A source-scope fixture.":
            support["summary"] = "该合成记录用于验证条文解释的材料范围。"
if PROTECTED:''')
    provider.write_text(program, encoding='utf-8', newline='\n')
    result = execution.execute_authored_run(transport / 'runs', problem_contract=problem,
        run_id='synthetic-v4-production', repository_root=ROOT,
        codex_provider_executable=provider, timeout_seconds=60, mode='closed-input',
        closed_input_materials=CLOSED_MATERIALS, contract_version=4, source_version='v9.0')
    assert read_json(observation)['synthetic'] is True
    assert read_json(observation)['actual_model_runs'] == 0
    run = Path(result['run_dir'])
    report = run_fresh_validator_v4(run, repository_root=ROOT)
    assert report['valid'] is report['complete'] is True
    assert report['phase_count'] == 13
    assert report['fresh_process'] is True
    assert not (run / 'continuation/terminal-authority-key.json').exists()
    assert (run / 'continuation/terminal-record.json').is_file()
    assert all(paragraph in (run / 'delivery/xi-kari-answer.md').read_text('utf-8') for paragraph in BODY)
    original = read_json(run / 'authoring/XK01-base-authoring-output.bin')
    limitations = original['semantic_packet']['retrieval']['assessments'][0]['cannot_prove']
    packet = read_json(run / 'continuation/input-packet.json')
    index = read_json(run / 'retrieval/index.json')
    assert packet['retrieval']['assessments'][0]['cannot_prove'] == limitations
    assert read_json(run / index['sources'][0]['assessment_path'])['cannot_prove'] == limitations
    assert limitations[0] in (run / 'delivery/xi-kari-answer.md').read_text('utf-8')
    from xi_kari_runtime.phase_chain import load_phase_records
    from xi_kari_runtime.validation_v4 import validate_terminal_closure_v4, validation_capture_paths_v4, validation_execution_for_report_v4
    records = load_phase_records(run)
    contract = read_json(run / 'run-contract.json')
    completion = read_json(run / 'continuation/completion.json')
    preseal = validation_execution_for_report_v4(run, read_json(run / 'validation/attempts/final/validator-report.json'), boundary='preseal', repository_root=ROOT)
    assert set(validation_capture_paths_v4(preseal)) <= {row['path'] for row in records[12]['artifact_bindings']}
    for field in ('official_validation_execution_path', 'promotion_validation_execution_path'):
        path = run / completion[field]
        prior = path.read_bytes()
        captured = read_json(path)
        captured['child_pid'] += 1
        try:
            atomic_write_json(path, captured)
            terminal, errors = validate_terminal_closure_v4(run, contract, records, required=True)
            assert terminal is None and errors
        finally:
            path.write_bytes(prior)
    assert validate_terminal_closure_v4(run, contract, records, required=True) == ('complete', [])


def test_production_gate_reopens_signed_process_proof_and_rejects_synthetic_model_flags(tmp_path):
    from tests.test_v4_semantic_executions import fixture_binding
    from tests.test_v4_stage_chain_integration import dynamic_inputs
    from xi_kari_runtime.semantic_executions_v4 import build_semantic_execution_request_v4, execute_semantic_request_v4
    from xi_kari_runtime.stage_consumers_v4 import validate_stage_chain_v4
    from xi_kari_runtime.validation_v4 import checked_execution_v4

    packet, contract = dynamic_inputs()
    controls = validate_stage_chain_v4(packet, run_contract=contract, repository_root=ROOT)
    author_request = controls['stage_results']['recursion']['result']['paths'][0]['nodes'][1]['author_request']
    request = build_semantic_execution_request_v4(packet, controls, run_contract=contract, kind='next_author', author_request=author_request, repository_root=ROOT)
    binding = fixture_binding(tmp_path)
    run = tmp_path / 'isolated-run'
    result = execute_semantic_request_v4(request, binding=binding, run_directory=run, repository_root=ROOT)
    assert result['status'] == 'executed'
    result['actual_model_execution'] = True
    result['semantic_gate'] = 'validated'
    with pytest.raises(ValueError, match='actual configured provider'):
        checked_execution_v4(result, expected_request=request, binding=binding, run_dir=run, original_run_dir=str(run), repository_root=ROOT)


@pytest.fixture(scope='module')
def replay_inputs_v4():
    from xi_kari_runtime.validation_v4 import prepare_packet_v4
    from xi_kari_runtime.stage_consumers_v4 import validate_stage_chain_v4

    semantic, contract = _packet_inputs()
    _, adapter = _provider_pair()
    contract['capability_snapshot'] = {'semantic_authoring_adapter': adapter}
    pending = prepare_packet_v4(semantic, contract=contract, repository_root=ROOT, domain_read_plan=None)
    controls = validate_stage_chain_v4(pending, run_contract=contract, repository_root=ROOT)
    return semantic, contract, pending, controls


def _replay_bundle_v4(tmp_path, replay_inputs_v4):
    semantic, contract, pending, controls = deepcopy(replay_inputs_v4)
    atomic_write_json(tmp_path / 'authoring/XK01-base-authoring-request.json', {'source_inputs': {}})
    bundle = {
        'schema_id': 'xi-kari.v4.production-author-executions', 'schema_version': 4,
        'run_id': contract['run_id'], 'run_directory': str(tmp_path),
        'semantic_base_sha256': sha256_json(semantic), 'prepared_packet_sha256': sha256_json(pending),
        'stage_controls': controls, 'provider_binding': None, 'next_author_executions': [],
        'probe_bundle': None, 'sensitivity_changes': [], 'reader_execution': None, 'reader_reused': True,
    }
    return semantic, contract, pending, bundle


def test_reused_reader_replay_rejects_unconsumed_provider_authority(tmp_path, replay_inputs_v4):
    from xi_kari_runtime.validation_v4 import replay_author_executions_v4

    semantic, contract, _, bundle = _replay_bundle_v4(tmp_path, replay_inputs_v4)
    bundle['provider_binding'] = {'kind': 'codex_provider', 'provider': contract['capability_snapshot']['semantic_authoring_adapter']['provider_binding']}
    with pytest.raises(ValueError, match='provider.*unused|unused.*provider'):
        replay_author_executions_v4(tmp_path, semantic, contract=contract, repository_root=ROOT, bundle=bundle)


@pytest.mark.parametrize('field', ['executable_path', 'model', 'timeout_seconds', 'argv_sha256'])
def test_reader_execution_replay_requires_exact_frozen_provider(tmp_path, monkeypatch, replay_inputs_v4, field):
    from xi_kari_runtime import validation_v4

    semantic, contract, pending, bundle = _replay_bundle_v4(tmp_path, replay_inputs_v4)
    provider = deepcopy(contract['capability_snapshot']['semantic_authoring_adapter']['provider_binding'])
    provider[field] = 19 if field == 'timeout_seconds' else 'unfrozen-provider'
    bundle.update(provider_binding={'kind': 'codex_provider', 'provider': provider}, reader_execution={}, reader_reused=False)
    consumed = []

    def synthetic_reader(*args, **kwargs):
        consumed.append(True)
        return {'semantic_response': {'reader_sections': pending['reader_sections'], 'visibility_ledger': pending['visibility_ledger']}}

    monkeypatch.setattr(validation_v4, 'checked_execution_v4', synthetic_reader)
    with pytest.raises(ValueError, match='frozen.*provider|provider.*frozen'):
        validation_v4.replay_author_executions_v4(tmp_path, semantic, contract=contract, repository_root=ROOT, bundle=bundle)
    assert consumed == []


@pytest.fixture(scope='module')
def rejected_fresh_capture_v4(tmp_path_factory):
    from xi_kari_runtime.validation_v4 import run_fresh_validator_v4

    run = tmp_path_factory.mktemp('synthetic-rejected-fresh-capture')
    atomic_write_json(run / 'run-contract.json', {'schema_id': 'xi-kari.v4.run-contract', 'schema_version': 4})
    report = run_fresh_validator_v4(run, repository_root=ROOT, require_complete=False)
    assert report['valid'] is False
    return run


def test_failed_fresh_validation_remains_a_readonly_process_record(rejected_fresh_capture_v4):
    from xi_kari_runtime.validation_v4 import validate_validation_execution_v4

    run = rejected_fresh_capture_v4
    path = next((run / 'validation/attempts').glob('final-*/execution.json'))
    before = {item.name: item.read_bytes() for item in path.parent.iterdir()}
    capture = validate_validation_execution_v4(run, path.relative_to(run).as_posix(), repository_root=ROOT)
    assert capture['report']['valid'] is False
    assert capture['execution']['exit_status'] == 2
    assert {item.name: item.read_bytes() for item in path.parent.iterdir()} == before


@pytest.mark.parametrize('mutation', ['stdout_bytes', 'stderr_bytes', 'command', 'child_pid', 'report_bytes', 'environment'])
def test_disk_validation_consumes_physical_fresh_process_receipt(tmp_path, rejected_fresh_capture_v4, mutation):
    import shutil
    from xi_kari_runtime.validation_v4 import validate_json_artifact_ownership_v4

    run = tmp_path / 'copy'
    shutil.copytree(rejected_fresh_capture_v4, run)
    attempt = next((run / 'validation/attempts').glob('final-*'))
    execution = read_json(attempt / 'execution.json')
    if mutation in {'stdout_bytes', 'stderr_bytes'}:
        path = attempt / ('stdout.bin' if mutation == 'stdout_bytes' else 'stderr.bin')
        path.write_bytes(path.read_bytes() + b'\n')
    elif mutation == 'report_bytes':
        path = attempt / 'validator-report.json'
        path.write_bytes(path.read_bytes() + b'\n')
    else:
        if mutation == 'command':
            execution['command'][-1] = '--invented-boundary'
            execution['command_sha256'] = sha256_json(execution['command'])
        elif mutation == 'child_pid':
            execution['child_pid'] += 1
        elif mutation == 'environment':
            execution['provider_environment_sha256'] = '0' * 64
        atomic_write_json(attempt / 'execution.json', execution)
    errors = validate_json_artifact_ownership_v4(run, ROOT)
    assert any('validation execution' in error for error in errors), errors


def test_signed_terminal_cannot_promote_marker_only_fresh_report(tmp_path):
    from xi_kari_runtime.canonical_json import sha256_file
    from xi_kari_runtime.terminal_authority import COMPLETION_RELATIVE, KEY_RELATIVE, OFFICIAL_REPORT_RELATIVE, TRANSACTION_RELATIVE, commit_terminal_record, generate_terminal_authority
    from xi_kari_runtime.validation_v4 import validate_terminal_closure_v4

    authority, key = generate_terminal_authority('synthetic-marker-completion')
    contract = {'run_id': 'synthetic-marker-completion', 'terminal_authority': authority, 'repository_root': str(ROOT), 'validator_set_sha256': 'a' * 64, 'provider_environment_sha256': 'b' * 64}
    records = [{'phase': 'XK' + str(index), 'record_sha256': str(index).zfill(64)} for index in range(13)]
    official = {'schema_id': 'xi-kari.v4.validator-report', 'run_id': contract['run_id'], 'fresh': True, 'fresh_process': True, 'validation_boundary': 'official', 'valid': True, 'validated_phase': 'XK12', 'phase_count': 13, 'chain_head_sha256': records[-1]['record_sha256'], 'validator_set_sha256': contract['validator_set_sha256']}
    atomic_write_json(tmp_path / OFFICIAL_REPORT_RELATIVE, official)
    atomic_write_json(tmp_path / 'artifacts/artifact-manifest.json', {})
    atomic_write_json(tmp_path / 'delivery/final-chat.json', {'validation_authority_path': COMPLETION_RELATIVE})
    atomic_write_json(tmp_path / TRANSACTION_RELATIVE, {'state': 'official_validated'})
    completion = {
        'schema_id': 'xi-kari.v4.completion', 'schema_version': 4, 'run_id': contract['run_id'],
        'official_validation_path': OFFICIAL_REPORT_RELATIVE, 'official_validation_sha256': sha256_file(tmp_path / OFFICIAL_REPORT_RELATIVE),
        'chain_head_sha256': records[-1]['record_sha256'], 'phase_count': 13, 'validator_set_sha256': contract['validator_set_sha256'],
        'manifest_sha256': sha256_file(tmp_path / 'artifacts/artifact-manifest.json'), 'final_chat_sha256': sha256_file(tmp_path / 'delivery/final-chat.json'),
        'xk12_transaction_sha256': sha256_file(tmp_path / TRANSACTION_RELATIVE), 'provider_environment_sha256': contract['provider_environment_sha256'],
        'completed_at': '2026-09-30T05:00:00Z',
    }
    atomic_write_json(tmp_path / COMPLETION_RELATIVE, completion)
    atomic_write_json(tmp_path / KEY_RELATIVE, key)
    commit_terminal_record(tmp_path, contract, {'run_id': contract['run_id'], 'terminal_state': 'complete', 'phase_count': 13, 'chain_head_sha256': records[-1]['record_sha256'], 'completion_sha256': sha256_file(tmp_path / COMPLETION_RELATIVE)})
    terminal, errors = validate_terminal_closure_v4(tmp_path, contract, records, required=True)
    assert terminal is None
    assert errors


@pytest.mark.parametrize('directory', ['sem', 'semantic-executions'])
def test_semantic_execution_replay_owns_short_and_historical_run_paths(tmp_path, directory):
    from xi_kari_runtime.validation_v4 import _expected_root_ids_v4, _rebased_execution_v4

    original = tmp_path / 'original'
    candidate = tmp_path / 'candidate'
    relative = directory + '/attempt-' + 'a' * 32
    (candidate / relative).mkdir(parents=True)
    rebased = _rebased_execution_v4({'attempt_directory': str(original / relative)}, run_dir=candidate, original_run_dir=str(original))
    assert rebased['attempt_directory'] == str(candidate / relative)
    assert _expected_root_ids_v4(relative + '/capture/request.json') == {'xi-kari.v4.xk.semantic-execution-request'}
    assert _expected_root_ids_v4(relative + '/capture/receipt.json') == {'xi-kari.v4.xk.semantic-execution-attestation'}
    assert _expected_root_ids_v4('extra/' + relative + '/capture/request.json') is None
    with pytest.raises(ValueError, match='not owned'):
        _rebased_execution_v4({'attempt_directory': str(original / relative / 'nested')}, run_dir=candidate, original_run_dir=str(original))
    with pytest.raises(ValueError, match='outside'):
        _rebased_execution_v4({'attempt_directory': str(tmp_path / relative)}, run_dir=candidate, original_run_dir=str(original))


@pytest.mark.parametrize('mutation', ['unchanged', 'content_utf8', 'content_witness', 'missing_item', 'duplicate_item'])
def test_domain_author_input_replay_consumes_original_scoped_bytes(tmp_path, mutation):
    from xi_kari_runtime.domain_pipeline_v4 import prepare_domain_inputs
    from xi_kari_runtime.validation_v4 import domain_plan_v4

    prepared = prepare_domain_inputs(['D.04'], run_id='synthetic-domain-replay', problem_contract_sha256='a' * 64, repository_root=ROOT)
    inputs = {'plan': prepared['plan'], 'author_inputs': [{key: item[key] for key in ('domain_id', 'content_utf8', 'content_witness')} for item in prepared['author_inputs']]}
    atomic_write_json(tmp_path / 'authoring/XK04-domain-read-plan.json', inputs['plan'])
    if mutation == 'unchanged':
        assert domain_plan_v4(tmp_path, {'source_inputs': {'domain_inputs': inputs}}) == inputs['plan']
        return
    if mutation == 'missing_item':
        inputs['author_inputs'] = []
    elif mutation == 'duplicate_item':
        inputs['author_inputs'].append(deepcopy(inputs['author_inputs'][0]))
    else:
        inputs['author_inputs'][0][mutation] = 'tampered-domain-input'
    with pytest.raises(ValueError, match='domain.*input|input.*domain'):
        domain_plan_v4(tmp_path, {'source_inputs': {'domain_inputs': inputs}})


def test_production_retrieval_does_not_invent_missing_author_limitations(tmp_path):
    from tests.test_v4_pipeline_e2e_fixtures import static_author_output
    from xi_kari_runtime.retrieval import materialize_retrieval_bundle

    value, _, _, _, _ = static_author_output(mode='closed-input')
    retrieval = value['semantic_packet']['retrieval']
    assert retrieval['assessments'][0]['cannot_prove'] == []
    before = deepcopy(retrieval)
    with pytest.raises(ValueError, match='cannot_prove'):
        materialize_retrieval_bundle(tmp_path, retrieval['sources'], retrieval['assessments'], mode='closed-input', run_id='synthetic-empty-limit')
    assert retrieval == before
    assert not (tmp_path / 'retrieval/index.json').exists()


def test_reader_materialization_is_independent_of_author_dictionary_order(replay_inputs_v4):
    from xi_kari_runtime.canonical_json import canonical_bytes, read_json_text
    from xi_kari_runtime.semantic_projection import typed_semantic_atoms
    from xi_kari_runtime.validation_v4 import reader_payload_v4

    _, contract, pending, _ = deepcopy(replay_inputs_v4)
    from_disk = read_json_text(canonical_bytes(pending).decode('utf-8'))
    authored_order = typed_semantic_atoms(reader_payload_v4(pending, contract))
    disk_order = typed_semantic_atoms(reader_payload_v4(from_disk, contract))
    assert authored_order == disk_order


@pytest.mark.parametrize('relative,accepted', [
    ('authoring/XK01-base-authoring-stderr.bin', True),
    ('sem/attempt-' + 'a' * 32 + '/capture/stderr.bin', True),
    ('semantic-executions/attempt-' + 'a' * 32 + '/capture/stderr.bin', True),
    ('authoring/XK01-base-authoring-output.bin', False),
    ('sem/attempt-' + 'a' * 32 + '/capture/output.bin', False),
    ('unknown/stderr.bin', False),
])
def test_manifest_accepts_empty_success_stderr_only(relative, accepted):
    from jsonschema import Draft202012Validator
    from xi_kari_runtime.canonical_json import sha256_bytes

    record = {'path': relative, 'sha256': sha256_bytes(b''), 'bytes': 0}
    manifest = {
        'schema_id': 'xi-kari.v4.artifact-manifest', 'schema_version': 4,
        'runtime_version': '4.0.0', 'artifact_schema_version': 4, 'source_version': 'v9.0',
        'run_id': 'synthetic-empty-stderr', 'input_packet_sha256': 'a' * 64,
        'candidate_census_sha256': 'a' * 64, 'validated_chain_head_sha256': 'a' * 64,
        'validator_set_sha256': 'a' * 64, 'phase_responsibilities': {},
        'phase_artifacts': {'XK1': [record]},
        'delivery': {name: {'path': 'delivery/' + name, 'sha256': 'a' * 64, 'bytes': 1} for name in ('answer', 'dossier', 'atlas', 'casebook', 'artifact_index', 'final_chat')},
    }
    assert Draft202012Validator(read_json(ROOT / 'schemas/xk-v4-production-manifest.schema.json')).is_valid(manifest) is accepted


@pytest.mark.parametrize('unreadable_report', [False, True])
def test_failed_promotion_capture_survives_candidate_cleanup(tmp_path, monkeypatch, unreadable_report):
    from xi_kari_runtime import materialization_v4 as materializer
    from xi_kari_runtime.canonical_json import atomic_write_bytes

    run = tmp_path / 'synthetic-failed-promotion'
    run.mkdir()
    relative = 'validation/attempts/promotion-' + 'a' * 32 + '/execution.json'
    failed = {'valid': False, 'errors': ['synthetic refusal']}

    def synthetic_validator(directory, **arguments):
        if arguments.get('preseal'):
            return {'valid': True}
        assert arguments.get('promotion') is True
        capture = directory / Path(relative).parent
        atomic_write_json(capture / 'execution.json', {'synthetic': True, 'exit_status': 2})
        atomic_write_json(capture / 'validator-report.json', failed)
        atomic_write_bytes(capture / 'stdout.bin', b'synthetic failed validation capture')
        atomic_write_bytes(capture / 'stderr.bin', b'')
        if unreadable_report:
            raise ValueError('synthetic unreadable validator report')
        return failed

    monkeypatch.setattr(materializer, 'run_fresh_validator_v4', synthetic_validator)
    monkeypatch.setattr(materializer, 'validation_execution_for_report_v4', lambda *args, **kwargs: relative)
    monkeypatch.setattr(materializer, '_set_state', lambda *args, **kwargs: None)
    monkeypatch.setattr(materializer, '_append', lambda *args, **kwargs: None)
    monkeypatch.setattr(materializer, 'load_phase_records', lambda *args: [])
    monkeypatch.setattr(materializer, 'build_manifest_v4', lambda *args, **kwargs: {})
    with pytest.raises(ValueError, match='synthetic unreadable validator report' if unreadable_report else 'fresh promotion validation failed'):
        materializer._complete(run, packet={}, contract={'run_id': 'synthetic-failed-promotion'}, repository_root=ROOT, packet_sha256='a' * 64)
    assert read_json(run / Path(relative).parent / 'validator-report.json') == failed
    assert (run / Path(relative).parent / 'stdout.bin').read_bytes() == b'synthetic failed validation capture'
    assert not list(tmp_path.glob('.synthetic-failed-promotion.xk12-*'))


def test_base_request_accepts_only_the_closed_temporal_context_binding():
    from jsonschema import Draft202012Validator
    from tests.test_p04_v4_authoring import _authoring_input
    from xi_kari_runtime.execution import _base_request

    _, problem, plan, lock, _ = _authoring_input()
    provider, _ = _provider_pair()
    request = _base_request(run_id=plan['run_id'], mode='open-world', problem_contract=problem,
        repository_root=ROOT, source_lock=lock, read_plan={}, concept_authority={},
        privacy_contract={}, ontology_read_plan=plan, base_provider_binding=provider)
    schema = read_json(ROOT / 'schemas/xk-v4-base-authoring-request.schema.json')
    validator = Draft202012Validator({'$defs': schema['$defs'], **schema['properties']['source_inputs']})
    inputs = request['source_inputs']
    assert validator.is_valid(inputs)
    binding = {'context_sha256': 'a' * 64, 'audit_sha256': 'b' * 64, 'evidence_scope': 'isolated_runtime_reads'}
    inputs['temporal_audit_binding'] = binding
    assert validator.is_valid(inputs)
    for field in binding:
        bad = deepcopy(inputs)
        bad['temporal_audit_binding'].pop(field)
        assert not validator.is_valid(bad)
    for field, value in (('origin_run_directory', 'private-origin'), ('evidence_scope', 'qualified'), ('context_sha256', 'unbound')):
        bad = deepcopy(inputs)
        bad['temporal_audit_binding'][field] = value
        assert not validator.is_valid(bad)
