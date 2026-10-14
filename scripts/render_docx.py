#!/usr/bin/env python3
"""把完整的 UTF-8 Markdown 答案导出为 Word .docx。

只用 Python 标准库：zipfile 加手写最小 OOXML 包，离线、可重复，拒绝写入技能
安装目录。支持的语法见 ``SUPPORTED``；未支持的语法保留可见原文，并把限制写进
文档末尾，同时汇总到 stdout JSON 的 ``unsupported`` 字段。段落编号刻意不用
``numbering.xml``/``numPr``，改为在文本前置项目符号或序号并递增左缩进。
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import struct
import sys
import tempfile
from xml.sax.saxutils import escape as _xml_escape
import zipfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from xikari_paths import require_external_output
finally:
    sys.path.pop(0)


SUPPORTED = '标题、段落、粗体/斜体、行内代码、有序与无序列表、引用块、围栏代码块、管道表格、分隔线、脚注、本地图片'
MAX_IMAGE_BYTES = 20 * 1024 * 1024
EMU_PER_PIXEL = 9525
MAX_IMAGE_EMU = 6 * 914400
DEFAULT_PIXELS = (480, 320)
IMAGE_MIMES = {
    '.png': ('png', 'image/png'),
    '.jpeg': ('jpeg', 'image/jpeg'),
    '.jpg': ('jpg', 'image/jpeg'),
    '.gif': ('gif', 'image/gif'),
    '.bmp': ('bmp', 'image/bmp'),
}
_CONTROL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
_HEADING = re.compile(r'^ {0,3}(#{1,6})(?:\s+|$)(.*?)\s*$')
_FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})\s*(\S*)\s*$')
_QUOTE = re.compile(r'^ {0,3}>\s?(.*)$')
_RULE = re.compile(r'^ {0,3}([-*_])(?:\s*\1){2,}\s*$')
_LIST = re.compile(r'^([ \t]*)([-+*]|\d+[.)])([ \t]+)(.*)$')
_IMAGE_LINE = re.compile(r'^\s*!\[([^\]]*)\]\(([^)]+)\)\s*$')
_FOOTNOTE_DEF = re.compile(r'^ {0,3}\[\^([^\]\n]+)\]:[ \t]?(.*)$')
_FOOTNOTE_REF = re.compile(r'\[\^([^\]\n]+)\]')


class DocxError(ValueError):
    """输入、路径或 Markdown 结构无法生成有效的 .docx。"""


def escape_text(value: str) -> str:
    """剔除 XML 非法控件字符，并转义 ``& < > "``，中文原样保留。"""
    return _xml_escape(_CONTROL.sub(' ', str(value)), {'"': '&quot;'})


def read_markdown(path: Path) -> tuple[str, bytes]:
    """按 UTF-8（容忍 BOM）读入 Markdown；含 NUL 视为非文本并报错。"""
    raw = Path(path).read_bytes()
    if b'\x00' in raw:
        raise DocxError(f'输入含 NUL 字符，不是有效的 UTF-8 文本: {path}')
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError as error:
        raise DocxError(f'输入不是有效的 UTF-8 文本: {path}') from error
    return text, raw


def split_cells(line: str) -> list[str]:
    """切分管道表格的一行，尊重 ``\\|`` 转义与行内代码。"""
    value = line.strip()
    if value.startswith('|'):
        value = value[1:]
    if value.endswith('|') and not value.endswith('\\|'):
        value = value[:-1]
    cells, current, ticks, i = [], [], False, 0
    while i < len(value):
        char = value[i]
        if char == '\\' and i + 1 < len(value):
            current.append(value[i + 1])
            i += 2
            continue
        if char == '`':
            ticks = not ticks
            current.append(char)
            i += 1
            continue
        if char == '|' and not ticks:
            cells.append(''.join(current).strip())
            current = []
        else:
            current.append(char)
        i += 1
    cells.append(''.join(current).strip())
    return cells


def _table_separator(line: str) -> bool:
    return bool('|' in line) and all(re.fullmatch(r':?-{3,}:?', cell) for cell in split_cells(line))


