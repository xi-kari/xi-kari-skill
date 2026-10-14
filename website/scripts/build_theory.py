"""Create the handbook's theory pages from the unchanged canonical manuscript."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re


WEBSITE = Path(__file__).resolve().parents[1]
REPO = WEBSITE.parent
TITLE = "Xikari-条件结构与转化论"
SOURCE_SHA256 = "df579dbdbb68442b1781b066606c267761f0a1673fbd034ce93eeeb41641439f"
DOCX_SHA256 = "92a02c9118f6d2bd768d9db8a62ad6eeda8f13d44ae8f71e907f22b7a248f49e"
PART = re.compile(r'^<a id="part_(\d+)"></a>\s*$')
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
SECTION = re.compile(r"^((?:\d+|[A-D])(?:\.\d+)+)(?=\s|\u3000|[^\w.]|$)")
ALLOWED_HTML = re.compile(r'<a id="part_\d+"></a>|<br\s*/?>', re.IGNORECASE)


@dataclass(frozen=True)
class Page:
    path: str
    title: str
    start: int
    end: int
    part: int | None
    level: int

    @property
    def route(self) -> str:
        return "/" + self.path.removesuffix(".md").removesuffix("index")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def heading_id(title: str, part: int | None = None) -> str:
    match = SECTION.match(title)
    if match:
        return "section-" + match.group(1).lower().replace(".", "-")
    if title == TITLE:
        return "book"
    if title == "范围与阅读方式":
        return "reading-scope"
    if title == "分部目录":
        return "contents"
    return f"part-title-{part}"


def split_source(source: str) -> tuple[list[str], list[Page]]:
    lines = source.splitlines(keepends=True)
    parts = [(i, int(match.group(1))) for i, line in enumerate(lines)
             if (match := PART.match(line))]
    if [number for _, number in parts] != list(range(1, 22)):
        raise ValueError("The manuscript must contain ordered part_1 through part_21 anchors")
    pages = [Page("theory/index.md", TITLE, 0, parts[0][0], None, 1)]
    for position, (start, number) in enumerate(parts):
        end = parts[position + 1][0] if position + 1 < len(parts) else len(lines)
        title = next(HEADING.match(line).group(2) for line in lines[start:end]
                     if HEADING.match(line))
        if number <= 16:
            path = f"theory/part-{number:02}.md"
        else:
            path = {17: "theory/appendix-a/index.md", 18: "theory/appendix-b.md",
                    19: "theory/appendix-c.md", 20: "theory/appendix-d/index.md",
                    21: "theory/references.md"}[number]
        if number not in {17, 20}:
            pages.append(Page(path, title, start, end, number, 1))
            continue
        sections = [(i, HEADING.match(lines[i]).group(2)) for i in range(start, end)
                    if lines[i].startswith("## ")]
        prefix = "a" if number == 17 else "d"
        if len(sections) != (11 if number == 17 else 32):
            raise ValueError(f"Unexpected appendix {prefix.upper()} section count")
        pages.append(Page(path, title, start, sections[0][0], number, 1))
        for index, (section_start, section_title) in enumerate(sections):
            section_end = sections[index + 1][0] if index + 1 < len(sections) else end
            section_number = int(SECTION.match(section_title).group(1).split(".")[1])
            section_path = f"theory/appendix-{prefix}/{prefix}-{section_number:02}.md"
            pages.append(Page(section_path, section_title, section_start, section_end, number, 2))
    return lines, pages


def safe_html(text: str) -> str:
    def escape_literal(value: str) -> str:
        return (value.replace("<", "&lt;").replace(">", "&gt;")
                .replace("{", "&#123;").replace("}", "&#125;")
                .replace("_", "&#95;"))

    output = []
    position = 0
    for match in ALLOWED_HTML.finditer(text):
        output.append(escape_literal(text[position:match.start()]))
        output.append(match.group())
        position = match.end()
    output.append(escape_literal(text[position:]))
    return "".join(output)


def lesson_sections(website: Path) -> list[str]:
    path = website / "content/section-lessons.json"
    if not path.is_file():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("lessons"), dict):
        raise ValueError("section-lessons.json must contain a lessons object keyed by section number")
    if any(not isinstance(lesson, dict) for lesson in value["lessons"].values()):
        raise ValueError("Each section lesson must be an object")
    return list(value["lessons"])


def reading_units(lines: list[str], pages: list[Page]) -> list[dict]:
    headings = []
    part = None
    for index, line in enumerate(lines):
        if anchor := PART.match(line):
            part = int(anchor.group(1))
        if match := HEADING.match(line):
            headings.append((index, len(match.group(1)), match.group(2), part))
    units = []
    current_task = "FRONT"
    for position, (start, level, title, part) in enumerate(headings):
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        match = SECTION.match(title)
        section = match.group(1) if match else None
        if section:
            key = section
            output_id = "section-" + section.lower().replace(".", "-")
            kind = f"numbered_h{level}"
            if level == 2:
                current_task = "S-" + section.replace(".", "-")
            task = current_task
            subtree_end = next((index for index, other_level, _, _ in headings[position + 1:]
                                if other_level <= level), len(lines))
        else:
            subtree_end = end
            if position == 0:
                key, task, kind = "front-title", "FRONT", "front_matter"
            elif part is None:
                key = {"范围与阅读方式": "front-scope", "分部目录": "front-contents"}[title]
                task, kind = "FRONT", "front_matter"
            elif part == 18:
                key, task, kind = "app-b", "APP-B", "appendix_b"
            elif part == 21:
                key, task, kind = "references", "REFERENCES", "references"
            else:
                suffix = "part" if part <= 16 else {17: "appendix-a", 19: "appendix-c", 20: "appendix-d"}[part]
                key, kind = f"intro-{part:02}-{suffix}", "part_introduction"
                first_section = next(SECTION.match(other_title).group(1)
                                     for _, other_level, other_title, other_part in headings[position + 1:]
                                     if other_level == 2 and other_part == part and SECTION.match(other_title))
                task = "S-" + first_section.replace(".", "-")
            output_id = key
        page = next(page for page in pages if page.start <= start < page.end)
        units.append({"output_id": output_id, "lesson_key": key, "task_id": task,
                      "section_id": section, "title_exact": title, "heading_level": level,
                      "kind": kind, "source_start_line": start + 1, "source_end_line": end,
                      "subtree_end_line": subtree_end,
                      "source_sha256": sha256("".join(lines[start:end]).encode("utf-8")),
                      "theory_sha256": SOURCE_SHA256,
                      "website_source_route": page.route + "#" + heading_id(title, page.part) if section else None,
                      "required_output": True})
    return units


def annotation_points(lines: list[str], pages: list[Page], sections: list[str]) -> tuple[dict[int, list[str]], list[str]]:
    units = reading_units(lines, pages)
    by_key = {unit["lesson_key"]: unit for unit in units}
    unknown = set(sections) - set(by_key)
    if unknown:
        raise ValueError("Unknown lesson sections: " + ", ".join(sorted(unknown)))
    ordered = [unit["lesson_key"] for unit in units if unit["lesson_key"] in sections]
    points = {}
    for section in ordered:
        unit = by_key[section]
        start, end = unit["source_start_line"] - 1, unit["source_end_line"]
        while end > start and (not lines[end - 1].strip() or PART.match(lines[end - 1])):
            end -= 1
        page = next(page for page in pages if page.start <= start < page.end)
        if end > page.end:
            raise ValueError(f"Lesson section crosses generated pages: {section}")
        points.setdefault(end, []).append(section)
    return points, ordered


def render_page(page: Page, lines: list[str], part_routes: dict[int, str],
                annotations: dict[int, list[str]] | None = None) -> str:
    rendered = []
    for index in range(page.start, page.end):
        line = re.sub(r"\]\(#part_(\d+)\)",
                      lambda match: f"]({part_routes[int(match.group(1))]}#part_{match.group(1)})", lines[index])
        match = HEADING.match(line)
        if match:
            level = len(match.group(1)) - page.level + 1
            identifier = heading_id(match.group(2), page.part)
            rendered.append(f"{'#' * max(1, level)} {safe_html(match.group(2))} {{#{identifier}}}\n")
        else:
            rendered.append(safe_html(line))
        for section in (annotations or {}).get(index + 1, []):
            rendered.append(f'\n</div>\n\n<SectionLesson section="{section}" />\n\n<div v-pre class="theory-source">\n\n')
    frontmatter = "---\ntitle: " + json.dumps(page.title, ensure_ascii=False) + "\n---\n\n"
    return frontmatter + '<div v-pre class="theory-source">\n\n' + "".join(rendered).rstrip() + "\n\n</div>\n"


def sidebar_for(pages: list[Page]) -> list[dict]:
    def item(page: Page) -> dict:
        return {"text": page.title, "link": page.route}

    groups = [{"text": "原文入口", "items": [{"text": "范围与阅读方式", "link": "/theory/"}]}]
    for label, first, last in [("导读与通用结构", 1, 6), ("人类、行动者与推演", 7, 12),
                               ("工具、选择与治理", 13, 16)]:
        groups.append({"text": label, "collapsed": True,
                       "items": [item(p) for p in pages if p.part is not None and first <= p.part <= last]})
    for number, label in [(17, "附录 A · 人类变量接口卡"), (20, "附录 D · 32 个领域")]:
        groups.append({"text": label, "collapsed": True,
                       "items": [item(p) for p in pages if p.part == number]})
    groups.insert(-1, {"text": "术语与共同方法", "collapsed": True,
                      "items": [item(p) for p in pages if p.part in {18, 19}]})
    groups.append({"text": "参考与下载", "items": [item(p) for p in pages if p.part == 21]
                   + [{"text": "下载完整原文", "link": "/downloads"}]})
    return groups


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def build(website: Path = WEBSITE, source: Path | None = None, docx: Path | None = None) -> dict:
    source = source or REPO / "source" / f"{TITLE}.md"
    data = source.read_bytes()
    if sha256(data) != SOURCE_SHA256:
        raise ValueError("The canonical manuscript does not match the selected source identity")
    download_dir = website / "public/downloads"
    existing_docx = download_dir / f"{TITLE}.docx"
    if docx is None:
        if not existing_docx.is_file():
            raise FileNotFoundError("The Word edition is missing from public/downloads; provide it with --docx <path>")
        docx = existing_docx
    docx_data = docx.read_bytes()
    if sha256(docx_data) != DOCX_SHA256:
        raise ValueError("The Word edition does not match the selected source identity")
    lines, pages = split_source(data.decode("utf-8"))
    units = reading_units(lines, pages)
    annotations, annotation_sections = annotation_points(lines, pages, lesson_sections(website))
    part_routes = {page.part: page.route for page in reversed(pages) if page.part is not None}
    records = []
    sections = {}
    units_by_start = {unit["source_start_line"] - 1: unit for unit in units}
    for page in pages:
        raw = "".join(lines[page.start:page.end])
        path = website / page.path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_page(page, lines, part_routes, annotations), encoding="utf-8", newline="\n")
        records.append({"path": page.path, "route": page.route, "title": page.title,
                        "part": page.part, "source_start_line": page.start + 1,
                        "source_end_line": page.end, "source_sha256": sha256(raw.encode("utf-8"))})
        for index, line in enumerate(lines[page.start:page.end], page.start):
            match = HEADING.match(line)
            if match:
                unit = units_by_start[index]
                sections[unit["lesson_key"]] = page.route + "#" + heading_id(match.group(2), page.part)
    download_dir.mkdir(parents=True, exist_ok=True)
    (download_dir / f"{TITLE}.md").write_bytes(data)
    if docx.resolve() != existing_docx.resolve():
        existing_docx.write_bytes(docx_data)
    manifest = {"title": TITLE, "author": "Xikari", "source_date": "2026-10-13",
                "source_sha256": SOURCE_SHA256, "source_bytes": len(data),
                "source_lines": len(lines), "docx_sha256": DOCX_SHA256,
                "parts": {f"part_{number}": route + f"#part_{number}" for number, route in sorted(part_routes.items())},
                "sections": sections, "pages": records}
    if annotation_sections:
        manifest["annotation_sections"] = annotation_sections
    write_json(website / "content/reading-units.json", {
        "source_sha256": SOURCE_SHA256, "source_lines": len(lines), "units": units})
    write_json(website / "public/source-map.json", manifest)
    write_json(website / ".vitepress/theory-sidebar.json", sidebar_for(pages))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--docx", type=Path)
    parser.add_argument("--website", type=Path, default=WEBSITE)
    arguments = parser.parse_args()
    manifest = build(arguments.website, arguments.source, arguments.docx)
    print(json.dumps({"pages": len(manifest["pages"]), "source_sha256": manifest["source_sha256"]}))
