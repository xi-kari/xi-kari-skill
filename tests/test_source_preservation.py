from __future__ import annotations

import importlib.util
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load_checker():
    path = ROOT / "scripts" / "verify_source_preservation.py"
    assert path.is_file(), "source migration needs a unit-exact preservation checker"
    spec = importlib.util.spec_from_file_location("verify_source_preservation", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def units(text="完整定义；反例与限定必须保留", marker="1."):
    return {"paragraphs": [{"ordinal": 1, "text": text, "style": "Body", "numbering": {"rendered_marker": marker}}], "tables": [{"ordinal": 1, "cell_paragraph_ordinals": [[[1]]]}]}


def test_preservation_rejects_unapproved_shortening():
    assert load_checker().compare_units(units(), units("完整定义"), {})


def test_preservation_rejects_deleted_paragraph_and_list_structure():
    checker = load_checker()
    assert checker.compare_units(units(), {"paragraphs": [], "tables": []}, {})
    assert checker.compare_units(units(), units(marker=""), {})


def test_preservation_accepts_only_exact_approved_replacement():
    checker = load_checker()
    approval = {1: {"before": units()["paragraphs"][0]["text"], "after": "完整定义；明确推荐与执行的区别", "category": "normative_opinion"}}
    assert checker.compare_units(units(), units(approval[1]["after"]), approval) == []
    assert checker.compare_units(units(), units("完整定义；另一个未批准的版本"), approval)


def test_current_source_is_complete_successor():
    from build_source_snapshot import extract_snapshot
    current = ROOT / "source" / "跨尺度多圈层结构推演框架v8.3.docx"
    assert current.is_file(), "the successor must be a complete authoritative DOCX"
    snapshot = extract_snapshot(current.read_bytes())
    assert len(snapshot.paragraphs) == 4631
    assert len(snapshot.tables) == 122
    assert sum(p.numbering is not None for p in snapshot.paragraphs) == 162
    assert snapshot.paragraphs[1].text == "v8.3"
    assert "不以缺失数量" in snapshot.paragraphs[2844].text


def rewrite_docx(source, *, updates=None, removed=()):
    output = BytesIO()
    updates = dict(updates or {})
    with ZipFile(BytesIO(source)) as original, ZipFile(output, "w") as result:
        for member in original.infolist():
            if member.filename not in removed:
                result.writestr(member, updates.pop(member.filename, original.read(member)))
        for name, payload in updates.items():
            result.writestr(name, payload)
    return output.getvalue()


def check_files(tmp_path, baseline, current, **approval_fields):
    before = tmp_path / "baseline.docx"
    after = tmp_path / "current.docx"
    approved = tmp_path / "approved.json"
    before.write_bytes(baseline)
    after.write_bytes(current)
    approval = {
        "baseline_raw_sha256": sha256(baseline).hexdigest(),
        "current_raw_sha256": sha256(current).hexdigest(),
        "changes": [],
        "version_metadata_members": [],
        **approval_fields,
    }
    approved.write_text(json.dumps(approval), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_source_preservation.py"),
         "--baseline", str(before), "--current", str(after),
         "--approved-changes", str(approved)],
        capture_output=True, text=True, encoding="utf-8", check=False,
    )
    assert before.read_bytes() == baseline
    assert after.read_bytes() == current
    assert json.loads(approved.read_text(encoding="utf-8")) == approval
    return result


@pytest.fixture
def current_docx():
    return (ROOT / "source/跨尺度多圈层结构推演框架v8.3.docx").read_bytes()


@pytest.mark.parametrize("field", ["baseline_raw_sha256", "current_raw_sha256"])
def test_preservation_rejects_approval_hash_mismatch(tmp_path, current_docx, field):
    result = check_files(tmp_path, current_docx, current_docx, **{field: "0" * 64})
    assert result.returncode == 1, result.stdout
    assert field in result.stdout


@pytest.mark.parametrize("member", ["word/header3.xml", "docProps/core.xml", "word/styles.xml"])
def test_preservation_rejects_unapproved_nonbody_change(tmp_path, current_docx, member):
    with ZipFile(BytesIO(current_docx)) as original:
        payload = original.read(member).replace(b"v8.3", b"UNAPPROVED SOURCE CHANGE")
        if payload == original.read(member):
            payload += b"<!-- unapproved change -->"
    changed = rewrite_docx(current_docx, updates={member: payload})
    result = check_files(tmp_path, current_docx, changed)
    assert result.returncode == 1, result.stdout
    assert member in result.stdout


def test_preservation_metadata_allowlist_only_permits_version_replacement(tmp_path, current_docx):
    member = "word/header3.xml"
    with ZipFile(BytesIO(current_docx)) as original:
        changed = rewrite_docx(current_docx, updates={
            member: original.read(member).replace(b"v8.3", b"UNAPPROVED SOURCE CHANGE")})
    result = check_files(tmp_path, current_docx, changed, version_metadata_members=[member])
    assert result.returncode == 1, result.stdout
    assert member in result.stdout


@pytest.mark.parametrize("operation", ["add", "remove"])
def test_preservation_rejects_archive_member_set_change(tmp_path, current_docx, operation):
    changed = (rewrite_docx(current_docx, updates={"word/extra.xml": b"<extra/>"})
               if operation == "add" else rewrite_docx(current_docx, removed=["word/header3.xml"]))
    result = check_files(tmp_path, current_docx, changed)
    assert result.returncode == 1, result.stdout
    assert "member" in result.stdout


def test_preservation_rejects_nontext_document_structure_change(tmp_path, current_docx):
    with ZipFile(BytesIO(current_docx)) as original:
        document = ET.fromstring(original.read("word/document.xml"))
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    page_size = next(document.iter(namespace + "pgSz"))
    page_size.set(namespace + "w", "1")
    changed = rewrite_docx(current_docx, updates={"word/document.xml": ET.tostring(document)})
    result = check_files(tmp_path, current_docx, changed)
    assert result.returncode == 1, result.stdout
    assert "document.xml" in result.stdout


def test_preservation_accepts_exact_approved_metadata_version_change(tmp_path, current_docx):
    member = "word/header3.xml"
    with ZipFile(BytesIO(current_docx)) as original:
        baseline = rewrite_docx(current_docx, updates={
            member: original.read(member).replace(b"v8.3", b"v8.2")})
    result = check_files(tmp_path, baseline, current_docx, version_metadata_members=[member])
    assert result.returncode == 0, result.stdout + result.stderr


def test_preservation_accepts_identical_package(tmp_path, current_docx):
    result = check_files(tmp_path, current_docx, current_docx)
    assert result.returncode == 0, result.stdout + result.stderr
