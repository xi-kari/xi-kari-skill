import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'read_source.py'


def module():
    spec = importlib.util.spec_from_file_location('read_source_search', SCRIPT)
    target = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(target)
    return target


class SourceSearchTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True, encoding='utf-8')

    def test_section_at_returns_the_most_specific_containing_section(self):
        reader = module()
        lines = ['# 书', '## 1.1 父节', '正文', '### 1.1.1 子节', '深层正文', '## 1.2 后节', '其他']
        sections, _ = reader.build_index(lines)
        order = sorted(sections.items(), key=lambda item: item[1]['start'])
        self.assertEqual(reader.section_at(order, 1)[0], '1.1')
        self.assertEqual(reader.section_at(order, 4)[0], '1.1.1')
        self.assertEqual(reader.section_at(order, 6)[0], '1.2')
        self.assertIsNone(reader.section_at(order, 0)[0])

    def test_search_attributes_hits_to_real_sections(self):
        result = self.run_cli('--search', '条件结构')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('命中', result.stdout)
        self.assertIn('§', result.stdout)
        self.assertRegex(result.stdout, r'行\d+:')

    def test_search_is_literal_and_a_missing_term_is_not_a_failure(self):
        result = self.run_cli('--search', 'ZzzNotInTheoryZzz')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('未找到', result.stdout)

    def test_search_rejects_empty_terms_and_invalid_options(self):
        self.assertEqual(self.run_cli('--search', '   ').returncode, 2)
        self.assertEqual(self.run_cli('--search', '条件', '--limit', '0').returncode, 2)
        self.assertEqual(self.run_cli('--search', '条件', '--context', '-1').returncode, 2)

    def test_limit_bounds_the_number_of_shown_hits(self):
        result = self.run_cli('--search', '条件', '--limit', '3')
        self.assertEqual(result.returncode, 0, result.stderr)
        shown = [line for line in result.stdout.splitlines() if line.startswith('> ')]
        self.assertEqual(len(shown), 3)

    def test_context_reports_neighbouring_lines(self):
        without = self.run_cli('--search', '条件', '--limit', '1')
        widened = self.run_cli('--search', '条件', '--limit', '1', '--context', '2')
        self.assertEqual(widened.returncode, 0, widened.stderr)
        self.assertGreater(len(widened.stdout.splitlines()), len(without.stdout.splitlines()))


if __name__ == '__main__':
    unittest.main()
