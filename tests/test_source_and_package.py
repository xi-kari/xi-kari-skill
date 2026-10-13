import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reader = load('read_source')
builder = load('build_install_package')


class SourceAndPackageTests(unittest.TestCase):
    def test_complete_section_includes_children_but_not_sibling(self):
        lines = ['# Book', '## 1.1 Parent', 'text', '### 1.1.1 Child', 'body', '## 1.2 Next', 'other']
        sections, _ = reader.build_index(lines)
        selected = lines[sections['1.1']['start']:sections['1.1']['end']]
        self.assertEqual(selected, lines[1:5])

    def test_overlapping_reads_do_not_duplicate_material(self):
        self.assertEqual(reader.merge_ranges([(5, 9), (1, 7), (11, 14)]), [(1, 9), (11, 14)])

    def test_unknown_section_does_not_return_neighbor(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/read_source.py'), '--section', '99.999'], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(result.stdout)

    def test_full_chunks_preserve_every_character_of_theory(self):
        text = reader.SOURCE.read_bytes().decode('utf-8-sig')
        chunks = reader.full_text_chunks(text, 6000)
        self.assertEqual(''.join(text[start:end] for start, end in chunks), text)
        self.assertEqual(chunks[0][0], 0)
        self.assertEqual(chunks[-1][1], len(text))
        self.assertTrue(all(0 < end - start <= 6000 for start, end in chunks))

    def test_chunks_handle_long_lines_unicode_and_empty_text(self):
        text = '书前\n\n' + '长表格🙂' * 200 + '\n末尾文献'
        chunks = reader.full_text_chunks(text, 27)
        self.assertEqual(''.join(text[a:b] for a, b in chunks), text)
        self.assertTrue(all(b - a <= 27 for a, b in chunks))
        self.assertEqual(reader.full_text_chunks('', 27), [])
        with self.assertRaises(ValueError):
            reader.full_text_chunks(text, 0)

    def test_out_of_range_chunk_returns_error_without_partial_text(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/read_source.py'), '--chunk', '999999'], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(result.stdout)

    def test_real_source_parts_and_nested_section(self):
        lines = reader.SOURCE.read_text(encoding='utf-8').splitlines()
        sections, parts = reader.build_index(lines)
        self.assertEqual(set(parts), set(range(1, 22)))
        self.assertLess(sections['13.11']['start'], sections['13.11.2']['start'])
        self.assertGreaterEqual(sections['13.11']['end'], sections['13.11.2']['end'])
        self.assertIn('C.12', sections)
        self.assertIn('D.32', sections)

    def test_packaged_bytes_match_and_exclude_development(self):
        with tempfile.TemporaryDirectory() as directory:
            result = builder.build(ROOT, Path(directory))
            with zipfile.ZipFile(Path(directory) / result['archive']) as zf:
                self.assertIsNone(zf.testzip())
                self.assertEqual(set(zf.namelist()), {r['path'] for r in result['files']})
                self.assertFalse(any(n.startswith(('tests/', '.github/')) for n in zf.namelist()))
                self.assertNotIn('scripts/build_install_package.py', zf.namelist())
                for name in zf.namelist():
                    self.assertEqual(zf.read(name), (ROOT / name).read_bytes())

    def test_package_rejects_path_escape_and_case_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for names in [['../outside'], ['SKILL.md', 'skill.md']]:
                (root / 'skill-package.json').write_text(json.dumps({'files': names}), encoding='utf-8')
                with self.assertRaises(ValueError):
                    builder.selected_files(root)


if __name__ == '__main__':
    unittest.main()
