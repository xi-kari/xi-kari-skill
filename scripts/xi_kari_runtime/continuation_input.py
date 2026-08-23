"""Runtime-bound closed-input restoration for production continuations."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .authoring import require_base_authoring_provider
from .canonical_json import (
    canonical_bytes,
    read_bounded_regular_file,
    read_json_text,
    sha256_bytes,
    sha256_json,
)
from .closed_input import validate_frozen_closed_input_materials
from .phase_chain import compute_record_sha256, load_phase_records
from .problem_contract import contract_hash, validate_problem_contract


BASE_REQUEST_RELATIVE = "authoring/XK01-base-authoring-request.json"
BASE_RECEIPT_RELATIVE = "authoring/XK01-base-authoring-receipt.json"
SEMANTIC_TRACE_RELATIVE = "authoring/XK01-semantic-read-trace.json"
USER_MATERIAL_FIELDS = (
    "source_id",
    "title",
    "content",
    "published_at",
    "event_at",
)
MAX_BASE_REQUEST_BYTES = 256 * 1024 * 1024
MAX_RUNTIME_RECORD_BYTES = 16 * 1024 * 1024


def _read_canonical_object(
    path: Path, *, label: str, limit: int
) -> tuple[dict[str, Any], bytes]:
    try:
        payload = read_bounded_regular_file(path, limit=limit)
        value = read_json_text(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError(f"closed-input parent {label} is invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"closed-input parent {label} is not an object")
    if payload != canonical_bytes(value) + b"\n":
        raise ValueError(f"closed-input parent {label} is not canonical JSON")
    return value, payload


def _require_phase_binding(
    run_dir: Path,
    *,
    phase: str,
    relative: str,
    payload: bytes,
) -> None:
    records = load_phase_records(run_dir)
    expected_index = int(phase.removeprefix("XK"))
    if len(records) <= expected_index:
        raise ValueError(f"closed-input parent has no {phase} runtime binding")
    predecessor: str | None = None
    for index, record in enumerate(records[: expected_index + 1]):
        expected_phase = f"XK{index}"
        if (
            record.get("phase") != expected_phase
            or record.get("index") != index
            or record.get("predecessor_sha256") != predecessor
            or record.get("record_sha256") != compute_record_sha256(record)
        ):
            raise ValueError(
                f"closed-input parent {expected_phase} runtime binding is invalid"
            )
        predecessor = record.get("record_sha256")
    bindings = records[expected_index].get("artifact_bindings")
    if not isinstance(bindings, list):
        raise ValueError(f"closed-input parent {phase} artifact bindings are invalid")
    matches = [
        binding
        for binding in bindings
        if isinstance(binding, Mapping) and binding.get("path") == relative
    ]
    if len(matches) != 1 or matches[0].get("sha256") != sha256_bytes(payload):
        raise ValueError(
            f"closed-input parent {relative} differs from its {phase} runtime binding"
        )


def load_runtime_bound_closed_input_materials(
    run_dir: Path, contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    parent = Path(run_dir).resolve()
    disk_contract, contract_bytes = _read_canonical_object(
        parent / "run-contract.json",
        label="run contract",
        limit=MAX_RUNTIME_RECORD_BYTES,
    )
    if disk_contract != dict(contract):
        raise ValueError("closed-input parent contract changed during restoration")
    _require_phase_binding(
        parent,
        phase="XK0",
        relative="run-contract.json",
        payload=contract_bytes,
    )

    problem_contract = disk_contract.get("problem_contract")
    evidence_cutoff = disk_contract.get("evidence_cutoff")
    try:
        validated_problem = validate_problem_contract(
            problem_contract if isinstance(problem_contract, Mapping) else {},
            mode="closed-input",
        )
    except ValueError as exc:
        raise ValueError(
            f"closed-input parent problem contract is invalid: {exc}"
        ) from exc
    if (
        disk_contract.get("mode") != "closed-input"
        or not isinstance(problem_contract, Mapping)
        or validated_problem != dict(problem_contract)
        or not isinstance(evidence_cutoff, str)
        or problem_contract.get("evidence_cutoff") != evidence_cutoff
        or disk_contract.get("problem_contract_sha256")
        != contract_hash(problem_contract)
    ):
        raise ValueError("closed-input parent mode or evidence cutoff binding is invalid")

    trace, trace_bytes = _read_canonical_object(
        parent / SEMANTIC_TRACE_RELATIVE,
        label="semantic read trace",
        limit=MAX_RUNTIME_RECORD_BYTES,
    )
    _require_phase_binding(
        parent,
        phase="XK1",
        relative=SEMANTIC_TRACE_RELATIVE,
        payload=trace_bytes,
    )
    if (
        trace.get("schema_id") != "xi-kari.v2.semantic-read-trace"
        or trace.get("schema_version") != 1
        or trace.get("run_id") != disk_contract.get("run_id")
        or trace.get("contract_profile") != disk_contract.get("contract_profile")
    ):
        raise ValueError("closed-input parent semantic trace binding is invalid")
    receipt, _receipt_bytes = _read_canonical_object(
        parent / BASE_RECEIPT_RELATIVE,
        label="base authoring receipt",
        limit=MAX_RUNTIME_RECORD_BYTES,
    )
    if trace.get("base_authoring_execution") != receipt:
        raise ValueError(
            "closed-input parent base authoring receipt differs from its runtime trace"
        )
    if (
        receipt.get("schema_id") != "xi-kari.v2.base-authoring-execution"
        or receipt.get("schema_version") != 1
        or receipt.get("protocol") != "xi-kari.v2.base-authoring/v1"
        or receipt.get("run_id") != disk_contract.get("run_id")
        or receipt.get("request_path") != BASE_REQUEST_RELATIVE
        or receipt.get("exit_status") != 0
        or receipt.get("receipt_sha256")
        != sha256_json(
            {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        )
    ):
        raise ValueError("closed-input parent base authoring receipt binding is invalid")

    request, request_bytes = _read_canonical_object(
        parent / BASE_REQUEST_RELATIVE,
        label="base authoring request",
        limit=MAX_BASE_REQUEST_BYTES,
    )
    if (
        receipt.get("input_sha256") != sha256_bytes(request_bytes)
        or receipt.get("input_byte_count") != len(request_bytes)
    ):
        raise ValueError("closed-input parent base authoring request hash differs")
    if (
        request.get("schema_id") != "xi-kari.v2.base-authoring-request"
        or request.get("schema_version") != 1
        or request.get("protocol") != "xi-kari.v2.base-authoring/v1"
        or request.get("run_id") != disk_contract.get("run_id")
        or request.get("mode") != disk_contract.get("mode")
        or request.get("problem_contract") != problem_contract
    ):
        raise ValueError(
            "closed-input parent base request differs from the parent contract"
        )

    source_inputs = request.get("source_inputs")
    if not isinstance(source_inputs, Mapping):
        raise ValueError("closed-input parent base request has no source inputs")
    base_provider = source_inputs.get("base_provider_binding")
    try:
        require_base_authoring_provider(
            base_provider,
            mode="closed-input",
            verify_executable=False,
        )
    except ValueError as exc:
        raise ValueError(
            f"closed-input parent base provider binding is invalid: {exc}"
        ) from exc
    if (
        receipt.get("provider_binding_sha256") != sha256_json(dict(base_provider))
        or receipt.get("provider_executable_sha256")
        != base_provider.get("executable_sha256")
        or receipt.get("provider_argv_sha256") != base_provider.get("argv_sha256")
    ):
        raise ValueError("closed-input parent base provider receipt differs")
    persisted = source_inputs.get("closed_input_materials")
    manifest = source_inputs.get("frozen_material_manifest")
    normalized = validate_frozen_closed_input_materials(
        persisted,
        manifest,
        evidence_cutoff=evidence_cutoff,
    )
    if persisted != normalized:
        raise ValueError("closed-input parent material order differs from its frozen order")
    return [
        {field: material[field] for field in USER_MATERIAL_FIELDS if field in material}
        for material in normalized
    ]


__all__ = ["load_runtime_bound_closed_input_materials"]
