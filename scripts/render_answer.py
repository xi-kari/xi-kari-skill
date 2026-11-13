"""Render UTF-8 Markdown as a self-contained, offline Chinese reading document.

Uses only Python's standard library. Supports headings, paragraphs, emphasis,
links, local images, nested lists, quotes, pipe tables, footnotes, and code.
Explicit formulas use bundled KaTeX in the generated browser document.
Other Markdown extensions remain literal text; the original bytes are downloadable.

The page draws the document as a track chart: each section is a fix placed at its
measured distance, and the reader's position is flown along it. Everything the
chart shows is counted from the rendered text; nothing is added to the text itself.
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
from types import SimpleNamespace
import unicodedata
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from xikari_paths import require_external_output
    from xikari_page import DOWNLOAD, STATION, foundation, icon
finally:
    sys.path.pop(0)


ASSETS = Path(__file__).resolve().parents[1] / 'assets'
HAN = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')
WORD = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*|\d+(?:[.,]\d+)*")
TAG = re.compile(r'<[^>]+>')
TITLE_BLOCK = re.compile(r'\s*<span class="legacy-anchor"[^>]*></span><h1 [^>]*>.*?</h1>', re.S)
HEADING = re.compile(r'^ {0,3}(#{1,6})(?:\s+|$)(.*?)\s*$')
FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})([^\n]*)$')
LIST = re.compile(r'^( {0,3})([-+*]|\d+[.)])([ \t]+)(.*)$')
REFERENCE = re.compile(r'^ {0,3}\[([^]\n]+)\]:\s*(?:<([^>]+)>|(\S+))(?:\s+[\"\x27](.*)[\"\x27])?\s*$')
CLAUSE = re.compile(r'^\*\*(第[一二三四五六七八九十百零〇两\d]+条[\s\u3000].+?)\*\*$')
FOOTNOTE = re.compile(r'^ {0,3}\[\^([^]\n]+)\]:[ \t]?(.*)$')
CHINESE_NUMERAL = '一二三四五六七八九十百千零〇两'
UNIT_AFTER_NUMBER = '年月日号时分秒岁个项条种人位次天元倍万亿千百%％'
HEADING_NUMBER = re.compile(
    '^(?:'
    f'第[{CHINESE_NUMERAL}\\d]+(?:部分|[部篇编卷章节回])[、．.:：]?'
    f'|[{CHINESE_NUMERAL}]{{1,4}}[、．]'
    f'|[（(][{CHINESE_NUMERAL}\\d]{{1,3}}[)）]'
    '|\\d{1,2}(?:\\.\\d{1,2}){0,3}[、．]'
    f'|\\d{{1,2}}(?:\\.\\d{{1,2}}){{1,3}}(?=[\\u4e00-\\u9fff])(?![{UNIT_AFTER_NUMBER}])'
    f'|\\d{{1,2}}(?:\\.\\d{{1,2}}){{0,3}}\\.?(?=[ \\t\\u3000]+(?![{UNIT_AFTER_NUMBER}]))'
    ')[ \\t\\u3000]*'
)
TITLE_BREAKS = ('：', '——')
NUMBER_END = '、．.:： \t\u3000'
FIX_MARK = ('<svg class="fix-mark" viewBox="0 0 12 12" aria-hidden="true" focusable="false">'
            '<path d="M6 1.5 11 10.3H1Z"/></svg>')
ENTRY_MARK = ('<svg class="entry-mark" viewBox="0 0 12 12" aria-hidden="true" focusable="false">'
              '<circle cx="6" cy="6" r="3.7"/></svg>')


def escape(value: str) -> str:
    return html.escape(value, quote=True)


LABELS = {
    'zh': {
        'html_lang': 'zh-CN',
        'long_formula': '一条公式超过 10000 字符，已保留原式，未执行公式排版。',
        'duplicate_footnote': '重复的脚注定义保留原文；引用使用首次定义。',
        'back_aria': '返回脚注 {number} 的第 {index} 处引用',
        'back': '返回引用 {index}',
        'unused_footnote': '（正文未引用）',
        'footnote_position': '脚注 ',
        'footnotes': '脚注',
        'image': '图像：',
        'untitled_image': '未命名图像',
        'image_without_alt': '有图像未提供替代文字，已用文件名标明；阅读时请结合正文。',
        'remote_image': '远程图像未下载，离线保留说明与地址',
        'large_image': '图像超过 20 MiB，保留说明与路径',
        'image_format': '此图像格式暂不内嵌，保留说明与路径',
        'svg_entity': 'SVG 含外部实体声明，未内嵌',
        'svg_root': 'SVG 根元素无效，未内嵌',
        'svg_active': 'SVG 含主动内容或样式块，未内嵌',
        'svg_reference': 'SVG 含外部引用或主动属性，未内嵌',
        'image_unreadable': '本地图像无法读取，保留说明与路径',
        'unsafe_link': '危险链接协议已停用，链接文字与原地址仍保留。',
        'mermaid_note': 'Mermaid 保留源码与文字说明，未加载在线绘图服务。',
        'mermaid_caption': 'Mermaid 图示源码 · 离线保留，未渲染为图',
        'table': '表格，可横向滚动',
        'unsupported': '未支持的扩展语法保留为原文；可下载完整 Markdown。',
        'math_unavailable': '公式排版资源不可用，已保留完整原式；其他阅读功能照常可用。',
        'read_all': '阅读全文',
        'format_notes': '阅读格式说明',
        'skip': '跳至正文',
        'contents': '目录',
        'sections': '章节与条文',
        'download': '下载 Markdown 原稿',
        'tools': '阅读工具',
        'open_contents': '打开目录',
        'search': '搜索全文',
        'previous_match': '上一处匹配',
        'previous_title': '上一处（Shift+Enter）',
        'next_match': '下一处匹配',
        'next_title': '下一处（Enter）',
        'close_search': '关闭搜索',
        'ask_here': '追问此处',
        'settings': '阅读设置',
        'smaller': '减小正文字号',
        'smaller_title': '减小字号',
        'larger': '增大正文字号',
        'larger_title': '增大字号',
        'night': '夜间阅读',
        'to_night': '切换到夜间阅读',
        'print': '打印或存为 PDF',
        'footer': '离线阅读版：正文完整保留，页面不联网，也不会自动发送任何内容。',
        'to_start': '回到开篇',
        'question_title': '围绕原文继续讨论',
        'close_question': '收起追问',
        'close_question_title': '收起追问（Esc）',
        'question_help': '先在正文中选中一段文字，或在下面选择一个章节。追问只在本页生成，由你复制到对话里。',
        'quote_label': '引用一个章节',
        'choose_section': '选择章节或条款',
        'quote_section': '引用此章节',
        'question_label': '追问内容（可编辑）',
        'question_placeholder': '选取原文后，这里会列出作品、章节位置和原文选段。',
        'no_passage': '尚未选取原文',
        'copy_question': '复制追问',
        'ask_selection': '追问选段',
        'noscript': '正文、目录、脚注和原文下载仍可使用，公式保留原式。浏览器内搜索与打印可通过 Ctrl+F、Ctrl+P 打开。',
        'same_file': '输入与输出不能是同一个文件',
        'failed': '阅读版生成失败：',
        'overview': '全文概览',
        'strip_time': '读完约',
        'strip_length': '篇幅',
        'strip_sections': '章节',
        'strip_figures': '图表',
        'strip_notes': '脚注',
        'unit_minute': '分钟',
        'unit_hour': '小时',
        'length_wan': '约 {n} 万字',
        'length_plain': '约 {n} 字',
        'opening': '开篇',
        'section_value': '{n} 节',
        'sections_value': '{n} 节',
        'subsection_value': '{n} 小节',
        'subsections_value': '{n} 小节',
        'tables_value': '表 {n}',
        'figures_value': '图 {n}',
        'formulas_value': '式 {n}',
        'notes_value': '{n} 条',
        'join': ' · ',
        'rack_unit': '字',
        'rack_unit_thousands': '千字',
        'unfold': '展开全部小节',
        'resume': '继续阅读',
        'face': '正文用宋体',
        'face_title': '正文在黑体与宋体之间切换',
        'keys': '键盘',
        'keys_search': '搜索',
        'keys_sections': '上一节、下一节',
        'keys_close': '关闭',
        'face_specimen': '文',
    },
    'en': {
        'html_lang': 'en',
        'long_formula': 'A formula longer than 10,000 characters is kept as written and was not typeset.',
        'duplicate_footnote': 'Duplicate footnote definitions are kept as written; references use the first definition.',
        'back_aria': 'Back to reference {index} of footnote {number}',
        'back': 'Back to reference {index}',
        'unused_footnote': ' (not referenced in the text)',
        'footnote_position': 'Footnote ',
        'footnotes': 'Footnotes',
        'image': 'Image: ',
        'untitled_image': 'untitled image',
        'image_without_alt': 'An image without alternative text is labeled with its file name; read it together with the text.',
        'remote_image': 'Remote image not downloaded; its description and address are kept offline',
        'large_image': 'Image larger than 20 MiB; its description and path are kept',
        'image_format': 'This image format is not embedded; its description and path are kept',
        'svg_entity': 'The SVG declares external entities and was not embedded',
        'svg_root': 'The SVG root element is invalid; not embedded',
        'svg_active': 'The SVG contains active content or style blocks; not embedded',
        'svg_reference': 'The SVG contains external references or active attributes; not embedded',
        'image_unreadable': 'The local image could not be read; its description and path are kept',
        'unsafe_link': 'A link with an unsafe protocol was disabled; its text and address are kept.',
        'mermaid_note': 'Mermaid diagrams are kept as source with their descriptions; no online drawing service was loaded.',
        'mermaid_caption': 'Mermaid diagram source · kept offline, not drawn',
        'table': 'Table, scrolls horizontally',
        'unsupported': 'Unsupported extended syntax is kept as written; the complete Markdown can be downloaded.',
        'math_unavailable': 'Formula typesetting is unavailable; every formula is kept as written and the other reading features work as usual.',
        'read_all': 'Read the full text',
        'format_notes': 'Notes on this reading format',
        'skip': 'Skip to the text',
        'contents': 'Contents',
        'sections': 'Sections and clauses',
        'download': 'Download Markdown',
        'tools': 'Reading tools',
        'open_contents': 'Open contents',
        'search': 'Search the text',
        'previous_match': 'Previous match',
        'previous_title': 'Previous (Shift+Enter)',
        'next_match': 'Next match',
        'next_title': 'Next (Enter)',
        'close_search': 'Close search',
        'ask_here': 'Ask about this',
        'settings': 'Reading settings',
        'smaller': 'Decrease text size',
        'smaller_title': 'Smaller text',
        'larger': 'Increase text size',
        'larger_title': 'Larger text',
        'night': 'Night reading',
        'to_night': 'Switch to night reading',
        'print': 'Print or save as PDF',
        'footer': 'Offline reading edition: the full text is kept, the page makes no network connections, and it sends nothing automatically.',
        'to_start': 'Back to the beginning',
        'question_title': 'Continue from the text',
        'close_question': 'Close the question panel',
        'close_question_title': 'Close (Esc)',
        'question_help': 'Select a passage in the text, or choose a section below. The question is composed on this page only; copy it into your conversation.',
        'quote_label': 'Quote a section',
        'choose_section': 'Choose a section or clause',
        'quote_section': 'Quote this section',
        'question_label': 'Your question (editable)',
        'question_placeholder': 'After you select a passage, the work, its section and the quoted passage appear here.',
        'no_passage': 'No passage selected yet',
        'copy_question': 'Copy question',
        'ask_selection': 'Ask about selection',
        'noscript': 'The text, contents, footnotes and Markdown download still work, and formulas are kept as written. Use Ctrl+F to search and Ctrl+P to print.',
        'same_file': 'Input and output must not be the same file',
        'failed': 'Reading page could not be generated: ',
        'overview': 'Overview of the text',
        'strip_time': 'Reading time',
        'strip_length': 'Length',
        'strip_sections': 'Sections',
        'strip_figures': 'Tables and figures',
        'strip_notes': 'Footnotes',
        'unit_minute': 'min',
        'unit_hour': 'hr',
        'length_wan': 'About {n} words',
        'length_plain': 'About {n} words',
        'opening': 'Start',
        'section_value': '{n} section',
        'sections_value': '{n} sections',
        'subsection_value': '{n} subsection',
        'subsections_value': '{n} subsections',
        'tables_value': 'Tables {n}',
        'figures_value': 'Figures {n}',
        'formulas_value': 'Formulas {n}',
        'notes_value': '{n}',
        'join': ' · ',
        'rack_unit': 'words',
        'rack_unit_thousands': 'k words',
        'unfold': 'Unfold every subsection',
        'resume': 'Continue reading',
        'face': 'Set the text in a serif face',
        'face_title': 'Switch the text between sans and serif',
        'keys': 'Keyboard',
        'keys_search': 'search',
        'keys_sections': 'previous and next section',
        'keys_close': 'close',
        'face_specimen': 'Ag',
    },
}
# Labels the page sets in the display cut. `website/scripts/build_output_fonts.py` cuts the face to them.
DISPLAY_KEYS = ('ask_here', 'ask_selection', 'copy_question', 'quote_section', 'download', 'resume', 'contents', 'opening',
                'unit_minute', 'unit_hour', 'length_wan', 'length_plain', 'section_value', 'sections_value', 'subsection_value',
                'subsections_value', 'tables_value', 'figures_value', 'formulas_value', 'notes_value', 'join')


def display_strings(lang: str = 'zh') -> list[str]:
    """Every string this page sets in the display cut, for the font build and its check."""
    return [LABELS[lang][key] for key in DISPLAY_KEYS]


def number_heading(rendered: str, label: str = 'heading-no') -> str:
    """Mark a heading's own leading number so it can hang in the margin; the text is unchanged."""
    match = HEADING_NUMBER.match(rendered)
    if not match or match.end() >= len(rendered):
        return rendered
    number = match.group(0)
    figure = number.rstrip('、．.:： \t\u3000')
    separator = number[len(figure):]
    if separator:
        number = f'{figure}<span class="number-sep">{separator}</span>'
    return f'<span class="{label}">{number}</span>{rendered[match.end():]}'


