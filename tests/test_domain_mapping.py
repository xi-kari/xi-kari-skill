"""Behavioral examples and failure cases for supplied domain mappings."""

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/domain_mapping.py'
EXAMPLE = ROOT / 'assets/examples/domain-mapping.json'
spec = importlib.util.spec_from_file_location('domain_mapping', SCRIPT)
mapping = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mapping)


def example():
    return json.loads(EXAMPLE.read_text(encoding='utf-8'))


class MappingTests(unittest.TestCase):
    def test_unknown_evidence_does_not_become_supported_from_a_word_match(self):
        result = mapping.lookup(example(), '教师评语')
        self.assertEqual(result['status'], 'matched')
        row = result['matches'][0]
        self.assertEqual(row['assessments']['semantic']['status'], 'partial')
        self.assertEqual(row['assessments']['factual']['status'], 'unknown')
        self.assertEqual(row['assessments']['formal']['status'], 'not_claimed')
        self.assertIn('不会', mapping.impact(example(), ['s-course'])['notice'])

    def test_same_word_returns_all_senses_until_context_is_explicit(self):
        result = mapping.lookup(example(), '反馈')
        self.assertEqual(result['status'], 'ambiguous')
        self.assertEqual({row['id'] for row in result['matches']}, {'m-comments', 'm-survey'})
        result = mapping.lookup(example(), '反馈', '学习者对课程的问卷')
        self.assertEqual([row['id'] for row in result['matches']], ['m-survey'])
        self.assertEqual(mapping.lookup(example(), '反馈', '另一机构')['status'], 'unmapped')

    def test_alias_and_unicode_variants_retain_same_record_not_extra_support(self):
        data = example()
        data['entries'][0]['terms'].append('Teacher FEEDBACK')
        before = copy.deepcopy(data)
        matched = mapping.lookup(data, ' Ｔｅａｃｈｅｒ  feedback ')
        self.assertEqual(matched['matches'][0], data['entries'][0])
        self.assertEqual(mapping.lookup(data, '教师评语')['matches'], mapping.lookup(data, '反馈', data['entries'][0]['context'])['matches'])
        self.assertEqual(data, before)

    def test_not_found_is_explicit_and_does_not_guess_by_substring(self):
        for query in ('评价', '评语', '学习成效已改善'):
            result = mapping.lookup(example(), query)
            self.assertEqual(result['status'], 'unmapped')
            self.assertFalse(result['matches'])
        with self.assertRaises(mapping.MappingError):
            mapping.lookup(example(), ' ')
        with self.assertRaises(mapping.MappingError):
            mapping.lookup(example(), 'not-present', [])

    def test_correction_propagates_to_transitive_dependents_only(self):
        result = mapping.impact(example(), ['s-course'])
        self.assertEqual(result['affected_entries'], ['m-change', 'm-comments'])
        self.assertEqual(result['affected_outputs'], ['o-feedback', 'o-response'])
        self.assertEqual(result['unaffected_outputs'], ['o-completion'])
        self.assertEqual(result['paths']['o-response'], ['s-course', 'm-change', 'o-response'])
        data = example()
        data['entries'][2]['source_ids'] = ['s-survey']
        data['entries'][2]['assessments']['semantic']['basis'] = ['s-survey']
        result = mapping.impact(data, ['m-comments'])
        self.assertEqual(result['paths']['o-response'], ['m-comments', 'm-change', 'o-response'])

    def test_assessment_field_method_and_review_sources_are_dependencies(self):
        for variant in ('assessment', 'field', 'method', 'review'):
            with self.subTest(variant=variant):
                data = example()
                row = data['entries'][0]
                if variant == 'assessment':
                    row['assessments']['factual']['basis'] = ['s-completion']
                elif variant == 'field':
                    row['fields'] = copy.deepcopy(data['entries'][3]['fields'])
                elif variant == 'method':
                    row['methods'][0]['source_ids'] = ['s-completion']
                else:
                    row['target_review'] = dict(requested=True, status='reviewed', basis=['s-completion'], rationale='仅作输入依赖测试')
                self.assertIn('m-comments', mapping.impact(data, ['s-completion'])['affected_entries'])

    def test_reordering_rows_does_not_change_impact_scope(self):
        data = example()
        before = mapping.impact(data, ['s-course', 's-survey'])
        for group in ('sources', 'entries', 'outputs'):
            data[group].reverse()
        self.assertEqual(mapping.impact(data, ['s-survey', 's-course']), before)

    def test_unknown_fields_and_duplicate_ids_are_rejected_everywhere(self):
        locations = [lambda d: d, lambda d: d['sources'][0], lambda d: d['entries'][0],
                     lambda d: d['entries'][0]['assessments'],
                     lambda d: d['entries'][0]['assessments']['factual'],
                     lambda d: d['entries'][0]['methods'][0],
                     lambda d: d['entries'][3]['fields'][0],
                     lambda d: d['entries'][2]['target_review'], lambda d: d['outputs'][0]]
        for location in locations:
            data = example()
            location(data)['typo'] = 'must not disappear'
            with self.assertRaises(mapping.MappingError):
                mapping.validate_mapping(data)
        data = example(); data['entries'][0]['id'] = data['sources'][0]['id']
        with self.assertRaises(mapping.MappingError):
            mapping.validate_mapping(data)

    def test_invalid_refs_and_cycles_are_rejected_without_false_impact(self):
        for field in ('source_ids', 'depends_on'):
            data = example(); data['entries'][0][field] = ['absent']
            with self.assertRaises(mapping.MappingError):
                mapping.validate_mapping(data)
        data = example(); data['entries'][0]['depends_on'] = ['m-change']
        with self.assertRaisesRegex(mapping.MappingError, '循环'):
            mapping.validate_mapping(data)
        for changed in (['absent'], ['o-feedback'], [], ['s-course', 's-course']):
            with self.assertRaises(mapping.MappingError):
                mapping.impact(example(), changed)

    def test_supported_claim_requires_basis_but_not_formal_eligibility(self):
        data = example()
        data['entries'][0]['assessments']['factual']['status'] = 'supported'
        with self.assertRaises(mapping.MappingError):
            mapping.validate_mapping(data)
        data['entries'][0]['assessments']['factual']['basis'] = ['s-course']
        self.assertTrue(mapping.validate_mapping(data)['valid'])
        self.assertEqual(data['entries'][0]['assessments']['formal']['status'], 'not_claimed')

    def test_formal_transfer_review_does_not_upgrade_other_assessments(self):
        data = example()
        row = data['entries'][2]
        row['target_review'] = dict(requested=True, status='pending', basis=[], rationale='尚无目标侧记录')
        self.assertTrue(mapping.validate_mapping(data)['valid'])
        self.assertEqual(mapping.lookup(data, '响应')['matches'][0]['assessments']['factual']['status'], 'unknown')
        row['target_review']['status'] = 'reviewed'
        with self.assertRaises(mapping.MappingError):
            mapping.validate_mapping(data)

    def test_unmapped_domain_fact_can_remain_supported(self):
        data = example(); row = data['entries'][3]
        row['mapping_kind'] = 'unmapped'; row['target_meaning'] = None
        row['theory_anchors'] = []
        report = mapping.validate_mapping(data)
        self.assertTrue(report['valid'])
        self.assertEqual(mapping.lookup(data, '完成率')['matches'][0]['assessments']['factual']['status'], 'supported')

    def test_known_noncorrespondence_is_not_reported_as_unknown_target(self):
        for kind, expected in (('unmapped', '目标含义：无对应'),
                               ('not_applicable', '目标含义：不适用')):
            with self.subTest(kind=kind):
                data = example(); row = data['entries'][3]
                row['mapping_kind'] = kind
                row['target_meaning'] = None
                report = mapping.validate_mapping(data)
                self.assertNotIn('m-completion.target_meaning', report['unresolved_fields'])
                self.assertIn(expected, mapping.render_markdown(data))
                row['local_meaning'] = None
                self.assertIn('m-completion.local_meaning', mapping.validate_mapping(data)['unresolved_fields'])
                self.assertIn('当地含义：未知', mapping.render_markdown(data))
        data = example(); row = data['entries'][3]
        row['mapping_kind'] = 'unknown'; row['target_meaning'] = None
        self.assertIn('m-completion.target_meaning', mapping.validate_mapping(data)['unresolved_fields'])
        self.assertIn('目标含义：未知', mapping.render_markdown(data))

    def test_null_units_and_unknown_meanings_are_kept_without_defaults(self):
        data = example(); row = data['entries'][3]
        row['fields'][0]['denominator'] = None
        row['fields'][0]['time_window'] = None
        report = mapping.validate_mapping(data)
        self.assertIn('m-completion.fields.completion_rate.denominator', report['unresolved_fields'])
        rendered = mapping.render_markdown(data)
        self.assertIn('分母=未知', rendered)
        self.assertNotIn('分母=0', rendered)
        row['mapping_kind'] = 'unknown'; row['target_meaning'] = None
        self.assertTrue(mapping.validate_mapping(data)['valid'])

    def test_boolean_version_invalid_type_and_normalized_duplicate_are_rejected(self):
        for change in (lambda d: d.update(schema_version=True),
                       lambda d: d['entries'][0].update(terms=['Feedback', 'Ｆｅｅｄｂａｃｋ']),
                       lambda d: d['entries'][0].update(local_meaning=float('nan')),
                       lambda d: d['entries'][0].update(layer=['term']),
                       lambda d: d['entries'][0]['assessments']['semantic'].update(status=[])):
            data = example(); change(data)
            with self.assertRaises(mapping.MappingError):
                mapping.validate_mapping(data)

    def test_strict_json_rejects_duplicate_keys_nonfinite_numbers_and_oversize(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'bad.json'
            for text in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '{} trailing'):
                source.write_text(text, encoding='utf-8')
                with self.assertRaises(mapping.MappingError):
                    mapping.read_mapping(source)
            source.write_bytes(b' ' * (mapping.MAX_BYTES + 1))
            with self.assertRaises(mapping.MappingError):
                mapping.read_mapping(source)

    def test_theory_versions_and_anchor_existence_are_checked_without_requiring_mapping(self):
        data = example(); del data['theory_sha256']
        with self.assertRaises(mapping.MappingError):
            mapping.validate_mapping(data)
        data = example(); data['theory_sha256'] = '0' * 64
        with self.assertRaisesRegex(mapping.MappingError, '版本'):
            mapping.validate_mapping(data)
        data = example(); data['entries'][0]['theory_anchors'] = ['99.999']
        with self.assertRaisesRegex(mapping.MappingError, '不存在'):
            mapping.validate_mapping(data)
        data = example(); del data['theory_sha256']
        for row in data['entries']:
            row['theory_anchors'] = []
        self.assertTrue(mapping.validate_mapping(data)['valid'])

    def test_render_contains_authored_prose_and_all_limits_not_invented_results(self):
        data = example()
        rendered = mapping.render_markdown(data)
        for text in ('80%', '未给技能测验', '目标侧独立复核', '不补零', '尚不能确认按评语修改', '分母=', '来源范围'):
            self.assertIn(text, rendered)
        data['outputs'] = []
        self.assertIn('尚未提供成文', mapping.render_markdown(data))
        data['outputs'] = [dict(id='evil',title='<script>x</script>',text='[click](javascript:alert(1))',entry_ids=['m-comments'],source_ids=[])]
        rendered = mapping.render_markdown(data)
        self.assertNotIn('<script>', rendered)
        self.assertNotIn('[click]', rendered)


