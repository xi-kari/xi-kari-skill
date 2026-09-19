"""Disk-authoritative XK0-XK12 event chain for isolated Xi-Kari runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .canonical_json import atomic_write_text, confined_path, read_json_text, sha256_file, sha256_json


PHASES = tuple(f"XK{index}" for index in range(13))
EVENTS_RELATIVE = "phase-events.jsonl"


def _events_path(run_dir: Path) -> Path:
    return Path(run_dir).resolve() / EVENTS_RELATIVE


def _paths(value: str | Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, str):
        return (Path(value).as_posix(),)
    return tuple(Path(item).as_posix() for item in value)


def _record_projection(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "record_sha256"}


def compute_record_sha256(record: dict[str, Any]) -> str:
    return sha256_json(_record_projection(record))


def load_phase_records(run_dir: Path) -> list[dict[str, Any]]:
    """Read the JSONL chain; tolerate the old phase-file layout only for migration diagnostics."""

    path = _events_path(run_dir)
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(read_json_from_text(line))
    return records


def read_json_from_text(text: str) -> dict[str, Any]:
    value = read_json_text(text)
    if not isinstance(value, dict):
        raise ValueError("phase event must be an object")
    return value


def _write_records(run_dir: Path, records: list[dict[str, Any]]) -> None:
    import json

    payload = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for record in records
    )
    atomic_write_text(_events_path(run_dir), payload)


def append_phase(
    run_dir: Path,
    *,
    run_id: str,
    phase: str,
    artifact_path: str | Iterable[str],
    input_sha256: str,
    created_at: str,
) -> dict[str, Any]:
    """Append one phase event, binding all files belonging to that phase."""

    if phase not in PHASES:
        raise ValueError(f"unknown Xi-Kari phase: {phase}")
    run_dir = Path(run_dir).resolve()
    paths = _paths(artifact_path)
    if not paths:
        raise ValueError("phase must bind at least one artifact")
    artifact_bindings: list[dict[str, str]] = []
    for relative in paths:
        path = confined_path(run_dir, relative, must_exist=True)
        artifact_bindings.append({"path": relative, "sha256": sha256_file(path)})
    records = load_phase_records(run_dir)
    index = PHASES.index(phase)
    if index < len(records):
        existing = records[index]
        if (
            existing.get("run_id") == run_id
            and existing.get("phase") == phase
            and existing.get("artifact_bindings") == artifact_bindings
            and existing.get("input_sha256") == input_sha256
        ):
            return existing
        raise ValueError(f"phase {phase} is already sealed with different bytes")
    if index != len(records):
        expected = PHASES[len(records)] if len(records) < len(PHASES) else "<complete>"
        raise ValueError(f"cannot append {phase}; next phase is {expected}")
    predecessor = records[-1]["record_sha256"] if records else None
    record: dict[str, Any] = {
        "schema_id": "xi-kari.v3.phase-event",
        "schema_version": 3,
        "run_id": run_id,
        "phase": phase,
        "index": index,
        "predecessor_sha256": predecessor,
        "input_sha256": input_sha256,
        "artifact_bindings": artifact_bindings,
        "created_at": created_at,
    }
    record["record_sha256"] = compute_record_sha256(record)
    _write_records(run_dir, [*records, record])
    return record


def validate_phase_chain(run_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    run_dir = Path(run_dir).resolve()
    errors: list[str] = []
    path = _events_path(run_dir)
    if path.is_symlink():
        return [], ["phase-events.jsonl is a symlink"]
    if not path.is_file():
        return [], ["missing phase-events.jsonl"]
    try:
        records = load_phase_records(run_dir)
    except Exception as exc:
        return [], [f"cannot read phase-events.jsonl: {exc}"]
    predecessor: str | None = None
    run_id: str | None = None
    for index, record in enumerate(records):
        phase = f"XK{index}"
        if record.get("phase") != phase or record.get("index") != index:
            errors.append(f"phase identity mismatch at index {index}")
        if run_id is None:
            run_id = record.get("run_id")
        elif record.get("run_id") != run_id:
            errors.append(f"run_id mismatch at {phase}")
        if record.get("predecessor_sha256") != predecessor:
            errors.append(f"predecessor mismatch at {phase}")
        if record.get("record_sha256") != compute_record_sha256(record):
            errors.append(f"record sha256 mismatch at {phase}")
        bindings = record.get("artifact_bindings")
        if not isinstance(bindings, list) or not bindings:
            errors.append(f"missing artifact bindings at {phase}")
        else:
            for binding in bindings:
                try:
                    path_value = binding["path"]
                    observed = sha256_file(confined_path(run_dir, path_value, must_exist=True))
                    if observed != binding.get("sha256"):
                        errors.append(f"artifact sha256 mismatch at {phase}: {path_value}")
                except Exception as exc:
                    errors.append(f"invalid artifact at {phase}: {exc}")
        predecessor = record.get("record_sha256")
    if len(records) > len(PHASES):
        errors.append("phase chain has more than XK12")
    return records, errors


PHASE_NAMES = PHASES
append_phase_record = append_phase
verify_phase_chain = validate_phase_chain
