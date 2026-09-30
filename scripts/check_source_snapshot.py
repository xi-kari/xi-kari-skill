#!/usr/bin/env python3
"""Read-only checker for the Xi-Kari v8.3 source snapshot."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

from jsonschema import Draft202012Validator

from build_source_snapshot import CANDIDATE_KIND_ORDER, build
from xi_kari_runtime.source_profile import SOURCE_VERSION, get_source_profile


PARAGRAPH_MARKER = re.compile(r"<!-- source-paragraph:(V83-P\d{4}) style=[^>]* -->")
TABLE_MARKER = re.compile(r'<table data-source-table="(V83-T\d{3})">')
V90_PARAGRAPH_MARKER = re.compile(r"<!-- source-paragraph:(V90-P\d{5})\b")
V90_BODY_MARKER = re.compile(r"<!-- source-body:(V90-B\d{5})\b")
V90_TABLE_MARKER = re.compile(r'<table data-source-table="(V90-T\d{3})"')
FORBIDDEN_CLASSIFICATION_FIELDS = {
    "binding_dispositions",
    "bound_card_paths",
    "bound_concept_ids",
    "classification",
    "concept_id",
    "disposition",
    "disposition_reason",
    "disposition_status",
}


def _canonical(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _semantic_payload(row: dict[str, object]) -> dict[str, object]:
    payload = {
        "source_unit_type": row.get("source_unit_type"),
        "source_style": row.get("source_style"),
        "source_text": row.get("source_text"),
        "candidate_kinds": row.get("candidate_kinds"),
        "matched_signals": row.get("matched_signals"),
        "source_undefined_fields": row.get("source_undefined_fields"),
    }
    if row.get("source_unit_type") == "table_row":
        payload.update(
            {
                "source_table_anchor": row.get("source_table_anchor"),
                "source_table_row_index": row.get("source_table_row_index"),
            }
        )
    return payload


def _load_json(path: Path, label: str) -> tuple[object | None, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"cannot read {label}: {exc}"]


def check_manifest(root: Path) -> list[str]:
    base = root / "references" / "source" / "v8.3"
    manifest, errors = _load_json(base / "source-manifest.json", "source manifest")
    schema, load_errors = _load_json(
        root / "schemas" / "source-manifest.schema.json",
        "source manifest schema",
    )
    errors.extend(load_errors)
    if not isinstance(manifest, dict) or not isinstance(schema, dict):
        return errors
    validator = Draft202012Validator(schema)
    for schema_error in sorted(
        validator.iter_errors(manifest), key=lambda item: list(item.path)
    ):
        location = ".".join(str(part) for part in schema_error.path) or "<manifest>"
        errors.append(f"source manifest schema {location}: {schema_error.message}")
    return errors


def check_source_unit_contract(root: Path) -> list[str]:
    base = root / "references" / "source" / "v8.3"
    manifest, errors = _load_json(base / "source-manifest.json", "source manifest")
    table_values, load_errors = _load_json(
        base / "indexes" / "tables.json", "source table index"
    )
    errors.extend(load_errors)
    if not isinstance(manifest, dict) or not isinstance(table_values, list):
        return errors

    sequence = manifest.get("source_unit_sequence")
    if not isinstance(sequence, list):
        errors.append("source manifest has no source_unit_sequence")
    else:
        tables_before_paragraph: dict[int, list[str]] = {}
        for table in table_values:
            if not isinstance(table, dict):
                errors.append("source table index contains a non-object record")
                continue
            anchor = table.get("anchor")
            paragraph_ordinals = table.get("paragraph_ordinals")
            if (
                not isinstance(anchor, str)
                or not isinstance(paragraph_ordinals, list)
                or not paragraph_ordinals
                or not all(isinstance(value, int) for value in paragraph_ordinals)
            ):
                errors.append(f"cannot order source table unit: {anchor!r}")
                continue
            tables_before_paragraph.setdefault(paragraph_ordinals[0], []).append(anchor)
        expected_sequence: list[str] = []
        for ordinal in range(1, 4632):
            expected_sequence.extend(tables_before_paragraph.get(ordinal, []))
            expected_sequence.append(f"V83-P{ordinal:04d}")
        if sequence != expected_sequence:
            errors.append("source_unit_sequence differs from DOCX paragraph/table order")
        if manifest.get("source_unit_count") != len(sequence):
            errors.append("source_unit_count differs from source_unit_sequence")

    expected_paths = {
        "audit/paragraphs.jsonl",
        "indexes/tables.json",
        *(f"audit/tables/V83-T{ordinal:03d}.md" for ordinal in range(1, 123)),
    }
    file_hashes = manifest.get("source_unit_file_sha256")
    if not isinstance(file_hashes, dict):
        errors.append("source manifest has no source_unit_file_sha256")
        return errors
    missing = sorted(expected_paths - set(file_hashes))
    if missing:
        errors.append(f"source unit file hashes omit runtime files: {missing}")
    for relative, expected_hash in sorted(file_hashes.items()):
        if not isinstance(relative, str) or relative not in expected_paths:
            errors.append(f"unexpected source unit file hash path: {relative!r}")
            continue
        path = base / relative
        if path.is_symlink() or not path.is_file():
            errors.append(f"missing or unsafe source unit file: {relative}")
            continue
        observed_hash = sha256(path.read_bytes()).hexdigest()
        if observed_hash != expected_hash:
            errors.append(f"source unit file hash mismatch: {relative}")
    return errors


def check_candidate_index(root: Path) -> list[str]:
    base = root / "references" / "source" / "v8.3"
    path = base / "indexes" / "candidates.jsonl"
    if not path.is_file():
        return [f"missing source candidate index: {path}"]

    errors: list[str] = []
    manifest, load_errors = _load_json(base / "source-manifest.json", "source manifest")
    errors.extend(load_errors)
    schema, load_errors = _load_json(
        root / "schemas" / "source-candidate.schema.json",
        "source candidate schema",
    )
    errors.extend(load_errors)
    paragraph_rows: dict[str, dict[str, object]] = {}
    paragraph_path = base / "audit" / "paragraphs.jsonl"
    try:
        for line_number, line in enumerate(
            paragraph_path.read_text(encoding="utf-8").splitlines(), 1
        ):
            if not line.strip():
                continue
            value = json.loads(line)
            if isinstance(value, dict) and isinstance(value.get("anchor"), str):
                paragraph_rows[value["anchor"]] = value
            else:
                errors.append(
                    f"source paragraph line {line_number}: record is not an anchored object"
                )
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read source paragraphs for candidate index: {exc}")
    table_values, load_errors = _load_json(
        base / "indexes" / "tables.json",
        "source table index for candidate index",
    )
    errors.extend(load_errors)
    tables = {
        value["anchor"]: value
        for value in table_values
        if isinstance(value, dict) and isinstance(value.get("anchor"), str)
    } if isinstance(table_values, list) else {}
    if not isinstance(manifest, dict) or not isinstance(schema, dict):
        return errors
    validator = Draft202012Validator(schema)

    rows: list[dict[str, object]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [*errors, f"cannot read source candidate index: {exc}"]
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"candidate index line {line_number}: invalid JSON: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"candidate index line {line_number}: record is not an object")
            continue
        rows.append(value)
        for schema_error in sorted(
            validator.iter_errors(value), key=lambda item: list(item.path)
        ):
            location = ".".join(str(part) for part in schema_error.path) or "<record>"
            errors.append(
                f"candidate index line {line_number} schema {location}: "
                f"{schema_error.message}"
            )

    ids = [row.get("candidate_id") for row in rows]
    id_strings = [value for value in ids if isinstance(value, str)]
    if len(id_strings) != len(set(id_strings)):
        errors.append("source candidate index candidate_id values are not unique")
    if manifest.get("candidate_count") != len(rows):
        errors.append("source manifest candidate_count differs from candidate index")
    if manifest.get("candidate_index_sha256") != sha256(path.read_bytes()).hexdigest():
        errors.append("source manifest candidate_index_sha256 mismatch")

    expected_raw = manifest.get("raw_sha256")
    expected_semantic = manifest.get("semantic_sha256")
    expected_list_structure = manifest.get("list_structure_sha256")
    expected_ruleset = manifest.get("candidate_ruleset_version")
    observed_counts = {kind: 0 for kind in CANDIDATE_KIND_ORDER}
    source_order: list[tuple[int, int, str]] = []
    for index, row in enumerate(rows):
        candidate_id = row.get("candidate_id")
        label = candidate_id if isinstance(candidate_id, str) else f"row {index + 1}"
        if FORBIDDEN_CLASSIFICATION_FIELDS & set(row):
            errors.append(f"{label}: ontology classification fields are forbidden")
        if row.get("previous_candidate_id") != (ids[index - 1] if index else None):
            errors.append(f"{label}: previous_candidate_id mismatch")
        if row.get("next_candidate_id") != (
            ids[index + 1] if index + 1 < len(ids) else None
        ):
            errors.append(f"{label}: next_candidate_id mismatch")

        anchor = row.get("source_anchor")
        if isinstance(candidate_id, str) and isinstance(anchor, str):
            if candidate_id != f"V83-CANDIDATE-{anchor.removeprefix('V83-')}":
                errors.append(f"{label}: candidate ID/source anchor mismatch")
        if unit_type := row.get("source_unit_type"):
            if unit_type in {"paragraph", "table"} and row.get(
                "source_anchors"
            ) != [anchor]:
                errors.append(
                    f"{label}: source_anchors must retain the exact unit anchor"
                )
        if row.get("candidate_ruleset_version") != expected_ruleset:
            errors.append(f"{label}: candidate ruleset version mismatch")

        kinds = row.get("candidate_kinds")
        signals = row.get("matched_signals")
        if not isinstance(kinds, list) or not isinstance(signals, dict):
            errors.append(f"{label}: malformed candidate kinds/signals")
            continue
        expected_kinds = [kind for kind in CANDIDATE_KIND_ORDER if kind in signals]
        if kinds != expected_kinds:
            errors.append(f"{label}: candidate kinds are not in declared signal order")
        for kind in kinds:
            if kind in observed_counts:
                observed_counts[kind] += 1
            else:
                errors.append(f"{label}: unknown candidate kind {kind!r}")

        text = row.get("source_text")
        if isinstance(text, str):
            if row.get("text_sha256") != sha256(text.encode("utf-8")).hexdigest():
                errors.append(f"{label}: text_sha256 mismatch")
            fingerprint = sha256(_canonical(_semantic_payload(row))).hexdigest()
            if row.get("semantic_fingerprint_sha256") != fingerprint:
                errors.append(f"{label}: semantic fingerprint mismatch")
        if row.get("source_raw_sha256") != expected_raw:
            errors.append(f"{label}: source raw hash mismatch")
        if row.get("source_semantic_sha256") != expected_semantic:
            errors.append(f"{label}: source semantic hash mismatch")
        if row.get("source_list_structure_sha256") != expected_list_structure:
            errors.append(f"{label}: source list structure hash mismatch")
        undefined_fields = row.get("source_undefined_fields")
        if not isinstance(undefined_fields, list):
            errors.append(f"{label}: source_undefined_fields is not a list")
        elif "undefined_field" in kinds and not undefined_fields:
            errors.append(f"{label}: undefined_field signal has no exact source signals")

        expected_span: dict[str, object] | None = None
        expected_text: str | None = None
        expected_style: str | None = None
        expected_ordinal: int | None = None
        expected_numbering: object = None
        unit_type = row.get("source_unit_type")
        if unit_type == "paragraph" and isinstance(anchor, str):
            paragraph = paragraph_rows.get(anchor)
            if paragraph is None:
                errors.append(f"{label}: unknown source paragraph anchor")
            else:
                expected_span = {
                    "start_anchor": anchor,
                    "end_anchor": anchor,
                    "paragraph_anchors": [anchor],
                }
                expected_text = paragraph.get("text") if isinstance(paragraph.get("text"), str) else None
                expected_style = paragraph.get("style") if isinstance(paragraph.get("style"), str) else None
                expected_ordinal = paragraph.get("ordinal") if isinstance(paragraph.get("ordinal"), int) else None
                expected_numbering = paragraph.get("numbering")
        elif unit_type == "table" and isinstance(anchor, str):
            table = tables.get(anchor)
            if table is None:
                errors.append(f"{label}: unknown source table anchor")
            else:
                ordinals = table.get("paragraph_ordinals")
                table_rows = table.get("rows")
                if isinstance(ordinals, list) and ordinals and all(
                    isinstance(value, int) for value in ordinals
                ):
                    paragraph_anchors = [f"V83-P{value:04d}" for value in ordinals]
                    expected_span = {
                        "start_anchor": paragraph_anchors[0],
                        "end_anchor": paragraph_anchors[-1],
                        "paragraph_anchors": paragraph_anchors,
                    }
                if isinstance(table_rows, list):
                    expected_text = json.dumps(
                        table_rows,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                expected_style = ""
                expected_ordinal = table.get("ordinal") if isinstance(table.get("ordinal"), int) else None
        elif unit_type == "table_row" and isinstance(anchor, str):
            table_anchor = row.get("source_table_anchor")
            row_index = row.get("source_table_row_index")
            table = tables.get(table_anchor) if isinstance(table_anchor, str) else None
            if table is None:
                errors.append(f"{label}: unknown source table for row candidate")
            elif not isinstance(row_index, int) or row_index < 1:
                errors.append(f"{label}: invalid source table row index")
            elif anchor != f"{table_anchor}-R{row_index:03d}":
                errors.append(f"{label}: row anchor/table coordinates mismatch")
            else:
                table_rows = table.get("rows")
                bindings = table.get("cell_paragraph_ordinals")
                if (
                    not isinstance(table_rows, list)
                    or not isinstance(bindings, list)
                    or row_index > len(table_rows)
                    or row_index > len(bindings)
                ):
                    errors.append(f"{label}: source table row is out of range")
                else:
                    row_bindings = bindings[row_index - 1]
                    if isinstance(row_bindings, list):
                        ordinals = [
                            ordinal
                            for cell in row_bindings
                            if isinstance(cell, list)
                            for ordinal in cell
                            if isinstance(ordinal, int)
                        ]
                    else:
                        ordinals = []
                    if ordinals:
                        paragraph_anchors = [
                            f"V83-P{value:04d}" for value in ordinals
                        ]
                        expected_span = {
                            "start_anchor": paragraph_anchors[0],
                            "end_anchor": paragraph_anchors[-1],
                            "paragraph_anchors": paragraph_anchors,
                        }
                        if row.get("source_anchors") != paragraph_anchors:
                            errors.append(
                                f"{label}: row source_anchors differ from exact row paragraphs"
                            )
                    expected_text = json.dumps(
                        table_rows[row_index - 1],
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    expected_style = "TableHead" if row_index == 1 else "TableRow"
                    expected_ordinal = row_index
        if expected_span is None:
            errors.append(f"{label}: cannot establish complete source span")
        else:
            if row.get("source_span") != expected_span:
                errors.append(f"{label}: source span does not cover the exact source unit")
            start_anchor = expected_span["start_anchor"]
            start_ordinal = int(str(start_anchor).removeprefix("V83-P"))
            source_order.append(
                (
                    start_ordinal,
                    {"table": 0, "table_row": 1, "paragraph": 2}.get(
                        str(unit_type), 3
                    ),
                    str(candidate_id),
                )
            )
        if expected_text is not None and text != expected_text:
            errors.append(f"{label}: source_text differs from the exact source unit")
        if expected_style is not None and row.get("source_style") != expected_style:
            errors.append(f"{label}: source_style differs from the exact source unit")
        if expected_ordinal is not None and row.get("ordinal") != expected_ordinal:
            errors.append(f"{label}: ordinal differs from the exact source unit")
        if row.get("source_numbering") != expected_numbering:
            errors.append(f"{label}: source numbering differs from the exact source unit")

    if source_order != sorted(source_order):
        errors.append("source candidate index is not in deterministic source order")
    if manifest.get("candidate_kind_counts") != observed_counts:
        errors.append("source manifest candidate_kind_counts differs from candidate index")
    required_positive_kinds = set(CANDIDATE_KIND_ORDER) - {"undefined_field"}
    if set(observed_counts) != set(CANDIDATE_KIND_ORDER) or any(
        observed_counts[kind] == 0 for kind in required_positive_kinds
    ):
        errors.append("candidate index does not cover every declared source-signal kind")
    return errors


def check_coverage(root: Path) -> list[str]:
    reader = root / "references" / "source" / "v8.3" / "reader"
    contents = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(reader.glob("*.md"))
        if path.name != "00-index.md"
    )
    paragraph_counts = Counter(PARAGRAPH_MARKER.findall(contents))
    table_counts = Counter(TABLE_MARKER.findall(contents))
    errors: list[str] = []
    expected_paragraphs = {f"V83-P{i:04d}" for i in range(1, 4632)}
    expected_tables = {f"V83-T{i:03d}" for i in range(1, 123)}
    if set(paragraph_counts) != expected_paragraphs:
        errors.append(
            "reader paragraph coverage mismatch: "
            f"missing={len(expected_paragraphs - set(paragraph_counts))}, "
            f"extra={len(set(paragraph_counts) - expected_paragraphs)}"
        )
    duplicate_paragraphs = sorted(anchor for anchor, count in paragraph_counts.items() if count != 1)
    if duplicate_paragraphs:
        errors.append(f"reader paragraph anchors are not unique: {duplicate_paragraphs[:5]}")
    if set(table_counts) != expected_tables:
        errors.append(
            "reader table coverage mismatch: "
            f"missing={len(expected_tables - set(table_counts))}, "
            f"extra={len(set(table_counts) - expected_tables)}"
        )
    duplicate_tables = sorted(anchor for anchor, count in table_counts.items() if count != 1)
    if duplicate_tables:
        errors.append(f"reader table anchors are not unique: {duplicate_tables[:5]}")
    return errors


def check_inventory_candidate_coverage(root: Path) -> list[str]:
    base = root / "references" / "source" / "v8.3"
    inventory_anchors: set[str] = set()
    errors: list[str] = []
    for path in sorted((root / "references" / "ontology" / "inventory").glob("*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            errors.append(f"cannot read ontology inventory for candidate coverage: {exc}")
            continue
        for line_number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                anchors = record["source_anchors"]
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                errors.append(f"{path}:{line_number}: invalid inventory anchors: {exc}")
                continue
            if not isinstance(anchors, list):
                errors.append(f"{path}:{line_number}: source_anchors must be a list")
                continue
            inventory_anchors.update(
                anchor for anchor in anchors if isinstance(anchor, str)
            )

    covered_anchors: set[str] = set()
    candidate_path = base / "indexes" / "candidates.jsonl"
    try:
        lines = candidate_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [*errors, f"cannot read candidates for inventory coverage: {exc}"]
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"candidate coverage line {line_number}: invalid JSON: {exc}")
            continue
        source_anchors = candidate.get("source_anchors")
        if isinstance(source_anchors, list):
            covered_anchors.update(
                value for value in source_anchors if isinstance(value, str)
            )
    missing = sorted(inventory_anchors - covered_anchors)
    if missing:
        errors.append(f"candidate corpus omits authored inventory anchors: {missing}")
    return errors


def _load_jsonl(path: Path, label: str) -> tuple[list[dict[str, object]], list[str]]:
    rows: list[dict[str, object]] = []
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [f"cannot read {label}: {exc}"]
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{label} line {line_number}: invalid JSON: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"{label} line {line_number}: record is not an object")
            continue
        rows.append(value)
    return rows, errors


def check_v90_manifest(root: Path) -> list[str]:
    profile = get_source_profile("v9.0")
    base = profile.source_directory(root)
    manifest, errors = _load_json(base / "source-manifest.json", "v9.0 manifest")
    schema, schema_errors = _load_json(
        root / profile.manifest_schema_path, "v9.0 manifest schema"
    )
    errors.extend(schema_errors)
    if not isinstance(manifest, dict) or not isinstance(schema, dict):
        return errors
    validator = Draft202012Validator(schema)
    for schema_error in sorted(
        validator.iter_errors(manifest), key=lambda item: list(item.path)
    ):
        location = ".".join(str(part) for part in schema_error.path) or "<manifest>"
        errors.append(f"v9.0 manifest schema {location}: {schema_error.message}")
    return errors


def check_v90_source_units(root: Path) -> list[str]:
    profile = get_source_profile("v9.0")
    base = profile.source_directory(root)
    manifest, errors = _load_json(base / "source-manifest.json", "v9.0 manifest")
    body_rows, row_errors = _load_jsonl(
        base / "audit" / "body-blocks.jsonl", "v9.0 body blocks"
    )
    errors.extend(row_errors)
    paragraph_rows, row_errors = _load_jsonl(
        base / "audit" / "paragraphs.jsonl", "v9.0 paragraphs"
    )
    errors.extend(row_errors)
    table_values, load_errors = _load_json(
        base / "indexes" / "tables.json", "v9.0 table index"
    )
    errors.extend(load_errors)
    aliases, load_errors = _load_json(
        base / "indexes" / "aliases.json", "v9.0 alias index"
    )
    errors.extend(load_errors)
    if not all(
        (
            isinstance(manifest, dict),
            isinstance(table_values, list),
            isinstance(aliases, dict),
        )
    ):
        return errors

    paragraph_by_anchor = {
        row["anchor"]: row
        for row in paragraph_rows
        if isinstance(row.get("anchor"), str)
    }
    table_by_anchor = {
        row["anchor"]: row
        for row in table_values
        if isinstance(row, dict) and isinstance(row.get("anchor"), str)
    }
    expected_paragraphs = {
        f"V90-P{ordinal:05d}" for ordinal in range(1, profile.expected_paragraphs + 1)
    }
    expected_tables = {
        f"V90-T{ordinal:03d}" for ordinal in range(1, profile.expected_tables + 1)
    }
    expected_bodies = {
        f"V90-B{ordinal:05d}"
        for ordinal in range(1, (profile.expected_body_blocks or 0) + 1)
    }
    if set(paragraph_by_anchor) != expected_paragraphs:
        errors.append("v9.0 paragraph anchor set is incomplete or mixed")
    if set(table_by_anchor) != expected_tables:
        errors.append("v9.0 table anchor set is incomplete or mixed")
    body_anchors = [row.get("anchor") for row in body_rows]
    if set(body_anchors) != expected_bodies or len(body_anchors) != len(expected_bodies):
        errors.append("v9.0 body block anchor set is incomplete, duplicated, or mixed")

    reconstructed_sequence: list[str] = []
    for expected_ordinal, row in enumerate(body_rows, 1):
        if row.get("ordinal") != expected_ordinal:
            errors.append(f"v9.0 body block ordinal mismatch at {expected_ordinal}")
        paragraph_anchor = row.get("paragraph_anchor")
        table_anchor = row.get("table_anchor")
        if isinstance(paragraph_anchor, str) and table_anchor is None:
            reconstructed_sequence.append(paragraph_anchor)
        elif isinstance(table_anchor, str) and paragraph_anchor is None:
            table = table_by_anchor.get(table_anchor)
            if table is None:
                errors.append(f"v9.0 body block references unknown table: {table_anchor}")
                continue
            reconstructed_sequence.append(table_anchor)
            paragraph_anchors = table.get("paragraph_anchors")
            if not isinstance(paragraph_anchors, list):
                errors.append(f"v9.0 table lacks paragraph anchors: {table_anchor}")
            else:
                reconstructed_sequence.extend(paragraph_anchors)
        else:
            errors.append(f"v9.0 body block has ambiguous payload: {row.get('anchor')}")
    manifest_sequence = manifest.get("source_unit_sequence")
    if manifest_sequence != reconstructed_sequence:
        errors.append("v9.0 source unit sequence differs from body/table document order")
    if isinstance(manifest_sequence, list) and len(manifest_sequence) != len(
        set(manifest_sequence)
    ):
        errors.append("v9.0 source unit sequence contains duplicates")
    if len(reconstructed_sequence) != len(set(reconstructed_sequence)):
        errors.append("v9.0 source unit sequence contains duplicates")

    body_aliases = aliases.get("body_blocks")
    paragraph_aliases = aliases.get("paragraphs")
    table_aliases = aliases.get("tables")
    expected_body_aliases = {
        f"XK9-B{ordinal:05d}": f"V90-B{ordinal:05d}"
        for ordinal in range(1, (profile.expected_body_blocks or 0) + 1)
    }
    expected_paragraph_aliases = {
        f"XK9-P{ordinal:05d}": f"V90-P{ordinal:05d}"
        for ordinal in range(1, profile.expected_paragraphs + 1)
    }
    expected_table_aliases = {
        f"XK9-T{ordinal:03d}": f"V90-T{ordinal:03d}"
        for ordinal in range(1, profile.expected_tables + 1)
    }
    if body_aliases != expected_body_aliases:
        errors.append("v9.0 body alias map is incomplete or not identity-preserving")
    if paragraph_aliases != expected_paragraph_aliases:
        errors.append("v9.0 paragraph alias map is incomplete or not identity-preserving")
    if table_aliases != expected_table_aliases:
        errors.append("v9.0 table alias map is incomplete or not identity-preserving")

    file_hashes = manifest.get("source_unit_file_sha256")
    if not isinstance(file_hashes, dict):
        errors.append("v9.0 manifest has no source unit file hashes")
    else:
        for relative, expected_hash in sorted(file_hashes.items()):
            if not isinstance(relative, str) or not isinstance(expected_hash, str):
                errors.append(f"invalid v9.0 source unit file hash: {relative!r}")
                continue
            path = base / relative
            if path.is_symlink() or not path.is_file():
                errors.append(f"missing or unsafe v9.0 source unit file: {relative}")
                continue
            if sha256(path.read_bytes()).hexdigest() != expected_hash:
                errors.append(f"v9.0 source unit file hash mismatch: {relative}")
    index_hashes = manifest.get("index_file_sha256")
    if not isinstance(index_hashes, dict):
        errors.append("v9.0 manifest has no index file hashes")
    else:
        expected_index_paths = {
            path.relative_to(base).as_posix()
            for path in (base / "indexes").glob("*")
            if path.is_file() and not path.is_symlink()
        }
        if set(index_hashes) != expected_index_paths:
            errors.append("v9.0 index file hash set is incomplete or has extras")
        for relative, expected_hash in sorted(index_hashes.items()):
            path = base / relative
            if path.is_symlink() or not path.is_file():
                errors.append(f"missing or unsafe v9.0 index file: {relative}")
                continue
            if sha256(path.read_bytes()).hexdigest() != expected_hash:
                errors.append(f"v9.0 index file hash mismatch: {relative}")

    divisions = manifest.get("divisions")
    if isinstance(divisions, list):
        division_paragraphs = [
            anchor
            for division in divisions
            if isinstance(division, dict)
            for anchor in division.get("paragraph_anchors", [])
            if isinstance(anchor, str)
        ]
        division_tables = [
            anchor
            for division in divisions
            if isinstance(division, dict)
            for anchor in division.get("table_anchors", [])
            if isinstance(anchor, str)
        ]
        if len(division_paragraphs) != len(set(division_paragraphs)) or set(
            division_paragraphs
        ) != expected_paragraphs:
            errors.append("v9.0 reader divisions do not cover paragraphs exactly once")
        if len(division_tables) != len(set(division_tables)) or set(
            division_tables
        ) != expected_tables:
            errors.append("v9.0 reader divisions do not cover tables exactly once")

    reader = base / "reader"
    try:
        contents = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(reader.glob("*.md"))
            if path.name != "00-index.md"
        )
    except OSError as exc:
        errors.append(f"cannot read v9.0 reader units: {exc}")
        return errors
    paragraph_counts = Counter(V90_PARAGRAPH_MARKER.findall(contents))
    body_counts = Counter(V90_BODY_MARKER.findall(contents))
    table_counts = Counter(V90_TABLE_MARKER.findall(contents))
    if set(paragraph_counts) != expected_paragraphs or any(
        count != 1 for count in paragraph_counts.values()
    ):
        errors.append("v9.0 reader paragraph coverage is incomplete or duplicated")
    if set(body_counts) != expected_bodies or any(
        count != 1 for count in body_counts.values()
    ):
        errors.append("v9.0 reader body coverage is incomplete or duplicated")
    if set(table_counts) != expected_tables or any(
        count != 1 for count in table_counts.values()
    ):
        errors.append("v9.0 reader table coverage is incomplete or duplicated")
    return errors


def check_v90_candidate_index(root: Path) -> list[str]:
    profile = get_source_profile("v9.0")
    base = profile.source_directory(root)
    manifest, errors = _load_json(base / "source-manifest.json", "v9.0 manifest")
    schema, load_errors = _load_json(
        root / profile.candidate_schema_path, "v9.0 candidate schema"
    )
    errors.extend(load_errors)
    paragraph_rows, load_errors = _load_jsonl(
        base / "audit" / "paragraphs.jsonl", "v9.0 paragraphs"
    )
    errors.extend(load_errors)
    table_values, load_errors = _load_json(
        base / "indexes" / "tables.json", "v9.0 table index"
    )
    errors.extend(load_errors)
    rows, load_errors = _load_jsonl(
        base / "indexes" / "candidates.jsonl", "v9.0 candidates"
    )
    errors.extend(load_errors)
    if not isinstance(manifest, dict) or not isinstance(schema, dict) or not isinstance(
        table_values, list
    ):
        return errors
    validator = Draft202012Validator(schema)
    paragraph_by_anchor = {
        row["anchor"]: row
        for row in paragraph_rows
        if isinstance(row.get("anchor"), str)
    }
    table_by_anchor = {
        row["anchor"]: row
        for row in table_values
        if isinstance(row, dict) and isinstance(row.get("anchor"), str)
    }
    ids: list[str] = []
    observed_counts = Counter({kind: 0 for kind in (
        "heading",
        "domain_entry",
        "definition",
        "table",
        "variable",
        "operator",
        "constraint",
        "undefined_field",
    )})
    domain_ids: list[str] = []
    source_positions: list[tuple[int, int, str]] = []
    for line_number, row in enumerate(rows, 1):
        label = f"v9.0 candidate line {line_number}"
        for schema_error in sorted(
            validator.iter_errors(row), key=lambda item: list(item.path)
        ):
            location = ".".join(str(part) for part in schema_error.path) or "<record>"
            errors.append(f"{label} schema {location}: {schema_error.message}")
        candidate_id = row.get("candidate_id")
        if isinstance(candidate_id, str):
            ids.append(candidate_id)
        if row.get("ordinal") != line_number:
            errors.append(f"{label}: ordinal is not the global deterministic order")
        expected_previous = rows[line_number - 2].get("candidate_id") if line_number > 1 else None
        expected_next = rows[line_number].get("candidate_id") if line_number < len(rows) else None
        if row.get("previous_candidate_id") != expected_previous:
            errors.append(f"{label}: previous_candidate_id is not adjacent")
        if row.get("next_candidate_id") != expected_next:
            errors.append(f"{label}: next_candidate_id is not adjacent")
        kinds = row.get("candidate_kinds")
        if isinstance(kinds, list):
            for kind in kinds:
                if isinstance(kind, str):
                    observed_counts[kind] += 1
        if "domain_entry" in (kinds or []):
            domain_id = row.get("domain_id")
            if isinstance(domain_id, str):
                domain_ids.append(domain_id)
        unit_type = row.get("source_unit_type")
        source_anchors = row.get("source_anchors")
        if not isinstance(source_anchors, list) or not source_anchors:
            continue
        if unit_type == "paragraph":
            anchor = row.get("source_anchor")
            paragraph = paragraph_by_anchor.get(anchor)
            if paragraph is None:
                errors.append(f"{label}: paragraph source anchor does not resolve")
                continue
            if source_anchors != [anchor]:
                errors.append(f"{label}: paragraph candidate span is not exact")
            if row.get("source_text") != paragraph.get("text"):
                errors.append(f"{label}: source_text differs from exact paragraph")
            if row.get("source_style") != paragraph.get("style_id"):
                errors.append(f"{label}: source_style differs from exact paragraph")
            if row.get("source_numbering") != paragraph.get("numbering"):
                errors.append(f"{label}: source numbering differs from exact paragraph")
            if row.get("body_anchor") != paragraph.get("body_anchor"):
                errors.append(f"{label}: body ownership differs from exact paragraph")
            source_positions.append((int(paragraph.get("ordinal", 0)), 2, str(candidate_id)))
        elif unit_type == "table":
            anchor = row.get("source_anchor")
            table = table_by_anchor.get(anchor)
            if table is None:
                errors.append(f"{label}: table source anchor does not resolve")
                continue
            table_rows = table.get("rows")
            if not isinstance(table_rows, list):
                errors.append(f"{label}: table rows are invalid")
                continue
            expected_anchors = table.get("paragraph_anchors")
            expected_text = json.dumps(
                [
                    [
                        "\n".join(
                            str(paragraph_by_anchor[paragraph_anchor].get("text", ""))
                            for paragraph_anchor in cell.get("paragraph_anchors", [])
                        )
                        for cell in source_row.get("cells", [])
                        if isinstance(cell, dict)
                    ]
                    for source_row in table_rows
                    if isinstance(source_row, dict)
                ],
                ensure_ascii=False,
                separators=(",", ":"),
            )
            if source_anchors != expected_anchors:
                errors.append(f"{label}: table paragraph binding differs")
            if row.get("source_text") != expected_text:
                errors.append(f"{label}: table text differs from exact cells")
            if row.get("body_anchor") != table.get("body_anchor"):
                errors.append(f"{label}: table body ownership differs")
            if row.get("source_numbering") is not None:
                errors.append(f"{label}: table candidate unexpectedly has numbering")
            if isinstance(expected_anchors, list) and expected_anchors:
                first = paragraph_by_anchor.get(expected_anchors[0], {}).get("ordinal", 0)
                source_positions.append((int(first), 0, str(candidate_id)))
        elif unit_type == "table_row":
            table_anchor = row.get("source_table_anchor")
            table = table_by_anchor.get(table_anchor)
            row_index = row.get("source_table_row_index")
            if table is None or not isinstance(row_index, int):
                errors.append(f"{label}: table row source does not resolve")
                continue
            table_rows = table.get("rows")
            if not isinstance(table_rows, list) or not (1 <= row_index <= len(table_rows)):
                errors.append(f"{label}: table row index is outside source")
                continue
            source_row = table_rows[row_index - 1]
            if not isinstance(source_row, dict):
                errors.append(f"{label}: table row source is invalid")
                continue
            cells = source_row.get("cells")
            if not isinstance(cells, list):
                errors.append(f"{label}: table row cells are invalid")
                continue
            expected_anchors = [
                anchor
                for cell in cells
                if isinstance(cell, dict)
                for anchor in cell.get("paragraph_anchors", [])
                if isinstance(anchor, str)
            ]
            expected_text = json.dumps(
                [
                    "\n".join(
                        str(paragraph_by_anchor[anchor].get("text", ""))
                        for anchor in cell.get("paragraph_anchors", [])
                    )
                    for cell in cells
                    if isinstance(cell, dict)
                ],
                ensure_ascii=False,
                separators=(",", ":"),
            )
            if source_anchors != expected_anchors:
                errors.append(f"{label}: table row paragraph binding differs")
            if row.get("source_text") != expected_text:
                errors.append(f"{label}: table row text differs from exact cells")
            if row.get("body_anchor") != table.get("body_anchor"):
                errors.append(f"{label}: table row body ownership differs")
            first = paragraph_by_anchor.get(expected_anchors[0], {}).get("ordinal", 0)
            source_positions.append((int(first), 1, str(candidate_id)))

        payload: dict[str, object] = {
            "source_unit_type": row.get("source_unit_type"),
            "source_style": row.get("source_style"),
            "source_text": row.get("source_text"),
            "candidate_kinds": row.get("candidate_kinds"),
            "matched_signals": row.get("matched_signals"),
            "source_undefined_fields": row.get("source_undefined_fields"),
            "domain_id": row.get("domain_id"),
        }
        if unit_type == "table_row":
            payload.update(
                {
                    "source_table_anchor": row.get("source_table_anchor"),
                    "source_table_row_index": row.get("source_table_row_index"),
                }
            )
        if row.get("semantic_fingerprint_sha256") != sha256(_canonical(payload)).hexdigest():
            errors.append(f"{label}: semantic fingerprint differs from source payload")
        forbidden = FORBIDDEN_CLASSIFICATION_FIELDS.intersection(row)
        if forbidden:
            errors.append(f"{label}: source census contains classifications: {sorted(forbidden)}")

    if len(ids) != len(set(ids)):
        errors.append("v9.0 candidate IDs are not unique")
    if source_positions != sorted(source_positions):
        errors.append("v9.0 candidate index is not in deterministic source order")
    if manifest.get("candidate_count") != len(rows):
        errors.append("v9.0 manifest candidate count differs from candidate index")
    if manifest.get("candidate_kind_counts") != dict(observed_counts):
        errors.append("v9.0 manifest candidate kind counts differ from candidate index")
    expected_domains = [f"D.{ordinal:02d}" for ordinal in range(1, 33)]
    if domain_ids != expected_domains:
        errors.append("v9.0 domain-entry candidates are missing, duplicated, or out of order")
    toc_anchors = {
        row["anchor"]
        for row in paragraph_rows
        if row.get("style_id") == "TOCItem" and isinstance(row.get("anchor"), str)
    }
    if any(toc_anchors.intersection(row.get("source_anchors", [])) for row in rows):
        errors.append("v9.0 TOCItem paragraph entered the semantic candidate census")
    try:
        candidate_bytes = (base / "indexes" / "candidates.jsonl").read_bytes()
    except OSError as exc:
        errors.append(f"cannot hash v9.0 candidate index: {exc}")
    else:
        if manifest.get("candidate_index_sha256") != sha256(candidate_bytes).hexdigest():
            errors.append("v9.0 candidate index hash differs from manifest")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--source-version", default=SOURCE_VERSION)
    args = parser.parse_args()
    root = args.root.resolve()
    errors = build(root, check=True, source_version=args.source_version)
    if args.source_version == "v9.0":
        errors.extend(check_v90_manifest(root))
        errors.extend(check_v90_source_units(root))
        errors.extend(check_v90_candidate_index(root))
    elif args.source_version == "v8.3":
        errors.extend(check_manifest(root))
        errors.extend(check_source_unit_contract(root))
        errors.extend(check_coverage(root))
        errors.extend(check_candidate_index(root))
        errors.extend(check_inventory_candidate_coverage(root))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("source snapshot: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