class OutputTests(unittest.TestCase):
    def test_output_is_atomic_and_existing_file_and_input_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'result.md'
            mapping.write_document('complete\n', output)
            self.assertEqual(output.read_text(), 'complete\n')
            with self.assertRaises(mapping.MappingError):
                mapping.write_document('replacement', output)
            self.assertEqual(output.read_text(), 'complete\n')
            self.assertEqual(list(Path(directory).iterdir()), [output])

    def test_existing_lock_is_preserved_and_temp_is_not_published(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'result.md'; lock = Path(str(output) + '.lock')
            lock.write_text('another writer')
            with self.assertRaises(mapping.MappingError):
                mapping.write_document('result', output)
            self.assertEqual(lock.read_text(), 'another writer')
            self.assertFalse(output.exists())
            self.assertEqual(list(Path(directory).iterdir()), [lock])

    def test_racing_external_file_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'result.md'
            original = mapping.os.link
            def race(source, destination):
                output.write_text('external writer')
                return original(source, destination)
            with mock.patch.object(mapping.os, 'link', side_effect=race):
                with self.assertRaises(mapping.MappingError):
                    mapping.write_document('ours', output)
            self.assertEqual(output.read_text(), 'external writer')
            self.assertEqual(list(Path(directory).iterdir()), [output])

    def test_write_failure_leaves_no_output_or_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'result.md'
            with mock.patch.object(mapping.os, 'link', side_effect=OSError('no hard-link support')):
                with self.assertRaises(OSError):
                    mapping.write_document('ours', output)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_install_path_and_symlink_into_install_are_rejected_before_write(self):
        with self.assertRaises(OSError):
            mapping.write_document('x', ROOT / 'must-not-write' / 'output.md')
        self.assertFalse((ROOT / 'must-not-write').exists())
        with tempfile.TemporaryDirectory() as directory:
            alias = Path(directory) / 'installed'
            try:
                alias.symlink_to(ROOT, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest('symlinks unavailable')
            with self.assertRaises(OSError):
                mapping.write_document('x', alias / 'must-not-write.md')
            self.assertFalse((ROOT / 'must-not-write.md').exists())

    def test_dangling_output_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'output.md'; target = Path(directory) / 'absent'
            try:
                output.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest('symlinks unavailable')
            with self.assertRaises(mapping.MappingError):
                mapping.write_document('x', output)
            self.assertFalse(target.exists())

    def test_cli_end_to_end_and_no_clobber(self):
        def run(source, *arguments):
            return subprocess.run([sys.executable, str(SCRIPT), '--mapping', str(source), *map(str, arguments)],
                                  capture_output=True, text=True, encoding='utf-8')
        self.assertTrue(json.loads(run(EXAMPLE, 'validate').stdout)['valid'])
        self.assertEqual(json.loads(run(EXAMPLE, 'lookup', '--term', '反馈').stdout)['status'], 'ambiguous')
        self.assertEqual(json.loads(run(EXAMPLE, 'impact', '--changed', 's-course').stdout)['unaffected_outputs'], ['o-completion'])
        self.assertNotEqual(run(EXAMPLE, 'impact', '--changed', 'missing').returncode, 0)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'mapping.json'; source.write_bytes(EXAMPLE.read_bytes())
            output = Path(directory) / 'mapping.md'
            result = run(source, 'render', '--output', output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('80%', output.read_text(encoding='utf-8'))
            before = output.read_bytes()
            self.assertNotEqual(run(source, 'render', '--output', output).returncode, 0)
            self.assertEqual(output.read_bytes(), before)
            before_source = source.read_bytes()
            self.assertNotEqual(run(source, 'render', '--output', source).returncode, 0)
            self.assertEqual(source.read_bytes(), before_source)


if __name__ == '__main__':
    unittest.main()
