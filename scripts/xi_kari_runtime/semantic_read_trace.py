"""Runtime-owned binding and validation for the 21-volume semantic read trace."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import os
from pathlib import Path
import re
import stat
from typing import Any

from .canonical_json import read_json, sha256_file, sha256_json
from .contracts import PRODUCTION_CONTRACT_PROFILE


INPUT_SCHEMA_ID = "xi-kari.v2.semantic-read-trace-input"
ARTIFACT_SCHEMA_ID = "xi-kari.v2.semantic-read-trace"
RECEIPT_PROTOCOL = "xi-kari.v2.semantic-read-import-receipt/v1"
MODEL_RECORD_FIELDS = frozenset(
    {
        "reader_unit",
        "synthesis",
        "semantic_observations",
        "continuity_with_previous",
        "problem_relation",
        "source_undefined_refs",
    }
)
BOUND_RECORD_FIELDS = MODEL_RECORD_FIELDS | {
    "index",
    "sequence",
    "source_binding",
}
CONTINUITY_FIELDS = frozenset(
    {"previous_reader_unit", "relation", "explanation"}
)
OBSERVATION_FIELDS = frozenset(
    {"proposition", "role", "source_anchor_refs"}
)
PROBLEM_RELATION_FIELDS = frozenset({"status", "rationale"})
CONTINUITY_RELATIONS = frozenset(
    {"extends", "qualifies", "limits", "instantiates"}
)
PROBLEM_RELATION_STATUSES = frozenset(
    {"applied", "boundary_only", "not_applicable"}
)
SOURCE_ANCHOR = re.compile(r"^V82-(?:P\d{4}|T\d{3})$")
ARTIFACT_FIELDS = frozenset(
    {
        "schema_id",
        "schema_version",
        "run_id",
        "contract_profile",
        "source_manifest_sha256",
        "reader_unit_count",
        "import_receipt",
        "import_receipt_sha256",
        "records",
        "complete",
    }
)
OPTIONAL_BASE_EXECUTION_FIELD = "base_authoring_execution"
RECEIPT_FIELDS = frozenset(
    {
        "protocol",
        "receipt_id",
        "run_id",
        "problem_contract_sha256",
        "source_manifest_sha256",
        "xk0_record_sha256",
        "semantic_payload_sha256",
        "input_file_sha256",
        "input_byte_count",
        "input_path",
        "runtime_importer_pid",
        "imported_at",
    }
)


def _require_exact_fields(
    value: Any, expected: frozenset[str], *, label: str
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ValueError(f"{label} fields are not exact")
    return value


def _text(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")
    return value.strip()


def _text_list(
    value: Any,
    *,
    label: str,
    require_nonempty: bool,
) -> list[str]:
    if not isinstance(value, list) or (require_nonempty and not value):
        qualifier = "a non-empty list" if require_nonempty else "a list"
        raise ValueError(f"{label} must be {qualifier}")
    result = [_text(item, label=f"{label} item") for item in value]
    if len(result) != len(set(result)):
        raise ValueError(f"{label} contains duplicate values")
    return result


def _ordinary_input_file(path: str | Path) -> Path:
    raw = Path(path).expanduser()
    candidate = raw if raw.is_absolute() else Path.cwd() / raw
    candidate = candidate.absolute()
    current = Path(candidate.anchor)
    for part in candidate.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise ValueError(
                f"semantic read trace input path contains a symlink: {current}"
            )
    try:
        metadata = candidate.stat(follow_symlinks=False)
    except OSError as exc:
        raise ValueError(
            f"semantic read trace input is unavailable: {candidate}"
        ) from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError(
            f"semantic read trace input is not a regular file: {candidate}"
        )
    return candidate.resolve(strict=True)


def _source_context(
    repository_root: Path,
    source_lock: Mapping[str, Any],
    source_events: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], str, list[str], dict[str, set[str]]]:
    source_root = Path(repository_root) / "references/source/v8.2"
    manifest_path = source_root / "source-manifest.json"
    manifest = read_json(manifest_path)
    if not isinstance(manifest, Mapping):
        raise ValueError("semantic read trace source manifest is not an object")
    manifest_sha256 = sha256_file(manifest_path)
    reader_units = manifest.get("reader_units")
    if (
        not isinstance(reader_units, list)
        or len(reader_units) != 21
        or any(not isinstance(unit, str) or not unit for unit in reader_units)
    ):
        raise ValueError("semantic read trace source manifest has no exact 21-unit sequence")
    if source_lock.get("source_manifest_sha256") != manifest_sha256:
        raise ValueError("semantic read trace source lock manifest binding differs")
    if source_lock.get("reader_sequence") != reader_units:
        raise ValueError("semantic read trace source lock reader sequence differs")
    membership = {unit: set() for unit in reader_units}
    for event in source_events:
        unit = event.get("reader_unit")
        anchor = event.get("source_anchor")
        if unit in membership and isinstance(anchor, str):
            membership[unit].add(anchor)
    if any(not membership[unit] for unit in reader_units):
        raise ValueError("semantic read trace source event ownership is incomplete")
    return manifest, manifest_sha256, list(reader_units), membership


def _semantic_projection(record: Mapping[str, Any]) -> dict[str, Any]:
    return {field: deepcopy(record[field]) for field in MODEL_RECORD_FIELDS}


def _normalise_boilerplate(value: str) -> str:
    return " ".join(value.casefold().split())


def _bound_records(
    payload: Any,
    *,
    repository_root: Path,
    source_lock: Mapping[str, Any],
    source_events: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    document = _require_exact_fields(
        payload,
        frozenset({"schema_id", "schema_version", "records"}),
        label="semantic read trace input",
    )
    if (
        document.get("schema_id") != INPUT_SCHEMA_ID
        or document.get("schema_version") != 1
    ):
        raise ValueError("semantic read trace input schema identity is invalid")
    manifest, manifest_sha256, reader_units, membership = _source_context(
        repository_root, source_lock, source_events
    )
    records = document.get("records")
    if not isinstance(records, list) or len(records) != 21:
        raise ValueError("semantic read trace must contain exactly 21 records")
    observed_units = [
        record.get("reader_unit") if isinstance(record, Mapping) else None
        for record in records
    ]
    if observed_units != reader_units:
        raise ValueError(
            "semantic read trace reader units differ from manifest order"
        )
    reader_hashes = manifest.get("reader_file_sha256")
    if not isinstance(reader_hashes, Mapping):
        raise ValueError("semantic read trace manifest has no reader file hashes")
    output: list[dict[str, Any]] = []
    boilerplate_owners: dict[str, str] = {}
    source_root = Path(repository_root) / "references/source/v8.2"
    for index, (raw_record, unit) in enumerate(
        zip(records, reader_units, strict=True)
    ):
        record = _require_exact_fields(
            raw_record,
            MODEL_RECORD_FIELDS,
            label=f"semantic read trace record {index + 1}",
        )
        synthesis = _text(
            record.get("synthesis"),
            label=f"semantic read trace record {index + 1} synthesis",
        )
        observations = record.get("semantic_observations")
        if not isinstance(observations, list) or not observations:
            raise ValueError(
                f"semantic read trace record {index + 1} requires an observation"
            )
        bound_observations: list[dict[str, Any]] = []
        semantic_text = [synthesis]
        for observation_index, raw_observation in enumerate(observations, start=1):
            observation = _require_exact_fields(
                raw_observation,
                OBSERVATION_FIELDS,
                label=(
                    f"semantic read trace record {index + 1} observation "
                    f"{observation_index}"
                ),
            )
            proposition = _text(
                observation.get("proposition"),
                label=(
                    f"semantic read trace record {index + 1} observation "
                    f"{observation_index} proposition"
                ),
            )
            role = _text(
                observation.get("role"),
                label=(
                    f"semantic read trace record {index + 1} observation "
                    f"{observation_index} role"
                ),
            )
            anchors = _text_list(
                observation.get("source_anchor_refs"),
                label=(
                    f"semantic read trace record {index + 1} observation "
                    f"{observation_index} source anchors"
                ),
                require_nonempty=True,
            )
            for anchor in anchors:
                if SOURCE_ANCHOR.fullmatch(anchor) is None:
                    raise ValueError(
                        f"semantic read trace source anchor is invalid: {anchor}"
                    )
                if anchor not in membership[unit]:
                    raise ValueError(
                        "semantic read trace source anchor crosses reader units: "
                        f"{unit}: {anchor}"
                    )
            semantic_text.extend((proposition, role))
            bound_observations.append(
                {
                    "proposition": proposition,
                    "role": role,
                    "source_anchor_refs": anchors,
                }
            )

        continuity = _require_exact_fields(
            record.get("continuity_with_previous"),
            CONTINUITY_FIELDS,
            label=f"semantic read trace record {index + 1} continuity",
        )
        relation = continuity.get("relation")
        previous = continuity.get("previous_reader_unit")
        explanation = _text(
            continuity.get("explanation"),
            label=f"semantic read trace record {index + 1} continuity explanation",
        )
        if index == 0:
            if previous is not None or relation != "root":
                raise ValueError(
                    "semantic read trace first continuity must be root with null predecessor"
                )
        elif (
            previous != reader_units[index - 1]
            or relation not in CONTINUITY_RELATIONS
        ):
            raise ValueError(
                "semantic read trace continuity does not bind the previous reader unit"
            )

        problem_relation = _require_exact_fields(
            record.get("problem_relation"),
            PROBLEM_RELATION_FIELDS,
            label=f"semantic read trace record {index + 1} problem relation",
        )
        problem_status = problem_relation.get("status")
        if problem_status not in PROBLEM_RELATION_STATUSES:
            raise ValueError(
                f"semantic read trace record {index + 1} problem relation status is invalid"
            )
        rationale = _text(
            problem_relation.get("rationale"),
            label=f"semantic read trace record {index + 1} problem rationale",
        )
        undefined_refs = _text_list(
            record.get("source_undefined_refs"),
            label=f"semantic read trace record {index + 1} source undefined refs",
            require_nonempty=False,
        )
        semantic_text.extend((explanation, rationale))
        boilerplate = _normalise_boilerplate("\n".join(semantic_text))
        previous_owner = boilerplate_owners.setdefault(boilerplate, unit)
        if previous_owner != unit:
            raise ValueError(
                "semantic read trace contains repeated boilerplate across reader units: "
                f"{previous_owner}, {unit}"
            )

        source_file = f"reader/{unit}"
        source_path = source_root / source_file
        expected_sha256 = reader_hashes.get(source_file)
        observed_sha256 = sha256_file(source_path)
        if expected_sha256 != observed_sha256:
            raise ValueError(
                f"semantic read trace reader hash differs from manifest: {unit}"
            )
        output.append(
            {
                "index": index,
                "sequence": index + 1,
                "reader_unit": unit,
                "source_binding": {
                    "path": f"references/source/v8.2/{source_file}",
                    "source_file": source_file,
                    "expected_sha256": expected_sha256,
                    "observed_sha256": observed_sha256,
                    "source_manifest_sha256": manifest_sha256,
                },
                "synthesis": synthesis,
                "semantic_observations": bound_observations,
                "continuity_with_previous": {
                    "previous_reader_unit": previous,
                    "relation": relation,
                    "explanation": explanation,
                },
                "problem_relation": {
                    "status": problem_status,
                    "rationale": rationale,
                },
                "source_undefined_refs": undefined_refs,
            }
        )
    return output, manifest_sha256


def _receipt_id(receipt: Mapping[str, Any]) -> str:
    projection = {key: value for key, value in receipt.items() if key != "receipt_id"}
    return f"XK01-SR-{sha256_json(projection)[:32]}"


def validate_semantic_read_trace_input(
    value: Any,
    *,
    repository_root: Path,
    source_lock: Mapping[str, Any],
    source_events: Sequence[Mapping[str, Any]],
) -> None:
    _bound_records(
        value,
        repository_root=repository_root,
        source_lock=source_lock,
        source_events=source_events,
    )


def build_semantic_read_trace(
    input_path: str | Path,
    *,
    repository_root: Path,
    run_contract: Mapping[str, Any],
    source_lock: Mapping[str, Any],
    source_events: Sequence[Mapping[str, Any]],
    xk0_record_sha256: str,
    imported_at: str,
    base_authoring_execution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    path = _ordinary_input_file(input_path)
    payload = read_json(path)
    records, manifest_sha256 = _bound_records(
        payload,
        repository_root=repository_root,
        source_lock=source_lock,
        source_events=source_events,
    )
    semantic_payload = {
        "schema_id": INPUT_SCHEMA_ID,
        "schema_version": 1,
        "records": [_semantic_projection(record) for record in records],
    }
    receipt: dict[str, Any] = {
        "protocol": RECEIPT_PROTOCOL,
        "receipt_id": "",
        "run_id": run_contract.get("run_id"),
        "problem_contract_sha256": run_contract.get("problem_contract_sha256"),
        "source_manifest_sha256": manifest_sha256,
        "xk0_record_sha256": xk0_record_sha256,
        "semantic_payload_sha256": sha256_json(semantic_payload),
        "input_file_sha256": sha256_file(path),
        "input_byte_count": path.stat().st_size,
        "input_path": str(path),
        "runtime_importer_pid": os.getpid(),
        "imported_at": imported_at,
    }
    receipt["receipt_id"] = _receipt_id(receipt)
    artifact = {
        "schema_id": ARTIFACT_SCHEMA_ID,
        "schema_version": 1,
        "run_id": run_contract.get("run_id"),
        "contract_profile": PRODUCTION_CONTRACT_PROFILE,
        "source_manifest_sha256": manifest_sha256,
        "reader_unit_count": 21,
        "import_receipt": receipt,
        "import_receipt_sha256": sha256_json(receipt),
        "records": records,
        "complete": True,
    }
    if base_authoring_execution is not None:
        if not isinstance(base_authoring_execution, Mapping):
            raise ValueError("base authoring execution receipt is not an object")
        artifact[OPTIONAL_BASE_EXECUTION_FIELD] = deepcopy(
            dict(base_authoring_execution)
        )
    return artifact


def validate_semantic_read_trace(
    value: Any,
    *,
    repository_root: Path,
    run_contract: Mapping[str, Any],
    source_lock: Mapping[str, Any],
    source_events: Sequence[Mapping[str, Any]],
    xk0_record_sha256: str,
) -> list[str]:
    try:
        if not isinstance(value, Mapping):
            raise ValueError("XK1 semantic read trace is not an object")
        allowed_fields = set(ARTIFACT_FIELDS) | {OPTIONAL_BASE_EXECUTION_FIELD}
        if set(value) not in (set(ARTIFACT_FIELDS), allowed_fields):
            raise ValueError("XK1 semantic read trace fields are not exact")
        artifact = value
        if (
            artifact.get("schema_id") != ARTIFACT_SCHEMA_ID
            or artifact.get("schema_version") != 1
            or artifact.get("reader_unit_count") != 21
            or artifact.get("complete") is not True
        ):
            raise ValueError("XK1 semantic read trace identity is invalid")
        if artifact.get("run_id") != run_contract.get("run_id"):
            raise ValueError("XK1 semantic read trace run_id differs from run contract")
        if (
            artifact.get("contract_profile") != PRODUCTION_CONTRACT_PROFILE
            or run_contract.get("contract_profile") != PRODUCTION_CONTRACT_PROFILE
        ):
            raise ValueError("XK1 semantic read trace is not bound to production profile")
        raw_records = artifact.get("records")
        if not isinstance(raw_records, list):
            raise ValueError("XK1 semantic read trace records are not a list")
        semantic_records: list[dict[str, Any]] = []
        for index, raw_record in enumerate(raw_records, start=1):
            record = _require_exact_fields(
                raw_record,
                BOUND_RECORD_FIELDS,
                label=f"XK1 semantic read trace record {index}",
            )
            semantic_records.append(_semantic_projection(record))
        if OPTIONAL_BASE_EXECUTION_FIELD in artifact:
            execution = artifact[OPTIONAL_BASE_EXECUTION_FIELD]
            if not isinstance(execution, Mapping):
                raise ValueError("XK1 base authoring execution receipt is not an object")
            if execution.get("run_id") != run_contract.get("run_id"):
                raise ValueError("XK1 base authoring execution run_id differs")
            if execution.get("semantic_read_trace_sha256") != sha256_json(
                {
                    "schema_id": INPUT_SCHEMA_ID,
                    "schema_version": 1,
                    "records": semantic_records,
                }
            ):
                raise ValueError("XK1 base authoring execution trace hash differs")
        payload = {
            "schema_id": INPUT_SCHEMA_ID,
            "schema_version": 1,
            "records": semantic_records,
        }
        expected_records, manifest_sha256 = _bound_records(
            payload,
            repository_root=repository_root,
            source_lock=source_lock,
            source_events=source_events,
        )
        if raw_records != expected_records:
            raise ValueError("XK1 semantic read trace differs from fresh source binding")
        if artifact.get("source_manifest_sha256") != manifest_sha256:
            raise ValueError("XK1 semantic read trace manifest binding differs")
        receipt = _require_exact_fields(
            artifact.get("import_receipt"),
            RECEIPT_FIELDS,
            label="XK1 semantic read import receipt",
        )
        expected_receipt_values = {
            "protocol": RECEIPT_PROTOCOL,
            "run_id": run_contract.get("run_id"),
            "problem_contract_sha256": run_contract.get(
                "problem_contract_sha256"
            ),
            "source_manifest_sha256": manifest_sha256,
            "xk0_record_sha256": xk0_record_sha256,
            "semantic_payload_sha256": sha256_json(payload),
        }
        for field, expected in expected_receipt_values.items():
            if receipt.get(field) != expected:
                raise ValueError(
                    f"XK1 semantic read import receipt binding differs: {field}"
                )
        if receipt.get("receipt_id") != _receipt_id(receipt):
            raise ValueError("XK1 semantic read import receipt id differs")
        if (
            not isinstance(receipt.get("runtime_importer_pid"), int)
            or isinstance(receipt.get("runtime_importer_pid"), bool)
            or receipt.get("runtime_importer_pid", 0) < 1
        ):
            raise ValueError("XK1 semantic read import receipt pid is invalid")
        if (
            not isinstance(receipt.get("input_byte_count"), int)
            or isinstance(receipt.get("input_byte_count"), bool)
            or receipt.get("input_byte_count", 0) < 2
        ):
            raise ValueError("XK1 semantic read import receipt byte count is invalid")
        if not isinstance(receipt.get("input_path"), str) or not Path(
            receipt["input_path"]
        ).is_absolute():
            raise ValueError("XK1 semantic read import receipt path is invalid")
        if artifact.get("import_receipt_sha256") != sha256_json(receipt):
            raise ValueError("XK1 semantic read import receipt hash differs")
    except (KeyError, OSError, TypeError, ValueError) as exc:
        return [str(exc)]
    return []


__all__ = (
    "ARTIFACT_SCHEMA_ID",
    "INPUT_SCHEMA_ID",
    "PRODUCTION_CONTRACT_PROFILE",
    "build_semantic_read_trace",
    "validate_semantic_read_trace_input",
    "validate_semantic_read_trace",
)