def _block_start(lines: list[str], index: int) -> bool:
    """判断第 index 行是否开启一个新块，供段落累积时断句。"""
    line = lines[index]
    if not line.strip():
        return True
    if _FENCE.match(line) or _HEADING.match(line) or line.strip().startswith(':::'):
        return True
    if _QUOTE.match(line) or _RULE.fullmatch(line) or _LIST.match(line):
        return True
    if _IMAGE_LINE.match(line) or _FOOTNOTE_DEF.match(line):
        return True
    if '|' in line and index + 1 < len(lines) and _table_separator(lines[index + 1]):
        return True
    return False


def parse_blocks(lines: list[str]) -> list[dict]:
    """把 Markdown 行序列解析成块列表；脚注定义单独收集为 footnote 块。"""
    blocks: list[dict] = []
    i, total = 0, len(lines)
    while i < total:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        definition = _FOOTNOTE_DEF.match(line)
        if definition:
            blocks.append({'kind': 'footnote', 'label': definition.group(1), 'text': definition.group(2).strip()})
            i += 1
            continue
        fence = _FENCE.match(line)
        if fence:
            closing = re.compile(r'^ {0,3}' + re.escape(fence.group(1)[0]) + r'{3,}\s*$')
            info = fence.group(2)
            body, i = [], i + 1
            while i < total and not closing.match(lines[i]):
                body.append(lines[i])
                i += 1
            i += 1
            if info.lower() in ('mermaid',):
                blocks.append({'kind': 'unsupported', 'text': f'```{info}\n' + '\n'.join(body),
                               'note': f'围栏代码块语言 {info} 未支持，保留原文'})
            else:
                blocks.append({'kind': 'code', 'lines': body})
            continue
        if line.strip().startswith(':::'):
            blocks.append({'kind': 'unsupported', 'text': line.strip(), 'note': '容器语法 ::: 未支持，保留原文'})
            i += 1
            continue
        heading = _HEADING.match(line)
        if heading:
            blocks.append({'kind': 'heading', 'level': len(heading.group(1)), 'text': heading.group(2)})
            i += 1
            continue
        if _RULE.fullmatch(line):
            blocks.append({'kind': 'rule'})
            i += 1
            continue
        if _QUOTE.match(line):
            quoted = []
            while i < total and _QUOTE.match(lines[i]):
                quoted.append(_QUOTE.match(lines[i]).group(1).strip())
                i += 1
            blocks.append({'kind': 'quote', 'text': ' '.join(part for part in quoted if part)})
            continue
        if '|' in line and i + 1 < total and _table_separator(lines[i + 1]):
            rows = [split_cells(line)]
            i += 2
            while i < total and lines[i].strip() and '|' in lines[i]:
                rows.append(split_cells(lines[i]))
                i += 1
            width = max(len(row) for row in rows)
            blocks.append({'kind': 'table', 'rows': [row + [''] * (width - len(row)) for row in rows]})
            continue
        item = _LIST.match(line)
        if item and not (item.group(2) in '-+*' and item.group(4).strip().startswith(('-', '*', '_'))):
            indent = len(item.group(1).expandtabs(4))
            marker = item.group(2)
            ordered = marker[0].isdigit()
            blocks.append({'kind': 'list_item', 'depth': indent // 2,
                           'bullet': marker if ordered else '•', 'text': item.group(4)})
            i += 1
            continue
        image = _IMAGE_LINE.match(line)
        if image:
            blocks.append({'kind': 'image', 'alt': image.group(1), 'dest': image.group(2).strip()})
            i += 1
            continue
        collected, i = [line.strip()], i + 1
        while i < total and not _block_start(lines, i):
            collected.append(lines[i].strip())
            i += 1
        blocks.append({'kind': 'paragraph', 'text': ' '.join(collected)})
    return blocks


