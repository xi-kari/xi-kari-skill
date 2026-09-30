"""Deterministic Xi-Kari v9.0 DOCX source snapshot builder."""

from __future__ import annotations

import codecs
from dataclasses import dataclass
from hashlib import sha256
import html
from io import BytesIO
import json
from pathlib import Path
import re
from typing import Mapping, Sequence
from zipfile import BadZipFile, ZipFile
import xml.etree.ElementTree as ET

from xi_kari_runtime.source_profile import SourceProfile


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"
W15_NS = "http://schemas.microsoft.com/office/word/2012/wordml"
W15 = f"{{{W15_NS}}}"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"

INDEX_HEADING_STYLES = frozenset({"Heading1", "Heading2", "Heading3"})
CANDIDATE_HEADING_STYLES = INDEX_HEADING_STYLES | {"CoverTitle", "CardLabel"}
CONCEPT_STYLES = CANDIDATE_HEADING_STYLES
CANDIDATE_KIND_ORDER = (
    "heading",
    "domain_entry",
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
    r"PF-\d+|WS\d+|Ω|Ψ)(?![A-Za-z0-9])"
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
UNDEFINED_FIELD_SIGNALS = ("未定义", "未给出", "未规定", "尚未定义", "待定义")
DOMAIN_ENTRY_RE = re.compile(r"^(D\.(?:0[1-9]|[12]\d|3[0-2]))\u3000")


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
    alias: str
    document_paragraph_index: int
    locator: str
    body_anchor: str
    body_alias: str
    scope: str
    style: str
    style_name: str | None
    text: str
    inline_events: tuple[Mapping[str, object], ...]
    numbering: Numbering | None
    table_anchor: str | None = None
    table_alias: str | None = None
    table_row_index: int | None = None
    table_cell_index: int | None = None


@dataclass(frozen=True)
class BodyBlock:
    ordinal: int
    anchor: str
    alias: str
    kind: str
    scope: str
    locator: str
    paragraph_anchor: str | None = None
    table_anchor: str | None = None


@dataclass(frozen=True)
class TableCell:
    index: int
    locator: str
    grid_span: int
    vertical_merge: str | None
    paragraph_anchors: tuple[str, ...]


@dataclass(frozen=True)
class TableRow:
    index: int
    locator: str
    cells: tuple[TableCell, ...]


@dataclass(frozen=True)
class Table:
    ordinal: int
    anchor: str
    alias: str
    locator: str
    body_anchor: str
    body_alias: str
    scope: str
    rows: tuple[TableRow, ...]
    paragraph_anchors: tuple[str, ...]


@dataclass(frozen=True)
class Division:
    ordinal: int
    title: str
    reader_file: str
    body_anchors: tuple[str, ...]
    paragraph_anchors: tuple[str, ...]
    table_anchors: tuple[str, ...]
    source_unit_anchors: tuple[str, ...]


@dataclass(frozen=True)
class Snapshot:
    raw_sha256: str
    semantic_sha256: str
    list_structure_sha256: str
    xml_sha256: Mapping[str, str]
    structural_flags: Mapping[str, int]
    body_blocks: tuple[BodyBlock, ...]
    paragraphs: tuple[Paragraph, ...]
    tables: tuple[Table, ...]
    source_unit_sequence: tuple[str, ...]
    divisions: tuple[Division, ...]


@dataclass(frozen=True)
class SourceCandidate:
    candidate_id: str
    source_anchor: str
    source_aliases: tuple[str, ...]
    source_unit_type: str
    source_style: str
    source_text: str
    source_anchors: tuple[str, ...]
    body_anchor: str
    source_numbering: Numbering | None
    candidate_kinds: tuple[str, ...]
    matched_signals: Mapping[str, tuple[str, ...]]
    domain_id: str | None = None
    source_table_anchor: str | None = None
    source_table_row_index: int | None = None


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _read_member(source: bytes, member_name: str, *, maximum_size: int) -> bytes:
    if len(source) > 8 * 1024 * 1024:
        raise ValueError("DOCX archive exceeds 8 MiB safety limit")
    try:
        with ZipFile(BytesIO(source)) as archive:
            members = archive.infolist()
            if len(members) > 512:
                raise ValueError("DOCX contains too many ZIP members")
            matches = [member for member in members if member.filename == member_name]
            if len(matches) != 1:
                raise ValueError(f"DOCX must contain exactly one {member_name}")
            member = matches[0]
            if member.file_size > maximum_size:
                raise ValueError(f"{member_name} exceeds safety limit")
            if member.file_size and member.compress_size == 0:
                raise ValueError(f"invalid {member_name} compression metadata")
            if member.file_size / max(member.compress_size, 1) > 100:
                raise ValueError(f"{member_name} compression ratio exceeds safety limit")
            payload = archive.read(member)
    except BadZipFile as exc:
        raise ValueError(f"invalid DOCX ZIP: {exc}") from exc
    if payload.startswith(
        (
            codecs.BOM_UTF16_LE,
            codecs.BOM_UTF16_BE,
            codecs.BOM_UTF32_LE,
            codecs.BOM_UTF32_BE,
        )
    ):
        raise ValueError(f"{member_name} must be UTF-8")
    text = payload.decode("utf-8-sig", errors="strict")
    if "\x00" in text or re.search(r"<!\s*(?:doctype|entity)\b", text, re.I):
        raise ValueError(f"{member_name} contains forbidden encoding or XML constructs")
    return payload


def _parse_xml(payload: bytes, member_name: str) -> ET.Element:
    try:
        return ET.fromstring(payload.decode("utf-8-sig", errors="strict"))
    except ET.ParseError as exc:
        raise ValueError(f"invalid {member_name}: {exc}") from exc


def _w_val(element: ET.Element | None, child_name: str) -> str | None:
    if element is None:
        return None
    child = element.find(f"{W}{child_name}")
    return None if child is None else child.attrib.get(f"{W}val")


def _int_value(value: str | None, *, label: str) -> int:
    if value is None:
        raise ValueError(f"missing OOXML numbering value: {label}")
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"invalid OOXML numbering value for {label}: {value!r}") from exc


