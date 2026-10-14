#!/usr/bin/env python3
"""把一个长任务的每一轮记为一条只读事实，跨轮次接续。

它只登记「哪些已决定、哪些仍悬、哪些被新证据动摇、哪些已撤回」，并按
decided/open/revisit/withdrawn 四种身份生成接续摘要 brief。它是清单与接续
装置，不是评分器、不是完成度证明，也不判断内容真伪。它不得把「用户认可」
记成「事实成立」，也不得把「未实施的方案」记成「已观察结果」——为此
decided 条目带 kind，kind=fact/observation 必须给出真实来源位置。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from xikari_paths import require_external_output
finally:
    sys.path.pop(0)


FORMAT = 'xikari-task-state-1'
SCHEMA_VERSION = 1
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z')
IDENTITIES = ('decided', 'open', 'revisit', 'withdrawn')
KINDS = {'decision', 'fact', 'observation', 'plan', 'interpretation'}
ROUND_KEYS = {'round', 'question', 'materials', 'central_judgement', 'manuscript',
              'decided', 'open', 'revisit', 'withdrawn'}
ENTRY_KEYS = {'id', 'statement', 'kind', 'basis', 'sources', 'why_open', 'competing',
              'ref', 'reason', 'change_conditions', 'load_bearing'}
RUNTIME_ROUND_KEYS = {'recorded_at', 'record_file'}
RUNTIME_ENTRY_KEYS = {'identity'}
LOCATION_KEYS = ('path', 'url', 'catalog_id')
SOURCE_KEYS = LOCATION_KEYS + ('description',)
NOTICE = '本摘要只重述台账中已登记的内容，不判断对错、不给优先级，也不把用户认可当作事实成立、不把未实施方案当作已观察结果。'
SCOPE = '仅核对台账内部结构与引用是否可解析；不判断内容真伪、依据是否充分或任务是否完成。'


class TaskStateError(ValueError):
    """任务状态数据不合法，统一抛 ValueError。"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _reject_duplicate_keys(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise TaskStateError(f'JSON含重复键: {key}')
        seen[key] = value
    return seen


def read_json(path) -> object:
    """以 utf-8-sig 读取 JSON，并用 object_pairs_hook 拒绝重复键。"""
    path = Path(path)
    try:
        text = path.read_text(encoding='utf-8-sig')
    except OSError as exc:
        raise TaskStateError(f'无法读取 {path}: {exc}') from exc
    try:
        return json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise TaskStateError(f'{path} 不是有效JSON: {exc}') from exc


def text_field(item, field, where, required=False, limit=8000) -> str:
    value = item.get(field, '')
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise TaskStateError(f'{where}.{field}须为{"非空" if required else ""}文本，不超过{limit}字符。')
    return value


def text_list(item, field, where, required=False) -> list:
    value = item.get(field, [])
    if not isinstance(value, list) or any(not isinstance(entry, str) or not entry.strip() for entry in value):
        raise TaskStateError(f'{where}.{field}应是文字列表。')
    if required and not value:
        raise TaskStateError(f'{where}.{field}不能为空。')
    return value


def location_list(item, field, where) -> list:
    """kind=fact/observation 的来源：每条至少给出 path/url/catalog_id 之一。

    「用户认可」没有来源位置，只能以 kind=decision 的身份保留，因此
    仅凭 description 无法支撑事实或观察。
    """
    value = item.get(field)
    if not isinstance(value, list) or not value:
        raise TaskStateError(f'{where}.{field} 须为非空来源列表：事实与观察必须给出真实来源位置。')
    for source in value:
        if not isinstance(source, dict):
            raise TaskStateError(f'{where}.{field} 每项须为来源对象。')
        if not any(isinstance(source.get(key), str) and source[key].strip() for key in LOCATION_KEYS):
            raise TaskStateError(
                f'{where}.{field} 每条须至少含 path、url 或 catalog_id 之一；'
                '仅凭 description（如「用户认可」）不能支撑事实或观察。')
    return value


