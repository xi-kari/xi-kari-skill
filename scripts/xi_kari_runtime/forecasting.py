"""Typed forecast expressions and prospective evaluation boundaries."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import math
from typing import Any

from .causality import CausalError, claim_support
from .canonical_json import sha256_json
from .problem_contract import parse_instant


class ForecastError(ValueError):
    """A forecast exceeds its registered evidence or expression type."""


EXPRESSION_FIELDS = {
    "unknown": {"reason", "minimal_observations"},
    "computation_priority": {"priority", "reasons", "budget"},
    "subjective_belief": {"subject", "information", "time", "value", "basis_claim_ids"},
    "decision_weight": {"value", "weight_model", "premise_or_model_claim_ids"},
    "support_order": {"comparison_domain", "items", "order_groups", "incomparable_items", "reverse_signals", "basis_claim_ids"},
    "direction": {"direction", "identification_conditions", "trigger_points", "minimal_observations", "stop_conditions", "basis_claim_ids"},
    "conditional_model": {"value", "model_version", "assumptions", "domain", "generation_method", "uncertainty", "probability_scope", "prior", "data", "model_claim_ids", "analysis_claim_ids", "target_domain_mapping", "calibration"},
    "empirical_frequency": {"value", "positive_outcomes", "sample_size", "reference_class", "measurement_unit", "cutoff", "sampling_selection", "support_claim_ids", "population_kind", "calibration"},
    "probability_interval": {"lower", "upper", "method", "interpretation", "level", "level_status", "level_reason", "base_expression", "analysis_claim_ids", "calibration"},
}


def _required(record: Mapping[str, Any], fields: tuple[str, ...]) -> None:
    if any(not record.get(field) for field in fields):
        raise ForecastError("forecast lacks a required basis or scope field")


def _number(value: object, *, probability: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ForecastError("forecast value must be finite and numeric")
    if probability and not 0 <= value <= 1:
        raise ForecastError("probability must be between zero and one")
    return float(value)


def _supported(refs: object, constraints: Mapping[str, Any]) -> None:
    try:
        status = claim_support(refs, constraints)
    except CausalError as error:
        raise ForecastError("forecast support claims do not resolve") from error
    if status != "supported":
        raise ForecastError("forecast lacks supported basis claims")


def _calibration(record: Mapping[str, Any], constraints: Mapping[str, Any]) -> None:
    status = record.get("status")
    if status in {"not_tested", "insufficient"}:
        _required(record, ("reason",))
    elif status == "evaluated":
        _required(record, ("model_version", "window", "domain", "metric", "result_claim_ids"))
        _supported(record["result_claim_ids"], constraints)
    else:
        raise ForecastError("calibration must retain a distinct evaluation status")


def validate_probability_expression(
    expression: Mapping[str, Any], *, claim_constraints: Mapping[str, Any]
) -> dict[str, Any]:
    record = deepcopy(dict(expression))
    kind = record.get("kind")
    if kind not in EXPRESSION_FIELDS:
        raise ForecastError("unknown forecast expression kind")
    if set(record) - EXPRESSION_FIELDS[kind] - {"kind", "event", "expression_id"}:
        raise ForecastError("forecast field does not belong to its expression type")
    _required(record, ("event",))
    if kind == "probability_interval":
        _required(record, ("method", "interpretation", "level_status", "base_expression"))
        lower, upper = _number(record.get("lower"), probability=True), _number(record.get("upper"), probability=True)
        if lower > upper:
            raise ForecastError("probability interval endpoints are reversed")
        if record["level_status"] == "provided":
            _number(record.get("level"), probability=True)
        elif record["level_status"] == "not_applicable":
            _required(record, ("level_reason",))
            if "level" in record:
                raise ForecastError("inapplicable interval level cannot carry a number")
        else:
            raise ForecastError("interval level status is invalid")
        base = record["base_expression"]
        if not isinstance(base, Mapping) or base.get("kind") not in {"empirical_frequency", "conditional_model"} or base.get("event") != record["event"]:
            raise ForecastError("interval must bind a numeric basis for the same target")
        validate_probability_expression(base, claim_constraints=claim_constraints)
        _supported(record.get("analysis_claim_ids", []), claim_constraints)
        _calibration(record.get("calibration", {}), claim_constraints)
        return record
    if kind in {"unknown", "computation_priority", "subjective_belief", "decision_weight", "support_order", "direction"}:
        if "numeric_probability" in record or "calibration" in record:
            raise ForecastError("nonprobability expression cannot carry reality probability or calibration")
        if kind == "unknown":
            _required(record, ("reason", "minimal_observations"))
            if "value" in record or "direction" in record:
                raise ForecastError("unknown forecast cannot invent a value or direction")
        elif kind == "computation_priority":
            _required(record, ("reasons", "budget"))
            if isinstance(record.get("priority"), bool) or not isinstance(record.get("priority"), int) or record["priority"] < 1:
                raise ForecastError("computation priority requires a positive ordinal")
            _required(record["budget"], ("unit",))
            if _number(record["budget"].get("amount")) < 0:
                raise ForecastError("computation budget cannot be negative")
        elif kind == "subjective_belief":
            _required(record, ("subject", "information", "time"))
            parse_instant(record["time"], field="subjective belief time")
            _number(record.get("value"), probability=True)
            _supported(record.get("basis_claim_ids", []), claim_constraints)
        elif kind == "decision_weight":
            _required(record, ("weight_model",))
            _number(record.get("value"))
            _supported(record.get("premise_or_model_claim_ids", []), claim_constraints)
        elif kind == "support_order":
            _required(record, ("comparison_domain", "items", "reverse_signals"))
            items = record["items"]
            groups = record.get("order_groups", [])
            incomparable = record.get("incomparable_items", [])
            if not isinstance(items, list) or not isinstance(groups, list) or not isinstance(incomparable, list) or any(not isinstance(group, list) or not group for group in groups):
                raise ForecastError("support order must record a partial order and incomparable items")
            allocated = [item for group in groups for item in group] + incomparable
            if any(not isinstance(item, str) for item in allocated + items) or len(allocated) != len(set(allocated)) or set(allocated) != set(items) or len(items) != len(set(items)):
                raise ForecastError("support order does not partition its comparison domain")
            _supported(record.get("basis_claim_ids", []), claim_constraints)
        else:
            _required(record, ("identification_conditions", "trigger_points", "minimal_observations", "stop_conditions"))
            if record.get("direction") not in {"increase", "decrease", "unchanged"}:
                raise ForecastError("direction expression has no identified direction")
            _supported(record.get("basis_claim_ids", []), claim_constraints)
        return record
    if kind == "conditional_model":
        _required(record, ("event", "model_version", "assumptions", "domain", "generation_method", "uncertainty", "probability_scope"))
        value = _number(record.get("value"), probability=True)
        _supported(record.get("model_claim_ids", []), claim_constraints)
        _supported(record.get("analysis_claim_ids", []), claim_constraints)
        prior, data = record.get("prior", {}), record.get("data", {})
        if prior.get("mode") == "specified":
            _required(prior, ("distribution",))
            _supported(prior.get("basis_claim_ids", []), claim_constraints)
        elif prior.get("mode") == "not_applicable":
            _required(prior, ("reason",))
        else:
            raise ForecastError("conditional model must identify its prior responsibility")
        if data.get("status") == "observed":
            _supported(data.get("basis_claim_ids", []), claim_constraints)
        elif data.get("status") == "none":
            _required(data, ("reason",))
            if prior.get("mode") != "specified":
                raise ForecastError("a no-data model requires an explicit supported prior")
        else:
            raise ForecastError("conditional model data status is missing")
        if record["generation_method"] == "beta_binomial_posterior_mean":
            if prior.get("distribution") != "beta":
                raise ForecastError("beta-binomial generation requires a beta prior")
            alpha, beta = _number(prior.get("alpha")), _number(prior.get("beta"))
            if alpha <= 0 or beta <= 0:
                raise ForecastError("beta prior parameters must be positive")
            n, s = (0, 0) if data["status"] == "none" else (data.get("sample_size"), data.get("positive_outcomes"))
            if any(isinstance(item, bool) or not isinstance(item, int) for item in (n, s)) or not 0 <= s <= n:
                raise ForecastError("beta-binomial observations require integer counts")
            if abs(value - (alpha + s) / (alpha + beta + n)) > 1e-12:
                raise ForecastError("conditional posterior differs from the registered model calculation")
        if record["probability_scope"] == "world_probability":
            mapping = record.get("target_domain_mapping", {})
            _required(mapping, ("target_event", "target_domain", "limits"))
            if mapping["target_event"] != record["event"] or mapping["target_domain"] != record["domain"]:
                raise ForecastError("world probability mapping differs from its target")
            _supported(mapping.get("basis_claim_ids", []), claim_constraints)
        elif record["probability_scope"] != "model_conditional":
            raise ForecastError("conditional probability scope is not recognized")
        _calibration(record.get("calibration", {}), claim_constraints)
        return record
    if kind != "empirical_frequency":
        raise ForecastError("unknown forecast expression kind")
    _required(record, ("event", "reference_class", "measurement_unit", "cutoff", "sampling_selection", "population_kind"))
    parse_instant(record["cutoff"], field="frequency cutoff")
    successes, count = record.get("positive_outcomes"), record.get("sample_size")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in (successes, count)) or count < 1 or not 0 <= successes <= count:
        raise ForecastError("empirical frequency requires integer counts and a positive denominator")
    value = _number(record.get("value"), probability=True)
    if abs(value - successes / count) > 1e-12:
        raise ForecastError("empirical frequency differs from its count ratio")
    if record["population_kind"] != "observed_trials":
        raise ForecastError("simulation draw frequency is not empirical reality probability")
    _supported(record.get("support_claim_ids", []), claim_constraints)
    _calibration(record.get("calibration", {}), claim_constraints)
    return record


def _parent_binding(state: Mapping[str, Any], transition: Mapping[str, Any]) -> dict[str, str]:
    if transition.get("result_state_sha256") != sha256_json(state) or transition.get("output_state") != state:
        raise ForecastError("forecast parent state does not match its actual transition")
    _required(transition, ("state_diff_id", "source_state_sha256"))
    return {"parent_state_sha256": sha256_json(state), "parent_transition_sha256": sha256_json(transition)}


def freeze_forecast(
    record: Mapping[str, Any], *, parent_state: Mapping[str, Any],
    parent_transition: Mapping[str, Any], claim_constraints: Mapping[str, Any],
) -> dict[str, Any]:
    _required(record, (
        "forecast_id", "model_version", "target", "deadline", "object_id", "identity_criterion",
        "scope", "scale", "allowed_error", "baseline_time", "input_cutoff", "registered_at",
        "resources", "parent_state_diff_id", "event_criterion", "baseline_ids", "paths",
        "early_signals", "reverse_signals", "abstention_conditions", "stop_conditions",
        "retirement_conditions", "calibration_plan", "outcome_source", "expression",
    ))
    if record.get("order") not in {1, 2, 3} or isinstance(record.get("order"), bool):
        raise ForecastError("forecast order must be registered separately")
    times = [parse_instant(record[field], field="forecast time boundary") for field in ("baseline_time", "input_cutoff", "registered_at", "deadline")]
    if not times[0] <= times[1] <= times[2] < times[3]:
        raise ForecastError("forecast input and registration must precede its deadline")
    objects = [obj for obj in parent_state.get("objects", []) if obj.get("object_id") == record["object_id"]]
    if len(objects) != 1 or objects[0].get("K") != record["identity_criterion"] or record["parent_state_diff_id"] != parent_transition.get("state_diff_id"):
        raise ForecastError("forecast object or K differs from its actual parent")
    if set(record["baseline_ids"]) != {"state-continuation", "direct-long-range", "shallow-plus-continuation"} or len(record["baseline_ids"]) != 3:
        raise ForecastError("forecast must retain all three order-specific comparisons")
    if record["event_criterion"].get("relation") not in {"at_most", "at_least"}:
        raise ForecastError("forecast event must have a decidable registered relation")
    _required(record["event_criterion"], ("metric",))
    _number(record["event_criterion"].get("threshold"))
    validate_probability_expression(record["expression"], claim_constraints=claim_constraints)
    if record["expression"]["event"] != record["target"]:
        raise ForecastError("forecast probability expression differs from its target")
    contract = deepcopy(dict(record))
    return {"contract": contract, "contract_sha256": sha256_json(contract), **_parent_binding(parent_state, parent_transition), "evaluations": []}


def append_forecast_result(
    frozen: Mapping[str, Any], result: Mapping[str, Any], *,
    parent_state: Mapping[str, Any], parent_transition: Mapping[str, Any],
    claim_constraints: Mapping[str, Any],
) -> dict[str, Any]:
    contract = frozen["contract"]
    if frozen.get("contract_sha256") != sha256_json(contract):
        raise ForecastError("frozen forecast contract changed")
    binding = _parent_binding(parent_state, parent_transition)
    if any(frozen.get(key) != value for key, value in binding.items()):
        raise ForecastError("frozen forecast parent binding changed")
    registered = parse_instant(contract["registered_at"], field="forecast registration")
    accessed = parse_instant(result["first_result_access_at"], field="forecast result access")
    evaluated = parse_instant(result["evaluated_at"], field="forecast evaluation")
    if registered >= accessed or accessed > evaluated or evaluated < parse_instant(contract["deadline"], field="forecast deadline"):
        raise ForecastError("forecast result does not follow its frozen prospective contract")
    kind = result.get("kind")
    if kind == "observed":
        _supported(result.get("basis_claim_ids", []), claim_constraints)
        criterion = contract["event_criterion"]
        metrics = result.get("observed_metrics", {})
        if criterion["metric"] not in metrics:
            raise ForecastError("forecast outcome lacks its registered target measurement")
        value = _number(metrics[criterion["metric"]])
        passed = value <= criterion["threshold"] if criterion["relation"] == "at_most" else value >= criterion["threshold"]
        status = "supported" if passed else "not_supported"
    elif kind in {"undecided", "target_invalid", "unevaluable"}:
        _required(result, ("reason",))
        if kind == "target_invalid":
            _supported(result.get("basis_claim_ids", []), claim_constraints)
        status = kind
    else:
        raise ForecastError("forecast outcome kind is not recognized")
    snapshot = deepcopy(dict(frozen))
    row = {**deepcopy(dict(result)), "status": status, "forecast_contract_sha256": frozen["contract_sha256"]}
    if snapshot["evaluations"] and evaluated <= parse_instant(snapshot["evaluations"][-1]["evaluated_at"], field="previous forecast evaluation"):
        raise ForecastError("forecast result history must be append-only in time")
    snapshot["evaluations"].append(row)
    return snapshot


def evaluate_order_comparison(
    records: list[Mapping[str, Any]], *, claim_constraints: Mapping[str, Any]
) -> dict[str, Any]:
    groups: dict[int, list[Mapping[str, Any]]] = {}
    seen: set[str] = set()
    names = {"state-continuation", "direct-long-range", "shallow-plus-continuation"}
    for row in records:
        _required(row, ("forecast_id", "source_lineage_refs", "comparison", "outcome_available_at"))
        if row["forecast_id"] in seen or row.get("order") not in {1, 2, 3} or isinstance(row.get("order"), bool):
            raise ForecastError("order comparison has a duplicate forecast or invalid order")
        seen.add(row["forecast_id"])
        _supported(row.get("basis_claim_ids", []), claim_constraints)
        _number(row.get("probability"), probability=True)
        if row.get("outcome") not in {0, 1} or isinstance(row.get("outcome"), bool):
            raise ForecastError("Brier evaluation requires a binary observed outcome")
        comparison = row["comparison"]
        _required(comparison, ("target", "input_cutoff", "information_sha256", "evaluation_rule", "window", "registered_at"))
        if parse_instant(comparison["registered_at"], field="comparison registration") >= parse_instant(row["outcome_available_at"], field="comparison outcome"):
            raise ForecastError("comparison was not frozen before outcome access")
        if comparison["evaluation_rule"] != "brier-v1" or _number(row.get("reasoning_budget")) < 0:
            raise ForecastError("comparison metric or resource budget is invalid")
        if set(row.get("baselines", {})) != names:
            raise ForecastError("each order needs all three registered baselines")
        for baseline in row["baselines"].values():
            _number(baseline.get("probability"), probability=True)
            if _number(baseline.get("reasoning_budget")) < 0:
                raise ForecastError("baseline resource budget is invalid")
        groups.setdefault(row["order"], []).append(row)
    orders = []
    for order, rows in sorted(groups.items()):
        comparable = all(row.get("evaluation_status") == "out_of_sample" and all(baseline.get("comparison") == row["comparison"] for baseline in row["baselines"].values()) for row in rows)
        n = len(rows)
        score = sum((row["probability"] - row["outcome"]) ** 2 for row in rows) / n
        baselines = {name: sum((row["baselines"][name]["probability"] - row["outcome"]) ** 2 for row in rows) / n for name in sorted(names)}
        orders.append({"order": order, "n": n, "brier_score": score, "baseline_scores": baselines,
            "comparison_state": "comparable" if comparable else "not_comparable",
            "scoped_gain": {name: baselines[name] - score if comparable else None for name in sorted(names)},
            "source_lineage_refs": sorted({ref for row in rows for ref in row["source_lineage_refs"]}),
            "resources": [{"forecast_id": row["forecast_id"], "reasoning_budget": row["reasoning_budget"], "baseline_budgets": {name: value["reasoning_budget"] for name, value in row["baselines"].items()}} for row in rows]})
    return {"orders": orders, "capability_state": "capability_not_established"}


def evaluate_alert(record: Mapping[str, Any], *, claim_constraints: Mapping[str, Any]) -> dict[str, Any]:
    counts = [record.get(field) for field in ("true_positive", "false_positive", "true_negative", "false_negative")]
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts):
        raise ForecastError("alert classification needs nonnegative integer counts")
    _supported(record.get("count_basis_claim_ids", []), claim_constraints)
    _supported(record.get("clock_basis_claim_ids", []), claim_constraints)
    tp, fp, tn, fn = counts
    def ratio(numerator: int, denominator: int) -> float | None:
        return numerator / denominator if denominator else None
    sequence = ("discovered_at", "verified_at", "published_at", "reached_at", "understood_at", "resourced_at", "effective_at", "protected_at")
    clocks = record.get("clocks", {})
    if not isinstance(clocks, Mapping) or set(clocks) - set(sequence):
        raise ForecastError("alert clocks must distinguish the response chain")
    parsed = [parse_instant(clocks[key], field="alert clock") for key in sequence if key in clocks]
    if parsed != sorted(parsed):
        raise ForecastError("alert response clocks are out of order")
    if record.get("response_changed_outcome") not in {"supported", "unsupported_or_undecided", "unknown"}:
        raise ForecastError("alert response causal effect needs a distinct result")
    protection = claim_support(record.get("protection_claim_ids", []), claim_constraints)
    if any(key not in clocks for key in sequence):
        protection = "unsupported_or_undecided"
    return {"false_positive_rate": ratio(fp, fp + tn), "false_alert_fraction": ratio(fp, tp + fp), "false_negative_rate": ratio(fn, tp + fn),
        "denominators": {"negative_trials": fp + tn, "alerts": tp + fp, "positive_trials": tp + fn},
        "clocks": deepcopy(clocks), "response_changed_outcome": record["response_changed_outcome"], "actual_protection": protection, "permission_effect": "none"}


def evaluate_information_value(record: Mapping[str, Any], *, claim_constraints: Mapping[str, Any]) -> dict[str, Any]:
    _supported(record.get("model_claim_ids", []), claim_constraints)
    _supported(record.get("utility_premise_claim_ids", []), claim_constraints)
    _required(record, ("utility_unit", "state_probabilities", "signal_likelihoods", "utilities", "formal_assumptions"))
    assumptions = record["formal_assumptions"]
    required = {"free_information", "can_ignore_information", "action_set_unchanged", "objective_unchanged"}
    if set(assumptions) != required or any(value is not True for value in assumptions.values()):
        return {"formal_evsi": None, "net_value": None, "formal_state": "not_applicable", "real_costs": deepcopy(record.get("real_costs", []))}
    probabilities, signals, utilities = record["state_probabilities"], record["signal_likelihoods"], record["utilities"]
    states = set(probabilities)
    if any(abs(sum(_number(values[state], probability=True) for values in signals.values()) - 1) > 1e-12 for state in states) or abs(sum(_number(value, probability=True) for value in probabilities.values()) - 1) > 1e-12:
        raise ForecastError("information model probabilities do not normalize")
    if any(set(values) != states for values in list(signals.values()) + list(utilities.values())):
        raise ForecastError("information model state domains differ")
    for values in utilities.values():
        for value in values.values():
            _number(value)
    baseline = max(sum(probabilities[state] * values[state] for state in states) for values in utilities.values())
    informed = sum(max(sum(probabilities[state] * likelihood[state] * values[state] for state in states) for values in utilities.values()) for likelihood in signals.values())
    evsi = informed - baseline
    costs = record.get("real_costs", [])
    if not isinstance(costs, list):
        raise ForecastError("real information costs must be a distribution record list")
    for cost in costs:
        _required(cost, ("kind", "unit", "bearers"))
        if _number(cost.get("value")) < 0:
            raise ForecastError("information cost cannot be negative")
    same_unit = all(cost["unit"] == record["utility_unit"] for cost in costs)
    return {"formal_evsi": evsi, "formal_state": "conditional_on_registered_assumptions", "net_value": evsi - sum(cost["value"] for cost in costs) if same_unit else None, "real_costs": deepcopy(costs), "utility_unit": record["utility_unit"]}


__all__ = ("ForecastError", "validate_probability_expression", "freeze_forecast", "append_forecast_result", "evaluate_order_comparison", "evaluate_alert", "evaluate_information_value")
