"""Check the read-only domain card tool on bundled samples and hand-made libraries."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/domain_cards.py'
spec = importlib.util.spec_from_file_location('domain_cards_under_test', SCRIPT)
cards = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cards)
CURRENT = cards.theory()['sha256']
BODY = ('# 热线工单\n\n## 来源与已核范围\n\n办理规程第九条，用户提供。\n\n## 词义与关系\n\n'
        '按规则成立的状态与实际效果分开（§2.4.3）；送达与改变了处理分开（§3.3）。\n\n'
        '## 修订记录\n\n- 2026-11-18：建立。\n')


def card(body=BODY, **changes):
    header = {'id': 'hotline', 'title': '热线工单办理', 'scope': '某市热线；规程 2026 年版；第一季度材料',
              'updated': '2026-11-18', 'theory_sha256': CURRENT, 'anchors': ['2.4.3', '3.3']}
    for key, value in changes.items():
        if value is None:
            header.pop(key, None)
        else:
            header[key] = value
    return '---\n' + json.dumps(header, ensure_ascii=False) + '\n---\n\n' + body


class DomainCardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.library = Path(self.temp.name) / '领域 卡'
        self.library.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, text, encoding='utf-8'):
        path = self.library / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding=encoding, newline='\n')
        return path

    def one(self, text, **kwargs):
        path = self.write('card.md', text, **kwargs)
        return cards.examine(path, self.library)

    def test_bundled_samples_and_example_card_are_clean(self):
        report = cards.check_cards(None)
        self.assertTrue(report['ok'])
        self.assertTrue(report['bundled_samples'])
        self.assertEqual({row['file'] for row in report['cards']},
                         {'education-learning.md', 'organization-work.md', 'technical-maintenance.md'})
        for row in report['cards']:
            self.assertEqual((row['theory'], row['errors'], row['warnings']), ('current', [], []), row['file'])
        example = cards.check_cards(ROOT / 'assets/examples/domain-card-example.md')
        self.assertEqual((example['error_count'], example['warning_count']), (0, 0), example['cards'])

    def test_the_header_example_in_the_guide_is_accepted_as_written(self):
        guide = (ROOT / 'references/domains/README.md').read_text(encoding='utf-8')
        section = guide[guide.index('## 卡片怎样写'):]
        fence = '`' * 3
        start = section.index('\n', section.index(fence)) + 1
        block = section[start:section.index('\n' + fence, start)]
        self.assertIn('hotline-tickets', block)
        text = (block.replace('所据原文的 SHA-256', CURRENT)
                + '\n\n## 来源与已核范围\n\n用户提供的规程。\n\n## 修订记录\n\n- 2026-11-18：建立。\n')
        row = self.one(text)
        self.assertEqual(row['errors'], [])
        self.assertEqual(row['id'], 'hotline-tickets')

    def test_a_complete_user_card_passes_without_warnings(self):
        row = self.one(card())
        self.assertEqual((row['errors'], row['warnings']), ([], []))
        self.assertEqual((row['id'], row['updated'], row['theory']), ('hotline', '2026-11-18', 'current'))

    def test_missing_or_broken_headers_are_named(self):
        self.assertIn('没有卡头', self.one(BODY)['errors'][0])
        self.assertIn('不是合法 JSON', self.one('---\n{"id": \n---\n' + BODY)['errors'][0])
        self.assertIn('JSON 对象', self.one('---\n["hotline"]\n---\n' + BODY)['errors'][0])
        for key in ('id', 'title', 'scope'):
            with self.subTest(key=key):
                self.assertTrue(any(key in error for error in self.one(card(**{key: None}))['errors']))
                self.assertTrue(any(key in error for error in self.one(card(**{key: '  '}))['errors']))
        for value in (None, '2026-13-40', 20261118, '昨天'):
            with self.subTest(updated=value):
                self.assertTrue(any('updated' in error for error in self.one(card(updated=value))['errors']))

    def test_section_references_need_a_binding_and_must_exist(self):
        for value in ('2.4.3', ['§2.4.3'], ['2'], [243]):
            with self.subTest(anchors=value):
                self.assertTrue(any('anchors' in error for error in self.one(card(anchors=value))['errors']))
        self.assertTrue(any('theory_sha256' in error for error in self.one(card(theory_sha256=None))['errors']))
        self.assertTrue(any('theory_sha256' in error for error in self.one(card(theory_sha256='ABC'))['errors']))
        self.assertIn('随包原文中没有 §99.9。', self.one(card(anchors=['2.4.3', '3.3', '99.9']))['errors'])
        self.assertIn('随包原文中没有 §88.1。', self.one(card(body=BODY + '\n另见 §88.1。\n'))['errors'])

    def test_a_card_without_theory_use_needs_no_binding(self):
        body = '# 报修\n\n## 来源\n\n物业规定。\n\n## 修订记录\n\n- 2026-11-18：建立。\n'
        row = self.one(card(body=body, theory_sha256=None, anchors=[]))
        self.assertEqual((row['errors'], row['warnings'], row['theory']), ([], [], 'not_bound'))
        row = self.one(card(body=body, theory_sha256=None, anchors=None))
        self.assertEqual((row['errors'], row['anchors']), ([], []))

    def test_another_theory_version_warns_instead_of_checking_sections(self):
        row = self.one(card(theory_sha256='0' * 64, anchors=['2.4.3', '3.3', '99.9']))
        self.assertEqual(row['errors'], [])
        self.assertEqual(row['theory'], 'other_version')
        self.assertTrue(any('不是当前随包版本' in warning for warning in row['warnings']))

    def test_cited_sections_should_be_listed_and_parents_cover_children(self):
        row = self.one(card(body=BODY + '\n任务终点见 §13.11.2。\n'))
        self.assertEqual(row['errors'], [])
        self.assertTrue(any('§13.11.2' in warning for warning in row['warnings']))
        body = BODY.replace('§2.4.3', '§7.3.5').replace('§3.3', '§7.3.9')
        self.assertEqual(self.one(card(body=body, anchors=['7.3']))['warnings'], [])

    def test_sources_and_revision_record_are_expected_in_either_language(self):
        row = self.one(card(body='# 卡片\n\n正文（§2.4.3、§3.3）。\n'))
        self.assertEqual(row['errors'], [])
        self.assertEqual(len([w for w in row['warnings'] if '一节' in w]), 2)
        english = '# Hotline\n\n## Sources checked\n\nRules (§2.4.3, §3.3).\n\n## Revision record\n\n- 2026-11-18: created.\n'
        self.assertEqual(self.one(card(body=english))['warnings'], [])

    def test_library_listing_skips_readme_and_reports_duplicate_ids(self):
        self.write('a.md', card())
        self.write('sub/b.md', card(id='repair', title='报修'))
        self.write('c.md', card(title='重复的标识'))
        self.write('README.md', '# 说明\n')
        self.write('notes.txt', '不是卡片')
        listing = cards.list_cards(self.library)
        self.assertEqual([row['file'] for row in listing['cards']], ['a.md', 'c.md', 'sub/b.md'])
        self.assertEqual({key for row in listing['cards'] for key in row},
                         {'file', 'id', 'title', 'scope', 'updated', 'theory', 'anchors', 'problems'})
        self.assertFalse(listing['bundled_samples'])
        report = cards.check_cards(self.library)
        by_file = {row['file']: row for row in report['cards']}
        self.assertEqual(by_file['a.md']['errors'], [])
        self.assertTrue(any('重复' in error for error in by_file['c.md']['errors']))
        self.assertFalse(report['ok'])
        single = cards.check_cards(self.library / 'sub' / 'b.md')
        self.assertEqual([row['file'] for row in single['cards']], ['b.md'])
        self.assertTrue(single['ok'])

    def test_encoding_and_size_limits(self):
        self.assertEqual(self.one(card(), encoding='utf-8-sig')['errors'], [])
        path = self.library / 'latin.md'
        path.write_bytes(card().encode('utf-16'))
        self.assertIn('UTF-8', cards.examine(path, self.library)['errors'][0])
        path = self.library / 'big.md'
        path.write_bytes(card().encode('utf-8') + b' ' * cards.MAX_BYTES)
        self.assertIn('1 MiB', cards.examine(path, self.library)['errors'][0])

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], cwd=self.temp.name,
                              capture_output=True, text=True, encoding='utf-8', timeout=30)

    def snapshot(self, folder):
        return {path.relative_to(folder).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in folder.rglob('*') if path.is_file()}

    def test_command_line_exit_codes_and_read_only_behaviour(self):
        self.write('good.md', card())
        before, scripts = self.snapshot(self.library), self.snapshot(ROOT / 'scripts')
        listed = self.run_cli('--library', self.library, 'list')
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual(json.loads(listed.stdout)['cards'][0]['title'], '热线工单办理')
        checked = self.run_cli('--library', self.library, 'check')
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertTrue(json.loads(checked.stdout)['ok'])
        self.write('bad.md', BODY)
        before = self.snapshot(self.library)
        failed = self.run_cli('--library', self.library, 'check')
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(json.loads(failed.stdout)['error_count'], 1)
        self.assertEqual(self.run_cli('--library', self.library, 'list').returncode, 0)
        missing = self.run_cli('--library', self.library / '不存在', 'check')
        self.assertEqual((missing.returncode, missing.stdout), (2, ''))
        self.assertIn('找不到', missing.stderr)
        self.assertNotIn('Traceback', missing.stderr)
        bundled = self.run_cli('check')
        self.assertEqual(bundled.returncode, 0, bundled.stdout)
        usage = self.run_cli('--help')
        self.assertEqual(usage.returncode, 0, usage.stderr)
        self.assertIn('领域库目录或单张卡片', usage.stdout)
        self.assertEqual(before, self.snapshot(self.library))
        self.assertEqual(scripts, self.snapshot(ROOT / 'scripts'))


if __name__ == '__main__':
    unittest.main()
