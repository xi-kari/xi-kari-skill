"""Behavioral examples and failure cases for supplied domain mappings."""

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import time
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
        missing = mapping.lookup(example(), '反馈', '另一机构')
        self.assertEqual(missing['status'], 'context_not_found')
        self.assertEqual(missing['matches'], [])
        self.assertEqual(set(missing['context_options']), {'教师对作业的评语', '学习者对课程的问卷'})

    def test_common_word_with_a_narrow_registered_sense_needs_its_context(self):
        data = example()
        row = data['entries'][3]
        row['terms'] = ['完成率', '课程完成比例', '比例']
        row['context_required_terms'] = ['比例']
        mapping.validate_mapping(data)
        withheld = mapping.lookup(data, '比例')
        self.assertEqual(withheld['status'], 'context_required')
        self.assertEqual(withheld['matches'], [])
        self.assertEqual(withheld['context_required_entries'], [row['id']])
        self.assertEqual(withheld['context_options'], [row['context']])
        self.assertEqual([r['id'] for r in mapping.lookup(data, '比例', row['context'])['matches']], [row['id']])
        self.assertEqual(mapping.lookup(data, '比例', '另一机构的比例')['status'], 'context_not_found')
        self.assertEqual(mapping.lookup(data, '完成率')['status'], 'matched')
        self.assertEqual(mapping.lookup(data, '完成率')['context_required_entries'], [])
        # One context-dependent sense withholds every sense of the same word.
        data['entries'][0]['context_required_terms'] = ['反馈']
        both = mapping.lookup(data, '反馈')
        self.assertEqual((both['status'], both['matches']), ('context_required', []))
        self.assertEqual(both['context_required_entries'], ['m-comments'])
        self.assertEqual([r['id'] for r in mapping.lookup(data, '反馈', '学习者对课程的问卷')['matches']], ['m-survey'])
        self.assertIn('须给出语境才查询的词', mapping.render_markdown(data))
        for bad in ([], ['不在词表'], ['比例', '比例'], [1]):
            broken = copy.deepcopy(data)
            broken['entries'][3]['context_required_terms'] = bad
            with self.subTest(bad=bad), self.assertRaises(mapping.MappingError):
                mapping.validate_mapping(broken)

    def test_shipped_packs_withhold_common_words_until_context_is_given(self):
        for path in sorted((ROOT / 'assets/domains').glob('*.json')):
            data = json.loads(path.read_text(encoding='utf-8'))
            marked = [(row, term) for row in data['entries'] for term in row.get('context_required_terms', [])]
            self.assertTrue(marked, path.name)
            for row, term in marked:
                with self.subTest(pack=path.name, term=term):
                    self.assertEqual(mapping.lookup(data, term)['status'], 'context_required')
                    self.assertIn(row['id'], [r['id'] for r in mapping.lookup(data, term, row['context'])['matches']])

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
            self.assertEqual(result['context_options'], [])
        with self.assertRaises(mapping.MappingError):
            mapping.lookup(example(), ' ')
        with self.assertRaises(mapping.MappingError):
            mapping.lookup(example(), 'not-present', [])

    def test_exact_policy_preserves_protocol_spelling_symbols_and_context(self):
        data = example()
        row = data['entries'][0]
        row.update(terms=['GET', 'ℝ'], context='API / Foo', match_policy='exact')
        self.assertEqual([r['id'] for r in mapping.lookup(data, 'GET', 'API / Foo')['matches']], ['m-comments'])
        for query in ('get', 'ＧＥＴ', ' GET', 'R'):
            with self.subTest(query=query):
                self.assertEqual(mapping.lookup(data, query)['matches'], [])
        for context in ('API / foo', 'API  / Foo', 'API / Foo '):
            self.assertEqual(mapping.lookup(data, 'GET', context)['matches'], [])
        row['terms'].append('get')  # An explicitly supplied alias is permitted.
        self.assertEqual(mapping.lookup(data, 'get')['matches'], [row])
        row['match_policy'] = 'normalized'
        with self.assertRaises(mapping.MappingError):
            mapping.validate_mapping(data)

    def test_normalized_and_exact_hits_remain_ambiguous_without_precedence(self):
        data = example()
        data['entries'][0].update(terms=['GET'], match_policy='exact')
        data['entries'][1].update(terms=['get'], match_policy='normalized')
        found = mapping.lookup(data, 'GET')
        self.assertEqual(found['status'], 'ambiguous')
        self.assertEqual({r['id'] for r in found['matches']}, {'m-comments', 'm-survey'})
        self.assertEqual([r['id'] for r in mapping.lookup(data, 'get')['matches']], ['m-survey'])
        data['entries'][0]['match_policy'] = 'fuzzy'
        with self.assertRaises(mapping.MappingError):
            mapping.validate_mapping(data)

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

    def test_impact_matches_independent_fixed_point_on_branched_graphs(self):
        rng = random.Random(731)
        for iteration in range(8):
            data = example()
            source_ids = [row['id'] for row in data['sources']]
            template = data['entries'][0]
            data['entries'] = []
            expected_parents = {}
            for index in range(24):
                row = copy.deepcopy(template)
                identifier = f'n{index}'
                parents = rng.sample([f'n{i}' for i in range(index)], min(index, rng.randrange(4)))
                source = rng.choice(source_ids)
                row.update(id=identifier, terms=[identifier], source_ids=[source], depends_on=parents,
                           theory_anchors=[], methods=[], fields=[])
                for assessment in row['assessments'].values():
                    assessment.update(status='not_claimed', basis=[])
                data['entries'].append(row)
                expected_parents[identifier] = set(parents) | {source}
            data['outputs'] = []
            for index in range(6):
                entry_ids = rng.sample([row['id'] for row in data['entries']], 2)
                source = rng.choice(source_ids)
                row = dict(id=f'o{index}', title='结果', text='有明确依赖的结果', entry_ids=entry_ids, source_ids=[source])
                data['outputs'].append(row)
                expected_parents[row['id']] = set(entry_ids) | {source}
            changed = [rng.choice(source_ids), f'n{rng.randrange(24)}']
            reachable = set(changed)
            while True:
                expanded = reachable | {node for node, parents in expected_parents.items() if parents & reachable}
                if expanded == reachable:
                    break
                reachable = expanded
            rng.shuffle(data['entries'])
            result = mapping.impact(data, changed)
            with self.subTest(iteration=iteration):
                self.assertEqual(set(result['affected_entries']), reachable & {r['id'] for r in data['entries']})
                self.assertEqual(set(result['affected_outputs']), reachable & {r['id'] for r in data['outputs']})
                for node, path in result['paths'].items():
                    self.assertIn(path[0], changed)
                    self.assertEqual(path[-1], node)
                    self.assertTrue(all(parent in expected_parents[child] for parent, child in zip(path, path[1:])))

    def test_long_dependencies_and_a_long_cycle_do_not_depend_on_python_recursion(self):
        data = example(); template = data['entries'][0]
        data['entries'] = []
        for index in range(1100):
            row = copy.deepcopy(template)
            row.update(id=f'n{index}', terms=[f'term{index}'], source_ids=['s-course'],
                       depends_on=[] if index == 0 else [f'n{index-1}'], theory_anchors=[], methods=[])
            data['entries'].append(row)
        data['outputs'] = [dict(id='final', title='终点', text='保留全部依赖', entry_ids=['n1099'], source_ids=[])]
        result = mapping.impact(data, ['n0'])
        self.assertEqual(len(result['affected_entries']), 1100)
        self.assertEqual(result['affected_outputs'], ['final'])
        self.assertEqual(len(result['paths']['final']), 1101)
        data['entries'][0]['depends_on'] = ['n1099']
        with self.assertRaisesRegex(mapping.MappingError, '循环'):
            mapping.validate_mapping(data)

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
        for changed in (['absent'], [], ['s-course', 's-course']):
            with self.assertRaises(mapping.MappingError):
                mapping.impact(example(), changed)

    def test_a_corrected_output_is_itself_the_review_scope(self):
        result = mapping.impact(example(), ['o-feedback'])
        self.assertEqual(result['affected_entries'], [])
        self.assertEqual(result['affected_outputs'], ['o-feedback'])
        self.assertEqual(result['unaffected_outputs'], ['o-completion', 'o-response'])
        self.assertEqual(result['paths'], {'o-feedback': ['o-feedback']})

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

    def test_candidate_meanings_and_pending_review_remain_unresolved(self):
        data = example(); row = data['entries'][0]
        row['mapping_kind'] = 'unknown'
        for assessment in row['assessments'].values():
            assessment['status'] = 'not_claimed'
        row['target_review'] = dict(requested=True, status='pending', basis=[], rationale='尚待目标侧核对')
        unresolved = mapping.validate_mapping(data)['unresolved_fields']
        for field in ('mapping_kind', 'unknowns', 'target_review'):
            self.assertIn(f"{row['id']}.{field}", unresolved)
        self.assertNotIn(f"{row['id']}.local_meaning", unresolved)
        self.assertNotIn(f"{row['id']}.target_meaning", unresolved)

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

    def test_cli_snapshot_digest_binds_original_bytes_including_bom_and_line_endings(self):
        content = json.dumps(example(), ensure_ascii=False, indent=2)
        payloads = [content.encode('utf-8'), b'\xef\xbb\xbf' + (content.replace('\n', '\r\n') + '\r\n').encode('utf-8')]
        digests = []
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'snapshot.json'
            for payload in payloads:
                source.write_bytes(payload)
                result = subprocess.run([sys.executable, str(SCRIPT), '--mapping', str(source), 'validate'],
                                        capture_output=True, text=True, encoding='utf-8', timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)
                digest = report['snapshot_sha256']
                self.assertEqual(digest, hashlib.sha256(payload).hexdigest())
                self.assertEqual(report['id'], example()['id'])
                self.assertEqual(mapping.read_mapping(source), example())
                digests.append(digest)
        self.assertNotEqual(*digests)

    def test_unpaired_unicode_and_excessive_json_nesting_fail_before_output(self):
        data = example()
        data['entries'][0]['local_meaning'] = '\ud800'
        with self.assertRaisesRegex(mapping.MappingError, 'Unicode'):
            mapping.validate_mapping(data)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'bad.json'
            for text in (json.dumps(data), '[' * 2000 + '0' + ']' * 2000):
                source.write_text(text, encoding='utf-8')
                result = subprocess.run([sys.executable, str(SCRIPT), '--mapping', str(source), 'validate'],
                                        capture_output=True, text=True, encoding='utf-8', timeout=15)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')
                self.assertNotIn('Traceback', result.stderr)

    def test_large_path_expansion_fails_without_partial_cli_json(self):
        data = example(); template = data['entries'][0]
        data['entries'] = []; data['outputs'] = []
        identifiers = [f'n{index:04d}_' + 'x' * 90 for index in range(1000)]
        for index, identifier in enumerate(identifiers):
            row = copy.deepcopy(template)
            row.update(id=identifier, terms=[f't{index}'], theory_anchors=[], methods=[],
                       depends_on=[] if index == 0 else [identifiers[index-1]])
            data['entries'].append(row)
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.assertLess(len(payload), mapping.MAX_BYTES)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'large.json'
            source.write_bytes(payload)
            result = subprocess.run([sys.executable, str(SCRIPT), '--mapping', str(source),
                                     'impact', '--changed', identifiers[0]],
                                    capture_output=True, text=True, encoding='utf-8', timeout=20)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            self.assertIn('输出超过', result.stderr)
            self.assertNotIn('Traceback', result.stderr)

    def test_theory_versions_and_anchor_existence_are_checked_without_requiring_mapping(self):
        data = example(); del data['theory_sha256']
        with self.assertRaises(mapping.MappingError):
            mapping.validate_mapping(data)
        data = example()
        self.assertEqual(mapping.validate_mapping(data)['theory_status'], 'current')
        self.assertEqual(mapping.validate_mapping(data)['warnings'], [])
        data['entries'][0]['theory_anchors'] = ['99.999']
        with self.assertRaisesRegex(mapping.MappingError, '不存在'):
            mapping.validate_mapping(data)
        data = example(); del data['theory_sha256']
        for row in data['entries']:
            row['theory_anchors'] = []
        result = mapping.validate_mapping(data)
        self.assertTrue(result['valid'])
        self.assertEqual(result['theory_status'], 'not_bound')

    def test_explicit_theory_binding_is_checked_even_without_anchors(self):
        data = example()
        for row in data['entries']:
            row['theory_anchors'] = []
        self.assertTrue(mapping.validate_mapping(data)['valid'])
        data['theory_sha256'] = '0' * 63
        with self.assertRaisesRegex(mapping.MappingError, 'SHA-256'):
            mapping.validate_mapping(data)

    def test_snapshot_bound_to_an_earlier_theory_stays_queryable_and_traceable(self):
        data = example()
        data['theory_sha256'] = '0' * 64
        data['entries'][0]['theory_anchors'] = ['99.999']
        report = mapping.validate_mapping(data)
        self.assertTrue(report['valid'])
        self.assertEqual(report['theory_status'], 'other_version')
        self.assertTrue(any('未对当前原文复核' in warning for warning in report['warnings']))
        found = mapping.lookup(data, '反馈', '学习者对课程的问卷')
        self.assertEqual([row['id'] for row in found['matches']], ['m-survey'])
        self.assertEqual(found['theory_status'], 'other_version')
        traced = mapping.impact(data, ['s-course'])
        self.assertTrue(traced['affected_entries'])
        self.assertEqual(traced['warnings'], report['warnings'])
        self.assertIn('理论版本提示', mapping.render_markdown(data))
        previous = next(iter(mapping.theory_reference()['previous']), None)
        if previous:
            data['theory_sha256'] = previous
            self.assertEqual(mapping.validate_mapping(data)['theory_status'], 'previous_version')

    def test_shipped_mappings_are_bound_to_the_current_theory(self):
        for path in [EXAMPLE, *sorted((ROOT / 'assets/domains').glob('*.json'))]:
            with self.subTest(path=path.name):
                report = mapping.validate_mapping(json.loads(path.read_text(encoding='utf-8-sig')))
                self.assertEqual(report['theory_status'], 'current',
                                 'update the shipped mapping after reviewing the changed theory text')

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

    def test_authored_domain_result_precedes_mapping_apparatus(self):
        data = example()
        text = mapping.render_markdown(data)
        result_index = text.index('## 已写成的领域表述')
        source_index = text.index('## 来源范围')
        self.assertLess(result_index, source_index)
        self.assertLess(text.index(data['outputs'][0]['text']), source_index)
        self.assertLess(source_index, text.index('## 对应、区别与证据'))
        self.assertIn('词与语境匹配策略：规范化匹配', text)
        data['outputs'] = []
        text = mapping.render_markdown(data)
        self.assertLess(text.index('尚未提供成文'), text.index('## 来源范围'))


