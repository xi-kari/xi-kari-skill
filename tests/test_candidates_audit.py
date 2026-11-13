import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'candidates.py'

spec = importlib.util.spec_from_file_location('candidates_under_audit', SCRIPT)
cand = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cand)

NOVELTY = {'level': 'new_here', 'scope': '领域层未检索'}
# Characters a reader cannot see: zero-width space and joiner, byte-order mark, word joiner,
# no-break space, ideographic space.
INVISIBLE = [chr(code) for code in (0x200B, 0x200D, 0xFEFF, 0x2060, 0x00A0, 0x3000)]
BACKSLASH = chr(0x5C)


def base(identifier='B1'):
    return {'id': identifier, 'statement': f'起点 {identifier}', 'kind': 'observed', 'source': '教学占位：记录'}


def question(identifier, parents=('B1',), **extra):
    item = {'id': identifier, 'statement': f'问题 {identifier}', 'identity': 'question', 'move': 'task',
            'parents': list(parents), 'novelty': dict(NOVELTY)}
    item.update(extra)
    return item


def empirical(identifier='E1', parents=('B1',), **extra):
    item = {'id': identifier, 'statement': f'候选 {identifier}', 'identity': 'empirical', 'move': 'invert',
            'parents': list(parents), 'novelty': dict(NOVELTY), 'observables': ['应看到甲'],
            'rivals': [{'statement': '竞争项', 'distinguishing': '看乙'}], 'minimal_test': '比对已有记录',
            'reject_conditions': ['出现丙'], 'changes': ['改变方案'], 'strength': 'exploration'}
    item.update(extra)
    return item


class Workspace(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.ledger = self.root / '候选.json'
        self.counter = 0

    def write(self, value, raw=None):
        self.counter += 1
        path = self.root / f'record-{self.counter}.json'
        if raw is None:
            path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
        else:
            path.write_text(raw, encoding='utf-8')
        return path

    def add(self, bases=(), candidates=()):
        return cand.add_records(self.ledger, self.write({'base': list(bases), 'candidates': list(candidates)}))

    def stored(self):
        return json.loads(self.ledger.read_text(encoding='utf-8'))

    def rewrite(self, change):
        ledger = self.stored()
        change(ledger)
        self.ledger.write_text(json.dumps(ledger, ensure_ascii=False), encoding='utf-8')

    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), '--ledger', str(self.ledger), *args],
                              capture_output=True, text=True, encoding='utf-8')


class HandWrittenLedgerTests(Workspace):
    def test_a_ledger_without_a_question_is_usable(self):
        self.ledger.write_text(json.dumps({'schema_version': 1, 'format': cand.FORMAT, 'base': [], 'candidates': []}),
                               encoding='utf-8')
        self.assertEqual(self.run_tool('list').returncode, 0)
        result = cand.add_records(self.ledger, self.write({'question': '还能推出什么', 'base': [base()]}))
        self.assertEqual(result['added_base'], ['B1'])
        self.assertEqual(self.stored()['question'], '还能推出什么')
        self.assertEqual(self.run_tool('render', '--output', str(self.root / 'out.md')).returncode, 0)


