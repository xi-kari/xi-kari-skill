import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rule_card_lint', ROOT / 'scripts/lint_derived.py')
lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint)

STATE_LIMITS = {
    'S0': '- 核查原文判据「它不能证明参与者缺乏能力、价值或意愿，也不能授权扶持、解散、筛选或排除。」。〔原文 §8.3.1〕',
    'S1': '- 核查原文判据「这个原型不能被读成“幼稚”“落后”或“应被整合”。它也不能赋予生成者永久领导、扩大权力、强制建制或替换他人的资格。」。〔原文 §8.3.2〕',
    'S2': '- 核查原文判据「这个原型不允许把不认同者、退出者或模糊参与者本身称作负向主体，也不允许用“扩维需要”来授权统一思想、限制退出或清退异议。」。〔原文 §8.3.3〕',
    'S3': '- 核查原文判据「归入这个原型，不能授权“打壁垒”、清洗、接管、强制改革，或把过渡的成本交给弱势位置。」。〔原文 §8.3.4〕',
    'S4': '- 核查原文判据「“过渡谷地”最多是一个有待检验的描述，不能为无限的代价、不可逆的伤害、取消申诉或牺牲低权力位置提供正当性。这个原型不产生拆除、清洗或强制迁移的行动授权。」。〔原文 §8.3.5〕',
    'S5': '\n'.join([
        '- 核查原文判据「这个原型不是“善”“成熟”或“可以输出模式”的标签。存续、增长和筛选不等于正当，也不能授权扩张、复制、接管，或要求成员增加承担。」。〔原文 §8.3.6〕',
        '- 协同靠封闭反馈或压制异议维持的，不归入这一原型，改查虚稳态等路径；核查原文判据「这不预先认定它的产出是假的」。〔原文 §8.3.6〕',
        '- 产出按它自己的材料核对；效率上的优势是否成立，按把维护、恢复、退出和外部成本纳入之后的材料判断，被压制的异议所对应的代价能够查明的一并计入。〔派生，待确认〕',
    ]),
    'S6': '\n'.join([
        '- 核查原文判据「这个原型不是绝对的终态，不是没有冲突的社会，也不是历史的终点。」。〔原文 §8.3.7〕',
        '- 核查原文判据「它也不能替任何对象取得对他者的决策权。」。〔原文 §8.3.7〕',
        '- 不能把状态编号当作退场资格。〔派生，待确认〕',
    ]),
}


def section(text, title):
    match = re.search(r'^## ' + re.escape(title) + r'\s*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    if match is None:
        raise AssertionError(f'missing section: {title}')
    return match.group(1).strip()


def card_meta(relative):
    text = (ROOT / relative).read_text(encoding='utf-8-sig')
    return json.loads(re.match(r'---\n(\{.*?\})\n---\n', text, re.S).group(1))


class EnglishTitleTests(unittest.TestCase):
    def test_every_card_and_its_index_row_carry_one_english_title(self):
        index = json.loads((ROOT / 'rules/index.json').read_text(encoding='utf-8-sig'))
        self.assertEqual(len(index['rules']), 41)
        seen = set()
        for row in index['rules']:
            with self.subTest(card=row['id']):
                meta = card_meta(row['file'])
                title = meta.get('title_en')
                self.assertIsInstance(title, str)
                self.assertRegex(title, r'^[A-Z][^　-鿿]*[^.\s]$')
                self.assertEqual(row.get('title_en'), title)
                self.assertEqual(row.get('title'), meta.get('title'))
                self.assertNotIn(title.lower(), seen)
                seen.add(title.lower())

    def test_english_guide_tells_how_to_name_a_card(self):
        guide = (ROOT / 'references/english.md').read_text(encoding='utf-8')
        load = card_meta('rules/mechanism/CM-LOAD.md')['title_en']
        self.assertIn(f'CM-LOAD ({load})', guide)

    def check_mutated_package(self, mutate):
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp)
            for relative in ('source', 'modules', 'rules', 'cases', 'references', 'agents'):
                shutil.copytree(ROOT / relative, package / relative)
            mutate(package)
            return lint.check(package)

    def test_lint_rejects_an_index_title_that_differs_from_the_card(self):
        def mutate(package):
            path = package / 'rules/index.json'
            index = json.loads(path.read_text(encoding='utf-8'))
            index['rules'][0]['title_en'] = 'Something else'
            path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        result = self.check_mutated_package(mutate)
        self.assertFalse(result['ok'])
        self.assertIn('rules/index.json: CM-FEEDBACK.title_en differs from card', result['errors'])

    def test_lint_requires_an_english_title_on_every_card(self):
        def mutate(package):
            path = package / 'rules/mechanism/CM-LOAD.md'
            text = path.read_text(encoding='utf-8')
            title = card_meta('rules/mechanism/CM-LOAD.md')['title_en']
            path.write_text(text.replace(f'  "title_en": "{title}",\n', '', 1), encoding='utf-8')
            index_path = package / 'rules/index.json'
            index = json.loads(index_path.read_text(encoding='utf-8'))
            for row in index['rules']:
                if row['id'] == 'CM-LOAD':
                    del row['title_en']
            index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        result = self.check_mutated_package(mutate)
        self.assertFalse(result['ok'])
        self.assertIn('rules/mechanism/CM-LOAD.md: title_en must be a non-empty string', result['errors'])


