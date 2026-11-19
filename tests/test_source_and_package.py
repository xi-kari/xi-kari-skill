import importlib.util
import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
import re

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reader = load('read_source')
builder = load('build_install_package')


class SourceAndPackageTests(unittest.TestCase):
    def test_release_metadata_and_shipped_teaching_versions_agree(self):
        metadata = json.loads((ROOT / 'skill-package.json').read_text(encoding='utf-8'))
        project = (ROOT / 'pyproject.toml').read_text(encoding='utf-8')
        version = re.search(r'(?m)^version\s*=\s*"([^"]+)"', project).group(1)
        self.assertEqual(metadata['version'], version)
        for order in (1, 2, 3):
            record = json.loads((ROOT / f'cases/forecast-public-resignation/order-{order}.json').read_text(encoding='utf-8'))
            self.assertEqual(record['skill_version'], version)
        expected = f'xi-kari-skill-{version}-windows.zip'
        self.assertIn(expected, (ROOT / 'docs/INSTALL.md').read_text(encoding='utf-8'))

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
            theory_manifest = json.loads((ROOT / 'source/source-manifest.json').read_text(encoding='utf-8'))
            protected = {'source/' + theory_manifest['source_file']}
            english_manifest_path = ROOT / 'source/en/source-manifest.json'
            if english_manifest_path.exists():
                english_manifest = json.loads(english_manifest_path.read_text(encoding='utf-8'))
                protected.add('source/en/' + english_manifest['source_file'])
                if 'imported_from' in english_manifest:
                    protected.add('source/en/' + english_manifest['imported_from']['source_file'])
            with zipfile.ZipFile(Path(directory) / result['archive']) as zf:
                self.assertIsNone(zf.testzip())
                self.assertEqual(result['archive_root'], 'xi-kari-skill')
                prefix = result['archive_root'] + '/'
                self.assertEqual(set(zf.namelist()), {prefix + r['path'] for r in result['files']})
                self.assertFalse(any(n.startswith((prefix + 'tests/', prefix + '.github/')) for n in zf.namelist()))
                self.assertNotIn(prefix + 'scripts/build_install_package.py', zf.namelist())
                for name in zf.namelist():
                    relative = name.removeprefix(prefix)
                    row = next(x for x in result['files'] if x['path'] == relative)
                    self.assertEqual(hashlib.sha256(zf.read(name)).hexdigest(), row['sha256'])
                    raw = (ROOT / relative).read_bytes()
                    if not relative.endswith('.woff2') and relative not in protected:
                        raw = raw.replace(b'\r\n', b'\n')
                    self.assertEqual(zf.read(name), raw)

    def imported_english_package(self, root):
        original = b'\xef\xbb\xbf# Imported English\r\n\r\nOriginal wording.\r\n'
        source = b'# Chinese source\n'
        english = b'# English reading edition\n'
        source_manifest = {'source_file': 'theory.md', 'sha256': hashlib.sha256(source).hexdigest(),
                           'bytes': len(source)}
        english_manifest = {
            'source_file': 'edition.md', 'sha256': hashlib.sha256(english).hexdigest(),
            'bytes': len(english), 'translates': {'sha256': source_manifest['sha256']},
            'imported_from': {'source_file': 'upstream/original.md',
                              'sha256': hashlib.sha256(original).hexdigest(), 'bytes': len(original)},
        }
        contents = {
            'SKILL.md': b'Instructions.\r\n',
            'source/theory.md': source,
            'source/source-manifest.json': json.dumps(source_manifest).encode(),
            'source/en/edition.md': english,
            'source/en/source-manifest.json': json.dumps(english_manifest).encode(),
            'source/en/upstream/original.md': original,
        }
        metadata = {'name': 'xi-kari-skill', 'version': '1.0.0',
                    'files': ['skill-package.json', *contents]}
        contents['skill-package.json'] = json.dumps(metadata).encode()
        for name, data in contents.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return original, english_manifest, metadata

    def test_imported_english_original_keeps_bom_and_crlf_bytes_in_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original, english_manifest, _ = self.imported_english_package(root / 'input')
            result = builder.build(root / 'input', root / 'output')
            with zipfile.ZipFile(root / 'output' / result['archive']) as archive:
                prefix = result['archive_root'] + '/'
                self.assertEqual(archive.read(prefix + 'source/en/upstream/original.md'), original)
                self.assertEqual(archive.read(prefix + 'SKILL.md'), b'Instructions.\n')
            row = next(item for item in result['files'] if item['path'] == 'source/en/upstream/original.md')
            self.assertEqual(row['sha256'], english_manifest['imported_from']['sha256'])
            self.assertEqual(row['bytes'], english_manifest['imported_from']['bytes'])

    def test_missing_or_mismatched_imported_english_source_fails_before_writing(self):
        for damage in ('missing_payload', 'changed_bytes', 'wrong_byte_count', 'invalid_metadata', 'escaping_path'):
            with self.subTest(damage=damage), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                package = root / 'input'
                original, manifest, metadata = self.imported_english_package(package)
                if damage == 'missing_payload':
                    metadata['files'].remove('source/en/upstream/original.md')
                    (package / 'skill-package.json').write_text(json.dumps(metadata), encoding='utf-8')
                elif damage == 'changed_bytes':
                    (package / 'source/en/upstream/original.md').write_bytes(original.replace(b'Original', b'Modified'))
                elif damage == 'wrong_byte_count':
                    manifest['imported_from']['bytes'] += 1
                elif damage == 'invalid_metadata':
                    manifest['imported_from'] = None
                else:
                    manifest['imported_from']['source_file'] = '../theory.md'
                (package / 'source/en/source-manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
                output = root / 'output'
                with self.assertRaisesRegex(ValueError, 'English imported'):
                    builder.build(package, output)
                self.assertFalse(output.exists())

    def test_package_rejects_path_escape_and_case_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for names in [['../outside'], ['SKILL.md', 'skill.md']]:
                (root / 'skill-package.json').write_text(json.dumps({'name': 'xi-kari-skill', 'files': names}), encoding='utf-8')
                with self.assertRaises(ValueError):
                    builder.selected_files(root)

    def test_development_and_runtime_files_cannot_be_added_to_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('tests/a.py', 'docs/index.html', 'scripts/__pycache__/a.pyc', 'runs/result.json', 'AGENTS.md', 'scripts/build_install_package.py', 'scripts/lint_derived.py'):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('not for installation', encoding='utf-8')
                (root / 'skill-package.json').write_text(json.dumps({'name': 'xi-kari-skill', 'files': [name]}), encoding='utf-8')
                with self.subTest(path=name), self.assertRaises(ValueError):
                    builder.selected_files(root)

    def test_package_is_reproducible_across_worktree_line_endings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'input'; package.mkdir()
            source = b'# unchanged theory\r\nText\r\n'
            (package / 'source').mkdir()
            (package / 'source/theory.md').write_bytes(source)
            manifest = {'source_file': 'theory.md', 'sha256': hashlib.sha256(source).hexdigest()}
            (package / 'source/source-manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            metadata = {'name': 'xi-kari-skill', 'version': '1.0.0', 'files': ['SKILL.md', 'skill-package.json', 'source/source-manifest.json', 'source/theory.md']}
            (package / 'skill-package.json').write_text(json.dumps(metadata), encoding='utf-8')
            (package / 'SKILL.md').write_bytes(b'line one\nline two\n')
            first = builder.build(package, root / 'first')
            (package / 'SKILL.md').write_bytes(b'line one\r\nline two\r\n')
            second = builder.build(package, root / 'second')
            self.assertEqual(first['sha256'], second['sha256'])
            with zipfile.ZipFile(root / 'second' / second['archive']) as archive:
                self.assertEqual(archive.read('xi-kari-skill/source/theory.md'), source)

    def test_archive_entries_are_recorded_the_same_way_on_every_build_host(self):
        with tempfile.TemporaryDirectory() as directory:
            result = builder.build(ROOT, Path(directory))
            with zipfile.ZipFile(Path(directory) / result['archive']) as archive:
                entries = archive.infolist()
            theory = [entry for entry in entries if entry.filename.endswith('/source/Xikari-条件结构与转化论.md')]
            self.assertEqual(len(theory), 1)
            # A name outside ASCII is stored as UTF-8 and flagged as such, and no
            # entry is marked as made on DOS, where some unzip programs re-decode names.
            self.assertTrue(theory[0].flag_bits & 0x800)
            self.assertEqual({entry.create_system for entry in entries}, {3})
            self.assertEqual({entry.external_attr for entry in entries}, {0o600 << 16})


if __name__ == '__main__':
    unittest.main()
