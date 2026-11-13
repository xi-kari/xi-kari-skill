import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cand = load('candidates')
lint = load('lint_derived')
metrics = load('answer_metrics')

INSTRUCTIONS = (['SKILL.md', 'AGENTS.md', 'CONTRIBUTING.md', 'agents/reviewer.md', 'agents/openai.yaml']
                + sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / 'references').glob('*.md'))
                + sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / 'modules').glob('*/MODULE.md')))
MOVE_LABELS = [label for key, label in cand.MOVES.items() if key != 'association']


def read(path):
    return (ROOT / path).read_text(encoding='utf-8-sig')


def table_rows(text, heading):
    block = text.split(heading + '\n', 1)[1].split('\n## ', 1)[0]
    return [line for line in block.splitlines() if line.startswith('| ')][2:]


def section(text, heading):
    match = re.search(r'^#+ ' + re.escape(heading) + r'\s*\n(.*?)(?=^#{1,3} |\Z)', text, re.M | re.S)
    if match is None:
        raise AssertionError(f'missing section: {heading}')
    return match.group(1)


class RouteAndModuleTests(unittest.TestCase):
    def test_entry_lists_eight_routes_and_eleven_modules(self):
        skill = read('SKILL.md')
        routes = table_rows(skill, '## 八条问题路由')
        self.assertEqual([row.split('|')[1].split()[0] for row in routes], [f'R{n}' for n in range(1, 9)])
        modules = table_rows(skill, '## 十一个方法模块')
        self.assertEqual(len(modules), 11)
        for number, row in enumerate(modules):
            link = re.search(r'\[M(\d+) ([^\]]+)\]\(([^)]+)\)', row)
            self.assertEqual(int(link.group(1)), number)
            meta = lint.metadata(read(link.group(3)))
            self.assertEqual((meta['id'], meta['title']), (f'M{number}', link.group(2)))

    def test_routing_guide_agrees_with_the_entry(self):
        routing = table_rows(read('references/routing.md'), '## 八条路线')
        skill = table_rows(read('SKILL.md'), '## 八条问题路由')
        self.assertEqual(len(routing), 8)
        for guide_row, entry_row in zip(routing, skill):
            self.assertEqual(guide_row.split('|')[1].strip(), entry_row.split('|')[1].strip())
        for row in (routing[7], skill[7]):
            self.assertIn('R8 生成', row)
            self.assertRegex(row, r'M10 → M8 → M9')
            self.assertIn('候选', row.split('|')[4])

    def test_no_instruction_still_counts_seven_routes_or_ten_modules(self):
        for path in INSTRUCTIONS:
            with self.subTest(path=path):
                text = read(path)
                self.assertNotRegex(text, r'(?<!十)七条(?:问题)?路[由线]|十个(?:方法)?模块|十个 `modules|R1—R7|M0—M9(?!、)')

    def test_generation_keeps_its_output_apart_from_neighbouring_routes(self):
        skill, routing = read('SKILL.md'), read('references/routing.md')
        for text in (skill, routing):
            for term in ('仍走 R3', 'R5', 'R6') if text is skill else ('仍是 R3', 'R5、R6', '先 R2 后 R8', 'R7'):
                self.assertIn(term, text)
        self.assertIn('不从空白联想', routing)
        self.assertIn('重述不算新', skill)
        self.assertIn('只相对写明的检索范围', skill)

    def test_neighbouring_modules_know_about_generation(self):
        self.assertIn('R2—R6 与 R8', read('modules/contract/MODULE.md'))
        self.assertIn('写明检索范围', read('modules/evidence/MODULE.md'))
        self.assertIn('子项是否带着父项的条件', read('modules/critique/MODULE.md'))
        self.assertIn('联想单列', read('modules/compose/MODULE.md'))
        self.assertIn('R1—R8', read('agents/reviewer.md'))
        self.assertIn('M10', read('references/forward-workflow.md'))
        self.assertIn('candidates.json', read('references/task-routes.md'))
        self.assertIn('八条路由与十一个模块', read('AGENTS.md'))


class ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read('modules/generate/MODULE.md')
        cls.meta = lint.metadata(cls.text)

    def test_module_has_the_shared_sections(self):
        self.assertEqual(re.findall(r'^## (.+)$', self.text, re.M),
                         ['用途与输入', '步骤与判断', '交接物与模板', '停止与降级',
                          '教学例，不作经验证据', '常见误用', '工具与相关指南'])
        self.assertLessEqual(len(self.text.splitlines()), 300)

    def test_every_move_names_its_source_contract(self):
        rows = [line for line in section(self.text, '步骤与判断').splitlines() if line.strip().startswith('| ')][2:]
        self.assertEqual([row.split('|')[2].strip() for row in rows], MOVE_LABELS)
        families = [row.split('|')[1].strip() for row in rows]
        self.assertEqual(families, ['推必然'] * 3 + ['挪位置'] * 6 + ['接外部'] * 2)
        for row in rows:
            with self.subTest(move=row.split('|')[2].strip()):
                anchors = lint.references(row.split('|')[4])
                self.assertTrue(anchors)
                for anchor in anchors:
                    self.assertTrue(any(anchor == declared or anchor.startswith(declared + '.')
                                        for declared in self.meta['reading']),
                                    f'§{anchor} is cited by a move but not in the module reading')

    def test_identities_screens_and_stops_are_all_stated(self):
        steps = section(self.text, '步骤与判断')
        for label in cand.IDENTITIES.values():
            self.assertIn(label, steps)
        for term in ('从哪里来', '新在哪里', '怎样会错', '成立了改变什么', '重述不算新候选',
                     '至少并列一个竞争项', '保留未知', '若父项成立', '代次不增加支持', '第三代',
                     '不逐项走完', '产出少就如实说少'):
            self.assertIn(term, steps)
        for label in cand.STATUSES.values():
            self.assertIn(label, self.text)
        limits = section(self.text, '停止与降级')
        for term in ('一并复核', '不能回头支撑原判断', '不能直接写成人格结论、有效圈层或因果机制',
                     '都不提高判断强度'):
            self.assertIn(term, limits)

    def test_teaching_example_is_marked_and_does_not_assert_an_outcome(self):
        example = section(self.text, '教学例，不作经验证据')
        for term in ('模型内推论', '经验候选', '竞争项', '区分观察', '构想', '哪一项都不能写成'):
            self.assertIn(term, example)
        self.assertIn('6 人', example)
        self.assertIn('缺 2 人', example)


class GuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read('references/generation.md')
        cls.meta = lint.metadata(cls.text)
        manifest = json.loads(read('source/source-manifest.json'))
        cls.units = lint.source_units(read('source/' + manifest['source_file']))

    def test_every_move_has_method_identity_and_idle_form(self):
        for label in MOVE_LABELS:
            with self.subTest(move=label):
                body = section(self.text, label)
                for term in ('做法', '结果身份', '空转'):
                    self.assertIn(term, body)

    def test_guide_cites_what_the_module_cites(self):
        module = read('modules/generate/MODULE.md')
        rows = [line for line in section(module, '步骤与判断').splitlines() if line.strip().startswith('| ')][2:]
        for row in rows:
            label = row.split('|')[2].strip()
            for anchor in lint.references(row.split('|')[4]):
                with self.subTest(move=label, anchor=anchor):
                    self.assertTrue(any(declared == anchor or declared.startswith(anchor + '.')
                                        or anchor.startswith(declared + '.')
                                        for declared in self.meta['anchors']))

    def test_identity_and_novelty_tables_use_the_ledger_vocabulary(self):
        identities = [row.split('|')[1].strip() for row in table_rows(self.text, '## 七种身份')]
        self.assertEqual(identities, list(cand.IDENTITIES.values()))
        screen = self.text.split('## 四问筛选\n', 1)[1].split('\n## ', 1)[0]
        levels = [line.split('|')[1].strip() for line in screen.splitlines() if line.startswith('| ')][2:]
        self.assertEqual(levels, list(cand.NOVELTY.values()))
        kinds = [row.split('|')[1].strip() for row in table_rows(self.text, '## 起点')]
        self.assertEqual(kinds, list(cand.BASE_KINDS.values()))

    def test_literal_quotations_carry_the_generation_discipline(self):
        quotes = lint.original_quotes(self.text)
        cited = {anchor for quote in quotes for anchor in quote['anchors']}
        self.assertLessEqual({'11.9.1', '2.6', '2.13', '4.19', '5.5.9', '5.10.2', '11.8', '16.5', '4.17.2'}, cited)
        for quote in quotes:
            with self.subTest(quote=quote['text']):
                compact = lint.compact_whitespace(quote['text'])
                self.assertTrue(any(compact in lint.compact_whitespace(self.units[anchor])
                                    for anchor in quote['anchors']))

    def test_guide_refuses_unscoped_novelty_and_upgrading_by_depth(self):
        for term in ('不使用“首次”“全新”这类不带范围的说法', '数量不是质量', '走得更远不使任何一项更可信',
                     '不用“发现了”称呼未经检验的东西', '不能写成“培训无效”', '只组织用法'):
            self.assertIn(term, self.text)

    def test_guide_closes_the_gaps_found_in_use(self):
        for term in ('不因为没有检索就算作新的', '读到什么深度', '照样进入主要部分，只是不称新',
                     '不替它换一个词再要求它满足合同', '以决定这条陈述的那一步为准',
                     '不逐项交代没有采用的走法', '账本的条数和字段不进正文',
                     '写成经验候选就要满足经验候选的全部要求'):
            self.assertIn(term, self.text)
        module = read('modules/generate/MODULE.md')
        for term in ('到能逐项写出起点的身份与出处为止', '称可能已有', '按 M8 实际攻击一次'):
            self.assertIn(term, module)
        self.assertNotIn('走法、身份、竞争项和检验办法', read('SKILL.md'))
        self.assertIn('怎样得到', read('SKILL.md'))


class LedgerGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read('references/candidate-ledger.md')

    def test_every_field_and_value_the_tool_accepts_is_documented(self):
        for key in sorted(cand.BASE_KEYS | cand.CANDIDATE_KEYS):
            with self.subTest(field=key):
                self.assertIn(f'`{key}`', self.text)
        for group in (cand.BASE_KINDS, cand.IDENTITIES, cand.MOVES, cand.NOVELTY):
            for key, label in group.items():
                with self.subTest(value=key):
                    self.assertIn(f'`{key}` {label}', self.text)
        for key, label in cand.STRENGTHS.items():
            if key != 'diagnostic':
                self.assertIn(f'`{key}` {label}', self.text)
        for label in cand.STATUSES.values():
            self.assertIn(label, self.text)

    def test_every_command_is_shown(self):
        for command in ('add', 'revise', 'advance', 'list', 'show', 'lineage', 'check', 'render'):
            with self.subTest(command=command):
                self.assertRegex(self.text, r'candidates\.py" --ledger "[^"]+" ' + command + r'\b')

    def test_guide_states_what_the_tool_does_not_judge(self):
        for term in ('不生成置信度、新颖性分数', '续推、复述和模型之间的一致都不是证据', '不判断它是否充分',
                     '不判断候选是否为真', '教学占位'):
            self.assertIn(term, self.text)


class PackagingTests(unittest.TestCase):
    def test_new_resources_ship_and_every_listed_file_exists(self):
        files = json.loads(read('skill-package.json'))['files']
        for name in ('modules/generate/MODULE.md', 'references/generation.md', 'references/candidate-ledger.md',
                     'scripts/candidates.py', 'assets/examples/candidates-example.json'):
            self.assertIn(name, files)
        self.assertEqual(len(files), len(set(files)))
        for name in files:
            with self.subTest(file=name):
                self.assertTrue((ROOT / name).is_file())

    def test_english_working_notes_name_the_new_route_and_module(self):
        text = read('references/english.md')
        for term in ('| R8 生成 | R8 Generation |', '| M10 生成 | M10 Generation |', 'candidate ledger',
                     'heuristic analogy', '`candidates.py`', '`candidates.json`'):
            self.assertIn(term, text)

    def test_route_and_module_codes_count_as_internal_codes(self):
        found = metrics.measure('R8、M10、R1、M9。M01、R9、M11。')['internal_codes']
        self.assertEqual(found, ['R8', 'M10', 'R1', 'M9'])


if __name__ == '__main__':
    unittest.main()
