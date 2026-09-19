from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


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