def segment(rendered: str) -> str:
    """Let a title break after its own punctuation: each clause stays together when it fits the line."""
    pieces, start, depth, i = [], 0, 0, 0
    while i < len(rendered):
        if rendered[i] == '<':
            end = rendered.find('>', i)
            if end < 0:
                return rendered
            tag = rendered[i:end + 1]
            if tag.startswith('</'):
                depth -= 1
            elif not tag.endswith('/>') and not re.match(r'<(?:br|img|wbr)\b', tag):
                depth += 1
            i = end + 1
            continue
        if depth == 0 and rendered[i] in '，、；' and rendered[i + 1:].strip():
            pieces.append(rendered[start:i + 1])
            start = i + 1
        i += 1
    if not pieces:
        return rendered
    pieces.append(rendered[start:])
    return ''.join(f'<span class="seg">{piece}</span>' for piece in pieces if piece)


def split_title(rendered: str) -> str:
    """Set a “主题：副题” title on two lines; the title text itself is unchanged."""
    depth, i = 0, 0
    while i < len(rendered):
        if rendered[i] == '<':
            end = rendered.find('>', i)
            if end < 0:
                return rendered
            tag = rendered[i:end + 1]
            if tag.startswith('</'):
                depth -= 1
            elif not tag.endswith('/>') and not re.match(r'<(?:br|img|wbr)\b', tag):
                depth += 1
            i = end + 1
            continue
        if depth == 0:
            for mark in TITLE_BREAKS:
                if rendered.startswith(mark, i):
                    head, tail = rendered[:i], rendered[i + len(mark):]
                    if not head.strip() or not tail.strip():
                        return segment(rendered)
                    return (f'<span class="title-main">{segment(head)}<span class="title-colon">{mark}</span></span>'
                            f'<span class="title-sub">{segment(tail)}</span>')
        i += 1
    return segment(rendered)


