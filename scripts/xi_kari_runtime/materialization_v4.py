"""Code-owned XK2-XK12 materialization for source-v9.0 production runs."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import math
from pathlib import Path
import shutil
from typing import Any
import uuid

from .canonical_json import atomic_write_json, atomic_write_text, confined_path, read_json, sha256_file, sha256_json
from .contracts import DELIVERY_PATHS, PHASE_RESPONSIBILITIES
from .materialization import (
    _begin_xk12_transaction, _promote_xk12_candidate, _resolve_run_directory,
    _rollback_xk12_transaction, _set_state, _write_xk12_transaction_state,
)
from .packet_v4 import require_packet_contract_v4
from .phase_chain import PHASES, append_phase, load_phase_records, validate_phase_chain
from .prose import render_artifact_index
from .retrieval import materialize_retrieval_bundle
from .terminal_authority import (
    COMPLETION_RELATIVE, KEY_RELATIVE, OFFICIAL_REPORT_RELATIVE, TERMINAL_RELATIVE,
    TRANSACTION_RELATIVE, commit_terminal_record,
)
from .validation_v4 import (
    AUTHOR_EXECUTIONS_RELATIVE, DEFAULT_REPOSITORY_ROOT, PACKET_RELATIVE, PRODUCTION_PROFILE_V4, RUNTIME_VERSION_V4,
    build_reader_artifacts_v4, build_semantic_phase_artifacts_v4,
    expected_phase_paths_v4, phase_input_sha256_v4, require_run_contract_v4,
    run_fresh_validator_v4, semantic_phase_input_v4, utc_now_v4,
    validate_preparation_v4, validate_run_v4,
    validate_authoring_inputs_v4, validate_authoring_projection_v4,
    validate_terminal_closure_v4, checked_execution_v4, domain_plan_v4, prepare_packet_v4,
    probe_outcomes_v4, recursive_author_targets_v4, replay_author_executions_v4,
    validation_execution_for_report_v4,
)


def _complete_base_reader_v4(pending: Mapping[str, Any], contract: Mapping[str, Any], repository_root: Path, *, temporal_audit: object = None) -> bool:
    from .semantic_projection import validate_reader_sections, validate_reader_section_privacy
    from .prose import check_plain_language, reader_contract_gaps, render_reader_outputs
    from .validation_v4 import reader_payload_v4
    try:
        require_packet_contract_v4(pending, mode=contract['mode'], run_contract=contract, repository_root=repository_root, temporal_audit=temporal_audit)
        validate_reader_section_privacy(pending)
        if validate_reader_sections(pending):
            return False
        rendered = render_reader_outputs(reader_payload_v4(pending, contract))
        return not reader_contract_gaps(dict(pending), rendered['answer']) and not any(check for text in rendered.values() for check in check_plain_language(text))
    except ValueError:
        return False


def _sensitivity_changes_v4(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    roots = ('local_world_model', 'recursive_lineage', 'transformation_ledger', 'forecast', 'action_ranking')

    def locate(value: Any, path: str) -> list[dict[str, Any]]:
        if isinstance(value, Mapping):
            for key, item in value.items():
                if key in {'schema_version', 'source_version', 'run_id', 'model_version', 'source_anchors', 'ontology_refs', 'evidence_refs'}:
                    continue
                child = path + '.' + key
                if key in {'value', 'observed_value', 'threshold', 'weight', 'probability'} and isinstance(item, (int, float)) and not isinstance(item, bool) and math.isfinite(item):
                    return [{'path': child, 'before': item, 'after': item + max(abs(item) * 0.1, 0.1), 'reason': '检查当前已登记数值在明确假设变化下对本题结论的影响；原始材料保持冻结。'}]
                found = locate(item, child)
                if found:
                    return found
        elif isinstance(value, list):
            for index, item in enumerate(value):
                found = locate(item, path + '[' + str(index) + ']')
                if found:
                    return found
        return []

    for field in roots:
        found = locate(packet.get(field), field)
        if found:
            return found
    conditions = packet.get('recursive_lineage', {}).get('conditions', {})
    for name, value in conditions.items():
        if isinstance(value, bool):
            return [{'path': 'recursive_lineage.conditions.' + name, 'before': value, 'after': not value, 'reason': '检查当前明确条件改变后本题的条件结论；不把该假设当作已发生事实。'}]
    raise ValueError('version-four applicable dynamics have no registered semantic perturbation for sensitivity authoring')


def _author_input_v4(run_dir: Path, semantic_base: Mapping[str, Any], *, contract: Mapping[str, Any], repository_root: Path, temporal_audit: object = None) -> dict[str, Any]:
    from .semantic_executions_v4 import (
        bind_semantic_execution_provider_v4, build_semantic_execution_request_v4,
        execute_next_author_v4, execute_semantic_probes_v4, execute_final_reader_v4,
    )
    from .stage_consumers_v4 import validate_stage_chain_v4
    semantic = deepcopy(dict(semantic_base))
    domain = domain_plan_v4(run_dir, repository_root=repository_root)
    pending = prepare_packet_v4(semantic, contract=contract, repository_root=repository_root, domain_read_plan=domain, temporal_audit=temporal_audit)
    controls = validate_stage_chain_v4(pending, run_contract=contract, repository_root=repository_root, temporal_audit=temporal_audit)
    bundle = {
        'schema_id': 'xi-kari.v4.production-author-executions', 'schema_version': 4,
        'run_id': contract['run_id'], 'run_directory': str(run_dir),
        'semantic_base_sha256': sha256_json(semantic_base), 'prepared_packet_sha256': sha256_json(pending),
        'stage_controls': controls, 'provider_binding': None, 'next_author_executions': [],
        'probe_bundle': None, 'sensitivity_changes': [], 'reader_execution': None, 'reader_reused': False,
    }
    requires = any(row['status'] == 'applicable' for row in pending['applicability'].values())
    if requires or not _complete_base_reader_v4(pending, contract, repository_root, temporal_audit=temporal_audit):
        provider = contract['capability_snapshot']['semantic_authoring_adapter']['provider_binding']
        bundle['provider_binding'] = bind_semantic_execution_provider_v4(provider['executable_path'], repository_root=repository_root, timeout_seconds=provider['timeout_seconds'])
    else:
        bundle['reader_reused'] = True
    atomic_write_json(run_dir / AUTHOR_EXECUTIONS_RELATIVE, bundle)
    consumed = set()
    while True:
        controls = validate_stage_chain_v4(pending, run_contract=contract, repository_root=repository_root, temporal_audit=temporal_audit)
        target = next((row for row in recursive_author_targets_v4(controls) if (row['path_id'], row['step_index']) not in consumed), None)
        if target is None:
            break
        request = build_semantic_execution_request_v4(pending, controls, run_contract=contract, kind='next_author', author_request=target['author_request'], repository_root=repository_root, temporal_audit=temporal_audit)
        prior = sha256_json(pending)
        execution = execute_next_author_v4(pending, controls, author_request=target['author_request'], run_contract=contract, binding=bundle['provider_binding'], run_directory=run_dir, repository_root=repository_root, temporal_audit=temporal_audit)
        checked = checked_execution_v4(execution, expected_request=request, binding=bundle['provider_binding'], run_dir=run_dir, original_run_dir=str(run_dir), repository_root=repository_root, temporal_audit=temporal_audit)
        path = next(row for row in semantic['recursive_lineage']['paths'] if row['path_id'] == target['path_id'])
        path['steps'][target['step_index']]['next_author_response'] = deepcopy(checked['semantic_response'])
        pending = prepare_packet_v4(semantic, contract=contract, repository_root=repository_root, domain_read_plan=domain, temporal_audit=temporal_audit)
        bundle['next_author_executions'].append({**target, 'prior_pending_sha256': prior, 'after_pending_sha256': sha256_json(pending), 'execution': execution})
        consumed.add((target['path_id'], target['step_index']))
        atomic_write_json(run_dir / AUTHOR_EXECUTIONS_RELATIVE, bundle)
    controls = validate_stage_chain_v4(pending, run_contract=contract, repository_root=repository_root, temporal_audit=temporal_audit)
    if requires:
        changes = _sensitivity_changes_v4(pending)
        bundle['sensitivity_changes'] = changes
        probes = execute_semantic_probes_v4(pending, controls, run_contract=contract, binding=bundle['provider_binding'], run_directory=run_dir, sensitivity_changes=changes, repository_root=repository_root, temporal_audit=temporal_audit)
        bundle['probe_bundle'] = probes
        atomic_write_json(run_dir / AUTHOR_EXECUTIONS_RELATIVE, bundle)
        requests, responses = [], []
        for spec, execution in zip((('red_team', None), ('stance_stability', 'support'), ('stance_stability', 'oppose'), ('sensitivity', 'baseline'), ('sensitivity', 'changed')), probes['executions'], strict=True):
            request = build_semantic_execution_request_v4(pending, controls, run_contract=contract, kind=spec[0], variant=spec[1], sensitivity_changes=changes, repository_root=repository_root, temporal_audit=temporal_audit)
            checked = checked_execution_v4(execution, expected_request=request, binding=bundle['provider_binding'], run_dir=run_dir, original_run_dir=str(run_dir), repository_root=repository_root, temporal_audit=temporal_audit)
            requests.append(request)
            responses.append(checked['semantic_response'])
        outcomes = probe_outcomes_v4(responses, requests, changes)
        if probes['gates'] != outcomes['comparison']:
            raise ValueError('version-four actual probe comparisons do not match recomputed semantic responses')
        pending = prepare_packet_v4(semantic, contract=contract, repository_root=repository_root, domain_read_plan=domain, probe_outcomes=outcomes, temporal_audit=temporal_audit)
    if not bundle['reader_reused']:
        execution = execute_final_reader_v4(pending, controls, run_contract=contract, binding=bundle['provider_binding'], run_directory=run_dir, repository_root=repository_root, temporal_audit=temporal_audit)
        bundle['reader_execution'] = execution
    bundle.update(prepared_packet_sha256=sha256_json(pending), stage_controls=controls)
    atomic_write_json(run_dir / AUTHOR_EXECUTIONS_RELATIVE, bundle)
    final, _ = replay_author_executions_v4(run_dir, semantic_base, contract=contract, repository_root=repository_root, bundle=bundle, temporal_audit=temporal_audit)
    return final


def build_manifest_v4(run_dir: Path, *, contract: Mapping[str, Any], records: list[dict[str, Any]], packet: Mapping[str, Any]) -> dict[str, Any]:
    from .concept_authority import load_concept_authority
    _, concept = load_concept_authority(Path(contract['repository_root']), source_version='v9.0')

    def binding(relative: str) -> dict[str, Any]:
        path = confined_path(run_dir, relative, must_exist=True)
        return {'path': relative, 'sha256': sha256_file(path), 'bytes': path.stat().st_size}

    return {
        'schema_id': 'xi-kari.v4.artifact-manifest', 'schema_version': 4,
        'runtime_version': RUNTIME_VERSION_V4, 'artifact_schema_version': 4, 'source_version': 'v9.0',
        'run_id': contract['run_id'], 'input_packet_sha256': sha256_file(run_dir / PACKET_RELATIVE),
        'candidate_census_sha256': concept['candidate_census_sha256'],
        'validated_chain_head_sha256': records[-1]['record_sha256'],
        'validator_set_sha256': contract['validator_set_sha256'], 'phase_responsibilities': PHASE_RESPONSIBILITIES,
        'phase_artifacts': {record['phase']: [binding(row['path']) for row in record['artifact_bindings']] for record in records},
        'delivery': {name: binding(relative) for name, relative in DELIVERY_PATHS.items()},
    }


def _append(run_dir: Path, phase: str, *, contract: Mapping[str, Any], packet_sha256: str, documents: Mapping[str, Any] | None = None, temporal_context: Any = None) -> None:
    records = load_phase_records(run_dir)
    index = PHASES.index(phase)
    if len(records) > index:
        for relative, expected in (documents or {}).items():
            if read_json(confined_path(run_dir, relative, must_exist=True)) != expected:
                raise ValueError(phase + ' already binds different semantic material')
        return
    if len(records) != index:
        raise ValueError('version-four materialization cannot skip a phase')
    for relative, value in (documents or {}).items():
        atomic_write_json(confined_path(run_dir, relative), value)
    paths = expected_phase_paths_v4(phase, mode=contract['mode'], run_dir=run_dir, temporal_context=temporal_context)
    append_phase(run_dir, run_id=contract['run_id'], phase=phase, artifact_path=paths,
        input_sha256=phase_input_sha256_v4(records[-1], semantic_phase_input_v4(run_dir, phase, packet_sha256=packet_sha256, paths=paths)),
        created_at=utc_now_v4())


def status_run_v4(run_dir: Path, *, repository_root: Path | None = None) -> dict[str, Any]:
    root = _resolve_run_directory(run_dir)
    contract = read_json(root / 'run-contract.json')
    repo = require_run_contract_v4(contract, repository_root=repository_root)
    records, errors = validate_phase_chain(root)
    state, terminal_errors = validate_terminal_closure_v4(root, contract, records, required=False)
    errors.extend(terminal_errors)
    continuation = read_json(root / 'continuation/state.json')
    derived = 'complete' if state == 'complete' and not errors else 'needs_attention' if errors or len(records) == 13 or continuation.get('state') == 'needs_attention' else 'prepared' if len(records) == 2 else 'in_progress'
    result = {
        'schema_id': 'xi-kari.v4.run-status', 'schema_version': 4,
        'run_id': contract['run_id'], 'run_dir': str(root), 'mode': contract['mode'], 'state': derived,
        'phase_count': len(records), 'current_phase': records[-1]['phase'] if records else None,
        'next_phase': PHASES[len(records)] if len(records) < 13 else None,
        'chain_head_sha256': records[-1]['record_sha256'] if records else None,
        'generation': contract['continuation']['generation'], 'parent_run_id': contract['continuation']['parent_run_id'],
    }
    if errors:
        result['integrity_errors'] = errors
    return result


def _recover_transaction(run_dir: Path, contract: Mapping[str, Any]) -> None:
    path = run_dir / TRANSACTION_RELATIVE
    if not path.is_file():
        return
    transaction = read_json(path)
    if transaction.get('state') == 'rolled_back':
        return
    records, errors = validate_phase_chain(run_dir)
    terminal, terminal_errors = validate_terminal_closure_v4(run_dir, contract, records, required=False)
    if terminal == 'complete' and not errors and not terminal_errors:
        return
    if (run_dir / TERMINAL_RELATIVE).exists():
        raise ValueError('version-four transaction has an invalid signed terminal; automatic rollback is forbidden')
    candidate_name = transaction.get('candidate_name')
    if not isinstance(candidate_name, str) or Path(candidate_name).name != candidate_name or not candidate_name.startswith('.' + run_dir.name + '.xk12-'):
        raise ValueError('version-four transaction candidate is unsafe')
    _rollback_xk12_transaction(run_dir, transaction)
    _discard_candidate_v4(run_dir, run_dir.parent / candidate_name)


def _discard_candidate_v4(run_dir: Path, candidate: Path) -> None:
    target = Path(candidate).absolute()
    if not target.exists():
        return
    parent = Path(run_dir).resolve().parent
    if target.is_symlink() or not target.is_dir() or target.resolve().parent != parent or not target.name.startswith('.' + Path(run_dir).name + '.xk12-'):
        raise ValueError('version-four transaction candidate does not stay in its isolated run parent')
    shutil.rmtree(target)


def _complete(run_dir: Path, *, packet: Mapping[str, Any], contract: Mapping[str, Any], repository_root: Path, packet_sha256: str) -> None:
    _set_state(run_dir, 'in_progress', next_phase='XK12')
    preseal = run_fresh_validator_v4(run_dir, repository_root=repository_root, preseal=True)
    if not preseal['valid']:
        _set_state(run_dir, 'needs_attention', next_phase='XK12')
        raise ValueError('version-four fresh preseal validation failed; see validator report')
    candidate = run_dir.parent / ('.' + run_dir.name + '.xk12-' + uuid.uuid4().hex)
    transaction = None
    try:
        shutil.copytree(run_dir, candidate, symlinks=True)
        (candidate / KEY_RELATIVE).unlink(missing_ok=True)
        final_chat = {'schema_id': 'xi-kari.v4.final-chat', 'schema_version': 4, 'run_id': contract['run_id'], 'answer_path': DELIVERY_PATHS['answer'], 'validation_authority_path': COMPLETION_RELATIVE}
        atomic_write_json(candidate / DELIVERY_PATHS['final_chat'], final_chat)
        manifest = build_manifest_v4(candidate, contract=contract, records=load_phase_records(candidate), packet=packet)
        _append(candidate, 'XK12', contract=contract, packet_sha256=packet_sha256, documents={
            'validation/attempts/final/validator-report.json': preseal,
            DELIVERY_PATHS['final_chat']: final_chat, 'artifacts/artifact-manifest.json': manifest,
        })
        _set_state(candidate, 'in_progress', next_phase='XK12')
        previous_promotions = set((candidate / 'validation/attempts').glob('promotion-*'))
        try:
            promotion = run_fresh_validator_v4(candidate, repository_root=repository_root, promotion=True)
        finally:
            for attempt in sorted(set((candidate / 'validation/attempts').glob('promotion-*')) - previous_promotions):
                relative = attempt.relative_to(candidate)
                source = confined_path(candidate, relative)
                if not source.is_dir():
                    raise ValueError('version-four promotion capture is not a regular directory')
                shutil.copytree(source, confined_path(run_dir, relative), symlinks=True)
        promotion_execution = validation_execution_for_report_v4(candidate, promotion, boundary='promotion', repository_root=repository_root)
        if not promotion['valid']:
            raise ValueError('version-four fresh promotion validation failed')
        transaction = _begin_xk12_transaction(run_dir, candidate)
        transaction = _promote_xk12_candidate(run_dir, candidate, transaction)
        _set_state(run_dir, 'in_progress', next_phase='XK12')
        official = run_fresh_validator_v4(run_dir, repository_root=repository_root, official=True)
        if not official['valid']:
            raise ValueError('version-four fresh official validation failed')
        official_execution = validation_execution_for_report_v4(run_dir, official, boundary='official', repository_root=repository_root)
        atomic_write_json(run_dir / OFFICIAL_REPORT_RELATIVE, official)
        transaction = _write_xk12_transaction_state(run_dir, transaction, 'official_validated')
        _discard_candidate_v4(run_dir, candidate)
        records = load_phase_records(run_dir)
        completion = {
            'schema_id': 'xi-kari.v4.completion', 'schema_version': 4, 'run_id': contract['run_id'],
            'official_validation_path': OFFICIAL_REPORT_RELATIVE, 'official_validation_sha256': sha256_file(run_dir / OFFICIAL_REPORT_RELATIVE),
            'official_validation_execution_path': official_execution, 'official_validation_execution_sha256': sha256_file(run_dir / official_execution),
            'promotion_validation_execution_path': promotion_execution, 'promotion_validation_execution_sha256': sha256_file(run_dir / promotion_execution),
            'chain_head_sha256': records[-1]['record_sha256'], 'phase_count': 13, 'validator_set_sha256': contract['validator_set_sha256'],
            'manifest_sha256': sha256_file(run_dir / 'artifacts/artifact-manifest.json'),
            'final_chat_sha256': sha256_file(run_dir / DELIVERY_PATHS['final_chat']),
            'xk12_transaction_sha256': sha256_file(run_dir / TRANSACTION_RELATIVE),
            'provider_environment_sha256': contract['provider_environment_sha256'], 'completed_at': utc_now_v4(),
        }
        atomic_write_json(run_dir / COMPLETION_RELATIVE, completion)
        commit_terminal_record(run_dir, contract, {'run_id': contract['run_id'], 'terminal_state': 'complete', 'terminal_at': utc_now_v4(), 'phase_count': 13, 'chain_head_sha256': records[-1]['record_sha256'], 'completion_sha256': sha256_file(run_dir / COMPLETION_RELATIVE)})
        _set_state(run_dir, 'complete', next_phase=None)
        report = run_fresh_validator_v4(run_dir, repository_root=repository_root)
        if not report['valid'] or not report['complete']:
            raise ValueError('version-four signed terminal failed fresh disk reread')
    except Exception:
        if transaction is None and (run_dir / TRANSACTION_RELATIVE).is_file():
            transaction = read_json(run_dir / TRANSACTION_RELATIVE)
        if transaction is not None and not (run_dir / TERMINAL_RELATIVE).exists():
            _rollback_xk12_transaction(run_dir, transaction)
        if not (run_dir / TERMINAL_RELATIVE).exists():
            _set_state(run_dir, 'needs_attention', next_phase='XK12')
        _discard_candidate_v4(run_dir, candidate)
        raise


def _bound_temporal_audit_v4(context: Any, supplied: object) -> object:
    audit = context.audit if context is not None else None
    if supplied is not None:
        from .temporal_audit import TemporalAudit
        if type(supplied) is not TemporalAudit or audit is None or supplied.run_dir != audit.run_dir or supplied.expected_audit_sha256 != audit.expected_audit_sha256:
            raise ValueError('version-four supplied temporal audit differs from the verified execute input')
    return audit


def materialize_run_v4(run_dir: Path, packet: Mapping[str, Any] | None = None, *, repository_root: Path | None = None, temporal_audit: object = None) -> dict[str, Any]:
    root = _resolve_run_directory(run_dir)
    contract = read_json(root / 'run-contract.json')
    repo = require_run_contract_v4(contract, repository_root=repository_root)
    if root == repo or repo in root.parents or root == DEFAULT_REPOSITORY_ROOT or DEFAULT_REPOSITORY_ROOT in root.parents:
        raise ValueError('version-four run must stay outside repositories and Skill installations')
    if any(path.is_symlink() for path in root.rglob('*')):
        raise ValueError('version-four run contains a symlink')
    _recover_transaction(root, contract)
    records, errors = validate_phase_chain(root)
    if errors:
        raise ValueError('version-four phase chain failed disk integrity validation')
    terminal, terminal_errors = validate_terminal_closure_v4(root, contract, records, required=False)
    if terminal_errors:
        raise ValueError('version-four signed terminal authority is invalid')
    validate_preparation_v4(root, contract=contract, repository_root=repo, records=records)
    projected, temporal_context = validate_authoring_inputs_v4(root, contract=contract, repository_root=repo)
    audit = _bound_temporal_audit_v4(temporal_context, temporal_audit)
    if terminal == 'complete':
        report = validate_run_v4(root, repository_root=repo)
        if not report['valid'] or not report['complete']:
            raise ValueError('version-four completed run failed disk validation')
        return status_run_v4(root, repository_root=repo)
    if len(records) == 13:
        raise ValueError('version-four unsigned complete chain cannot be promoted without its transaction')
    packet_path = root / PACKET_RELATIVE
    if packet_path.is_file():
        persisted = read_json(packet_path)
        if packet is not None and dict(packet) != persisted:
            raise ValueError('version-four supplied packet differs from persisted canonical input')
    elif packet is not None:
        if packet.get('schema_id') == 'xi-kari.v4.analysis-packet':
            persisted = dict(packet)
        else:
            if dict(packet) != projected:
                raise ValueError('version-four semantic base packet differs from actual author projection')
            try:
                persisted = _author_input_v4(root, projected, contract=contract, repository_root=repo, temporal_audit=audit)
            except Exception:
                _set_state(root, 'needs_attention', next_phase='XK2')
                raise
        validate_authoring_projection_v4(root, projected, contract=contract, packet=persisted, repository_root=repo, temporal_context=temporal_context)
        atomic_write_json(packet_path, persisted)
    else:
        raise ValueError('version-four prepared run has no canonical analysis packet')
    persisted = read_json(packet_path)
    require_packet_contract_v4(persisted, mode=contract['mode'], run_contract=contract, repository_root=repo, temporal_audit=audit)
    validate_authoring_projection_v4(root, projected, contract=contract, packet=persisted, repository_root=repo, temporal_context=temporal_context)
    packet_sha256 = sha256_file(packet_path)
    authors = read_json(root / AUTHOR_EXECUTIONS_RELATIVE)
    documents = build_semantic_phase_artifacts_v4(persisted, contract=contract, repository_root=repo, input_packet_sha256=packet_sha256, author_executions=authors, temporal_audit=audit)
    _set_state(root, 'in_progress', next_phase=PHASES[len(records)])
    if len(records) == 2:
        materialize_retrieval_bundle(root, persisted['retrieval']['sources'], persisted['retrieval']['assessments'], mode=contract['mode'], run_id=contract['run_id'], evidence_cutoff=contract['evidence_cutoff'])
    for phase in PHASES[2:11]:
        _append(root, phase, contract=contract, packet_sha256=packet_sha256, documents=documents[phase], temporal_context=temporal_context)
    if len(load_phase_records(root)) == 11:
        reader_documents, outputs = build_reader_artifacts_v4(root, packet=persisted, contract=contract, repository_root=repo)
        for name, text in outputs.items():
            atomic_write_text(root / DELIVERY_PATHS[name], text)
        atomic_write_text(root / DELIVERY_PATHS['artifact_index'], render_artifact_index(root, contract_profile=PRODUCTION_PROFILE_V4, authoring_profile='production-codex'))
        _append(root, 'XK11', contract=contract, packet_sha256=packet_sha256, documents=reader_documents)
    _complete(root, packet=persisted, contract=contract, repository_root=repo, packet_sha256=packet_sha256)
    return status_run_v4(root, repository_root=repo)


__all__ = ('build_manifest_v4', 'materialize_run_v4', 'status_run_v4')
