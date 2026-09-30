"""Strong governance qualification separated from ordinary procedural value."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .canonical_json import sha256_json
from .causality import claim_support


class GovernanceError(ValueError):
    """Governance inputs lack traceable independent responsibilities."""


GOVERNANCE_STEPS = {"issue_registration", "material_disclosure", "affected_object_identification", "objection_access", "decision_grade", "minority_preservation", "version_writeback"}
INTEREST_KINDS = {"funding", "evaluation", "identity", "promotion", "control", "commercial"}


def assess_governance_change(
    record: Mapping[str, Any], *, registries: Mapping[str, Any], claim_constraints: Mapping[str, Any]
) -> dict[str, Any]:
    objections = record.get("objections", [])
    if not isinstance(objections, list) or any(not objection.get("objection_id") or not objection.get("reason") or objection.get("disposition") not in {"adopted", "partly_adopted", "rejected", "ignored", "unresolved"} for objection in objections):
        raise GovernanceError("governance must preserve individually reasoned objection dispositions")
    if len({objection["objection_id"] for objection in objections}) != len(objections):
        raise GovernanceError("objection identity must remain unique")
    ordinary = bool(objections) and all(objection["disposition"] not in {"ignored", "unresolved"} for objection in objections)
    result = {"status": "nominal_only", "ordinary_procedure_value": "supported" if ordinary else "unsupported_or_undecided", "permission_effect": "none", "adopted_change_ids": []}
    adopted = [objection for objection in objections if objection["disposition"] in {"adopted", "partly_adopted"}]
    if not adopted:
        return result
    gates = record.get("governance_gate_claim_ids", {})
    if set(gates) != GOVERNANCE_STEPS or any(claim_support(refs, claim_constraints) != "supported" for refs in gates.values()):
        return result
    actors = registries.get("actors", {})
    ids = {record.get("proposer"), record.get("reviewer"), *record.get("decision_members", [])}
    if any(actor not in actors or actors[actor].get("actor_id") != actor for actor in ids):
        raise GovernanceError("governance actors must use canonical registered identities")
    evidence = registries.get("evidence", {})
    if not record.get("verified_evidence_refs") or any(ref not in evidence or evidence[ref].get("evidence_id") != ref or evidence[ref].get("integrity") != "verified" for ref in record["verified_evidence_refs"]):
        return result
    changes = registries.get("version_log", {})
    for objection in adopted:
        change = changes.get(objection.get("change_id"))
        if not isinstance(change, Mapping) or change.get("change_id") != objection.get("change_id") or not objection.get("effect"):
            return result
        if change.get("before_sha256") != sha256_json(change.get("before_content")) or change.get("after_sha256") != sha256_json(change.get("after_content")) or change["before_sha256"] == change["after_sha256"]:
            return result
        if claim_support(change.get("writeback_claim_ids", []), claim_constraints) != "supported" or claim_support(objection.get("effect_claim_ids", []), claim_constraints) != "supported":
            return result
        result["adopted_change_ids"].append(change["change_id"])
    approval = registries.get("approvals", {}).get(record.get("approval_ref"))
    if not isinstance(approval, Mapping) or approval.get("approval_id") != record.get("approval_ref") or not approval.get("source_ref") or approval.get("governance_id") != record.get("governance_id") or set(approval.get("change_ids", [])) != set(result["adopted_change_ids"]) or claim_support(approval.get("basis_claim_ids", []), claim_constraints) != "supported":
        return result
    issuer = approval.get("issuer")
    if issuer not in actors or actors[issuer].get("actor_id") != issuer or issuer in ids or record["reviewer"] == record["proposer"] or record["proposer"] in record["decision_members"]:
        return result
    if len(result["adopted_change_ids"]) == 1 and approval.get("content_sha256") != changes[result["adopted_change_ids"][0]]["after_sha256"]:
        return result
    for actor in {record["reviewer"], *record["decision_members"], issuer}:
        relation = registries.get("interests", {}).get((actor, record["proposer"]))
        if not isinstance(relation, Mapping) or relation.get("actors") != [actor, record["proposer"]] or set(relation.get("relationships", {})) != INTEREST_KINDS or any(value != "none_found" for value in relation["relationships"].values()) or claim_support(relation.get("basis_claim_ids", []), claim_constraints) != "supported":
            return result
    rejected_ids = {objection["objection_id"] for objection in objections if objection["disposition"] == "rejected"}
    if rejected_ids - set(record.get("minority_objection_ids", [])):
        return result
    if any(objection["disposition"] in {"ignored", "unresolved"} for objection in objections):
        return result
    result["status"] = "applied"
    return result


__all__ = ("GovernanceError", "assess_governance_change")
