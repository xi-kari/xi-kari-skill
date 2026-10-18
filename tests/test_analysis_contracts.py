from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AnalysisContractTests(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding='utf-8-sig')

    def test_path_hierarchy_is_shared_by_generation_and_composition(self):
        for path in ('modules/dynamics/MODULE.md', 'modules/forecast/MODULE.md', 'modules/compose/MODULE.md'):
            with self.subTest(path=path):
                text = self.read(path)
                for term in ('同一对象', '同一窗口', '互斥', '外溢', '触发条件', '早期信号', '反向信号', '下一份材料'):
                    self.assertIn(term, text)

    def test_institution_checklist_covers_operation_and_remedy(self):
        text = self.read('references/decision.md')
        checklist = text.split('## 制度与流程草案核对表\n', 1)[1].split('\n## ', 1)[0]
        rows = [line for line in checklist.splitlines() if line.startswith('| ')][2:]
        self.assertEqual(len(rows), 8)
        for term in ('谁申请', '谁决定', '制度暂停', '身份泄露', '保护失效', '授权到期', '纠错无法执行',
                     '回滚', '补救', '数据泄露', '收件', '排队', '回应', '协助表达', '代为提交', '代为决定',
                     '初审', '复核', '不超过 12 条'):
            self.assertIn(term, checklist)
        for path in ('modules/choice/MODULE.md', 'modules/compose/MODULE.md'):
            self.assertIn('制度与流程草案核对表', self.read(path))


if __name__ == '__main__':
    unittest.main()
