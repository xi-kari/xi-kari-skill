"""Check public research data and the page's JavaScript-free fallback."""

import hashlib
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
VOID_TAGS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


class Element:
    def __init__(self, tag, attrs):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children = []

    def text(self):
        return ''.join(child.text() if isinstance(child, Element) else child for child in self.children)

    def descendants(self, tag):
        for child in self.children:
            if isinstance(child, Element):
                if child.tag == tag:
                    yield child
                yield from child.descendants(tag)


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.root = Element('document', [])
        self.stack = [self.root]
        self.elements = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        node = Element(tag, attrs)
        self.stack[-1].children.append(node)
        self.elements.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                self.stack = self.stack[:index]
                return

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def find(self, attribute, value=None):
        return [node for node in self.elements if attribute in node.attrs and (value is None or node.attrs[attribute] == value)]


class ProjectPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.status = json.loads((DOCS / 'data/research-status.json').read_text(encoding='utf-8'))
        cls.topics = json.loads((DOCS / 'data/research-topics.json').read_text(encoding='utf-8'))
        cls.manifest = json.loads((ROOT / 'source/source-manifest.json').read_text(encoding='utf-8'))
        cls.package = json.loads((ROOT / 'skill-package.json').read_text(encoding='utf-8'))
        cls.source = (ROOT / 'source' / cls.manifest['source_file']).read_bytes()
        cls.source_text = cls.source.decode('utf-8')
        cls.html = (DOCS / 'index.html').read_text(encoding='utf-8')
        cls.page = Page(cls.html)
        cls.js = (DOCS / 'assets/project.js').read_text(encoding='utf-8')

    def test_delivery_totals_and_pending_roster_agree(self):
        d = self.status['delivery']
        self.assertEqual(self.status['schemaVersion'], 1)
        self.assertEqual(len(d['groups']), 8)
        self.assertEqual(len({g['id'] for g in d['groups']}), len(d['groups']))
        self.assertEqual(sum(g['total'] for g in d['groups']), d['total'])
        self.assertEqual(sum(g['delivered'] for g in d['groups']), d['delivered'])
        self.assertEqual(d['delivered'] + d['pending'], d['total'])
        for group in d['groups']:
            self.assertGreater(group['total'], 0)
            self.assertGreaterEqual(group['delivered'], 0)
            self.assertLessEqual(group['delivered'], group['total'])
        pending = d['pendingItems']
        self.assertEqual(len(pending), d['pending'])
        self.assertEqual(len({item['id'] for item in pending}), len(pending))
        for item in pending:
            self.assertTrue(item['title'] and item['detail'])

    def test_current_snapshot_records_author_confirmed_completion(self):
        d = self.status['delivery']
        self.assertEqual((d['delivered'], d['total'], d['pending']), (620, 620, 0))
        self.assertEqual(d['pendingItems'], [])
        self.assertTrue(all(group['delivered'] == group['total'] for group in d['groups']))
        self.assertEqual(d['snapshotDate'], '2026-10-14')
        self.assertEqual(d['provenance']['kind'], 'author-confirmation')
        self.assertEqual(d['provenance']['confirmedAt'], '2026-10-14')
        self.assertNotIn('completedAt', d)
        for field in ('forwardDelivered', 'reverseDelivered', 'overlap'):
            self.assertNotIn(field, d)
        self.assertGreaterEqual(self.status['updatedAt'], d['snapshotDate'])

    def test_previous_delivery_snapshot_remains_historical(self):
        archive = 'data/history/research-status-20261013.json'
        old = json.loads((DOCS / archive).read_text(encoding='utf-8'))['delivery']
        self.assertEqual((old['delivered'], old['total'], old['pending']), (612, 620, 8))
        self.assertEqual(old['forwardDelivered'] + old['reverseDelivered'] - old['overlap'], old['delivered'])
        self.assertEqual(old['snapshotDate'], '2026-10-13')
        self.assertIn('./' + archive, [node.attrs.get('href') for node in self.page.elements])
        self.assertNotIn('612 / 620', self.html)

    def test_manuscript_identity_matches_packaged_source(self):
        theory = self.status['theory']
        self.assertEqual(theory['sha256'], hashlib.sha256(self.source).hexdigest())
        for key in ('title', 'author', 'sha256'):
            self.assertEqual(theory[key], self.manifest[key])
        self.assertEqual(theory['version'], self.manifest['theory_version'])
        self.assertEqual((theory['mainParts'], theory['appendices'], theory['domains']), (16, 4, 32))

    def test_directory_uses_source_domain_titles_and_preserved_topics(self):
        titles = dict(re.findall(r'^## D\.(\d{2})\s+(.+)$', self.source_text, re.M))
        modules = self.topics['modules']
        self.assertEqual(len(modules), len(titles))
        self.assertEqual(len(modules), 32)
        self.assertEqual(len({m['id'] for m in modules}), 32)
        outline = (DOCS / 'data/research-outline.md').read_text(encoding='utf-8')
        flat = [topic for module in modules for topic in module['topics']]
        self.assertEqual(len(flat), 296)
        self.assertEqual(len({t['id'] for t in flat}), 296)
        for module in modules:
            self.assertEqual(module['title'], titles[module['id']])
            self.assertIn(f"## D.{module['id']} {module['title']}", outline)
            for topic in module['topics']:
                self.assertTrue(topic['id'].startswith(module['id'] + '.'))
                self.assertIn(f"{topic['id']} {topic['title']}", self.source_text)
                self.assertIn(f"**{topic['id']} {topic['title']}**：{topic['question']}", outline)

    def test_static_fallback_matches_delivery_json(self):
        d = self.status['delivery']
        rows = {node.attrs['data-delivery-group']: node for node in self.page.find('data-delivery-group')}
        self.assertEqual(set(rows), {g['id'] for g in d['groups']})
        for group in d['groups']:
            row = rows[group['id']]
            self.assertIn(group['title'], row.text())
            cells = list(row.descendants('td'))
            self.assertEqual(cells[0].text(), f"{group['delivered']} / {group['total']}")
            self.assertEqual(cells[1].text(), str(group['total'] - group['delivered']))
            progress = next(row.descendants('progress'))
            self.assertEqual(progress.attrs['value'], str(group['delivered']))
            self.assertEqual(progress.attrs['max'], str(group['total']))
            self.assertIn(group['title'], progress.attrs['aria-label'])
        pending = {node.attrs['data-pending-id']: node for node in self.page.find('data-pending-id')}
        self.assertEqual(set(pending), {item['id'] for item in d['pendingItems']})
        self.assertEqual('hidden' in self.page.find('data-pending-section')[0].attrs, d['pending'] == 0)
        for item in d['pendingItems']:
            self.assertIn(item['title'], pending[item['id']].text())
            self.assertIn(item['detail'], pending[item['id']].text())
        meter = self.page.find('data-delivery-meter')[0]
        self.assertEqual(meter.attrs['aria-valuenow'], str(d['delivered']))
        self.assertEqual(meter.attrs['aria-valuemax'], str(d['total']))
        for attr, date in [('data-snapshot-date', d['snapshotDate']), ('data-page-date', self.status['updatedAt'])]:
            node = self.page.find(attr)[0]
            self.assertEqual(node.attrs['datetime'], date)
            self.assertEqual(node.text(), date.replace('-', '.'))

    def test_historical_record_is_separate_from_current_delivery(self):
        history = json.loads((DOCS / 'data/research-progress.json').read_text(encoding='utf-8'))
        self.assertTrue(history['updatedAt'].startswith('2026-10-01'))
        known = {t['id'] for m in self.topics['modules'] for t in m['topics']}
        self.assertLessEqual(set(history['completed']), known)
        self.assertIn('./data/research-progress.json', [node.attrs.get('href') for node in self.page.elements])
        self.assertNotIn('requestJson(\'./data/research-progress.json\')', self.js)
        for old in ('api/research-progress', 'api/project-editor', 'data-editor-toggle', 'data-status-filter', 'topic-check'):
            self.assertNotIn(old, self.html + self.js)
        self.assertIn('32 个领域', self.page.find('data-research-scope')[0].text())
        self.assertIn('296 个专题', self.page.find('data-research-scope')[0].text())

    def test_page_links_and_release_match_current_package(self):
        ids = [node.attrs['id'] for node in self.page.find('id')]
        self.assertEqual(len(ids), len(set(ids)))
        links = [node.attrs.get('href', '') for node in self.page.elements if node.tag == 'a']
        for link in links:
            if link.startswith('#'):
                self.assertIn(link[1:], ids)
        self.assertIn('#usage', links)
        self.assertIn('#research', links)
        version = self.package['version']
        self.assertIn(f'https://github.com/xi-kari/xi-kari-skill/releases/download/v{version}/xi-kari-skill-{version}-windows.zip', links)
        self.assertIn(self.status['theory']['sourceUrl'], links)
        self.assertIn('https://github.com/xi-kari/xi-kari-skill/blob/main/docs/INSTALL.md', links)
        self.assertNotIn('https://github.com/xi-kari/xi-kari-skill#安装', links)
        self.assertIn('Windows', self.html)

    def test_route_table_matches_skill_routing(self):
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        routes = {m.group(1): m for m in re.finditer(r'^\| (R\d) ([^|]+?) \| [^|]+ \| ([^|]+) \| ([^|]+) \|$', skill, re.M)}
        self.assertEqual(sorted(routes), [f'R{n}' for n in range(1, 9)])
        rows = {node.attrs['data-route']: node for node in self.page.elements if node.tag == 'tr' and 'data-route' in node.attrs}
        self.assertEqual(set(rows), set(routes))
        for route, match in routes.items():
            with self.subTest(route=route):
                row = rows[route]
                self.assertEqual(row.attrs['data-name'], match.group(2).strip())
                self.assertEqual([leg.rstrip('?') for leg in row.attrs['data-legs'].split()], re.findall(r'M\d+', match.group(3)))
                self.assertIn(re.split(r'[，；]', match.group(4).strip())[0], row.text())
        asked = [node.attrs['data-route'] for node in self.page.elements if node.tag == 'button' and 'data-route' in node.attrs]
        self.assertEqual(asked, sorted(routes))

    def test_module_list_matches_skill_modules(self):
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        modules = re.findall(r'^\| \[(M\d+) ([^\]]+)\]\(modules/([a-z-]+)/MODULE\.md\) \|', skill, re.M)
        self.assertEqual([code for code, _, _ in modules], [f'M{n}' for n in range(11)])
        items = [node for node in self.page.elements if node.tag == 'li' and 'data-module' in node.attrs]
        self.assertEqual([node.attrs['data-module'] for node in items], [code for code, _, _ in modules])
        for (code, name, folder), node in zip(modules, items):
            with self.subTest(module=code):
                self.assertEqual(next(node.descendants('h3')).text(), name)
                self.assertTrue(next(node.descendants('a')).attrs['href'].endswith(f'/modules/{folder}/MODULE.md'))
                self.assertTrue((ROOT / 'modules' / folder / 'MODULE.md').is_file())

    def test_source_facts_on_the_page_match_the_manuscript(self):
        baseline = self.page.find('data-baseline-date')[0]
        self.assertEqual(baseline.attrs['datetime'], self.status['theory']['baselineDate'])
        self.assertEqual(baseline.text(), self.status['theory']['baselineDate'].replace('-', '.'))
        quotes = [node for node in self.page.elements if 'song' in node.attrs.get('class', '').split()]
        self.assertTrue(quotes)
        for quote in quotes:
            self.assertIn(quote.text().strip(), self.source_text)
        parts = [node for node in self.page.find('data-parts')[0].descendants('a')]
        self.assertEqual(len(parts), self.status['theory']['mainParts'] + self.status['theory']['appendices'])
        contents = re.findall(r'^\[(?:第.+?部分|附录[A-D])[\s　]*(.+?)\]\(#part_\d+\)$', self.source_text, re.M)
        self.assertEqual([re.sub(r'^[0-9A-D]+', '', node.text()) for node in parts], contents)

    def test_page_assets_keep_their_recorded_identity(self):
        provenance = json.loads((DOCS / 'assets/provenance.json').read_text(encoding='utf-8'))
        for item in provenance['outputs']['files'] + [provenance['socialCard']]:
            with self.subTest(file=item['file']):
                self.assertEqual(hashlib.sha256((DOCS / 'assets' / item['file']).read_bytes()).hexdigest(), item['sha256'])
        fonts = json.loads((DOCS / 'assets' / provenance['fonts']['record']).read_text(encoding='utf-8'))
        for face in fonts['faces'].values():
            with self.subTest(font=face['file']):
                data = (DOCS / 'assets/fonts' / face['file']).read_bytes()
                self.assertEqual((hashlib.sha256(data).hexdigest(), len(data)), (face['sha256'], face['bytes']))
        self.assertIn('SIL OPEN FONT LICENSE', (DOCS / 'assets' / provenance['fonts']['license']).read_text(encoding='utf-8'))
        css = (DOCS / 'assets/project.css').read_text(encoding='utf-8')
        local = [node.attrs[key] for node in self.page.elements for key in ('src', 'href') if node.attrs.get(key, '').startswith('./assets/')]
        local += ['./assets/' + path for path in re.findall(r'url\("\./([^"]+)"\)', css)]
        local.append('./assets/' + next(node.attrs['content'] for node in self.page.elements if node.attrs.get('property') == 'og:image').rsplit('/assets/', 1)[1])
        self.assertGreater(len(local), 6)
        for path in local:
            with self.subTest(asset=path):
                self.assertTrue((DOCS / path).is_file())

    def test_bundled_fonts_cover_the_text_set_in_them(self):
        spec = importlib.util.spec_from_file_location('build_page_fonts', ROOT / 'website/scripts/build_page_fonts.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        record = json.loads((DOCS / 'assets/fonts/source.json').read_text(encoding='utf-8'))
        self.assertEqual([page.name for page in builder.PAGES], ['index.html', '404.html'])
        for page in builder.PAGES:
            with self.subTest(page=page.name):
                self.assertEqual(builder.missing_characters(page.read_text(encoding='utf-8'), record), {})

    def test_not_found_page_leads_back_into_the_site(self):
        lost = Page((DOCS / '404.html').read_text(encoding='utf-8'))
        self.assertEqual([node.attrs['content'] for node in lost.find('name', 'robots')], ['noindex'])
        links = [node.attrs['href'] for node in lost.elements if node.tag == 'a' and node.attrs.get('href', '').startswith('/')]
        self.assertEqual(sorted(set(links)), ['/xi-kari-skill/', '/xi-kari-skill/handbook/'])
        local = [node.attrs[key] for node in lost.elements for key in ('src', 'href') if node.attrs.get(key, '').startswith('/xi-kari-skill/assets/')]
        self.assertEqual(sorted(local), ['/xi-kari-skill/assets/favicon.svg', '/xi-kari-skill/assets/project.css'])
        for path in local:
            with self.subTest(asset=path):
                self.assertTrue((DOCS / path.removeprefix('/xi-kari-skill/')).is_file())
        script = ''.join(node.text() for node in lost.elements if node.tag == 'script')
        self.assertIn("'/xi-kari-skill/handbook/'", script)
        self.assertTrue((DOCS / 'handbook/404.html').is_file())
        self.assertEqual(len(list(lost.root.descendants('h1'))), 1)

    def test_public_page_does_not_embed_machine_specific_locations(self):
        for relative in ('index.html', 'assets/project.js', 'assets/provenance.json', 'assets/fonts/source.json', 'data/research-status.json', 'data/research-topics.json', 'data/research-outline.md'):
            with self.subTest(file=relative):
                text = (DOCS / relative).read_text(encoding='utf-8')
                self.assertNotRegex(text, r'(?<![A-Za-z])[A-Za-z]:[/\\]|file://|xi-kari-runs|threadId|run-2026')


if __name__ == '__main__':
    unittest.main()
