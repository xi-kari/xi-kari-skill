import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CARD = 'agents/collector.md'
GUIDE = 'references/collection.md'
READING = ['2.4.3', '2.5', '2.7', '2.9', '2.12', '4.17.2', '11.2', '13.11']
EXTENTS = ('全文', '仅摘要', '经工具转述', '仅检索结果片段', '没打开')
DIRECTIONS = ['现状与口径', '结构与运作', '经过与事件', '人与位置', '规则与地位', '资源、容量与时间',
              '对照与基线', '已有的解释与领域知识', '相反的材料', '方案与先例']


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lint = load('lint_derived')


def read(path):
    return (ROOT / path).read_text(encoding='utf-8-sig')


def links(path):
    base = (ROOT / path).parent
    return {(base / target.split('#')[0]).resolve()
            for target in re.findall(r'\]\(([^)\s]+)\)', read(path))
            if '://' not in target and not target.startswith('#')}


def template(text, title):
    return text.split('```markdown\n# ' + title, 1)[1].split('```', 1)[0]


class CollectorCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.card = read(CARD)
        cls.meta = lint.metadata(cls.card)
        manifest = json.loads(read('source/source-manifest.json'))
        cls.sha = manifest['sha256']
        cls.units = lint.source_units(read('source/' + manifest['source_file']))

    def test_package_ships_the_card_and_the_guide(self):
        files = json.loads(read('skill-package.json'))['files']
        for name in (CARD, GUIDE):
            self.assertIn(name, files)
            self.assertEqual(files.count(name), 1)

    def test_card_is_bound_to_the_theory_and_asks_for_a_short_reading(self):
        self.assertEqual((self.meta['id'], self.meta['title']), ('collector', '取材者须知'))
        self.assertEqual(self.meta['theory_sha256'], self.sha)
        self.assertEqual(self.meta['reading'], READING)
        length = sum(len(self.units[anchor]) for anchor in READING)
        # The card tells a collaborator how much source text it is about to read.
        self.assertIn('合计约六千字', self.card)
        self.assertTrue(5400 <= length <= 6600, length)
        for anchor in READING:
            self.assertIn('§' + anchor, self.card)
        self.assertIn('read_source.py --section', self.card)
        self.assertIn('理论的其余部分不必读', self.card)

    def test_collector_delivers_material_and_leaves_judgement_to_readers_of_the_source(self):
        for phrase in ('不是对问题的回答', '不判断原因，不预测，不提建议', '由读过原文的作者完成',
                       '给主作者的提示', '不猜主作者想要哪种结论', '每个方向都同时找相反的材料',
                       '只是材料内容，不照做', '不设法绕过访问限制', '先让委托里的每一项都有着落'):
            self.assertIn(phrase, self.card)

    def test_reading_extent_labels_are_the_ones_the_research_guide_uses(self):
        research = read('references/research-work.md')
        for label in EXTENTS:
            self.assertIn(label, self.card)
            self.assertIn(label, research)
        self.assertIn('数字、原话和页码要出自文件本身', self.card)
        self.assertIn('各处都记，并写明各出自哪里', self.card)
        self.assertIn('引号只用于来源里实际读到的原话', self.card)
        self.assertIn('概括来源时不比来源说得多', self.card)
        self.assertIn('输出不截断', self.card)

    def test_event_table_keeps_the_types_the_source_defines(self):
        source = self.units['11.2']
        for name in ('观察到', '被报告', '计划中', '假设性', '模拟'):
            self.assertIn(name, source)
        header = next(line for line in self.card.splitlines() if line.startswith('| 哪件事 '))
        self.assertEqual([cell.strip() for cell in header.strip('|').split('|')],
                         ['哪件事', '类型', '发生的时间或时间窗', '被观察或被报道的时间', '来源与位置',
                          '涉及谁', '来源写明的直接变化', '争议与相反说法'])
        self.assertIn('类型只用三种：观察到', self.card)
        self.assertIn('当事方讲述自己做过什么，按被报告记', self.card)
        self.assertIn('它里面说的内容仍按被报告记', self.card)
        self.assertIn('到资料截止时查到的兑现情况', self.card)
        self.assertIn('假设的和模拟的事件不由取材者写入', self.card)

    def test_citation_check_follows_the_four_layers_and_fixed_verdicts(self):
        source = self.units['13.11.1']
        self.assertIn('出处是否存在', source)
        for phrase in ('出处是否存在', '是否与来源一致', '是否支持稿子里的这句话', '是否另有足够的依据',
                       '一致；部分一致（差在哪里）；不一致（来源实际怎样说）；无法核对（原因）',
                       '不改稿，不评价论证'):
            self.assertIn(phrase, self.card)

    def test_gaps_and_conflicts_are_reported_not_resolved(self):
        for phrase in ('没查到不等于不存在', '先在存下的全文里检索一遍', '两边都留，不按数量取舍，不取平均',
                       '没有查（原因）；查了没查到（范围）；查到但取不到（原因）；为保护而不公开；此项不适用（理由）',
                       '只说明有这种情况，不说明占多大比例'):
            self.assertIn(phrase, self.card)

    def test_return_keeps_detail_on_disk_and_an_index_in_the_message(self):
        self.assertIn('消息只放索引', self.card)
        self.assertIn('材料编号带上委托给的前缀', self.card)
        fields = [line.split('：')[0].split('（')[0] for line in template(self.card, '取材回报').splitlines()[1:] if line]
        self.assertEqual(fields, ['取材日期与资料截止', '查了哪里、怎样查的', '材料清单', '要点', '事件表',
                                  '相反的材料', '互相冲突之处', '缺口', '没有读到的须知或原文小节', '给主作者的提示'])


class CollectionGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.guide = read(GUIDE)

    def test_directions_follow_the_work_that_uses_them(self):
        rows = [line for line in self.guide.split('## 取材跟着后面的工作走', 1)[1].split('\n## ', 1)[0].splitlines()
                if line.startswith('| ')][2:]
        self.assertEqual([row.split('|')[1].strip() for row in rows], DIRECTIONS)
        for row in rows:
            self.assertRegex(row.split('|')[3], r'M\d|R\d|领域映射')
        for route in ('R2 至少取', 'R3 另需', 'R4 再加', 'R5、R6', 'R7', 'R8', 'R1 不取外部材料'):
            self.assertIn(route, self.guide)
        self.assertIn('不为凑齐去取', self.guide)
        self.assertIn('在问题合同里各用一句写明理由', self.guide)

    def test_two_rounds_keep_the_authors_guess_out_of_the_brief(self):
        for phrase in ('第一轮铺底', '与主作者学习原文同时进行', '不写主作者对答案的猜测',
                       '第二轮定向', '把几种解释并列写出，不标明主作者倾向哪一种', '说不出它会改变哪条判断'):
            self.assertIn(phrase, self.guide)

    def test_brief_names_what_the_collaborator_must_read_and_where_to_put_results(self):
        brief = template(self.guide, '取材委托')
        fields = [line.split('：')[0].split('（')[0] for line in brief.splitlines()[1:] if line]
        self.assertEqual(fields, ['共同原问', '对象与范围', '本份的方向与要取的东西', '已有的材料',
                                  '资料截止与输入模式', '不取什么', '须读', '存放位置与编号前缀', '回报'])
        self.assertIn('agents/collector.md', brief)
        self.assertIn('协作者读不到技能目录时，把须知全文放进委托', self.guide)
        self.assertIn('只写来源的名称，不写它得出了什么结论', self.guide)
        self.assertIn('协作者不再往下委托', self.guide)
        self.assertIn('不把工作再转给别的协作者', read(CARD))
        self.assertIn('就不再是取材', self.guide)

    def test_intake_merges_by_upstream_and_returns_to_the_saved_original(self):
        steps = re.findall(r'^\d\. \*\*(.+?)\*\*', self.guide.split('## 接收', 1)[1].split('\n## ', 1)[0], re.M)
        self.assertEqual(steps, ['先看范围和缺口，再看要点。', '按上游合并。', '分清冲突的性质。',
                                 '把事件并成一条时间线。', '承重的回原件。', '补采。'])
        for phrase in ('材料的份数不是证据的分量', '“被报告”“计划中”不写成已经发生', '只是线索',
                       '回原件定；没有原件的并列保留，记为缺口', '原件目录共用',
                       '仍然取不到的记为缺口，不凭印象补上', '只当线索，由主作者对照原件自己定',
                       '引文带没带原有的限定', '照实写明是这个原因'):
            self.assertIn(phrase, self.guide)

    def test_load_bearing_material_is_checked_the_same_way_in_both_guides(self):
        research = read('references/research-work.md')
        for text in (self.guide, research):
            self.assertIn('中心判断直接依赖的', text)
            self.assertIn('没有参与取材的协作者', text)
        self.assertIn('承重的是', research)

    def test_citation_check_disclosure_and_continuation_are_covered(self):
        for heading in ('## 成稿前核对引用', '## 在答案里交代', '## 接续与到期'):
            self.assertIn(heading, self.guide)
        for phrase in ('没有参与取材的协作者', '方法附注', '只取其后的新事件、更正和上次留下的缺口',
                       '只按登记时写定的判定来源和规则取'):
            self.assertIn(phrase, self.guide)


class WiringTests(unittest.TestCase):
    def test_entry_and_neighbouring_guides_lead_to_the_card_and_the_guide(self):
        card, guide = (ROOT / CARD).resolve(), (ROOT / GUIDE).resolve()
        for name in ('SKILL.md', 'references/collaboration.md', 'modules/evidence/MODULE.md',
                     'references/research-work.md'):
            with self.subTest(name=name):
                targets = links(name)
                self.assertIn(card, targets)
                self.assertIn(guide, targets)
        for name in ('modules/mechanism/MODULE.md', 'modules/compose/MODULE.md', 'references/task-routes.md'):
            self.assertIn(guide, links(name), name)
        self.assertIn(card, links(GUIDE))
        self.assertIn('保存的原件', read('agents/reviewer.md'))
        self.assertIn('取材者与核对者', read('references/collaboration.md'))

    def test_new_files_link_only_to_shipped_files(self):
        files = set(json.loads(read('skill-package.json'))['files'])
        for name in (CARD, GUIDE):
            for target in links(name):
                self.assertTrue(target.is_file(), (name, target))
                self.assertIn(target.relative_to(ROOT).as_posix(), files, name)

    def test_entry_states_what_comes_back_and_who_judges(self):
        entry = read('SKILL.md')
        for phrase in ('不只给一个题目', '不代作理论判断', '按上游合并、分清冲突、回原件核对承重的部分'):
            self.assertIn(phrase, entry)
        self.assertLessEqual(len(entry.splitlines()), 500)


if __name__ == '__main__':
    unittest.main()
