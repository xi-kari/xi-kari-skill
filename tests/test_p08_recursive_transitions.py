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


def test_four_branch_classes_need_dispositions_but_only_supported_classes_expand():
    dispositions = {
        "main": {"status": "applicable", "reason": "Declared conditional path", "evidence_refs": ["E-SPEND"]},
        "strongest_rival": {"status": "undetermined", "reason": "No discriminating material yet", "evidence_refs": []},
        "low_probability_high_consequence": {"status": "not_applicable", "reason": "No substantive severe route supported", "evidence_refs": []},
        "residual": {"status": "applicable", "reason": "Inherited measured gap", "evidence_refs": ["E-SPEND"]},
    }
    _, _, evidence, _ = recursive_fixture()
    assert recursion.validate_branch_dispositions(dispositions, evidence_registry=evidence) == ("main", "residual")
    dispositions["low_probability_high_consequence"].update(status="applicable", reason="Need a fourth story", evidence_refs=[])
    with pytest.raises(recursion.RecursiveInferenceError, match="evidence"):
        recursion.validate_branch_dispositions(dispositions, evidence_registry=evidence)


def test_low_probability_alone_cannot_prune_supported_severe_path():
    branch = {"branch_id": "SEVERE-1", "harm_level": "high", "probability_mass": {"kind": "unknown", "reason": "No reality probability estimate"}, "evidence_refs": ["E-SPEND"]}
    rules = {"RULE-1": {"rule_id": "RULE-1", "frozen_at": "2026-09-29T00:00:00Z", "allowed_reasons": ["dominated", "low_probability"]}}
    with pytest.raises(recursion.RecursiveInferenceError, match="high"):
        recursion.record_pruned_branch(branch, rule_id="RULE-1", reason="low_probability", evaluated_at="2026-09-30T00:00:00Z", pruning_rules=rules)
    retained = recursion.record_pruned_branch(branch, rule_id="RULE-1", reason="dominated", evaluated_at="2026-09-30T00:00:00Z", pruning_rules=rules)
    assert retained["probability_mass"]["kind"] == "unknown"
    assert retained["branch_id"] == "SEVERE-1"


def test_merge_refuses_different_future_actions_even_with_close_state():
    parent, child, event, evidence, actions = make_child()
    same = deepcopy(child)
    assert recursion.can_merge_recursive_nodes(child, same, tolerances={}) is True
    same["author_request"]["available_actions"] = [same["author_request"]["available_actions"][0]]
    assert recursion.can_merge_recursive_nodes(child, same, tolerances={}) is False
    same = deepcopy(child)
    same["history"].append("different mechanism history")
    assert recursion.can_merge_recursive_nodes(child, same, tolerances={}) is False


def test_failed_parent_records_every_downstream_order_as_not_run():
    parent, event, evidence, actions = recursive_fixture()
    parent.update(status="failed", stop_reason="invalid cross-scale map")
    result = recursion.execute_recursive_step(parent, event, action_catalog=actions, author=lambda request: pytest.fail("dependent author invoked"), evidence_registry=evidence, independent_question="next", incremental_gain="gain")
    assert [item["order"] for item in result["not_run_orders"]] == [2, 3]
    assert all(item["blocked_by_node_id"] == "NODE-1" for item in result["not_run_orders"])


def test_verified_feedback_creates_new_frozen_run_consumed_by_next_author_and_preserves_prediction(tmp_path):
    import json
    parent, prediction, _, _, actions = make_child()
    old = json.dumps(prediction, sort_keys=True).encode()
    old_path = tmp_path / "original-prediction.json"
    old_path.write_bytes(old)
    feedback_event = {"event_id": "OBSERVED-SPEND", "actor_id": "actor", "object_id": "actor", "kind": "observed", "update_path": "observed_direct", "occurrence_status": "occurred", "authorization_status": "unauthorized", "occurred_at": "2026-10-02T10:00:00Z", "evidence_refs": ["E-OBSERVED"], "conditions": [], "deltas": [{"object_id": "actor", "variable_id": "XK-PROV-CASH", "category": "resources", "before": 10, "after": 3, "clock_id": "interaction", "evidence_refs": ["E-OBSERVED"]}], "channel_id": None, "mechanism_id": None, "authorization_ref": None}
    evidence = {"E-OBSERVED": {"evidence_id": "E-OBSERVED", "identity": "observed", "source_refs": ["SYNTHETIC-FEEDBACK"], "available_at": "2026-10-02T11:00:00Z", "event_id": "OBSERVED-SPEND", "object_id": "actor", "variable_id": "XK-PROV-CASH", "observed_value": 3}}
    feedback = {"feedback_id": "FEEDBACK-1", "category": "external_change", "event_id": "OBSERVED-SPEND", "prediction_node_id": prediction["node_id"], "source_refs": ["SYNTHETIC-FEEDBACK"], "observed_event": feedback_event}
    requests = []
    update = recursion.apply_verified_feedback(prediction, parent["output_state"], feedback, new_run_id="RUN-UPDATED", new_evidence_cutoff="2026-10-02T12:00:00Z", action_catalog=actions, evidence_registry=evidence, author=lambda request: requests.append(deepcopy(request)) or {"possible_choice_ids": ["CHEAP"]}, competing_predictions=[parent], simple_baseline=parent)
    assert old_path.read_bytes() == old
    assert json.dumps(prediction, sort_keys=True).encode() == old
    assert update["run_id"] == "RUN-UPDATED"
    assert requests[0]["input_state"]["objects"][0]["variables"][0]["value"] == 3
    assert update["corrective_update_consumed"] is True
    assert update["general_learning_claim"] is False
    assert update["feedback_records"][0]["feedback_id"] == "FEEDBACK-1"
    assert update["original_prediction_sha256"] == world_volume._canonical_sha256(prediction)
    with pytest.raises(recursion.RecursiveInferenceError, match="new"):
        recursion.apply_verified_feedback(prediction, parent["output_state"], feedback, new_run_id=prediction["run_id"], new_evidence_cutoff="2026-10-02T12:00:00Z", action_catalog=actions, evidence_registry=evidence, author=lambda request: {}, competing_predictions=[parent], simple_baseline=parent)


def test_legal_terminal_node_does_not_become_its_own_parent():
    parent, event, evidence, actions = recursive_fixture()
    terminal = recursion.execute_recursive_step(parent, event, action_catalog=actions, author=lambda request: pytest.fail("No independent next question"), evidence_registry=evidence, independent_question=None, incremental_gain=None)
    assert terminal.get("parent_binding", {}).get("node_id") != terminal["node_id"]
    assert terminal["completion_binding"]["node_id"] == parent["node_id"]


def test_third_order_stop_never_creates_a_fourth_order_record():
    parent, event, evidence, actions = recursive_fixture()
    parent.update(order=3, status="failed", stop_reason="third-order mechanism failed")
    terminal = recursion.execute_recursive_step(parent, event, action_catalog=actions, author=lambda request: pytest.fail("Fourth order author invoked"), evidence_registry=evidence, independent_question="next", incremental_gain="conditional change")
    assert terminal["order"] == 3
    assert terminal["status"] == "stopped"
    assert terminal["not_run_orders"] == []
