"""Check public research data and the page's JavaScript-free fallback."""

import hashlib
from html.parser import HTMLParser
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
        self.assertEqual(d['forwardDelivered'] + d['reverseDelivered'] - d['overlap'], d['delivered'])
        for group in d['groups']:
            self.assertGreater(group['total'], 0)
            self.assertGreaterEqual(group['delivered'], 0)
            self.assertLessEqual(group['delivered'], group['total'])
        pending = d['pendingItems']
        self.assertEqual(len(pending), d['pending'])
        self.assertEqual(len({item['id'] for item in pending}), len(pending))
        for item in pending:
            self.assertTrue(item['title'] and item['detail'])

    def test_current_snapshot_names_all_eight_unfinished_tasks(self):
        d = self.status['delivery']
        self.assertEqual((d['delivered'], d['total'], d['pending']), (612, 620, 8))
        self.assertEqual({p['id'] for p in d['pendingItems']}, {'Q-01', 'Q-02', 'D-18', 'D-30', 'D-31', 'D-32', 'FINAL-SYN', 'FINAL-AUDIT'})
        self.assertEqual(d['snapshotDate'], '2026-10-13')
        self.assertGreaterEqual(self.status['updatedAt'], d['snapshotDate'])

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
        self.assertIn('理论验证率', self.page.find('data-delivery-boundary')[0].text())

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
        self.assertIn('Windows', self.html)

    def test_original_artwork_and_icon_counts_are_preserved(self):
        marks = self.page.find('data-field-mark')
        self.assertEqual(len(marks), 96)
        self.assertEqual(sum(m.attrs.get('data-field-compact') == 'true' for m in marks), 48)
        masks = [node for node in self.page.elements if node.tag == 'mask']
        self.assertEqual(sum('signature-latin-' in node.attrs.get('id', '') for node in masks), 23)
        self.assertEqual(sum('signature-dawn-' in node.attrs.get('id', '') for node in masks), 3)
        provenance = json.loads((DOCS / 'assets/provenance.json').read_text(encoding='utf-8'))['wallpaper']
        self.assertEqual(hashlib.sha256((DOCS / 'assets' / provenance['file']).read_bytes()).hexdigest(), provenance['sha256'])

    def test_public_page_does_not_embed_machine_specific_locations(self):
        for relative in ('index.html', 'assets/project.js', 'data/research-status.json', 'data/research-topics.json', 'data/research-outline.md'):
            with self.subTest(file=relative):
                text = (DOCS / relative).read_text(encoding='utf-8')
                self.assertNotRegex(text, r'(?<![A-Za-z])[A-Za-z]:[/\\]|file://|xi-kari-runs|threadId|run-2026')


if __name__ == '__main__':
    unittest.main()
