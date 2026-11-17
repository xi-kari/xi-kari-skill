"""Keep font additions reproducible and the three committed outputs consistent."""

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'website/scripts/build_fonts.py'
FONT = ROOT / 'website/.vitepress/theme/fonts/xk-display.woff2'


def builder():
    spec = importlib.util.spec_from_file_location('handbook_font_build', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FontWriteTests(unittest.TestCase):
    def test_failed_replacement_restores_all_outputs_and_allows_retry(self):
        for fail_at in (2, 3):
            with self.subTest(fail_at=fail_at), tempfile.TemporaryDirectory() as directory:
                module = builder()
                paths = [Path(directory) / name for name in ('font.woff2', 'source.json', 'fonts.css')]
                previous = {path: f'old {path.name}'.encode() for path in paths}
                payloads = {path: f'new {path.name}'.encode() for path in paths}
                for path, data in previous.items():
                    path.write_bytes(data)
                actual_replace = module.os.replace
                calls = 0

                def replace(source, destination):
                    nonlocal calls
                    calls += 1
                    if calls == fail_at:
                        raise PermissionError('simulated locked output on Windows')
                    return actual_replace(source, destination)

                with patch.object(module.os, 'replace', side_effect=replace):
                    with self.assertRaises(PermissionError):
                        module.write_outputs(payloads)
                self.assertEqual({path: path.read_bytes() for path in paths}, previous)
                self.assertEqual(set(Path(directory).iterdir()), set(paths))
                module.write_outputs(payloads)
                self.assertEqual({path: path.read_bytes() for path in paths}, payloads)

    def test_failed_staging_does_not_replace_any_output(self):
        module = builder()
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / name for name in ('font.woff2', 'source.json', 'fonts.css')]
            for path in paths:
                path.write_bytes(b'old')
            actual_fsync = module.os.fsync
            calls = 0

            def fsync(descriptor):
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError('simulated staging write failure')
                return actual_fsync(descriptor)

            with patch.object(module.os, 'fsync', side_effect=fsync):
                with self.assertRaises(OSError):
                    module.write_outputs({path: b'new' for path in paths})
            self.assertTrue(all(path.read_bytes() == b'old' for path in paths))
            self.assertEqual(set(Path(directory).iterdir()), set(paths))


@unittest.skipUnless(importlib.util.find_spec('fontTools') and importlib.util.find_spec('brotli'),
                     'optional font build dependencies are not installed')
class FontReproducibilityTests(unittest.TestCase):
    def test_identical_additions_ignore_the_build_clock(self):
        from fontTools import subset
        from fontTools.ttLib import TTFont

        # A tiny static fixture cut from the committed face exercises the real
        # subset/merge/save path without downloading a variable source font.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = TTFont(FONT, recalcTimestamp=False)
            cutter = subset.Subsetter()
            cutter.populate(text='A')
            cutter.subset(baseline)
            baseline_path = root / 'baseline.woff2'
            baseline.save(baseline_path)
            baseline.close()
            baseline_data = baseline_path.read_bytes()
            source = TTFont(FONT, recalcTimestamp=False)
            origin = {'family': source['name'].getDebugName(1),
                      'version': source['name'].getDebugName(5),
                      'sha256': hashlib.sha256(FONT.read_bytes()).hexdigest()}
            source.close()
            outputs = []
            for clock in (4_000_000_000, 4_000_000_900):
                run = root / str(clock)
                run.mkdir()
                module = builder()
                module.FONT_DIR = run
                module.RECORD = run / 'source.json'
                module.CSS_PATH = run / 'fonts.css'
                target = run / module.FILE
                target.write_bytes(baseline_data)
                module.RECORD.write_text(json.dumps({
                    'source': origin, 'characters': 'A',
                    'sha256': hashlib.sha256(baseline_data).hexdigest(),
                }), encoding='utf-8')
                with patch.object(module, 'needed_characters', return_value='A旧'), \
                     patch('fontTools.varLib.instancer.instantiateVariableFont', side_effect=lambda font, *args: font), \
                     patch('fontTools.merge.util.timestampNow', return_value=clock), \
                     patch('fontTools.ttLib.tables._h_e_a_d.timestampNow', return_value=clock):
                    module.build(FONT)
                outputs.append(tuple(path.read_bytes() for path in (target, module.RECORD, module.CSS_PATH)))
            self.assertEqual(outputs[0], outputs[1])


if __name__ == '__main__':
    unittest.main()
