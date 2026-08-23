#!/usr/bin/env python3
"""Build and verify the compact, lossless Xi-Kari v8.2 source snapshot.

The reader edition removes XML and duplicated machine metadata, but keeps every
non-empty paragraph and every table cell exactly once in source order.  The
audit edition retains paragraph/table anchors so semantic material can always
be traced back to the DOCX.
"""

from __future__ import annotations

import argparse
import codecs
from dataclasses import dataclass
from hashlib import sha256
import html
from io import BytesIO
import json
from pathlib import Path
import re
import shutil
from typing import Iterable, Mapping, Sequence
from zipfile import BadZipFile, ZipFile
import xml.etree.ElementTree as ET


RAW_SHA256 = "670e90e0073eb1a7575a75c4e0a410630ce16bd5a10f2456b83c82480333de3f"
SEMANTIC_SHA256 = "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"
SEMANTIC_NORMALIZATION_VERSION = 1
LIST_STRUCTURE_NORMALIZATION_VERSION = 1
LIST_STRUCTURE_SHA256 = "8b4a40f8559ac61c1bb8c224054de7978bb93298efbbd41f40ed065f89bab050"
EXPECTED_PARAGRAPHS = 4631
EXPECTED_LIST_PARAGRAPHS = 162
EXPECTED_NON_WHITESPACE_CHARS = 165690
EXPECTED_TABLES = 122
EXPECTED_DIVISIONS = 20
CANDIDATE_RULESET_VERSION = 4

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"
W15_NS = "http://schemas.microsoft.com/office/word/2012/wordml"
W15 = f"{{{W15_NS}}}"
HEADING_STYLES = frozenset(
    {"CoverTitle", "CoverVer", "CoverSub", "CoverDate", "FrontHeading", "PartTitle", "SecH2", "SecH3"}
)
CONCEPT_STYLES = HEADING_STYLES | {"CardLabel"}
STRUCTURAL_CANDIDATE_STYLES = frozenset({"TOC1", "TOC2", "TOC3", "CardLabel"})
CANDIDATE_KIND_ORDER = (
    "heading",
    "definition",
    "table",
    "variable",
    "operator",
    "constraint",
    "undefined_field",
)
DEFINITION_SIGNALS = (
    "定义",
    "定义为",
    "记为",
    "称为",
    "是指",
    "所谓",
    "表示为",
    "规定为",
    "写为",
)
VARIABLE_SIGNALS = ("变量", "字段", "参数", "状态量", "符号", "向量", "张量")
VARIABLE_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:HV\d{2}|H[1-6]|S[0-6]|CM-[A-Z][A-Z0-9-]*|"
    r"M\d{2}|G[1-4](?:-instance)?|D[0-3]|U(?:0[1-9]|1[01])|S\*|SP\d*|"
    r"PF-\d+|WS\d+|Ω|Ψ)"
    r"(?![A-Za-z0-9])"
)
STATE_VALUE_SIGNALS = (
    "未知",
    "不适用",
    "不可观察",
    "未测",
    "为保护而不公开",
    "保护性不公开",
)
OPERATOR_SIGNALS = (
    "算子",
    "映射",
    "变换",
    "函数",
    "投影",
    "聚合",
    "转换",
    "递归",
    "操作",
    "→",
    "↔",
    "⇒",
    "⊕",
    "∪",
    "∩",
)
CONSTRAINT_SIGNALS = (
    "必须",
    "不得",
    "不能",
    "禁止",
    "只有",
    "仅当",
    "不等于",
    "上限",
    "约束",
    "暂停条件",
    "停止条件",
    "撤回条件",
    "须",
    "不应",
    "应设置",
    "不是",
    "不表示",
    "不意味着",
    "不蕴含",
    "不把",
    "防止",
    "要有",
    "才登记",
    "不生成",
    "不计作",
    "要求",
)
UNDEFINED_FIELD_SIGNALS = (
    "未定义",
    "未给出",
    "未规定",
    "尚未定义",
    "待定义",
)

DIVISION_SPECS = (
    ("01-guide", "第一部分　导读", 350, 423, (2, 3)),
    ("02-boundary-method", "第二部分　边界与方法", 424, 522, (4, 5)),
    ("03-universal-grammar", "第三部分　通用结构语法", 523, 584, ()),
    ("04-root-assumptions", "第四部分　根假设与推论", 585, 862, tuple(range(6, 12))),
    ("05-scale-circle-transformation", "第五部分　跨尺度与跨圈层变换", 863, 1082, tuple(range(12, 17))),
    ("06-operation-evolution", "第六部分　运转与演化", 1083, 1159, (17,)),
    ("07-human-structured-world", "第七部分　人类结构化世界", 1160, 1267, (18, 19)),
    ("08-human-state-prototypes", "第八部分　人类状态原型", 1268, 1550, tuple(range(20, 30))),
    ("09-actor-state-personality", "第九部分　行动者状态与人格假设", 1551, 1739, tuple(range(30, 36))),
    ("10-multicircle-joint-state", "第十部分　多圈层对象与联合状态", 1740, 1930, tuple(range(36, 42))),
    ("11-event-dynamic-inference", "第十一部分　事件驱动的动态推演", 1931, 2131, tuple(range(42, 48))),
    ("12-conditional-forecast-choice", "第十二部分　条件前瞻与有限选择", 2132, 2348, tuple(range(48, 56))),
    ("13-interfaces-tools", "第十三部分　接口与工具", 2349, 2600, tuple(range(56, 64))),
    ("14-normative-selection", "第十四部分　规范选择", 2601, 2667, ()),
    ("15-intervention-applications", "第十五部分　干涉与应用", 2668, 2776, ()),
    ("16-governance", "第十六部分　治理", 2777, 2905, ()),
    ("17-appendix-a-human-variable-cards", "附录A　人类变量接口卡册", 2906, 4477, tuple(range(64, 120))),
    ("18-appendix-b-numbering-terms", "附录B　编号体系与术语总表", 4478, 4572, (120,)),
    ("19-appendix-c-revisions", "附录C　版本修订记录", 4573, 4586, (121,)),
    ("20-appendix-d-common-kernel-mapping", "附录D　双文本共同内核与映射", 4587, 4631, (122,)),
)


