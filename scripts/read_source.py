"""Read complete sections from the bundled Xikari manuscript.

The Chinese manuscript is the theory source. ``--lang en`` reads the bundled
English reference edition, which shares every section and part identifier;
``--parallel`` prints the Chinese and English text of the same sections.
"""

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
EN_MANIFEST = ROOT / "source" / "en" / "source-manifest.json"
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


def section_at(order: list[tuple[str, dict]], index: int) -> tuple[str | None, dict | None]:
    """Return the most specific section containing a zero-based line index.

    ``order`` is sections sorted by ascending start line. Deeper subsections
    begin later, so the last match is the innermost containing section.
    """
    found_key = found_item = None
    for key, item in order:
        if item["start"] > index:
            break
        if index < item["end"]:
            found_key, found_item = key, item
    return found_key, found_item


def search_lines(lines: list[str], order: list[tuple[str, dict]], terms: list[str], limit: int,
                 context: int = 0) -> list[dict]:
    """Find lines containing every term (case-insensitive literal match)."""
    needles = [term.casefold() for term in terms]
    hits = []
    for index, line in enumerate(lines):
        folded = line.casefold()
        if not all(needle in folded for needle in needles):
            continue
        key, item = section_at(order, index)
        neighbours = []
        if context:
            start = max(0, index - context)
            stop = min(len(lines), index + context + 1)
            neighbours = [{"line": row + 1, "text": lines[row]} for row in range(start, stop) if row != index]
        hits.append({
            "line": index + 1,
            "section": key,
            "section_title": item["title"] if item else None,
            "text": line,
            "context": neighbours,
        })
        if limit and len(hits) >= limit:
            break
    return hits


def full_text_chunks(text: str, size: int) -> list[tuple[int, int]]:
    if size < 1:
        raise ValueError("Chunk size must be positive")
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            paragraph = text.rfind("\n\n", start, end)
            line = text.rfind("\n", start, end)
            if paragraph >= start + size // 2:
                end = paragraph + 2
            elif line >= start + size // 2:
                end = line + 1
        chunks.append((start, end))
        start = end
    return chunks


def english_source() -> tuple[Path, dict]:
    """Return the English reference edition and its manifest."""
    manifest = json.loads(EN_MANIFEST.read_text(encoding="utf-8"))
    path = (EN_MANIFEST.parent / manifest["source_file"]).resolve()
    if not path.is_relative_to(EN_MANIFEST.parent.resolve()):
        raise ValueError("English edition escapes source/en")
    return path, manifest


def load_edition(path: Path) -> tuple[bytes, str, list[str], dict, dict]:
    data = path.read_bytes()
    text = data.decode("utf-8-sig")
    lines = text.splitlines()
    sections, parts = build_index(lines)
    return data, text, lines, sections, parts


def check_english(zh_manifest: dict, zh_sections: dict, zh_parts: dict) -> dict:
    """Compare the English edition's identity and structure with the Chinese source."""
    if not EN_MANIFEST.exists():
        return {"present": False, "ok": True}
    path, manifest = english_source()
    data, _, _, sections, parts = load_edition(path)
    digest = hashlib.sha256(data).hexdigest()
    result = {
        "present": True,
        "matches_manifest": digest == manifest.get("sha256") and len(data) == manifest.get("bytes"),
        "translates_current_source": manifest.get("translates", {}).get("sha256") == zh_manifest.get("sha256"),
        "same_sections": list(sections) == list(zh_sections),
        "same_parts": sorted(parts) == sorted(zh_parts),
        "sha256": digest,
    }
    result["ok"] = all(result[key] for key in ("matches_manifest", "translates_current_source", "same_sections", "same_parts"))
    return result


def selected_ranges(sections: dict, parts: dict, keys: list[str], numbers: list[int]) -> list[tuple[int, int]]:
    ranges = []
    for key in keys:
        if key not in sections:
            raise ValueError(f"Unknown section: {key}; use --list")
        ranges.append((sections[key]["start"], sections[key]["end"]))
    for number in numbers:
        if number not in parts:
            raise ValueError(f"Unknown part: {number}; available: {sorted(parts)}")
        ranges.append((parts[number]["start"], parts[number]["end"]))
    return merge_ranges(ranges)


