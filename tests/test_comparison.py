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


def wide_model():
    """Five options on one scale: a tie, two close values, one unknown, one stated fact."""
    data = model()
    data['candidates'] = [{'id': name, 'label': label} for name, label in
                          (('a', '甲'), ('b', '乙'), ('c', '丙'), ('d', '丁'), ('e', '戊'))]
    data['dimensions'] = [{'id': 'cost', 'label': '成本', 'direction': 'lower_is_better', 'unit': '万元'}]
    values = {'a': (0, 'observed'), 'b': (40, 'assumed'), 'c': (10, 'assumed'), 'd': (None, 'unknown'), 'e': (0, 'assumed')}
    data['cells'] = {name: {'cost': {'value': value, 'basis': basis, **({'source': '账目'} if basis == 'observed' else {})}}
                     for name, (value, basis) in values.items()}
    return data


class ComparisonPageTests(unittest.TestCase):
    def page(self, data=None, lang='zh'):
        target = module()
        return target, target.render_html(target.build_comparison(data or model(), lang))

    def test_plate_carries_the_key_and_the_boundary_and_says_each_fact_once(self):
        target, page = self.page()
        self.assertIn('<span class="page-kind">方案比较</span><span class="page-sheet">xikari-comparison-1</span>', page)
        plate = page[page.index('<section class="plate cmp-plate"'):page.index('<section class="cmp-section"')]
        for kind in ('observed', 'assumed', 'unknown'):
            self.assertIn(f'<dt><span class="basis basis-{kind}">', plate)
        self.assertIn(f'<p class="boundary">{target.BOUNDARY}</p>', plate)
        self.assertEqual(page.count('教学虚构'), 1)
        self.assertEqual(page.count('取值不是现实事实'), 1)
        self.assertNotIn('共 3 个方案', page)
        self.assertNotIn('legend-heading', page)
        _, provided = self.page({**model(), 'fictional': False})
        self.assertIn('<span class="basis basis-observed">作者提供</span><span class="strip-aside">来源与假设需分别判断</span>', provided)

    def test_page_has_no_script_and_no_inline_style_and_its_style_hash_holds(self):
        import base64, hashlib, re
        _, page = self.page(wide_model())
        self.assertNotIn('<script', page)
        body = page.split('<body>', 1)[1]
        self.assertNotIn(' style=', body)
        style = re.search(r'<style>(.*?)</style>', page, re.S).group(1)
        digest = base64.b64encode(hashlib.sha256(style.encode('utf-8')).digest()).decode('ascii')
        self.assertIn(f"style-src &#x27;sha256-{digest}&#x27;", page)

    def test_every_option_carries_one_letter_in_the_head_the_cells_and_the_orders(self):
        import re
        target, page = self.page(wide_model())
        self.assertEqual(target.option_codes(target.build_comparison(wide_model())), {'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D', 'e': 'E'})
        head = re.findall(r'<th scope="col" role="columnheader"><span class="opt-code">(\w)</span>([^<]+)</th>', page)
        self.assertEqual(head, [('A', '甲'), ('B', '乙'), ('C', '丙'), ('D', '丁'), ('E', '戊')])
        cells = re.findall(r'<span class="cell-option"><span class="opt-code">(\w)</span>([^<]+)</span>', page)
        self.assertEqual(cells, head)
        ranked = re.findall(r'<span class="rank">(\d)</span><span class="opt-code">(\w)</span><span class="candidate">([^<]+)</span>', page)
        self.assertEqual(ranked, [('1', 'A', '甲'), ('2', 'E', '戊'), ('3', 'C', '丙'), ('4', 'B', '乙')])
        # the table keeps its roles, so it is still a table where a narrow screen lays it out as blocks
        self.assertIn('<table class="cmp-table" role="table">', page)
        self.assertEqual(page.count('role="cell"'), 5)
        self.assertEqual(page.count('role="rowheader"'), 1)

    def test_scale_places_only_ranked_values_by_their_value(self):
        import re
        target = module()
        result = target.build_comparison(wide_model())
        scale = target.scale_svg(result['dimensions'][0], target.option_codes(result))
        dots = re.findall(r'<circle class="sc-dot is-(\w+)" cx="([\d.]+)%" cy="(\d+)" r="6"/>', scale)
        # four ranked values; the unknown option has no dot and no letter on the scale
        self.assertEqual(len(dots), 4)
        self.assertNotIn('>D<', scale)
        places = {(kind, float(x)) for kind, x, _ in dots}
        self.assertEqual(places, {('observed', 5.0), ('assumed', 5.0), ('assumed', 27.5), ('assumed', 95.0)})
        # the two options tied at zero stand one above the other, each with its own letter beside it
        tied = sorted(int(y) for kind, x, y in dots if float(x) == 5.0)
        self.assertEqual(tied[1] - tied[0], 14)
        self.assertEqual(re.findall(r'dx="11">(\w)</text>', scale), ['A', 'E'])
        self.assertEqual(re.findall(r'<text class="sc-value"[^>]*>([^<]+)</text>', scale), ['0', '10', '40'])
        self.assertIn('aria-hidden="true"', scale)

    def test_scale_staggers_close_values_and_is_left_out_where_it_would_say_nothing(self):
        import re
        target = module()
        data = wide_model()
        data['cells']['c']['cost']['value'] = 38
        result = target.build_comparison(data)
        scale = target.scale_svg(result['dimensions'][0], target.option_codes(result))
        lines = {value: int(y) for y, value in re.findall(r'<text class="sc-value" x="[\d.]+%" y="(\d+)"[^>]*>([^<]+)</text>', scale)}
        self.assertGreater(lines['40'], lines['38'], 'A value close to its neighbour is lettered on the next line.')
        # one ranked value has no scale to stand on; neither has a dimension without a common scale
        single = model()
        result = target.build_comparison(single)
        codes = target.option_codes(result)
        self.assertNotEqual(target.scale_svg(result['dimensions'][0], codes), '')
        single['cells']['manual']['hours'] = {'value': None, 'basis': 'unknown'}
        result = target.build_comparison(single)
        self.assertEqual(target.scale_svg(result['dimensions'][0], codes), '')
        self.assertEqual(target.scale_svg(result['dimensions'][1], codes), '')
        self.assertEqual(target.render_html(result).count('<svg class="scale"'), 0)

    def test_scale_survives_values_beyond_floating_point(self):
        target = module()
        data = wide_model()
        data['cells']['b']['cost']['value'] = 10 ** 90 + 7
        data['cells']['c']['cost']['value'] = 10 ** 90 + 8
        result = target.build_comparison(data)
        scale = target.scale_svg(result['dimensions'][0], target.option_codes(result))
        self.assertIn('cx="95.00%"', scale)
        self.assertIn(str(10 ** 90 + 8), scale)
        # a spread that arithmetic cannot hold is not drawn; the order still lists it
        for low, high in ((0.5, 10 ** 400), (-1.7e308, 1.7e308)):
            data['cells']['a']['cost']['value'], data['cells']['b']['cost']['value'] = low, high
            result = target.build_comparison(data)
            self.assertEqual(target.scale_svg(result['dimensions'][0], target.option_codes(result)), '')
            self.assertIn('<ol class="ranking"', target.render_html(result))

    def test_english_page_sets_its_own_words(self):
        _, page = self.page(wide_model(), 'en')
        self.assertIn('<span class="page-kind">Comparison</span>', page)
        self.assertIn('<span class="strip-aside">values are not real-world facts</span>', page)
        self.assertIn('The letter before an option is its mark on the scales below.', page)


if __name__ == '__main__':
    unittest.main()
