#!/usr/bin/env python3
"""Validate, render and trace an authored research report and its open issues.

This tool never performs the research, verifies source truth or upgrades a claim.
It preserves authored prose and makes declared limitations and dependencies visible.
"""

from __future__ import annotations

import argparse
from collections import deque
import ctypes
import errno
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from read_source import build_index
    from xikari_paths import require_external_output
finally:
    sys.path.pop(0)


FORMAT = 'xikari-research-1'
NOTICE = '本工具只检查记录结构、引用与依赖并排版作者正文，不证明来源真实、论证充分、研究完成或现实效果。'
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z')
ANCHOR = re.compile(r'(?:\d+|[A-D])(?:\.\d+)+\Z')
KINDS = {
    'descriptive': '描述判断', 'causal': '因果判断', 'interpretive': '解释性判断',
    'normative': '规范判断', 'model_result': '模型内结果', 'candidate': '候选',
    'unknown': '未知', 'conditional_projection': '条件推演',
}
STATUSES = {
    'supported': '在声明范围内有支持', 'proposed': '提出待查', 'contested': '存在争议',
    'unknown': '未知', 'refuted': '已被反驳', 'withdrawn': '已撤回',
}
CATEGORIES = {
    'material_gap': '材料不足', 'identification_limit': '方法与识别限度',
    'domain_method': '领域知识或方法需要接入', 'mapping_gap': '映射或概念表达不足',
    'theory_candidate': '理论问题候选', 'normative_disagreement': '规范分歧',
    'implementation_gap': '技能实现或成品缺口',
}
ISSUE_STATUSES = {
    'open': '未决', 'under_investigation': '研究中', 'partially_resolved': '部分解决',
    'resolved_within_scope': '在限定范围内解决', 'withdrawn': '撤回', 'superseded': '被后续问题替代',
}
ACTIVE = {'open', 'under_investigation', 'partially_resolved'}
MAX_ITEMS = 2000


class ResearchError(ValueError):
    """An invalid or unsafe research operation."""


@lru_cache(maxsize=1)
def theory_index():
    """Locate bundled section IDs and source version; not a theory-content review."""
    source = Path(__file__).resolve().parents[1] / 'source' / 'Xikari-条件结构与转化论.md'
    raw = source.read_bytes()
    sections, _parts = build_index(raw.decode('utf-8-sig').splitlines())
    return {'anchors': frozenset(sections), 'sha256': hashlib.sha256(raw).hexdigest()}


def read_research(path: Path) -> dict:
    with Path(path).open('rb') as stream:
        raw = stream.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024:
        raise ResearchError('研究记录超过 4 MiB，请按实际专题拆分。')

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ResearchError(f'JSON 含重复字段：{key}')
            result[key] = value
        return result

    def nonfinite(value):
        raise ResearchError(f'JSON 不允许非有限数：{value}')

    try:
        return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique,
                          parse_constant=nonfinite)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ResearchError(f'无效研究 JSON：{exc}') from exc


def object_fields(value, required, optional, where):
    if not isinstance(value, dict):
        raise ResearchError(f'{where} 须为对象。')
    if any(not isinstance(key, str) for key in value):
        raise ResearchError(f'{where} 字段名须为文本。')
    missing = set(required) - set(value)
    extra = set(value) - set(required) - set(optional)
    if missing or extra:
        raise ResearchError(f'{where} 缺字段 {sorted(missing)}；未知字段 {sorted(extra)}。')


def text(item, key, where, required=True, limit=100000):
    value = item[key]
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise ResearchError(f'{where}.{key} 须为{"非空" if required else ""}文本，不超过 {limit} 字符。')
    if '\x00' in value:
        raise ResearchError(f'{where}.{key} 不允许 NUL 字符。')
    return value


def text_list(item, key, where, required=False):
    value = item[key]
    if (not isinstance(value, list) or len(value) > MAX_ITEMS
            or any(not isinstance(v, str) or not v.strip() or len(v) > 100000 for v in value)
            or (required and not value)):
        raise ResearchError(f'{where}.{key} 须为{"非空" if required else ""}文本列表。')
    if len(set(value)) != len(value):
        raise ResearchError(f'{where}.{key} 含重复项。')
    return value


