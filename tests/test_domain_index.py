"""Keep the domain entry index identical to what Appendix D of the theory text says."""

import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/build_domain_index.py'
spec = importlib.util.spec_from_file_location('build_domain_index_under_test', SCRIPT)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
INDEX = ROOT / 'references/domain-index.md'


class DomainIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = builder.SOURCE.read_bytes()
        cls.rows = builder.domains(cls.raw.decode('utf-8-sig'))
        cls.text = INDEX.read_text(encoding='utf-8')

    def test_index_is_exactly_what_the_builder_derives_from_the_source(self):
        self.assertEqual(self.text, builder.render(self.raw))
        check = subprocess.run([sys.executable, str(SCRIPT), '--check'], capture_output=True, text=True,
                               encoding='utf-8', timeout=30)
        self.assertEqual(check.returncode, 0, check.stderr)

    def test_every_domain_appears_once_with_its_own_title_links_and_topics(self):
        self.assertEqual([row['id'] for row in self.rows], [f'D.{number:02d}' for number in range(1, 33)])
        table = [line for line in self.text.splitlines() if re.match(r'\| D\.\d\d \|', line)]
        self.assertEqual(len(table), 32)
        for row, line in zip(self.rows, table):
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            self.assertEqual(cells, [row['id'], row['title'], row['links'], row['topics']])
            self.assertRegex(row['topics'], r'^\d\d\.01—\d\d\.\d\d$')
        topics = sum(int(row['topics'][-2:]) for row in self.rows)
        self.assertEqual(topics, 296)

    def test_header_binds_the_bundled_text_and_all_thirty_two_sections(self):
        header = json.loads(self.text.split('\n')[1])
        manifest = json.loads((ROOT / 'source/source-manifest.json').read_text(encoding='utf-8-sig'))
        self.assertEqual(header['theory_sha256'], manifest['sha256'])
        self.assertEqual(header['anchors'], [row['id'] for row in self.rows])

    def test_check_reports_a_stale_index_without_writing(self):
        self.assertNotEqual(builder.render(self.raw + '\n'.encode('utf-8')), self.text)
        before = INDEX.read_bytes()
        subprocess.run([sys.executable, str(SCRIPT), '--check'], capture_output=True, timeout=30)
        self.assertEqual(INDEX.read_bytes(), before)

    def test_index_ships_and_its_builder_does_not(self):
        package = json.loads((ROOT / 'skill-package.json').read_text(encoding='utf-8'))
        self.assertIn('references/domain-index.md', package['files'])
        self.assertNotIn('scripts/build_domain_index.py', package['files'])
        for name in ('modules/domain-mapping/MODULE.md', 'references/domains/README.md'):
            self.assertIn('domain-index.md', (ROOT / name).read_text(encoding='utf-8'), name)


if __name__ == '__main__':
    unittest.main()
