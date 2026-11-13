import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'candidates.py'

spec = importlib.util.spec_from_file_location('candidates_for_revision', SCRIPT)
cand = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cand)

NOVELTY = {'level': 'new_here', 'scope': '领域层未检索'}


def base(identifier='B1'):
    return {'id': identifier, 'statement': f'起点 {identifier}', 'kind': 'observed', 'source': '教学占位：记录'}


def empirical(identifier='C1', parents=('B1',), **extra):
    item = {'id': identifier, 'statement': f'候选 {identifier}', 'identity': 'empirical', 'move': 'invert',
            'parents': list(parents), 'novelty': dict(NOVELTY), 'observables': ['应看到甲'],
            'rivals': [{'statement': '竞争项', 'distinguishing': '看乙'}], 'minimal_test': '比对已有记录',
            'reject_conditions': ['出现丙'], 'changes': ['改变方案'], 'strength': 'exploration'}
    item.update(extra)
    return item


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.ledger = self.root / '候选.json'
        self.counter = 0
        self.clock = 0
        original = cand._now
        self.addCleanup(setattr, cand, '_now', original)
        cand._now = self.tick
        self.add([base()], [empirical('C1'), empirical('C2', parents=['C1'])])

    def tick(self):
        self.clock += 1
        return f'2026-01-01T00:00:{self.clock:02d}+00:00'

    def write(self, value):
        self.counter += 1
        path = self.root / f'record-{self.counter}.json'
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
        return path

    def add(self, bases=(), candidates=()):
        return cand.add_records(self.ledger, self.write({'base': list(bases), 'candidates': list(candidates)}))

    def candidate(self, identifier):
        return next(item for item in json.loads(self.ledger.read_text(encoding='utf-8'))['candidates']
                    if item['id'] == identifier)

    def revised(self, **extra):
        record = empirical('C1', rivals=[{'statement': '竞争项', 'distinguishing': '看乙'},
                                           {'statement': '更省的解释', 'distinguishing': '看丁'}])
        record.update(extra)
        return record

    def test_a_proposed_candidate_is_revised_in_place_and_the_old_wording_is_kept(self):
        before = self.candidate('C1')
        result = cand.revise(self.ledger, self.write(self.revised(statement='修订后的候选')), '自我攻击后补上更省的竞争项')
        self.assertEqual(result['id'], 'C1')
        after = self.candidate('C1')
        self.assertEqual(after['statement'], '修订后的候选')
        self.assertEqual(len(after['rivals']), 2)
        self.assertEqual((after['status'], after['history'], after['added_at']), ('proposed', [], before['added_at']))
        self.assertEqual(len(after['revisions']), 1)
        revision = after['revisions'][0]
        self.assertEqual(revision['note'], '自我攻击后补上更省的竞争项')
        self.assertEqual(revision['before']['statement'], '候选 C1')
        self.assertEqual(len(revision['before']['rivals']), 1)
        self.assertNotIn('status', revision['before'])
        cand.revise(self.ledger, self.write(self.revised(statement='再次修订')), '收窄表述')
        self.assertEqual([entry['before']['statement'] for entry in self.candidate('C1')['revisions']],
                         ['候选 C1', '修订后的候选'])

    def test_a_revision_states_why(self):
        untouched = self.ledger.read_bytes()
        for note in ('', '   '):
            with self.subTest(note=note), self.assertRaises(ValueError) as caught:
                cand.revise(self.ledger, self.write(self.revised()), note)
            self.assertIn('理由', str(caught.exception))
        self.assertEqual(self.ledger.read_bytes(), untouched)

    def test_once_testing_has_begun_changes_take_a_new_identifier(self):
        cand.advance(self.ledger, 'C1', 'testing')
        untouched = self.ledger.read_bytes()
        with self.assertRaises(ValueError) as caught:
            cand.revise(self.ledger, self.write(self.revised()), '想改措辞')
        self.assertIn('supersedes', str(caught.exception))
        self.assertEqual(self.ledger.read_bytes(), untouched)

    def test_a_revision_names_an_existing_candidate_and_obeys_the_same_rules_as_a_new_record(self):
        untouched = self.ledger.read_bytes()
        broken = self.revised()
        del broken['rivals']
        for record, fragment in ((empirical('C9'), '未找到候选'),
                                 (base('B1'), '未找到候选'),
                                 (broken, '竞争项'),
                                 (self.revised(status='supported'), '由工具写入'),
                                 (self.revised(revisions=[]), '由工具写入'),
                                 (self.revised(parents=['B9']), '父项 B9 不存在'),
                                 (self.revised(parents=['C2']), '成环'),
                                 ([self.revised()], '候选须为JSON对象')):
            with self.subTest(fragment=fragment), self.assertRaises(ValueError) as caught:
                cand.revise(self.ledger, self.write(record), '理由')
            self.assertIn(fragment, str(caught.exception))
        self.assertEqual(self.ledger.read_bytes(), untouched)

    def test_children_registered_before_a_revision_are_flagged_for_review(self):
        sections = {'3.3'}
        self.assertFalse(any('修订' in line for line in cand.check_ledger(cand.load_ledger(self.ledger), sections)['warnings']))
        cand.revise(self.ledger, self.write(self.revised(statement='修订后的候选')), '收窄表述')
        self.add([], [empirical('C3', parents=['C1'])])
        warnings = cand.check_ledger(cand.load_ledger(self.ledger), sections)['warnings']
        self.assertTrue(any(line.startswith('C2: 父项 C1 在它登记之后修订过') for line in warnings))
        self.assertFalse(any(line.startswith('C3: 父项 C1 在它登记之后修订过') for line in warnings))

    def test_the_rendered_ledger_shows_that_and_why_a_candidate_was_revised(self):
        cand.revise(self.ledger, self.write(self.revised(statement='修订后的候选')), '自我攻击后补上更省的竞争项')
        text = cand.render_markdown(cand.load_ledger(self.ledger))
        self.assertIn('修订后的候选', text)
        self.assertIn('- **修订：**', text)
        self.assertIn('自我攻击后补上更省的竞争项', text)
        self.assertIn('修订前的内容保留在账本文件里', text)

    def test_a_hand_edited_revision_trail_is_refused_on_load(self):
        cand.revise(self.ledger, self.write(self.revised()), '理由')
        ledger = json.loads(self.ledger.read_text(encoding='utf-8'))
        ledger['candidates'][0]['revisions'] = [{'note': '没有时间和原文'}]
        self.ledger.write_text(json.dumps(ledger, ensure_ascii=False), encoding='utf-8')
        with self.assertRaises(ValueError):
            cand.load_ledger(self.ledger)

    def test_command_line_revises_and_reports_failures(self):
        def run(*args):
            return subprocess.run([sys.executable, str(SCRIPT), '--ledger', str(self.ledger), *args],
                                  capture_output=True, text=True, encoding='utf-8')
        record = self.write(self.revised(statement='命令行修订'))
        self.assertEqual(run('revise', '--record', str(record)).returncode, 2)
        result = run('revise', '--record', str(record), '--note', '补竞争项')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['revisions'], 1)
        self.assertEqual(self.candidate('C1')['statement'], '命令行修订')
        self.assertEqual(run('check').returncode, 0)


if __name__ == '__main__':
    unittest.main()