def parse_inline(text: str, numbers: dict[str, int] | None = None) -> list[dict]:
    """把一行文本切成带样式的 run；粗体/斜体/行内代码/脚注上标。"""
    numbers = numbers or {}
    runs: list[dict] = []
    buffer: list[str] = []

    def flush() -> None:
        if buffer:
            runs.append({'text': ''.join(buffer), 'bold': False, 'italic': False, 'code': False, 'sup': False})
            buffer.clear()

    i, length = 0, len(text)
    while i < length:
        char = text[i]
        if char == '`':
            end = text.find('`', i + 1)
            if end != -1:
                flush()
                runs.append({'text': text[i + 1:end], 'bold': False, 'italic': False, 'code': True, 'sup': False})
                i = end + 1
                continue
        if text.startswith('[^', i):
            end = text.find(']', i + 2)
            if end != -1 and text[i + 2:end] in numbers:
                flush()
                runs.append({'text': str(numbers[text[i + 2:end]]), 'bold': False, 'italic': False,
                             'code': False, 'sup': True})
                i = end + 1
                continue
        if text.startswith('![', i):
            end = text.find('](', i + 2)
            close = text.find(')', end + 2) if end != -1 else -1
            if end != -1 and close != -1:
                alt, dest = text[i + 2:end], text[end + 2:close]
                buffer.append(f'图像：{alt or dest}')
                i = close + 1
                continue
        if text.startswith(('**', '__'), i):
            marker = text[i:i + 2]
            end = text.find(marker, i + 2)
            if end != -1 and end > i + 2:
                flush()
                runs.append({'text': text[i + 2:end], 'bold': True, 'italic': False, 'code': False, 'sup': False})
                i = end + 2
                continue
        if char in '*_':
            end = text.find(char, i + 1)
            if end != -1 and end > i + 1:
                flush()
                runs.append({'text': text[i + 1:end], 'bold': False, 'italic': True, 'code': False, 'sup': False})
                i = end + 1
                continue
        buffer.append(char)
        i += 1
    flush()
    return runs


def _run_xml(run: dict) -> str:
    props = []
    if run.get('code'):
        props.append('<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Courier New"/>')
    if run.get('bold'):
        props.append('<w:b/>')
    if run.get('italic'):
        props.append('<w:i/>')
    if run.get('sup'):
        props.append('<w:vertAlign w:val="superscript"/>')
    properties = f'<w:rPr>{"".join(props)}</w:rPr>' if props else ''
    return f'<w:r>{properties}<w:t xml:space="preserve">{escape_text(run["text"])}</w:t></w:r>'


def _paragraph_xml(runs: list[dict], style: str | None = None, indent: int | None = None,
                   border: bool = False) -> str:
    props = []
    if style:
        props.append(f'<w:pStyle w:val="{escape_text(style)}"/>')
    if indent is not None:
        props.append(f'<w:ind w:left="{int(indent)}"/>')
    if border:
        props.append('<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="999999"/></w:pBdr>')
    properties = f'<w:pPr>{"".join(props)}</w:pPr>' if props else ''
    return f'<w:p>{properties}{"".join(_run_xml(run) for run in runs)}</w:p>'


def _table_xml(rows: list[list[str]], width: int = 3000,
               numbers: dict[str, int] | None = None) -> str:
    numbers = numbers or {}
    grid = ''.join(f'<w:gridCol w:w="{width}"/>' for _ in range(len(rows[0])))
    body = []
    for index, row in enumerate(rows):
        header = index == 0
        cells = []
        for cell in row:
            runs = parse_inline(cell, numbers)
            if header:
                runs = [dict(run, bold=True) for run in runs]
            if not runs:
                runs = [{'text': '', 'bold': False, 'italic': False, 'code': False, 'sup': False}]
            cells.append(f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/></w:tcPr>'
                         + _paragraph_xml(runs, style='TableHeader' if header else None) + '</w:tc>')
        body.append(f'<w:tr>{"".join(cells)}</w:tr>')
    return ('<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="0" w:type="auto"/></w:tblPr>'
            f'<w:tblGrid>{grid}</w:tblGrid>{"".join(body)}</w:tbl>')


