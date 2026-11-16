"""Keep complete lesson translations bound to the Chinese content they translate."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / 'website'


def digest(data):
    return hashlib.sha256(data).hexdigest()


class CompleteEnglishLessonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chinese = json.loads((WEBSITE / 'content/section-lessons.json').read_text(encoding='utf-8'))['lessons']
        overrides = json.loads((WEBSITE / 'content/lesson-overrides.json').read_text(encoding='utf-8'))['lessons']
        for key, fields in overrides.items():
            cls.chinese[key] = {**cls.chinese.get(key, {}), **fields}
        cls.english = json.loads((WEBSITE / 'content/en/section-lessons.json').read_text(encoding='utf-8'))['lessons']
        cls.binding = json.loads((WEBSITE / 'content/en/translation-manifest.json').read_text(encoding='utf-8'))
        cls.english_units = {item['lesson_key']: item for item in json.loads((WEBSITE / 'content/en/reading-units.json').read_text(encoding='utf-8'))['units']}

    def test_every_chinese_lesson_has_an_english_counterpart_in_the_reader(self):
        self.assertEqual(len(self.chinese), 421)
        self.assertEqual(set(self.english), set(self.chinese))
        self.assertEqual(set(self.binding['reading_units']), set(self.chinese))
        source_map = json.loads((WEBSITE / 'public/en/source-map.json').read_text(encoding='utf-8'))
        self.assertEqual(set(source_map['annotation_sections']), set(self.chinese))
        self.assertLessEqual(set(self.english), set(self.english_units))

    def test_translations_remain_bound_to_each_chinese_lesson_and_the_reference_text(self):
        for record in self.binding['sources'] + [self.binding['translation']]:
            self.assertEqual(digest((WEBSITE / record['path']).read_bytes()), record['sha256'], record['path'])
        source_hash = digest((ROOT / 'source/en/Xikari-On-Conditions-Structure-and-Transformation.md').read_bytes())
        for key, chinese in self.chinese.items():
            english = self.english[key]
            expected = digest(json.dumps(chinese, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())
            self.assertEqual(english['translationOf']['lesson_sha256'], expected, key)
            self.assertEqual(english['translationOf']['source_sha256'], chinese['sourceHash'], key)
            self.assertEqual(english['sourceHash'], source_hash, key)
            self.assertEqual(english['sourceRefs'][0]['startLine'], self.english_units[key]['source_start_line'], key)
            self.assertEqual(english['sourceRefs'][0]['endLine'], self.english_units[key]['source_end_line'], key)

    def test_full_paragraphs_examples_answers_and_source_records_are_not_dropped(self):
        def compare(original, translated, location):
            if isinstance(original, dict):
                self.assertIsInstance(translated, dict, location)
                self.assertLessEqual(set(original), set(translated), location)
                for field, value in original.items():
                    if field not in {'sourceHash', 'sourceRefs'}:
                        compare(value, translated[field], location + '/' + field)
            elif isinstance(original, list):
                self.assertIsInstance(translated, list, location)
                self.assertEqual(len(original), len(translated), location)
                for index, (left, right) in enumerate(zip(original, translated)):
                    compare(left, right, location + '/' + str(index))
            elif isinstance(original, str):
                self.assertIsInstance(translated, str, location)
                if original.strip():
                    self.assertTrue(translated.strip(), location)
            else:
                self.assertEqual(original, translated, location)

        for key, original in self.chinese.items():
            compare(original, self.english[key], key)

    def test_quotes_are_actual_author_reference_text_and_archives_keep_their_identity(self):
        source = (ROOT / 'source/en/Xikari-On-Conditions-Structure-and-Transformation.md').read_text(encoding='utf-8')
        for key, original in self.chinese.items():
            translated = self.english[key]
            for quote in translated.get('sourceQuotes', []):
                self.assertIn(quote['text'], source, key)
            for field in ['taskId', 'lecturePath', 'sourcesPath', 'sourceSlicePath', 'diagramsPath', 'diagramPath', 'sourceSliceHash']:
                self.assertEqual(translated.get(field), original.get(field), (key, field))
            self.assertEqual([figure.get('path') for figure in translated.get('figures', [])],
                             [figure.get('path') for figure in original.get('figures', [])], key)
            self.assertEqual([item.get('id') for item in translated['sources']],
                             [item.get('id') for item in original['sources']], key)
            self.assertEqual([item.get('url') for item in translated['sources']],
                             [item.get('url') for item in original['sources']], key)

    @unittest.skipUnless(shutil.which('node'), 'Node.js is not installed')
    def test_reader_rejects_a_stale_translation_after_chinese_content_changes(self):
        loader = (WEBSITE / 'scripts/lesson_data.mjs').as_uri()
        script = 'import {loadLessons} from %s; try { console.log(JSON.stringify(loadLessons(process.argv[1], "en"))) } catch (error) { console.log(JSON.stringify({error: error.message})) }' % json.dumps(loader)
        with tempfile.TemporaryDirectory(prefix='xikari-translation-binding-') as directory:
            site = Path(directory)
            (site / 'content/en').mkdir(parents=True)
            chinese = b'{"lessons":{"1.1":{"title":"Chinese baseline"}}}'
            english = b'{"lessons":{"1.1":{"title":"English translation"}}}'
            (site / 'content/section-lessons.json').write_bytes(chinese)
            (site / 'content/en/section-lessons.json').write_bytes(english)
            binding = {'sources': [{'path': 'content/section-lessons.json', 'sha256': digest(chinese)}],
                       'translation': {'path': 'content/en/section-lessons.json', 'sha256': digest(english)}}
            (site / 'content/en/translation-manifest.json').write_text(json.dumps(binding), encoding='utf-8')

            def load():
                result = subprocess.run(['node', '--input-type=module', '-e', script, str(site)], capture_output=True, text=True, encoding='utf-8', check=True)
                return json.loads(result.stdout)

            self.assertEqual(load(), {'1.1': {'title': 'English translation'}})
            (site / 'content/section-lessons.json').write_bytes(chinese.replace(b'baseline', b'updated'))
            self.assertIn('no longer matches', load()['error'])


if __name__ == '__main__':
    unittest.main()