MESSAGES = {
    "zh": {
        "none": "未找到包含全部检索词的原文行；可换用原文实际用词，或改读相关完整小节。",
        "hits": "命中 {count} 行（检索词：{terms}；显示上限 {limit}；用于学完后定位复读，不替代完整阅读）",
        "joiner": "、",
        "front": "书前说明或参考文献区域",
        "line": "行{line}: {text}",
    },
    "en": {
        "none": "No line contains every search term; try the edition's actual wording, or read the relevant complete section.",
        "hits": "{count} matching line(s) (terms: {terms}; limit {limit}; for locating passages after complete study, not a substitute for it)",
        "joiner": ", ",
        "front": "front matter or references",
        "line": "line {line}: {text}",
    },
}


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--section", action="append", default=[], help="Exact section ID, e.g. 4.17 or C.3")
    parser.add_argument("--part", type=int, action="append", default=[], help="Part anchor number 1 through 21")
    parser.add_argument("--list", action="store_true", help="List available sections")
    parser.add_argument("--check", action="store_true", help="Maintenance-only source identity check")
    parser.add_argument("--chunks", action="store_true", help="Show total chunks for sequential complete reading")
    parser.add_argument("--chunk", type=int, action="append", default=[], help="Read a complete-text chunk, starting at 1")
    parser.add_argument("--chunk-size", type=int, default=6000, help="Maximum characters per chunk; keep fixed while reading")
    parser.add_argument("--search", action="append", default=[], metavar="TERM",
                        help="Locate a literal term after full-source study; repeatable, all terms must appear on a line")
    parser.add_argument("--limit", type=int, default=20, help="Maximum reported search hits")
    parser.add_argument("--context", type=int, default=0, help="Neighbouring lines reported around each search hit")
    parser.add_argument("--lang", choices=("zh", "en"), default="zh",
                        help="zh reads the Chinese theory source (default); en reads the English reference edition")
    parser.add_argument("--parallel", action="store_true",
                        help="With --section or --part, print the Chinese text and then the English text of the same range")
    args = parser.parse_args()
    try:
        path = SOURCE if args.lang == "zh" else english_source()[0]
        data, source_text, lines, sections, parts = load_edition(path)
        chunks = full_text_chunks(source_text, args.chunk_size)
        text = MESSAGES[args.lang]
        if args.limit < 1:
            raise ValueError("--limit must be positive")
        if args.context < 0:
            raise ValueError("--context must not be negative")
        if any(not term.strip() for term in args.search):
            raise ValueError("Search terms must not be empty")
        if args.parallel and not (args.section or args.part):
            raise ValueError("--parallel needs --section or --part")
        for number in args.chunk:
            if not 1 <= number <= len(chunks):
                raise ValueError(f"Unknown chunk: {number}; available: 1 through {len(chunks)}")
        editions = [(path, lines, sections, parts)]
        if args.parallel:
            english = english_source()[0]
            editions = [(SOURCE, *load_edition(SOURCE)[2:]), (english, *load_edition(english)[2:])]
        planned = [(name, rows, selected_ranges(index, anchors, args.section, args.part))
                   for name, rows, index, anchors in editions]
        if args.search:
            order = sorted(sections.items(), key=lambda item: item[1]["start"])
            hits = search_lines(lines, order, args.search, args.limit, args.context)
            if not hits:
                print(text["none"])
            else:
                print(text["hits"].format(count=len(hits), terms=text["joiner"].join(args.search), limit=args.limit))
            for hit in hits:
                where = f"§{hit['section']}　{hit['section_title']}" if hit["section"] else text["front"]
                print(f"\n> {where}")
                for neighbour in hit["context"]:
                    if neighbour["line"] < hit["line"]:
                        print(text["line"].format(line=neighbour["line"], text=neighbour["text"]))
                print(text["line"].format(line=hit["line"], text=hit["text"]))
                for neighbour in hit["context"]:
                    if neighbour["line"] > hit["line"]:
                        print(text["line"].format(line=neighbour["line"], text=neighbour["text"]))
        if args.chunks:
            print(json.dumps({"source": path.name, "characters": len(source_text),
                              "chunk_size": args.chunk_size, "chunks": len(chunks),
                              "reading_order": f"1 through {len(chunks)}", "includes_preface_and_references": True}, ensure_ascii=False))
        for number in args.chunk:
            start, end = chunks[number - 1]
            first_line = source_text.count("\n", 0, start) + 1
            last_line = source_text.count("\n", 0, end - 1) + 1
            print(f"\n[{path.name} · chunk {number}/{len(chunks)} · chars {start + 1}-{end} · lines {first_line}-{last_line}]\n")
            sys.stdout.write(source_text[start:end])
            if not source_text[start:end].endswith("\n"):
                print()
        if args.check:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
            zh_data, _, _, zh_sections, zh_parts = load_edition(SOURCE)
            digest = hashlib.sha256(zh_data).hexdigest()
            valid = digest == manifest["sha256"] and len(zh_data) == manifest["bytes"]
            english = check_english(manifest, zh_sections, zh_parts)
            print(json.dumps({"source_matches_manifest": valid, "sha256": digest,
                              "bytes": len(zh_data), "sections": len(zh_sections), "parts": len(zh_parts),
                              "english": english}, ensure_ascii=False))
            if not valid or not english["ok"]:
                return 1
        if args.list:
            for key, item in sections.items():
                print(f"{key}\t{item['start'] + 1}-{item['end']}\t{item['title']}")
        for name, rows, ranges in planned:
            for start, end in ranges:
                print(f"\n[{name.name} · lines {start + 1}-{end}]\n")
                print("\n".join(rows[start:end]))
        if not (args.check or args.list or args.section or args.part or args.chunks or args.chunk or args.search):
            parser.print_help()
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"Source reader: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
