import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock


def module():
    spec = importlib.util.spec_from_file_location('casebook', Path(__file__).resolve().parents[1] / 'scripts/casebook.py')
    target = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(target)
    return target


class CasebookTests(unittest.TestCase):
    def test_records_remain_distinct_from_observed_outcomes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record, library = root / 'case.json', root / 'library.json'
            data = {'id': 'capacity-1', 'title': '容量例', 'question': '哪里有约束', 'conditions': ['40工时'], 'interpretations': ['总量不足可能阻断新任务']}
            record.write_text(json.dumps(data), encoding='utf-8')
            original = record.read_bytes()
            first = module().add_case(library, record)
            self.assertEqual(first['outcome']['status'], 'not_observed')
            self.assertEqual(record.read_bytes(), original)
            before = library.read_bytes()
            with self.assertRaises(ValueError):
                module().add_case(library, record)
            self.assertEqual(library.read_bytes(), before)
            data.update(id='capacity-2', supersedes='capacity-1', outcome={'status': 'user_reported', 'basis': '当事人提供的实施说明', 'description': '仍有积压'})
            record.write_text(json.dumps(data), encoding='utf-8')
            module().add_case(library, record)
            cases = module().load_library(library)['cases']
            self.assertEqual(len(cases), 2)
            self.assertEqual(cases[0]['outcome']['status'], 'not_observed')
            self.assertEqual(cases[1]['outcome']['status'], 'user_reported')
            self.assertEqual(len(module().find_cases({'cases': cases}, '容量 40工时')), 2)

    def test_invalid_data_never_replaces_user_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record, library = root / 'record.json', root / 'original.json'
            record.write_text(json.dumps({'id': 'a', 'title': '题', 'question': '问'}), encoding='utf-8')
            library.write_text('{"user": "original"}', encoding='utf-8')
            original = library.read_bytes()
            with self.assertRaises(ValueError):
                module().add_case(library, record)
            self.assertEqual(library.read_bytes(), original)
            with self.assertRaises(ValueError):
                module().add_case(record, record)
            self.assertIn('question', json.loads(record.read_text()))

    def test_result_needs_basis_and_revision_needs_old_case(self):
        with self.assertRaises(ValueError):
            module().validate_case({'id': 'a', 'title': '题', 'question': '问', 'outcome': {'status': 'observed'}})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record, library = root / 'record.json', root / 'book.json'
            record.write_text(json.dumps({'id': 'b', 'title': '题', 'question': '问', 'supersedes': 'missing'}), encoding='utf-8')
            with self.assertRaises(ValueError):
                module().add_case(library, record)
            self.assertFalse(library.exists())

    def test_stale_write_does_not_replace_new_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'book.json'
            current = b'{"schema_version":1,"cases":[]}'
            path.write_bytes(current)
            with self.assertRaises(ValueError):
                module().save_library(path, {'schema_version': 1, 'cases': []}, b'old')
            self.assertEqual(path.read_bytes(), current)

    def test_concurrent_writers_cannot_both_commit_the_same_old_snapshot(self):
        target = module()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'book.json'
            original = b'{"schema_version":1,"cases":[]}'
            path.write_bytes(original)
            first = {'schema_version': 1, 'cases': [{'id': 'first', 'title': '先写', 'question': '问题'}]}
            second = {'schema_version': 1, 'cases': [{'id': 'second', 'title': '后写', 'question': '问题'}]}
            at_commit, release = threading.Event(), threading.Event()
            failures = []
            real_replace = target.os.replace

            def hold_first_replace(source, destination):
                at_commit.set()
                if not release.wait(5):
                    raise TimeoutError('测试未释放首次提交')
                real_replace(source, destination)

            def first_writer():
                try:
                    target.save_library(path, first, original)
                except BaseException as error:
                    failures.append(error)

            with mock.patch.object(target.os, 'replace', side_effect=hold_first_replace):
                thread = threading.Thread(target=first_writer)
                thread.start()
                try:
                    self.assertTrue(at_commit.wait(5), '首次写入没有到达提交位置')
                    with self.assertRaisesRegex(ValueError, '其他写入者'):
                        target.save_library(path, second, original)
                    self.assertEqual(path.read_bytes(), original)
                finally:
                    release.set()
                    thread.join(5)
            self.assertFalse(thread.is_alive())
            self.assertEqual(failures, [])
            self.assertEqual(json.loads(path.read_text(encoding='utf-8'))['cases'][0]['id'], 'first')
            committed = path.read_bytes()
            with self.assertRaisesRegex(ValueError, '已由其他工作改变'):
                target.save_library(path, second, original)
            self.assertEqual(path.read_bytes(), committed)
            fresh = target.load_library(path)
            fresh['cases'].append(second['cases'][0])
            target.save_library(path, fresh, committed)
            self.assertEqual([case['id'] for case in target.load_library(path)['cases']], ['first', 'second'])
            self.assertFalse(path.with_name(path.name + '.lock').exists())

    def test_failed_first_atomic_publish_leaves_no_partial_library(self):
        target = module()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'book.json'
            payload = {'schema_version': 1, 'cases': [{'id': 'a', 'title': '题', 'question': '问'}]}
            with mock.patch.object(target.os, 'link', side_effect=OSError('模拟首次提交失败')):
                with self.assertRaisesRegex(OSError, '首次提交失败'):
                    target.save_library(path, payload, None)
            self.assertFalse(path.exists())
            self.assertEqual(list(path.parent.iterdir()), [])
            target.save_library(path, payload, None)
            self.assertEqual(target.load_library(path)['cases'][0]['id'], 'a')

    def test_first_publish_does_not_replace_target_created_after_final_read(self):
        target = module()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'book.json'
            other_content = b'{"owner":"another writer"}'
            real_link = target.os.link

            def create_competing_target(source, destination):
                Path(destination).write_bytes(other_content)
                real_link(source, destination)

            with mock.patch.object(target.os, 'link', side_effect=create_competing_target):
                with self.assertRaisesRegex(ValueError, '首次提交前已出现'):
                    target.save_library(path, {'schema_version': 1, 'cases': []}, None)
            self.assertEqual(path.read_bytes(), other_content)
            self.assertEqual(list(path.parent.iterdir()), [path])

    def test_failed_existing_commit_preserves_original_and_releases_only_own_lock(self):
        target = module()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'book.json'
            original = b'{"schema_version":1,"cases":[]}'
            path.write_bytes(original)
            with mock.patch.object(target.os, 'replace', side_effect=OSError('模拟替换失败')):
                with self.assertRaisesRegex(OSError, '替换失败'):
                    target.save_library(path, {'schema_version': 1, 'cases': []}, original)
            self.assertEqual(path.read_bytes(), original)
            lock = path.with_name(path.name + '.lock')
            self.assertFalse(lock.exists())
            lock.write_bytes(b'another writer owns this')
            with self.assertRaisesRegex(ValueError, '其他写入者'):
                target.save_library(path, {'schema_version': 1, 'cases': []}, original)
            self.assertEqual(lock.read_bytes(), b'another writer owns this')
            self.assertEqual(path.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