def choice(item, key, options, where):
    value = item[key]
    if not isinstance(value, str) or value not in options:
        raise ResearchError(f'{where}.{key} 须为 {", ".join(sorted(options))} 之一。')
    return value


def rows(data, key, required=False):
    value = data[key]
    if (not isinstance(value, list) or len(value) > MAX_ITEMS
            or (required and not value)):
        raise ResearchError(f'{key} 须为{"非空" if required else ""}列表，最多 {MAX_ITEMS} 项。')
    return value


def validate_research(data) -> dict:
    """Check explicit data and graph contracts, without judging substantive truth."""
    try:
        encoded = json.dumps(data, allow_nan=False, ensure_ascii=False).encode('utf-8')
    except (ValueError, TypeError, RecursionError) as exc:
        raise ResearchError('研究输入须为有限、无循环的 JSON 数据。') from exc
    if len(encoded) > 4 * 1024 * 1024:
        raise ResearchError('研究记录超过 4 MiB，请按实际专题拆分。')
    object_fields(data, {'schema_version', 'title', 'question', 'scope', 'method', 'summary',
                         'summary_refs', 'inputs', 'findings', 'issues', 'issue_assessment'}, set(), '研究')
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise ResearchError('schema_version 须为整数 1。')
    for key in ('title', 'question', 'scope', 'method', 'summary', 'issue_assessment'):
        text(data, key, '研究')
    text_list(data, 'summary_refs', '研究', required=True)
    inputs = rows(data, 'inputs', required=True)
    findings = rows(data, 'findings', required=True)
    issues = rows(data, 'issues')
    used = set()

    def identifier(item, where):
        value = text(item, 'id', where, limit=96)
        if not ID.fullmatch(value) or value in used:
            raise ResearchError(f'{where} ID 无效或重复：{value}')
        used.add(value)

    for item in inputs:
        object_fields(item, {'id', 'kind', 'label', 'content', 'locator', 'status'}, set(), '输入')
        identifier(item, '输入')
        choice(item, 'kind', {'source', 'premise', 'mapping'}, item['id'])
        choice(item, 'status', {'known', 'unknown', 'synthetic'}, item['id'])
        for key in ('label', 'content'):
            text(item, key, item['id'])
        text(item, 'locator', item['id'], required=item['kind'] == 'source' and item['status'] != 'unknown')
    input_ids = {item['id'] for item in inputs}
    for item in findings:
        object_fields(item, {'id', 'title', 'kind', 'status', 'body', 'depends_on',
                             'limitations', 'change_conditions'}, set(), '结论')
        identifier(item, '结论')
        choice(item, 'kind', KINDS, item['id'])
        choice(item, 'status', STATUSES, item['id'])
        for key in ('title', 'body'):
            text(item, key, item['id'])
        text_list(item, 'depends_on', item['id'], required=True)
        text_list(item, 'limitations', item['id'])
        text_list(item, 'change_conditions', item['id'], required=True)
    finding_ids = {item['id'] for item in findings}
    all_nodes = input_ids | finding_ids
    for item in findings:
        unknown = set(item['depends_on']) - all_nodes
        if unknown:
            raise ResearchError(f'{item["id"]} 引用未知依赖：{sorted(unknown)}')
    if set(data['summary_refs']) - finding_ids:
        raise ResearchError('summary_refs 只能引用已有结论 ID。')
    graph = {item['id']: list(item['depends_on']) for item in findings}
    order = topological_order(graph, input_ids)
    for item in issues:
        object_fields(item, {'id', 'title', 'categories', 'affected_findings', 'materiality',
                             'status', 'current_work', 'why_unresolved', 'consequence', 'next_work',
                             'status_reason', 'resolution_scope'}, {'theory'}, '问题')
        identifier(item, '问题')
        for key in ('title', 'current_work', 'why_unresolved', 'consequence', 'status_reason'):
            text(item, key, item['id'])
        text_list(item, 'categories', item['id'], required=True)
        if set(item['categories']) - set(CATEGORIES):
            raise ResearchError(f'{item["id"]} 含未知问题分类。')
        text_list(item, 'affected_findings', item['id'], required=True)
        if set(item['affected_findings']) - finding_ids:
            raise ResearchError(f'{item["id"]} 引用未知结论。')
        choice(item, 'materiality', {'major', 'minor'}, item['id'])
        choice(item, 'status', ISSUE_STATUSES, item['id'])
        text(item, 'next_work', item['id'], required=item['status'] in ACTIVE)
        text(item, 'resolution_scope', item['id'], required=item['status'] in {'partially_resolved', 'resolved_within_scope'})
        if ('theory_candidate' in item['categories']) != ('theory' in item):
            raise ResearchError(f'{item["id"]} 理论问题分类须且仅须附 theory 原命题与挑战。')
        if 'theory' in item:
            theory = item['theory']
            object_fields(theory, {'proposition', 'anchor', 'source_sha256', 'scope', 'challenge'}, set(), item['id'] + '.theory')
            for key in theory:
                text(theory, key, item['id'] + '.theory')
            if not ANCHOR.fullmatch(theory['anchor']):
                raise ResearchError('theory.anchor 须为不含 § 的小节编号，如 4.17.4。')
            if theory['source_sha256'] != theory_index()['sha256']:
                raise ResearchError('theory.source_sha256 与随包原文不一致；请回查版本及受影响命题。')
            if theory['anchor'] not in theory_index()['anchors']:
                raise ResearchError(f'theory.anchor 不存在于随包原文：{theory["anchor"]}')
    return {
        'format': FORMAT, 'structure_valid': True,
        'input_count': len(inputs), 'finding_count': len(findings), 'issue_count': len(issues),
        'unknown_inputs': [item['id'] for item in inputs if item['status'] == 'unknown'],
        'synthetic_inputs': [item['id'] for item in inputs if item['status'] == 'synthetic'],
        'finding_order': order, 'notice': NOTICE,
    }


