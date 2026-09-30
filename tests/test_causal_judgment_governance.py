from copy import deepcopy
from importlib import import_module
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from xi_kari_runtime.canonical_json import sha256_json


def governance_inputs():
    before, after = {"action_ceiling": "execute"}, {"action_ceiling": "deliberation_only"}
    change = {"change_id": "change-1", "before_content": before, "after_content": after, "before_sha256": sha256_json(before), "after_sha256": sha256_json(after), "writeback_claim_ids": ["adopted-change"]}
    steps = ("issue_registration", "material_disclosure", "affected_object_identification", "objection_access", "decision_grade", "minority_preservation", "version_writeback")
    record = {"governance_id": "synthetic-governance", "proposer": "proposer", "reviewer": "reviewer", "decision_members": ["member"], "approval_ref": "approval-1", "objections": [{"objection_id": "objection-1", "disposition": "adopted", "reason": "Reduce unsupported action scope", "effect": "action ceiling narrowed", "change_id": "change-1", "effect_claim_ids": ["adopted-change"]}], "governance_gate_claim_ids": {step: ["procedure"] for step in steps}, "verified_evidence_refs": ["E-procedure", "E-change"], "minority_objection_ids": []}
    registries = {"version_log": {"change-1": change}, "actors": {actor: {"actor_id": actor} for actor in ("proposer", "reviewer", "member", "issuer")}, "evidence": {ref: {"evidence_id": ref, "integrity": "verified"} for ref in record["verified_evidence_refs"]}, "approvals": {"approval-1": {"approval_id": "approval-1", "issuer": "issuer", "source_ref": "SYNTHETIC-EXTERNAL-APPROVAL", "governance_id": record["governance_id"], "change_ids": ["change-1"], "content_sha256": change["after_sha256"], "basis_claim_ids": ["approval"]}}, "interests": {(actor, "proposer"): {"actors": [actor, "proposer"], "relationships": {key: "none_found" for key in ("funding", "evaluation", "identity", "promotion", "control", "commercial")}, "basis_claim_ids": ["independence"]} for actor in ("reviewer", "member", "issuer")}}
    constraints = {ref: {"blocked": False} for ref in ("adopted-change", "procedure", "approval", "independence")}
    return record, registries, constraints


def test_substantive_adoption_needs_actual_version_change_and_independent_external_approval():
    governance = import_module("xi_kari_runtime.governance")
    record, registries, constraints = governance_inputs()
    result = governance.assess_governance_change(record, registries=registries, claim_constraints=constraints)
    assert result["status"] == "applied"
    assert result["permission_effect"] == "none"
    record["objections"][0]["disposition"] = "rejected"
    record["objections"][0]["reason"] = "Reasoned response under the ordinary procedure"
    result = governance.assess_governance_change(record, registries=registries, claim_constraints=constraints)
    assert result["ordinary_procedure_value"] == "supported"
    assert result["status"] == "nominal_only"


@pytest.mark.parametrize("change", ["ghost-change", "unchanged-content", "self-approval", "unverified-evidence", "interest-conflict", "unresolved-objection", "wrong-approval-content"])
def test_adoption_marker_cannot_replace_the_original_governance_gates(change):
    governance = import_module("xi_kari_runtime.governance")
    record, registries, constraints = governance_inputs()
    if change == "ghost-change": record["objections"][0]["change_id"] = "missing-change"
    elif change == "unchanged-content":
        item = registries["version_log"]["change-1"]
        item["after_content"] = item["before_content"]
        item["after_sha256"] = item["before_sha256"]
    elif change == "self-approval": registries["approvals"]["approval-1"]["issuer"] = "proposer"
    elif change == "unverified-evidence": registries["evidence"]["E-procedure"]["integrity"] = "unverified"
    elif change == "interest-conflict": registries["interests"][("reviewer", "proposer")]["relationships"]["control"] = "same-control-chain"
    elif change == "unresolved-objection": record["objections"].append({"objection_id": "minority", "disposition": "unresolved", "reason": "Needs protected independent review"})
    else: registries["approvals"]["approval-1"]["content_sha256"] = "e" * 64
    assert governance.assess_governance_change(record, registries=registries, claim_constraints=constraints)["status"] == "nominal_only"