@dataclass(frozen=True)
class Numbering:
    num_id: int
    abstract_num_id: int
    ilvl: int
    num_fmt: str
    lvl_text: str
    abstract_num_template: str
    start: int
    start_override: int | None
    effective_start: int
    lvl_restart: int | None
    restart_numbering_after_break: bool
    sequence_ordinal: int
    rendered_marker: str


@dataclass(frozen=True)
class Paragraph:
    ordinal: int
    anchor: str
    style: str
    text: str
    numbering: Numbering | None


@dataclass(frozen=True)
class Table:
    ordinal: int
    anchor: str
    paragraph_ordinals: tuple[int, ...]
    rows: tuple[tuple[str, ...], ...]
    cell_paragraph_ordinals: tuple[tuple[tuple[int, ...], ...], ...]


@dataclass(frozen=True)
class Snapshot:
    raw_sha256: str
    semantic_sha256: str
    list_structure_sha256: str
    paragraphs: tuple[Paragraph, ...]
    tables: tuple[Table, ...]
    source_unit_sequence: tuple[str, ...]
    divisions: tuple[tuple[str, str, int, int, tuple[int, ...]], ...]


@dataclass(frozen=True)
class SourceCandidate:
    candidate_id: str
    ordinal: int
    source_anchor: str
    source_unit_type: str
    source_style: str
    source_text: str
    source_anchors: tuple[str, ...]
    paragraph_anchors: tuple[str, ...]
    source_numbering: Numbering | None
    candidate_kinds: tuple[str, ...]
    matched_signals: Mapping[str, tuple[str, ...]]
    source_table_anchor: str | None = None
    source_table_row_index: int | None = None


def _text(element: ET.Element) -> str:
    parts: list[str] = []
    for node in element.iter():
        if node.tag == f"{W}t":
            parts.append(node.text or "")
        elif node.tag == f"{W}tab":
            parts.append("\t")
        elif node.tag in {f"{W}br", f"{W}cr"}:
            parts.append("\n")
    return "".join(parts)


def _style(element: ET.Element) -> str:
    properties = element.find(f"{W}pPr")
    style = None if properties is None else properties.find(f"{W}pStyle")
    return "" if style is None else style.attrib.get(f"{W}val", "")


def _read_word_xml_root(
    source: bytes, member_name: str, *, maximum_size: int
) -> ET.Element:
    if len(source) > 8 * 1024 * 1024:
        raise ValueError("DOCX archive exceeds 8 MiB safety limit")
    try:
        with ZipFile(BytesIO(source)) as archive:
            members = archive.infolist()
            if len(members) > 512:
                raise ValueError("DOCX contains too many ZIP members")
            matches = [m for m in members if m.filename == member_name]
            if len(matches) != 1:
                raise ValueError(f"DOCX must contain exactly one {member_name}")
            member = matches[0]
            if member.file_size > maximum_size:
                raise ValueError(f"{member_name} exceeds safety limit")
            if member.file_size and member.compress_size == 0:
                raise ValueError(f"invalid {member_name} compression metadata")
            if member.file_size / max(member.compress_size, 1) > 100:
                raise ValueError(f"{member_name} compression ratio exceeds safety limit")
            xml_bytes = archive.read(member)
    except BadZipFile as exc:
        raise ValueError(f"invalid DOCX ZIP: {exc}") from exc
    if xml_bytes.startswith(
        (
            codecs.BOM_UTF16_LE,
            codecs.BOM_UTF16_BE,
            codecs.BOM_UTF32_LE,
            codecs.BOM_UTF32_BE,
        )
    ):
        raise ValueError(f"{member_name} must be UTF-8")
    text = xml_bytes.decode("utf-8-sig", errors="strict")
    if "\x00" in text or re.search(r"<!\s*(?:doctype|entity)\b", text, re.I):
        raise ValueError(f"{member_name} contains forbidden encoding or XML constructs")
    return ET.fromstring(text)


def _read_document_root(source: bytes) -> ET.Element:
    return _read_word_xml_root(
        source, "word/document.xml", maximum_size=16 * 1024 * 1024
    )


def _read_numbering_root(source: bytes) -> ET.Element:
    return _read_word_xml_root(
        source, "word/numbering.xml", maximum_size=1024 * 1024
    )


def _w_val(element: ET.Element, child_name: str) -> str | None:
    child = element.find(f"{W}{child_name}")
    return None if child is None else child.attrib.get(f"{W}val")


def _int_value(value: str | None, *, label: str) -> int:
    if value is None:
        raise ValueError(f"missing OOXML numbering value: {label}")
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"invalid OOXML numbering value for {label}: {value!r}") from exc


def _render_numbering_marker(
    *, num_fmt: str, lvl_text: str, ilvl: int, sequence_ordinal: int
) -> str:
    if num_fmt == "bullet":
        return lvl_text
    if num_fmt == "decimal":
        placeholder = f"%{ilvl + 1}"
        if placeholder not in lvl_text:
            raise ValueError(
                f"decimal numbering template {lvl_text!r} lacks {placeholder}"
            )
        return lvl_text.replace(placeholder, str(sequence_ordinal))
    raise ValueError(f"unsupported OOXML numbering format: {num_fmt!r}")


