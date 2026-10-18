import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lint_derived', ROOT / 'scripts/lint_derived.py')
lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint)


class DerivedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'source').mkdir()
        (self.root / 'modules/example').mkdir(parents=True)
        self.source = '# Book\n\n<a id="part_1"></a>\n# Part\n## 1.1 First\nbody\n### 1.1.1 Child\nchild\n## 1.2 Second\nother\n'
        self.install_source(self.source)
        self.write_module(['1.1'], 'Read §1.1.')

    def install_source(self, source):
        raw = source.encode('utf-8')
        self.sha = hashlib.sha256(raw).hexdigest()
        (self.root / 'source/theory.md').write_bytes(raw)
        (self.root / 'source/source-manifest.json').write_text(json.dumps({'source_file': 'theory.md', 'sha256': self.sha, 'bytes': len(raw)}))

    def write_module(self, anchors, body):
        meta = {'id': 'M0', 'reading': anchors, 'theory_sha256': self.sha}
        (self.root / 'modules/example/MODULE.md').write_text('---\n' + json.dumps(meta) + '\n---\n' + body, encoding='utf-8')

    def write_derived(self, relative, meta, body=''):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('---\n' + json.dumps(meta) + '\n---\n' + body, encoding='utf-8')
        return path

    def test_reference_and_agent_derived_bindings_are_checked(self):
        for relative, field in [('references/nested/method.md', 'anchors'),
                                ('agents/nested/analyst.md', 'reading')]:
            with self.subTest(relative=relative):
                self.write_derived(relative, {'id': relative, field: ['9.99'],
                                              'theory_sha256': '0' * 64})
                result = lint.check(self.root)
                self.assertIn(f'{relative}: stale theory_sha256', result['errors'])
                self.assertIn(f'{relative}: unknown source anchor 9.99', result['errors'])

    def test_valid_bindings_are_read_only(self):
        self.write_derived('references/nested/method.md',
                           {'id': 'method', 'anchors': ['1.1'], 'theory_sha256': self.sha})
        self.write_derived('agents/analyst.md',
                           {'id': 'analyst', 'reading': ['front', 'part:1'], 'theory_sha256': self.sha})
        (self.root / 'references/guide.md').write_text('# Plain guide\n\nSee §9.99.\n', encoding='utf-8')
        before = {str(p): (p.read_bytes(), p.stat().st_mtime_ns)
                  for p in self.root.rglob('*') if p.is_file()}
        result = lint.check(self.root)
        self.assertTrue(result['ok'], result['errors'])
        self.assertEqual(result['resource_count'], 3)
        self.assertEqual(before, {str(p): (p.read_bytes(), p.stat().st_mtime_ns)
                                  for p in self.root.rglob('*') if p.is_file()})

    def test_reference_and_agent_dependencies_identify_source_changes(self):
        old = self.root / 'old.md'
        old.write_text(self.source, encoding='utf-8')
        self.install_source(self.source.replace('child\n', 'changed child\n'))
        self.write_module(['1.1'], '')
        self.write_derived('references/nested/method.md',
                           {'id': 'method', 'anchors': ['1.2'], 'theory_sha256': self.sha}, 'Read §1.1.')
        self.write_derived('agents/analyst.md',
                           {'id': 'analyst', 'reading': ['part:1'], 'theory_sha256': self.sha})
        self.write_derived('references/unaffected.md',
                           {'id': 'unaffected', 'anchors': ['1.2'], 'theory_sha256': self.sha})
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = lint.check(self.root, old)
        self.assertTrue(result['ok'], result['errors'])
        self.assertEqual({item['file']: item['changed_anchors'] for item in result['affected']}, {
            'modules/example/MODULE.md': ['1.1'],
            'references/nested/method.md': ['1.1'],
            'agents/analyst.md': ['part:1'],
        })
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_each_declared_dependency_field_is_validated(self):
        relative = 'agents/analyst.md'
        self.write_derived(relative, {'id': 'analyst', 'anchors': ['9.99'],
                                      'reading': ['1.1'], 'theory_sha256': self.sha})
        self.assertIn(f'{relative}: unknown source anchor 9.99', lint.check(self.root)['errors'])

    def test_reference_frontmatter_errors_are_not_ignored(self):
        path = self.root / 'references/method.md'
        path.parent.mkdir()
        path.write_text('---\n{invalid}\n---\n# Method\n', encoding='utf-8')
        self.assertIn('references/method.md: frontmatter must be a JSON object (a YAML subset)',
                      lint.check(self.root)['errors'])

    def test_plain_guides_do_not_count_as_derived_resources(self):
        (self.root / 'modules/example/MODULE.md').unlink()
        path = self.root / 'references/guide.md'
        path.parent.mkdir()
        path.write_text('# Plain guide\n', encoding='utf-8')
        result = lint.check(self.root)
        self.assertEqual(result['resource_count'], 0)
        self.assertIn('no derived resources found', result['errors'])

    def test_reference_link_cannot_escape_package(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / 'external.md'
            target.write_text('---\n{}\n---\n', encoding='utf-8')
            link = self.root / 'references/external.md'
            link.parent.mkdir()
            try:
                link.symlink_to(target)
            except OSError as exc:
                if os.name != 'nt':
                    self.skipTest(f'symlinks unavailable: {exc}')
                link.parent.rmdir()
                junction = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link.parent), outside],
                                          capture_output=True)
                if junction.returncode:
                    self.skipTest(f'directory links unavailable: {junction.stderr!r}')
            self.assertIn('references/external.md: derived resource escapes package',
                          lint.check(self.root)['errors'])

    def test_unknown_range_endpoint_is_rejected(self):
        self.write_module(['1.1'], 'Read §1.1—1.99.')
        self.assertIn('unknown source anchor 1.99', '\n'.join(lint.check(self.root)['errors']))

    def test_body_anchor_followed_by_sentence_period_is_checked(self):
        self.write_module(['1.1'], 'Read §9.99.')
        self.assertIn('unknown source anchor 9.99', '\n'.join(lint.check(self.root)['errors']))

    def test_wrong_source_bytes_fail_even_with_matching_card_header(self):
        (self.root / 'source/theory.md').write_text(self.source + 'extra', encoding='utf-8')
        errors = '\n'.join(lint.check(self.root)['errors'])
        self.assertIn('source bytes differ', errors)
        self.assertIn('stale theory_sha256', errors)

    def test_previous_text_identifies_only_affected_dependencies(self):
        old = self.root / 'old.md'
        old.write_text(self.source, encoding='utf-8')
        self.install_source(self.source.replace('other', 'changed sibling'))
        self.write_module(['1.1'], 'Read §1.1.')
        self.assertEqual(lint.check(self.root, old)['affected'], [])
        self.install_source(self.source.replace('child\n', 'changed child\n'))
        self.write_module(['1.1'], 'Read §1.1.')
        result = lint.check(self.root, old)
        self.assertEqual(result['affected'][0]['changed_anchors'], ['1.1'])

    def test_unknown_reading_and_missing_frontmatter_fail(self):
        self.write_module(['part:99'], '')
        self.assertFalse(lint.check(self.root)['ok'])
        (self.root / 'modules/example/MODULE.md').write_text('# no metadata')
        self.assertIn('frontmatter', '\n'.join(lint.check(self.root)['errors']))

    def test_card_index_mismatch_and_unknown_competitor_fail(self):
        folder = self.root / 'rules/mechanism'
        folder.mkdir(parents=True)
        card = {'id': 'CM-A', 'type': 'mechanism', 'anchors': ['1.1'], 'theory_sha256': self.sha,
                'status': 'draft', 'applies_to': ['system'], 'triggers': ['change'], 'competes_with': ['CM-X']}
        (folder / 'a.md').write_text('---\n' + json.dumps(card) + '\n---\nRead §1.1.', encoding='utf-8')
        row = dict(card, file='rules/mechanism/a.md', status='author-confirmed')
        (self.root / 'rules/index.json').write_text(json.dumps({'theory_sha256': self.sha, 'rules': [row]}))
        errors = '\n'.join(lint.check(self.root)['errors'])
        self.assertIn('unknown competing rule CM-X', errors)
        self.assertIn('status differs', errors)


if __name__ == '__main__':
    unittest.main()