def _paragraph_text(element: ET.Element) -> tuple[str, tuple[Mapping[str, object], ...]]:
    parts: list[str] = []
    events: list[Mapping[str, object]] = []
    length = 0
    for node in element.iter():
        if node.tag == f"{W}t":
            value = node.text or ""
            parts.append(value)
            length += len(value)
        elif node.tag == f"{W}tab":
            parts.append("\t")
            events.append({"type": "tab", "text_offset": length})
            length += 1
        elif node.tag in {f"{W}br", f"{W}cr"}:
            parts.append("\n")
            events.append(
                {
                    "type": "break",
                    "break_type": node.attrib.get(f"{W}type", "textWrapping"),
                    "text_offset": length,
                }
            )
            length += 1
    return "".join(parts), tuple(events)


def _style_id(element: ET.Element) -> str:
    properties = element.find(f"{W}pPr")
    style = None if properties is None else properties.find(f"{W}pStyle")
    return "" if style is None else style.attrib.get(f"{W}val", "")


def _style_names(styles_root: ET.Element) -> Mapping[str, str]:
    values: dict[str, str] = {}
    for style in styles_root.findall(f"{W}style"):
        style_id = style.attrib.get(f"{W}styleId")
        name = _w_val(style, "name")
        if style_id and name is not None:
            values[style_id] = name
    return values


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
                "start": 1
                if start_value is None
                else _int_value(start_value, label="lvl.start"),
                "num_fmt": _w_val(level, "numFmt") or "",
                "lvl_text": _w_val(level, "lvlText") or "",
                "lvl_restart": None
                if lvl_restart_value is None
                else _int_value(lvl_restart_value, label="lvl.lvlRestart"),
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
            raise ValueError(
                f"numId {num_id} references unknown abstractNumId {abstract_num_id}"
            )
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
        result[id(paragraph)] = Numbering(
            num_id=num_id,
            abstract_num_id=abstract_num_id,
            ilvl=ilvl,
            num_fmt=num_fmt,
            lvl_text=lvl_text,
            abstract_num_template=str(abstract["template"]),
            start=start,
            start_override=None if start_override is None else int(start_override),
            effective_start=effective_start,
            lvl_restart=None
            if level["lvl_restart"] is None
            else int(level["lvl_restart"]),
            restart_numbering_after_break=bool(
                abstract["restart_numbering_after_break"]
            ),
            sequence_ordinal=sequence_ordinal,
            rendered_marker=_render_numbering_marker(
                num_fmt=num_fmt,
                lvl_text=lvl_text,
                ilvl=ilvl,
                sequence_ordinal=sequence_ordinal,
            ),
        )
    return result


def _numbering_record(value: Numbering | None) -> dict[str, object] | None:
    if value is None:
        return None
    return {
        "num_id": value.num_id,
        "abstract_num_id": value.abstract_num_id,
        "ilvl": value.ilvl,
        "num_fmt": value.num_fmt,
        "lvl_text": value.lvl_text,
        "abstract_num_template": value.abstract_num_template,
        "start": value.start,
        "start_override": value.start_override,
        "effective_start": value.effective_start,
        "lvl_restart": value.lvl_restart,
        "restart_numbering_after_break": value.restart_numbering_after_break,
        "sequence_ordinal": value.sequence_ordinal,
        "rendered_marker": value.rendered_marker,
    }


def _paragraph_record(paragraph: Paragraph) -> dict[str, object]:
    return {
        "anchor": paragraph.anchor,
        "aliases": [paragraph.alias],
        "ordinal": paragraph.ordinal,
        "document_paragraph_index": paragraph.document_paragraph_index,
        "locator": paragraph.locator,
        "body_anchor": paragraph.body_anchor,
        "body_alias": paragraph.body_alias,
        "scope": paragraph.scope,
        "style_id": paragraph.style,
        "style_name": paragraph.style_name,
        "text": paragraph.text,
        "text_sha256": sha256(paragraph.text.encode("utf-8")).hexdigest(),
        "inline_events": list(paragraph.inline_events),
        "numbering": _numbering_record(paragraph.numbering),
        "table_anchor": paragraph.table_anchor,
        "table_alias": paragraph.table_alias,
        "table_row_index": paragraph.table_row_index,
        "table_cell_index": paragraph.table_cell_index,
    }


def _body_record(block: BodyBlock) -> dict[str, object]:
    return {
        "anchor": block.anchor,
        "aliases": [block.alias],
        "ordinal": block.ordinal,
        "kind": block.kind,
        "scope": block.scope,
        "locator": block.locator,
        "paragraph_anchor": block.paragraph_anchor,
        "table_anchor": block.table_anchor,
    }


def _cell_record(cell: TableCell) -> dict[str, object]:
    return {
        "cell_index": cell.index,
        "locator": cell.locator,
        "grid_span": cell.grid_span,
        "vertical_merge": cell.vertical_merge,
        "paragraph_anchors": list(cell.paragraph_anchors),
    }


def _table_record(table: Table) -> dict[str, object]:
    return {
        "anchor": table.anchor,
        "aliases": [table.alias],
        "ordinal": table.ordinal,
        "locator": table.locator,
        "body_anchor": table.body_anchor,
        "body_alias": table.body_alias,
        "scope": table.scope,
        "paragraph_anchors": list(table.paragraph_anchors),
        "rows": [
            {
                "row_index": row.index,
                "locator": row.locator,
                "cells": [_cell_record(cell) for cell in row.cells],
            }
            for row in table.rows
        ],
    }


