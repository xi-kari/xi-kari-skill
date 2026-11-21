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

    def test_paths_say_whether_they_describe_one_unit_or_the_whole(self):
        text = self.read('modules/dynamics/MODULE.md')
        self.assertIn('先写明路径是对单个单位说的，还是对整体的构成说的', text)
        self.assertIn('不同单位可以处在不同路径', text)

    def test_generation_author_is_sent_to_the_full_guide(self):
        text = self.read('modules/generate/MODULE.md')
        self.assertIn('生成作者另读[生成指南](../../references/generation.md)全文', text)
        self.assertIn('由 M10 的生成作者读取', self.read('references/generation.md'))

    def test_a_practical_question_that_also_asks_about_other_theories_stays_mixed(self):
        text = self.read('references/routing.md')
        for phrase in ('跨理论对话通常接 R7', '比较的理论里不包括本框架自己时，同样按跨理论对话的做法做',
                       '是混合请求', '不把整题改成理论评估'):
            self.assertIn(phrase, text)

    def test_a_premise_of_the_framework_is_named_as_a_premise(self):
        text = self.read('references/communication.md')
        for phrase in ('这是本次分析采用的前提，不接受它时结论会怎样不同', '框架的说法不替事实作证，也不替读者决定价值'):
            self.assertIn(phrase, text)

    def test_lost_workload_is_distinct_from_available_capacity(self):
        text = self.read('modules/dynamics/MODULE.md')
        for term in ('p/(1−p)', '相对原工作量', '实际可用容量另查'):
            self.assertIn(term, text)

    def test_institution_checklist_covers_operation_and_remedy(self):
        text = self.read('references/decision.md')
        checklist = text.split('## 制度与流程草案核对表\n', 1)[1].split('\n## ', 1)[0]
        rows = [line for line in checklist.splitlines() if line.startswith('| ')][2:]
        self.assertEqual(len(rows), 8)
        for term in ('谁申请', '谁决定', '制度暂停', '身份泄露', '保护失效', '授权到期', '纠错无法执行',
                     '恢复原状', '补救', '数据泄露', '收件', '排队', '回应', '协助表达', '代为提交', '代为决定',
                     '初审', '复核', '不超过 12 条'):
            self.assertIn(term, checklist)
        for path in ('modules/choice/MODULE.md', 'modules/compose/MODULE.md'):
            self.assertIn('制度与流程草案核对表', self.read(path))

    def test_contract_branches_on_numeric_ambiguity_before_recommendation(self):
        text = self.read('modules/contract/MODULE.md')
        for term in ('动笔前', '计时口径', '预算或窗口的起算点', '能力是上限还是实际完成量',
                     '总量是否包含复核', '每种读法都算出结果', '先检查有没有任何方案可行', '结论依赖哪种读法'):
            self.assertIn(term, text)
        self.assertLess(text.index('动笔前'), text.index('4. 对未来请求'))

    def test_queue_ambiguity_has_both_operation_orders(self):
        text = self.read('modules/contract/MODULE.md')
        for term in ('未明确日内顺序', '先到件后处理', '先处理后到件',
                     'max(0, Q + A − C)', 'max(0, Q − C) + A', '首日是否有可处理任务'):
            self.assertIn(term, text)


if __name__ == '__main__':
    unittest.main()
