from importlib import import_module
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def test_hv09_description_and_hv11_voluntary_description_do_not_require_causal_roots():
    boundaries = import_module("xi_kari_runtime.judgment_boundaries")
    constraints = {name: {"blocked": False} for name in ("typed-load", "cost", "direction", "alternatives", "consequence", "voluntary", "refusal", "exit")}
    load = {"concept_id": "HV09", "route": "R0", "task_type": "synthetic-load", "window": "January", "position": "service-worker", "measurement_claim_ids": ["typed-load"]}
    result = boundaries.assess_hv_route(load, claim_constraints=constraints, formal_results={})
    assert result["result"] == "supported"
    assert result["ceiling"] == "load_description"
    action = {"concept_id": "HV11", "route": "R1", "component_claim_ids": {key: [key] for key in ("cost", "direction", "alternatives", "consequence", "voluntary", "refusal", "exit")}}
    result = boundaries.assess_hv_route(action, claim_constraints=constraints, formal_results={})
    assert result["ceiling"] == "voluntary_action_description"
    assert result["causal_effect"] == "unsupported_or_undecided"
    assert result["permission_effect"] == "none"
    assert result["personality_or_love_diagnosis"] == "prohibited"


def test_protected_professional_reference_does_not_leak_private_diagnosis_or_expand_purpose():
    boundaries = import_module("xi_kari_runtime.judgment_boundaries")
    secret = "SYNTHETIC-PRIVATE-DIAGNOSIS-RAW-VALUE"
    record = {"reference_id": "clinical-reference", "source_ref": "professional-record", "permission_ref": "limited-consent", "purpose": "support-discussion", "scope": "provided-record-only", "visibility": "withheld_for_protection", "raw_value": secret}
    sources = {"professional-record": {"source_id": "professional-record", "record_kind": "existing_professional_diagnosis", "scope": "provided-record-only", "qualification_claim_ids": ["professional-source"], "trusted_verifier_ref": "reviewer"}}
    permissions = {"limited-consent": {"permission_id": "limited-consent", "purpose": "support-discussion", "scope": "provided-record-only", "source_ref": "professional-record", "basis_claim_ids": ["consent"]}}
    kwargs = dict(source_registry=sources, permission_registry=permissions, claim_constraints={ref: {"blocked": False} for ref in ("professional-source", "consent")})
    result = boundaries.validate_professional_reference(record, **kwargs)
    assert secret not in str(result)
    record["purpose"] = "diagnose_personality_essence"
    with pytest.raises(boundaries.BoundaryError) as error:
        boundaries.validate_professional_reference(record, **kwargs)
    assert secret not in str(error.value)
    assert error.value.__cause__ is None


def test_application_success_does_not_prove_external_copies_or_consequences():
    boundaries = import_module("xi_kari_runtime.judgment_boundaries")
    events = [{"event_id": "request-1", "stage": "tool_request", "occurred_at": "2026-01-01T00:00:00Z", "evidence_refs": ["request-log"]}, {"event_id": "execution-1", "stage": "application_execution", "occurred_at": "2026-01-01T00:00:01Z", "evidence_refs": ["success-response"]}]
    evidence = {ref: {"evidence_id": ref, "identity": "observed", "event_id": event["event_id"], "stage": event["stage"], "source_refs": ["SYNTHETIC-HOST-FIXTURE"]} for event, ref in zip(events, ("request-log", "success-response"))}
    result = boundaries.assess_action_chain(events, evidence_registry=evidence)
    assert result["stages"]["application_execution"] == "supported"
    assert result["stages"]["external_state"] == result["stages"]["consequences"] == "not_evaluated"
    assert result["permission_effect"] == "none"


def test_corrective_hearing_and_understanding_cannot_close_resource_remedy():
    boundaries = import_module("xi_kari_runtime.judgment_boundaries")
    record = {"safe_hearing_claim_ids": ["heard"], "evidence_understood_claim_ids": ["understood"], "authorized_decision_changed_claim_ids": [], "resources_restored_claim_ids": []}
    result = boundaries.assess_correction_endpoints(record, claim_constraints={ref: {"blocked": False} for ref in ("heard", "understood")})
    assert result["safe_hearing"] == result["evidence_understood"] == "supported"
    assert result["authorized_decision_changed"] == result["resources_restored"] == "unsupported_or_undecided"


