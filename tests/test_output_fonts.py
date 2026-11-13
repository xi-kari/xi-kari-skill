import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / 'assets' / 'fonts'
GENERATORS = ('render_answer', 'condition_lab', 'comparison')


def generator(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


class OutputFontTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((FONTS / 'source.json').read_text(encoding='utf-8'))

    def test_cuts_match_their_record_and_carry_the_licence(self):
        self.assertEqual(self.record['license'], 'SIL Open Font License 1.1')
        self.assertIn('SIL OPEN FONT LICENSE', (FONTS / self.record['licenseFile']).read_text(encoding='utf-8'))
        for lang, name in (('zh', 'xk-display.woff2'), ('en', 'xk-display-latin.woff2')):
            face = self.record['faces'][lang]
            data = (FONTS / name).read_bytes()
            self.assertEqual(face['file'], name)
            self.assertEqual(face['weight'], 900)
            self.assertEqual(data[:4], b'wOF2')
            self.assertEqual(face['bytes'], len(data))
            self.assertEqual(face['sha256'], hashlib.sha256(data).hexdigest())
            self.assertEqual(face['source']['family'], 'Noto Sans SC')

    def test_every_display_string_of_every_generator_is_in_the_cut(self):
        for lang in ('zh', 'en'):
            covered = set(self.record['faces'][lang]['characters'])
            for name in GENERATORS:
                for string in generator(name).display_strings(lang):
                    missing = {char for char in string if not char.isspace()} - covered
                    self.assertFalse(missing, f'{name} ({lang}) sets {string!r} in the display face; rebuild with website/scripts/build_output_fonts.py')
        zh = set(self.record['faces']['zh']['characters'])
        for char in '0123456789%.,:()ABCXYZabcxyz一二三十百第章节条、':
            self.assertIn(char, zh)
        self.assertFalse({char for char in self.record['faces']['en']['characters'] if '一' <= char <= '鿿'})

    def test_cuts_are_small_enough_to_inline_and_are_packaged(self):
        self.assertLess((FONTS / 'xk-display.woff2').stat().st_size, 40 * 1024)
        self.assertLess((FONTS / 'xk-display-latin.woff2').stat().st_size, 16 * 1024)
        packaged = set(json.loads((ROOT / 'skill-package.json').read_text(encoding='utf-8'))['files'])
        for name in ('assets/fonts/xk-display.woff2', 'assets/fonts/xk-display-latin.woff2', 'assets/fonts/OFL.txt',
                     'assets/fonts/source.json', 'scripts/xikari_page.py'):
            self.assertIn(name, packaged)

    def test_check_command_reads_only_and_passes(self):
        before = {path.name: path.read_bytes() for path in FONTS.iterdir()}
        result = subprocess.run([sys.executable, str(ROOT / 'website/scripts/build_output_fonts.py'), '--check'],
                                capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(before, {path.name: path.read_bytes() for path in FONTS.iterdir()})

    def test_pages_fall_back_to_installed_faces_when_the_cut_is_missing(self):
        page = generator('xikari_page')
        self.assertEqual(page.display_face(ROOT / 'tests', 'zh'), '')
        css = page.foundation(ROOT / 'assets', 'zh')
        self.assertTrue(css.startswith('@font-face{font-family:"XK Display"'))
        self.assertIn('--display: "XK Display", "Noto Sans SC"', css)


if __name__ == '__main__':
    unittest.main()
