"""Repository-owned identity of the single active source and runtime."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
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


@dataclass(frozen=True)
class SourceProfile:
    """A repository-controlled source build profile.

    The active runtime constants above intentionally remain bound to v8.3
    until the full v9.0 runtime migration is integrated.
    """

    source_version: str
    anchor_prefix: str
    document_name: str
    snapshot_directory: str
    manifest_schema_path: str
    candidate_schema_path: str
    framework_revision: str
    raw_sha256: str
    semantic_sha256: str | None
    list_structure_sha256: str | None
    semantic_normalization_version: int
    list_structure_normalization_version: int
    candidate_ruleset_version: int
    expected_body_blocks: int | None
    expected_paragraphs: int
    expected_nonempty_paragraphs: int
    expected_top_level_paragraphs: int | None
    expected_list_paragraphs: int
    expected_non_whitespace_chars: int
    expected_tables: int
    expected_reader_units: int
    division_style: str
    division_start_title: str
    division_titles: tuple[str, ...] | None

    def source_directory(self, repository_root: Path) -> Path:
        return Path(repository_root) / self.snapshot_directory

    def source_document(self, repository_root: Path) -> Path:
        return Path(repository_root) / "source" / self.document_name


_SOURCE_PROFILES = {
    "v8.3": SourceProfile(
        source_version="v8.3",
        anchor_prefix="V83",
        document_name=SOURCE_DOCUMENT_NAME,
        snapshot_directory="references/source/v8.3",
        manifest_schema_path="schemas/source-manifest.schema.json",
        candidate_schema_path="schemas/source-candidate.schema.json",
        framework_revision="v8.3",
        raw_sha256=RAW_SHA256,
        semantic_sha256=SEMANTIC_SHA256,
        list_structure_sha256=LIST_STRUCTURE_SHA256,
        semantic_normalization_version=1,
        list_structure_normalization_version=1,
        candidate_ruleset_version=4,
        expected_body_blocks=None,
        expected_paragraphs=EXPECTED_PARAGRAPHS,
        expected_nonempty_paragraphs=EXPECTED_PARAGRAPHS,
        expected_top_level_paragraphs=None,
        expected_list_paragraphs=EXPECTED_LIST_PARAGRAPHS,
        expected_non_whitespace_chars=EXPECTED_NON_WHITESPACE_CHARS,
        expected_tables=EXPECTED_TABLES,
        expected_reader_units=EXPECTED_DIVISIONS + 1,
        division_style="PartTitle",
        division_start_title="第一部分　导读",
        division_titles=None,
    ),
    "v9.0": SourceProfile(
        source_version="v9.0",
        anchor_prefix="V90",
        document_name="跨尺度多圈层结构推演框架v9.0.docx",
        snapshot_directory="references/source/v9.0",
        manifest_schema_path="schemas/source-manifest-v90.schema.json",
        candidate_schema_path="schemas/source-candidate-v90.schema.json",
        framework_revision="local-delivery-2026-09-30",
        raw_sha256="ffc45afdc288ecd268fd02e46d47318b7ddf17bf7b47605aa6c413c95398544b",
        semantic_sha256="24bf22bad46be7369df5c3a99976b48561ca03ac7f85500b4dbd7819a92015ac",
        list_structure_sha256="0517e112d6c2d02c254eb42f8d139d293dff57e56ab53c5a7551e1f92f020de9",
        semantic_normalization_version=2,
        list_structure_normalization_version=2,
        candidate_ruleset_version=5,
        expected_body_blocks=1952,
        expected_paragraphs=4298,
        expected_nonempty_paragraphs=4175,
        expected_top_level_paragraphs=1832,
        expected_list_paragraphs=162,
        expected_non_whitespace_chars=204514,
        expected_tables=120,
        expected_reader_units=21,
        division_style="Heading1",
        division_start_title="第一部分　导读",
        division_titles=(
            "第一部分　导读",
            "第二部分　边界与方法",
            "第三部分　通用结构语法",
            "第四部分　根假设与推论",
            "第五部分　跨尺度与跨圈层变换",
            "第六部分　运转与演化",
            "第七部分　人类结构化世界",
            "第八部分　人类状态原型",
            "第九部分　行动者状态与人格假设",
            "第十部分　多圈层对象与联合状态",
            "第十一部分　事件驱动的动态推演",
            "第十二部分　条件前瞻与有限选择",
            "第十三部分　接口与工具",
            "第十四部分　规范选择",
            "第十五部分　干涉与应用",
            "第十六部分　治理",
            "附录A　人类变量接口卡册",
            "附录B　编号体系与术语总表",
            "附录C 共同方法内核与跨学科桥接",
            "附录D　领域解释与应用图谱",
        ),
    ),
}


def get_source_profile(source_version: str = SOURCE_VERSION) -> SourceProfile:
    """Return an allow-listed build profile without changing runtime identity."""
    try:
        return _SOURCE_PROFILES[source_version]
    except KeyError as exc:
        supported = ", ".join(sorted(_SOURCE_PROFILES))
        raise ValueError(
            f"Unsupported source build profile {source_version!r}; expected one of {supported}"
        ) from exc


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
