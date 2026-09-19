#!/usr/bin/env python3
"""Read-only verification of an explicitly approved, unit-exact source change."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from build_source_snapshot import extract_snapshot


def source_units(path: Path) -> dict[str, list[dict[str, object]]]:
    snapshot = extract_snapshot(path.read_bytes())
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
    errors = compare_units(source_units(args.baseline), source_units(args.current), approved)
    print(json.dumps({"passed": not errors, "errors": errors,
                      "approved_changes": len(approved)}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
