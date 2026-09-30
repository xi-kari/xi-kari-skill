"""Immutable G/H empirical contracts and separately computed result gates."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import json
from typing import Any
from pathlib import Path

from .canonical_json import sha256_json
from .causality import CausalError, _number, claim_support
from .problem_contract import parse_instant


CRITERIA = {
    "G1a": {"out_of_sample_predictive_gain"}, "G1b": {"out_of_sample_intervention_gain"},
    "G2a": {"controlled_perturbation_effect", "controlled_intervention_effect"},
    "G2b": {"identified_natural_variation_channel_effect"},
    "G3a": {"historical_conditional_predictive_gain"},
    "G3b": {"history_erasure_effect", "history_restoration_effect", "equivalent_intervention_effect"},
    "G4a": {"conditional_information_gain", "conditional_predictive_gain", "conditional_intervention_gain"},
    "G4b": {"object_dynamics_non_commutation", "intervention_non_commutation", "identity_criterion_violation", "effective_relation_change", "intervention_response_change"},
    "H1-resource-allocation": {"meaning_arrangement_resource_allocation_effect"},
    "H1-action-choice": {"meaning_arrangement_action_choice_effect"},
    "H1-coordination-outcome": {"meaning_arrangement_coordination_outcome_effect"},
    "H4-evidence-coverage": {"position_or_mediation_evidence_coverage_effect"},
    "H4-expression-safety": {"position_or_mediation_expression_safety_effect"},
    "H4-behavioral-response": {"mediation_or_publicity_behavioral_response_effect"},
    "H4-reflexive-response": {"observation_or_publication_reflexive_response_effect"},
}
H5_FAMILIES = {"institutional_or_textual_record", "role_or_organizational_arrangement", "habit_or_practice", "trauma_record", "collective_memory_carrier"}
H5_CRITERIA = {"threshold_persistence_over_preregistered_window", "repeat_detection_across_preregistered_windows", "persistence_after_event_or_exposure_end"}
NULL_GATES = {"equivalence", "sensitivity", "tolerance"}
PREREQUISITES = {
    "G1": {"complexity_matched_zero", "group_leakage_control", "out_of_sample", "boundary_perturbation", "independent_time_or_location"},
    "G2": {"identification", "alternative_channels", "common_inputs", "measurement_protocol"},
    "G3": {"current_state_conditioning", "environment_conditioning", "measurement_protocol", "out_of_sample"},
    "G4": {"D3_E5_mapping", "comparison_model", "retained_variable_conditioning"},
    "H1": {"selected_meaning_arrangement", "identification", "measurement_protocol"},
    "H4": {"selected_position_or_mediation", "identification", "measurement_protocol"},
    "H5": {"selected_carrier", "registered_observation_windows", "measurement_protocol"},
}


def freeze_empirical_instance(record: Mapping[str, Any]) -> dict[str, Any]:
    required = {"instance_id", "contract_version", "preregistration_timestamp", "candidate_object_id", "object_contract_id", "scale_profile", "time_window", "identity_criterion", "target_variables", "selected_subtype", "selected_success_criterion", "candidate_specification", "zero_model", "controls", "model_classes", "sampling_unit", "generalization_unit", "evaluation_metric", "decision_threshold", "decision_rule", "null_decision_rule", "evidence_mode", "falsifier", "pause_condition", "deviation_record", "preregistration_status"}
    if required - set(record) or any(not record[field] for field in required - {"decision_threshold", "deviation_record"}):
        raise CausalError("empirical instance lacks its required preregistration responsibility")
    if ("root_id" in record) == ("claim_id" in record):
        raise CausalError("empirical instance must select either a G root or an H claim")
    family = record.get("root_id", record.get("claim_id"))
    if family not in {"G1", "G2", "G3", "G4", "H1", "H4", "H5"}:
        raise CausalError("classification and normative H rules are not empirical instances")
    subtype, criterion = record["selected_subtype"], record["selected_success_criterion"]
    allowed = H5_CRITERIA if family == "H5" and subtype in H5_FAMILIES else CRITERIA.get(subtype, set())
    if not isinstance(criterion, str) or criterion not in allowed or (family != "H5" and not str(subtype).startswith(family)):
        raise CausalError("empirical instance must preselect one permitted subtype and criterion")
    if family == "H5" and (record.get("selected_carrier_family_id") != subtype or not isinstance(record.get("selected_carrier"), str) or not record["selected_carrier"].strip()):
        raise CausalError("H5 requires one atomic carrier of its preselected family")
    candidate = record["candidate_specification"]
    if not isinstance(candidate, Mapping):
        raise CausalError("empirical candidate specification must be typed")
    fields = {"G2": {"channel", "transition", "quantity_type", "unit", "measured_dimensions"}, "G3": {"current_state", "known_current_state_fields", "environment", "measurement_protocol", "history_variable", "split_id"}, "G4": {"mapping_id", "source_scale", "target_scale", "retained_variables"}}.get(family, set())
    if any(not candidate.get(field) for field in fields):
        raise CausalError("empirical candidate lacks a family-specific preregistration condition")
    if family == "G3":
        _number(candidate.get("conditional_gain_threshold"))
        _number(candidate.get("conditional_gain_null_threshold"))
    if record["evaluation_metric"] != criterion:
        raise CausalError("empirical evaluation metric differs from the selected success criterion")
    parse_instant(record["preregistration_timestamp"], field="empirical registration")
    _number(record["decision_threshold"])
    rule = record["decision_rule"]
    if rule.get("relation") not in {"greater_than", "less_than"} or isinstance(rule.get("comparison_count"), bool) or not isinstance(rule.get("comparison_count"), int) or rule["comparison_count"] < 1:
        raise CausalError("empirical positive rule is incomplete")
    if len(record["target_variables"]) > 1 and not rule.get("primary_target_or_aggregation"):
        raise CausalError("multiple targets require a frozen primary target or aggregation")
    if len(record["model_classes"]) > 1 and not rule.get("model_selection_or_ensemble"):
        raise CausalError("multiple models require a frozen selection or ensemble rule")
    if rule["comparison_count"] > 1 and not rule.get("multiple_comparison_correction"):
        raise CausalError("multiple comparisons require a frozen correction rule")
    null = record["null_decision_rule"]
    if not isinstance(null, Mapping) or set(null) != NULL_GATES:
        raise CausalError("empirical zero conclusion requires all three frozen gates")
    for gate in null.values():
        if not gate.get("metric") or gate.get("relation") not in {"at_most", "at_least"}:
            raise CausalError("empirical null gate is not decidable")
        _number(gate.get("threshold"))
    if record["evidence_mode"] not in {"confirmatory", "replication", "falsification", "exploratory"} or not isinstance(record["deviation_record"], list):
        raise CausalError("empirical study mode or deviation history is invalid")
    contract = deepcopy(dict(record))
    missing = {"status": "not_evaluated", "reason": "instance has not run"}
    return {"preregistration": contract, "preregistration_sha256": sha256_json(contract), "qualification": "not_evaluated", "result": {"result_state": "not_evaluated", **{field: deepcopy(missing) for field in ("result_timestamp", "observed_primary_result", "decision_rule_outcome", "null_decision_rule_outcome", "evidence_refs", "analysis_artifact_refs")}}}


def evaluate_empirical_instance(
    frozen: Mapping[str, Any], evaluation: Mapping[str, Any], *, claim_constraints: Mapping[str, Any]
) -> dict[str, Any]:
    contract = frozen["preregistration"]
    if frozen.get("preregistration_sha256") != sha256_json(contract):
        raise CausalError("empirical preregistration changed")
    freeze_empirical_instance(contract)
    snapshot = deepcopy(dict(frozen))
    registered = parse_instant(contract["preregistration_timestamp"], field="empirical registration")
    accessed = parse_instant(evaluation["first_result_access_timestamp"], field="empirical result access")
    completed = parse_instant(evaluation["result_timestamp"], field="empirical completion")
    eligible = registered < accessed <= completed and contract["preregistration_status"] == "frozen_before_evidence" and evaluation.get("completion_status") == "completed_from_frozen" and evaluation.get("contract_version") == contract["contract_version"] and not contract["deviation_record"] and not evaluation.get("deviation_record") and contract["evidence_mode"] != "exploratory"
    evidence = claim_support(evaluation.get("evidence_claim_ids", []), claim_constraints) == "supported"
    artifacts = claim_support(evaluation.get("analysis_artifact_claim_ids", []), claim_constraints) == "supported"
    eligible = eligible and evidence and artifacts
    family = contract.get("root_id", contract.get("claim_id"))
    prerequisite_claims = evaluation.get("prerequisite_claim_ids", {})
    eligible = eligible and all(claim_support(prerequisite_claims.get(key, []), claim_constraints) == "supported" for key in PREREQUISITES[family])
    candidate = contract["candidate_specification"]
    if family == "G3":
        eligible = eligible and all(key in candidate["current_state"] for key in candidate["known_current_state_fields"])
        gain = evaluation.get("historical_conditional_predictive_gain")
        gain_threshold = _number(candidate.get("conditional_gain_threshold"))
        eligible = eligible and gain is not None
    else:
        gain, gain_threshold = None, None
    metrics = evaluation.get("metrics", {})
    selected = contract["selected_success_criterion"]
    value = _number(metrics[selected]) if selected in metrics else None
    threshold = contract["decision_threshold"]
    positive = eligible and contract["evidence_mode"] in {"confirmatory", "replication"} and value is not None and (value > threshold if contract["decision_rule"]["relation"] == "greater_than" else value < threshold)
    if family == "G3":
        positive = positive and _number(gain) > gain_threshold
    null_results = {}
    for name, gate in contract["null_decision_rule"].items():
        measurement = _number(metrics[gate["metric"]]) if gate["metric"] in metrics else None
        supported = claim_support(evaluation.get("null_gate_claim_ids", {}).get(name, []), claim_constraints) == "supported"
        passed = eligible and supported and measurement is not None and (measurement <= gate["threshold"] if gate["relation"] == "at_most" else measurement >= gate["threshold"])
        null_results[name] = {"value": measurement, "threshold": gate["threshold"], "passed": passed}
    null_passed = eligible and all(row["passed"] for row in null_results.values())
    if family == "G3":
        null_passed = null_passed and _number(gain) <= candidate["conditional_gain_null_threshold"]
    result_state = "supported" if positive else "null_supported" if null_passed else "unsupported_or_undecided"
    snapshot["qualification"] = "qualified" if eligible else "unqualified"
    snapshot["result"] = {"result_timestamp": evaluation["result_timestamp"], "observed_primary_result": value, "decision_rule_outcome": {"value": value, "threshold": threshold, "passed": positive}, "null_decision_rule_outcome": null_results, "result_state": result_state, "evidence_refs": list(evaluation.get("evidence_claim_ids", [])), "analysis_artifact_refs": list(evaluation.get("analysis_artifact_claim_ids", [])), "deviation_record": deepcopy(evaluation.get("deviation_record", []))}
    snapshot["evaluation_sha256"] = sha256_json(evaluation)
    if family == "G2":
        snapshot["measured_dimensions"] = {name: claim_support(evaluation.get("dimension_claim_ids", {}).get(name, []), claim_constraints) for name in candidate["measured_dimensions"]}
    return snapshot


class EvaluatedInstanceRegistry(Mapping[str, Mapping[str, Any]]):
    """A per-input registry rebuilt by actual validation, never from result labels."""
    def __init__(self, inputs: list[Mapping[str, Any]], *, graph: Mapping[str, Any], derived_instances: list[Mapping[str, Any]] | None = None, evidence_mode: str = 'open-world', repository_root: Path | None = None):
        from .claims import claim_constraints, validate_empirical_instances
        from .causality import assess_derived_causal_instance
        from .v4_contracts import claim_graph_input
        graph = claim_graph_input(graph)
        checked = validate_empirical_instances(inputs, claim_mechanism_graph=graph, evidence_mode=evidence_mode, repository_root=repository_root)
        results = {}
        for instance in checked["instances"]:
            prereg = instance["preregistration"]
            identifier = prereg["instance_id"]
            results[identifier] = {**instance, "instance_id": identifier, "instance_family": prereg.get("root_id", prereg.get("claim_id")), "formal_result": instance["result"]["result_state"]}
        constraints = claim_constraints(graph)
        for record in derived_instances or []:
            result = assess_derived_causal_instance(record, formal_results=results, claim_constraints=constraints)
            if result["instance_id"] in results:
                raise CausalError("evaluated instance identity is duplicated")
            results[result["instance_id"]] = result
        self._results_json = json.dumps(results, ensure_ascii=False, sort_keys=True)
        self.graph_sha256 = checked["claim_graph_sha256"]
        self.inputs_sha256 = sha256_json({"empirical": inputs, "derived": derived_instances or []})
        self._inputs_json = json.dumps({**{item['frozen']['preregistration']['instance_id']: item for item in inputs}, **{item['instance_id']: item for item in derived_instances or []}}, ensure_ascii=False, sort_keys=True, allow_nan=False)

    def matches_graph(self, graph: Mapping[str, Any]) -> bool:
        from .v4_contracts import claim_graph_input
        return self.graph_sha256 == sha256_json(claim_graph_input(graph))

    def instance_input(self, identifier: str) -> Mapping[str, Any]:
        return json.loads(self._inputs_json)[identifier]

    def __getitem__(self, identifier: str) -> Mapping[str, Any]:
        return json.loads(self._results_json)[identifier]

    def __iter__(self):
        return iter(json.loads(self._results_json))

    def __len__(self):
        return len(json.loads(self._results_json))


__all__ = ("freeze_empirical_instance", "evaluate_empirical_instance", "EvaluatedInstanceRegistry")
