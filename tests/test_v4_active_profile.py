from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
import tomllib

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from xi_kari_runtime import source_profile


def test_default_profile_selects_the_current_source_and_contract() -> None:
    profile = source_profile.get_source_profile()
    manifest = json.loads(
        (ROOT / "references/source/v9.0/source-manifest.json").read_text(encoding="utf-8")
    )

    assert profile.source_version == source_profile.SOURCE_VERSION == "v9.0"
    assert profile.anchor_prefix == source_profile.ANCHOR_PREFIX == "V90"
    assert source_profile.RUNTIME_VERSION == "4.0.0"
    assert source_profile.DEFAULT_CONTRACT_VERSION == 4
    assert source_profile.DEFAULT_CONTRACT_PROFILE == "production-authoring-v4"
    assert profile.source_document(ROOT) == source_profile.source_document(ROOT)
    assert profile.source_directory(ROOT) == source_profile.source_directory(ROOT)
    assert profile.raw_sha256 == source_profile.RAW_SHA256 == manifest["raw_sha256"]
    assert sha256(profile.source_document(ROOT).read_bytes()).hexdigest() == profile.raw_sha256


def test_explicit_legacy_profile_validates_without_rebinding_or_mutating_records() -> None:
    legacy = source_profile.get_source_profile("v8.3")
    manifest = json.loads(
        legacy.source_directory(ROOT).joinpath("source-manifest.json").read_text(encoding="utf-8")
    )
    record = {"source_version": "v8.3", "source_anchors": ["V83-P2487"], "ontology_refs": []}
    original = deepcopy(record)

    source_profile.require_source_profile(record, source_version="v8.3")
    with pytest.raises(ValueError, match="v9.0"):
        source_profile.require_current_source(record)
    with pytest.raises(ValueError, match="V83"):
        source_profile.require_source_profile(
            {**record, "source_anchors": ["V90-P00111"]}, source_version="v8.3"
        )

    assert record == original
    assert source_profile.get_source_profile().source_version == "v9.0"
    assert legacy.document_name == "跨尺度多圈层结构推演框架v8.3.docx"
    assert legacy.raw_sha256 == manifest["raw_sha256"] == "4a3ad8e8692b7a906f733096bbc8e05d0ac4f8cfbf79d3926eb1729df828c7f5"
    assert legacy.semantic_sha256 == manifest["semantic_sha256"]
    assert legacy.list_structure_sha256 == manifest["list_structure_sha256"]
    assert (legacy.expected_paragraphs, legacy.expected_tables) == (4631, 122)
    assert sha256(legacy.source_document(ROOT).read_bytes()).hexdigest() == legacy.raw_sha256
    assert source_profile.LEGACY_RUNTIME_VERSION == "3.0.0"


def test_package_version_matches_the_active_runtime() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    package = next(row for row in lock["package"] if row["name"] == "xi-kari-skill")

    assert project["project"]["version"] == package["version"] == source_profile.RUNTIME_VERSION == "4.0.0"
    assert package["source"] == {"virtual": "."}
    assert project["project"]["requires-python"] == ">=3.11"


def test_explicit_legacy_source_check_uses_its_own_fingerprint() -> None:
    from build_source_snapshot import build

    assert build(ROOT, check=True, source_version="v8.3") == []


def test_default_knowledge_profile_matches_active_source_with_explicit_legacy_access() -> None:
    from build_knowledge_index import get_knowledge_profile

    active = get_knowledge_profile()
    legacy = get_knowledge_profile("v8.3")

    assert active.source_version == "v9.0"
    assert active.ontology_root == "references/ontology/v9.0"
    assert active.learning_pack_root == "references/learning-packs/v9.0"
    assert active.domain_index == "references/domains/index.json"
    assert legacy.source_version == "v8.3"
    assert legacy.ontology_root == "references/ontology"
    assert get_knowledge_profile() == active


def _copy_source_assets(destination: Path, version: str) -> None:
    from build_knowledge_index import get_knowledge_profile

    profile = get_knowledge_profile(version)
    for relative in (profile.source_root, profile.ontology_root, profile.learning_pack_root, "schemas"):
        shutil.copytree(ROOT / relative, destination / relative, ignore=shutil.ignore_patterns("v9.0") if version == "v8.3" else None)
    if profile.domain_index:
        shutil.copytree(ROOT / "references/domains", destination / "references/domains")
        shutil.copytree(ROOT / "references/learning-packs/domains", destination / "references/learning-packs/domains")


def test_default_ontology_check_needs_only_current_source_assets(tmp_path: Path) -> None:
    from check_ontology import check

    _copy_source_assets(tmp_path, "v9.0")

    assert check(tmp_path) == []


def test_explicit_legacy_ontology_check_does_not_require_current_assets(tmp_path: Path) -> None:
    from check_ontology import check

    _copy_source_assets(tmp_path, "v8.3")

    assert check(tmp_path, source_version="v8.3") == []


@pytest.mark.parametrize(("mutation", "diagnostic"), [
    ("missing_content", "D.01: domain content is missing"),
    ("wrong_path", "D.01: domain content path does not match its identity"),
    ("wrong_hash", "D.01: domain content hash differs from the current bytes"),
    ("claimed_read", "D.01: available content still requires a run-owned read trace"),
    ("wrong_source", "D.01: domain source identity differs from current source"),
])
def test_available_domain_assets_cannot_forge_content_or_runtime_reading(
    tmp_path: Path, mutation: str, diagnostic: str
) -> None:
    from check_ontology import check

    _copy_source_assets(tmp_path, "v9.0")
    index_path = tmp_path / "references/domains/index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    entry = index["entries"][0]
    if mutation == "missing_content":
        (tmp_path / entry["content_path"]).unlink()
    elif mutation == "wrong_path":
        entry["content_path"] = "references/learning-packs/domains/D.02.md"
    elif mutation == "wrong_hash":
        entry["content_sha256"] = "0" * 64
    elif mutation == "claimed_read":
        entry["read_trace_status"] = "read"
    else:
        index["source_raw_sha256"] = "0" * 64
    index_path.write_text(json.dumps(index, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    assert any(diagnostic in error for error in check(tmp_path))
