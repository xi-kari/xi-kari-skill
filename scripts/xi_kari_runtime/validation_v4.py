"""Disk-authoritative validation of isolated source-v9.0 production runs."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any
import uuid

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from .authority import authority_paths, repository_root as resolve_repository_root
from .canonical_json import (
    atomic_write_bytes, atomic_write_json, canonical_bytes, confined_path, read_bounded_regular_file, read_json,
    read_json_text, sha256_bytes, sha256_file, sha256_json,
)
from .claims import validate_claim_graph
from .concept_authority import load_concept_authority
from .contracts import (
    DELIVERY_PATHS, PHASE_RESPONSIBILITIES, build_runtime_packet_binding,
    validate_execute_owned_binding,
)
from .coverage import build_semantic_coverage, load_reader_outputs
from .ontology_read_trace import build_ontology_read_trace, validate_ontology_read_trace
from .packet_v4 import require_packet_contract_v4, validate_world_stage
from .phase_chain import PHASES, validate_phase_chain
from .problem_contract import contract_hash, stance_neutrality_key, validate_problem_contract
from .prose import (
    build_prose_plan, check_plain_language, render_artifact_index, render_reader_outputs,
)
from .retrieval import (
    _normalise_source, materialize_retrieval_bundle, validate_full_source_lock,
    validate_retrieval_bundle,
)
from .semantic_projection import protected_retrieval_values, typed_semantic_atoms
from .semantic_read_trace import validate_semantic_read_trace
from .terminal_authority import (
    COMPLETION_RELATIVE, OFFICIAL_REPORT_RELATIVE, TERMINAL_RELATIVE,
    TRANSACTION_RELATIVE, verify_terminal_record,
)
from .v4_contracts import validate_versioned_schema

RUNTIME_VERSION_V4 = '4.0.0'
PRODUCTION_PROFILE_V4 = 'production-authoring-v4'
DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ENVIRONMENT_FIELDS = (
    'XI_KARI_PROVIDER_MODEL', 'XI_KARI_REASONING_EFFORT',
    'XI_KARI_PROVIDER_BASE_URL', 'XI_KARI_PROVIDER_WIRE_API',
)
PACKET_RELATIVE = 'continuation/input-packet.json'
STDERR_RELATIVE = 'authoring/XK01-base-authoring-stderr.bin'
SOURCE_TRACE_INPUT_RELATIVE = 'authoring/XK01-semantic-read-trace-input.json'
ONTOLOGY_TRACE_INPUT_RELATIVE = 'authoring/XK04-ontology-read-trace-input.json'
_CUSTOM_SOURCE_IDS = frozenset({
    'xi-kari.v4.source-lock', 'xi-kari.v4.source-read-event',
    'xi-kari.v4.semantic-read-trace',
})


def utc_now_v4() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def provider_environment_sha256_v4() -> str:
    return sha256_json({field: os.environ.get(field) for field in ENVIRONMENT_FIELDS})


provider_environment_sha256 = provider_environment_sha256_v4


def validator_set_sha256_v4(repository_root: Path) -> str:
    root = resolve_repository_root(repository_root)
    paths = set(authority_paths(root))
    for directory in ('references/source/v9.0', 'references/ontology/v9.0', 'references/domains'):
        base = root / directory
        if not base.is_dir() or base.is_symlink():
            raise ValueError('version-four source, ontology or domain authority is missing')
        for path in base.rglob('*'):
            if path.is_symlink():
                raise ValueError('version-four authority contains a symlink')
            if path.is_file():
                paths.add(path)
    from .source_profile import get_source_profile
    paths.add(get_source_profile('v9.0').source_document(root))
    return sha256_json([
        {'path': path.relative_to(root).as_posix(), 'sha256': sha256_file(path)}
        for path in sorted(paths)
    ])


def phase_input_sha256_v4(previous: Mapping[str, Any] | None, value: Any) -> str:
    return sha256_json({'predecessor': previous.get('record_sha256') if previous else None, 'value': value})


def _root_schema_ids(schema: Any, *, document: Mapping[str, Any] | None = None, references: frozenset[str] = frozenset()) -> set[str]:
    if not isinstance(schema, Mapping):
        return set()
    document = document if document is not None else schema
    result: set[str] = set()
    identity = schema.get('properties', {}).get('schema_id', {})
    if isinstance(identity, Mapping):
        if isinstance(identity.get('const'), str):
            result.add(identity['const'])
        result.update(value for value in identity.get('enum', []) if isinstance(value, str))
    for keyword in ('oneOf', 'anyOf', 'allOf'):
        for branch in schema.get(keyword, []):
            result.update(_root_schema_ids(branch, document=document, references=references))
    reference = schema.get('$ref')
    if isinstance(reference, str) and reference.startswith('#/') and reference not in references:
        target: Any = document
        for token in reference[2:].split('/'):
            token = token.replace('~1', '/').replace('~0', '~')
            if not isinstance(target, Mapping) or token not in target:
                target = None
                break
            target = target[token]
        result.update(_root_schema_ids(target, document=document, references=references | {reference}))
    return result


def schema_registry_v4(repository_root: Path) -> tuple[dict[str, Path], list[str]]:
    registry: dict[str, Path] = {}
    uris: dict[str, Path] = {}
    errors: list[str] = []
    for path in sorted((Path(repository_root) / 'schemas').glob('*.json')):
        try:
            schema = read_json(path)
            Draft202012Validator.check_schema(schema)
            uri = schema.get('$id')
            if isinstance(uri, str):
                previous = uris.setdefault(uri, path)
                if previous != path:
                    errors.append('duplicate root schema URI: ' + path.name)
            for identity in _root_schema_ids(schema):
                if not identity.startswith(('xi-kari.v3.', 'xi-kari.v4.')):
                    continue
                previous = registry.setdefault(identity, path)
                if previous != path:
                    errors.append('duplicate root schema owner: ' + identity)
        except Exception:
            errors.append('invalid schema resource: ' + path.name)
    return registry, errors


def _expected_root_ids_v4(relative: str) -> set[str] | None:
    exact = {
        'run-contract.json': {'xi-kari.v4.run-contract'},
        'capability-snapshot.json': {'xi-kari.v4.capability-snapshot'},
        'source-lock.json': {'xi-kari.v4.source-lock'},
        'authoring/XK01-read-plan.json': {'xi-kari.v4.read-plan'},
        'authoring/XK01-read-events.jsonl': {'xi-kari.v4.source-read-event'},
        'authoring/XK01-semantic-read-trace.json': {'xi-kari.v4.semantic-read-trace'},
        SOURCE_TRACE_INPUT_RELATIVE: {'xi-kari.v4.semantic-read-trace-input'},
        ONTOLOGY_TRACE_INPUT_RELATIVE: {'xi-kari.v3.ontology-read-trace-input'},
        'authoring/XK01-base-authoring-request.json': {'xi-kari.v4.base-authoring-request'},
        PACKET_RELATIVE: {'xi-kari.v4.analysis-packet'},
        'artifacts/artifact-manifest.json': {'xi-kari.v4.artifact-manifest'},
        DELIVERY_PATHS['final_chat']: {'xi-kari.v4.final-chat'},
        COMPLETION_RELATIVE: {'xi-kari.v4.completion'},
        'validation/attempts/final/validator-report.json': {'xi-kari.v4.validator-report'},
        OFFICIAL_REPORT_RELATIVE: {'xi-kari.v4.validator-report'},
    }
    if relative in exact:
        return exact[relative]
    from .contracts import expected_phase_artifact_paths
    wrapped = {path for phase in PHASES[2:12] for path in expected_phase_artifact_paths(phase, contract_profile='production-authoring-v3', mode='closed-input')
               if path.startswith('authoring/') and path not in {'authoring/XK02-semantic-retrieval.json', 'authoring/XK02-retrieval-execution-receipt.json', 'authoring/XK04-ontology-read-plan.json', 'authoring/XK04-ontology-read-trace.json'}}
    if relative in wrapped:
        return {'xi-kari.v4.production-phase-artifact'}
    path = Path(relative)
    if path.match('validation/attempts/*/execution.json'):
        return {'xi-kari.v4.validation-execution'}
    if path.match('validation/attempts/*/validator-report.json'):
        return {'xi-kari.v4.validator-report'}
    from .validation import _expected_artifact_schema_ids
    return _expected_artifact_schema_ids(relative)


def validate_json_artifact_ownership_v4(run_dir: Path, repository_root: Path) -> list[str]:
    owners, errors = schema_registry_v4(repository_root)
    resources = Registry()
    for path in sorted((repository_root / 'schemas').glob('*.json')):
        schema = read_json(path)
        if isinstance(schema.get('$id'), str):
            resources = resources.with_resource(schema['$id'], Resource.from_contents(schema))
    for path in sorted(Path(run_dir).rglob('*')):
        if not path.is_file() or path.suffix not in {'.json', '.jsonl'}:
            continue
        relative = path.relative_to(run_dir).as_posix()
        if relative == 'authoring/XK01-base-authoring-events.jsonl':
            continue
        expected_ids = _expected_root_ids_v4(relative)
        if expected_ids is None:
            errors.append('artifact path has no runtime owner: ' + relative)
            continue
        try:
            values = [read_json_text(line) for line in path.read_text('utf-8').splitlines() if line.strip()] if path.suffix == '.jsonl' else [read_json(path)]
        except Exception:
            errors.append('unreadable JSON artifact: ' + relative)
            continue
        for value in values:
            identity = value.get('schema_id') if isinstance(value, Mapping) else None
            if identity not in expected_ids:
                errors.append('artifact path root schema owner differs: ' + relative)
                continue
            if identity in _CUSTOM_SOURCE_IDS and identity not in owners:
                continue
            owner = owners.get(identity)
            if owner is None:
                errors.append('unknown root schema owner: ' + relative)
                continue
            validator = Draft202012Validator(read_json(owner), format_checker=FormatChecker(), registry=resources)
            try:
                failure = next(validator.iter_errors(value), None)
            except Exception:
                failure = True
            if failure is not None:
                errors.append('artifact root schema contract failed: ' + relative)
    return errors


def require_run_contract_v4(contract: Mapping[str, Any], *, repository_root: Path | None = None) -> Path:
    if (contract.get('schema_id'), contract.get('schema_version'), contract.get('runtime_version'), contract.get('source_version'), contract.get('contract_profile')) != ('xi-kari.v4.run-contract', 4, RUNTIME_VERSION_V4, 'v9.0', PRODUCTION_PROFILE_V4):
        raise ValueError('incompatible version-four production run identity; source v9.0 is required')
    bound = resolve_repository_root(Path(str(contract.get('repository_root', ''))))
    if repository_root is not None and resolve_repository_root(repository_root) != bound:
        raise ValueError('supplied repository root differs from the version-four run')
    validate_versioned_schema('xk-v4-production-run.schema.json', contract, repository_root=bound)
    problem = validate_problem_contract(contract['problem_contract'], mode=contract['mode'])
    if contract['question'] != problem['question'] or contract['problem_contract_sha256'] != contract_hash(problem):
        raise ValueError('version-four frozen problem differs from its run binding')
    if contract['evidence_cutoff'] != problem['evidence_cutoff'] or contract['stance_neutrality_key'] != stance_neutrality_key(problem, mode=contract['mode']):
        raise ValueError('version-four cutoff or neutrality binding differs')
    if contract['validator_set_sha256'] != validator_set_sha256_v4(bound):
        raise ValueError('repository authority differs from the version-four run contract')
    if contract['provider_environment_sha256'] != provider_environment_sha256_v4():
        raise ValueError('provider environment differs from execute')
    capability = contract['capability_snapshot']
    if capability['network_retrieval'] != (contract['mode'] == 'open-world'):
        raise ValueError('version-four network capability differs from evidence mode')
    if contract['continuation'] != {'kind': 'original', 'generation': 0, 'parent_run_id': None, 'parent_chain_head_sha256': None}:
        raise ValueError('version-four continuation lineage is not integrated')
    return bound


def _phase_document(packet: Mapping[str, Any], contract: Mapping[str, Any], phase: str, kind: str, payload: Any, result: Mapping[str, Any], packet_sha256: str) -> dict[str, Any]:
    return {
        'schema_id': 'xi-kari.v4.production-phase-artifact', 'schema_version': 4,
        'run_id': contract['run_id'], 'phase': phase, 'kind': kind,
        'input_packet_sha256': packet_sha256, 'payload': deepcopy(payload), 'result': deepcopy(dict(result)),
    }


def _stage_results(packet: Mapping[str, Any], contract: Mapping[str, Any], repository_root: Path) -> dict[str, Any]:
    try:
        from .stage_consumers_v4 import validate_stage_chain_v4
    except ModuleNotFoundError as exc:
        if exc.name != __package__ + '.stage_consumers_v4':
            raise
        result = {}
        for stage, applicability in packet['applicability'].items():
            if applicability['status'] == 'applicable':
                if stage != 'world_state':
                    raise ValueError(stage + ' version-four production consumer is not integrated')
                actual = validate_world_stage(packet['local_world_model'], evidence_ledger=packet['evidence'], retrieval_index=packet['retrieval'], repository_root=repository_root)
                result[stage] = {'applicability': applicability, 'evaluated': True, 'result': actual}
            else:
                result[stage] = {'applicability': applicability, 'evaluated': False}
        return result
    bundle = validate_stage_chain_v4(packet, run_contract=contract, repository_root=repository_root)
    stages = bundle.get('stage_results')
    if not isinstance(stages, Mapping) or set(stages) != set(packet['applicability']):
        raise ValueError('version-four stage consumer did not return all actual stage results')
    return {stage: {'applicability': packet['applicability'][stage], 'evaluated': row.get('validation_status') == 'validated', **dict(row)} for stage, row in stages.items()}


def build_semantic_phase_artifacts_v4(packet: Mapping[str, Any], *, contract: Mapping[str, Any], repository_root: Path, input_packet_sha256: str | None = None) -> dict[str, dict[str, Any]]:
    require_packet_contract_v4(packet, mode=contract['mode'], run_contract=contract, repository_root=repository_root)
    packet_sha256 = input_packet_sha256 or sha256_json(packet)
    stages = _stage_results(packet, contract, repository_root)
    registry = None
    if 'empirical_instances' in packet or 'derived_instances' in packet:
        from .formal_results import rebuild_instance_registry
        registry = rebuild_instance_registry(packet.get('empirical_instances', []), graph=packet['claim_mechanism_graph'], derived_instances=packet.get('derived_instances', []), evidence_mode=contract['mode'], repository_root=repository_root)
    graph = validate_claim_graph(packet['claim_mechanism_graph'], evidence_mode=contract['mode'], repository_root=repository_root, verified_instance_results=registry)
    dispositions, closure = load_concept_authority(repository_root, source_version='v9.0')
    if packet['concept_disposition'] != dispositions:
        raise ValueError('version-four packet candidate dispositions differ from source authority')
    documents: dict[str, dict[str, Any]] = {phase: {} for phase in PHASES[2:11]}

    def add(phase: str, suffix: str, kind: str, payload: Any, result: Mapping[str, Any]) -> None:
        documents[phase]['authoring/' + suffix + '.json'] = _phase_document(packet, contract, phase, kind, payload, result, packet_sha256)

    add('XK2', 'XK02-retrieval-ledger', 'retrieval-ledger', packet['retrieval'], {'mode': contract['mode'], 'source_count': len(packet['retrieval']['sources'])})
    add('XK3', 'XK03-evidence-ledger', 'evidence-ledger', packet['evidence'], {'evidence_count': len(packet['evidence']['evidence']), 'claim_count': len(packet['evidence'].get('claims', []))})
    add('XK3', 'XK03-unknown-register', 'unknown-register', packet['facts']['unknown'], {'evidence_cutoff': contract['evidence_cutoff'], 'unsupported_claim_ids': packet['evidence'].get('unsupported_claims', [])})
    add('XK4', 'XK04-concept-disposition', 'concept-disposition', dispositions, closure)
    add('XK4', 'XK04-concept-closure-report', 'concept-closure-report', closure, {'unresolved': 0, 'candidate_count': len(dispositions), 'complete': True})
    add('XK5', 'XK05-local-world-model', 'local-world-model', packet.get('local_world_model'), stages['world_state'])
    add('XK6', 'XK06-transformation-ledger', 'transformation-ledger', packet.get('transformation_ledger'), stages['transformation'])
    add('XK6', 'XK06-cascade', 'cascade', packet.get('cascade'), stages['transformation'])
    add('XK7', 'XK07-claim-mechanism-graph', 'claim-mechanism-graph', packet['claim_mechanism_graph'], graph)
    add('XK7', 'XK07-case-ledger', 'case-ledger', packet['case_ledger'], {'case_count': len(packet['case_ledger'].get('cases', [])), 'cases': packet['cases']})
    add('XK8', 'XK08-recursive-lineage', 'recursive-lineage', {'lineage': packet.get('recursive_lineage'), 'states': packet.get('recursive_states')}, stages['recursion'])
    requires_probes = any(row['status'] == 'applicable' for row in packet['applicability'].values())
    probe = {'evaluated': False, 'status': 'required_but_not_integrated' if requires_probes else 'not_applicable', 'reason': 'Fresh semantic probe author execution is required for applicable dynamics.' if requires_probes else 'Every dynamic stage is source-bound not applicable.'}
    for suffix, kind, field in (
        ('XK09-semantic-authoring-bundle', 'semantic-authoring-bundle', None),
        ('XK09-order-evaluation', 'order-evaluation', 'order_evaluation'),
        ('XK09-red-team-report', 'red-team-report', 'red_team'),
        ('XK09-stance-pair', 'stance-pair', 'stance_pair'),
        ('XK09-sensitivity-report', 'sensitivity-report', None),
        ('XK09-stance-stability-report', 'stance-stability-report', None),
    ):
        add('XK9', suffix, kind, packet.get(field) if field else None, probe)
    add('XK10', 'XK10-verdict', 'verdict', packet.get('verdict'), {'formal_claim_results': packet.get('formal_results'), 'mechanism': stages['mechanism']})
    add('XK10', 'XK10-action-ranking', 'action-ranking', packet.get('action_ranking'), stages['action_choice'])
    add('XK10', 'XK10-forecast-ledger', 'forecast-ledger', packet.get('forecast'), stages['forecast'])
    add('XK10', 'XK10-framework-gap-ledger', 'framework-gap-ledger', packet.get('framework_gap'), {'source_undefined_remains_undefined': True})
    return documents


def expected_phase_paths_v4(phase: str, *, mode: str, run_dir: Path | None = None) -> tuple[str, ...]:
    from .contracts import expected_phase_artifact_paths
    paths = list(expected_phase_artifact_paths(phase, contract_profile='production-authoring-v3', mode=mode))
    if phase == 'XK1':
        paths.extend((STDERR_RELATIVE, SOURCE_TRACE_INPUT_RELATIVE))
    if phase == 'XK4':
        paths.append(ONTOLOGY_TRACE_INPUT_RELATIVE)
    if phase == 'XK2' and run_dir is not None and (run_dir / 'retrieval/index.json').is_file():
        index = read_json(run_dir / 'retrieval/index.json')
        paths.extend(sorted({row[field] for row in index['sources'] for field in ('source_path', 'assessment_path')}))
    return tuple(paths)


def phase_artifact_paths_v4(phase: str, mode: str | None = None) -> tuple[str, ...]:
    return expected_phase_paths_v4(phase, mode=mode or 'open-world')


def semantic_phase_input_v4(run_dir: Path, phase: str, *, packet_sha256: str, paths: tuple[str, ...]) -> dict[str, Any]:
    return {'packet_sha256': packet_sha256, 'phase': phase, 'artifacts': [{'path': relative, 'sha256': sha256_file(confined_path(run_dir, relative, must_exist=True))} for relative in paths]}


def _read_jsonl(path: Path) -> list[Any]:
    return [read_json_text(line) for line in path.read_text('utf-8').splitlines() if line.strip()]


def validate_preparation_v4(run_dir: Path, *, contract: Mapping[str, Any], repository_root: Path, records: list[dict[str, Any]]) -> None:
    if len(records) < 2:
        raise ValueError('version-four run must be prepared through XK1')
    capability = read_json(run_dir / 'capability-snapshot.json')
    expected_capability = {'schema_id': 'xi-kari.v4.capability-snapshot', 'schema_version': 4, 'run_id': contract['run_id'], 'mode': contract['mode'], **contract['capability_snapshot'], 'captured_at': contract['created_at']}
    if capability != expected_capability:
        raise ValueError('version-four capability snapshot differs from its run contract')
    validate_versioned_schema('xk-v4-production-capability.schema.json', capability, repository_root=repository_root)
    lock = read_json(run_dir / 'source-lock.json')
    if lock.get('framework_version') != 'v9.0' or lock.get('run_id') != contract['run_id']:
        raise ValueError('version-four source lock mixes source or run identities')
    events = _read_jsonl(run_dir / 'authoring/XK01-read-events.jsonl')
    errors = validate_full_source_lock(lock, events, repository_root)
    if errors:
        raise ValueError('version-four source lock failed fresh source validation')
    plan = read_json(run_dir / 'authoring/XK01-read-plan.json')
    expected_plan = {'schema_id': 'xi-kari.v4.read-plan', 'schema_version': 4, 'run_id': contract['run_id'], 'framework_version': 'v9.0', **{key: lock[key] for key in ('reader_sequence', 'reader_unit_count', 'paragraph_count', 'table_count', 'source_unit_count')}, 'requires_complete_semantic_read': True}
    if plan != expected_plan:
        raise ValueError('version-four read plan differs from the actual source lock')
    trace = read_json(run_dir / 'authoring/XK01-semantic-read-trace.json')
    if validate_semantic_read_trace(trace, repository_root=repository_root, run_contract=contract, source_lock=lock, source_events=events, xk0_record_sha256=records[0]['record_sha256']):
        raise ValueError('version-four semantic read trace failed source-bound validation')
    raw_trace_bytes = read_bounded_regular_file(run_dir / SOURCE_TRACE_INPUT_RELATIVE, limit=16 * 1024 * 1024)
    receipt = trace['import_receipt']
    if receipt['input_file_sha256'] != sha256_bytes(raw_trace_bytes) or receipt['input_byte_count'] != len(raw_trace_bytes):
        raise ValueError('version-four source trace input bytes differ from import authority')
    raw_trace = read_json_text(raw_trace_bytes.decode('utf-8'))
    if trace['import_receipt']['semantic_payload_sha256'] != sha256_json(raw_trace):
        raise ValueError('version-four source trace semantic input differs')
    ontology_plan = read_json(run_dir / 'authoring/XK04-ontology-read-plan.json')
    ontology_trace = read_json(run_dir / 'authoring/XK04-ontology-read-trace.json')
    if ontology_plan.get('framework_version') != 'v9.0':
        raise ValueError('version-four ontology plan mixes source authority')
    errors = validate_ontology_read_trace(ontology_trace, plan=ontology_plan, expected_run_id=contract['run_id'], expected_problem_contract_sha256=contract['problem_contract_sha256'], repository_root=repository_root)
    if errors:
        raise ValueError('version-four ontology trace failed fresh source authority')
    raw_ontology = read_json(run_dir / ONTOLOGY_TRACE_INPUT_RELATIVE)
    expected_trace = build_ontology_read_trace(raw_ontology, plan=ontology_plan, run_id=contract['run_id'], repository_root=repository_root, problem_contract_sha256=contract['problem_contract_sha256'])
    if ontology_trace != expected_trace:
        raise ValueError('version-four ontology trace differs from persisted semantic inputs')
    if records[0]['input_sha256'] != sha256_json({'question': contract['question'], 'mode': contract['mode'], 'problem_contract': contract['problem_contract'], 'privacy_contract': contract['privacy_contract']}):
        raise ValueError('XK0 exact input hash differs')
    if records[1]['input_sha256'] != phase_input_sha256_v4(records[0], {'source_lock': lock, 'semantic_read_trace': trace}):
        raise ValueError('XK1 exact input hash differs')


def validate_authoring_replay_v4(run_dir: Path, *, contract: Mapping[str, Any], packet: Mapping[str, Any], repository_root: Path) -> None:
    from .authoring import require_base_authoring_provider
    from .execution import _base_prompt, _project_retrieval, _rebind_visibility_ledger, parse_base_authoring_output
    from .contracts import build_analysis_packet
    from .retrieval_execution import load_host_capture_bundle, validate_retrieval_execution_receipt

    base = read_json(run_dir / 'authoring/XK01-base-authoring-receipt.json')
    request_path = run_dir / 'authoring/XK01-base-authoring-request.json'
    request = read_json(request_path)
    provider = request['source_inputs']['base_provider_binding']
    require_base_authoring_provider(provider, mode=contract['mode'], verify_executable=False)
    byte_inputs = {
        'input_sha256': request_path, 'prompt_sha256': run_dir / 'authoring/XK01-base-authoring-prompt.txt',
        'stdout_sha256': run_dir / 'authoring/XK01-base-authoring-events.jsonl',
        'stderr_sha256': run_dir / STDERR_RELATIVE,
        'semantic_output_sha256': run_dir / 'authoring/XK01-base-authoring-output.bin',
    }
    for field, path in byte_inputs.items():
        raw = read_bounded_regular_file(path, limit=64 * 1024 * 1024)
        if field != 'stderr_sha256' and not raw:
            raise ValueError('version-four authoring physical input is empty: ' + path.name)
        if base.get(field) != sha256_bytes(raw):
            raise ValueError('version-four authoring physical input hash differs: ' + path.name)
    if base.get('receipt_sha256') != sha256_json({key: value for key, value in base.items() if key != 'receipt_sha256'}):
        raise ValueError('version-four base author receipt hash differs')
    trace = read_json(run_dir / 'authoring/XK01-semantic-read-trace.json')
    if trace.get('base_authoring_execution') != base:
        raise ValueError('version-four semantic trace does not bind the execute receipt')
    if request.get('source_inputs', {}).get('source_version') != 'v9.0' or request.get('contract_version') != 4:
        raise ValueError('version-four base request source or contract version differs')
    if request.get('privacy_contract') != contract['privacy_contract'] or request.get('problem_contract') != contract['problem_contract']:
        raise ValueError('version-four base request changed frozen problem or privacy')
    if request.get('natural_request') != contract.get('natural_request'):
        raise ValueError('version-four natural request differs from execute')
    if (run_dir / 'authoring/XK01-base-authoring-prompt.txt').read_bytes() != _base_prompt(request):
        raise ValueError('version-four prompt differs from its request')
    for field, expected in (('provider_binding_sha256', sha256_json(provider)), ('provider_executable_sha256', provider['executable_sha256']), ('provider_argv_sha256', provider['argv_sha256'])):
        if base.get(field) != expected:
            raise ValueError('version-four base provider binding differs: ' + field)
    adapter = contract['capability_snapshot']['semantic_authoring_adapter']
    validate_provider_pair_v4(provider, adapter, mode=contract['mode'])
    if adapter['executable_sha256'] != base.get('adapter_executable_sha256'):
        raise ValueError('version-four execute provider differs from XK0 capability')
    ontology_plan = read_json(run_dir / 'authoring/XK04-ontology-read-plan.json')
    lock = read_json(run_dir / 'source-lock.json')
    events = _read_jsonl(run_dir / 'authoring/XK01-read-events.jsonl')
    raw_packet, raw_trace, raw_ontology = parse_base_authoring_output(
        (run_dir / 'authoring/XK01-base-authoring-output.bin').read_bytes(),
        problem_contract=contract['problem_contract'], mode=contract['mode'], ontology_read_plan=ontology_plan,
        repository_root=repository_root, natural_request=contract.get('natural_request'),
        source_lock=lock, source_events=events, contract_version=4,
    )
    if raw_trace != read_json(run_dir / SOURCE_TRACE_INPUT_RELATIVE) or raw_ontology != read_json(run_dir / ONTOLOGY_TRACE_INPUT_RELATIVE):
        raise ValueError('version-four source or ontology trace inputs differ from the actual model output')
    if base.get('semantic_read_trace_sha256') != sha256_json(raw_trace) or base.get('ontology_read_trace_sha256') != sha256_json(raw_ontology) or base.get('ontology_read_plan_sha256') != sha256_json(ontology_plan):
        raise ValueError('version-four semantic read receipt differs from actual author output')
    host_captures = load_host_capture_bundle(run_dir, run_id=contract['run_id'])[1] if contract['mode'] == 'open-world' else None
    projected, _, semantic = _project_retrieval(
        raw_packet, event_stream=(run_dir / 'authoring/XK01-base-authoring-events.jsonl').read_bytes(),
        receipt=base, request_bytes=request_path.read_bytes(), run_id=contract['run_id'], provider=provider,
        adapter_sha256=base['adapter_executable_sha256'], child_pid=base['child_pid'],
        started_at=base['started_at'], completed_at=base['completed_at'], evidence_cutoff=contract['evidence_cutoff'],
        closed_input_materials=request['source_inputs'].get('closed_input_materials'),
        frozen_material_manifest=request['source_inputs'].get('frozen_material_manifest'), host_captures=host_captures,
        contract_version=4,
    )
    _rebind_visibility_ledger(projected, privacy_purpose=contract['privacy_contract']['purpose'])
    expected = build_analysis_packet(projected, run_contract=contract, repository_root=repository_root)
    if expected != packet:
        raise ValueError('version-four persisted packet differs from the actual author projection')
    semantic_document = read_json(run_dir / 'authoring/XK02-semantic-retrieval.json')
    semantic_body = {key: value for key, value in semantic_document.items() if key not in {'schema_id', 'schema_version', 'run_id', 'mode'}}
    if semantic_body != semantic:
        raise ValueError('version-four semantic retrieval differs from the actual author projection')
    receipt = read_json(run_dir / 'authoring/XK02-retrieval-execution-receipt.json')
    errors = validate_execute_owned_binding(contract['capability_snapshot']['execute_owned_binding'], run_contract=contract, base_receipt=base, retrieval_receipt=receipt)
    if errors:
        raise ValueError('version-four execute-owned receipt binding failed')
    from .v4_retrieval import host_retrieval_view
    host_retrieval = host_retrieval_view(packet['retrieval'])
    if contract['mode'] == 'closed-input':
        from .closed_input import validate_closed_input_execution
        errors = validate_closed_input_execution(receipt, host_retrieval, run_id=contract['run_id'], evidence_cutoff=contract['evidence_cutoff'], semantic_document=semantic_document, event_stream=(run_dir / 'authoring/XK01-base-authoring-events.jsonl').read_bytes(), base_request=request, base_request_bytes=request_path.read_bytes(), base_receipt=base)
    else:
        errors = validate_retrieval_execution_receipt(receipt, host_retrieval, run_id=contract['run_id'], evidence_cutoff=contract['evidence_cutoff'], semantic_retrieval=semantic, event_stream=(run_dir / 'authoring/XK01-base-authoring-events.jsonl').read_bytes(), adapter_input=request_path.read_bytes(), host_captures=host_captures)
    if errors:
        raise ValueError('version-four actual retrieval execution receipt failed')


def validate_provider_pair_v4(base_provider: Mapping[str, Any], adapter: Mapping[str, Any], *, mode: str) -> None:
    from .authoring import require_base_authoring_provider, require_semantic_authoring_adapter
    require_base_authoring_provider(base_provider, mode=mode, verify_executable=False)
    require_semantic_authoring_adapter(adapter, verify_executable=False)
    probe = adapter['provider_binding']
    identity_fields = ('protocol', 'repository_root', 'executable_path', 'executable_sha256', 'model', 'reasoning_effort', 'approval_policy', 'sandbox', 'ephemeral', 'ignore_user_config', 'strict_config', 'timeout_seconds')
    if any(base_provider.get(field) != probe.get(field) for field in identity_fields):
        raise ValueError('version-four base and probe provider identities differ')


def reader_payload_v4(packet: Mapping[str, Any], contract: Mapping[str, Any]) -> dict[str, Any]:
    return {**deepcopy(dict(packet)), 'question': contract['question'], 'sources': deepcopy(packet['retrieval']['sources']), 'assessments': deepcopy(packet['retrieval']['assessments'])}


def build_reader_artifacts_v4(run_dir: Path, *, packet: Mapping[str, Any], contract: Mapping[str, Any], repository_root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    from .coverage import build_coverage_v4
    payload = reader_payload_v4(packet, contract)
    outputs = render_reader_outputs(payload)
    lock = read_json(run_dir / 'source-lock.json')
    index = read_json(run_dir / 'retrieval/index.json')
    coverage = build_coverage_v4(run_id=contract['run_id'], source_lock=lock, retrieval_index=index, evidence_ledger=packet['evidence'])
    if not coverage.get('complete'):
        raise ValueError('version-four source, evidence or output coverage is incomplete')
    prose_plan = build_prose_plan(run_id=contract['run_id'], payload=payload, coverage=coverage)
    semantic = build_semantic_coverage(run_id=contract['run_id'], packet=payload, source_read_complete=coverage['source_read']['complete'], candidate_closure_complete=True, reader_outputs=outputs)
    prose_errors = [error for value in outputs.values() for error in check_plain_language(value)]
    if prose_errors or not semantic['reader_projection_complete']:
        raise ValueError('version-four complete reader projection failed its prose or semantic contract')
    protected_values = set(protected_retrieval_values(payload).values())
    from .semantic_projection import _resolve_path_parent
    for atom in typed_semantic_atoms(payload):
        if atom.get('projection_status') != 'withheld_for_protection':
            continue
        parent = _resolve_path_parent(payload, atom['canonical_path'])
        if parent is not None:
            value = parent[0][parent[1]]
            if isinstance(value, str):
                protected_values.add(value)
    if any(value and value in text for value in protected_values for text in outputs.values()):
        raise ValueError('version-four reader privacy validation failed')
    packet_sha256 = sha256_file(run_dir / PACKET_RELATIVE)
    documents = {
        'authoring/XK11-output-plan.json': _phase_document(packet, contract, 'XK11', 'output-plan', prose_plan, {'coverage': coverage}, packet_sha256),
        'authoring/XK11-semantic-coverage.json': _phase_document(packet, contract, 'XK11', 'semantic-coverage', None, semantic, packet_sha256),
        'authoring/XK11-prose-review.json': _phase_document(packet, contract, 'XK11', 'prose-review', None, {'check_method': 'deterministic-plain-language-rules', 'independent_reviewer': False, 'valid': True, 'errors': []}, packet_sha256),
    }
    return documents, outputs


def validate_terminal_closure_v4(run_dir: Path, contract: Mapping[str, Any], records: list[dict[str, Any]], *, required: bool) -> tuple[str | None, list[str]]:
    terminal, errors = verify_terminal_record(run_dir, contract)
    if terminal is None:
        if required and not errors:
            errors.append('version-four signed terminal authority is missing')
        return None, errors
    payload = terminal['signed_payload']
    if payload.get('terminal_state') != 'complete' or payload.get('phase_count') != 13 or len(records) != 13 or payload.get('chain_head_sha256') != records[-1]['record_sha256']:
        return None, ['version-four signed terminal completion boundary differs']
    try:
        completion = read_json(run_dir / COMPLETION_RELATIVE)
        validate_versioned_schema('xk-v4-production-completion.schema.json', completion, repository_root=Path(contract['repository_root']))
        expected = {'schema_id': 'xi-kari.v4.completion', 'schema_version': 4, 'run_id': contract['run_id'], 'official_validation_path': OFFICIAL_REPORT_RELATIVE, 'official_validation_sha256': sha256_file(run_dir / OFFICIAL_REPORT_RELATIVE), 'chain_head_sha256': records[-1]['record_sha256'], 'phase_count': 13, 'validator_set_sha256': contract['validator_set_sha256'], 'manifest_sha256': sha256_file(run_dir / 'artifacts/artifact-manifest.json'), 'final_chat_sha256': sha256_file(run_dir / 'delivery/final-chat.json'), 'xk12_transaction_sha256': sha256_file(run_dir / TRANSACTION_RELATIVE), 'provider_environment_sha256': contract['provider_environment_sha256'], 'completed_at': completion['completed_at']}
        if completion != expected or payload.get('completion_sha256') != sha256_file(run_dir / COMPLETION_RELATIVE):
            errors.append('version-four signed completion disk closure differs')
        official = read_json(run_dir / OFFICIAL_REPORT_RELATIVE)
        if any(official.get(field) != value for field, value in {'schema_id': 'xi-kari.v4.validator-report', 'run_id': contract['run_id'], 'fresh': True, 'fresh_process': True, 'validation_boundary': 'official', 'valid': True, 'validated_phase': 'XK12', 'phase_count': 13, 'chain_head_sha256': records[-1]['record_sha256'], 'validator_set_sha256': contract['validator_set_sha256']}.items()):
            errors.append('version-four official report is not authoritative')
        if read_json(run_dir / TRANSACTION_RELATIVE).get('state') != 'official_validated':
            errors.append('version-four XK12 transaction is not finalized')
        if read_json(run_dir / 'delivery/final-chat.json').get('validation_authority_path') != COMPLETION_RELATIVE:
            errors.append('version-four final chat does not bind signed completion')
    except Exception:
        errors.append('version-four signed completion closure is unreadable or invalid')
    return ('complete' if not errors else None), errors


def _report(contract: Mapping[str, Any] | None, records: list[dict[str, Any]], errors: list[str], *, repository_root: Path, boundary: str, fresh_process: bool, complete: bool) -> dict[str, Any]:
    try:
        authority = validator_set_sha256_v4(repository_root)
    except Exception:
        authority = '0' * 64
    return {
        'schema_id': 'xi-kari.v4.validator-report', 'schema_version': 4,
        'validator_version': RUNTIME_VERSION_V4, 'validator_set_sha256': authority,
        'run_id': contract.get('run_id') if contract else None, 'fresh': True,
        'fresh_process': fresh_process, 'validator_pid': os.getpid(), 'validator_parent_pid': os.getppid(), 'validation_boundary': boundary,
        'complete': complete and not errors, 'checked_at': utc_now_v4(),
        'validated_phase': records[-1]['phase'] if records else None,
        'chain_head_sha256': records[-1]['record_sha256'] if records else None,
        'phase_count': len(records), 'checks': sorted({PHASE_RESPONSIBILITIES.get(row.get('phase'), 'chain') for row in records}),
        'valid': not errors, 'errors': list(dict.fromkeys(errors)),
    }


def validate_run_v4(run_dir: Path, *, repository_root: Path | None = None, require_complete: bool = True, check_manifest: bool = True, validation_boundary: str = 'final', fresh_process: bool = False, _lineage_ancestors: frozenset[Path] | None = None) -> dict[str, Any]:
    if validation_boundary not in {'preseal', 'promotion', 'official', 'final'}:
        raise ValueError('unsupported version-four validation boundary')
    root = Path(run_dir).expanduser().absolute()
    repo = Path(repository_root or DEFAULT_REPOSITORY_ROOT)
    contract: Mapping[str, Any] | None = None
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    terminal_state = None
    try:
        current = Path(root.anchor)
        for part in root.parts[1:]:
            current /= part
            if current.is_symlink():
                raise ValueError('version-four run path contains a symlink')
        if any(path.is_symlink() for path in root.rglob('*')):
            raise ValueError('version-four run artifact contains a symlink')
        root = root.resolve()
        contract = read_json(root / 'run-contract.json')
        repo = require_run_contract_v4(contract, repository_root=repository_root)
        for forbidden in {repo, DEFAULT_REPOSITORY_ROOT}:
            if root == forbidden or forbidden in root.parents:
                raise ValueError('version-four run is inside a repository or Skill installation')
        records, chain_errors = validate_phase_chain(root)
        errors.extend(chain_errors)
        errors.extend(validate_json_artifact_ownership_v4(root, repo))
        if any(row.get('run_id') != contract['run_id'] for row in records):
            errors.append('version-four phase chain run identity differs')
        validate_preparation_v4(root, contract=contract, repository_root=repo, records=records)
        packet = read_json(root / PACKET_RELATIVE)
        require_packet_contract_v4(packet, mode=contract['mode'], run_contract=contract, repository_root=repo)
        validate_authoring_replay_v4(root, contract=contract, packet=packet, repository_root=repo)
        packet_sha256 = sha256_file(root / PACKET_RELATIVE)
        expected_documents = build_semantic_phase_artifacts_v4(packet, contract=contract, repository_root=repo, input_packet_sha256=packet_sha256)
        for record in records:
            phase = record['phase']
            paths = expected_phase_paths_v4(phase, mode=contract['mode'], run_dir=root)
            if tuple(row['path'] for row in record['artifact_bindings']) != paths:
                errors.append(phase + ' exact artifact ownership differs')
            if record['index'] >= 2:
                expected_input = phase_input_sha256_v4(records[record['index'] - 1], semantic_phase_input_v4(root, phase, packet_sha256=packet_sha256, paths=paths))
                if record['input_sha256'] != expected_input:
                    errors.append(phase + ' exact phase input hash differs')
            for relative, expected in expected_documents.get(phase, {}).items():
                if read_json(root / relative) != expected:
                    errors.append(phase + ' semantic materialization differs: ' + relative)
        if len(records) > 2:
            index = read_json(root / 'retrieval/index.json')
            errors.extend(validate_retrieval_bundle(root, index, mode=contract['mode'], evidence_cutoff=contract['evidence_cutoff']))
            for row in index['sources']:
                actual = read_json(confined_path(root, row['source_path'], must_exist=True))
                expected = next(source for source in packet['retrieval']['sources'] if source['source_id'] == row['source_id'])
                if actual != _normalise_source(expected, run_id=contract['run_id']):
                    errors.append('version-four source material differs from the actual author projection')
        if len(records) > 9 and any(row['status'] == 'applicable' for row in packet['applicability'].values()):
            errors.append('version-four fresh red-team, stance-stability and sensitivity probes are not integrated')
        if len(records) > 11:
            documents, rendered = build_reader_artifacts_v4(root, packet=packet, contract=contract, repository_root=repo)
            for relative, expected in documents.items():
                if read_json(root / relative) != expected:
                    errors.append('version-four reader coverage or prose plan differs from disk output')
            for name, actual in load_reader_outputs(root).items():
                if actual != rendered[name]:
                    errors.append('version-four reader projection differs: ' + name)
            expected_index = render_artifact_index(root, contract_profile=PRODUCTION_PROFILE_V4, authoring_profile='production-codex')
            if (root / 'delivery/artifact-index.md').read_text('utf-8') != expected_index:
                errors.append('version-four delivery artifact index differs')
        if require_complete and len(records) != 13:
            errors.append('version-four run is incomplete: ' + str(len(records)) + '/13 phases')
        if validation_boundary == 'preseal' and len(records) != 12:
            errors.append('version-four preseal validation requires XK11')
        state = read_json(root / 'continuation/state.json')
        if state.get('run_id') != contract['run_id']:
            errors.append('version-four continuation state run identity differs')
        if len(records) < 13:
            for relative in expected_phase_paths_v4('XK12', mode=contract['mode']):
                if (root / relative).exists():
                    errors.append('premature version-four XK12 declaration: ' + relative)
            if state.get('state') == 'complete':
                errors.append('version-four continuation claims completion before XK12')
        if len(records) == 13:
            if check_manifest:
                from .materialization_v4 import build_manifest_v4
                if read_json(root / 'artifacts/artifact-manifest.json') != build_manifest_v4(root, contract=contract, records=records[:12], packet=packet):
                    errors.append('version-four manifest differs from exact disk artifacts')
            expected_chat = {'schema_id': 'xi-kari.v4.final-chat', 'schema_version': 4, 'run_id': contract['run_id'], 'answer_path': DELIVERY_PATHS['answer'], 'validation_authority_path': COMPLETION_RELATIVE}
            if read_json(root / DELIVERY_PATHS['final_chat']) != expected_chat:
                errors.append('version-four final chat differs from completion contract')
            preseal = read_json(root / 'validation/attempts/final/validator-report.json')
            if any(preseal.get(field) != value for field, value in {'schema_id': 'xi-kari.v4.validator-report', 'valid': True, 'fresh_process': True, 'validation_boundary': 'preseal', 'validated_phase': 'XK11', 'chain_head_sha256': records[11]['record_sha256'], 'validator_set_sha256': contract['validator_set_sha256'], 'run_id': contract['run_id']}.items()):
                errors.append('version-four XK12 preseal report does not bind the fresh XK11 chain')
            if validation_boundary in {'promotion', 'official'} and (state.get('state') not in {'in_progress', 'needs_attention'} or state.get('next_phase') != 'XK12'):
                errors.append('version-four promotion or official validation requires uncommitted continuation')
            terminal_state, terminal_errors = validate_terminal_closure_v4(root, contract, records, required=validation_boundary == 'final')
            errors.extend(terminal_errors)
    except Exception as exc:
        if isinstance(exc, ValueError) and str(exc).startswith(('version-four ', 'incompatible version-four ', 'supplied repository root ', 'repository authority ', 'provider environment ', 'XK0 ', 'XK1 ')):
            errors.append(str(exc))
        else:
            errors.append('version-four disk validation failed: ' + type(exc).__name__)
    return _report(contract, records, errors, repository_root=repo, boundary=validation_boundary, fresh_process=fresh_process, complete=validation_boundary == 'final' and terminal_state == 'complete')


def run_fresh_validator_v4(run_dir: Path, *, repository_root: Path, preseal: bool = False, promotion: bool = False, official: bool = False, require_complete: bool = True) -> dict[str, Any]:
    if sum((preseal, promotion, official)) > 1:
        raise ValueError('version-four fresh validator boundary is ambiguous')
    boundary = 'preseal' if preseal else 'promotion' if promotion else 'official' if official else 'final'
    root = resolve_repository_root(repository_root)
    command = [sys.executable, '-B', '-m', 'xi_kari_runtime.validation_v4', '--run-dir', str(Path(run_dir).absolute()), '--repository-root', str(root), '--boundary', boundary]
    if not require_complete or preseal:
        command.append('--allow-incomplete')
    environment = os.environ.copy()
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    environment['PYTHONPATH'] = str(root / 'scripts')
    process = subprocess.Popen(command, cwd=root, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    attempt = confined_path(Path(run_dir).resolve(), 'validation/attempts/' + boundary + '-' + uuid.uuid4().hex)
    attempt.mkdir(parents=True, exist_ok=False)
    atomic_write_bytes(attempt / 'stdout.bin', stdout)
    atomic_write_bytes(attempt / 'stderr.bin', stderr)
    execution = {
        'schema_id': 'xi-kari.v4.validation-execution', 'schema_version': 4,
        'run_id': None, 'boundary': boundary, 'parent_pid': os.getpid(), 'launcher_pid': process.pid, 'child_pid': process.pid,
        'command': command, 'command_sha256': sha256_json(command), 'exit_status': process.returncode,
        'provider_environment_sha256': provider_environment_sha256_v4(), 'stdout_sha256': sha256_bytes(stdout),
        'stderr_sha256': sha256_bytes(stderr), 'report_sha256': None, 'completed_at': utc_now_v4(),
    }
    try:
        report = read_json_text(stdout.decode('utf-8'))
    except Exception as exc:
        atomic_write_json(attempt / 'execution.json', execution)
        raise ValueError('version-four fresh validator returned no readable report') from exc
    atomic_write_json(attempt / 'validator-report.json', report)
    execution.update(run_id=report.get('run_id'), child_pid=report.get('validator_pid'), report_sha256=sha256_file(attempt / 'validator-report.json'))
    atomic_write_json(attempt / 'execution.json', execution)
    owned_process = report.get('validator_pid') == process.pid or (os.name == 'nt' and report.get('validator_parent_pid') == process.pid)
    if report.get('schema_id') != 'xi-kari.v4.validator-report' or report.get('fresh_process') is not True or not owned_process or report.get('validator_pid') == os.getpid() or report.get('validation_boundary') != boundary:
        raise ValueError('version-four validation did not originate in the required new process')
    if (process.returncode == 0) != (report.get('valid') is True):
        raise ValueError('version-four fresh validator exit code differs from its report')
    return report


def _main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--repository-root', type=Path, required=True)
    parser.add_argument('--boundary', choices=('preseal', 'promotion', 'official', 'final'), default='final')
    parser.add_argument('--allow-incomplete', action='store_true')
    args = parser.parse_args()
    report = validate_run_v4(args.run_dir, repository_root=args.repository_root, require_complete=not args.allow_incomplete, validation_boundary=args.boundary, fresh_process=True)
    sys.stdout.buffer.write(canonical_bytes(report) + b'\n')
    return 0 if report['valid'] else 2


if __name__ == '__main__':
    raise SystemExit(_main())