def source_list(item, field, where) -> list:
    value = item.get(field)
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(source, dict) for source in value):
        raise TaskStateError(f'{where}.{field} 应是来源对象列表。')
    for source in value:
        if not any(isinstance(source.get(key), str) and source[key].strip() for key in SOURCE_KEYS):
            raise TaskStateError(f'{where}.{field} 每条至少含 path、url、catalog_id 或 description 之一。')
    return value


def validate_entry(entry, identity, where, prior_rounds=(), known_ids=(), current_round=None,
                   stored=False) -> dict:
    """校验单条条目；identity 由所属列表注入，不由条目自称。"""
    if not isinstance(entry, dict):
        raise TaskStateError(f'{where} 的条目须为对象。')
    allowed = set(ENTRY_KEYS) | (RUNTIME_ENTRY_KEYS if stored else set())
    extra = set(entry) - allowed
    if extra:
        raise TaskStateError(f'{where} 含未知字段，不能静默忽略: ' + ', '.join(sorted(extra)))
    identifier = entry.get('id')
    if not isinstance(identifier, str) or not ID.fullmatch(identifier):
        raise TaskStateError(f'{where} 的条目 id 须为字母或数字开头、只含 A-Za-z0-9._-、不超过96字符: {identifier!r}')
    text_field(entry, 'statement', where, required=True)
    if identity == 'decided':
        kind = entry.get('kind')
        if not isinstance(kind, str) or kind not in KINDS:
            raise TaskStateError(f'{where}.kind 须为 decision、fact、observation、plan 或 interpretation。')
        text_field(entry, 'basis', where, required=True)
        if kind in ('fact', 'observation'):
            location_list(entry, 'sources', where)
        else:
            source_list(entry, 'sources', where)
        text_list(entry, 'change_conditions', where)
        if 'load_bearing' in entry and not isinstance(entry['load_bearing'], bool):
            raise TaskStateError(f'{where}.load_bearing 须为 true 或 false。')
    elif identity == 'open':
        if 'why_open' in entry:
            text_field(entry, 'why_open', where)
        text_list(entry, 'competing', where)
    else:  # revisit / withdrawn
        if 'ref' not in entry:
            raise TaskStateError(f'{where} 必须给出 ref，指向需复核或撤回的既有判断。')
        text_field(entry, 'reason', where, required=True)
        ref = entry['ref']
        if isinstance(ref, bool):
            raise TaskStateError(f'{where}.ref 须为先前轮次号或既有条目 id。')
        if isinstance(ref, int):
            if current_round is not None and ref >= current_round:
                raise TaskStateError(f'{where}.ref 只能指向更早的轮次。')
            if ref not in set(prior_rounds):
                raise TaskStateError(f'{where}.ref 所指轮次不存在: {ref}')
        elif isinstance(ref, str):
            if ref not in set(known_ids):
                raise TaskStateError(f'{where}.ref 所指既有判断不存在: {ref}')
        else:
            raise TaskStateError(f'{where}.ref 须为先前轮次号或既有条目 id。')
    return entry


