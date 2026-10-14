import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'comparison.py'


def module():
    spec = importlib.util.spec_from_file_location('comparison', SCRIPT)
    target = importlib.util.module_from_spec(spec)
    sys.modules['comparison'] = target
    spec.loader.exec_module(target)
    return target


def model():
    return {
        'schema_version': 1,
        'title': '虚构复核方案比较',
        'purpose': '比较三种安排，演示依据身份如何保留。',
        'fictional': True,
        'assumptions': ['全部数值为教学设定'],
        'boundaries': ['本表不判断方案价值'],
        'candidates': [
            {'id': 'auto', 'label': '完全自动排序'},
            {'id': 'manual', 'label': '人工复核'},
            {'id': 'hybrid', 'label': '混合规则'},
        ],
        'dimensions': [
            {'id': 'hours', 'label': '额外工时', 'direction': 'lower_is_better', 'unit': '工时'},
            {'id': 'reversible', 'label': '可逆性', 'direction': 'not_orderable'},
        ],
        'cells': {
            'auto': {'hours': {'value': 0, 'basis': 'assumed', 'note': '教学设定'},
                     'reversible': {'value': '低', 'basis': 'assumed'}},
            'manual': {'hours': {'value': 12, 'basis': 'assumed'},
                       'reversible': {'value': '高', 'basis': 'assumed'}},
            'hybrid': {'hours': {'value': None, 'basis': 'unknown', 'note': '尚无可靠估计'},
                       'reversible': {'value': '中', 'basis': 'assumed'}},
        },
    }


class ComparisonTests(unittest.TestCase):
    def test_unknown_is_never_ranked_and_stays_marked(self):
        result = module().build_comparison(model())
        direction = next(item for item in result['dimensions'] if item['id'] == 'hours')
        ranked = [candidate['id'] for candidate in direction['ranking']]
        self.assertNotIn('hybrid', ranked)
        self.assertIn('hybrid', [item['id'] for item in direction['unranked']])
        hybrid = next(item for item in direction['unranked'] if item['id'] == 'hybrid')
        self.assertEqual(hybrid['reason'], 'unknown')

    def test_assumed_cells_are_marked_in_every_format(self):
        result = module().build_comparison(model())
        self.assertTrue(result['cells_have_assumed'])
        markdown = module().render_markdown(result)
        self.assertIn('假设', markdown)
        payload = json.loads(module().render_json(result))
        auto = next(row for row in payload['rows'] if row['candidate'] == 'auto')
        self.assertEqual(auto['values']['hours']['basis'], 'assumed')

    def test_not_orderable_dimension_produces_no_ranking(self):
        result = module().build_comparison(model())
        reversible = next(item for item in result['dimensions'] if item['id'] == 'reversible')
        self.assertNotIn('ranking', reversible)
        self.assertIn('not_orderable', reversible['reason'])

    def test_no_overall_best_is_asserted(self):
        result = module().build_comparison(model())
        self.assertNotIn('best', result)
        self.assertNotIn('winner', result)
        markdown = module().render_markdown(result)
        self.assertIn('不判断方案价值', markdown)

    def test_markdown_columns_match_candidates(self):
        result = module().build_comparison(model())
        markdown = module().render_markdown(result)
        header = next(line for line in markdown.splitlines() if line.startswith('|'))
        self.assertEqual(header.count('|'), len(model()['candidates']) + 2)

    def test_html_has_no_external_resource_reference(self):
        result = module().build_comparison(model())
        document = module().render_html(result)
        self.assertNotIn('http://', document.replace('http://www.w3.org', ''))
        self.assertNotIn('https://', document)
        self.assertNotIn('<link', document)
        self.assertNotIn('src=', document)

    def test_invalid_models_are_refused_on_specific_grounds(self):
        validate = module().validate_comparison
        broken = model(); broken['candidates'] = [{'id': 'a'}]
        with self.assertRaises(ValueError): validate(broken)
        broken = model(); broken['cells']['auto']['hours'] = {'value': 1}
        with self.assertRaises(ValueError): validate(broken)
        broken = model(); broken['dimensions'][0]['direction'] = 'bigger'
        with self.assertRaises(ValueError): validate(broken)
        broken = model(); broken['candidates'] = [{'id': 'x', 'label': '甲'}, {'id': 'x', 'label': '乙'}]
        with self.assertRaises(ValueError): validate(broken)
        broken = model(); broken['cells']['ghost'] = {'hours': {'value': 1, 'basis': 'assumed'}}
        with self.assertRaises(ValueError): validate(broken)

    def test_missing_basis_is_not_defaulted(self):
        broken = model()
        broken['cells']['auto']['hours'] = {'value': 0}
        with self.assertRaises(ValueError):
            module().validate_comparison(broken)

    def test_outputs_are_written_outside_the_install_tree_only(self):
        target = module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'model.json'
            source.write_text(json.dumps(model(), ensure_ascii=False), encoding='utf-8')
            out = root / 'out'
            written = target.write_outputs(target.build_comparison(model()), source, out)
            self.assertEqual(set(written), {'json', 'md', 'html'})
            for path in written.values():
                self.assertTrue(Path(path).exists())
            with self.assertRaises(OSError):
                target.write_outputs(target.build_comparison(model()), source, ROOT / 'scripts' / 'nope')

    def test_cli_writes_all_formats_and_refuses_the_install_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'model.json'
            source.write_text(json.dumps(model(), ensure_ascii=False), encoding='utf-8')
            out = root / 'out'
            result = subprocess.run([sys.executable, str(SCRIPT), str(source), '--output', str(out)],
                                    capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary['candidates'], 3)
            self.assertTrue((out / 'comparison-table.html').exists())
            refused = subprocess.run([sys.executable, str(SCRIPT), str(source), '--output', str(ROOT / 'scripts' / 'refused')],
                                     capture_output=True, text=True, encoding='utf-8')
            self.assertNotEqual(refused.returncode, 0)


if __name__ == '__main__':
    unittest.main()
