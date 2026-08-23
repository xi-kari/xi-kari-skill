#!/usr/bin/env python3
"""Read-only checker for the Xi-Kari v8.2 source snapshot."""

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


PARAGRAPH_MARKER = re.compile(r"<!-- source-paragraph:(V82-P\d{4}) style=[^>]* -->")
TABLE_MARKER = re.compile(r'<table data-source-table="(V82-T\d{3})">')
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
    base = root / "references" / "source" / "v8.2"
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
    base = root / "references" / "source" / "v8.2"
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
            expected_sequence.append(f"V82-P{ordinal:04d}")
        if sequence != expected_sequence:
            errors.append("source_unit_sequence differs from DOCX paragraph/table order")
        if manifest.get("source_unit_count") != len(sequence):
            errors.append("source_unit_count differs from source_unit_sequence")

    expected_paths = {
        "audit/paragraphs.jsonl",
        "indexes/tables.json",
        *(f"audit/tables/V82-T{ordinal:03d}.md" for ordinal in range(1, 123)),
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
    base = root / "references" / "source" / "v8.2"
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
            if candidate_id != f"V82-CANDIDATE-{anchor.removeprefix('V82-')}":
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
                    paragraph_anchors = [f"V82-P{value:04d}" for value in ordinals]
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
                            f"V82-P{value:04d}" for value in ordinals
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
            start_ordinal = int(str(start_anchor).removeprefix("V82-P"))
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
    reader = root / "references" / "source" / "v8.2" / "reader"
    contents = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(reader.glob("*.md"))
        if path.name != "00-index.md"
    )
    paragraph_counts = Counter(PARAGRAPH_MARKER.findall(contents))
    table_counts = Counter(TABLE_MARKER.findall(contents))
    errors: list[str] = []
    expected_paragraphs = {f"V82-P{i:04d}" for i in range(1, 4632)}
    expected_tables = {f"V82-T{i:03d}" for i in range(1, 123)}
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
    base = root / "references" / "source" / "v8.2"
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    errors = build(root, check=True)
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
