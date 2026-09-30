from copy import deepcopy
from importlib import import_module
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def frequency():
    return {
        "kind": "empirical_frequency", "event": "synthetic-task-pass", "value": 2 / 3,
        "positive_outcomes": 2, "sample_size": 3, "reference_class": "synthetic-enrollees-v1",
        "measurement_unit": "one-registered-task", "cutoff": "2026-01-01T00:00:00Z",
        "sampling_selection": "all-registered-tasks", "support_claim_ids": ["frequency-data"],
        "population_kind": "observed_trials", "calibration": {"status": "not_tested", "reason": "No separate outcome evaluation"},
    }


def test_empirical_frequency_recomputes_ratio_and_keeps_calibration_separate():
    forecast = import_module("xi_kari_runtime.forecasting")
    record = frequency()
    checked = forecast.validate_probability_expression(record, claim_constraints={"frequency-data": {"blocked": False}})
    assert checked["value"] == pytest.approx(2 / 3)
    assert checked["calibration"]["status"] == "not_tested"
    record["value"] = 0.8
    with pytest.raises(forecast.ForecastError, match="ratio"):
        forecast.validate_probability_expression(record, claim_constraints={"frequency-data": {"blocked": False}})


def conditional_model():
    return {
        "kind": "conditional_model", "event": "synthetic-next-task-pass", "value": 4 / 7,
        "model_version": "synthetic-beta-binomial-v1", "assumptions": ["exchangeable-within-domain"],
        "domain": "synthetic-task-domain", "generation_method": "beta_binomial_posterior_mean",
        "uncertainty": "model-dependent; three observations", "probability_scope": "model_conditional",
        "prior": {"mode": "specified", "distribution": "beta", "alpha": 2, "beta": 2, "basis_claim_ids": ["prior-basis"]},
        "data": {"status": "observed", "sample_size": 3, "positive_outcomes": 2, "basis_claim_ids": ["data-basis"]},
        "model_claim_ids": ["model-basis"], "analysis_claim_ids": ["calculation-basis"],
        "calibration": {"status": "not_tested", "reason": "No empirical calibration sample"},
    }


def test_small_sample_conditional_posterior_is_model_bound_and_not_calibrated():
    forecast = import_module("xi_kari_runtime.forecasting")
    support = {ref: {"blocked": False} for ref in ("prior-basis", "data-basis", "model-basis", "calculation-basis")}
    record = conditional_model()
    result = forecast.validate_probability_expression(record, claim_constraints=support)
    assert result["value"] == pytest.approx(4 / 7)
    assert result["probability_scope"] == "model_conditional"
    assert result["calibration"]["status"] == "not_tested"
    record["data"]["basis_claim_ids"] = []
    with pytest.raises(forecast.ForecastError, match="basis"):
        forecast.validate_probability_expression(record, claim_constraints=support)


@pytest.mark.parametrize("kind,details", [
    ("unknown", {"reason": "Direction and probability not identified", "minimal_observations": ["Collect a discriminating outcome"]}),
    ("computation_priority", {"priority": 1, "reasons": ["Severe consequences and a short response window"], "budget": {"unit": "analyst-minutes", "amount": 15}}),
    ("subjective_belief", {"subject": "synthetic-actor", "information": "synthetic-report", "time": "2026-01-01T00:00:00Z", "value": 0.8, "basis_claim_ids": ["basis"]}),
    ("decision_weight", {"value": 0.8, "weight_model": "public-normative-premise", "premise_or_model_claim_ids": ["basis"]}),
    ("support_order", {"comparison_domain": "registered-paths", "items": ["A", "B", "C"], "order_groups": [["A", "B"]], "incomparable_items": ["C"], "reverse_signals": ["Material refutes the shared premise"], "basis_claim_ids": ["basis"]}),
])
def test_nonprobability_expression_retains_its_type_without_fabricating_probability(kind, details):
    forecast = import_module("xi_kari_runtime.forecasting")
    result = forecast.validate_probability_expression({"kind": kind, "event": "synthetic-target", **details}, claim_constraints={"basis": {"blocked": False}})
    assert result["kind"] == kind
    assert "numeric_probability" not in result
    assert "calibrated" not in result


