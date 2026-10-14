"""独立复核 comparison 工具：原子提交与依据身份语义的复现测试。"""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'comparison.py'


def module():
    spec = importlib.util.spec_from_file_location('comparison_audit', SCRIPT)
    target = importlib.util.module_from_spec(spec)
    sys.modules['comparison_audit'] = target
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


def failing_replace(comp, fail_on):
    real_replace = comp.os.replace
    calls = {'n': 0}

    def wrapper(src, dst, *args, **kwargs):
        calls['n'] += 1
        if calls['n'] == fail_on:
            raise OSError(f'模拟第{fail_on}个文件替换失败')
        return real_replace(src, dst, *args, **kwargs)

    return wrapper, real_replace


class ComparisonAtomicWriteTests(unittest.TestCase):
    def test_failed_replacement_restores_previous_outputs_not_deletes_them(self):
        comp = module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'model.json'
            source.write_text(json.dumps(model(), ensure_ascii=False), encoding='utf-8')
            out = root / 'out'
            result = comp.build_comparison(comp.read_comparison(source))
            written = comp.write_outputs(result, source, out)
            before = {kind: Path(path).read_bytes() for kind, path in written.items()}

            wrapper, real_replace = failing_replace(comp, 3)
            comp.os.replace = wrapper
            try:
                with self.assertRaises(OSError):
                    comp.write_outputs(result, source, out, 'all', force=True)
            finally:
                comp.os.replace = real_replace

            for kind, path in written.items():
                target = Path(path)
                self.assertTrue(target.exists(), f'{kind} 在失败后被删除，而非恢复为原内容')
                self.assertEqual(target.read_bytes(), before[kind], f'{kind} 未恢复为提交前内容')
            self.assertFalse((out / '.comparison.lock').exists(), '失败后残留独占锁')
            self.assertEqual(list(out.glob('.comparison-*')), [], '失败后残留临时文件')

    def test_fresh_write_failure_leaves_no_partial_outputs(self):
        comp = module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'model.json'
            source.write_text(json.dumps(model(), ensure_ascii=False), encoding='utf-8')
            out = root / 'out'
            result = comp.build_comparison(comp.read_comparison(source))

            wrapper, real_replace = failing_replace(comp, 2)
            comp.os.replace = wrapper
            try:
                with self.assertRaises(OSError):
                    comp.write_outputs(result, source, out)
            finally:
                comp.os.replace = real_replace

            self.assertEqual({p.name for p in out.iterdir()}, set(),
                             '全新写入中途失败后留下了半成品')

    def test_directory_at_third_target_is_refused_before_any_write(self):
        comp = module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'model.json'
            source.write_text(json.dumps(model(), ensure_ascii=False), encoding='utf-8')
            out = root / 'out'
            out.mkdir()
            (out / 'comparison-table.html').mkdir()
            result = comp.build_comparison(comp.read_comparison(source))
            with self.assertRaises(ValueError):
                comp.write_outputs(result, source, out)
            self.assertFalse((out / 'comparison-results.json').exists())
            self.assertFalse((out / 'comparison-table.md').exists())
            self.assertFalse((out / '.comparison.lock').exists())

    def test_non_text_source_is_refused(self):
        comp = module()
        for bad in (123, ['x'], {'a': 1}, True):
            broken = model()
            broken['cells']['auto']['hours'] = {'value': 1, 'basis': 'observed', 'source': bad}
            with self.assertRaises(ValueError, msg=f'source={bad!r} 未被拒绝'):
                comp.validate_comparison(broken)


class ComparisonBasisSemanticsTests(unittest.TestCase):
    def test_unknown_and_not_orderable_hold_in_all_formats(self):
        comp = module()
        result = comp.build_comparison(model())
        hours = next(item for item in result['dimensions'] if item['id'] == 'hours')
        self.assertNotIn('hybrid', [item['id'] for item in hours['ranking']],
                         'unknown 单元格被纳入排序')
        reversible = next(item for item in result['dimensions'] if item['id'] == 'reversible')
        self.assertNotIn('ranking', reversible, 'not_orderable 维度产生了排序')

        markdown = comp.render_markdown(result)
        document = comp.render_html(result)
        payload = json.loads(comp.render_json(result))
        self.assertIn('假设', markdown)
        self.assertIn('basis-assumed', document)
        auto = next(row for row in payload['rows'] if row['candidate'] == 'auto')
        self.assertEqual(auto['values']['hours']['basis'], 'assumed')

    def test_unknown_with_numeric_value_is_refused(self):
        comp = module()
        broken = model()
        broken['cells']['hybrid']['hours'] = {'value': 5, 'basis': 'unknown'}
        with self.assertRaises(ValueError):
            comp.validate_comparison(broken)


if __name__ == '__main__':
    unittest.main()