def _drawing_xml(rel_id: str, name: str, pixels: tuple[int, int], identifier: int) -> str:
    cx, cy = pixels[0] * EMU_PER_PIXEL, pixels[1] * EMU_PER_PIXEL
    if cx > MAX_IMAGE_EMU:
        cy = max(1, cy * MAX_IMAGE_EMU // cx)
        cx = MAX_IMAGE_EMU
    return (f'<w:p><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{identifier}" name="图像{identifier}"/>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic><pic:nvPicPr>'
            f'<pic:cNvPr id="{identifier}" name="{escape_text(name)}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')


def image_pixels(data: bytes) -> tuple[int, int]:
    """从字节头解析 PNG/JPEG/GIF/BMP 的像素尺寸；失败时回退到固定尺寸。"""
    try:
        if data[:8] == b'\x89PNG\r\n\x1a\n' and len(data) >= 24:
            return struct.unpack('>II', data[16:24])
        if data[:3] == b'GIF' and len(data) >= 10:
            return struct.unpack('<HH', data[6:10])
        if data[:2] == b'BM' and len(data) >= 26:
            return struct.unpack('<ii', data[18:26])[0:2]
        if data[:2] == b'\xff\xd8':
            i = 2
            while i + 9 < len(data):
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3):
                    height, width = struct.unpack('>HH', data[i + 5:i + 9])
                    return width, height
                if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                    i += 2
                    continue
                i += 2 + struct.unpack('>H', data[i + 2:i + 4])[0]
    except (struct.error, IndexError):
        pass
    return DEFAULT_PIXELS


def _is_remote(destination: str) -> bool:
    lowered = destination.lower()
    return lowered.startswith(('http://', 'https://', '//'))


def _resolve_image(destination: str, source_path: Path | None) -> Path:
    path = Path(destination)
    if not path.is_absolute() and source_path is not None:
        path = Path(source_path).parent / path
    return path


def _block_inline_texts(block: dict) -> list[str]:
    if block['kind'] in ('heading', 'paragraph', 'quote', 'list_item'):
        return [block['text']]
    if block['kind'] == 'table':
        return [cell for row in block['rows'] for cell in row]
    return []


def _footnote_numbers(blocks: list[dict], definitions: dict[str, str]) -> dict[str, int]:
    numbers: dict[str, int] = {}
    for block in blocks:
        for text in _block_inline_texts(block):
            for label in _FOOTNOTE_REF.findall(text):
                if label in definitions and label not in numbers:
                    numbers[label] = len(numbers) + 1
    return numbers


