from copy import deepcopy
from importlib import import_module
from pathlib import Path
import json

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


@pytest.mark.parametrize(("filename", "definition"), [
    ("xk-semantic-read-trace.schema.json", "source_binding"),
    ("xk-source-read.schema.json", "receipt"),
])
def test_reader_artifact_schemas_accept_current_paths_and_reject_legacy(filename, definition):
    from jsonschema import Draft202012Validator

    root = Path(__file__).resolve().parents[1]
    schema = json.loads((root / "schemas" / filename).read_text(encoding="utf-8"))
    path_schema = schema["$defs"][definition]["properties"]["path"]
    validator = Draft202012Validator(path_schema)
    assert validator.is_valid("references/source/v8.3/reader/00-source-envelope.md")
    assert not validator.is_valid("references/source/v8.2/reader/00-source-envelope.md")
    assert not validator.is_valid("references/source/v8x3/reader/00-source-envelope.md")


@pytest.mark.parametrize("filename", ("xk-source-read.schema.json", "xk-source.schema.json"))
def test_runtime_source_schemas_bind_the_current_authoritative_hashes(filename):
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "references/source/v8.3/source-manifest.json").read_text(encoding="utf-8"))
    schema = json.loads((root / "schemas" / filename).read_text(encoding="utf-8"))
    properties = schema.get("properties") or schema["$defs"]["source_lock"]["properties"]
    assert properties["source_raw_sha256"]["const"] == manifest["raw_sha256"]
    assert properties["source_semantic_sha256"]["const"] == manifest["semantic_sha256"]
