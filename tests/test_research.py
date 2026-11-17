"""Research double reports: limitation propagation, dependencies and safe publication."""

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'research.py'
EXAMPLE = ROOT / 'assets' / 'examples' / 'research.json'
spec = importlib.util.spec_from_file_location('xikari_research_test', SCRIPT)
research = importlib.util.module_from_spec(spec)
spec.loader.exec_module(research)


def example():
    return json.loads(EXAMPLE.read_text(encoding='utf-8'))


class ResearchMeaningTests(unittest.TestCase):
    def test_example_retains_descriptive_causal_and_unknown_identities(self):
        data = example()
        report = research.render_documents(data)['research-report.md']
        self.assertIn('30/50 = 60%', report)
        self.assertIn('40/50 = 80%', report)
        self.assertIn('判断身份：描述判断；状态：在声明范围内有支持', report)
        self.assertIn('判断身份：因果判断；状态：未知', report)
        self.assertIn('就业变化保留未知，不填零', report)
        self.assertIn('合成材料', report)
        self.assertEqual(data['findings'][1]['status'], 'unknown')

    def test_major_issue_is_visible_near_summary_and_downstream_claim(self):
        documents = research.render_documents(example())
        main = documents['research-report.md']
        summary = main.split('## 范围与方法')[0]
        downstream = main.split('### F-use')[1].split('## 解释范围')[0]
        issue = '不能把结业比例提高写成课程调整的因果效果'
        self.assertIn(issue, summary)
        self.assertIn(issue, downstream)
        self.assertIn(issue, documents['research-issues.md'])

    def test_minor_issue_remains_local_and_resolved_issue_is_not_open_warning(self):
        data = example()
        data['issues'][0]['materiality'] = 'minor'
        data['issues'][1].update(status='resolved_within_scope', resolution_scope='仅解决记录取得；识别问题仍另列。')
        main = research.render_documents(data)['research-report.md']
        summary = main.split('## 范围与方法')[0]
        self.assertNotIn('影响当前判断的重大未决', summary)
        self.assertIn('在限定范围内解决', main)

    def test_source_correction_affects_only_declared_dependents(self):
        result = research.impact(example(), ['S-register'])
        self.assertEqual(result['affected_findings'], ['F-completion', 'F-causal', 'F-use'])
        self.assertEqual(result['independent_findings'], ['F-employment', 'F-definition'])
        self.assertEqual(result['affected_issues'], ['I-identification'])
        self.assertEqual(result['paths']['F-use'], ['S-register', 'F-completion', 'F-use'])
        self.assertTrue(result['summary_needs_review'])

    def test_mapping_and_multiple_changes_propagate_without_editing_findings(self):
        data = example()
        before = copy.deepcopy(data)
        result = research.impact(data, ['M-completion', 'S-followup', 'M-completion'])
        self.assertEqual(set(result['affected_findings']), {item['id'] for item in data['findings']})
        self.assertEqual(result['changed'], ['M-completion', 'S-followup'])
        research.render_documents(data)
        self.assertEqual(data, before)

    def test_change_to_local_finding_does_not_mark_independent_summary(self):
        result = research.impact(example(), ['F-definition'])
        self.assertEqual(result['affected_findings'], ['F-definition'])
        self.assertFalse(result['summary_needs_review'])

    def test_unknown_source_is_not_used_as_zero_or_supported_fact(self):
        main = research.render_documents(example())['research-report.md']
        section = main.split('### F-employment')[1].split('### F-definition')[0]
        self.assertIn('尚依赖未知输入', section)
        self.assertIn('S-followup → F-employment', section)
        self.assertNotIn('就业率为 0', section)

    def test_no_issues_requires_scope_and_does_not_certify_universal_success(self):
        data = example()
        data['issues'] = []
        report = research.render_documents(data)['research-issues.md']
        self.assertIn('不表示理论或研究普遍无误', report)
        data['issue_assessment'] = ''
        with self.assertRaises(ValueError):
            research.validate_research(data)

    def test_theory_candidate_requires_specific_commitment_and_real_section(self):
        data = example()
        issue = data['issues'][0]
        issue['categories'] = ['theory_candidate']
        with self.assertRaises(ValueError):
            research.validate_research(data)
        issue['theory'] = {'proposition': '合成测试命题，不是实际引用。', 'anchor': '2.13',
                           'source_sha256': research.theory_index()['sha256'],
                           'scope': '仅用于结构校验测试。', 'challenge': '需由作者核对的具体挑战。'}
        research.validate_research(data)
        text = research.render_documents(data)['research-issues.md']
        self.assertIn('不证明原命题已被反驳', text)
        issue['theory']['anchor'] = '99.999'
        with self.assertRaisesRegex(ValueError, '不存在'):
            research.validate_research(data)
        issue['theory']['anchor'] = '2.13'
        issue['theory']['source_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, '原文不一致'):
            research.validate_research(data)


class ResearchValidationTests(unittest.TestCase):
    def test_cycle_unknown_dependency_and_duplicate_cross_kind_ids_rejected(self):
        edits = [
            lambda d: d['findings'][0]['depends_on'].append('F-use'),
            lambda d: d['findings'][0]['depends_on'].append('F-completion'),
            lambda d: d['findings'][0]['depends_on'].append('missing'),
            lambda d: d['findings'][0].update(id='S-register'),
            lambda d: d['issues'][0].update(id='F-use'),
        ]
        for edit in edits:
            with self.subTest(edit=edit):
                data = example()
                edit(data)
                with self.assertRaises(ValueError):
                    research.validate_research(data)

    def test_invalid_data_at_each_level_is_not_silently_discarded(self):
        edits = [
            lambda d: d.update(schema_version=True),
            lambda d: d.update(typo='ignored?'),
            lambda d: d['inputs'][0].update(extra='wrong'),
            lambda d: d['findings'][0].update(explanation='wrong key'),
            lambda d: d['issues'][0].update(explained=True),
            lambda d: d['findings'][0].update(kind='forecast'),
            lambda d: d['findings'][0].update(status='certified'),
            lambda d: d['inputs'][0].update(locator=''),
            lambda d: d['findings'][0].update(body=''),
            lambda d: d['findings'][0].update(depends_on=[]),
            lambda d: d['findings'][0].update(change_conditions=[]),
            lambda d: d['issues'][0].update(affected_findings=['missing']),
            lambda d: d['issues'][0].update(categories=['invented']),
            lambda d: d['issues'][0].update(status='partially_resolved', resolution_scope=''),
            lambda d: d['issues'][0].update(next_work=''),
            lambda d: d.update(summary_refs=['S-register']),
            lambda d: d['findings'][0].update(limitations=[float('nan')]),
        ]
        for edit in edits:
            with self.subTest(edit=edit):
                data = example()
                edit(data)
                with self.assertRaises(ValueError):
                    research.validate_research(data)

    def test_bad_changed_ids_do_not_return_empty_success(self):
        for changed in ([], ['missing'], 'S-register', [None]):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                research.impact(example(), changed)

    def test_deep_declared_dependency_chain_is_iterative(self):
        data = example()
        data['issues'] = []
        template = data['findings'][0]
        data['findings'] = []
        for index in range(1200):
            item = copy.deepcopy(template)
            item.update(id=f'F{index}', depends_on=['S-register' if index == 0 else f'F{index-1}'])
            data['findings'].append(item)
        data['summary_refs'] = ['F1199']
        result = research.impact(data, ['S-register'])
        self.assertEqual(len(result['affected_findings']), 1200)
        self.assertEqual(result['paths']['F1199'][-1], 'F1199')

    def test_reordering_records_does_not_change_dependency_reachability(self):
        data = example()
        expected = set(research.impact(data, ['S-register'])['affected_findings'])
        data['inputs'].reverse()
        data['findings'].reverse()
        actual = set(research.impact(data, ['S-register'])['affected_findings'])
        self.assertEqual(actual, expected)

    def test_bad_json_duplicate_keys_and_nonfinite_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            for raw in ('{"schema_version":1,"schema_version":1}', '{"x":NaN}', '{"x":Infinity}', '{'):
                path.write_text(raw, encoding='utf-8')
                with self.subTest(raw=raw), self.assertRaises(ValueError):
                    research.read_research(path)

    def test_oversize_input_read_is_bounded_before_parsing(self):
        class TooLargeStream:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                self.limit = limit
                return b' ' * limit

        stream = TooLargeStream()
        with patch.object(Path, 'open', return_value=stream), self.assertRaisesRegex(ValueError, '4 MiB'):
            research.read_research(Path('large.json'))
        self.assertEqual(stream.limit, 4 * 1024 * 1024 + 1)


class ResearchPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / '双成果'
        self.documents = research.render_documents(example())

    def assert_no_partial(self):
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.root.glob('.research-*')))
        self.assertFalse(self.output.with_name(self.output.name + '.research.lock').exists())

    def test_pair_is_published_with_utf8_content(self):
        research.write_documents(self.documents, self.output)
        self.assertEqual({p.name for p in self.output.iterdir()}, set(self.documents))
        for name, contents in self.documents.items():
            self.assertEqual((self.output / name).read_text(encoding='utf-8'), contents)

    def test_existing_empty_directory_and_file_are_never_overwritten(self):
        self.output.mkdir()
        with self.assertRaises(ValueError):
            research.write_documents(self.documents, self.output)
        self.assertEqual(list(self.output.iterdir()), [])
        self.output.rmdir()
        self.output.write_text('external', encoding='utf-8')
        with self.assertRaises(ValueError):
            research.write_documents(self.documents, self.output)
        self.assertEqual(self.output.read_text(), 'external')

    def test_preexisting_lock_is_not_deleted(self):
        lock = self.output.with_name(self.output.name + '.research.lock')
        lock.write_text('other writer', encoding='utf-8')
        with self.assertRaises(ValueError):
            research.write_documents(self.documents, self.output)
        self.assertEqual(lock.read_text(), 'other writer')
        self.assertFalse(self.output.exists())

    def test_failure_writing_second_document_publishes_neither(self):
        real_open = Path.open

        def fail_second(path, *args, **kwargs):
            if path.name == 'research-issues.md':
                raise OSError('simulated disk failure')
            return real_open(path, *args, **kwargs)

        with patch.object(Path, 'open', fail_second), self.assertRaises(OSError):
            research.write_documents(self.documents, self.output)
        self.assert_no_partial()

    def test_final_race_cannot_replace_even_an_empty_external_directory(self):
        real_publish = research.publish_directory

        def concurrent_directory(staging, output):
            output.mkdir()
            real_publish(staging, output)

        with patch.object(research, 'publish_directory', concurrent_directory), self.assertRaises(OSError):
            research.write_documents(self.documents, self.output)
        self.assertTrue(self.output.is_dir())
        self.assertEqual(list(self.output.iterdir()), [])
        self.assertFalse(list(self.root.glob('.research-*')))

    def test_installed_output_and_linked_installed_output_rejected(self):
        destination = ROOT / 'research-test-must-not-exist'
        self.assertFalse(destination.exists())
        with self.assertRaises(OSError):
            research.write_documents(self.documents, destination)
        self.assertFalse(destination.exists())
        link = self.root / 'installed-link'
        try:
            link.symlink_to(ROOT, target_is_directory=True)
        except (OSError, NotImplementedError):
            return
        with self.assertRaises(OSError):
            research.write_documents(self.documents, link / 'research-test-must-not-exist')
        self.assertFalse(destination.exists())

    def test_dangling_destination_symlink_is_not_replaced(self):
        try:
            self.output.symlink_to(self.root / 'missing', target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('symbolic links unavailable')
        with self.assertRaises(ValueError):
            research.write_documents(self.documents, self.output)
        self.assertTrue(self.output.is_symlink())

    def test_document_pair_cannot_be_partially_requested(self):
        with self.assertRaises(ValueError):
            research.write_documents({'research-report.md': 'alone'}, self.output)
        self.assert_no_partial()


class ResearchCliTests(unittest.TestCase):
    def run_cli(self, source, *args):
        return subprocess.run([sys.executable, str(SCRIPT), '--research', str(source), *args],
                              capture_output=True, text=True, encoding='utf-8')

    def test_validate_render_and_impact_leave_input_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / '研究输入.json'
            source.write_text(EXAMPLE.read_text(encoding='utf-8'), encoding='utf-8')
            before = source.read_bytes()
            check = self.run_cli(source, 'validate')
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertTrue(json.loads(check.stdout)['structure_valid'])
            output = Path(directory) / 'output'
            render = self.run_cli(source, 'render', '--output', str(output))
            self.assertEqual(render.returncode, 0, render.stderr)
            self.assertTrue((output / 'research-issues.md').exists())
            impact = self.run_cli(source, 'impact', '--changed', 'S-register')
            self.assertEqual(impact.returncode, 0, impact.stderr)
            self.assertIn('F-use', json.loads(impact.stdout)['affected_findings'])
            rerender = self.run_cli(source, 'render', '--output', str(output))
            self.assertNotEqual(rerender.returncode, 0)
            self.assertEqual(source.read_bytes(), before)

    def test_bad_input_fails_without_creating_output_or_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'bad.json'
            source.write_text('{}', encoding='utf-8')
            output = Path(directory) / 'output'
            result = self.run_cli(source, 'render', '--output', str(output))
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Traceback', result.stderr)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
