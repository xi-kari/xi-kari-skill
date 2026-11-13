import base64
from html.parser import HTMLParser
import importlib.util
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def renderer():
    spec = importlib.util.spec_from_file_location('render_answer', ROOT / 'scripts/render_answer.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Page(HTMLParser):
    """Collect start tags and, for the article, the order its direct children open in."""

    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.stack = []
        self.children = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if self.stack and self.stack[-1][1].get('id') == 'document':
            self.children.append((tag, attributes))
        self.tags.append((tag, attributes))
        if tag not in ('meta', 'br', 'img', 'input', 'hr', 'link', 'path', 'circle', 'rect'):
            self.stack.append((tag, attributes))

    def handle_startendtag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                return


LONG = ('# 标题：副题\n\n**开头一句给出判断。**后面是说明。\n\n## 一、材料\n\n' + '材料正文。' * 80 + '\n\n| 甲 | 乙 |\n| --- | --- |\n| 1 | 2 |\n\n'
        '### 1.1 细目\n\n' + '细目正文。' * 40 + '\n\n## 二、机制\n\n' + '机制正文。' * 160 + '行内 \\(y\\) 不计入。[^n]\n\n$$x^2$$\n\n[^n]: 注。\n')


class ReaderChartTests(unittest.TestCase):
    def sections(self, source, **options):
        output = renderer().render_document(source, **options)
        return output, [attrs for _, attrs in Page(output).tags if 'data-reader-section' in attrs]

    def test_every_heading_carries_the_length_of_the_text_it_opens(self):
        output, sections = self.sections(LONG)
        by_title = {item['data-section-title']: item for item in sections}
        self.assertEqual(set(by_title), {'标题：副题', '一、材料', '1.1 细目', '二、机制', '脚注'})
        self.assertGreater(int(by_title['二、机制']['data-units']), int(by_title['一、材料']['data-units']))
        # eighty four-character sentences, the heading's three characters, and the table's two characters and two numbers
        self.assertEqual(int(by_title['一、材料']['data-units']), 80 * 4 + 3 + 4)
        self.assertEqual(by_title['一、材料']['data-tables'], '1')
        self.assertEqual(by_title['二、机制']['data-notes'], '1')
        self.assertNotIn('data-tables', by_title['1.1 细目'])
        total = sum(int(item['data-units']) for item in sections)
        stated = re.search(r'全文约 ([\d,]+) 字', output)
        self.assertAlmostEqual(total, int(stated.group(1).replace(',', '')), delta=60)

    def test_strip_and_track_count_formulas_and_figures_the_same_way(self):
        output, sections = self.sections(LONG)
        by_title = {item['data-section-title']: item for item in sections}
        # one set-off formula; the inline one is text and is neither counted nor plotted
        self.assertEqual(by_title['二、机制']['data-formulas'], '1')
        self.assertIn('表 1 · 式 1', output)
        self.assertEqual(output.count('class="reader-math math-display"'), 1)
        self.assertEqual(output.count('class="reader-math"'), 1)

    def test_fixes_are_the_top_level_sections_with_their_own_numbers(self):
        _, sections = self.sections(LONG)
        fixes = {item['data-section-title']: item['data-fix'] for item in sections if 'data-fix' in item}
        self.assertEqual(fixes, {'一、材料': '一', '二、机制': '二', '脚注': ''})
        labels = {item['data-section-title']: item['data-label'] for item in sections if 'data-fix' in item}
        self.assertEqual(labels['一、材料'], '材料')

    def test_unnumbered_fixes_are_numbered_in_sequence_without_touching_the_text(self):
        output, sections = self.sections('# 题\n\n## 甲\n\n正文。\n\n## 乙\n\n正文。\n')
        self.assertEqual([item['data-fix'] for item in sections if 'data-fix' in item], ['01', '02'])
        page = Page(output)
        headings = [attrs for tag, attrs in page.children if tag == 'h2']
        self.assertEqual([item['data-section-title'] for item in headings], ['甲', '乙'])
        self.assertIn('>甲</h2>', output)
        self.assertIn('<span class="toc-seq num" aria-hidden="true">01</span>', output)

    def test_a_document_of_parts_takes_its_parts_as_fixes(self):
        _, sections = self.sections('# 第一部分\n\n## 甲\n\n正文。\n\n# 第二部分\n\n## 乙\n\n正文。\n')
        self.assertEqual([item['data-section-title'] for item in sections if 'data-fix' in item], ['第二部分'])
        _, sections = self.sections('前言。\n\n## 甲\n\n正文。\n\n# 唯一标题\n\n## 乙\n\n正文。\n')
        self.assertEqual([item['data-section-title'] for item in sections if 'data-fix' in item], ['甲', '乙'])

    def test_plate_stands_under_the_title_and_the_strip_is_counted_from_the_text(self):
        output, _ = self.sections(LONG)
        children = Page(output).children
        order = [(tag, attrs.get('class') or attrs.get('id')) for tag, attrs in children][:5]
        self.assertEqual(order[1][0], 'h1')
        self.assertEqual(order[2], ('aside', 'plate'))
        self.assertEqual(order[3], ('p', 'lede'))
        self.assertIn('data-reader-chrome', output)
        for label in ('读完约', '篇幅', '章节', '图表', '脚注'):
            self.assertIn(f'<dt>{label}</dt>', output)
        self.assertIn('2 节 · 1 小节', output)
        self.assertIn('<span class="toolbar-here">开篇</span>', output)
        self.assertIn('id="track-strip" aria-hidden="true" hidden', output)

    def test_opening_sentence_is_marked_only_where_the_source_marks_it(self):
        module = renderer()
        self.assertIn('<p class="lede"><strong class="key">开头一句给出判断。</strong>后面是说明。</p>', self.sections(LONG)[0])
        self.assertEqual(module.mark_opening('没有加粗的一句。后文'), '没有加粗的一句。后文')
        self.assertEqual(module.mark_opening('<strong>标签</strong>：正文。'), '<strong>标签</strong>：正文。')
        self.assertEqual(module.mark_opening('前面有字<strong>再加粗。</strong>'), '前面有字<strong>再加粗。</strong>')
        self.assertEqual(module.mark_opening('<strong>全句加粗。</strong>后文'), '<strong class="key">全句加粗。</strong>后文')
        self.assertEqual(module.mark_opening('<strong>He said “yes.”</strong> More'), '<strong class="key">He said “yes.”</strong> More')
        plain = renderer().render_document('# 题\n\n开头没有加粗。后文。\n\n## 节\n\n正文。\n')
        self.assertIn('<p class="lede">开头没有加粗。后文。</p>', plain)
        self.assertNotIn('class="key"', plain)
        direct = renderer().render_document('# 题\n\n## 直接进入小节\n\n正文。\n')
        self.assertNotIn('class="lede"', direct)

    def test_a_title_breaks_after_its_own_punctuation_and_keeps_its_text(self):
        output, sections = self.sections('# 审批上收之后，投诉为什么反而上升：一个机制诊断\n\n正文。\n\n## 节\n\n正文。\n')
        self.assertIn('<span class="title-main"><span class="seg">审批上收之后，</span><span class="seg">投诉为什么反而上升</span>'
                      '<span class="title-colon">：</span></span><span class="title-sub">一个机制诊断</span>', output)
        self.assertEqual(sections[0]['data-section-title'], '审批上收之后，投诉为什么反而上升：一个机制诊断')
        self.assertNotIn('class="seg"', renderer().render_document('# 没有标点的标题\n\n正文。\n'))

    def test_rack_opens_with_the_opening_and_its_lengths_add_up(self):
        output, sections = self.sections(LONG)
        rack = output[output.index('<ol class="rack">'):output.index('</nav>')]
        self.assertEqual(rack.count('class="toc-level-2 rack-bay"'), 3)
        self.assertEqual(rack.count('class="rack-bay rack-entry"'), 1)
        self.assertEqual(rack.count('<ol class="rack-sub">'), 1)
        links = re.findall(r'<a href="#([^"]+)">(.*?)</a>', rack)
        self.assertEqual([re.sub(r'<[^>]+>', '', text) for _, text in links], ['开篇', '一、材料', '1.1 细目', '二、机制', '脚注'])
        self.assertEqual(links[0][0], sections[0]['id'], 'The opening strip leads to the title.')
        self.assertNotIn('rack-title', rack)
        self.assertIn('id="rack-fold"', output)
        self.assertIn('<span class="rack-unit" id="rack-unit" aria-hidden="true">字</span>', output)
        lengths = [int(value) for value in re.findall(r'<span class="toc-min num">(\d+)</span>', rack)]
        self.assertEqual(len(lengths), 4)
        self.assertEqual(sum(lengths), sum(int(item['data-units']) for item in sections), 'The column adds up to the measured text.')
        stated = int(re.search(r'全文约 ([\d,]+) 字', output).group(1).replace(',', ''))
        self.assertEqual(round(sum(lengths), -2), stated, 'The plate states the same whole, rounded.')

    def test_long_documents_state_rack_lengths_in_thousands(self):
        output, _ = self.sections('# 题\n\n## 甲\n\n' + '正文内容。' * 300 + '\n\n## 乙\n\n' + '正文内容。' * 400 + '\n')
        self.assertIn('<span class="rack-unit" id="rack-unit" aria-hidden="true">千字</span>', output)
        self.assertEqual(re.findall(r'<span class="toc-min num">([^<]+)</span>', output), ['&lt;0.1', '1.2', '1.6'])

    def test_rounded_rack_lengths_still_add_up_to_the_stated_whole(self):
        module = renderer()
        # 2,350 units: rounding each strip alone would give 0.3 + 0.3 + 0.3 + 0.3 + 0.3 + 0.3 + 0.7 = 2.5 against a stated 2.4
        parts = [250, 250, 250, 250, 250, 250, 850]
        shown = module.rack_lengths(parts, True)
        self.assertEqual(round(sum(float(value) for value in shown), 1), 2.4)
        self.assertTrue(all(abs(float(value) * 1000 - units) < 100 for value, units in zip(shown, parts)))
        self.assertEqual(module.rack_lengths([137, 0, 19], False), ['137', '0', '19'])
        self.assertEqual(module.rack_lengths([20, 0, 2400], True), ['&lt;0.1', '0', '2.4'])
        source = '# 题\n\n' + ''.join(f'## 节{index}\n\n' + '正文内容。' * (60 + index * 7) + '\n\n' for index in range(9))
        output, _ = self.sections(source)
        column = [float(value) for value in re.findall(r'<span class="toc-min num">([\d.]+)</span>', output)]
        stated = int(re.search(r'全文约 ([\d,]+) 字', output).group(1).replace(',', ''))
        self.assertEqual(round(sum(column) * 1000), stated)

    def test_text_without_sections_gets_a_strip_and_no_track_data(self):
        output, sections = self.sections('只有一段话。\n')
        self.assertEqual(sections, [])
        self.assertIn('id="reader-plate"', output)
        self.assertNotIn('<dt>章节</dt>', output)
        self.assertNotIn('id="rack-fold"', output)
        self.assertNotIn('class="rack-bay rack-entry"', output)
        lead = re.search(r'data-lead-units="(\d+)"', output)
        self.assertEqual(int(lead.group(1)), 5)

    def test_display_face_is_inlined_and_covers_every_display_string(self):
        module = renderer()
        output = module.render_document('# 题\n\n正文。\n')
        face = re.search(r'@font-face\{font-family:"XK Display";[^}]*src:url\("data:font/woff2;base64,([A-Za-z0-9+/=]+)"\)', output)
        self.assertIsNotNone(face)
        self.assertEqual(base64.b64decode(face.group(1)), (ROOT / 'assets/fonts/xk-display.woff2').read_bytes())
        self.assertIn('font-src data:', output)
        english = module.render_document('# Title\n\nText.\n', lang='en')
        latin = base64.b64encode((ROOT / 'assets/fonts/xk-display-latin.woff2').read_bytes()).decode('ascii')
        self.assertIn(latin, english)

    def test_english_strip_has_no_chinese_and_counts_singular(self):
        output = renderer().render_document('# T\n\n**One sentence here is the opening one.** More.\n\n## A\n\nText.\n\n### A1\n\nText.\n', lang='en')
        visible = re.sub(r'<(script|style)>.*?</\1>', '', output, flags=re.S)
        self.assertIsNone(re.search(r'[一-鿿]', visible))
        self.assertIn('<dd>1 section · 1 subsection</dd>', visible)
        self.assertIn('<strong class="key">One sentence here is the opening one.</strong>', visible)
        self.assertIn('<span class="toolbar-here">Start</span>', visible)
        self.assertIn('>Download Markdown</a>', visible)


if __name__ == '__main__':
    unittest.main()