def text_units(fragment: str) -> tuple[int, int]:
    """Han characters and Latin words or numbers in a rendered fragment."""
    text = html.unescape(TAG.sub(' ', fragment))
    return len(HAN.findall(text)), len(WORD.findall(text))


def reading_minutes(han: int, words: int) -> float:
    return han / 400 + words / 220


def length_text(total: int, lang: str = 'zh') -> str:
    L = LABELS[lang]
    if lang != 'en' and total >= 10000:
        return L['length_wan'].format(n=f'{total / 10000:.1f}'.removesuffix('.0'))
    return L['length_plain'].format(n=f'{round(total, -2):,}' if total >= 1000 else f'{max(1, round(total, -1) or total)}')


def duration_text(minutes: int, lang: str = 'zh') -> str:
    hours, rest = divmod(minutes, 60)
    if lang == 'en':
        unit = lambda n, word: f"{n} {word}{'' if n == 1 else 's'}"
        return unit(minutes, 'minute') if minutes < 60 else unit(hours, 'hour') + (f' {unit(rest, "minute")}' if rest else '')
    return f'{minutes} 分钟' if minutes < 60 else f'{hours} 小时' + (f' {rest} 分钟' if rest else '')


def reading_stats(body: str, lang: str = 'zh') -> str:
    """Length and reading time of the rendered text, for orientation only."""
    han, words = text_units(body)
    minutes = max(1, round(reading_minutes(han, words)))
    if lang == 'en':
        return f'{length_text(han + words, lang)}; about {duration_text(minutes, lang)} to read.'
    return f'全文{length_text(han + words, lang)}，读完约需 {duration_text(minutes, lang)}。'


def measure(fragment: str) -> dict:
    """What a stretch of rendered text holds: its length, and the tables, figures, set-off formulas and note references in it."""
    han, words = text_units(fragment)
    return {'units': han + words, 'minutes': reading_minutes(han, words), 'tables': fragment.count('<table'),
            'figures': fragment.count('<figure class="figure-image">'),
            'formulas': fragment.count('class="reader-math math-display"'),
            'notes': fragment.count('class="footnote-ref"')}


def section_measures(body: str, headings: list[tuple[int, str, str]]) -> tuple[dict, dict[str, dict]]:
    """Measure the text before the first heading and the text each heading opens."""
    marks = sorted((index, anchor) for index, anchor in
                   ((body.find(f' id="{anchor}" data-reader-section="'), anchor) for _, anchor, _ in headings) if index >= 0)
    lead = measure(body[:body.rfind('<', 0, marks[0][0])] if marks else body)
    sections = {}
    for position, (index, anchor) in enumerate(marks):
        end = body.rfind('<', 0, marks[position + 1][0]) if position + 1 < len(marks) else len(body)
        sections[anchor] = measure(body[body.find('>', index) + 1:end])
    return lead, sections


