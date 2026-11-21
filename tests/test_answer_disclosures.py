from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
GUIDE = 'references/complete-answer.md'


def read(path):
    return (ROOT / path).read_text(encoding='utf-8-sig')


def links(path):
    base = (ROOT / path).parent
    return {(base / target.split('#')[0]).resolve()
            for target in re.findall(r'\]\(([^)\s]+)\)', read(path))
            if '://' not in target and not target.startswith('#')}


class AnswerDisclosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.section = read(GUIDE).split('## 开头的交代与方法附注', 1)[1].split('\n## ', 1)[0]

    def test_method_note_has_one_order_and_scales_with_the_answer(self):
        items = re.findall(r'^\d\. \*\*(.+?)\*\*', self.section, re.M)
        self.assertEqual(items, ['判断类型与阅读。', '规则卡。', '取材。', '核对与审查。', '没有做到的部分。'])
        for phrase in ('只写本次适用的项', '短答合成一两句；长稿每项一小段', '不把中心判断推到后面',
                       '没有人可问时替用户作的假定', '就同时写在那条结论处', '不写制作经过'):
            self.assertIn(phrase, self.section)

    def test_other_guides_point_here_instead_of_setting_their_own_length(self):
        guide = (ROOT / GUIDE).resolve()
        for name in ('references/communication.md', 'references/collection.md', 'modules/compose/MODULE.md'):
            self.assertIn(guide, links(name), name)
        self.assertNotIn('末尾一行方法附注', read('modules/compose/MODULE.md'))
        for target in ('references/communication.md', 'references/collection.md'):
            self.assertIn((ROOT / target).resolve(), links(GUIDE))

    def test_entry_still_puts_the_short_disclosures_after_the_central_judgement(self):
        entry = read('SKILL.md')
        self.assertIn('合成一两句紧接在中心判断之后', entry)
        self.assertIn('references/complete-answer.md', entry)


if __name__ == '__main__':
    unittest.main()
