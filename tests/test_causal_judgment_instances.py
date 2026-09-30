from copy import deepcopy
from importlib import import_module
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def root_contract():
    return {
        "instance_id": "synthetic-G2-instance", "root_id": "G2", "contract_version": "synthetic-contract-v1",
        "preregistration_timestamp": "2026-01-01T00:00:00Z", "candidate_object_id": "synthetic-object", "object_contract_id": "object-contract-v1",
        "scale_profile": {"scope": "registered-team"}, "time_window": "January", "identity_criterion": {"members": ["A", "B"]},
        "target_variables": ["task-delay"], "selected_subtype": "G2a", "selected_success_criterion": "controlled_perturbation_effect",
        "candidate_specification": {"channel": "synthetic-handoff", "transition": "task-delay-change", "quantity_type": "duration", "unit": "hours", "measured_dimensions": ["delay"]}, "zero_model": "no-delay-change", "controls": ["matched-load"], "model_classes": ["registered-model"],
        "sampling_unit": "synthetic-task", "generalization_unit": "registered-team", "evaluation_metric": "controlled_perturbation_effect", "decision_threshold": 0.1,
        "decision_rule": {"relation": "greater_than", "comparison_count": 1},
        "null_decision_rule": {"equivalence": {"metric": "equivalence-upper", "relation": "at_most", "threshold": 0.1}, "sensitivity": {"metric": "detectable-effect", "relation": "at_most", "threshold": 0.1}, "tolerance": {"metric": "error", "relation": "at_most", "threshold": 0.01}},
        "evidence_mode": "confirmatory", "falsifier": "no registered effect", "pause_condition": "scope changes", "deviation_record": [], "preregistration_status": "frozen_before_evidence",
    }


def root_result():
    return {"result_timestamp": "2026-02-02T00:00:00Z", "first_result_access_timestamp": "2026-02-01T00:00:00Z", "contract_version": "synthetic-contract-v1", "completion_status": "completed_from_frozen",
        "metrics": {"controlled_perturbation_effect": 0.2, "equivalence-upper": 0.2, "detectable-effect": 0.05, "error": 0.001},
        "evidence_claim_ids": ["experiment"], "analysis_artifact_claim_ids": ["analysis"], "null_gate_claim_ids": {gate: ["null-analysis"] for gate in ("equivalence", "sensitivity", "tolerance")}, "deviation_record": [],
        "prerequisite_claim_ids": {key: ["experiment"] for key in ("identification", "alternative_channels", "common_inputs", "measurement_protocol")}, "dimension_claim_ids": {"delay": ["experiment"]}}


def test_root_qualification_keeps_four_results_and_three_null_gates():
    instances = import_module("xi_kari_runtime.empirical_instances")
    frozen = instances.freeze_empirical_instance(root_contract())
    assert frozen["result"]["result_state"] == "not_evaluated"
    support = {ref: {"blocked": False} for ref in ("experiment", "analysis", "null-analysis")}
    result = root_result()
    checked = instances.evaluate_empirical_instance(frozen, result, claim_constraints=support)
    assert checked["qualification"] == "qualified"
    assert checked["result"]["result_state"] == "supported"
    result["metrics"].update(controlled_perturbation_effect=0.01, **{"equivalence-upper": 0.02})
    assert instances.evaluate_empirical_instance(frozen, result, claim_constraints=support)["result"]["result_state"] == "null_supported"
    result["metrics"]["detectable-effect"] = 0.3
    assert instances.evaluate_empirical_instance(frozen, result, claim_constraints=support)["result"]["result_state"] == "unsupported_or_undecided"


def test_g2_support_cannot_come_from_effect_number_without_identification_checks():
    instances = import_module("xi_kari_runtime.empirical_instances")
    frozen = instances.freeze_empirical_instance(root_contract())
    result = root_result()
    result["prerequisite_claim_ids"] = {}
    checked = instances.evaluate_empirical_instance(frozen, result, claim_constraints={ref: {"blocked": False} for ref in ("experiment", "analysis", "null-analysis")})
    assert checked["result"]["result_state"] == "unsupported_or_undecided"
    assert checked["qualification"] == "unqualified"


@pytest.mark.parametrize("change", ["exploratory", "postdated", "deviated", "classification-H2", "multiple-criteria", "multiple-targets", "multiple-models"])
def test_empirical_gate_rejects_posthoc_or_ineligible_instance(change):
    instances = import_module("xi_kari_runtime.empirical_instances")
    from xi_kari_runtime.causality import CausalError
    contract = root_contract()
    if change == "exploratory": contract["evidence_mode"] = "exploratory"
    elif change == "postdated": contract["preregistration_timestamp"] = "2026-02-03T00:00:00Z"
    elif change == "deviated": contract["deviation_record"] = ["criterion-changed-after-outcomes"]
    elif change == "classification-H2":
        contract.pop("root_id")
        contract["claim_id"] = "H2"
    elif change == "multiple-criteria": contract["selected_success_criterion"] = ["controlled_perturbation_effect", "controlled_intervention_effect"]
    elif change == "multiple-targets": contract["target_variables"].append("other-target")
    else: contract["model_classes"].append("other-model")
    if change in {"classification-H2", "multiple-criteria", "multiple-targets", "multiple-models"}:
        with pytest.raises(CausalError): instances.freeze_empirical_instance(contract)
    else:
        checked = instances.evaluate_empirical_instance(instances.freeze_empirical_instance(contract), root_result(), claim_constraints={ref: {"blocked": False} for ref in ("experiment", "analysis", "null-analysis")})
        assert checked["qualification"] == "unqualified"
        assert checked["result"]["result_state"] == "unsupported_or_undecided"


