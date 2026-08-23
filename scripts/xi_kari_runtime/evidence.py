"""Claim/evidence binding built from separately assessed source records."""

from __future__ import annotations

from copy import deepcopy
from collections.abc import Mapping
from typing import Any

from .retrieval import ADMITTED_ASSESSMENT_VERDICTS, has_bound_host_observation


FACTUAL_KINDS = {
    "external_fact",
    "source_claim",
    "documented_real_case",
    "authorization_boundary",
}
HOST_OBSERVATION_REQUIRED_KINDS = {
    "external_fact",
    "documented_real_case",
}
SUPPORTING_STATUSES = {"supports", "partially_supports"}
EVIDENCE_STATUSES = SUPPORTING_STATUSES | {"refutes", "nonprobative"}
AUTHORIZATION_FIELDS = {
    "decision_subject",
    "target_object",
    "single_action",
    "territory",
    "validity_interval",
}
WORLD_TARGET_RELATIONS = {"descriptive", "authorization"}


def _normalise_world_targets(
    value: Any,
    *,
    claim_id: str,
    target_hashes: Mapping[str, str] | None = None,
) -> list[dict[str, str]]:
    if value is None:
        value = []
    if not isinstance(value, list):
        raise ValueError(f"claim world_targets must be a list: {claim_id}")
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for target in value:
        if not isinstance(target, Mapping):
            raise ValueError(f"claim world target must be an object: {claim_id}")
        allowed = {"target_path", "relation"} | (
            {"target_sha256"} if "target_sha256" in target else set()
        )
        if set(target) != allowed:
            raise ValueError(f"claim world target fields are invalid: {claim_id}")
        path = target.get("target_path")
        relation = target.get("relation")
        if not isinstance(path, str) or not path or relation not in WORLD_TARGET_RELATIONS:
            raise ValueError(f"claim world target identity is invalid: {claim_id}")
        expected_hash = target_hashes.get(path) if target_hashes is not None else None
        observed_hash = target.get("target_sha256")
        if expected_hash is not None:
            if observed_hash is not None and observed_hash != expected_hash:
                raise ValueError(f"claim world target hash differs: {claim_id}:{path}")
            observed_hash = expected_hash
        elif target_hashes is not None:
            raise ValueError(f"claim world target path does not resolve: {claim_id}:{path}")
        if not isinstance(observed_hash, str) or len(observed_hash) != 64:
            raise ValueError(f"claim world target hash is missing: {claim_id}:{path}")
        key = (path, relation)
        if key in seen:
            raise ValueError(f"duplicate claim world target: {claim_id}:{path}")
        seen.add(key)
        result.append(
            {
                "target_path": path,
                "target_sha256": observed_hash,
                "relation": relation,
            }
        )
    return sorted(result, key=lambda item: (item["target_path"], item["relation"]))


def _authorization_boundary(value: Any, *, kind: str, claim_id: str) -> dict[str, Any] | None:
    if kind != "authorization_boundary":
        if value is not None:
            raise ValueError(
                f"non-authorization claim cannot carry authorization_boundary: {claim_id}"
            )
        return None
    if not isinstance(value, Mapping) or set(value) != AUTHORIZATION_FIELDS:
        raise ValueError(
            f"authorization claim requires one atomic authorization_boundary: {claim_id}"
        )
    for field in AUTHORIZATION_FIELDS - {"validity_interval"}:
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise ValueError(
                f"authorization_boundary.{field} must be non-empty: {claim_id}"
            )
    validity = value.get("validity_interval")
    if (
        not isinstance(validity, Mapping)
        or set(validity) != {"starts_at", "ends_at"}
        or any(
            not isinstance(validity.get(field), str) or not validity[field].strip()
            for field in ("starts_at", "ends_at")
        )
    ):
        raise ValueError(
            f"authorization_boundary.validity_interval is incomplete: {claim_id}"
        )
    return deepcopy(dict(value))


def _assessment_verdicts(retrieval_index: dict[str, Any]) -> dict[str, Any]:
    return {
        item.get("source_id"): item.get("assessment_verdict")
        for item in retrieval_index.get("sources", [])
        if isinstance(item, dict)
    }


def _independence_identities(retrieval_index: dict[str, Any]) -> dict[str, str]:
    return {
        item.get("source_id"): item.get("independence_key")
        or item.get("content_sha256")
        or item.get("source_id")
        for item in retrieval_index.get("sources", [])
        if isinstance(item, dict) and isinstance(item.get("source_id"), str)
    }


def _source_records(retrieval_index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["source_id"]: item
        for item in retrieval_index.get("sources", [])
        if isinstance(item, dict) and isinstance(item.get("source_id"), str)
    }


