"""Evidence-bound atomic scale contracts and their independent registries."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .world_volume import _canonical_sha256, _native_snapshot, _registered_time


SECTION_FIELDS = {
    "identity": "contract_id concept_id version proposition_ids purpose",
    "scale": "SP0 SP1 axis_differences unchanged_axes transformation_class j_authorization",
    "objects": "source_object target_object source_K target_K identity_mapping units population boundaries members exclusions",
    "semantics": "preserved_core allowed_changes lost_elements prohibited_mappings task_preservation",
    "transformation": "operator_ids selected_operator_branch claim_mode rules causal_bridge lag mapping_error validity root_instance_ids selected_subtype selected_success_criterion decision_rule null_decision_rule positive_threshold equivalence_or_sufficiency power_or_sensitivity tolerance result_state parent_representation",
    "variables": "inputs states outputs dependencies effective_variable_candidates",
    "evidence": "source_refs target_refs coverage heterogeneity counterexamples absence_signals alternatives residual_checks replication_or_external_validation task_checks",
    "loss": "compressed_details irrecoverable_information low_visibility_positions local_exclusions folded_differences return_positions",
    "responsibility": "actors decision_subjects authorizers carrying_vehicles responsible_subjects beneficiaries cost_bearers",
    "normative": "value_premises selection_kind selection_record normative_principle_ids authorization_sources c12_gate procedure_ids",
    "protection": "applicability low_power_positions safe_submission anti_retaliation",
    "action": "judgment_ceiling action_ceiling prohibited_actions stop_conditions action_owner selected_action",
    "correction": "appeal review rollback repair writeback",
    "lifecycle": "validity review_points pause exit",
}
FIELD_TYPES_BY_SECTION = {section: {field: (list,) for field in fields.split()} for section, fields in SECTION_FIELDS.items()}
for _section, _fields in {
    "identity": "contract_id concept_id version",
    "scale": "transformation_class",
    "transformation": "selected_operator_branch claim_mode selected_subtype selected_success_criterion result_state",
    "normative": "selection_kind",
    "action": "judgment_ceiling action_ceiling",
}.items():
    for _field in _fields.split():
        FIELD_TYPES_BY_SECTION[_section][_field] = (str,)
for _section, _fields in {
    "identity": "purpose", "scale": "SP0 SP1",
    "objects": "source_object target_object source_K target_K identity_mapping population",
    "semantics": "task_preservation",
    "transformation": "rules validity decision_rule null_decision_rule parent_representation",
    "evidence": "coverage", "normative": "selection_record c12_gate",
    "protection": "applicability safe_submission anti_retaliation",
    "action": "selected_action",
    "correction": "appeal review rollback repair", "lifecycle": "validity",
}.items():
    for _field in _fields.split():
        FIELD_TYPES_BY_SECTION[_section][_field] = (dict,)
for _field in ("lag", "mapping_error", "positive_threshold", "equivalence_or_sufficiency", "power_or_sensitivity", "tolerance"):
    FIELD_TYPES_BY_SECTION["transformation"][_field] = (dict, int, float)
for _field in ("units", "boundaries", "members"):
    FIELD_TYPES_BY_SECTION["objects"][_field] = (dict, list)
FIELD_TYPES_BY_SECTION["scale"]["j_authorization"] = (dict, list)
FIELD_TYPES_BY_SECTION["action"]["action_owner"] = (str, dict)
FIELD_TYPES_BY_SECTION["correction"]["writeback"] = (dict, list)
SCALE_MISSING_STATES = {"unknown", "not_applicable", "not_observable", "withheld_for_protection"}
K_CHECKS = ("source_under_source_K", "source_under_target_K", "target_under_source_K", "target_under_target_K")
RESULT_STATES = {"supported", "null_supported", "unsupported_or_undecided", "not_evaluated"}
SOURCE_BRANCHES = {
    "scale_operator:M02": {"descriptive_nesting": "descriptive_mapping", "cross_layer_causal": "causal", "object_conversion": "object_conversion", "intervention_conversion": "intervention_conversion"},
    "scale_operator:M05": {"institutional_fact": "descriptive_mapping", "institutional_causal_effect": "causal", "institutional_object_conversion": "object_conversion", "institutional_intervention_conversion": "intervention_conversion"},
    "scale_operator:M07": {"representation_claim": "descriptive_mapping", "actual_acts": "descriptive_mapping", "delegation_validity": "descriptive_mapping", "J_transfer": "descriptive_mapping"},
}


class ScaleContractError(ValueError):
    pass


def _missing(value: object) -> bool:
    return isinstance(value, dict) and value.get("status") in SCALE_MISSING_STATES


def _artifact(registry: Mapping[str, Mapping[str, Any]], identifier: str, id_field: str) -> dict[str, Any]:
    item = registry.get(identifier)
    if not isinstance(item, Mapping) or item.get(id_field) != identifier:
        raise ScaleContractError("independent registry artifact does not resolve")
    artifact = dict(item)
    declared_hash = artifact.pop("artifact_sha256", None)
    if declared_hash != _canonical_sha256(artifact):
        raise ScaleContractError("independent artifact hash differs from its actual content")
    return dict(item)


def classify_scale_relations(relations: set[str]) -> str:
    if not relations or not relations.issubset({"equal", "expands", "contracts", "incomparable", "unknown"}):
        raise ScaleContractError("scale relations are outside the closed vocabulary")
    if "incomparable" in relations:
        return "horizontal_or_incomparable"
    if {"expands", "contracts"}.issubset(relations):
        return "mixed"
    if "unknown" in relations:
        return "unresolved"
    if relations == {"equal"}:
        return "all_equal"
    return "elevation" if relations.issubset({"equal", "expands"}) else "reduction"


def validate_scale_instance(
    record: Mapping[str, Any], *,
    comparator_results: Mapping[str, Mapping[str, Any]],
    identity_mapping_results: Mapping[str, Mapping[str, Any]],
    root_instances: Mapping[str, Mapping[str, Any]],
    evidence_registry: Mapping[str, Mapping[str, Any]],
    evaluation_results: Mapping[str, Mapping[str, Any]],
    operator_branches: Mapping[str, Mapping[str, str]] | None = None,
    verification_artifacts: Mapping[str, Mapping[str, Any]] | None = None,
    representation_registry: Mapping[str, Mapping[str, Any]] | None = None,
    task_check_results: Mapping[str, Mapping[str, Any]] | None = None,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    contract = _native_snapshot(record, label="scale instance", error_type=ScaleContractError)
    if not isinstance(contract, dict) or set(contract) != set(SECTION_FIELDS):
        raise ScaleContractError("formal scale instance requires exactly fourteen sections")
    for section, fields in SECTION_FIELDS.items():
        content = contract[section]
        if not isinstance(content, dict) or set(content) != set(fields.split()):
            raise ScaleContractError(f"scale section has an inexact field set: {section}")
        for field, value in content.items():
            missing_record = isinstance(value, dict) and "status" in value and set(value).issubset({"status", "reason", "evidence_refs"})
            if missing_record:
                if value["status"] not in SCALE_MISSING_STATES or not isinstance(value.get("reason"), str) or not value["reason"].strip():
                    raise ScaleContractError("scale missing states require the exact four-state vocabulary and reason")
            elif type(value) not in FIELD_TYPES_BY_SECTION[section][field]:
                raise ScaleContractError(f"scale field has an invalid fixed type: {section}.{field}")
    identity, scale, objects, transform = (contract[key] for key in ("identity", "scale", "objects", "transformation"))
    if not all(isinstance(identity[key], str) and identity[key] for key in ("contract_id", "concept_id", "version")) or not isinstance(identity["proposition_ids"], list) or not identity["proposition_ids"]:
        raise ScaleContractError("scale identity is incomplete")
    from .v4_contracts import v4_authority

    try:
        source_concepts, _anchors, source_dependencies = v4_authority(repository_root)
    except ValueError as error:
        raise ScaleContractError(str(error)) from error
    if identity["concept_id"] not in source_concepts:
        raise ScaleContractError("formal scale concept identity does not resolve actual P03 authority")
    task = identity["purpose"]
    task_keys = {"target_task", "use_scope", "target_quantity", "horizon", "environment", "allowed_operations", "tolerance"}
    if not isinstance(task, dict) or not task_keys.issubset(task) or any(_missing(task[key]) for key in task_keys):
        raise ScaleContractError("scale task boundary must be frozen before comparisons")
    if not isinstance(task["use_scope"], list) or not task["use_scope"] or not isinstance(task["allowed_operations"], list) or not task["allowed_operations"]:
        raise ScaleContractError("scale task requires declared uses and operations")
    task_hash = _canonical_sha256(task)
    preservation = contract["semantics"]["task_preservation"]
    if not isinstance(preservation, dict) or set(preservation) != {"target_quantity", "preserved_for_task", "allowed_changes", "validity_conditions"} or preservation["target_quantity"] != task["target_quantity"] or not isinstance(preservation["preserved_for_task"], list) or not isinstance(preservation["allowed_changes"], list) or not preservation["validity_conditions"]:
        raise ScaleContractError("task preservation must bind the declared quantity and validity conditions")
    for side in ("source", "target"):
        obj, criterion = objects[side + "_object"], objects[side + "_K"]
        if not isinstance(obj, dict) or not obj.get("object_id") or not isinstance(criterion, dict) or set(criterion) != {"version", "definition"} or not criterion["version"] or not criterion["definition"]:
            raise ScaleContractError("scale object and K must be explicit nonempty registered values")

    def resolve_evidence(refs: object, *, target_hash: str | None = None) -> None:
        if not isinstance(refs, list) or not refs:
            raise ScaleContractError("empirical scale responsibility requires external evidence")
        for ref in refs:
            evidence = evidence_registry.get(ref)
            if not isinstance(evidence, Mapping) or evidence.get("evidence_id") != ref or not evidence.get("source_refs"):
                raise ScaleContractError("scale evidence does not resolve an independent source")
            if target_hash is not None and evidence.get("object_sha256") != target_hash:
                raise ScaleContractError("scale evidence object content binding differs")
            if evidence.get("identity") in {"definition", "framework", "simulated", "hypothetical"}:
                raise ScaleContractError("source definitions and simulations are not object evidence")

    resolve_evidence(contract["evidence"]["source_refs"], target_hash=_canonical_sha256(objects["source_object"]))
    resolve_evidence(contract["evidence"]["target_refs"], target_hash=_canonical_sha256(objects["target_object"]))
    checks_consumed: dict[str, str] = {}

    def task_check(identifier: str, expected: Mapping[str, Any] | None = None) -> dict[str, Any]:
        check = _artifact(task_check_results or {}, identifier, "check_id")
        if check.get("task_sha256") != task_hash or check.get("result") not in RESULT_STATES:
            raise ScaleContractError("independent task/reconstruction check has a different task or result")
        if expected is not None and (check["result"] != expected["result"] or check.get("scope") != expected["scope"]):
            raise ScaleContractError("declared task check differs from the independently verified artifact")
        resolve_evidence(check.get("evidence_refs"))
        checks_consumed[identifier] = check["result"]
        return check

    task_rows = contract["evidence"]["task_checks"]
    if not _missing(task_rows):
        for row in task_rows:
            if not isinstance(row, dict) or set(row) != {"check_id", "task_ref", "evidence_refs", "result", "tolerance_ref", "scope"} or row["task_ref"] != task["target_task"] or row["tolerance_ref"] != task["tolerance"]:
                raise ScaleContractError("task check must bind the declared target task, scope and tolerance")
            resolve_evidence(row["evidence_refs"])
            task_check(row["check_id"], row)
    parents_consumed: list[str] = []
    reconstruction_results: dict[str, str] = {}
    parent_binding = transform["parent_representation"]
    parent_locations: set[str] = set()
    if not _missing(parent_binding):
        if set(parent_binding) != {"representation_id", "version", "content_hash", "mapping_ref", "reconstruction_method_ref"}:
            raise ScaleContractError("parent representation lineage has an inexact field set")
        parent = _artifact(representation_registry or {}, parent_binding["representation_id"], "representation_id")
        if parent_binding["content_hash"] != _canonical_sha256(parent.get("content")) or any(_canonical_sha256(parent_binding[key]) != _canonical_sha256(parent.get(key)) for key in ("version", "mapping_ref", "reconstruction_method_ref")) or parent.get("source_object_sha256") != _canonical_sha256(objects["source_object"]) or parent.get("task_sha256") != task_hash:
            raise ScaleContractError("parent representation content, mapping, method or task binding changed")
        content = parent.get("content")
        if isinstance(content, dict):
            parent_locations.update(content)
            for component in content.get("components", []):
                if isinstance(component, dict) and isinstance(component.get("component_ref"), str):
                    parent_locations.add(component["component_ref"])
        parents_consumed.append(parent_binding["representation_id"])
    folded = contract["loss"]["folded_differences"]
    if not _missing(folded):
        for difference in folded:
            if not isinstance(difference, dict) or set(difference) != {"component_ref", "difference", "recoverability", "affected_task_refs"} or difference["component_ref"] not in parent_locations or not difference["difference"] or not difference["recoverability"] or task["target_task"] not in difference["affected_task_refs"]:
                raise ScaleContractError("folded difference does not resolve the actual parent/task scope")
    returns = contract["loss"]["return_positions"]
    if not _missing(returns):
        for position in returns:
            if not isinstance(position, dict) or set(position) != {"parent_location_ref", "return_condition", "reconstruction_check_ref"} or position["parent_location_ref"] not in parent_locations or not position["return_condition"]:
                raise ScaleContractError("return position does not resolve the retained parent representation")
            check = task_check(position["reconstruction_check_ref"])
            if check.get("scope") != "reconstruction":
                raise ScaleContractError("return position references a task-sufficiency check instead of reconstruction")
            reconstruction_results[position["reconstruction_check_ref"]] = check["result"]
    candidates = contract["variables"]["effective_variable_candidates"]
    if not _missing(candidates):
        for candidate in candidates:
            if not isinstance(candidate, dict) or set(candidate) != {"variable_id", "source_location_refs", "task_ref", "candidate_reason", "validation_refs"} or not candidate["variable_id"].startswith("XK-PROV-") or candidate["task_ref"] != task["target_task"] or not candidate["candidate_reason"] or not candidate["source_location_refs"] or not set(candidate["source_location_refs"]).issubset(parent_locations):
                raise ScaleContractError("effective-variable candidate must remain provisional and resolve actual parent locations")
            for ref in candidate["validation_refs"]:
                task_check(ref)
    for profile_key in ("SP0", "SP1"):
        if not isinstance(scale[profile_key], dict) or set(scale[profile_key]) != set("AXTOCRINJ"):
            raise ScaleContractError("scale profile must have all nine distinct axes")
    rows = scale["axis_differences"]
    if not isinstance(rows, list) or len(rows) != 9 or {row.get("axis_id") for row in rows} != set("AXTOCRINJ"):
        raise ScaleContractError("scale comparisons must cover nine distinct axes")
    consumed: list[str] = []
    for row in rows:
        if set(row) != {"axis_id", "relation", "comparator_result_id", "artifact_sha256"}:
            raise ScaleContractError("axis comparison cannot self-certify a witness")
        if row["relation"] == "unknown":
            if row["comparator_result_id"] is not None or row["artifact_sha256"] is not None:
                raise ScaleContractError("unknown axis cannot carry a validated comparator")
            continue
        artifact = _artifact(comparator_results, row["comparator_result_id"], "result_id")
        expected = {"axis_id": row["axis_id"], "relation": row["relation"], "source_profile_sha256": _canonical_sha256(scale["SP0"]), "target_profile_sha256": _canonical_sha256(scale["SP1"]), "task_sha256": task_hash, "contract_version": identity["version"], "artifact_sha256": row["artifact_sha256"]}
        if any(artifact.get(key) != value for key, value in expected.items()) or artifact.get("valid") is not True:
            raise ScaleContractError("axis comparator is not bound to this profile/task/version")
        payload = artifact.get("comparison_payload")
        if not isinstance(payload, dict) or _canonical_sha256(payload.get("source")) != _canonical_sha256(scale["SP0"][row["axis_id"]]) or _canonical_sha256(payload.get("target")) != _canonical_sha256(scale["SP1"][row["axis_id"]]) or not isinstance(payload.get("witness"), dict) or not payload["witness"] or payload["witness"].get("relation") != row["relation"]:
            raise ScaleContractError("axis comparator lacks its independent structured witness")
        resolve_evidence(artifact.get("evidence_refs"))
        if row["relation"] == "equal" and _canonical_sha256(payload["source"]) != _canonical_sha256(payload["target"]):
            raise ScaleContractError("equality witness differs from actual axis values")
        consumed.append(row["comparator_result_id"])
    classification = classify_scale_relations({row["relation"] for row in rows})
    if classification != scale["transformation_class"] or set(scale["unchanged_axes"]) != {row["axis_id"] for row in rows if row["relation"] == "equal"}:
        raise ScaleContractError("scale classification or unchanged axes differs from verified comparisons")
    operators = transform["operator_ids"]
    if not isinstance(operators, list) or len(operators) != 1 or operators[0] not in {f"scale_operator:M{i:02d}" for i in range(1, 10)}:
        raise ScaleContractError("atomic scale record requires one qualified M01-M09 operator")
    if operators[0] not in {concept["source_concept_id"] for concept in source_concepts.values()}:
        raise ScaleContractError("qualified scale operator does not resolve actual P03 source identity")
    branches = SOURCE_BRANCHES.get(operators[0], (operator_branches or {}).get(operators[0], {}))
    mode, result = transform["claim_mode"], transform["result_state"]
    if branches.get(transform["selected_operator_branch"]) != mode or result not in RESULT_STATES:
        raise ScaleContractError("scale branch, mode or result is not independently registered")
    if result in {"supported", "null_supported"} and (not isinstance(transform["rules"], dict) or _missing(transform["rules"]) or not transform["rules"]):
        raise ScaleContractError("supported scale mapping requires its concrete operator bridge")
    if operators[0] == "scale_operator:M02" and result in {"supported", "null_supported"}:
        rules = transform["rules"]
        if not {"boundary_map", "member_map", "overlap_map", "exit_map", "interface_map"}.issubset(rules) or any(_missing(rules[key]) for key in ("boundary_map", "member_map", "overlap_map", "exit_map", "interface_map")):
            raise ScaleContractError("M02 description needs boundary/member/overlap/exit/interface mappings")
    mapping = objects["identity_mapping"]
    if not isinstance(mapping, dict) or mapping.get("classification") not in {"same_object", "converted_object", "incomparable", "undetermined"}:
        raise ScaleContractError("scale K mapping classification is missing")
    mapping_class = mapping["classification"]
    if mapping.get("mapping_id") == "builtin:deep-identity":
        if mapping_class != "same_object" or _canonical_sha256(objects["source_object"]) != _canonical_sha256(objects["target_object"]) or _canonical_sha256(objects["source_K"]) != _canonical_sha256(objects["target_K"]):
            raise ScaleContractError("builtin deep identity requires both objects and both Ks deep-equal")
    else:
        mapping_result = _artifact(identity_mapping_results, mapping.get("mapping_id"), "mapping_id")
        digests = {key + "_sha256": _canonical_sha256(objects[key]) for key in ("source_object", "target_object", "source_K", "target_K")}
        if mapping.get("artifact_sha256") != mapping_result["artifact_sha256"] or mapping_result.get("classification") != mapping_class or any(mapping_result.get(key) != value for key, value in digests.items()):
            raise ScaleContractError("K mapping is not bound to both actual objects and both Ks")
        checks = mapping_result.get("criterion_results")
        if not isinstance(checks, dict) or set(checks) != set(K_CHECKS) or not set(checks.values()).issubset({"passed", "failed", "undetermined"}):
            raise ScaleContractError("K mapping must expose all four typed criterion results")
        if digests["source_K_sha256"] == digests["target_K_sha256"] and (checks["source_under_source_K"] != checks["source_under_target_K"] or checks["target_under_source_K"] != checks["target_under_target_K"]):
            raise ScaleContractError("identical K criteria cannot produce contradictory checks on the same object")
        if digests["source_object_sha256"] == digests["target_object_sha256"] and (checks["source_under_source_K"] != checks["target_under_source_K"] or checks["source_under_target_K"] != checks["target_under_target_K"]):
            raise ScaleContractError("identical object content cannot produce contradictory checks under a frozen K")
        direction_results = []
        for direction in ("forward_mapping", "reverse_mapping"):
            attempt = mapping_result.get(direction)
            if not isinstance(attempt, dict) or attempt.get("status") not in {"valid", "invalid", "not_run"}:
                raise ScaleContractError("K mapping requires both direction attempts")
            if attempt["status"] != "not_run":
                resolve_evidence(attempt.get("evidence_refs"))
            direction_results.append(attempt["status"])
        preserved, violated = mapping_result.get("preserved_criteria"), mapping_result.get("violated_criteria")
        if not isinstance(preserved, list) or not isinstance(violated, list):
            raise ScaleContractError("K mapping must separate preserved and violated criteria")
        if mapping_class == "same_object" and (set(checks.values()) != {"passed"} or direction_results != ["valid", "valid"] or not preserved or violated):
            raise ScaleContractError("same object requires four passed checks and valid bidirectional mapping")
        if mapping_class == "converted_object" and (checks["source_under_source_K"] != "passed" or checks["target_under_target_K"] != "passed" or checks["target_under_source_K"] != "failed" or not violated):
            raise ScaleContractError("converted object requires concrete own-K success and cross-K failure")
        if mapping_class == "incomparable" and (checks["source_under_source_K"] != "passed" or checks["target_under_target_K"] != "passed" or "failed" not in {checks["source_under_target_K"], checks["target_under_source_K"]} or "invalid" not in direction_results or "not_run" in direction_results):
            raise ScaleContractError("known incomparable requires completed failed cross-K mapping")
        if mapping_class == "undetermined" and set(checks.values()) != {"undetermined"}:
            raise ScaleContractError("undetermined mapping cannot claim tested identity or conversion")
        if mapping_class in {"incomparable", "undetermined"} and result not in {"unsupported_or_undecided", "not_evaluated"} or mapping_class == "incomparable" and result == "not_evaluated":
            raise ScaleContractError("known mapping failure and unrun mapping have distinct result ceilings")
        preregistration = mapping_result.get("preregistration")
        if not isinstance(preregistration, dict) or not preregistration.get("preregistration_id") or _registered_time(preregistration.get("frozen_at"), "K mapping preregistration") >= _registered_time(preregistration.get("result_accessed_at"), "K mapping result access"):
            raise ScaleContractError("K mapping criterion must be frozen before result access")
        refs = mapping_result.get("verification_artifact_refs")
        if not isinstance(refs, list) or not refs:
            raise ScaleContractError("nontrivial K mapping requires independent verification artifacts")
        for ref in refs:
            proof = _artifact(verification_artifacts or {}, ref, "artifact_id")
            content = proof.get("content")
            if not isinstance(content, dict) or content.get("mapping_id") != mapping["mapping_id"] or content.get("criterion_results") != checks or any(content.get(key) != value for key, value in digests.items()):
                raise ScaleContractError("K verification artifact does not cover the actual mapping criteria")
        resolve_evidence(mapping_result.get("evidence_refs"))
    if mapping_class == "converted_object" and mode != "object_conversion":
        raise ScaleContractError("object conversion requires its own atomic mode")
    if mode == "descriptive_mapping":
        if any(not _missing(transform[key]) or transform[key]["status"] != "not_applicable" for key in ("root_instance_ids", "selected_subtype", "selected_success_criterion")):
            raise ScaleContractError("descriptive mapping must explicitly mark root-only responsibility not applicable")
    else:
        from .scale_root_bindings import EvaluatedScaleRootRegistry

        if result in {"supported", "null_supported"} and type(root_instances) is not EvaluatedScaleRootRegistry:
            raise ScaleContractError("formal root support requires a code-recomputed P05 registry from raw frozen inputs")
        if not isinstance(transform["root_instance_ids"], list) or not transform["root_instance_ids"]:
            raise ScaleContractError("non-descriptive scale claims require actual immutable root instances")
        if mode in {"causal", "object_conversion", "intervention_conversion"} and (not isinstance(transform["causal_bridge"], list) or not transform["causal_bridge"]):
            raise ScaleContractError("scale causal or conversion mode lacks a causal bridge")
        if not isinstance(transform["selected_subtype"], str) or not isinstance(transform["selected_success_criterion"], str):
            raise ScaleContractError("root mode requires one preselected subtype and success criterion")
        scope_hash = _canonical_sha256({"SP0": scale["SP0"], "SP1": scale["SP1"], "source_K": objects["source_K"], "target_K": objects["target_K"], "task": task})
        if len(transform["root_instance_ids"]) != len(set(transform["root_instance_ids"])):
            raise ScaleContractError("scale root instance IDs must be unique")
        for instance_id in transform["root_instance_ids"]:
            root = _artifact(root_instances, instance_id, "instance_id")
            if type(root_instances) is EvaluatedScaleRootRegistry and (root.get("operator_ids") != transform["operator_ids"] or root.get("selected_operator_branch") != transform["selected_operator_branch"] or root.get("claim_mode") != mode):
                raise ScaleContractError("scale root mode differs from its preselected operator and branch")
            if root.get("root_id") not in {"G1", "G2", "G3", "G4"} or any(root.get(key) != expected for key, expected in {"contract_version": identity["version"], "selected_subtype": transform["selected_subtype"], "selected_success_criterion": transform["selected_success_criterion"], "result_state": result, "scope_sha256": scope_hash}.items()):
                raise ScaleContractError("scale root family, version, criterion, result or scope does not match")
            if result in {"supported", "null_supported"}:
                if root.get("eligibility_status") != "eligible" or _registered_time(root.get("preregistration_timestamp"), "root preregistration") >= _registered_time(root.get("result_timestamp"), "root result"):
                    raise ScaleContractError("root support requires actual eligible preregistered evaluation")
                resolve_evidence(root.get("evidence_refs"))
                refs = root.get("analysis_artifact_refs")
                if not isinstance(refs, list) or not refs:
                    raise ScaleContractError("supported root requires independent analysis artifacts")
                for ref in refs:
                    _artifact(verification_artifacts or {}, ref, "artifact_id")
            if mode == "object_conversion" and (root.get("root_id") != "G4" or root.get("selected_subtype") != "G4b"):
                raise ScaleContractError("object conversion requires a supported G4b instance")
            if operators[0] == "scale_operator:M02" and mode != "root_hypothesis" and root.get("root_id") != "G4":
                raise ScaleContractError("cross-layer M02 modes require their registered G4 root")
    if mode == "object_conversion":
        allowed_mapping = {"supported": {"converted_object"}, "null_supported": {"same_object"}, "unsupported_or_undecided": {"same_object", "incomparable", "undetermined"}, "not_evaluated": {"undetermined"}}
        if mapping_class not in allowed_mapping[result]:
            raise ScaleContractError("object-conversion mapping contradicts the actual result state")
    applicability = contract["protection"]["applicability"]
    if not isinstance(applicability, dict) or set(applicability) != {"object_type", "downstream_uses", "reason", "evidence_refs"} or not applicability["reason"] or applicability["downstream_uses"] != task["use_scope"]:
        raise ScaleContractError("protection applicability must freeze object type and downstream uses")
    resolve_evidence(applicability["evidence_refs"])
    pure_description = applicability["object_type"] == "nonhuman" and applicability["downstream_uses"] == ["description_only"] and task["allowed_operations"] == ["describe"]
    if not pure_description and any(_missing(contract["protection"][key]) for key in ("low_power_positions", "safe_submission", "anti_retaliation")):
        raise ScaleContractError("human or changed-use protection floor is compulsory")
    if not pure_description and _missing(scale["j_authorization"]):
        raise ScaleContractError("real intervention requires exact J authorization")
    if contract["action"]["action_ceiling"] not in {"deliberation_only", "no_new_action"} or not _missing(contract["action"]["selected_action"]):
        raise ScaleContractError("external action requires the separate atomic selection/authorization validator")
    if result == "supported":
        rule = transform["decision_rule"]
        if not isinstance(rule, dict) or set(rule) != {"preregistered_at", "result_accessed_at", "evaluation_id"}:
            raise ScaleContractError("positive result requires its preregistered decision rule")
        if _registered_time(rule["preregistered_at"], "preregistration") >= _registered_time(rule["result_accessed_at"], "result access"):
            raise ScaleContractError("decision rule must precede result access")
        evaluation = evaluation_results.get(rule["evaluation_id"])
        if not isinstance(evaluation, Mapping) or evaluation.get("evaluation_id") != rule["evaluation_id"] or evaluation.get("contract_id") != identity["contract_id"] or evaluation.get("task_sha256") != task_hash:
            raise ScaleContractError("decision result does not resolve the independent evaluation")
        threshold, value = transform["positive_threshold"], evaluation.get("observed_value")
        if type(threshold) not in {int, float} or type(value) not in {int, float} or evaluation.get("operator") not in {"ge", "le"} or not (value >= threshold if evaluation["operator"] == "ge" else value <= threshold):
            raise ScaleContractError("independent result fails the frozen positive threshold")
        resolve_evidence(evaluation.get("evidence_refs"))
    elif result == "null_supported":
        rule = transform["null_decision_rule"]
        gates = {"equivalence_or_sufficiency", "power_or_sensitivity", "tolerance"}
        if not isinstance(rule, dict) or not isinstance(rule.get("evaluation_ids"), dict) or set(rule["evaluation_ids"]) != gates:
            raise ScaleContractError("null support requires all three independently evaluated null gates")
        if _registered_time(rule.get("preregistered_at"), "null preregistration") >= _registered_time(rule.get("result_accessed_at"), "null result access"):
            raise ScaleContractError("null decision rule must precede result access")
        if len(set(rule["evaluation_ids"].values())) != 3:
            raise ScaleContractError("null gates require distinct evaluation identities")
        for gate, evaluation_id in rule["evaluation_ids"].items():
            declared = transform[gate]
            evaluation = evaluation_results.get(evaluation_id)
            if not isinstance(declared, dict) or declared.get("evaluation_id") != evaluation_id or not isinstance(evaluation, Mapping) or any(evaluation.get(key) != expected for key, expected in {"evaluation_id": evaluation_id, "contract_id": identity["contract_id"], "task_sha256": task_hash, "gate": gate, "result": "passed"}.items()):
                raise ScaleContractError("null support gate is missing, failed or bound to another task")
            resolve_evidence(evaluation.get("evidence_refs"))
    return {"contract_id": identity["contract_id"], "contract_sha256": _canonical_sha256(contract), "task_sha256": task_hash, "transformation_class": classification, "mapping_class": mapping_class, "result_state": result, "consumed_comparator_ids": consumed, "consumed_representation_ids": parents_consumed, "task_check_results": checks_consumed, "reconstruction_results": reconstruction_results, "source_revision": source_dependencies["source_raw_sha256"]}


def evaluate_task_partition(representation_by_source: Mapping[str, Any], answer_by_source: Mapping[str, Any]) -> dict[str, Any]:
    if not representation_by_source or set(representation_by_source) != set(answer_by_source):
        raise ScaleContractError("finite task check needs the same nonempty declared source domain")
    groups: dict[str, list[str]] = {}
    for source, representation in representation_by_source.items():
        groups.setdefault(_canonical_sha256(representation), []).append(source)
    sufficient = all(len({_canonical_sha256(answer_by_source[source]) for source in sources}) == 1 for sources in groups.values())
    return {"task_sufficient": sufficient, "reconstructable": all(len(sources) == 1 for sources in groups.values()), "source_domain": sorted(representation_by_source), "scope": "declared finite domain only", "representation_sha256": _canonical_sha256(representation_by_source), "answer_sha256": _canonical_sha256(answer_by_source)}


def validate_scale_chain(records: list[Mapping[str, Any]], **registries: Any) -> dict[str, Any]:
    if not records:
        raise ScaleContractError("scale chain must contain an atomic record")
    identifiers = [record["identity"]["contract_id"] for record in records]
    if len(identifiers) != len(set(identifiers)):
        raise ScaleContractError("scale chain contract IDs must be unique")
    steps = [validate_scale_instance(record, **registries) for record in records]
    for previous, current in zip(records, records[1:]):
        if any(_canonical_sha256(left) != _canonical_sha256(right) for left, right in (
            (previous["objects"]["target_object"], current["objects"]["source_object"]),
            (previous["objects"]["target_K"], current["objects"]["source_K"]),
            (previous["scale"]["SP1"], current["scale"]["SP0"]),
        )):
            raise ScaleContractError("adjacent scale steps do not preserve object/K/SP continuity")
    unresolved = [step["contract_id"] for step in steps if step["result_state"] in {"unsupported_or_undecided", "not_evaluated"}]
    return {"steps": steps, "unresolved_contract_ids": unresolved, "chain_sha256": _canonical_sha256(records)}