def _semantic_payload(
    body_blocks: Sequence[BodyBlock],
    paragraphs: Mapping[str, Paragraph],
    tables: Mapping[str, Table],
) -> dict[str, object]:
    blocks: list[dict[str, object]] = []
    for block in body_blocks:
        if block.paragraph_anchor is not None:
            paragraph = paragraphs[block.paragraph_anchor]
            blocks.append(
                {
                    "kind": block.kind,
                    "style_id": paragraph.style,
                    "text": paragraph.text,
                    "inline_events": list(paragraph.inline_events),
                    "numbering": _numbering_record(paragraph.numbering),
                }
            )
            continue
        if block.table_anchor is None:
            raise ValueError(f"body block lacks source payload: {block.anchor}")
        table = tables[block.table_anchor]
        blocks.append(
            {
                "kind": "table",
                "rows": [
                    [
                        {
                            "grid_span": cell.grid_span,
                            "vertical_merge": cell.vertical_merge,
                            "paragraphs": [
                                {
                                    "style_id": paragraphs[anchor].style,
                                    "text": paragraphs[anchor].text,
                                    "inline_events": list(
                                        paragraphs[anchor].inline_events
                                    ),
                                    "numbering": _numbering_record(
                                        paragraphs[anchor].numbering
                                    ),
                                }
                                for anchor in cell.paragraph_anchors
                            ],
                        }
                        for cell in row.cells
                    ]
                    for row in table.rows
                ],
            }
        )
    return {"normalization_version": 2, "body": blocks}


def _list_payload(paragraphs: Sequence[Paragraph]) -> dict[str, object]:
    return {
        "normalization_version": 2,
        "items": [
            {
                "paragraph_anchor": paragraph.anchor,
                "paragraph_alias": paragraph.alias,
                "locator": paragraph.locator,
                "text": paragraph.text,
                **(_numbering_record(paragraph.numbering) or {}),
            }
            for paragraph in paragraphs
            if paragraph.numbering is not None
        ],
    }


def _build_divisions(
    body_blocks: Sequence[BodyBlock],
    paragraphs: Mapping[str, Paragraph],
    tables: Mapping[str, Table],
    profile: SourceProfile,
) -> tuple[Division, ...]:
    starts: list[tuple[int, str]] = []
    for index, block in enumerate(body_blocks):
        if block.paragraph_anchor is None:
            continue
        paragraph = paragraphs[block.paragraph_anchor]
        if paragraph.style == profile.division_style:
            starts.append((index, paragraph.text))
    if not starts or starts[0][1] != profile.division_start_title:
        raise ValueError(
            f"top-level {profile.division_style} sequence does not start with "
            f"{profile.division_start_title!r}"
        )
    observed_titles = tuple(title for _, title in starts)
    if profile.division_titles is not None and observed_titles != profile.division_titles:
        raise ValueError(
            f"top-level {profile.division_style} sequence differs from the pinned source profile"
        )
    ranges = [(0, starts[0][0], "Front matter")]
    ranges.extend(
        (
            start,
            starts[index + 1][0] if index + 1 < len(starts) else len(body_blocks),
            title,
        )
        for index, (start, title) in enumerate(starts)
    )
    divisions: list[Division] = []
    for ordinal, (start, end, title) in enumerate(ranges):
        owned = tuple(body_blocks[start:end])
        body_anchors = tuple(block.anchor for block in owned)
        paragraph_anchors: list[str] = []
        table_anchors: list[str] = []
        source_units: list[str] = []
        for block in owned:
            if block.paragraph_anchor is not None:
                paragraph_anchors.append(block.paragraph_anchor)
                source_units.append(block.paragraph_anchor)
            elif block.table_anchor is not None:
                table = tables[block.table_anchor]
                table_anchors.append(table.anchor)
                source_units.append(table.anchor)
                source_units.extend(table.paragraph_anchors)
                paragraph_anchors.extend(table.paragraph_anchors)
        reader_file = (
            "00-source-envelope.md" if ordinal == 0 else f"{ordinal:02d}.md"
        )
        divisions.append(
            Division(
                ordinal=ordinal,
                title=title,
                reader_file=reader_file,
                body_anchors=body_anchors,
                paragraph_anchors=tuple(paragraph_anchors),
                table_anchors=tuple(table_anchors),
                source_unit_anchors=tuple(source_units),
            )
        )
    return tuple(divisions)


