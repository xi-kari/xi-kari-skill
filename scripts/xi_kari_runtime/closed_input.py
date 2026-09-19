"""Runtime-owned freezing and validation for Xi-Kari closed-input materials.

Closed-input is a different evidence mode, not an empty open-world search.  The
caller supplies a finite set of material bodies; this module freezes their
identity and bytes before a model process starts.  Later stages can therefore
rebuild the boundary from disk instead of trusting a model-authored source
record or manifest.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime, time, timezone
import re
from typing import Any

from .canonical_json import (
    canonical_bytes,
    read_json_text,
    sha256_bytes,
    sha256_json,
    sha256_text,
)


CLOSED_INPUT_SCHEMA_ID = "xi-kari.v3.closed-input-materials"
CLOSED_INPUT_SCHEMA_VERSION = 1
CLOSED_INPUT_ORIGIN = "user_material"
MATERIAL_FIELDS = frozenset(
    {"source_id", "title", "content", "published_at", "event_at"}
)
MODEL_CLOSED_SOURCE_FIELDS = MATERIAL_FIELDS | {"origin"}
REQUIRED_MATERIAL_FIELDS = frozenset({"source_id", "title", "content"})
MAX_MATERIALS = 10_000
MAX_SOURCE_ID_LENGTH = 128
MAX_TITLE_LENGTH = 16_384
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
CLOSED_QUERY_DIRECTIONS = {
    "current_baseline",
    "mechanism_support",
    "counterevidence",
    "comparable_case",
    "affected_low_power_position",
    "authoritative_definition",
}
CLOSED_RECEIPT_FIELDS = frozenset(
    {
        "schema_id",
        "schema_version",
        "run_id",
        "web_search_executed",
        "event_stream_sha256",
        "event_count",
        "base_request_sha256",
        "semantic_retrieval_sha256",
        "frozen_material_manifest_sha256",
        "retrieval_sha256",
        "provider_binding_sha256",
        "adapter_executable_sha256",
        "child_pid",
        "started_at",
        "completed_at",
        "exit_status",
        "thread_id",
        "query_bindings",
        "source_bindings",
        "receipt_sha256",
    }
)


def _text(value: Any, *, field: str, max_length: int) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError(f"closed-input material {field} must be non-empty text")
    if len(value) > max_length:
        raise ValueError(f"closed-input material {field} exceeds its size limit")
    return value.strip() if field != "content" else value


def _date_value(value: str, *, field: str) -> datetime:
    try:
        if "T" in value:
            candidate = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                raise ValueError
            return parsed.astimezone(timezone.utc)
        return datetime.combine(
            date.fromisoformat(value), time.min, tzinfo=timezone.utc
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"closed-input material {field} must be an ISO date or date-time"
        ) from exc


def _validate_date_boundary(
    value: Any, *, field: str, evidence_cutoff: str | None
) -> str | None:
    if value is None:
        return None
    candidate = _text(value, field=field, max_length=128)
    endpoints = candidate.split("/")
    if any(not endpoint for endpoint in endpoints):
        raise ValueError(f"closed-input material {field} has an empty endpoint")
    parsed = [_date_value(endpoint, field=field) for endpoint in endpoints]
    if parsed != sorted(parsed):
        raise ValueError(f"closed-input material {field} endpoints are not ordered")
    if evidence_cutoff is not None:
        cutoff = _date_value(evidence_cutoff, field="evidence_cutoff")
        if any(endpoint > cutoff for endpoint in parsed):
            raise ValueError(
                f"closed-input material {field} is after the evidence cutoff"
            )
    return candidate


def _validate_source_id(value: Any) -> str:
    source_id = _text(value, field="source_id", max_length=MAX_SOURCE_ID_LENGTH)
    # IDs are data, not paths.  Reject separators, drive syntax, control
    # characters and traversal spellings before they can reach a filename.
    if source_id in {".", ".."} or re.search(r"[\\/:\x00-\x1f\x7f]", source_id):
        raise ValueError("closed-input material source_id is not path-safe")
    return source_id


def material_manifest(materials: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    entries = sorted(
        [
            {
                "source_id": str(material["source_id"]),
                "content_sha256": str(material["content_sha256"]),
            }
            for material in materials
        ],
        key=lambda item: item["source_id"],
    )
    return {"materials": entries, "manifest_sha256": sha256_json(entries)}


def freeze_closed_input_materials(
    materials: Sequence[Mapping[str, Any]],
    *,
    evidence_cutoff: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Normalize and freeze user material records deterministically.

    The returned records are runtime-owned: ``origin`` is always
    ``user_material`` and ``content_sha256`` is computed from the exact UTF-8
    content supplied by the caller.  Input order is discarded deliberately so
    the same set of materials yields the same request/manifest.
    """

    if isinstance(materials, (str, bytes, bytearray)) or not isinstance(
        materials, Sequence
    ):
        raise ValueError("closed-input materials must be a sequence of objects")
    if not materials:
        raise ValueError("closed-input materials must be a non-empty sequence")
    if len(materials) > MAX_MATERIALS:
        raise ValueError("closed-input materials exceed the item limit")

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(materials, start=1):
        if not isinstance(raw, Mapping):
            raise ValueError(f"closed-input material {index} must be an object")
        unknown = set(raw) - MATERIAL_FIELDS
        if unknown:
            raise ValueError(
                "closed-input material contains unsupported field: "
                + sorted(unknown)[0]
            )
        missing = REQUIRED_MATERIAL_FIELDS - set(raw)
        if missing:
            raise ValueError(
                "closed-input material is missing required field: "
                + sorted(missing)[0]
            )
        source_id = _validate_source_id(raw["source_id"])
        if source_id in seen:
            raise ValueError(f"duplicate closed-input material source_id: {source_id}")
        seen.add(source_id)
        title = _text(raw["title"], field="title", max_length=MAX_TITLE_LENGTH)
        content = _text(raw["content"], field="content", max_length=MAX_CONTENT_LENGTH)
        record: dict[str, Any] = {
            "source_id": source_id,
            "origin": CLOSED_INPUT_ORIGIN,
            "title": title,
            "content": content,
            "content_sha256": sha256_text(content),
        }
        for field in ("published_at", "event_at"):
            value = _validate_date_boundary(
                raw.get(field), field=field, evidence_cutoff=evidence_cutoff
            )
            if value is not None:
                record[field] = value
        normalized.append(record)

    normalized.sort(key=lambda item: item["source_id"])
    return normalized, material_manifest(normalized)


