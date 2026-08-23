"""Coverage accounting for source reads, assessments, support, and outputs."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .prose import build_reader_trace
from .semantic_projection import (
    reader_projection_units,
    redact_payload_for_delivery,
    typed_semantic_atoms,
)


REQUIRED_OUTPUTS = ("answer", "dossier", "atlas", "casebook")
READER_OUTPUT_PATHS = {
    "answer": "delivery/xi-kari-answer.md",
    "dossier": "delivery/xi-kari-dossier.md",
    "atlas": "delivery/xi-kari-concept-atlas.md",
    "casebook": "delivery/xi-kari-case-and-countercase.md",
}


def build_coverage(
    *,
    run_id: str,
    source_lock: dict[str, Any],
    retrieval_index: dict[str, Any],
    evidence_ledger: dict[str, Any],
    planned_outputs: list[str] | tuple[str, ...] = REQUIRED_OUTPUTS,
) -> dict[str, Any]:
    receipts = source_lock.get("reader_receipts", source_lock.get("receipts", []))
    mismatched = [
        item.get("unit")
        for item in receipts
        if item.get("expected_sha256") != item.get("observed_sha256")
    ]
    sources = retrieval_index.get("sources", [])
    unsupported = list(evidence_ledger.get("unsupported_claims", []))
    outputs = list(planned_outputs)
    missing_outputs = sorted(set(REQUIRED_OUTPUTS) - set(outputs))
    complete = (
        source_lock.get("complete") is True
        and source_lock.get("reader_unit_count") == len(receipts)
        and source_lock.get("source_unit_count") == 4753
        and not mismatched
        and retrieval_index.get("source_count") == len(sources)
        and retrieval_index.get("all_sources_assessed") is True
        and not missing_outputs
    )
    return {
        "schema_id": "xi-kari.v2.coverage",
        "schema_version": 3,
        "run_id": run_id,
        "source_read": {
            "expected": source_lock.get("reader_unit_count"),
            "observed": len(receipts),
            "source_units_expected": 4753,
            "source_units_observed": source_lock.get("source_unit_count"),
            "mismatched": mismatched,
            "complete": source_lock.get("complete") is True and not mismatched,
        },
        "source_assessment": {
            "sources": len(sources),
            "assessments": len(sources) if retrieval_index.get("all_sources_assessed") else 0,
            "unassessed": [] if retrieval_index.get("all_sources_assessed") else ["unknown"],
        },
        "claim_support": {
            "claims": len(evidence_ledger.get("claims", [])),
            "supported": len(evidence_ledger.get("claims", [])) - len(unsupported),
            "unsupported": unsupported,
        },
        "outputs": {"required": list(REQUIRED_OUTPUTS), "planned": outputs, "missing": missing_outputs},
        "complete": complete,
    }


def validate_coverage(coverage: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    source_read = coverage.get("source_read", {})
    if source_read.get("expected") != source_read.get("observed"):
        errors.append("source read coverage count mismatch")
    if source_read.get("mismatched"):
        errors.append("source read coverage contains mismatches")
    if source_read.get("source_units_expected") != source_read.get("source_units_observed"):
        errors.append("source unit coverage is not 4753")
    source_assessment = coverage.get("source_assessment", {})
    if source_assessment.get("sources") != source_assessment.get("assessments"):
        errors.append("not every source has a separate assessment")
    if coverage.get("outputs", {}).get("missing"):
        errors.append("required readable output is missing from plan")
    if not coverage.get("complete"):
        errors.append("coverage is not complete")
    return errors


def load_reader_outputs(run_dir: Path) -> dict[str, str]:
    root = Path(run_dir)
    return {
        name: path.read_text(encoding="utf-8") if path.is_file() else ""
        for name, relative in READER_OUTPUT_PATHS.items()
        for path in (root / relative,)
    }


def _fragments(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, (list, tuple)):
        result: list[str] = []
        for item in value:
            result.extend(_fragments(item))
        return list(dict.fromkeys(result))
    return []


def _leaf_source_paths(value: Any, base_path: str) -> list[str]:
    if isinstance(value, Mapping):
        result: list[str] = []
        for key, child in value.items():
            result.extend(
                _leaf_source_paths(child, f"{base_path}.{key}")
            )
        return result
    if isinstance(value, (list, tuple)):
        result = []
        for index, child in enumerate(value):
            result.extend(_leaf_source_paths(child, f"{base_path}[{index}]"))
        return result
    if value in (None, ""):
        return []
    return [base_path]


def _projection_check(
    *,
    unit_id: str,
    unit_kind: str,
    fragments: list[str],
    required_outputs: tuple[str, ...] = ("answer",),
    atom_statuses: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    normalized = list(dict.fromkeys(fragment for fragment in fragments if fragment))
    if not normalized:
        return None
    return {
        "unit_id": unit_id,
        "unit_kind": unit_kind,
        "fragments": normalized,
        "required_outputs": list(required_outputs),
        "atom_statuses": list(atom_statuses or []),
        "projected_outputs": [],
        "missing_fragments": list(normalized),
        "complete": False,
    }


def _stance_projection(
    packet: Mapping[str, Any], reader_trace: Mapping[str, Any]
) -> dict[str, Any]:
    applicability = packet.get("dynamic_applicability")
    stance = packet.get("stance_pair")
    if applicability != "applicable" or not isinstance(stance, Mapping):
        return {
            "preferred": None,
            "required_fragments": [],
            "missing_required_fragments": [],
            "forbidden_fragments": [],
            "present_forbidden_fragments": [],
            "complete": True,
        }

    def claim(side: str) -> str:
        value = stance.get(side)
        if not isinstance(value, Mapping):
            return ""
        return str(value.get("claim", "")).strip().rstrip("。；;，, ")

    preferred = stance.get("preferred")
    valid_preferred = preferred in {"position", "counterposition", "undecided"}
    position = claim("position")
    counterposition = claim("counterposition")
    answer = packet.get("answer")
    direct = (
        str(answer.get("direct_answer", "")).strip().rstrip("。；;，, ")
        if isinstance(answer, Mapping)
        else ""
    )
    reason = str(stance.get("selection_reason", "")).strip().rstrip("。；;，, ")
    if preferred == "position":
        selected, rival = position, counterposition
        required = [
            {"output": "answer", "fragment": f"当前较强判断：{selected}"},
            {"output": "answer", "fragment": f"**最强反方**：{rival}"},
            {"output": "dossier", "fragment": f"当前较强的立场：{selected}"},
            {"output": "dossier", "fragment": f"最强反方：{rival}"},
        ]
        forbidden = [
            {"output": "answer", "fragment": f"当前较强判断：{rival}"},
            {"output": "answer", "fragment": f"**最强反方**：{selected}"},
            {"output": "dossier", "fragment": f"当前较强的立场：{rival}"},
            {"output": "dossier", "fragment": f"最强反方：{selected}"},
        ]
    elif preferred == "counterposition":
        selected, rival = counterposition, position
        required = [
            {"output": "answer", "fragment": f"当前较强判断：{selected}"},
            {"output": "answer", "fragment": f"**最强反方**：{rival}"},
            {"output": "dossier", "fragment": f"当前较强的立场：{selected}"},
            {"output": "dossier", "fragment": f"最强反方：{rival}"},
        ]
        forbidden = [
            {"output": "answer", "fragment": f"当前较强判断：{rival}"},
            {"output": "answer", "fragment": f"**最强反方**：{selected}"},
            {"output": "dossier", "fragment": f"当前较强的立场：{rival}"},
            {"output": "dossier", "fragment": f"最强反方：{selected}"},
        ]
    elif preferred == "undecided":
        required = [
            {"output": "answer", "fragment": f"当前未定选判断：{direct}"},
            {"output": "answer", "fragment": f"**待比较立场一**：{position}"},
            {"output": "answer", "fragment": f"**待比较立场二**：{counterposition}"},
            {"output": "answer", "fragment": f"未定选原因：{reason}"},
            {"output": "dossier", "fragment": f"当前尚未定选：{direct}"},
            {"output": "dossier", "fragment": f"待比较立场一：{position}"},
            {"output": "dossier", "fragment": f"待比较立场二：{counterposition}"},
            {"output": "dossier", "fragment": f"未定选原因：{reason}"},
        ]
        forbidden = [
            {"output": "answer", "fragment": "当前较强判断："},
            {"output": "answer", "fragment": "**最强反方**："},
            {"output": "answer", "fragment": "暂时选择当前判断"},
            {
                "output": "answer",
                "fragment": "## 另一种解释：最强反方与当前选择",
            },
            {"output": "dossier", "fragment": "当前较强的立场："},
            {"output": "dossier", "fragment": "最强反方："},
            {"output": "dossier", "fragment": "暂时选择的理由"},
        ]
    else:
        required = [{"output": "answer", "fragment": "未登记有效立场裁决"}]
        forbidden = []
    output_matches = {
        item.get("output"): item.get("matches_observed") is True
        for item in reader_trace.get("outputs", [])
        if isinstance(item, Mapping)
    }
    missing = [
        item for item in required if output_matches.get(item["output"]) is not True
    ]
    if not valid_preferred:
        missing = list(required)
    present_forbidden = [
        item
        for item in forbidden
        if output_matches.get(item["output"]) is not True
    ]
    return {
        "preferred": preferred,
        "required_fragments": required,
        "missing_required_fragments": missing,
        "forbidden_fragments": forbidden,
        "present_forbidden_fragments": present_forbidden,
        "complete": not missing and not present_forbidden,
    }


def build_semantic_coverage(
    *,
    run_id: str,
    packet: dict[str, Any],
    source_read_complete: bool,
    candidate_closure_complete: bool,
    reader_outputs: Mapping[str, str],
) -> dict[str, Any]:
    audit_packet = packet
    reader_units = reader_projection_units(audit_packet)
    reader_units_by_path: dict[str, list[str]] = {}
    for unit in reader_units:
        for fragment in unit.get("fragment_traces", []):
            for path in fragment.get("exact_source_paths", []):
                reader_units_by_path.setdefault(path, []).append(unit["unit_id"])
    typed_atom_ledger = []
    for atom in typed_semantic_atoms(audit_packet):
        reader_unit_ids = sorted(
            set(reader_units_by_path.get(atom["canonical_path"], []))
        )
        status = atom["projection_status"]
        if status != "withheld_for_protection":
            status = "projected" if reader_unit_ids else "audit_only"
        typed_atom_ledger.append(
            {
                "canonical_path": atom["canonical_path"],
                "value_type": atom["value_type"],
                "visibility": atom["visibility"],
                "projection_status": status,
                "reader_unit_ids": reader_unit_ids,
            }
        )
    packet = redact_payload_for_delivery(audit_packet)
    graph = packet.get("claim_mechanism_graph", {})
    graph_claims = {
        item.get("claim_id"): item
        for item in graph.get("claims", [])
        if isinstance(graph, Mapping) and isinstance(item, Mapping)
    }
    graph_mechanisms = {
        item.get("mechanism_id"): item
        for item in graph.get("mechanisms", [])
        if isinstance(graph, Mapping) and isinstance(item, Mapping)
    }
    evidence_claims = {
        item.get("claim_id"): item
        for item in packet.get("evidence", {}).get("claims", [])
        if isinstance(item, Mapping)
    }
    lineage = packet.get("recursive_lineage", {})
    main_branch = next(
        (
            item
            for item in lineage.get("branches", [])
            if isinstance(lineage, Mapping)
            and isinstance(item, Mapping)
            and item.get("kind") == "main"
        ),
        {},
    )
    main_node_ids = list(main_branch.get("node_ids", []))
    conclusion_units = {
        "answer_basis": list(packet.get("answer", {}).get("basis_refs", [])),
        "mechanism_ids": [str(value) for value in graph_mechanisms],
        "case_ids": [
            str(item.get("case_id"))
            for item in packet.get("case_ledger", {}).get("cases", [])
            if isinstance(item, dict)
        ],
        "recursive_node_ids": [
            str(item.get("node_id"))
            for item in lineage.get("nodes", [])
            if isinstance(item, Mapping) and item.get("node_id") is not None
        ],
        "withdrawal_conditions": list(
            packet.get("answer", {}).get("withdrawal_conditions", [])
        ),
    }
    checks: list[dict[str, Any]] = []
    trace_units: list[dict[str, Any]] = []

    def add(
        unit_id: str,
        unit_kind: str,
        fragments: list[str],
        *,
        required_outputs: tuple[str, ...] = ("answer",),
        atom_statuses: list[dict[str, Any]] | None = None,
        fragment_traces: list[dict[str, Any]] | None = None,
        exact_source_paths: list[str] | None = None,
    ) -> None:
        check = _projection_check(
            unit_id=unit_id,
            unit_kind=unit_kind,
            fragments=fragments,
            required_outputs=required_outputs,
            atom_statuses=atom_statuses,
        )
        if check is not None:
            checks.append(check)
            normalized_sources = list(dict.fromkeys(exact_source_paths or []))
            trace_units.append(
                {
                    "unit_id": unit_id,
                    "unit_kind": unit_kind,
                    "fragments": list(check["fragments"]),
                    "required_outputs": list(required_outputs),
                    "fragment_traces": (
                        list(fragment_traces)
                        if fragment_traces is not None
                        else [
                            {
                                "text": fragment,
                                "exact_source_paths": normalized_sources,
                            }
                            for fragment in check["fragments"]
                        ]
                    ),
                }
            )

    for unit in reader_units:
        required_outputs = tuple(unit.get("required_outputs", ("answer",)))
        add(
            unit["unit_id"],
            unit["unit_kind"],
            list(unit["fragments"]),
            required_outputs=required_outputs,
            atom_statuses=list(unit.get("atom_statuses", [])),
            fragment_traces=list(unit.get("fragment_traces", [])),
        )

    answer = packet.get("answer", {})
    add(
        "answer.direct",
        "judgment",
        _fragments(answer.get("direct_answer")),
        exact_source_paths=_leaf_source_paths(
            answer.get("direct_answer"), "answer.direct_answer"
        ),
    )
    for index, value in enumerate(answer.get("why", [])):
        add(
            f"answer.reason.{index}",
            "judgment_reason",
            _fragments(value),
            exact_source_paths=_leaf_source_paths(value, f"answer.why[{index}]"),
        )
    for index, value in enumerate(answer.get("uncertainties", [])):
        add(
            f"answer.uncertainty.{index}",
            "uncertainty",
            _fragments(value),
            exact_source_paths=_leaf_source_paths(
                value, f"answer.uncertainties[{index}]"
            ),
        )
    for index, value in enumerate(answer.get("withdrawal_conditions", [])):
        add(
            f"answer.withdrawal.{index}",
            "withdrawal",
            _fragments(value),
            exact_source_paths=_leaf_source_paths(
                value, f"answer.withdrawal_conditions[{index}]"
            ),
        )

    for reference in answer.get("basis_refs", []):
        value = graph_claims.get(reference) or evidence_claims.get(reference)
        if isinstance(value, Mapping):
            add(
                f"basis.claim.{reference}",
                "basis_claim",
                _fragments(value.get("statement", value.get("text"))),
            )
        mechanism = graph_mechanisms.get(reference)
        if isinstance(mechanism, Mapping):
            add(
                f"basis.mechanism.{reference}",
                "basis_mechanism",
                _fragments(mechanism.get("name")),
            )

    mechanism_values = list(graph_mechanisms.values()) or [
        item for item in packet.get("mechanisms", []) if isinstance(item, Mapping)
    ]
    for index, mechanism in enumerate(mechanism_values):
        identifier = mechanism.get("mechanism_id", index)
        add(
            f"mechanism.{identifier}",
            "mechanism",
            _fragments(mechanism.get("name"))
            + _fragments(mechanism.get("input_state"))
            + _fragments(mechanism.get("channel"))
            + _fragments(mechanism.get("output_state"))
            + _fragments(mechanism.get("explanation"))
            + _fragments(mechanism.get("failure_condition")),
        )

    case_ledger = packet.get("case_ledger", {})
    for index, case in enumerate(case_ledger.get("cases", [])):
        if not isinstance(case, Mapping):
            continue
        add(
            f"case.{case.get('case_id', index)}",
            "case",
            _fragments(case.get("summary"))
            + _fragments(case.get("boundary"))
            + _fragments(case.get("cannot_prove")),
        )
    for index, case in enumerate(case_ledger.get("countercases", [])):
        if not isinstance(case, Mapping):
            continue
        add(
            f"countercase.{case.get('countercase_id', index)}",
            "countercase",
            _fragments(case.get("conditions"))
            + _fragments(case.get("expected_signal"))
            + _fragments(case.get("reverse_signal"))
            + _fragments(case.get("decision_impact")),
        )

    states = packet.get("recursive_states", {})
    state_values = states.values() if isinstance(states, Mapping) else ()
    states_by_node = {
        value.get("node_id"): value
        for value in state_values
        if isinstance(value, Mapping)
    }
    for node_id in main_node_ids:
        state = states_by_node.get(node_id)
        if not isinstance(state, Mapping):
            continue
        add(
            f"recursive.{node_id}",
            "recursive_state",
            _fragments(state.get("state_delta"))
            + _fragments(state.get("carrier"))
            + _fragments(state.get("conditions"))
            + _fragments(state.get("failure_condition"))
            + _fragments(state.get("early_signal"))
            + _fragments(state.get("reverse_signal"))
            + _fragments(state.get("writeback")),
        )

    stance = packet.get("stance_pair", {})
    if isinstance(stance, Mapping):
        for side in ("position", "counterposition"):
            value = stance.get(side)
            if isinstance(value, Mapping):
                add(
                    f"stance.{side}",
                    "stance",
                    _fragments(value.get("claim")),
                )
        add(
            "stance.selection",
            "stance_selection",
            _fragments(stance.get("selection_reason"))
            + _fragments(stance.get("switch_conditions")),
        )
    red_team = packet.get("red_team", {})
    if isinstance(red_team, Mapping):
        add(
            "red_team.strongest_attack",
            "counterargument",
            _fragments(red_team.get("strongest_attack")),
        )
        add(
            "red_team.reverse_signals",
            "reverse_signal",
            _fragments(red_team.get("reverse_signals")),
        )

    order_evaluation = packet.get("order_evaluation", {})
    if isinstance(order_evaluation, Mapping):
        for index, evaluation in enumerate(order_evaluation.get("orders", [])):
            if not isinstance(evaluation, Mapping):
                continue
            order = evaluation.get("order", index + 1)
            add(
                f"order_evaluation.{order}",
                "order_evaluation",
                _fragments(evaluation.get("baseline"))
                + _fragments(evaluation.get("explanatory_increment"))
                + _fragments(evaluation.get("predictive_increment"))
                + _fragments(evaluation.get("new_assumptions"))
                + _fragments(evaluation.get("new_losses"))
                + _fragments(evaluation.get("local_predictability"))
                + _fragments(evaluation.get("continue_value")),
            )

    verdict = packet.get("verdict", {})
    if isinstance(verdict, Mapping):
        if verdict.get("judgment_kind") == "non-decidability":
            boundary = verdict.get("non_decidability")
            if isinstance(boundary, Mapping):
                add(
                    "verdict.non_decidability",
                    "verdict_boundary",
                    _fragments(boundary.get("reason"))
                    + _fragments(boundary.get("missing_inputs")),
                )
        else:
            current = verdict.get("current_best_judgment")
            if isinstance(current, Mapping):
                add(
                    "verdict.current_best",
                    "verdict_boundary",
                    _fragments(current.get("proposition"))
                    + _fragments(current.get("time_window"))
                    + _fragments(current.get("withdrawal_conditions"))
                    + _fragments(current.get("action_ceiling")),
                )

    ranking = packet.get("action_ranking", {})
    if isinstance(ranking, Mapping):
        for index, option in enumerate(ranking.get("options", [])):
            if not isinstance(option, Mapping):
                continue
            add(
                f"action.{option.get('option_id', index)}",
                "action",
                _fragments(option.get("description"))
                + _fragments(option.get("stop_conditions"))
                + _fragments(option.get("rollback"))
                + _fragments(option.get("appeal"))
                + _fragments(option.get("remedy")),
            )

    applicability = packet.get("dynamic_applicability")
    if applicability == "not_applicable":
        add(
            "three_order.not_applicable",
            "not_applicable",
            ["三阶推演不适用"]
            + _fragments(packet.get("not_applicable_reason")),
        )
    reader_trace = build_reader_trace(
        dict(audit_packet),
        trace_units,
        dict(reader_outputs),
    )
    reader_trace["run_id"] = run_id
    output_matches = {
        item["output"]: item["matches_observed"]
        for item in reader_trace["outputs"]
    }
    traced_fragments = {
        (entry["unit_id"], entry["output"], entry["fragment_index"])
        for entry in reader_trace["entries"]
    }
    for check in checks:
        projected_outputs: list[str] = []
        missing_fragments: list[str] = []
        for output in check["required_outputs"]:
            output_complete = output_matches.get(output) is True
            for fragment_index, fragment in enumerate(check["fragments"]):
                if (
                    check["unit_id"],
                    output,
                    fragment_index,
                ) not in traced_fragments:
                    output_complete = False
                if not output_complete and fragment not in missing_fragments:
                    missing_fragments.append(fragment)
            if output_complete:
                projected_outputs.append(output)
        check["projected_outputs"] = projected_outputs
        check["missing_fragments"] = missing_fragments
        check["complete"] = not missing_fragments
    stance_projection = _stance_projection(packet, reader_trace)
    unprojected = [item["unit_id"] for item in checks if not item["complete"]]
    if not stance_projection["complete"]:
        unprojected.append("stance.role_projection")
    answer_checks = [
        item for item in checks if "answer" in item.get("required_outputs", [])
    ]
    stance_answer_complete = not any(
        item.get("output") == "answer"
        for item in (
            stance_projection.get("missing_required_fragments", [])
            + stance_projection.get("present_forbidden_fragments", [])
        )
    )
    main_answer_complete = (
        bool(answer_checks)
        and all(item["complete"] for item in answer_checks)
        and stance_answer_complete
    )
    reader_projection_complete = (
        bool(checks) and not unprojected and main_answer_complete
    )
    return {
        "schema_id": "xi-kari.v2.semantic-coverage",
        "schema_version": 3,
        "run_id": run_id,
        "dynamic_applicability": applicability,
        "not_applicable_reason": packet.get("not_applicable_reason"),
        "conclusion_units": conclusion_units,
        "typed_atom_ledger": typed_atom_ledger,
        "projection_checks": checks,
        "reader_trace": reader_trace,
        "stance_projection": stance_projection,
        "unprojected_unit_ids": unprojected,
        "source_read_complete": source_read_complete,
        "candidate_closure_complete": candidate_closure_complete,
        "main_answer_complete": main_answer_complete,
        "reader_projection_complete": reader_projection_complete,
    }
