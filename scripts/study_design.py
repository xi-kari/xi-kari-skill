#!/usr/bin/env python3
"""Turn unresolved substantive questions into an executable study design.

Each competing proposition must name at least one observation that would tell it
apart from the others; a design where nothing distinguishes them is refused rather
than passed along. Fields may be left out — missing stays missing and is reported
as missing, never filled with a zero or a plausible-looking default. The tool does
not judge whether the research is worth doing, whether the observations are
obtainable, or whether any source is trustworthy.
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
    from xikari_paths import require_external_output
finally:
    sys.path.pop(0)


FORMAT = 'xikari-study-design-1'
MARK = '<!-- xikari-study-design -->'
IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z')
NOTICE = '本报告只检查结构与区分观察是否填写，不判断研究是否值得做、观察是否真实可获得或来源是否可信。'
SUBSTANTIVE = ('observation_targets', 'time_window', 'required_materials',
               'hold_conditions', 'change_conditions', 'confounders', 'stop_conditions', 'execution')
LABELS = {
    'observation_targets': '观察对象与位置',
    'time_window': '时间窗',
    'required_materials': '所需材料与字段',
    'hold_conditions': '保持的条件',
    'change_conditions': '改变的条件',
    'confounders': '混杂与选择偏差',
    'stop_conditions': '停止条件',
    'execution': '执行者与权限',
    'supports': '支持该命题的观察',
    'excludes': '排除该命题的观察',
    'distinguishing': '能区分该命题的观察',
}
MISSING = '（设计未填写，保留为缺失，未补默认值）'


class StudyDesignError(ValueError):
    """Invalid study-design data."""


def read_design(path: Path) -> dict:
    data = Path(path).read_bytes()
    if len(data) > 4 * 1024 * 1024:
        raise StudyDesignError('研究设计超过4MiB，请拆分为多个设计。')
    text = data.decode('utf-8-sig')

    def reject_duplicates(pairs):
        seen = {}
        for key, value in pairs:
            if key in seen:
                raise StudyDesignError(f'JSON含重复键: {key}')
            seen[key] = value
        return seen

    try:
        return json.loads(text, object_pairs_hook=reject_duplicates)
    except json.JSONDecodeError as exc:
        raise StudyDesignError(f'研究设计不是有效JSON: {exc}') from exc


def text_field(item, field, where, required=False, limit=8000):
    value = item.get(field, '')
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise StudyDesignError(f'{where}.{field}须为{"非空" if required else ""}文本，不超过{limit}字符。')
    return value


def text_list(item, field, where):
    value = item.get(field, [])
    if not isinstance(value, list) or any(not isinstance(entry, str) or not entry.strip() for entry in value):
        raise StudyDesignError(f'{where}.{field}应是文字列表。')
    return value


def validate_design(design) -> dict:
    if not isinstance(design, dict) or design.get('schema_version') != 1:
        raise StudyDesignError('研究设计须为schema_version=1的JSON对象。')
    extra = set(design) - {'schema_version', 'question', 'propositions', *SUBSTANTIVE}
    if extra:
        raise StudyDesignError('研究设计含未知字段，不能静默忽略: ' + ', '.join(sorted(extra)))
    question = text_field(design, 'question', '研究设计', required=True)
    propositions = design.get('propositions')
    if not isinstance(propositions, list) or not propositions:
        raise StudyDesignError('propositions须为非空列表：没有竞争命题就无法设计区分观察。')
    seen = set()
    reported = []
    for item in propositions:
        if not isinstance(item, dict):
            raise StudyDesignError('每个命题须为对象。')
        unknown = set(item) - {'id', 'statement', 'supports', 'excludes', 'distinguishing'}
        if unknown:
            raise StudyDesignError('命题含未知字段，不能静默忽略: ' + ', '.join(sorted(unknown)))
        identifier = item.get('id')
        if identifier is not None:
            if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
                raise StudyDesignError(f'命题ID须为字母或数字开头、不超过96字符: {identifier!r}')
            if identifier in seen:
                raise StudyDesignError(f'命题ID重复: {identifier}')
            seen.add(identifier)
        statement = text_field(item, 'statement', f'命题 {identifier or "（未命名）"}', required=True)
        supports = text_list(item, 'supports', f'命题 {identifier or statement[:12]}')
        excludes = text_list(item, 'excludes', f'命题 {identifier or statement[:12]}')
        distinguishing = text_list(item, 'distinguishing', f'命题 {identifier or statement[:12]}')
        if not distinguishing:
            raise StudyDesignError(
                f'命题「{statement[:30]}」没有能区分它的观察（distinguishing）。'
                '无法与其他命题区分的部分不能作为研究命题；请补上区分观察，或改为已知事实写入正文。')
        missing = [field for field, value in (('supports', supports), ('excludes', excludes)) if not value]
        reported.append({
            'id': identifier,
            'statement': statement,
            'distinguishing_count': len(distinguishing),
            'missing': missing,
            'supports': supports,
            'excludes': excludes,
            'distinguishing': distinguishing,
        })
    missing_top = []
    for field in SUBSTANTIVE:
        if field == 'execution':
            entries = design.get(field, [])
            if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
                raise StudyDesignError('execution应是对象列表；每项说明由谁在什么权限内完成。')
            for entry in entries:
                unknown = set(entry) - {'who', 'authority'}
                if unknown:
                    raise StudyDesignError('execution含未知字段，不能静默忽略: ' + ', '.join(sorted(unknown)))
                text_field(entry, 'who', 'execution', required=True)
                text_field(entry, 'authority', 'execution', required=True)
            if not entries:
                missing_top.append(field)
            continue
        if field == 'time_window':
            if not text_field(design, field, '研究设计').strip():
                missing_top.append(field)
            continue
        if not text_list(design, field, '研究设计'):
            missing_top.append(field)
    return {
        'format': FORMAT,
        'valid': True,
        'question': question,
        'proposition_count': len(reported),
        'propositions': [{key: value for key, value in item.items()
                          if key in ('id', 'statement', 'distinguishing_count', 'missing')}
                         for item in reported],
        'missing': missing_top,
        'notice': NOTICE,
    }


def render_markdown(report: dict, design: dict) -> str:
    """Render the design a next person could actually run, keeping missing fields visible."""
    lines = [MARK, '', '# 研究与采集说明', '', f"**研究问题：** {report['question']}", '',
             '本文件说明要区分哪些命题、看哪些对象、记录什么字段，以及什么情况下停止。'
             '缺失的字段保留为缺失，不补默认值。', '',
             '## 要区分的竞争命题', '']
    for item in design.get('propositions', []):
        lines.append(f"### {item.get('statement', '（未命名命题）')}")
        if item.get('id'):
            lines.append('')
            lines.append(f"标识：{item['id']}")
        lines.append('')
        for field in ('supports', 'excludes', 'distinguishing'):
            values = item.get(field) or []
            lines.append(f"**{LABELS[field]}：**")
            lines.append('')
            if values:
                for entry in values:
                    lines.append(f'- {entry}')
            else:
                lines.append(f'- {MISSING}')
            lines.append('')
    lines.append('## 观察与记录安排')
    lines.append('')
    for field in ('observation_targets', 'time_window', 'required_materials',
                  'hold_conditions', 'change_conditions', 'confounders', 'stop_conditions'):
        lines.append(f"### {LABELS[field]}")
        lines.append('')
        if field == 'time_window':
            value = (design.get(field) or '').strip()
            lines.append(f"- {value}" if value else f'- {MISSING}')
        else:
            values = design.get(field) or []
            if values:
                for entry in values:
                    lines.append(f'- {entry}')
            else:
                lines.append(f'- {MISSING}')
        lines.append('')
    lines.append('### 执行者与权限')
    lines.append('')
    entries = design.get('execution') or []
    if entries:
        for entry in entries:
            lines.append(f"- {entry.get('who', '')}：{entry.get('authority', '')}")
    else:
        lines.append(f'- {MISSING}')
    lines.append('')
    if report['missing']:
        lines.append('## 仍然缺失的字段')
        lines.append('')
        for field in report['missing']:
            lines.append(f"- {LABELS.get(field, field)}")
        lines.append('')
        lines.append('缺失项须由实际承担研究的人补齐；本工具不会代为填写。')
        lines.append('')
    lines.append(f"> {NOTICE}")
    lines.append('')
    return '\n'.join(lines)


def write_document(text: str, output: Path, force: bool = False) -> Path:
    require_external_output(output, __file__)
    output = Path(output)
    if output.exists() and (not force or not owned_output(output)):
        raise StudyDesignError(f'输出已存在且不属于本工具产物: {output}；使用新路径，或仅对本工具产物使用--force。')
    output.parent.mkdir(parents=True, exist_ok=True)
    lock = output.with_name(output.name + '.lock')
    require_external_output(lock, __file__)
    temporary = None
    owns_lock = False
    try:
        fd, name = tempfile.mkstemp(prefix='.study-design-', suffix='.tmp', dir=output.parent)
        temporary = Path(name)
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise StudyDesignError(f'输出位置有其他写入者或遗留锁: {lock}；未自动覆盖。') from error
        owns_lock = True
        os.close(descriptor)
        if output.exists() and (not force or not owned_output(output)):
            raise StudyDesignError(
                f'输出在取得写锁前已被其他写入者创建或改动: {output}；本次未覆盖，请重读后重试或改用新路径。')
        os.replace(temporary, output)
        temporary = None
        return output
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if owns_lock:
            lock.unlink(missing_ok=True)


def owned_output(path: Path) -> bool:
    try:
        return MARK in path.read_text(encoding='utf-8')[:2048]
    except (OSError, UnicodeError):
        return False


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--design', type=Path, required=True, help='研究设计 JSON')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('validate', help='校验结构并报告缺失；不写文件')
    render = commands.add_parser('render', help='生成可读的研究与采集说明')
    render.add_argument('--output', '-o', type=Path, required=True, help='安装目录之外的输出文件')
    render.add_argument('--force', action='store_true', help='仅覆盖本工具先前生成的说明')
    args = parser.parse_args(argv)
    try:
        if args.command == 'render' and Path(args.design).resolve() == args.output.resolve():
            raise StudyDesignError('输出路径与研究设计输入是同一个文件；为避免覆盖输入，请改用其他路径。')
        design = read_design(args.design)
        report = validate_design(design)
        if args.command == 'validate':
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
        target = write_document(render_markdown(report, design), args.output, args.force)
        print(json.dumps({'output': str(target.resolve()), 'missing': report['missing'],
                          'notice': report['notice']}, ensure_ascii=False))
        return 0
    except (OSError, UnicodeError, StudyDesignError, ValueError) as error:
        print(f'研究设计处理失败：{error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