def validate_frozen_closed_input_materials(
    materials: Any,
    manifest: Any,
    *,
    evidence_cutoff: str | None = None,
) -> list[dict[str, Any]]:
    """Recompute and validate a persisted frozen material set."""

    if not isinstance(materials, list):
        raise ValueError("closed-input persisted materials must be a list")
    raw_materials: list[dict[str, Any]] = []
    for index, material in enumerate(materials, start=1):
        if not isinstance(material, Mapping):
            raise ValueError(f"closed-input persisted material {index} is not an object")
        if set(material) - (MATERIAL_FIELDS | {"origin", "content_sha256"}):
            raise ValueError(
                f"closed-input persisted material {index} has unsupported fields"
            )
        if material.get("origin") != CLOSED_INPUT_ORIGIN:
            raise ValueError(
                f"closed-input persisted material {index} origin is invalid"
            )
        content = material.get("content")
        if not isinstance(content, str) or material.get("content_sha256") != sha256_text(
            content
        ):
            raise ValueError(
                f"closed-input persisted material {index} content hash differs"
            )
        raw_materials.append(
            {key: material[key] for key in MATERIAL_FIELDS if key in material}
        )
    normalized, expected_manifest = freeze_closed_input_materials(
        raw_materials, evidence_cutoff=evidence_cutoff
    )
    if manifest != expected_manifest:
        raise ValueError("closed-input frozen material manifest differs from materials")
    return normalized