def build_evidence_ledger(
    *,
    run_id: str,
    claims: list[dict[str, Any]],
    retrieval_index: dict[str, Any],
    world_target_hashes: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    source_ids = {item["source_id"] for item in retrieval_index.get("sources", [])}
    source_records = _source_records(retrieval_index)
    assessment_verdicts = _assessment_verdicts(retrieval_index)
    independence_identities = _independence_identities(retrieval_index)
    normalised_claims: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    support_edges: list[dict[str, str]] = []
    unsupported: list[str] = []
    seen_claims: set[str] = set()
    for raw_claim in claims:
        claim_id = raw_claim.get("claim_id")
        text = raw_claim.get("text")
        kind = raw_claim.get("kind")
        if not all(isinstance(value, str) and value for value in (claim_id, text, kind)):
            raise ValueError("each claim requires claim_id, text, and kind")
        if claim_id in seen_claims:
            raise ValueError(f"duplicate claim_id: {claim_id}")
        seen_claims.add(claim_id)
        authorization_boundary = _authorization_boundary(
            raw_claim.get("authorization_boundary"),
            kind=kind,
            claim_id=claim_id,
        )
        world_targets = _normalise_world_targets(
            raw_claim.get("world_targets"),
            claim_id=claim_id,
            target_hashes=world_target_hashes,
        )
        supports = raw_claim.get("support", [])
        if not isinstance(supports, list):
            raise ValueError(f"claim support must be a list: {claim_id}")
        claim_evidence_ids: list[str] = []
        seen_support_identities: set[str] = set()
        for index, support in enumerate(supports, start=1):
            source_id = support.get("source_id")
            if source_id not in source_ids:
                raise ValueError(f"claim {claim_id} names unassessed source: {source_id}")
            evidence_id = f"{claim_id}-e{index}"
            status = support.get("status", "supports")
            if status not in EVIDENCE_STATUSES:
                raise ValueError(f"claim {claim_id} has invalid evidence status: {status}")
            if (
                kind in HOST_OBSERVATION_REQUIRED_KINDS
                and status in SUPPORTING_STATUSES
                and not has_bound_host_observation(source_records[source_id])
            ):
                raise ValueError(
                    "factual support requires a bound host observation: "
                    f"{claim_id} -> {source_id}"
                )
            entry = {
                "evidence_id": evidence_id,
                "claim_id": claim_id,
                "source_id": source_id,
                "status": status,
                "summary": support.get("summary", ""),
                "cannot_prove": list(support.get("cannot_prove", [])),
            }
            evidence.append(entry)
            if (
                status in SUPPORTING_STATUSES
                and assessment_verdicts.get(source_id)
                in ADMITTED_ASSESSMENT_VERDICTS
            ):
                identity = independence_identities[source_id]
                if identity not in seen_support_identities:
                    seen_support_identities.add(identity)
                    claim_evidence_ids.append(evidence_id)
                    support_edges.append(
                        {
                            "claim_id": claim_id,
                            "evidence_id": evidence_id,
                            "source_id": source_id,
                        }
                    )
        if not claim_evidence_ids:
            unsupported.append(claim_id)
        normalised_claims.append(
            {
                "claim_id": claim_id,
                "text": text,
                "kind": kind,
                "evidence_refs": claim_evidence_ids,
                "authorization_boundary": authorization_boundary,
                "world_targets": world_targets,
            }
        )
        if kind in FACTUAL_KINDS and not claim_evidence_ids:
            raise ValueError(
                "factual claim has no assessed source support; "
                f"no admitted supporting evidence: {claim_id}"
            )
    return {
        "schema_id": "xi-kari.v2.evidence-ledger",
        "schema_version": 3,
        "run_id": run_id,
        "claims": normalised_claims,
        "evidence": evidence,
        "support_edges": support_edges,
        "unsupported_claims": unsupported,
    }


def validate_evidence_ledger(
    ledger: dict[str, Any], retrieval_index: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    source_ids = {item.get("source_id") for item in retrieval_index.get("sources", [])}
    source_records = _source_records(retrieval_index)
    assessment_verdicts = _assessment_verdicts(retrieval_index)
    independence_identities = _independence_identities(retrieval_index)
    claims = ledger.get("claims", [])
    evidence = ledger.get("evidence", [])
    edges = ledger.get("support_edges", [])
    if not all(isinstance(values, list) for values in (claims, evidence, edges)):
        return ["evidence ledger claims, evidence, and support_edges must be lists"]
    claim_by_id: dict[str, dict[str, Any]] = {}
    for claim in claims:
        claim_id = claim.get("claim_id") if isinstance(claim, dict) else None
        if not isinstance(claim_id, str) or not claim_id:
            errors.append("evidence ledger contains a claim without claim_id")
            continue
        if claim_id in claim_by_id:
            errors.append(f"duplicate evidence claim_id: {claim_id}")
            continue
        claim_by_id[claim_id] = claim
        try:
            _authorization_boundary(
                claim.get("authorization_boundary"),
                kind=str(claim.get("kind")),
                claim_id=claim_id,
            )
        except ValueError as error:
            errors.append(str(error))
        try:
            _normalise_world_targets(
                claim.get("world_targets"),
                claim_id=claim_id,
            )
        except ValueError as error:
            errors.append(str(error))

    evidence_by_id: dict[str, dict[str, Any]] = {}
    expected_edges: set[tuple[str, str, str]] = set()
    evidence_by_claim: dict[str, list[str]] = {claim_id: [] for claim_id in claim_by_id}
    for entry in evidence:
        evidence_id = entry.get("evidence_id") if isinstance(entry, dict) else None
        claim_id = entry.get("claim_id") if isinstance(entry, dict) else None
        source_id = entry.get("source_id") if isinstance(entry, dict) else None
        if not all(isinstance(value, str) and value for value in (evidence_id, claim_id, source_id)):
            errors.append("evidence entry lacks evidence_id, claim_id, or source_id")
            continue
        if evidence_id in evidence_by_id:
            errors.append(f"duplicate evidence_id: {evidence_id}")
            continue
        evidence_by_id[evidence_id] = entry
        if claim_id not in claim_by_id:
            errors.append(f"evidence has unknown claim: {evidence_id}")
        else:
            evidence_by_claim[claim_id].append(evidence_id)
        if source_id not in source_ids:
            errors.append(f"evidence has unassessed source: {evidence_id}")
        status = entry.get("status")
        if status not in EVIDENCE_STATUSES:
            errors.append(f"evidence has invalid status: {evidence_id}")
        if status in SUPPORTING_STATUSES:
            if assessment_verdicts.get(source_id) not in ADMITTED_ASSESSMENT_VERDICTS:
                errors.append(
                    f"supporting evidence uses a non-admitted assessment: {evidence_id}"
                )
            claim = claim_by_id.get(claim_id)
            if (
                isinstance(claim, dict)
                and claim.get("kind") in HOST_OBSERVATION_REQUIRED_KINDS
                and not has_bound_host_observation(source_records.get(source_id, {}))
            ):
                errors.append(
                    "supporting factual evidence lacks a bound host observation: "
                    f"{evidence_id}"
                )

    actual_edges: set[tuple[str, str, str]] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            errors.append("support edge is not an object")
            continue
        triple = (edge.get("claim_id"), edge.get("evidence_id"), edge.get("source_id"))
        if not all(isinstance(value, str) and value for value in triple):
            errors.append(f"support edge is incomplete: {edge}")
            continue
        if triple in actual_edges:
            errors.append(f"duplicate support edge: {edge}")
        actual_edges.add(triple)
        if triple[0] not in claim_by_id:
            errors.append(f"support edge has unknown claim: {edge}")
        if triple[1] not in evidence_by_id:
            errors.append(f"support edge has unknown evidence: {edge}")
        if triple[2] not in source_ids:
            errors.append(f"support edge has unassessed source: {edge}")
    expected_unsupported: set[str] = set()
    for claim_id, claim in claim_by_id.items():
        refs = claim.get("evidence_refs")
        expected_refs: list[str] = []
        seen_support_identities: set[str] = set()
        for evidence_id in evidence_by_claim.get(claim_id, []):
            entry = evidence_by_id[evidence_id]
            source_id = entry.get("source_id")
            if (
                entry.get("status") not in SUPPORTING_STATUSES
                or assessment_verdicts.get(source_id)
                not in ADMITTED_ASSESSMENT_VERDICTS
                or (
                    claim.get("kind") in HOST_OBSERVATION_REQUIRED_KINDS
                    and not has_bound_host_observation(
                        source_records.get(source_id, {})
                    )
                )
            ):
                continue
            identity = independence_identities.get(source_id, source_id)
            if identity in seen_support_identities:
                continue
            seen_support_identities.add(identity)
            expected_refs.append(evidence_id)
            expected_edges.add((claim_id, evidence_id, source_id))
        if not isinstance(refs, list) or refs != expected_refs:
            errors.append(f"claim evidence_refs differ from evidence bindings: {claim_id}")
        if not expected_refs:
            expected_unsupported.add(claim_id)
            if claim.get("kind") in FACTUAL_KINDS:
                errors.append(
                    "factual claim has no assessed source support; "
                    f"no admitted supporting evidence: {claim_id}"
                )
    if actual_edges != expected_edges:
        errors.append("support edges do not exactly match evidence claim/source bindings")
    unsupported = ledger.get("unsupported_claims")
    if not isinstance(unsupported, list) or set(unsupported) != expected_unsupported:
        errors.append("unsupported_claims differs from claims without evidence")
    if ledger.get("run_id") != retrieval_index.get("run_id"):
        errors.append("evidence ledger run_id differs from retrieval index")
    return errors
