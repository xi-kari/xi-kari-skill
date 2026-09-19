#!/usr/bin/env python3
"""Read-only verification of an explicitly approved, unit-exact source change."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from build_source_snapshot import extract_snapshot


def source_units(path: Path) -> dict[str, list[dict[str, object]]]:
    return _source_units(path.read_bytes())


def _source_units(source: bytes) -> dict[str, list[dict[str, object]]]:
    snapshot = extract_snapshot(source)
    return {
        "paragraphs": [{"ordinal": p.ordinal, "text": p.text, "style": p.style,
                        "numbering": None if p.numbering is None else asdict(p.numbering)}
                       for p in snapshot.paragraphs],
        "tables": [{"ordinal": t.ordinal, "cell_paragraph_ordinals": t.cell_paragraph_ordinals}
                   for t in snapshot.tables],
    }


def compare_units(before: dict, after: dict, approved: dict[int, dict]) -> list[str]:
    errors: list[str] = []
    old = before["paragraphs"]
    new = after["paragraphs"]
    if len(old) != len(new):
        errors.append("paragraph count changed; paragraphs may not be deleted or merged")
    if before["tables"] != after["tables"]:
        errors.append("table cells, paragraph bindings or table order changed")
    seen: set[int] = set()
    for left, right in zip(old, new):
        ordinal = left["ordinal"]
        for field in ("ordinal", "style", "numbering"):
            if left[field] != right[field]:
                errors.append(f"paragraph {ordinal}: {field} changed")
        if ordinal in approved:
            seen.add(ordinal)
            delta = approved[ordinal]
            if delta.get("before") != left["text"] or delta.get("after") != right["text"]:
                errors.append(f"paragraph {ordinal}: approved replacement does not match")
            if not delta.get("category"):
                errors.append(f"paragraph {ordinal}: approval category missing")
        elif left["text"] != right["text"]:
            errors.append(f"paragraph {ordinal}: unapproved content change")
    for ordinal in set(approved) - seen:
        errors.append(f"paragraph {ordinal}: approved change has no source paragraph")
    return errors


def _document_structure(document: bytes, approved_ordinals: set[int]) -> bytes:
    root = ET.fromstring(document)
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs = [p for p in root.iter(namespace + "p")
                  if "".join(node.text or "" for node in p.iter(namespace + "t")).strip()]
    for ordinal, paragraph in enumerate(paragraphs, 1):
        if ordinal in approved_ordinals:
            for node in paragraph.iter(namespace + "t"):
                node.text = None
    return ET.tostring(root)


def compare_packages(baseline: bytes, current: bytes, approval: dict) -> list[str]:
    errors: list[str] = []
    for field, payload in (("baseline_raw_sha256", baseline), ("current_raw_sha256", current)):
        if approval.get(field) != sha256(payload).hexdigest():
            errors.append(f"{field}: approved hash does not match the source package")
    metadata = approval.get("version_metadata_members", [])
    if (not isinstance(metadata, list)
            or any(not isinstance(name, str) for name in metadata)
            or len(set(metadata)) != len(metadata)):
        errors.append("invalid version_metadata_members allowlist")
        return errors
    allowed_metadata = set(metadata)
    for name in allowed_metadata:
        if name != "docProps/core.xml" and not re.fullmatch(r"word/header\d+\.xml", name):
            errors.append(f"{name}: member is not version metadata")
    with ZipFile(BytesIO(baseline)) as before, ZipFile(BytesIO(current)) as after:
        old_names, new_names = before.namelist(), after.namelist()
        if len(set(old_names)) != len(old_names) or len(set(new_names)) != len(new_names):
            errors.append("duplicate DOCX ZIP member")
            return errors
        old_set, new_set = set(old_names), set(new_names)
        if old_set != new_set:
            errors.append("DOCX ZIP member set changed")
        for name in sorted(allowed_metadata - (old_set & new_set)):
            errors.append(f"{name}: approved metadata member is missing")
        ordinals = {int(row["ordinal"]) for row in approval["changes"]}
        for name in sorted(old_set & new_set):
            left, right = before.read(name), after.read(name)
            if name == "word/document.xml":
                if _document_structure(left, ordinals) != _document_structure(right, ordinals):
                    errors.append("word/document.xml: unapproved text or XML structure change")
                continue
            expected = left.replace(b"v8.2", b"v8.3") if name in allowed_metadata else left
            if right != expected:
                errors.append(f"{name}: unapproved DOCX member change")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--approved-changes", type=Path, required=True)
    args = parser.parse_args()
    changes = json.loads(args.approved_changes.read_text(encoding="utf-8"))
    rows = changes["changes"]
    approved = {int(row["ordinal"]): row for row in rows}
    if len(approved) != len(rows):
        raise SystemExit("duplicate approved paragraph")
    baseline, current = args.baseline.read_bytes(), args.current.read_bytes()
    errors = compare_packages(baseline, current, changes)
    errors.extend(compare_units(_source_units(baseline), _source_units(current), approved))
    print(json.dumps({"passed": not errors, "errors": errors,
                      "approved_changes": len(approved)}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
