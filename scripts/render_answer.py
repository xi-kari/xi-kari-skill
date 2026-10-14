"""Render UTF-8 Markdown as a self-contained, offline Chinese reading document.

Uses only Python's standard library. Supports headings, paragraphs, emphasis,
links, local images, nested lists, quotes, pipe tables, footnotes, and code.
Explicit formulas use bundled KaTeX in the generated browser document.
Other Markdown extensions remain literal text; the original bytes are downloadable.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import ntpath
import os
from pathlib import Path, PureWindowsPath
import re
import sys
import unicodedata
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


ASSETS = Path(__file__).resolve().parents[1] / 'assets'
HEADING = re.compile(r'^ {0,3}(#{1,6})(?:\s+|$)(.*?)\s*$')
FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})([^\n]*)$')
LIST = re.compile(r'^( {0,3})([-+*]|\d+[.)])([ \t]+)(.*)$')
REFERENCE = re.compile(r'^ {0,3}\[([^]\n]+)\]:\s*(?:<([^>]+)>|(\S+))(?:\s+[\"\x27](.*)[\"\x27])?\s*$')
CLAUSE = re.compile(r'^\*\*(第[一二三四五六七八九十百零〇两\d]+条[\s\u3000].+?)\*\*$')
FOOTNOTE = re.compile(r'^ {0,3}\[\^([^]\n]+)\]:[ \t]?(.*)$')


def escape(value: str) -> str:
    return html.escape(value, quote=True)


def safe_url(value: str) -> bool:
    normalized = html.unescape(value).strip()
    for _ in range(3):
        normalized = unquote(normalized)
    normalized = re.sub(r'[\x00-\x20\x7f]+', '', normalized)
    if re.match(r'^[a-zA-Z]:[\\/]', normalized):
        return True
    try:
        return urlsplit(normalized).scheme.lower() in ('', 'http', 'https', 'mailto', 'file')
    except ValueError:
        return False


def split_cells(line: str) -> list[str]:
    value = line.strip()
    if value.startswith('|'):
        value = value[1:]
    if value.endswith('|') and not value.endswith('\\|'):
        value = value[:-1]
    cells, current, ticks, i = [], [], '', 0
    while i < len(value):
        char = value[i]
        if char == '\\' and i + 1 < len(value):
            current.extend(value[i:i + 2])
            i += 2
            continue
        if char == '`':
            end = i
            while end < len(value) and value[end] == '`':
                end += 1
            run = value[i:end]
            ticks = '' if ticks == run else (run if not ticks else ticks)
            current.append(run)
            i = end
            continue
        if char == '|' and not ticks:
            cells.append(''.join(current).strip())
            current = []
        else:
            current.append(char)
        i += 1
    cells.append(''.join(current).strip())
    return cells


def table_separator(line: str) -> bool:
    return bool('|' in line and all(re.fullmatch(r':?-{3,}:?', cell) for cell in split_cells(line)))


class MarkdownReader:
    def __init__(self, source_path: Path):
        self.source_path = source_path
        self.headings: list[tuple[int, str, str]] = []
        self.fragments: dict[str, str] = {}
        self.references: dict[str, str] = {}
        self.notes: set[str] = set()
        self.anchor_counts: dict[str, int] = {}
        self.footnotes: dict[str, tuple[str, list[str]]] = {}
        self.footnote_numbers: dict[str, int] = {}
        self.footnote_refs: dict[str, list[str]] = {}
        self.has_math = False
        self.label_mode = False

    def anchor(self, level: int, text: str) -> str:
        self.label_mode = True
        try:
            plain = html.unescape(re.sub(r'<[^>]*>', '', self.inline(re.sub(r'\[\^[^]]+\]', '', text))))
        finally:
            self.label_mode = False
        identity = unicodedata.normalize('NFC', re.sub(r'\s+', ' ', plain).strip())
        base = 'section-' + hashlib.sha256(identity.encode('utf-8')).hexdigest()[:16]
        count = self.anchor_counts.get(base, 0) + 1
        self.anchor_counts[base] = count
        anchor = base if count == 1 else f'{base}-{count}'
        self.headings.append((level, anchor, plain))
        slug = re.sub(r'[^\w\-\s]', '', plain.lower()).strip().replace(' ', '-')
        self.fragments.setdefault(slug, anchor)
        self.fragments.setdefault(plain, anchor)
        return anchor

    def heading_attributes(self, anchor: str, level: int) -> str:
        plain = self.headings[-1][2]
        return f'id="{anchor}" data-reader-section="{level}" data-section-title="{escape(plain)}" tabindex="-1"'

    def legacy_anchor(self) -> str:
        return f'<span class="legacy-anchor" id="section-{len(self.headings)}" aria-hidden="true"></span>'

    def math(self, tex: str, raw: str, display: bool = False) -> str:
        if self.label_mode:
            return escape(raw)
        if len(tex) > 10000:
            self.notes.add('一条公式超过 10000 字符，已保留原式，未执行公式排版。')
            return escape(raw)
        self.has_math = True
        tag = 'div' if display else 'span'
        return f'<{tag} class="reader-math{ " math-display" if display else ""}" data-tex="{escape(tex)}" data-math-source="{escape(raw)}" data-display="{str(display).lower()}"><span class="math-source">{escape(raw)}</span></{tag}>'

    def footnote_reference(self, label: str) -> str:
        key = label.casefold()
        if self.label_mode or key not in self.footnotes:
            return escape('[^' + label + ']')
        number = self.footnote_numbers.setdefault(key, len(self.footnote_numbers) + 1)
        identifier = hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]
        references = self.footnote_refs.setdefault(key, [])
        reference = f'fnref-{identifier}-{len(references) + 1}'
        references.append(reference)
        return f'<sup class="footnote-ref" data-footnote-source="{escape("[^" + label + "]")}"><a id="{reference}" href="#fn-{identifier}" role="doc-noteref" aria-label="脚注 {number}">{number}</a></sup>'

    def extract_footnotes(self, lines: list[str]) -> list[str]:
        remaining, i, fence = [], 0, None
        while i < len(lines):
            line = lines[i]
            marker = FENCE.match(line)
            if fence:
                remaining.append(line)
                if re.fullmatch(r' {0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}\s*', line):
                    fence = None
                i += 1
                continue
            if marker:
                fence = marker.group(1)
            definition = FOOTNOTE.match(line) if not marker else None
            if not definition:
                remaining.append(line); i += 1; continue
            label, first = definition.groups()
            key = label.casefold()
            if key in self.footnotes:
                self.notes.add('重复的脚注定义保留原文；引用使用首次定义。')
                remaining.append(line); i += 1; continue
            content = [first]; i += 1
            while i < len(lines):
                if lines[i].startswith(('    ', '\t')):
                    content.append(lines[i][1:] if lines[i].startswith('\t') else lines[i][4:]); i += 1
                elif not lines[i].strip() and i + 1 < len(lines) and lines[i + 1].startswith(('    ', '\t')):
                    content.append(''); i += 1
                else:
                    break
            self.footnotes[key] = (label, content)
            remaining.append('')
        return remaining

    def render_footnotes(self) -> str:
        if not self.footnotes:
            return ''
        order = list(self.footnote_numbers) + [key for key in self.footnotes if key not in self.footnote_numbers]
        for key in order:
            self.footnote_numbers.setdefault(key, len(self.footnote_numbers) + 1)
        bodies = {key: self.blocks(self.footnotes[key][1]) for key in order}
        items = []
        for key in order:
            identifier = hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]
            references = self.footnote_refs.get(key, [])
            back = ' '.join(f'<a class="footnote-backref" href="#{reference}" aria-label="返回脚注 {self.footnote_numbers[key]} 的第 {index} 处引用">返回引用 {index}</a>' for index, reference in enumerate(references, 1))
            unused = f'<p class="footnote-unused">{escape("[^" + self.footnotes[key][0] + "]")}（正文未引用）</p>' if not references else ''
            position = '脚注 [^' + self.footnotes[key][0] + ']'
            items.append(f'<li id="fn-{identifier}" data-section-title="{escape(position)}" tabindex="-1">{unused}{bodies[key]}<p class="footnote-returns">{back}</p></li>')
        self.headings.append((2, 'reader-footnotes', '脚注'))
        return '<section id="reader-footnotes" data-reader-section="2" data-section-title="脚注" class="footnotes" role="doc-endnotes" aria-label="脚注" tabindex="-1"><h2>脚注</h2><ol>' + ''.join(items) + '</ol></section>'

    def image(self, alt: str, destination: str) -> str:
        label = re.sub(r'[*`_]', '', alt).strip()
        if not label:
            label = '图像：' + (Path(destination).name or '未命名图像')
            self.notes.add('有图像未提供替代文字，已用文件名标明；阅读时请结合正文。')
        try:
            parts = urlsplit(destination)
            windows_path = bool(re.match(r'^[A-Za-z]:[\\/]', destination))
            if (parts.scheme not in ('', 'file') and not windows_path) or destination.startswith('//'):
                raise ValueError('远程图像未下载，离线保留说明与地址')
            raw_path = unquote(parts.path) if parts.scheme == 'file' else unquote(destination)
            if parts.scheme == 'file' and re.match(r'^/[A-Za-z]:/', raw_path):
                raw_path = raw_path[1:]
            path = Path(raw_path)
            if not path.is_absolute():
                path = self.source_path.parent / path
            data = path.read_bytes()
            if len(data) > 20 * 1024 * 1024:
                raise ValueError('图像超过 20 MiB，保留说明与路径')
            suffix = path.suffix.lower()
            mimes = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml'}
            if suffix not in mimes:
                raise ValueError('此图像格式暂不内嵌，保留说明与路径')
            if suffix == '.svg':
                if re.search(br'<!DOCTYPE|<!ENTITY', data, re.I):
                    raise ValueError('SVG 含外部实体声明，未内嵌')
                root = ET.fromstring(data)
                if root.tag.split('}')[-1] != 'svg':
                    raise ValueError('SVG 根元素无效，未内嵌')
                for element in root.iter():
                    name = element.tag.split('}')[-1].lower()
                    if name in ('script', 'foreignobject', 'iframe', 'object', 'embed', 'audio', 'video', 'style'):
                        raise ValueError('SVG 含主动内容或样式块，未内嵌')
                    for key, value in element.attrib.items():
                        key = key.split('}')[-1].lower()
                        if key.startswith('on') or (key in ('href', 'src') and not value.startswith('#')) or re.search(r'url\s*\(\s*[\"\x27]?(?!#)', value, re.I):
                            raise ValueError('SVG 含外部引用或主动属性，未内嵌')
            encoded = base64.b64encode(data).decode('ascii')
            return f'<img src="data:{mimes[suffix]};base64,{encoded}" alt="{escape(label)}" loading="lazy" decoding="async">'
        except (OSError, ValueError, ET.ParseError) as error:
            explanation = str(error) if isinstance(error, ValueError) else '本地图像无法读取，保留说明与路径'
            self.notes.add(explanation)
            return f'<span class="image-fallback" role="img" aria-label="{escape(label)}">{escape(label)} <span>（{escape(explanation)}：{escape(destination)}）</span></span>'

    def link(self, label: str, destination: str) -> str:
        if not safe_url(destination):
            self.notes.add('危险链接协议已停用，链接文字与原地址仍保留。')
            return f'<span class="disabled-link">{self.inline(label)}（{escape(destination)}）</span>'
        path_and_query, fragment_mark, fragment = destination.partition('#')
        path, query_mark, query = path_and_query.partition('?')
        decoded_path = unquote(path)
        windows_path = PureWindowsPath(decoded_path)
        suffix = (query_mark + query if query_mark else '') + (fragment_mark + fragment if fragment_mark else '')
        if windows_path.is_absolute():
            destination = PureWindowsPath(ntpath.normpath(decoded_path)).as_uri() + suffix
        elif not urlsplit(destination).scheme and not destination.startswith('#') and path:
            base = PureWindowsPath(self.source_path.parent)
            if base.is_absolute():
                destination = PureWindowsPath(ntpath.normpath(str(base / decoded_path))).as_uri() + suffix
            else:
                destination = Path(os.path.abspath(self.source_path.parent / decoded_path)).as_uri() + suffix
        return f'<a href="{escape(destination)}" rel="noopener noreferrer">{self.inline(label)}</a>'

    @staticmethod
    def bracket_end(text: str, start: int, opening: str, closing: str) -> int:
        depth, i = 1, start + 1
        while i < len(text):
            if text[i] == '\\':
                i += 2
                continue
            if text[i] == opening:
                depth += 1
            elif text[i] == closing:
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return -1

    def inline(self, text: str, depth: int = 0) -> str:
        if depth > 12:
            return escape(text)
        result, i = [], 0
        while i < len(text):
            if text.startswith('\\(', i):
                end = text.find('\\)', i + 2)
                if end >= 0:
                    result.append(self.math(text[i + 2:end], text[i:end + 2])); i = end + 2; continue
            if text[i] == '\\' and i + 1 < len(text) and text[i + 1] in r'\`*_{}[]()#+-.!|>~$':
                result.append(escape(text[i + 1])); i += 2; continue
            if text[i] == '`':
                run = re.match(r'`+', text[i:]).group()
                end = text.find(run, i + len(run))
                if end >= 0:
                    code = text[i + len(run):end].replace('\n', ' ')
                    if code.startswith(' ') and code.endswith(' ') and code.strip():
                        code = code[1:-1]
                    result.append('<code>' + escape(code) + '</code>'); i = end + len(run); continue
            if text[i] == '$' and not text.startswith('$$', i) and (i == 0 or text[i - 1] not in '$0123456789'):
                close = re.search(r'(?<![\\$])\$(?!\$)', text[i + 1:])
                if close:
                    end = i + 1 + close.start()
                    tex = text[i + 1:end]
                    numeric = bool(tex and tex[0].isdigit())
                    explicit = bool(re.search(r'[\\^_+=<>*/{}]', tex))
                    if tex and not tex[0].isspace() and not tex[-1].isspace() and '`' not in tex and not text[end + 1:end + 2].isdigit() and (not numeric or explicit):
                        result.append(self.math(tex, text[i:end + 1])); i = end + 1; continue
            if text.startswith('[^', i):
                end = text.find(']', i + 2)
                if end >= 0:
                    result.append(self.footnote_reference(text[i + 2:end])); i = end + 1; continue
            is_image = text.startswith('![', i)
            if is_image or text[i] == '[':
                start = i + 1 if is_image else i
                end = self.bracket_end(text, start, '[', ']')
                destination, final = None, end + 1
                if end >= 0 and text[end + 1:end + 2] == '(':
                    close = self.bracket_end(text, end + 1, '(', ')')
                    if close >= 0:
                        target = text[end + 2:close].strip()
                        match = re.fullmatch(r'(?:<([^>]+)>|(.*?))(?:\s+[\"\x27].*[\"\x27])?', target)
                        destination = (match.group(1) or match.group(2)) if match else target
                        final = close + 1
                elif end >= 0:
                    reference = text[start + 1:end]
                    if text[end + 1:end + 2] == '[':
                        close = text.find(']', end + 2)
                        if close >= 0:
                            reference = text[end + 2:close] or reference
                            final = close + 1
                    destination = self.references.get(reference.casefold())
                if destination is not None:
                    label = text[start + 1:end]
                    result.append(self.image(label, destination) if is_image else self.link(label, destination))
                    i = final; continue
            matched = False
            for token, tag in (('**', 'strong'), ('__', 'strong'), ('~~', 'del'), ('*', 'em'), ('_', 'em')):
                if text.startswith(token, i) and (token[0] != '_' or i == 0 or not text[i - 1].isalnum()):
                    end = text.find(token, i + len(token))
                    if end > i + len(token) and not text[i + len(token)].isspace():
                        result.append(f'<{tag}>' + self.inline(text[i + len(token):end], depth + 1) + f'</{tag}>')
                        i = end + len(token); matched = True; break
            if matched:
                continue
            if text[i] == '<':
                match = re.match(r'<((?:https?://|mailto:)[^<>\s]+)>', text[i:])
                if match:
                    result.append(self.link(match.group(1), match.group(1))); i += len(match.group()); continue
            if text[i] == '&':
                match = re.match(r'&(?:#[0-9]+|#x[0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]+);', text[i:])
                if match:
                    result.append(escape(html.unescape(match.group()))); i += len(match.group()); continue
            result.append(escape(text[i])); i += 1
        return ''.join(result)

    @staticmethod
    def block_start(line: str) -> bool:
        return bool(HEADING.match(line) or FENCE.match(line) or LIST.match(line) or re.match(r'^ {0,3}(?:>|\$\$|\\\[)', line) or re.fullmatch(r' {0,3}(?:\*\s*){3,}| {0,3}(?:-\s*){3,}| {0,3}(?:_\s*){3,}', line))

    def blocks(self, lines: list[str]) -> str:
        output, i = [], 0
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1; continue
            fence = FENCE.match(line)
            if fence:
                marker, language = fence.group(1), fence.group(2).strip()
                code = []; i += 1
                while i < len(lines) and not re.fullmatch(r' {0,3}' + re.escape(marker[0]) + '{' + str(len(marker)) + r',}\s*', lines[i]):
                    code.append(lines[i]); i += 1
                if i < len(lines):
                    i += 1
                body = '<pre><code>' + escape('\n'.join(code)) + '</code></pre>'
                if language.casefold() == 'mermaid':
                    self.notes.add('Mermaid 保留源码与文字说明，未加载在线绘图服务。')
                    body = '<figure class="diagram-source"><figcaption>Mermaid 图示源码 · 离线保留，未渲染为图</figcaption>' + body + '</figure>'
                elif language:
                    body = '<figure class="code-block"><figcaption>' + escape(language) + '</figcaption>' + body + '</figure>'
                output.append(body); continue
            math_open = re.match(r'^ {0,3}(\$\$|\\\[)(.*)$', line)
            if math_open:
                opening, tail = math_open.groups()
                closing = '$$' if opening == '$$' else '\\]'
                if tail.rstrip().endswith(closing):
                    tex = tail.rstrip()[:-len(closing)]
                    output.append(self.math(tex, line, True)); i += 1; continue
                if not tail.strip():
                    end = next((j for j in range(i + 1, len(lines)) if lines[j].strip() == closing), None)
                    if end is not None:
                        output.append(self.math('\n'.join(lines[i + 1:end]), '\n'.join(lines[i:end + 1]), True)); i = end + 1; continue
            heading = HEADING.match(line)
            if heading:
                level = len(heading.group(1))
                text = re.sub(r'\s+#+\s*$', '', heading.group(2))
                anchor = self.anchor(level, text)
                output.append(self.legacy_anchor() + f'<h{level} {self.heading_attributes(anchor, level)}>{self.inline(text)}</h{level}>'); i += 1; continue
            if i + 1 < len(lines) and re.fullmatch(r' {0,3}(?:=+|-+)\s*', lines[i + 1]):
                level = 1 if lines[i + 1].lstrip().startswith('=') else 2
                anchor = self.anchor(level, line)
                output.append(self.legacy_anchor() + f'<h{level} {self.heading_attributes(anchor, level)}>{self.inline(line)}</h{level}>'); i += 2; continue
            if re.fullmatch(r' {0,3}(?:\*\s*){3,}| {0,3}(?:-\s*){3,}| {0,3}(?:_\s*){3,}', line):
                output.append('<hr>'); i += 1; continue
            if re.match(r'^ {0,3}>', line):
                quote = []
                while i < len(lines) and re.match(r'^ {0,3}>', lines[i]):
                    quote.append(re.sub(r'^ {0,3}> ?', '', lines[i])); i += 1
                output.append('<blockquote>' + self.blocks(quote) + '</blockquote>'); continue
            item = LIST.match(line)
            if item:
                base = len(item.group(1)); ordered = item.group(2)[0].isdigit()
                tag = 'ol' if ordered else 'ul'
                start = ' start="' + str(int(item.group(2)[:-1])) + '"' if ordered else ''
                items = []
                while i < len(lines):
                    item = LIST.match(lines[i])
                    if not item or len(item.group(1)) != base or item.group(2)[0].isdigit() != ordered:
                        break
                    content_indent = len(item.group(1)) + len(item.group(2)) + len(item.group(3))
                    content = [item.group(4)]; i += 1
                    while i < len(lines):
                        candidate = LIST.match(lines[i])
                        indent = len(lines[i]) - len(lines[i].lstrip(' '))
                        if candidate and len(candidate.group(1)) == base:
                            break
                        if lines[i].strip() and indent <= base and (self.block_start(lines[i]) or not content[-1].strip()):
                            break
                        if not lines[i].strip():
                            if i + 1 == len(lines) or (lines[i + 1].strip() and len(lines[i + 1]) - len(lines[i + 1].lstrip(' ')) <= base):
                                i += 1; break
                            content.append(''); i += 1; continue
                        content.append(lines[i][min(content_indent, indent):]); i += 1
                    items.append('<li>' + self.blocks(content) + '</li>')
                output.append(f'<{tag}{start}>' + ''.join(items) + f'</{tag}>'); continue
            if i + 1 < len(lines) and '|' in line and table_separator(lines[i + 1]):
                header = split_cells(line); alignment = split_cells(lines[i + 1]); rows = []; i += 2
                while i < len(lines) and lines[i].strip() and '|' in lines[i]:
                    rows.append(split_cells(lines[i])); i += 1
                columns = max([len(header)] + [len(row) for row in rows])
                def cells(row, tag):
                    result = []
                    for column in range(columns):
                        align = alignment[column] if column < len(alignment) else ''
                        direction = 'center' if align.startswith(':') and align.endswith(':') else ('right' if align.endswith(':') else 'left')
                        text = row[column] if column < len(row) else ''
                        scope = ' scope="col"' if tag == 'th' else ''
                        result.append(f'<{tag}{scope} class="align-{direction}">{self.inline(text)}</{tag}>')
                    return ''.join(result)
                output.append('<div class="table-scroll" tabindex="0" role="region" aria-label="表格，可横向滚动"><table><thead><tr>' + cells(header, 'th') + '</tr></thead><tbody>' + ''.join('<tr>' + cells(row, 'td') + '</tr>' for row in rows) + '</tbody></table></div>'); continue
            if line.startswith('    ') or line.startswith('\t'):
                code = []
                while i < len(lines) and (lines[i].startswith(('    ', '\t')) or not lines[i].strip()):
                    code.append(lines[i][1:] if lines[i].startswith('\t') else lines[i][4:]); i += 1
                output.append('<pre><code>' + escape('\n'.join(code).rstrip('\n')) + '</code></pre>'); continue
            clause = CLAUSE.match(line)
            if clause:
                anchor = self.anchor(3, clause.group(1))
                output.append(self.legacy_anchor() + f'<p class="clause" {self.heading_attributes(anchor, 3)}>{self.inline(line)}</p>'); i += 1; continue
            paragraph = [line]; i += 1
            while i < len(lines) and lines[i].strip() and not self.block_start(lines[i]) and not CLAUSE.match(lines[i]):
                if i + 1 < len(lines) and (table_separator(lines[i + 1]) or re.fullmatch(r' {0,3}(?:=+|-+)\s*', lines[i + 1])):
                    break
                paragraph.append(lines[i]); i += 1
            rendered = []
            for index, part in enumerate(paragraph):
                hard = part.endswith('  ') or part.endswith('\\')
                rendered.append(self.inline(part.rstrip() if part.endswith('  ') else (part[:-1] if part.endswith('\\') else part)))
                if index + 1 < len(paragraph):
                    rendered.append('<br>\n' if hard else '\n')
            output.append('<p>' + ''.join(rendered) + '</p>')
        return '\n'.join(output)

    def render(self, source: str) -> str:
        lines = self.extract_footnotes(source.lstrip('\ufeff').splitlines())
        for line in lines:
            reference = REFERENCE.match(line)
            if reference and not reference.group(1).startswith('^'):
                self.references[reference.group(1).casefold()] = reference.group(2) or reference.group(3)
        if re.search(r'^\s*:::', source, re.M):
            self.notes.add('未支持的扩展语法保留为原文；可下载完整 Markdown。')
        body = self.blocks(lines) + self.render_footnotes()
        for old, new in self.fragments.items():
            body = body.replace('href="#' + escape(old) + '"', 'href="#' + new + '"')
        return body


def katex_assets() -> tuple[str, str]:
    directory = ASSETS / 'vendor' / 'katex'
    javascript = (directory / 'katex.min.js').read_text(encoding='utf-8')
    css = (directory / 'katex.min.css').read_text(encoding='utf-8')
    def embed_font(match: re.Match) -> str:
        name = match.group(1)
        if not re.fullmatch(r'fonts/[A-Za-z0-9_-]+\.woff2', name):
            raise ValueError('KaTeX 字体路径无效')
        data = base64.b64encode((directory / name).read_bytes()).decode('ascii')
        return f'src:url("data:font/woff2;base64,{data}") format("woff2")'
    css = re.sub(r'src:url\((fonts/[^)]+\.woff2)\)[^;}]*', embed_font, css)
    if re.search(r'url\((?![\"\x27]?data:)', css):
        raise ValueError('KaTeX 样式仍有未内嵌资源')
    if '</script' in javascript.lower() or '</style' in css.lower():
        raise ValueError('KaTeX 资产包含无法安全内嵌的结束标签')
    return javascript, css


def render_document(source: str, *, title: str | None = None, source_path: Path | None = None, source_bytes: bytes | None = None) -> str:
    source_path = Path(source_path or Path.cwd() / 'answer.md').resolve()
    reader = MarkdownReader(source_path)
    body = reader.render(source)
    title = title or next((text for level, _, text in reader.headings if level == 1), source_path.stem)
    toc = ''.join(f'<li class="toc-level-{level}"><a href="#{anchor}">{escape(text)}</a></li>' for level, anchor, text in reader.headings)
    if not toc:
        toc = '<li><a href="#document">阅读全文</a></li>'
    css = (ASSETS / 'reader.css').read_text(encoding='utf-8')
    javascript = (ASSETS / 'reader.js').read_text(encoding='utf-8')
    scripts = [javascript]
    if reader.has_math:
        try:
            math_script, math_css = katex_assets()
            scripts.insert(0, math_script)
            css = math_css + '\n' + css
        except (OSError, UnicodeError, ValueError):
            reader.notes.add('公式排版资源不可用，已保留完整原式；其他阅读功能照常可用。')
    script_hashes = ' '.join("'sha256-" + base64.b64encode(hashlib.sha256(script.encode('utf-8')).digest()).decode('ascii') + "'" for script in scripts)
    style_hash = base64.b64encode(hashlib.sha256(css.encode('utf-8')).digest()).decode('ascii')
    original = base64.b64encode(source_bytes if source_bytes is not None else source.encode('utf-8')).decode('ascii')
    notes = ''.join('<li>' + escape(note) + '</li>' for note in sorted(reader.notes))
    note_html = '<details class="render-notes"><summary>阅读格式说明</summary><ul>' + notes + '</ul></details>' if notes else ''
    math_enabled = len(scripts) > 1
    style_attributes = "'unsafe-inline'" if math_enabled else "'none'"
    font_sources = 'data:' if math_enabled else "'none'"
    csp = f"default-src 'none'; script-src {script_hashes}; script-src-attr 'none'; style-src 'sha256-{style_hash}'; style-src-elem 'sha256-{style_hash}'; style-src-attr {style_attributes}; img-src data:; connect-src 'none'; font-src {font_sources}; object-src 'none'; base-uri 'none'; form-action 'none'"
    script_html = ''.join('<script>' + script + '</script>' for script in scripts)
    section_options = ''.join(f'<option value="{anchor}">{escape(text)}</option>' for _, anchor, text in reader.headings)
    return f'''<!doctype html>
<html lang="zh-CN" data-theme="paper" data-font="medium">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{escape(csp)}">
<meta name="color-scheme" content="light dark"><title>{escape(title)}</title>
<style>{css}</style></head>
<body>
<a class="skip-link" href="#document">跳至正文</a>
<header class="reader-toolbar" aria-label="阅读工具">
<button id="nav-toggle" type="button" aria-controls="contents" aria-expanded="false">目录</button>
<div class="search-control"><label for="reader-search">搜索全文</label><input id="reader-search" type="search" placeholder="输入文字定位" autocomplete="off" spellcheck="false"><span id="search-status" role="status" aria-live="polite">保留全部正文</span></div>
<div class="search-buttons"><button id="previous-match" type="button" disabled aria-label="上一处匹配">上一处</button><button id="next-match" type="button" disabled aria-label="下一处匹配">下一处</button></div>
<div class="reading-controls"><button id="quote-question" type="button" aria-controls="question-panel" aria-expanded="false">追问此处</button><button id="font-smaller" type="button" aria-label="减小正文字号">字小</button><button id="font-larger" type="button" aria-label="增大正文字号">字大</button><button id="theme-toggle" type="button" aria-pressed="false">夜读</button><button id="print-reader" type="button">打印</button></div>
</header>
<section id="question-panel" class="question-panel" aria-labelledby="question-title" hidden>
<div class="question-heading"><h2 id="question-title">围绕原文继续讨论</h2><button id="close-question" type="button">收起追问</button></div>
<p id="question-help">先选中正文，再点“追问此处”；也可以选择一个章节。文字只在本页生成，由你复制到对话中。</p>
<div class="question-section"><label for="question-section">选择章节</label><select id="question-section"><option value="">请选择章节或条款</option>{section_options}</select><button id="quote-section" type="button" disabled>引用所选章节</button></div>
<label for="question-text">可编辑的追问内容</label><textarea id="question-text" rows="8" aria-describedby="question-help" placeholder="选取原文后，这里会包含作品、章节位置和原文选段。"></textarea>
<div class="question-actions"><button id="copy-question" type="button" disabled>复制追问</button><span id="question-status" role="status" aria-live="polite">尚未选取原文</span></div>
</section>
<div class="reading-layout"><aside id="contents" aria-label="目录"><div class="contents-heading">内容导航</div><nav aria-label="章节与条文"><ol>{toc}</ol></nav><a class="source-download" href="data:text/markdown;charset=utf-8;base64,{original}" download="{escape(source_path.name)}">下载完整 Markdown</a></aside>
<main><article id="document" tabindex="-1">{body}</article>{note_html}<footer class="reader-footer"><a href="#document">回到开篇</a><span>正文完整保留 · 离线阅读</span></footer></main></div>
<noscript><p class="no-script">正文、目录、脚注和原文下载仍可使用，公式保留原式。浏览器内搜索与打印可通过 Ctrl+F、Ctrl+P 打开。</p></noscript>
{script_html}
</body></html>'''


def main() -> int:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='完整 UTF-8 Markdown 文件')
    parser.add_argument('--output', '-o', type=Path, required=True, help='输出的单文件 HTML')
    parser.add_argument('--title', help='浏览器标签标题；不更改正文')
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError('输入与输出不能是同一个文件')
        raw = args.input.read_bytes()
        text = raw.decode('utf-8-sig')
        document = render_document(text, title=args.title, source_path=args.input, source_bytes=raw)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(document, encoding='utf-8', newline='\n')
        print(json.dumps({'output': str(args.output.resolve()), 'source_bytes': len(raw), 'html_bytes': args.output.stat().st_size, 'renderer': 'python-standard-library', 'offline': True}, ensure_ascii=False))
        return 0
    except (OSError, UnicodeError, ValueError) as error:
        print(f'阅读版生成失败：{error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
