from copy import deepcopy
from importlib import import_module
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from xi_kari_runtime.canonical_json import sha256_json


def forecast_inputs():
    state = {"snapshot_id": "synthetic-S1", "run_id": "synthetic-run", "model_version": "v1", "objects": [{"object_id": "object-1", "K": {"membership": ["unit-1"]}, "variables": [{"variable_id": "delay", "category": "resources", "value": 1, "clock_id": "weekly"}]}]}
    transition = {"state_diff_id": "synthetic-diff-1", "source_state_sha256": "0" * 64, "result_state_sha256": sha256_json(state), "output_state": state}
    record = {
        "forecast_id": "synthetic-F1", "model_version": "v1", "target": "synthetic-delay-decline",
        "deadline": "2026-02-01T00:00:00Z", "object_id": "object-1", "identity_criterion": state["objects"][0]["K"],
        "scope": "unit-1", "scale": "weekly-individual", "allowed_error": {"unit": "hours", "value": 0.1},
        "baseline_time": "2026-01-01T00:00:00Z", "input_cutoff": "2026-01-01T00:00:00Z", "registered_at": "2026-01-02T00:00:00Z",
        "resources": {"information": "frozen-synthetic-material", "computation": "15-minutes"}, "order": 1,
        "parent_state_diff_id": transition["state_diff_id"], "event_criterion": {"metric": "delay-change", "relation": "at_most", "threshold": -0.1},
        "baseline_ids": ["state-continuation", "direct-long-range", "shallow-plus-continuation"],
        "paths": ["direct-path"], "early_signals": ["shorter-handoff"], "reverse_signals": ["longer-handoff"],
        "abstention_conditions": ["insufficient-evidence"], "stop_conditions": ["object-changes"], "retirement_conditions": ["repeated-no-gain"],
        "calibration_plan": "brier-on-registered-future-trials", "outcome_source": "synthetic-measurement",
        "expression": {"kind": "unknown", "event": "synthetic-delay-decline", "reason": "Probability unknown", "minimal_observations": ["measure-delay"]},
    }
    return record, state, transition


def test_forecast_failure_remains_frozen_and_new_target_requires_new_version():
    forecast = import_module("xi_kari_runtime.forecasting")
    record, state, transition = forecast_inputs()
    frozen = forecast.freeze_forecast(record, parent_state=state, parent_transition=transition, claim_constraints={})
    result = {"kind": "observed", "evaluated_at": "2026-02-02T00:00:00Z", "first_result_access_at": "2026-02-01T00:00:00Z", "observed_metrics": {"delay-change": 0.5}, "basis_claim_ids": ["outcome"]}
    updated = forecast.append_forecast_result(frozen, result, parent_state=state, parent_transition=transition, claim_constraints={"outcome": {"blocked": False}})
    assert updated["evaluations"][0]["status"] == "not_supported"
    assert frozen["evaluations"] == []
    updated["contract"]["deadline"] = "2026-03-01T00:00:00Z"
    with pytest.raises(forecast.ForecastError, match="frozen"):
        forecast.append_forecast_result(updated, result, parent_state=state, parent_transition=transition, claim_constraints={"outcome": {"blocked": False}})


def test_forecasts_from_correlated_orders_are_scored_by_order_with_all_baselines():
    forecast = import_module("xi_kari_runtime.forecasting")
    comparison = {"target": "synthetic-event", "input_cutoff": "2026-01-01T00:00:00Z", "information_sha256": "a" * 64, "evaluation_rule": "brier-v1", "window": "January", "registered_at": "2026-01-01T00:00:00Z"}
    rows = []
    for order, probability in ((1, 0.8), (2, 0.7), (3, 0.6)):
        rows.append({"order": order, "forecast_id": f"synthetic-F{order}", "probability": probability, "outcome": 1, "outcome_available_at": "2026-02-01T00:00:00Z", "evaluation_status": "out_of_sample", "basis_claim_ids": ["actual-outcome"], "source_lineage_refs": ["one-frozen-origin"], "comparison": comparison, "reasoning_budget": 100,
            "baselines": {name: {"probability": 0.5, "comparison": deepcopy(comparison), "reasoning_budget": 20} for name in ("state-continuation", "direct-long-range", "shallow-plus-continuation")}})
    result = forecast.evaluate_order_comparison(rows, claim_constraints={"actual-outcome": {"blocked": False}})
    assert [item["order"] for item in result["orders"]] == [1, 2, 3]
    assert [item["brier_score"] for item in result["orders"]] == pytest.approx([0.04, 0.09, 0.16])
    assert all(len(item["baseline_scores"]) == 3 for item in result["orders"])
    assert result["capability_state"] == "capability_not_established"
    assert "aggregate_hit_rate" not in result
    rows[2]["baselines"]["state-continuation"]["comparison"]["information_sha256"] = "b" * 64
    result = forecast.evaluate_order_comparison(rows, claim_constraints={"actual-outcome": {"blocked": False}})
    assert result["orders"][2]["comparison_state"] == "not_comparable"