def _paragraph_numbering(
    paragraph_elements: Sequence[ET.Element], numbering_root: ET.Element
) -> Mapping[int, Numbering]:
    abstracts: dict[int, dict[str, object]] = {}
    for abstract in numbering_root.findall(f"{W}abstractNum"):
        abstract_num_id = _int_value(
            abstract.attrib.get(f"{W}abstractNumId"), label="abstractNumId"
        )
        levels: dict[int, dict[str, object]] = {}
        for level in abstract.findall(f"{W}lvl"):
            ilvl = _int_value(level.attrib.get(f"{W}ilvl"), label="lvl.ilvl")
            start_value = _w_val(level, "start")
            lvl_restart_value = _w_val(level, "lvlRestart")
            levels[ilvl] = {
                "start": 1 if start_value is None else _int_value(start_value, label="lvl.start"),
                "num_fmt": _w_val(level, "numFmt") or "",
                "lvl_text": _w_val(level, "lvlText") or "",
                "lvl_restart": (
                    None
                    if lvl_restart_value is None
                    else _int_value(lvl_restart_value, label="lvl.lvlRestart")
                ),
            }
        abstracts[abstract_num_id] = {
            "template": _w_val(abstract, "tmpl") or "",
            "restart_numbering_after_break": abstract.attrib.get(
                f"{W15}restartNumberingAfterBreak", "0"
            )
            in {"1", "true", "on"},
            "levels": levels,
        }

    instances: dict[int, dict[str, object]] = {}
    for instance in numbering_root.findall(f"{W}num"):
        num_id = _int_value(instance.attrib.get(f"{W}numId"), label="numId")
        abstract_num_id = _int_value(
            _w_val(instance, "abstractNumId"), label="num.abstractNumId"
        )
        start_overrides: dict[int, int] = {}
        for override in instance.findall(f"{W}lvlOverride"):
            ilvl = _int_value(
                override.attrib.get(f"{W}ilvl"), label="lvlOverride.ilvl"
            )
            start_override = _w_val(override, "startOverride")
            if start_override is not None:
                start_overrides[ilvl] = _int_value(
                    start_override, label="lvlOverride.startOverride"
                )
        instances[num_id] = {
            "abstract_num_id": abstract_num_id,
            "start_overrides": start_overrides,
        }

    counters: dict[tuple[int, int], int] = {}
    result: dict[int, Numbering] = {}
    for paragraph in paragraph_elements:
        properties = paragraph.find(f"{W}pPr")
        num_properties = None if properties is None else properties.find(f"{W}numPr")
        if num_properties is None:
            continue
        num_id = _int_value(_w_val(num_properties, "numId"), label="p.numId")
        if num_id == 0:
            continue
        ilvl = _int_value(_w_val(num_properties, "ilvl"), label="p.ilvl")
        instance = instances.get(num_id)
        if instance is None:
            raise ValueError(f"paragraph references unknown numId {num_id}")
        abstract_num_id = int(instance["abstract_num_id"])
        abstract = abstracts.get(abstract_num_id)
        if abstract is None:
            raise ValueError(f"numId {num_id} references unknown abstractNumId {abstract_num_id}")
        levels = abstract["levels"]
        if not isinstance(levels, dict) or ilvl not in levels:
            raise ValueError(f"numId {num_id} references unknown ilvl {ilvl}")
        level = levels[ilvl]
        if not isinstance(level, dict):
            raise ValueError(f"invalid numbering level for numId {num_id} ilvl {ilvl}")
        start_overrides = instance["start_overrides"]
        if not isinstance(start_overrides, dict):
            raise ValueError(f"invalid numbering overrides for numId {num_id}")
        start = int(level["start"])
        start_override = start_overrides.get(ilvl)
        effective_start = start if start_override is None else int(start_override)
        counter_key = (num_id, ilvl)
        sequence_ordinal = counters.get(counter_key, effective_start - 1) + 1
        counters[counter_key] = sequence_ordinal
        num_fmt = str(level["num_fmt"])
        lvl_text = str(level["lvl_text"])
        rendered_marker = _render_numbering_marker(
            num_fmt=num_fmt,
            lvl_text=lvl_text,
            ilvl=ilvl,
            sequence_ordinal=sequence_ordinal,
        )
        result[id(paragraph)] = Numbering(
            num_id=num_id,
            abstract_num_id=abstract_num_id,
            ilvl=ilvl,
            num_fmt=num_fmt,
            lvl_text=lvl_text,
            abstract_num_template=str(abstract["template"]),
            start=start,
            start_override=(None if start_override is None else int(start_override)),
            effective_start=effective_start,
            lvl_restart=(
                None if level["lvl_restart"] is None else int(level["lvl_restart"])
            ),
            restart_numbering_after_break=bool(
                abstract["restart_numbering_after_break"]
            ),
            sequence_ordinal=sequence_ordinal,
            rendered_marker=rendered_marker,
        )
    return result


