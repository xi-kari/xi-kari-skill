"""Cross-file revision cases, independent of either tool's graph implementation."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('bridge_research', ROOT / 'scripts/research.py')
research = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(research)


class MappingResearchBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.mapping_path = Path(self.temp.name) / 'mapping.json'
        self.mapping = json.loads((ROOT / 'assets/examples/domain-mapping.json').read_text(encoding='utf-8'))
        self.mapping_path.write_text(json.dumps(self.mapping, ensure_ascii=False), encoding='utf-8')
        self.digest = hashlib.sha256(self.mapping_path.read_bytes()).hexdigest()
        self.data = {
            'schema_version': 1, 'title': '评语、调整与完成记录的独立使用',
            'question': '评语来源更正影响哪些判断？', 'scope': '合成修订测试',
            'method': '区分三个来源及其实际使用范围。',
            'summary': '保留独立统计；评语改变只触发依赖它的研究。',
            'summary_refs': ['F-action', 'F-independent'],
            'inputs': [self.mapping_input('M-response', ['o-response']),
                       self.mapping_input('M-completion', ['o-completion']),
                       {'id': 'S-local', 'kind': 'source', 'label': '独立登记',
                        'content': '本地只登记20人，未使用评语来源。', 'locator': 'fixture/local', 'status': 'synthetic'}],
            'findings': [self.finding('F-response', ['M-response']),
                         self.finding('F-action', ['F-response']),
                         self.finding('F-completion', ['M-completion']),
                         self.finding('F-independent', ['S-local'])],
            'issues': [{'id': 'I-response', 'title': '实际调整记录不足', 'categories': ['material_gap'],
                        'affected_findings': ['F-response'], 'materiality': 'major', 'status': 'open',
                        'current_work': '已比较评语与调整记录。', 'why_unresolved': '缺少执行记录。',
                        'consequence': '不能仅由评语判断已调整。', 'next_work': '取得执行记录。',
                        'status_reason': '记录未取得。', 'resolution_scope': ''}],
            'issue_assessment': '只追踪当前声明的依赖。',
        }

    def mapping_input(self, identifier, nodes):
        return {'id': identifier, 'kind': 'mapping', 'label': identifier,
                'content': '使用所列节点的具体领域区别，不将其当现实效果。',
                'locator': 'mapping.json', 'status': 'synthetic',
                'mapping_ref': {'id': self.mapping['id'], 'version': self.mapping['version'],
                                'sha256': self.digest, 'node_ids': nodes}}

    @staticmethod
    def finding(identifier, dependencies):
        return {'id': identifier, 'title': identifier, 'kind': 'interpretive', 'status': 'proposed',
                'body': '依声明材料保留当前局部判断；来源变更后实际重新论证。',
                'depends_on': dependencies, 'limitations': [], 'change_conditions': ['所据来源改变。']}

    def run_bridge(self, *changed):
        return research.impact_mapping(self.data, self.mapping_path, list(changed))

    def test_source_to_entry_to_output_to_research_summary_and_issue(self):
        before = copy.deepcopy(self.data)
        result = self.run_bridge('s-course')
        self.assertEqual(result['affected_mapping_inputs'], ['M-response'])
        self.assertEqual(result['affected_findings'], ['F-response', 'F-action'])
        self.assertEqual(result['independent_findings'], ['F-completion', 'F-independent'])
        self.assertEqual(result['affected_issues'], ['I-response'])
        self.assertTrue(result['summary_needs_review'])
        self.assertEqual(result['paths']['F-action'], ['M-response', 'F-response', 'F-action'])
        self.assertEqual(result['mapping_paths']['o-response'][0], 's-course')
        self.assertEqual(result['mapping_paths']['o-response'][-1], 'o-response')
        self.assertEqual(self.data, before, 'Tracing must not silently revise prose or statuses')

    def test_multiple_changes_union_without_touching_independent_source(self):
        result = self.run_bridge('s-course', 's-completion')
        self.assertEqual(set(result['affected_findings']), {'F-response', 'F-action', 'F-completion'})
        self.assertEqual(result['independent_findings'], ['F-independent'])

    def test_valid_unrelated_change_is_distinct_from_missing_binding(self):
        result = self.run_bridge('s-survey')
        self.assertEqual(result['affected_findings'], [])
        self.assertEqual(result['verified_mapping_inputs'], ['M-response', 'M-completion'])
        self.assertFalse(result['summary_needs_review'])
        for row in self.data['inputs'][:2]:
            del row['mapping_ref']
        with self.assertRaisesRegex(research.ResearchError, '没有.*匹配'):
            self.run_bridge('s-survey')

    def test_wrong_pack_version_digest_or_node_never_becomes_empty_success(self):
        original = copy.deepcopy(self.data)
        for field, value in [('id', 'other-pack'), ('version', '2.0'),
                             ('sha256', '0' * 64), ('node_ids', ['missing-node'])]:
            with self.subTest(field=field):
                self.data = copy.deepcopy(original)
                for row in self.data['inputs'][:2]:
                    row['mapping_ref'][field] = value
                with self.assertRaises(research.ResearchError):
                    self.run_bridge('s-course')

    def test_reformatted_or_corrected_file_requires_the_original_snapshot(self):
        raw = self.mapping_path.read_bytes()
        self.mapping_path.write_bytes(raw + b'\n')
        with self.assertRaisesRegex(research.ResearchError, 'SHA-256'):
            self.run_bridge('s-course')
        self.mapping_path.write_bytes(raw)
        self.assertEqual(self.run_bridge('s-course')['affected_findings'], ['F-response', 'F-action'])

    def test_unbound_mapping_descendants_are_unassessed_not_independent(self):
        unbound = self.mapping_input('M-manual', ['m-comments'])
        del unbound['mapping_ref']
        self.data['inputs'].append(unbound)
        self.data['findings'].append(self.finding('F-manual', ['M-manual']))
        self.data['findings'].append(self.finding('F-manual-later', ['F-manual']))
        self.data['summary_refs'].append('F-manual-later')
        result = self.run_bridge('s-course')
        self.assertEqual(result['unverified_mapping_inputs'], ['M-manual'])
        self.assertEqual(result['unassessed_findings'], ['F-manual', 'F-manual-later'])
        self.assertTrue(result['summary_has_unassessed_dependencies'])
        self.assertNotIn('F-manual-later', result['independent_findings'])

    def test_other_pack_and_other_snapshot_do_not_bind_by_shared_node_name(self):
        for field, value in [('id', 'unrelated-pack'), ('version', '2.0')]:
            with self.subTest(field=field):
                other = self.data['inputs'][1]['mapping_ref']
                saved = copy.deepcopy(other)
                other[field] = value
                other['node_ids'] = ['o-response']
                result = self.run_bridge('s-course')
                self.assertEqual(result['affected_findings'], ['F-response', 'F-action'])
                self.assertEqual(result['unassessed_findings'], ['F-completion'])
                self.assertEqual(result['independent_findings'], ['F-independent'])
                self.data['inputs'][1]['mapping_ref'] = saved

    def test_research_ids_do_not_implicitly_match_mapping_ids(self):
        self.data['inputs'][2]['id'] = 's-course'
        self.data['findings'][3]['depends_on'] = ['s-course']
        self.assertIn('F-independent', self.run_bridge('s-course')['independent_findings'])

    def test_direct_source_and_entry_bindings_are_supported(self):
        self.data['inputs'][0]['mapping_ref']['node_ids'] = ['s-course']
        self.data['inputs'][1]['mapping_ref']['node_ids'] = ['m-change']
        result = self.run_bridge('s-course')
        self.assertEqual(set(result['affected_findings']), {'F-response', 'F-action', 'F-completion'})

    def test_a_corrected_mapping_output_reaches_the_research_that_cites_it(self):
        result = self.run_bridge('o-completion')
        self.assertEqual(result['changed_mapping_nodes'], ['o-completion'])
        self.assertEqual(result['affected_mapping_inputs'], ['M-completion'])
        self.assertEqual(result['matched_mapping_nodes'], {'M-completion': ['o-completion']})
        self.assertNotIn('M-response', result['affected_mapping_inputs'])
        self.assertTrue(result['affected_findings'])

    def newer_snapshot(self, change):
        newer = copy.deepcopy(self.mapping)
        change(newer)
        path = Path(self.temp.name) / 'mapping-new.json'
        path.write_text(json.dumps(newer, ensure_ascii=False, indent=1), encoding='utf-8')
        return path

    def test_newer_snapshot_supplies_the_changed_nodes(self):
        def correct_course(newer):
            newer['sources'][0]['scope'] = '更正后的范围：只支持评语已经发出。'
        newer = self.newer_snapshot(correct_course)
        derived = research.impact_mapping(self.data, self.mapping_path, against=newer)
        explicit = self.run_bridge('s-course')
        self.assertEqual(derived['mapping_diff']['changed_nodes'], ['s-course'])
        self.assertEqual(derived['mapping_diff']['groups']['sources']['modified'], {'s-course': ['scope']})
        for key in ('affected_findings', 'independent_findings', 'affected_issues', 'summary_needs_review'):
            self.assertEqual(derived[key], explicit[key], key)
        self.assertIsNone(explicit['mapping_diff'])

    def test_reformatted_or_added_only_snapshot_changes_no_finding(self):
        def add_entry(newer):
            extra = copy.deepcopy(newer['entries'][3])
            extra['id'] = 'm-new'
            extra['terms'] = ['新增条目']
            newer['entries'].append(extra)
        newer = self.newer_snapshot(add_entry)
        result = research.impact_mapping(self.data, self.mapping_path, against=newer)
        self.assertEqual(result['mapping_diff']['changed_nodes'], [])
        self.assertEqual(result['mapping_diff']['added_nodes'], ['m-new'])
        self.assertEqual(result['affected_findings'], [])
        self.assertEqual(result['verified_mapping_inputs'], ['M-response', 'M-completion'])
        with self.assertRaisesRegex(research.ResearchError, '二选一'):
            research.impact_mapping(self.data, self.mapping_path, ['s-course'], against=newer)
        with self.assertRaises(research.ResearchError):
            research.impact_mapping(self.data, self.mapping_path, [])

    def test_diff_reports_records_not_bytes_and_refuses_another_pack(self):
        mapping = research.domain_mapping
        same = mapping.diff_mappings(self.mapping, copy.deepcopy(self.mapping), 'a', 'b')
        self.assertTrue(same['content_identical'])
        self.assertFalse(same['bytes_identical'])
        self.assertEqual((same['changed_nodes'], same['added_nodes'], same['old_impact']), ([], [], None))
        newer = copy.deepcopy(self.mapping)
        newer['entries'].reverse()
        self.assertEqual(mapping.diff_mappings(self.mapping, newer)['changed_nodes'], [])
        del newer['outputs'][0]
        newer['scope'] = '新范围'
        changed = mapping.diff_mappings(self.mapping, newer)
        self.assertEqual(changed['groups']['outputs']['removed'], ['o-feedback'])
        self.assertEqual(changed['pack_fields_changed'], ['scope'])
        self.assertEqual(changed['old_impact']['affected_outputs'], ['o-feedback'])
        other = copy.deepcopy(self.mapping)
        other['id'] = 'another-pack'
        with self.assertRaises(mapping.MappingError):
            mapping.diff_mappings(self.mapping, other)

    def test_unknown_changed_node_is_an_error_and_does_not_edit_input(self):
        before = copy.deepcopy(self.data)
        with self.assertRaises(ValueError):
            self.run_bridge('typo-source')
        self.assertEqual(self.data, before)

    def test_binding_structure_is_checked_without_opening_locator(self):
        original = copy.deepcopy(self.data)
        for change in [lambda d: d['inputs'][0].update(kind='source'),
                       lambda d: d['inputs'][0]['mapping_ref'].update(node_ids=[]),
                       lambda d: d['inputs'][0]['mapping_ref'].update(sha256='bad'),
                       lambda d: d['inputs'][0]['mapping_ref'].update(node_ids=[1]),
                       lambda d: d['inputs'][0]['mapping_ref'].update(extra='unsupported')]:
            with self.subTest(change=change):
                data = copy.deepcopy(original)
                change(data)
                with self.assertRaises(research.ResearchError):
                    research.validate_research(data)
        self.data['inputs'][0]['locator'] = 'https://unavailable.invalid/not-opened'
        report = research.validate_research(self.data)
        self.assertEqual(report['unverified_mapping_inputs'], ['M-response', 'M-completion'])

    def test_render_does_not_claim_bindings_were_verified(self):
        del self.data['inputs'][1]['mapping_ref']
        report = research.render_documents(self.data)['research-report.md']
        self.assertIn(self.digest, report)
        self.assertEqual(report.count('仅展示作者绑定'), 1)
        self.assertIn('未绑定可自动追踪', report)


if __name__ == '__main__':
    unittest.main()
