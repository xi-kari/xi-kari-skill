import base64
from html.parser import HTMLParser
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]


def renderer():
    spec = importlib.util.spec_from_file_location('render_answer', ROOT / 'scripts/render_answer.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.text = []
        self._noncontent = 0
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        if tag in ('script', 'style'):
            self._noncontent += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self._noncontent -= 1

    def handle_data(self, data):
        if not self._noncontent:
            self.text.append(data)


class ReaderRenderingTests(unittest.TestCase):
    def test_windows_drive_and_unc_links_use_explicit_file_uris(self):
        module = renderer()
        reader = module.MarkdownReader(Path('D:/workspace/articles/answer.md'))
        cases = [
            ('D:/理论/完整 原文.md', 'file:///D:/' + quote('理论/完整 原文.md', safe='/')),
            (r'C:\figures\diagram.svg#overview', 'file:///C:/figures/diagram.svg#overview'),
            ('D:/docs/a%20b.html?view=full#part-2', 'file:///D:/docs/a%20b.html?view=full#part-2'),
            (r'\\fileserver\share\图 文件.svg#overview', 'file://fileserver/share/' + quote('图 文件.svg') + '#overview'),
            ('//fileserver/share/report.html#part-2', 'file://fileserver/share/report.html#part-2'),
            ('D:/docs/literal%23name.md#part-2', 'file:///D:/docs/literal%23name.md#part-2'),
        ]
        with patch.object(module.Path, 'resolve', side_effect=AssertionError('Link formatting must not inspect its target')):
            for target, expected in cases:
                with self.subTest(target=target):
                    output = reader.inline('[本地材料](<' + target + '>)')
                    href = next(attrs['href'] for tag, attrs in Document(output).tags if tag == 'a')
                    self.assertEqual(href, expected)

    def test_external_anchor_and_relative_link_semantics_remain_intact(self):
        module = renderer()
        reader = module.MarkdownReader(Path('D:/workspace/articles/answer.md'))
        cases = [
            ('https://example.com/a?x=1&y=2#top', 'https://example.com/a?x=1&y=2#top'),
            ('mailto:reader@example.com?subject=Hello', 'mailto:reader@example.com?subject=Hello'),
            ('#section-2', '#section-2'),
            ('file:///D:/docs/a%20b.html#part-2', 'file:///D:/docs/a%20b.html#part-2'),
            ('../figures/a%20b.svg#view', 'file:///D:/workspace/figures/a%20b.svg#view'),
        ]
        with patch.object(module.Path, 'resolve', side_effect=AssertionError('Link formatting must not inspect its target')):
            for target, expected in cases:
                with self.subTest(target=target):
                    output = reader.link('材料', target)
                    href = next(attrs['href'] for tag, attrs in Document(output).tags if tag == 'a')
                    self.assertEqual(href, expected)

    def test_literal_heading_suffix_and_malformed_url_are_preserved(self):
        output = renderer().render_document('# C#\n\n[坏地址](http://[)')
        self.assertIn('C#', ''.join(Document(output).text))
        self.assertIn('坏地址', ''.join(Document(output).text))

    def test_longform_blocks_and_nested_lists_preserve_content(self):
        source = '# 标题\n\n段落 **强调**，含 [链接](https://example.com)。\n\n## 同名\n\n> 引文\n> 第二行\n\n3. 第三项\n   - 内层甲\n   - 内层乙\n4. 第四项\n\n| 项目 | 意义 |\n| :--- | ---: |\n| 原文 | a\\|b |\n\n```python\nprint("<hello>")\n```\n\n## 同名\n\n末尾完整。'
        output = renderer().render_document(source)
        document = Document(output)
        tags = [tag for tag, _ in document.tags]
        for tag in ('h1', 'h2', 'blockquote', 'ol', 'ul', 'table', 'pre', 'code', 'a'):
            self.assertIn(tag, tags)
        for text in ('内层甲', '内层乙', '第四项', 'a|b', 'print("<hello>")', '末尾完整。'):
            self.assertIn(text, ''.join(document.text))
        self.assertTrue(any(tag == 'ol' and attrs.get('start') == '3' for tag, attrs in document.tags))
        ids = [attrs['id'] for _, attrs in document.tags if 'id' in attrs]
        self.assertEqual(len(ids), len(set(ids)))

    def test_html_and_unsafe_links_are_inert(self):
        source = '# 安全\n\n<script>alert(1)</script>\n\n<img src=x onerror=alert(2)>\n\n[坏链接](javascript:alert(3))\n\n[编码](java%73cript:alert(4))\n\n```html\n</script><script>alert(5)</script>\n```'
        output = renderer().render_document(source)
        document = Document(output)
        self.assertEqual(sum(tag == 'script' for tag, _ in document.tags), 1)
        for tag, attrs in document.tags:
            self.assertFalse(any(name.startswith('on') for name in attrs))
            if tag == 'a':
                self.assertNotIn('javascript:', attrs.get('href', '').lower())
        self.assertIn('<script>alert(1)</script>', ''.join(document.text))
        self.assertIn('Content-Security-Policy', output)

    def test_source_roundtrip_and_unsupported_extensions_remain_visible(self):
        source = '# 原文\r\n\r\n$$ x^2 $$\r\n\r\n[^note]: 扩展脚注\r\n\r\n:::unknown\r\n扩展内容\r\n:::\r\n'
        output = renderer().render_document(source)
        match = re.search(r'href="data:text/markdown;charset=utf-8;base64,([A-Za-z0-9+/=]+)"', output)
        self.assertEqual(base64.b64decode(match.group(1)).decode('utf-8'), source)
        for text in ('$$ x^2 $$', '扩展脚注', ':::unknown', '扩展内容'):
            self.assertIn(text, ''.join(Document(output).text))

    def test_stable_heading_ids_survive_unrelated_insertions(self):
        def ids(source):
            return {attrs['data-section-title']: attrs['id'] for tag, attrs in Document(renderer().render_document(source)).tags if 'data-reader-section' in attrs}
        before = ids('# 总题\n\n## 稳定章节\n\n内容\n\n**第二条　规则**\n')
        after = ids('# 总题\n\n## 新增章节\n\n新内容\n\n## 稳定章节\n\n内容\n\n**第二条　规则**\n')
        self.assertEqual(before['稳定章节'], after['稳定章节'])
        self.assertEqual(before['第二条　规则'], after['第二条　规则'])
        self.assertNotEqual(after['新增章节'], after['稳定章节'])

    def test_footnote_multiple_references_and_code_are_preserved(self):
        source = '# 脚注\n\n第一次[^a]，第二次[^a]，未知[^missing]。\n\n[^a]: 证据段落。\n\n    第二段有[出处](https://example.com)。\n\n```text\n[^code]: 代码，不是脚注\n```\n'
        output = renderer().render_document(source)
        doc = Document(output)
        references = [attrs for tag, attrs in doc.tags if attrs.get('role') == 'doc-noteref']
        back = [attrs for tag, attrs in doc.tags if attrs.get('class') == 'footnote-backref']
        self.assertEqual(len(references), 2)
        self.assertEqual(len(back), 2)
        self.assertEqual(references[0]['href'], references[1]['href'])
        self.assertEqual({x['href'][1:] for x in back}, {x['id'] for x in references})
        for text in ('证据段落', '第二段', '[^missing]', '[^code]: 代码，不是脚注'):
            self.assertIn(text, ''.join(doc.text))

    def test_reading_progress_and_sidebar_affordances_are_present(self):
        output = renderer().render_document('# 长篇阅读\n\n## 第一节\n\n正文。\n')
        document = Document(output)
        identifiers = [attrs.get('id') for _, attrs in document.tags if attrs.get('id')]
        self.assertIn('reader-progress-bar', identifiers)
        progress = next(attrs for _, attrs in document.tags if attrs.get('class') == 'reader-progress')
        self.assertEqual(progress.get('role'), 'presentation')
        self.assertIn('class="reader-progress"', output)
        for token in ('--accent-soft', '--ink-strong', '--quote-rule', '--radius-lg'):
            self.assertIn(token + ':', output)

    def test_math_currency_and_code_are_distinguished_and_offline(self):
        source = r'# 公式' + '\n\n' + r'原式 \(x^2\)，也可用 $y+1$。价格 $5 与 $10。代码 `$z$`。' + '\n\n$$\\frac{a}{b}$$\n'
        output = renderer().render_document(source)
        doc = Document(output)
        formulas = [attrs for _, attrs in doc.tags if 'data-tex' in attrs]
        self.assertEqual([x['data-tex'] for x in formulas], ['x^2', 'y+1', r'\frac{a}{b}'])
        self.assertIn('价格 $5 与 $10', ''.join(doc.text))
        self.assertIn('$z$', ''.join(doc.text))
        self.assertIn('data:font/woff2;base64,', output)
        self.assertIn('connect-src &#x27;none&#x27;', output)
        self.assertFalse(any(tag == 'script' and 'src' in attrs for tag, attrs in doc.tags))
        plain = renderer().render_document('# 没有公式\n\n普通段落')
        self.assertNotIn('data:font/woff2;base64,', plain)

    def test_missing_math_assets_preserve_formula_and_other_controls(self):
        module = renderer()
        with patch.object(module, 'katex_assets', side_effect=OSError('missing')):
            output = module.render_document('# 公式\n\n$$x^2$$')
        doc = Document(output)
        self.assertIn('$$x^2$$', ''.join(doc.text))
        self.assertIn('公式排版资源不可用', ''.join(doc.text))
        self.assertTrue(any(attrs.get('id') == 'question-text' for _, attrs in doc.tags))

    def test_mermaid_is_honestly_preserved_not_executed(self):
        source = '# 图\n\n```mermaid\nflowchart LR\n A[材料] --> B[判断]\n```'
        output = renderer().render_document(source)
        self.assertIn('Mermaid 图示源码', output)
        self.assertIn('flowchart LR', output)
        self.assertNotIn('mermaid.min.js', output)

    def test_reference_links_and_wide_table_do_not_drop_extra_cells(self):
        source = '[原书][book]\n\n[book]: https://example.com/source\n\n| 甲 | 乙 |\n| --- | --- |\n| 一 | 二 | 三，必须保留 |'
        output = renderer().render_document(source)
        document = Document(output)
        self.assertIn('三，必须保留', ''.join(document.text))
        self.assertTrue(any(tag == 'a' and attrs.get('href') == 'https://example.com/source' for tag, attrs in document.tags))

    def test_local_images_embed_and_remote_or_missing_images_keep_alt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'local.png').write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jDioAAAAASUVORK5CYII='))
            source = '![本地图](local.png)\n\n![远程图](https://example.com/x.png)\n\n![缺失图](absent.svg)'
            output = renderer().render_document(source, source_path=root / 'answer.md')
            images = [attrs for tag, attrs in Document(output).tags if tag == 'img']
            self.assertEqual(len(images), 1)
            self.assertTrue(images[0]['src'].startswith('data:image/png;base64,'))
            self.assertEqual(images[0]['alt'], '本地图')
            self.assertIn('远程图', output)
            self.assertIn('缺失图', output)

    def test_svg_script_is_not_embedded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'bad.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>', encoding='utf-8')
            output = renderer().render_document('![说明](bad.svg)', source_path=root / 'answer.md')
            self.assertNotIn('data:image/svg+xml', output)
            self.assertIn('说明', output)

    def test_cli_preserves_source_and_emits_self_contained_document(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / '完整 原文.md'
            target = root / '阅读版.html'
            original = '\ufeff# 完整标题\r\n\r\n**第二十七条　最终条款**\r\n\r\n最后一段。'.encode('utf-8')
            source.write_bytes(original)
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/render_answer.py'), str(source), '--output', str(target)], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(source.read_bytes(), original)
            output = target.read_text(encoding='utf-8')
            self.assertIn('第二十七条', output)
            self.assertIn('最后一段。', output)
            document = Document(output)
            self.assertFalse(any(tag == 'script' and 'src' in attrs for tag, attrs in document.tags))
            self.assertFalse(any(tag == 'link' and attrs.get('rel') == 'stylesheet' for tag, attrs in document.tags))
            source_uri = next(attrs['href'] for tag, attrs in document.tags if tag == 'a' and attrs.get('download'))
            self.assertEqual(base64.b64decode(source_uri.split(',', 1)[1]), original)


if __name__ == '__main__':
    unittest.main()
