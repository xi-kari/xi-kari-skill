import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'task_state.py'


def module():
    spec = importlib.util.spec_from_file_location('task_state', SCRIPT)
    target = importlib.util.module_from_spec(spec)
    sys.modules['task_state'] = target
    spec.loader.exec_module(target)
    return target


def dump(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    return path


def record(number, question='本轮问题', **extra):
    data = {'round': number, 'question': question}
    data.update(extra)
    return data


def decided(identifier, statement='某个结论', kind='decision', **extra):
    data = {'id': identifier, 'statement': statement, 'kind': kind, 'basis': '依据说明'}
    if kind in ('fact', 'observation'):
        data.setdefault('sources', [{'path': '材料/来源.md'}])
    data.update(extra)
    return data


def ids_of(items):
    return {item['id'] for item in items}


def run_cli(*argv):
    return subprocess.run([sys.executable, str(SCRIPT), *argv],
                          capture_output=True, text=True, encoding='utf-8')


class TaskStateTests(unittest.TestCase):
    def test_normal_append(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / 'state.json'
            first = dump(root / 'round1.json', record(1, '第一轮：先确认是否需要搬迁',
                                                       decided=[decided('r1-d1')]))
            self.assertEqual(module().init_state(state, '共同问题')['rounds'], 0)
            module().add_round(state, first)
            loaded = module().load_state(state)
            self.assertEqual(len(loaded['rounds']), 1)
            listing = module().render_list(loaded)
            self.assertEqual(listing[0]['question'], '第一轮：先确认是否需要搬迁')
            self.assertEqual(listing[0]['counts']['decided'], 1)
            self.assertFalse(listing[0]['has_central_judgement'])
            brief = module().render_brief(loaded)
            self.assertEqual(brief['task'], '共同问题')
            self.assertEqual(brief['rounds'], 1)
            self.assertEqual(ids_of(brief['effective']), {'r1-d1'})

    def test_duplicate_round_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / 'state.json'
            module().init_state(state, 'T')
            module().add_round(state, dump(root / 'r1.json', record(1, 'Q1', decided=[decided('r1-d1')])))
            before = state.read_bytes()
            for bad in (1, 3, 0):
                dump(root / 'bad.json', record(bad, 'Q'))
                with self.assertRaises(ValueError):
                    module().add_round(state, root / 'bad.json')
                self.assertEqual(state.read_bytes(), before)

    def test_stale_state_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            current = b'{"schema_version":1,"format":"xikari-task-state-1","task":"t","rounds":[]}'
            path.write_bytes(current)
            with self.assertRaisesRegex(ValueError, '已由其他工作改变'):
                module().save_state(path, {'schema_version': 1, 'format': 'xikari-task-state-1',
                                           'task': 't', 'rounds': []}, b'old')
            self.assertEqual(path.read_bytes(), current)

    def test_lock_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / 'state.json'
            module().init_state(state, 'T')
            before = state.read_bytes()
            lock = state.with_name(state.name + '.lock')
            lock.write_bytes(b'another writer owns this')
            dump(root / 'r1.json', record(1, 'Q1', decided=[decided('r1-d1')]))
            with self.assertRaisesRegex(ValueError, '写入者|写锁'):
                module().add_round(state, root / 'r1.json')
            self.assertEqual(state.read_bytes(), before)
            self.assertEqual(lock.read_bytes(), b'another writer owns this')

    def test_brief_distinguishes_four_identities(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / 'state.json'
            module().init_state(state, 'T')
            module().add_round(state, dump(root / 'r1.json', record(1, 'Q1', decided=[decided('r1-d1')])))
            module().add_round(state, dump(root / 'r2.json', record(
                2, 'Q2',
                decided=[decided('r2-d1')],
                open=[{'id': 'r2-o1', 'statement': '仍未决的问题'}],
                revisit=[{'id': 'r2-v1', 'statement': '需复核的结论', 'ref': 'r1-d1', 'reason': '新证据'}],
                withdrawn=[{'id': 'r2-w1', 'statement': '撤回的判断', 'ref': 1, 'reason': '不再成立'}],
            )))
            brief = module().render_brief(module().load_state(state))
            self.assertEqual(ids_of(brief['effective']), {'r2-d1'})
            self.assertEqual(ids_of(brief['open']), {'r2-o1'})
            self.assertEqual(ids_of(brief['revisit']), {'r2-v1'})
            self.assertEqual(ids_of(brief['withdrawn']), {'r2-w1'})
            flat = [i for group in ('effective', 'open', 'revisit', 'withdrawn') for i in ids_of(brief[group])]
            self.assertEqual(len(flat), len(set(flat)))
            revisit = brief['revisit'][0]
            self.assertEqual(revisit['ref'], 'r1-d1')
            self.assertIn('r1-d1', revisit['ref_entries'])

    def test_withdrawn_invalidates_old_conclusion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / 'state.json'
            module().init_state(state, 'T')
            module().add_round(state, dump(root / 'r1.json', record(1, 'Q1', decided=[decided('r1-d1')])))
            module().add_round(state, dump(root / 'r2.json', record(
                2, 'Q2', withdrawn=[{'id': 'r2-w1', 'statement': '撤回', 'ref': 'r1-d1', 'reason': '不成立'}])))
            brief = module().render_brief(module().load_state(state))
            self.assertNotIn('r1-d1', ids_of(brief['effective']))

    def test_ref_pointing_at_missing_targets_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / 'state.json'
            module().init_state(state, 'T')
            module().add_round(state, dump(root / 'r1.json', record(1, 'Q1', decided=[decided('r1-d1')])))
            module().add_round(state, dump(root / 'r2.json', record(2, 'Q2', decided=[decided('r2-d1')])))
            before = state.read_bytes()
            for entry in (
                {'id': 'x', 'statement': 's', 'ref': 3, 'reason': 'r'},
                {'id': 'x', 'statement': 's', 'ref': 'nope', 'reason': 'r'},
            ):
                dump(root / 'bad.json', record(3, 'Q3', revisit=[entry]))
                with self.assertRaises(ValueError):
                    module().add_round(state, root / 'bad.json')
                self.assertEqual(state.read_bytes(), before)
            dump(root / 'cur.json', record(2, 'Q2', withdrawn=[{'id': 'y', 'statement': 's', 'ref': 2, 'reason': 'r'}]))
            with self.assertRaises(ValueError):
                module().add_round(state, root / 'cur.json')
            self.assertEqual(state.read_bytes(), before)

    def test_revisit_and_withdrawn_require_ref_and_reason(self):
        validate = module().validate_entry
        base = {'id': 'v1', 'statement': 's'}
        with self.assertRaises(ValueError):
            validate(dict(base), 'revisit', '第 1 轮', prior_rounds=[], known_ids=set(), current_round=1)
        with self.assertRaises(ValueError):
            validate({**base, 'ref': 'r1-d1'}, 'revisit', '第 1 轮', prior_rounds=[], known_ids={'r1-d1'}, current_round=1)
        with self.assertRaises(ValueError):
            validate({**base, 'reason': 'r'}, 'withdrawn', '第 1 轮', prior_rounds=[], known_ids=set(), current_round=1)

    def test_fact_and_observation_require_real_source_locations(self):
        validate = module().validate_entry
        for kind in ('fact', 'observation'):
            with self.assertRaises(ValueError):
                validate({'id': 'a', 'statement': 's', 'kind': kind, 'basis': 'b'}, 'decided', '第 1 轮')
            with self.assertRaises(ValueError):
                validate({'id': 'a', 'statement': 's', 'kind': kind, 'basis': 'b',
                          'sources': [{'description': '用户认可'}]}, 'decided', '第 1 轮')
        validate({'id': 'a', 'statement': 's', 'kind': 'fact', 'basis': 'b',
                  'sources': [{'path': '材料.md#3'}]}, 'decided', '第 1 轮')
        validate({'id': 'a', 'statement': 's', 'kind': 'observation', 'basis': 'b',
                  'sources': [{'catalog_id': 'clip-1'}]}, 'decided', '第 1 轮')

    def test_decided_entries_require_kind_and_basis(self):
        validate = module().validate_entry
        with self.assertRaises(ValueError):
            validate({'id': 'a', 'statement': 's', 'kind': 'hunch', 'basis': 'b'}, 'decided', '第 1 轮')
        with self.assertRaises(ValueError):
            validate({'id': 'a', 'statement': 's', 'kind': 'fact', 'sources': [{'path': 'x'}]}, 'decided', '第 1 轮')
        with self.assertRaises(ValueError):
            validate({'id': '', 'statement': 's', 'kind': 'decision', 'basis': 'b'}, 'decided', '第 1 轮')

    def test_unknown_fields_are_refused_at_round_and_entry_level(self):
        rv = module().validate_round
        with self.assertRaises(ValueError):
            rv({'round': 1, 'question': 'Q', 'next_page': 1}, [], set())
        with self.assertRaises(ValueError):
            rv({'round': 1, 'question': 'Q',
                'decided': [{'id': 'a', 'statement': 's', 'kind': 'decision', 'basis': 'b', 'mood': 'x'}]}, [], set())
        with self.assertRaises(ValueError):
            rv({'round': 1, 'question': 'Q', 'decided': [decided('a')], 'recorded_at': 'now'}, [], set())

    def test_duplicate_entry_ids_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / 'state.json'
            module().init_state(state, 'T')
            module().add_round(state, dump(root / 'r1.json', record(1, 'Q1', decided=[decided('dup')])))
            before = state.read_bytes()
            dump(root / 'r2.json', record(2, 'Q2', open=[{'id': 'dup', 'statement': 's'}]))
            with self.assertRaises(ValueError):
                module().add_round(state, root / 'r2.json')
            self.assertEqual(state.read_bytes(), before)
            rv = module().validate_round
            with self.assertRaises(ValueError):
                rv({'round': 1, 'question': 'Q', 'open': [{'id': 'same', 'statement': 's'},
                                                          {'id': 'same', 'statement': 's'}]}, [], set())

    def test_record_with_duplicate_json_keys_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / 'state.json'
            module().init_state(state, 'T')
            (root / 'r1.json').write_text('{"round":1,"round":1,"question":"Q"}', encoding='utf-8')
            before = state.read_bytes()
            with self.assertRaises(ValueError):
                module().add_round(state, root / 'r1.json')
            self.assertEqual(state.read_bytes(), before)

    def test_check_reads_from_disk_and_reports_inconsistency(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / 'state.json'
            module().init_state(state, 'T')
            module().add_round(state, dump(root / 'r1.json', record(1, 'Q1', decided=[decided('r1-d1')])))
            data = json.loads(state.read_text(encoding='utf-8'))
            data['rounds'][0]['decided'][0]['statement'] = ''
            state.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            before = state.read_bytes()
            report = module().check_state(state)
            self.assertFalse(report['ok'])
            self.assertTrue(report['errors'])
            self.assertEqual(report['rounds'], 1)
            self.assertIn('不判断内容真伪', report['scope'])
            self.assertEqual(state.read_bytes(), before)
            proc = run_cli('--state', str(state), 'check')
            self.assertEqual(proc.returncode, 1, proc.stderr)
            self.assertEqual(state.read_bytes(), before)

    def test_list_brief_and_check_never_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / 'state.json'
            module().init_state(state, 'T')
            module().add_round(state, dump(root / 'r1.json', record(1, 'Q1', decided=[decided('r1-d1')])))

            def snapshot():
                return sorted(p.name for p in root.iterdir())

            before = snapshot()
            for command in ('list', 'brief', 'check'):
                proc = run_cli('--state', str(state), command)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                json.loads(proc.stdout)
                self.assertEqual(snapshot(), before)

    def test_install_tree_is_write_protected_but_readable(self):
        """台账是写入目标，必须拒绝落在安装目录内；轮次记录是只读输入，随包示例就从安装目录读取。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            forbidden = ROOT / 'scripts' / 'task-state-forbidden.json'
            with self.assertRaises(OSError):
                module().init_state(forbidden, 'T')
            self.assertFalse(forbidden.exists())
            state = root / 'state.json'
            module().init_state(state, 'T')
            # 读取安装目录内的轮次记录是正常的，与 casebook.py、condition_lab.py 一致。
            shipped = ROOT / 'assets' / 'examples' / 'task-state-example.json'
            if shipped.is_file():
                added = module().add_round(state, shipped)
                self.assertEqual(added['round'], 1)
            # 但从安装目录内读取绝不能演变成向安装目录写入。
            self.assertFalse(forbidden.exists())
            self.assertFalse((ROOT / 'scripts' / 'task-state-record.json').exists())
            self.assertTrue(state.is_file())

    def test_init_refuses_an_existing_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / 'state.json'
            state.write_text('not json at all', encoding='utf-8')
            before = state.read_bytes()
            with self.assertRaises(ValueError):
                module().init_state(state, 'T')
            self.assertEqual(state.read_bytes(), before)
            empty = root / 'empty.json'
            empty.write_bytes(b'')
            with self.assertRaises(ValueError):
                module().init_state(empty, 'T')
            self.assertEqual(empty.read_bytes(), b'')

    def test_first_publish_does_not_replace_a_target_created_between_read_and_link(self):
        target = module()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            other = b'{"owner":"another writer"}'
            real_link = target.os.link

            def competing(source, destination):
                Path(destination).write_bytes(other)
                real_link(source, destination)

            with mock.patch.object(target.os, 'link', side_effect=competing):
                with self.assertRaisesRegex(ValueError, '首次提交前已出现'):
                    target.save_state(path, {'schema_version': 1, 'format': 'xikari-task-state-1',
                                             'task': 't', 'rounds': []}, None)
            self.assertEqual(path.read_bytes(), other)
            self.assertEqual([p.name for p in Path(directory).iterdir()], ['state.json'])

    def test_failed_commit_preserves_original_and_releases_own_lock(self):
        target = module()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            original = b'{"schema_version":1,"format":"xikari-task-state-1","task":"t","rounds":[]}'
            path.write_bytes(original)
            with mock.patch.object(target.os, 'replace', side_effect=OSError('模拟替换失败')):
                with self.assertRaisesRegex(OSError, '替换失败'):
                    target.save_state(path, {'schema_version': 1, 'format': 'xikari-task-state-1',
                                             'task': 't', 'rounds': []}, original)
            self.assertEqual(path.read_bytes(), original)
            self.assertFalse(path.with_name(path.name + '.lock').exists())

    def test_open_and_revisit_are_never_treated_as_settled(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / 'state.json'
            module().init_state(state, 'T')
            module().add_round(state, dump(root / 'r1.json', record(1, 'Q1', decided=[decided('r1-d1')])))
            module().add_round(state, dump(root / 'r2.json', record(
                2, 'Q2', open=[{'id': 'r2-o1', 'statement': '未决'}],
                revisit=[{'id': 'r2-v1', 'statement': '复核', 'ref': 'r1-d1', 'reason': '新证据'}])))
            brief = module().render_brief(module().load_state(state))
            settled = ids_of(brief['effective'])
            for item in brief['open'] + brief['revisit']:
                self.assertNotIn(item['id'], settled)
            self.assertIn('不把用户认可当作事实成立', brief['notice'])

    def test_cli_end_to_end(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / 'state.json'
            proc = run_cli('--state', str(state), 'init', '--task', '共同问题')
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout)['rounds'], 0)
            dump(root / 'r1.json', record(1, 'Q1', decided=[decided('r1-d1')]))
            proc = run_cli('--state', str(state), 'record', '--record', str(root / 'r1.json'))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            saved = json.loads(proc.stdout)
            self.assertEqual(saved['round'], 1)
            self.assertEqual(saved['decided'][0]['identity'], 'decided')
            self.assertIn('recorded_at', saved)
            for command in ('list', 'brief', 'check'):
                proc = run_cli('--state', str(state), command)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                json.loads(proc.stdout)
            bad = run_cli('--state', str(root / 'missing.json'), 'list')
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(bad.stdout, '')
            self.assertTrue(bad.stderr.startswith('任务状态处理失败'))

    def test_brief_carries_central_judgement_and_manuscript(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / 'state.json'
            module().init_state(state, 'T')
            module().add_round(state, dump(root / 'r1.json', record(
                1, 'Q1', central_judgement='当前中心判断',
                manuscript={'path': 'drafts/main.md', 'heading': '现状'},
                decided=[decided('r1-d1')])))
            brief = module().render_brief(module().load_state(state))
            self.assertEqual(brief['central_judgement'], {'statement': '当前中心判断', 'round': 1})
            self.assertEqual(brief['manuscript'], {'path': 'drafts/main.md', 'round': 1})
            self.assertEqual(brief['gaps'], [])


    def test_malformed_ledgers_never_escape_as_type_or_attribute_error(self):
        # 非字符串的 kind/round/id/central_judgement 必须报错而非抛 TypeError/AttributeError。
        cases = [
            {'round': 1, 'question': 'Q',
             'decided': [{'id': 'a', 'statement': 's', 'kind': [], 'basis': 'b', 'identity': 'decided'}]},
            {'round': [1], 'question': 'Q'},
            {'round': 1, 'question': 'Q',
             'decided': [{'id': [1], 'statement': 's', 'kind': 'decision', 'basis': 'b', 'identity': 'decided'}]},
            {'round': 1, 'question': 'Q', 'central_judgement': ['x']},
        ]
        for round_obj in cases:
            state = {'schema_version': 1, 'format': 'xikari-task-state-1', 'task': 'T',
                     'rounds': [round_obj]}
            report = module().check_state(dump(Path(tempfile.mkdtemp()) / 'state.json', state))
            self.assertFalse(report['ok'])
            self.assertTrue(report['errors'])
            # 只读渲染不得因畸形字段崩溃
            module().render_list(state)
            module().render_brief(state)

    def test_check_reports_malformed_ledger_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'state.json'
            dump(state, {'schema_version': 1, 'format': 'xikari-task-state-1', 'task': 'T',
                         'rounds': [{'round': 1, 'question': 'Q', 'central_judgement': ['x']}]})
            before = state.read_bytes()
            proc = run_cli('--state', str(state), 'check')
            self.assertEqual(proc.returncode, 1, proc.stderr)
            self.assertNotIn('Traceback', proc.stderr)
            json.loads(proc.stdout)
            self.assertEqual(state.read_bytes(), before)

    def test_non_string_central_judgement_yields_no_brief_judgement(self):
        state = {'schema_version': 1, 'format': 'xikari-task-state-1', 'task': 'T',
                 'rounds': [{'round': 1, 'question': 'Q', 'central_judgement': ['x'],
                             'decided': [{'id': 'r1-d1', 'statement': 's', 'kind': 'decision',
                                          'basis': 'b', 'identity': 'decided'}]}]}
        self.assertFalse(module().render_list(state)[0]['has_central_judgement'])
        self.assertIsNone(module().render_brief(state)['central_judgement'])


    def test_shipped_example_can_be_recorded_from_the_install_tree(self):
        """随包示例位于安装目录内，是只读输入；把它当成待写入路径拒绝会挡住正常用法。"""
        example = ROOT / 'assets' / 'examples' / 'task-state-example.json'
        self.assertTrue(example.is_file(), '随包示例缺失')
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'state.json'
            module().init_state(state, '接续装置是否够用')
            added = module().add_round(state, example)
            self.assertEqual(added['round'], 1)
            loaded = module().load_state(state)
            self.assertEqual(len(loaded['rounds']), 1)
            for identity in ('decided', 'open'):
                for entry in loaded['rounds'][0].get(identity, []):
                    self.assertEqual(entry['identity'], identity)

    def test_example_record_still_cannot_be_written_over(self):
        """放开读取不等于放开写入：示例文件本身必须逐字节保持不变。"""
        example = ROOT / 'assets' / 'examples' / 'task-state-example.json'
        before = example.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'state.json'
            module().init_state(state, 'Q')
            module().add_round(state, example)
        self.assertEqual(example.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
