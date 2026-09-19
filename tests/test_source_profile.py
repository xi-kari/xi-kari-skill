from copy import deepcopy
from importlib import import_module
from pathlib import Path

import pytest


def profile():
    return import_module("scripts.xi_kari_runtime.source_profile")


def test_source_identity_and_runtime_identity_are_distinct() -> None:
    binding = profile()
    assert binding.SOURCE_VERSION == "v8.3"
    assert binding.ANCHOR_PREFIX == "V83"
    assert binding.RUNTIME_VERSION == "3.0.0"


def test_legacy_identity_is_rejected_without_rewriting() -> None:
    binding = profile()
    record = {"source_version": "v8.2", "source_anchors": ["V82-P2487"]}
    original = deepcopy(record)
    with pytest.raises(ValueError, match="v8.3"):
        binding.require_current_source(record)
    assert record == original


def test_current_identity_does_not_accept_legacy_anchors() -> None:
    binding = profile()
    with pytest.raises(ValueError, match="V82"):
        binding.require_current_source(
            {"source_version": "v8.3", "source_anchors": ["V82-P2487"]}
        )


def test_current_identity_accepts_current_anchors() -> None:
    binding = profile()
    binding.require_current_source(
        {"source_version": "v8.3", "source_anchors": ["V83-P2487"]}
    )


def test_source_paths_are_bound_to_the_supplied_repository() -> None:
    binding = profile()
    root = Path("isolated-repository")
    assert binding.source_directory(root) == root / "references" / "source" / "v8.3"
    assert binding.source_document(root) == root / "source" / "跨尺度多圈层结构推演框架v8.3.docx"
