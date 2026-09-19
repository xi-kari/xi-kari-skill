"""Separated fact/prediction/value/responsibility/authorization judgments."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
import re
from typing import Any

from .canonical_json import sha256_json
from .claims import ClaimMechanismError, claim_constraints, validate_claim_graph
from .problem_contract import parse_instant
from .recursion import LineageValidation
from .world_volume import _native_snapshot, _validate_ontology_binding, _validate_schema


REQUIRED_VERDICT_ONTOLOGY = frozenset(
    {
        "V83-CANON-CORE-OUTPUT-SEPARATION",
        "V83-CANON-CORE-STRONG-JUDGMENT",
        "V83-CANON-AUTHORIZATION",
    }
)
REQUIRED_ACTION_ONTOLOGY = frozenset(
    {
        "V83-CANON-SELECTION",
        "V83-CANON-NO-ACTION",
        "V83-CANON-AUTHORIZATION",
    }
)
REQUIRED_GAP_ONTOLOGY = frozenset(
    {
        "V83-CANDIDATE-PROVISIONAL-VARIABLE",
        "V83-CANON-CORE-COMMON-KERNEL",
    }
)
FRAMEWORK_GAP_SOURCE_ANCHORS = ("V83-P2084", "V83-P4613")
VERDICT_KINDS = (
    "fact",
    "structure",
    "mechanism",
    "prediction",
    "value",
    "responsibility",
    "authorization",
)
OPTION_KINDS = (
    "active",
    "delay",
    "probe",
    "exit-or-transfer",
    "maintain-status-quo",
    "no-action",
)
CLAIM_KIND_BY_VERDICT = {
    "fact": frozenset({"factual"}),
    "structure": frozenset({"structural"}),
    "mechanism": frozenset({"mechanism"}),
    "prediction": frozenset({"prediction"}),
    "value": frozenset({"value"}),
    "responsibility": frozenset({"responsibility"}),
    "authorization": frozenset({"authorization"}),
}
FRAMEWORK_GAP_TOKEN = re.compile(
    r"(?<![A-Z0-9_.:-])(XK-(?:GAP|PROV)-[A-Z0-9_.:-]+)(?![A-Z0-9_.:-])"
)


class JudgmentError(ValueError):
    """Raised when outputs cross a fact/value/authorization boundary."""


def empty_framework_gap_ledger() -> dict[str, Any]:
    """Return the explicit isolated state for an applicable run with no gaps."""

    return {
        "schema_id": "xi-kari.v3.xk.framework-gap-ledger",
        "source_version": "v8.3",
        "ontology_refs": sorted(REQUIRED_GAP_ONTOLOGY),
        "source_anchors": list(FRAMEWORK_GAP_SOURCE_ANCHORS),
        "candidates": [],
        "isolated_from_current_reasoning": True,
    }


def _unique(records: Sequence[Mapping[str, Any]], field: str, label: str) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for record in records:
        identifier = record[field]
        if identifier in result:
            raise JudgmentError(f"duplicate {label} ID: {identifier}")
        result[identifier] = record
    return result


def _walk_strings(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, item in value.items():
            if isinstance(key, str):
                found.add(key)
            found.update(_walk_strings(item))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            found.update(_walk_strings(item))
    elif isinstance(value, str):
        found.add(value)
    return found


def _framework_gap_tokens(value: object) -> set[str]:
    return {
        token
        for text in _walk_strings(value)
        for token in FRAMEWORK_GAP_TOKEN.findall(text)
    }


def five_by_kind(verdict: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    records = verdict.get("five_verdicts", [])
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        return {}
    return {record["kind"]: record for record in records if isinstance(record, Mapping)}


def validate_verdict_bundle(
    verdict: Mapping[str, object],
    *,
    claim_mechanism_graph: Mapping[str, object],
    recursive_validation: LineageValidation | None = None,
    recursive_states: Mapping[str, Mapping[str, object]] | None = None,
    evidence_mode: str = "open-world",
    repository_root: Path | None = None,
) -> dict[str, Any]:
    """Validate exactly seven non-substitutable verdict kinds."""

    snapshot = _native_snapshot(
        verdict, label="verdict bundle", error_type=JudgmentError
    )
    if not isinstance(snapshot, dict):
        raise JudgmentError("verdict bundle must be a mapping")
    try:
        _validate_schema(
            "xk-verdict.schema.json",
            snapshot,
            label="verdict bundle",
            error_type=JudgmentError,
            repository_root=repository_root,
        )
    except JudgmentError as error:
        records = snapshot.get("five_verdicts")
        if isinstance(records, list) and {
            record.get("kind")
            for record in records
            if isinstance(record, Mapping)
        } != set(VERDICT_KINDS):
            raise JudgmentError(
                "verdict bundle must separate all seven verdict kinds"
            ) from error
        raise
    graph = _native_snapshot(
        claim_mechanism_graph,
        label="claim mechanism graph for verdict",
        error_type=JudgmentError,
    )
    if not isinstance(graph, dict):
        raise JudgmentError("claim mechanism graph must be a mapping")
    try:
        graph = validate_claim_graph(
            graph, evidence_mode=evidence_mode, repository_root=repository_root
        )
    except ClaimMechanismError as error:
        raise JudgmentError(f"invalid claim graph for verdict: {error}") from error
    _validate_ontology_binding(
        snapshot,
        required=REQUIRED_VERDICT_ONTOLOGY,
        label="verdict bundle",
        error_type=JudgmentError,
        repository_root=repository_root,
    )
    by_claim = {claim["claim_id"]: claim for claim in graph["claims"]}
    by_evidence = {entry["evidence_id"]: entry for entry in graph["evidence"]}
    by_explanation = {
        explanation["explanation_id"]: explanation
        for explanation in graph["explanations"]
    }
    local_records = _unique(snapshot["claim_verdicts"], "claim_id", "claim verdict")
    if set(local_records) != set(by_claim):
        raise JudgmentError("claim verdicts must cover every claim exactly once")
    constraints = claim_constraints(
        graph,
        undecidable_claim_ids={identifier for identifier, row in local_records.items() if row["status"] == "undecidable"},
    )
    for identifier, record in local_records.items():
        constraint = constraints[identifier]
        for field in ("blocking_claim_ids", "blocking_evidence_refs", "missing_input_ids"):
            if set(record[field]) != set(constraint[field]):
                raise JudgmentError(f"claim {identifier} {field} differs from its dependency constraints")
        if constraint["blocked"] and record["status"] != "undecidable":
            raise JudgmentError(f"blocked claim {identifier} cannot retain a usable verdict")
        if constraint["limiting"] and record["status"] == "locked":
            raise JudgmentError(f"claim {identifier} with limiting missing input cannot be locked")
        if record["status"] != "undecidable" and not by_claim[identifier]["evidence_refs"]:
            raise JudgmentError(f"usable claim {identifier} requires grounded evidence")
        if record["status"] == "locked":
            claim = by_claim[identifier]
            if any(local_records[parent]["status"] != "locked" for parent in claim["depends_on_claim_ids"]):
                raise JudgmentError(f"locked claim {identifier} cannot exceed a bounded dependency")
            if claim["kind"] == "factual":
                identities = {by_evidence[ref]["identity"] for ref in claim["evidence_refs"]}
                if "observed" not in identities or identities.intersection({"model-candidate", "simulated-result", "user-material", "unknown"}):
                    raise JudgmentError(f"locked factual claim {identifier} requires observed evidence")
    records = snapshot["five_verdicts"]
    verdict_ids = [record["verdict_id"] for record in records]
    if len(verdict_ids) != len(set(verdict_ids)):
        raise JudgmentError("seven verdict IDs must be unique")
    if {record["kind"] for record in records} != set(VERDICT_KINDS):
        raise JudgmentError("verdict bundle must separate all seven verdict kinds")

    validated_node_ids = (
        set(recursive_validation.node_ids) if recursive_validation is not None else set()
    )
    states_by_node = {
        str(state.get("node_id")): state
        for state in (recursive_states or {}).values()
        if isinstance(state, Mapping) and isinstance(state.get("node_id"), str)
    }

    current_ids = set(by_claim) | set(by_evidence) | set(by_explanation)
    for record in records:
        kind = record["kind"]
        if record["status"] == "undecidable":
            bound_fields = (
                "claim_ids",
                "evidence_refs",
                "claim_evidence_edges",
                "mechanism_ids",
                "recursive_node_ids",
            )
            if any(record[field] for field in bound_fields) or record[
                "authorization_scope"
            ] is not None:
                raise JudgmentError(
                    f"{kind} undecidable verdict cannot retain grounded bindings"
                )
            continue
        if not record["claim_ids"] or not record["evidence_refs"]:
            raise JudgmentError(
                f"{kind} verdict requires grounded claim and evidence references"
            )
        claims = []
        for claim_id in record["claim_ids"]:
            claim = by_claim.get(claim_id)
            if claim is None:
                raise JudgmentError(f"{kind} verdict references an unknown claim")
            claims.append(claim)
            if local_records[claim_id]["status"] == "undecidable":
                raise JudgmentError(f"{kind} verdict cannot promote an undecidable local claim")
            if record["status"] == "locked" and local_records[claim_id]["status"] != "locked":
                raise JudgmentError(f"{kind} verdict cannot exceed its local claim strength")
        if any(claim["kind"] not in CLAIM_KIND_BY_VERDICT[kind] for claim in claims):
            raise JudgmentError(
                f"{kind} verdict cannot substitute a claim from another verdict kind"
            )
        evidence_refs = set(record["evidence_refs"])
        if not evidence_refs.issubset(by_evidence):
            raise JudgmentError(f"{kind} verdict evidence does not resolve")
        edges = record["claim_evidence_edges"]
        edge_pairs = {
            (edge["claim_id"], edge["evidence_id"])
            for edge in edges
        }
        if (
            len(edge_pairs) != len(edges)
            or {claim_id for claim_id, _ in edge_pairs} != set(record["claim_ids"])
            or {evidence_id for _, evidence_id in edge_pairs} != evidence_refs
            or any(
                evidence_id not in by_claim[claim_id]["evidence_refs"]
                for claim_id, evidence_id in edge_pairs
            )
        ):
            raise JudgmentError(
                f"{kind} verdict claim/evidence edge does not exist"
            )
        if not set(record["mechanism_ids"]).issubset(
            {mechanism["mechanism_id"] for mechanism in graph["mechanisms"]}
        ):
            raise JudgmentError(f"{kind} verdict mechanism does not resolve")
        node_ids = set(record["recursive_node_ids"])
        if node_ids.intersection(current_ids):
            raise JudgmentError("verdict node identity collides with a current graph identity")
        if node_ids and (
            recursive_validation is None or not node_ids.issubset(validated_node_ids)
        ):
            raise JudgmentError("verdict recursive node does not resolve to validated XK8")
        scope = record["authorization_scope"]
        if kind == "authorization":
            if not isinstance(scope, Mapping):
                raise JudgmentError("authorization verdict requires one atomic scope")
            source_evidence_id = scope.get("source_evidence_id")
            if source_evidence_id not in evidence_refs:
                raise JudgmentError(
                    "authorization scope source differs from its verdict evidence"
                )
            if by_evidence[source_evidence_id]["identity"] in {
                "model-candidate",
                "simulated-result",
            }:
                raise JudgmentError(
                    "authorization scope cannot be grounded by model or simulation evidence"
                )
            if len(claims) != 1:
                raise JudgmentError(
                    "authorization verdict requires exactly one frozen authorization claim"
                )
            frozen_boundary = claims[0].get("authorization_boundary")
            verdict_boundary = {
                key: value
                for key, value in scope.items()
                if key != "source_evidence_id"
            }
            if not isinstance(frozen_boundary, Mapping) or verdict_boundary != dict(
                frozen_boundary
            ):
                raise JudgmentError(
                    "authorization tuple differs from frozen XK3 authorization boundary"
                )
        elif scope is not None:
            raise JudgmentError("non-authorization verdict cannot carry authorization scope")
        if kind == "fact" and record["status"] == "locked":
            identities = {by_evidence[evidence_id]["identity"] for evidence_id in record["evidence_refs"]}
            if "observed" not in identities or identities.intersection(
                {"model-candidate", "simulated-result", "user-material"}
            ):
                raise JudgmentError(
                    "fact verdict lock requires observed evidence and cannot use model or user candidates"
                )
            if any(
                states_by_node.get(node_id, {}).get("evidence_identity")
                in {"model-candidate", "simulated-result"}
                for node_id in node_ids
            ):
                raise JudgmentError("simulated recursive node cannot become a factual lock")

    ranking = snapshot["explanation_ranking"]
    ranked_ids = [item["explanation_id"] for item in ranking]
    if len(ranked_ids) != len(set(ranked_ids)) or set(ranked_ids) != set(by_explanation):
        raise JudgmentError("explanation disposition must cover every explanation category exactly once")
    rows_by_id = {row["explanation_id"]: row for row in ranking}
    for row in ranking:
        explanation = by_explanation[row["explanation_id"]]
        if not set(row["claim_ids"]).issubset(by_claim):
            raise JudgmentError("explanation local comparison references an unknown claim")
        if explanation["applicability"] == "not-applicable":
            if row["role"] != "not-applicable" or row["rank"] is not None or row["claim_ids"]:
                raise JudgmentError("not-applicable explanation cannot retain a ranking or local comparison")
        elif row["role"] == "not-applicable" or not row["claim_ids"]:
            raise JudgmentError("applicable explanation must retain its local comparison")
        if row["role"] in {"excluded", "unresolved", "not-applicable"} and row["rank"] is not None:
            raise JudgmentError("excluded or unresolved explanation cannot carry a preference rank")
        if row["rank"] is not None and any(local_records[claim_id]["status"] == "undecidable" for claim_id in row["claim_ids"]):
            raise JudgmentError("ranked explanation cannot rely on an undecidable local claim")
    if snapshot["judgment_kind"] == "best-current":
        best = snapshot["current_best_judgment"]
        if best is None or snapshot["non_decidability"] is not None:
            raise JudgmentError("best-current judgment requires a current verdict only")
        primary = rows_by_id.get(best["best_explanation_id"])
        if primary is None or primary["role"] != "primary" or primary["rank"] != 1:
            raise JudgmentError("best-current judgment must bind a primary local explanation")
        runner_up = best["runner_up_explanation_id"]
        if runner_up is not None and (
            runner_up == best["best_explanation_id"] or runner_up not in rows_by_id
            or rows_by_id[runner_up]["role"] in {"excluded", "not-applicable"}
        ):
            raise JudgmentError("best-current rival does not resolve to an applicable explanation")
        if not set(best["strongest_counterevidence_refs"]).issubset(by_evidence):
            raise JudgmentError("strongest counterevidence does not resolve")
    else:
        if snapshot["current_best_judgment"] is not None or snapshot["non_decidability"] is None:
            raise JudgmentError("non-decidability must not carry a best-current verdict")
        remaining = set(snapshot["non_decidability"]["remaining_partial_order"])
        if len(remaining) < 2 or not remaining.issubset(by_explanation):
            raise JudgmentError(
                "non-decidability requires at least two unresolved explanations"
            )
        if any(rows_by_id[identifier]["rank"] is not None for identifier in remaining):
            raise JudgmentError("unresolved explanations cannot carry a preference rank")
    return snapshot


def validate_action_ranking(
    ranking: Mapping[str, object],
    *,
    verdict_bundle: Mapping[str, object],
    repository_root: Path | None = None,
) -> dict[str, Any]:
    """Validate real options, six category dispositions, and separate recommendation from permission."""

    snapshot = _native_snapshot(
        ranking, label="action ranking", error_type=JudgmentError
    )
    verdict = _native_snapshot(
        verdict_bundle, label="verdict authority", error_type=JudgmentError
    )
    if not isinstance(snapshot, dict) or not isinstance(verdict, dict):
        raise JudgmentError("action ranking and verdict authority must be mappings")
    _validate_schema(
        "xk-verdict-action-ranking.schema.json",
        snapshot,
        label="action ranking",
        error_type=JudgmentError,
        repository_root=repository_root,
    )
    _validate_ontology_binding(
        snapshot,
        required=REQUIRED_ACTION_ONTOLOGY,
        label="action ranking",
        error_type=JudgmentError,
        repository_root=repository_root,
    )
    verdict_records = {
        record["verdict_id"]: record for record in verdict.get("five_verdicts", [])
    }
    verdict_ids = {record["verdict_id"] for record in verdict.get("five_verdicts", [])}
    if set(snapshot["considered_verdict_ids"]) != verdict_ids:
        raise JudgmentError("action ranking must consider exactly the seven verdict IDs")
    options = snapshot["options"]
    option_ids = [option["option_id"] for option in options]
    options_by_id = {option["option_id"]: option for option in options}
    if len(option_ids) != len(set(option_ids)):
        raise JudgmentError("action option IDs must be unique")
    categories = _unique(snapshot["category_dispositions"], "kind", "option category")
    if set(categories) != set(OPTION_KINDS):
        raise JudgmentError("action comparison must dispose of all six option categories")
    for kind, category in categories.items():
        actual = {option["option_id"] for option in options if option["kind"] == kind}
        if set(category["option_ids"]) != actual:
            raise JudgmentError("option category disposition does not match its real options")
        if (category["applicability"] == "applicable") != bool(actual):
            raise JudgmentError("option category applicability must match its real options")
    if snapshot["requested_choice"] and not any(option["kind"] == "no-action" for option in options):
        raise JudgmentError("requested choice must retain an explicit no-action baseline")
    display_order = snapshot["display_order"]
    if set(display_order) != set(option_ids) or len(display_order) != len(option_ids):
        raise JudgmentError("action display order must cover each option exactly once")
    selection_status = snapshot["selection_status"]
    ranking_ids = snapshot["ranking"]
    local_records = {row["claim_id"]: row for row in verdict.get("claim_verdicts", [])}
    supporting = set(snapshot["supporting_claim_ids"])
    if not supporting.issubset(local_records):
        raise JudgmentError("action supporting claim does not resolve to a local verdict")
    if selection_status in {"selected", "recommended"}:
        if not snapshot["requested_choice"]:
            raise JudgmentError("recommended or selected action requires a requested choice")
        if not supporting or any(local_records[identifier]["status"] == "undecidable" for identifier in supporting):
            raise JudgmentError("action supporting claims must have usable local verdicts")
        if (
            not isinstance(ranking_ids, list)
            or not ranking_ids
            or not set(ranking_ids).issubset(option_ids)
            or len(ranking_ids) != len(set(ranking_ids))
        ):
            raise JudgmentError("action preference order must reference distinct real options")
        if (
            snapshot["preferred_option_id"] != ranking_ids[0]
            or snapshot["second_option_id"] != (ranking_ids[1] if len(ranking_ids) > 1 else None)
        ):
            raise JudgmentError("requested choice requires real preferred and second options")
        preferred_option = options_by_id[snapshot["preferred_option_id"]]
        if selection_status == "selected" and (
            preferred_option["authorized"] is not True
            or preferred_option["execution_status"] != "executable"
        ):
            raise JudgmentError(
                "preferred action option must be authorized and executable"
            )
        if selection_status == "recommended" and preferred_option["execution_status"] == "not_executable":
            raise JudgmentError("recommended option must be an analysis proposal or an executable option")
    else:
        if ranking_ids is not None:
            raise JudgmentError("unselected action comparison cannot carry a ranking")
        if snapshot["preferred_option_id"] is not None or snapshot["second_option_id"] is not None:
            raise JudgmentError("unselected action comparison cannot name preferred options")
        if selection_status == "not-requested" and snapshot["requested_choice"]:
            raise JudgmentError("not-requested action status conflicts with the request")
        if selection_status == "undecided" and not snapshot["requested_choice"]:
            raise JudgmentError("undecided action status requires a requested choice")

    options_by_id = {option["option_id"]: option for option in options}
    if selection_status == "selected":
        preferred = options_by_id[snapshot["preferred_option_id"]]
        if preferred["kind"] != "no-action" and not preferred["authorized"]:
            raise JudgmentError(
                "preferred executable option requires current authorization"
            )

    for option in options:
        auth_ref = option["authorization_verdict_id"]
        execution_status = option["execution_status"]
        if option["authorized"]:
            if execution_status != "executable":
                raise JudgmentError("authorized option must be executable")
        elif execution_status not in {"analysis_only", "not_executable"}:
            raise JudgmentError(
                "unauthorized option must be analysis_only or not_executable"
            )
        interval = option["validity_interval"]
        starts_at = parse_instant(
            interval["starts_at"], field="action validity_interval.starts_at"
        )
        ends_at = parse_instant(
            interval["ends_at"], field="action validity_interval.ends_at"
        )
        if starts_at >= ends_at:
            if option["authorized"]:
                raise JudgmentError(
                    "authorization validity interval must start before it ends"
                )
            raise JudgmentError(
                "action validity interval must start before it ends"
            )
        if option["authorized"]:
            if not auth_ref or auth_ref not in verdict_records:
                raise JudgmentError("authorized option requires an authorization verdict")
            if verdict_records[auth_ref]["status"] not in {"locked", "bounded"}:
                raise JudgmentError("authorization verdict is not currently usable")
            if verdict_records[auth_ref]["kind"] != "authorization":
                raise JudgmentError("authorization verdict reference cannot be prediction or responsibility")
            if (
                not verdict_records[auth_ref].get("claim_ids")
                or not verdict_records[auth_ref].get("evidence_refs")
            ):
                raise JudgmentError("authorization verdict is not grounded")
            scope = verdict_records[auth_ref].get("authorization_scope")
            if not isinstance(scope, Mapping) or any(
                option.get(option_field) != scope.get(scope_field)
                for option_field, scope_field in (
                    ("executor", "decision_subject"),
                    ("description", "single_action"),
                    ("target_object", "target_object"),
                    ("territory", "territory"),
                    ("validity_interval", "validity_interval"),
                )
            ):
                raise JudgmentError(
                    "authorized option differs from its atomic authorization scope"
                )
            control_bindings = option.get("control_bindings")
            if not isinstance(control_bindings, Mapping):
                raise JudgmentError(
                    "authorized option requires evidence-bound controls"
                )
            authorization_evidence = set(
                verdict_records[auth_ref]["evidence_refs"]
            )
            for field in ("stop_conditions", "rollback", "appeal", "remedy"):
                control = control_bindings.get(field)
                if (
                    not isinstance(control, Mapping)
                    or control.get("authorization_verdict_id") != auth_ref
                    or set(control.get("evidence_refs", []))
                    != authorization_evidence
                ):
                    raise JudgmentError(
                        f"authorized {field} control is not bound to its authorization verdict and evidence"
                    )
                if control.get("content_sha256") != sha256_json(option[field]):
                    raise JudgmentError(
                        f"authorized {field} control binding differs from its content"
                    )
        elif auth_ref is not None:
            raise JudgmentError("unauthorized option cannot carry an authorization verdict")
        if option["kind"] == "no-action" and option["authorized"]:
            raise JudgmentError("no-action cannot be represented as an authorized intervention")
    return snapshot


def validate_framework_gap_isolation(
    gap: Mapping[str, object],
    *,
    claim_mechanism_graph: Mapping[str, object],
    verdict_bundle: Mapping[str, object],
    action_ranking: Mapping[str, object],
    recursive_validation: LineageValidation | None = None,
    recursive_states: Mapping[str, Mapping[str, object]] | None = None,
    evidence_mode: str = "open-world",
    repository_root: Path | None = None,
) -> dict[str, Any]:
    """Keep future framework candidates out of current claims, verdicts, and actions."""

    snapshot = _native_snapshot(
        gap, label="framework gap ledger", error_type=JudgmentError
    )
    graph = _native_snapshot(
        claim_mechanism_graph, label="gap claim graph", error_type=JudgmentError
    )
    verdict = _native_snapshot(
        verdict_bundle, label="gap verdict", error_type=JudgmentError
    )
    action = _native_snapshot(
        action_ranking, label="gap action ranking", error_type=JudgmentError
    )
    if not all(isinstance(value, dict) for value in (snapshot, graph, verdict, action)):
        raise JudgmentError("framework-gap inputs must be mappings")
    try:
        _validate_schema(
            "xk-verdict-framework-gap.schema.json",
            snapshot,
            label="framework gap ledger",
            error_type=JudgmentError,
            repository_root=repository_root,
        )
    except JudgmentError as error:
        if "gap_id" in str(error):
            raise JudgmentError(
                "framework gap identity is not isolated from current reasoning"
            ) from error
        raise
    _validate_ontology_binding(
        snapshot,
        required=REQUIRED_GAP_ONTOLOGY,
        label="framework gap ledger",
        error_type=JudgmentError,
        repository_root=repository_root,
    )
    try:
        graph = validate_claim_graph(
            graph, evidence_mode=evidence_mode, repository_root=repository_root
        )
    except ClaimMechanismError as error:
        raise JudgmentError(f"invalid current claim graph: {error}") from error
    # Inspect raw values even after a current-artifact failure so a forged gap
    # reference cannot hide behind that earlier error.  Any unrelated failure
    # is re-raised after the isolation check.
    verdict_error: JudgmentError | None = None
    action_error: JudgmentError | None = None
    try:
        validate_verdict_bundle(
            verdict,
            claim_mechanism_graph=graph,
            recursive_validation=recursive_validation,
            recursive_states=recursive_states,
            evidence_mode=evidence_mode,
            repository_root=repository_root,
        )
    except JudgmentError as error:
        verdict_error = error
    try:
        validate_action_ranking(
            action,
            verdict_bundle=verdict,
            repository_root=repository_root,
        )
    except JudgmentError as error:
        action_error = error

    current_values = (graph, verdict, action)
    current_ids = set().union(*(_walk_strings(value) for value in current_values))
    current_tokens = set().union(
        *(_framework_gap_tokens(value) for value in current_values)
    )
    gap_ids = [candidate["gap_id"] for candidate in snapshot["candidates"]]
    if len(gap_ids) != len(set(gap_ids)) or set(gap_ids).intersection(
        current_ids | current_tokens
    ):
        raise JudgmentError("framework gap identity is not isolated from current reasoning")
    claim_ids = {claim["claim_id"] for claim in graph["claims"]}
    mechanism_ids = {mechanism["mechanism_id"] for mechanism in graph["mechanisms"]}
    evidence_ids = {entry["evidence_id"] for entry in graph["evidence"]}
    residual_ids = {
        residual_id
        for explanation in graph["explanations"]
        for residual_id in explanation["residual_ids"]
    }
    validated_node_ids = (
        set(recursive_validation.node_ids)
        if recursive_validation is not None
        else set()
    )
    frozen_state_node_ids = (
        {
            str(state.get("node_id"))
            for state in recursive_states.values()
            if isinstance(state, Mapping) and isinstance(state.get("node_id"), str)
        }
        if recursive_states is not None
        else None
    )
    for candidate in snapshot["candidates"]:
        if not set(candidate["current_claim_ids"]).issubset(claim_ids):
            raise JudgmentError("framework gap current claim reference does not resolve")
        if not set(candidate["current_mechanism_ids"]).issubset(mechanism_ids):
            raise JudgmentError("framework gap current mechanism reference does not resolve")
        if not set(candidate["evidence_refs"]).issubset(evidence_ids):
            raise JudgmentError("framework gap evidence reference does not resolve")
        if not set(candidate["originating_residual_ids"]).issubset(residual_ids):
            raise JudgmentError("framework gap residual origin does not resolve")
        node_ids = set(candidate["recursive_node_ids"])
        if node_ids and (
            recursive_validation is None
            or not node_ids.issubset(validated_node_ids)
        ):
            raise JudgmentError(
                "framework gap recursive node does not resolve to validated XK8"
            )
        if (
            node_ids
            and frozen_state_node_ids is not None
            and not node_ids.issubset(frozen_state_node_ids)
        ):
            raise JudgmentError(
                "framework gap recursive node does not resolve to frozen recursive states"
            )
        if any(
            gap_id in current_ids | current_tokens
            for gap_id in (candidate["gap_id"], *candidate["provisional_variable_ids"])
        ):
            raise JudgmentError("framework gap leaked into current reasoning")
    if verdict_error is not None:
        raise JudgmentError(
            f"invalid current verdict bundle: {verdict_error}"
        ) from verdict_error
    if action_error is not None:
        raise JudgmentError(
            f"invalid current action ranking: {action_error}"
        ) from action_error
    return snapshot


# Compatibility aliases are intentionally semantic-only; they do not expose old
# U phases or authority registries.
_validate_action_ranking = validate_action_ranking
_validate_framework_gap_isolation = validate_framework_gap_isolation


__all__ = (
    "JudgmentError",
    "empty_framework_gap_ledger",
    "five_by_kind",
    "validate_action_ranking",
    "validate_framework_gap_isolation",
    "validate_verdict_bundle",
)
