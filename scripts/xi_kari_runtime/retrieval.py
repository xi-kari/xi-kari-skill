"""Source-read receipts and source-by-source retrieval assessment artifacts."""

from __future__ import annotations

from datetime import date, datetime, time, timezone
import re
import json
import unicodedata
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from .authority import validator_set_sha256
from .canonical_json import (
    atomic_write_json,
    confined_path,
    read_json,
    sha256_bytes,
    sha256_file,
    sha256_json,
    sha256_text,
)
from .problem_contract import parse_instant


ALLOWED_MODES = {"open-world", "closed-input"}
CLOSED_INPUT_ORIGINS = {"user", "user_material", "provided", "v8.3"}
ASSESSMENT_VERDICTS = {
    "admitted",
    "usable_with_limits",
    "rejected",
    "nonprobative",
}
ADMITTED_ASSESSMENT_VERDICTS = {"admitted", "usable_with_limits"}

FULL_PARAGRAPH_COUNT = 4631
FULL_TABLE_COUNT = 122
FULL_SOURCE_UNIT_COUNT = FULL_PARAGRAPH_COUNT + FULL_TABLE_COUNT
FULL_READER_UNIT_COUNT = 21
CONTENT_AUTHORITIES = frozenset(
    {"model-authored-excerpt", "host-observed", "unknown"}
)


def _normalise_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = " ".join(unicodedata.normalize("NFKC", value).split()).casefold()
    return value or None


def _normalise_publisher(value: Any) -> str | None:
    url = _normalise_url(value)
    return f"url:{url}" if url is not None else _normalise_text(value)


