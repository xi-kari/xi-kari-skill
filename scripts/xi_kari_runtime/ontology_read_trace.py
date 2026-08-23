"""Runtime-owned ontology read plan and problem-bound production trace."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import hashlib
import hmac
from pathlib import Path
import re
from typing import Any
import unicodedata

from .canonical_json import (
    read_json,
    read_json_text,
    sha256_bytes,
    sha256_file,
    sha256_json,
)


PLAN_SCHEMA_ID = "xi-kari.v2.ontology-read-plan"
INPUT_SCHEMA_ID = "xi-kari.v2.ontology-read-trace-input"
TRACE_SCHEMA_ID = "xi-kari.v2.ontology-read-trace"
PLAN_RECORD_FIELDS = frozenset(
    {
        "item_id",
        "kind",
        "subject_id",
        "related_subject_id",
        "path",
        "content_sha256",
        "disposition",
    }
)
MODEL_RECORD_FIELDS = frozenset(
    {
        "item_id",
        "read_status",
        "content_witness",
        "content_excerpt",
        "problem_relation",
    }
)
PROBLEM_RELATION_FIELDS = frozenset({"status", "rationale"})
TRACE_RECORD_FIELDS = PLAN_RECORD_FIELDS | MODEL_RECORD_FIELDS
PROBLEM_RELATION_STATUSES = frozenset(
    {"applied", "boundary_only", "not_applicable"}
)
CONTENT_PROOF_KIND = "byte-access+problem-bound-semantic-trace"
CONTENT_WITNESS_PROTOCOL = "xi-kari.v2.ontology-content-witness/v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_RATIONALE_RE = re.compile(
    r"(?:\bnot[\s_-]*read\b|\bunread\b|\bplaceholder\b|\btodo\b|"
    r"\btbd\b|\bn/?a\b|\bno[\s_-]+(?:read|content|access)\b|"
    r"未读|未读取|未检查|无法读取|无法访问|占位|待补)",
    re.IGNORECASE,
)
_GENERIC_RATIONALE_RE = re.compile(
    r"(?:checked\s+against\s+(?:the\s+)?frozen\s+problem|"
    r"without\s+changing\s+(?:its|the)\s+(?:repository\s+)?disposition|"
    r"same\s+generic\s+template|"
    r"仅?核对(?:了)?冻结问题|通用模板)",
    re.IGNORECASE,
)
_CANDIDATE_BYTES_CACHE: dict[tuple[str, int, int], dict[str, bytes]] = {}


class OntologyReadTraceError(ValueError):
    """Raised when ontology read coverage is not exact and problem-bound."""


def _require_sha256(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise OntologyReadTraceError(f"{field} must be a lowercase SHA-256")
    return value


def _require_challenge(value: Any) -> str:
    return _require_sha256(value, field="content access challenge")


def content_access_witness(
    *,
    challenge: str,
    problem_contract_sha256: str,
    item_id: str,
    content_sha256: str,
) -> str:
    """Derive the per-item, per-run proof without exposing expected values."""

    challenge = _require_challenge(challenge)
    problem_contract_sha256 = _require_sha256(
        problem_contract_sha256, field="problem contract hash"
    )
    content_sha256 = _require_sha256(content_sha256, field="content hash")
    if not isinstance(item_id, str) or not item_id.strip():
        raise OntologyReadTraceError("content witness item_id is invalid")
    payload = "\0".join(
        (
            CONTENT_WITNESS_PROTOCOL,
            challenge,
            problem_contract_sha256,
            item_id,
            content_sha256,
        )
    ).encode("utf-8")
    return sha256_bytes(payload)


def _safe_authority_path(repository_root: Path, relative: Any) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise OntologyReadTraceError("ontology content path is invalid")
    candidate_relative = Path(relative)
    if candidate_relative.is_absolute() or ".." in candidate_relative.parts:
        raise OntologyReadTraceError("ontology content path escapes repository")
    root = Path(repository_root).resolve()
    candidate = root / candidate_relative
    current = root
    for part in candidate_relative.parts:
        current = current / part
        if current.is_symlink():
            raise OntologyReadTraceError(
                f"ontology content path contains symlink: {relative}"
            )
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise OntologyReadTraceError(
            f"ontology content path is outside repository: {relative}"
        ) from exc
    if candidate.is_symlink() or not resolved.is_file():
        raise OntologyReadTraceError(f"ontology content is not a regular file: {relative}")
    return resolved


def _candidate_rows(path: Path) -> list[tuple[dict[str, Any], bytes]]:
    rows: list[tuple[dict[str, Any], bytes]] = []
    for line_number, raw_line in enumerate(path.read_bytes().splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            value = read_json_text(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, TypeError) as exc:
            raise OntologyReadTraceError(
                f"ontology authority row is invalid: {path.name}:{line_number}"
            ) from exc
        if not isinstance(value, dict):
            raise OntologyReadTraceError(
                f"ontology authority row is invalid: {path.name}:{line_number}"
            )
        rows.append((value, raw_line))
    return rows


def read_ontology_item_bytes(
    repository_root: Path,
    plan_record: Mapping[str, Any],
) -> bytes:
    """Read the exact authority bytes addressed by one runtime plan record."""

    if not isinstance(plan_record, Mapping):
        raise OntologyReadTraceError("ontology plan record is not an object")
    kind = plan_record.get("kind")
    item_id = plan_record.get("item_id")
    path = plan_record.get("path")
    if not isinstance(item_id, str) or not isinstance(kind, str):
        raise OntologyReadTraceError("ontology plan record identity is invalid")
    root = Path(repository_root).resolve()
    if kind == "candidate":
        census_path = root / "references" / "ontology" / "candidate-census.jsonl"
        if path != "references/ontology/candidate-census.jsonl":
            raise OntologyReadTraceError("candidate plan path is invalid")
        try:
            metadata = census_path.stat()
        except OSError as exc:
            raise OntologyReadTraceError("candidate census is unavailable") from exc
        cache_key = (str(census_path), metadata.st_mtime_ns, metadata.st_size)
        cached = _CANDIDATE_BYTES_CACHE.get(cache_key)
        if cached is None:
            cached = {
                str(row.get("candidate_id")): raw
                for row, raw in _candidate_rows(census_path)
            }
            _CANDIDATE_BYTES_CACHE.clear()
            _CANDIDATE_BYTES_CACHE[cache_key] = cached
        candidate_id = item_id.removeprefix("candidate:")
        match = cached.get(candidate_id)
        if match is None:
            raise OntologyReadTraceError(
                f"candidate authority row is not uniquely bound: {candidate_id}"
            )
        return match
    authority_path = _safe_authority_path(root, path)
    return authority_path.read_bytes()


def derive_content_observation(content: bytes, item_id: str) -> str:
    """Pick a source substring tied to the item, for independent membership checks."""

    if not isinstance(content, bytes) or not content:
        raise OntologyReadTraceError("ontology content bytes are empty")
    if not isinstance(item_id, str) or not item_id:
        raise OntologyReadTraceError("ontology content observation item_id is invalid")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OntologyReadTraceError("ontology content is not UTF-8 text") from exc
    if not text.strip():
        raise OntologyReadTraceError("ontology content has no observable text")
    target = min(160, len(text))
    starts: list[int]
    if len(text) <= target:
        starts = [0]
    else:
        digest = hashlib.sha256(item_id.encode("utf-8")).digest()
        preferred = int.from_bytes(digest[:8], "big") % max(1, len(text) - target)
        span = len(text) - target
        starts = [
            preferred,
            0,
            max(0, len(text) // 3 - target // 2),
            max(0, len(text) // 2 - target // 2),
            span,
        ]
    candidates: list[tuple[int, str]] = []
    for raw_start in starts:
        start = raw_start
        while start > 0 and not text[start - 1].isspace():
            start -= 1
        end = min(len(text), start + target)
        while end < len(text) and not text[end - 1].isspace():
            end += 1
        excerpt = text[start:end].strip()
        signal = re.sub(
            r"v82[-_a-z0-9]+|[0-9a-f]{16,}|references/[a-z0-9_./-]+",
            " ",
            excerpt,
            flags=re.IGNORECASE,
        )
        score = sum(char.isalnum() for char in signal)
        candidates.append((score, excerpt))
    _score, excerpt = max(candidates, key=lambda item: item[0])
    if len(" ".join(excerpt.split())) < 12 or _score < 12:
        raise OntologyReadTraceError("ontology content observation is too short")
    return excerpt


def _normalise_identifier_free_rationale(
    rationale: str,
    *,
    plan_record: Mapping[str, Any],
) -> str:
    text = unicodedata.normalize("NFKC", rationale).casefold()
    identifiers = [
        plan_record.get("item_id"),
        plan_record.get("subject_id"),
        plan_record.get("related_subject_id"),
        plan_record.get("path"),
        plan_record.get("content_sha256"),
    ]
    for identifier in sorted(
        (item for item in identifiers if isinstance(item, str) and item),
        key=len,
        reverse=True,
    ):
        text = text.replace(unicodedata.normalize("NFKC", identifier).casefold(), " ")
    # Remove common identifier forms even when a model changes punctuation.
    text = re.sub(
        r"\b(?:candidate|card|neighbor|bundle)\s*[:/#-]\s*[a-z0-9._:/-]+",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\bv82[-_a-z0-9]+\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b[0-9a-f]{64}\b", " ", text, flags=re.IGNORECASE)
    return " ".join(text.split())


def _rationale_mentions_observation(
    rationale: str,
    excerpt: str,
    *,
    plan_record: Mapping[str, Any],
) -> bool:
    rationale_text = _normalise_identifier_free_rationale(
        rationale,
        plan_record=plan_record,
    ).replace(" ", "")
    excerpt_text = _normalise_identifier_free_rationale(
        excerpt,
        plan_record=plan_record,
    ).replace(" ", "")
    if len(excerpt_text) < 12:
        return False
    starts = {0, max(0, len(excerpt_text) // 3), max(0, len(excerpt_text) // 2)}
    starts.add(max(0, len(excerpt_text) - 24))
    return any(
        len(fragment) >= 12 and fragment in rationale_text
        for start in starts
        for fragment in (excerpt_text[start : start + 16],)
    )


def _record(
    *,
    item_id: str,
    kind: str,
    subject_id: str,
    path: str,
    content_sha256: str,
    disposition: str,
    related_subject_id: str | None = None,
) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "kind": kind,
        "subject_id": subject_id,
        "related_subject_id": related_subject_id,
        "path": path,
        "content_sha256": content_sha256,
        "disposition": disposition,
    }


def build_ontology_read_plan(
    repository_root: Path,
    *,
    run_id: str,
    problem_contract_sha256: str,
    content_access_challenge: str,
) -> dict[str, Any]:
    """Freeze every ontology read obligation into one deterministic run plan."""

    if not isinstance(run_id, str) or not run_id.strip():
        raise OntologyReadTraceError("ontology read plan run_id is invalid")
    problem_contract_sha256 = _require_sha256(
        problem_contract_sha256, field="problem contract hash"
    )
    content_access_challenge = _require_challenge(content_access_challenge)
    repo = Path(repository_root).resolve()
    ontology = repo / "references" / "ontology"
    census_path = ontology / "candidate-census.jsonl"
    registry_path = ontology / "concept-registry.json"
    relations_path = ontology / "concept-relations.json"
    bundles_path = ontology / "continuity-bundle-registry.json"
    required = (census_path, registry_path, relations_path, bundles_path)
    if not all(path.is_file() and not path.is_symlink() for path in required):
        raise OntologyReadTraceError("complete ontology read authority is unavailable")

    candidate_rows = _candidate_rows(census_path)
    census = [row for row, _raw in candidate_rows]
    candidate_bytes: dict[str, bytes] = {}
    for row, raw in candidate_rows:
        candidate_id = row.get("candidate_id")
        if not isinstance(candidate_id, str) or candidate_id in candidate_bytes:
            raise OntologyReadTraceError("candidate read authority identity is invalid")
        candidate_bytes[candidate_id] = raw
    registry = read_json(registry_path)
    relations = read_json(relations_path)
    bundle_registry = read_json(bundles_path)
    if not all(isinstance(value, Mapping) for value in (registry, relations, bundle_registry)):
        raise OntologyReadTraceError("ontology read authority is not an object")
    concepts = registry.get("concepts")
    bundles = bundle_registry.get("bundles")
    if not isinstance(concepts, list) or not isinstance(bundles, Mapping):
        raise OntologyReadTraceError("ontology read authority is incomplete")

    records: list[dict[str, Any]] = []
    for candidate in census:
        candidate_id = candidate.get("candidate_id")
        disposition = candidate.get("disposition")
        if not isinstance(candidate_id, str) or not isinstance(disposition, str):
            raise OntologyReadTraceError("candidate read authority is invalid")
        records.append(
            _record(
                item_id=f"candidate:{candidate_id}",
                kind="candidate",
                subject_id=candidate_id,
                path="references/ontology/candidate-census.jsonl",
                content_sha256=sha256_bytes(candidate_bytes[candidate_id]),
                disposition=disposition,
            )
        )

    semantic_concepts: list[Mapping[str, Any]] = []
    concept_by_id: dict[str, Mapping[str, Any]] = {}
    for concept in concepts:
        if not isinstance(concept, Mapping):
            raise OntologyReadTraceError("concept registry record is invalid")
        concept_id = concept.get("concept_id")
        if not isinstance(concept_id, str) or concept_id in concept_by_id:
            raise OntologyReadTraceError("concept registry identity is invalid")
        concept_by_id[concept_id] = concept
        if concept.get("disposition") in {"canonical_concept", "structural_rule"}:
            semantic_concepts.append(concept)

    for concept in semantic_concepts:
        concept_id = str(concept["concept_id"])
        card_path = concept.get("card_path")
        disposition = concept.get("disposition")
        if not isinstance(card_path, str) or not isinstance(disposition, str):
            raise OntologyReadTraceError(f"semantic card binding is invalid: {concept_id}")
        card = repo / card_path
        if not card.is_file() or card.is_symlink():
            raise OntologyReadTraceError(f"semantic card is unavailable: {card_path}")
        records.append(
            _record(
                item_id=f"card:{concept_id}",
                kind="canonical_or_structural_card",
                subject_id=concept_id,
                path=card_path,
                content_sha256=sha256_file(card),
                disposition=disposition,
            )
        )

    neighbor_count = 0
    for concept_id, relation in relations.items():
        if not isinstance(concept_id, str) or not isinstance(relation, Mapping):
            raise OntologyReadTraceError("ontology relation record is invalid")
        neighbors = relation.get("required_neighbors")
        if not isinstance(neighbors, list):
            raise OntologyReadTraceError(
                f"ontology relation neighbors are invalid: {concept_id}"
            )
        source_concept = concept_by_id.get(concept_id)
        if source_concept is None:
            raise OntologyReadTraceError(
                f"ontology relation source is not registered: {concept_id}"
            )
        for neighbor_id in neighbors:
            neighbor = concept_by_id.get(neighbor_id)
            if not isinstance(neighbor_id, str) or neighbor is None:
                raise OntologyReadTraceError(
                    f"required ontology neighbor is not registered: {concept_id}"
                )
            neighbor_path = neighbor.get("card_path")
            if not isinstance(neighbor_path, str):
                raise OntologyReadTraceError(
                    f"required ontology neighbor has no card: {neighbor_id}"
                )
            neighbor_card = repo / neighbor_path
            if not neighbor_card.is_file() or neighbor_card.is_symlink():
                raise OntologyReadTraceError(
                    f"required ontology neighbor card is unavailable: {neighbor_path}"
                )
            records.append(
                _record(
                    item_id=f"neighbor:{concept_id}:{neighbor_id}",
                    kind="required_neighbor",
                    subject_id=concept_id,
                    related_subject_id=neighbor_id,
                    path=neighbor_path,
                    content_sha256=sha256_file(neighbor_card),
                    disposition="required_neighbor",
                )
            )
            neighbor_count += 1

    for path, binding in sorted(bundles.items()):
        if not isinstance(path, str) or not isinstance(binding, Mapping):
            raise OntologyReadTraceError("continuity bundle registry is invalid")
        bundle = repo / path
        if not bundle.is_file() or bundle.is_symlink():
            raise OntologyReadTraceError(f"continuity bundle is unavailable: {path}")
        observed_hash = sha256_file(bundle)
        if binding.get("sha256") != observed_hash:
            raise OntologyReadTraceError(f"continuity bundle hash differs: {path}")
        records.append(
            _record(
                item_id=f"bundle:{path}",
                kind="continuity_bundle",
                subject_id=path,
                path=path,
                content_sha256=observed_hash,
                disposition=str(binding.get("route_kind", "continuity_bundle")),
            )
        )

    item_ids = [record["item_id"] for record in records]
    if len(item_ids) != len(set(item_ids)):
        raise OntologyReadTraceError("ontology read plan item identities collide")
    return {
        "schema_id": PLAN_SCHEMA_ID,
        "schema_version": 1,
        "run_id": run_id,
        "problem_contract_sha256": problem_contract_sha256,
        "content_access_challenge": content_access_challenge,
        "proof_kind": CONTENT_PROOF_KIND,
        "witness_protocol": CONTENT_WITNESS_PROTOCOL,
        "authority_bindings": {
            "candidate_census_sha256": sha256_file(census_path),
            "concept_registry_sha256": sha256_file(registry_path),
            "concept_relations_sha256": sha256_file(relations_path),
            "continuity_bundle_registry_sha256": sha256_file(bundles_path),
        },
        "candidate_count": len(census),
        "card_count": len(semantic_concepts),
        "required_neighbor_count": neighbor_count,
        "continuity_bundle_count": len(bundles),
        "record_count": len(records),
        "records": records,
        "complete": True,
    }


def _model_records(
    value: Any,
    *,
    plan: Mapping[str, Any],
    repository_root: Path,
) -> list[Mapping[str, Any]]:
    if not isinstance(value, Mapping) or set(value) != {
        "schema_id",
        "schema_version",
        "records",
    }:
        raise OntologyReadTraceError("ontology read trace input fields are not exact")
    if value.get("schema_id") != INPUT_SCHEMA_ID or value.get("schema_version") != 1:
        raise OntologyReadTraceError("ontology read trace input identity is invalid")
    records = value.get("records")
    plan_records = plan.get("records")
    if not isinstance(records, list) or not isinstance(plan_records, list):
        raise OntologyReadTraceError("ontology read trace records are not a list")
    expected_ids = [record.get("item_id") for record in plan_records]
    observed_ids = [
        record.get("item_id") if isinstance(record, Mapping) else None
        for record in records
    ]
    if observed_ids != expected_ids or len(observed_ids) != len(set(observed_ids)):
        raise OntologyReadTraceError(
            "ontology read trace does not cover the exact ontology read plan"
        )
    challenge = _require_challenge(plan.get("content_access_challenge"))
    problem_contract_sha256 = _require_sha256(
        plan.get("problem_contract_sha256"), field="problem contract hash"
    )
    if plan.get("proof_kind") != CONTENT_PROOF_KIND:
        raise OntologyReadTraceError("ontology read trace proof kind is invalid")
    if plan.get("witness_protocol") != CONTENT_WITNESS_PROTOCOL:
        raise OntologyReadTraceError("ontology read trace witness protocol is invalid")
    rationale_owners: dict[str, str] = {}
    content_cache: dict[str, bytes] = {}
    candidate_cache = {
        f"candidate:{row.get('candidate_id')}": raw
        for row, raw in _candidate_rows(
            Path(repository_root)
            / "references"
            / "ontology"
            / "candidate-census.jsonl"
        )
    }
    statuses: list[str] = []
    for plan_record, record in zip(plan_records, records, strict=True):
        if not isinstance(record, Mapping) or set(record) != MODEL_RECORD_FIELDS:
            raise OntologyReadTraceError("ontology read trace record fields are not exact")
        if record.get("read_status") != "read":
            raise OntologyReadTraceError("ontology read trace contains an unread ontology item")
        item_id = record.get("item_id")
        if item_id != plan_record.get("item_id"):
            raise OntologyReadTraceError("ontology read trace item identity differs from plan")
        content_sha256 = _require_sha256(
            plan_record.get("content_sha256"), field="ontology plan content hash"
        )
        cache_key = ":".join(
            (
                str(plan_record.get("kind")),
                str(plan_record.get("item_id")),
                str(plan_record.get("path")),
            )
        )
        if plan_record.get("kind") == "candidate":
            content = candidate_cache.get(str(item_id))
            if content is None:
                raise OntologyReadTraceError(
                    f"candidate source bytes are missing for {item_id}"
                )
        else:
            if cache_key not in content_cache:
                content_cache[cache_key] = read_ontology_item_bytes(
                    repository_root, plan_record
                )
            content = content_cache[cache_key]
        observed_content_sha256 = sha256_bytes(content)
        if observed_content_sha256 != content_sha256:
            raise OntologyReadTraceError(
                f"ontology source content hash differs for {item_id}"
            )
        witness = record.get("content_witness")
        expected_witness = content_access_witness(
            challenge=challenge,
            problem_contract_sha256=problem_contract_sha256,
            item_id=str(item_id),
            content_sha256=content_sha256,
        )
        if not isinstance(witness, str) or not _SHA256_RE.fullmatch(witness):
            raise OntologyReadTraceError("ontology content witness is invalid")
        if not hmac.compare_digest(witness, expected_witness):
            raise OntologyReadTraceError(
                f"ontology content witness does not prove source access for {item_id}"
            )
        excerpt = record.get("content_excerpt")
        if not isinstance(excerpt, str) or not excerpt.strip():
            raise OntologyReadTraceError("ontology content observation is empty")
        excerpt_bytes = excerpt.encode("utf-8")
        if len(" ".join(excerpt.split())) < 12:
            raise OntologyReadTraceError("ontology content observation is too short")
        if not any(char.isalnum() for char in excerpt):
            raise OntologyReadTraceError("ontology content observation is a placeholder")
        if excerpt_bytes not in content:
            raise OntologyReadTraceError(
                f"ontology content observation is not a source member for {item_id}"
            )
        relation = record.get("problem_relation")
        if not isinstance(relation, Mapping) or set(relation) != PROBLEM_RELATION_FIELDS:
            raise OntologyReadTraceError(
                "ontology read trace problem relation fields are not exact"
            )
        if relation.get("status") not in PROBLEM_RELATION_STATUSES:
            raise OntologyReadTraceError(
                "ontology read trace problem relation status is invalid"
            )
        rationale = relation.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            raise OntologyReadTraceError(
                "ontology read trace problem relation rationale is empty"
            )
        item_id = str(item_id)
        if item_id not in rationale:
            raise OntologyReadTraceError(
                "ontology read trace problem relation rationale does not name its item_id"
            )
        if _FORBIDDEN_RATIONALE_RE.search(rationale):
            raise OntologyReadTraceError(
                "ontology read trace rationale contains explicit not-read or placeholder text"
            )
        if _GENERIC_RATIONALE_RE.search(rationale):
            raise OntologyReadTraceError(
                "ontology read trace contains repeated problem relation boilerplate"
            )
        if not _rationale_mentions_observation(
            rationale,
            excerpt,
            plan_record=plan_record,
        ):
            raise OntologyReadTraceError(
                "ontology read trace rationale does not contain a source observation"
            )
        normalised = _normalise_identifier_free_rationale(
            rationale,
            plan_record=plan_record,
        )
        if len(normalised) < 12:
            raise OntologyReadTraceError(
                "ontology read trace rationale is only identifier boilerplate"
            )
        previous = rationale_owners.setdefault(normalised, item_id)
        if previous != item_id and len(normalised) < 128:
            raise OntologyReadTraceError(
                "ontology read trace contains repeated problem relation boilerplate"
            )
        statuses.append(str(relation.get("status")))
    if statuses and all(status == "not_applicable" for status in statuses):
        raise OntologyReadTraceError(
            "ontology read trace marks all ontology items not_applicable"
        )
    return records


def build_ontology_read_trace(
    model_trace: Mapping[str, Any],
    *,
    plan: Mapping[str, Any],
    run_id: str,
    repository_root: Path,
    problem_contract_sha256: str,
) -> dict[str, Any]:
    """Bind model read dispositions to the exact runtime-owned plan."""

    if (
        plan.get("run_id") != run_id
        or plan.get("complete") is not True
        or plan.get("problem_contract_sha256") != problem_contract_sha256
    ):
        raise OntologyReadTraceError("ontology read plan is not bound to this run")
    model_records = _model_records(
        model_trace,
        plan=plan,
        repository_root=repository_root,
    )
    plan_records = plan["records"]
    records = [
        {**deepcopy(dict(plan_record)), **deepcopy(dict(model_record))}
        for plan_record, model_record in zip(plan_records, model_records, strict=True)
    ]
    return {
        "schema_id": TRACE_SCHEMA_ID,
        "schema_version": 1,
        "run_id": run_id,
        "problem_contract_sha256": plan["problem_contract_sha256"],
        "content_access_challenge": plan["content_access_challenge"],
        "proof_kind": plan["proof_kind"],
        "witness_protocol": plan["witness_protocol"],
        "ontology_read_plan_sha256": sha256_json(plan),
        "semantic_trace_input_sha256": sha256_json(model_trace),
        "record_count": len(records),
        "records": records,
        # Runtime writes this control field only after every proof validates.
        "complete": bool(model_records) and len(model_records) == len(plan_records),
    }


def validate_ontology_read_trace(
    trace: Any,
    *,
    plan: Mapping[str, Any],
    expected_run_id: str,
    expected_problem_contract_sha256: str,
    repository_root: Path,
) -> list[str]:
    errors: list[str] = []
    try:
        fresh_plan = build_ontology_read_plan(
            repository_root,
            run_id=expected_run_id,
            problem_contract_sha256=expected_problem_contract_sha256,
            content_access_challenge=plan.get("content_access_challenge"),
        )
        if dict(plan) != fresh_plan:
            raise OntologyReadTraceError(
                "ontology read plan differs from current repository authority"
            )
        if not isinstance(trace, Mapping) or set(trace) != {
            "schema_id",
            "schema_version",
            "run_id",
            "problem_contract_sha256",
            "content_access_challenge",
            "proof_kind",
            "witness_protocol",
            "ontology_read_plan_sha256",
            "semantic_trace_input_sha256",
            "record_count",
            "records",
            "complete",
        }:
            raise OntologyReadTraceError("ontology read trace fields are not exact")
        if (
            trace.get("schema_id") != TRACE_SCHEMA_ID
            or trace.get("schema_version") != 1
            or trace.get("run_id") != expected_run_id
            or trace.get("problem_contract_sha256")
            != expected_problem_contract_sha256
            or trace.get("content_access_challenge")
            != plan.get("content_access_challenge")
            or trace.get("proof_kind") != CONTENT_PROOF_KIND
            or trace.get("witness_protocol") != CONTENT_WITNESS_PROTOCOL
            or trace.get("ontology_read_plan_sha256") != sha256_json(plan)
            or trace.get("complete") is not True
        ):
            raise OntologyReadTraceError("ontology read trace binding is invalid")
        records = trace.get("records")
        plan_records = plan.get("records")
        if (
            not isinstance(records, list)
            or not isinstance(plan_records, list)
            or trace.get("record_count") != len(records)
            or len(records) != len(plan_records)
            or [record.get("item_id") for record in records if isinstance(record, Mapping)]
            != [record.get("item_id") for record in plan_records]
        ):
            raise OntologyReadTraceError(
                "ontology read trace does not cover the exact ontology read plan"
            )
        semantic_records: list[dict[str, Any]] = []
        for record, plan_record in zip(records, plan_records, strict=True):
            if not isinstance(record, Mapping) or set(record) != TRACE_RECORD_FIELDS:
                raise OntologyReadTraceError(
                    "ontology read trace record fields are not exact"
                )
            static = {field: record.get(field) for field in PLAN_RECORD_FIELDS}
            if static != plan_record:
                raise OntologyReadTraceError(
                    "ontology read trace differs from the runtime-owned ontology read plan"
                )
            semantic_records.append(
                {field: deepcopy(record[field]) for field in MODEL_RECORD_FIELDS}
            )
        semantic = {
            "schema_id": INPUT_SCHEMA_ID,
            "schema_version": 1,
            "records": semantic_records,
        }
        _model_records(
            semantic,
            plan=plan,
            repository_root=repository_root,
        )
        if trace.get("semantic_trace_input_sha256") != sha256_json(semantic):
            raise OntologyReadTraceError(
                "ontology read trace semantic input hash differs"
            )
    except (KeyError, OSError, TypeError, ValueError) as exc:
        errors.append(str(exc))
    return errors


__all__ = (
    "CONTENT_PROOF_KIND",
    "CONTENT_WITNESS_PROTOCOL",
    "INPUT_SCHEMA_ID",
    "OntologyReadTraceError",
    "PLAN_SCHEMA_ID",
    "TRACE_SCHEMA_ID",
    "build_ontology_read_plan",
    "build_ontology_read_trace",
    "content_access_witness",
    "derive_content_observation",
    "read_ontology_item_bytes",
    "validate_ontology_read_trace",
)
