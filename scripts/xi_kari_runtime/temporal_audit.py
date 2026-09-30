"""Run-local preregistration and result-access evidence from actual file reads."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import time
from typing import Any
from uuid import uuid4

from .canonical_json import (
    atomic_write_json, confined_path,
    read_bounded_regular_file, read_json_text, sha256_bytes, sha256_json,
)
from .problem_contract import parse_instant


AUDIT_PATH = "temporal-audit/audit.json"
SCHEMA_ID = "xi-kari.runtime.temporal-audit"
MAX_FILE_BYTES = 64 * 1024 * 1024
_LOAD_TOKEN = object()


class TemporalAuditError(ValueError):
    """Temporal evidence is absent, changed, or outside its recorded scope."""


def _read(root: Path, relative: str) -> bytes:
    try:
        return read_bounded_regular_file(
            confined_path(root, relative, must_exist=True), limit=MAX_FILE_BYTES,
        )
    except (OSError, ValueError, TypeError):
        raise TemporalAuditError("temporal material is unavailable or invalid") from None


def _json(raw: bytes) -> dict[str, Any]:
    try:
        value = read_json_text(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except (UnicodeError, ValueError, TypeError):
        raise TemporalAuditError("temporal material is not a JSON object") from None


def _digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _contract(raw: Mapping[str, Any], kind: str, at: str) -> dict[str, Any]:
    if kind not in {"empirical", "history"} or not isinstance(raw.get("instance_id"), str) or not raw["instance_id"]:
        raise TemporalAuditError("temporal registration identity is invalid")
    if set(raw) & {"qualification", "result", "formal_result", "temporal_audit"}:
        raise TemporalAuditError("temporal registration contains result controls")
    result = deepcopy(dict(raw))
    result["preregistration_timestamp" if kind == "empirical" else "registered_at"] = at
    result["preregistration_status"] = "frozen_before_evidence"
    return result


def _evaluation(raw: Mapping[str, Any], kind: str, first_at: str, at: str) -> dict[str, Any]:
    if set(raw) & {"qualification", "formal_result", "temporal_audit"}:
        raise TemporalAuditError("temporal evaluation contains cached controls")
    result = deepcopy(dict(raw))
    if kind == "empirical":
        result.update(first_result_access_timestamp=first_at, result_timestamp=at,
                      completion_status="completed_from_frozen")
    else:
        result["outcome_first_seen_at"] = first_at
    return result


def _refs(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        return set().union(*(_refs(item) for item in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(_refs(item) for item in value)) if value else set()
    return {value} if isinstance(value, str) and value else set()


def _required_refs(evaluation: Mapping[str, Any], kind: str) -> tuple[set[str], set[str], set[str]]:
    fields = ("evidence_claim_ids", "prerequisite_claim_ids", "dimension_claim_ids", "null_gate_claim_ids") if kind == "empirical" else ("out_of_sample_claim_ids", "criterion_claim_ids", "null_claim_ids")
    evidence = _refs(evaluation.get("evidence_claim_ids", [])) if kind == "empirical" else set()
    analysis = _refs(evaluation.get("analysis_artifact_claim_ids", []))
    all_refs = analysis | set().union(*(_refs(evaluation.get(field, [])) for field in fields))
    return all_refs, evidence, analysis


def _accesses(events: list[dict[str, Any]], evaluation: Mapping[str, Any], kind: str) -> list[dict[str, Any]]:
    required, evidence, analysis = _required_refs(evaluation, kind)
    reads = [event for event in events if event["kind"] == "material_read"]
    matched = [event for event in reads if required.intersection(event["claim_ids"])]
    covered = set().union(*(set(event["claim_ids"]) for event in matched)) if matched else set()
    evidence_covered = set().union(*(set(event["claim_ids"]) for event in matched if event["role"] == "evidence")) if matched else set()
    analysis_covered = set().union(*(set(event["claim_ids"]) for event in matched if event["role"] == "analysis")) if matched else set()
    if not required or not analysis or required - covered or evidence - evidence_covered or analysis - analysis_covered:
        raise TemporalAuditError("temporal evidence does not cover the evaluation materials")
    hashes = {event["material"]["sha256"] for event in matched}
    paths = {event["material"]["path"] for event in matched}
    return [event for event in reads if event["material"]["sha256"] in hashes or event["material"]["path"] in paths]


class TemporalAuditWriter:
    """Observe local reads before exposing result bytes to the semantic author.

    This observes only this isolated runtime. It cannot certify an external
    experiment's preregistration, an earlier reader's access, or world facts.
    """

    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir).resolve()
        package = Path(__file__).resolve().parents[2]
        if self.run_dir == package or package in self.run_dir.parents:
            raise TemporalAuditError("temporal audit must be outside the skill package")
        self.run_dir.mkdir(parents=True, exist_ok=True)
        audit_dir = confined_path(self.run_dir, "temporal-audit")
        try:
            audit_dir.mkdir(exist_ok=False)
        except OSError:
            raise TemporalAuditError("temporal audit requires a fresh run-local directory") from None
        self._document = {
            "schema_id": SCHEMA_ID, "schema_version": 1, "audit_id": str(uuid4()),
            "run_path_sha256": sha256_json(str(self.run_dir)),
            "evidence_scope": "isolated_runtime_reads", "sealed": False, "events": [],
        }
        self._closed = False
        self._persist()

    def _persist(self) -> None:
        atomic_write_json(confined_path(self.run_dir, AUDIT_PATH), self._document)

    def _event(self, kind: str) -> dict[str, Any]:
        if self._closed:
            raise TemporalAuditError("temporal audit is sealed")
        return {"event_id": len(self._document["events"]) + 1, "kind": kind,
                "at": _now(), "monotonic_ns": time.monotonic_ns()}

    def _material(self, relative: str, raw: bytes) -> dict[str, Any]:
        relative = confined_path(self.run_dir, relative, must_exist=True).relative_to(self.run_dir).as_posix()
        return {"path": relative, "sha256": sha256_bytes(raw), "bytes": len(raw)}

    def _append(self, event: dict[str, Any]) -> None:
        self._document["events"].append(event)
        self._persist()

    def freeze_preregistration(self, relative_path: str, *, kind: str) -> dict[str, Any]:
        event = self._event("preregistration")
        raw = _read(self.run_dir, relative_path)
        contract = _contract(_json(raw), kind, event["at"])
        if any(row.get("instance_id") == contract["instance_id"] for row in self._document["events"] if row["kind"] == "preregistration"):
            raise TemporalAuditError("temporal instance already has a frozen registration")
        snapshot = f"temporal-audit/contracts/{event['event_id']}.json"
        atomic_write_json(confined_path(self.run_dir, snapshot), contract)
        event.update(instance_id=contract["instance_id"], contract_kind=kind,
                     material=self._material(relative_path, raw), snapshot=snapshot,
                     contract_sha256=sha256_json(contract))
        self._append(event)
        return deepcopy(contract)

    def read_material(self, relative_path: str, *, claim_ids: list[str], role: str) -> bytes:
        event = self._event("material_read")
        if role not in {"evidence", "analysis"} or not isinstance(claim_ids, list) or not claim_ids or any(not isinstance(ref, str) or not ref for ref in claim_ids) or len(set(claim_ids)) != len(claim_ids):
            raise TemporalAuditError("temporal material role or claim binding is invalid")
        raw = _read(self.run_dir, relative_path)
        event.update(material=self._material(relative_path, raw), claim_ids=list(claim_ids), role=role)
        self._append(event)
        return raw

    def complete_evaluation(self, instance_id: str, relative_path: str) -> dict[str, Any]:
        event = self._event("evaluation_completed")
        registrations = [row for row in self._document["events"] if row["kind"] == "preregistration" and row["instance_id"] == instance_id]
        if len(registrations) != 1 or any(row["kind"] == "evaluation_completed" and row["instance_id"] == instance_id for row in self._document["events"]):
            raise TemporalAuditError("temporal evaluation requires one uncompleted registration")
        registration = registrations[0]
        raw = _read(self.run_dir, relative_path)
        source = _json(raw)
        accesses = _accesses(self._document["events"], source, registration["contract_kind"])
        first = min(accesses, key=lambda row: row["event_id"])
        evaluation = _evaluation(source, registration["contract_kind"], first["at"], event["at"])
        snapshot = f"temporal-audit/evaluations/{event['event_id']}.json"
        atomic_write_json(confined_path(self.run_dir, snapshot), evaluation)
        event.update(instance_id=instance_id, contract_kind=registration["contract_kind"],
                     registration_event_id=registration["event_id"],
                     contract_sha256=registration["contract_sha256"],
                     material=self._material(relative_path, raw), snapshot=snapshot,
                     evaluation_sha256=sha256_json(evaluation))
        self._append(event)
        return deepcopy(evaluation)

    def seal(self) -> TemporalAudit:
        if self._closed:
            raise TemporalAuditError("temporal audit is already sealed")
        self._document["sealed"] = True
        self._persist()
        self._closed = True
        return load_temporal_audit(self.run_dir, expected_audit_sha256=sha256_bytes(_read(self.run_dir, AUDIT_PATH)))


class TemporalAudit:
    """A pinned disk reader; no stored qualification or verification verdict."""

    __slots__ = ("_run_dir", "_expected_audit_sha256")

    def __init__(self, run_dir: Path, expected_audit_sha256: str, *, _token: object):
        if _token is not _LOAD_TOKEN:
            raise TemporalAuditError("temporal audit requires a runtime-owned disk binding")
        self._run_dir = Path(run_dir).resolve()
        self._expected_audit_sha256 = expected_audit_sha256

    @property
    def expected_audit_sha256(self) -> str:
        return self._expected_audit_sha256

    @property
    def run_dir(self) -> Path:
        return self._run_dir

    def _read_events(self) -> list[dict[str, Any]]:
        raw = _read(self._run_dir, AUDIT_PATH)
        if sha256_bytes(raw) != self._expected_audit_sha256:
            raise TemporalAuditError("temporal audit differs from its runtime commitment")
        document = _json(raw)
        if document.get("schema_id") != SCHEMA_ID or document.get("schema_version") != 1 or document.get("sealed") is not True or document.get("evidence_scope") != "isolated_runtime_reads" or document.get("run_path_sha256") != sha256_json(str(self._run_dir)):
            raise TemporalAuditError("temporal audit identity is invalid")
        events = document.get("events")
        if not isinstance(events, list):
            raise TemporalAuditError("temporal audit event sequence is invalid")
        last_time, last_tick = None, None
        registrations: dict[str, dict[str, Any]] = {}
        completions: set[str] = set()
        for index, event in enumerate(events, 1):
            if not isinstance(event, dict) or type(event.get("event_id")) is not int or event["event_id"] != index or event.get("kind") not in {"preregistration", "material_read", "evaluation_completed"}:
                raise TemporalAuditError("temporal audit event sequence is invalid")
            at = parse_instant(event.get("at"), field="temporal audit time")
            tick = event.get("monotonic_ns")
            if not isinstance(tick, int) or isinstance(tick, bool) or tick < 0 or (last_tick is not None and (tick < last_tick or at < last_time)):
                raise TemporalAuditError("temporal audit clock or ordering is invalid")
            last_time, last_tick = at, tick
            material = event.get("material")
            if not isinstance(material, dict) or not isinstance(material.get("path"), str) or not _digest(material.get("sha256")) or type(material.get("bytes")) is not int or material["bytes"] < 0:
                raise TemporalAuditError("temporal material identity is invalid")
            confined_path(self._run_dir, material["path"])
            if event["kind"] == "material_read":
                if event.get("role") not in {"evidence", "analysis"} or not isinstance(event.get("claim_ids"), list) or not event["claim_ids"] or any(not isinstance(ref, str) or not ref for ref in event["claim_ids"]) or len(event["claim_ids"]) != len(set(event["claim_ids"])):
                    raise TemporalAuditError("temporal material binding is invalid")
                continue
            if not isinstance(event.get("instance_id"), str) or not event["instance_id"] or event.get("contract_kind") not in {"empirical", "history"} or not _digest(event.get("contract_sha256")) or not isinstance(event.get("snapshot"), str):
                raise TemporalAuditError("temporal registration or completion identity is invalid")
            confined_path(self._run_dir, event["snapshot"])
            if event["kind"] == "preregistration":
                if event["instance_id"] in registrations:
                    raise TemporalAuditError("temporal preregistration version binding changed")
                registrations[event["instance_id"]] = event
            else:
                registration = registrations.get(event["instance_id"], {})
                if event["instance_id"] in completions or not _digest(event.get("evaluation_sha256")) or registration.get("event_id") != event.get("registration_event_id") or registration.get("contract_kind") != event["contract_kind"] or registration.get("contract_sha256") != event["contract_sha256"]:
                    raise TemporalAuditError("temporal evaluation version binding changed")
                completions.add(event["instance_id"])
        return events

    def _original(self, event: Mapping[str, Any]) -> bytes:
        material = event["material"]
        original = _read(self._run_dir, material["path"])
        if sha256_bytes(original) != material["sha256"] or len(original) != material["bytes"]:
            raise TemporalAuditError("temporal original material changed")
        return original

    def verify(self, kind: str, contract: Mapping[str, Any], evaluation: Mapping[str, Any]) -> dict[str, Any]:
        events = self._read_events()
        identifier = contract.get("instance_id")
        registrations = [row for row in events if row["kind"] == "preregistration" and row["instance_id"] == identifier]
        completions = [row for row in events if row["kind"] == "evaluation_completed" and row["instance_id"] == identifier]
        if len(registrations) != 1 or len(completions) != 1:
            raise TemporalAuditError("temporal binding lacks registration or completion")
        registration, completion = registrations[0], completions[0]
        if registration["contract_kind"] != kind or completion["contract_kind"] != kind or registration["contract_sha256"] != sha256_json(contract) or completion["contract_sha256"] != sha256_json(contract) or completion["evaluation_sha256"] != sha256_json(evaluation) or completion["registration_event_id"] != registration["event_id"]:
            raise TemporalAuditError("temporal binding differs from the evaluated scope or version")
        accesses = _accesses(events[:completion["event_id"] - 1], evaluation, kind)
        first = min(accesses, key=lambda row: row["event_id"])
        if not registration["event_id"] < first["event_id"] < completion["event_id"] or not parse_instant(registration["at"], field="registration") < parse_instant(first["at"], field="first result access") <= parse_instant(completion["at"], field="completion"):
            raise TemporalAuditError("preregistration does not precede first recorded result access")
        registered_snapshot = _json(_read(self._run_dir, registration["snapshot"]))
        completed_snapshot = _json(_read(self._run_dir, completion["snapshot"]))
        if registered_snapshot != contract or _contract(_json(self._original(registration)), kind, registration["at"]) != contract:
            raise TemporalAuditError("temporal preregistration original or snapshot changed")
        if completed_snapshot != evaluation or _evaluation(_json(self._original(completion)), kind, first["at"], completion["at"]) != evaluation:
            raise TemporalAuditError("temporal evaluation original or snapshot changed")
        for event in accesses:
            self._original(event)
        return {
            "status": "verified", "evidence_scope": "isolated_runtime_reads",
            "audit_sha256": self._expected_audit_sha256,
            "registration_event_id": registration["event_id"],
            "first_access_event_id": first["event_id"],
            "completion_event_id": completion["event_id"],
            "registration_timestamp": registration["at"],
            "first_access_timestamp": first["at"], "completion_timestamp": completion["at"],
            "material_sha256s": sorted({row["material"]["sha256"] for row in accesses}),
        }


def load_temporal_audit(run_dir: Path, *, expected_audit_sha256: str) -> TemporalAudit:
    """Load using a pin supplied by trusted runtime state, never author JSON.

    Fresh-process callers must obtain this pin from the enclosing verified
    execution binding. A hash copied from the audit itself has no authority.
    """
    if not _digest(expected_audit_sha256):
        raise TemporalAuditError("temporal audit requires a valid runtime commitment")
    audit = TemporalAudit(run_dir, expected_audit_sha256, _token=_LOAD_TOKEN)
    try:
        audit._read_events()
    except (KeyError, ValueError, TypeError, OSError):
        raise TemporalAuditError("temporal audit identity or event binding is invalid") from None
    return audit


def verify_temporal_binding(audit: object, *, kind: str, contract: Mapping[str, Any], evaluation: Mapping[str, Any]) -> dict[str, Any]:
    if type(audit) is not TemporalAudit:
        return {"status": "unverified", "reason": "runtime_temporal_evidence_missing"}
    try:
        return audit.verify(kind, contract, evaluation)
    except (TemporalAuditError, KeyError, TypeError, ValueError, OSError):
        return {"status": "unverified", "reason": "runtime_temporal_evidence_invalid"}


__all__ = ("TemporalAuditError", "TemporalAuditWriter", "TemporalAudit", "load_temporal_audit", "verify_temporal_binding")
