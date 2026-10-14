"""Verify the handbook preserves the selected theory and its reading locations."""

import hashlib
import html
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"
SPEC = importlib.util.spec_from_file_location("handbook_source", WEBSITE / "scripts/build_theory.py")
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


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
                body = generated.split('<div v-pre class="theory-source">\n\n', 1)[1].rsplit("\n\n</div>", 1)[0]
                recovered = []
                for line in body.splitlines():
                    match = re.match(r"^(#+) (.*?) \{#[^}]+\}$", line)
                    if match:
                        line = "#" * (len(match.group(1)) + page.level - 1) + " " + match.group(2)
                    line = html.unescape(line)
                    line = re.sub(r"\]\(/theory/[^)]*#(part_\d+)\)", r"](#\1)", line)
                    recovered.append(line)
                expected = "".join(self.lines[page.start:page.end]).rstrip().splitlines()
                self.assertEqual(recovered, expected)

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

    def test_missing_word_edition_requires_an_explicit_path(self):
        with tempfile.TemporaryDirectory(prefix="xikari-handbook-docx-") as directory:
            destination = Path(directory) / "site"
            with self.assertRaisesRegex(FileNotFoundError, r"--docx <path>"):
                builder.build(destination, self.source)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
