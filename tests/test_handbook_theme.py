"""Check the handbook theme's bundled display face, its custom properties and its dated facts."""

import hashlib
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / 'website'
THEME = WEBSITE / '.vitepress' / 'theme'
BUILT = ROOT / 'docs' / 'handbook'
VOID_TAGS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
SKIPPED_TAGS = {'script', 'style', 'template'}


def face_rules():
    """Which selectors put text in the display face, and which put it back in a text face.

    A rule is filed under its subject: a class, or a tag inside the nearest class named before it.
    """
    display, plain = set(), set()
    for path in sorted((THEME / 'styles').glob('*.css')):
        css = re.sub(r'/\*.*?\*/', '', path.read_text(encoding='utf-8'), flags=re.S)
        for selectors, body in re.findall(r'([^{}]+)\{([^{}]*)\}', css):
            if 'var(--xk-font-display)' in body:
                target = display
            elif re.search(r'font(?:-family)?:[^;]*var\(--xk-font-(?:sans|song|code|body)\)', body):
                target = plain
            else:
                continue
            selectors = re.sub(r':(?:is|not|where|has)\([^()]*\)', '', selectors)
            for selector in selectors.split(','):
                parts = re.sub(r'::?[\w-]+(?:\([^()]*\))?', '', selector).replace('>', ' ').replace('+', ' ').replace('~', ' ').split()
                if not parts or parts[0].startswith('@'):
                    continue
                classes = re.findall(r'\.([\w-]+)', parts[-1])
                if classes:
                    target.add(('class', classes[0]))
                    continue
                tag = re.match(r'[a-z][a-z0-9]*', parts[-1])
                above = [name for part in parts[:-1] for name in re.findall(r'\.([\w-]+)', part)]
                if tag and above:
                    target.add(('tag', above[-1], tag.group(0)))
    return display, plain


class DisplayText(HTMLParser):
    """Collect the characters a built page sets in the display face."""

    def __init__(self, display, plain):
        super().__init__(convert_charrefs=True)
        self.display_classes = {rule[1] for rule in display if rule[0] == 'class'}
        self.plain_classes = {rule[1] for rule in plain if rule[0] == 'class'}
        self.display_tags = {(rule[1], rule[2]) for rule in display if rule[0] == 'tag'}
        self.plain_tags = {(rule[1], rule[2]) for rule in plain if rule[0] == 'tag'}
        self.stack = []
        self.found = {}

    def handle_starttag(self, tag, attrs):
        classes = set((dict(attrs).get('class') or '').split())
        above = set().union(*(entry[1] for entry in self.stack)) if self.stack else set()
        face = self.stack[-1][2] if self.stack else 'plain'
        if tag in SKIPPED_TAGS:
            face = 'skip'
        elif face != 'skip':
            # a rule on the element's own class outranks a rule on its tag, as it does in the stylesheet
            if any((name, tag) in self.display_tags for name in above):
                face = 'display'
            if any((name, tag) in self.plain_tags for name in above):
                face = 'plain'
            if classes & self.display_classes:
                face = 'display'
            if classes & self.plain_classes:
                face = 'plain'
        if tag not in VOID_TAGS:
            self.stack.append((tag, classes, face, ' '.join(sorted(classes & self.display_classes)) or tag))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        if self.stack and self.stack[-1][2] == 'display':
            owner = next(entry[3] for entry in reversed(self.stack) if entry[2] == 'display')
            self.found.setdefault(owner, set()).update(char for char in data if not char.isspace())


class HandbookThemeTests(unittest.TestCase):
    def test_display_subset_covers_the_text_set_in_it(self):
        spec = importlib.util.spec_from_file_location('build_fonts', WEBSITE / 'scripts/build_fonts.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        record = json.loads((THEME / 'fonts/source.json').read_text(encoding='utf-8'))
        self.assertEqual(builder.missing_characters(record), '')

    def test_display_subset_keeps_its_recorded_identity(self):
        record = json.loads((THEME / 'fonts/source.json').read_text(encoding='utf-8'))
        data = (THEME / 'fonts' / record['file']).read_bytes()
        self.assertEqual((hashlib.sha256(data).hexdigest(), len(data)), (record['sha256'], record['bytes']))
        self.assertEqual(sorted(path.name for path in (THEME / 'fonts').glob('*.woff2')), [record['file']])
        self.assertIn('SIL OPEN FONT LICENSE', (WEBSITE / record['licenseFile']).read_text(encoding='utf-8'))
        css = (THEME / 'styles/fonts.css').read_text(encoding='utf-8')
        self.assertEqual(re.findall(r'url\("\.\./fonts/([^"]+)"\)', css), [record['file']])
        self.assertIn(f'font-family: "{record["family"]}"', css)
        self.assertIn(record['licenseFile'].rsplit('/', 1)[1], (WEBSITE / 'public/THIRD_PARTY_NOTICES.txt').read_text(encoding='utf-8'))

    def test_built_pages_set_only_covered_characters_in_the_display_face(self):
        record = json.loads((THEME / 'fonts/source.json').read_text(encoding='utf-8'))
        covered = set(record['characters'])
        display, plain = face_rules()
        self.assertIn(('class', 'xk-mod__title'), display)
        self.assertIn(('class', 'xk-mod__title--plain'), plain)
        pages = sorted(BUILT.rglob('*.html'))
        self.assertGreater(len(pages), 60)
        gaps = {}
        for page in pages:
            reader = DisplayText(display, plain)
            reader.feed(page.read_text(encoding='utf-8'))
            for owner, chars in reader.found.items():
                missing = ''.join(sorted(chars - covered))
                if missing:
                    gaps.setdefault(owner, set()).update(missing)
        self.assertEqual({owner: ''.join(sorted(chars)) for owner, chars in gaps.items()}, {})

    def test_every_custom_property_the_theme_reads_is_defined(self):
        sources = [path for pattern in ('*.css', '*.vue', '*.ts') for path in THEME.rglob(pattern)]
        texts = {path: path.read_text(encoding='utf-8') for path in sources}
        defined = set()
        for text in texts.values():
            defined.update(re.findall(r'(--xk-[a-z0-9-]+)\s*:', text))
            defined.update(re.findall(r'''['"](--xk-[a-z0-9-]+)['"]''', text))
        for path, text in sorted(texts.items()):
            with self.subTest(file=path.relative_to(THEME).as_posix()):
                self.assertEqual(sorted(set(re.findall(r'var\((--xk-[a-z0-9-]+)', text)) - defined), [])

    def test_home_page_baseline_comes_from_the_project_record(self):
        config = (WEBSITE / '.vitepress/config.mts').read_text(encoding='utf-8')
        self.assertIn('docs/data/research-status.json', config)
        home = (THEME / 'components/XkHome.vue').read_text(encoding='utf-8')
        self.assertIn('xkBaseline', home)
        self.assertNotRegex(home, r'20\d\d\s*年\s*\d+\s*月\s*\d+\s*日')
        status = json.loads((ROOT / 'docs/data/research-status.json').read_text(encoding='utf-8'))
        built = (ROOT / 'docs/handbook/index.html').read_text(encoding='utf-8')
        self.assertIn(status['theory']['baselineDate'].replace('-', '.'), built)


if __name__ == '__main__':
    unittest.main()