def extract_snapshot(source: bytes, profile: SourceProfile) -> Snapshot:
    document_xml = _read_member(
        source, "word/document.xml", maximum_size=16 * 1024 * 1024
    )
    numbering_xml = _read_member(
        source, "word/numbering.xml", maximum_size=1024 * 1024
    )
    styles_xml = _read_member(source, "word/styles.xml", maximum_size=4 * 1024 * 1024)
    document_root = _parse_xml(document_xml, "word/document.xml")
    numbering_root = _parse_xml(numbering_xml, "word/numbering.xml")
    styles_root = _parse_xml(styles_xml, "word/styles.xml")
    body = document_root.find(f"{W}body")
    if body is None:
        raise ValueError("document.xml has no body")

    structural_flags = {
        "tracked_insertions": len(document_root.findall(f".//{W}ins")),
        "tracked_deletions": len(document_root.findall(f".//{W}del")),
        "drawings": len(document_root.findall(f".//{W}drawing")),
        "textboxes": len(document_root.findall(f".//{W}txbxContent")),
        "math_objects": len(document_root.findall(f".//{{{M_NS}}}oMath")),
    }
    if any(structural_flags.values()):
        raise ValueError(f"unsupported or review-required content: {structural_flags}")

    paragraph_elements = tuple(document_root.iter(f"{W}p"))
    paragraph_ordinals = {
        id(paragraph): ordinal
        for ordinal, paragraph in enumerate(paragraph_elements, 1)
    }
    numbering = _paragraph_numbering(paragraph_elements, numbering_root)
    style_names = _style_names(styles_root)

    body_blocks: list[BodyBlock] = []
    paragraphs: list[Paragraph] = []
    tables: list[Table] = []
    source_sequence: list[str] = []
    top_level_paragraph_index = 0
    table_index = 0
    main_started = False

    def make_paragraph(
        element: ET.Element,
        *,
        locator: str,
        body_anchor: str,
        body_alias: str,
        scope: str,
        table_anchor: str | None = None,
        table_alias: str | None = None,
        row_index: int | None = None,
        cell_index: int | None = None,
    ) -> Paragraph:
        ordinal = paragraph_ordinals[id(element)]
        text, events = _paragraph_text(element)
        style = _style_id(element)
        return Paragraph(
            ordinal=ordinal,
            anchor=f"V90-P{ordinal:05d}",
            alias=f"XK9-P{ordinal:05d}",
            document_paragraph_index=ordinal,
            locator=locator,
            body_anchor=body_anchor,
            body_alias=body_alias,
            scope=scope,
            style=style,
            style_name=style_names.get(style),
            text=text,
            inline_events=events,
            numbering=numbering.get(id(element)),
            table_anchor=table_anchor,
            table_alias=table_alias,
            table_row_index=row_index,
            table_cell_index=cell_index,
        )

    for child in body:
        if child.tag == f"{W}sectPr":
            continue
        block_ordinal = len(body_blocks) + 1
        body_anchor = f"V90-B{block_ordinal:05d}"
        body_alias = f"XK9-B{block_ordinal:05d}"
        if child.tag == f"{W}p":
            top_level_paragraph_index += 1
            text, _ = _paragraph_text(child)
            style = _style_id(child)
            if style == profile.division_style and text == profile.division_start_title:
                main_started = True
            scope = "main_text_and_appendices" if main_started else "front_matter"
            paragraph = make_paragraph(
                child,
                locator=f"word/document.xml/body/p[{top_level_paragraph_index}]",
                body_anchor=body_anchor,
                body_alias=body_alias,
                scope=scope,
            )
            paragraphs.append(paragraph)
            source_sequence.append(paragraph.anchor)
            kind = "code_block" if paragraph.style == "CodeBlock" else "paragraph"
            body_blocks.append(
                BodyBlock(
                    ordinal=block_ordinal,
                    anchor=body_anchor,
                    alias=body_alias,
                    kind=kind,
                    scope=scope,
                    locator=paragraph.locator,
                    paragraph_anchor=paragraph.anchor,
                )
            )
            continue
        if child.tag != f"{W}tbl":
            raise ValueError(f"unsupported document body element: {child.tag}")

        table_index += 1
        table_anchor = f"V90-T{table_index:03d}"
        table_alias = f"XK9-T{table_index:03d}"
        table_locator = f"word/document.xml/body/tbl[{table_index}]"
        scope = "main_text_and_appendices" if main_started else "front_matter"
        rows: list[TableRow] = []
        table_paragraph_anchors: list[str] = []
        for row_index, row_element in enumerate(child.findall(f"{W}tr"), 1):
            row_locator = f"{table_locator}/tr[{row_index}]"
            cells: list[TableCell] = []
            for cell_index, cell_element in enumerate(row_element.findall(f"{W}tc"), 1):
                if cell_element.findall(f".//{W}tbl"):
                    raise ValueError("nested table requires explicit extractor extension")
                cell_locator = f"{row_locator}/tc[{cell_index}]"
                grid_span = _w_val(cell_element.find(f"{W}tcPr"), "gridSpan")
                grid_span_value = 1 if grid_span is None else _int_value(
                    grid_span, label="tc.gridSpan"
                )
                vertical_merge_element = cell_element.find(f"{W}tcPr/{W}vMerge")
                vertical_merge = (
                    None
                    if vertical_merge_element is None
                    else vertical_merge_element.attrib.get(f"{W}val", "continue")
                )
                cell_paragraph_anchors: list[str] = []
                for paragraph_index, paragraph_element in enumerate(
                    cell_element.findall(f"{W}p"), 1
                ):
                    paragraph = make_paragraph(
                        paragraph_element,
                        locator=f"{cell_locator}/p[{paragraph_index}]",
                        body_anchor=body_anchor,
                        body_alias=body_alias,
                        scope=scope,
                        table_anchor=table_anchor,
                        table_alias=table_alias,
                        row_index=row_index,
                        cell_index=cell_index,
                    )
                    paragraphs.append(paragraph)
                    cell_paragraph_anchors.append(paragraph.anchor)
                    table_paragraph_anchors.append(paragraph.anchor)
                if not cell_paragraph_anchors:
                    raise ValueError(f"table cell has no paragraph: {cell_locator}")
                cells.append(
                    TableCell(
                        index=cell_index,
                        locator=cell_locator,
                        grid_span=grid_span_value,
                        vertical_merge=vertical_merge,
                        paragraph_anchors=tuple(cell_paragraph_anchors),
                    )
                )
            if not cells:
                raise ValueError(f"table row has no cells: {row_locator}")
            rows.append(TableRow(index=row_index, locator=row_locator, cells=tuple(cells)))
        if not rows:
            raise ValueError(f"table has no rows: {table_locator}")
        table = Table(
            ordinal=table_index,
            anchor=table_anchor,
            alias=table_alias,
            locator=table_locator,
            body_anchor=body_anchor,
            body_alias=body_alias,
            scope=scope,
            rows=tuple(rows),
            paragraph_anchors=tuple(table_paragraph_anchors),
        )
        tables.append(table)
        source_sequence.append(table.anchor)
        source_sequence.extend(table.paragraph_anchors)
        body_blocks.append(
            BodyBlock(
                ordinal=block_ordinal,
                anchor=body_anchor,
                alias=body_alias,
                kind="table",
                scope=scope,
                locator=table_locator,
                table_anchor=table.anchor,
            )
        )

    paragraphs.sort(key=lambda paragraph: paragraph.ordinal)
    if tuple(paragraph.ordinal for paragraph in paragraphs) != tuple(
        range(1, len(paragraph_elements) + 1)
    ):
        raise ValueError("paragraph coverage or document order mismatch")
    paragraph_map = {paragraph.anchor: paragraph for paragraph in paragraphs}
    table_map = {table.anchor: table for table in tables}
    divisions = _build_divisions(body_blocks, paragraph_map, table_map, profile)
    semantic_sha256 = sha256(
        _canonical(_semantic_payload(body_blocks, paragraph_map, table_map))
    ).hexdigest()
    list_structure_sha256 = sha256(_canonical(_list_payload(paragraphs))).hexdigest()
    return Snapshot(
        raw_sha256=sha256(source).hexdigest(),
        semantic_sha256=semantic_sha256,
        list_structure_sha256=list_structure_sha256,
        xml_sha256={
            "word/document.xml": sha256(document_xml).hexdigest(),
            "word/numbering.xml": sha256(numbering_xml).hexdigest(),
            "word/styles.xml": sha256(styles_xml).hexdigest(),
        },
        structural_flags=structural_flags,
        body_blocks=tuple(body_blocks),
        paragraphs=tuple(paragraphs),
        tables=tuple(tables),
        source_unit_sequence=tuple(source_sequence),
        divisions=divisions,
    )


