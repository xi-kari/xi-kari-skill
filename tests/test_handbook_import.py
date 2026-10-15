import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile


SCRIPT = Path(__file__).resolve().parents[1] / "website/scripts/import_reading_packages.py"
SPEC = importlib.util.spec_from_file_location("import_reading_packages", SCRIPT)
importer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(importer)


class ReadingPackageImportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repository = self.root / "repository"
        self.packages = self.root / "packages"
        self.report = self.root / "reports"
        self.packages.mkdir()
        (self.repository / "source").mkdir(parents=True)
        (self.repository / "website/content").mkdir(parents=True)
        self.theory = "# 标题\n第一节。\n## 第二节\n正文。\n".encode("utf-8")
        self.source_hash = importer.sha256(self.theory)
        (self.repository / "source/Xikari-条件结构与转化论.md").write_bytes(self.theory)
        self.units = [
            {"lesson_key": "1.1", "task_id": "S-1-1", "output_id": "section-1-1", "source_start_line": 1, "source_end_line": 4, "source_sha256": self.source_hash}
        ]
        (self.repository / "website/content/reading-units.json").write_bytes(importer.json_bytes({
            "source_sha256": self.source_hash, "source_lines": 4, "units": self.units,
        }))
        self.lesson = {
            "title": "第一节", "lead": "解释", "explanation": ["解释正文。"],
            "sourceHash": self.source_hash, "outputId": "section-1-1",
            "sourceRefs": [{"section": "1.1", "start_line": 1, "end_line": 4}],
            "diagramPath": "figures/test.png",
            "figures": [{"path": "figures/test.png", "alt": "示意图", "caption": "教学构造"}],
            "caseLinks": [{"title": "来源", "href": "https://example.org/case"}],
            "caseNotes": [],
            "teachingExamples": [{"title": "教学例", "text": "完整教学内容", "assumptions": "已知条件", "boundary": "边界"}],
            "extension": {"arbitrary": "尚未有专门渲染器的字段也要保留"},
        }
        self.source = {"id": "theory", "title": "原文", "url": "source/theory.md", "locator": "第1—4行"}

    def make_package(self, name="unrelated-filename.zip", lesson=None, extra=None):
        payload = {
            "S-1-1/sections.json": importer.json_bytes({"taskId": "S-1-1", "sourceSha256": self.source_hash, "lessons": {"1.1": lesson or self.lesson}}),
            "S-1-1/source/theory.md": self.theory,
            "S-1-1/source-slice.md": self.theory,
            "S-1-1/sources.json": importer.json_bytes({"sources": [self.source]}),
            "S-1-1/lecture.md": "# 讲解\n\n![示意](figures/test.png)\n\n[原文](source/theory.md)\n".encode("utf-8"),
            "S-1-1/diagrams.md": "![图](figures/test.png)".encode("utf-8"),
            "S-1-1/figures/test.png": b"\x89PNG\r\n\x1a\nfixture",
            "S-1-1/status.json": b'{"complete":true}',
            "S-1-1/scripts/never_run.py": b'raise RuntimeError("Do not run package code")',
        }
        payload.update(extra or {})
        path = self.packages / name
        with zipfile.ZipFile(path, "w") as archive:
            for key, value in payload.items():
                archive.writestr(key, value)
        return path

    def run_import(self):
        return importer.import_packages(self.packages, self.repository, self.report)

    def test_import_uses_manifest_identity_and_preserves_content(self):
        self.make_package()
        result = self.run_import()
        output = json.loads((self.repository / "website/content/section-lessons.json").read_text(encoding="utf-8"))["lessons"]["1.1"]
        self.assertEqual(result["lesson_count"], 1)
        self.assertEqual(output["extension"], self.lesson["extension"])
        self.assertEqual(output["teachingExamples"], self.lesson["teachingExamples"])
        self.assertEqual(output["sourceRefs"][0]["start_line"], 1)
        self.assertEqual(output["sourceRefs"][0]["startLine"], 1)
        self.assertEqual(output["sources"][0]["url"], "/reading-assets/theory.md")
        self.assertEqual(output["figures"][0]["path"], "/reading-assets/S-1-1/figures/test.png")
        public = self.repository / "website/public/reading-assets"
        lecture = (public / "S-1-1/lecture.md").read_text(encoding="utf-8")
        self.assertIn("](/reading-assets/S-1-1/figures/test.png)", lecture)
        self.assertFalse((public / "S-1-1/status.json").exists())
        self.assertFalse((public / "S-1-1/scripts/never_run.py").exists())

    def test_identical_duplicate_is_imported_once(self):
        self.make_package("one.zip")
        self.make_package("two.zip")
        result = self.run_import()
        self.assertEqual(result["task_count"], 1)
        self.assertEqual(len(result["duplicates"]), 1)

    def test_conflicting_duplicate_supplement_rejects_all_public_writes(self):
        self.make_package("one.zip")
        self.make_package("two.zip", extra={"S-1-1/lecture.md": b"Different substantive report"})
        with self.assertRaises(importer.ImportValidationError):
            self.run_import()
        self.assertFalse((self.repository / "website/public/reading-assets").exists())
        self.assertFalse((self.repository / "website/content/section-lessons.json").exists())

    def test_declared_completion_does_not_override_wrong_source_bytes(self):
        self.make_package(extra={"S-1-1/source/theory.md": b"Wrong version"})
        with self.assertRaises(importer.ImportValidationError):
            self.run_import()

    def test_wrong_unit_range_rejected(self):
        lesson = copy.deepcopy(self.lesson)
        lesson["sourceRefs"][0]["end_line"] = 3
        self.make_package(lesson=lesson)
        with self.assertRaises(importer.ImportValidationError):
            self.run_import()

    def test_unsafe_unreferenced_member_rejects_archive(self):
        self.make_package(extra={"../outside.txt": b"Never extract"})
        with self.assertRaises(importer.ImportValidationError):
            self.run_import()
        self.assertFalse((self.root / "outside.txt").exists())

    def test_missing_image_rejected(self):
        lesson = copy.deepcopy(self.lesson)
        lesson["figures"][0]["path"] = "figures/not-there.png"
        self.make_package(lesson=lesson)
        with self.assertRaises(importer.ImportValidationError):
            self.run_import()

    def test_entire_missing_task_rejected(self):
        with self.assertRaises(importer.ImportValidationError):
            self.run_import()
        report = json.loads((self.report / "import-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(report["errors"][0]["missing_units"], ["1.1"])

    def test_unsafe_source_link_rejected(self):
        self.source["url"] = "javascript:alert(1)"
        self.make_package()
        with self.assertRaises(importer.ImportValidationError):
            self.run_import()


if __name__ == "__main__":
    unittest.main()
