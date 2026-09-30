"""Import a preexisting observed audit without changing its original run identity."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .canonical_json import (
    atomic_write_bytes, canonical_bytes, confined_path, read_bounded_regular_file,
    read_json_text, sha256_bytes, sha256_json,
)
from .temporal_audit import AUDIT_PATH, MAX_FILE_BYTES, TemporalAudit, load_temporal_audit


CONTEXT_PATH = "authoring/XK02-temporal-audit-context.json"
SCHEMA_ID = "xi-kari.runtime.temporal-audit-context"
SNAPSHOT_ROOT = "temporal-evidence/source/"
MAX_CONTEXT_BYTES = 256 * 1024 * 1024
_CREATION_KEY = object()


def _raw(root: Path, relative: str) -> bytes:
    try:
        return read_bounded_regular_file(confined_path(root, relative, must_exist=True), limit=MAX_FILE_BYTES)
    except (OSError, ValueError, TypeError):
        raise ValueError("bound temporal material is unavailable or indirect") from None


def _capture(audit: TemporalAudit) -> tuple[list[dict[str, Any]], dict[str, bytes]]:
    from .materialization import _require_external_runs_root
    _require_external_runs_root(audit.run_dir, Path(__file__).resolve().parents[2])
    events = audit._read_events()
    raw_audit = _raw(audit.run_dir, AUDIT_PATH)
    if sha256_bytes(raw_audit) != audit.expected_audit_sha256:
        raise ValueError("bound temporal audit changed")
    files = {AUDIT_PATH: raw_audit}
    for event in events:
        material = event["material"]
        raw = _raw(audit.run_dir, material["path"])
        if sha256_bytes(raw) != material["sha256"] or len(raw) != material["bytes"]:
            raise ValueError("bound temporal original changed")
        files[material["path"]] = raw
        if event["kind"] != "material_read":
            snapshot = _raw(audit.run_dir, event["snapshot"])
            value = read_json_text(snapshot.decode("utf-8"))
            expected = event["contract_sha256"] if event["kind"] == "preregistration" else event["evaluation_sha256"]
            if sha256_json(value) != expected:
                raise ValueError("bound temporal frozen snapshot changed")
            files[event["snapshot"]] = snapshot
        if sum(map(len, files.values())) > MAX_CONTEXT_BYTES:
            raise ValueError("bound temporal context exceeds its capture limit")
    members = [{"source_path": path, "snapshot_path": SNAPSHOT_ROOT + path,
                "sha256": sha256_bytes(raw), "bytes": len(raw)} for path, raw in sorted(files.items())]
    return members, files


def _binding(raw: bytes, descriptor: Mapping[str, Any]) -> dict[str, Any]:
    return {"context_sha256": sha256_bytes(raw), "audit_sha256": descriptor["audit_sha256"],
            "evidence_scope": "isolated_runtime_reads"}


def _matches_contract(descriptor: Mapping[str, Any], contract: Mapping[str, Any]) -> None:
    if contract.get("contract_profile") != "production-authoring-v4" or descriptor["run_id"] != contract.get("run_id") or descriptor["problem_contract_sha256"] != contract.get("problem_contract_sha256"):
        raise ValueError("temporal context differs from the frozen execution contract")


class TemporalAuditContext:
    """An execution-owned context; its public summary never contains source paths."""

    __slots__ = ("_audit", "_raw_descriptor", "_files")

    def __init__(self, audit: TemporalAudit, raw: bytes, files: dict[str, bytes], *, _key: object):
        if _key is not _CREATION_KEY or type(audit) is not TemporalAudit:
            raise ValueError("temporal context requires runtime-observed input")
        self._audit, self._raw_descriptor, self._files = audit, raw, dict(files)

    @property
    def audit(self) -> TemporalAudit:
        return self._audit

    @property
    def binding(self) -> dict[str, Any]:
        return _binding(self._raw_descriptor, read_json_text(self._raw_descriptor.decode("utf-8")))

    @property
    def artifact_paths(self) -> tuple[str, ...]:
        descriptor = read_json_text(self._raw_descriptor.decode("utf-8"))
        return (CONTEXT_PATH, *(row["snapshot_path"] for row in descriptor["members"]))


def freeze_temporal_context_v4(audit: object, *, run_id: str,
        problem_contract_sha256: str, repository_root: Path | None = None) -> TemporalAuditContext | None:
    """Bind only already observed inputs; never create registration from author output."""
    if audit is None:
        return None
    if type(audit) is not TemporalAudit:
        raise ValueError("temporal context cannot be supplied as author JSON")
    from .materialization import _require_external_runs_root
    from .v4_contracts import validate_versioned_schema
    repo = Path(repository_root or Path(__file__).resolve().parents[2]).resolve()
    _require_external_runs_root(audit.run_dir, repo)
    members, files = _capture(audit)
    descriptor = {
        "schema_id": SCHEMA_ID, "schema_version": 1, "run_id": run_id,
        "problem_contract_sha256": problem_contract_sha256, "evidence_scope": "isolated_runtime_reads",
        "origin_run_directory": str(audit.run_dir), "origin_run_path_sha256": sha256_json(str(audit.run_dir)),
        "audit_sha256": audit.expected_audit_sha256, "members": members,
    }
    validate_versioned_schema("xk-temporal-audit-context.schema.json", descriptor, repository_root=repo)
    return TemporalAuditContext(audit, canonical_bytes(descriptor) + b"\n", files, _key=_CREATION_KEY)


def persist_temporal_context_v4(context: TemporalAuditContext | None, *, run_dir: Path,
        run_contract: Mapping[str, Any]) -> None:
    if context is None:
        return
    if type(context) is not TemporalAuditContext:
        raise ValueError("temporal context is not runtime-owned")
    descriptor = read_json_text(context._raw_descriptor.decode("utf-8"))
    _matches_contract(descriptor, run_contract)
    members, current = _capture(context.audit)
    if members != descriptor["members"] or current != context._files:
        raise ValueError("temporal source changed after the execute input was frozen")
    root = Path(run_dir).resolve()
    from .materialization import _require_external_runs_root
    _require_external_runs_root(root, Path(__file__).resolve().parents[2])
    if root == context.audit.run_dir:
        raise ValueError("temporal import must preserve its distinct original audit root")
    if (root / CONTEXT_PATH).exists() or (root / SNAPSHOT_ROOT).exists():
        raise ValueError("temporal context cannot replace an existing execution import")
    for member in members:
        atomic_write_bytes(confined_path(root, member["snapshot_path"]), current[member["source_path"]])
    atomic_write_bytes(confined_path(root, CONTEXT_PATH), context._raw_descriptor)


def load_temporal_context_v4(run_dir: Path, *, run_contract: Mapping[str, Any],
        expected_binding: Mapping[str, Any] | None,
        repository_root: Path | None = None) -> TemporalAuditContext | None:
    """Use the independently verified base-request binding, never a self-reported pin."""
    root = Path(run_dir).resolve()
    if expected_binding is None:
        if (root / CONTEXT_PATH).exists() or (root / SNAPSHOT_ROOT).exists():
            raise ValueError("temporal context has no independent execute input binding")
        return None
    from .v4_contracts import validate_versioned_schema
    from .materialization import _require_external_runs_root
    repo = Path(repository_root or Path(__file__).resolve().parents[2]).resolve()
    try:
        _require_external_runs_root(root, repo)
        raw = _raw(root, CONTEXT_PATH)
        descriptor = read_json_text(raw.decode("utf-8"))
        validate_versioned_schema("xk-temporal-audit-context.schema.json", descriptor, repository_root=repo)
        if dict(expected_binding) != _binding(raw, descriptor):
            raise ValueError()
        _matches_contract(descriptor, run_contract)
        origin = Path(descriptor["origin_run_directory"])
        if not origin.is_absolute() or str(origin.resolve()) != str(origin) or origin.resolve() == root or sha256_json(str(origin)) != descriptor["origin_run_path_sha256"]:
            raise ValueError()
        _require_external_runs_root(origin, repo)
        audit = load_temporal_audit(origin, expected_audit_sha256=descriptor["audit_sha256"])
        members, files = _capture(audit)
        if descriptor["members"] != members:
            raise ValueError()
        snapshot_root = root / SNAPSHOT_ROOT
        actual_paths = {path.relative_to(root).as_posix() for path in snapshot_root.rglob("*") if path.is_file()}
        if actual_paths != {member["snapshot_path"] for member in members}:
            raise ValueError()
        for member in members:
            if _raw(root, member["snapshot_path"]) != files[member["source_path"]]:
                raise ValueError()
        return TemporalAuditContext(audit, raw, files, _key=_CREATION_KEY)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        raise ValueError("temporal context, original root, or exact snapshot binding is invalid") from None


__all__ = ("CONTEXT_PATH", "TemporalAuditContext", "freeze_temporal_context_v4",
           "persist_temporal_context_v4", "load_temporal_context_v4")