class LanguageTests(unittest.TestCase):
    def test_chinese_render_names_fixed_values_in_chinese(self):
        text = mapping.render_markdown(example())
        for raw in ('对应类型：partial', '层次：term', '层次：measurement', '：partial**', '：unknown**',
                    '：not_claimed**', '（synthetic）', '（planned）', '复核：not_requested'):
            self.assertNotIn(raw, text)
        for label in ('对应类型：部分对应', '层次：测量', '**语义对应：部分支持**', '**正式实例资格：未申请**',
                      '（合成材料）', '（计划中）', '目标侧独立复核：未申请'):
            self.assertIn(label, text)

    def test_english_render_has_english_fixed_labels_and_keeps_authored_text(self):
        data = example()
        text = mapping.render_markdown(data, 'en')
        for label in ('# Domain mapping and how to use it', '## Domain statements already written',
                      '## Sources and their scope', '## Correspondences, distinctions and evidence',
                      'kind of correspondence: partial correspondence', '**Semantic correspondence: partly supported.**',
                      '**Formal-instance eligibility: not claimed.**', 'denominator=', 'Independent review on the target side'):
            self.assertIn(label, text)
        for fixed in ('# 领域映射与使用说明', '## 已写成的领域表述', '## 来源范围', '对应类型：', '当地含义：', '目标侧独立复核：', '依据：'):
            self.assertNotIn(fixed, text)
        self.assertIn(data['outputs'][0]['text'], text)
        data['entries'][3]['fields'][0]['denominator'] = None
        self.assertIn('denominator=unknown (not supplied', mapping.render_markdown(data, 'en'))
        data['theory_sha256'] = '0' * 64
        self.assertIn('Theory version notice', mapping.render_markdown(data, 'en'))
        with self.assertRaises(mapping.MappingError):
            mapping.render_markdown(data, 'fr')


    def test_embedded_chapter_is_the_same_content_one_level_down(self):
        data = example()
        for lang, title in (('zh', '领域映射与使用说明'), ('en', 'Domain mapping and how to use it')):
            with self.subTest(lang=lang):
                standalone = mapping.render_markdown(data, lang)
                chapter = mapping.render_markdown(data, lang, embed=True)
                self.assertTrue(standalone.startswith(f'# {title}\n'))
                self.assertTrue(chapter.startswith(f'## {title}\n'))
                self.assertNotIn('<!--', standalone + chapter)
                shifted = ['#' + line if line.startswith('#') else line for line in standalone.splitlines()]
                self.assertEqual(chapter.splitlines(), shifted)
                self.assertFalse([line for line in chapter.splitlines() if line.startswith('# ')])

    def test_authored_hashes_cannot_become_headings_in_the_chapter(self):
        data = example()
        data['outputs'][0]['text'] = '# 作者正文里的井号\n## 第二行'
        chapter = mapping.render_markdown(data, embed=True)
        self.assertIn('\\# 作者正文里的井号', chapter)
        self.assertNotIn('\n## 第二行', chapter)


