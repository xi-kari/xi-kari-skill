"""Repository-owned candidate closure and compact ontology bindings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonical_json import read_json, read_json_text, sha256_file
from .source_profile import SOURCE_VERSION


CONCEPT_AUTHORITY_SCHEMA_ID = "xi-kari.v3.concept-authority-binding"
CONCEPT_AUTHORITY_SCHEMA_VERSION = 1
LEDGER_FIELDS = (
    "bound_card_paths",
    "bound_concept_ids",
    "candidate_id",
    "disposition",
    "disposition_reason",
    "disposition_status",
    "parent_card_paths",
    "parent_concept_ids",
    "semantic_review_note",
    "source_anchor",
    "source_undefined_fields",
)
SOURCE_BINDING_FIELDS = (
    "candidate_id",
    "source_anchors",
    "source_span",
    "semantic_fingerprint_sha256",
)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValueError(f"concept authority file is unavailable: {path.name}")
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        value = read_json_text(line)
        if not isinstance(value, dict):
            raise ValueError(
                f"concept authority row is not an object: {path.name}:{line_number}"
            )
        rows.append(value)
    if not rows:
        raise ValueError(f"concept authority file is empty: {path.name}")
    return rows


def load_concept_authority(
    repository_root: Path,
    *,
    source_version: str = SOURCE_VERSION,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read and cross-check the repository-owned 1:1 candidate closure."""

    repo = Path(repository_root).resolve()
    if source_version == "v8.3":
        source_root = repo / "references" / "source" / "v8.3"
        ontology_root = repo / "references" / "ontology"
        domain_index_path = None
    elif source_version == "v9.0":
        source_root = repo / "references" / "source" / "v9.0"
        ontology_root = repo / "references" / "ontology" / "v9.0"
        domain_index_path = repo / "references" / "domains" / "index.json"
    else:
        raise ValueError(f"unsupported concept authority source version: {source_version}")
    source_path = source_root / "indexes" / "candidates.jsonl"
    manifest_path = source_root / "source-manifest.json"
    census_path = ontology_root / "candidate-census.jsonl"
    ledger_path = ontology_root / "concept-disposition-ledger.jsonl"
    registry_path = ontology_root / "concept-registry.json"
    relations_path = ontology_root / "concept-relations.json"
    required_paths = (
        source_path,
        manifest_path,
        census_path,
        ledger_path,
        registry_path,
        relations_path,
    )
    if not all(path.is_file() for path in required_paths):
        raise ValueError("complete concept authority is unavailable")

    source_rows = _read_jsonl(source_path)
    census_rows = _read_jsonl(census_path)
    ledger_rows = _read_jsonl(ledger_path)
    manifest = read_json(manifest_path)
    registry = read_json(registry_path)
    relations = read_json(relations_path)
    if not all(isinstance(value, dict) for value in (manifest, registry, relations)):
        raise ValueError("concept authority metadata is invalid")

    candidate_count = len(source_rows)
    if len(census_rows) != candidate_count or len(ledger_rows) != candidate_count:
        raise ValueError(
            f"candidate disposition closure must contain {candidate_count} rows"
        )
    source_ids = [row.get("candidate_id") for row in source_rows]
    census_ids = [row.get("candidate_id") for row in census_rows]
    ledger_ids = [row.get("candidate_id") for row in ledger_rows]
    if (
        any(
            not isinstance(candidate_id, str) or not candidate_id
            for candidate_id in source_ids
        )
        or len(set(source_ids)) != candidate_count
        or census_ids != source_ids
        or ledger_ids != source_ids
    ):
        raise ValueError("candidate authority is not a complete ordered 1:1 closure")

    source_sha256 = sha256_file(source_path)
    census_sha256 = sha256_file(census_path)
    if (
        manifest.get("candidate_index_sha256") != source_sha256
        or manifest.get("candidate_count") != candidate_count
    ):
        raise ValueError("source candidate authority binding is invalid")
    if (
        registry.get("candidate_census_sha256") != census_sha256
        or registry.get("candidate_count") != candidate_count
        or registry.get("unresolved_candidate_count") != 0
    ):
        raise ValueError("ontology candidate authority binding is invalid")

    for source_row, census_row, ledger_row in zip(
        source_rows, census_rows, ledger_rows, strict=True
    ):
        candidate_id = source_row["candidate_id"]
        if source_version == "v8.3":
            source_binding_differs = any(
                census_row.get(field) != source_row.get(field)
                for field in SOURCE_BINDING_FIELDS
            )
        else:
            source_binding_differs = any(
                census_row.get(field) != value
                for field, value in source_row.items()
            )
        if source_binding_differs:
            raise ValueError(
                f"candidate census differs from source authority: {candidate_id}"
            )
        if set(ledger_row) != set(LEDGER_FIELDS) or ledger_row != {
            field: census_row.get(field) for field in LEDGER_FIELDS
        }:
            raise ValueError(
                f"candidate ledger differs from the reviewed census: {candidate_id}"
            )
        if census_row.get("disposition_status") != "final":
            raise ValueError("candidate disposition closure is not ordered and final")
        if census_row.get("disposition") == "unresolved":
            raise ValueError("candidate disposition closure contains unresolved rows")

    concept_count = registry.get("concept_count")
    concepts = registry.get("concepts")
    if (
        not isinstance(concept_count, int)
        or isinstance(concept_count, bool)
        or concept_count < 1
        or not isinstance(concepts, list)
        or len(concepts) != concept_count
        or len(relations) != concept_count
    ):
        raise ValueError("ontology concept authority count is invalid")

    registered_ids = {
        concept.get("concept_id")
        for concept in concepts
        if isinstance(concept, dict) and isinstance(concept.get("concept_id"), str)
    }
    if domain_index_path is not None:
        if not domain_index_path.is_file() or domain_index_path.is_symlink():
            raise ValueError("v9.0 domain identity authority is unavailable")
        domain_index = read_json(domain_index_path)
        entries = domain_index.get("entries") if isinstance(domain_index, dict) else None
        if not isinstance(entries, list):
            raise ValueError("v9.0 domain identity authority is invalid")
        registered_ids.update(
            entry.get("identity_id")
            for entry in entries
            if isinstance(entry, dict) and isinstance(entry.get("identity_id"), str)
        )
    if source_version == "v9.0":
        terminal = {"canonical", "alias", "subordinate_value", "out_of_scope"}
        for row in census_rows:
            candidate_id = row.get("candidate_id")
            disposition = row.get("disposition")
            bound_ids = row.get("bound_concept_ids")
            parent_ids = row.get("parent_concept_ids")
            if disposition not in terminal:
                raise ValueError(
                    f"v9.0 candidate disposition is not terminal: {candidate_id}"
                )
            if not isinstance(bound_ids, list) or not isinstance(parent_ids, list):
                raise ValueError(f"v9.0 candidate identity binding is invalid: {candidate_id}")
            if any(value not in registered_ids for value in [*bound_ids, *parent_ids]):
                raise ValueError(
                    f"v9.0 candidate identity binding does not resolve: {candidate_id}"
                )

    binding = {
        "schema_id": (
            CONCEPT_AUTHORITY_SCHEMA_ID
            if source_version == "v8.3"
            else "xi-kari.v4.concept-authority-binding"
        ),
        "schema_version": (
            CONCEPT_AUTHORITY_SCHEMA_VERSION if source_version == "v8.3" else 2
        ),
        "source_candidate_count": candidate_count,
        "source_candidate_index_sha256": source_sha256,
        "candidate_census_sha256": census_sha256,
        "concept_disposition_ledger_sha256": sha256_file(ledger_path),
        "ontology_concept_count": concept_count,
        "concept_registry_sha256": sha256_file(registry_path),
        "concept_relations_sha256": sha256_file(relations_path),
    }
    if source_version == "v9.0":
        binding["framework_version"] = source_version
    return census_rows, binding
