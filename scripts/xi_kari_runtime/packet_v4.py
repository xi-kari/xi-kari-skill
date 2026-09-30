"""Runtime assembly and validation of source-bound version-four analysis packets."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from .canonical_json import sha256_json
from .claims import validate_claim_graph
from .concept_authority import load_concept_authority
from .evidence import validate_evidence_ledger
from .problem_contract import FROZEN_FIELDS, contract_hash, stance_neutrality_key, validate_problem_contract
from .v4_contracts import validate_applicability, validate_versioned_schema


def validate_world_stage(
    world: Mapping[str, Any], *, evidence_ledger: Mapping[str, Any], retrieval_index: Mapping[str, Any],
    repository_root: Path | None = None,
) -> dict[str, Any]:
    from .world_volume import (
        apply_registered_events, bind_registered_event_evidence,
        freeze_object_identity, validate_identity_continuation, validate_prototype_record,
        validate_registered_world_bundle,
    )
    if world.get('schema_id') == 'xi-kari.v4.xk.world-volume':
        checked = validate_registered_world_bundle(
            world, repository_root=repository_root, evidence_ledger=evidence_ledger,
            retrieval_index=retrieval_index, expected_run_id=evidence_ledger['run_id'],
        )
        fields = ('state_diff_id', 'source_state_sha256', 'result_state_sha256', 'event_id', 'event_role', 'evidence_identity', 'authorization_status', 'external_action_authorized', 'reported_content_status')
        return {
            'initial_state_sha256': sha256_json(world['registered_state']),
            'output_state': checked['final_state'],
            'transitions': [{field: getattr(row, field) for field in fields} for row in checked['transitions']],
            'identities': checked['identity_bindings'],
        }
    required = {
        'initial_state', 'events', 'event_bindings', 'channel_registry', 'authorization_registry',
        'identities', 'prototypes', 'identity_changes',
    }
    if not isinstance(world, Mapping) or set(world) != required:
        raise ValueError('world consumer requires exact state, event, identity and registry inputs')
    state = world['initial_state']
    if not isinstance(state, Mapping) or not {'snapshot_id', 'model_version', 'run_id', 'evidence_cutoff', 'objects', 'unknowns', 'losses', 'residuals'}.issubset(state):
        raise ValueError('world initial state is incomplete')
    identities = {row['object_id']: freeze_object_identity(row) for row in world['identities']}
    if len(identities) != len(world['identities']):
        raise ValueError('world identities are duplicated')
    evidence = bind_registered_event_evidence(
        state, world['events'], evidence_ledger=evidence_ledger,
        retrieval_index=retrieval_index, bindings=world['event_bindings'],
    )
    for change in world['identity_changes']:
        validate_identity_continuation(change['previous'], change['current'], recheck_id=change['recheck_id'], identity_rechecks=change['identity_rechecks'])
    prototypes = [
        validate_prototype_record(row, identity_record=identities[row['object_id']], evidence_registry=evidence)
        for row in world['prototypes']
    ]
    transitions = apply_registered_events(
        state, world['events'], evidence_registry=evidence,
        channel_registry=world['channel_registry'], authorization_registry=world['authorization_registry'],
    )
    fields = ('state_diff_id', 'source_state_sha256', 'result_state_sha256', 'event_id', 'event_role', 'evidence_identity', 'authorization_status', 'external_action_authorized', 'reported_content_status')
    return {
        'initial_state_sha256': sha256_json(state),
        'output_state': transitions[-1].output_state if transitions else deepcopy(dict(state)),
        'transitions': [{field: getattr(transition, field) for field in fields} for transition in transitions],
        'identities': identities, 'prototypes': prototypes,
    }


def build_analysis_packet_v4(
    semantic_packet: Mapping[str, Any], *, run_contract: Mapping[str, Any], repository_root: Path,
    domain_read_plan: Mapping[str, Any] | None = None, reader_finalization: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    packet = prepare_analysis_packet_v4(semantic_packet, run_contract=run_contract, repository_root=repository_root, domain_read_plan=domain_read_plan)
    if reader_finalization is not None:
        if not isinstance(reader_finalization, Mapping) or set(reader_finalization) != {'reader_sections', 'visibility_ledger'}:
            raise ValueError('reader finalization may only provide complete sections and disclosure decisions')
        packet.update(deepcopy(dict(reader_finalization)))
    require_packet_contract_v4(packet, mode=run_contract['mode'], run_contract=run_contract, repository_root=repository_root)
    return packet


def prepare_analysis_packet_v4(
    semantic_packet: Mapping[str, Any], *, run_contract: Mapping[str, Any], repository_root: Path,
    domain_read_plan: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute semantic outcomes for reader authoring; delivery still needs validation."""
    from .contracts import build_runtime_packet_binding
    if run_contract.get('contract_profile') != 'production-authoring-v4':
        raise ValueError('version-four packet requires its version-four run profile')
    packet = deepcopy(dict(semantic_packet))
    if any(field in packet for field in ('runtime_binding', 'concept_disposition', 'formal_results', 'domain_binding', 'domain_read_trace', 'domain_usage', 'stage_outcomes')):
        raise ValueError('semantic author cannot supply runtime-owned packet authority')
    if 'empirical_instances' in packet or 'derived_instances' in packet:
        from .formal_results import bind_formal_claim_results
        resolved = bind_formal_claim_results(
            packet['claim_mechanism_graph'], empirical_instances=packet.get('empirical_instances', []),
            derived_instances=packet.get('derived_instances', []), evidence_mode=run_contract['mode'], repository_root=repository_root,
        )
        packet['claim_mechanism_graph'] = resolved['claim_mechanism_graph']
        packet['formal_results'] = {key: value for key, value in resolved.items() if key != 'claim_mechanism_graph'}
    dispositions, _ = load_concept_authority(repository_root, source_version='v9.0')
    packet.update(
        schema_id='xi-kari.v4.analysis-packet', schema_version=4,
        runtime_binding=build_runtime_packet_binding(run_contract), concept_disposition=dispositions,
    )
    if 'domain_trace' in packet:
        from .domain_pipeline_v4 import validate_domain_inputs
        from .formal_results import rebuild_instance_registry
        if domain_read_plan is None:
            raise ValueError('domain author semantics require the frozen runtime reading plan')
        registry = rebuild_instance_registry(packet.get('empirical_instances', []), graph=packet['claim_mechanism_graph'], derived_instances=packet.get('derived_instances', []), evidence_mode=run_contract['mode'], repository_root=repository_root)
        checked = validate_domain_inputs(domain_read_plan, packet['domain_trace'], graph=packet['claim_mechanism_graph'], run_contract=run_contract, repository_root=repository_root, verified_instance_results=registry)
        packet['domain_binding'] = {'plan': deepcopy(dict(domain_read_plan)), **checked}
        packet['domain_read_trace'] = checked['read_trace']
    from .stage_consumers_v4 import validate_stage_chain_v4
    stages = validate_stage_chain_v4(packet, run_contract=run_contract, repository_root=repository_root)
    packet['stage_outcomes'] = {stage: deepcopy(row['result']) for stage, row in stages['stage_results'].items()}
    validate_versioned_schema('xk-v4-analysis-packet.schema.json', packet, repository_root=repository_root)
    _require_packet_semantics_v4(packet, mode=run_contract['mode'], run_contract=run_contract, repository_root=repository_root)
    return packet