def validate_round(round_obj, existing_rounds, existing_ids, stored=False) -> dict:
    """校验一轮；round 必须紧接现有轮次，既拒重复也拒跳号与乱序。"""
    if not isinstance(round_obj, dict):
        raise TaskStateError('轮次须为 JSON 对象。')
    allowed = set(ROUND_KEYS) | (RUNTIME_ROUND_KEYS if stored else set())
    extra = set(round_obj) - allowed
    if extra:
        raise TaskStateError('轮次含未知字段，不能静默忽略: ' + ', '.join(sorted(extra)))
    number = round_obj.get('round')
    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        raise TaskStateError('轮次号 round 须为不小于 1 的整数。')
    if number != len(existing_rounds) + 1:
        raise TaskStateError(
            f'轮次号必须按顺序追加：现有 {len(existing_rounds)} 轮，下一轮应为 {len(existing_rounds) + 1}，得到 {number}。')
    text_field(round_obj, 'question', f'第 {number} 轮', required=True)
    text_list(round_obj, 'materials', f'第 {number} 轮')
    text_field(round_obj, 'central_judgement', f'第 {number} 轮')
    if 'manuscript' in round_obj:
        manuscript = round_obj['manuscript']
        if not isinstance(manuscript, dict):
            raise TaskStateError(f'第 {number} 轮 manuscript 须为对象。')
        text_field(manuscript, 'path', f'第 {number} 轮.manuscript', required=True)
        text_field(manuscript, 'heading', f'第 {number} 轮.manuscript')
        text_field(manuscript, 'note', f'第 {number} 轮.manuscript')
    prior_rounds = [item['round'] for item in existing_rounds if isinstance(item.get('round'), int)]
    known = set(existing_ids)
    local = set()
    for identity in IDENTITIES:
        value = round_obj.get(identity, [])
        if not isinstance(value, list):
            raise TaskStateError(f'第 {number} 轮 {identity} 须为条目列表。')
        for entry in value:
            validate_entry(entry, identity, f'第 {number} 轮 {identity}',
                           prior_rounds=prior_rounds, known_ids=known,
                           current_round=number, stored=stored)
            identifier = entry.get('id')
            if identifier in known or identifier in local:
                raise TaskStateError(f'条目 id 重复: {identifier}')
            local.add(identifier)
    return round_obj


def _round_ids(round_obj) -> set:
    identifiers = set()
    for identity in IDENTITIES:
        for entry in round_obj.get(identity, []) or []:
            if isinstance(entry, dict) and isinstance(entry.get('id'), str):
                identifiers.add(entry['id'])
    return identifiers


def _empty_state(task='') -> dict:
    return {'schema_version': SCHEMA_VERSION, 'format': FORMAT, 'task': task, 'rounds': []}


def load_state(path, allow_missing=False) -> dict:
    path = Path(path)
    if not path.exists():
        if allow_missing:
            return _empty_state()
        raise TaskStateError('状态台账不存在；先执行 init。')
    state = read_json(path)
    if not isinstance(state, dict) or state.get('schema_version') != SCHEMA_VERSION or state.get('format') != FORMAT:
        raise TaskStateError('目标不是可识别的状态台账，不会覆盖。')
    rounds = state.get('rounds')
    if not isinstance(rounds, list):
        raise TaskStateError('状态台账的 rounds 须为列表。')
    seen_rounds = set()
    known_ids = set()
    for index, round_obj in enumerate(rounds):
        if not isinstance(round_obj, dict):
            raise TaskStateError(f'状态台账第 {index + 1} 项不是对象。')
        number = round_obj.get('round')
        if not isinstance(number, int) or isinstance(number, bool):
            raise TaskStateError(f'状态台账第 {index + 1} 轮的轮次号不是整数。')
        if number in seen_rounds:
            raise TaskStateError('状态台账包含重复轮次号')
        if number != index + 1:
            raise TaskStateError('状态台账包含重复轮次号或轮次号不连续')
        seen_rounds.add(number)
        for identity in IDENTITIES:
            value = round_obj.get(identity, [])
            if isinstance(value, list):
                for entry in value:
                    if (isinstance(entry, dict) and isinstance(entry.get('id'), str)
                            and entry.get('id') in known_ids):
                        raise TaskStateError('状态台账包含重复条目标识')
        validate_round(round_obj, rounds[:index], known_ids, stored=True)
        known_ids |= _round_ids(round_obj)
    return state


