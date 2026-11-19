"""Check the ten-sentence primer the skill carries and the reading mode that uses it."""

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PRIMER = ROOT / 'references' / 'ten-sentences.md'
NUMBERED = re.compile(r'^(\d+)\. (.+)$', re.MULTILINE)
SECTION = re.compile(r'(?:§((?:\d+)(?:\.\d+)+)|\b([A-D]\.\d+))')


def numbered_blocks(text: str) -> list[list[str]]:
    """Runs of list items numbered 1, 2, 3, ... in the order they appear."""
    blocks: list[list[str]] = []
    for number, item in NUMBERED.findall(text):
        if number == '1':
            blocks.append([])
        if blocks and int(number) == len(blocks[-1]) + 1:
            blocks[-1].append(item.strip())
    return blocks


class PrimerModeTests(unittest.TestCase):
    def test_package_carries_the_primer(self):
        files = json.loads((ROOT / 'skill-package.json').read_text(encoding='utf-8'))['files']
        self.assertIn('references/ten-sentences.md', files)
        self.assertTrue(PRIMER.exists())

    def test_primer_states_ten_sentences_in_both_languages(self):
        chinese, english = numbered_blocks(PRIMER.read_text(encoding='utf-8'))
        self.assertEqual((len(chinese), len(english)), (10, 10))

    def test_primer_sentences_match_the_handbook_and_the_readme(self):
        chinese, english = numbered_blocks(PRIMER.read_text(encoding='utf-8'))
        heading = re.compile(r'^## (?:[一二三四五六七八九十]+　|\d+\. )(.+)$', re.MULTILINE)
        for sentences, page, readme in ((chinese, 'website/primer/index.md', 'README.md'),
                                        (english, 'website/en/primer/index.md', 'README.en.md')):
            with self.subTest(page=page):
                titles = [title.strip() for title in heading.findall((ROOT / page).read_text(encoding='utf-8'))]
                self.assertEqual(len(titles), 10)
                # the handbook heading opens each sentence of the primer, apart from closing punctuation
                opening = [re.split(r'[。：:.；;]', sentence)[0] for sentence in sentences]
                self.assertEqual([title.startswith(start) or start.startswith(title) for title, start in zip(titles, opening)], [True] * 10)
                listed = next(block for block in numbered_blocks((ROOT / readme).read_text(encoding='utf-8'))
                              if len(block) == 10 and block[0].startswith(titles[0]))
                self.assertEqual([item.startswith(title) for title, item in zip(titles, listed)], [True] * 10)

    def test_every_cited_section_exists_in_the_source(self):
        text = PRIMER.read_text(encoding='utf-8')
        cited = {first or second for first, second in SECTION.findall(text)}
        self.assertGreater(len(cited), 25)
        source = (ROOT / 'source' / 'Xikari-条件结构与转化论.md').read_text(encoding='utf-8')
        headings = set(re.findall(r'^#{1,4}\s+((?:\d+|[A-D])(?:\.\d+)+)[\s　]', source, re.MULTILINE))
        self.assertEqual(sorted(cited - headings), [])

    def test_skill_offers_the_mode_only_on_request_and_keeps_full_study_the_default(self):
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('默认模式为 `full`', skill)
        self.assertIn('`primer` 只在用户明确要求时使用', skill)
        self.assertIn('(references/ten-sentences.md)', skill)
        self.assertIn('不作默认', skill)
        study = (ROOT / 'references' / 'full-source-study.md').read_text(encoding='utf-8')
        self.assertIn('`reading_mode=primer`', study)
        self.assertIn('作者不为省时间自行改用', study)
        primer = PRIMER.read_text(encoding='utf-8')
        self.assertIn('本次只按十句话作答，没有读原文', primer)

    def test_forecast_guidance_allows_a_rough_probability_with_its_basis(self):
        guide = (ROOT / 'references' / 'forecasting.md').read_text(encoding='utf-8')
        self.assertIn('历史频率、同类事件的比例、余量相对已见波动的大小，都可以作为经验依据', guide)
        self.assertIn('把握程度仍只由依据决定', guide)


if __name__ == '__main__':
    unittest.main()
