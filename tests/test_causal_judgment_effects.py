from importlib import import_module
from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from tests.temporal_materials import assess_history_with_materials


def test_identified_total_effect_preserves_unknown_mechanism_and_transport():
    causal = import_module("xi_kari_runtime.causality")
    record = {
        "treatment_version": "synthetic-assigned-offer-v1",
        "estimand": "intention_to_treat", "population": "synthetic-study-enrollees",
        "outcome": "synthetic-task-score", "window": "registered-six-weeks",
        "scale": "individual", "identification_assumptions": ["random_assignment"],
        "identification_claim_ids": ["claim-randomized-comparison"],
        "mechanism_claim_ids": [], "transport_claim_ids": [],
        "measured_dimensions": {},
    }
    support = {"claim-randomized-comparison": {"blocked": False, "limiting": False}}
    result = causal.assess_effect(record, claim_constraints=support)
    assert result["total_effect"] == "supported"
    assert result["mechanism"] == "unsupported_or_undecided"
    assert result["transport"] == "unsupported_or_undecided"
    assert result["measured_dimensions"] == {}


def effect_record():
    return {
        "treatment_version": "synthetic-offer-v1", "estimand": "intention_to_treat",
        "population": "synthetic-enrollees", "outcome": "score", "window": "six-weeks",
        "scale": "individual", "identification_assumptions": ["random_assignment"],
        "identification_claim_ids": ["random-assignment"], "mechanism_claim_ids": ["mediator"],
        "transport_claim_ids": ["new-population"],
        "measured_dimensions": {"delay": {"channel_id": "handoff", "quantity_type": "duration", "unit": "seconds", "window": "six-weeks", "claim_ids": ["delay"]}},
    }


def test_failed_mediator_or_transport_does_not_retract_assignment_effect():
    causal = import_module("xi_kari_runtime.causality")
    support = {ref: {"blocked": ref in {"mediator", "new-population"}, "limiting": False} for ref in ("random-assignment", "mediator", "new-population", "delay")}
    record = effect_record()
    before = deepcopy(record)
    result = causal.assess_effect(record, claim_constraints=support)
    assert (result["total_effect"], result["mechanism"], result["transport"]) == ("supported", "unsupported_or_undecided", "unsupported_or_undecided")
    assert set(result["measured_dimensions"]) == {"delay"}
    assert record == before


def test_causal_record_cannot_invent_support_or_unmeasured_dimensions():
    causal = import_module("xi_kari_runtime.causality")
    with pytest.raises(causal.CausalError, match="unresolved"):
        causal.assess_effect(effect_record(), claim_constraints={})


def history_contract():
    return {
        "instance_id": "synthetic-history-1", "subtype": "G3a",
        "criterion": "historical_conditional_predictive_gain",
        "registered_at": "2026-01-01T00:00:00Z", "input_cutoff": "2025-12-31T00:00:00Z",
        "current_state": {"skill": "measured"}, "known_current_state_fields": ["skill"],
        "environment": "synthetic-stable", "measurement_protocol": "task-score-v1",
        "history_variable": "prior-training", "target": "held-out-task", "window": "2026-January",
        "split_id": "held-out-1", "model_version": "synthetic-model-v1",
        "study_mode": "confirmatory", "preregistration_status": "frozen_before_evidence",
        "deviation_record": [], "zero_model": "current-state-is-sufficient",
        "gain_threshold": 0.01, "criterion_threshold": 0.01, "null_rule": None,
    }


def history_result():
    return {
        "outcome_first_seen_at": "2026-02-01T00:00:00Z", "target": "held-out-task",
        "window": "2026-January", "split_id": "held-out-1", "model_version": "synthetic-model-v1",
        "predictive_gain": 0.0, "criterion_values": {}, "out_of_sample_claim_ids": ["conditional-test"],
        "criterion_claim_ids": [], "null_claim_ids": [],
        "analysis_artifact_claim_ids": ["conditional-test"], "null_metrics": {},
    }


def test_history_carried_by_current_skill_retains_learning_without_g3(tmp_path):
    causal = import_module("xi_kari_runtime.causality")
    frozen = causal.freeze_history_contract(history_contract())
    support = {ref: {"blocked": False, "limiting": False} for ref in ("training-process", "conditional-test")}
    result = assess_history_with_materials(tmp_path, frozen, history_result(), claim_constraints=support, ordinary_history_claim_ids=["training-process"])
    assert result["ordinary_history"] == "supported"
    assert result["formal_result"] == "unsupported_or_undecided"
    assert result["qualification"] == "qualified"


@pytest.mark.parametrize("change", ["omit-state", "postdated", "exploratory"])
def test_history_qualification_failure_preserves_ordinary_history(change):
    causal = import_module("xi_kari_runtime.causality")
    contract = history_contract()
    if change == "omit-state":
        contract["current_state"] = {"other": "measured"}
    elif change == "postdated":
        contract["registered_at"] = "2026-02-02T00:00:00Z"
    else:
        contract["study_mode"] = "exploratory"
    result = history_result()
    result["predictive_gain"] = 0.5
    assessment = causal.assess_history(causal.freeze_history_contract(contract), result, claim_constraints={ref: {"blocked": False} for ref in ("training", "conditional-test")}, ordinary_history_claim_ids=["training"])
    assert assessment["ordinary_history"] == "supported"
    assert assessment["formal_result"] == "unsupported_or_undecided"
    assert assessment["qualification"] != "qualified"