def _normalise_url(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = urlsplit(unicodedata.normalize("NFC", value.strip()))
    except ValueError:
        return None
    scheme = parsed.scheme.casefold()
    hostname = parsed.hostname
    if scheme not in {"http", "https"} or not hostname:
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    try:
        hostname = hostname.encode("idna").decode("ascii").casefold()
    except UnicodeError:
        hostname = unicodedata.normalize("NFC", hostname).casefold()
    rendered_host = f"[{hostname}]" if ":" in hostname else hostname
    if port is not None and (scheme, port) not in {("http", 80), ("https", 443)}:
        rendered_host = f"{rendered_host}:{port}"
    path = unicodedata.normalize("NFC", parsed.path) or "/"
    query = unicodedata.normalize("NFC", parsed.query)
    path = re.sub(r"%[0-9a-fA-F]{2}", lambda match: match.group().upper(), path)
    query = re.sub(r"%[0-9a-fA-F]{2}", lambda match: match.group().upper(), query)
    return urlunsplit((scheme, rendered_host, path, query, ""))


def _normalise_lineage_token(value: Any) -> str | None:
    url = _normalise_url(value)
    if url is not None:
        return f"url:{url}"
    text = _normalise_text(value)
    return f"text:{text}" if text is not None else None


def _normalise_independence_identity(value: Any) -> str | None:
    url = _normalise_url(value)
    return f"url:{url}" if url is not None else _normalise_text(value)


def _source_reference_index(source_ids: set[str]) -> dict[str, set[str]]:
    references: dict[str, set[str]] = {}
    for source_id in source_ids:
        token = _normalise_text(source_id)
        if token is not None:
            references.setdefault(token, set()).add(source_id)
    return references


def _resolved_conflict_source_ids(
    raw: Mapping[str, Any],
    *,
    source_ids: set[str],
    source_id: str,
) -> set[str]:
    candidate = source_id
    conflicts = raw.get("conflict_source_ids")
    if not isinstance(conflicts, list):
        raise ValueError(
            f"source assessment conflict_source_ids must resolve uniquely: {candidate}"
        )
    references = _source_reference_index(source_ids)
    resolved: set[str] = set()
    for conflict in conflicts:
        token = _normalise_text(conflict)
        targets = references.get(token, set()) if token is not None else set()
        if len(targets) != 1:
            raise ValueError(
                f"source assessment conflict_source_ids must resolve uniquely: {candidate}"
            )
        target = next(iter(targets))
        if target == source_id:
            raise ValueError(f"source assessment cannot conflict with itself: {candidate}")
        if target in resolved:
            raise ValueError(
                f"source assessment conflict_source_ids must resolve uniquely: {candidate}"
            )
        resolved.add(target)
    return resolved


def _validate_conflict_relationships(
    assessments: Mapping[str, Mapping[str, Any]],
    *,
    source_ids: set[str],
) -> None:
    resolved_by_source = {
        source_id: _resolved_conflict_source_ids(
            assessments[source_id], source_ids=source_ids, source_id=source_id
        )
        for source_id in sorted(source_ids)
    }
    for source_id, conflicts in resolved_by_source.items():
        for conflict_source_id in sorted(conflicts):
            if source_id not in resolved_by_source[conflict_source_id]:
                raise ValueError(
                    "source assessment conflict_source_ids must be symmetric: "
                    f"{source_id} -> {conflict_source_id}"
                )


def has_bound_host_observation(source: Mapping[str, Any]) -> bool:
    """Accept only a host-authority record with a self-consistent binding."""

    if source.get("content_authority") != "host-observed":
        return False
    observation = source.get("host_observation")
    if not isinstance(observation, Mapping) or observation.get("status") != "bound":
        return False
    binding_sha256 = observation.get("binding_sha256")
    event_stream_sha256 = observation.get("event_stream_sha256")
    event_ids = observation.get("open_event_ids")
    if (
        not isinstance(binding_sha256, str)
        or not re.fullmatch(r"[0-9a-f]{64}", binding_sha256)
        or not isinstance(event_stream_sha256, str)
        or not re.fullmatch(r"[0-9a-f]{64}", event_stream_sha256)
        or not isinstance(event_ids, list)
        or not event_ids
        or not all(isinstance(item, str) and item for item in event_ids)
        or len(event_ids) != len(set(event_ids))
        or not isinstance(source.get("source_id"), str)
        or not isinstance(source.get("content_sha256"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", source["content_sha256"])
    ):
        return False
    binding = {
        "source_id": source["source_id"],
        "content_sha256": source["content_sha256"],
        "event_stream_sha256": event_stream_sha256,
        "open_event_ids": event_ids,
    }
    capture_fields = (
        "capture_id", "requested_url", "final_url", "peer_ip",
        "response_status", "content_type", "charset", "body_sha256",
        "text_sha256", "body_byte_count", "text_character_count",
        "redirect_chain", "excerpt_sha256", "excerpt_start", "excerpt_end",
    )
    if any(field in observation for field in capture_fields):
        if not all(field in observation for field in capture_fields):
            return False
        binding.update({field: observation[field] for field in capture_fields})
    expected_binding = sha256_json(binding)
    return binding_sha256 == expected_binding


def validate_source_assessment_payload(
    raw: dict[str, Any],
    *,
    source_ids: set[str],
    source_id: str | None = None,
    require_provenance: bool = False,
) -> None:
    """Validate one source judgment before it can enter the evidence graph.

    ``require_provenance`` is enabled for a real open-world packet.  The
    low-level writer keeps backwards-compatible defaults for small unit tests,
    but the runtime seam never accepts an unexamined source.
    """

    candidate = source_id if source_id is not None else raw.get("source_id")
    if not isinstance(candidate, str) or not candidate:
        raise ValueError("source assessment source_id must be non-empty")
    if candidate not in source_ids:
        raise ValueError(f"assessment has unknown source_id: {candidate}")
    for field in (
        "authority",
        "independence",
        "freshness",
        "relevance",
        "verdict",
    ):
        if not isinstance(raw.get(field), str) or not raw[field].strip():
            raise ValueError(f"source assessment {field} must be text: {candidate}")
    verdict = "admitted" if raw.get("verdict") == "usable" else raw.get("verdict")
    if verdict not in ASSESSMENT_VERDICTS:
        raise ValueError(f"source assessment verdict is invalid: {candidate}")
    limitations = raw.get("limitations")
    if not isinstance(limitations, list) or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        raise ValueError(f"source assessment limitations must be text: {candidate}")
    cannot_prove = raw.get("cannot_prove")
    if not isinstance(cannot_prove, list) or not cannot_prove or not all(
        isinstance(item, str) and item.strip() for item in cannot_prove
    ):
        raise ValueError(
            f"source assessment cannot_prove must be non-empty text: {candidate}"
        )
    identity = raw.get("independence_identity")
    if not isinstance(identity, str) or not identity.strip():
        raise ValueError(
            f"source assessment independence_identity must be text: {candidate}"
        )
    lineage = raw.get("source_lineage")
    if "source_lineage" in raw and (
        not isinstance(lineage, list)
        or not all(isinstance(item, str) and item.strip() for item in lineage)
    ):
        raise ValueError(
            f"source assessment source_lineage must be a list of text: {candidate}"
        )
    conflicts = raw.get("conflict_source_ids")
    if "conflict_source_ids" in raw:
        _resolved_conflict_source_ids(
            raw,
            source_ids=source_ids,
            source_id=candidate,
        )
    if not require_provenance:
        return
    for field in ("interest_relevance",):
        if not isinstance(raw.get(field), str) or not raw[field].strip():
            raise ValueError(f"source assessment {field} must be text: {candidate}")
    if not isinstance(lineage, list):
        raise ValueError(
            f"source assessment source_lineage must be a list of text: {candidate}"
        )
    for field in ("affected_positions", "low_power_positions"):
        values = raw.get(field)
        if not isinstance(values, list) or not values or not all(
            isinstance(item, str) and item.strip() for item in values
        ):
            raise ValueError(
                f"source assessment {field} must be a non-empty list: {candidate}"
            )
    if not isinstance(conflicts, list):
        raise ValueError(
            f"source assessment conflict_source_ids must resolve uniquely: {candidate}"
        )


def _date_value(value: str, *, field: str) -> datetime:
    try:
        if "T" in value:
            return parse_instant(value, field=field)
        return datetime.combine(
            date.fromisoformat(value), time.min, tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise ValueError(f"source {field} is not an ISO date or date-time") from exc


def _validate_source_cutoff(source: dict[str, Any], evidence_cutoff: str | None) -> None:
    if evidence_cutoff is None:
        return
    # The frozen problem contract uses an RFC3339 instant. Source records may
    # still expose date-only endpoints, which are interpreted at UTC midnight,
    # but a date-only cutoff must never silently widen the admissible window.
    cutoff = parse_instant(evidence_cutoff, field="evidence_cutoff")
    for field in ("published_at", "event_at", "accessed_at"):
        value = source.get(field)
        if value is None:
            continue
        if not isinstance(value, str) or not value:
            raise ValueError(f"source {field} must be an ISO date or date-time")
        for endpoint in value.split("/"):
            if _date_value(endpoint, field=field) > cutoff:
                raise ValueError(
                    f"source {source.get('source_id')} {field} is after evidence cutoff"
                )


def validate_external_source_metadata(source: dict[str, Any]) -> None:
    if source.get("origin") != "external":
        return
    publisher = source.get("publisher")
    if not isinstance(publisher, str) or not publisher.strip():
        raise ValueError("external source requires publisher")
    locator = source.get("url")
    if not isinstance(locator, str):
        raise ValueError("external source requires a verifiable HTTPS locator")
    parsed = urlsplit(locator)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise ValueError("external source requires a verifiable HTTPS locator")
    for field in ("published_at", "event_at", "accessed_at"):
        value = source.get(field)
        if not isinstance(value, str) or not value:
            raise ValueError(f"external source requires {field} date boundary")
        for endpoint in value.split("/"):
            _date_value(endpoint, field=field)


def _safe_component(source_id: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", source_id).strip("-.") or "source"
    return f"{base[:64]}-{sha256_text(source_id)[:10]}"


def build_source_read_lock(repository_root: Path, *, run_id: str) -> dict[str, Any]:
    """Read and hash every reader unit named by the authoritative manifest."""

    repository_root = Path(repository_root).resolve()
    manifest_path = repository_root / "references" / "source" / "v8.3" / "source-manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = read_json(manifest_path)
    sequence = manifest.get("sequence")
    expected_hashes = manifest.get("reader_file_sha256")
    if not isinstance(sequence, list) or not isinstance(expected_hashes, dict):
        raise ValueError("source manifest has no complete reader sequence")
    if manifest.get("reader_unit_count") != len(sequence):
        raise ValueError("source manifest reader count differs from sequence")
    receipts: list[dict[str, Any]] = []
    for index, name in enumerate(sequence):
        name_path = Path(name)
        if name_path.is_absolute() or ".." in name_path.parts or name_path.name != name:
            raise ValueError(f"reader sequence contains unsafe unit name: {name}")
        relative = f"reader/{name}"
        reader_path = repository_root / "references" / "source" / "v8.3" / relative
        if reader_path.is_symlink():
            raise ValueError(f"reader unit is a symlink: {relative}")
        content = reader_path.read_bytes()
        expected = expected_hashes.get(relative)
        observed = sha256_bytes(content)
        if expected != observed:
            raise ValueError(f"reader unit hash mismatch: {relative}")
        manifest_sha256 = sha256_bytes(manifest_bytes)
        receipt = {
            "index": index,
            "sequence": index + 1,
            "receipt_id": f"read-receipt-{index + 1:06d}",
            "run_id": run_id,
            "source_manifest_sha256": manifest_sha256,
            "unit": name,
            "path": f"references/source/v8.3/{relative}",
            "source_file": relative,
            "bytes_read": len(content),
            "expected_sha256": expected,
            "observed_sha256": observed,
            "content_sha256": observed,
            "read_complete": True,
        }
        receipt["receipt_sha256"] = sha256_json(receipt)
        receipts.append(receipt)
    return {
        "schema_id": "xi-kari.v3.source-read",
        "schema_version": 3,
        "run_id": run_id,
        "framework_version": manifest.get("framework_version"),
        "source_manifest_sha256": manifest_sha256,
        "source_raw_sha256": manifest.get("raw_sha256"),
        "source_semantic_sha256": manifest.get("semantic_sha256"),
        "reader_unit_count": len(receipts),
        "sequence": sequence,
        "receipts": receipts,
        "receipt_set_sha256": sha256_json(receipts),
        "complete": True,
    }


def _reader_for_ordinal(manifest: dict[str, Any], ordinal: int) -> str:
    """Resolve a paragraph/table ordinal to its reader volume deterministically."""

    if ordinal < 350:
        return "00-source-envelope.md"
    for division in manifest.get("divisions", []):
        if not isinstance(division, dict):
            continue
        if int(division.get("start_ordinal", 0)) <= ordinal <= int(division.get("end_ordinal", 0)):
            slug = division.get("slug")
            if isinstance(slug, str):
                return f"{slug}.md"
    raise ValueError(f"source ordinal is outside the manifest divisions: {ordinal}")


def build_full_source_lock(
    repository_root: Path, *, run_id: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Read all 21 volumes and all 4631+122 source units.

    The 21 volume receipts prove the immutable reader files were loaded.  The
    4753 unit events independently bind every paragraph and table snapshot, so
    a volume-level receipt can never be mistaken for semantic source coverage.
    """

    repository_root = Path(repository_root).resolve()
    source_root = repository_root / "references" / "source" / "v8.3"
    manifest_path = source_root / "source-manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = read_json(manifest_path)
    sequence = manifest.get("sequence")
    expected_hashes = manifest.get("reader_file_sha256")
    if not isinstance(sequence, list) or len(sequence) != FULL_READER_UNIT_COUNT:
        raise ValueError("v8.3 manifest must contain exactly 21 reader volumes")
    if not isinstance(expected_hashes, dict):
        raise ValueError("v8.3 manifest has no reader file hashes")

    reader_receipts: list[dict[str, Any]] = []
    for index, name in enumerate(sequence, start=1):
        relative = f"reader/{name}"
        path = source_root / relative
        content = path.read_bytes()
        expected = expected_hashes.get(relative)
        observed = sha256_bytes(content)
        if expected != observed:
            raise ValueError(f"reader unit hash mismatch: {relative}")
        reader_receipts.append(
            {
                "receipt_id": f"reader-{index:02d}",
                "sequence": index,
                "unit": name,
                "path": f"references/source/v8.3/{relative}",
                "bytes_read": len(content),
                "expected_sha256": expected,
                "observed_sha256": observed,
                "read_complete": True,
            }
        )

    paragraph_path = source_root / "audit" / "paragraphs.jsonl"
    paragraphs = [
        json.loads(line)
        for line in paragraph_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    table_paths = sorted((source_root / "audit" / "tables").glob("V83-T*.md"))
    if len(paragraphs) != FULL_PARAGRAPH_COUNT or len(table_paths) != FULL_TABLE_COUNT:
        raise ValueError(
            f"v8.3 source unit counts differ: paragraphs={len(paragraphs)}, tables={len(table_paths)}"
        )

    events: list[dict[str, Any]] = []
    for ordinal, paragraph in enumerate(paragraphs, start=1):
        anchor = paragraph.get("anchor")
        text = paragraph.get("text", "")
        if not isinstance(anchor, str) or not isinstance(text, str):
            raise ValueError(f"invalid paragraph source unit at ordinal {ordinal}")
        events.append(
            {
                "schema_id": "xi-kari.v3.source-read-event",
                "schema_version": 3,
                "event_id": f"read-{len(events)+1:04d}",
                "run_id": run_id,
                "ordinal": ordinal,
                "source_anchor": anchor,
                "source_unit_type": "paragraph",
                "reader_unit": _reader_for_ordinal(manifest, ordinal),
                "source_sha256": sha256_text(text),
                "status": "read",
            }
        )
    table_index_rows = read_json(source_root / "indexes" / "tables.json")
    for table_index, path in enumerate(table_paths, start=1):
        raw = path.read_bytes()
        anchor = f"V83-T{table_index:03d}"
        # The table's first paragraph ordinal is authoritative for volume
        # routing; the index is intentionally read from the source snapshot.
        row = table_index_rows[table_index - 1]
        paragraph_ordinals = row.get("paragraph_ordinals", [])
        first_paragraph = int(paragraph_ordinals[0]) if paragraph_ordinals else 1
        events.append(
            {
                "schema_id": "xi-kari.v3.source-read-event",
                "schema_version": 3,
                "event_id": f"read-{len(events)+1:04d}",
                "run_id": run_id,
                "ordinal": FULL_PARAGRAPH_COUNT + table_index,
                "source_anchor": anchor,
                "source_unit_type": "table",
                "reader_unit": _reader_for_ordinal(manifest, first_paragraph),
                "source_sha256": sha256_bytes(raw),
                "status": "read",
            }
        )
    if len({event["source_anchor"] for event in events}) != FULL_SOURCE_UNIT_COUNT:
        raise ValueError("source unit anchors are not unique")
    lock = {
        "schema_id": "xi-kari.v3.source-lock",
        "schema_version": 3,
        "run_id": run_id,
        "framework_version": manifest.get("framework_version"),
        "source_manifest_sha256": sha256_bytes(manifest_bytes),
        "source_raw_sha256": manifest.get("raw_sha256"),
        "source_semantic_sha256": manifest.get("semantic_sha256"),
        "validator_set_sha256": validator_set_sha256(repository_root),
        "paragraph_count": FULL_PARAGRAPH_COUNT,
        "table_count": FULL_TABLE_COUNT,
        "source_unit_count": FULL_SOURCE_UNIT_COUNT,
        "reader_unit_count": FULL_READER_UNIT_COUNT,
        "reader_sequence": sequence,
        "reader_receipts": reader_receipts,
        "source_unit_event_sha256": sha256_json(events),
        "complete": True,
    }
    return lock, events


def validate_source_read_lock(lock: dict[str, Any], repository_root: Path) -> list[str]:
    errors: list[str] = []
    try:
        fresh = build_source_read_lock(repository_root, run_id=lock.get("run_id", ""))
    except Exception as exc:
        return [f"fresh source read failed: {exc}"]
    for index, receipt in enumerate(lock.get("receipts", []), start=1):
        if receipt.get("sequence") != index:
            errors.append(f"source receipt sequence mismatch: {index}")
        if receipt.get("run_id") != lock.get("run_id"):
            errors.append(f"source receipt run binding mismatch: {index}")
        if receipt.get("source_manifest_sha256") != lock.get("source_manifest_sha256"):
            errors.append(f"source receipt manifest binding mismatch: {index}")
        projection = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        if receipt.get("receipt_sha256") != sha256_json(projection):
            errors.append(f"source receipt hash mismatch: {index}")
    for field in (
        "framework_version",
        "source_manifest_sha256",
        "source_raw_sha256",
        "source_semantic_sha256",
        "reader_unit_count",
        "sequence",
        "receipts",
        "receipt_set_sha256",
        "complete",
    ):
        if lock.get(field) != fresh.get(field):
            errors.append(f"source read binding mismatch: {field}")
    return errors


def validate_full_source_lock(
    lock: dict[str, Any], events: list[dict[str, Any]], repository_root: Path
) -> list[str]:
    """Freshly recompute the full source lock and every unit event."""

    errors: list[str] = []
    try:
        fresh_lock, fresh_events = build_full_source_lock(
            repository_root, run_id=str(lock.get("run_id", ""))
        )
    except Exception as exc:
        return [f"fresh full source read failed: {exc}"]
    for field in (
        "framework_version",
        "source_manifest_sha256",
        "source_raw_sha256",
        "source_semantic_sha256",
        "validator_set_sha256",
        "paragraph_count",
        "table_count",
        "source_unit_count",
        "reader_unit_count",
        "reader_sequence",
        "reader_receipts",
        "source_unit_event_sha256",
        "complete",
    ):
        if lock.get(field) != fresh_lock.get(field):
            errors.append(f"full source lock mismatch: {field}")
    if events != fresh_events:
        errors.append("full source read events differ from fresh source units")
    if len(events) != FULL_SOURCE_UNIT_COUNT:
        errors.append("full source read event count is not 4753")
    return errors


def build_retrieval_plan(*, run_id: str, mode: str) -> dict[str, Any]:
    if mode not in ALLOWED_MODES:
        raise ValueError(f"unsupported mode: {mode}")
    return {
        "schema_id": "xi-kari.v3.retrieval-plan",
        "schema_version": 3,
        "run_id": run_id,
        "mode": mode,
        "open_world_default": mode == "open-world",
        "network_allowed": mode == "open-world",
        "external_definition_authority": False,
        "source_assessment_policy": "one-separate-assessment-per-source",
    }


def _normalise_source(source: dict[str, Any], *, run_id: str | None) -> dict[str, Any]:
    source_id = source.get("source_id")
    origin = source.get("origin")
    title = source.get("title")
    if not all(isinstance(value, str) and value for value in (source_id, origin, title)):
        raise ValueError("each source requires source_id, origin, and title")
    validate_external_source_metadata(source)
    content_authority = source.get("content_authority", "unknown")
    if content_authority not in CONTENT_AUTHORITIES:
        raise ValueError(f"source content_authority is invalid: {source_id}")
    host_observation = source.get("host_observation")
    if host_observation is not None and not isinstance(host_observation, Mapping):
        raise ValueError(f"source host_observation is invalid: {source_id}")
    content = source.get("content")
    if content is not None and not isinstance(content, str):
        raise ValueError(f"source content must be text: {source_id}")
    content_hash = source.get("content_sha256")
    if content is not None:
        observed = sha256_text(content)
        if content_hash is not None and content_hash != observed:
            raise ValueError(f"source content_sha256 mismatch: {source_id}")
        content_hash = observed
    if content_hash is None:
        content_hash = sha256_json(
            {
                "source_id": source_id,
                "origin": origin,
                "title": title,
                "url": source.get("url"),
                "published_at": source.get("published_at"),
            }
        )
    record = {
        "schema_id": "xi-kari.v3.source-record",
        "schema_version": 3,
        "source_id": source_id,
        "origin": origin,
        "title": title,
        "url": source.get("url"),
        "publisher": source.get("publisher"),
        "published_at": source.get("published_at"),
        "event_at": source.get("event_at"),
        "accessed_at": source.get("accessed_at"),
        "content_sha256": content_hash,
        "content": content,
        "content_authority": content_authority,
    }
    if host_observation is not None:
        record["host_observation"] = dict(host_observation)
    if content_authority == "host-observed" and not has_bound_host_observation(record):
        raise ValueError(f"source host observation is not bound: {source_id}")
    if run_id is not None:
        record["run_id"] = run_id
    return record


def _derived_independence_keys(
    sources: dict[str, dict[str, Any]],
    assessments: dict[str, dict[str, Any]],
) -> dict[str, str]:
    parents = {source_id: source_id for source_id in sources}

    def find(source_id: str) -> str:
        while parents[source_id] != source_id:
            parents[source_id] = parents[parents[source_id]]
            source_id = parents[source_id]
        return source_id

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parents[max(left_root, right_root)] = min(left_root, right_root)

    by_content: dict[str, str] = {}
    by_lineage_token: dict[str, str] = {}
    by_independence_identity: dict[str, str] = {}
    by_publisher: dict[str, str] = {}
    by_source_url: dict[str, str] = {}
    by_source_reference: dict[str, str] = {}
    unknown_publisher_anchor: str | None = None
    for source_id, source in sources.items():
        source_reference = _normalise_text(source_id)
        if source_reference is not None:
            prior_reference = by_source_reference.setdefault(source_reference, source_id)
            union(source_id, prior_reference)
        source_url = _normalise_url(source.get("url"))
        if source_url is not None:
            prior_url = by_source_url.setdefault(source_url, source_id)
            union(source_id, prior_url)
    for source_id, source in sources.items():
        content_hash = str(source["content_sha256"])
        prior_content = by_content.setdefault(content_hash, source_id)
        union(source_id, prior_content)
        identity = assessments.get(source_id, {}).get("independence_identity")
        normalized_identity = _normalise_independence_identity(identity)
        if normalized_identity is not None:
            prior_identity = by_independence_identity.setdefault(
                normalized_identity, source_id
            )
            union(source_id, prior_identity)
        publisher = _normalise_publisher(source.get("publisher"))
        if publisher is None:
            if unknown_publisher_anchor is None:
                unknown_publisher_anchor = source_id
            else:
                union(source_id, unknown_publisher_anchor)
        else:
            prior_publisher = by_publisher.setdefault(publisher, source_id)
            union(source_id, prior_publisher)
        lineage = assessments.get(source_id, {}).get("source_lineage", [])
        for token in lineage if isinstance(lineage, list) else []:
            normalized_token = _normalise_lineage_token(token)
            if normalized_token is None:
                continue
            prior_lineage = by_lineage_token.setdefault(normalized_token, source_id)
            union(source_id, prior_lineage)
            source_reference = _normalise_text(token)
            if source_reference is not None and source_reference in by_source_reference:
                union(source_id, by_source_reference[source_reference])
            source_url = _normalise_url(token)
            if source_url is not None and source_url in by_source_url:
                union(source_id, by_source_url[source_url])

    components: dict[str, list[str]] = {}
    for source_id in sources:
        components.setdefault(find(source_id), []).append(source_id)
    result: dict[str, str] = {}
    for members in components.values():
        signature = {
            "content_sha256": sorted(
                {str(sources[source_id]["content_sha256"]) for source_id in members}
            ),
            "lineage_tokens": sorted(
                {
                    normalized_token
                    for source_id in members
                    for token in assessments.get(source_id, {}).get(
                        "source_lineage", []
                    )
                    for normalized_token in [_normalise_lineage_token(token)]
                    if normalized_token is not None
                }
            ),
            "independence_identities": sorted(
                {
                    normalized_identity
                    for source_id in members
                    for identity in [
                        assessments.get(source_id, {}).get(
                            "independence_identity"
                        )
                    ]
                    for normalized_identity in [_normalise_independence_identity(identity)]
                    if normalized_identity is not None
                }
            ),
            "publishers": sorted(
                {
                    _normalise_publisher(sources[source_id].get("publisher"))
                    or "unknown-publisher"
                    for source_id in members
                }
            ),
            "source_urls": sorted(
                {
                    source_url
                    for source_id in members
                    for source_url in [_normalise_url(sources[source_id].get("url"))]
                    if source_url is not None
                }
            ),
        }
        key = sha256_json(signature)
        for source_id in members:
            result[source_id] = key
    return result


def materialize_retrieval_bundle(
    root: Path,
    sources: list[dict[str, Any]],
    assessments: list[dict[str, Any]],
    *,
    mode: str,
    run_id: str | None = None,
    evidence_cutoff: str | None = None,
) -> dict[str, Any]:
    """Write independent source and assessment records and return their bindings."""

    if mode not in ALLOWED_MODES:
        raise ValueError(f"unsupported mode: {mode}")
    root = Path(root).resolve()
    source_by_id: dict[str, dict[str, Any]] = {}
    for raw in sources:
        record = _normalise_source(raw, run_id=run_id)
        _validate_source_cutoff(record, evidence_cutoff)
        source_id = record["source_id"]
        if source_id in source_by_id:
            raise ValueError(f"duplicate source_id: {source_id}")
        if mode == "closed-input" and record["origin"] not in CLOSED_INPUT_ORIGINS:
            raise ValueError(f"closed-input run rejects external source: {source_id}")
        source_by_id[source_id] = record
    assessment_by_id: dict[str, dict[str, Any]] = {}
    for raw in assessments:
        source_id = raw.get("source_id")
        if not isinstance(source_id, str) or source_id not in source_by_id:
            raise ValueError(f"assessment has unknown source_id: {source_id}")
        if source_id in assessment_by_id:
            raise ValueError(f"duplicate assessment for source: {source_id}")
        validate_source_assessment_payload(
            raw,
            source_ids=set(source_by_id),
            source_id=source_id,
        )
        verdict = "admitted" if raw["verdict"] == "usable" else raw["verdict"]
        independence_identity = raw["independence_identity"]
        source_sha = sha256_json(source_by_id[source_id])
        assessment = {
            "schema_id": "xi-kari.v3.source-assessment",
            "schema_version": 3,
            "source_id": source_id,
            "source_sha256": source_sha,
            "authority": raw["authority"],
            "independence": raw["independence"],
            "independence_identity": independence_identity,
            "freshness": raw["freshness"],
            "relevance": raw["relevance"],
            "verdict": verdict,
            "limitations": list(raw["limitations"]),
            "cannot_prove": list(raw["cannot_prove"]),
            # Preserve the independent judgment fields for validation and reader projection.
            "source_lineage": list(raw.get("source_lineage", [])),
            "interest_relevance": raw.get("interest_relevance", "未登记"),
            "affected_positions": list(raw.get("affected_positions", ["未登记"])),
            "low_power_positions": list(raw.get("low_power_positions", ["未登记"])),
            "conflict_source_ids": list(raw.get("conflict_source_ids", [])),
        }
        if run_id is not None:
            assessment["run_id"] = run_id
        assessment_by_id[source_id] = assessment
    missing = sorted(set(source_by_id) - set(assessment_by_id))
    extra = sorted(set(assessment_by_id) - set(source_by_id))
    if missing or extra:
        raise ValueError(f"one separate assessment is required per source: missing={missing}, extra={extra}")
    _validate_conflict_relationships(
        assessment_by_id,
        source_ids=set(source_by_id),
    )
    independence_keys = _derived_independence_keys(
        source_by_id, assessment_by_id
    )

    bindings: list[dict[str, Any]] = []
    for source_id in sorted(source_by_id):
        component = _safe_component(source_id)
        source_relative = Path("retrieval") / "sources" / f"{component}.json"
        assessment_relative = Path("retrieval") / "assessments" / f"{component}.json"
        source_path = root / source_relative
        assessment_path = root / assessment_relative
        atomic_write_json(source_path, source_by_id[source_id])
        atomic_write_json(assessment_path, assessment_by_id[source_id])
        binding = {
            "source_id": source_id,
            "source_path": source_relative.as_posix(),
            "source_sha256": sha256_json(source_by_id[source_id]),
            "assessment_path": assessment_relative.as_posix(),
            "assessment_sha256": sha256_json(assessment_by_id[source_id]),
            "assessment_verdict": assessment_by_id[source_id]["verdict"],
            "origin": source_by_id[source_id]["origin"],
            "content_sha256": source_by_id[source_id]["content_sha256"],
            "independence_key": independence_keys[source_id],
            "independence_identity": assessment_by_id[source_id][
                "independence_identity"
            ],
        }
        binding["content_authority"] = source_by_id[source_id]["content_authority"]
        if "host_observation" in source_by_id[source_id]:
            binding["host_observation"] = source_by_id[source_id][
                "host_observation"
            ]
        bindings.append(binding)
    index = {
        "schema_id": "xi-kari.v3.retrieval-index",
        "schema_version": 3,
        "mode": mode,
        "run_id": run_id,
        "sources": bindings,
        "source_count": len(bindings),
        "all_sources_assessed": True,
    }
    atomic_write_json(root / "retrieval" / "index.json", index)
    return index


def validate_retrieval_bundle(
    root: Path,
    index: dict[str, Any],
    *,
    mode: str,
    evidence_cutoff: str | None = None,
) -> list[str]:
    errors: list[str] = []
    root = Path(root).resolve()
    seen: set[str] = set()
    loaded_sources: dict[str, dict[str, Any]] = {}
    loaded_assessments: dict[str, dict[str, Any]] = {}
    bindings_by_id: dict[str, dict[str, Any]] = {}
    for binding in index.get("sources", []):
        source_id = binding.get("source_id")
        if source_id in seen:
            errors.append(f"duplicate retrieval binding: {source_id}")
            continue
        seen.add(source_id)
        if isinstance(source_id, str) and isinstance(binding, dict):
            bindings_by_id[source_id] = binding
        try:
            source_path = confined_path(root, binding["source_path"], must_exist=True)
            assessment_path = confined_path(root, binding["assessment_path"], must_exist=True)
            if source_path.parent.parent != (root / "retrieval").resolve():
                raise ValueError("source path leaves retrieval directory")
            if assessment_path.parent.parent != (root / "retrieval").resolve():
                raise ValueError("assessment path leaves retrieval directory")
            source = read_json(source_path)
            assessment = read_json(assessment_path)
            if isinstance(source_id, str):
                loaded_sources[source_id] = source
                loaded_assessments[source_id] = assessment
            _validate_source_cutoff(source, evidence_cutoff)
            validate_source_assessment_payload(
                assessment,
                source_ids={
                    str(item.get("source_id"))
                    for item in index.get("sources", [])
                    if isinstance(item, dict) and isinstance(item.get("source_id"), str)
                },
                source_id=source_id,
            )
            if sha256_json(source) != binding.get("source_sha256"):
                errors.append(f"source binding mismatch: {source_id}")
            if sha256_json(assessment) != binding.get("assessment_sha256"):
                errors.append(f"assessment binding mismatch: {source_id}")
            if assessment.get("source_sha256") != binding.get("source_sha256"):
                errors.append(f"assessment source binding mismatch: {source_id}")
            if assessment.get("source_id") != source.get("source_id"):
                errors.append(f"assessment source_id mismatch: {source_id}")
            if assessment.get("verdict") != binding.get("assessment_verdict"):
                errors.append(f"assessment verdict binding mismatch: {source_id}")
            if assessment.get("independence_identity") != binding.get(
                "independence_identity"
            ):
                errors.append(f"assessment independence binding mismatch: {source_id}")
            if source.get("content_sha256") != binding.get("content_sha256"):
                errors.append(f"source content binding mismatch: {source_id}")
            if source.get("content_authority") != binding.get("content_authority"):
                errors.append(f"source content authority mismatch: {source_id}")
            if source.get("host_observation") != binding.get("host_observation"):
                errors.append(f"source host observation mismatch: {source_id}")
            if source.get("origin") != binding.get("origin"):
                errors.append(f"source origin binding mismatch: {source_id}")
            expected_run_id = index.get("run_id")
            if expected_run_id is not None and source.get("run_id") != expected_run_id:
                errors.append(f"source run_id mismatch: {source_id}")
            if expected_run_id is not None and assessment.get("run_id") != expected_run_id:
                errors.append(f"assessment run_id mismatch: {source_id}")
            if mode == "closed-input" and source.get("origin") not in CLOSED_INPUT_ORIGINS:
                errors.append(f"closed-input contains external source: {source_id}")
        except Exception as exc:
            errors.append(f"cannot validate retrieval source {source_id}: {exc}")
    if index.get("source_count") != len(seen):
        errors.append("retrieval source count mismatch")
    if loaded_sources and set(loaded_sources) == set(bindings_by_id):
        try:
            _validate_conflict_relationships(
                loaded_assessments,
                source_ids=set(loaded_sources),
            )
        except ValueError as exc:
            errors.append(str(exc))
        expected_keys = _derived_independence_keys(
            loaded_sources, loaded_assessments
        )
        for source_id, expected_key in expected_keys.items():
            if bindings_by_id[source_id].get("independence_key") != expected_key:
                errors.append(
                    f"derived independence binding mismatch: {source_id}"
                )
    return errors


read_all_sources = build_source_read_lock
build_read_receipts = build_source_read_lock
assess_sources = materialize_retrieval_bundle
