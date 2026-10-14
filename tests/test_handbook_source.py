"""Verify the handbook preserves the selected theory and its reading locations."""

import hashlib
import html
import importlib.util
import json
from collections import Counter
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"
SPEC = importlib.util.spec_from_file_location("handbook_source", WEBSITE / "scripts/build_theory.py")
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)
LESSON_SECTIONS = {"3.3", "4.5", "2.4.2", "C.9", "C.12", "7.2.4", "D.31", "4.6"}
LESSON_BOUNDARY = re.compile(r'\n</div>\n\n<SectionLesson section="[^"]+" />\n\n<div v-pre class="theory-source">(?:\n\n|$)')


def restore_original(generated, page):
    body = generated.split('<div v-pre class="theory-source">\n\n', 1)[1].rsplit("\n\n</div>", 1)[0]
    body = LESSON_BOUNDARY.sub("", body)
    recovered = []
    for line in body.rstrip().splitlines():
        match = re.match(r"^(#+) (.*?) \{#[^}]+\}$", line)
        if match:
            line = "#" * (len(match.group(1)) + page.level - 1) + " " + match.group(2)
        line = html.unescape(line)
        line = re.sub(r"\]\(/theory/[^)]*#(part_\d+)\)", r"](#\1)", line)
        recovered.append(line)
    return recovered


class HandbookSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ROOT / "source" / f"{builder.TITLE}.md"
        cls.raw = cls.source.read_bytes()
        cls.lines, cls.pages = builder.split_source(cls.raw.decode("utf-8"))
        cls.manifest = json.loads((WEBSITE / "public/source-map.json").read_text(encoding="utf-8"))

    def test_downloads_are_identical_to_the_selected_editions(self):
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), builder.SOURCE_SHA256)
        self.assertEqual((WEBSITE / "public/downloads" / self.source.name).read_bytes(), self.raw)
        word = (WEBSITE / "public/downloads" / f"{builder.TITLE}.docx").read_bytes()
        self.assertEqual(hashlib.sha256(word).hexdigest(), builder.DOCX_SHA256)
        self.assertEqual(self.manifest["source_sha256"], builder.SOURCE_SHA256)

    def test_page_spans_cover_each_source_line_once_in_reading_order(self):
        records = self.manifest["pages"]
        self.assertEqual(len(records), 65)
        self.assertEqual(records[0]["source_start_line"], 1)
        self.assertEqual(records[-1]["source_end_line"], len(self.lines))
        previous_end = 0
        recovered = []
        for record in records:
            self.assertEqual(record["source_start_line"], previous_end + 1)
            chunk = "".join(self.lines[previous_end:record["source_end_line"]])
            self.assertEqual(hashlib.sha256(chunk.encode("utf-8")).hexdigest(), record["source_sha256"])
            recovered.append(chunk)
            previous_end = record["source_end_line"]
        self.assertEqual("".join(recovered).encode("utf-8"), self.raw)

    def test_rendered_markdown_reverses_to_all_original_text(self):
        for page in self.pages:
            with self.subTest(page=page.path):
                generated = (WEBSITE / page.path).read_text(encoding="utf-8")
                expected = "".join(self.lines[page.start:page.end]).rstrip().splitlines()
                self.assertEqual(restore_original(generated, page), expected)

    def test_original_anchors_and_numbered_sections_resolve(self):
        self.assertEqual(set(self.manifest["parts"]), {f"part_{i}" for i in range(1, 22)})
        routes = {record["route"]: record["path"] for record in self.manifest["pages"]}
        destinations = list(self.manifest["parts"].values()) + list(self.manifest["sections"].values())
        for destination in destinations:
            route, anchor = destination.split("#")
            page = (WEBSITE / routes[route]).read_text(encoding="utf-8")
            self.assertTrue(f'id="{anchor}"' in page or f"{{#{anchor}}}" in page, destination)
        for record in self.manifest["pages"]:
            page = (WEBSITE / record["path"]).read_text(encoding="utf-8")
            anchors = re.findall(r"\{#([^}]+)\}", page) + re.findall(r'<a id="([^"]+)">', page)
            self.assertEqual(len(anchors), len(set(anchors)), record["path"])

    def test_formula_notation_html_breaks_and_template_text_remain_literal(self):
        rendered = "\n".join((WEBSITE / page.path).read_text(encoding="utf-8") for page in self.pages)
        self.assertEqual(rendered.count("<br>"), self.raw.decode("utf-8").count("<br>"))
        self.assertIn("human&#95;strong&#95;type:&lt;ID&gt;", rendered)
        self.assertIn("S*=&lt;B,X,R,I,T,SP,K&gt;", rendered)
        self.assertIn("x&#95;&#123;t+1&#125;", rendered)
        self.assertNotIn("<ID>", rendered)
        sample = builder.Page("theory/sample.md", "Sample", 0, 3, None, 1)
        text = builder.render_page(sample, ["# Sample\n", "{{ danger() }} <script>x</script>\n", "a<br>b\n"], {})
        self.assertIn('<div v-pre class="theory-source">', text)
        self.assertIn("&#123;&#123; danger() &#125;&#125; &lt;script&gt;x&lt;/script&gt;", text)
        self.assertIn("a<br>b", text)
        formula = "x∼_H x′ ⇒ F_u(x)∼_{H−1} F_u(x′)"
        escaped = builder.safe_html(formula)
        self.assertEqual(html.unescape(escaped), formula)
        self.assertNotIn("{", escaped)
        self.assertNotIn("_", escaped)

    def test_rebuild_is_reproducible_without_the_author_machine(self):
        with tempfile.TemporaryDirectory(prefix="xikari-handbook-") as directory:
            root = Path(directory)
            lessons = WEBSITE / "content/section-lessons.json"
            if lessons.is_file():
                (root / "content").mkdir()
                shutil.copyfile(lessons, root / "content/section-lessons.json")
            result = builder.build(root, self.source, WEBSITE / "public/downloads" / f"{builder.TITLE}.docx")
            self.assertEqual(result, self.manifest)
            for record in result["pages"]:
                self.assertEqual((root / record["path"]).read_bytes(), (WEBSITE / record["path"]).read_bytes())

    def test_source_identity_change_fails_before_creating_pages(self):
        with tempfile.TemporaryDirectory(prefix="xikari-handbook-identity-") as directory:
            root = Path(directory)
            source = root / "changed.md"
            source.write_bytes(self.raw + b"\n")
            destination = root / "site"
            with self.assertRaisesRegex(ValueError, "canonical manuscript"):
                builder.build(destination, source)
            self.assertFalse(destination.exists())

    def test_eight_lessons_follow_their_own_original_units(self):
        with tempfile.TemporaryDirectory(prefix="xikari-section-lessons-") as directory:
            root = Path(directory)
            (root / "content").mkdir()
            (root / "content/section-lessons.json").write_text(
                json.dumps({"lessons": {section: {} for section in sorted(LESSON_SECTIONS)}}), encoding="utf-8")
            manifest = builder.build(root, self.source, WEBSITE / "public/downloads" / f"{builder.TITLE}.docx")
            self.assertEqual(set(manifest["annotation_sections"]), LESSON_SECTIONS)
            self.assertEqual(manifest["pages"], self.manifest["pages"])
            found = []
            for page in self.pages:
                generated = (root / page.path).read_text(encoding="utf-8")
                self.assertEqual(restore_original(generated, page),
                                 "".join(self.lines[page.start:page.end]).rstrip().splitlines())
                depth = 0
                for token in re.finditer(r'<div v-pre class="theory-source">|</div>|<SectionLesson section="([^"]+)" />', generated):
                    if token.group(1):
                        self.assertEqual(depth, 0, token.group(1))
                        found.append(token.group(1))
                    elif token.group() == "</div>":
                        depth -= 1
                    else:
                        depth += 1
                self.assertEqual(depth, 0, page.path)
                for section in LESSON_SECTIONS:
                    component = f'<SectionLesson section="{section}" />'
                    if component not in generated:
                        continue
                    heading = next(index for index in range(page.start, page.end)
                                   if re.match(r'^#{1,6}\s+' + re.escape(section) + r'(?:\s|\u3000)', self.lines[index]))
                    end = next((index for index in range(heading + 1, page.end)
                                if re.match(r'^#{1,6}\s', self.lines[index])), page.end)
                    last = next(line for line in reversed(self.lines[heading:end])
                                if line.strip() and not line.startswith('<a id="part_'))
                    literal = builder.safe_html(last.rstrip("\r\n"))
                    component_start = generated.index(component)
                    last_start = generated.rfind(literal, 0, component_start)
                    self.assertGreaterEqual(last_start, 0, section)
                    self.assertEqual(generated[last_start + len(literal):component_start].strip(), "</div>", section)
            self.assertEqual(found, manifest["annotation_sections"])
            self.assertEqual(len(found), 8)

    def test_parent_lesson_immediately_precedes_the_child_original(self):
        lines = ["# Part\n", "## 3.3 Parent\n", "Introduction.\n", "### 3.3.1 Child\n",
                 "Child text.\n", "### 3.3.2 Other child\n", "Other text.\n", "## 3.4 Next\n"]
        page = builder.Page("theory/part.md", "Part", 0, len(lines), 3, 1)
        points, _ = builder.annotation_points(lines, [page], ["3.3", "3.3.1"])
        text = builder.render_page(page, lines, {}, points)
        self.assertLess(text.index("Introduction."), text.index('section="3.3"'))
        self.assertLess(text.index('section="3.3"'), text.index("3.3.1 Child"))
        self.assertLess(text.index("Child text."), text.index('section="3.3.1"'))
        self.assertLess(text.index('section="3.3.1"'), text.index("Other child"))

    def test_reading_units_are_a_complete_source_derived_partition(self):
        stored = json.loads((WEBSITE / "content/reading-units.json").read_text(encoding="utf-8"))
        units = builder.reading_units(self.lines, self.pages)
        self.assertEqual(stored["source_sha256"], hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(stored["source_lines"], len(self.lines))
        self.assertEqual(stored["units"], units)
        self.assertEqual(len(units), 412)
        self.assertEqual(sum(unit["section_id"] is not None for unit in units), 388)
        self.assertEqual(sum(unit["heading_level"] == 3 for unit in units), 140)
        self.assertEqual(len({unit["lesson_key"] for unit in units}), 412)
        covered = Counter()
        for unit in units:
            start, end = unit["source_start_line"], unit["source_end_line"]
            covered.update(range(start, end + 1))
            self.assertEqual(hashlib.sha256("".join(self.lines[start - 1:end]).encode("utf-8")).hexdigest(), unit["source_sha256"])
        self.assertEqual(set(covered), set(range(1, len(self.lines) + 1)))
        self.assertTrue(all(count == 1 for count in covered.values()))

    def test_all_412_numbered_and_unnumbered_lessons_render_in_original_order(self):
        units = builder.reading_units(self.lines, self.pages)
        keys = [unit["lesson_key"] for unit in units]
        with tempfile.TemporaryDirectory(prefix="xikari-all-reading-units-") as directory:
            root = Path(directory)
            (root / "content").mkdir()
            (root / "content/section-lessons.json").write_text(
                json.dumps({"lessons": {key: {} for key in keys}}), encoding="utf-8")
            manifest = builder.build(root, self.source, WEBSITE / "public/downloads" / f"{builder.TITLE}.docx")
            self.assertEqual(manifest["pages"], self.manifest["pages"])
            self.assertEqual(manifest["annotation_sections"], keys)
            self.assertEqual(set(manifest["sections"]), set(keys))
            found = []
            for page in self.pages:
                text = (root / page.path).read_text(encoding="utf-8")
                self.assertEqual(restore_original(text, page),
                                 "".join(self.lines[page.start:page.end]).rstrip().splitlines())
                depth = 0
                for token in re.finditer(r'<div v-pre class="theory-source">|</div>|<SectionLesson section="([^"]+)" />', text):
                    if token.group(1):
                        self.assertEqual(depth, 0, token.group(1))
                        found.append(token.group(1))
                    elif token.group() == "</div>":
                        depth -= 1
                    else:
                        depth += 1
                self.assertEqual(depth, 0, page.path)
            self.assertEqual(found, keys)
            front = (root / "theory/index.md").read_text(encoding="utf-8")
            self.assertLess(front.index('section="front-title"'), front.index("## 范围与阅读方式"))
            self.assertLess(front.index('section="front-scope"'), front.index("## 分部目录"))
            part = (root / "theory/part-03.md").read_text(encoding="utf-8")
            self.assertLess(part.index('section="intro-03-part"'), part.index("## 3.1"))

    def test_unknown_lesson_section_fails_before_writing_theory_pages(self):
        with tempfile.TemporaryDirectory(prefix="xikari-unknown-lesson-") as directory:
            root = Path(directory)
            (root / "content").mkdir()
            (root / "content/section-lessons.json").write_text('{"lessons":{"99.999":{}}}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unknown lesson sections"):
                builder.build(root, self.source, WEBSITE / "public/downloads" / f"{builder.TITLE}.docx")
            self.assertFalse((root / "theory").exists())

    def test_missing_word_edition_requires_an_explicit_path(self):
        with tempfile.TemporaryDirectory(prefix="xikari-handbook-docx-") as directory:
            destination = Path(directory) / "site"
            with self.assertRaisesRegex(FileNotFoundError, r"--docx <path>"):
                builder.build(destination, self.source)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
