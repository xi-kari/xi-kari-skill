from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from xi_kari_runtime import recursion, world_volume


def recursive_fixture():
    state = {"snapshot_id": "STATE-1", "model_version": "test-model-1", "run_id": "RUN-SYNTHETIC", "evidence_cutoff": "2026-09-30T12:00:00Z", "objects": [{"object_id": "actor", "K": {"version": "1", "definition": "same actor"}, "variables": [{"variable_id": "XK-PROV-CASH", "category": "resources", "value": 10, "clock_id": "interaction"}]}], "unknowns": [{"unknown_id": "UNKNOWN-1", "content": "choice remains uncertain"}], "losses": [{"loss_id": "LOSS-1", "content": "unmeasured care constraints"}], "residuals": [{"residual_id": "RES-1", "content": "unmodeled cost"}], "existing_obligations": [{"obligation_id": "DUTY-1", "content": "existing duty persists"}]}
    parent = {"node_id": "NODE-1", "path_id": "PATH-1", "run_id": "RUN-SYNTHETIC", "order": 1, "status": "active", "output_state": state, "evidence_identity": "simulated", "declared_evidence_grade": "low", "model_version": "test-model-1", "conditions": ["assume current rules remain"], "history": ["original predicted resource spend"], "dimensions": {"time_rolling": True, "simulation_reentry": True, "anticipatory_reflexivity": False}}
    event = {"event_id": "SPEND-1", "actor_id": "actor", "object_id": "actor", "kind": "simulated", "update_path": "scenario", "occurrence_status": "not_occurred", "authorization_status": "unknown", "occurred_at": "2026-10-01T00:00:00Z", "evidence_refs": ["E-SPEND"], "conditions": ["conditional spend occurs"], "deltas": [{"object_id": "actor", "variable_id": "XK-PROV-CASH", "category": "resources", "before": 10, "after": 4, "clock_id": "interaction", "evidence_refs": ["E-SPEND"]}], "channel_id": None, "mechanism_id": None, "authorization_ref": None}
    evidence = {"E-SPEND": {"evidence_id": "E-SPEND", "identity": "simulated", "source_refs": ["SYNTHETIC-UNIT-FIXTURE"], "available_at": "2026-09-30T00:00:00Z", "event_id": "SPEND-1", "object_id": "actor", "variable_id": "XK-PROV-CASH", "observed_value": 4}}
    actions = [
        {"option_id": "WAIT", "option_kind": "no_action", "action_type": "no_new_action", "target_object": "actor", "requirements": []},
        {"option_id": "EXPENSIVE", "option_kind": "external_action", "action_type": "spend eight", "target_object": "actor", "requirements": [{"object_id": "actor", "variable_id": "XK-PROV-CASH", "operator": "ge", "operand": 8, "source_refs": ["SYNTHETIC-COST"]}]},
        {"option_id": "CHEAP", "option_kind": "external_action", "action_type": "spend three", "target_object": "actor", "requirements": [{"object_id": "actor", "variable_id": "XK-PROV-CASH", "operator": "ge", "operand": 3, "source_refs": ["SYNTHETIC-COST"]}]},
    ]
    return parent, event, evidence, actions


def test_typed_resource_difference_changes_actual_next_author_input_and_action_set():
    parent, event, evidence, actions = recursive_fixture()
    before = deepcopy(parent)
    requests = []
    def author(request):
        requests.append(deepcopy(request))
        return {"possible_choice_ids": ["CHEAP"], "choice_basis": "conditional feasible spend"}
    child = recursion.execute_recursive_step(parent, event, action_catalog=actions, author=author, evidence_registry=evidence, independent_question="What can the actor do after spending?", incremental_gain="New resource constraint excludes the expensive option")
    assert len(requests) == 1
    request = requests[0]
    assert request["input_state"]["objects"][0]["variables"][0]["value"] == 4
    assert {option["option_id"] for option in request["available_actions"]} == {"WAIT", "CHEAP"}
    assert request["excluded_actions"][0]["option_id"] == "EXPENSIVE"
    assert request["existing_obligations"] == before["output_state"]["existing_obligations"]
    assert child["output_state"] == request["input_state"]
    assert child["order"] == 2
    assert child["declared_evidence_grade"] == "low"
    assert child["evidence_identity"] == "simulated"
    assert parent == before


def test_stale_child_input_or_unregistered_action_choice_is_rejected():
    parent, event, evidence, actions = recursive_fixture()
    with pytest.raises(recursion.RecursiveInferenceError, match="input"):
        recursion.execute_recursive_step(parent, event, action_catalog=actions, author=lambda request: {}, evidence_registry=evidence, independent_question="Next choices?", incremental_gain="New resources", proposed_input_state=parent["output_state"])
    with pytest.raises(recursion.RecursiveInferenceError, match="choice"):
        recursion.execute_recursive_step(parent, event, action_catalog=actions, author=lambda request: {"possible_choice_ids": ["EXPENSIVE"]}, evidence_registry=evidence, independent_question="Next choices?", incremental_gain="New resources")