def topological_order(graph, input_ids):
    """Iterative traversal avoids recursion limits on valid long dependency chains."""
    waiting = {key: len([ref for ref in refs if ref not in input_ids]) for key, refs in graph.items()}
    children = {key: [] for key in graph}
    for key, refs in graph.items():
        for ref in refs:
            if ref in children:
                children[ref].append(key)
    queue = deque(key for key in graph if not waiting[key])
    order = []
    while queue:
        key = queue.popleft()
        order.append(key)
        for child in children[key]:
            waiting[child] -= 1
            if not waiting[child]:
                queue.append(child)
    if len(order) != len(graph):
        raise ResearchError('结论依赖存在循环；请区分并列争议与实际推导依赖。')
    return order


def impact(data, changed) -> dict:
    """Find dependent findings; changes request review, never automatic rejection."""
    validate_research(data)
    if (not isinstance(changed, (list, tuple)) or not changed
            or any(not isinstance(key, str) for key in changed)):
        raise ResearchError('changed 须为至少一个已知输入或结论 ID。')
    nodes = {item['id'] for item in data['inputs'] + data['findings']}
    if set(changed) - nodes:
        raise ResearchError(f'未知变更 ID：{sorted(set(changed) - nodes)}')
    children = {key: [] for key in nodes}
    for item in data['findings']:
        for ref in item['depends_on']:
            children[ref].append(item['id'])
    paths = {key: [key] for key in dict.fromkeys(changed)}
    queue = deque(paths)
    while queue:
        key = queue.popleft()
        for child in children[key]:
            if child not in paths:
                paths[child] = paths[key] + [child]
                queue.append(child)
    affected = [item['id'] for item in data['findings'] if item['id'] in paths]
    return {
        'changed': list(dict.fromkeys(changed)), 'affected_findings': affected,
        'independent_findings': [item['id'] for item in data['findings'] if item['id'] not in paths],
        'affected_issues': [item['id'] for item in data['issues'] if set(item['affected_findings']) & set(affected)],
        'summary_needs_review': bool(set(data['summary_refs']) & set(affected)),
        'paths': {key: paths[key] for key in affected},
        'notice': '这里只沿已声明依赖定位需复核范围，不自动撤回、改写或升级判断；漏记依赖须由作者补足。',
    }


def _issue_label(item):
    return f'{item["id"]}：{item["title"]}（{ISSUE_STATUSES[item["status"]]}）'