class StateRuleCardTests(unittest.TestCase):
    def test_state_limits_match_required_source_wording(self):
        for card_id, expected in STATE_LIMITS.items():
            with self.subTest(card=card_id):
                text = (ROOT / f'rules/state/{card_id}.md').read_text(encoding='utf-8-sig')
                self.assertEqual(section(text, '不能推出的结论'), expected)

    def test_state_limit_quotes_match_their_full_source_sections(self):
        source = (ROOT / 'source/Xikari-条件结构与转化论.md').read_text(encoding='utf-8-sig')
        units = lint.source_units(source)
        for card_id in STATE_LIMITS:
            text = (ROOT / f'rules/state/{card_id}.md').read_text(encoding='utf-8-sig')
            anchors = lint.metadata(text)['anchors']
            quotes = re.findall(r'「([^」]+)」。〔原文 §([^〕]+)〕', section(text, '不能推出的结论'))
            with self.subTest(card=card_id):
                self.assertEqual(len(quotes), 2 if card_id in ('S5', 'S6') else 1)
                for quote, anchor in quotes:
                    self.assertIn(anchor, anchors)
                    self.assertIn(quote, units[anchor])

    def test_state_cards_remain_draft(self):
        for card_id in STATE_LIMITS:
            with self.subTest(card=card_id):
                text = (ROOT / f'rules/state/{card_id}.md').read_text(encoding='utf-8-sig')
                self.assertEqual(lint.metadata(text)['status'], 'draft')


class GeneralRuleCardTests(unittest.TestCase):
    def test_maintenance_signal_precedes_domain_examples(self):
        text = (ROOT / 'rules/mechanism/CM-MAINTENANCE.md').read_text(encoding='utf-8-sig')
        generic, separator, example = section(text, '早期信号').partition('例：')
        self.assertTrue(separator, 'specific maintenance signals must be introduced as examples')
        for term in ('同一性或功能判据', '维护窗', '磨损', '补给', '通道', '原对象之外'):
            self.assertIn(term, generic)
        for term in ('备件', '工单', '维修队列', '外包人员'):
            self.assertNotIn(term, generic)
            self.assertIn(term, example)
        self.assertTrue(example.endswith('〔派生，待确认〕'))

    def test_early_signal_precedes_resignation_example(self):
        text = (ROOT / 'rules/signal/SIG-EARLY-REVERSE.md').read_text(encoding='utf-8-sig')
        generic, separator, example = section(text, '早期信号').partition('例：')
        self.assertTrue(separator, 'the resignation scenario must be introduced as an example')
        for term in ('路径机制', '结果前登记', '可观察变化', '时间先后', '目标结果'):
            self.assertIn(term, generic)
        for term in ('离职', '工时', '外部机会', '申诉'):
            self.assertNotIn(term, generic)
            self.assertIn(term, example)
        self.assertTrue(example.endswith('〔派生，待确认〕'))