def save_state(path, state, expected) -> None:
    """独占锁 + 临时文件 + 原子提交；拒绝覆盖已被其他写入者改动的目标。"""
    require_external_output(path, __file__)
    require_external_output(Path(path).with_name(Path(path).name + '.lock'), __file__)
    path = Path(path).resolve()
    lock = path.with_name(path.name + '.lock')
    require_external_output(lock, __file__)
    path.parent.mkdir(parents=True, exist_ok=True)
    state.setdefault('format', FORMAT)
    payload = (json.dumps(state, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    temporary = None
    owns_lock = False
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.task-state-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise ValueError('状态台账有其他写入者或遗留写锁；本次未提交。确认写入结束并重读后再记录，不自动移除锁') from error
        owns_lock = True
        os.close(descriptor)
        current = path.read_bytes() if path.exists() else None
        if current != expected:
            raise ValueError('状态台账已由其他工作改变，请重读后再记录')
        if expected is None:
            try:
                os.link(temporary, path)
            except FileExistsError as error:
                raise ValueError('状态台账在首次提交前已出现；本次未覆盖，请重读后再记录') from error
        else:
            os.replace(temporary, path)
            temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if owns_lock:
            lock.unlink(missing_ok=True)


def init_state(state_path, task) -> dict:
    require_external_output(state_path, __file__)
    state_path = Path(state_path)
    if state_path.exists():
        raise ValueError('状态台账已存在，不覆盖')
    task_text = task if isinstance(task, str) and task.strip() else None
    if task_text is None:
        raise TaskStateError('init 需要非空的 --task 文本作为共同问题。')
    now = _now()
    state = _empty_state(task_text)
    state['created_at'] = now
    state['updated_at'] = now
    save_state(state_path, state, None)
    return {'path': str(state_path.resolve()), 'task': task_text, 'rounds': 0}


def add_round(state_path, record_path) -> dict:
    # 台账必须写在安装目录之外；轮次记录是只读输入，随包示例也从安装目录读取，
    # 因此与 casebook.py 一致，不对此路径设写入保护。
    require_external_output(state_path, __file__)
    state_path = Path(state_path)
    record_path = Path(record_path)
    if state_path.resolve() == record_path.resolve():
        raise ValueError('状态台账与轮次记录不能是同一文件')
    if not state_path.exists():
        raise ValueError('状态台账不存在；先执行 init')
    expected = state_path.read_bytes()
    state = load_state(state_path)
    record = read_json(record_path)
    known_ids = set()
    for item in state['rounds']:
        known_ids |= _round_ids(item)
    round_obj = validate_round(record, state['rounds'], known_ids)
    round_obj = dict(round_obj)
    round_obj['recorded_at'] = _now()
    round_obj['record_file'] = str(record_path.resolve())
    for identity in IDENTITIES:
        for entry in round_obj.get(identity, []):
            entry['identity'] = identity
    state['rounds'].append(round_obj)
    state['updated_at'] = _now()
    save_state(state_path, state, expected)
    return round_obj


def render_list(state) -> list:
    listing = []
    for round_obj in state.get('rounds', []):
        manuscript = round_obj.get('manuscript')
        counts = {identity: len(round_obj.get(identity, []) or []) for identity in IDENTITIES}
        listing.append({
            'round': round_obj.get('round'),
            'question': round_obj.get('question'),
            'counts': counts,
            'has_central_judgement': bool(isinstance(round_obj.get('central_judgement'), str)
                                          and round_obj.get('central_judgement').strip()),
            'manuscript': manuscript.get('path') if isinstance(manuscript, dict) else None,
            'recorded_at': round_obj.get('recorded_at'),
        })
    return listing


def _resolve_ref_entries(rounds, ref) -> list:
    if isinstance(ref, bool):
        return []
    if isinstance(ref, int):
        for round_obj in rounds:
            if round_obj.get('round') == ref:
                return sorted(_round_ids(round_obj))
        return []
    if isinstance(ref, str):
        for round_obj in rounds:
            if ref in _round_ids(round_obj):
                return [ref]
        return []
    return []


def render_brief(state) -> dict:
    """生成接续摘要；只重述台账已有内容，可重复，不带生成时间戳。"""
    rounds = state.get('rounds', [])
    all_entries = []
    for round_obj in rounds:
        number = round_obj.get('round')
        for identity in IDENTITIES:
            for entry in round_obj.get(identity, []) or []:
                all_entries.append((number, identity, entry))
    superseded = set()
    for number, identity, entry in all_entries:
        if identity in ('revisit', 'withdrawn'):
            ref = entry.get('ref')
            if isinstance(ref, bool):
                continue
            if isinstance(ref, int):
                for round_obj in rounds:
                    if round_obj.get('round') == ref:
                        superseded |= _round_ids(round_obj)
            elif isinstance(ref, str):
                superseded.add(ref)

    def describe(number, identity, entry):
        item = {'id': entry.get('id'), 'statement': entry.get('statement'), 'round': number}
        if identity == 'open':
            if entry.get('why_open'):
                item['why_open'] = entry['why_open']
            if entry.get('competing'):
                item['competing'] = entry['competing']
        elif identity in ('revisit', 'withdrawn'):
            item['ref'] = entry.get('ref')
            item['reason'] = entry.get('reason')
            item['ref_entries'] = _resolve_ref_entries(rounds, entry.get('ref'))
        return item

    def collect(identity, keep):
        selected = [(number, entry) for number, kind, entry in all_entries if kind == identity and keep(entry)]
        selected.sort(key=lambda pair: (pair[0], pair[1].get('id')))
        return [describe(number, identity, entry) for number, entry in selected]

    effective = collect('decided', lambda entry: not (
        isinstance(entry.get('id'), str) and entry.get('id') in superseded))
    opens = collect('open', lambda entry: True)
    revisits = collect('revisit', lambda entry: True)
    withdrawns = collect('withdrawn', lambda entry: True)

    central_judgement = None
    for round_obj in rounds:
        value = round_obj.get('central_judgement')
        if isinstance(value, str) and value.strip():
            central_judgement = {'statement': value.strip(), 'round': round_obj.get('round')}
    manuscript = None
    for round_obj in rounds:
        document = round_obj.get('manuscript')
        if (isinstance(document, dict) and isinstance(document.get('path'), str)
                and document['path'].strip()):
            manuscript = {'path': document['path'], 'round': round_obj.get('round')}

    gaps = [{'statement': item['statement'], 'round': item['round'], 'identity': identity}
            for identity, group in (('open', opens), ('revisit', revisits)) for item in group]

    return {
        'task': state.get('task', ''),
        'rounds': len(rounds),
        'central_judgement': central_judgement,
        'manuscript': manuscript,
        'effective': effective,
        'open': opens,
        'revisit': revisits,
        'withdrawn': withdrawns,
        'gaps': gaps,
        'notice': NOTICE,
    }


def check_state(state_path) -> dict:
    """只读核对台账内部一致性与引用可解析性；尽量一次报全，不因一处失败中止。"""
    state_path = Path(state_path)
    errors = []
    warnings = []
    task = ''
    rounds_count = 0
    entries_count = 0
    format_name = None
    try:
        state = read_json(state_path)
    except TaskStateError as exc:
        return {'ok': False, 'format': None, 'task': '', 'rounds': 0, 'entries': 0,
                'errors': [str(exc)], 'warnings': [], 'scope': SCOPE}
    if not isinstance(state, dict):
        errors.append('状态台账须为 JSON 对象。')
        return {'ok': False, 'format': None, 'task': '', 'rounds': 0, 'entries': 0,
                'errors': errors, 'warnings': warnings, 'scope': SCOPE}
    format_name = state.get('format')
    if state.get('schema_version') != SCHEMA_VERSION:
        errors.append('schema_version 须为 1。')
    if format_name != FORMAT:
        errors.append(f'format 须为 {FORMAT}。')
    if isinstance(state.get('task'), str):
        task = state['task']
    rounds = state.get('rounds')
    if not isinstance(rounds, list):
        errors.append('rounds 须为列表。')
        rounds = []
    rounds_count = len(rounds)
    seen_rounds = set()
    known_ids = set()
    prior_numbers = []
    for index, round_obj in enumerate(rounds):
        if not isinstance(round_obj, dict):
            errors.append(f'第 {index + 1} 项不是对象。')
            continue
        number = round_obj.get('round')
        if not isinstance(number, int) or isinstance(number, bool):
            errors.append(f'第 {index + 1} 轮的轮次号不是整数: {number!r}')
        else:
            if number in seen_rounds:
                errors.append(f'存在重复轮次号: {number}')
            elif number != index + 1:
                errors.append(f'轮次号不连续：期望 {index + 1}，得到 {number!r}')
            seen_rounds.add(number)
        extra = set(round_obj) - (ROUND_KEYS | RUNTIME_ROUND_KEYS)
        if extra:
            errors.append(f'第 {number} 轮含未知字段: ' + ', '.join(sorted(extra)))
        if 'central_judgement' in round_obj:
            judgement = round_obj.get('central_judgement')
            if not isinstance(judgement, str):
                errors.append(f'第 {number} 轮 central_judgement 须为文本。')
            elif judgement == '':
                errors.append(f'第 {number} 轮声明了 central_judgement 却为空串。')
        if 'manuscript' in round_obj:
            document = round_obj['manuscript']
            if not isinstance(document, dict) or not (isinstance(document.get('path'), str) and document['path'].strip()):
                errors.append(f'第 {number} 轮 manuscript 缺 path。')
        for identity in IDENTITIES:
            value = round_obj.get(identity, [])
            if not isinstance(value, list):
                errors.append(f'第 {number} 轮 {identity} 须为条目列表。')
                continue
            for entry in value:
                entries_count += 1
                if not isinstance(entry, dict):
                    errors.append(f'第 {number} 轮 {identity} 含非对象条目。')
                    continue
                identifier = entry.get('id')
                if isinstance(identifier, str) and identifier in known_ids:
                    errors.append(f'条目标识重复: {identifier}')
                try:
                    validate_entry(entry, identity, f'第 {number} 轮 {identity}',
                                   prior_rounds=prior_numbers, known_ids=known_ids,
                                   current_round=number, stored=True)
                except TaskStateError as exc:
                    errors.append(str(exc))
                if isinstance(identifier, str):
                    known_ids.add(identifier)
        prior_numbers.append(number if isinstance(number, int) else index + 1)
    if rounds and not any(isinstance(r.get('central_judgement'), str) and r.get('central_judgement').strip()
                          for r in rounds if isinstance(r, dict)):
        warnings.append('整个台账尚未登记任何 central_judgement。')
    if not errors and not known_ids:
        warnings.append('台账为空，尚无可接续的判断。')
    return {
        'ok': not errors,
        'format': format_name,
        'task': task,
        'rounds': rounds_count,
        'entries': entries_count,
        'errors': errors,
        'warnings': warnings,
        'scope': SCOPE,
    }


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True,
                        help='用户选定的状态台账 JSON；不写技能安装目录、不写宿主全局记忆')
    commands = parser.add_subparsers(dest='command', required=True)
    start = commands.add_parser('init', help='以 --task 初始化一份新台账，已存在即拒绝')
    start.add_argument('--task', required=True, help='任务原文或共同问题')
    record = commands.add_parser('record', help='追加一轮并原子提交')
    record.add_argument('--record', type=Path, required=True, help='轮次记录 JSON')
    commands.add_parser('list', help='只读列出各轮的轮次号、问题与条目计数')
    commands.add_parser('brief', help='只读生成供接续的摘要')
    commands.add_parser('check', help='只读核对内部一致性与引用可解析性')
    args = parser.parse_args(argv)
    try:
        if args.command == 'init':
            result = init_state(args.state, args.task)
        elif args.command == 'record':
            result = add_round(args.state, args.record)
        elif args.command == 'list':
            result = render_list(load_state(args.state))
        elif args.command == 'brief':
            result = render_brief(load_state(args.state))
        else:
            result = check_state(args.state)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if isinstance(result, dict) and result.get('ok') is False else 0
    except (OSError, UnicodeError, ValueError, TypeError) as error:
        print(f'任务状态处理失败：{error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
