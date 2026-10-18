import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AnswerMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('answer_metrics', ROOT / 'scripts/answer_metrics.py')
        cls.metrics = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.metrics)

    def test_internal_codes_use_declared_boundaries(self):
        result = self.metrics.measure('S0—S6、X0、G3、CM-LOAD、IT2、IG1、DF7、M9、R4、CAS-FAILURE。AS0、X01。')
        self.assertEqual(result['internal_codes'], ['S0—S6', 'X0', 'G3', 'CM-LOAD', 'IT2', 'IG1', 'DF7', 'M9', 'R4', 'CAS-FAILURE'])

    def test_only_trailing_method_note_is_excluded(self):
        result = self.metrics.measure('工作已经完成。\n\n方法附注：S6、CM-LOAD（派生草稿）。')
        self.assertEqual(result['characters'], len('工作已经完成。'))
        self.assertEqual(result['internal_codes'], [])
        self.assertEqual(self.metrics.measure('方法附注：S6。\n实际正文 X0。')['internal_codes'], ['S6', 'X0'])

    def test_method_note_does_not_hide_prior_code(self):
        result = self.metrics.measure('S6 已完成。\n\n**方法附注：** CM-LOAD（派生草稿）。')
        self.assertEqual(result['internal_codes'], ['S6'])

    def test_negative_density_follows_declared_sentence_and_word_rules(self):
        result = self.metrics.measure('不能倒填，不等于无用。只在已登记时成立！无需重复？\n\n方法附注：不得、不是。')
        self.assertEqual(result['sentences'], 3)
        self.assertEqual(result['negative_words'], 3)
        self.assertEqual(result['negatives_per_sentence'], 1.0)
        self.assertEqual(result['paragraphs'], 1)

    def test_empty_body_has_no_defined_density(self):
        self.assertIsNone(self.metrics.measure('')['negatives_per_sentence'])
        self.assertEqual(self.metrics.measure('')['paragraphs'], 0)

    def test_paragraphs_and_unpunctuated_tail_are_counted(self):
        result = self.metrics.measure('最低为 20 件。\n\n当天收件次日处理时为 28 件')
        self.assertEqual(result['paragraphs'], 2)
        self.assertEqual(result['sentences'], 2)


class PresentationContractTests(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding='utf-8-sig')

    def test_draft_disclosure_is_identical_and_outside_body(self):
        phrase = '正文用白话说机制，所用草稿卡只列在答案末尾一行“方法附注”或执行记录里，并标明派生草稿身份。'
        for path in ('SKILL.md', 'rules/README.md', 'modules/forecast/MODULE.md'):
            with self.subTest(path=path):
                text = self.read(path)
                self.assertIn(phrase, text)
                self.assertNotRegex(text, r'在答案中列出|明示身份并列出所用草稿卡|明确其身份并列出实际所用草稿卡')

    def test_plain_language_scope_and_theory_exception(self):
        text = self.read('references/communication.md')
        for term in ('S0—S6', 'X0', 'IT', 'IG', 'DF', 'CM-', '规则卡编号', '路由', '模块', '写回', '良性退场', '记忆', 'R1', 'R7', '首次出现'):
            self.assertIn(term, text)
        self.assertIn('扫描正文中的代号和自造词', self.read('modules/compose/MODULE.md'))

    def test_length_instructions_agree_across_entry_and_guides(self):
        for path in ('SKILL.md', 'references/communication.md', 'references/complete-answer.md'):
            with self.subTest(path=path):
                text = self.read(path)
                self.assertIn('篇幅与问题相称', text)
                self.assertNotIn('只有用户明确要求简答或限制篇幅时才压缩', text)
                self.assertNotIn('用户明确要求简答或规定篇幅时才压缩', text)
        text = self.read('modules/compose/MODULE.md')
        for term in ('一到两段', '边界只写一次', '把边界写成一串否定句', '有确定答案的题写成长篇', '回到开头修改'):
            self.assertIn(term, text)


if __name__ == '__main__':
    unittest.main()