def own_number(plain: str) -> tuple[str, str]:
    """A heading's own number and the rest of its text; the number is empty when it has none."""
    match = HEADING_NUMBER.match(plain)
    if not match or match.end() >= len(plain):
        return '', plain
    return match.group(0).rstrip(NUMBER_END), plain[match.end():]


def outline(body: str, headings: list[tuple[int, str, str]], measures: dict[str, dict], lead: dict) -> tuple[dict[str, dict], dict]:
    """Decide which headings are fixes on the track: the top level of the document's own structure.

    The title is the only h1, or the h1 that opens a document with several. The fixes are the
    shallowest headings besides it, and the footnotes when there are any. A fix carries its own
    number when it has one. When no fix is numbered they are numbered in sequence for wayfinding;
    the heading text itself is never changed. Each fix carries the length of everything it opens;
    what stands before the first fix is the opening.
    """
    firsts = [anchor for level, anchor, _ in headings if level == 1]
    title = (firsts[0] if firsts and (len(firsts) == 1 or (headings[0][0] == 1 and TITLE_BLOCK.match(body))) else None)
    levels = [level for level, anchor, _ in headings if anchor not in (title, 'reader-footnotes')]
    fix_level = min(levels) if levels else 0
    info, current = {}, None
    opening = {'units': lead['units'], 'minutes': lead['minutes']}
    for level, anchor, text in headings:
        number, label = own_number(text)
        own = measures.get(anchor, {'units': 0, 'minutes': 0.0})
        fix = anchor != title and (anchor == 'reader-footnotes' or level == fix_level)
        info[anchor] = {'title': anchor == title, 'fix': fix, 'number': number, 'label': label, 'sequence': '',
                        'units': own['units'], 'minutes': own['minutes']}
        if fix:
            current = anchor
        else:
            holder = info[current] if current else opening
            holder['units'] += own['units']
            holder['minutes'] += own['minutes']
    numbered = [anchor for anchor, item in info.items() if item['fix'] and anchor != 'reader-footnotes']
    if numbered and not any(info[anchor]['number'] for anchor in numbered):
        for position, anchor in enumerate(numbered, 1):
            info[anchor]['sequence'] = f'{position:02d}'
    return info, opening


def toc_label(text: str) -> str:
    """A contents entry with its own number set apart; the entry's text is unchanged."""
    rendered = escape(text)
    match = HEADING_NUMBER.match(rendered)
    if not match or match.end() >= len(rendered):
        return f'<span class="toc-title">{rendered}</span>'
    number = match.group(0)
    figure = number.rstrip(NUMBER_END)
    separator = number[len(figure):]
    if separator:
        figure += f'<span class="number-sep">{separator}</span>'
    return f'<span class="toc-no">{figure}</span><span class="toc-title">{rendered[match.end():]}</span>'