def _source_lines(data):
    lines = ['## 材料、前提与映射', '']
    for item in data['inputs']:
        lines += [f'### {item["id"]} · {item["label"]}', '',
                  f'类型：{item["kind"]}；记录状态：{item["status"]}。', '', item['content'], '',
                  f'出处或位置：{item["locator"] or "尚未取得，保留未知"}', '']
    return lines


def render_documents(data) -> dict[str, str]:
    validation = validate_research(data)
    major = [item for item in data['issues'] if item['materiality'] == 'major' and item['status'] in ACTIVE]
    lines = ['<!-- xikari-research-report -->', '', f'# {data["title"]}', '',
             f'研究问题：{data["question"]}', '', '## 当前判断', '', data['summary'], '',
             f'综合所据结论：{", ".join(data["summary_refs"])}。', '']
    if validation['synthetic_inputs']:
        lines += ['本报告使用合成材料：' + ', '.join(validation['synthetic_inputs'])
                  + '。相应结果只用于教学或模型示意，不作现实效果证据。', '']
    if major:
        lines += ['**影响当前判断的重大未决：**', '']
        for item in major:
            lines += [f'- {_issue_label(item)}：{item["consequence"]}', '']
    lines += ['## 范围与方法', '', data['scope'], '', data['method'], '', '## 研究论证', '']
    unknown = validation['unknown_inputs']
    unknown_impacts = impact(data, unknown) if unknown else {'paths': {}}
    issue_impacts = {issue['id']: set(impact(data, issue['affected_findings'])['affected_findings'])
                     for issue in data['issues']}
    for item in data['findings']:
        lines += [f'### {item["id"]} · {item["title"]}', '',
                  f'判断身份：{KINDS[item["kind"]]}；状态：{STATUSES[item["status"]]}。', '',
                  item['body'], '', f'依据及前提：{", ".join(item["depends_on"])}。', '']
        if item['id'] in unknown_impacts['paths']:
            lines += ['**尚依赖未知输入：** ' + ' → '.join(unknown_impacts['paths'][item['id']])
                      + '。该部分仍需作者复核，未由本工具补成事实。', '']
        if item['limitations']:
            lines += ['本项限制：', ''] + [f'- {entry}' for entry in item['limitations']] + ['']
        related = [issue for issue in data['issues'] if item['id'] in issue_impacts[issue['id']]]
        for issue in related:
            lines += [f'关联问题 {_issue_label(issue)}：{issue["consequence"]}', '']
        lines += ['可能改判的条件：', ''] + [f'- {entry}' for entry in item['change_conditions']] + ['']
    lines += ['## 解释范围与问题评估', '', data['issue_assessment'], '',
              '问题的已做工作、剩余缺口和下一步见同目录的 [问题报告](research-issues.md)。', '']
    lines += _source_lines(data) + [f'> {NOTICE}', '']

    boundary = ['<!-- xikari-research-issues -->', '', f'# {data["title"]}：解释边界与问题', '',
                f'对应研究问题：{data["question"]}', '', data['issue_assessment'], '',
                '主体论证见 [研究报告](research-report.md)。', '']
    if not data['issues']:
        boundary += ['本次记录未提出具体问题项；这一结果只覆盖上述评估范围，不表示理论或研究普遍无误。', '']
    for item in data['issues']:
        boundary += [f'## {_issue_label(item)}', '',
                     '分类：' + '、'.join(CATEGORIES[key] for key in item['categories']) + '。', '',
                     f'受影响结论：{", ".join(item["affected_findings"])}；影响程度：{item["materiality"]}。', '']
        for key, label in (('current_work', '已经完成的工作'), ('why_unresolved', '仍未解决的具体原因'),
                           ('consequence', '对主报告的影响'), ('next_work', '下一项工作'),
                           ('status_reason', '当前状态依据'), ('resolution_scope', '已解决与仍未解决的范围')):
            boundary += [f'**{label}：**', '', item[key] or '未提供；不补造已完成工作。', '']
        if 'theory' in item:
            theory = item['theory']
            boundary += ['### 理论问题候选的具体命中位置', '',
                         f'原文位置：§{theory["anchor"]}', '', theory['proposition'], '',
                         f'所据原文字节 SHA-256：{theory["source_sha256"]}', '',
                         f'原命题范围与前提：{theory["scope"]}', '',
                         f'具体挑战：{theory["challenge"]}', '',
                         '这是待评估的理论问题候选；记录结构不证明原命题已被反驳。', '']
    boundary += [f'> {NOTICE}', '']
    return {'research-report.md': '\n'.join(lines), 'research-issues.md': '\n'.join(boundary)}