class TamperTests(Workspace):
    def setUp(self):
        super().setUp()
        self.add([base()], [empirical('E1'), question('Q1')])
        self.evidence = self.write([{'ref': '教学占位：比对表', 'direction': 'supports'}])

    def refused(self, fragment='直接改写'):
        with self.assertRaises(ValueError) as caught:
            cand.load_ledger(self.ledger)
        self.assertIn(fragment, str(caught.exception))
        for command in (('check',), ('list',), ('render', '--output', str(self.root / 'o.md'))):
            result = self.run_tool(*command)
            self.assertEqual(result.returncode, 2, command)
            self.assertNotIn('Traceback', result.stderr)

    def test_a_second_support_without_evidence_is_not_hidden_by_an_earlier_one(self):
        cand.advance(self.ledger, 'E1', 'testing')
        cand.advance(self.ledger, 'E1', 'supported', evidence_path=self.evidence)
        cand.advance(self.ledger, 'E1', 'testing', note='出现反例')

        def forge(ledger):
            item = ledger['candidates'][0]
            item['history'].append({'from': 'testing', 'to': 'supported', 'at': 'x'})
            item['status'] = 'supported'
        self.rewrite(forge)
        self.refused('没有支持性证据')

    def test_a_question_cannot_be_edited_into_a_supported_state(self):
        def forge(ledger):
            item = ledger['candidates'][1]
            item['history'] = [{'from': 'proposed', 'to': 'testing', 'at': 'x'},
                               {'from': 'testing', 'to': 'supported', 'at': 'x',
                                'evidence': [{'ref': 'r', 'direction': 'supports'}]}]
            item['status'] = 'supported'
        self.rewrite(forge)
        self.refused()

    def test_steps_missing_their_time_are_refused_not_crashed_on(self):
        cand.advance(self.ledger, 'E1', 'testing')
        self.rewrite(lambda ledger: ledger['candidates'][0]['history'][0].pop('at'))
        self.refused()

    def test_a_rejection_whose_reason_was_removed_is_refused(self):
        cand.advance(self.ledger, 'E1', 'rejected', note='出现丙')
        self.rewrite(lambda ledger: ledger['candidates'][0]['history'][0].pop('note'))
        self.refused()

    def test_unknown_step_fields_and_stray_diagnostic_strength_are_refused(self):
        cand.advance(self.ledger, 'E1', 'testing')
        self.rewrite(lambda ledger: ledger['candidates'][0]['history'][0].update(score=3))
        self.refused()

        def stray(ledger):
            ledger['candidates'][0]['history'][0].pop('score')
            ledger['candidates'][0]['strength'] = 'diagnostic'
        self.rewrite(stray)
        self.refused('诊断级')


class LineageShapeTests(Workspace):
    def test_a_long_chain_is_added_and_read_back_whichever_order_it_arrives_in(self):
        length = 600
        chain = [question(f'N{index}', parents=[f'N{index - 1}'] if index else ['B1']) for index in range(length)]
        self.add([base()], list(reversed(chain)))
        ledger = cand.load_ledger(self.ledger)
        self.assertEqual(cand.generations(ledger)[f'N{length - 1}'], length)
        self.assertEqual(cand.lineage(ledger, f'N{length - 1}')['generation'], length)
        self.assertTrue(cand.check_ledger(ledger, {'3.3'})['ok'])
        text = cand.render_markdown(ledger)
        self.assertIn(f'- N{length - 1} ← N{length - 2}；最终起点：B1', text)
        self.assertEqual(self.run_tool('list').returncode, 0)

    def test_a_diamond_lineage_renders_in_proportion_to_its_size(self):
        levels = 22
        items = []
        for level in range(levels):
            parents = ['B1'] if level == 0 else [f'L{level - 1}a', f'L{level - 1}b']
            items += [question(f'L{level}a', parents=parents), question(f'L{level}b', parents=parents)]
        self.add([base()], items)
        started = time.perf_counter()
        text = cand.render_markdown(cand.load_ledger(self.ledger))
        self.assertLess(time.perf_counter() - started, 10)
        self.assertLess(len(text), 200_000)
        self.assertIn(f'- L{levels - 1}a ← L{levels - 2}a ＋ L{levels - 2}b；最终起点：B1', text)

    def test_a_cycle_is_named_without_recursion(self):
        ring = [question(f'R{index}', parents=[f'R{(index + 1) % 500}']) for index in range(500)]
        with self.assertRaises(ValueError) as caught:
            self.add([base()], ring)
        self.assertIn('成环', str(caught.exception))
        self.assertFalse(self.ledger.exists())

    def test_one_ledger_holds_a_bounded_number_of_items(self):
        many = [question(f'Q{index}') for index in range(cand.MAX_ITEMS)]
        with self.assertRaises(ValueError) as caught:
            self.add([base()], many)
        self.assertIn('拆分账本', str(caught.exception))
        self.assertFalse(self.ledger.exists())


