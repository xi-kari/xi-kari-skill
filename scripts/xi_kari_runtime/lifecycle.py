"""CLI lifecycle orchestration for isolated Xi-Kari runs."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
from typing import Any, Mapping
import uuid

from .authority import validator_set_sha256
from .canonical_json import (
    atomic_write_bytes,
    atomic_write_json,
    atomic_write_text,
    canonical_dumps,
    read_json,
    sha256_file,
    sha256_json,
)
from .contracts import (
    LEGACY_CONTRACT_PROFILE,
    PRODUCTION_CONTRACT_PROFILE,
    derive_repair_scope,
    expected_phase_artifact_paths,
    repair_phase_events_sha256,
)
from .materialization import (
    _bound_repository_root,
    _phase_input,
    _resolve_run_directory,
    _set_state,
    prepare_run,
    repair_plan,
    resume_run,
    status_run,
    utc_now,
)
from .phase_chain import append_phase, load_phase_records
from .repair import repair_run, repair_snapshot_sha256
from .retrieval import build_full_source_lock
from .validation import run_fresh_validator, validator_fingerprint, validate_run


REPAIR_PLAN_RELATIVE = Path("continuation/repair-plan.json")


def require_cli_start_profile(contract_profile: str) -> None:
    if contract_profile == PRODUCTION_CONTRACT_PROFILE:
        raise ValueError("production runs must be started with execute")
    if contract_profile != LEGACY_CONTRACT_PROFILE:
        raise ValueError(f"unsupported CLI start profile: {contract_profile}")


def _remove_file(path: Path) -> None:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError(f"lifecycle artifact is not a regular file: {path}")
    if path.exists():
        path.unlink()


def _convert_prepared_staging_run(run_dir: Path) -> None:
    contract = read_json(run_dir / "run-contract.json")
    if not isinstance(contract, Mapping):
        raise ValueError("run contract is not an object")
    records = load_phase_records(run_dir)
    if [record.get("phase") for record in records] != ["XK0", "XK1"]:
        raise ValueError("init staging run did not seal exactly XK0-XK1")
    for relative in expected_phase_artifact_paths(
        "XK1", contract_profile=str(contract.get("contract_profile", ""))
    ):
        _remove_file(run_dir / relative)
    _remove_file(run_dir / "authoring/XK02-retrieval-ledger.json")
    atomic_write_text(
        run_dir / "phase-events.jsonl",
        canonical_dumps(records[0]) + "\n",
    )
    _set_state(run_dir, "initialized", next_phase="XK1")


def _require_valid_initialized_run(
    run_dir: Path,
    *,
    repository_root: Path | None,
) -> tuple[dict[str, Any], Path]:
    status = status_run(run_dir)
    if not (
        status.get("state") == "initialized"
        and status.get("phase_count") == 1
        and status.get("current_phase") == "XK0"
        and status.get("next_phase") == "XK1"
    ):
        raise ValueError("run is not at the initialized XK0 boundary")
    report = run_fresh_validator(
        run_dir,
        repository_root=repository_root,
        preseal=False,
        require_complete=False,
    )
    if report.get("valid") is not True or report.get("validated_phase") != "XK0":
        raise ValueError(
            f"initialized run validation failed: {report.get('errors', [])}"
        )
    contract = read_json(run_dir / "run-contract.json")
    if not isinstance(contract, dict):
        raise ValueError("run contract is not an object")
    if contract.get("contract_profile") != LEGACY_CONTRACT_PROFILE:
        raise ValueError("production runs must be started with execute")
    return contract, _bound_repository_root(run_dir, repository_root)


def initialize_run(
    runs_root: Path,
    *,
    problem_contract: Mapping[str, Any],
    mode: str,
    run_id: str | None,
    repository_root: Path | None,
    semantic_authoring_adapter: str | Path | None,
    semantic_authoring_timeout_seconds: int,
    contract_profile: str,
    semantic_read_trace_path: str | Path | None,
    semantic_authoring_profile: str,
    codex_provider_executable: str | Path | None,
    privacy_purpose: str,
    delivery_audience: str,
) -> Path:
    require_cli_start_profile(contract_profile)
    root = _resolve_run_directory(runs_root)
    root_existed = root.exists()
    staging_root = root.parent / f".{root.name}.init-{uuid.uuid4().hex}"
    prepared: Path | None = None
    final: Path | None = None
    moved = False
    try:
        prepared = prepare_run(
            staging_root,
            problem_contract=problem_contract,
            mode=mode,
            run_id=run_id,
            repository_root=repository_root,
            semantic_authoring_adapter=semantic_authoring_adapter,
            semantic_authoring_timeout_seconds=semantic_authoring_timeout_seconds,
            contract_profile=contract_profile,
            semantic_read_trace_path=semantic_read_trace_path,
            semantic_authoring_profile=semantic_authoring_profile,
            codex_provider_executable=codex_provider_executable,
            privacy_purpose=privacy_purpose,
            delivery_audience=delivery_audience,
        )
        _convert_prepared_staging_run(prepared)
        _require_valid_initialized_run(
            prepared,
            repository_root=repository_root,
        )
        root.mkdir(parents=True, exist_ok=True)
        final = root / prepared.name
        if final.exists():
            raise FileExistsError(f"run directory already exists: {final}")
        os.replace(prepared, final)
        moved = True
        prepared = None
        status = status_run(final)
        if status.get("state") != "initialized":
            raise ValueError("moved init run is not initialized")
        return final
    except Exception:
        if moved and final is not None and final.is_dir() and not final.is_symlink():
            shutil.rmtree(final)
        raise
    finally:
        if prepared is not None and prepared.is_dir() and not prepared.is_symlink():
            shutil.rmtree(prepared)
        if staging_root.is_dir() and not staging_root.is_symlink():
            shutil.rmtree(staging_root)
        if not root_existed and root.is_dir() and not any(root.iterdir()):
            root.rmdir()


def _write_xk1_artifacts(
    run_dir: Path,
    *,
    contract: Mapping[str, Any],
    repository_root: Path,
    created: list[Path] | None = None,
) -> list[Path]:
    run_id = str(contract["run_id"])
    lock, events = build_full_source_lock(repository_root, run_id=run_id)
    source_lock_path = run_dir / "source-lock.json"
    events_path = run_dir / "authoring/XK01-read-events.jsonl"
    read_plan_path = run_dir / "authoring/XK01-read-plan.json"
    if created is None:
        created = []
    created.append(source_lock_path)
    atomic_write_json(source_lock_path, lock)
    created.append(events_path)
    atomic_write_text(
        events_path,
        "".join(canonical_dumps(event) + "\n" for event in events),
    )
    created.append(read_plan_path)
    atomic_write_json(
        read_plan_path,
        {
            "schema_id": "xi-kari.v2.read-plan",
            "schema_version": 3,
            "run_id": run_id,
            "framework_version": lock["framework_version"],
            "reader_sequence": lock["reader_sequence"],
            "reader_unit_count": lock["reader_unit_count"],
            "paragraph_count": lock["paragraph_count"],
            "table_count": lock["table_count"],
            "source_unit_count": lock["source_unit_count"],
            "requires_complete_semantic_read": True,
        },
    )
    previous = load_phase_records(run_dir)[-1]
    append_phase(
        run_dir,
        run_id=run_id,
        phase="XK1",
        artifact_path=expected_phase_artifact_paths(
            "XK1", contract_profile=str(contract["contract_profile"])
        ),
        input_sha256=_phase_input(
            previous,
            {"source_lock": lock, "semantic_read_trace": None},
        ),
        created_at=utc_now(),
    )
    retrieval_path = run_dir / "authoring/XK02-retrieval-ledger.json"
    created.append(retrieval_path)
    atomic_write_json(
        retrieval_path,
        {
            "schema_id": "xi-kari.v2.retrieval-ledger",
            "schema_version": 3,
            "run_id": run_id,
            "mode": contract["mode"],
            "status": "awaiting_retrieval",
        },
    )
    return created


def prepare_initialized_run(
    run_dir: Path,
    *,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    run_dir = _resolve_run_directory(run_dir)
    contract, repository = _require_valid_initialized_run(
        run_dir,
        repository_root=repository_root,
    )
    paths = [
        *(run_dir / relative for relative in expected_phase_artifact_paths(
            "XK1", contract_profile=str(contract["contract_profile"])
        )),
        run_dir / "authoring/XK02-retrieval-ledger.json",
    ]
    if any(path.exists() or path.is_symlink() for path in paths):
        raise ValueError("initialized run contains a premature XK1 artifact")
    phase_path = run_dir / "phase-events.jsonl"
    state_path = run_dir / "continuation/state.json"
    original_phase = phase_path.read_bytes()
    original_state = state_path.read_bytes()
    created: list[Path] = []
    try:
        created = _write_xk1_artifacts(
            run_dir,
            contract=contract,
            repository_root=repository,
            created=created,
        )
        _set_state(run_dir, "prepared", next_phase="XK2")
        report = run_fresh_validator(
            run_dir,
            repository_root=repository,
            preseal=False,
            require_complete=False,
        )
        if report.get("valid") is not True or report.get("validated_phase") != "XK1":
            raise ValueError(
                f"prepared run validation failed: {report.get('errors', [])}"
            )
        status = status_run(run_dir)
        if status.get("state") != "prepared" or status.get("phase_count") != 2:
            raise ValueError("initialized run did not advance to prepared")
        return status
    except Exception as failure:
        rollback_errors: list[str] = []
        for path in reversed(created):
            try:
                _remove_file(path)
            except Exception as exc:
                rollback_errors.append(f"{path}: {exc}")
        try:
            atomic_write_bytes(phase_path, original_phase)
        except Exception as exc:
            rollback_errors.append(f"{phase_path}: {exc}")
        try:
            atomic_write_bytes(state_path, original_state)
        except Exception as exc:
            rollback_errors.append(f"{state_path}: {exc}")
        if rollback_errors:
            failure.add_note("lifecycle rollback errors: " + "; ".join(rollback_errors))
        raise


def validate_lifecycle_run(
    run_dir: Path,
    *,
    repository_root: Path | None,
    validation_boundary: str,
    require_complete: bool,
) -> dict[str, Any]:
    status = status_run(run_dir)
    if status.get("state") == "initialized":
        if validation_boundary != "final":
            raise ValueError("initialized validation only supports the final boundary")
        require_complete = False
    return validate_run(
        run_dir,
        repository_root=repository_root,
        require_complete=require_complete,
        validation_boundary=validation_boundary,
        fresh_process=True,
    )


def _repair_errors(report: Mapping[str, Any]) -> list[str]:
    prefix = "run artifact schema continuation/repair-plan.json"
    return [
        str(error)
        for error in report.get("errors", [])
        if not str(error).startswith(prefix)
    ]


def _bound_plan_document(
    run_dir: Path,
    *,
    repository_root: Path,
    status: Mapping[str, Any],
    errors: list[str],
    report: Mapping[str, Any],
) -> dict[str, Any]:
    earliest, reset_phases = derive_repair_scope(errors)
    return {
        "schema_id": "xi-kari.v2.repair-plan",
        "schema_version": 3,
        "run_id": status["run_id"],
        "earliest_invalid_phase": earliest,
        "reset_phases": reset_phases,
        "reason": errors,
        "fresh": True,
        "planned_state": "invalid",
        "run_contract_sha256": sha256_file(run_dir / "run-contract.json"),
        "phase_events_sha256": repair_phase_events_sha256(run_dir),
        "run_snapshot_sha256": repair_snapshot_sha256(run_dir),
        "validator_set_sha256": validator_set_sha256(repository_root),
        "validation_errors_sha256": sha256_json(errors),
        "validator_fresh_process": report.get("fresh_process") is True,
        "validator_fingerprint_sha256": validator_fingerprint(report),
    }


def write_bound_repair_plan(
    run_dir: Path,
    *,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    return repair_plan(
        run_dir,
        repository_root=repository_root,
    )


def validate_bound_repair_plan(
    run_dir: Path,
    *,
    repository_root: Path | None = None,
) -> tuple[dict[str, Any], str]:
    run_dir = _resolve_run_directory(run_dir)
    plan_path = run_dir / REPAIR_PLAN_RELATIVE
    if not plan_path.is_file() or plan_path.is_symlink():
        raise ValueError("invalid run requires a current bound repair plan")
    plan = read_json(plan_path)
    if not isinstance(plan, dict):
        raise ValueError("repair plan is not an object")
    status = status_run(run_dir)
    if status.get("state") == "complete":
        raise ValueError("complete run is immutable")
    if status.get("state") == "cancelled":
        raise ValueError("cancelled run is terminal")
    repository = _bound_repository_root(run_dir, repository_root)
    report = run_fresh_validator(
        run_dir,
        repository_root=repository,
        preseal=False,
        require_complete=False,
    )
    errors = _repair_errors(report)
    if not errors:
        raise ValueError("repair plan is stale because the parent is now valid")
    expected = _bound_plan_document(
        run_dir,
        repository_root=repository,
        status=status,
        errors=errors,
        report=report,
    )
    if plan != expected:
        raise ValueError("repair plan is tampered or stale")
    return plan, str(expected["run_snapshot_sha256"])


def resume_lifecycle_run(
    run_dir: Path,
    packet: Mapping[str, Any] | None = None,
    *,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    run_dir = _resolve_run_directory(run_dir)
    status = status_run(run_dir)
    if status.get("state") == "cancelled":
        raise ValueError("cannot resume cancelled run")
    if status.get("state") == "complete":
        return status
    if status.get("state") == "initialized":
        if packet is not None:
            raise ValueError("initialized resume does not accept an analysis packet")
        return prepare_initialized_run(
            run_dir,
            repository_root=repository_root,
        )
    plan_path = run_dir / REPAIR_PLAN_RELATIVE
    if plan_path.is_file() or status.get("state") == "invalid":
        plan, snapshot_sha256 = validate_bound_repair_plan(
            run_dir,
            repository_root=repository_root,
        )
        contract = read_json(run_dir / "run-contract.json")
        if not isinstance(contract, Mapping):
            raise ValueError("run contract is not an object")
        if (
            contract.get("contract_profile") == PRODUCTION_CONTRACT_PROFILE
            and packet is not None
        ):
            raise ValueError("production repair owns its fresh authoring packet")
        child = repair_run(
            run_dir,
            reason=(
                "resume consumed bound repair plan at "
                f"{plan['earliest_invalid_phase']}"
            ),
            replacement_packet=packet,
            repository_root=repository_root,
            validated_plan=plan,
            validated_parent_snapshot_sha256=snapshot_sha256,
        )
        return status_run(child)
    return resume_run(
        run_dir,
        packet,
        repository_root=repository_root,
    )
