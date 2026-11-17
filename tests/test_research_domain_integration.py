"""Exercise research and mapping from the actual isolated install payload."""

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('integration_package_builder', ROOT / 'scripts/build_install_package.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ResearchDomainIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.work = Path(cls.temp.name)
        result = builder.build(ROOT, cls.work / 'archives')
        with zipfile.ZipFile(cls.work / 'archives' / result['archive']) as archive:
            archive.extractall(cls.work / 'installed')
        cls.install = cls.work / 'installed' / result['archive_root']
        cls.initial = cls.snapshot()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def snapshot(cls):
        return {p.relative_to(cls.install).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in cls.install.rglob('*') if p.is_file()}

    def tearDown(self):
        self.assertEqual(self.initial, self.snapshot(), 'Running a shipped tool changed its install payload')

    def command(self, script, *args, success=True):
        process = subprocess.run([sys.executable, str(self.install / 'scripts' / script), *map(str, args)],
                                 cwd=self.work, capture_output=True, text=True, encoding='utf-8', timeout=30)
        if success:
            self.assertEqual(process.returncode, 0, process.stderr)
        else:
            self.assertNotEqual(process.returncode, 0, process.stdout)
            self.assertNotIn('Traceback', process.stderr)
        return process

    def test_installed_research_delivers_both_reports_and_preserves_independent_findings(self):
        source = self.install / 'assets/examples/research.json'
        destination = self.work / 'research-output'
        self.command('research.py', '--research', source, 'validate')
        self.command('research.py', '--research', source, 'render', '--output', destination)
        report = (destination / 'research-report.md').read_text(encoding='utf-8')
        issues = (destination / 'research-issues.md').read_text(encoding='utf-8')
        for content in (report, issues):
            self.assertIn('I-identification', content)
            self.assertIn('I-followup', content)
        self.assertIn('20 个百分点', report)
        self.assertIn('不能判断就业机会改善或恶化', report)
        result = json.loads(self.command('research.py', '--research', source, 'impact',
                                        '--changed', 'S-register').stdout)
        self.assertEqual(set(result['affected_findings']), {'F-completion', 'F-causal', 'F-use'})
        self.assertEqual(set(result['independent_findings']), {'F-definition', 'F-employment'})
        before = {p.name: p.read_bytes() for p in destination.iterdir()}
        self.command('research.py', '--research', source, 'render', '--output', destination, success=False)
        self.assertEqual(before, {p.name: p.read_bytes() for p in destination.iterdir()})

    def test_installed_mapping_disambiguates_and_does_not_invent_missing_context(self):
        source = self.install / 'assets/examples/domain-mapping.json'
        result = json.loads(self.command('domain_mapping.py', '--mapping', source, 'lookup', '--term', '反馈').stdout)
        self.assertTrue(result['ambiguous'])
        self.assertEqual({row['id'] for row in result['matches']}, {'m-comments', 'm-survey'})
        result = json.loads(self.command('domain_mapping.py', '--mapping', source, 'lookup',
                                        '--term', '教师评语', '--context', '教师对作业的评语').stdout)
        self.assertEqual([row['id'] for row in result['matches']], ['m-comments'])
        self.assertEqual(result['matches'][0]['assessments']['factual']['status'], 'unknown')
        absent = json.loads(self.command('domain_mapping.py', '--mapping', source, 'lookup',
                                        '--term', '反馈', '--context', '未提供的语境').stdout)
        self.assertEqual(absent['matches'], [])
        change = json.loads(self.command('domain_mapping.py', '--mapping', source, 'impact',
                                        '--changed', 's-course').stdout)
        self.assertEqual(set(change['affected_outputs']), {'o-feedback', 'o-response'})
        self.assertEqual(change['unaffected_outputs'], ['o-completion'])

    def test_source_backed_domain_packs_are_usable_from_install(self):
        for name in ('organization-work', 'education-learning', 'technical-maintenance'):
            with self.subTest(domain=name):
                source = self.install / 'assets/domains' / (name + '.json')
                self.command('domain_mapping.py', '--mapping', source, 'validate')
                mapping = json.loads(source.read_text(encoding='utf-8'))
                self.assertTrue(mapping['sources'])
                self.assertTrue(all(s['kind'] == 'document' for s in mapping['sources']))
                entry = mapping['entries'][0]
                result = json.loads(self.command('domain_mapping.py', '--mapping', source, 'lookup',
                                                '--term', entry['terms'][0], '--context', entry['context']).stdout)
                self.assertIn(entry['id'], [row['id'] for row in result['matches']])
                destination = self.work / (name + '.md')
                self.command('domain_mapping.py', '--mapping', source, 'render', '--output', destination)
                self.assertIn(mapping['outputs'][0]['text'], destination.read_text(encoding='utf-8'))

    def test_installed_mapping_revision_reaches_the_research_report(self):
        mapping = self.install / 'assets/examples/domain-mapping.json'
        identity = json.loads(self.command('domain_mapping.py', '--mapping', mapping, 'validate').stdout)
        study = json.loads((self.install / 'assets/examples/research.json').read_text(encoding='utf-8'))
        study['inputs'][-1]['mapping_ref'] = {
            'id': identity['id'], 'version': identity['version'],
            'sha256': identity['snapshot_sha256'], 'node_ids': ['o-completion'],
        }
        study['findings'].append({
            'id': 'F-independent', 'title': '同时改变招募与教学的记录', 'kind': 'descriptive',
            'status': 'supported', 'body': '登记材料同时记录两项改变，不依赖完成口径的定义。',
            'depends_on': ['S-changes'], 'limitations': [], 'change_conditions': ['该登记被更正。'],
        })
        path = self.work / 'bound-research.json'
        path.write_text(json.dumps(study, ensure_ascii=False), encoding='utf-8')
        original = path.read_bytes()
        result = json.loads(self.command('research.py', '--research', path, 'impact-mapping',
                                        '--mapping', mapping, '--changed', 's-completion').stdout)
        self.assertEqual(set(result['affected_findings']),
                         {'F-completion', 'F-causal', 'F-employment', 'F-definition', 'F-use'})
        self.assertEqual(result['independent_findings'], ['F-independent'])
        self.assertEqual(set(result['affected_issues']), {'I-identification', 'I-followup'})
        self.assertTrue(result['summary_needs_review'])
        self.assertEqual(path.read_bytes(), original)
        destination = self.work / 'bound-research-output'
        self.command('research.py', '--research', path, 'render', '--output', destination)
        self.assertIn(identity['snapshot_sha256'], (destination / 'research-report.md').read_text(encoding='utf-8'))
        newer = self.work / 'mapping-reformatted.json'
        newer.write_bytes(mapping.read_bytes() + b'\n')
        result = self.command('research.py', '--research', path, 'impact-mapping',
                              '--mapping', newer, '--changed', 's-completion', success=False)
        self.assertIn('SHA-256', result.stderr)
        self.assertEqual(result.stdout, '')

    def test_both_tools_reject_writing_into_the_installed_package(self):
        self.command('research.py', '--research', self.install / 'assets/examples/research.json',
                     'render', '--output', self.install / 'forbidden-research', success=False)
        self.command('domain_mapping.py', '--mapping', self.install / 'assets/examples/domain-mapping.json',
                     'render', '--output', self.install / 'forbidden-mapping.md', success=False)

    def test_finite_tools_keep_joint_conflicts_visible_in_the_install(self):
        source = self.install / 'assets/examples/finite-tools.json'
        collection = json.loads(source.read_text(encoding='utf-8'))
        results = {}
        for case in collection['models']:
            result = json.loads(self.command('finite_tools.py', '--model', source, '--case', case, 'compute').stdout)
            self.assertTrue(result['computed'])
            self.assertTrue(result['model']['fictional'])
            results[case] = result['result']
        self.assertEqual(results['schedule-shared-capacity']['status'], 'infeasible_in_model')
        self.assertIsNone(results['schedule-shared-capacity']['schedule'])
        self.assertTrue(results['relation-local-without-chain']['all_local_relations_nonempty'])
        self.assertEqual(results['relation-local-without-chain']['status'], 'no_joint_witness')
        self.command('finite_tools.py', '--model', source, '--case', 'schedule-shared-capacity',
                     'compute', '--output', self.install / 'forbidden-finite.json', success=False)

    def test_shipped_new_guides_link_to_shipped_runtime_resources(self):
        required = ['modules/research/MODULE.md', 'modules/domain-mapping/MODULE.md',
                    'references/output-modes.md', 'references/capability-operations.md',
                    'references/capability-quickstart.md', 'references/finite-tools.md',
                    'references/research-format.md', 'references/domain-mapping-format.md']
        required += [p.relative_to(ROOT).as_posix() for p in (ROOT / 'references/domains').glob('*.md')]
        required += [p.relative_to(ROOT).as_posix() for p in (ROOT / 'references/output-modes').glob('*.md')]
        required += [p.relative_to(ROOT).as_posix() for p in (ROOT / 'assets/examples/output-modes').glob('*.md')]
        for name in required:
            path = self.install / name
            self.assertTrue(path.is_file(), name)
            for target in re.findall(r'\]\(([^)\s]+)\)', path.read_text(encoding='utf-8')):
                if '://' in target or target.startswith('#'):
                    continue
                relative = target.split('#')[0]
                if relative:
                    destination = (path.parent / relative).resolve()
                    self.assertTrue(destination.is_relative_to(self.install.resolve()), (name, target))
                    self.assertTrue(destination.exists(), (name, target))


if __name__ == '__main__':
    unittest.main()
