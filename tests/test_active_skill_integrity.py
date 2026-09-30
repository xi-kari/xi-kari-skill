from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_xi_kari_skill import check


@pytest.fixture
def package(tmp_path: Path) -> Path:
    destination = tmp_path / "package"
    shutil.copytree(ROOT, destination, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
    return destination


def test_skill_checker_rejects_current_source_manifest_identity_drift(package: Path) -> None:
    path = package / "references/source/v9.0/source-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["raw_sha256"] = "0" * 64
    path.write_text(json.dumps(manifest), encoding="utf-8")

    errors = check(package, all_checks=False)

    assert any("v9.0" in error and "manifest" in error for error in errors)


def test_reader_text_is_not_parsed_as_product_navigation(package: Path) -> None:
    (package / "references/source/v9.0/reader/navigation-example.md").write_text(
        "[source notation](not-a-product-file.md)\n", encoding="utf-8"
    )

    assert check(package, all_checks=False) == []


def test_product_document_links_remain_checked(package: Path) -> None:
    (package / "protocols/navigation-example.md").write_text(
        "[required product document](not-a-product-file.md)\n", encoding="utf-8"
    )

    assert any("broken markdown link" in error for error in check(package, all_checks=False))


def test_complete_skill_check_still_verifies_legacy_source_bytes(package: Path) -> None:
    path = package / "source/跨尺度多圈层结构推演框架v8.3.docx"
    path.write_bytes(path.read_bytes() + b"changed legacy source")

    assert any("raw SHA256 mismatch" in error for error in check(package, all_checks=True))