def test_protection_review_expiry_never_automatically_releases_private_value():
    boundaries = import_module("xi_kari_runtime.judgment_boundaries")
    result = boundaries.assess_protected_opacity({"protected_positions": ["patient"], "beneficiaries": ["patient"], "independent_verifier_ref": "reviewer", "review_at": "2026-01-01T00:00:00Z", "release_conditions": ["new-safe-review"], "justification_claim_ids": [], "suppression_claim_ids": [], "raw_value": "SYNTHETIC-PRIVATE-VALUE"}, claim_constraints={}, evaluated_at="2026-02-01T00:00:00Z")
    assert result["justification"] == "unsupported_or_undecided"
    assert result["suppression"] == "unsupported_or_undecided"
    assert result["review_due"] is True
    assert result["automatic_disclosure"] is False
    assert "SYNTHETIC-PRIVATE-VALUE" not in str(result)


def test_late_supervision_cannot_retroactively_protect_an_irreversible_action():
    boundaries = import_module("xi_kari_runtime.judgment_boundaries")
    conditions = ("evidence_visible", "counterevidence_visible", "uncertainty_visible", "competence", "available_time", "manageable_workload", "reject_modify_pause_power")
    record = {"selection_id": "synthetic-action", "condition_claim_ids": {key: ["oversight-condition"] for key in conditions}, "executor_effect_receipt": {"selection_id": "synthetic-action", "signal_received_at": "2026-01-01T00:00:02Z", "irreversible_action_at": "2026-01-01T00:00:01Z", "effect_claim_ids": ["actual-effect"]}}
    support = {ref: {"blocked": False} for ref in ("oversight-condition", "actual-effect")}
    assert boundaries.assess_oversight(record, claim_constraints=support)["effective_for_registered_action"] is False
    record["executor_effect_receipt"]["signal_received_at"] = "2026-01-01T00:00:00Z"
    assert boundaries.assess_oversight(record, claim_constraints=support)["effective_for_registered_action"] is True


def test_three_and_five_signals_are_procedural_gates_and_never_malice_probability():
    boundaries = import_module("xi_kari_runtime.judgment_boundaries")
    signals = [{"signal_id": identifier, "status": "present" if index < 3 else "absent", "basis_claim_ids": ["signal-material"]} for index, identifier in enumerate(boundaries.COMPLIANCE_SIGNALS)]
    record = {"signals": signals, "dependency_notes": ["Several signals share one control chain"], "false_positive_costs": ["unnecessary pause"], "false_negative_costs": ["unprotected user"], "context": "synthetic-audit"}
    support = {"signal-material": {"blocked": False}}
    result = boundaries.assess_compliance_risk(record, claim_constraints=support)
    assert result["strong_judgment_blocked"] is True
    assert result["high_risk"] is False
    record["signals"][3]["status"] = record["signals"][4]["status"] = "present"
    result = boundaries.assess_compliance_risk(record, claim_constraints=support)
    assert result["high_risk"] is True
    assert result["malicious_intent"] == "not_established"
    assert result["calibrated_probability"] is None


def test_professional_reference_requires_an_explicit_original_purpose():
    boundaries = import_module("xi_kari_runtime.judgment_boundaries")
    record = {"reference_id": "ref", "source_ref": "source", "permission_ref": "permission", "purpose": None, "scope": "bounded-record", "visibility": "public"}
    sources = {"source": {"source_id": "source", "record_kind": "existing_professional_diagnosis", "scope": "bounded-record", "qualification_claim_ids": ["qualified-source"]}}
    permissions = {"permission": {"permission_id": "permission", "source_ref": "source", "purpose": None, "scope": "bounded-record", "basis_claim_ids": ["consent"]}}
    with pytest.raises(boundaries.BoundaryError):
        boundaries.validate_professional_reference(record, source_registry=sources, permission_registry=permissions, claim_constraints={ref: {"blocked": False} for ref in ("qualified-source", "consent")})
