from copy import deepcopy
from importlib import import_module
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def comparison_inputs():
    state = {"available_actions": [{"option_id": "WAIT", "option_kind": "no_action", "action_type": "no_new_action", "target_object": "synthetic-object"}, {"option_id": "PILOT", "option_kind": "external_action", "action_type": "reversible-pilot", "target_object": "synthetic-object"}], "no_action_option_id": "WAIT", "existing_obligations": [{"obligation_id": "maintenance", "condition": "existing-valid-duty", "scope": "synthetic-object"}]}
    record = {"comparison_id": "synthetic-choice-1", "scope": {"object_id": "synthetic-object", "window": "October"}, "options": deepcopy(state["available_actions"]), "no_action_option_id": "WAIT", "existing_items": deepcopy(state["existing_obligations"]), "recommended_option_id": "WAIT", "selection_status": "recommended", "execution_status": "analysis_only", "normative_premises": ["N2"], "normative_basis_claim_ids": ["premise"], "affected_positions": ["service-users"], "cost_distribution": [{"position": "service-users", "cost": "ongoing-delay"}], "reasons": ["limited-evidence-of-pilot-net-benefit"], "counterarguments": ["continued-delay-costs"], "switch_conditions": ["better-evidence"], "baseline_time": "2026-09-30T00:00:00Z", "natural_changes": ["continuing-demand"], "observation_plan": ["monitor-delay"], "reopen_conditions": ["safety-trigger"], "responsible_subject": "synthetic-committee"}
    return state, record


def test_recommended_no_action_retains_existing_duties_without_execution_permission():
    choice = import_module("xi_kari_runtime.choice")
    state, record = comparison_inputs()
    result = choice.validate_action_comparison(record, action_state=state, claim_constraints={"premise": {"blocked": False}})
    assert result["recommended_option_id"] == "WAIT"
    assert result["permission_effect"] == "none"
    assert result["existing_items"] == state["existing_obligations"]
    record["existing_items"] = []
    with pytest.raises(choice.ChoiceError, match="existing"):
        choice.validate_action_comparison(record, action_state=state, claim_constraints={"premise": {"blocked": False}})


def test_actual_no_new_action_decision_requires_observed_decision_evidence():
    choice = import_module("xi_kari_runtime.choice")
    _, comparison = comparison_inputs()
    record = {"subject": "synthetic-committee", "scope": comparison["scope"], "chosen_baseline": "WAIT", "evidence_refs": ["decision-minutes"], "existing_items": comparison["existing_items"], "permission_effect": "none"}
    evidence = {"decision-minutes": {"evidence_id": "decision-minutes", "identity": "observed", "decision_subject": "synthetic-committee", "scope": comparison["scope"], "chosen_baseline": "WAIT", "source_refs": ["SYNTHETIC-UNIT-FIXTURE"]}}
    result = choice.validate_no_new_action_choice(record, comparison=comparison, decision_evidence_registry=evidence)
    assert result["permission_effect"] == "none"
    evidence["decision-minutes"]["identity"] = "model-candidate"
    with pytest.raises(choice.ChoiceError, match="decision evidence"):
        choice.validate_no_new_action_choice(record, comparison=comparison, decision_evidence_registry=evidence)


