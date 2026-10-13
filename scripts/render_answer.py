"""Render UTF-8 Markdown as a self-contained, offline Chinese reading document.

Uses only Python's standard library. Supports headings, paragraphs, emphasis,
links, local images, nested lists, quotes, pipe tables, and fenced/indented code.
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
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


ASSETS = Path(__file__).resolve().parents[1] / 'assets'
HEADING = re.compile(r'^ {0,3}(#{1,6})(?:\s+|$)(.*?)\s*$')
FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})([^\n]*)$')
LIST = re.compile(r'^( {0,3})([-+*]|\d+[.)])([ \t]+)(.*)$')
REFERENCE = re.compile(r'^ {0,3}\[([^]\n]+)\]:\s*(?:<([^>]+)>|(\S+))(?:\s+[\"\x27](.*)[\"\x27])?\s*$')
CLAUSE = re.compile(r'^\*\*(第[一二三四五六七八九十百零〇两\d]+条[\s\u3000].+?)\*\*$')


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

    def anchor(self, level: int, text: str) -> str:
        plain = html.unescape(re.sub(r'<[^>]*>', '', self.inline(text)))
        anchor = f'section-{len(self.headings) + 1}'
        self.headings.append((level, anchor, plain))
        slug = re.sub(r'[^\w\-\s]', '', plain.lower()).strip().replace(' ', '-')
        self.fragments.setdefault(slug, anchor)
        self.fragments.setdefault(plain, anchor)
        return anchor

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
            if text[i] == '\\' and i + 1 < len(text) and text[i + 1] in r'\`*_{}[]()#+-.!|>~':
                result.append(escape(text[i + 1])); i += 2; continue
            if text[i] == '`':
                run = re.match(r'`+', text[i:]).group()
                end = text.find(run, i + len(run))
                if end >= 0:
                    code = text[i + len(run):end].replace('\n', ' ')
                    if code.startswith(' ') and code.endswith(' ') and code.strip():
                        code = code[1:-1]
                    result.append('<code>' + escape(code) + '</code>'); i = end + len(run); continue
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
        return bool(HEADING.match(line) or FENCE.match(line) or LIST.match(line) or re.match(r'^ {0,3}>', line) or re.fullmatch(r' {0,3}(?:\*\s*){3,}| {0,3}(?:-\s*){3,}| {0,3}(?:_\s*){3,}', line))

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
            heading = HEADING.match(line)
            if heading:
                level = len(heading.group(1))
                text = re.sub(r'\s+#+\s*$', '', heading.group(2))
                anchor = self.anchor(level, text)
                output.append(f'<h{level} id="{anchor}" tabindex="-1">{self.inline(text)}</h{level}>'); i += 1; continue
            if i + 1 < len(lines) and re.fullmatch(r' {0,3}(?:=+|-+)\s*', lines[i + 1]):
                level = 1 if lines[i + 1].lstrip().startswith('=') else 2
                anchor = self.anchor(level, line)
                output.append(f'<h{level} id="{anchor}" tabindex="-1">{self.inline(line)}</h{level}>'); i += 2; continue
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
                output.append(f'<p class="clause" id="{anchor}" tabindex="-1">{self.inline(line)}</p>'); i += 1; continue
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
        lines = source.lstrip('\ufeff').splitlines()
        for line in lines:
            reference = REFERENCE.match(line)
            if reference and not reference.group(1).startswith('^'):
                self.references[reference.group(1).casefold()] = reference.group(2) or reference.group(3)
        if re.search(r'^\s*(?:\$\$|\[\^|:::|---\s*$)', source, re.M):
            self.notes.add('数学公式、脚注及其他扩展语法可能按原文显示；可下载完整 Markdown。')
        body = self.blocks(lines)
        for old, new in self.fragments.items():
            body = body.replace('href="#' + escape(old) + '"', 'href="#' + new + '"')
        return body


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
    script_hash = base64.b64encode(hashlib.sha256(javascript.encode('utf-8')).digest()).decode('ascii')
    style_hash = base64.b64encode(hashlib.sha256(css.encode('utf-8')).digest()).decode('ascii')
    original = base64.b64encode(source_bytes if source_bytes is not None else source.encode('utf-8')).decode('ascii')
    notes = ''.join('<li>' + escape(note) + '</li>' for note in sorted(reader.notes))
    note_html = '<details class="render-notes"><summary>阅读格式说明</summary><ul>' + notes + '</ul></details>' if notes else ''
    csp = f"default-src 'none'; script-src 'sha256-{script_hash}'; style-src 'sha256-{style_hash}'; img-src data:; connect-src 'none'; font-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"
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
<div class="reading-controls"><button id="font-smaller" type="button" aria-label="减小正文字号">字小</button><button id="font-larger" type="button" aria-label="增大正文字号">字大</button><button id="theme-toggle" type="button" aria-pressed="false">夜读</button><button id="print-reader" type="button">打印</button></div>
</header>
<div class="reading-layout"><aside id="contents" aria-label="目录"><div class="contents-heading">内容导航</div><nav aria-label="章节与条文"><ol>{toc}</ol></nav><a class="source-download" href="data:text/markdown;charset=utf-8;base64,{original}" download="{escape(source_path.name)}">下载完整 Markdown</a></aside>
<main><article id="document" tabindex="-1">{body}</article>{note_html}<footer class="reader-footer"><a href="#document">回到开篇</a><span>正文完整保留 · 离线阅读</span></footer></main></div>
<noscript><p class="no-script">正文、目录和原文下载仍可使用。浏览器内搜索与打印可通过 Ctrl+F、Ctrl+P 打开。</p></noscript>
<script>{javascript}</script>
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
