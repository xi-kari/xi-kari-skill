import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "evidence.py"
spec = importlib.util.spec_from_file_location("xikari_evidence", SCRIPT)
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.catalog = self.root / "work" / "materials.json"

    def tearDown(self):
        self.temp.cleanup()

    def command(self, *arguments):
        args = evidence.parser().parse_args(["--catalog", str(self.catalog), *map(str, arguments)])
        return evidence.run(args)

    def cli_command(self, *arguments, expected_exit=0):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--catalog", str(self.catalog), *map(str, arguments)],
            capture_output=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, expected_exit, result.stderr or result.stdout)
        return json.loads(result.stdout if expected_exit == 0 else result.stderr)

    def material(self, name="source.md", content="第一行\n第二行\n第三行\n"):
        path = self.root / name
        path.write_text(content, encoding="utf-8", newline="")
        return path

    def add(self, path, key="source", *args):
        return self.command("add", path, "--id", key, *args)

    def test_text_locator_and_selected_snapshot_do_not_copy_whole_source(self):
        path = self.material(content="不选中的私密材料\n必要材料\n末行\n")
        raw = path.read_bytes()
        self.add(path)
        self.assertNotIn("不选中的私密材料", self.catalog.read_text(encoding="utf-8"))
        result = self.command("show", "--id", "source", "--at", "L2:L3")
        self.assertEqual([u["locator"] for u in result["source_extracts"]], ["L2", "L3"])
        self.command("clip", "--id", "source", "--clip-id", "claim-1", "--at", "L2", "--claim", "作者判断", "--support", "只能支持这一材料中的陈述，不能推广到总体", "--assumption", "材料表述未遗漏例外")
        record = self.command("show", "--clip", "claim-1")["clip"]
        self.assertEqual(record["source_extracts"][0]["text"], "必要材料")
        self.assertEqual(record["author_statement"], "作者判断")
        self.assertNotIn("不选中的私密材料", self.catalog.read_text(encoding="utf-8"))
        self.assertEqual(path.read_bytes(), raw)

    def test_text_extraction_preserves_empty_lines_bom_and_whitespace(self):
        cases = [
            ("", []), ("\ufeff", []), ("text", ["text"]),
            (" \t ", [" \t "]), ("\ufeff \ttext \t", [" \ttext \t"]),
            ("a\ufeffb", ["a\ufeffb"]),
            ("\n", [""]), ("\r", [""]), ("\r\n", [""]),
            ("\n\n", ["", ""]), ("\r\r", ["", ""]), ("\r\n\r\n", ["", ""]),
            ("a\n", ["a"]), ("a\r", ["a"]), ("a\r\n", ["a"]),
            ("\n \t\r\nlast\r", ["", " \t", "last"]),
            ("a\r\nb\rc\n\n", ["a", "b", "c", ""]),
            ("a\n\rb", ["a", "", "b"]),
        ]
        for kind in ("txt", "md"):
            for text, expected in cases:
                with self.subTest(kind=kind, text=text):
                    units, _ = evidence.extract(text.encode("utf-8"), kind)
                    self.assertEqual(units, [{"locator": f"L{i}", "text": line, "location": {"line": i}}
                                             for i, line in enumerate(expected, 1)])

    def test_text_inline_separators_are_not_physical_line_endings(self):
        for kind in ("txt", "md"):
            for separator in ("\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"):
                for newline in ("\n", "\r\n", "\r"):
                    for terminated in (False, True):
                        with self.subTest(kind=kind, separator=separator, newline=newline, terminated=terminated):
                            expected = [f"{separator}needle{separator}middle{separator}", "", f"\t tail{separator} "]
                            text = "\ufeff" + newline.join(expected) + (newline if terminated else "")
                            units, _ = evidence.extract(text.encode("utf-8"), kind)
                            self.assertEqual(units, [{"locator": f"L{i}", "text": line, "location": {"line": i}}
                                                     for i, line in enumerate(expected, 1)])
                with self.subTest(kind=kind, separator_only=separator):
                    units, _ = evidence.extract(separator.encode("utf-8"), kind)
                    self.assertEqual(units, [{"locator": "L1", "text": separator, "location": {"line": 1}}])

    def test_text_cli_physical_locations_survive_search_show_and_clip(self):
        inline = "\v\f\x1c\x1d\x1e\x85\u2028\u2029"
        expected = [f"  needle first{inline} tail\t", "", "needle second\ufeffinside", "needle last  "]
        raw = ("\ufeff" + expected[0] + "\r\n\r" + expected[2] + "\n" + expected[3] + "\r\n").encode("utf-8")
        for kind in ("txt", "md"):
            with self.subTest(kind=kind):
                self.catalog = self.root / f"{kind}-catalog.json"
                path = self.root / f"physical.{kind}"
                path.write_bytes(raw)
                added = self.cli_command("add", path, "--id", "physical")
                before = self.catalog.read_bytes()
                found = self.cli_command("search", "needle", "--id", "physical")
                shown = self.cli_command("show", "--id", "physical", "--at", "L1:L4")
                self.assertEqual(self.catalog.read_bytes(), before)
                self.cli_command("clip", "--id", "physical", "--clip-id", "selected", "--at", "L1:L3", "--support", "Synthetic physical lines")
                after_clip = self.catalog.read_bytes()
                saved = self.cli_command("show", "--clip", "selected")
                self.assertEqual(self.catalog.read_bytes(), after_clip)
                self.assertEqual(path.read_bytes(), raw)
                expected_units = [{"locator": f"L{i}", "text": line, "location": {"line": i}} for i, line in enumerate(expected, 1)]
                self.assertEqual(shown["source_extracts"], expected_units)
                self.assertEqual([(u["locator"], u["text"]) for u in found["matches"]], [("L1", expected[0]), ("L3", expected[2]), ("L4", expected[3])])
                self.assertTrue(found["complete"])
                self.assertEqual(found["skipped_sources"], [])
                self.assertEqual(found["total_matches"], 3)
                self.assertEqual(added["source"]["unit_count"], 4)
                self.assertEqual(added["source"]["extraction"], "evidence.py/2")
                self.assertEqual(saved["clip"]["source_extracts"], expected_units[:3])
                self.assertEqual(saved["status"]["state"], "current")

    def test_text_old_extraction_requires_new_identity_and_preserves_old_snapshot(self):
        for kind in ("txt", "md"):
            for previous_extraction in ("evidence.py/1", None):
                with self.subTest(kind=kind, extraction=previous_extraction):
                    self.catalog = self.root / f"{kind}-{previous_extraction is None}.json"
                    path = self.material(f"previous.{kind}", "needle before\vneedle after\nneedle next\n")
                    raw = path.read_bytes()
                    self.add(path, "old")
                    self.command("clip", "--id", "old", "--clip-id", "saved", "--at", "L1", "--support", "Synthetic old snapshot")
                    catalog = json.loads(self.catalog.read_text(encoding="utf-8"))
                    catalog["sources"]["old"]["unit_count"] = 3
                    if previous_extraction is None:
                        catalog["sources"]["old"].pop("extraction")
                    else:
                        catalog["sources"]["old"]["extraction"] = previous_extraction
                    catalog["clips"]["saved"]["source_extracts"] = [{"locator": "L2", "text": "needle after", "location": {"line": 2}}]
                    self.catalog.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
                    before = self.catalog.read_bytes()
                    for arguments in [
                        ("show", "--id", "old", "--at", "L2"),
                        ("clip", "--id", "old", "--clip-id", "blocked", "--at", "L2", "--support", "Must not capture"),
                    ]:
                        with self.subTest(operation=arguments[0]):
                            with self.assertRaisesRegex(evidence.MaterialError, "提取.*新ID.*--supersedes old"):
                                self.command(*arguments)
                    found = self.command("search", "needle", "--id", "old")
                    with self.subTest(operation="search"):
                        self.assertFalse(found["complete"])
                        self.assertEqual(found["total_matches"], 0)
                        self.assertEqual([s["source_id"] for s in found["skipped_sources"]], ["old"])
                    saved = self.command("show", "--clip", "saved")
                    self.assertEqual(saved["clip"], catalog["clips"]["saved"])
                    self.assertEqual(saved["status"]["state"], "current")
                    with self.subTest(operation="read_only"):
                        self.assertEqual(self.catalog.read_bytes(), before)
                    added = self.add(path, "new", "--supersedes", "old")
                    shown = self.command("show", "--id", "new", "--at", "L1:L2")
                    current = json.loads(self.catalog.read_text(encoding="utf-8"))
                    self.assertEqual(current["sources"]["old"], catalog["sources"]["old"])
                    self.assertEqual(current["clips"]["saved"], catalog["clips"]["saved"])
                    self.assertEqual(path.read_bytes(), raw)
                    self.assertEqual(added["source"]["supersedes"], "old")
                    self.assertEqual(added["source"]["extraction"], "evidence.py/2")
                    self.assertEqual(added["source"]["unit_count"], 2)
                    self.assertEqual([(u["locator"], u["text"]) for u in shown["source_extracts"]], [("L1", "needle before\vneedle after"), ("L2", "needle next")])

    def test_csv_multiline_cells_preserve_record_and_physical_lines(self):
        path = self.material("table.csv", 'name,notes,value\r\nAlice,"first\r\nsecond, quoted ""word""",42\r\nBob,ok,7\r\n')
        self.add(path)
        result = self.command("show", "--id", "source", "--at", "R2C2")["source_extracts"][0]
        self.assertEqual(result["text"], 'first\r\nsecond, quoted "word"')
        self.assertEqual(result["location"], {"record": 2, "column": 2, "physical_lines": [2, 3]})
        row = self.command("show", "--id", "source", "--at", "R3")["source_extracts"]
        self.assertEqual([u["text"] for u in row], ["Bob", "ok", "7"])
        self.assertEqual(row[0]["location"]["physical_lines"], [4, 4])

    def test_csv_blank_record_and_formula_are_only_text(self):
        self.add(self.material("cells.csv", 'header\n\n"=2+3"\n'))
        self.assertEqual(self.command("show", "--id", "source", "--at", "R2")["source_extracts"][0]["text"], "")
        self.assertEqual(self.command("show", "--id", "source", "--at", "R3C1")["source_extracts"][0]["text"], "=2+3")

    def test_docx_keeps_interleaved_paragraph_table_nested_table_order(self):
        path = self.root / "document.docx"
        xml = '''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
          <w:p><w:r><w:t>开头</w:t></w:r></w:p>
          <w:tbl><w:tr><w:tc>
            <w:p><w:r><w:t>表格一</w:t><w:tab/><w:t>继续</w:t></w:r></w:p>
            <w:tbl><w:tr><w:tc><w:p><w:r><w:t>内嵌表</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
            <w:p><w:r><w:t>表格二</w:t></w:r></w:p>
          </w:tc><w:tc><w:p><w:r><w:t>第二格</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
          <w:sdt><w:sdtContent><w:p><w:r><w:t>中间</w:t></w:r></w:p></w:sdtContent></w:sdt>
          <w:p><w:r><w:t>结束</w:t></w:r><w:del><w:r><w:t>删除内容</w:t></w:r></w:del><w:r><w:drawing><w:txbxContent><w:p><w:r><w:t>文本框</w:t></w:r></w:p></w:txbxContent></w:drawing></w:r></w:p>
        </w:body></w:document>'''
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", xml)
        self.add(path)
        result = self.command("show", "--id", "source", "--at", "P1", "--at", "T1", "--at", "P2", "--at", "P3")
        units = result["source_extracts"]
        self.assertEqual([u["text"] for u in units], ["开头", "表格一\t继续", "内嵌表", "表格二", "第二格", "中间", "结束"])
        self.assertEqual(units[2]["locator"], "T1R1C1T1R1C1P1")
        self.assertEqual(units[3]["locator"], "T1R1C1P2")
        self.assertEqual([u["location"]["document_order"] for u in units], list(range(1, 8)))

    def test_invalid_materials_leave_no_catalog_or_work_directory(self):
        fixtures = [("bad.csv", b'a,"unfinished\n'), ("bad.docx", b"not a zip"), ("bad.txt", b"\xff\xfe"), ("bad.md", b"a\x00b"), ("bad.bin", b"unrecognised")]
        for name, data in fixtures:
            with self.subTest(name=name):
                path = self.root / name
                path.write_bytes(data)
                with self.assertRaises(evidence.MaterialError):
                    self.add(path)
                self.assertFalse(self.catalog.exists())
                self.assertFalse(self.catalog.parent.exists())
                self.assertEqual(path.read_bytes(), data)

    def test_docx_cli_reads_wrapped_rows_cells_and_nested_tables_in_order(self):
        path = self.root / "controls.docx"
        xml = '''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
          <w:p><w:r><w:t>needle intro</w:t></w:r></w:p>
          <w:tbl>
            <w:tr><w:tc><w:p><w:r><w:t>needle before</w:t></w:r></w:p></w:tc></w:tr>
            <w:sdt><w:sdtPr><w:alias w:val="needle metadata"/></w:sdtPr><w:sdtContent><w:tr>
              <w:tc>
                <w:p><w:r><w:t>needle row</w:t></w:r></w:p>
                <w:tbl><w:sdt><w:sdtContent><w:tr><w:sdt><w:sdtContent><w:tc>
                  <w:p><w:r><w:t>needle nested</w:t></w:r></w:p>
                </w:tc></w:sdtContent></w:sdt></w:tr></w:sdtContent></w:sdt></w:tbl>
                <w:p><w:r><w:t>needle after nested</w:t></w:r>
                  <w:del><w:r><w:t>needle deleted</w:t></w:r></w:del>
                  <w:r><w:drawing><w:txbxContent><w:p><w:r><w:t>needle textbox</w:t></w:r></w:p></w:txbxContent></w:drawing></w:r>
                </w:p>
              </w:tc>
              <w:sdt><w:sdtContent><w:tc><w:p><w:r><w:t>needle cell</w:t></w:r></w:p></w:tc></w:sdtContent></w:sdt>
            </w:tr></w:sdtContent></w:sdt>
            <w:tr><w:tc><w:p><w:r><w:t>needle after</w:t></w:r></w:p></w:tc></w:tr>
          </w:tbl>
        </w:body></w:document>'''
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", xml)
        raw = path.read_bytes()
        added = self.cli_command("add", path, "--id", "controls")
        catalog_before = self.catalog.read_bytes()
        found = self.cli_command("search", "needle", "--id", "controls")
        shown = self.cli_command("show", "--id", "controls", "--at", "P1", "--at", "T1")
        nested = self.cli_command("show", "--id", "controls", "--at", "T1R2C1T1")
        expected = [
            ("P1", "needle intro"),
            ("T1R1C1P1", "needle before"),
            ("T1R2C1P1", "needle row"),
            ("T1R2C1T1R1C1P1", "needle nested"),
            ("T1R2C1P2", "needle after nested"),
            ("T1R2C2P1", "needle cell"),
            ("T1R3C1P1", "needle after"),
        ]
        self.assertEqual(path.read_bytes(), raw)
        self.assertEqual(self.catalog.read_bytes(), catalog_before)
        self.assertEqual(added["source"]["unit_count"], len(expected))
        self.assertTrue(found["complete"])
        self.assertEqual(found["skipped_sources"], [])
        self.assertEqual(found["total_matches"], len(expected))
        self.assertEqual([(u["locator"], u["text"]) for u in found["matches"]], expected)
        self.assertEqual([(u["locator"], u["text"]) for u in shown["source_extracts"]], expected)
        self.assertEqual([u["location"]["document_order"] for u in shown["source_extracts"]], list(range(1, 8)))
        self.assertEqual([(u["locator"], u["text"]) for u in nested["source_extracts"]], [expected[3]])

    def test_docx_cli_excludes_move_origin_and_preserves_destination(self):
        path = self.root / "moved.docx"
        xml = '''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
          <w:p>
            <w:moveFromRangeStart w:id="1" w:name="move1"/>
            <w:moveFrom w:id="2" w:author="Synthetic"><w:r><w:t>needle moved text</w:t></w:r></w:moveFrom>
            <w:moveFromRangeEnd w:id="1"/>
          </w:p>
          <w:p>
            <w:moveToRangeStart w:id="3" w:name="move1"/>
            <w:moveTo w:id="4" w:author="Synthetic"><w:r><w:t>needle moved text</w:t></w:r></w:moveTo>
            <w:moveToRangeEnd w:id="3"/>
          </w:p>
        </w:body></w:document>'''
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", xml)
        raw = path.read_bytes()
        self.cli_command("add", path, "--id", "moved")
        found = self.cli_command("search", "needle", "--id", "moved")
        shown = self.cli_command("show", "--id", "moved", "--at", "P1", "--at", "P2")
        self.cli_command("clip", "--id", "moved", "--clip-id", "destination", "--at", "P2", "--support", "Synthetic destination only")
        saved = self.cli_command("show", "--clip", "destination")
        self.assertEqual(path.read_bytes(), raw)
        self.assertTrue(found["complete"])
        self.assertEqual(found["total_matches"], 1)
        self.assertEqual([u["locator"] for u in found["matches"]], ["P2"])
        self.assertEqual([(u["locator"], u["text"]) for u in shown["source_extracts"]], [("P1", ""), ("P2", "needle moved text")])
        self.assertEqual(saved["clip"]["source_extracts"], [shown["source_extracts"][1]])
        self.assertEqual(saved["status"]["state"], "current")

    def test_docx_cli_requires_new_registration_for_old_extraction_version(self):
        path = self.root / "previous.docx"
        xml = '''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
          <w:p><w:r><w:t>needle original</w:t></w:r></w:p>
        </w:body></w:document>'''
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", xml)
        raw = path.read_bytes()
        for index, previous_extraction in enumerate(("evidence.py/1", None)):
            with self.subTest(extraction=previous_extraction):
                self.catalog = self.root / f"catalog-{index}.json"
                self.cli_command("add", path, "--id", "old")
                self.cli_command("clip", "--id", "old", "--clip-id", "saved", "--at", "P1", "--support", "Synthetic snapshot")
                catalog = json.loads(self.catalog.read_text(encoding="utf-8"))
                if previous_extraction is None:
                    catalog["sources"]["old"].pop("extraction")
                else:
                    catalog["sources"]["old"]["extraction"] = previous_extraction
                self.catalog.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
                before = self.catalog.read_bytes()
                for arguments in [
                    ("show", "--id", "old", "--at", "P1"),
                    ("clip", "--id", "old", "--clip-id", "new-clip", "--at", "P1", "--support", "Must not capture"),
                ]:
                    rejected = self.cli_command(*arguments, expected_exit=2)
                    self.assertIn("提取", rejected["error"])
                    self.assertIn("新ID", rejected["error"])
                    self.assertIn("--supersedes old", rejected["error"])
                found = self.cli_command("search", "needle", "--id", "old")
                self.assertFalse(found["complete"])
                self.assertEqual(found["total_matches"], 0)
                self.assertEqual([s["source_id"] for s in found["skipped_sources"]], ["old"])
                saved = self.cli_command("show", "--clip", "saved")
                self.assertEqual(saved["clip"], catalog["clips"]["saved"])
                self.assertEqual(saved["status"]["state"], "current")
                self.assertEqual(self.catalog.read_bytes(), before)
                added = self.cli_command("add", path, "--id", "new", "--supersedes", "old")
                self.assertEqual(added["source"]["extraction"], "evidence.py/2")
                shown = self.cli_command("show", "--id", "new", "--at", "P1")
                self.assertEqual(shown["source_extracts"][0]["text"], "needle original")
                current = json.loads(self.catalog.read_text(encoding="utf-8"))
                self.assertEqual(current["sources"]["old"], catalog["sources"]["old"])
                self.assertEqual(current["clips"]["saved"], catalog["clips"]["saved"])
                self.assertEqual(path.read_bytes(), raw)

    def test_docx_cli_skips_deleted_cells_without_renumbering_storage_locators(self):
        path = self.root / "cell-revisions.docx"
        xml = '''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
          <w:tbl><w:tr>
            <w:tc><w:p><w:r><w:t>needle first</w:t></w:r></w:p></w:tc>
            <w:tc><w:tcPr><w:cellDel w:id="1" w:author="Synthetic"/></w:tcPr>
              <w:p><w:r><w:t>needle deleted cell</w:t></w:r></w:p>
              <w:tbl><w:tr><w:tc><w:p><w:r><w:t>needle deleted nested</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
              <w:p/>
            </w:tc>
            <w:tc><w:tcPr><w:cellIns w:id="2" w:author="Synthetic"/></w:tcPr>
              <w:p><w:r><w:t>needle inserted</w:t></w:r></w:p>
              <w:tbl><w:tr><w:tc><w:p><w:r><w:t>needle retained nested</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
              <w:p/>
            </w:tc>
            <w:sdt><w:sdtContent><w:tc><w:tcPr><w:cellDel w:id="3" w:author="Synthetic"/></w:tcPr>
              <w:p><w:r><w:t>needle wrapped deleted</w:t></w:r></w:p>
              <w:tbl><w:tr><w:tc><w:p><w:r><w:t>needle wrapped deleted nested</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
              <w:p/>
            </w:tc></w:sdtContent></w:sdt>
            <w:tc><w:p><w:r><w:t>needle last</w:t></w:r></w:p></w:tc>
            <w:tc><w:tcPr><w:tcPrChange w:id="5" w:author="Synthetic"><w:tcPr>
              <w:cellDel w:id="6" w:author="Synthetic"/>
            </w:tcPr></w:tcPrChange></w:tcPr><w:p><w:r><w:t>needle current history</w:t></w:r></w:p></w:tc>
          </w:tr><w:tr><w:trPr><w:del w:id="4" w:author="Synthetic"/></w:trPr>
            <w:tc><w:p><w:r><w:t>needle row content</w:t></w:r></w:p></w:tc>
          </w:tr></w:tbl>
        </w:body></w:document>'''
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", xml)
        raw = path.read_bytes()
        added = self.cli_command("add", path, "--id", "cells")
        catalog_before = self.catalog.read_bytes()
        found = self.cli_command("search", "needle", "--id", "cells")
        shown = self.cli_command("show", "--id", "cells", "--at", "T1")
        expected = [
            ("T1R1C1P1", "needle first"),
            ("T1R1C3P1", "needle inserted"),
            ("T1R1C3T1R1C1P1", "needle retained nested"),
            ("T1R1C5P1", "needle last"),
            ("T1R1C6P1", "needle current history"),
            ("T1R2C1P1", "needle row content"),
        ]
        self.assertEqual(found["total_matches"], len(expected))
        self.assertTrue(found["complete"])
        self.assertEqual([(u["locator"], u["text"]) for u in found["matches"]], expected)
        self.assertEqual([(u["locator"], u["text"]) for u in shown["source_extracts"] if u["text"]], expected)
        self.assertEqual(added["source"]["unit_count"], len(expected) + 1)
        self.assertIn("不重建全部结构修订", " ".join(shown["extraction_limits"]))
        for locator in ("T1R1C2", "T1R1C2T1", "T1R1C4", "T1R1C4T1"):
            rejected = self.cli_command("show", "--id", "cells", "--at", locator, expected_exit=2)
            self.assertIn("定位不存在", rejected["error"])
        self.assertEqual(self.catalog.read_bytes(), catalog_before)
        self.assertEqual(path.read_bytes(), raw)

    def test_text_and_csv_registration_use_their_format_extraction_versions(self):
        for name, locator, version in (("plain.txt", "L1", "evidence.py/2"), ("markdown.md", "L1", "evidence.py/2"), ("table.csv", "R1C1", "evidence.py/1")):
            with self.subTest(name=name):
                path = self.material(name, "needle original\n")
                raw = path.read_bytes()
                source_id = path.stem
                added = self.cli_command("add", path, "--id", source_id)
                self.assertEqual(added["source"]["extraction"], version)
                found = self.cli_command("search", "needle", "--id", source_id)
                self.assertTrue(found["complete"])
                self.assertEqual(found["total_matches"], 1)
                shown = self.cli_command("show", "--id", source_id, "--at", locator)
                self.assertEqual(shown["source_extracts"][0]["text"], "needle original")
                self.assertEqual(path.read_bytes(), raw)

    def test_csv_and_pdf_live_extraction_remains_compatible_without_version(self):
        page = mock.Mock()
        page.extract_text.return_value = "needle original"
        reader = mock.Mock(is_encrypted=False, pages=[page])
        with mock.patch.dict(sys.modules, {"pypdf": mock.Mock(PdfReader=mock.Mock(return_value=reader))}):
            for kind, locator in (("csv", "R1C1"), ("pdf", "PDF1")):
                for remove_version in (False, True):
                    with self.subTest(kind=kind, remove_version=remove_version):
                        self.catalog = self.root / f"compatible-{kind}-{remove_version}.json"
                        path = self.material(f"compatible.{kind}", "needle original\n")
                        raw = path.read_bytes()
                        added = self.add(path)
                        self.assertEqual(added["source"]["extraction"], "evidence.py/1")
                        if remove_version:
                            catalog = json.loads(self.catalog.read_text(encoding="utf-8"))
                            catalog["sources"]["source"].pop("extraction")
                            self.catalog.write_text(json.dumps(catalog), encoding="utf-8")
                        before = self.catalog.read_bytes()
                        found = self.command("search", "needle", "--id", "source")
                        shown = self.command("show", "--id", "source", "--at", locator)
                        self.assertTrue(found["complete"])
                        self.assertEqual(found["total_matches"], 1)
                        self.assertEqual(found["skipped_sources"], [])
                        self.assertEqual(shown["source_extracts"][0]["text"], "needle original")
                        self.assertEqual(self.catalog.read_bytes(), before)
                        self.command("clip", "--id", "source", "--clip-id", "saved", "--at", locator, "--support", "Synthetic compatible format")
                        self.assertEqual(self.command("show", "--clip", "saved")["clip"]["source_extracts"], shown["source_extracts"])
                        self.assertEqual(path.read_bytes(), raw)

    def test_source_changed_old_clip_retained_and_new_identity_registered(self):
        path = self.material(content="原来的判断\n")
        old = self.add(path)["source"]
        self.command("clip", "--id", "source", "--clip-id", "old", "--at", "L1", "--support", "原版本原话")
        path.write_text("修订后的判断\n", encoding="utf-8")
        with self.assertRaisesRegex(evidence.MaterialError, "内容已变化"):
            self.command("show", "--id", "source", "--at", "L1")
        result = self.command("search", "判断")
        self.assertFalse(result["complete"])
        self.assertEqual(result["total_matches"], 0)
        self.assertEqual(len(result["skipped_sources"]), 1)
        snapshot = self.command("show", "--clip", "old")
        self.assertEqual(snapshot["status"]["state"], "changed")
        self.assertEqual(snapshot["clip"]["source_extracts"][0]["text"], "原来的判断")
        new = self.add(path, "source-v2", "--supersedes", "source")["source"]
        self.assertNotEqual(new["sha256"], old["sha256"])
        self.assertEqual(self.command("show", "--id", "source")["source"]["sha256"], old["sha256"])
        self.assertEqual(self.command("show", "--id", "source-v2")["status"]["state"], "current")

    def test_missing_original_does_not_destroy_preserved_clip(self):
        path = self.material()
        self.add(path)
        self.command("clip", "--id", "source", "--clip-id", "saved", "--at", "L1", "--support", "有限支持")
        path.unlink()
        result = self.command("show", "--clip", "saved")
        self.assertEqual(result["status"]["state"], "missing")
        self.assertEqual(result["clip"]["source_extracts"][0]["text"], "第一行")

    def test_duplicate_ids_unknown_sources_and_invalid_locators_do_not_change_catalog(self):
        path = self.material()
        self.add(path)
        before = self.catalog.read_bytes()
        commands = [
            ("add", path, "--id", "source"),
            ("add", path, "--id", "new", "--supersedes", "missing"),
            ("show", "--id", "missing"),
            ("show", "--clip", "missing"),
            ("show", "--id", "source", "--at", "L1:L999999999999"),
            ("clip", "--id", "source", "--clip-id", "bad", "--at", "L5", "--support", "none"),
        ]
        for command in commands:
            with self.subTest(command=command):
                with self.assertRaises(evidence.MaterialError):
                    self.command(*command)
                self.assertEqual(self.catalog.read_bytes(), before)
        self.command("clip", "--id", "source", "--clip-id", "one", "--at", "L1", "--support", "有限支持")
        before = self.catalog.read_bytes()
        with self.assertRaisesRegex(evidence.MaterialError, "片段ID已存在"):
            self.command("clip", "--id", "source", "--clip-id", "one", "--at", "L2", "--support", "新内容")
        self.assertEqual(self.catalog.read_bytes(), before)

    def test_original_and_arbitrary_catalog_cannot_be_overwritten(self):
        path = self.material()
        self.catalog = path
        before = path.read_bytes()
        with self.assertRaisesRegex(evidence.MaterialError, "与原始材料相同"):
            self.add(path)
        self.assertEqual(path.read_bytes(), before)
        other = self.material("other.txt")
        with self.assertRaises(evidence.MaterialError):
            self.add(other)
        self.assertEqual(path.read_bytes(), before)

    def test_source_cannot_be_lock_file_and_active_lock_is_preserved(self):
        lock = self.catalog.with_name(self.catalog.name + ".lock")
        lock.parent.mkdir()
        lock.write_text("用户原件", encoding="utf-8")
        with self.assertRaisesRegex(evidence.MaterialError, "与原始材料相同"):
            self.add(lock, "lock", "--type", "txt")
        path = self.material()
        with self.assertRaisesRegex(evidence.MaterialError, "正在写入"):
            self.add(path)
        self.assertEqual(lock.read_text(encoding="utf-8"), "用户原件")
        self.assertFalse(self.catalog.exists())

    def test_source_symlink_cannot_alias_catalog(self):
        path = self.material()
        alias = self.root / "alias.txt"
        try:
            alias.symlink_to(path)
        except OSError:
            self.skipTest("此Windows运行环境不允许创建符号链接")
        self.catalog = alias
        before = path.read_bytes()
        with self.assertRaises(evidence.MaterialError):
            self.add(path)
        self.assertEqual(path.read_bytes(), before)

    def test_host_extraction_requires_honest_origin_mapping(self):
        path = self.material()
        with self.assertRaisesRegex(evidence.MaterialError, "locator-note"):
            self.add(path, "web", "--origin", "https://example.invalid/material")
        result = self.add(path, "web", "--origin", "https://example.invalid/material", "--source-date", "日期未知", "--locator-note", "宿主提取正文；L是副本行号，原页以标题和原句定位")
        self.assertEqual(result["source"]["source_date"], "日期未知")
        self.assertIn("example.invalid", result["source"]["origin"])

    def test_pdf_missing_dependency_and_empty_extraction_are_explicit(self):
        with mock.patch.dict(sys.modules, {"pypdf": None}):
            with self.assertRaisesRegex(evidence.MaterialError, "宿主现有PDF工具"):
                evidence.extract(b"not used", "pdf")
        empty_page = mock.Mock()
        empty_page.extract_text.return_value = ""
        fake_reader = mock.Mock(is_encrypted=False, pages=[empty_page])
        with mock.patch.dict(sys.modules, {"pypdf": mock.Mock(PdfReader=mock.Mock(return_value=fake_reader))}):
            with self.assertRaisesRegex(evidence.MaterialError, "扫描页"):
                evidence.extract(b"not used", "pdf")

    def test_pdf_page_number_is_not_printed_page_and_empty_pages_warn(self):
        page1, page2 = mock.Mock(), mock.Mock()
        page1.extract_text.return_value = "有文字的页"
        page2.extract_text.return_value = ""
        fake_reader = mock.Mock(is_encrypted=False, pages=[page1, page2])
        with mock.patch.dict(sys.modules, {"pypdf": mock.Mock(PdfReader=mock.Mock(return_value=fake_reader))}):
            units, warnings = evidence.extract(b"not used", "pdf")
        self.assertEqual(units[0]["locator"], "PDF1")
        self.assertEqual(units[0]["location"]["page"], 1)
        self.assertIn("2", warnings[1])

    def test_real_pdf_text_layer_when_optional_dependency_available(self):
        try:
            from pypdf import PdfWriter
            from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
        except ImportError:
            self.skipTest("可选pypdf未安装；缺依赖和空提取行为由独立测试覆盖")
        path = self.root / "actual.pdf"
        writer = PdfWriter()
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})})
        stream = DecodedStreamObject()
        stream.set_data(b"BT /F1 12 Tf 72 720 Td (Actual PDF excerpt) Tj ET")
        page[NameObject("/Contents")] = stream
        with path.open("wb") as output:
            writer.write(output)
        self.add(path)
        result = self.command("show", "--id", "source", "--at", "PDF1")
        self.assertIn("Actual PDF excerpt", result["source_extracts"][0]["text"])

    def test_cli_json_and_failure_exit(self):
        path = self.material()
        result = subprocess.run([sys.executable, str(SCRIPT), "--catalog", str(self.catalog), "add", str(path), "--id", "source"], capture_output=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["source"]["id"], "source")
        result = subprocess.run([sys.executable, str(SCRIPT), "--catalog", str(self.catalog), "show", "--id", "missing"], capture_output=True, encoding="utf-8")
        self.assertEqual(result.returncode, 2)
        self.assertIn("未知材料ID", json.loads(result.stderr)["error"])
        self.assertFalse(result.stdout)


if __name__ == "__main__":
    unittest.main()