def authorization_inputs():
    state, comparison = comparison_inputs()
    option = comparison["options"][1]
    interval = {"starts_at": "2026-09-30T00:00:00Z", "ends_at": "2026-10-30T00:00:00Z"}
    option.update(decision_subject="actor-holder", territory="registered-team", validity_interval=interval)
    atom = {"tuple_id": "J-1", "source_ref": "external-grant", "issuer": "actor-issuer", "decision_subject": "actor-holder", "target_object": "synthetic-object", "single_action": "reversible-pilot", "territory": "registered-team", "validity_interval": interval, "status": "valid", "revoked_at": None, "basis_claim_ids": ["grant"]}
    mechanism_types = ("stop", "safe_submission", "anti_retaliation", "appeal", "independent_review", "rollback", "remedy", "residual_harm_tracking", "version_writeback", "expiry")
    mechanisms = {kind: {"mechanism_id": kind, "kind": kind, "owner": "actor-reviewer" if kind == "independent_review" else "actor-holder", "operability_claim_ids": ["control"], "expires_at": interval["ends_at"]} for kind in mechanism_types}
    record = {"selection_id": "synthetic-selection", "selection_type": "SEL-GOV", "proposer": "actor-proposer", "selected_option_id": "PILOT", "authorization_tuple_id": "J-1", "normative_premises": ["N2", "N4"], "normative_basis_claim_ids": ["premise"], "value_conflicts": [], "objections": [], "affected_positions": ["service-users"], "low_power_positions": ["service-users"], "rights_floor": [f"PF-{i}" for i in range(1, 11)],
        "protection_floor_bindings": [{"pf_id": f"PF-{i}", "status": "active", "check_status": "passed", "reason": "synthetic protection fixture", "basis_claim_ids": ["protection"], "mechanism_refs": list(mechanisms), "mechanism_bindings": [{"mechanism_ref": kind, "responsible_subject": "actor-reviewer" if kind == "independent_review" else "actor-holder"} for kind in mechanism_types], "expires_at": interval["ends_at"]} for i in range(1, 11)],
        "coercion_and_choice": {name: {"status": "passed", "basis_claim_ids": ["choice"]} for name in ("no_coercion", "no_default_lock", "understandable_information", "decision_capacity", "safe_refusal", "real_exit")},
        "minimum_harm": {"selected": True, "reason": "bounded pilot", "basis_claim_ids": ["review"]}, "proportionality": {"selected": True, "reason": "limited cost", "basis_claim_ids": ["review"]}, "independent_review_ref": "review-1",
        "O_records": {f"O{i}": {"record_id": f"O{i}-1", "comparison_id": comparison["comparison_id"], "selected_option_id": "PILOT", "authorization_tuple_id": "J-1", "basis_claim_ids": ["procedure"], "previous_record_ref": f"O{i-1}-1" if i > 1 else None} for i in range(1, 5)}, "control_mechanism_refs": list(mechanisms)}
    review = {"review-1": {"review_id": "review-1", "reviewer": "actor-reviewer", "selection_id": record["selection_id"], "basis_claim_ids": ["review"]}}
    actors = {actor: {"actor_id": actor} for actor in ("actor-holder", "actor-issuer", "actor-reviewer", "actor-proposer")}
    interests = {(subject, target): {"actors": [subject, target], "relationships": {kind: "none_found" for kind in ("funding", "evaluation", "identity", "promotion", "control", "commercial")}, "basis_claim_ids": ["independence"]} for subject in ("actor-reviewer", "actor-issuer") for target in ("actor-proposer", "actor-holder")}
    kwargs = {"comparison": comparison, "authorization_registry": {"J-1": atom}, "mechanism_registry": mechanisms, "review_registry": review, "actor_registry": actors, "interest_registry": interests, "claim_constraints": {ref: {"blocked": False} for ref in ("grant", "control", "premise", "protection", "choice", "review", "procedure", "independence")}, "used_at": "2026-10-01T00:00:00Z", "outer_impact_domain": "human", "downstream_impact_domain": "human"}
    return record, kwargs


def test_external_selection_requires_one_current_atomic_scope_and_complete_controls():
    choice = import_module("xi_kari_runtime.choice")
    record, kwargs = authorization_inputs()
    result = choice.validate_external_selection(record, **kwargs)
    assert result["status"] == "authorized"
    assert result["selected_action"]["option_id"] == "PILOT"
    record["selected_option_id"] = "WAIT"
    with pytest.raises(choice.ChoiceError, match="external_action"):
        choice.validate_external_selection(record, **kwargs)


@pytest.mark.parametrize("change", ["revoked", "expired", "tuple-mix", "open-objection", "unresolved-conflict", "unknown-protection", "missing-floor", "N1-only", "self-review", "interest-conflict", "missing-O4", "SEL-SYS", "control-expired"])
def test_authorization_gates_cannot_be_offset_by_other_successes(change):
    choice = import_module("xi_kari_runtime.choice")
    record, kwargs = authorization_inputs()
    if change == "revoked": kwargs["authorization_registry"]["J-1"]["revoked_at"] = "2026-09-30T00:00:00Z"
    elif change == "expired": kwargs["used_at"] = "2026-11-01T00:00:00Z"
    elif change == "tuple-mix": kwargs["authorization_registry"]["J-1"]["single_action"] = "read-only"
    elif change == "open-objection": record["objections"] = [{"objection_id": "objection-minority", "status": "protected_and_pending"}]
    elif change == "unresolved-conflict": record["value_conflicts"] = [{"conflict_id": "conflict-1", "status": "unresolved_action_paused"}]
    elif change == "unknown-protection": record["protection_floor_bindings"][0]["check_status"] = "unknown"
    elif change == "missing-floor": record["protection_floor_bindings"].pop()
    elif change == "N1-only": record["normative_premises"] = ["N1"]
    elif change == "self-review": kwargs["review_registry"]["review-1"]["reviewer"] = "actor-proposer"
    elif change == "interest-conflict": kwargs["interest_registry"][("actor-reviewer", "actor-proposer")]["relationships"]["funding"] = "same-sponsor"
    elif change == "missing-O4": record["O_records"].pop("O4")
    elif change == "SEL-SYS": record["selection_type"] = "SEL-SYS"
    else: kwargs["mechanism_registry"]["stop"]["expires_at"] = "2026-09-30T00:00:00Z"
    with pytest.raises(choice.ChoiceError):
        choice.validate_external_selection(record, **kwargs)


