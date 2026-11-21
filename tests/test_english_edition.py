import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CJK = re.compile(r'[㐀-鿿]')


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


edition = load('build_english_edition')
reader = load('read_source')
answer = load('render_answer')
docx = load('render_docx')


def run(*args):
    return subprocess.run([sys.executable, str(ROOT / 'scripts/read_source.py'), *args],
                          capture_output=True, text=True, encoding='utf-8')


class EnglishEditionTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / 'source/en/source-manifest.json').read_text(encoding='utf-8'))
        self.path = ROOT / 'source/en' / self.manifest['source_file']
        self.text = self.path.read_text(encoding='utf-8')

    def test_edition_translates_the_current_source_and_aligns_with_it(self):
        result = edition.check()
        self.assertTrue(result['ok'], result['problems'])
        zh = json.loads((ROOT / 'source/source-manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(result['relation'], 'current')
        self.assertEqual(self.manifest['translates']['sha256'], zh['sha256'])
        self.assertEqual((result['sections'], result['parts']), (397, 21))
        self.assertEqual(result['blocks'], self.manifest['alignment']['blocks'])
        self.assertEqual(result['blocks'], len(edition.blocks(reader.SOURCE.read_text(encoding='utf-8'))))

    def test_translation_relation_accepts_only_the_recorded_wording_predecessor(self):
        zh = {'sha256': 'b' * 64, 'wording_revision_of': {'sha256': 'a' * 64}}
        self.assertEqual(reader.translation_relation(zh, {'translates': {'sha256': 'b' * 64}}), 'current')
        self.assertEqual(reader.translation_relation(zh, {'translates': {'sha256': 'a' * 64}}),
                         'wording-predecessor')
        self.assertIsNone(reader.translation_relation(zh, {'translates': {'sha256': 'c' * 64}}))
        self.assertIsNone(reader.translation_relation({'sha256': 'b' * 64}, {'translates': {'sha256': 'a' * 64}}))
        self.assertIsNone(reader.translation_relation(zh, {}))

    def test_reworded_source_keeps_sections_but_skips_paragraph_comparison(self):
        zh = self.text.replace('\n\n', '\n\nextra\n\n', 1)
        strict = edition.alignment(zh, self.text)
        loose = edition.alignment(zh, self.text, compare_blocks=False)
        self.assertTrue(any('paragraph blocks' in problem for problem in strict['problems']))
        self.assertFalse(any('paragraph blocks' in problem for problem in loose['problems']))
        self.assertEqual(loose['blocks'], strict['blocks'])

    def test_every_section_and_part_shares_its_identifier_and_order(self):
        zh_sections, zh_parts = reader.build_index(reader.SOURCE.read_text(encoding='utf-8').splitlines())
        en_sections, en_parts = reader.build_index(self.text.splitlines())
        self.assertEqual(list(zh_sections), list(en_sections))
        self.assertEqual(sorted(zh_parts), sorted(en_parts))

    def test_edition_is_english_prose_without_glosses(self):
        body = edition.NOTE_DEF.sub('', self.text)
        self.assertEqual(edition.GLOSS.findall(body), [])
        self.assertNotRegex(body, r'\]\(#[^)]*\) \(in Chinese\)')
        self.assertNotIn('](/works/', body)
        self.assertIn('`A* = <所指的行动者，观察窗，', body)
        self.assertIn('M(SP0→SP1)=<保留变量, 改变变量, 丢失变量, 变换方式,', body)
        self.assertIn('The full tuple in English is `A* = <the actor referred to, observation window,', self.text)
        for line in body.splitlines():
            if line.startswith(('#', '|')) and CJK.search(line):
                self.fail(f'Chinese left in a heading or table row: {line[:80]}')

    def test_headings_follow_the_current_chinese_and_keep_codes_only_at_the_end(self):
        self.assertIn('## 3.3 Effective Feedback (D2)', self.text)
        self.assertNotIn('## 3.3 D2 ', self.text)
        self.assertIn('## 1.1 Four Kinds of Output and Eight Layers of Responsibility', self.text)

    def test_translator_notes_resolve_and_tuples_keep_the_current_chinese_wording(self):
        notes = re.findall(r'(?m)^\[\^(tn-[^\]]+)\]:', self.text)
        self.assertTrue(notes)
        self.assertEqual(len(notes), len(set(notes)))
        self.assertEqual(set(re.findall(r'\[\^(tn-[^\]]+)\](?!:)', self.text)), set(notes))
        for _, chinese, _, _ in edition.TUPLES:
            self.assertEqual(self.text.count(chinese), 1, chinese[:24])
        # Notes that only explained a word the current Chinese no longer uses are gone.
        self.assertEqual([note for note in notes if note.startswith(('tn-contract', 'tn-protocol'))], [])

    def test_revision_names_the_edition_it_revises_and_retains_legal_material(self):
        revision = self.manifest['revision_of']
        self.assertEqual(revision, {
            'edition_sha256': '51795bb7988f2669a324a52666c320cfba1382f597f7b5c6a1431844572da1fb',
            'translates': '6ef2e508474d4ac1ad07d7e4e068955342c405b5f680afcfc40d68cca3d0149c',
            'supplied_manuscript_sha256': 'f59bcdb483027736ef973b43ffc0c0ce37d9cb5e67ab3f05c6c67d22a62e65a1'})
        self.assertNotIn('imported_from', self.manifest)
        self.assertFalse((ROOT / 'source/en/upstream').exists())
        body, notices = edition.edition_body(self.text)
        self.assertEqual(notices, self.manifest['non_body_material'])
        self.assertEqual([notice['kind'] for notice in notices], ['copyright_notice', 'copyright_and_license'])
        self.assertIn('English translation of v3.0 (November 2026)', self.text)
        self.assertIn('Translated from the Chinese v3.0 text:', self.text)
        # The edition before this one, and the Chinese text it followed, stay on record.
        self.assertEqual(self.manifest['previous_edition'], {
            'edition_sha256': 'fcf100a5c8688d1e0337c52750ce3ad21fb5dbcc250f97946602ce094345f825',
            'translates': '2128af7cfa4c63b58207521a375aa34c2aea230d47e1c04a5afec3334e290d28'})
        self.assertIn('## Copyright and License', self.text)
        self.assertNotIn('## Copyright and License', body)

    def test_edition_notices_do_not_hide_missing_or_extra_theory_body(self):
        zh = reader.SOURCE.read_text(encoding='utf-8')
        body, _ = edition.edition_body(self.text)
        paragraph = next(block for block in edition.blocks(body) if block.startswith('Some relations specify'))
        result = edition.alignment(zh, self.text.replace(paragraph, '', 1))
        self.assertTrue(result['problems'])
        injected = self.text.replace('### MIT License', '## 99.1 Extra theory section\n\n### MIT License', 1)
        self.assertTrue(edition.alignment(zh, injected)['problems'])

    def test_check_reports_a_stale_translation_without_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / 'source', root / 'source')
            manifest_path = root / 'source/en/source-manifest.json'
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            manifest['translates']['sha256'] = '0' * 64
            manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
            before = {path: path.read_bytes() for path in root.rglob('*') if path.is_file()}
            saved = (edition.ROOT, edition.ZH_MANIFEST, edition.EN_DIR, edition.EN_MANIFEST)
            try:
                edition.ROOT, edition.ZH_MANIFEST = root, root / 'source/source-manifest.json'
                edition.EN_DIR, edition.EN_MANIFEST = root / 'source/en', manifest_path
                result = edition.check()
            finally:
                edition.ROOT, edition.ZH_MANIFEST, edition.EN_DIR, edition.EN_MANIFEST = saved
            self.assertFalse(result['ok'])
            self.assertTrue(any('different Chinese source' in problem for problem in result['problems']))
            self.assertEqual(before, {path: path.read_bytes() for path in root.rglob('*') if path.is_file()})

    def test_check_rejects_changed_source_bytes_and_stale_alignment_counts(self):
        for damage in ('source_bytes', 'alignment_counts', 'legal_material'):
            with self.subTest(damage=damage), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                shutil.copytree(ROOT / 'source', root / 'source')
                manifest_path = root / 'source/en/source-manifest.json'
                if damage == 'source_bytes':
                    source_path = root / 'source' / self.manifest['translates']['source_file']
                    source_path.write_bytes(source_path.read_bytes().replace('v2'.encode(), 'v3'.encode(), 1))
                    expected = 'Chinese source bytes differ'
                elif damage == 'alignment_counts':
                    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
                    manifest['alignment']['sections'] -= 1
                    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
                    expected = 'alignment counts differ'
                else:
                    # A changed notice must not pass because notices are left out of body alignment.
                    source_path = root / 'source/en' / self.manifest['source_file']
                    data = source_path.read_text(encoding='utf-8').replace(
                        'Original text © 2026', 'Original text © 2025', 1).encode('utf-8')
                    source_path.write_bytes(data)
                    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
                    manifest['sha256'], manifest['bytes'] = edition.sha256(data), len(data)
                    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
                    expected = 'copyright and license material differs'
                before = {path: path.read_bytes() for path in root.rglob('*') if path.is_file()}
                saved = (edition.ROOT, edition.ZH_MANIFEST, edition.EN_DIR, edition.EN_MANIFEST)
                try:
                    edition.ROOT, edition.ZH_MANIFEST = root, root / 'source/source-manifest.json'
                    edition.EN_DIR, edition.EN_MANIFEST = root / 'source/en', manifest_path
                    result = edition.check()
                finally:
                    edition.ROOT, edition.ZH_MANIFEST, edition.EN_DIR, edition.EN_MANIFEST = saved
                self.assertFalse(result['ok'])
                self.assertTrue(any(expected in problem for problem in result['problems']))
                self.assertEqual(before, {path: path.read_bytes() for path in root.rglob('*') if path.is_file()})

    def test_glossary_keeps_the_core_distinctions(self):
        glossary = (ROOT / 'references/glossary-en.md').read_text(encoding='utf-8')
        for chinese, english in [('圈层', 'circle'), ('推演', 'projection'), ('条件前瞻', 'conditional foresight'),
                                 ('有限选择', 'bounded choice'), ('授权', 'authorization'), ('处置权', 'authority to act'),
                                 ('修复', 'repair'), ('恢复', 'recovery'), ('简单基线', 'simple baseline'),
                                 ('分组增益', 'grouping gain'), ('对象事实', 'object facts'),
                                 ('构成关系', 'constitutive relation')]:
            self.assertRegex(glossary, rf'(?m)^\| {re.escape(chinese)} \| {re.escape(english)} \|')

    def test_english_resources_are_installed(self):
        files = set(json.loads((ROOT / 'skill-package.json').read_text(encoding='utf-8'))['files'])
        for name in ('source/en/source-manifest.json', 'source/en/' + self.manifest['source_file'],
                     'references/english.md', 'references/glossary-en.md'):
            self.assertIn(name, files)
        self.assertNotIn('scripts/build_english_edition.py', files)
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        description = re.search(r'(?m)^description: (.+)$', skill).group(1)
        self.assertIn('English', description)
        for name in ('Xikari Skill', 'Xi-Kari Skill', 'xi-kari-skill', '$xi-kari-skill', '/xi-kari-skill'):
            self.assertIn(name, description)
        self.assertLessEqual(len(description), 1024)
        self.assertIn('references/english.md', skill)

    def test_install_package_binds_the_english_edition(self):
        builder = load('build_install_package')
        with tempfile.TemporaryDirectory() as temporary:
            result = builder.build(ROOT, Path(temporary))
            self.assertEqual(result['english_edition_sha256'], self.manifest['sha256'])
            with zipfile.ZipFile(Path(temporary) / result['archive']) as archive:
                packaged = archive.read('xi-kari-skill/source/en/' + self.manifest['source_file'])
            self.assertEqual(packaged, self.path.read_bytes())


class EnglishReaderTests(unittest.TestCase):
    def test_lang_en_reads_the_same_section_in_english(self):
        result = run('--lang', 'en', '--section', '1.1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Xikari-On-Conditions-Structure-and-Transformation.md', result.stdout)
        self.assertIn('## 1.1 Four Kinds of Output and Eight Layers of Responsibility', result.stdout)
        self.assertIsNone(CJK.search(result.stdout))

    def test_parallel_prints_chinese_then_english(self):
        result = run('--parallel', '--section', '4.17')
        self.assertEqual(result.returncode, 0, result.stderr)
        chinese = result.stdout.index('[Xikari-条件结构与转化论.md')
        english = result.stdout.index('[Xikari-On-Conditions-Structure-and-Transformation.md')
        self.assertLess(chinese, english)
        self.assertEqual(run('--parallel').returncode, 2)

    def test_english_search_and_check(self):
        result = run('--lang', 'en', '--search', 'action ceiling', '--limit', '1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('1 matching line(s)', result.stdout)
        check = run('--check')
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        report = json.loads(check.stdout)
        self.assertTrue(report['source_matches_manifest'])
        self.assertTrue(report['english']['ok'])


class EnglishOutputTests(unittest.TestCase):
    SAMPLE = '# Why Rules Fail\n\nA claim with a note.[^a]\n\n| Option | Cost |\n| --- | --- |\n| A | 1 |\n\n![](missing.png)\n\n[^a]: The note.\n'

    def test_reading_page_interface_is_english(self):
        html = answer.render_document(self.SAMPLE, lang='en')
        self.assertIn('<html lang="en"', html)
        visible = re.sub(r'<(script|style)>.*?</\1>', '', html, flags=re.S)
        self.assertIsNone(CJK.search(visible), CJK.findall(visible)[:5])
        self.assertIn('<h2>Footnotes</h2>', visible)
        self.assertIn('Back to reference 1', visible)
        self.assertRegex(visible, r'About \d+ words; about 1 minute to read\.')

    def test_chinese_reading_page_is_unchanged_by_default(self):
        html = answer.render_document(self.SAMPLE)
        self.assertIn('<html lang="zh-CN"', html)
        self.assertIn('<h2>脚注</h2>', html)
        with self.assertRaises(ValueError):
            answer.render_document(self.SAMPLE, lang='fr')

    def test_word_labels_and_language_are_english(self):
        parts, unsupported = docx.build_document(self.SAMPLE, None, None, 'en')
        document = parts['word/document.xml'].decode('utf-8')
        self.assertIsNone(CJK.search(document))
        self.assertIn('>Footnotes<', document)
        self.assertIn('<w:lang w:val="en-US"/>', parts['word/styles.xml'].decode('utf-8'))
        self.assertTrue(all(CJK.search(note) is None for note in unsupported))
        chinese, _ = docx.build_document(self.SAMPLE, None, None)
        self.assertNotIn('w:lang', chinese['word/styles.xml'].decode('utf-8'))
        self.assertIn('>脚注<', chinese['word/document.xml'].decode('utf-8'))

    def test_comparison_table_labels_are_english(self):
        comparison = load('comparison')
        model = {'schema_version': 1, 'title': 'Staffing options: a teaching example', 'purpose': 'Compare two options.',
                 'fictional': True, 'assumptions': ['Demand stays flat.'], 'boundaries': ['Teaching data only.'],
                 'candidates': [{'id': 'A', 'label': 'Hire'}, {'id': 'B', 'label': 'Contract'}],
                 'dimensions': [{'id': 'cost', 'label': 'Annual cost', 'unit': 'USD', 'direction': 'lower_is_better'},
                                {'id': 'fit', 'label': 'Team fit', 'direction': 'not_orderable'}],
                 'cells': {'A': {'cost': {'basis': 'assumed', 'value': 90000},
                                 'fit': {'basis': 'observed', 'value': 'good', 'source': 'interviews'}},
                           'B': {'cost': {'basis': 'unknown', 'value': None}, 'fit': {'basis': 'assumed', 'value': True}}}}
        result = comparison.build_comparison(model, 'en')
        self.assertEqual(result['language'], 'en')
        markdown, page = comparison.render_markdown(result), comparison.render_html(result)
        visible = re.sub(r'<style>.*?</style>', '', page, flags=re.S)
        for text in (markdown, visible, comparison.render_json(result)):
            self.assertIsNone(CJK.search(text), CJK.findall(text)[:5])
        self.assertIn('| Annual cost (USD) | 90000 (Assumption) | Unknown |', markdown)
        self.assertIn('<html lang="en">', page)
        self.assertIn('How to read this table', page)
        self.assertNotIn('language', comparison.build_comparison(model))


if __name__ == '__main__':
    unittest.main()
