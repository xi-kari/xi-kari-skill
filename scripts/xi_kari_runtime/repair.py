"""Forward-only repair planning for Xi-Kari v2."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any, Mapping

from .canonical_json import atomic_write_json, read_json, sha256_file, sha256_json
from .contracts import PRODUCTION_CONTRACT_PROFILE, build_runtime_packet_binding
from .materialization import fork_run, materialize_run, repair_plan, status_run


def repair_snapshot_sha256(run_dir: Path) -> str:
    """Hash the parent run bytes while excluding the mutable plan itself."""

    root = Path(run_dir).expanduser().resolve()
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"repair snapshot cannot contain a symlink: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative == "continuation/repair-plan.json":
            continue
        entries.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return sha256_json(entries)


def repair_run(
    run_dir: Path,
    *,
    reason: str,
    replacement_packet: Mapping[str, Any] | None = None,
    patch: Mapping[str, Any] | None = None,
    runs_root: Path | None = None,
    run_id: str | None = None,
    repository_root: Path | None = None,
    semantic_read_trace_path: str | Path | None = None,
    validated_plan: Mapping[str, Any] | None = None,
    validated_parent_snapshot_sha256: str | None = None,
) -> Path:
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("repair requires a reason")
    parent = Path(run_dir).expanduser().resolve()
    parent_contract = read_json(parent / "run-contract.json")
    production = (
        isinstance(parent_contract, Mapping)
        and parent_contract.get("contract_profile") == PRODUCTION_CONTRACT_PROFILE
    )
    if production and patch:
        raise ValueError(
            "production repair requires a fresh base authoring packet; patch is not accepted"
        )
    if production and semantic_read_trace_path is not None:
        raise ValueError(
            "production continuation owns a fresh semantic read trace"
        )
    parent_status = status_run(parent)
    if (
        validated_plan is None
        and production
        and parent_status.get("state") == "prepared"
    ):
        # A prepared production run has no validation failure to repair. Treat
        # this request as a fresh production reauthoring fork instead.
        return fork_run(
            parent,
            runs_root=runs_root,
            run_id=run_id,
            repository_root=repository_root,
            continuation_kind="fork",
            semantic_read_trace_path=None,
        )
    if validated_plan is None:
        plan = repair_plan(parent, repository_root=repository_root)
    else:
        plan = dict(validated_plan)
        disk_plan = read_json(parent / "continuation" / "repair-plan.json")
        if disk_plan != plan:
            raise ValueError("repair plan changed before repair execution")
        if validated_parent_snapshot_sha256 is not None and (
            repair_snapshot_sha256(parent) != validated_parent_snapshot_sha256
        ):
            raise ValueError("parent changed after repair plan validation")
    if replacement_packet is None:
        if not production:
            packet_path = parent / "continuation" / "input-packet.json"
            if not packet_path.is_file():
                raise ValueError("repair requires replacement_packet when no parent packet exists")
            replacement_packet = read_json(packet_path)
            if patch:
                merged = dict(replacement_packet)
                merged.update(dict(patch))
                replacement_packet = merged
    child = fork_run(
        parent,
        runs_root=runs_root,
        run_id=run_id,
        base_phase=plan["earliest_invalid_phase"],
        repository_root=repository_root,
        continuation_kind="repair",
        semantic_read_trace_path=(
            None if production else semantic_read_trace_path
        ),
    )

    def discard_child() -> None:
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)

    try:
        child_contract = read_json(child / "run-contract.json")
        runtime_binding = build_runtime_packet_binding(child_contract)
        if production:
            fresh_path = child / "continuation" / "input-packet.json"
            fresh_packet = read_json(fresh_path)
            if not isinstance(fresh_packet, Mapping):
                raise ValueError(
                    "production continuation did not persist its fresh base packet"
                )
            if replacement_packet is None:
                replacement_packet = dict(fresh_packet)
            else:
                supplied = {
                    key: value
                    for key, value in dict(replacement_packet).items()
                    if key not in {"runtime_binding", "concept_disposition"}
                }
                observed = {
                    key: value
                    for key, value in dict(fresh_packet).items()
                    if key not in {"runtime_binding", "concept_disposition"}
                }
                if supplied != observed:
                    raise ValueError(
                        "replacement packet differs from the fresh base authoring output"
                    )
        if replacement_packet is None:
            raise ValueError("repair requires a replacement packet")
        supplied_binding = replacement_packet.get("runtime_binding")
        if supplied_binding is not None and supplied_binding != runtime_binding:
            raise ValueError("replacement packet runtime binding differs from the child run")
        bound_replacement = dict(replacement_packet)
        bound_replacement["runtime_binding"] = runtime_binding
    except Exception:
        discard_child()
        raise
    try:
        parent_plan_path = parent / "continuation" / "repair-plan.json"
        parent_plan_sha256 = sha256_file(parent_plan_path)
        parent_binding_path = child / "continuation" / "parent.json"
        parent_binding = read_json(parent_binding_path)
        parent_binding["parent_repair_plan_sha256"] = parent_plan_sha256
        parent_binding["parent_repair_reset_phases"] = list(plan["reset_phases"])
        atomic_write_json(parent_binding_path, parent_binding)
        atomic_write_json(
            child / "continuation/repair-record.json",
            {
                "schema_id": "xi-kari.v2.repair-record",
                "schema_version": 3,
                "run_id": status_run(child)["run_id"],
                "parent_run_id": status_run(parent)["run_id"],
                "earliest_invalid_phase": plan["earliest_invalid_phase"],
                "reason": reason.strip(),
                "replacement_packet_sha256": sha256_json(bound_replacement),
                "parent_repair_plan_sha256": parent_plan_sha256,
                "parent_repair_reset_phases": list(plan["reset_phases"]),
            },
        )
        materialize_run(child, bound_replacement, repository_root=repository_root)
    except Exception:
        discard_child()
        raise
    return child
