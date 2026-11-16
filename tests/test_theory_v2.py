"""Engineering checks for the approved v2 manuscript and its reading paths.

These checks establish identity, reachability and packaging, not whether a model
understands the text or gives a sound answer. Semantic scenarios live outside
the installable skill and are assessed separately.
"""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
V2_SHA256 = '6ef2e508474d4ac1ad07d7e4e068955342c405b5f680afcfc40d68cca3d0149c'
NEW_SECTIONS = ('2.4.3', '2.14', '6.10.1', '7.6.1', '14.4.1', '14.9.1')


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reader = load('read_source')
lint = load('lint_derived')


class TheoryV2Tests(unittest.TestCase):
    def test_approved_manuscript_identity_is_not_just_a_self_consistent_manifest(self):
        manifest = json.loads((ROOT / 'source/source-manifest.json').read_text(encoding='utf-8'))
        raw = (ROOT / 'source' / manifest['source_file']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), V2_SHA256)
        self.assertEqual(manifest['sha256'], V2_SHA256)
        self.assertEqual(len(raw), 692246)
        self.assertEqual(manifest['bytes'], len(raw))
        self.assertEqual(manifest['theory_version'], 'v2')

    def test_each_new_section_can_be_read_completely_by_the_shipped_cli(self):
        lines = reader.SOURCE.read_text(encoding='utf-8-sig').splitlines()
        sections, _ = reader.build_index(lines)
        for anchor in NEW_SECTIONS:
            with self.subTest(anchor=anchor):
                self.assertIn(anchor, sections)
                row = sections[anchor]
                result = subprocess.run(
                    [sys.executable, str(ROOT / 'scripts/read_source.py'), '--section', anchor],
                    capture_output=True, text=True, encoding='utf-8',
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                _, separator, body = result.stdout.lstrip('\n').partition('\n\n')
                self.assertTrue(separator)
                self.assertEqual(body.rstrip('\n'), '\n'.join(lines[row['start']:row['end']]))

    def test_relevant_module_reading_paths_cover_new_sections_in_full(self):
        lines = reader.SOURCE.read_text(encoding='utf-8-sig').splitlines()
        ranges = lint.source_ranges(lines)
        core = json.loads((ROOT / 'references/reading-core.json').read_text(encoding='utf-8'))['reading']
        required = {
            'contract': ('2.14',),
            'mechanism': ('2.4.3', '7.6.1'),
            'dynamics': ('6.10.1',),
            'forecast': ('6.10.1',),
            'choice': ('14.4.1', '14.9.1'),
        }
        for module, anchors in required.items():
            meta = lint.metadata((ROOT / f'modules/{module}/MODULE.md').read_text(encoding='utf-8'))
            covered = reader.merge_ranges([ranges[key] for key in core + meta['reading']])
            for anchor in anchors:
                with self.subTest(module=module, anchor=anchor):
                    self.assertIn(anchor, ranges)
                    start, end = ranges[anchor]
                    self.assertTrue(any(left <= start and end <= right for left, right in covered),
                                    f'Missing full reading dependency: {module} -> {anchor}')

    def test_new_rule_cards_are_shipped_drafts_with_verifiable_source_quotes(self):
        index = json.loads((ROOT / 'rules/index.json').read_text(encoding='utf-8'))['rules']
        payload = set(json.loads((ROOT / 'skill-package.json').read_text(encoding='utf-8'))['files'])
        units = lint.source_units(reader.SOURCE.read_text(encoding='utf-8-sig'))
        required = {
            'CM-ALLOCATION-CAPABILITY': '7.6.1',
            'PATH-formation-maintenance-recovery-replication': '6.10.1',
        }
        for card_id, anchor in required.items():
            with self.subTest(card=card_id):
                rows = [row for row in index if row['id'] == card_id]
                self.assertEqual(len(rows), 1)
                row = rows[0]
                self.assertIn(row['file'], payload)
                text = (ROOT / row['file']).read_text(encoding='utf-8-sig')
                meta = lint.metadata(text)
                self.assertEqual(row, dict(meta, file=row['file']))
                self.assertEqual(meta['status'], 'draft')
                self.assertEqual(meta['theory_sha256'], V2_SHA256)
                self.assertIn(anchor, meta['anchors'])
                quotes = [quote for quote in lint.original_quotes(text) if anchor in quote['anchors']]
                self.assertTrue(quotes, f'{card_id} must quote its defining source section')
                for quote in quotes:
                    self.assertIn(lint.compact_whitespace(quote['text']),
                                  lint.compact_whitespace(units[anchor]))


if __name__ == '__main__':
    unittest.main()