def test_history_null_requires_three_independent_preregistered_gates(tmp_path):
    causal = import_module("xi_kari_runtime.causality")
    contract = history_contract()
    contract["null_rule"] = {
        "equivalence": {"metric": "upper-residual-bound", "relation": "at_most", "threshold": 0.01},
        "sensitivity": {"metric": "detectable-effect", "relation": "at_most", "threshold": 0.01},
        "tolerance": {"metric": "measurement-error", "relation": "at_most", "threshold": 0.005},
    }
    result = history_result()
    result["null_metrics"] = {"upper-residual-bound": 0.001, "detectable-effect": 0.005, "measurement-error": 0.002}
    result["null_claim_ids"] = ["null-analysis"]
    support = {ref: {"blocked": False} for ref in ("training", "conditional-test", "null-analysis")}
    frozen = causal.freeze_history_contract(contract)
    assessment = assess_history_with_materials(tmp_path, frozen, result, claim_constraints=support, ordinary_history_claim_ids=["training"])
    assert assessment["formal_result"] == "null_supported"
    result["null_metrics"]["detectable-effect"] = 0.1
    assessment = assess_history_with_materials(tmp_path, frozen, result, claim_constraints=support, ordinary_history_claim_ids=["training"])
    assert assessment["formal_result"] == "unsupported_or_undecided"


def test_positive_g3a_and_preselected_g3b_have_distinct_responsibilities(tmp_path):
    causal = import_module("xi_kari_runtime.causality")
    contract = history_contract()
    result = history_result()
    result["predictive_gain"] = 0.2
    support = {"conditional-test": {"blocked": False}, "erasure-study": {"blocked": False}}
    assert assess_history_with_materials(tmp_path, causal.freeze_history_contract(contract), result, claim_constraints=support, ordinary_history_claim_ids=[])["formal_result"] == "supported"
    contract.update(subtype="G3b", criterion="history_erasure_effect")
    result["criterion_values"] = {"history_erasure_effect": 0.001, "history_restoration_effect": 0.5}
    result["criterion_claim_ids"] = ["erasure-study"]
    frozen = causal.freeze_history_contract(contract)
    assert assess_history_with_materials(tmp_path, frozen, result, claim_constraints=support, ordinary_history_claim_ids=[])["formal_result"] == "unsupported_or_undecided"
    result["criterion_values"]["history_erasure_effect"] = 0.2
    assert assess_history_with_materials(tmp_path, frozen, result, claim_constraints=support, ordinary_history_claim_ids=[])["formal_result"] == "supported"
    frozen["contract"]["criterion"] = "history_restoration_effect"
    with pytest.raises(causal.CausalError, match="changed"):
        assess_history_with_materials(tmp_path, frozen, result, claim_constraints=support, ordinary_history_claim_ids=[])


@pytest.mark.parametrize("criterion", [["history_erasure_effect", "history_restoration_effect"], "historical_conditional_predictive_gain"])
def test_g3b_rejects_nonunique_or_wrong_subtype_criterion(criterion):
    causal = import_module("xi_kari_runtime.causality")
    contract = history_contract()
    contract.update(subtype="G3b", criterion=criterion)
    with pytest.raises(causal.CausalError, match="preselect"):
        causal.freeze_history_contract(contract)


def test_retained_skill_can_be_ordinary_learning_without_cm_learning():
    causal = import_module("xi_kari_runtime.causality")
    support = {ref: {"blocked": False} for ref in ("receipt", "return-update", "retention", "round-two", "round-three", "skill-process")}
    record = {
        "receipt_claim_ids": ["receipt"], "return_update_claim_ids": ["return-update"],
        "retention_claim_ids": ["retention"], "later_round_claim_ids": [["round-two"], ["round-three"]],
        "ordinary_learning_claim_ids": ["skill-process"], "institutional_writeback_claim_ids": [],
        "cm_feedback_instance": None, "g3_instance": None, "task_change_claim_ids": [],
        "task_version": "original-task", "comparison_task_version": "original-task",
    }
    result = causal.assess_feedback(record, claim_constraints=support)
    assert result["effective_feedback"] == "supported"
    assert result["ordinary_learning"] == "supported"
    assert result["cm_learning"] == "unsupported_or_undecided"


def test_one_receipt_or_writeback_does_not_prove_feedback_or_learning():
    causal = import_module("xi_kari_runtime.causality")
    record = {"receipt_claim_ids": ["receipt"], "institutional_writeback_claim_ids": ["archive"]}
    result = causal.assess_feedback(record, claim_constraints={"receipt": {"blocked": False}, "archive": {"blocked": False}})
    assert (result["receipt"], result["institutional_writeback"]) == ("supported", "supported")
    assert (result["effective_feedback"], result["ordinary_learning"], result["cm_learning"]) == ("unsupported_or_undecided",) * 3


