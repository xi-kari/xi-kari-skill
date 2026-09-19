#!/usr/bin/env python3
"""Aggregate authored concept shards into deterministic read-only indexes."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from typing import Any


# Keep canonical concepts and source-level candidates in one auditable ID
# namespace.  A candidate/heading is not thereby promoted to a concept.
CONCEPT_ID = re.compile(r"\bV83-(?:CANON|CANDIDATE|HEADING|PROVISIONAL|SOURCE)(?:-[A-Z0-9]+)+\b")
ANCHOR = re.compile(r"\bV83-(?:P\d{4}|T\d{3})\b")
SOURCE_ANCHOR = re.compile(r"^V83-(?:P\d{4}|T\d{3}(?:-R\d{3})?)$")
SOURCE_CANDIDATE_ID = re.compile(
    r"^V83-CANDIDATE-(?:P\d{4}|T\d{3}(?:-R\d{3})?)$"
)
ALLOWED_DISPOSITIONS = {
    "canonical_concept",
    "structural_rule",
    "subordinate_value",
    "alias",
    "example_only",
    "heading_only",
    "source_undefined",
    "unresolved",
}
SEMANTIC_DISPOSITIONS = {"canonical_concept", "structural_rule"}
MAX_NEIGHBORS = 16
CANDIDATE_REVIEW_VERSION = 4
EXAMPLE_MARKERS = ("例如", "比如", "示例", "例：", "例:", "案例")
EXACT_REVIEW_COUNT_SEMANTICS = (
    "authored exact candidate decisions; not an ontology cardinality claim"
)
STRUCTURAL_SECTION_STYLES = {
    "CoverTitle": 0,
    "FrontHeading": 1,
    "PartTitle": 1,
    "SecH2": 2,
    "SecH3": 3,
    "CardLabel": 4,
}
NAVIGATION_TABLES = {"V83-T001", "V83-T119", "V83-T120"}


def _json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _jsonl(values: list[dict[str, object]]) -> bytes:
    return b"".join(
        (
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        for value in values
    )


def _read_inventory(root: Path) -> tuple[list[dict[str, object]], list[str]]:
    inventory_root = root / "references" / "ontology" / "inventory"
    errors: list[str] = []
    records: list[dict[str, object]] = []
    for path in sorted(inventory_root.glob("*.jsonl")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{line_number}: invalid JSON: {exc}")
                continue
            if not isinstance(value, dict):
                errors.append(f"{path}:{line_number}: inventory entry must be object")
                continue
            # Accept the authored shard vocabulary (`id`/`card`/`name`) and
            # normalize it at the machine boundary.  The human-readable cards
            # remain the primary interface.
            if "concept_id" not in value and "id" in value:
                value["concept_id"] = value["id"]
            if "card_path" not in value and "card" in value:
                value["card_path"] = value["card"]
            if "name_zh" not in value and "name" in value:
                value["name_zh"] = value["name"]
            if "name_zh" not in value and "canonical_name_zh" in value:
                value["name_zh"] = value["canonical_name_zh"]
            if "concept_family" not in value and "family" in value:
                value["concept_family"] = value["family"]
            value.setdefault("inventory_path", path.relative_to(root).as_posix())
            records.append(value)
    if not records:
        errors.append(f"no inventory entries under {inventory_root}")
    return records, errors


def _card_paths(root: Path) -> list[Path]:
    return sorted((root / "references" / "ontology" / "cards").glob("**/*.md"))


def _frontmatter(text: str) -> dict[str, str]:
    """Read the tiny optional header used by human cards.

    Cards are Markdown-first; the inventory remains authoritative for identity
    and source anchors. This parser only collects optional card metadata.
    """

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip("`\"'")
    return values


def _card_record(root: Path, path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    header = _frontmatter(text)
    declared_ids: list[str] = []
    if header.get("id"):
        declared_ids.extend(CONCEPT_ID.findall(header["id"]))
    if header.get("covered_ids"):
        declared_ids.extend(CONCEPT_ID.findall(header["covered_ids"]))
    # Core cards often have no front matter. Keep IDs found in the text as
    # optional metadata only; shared cards must not bind one ID to all others.
    declared_ids.extend(CONCEPT_ID.findall(text[:4000]))
    heading = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), path.stem)
    return {
        "name_zh": heading,
        "card_path": path.relative_to(root).as_posix(),
        "card_sha256": sha256(text.encode("utf-8")).hexdigest(),
        "source_anchors": sorted(set(ANCHOR.findall(text))),
        "declared_ids": sorted(set(declared_ids)),
    }


def _merge_records(root: Path, inventory: list[dict[str, object]], errors: list[str]) -> list[dict[str, object]]:
    cards = [_card_record(root, path) for path in _card_paths(root)]
    card_by_path = {str(record["card_path"]): record for record in cards}
    seen: set[str] = set()
    merged: list[dict[str, object]] = []
    for entry in inventory:
        concept_id = entry.get("concept_id")
        disposition = entry.get("disposition")
        if not isinstance(concept_id, str) or not concept_id:
            errors.append(f"inventory entry has no concept_id: {entry}")
            continue
        if concept_id in seen:
            errors.append(f"duplicate concept_id: {concept_id}")
            continue
        seen.add(concept_id)
        if disposition not in ALLOWED_DISPOSITIONS:
            errors.append(f"{concept_id}: invalid disposition {disposition!r}")
        record = dict(entry)
        card_path_value = record.get("card_path")
        if isinstance(card_path_value, str) and card_path_value:
            card_path = root / card_path_value
            if not card_path.is_file():
                errors.append(f"{concept_id}: missing card {card_path}")
            else:
                card = card_by_path.get(card_path_value)
                if card:
                    # Inventory identity and anchors win. A shared card (for
                    # example H1-H6 or S0-S6) cannot replace them.
                    record.setdefault("card_sha256", card["card_sha256"])
                    record.setdefault("card_declared_ids", card["declared_ids"])
                    record.setdefault("card_source_anchors", card["source_anchors"])
                    record.setdefault("card_title", card["name_zh"])
        neighbors = record.get("required_neighbors")
        if not isinstance(neighbors, list):
            neighbors = record.get("required_neighbor_ids", [])
        if not isinstance(neighbors, list):
            neighbors = []
        record["required_neighbors"] = [str(value) for value in neighbors if isinstance(value, str)]
        merged.append(record)
    known = {record["concept_id"] for record in merged}
    semantic_ids = {
        str(record["concept_id"])
        for record in merged
        if record.get("disposition") in SEMANTIC_DISPOSITIONS
    }
    by_card: dict[str, list[str]] = {}
    by_family: dict[str, list[str]] = {}
    for record in merged:
        concept_id = str(record["concept_id"])
        if record.get("disposition") not in SEMANTIC_DISPOSITIONS:
            continue
        card_path = str(record.get("card_path", ""))
        family = str(record.get("concept_family", record.get("family", "unassigned")))
        by_card.setdefault(card_path, []).append(concept_id)
        by_family.setdefault(family, []).append(concept_id)
    for record in merged:
        concept_id = str(record["concept_id"])
        raw_neighbors = [
            neighbor
            for neighbor in record.get("required_neighbors", [])
            if neighbor in known and neighbor in semantic_ids and neighbor != concept_id
        ]
        if record.get("disposition") not in SEMANTIC_DISPOSITIONS:
            neighbors: list[str] = []
        elif len(raw_neighbors) > MAX_NEIGHBORS or not raw_neighbors:
            card_candidates = sorted(set(by_card.get(str(record.get("card_path", "")), [])) - {concept_id})
            family_candidates = sorted(set(by_family.get(str(record.get("concept_family", record.get("family", "unassigned"))), [])) - {concept_id})
            neighbors = (card_candidates or family_candidates)[:MAX_NEIGHBORS]
        else:
            neighbors = sorted(set(raw_neighbors))
        record["required_neighbors"] = neighbors
    return sorted(merged, key=lambda item: str(item["concept_id"]))


def _source_hashes(root: Path) -> dict[str, str]:
    manifest_path = root / "references" / "source" / "v8.3" / "source-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    result: dict[str, str] = {}
    for source_key, output_key in (
        ("raw_sha256", "raw_sha256"),
        ("semantic_sha256", "semantic_sha256"),
    ):
        value = manifest.get(source_key)
        if isinstance(value, str):
            result[output_key] = value
    return result


def _registry_record(
    root: Path,
    record: dict[str, object],
    *,
    validation_status: str,
    source_hashes: dict[str, str],
) -> dict[str, object]:
    """Project authored records into a locator-only machine registry.

    Definitions, interpretations, examples and inference prose stay in the
    inventory shards and Markdown cards. The generated registry deliberately
    carries only identity, routing, relation, hash and validation metadata.
    """

    card_path = record.get("card_path")
    card_exists = isinstance(card_path, str) and bool(card_path) and (root / card_path).is_file()
    hashes = dict(source_hashes)
    for key in ("card_sha256", "source_raw_sha256", "source_semantic_sha256"):
        value = record.get(key)
        if key == "source_raw_sha256":
            output_key = "raw_sha256"
        elif key == "source_semantic_sha256":
            output_key = "semantic_sha256"
        else:
            output_key = key
        if isinstance(value, str):
            hashes[output_key] = value
    disposition = str(record.get("disposition", "unresolved"))
    semantic = disposition in SEMANTIC_DISPOSITIONS
    return {
        "concept_id": str(record["concept_id"]),
        "disposition": disposition,
        "inventory_path": str(record.get("inventory_path", "")),
        "card_path": str(card_path) if isinstance(card_path, str) else None,
        "source_anchors": sorted({str(value) for value in record.get("source_anchors", []) if isinstance(value, str)}),
        "required_neighbors": sorted({str(value) for value in record.get("required_neighbors", []) if isinstance(value, str)}),
        "hashes": hashes,
        "validation": {
            "status": validation_status,
            "source_anchor_binding": "declared" if record.get("source_anchors") else "missing",
            "card_binding": "declared" if card_exists else ("missing" if isinstance(card_path, str) and card_path else "not_applicable"),
            "relation_binding": "bounded" if semantic and record.get("required_neighbors") else ("missing" if semantic else "not_applicable"),
        },
    }


def _field_anchor_values(record: dict[str, object]) -> set[str]:
    anchors: set[str] = set()

    def visit(value: object, *, inside_field_anchors: bool = False) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                visit(
                    child,
                    inside_field_anchors=(inside_field_anchors or key == "field_anchors"),
                )
        elif isinstance(value, list):
            for child in value:
                if (
                    inside_field_anchors
                    and isinstance(child, str)
                    and SOURCE_ANCHOR.fullmatch(child)
                ):
                    anchors.add(child)
                else:
                    visit(child, inside_field_anchors=inside_field_anchors)

    visit(record)
    return anchors


def _record_aliases(record: dict[str, object]) -> set[str]:
    aliases = {
        value.strip()
        for key in (
            "qualified_id",
            "name",
            "name_zh",
            "canonical_name_zh",
            "authoritative_name_zh",
        )
        for value in [record.get(key)]
        if isinstance(value, str) and value.strip()
    }
    qualified_id = record.get("qualified_id")
    if isinstance(qualified_id, str) and ":" in qualified_id:
        aliases.add(qualified_id.rsplit(":", 1)[-1].strip())
    concept_id = str(record.get("concept_id", ""))
    short_code = re.search(
        r"-(HV\d{2}|H[1-6]|S[0-6]|X0|D[0-3]|M\d{2}|T[0-4])$",
        concept_id,
    )
    if short_code:
        aliases.add(short_code.group(1))
    return {alias for alias in aliases if len(alias) >= 2}


def _parent_authority_context(
    root: Path,
    records: list[dict[str, object]],
    errors: list[str],
) -> dict[str, Any]:
    semantic_records = [
        record
        for record in records
        if record.get("disposition") in SEMANTIC_DISPOSITIONS
    ]
    exact_owners: dict[str, set[str]] = {}
    field_owners: dict[str, set[str]] = {}
    alias_owners: dict[str, set[str]] = {}
    for record in semantic_records:
        concept_id = str(record["concept_id"])
        for anchor in record.get("source_anchors", []):
            if isinstance(anchor, str):
                exact_owners.setdefault(anchor, set()).add(concept_id)
        for anchor in _field_anchor_values(record):
            field_owners.setdefault(anchor, set()).add(concept_id)
        for alias in _record_aliases(record):
            alias_owners.setdefault(alias, set()).add(concept_id)

    paragraph_path = (
        root / "references" / "source" / "v8.3" / "audit" / "paragraphs.jsonl"
    )
    paragraphs: list[dict[str, object]] = []
    if paragraph_path.is_file():
        try:
            paragraphs = [
                value
                for line in paragraph_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
                for value in [json.loads(line)]
                if isinstance(value, dict)
                and isinstance(value.get("anchor"), str)
            ]
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"cannot derive source parent authority from paragraphs: {exc}")

    paragraph_position = {
        str(paragraph["anchor"]): index
        for index, paragraph in enumerate(paragraphs)
    }
    section_indexes = [
        index
        for index, paragraph in enumerate(paragraphs)
        if paragraph.get("style") in STRUCTURAL_SECTION_STYLES
    ]
    section_ranges: list[tuple[int, int, int, str]] = []
    for section_offset, start in enumerate(section_indexes):
        style = str(paragraphs[start].get("style", ""))
        level = STRUCTURAL_SECTION_STYLES[style]
        end = len(paragraphs)
        for later in section_indexes[section_offset + 1 :]:
            later_level = STRUCTURAL_SECTION_STYLES[
                str(paragraphs[later].get("style", ""))
            ]
            if later_level <= level:
                end = later
                break
        section_ranges.append(
            (start, end, level, str(paragraphs[start]["anchor"]))
        )

    active_scopes: dict[str, tuple[str, ...]] = {}
    for anchor, position in paragraph_position.items():
        active_scopes[anchor] = tuple(
            section_anchor
            for start, end, _level, section_anchor in section_ranges
            if start <= position < end
        )

    card_section_owners: dict[str, set[str]] = {}
    for start, end, _level, section_anchor in section_ranges:
        if paragraphs[start].get("style") != "CardLabel":
            continue
        owners: set[str] = set(exact_owners.get(section_anchor, set()))
        for paragraph in paragraphs[start:end]:
            anchor = str(paragraph["anchor"])
            owners.update(exact_owners.get(anchor, set()))
            owners.update(field_owners.get(anchor, set()))
        if owners:
            for paragraph in paragraphs[start:end]:
                card_section_owners[str(paragraph["anchor"])] = set(owners)

    tables_path = root / "references" / "source" / "v8.3" / "indexes" / "tables.json"
    table_rows: dict[str, list[dict[str, object]]] = {}
    paragraph_rows: dict[str, dict[str, object]] = {}
    source_unit_scope_anchors: dict[str, str] = {}
    if tables_path.is_file():
        try:
            table_values = json.loads(tables_path.read_text(encoding="utf-8"))
            if isinstance(table_values, list):
                for table in table_values:
                    if not isinstance(table, dict) or not isinstance(
                        table.get("anchor"), str
                    ):
                        continue
                    table_anchor = str(table["anchor"])
                    rows = table.get("rows")
                    bindings = table.get("cell_paragraph_ordinals")
                    if not isinstance(rows, list) or not isinstance(bindings, list):
                        continue
                    table_rows[table_anchor] = []
                    for row_index, (cells, row_bindings) in enumerate(
                        zip(rows, bindings, strict=True), 1
                    ):
                        if not isinstance(cells, list) or not isinstance(
                            row_bindings, list
                        ):
                            continue
                        anchors = [
                            f"V83-P{ordinal:04d}"
                            for cell in row_bindings
                            if isinstance(cell, list)
                            for ordinal in cell
                            if isinstance(ordinal, int)
                        ]
                        row = {
                            "table_anchor": table_anchor,
                            "row_index": row_index,
                            "row_anchor": f"{table_anchor}-R{row_index:03d}",
                            "cells": [str(cell) for cell in cells],
                            "source_anchors": anchors,
                        }
                        table_rows[table_anchor].append(row)
                        if anchors:
                            source_unit_scope_anchors.setdefault(table_anchor, anchors[0])
                            source_unit_scope_anchors[str(row["row_anchor"])] = anchors[0]
                        for anchor in anchors:
                            paragraph_rows[anchor] = row
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"cannot derive source parent authority from tables: {exc}")

    return {
        "exact_owners": exact_owners,
        "field_owners": field_owners,
        "alias_owners": alias_owners,
        "active_scopes": active_scopes,
        "card_section_owners": card_section_owners,
        "table_rows": table_rows,
        "paragraph_rows": paragraph_rows,
        "source_unit_scope_anchors": source_unit_scope_anchors,
        "paragraphs_available": bool(paragraphs),
    }


def _exact_alias_owners(text: str, context: dict[str, Any]) -> set[str]:
    return set(context["alias_owners"].get(text.strip(), set()))


def _candidate_row(
    candidate: dict[str, object], context: dict[str, Any]
) -> dict[str, object] | None:
    if candidate.get("source_unit_type") == "table_row":
        table_anchor = candidate.get("source_table_anchor")
        row_index = candidate.get("source_table_row_index")
        rows = context["table_rows"].get(table_anchor, [])
        if isinstance(row_index, int) and 1 <= row_index <= len(rows):
            return rows[row_index - 1]
    for anchor in candidate.get("source_anchors", []):
        if isinstance(anchor, str) and anchor in context["paragraph_rows"]:
            return context["paragraph_rows"][anchor]
    return None


def _authority_record(
    kind: str,
    parent_ids: set[str] | list[str],
    evidence_anchors: set[str] | list[str],
) -> dict[str, object]:
    return {
        "kind": kind,
        "derived_parent_concept_ids": sorted(set(parent_ids)),
        "evidence_anchors": sorted(set(evidence_anchors)),
    }


def _scopes_overlap(
    left_anchor: str,
    right_anchor: str,
    context: dict[str, Any],
) -> bool:
    left_anchor = context["source_unit_scope_anchors"].get(left_anchor, left_anchor)
    right_anchor = context["source_unit_scope_anchors"].get(right_anchor, right_anchor)
    if left_anchor == right_anchor:
        return True
    left = set(context["active_scopes"].get(left_anchor, ()))
    right = set(context["active_scopes"].get(right_anchor, ()))
    return bool(left & right)


def _derive_parent_authority(
    candidate: dict[str, object],
    context: dict[str, Any],
    *,
    review: dict[str, object] | None = None,
) -> dict[str, object]:
    source_anchor = str(candidate.get("source_anchor", ""))
    source_anchors = [
        str(anchor)
        for anchor in candidate.get("source_anchors", [])
        if isinstance(anchor, str)
    ]
    row = _candidate_row(candidate, context)
    table_anchor = (
        str(row["table_anchor"])
        if isinstance(row, dict)
        else str(candidate.get("source_table_anchor", ""))
    )
    unit_type = str(candidate.get("source_unit_type", ""))

    if table_anchor == "V83-T001" or (
        table_anchor == "V83-T120" and unit_type == "table_row"
    ) or source_anchor in NAVIGATION_TABLES:
        return _authority_record("source_section", set(), [source_anchor])

    alias_ids = _exact_alias_owners(str(candidate.get("source_text", "")), context)
    if alias_ids and (row is None or table_anchor in {"V83-T119", "V83-T120"}):
        return _authority_record(
            "table_row_alias_equality" if row is not None else "exact_alias_equality",
            alias_ids,
            source_anchors or [source_anchor],
        )
    if row is not None and table_anchor == "V83-T119":
        row_alias_ids: set[str] = set()
        for cell in row.get("cells", []):
            row_alias_ids.update(_exact_alias_owners(str(cell), context))
        if row_alias_ids:
            return _authority_record(
                (
                    "table_row_alias_equality"
                    if unit_type == "table_row"
                    else "table_row_owner"
                ),
                row_alias_ids,
                [str(value) for value in row.get("source_anchors", [])],
            )

    field_ids: set[str] = set()
    field_evidence: set[str] = set()
    for anchor in [source_anchor, *source_anchors]:
        owners = context["field_owners"].get(anchor, set())
        if owners:
            field_ids.update(owners)
            field_evidence.add(anchor)
    if field_ids:
        return _authority_record("inventory_field_anchor", field_ids, field_evidence)

    card_ids: set[str] = set()
    card_evidence: set[str] = set()
    for anchor in source_anchors:
        owners = context["card_section_owners"].get(anchor, set())
        if owners:
            card_ids.update(owners)
            card_evidence.add(anchor)
    if card_ids:
        return _authority_record("card_label_section", card_ids, card_evidence)

    if row is not None:
        row_ids: set[str] = set()
        row_evidence: set[str] = set()
        for anchor in row.get("source_anchors", []):
            owners = set(context["exact_owners"].get(anchor, set()))
            owners |= context["field_owners"].get(anchor, set())
            if owners:
                row_ids.update(owners)
                row_evidence.add(str(anchor))
        if row_ids:
            return _authority_record("table_row_owner", row_ids, row_evidence)

    if review is not None and not context["paragraphs_available"]:
        claimed = {
            str(parent)
            for parent in review.get("parent_concept_ids", [])
            if isinstance(parent, str)
        }
        source_basis = review.get("source_basis")
        relations = (
            source_basis.get("parent_relations", [])
            if isinstance(source_basis, dict)
            else []
        )
        derived: set[str] = set()
        evidence: set[str] = set()
        candidate_scope_anchor = source_anchors[0] if source_anchors else source_anchor
        for relation in relations:
            if not isinstance(relation, dict):
                continue
            parent_id = relation.get("parent_concept_id")
            evidence_anchor = relation.get("evidence_anchor")
            if not isinstance(parent_id, str) or not isinstance(evidence_anchor, str):
                continue
            strong_owners = set(context["exact_owners"].get(evidence_anchor, set()))
            strong_owners.update(context["field_owners"].get(evidence_anchor, set()))
            local = _scopes_overlap(candidate_scope_anchor, evidence_anchor, context)
            if not context["paragraphs_available"]:
                local = True
            if local and (not strong_owners or parent_id in strong_owners):
                derived.add(parent_id)
                evidence.add(evidence_anchor)
        if derived == claimed:
            return _authority_record("source_section", derived, evidence)

    return _authority_record("source_section", set(), source_anchors or [source_anchor])


def _read_candidate_reviews(
    root: Path,
    records: list[dict[str, object]],
    candidates: list[dict[str, object]],
    errors: list[str],
    parent_context: dict[str, Any],
) -> dict[str, dict[str, object]]:
    path = root / "references" / "ontology" / "candidate-semantic-scopes.json"
    if not path.is_file():
        return {}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read authored exact candidate reviews: {exc}")
        return {}
    if not isinstance(document, dict):
        errors.append("authored exact candidate reviews must be an object")
        return {}
    if document.get("schema_id") != "xi-kari.v8.3.candidate-semantic-scopes":
        errors.append("exact candidate reviews have an invalid schema_id")
    if document.get("schema_version") != 3:
        errors.append("exact candidate reviews have an invalid schema_version")
    if document.get("framework_version") != "v8.3":
        errors.append("exact candidate reviews have an invalid framework_version")
    if document.get("review_count_semantics") != EXACT_REVIEW_COUNT_SEMANTICS:
        errors.append("exact candidate reviews must disclaim ontology cardinality")
    raw_reviews = document.get("reviews")
    if not isinstance(raw_reviews, list):
        errors.append("exact candidate reviews must contain a reviews list")
        return {}

    records_by_id = {str(record["concept_id"]): record for record in records}
    semantic_ids = {
        str(record["concept_id"])
        for record in records
        if record.get("disposition") in SEMANTIC_DISPOSITIONS
    }
    candidates_by_id = {
        str(candidate.get("candidate_id")): candidate for candidate in candidates
    }
    source_units = {
        str(candidate.get("source_anchor")): candidate.get("source_text")
        for candidate in candidates
        if isinstance(candidate.get("source_anchor"), str)
        and isinstance(candidate.get("source_text"), str)
    }
    paragraph_path = (
        root
        / "references"
        / "source"
        / "v8.3"
        / "audit"
        / "paragraphs.jsonl"
    )
    if paragraph_path.is_file():
        try:
            for line in paragraph_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                paragraph = json.loads(line)
                if (
                    isinstance(paragraph, dict)
                    and isinstance(paragraph.get("anchor"), str)
                    and isinstance(paragraph.get("text"), str)
                ):
                    source_units[paragraph["anchor"]] = paragraph["text"]
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"cannot read exact review source units: {exc}")
    reviews: dict[str, dict[str, object]] = {}
    for index, raw_review in enumerate(raw_reviews):
        if not isinstance(raw_review, dict):
            errors.append(f"exact candidate review {index} must be an object")
            continue
        candidate_id = raw_review.get("candidate_id")
        if not isinstance(candidate_id, str) or not SOURCE_CANDIDATE_ID.fullmatch(
            candidate_id
        ):
            errors.append(
                f"exact candidate review {index} has invalid candidate_id {candidate_id!r}"
            )
            continue
        if candidate_id in reviews:
            errors.append(f"duplicate exact candidate review: {candidate_id}")
            continue
        source_anchor = raw_review.get("source_anchor")
        if not isinstance(source_anchor, str) or not SOURCE_ANCHOR.fullmatch(source_anchor):
            errors.append(f"{candidate_id}: invalid exact review source_anchor")
        fingerprint = raw_review.get("semantic_fingerprint_sha256")
        if not isinstance(fingerprint, str) or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
            errors.append(f"{candidate_id}: invalid exact review semantic fingerprint")
        disposition = raw_review.get("disposition")
        if disposition not in ALLOWED_DISPOSITIONS - {"unresolved"}:
            errors.append(f"{candidate_id}: invalid exact review disposition {disposition!r}")
        bound_ids = raw_review.get("bound_concept_ids")
        parent_ids = raw_review.get("parent_concept_ids")
        if not isinstance(bound_ids, list):
            errors.append(f"{candidate_id}: bound_concept_ids must be a list")
            bound_ids = []
        if not isinstance(parent_ids, list):
            errors.append(f"{candidate_id}: parent_concept_ids must be a list")
            parent_ids = []
        source_basis = raw_review.get("source_basis")
        parent_relations = (
            source_basis.get("parent_relations")
            if isinstance(source_basis, dict)
            else None
        )
        evidence_parent_ids = {
            relation.get("parent_concept_id")
            for relation in parent_relations
            if isinstance(relation, dict)
            and isinstance(relation.get("parent_concept_id"), str)
        } if isinstance(parent_relations, list) else set()
        if set(parent_ids) != evidence_parent_ids:
            errors.append(
                f"{candidate_id}: parent relation evidence does not match parent_concept_ids"
            )
        if isinstance(parent_relations, list):
            for relation in parent_relations:
                if not isinstance(relation, dict):
                    continue
                parent_id = relation.get("parent_concept_id")
                expected_card = (
                    records_by_id[parent_id].get("card_path")
                    if isinstance(parent_id, str) and parent_id in records_by_id
                    else None
                )
                if relation.get("parent_card_path") != expected_card:
                    errors.append(
                        f"{candidate_id}: parent relation card does not match {parent_id}"
                    )
                evidence_anchor = relation.get("evidence_anchor")
                if (
                    not isinstance(evidence_anchor, str)
                    or source_units.get(evidence_anchor)
                    != relation.get("evidence_excerpt")
                ):
                    errors.append(
                        f"{candidate_id}: parent relation evidence is not source-exact at {evidence_anchor}"
                    )
                if relation.get("evidence_kind") == "source_card_match":
                    card_excerpt = relation.get("card_excerpt")
                    card_text = ""
                    if isinstance(expected_card, str):
                        card_path = root / expected_card
                        if card_path.is_file():
                            card_text = card_path.read_text(encoding="utf-8")
                    if (
                        not isinstance(card_excerpt, str)
                        or not card_excerpt
                        or card_excerpt not in card_text
                    ):
                        errors.append(
                            f"{candidate_id}: source_card_match excerpt is absent from the parent card"
                        )
                elif relation.get("evidence_kind") != "authored_relation":
                    errors.append(
                        f"{candidate_id}: parent relation has an invalid evidence_kind"
                    )
                relation_note = relation.get("relation_note")
                if not isinstance(relation_note, str) or not relation_note.strip():
                    errors.append(
                        f"{candidate_id}: parent relation has no authored relation_note"
                    )
        candidate = candidates_by_id.get(candidate_id)
        if (
            not isinstance(source_basis, dict)
            or not isinstance(candidate, dict)
            or source_basis.get("source_excerpt") != candidate.get("source_text")
        ):
            errors.append(
                f"{candidate_id}: source_basis excerpt does not match the exact source candidate"
            )
        if (
            not isinstance(source_basis, dict)
            or source_basis.get("disposition") != disposition
        ):
            errors.append(
                f"{candidate_id}: source_basis disposition contradicts exact review disposition"
            )
        context_evidence = (
            source_basis.get("context_evidence")
            if isinstance(source_basis, dict)
            else None
        )
        current_source_is_bound = False
        if not isinstance(context_evidence, list) or not context_evidence:
            errors.append(f"{candidate_id}: exact review has no source context evidence")
        else:
            for context_row in context_evidence:
                if not isinstance(context_row, dict):
                    errors.append(f"{candidate_id}: invalid source context evidence")
                    continue
                context_anchor = context_row.get("source_anchor")
                context_excerpt = context_row.get("source_excerpt")
                if (
                    not isinstance(context_anchor, str)
                    or source_units.get(context_anchor) != context_excerpt
                ):
                    errors.append(
                        f"{candidate_id}: source context evidence is not exact at {context_anchor}"
                    )
                if (
                    isinstance(candidate, dict)
                    and context_anchor == candidate.get("source_anchor")
                    and context_excerpt == candidate.get("source_text")
                ):
                    current_source_is_bound = True
        if not current_source_is_bound:
            errors.append(
                f"{candidate_id}: source context evidence omits the exact candidate unit"
            )
        if disposition in SEMANTIC_DISPOSITIONS:
            if not bound_ids:
                errors.append(f"{candidate_id}: semantic review has no bound concept")
            elif any(
                concept_id not in semantic_ids
                or records_by_id[concept_id].get("disposition") != disposition
                for concept_id in bound_ids
            ):
                errors.append(f"{candidate_id}: semantic review has an incompatible binding")
            if parent_ids:
                errors.append(f"{candidate_id}: semantic review cannot have parent concepts")
        elif disposition in {"subordinate_value", "alias"}:
            if not parent_ids or any(parent not in semantic_ids for parent in parent_ids):
                errors.append(f"{candidate_id}: exact review has unknown semantic parents")
            if bound_ids:
                errors.append(f"{candidate_id}: subordinate review cannot bind concepts")
            if isinstance(candidate, dict):
                parent_authority = _derive_parent_authority(
                    candidate,
                    parent_context,
                    review=raw_review,
                )
                derived_parent_ids = parent_authority[
                    "derived_parent_concept_ids"
                ]
                if derived_parent_ids != sorted(str(parent) for parent in parent_ids):
                    errors.append(
                        f"{candidate_id}: derived parent concepts "
                        f"{derived_parent_ids} do not match review "
                        f"parent_concept_ids {sorted(str(parent) for parent in parent_ids)}"
                    )
        elif bound_ids or parent_ids:
            errors.append(f"{candidate_id}: nonsemantic exact review cannot bind concepts")
        note = raw_review.get("review_note")
        if not isinstance(note, str) or not note.strip():
            errors.append(f"{candidate_id}: exact review has no review_note")
        elif not isinstance(source_basis, dict) or note != source_basis.get(
            "decision_note"
        ):
            errors.append(
                f"{candidate_id}: review_note contradicts source_basis decision_note"
            )
        elif (
            not isinstance(source_anchor, str)
            or source_anchor not in note
            or str(disposition) not in note
            or any(str(parent_id) not in note for parent_id in parent_ids)
        ):
            errors.append(
                f"{candidate_id}: review_note contradicts its anchor, disposition, or parents"
            )
        reviews[candidate_id] = dict(raw_review)
    return reviews


def _candidate_census(
    root: Path,
    records: list[dict[str, object]],
    errors: list[str],
) -> list[dict[str, object]]:
    """Dispose every deterministic source candidate against authored semantics.

    The source extractor deliberately over-generates.  This pass never promotes
    an unbound keyword into a concept.  It binds authored concepts where a card
    and exact source anchor exist; otherwise it records the source unit as a
    heading, explicit source gap, example, or an exact authored candidate
    review. Every decision retains the complete source record and a
    candidate-specific explanation.
    """

    path = root / "references" / "source" / "v8.3" / "indexes" / "candidates.jsonl"
    if not path.is_file():
        return []
    candidates: list[dict[str, object]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{line_number}: invalid candidate JSON: {exc}")
            continue
        if not isinstance(candidate, dict):
            errors.append(f"{path}:{line_number}: source candidate must be object")
            continue
        candidates.append(candidate)

    by_anchor: dict[str, list[dict[str, object]]] = {}
    records_by_id = {str(record["concept_id"]): record for record in records}
    for record in records:
        for anchor in record.get("source_anchors", []):
            if isinstance(anchor, str):
                by_anchor.setdefault(anchor, []).append(record)
    semantic_ids = {
        str(record["concept_id"])
        for record in records
        if record.get("disposition") in SEMANTIC_DISPOSITIONS
    }
    if candidates and not semantic_ids:
        errors.append("candidate census cannot resolve a semantic parent: no authored semantic concepts")
        return []
    parent_context = _parent_authority_context(root, records, errors)
    reviews = _read_candidate_reviews(
        root,
        records,
        candidates,
        errors,
        parent_context,
    )
    used_review_ids: set[str] = set()
    table_outcomes: dict[str, dict[str, object]] = {}
    table_heading_anchors = {
        anchor
        for candidate in candidates
        if candidate.get("source_unit_type") == "table_row"
        and candidate.get("source_style") == "TableHead"
        for anchor in candidate.get("source_anchors", [])
        if isinstance(anchor, str)
    }

    reviewed: list[dict[str, object]] = []
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id", ""))
        anchor = str(candidate.get("source_anchor", ""))
        kinds = [str(value) for value in candidate.get("candidate_kinds", [])]
        text = str(candidate.get("source_text", ""))
        source_style = str(candidate.get("source_style", ""))
        anchored = sorted(
            by_anchor.get(anchor, []), key=lambda record: str(record.get("concept_id", ""))
        )
        authored_semantics = [
            record for record in anchored if record.get("disposition") in SEMANTIC_DISPOSITIONS
        ]
        authored_other = [
            record for record in anchored if record.get("disposition") not in SEMANTIC_DISPOSITIONS
        ]
        bound_ids: list[str] = []
        bound_cards: list[str] = []
        parent_ids: list[str] = []
        parent_cards: list[str] = []
        review = reviews.get(candidate_id)
        if review is not None and (
            review.get("source_anchor") != anchor
            or review.get("semantic_fingerprint_sha256")
            != candidate.get("semantic_fingerprint_sha256")
        ):
            errors.append(f"{candidate_id}: exact candidate review binding mismatch")
            review = None
        parent_authority = _derive_parent_authority(
            candidate,
            parent_context,
            review=review,
        )
        row = _candidate_row(candidate, parent_context)
        row_table_anchor = (
            str(row["table_anchor"])
            if isinstance(row, dict)
            else str(candidate.get("source_table_anchor", ""))
        )
        unit_type = str(candidate.get("source_unit_type", ""))
        navigation_unit = (
            anchor in NAVIGATION_TABLES
            or row_table_anchor == "V83-T001"
            or (row_table_anchor == "V83-T120" and unit_type == "table_row")
        )

        if navigation_unit:
            if review is not None:
                used_review_ids.add(candidate_id)
            disposition = "heading_only"
            reason = "source_navigation_unit"
            note = (
                f"{anchor} 属于源文档的阅读地图或术语导航，只承担定位责任；"
                "导航行和整表不归入其中任一被列概念。"
            )
            if isinstance(row, dict):
                row_anchor = row.get("row_anchor")
                if isinstance(row_anchor, str):
                    table_outcomes[row_anchor] = {
                        "disposition": disposition,
                        "bound_concept_ids": [],
                        "parent_concept_ids": [],
                    }
            if row_table_anchor:
                table_outcomes.setdefault(
                    row_table_anchor,
                    {
                        "disposition": disposition,
                        "bound_concept_ids": [],
                        "parent_concept_ids": [],
                    },
                )
        elif unit_type == "table_row":
            inherited = table_outcomes.get(row_table_anchor)
            if source_style == "TableHead" or "heading" in kinds:
                disposition = "heading_only"
                reason = "source_table_row_heading"
                note = f"{anchor} 是表格列头行，只规定本表的阅读结构。"
            elif review is not None and review.get("disposition") in {
                "subordinate_value",
                "alias",
            }:
                used_review_ids.add(candidate_id)
                disposition = str(review["disposition"])
                reason = "authored_exact_candidate_review"
                parent_ids = sorted(
                    str(parent) for parent in review.get("parent_concept_ids", [])
                )
                parent_cards = sorted(
                    {
                        str(records_by_id[parent].get("card_path"))
                        for parent in parent_ids
                        if parent in records_by_id
                        and isinstance(records_by_id[parent].get("card_path"), str)
                        and records_by_id[parent].get("card_path")
                    }
                )
                note = str(review["review_note"])
            elif inherited and inherited.get("disposition") == "example_only":
                disposition = "example_only"
                reason = "source_table_example_row"
                note = f"{anchor} 是源文明确标示的示例表中的一行，不生成概念父项。"
                parent_authority = _authority_record(
                    "table_row_owner", set(), candidate.get("source_anchors", [])
                )
            elif parent_authority["derived_parent_concept_ids"]:
                parent_ids = list(parent_authority["derived_parent_concept_ids"])
                parent_cards = sorted(
                    {
                        str(records_by_id[parent].get("card_path"))
                        for parent in parent_ids
                        if parent in records_by_id
                        and isinstance(records_by_id[parent].get("card_path"), str)
                        and records_by_id[parent].get("card_path")
                    }
                )
                disposition = (
                    "alias"
                    if parent_authority["kind"]
                    in {"table_row_alias_equality", "exact_alias_equality"}
                    else "subordinate_value"
                )
                reason = "derived_table_row_parent_authority"
                note = (
                    f"{anchor} 以精确表格行 {', '.join(candidate.get('source_anchors', []))} "
                    f"归入 {', '.join(parent_ids)}；整表跨度不能覆盖或改写该行归属。"
                )
            elif inherited:
                inherited_disposition = str(inherited.get("disposition", "unresolved"))
                if inherited_disposition in SEMANTIC_DISPOSITIONS:
                    parent_ids = [
                        str(value) for value in inherited.get("bound_concept_ids", [])
                    ]
                    disposition = "subordinate_value"
                elif inherited_disposition in {"subordinate_value", "alias"}:
                    parent_ids = [
                        str(value) for value in inherited.get("parent_concept_ids", [])
                    ]
                    disposition = "subordinate_value"
                else:
                    disposition = inherited_disposition
                parent_cards = sorted(
                    {
                        str(records_by_id[parent].get("card_path"))
                        for parent in parent_ids
                        if parent in records_by_id
                        and isinstance(records_by_id[parent].get("card_path"), str)
                        and records_by_id[parent].get("card_path")
                    }
                )
                reason = "derived_table_row_owner"
                parent_authority = _authority_record(
                    "table_row_owner",
                    parent_ids,
                    candidate.get("source_anchors", []),
                )
                note = (
                    f"{anchor} 保留为精确表格行，并从已验证的 {row_table_anchor} "
                    f"结构归属取得终态 {disposition}。"
                )
            else:
                disposition = "unresolved"
                reason = "no_table_row_parent_authority"
                note = f"{anchor} 尚无可独立复核的表格行父项。"
        elif source_style.startswith("TOC"):
            disposition = "heading_only"
            reason = "source_table_of_contents_heading"
            note = (
                f"{anchor} 使用 {source_style} 目录样式，只承担源文档导航与阅读顺序。"
                "目录词项不因变量、算子或约束关键词自动升级为正式概念。"
            )
        elif (
            bool(kinds)
            and set(kinds) <= {"heading", "variable"}
            and not (
                review is not None
                and review.get("disposition") in {"alias", "subordinate_value"}
            )
            and (
                any(
                    record.get("disposition") == "heading_only"
                    for record in anchored
                )
                or (
                    unit_type == "paragraph"
                    and source_style == "TableText"
                    and len(text.strip()) <= 100
                    and isinstance(row, dict)
                    and table_outcomes.get(str(row.get("row_anchor")), {}).get(
                        "disposition"
                    )
                    == "heading_only"
                )
            )
        ):
            if review is not None and review.get("disposition") in SEMANTIC_DISPOSITIONS:
                errors.append(
                    f"{candidate_id}: exact semantic review cannot override source heading/navigation gate"
                )
            disposition = "heading_only"
            reason = (
                "source_heading_navigation_conflict"
                if any(
                    record.get("disposition") == "heading_only"
                    for record in anchored
                )
                else "source_navigation_enumeration"
            )
            note = (
                f"{anchor} 只提供标题或导航枚举信号，不形成独立 v8.3 定义；"
                "同锚点的 heading_only 或所属导航表行优先约束该候选。"
            )
            bound_ids = []
            bound_cards = []
            parent_ids = []
            parent_cards = []
            parent_authority = _authority_record(
                "source_navigation", set(), [anchor]
            )
        elif authored_semantics:
            structural = [
                record for record in authored_semantics if record.get("disposition") == "structural_rule"
            ]
            canonical = [
                record for record in authored_semantics if record.get("disposition") == "canonical_concept"
            ]
            selected = authored_semantics
            disposition = (
                "structural_rule"
                if structural and ({"constraint", "operator"} & set(kinds))
                else "canonical_concept"
                if canonical
                else "structural_rule"
            )
            reason = "authored_anchor_semantic_binding"
            bound_ids = sorted(str(record["concept_id"]) for record in selected)
            bound_cards = sorted(
                {
                    str(record.get("card_path"))
                    for record in selected
                    if isinstance(record.get("card_path"), str) and record.get("card_path")
                }
            )
            note = (
                f"{anchor} 与已审概念卡 {', '.join(bound_ids)} 共享精确原文锚点；"
                f"源单元信号为 {', '.join(kinds)}，因此按 {disposition} 绑定。"
                "概念边界、允许推论和非等价锁仍以对应卡片及原文为准。"
            )
        elif (
            parent_authority["kind"]
            in {"table_row_alias_equality", "exact_alias_equality"}
            and parent_authority["derived_parent_concept_ids"]
        ):
            if review is not None:
                used_review_ids.add(candidate_id)
            disposition = "alias"
            reason = "derived_exact_alias_equality"
            parent_ids = list(parent_authority["derived_parent_concept_ids"])
            parent_cards = sorted(
                {
                    str(records_by_id[parent].get("card_path"))
                    for parent in parent_ids
                    if parent in records_by_id
                    and isinstance(records_by_id[parent].get("card_path"), str)
                    and records_by_id[parent].get("card_path")
                }
            )
            note = (
                str(review.get("review_note"))
                if review is not None
                else (
                    f"{anchor} 与源表格行或术语中的正式别名精确相等；"
                    f"其父概念独立解析为 {', '.join(parent_ids)}。"
                )
            )
        elif (
            review is None
            and parent_authority["kind"]
            in {
                "inventory_field_anchor",
                "card_label_section",
                "table_row_owner",
            }
            and parent_authority["derived_parent_concept_ids"]
        ):
            disposition = "subordinate_value"
            reason = "derived_source_parent_authority"
            parent_ids = list(parent_authority["derived_parent_concept_ids"])
            parent_cards = sorted(
                {
                    str(records_by_id[parent].get("card_path"))
                    for parent in parent_ids
                    if parent in records_by_id
                    and isinstance(records_by_id[parent].get("card_path"), str)
                    and records_by_id[parent].get("card_path")
                }
            )
            note = (
                f"{anchor} 的父项由 {parent_authority['kind']} 独立解析为 "
                f"{', '.join(parent_ids)}。"
            )
        elif "undefined_field" in kinds:
            disposition = "source_undefined"
            reason = "explicit_source_undefined_field"
            note = (
                f"{anchor} 明示未定义或不可推出字段："
                f"{'、'.join(str(value) for value in candidate.get('source_undefined_fields', []))}。"
                "该缺口保持为源内未定义，不能被解释层或外部材料补写成 v8.3 定义。"
            )
        elif "heading" in kinds:
            disposition = "heading_only"
            reason = "source_heading_without_independent_definition_card"
            note = (
                f"{anchor} 是源结构标题，但没有独立、同锚点的正式概念卡。"
                "它用于保持阅读顺序和章节边界，不因标题形态自动升级为概念。"
            )
        elif review is None and any(marker in text for marker in EXAMPLE_MARKERS):
            disposition = "example_only"
            reason = "source_example_or_instantiation"
            note = (
                f"{anchor} 以示例或实例化方式承载 {', '.join(kinds)} 信号；"
                "它可说明相邻规则如何落地，但不能单独生成新的 v8.3 定义。"
            )
        elif authored_other:
            selected = authored_other[0]
            disposition = str(selected.get("disposition"))
            if (
                disposition == "unresolved"
                or (disposition == "heading_only" and "heading" not in kinds)
                or (disposition == "source_undefined" and "undefined_field" not in kinds)
            ):
                disposition = "unresolved"
            reason = (
                "authored_nonsemantic_anchor_binding"
                if disposition != "unresolved"
                else "no_exact_candidate_review"
            )
            if disposition in {"subordinate_value", "alias"}:
                if review and review.get("disposition") == disposition:
                    used_review_ids.add(candidate_id)
                    parent_ids = sorted(
                        str(parent) for parent in review.get("parent_concept_ids", [])
                    )
                    parent_cards = sorted(
                        {
                            str(records_by_id[parent].get("card_path"))
                            for parent in parent_ids
                            if parent in records_by_id
                            and isinstance(records_by_id[parent].get("card_path"), str)
                            and records_by_id[parent].get("card_path")
                        }
                    )
                else:
                    disposition = "unresolved"
                    reason = "no_exact_candidate_review"
            note = (
                f"{anchor} 命中已审的非独立条目 {selected.get('concept_id')}，"
                f"终态为 {disposition}；该处置不把标题、例示或缺失标记伪装成正式概念。"
            )
        elif review:
            used_review_ids.add(candidate_id)
            disposition = str(review.get("disposition"))
            reason = "authored_exact_candidate_review"
            bound_ids = sorted(
                str(concept_id) for concept_id in review.get("bound_concept_ids", [])
            )
            parent_ids = sorted(
                str(parent) for parent in review.get("parent_concept_ids", [])
            )
            bound_cards = sorted(
                {
                    str(records_by_id[concept_id].get("card_path"))
                    for concept_id in bound_ids
                    if concept_id in records_by_id
                    and isinstance(records_by_id[concept_id].get("card_path"), str)
                    and records_by_id[concept_id].get("card_path")
                }
            )
            parent_cards = sorted(
                {
                    str(records_by_id[parent].get("card_path"))
                    for parent in parent_ids
                    if parent in records_by_id
                    and isinstance(records_by_id[parent].get("card_path"), str)
                    and records_by_id[parent].get("card_path")
                }
            )
            note = str(review.get("review_note"))
            heading_signal = (
                "heading" in kinds
                or source_style in {"TableHead", "CardLabel"}
                or anchor in table_heading_anchors
                or "导航索引" in text
            )
            review_source_basis = review.get("source_basis")
            review_context = (
                review_source_basis.get("context_evidence", [])
                if isinstance(review_source_basis, dict)
                else []
            )
            example_context = any(
                isinstance(context_row, dict)
                and isinstance(context_row.get("source_excerpt"), str)
                and (
                    any(
                        marker in context_row["source_excerpt"]
                        for marker in EXAMPLE_MARKERS
                    )
                    or "一个虚拟" in context_row["source_excerpt"]
                    or "一个具体事件" in context_row["source_excerpt"]
                    or (
                        "虚拟" in context_row["source_excerpt"]
                        and "例" in context_row["source_excerpt"]
                    )
                )
                for context_row in review_context
            )
            if disposition == "heading_only" and not heading_signal:
                errors.append(f"{candidate_id}: heading_only review has no heading signal")
                disposition = "unresolved"
            elif disposition == "example_only" and not any(
                marker in text for marker in EXAMPLE_MARKERS
            ) and source_style != "CodeBlock" and not example_context:
                errors.append(f"{candidate_id}: example_only review has no example signal")
                disposition = "unresolved"
            elif disposition == "source_undefined" and "undefined_field" not in kinds:
                errors.append(
                    f"{candidate_id}: source_undefined review has no definition-gap signal"
                )
                disposition = "unresolved"
        else:
            disposition = "unresolved"
            reason = "no_exact_candidate_review"
            note = (
                f"{anchor} 没有精确正式锚点、专用源信号处置或逐候选审查。"
                "该候选保持待审，不能因靠近某个概念就获得终态。"
            )

        row = dict(candidate)
        row.update(
            {
                "candidate_review_version": CANDIDATE_REVIEW_VERSION,
                "disposition": disposition,
                "disposition_status": "pending" if disposition == "unresolved" else "final",
                "disposition_reason": reason,
                "semantic_review_note": note,
                "bound_concept_ids": bound_ids,
                "bound_card_paths": bound_cards,
                "parent_concept_ids": parent_ids,
                "parent_card_paths": parent_cards,
                "review_basis": {
                    "exact_anchor_inventory_ids": [
                        str(record.get("concept_id")) for record in anchored
                    ],
                    "candidate_kinds": kinds,
                    "parent_authority": parent_authority,
                    "exact_candidate_review": (
                        {
                            "candidate_id": review.get("candidate_id"),
                            "disposition": review.get("disposition"),
                            "semantic_fingerprint_sha256": review.get(
                                "semantic_fingerprint_sha256"
                            ),
                            "source_basis_sha256": sha256(
                                json.dumps(
                                    review.get("source_basis"),
                                    ensure_ascii=False,
                                    sort_keys=True,
                                    separators=(",", ":"),
                                ).encode("utf-8")
                            ).hexdigest(),
                        }
                        if candidate_id in used_review_ids and review
                        else None
                    ),
                    "definition_layer_separate": True,
                    "no_automatic_promotion": True,
                },
            }
        )
        reviewed.append(row)
        if unit_type == "table":
            table_outcomes[anchor] = {
                "disposition": disposition,
                "bound_concept_ids": list(bound_ids),
                "parent_concept_ids": list(parent_ids),
            }
    unused_reviews = sorted(set(reviews) - used_review_ids)
    if unused_reviews:
        errors.append(f"unused exact candidate reviews: {unused_reviews}")
    unresolved_count = sum(
        1 for candidate in reviewed if candidate.get("disposition") == "unresolved"
    )
    if unresolved_count:
        errors.append(f"unresolved source candidates: {unresolved_count}")
    return reviewed


def _render_files(root: Path, records: list[dict[str, object]], errors: list[str]) -> dict[str, bytes]:
    source_map: dict[str, list[str]] = {}
    relations: dict[str, dict[str, object]] = {}
    for record in records:
        concept_id = str(record["concept_id"])
        for anchor in record.get("source_anchors", []):
            source_map.setdefault(str(anchor), []).append(concept_id)
        relations[concept_id] = {
            "required_neighbors": sorted(set(record.get("required_neighbors", []))),
            "disposition": record.get("disposition"),
        }
    family_rows = sorted({(
        str(record.get("concept_family", record.get("family", "unassigned"))),
        str(record["concept_id"]),
        str(record.get("canonical_name_zh", record.get("name_zh", ""))),
    ) for record in records})
    family_lines = ["# Xi-Kari v8.3 concept families", "", "This index is generated from authored inventory and cards; cards remain the reading interface.", "", "| family | concept | name |", "| --- | --- | --- |"]
    family_lines.extend(f"| `{family}` | `{concept_id}` | {name} |" for family, concept_id, name in family_rows)
    bundle_lines = ["# Xi-Kari continuity map", "", "Each bundle is a required co-reading boundary, not a new source definition.", ""]
    for path in sorted((root / "references" / "ontology" / "bundles").glob("*.md")):
        anchors = sorted(set(ANCHOR.findall(path.read_text(encoding="utf-8"))))
        bundle_lines.append(f"- `{path.relative_to(root).as_posix()}`: {', '.join(f'`{a}`' for a in anchors) or 'no explicit anchor'}")
    disposition_counts: dict[str, int] = {}
    for record in records:
        disposition = str(record.get("disposition", "unknown"))
        disposition_counts[disposition] = disposition_counts.get(disposition, 0) + 1
    source_hashes = _source_hashes(root)
    candidate_census = _candidate_census(root, records, errors)
    candidate_bytes = _jsonl(candidate_census)
    candidate_counts: dict[str, int] = {}
    for candidate in candidate_census:
        disposition = str(candidate.get("disposition", "unresolved"))
        candidate_counts[disposition] = candidate_counts.get(disposition, 0) + 1
    registry = {
        "schema_id": "xi-kari.concept-registry",
        "schema_version": 1,
        "framework_version": "v8.3",
        "concept_count": len(records),
        "concept_count_semantics": "inventory record count; not a claim of complete ontology concept count",
        "candidate_count": len(candidate_census),
        "candidate_count_semantics": "reviewed source candidates under the current extraction rules; not an ontology cardinality claim",
        "unresolved_candidate_count": candidate_counts.get("unresolved", 0),
        "candidate_disposition_counts": candidate_counts,
        "candidate_census_sha256": sha256(candidate_bytes).hexdigest(),
        "disposition_counts": disposition_counts,
        "neighbor_policy": "semantic-only; shared-card or family fallback; max 16 per record",
        "concepts": [
            _registry_record(
                root,
                record,
                validation_status="failed" if errors else "passed",
                source_hashes=source_hashes,
            )
            for record in records
        ],
    }
    disposition_ledger = [
        {
            key: candidate.get(key)
            for key in (
                "candidate_id",
                "source_anchor",
                "disposition",
                "disposition_status",
                "disposition_reason",
                "semantic_review_note",
                "bound_concept_ids",
                "bound_card_paths",
                "parent_concept_ids",
                "parent_card_paths",
                "source_undefined_fields",
            )
        }
        for candidate in candidate_census
    ]
    return {
        "references/ontology/candidate-census.jsonl": candidate_bytes,
        "references/ontology/concept-disposition-ledger.jsonl": _jsonl(disposition_ledger),
        "references/ontology/concept-registry.json": _json(registry),
        "references/ontology/concept-relations.json": _json(relations),
        "references/ontology/source-to-concept-map.json": _json({key: sorted(set(value)) for key, value in sorted(source_map.items())}),
        "references/ontology/concept-family-map.md": ("\n".join(family_lines) + "\n").encode("utf-8"),
        "references/ontology/continuity-map.md": ("\n".join(bundle_lines) + "\n").encode("utf-8"),
    }


def run(root: Path, *, check: bool) -> list[str]:
    inventory, errors = _read_inventory(root)
    records = _merge_records(root, inventory, errors)
    generated = _render_files(root, records, errors)
    for relative, content in generated.items():
        path = root / relative
        if check:
            if not path.is_file():
                errors.append(f"missing generated index: {relative}")
            elif path.read_bytes() != content:
                errors.append(f"generated index differs: {relative}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    errors = run(args.root.resolve(), check=args.check or args.all or not args.write)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("knowledge index: PASS" if not args.write else "knowledge index: generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