class OutputTests(unittest.TestCase):
    def test_output_budget_is_utf8_bytes_and_precedes_directory_creation(self):
        with mock.patch.object(mapping, 'MAX_OUTPUT_BYTES', 6):
            self.assertEqual(mapping._bounded_join(['甲', '乙']), '甲乙')
            with self.assertRaises(mapping.MappingError):
                mapping._bounded_join(['甲', '乙'], '\n')
            with self.assertRaises(mapping.MappingError):
                mapping._json_output({'内容': '甲'})
            with self.assertRaises(mapping.MappingError):
                mapping.render_markdown(example())
            with tempfile.TemporaryDirectory() as directory:
                parent = Path(directory) / 'not-created'
                with self.assertRaises(mapping.MappingError):
                    mapping.write_document('甲乙丙', parent / 'result.md')
                self.assertFalse(parent.exists())

    def test_real_concurrent_processes_publish_one_complete_document(self):
        program = '''
import importlib.util
from pathlib import Path
import sys
import time
spec = importlib.util.spec_from_file_location('domain_mapping_writer', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
output, gate, ready = map(Path, sys.argv[2:5])
ready.write_text('ready', encoding='utf-8')
deadline = time.monotonic() + 15
while not gate.exists():
    if time.monotonic() >= deadline:
        raise SystemExit(9)
    time.sleep(0.01)
try:
    module.write_document(sys.argv[5] * 10000, output)
except (module.MappingError, OSError):
    raise SystemExit(2)
'''
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory); output = work / 'result.md'; gate = work / 'go'
            processes = []
            messages = [f'完整文档-{index}\n' for index in range(4)]
            try:
                for index, message in enumerate(messages):
                    process = subprocess.Popen([sys.executable, '-c', program, str(SCRIPT), str(output),
                                                str(gate), str(work / f'ready-{index}'), message],
                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    processes.append(process)
                deadline = time.monotonic() + 15
                while len(list(work.glob('ready-*'))) != len(processes):
                    self.assertLess(time.monotonic(), deadline, 'Writers did not become ready')
                    time.sleep(0.01)
                gate.touch()
                statuses = []
                for process in processes:
                    _, stderr = process.communicate(timeout=15)
                    self.assertEqual(stderr, b'')
                    statuses.append(process.returncode)
                self.assertEqual(sorted(statuses), [0, 2, 2, 2])
                self.assertIn(output.read_text(encoding='utf-8'), [message * 10000 for message in messages])
                self.assertFalse(output.with_name(output.name + '.lock').exists())
                self.assertEqual(list(work.glob('.domain-mapping-*.tmp')), [])
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.kill()
                    process.communicate()

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
            chapter = Path(directory) / 'chapter.md'
            result = run(source, 'render', '--embed', '--lang', 'en', '--output', chapter)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)['notice'].startswith('This tool checks only'))
            self.assertTrue(chapter.read_text(encoding='utf-8').startswith('## Domain mapping and how to use it\n'))


if __name__ == '__main__':
    unittest.main()
