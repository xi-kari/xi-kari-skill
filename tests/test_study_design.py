import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'study_design.py'


def module():
    spec = importlib.util.spec_from_file_location('study_design', SCRIPT)
    target = importlib.util.module_from_spec(spec)
    sys.modules['study_design'] = target
    spec.loader.exec_module(target)
    return target


def design():
    return {
        'schema_version': 1,
        'question': '申诉等待是否来自复核容量，而不是入口记录改变',
        'propositions': [
            {
                'id': 'capacity',
                'statement': '等待主要由复核容量不足造成',
                'supports': ['复核环节之前已无排队，而复核之后出现等待'],
                'excludes': ['入口记录规则改变前后，等待在复核环节内没有变化'],
                'distinguishing': ['比较入口规则改变前后、复核环节内外的等待分布'],
            },
            {
                'id': 'records',
                'statement': '等待上升只是入口记录口径改变造成',
                'supports': ['同一时段核对原始受理时间与登记时间'],
                'excludes': ['原始受理时间也同步上升'],
                'distinguishing': ['取得入口规则变更日期，并核对原始受理时间'],
            },
        ],
        'observation_targets': ['申请人从提交到获得服务的完整过程'],
        'time_window': '入口规则改变前后各六个月',
        'required_materials': ['入口规则变更记录', '原始受理时间', '复核完成时间'],
        'hold_conditions': ['受理渠道数量不变'],
        'change_conditions': ['入口规则变更'],
        'confounders': ['同期人员减少', '案件类型构成变化'],
        'stop_conditions': ['无法取得入口规则变更日期时，本轮停止对因果作用的判断'],
        'execution': [{'who': '持有案件数据库只读权限的分析者', 'authority': '仅限内部统计，不含个人身份信息'}],
    }


class StudyDesignTests(unittest.TestCase):
    def test_a_proposition_without_a_distinguishing_observation_is_refused(self):
        broken = design()
        broken['propositions'][0]['distinguishing'] = []
        with self.assertRaises(ValueError):
            module().validate_design(broken)

    def test_structural_errors_are_refused_on_specific_grounds(self):
        validate = module().validate_design
        broken = design(); broken['schema_version'] = 2
        with self.assertRaises(ValueError): validate(broken)
        broken = design(); del broken['question']
        with self.assertRaises(ValueError): validate(broken)
        broken = design(); broken['propositions'] = []
        with self.assertRaises(ValueError): validate(broken)
        broken = design(); broken['propositions'][0]['statement'] = ''
        with self.assertRaises(ValueError): validate(broken)
        broken = design(); broken['propositions'][0]['id'] = design()['propositions'][1]['id']
        with self.assertRaises(ValueError): validate(broken)
        broken = design(); broken['confounders'] = '不是列表'
        with self.assertRaises(ValueError): validate(broken)

    def test_missing_fields_are_reported_as_missing_not_invented(self):
        sparse = {
            'schema_version': 1,
            'question': '只给出问题，其余留空',
            'propositions': [{
                'id': 'only', 'statement': '某个命题',
                'distinguishing': ['某项可以区分它的观察'],
            }],
        }
        report = module().validate_design(sparse)
        self.assertTrue(report['valid'])
        for field in ('observation_targets', 'time_window', 'required_materials',
                      'hold_conditions', 'change_conditions', 'confounders', 'stop_conditions', 'execution'):
            self.assertIn(field, report['missing'])
        self.assertIn('supports', report['propositions'][0]['missing'])
        self.assertIn('excludes', report['propositions'][0]['missing'])

    def test_report_never_claims_the_research_is_worthwhile_or_verified(self):
        report = module().validate_design(design())
        self.assertIn('不判断', report['notice'])
        self.assertTrue(report['valid'])

    def test_render_keeps_every_substantive_field(self):
        document = module().render_markdown(module().validate_design(design()), design())
        for text in ('申诉等待是否来自复核容量', '等待主要由复核容量不足造成',
                     '比较入口规则改变前后、复核环节内外的等待分布',
                     '入口规则改变前后各六个月', '入口规则变更记录',
                     '受理渠道数量不变', '同期人员减少', '无法取得入口规则变更日期时',
                     '持有案件数据库只读权限的分析者'):
            self.assertIn(text, document)
        self.assertIn('缺失', module().render_markdown(module().validate_design({
            'schema_version': 1, 'question': '稀疏设计',
            'propositions': [{'id': 'a', 'statement': '命题', 'distinguishing': ['观察']}],
        }), {'schema_version': 1, 'question': '稀疏设计',
             'propositions': [{'id': 'a', 'statement': '命题', 'distinguishing': ['观察']}]}))

    def test_render_refuses_to_write_into_the_install_tree(self):
        target = module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'design.json'
            source.write_text(json.dumps(design(), ensure_ascii=False), encoding='utf-8')
            with self.assertRaises(OSError):
                target.write_document('# 内容', ROOT / 'scripts' / 'refused.md')

    def test_cli_validate_and_render(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'design.json'
            source.write_text(json.dumps(design(), ensure_ascii=False), encoding='utf-8')
            valid = subprocess.run([sys.executable, str(SCRIPT), '--design', str(source), 'validate'],
                                   capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(valid.returncode, 0, valid.stderr)
            self.assertTrue(json.loads(valid.stdout)['valid'])
            out = root / '说明.md'
            rendered = subprocess.run([sys.executable, str(SCRIPT), '--design', str(source),
                                       'render', '--output', str(out)],
                                      capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            self.assertTrue(out.exists())
            self.assertIn('申诉等待', out.read_text(encoding='utf-8'))
            bad = subprocess.run([sys.executable, str(SCRIPT), '--design', str(source),
                                  'render', '--output', str(ROOT / 'scripts' / 'no.md')],
                                 capture_output=True, text=True, encoding='utf-8')
            self.assertNotEqual(bad.returncode, 0)


if __name__ == '__main__':
    unittest.main()
