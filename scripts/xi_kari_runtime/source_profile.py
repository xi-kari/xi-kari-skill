"""Repository-owned identity of the single active source and runtime."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any


SOURCE_VERSION = "v8.3"
ANCHOR_PREFIX = "V83"
RUNTIME_VERSION = "3.0.0"
SOURCE_DOCUMENT_NAME = "跨尺度多圈层结构推演框架v8.3.docx"
RAW_SHA256 = "4a3ad8e8692b7a906f733096bbc8e05d0ac4f8cfbf79d3926eb1729df828c7f5"
SEMANTIC_SHA256 = "f190a80be88033ba21d717a310f4419c00489b3a6dea17b6a1e2b14af1447d9f"
LIST_STRUCTURE_SHA256 = "967dd396860e4b5d246ae2e3699eb33b8ab8ee46ca12bb72959e1249216d7a5f"
EXPECTED_PARAGRAPHS = 4631
EXPECTED_LIST_PARAGRAPHS = 162
EXPECTED_NON_WHITESPACE_CHARS = 168241
EXPECTED_TABLES = 122
EXPECTED_DIVISIONS = 20


def source_directory(repository_root: Path) -> Path:
    return Path(repository_root) / "references" / "source" / SOURCE_VERSION


def source_document(repository_root: Path) -> Path:
    return Path(repository_root) / "source" / SOURCE_DOCUMENT_NAME


def require_current_source(record: Mapping[str, Any]) -> None:
    """Reject older source identities without altering their artifacts."""
    if record.get("source_version") != SOURCE_VERSION:
        raise ValueError(f"This runtime requires {SOURCE_VERSION}; source migration is not automatic")
    for field in ("source_anchors", "ontology_refs"):
        for reference in record.get(field, ()):
            if not isinstance(reference, str) or not reference.startswith(ANCHOR_PREFIX + "-"):
                raise ValueError(f"Mixed source identity: {reference!r}; expected {ANCHOR_PREFIX}")
