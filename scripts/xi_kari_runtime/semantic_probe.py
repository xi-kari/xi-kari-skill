"""Fresh-process semantic probe used by XK9 stability and sensitivity checks."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
from typing import Any, Mapping

from .authoring import (
    SEMANTIC_AUTHORING_FIELDS,
    _semantic_inputs,
    validate_semantic_probe_authorings,
    variant_contract as build_variant_contract,
)
from .canonical_json import read_json, sha256_file, sha256_json
from .contracts import require_packet_contract
from .judgment import (
    validate_action_ranking,
    validate_framework_gap_isolation,
    validate_verdict_bundle,
)
from .semantic_chain import validate_semantic_chain
from .semantic_projection import semantic_atom_paths
from .transformations import validate_cascade


def _variant(
    packet: Mapping[str, Any],
    authoring_bundle: Mapping[str, Any],
    run_contract: Mapping[str, Any],
    source_lock: Mapping[str, Any],
    read_plan: Mapping[str, Any],
    input_packet_sha256: str,
    *,
    requested_stance: str,
    time_window: str | None,
) -> tuple[dict[str, Any], dict[str, Any], Mapping[str, Any]]:
    authorings = validate_semantic_probe_authorings(
        authoring_bundle,
        packet,
        run_contract,
        source_lock=source_lock,
        read_plan=read_plan,
        input_packet_sha256=input_packet_sha256,
        verify_executable=False,
    )
    variant_kind = (
        "time-window-shift"
        if time_window is not None
        else f"stance-{requested_stance}"
    )
    authoring = authorings.get(variant_kind)
    if not isinstance(authoring, Mapping):
        raise ValueError("independent semantic probe authoring is missing")
    semantic_packet = authoring["semantic_packet"]
    variant_packet = {
        key: deepcopy(value)
        for key, value in packet.items()
        if key != "semantic_probe_authorings"
        and key not in SEMANTIC_AUTHORING_FIELDS
    }
    variant_packet.update(_semantic_inputs(semantic_packet))
    variant_contract = build_variant_contract(
        run_contract,
        requested_stance=requested_stance,
        time_window=time_window,
    )
    binding = deepcopy(dict(packet["runtime_binding"]))
    binding["problem_contract_sha256"] = variant_contract[
        "problem_contract_sha256"
    ]
    binding["stance_neutrality_key"] = variant_contract["stance_neutrality_key"]
    variant_packet["runtime_binding"] = binding
    return variant_packet, variant_contract, authoring


def _variant_visibility_ledger(
    source_packet: Mapping[str, Any],
    variant_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Rebind frozen visibility decisions to the independently authored shape."""

    ledger = source_packet.get("visibility_ledger")
    entries = ledger.get("entries") if isinstance(ledger, Mapping) else None
    if not isinstance(entries, list):
        raise ValueError("semantic variant requires the frozen visibility ledger")

    decisions: dict[str, Mapping[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError("semantic variant visibility entry is not an object")
        path = entry.get("canonical_path")
        if not isinstance(path, str) or not path:
            raise ValueError("semantic variant visibility path is invalid")
        if path in decisions:
            raise ValueError("semantic variant visibility path is duplicated")
        decisions[path] = entry

    variant_paths = semantic_atom_paths(variant_packet)
    missing = [path for path in variant_paths if path not in decisions]
    if missing:
        raise ValueError(
            "independent semantic variant introduces an unclassified semantic atom: "
            + missing[0]
        )
    return {
        "entries": [deepcopy(dict(decisions[path])) for path in variant_paths],
    }


def _apply_mutation(packet: dict[str, Any], mutation: str | None) -> None:
    if mutation is None:
        return
    if mutation == "remove-scale-bridge":
        ledger = packet.get("transformation_ledger")
        if not isinstance(ledger, dict):
            return
        scale = next(
            (
                record
                for record in ledger.get("transformations", [])
                if isinstance(record, dict) and record.get("kind") == "scale"
            ),
            None,
        )
        if isinstance(scale, dict):
            differences = scale.get("axis_differences", [])
            for difference in differences:
                if isinstance(difference, dict) and difference.get("relation") != "unknown":
                    difference["evidence_refs"] = []
                    break
        return
    if mutation == "remove-second-order-feedback":
        states = packet.get("recursive_states")
        if not isinstance(states, dict):
            return
        # Pick a live second-order state that actually has a third-order
        # successor.  The fixture intentionally contains one already-stopped
        # order-two path; mutating that path would be a no-op and would make
        # this metamorphic probe falsely appear valid.  Marking a live parent
        # stopped while retaining its child must be rejected by the recursive
        # parent/child continuity validator.
        order_three_parents = {
            str(state.get("parent_state_ids", [None])[0])
            for state in states.values()
            if isinstance(state, dict)
            and state.get("order") == 3
            and state.get("parent_state_ids")
        }
        for state_id, state in states.items():
            if (
                isinstance(state, dict)
                and state.get("order") == 2
                and state.get("status") != "stopped"
                and str(state_id) in order_three_parents
            ):
                state["status"] = "stopped"
                state["stop_reason"] = (
                    "sensitivity probe removed the second-order feedback"
                )
                break
        return
    raise ValueError(f"unknown semantic probe mutation: {mutation}")


def _validate_semantics(
    packet: Mapping[str, Any],
    run_contract: Mapping[str, Any],
    *,
    repository_root: Path,
) -> None:
    require_packet_contract(
        packet,
        mode=str(run_contract["mode"]),
        run_contract=run_contract,
    )
    if packet.get("dynamic_applicability") == "not_applicable":
        return
    world = packet["local_world_model"]
    if packet.get("cascade") is not None:
        validate_cascade(packet["cascade"], world, repository_root=repository_root)
    chain = validate_semantic_chain(
        world_volume=world,
        transformation_ledger=packet["transformation_ledger"],
        claim_mechanism_graph=packet["claim_mechanism_graph"],
        recursive_lineage=packet["recursive_lineage"],
        recursive_states=packet["recursive_states"],
        evidence_mode=str(run_contract["mode"]),
        repository_root=repository_root,
    )
    validate_verdict_bundle(
        packet["verdict"],
        claim_mechanism_graph=chain.graph,
        recursive_validation=chain.recursive,
        recursive_states=packet["recursive_states"],
        evidence_mode=str(run_contract["mode"]),
        repository_root=repository_root,
    )
    validate_action_ranking(
        packet["action_ranking"],
        verdict_bundle=packet["verdict"],
        repository_root=repository_root,
    )
    if packet.get("framework_gap") is not None:
        validate_framework_gap_isolation(
            packet["framework_gap"],
            claim_mechanism_graph=chain.graph,
            verdict_bundle=packet["verdict"],
            action_ranking=packet["action_ranking"],
            recursive_validation=chain.recursive,
            recursive_states=packet["recursive_states"],
            evidence_mode=str(run_contract["mode"]),
            repository_root=repository_root,
        )


def _invariant_projection(packet: Mapping[str, Any]) -> dict[str, Any]:
    stance = packet.get("stance_pair", {})
    preferred = stance.get("preferred") if isinstance(stance, Mapping) else None
    selected = (
        stance.get(preferred)
        if isinstance(stance, Mapping) and preferred in {"position", "counterposition"}
        else None
    )
    return {
        "dynamic_applicability": packet.get("dynamic_applicability"),
        "verdict": packet.get("verdict"),
        "action_ranking": packet.get("action_ranking"),
        "stance": {
            "preferred": preferred,
            "selected": selected,
            "selection_reason": (
                stance.get("selection_reason")
                if isinstance(stance, Mapping)
                else None
            ),
            "switch_conditions": (
                stance.get("switch_conditions")
                if isinstance(stance, Mapping)
                else None
            ),
        },
        "answer": {
            key: packet.get("answer", {}).get(key)
            for key in (
                "direct_answer",
                "judgment_strength",
                "withdrawal_conditions",
                "action_ceiling",
            )
        },
    }


def _downstream_projection(packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: packet.get(key)
        for key in (
            "local_world_model",
            "transformation_ledger",
            "cascade",
            "claim_mechanism_graph",
            "recursive_lineage",
            "recursive_states",
            "order_evaluation",
            "red_team",
            "stance_pair",
            "verdict",
            "action_ranking",
            "forecast",
            "framework_gap",
            "mechanisms",
            "orders",
            "answer",
        )
    }


def run_probe(
    *,
    packet_path: Path,
    authoring_bundle_path: Path,
    run_contract_path: Path,
    source_lock_path: Path,
    read_plan_path: Path,
    repository_root: Path,
    requested_stance: str,
    time_window: str | None = None,
    mutation: str | None = None,
) -> dict[str, Any]:
    packet = read_json(packet_path)
    authoring_bundle = read_json(authoring_bundle_path)
    run_contract = read_json(run_contract_path)
    source_lock = read_json(source_lock_path)
    read_plan = read_json(read_plan_path)
    variant_packet, variant_contract, authoring = _variant(
        packet,
        authoring_bundle,
        run_contract,
        source_lock,
        read_plan,
        sha256_file(packet_path),
        requested_stance=requested_stance,
        time_window=time_window,
    )
    _apply_mutation(variant_packet, mutation)
    variant_packet["visibility_ledger"] = _variant_visibility_ledger(
        packet,
        variant_packet,
    )
    errors: list[str] = []
    try:
        _validate_semantics(
            variant_packet,
            variant_contract,
            repository_root=repository_root,
        )
    except Exception as exc:  # the probe reports semantic failure as data
        errors.append(str(exc))
    projection = _invariant_projection(variant_packet)
    result = {
        "requested_stance": requested_stance,
        "authoring_id": authoring["authoring_id"],
        "authoring_provenance_sha256": authoring["runtime_receipt_sha256"],
        "process_pid": os.getpid(),
        "input_variant_sha256": sha256_json(variant_packet),
        "invariant_projection_sha256": sha256_json(projection),
        "downstream_projection_sha256": sha256_json(
            _downstream_projection(variant_packet)
        ),
        "verdict_sha256": sha256_json(variant_packet.get("verdict")),
        "action_ranking_sha256": sha256_json(
            variant_packet.get("action_ranking")
        ),
        "valid": not errors,
        "errors": errors,
    }
    # `mutation` is a probe-control detail, not part of a normal stance
    # receipt.  Leaving a null field in the receipt would violate the strict
    # XK9 stance-stability schema; sensitivity reports identify their own
    # mutation by `probe_id`.
    if mutation is not None:
        result["mutation"] = mutation
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--authoring-bundle", type=Path, required=True)
    parser.add_argument("--run-contract", type=Path, required=True)
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--read-plan", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument(
        "--requested-stance", choices=("support", "oppose"), required=True
    )
    parser.add_argument("--time-window")
    parser.add_argument("--mutation")
    args = parser.parse_args()
    result = run_probe(
        packet_path=args.packet,
        authoring_bundle_path=args.authoring_bundle,
        run_contract_path=args.run_contract,
        source_lock_path=args.source_lock,
        read_plan_path=args.read_plan,
        repository_root=args.repository_root,
        requested_stance=args.requested_stance,
        time_window=args.time_window,
        mutation=args.mutation,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
