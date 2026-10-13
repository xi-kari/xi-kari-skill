"""Read complete sections from the bundled Xikari manuscript."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "Xikari-条件结构与转化论.md"
MANIFEST = ROOT / "source" / "source-manifest.json"
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
SECTION = re.compile(r"^((?:\d+|[A-D])(?:\.\d+)+)(?=\s|\u3000|[^\w.]|$)")
PART = re.compile(r'^<a id="part_(\d+)"></a>\s*$')


def build_index(lines: list[str]) -> tuple[dict, dict]:
    headings = []
    parts = []
    for i, line in enumerate(lines):
        match = HEADING.match(line)
        if match:
            headings.append((i, len(match.group(1)), match.group(2)))
        match = PART.match(line)
        if match:
            parts.append((int(match.group(1)), i))
    sections = {}
    for pos, (start, level, title) in enumerate(headings):
        match = SECTION.match(title)
        if not match:
            continue
        key = match.group(1)
        if key in sections:
            raise ValueError(f"Duplicate section: {key}")
        end = next((row[0] for row in headings[pos + 1:] if row[1] <= level), len(lines))
        while end > start and (not lines[end - 1].strip() or PART.match(lines[end - 1])):
            end -= 1
        sections[key] = {"title": title, "start": start, "end": end}
    part_index = {}
    for pos, (key, start) in enumerate(parts):
        end = parts[pos + 1][1] if pos + 1 < len(parts) else len(lines)
        part_index[key] = {"start": start, "end": end}
    return sections, part_index


def merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--section", action="append", default=[], help="Exact section ID, e.g. 4.17 or C.3")
    parser.add_argument("--part", type=int, action="append", default=[], help="Part anchor number 1 through 21")
    parser.add_argument("--list", action="store_true", help="List available sections")
    parser.add_argument("--check", action="store_true", help="Maintenance-only source identity check")
    args = parser.parse_args()
    try:
        data = SOURCE.read_bytes()
        lines = data.decode("utf-8-sig").splitlines()
        sections, parts = build_index(lines)
        if args.check:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
            digest = hashlib.sha256(data).hexdigest()
            valid = digest == manifest["sha256"] and len(data) == manifest["bytes"]
            print(json.dumps({"source_matches_manifest": valid, "sha256": digest,
                              "bytes": len(data), "sections": len(sections), "parts": len(parts)}, ensure_ascii=False))
            if not valid:
                return 1
        if args.list:
            for key, item in sections.items():
                print(f"{key}\t{item['start'] + 1}-{item['end']}\t{item['title']}")
        ranges = []
        for key in args.section:
            if key not in sections:
                raise ValueError(f"Unknown section: {key}; use --list")
            item = sections[key]
            ranges.append((item["start"], item["end"]))
        for key in args.part:
            if key not in parts:
                raise ValueError(f"Unknown part: {key}; available: {sorted(parts)}")
            item = parts[key]
            ranges.append((item["start"], item["end"]))
        for start, end in merge_ranges(ranges):
            print(f"\n[{SOURCE.name} · lines {start + 1}-{end}]\n")
            print("\n".join(lines[start:end]))
        if not (args.check or args.list or ranges):
            parser.print_help()
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"Source reader: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
