"""独立复核 study_design 的写入安全：写锁窗口内出现的外部写入者不得被静默覆盖。"""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'study_design.py'


def module():
    spec = importlib.util.spec_from_file_location('study_design', SCRIPT)
    target = importlib.util.module_from_spec(spec)
    sys.modules['study_design'] = target
    spec.loader.exec_module(target)
    return target


MARK = '<!-- xikari-study-design -->'


class WriteRaceReviewTests(unittest.TestCase):
    def test_external_file_appearing_in_the_lock_window_is_not_clobbered(self):
        """预检查之后、取锁之前出现的外部文件必须被拒绝覆盖，而不是被 os.replace 吞掉。"""
        target = module()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / '说明.md'
            real_mkstemp = target.tempfile.mkstemp

            def rigged_mkstemp(*args, **kwargs):
                descriptor, name = real_mkstemp(*args, **kwargs)
                output.write_text('外部写入者的文件，不含工具标记\n', encoding='utf-8')
                return descriptor, name

            target.tempfile.mkstemp = rigged_mkstemp
            try:
                with self.assertRaises(ValueError):
                    target.write_document(f'正文\n{MARK}\n', output, force=False)
            finally:
                target.tempfile.mkstemp = real_mkstemp
            self.assertEqual(output.read_text(encoding='utf-8').strip(), '外部写入者的文件，不含工具标记')
            self.assertFalse(Path(str(output) + '.lock').exists())

    def test_external_file_appearing_in_the_lock_window_is_refused_even_with_force(self):
        """--force 只授权覆盖本工具先前的产物，不能授权覆盖窗口内出现的外部文件。"""
        target = module()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / '说明.md'
            real_mkstemp = target.tempfile.mkstemp

            def rigged_mkstemp(*args, **kwargs):
                descriptor, name = real_mkstemp(*args, **kwargs)
                output.write_text('外部文件二\n', encoding='utf-8')
                return descriptor, name

            target.tempfile.mkstemp = rigged_mkstemp
            try:
                with self.assertRaises(ValueError):
                    target.write_document(f'正文\n{MARK}\n', output, force=True)
            finally:
                target.tempfile.mkstemp = real_mkstemp
            self.assertEqual(output.read_text(encoding='utf-8').strip(), '外部文件二')
            self.assertFalse(Path(str(output) + '.lock').exists())


class UnknownFieldReviewTests(unittest.TestCase):
    def test_unknown_key_inside_a_proposition_is_refused(self):
        """命题内拼错的键不能被静默丢弃，须与原顶层未知字段同等拒绝。"""
        broken = {'schema_version': 1, 'question': 'q',
                  'propositions': [{'id': 'a', 'statement': 's',
                                    'distinguishing': ['d'], 'suports': ['拼错的键']}]}
        with self.assertRaises(ValueError):
            module().validate_design(broken)

    def test_unknown_key_inside_an_execution_entry_is_refused(self):
        broken = {'schema_version': 1, 'question': 'q',
                  'propositions': [{'id': 'a', 'statement': 's', 'distinguishing': ['d']}],
                  'execution': [{'who': 'w', 'authority': 'a', 'bogus': 1}]}
        with self.assertRaises(ValueError):
            module().validate_design(broken)



class SamePathReviewTests(unittest.TestCase):
    def test_render_refuses_to_overwrite_its_own_input_design(self):
        """输出与输入是同一文件时，即使 --force 也不得覆盖输入设计，避免数据丢失。"""
        root = ROOT
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'design.json'
            data = {'schema_version': 1,
                    'question': f'{MARK} 研究问题本身含标记',
                    'propositions': [{'id': 'a', 'statement': 's', 'distinguishing': ['d']}]}
            source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            before = source.read_text(encoding='utf-8')
            result = subprocess.run(
                [sys.executable, str(SCRIPT), '--design', str(source),
                 'render', '--output', str(source), '--force'],
                capture_output=True, text=True, encoding='utf-8')
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(source.read_text(encoding='utf-8'), before)

if __name__ == '__main__':
    unittest.main()
