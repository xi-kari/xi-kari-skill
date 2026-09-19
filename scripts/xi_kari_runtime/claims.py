"""Claim/mechanism graph semantics for Xi-Kari v3."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .world_volume import (
    _native_snapshot,
    _validate_ontology_binding,
    _validate_schema,
)


REQUIRED_CLAIM_ONTOLOGY = frozenset(
    {
        "V83-CANON-CORE-CLAIM-ROLES",
        "V83-CANON-CORE-EVIDENCE-CONTRACT",
        "V83-CANON-CORE-BRANCH-PATH",
    }
)
EXPLANATION_KINDS = (
    "simple-baseline",
    "main",
    "strongest-rival",
    "mixture",
    "residual",
)


class ClaimMechanismError(ValueError):
    """Raised when claims, mechanisms, or cases cross semantic boundaries."""


def _unique_ids(records: list[Mapping[str, Any]], field: str, label: str) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for record in records:
        identifier = record[field]
        if identifier in result:
            raise ClaimMechanismError(f"duplicate {label} ID: {identifier}")
        result[identifier] = record
    return result


def validate_claim_graph(
    graph: Mapping[str, object],
    *,
    evidence_mode: str = "open-world",
    repository_root: Path | None = None,
) -> dict[str, Any]:
    """Validate a v8.3-bound claim/mechanism graph and return its snapshot."""

    if evidence_mode not in {"open-world", "closed-input"}:
        raise ClaimMechanismError(f"unsupported evidence mode: {evidence_mode}")

    snapshot = _native_snapshot(
        graph, label="claim mechanism graph", error_type=ClaimMechanismError
    )
    if not isinstance(snapshot, dict):
        raise ClaimMechanismError("claim mechanism graph must be a mapping")
    raw_countercases = snapshot.get("countercases")
    if isinstance(raw_countercases, list) and any(
        isinstance(countercase, Mapping)
        and not countercase.get("attacks_mechanism_ids")
        for countercase in raw_countercases
    ):
        raise ClaimMechanismError(
            "countercase must bind and attack a decisive mechanism"
        )
    _validate_schema(
        "xk-claim-mechanism.schema.json",
        snapshot,
        label="claim mechanism graph",
        error_type=ClaimMechanismError,
        repository_root=repository_root,
    )
    _validate_ontology_binding(
        snapshot,
        required=REQUIRED_CLAIM_ONTOLOGY,
        label="claim mechanism graph",
        error_type=ClaimMechanismError,
        repository_root=repository_root,
    )

    evidence = _unique_ids(snapshot["evidence"], "evidence_id", "evidence")
    claims = _unique_ids(snapshot["claims"], "claim_id", "claim")
    mechanisms = _unique_ids(
        snapshot["mechanisms"], "mechanism_id", "mechanism"
    )
    explanations = _unique_ids(
        snapshot["explanations"], "explanation_id", "explanation"
    )
    cases = _unique_ids(snapshot["cases"], "case_id", "case")
    countercases = _unique_ids(
        snapshot["countercases"], "countercase_id", "countercase"
    )
    if snapshot["central_claim_id"] not in claims:
        raise ClaimMechanismError("central claim does not resolve")

    evidence_ids = set(evidence)
    mechanism_ids = set(mechanisms)
    claim_ids = set(claims)
    residual_ids = {
        residual_id
        for explanation in explanations.values()
        for residual_id in explanation["residual_ids"]
    }
    if any(
        not isinstance(residual_id, str)
        or not residual_id.startswith(("RESIDUAL-", "XK-RESIDUAL-"))
        for residual_id in residual_ids
    ):
        raise ClaimMechanismError("residual explanation references an invented identity")

    for record in evidence.values():
        xk3_refs = record["xk3_evidence_refs"]
        if len(xk3_refs) != len(set(xk3_refs)):
            raise ClaimMechanismError(
                "claim graph evidence has duplicate XK3 evidence bindings"
            )

    for claim in claims.values():
        if not set(claim["evidence_refs"]).issubset(evidence_ids):
            raise ClaimMechanismError("claim evidence reference does not resolve")
        if not set(claim["mechanism_ids"]).issubset(mechanism_ids):
            raise ClaimMechanismError("claim mechanism reference does not resolve")
        if not set(claim["depends_on_claim_ids"]).issubset(claim_ids):
            raise ClaimMechanismError("claim dependency does not resolve")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(claim_id: str) -> None:
        if claim_id in visiting:
            raise ClaimMechanismError("claim dependency cycle is not permitted")
        if claim_id in visited:
            return
        visiting.add(claim_id)
        for parent in claims[claim_id]["depends_on_claim_ids"]:
            visit(parent)
        visiting.remove(claim_id)
        visited.add(claim_id)

    for claim_id in claims:
        visit(claim_id)
    missing_inputs = _unique_ids(snapshot["missing_inputs"], "missing_id", "missing input")
    for missing in missing_inputs.values():
        affected = set(missing["affected_claim_ids"])
        if not affected.issubset(claim_ids):
            raise ClaimMechanismError("missing input affected claim does not resolve")
        if missing["scope"] == "global" and affected != claim_ids:
            raise ClaimMechanismError("global missing input must cover every claim")

    signatures: set[tuple[object, ...]] = set()
    for mechanism in mechanisms.values():
        if not set(mechanism["evidence_refs"]).issubset(evidence_ids):
            raise ClaimMechanismError("mechanism evidence reference does not resolve")
        signature = (
            mechanism["carrier"],
            mechanism["channel"],
            mechanism["clock"],
            tuple(sorted(mechanism["conditions"])),
        )
        if signature in signatures:
            raise ClaimMechanismError(
                "mechanisms must be genuinely different in carrier, channel, clock, or conditions"
            )
        signatures.add(signature)

    if len(explanations) != len(EXPLANATION_KINDS) or {
        explanation["kind"] for explanation in explanations.values()
    } != set(EXPLANATION_KINDS):
        raise ClaimMechanismError(
            "claim graph must preserve simple-baseline, main, strongest-rival, mixture, and residual explanations"
        )
    explanation_by_kind = {
        explanation["kind"]: explanation for explanation in explanations.values()
    }
    explanation_signatures: set[tuple[object, ...]] = set()
    for explanation in explanations.values():
        if not set(explanation["claim_ids"]).issubset(claim_ids):
            raise ClaimMechanismError("explanation claim reference does not resolve")
        if not set(explanation["mechanism_ids"]).issubset(mechanism_ids):
            raise ClaimMechanismError("explanation mechanism reference does not resolve")
        if explanation["applicability"] == "not-applicable":
            if any(explanation[field] for field in ("claim_ids", "mechanism_ids", "residual_ids")):
                raise ClaimMechanismError("not-applicable explanation cannot fabricate claim or mechanism bindings")
            continue
        if not explanation["claim_ids"]:
            raise ClaimMechanismError("applicable explanation requires a claim")
        if explanation["kind"] == "residual" and not explanation["residual_ids"]:
            raise ClaimMechanismError("residual explanation must retain a residual")
        if explanation["kind"] == "strongest-rival" and not explanation["mechanism_ids"]:
            raise ClaimMechanismError("strongest-rival explanation needs a mechanism")
        signature = (
            tuple(sorted(explanation["claim_ids"])),
            tuple(sorted(explanation["mechanism_ids"])),
            tuple(sorted(explanation["residual_ids"])),
            " ".join(explanation["rationale"].split()).casefold(),
        )
        if signature in explanation_signatures:
            raise ClaimMechanismError(
                "explanations must be genuinely different, not relabelled copies"
            )
        explanation_signatures.add(signature)

    baseline = explanation_by_kind["simple-baseline"]
    main = explanation_by_kind["main"]
    rival = explanation_by_kind["strongest-rival"]
    mixture = explanation_by_kind["mixture"]
    if baseline["mechanism_ids"]:
        raise ClaimMechanismError("simple baseline cannot hide a mechanism")
    if main["applicability"] == "applicable" and not main["mechanism_ids"]:
        raise ClaimMechanismError("main explanation needs a mechanism")
    main_mechanism_ids = set(main["mechanism_ids"])
    baseline_claim_mechanisms = {
        mechanism_id
        for claim_id in baseline["claim_ids"]
        for mechanism_id in claims[claim_id]["mechanism_ids"]
    }
    if baseline_claim_mechanisms.intersection(main_mechanism_ids):
        raise ClaimMechanismError(
            "simple baseline claim cannot smuggle the main mechanism"
        )
    if (
        main["applicability"] == rival["applicability"] == "applicable"
        and set(main["mechanism_ids"]) == set(rival["mechanism_ids"])
    ):
        raise ClaimMechanismError(
            "main and strongest-rival explanations need different mechanisms"
        )
    rival_claim_mechanisms = {
        mechanism_id
        for claim_id in rival["claim_ids"]
        for mechanism_id in claims[claim_id]["mechanism_ids"]
    }
    if (
        set(rival["mechanism_ids"]).intersection(main_mechanism_ids)
        or rival_claim_mechanisms.intersection(main_mechanism_ids)
    ):
        raise ClaimMechanismError(
            "strongest-rival claim cannot smuggle the main mechanism"
        )
    required_mixture = set(main["mechanism_ids"]) | set(rival["mechanism_ids"])
    if mixture["applicability"] == "applicable" and (
        len(mixture["mechanism_ids"]) < 2
        or main["applicability"] != "applicable"
        or rival["applicability"] != "applicable"
        or not required_mixture.issubset(set(mixture["mechanism_ids"]))
    ):
        raise ClaimMechanismError(
            "mixture explanation must combine the main and strongest-rival mechanisms"
        )

    for case in cases.values():
        if not set(case["tests_claim_ids"]).issubset(claim_ids):
            raise ClaimMechanismError("case claim reference does not resolve")
        if case["kind"] == "documented-real" and not case["source_refs"]:
            raise ClaimMechanismError("documented-real case requires a source")
        if case["kind"] == "conditional-scenario" and case["source_refs"]:
            raise ClaimMechanismError(
                "conditional scenario cannot masquerade as an externally sourced case"
            )
    for countercase in countercases.values():
        if not set(countercase["attacks_claim_ids"]).issubset(claim_ids):
            raise ClaimMechanismError("countercase claim reference does not resolve")
        expected_mechanism_ids = {
            mechanism_id
            for claim_id in countercase["attacks_claim_ids"]
            for mechanism_id in claims[claim_id]["mechanism_ids"]
        }
        if (
            not expected_mechanism_ids
            or set(countercase["attacks_mechanism_ids"])
            != expected_mechanism_ids
        ):
            raise ClaimMechanismError(
                "countercase must bind and attack a decisive mechanism"
            )

    mechanism_claim_ids = {
        mechanism_id: {
            claim_id
            for claim_id, claim in claims.items()
            if mechanism_id in claim["mechanism_ids"]
        }
        for mechanism_id in mechanisms
    }
    for mechanism_id, covered_claim_ids in mechanism_claim_ids.items():
        documented_cases = [
            case
            for case in cases.values()
            if case["kind"]
            in (
                {"documented-real"}
                if evidence_mode == "open-world"
                else {"user-material"}
            )
            and covered_claim_ids.intersection(case["tests_claim_ids"])
        ]
        conditional_cases = [
            case
            for case in cases.values()
            if case["kind"] in {"user-material", "conditional-scenario"}
            and covered_claim_ids.intersection(case["tests_claim_ids"])
        ]
        failure_cases = [
            countercase
            for countercase in countercases.values()
            if covered_claim_ids.intersection(countercase["attacks_claim_ids"])
        ]
        if not documented_cases:
            raise ClaimMechanismError(
                f"mechanism {mechanism_id} lacks a documented-real case"
            )
        if not conditional_cases:
            raise ClaimMechanismError(
                f"mechanism {mechanism_id} lacks a conditional or user-material case"
            )
        if not failure_cases:
            raise ClaimMechanismError(
                f"mechanism {mechanism_id} lacks a countercase or failure case"
            )

    return snapshot


def claim_constraints(
    graph: Mapping[str, Any], *, undecidable_claim_ids: set[str] | None = None
) -> dict[str, dict[str, Any]]:
    """Derive local constraints from frozen evidence identities and the dependency DAG.

    Reusing an XK3 atom under a different evidence ID cannot restore its support.
    Source invalidation also applies to aliases bound to that source. Ordinary
    missing facts remain local; a shared premise propagates only to descendants.
    """

    claims = {row["claim_id"]: row for row in graph["claims"]}
    evidence = {row["evidence_id"]: row for row in graph["evidence"]}
    mechanisms = {row["mechanism_id"]: row for row in graph["mechanisms"]}
    parent = {identifier: identifier for identifier in evidence}

    def root(identifier: str) -> str:
        while parent[identifier] != identifier:
            parent[identifier] = parent[parent[identifier]]
            identifier = parent[identifier]
        return identifier

    invalid_sources = {
        source for row in evidence.values() if row["support_status"] == "invalidated"
        for source in row["source_refs"]
    }
    owners: dict[tuple[str, str], str] = {}
    for identifier, row in evidence.items():
        keys = [("atom", atom) for atom in row["xk3_evidence_refs"]]
        keys.extend(("source", source) for source in row["source_refs"] if source in invalid_sources)
        for key in keys:
            if key in owners:
                parent[root(identifier)] = root(owners[key])
            else:
                owners[key] = identifier
    groups: dict[str, set[str]] = {}
    for identifier in evidence:
        groups.setdefault(root(identifier), set()).add(identifier)
    failed_groups = {
        group for group, identifiers in groups.items()
        if any(evidence[identifier]["support_status"] != "available" for identifier in identifiers)
    }
    missing_by_claim: dict[str, list[Mapping[str, Any]]] = {identifier: [] for identifier in claims}
    for missing in graph["missing_inputs"]:
        for identifier in missing["affected_claim_ids"]:
            missing_by_claim[identifier].append(missing)
    undecidable = undecidable_claim_ids or set()
    result: dict[str, dict[str, Any]] = {}

    def derive(identifier: str) -> dict[str, Any]:
        if identifier in result:
            return result[identifier]
        claim = claims[identifier]
        evidence_refs = set(claim["evidence_refs"])
        for mechanism_id in claim["mechanism_ids"]:
            evidence_refs.update(mechanisms[mechanism_id]["evidence_refs"])
        blocked_evidence = set().union(*(
            groups[root(ref)] for ref in evidence_refs if root(ref) in failed_groups
        )) if evidence_refs else set()
        missing_ids = {row["missing_id"] for row in missing_by_claim[identifier]}
        blocked = bool(blocked_evidence) or any(row["effect"] == "blocking" for row in missing_by_claim[identifier])
        limiting = any(row["effect"] == "limiting" for row in missing_by_claim[identifier])
        blocked_claims: set[str] = set()
        for dependency in claim["depends_on_claim_ids"]:
            inherited = derive(dependency)
            missing_ids.update(inherited["missing_input_ids"])
            blocked_evidence.update(inherited["blocking_evidence_refs"])
            limiting = limiting or inherited["limiting"]
            if inherited["blocked"] or dependency in undecidable:
                blocked = True
                blocked_claims.add(dependency)
                blocked_claims.update(inherited["blocking_claim_ids"])
        value = {
            "blocked": blocked, "limiting": limiting,
            "blocking_claim_ids": sorted(blocked_claims),
            "blocking_evidence_refs": sorted(blocked_evidence),
            "missing_input_ids": sorted(missing_ids),
        }
        result[identifier] = value
        return value

    for identifier in claims:
        derive(identifier)
    return result


def qualifies_as_insight(candidate: Mapping[str, object]) -> bool:
    """Return whether a candidate changes an explanation, path, or action boundary."""

    if not isinstance(candidate, Mapping):
        return False
    changed_fields = (
        "explanation_change",
        "ranking_change",
        "residual_change",
        "prediction_change",
        "action_change",
        "scale_or_circle_change",
    )
    return any(bool(candidate.get(field)) for field in changed_fields)


__all__ = (
    "ClaimMechanismError",
    "claim_constraints",
    "qualifies_as_insight",
    "validate_claim_graph",
)
