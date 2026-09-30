from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from tests.test_causal_judgment_choice import comparison_inputs
from tests.test_causal_judgment_forecasts import forecast_inputs
from tests.test_p04_v4_claim_contracts import _v4_graph
from tests.test_p08_recursive_transitions import recursive_fixture
from xi_kari_runtime import judgment, recursion, stability


def chain_inputs():
    parent, event, evidence, actions = recursive_fixture()
    child = recursion.execute_recursive_step(parent, event, action_catalog=actions, author=lambda request: {"possible_choice_ids": ["WAIT"], "choice_basis": "no-new-action-analysis"}, evidence_registry=evidence, independent_question="Conditional next choice?", incremental_gain="Changed action feasibility")
    graph = _v4_graph()
    graph["applicability"]["action_choice"]["status"] = "applicable"
    next(row for row in graph["claims"] if row["claim_id"] == "CLAIM-VALUE")["responsibility_refs"] = ["V90-CANON-N2"]
    record, _, _ = forecast_inputs()
    record.update(object_id="actor", identity_criterion={"version": "1", "definition": "same actor"}, model_version=child["model_version"], order=2, parent_state_diff_id=child["state_diff_id"], baseline_time="2026-09-30T12:00:00Z", input_cutoff="2026-09-30T12:00:00Z", registered_at="2026-09-30T12:01:00Z", deadline="2026-10-30T12:00:00Z")
    kwargs = dict(child=child, parent=parent, event=event, action_catalog=actions, evidence_registry=evidence, claim_mechanism_graph=graph)
    forecast = stability.freeze_forecast_from_recursive_child(record, **kwargs)
    _, comparison = comparison_inputs()
    action_state = recursion.current_action_set(child["output_state"], actions)
    comparison.update(options=deepcopy(action_state["available_actions"]), existing_items=deepcopy(action_state["existing_obligations"]), normative_basis_claim_ids=["CLAIM-VALUE"], scope={"object_id": "actor", "window": "October"})
    return comparison, forecast, kwargs


def test_actual_p04_p08_p09_inputs_reach_normative_comparison_without_granting_permission():
    comparison, forecast, kwargs = chain_inputs()
    checked = judgment.validate_decision_from_recursive_forecast(comparison, forecast=forecast, **kwargs)
    assert checked["recommended_option_id"] == "WAIT"
    assert checked["existing_items"] == [{"obligation_id": "DUTY-1", "content": "existing duty persists"}]
    assert checked["permission_effect"] == "none"
    comparison["normative_basis_claim_ids"] = ["CLAIM-PREDICTION"]
    with pytest.raises(judgment.JudgmentError, match="normative premise"):
        judgment.validate_decision_from_recursive_forecast(comparison, forecast=forecast, **kwargs)


def test_decision_cannot_silently_use_an_unbound_registered_normative_premise():
    comparison, forecast, kwargs = chain_inputs()
    comparison["normative_premises"] = ["N4"]
    with pytest.raises(judgment.JudgmentError, match="registered N premise"):
        judgment.validate_decision_from_recursive_forecast(comparison, forecast=forecast, **kwargs)