def extract_snapshot(source: bytes) -> Snapshot:
    root = _read_document_root(source)
    numbering_root = _read_numbering_root(source)
    paragraph_elements = tuple(p for p in root.iter(f"{W}p") if _text(p).strip())
    numbering = _paragraph_numbering(paragraph_elements, numbering_root)
    paragraphs = tuple(
        Paragraph(
            i,
            f"V82-P{i:04d}",
            _style(element),
            _text(element),
            numbering.get(id(element)),
        )
        for i, element in enumerate(paragraph_elements, 1)
    )
    ordinals = {id(element): i for i, element in enumerate(paragraph_elements, 1)}
    tables: list[Table] = []
    table_elements = tuple(root.iter(f"{W}tbl"))
    for table_ordinal, table_element in enumerate(table_elements, 1):
        rows: list[tuple[str, ...]] = []
        bindings: list[tuple[tuple[int, ...], ...]] = []
        paragraph_ordinals: list[int] = []
        for row_element in table_element.findall(f"{W}tr"):
            row_text: list[str] = []
            row_bindings: list[tuple[int, ...]] = []
            for cell_element in row_element.findall(f"{W}tc"):
                cell_text: list[str] = []
                cell_ordinals: list[int] = []
                for paragraph in cell_element.iter(f"{W}p"):
                    value = _text(paragraph)
                    if not value.strip():
                        continue
                    ordinal = ordinals[id(paragraph)]
                    cell_text.append(value)
                    cell_ordinals.append(ordinal)
                    paragraph_ordinals.append(ordinal)
                row_text.append("\n".join(cell_text))
                row_bindings.append(tuple(cell_ordinals))
            rows.append(tuple(row_text))
            bindings.append(tuple(row_bindings))
        tables.append(Table(table_ordinal, f"V82-T{table_ordinal:03d}", tuple(paragraph_ordinals), tuple(rows), tuple(bindings)))
    part_titles = [(i, p.text) for i, p in enumerate(paragraphs) if p.style == "PartTitle"]
    expected_titles = [spec[1] for spec in DIVISION_SPECS]
    if [title for _, title in part_titles] != expected_titles:
        raise ValueError("top-level PartTitle sequence does not match v8.2")
    starts = [index + 1 for index, _ in part_titles]
    divisions: list[tuple[str, str, int, int, tuple[int, ...]]] = []
    table_by_ordinal = {table.ordinal: table for table in tables}
    for index, (slug, title, _start, _end, expected_tables) in enumerate(DIVISION_SPECS):
        start = starts[index]
        end = starts[index + 1] - 1 if index + 1 < len(starts) else len(paragraphs)
        owned = tuple(table.ordinal for table in tables if table.paragraph_ordinals and start <= table.paragraph_ordinals[0] <= end)
        divisions.append((slug, title, start, end, owned))
        if owned != expected_tables:
            raise ValueError(f"table ownership mismatch for {slug}: {owned} != {expected_tables}")
    paragraph_anchor_by_element = {
        id(element): paragraph.anchor
        for element, paragraph in zip(paragraph_elements, paragraphs, strict=True)
    }
    table_anchor_by_element = {
        id(element): table.anchor
        for element, table in zip(table_elements, tables, strict=True)
    }
    source_unit_sequence = tuple(
        anchor
        for element in root.iter()
        if (
            anchor := (
                table_anchor_by_element.get(id(element))
                if element.tag == f"{W}tbl"
                else paragraph_anchor_by_element.get(id(element))
                if element.tag == f"{W}p"
                else None
            )
        )
        is not None
    )
    semantic_payload = {
        "normalization_version": SEMANTIC_NORMALIZATION_VERSION,
        "paragraphs": [{"ordinal": p.ordinal, "style": p.style, "text": p.text} for p in paragraphs],
        "tables": [
            {
                "ordinal": t.ordinal,
                "paragraph_ordinals": list(t.paragraph_ordinals),
                "rows": [list(row) for row in t.rows],
                "cell_paragraph_ordinals": [[list(cell) for cell in row] for row in t.cell_paragraph_ordinals],
            }
            for t in tables
        ],
    }
    semantic_bytes = (json.dumps(semantic_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    list_structure_payload = {
        "normalization_version": LIST_STRUCTURE_NORMALIZATION_VERSION,
        "paragraphs": [
            {
                "ordinal": paragraph.ordinal,
                "anchor": paragraph.anchor,
                "numbering": _numbering_record(paragraph.numbering),
            }
            for paragraph in paragraphs
            if paragraph.numbering is not None
        ],
    }
    list_structure_bytes = (
        json.dumps(
            list_structure_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    return Snapshot(
        sha256(source).hexdigest(),
        sha256(semantic_bytes).hexdigest(),
        sha256(list_structure_bytes).hexdigest(),
        paragraphs,
        tuple(tables),
        source_unit_sequence,
        tuple(divisions),
    )


def _canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _numbering_record(numbering: Numbering | None) -> dict[str, object] | None:
    if numbering is None:
        return None
    return {
        "num_id": numbering.num_id,
        "abstract_num_id": numbering.abstract_num_id,
        "ilvl": numbering.ilvl,
        "num_fmt": numbering.num_fmt,
        "lvl_text": numbering.lvl_text,
        "abstract_num_template": numbering.abstract_num_template,
        "start": numbering.start,
        "start_override": numbering.start_override,
        "effective_start": numbering.effective_start,
        "lvl_restart": numbering.lvl_restart,
        "restart_numbering_after_break": numbering.restart_numbering_after_break,
        "sequence_ordinal": numbering.sequence_ordinal,
        "rendered_marker": numbering.rendered_marker,
    }


def _paragraph_record(p: Paragraph) -> dict[str, object]:
    return {
        "ordinal": p.ordinal,
        "anchor": p.anchor,
        "style": p.style,
        "text": p.text,
        "numbering": _numbering_record(p.numbering),
    }


def _table_record(t: Table) -> dict[str, object]:
    return {
        "ordinal": t.ordinal,
        "anchor": t.anchor,
        "paragraph_ordinals": list(t.paragraph_ordinals),
        "rows": [list(row) for row in t.rows],
        "cell_paragraph_ordinals": [[list(cell) for cell in row] for row in t.cell_paragraph_ordinals],
    }


def _literal_matches(text: str, signals: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({signal for signal in signals if signal in text}))


def _candidate_source_order(candidate: SourceCandidate) -> tuple[int, int, str]:
    start_ordinal = int(candidate.paragraph_anchors[0].removeprefix("V82-P"))
    unit_rank = {"table": 0, "table_row": 1, "paragraph": 2}[
        candidate.source_unit_type
    ]
    return start_ordinal, unit_rank, candidate.candidate_id


def extract_candidates(snapshot: Snapshot) -> tuple[SourceCandidate, ...]:
    """Extract a deterministic source-signal census without ontology decisions."""

    candidates: list[SourceCandidate] = []
    for paragraph in snapshot.paragraphs:
        signals: dict[str, tuple[str, ...]] = {}
        if paragraph.style in HEADING_STYLES:
            signals["heading"] = (paragraph.style,)
        definition = _literal_matches(paragraph.text, DEFINITION_SIGNALS)
        if definition:
            signals["definition"] = definition
        variable = set(_literal_matches(paragraph.text, VARIABLE_SIGNALS))
        variable.update(_literal_matches(paragraph.text, STATE_VALUE_SIGNALS))
        variable.update(VARIABLE_TOKEN_RE.findall(paragraph.text))
        if variable:
            signals["variable"] = tuple(sorted(variable))
        operator = _literal_matches(paragraph.text, OPERATOR_SIGNALS)
        if operator:
            signals["operator"] = operator
        constraint = set(_literal_matches(paragraph.text, CONSTRAINT_SIGNALS))
        if paragraph.style == "Declaration":
            constraint.add("Declaration")
        if constraint:
            signals["constraint"] = tuple(sorted(constraint))
        undefined = _literal_matches(paragraph.text, UNDEFINED_FIELD_SIGNALS)
        if undefined:
            signals["undefined_field"] = undefined
        if not signals and paragraph.style in STRUCTURAL_CANDIDATE_STYLES:
            signals["heading"] = (paragraph.style,)
        if not signals:
            continue
        kinds = tuple(kind for kind in CANDIDATE_KIND_ORDER if kind in signals)
        candidates.append(
            SourceCandidate(
                candidate_id=f"V82-CANDIDATE-{paragraph.anchor.removeprefix('V82-')}",
                ordinal=paragraph.ordinal,
                source_anchor=paragraph.anchor,
                source_unit_type="paragraph",
                source_style=paragraph.style,
                source_text=paragraph.text,
                source_anchors=(paragraph.anchor,),
                paragraph_anchors=(paragraph.anchor,),
                source_numbering=paragraph.numbering,
                candidate_kinds=kinds,
                matched_signals={kind: signals[kind] for kind in kinds},
            )
        )
    for table in snapshot.tables:
        source_text = json.dumps(
            [list(row) for row in table.rows],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        candidates.append(
            SourceCandidate(
                candidate_id=f"V82-CANDIDATE-{table.anchor.removeprefix('V82-')}",
                ordinal=table.ordinal,
                source_anchor=table.anchor,
                source_unit_type="table",
                source_style="",
                source_text=source_text,
                source_anchors=(table.anchor,),
                paragraph_anchors=tuple(
                    f"V82-P{ordinal:04d}" for ordinal in table.paragraph_ordinals
                ),
                source_numbering=None,
                candidate_kinds=("table",),
                matched_signals={"table": (table.anchor,)},
            )
        )
        for row_index, (row, bindings) in enumerate(
            zip(table.rows, table.cell_paragraph_ordinals, strict=True), 1
        ):
            paragraph_anchors = tuple(
                f"V82-P{ordinal:04d}"
                for cell in bindings
                for ordinal in cell
            )
            if not paragraph_anchors:
                continue
            row_anchor = f"{table.anchor}-R{row_index:03d}"
            is_heading = row_index == 1
            kinds = ("heading", "table") if is_heading else ("table",)
            matched_signals = {"table": (table.anchor,)}
            if is_heading:
                matched_signals = {
                    "heading": ("TableHead",),
                    **matched_signals,
                }
            candidates.append(
                SourceCandidate(
                    candidate_id=(
                        f"V82-CANDIDATE-{row_anchor.removeprefix('V82-')}"
                    ),
                    ordinal=row_index,
                    source_anchor=row_anchor,
                    source_unit_type="table_row",
                    source_style="TableHead" if is_heading else "TableRow",
                    source_text=json.dumps(
                        list(row),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    source_anchors=paragraph_anchors,
                    paragraph_anchors=paragraph_anchors,
                    source_numbering=None,
                    candidate_kinds=kinds,
                    matched_signals=matched_signals,
                    source_table_anchor=table.anchor,
                    source_table_row_index=row_index,
                )
            )
    return tuple(sorted(candidates, key=_candidate_source_order))


def _candidate_semantic_payload(candidate: SourceCandidate) -> dict[str, object]:
    undefined_fields = list(candidate.matched_signals.get("undefined_field", ()))
    payload: dict[str, object] = {
        "source_unit_type": candidate.source_unit_type,
        "source_style": candidate.source_style,
        "source_text": candidate.source_text,
        "candidate_kinds": list(candidate.candidate_kinds),
        "matched_signals": {
            kind: list(candidate.matched_signals[kind])
            for kind in candidate.candidate_kinds
        },
        "source_undefined_fields": undefined_fields,
    }
    if candidate.source_unit_type == "table_row":
        payload.update(
            {
                "source_table_anchor": candidate.source_table_anchor,
                "source_table_row_index": candidate.source_table_row_index,
            }
        )
    return payload


def _candidate_record(
    candidate: SourceCandidate,
    snapshot: Snapshot,
    *,
    previous_candidate_id: str | None,
    next_candidate_id: str | None,
) -> dict[str, object]:
    semantic_payload = _candidate_semantic_payload(candidate)
    return {
        "schema_id": "xi-kari.v8.2.source-candidate",
        "schema_version": 1,
        "framework_version": "v8.2",
        "candidate_ruleset_version": CANDIDATE_RULESET_VERSION,
        "candidate_id": candidate.candidate_id,
        "previous_candidate_id": previous_candidate_id,
        "next_candidate_id": next_candidate_id,
        "ordinal": candidate.ordinal,
        "source_anchor": candidate.source_anchor,
        "source_anchors": list(candidate.source_anchors),
        "source_span": {
            "start_anchor": candidate.paragraph_anchors[0],
            "end_anchor": candidate.paragraph_anchors[-1],
            "paragraph_anchors": list(candidate.paragraph_anchors),
        },
        "source_numbering": _numbering_record(candidate.source_numbering),
        **semantic_payload,
        "text_sha256": sha256(candidate.source_text.encode("utf-8")).hexdigest(),
        "semantic_fingerprint_sha256": sha256(
            _canonical(semantic_payload)
        ).hexdigest(),
        "source_raw_sha256": snapshot.raw_sha256,
        "source_semantic_sha256": snapshot.semantic_sha256,
        "source_list_structure_sha256": snapshot.list_structure_sha256,
    }


def _division_for_ordinal(snapshot: Snapshot, ordinal: int) -> tuple[str, str, int, int, tuple[int, ...]]:
    for division in snapshot.divisions:
        if division[2] <= ordinal <= division[3]:
            return division
    raise ValueError(f"no division for paragraph ordinal {ordinal}")


def _heading_level(style: str) -> int:
    return {"CoverTitle": 1, "PartTitle": 1, "FrontHeading": 2, "SecH2": 2, "SecH3": 3}.get(style, 0)


def _render_table_html(table: Table, paragraphs: Mapping[int, Paragraph]) -> str:
    lines = [f'<table data-source-table="{table.anchor}">']
    for row_index, (row, bindings) in enumerate(zip(table.rows, table.cell_paragraph_ordinals, strict=True), 1):
        lines.append("<tr>")
        for column_index, (cell, ordinals) in enumerate(zip(row, bindings, strict=True), 1):
            anchors = ",".join(paragraphs[ordinal].anchor for ordinal in ordinals)
            lines.append(f'<td data-source-cell="{row_index},{column_index}" data-paragraphs="{anchors}">')
            for ordinal in ordinals:
                paragraph = paragraphs[ordinal]
                lines.append(f'<!-- source-paragraph:{paragraph.anchor} style={paragraph.style} -->')
            lines.append(f"<pre>{html.escape(cell)}</pre>")
            lines.append("</td>")
        lines.append("</tr>")
    lines.append("</table>")
    return "\n".join(lines)


def _reader_for_division(snapshot: Snapshot, division: tuple[str, str, int, int, tuple[int, ...]], root: ET.Element) -> str:
    slug, title, start, end, owned_tables = division
    paragraphs = {p.ordinal: p for p in snapshot.paragraphs}
    table_by_id = {t.ordinal: t for t in snapshot.tables}
    table_by_first_paragraph = {t.paragraph_ordinals[0]: t for t in snapshot.tables if t.paragraph_ordinals}
    body = root.find(f"{W}body")
    if body is None:
        raise ValueError("document.xml has no body")
    lines = [f"# {title}", "", f"Source: `v8.2`", f"Raw SHA256: `{snapshot.raw_sha256}`", f"Semantic SHA256: `{snapshot.semantic_sha256}`", f"List structure SHA256: `{snapshot.list_structure_sha256}`", f"Paragraph range: `V82-P{start:04d}`-`V82-P{end:04d}`", f"Tables: {', '.join(f'`V82-T{x:03d}`' for x in owned_tables) or '`none`'}", "", "<!-- This is a lossless reader edition; anchors are source coordinates. -->", ""]
    ordinal_by_element = {id(element): i for i, element in enumerate((p for p in body.iter(f"{W}p") if _text(p).strip()), 1)}
    table_ordinal_by_element = {id(element): i for i, element in enumerate(body.iter(f"{W}tbl"), 1)}
    for child in list(body):
        if child.tag == f"{W}p":
            value = _text(child)
            if not value.strip():
                continue
            ordinal = ordinal_by_element.get(id(child))
            if ordinal is None or not (start <= ordinal <= end):
                continue
            paragraph = paragraphs[ordinal]
            level = _heading_level(paragraph.style)
            marker = f"<!-- source-paragraph:{paragraph.anchor} style={paragraph.style} -->"
            if level:
                lines.extend([marker, f"{'#' * level} {html.escape(paragraph.text)}", ""])
            else:
                text = html.escape(paragraph.text)
                if paragraph.numbering is not None and paragraph.numbering.rendered_marker:
                    text = (
                        "  " * paragraph.numbering.ilvl
                        + html.escape(paragraph.numbering.rendered_marker)
                        + " "
                        + text
                    )
                lines.extend([marker, text, ""])
        elif child.tag == f"{W}tbl":
            ordinal = table_ordinal_by_element.get(id(child))
            if ordinal is None or ordinal not in owned_tables:
                continue
            table = table_by_id[ordinal]
            lines.extend([f"## {table.anchor}", "", _render_table_html(table, paragraphs), ""])
    return "\n".join(lines)


def _render_table_audit(table: Table, snapshot: Snapshot) -> str:
    payload = _table_record(table)
    lines = [f"# v8.2 Table {table.anchor}", "", f"Raw SHA256: `{snapshot.raw_sha256}`", f"Semantic SHA256: `{snapshot.semantic_sha256}`", f"List structure SHA256: `{snapshot.list_structure_sha256}`", f"Row count: `{len(table.rows)}`", f"Column count: `{max((len(row) for row in table.rows), default=0)}`", "", "## Exact rows", "", "```json", json.dumps(payload["rows"], ensure_ascii=False, indent=2), "```", "", "## Cell paragraph anchors", "", "```json", json.dumps(payload["cell_paragraph_ordinals"], ensure_ascii=False, indent=2), "```", ""]
    return "\n".join(lines)


def _expected_files(source: bytes, snapshot: Snapshot, root: ET.Element) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    files["reader/00-index.md"] = _reader_index(snapshot).encode("utf-8")
    envelope = ("00-source-envelope", "Front matter", 1, 349, (1,))
    files["reader/00-source-envelope.md"] = _reader_for_division(snapshot, envelope, root).encode("utf-8")
    for division in snapshot.divisions:
        files[f"reader/{division[0]}.md"] = _reader_for_division(snapshot, division, root).encode("utf-8")
    audit_paragraphs = "".join(json.dumps(_paragraph_record(p), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for p in snapshot.paragraphs)
    files["audit/paragraphs.jsonl"] = audit_paragraphs.encode("utf-8")
    for table in snapshot.tables:
        files[f"audit/tables/{table.anchor}.md"] = _render_table_audit(table, snapshot).encode("utf-8")
    files["indexes/headings.json"] = _canonical([_paragraph_record(p) for p in snapshot.paragraphs if p.style in HEADING_STYLES])
    files["indexes/terms.json"] = _canonical([_paragraph_record(p) for p in snapshot.paragraphs if p.style in CONCEPT_STYLES])
    files["indexes/tables.json"] = _canonical([_table_record(t) for t in snapshot.tables])
    files["indexes/anchors.json"] = _canonical({"paragraphs": [p.anchor for p in snapshot.paragraphs], "tables": [t.anchor for t in snapshot.tables]})
    candidates = extract_candidates(snapshot)
    candidate_records = [
        _candidate_record(
            candidate,
            snapshot,
            previous_candidate_id=(
                candidates[index - 1].candidate_id if index else None
            ),
            next_candidate_id=(
                candidates[index + 1].candidate_id
                if index + 1 < len(candidates)
                else None
            ),
        )
        for index, candidate in enumerate(candidates)
    ]
    candidate_index = b"".join(_canonical(record) for record in candidate_records)
    files["indexes/candidates.jsonl"] = candidate_index
    candidate_kind_counts = {
        kind: sum(kind in candidate.candidate_kinds for candidate in candidates)
        for kind in CANDIDATE_KIND_ORDER
    }
    manifest = {
        "schema_id": "xi-kari.v8.2.source-manifest",
        "schema_version": 2,
        "framework_version": "v8.2",
        "framework_revision": "v8.2",
        "raw_sha256": snapshot.raw_sha256,
        "semantic_sha256": snapshot.semantic_sha256,
        "semantic_normalization_version": SEMANTIC_NORMALIZATION_VERSION,
        "list_structure_sha256": snapshot.list_structure_sha256,
        "list_structure_normalization_version": LIST_STRUCTURE_NORMALIZATION_VERSION,
        "paragraph_count": len(snapshot.paragraphs),
        "list_paragraph_count": sum(
            paragraph.numbering is not None for paragraph in snapshot.paragraphs
        ),
        "heading_count": sum(p.style in HEADING_STYLES for p in snapshot.paragraphs),
        "table_count": len(snapshot.tables),
        "concept_count": len({(p.style, p.text) for p in snapshot.paragraphs if p.style in CONCEPT_STYLES}),
        "concept_count_semantics": "mechanical count of distinct (style, text) pairs among concept-styled source paragraphs; not a complete ontology concept count",
        "candidate_ruleset_version": CANDIDATE_RULESET_VERSION,
        "candidate_count": len(candidates),
        "candidate_count_semantics": "deterministic source-signal census under the declared ruleset; not an ontology classification or a complete or fixed concept count",
        "candidate_kind_counts": candidate_kind_counts,
        "candidate_index_sha256": sha256(candidate_index).hexdigest(),
        "contract_count": sum(p.style in HEADING_STYLES and "合同" in p.text for p in snapshot.paragraphs),
        "source_unit_count": len(snapshot.paragraphs) + len(snapshot.tables),
        "source_unit_sequence": list(snapshot.source_unit_sequence),
        "source_unit_file_sha256": {
            path: sha256(files[path]).hexdigest()
            for path in sorted(
                {
                    "audit/paragraphs.jsonl",
                    "indexes/tables.json",
                    *(f"audit/tables/{table.anchor}.md" for table in snapshot.tables),
                }
            )
        },
        "non_whitespace_chars": sum(not c.isspace() for p in snapshot.paragraphs for c in p.text),
        "divisions": [{"slug": d[0], "title": d[1], "start_ordinal": d[2], "end_ordinal": d[3], "table_ordinals": list(d[4])} for d in snapshot.divisions],
        "reader_units": ["00-source-envelope.md", *(f"{d[0]}.md" for d in snapshot.divisions)],
        "reader_unit_count": 21,
        "sequence": ["00-source-envelope.md", *(f"{d[0]}.md" for d in snapshot.divisions)],
        "reader_file_sha256": {
            path: sha256(content).hexdigest()
            for path, content in sorted(files.items())
            if path.startswith("reader/") and path != "reader/00-index.md"
        },
        "reader_files": sorted(path for path in files if path.startswith("reader/")),
        "audit_files": sorted(path for path in files if path.startswith("audit/")),
        "index_files": sorted(path for path in files if path.startswith("indexes/")),
    }
    files["source-manifest.json"] = _canonical(manifest)
    return files


def _reader_index(snapshot: Snapshot) -> str:
    lines = ["# Xi-Kari v8.2 lossless reader", "", f"Raw SHA256: `{snapshot.raw_sha256}`", f"Semantic SHA256: `{snapshot.semantic_sha256}`", f"List structure SHA256: `{snapshot.list_structure_sha256}`", "", "Read every file below in order. This index never replaces the source volumes.", "", "| order | file | paragraph range | tables |", "| ---: | --- | --- | --- |"]
    lines.append("| 0 | `00-source-envelope.md` | `V82-P0001`-`V82-P0349` | `V82-T001` |")
    for index, division in enumerate(snapshot.divisions, 1):
        tables = ", ".join(f"`V82-T{x:03d}`" for x in division[4]) or "none"
        lines.append(f"| {index} | `{division[0]}.md` | `V82-P{division[2]:04d}`-`V82-P{division[3]:04d}` | {tables} |")
    lines.extend(["", "The audit directory preserves exact unit records and table cell bindings.", ""])
    return "\n".join(lines)


def _validate_snapshot(snapshot: Snapshot) -> list[str]:
    errors: list[str] = []
    if snapshot.raw_sha256 != RAW_SHA256:
        errors.append(f"raw SHA256 mismatch: {snapshot.raw_sha256}")
    if snapshot.semantic_sha256 != SEMANTIC_SHA256:
        errors.append(f"semantic SHA256 mismatch: {snapshot.semantic_sha256}")
    if snapshot.list_structure_sha256 != LIST_STRUCTURE_SHA256:
        errors.append(
            f"list structure SHA256 mismatch: {snapshot.list_structure_sha256}"
        )
    if len(snapshot.paragraphs) != EXPECTED_PARAGRAPHS:
        errors.append(f"paragraph count mismatch: {len(snapshot.paragraphs)}")
    list_paragraph_count = sum(
        paragraph.numbering is not None for paragraph in snapshot.paragraphs
    )
    if list_paragraph_count != EXPECTED_LIST_PARAGRAPHS:
        errors.append(f"list paragraph count mismatch: {list_paragraph_count}")
    if len(snapshot.tables) != EXPECTED_TABLES:
        errors.append(f"table count mismatch: {len(snapshot.tables)}")
    if len(snapshot.divisions) != EXPECTED_DIVISIONS:
        errors.append(f"division count mismatch: {len(snapshot.divisions)}")
    if tuple(p.ordinal for p in snapshot.paragraphs) != tuple(range(1, EXPECTED_PARAGRAPHS + 1)):
        errors.append("paragraph ordinals are not continuous")
    if tuple(t.ordinal for t in snapshot.tables) != tuple(range(1, EXPECTED_TABLES + 1)):
        errors.append("table ordinals are not continuous")
    if len(snapshot.source_unit_sequence) != EXPECTED_PARAGRAPHS + EXPECTED_TABLES:
        errors.append(
            f"source unit sequence count mismatch: {len(snapshot.source_unit_sequence)}"
        )
    if len(set(snapshot.source_unit_sequence)) != len(snapshot.source_unit_sequence):
        errors.append("source unit sequence anchors are not unique")
    measured = sum(not c.isspace() for p in snapshot.paragraphs for c in p.text)
    if measured != EXPECTED_NON_WHITESPACE_CHARS:
        errors.append(f"non-whitespace count mismatch: {measured}")
    paragraph_by_ordinal = {p.ordinal: p.text for p in snapshot.paragraphs}
    for table in snapshot.tables:
        flat = tuple(o for row in table.cell_paragraph_ordinals for cell in row for o in cell)
        if flat != table.paragraph_ordinals:
            errors.append(f"{table.anchor}: cell binding order mismatch")
        for row, bindings in zip(table.rows, table.cell_paragraph_ordinals, strict=True):
            for cell, ordinals in zip(row, bindings, strict=True):
                expected = "\n".join(paragraph_by_ordinal[o] for o in ordinals)
                if cell != expected:
                    errors.append(f"{table.anchor}: cell text mismatch")
    return errors


def _output_files(root: Path) -> dict[str, bytes]:
    base = root / "references" / "source" / "v8.2"
    files: dict[str, bytes] = {}
    for path in base.rglob("*"):
        if path.is_file():
            files[path.relative_to(base).as_posix()] = path.read_bytes()
    return files


def build(root: Path, *, check: bool) -> list[str]:
    source_path = root / "source" / "跨尺度多圈层结构推演框架v8.2.docx"
    if not source_path.is_file():
        return [f"missing source: {source_path}"]
    source = source_path.read_bytes()
    snapshot = extract_snapshot(source)
    errors = _validate_snapshot(snapshot)
    generated = _expected_files(source, snapshot, _read_document_root(source))
    base = root / "references" / "source" / "v8.2"
    if check:
        actual = _output_files(root)
        if set(actual) != set(generated):
            errors.append(f"generated file set mismatch: missing={sorted(set(generated)-set(actual))}, extra={sorted(set(actual)-set(generated))}")
        for path, expected in generated.items():
            if actual.get(path) != expected:
                errors.append(f"generated file differs: {path}")
    else:
        base.mkdir(parents=True, exist_ok=True)
        for path in sorted(set(_output_files(root)) | set(generated)):
            target = base / path
            if path not in generated:
                target.unlink()
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(generated[path])
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--all", action="store_true", help="check source and generated files")
    parser.add_argument("--write", action="store_true", help="write generated source files")
    args = parser.parse_args()
    check = args.check or args.all or not args.write
    errors = build(args.root.resolve(), check=check)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("source snapshot: PASS")
    if not check:
        print("source snapshot: generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
