"""Verify the handbook preserves the selected theory and its reading locations."""

import hashlib
import html
from html.parser import HTMLParser
import importlib.util
import json
from collections import Counter
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"
REWORDED_SHA256 = "5747a277dbf5a5cfb1583c0a172c3361710f4efee17d707ceb6151ce8cbaba3e"
V2_SHA256 = "6ef2e508474d4ac1ad07d7e4e068955342c405b5f680afcfc40d68cca3d0149c"
SPEC = importlib.util.spec_from_file_location("handbook_source", WEBSITE / "scripts/build_theory.py")
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)
LESSON_SECTIONS = {"3.3", "4.5", "2.4.2", "C.9", "C.12", "7.2.4", "D.31", "4.6"}
LESSON_BOUNDARY = re.compile(r'\n</div>\n\n<SectionLesson section="[^"]+" />\n\n<div v-pre class="theory-source">(?:\n\n|$)')


def restore_original(generated, page):
    body = generated.split('<div v-pre class="theory-source">\n\n', 1)[1].rsplit("\n\n</div>", 1)[0]
    # A copied note can begin a source block immediately after its final lesson.
    # Remove the copies before merging blocks so their separator stays intact.
    body = re.sub(r"\n\n<!-- source-note-copies:start -->.*?<!-- source-note-copies:end -->", "", body, flags=re.S)
    body = LESSON_BOUNDARY.sub("", body)
    recovered = []
    for line in body.rstrip().splitlines():
        match = re.match(r"^(#+) (.*?) \{#[^}]+\}$", line)
        if match:
            line = "#" * (len(match.group(1)) + page.level - 1) + " " + match.group(2)
        line = html.unescape(line)
        line = re.sub(r"\]\(/(?:en/)?theory/[^)]*#(part_\d+)\)", r"](#\1)", line)
        recovered.append(line)
    return recovered


class HandbookSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WEBSITE / "public/downloads" / f"{builder.TITLE}.md"
        cls.raw = cls.source.read_bytes()
        cls.lines, cls.pages = builder.split_source(cls.raw.decode("utf-8"))
        cls.manifest = json.loads((WEBSITE / "public/source-map.json").read_text(encoding="utf-8"))

    def test_downloads_are_identical_to_the_selected_editions(self):
        self.assertEqual(builder.SOURCE_SHA256, REWORDED_SHA256)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), builder.SOURCE_SHA256)
        self.assertEqual(self.raw, builder.SOURCE.read_bytes())
        word = (WEBSITE / "public/downloads" / f"{builder.TITLE}.docx").read_bytes()
        self.assertEqual(hashlib.sha256(word).hexdigest(), builder.DOCX_SHA256)
        self.assertEqual(self.manifest["source_sha256"], builder.SOURCE_SHA256)
        self.assertEqual(self.manifest["theory_version"], "v2")
        self.assertEqual(self.manifest["edition"], "表述修订稿")
        self.assertEqual(self.manifest["source_date"], "2026-11-19")
        self.assertEqual(self.manifest["legacy_docx"]["theory_version"], "v1")
        self.assertEqual(self.manifest["legacy_docx"]["sha256"], builder.DOCX_SHA256)
        self.assertNotIn("docx_sha256", self.manifest)

    def test_the_handbook_reads_its_own_copy_while_the_skill_keeps_v2(self):
        self.assertTrue(builder.SOURCE.is_relative_to(WEBSITE / "content"))
        self.assertEqual(hashlib.sha256(builder.SOURCE.read_bytes()).hexdigest(), REWORDED_SHA256)
        skill_source = (ROOT / "source" / self.source.name).read_bytes()
        self.assertEqual(hashlib.sha256(skill_source).hexdigest(), V2_SHA256)
        self.assertEqual(builder.V2_SOURCE, ROOT / "source" / self.source.name)

    def test_v2_download_is_byte_identical_to_the_v2_source(self):
        v2 = (ROOT / "source" / self.source.name).read_bytes()
        self.assertEqual(builder.V2_SHA256, V2_SHA256)
        self.assertEqual((WEBSITE / "public/downloads" / f"{builder.TITLE}.v2.md").read_bytes(), v2)
        self.assertEqual(self.manifest["previous_edition"], {
            "theory_version": "v2", "language": "zh", "sha256": V2_SHA256, "bytes": len(v2),
            "path": f"/downloads/{builder.TITLE}.v2.md", "source_date": "2026-11-16"})

    def test_changed_v2_source_fails_before_creating_pages(self):
        with tempfile.TemporaryDirectory(prefix="xikari-handbook-v2-") as directory:
            root = Path(directory)
            changed = root / "v2.md"
            changed.write_bytes((ROOT / "source" / self.source.name).read_bytes() + b"\n")
            destination = root / "site"
            with mock.patch.object(builder, "V2_SOURCE", changed):
                with self.assertRaisesRegex(ValueError, "v2 manuscript"):
                    builder.build(destination, self.source)
            self.assertFalse(destination.exists())

    def test_default_build_uses_the_handbooks_selected_edition(self):
        with tempfile.TemporaryDirectory(prefix="xikari-handbook-default-") as directory:
            destination = Path(directory) / "site"
            manifest = builder.build(
                destination, docx=WEBSITE / "public/downloads" / f"{builder.TITLE}.docx")
            self.assertEqual(manifest["source_sha256"], builder.SOURCE_SHA256)
            self.assertEqual((destination / "public/downloads" / self.source.name).read_bytes(), self.raw)
            self.assertEqual((destination / "public/downloads" / f"{builder.TITLE}.v2.md").read_bytes(),
                             (ROOT / "source" / self.source.name).read_bytes())
            self.assertEqual(manifest["pages"], self.manifest["pages"])

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
        self.assertIn("∩&#95;&#123;x∈X&#95;y&#125;A&#95;ok(x)", rendered)
        self.assertIn("SP=&lt;A,X,T,O,C,R,I,N,J&gt;", rendered)
        self.assertIn("S*=&lt;B,X,R,I,T,SP,K&gt;", rendered)
        self.assertIn("x&#95;&#123;t+1&#125;", rendered)
        self.assertNotIn("<A,X,T", rendered)
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
                supplements = WEBSITE / "content/lesson-overrides.json"
                if supplements.is_file():
                    shutil.copyfile(supplements, root / "content/lesson-overrides.json")
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
        self.assertEqual(len(units), 421)
        self.assertEqual(sum(unit["section_id"] is not None for unit in units), 397)
        self.assertEqual(sum(unit["heading_level"] == 3 for unit in units), 147)
        self.assertEqual(len({unit["lesson_key"] for unit in units}), 421)
        covered = Counter()
        for unit in units:
            start, end = unit["source_start_line"], unit["source_end_line"]
            covered.update(range(start, end + 1))
            self.assertEqual(hashlib.sha256("".join(self.lines[start - 1:end]).encode("utf-8")).hexdigest(), unit["source_sha256"])
        self.assertEqual(set(covered), set(range(1, len(self.lines) + 1)))
        self.assertTrue(all(count == 1 for count in covered.values()))

    def test_all_numbered_and_unnumbered_lessons_render_in_original_order(self):
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

    def test_every_reading_unit_has_a_lesson_once_supplements_apply(self):
        imported_bytes = (WEBSITE / "content/section-lessons.json").read_bytes()
        imported = json.loads(imported_bytes)["lessons"]
        supplements = json.loads((WEBSITE / "content/lesson-overrides.json").read_text(encoding="utf-8"))
        units = [unit["lesson_key"] for unit in
                 json.loads((WEBSITE / "content/reading-units.json").read_text(encoding="utf-8"))["units"]]
        self.assertEqual(supplements["baseSha256"], hashlib.sha256(imported_bytes).hexdigest())
        self.assertLessEqual(set(supplements["lessons"]), set(imported) | set(units))
        self.assertEqual(set(imported) | set(supplements["lessons"]), set(units))
        self.assertEqual(self.manifest["annotation_sections"], units)
        for key in set(units) - set(imported):
            lesson = supplements["lessons"][key]
            self.assertTrue(lesson.get("title") and lesson.get("lead") and lesson.get("explanation"), key)

    def test_supplement_supplies_the_lesson_for_a_unit_the_import_lacks(self):
        with tempfile.TemporaryDirectory(prefix="xikari-supplemented-unit-") as directory:
            root = Path(directory)
            (root / "content").mkdir()
            (root / "content/section-lessons.json").write_text('{"lessons":{"3.3":{}}}', encoding="utf-8")
            (root / "content/lesson-overrides.json").write_text(
                json.dumps({"baseSha256": "-", "lessons": {"3.3": {"lead": "x"}, "1.5.3": {"title": "y"}}}), encoding="utf-8")
            manifest = builder.build(root, self.source, WEBSITE / "public/downloads" / f"{builder.TITLE}.docx")
            self.assertEqual(manifest["annotation_sections"], ["1.5.3", "3.3"])
            part = (root / "theory/part-01.md").read_text(encoding="utf-8")
            self.assertLess(part.index("有读取的记录，或有完成的标记，也不证明已经理解。"), part.index('<SectionLesson section="1.5.3" />'))
            self.assertLess(part.index('<SectionLesson section="1.5.3" />'), part.index("## 1.6 "))

    def test_unknown_supplemented_unit_fails_before_writing_theory_pages(self):
        with tempfile.TemporaryDirectory(prefix="xikari-unknown-supplement-") as directory:
            root = Path(directory)
            (root / "content").mkdir()
            (root / "content/section-lessons.json").write_text('{"lessons":{"3.3":{}}}', encoding="utf-8")
            (root / "content/lesson-overrides.json").write_text('{"lessons":{"99.999":{}}}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unknown lesson sections"):
                builder.build(root, self.source, WEBSITE / "public/downloads" / f"{builder.TITLE}.docx")
            self.assertFalse((root / "theory").exists())

    @unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
    def test_site_loader_adds_lessons_only_for_listed_reading_units(self):
        loader = (WEBSITE / "scripts/lesson_data.mjs").as_uri()
        script = ("import { loadLessons } from %s\n"
                  "try { console.log(JSON.stringify(loadLessons(process.argv[1]))) }\n"
                  "catch (error) { console.log(JSON.stringify({ error: error.message })) }\n") % json.dumps(loader)
        with tempfile.TemporaryDirectory(prefix="xikari-lesson-loader-") as directory:
            root = Path(directory)
            (root / "content").mkdir()
            imported = b'{"lessons":{"3.3":{"title":"a","lead":"b"}}}'
            (root / "content/section-lessons.json").write_bytes(imported)
            (root / "content/reading-units.json").write_text(
                json.dumps({"units": [{"lesson_key": "3.3"}, {"lesson_key": "1.5.3"}]}), encoding="utf-8")

            def load(lessons):
                (root / "content/lesson-overrides.json").write_text(json.dumps(
                    {"baseSha256": hashlib.sha256(imported).hexdigest(), "lessons": lessons}), encoding="utf-8")
                result = subprocess.run(["node", "--input-type=module", "-e", script, str(root)],
                                        capture_output=True, text=True, encoding="utf-8", check=True)
                return json.loads(result.stdout)

            self.assertEqual(load({"3.3": {"lead": "c"}, "1.5.3": {"title": "d"}}),
                             {"3.3": {"title": "a", "lead": "c"}, "1.5.3": {"title": "d"}})
            self.assertEqual(load({"99.999": {"title": "e"}}), {"error": "Unknown supplemented reading unit: 99.999"})

    def test_unknown_lesson_section_fails_before_writing_theory_pages(self):
        with tempfile.TemporaryDirectory(prefix="xikari-unknown-lesson-") as directory:
            root = Path(directory)
            (root / "content").mkdir()
            (root / "content/section-lessons.json").write_text('{"lessons":{"99.999":{}}}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unknown lesson sections"):
                builder.build(root, self.source, WEBSITE / "public/downloads" / f"{builder.TITLE}.docx")
            self.assertFalse((root / "theory").exists())

    def test_default_build_keeps_a_labelled_legacy_word_download(self):
        with tempfile.TemporaryDirectory(prefix="xikari-handbook-docx-") as directory:
            destination = Path(directory) / "site"
            manifest = builder.build(destination, self.source)
            self.assertEqual(manifest["legacy_docx"]["theory_version"], "v1")
            legacy = destination / "public" / manifest["legacy_docx"]["path"].lstrip("/")
            self.assertEqual(hashlib.sha256(legacy.read_bytes()).hexdigest(), builder.DOCX_SHA256)

    def test_explicit_missing_word_download_fails_before_creating_pages(self):
        with tempfile.TemporaryDirectory(prefix="xikari-handbook-docx-") as directory:
            root = Path(directory)
            with self.assertRaisesRegex(FileNotFoundError, "Word edition not found"):
                builder.build(root / "site", docx=root / "missing.docx")
            self.assertFalse((root / "site").exists())


class BilingualHandbookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (ROOT / "source/en" / builder.EN_FILE).read_bytes()
        cls.lines, cls.pages = builder.split_source(cls.raw.decode("utf-8"), "en")
        cls.manifest = json.loads((WEBSITE / "public/en/source-map.json").read_text(encoding="utf-8"))

    def test_english_source_and_author_original_downloads_retain_bytes(self):
        downloads = WEBSITE / "public/downloads"
        self.assertEqual((downloads / builder.EN_FILE).read_bytes(), self.raw)
        self.assertEqual((downloads / "xikari-conditions-en.original.md").read_bytes(),
                         (ROOT / "source/en/upstream/xikari-conditions-en.md").read_bytes())
        self.assertEqual(self.manifest["source_sha256"], hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(self.manifest["canonical_chinese_sha256"], builder.SOURCE_SHA256)

    def test_english_edition_names_the_chinese_text_it_translates(self):
        # The reference translation follows v2 as first published; the Chinese was reworded later.
        self.assertEqual(self.manifest["translates_chinese_sha256"], V2_SHA256)
        self.assertEqual(self.manifest["source_date"], "2026-11-16")
        self.assertNotIn("edition", self.manifest)
        chinese = json.loads((WEBSITE / "public/source-map.json").read_text(encoding="utf-8"))
        self.assertEqual(chinese["previous_edition"]["sha256"], self.manifest["translates_chinese_sha256"])
        self.assertNotIn("translates_chinese_sha256", chinese)

    def test_all_numbered_sections_keep_the_same_route_and_anchor_across_languages(self):
        chinese = json.loads((WEBSITE / "public/source-map.json").read_text(encoding="utf-8"))
        numbered = {key: route for key, route in chinese["sections"].items() if builder.SECTION.match(key)}
        english = {key: route for key, route in self.manifest["sections"].items() if builder.SECTION.match(key)}
        self.assertEqual(len(numbered), 397)
        self.assertEqual(english, {key: "/en" + route for key, route in numbered.items()})
        self.assertEqual(len(self.pages), 65)

    def test_english_source_pages_preserve_the_entire_manuscript_including_license(self):
        recovered = []
        for page in self.pages:
            rendered = (WEBSITE / page.path).read_text(encoding="utf-8")
            expected = "".join(self.lines[page.start:page.end]).rstrip().splitlines()
            self.assertEqual(restore_original(rendered, page), expected, page.path)
            recovered.extend(self.lines[page.start:page.end])
        self.assertEqual("".join(recovered).encode("utf-8"), self.raw)
        self.assertIn("copyright-license", self.manifest["sections"])
        self.assertIn("mit-license", self.manifest["sections"])

    def test_translator_notes_resolve_on_every_split_page(self):
        originals = {match.group(1): match.group(2) for line in self.lines
                     if (match := builder.FOOTNOTE_DEFINITION.match(line))}
        observed = set()
        copied = 0
        for page in self.pages:
            rendered = (WEBSITE / page.path).read_text(encoding="utf-8")
            definitions = {match.group(1): html.unescape(match.group(2)) for line in rendered.splitlines()
                           if (match := builder.FOOTNOTE_DEFINITION.match(line))}
            references = set(builder.FOOTNOTE_REFERENCE.findall(rendered))
            self.assertLessEqual(references, set(definitions), page.path)
            for key, value in definitions.items():
                self.assertEqual(value, originals[key], key)
            observed.update(references)
            copied += "source-note-copies:start" in rendered
        self.assertEqual(observed, set(originals))
        self.assertEqual(len(observed), 45)
        self.assertGreater(copied, 0)

    def test_inline_code_and_fenced_code_keep_literal_punctuation(self):
        sample = builder.Page("en/theory/sample.md", "Sample", 0, 7, None, 1)
        lines = ["# Sample\n", "`claim_type=O` and ``x_<ID>{t}`value``\n", "\n",
                 "```text\n", "x_<ID>{t} & input\n", "```\n", "x_{t+1}\n"]
        rendered = builder.render_page(sample, lines, {})
        self.assertIn("`claim_type=O`", rendered)
        self.assertIn("``x_<ID>{t}`value``", rendered)
        self.assertIn("```text\nx_<ID>{t} & input\n```", rendered)
        self.assertIn("x&#95;&#123;t+1&#125;", rendered)
        self.assertEqual(restore_original(rendered, sample), [line.rstrip() for line in lines])

    @unittest.skipUnless(shutil.which("node") and
                         (WEBSITE / "node_modules/vitepress/dist/node/index.js").is_file(),
                         "The website's VitePress dependencies are not installed")
    def test_markdown_escapes_and_code_render_without_visible_entity_spelling(self):
        # Reversing generated Markdown is insufficient: \&#95; can reverse to \_
        # while rendering as the visible characters "&#95;". Compare the actual
        # Markdown renderer's text output for every affected manuscript line.
        examples = [r"x\_{t+1}=x\_t−k x\_{t−d}",
                    r"M(F\_t(x)) and F̄\_t(M(x))",
                    r"`claim_type=O` and ``x_<ID>{t}`value``",
                    r"\_literal\_ &amp; input \{value\} \\< limit",
                    "```text\nx_<ID>{t} & input\n```"]
        examples += [line.rstrip() for line in self.lines if r"\_" in line]
        self.assertGreater(len(examples), 10)
        generated = []
        for text in examples:
            lines = ["# Sample\n", text + "\n"]
            page = builder.Page("en/theory/sample.md", "Sample", 0, len(lines), None, 1)
            rendered = builder.render_page(page, lines, {}) if "[^" not in text else builder.safe_html(text)
            generated.append(rendered.split('<div v-pre class="theory-source">\n\n', 1)[-1]
                             .removeprefix("# Sample {#part-title-None}\n").removesuffix("\n\n</div>\n"))
        module = (WEBSITE / "node_modules/vitepress/dist/node/index.js").as_uri()
        script = ("import { createMarkdownRenderer } from %s;\n"
                  "import { readFileSync } from 'node:fs';\n"
                  "const md = await createMarkdownRenderer(process.argv[1], {}, '/');\n"
                  "const baseline = await createMarkdownRenderer(process.argv[1], { html: false }, '/');\n"
                  # Formula braces are source text, not VitePress attributes;
                  # the generated edition must protect them from that extension.
                  "baseline.core.ruler.disable('curly_attributes');\n"
                  "const values = JSON.parse(readFileSync(0, 'utf8'));\n"
                  "console.log(JSON.stringify(values.map(([original, generated]) => "
                  "[baseline.render(original), md.render(generated)])));\n") % json.dumps(module)
        result = subprocess.run(["node", "--input-type=module", "-e", script, str(WEBSITE)],
                                input=json.dumps(list(zip(examples, generated))),
                                capture_output=True, text=True, encoding="utf-8", check=True)

        class VisibleText(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.parts = []

            def handle_data(self, data):
                self.parts.append(data)

        def visible(markup):
            parser = VisibleText()
            parser.feed(markup)
            return "".join(parser.parts).strip()

        outputs = json.loads(result.stdout)
        for original, (before, after) in zip(examples, outputs):
            self.assertEqual(visible(after), visible(before), original)
            self.assertNotIn("&amp;#95;", after, original)
        self.assertEqual(visible(outputs[0][1]), "x_{t+1}=x_t−k x_{t−d}")

    def test_unknown_english_footnote_fails_without_emitting_an_unresolved_reference(self):
        page = builder.Page("en/theory/sample.md", "Sample", 0, 2, None, 1)
        with self.assertRaisesRegex(ValueError, "Undefined translator notes"):
            builder.render_page(page, ["# Sample\n", "Text[^missing].\n"], {})

    def test_bilingual_build_is_reproducible_in_a_clean_directory(self):
        with tempfile.TemporaryDirectory(prefix="xikari-bilingual-") as directory:
            root = Path(directory)
            manifests = builder.build_all(root)
            self.assertEqual(set(manifests), {"zh", "en"})
            self.assertEqual(manifests["en"]["pages"], self.manifest["pages"])
            self.assertEqual(manifests["en"]["annotation_sections"], [])
            self.assertEqual((root / "public/downloads" / builder.EN_FILE).read_bytes(), self.raw)


if __name__ == "__main__":
    unittest.main()
