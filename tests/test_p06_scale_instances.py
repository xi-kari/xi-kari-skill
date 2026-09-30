from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from xi_kari_runtime import transformations, world_volume


FIELDS = {
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


def missing(reason="Not applicable to the synthetic pure description"):
    return {"status": "not_applicable", "reason": reason}


def scale_fixture():
    record = {section: {field: missing() for field in fields.split()} for section, fields in FIELDS.items()}
    task = {"target_task": "describe nested boundary", "use_scope": ["description_only"], "target_quantity": "membership", "horizon": "frozen window", "environment": "synthetic", "allowed_operations": ["describe"], "tolerance": "exact"}
    record["identity"].update(contract_id="SCALE-1", concept_id="V90-CANON-D3", version="4.0.0", proposition_ids=["CLAIM-1"], purpose=task)
    source = {"object_id": "OBJECT-N", "boundary": ["unit-1", "unit-2"]}
    criterion = {"version": "1", "definition": "same bounded synthetic units"}
    record["objects"].update(source_object=source, target_object=deepcopy(source), source_K=criterion, target_K=deepcopy(criterion), identity_mapping={"mapping_id": "builtin:deep-identity", "classification": "same_object"})
    profile = dict.fromkeys("AXTOCRINJ", "same declared profile")
    record["scale"].update(SP0=profile, SP1=deepcopy(profile), axis_differences=[], unchanged_axes=list("AXTOCRINJ"), transformation_class="all_equal")
    comparators = {}
    for axis in "AXTOCRINJ":
        payload = {"source": profile[axis], "target": profile[axis], "witness": {"relation": "equal", "scope": "synthetic exact identity"}}
        artifact = {"result_id": "CMP-" + axis, "axis_id": axis, "relation": "equal", "valid": True, "source_profile_sha256": world_volume._canonical_sha256(profile), "target_profile_sha256": world_volume._canonical_sha256(profile), "task_sha256": world_volume._canonical_sha256(task), "contract_version": "4.0.0", "comparison_payload": payload, "evidence_refs": ["E-OBJECT"]}
        comparators["CMP-" + axis] = {**artifact, "artifact_sha256": world_volume._canonical_sha256(artifact)}
        record["scale"]["axis_differences"].append({"axis_id": axis, "relation": "equal", "comparator_result_id": "CMP-" + axis, "artifact_sha256": comparators["CMP-" + axis]["artifact_sha256"]})
    record["transformation"].update(operator_ids=["scale_operator:M02"], selected_operator_branch="descriptive_nesting", claim_mode="descriptive_mapping", rules={"boundary_map": "identity", "member_map": "identity", "overlap_map": [], "exit_map": [], "interface_map": []}, decision_rule={"preregistered_at": "2026-09-29T00:00:00Z", "result_accessed_at": "2026-09-30T00:00:00Z", "evaluation_id": "EVAL-1"}, positive_threshold=1, result_state="supported")
    record["semantics"].update(preserved_core=["boundary and member identity"], allowed_changes=[], lost_elements=[], prohibited_mappings=["description does not authorize intervention"], task_preservation={"target_quantity": "membership", "preserved_for_task": ["boundary"], "allowed_changes": [], "validity_conditions": ["frozen description only"]})
    record["evidence"].update(source_refs=["E-OBJECT"], target_refs=["E-OBJECT"], task_checks=[{"check_id": "CHECK-1", "task_ref": "describe nested boundary", "evidence_refs": ["E-OBJECT"], "result": "supported", "tolerance_ref": "exact", "scope": "description"}])
    record["protection"]["applicability"] = {"object_type": "nonhuman", "downstream_uses": ["description_only"], "reason": "Synthetic natural-object description", "evidence_refs": ["E-OBJECT"]}
    record["action"].update(judgment_ceiling="bounded_description", action_ceiling="deliberation_only", selected_action=missing(), stop_conditions=["purpose change"])
    record["lifecycle"].update(validity={"window": "frozen"}, review_points=["purpose change"], pause=["identity failure"], exit=["window end"])
    registries = {
        "comparator_results": comparators, "identity_mapping_results": {}, "root_instances": {},
        "evidence_registry": {"E-OBJECT": {"evidence_id": "E-OBJECT", "identity": "observed", "source_refs": ["SYNTHETIC-UNIT-FIXTURE"], "object_sha256": world_volume._canonical_sha256(source)}},
        "evaluation_results": {"EVAL-1": {"evaluation_id": "EVAL-1", "contract_id": "SCALE-1", "task_sha256": world_volume._canonical_sha256(task), "observed_value": 1, "operator": "ge", "evidence_refs": ["E-OBJECT"]}},
    }
    return record, registries


def test_complete_formal_description_consumes_nine_independent_comparators():
    record, registries = scale_fixture()
    result = transformations.validate_scale_instance(record, **registries)
    assert result["transformation_class"] == "all_equal"
    assert result["result_state"] == "supported"
    assert result["contract_id"] == "SCALE-1"
    assert set(result["consumed_comparator_ids"]) == {"CMP-" + axis for axis in "AXTOCRINJ"}


@pytest.mark.parametrize("mutation", ["missing_section", "fifteenth", "missing_field", "ghost_comparator", "internal_valid", "wrong_task", "K_name_only", "extra_operator", "missing_root", "human_floor"])
def test_formal_scale_instance_rejects_unproved_responsibility(mutation):
    record, registries = scale_fixture()
    if mutation == "missing_section": del record["loss"]
    if mutation == "fifteenth": record["task"] = {"valid": True}
    if mutation == "missing_field": del record["variables"]["dependencies"]
    if mutation == "ghost_comparator": del registries["comparator_results"]["CMP-A"]
    if mutation == "internal_valid": registries["comparator_results"] = {}; record["scale"]["axis_differences"][0]["valid"] = True
    if mutation == "wrong_task": record["identity"]["purpose"]["allowed_operations"] = ["intervene"]
    if mutation == "K_name_only": record["objects"]["target_K"]["definition"] = "different definition with same object name"
    if mutation == "extra_operator": record["transformation"]["operator_ids"].append("scale_operator:M08")
    if mutation == "missing_root": record["transformation"].update(claim_mode="causal", selected_operator_branch="cross_layer_causal", causal_bridge=["claimed bridge"])
    if mutation == "human_floor": record["protection"]["applicability"].update(object_type="human", downstream_uses=["allocation"])
    with pytest.raises(transformations.TransformationError):
        transformations.validate_scale_instance(record, **registries)


@pytest.mark.parametrize("relations,expected", [({"incomparable", "unknown"}, "horizontal_or_incomparable"), ({"expands", "contracts", "unknown"}, "mixed"), ({"equal", "unknown"}, "unresolved")])
def test_known_axis_conflicts_precede_unknown_axes(relations, expected):
    assert transformations.classify_scale_relations(relations) == expected


def attach_mapping(record, registries, classification="same_object"):
    obj = record["objects"]
    digests = {key + "_sha256": world_volume._canonical_sha256(obj[key]) for key in ("source_object", "target_object", "source_K", "target_K")}
    checks = dict.fromkeys(("source_under_source_K", "source_under_target_K", "target_under_source_K", "target_under_target_K"), "passed")
    if classification == "converted_object": checks["target_under_source_K"] = "failed"
    mapping = {"mapping_id": "MAP-1", "classification": classification, **digests, "criterion_results": checks,
        "forward_mapping": {"status": "valid", "evidence_refs": ["E-OBJECT"]}, "reverse_mapping": {"status": "valid", "evidence_refs": ["E-OBJECT"]},
        "preserved_criteria": ["tracked boundary"], "violated_criteria": ["old boundary"] if classification == "converted_object" else [],
        "preregistration": {"preregistration_id": "PRE-MAP-1", "frozen_at": "2026-09-29T00:00:00Z", "result_accessed_at": "2026-09-30T00:00:00Z"},
        "verification_artifact_refs": ["VER-MAP-1"], "evidence_refs": ["E-OBJECT"]}
    registries["identity_mapping_results"]["MAP-1"] = {**mapping, "artifact_sha256": world_volume._canonical_sha256(mapping)}
    proof = {"artifact_id": "VER-MAP-1", "content": {"mapping_id": "MAP-1", "criterion_results": checks, **digests}}
    registries["verification_artifacts"] = {"VER-MAP-1": {**proof, "artifact_sha256": world_volume._canonical_sha256(proof)}}
    obj["identity_mapping"] = {"mapping_id": "MAP-1", "classification": classification, "artifact_sha256": registries["identity_mapping_results"]["MAP-1"]["artifact_sha256"]}


def test_nontrivial_K_mapping_uses_all_four_criteria_and_verification_artifact():
    record, registries = scale_fixture()
    attach_mapping(record, registries)
    assert transformations.validate_scale_instance(record, **registries)["mapping_class"] == "same_object"
    registries["verification_artifacts"]["VER-MAP-1"]["content"]["criterion_results"]["source_under_target_K"] = "failed"
    with pytest.raises(transformations.TransformationError, match="artifact"):
        transformations.validate_scale_instance(record, **registries)


def test_object_conversion_requires_exact_supported_G4b_root():
    record, registries = scale_fixture()
    attach_mapping(record, registries, "converted_object")
    record["transformation"].update(claim_mode="object_conversion", selected_operator_branch="object_conversion", root_instance_ids=["ROOT-1"], selected_subtype="G4b", selected_success_criterion="object_conversion", causal_bridge=["synthetic verified bridge"])
    root = {"instance_id": "ROOT-1", "root_id": "G4", "contract_version": "4.0.0", "selected_subtype": "G4b", "selected_success_criterion": "object_conversion", "result_state": "supported", "eligibility_status": "eligible", "scope_sha256": world_volume._canonical_sha256({"SP0": record["scale"]["SP0"], "SP1": record["scale"]["SP1"], "source_K": record["objects"]["source_K"], "target_K": record["objects"]["target_K"], "task": record["identity"]["purpose"]}), "preregistration_timestamp": "2026-09-29T00:00:00Z", "result_timestamp": "2026-09-30T00:00:00Z", "evidence_refs": ["E-OBJECT"], "analysis_artifact_refs": ["VER-MAP-1"]}
    registries["root_instances"]["ROOT-1"] = {**root, "artifact_sha256": world_volume._canonical_sha256(root)}
    assert transformations.validate_scale_instance(record, **registries)["mapping_class"] == "converted_object"
    for field, value in (("selected_subtype", "G4a"), ("result_state", "unsupported_or_undecided"), ("eligibility_status", "ineligible")):
        changed = deepcopy(registries)
        changed["root_instances"]["ROOT-1"][field] = value
        with pytest.raises(transformations.TransformationError):
            transformations.validate_scale_instance(record, **changed)


def test_irrecoverable_finite_representation_can_be_sufficient_for_declared_task():
    result = transformations.evaluate_task_partition({"x1": "z", "x2": "z"}, {"x1": "same answer", "x2": "same answer"})
    assert result["task_sufficient"] is True
    assert result["reconstructable"] is False
    assert transformations.evaluate_task_partition({"x1": "z", "x2": "z"}, {"x1": "different intervention effect", "x2": "other effect"})["task_sufficient"] is False


def test_null_support_requires_three_preregistered_independent_gates():
    record, registries = scale_fixture()
    rule = {"preregistered_at": "2026-09-29T00:00:00Z", "result_accessed_at": "2026-09-30T00:00:00Z", "evaluation_ids": {}}
    for gate in ("equivalence_or_sufficiency", "power_or_sensitivity", "tolerance"):
        identifier = "NULL-" + gate
        rule["evaluation_ids"][gate] = identifier
        record["transformation"][gate] = {"evaluation_id": identifier}
        registries["evaluation_results"][identifier] = {"evaluation_id": identifier, "contract_id": "SCALE-1", "task_sha256": world_volume._canonical_sha256(record["identity"]["purpose"]), "gate": gate, "result": "passed", "evidence_refs": ["E-OBJECT"]}
    record["transformation"].update(result_state="null_supported", null_decision_rule=rule)
    assert transformations.validate_scale_instance(record, **registries)["result_state"] == "null_supported"
    del registries["evaluation_results"]["NULL-power_or_sensitivity"]
    with pytest.raises(transformations.TransformationError, match="null"):
        transformations.validate_scale_instance(record, **registries)


def test_scale_chain_retains_earlier_unresolved_step_and_unique_contracts():
    first, registries = scale_fixture()
    second = deepcopy(first)
    first["transformation"]["result_state"] = "unsupported_or_undecided"
    second["identity"]["contract_id"] = "SCALE-2"
    second["transformation"]["decision_rule"]["evaluation_id"] = "EVAL-2"
    registries["evaluation_results"]["EVAL-2"] = {**registries["evaluation_results"]["EVAL-1"], "evaluation_id": "EVAL-2", "contract_id": "SCALE-2"}
    result = transformations.validate_scale_chain([first, second], **registries)
    assert result["unresolved_contract_ids"] == ["SCALE-1"]
    assert result["steps"][1]["result_state"] == "supported"
    second["identity"]["contract_id"] = "SCALE-1"
    with pytest.raises(transformations.TransformationError, match="unique"):
        transformations.validate_scale_chain([first, second], **registries)


def test_scale_operator_uses_actual_source_qualified_identity():
    record, registries = scale_fixture()
    record["transformation"]["operator_ids"] = ["scale_operator:M02"]
    assert transformations.validate_scale_instance(record, **registries)["result_state"] == "supported"
    record["transformation"]["operator_ids"] = ["V90-CANON-M02"]
    with pytest.raises(transformations.TransformationError, match="qualified"):
        transformations.validate_scale_instance(record, **registries)


@pytest.mark.parametrize("mutation", ["scale_missing_vocabulary", "scalar_variables", "wrong_task_quantity", "missing_bridge", "empty_identity_K"])
def test_present_fields_cannot_replace_their_semantic_responsibility(mutation):
    record, registries = scale_fixture()
    if mutation == "scale_missing_vocabulary": record["loss"]["compressed_details"] = {"status": "not_collected", "reason": "Wrong vocabulary for scale contract"}
    if mutation == "scalar_variables": record["variables"]["inputs"] = "everything preserved"
    if mutation == "wrong_task_quantity": record["semantics"]["task_preservation"]["target_quantity"] = "a different quantity"
    if mutation == "missing_bridge": record["transformation"]["rules"] = missing("No boundary/member/exit/interface mapping")
    if mutation == "empty_identity_K": record["objects"]["source_K"] = {}; record["objects"]["target_K"] = {}
    with pytest.raises(transformations.TransformationError):
        transformations.validate_scale_instance(record, **registries)