def validate_snapshot(snapshot: Snapshot, profile: SourceProfile) -> list[str]:
    errors: list[str] = []
    if snapshot.raw_sha256 != profile.raw_sha256:
        errors.append(f"raw SHA256 mismatch: {snapshot.raw_sha256}")
    if profile.semantic_sha256 and snapshot.semantic_sha256 != profile.semantic_sha256:
        errors.append(f"semantic SHA256 mismatch: {snapshot.semantic_sha256}")
    if (
        profile.list_structure_sha256
        and snapshot.list_structure_sha256 != profile.list_structure_sha256
    ):
        errors.append(
            f"list structure SHA256 mismatch: {snapshot.list_structure_sha256}"
        )
    checks = (
        ("body block", len(snapshot.body_blocks), profile.expected_body_blocks),
        ("paragraph", len(snapshot.paragraphs), profile.expected_paragraphs),
        (
            "non-empty paragraph",
            sum(bool(paragraph.text.strip()) for paragraph in snapshot.paragraphs),
            profile.expected_nonempty_paragraphs,
        ),
        (
            "top-level paragraph",
            sum(block.paragraph_anchor is not None for block in snapshot.body_blocks),
            profile.expected_top_level_paragraphs,
        ),
        (
            "list paragraph",
            sum(paragraph.numbering is not None for paragraph in snapshot.paragraphs),
            profile.expected_list_paragraphs,
        ),
        ("table", len(snapshot.tables), profile.expected_tables),
        ("reader unit", len(snapshot.divisions), profile.expected_reader_units),
    )
    for label, observed, expected in checks:
        if expected is not None and observed != expected:
            errors.append(f"{label} count mismatch: {observed}")
    measured_chars = sum(
        not char.isspace() for paragraph in snapshot.paragraphs for char in paragraph.text
    )
    if measured_chars != profile.expected_non_whitespace_chars:
        errors.append(f"non-whitespace count mismatch: {measured_chars}")
    expected_sequence_count = len(snapshot.paragraphs) + len(snapshot.tables)
    if len(snapshot.source_unit_sequence) != expected_sequence_count:
        errors.append(
            f"source unit sequence count mismatch: {len(snapshot.source_unit_sequence)}"
        )
    if len(set(snapshot.source_unit_sequence)) != len(snapshot.source_unit_sequence):
        errors.append("source unit sequence anchors are not unique")
    if tuple(block.ordinal for block in snapshot.body_blocks) != tuple(
        range(1, len(snapshot.body_blocks) + 1)
    ):
        errors.append("body block ordinals are not continuous")
    if tuple(paragraph.ordinal for paragraph in snapshot.paragraphs) != tuple(
        range(1, len(snapshot.paragraphs) + 1)
    ):
        errors.append("paragraph ordinals are not continuous")
    if tuple(table.ordinal for table in snapshot.tables) != tuple(
        range(1, len(snapshot.tables) + 1)
    ):
        errors.append("table ordinals are not continuous")
    division_paragraphs = tuple(
        anchor for division in snapshot.divisions for anchor in division.paragraph_anchors
    )
    if len(division_paragraphs) != len(snapshot.paragraphs) or set(
        division_paragraphs
    ) != {paragraph.anchor for paragraph in snapshot.paragraphs}:
        errors.append("reader divisions do not cover each paragraph exactly once")
    division_tables = tuple(
        anchor for division in snapshot.divisions for anchor in division.table_anchors
    )
    if len(division_tables) != len(snapshot.tables) or set(division_tables) != {
        table.anchor for table in snapshot.tables
    }:
        errors.append("reader divisions do not cover each table exactly once")
    numbered = [
        paragraph.numbering
        for paragraph in snapshot.paragraphs
        if paragraph.numbering is not None
    ]
    format_counts = {
        value: sum(item.num_fmt == value for item in numbered)
        for value in ("bullet", "decimal")
    }
    if format_counts != {"bullet": 139, "decimal": 23}:
        errors.append(f"list format counts mismatch: {format_counts}")
    if any(snapshot.structural_flags.values()):
        errors.append(f"unsupported structural flags: {snapshot.structural_flags}")
    return errors


def _matched_signals(text: str, style: str) -> tuple[tuple[str, ...], Mapping[str, tuple[str, ...]], str | None]:
    matches: dict[str, tuple[str, ...]] = {}
    domain_match = DOMAIN_ENTRY_RE.match(text) if style == "Heading2" else None
    domain_id = None if domain_match is None else domain_match.group(1)
    if style in CANDIDATE_HEADING_STYLES:
        matches["heading"] = (style,)
    if domain_id is not None:
        matches["domain_entry"] = (domain_id,)
    definition_matches = tuple(signal for signal in DEFINITION_SIGNALS if signal in text)
    if definition_matches:
        matches["definition"] = definition_matches
    variable_matches = tuple(signal for signal in VARIABLE_SIGNALS if signal in text)
    variable_tokens = tuple(dict.fromkeys(VARIABLE_TOKEN_RE.findall(text)))
    if variable_matches or variable_tokens:
        matches["variable"] = (*variable_matches, *variable_tokens)
    operator_matches = tuple(signal for signal in OPERATOR_SIGNALS if signal in text)
    if operator_matches:
        matches["operator"] = operator_matches
    constraint_matches = tuple(signal for signal in CONSTRAINT_SIGNALS if signal in text)
    if constraint_matches:
        matches["constraint"] = constraint_matches
    undefined_matches = tuple(
        signal for signal in UNDEFINED_FIELD_SIGNALS if signal in text
    )
    if undefined_matches:
        matches["undefined_field"] = undefined_matches
    kinds = tuple(kind for kind in CANDIDATE_KIND_ORDER if kind in matches)
    return kinds, matches, domain_id