def build_document(source: str, title: str | None, source_path: Path | None) -> tuple[dict[str, bytes], list[str]]:
    """把 Markdown 文本渲染成 OOXML 部件；返回（部件名→字节, 未支持语法说明）。"""
    lines = source.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    blocks = parse_blocks(lines)
    definitions = {block['label']: block['text'] for block in blocks if block['kind'] == 'footnote'}
    numbers = _footnote_numbers(blocks, definitions)

    unsupported: list[str] = []
    body: list[str] = []
    media: list[tuple[str, bytes]] = []
    relationships: list[str] = []

    for block in blocks:
        kind = block['kind']
        if kind in ('footnote',):
            continue
        if kind == 'heading':
            body.append(_paragraph_xml(parse_inline(block['text'], numbers), style=f"Heading{block['level']}"))
        elif kind == 'paragraph':
            body.append(_paragraph_xml(parse_inline(block['text'], numbers)))
        elif kind == 'quote':
            body.append(_paragraph_xml(parse_inline(block['text'], numbers), style='Quote', indent=360))
        elif kind == 'rule':
            body.append(_paragraph_xml([], border=True))
        elif kind == 'list_item':
            bullet = block['bullet']
            runs = [{'text': f'{bullet} ', 'bold': False, 'italic': False, 'code': False, 'sup': False}]
            body.append(_paragraph_xml(runs + parse_inline(block['text'], numbers), style='ListParagraph',
                                       indent=360 * block['depth']))
        elif kind == 'code':
            for line in block['lines'] or ['']:
                runs = [{'text': line, 'bold': False, 'italic': False, 'code': True, 'sup': False}]
                body.append(_paragraph_xml(runs, style='Code'))
        elif kind == 'table':
            body.append(_table_xml(block['rows'], numbers=numbers))
        elif kind == 'image':
            alt, dest = block['alt'], block['dest']
            label = alt or Path(dest).name or '未命名图像'
            if _is_remote(dest):
                unsupported.append(f'远程图像未下载，正文保留说明文字：{dest}')
                body.append(_paragraph_xml([{'text': f'图像：{label}（远程图像未下载：{dest}）',
                                             'bold': False, 'italic': False, 'code': False, 'sup': False}]))
                continue
            path = _resolve_image(dest, source_path)
            try:
                data = path.read_bytes()
            except OSError:
                unsupported.append(f'本地图像无法读取，正文保留说明文字：{dest}')
                body.append(_paragraph_xml([{'text': f'图像：{label}（无法读取：{dest}）',
                                             'bold': False, 'italic': False, 'code': False, 'sup': False}]))
                continue
            suffix = path.suffix.lower()
            if suffix not in IMAGE_MIMES:
                unsupported.append(f'图像格式未支持，正文保留说明文字：{dest}')
                body.append(_paragraph_xml([{'text': f'图像：{label}（格式未支持：{dest}）',
                                             'bold': False, 'italic': False, 'code': False, 'sup': False}]))
                continue
            if len(data) > MAX_IMAGE_BYTES:
                unsupported.append(f'图像超过 20 MiB，正文保留说明文字：{dest}')
                body.append(_paragraph_xml([{'text': f'图像：{label}（超过大小上限：{dest}）',
                                             'bold': False, 'italic': False, 'code': False, 'sup': False}]))
                continue
            index = len(media) + 1
            name = f'image{index}{suffix}'
            rel_id = f'rId{index}'
            media.append((name, data))
            relationships.append(
                f'<Relationship Id="{rel_id}" Type="http://schemas.openxmlformats.org/officeDocument/'
                f'2006/relationships/image" Target="media/{escape_text(name)}"/>')
            body.append(_drawing_xml(rel_id, name, image_pixels(data), index))
        elif kind == 'unsupported':
            unsupported.append(block['note'])
            for line in block['text'].split('\n'):
                if line:
                    body.append(_paragraph_xml([{'text': line, 'bold': False, 'italic': False,
                                                 'code': False, 'sup': False}], style='Code'))

    if numbers:
        ordered = sorted(numbers.items(), key=lambda item: item[1])
        body.append(_paragraph_xml([{'text': '脚注', 'bold': False, 'italic': False, 'code': False, 'sup': False}],
                                   style='Heading1'))
        for label, number in ordered:
            runs = [{'text': f'{number}. ', 'bold': False, 'italic': False, 'code': False, 'sup': False}]
            runs += [{'text': f'[^{label}] ', 'bold': False, 'italic': False, 'code': False, 'sup': False}]
            runs += parse_inline(definitions[label], numbers)
            body.append(_paragraph_xml(runs, style='FootnoteText'))

    if unsupported:
        body.append(_paragraph_xml([{'text': '未支持语法说明', 'bold': False, 'italic': False,
                                     'code': False, 'sup': False}], style='Heading1'))
        for note in dict.fromkeys(unsupported):
            body.append(_paragraph_xml([{'text': f'本工具当前支持的 Markdown 子集：{SUPPORTED}。{note}',
                                         'bold': False, 'italic': False, 'code': False, 'sup': False}],
                                       style='FootnoteText'))

    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
                'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
                'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
                'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                f'<w:body>{"".join(body)}</w:body></w:document>')

    extensions = sorted({IMAGE_MIMES['.' + name.rsplit('.', 1)[1]][0] for name, _ in media})
    defaults = ''.join(
        f'<Default Extension="{escape_text(ext)}" ContentType="{escape_text(mime)}"/>'
        for ext, mime in ((ext, f'image/{"jpeg" if ext in ("jpg", "jpeg") else ext}') for ext in extensions))
    content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     f'{defaults}'
                     '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                     '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                     '</Types>')

    package_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                    'relationships/officeDocument" Target="word/document.xml"/>'
                    '</Relationships>')

    document_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                     '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                     f'{"".join(relationships)}</Relationships>')

    parts: dict[str, bytes] = {
        '[Content_Types].xml': content_types.encode('utf-8'),
        '_rels/.rels': package_rels.encode('utf-8'),
        'word/document.xml': document.encode('utf-8'),
        'word/_rels/document.xml.rels': document_rels.encode('utf-8'),
        'word/styles.xml': STYLES.encode('utf-8'),
    }
    for name, data in media:
        parts[f'word/media/{name}'] = data
    return parts, list(dict.fromkeys(unsupported))