def test_direction_also_requires_identification_not_a_fallback():
    forecast = import_module("xi_kari_runtime.forecasting")
    record = {"kind": "direction", "event": "synthetic-target", "direction": "increase", "identification_conditions": ["registered-comparison"], "trigger_points": ["observed-input"], "minimal_observations": ["measure-target"], "stop_conditions": ["scope-changes"], "basis_claim_ids": ["basis"]}
    assert forecast.validate_probability_expression(record, claim_constraints={"basis": {"blocked": False}})["direction"] == "increase"
    with pytest.raises(forecast.ForecastError, match="basis"):
        forecast.validate_probability_expression(record, claim_constraints={"basis": {"blocked": True}})


def test_probability_interval_preserves_its_method_and_interpretation():
    forecast = import_module("xi_kari_runtime.forecasting")
    record = {
        "kind": "probability_interval", "event": "synthetic-next-task-pass", "lower": 0.2, "upper": 0.8,
        "method": "beta-posterior-quantiles", "interpretation": "conditional-credible-region",
        "level": 0.9, "level_status": "provided", "base_expression": conditional_model(),
        "analysis_claim_ids": ["interval-calculation"],
        "calibration": {"status": "not_tested", "reason": "Coverage not evaluated"},
    }
    support = {ref: {"blocked": False} for ref in ("prior-basis", "data-basis", "model-basis", "calculation-basis", "interval-calculation")}
    result = forecast.validate_probability_expression(record, claim_constraints=support)
    assert result["interpretation"] == "conditional-credible-region"
    assert result["calibration"]["status"] == "not_tested"
    record["lower"] = 0.9
    with pytest.raises(forecast.ForecastError, match="endpoint"):
        forecast.validate_probability_expression(record, claim_constraints=support)


def test_computation_priority_cannot_smuggle_a_numeric_probability_value():
    forecast = import_module("xi_kari_runtime.forecasting")
    record = {"kind": "computation_priority", "event": "synthetic-target", "priority": 1, "reasons": ["short-window"], "budget": {"unit": "minutes", "amount": 15}, "value": 0.9}
    with pytest.raises(forecast.ForecastError, match="field"):
        forecast.validate_probability_expression(record, claim_constraints={})


@pytest.mark.parametrize("change", ["noninteger", "simulation", "missing-reference", "false-calibration", "failed-basis"])
def test_empirical_probability_preserves_denominator_lineage_and_calibration_gates(change):
    forecast = import_module("xi_kari_runtime.forecasting")
    record = frequency()
    support = {"frequency-data": {"blocked": False}}
    if change == "noninteger":
        record["sample_size"] = True
    elif change == "simulation":
        record["population_kind"] = "model_draws"
    elif change == "missing-reference":
        record["reference_class"] = ""
    elif change == "false-calibration":
        record["calibration"] = {"status": "evaluated", "model_version": "v1", "window": "January", "domain": "tasks", "metric": "brier", "result_claim_ids": []}
    else:
        support["frequency-data"]["blocked"] = True
    with pytest.raises(forecast.ForecastError):
        forecast.validate_probability_expression(record, claim_constraints=support)


def test_pure_prior_remains_explicit_and_missing_world_mapping_is_rejected():
    forecast = import_module("xi_kari_runtime.forecasting")
    record = conditional_model()
    record["data"] = {"status": "none", "reason": "No empirical observations"}
    record["value"] = 0.5
    support = {ref: {"blocked": False} for ref in ("prior-basis", "model-basis", "calculation-basis")}
    checked = forecast.validate_probability_expression(record, claim_constraints=support)
    assert checked["data"]["status"] == "none"
    record["probability_scope"] = "world_probability"
    with pytest.raises(forecast.ForecastError):
        forecast.validate_probability_expression(record, claim_constraints=support)


def test_zero_empirical_observations_must_be_declared_as_no_data():
    forecast = import_module("xi_kari_runtime.forecasting")
    record = conditional_model()
    record["value"] = 0.5
    record["data"].update(sample_size=0, positive_outcomes=0)
    support = {ref: {"blocked": False} for ref in ("prior-basis", "data-basis", "model-basis", "calculation-basis")}
    with pytest.raises(forecast.ForecastError, match="no-data"):
        forecast.validate_probability_expression(record, claim_constraints=support)