def validate_closed_input_execution(
    receipt: Any,
    retrieval: Any,
    *,
    run_id: str,
    evidence_cutoff: str,
    semantic_document: Any,
    event_stream: bytes,
    base_request: Any,
    base_request_bytes: bytes,
    base_receipt: Any,
) -> list[str]:
    """Freshly rebuild a closed-input projection from persisted bytes."""

    errors: list[str] = []
    if not isinstance(receipt, Mapping) or set(receipt) != CLOSED_RECEIPT_FIELDS:
        return ["closed-input execution receipt fields are not exact"]
    if (
        receipt.get("schema_id") != "xi-kari.v3.closed-input-execution"
        or receipt.get("schema_version") != 1
        or receipt.get("run_id") != run_id
        or receipt.get("web_search_executed") is not False
        or receipt.get("exit_status") != 0
    ):
        errors.append("closed-input execution receipt identity is invalid")
    for field in (
        "event_stream_sha256",
        "base_request_sha256",
        "semantic_retrieval_sha256",
        "frozen_material_manifest_sha256",
        "retrieval_sha256",
        "provider_binding_sha256",
        "adapter_executable_sha256",
        "receipt_sha256",
    ):
        try:
            _require_hash(receipt.get(field), field=field)
        except ValueError as exc:
            errors.append(str(exc))
    if receipt.get("receipt_sha256") != sha256_json(
        {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    ):
        errors.append("closed-input execution receipt self-hash differs")
    if receipt.get("event_stream_sha256") != sha256_bytes(event_stream):
        errors.append("closed-input event stream hash differs")
    if receipt.get("base_request_sha256") != sha256_bytes(base_request_bytes):
        errors.append("closed-input base request hash differs")
    try:
        events, thread_id = _event_objects(event_stream)
        if receipt.get("event_count") != len(events):
            errors.append("closed-input event count differs")
        if receipt.get("thread_id") != thread_id:
            errors.append("closed-input thread identity differs")
    except ValueError as exc:
        errors.append(str(exc))

    if not isinstance(base_request, Mapping):
        errors.append("closed-input base request is not an object")
        return errors
    if base_request_bytes != canonical_bytes(dict(base_request)) + b"\n":
        errors.append("closed-input base request is not canonical JSON")
    if base_request.get("run_id") != run_id or base_request.get("mode") != "closed-input":
        errors.append("closed-input base request binding differs")
    source_inputs = base_request.get("source_inputs")
    if not isinstance(source_inputs, Mapping):
        errors.append("closed-input base request source_inputs is invalid")
        return errors
    manifest = source_inputs.get("frozen_material_manifest")
    try:
        frozen = validate_frozen_closed_input_materials(
            source_inputs.get("closed_input_materials"),
            manifest,
            evidence_cutoff=evidence_cutoff,
        )
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    if receipt.get("frozen_material_manifest_sha256") != sha256_json(manifest):
        errors.append("closed-input receipt manifest hash differs")

    if not isinstance(semantic_document, Mapping):
        errors.append("closed-input semantic retrieval is not an object")
        return errors
    if (
        semantic_document.get("schema_id")
        != "xi-kari.v3.retrieval-semantic-input"
        or semantic_document.get("schema_version") != 1
        or semantic_document.get("run_id") != run_id
        or semantic_document.get("mode") != "closed-input"
    ):
        errors.append("closed-input semantic retrieval binding differs")
        return errors
    semantic = {
        key: value
        for key, value in semantic_document.items()
        if key not in {"schema_id", "schema_version", "run_id", "mode"}
    }
    if semantic.get("frozen_material_manifest") != manifest:
        errors.append("closed-input semantic manifest differs from the base request")
    semantic_for_projection = {
        "mode": "closed-input",
        **{
            key: value
            for key, value in semantic.items()
            if key != "frozen_material_manifest"
        },
    }
    try:
        expected_semantic, expected_retrieval, query_bindings, source_bindings = (
            _normalize_closed_semantic(
                semantic_for_projection,
                frozen,
                manifest=manifest,
                run_id=run_id,
                completed_at=str(receipt.get("completed_at")),
            )
        )
        if expected_semantic != semantic:
            errors.append("closed-input semantic retrieval normalization differs")
        if expected_retrieval != retrieval:
            errors.append("closed-input runtime retrieval projection differs")
        if receipt.get("query_bindings") != query_bindings:
            errors.append("closed-input query bindings differ")
        if receipt.get("source_bindings") != source_bindings:
            errors.append("closed-input source bindings differ")
    except ValueError as exc:
        errors.append(str(exc))
    if receipt.get("semantic_retrieval_sha256") != sha256_json(semantic):
        errors.append("closed-input semantic retrieval hash differs")
    if not isinstance(retrieval, Mapping) or receipt.get(
        "retrieval_sha256"
    ) != sha256_json(dict(retrieval)):
        errors.append("closed-input retrieval hash differs")

    if not isinstance(base_receipt, Mapping):
        errors.append("closed-input base authoring receipt is invalid")
        return errors
    for receipt_field, base_field in (
        ("provider_binding_sha256", "provider_binding_sha256"),
        ("adapter_executable_sha256", "adapter_executable_sha256"),
        ("child_pid", "child_pid"),
        ("started_at", "started_at"),
        ("completed_at", "completed_at"),
        ("thread_id", "thread_id"),
    ):
        if receipt.get(receipt_field) != base_receipt.get(base_field):
            errors.append(f"closed-input {receipt_field} differs from base authoring")
    try:
        started = _date_value(str(receipt.get("started_at")), field="started_at")
        completed = _date_value(
            str(receipt.get("completed_at")), field="completed_at"
        )
        cutoff = _date_value(evidence_cutoff, field="evidence_cutoff")
        if started > completed or completed > cutoff:
            errors.append("closed-input execution time is outside the evidence cutoff")
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def _require_list(value: Any, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"closed-input retrieval {field} must be a list")
    return value


def _require_hash(value: Any, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"closed-input {field} must be a SHA-256")
    return value


def _event_objects(event_stream: bytes) -> tuple[list[dict[str, Any]], str]:
    if not isinstance(event_stream, bytes) or not event_stream:
        raise ValueError("closed-input event stream is empty")
    try:
        events = [
            read_json_text(line)
            for line in event_stream.decode("utf-8").splitlines()
        ]
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError("closed-input event stream is not JSONL") from exc
    if not events or not all(isinstance(event, dict) for event in events):
        raise ValueError("closed-input event stream contains a non-object event")
    if events[0].get("type") != "thread.started" or events[-1].get("type") != "turn.completed":
        raise ValueError("closed-input event stream has no complete turn")

    def contains_web_search(value: Any) -> bool:
        if isinstance(value, Mapping):
            if value.get("type") in {"web_search", "web.run", "web_search_call"}:
                return True
            return any(contains_web_search(child) for child in value.values())
        if isinstance(value, list):
            return any(contains_web_search(child) for child in value)
        return False

    if any(contains_web_search(event) for event in events):
        raise ValueError("closed-input event stream contains web retrieval events")
    thread_id = events[0].get("thread_id")
    if not isinstance(thread_id, str) or not thread_id.strip():
        raise ValueError("closed-input event stream has no thread identity")
    return events, thread_id


def _normalize_closed_semantic(
    retrieval: Mapping[str, Any],
    frozen_materials: Sequence[Mapping[str, Any]],
    *,
    manifest: Mapping[str, Any],
    run_id: str,
    completed_at: str,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]], list[dict[str, Any]]]:
    """Validate model semantics against frozen materials and add host fields."""

    if set(retrieval) != {
        "mode",
        "queries",
        "sources",
        "assessments",
        "saturation_status",
        "capability_gap",
        "remaining_unknowns",
    }:
        raise ValueError("closed-input retrieval contains runtime or unsupported fields")
    if retrieval.get("mode") != "closed-input":
        raise ValueError("closed-input retrieval mode differs from execution mode")
    frozen_by_id = {item["source_id"]: item for item in frozen_materials}
    queries_raw = _require_list(retrieval.get("queries"), field="queries")
    if not queries_raw:
        raise ValueError("closed-input retrieval requires at least one query")
    semantic_queries: list[dict[str, str]] = []
    seen_query_texts: set[str] = set()
    for index, raw in enumerate(queries_raw, start=1):
        if not isinstance(raw, Mapping) or set(raw) != {"direction", "query", "purpose"}:
            raise ValueError(f"closed-input query {index} fields are not exact")
        direction = _text(raw.get("direction"), field="query direction", max_length=256)
        query = _text(raw.get("query"), field="query", max_length=16_384)
        purpose = _text(raw.get("purpose"), field="query purpose", max_length=16_384)
        if direction not in CLOSED_QUERY_DIRECTIONS:
            raise ValueError(f"closed-input query direction is invalid: {direction}")
        if query in seen_query_texts:
            raise ValueError("closed-input query texts must be unique")
        seen_query_texts.add(query)
        semantic_queries.append({"direction": direction, "query": query, "purpose": purpose})

    sources_raw = _require_list(retrieval.get("sources"), field="sources")
    if not sources_raw:
        raise ValueError("closed-input retrieval requires frozen material sources")
    semantic_sources: list[dict[str, Any]] = []
    seen_source_ids: set[str] = set()
    for index, raw in enumerate(sources_raw, start=1):
        if not isinstance(raw, Mapping):
            raise ValueError(f"closed-input source {index} must be an object")
        unsupported = set(raw) - MODEL_CLOSED_SOURCE_FIELDS
        if unsupported:
            raise ValueError(
                "closed-input model source contains unsupported field: "
                + sorted(unsupported)[0]
            )
        source_id = _validate_source_id(raw.get("source_id"))
        if source_id in seen_source_ids:
            raise ValueError(f"duplicate closed-input model source: {source_id}")
        seen_source_ids.add(source_id)
        frozen = frozen_by_id.get(source_id)
        if frozen is None:
            raise ValueError(f"closed-input model source is not frozen: {source_id}")
        title = _text(raw.get("title"), field="source title", max_length=MAX_TITLE_LENGTH)
        content = _text(raw.get("content"), field="source content", max_length=MAX_CONTENT_LENGTH)
        if title != frozen["title"] or content != frozen["content"]:
            raise ValueError(f"closed-input model source does not match frozen material: {source_id}")
        for field in ("published_at", "event_at"):
            if raw.get(field) != frozen.get(field):
                raise ValueError(f"closed-input model source date differs from frozen material: {source_id}")
        if raw.get("origin") not in {"user", "user_material", "provided"}:
            raise ValueError(f"closed-input model source origin is invalid: {source_id}")
        semantic_source = {
            "source_id": source_id,
            "origin": CLOSED_INPUT_ORIGIN,
            "title": frozen["title"],
            "content": frozen["content"],
        }
        for field in ("published_at", "event_at"):
            if field in frozen:
                semantic_source[field] = frozen[field]
        semantic_sources.append(semantic_source)
    if seen_source_ids != set(frozen_by_id):
        missing = sorted(set(frozen_by_id) - seen_source_ids)
        raise ValueError("closed-input model omitted frozen material: " + missing[0])

    assessments_raw = _require_list(retrieval.get("assessments"), field="assessments")
    if len(assessments_raw) != len(frozen_by_id):
        raise ValueError("closed-input requires one assessment per frozen material")
    semantic_assessments: list[dict[str, Any]] = []
    assessment_ids: set[str] = set()
    for index, raw in enumerate(assessments_raw, start=1):
        if not isinstance(raw, Mapping):
            raise ValueError(f"closed-input assessment {index} must be an object")
        if "source_id" not in raw:
            raise ValueError(f"closed-input assessment {index} has no source_id")
        source_id = _validate_source_id(raw["source_id"])
        if source_id not in frozen_by_id or source_id in assessment_ids:
            raise ValueError(f"closed-input assessment source is invalid: {source_id}")
        if any(
            key in raw
            for key in ("source_url", "source_lineage_urls", "conflict_source_urls")
        ):
            raise ValueError("closed-input assessment cannot carry external URL fields")
        assessment_ids.add(source_id)
        normalized = deepcopy_mapping(raw)
        normalized["source_id"] = source_id
        for field in ("source_lineage", "conflict_source_ids"):
            values = normalized.get(field, [])
            if not isinstance(values, list) or len(values) != len(set(values)):
                raise ValueError(f"closed-input assessment {field} is invalid")
            if any(_validate_source_id(item) not in frozen_by_id for item in values):
                raise ValueError(f"closed-input assessment {field} does not resolve")
            normalized[field] = [_validate_source_id(item) for item in values]
        semantic_assessments.append(normalized)
    if assessment_ids != set(frozen_by_id):
        raise ValueError("closed-input assessments do not cover every frozen material")

    saturation = _text(
        retrieval.get("saturation_status"), field="saturation_status", max_length=256
    )
    capability_gap = _text(
        retrieval.get("capability_gap"), field="capability_gap", max_length=16_384
    )
    unknowns = _require_list(retrieval.get("remaining_unknowns"), field="remaining_unknowns")
    normalized_unknowns = [
        _text(value, field="remaining_unknowns item", max_length=16_384)
        for value in unknowns
    ]
    semantic = {
        "queries": semantic_queries,
        "sources": semantic_sources,
        "assessments": semantic_assessments,
        "saturation_status": saturation,
        "capability_gap": capability_gap,
        "remaining_unknowns": normalized_unknowns,
        "frozen_material_manifest": deepcopy_mapping(manifest),
    }
    source_ids = sorted(frozen_by_id)
    projected_sources: list[dict[str, Any]] = []
    for source_id in source_ids:
        source = dict(frozen_by_id[source_id])
        source["accessed_at"] = completed_at
        source["run_id"] = run_id
        projected_sources.append(source)
    projected_queries: list[dict[str, Any]] = []
    query_bindings: list[dict[str, str | list[str]]] = []
    for index, query in enumerate(semantic_queries, start=1):
        query_id = (
            f"QUERY-CLOSED-{index:02d}-"
            + sha256_json(
                {
                    "run_id": run_id,
                    "direction": query["direction"],
                    "query": query["query"],
                }
            )[:16].upper()
        )
        projected_queries.append(
            {
                "query_id": query_id,
                "direction": query["direction"],
                "query": query["query"],
                "status": "executed",
                "executed_at": completed_at,
                "result_source_ids": source_ids,
            }
        )
        query_bindings.append(
            {
                "query_id": query_id,
                "query_sha256": sha256_text(query["query"]),
                "purpose_sha256": sha256_text(query["purpose"]),
                "result_source_ids": source_ids,
            }
        )
    projected = {
        "mode": "closed-input",
        "queries": projected_queries,
        "sources": projected_sources,
        "assessments": semantic_assessments,
        "saturation_status": saturation,
        "capability_gap": capability_gap,
        "remaining_unknowns": normalized_unknowns,
        "frozen_material_manifest": deepcopy_mapping(manifest),
    }
    return semantic, projected, query_bindings, [
        {
            "source_id": source_id,
            "content_sha256": frozen_by_id[source_id]["content_sha256"],
        }
        for source_id in source_ids
    ]


def deepcopy_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    """Small JSON-only deep copy without importing the runtime packet helpers."""

    if not isinstance(value, Mapping):
        raise ValueError("expected a mapping")
    result: dict[str, Any] = {}
    for key, child in value.items():
        if isinstance(child, Mapping):
            result[str(key)] = deepcopy_mapping(child)
        elif isinstance(child, list):
            result[str(key)] = [
                deepcopy_mapping(item) if isinstance(item, Mapping) else item
                for item in child
            ]
        else:
            result[str(key)] = child
    return result


__all__ = [
    "CLOSED_INPUT_ORIGIN",
    "CLOSED_INPUT_SCHEMA_ID",
    "CLOSED_INPUT_SCHEMA_VERSION",
    "freeze_closed_input_materials",
    "material_manifest",
    "validate_closed_input_execution",
    "validate_frozen_closed_input_materials",
]
