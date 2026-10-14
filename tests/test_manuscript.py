"""Observable file protection, merge behavior, and explicit dependency traversal."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "manuscript.py"
SPEC = importlib.util.spec_from_file_location("manuscript", SCRIPT)
manuscript = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = manuscript
SPEC.loader.exec_module(manuscript)


class TextMergeTests(unittest.TestCase):
    def test_independent_edits_and_shared_change(self):
        base = "题目\n第一段\n第二段\n第三段\n"
        current = "新题目\n用户改第一段\n第二段\n第三段\n"
        candidate = "新题目\n第一段\n第二段\n模型改第三段\n"
        # Adjacent shared and separate changes can be represented as overlapping
        # diff hunks; conservatively keep those for human integration.
        merged, conflicts = manuscript.merge_text(base, current, candidate)
        self.assertIsNone(merged)
        self.assertTrue(conflicts)

    def test_parallel_nonoverlapping_edits(self):
        merged, conflicts = manuscript.merge_text(
            "标题\n甲\n乙\n丙\n", "标题\n甲改\n乙\n丙\n", "标题\n甲\n乙\n丙改\n"
        )
        self.assertEqual(merged, "标题\n甲改\n乙\n丙改\n")
        self.assertEqual(conflicts, [])

    def test_adjacent_line_replacements_merge(self):
        merged, conflicts = manuscript.merge_text("a\nb\n", "A\nb\n", "a\nB\n")
        self.assertEqual(merged, "A\nB\n")
        self.assertEqual(conflicts, [])

    def test_identical_edits_are_kept_once(self):
        base = "a\nseparator\nc\nseparator2\ne\n"
        current = "A\nseparator\nC\nseparator2\ne\n"
        candidate = "a\nseparator\nC\nseparator2\nE\n"
        merged, conflicts = manuscript.merge_text(base, current, candidate)
        self.assertEqual(merged, "A\nseparator\nC\nseparator2\nE\n")
        self.assertEqual(conflicts, [])

    def test_identical_versions(self):
        self.assertEqual(manuscript.merge_text("old", "新稿", "新稿"), ("新稿", []))

    def test_one_unchanged_side(self):
        self.assertEqual(manuscript.merge_text("base", "base", "candidate"), ("candidate", []))
        self.assertEqual(manuscript.merge_text("base", "current", "base"), ("current", []))

    def test_conflicting_same_line_changes(self):
        merged, conflicts = manuscript.merge_text("a\nb\n", "a\nuser\n", "a\nmodel\n")
        self.assertIsNone(merged)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["base_start_line"], 2)
        self.assertEqual(conflicts[0]["current_edit"]["replacement"], "user\n")

    def test_overlapping_deletion_and_modification(self):
        merged, conflicts = manuscript.merge_text("a\nb\nc\n", "a\n", "a\nb\nC\n")
        self.assertIsNone(merged)
        self.assertTrue(conflicts)

    def test_different_insertions_at_same_position_conflict(self):
        merged, conflicts = manuscript.merge_text("a\nb\n", "a\nuser\nb\n", "a\nmodel\nb\n")
        self.assertIsNone(merged)
        self.assertTrue(conflicts)

    def test_identical_insertions(self):
        result = manuscript.merge_text("a\nb\n", "a\nnew\nb\n", "a\nnew\nb\n")
        self.assertEqual(result, ("a\nnew\nb\n", []))

    def test_insertion_on_changed_boundary_conflicts(self):
        merged, conflicts = manuscript.merge_text("a\nb\nc\n", "a\nB\nc\n", "a\nb\ninsert\nc\n")
        self.assertIsNone(merged)
        self.assertTrue(conflicts)

    def test_empty_base_with_conflicting_new_text(self):
        merged, conflicts = manuscript.merge_text("", "user", "model")
        self.assertIsNone(merged)
        self.assertTrue(conflicts)

    def test_bom_crlf_unicode_and_no_final_newline(self):
        merged, conflicts = manuscript.merge_text(
            "\ufeff标题\r\n甲\r\n乙\r\n丙", "\ufeff标题\r\n甲改\r\n乙\r\n丙",
            "\ufeff标题\r\n甲\r\n乙\r\n丙改"
        )
        self.assertEqual(merged.encode("utf-8"), "\ufeff标题\r\n甲改\r\n乙\r\n丙改".encode("utf-8"))
        self.assertEqual(conflicts, [])


class TemporaryFiles(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def file(self, name, content):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
        return target

    def trio(self):
        return self.file("base.md", "a\nb\nc\n"), self.file("current.md", "A\nb\nc\n"), self.file("candidate.md", "a\nb\nC\n")


class FileTests(TemporaryFiles):
    def test_merge_never_changes_inputs(self):
        inputs = self.trio()
        before = [path.read_bytes() for path in inputs]
        output = self.root / "merged.md"
        result = manuscript.merge(*inputs, output)
        self.assertEqual(result["status"], "merged")
        self.assertEqual(output.read_bytes(), b"A\nb\nC\n")
        self.assertEqual([path.read_bytes() for path in inputs], before)

    def test_existing_output_and_input_as_output_rejected(self):
        inputs = self.trio()
        existing = self.file("existing.md", "DO NOT CHANGE")
        for output in (existing, inputs[1]):
            before = output.read_bytes()
            with self.assertRaises(ValueError):
                manuscript.merge(*inputs, output)
            self.assertEqual(output.read_bytes(), before)

    def test_conflicts_do_not_write_manuscript(self):
        base, current, candidate = self.trio()
        candidate.write_bytes(b"OTHER\nb\nc\n")
        output, conflicts = self.root / "merged.md", self.root / "conflicts.json"
        result = manuscript.merge(base, current, candidate, output, conflicts)
        self.assertEqual(result["status"], "conflict")
        self.assertFalse(output.exists())
        self.assertFalse(json.loads(conflicts.read_text(encoding="utf-8"))["merged_output_written"])

    def test_conflict_report_cannot_overwrite_or_mimic_output(self):
        inputs = self.trio()
        output = self.root / "merged.md"
        existing = self.file("report.json", "original")
        for report in (existing, output, inputs[0]):
            with self.assertRaises(ValueError):
                manuscript.merge(*inputs, output, report)
        self.assertFalse(output.exists())
        self.assertEqual(existing.read_text(), "original")

    def test_snapshot_selected_files_and_relative_assets_only(self):
        source = self.root / "project"
        self.file("project/正文.md", b"\xef\xbb\xbftext\r\n")
        self.file("project/images/plot.svg", "<svg/>\n")
        self.file("project/unselected.md", "private")
        output = self.root / "branch"
        result = manuscript.snapshot(source, ["正文.md", "images/plot.svg"], output)
        self.assertEqual(result["files"], 2)
        self.assertEqual((output / "正文.md").read_bytes(), (source / "正文.md").read_bytes())
        self.assertEqual((output / "images/plot.svg").read_bytes(), b"<svg/>\n")
        self.assertFalse((output / "unselected.md").exists())
        self.assertTrue((output / manuscript.SNAPSHOT_INDEX).is_file())

    def test_snapshot_rejects_existing_destination(self):
        self.file("正文.md", "original")
        target = self.root / "branch"
        target.mkdir()
        sentinel = target / "user.txt"
        sentinel.write_text("user")
        with self.assertRaises(ValueError):
            manuscript.snapshot(self.root, ["正文.md"], target)
        self.assertEqual(sentinel.read_text(), "user")

    def test_snapshot_rejects_path_escape_missing_and_duplicates(self):
        source = self.root / "project"
        self.file("project/a.md", "a")
        self.file("outside.md", "outside")
        for selected in (["../outside.md"], [str(self.root / "outside.md")], ["a.md", "a.md"], ["missing.md"]):
            with self.assertRaises((ValueError, FileNotFoundError)):
                manuscript.snapshot(source, selected, self.root / "branch")
            self.assertFalse((self.root / "branch").exists())

    def test_compare_contains_changes_and_missing_newline_marker(self):
        current, candidate = self.file("current.md", "旧"), self.file("candidate.md", "新")
        output = self.root / "comparison.diff"
        manuscript.compare(current, candidate, output)
        value = output.read_text(encoding="utf-8")
        self.assertIn("-旧\n", value)
        self.assertIn("+新\n", value)
        self.assertEqual(value.count("\\ No newline at end of file"), 2)
        with self.assertRaises(ValueError):
            manuscript.compare(current, candidate, output)

    def test_invalid_utf8_fails_without_output(self):
        inputs = list(self.trio())
        inputs[0].write_bytes(b"\xff")
        output = self.root / "merged.md"
        with self.assertRaises(UnicodeDecodeError):
            manuscript.merge(*inputs, output)
        self.assertFalse(output.exists())

    def test_cli_conflict_exit_code(self):
        base, current, candidate = self.trio()
        candidate.write_bytes(b"OTHER\nb\nc\n")
        output = self.root / "merged.md"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "merge", "--base", str(base), "--current", str(current),
             "--candidate", str(candidate), "--output", str(output)], capture_output=True, encoding="utf-8"
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "conflict")
        self.assertFalse(output.exists())


class DependencyTests(TemporaryFiles):
    def graph(self, nodes, links):
        document = {
            "nodes": [{"id": key, "label": key, "location": {"path": "xi-kari-answer.md", "heading": key}} for key in nodes],
            "links": [{"source": left, "dependent": right} for left, right in links],
        }
        return self.file("links.json", json.dumps(document))

    def test_transitive_cycle_terminates_and_unrelated_node_omitted(self):
        path = self.graph(["A", "B", "C", "D"], [("A", "B"), ("B", "C"), ("C", "A")])
        result = manuscript.affected(path, ["A"])
        self.assertEqual([node["id"] for node in result["affected"]], ["B", "C"])
        self.assertEqual(result["affected"][1]["reached_by"][0]["path"], ["A", "B", "C"])

    def test_multiple_origins_and_duplicate_links(self):
        path = self.graph(["A", "B", "C", "D"], [("A", "C"), ("B", "C"), ("A", "C"), ("C", "D")])
        result = manuscript.affected(path, ["A", "B", "A"])
        self.assertEqual([node["id"] for node in result["changed"]], ["A", "B"])
        self.assertEqual(len(result["affected"]), 2)
        self.assertEqual([row["changed"] for row in result["affected"][1]["reached_by"]], ["A", "B"])

    def test_self_loop(self):
        path = self.graph(["A"], [("A", "A")])
        self.assertEqual(manuscript.affected(path, ["A"])["affected"], [])

    def test_unknown_edge_endpoint_and_changed_id_rejected(self):
        path = self.graph(["A"], [("A", "missing")])
        with self.assertRaises(ValueError):
            manuscript.affected(path, ["A"])
        path = self.graph(["A"], [])
        with self.assertRaises(ValueError):
            manuscript.affected(path, ["missing"])

    def test_duplicate_node_and_bad_locator_rejected(self):
        path = self.graph(["A", "A"], [])
        with self.assertRaises(ValueError):
            manuscript.affected(path, ["A"])
        for location in ({}, {"path": "a.md", "line": 0}, {"path": "a.md", "line": True}):
            path = self.file("links.json", json.dumps({"nodes": [{"id": "A", "location": location}], "links": []}))
            with self.assertRaises(ValueError):
                manuscript.affected(path, ["A"])


if __name__ == "__main__":
    unittest.main()
