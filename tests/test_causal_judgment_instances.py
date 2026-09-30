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
