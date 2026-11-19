"""Create the handbook's theory pages from the selected canonical manuscript."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re


WEBSITE = Path(__file__).resolve().parents[1]
ROOT = WEBSITE.parent
TITLE = "Xikari-条件结构与转化论"
EN_TITLE = "Xikari: On Conditions, Structure, and Transformation"
EN_FILE = "Xikari-On-Conditions-Structure-and-Transformation.md"
# The handbook shows the author's rewording of v2 from its own copy; the skill's source/ keeps v2.
SOURCE = WEBSITE / "content/theory-source" / f"{TITLE}.md"
SOURCE_SHA256 = "5747a277dbf5a5cfb1583c0a172c3361710f4efee17d707ceb6151ce8cbaba3e"
EDITION = "表述修订稿"
SOURCE_DATE = "2026-11-19"
# v2 as first published stays downloadable: the lessons and the English edition follow it.
V2_SOURCE = ROOT / "source" / f"{TITLE}.md"
V2_SHA256 = "6ef2e508474d4ac1ad07d7e4e068955342c405b5f680afcfc40d68cca3d0149c"
V2_FILE = f"{TITLE}.v2.md"
V2_DATE = "2026-11-16"
EN_SOURCE_SHA256 = "51795bb7988f2669a324a52666c320cfba1382f597f7b5c6a1431844572da1fb"
EN_UPSTREAM_SHA256 = "f59bcdb483027736ef973b43ffc0c0ce37d9cb5e67ab3f05c6c67d22a62e65a1"
# The original Word download is an explicitly retained first edition, not v2.
DOCX_SHA256 = "878189fe49000577c2715a9ffb006f0e43a6bc03f6a5ca4ec599cb5607a97e59"
PART = re.compile(r'^<a id="part_(\d+)"></a>\s*$')
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
SECTION = re.compile(r"^((?:\d+|[A-D])(?:\.\d+)+)(?=\s|\u3000|[^\w.]|$)")
ALLOWED_HTML = re.compile(r'<a id="part_\d+"></a>|<br\s*/?>', re.IGNORECASE)
CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`)(.*?)(?<!`)\1(?!`)")
ESCAPED_PUNCTUATION = re.compile(r"\\[!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~]")
FOOTNOTE_DEFINITION = re.compile(r"^\[\^([^\]]+)\]:\s*(.*)$")
FOOTNOTE_REFERENCE = re.compile(r"\[\^([^\]]+)\](?!:)")


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
    if title in {TITLE, EN_TITLE}:
        return "book"
    if title in {"范围与阅读方式", "Scope and Reading Approach"}:
        return "reading-scope"
    if title in {"分部目录", "Contents by Part"}:
        return "contents"
    if title == "Copyright and License":
        return "copyright-license"
    if title == "MIT License":
        return "mit-license"
    return f"part-title-{part}"


def split_source(source: str, language: str = "zh") -> tuple[list[str], list[Page]]:
    lines = source.splitlines(keepends=True)
    parts = [(i, int(match.group(1))) for i, line in enumerate(lines)
             if (match := PART.match(line))]
    if [number for _, number in parts] != list(range(1, 22)):
        raise ValueError("The manuscript must contain ordered part_1 through part_21 anchors")
    prefix = "en/" if language == "en" else ""
    pages = [Page(prefix + "theory/index.md", EN_TITLE if language == "en" else TITLE,
                  0, parts[0][0], None, 1)]
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
        path = prefix + path
        if number not in {17, 20}:
            pages.append(Page(path, title, start, end, number, 1))
            continue
        sections = [(i, HEADING.match(lines[i]).group(2)) for i in range(start, end)
                    if lines[i].startswith("## ")]
        appendix = "a" if number == 17 else "d"
        if len(sections) != (11 if number == 17 else 32):
            raise ValueError(f"Unexpected appendix {appendix.upper()} section count")
        pages.append(Page(path, title, start, sections[0][0], number, 1))
        for index, (section_start, section_title) in enumerate(sections):
            section_end = sections[index + 1][0] if index + 1 < len(sections) else end
            section_number = int(SECTION.match(section_title).group(1).split(".")[1])
            section_path = f"{prefix}theory/appendix-{appendix}/{appendix}-{section_number:02}.md"
            pages.append(Page(section_path, section_title, section_start, section_end, number, 2))
    return lines, pages


def safe_html(text: str) -> str:
    def escape_literal(value: str) -> str:
        return (value.replace("<", "&lt;").replace(">", "&gt;")
                .replace("{", "&#123;").replace("}", "&#125;")
                .replace("_", "&#95;"))

    output = []
    position = 0
    # Markdown renders code spans as literal text. Entity-escaping their contents
    # would visibly print "&#95;" or "&lt;" instead of the author's identifiers.
    # The author already uses Markdown escapes in formulas such as x\_{t+1}.
    # Keep the escape together: changing it to \&#95; escapes the ampersand,
    # causing the browser to show the entity's spelling rather than an underscore.
    protected = sorted(list(ALLOWED_HTML.finditer(text)) + list(CODE_SPAN.finditer(text))
                       + list(ESCAPED_PUNCTUATION.finditer(text)),
                       key=lambda match: match.start())
    for match in protected:
        if match.start() < position:
            continue
        output.append(escape_literal(text[position:match.start()]))
        output.append(match.group())
        position = match.end()
    output.append(escape_literal(text[position:]))
    return "".join(output)


def lesson_sections(website: Path, language: str = "zh") -> list[str]:
    content = website / "content" / ("en" if language == "en" else "")
    path = content / "section-lessons.json"
    if not path.is_file():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("lessons"), dict):
        raise ValueError("section-lessons.json must contain a lessons object keyed by section number")
    if any(not isinstance(lesson, dict) for lesson in value["lessons"].values()):
        raise ValueError("Each section lesson must be an object")
    sections = list(value["lessons"])
    # A supplement may supply the whole lesson for a reading unit the import lacks.
    supplements = content / "lesson-overrides.json"
    if supplements.is_file():
        added = json.loads(supplements.read_text(encoding="utf-8")).get("lessons", {})
        if not isinstance(added, dict) or any(not isinstance(lesson, dict) for lesson in added.values()):
            raise ValueError("lesson-overrides.json must contain a lessons object of objects")
        sections += [key for key in added if key not in value["lessons"]]
    return sections


def reading_units(lines: list[str], pages: list[Page], language: str = "zh") -> list[dict]:
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
                key = {"范围与阅读方式": "front-scope", "分部目录": "front-contents",
                       "Scope and Reading Approach": "front-scope", "Contents by Part": "front-contents"}[title]
                task, kind = "FRONT", "front_matter"
            elif part == 18:
                key, task, kind = "app-b", "APP-B", "appendix_b"
            elif title in {"Copyright and License", "MIT License"}:
                key = {"Copyright and License": "copyright-license", "MIT License": "mit-license"}[title]
                task, kind = "LICENSE", "license"
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
                      "theory_sha256": EN_SOURCE_SHA256 if language == "en" else SOURCE_SHA256,
                      "website_source_route": page.route + "#" + heading_id(title, page.part) if section else None,
                      "required_output": True})
    return units


def annotation_points(lines: list[str], pages: list[Page], sections: list[str],
                      language: str = "zh") -> tuple[dict[int, list[str]], list[str]]:
    units = reading_units(lines, pages, language)
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
    fence = None
    for index in range(page.start, page.end):
        line = re.sub(r"\]\(#part_(\d+)\)",
                      lambda match: f"]({part_routes[int(match.group(1))]}#part_{match.group(1)})", lines[index])
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            rendered.append(line)
        elif fence:
            rendered.append(line)
        elif match := HEADING.match(line):
            level = len(match.group(1)) - page.level + 1
            identifier = heading_id(match.group(2), page.part)
            rendered.append(f"{'#' * max(1, level)} {safe_html(match.group(2))} {{#{identifier}}}\n")
        else:
            rendered.append(safe_html(line))
        for section in (annotations or {}).get(index + 1, []):
            rendered.append(f'\n</div>\n\n<SectionLesson section="{section}" />\n\n<div v-pre class="theory-source">\n\n')
    frontmatter = "---\ntitle: " + json.dumps(page.title, ensure_ascii=False) + "\n---\n\n"
    content = "".join(rendered).rstrip()
    # Appendix pages can refer to translator notes defined elsewhere in the
    # original part. Supply those exact definitions on every page that uses them.
    local_definitions = {match.group(1) for line in lines[page.start:page.end]
                         if (match := FOOTNOTE_DEFINITION.match(line))}
    references = list(dict.fromkeys(FOOTNOTE_REFERENCE.findall(content)))
    all_definitions = {match.group(1): line for line in lines
                       if (match := FOOTNOTE_DEFINITION.match(line))}
    missing = [key for key in references if key not in all_definitions]
    if missing:
        raise ValueError("Undefined translator notes: " + ", ".join(missing))
    extra = [all_definitions[key] for key in references if key not in local_definitions]
    if extra:
        content += "\n\n<!-- source-note-copies:start -->\n\n" + "\n".join(safe_html(line).rstrip() for line in extra)
        content += "\n\n<!-- source-note-copies:end -->"
    return frontmatter + '<div v-pre class="theory-source">\n\n' + content + "\n\n</div>\n"


def sidebar_for(pages: list[Page], language: str = "zh") -> list[dict]:
    def item(page: Page) -> dict:
        return {"text": page.title, "link": page.route}

    en = language == "en"
    groups = [{"text": "Start reading" if en else "原文入口", "items": [
        {"text": "Scope and reading approach" if en else "范围与阅读方式",
         "link": "/en/theory/" if en else "/theory/"}]}]
    for label, first, last in [("导读与通用结构", 1, 6), ("人类、行动者与推演", 7, 12),
                               ("工具、选择与治理", 13, 16)]:
        if en:
            label = {1: "Introduction and universal structure", 7: "Humans, actors, and projection",
                     13: "Tools, choice, and governance"}[first]
        groups.append({"text": label, "collapsed": True,
                       "items": [item(p) for p in pages if p.part is not None and first <= p.part <= last]})
    for number, label in [(17, "附录 A · 人类变量接口卡"), (20, "附录 D · 32 个领域")]:
        if en:
            label = {17: "Appendix A · Human variable interfaces", 20: "Appendix D · 32 domains"}[number]
        groups.append({"text": label, "collapsed": True,
                       "items": [item(p) for p in pages if p.part == number]})
    groups.insert(-1, {"text": "Terminology and common method" if en else "术语与共同方法", "collapsed": True,
                      "items": [item(p) for p in pages if p.part in {18, 19}]})
    groups.append({"text": "References and downloads" if en else "参考与下载", "items": [item(p) for p in pages if p.part == 21]
                   + [{"text": "Download the complete text" if en else "下载完整原文",
                       "link": "/en/downloads" if en else "/downloads"}]})
    return groups


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def build(website: Path = WEBSITE, source: Path | None = None, docx: Path | None = None,
          language: str = "zh") -> dict:
    if language not in {"zh", "en"}:
        raise ValueError("language must be zh or en")
    en = language == "en"
    title = EN_TITLE if en else TITLE
    expected_hash = EN_SOURCE_SHA256 if en else SOURCE_SHA256
    source = source or (ROOT / "source/en" / EN_FILE if en else SOURCE)
    data = source.read_bytes()
    if sha256(data) != expected_hash:
        raise ValueError("The canonical manuscript does not match the selected source identity")
    v2_data = None if en else V2_SOURCE.read_bytes()
    if v2_data is not None and sha256(v2_data) != V2_SHA256:
        raise ValueError("The v2 manuscript does not match its registered identity")
    download_dir = website / "public/downloads"
    # Preserve the old Word object only as a labelled legacy artifact. Its
    # availability must not gate a current Markdown edition or a clean build.
    legacy_source = docx or WEBSITE / "public/downloads" / f"{TITLE}.docx"
    legacy_data = legacy_source.read_bytes() if legacy_source.is_file() else None
    if docx is not None and legacy_data is None:
        raise FileNotFoundError(f"Word edition not found: {docx}")
    if legacy_data is not None and sha256(legacy_data) != DOCX_SHA256:
        raise ValueError("The legacy Word edition does not match the selected source identity")
    upstream = ROOT / "source/en/upstream/xikari-conditions-en.md"
    upstream_data = upstream.read_bytes() if en else None
    if upstream_data is not None and sha256(upstream_data) != EN_UPSTREAM_SHA256:
        raise ValueError("The author's English original does not match its registered identity")
    lines, pages = split_source(data.decode("utf-8"), language)
    units = reading_units(lines, pages, language)
    annotations, annotation_sections = annotation_points(lines, pages, lesson_sections(website, language), language)
    part_routes = {page.part: page.route for page in reversed(pages) if page.part is not None}
    records = []
    sections = {}
    units_by_start = {unit["source_start_line"] - 1: unit for unit in units}
    # Render and validate all pages before writing any output.
    rendered_pages = [(page, render_page(page, lines, part_routes, annotations)) for page in pages]
    for page, rendered in rendered_pages:
        raw = "".join(lines[page.start:page.end])
        path = website / page.path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8", newline="\n")
        records.append({"path": page.path, "route": page.route, "title": page.title,
                        "part": page.part, "source_start_line": page.start + 1,
                        "source_end_line": page.end, "source_sha256": sha256(raw.encode("utf-8"))})
        for index, line in enumerate(lines[page.start:page.end], page.start):
            match = HEADING.match(line)
            if match:
                unit = units_by_start[index]
                sections[unit["lesson_key"]] = page.route + "#" + heading_id(match.group(2), page.part)
    download_dir.mkdir(parents=True, exist_ok=True)
    download_name = EN_FILE if en else TITLE + ".md"
    (download_dir / download_name).write_bytes(data)
    if v2_data is not None:
        (download_dir / V2_FILE).write_bytes(v2_data)
    if upstream_data is not None:
        (download_dir / "xikari-conditions-en.original.md").write_bytes(upstream_data)
    legacy = None
    if legacy_data is not None:
        for name in [f"{TITLE}.docx", f"{TITLE}.v1.docx"]:
            target = download_dir / name
            if not target.is_file() or target.read_bytes() != legacy_data:
                target.write_bytes(legacy_data)
        legacy = {"theory_version": "v1", "language": "zh", "sha256": DOCX_SHA256,
                  "path": f"/downloads/{TITLE}.v1.docx", "source_date": "2026-10-17"}
    manifest = {"title": title, "author": "Xikari", "language": language, "theory_version": "v2"}
    if not en:
        manifest["edition"] = EDITION
    # The English reference translation was made from v2 as first published.
    manifest.update({"source_date": V2_DATE if en else SOURCE_DATE,
                     "source_sha256": expected_hash, "source_bytes": len(data),
                     "source_lines": len(lines), "download": "/downloads/" + download_name,
                     "canonical_chinese_sha256": SOURCE_SHA256})
    if en:
        manifest["translates_chinese_sha256"] = V2_SHA256
    else:
        manifest["previous_edition"] = {"theory_version": "v2", "language": "zh", "sha256": V2_SHA256,
                                        "bytes": len(v2_data), "path": "/downloads/" + V2_FILE,
                                        "source_date": V2_DATE}
    manifest.update({"parts": {f"part_{number}": route + f"#part_{number}"
                               for number, route in sorted(part_routes.items())},
                     "sections": sections, "pages": records,
                     "annotation_sections": annotation_sections})
    if legacy is not None:
        manifest["legacy_docx"] = legacy
    if en:
        manifest["author_original"] = {"path": "/downloads/xikari-conditions-en.original.md",
                                       "sha256": EN_UPSTREAM_SHA256, "bytes": len(upstream_data)}
        manifest["role"] = "Reference translation; the Chinese source governs."
    locale_path = "en/" if en else ""
    write_json(website / f"content/{locale_path}reading-units.json", {
        "language": language, "source_sha256": expected_hash, "source_lines": len(lines), "units": units})
    write_json(website / f"public/{locale_path}source-map.json", manifest)
    write_json(website / (".vitepress/en-theory-sidebar.json" if en else ".vitepress/theory-sidebar.json"),
               sidebar_for(pages, language))
    return manifest


def build_all(website: Path = WEBSITE, source: Path | None = None, docx: Path | None = None) -> dict:
    manifests = {"zh": build(website, source, docx), "en": build(website, docx=docx, language="en")}
    keys = lambda manifest: [key for key in manifest["sections"] if SECTION.match(key)]
    if keys(manifests["zh"]) != keys(manifests["en"]):
        raise ValueError("The Chinese and English numbered sections are not aligned")
    return manifests


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--docx", type=Path, help="Optional legacy v1 Word file; never represented as v2")
    parser.add_argument("--website", type=Path, default=WEBSITE)
    parser.add_argument("--language", choices=["zh", "en", "all"], default="all")
    arguments = parser.parse_args()
    if arguments.language == "all":
        manifests = build_all(arguments.website, arguments.source, arguments.docx)
    else:
        manifests = {arguments.language: build(arguments.website, arguments.source, arguments.docx, arguments.language)}
    print(json.dumps({language: {"pages": len(manifest["pages"]), "source_sha256": manifest["source_sha256"]}
                      for language, manifest in manifests.items()}))