def build_parts(source: str, title: str | None, source_path: Path | None) -> dict[str, bytes]:
    """纯装配入口：返回 部件名→字节；不写盘。"""
    parts, _ = build_document(source, title, source_path)
    return parts


def _same_path(first: Path, second: Path) -> bool:
    if Path(first).resolve() == Path(second).resolve():
        return True
    try:
        return Path(first).samefile(second)
    except OSError:
        return False


def write_docx(output: Path, parts: dict[str, bytes], expected: bytes | None) -> None:
    """独占锁加临时文件加原子替换地写出 .docx，拒绝覆盖他处改动。"""
    output = Path(output)
    require_external_output(output, __file__)
    require_external_output(output.with_name(output.name + '.lock'), __file__)
    resolved = output.resolve()
    require_external_output(resolved.with_name(resolved.name + '.lock'), __file__)
    if output.is_symlink():
        raise DocxError(f'输出是符号链接，拒绝替换: {output}')
    output.parent.mkdir(parents=True, exist_ok=True)
    lock = resolved.with_name(resolved.name + '.lock')
    temporary = None
    owns_lock = False
    try:
        with tempfile.NamedTemporaryFile(dir=resolved.parent, prefix='.render-docx-', suffix='.tmp',
                                         delete=False) as stream:
            temporary = Path(stream.name)
            with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
                for name in PARTS_ORDER(parts):
                    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o600 << 16
                    archive.writestr(info, parts[name])
            stream.flush()
            os.fsync(stream.fileno())
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise DocxError('输出有其他写入者或遗留写锁；本次未提交。确认写入结束并重读后再试，不自动移除锁') from error
        owns_lock = True
        os.close(descriptor)
        current = resolved.read_bytes() if resolved.exists() else None
        if current != expected:
            raise DocxError('输出已由其他工作改变，请重读后再写入')
        if expected is None:
            try:
                os.link(temporary, resolved)
            except FileExistsError as error:
                raise DocxError('输出在首次提交前已出现；本次未覆盖，请重读后再写入') from error
        else:
            os.replace(temporary, resolved)
            temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if owns_lock:
            lock.unlink(missing_ok=True)


def PARTS_ORDER(parts: dict[str, bytes]) -> list[str]:
    """固定部件顺序，保证同输入字节相同。"""
    preferred = ['[Content_Types].xml', '_rels/.rels', 'word/document.xml',
                 'word/_rels/document.xml.rels', 'word/styles.xml']
    ordered = [name for name in preferred if name in parts]
    ordered += sorted(name for name in parts if name not in preferred)
    return ordered


def resolve_title(source: str, title: str | None, source_path: Path | None) -> str:
    """标题只作元数据：显式 --title 优先，否则取首个一级标题，再无则取文件名主干。"""
    if title:
        return title
    match = re.search(r'^ {0,3}#\s+(.*?)\s*$', source, re.MULTILINE)
    if match:
        return match.group(1)
    if source_path is not None:
        return Path(source_path).stem
    return '文档'