def rack_lengths(parts: list[int], thousands: bool) -> list[str]:
    """Lengths in the unit the rack states, so that the column adds up to the length the plate states.

    Counts are given as counted. In thousands each strip is rounded to a tenth, and the tenths
    lost to rounding go to the strips that lost most, so the column still sums to the whole.
    """
    if not thousands:
        return [str(units) for units in parts]
    tenths = [units // 100 for units in parts]
    spare = round(sum(parts) / 100) - sum(tenths)
    for index in sorted(range(len(parts)), key=lambda index: (-(parts[index] % 100), index))[:max(0, spare)]:
        tenths[index] += 1
    return [f'{value / 10:.1f}' if value else ('&lt;0.1' if units else '0') for value, units in zip(tenths, parts)]


def length_cell(value: str) -> str:
    return f'<span class="toc-len" aria-hidden="true"><span class="toc-min num">{value}</span>{FIX_MARK}</span>'


def build_rack(headings: list[tuple[int, str, str]], info: dict[str, dict], opening: dict, label: str, thousands: bool) -> str:
    """The contents as a rack of strips: the opening, then one strip per fix with its subsections racked beneath it."""
    items, bay_open, sub_open = [], False, False
    has_fix = any(item['fix'] for item in info.values())
    leading = headings[0][1] if headings and info[headings[0][1]]['title'] else None
    entry = has_fix and bool(leading or opening['units'])
    lengths = iter(rack_lengths(([opening['units']] if entry else []) + [item['units'] for item in info.values() if item['fix']], thousands))

    def close() -> None:
        nonlocal bay_open, sub_open
        if sub_open:
            items.append('</ol>')
        if bay_open:
            items.append('</li>')
        bay_open = sub_open = False

    if entry:
        items.append(f'<li class="rack-bay rack-entry"><span class="toc-seq" aria-hidden="true">{ENTRY_MARK}</span>'
                     f'<a href="#{leading or "document"}"><span class="toc-title">{label}</span></a>'
                     f'{length_cell(next(lengths))}</li>')
    for level, anchor, text in headings:
        item = info[anchor]
        if item['title']:
            if has_fix and anchor == leading:
                continue
            close()
            items.append(f'<li class="toc-level-1 rack-title"><a href="#{anchor}">{split_title(escape(text))}</a></li>')
        elif item['fix']:
            close()
            sequence = (f'<span class="toc-seq num" aria-hidden="true">{item["sequence"]}</span>' if item['sequence']
                        else '' if item['number'] else f'<span class="toc-seq" aria-hidden="true">{FIX_MARK}</span>')
            items.append(f'<li class="toc-level-{level} rack-bay">{sequence}<a href="#{anchor}">{toc_label(text)}</a>'
                         f'{length_cell(next(lengths))}')
            bay_open = True
        else:
            if bay_open and not sub_open:
                items.append('<ol class="rack-sub">')
                sub_open = True
            items.append(f'<li class="toc-level-{level}"><a href="#{anchor}">{toc_label(text)}</a></li>')
    close()
    return ''.join(items)


def mark_opening(inner: str) -> str:
    """Where the document itself opens with an emphasized sentence, mark it as the sentence to notice.

    Only the source decides: a first paragraph that begins with a whole sentence in bold keeps
    its words and gains the mark; anything else is left as written.
    """
    match = re.match(r'<strong>(.*?)</strong>', inner, re.S)
    if not match:
        return inner
    text = html.unescape(TAG.sub('', match.group(1))).rstrip('”’」』）)" \n')
    if not text or text[-1] not in '。！？.!?':
        return inner
    return '<strong class="key">' + inner[len('<strong>'):]


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
    def __init__(self, source_path: Path, lang: str = 'zh'):
        self.labels = LABELS[lang]
        self.t = SimpleNamespace(**self.labels)
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

    def heading_content(self, level: int, text: str) -> str:
        rendered = self.inline(text)
        if level == 1:
            return split_title(rendered)
        return number_heading(rendered) if level <= 4 else rendered

    def heading_attributes(self, anchor: str, level: int) -> str:
        plain = self.headings[-1][2]
        return f'id="{anchor}" data-reader-section="{level}" data-section-title="{escape(plain)}" tabindex="-1"'

    def legacy_anchor(self) -> str:
        return f'<span class="legacy-anchor" id="section-{len(self.headings)}" aria-hidden="true"></span>'

    def math(self, tex: str, raw: str, display: bool = False) -> str:
        if self.label_mode:
            return escape(raw)
        if len(tex) > 10000:
            self.notes.add(self.labels['long_formula'])
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
        return f'<sup class="footnote-ref" data-footnote-source="{escape("[^" + label + "]")}"><a id="{reference}" href="#fn-{identifier}" role="doc-noteref" aria-label="{self.t.footnote_position}{number}">{number}</a></sup>'

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
                self.notes.add(self.labels['duplicate_footnote'])
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
            back = ' '.join(f'<a class="footnote-backref" href="#{reference}" aria-label="{self.t.back_aria.format(number=self.footnote_numbers[key], index=index)}">{self.t.back.format(index=index)}</a>' for index, reference in enumerate(references, 1))
            unused = f'<p class="footnote-unused">{escape("[^" + self.footnotes[key][0] + "]")}{self.t.unused_footnote}</p>' if not references else ''
            position = self.labels['footnote_position'] + '[^' + self.footnotes[key][0] + ']'
            items.append(f'<li id="fn-{identifier}" data-section-title="{escape(position)}" tabindex="-1">{unused}{bodies[key]}<p class="footnote-returns">{back}</p></li>')
        self.headings.append((2, 'reader-footnotes', self.labels['footnotes']))
        return '<section id="reader-footnotes" data-reader-section="2" data-section-title="' + self.labels['footnotes'] + '" class="footnotes" role="doc-endnotes" aria-label="' + self.labels['footnotes'] + '" tabindex="-1"><h2>' + self.labels['footnotes'] + '</h2><ol>' + ''.join(items) + '</ol></section>'

    def image(self, alt: str, destination: str) -> str:
        label = re.sub(r'[*`_]', '', alt).strip()
        if not label:
            label = self.labels['image'] + (Path(destination).name or self.labels['untitled_image'])
            self.notes.add(self.labels['image_without_alt'])
        try:
            parts = urlsplit(destination)
            windows_path = bool(re.match(r'^[A-Za-z]:[\\/]', destination))
            if (parts.scheme not in ('', 'file') and not windows_path) or destination.startswith('//'):
                raise ValueError(self.labels['remote_image'])
            raw_path = unquote(parts.path) if parts.scheme == 'file' else unquote(destination)
            if parts.scheme == 'file' and re.match(r'^/[A-Za-z]:/', raw_path):
                raw_path = raw_path[1:]
            path = Path(raw_path)
            if not path.is_absolute():
                path = self.source_path.parent / path
            data = path.read_bytes()
            if len(data) > 20 * 1024 * 1024:
                raise ValueError(self.labels['large_image'])
            suffix = path.suffix.lower()
            mimes = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml'}
            if suffix not in mimes:
                raise ValueError(self.labels['image_format'])
            if suffix == '.svg':
                if re.search(br'<!DOCTYPE|<!ENTITY', data, re.I):
                    raise ValueError(self.labels['svg_entity'])
                root = ET.fromstring(data)
                if root.tag.split('}')[-1] != 'svg':
                    raise ValueError(self.labels['svg_root'])
                for element in root.iter():
                    name = element.tag.split('}')[-1].lower()
                    if name in ('script', 'foreignobject', 'iframe', 'object', 'embed', 'audio', 'video', 'style'):
                        raise ValueError(self.labels['svg_active'])
                    for key, value in element.attrib.items():
                        key = key.split('}')[-1].lower()
                        if key.startswith('on') or (key in ('href', 'src') and not value.startswith('#')) or re.search(r'url\s*\(\s*[\"\x27]?(?!#)', value, re.I):
                            raise ValueError(self.labels['svg_reference'])
            encoded = base64.b64encode(data).decode('ascii')
            return f'<img src="data:{mimes[suffix]};base64,{encoded}" alt="{escape(label)}" loading="lazy" decoding="async">'
        except (OSError, ValueError, ET.ParseError) as error:
            explanation = str(error) if isinstance(error, ValueError) else self.labels['image_unreadable']
            self.notes.add(explanation)
            return f'<span class="image-fallback" role="img" aria-label="{escape(label)}">{escape(label)} <span>（{escape(explanation)}：{escape(destination)}）</span></span>'

    def link(self, label: str, destination: str) -> str:
        if not safe_url(destination):
            self.notes.add(self.labels['unsafe_link'])
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
                    self.notes.add(self.labels['mermaid_note'])
                    body = '<figure class="diagram-source"><figcaption>' + self.labels['mermaid_caption'] + '</figcaption>' + body + '</figure>'
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
                output.append(self.legacy_anchor() + f'<h{level} {self.heading_attributes(anchor, level)}>{self.heading_content(level, text)}</h{level}>'); i += 1; continue
            if i + 1 < len(lines) and re.fullmatch(r' {0,3}(?:=+|-+)\s*', lines[i + 1]):
                level = 1 if lines[i + 1].lstrip().startswith('=') else 2
                anchor = self.anchor(level, line)
                output.append(self.legacy_anchor() + f'<h{level} {self.heading_attributes(anchor, level)}>{self.heading_content(level, line)}</h{level}>'); i += 2; continue
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
                output.append('<div class="table-scroll" tabindex="0" role="region" aria-label="' + self.labels['table'] + '"><table><thead><tr>' + cells(header, 'th') + '</tr></thead><tbody>' + ''.join('<tr>' + cells(row, 'td') + '</tr>' for row in rows) + '</tbody></table></div>'); continue
            if line.startswith('    ') or line.startswith('\t'):
                code = []
                while i < len(lines) and (lines[i].startswith(('    ', '\t')) or not lines[i].strip()):
                    code.append(lines[i][1:] if lines[i].startswith('\t') else lines[i][4:]); i += 1
                output.append('<pre><code>' + escape('\n'.join(code).rstrip('\n')) + '</code></pre>'); continue
            clause = CLAUSE.match(line)
            if clause:
                anchor = self.anchor(3, clause.group(1))
                content = re.sub(f'^<strong>(第[{CHINESE_NUMERAL}\\d]+条)', r'<strong><span class="clause-no">\1</span>', self.inline(line), count=1)
                output.append(self.legacy_anchor() + f'<p class="clause" {self.heading_attributes(anchor, 3)}>{content}</p>'); i += 1; continue
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
            content = ''.join(rendered)
            written_alt = re.match(r'^\s*!\[([^\]]*)\]', paragraph[0])
            if len(paragraph) == 1 and re.fullmatch(r'<img [^>]*>', content) and written_alt and re.sub(r'[*`_]', '', written_alt.group(1)).strip():
                caption = re.search(r' alt="([^"]*)"', content).group(1)
                output.append(f'<figure class="figure-image">{content}<figcaption aria-hidden="true">{caption}</figcaption></figure>')
                continue
            output.append('<p>' + content + '</p>')
        return '\n'.join(output)

    def render(self, source: str) -> str:
        lines = self.extract_footnotes(source.lstrip('\ufeff').splitlines())
        for line in lines:
            reference = REFERENCE.match(line)
            if reference and not reference.group(1).startswith('^'):
                self.references[reference.group(1).casefold()] = reference.group(2) or reference.group(3)
        if re.search(r'^\s*:::', source, re.M):
            self.notes.add(self.labels['unsupported'])
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


NOSCRIPT_CSS = ('.toolbar-actions,.search-control,#nav-toggle,.rack-fold,.bar-readout{display:none!important}'
                '@media (max-width:1040px){.reader-sidebar{position:static;transform:none;visibility:visible;width:auto;'
                'height:auto;max-height:none;border-right:0;border-bottom:1.5px solid var(--ink)}}')
ICONS = {
    'station': icon(STATION, ' station'),
    'contents': icon('<path d="M9 6h11M9 12h11M9 18h11"/><path d="M4.5 6h.01M4.5 12h.01M4.5 18h.01" stroke-width="2.6"/>'),
    'search': icon('<circle cx="10.8" cy="10.8" r="6.3"/><path d="m15.6 15.6 4.4 4.4"/>'),
    'up': icon('<path d="m6.5 14.5 5.5-5.5 5.5 5.5"/>'),
    'down': icon('<path d="m6.5 9.5 5.5 5.5 5.5-5.5"/>'),
    'close': icon('<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>'),
    'ask': icon('<path d="M20 11.6a7.6 7.6 0 0 1-11.1 6.8L4 19.6l1.3-4.3A7.6 7.6 0 1 1 20 11.6Z"/><path d="M9 10.2h6M9 13.4h3.6"/>'),
    'moon': icon('<path d="M19.6 14.4A7.9 7.9 0 1 1 9.6 4.4a6.3 6.3 0 0 0 10 10Z"/>', ' theme-moon'),
    'sun': icon('<circle cx="12" cy="12" r="3.8"/><path d="M12 3v1.8M12 19.2V21M4.9 4.9l1.3 1.3M17.8 17.8l1.3 1.3M3 12h1.8M19.2 12H21M4.9 19.1l1.3-1.3M17.8 6.2l1.3-1.3"/>', ' theme-sun'),
    'print': icon('<path d="M7 8.5V4h10v4.5"/><path d="M7 17H5.5A1.5 1.5 0 0 1 4 15.5v-5A2 2 0 0 1 6 8.5h12a2 2 0 0 1 2 2v5a1.5 1.5 0 0 1-1.5 1.5H17"/><path d="M7 14h10v6H7z"/>'),
    'download': icon(DOWNLOAD),
    'unfold': icon('<path d="m7.5 9 4.5-4.5L16.5 9"/><path d="m7.5 15 4.5 4.5 4.5-4.5"/>'),
    'arrow': icon('<path d="M5 12h13"/><path d="m12.5 6.5 5.5 5.5-5.5 5.5"/>'),
    'type': '<span class="font-step" aria-hidden="true">Aa</span>',
}


def strip_cells(L: dict, lang: str, units: int, minutes: int, sections: int, subsections: int, totals: dict, notes: int) -> str:
    """The briefing strip: what the file is, counted from its own text."""
    value, unit = ((str(minutes), L['unit_minute']) if minutes < 100
                   else (f'{minutes / 60:.1f}'.removesuffix('.0'), L['unit_hour']))
    cells = [f'<div class="cell-big"><dt>{L["strip_time"]}</dt><dd><span class="strip-big">{value}</span>'
             f'<span class="strip-unit">{unit}</span></dd></div>',
             f'<div><dt>{L["strip_length"]}</dt><dd>{length_text(units, lang)}</dd></div>']
    if sections:
        parts = [L['section_value' if sections == 1 else 'sections_value'].format(n=sections)]
        if subsections:
            parts.append(L['subsection_value' if subsections == 1 else 'subsections_value'].format(n=subsections))
        cells.append(f'<div><dt>{L["strip_sections"]}</dt><dd>{L["join"].join(parts)}</dd></div>')
    held = [L[key + '_value'].format(n=totals[key]) for key in ('tables', 'figures', 'formulas') if totals[key]]
    if held:
        cells.append(f'<div><dt>{L["strip_figures"]}</dt><dd>{L["join"].join(held)}</dd></div>')
    if notes:
        cells.append(f'<div><dt>{L["strip_notes"]}</dt><dd>{L["notes_value"].format(n=notes)}</dd></div>')
    return ''.join(cells)


def render_document(source: str, *, title: str | None = None, source_path: Path | None = None, source_bytes: bytes | None = None, lang: str = 'zh') -> str:
    if lang not in LABELS:
        raise ValueError(f'unsupported language: {lang}')
    L = LABELS[lang]
    source_path = Path(source_path or Path.cwd() / 'answer.md').resolve()
    reader = MarkdownReader(source_path, lang)
    body = reader.render(source)
    title = title or next((text for level, _, text in reader.headings if level == 1), source_path.stem)

    # Measure the rendered text, then write the measurements onto the headings they belong to.
    han, words = text_units(body)
    minutes = max(1, round(reading_minutes(han, words)))
    stats = reading_stats(body, lang)
    lead, measures = section_measures(body, reader.headings)
    info, opening = outline(body, reader.headings, measures, lead)
    thousands = han + words >= 2000
    totals = {key: lead[key] + sum(item[key] for item in measures.values()) for key in ('tables', 'figures', 'formulas')}
    for _, anchor, _ in reader.headings:
        data, item = measures.get(anchor), info[anchor]
        if not data:
            continue
        attributes = f' data-units="{data["units"]}" data-minutes="{data["minutes"]:.2f}"'
        attributes += ''.join(f' data-{key}="{data[key]}"' for key in ('tables', 'figures', 'formulas', 'notes') if data[key])
        if item['fix']:
            attributes += f' data-fix="{escape(item["number"] or item["sequence"])}" data-label="{escape(item["label"])}"'
        body = body.replace(f' id="{anchor}" data-reader-section="', f' id="{anchor}"{attributes} data-reader-section="', 1)
    fixes = sum(1 for anchor, item in info.items() if item['fix'] and anchor != 'reader-footnotes')
    subsections = sum(1 for anchor, item in info.items() if not item['fix'] and not item['title'])

    # The plate stands directly under the title; the first paragraph after it is the opening.
    plate = (f'<aside class="plate" id="reader-plate" data-reader-chrome aria-label="{L["overview"]}">'
             f'<dl class="strip plate-strip">{strip_cells(L, lang, han + words, minutes, fixes, subsections, totals, len(reader.footnotes))}</dl>'
             '<div class="chart" id="reader-chart" aria-hidden="true" hidden></div>'
             '<div class="plate-dock dock" id="reader-dock" hidden>'
             '<p class="dock-here" aria-hidden="true"><span class="dock-chip num" id="dock-chip"></span><span class="dock-title" id="dock-title"></span></p>'
             '<p class="dock-go" aria-hidden="true"><span class="dock-read" id="dock-read"></span><span class="dock-left" id="dock-left"></span></p>'
             f'<button id="resume-reading" class="sign sign-go sign-small" type="button" hidden>{ICONS["arrow"]}<span class="button-label">{L["resume"]}</span></button>'
             '</div></aside>')
    titled = next((anchor for anchor, item in info.items() if item['title']), None)
    cut = body.index('</h1>', body.index(f' id="{titled}"')) + 5 if titled else 0
    head, rest = body[:cut], body[cut:].lstrip('\n')
    if rest.startswith('<p>') and '</p>' in rest:
        end = rest.index('</p>')
        rest = '<p class="lede">' + mark_opening(rest[3:end]) + rest[end:]
    body = (head + '\n' if head else '') + plate + '\n' + rest

    toc = (build_rack(reader.headings, info, opening, L['opening'], thousands)
           or f'<li class="rack-loose"><a href="#document">{L["read_all"]}</a></li>')
    fold = (f'<button id="rack-fold" class="icon-button rack-fold" type="button" aria-pressed="false" aria-label="{L["unfold"]}" title="{L["unfold"]}">{ICONS["unfold"]}</button>'
            if '<ol class="rack-sub">' in toc else '')
    unit = (f'<span class="rack-unit" id="rack-unit" aria-hidden="true">{L["rack_unit_thousands" if thousands else "rack_unit"]}</span>'
            if fixes or 'reader-footnotes' in info else '')
    css = foundation(ASSETS, lang) + '\n' + (ASSETS / 'reader.css').read_text(encoding='utf-8')
    javascript = (ASSETS / 'reader.js').read_text(encoding='utf-8')
    scripts = [javascript]
    if reader.has_math:
        try:
            math_script, math_css = katex_assets()
            scripts.insert(0, math_script)
            css = math_css + '\n' + css
        except (OSError, UnicodeError, ValueError):
            reader.notes.add(L['math_unavailable'])
    script_hashes = ' '.join("'sha256-" + base64.b64encode(hashlib.sha256(script.encode('utf-8')).digest()).decode('ascii') + "'" for script in scripts)
    style_hash = base64.b64encode(hashlib.sha256(css.encode('utf-8')).digest()).decode('ascii')
    fallback_hash = base64.b64encode(hashlib.sha256(NOSCRIPT_CSS.encode('utf-8')).digest()).decode('ascii')
    original_bytes = source_bytes if source_bytes is not None else source.encode('utf-8')
    original = base64.b64encode(original_bytes).decode('ascii')
    identity = hashlib.sha256(original_bytes).hexdigest()[:16]
    notes = ''.join('<li>' + escape(note) + '</li>' for note in sorted(reader.notes))
    note_html = '<details class="render-notes"><summary>' + L['format_notes'] + '</summary><ul>' + notes + '</ul></details>' if notes else ''
    math_enabled = len(scripts) > 1
    style_attributes = "'unsafe-inline'" if math_enabled else "'none'"
    csp = f"default-src 'none'; script-src {script_hashes}; script-src-attr 'none'; style-src 'sha256-{style_hash}' 'sha256-{fallback_hash}'; style-src-elem 'sha256-{style_hash}' 'sha256-{fallback_hash}'; style-src-attr {style_attributes}; img-src data:; connect-src 'none'; font-src data:; object-src 'none'; base-uri 'none'; form-action 'none'"
    script_html = ''.join('<script>' + script + '</script>' for script in scripts)
    section_options = ''.join(f'<option value="{anchor}">{escape(text)}</option>' for _, anchor, text in reader.headings)
    return f'''<!doctype html>
<html lang="{L['html_lang']}" data-font="medium" data-doc="{identity}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta http-equiv="Content-Security-Policy" content="{escape(csp)}">
<meta name="color-scheme" content="light dark"><meta name="generator" content="Xikari reader"><title>{escape(title)}</title>
<style>{css}</style><noscript><style>{NOSCRIPT_CSS}</style></noscript></head>
<body>
<a class="skip-link" href="#document">{L['skip']}</a>
<header class="reader-toolbar" aria-label="{L['tools']}">
<button id="nav-toggle" class="icon-button" type="button" aria-controls="contents" aria-expanded="false" aria-label="{L['open_contents']}" title="{L['contents']}">{ICONS['contents']}</button>
<a class="bar-mark" href="#document" aria-label="{L['to_start']}" title="{L['to_start']}">{ICONS['station']}</a>
<p class="toolbar-heading" aria-hidden="true"><span class="toolbar-here">{L['opening']}</span><span class="toolbar-doc">{escape(title)}</span></p>
<p class="bar-readout" id="bar-readout" aria-hidden="true"></p>
<div class="search-control" role="search">{ICONS['search']}<label class="visually-hidden" for="reader-search">{L['search']}</label><input id="reader-search" type="search" placeholder="{L['search']}" autocomplete="off" spellcheck="false" enterkeyhint="search"><kbd class="search-key" aria-hidden="true">/</kbd><span id="search-status" role="status" aria-live="polite"></span><span class="search-buttons"><button id="previous-match" class="icon-button" type="button" disabled aria-label="{L['previous_match']}" title="{L['previous_title']}">{ICONS['up']}</button><button id="next-match" class="icon-button" type="button" disabled aria-label="{L['next_match']}" title="{L['next_title']}">{ICONS['down']}</button></span><button id="search-close" class="icon-button" type="button" aria-label="{L['close_search']}">{ICONS['close']}</button></div>
<div class="toolbar-actions">
<button id="search-toggle" class="icon-button" type="button" aria-label="{L['search']}" aria-controls="reader-search" aria-expanded="false">{ICONS['search']}</button>
<button id="quote-question" class="sign sign-go sign-small" type="button" aria-controls="question-panel" aria-expanded="false">{ICONS['ask']}<span class="button-label">{L['ask_here']}</span></button>
<button id="tools-toggle" class="icon-button" type="button" aria-label="{L['settings']}" aria-controls="reading-controls" aria-expanded="false">{ICONS['type']}</button>
<div class="reading-controls" id="reading-controls">
<button id="font-smaller" class="icon-button" type="button" aria-label="{L['smaller']}" title="{L['smaller_title']}"><span class="font-step" aria-hidden="true">A</span></button>
<button id="font-larger" class="icon-button" type="button" aria-label="{L['larger']}" title="{L['larger_title']}"><span class="font-step" aria-hidden="true">A</span></button>
<button id="face-toggle" class="icon-button" type="button" aria-pressed="false" aria-label="{L['face']}" title="{L['face_title']}"><span class="face-step" aria-hidden="true">{L['face_specimen']}</span></button>
<button id="theme-toggle" class="icon-button" type="button" aria-pressed="false" aria-label="{L['night']}" title="{L['to_night']}">{ICONS['moon']}{ICONS['sun']}</button>
<button id="print-reader" class="icon-button" type="button" aria-label="{L['print']}" title="{L['print']}">{ICONS['print']}</button>
</div>
</div>
<div class="reader-progress" role="presentation"><span id="reader-progress-bar"></span></div>
</header>
<div class="track-strip" id="track-strip" aria-hidden="true" hidden><p class="strip-here"><span class="strip-chip num" id="strip-chip"></span><span class="strip-name" id="strip-name"></span></p><div class="strip-track" id="strip-track"></div><p class="strip-go" id="strip-go"></p></div>
<div class="reader-shell">
<aside id="contents" class="reader-sidebar" aria-label="{L['contents']}">
<div class="rack-head"><p class="rack-name">{L['contents']}</p>{fold}{unit}</div>
<nav aria-label="{L['sections']}"><ol class="rack">{toc}</ol></nav>
<div class="sidebar-foot"><p class="doc-stats">{escape(stats)}</p><a class="source-download sign sign-small" href="data:text/markdown;charset=utf-8;base64,{original}" download="{escape(source_path.name)}">{ICONS['download']}{L['download']}</a></div>
</aside>
<div class="reader-main">
<main><article id="document" tabindex="-1" data-lead-units="{lead['units']}" data-lead-minutes="{lead['minutes']:.2f}">{body}</article>{note_html}</main>
<footer class="reader-footer dock"><p class="footer-note">{ICONS['station']}<span>{L['footer']}</span></p><p class="footer-keys"><span class="visually-hidden">{L['keys']}</span><kbd>/</kbd>{L['keys_search']}<kbd>[</kbd><kbd>]</kbd>{L['keys_sections']}<kbd>Esc</kbd>{L['keys_close']}</p><a href="#document">{L['to_start']}</a></footer>
</div>
</div>
<div class="nav-scrim" id="nav-scrim" hidden></div>
<section id="question-panel" class="question-panel" aria-labelledby="question-title" hidden>
<div class="question-heading"><h2 id="question-title">{L['question_title']}</h2><button id="close-question" class="icon-button" type="button" aria-label="{L['close_question']}" title="{L['close_question_title']}">{ICONS['close']}</button></div>
<p id="question-help">{L['question_help']}</p>
<label class="question-label" for="question-section">{L['quote_label']}</label>
<div class="question-section"><select id="question-section"><option value="">{L['choose_section']}</option>{section_options}</select><button id="quote-section" class="sign sign-small" type="button" disabled>{L['quote_section']}</button></div>
<label class="question-label" for="question-text">{L['question_label']}</label><textarea id="question-text" rows="8" aria-describedby="question-help" placeholder="{L['question_placeholder']}"></textarea>
<div class="question-actions"><span id="question-status" role="status" aria-live="polite">{L['no_passage']}</span><button id="copy-question" class="sign sign-go sign-small" type="button" disabled>{L['copy_question']}</button></div>
</section>
<button id="selection-question" class="selection-bubble sign sign-go sign-small" type="button" hidden>{ICONS['ask']}{L['ask_selection']}</button>
<noscript><p class="no-script">{L['noscript']}</p></noscript>
{script_html}
</body></html>'''


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='完整 UTF-8 Markdown 文件')
    parser.add_argument('--output', '-o', type=Path, required=True, help='输出的单文件 HTML')
    parser.add_argument('--title', help='浏览器标签标题；不更改正文')
    parser.add_argument('--lang', choices=sorted(LABELS), default='zh', help='界面语言：zh（默认）或 en；不翻译正文')
    args = parser.parse_args()
    L = LABELS[args.lang]
    try:
        require_external_output(args.output, __file__)
        if args.input.resolve() == args.output.resolve():
            raise ValueError(L['same_file'])
        raw = args.input.read_bytes()
        text = raw.decode('utf-8-sig')
        document = render_document(text, title=args.title, source_path=args.input, source_bytes=raw, lang=args.lang)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(document, encoding='utf-8', newline='\n')
        print(json.dumps({'output': str(args.output.resolve()), 'source_bytes': len(raw), 'html_bytes': args.output.stat().st_size, 'renderer': 'python-standard-library', 'offline': True}, ensure_ascii=False))
        return 0
    except (OSError, UnicodeError, ValueError) as error:
        print(f"{L['failed']}{error}", file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
