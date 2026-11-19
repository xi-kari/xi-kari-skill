"""Check the handbook's primer and the one-sentence strips set under section headings."""

import html
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / 'website'
BUILT = ROOT / 'docs' / 'handbook'
LOCALES = {
    'zh': {'page': 'primer/index.md', 'map': 'public/source-map.json', 'content': 'content',
           'readme': 'README.md', 'built': 'theory/part-03.html', 'tag': '一句话'},
    'en': {'page': 'en/primer/index.md', 'map': 'public/en/source-map.json', 'content': 'content/en',
           'readme': 'README.en.md', 'built': 'en/theory/part-03.html', 'tag': 'In brief'},
}
SENTENCE = re.compile(r'^## (?:[一二三四五六七八九十]+　|\d+\. )(.+)$', re.MULTILINE)
SOURCE_LINK = re.compile(r'\]\(\.\./(theory/[^)#\s]+)#(section-[a-z0-9-]+)\)')
GIST = re.compile(r'<h[234] id="(section-[a-z0-9-]+)"[^>]*>.*?</h[234]>\s*'
                  r'<div class="xk-gist"><span class="xk-gist__tag">([^<]*)</span>'
                  r'<span class="xk-gist__text">(.*?)</span>(<details class="xk-gist__codes">.*?</details>)?</div>', re.DOTALL)
CODE_LINK = re.compile(r'<li><a href="([^"]+)"><b>([^<]+)</b>([^<]+)</a></li>')


def squeeze(text: str) -> str:
    """Text without any spacing, for comparing a name with the heading it was cut from."""
    return re.sub(r'\s+', '', text)


def lessons(locale: str) -> dict:
    content = WEBSITE / LOCALES[locale]['content']
    data = json.loads((content / 'section-lessons.json').read_text(encoding='utf-8'))['lessons']
    overrides = content / 'lesson-overrides.json'
    if overrides.exists():
        for key, fields in json.loads(overrides.read_text(encoding='utf-8'))['lessons'].items():
            data[key] = {**data.get(key, {}), **fields}
    return data


class HandbookPrimerTests(unittest.TestCase):
    def test_each_language_states_ten_sentences(self):
        for locale, paths in LOCALES.items():
            with self.subTest(locale=locale):
                text = (WEBSITE / paths['page']).read_text(encoding='utf-8')
                self.assertEqual(len(SENTENCE.findall(text)), 10)

    def test_every_source_reference_resolves_to_a_section_of_the_book(self):
        for locale, paths in LOCALES.items():
            with self.subTest(locale=locale):
                sections = json.loads((WEBSITE / paths['map']).read_text(encoding='utf-8'))['sections']
                prefix = '/en/' if locale == 'en' else '/'
                known = set(sections.values())
                links = SOURCE_LINK.findall((WEBSITE / paths['page']).read_text(encoding='utf-8'))
                self.assertGreater(len(links), 25)
                missing = [f'{route}#{anchor}' for route, anchor in links if f'{prefix}{route}#{anchor}' not in known]
                self.assertEqual(missing, [])

    def test_both_languages_cite_the_same_sections(self):
        cited = {locale: SOURCE_LINK.findall((WEBSITE / paths['page']).read_text(encoding='utf-8'))
                 for locale, paths in LOCALES.items()}
        self.assertEqual(cited['zh'], cited['en'])

    def test_readme_lists_the_same_ten_sentences(self):
        for locale, paths in LOCALES.items():
            with self.subTest(locale=locale):
                sentences = [item.strip() for item in SENTENCE.findall((WEBSITE / paths['page']).read_text(encoding='utf-8'))]
                readme = (ROOT / paths['readme']).read_text(encoding='utf-8')
                listed = re.findall(r'^(\d+)\. (.+)$', readme, re.MULTILINE)
                start = next(i for i, (number, text) in enumerate(listed) if number == '1' and text.startswith(sentences[0]))
                block = [text for _, text in listed[start:start + 10]]
                self.assertEqual([text.startswith(sentence) for sentence, text in zip(sentences, block)], [True] * 10)

    def test_built_pages_set_each_lesson_lead_under_its_heading(self):
        for locale, paths in LOCALES.items():
            with self.subTest(locale=locale):
                page = BUILT / paths['built']
                self.assertTrue(page.exists(), 'Build the handbook before this check.')
                sections = json.loads((WEBSITE / paths['map']).read_text(encoding='utf-8'))['sections']
                route = ('/en/' if locale == 'en' else '/') + 'theory/part-03'
                all_lessons = lessons(locale)
                expected = {href.split('#')[1]: all_lessons[key]['lead'].strip()
                            for key, href in sections.items()
                            if href.split('#')[0] == route and '#section-' in href and all_lessons.get(key, {}).get('lead')}
                found = {anchor: (tag, html.unescape(text)) for anchor, tag, text, _ in GIST.findall(page.read_text(encoding='utf-8'))}
                self.assertGreater(len(expected), 10)
                self.assertEqual({anchor: text for anchor, (tag, text) in found.items()}, expected)
                self.assertEqual({tag for tag, _ in found.values()}, {paths['tag']})

    def test_strips_name_the_codes_a_section_uses_from_the_books_own_headings(self):
        for locale, paths in LOCALES.items():
            with self.subTest(locale=locale):
                content = WEBSITE / paths['content']
                units = json.loads((content / 'reading-units.json').read_text(encoding='utf-8'))['units']
                headings = {unit['section_id']: unit['title_exact'] for unit in units if unit.get('section_id')}
                routes = {unit['website_source_route'] for unit in units if unit.get('website_source_route')}
                text = (BUILT / paths['built']).read_text(encoding='utf-8')
                legends = {anchor: CODE_LINK.findall(codes) for anchor, _, _, codes in GIST.findall(text) if codes}
                self.assertGreater(len(legends), 5)
                page_route = ('/en/' if locale == 'en' else '/') + 'theory/part-03'
                for anchor, links in legends.items():
                    codes = [code for _, code, _ in links]
                    self.assertEqual(len(codes), len(set(codes)), anchor)
                    for href, code, name in links:
                        name = html.unescape(name)
                        # every name is cut from a heading that carries this code and nothing else like it
                        owners = [title for title in headings.values() if code in title and squeeze(name) in squeeze(title.replace(code, ''))]
                        self.assertEqual(len(owners), 1, (anchor, code, name))
                        target = page_route + href if href.startswith('#') else href.replace('/xi-kari-skill/handbook', '').replace('.html#', '#')
                        self.assertIn(target, routes, (anchor, code, href))
                # a section does not list the code its own heading defines
                own = {anchor: [code for _, code, _ in links] for anchor, links in legends.items()}
                self.assertNotIn('D0', own.get('section-3-1', []))
                self.assertIn('D0', {code for codes in own.values() for code in codes})

    def test_strips_are_presentation_and_leave_the_generated_source_pages_alone(self):
        for folder in ('theory', 'en/theory'):
            for page in (WEBSITE / folder).rglob('*.md'):
                self.assertNotIn('xk-gist', page.read_text(encoding='utf-8'), page.name)
        css = (WEBSITE / '.vitepress/theme/styles/theory.css').read_text(encoding='utf-8')
        self.assertIn('html.xk-source-only .xk-gist { display: none; }', css)


if __name__ == '__main__':
    unittest.main()