def test_alert_denominators_and_protection_clock_remain_distinct():
    forecast = import_module("xi_kari_runtime.forecasting")
    record = {"true_positive": 3, "false_positive": 1, "true_negative": 8, "false_negative": 2,
        "count_basis_claim_ids": ["classified-trials"], "response_changed_outcome": "unknown",
        "clocks": {"discovered_at": "2026-01-01T00:00:00Z", "verified_at": "2026-01-01T01:00:00Z", "published_at": "2026-01-01T02:00:00Z"},
        "clock_basis_claim_ids": ["clock-observations"]}
    result = forecast.evaluate_alert(record, claim_constraints={ref: {"blocked": False} for ref in ("classified-trials", "clock-observations")})
    assert result["false_positive_rate"] == pytest.approx(1 / 9)
    assert result["false_alert_fraction"] == pytest.approx(1 / 4)
    assert result["false_negative_rate"] == pytest.approx(2 / 5)
    assert result["actual_protection"] == "unsupported_or_undecided"
    assert result["permission_effect"] == "none"


def test_formal_information_value_can_be_positive_while_net_inquiry_value_is_negative():
    forecast = import_module("xi_kari_runtime.forecasting")
    record = {
        "state_probabilities": {"A": 0.5, "B": 0.5},
        "signal_likelihoods": {"A-signal": {"A": 1.0, "B": 0.0}, "B-signal": {"A": 0.0, "B": 1.0}},
        "utilities": {"choose-A": {"A": 1.0, "B": 0.0}, "choose-B": {"A": 0.0, "B": 1.0}},
        "utility_unit": "registered-utility", "model_claim_ids": ["model"], "utility_premise_claim_ids": ["normative-premise"],
        "formal_assumptions": {"free_information": True, "can_ignore_information": True, "action_set_unchanged": True, "objective_unchanged": True},
        "real_costs": [{"kind": "lost-window", "unit": "registered-utility", "value": 0.8, "bearers": ["affected-position"]}],
    }
    result = forecast.evaluate_information_value(record, claim_constraints={ref: {"blocked": False} for ref in ("model", "normative-premise")})
    assert result["formal_evsi"] == pytest.approx(0.5)
    assert result["net_value"] == pytest.approx(-0.3)
    record["real_costs"][0]["unit"] = "unconverted-privacy-burden"
    assert forecast.evaluate_information_value(record, claim_constraints={ref: {"blocked": False} for ref in ("model", "normative-premise")})["net_value"] is None


def test_forecast_consumes_the_actual_p08_child_and_rejects_stale_state():
    from tests.test_p08_recursive_transitions import recursive_fixture
    from tests.test_p04_v4_claim_contracts import _v4_graph
    from xi_kari_runtime import recursion, stability
    parent, event, evidence, actions = recursive_fixture()
    child = recursion.execute_recursive_step(parent, event, action_catalog=actions, author=lambda request: {"possible_choice_ids": ["WAIT"], "choice_basis": "conditional baseline"}, evidence_registry=evidence, independent_question="Next conditional consequences?", incremental_gain="Changed resource availability")
    record, _, _ = forecast_inputs()
    record.update(object_id="actor", identity_criterion={"version": "1", "definition": "same actor"}, model_version=child["model_version"], order=child["order"], parent_state_diff_id=child["state_diff_id"], baseline_time="2026-09-30T12:00:00Z", input_cutoff="2026-09-30T12:00:00Z", registered_at="2026-09-30T12:01:00Z", deadline="2026-10-30T12:00:00Z")
    kwargs = dict(child=child, parent=parent, event=event, action_catalog=actions, evidence_registry=evidence, claim_mechanism_graph=_v4_graph())
    frozen = stability.freeze_forecast_from_recursive_child(record, **kwargs)
    assert frozen["contract"]["order"] == 2
    assert frozen["parent_state_sha256"] == sha256_json(child["output_state"])
    child["output_state"]["objects"][0]["variables"][0]["value"] = 100
    with pytest.raises(recursion.RecursiveInferenceError):
        stability.freeze_forecast_from_recursive_child(record, **kwargs)