class FailureCascadeCardTests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / 'rules/cascade/CAS-FAILURE.md'
        self.assertTrue(self.path.is_file(), 'technical failure cascade card is missing')
        self.text = self.path.read_text(encoding='utf-8-sig')
        self.meta = lint.metadata(self.text)

    def test_failure_card_contract_and_source_binding(self):
        manifest = json.loads((ROOT / 'source/source-manifest.json').read_text(encoding='utf-8-sig'))
        source = (ROOT / 'source' / manifest['source_file']).read_bytes()
        self.assertEqual(self.meta['id'], 'CAS-FAILURE')
        self.assertEqual(self.meta['type'], 'cascade')
        self.assertEqual(self.meta['status'], 'draft')
        self.assertEqual(set(self.meta['applies_to']), {'technical_system', 'mixed'})
        self.assertIn('6.13', self.meta['anchors'])
        self.assertEqual(self.meta['theory_sha256'], manifest['sha256'])
        self.assertEqual(self.meta['theory_sha256'], hashlib.sha256(source).hexdigest())
        units = lint.source_units(source.decode('utf-8-sig'))
        for anchor in self.meta['anchors']:
            self.assertIn(anchor, units)

    def test_failure_card_has_eight_derived_sections(self):
        headings = ['适用对象', '触发观察', '生成的路径', '时钟与时延',
                    '早期信号', '反向信号', '竞争解释', '不能推出的结论']
        self.assertEqual(re.findall(r'^## (.+)$', self.text, re.M), headings)
        self.assertNotIn('〔原文', self.text)
        self.assertNotIn('〔作者确认〕', self.text)
        for heading in headings:
            with self.subTest(section=heading):
                statements = [line for line in section(self.text, heading).splitlines() if line.strip()]
                self.assertTrue(statements)
                self.assertTrue(all(line.startswith('- ') and line.endswith('〔派生，待确认〕')
                                    for line in statements))

    def test_failure_card_separates_three_explanations(self):
        paths = section(self.text, '生成的路径').splitlines()
        cases = {line[2:].split('：', 1)[0]: line for line in paths if line.startswith('- ')}
        self.assertEqual(set(cases), {'单点逐跳', '恢复受阻', '共因并发'})
        for term in ('逐跳', '传导通道', '时间顺序'):
            self.assertIn(term, cases['单点逐跳'])
        for term in ('多个故障共同阻碍恢复', '恢复依赖', '不把'):
            self.assertIn(term, cases['恢复受阻'])
        for term in ('共同外因同时损坏多处', '暴露', '不因同步'):
            self.assertIn(term, cases['共因并发'])
        limits = section(self.text, '不能推出的结论')
        for term in ('不能把同时失效视为逐跳传导', '不能互换', '状态变量或阈值'):
            self.assertIn(term, limits)

    def test_failure_card_index_matches_header_and_competitors_exist(self):
        index = json.loads((ROOT / 'rules/index.json').read_text(encoding='utf-8-sig'))
        matches = [row for row in index['rules'] if row['id'] == 'CAS-FAILURE']
        self.assertEqual(matches, [dict(self.meta, file='rules/cascade/CAS-FAILURE.md')])
        ids = {row['id'] for row in index['rules']}
        self.assertTrue(self.meta['competes_with'])
        self.assertNotIn('CAS-FAILURE', self.meta['competes_with'])
        self.assertTrue(set(self.meta['competes_with']).issubset(ids))


if __name__ == '__main__':
    unittest.main()