def extract_candidates(snapshot: Snapshot) -> tuple[SourceCandidate, ...]:
    candidates: list[tuple[int, int, SourceCandidate]] = []
    paragraph_map = {paragraph.anchor: paragraph for paragraph in snapshot.paragraphs}
    for paragraph in snapshot.paragraphs:
        if not paragraph.text.strip() or paragraph.style == "TOCItem":
            continue
        kinds, matched_signals, domain_id = _matched_signals(
            paragraph.text, paragraph.style
        )
        if not kinds:
            continue
        candidate = SourceCandidate(
            candidate_id=f"V90-CANDIDATE-P{paragraph.ordinal:05d}",
            source_anchor=paragraph.anchor,
            source_aliases=(paragraph.alias,),
            source_unit_type="paragraph",
            source_style=paragraph.style,
            source_text=paragraph.text,
            source_anchors=(paragraph.anchor,),
            body_anchor=paragraph.body_anchor,
            source_numbering=paragraph.numbering,
            candidate_kinds=kinds,
            matched_signals=matched_signals,
            domain_id=domain_id,
        )
        candidates.append((paragraph.ordinal, 2, candidate))

    for table in snapshot.tables:
        table_text = json.dumps(
            [
                [
                    "\n".join(
                        paragraph_map[anchor].text for anchor in cell.paragraph_anchors
                    )
                    for cell in row.cells
                ]
                for row in table.rows
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        table_candidate = SourceCandidate(
            candidate_id=f"V90-CANDIDATE-T{table.ordinal:03d}",
            source_anchor=table.anchor,
            source_aliases=(table.alias,),
            source_unit_type="table",
            source_style="",
            source_text=table_text,
            source_anchors=table.paragraph_anchors,
            body_anchor=table.body_anchor,
            source_numbering=None,
            candidate_kinds=("table",),
            matched_signals={"table": (table.anchor,)},
        )
        first_table_ordinal = min(
            paragraph_map[anchor].ordinal for anchor in table.paragraph_anchors
        )
        candidates.append((first_table_ordinal, 0, table_candidate))
        for row in table.rows:
            paragraph_anchors = tuple(
                anchor for cell in row.cells for anchor in cell.paragraph_anchors
            )
            cell_texts = [
                "\n".join(paragraph_map[anchor].text for anchor in cell.paragraph_anchors)
                for cell in row.cells
            ]
            is_heading = row.index == 1
            kinds = ("heading", "table") if is_heading else ("table",)
            matched: Mapping[str, tuple[str, ...]] = {"table": (table.anchor,)}
            if is_heading:
                matched = {"heading": ("TableHead",), **matched}
            source_text = json.dumps(
                cell_texts, ensure_ascii=False, separators=(",", ":")
            )
            candidate = SourceCandidate(
                candidate_id=f"V90-CANDIDATE-T{table.ordinal:03d}-R{row.index:03d}",
                source_anchor=f"{table.anchor}-R{row.index:03d}",
                source_aliases=(f"{table.alias}-R{row.index:03d}",),
                source_unit_type="table_row",
                source_style="TableHead" if is_heading else "TableRow",
                source_text=source_text,
                source_anchors=paragraph_anchors,
                body_anchor=table.body_anchor,
                source_numbering=None,
                candidate_kinds=kinds,
                matched_signals=matched,
                source_table_anchor=table.anchor,
                source_table_row_index=row.index,
            )
            first_ordinal = min(
                paragraph_map[anchor].ordinal for anchor in paragraph_anchors
            )
            candidates.append((first_ordinal, 1, candidate))
    return tuple(candidate for _, _, candidate in sorted(candidates, key=lambda item: (item[0], item[1], item[2].candidate_id)))


def _candidate_semantic_payload(candidate: SourceCandidate) -> dict[str, object]:
    payload: dict[str, object] = {
        "source_unit_type": candidate.source_unit_type,
        "source_style": candidate.source_style,
        "source_text": candidate.source_text,
        "candidate_kinds": list(candidate.candidate_kinds),
        "matched_signals": {
            kind: list(candidate.matched_signals[kind])
            for kind in candidate.candidate_kinds
        },
        "source_undefined_fields": list(
            candidate.matched_signals.get("undefined_field", ())
        ),
        "domain_id": candidate.domain_id,
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
    profile: SourceProfile,
    *,
    ordinal: int,
    previous_candidate_id: str | None,
    next_candidate_id: str | None,
) -> dict[str, object]:
    semantic_payload = _candidate_semantic_payload(candidate)
    return {
        "schema_id": "xi-kari.v9.0.source-candidate",
        "schema_version": 2,
        "framework_version": profile.source_version,
        "framework_revision": profile.framework_revision,
        "candidate_ruleset_version": profile.candidate_ruleset_version,
        "candidate_id": candidate.candidate_id,
        "previous_candidate_id": previous_candidate_id,
        "next_candidate_id": next_candidate_id,
        "ordinal": ordinal,
        "source_anchor": candidate.source_anchor,
        "source_aliases": list(candidate.source_aliases),
        "source_anchors": list(candidate.source_anchors),
        "body_anchor": candidate.body_anchor,
        "source_span": {
            "start_anchor": candidate.source_anchors[0],
            "end_anchor": candidate.source_anchors[-1],
            "paragraph_anchors": list(candidate.source_anchors),
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


def _render_paragraph(paragraph: Paragraph) -> list[str]:
    marker = (
        f"<!-- source-paragraph:{paragraph.anchor} alias={paragraph.alias} "
        f"locator={paragraph.locator} style={paragraph.style or 'Normal'} -->"
    )
    if not paragraph.text:
        return [marker, "<!-- empty-paragraph -->", ""]
    level = {"CoverTitle": 1, "Heading1": 1, "Heading2": 2, "Heading3": 3}.get(
        paragraph.style, 0
    )
    text = paragraph.text
    if paragraph.numbering is not None:
        text = (
            "  " * paragraph.numbering.ilvl
            + paragraph.numbering.rendered_marker
            + " "
            + text
        )
    if level:
        return [marker, f"{'#' * level} {html.escape(text)}", ""]
    return [marker, f"<pre>{html.escape(text)}</pre>", ""]


def _render_table(table: Table, paragraphs: Mapping[str, Paragraph]) -> list[str]:
    lines = [
        f'<!-- source-body:{table.body_anchor} alias={table.body_alias} -->',
        f'<table data-source-table="{table.anchor}" data-source-alias="{table.alias}" data-locator="{table.locator}">',
    ]
    for row in table.rows:
        lines.append(f'<tr data-source-row="{row.index}">')
        for cell in row.cells:
            merge = "" if cell.vertical_merge is None else cell.vertical_merge
            lines.append(
                f'<td data-source-cell="{row.index},{cell.index}" '
                f'data-grid-span="{cell.grid_span}" data-vmerge="{merge}">'
            )
            for anchor in cell.paragraph_anchors:
                lines.extend(_render_paragraph(paragraphs[anchor]))
            lines.append("</td>")
        lines.append("</tr>")
    lines.extend(["</table>", ""])
    return lines


def _reader_for_division(
    division: Division,
    snapshot: Snapshot,
    profile: SourceProfile,
) -> bytes:
    paragraph_map = {paragraph.anchor: paragraph for paragraph in snapshot.paragraphs}
    table_map = {table.anchor: table for table in snapshot.tables}
    block_map = {block.anchor: block for block in snapshot.body_blocks}
    lines = [
        f"# {division.title}",
        "",
        f"Source: `{profile.source_version}`",
        f"Raw SHA256: `{snapshot.raw_sha256}`",
        f"Semantic SHA256: `{snapshot.semantic_sha256}`",
        f"List structure SHA256: `{snapshot.list_structure_sha256}`",
        "",
        "<!-- Lossless reader edition. Source anchors and aliases are coordinates, not source prose. -->",
        "",
    ]
    for body_anchor in division.body_anchors:
        block = block_map[body_anchor]
        if block.paragraph_anchor is not None:
            lines.append(
                f"<!-- source-body:{block.anchor} alias={block.alias} -->"
            )
            lines.extend(_render_paragraph(paragraph_map[block.paragraph_anchor]))
        elif block.table_anchor is not None:
            lines.extend(_render_table(table_map[block.table_anchor], paragraph_map))
    return "\n".join(lines).encode("utf-8")


def _reader_index(snapshot: Snapshot, profile: SourceProfile) -> bytes:
    lines = [
        "# Xi-Kari v9.0 lossless reader",
        "",
        f"Raw SHA256: `{snapshot.raw_sha256}`",
        f"Semantic SHA256: `{snapshot.semantic_sha256}`",
        f"List structure SHA256: `{snapshot.list_structure_sha256}`",
        "",
        "Read every unit below in order. This index never replaces the source units.",
        "",
        "| order | file | title | paragraphs | tables |",
        "| ---: | --- | --- | ---: | ---: |",
    ]
    for division in snapshot.divisions:
        lines.append(
            f"| {division.ordinal} | `{division.reader_file}` | "
            f"{division.title} | {len(division.paragraph_anchors)} | "
            f"{len(division.table_anchors)} |"
        )
    lines.extend(
        [
            "",
            f"Reader unit count is generated from the {profile.division_style} sequence.",
            "The audit directory preserves every paragraph, including empty paragraphs, and every table cell binding.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def expected_files(
    source: bytes, snapshot: Snapshot, profile: SourceProfile
) -> dict[str, bytes]:
    del source
    files: dict[str, bytes] = {}
    paragraph_records = [_paragraph_record(paragraph) for paragraph in snapshot.paragraphs]
    body_records = [_body_record(block) for block in snapshot.body_blocks]
    table_records = [_table_record(table) for table in snapshot.tables]
    files["audit/paragraphs.jsonl"] = b"".join(
        _canonical(record) for record in paragraph_records
    )
    files["audit/body-blocks.jsonl"] = b"".join(
        _canonical(record) for record in body_records
    )
    for table, record in zip(snapshot.tables, table_records, strict=True):
        files[f"audit/tables/{table.anchor}.json"] = _canonical(record)
    files["indexes/body-blocks.json"] = _canonical(body_records)
    files["indexes/tables.json"] = _canonical(table_records)
    files["indexes/headings.json"] = _canonical(
        [
            record
            for paragraph, record in zip(
                snapshot.paragraphs, paragraph_records, strict=True
            )
            if paragraph.style in INDEX_HEADING_STYLES
        ]
    )
    files["indexes/terms.json"] = _canonical(
        [
            record
            for paragraph, record in zip(
                snapshot.paragraphs, paragraph_records, strict=True
            )
            if paragraph.style in CONCEPT_STYLES
        ]
    )
    domain_entries = [
        {
            "domain_id": match.group(1),
            "source_anchor": paragraph.anchor,
            "source_alias": paragraph.alias,
            "body_anchor": paragraph.body_anchor,
            "title": paragraph.text,
        }
        for paragraph in snapshot.paragraphs
        if paragraph.style == "Heading2"
        for match in [DOMAIN_ENTRY_RE.match(paragraph.text)]
        if match is not None
    ]
    files["indexes/domain-entries.json"] = _canonical(domain_entries)
    aliases = {
        "schema_id": "xi-kari.v9.0.source-aliases",
        "schema_version": 1,
        "framework_version": profile.source_version,
        "framework_revision": profile.framework_revision,
        "source_raw_sha256": snapshot.raw_sha256,
        "body_blocks": {block.alias: block.anchor for block in snapshot.body_blocks},
        "paragraphs": {
            paragraph.alias: paragraph.anchor for paragraph in snapshot.paragraphs
        },
        "tables": {table.alias: table.anchor for table in snapshot.tables},
    }
    files["indexes/aliases.json"] = _canonical(aliases)
    files["indexes/anchors.json"] = _canonical(
        {
            "body_blocks": [block.anchor for block in snapshot.body_blocks],
            "paragraphs": [paragraph.anchor for paragraph in snapshot.paragraphs],
            "tables": [table.anchor for table in snapshot.tables],
        }
    )
    candidates = extract_candidates(snapshot)
    candidate_records = [
        _candidate_record(
            candidate,
            snapshot,
            profile,
            ordinal=index + 1,
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
    files["reader/00-index.md"] = _reader_index(snapshot, profile)
    for division in snapshot.divisions:
        files[f"reader/{division.reader_file}"] = _reader_for_division(
            division, snapshot, profile
        )

    numbered = [
        paragraph.numbering
        for paragraph in snapshot.paragraphs
        if paragraph.numbering is not None
    ]
    source_hash_paths = {
        "audit/paragraphs.jsonl",
        "audit/body-blocks.jsonl",
        "indexes/body-blocks.json",
        "indexes/tables.json",
        "indexes/aliases.json",
        *(f"audit/tables/{table.anchor}.json" for table in snapshot.tables),
    }
    candidate_kind_counts = {
        kind: sum(kind in candidate.candidate_kinds for candidate in candidates)
        for kind in CANDIDATE_KIND_ORDER
    }
    manifest = {
        "schema_id": "xi-kari.v9.0.source-manifest",
        "schema_version": 3,
        "framework_version": profile.source_version,
        "framework_revision": profile.framework_revision,
        "raw_sha256": snapshot.raw_sha256,
        "semantic_sha256": snapshot.semantic_sha256,
        "semantic_normalization_version": profile.semantic_normalization_version,
        "list_structure_sha256": snapshot.list_structure_sha256,
        "list_structure_normalization_version": profile.list_structure_normalization_version,
        "xml_sha256": dict(snapshot.xml_sha256),
        "structural_flags": dict(snapshot.structural_flags),
        "body_block_count": len(snapshot.body_blocks),
        "paragraph_count": len(snapshot.paragraphs),
        "nonempty_paragraph_count": sum(
            bool(paragraph.text.strip()) for paragraph in snapshot.paragraphs
        ),
        "empty_paragraph_count": sum(
            not paragraph.text.strip() for paragraph in snapshot.paragraphs
        ),
        "top_level_paragraph_count": sum(
            block.paragraph_anchor is not None for block in snapshot.body_blocks
        ),
        "list_paragraph_count": len(numbered),
        "list_format_counts": {
            value: sum(item.num_fmt == value for item in numbered)
            for value in ("bullet", "decimal")
        },
        "heading_count": sum(
            paragraph.style in INDEX_HEADING_STYLES for paragraph in snapshot.paragraphs
        ),
        "table_count": len(snapshot.tables),
        "non_whitespace_chars": sum(
            not char.isspace()
            for paragraph in snapshot.paragraphs
            for char in paragraph.text
        ),
        "source_unit_count": len(snapshot.source_unit_sequence),
        "source_unit_sequence": list(snapshot.source_unit_sequence),
        "source_unit_file_sha256": {
            path: sha256(files[path]).hexdigest() for path in sorted(source_hash_paths)
        },
        "index_file_sha256": {
            path: sha256(content).hexdigest()
            for path, content in sorted(files.items())
            if path.startswith("indexes/")
        },
        "alias_index_sha256": sha256(files["indexes/aliases.json"]).hexdigest(),
        "candidate_ruleset_version": profile.candidate_ruleset_version,
        "candidate_count": len(candidates),
        "candidate_count_semantics": "deterministic source-signal census under the declared ruleset; not an ontology classification or a complete or fixed concept count",
        "candidate_kind_counts": candidate_kind_counts,
        "candidate_index_sha256": sha256(candidate_index).hexdigest(),
        "domain_entry_count": len(domain_entries),
        "coordinate_contract": "V90-B addresses direct body blocks; V90-P addresses every document paragraph including empty and table paragraphs; V90-T addresses direct body tables; XK9 aliases are valid only for this raw source revision",
        "divisions": [
            {
                "ordinal": division.ordinal,
                "title": division.title,
                "reader_file": division.reader_file,
                "body_anchors": list(division.body_anchors),
                "paragraph_anchors": list(division.paragraph_anchors),
                "table_anchors": list(division.table_anchors),
                "source_unit_anchors": list(division.source_unit_anchors),
            }
            for division in snapshot.divisions
        ],
        "reader_unit_count": len(snapshot.divisions),
        "reader_units": [division.reader_file for division in snapshot.divisions],
        "sequence": [division.reader_file for division in snapshot.divisions],
        "reader_file_sha256": {
            f"reader/{division.reader_file}": sha256(
                files[f"reader/{division.reader_file}"]
            ).hexdigest()
            for division in snapshot.divisions
        },
        "reader_files": sorted(path for path in files if path.startswith("reader/")),
        "audit_files": sorted(path for path in files if path.startswith("audit/")),
        "index_files": sorted(path for path in files if path.startswith("indexes/")),
    }
    files["source-manifest.json"] = _canonical(manifest)
    return files


def _output_files(base: Path) -> tuple[dict[str, bytes], list[str]]:
    if not base.exists():
        return {}, []
    if base.is_symlink() or not base.is_dir():
        return {}, [f"unsafe source snapshot directory: {base}"]
    files: dict[str, bytes] = {}
    errors: list[str] = []
    for path in base.rglob("*"):
        if path.is_symlink():
            errors.append(f"unsafe symlink in source snapshot: {path.relative_to(base)}")
        elif path.is_file():
            files[path.relative_to(base).as_posix()] = path.read_bytes()
    return files, errors


def build(root: Path, *, check: bool, profile: SourceProfile) -> list[str]:
    source_path = profile.source_document(root)
    if not source_path.is_file() or source_path.is_symlink():
        return [f"missing or unsafe source: {source_path}"]
    source = source_path.read_bytes()
    try:
        snapshot = extract_snapshot(source, profile)
        errors = validate_snapshot(snapshot, profile)
        generated = expected_files(source, snapshot, profile)
    except (OSError, ValueError, ET.ParseError) as exc:
        return [f"cannot build {profile.source_version} source snapshot: {exc}"]
    base = profile.source_directory(root)
    actual, read_errors = _output_files(base)
    errors.extend(read_errors)
    if check:
        if set(actual) != set(generated):
            errors.append(
                "generated file set mismatch: "
                f"missing={sorted(set(generated) - set(actual))}, "
                f"extra={sorted(set(actual) - set(generated))}"
            )
        for path, expected in generated.items():
            if actual.get(path) != expected:
                errors.append(f"generated file differs: {path}")
        return errors
    if errors:
        return errors
    base.mkdir(parents=True, exist_ok=True)
    for relative, content in sorted(generated.items()):
        target = base / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    for relative in sorted(set(actual) - set(generated), reverse=True):
        (base / relative).unlink()
    for directory in sorted(
        (path for path in base.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        try:
            directory.rmdir()
        except OSError:
            pass
    return []
