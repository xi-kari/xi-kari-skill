import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'read_source.py'


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reader = load('read_source')
lint = load('lint_derived')


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, encoding='utf-8')


class FrontMatterTests(unittest.TestCase):
    def test_front_is_everything_before_the_first_part_and_nothing_after(self):
        lines = reader.SOURCE.read_text(encoding='utf-8-sig').splitlines()
        _, parts = reader.build_index(lines)
        first = min(row['start'] for row in parts.values())
        result = run('--front')
        self.assertEqual(result.returncode, 0, result.stderr)
        header, _, body = result.stdout.lstrip('\n').partition('\n\n')
        self.assertEqual(header, f'[{reader.SOURCE.name} · lines 1-{first}]')
        self.assertEqual(body.rstrip('\n'), '\n'.join(lines[:first]).rstrip('\n'))
        self.assertNotIn('<a id="part_1"></a>', body)
        self.assertIn(lint.source_units('\n'.join(lines))['front'], body)

    def test_front_matches_the_identifier_used_by_the_reading_core(self):
        core = json.loads((ROOT / 'references/reading-core.json').read_text(encoding='utf-8'))['reading']
        self.assertIn('front', core)
        guide = (ROOT / 'references/full-source-study.md').read_text(encoding='utf-8')
        self.assertIn('read_source.py" --front', guide)
        self.assertIn('`layered` 用 `--front` 取得完整书前', guide)

    def test_front_reads_the_english_edition_and_both_in_parallel(self):
        english = run('--front', '--lang', 'en')
        self.assertEqual(english.returncode, 0, english.stderr)
        self.assertIn('Xikari-On-Conditions-Structure-and-Transformation.md · lines 1-', english.stdout)
        both = run('--front', '--parallel')
        self.assertEqual(both.returncode, 0, both.stderr)
        self.assertEqual(both.stdout.count(' · lines 1-'), 2)
        self.assertLess(both.stdout.index(reader.SOURCE.name), both.stdout.index('Xikari-On-Conditions'))

    def test_front_combines_with_sections_without_duplicating_lines(self):
        result = run('--front', '--section', '1.1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count('[Xikari-条件结构与转化论.md · lines '), 2)

    def test_an_edition_without_front_matter_is_refused(self):
        with self.assertRaises(ValueError):
            reader.selected_ranges({}, {1: {'start': 0, 'end': 5}}, [], [], front=True)
        self.assertEqual(reader.selected_ranges({}, {1: {'start': 3, 'end': 9}}, [], [], front=True), [(0, 3)])

    def test_parallel_still_needs_a_range(self):
        result = run('--parallel')
        self.assertEqual(result.returncode, 2)
        self.assertIn('--front', result.stderr)


if __name__ == '__main__':
    unittest.main()
