"""Keep explicitly selected cases in a user-chosen, task-independent local library."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from xikari_paths import require_external_output
finally:
    sys.path.pop(0)


OUTCOMES = {'not_observed', 'user_reported', 'observed', 'mixed', 'unknown'}


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def load_library(path: Path) -> dict:
    if not path.exists():
        return {'schema_version': 1, 'cases': []}
    library = read_json(path)
    if not isinstance(library, dict) or library.get('schema_version') != 1 or not isinstance(library.get('cases'), list):
        raise ValueError('目标不是可识别的案例资料库，不会覆盖')
    seen = set()
    for entry in library['cases']:
        validate_case(entry)
        if entry['id'] in seen:
            raise ValueError('案例库包含重复标识')
        seen.add(entry['id'])
    return library


def validate_case(case: dict) -> None:
    if not isinstance(case, dict):
        raise ValueError('案例必须是 JSON 对象')
    for key in ('id', 'title', 'question'):
        if not isinstance(case.get(key), str) or not case[key].strip():
            raise ValueError(f'案例缺少 {key}')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}', case['id']):
        raise ValueError('id 仅使用字母、数字、点、下划线和连字符，长度不超过96')
    for key in ('conditions', 'interpretations', 'counterexamples', 'choices', 'transfer_limits', 'tags'):
        if key in case and (not isinstance(case[key], list) or not all(isinstance(x, str) for x in case[key])):
            raise ValueError(f'{key} 应是文字列表')
    if 'sources' in case:
        if not isinstance(case['sources'], list) or not all(isinstance(x, dict) for x in case['sources']):
            raise ValueError('sources 应是来源对象列表')
        for source in case['sources']:
            if not any(isinstance(source.get(k), str) and source[k].strip() for k in ('path', 'url', 'catalog_id', 'description')):
                raise ValueError('来源应保留位置、材料标识或来源说明')
    outcome = case.get('outcome', {'status': 'not_observed'})
    if not isinstance(outcome, dict) or outcome.get('status') not in OUTCOMES:
        raise ValueError('outcome.status 必须区分未观察、用户报告、实际观察、混合或未知')
    if outcome['status'] in ('observed', 'user_reported', 'mixed'):
        if not isinstance(outcome.get('basis'), str) or not outcome['basis'].strip():
            raise ValueError('结果记录须说明观察或报告依据，不能把原方案当结果')
    for key in ('theory', 'artifacts'):
        if key in case and not isinstance(case[key], (dict, list)):
            raise ValueError(f'{key} 应保留可读的来源或成果位置')


def save_library(path: Path, library: dict, expected: bytes | None) -> None:
    require_external_output(path, __file__)
    require_external_output(path.with_name(path.name + '.lock'), __file__)
    path = path.resolve()
    require_external_output(path.with_name(path.name + '.lock'), __file__)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(library, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    temporary = None
    lock = path.with_name(path.name + '.lock')
    owns_lock = False
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.casebook-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise ValueError('案例库有其他写入者或遗留写锁；本次未提交。确认写入结束并重读后再添加，不自动移除锁') from error
        owns_lock = True
        os.close(descriptor)
        current = path.read_bytes() if path.exists() else None
        if current != expected:
            raise ValueError('案例库已由其他工作改变，请重读后再添加')
        if expected is None:
            # Publish the already-flushed file without replacing a new target.
            try:
                os.link(temporary, path)
            except FileExistsError as error:
                raise ValueError('案例库在首次提交前已出现；本次未覆盖，请重读后再添加') from error
        else:
            os.replace(temporary, path)
            temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if owns_lock:
            lock.unlink(missing_ok=True)


def add_case(library_path: Path, record_path: Path) -> dict:
    require_external_output(library_path, __file__)
    if library_path.resolve() == record_path.resolve():
        raise ValueError('案例记录和资料库不能是同一文件')
    expected = library_path.read_bytes() if library_path.exists() else None
    library = load_library(library_path)
    case = read_json(record_path)
    validate_case(case)
    existing = {entry['id'] for entry in library['cases']}
    if case['id'] in existing:
        raise ValueError('案例标识已存在；补充现实结果时用新标识及 supersedes 保留原判断')
    if 'supersedes' in case and case['supersedes'] not in existing:
        raise ValueError('supersedes 所指旧案例不存在')
    case = dict(case)
    case.setdefault('outcome', {'status': 'not_observed'})
    case['record_file'] = str(record_path.resolve())
    case['saved_at'] = datetime.now(timezone.utc).isoformat()
    library['cases'].append(case)
    save_library(library_path, library, expected)
    return case


def find_cases(library: dict, query: str) -> list[dict]:
    terms = query.casefold().split()
    return [case for case in library['cases'] if all(term in json.dumps(case, ensure_ascii=False).casefold() for term in terms)]


def main() -> int:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', type=Path, required=True, help='用户选定的案例库 JSON；不使用全局记忆目录')
    commands = parser.add_subparsers(dest='command', required=True)
    add = commands.add_parser('add', help='保存一份明确选择的案例记录')
    add.add_argument('--record', type=Path, required=True)
    commands.add_parser('list', help='列出案例及结果身份')
    search = commands.add_parser('search', help='按字面词语检索；不推定结构相似')
    search.add_argument('query')
    show = commands.add_parser('show', help='显示完整案例和来源位置')
    show.add_argument('id')
    args = parser.parse_args()
    try:
        if args.command == 'add':
            result = add_case(args.library, args.record)
        else:
            library = load_library(args.library)
            if args.command == 'list':
                result = [{key: case.get(key) for key in ('id', 'title', 'question', 'outcome', 'supersedes')} for case in library['cases']]
            elif args.command == 'search':
                result = find_cases(library, args.query)
            else:
                result = next((x for x in library['cases'] if x['id'] == args.id), None)
                if result is None:
                    raise ValueError('未找到该案例')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, UnicodeError, ValueError, TypeError) as error:
        print(f'案例资料处理失败：{error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