class SizeAndTextTests(Workspace):
    def test_a_ledger_that_could_not_be_read_back_is_never_written(self):
        self.add([base()], [])
        untouched = self.ledger.read_bytes()
        heavy = [question(f'Q{index}', changes=['长' * cand.MAX_TEXT] * 100) for index in range(8)]
        with self.assertRaises(ValueError) as caught:
            self.add([], heavy)
        self.assertIn('4MiB', str(caught.exception))
        self.assertEqual(self.ledger.read_bytes(), untouched)
        self.assertEqual(self.run_tool('list').returncode, 0)
        self.assertEqual([path.name for path in self.root.glob('.candidates-*')], [])

    def test_list_entries_obey_the_same_limits_as_single_fields(self):
        for record in (question('Q1', changes=['长' * (cand.MAX_TEXT + 1)]),
                       question('Q1', changes=['项'] * (cand.MAX_LIST + 1)),
                       question('Q1', theory=[{'section': '9' * 33}])):
            with self.subTest(record=str(record)[:60]), self.assertRaises(ValueError):
                self.add([base()], [record])
        self.assertFalse(self.ledger.exists())

    def test_text_made_only_of_invisible_characters_counts_as_empty(self):
        for blank in INVISIBLE + [' ' + chr(9) + chr(10)]:
            with self.subTest(blank=ascii(blank)), self.assertRaises(ValueError):
                self.add([base()], [question('Q1', statement=blank)])
            with self.subTest(blank=ascii(blank), field='list'), self.assertRaises(ValueError):
                self.add([base()], [question('Q1', changes=[blank])])
        self.assertTrue(cand.is_blank(''))
        self.assertFalse(cand.is_blank(INVISIBLE[0] + '字'))
        self.assertFalse(self.ledger.exists())

    def test_unreadable_input_is_reported_as_a_tool_error(self):
        deep = '[' * 100000 + ']' * 100000
        surrogate = ('{"base": [{"id": "B1", "statement": "' + BACKSLASH + 'ud800", "kind": "assumption"}]}')
        huge = '{"base": [{"id": "B1", "statement": "x", "kind": "assumption", "conditions": [' + '9' * 5000 + ']}]}'
        for raw, fragment in ((deep, '嵌套过深'), (surrogate, 'UTF-8'), (huge, '数值')):
            with self.subTest(fragment=fragment):
                path = self.write(None, raw=raw)
                with self.assertRaises(ValueError) as caught:
                    cand.add_records(self.ledger, path)
                self.assertIn(fragment, str(caught.exception))
                result = self.run_tool('add', '--record', str(path))
                self.assertEqual(result.returncode, 2)
                self.assertNotIn('Traceback', result.stderr)
        self.assertFalse(self.ledger.exists())


class ReplacementTests(Workspace):
    def test_replacement_cannot_loop_or_point_at_an_ancestor(self):
        with self.assertRaises(ValueError) as caught:
            self.add([base()], [question('Q1', supersedes='Q2'), question('Q2', supersedes='Q1')])
        self.assertIn('取代关系成环', str(caught.exception))
        with self.assertRaises(ValueError) as caught:
            self.add([base()], [question('Q1'), question('Q3', parents=['Q1'], supersedes='Q1')])
        self.assertIn('不能取代自己的父项或祖先', str(caught.exception))
        self.assertFalse(self.ledger.exists())

    def test_every_candidate_replacing_the_same_one_is_reported(self):
        self.add([base()], [question('Q3'), question('Q4', supersedes='Q3'), question('Q5', supersedes='Q3')])
        warnings = cand.check_ledger(cand.load_ledger(self.ledger), {'3.3'})['warnings']
        self.assertTrue(any(line.startswith('Q3: 已被 Q4、Q5 取代') for line in warnings))


if __name__ == '__main__':
    unittest.main()
