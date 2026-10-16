#!/usr/bin/env python3
"""Track the substantive claims of one task with their basis, status and change conditions.

This is an inventory, not an evaluator. It records what each conclusion rests on,
which conditions would overturn it, and which competing claims remain open. It does
not judge truth, assign confidence, or certify that analysis is complete.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from evidence import MaterialError, load_catalog as load_material_catalog
    from xikari_paths import require_external_output
finally:
    sys.path.pop(0)


FORMAT = 'xikari-claims-1'
KINDS = {'fact', 'structure', 'mechanism', 'forward', 'value', 'interpretation'}
STATUSES = {'proposed', 'supported', 'contested', 'refuted', 'withdrawn', 'unknown'}
DIRECTIONS = {'supports', 'undercuts', 'context'}
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z')
SECTIONS = {'', 'list', 'search', 'show', 'add', 'check'}


class ClaimError(ValueError):
    """Invalid claim data, raised as ValueError to match the other tool scripts."""


def read_json(path: Path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except OSError as exc:
        raise ClaimError(f'无法读取 {path}: {exc}') from exc
    except json.JSONDecodeError as exc:
        raise ClaimError(f'{path} 不是有效JSON: {exc}') from exc


def text_of(item, field, where, required=False, limit=8000):
    value = item.get(field, '')
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise ClaimError(f'{where}.{field}须为{"非空" if required else ""}文本，不超过{limit}字符。')
    return value


def text_list(item, field, where, required=False):
    value = item.get(field, [])
    if not isinstance(value, list) or any(not isinstance(entry, str) or not entry.strip() for entry in value):
        raise ClaimError(f'{where}.{field}应是文字列表。')
    if required and not value:
        raise ClaimError(f'{where}.{field}不能为空：{field}是承担关键结论的必要说明。')
    return value


def validate_claim(case) -> None:
    if not isinstance(case, dict):
        raise ClaimError('主张必须是JSON对象')
    for key in ('id', 'statement'):
        if not isinstance(case.get(key), str) or not case[key].strip():
            raise ClaimError(f'主张缺少 {key}')
    if not ID.fullmatch(case['id']):
        raise ClaimError('id仅使用字母、数字、点、下划线和连字符，不超过96字符')
    if len(case['statement']) > 8000:
        raise ClaimError('statement不超过8000字符')
    if case.get('kind') not in KINDS:
        raise ClaimError('kind须为fact、structure、mechanism、forward、value或interpretation')
    if case.get('status') not in STATUSES:
        raise ClaimError('status须为proposed、supported、contested、refuted、withdrawn或unknown')
    where = f'主张 {case["id"]}'
    for field in ('reasons', 'change_conditions', 'conditions', 'open_questions'):
        text_list(case, field, where)
    direction_of = []
    for entry in case.get('evidence', []):
        if not isinstance(entry, dict):
            raise ClaimError(f'{where}.evidence 每项须为对象')
        if not isinstance(entry.get('catalog'), str) or not entry['catalog'].strip():
            raise ClaimError(f'{where}.evidence 每项须指出 catalog')
        if not isinstance(entry.get('clip'), str) or not entry['clip'].strip():
            raise ClaimError(f'{where}.evidence 每项须指出 clip')
        if entry.get('direction') not in DIRECTIONS:
            raise ClaimError(f'{where}.evidence 每项须声明 direction 为 supports、undercuts 或 context')
        direction_of.append(entry['direction'])
    for entry in case.get('theory', []):
        if not isinstance(entry, dict) or not isinstance(entry.get('section'), str) or not entry['section'].strip():
            raise ClaimError(f'{where}.theory 每项须给出 section，如 4.17 或 C.3')
    if case.get('status') == 'supported' and 'supports' not in direction_of and not case.get('theory'):
        raise ClaimError(f'{where}: status=supported 须有支持性依据；先登记 evidence 或 theory，或改用 proposed')
    if case.get('status') == 'contested':
        counterclaims = case.get('counterclaims')
        if not isinstance(counterclaims, list) or not counterclaims:
            raise ClaimError(f'{where}: status=contested 须列出仍然成立的竞争主张 counterclaims')
    if case.get('status') == 'withdrawn':
        text_of(case, 'withdraw_reason', where, required=True)
    for entry in case.get('counterclaims', []):
        if not isinstance(entry, dict) or not isinstance(entry.get('statement'), str) or not entry['statement'].strip():
            raise ClaimError(f'{where}.counterclaims 每项须给出 statement')
    if case.get('kind') == 'forward':
        registration = case.get('registration')
        if not isinstance(registration, dict):
            raise ClaimError(f'{where}: 前瞻主张须在结果之前登记 registration（window、baseline、criteria）')
        for field in ('window', 'baseline', 'criteria'):
            if not isinstance(registration.get(field), str) or not registration[field].strip():
                raise ClaimError(f'{where}.registration 缺少 {field}')
        if case.get('status') == 'supported' and not case.get('outcome'):
            raise ClaimError(f'{where}: 前瞻主张在取得结果之前不能标为 supported；先登记 outcome')
    if case.get('load_bearing'):
        text_list(case, 'change_conditions', where, required=True)
        if not case.get('counterclaims'):
            raise ClaimError(f'{where}: 承担关键结论的主张须列出最强竞争主张 counterclaims')


def load_ledger(path: Path) -> dict:
    if not Path(path).exists():
        return {'schema_version': 1, 'format': FORMAT, 'claims': []}
    ledger = read_json(path)
    if not isinstance(ledger, dict) or ledger.get('schema_version') != 1 or not isinstance(ledger.get('claims'), list):
        raise ClaimError('目标不是可识别的主张台账，不会覆盖')
    seen = set()
    for case in ledger['claims']:
        validate_claim(case)
        if case['id'] in seen:
            raise ClaimError('台账包含重复主张标识')
        seen.add(case['id'])
    return ledger


def save_ledger(path: Path, ledger: dict, expected: bytes | None) -> None:
    require_external_output(path, __file__)
    lock = Path(path).with_name(Path(path).name + '.lock')
    require_external_output(lock, __file__)
    path = Path(path).resolve()
    lock = path.with_name(path.name + '.lock')
    require_external_output(lock, __file__)
    path.parent.mkdir(parents=True, exist_ok=True)
    ledger.setdefault('format', FORMAT)
    payload = (json.dumps(ledger, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    temporary = None
    owns_lock = False
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.claims-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise ValueError('主张台账有其他写入者或遗留写锁；本次未提交。确认写入结束并重读后再添加，不自动移除锁') from error
        owns_lock = True
        os.close(descriptor)
        current = path.read_bytes() if path.exists() else None
        if current != expected:
            raise ValueError('主张台账已由其他工作改变，请重读后再添加')
        if expected is None:
            try:
                os.link(temporary, path)
            except FileExistsError as error:
                raise ValueError('主张台账在首次提交前已出现；本次未覆盖，请重读后再添加') from error
        else:
            os.replace(temporary, path)
            temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if owns_lock:
            lock.unlink(missing_ok=True)


def add_claim(ledger_path: Path, record_path: Path) -> dict:
    require_external_output(ledger_path, __file__)
    if Path(ledger_path).resolve() == Path(record_path).resolve():
        raise ClaimError('主张记录和台账不能是同一文件')
    expected = ledger_path.read_bytes() if ledger_path.exists() else None
    ledger = load_ledger(ledger_path)
    case = read_json(record_path)
    validate_claim(case)
    existing = {entry['id'] for entry in ledger['claims']}
    if case['id'] in existing:
        raise ClaimError('主张标识已存在；修订时用新标识及 supersedes 保留原记录')
    if 'supersedes' in case:
        if case['supersedes'] not in existing:
            raise ClaimError('supersedes 所指旧主张不存在')
    case = dict(case)
    case['record_file'] = str(Path(record_path).resolve())
    ledger['claims'].append(case)
    save_ledger(ledger_path, ledger, expected)
    return case


def load_catalog_clips(path_text: str) -> dict:
    try:
        catalog = load_material_catalog(Path(path_text))
    except (MaterialError, TypeError) as exc:
        raise ClaimError(f'材料目录结构无效：{exc}') from exc
    return catalog['clips']


def check_ledger(ledger: dict, section_keys) -> dict:
    """Report resolvable references and declared-structure gaps. Never scores support."""
    sections = set(section_keys)
    errors, warnings = [], []
    catalogs: dict = {}
    for case in ledger.get('claims', []):
        identifier = case.get('id', '<未命名>')
        for entry in case.get('theory', []):
            section = entry.get('section')
            if section and section not in sections:
                errors.append(f'{identifier}: 理论小节 {section} 在原文索引中不存在')
            elif not section:
                warnings.append(f'{identifier}: theory 条目缺少 section')
        for entry in case.get('evidence', []):
            catalog_path = entry.get('catalog', '')
            if catalog_path not in catalogs:
                try:
                    catalogs[catalog_path] = load_catalog_clips(catalog_path)
                except (ClaimError, OSError) as exc:
                    catalogs[catalog_path] = None
                    errors.append(f'{identifier}: 材料目录无法读取 {catalog_path}: {exc}')
            clips = catalogs[catalog_path]
            if clips is None:
                continue
            clip = entry.get('clip', '')
            if clip not in clips:
                errors.append(f'{identifier}: 片段 {clip} 不在 {catalog_path} 中')
            else:
                record = clips[clip]
                if isinstance(record, dict) and record.get('source_id') and not record.get('support_boundary'):
                    warnings.append(f'{identifier}: 片段 {clip} 未声明支持范围 support_boundary')
        if case.get('status') == 'unknown':
            warnings.append(f'{identifier}: 状态为 unknown，正文不应把它当作已定结论')
    return {
        'ok': not errors, 'claims': len(ledger.get('claims', [])),
        'errors': errors, 'warnings': warnings,
        'scope': '仅核对引用是否可解析及已声明结构是否齐全；不判断依据是否充分、来源是否可信或分析是否完成。',
    }


def find_claims(ledger: dict, query: str) -> list[dict]:
    terms = query.casefold().split()
    return [case for case in ledger.get('claims', []) if all(term in json.dumps(case, ensure_ascii=False).casefold() for term in terms)]


def known_sections() -> set[str]:
    """Read the theory section index used to resolve theory references."""
    import read_source
    lines = read_source.SOURCE.read_text(encoding='utf-8-sig').splitlines()
    sections, _ = read_source.build_index(lines)
    return set(sections)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path, required=True, help='用户选定任务目录中的主张台账；不写入技能目录或全局记忆')
    commands = parser.add_subparsers(dest='command', required=True)
    add = commands.add_parser('add', help='保存一份主张记录')
    add.add_argument('--record', type=Path, required=True)
    commands.add_parser('list', help='列出主张、类型、状态与承担关系')
    search = commands.add_parser('search', help='按字面词语检索主张')
    search.add_argument('query')
    show = commands.add_parser('show', help='显示一条主张的全部字段')
    show.add_argument('id')
    commands.add_parser('check', help='核对理论小节与材料片段引用能否解析')
    args = parser.parse_args()
    try:
        if args.command == 'add':
            result = add_claim(args.ledger, args.record)
        else:
            ledger = load_ledger(args.ledger)
            if args.command == 'list':
                result = [{key: case.get(key) for key in ('id', 'kind', 'status', 'load_bearing', 'supersedes')}
                          for case in ledger['claims']]
            elif args.command == 'search':
                result = find_claims(ledger, args.query)
            elif args.command == 'show':
                result = next((case for case in ledger['claims'] if case['id'] == args.id), None)
                if result is None:
                    raise ClaimError('未找到该主张')
            else:
                result = check_ledger(ledger, known_sections())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if isinstance(result, dict) and result.get('ok') is False else 0
    except (OSError, UnicodeError, ClaimError, ValueError, TypeError) as error:
        print(f'主张台账处理失败：{error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