def render_document(input_path: Path, output: Path, title: str | None = None) -> dict:
    """完整流程：读入、拒绝同路径、装配、写出。"""
    input_path, output = Path(input_path), Path(output)
    if _same_path(input_path, output):
        raise DocxError('输入与输出不能是同一个文件')
    text, raw = read_markdown(input_path)
    parts, unsupported = build_document(text, title, input_path)
    write_docx(output, parts, None)
    return {'output': str(output.resolve()), 'source_bytes': len(raw),
            'docx_bytes': output.stat().st_size, 'renderer': 'python-standard-library',
            'offline': True, 'title': resolve_title(text, title, input_path), 'unsupported': unsupported}


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='把完整的 UTF-8 Markdown 答案导出为 Word .docx。')
    parser.add_argument('input', type=Path, help='完整 UTF-8 Markdown 文件')
    parser.add_argument('--output', '-o', type=Path, required=True, help='输出的 .docx 路径')
    parser.add_argument('--title', help='文档标题；不改变正文内容')
    args = parser.parse_args(argv)
    try:
        summary = render_document(args.input, args.output, args.title)
        print(json.dumps(summary, ensure_ascii=False))
        return 0
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as error:
        print(f'DOCX 生成失败：{error}', file=sys.stderr)
        return 2


STYLES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
          '<w:docDefaults><w:rPrDefault><w:rPr></w:rPr></w:rPrDefault>'
          '<w:pPrDefault><w:pPr></w:pPr></w:pPrDefault></w:docDefaults>'
          '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/>'
          '<w:pPr><w:spacing w:after="120" w:line="276" w:lineRule="auto"/></w:pPr></w:style>'
          + ''.join(
              f'<w:style w:type="paragraph" w:styleId="Heading{level}"><w:name w:val="heading {level}"/>'
              f'<w:basedOn w:val="Normal"/><w:next w:val="Normal"/>'
              f'<w:pPr><w:outlineLvl w:val="{level - 1}"/></w:pPr>'
              f'<w:rPr><w:b/><w:sz w:val="{max(22, 40 - level * 2)}"/></w:rPr></w:style>'
              for level in range(1, 7))
          + '<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/>'
          '<w:basedOn w:val="Normal"/>'
          '<w:pPr><w:spacing w:after="40"/><w:contextualSpacing/></w:pPr></w:style>'
          '<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/>'
          '<w:basedOn w:val="Normal"/>'
          '<w:pPr><w:pBdr><w:left w:val="single" w:sz="12" w:space="8" w:color="AAAAAA"/></w:pBdr>'
          '<w:spacing w:before="80" w:after="80"/></w:pPr>'
          '<w:rPr><w:i/><w:color w:val="555555"/></w:rPr></w:style>'
          '<w:style w:type="paragraph" w:styleId="Code"><w:name w:val="Code"/>'
          '<w:basedOn w:val="Normal"/>'
          '<w:pPr><w:spacing w:before="0" w:after="0"/><w:contextualSpacing/>'
          '<w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/></w:pPr>'
          '<w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Courier New"/>'
          '<w:sz w:val="20"/></w:rPr></w:style>'
          '<w:style w:type="paragraph" w:styleId="TableHeader"><w:name w:val="Table Header"/>'
          '<w:basedOn w:val="Normal"/>'
          '<w:pPr><w:spacing w:before="0" w:after="0"/></w:pPr>'
          '<w:rPr><w:b/></w:rPr></w:style>'
          '<w:style w:type="paragraph" w:styleId="FootnoteRef"><w:name w:val="Footnote Reference"/>'
          '<w:basedOn w:val="Normal"/><w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>'
          '<w:style w:type="paragraph" w:styleId="FootnoteText"><w:name w:val="Footnote Text"/>'
          '<w:basedOn w:val="Normal"/>'
          '<w:pPr><w:spacing w:before="0" w:after="40"/></w:pPr>'
          '<w:rPr><w:sz w:val="18"/></w:rPr></w:style>'
          '<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/>'
          '<w:tblPr><w:tblBorders>'
          '<w:top w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
          '<w:left w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
          '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
          '<w:right w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
          '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
          '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
          '</w:tblBorders></w:tblPr></w:style>'
          '</w:styles>')


if __name__ == '__main__':
    raise SystemExit(main())
