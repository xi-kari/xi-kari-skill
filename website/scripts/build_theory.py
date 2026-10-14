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


def render_page(page: Page, lines: list[str], part_routes: dict[int, str]) -> str:
    raw = "".join(lines[page.start:page.end])
    raw = re.sub(r"\]\(#part_(\d+)\)",
                 lambda match: f"]({part_routes[int(match.group(1))]}#part_{match.group(1)})", raw)
    rendered = []
    for line in raw.splitlines(keepends=True):
        match = HEADING.match(line)
        if match:
            level = len(match.group(1)) - page.level + 1
            identifier = heading_id(match.group(2), page.part)
            rendered.append(f"{'#' * max(1, level)} {safe_html(match.group(2))} {{#{identifier}}}\n")
        else:
            rendered.append(safe_html(line))
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
    part_routes = {page.part: page.route for page in reversed(pages) if page.part is not None}
    records = []
    sections = {}
    for page in pages:
        raw = "".join(lines[page.start:page.end])
        path = website / page.path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_page(page, lines, part_routes), encoding="utf-8", newline="\n")
        records.append({"path": page.path, "route": page.route, "title": page.title,
                        "part": page.part, "source_start_line": page.start + 1,
                        "source_end_line": page.end, "source_sha256": sha256(raw.encode("utf-8"))})
        for line in lines[page.start:page.end]:
            match = HEADING.match(line)
            if match and (section := SECTION.match(match.group(2))):
                sections[section.group(1)] = page.route + "#" + heading_id(match.group(2), page.part)
    download_dir.mkdir(parents=True, exist_ok=True)
    (download_dir / f"{TITLE}.md").write_bytes(data)
    if docx.resolve() != existing_docx.resolve():
        existing_docx.write_bytes(docx_data)
    manifest = {"title": TITLE, "author": "Xikari", "source_date": "2026-10-13",
                "source_sha256": SOURCE_SHA256, "source_bytes": len(data),
                "source_lines": len(lines), "docx_sha256": DOCX_SHA256,
                "parts": {f"part_{number}": route + f"#part_{number}" for number, route in sorted(part_routes.items())},
                "sections": sections, "pages": records}
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
