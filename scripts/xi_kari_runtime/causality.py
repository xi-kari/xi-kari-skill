"""Scoped causal conclusions evaluated against resolved claim constraints."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import math
from typing import Any

from .canonical_json import sha256_json
from .problem_contract import parse_instant


class CausalError(ValueError):
    """A causal record crosses its evidence or scope boundary."""


def _required(record: Mapping[str, Any], fields: Sequence[str]) -> None:
    if any(not record.get(field) for field in fields):
        raise CausalError("causal record lacks a required scope or design field")


def claim_support(refs: object, constraints: Mapping[str, Any]) -> str:
    """Read constraints produced by validation; never create empirical support."""
    if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
        raise CausalError("causal support must reference claim IDs")
    if len(refs) != len(set(refs)) or any(ref not in constraints for ref in refs):
        raise CausalError("causal support contains duplicate or unresolved claims")
    if not refs or any(constraints[ref]["blocked"] for ref in refs):
        return "unsupported_or_undecided"
    return "supported"


def _number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise CausalError("causal metric requires a finite number")
    return float(value)


def assess_effect(
    record: Mapping[str, Any], *, claim_constraints: Mapping[str, Any]
) -> dict[str, Any]:
    _required(record, (
        "treatment_version", "estimand", "population", "outcome", "window",
        "scale", "identification_assumptions",
    ))
    result = deepcopy(dict(record))
    result["total_effect"] = claim_support(
        record.get("identification_claim_ids", []), claim_constraints
    )
    result["mechanism"] = claim_support(
        record.get("mechanism_claim_ids", []), claim_constraints
    )
    result["transport"] = claim_support(
        record.get("transport_claim_ids", []), claim_constraints
    )
    dimensions = record.get("measured_dimensions", {})
    if not isinstance(dimensions, Mapping):
        raise CausalError("measured channel dimensions must be a mapping")
    result["measured_dimensions"] = {}
    for name, measurement in dimensions.items():
        if name not in {"capacity", "delay", "reliability", "controllability", "loss"}:
            raise CausalError("unknown channel measurement dimension")
        _required(measurement, ("channel_id", "quantity_type", "unit", "window"))
        result["measured_dimensions"][name] = {
            **deepcopy(measurement),
            "status": claim_support(measurement.get("claim_ids", []), claim_constraints),
        }
    return result


HISTORY_CRITERIA = {
    "G3a": {"historical_conditional_predictive_gain"},
    "G3b": {"history_erasure_effect", "history_restoration_effect", "equivalent_intervention_effect"},
}


def freeze_history_contract(record: Mapping[str, Any]) -> dict[str, Any]:
    _required(record, (
        "instance_id", "subtype", "criterion", "registered_at", "input_cutoff",
        "current_state", "known_current_state_fields", "environment",
        "measurement_protocol", "history_variable", "target", "window",
        "split_id", "model_version", "study_mode", "preregistration_status", "zero_model",
    ))
    if record["subtype"] not in HISTORY_CRITERIA or not isinstance(record["criterion"], str) or record["criterion"] not in HISTORY_CRITERIA[record["subtype"]]:
        raise CausalError("history subtype must preselect exactly one allowed criterion")
    if parse_instant(record["input_cutoff"], field="history input cutoff") > parse_instant(record["registered_at"], field="history registration"):
        raise CausalError("history input cutoff follows registration")
    _number(record.get("gain_threshold"))
    _number(record.get("criterion_threshold"))
    if record.get("study_mode") not in {"confirmatory", "replication", "falsification", "exploratory"} or not isinstance(record.get("deviation_record"), list):
        raise CausalError("history study mode or deviation record is invalid")
    null_rule = record.get("null_rule")
    if null_rule is not None:
        if not isinstance(null_rule, Mapping) or set(null_rule) != {"equivalence", "sensitivity", "tolerance"}:
            raise CausalError("null conclusion requires three frozen gates")
        for rule in null_rule.values():
            _required(rule, ("metric", "relation"))
            if rule["relation"] not in {"at_most", "at_least"}:
                raise CausalError("null gate has an unsupported relation")
            _number(rule.get("threshold"))
    snapshot = deepcopy(dict(record))
    return {"contract": snapshot, "contract_sha256": sha256_json(snapshot)}


def assess_history(
    frozen: Mapping[str, Any], result: Mapping[str, Any] | None, *,
    claim_constraints: Mapping[str, Any], ordinary_history_claim_ids: list[str],
) -> dict[str, Any]:
    contract = frozen["contract"]
    if frozen.get("contract_sha256") != sha256_json(contract):
        raise CausalError("frozen history contract changed")
    ordinary = claim_support(ordinary_history_claim_ids, claim_constraints)
    assessment = {"ordinary_history": ordinary, "qualification": "qualified", "formal_result": "not_evaluated", "contract_sha256": frozen["contract_sha256"]}
    known = contract["known_current_state_fields"]
    if not isinstance(known, list) or not isinstance(contract["current_state"], Mapping) or any(field not in contract["current_state"] for field in known):
        assessment.update(qualification="paused", formal_result="unsupported_or_undecided", reason="known_current_state_omitted")
        return assessment
    if result is None:
        return assessment
    if contract["study_mode"] == "exploratory" or contract["preregistration_status"] != "frozen_before_evidence" or contract["deviation_record"]:
        assessment.update(qualification="unqualified", formal_result="unsupported_or_undecided", reason="ineligible_study_or_deviation")
        return assessment
    if parse_instant(contract["registered_at"], field="history registration") >= parse_instant(result["outcome_first_seen_at"], field="history outcome"):
        assessment.update(qualification="paused", formal_result="unsupported_or_undecided", reason="registration_not_before_outcome")
        return assessment
    if any(result.get(field) != contract[field] for field in ("target", "window", "split_id", "model_version")):
        raise CausalError("history result differs from its frozen evaluation scope")
    gain = _number(result.get("predictive_gain"))
    gain_supported = claim_support(result.get("out_of_sample_claim_ids", []), claim_constraints) == "supported"
    artifacts = claim_support(result.get("analysis_artifact_claim_ids", []), claim_constraints) == "supported"
    positive = gain_supported and artifacts and contract["study_mode"] in {"confirmatory", "replication"} and gain > contract["gain_threshold"]
    if contract["subtype"] == "G3b":
        measured = result.get("criterion_values", {}).get(contract["criterion"])
        positive = positive and measured is not None and _number(measured) > contract["criterion_threshold"] and claim_support(result.get("criterion_claim_ids", []), claim_constraints) == "supported"
    assessment["formal_result"] = "supported" if positive else "unsupported_or_undecided"
    null_rule = contract.get("null_rule")
    if not positive and null_rule and artifacts and claim_support(result.get("null_claim_ids", []), claim_constraints) == "supported":
        metrics = result.get("null_metrics", {})
        null_passed = True
        for rule in null_rule.values():
            if rule["metric"] not in metrics:
                null_passed = False
                break
            value = _number(metrics[rule["metric"]])
            null_passed = null_passed and (value <= rule["threshold"] if rule["relation"] == "at_most" else value >= rule["threshold"])
        if null_passed:
            assessment["formal_result"] = "null_supported"
    return assessment


def assess_feedback(
    record: Mapping[str, Any], *, claim_constraints: Mapping[str, Any],
    formal_results: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    results = formal_results or {}
    def status(field: str) -> str:
        return claim_support(record.get(field, []), claim_constraints)
    def formal(identifier: object) -> bool:
        if identifier is None:
            return False
        if not isinstance(identifier, str) or identifier not in results:
            raise CausalError("feedback references an unresolved formal instance")
        instance = results[identifier]
        return instance.get("qualification") == "qualified" and instance.get("formal_result") == "supported"
    receipt = status("receipt_claim_ids")
    feedback = status("return_update_claim_ids")
    retention = status("retention_claim_ids")
    rounds = record.get("later_round_claim_ids", [])
    if not isinstance(rounds, list):
        raise CausalError("feedback later rounds must be a list")
    repeated = len(rounds) >= 2 and all(claim_support(refs, claim_constraints) == "supported" for refs in rounds)
    changed_goal = record.get("task_version") != record.get("comparison_task_version")
    cm_learning = (
        feedback == retention == "supported" and repeated and not changed_goal
        and formal(record.get("cm_feedback_instance_id"))
        and formal(record.get("g3_instance_id"))
        and status("task_change_claim_ids") == "supported"
    )
    return {
        "receipt": receipt, "effective_feedback": feedback, "retained_update": retention,
        "repeated_use": "supported" if repeated else "unsupported_or_undecided",
        "ordinary_learning": status("ordinary_learning_claim_ids"),
        "institutional_writeback": status("institutional_writeback_claim_ids"),
        "cm_learning": "supported" if cm_learning else "unsupported_or_undecided",
        "new_comparison_required": changed_goal,
    }


def assess_measurement(
    record: Mapping[str, Any], *, claim_constraints: Mapping[str, Any]
) -> dict[str, str]:
    _required(record, ("construct", "indicator", "indicator_role", "unit", "version", "selection_mechanism", "recording_mechanism", "reporting_mechanism"))
    if record["indicator_role"] not in {"direct_record", "reflective_indicator", "formative_component", "predictive_proxy"}:
        raise CausalError("measurement indicator role is not recognized")
    for field in ("cross_group_comparison", "cross_time_comparison"):
        if not isinstance(record.get(field), bool):
            raise CausalError("measurement comparison scope must be explicit")
    result = {
        key: claim_support(record.get(field, []), claim_constraints)
        for key, field in (("indicator", "indicator_claim_ids"), ("construct", "construct_claim_ids"), ("durable_capacity", "durable_capacity_claim_ids"), ("manipulation", "manipulation_claim_ids"))
    }
    comparison = record["cross_group_comparison"] or record["cross_time_comparison"]
    result["comparability"] = claim_support(record.get("comparability_claim_ids", []), claim_constraints) if comparison else "not_applicable"
    if comparison and result["comparability"] != "supported":
        result["construct"] = "unsupported_or_undecided"
    return result


def assess_propagation(
    record: Mapping[str, Any], *, claim_constraints: Mapping[str, Any],
    formal_results: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    hops = record.get("hops", [])
    if not isinstance(hops, list):
        raise CausalError("propagation hops must be a list")
    statuses = []
    for index, hop in enumerate(hops):
        _required(hop, ("from_id", "to_id", "channel", "window"))
        if index and hops[index - 1]["to_id"] != hop["from_id"]:
            raise CausalError("propagation hop endpoints do not connect")
        temporal = claim_support(hop.get("temporal_claim_ids", []), claim_constraints)
        causal = claim_support(hop.get("causal_claim_ids", []), claim_constraints)
        statuses.append("supported" if temporal == causal == "supported" else "unsupported_or_undecided")
    instance_id = record.get("formal_c7_instance_id")
    results = formal_results or {}
    if instance_id is not None and instance_id not in results:
        raise CausalError("C7 formal instance does not resolve")
    instance = results.get(instance_id, {})
    return {
        "hop_results": statuses,
        "cascade": "supported" if statuses and all(status == "supported" for status in statuses) else "unsupported_or_undecided",
        "common_cause": claim_support(record.get("common_cause_claim_ids", []), claim_constraints),
        "ordinary_externality": claim_support(record.get("ordinary_externality_claim_ids", []), claim_constraints),
        "formal_c7": "supported" if instance.get("qualification") == "qualified" and instance.get("formal_result") == "supported" else "unsupported_or_undecided",
    }


def assess_recovery(
    record: Mapping[str, Any], *, claim_constraints: Mapping[str, Any]
) -> dict[str, Any]:
    _required(record, ("function", "population", "window", "support_conditions"))
    result = deepcopy(dict(record))
    for name, field in (
        ("function_recovery", "function_claim_ids"), ("sustainability", "sustainability_claim_ids"),
        ("internal_margin", "internal_margin_claim_ids"), ("external_burden", "external_burden_claim_ids"),
        ("reliability", "reliability_test_claim_ids"),
    ):
        result[name] = claim_support(record.get(field, []), claim_constraints)
    return result


__all__ = ("CausalError", "assess_effect", "assess_history", "assess_feedback", "assess_measurement", "assess_propagation", "assess_recovery", "claim_support", "freeze_history_contract")