@pytest.mark.parametrize("family,subtype,criterion,candidate,checks", [
    ("G1", "G1a", "out_of_sample_predictive_gain", {"grouping": "synthetic-preselected-group"}, ["complexity_matched_zero", "group_leakage_control", "out_of_sample", "boundary_perturbation", "independent_time_or_location"]),
    ("G4", "G4a", "conditional_information_gain", {"mapping_id": "synthetic-map", "source_scale": "fine", "target_scale": "coarse", "retained_variables": ["retained"]}, ["D3_E5_mapping", "comparison_model", "retained_variable_conditioning"]),
    ("H1", "H1-coordination-outcome", "meaning_arrangement_coordination_outcome_effect", {"meaning_arrangement": "synthetic-public-anchor"}, ["selected_meaning_arrangement", "identification", "measurement_protocol"]),
    ("H4", "H4-expression-safety", "position_or_mediation_expression_safety_effect", {"position": "synthetic-low-power-position"}, ["selected_position_or_mediation", "identification", "measurement_protocol"]),
    ("H5", "habit_or_practice", "repeat_detection_across_preregistered_windows", {"carrier": "synthetic-practice"}, ["selected_carrier", "registered_observation_windows", "measurement_protocol"]),
])
def test_each_empirical_family_uses_only_its_preselected_criterion_and_checks(family, subtype, criterion, candidate, checks):
    instances = import_module("xi_kari_runtime.empirical_instances")
    contract, evaluation = root_contract(), root_result()
    if family.startswith("H"):
        contract.pop("root_id")
        contract["claim_id"] = family
    else: contract["root_id"] = family
    contract.update(selected_subtype=subtype, selected_success_criterion=criterion, evaluation_metric=criterion, candidate_specification=candidate)
    if family == "H5": contract.update(selected_carrier_family_id=subtype, selected_carrier="synthetic-practice")
    evaluation["metrics"][criterion] = 0.2
    evaluation["prerequisite_claim_ids"] = {key: ["experiment"] for key in checks}
    checked = instances.evaluate_empirical_instance(instances.freeze_empirical_instance(contract), evaluation, claim_constraints={ref: {"blocked": False} for ref in ("experiment", "analysis", "null-analysis")})
    assert checked["result"]["result_state"] == "supported"
    assert checked["preregistration"]["selected_success_criterion"] == criterion
    for check in checks:
        missing = deepcopy(evaluation)
        missing["prerequisite_claim_ids"].pop(check)
        assert instances.evaluate_empirical_instance(instances.freeze_empirical_instance(contract), missing, claim_constraints={ref: {"blocked": False} for ref in ("experiment", "analysis", "null-analysis")})["qualification"] == "unqualified"
    if family == "H5":
        contract["selected_carrier"] = ["one", "another"]
        from xi_kari_runtime.causality import CausalError
        with pytest.raises(CausalError, match="atomic"):
            instances.freeze_empirical_instance(contract)


def test_g3b_null_requires_both_history_increment_and_the_preselected_intervention_to_be_null():
    instances = import_module("xi_kari_runtime.empirical_instances")
    contract, result = root_contract(), root_result()
    contract.update(root_id="G3", selected_subtype="G3b", selected_success_criterion="history_erasure_effect", evaluation_metric="history_erasure_effect", candidate_specification={"current_state": {"skill": "registered"}, "known_current_state_fields": ["skill"], "environment": "fixed", "measurement_protocol": "score-v1", "history_variable": "training", "split_id": "held-out", "conditional_gain_threshold": 0.1, "conditional_gain_null_threshold": 0.01})
    result["metrics"].update(history_erasure_effect=0.001, **{"equivalence-upper": 0.002})
    result["historical_conditional_predictive_gain"] = 0.2
    result["prerequisite_claim_ids"] = {key: ["experiment"] for key in ("current_state_conditioning", "environment_conditioning", "measurement_protocol", "out_of_sample")}
    support = {ref: {"blocked": False} for ref in ("experiment", "analysis", "null-analysis")}
    frozen = instances.freeze_empirical_instance(contract)
    assert instances.evaluate_empirical_instance(frozen, result, claim_constraints=support)["result"]["result_state"] == "unsupported_or_undecided"
    result["historical_conditional_predictive_gain"] = 0.001
    assert instances.evaluate_empirical_instance(frozen, result, claim_constraints=support)["result"]["result_state"] == "null_supported"
