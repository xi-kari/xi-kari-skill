import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'read_source.py'
HEADER = re.compile(r'^\[(?P<name>[^\]]+?) · lines (?P<first>\d+)-(?P<last>\d+) · page (?P<page>\d+)/(?P<pages>\d+)\]$', re.M)


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reader = load('read_source')


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, encoding='utf-8')


class PagedSelectionTests(unittest.TestCase):
    def read_all_pages(self, *args):
        first = run(*args, '--page', '1')
        self.assertEqual(first.returncode, 0, first.stderr)
        total = int(HEADER.search(first.stdout)['pages'])
        outputs = [first.stdout]
        for number in range(2, total + 1):
            result = run(*args, '--page', str(number))
            self.assertEqual(result.returncode, 0, result.stderr)
            outputs.append(result.stdout)
        return total, outputs

    def test_pages_cover_a_part_in_order_with_whole_lines_and_no_overlap(self):
        lines = reader.SOURCE.read_text(encoding='utf-8-sig').splitlines()
        _, parts = reader.build_index(lines)
        start, end = parts[2]['start'], parts[2]['end']
        total, outputs = self.read_all_pages('--part', '2', '--chunk-size', '4000')
        self.assertGreater(total, 2)
        expected = start + 1
        collected = []
        for number, output in enumerate(outputs, 1):
            match = HEADER.search(output)
            self.assertEqual((int(match['page']), int(match['pages'])), (number, total))
            self.assertEqual(match['name'], reader.SOURCE.name)
            first, last = int(match['first']), int(match['last'])
            self.assertEqual(first, expected)
            page = lines[first - 1:last]
            self.assertTrue(len(page) == 1 or sum(len(line) + 1 for line in page) <= 4000)
            self.assertEqual(output[match.end():].strip('\n'), '\n'.join(page).strip('\n'))
            collected.extend(page)
            expected = last + 1
        self.assertEqual(expected - 1, end)
        self.assertEqual(collected, lines[start:end])

    def test_pages_prefer_to_end_after_a_blank_line(self):
        _, outputs = self.read_all_pages('--part', '2', '--chunk-size', '4000')
        lines = reader.SOURCE.read_text(encoding='utf-8-sig').splitlines()
        for output in outputs[:-1]:
            last = int(HEADER.search(output)['last'])
            self.assertEqual(lines[last - 1].strip(), '', f'page ending at line {last} splits a paragraph')

    def test_a_short_selection_is_one_page_and_english_pages_work(self):
        result = run('--section', '8.7', '--page', '1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(HEADER.search(result.stdout)['pages'], '1')
        english = run('--lang', 'en', '--part', '2', '--chunk-size', '5000', '--page', '2')
        self.assertEqual(english.returncode, 0, english.stderr)
        match = HEADER.search(english.stdout)
        self.assertEqual(match['name'], 'Xikari-On-Conditions-Structure-and-Transformation.md')
        self.assertEqual(match['page'], '2')

    def test_page_needs_a_selection_rejects_parallel_and_unknown_pages(self):
        alone = run('--page', '1')
        self.assertEqual(alone.returncode, 2)
        self.assertIn('--page needs --section, --part or --front', alone.stderr)
        parallel = run('--section', '8.7', '--parallel', '--page', '1')
        self.assertEqual(parallel.returncode, 2)
        self.assertIn('--parallel', parallel.stderr)
        beyond = run('--section', '8.7', '--page', '2')
        self.assertEqual(beyond.returncode, 2)
        self.assertIn('Unknown page: 2; available: 1 through 1', beyond.stderr)
        self.assertEqual(beyond.stdout, '')

    def test_chunk_summary_reports_the_last_line_for_readers_who_go_by_lines(self):
        import json
        summary = json.loads(run('--chunks').stdout)
        text = reader.SOURCE.read_text(encoding='utf-8-sig')
        self.assertEqual(summary['lines'], len(text.splitlines()))
        last = run('--chunk', str(summary['chunks'])).stdout
        self.assertIn(f"-{summary['lines']}]", last.splitlines()[1])
        guide = (ROOT / 'references/full-source-study.md').read_text(encoding='utf-8')
        self.assertIn('先看 `--chunks` 给出的总行数', guide)

    def test_reading_guide_names_the_page_option(self):
        guide = (ROOT / 'references/full-source-study.md').read_text(encoding='utf-8')
        self.assertIn('--page', guide)


if __name__ == '__main__':
    unittest.main()