def test_task_indicator_support_does_not_prove_durable_capacity_or_manipulation():
    causal = import_module("xi_kari_runtime.causality")
    record = {
        "construct": "synthetic-current-task-performance", "indicator": "score", "indicator_role": "direct_record",
        "unit": "points", "version": "v1", "selection_mechanism": "registered-enrollees",
        "recording_mechanism": "synthetic-task-test", "reporting_mechanism": "all-registered-results",
        "indicator_claim_ids": ["task-score"], "construct_claim_ids": ["task-score"],
        "durable_capacity_claim_ids": [], "manipulation_claim_ids": [],
        "cross_group_comparison": False, "cross_time_comparison": False, "comparability_claim_ids": [],
    }
    result = causal.assess_measurement(record, claim_constraints={"task-score": {"blocked": False}})
    assert (result["indicator"], result["construct"]) == ("supported", "supported")
    assert (result["durable_capacity"], result["manipulation"]) == ("unsupported_or_undecided",) * 2
    assert result["comparability"] == "not_applicable"
    record["cross_group_comparison"] = True
    result = causal.assess_measurement(record, claim_constraints={"task-score": {"blocked": False}})
    assert result["indicator"] == "supported"
    assert result["construct"] == "unsupported_or_undecided"


def test_synchronous_common_cause_is_not_a_proved_cascade_or_c7():
    causal = import_module("xi_kari_runtime.causality")
    record = {
        "hops": [{"from_id": "synthetic-A", "to_id": "synthetic-B", "channel": "supply", "window": "one-day", "temporal_claim_ids": [], "causal_claim_ids": []}],
        "common_cause_claim_ids": ["shared-power-loss"], "ordinary_externality_claim_ids": ["bounded-harm"],
        "formal_c7_instance_id": None,
    }
    result = causal.assess_propagation(record, claim_constraints={ref: {"blocked": False} for ref in ("shared-power-loss", "bounded-harm")})
    assert (result["common_cause"], result["ordinary_externality"]) == ("supported", "supported")
    assert (result["cascade"], result["formal_c7"]) == ("unsupported_or_undecided",) * 2


def test_supported_temporary_recovery_keeps_support_dependency_and_limits():
    causal = import_module("xi_kari_runtime.causality")
    record = {
        "function": "synthetic-clinic-hours", "population": "registered-users", "window": "grant-period",
        "support_conditions": ["temporary-building", "external-grant"],
        "function_claim_ids": ["service-restored"], "sustainability_claim_ids": [],
        "internal_margin_claim_ids": [], "external_burden_claim_ids": ["extra-travel"],
        "reliability_test_claim_ids": [], "unexperienced_conditions": ["seasonal-demand-peak"],
        "backup_count": 2, "common_cause_exposures": ["shared-electricity"],
    }
    result = causal.assess_recovery(record, claim_constraints={ref: {"blocked": False} for ref in ("service-restored", "extra-travel")})
    assert result["function_recovery"] == "supported"
    assert result["sustainability"] == result["reliability"] == "unsupported_or_undecided"
    assert result["support_conditions"] == ["temporary-building", "external-grant"]
    assert result["unexperienced_conditions"] == ["seasonal-demand-peak"]


def test_formal_feedback_and_learning_need_their_own_roots_and_method_gates():
    causal = import_module("xi_kari_runtime.causality")
    support = {ref: {"blocked": False} for ref in ("return", "update", "E4", "CAUSAL", "EVIDENCE", "retain", "round-2", "round-3", "task")}
    roots = {"g2": {"qualification": "qualified", "formal_result": "supported", "instance_family": "G2"}, "g3": {"qualification": "qualified", "formal_result": "supported", "instance_family": "G3"}}
    feedback = {"instance_id": "feedback-1", "instance_family": "CM-FEEDBACK", "g2_instance_id": "g2", "channel_contract": {"channel": "handoff", "quantity_type": "tasks", "unit": "tasks", "window": "synthetic-window"}, "return_claim_ids": ["return"], "state_update_claim_ids": ["update"], "method_claim_ids": {method: [method] for method in ("E4", "CAUSAL", "EVIDENCE")}}
    checked = causal.assess_derived_causal_instance(feedback, formal_results=roots, claim_constraints=support)
    assert checked["formal_result"] == "supported"
    roots["feedback-1"] = checked
    learning = {"instance_id": "learning-1", "instance_family": "CM-LEARNING", "cm_feedback_instance_id": "feedback-1", "g3_instance_id": "g3", "retention_claim_ids": ["retain"], "later_round_claim_ids": [["round-2"], ["round-3"]], "task_change_claim_ids": ["task"], "task_version": "original-task", "comparison_task_version": "original-task", "method_claim_ids": feedback["method_claim_ids"]}
    assert causal.assess_derived_causal_instance(learning, formal_results=roots, claim_constraints=support)["formal_result"] == "supported"
    learning["task_version"] = "new-easier-task"
    assert causal.assess_derived_causal_instance(learning, formal_results=roots, claim_constraints=support)["formal_result"] == "unsupported_or_undecided"