def publish_directory(staging: Path, output: Path):
    """Atomically publish without replacing even an empty concurrent directory.

    Windows os.rename refuses existing destinations. POSIX os.rename replaces an
    empty directory, so Linux/Darwin need their no-replace rename operation. An
    unavailable operation fails closed rather than falling back to clobbering.
    Only Python's standard library is used.
    """
    if os.name == 'nt':
        os.rename(staging, output)
        return
    libc = ctypes.CDLL(None, use_errno=True)
    source, destination = os.fsencode(staging), os.fsencode(output)
    if sys.platform.startswith('linux') and hasattr(libc, 'renameat2'):
        rename = libc.renameat2
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(-100, source, -100, destination, 1)  # AT_FDCWD, RENAME_NOREPLACE
    elif sys.platform == 'darwin' and hasattr(libc, 'renamex_np'):
        rename = libc.renamex_np
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(source, destination, 4)  # RENAME_EXCL
    else:
        raise OSError(errno.ENOTSUP, '此平台不提供安全的目录无覆盖发布；请使用支持的平台。')
    if result:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(output))


def write_documents(documents, output: Path) -> Path:
    """Publish a complete pair from a sibling staging directory under a write lock.

    Existing destinations, including empty directories and dangling symlinks, are
    refused. The cooperating tool writers share the exclusive sibling lock.
    """
    output = Path(output)
    require_external_output(output, __file__)
    if not isinstance(documents, dict) or set(documents) != {'research-report.md', 'research-issues.md'}:
        raise ResearchError('双成果必须同时包含 research-report.md 与 research-issues.md。')
    if any(not isinstance(value, str) or not value.strip() for value in documents.values()):
        raise ResearchError('双成果正文均须为非空文本。')
    if os.path.lexists(output):
        raise ResearchError(f'输出已存在，未覆盖：{output}；请指定全新目录。')
    lock = output.with_name(output.name + '.research.lock')
    require_external_output(lock, __file__)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = None
    owns_lock = False
    try:
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise ResearchError(f'输出有写入者或遗留锁：{lock}；未自动覆盖。') from exc
        owns_lock = True
        os.close(descriptor)
        if os.path.lexists(output):
            raise ResearchError('输出在取锁前已出现，未覆盖；请改用新目录。')
        staging = Path(tempfile.mkdtemp(prefix='.research-', dir=output.parent))
        for name, contents in documents.items():
            with (staging / name).open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(contents)
                stream.flush()
                os.fsync(stream.fileno())
        # Recheck after staging so a concurrent unrelated writer is not replaced.
        require_external_output(output, __file__)
        if os.path.lexists(output):
            raise ResearchError('输出在准备双成果期间已出现，未覆盖。')
        publish_directory(staging, output)
        staging = None
        return output
    finally:
        if staging is not None:
            shutil.rmtree(staging)
        if owns_lock:
            lock.unlink(missing_ok=True)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--research', required=True, type=Path, help='已经完成的作者研究内容 JSON')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('validate', help='校验结构、身份字段和依赖，不判断正文质量')
    render = commands.add_parser('render', help='同时生成主体和问题报告')
    render.add_argument('--output', type=Path, required=True, help='安装目录外的全新输出目录')
    changes = commands.add_parser('impact', help='由变更 ID 追踪受影响结论')
    changes.add_argument('--changed', action='append', required=True, help='可重复的输入或结论 ID')
    args = parser.parse_args(argv)
    try:
        data = read_research(args.research)
        if args.command == 'validate':
            result = validate_research(data)
        elif args.command == 'impact':
            result = impact(data, args.changed)
        else:
            output = write_documents(render_documents(data), args.output)
            result = {'output': str(output.resolve()), 'files': ['research-report.md', 'research-issues.md'],
                      'notice': NOTICE}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, UnicodeError, ResearchError, ValueError) as exc:
        print(f'研究成果处理失败：{exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