def test_stop_actually_reaches_isolated_executor_and_does_not_close_unremedied_harm(tmp_path):
    choice = import_module("xi_kari_runtime.choice")
    artifact = tmp_path / "action-effect.txt"
    executor = choice.IsolatedChoiceExecutor("synthetic-selection", {"PILOT": lambda: artifact.write_text("applied", encoding="utf-8")})
    receipt = executor.stop("protect-before-action", received_at="2026-10-01T00:00:00Z")
    with pytest.raises(choice.ChoiceError, match="stopped"):
        executor.execute("PILOT")
    assert not artifact.exists()
    record = {"selection_id": "synthetic-selection", "status": "authorized", "history": [], "existing_obligations": [{"obligation_id": "remedy"}], "open_harm_ids": ["harm-1"], "open_appeal_ids": [], "open_remedy_ids": ["remedy-1"], "open_record_ids": []}
    stopped = choice.transition_choice_state(record, "stopped", at="2026-10-01T00:00:01Z", responsible_subject="actor-holder", basis_refs=["stop-receipt"], executor_receipt=receipt, executor=executor)
    assert stopped["status"] == "stopped"
    assert stopped["existing_obligations"] == record["existing_obligations"]
    with pytest.raises(choice.ChoiceError, match="open"):
        choice.transition_choice_state(stopped, "closed", at="2026-10-01T00:00:02Z", responsible_subject="actor-holder", basis_refs=["closing-note"])


def test_active_executor_without_fresh_authorizer_and_unknown_transfer_cannot_complete():
    choice = import_module("xi_kari_runtime.choice")
    executed = []
    executor = choice.IsolatedChoiceExecutor("synthetic-selection", {"PILOT": lambda: executed.append("action")})
    with pytest.raises(choice.ChoiceError, match="authorization"):
        executor.execute("PILOT")
    assert executed == []
    record = {"selection_id": "synthetic-selection", "status": "stopped", "history": [], "open_remedy_ids": ["remedy-1"]}
    with pytest.raises(choice.ChoiceError, match="transfer"):
        choice.transition_choice_state(record, "closed", at="2026-10-01T00:00:02Z", responsible_subject="actor-holder", basis_refs=["closing-note"], formal_transfer_refs=["unknown-recipient"])


def test_protection_owner_must_match_the_actual_registered_mechanism():
    choice = import_module("xi_kari_runtime.choice")
    record, kwargs = authorization_inputs()
    record["protection_floor_bindings"][0]["mechanism_bindings"][0]["responsible_subject"] = "actor-issuer"
    with pytest.raises(choice.ChoiceError, match="owner"):
        choice.validate_external_selection(record, **kwargs)


def test_a_json_stop_marker_cannot_replace_the_actual_executor_signal():
    choice = import_module("xi_kari_runtime.choice")
    record = {"selection_id": "synthetic-selection", "status": "authorized", "history": []}
    receipt = {"selection_id": "synthetic-selection", "executor_status": "stopped", "stop_reached_executor": True, "received_at": "2026-10-01T00:00:00Z"}
    with pytest.raises(choice.ChoiceError, match="actual executor"):
        choice.transition_choice_state(record, "stopped", at="2026-10-01T00:00:01Z", responsible_subject="actor-holder", basis_refs=["marker"], executor_receipt=receipt)


def test_rollback_hash_and_reference_labels_do_not_prove_actual_restoration():
    choice = import_module("xi_kari_runtime.choice")
    record = {"selection_id": "synthetic-selection", "status": "stopped", "history": []}
    receipt = {"selection_id": "synthetic-selection", "restored_state_sha256": "a" * 64, "remedy_started_refs": ["fake-start"], "version_writeback_ref": "fake-version"}
    with pytest.raises(choice.ChoiceError, match="actual restoration"):
        choice.transition_choice_state(record, "rolled_back", at="2026-10-01T00:00:01Z", responsible_subject="actor-holder", basis_refs=["marker"], restoration_receipt=receipt)
