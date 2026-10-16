"""render_docx 的规格测试：纯标准库把 Markdown 渲染成 Word .docx。"""

import importlib.util
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'render_docx.py'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

REQUIRED_PARTS = [
    '[Content_Types].xml',
    '_rels/.rels',
    'word/document.xml',
    'word/_rels/document.xml.rels',
    'word/styles.xml',
]


def module():
    spec = importlib.util.spec_from_file_location('render_docx', SCRIPT)
    target = importlib.util.module_from_spec(spec)
    sys.modules['render_docx'] = target
    spec.loader.exec_module(target)
    return target


def make_png(width=4, height=4):
    """构造一张字节合法的最小 PNG，供本地内嵌测试使用。"""

    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data
                + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    raw = b''.join(b'\x00' + b'\xff\x00\x00' * width for _ in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def docxml(path):
    with zipfile.ZipFile(path) as archive:
        return archive.read('word/document.xml').decode('utf-8')


def root_of(path):
    return ET.fromstring(docxml(path))


def all_text(path):
    return [element.text or '' for element in root_of(path).iter(W + 't')]


def paragraph_text(paragraph):
    return ''.join(element.text or '' for element in paragraph.iter(W + 't'))


def paragraph_style(paragraph):
    properties = paragraph.find(W + 'pPr')
    if properties is None:
        return None
    style = properties.find(W + 'pStyle')
    return style.get(W + 'val') if style is not None else None


def paragraph_indent(paragraph):
    properties = paragraph.find(W + 'pPr')
    if properties is None:
        return None
    indentation = properties.find(W + 'ind')
    if indentation is None:
        return None
    value = indentation.get(W + 'left')
    return int(value) if value is not None else None


class RenderDocxTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.work = Path(self.directory.name)

    def render(self, text, name='answer.md', title=None, out='out.docx'):
        source = self.work / name
        source.write_text(text, encoding='utf-8')
        target = module()
        parts = target.build_parts(text, title, source)
        output = self.work / out
        target.write_docx(output, parts, None)
        return output, source

    def test_xml_escaping(self):
        text = '# 标题 <b> & 引号"\n\n段落 <script> 与 & 符号\n'
        output, _ = self.render(text)
        document = docxml(output)
        for entity in ('&lt;', '&gt;', '&amp;', '&quot;'):
            self.assertIn(entity, document)
        self.assertNotIn('<b>', document)
        self.assertNotIn('<script>', document)
        ET.fromstring(document)
        joined = ''.join(all_text(output))
        self.assertIn('标题', joined)
        self.assertIn('引号', joined)
        self.assertIn('段落', joined)

    def test_heading_levels(self):
        text = '\n'.join(f'{"#" * level} 层{level}' for level in range(1, 7)) + '\n'
        output, _ = self.render(text)
        styles = [paragraph_style(p) for p in root_of(output).iter(W + 'p')]
        styles = [style for style in styles if style]
        self.assertEqual(styles, [f'Heading{level}' for level in range(1, 7)])

    def test_table(self):
        text = '| 列甲 | 列乙 | 列丙 |\n| --- | --- | --- |\n| 一 | 二 | 三 |\n'
        output, _ = self.render(text)
        tables = list(root_of(output).iter(W + 'tbl'))
        self.assertEqual(len(tables), 1)
        rows = list(tables[0].iter(W + 'tr'))
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(len(list(row.iter(W + 'tc'))), 3)
        joined = ''.join(all_text(output))
        for cell in ('列甲', '列乙', '列丙', '一', '二', '三'):
            self.assertIn(cell, joined)

    def test_table_preserves_backslashes(self):
        cases = (
            ('windows_path', r'D:\data\notes.csv', r'D:\data\notes.csv'),
            ('code_path', r'`D:\data\notes.csv`', r'D:\data\notes.csv'),
            ('unc_path', r'\\server\share\notes.csv', r'\\server\share\notes.csv'),
            ('code_unc_path', r'`\\server\share\notes.csv`', r'\\server\share\notes.csv'),
            ('math', r'\alpha + \beta', r'\alpha + \beta'),
            ('escaped_pipe', r'a\|b', 'a|b'),
            ('code_escaped_pipe', r'`a\|b`', 'a|b'),
        )
        for name, source, expected in cases:
            with self.subTest(name=name):
                text = f'| 内容 | 核对 |\n| --- | --- |\n| {source} | 保留 |\n'
                output, _ = self.render(text, out=f'{name}.docx')
                tables = list(root_of(output).iter(W + 'tbl'))
                self.assertEqual(len(tables), 1)
                rows = list(tables[0].iter(W + 'tr'))
                cells = list(rows[1].iter(W + 'tc'))
                self.assertEqual(len(cells), 2)
                values = [''.join(t.text or '' for t in cell.iter(W + 't')) for cell in cells]
                self.assertEqual(values, [expected, '保留'])

    def test_table_escaped_backticks_and_backslash_parity(self):
        cases = (
            ('escaped_backtick', r'| a \` literal | second |', ['a ` literal', 'second']),
            ('two_backslashes', r'| slash\\| second |', [r'slash\\', 'second']),
            ('three_backslashes', r'| slash\\\| literal | second |', [r'slash\\| literal', 'second']),
            ('four_backslashes', r'| slash\\\\| second |', [r'slash\\\\', 'second']),
        )
        for name, row, expected in cases:
            with self.subTest(name=name):
                text = '| 内容 | 核对 |\n| --- | --- |\n' + row + '\n'
                output, _ = self.render(text, out=f'{name}.docx')
                tables = list(root_of(output).iter(W + 'tbl'))
                self.assertEqual(len(tables), 1)
                rows = list(tables[0].iter(W + 'tr'))
                cells = list(rows[1].iter(W + 'tc'))
                values = [''.join(t.text or '' for t in cell.iter(W + 't')) for cell in cells]
                self.assertEqual(values, expected)

    def test_nested_lists(self):
        text = '1. 外层甲\n2. 外层乙\n    - 内层甲\n    - 内层乙\n'
        output, _ = self.render(text)
        paragraphs = list(root_of(output).iter(W + 'p'))
        outer = next(p for p in paragraphs if '外层甲' in paragraph_text(p))
        inner = next(p for p in paragraphs if '内层甲' in paragraph_text(p))
        outer_indent = paragraph_indent(outer)
        inner_indent = paragraph_indent(inner)
        self.assertIsNotNone(outer_indent)
        self.assertIsNotNone(inner_indent)
        self.assertGreater(inner_indent, outer_indent)
        joined = ''.join(all_text(output))
        for item in ('外层甲', '外层乙', '内层甲', '内层乙'):
            self.assertIn(item, joined)

    def test_page_geometry_is_explicit(self):
        output, _ = self.render('# 页面\n\n正文。\n')
        body = root_of(output).find(W + 'body')
        section = body.find(W + 'sectPr')
        self.assertIsNotNone(section)
        self.assertEqual(list(body)[-1], section)
        size, margins = section.find(W + 'pgSz'), section.find(W + 'pgMar')
        self.assertEqual((size.get(W + 'w'), size.get(W + 'h')), ('12240', '15840'))
        self.assertEqual([margins.get(W + side) for side in ('top', 'right', 'bottom', 'left')], ['1440'] * 4)

    def test_table_columns_fit_the_printable_page(self):
        for columns in (2, 4, 6, 7):
            with self.subTest(columns=columns):
                header = [f'列{index}' for index in range(columns)]
                values = [f'值{index}' for index in range(columns)]
                text = '\n'.join('| ' + ' | '.join(row) + ' |' for row in (header, ['---'] * columns, values))
                output, _ = self.render(text, out=f'table-{columns}.docx')
                table = next(root_of(output).iter(W + 'tbl'))
                grid = [int(item.get(W + 'w')) for item in table.find(W + 'tblGrid')]
                self.assertEqual(len(grid), columns)
                self.assertTrue(all(width > 0 for width in grid))
                self.assertLessEqual(sum(grid), 9360, 'Table columns must fit inside the Letter page margins.')
                width = table.find(W + 'tblPr').find(W + 'tblW')
                self.assertEqual(width.get(W + 'type'), 'dxa')
                self.assertEqual(int(width.get(W + 'w')), sum(grid))
                for row in table.findall(W + 'tr'):
                    cells = row.findall(W + 'tc')
                    self.assertEqual([int(cell.find(W + 'tcPr').find(W + 'tcW').get(W + 'w')) for cell in cells], grid)
                self.assertEqual([''.join(cell.itertext()) for cell in table.findall(W + 'tr')[1].findall(W + 'tc')], values)

    def test_code_block(self):
        text = '```\n<tag> & 值 ≤ 上限\n```\n'
        output, _ = self.render(text)
        self.assertIn('<tag> & 值 ≤ 上限', all_text(output))
        self.assertIn('Code', [paragraph_style(p) for p in root_of(output).iter(W + 'p')])

    def test_code_fences_preserve_shorter_delimiters(self):
        for marker in ('`', '~'):
            for length in (4, 6):
                with self.subTest(marker=marker, length=length):
                    fence = marker * length
                    body = ['<tag> & 值', marker * (length - 1), '# 仍在代码中',
                            '', '- 保留列表标记']
                    text = '\n'.join([fence + 'text', *body, fence, '闭合后的正文']) + '\n'
                    output, _ = self.render(text, out=f'short-{ord(marker)}-{length}.docx')
                    paragraphs = [(paragraph_text(p), paragraph_style(p))
                                  for p in root_of(output).iter(W + 'p')]
                    self.assertEqual(paragraphs, [(line, 'Code') for line in body]
                                     + [('闭合后的正文', None)])

    def test_code_fences_close_with_equal_or_longer_delimiters(self):
        for marker in ('`', '~'):
            for length in (3, 4, 6):
                for extra in (0, 2):
                    with self.subTest(marker=marker, length=length, extra=extra):
                        text = '\n'.join([marker * length + 'text', '# 代码标题',
                                          marker * (length + extra),
                                          '# 正文标题', '', '闭合后的正文']) + '\n'
                        output, _ = self.render(text, out=f'close-{ord(marker)}-{length}-{extra}.docx')
                        paragraphs = [(paragraph_text(p), paragraph_style(p))
                                      for p in root_of(output).iter(W + 'p')]
                        self.assertEqual(paragraphs, [('# 代码标题', 'Code'),
                                                     ('正文标题', 'Heading1'),
                                                     ('闭合后的正文', None)])

    def test_code_fences_ignore_other_delimiters(self):
        for marker, other in (('`', '~'), ('~', '`')):
            with self.subTest(marker=marker):
                fence = marker * 4
                body = ['第一行', other * 4, other * 6, '# 仍在代码中']
                text = '\n'.join([fence, *body, fence, '闭合后的正文']) + '\n'
                output, _ = self.render(text, out=f'other-{ord(marker)}.docx')
                paragraphs = [(paragraph_text(p), paragraph_style(p))
                              for p in root_of(output).iter(W + 'p')]
                self.assertEqual(paragraphs, [(line, 'Code') for line in body]
                                 + [('闭合后的正文', None)])

    def test_code_fences_ignore_delimiters_with_trailing_content(self):
        for marker in ('`', '~'):
            with self.subTest(marker=marker):
                fence = marker * 4
                body = [fence + 'text', marker * 6 + ' trailing content',
                        '# 仍在代码中']
                text = '\n'.join([fence, *body, fence, '闭合后的正文']) + '\n'
                output, _ = self.render(text, out=f'content-{ord(marker)}.docx')
                paragraphs = [(paragraph_text(p), paragraph_style(p))
                              for p in root_of(output).iter(W + 'p')]
                self.assertEqual(paragraphs, [(line, 'Code') for line in body]
                                 + [('闭合后的正文', None)])

    def test_unclosed_code_fences_preserve_all_body_lines(self):
        for marker in ('`', '~'):
            with self.subTest(marker=marker):
                body = ['第一行', marker * 3, '# 保留标题标记', '',
                        '- 保留列表标记', '<tag> & 最后一行']
                text = '\n'.join([marker * 4 + 'text', *body])
                output, _ = self.render(text, out=f'unclosed-{ord(marker)}.docx')
                paragraphs = [(paragraph_text(p), paragraph_style(p))
                              for p in root_of(output).iter(W + 'p')]
                self.assertEqual(paragraphs, [(line, 'Code') for line in body])

    def test_unsupported_mermaid_preserves_original_block(self):
        for marker in ('`', '~'):
            with self.subTest(marker=marker):
                opening = '  ' + marker * 4 + 'mermaid'
                closing = ' ' + marker * 5 + '  '
                code = [opening, 'graph TD', '', '    A --> B', '   ', closing]
                text = '\n'.join([*code, '闭合后的正文']) + '\n'
                output, _ = self.render(text, out=f'mermaid-{ord(marker)}.docx')
                paragraphs = [(paragraph_text(p), paragraph_style(p))
                              for p in root_of(output).iter(W + 'p')]
                self.assertEqual(paragraphs[:len(code) + 1],
                                 [(line, 'Code') for line in code] + [('闭合后的正文', None)])
                self.assertIn(('未支持语法说明', 'Heading1'), paragraphs)
                self.assertTrue(any('围栏代码块语言 mermaid 未支持，保留原文' in text
                                    and style == 'FootnoteText' for text, style in paragraphs))

    def test_all_text_readback(self):
        text = ('# 第一章 结构\n\n'
                '中文段落 Alpha beta gamma.\n\n'
                '> 引用 Delta epsilon.\n\n'
                '- 列表项 Zeta\n')
        output, _ = self.render(text)
        joined = ''.join(all_text(output))
        for fragment in ('第一章', '结构', 'Alpha beta gamma', 'Delta epsilon', 'Zeta', '引用'):
            self.assertIn(fragment, joined)

    def test_required_parts(self):
        output, _ = self.render('# 标题\n\n正文\n')
        with zipfile.ZipFile(output) as archive:
            names = archive.namelist()
            for part in REQUIRED_PARTS:
                self.assertIn(part, names)
                self.assertTrue(archive.read(part))
            styles = archive.read('word/styles.xml').decode('utf-8')
        ET.fromstring(styles)

    def test_styles_are_reachable_with_images_and_table_references(self):
        image = self.work / 'pixel.png'
        image.write_bytes(make_png())
        output, _ = self.render(
            '# 标题\n\n正文。\n\n```text\n代码\n```\n\n'
            '| 左列 | 右列 |\n| --- | --- |\n| 左值 | 右值 |\n\n'
            '![图像](pixel.png)\n'
        )
        namespace = '{http://schemas.openxmlformats.org/package/2006/relationships}'
        relationship_type = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
        with zipfile.ZipFile(output) as archive:
            relationships = list(ET.fromstring(archive.read('word/_rels/document.xml.rels')))
            self.assertTrue(all(item.tag == namespace + 'Relationship' for item in relationships))
            identifiers = [item.get('Id') for item in relationships]
            self.assertEqual(len(identifiers), len(set(identifiers)))
            style_links = [item for item in relationships if item.get('Type') == relationship_type + 'styles']
            self.assertEqual(len(style_links), 1, 'The main document must link its styles part.')
            style_link = style_links[0]
            self.assertNotEqual(style_link.get('TargetMode'), 'External')
            styles = ET.fromstring(archive.read('word/' + style_link.get('Target')))
            style_ids = {item.get(W + 'styleId') for item in styles.findall(W + 'style')}
            document = ET.fromstring(archive.read('word/document.xml'))
            referenced = {item.get(W + 'val') for tag in ('pStyle', 'tblStyle') for item in document.iter(W + tag)}
            self.assertTrue({'Heading1', 'Code', 'TableGrid', 'TableHeader'} <= referenced)
            self.assertTrue(referenced <= style_ids)
            image_links = [item for item in relationships if item.get('Type') == relationship_type + 'image']
            self.assertEqual(len(image_links), 1)
            self.assertNotEqual(style_link.get('Id'), image_links[0].get('Id'))
            self.assertIn('word/' + image_links[0].get('Target'), archive.namelist())

    def test_reject_install_dir(self):
        target = module()
        output = ROOT / 'scripts' / 'refused-render.docx'
        parts = target.build_parts('# 标题\n', None, None)
        with self.assertRaises(OSError):
            target.write_docx(output, parts, None)
        self.assertFalse(output.exists())
        self.assertFalse(output.with_name(output.name + '.lock').exists())
        self.assertEqual([p for p in output.parent.glob('.render-docx*')], [])

    def test_reject_same_path(self):
        target = module()
        source = self.work / 'answer.md'
        original = '# 标题\n\n正文\n'.encode('utf-8')
        source.write_bytes(original)
        with self.assertRaises(ValueError):
            target.render_document(source, source, None)
        self.assertEqual(source.read_bytes(), original)

    def test_reject_stale_and_locked(self):
        target = module()
        parts = target.build_parts('# 标题\n', None, None)

        output = self.work / 'out.docx'
        changed = '被其他写入者改动后的内容'.encode('utf-8')
        output.write_bytes(changed)
        with self.assertRaises(ValueError):
            target.write_docx(output, parts, '开始时记录的旧字节'.encode('utf-8'))
        self.assertEqual(output.read_bytes(), changed)

        fresh = self.work / 'locked.docx'
        lock = fresh.with_name(fresh.name + '.lock')
        lock.write_text('保留写锁', encoding='utf-8')
        with self.assertRaises(ValueError) as caught:
            target.write_docx(fresh, parts, None)
        self.assertIn('写入者', str(caught.exception))
        self.assertFalse(fresh.exists())

    def test_footnotes_end_section(self):
        text = '正文引用[^a]与更多[^b]。\n\n[^a]: 第一条证据\n[^b]: 第二条证据\n'
        output, _ = self.render(text)
        with zipfile.ZipFile(output) as archive:
            self.assertNotIn('word/footnotes.xml', archive.namelist())
        self.assertIn('superscript', docxml(output))
        joined = ''.join(all_text(output))
        self.assertIn('脚注', joined)
        self.assertIn('第一条证据', joined)
        self.assertIn('第二条证据', joined)

    def test_local_image_embedded(self):
        (self.work / 'figure.png').write_bytes(make_png())
        output, _ = self.render('![示例图](figure.png)\n')
        with zipfile.ZipFile(output) as archive:
            media = [name for name in archive.namelist() if name.startswith('word/media/')]
            relationships = archive.read('word/_rels/document.xml.rels').decode('utf-8')
            document = archive.read('word/document.xml').decode('utf-8')
        self.assertTrue(media)
        self.assertIn('Relationship', relationships)
        self.assertIn('image', relationships)
        self.assertIn('r:embed', document)
        self.assertIn('w:drawing', document)

    def test_remote_image_not_downloaded(self):
        original = socket.socket

        def forbidden(*args, **kwargs):
            raise AssertionError('渲染过程不得发起网络访问')

        socket.socket = forbidden
        try:
            output, _ = self.render('![图](https://example.com/a.png)\n')
        finally:
            socket.socket = original
        with zipfile.ZipFile(output) as archive:
            media = [name for name in archive.namelist() if name.startswith('word/media/')]
        self.assertEqual(media, [])
        self.assertIn('图像', ''.join(all_text(output)))

    def test_cli_returncode_and_streams(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.work / 'missing.md'),
             '--output', str(self.work / 'out.docx')],
            capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')
        self.assertIn('失败', result.stderr)

        source = self.work / 'same.md'
        source.write_text('# 标题\n', encoding='utf-8')
        same = subprocess.run(
            [sys.executable, str(SCRIPT), str(source), '--output', str(source)],
            capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(same.returncode, 2)
        self.assertEqual(same.stdout, '')
        self.assertIn('失败', same.stderr)

    def test_deterministic_bytes(self):
        text = '# 标题\n\n段落 **粗体** 与 *斜体*。\n\n| 甲 | 乙 |\n| --- | --- |\n| 一 | 二 |\n'
        first, _ = self.render(text, name='first.md', out='first.docx')
        second, _ = self.render(text, name='second.md', out='second.docx')
        self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == '__main__':
    unittest.main()