def require_packet_contract_v4(
    packet: Mapping[str, Any], *, mode: str,
    run_contract: Mapping[str, Any] | None = None, repository_root: Path | None = None
) -> None:
    _require_packet_semantics_v4(packet, mode=mode, run_contract=run_contract, repository_root=repository_root)
    from .contracts import validate_visibility_ledger
    validate_visibility_ledger(packet, privacy_contract=run_contract.get('privacy_contract') if run_contract else None)


def _require_packet_semantics_v4(
    packet: Mapping[str, Any], *, mode: str,
    run_contract: Mapping[str, Any] | None = None, repository_root: Path | None = None,
) -> None:
    from .v4_contracts import repository_path
    repository_root = repository_path(repository_root)
    from .contracts import build_runtime_packet_binding, validate_answer_basis_references, validate_visibility_ledger
    validate_versioned_schema('xk-v4-analysis-packet.schema.json', packet, repository_root=repository_root)
    if mode not in {'open-world', 'closed-input'} or packet['retrieval'].get('mode') != mode:
        raise ValueError('version-four packet evidence mode differs from the contract')
    problem = validate_problem_contract({field: packet['problem_contract'].get(field) for field in FROZEN_FIELDS}, mode=mode)
    binding = packet['runtime_binding']
    if binding['mode'] != mode or binding['problem_contract_sha256'] != contract_hash(problem):
        raise ValueError('version-four packet problem binding differs from its frozen problem')
    if binding['stance_neutrality_key'] != stance_neutrality_key(problem, mode=mode):
        raise ValueError('version-four packet neutrality binding differs')
    if run_contract is not None:
        if dict(binding) != build_runtime_packet_binding(run_contract) or problem != run_contract['problem_contract']:
            raise ValueError('version-four packet differs from its frozen run contract')
    registry = None
    if 'empirical_instances' in packet or 'derived_instances' in packet:
        from .canonical_json import sha256_json
        from .formal_results import bind_formal_claim_results, rebuild_instance_registry
        resolved = bind_formal_claim_results(
            packet['claim_mechanism_graph'], empirical_instances=packet.get('empirical_instances', []),
            derived_instances=packet.get('derived_instances', []), evidence_mode=mode, repository_root=repository_root,
        )
        control = {key: value for key, value in resolved.items() if key != 'claim_mechanism_graph'}
        if sha256_json(control) != sha256_json(packet.get('formal_results')) or packet['claim_mechanism_graph'] != resolved['claim_mechanism_graph']:
            raise ValueError('packet formal qualification differs from its freshly recomputed instance results')
        registry = rebuild_instance_registry(packet.get('empirical_instances', []), graph=packet['claim_mechanism_graph'], derived_instances=packet.get('derived_instances', []), evidence_mode=mode, repository_root=repository_root)
    elif 'formal_results' in packet:
        raise ValueError('packet formal results require the actual semantic instance inputs')
    graph = validate_claim_graph(packet['claim_mechanism_graph'], evidence_mode=mode, repository_root=repository_root, verified_instance_results=registry)
    if packet['applicability'] != graph['applicability']:
        raise ValueError('version-four packet and claim applicability differ')
    validate_applicability(packet['applicability'], claims=graph['claims'], repository_root=repository_root)
    ledger = packet['evidence']
    errors = validate_evidence_ledger(dict(ledger), dict(packet['retrieval']))
    if errors:
        raise ValueError('version-four evidence ledger failed its material bindings: ' + errors[0])
    evidence = {row['evidence_id']: row for row in ledger['evidence']}
    for row in graph['evidence']:
        for reference in row['xk3_evidence_refs']:
            actual = evidence.get(reference)
            if actual is None:
                raise ValueError('claim graph material does not resolve to the actual evidence ledger')
            for field in ('evidence_identity', 'support_checks', 'availability_status', 'visibility', 'protected_review'):
                if row[field] != actual[field]:
                    raise ValueError('claim graph material differs from the actual evidence ledger')
    validate_answer_basis_references(packet, evidence_ledger=ledger)
    from .stage_consumers_v4 import validate_stage_chain_v4
    stage_contract = run_contract or {**dict(binding), 'problem_contract': problem}
    checked_stages = validate_stage_chain_v4(packet, run_contract=stage_contract, repository_root=repository_root)
    outcomes = {stage: row['result'] for stage, row in checked_stages['stage_results'].items()}
    if packet.get('stage_outcomes') != outcomes:
        raise ValueError('stage outcomes differ from freshly recomputed semantic inputs')
    if 'domain_trace' in packet:
        from .domain_pipeline_v4 import validate_domain_inputs
        domain = packet.get('domain_binding')
        if not isinstance(domain, Mapping) or not isinstance(domain.get('plan'), Mapping):
            raise ValueError('domain packet requires its frozen runtime binding')
        checked = validate_domain_inputs(domain['plan'], packet['domain_trace'], graph=graph, run_contract=stage_contract, repository_root=repository_root, verified_instance_results=registry)
        if {key: value for key, value in domain.items() if key != 'plan'} != checked or packet.get('domain_read_trace') != checked['read_trace']:
            raise ValueError('domain packet differs from freshly reread domain content and semantic inputs')
    elif any(field in packet for field in ('domain_binding', 'domain_read_trace')):
        raise ValueError('domain runtime outcomes require their actual author semantic inputs')


__all__ = ('build_analysis_packet_v4', 'prepare_analysis_packet_v4', 'require_packet_contract_v4', 'validate_world_stage')
