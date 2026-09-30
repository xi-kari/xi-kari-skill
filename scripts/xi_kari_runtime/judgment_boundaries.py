"""Human-variable ceilings and scoped use of protected professional materials."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .causality import claim_support
from .problem_contract import parse_instant


class BoundaryError(ValueError):
    """A judgment exceeds its registered route or permitted material use."""


def assess_hv_route(
    record: Mapping[str, Any], *, claim_constraints: Mapping[str, Any],
    formal_results: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    concept, route = record.get("concept_id"), record.get("route")
    if concept not in {"HV09", "HV11"} or route not in {"R0", "R1", "R2"}:
        raise BoundaryError("human-variable route is not registered")
    def root(field: str, expected: str) -> bool:
        instance = formal_results.get(record.get(field), {})
        return instance.get("instance_family") == expected and instance.get("qualification") == "qualified" and instance.get("formal_result") == "supported"
    if concept == "HV09":
        if any(not record.get(field) for field in ("task_type", "window", "position")):
            raise BoundaryError("HV09 description requires matching type, window and position")
        supported = claim_support(record.get("measurement_claim_ids", []), claim_constraints) == "supported"
        ceiling = "load_description"
        if route in {"R1", "R2"}:
            supported = supported and root("g2_instance_id", "G2") and root("cm_load_instance_id", "CM-LOAD")
            ceiling = "specified_load_effect"
        if route == "R2":
            supported = supported and root("g3_instance_id", "G3")
            ceiling = "registered_historical_load_effect"
    else:
        components = record.get("component_claim_ids", {})
        required = {"cost", "direction", "alternatives", "consequence"}
        if route == "R1":
            required |= {"voluntary", "refusal", "exit"}
        supported = all(claim_support(components.get(key, []), claim_constraints) == "supported" for key in required)
        ceiling = "candidate_cost_direction_risk" if route == "R0" else "voluntary_action_description" if route == "R1" else "specified_structural_effect"
        if route == "R2":
            supported = root("g2_instance_id", "G2")
    return {"concept_id": concept, "route": route, "result": "supported" if supported else "unsupported_or_undecided", "ceiling": ceiling, "causal_effect": "supported" if supported and ((concept == "HV09" and route in {"R1", "R2"}) or (concept == "HV11" and route == "R2")) else "unsupported_or_undecided", "permission_effect": "none", "personality_or_love_diagnosis": "prohibited", "ordinary_domain_value": "independently_assessed"}


def validate_professional_reference(
    record: Mapping[str, Any], *, source_registry: Mapping[str, Mapping[str, Any]],
    permission_registry: Mapping[str, Mapping[str, Any]], claim_constraints: Mapping[str, Any],
) -> dict[str, Any]:
    if any(not isinstance(record.get(field), str) or not record[field].strip() for field in ("reference_id", "source_ref", "permission_ref", "purpose", "scope", "visibility")):
        raise BoundaryError("professional reference requires an explicit source, purpose, scope and permitted use")
    forbidden = {"diagnose_personality_essence", "discriminatory_screening", "unauthorized_risk_scoring", "clinical_diagnosis_by_framework", "infer_recovered_memory"}
    if record.get("purpose") in forbidden:
        raise BoundaryError("framework cannot generate or expand a clinical or personality diagnosis")
    source = source_registry.get(record.get("source_ref"))
    permission = permission_registry.get(record.get("permission_ref"))
    if not isinstance(source, Mapping) or source.get("source_id") != record.get("source_ref") or source.get("record_kind") != "existing_professional_diagnosis" or not isinstance(permission, Mapping) or permission.get("permission_id") != record.get("permission_ref"):
        raise BoundaryError("professional reference requires a resolving existing source and permission")
    if source.get("scope") != record.get("scope") or any(permission.get(field) != record.get(field) for field in ("purpose", "scope", "source_ref")):
        raise BoundaryError("professional reference exceeds its permitted original purpose or scope")
    if claim_support(source.get("qualification_claim_ids", []), claim_constraints) != "supported" or claim_support(permission.get("basis_claim_ids", []), claim_constraints) != "supported":
        raise BoundaryError("professional source or permission lacks adequate support")
    if record.get("visibility") not in {"public", "withheld_for_protection"} or (record["visibility"] == "withheld_for_protection" and not source.get("trusted_verifier_ref")):
        raise BoundaryError("professional reference lacks a safe scoped verification path")
    return {"reference_id": record["reference_id"] if record["visibility"] == "public" else "protected_reference", "status": "bounded_external_reference", "visibility": record["visibility"], "purpose_status": "within_registered_scope", "framework_diagnosis": "prohibited", "permission_effect": "none"}


def assess_action_chain(
    events: list[Mapping[str, Any]], *, evidence_registry: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    names = ("suggestion", "tool_request", "application_execution", "external_state", "consequences")
    statuses = {name: "not_evaluated" for name in names}
    seen, previous = set(), None
    for event in events:
        stage = event.get("stage")
        if stage not in statuses or stage in seen or not event.get("event_id"):
            raise BoundaryError("action chain stages must have distinct registered events")
        seen.add(stage)
        at = parse_instant(event["occurred_at"], field="action-chain event time")
        if previous is not None and at < previous:
            raise BoundaryError("action chain event times do not preserve order")
        previous = at
        refs = event.get("evidence_refs", [])
        statuses[stage] = "supported" if refs else "unsupported_or_undecided"
        for ref in refs:
            evidence = evidence_registry.get(ref)
            if not isinstance(evidence, Mapping) or evidence.get("evidence_id") != ref or evidence.get("event_id") != event["event_id"] or evidence.get("stage") != stage or evidence.get("identity") != "observed" or not evidence.get("source_refs"):
                statuses[stage] = "unsupported_or_undecided"
    return {"stages": statuses, "permission_effect": "none", "causal_attribution": "independently_assessed"}


def assess_correction_endpoints(record: Mapping[str, Any], *, claim_constraints: Mapping[str, Any]) -> dict[str, str]:
    return {name: claim_support(record.get(field, []), claim_constraints) for name, field in (("safe_hearing", "safe_hearing_claim_ids"), ("evidence_understood", "evidence_understood_claim_ids"), ("authorized_decision_changed", "authorized_decision_changed_claim_ids"), ("resources_restored", "resources_restored_claim_ids"))}


def assess_protected_opacity(
    record: Mapping[str, Any], *, claim_constraints: Mapping[str, Any], evaluated_at: str
) -> dict[str, Any]:
    questions_complete = all(record.get(field) for field in ("protected_positions", "beneficiaries", "independent_verifier_ref", "review_at", "release_conditions"))
    justification = claim_support(record.get("justification_claim_ids", []), claim_constraints)
    if not questions_complete:
        justification = "unsupported_or_undecided"
    due = parse_instant(record["review_at"], field="protected review date") <= parse_instant(evaluated_at, field="protection evaluation") if record.get("review_at") else True
    return {"justification": justification, "suppression": claim_support(record.get("suppression_claim_ids", []), claim_constraints), "review_due": due, "automatic_disclosure": False, "publication_state": "protected_pending_scoped_review"}


def assess_oversight(record: Mapping[str, Any], *, claim_constraints: Mapping[str, Any]) -> dict[str, Any]:
    required = {"evidence_visible", "counterevidence_visible", "uncertainty_visible", "competence", "available_time", "manageable_workload", "reject_modify_pause_power"}
    conditions = record.get("condition_claim_ids", {})
    if not isinstance(conditions, Mapping) or set(conditions) != required:
        raise BoundaryError("supervision requires separately evidenced visibility, capability, time and power")
    passed = all(claim_support(refs, claim_constraints) == "supported" for refs in conditions.values())
    receipt = record.get("executor_effect_receipt", {})
    effective = passed and receipt.get("selection_id") == record.get("selection_id") and claim_support(receipt.get("effect_claim_ids", []), claim_constraints) == "supported"
    if effective:
        effective = parse_instant(receipt["signal_received_at"], field="supervision signal arrival") < parse_instant(receipt["irreversible_action_at"], field="irreversible action time")
    return {"conditions_supported": passed, "effective_for_registered_action": effective, "retroactive_protection": False, "permission_effect": "none"}


COMPLIANCE_SIGNALS = (
    "single_source", "counterevidence_dismissed", "open_assertion_labelled", "appeal_never_changes_result",
    "reviewers_same_control_chain", "ai_without_external_verification", "diagnosis_excuses_inaction",
    "structural_language_excuses_inaction", "love_mission_professional_cost_extraction", "appellant_pathologized",
)


def assess_compliance_risk(record: Mapping[str, Any], *, claim_constraints: Mapping[str, Any]) -> dict[str, Any]:
    signals = record.get("signals", [])
    if not isinstance(signals, list) or len(signals) != 10 or {signal.get("signal_id") for signal in signals} != set(COMPLIANCE_SIGNALS) or any(signal.get("status") not in {"present", "absent", "unknown"} for signal in signals):
        raise BoundaryError("compliance audit requires all ten unique scoped signal checks")
    if any(not record.get(field) for field in ("dependency_notes", "false_positive_costs", "false_negative_costs", "context")):
        raise BoundaryError("compliance audit must retain dependence, context and error costs")
    count = sum(signal["status"] == "present" and claim_support(signal.get("basis_claim_ids", []), claim_constraints) == "supported" for signal in signals)
    return {"present_supported_count": count, "strong_judgment_blocked": count >= 3, "high_risk": count >= 5, "threshold_type": "procedural", "malicious_intent": "not_established", "calibrated_probability": None, "permission_effect": "none"}


__all__ = ("BoundaryError", "assess_hv_route", "validate_professional_reference", "assess_action_chain", "assess_correction_endpoints", "assess_protected_opacity", "assess_oversight", "COMPLIANCE_SIGNALS", "assess_compliance_risk")