def test_failed_parent_blocks_only_dependent_author_calls():
    parent, event, evidence, actions = recursive_fixture()
    failed = deepcopy(parent)
    failed.update(status="stopped", stop_reason="failed mechanism domain", can_say="bounded observed facts", cannot_say="dependent future", next_observation="test channel", continuation_risk="invented pathway")
    calls = []
    result = recursion.execute_recursive_step(failed, event, action_catalog=actions, author=lambda request: calls.append(request), evidence_registry=evidence, independent_question="Next choices?", incremental_gain="New resources")
    assert result["status"] == "not_run"
    assert result["blocked_by_node_id"] == "NODE-1"
    assert calls == []
    result = recursion.execute_recursive_step(parent, event, action_catalog=actions, author=lambda request: {"possible_choice_ids": []}, evidence_registry=evidence, independent_question="Independent branch?", incremental_gain="New resources")
    assert result["status"] == "active"


def test_no_independent_next_question_completes_without_invented_residual():
    parent, event, evidence, actions = recursive_fixture()
    result = recursion.execute_recursive_step(parent, event, action_catalog=actions, author=lambda request: pytest.fail("No next author needed"), evidence_registry=evidence, independent_question=None, incremental_gain=None)
    assert result["status"] == "completed"
    assert result["completion_reason"] == "no_independent_next_question"
    assert result["output_state"] == parent["output_state"]


def make_child():
    parent, event, evidence, actions = recursive_fixture()
    child = recursion.execute_recursive_step(parent, event, action_catalog=actions, author=lambda request: {"possible_choice_ids": ["CHEAP"]}, evidence_registry=evidence, independent_question="Next choices?", incremental_gain="Actual new resources")
    return parent, child, event, evidence, actions


def test_fresh_child_validation_recomputes_state_actions_and_content_binding(tmp_path):
    import json
    parent, child, event, evidence, actions = make_child()
    path = tmp_path / "recursive-state.json"
    path.write_text(json.dumps(child), encoding="utf-8")
    reread = json.loads(path.read_text(encoding="utf-8"))
    assert recursion.validate_registered_child(reread, parent=parent, event=event, action_catalog=actions, evidence_registry=evidence)["order"] == 2
    reread["input_state"]["objects"][0]["variables"][0]["value"] = 10
    with pytest.raises(recursion.RecursiveInferenceError, match="state"):
        recursion.validate_registered_child(reread, parent=parent, event=event, action_catalog=actions, evidence_registry=evidence)


@pytest.mark.parametrize("mutation", ["unknown_content", "loss_removed", "residual_removed", "evidence_upgrade", "observed_upgrade", "parent_cycle", "model_changed", "request_stale"])
def test_child_cannot_erase_or_upgrade_inherited_responsibility(mutation):
    parent, child, event, evidence, actions = make_child()
    if mutation == "unknown_content": parent["output_state"]["unknowns"][0]["content"] = "changed under same ID"
    if mutation == "loss_removed": child["output_state"]["losses"] = []
    if mutation == "residual_removed": child["output_state"]["residuals"] = []
    if mutation == "evidence_upgrade": child["declared_evidence_grade"] = "high"
    if mutation == "observed_upgrade": child["evidence_identity"] = "observed"
    if mutation == "parent_cycle": child["node_id"] = parent["node_id"]
    if mutation == "model_changed": child["model_version"] = "new-model"
    if mutation == "request_stale": child["author_request"]["input_state"] = parent["output_state"]
    with pytest.raises(recursion.RecursiveInferenceError):
        recursion.validate_registered_child(child, parent=parent, event=event, action_catalog=actions, evidence_registry=evidence)


def test_no_action_baseline_does_not_erase_existing_obligations_or_choose_for_actor():
    parent, event, evidence, actions = recursive_fixture()
    child = recursion.execute_recursive_step(parent, event, action_catalog=actions, author=lambda request: {"possible_choice_ids": ["WAIT"], "choice_basis": "conditional no new action"}, evidence_registry=evidence, independent_question="Available choices?", incremental_gain="New resources")
    assert child["author_request"]["no_action_option_id"] == "WAIT"
    assert child["output_state"]["existing_obligations"] == parent["output_state"]["existing_obligations"]
    assert "selected_action" not in child
    with pytest.raises(recursion.RecursiveInferenceError, match="no_action"):
        recursion.current_action_set(parent["output_state"], [*actions, deepcopy(actions[0]) | {"option_id": "WAIT-2"}])
