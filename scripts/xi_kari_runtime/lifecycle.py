"""CLI lifecycle orchestration for isolated Xi-Kari runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .authority import validator_set_sha256
from .canonical_json import (
    read_json,
    sha256_file,
    sha256_json,
)
from .contracts import (
    PRODUCTION_CONTRACT_PROFILE,
    derive_repair_scope,
    repair_phase_events_sha256,
)
from .materialization import (
    _bound_repository_root,
    _resolve_run_directory,
    prepare_run,
    repair_plan,
    resume_run,
    status_run,
)
from .repair import repair_run, repair_snapshot_sha256
from .validation import run_fresh_validator, validator_fingerprint, validate_run


REPAIR_PLAN_RELATIVE = Path("continuation/repair-plan.json")


def require_cli_start_profile(contract_profile: str) -> None:
    if contract_profile != PRODUCTION_CONTRACT_PROFILE:
        raise ValueError(f"unsupported CLI start profile: {contract_profile}")


def initialize_run(runs_root: Path, **kwargs: Any) -> dict[str, Any]:
    """Perform read-only preflight without fabricating XK0 or semantic receipts."""
    require_cli_start_profile(str(kwargs.get("contract_profile", "")))
    return prepare_run(runs_root, **kwargs)


def validate_lifecycle_run(
    run_dir: Path,
    *,
    repository_root: Path | None,
    validation_boundary: str,
    require_complete: bool,
) -> dict[str, Any]:
    status_run(run_dir)
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
        "schema_id": "xi-kari.v3.repair-plan",
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
