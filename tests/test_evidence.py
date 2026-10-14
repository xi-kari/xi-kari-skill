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
