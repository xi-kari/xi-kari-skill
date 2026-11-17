#!/usr/bin/env python3
"""Look up, render and trace explicitly supplied domain mappings.

This tool checks a bounded data contract, not the truth of definitions, evidence
or formal-instance claims. It never infers a fact from a matched word.
"""

from __future__ import annotations

import argparse
from collections import deque
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from xikari_paths import require_external_output
    from read_source import build_index
finally:
    sys.path.pop(0)

FORMAT = 'xikari-domain-mapping-1'
MAX_BYTES = 4 * 1024 * 1024
MAX_ROWS = 2000
MAX_OUTPUT_BYTES = 32 * 1024 * 1024
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z')
ANCHOR = re.compile(r'(?:[1-9][0-9]*|[A-D])(?:\.[0-9]+)+\Z')
KINDS = {'definition_equivalence', 'role_instantiation', 'partial_correspondence',
         'observation_interface', 'heuristic_analogy', 'unmapped', 'not_applicable', 'unknown'}
LAYERS = {'term', 'relation', 'role', 'task', 'measurement', 'method', 'exception'}
STATUSES = {'supported', 'partial', 'unknown', 'disputed', 'not_claimed', 'not_applicable'}
MATCH_POLICIES = {'normalized', 'exact'}
NOTICE = ('本工具只核对数据结构、引用与依赖；评估状态均由输入提供。'
          '词义对应、事实证据和正式实例资格互不代证，不自动判断来源可信或理论适用。')
UNKNOWN = '未知（未提供，不补默认值）'


class MappingError(ValueError):
    """Invalid or inconsistent mapping input."""


@lru_cache(maxsize=1)
def theory_reference() -> dict:
    """Identify the bundled theory text and its sections; not a theory-content review.

    The manifest's previous identity, when recorded, lets an older snapshot be
    named precisely. Any other differing hash is reported, never silently trusted.
    """
    source_dir = Path(__file__).resolve().parents[1] / 'source'
    raw = (source_dir / 'Xikari-条件结构与转化论.md').read_bytes()
    sections, _ = build_index(raw.decode('utf-8-sig').splitlines())
    previous = {}
    try:
        manifest = json.loads((source_dir / 'source-manifest.json').read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        manifest = {}
    if isinstance(manifest, dict) and isinstance(manifest.get('previous_source_sha256'), str):
        previous[manifest['previous_source_sha256']] = str(manifest.get('previous_source_identity') or '')
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'sections': frozenset(sections), 'previous': previous}


def theory_binding(value: str) -> str:
    """Classify a well-formed theory hash against the bundled text."""
    reference = theory_reference()
    if value == reference['sha256']:
        return 'current'
    return 'previous_version' if value in reference['previous'] else 'other_version'


def theory_version_warning(status: str, subject: str) -> str:
    """One plain statement shared by validation, query, tracing and rendering."""
    if status == 'previous_version':
        return (f'{subject}绑定的是上一版理论原文，与当前随包原文不同：小节引用按所据版本保留，'
                '未对当前原文复核。旧快照仍可查询、追踪与渲染；复核受影响内容后另存新版。')
    return (f'{subject}绑定的理论散列与当前随包原文不同，也不是来源清单记录的上一版：小节引用未对当前原文复核。'
            '若是更早的快照，仍可查询与追踪；若是新建记录，请核对散列。')


def _object(value, allowed, required, where):
    if not isinstance(value, dict):
        raise MappingError(f'{where}须为对象。')
    extra = set(value) - set(allowed)
    missing = set(required) - set(value)
    if extra or missing:
        raise MappingError(f'{where}未知字段={sorted(extra, key=str)!r}，缺少字段={sorted(missing, key=str)!r}。')


def _text(value, where, nullable=False):
    if nullable and value is None:
        return value
    if not isinstance(value, str) or not value.strip() or len(value) > 16000:
        raise MappingError(f'{where}须为非空文本，不超过16000字符。')
    try:
        value.encode('utf-8')
    except UnicodeEncodeError as error:
        raise MappingError(f'{where}须为有效Unicode文本，不能含孤立代理字符。') from error
    return value


def _list(value, where, nonempty=False):
    if not isinstance(value, list) or len(value) > MAX_ROWS or (nonempty and not value):
        raise MappingError(f'{where}须为{"非空" if nonempty else ""}列表，最多{MAX_ROWS}项。')
    return value


def _strings(value, where, nonempty=False):
    _list(value, where, nonempty)
    for item in value:
        _text(item, where)
    if len(value) != len(set(value)):
        raise MappingError(f'{where}含重复项。')
    return value


def _enum(value, options, where):
    if not isinstance(value, str) or value not in options:
        raise MappingError(f'{where}须为以下值之一: {", ".join(sorted(options))}。')


def _identifier(value, where):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise MappingError(f'{where}须为不超过96字符的字母数字标识（可含 . _ -）。')
    return value


def normalized_term(value):
    """Unicode/case/space normalization only; never fuzzy or semantic matching."""
    _text(value, '查询词或语境')
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


def _match_key(value, policy):
    """Preserve significant spelling for identifiers under an explicit policy."""
    _text(value, '查询词或语境')
    return value if policy == 'exact' else normalized_term(value)


def read_snapshot(path: Path) -> tuple[dict, str]:
    """Parse and identify the same single bounded byte snapshot."""
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise MappingError('领域映射超过4MiB，请按实际任务拆分。')

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise MappingError(f'JSON含重复键: {key}')
            result[key] = value
        return result

    def constant(value):
        raise MappingError(f'JSON不能含非有限数: {value}')

    try:
        mapping = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs, parse_constant=constant)
        return mapping, hashlib.sha256(raw).hexdigest()
    except (json.JSONDecodeError, RecursionError) as error:
        raise MappingError(f'无法读取映射JSON: {error}') from error


def read_mapping(path: Path) -> dict:
    """Read the mapping while preserving the original public return shape."""
    return read_snapshot(path)[0]


def _index(mapping):
    sources = {row['id']: row for row in mapping['sources']}
    entries = {row['id']: row for row in mapping['entries']}
    outputs = {row['id']: row for row in mapping['outputs']}
    return sources, entries, outputs


def _dependencies(entry):
    refs = set(entry['source_ids']) | set(entry['depends_on'])
    for assessment in entry['assessments'].values():
        refs.update(assessment['basis'])
    for field in entry.get('fields', []):
        refs.update(field['source_ids'])
    for method in entry.get('methods', []):
        refs.update(method['source_ids'])
    refs.update(entry.get('target_review', {}).get('basis', []))
    return refs


def _graph(mapping):
    sources, entries, outputs = _index(mapping)
    children = {identifier: set() for identifier in (*sources, *entries, *outputs)}
    for row in entries.values():
        for parent in _dependencies(row):
            children[parent].add(row['id'])
    for row in outputs.values():
        for parent in row['source_ids'] + row['entry_ids']:
            children[parent].add(row['id'])
    return children


def validate_mapping(mapping) -> dict:
    """Validate the explicit contract; report uncertainty without filling it."""
    required = {'schema_version', 'id', 'version', 'domain', 'task', 'scope', 'sources', 'entries', 'outputs'}
    _object(mapping, required | {'theory_sha256'}, required, '领域包')
    if type(mapping['schema_version']) is not int or mapping['schema_version'] != 1:
        raise MappingError('schema_version必须为整数1。')
    _identifier(mapping['id'], '领域包.id')
    for key in ('version', 'domain', 'task', 'scope'):
        _text(mapping[key], f'领域包.{key}')
    if 'theory_sha256' in mapping:
        value = mapping['theory_sha256']
        if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value):
            raise MappingError('theory_sha256须为小写SHA-256。')
    seen = set()
    unknown = []
    for group in ('sources', 'entries', 'outputs'):
        _list(mapping[group], group, nonempty=group == 'entries')
        for row in mapping[group]:
            if not isinstance(row, dict):
                raise MappingError(f'{group}每项须为对象。')
            identifier = _identifier(row.get('id'), f'{group}.id')
            if identifier in seen:
                raise MappingError(f'来源、映射与成果ID必须全局唯一: {identifier}')
            seen.add(identifier)
    sources, entries, outputs = _index(mapping)

    def references(value, permitted, where):
        _strings(value, where)
        for identifier in value:
            _identifier(identifier, where)
            if identifier not in permitted:
                raise MappingError(f'{where}引用不存在或类型不符: {identifier}')

    for row in sources.values():
        keys = {'id', 'title', 'locator', 'version', 'scope', 'kind'}
        _object(row, keys, keys, f"来源 {row['id']}")
        for key in keys - {'id', 'kind'}:
            _text(row[key], f"来源 {row['id']}.{key}")
        _enum(row['kind'], {'document', 'user_material', 'synthetic'}, '来源.kind')
    for row in entries.values():
        where = f"映射 {row['id']}"
        keys = {'id', 'terms', 'context', 'layer', 'local_meaning', 'mapping_kind', 'target_meaning',
                'theory_anchors', 'source_ids', 'depends_on', 'preserved', 'excluded', 'unknowns', 'assessments'}
        _object(row, keys | {'fields', 'methods', 'target_review', 'match_policy'}, keys, where)
        policy = row.get('match_policy', 'normalized')
        _enum(policy, MATCH_POLICIES, where + '.match_policy')
        terms = _strings(row['terms'], where + '.terms', nonempty=True)
        if len({_match_key(term, policy) for term in terms}) != len(terms):
            raise MappingError(f'{where}.terms含当前匹配策略下重复的词。')
        _text(row['context'], where + '.context')
        _enum(row['layer'], LAYERS, where + '.layer')
        _enum(row['mapping_kind'], KINDS, where + '.mapping_kind')
        if row['mapping_kind'] == 'unknown':
            unknown.append(f"{row['id']}.mapping_kind")
        for key in ('local_meaning', 'target_meaning'):
            _text(row[key], where + '.' + key, nullable=True)
            known_absence = (key == 'target_meaning'
                             and row['mapping_kind'] in {'unmapped', 'not_applicable'})
            if row[key] is None and not known_absence:
                unknown.append(f"{row['id']}.{key}")
        for key in ('preserved', 'excluded', 'unknowns', 'theory_anchors'):
            _strings(row[key], where + '.' + key)
        if row['unknowns']:
            unknown.append(f"{row['id']}.unknowns")
        for anchor in row['theory_anchors']:
            if not ANCHOR.fullmatch(anchor):
                raise MappingError(f'{where}.theory_anchors不是小节编号: {anchor}')
        references(row['source_ids'], sources, where + '.source_ids')
        references(row['depends_on'], entries, where + '.depends_on')
        if row['id'] in row['depends_on']:
            raise MappingError(f'{where}不能依赖自己。')
        assessments = row['assessments']
        _object(assessments, {'semantic', 'factual', 'formal'}, {'semantic', 'factual', 'formal'}, where + '.assessments')
        for name, assessment in assessments.items():
            loc = where + '.assessments.' + name
            _object(assessment, {'status', 'basis', 'scope', 'rationale'}, {'status', 'basis', 'scope', 'rationale'}, loc)
            _enum(assessment['status'], STATUSES, loc + '.status')
            references(assessment['basis'], sources, loc + '.basis')
            _text(assessment['scope'], loc + '.scope')
            _text(assessment['rationale'], loc + '.rationale')
            if assessment['status'] in {'supported', 'partial', 'disputed'} and not assessment['basis']:
                raise MappingError(f'{loc}的当前状态必须指出来源basis；工具不核实来源支持程度。')
            if assessment['status'] in {'unknown', 'disputed'}:
                unknown.append(f"{row['id']}.assessments.{name}")
        if row['mapping_kind'] in {'unmapped', 'not_applicable'} and row['target_meaning'] is not None:
            raise MappingError(f'{where}不对应/不适用时target_meaning必须为null，理由写在excluded。')
        if row['mapping_kind'] not in {'unmapped', 'not_applicable', 'unknown'}:
            if row['local_meaning'] is None or row['target_meaning'] is None:
                raise MappingError(f'{where}声明对应时必须填写两端含义；尚未确定请用unknown。')
            if not row['source_ids']:
                raise MappingError(f'{where}声明对应时必须给出source_ids。')
        if row['mapping_kind'] == 'definition_equivalence' and assessments['semantic']['status'] != 'supported':
            raise MappingError(f'{where}定义对应需要有basis的语义支持声明；尚未支持请用unknown或部分对应。')
        if row['mapping_kind'] in {'unknown', 'unmapped', 'not_applicable'} and not (row['unknowns'] or row['excluded']):
            raise MappingError(f'{where}须说明未知、不对应或不适用的具体原因。')
        _list(row.get('fields', []), where + '.fields')
        names = set()
        for field in row.get('fields', []):
            field_keys = {'name', 'unit', 'denominator', 'time_window', 'missing_policy', 'source_ids'}
            _object(field, field_keys, field_keys, where + '.fields')
            _text(field['name'], where + '.fields.name')
            if field['name'] in names:
                raise MappingError(f'{where}字段名重复: {field["name"]}')
            names.add(field['name'])
            for key in ('unit', 'denominator', 'time_window'):
                _text(field[key], where + '.fields.' + key, nullable=True)
                if field[key] is None:
                    unknown.append(f"{row['id']}.fields.{field['name']}.{key}")
            _text(field['missing_policy'], where + '.fields.missing_policy')
            references(field['source_ids'], sources, where + '.fields.source_ids')
        _list(row.get('methods', []), where + '.methods')
        for method in row.get('methods', []):
            method_keys = {'name', 'status', 'scope', 'source_ids'}
            _object(method, method_keys, method_keys, where + '.methods')
            for key in ('name', 'scope'):
                _text(method[key], where + '.methods.' + key)
            _enum(method['status'], {'planned', 'performed', 'unavailable'}, where + '.methods.status')
            references(method['source_ids'], sources, where + '.methods.source_ids')
            if method['status'] == 'performed' and not method['source_ids']:
                raise MappingError(f'{where}已执行的方法必须指向记录来源。')
        if 'target_review' in row:
            review = row['target_review']
            review_keys = {'requested', 'status', 'basis', 'rationale'}
            _object(review, review_keys, review_keys, where + '.target_review')
            if type(review['requested']) is not bool:
                raise MappingError(f'{where}.target_review.requested须为布尔值。')
            _enum(review['status'], {'not_requested', 'pending', 'reviewed', 'not_applicable'}, where + '.target_review.status')
            references(review['basis'], sources, where + '.target_review.basis')
            _text(review['rationale'], where + '.target_review.rationale')
            if review['requested'] != (review['status'] in {'pending', 'reviewed'}):
                raise MappingError(f'{where}目标侧复核的申请状态与处理状态不一致。')
            if review['status'] == 'reviewed' and not review['basis']:
                raise MappingError(f'{where}目标侧已复核必须有记录来源。')
            if review['status'] == 'pending':
                unknown.append(f"{row['id']}.target_review")
    for row in outputs.values():
        keys = {'id', 'title', 'text', 'entry_ids', 'source_ids'}
        _object(row, keys, keys, f"成果 {row['id']}")
        for key in ('title', 'text'):
            _text(row[key], f"成果 {row['id']}.{key}")
        references(row['entry_ids'], entries, '成果.entry_ids')
        references(row['source_ids'], sources, '成果.source_ids')
        if not row['entry_ids'] and not row['source_ids']:
            raise MappingError(f"成果 {row['id']}须指出entry_ids或source_ids以便追踪依赖。")
    uses_theory = any(row['theory_anchors'] for row in entries.values())
    if uses_theory and 'theory_sha256' not in mapping:
        raise MappingError('使用理论小节的领域包须提供theory_sha256，不能省略理论版本。')
    theory_status, warnings = 'not_bound', []
    if 'theory_sha256' in mapping:
        theory_status = theory_binding(mapping['theory_sha256'])
        if theory_status == 'current':
            sections = theory_reference()['sections']
            for row in entries.values():
                for anchor in row['theory_anchors']:
                    if anchor not in sections:
                        raise MappingError(f"映射 {row['id']}引用了当前理论不存在的小节: {anchor}")
        else:
            # An older snapshot stays readable so its dependents can be traced;
            # its section IDs belong to the bound text and are not rechecked here.
            warnings.append(theory_version_warning(theory_status, '领域包'))
    graph = _graph(mapping)
    incoming = {identifier: 0 for identifier in graph}
    for children in graph.values():
        for child in children:
            incoming[child] += 1
    queue = deque(identifier for identifier, count in incoming.items() if not count)
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for child in graph[node]:
            incoming[child] -= 1
            if not incoming[child]:
                queue.append(child)
    if visited != len(graph):
        raise MappingError('映射依赖含循环，不能把相互引用作为独立依据；请拆成共同来源。')
    return {'format': FORMAT, 'valid': True, 'id': mapping['id'], 'version': mapping['version'],
            'source_count': len(sources), 'entry_count': len(entries), 'output_count': len(outputs),
            'theory_status': theory_status, 'warnings': warnings,
            'unresolved_fields': sorted(unknown), 'notice': NOTICE}


def lookup(mapping, term: str, context: str | None = None) -> dict:
    report = validate_mapping(mapping)
    needles = {policy: _match_key(term, policy) for policy in MATCH_POLICIES}
    contexts = ({policy: _match_key(context, policy) for policy in MATCH_POLICIES}
                if context is not None else None)
    term_matches = [row for row in mapping['entries']
               if needles[row.get('match_policy', 'normalized')]
               in {_match_key(value, row.get('match_policy', 'normalized')) for value in row['terms']}]
    matches = [row for row in term_matches
               if (contexts is None or contexts[row.get('match_policy', 'normalized')]
                    == _match_key(row['context'], row.get('match_policy', 'normalized')))]
    status = ('matched' if len(matches) == 1 else 'ambiguous' if matches
              else 'context_not_found' if term_matches and context is not None else 'unmapped')
    return {'format': FORMAT, 'term': term, 'context': context,
            'status': status,
            'ambiguous': len(matches) > 1, 'matches': matches,
            'context_options': list(dict.fromkeys(row['context'] for row in term_matches)),
            'theory_status': report['theory_status'], 'warnings': report['warnings'],
            'notice': NOTICE + ' 查询按各条目的match_policy匹配词和语境；默认normalized，exact保留全部字符。所有匹配均保留，不猜测语境。'}


def impact(mapping, changed: list[str]) -> dict:
    report = validate_mapping(mapping)
    _strings(changed, 'changed', nonempty=True)
    sources, entries, outputs = _index(mapping)
    permitted = set(sources) | set(entries)
    for identifier in changed:
        if identifier not in permitted:
            raise MappingError(f'变更ID不存在或不是来源/映射: {identifier}')
    graph = _graph(mapping)
    paths = {identifier: [identifier] for identifier in sorted(changed)}
    queue = deque(sorted(changed))
    while queue:
        node = queue.popleft()
        for child in sorted(graph[node]):
            if child not in paths:
                paths[child] = paths[node] + [child]
                queue.append(child)
    return {'format': FORMAT, 'changed': sorted(changed),
            'affected_entries': sorted(set(paths) & set(entries)),
            'affected_outputs': sorted(set(paths) & set(outputs)),
            'unaffected_outputs': sorted(set(outputs) - set(paths)),
            'paths': {identifier: paths[identifier] for identifier in sorted(paths)},
            'theory_status': report['theory_status'], 'warnings': report['warnings'],
            'notice': '这是已登记依赖的复核范围，不断言结论已经错误；未登记的依赖无法自动发现。不会改写原始材料或成果。'}


def _md(value):
    if value is None:
        return UNKNOWN
    return re.sub(r'([\\`*_{}\[\]<>#+!|])', r'\\\1', str(value))


def _bounded_join(parts, separator=''):
    """Check UTF-8 output size before publishing any part of the result."""
    chunks = []
    size = 0
    separator_bytes = len(separator.encode('utf-8'))
    for part in parts:
        size += len(part.encode('utf-8')) + (separator_bytes if chunks else 0)
        if size > MAX_OUTPUT_BYTES:
            raise MappingError(f'输出超过{MAX_OUTPUT_BYTES}字节，请按实际任务拆分；未写出部分结果。')
        chunks.append(part)
    return separator.join(chunks)


def _json_output(value):
    encoder = json.JSONEncoder(ensure_ascii=False, indent=2, allow_nan=False)
    return _bounded_join(encoder.iterencode(value))


def render_markdown(mapping) -> str:
    report = validate_mapping(mapping)
    lines = ['<!-- xikari-domain-mapping -->', '', '# 领域映射与使用说明', '',
             f"领域：{_md(mapping['domain'])}；版本：{_md(mapping['version'])}。", '',
             f"任务：{_md(mapping['task'])}", '', f"适用范围：{_md(mapping['scope'])}", '',
             NOTICE, '', '## 已写成的领域表述', '']
    if 'theory_sha256' in mapping:
        lines[8:8] = [f"理论文本 SHA-256：{mapping['theory_sha256']}。", '']
        if report['theory_status'] != 'current':
            lines[10:10] = [f"**理论版本提示：** {_md(report['warnings'][0])}", '']
    if not mapping['outputs']:
        lines += ['尚未提供成文；工具不会据词表编造研究结果。', '']
    for row in mapping['outputs']:
        lines += [f"### {_md(row['title'])}（{_md(row['id'])}）", '', _md(row['text']), '',
                  f"依赖映射：{_md(', '.join(row['entry_ids']) or '无')}；直接来源：{_md(', '.join(row['source_ids']) or '无')}。", '']
    lines += ['## 来源范围', '']
    if not mapping['sources']:
        lines += ['尚未提供来源。', '']
    for row in mapping['sources']:
        lines += [f"- {_md(row['id'])}：{_md(row['title'])}（{_md(row['kind'])}）；"
                  f"位置：{_md(row['locator'])}；版本：{_md(row['version'])}；范围：{_md(row['scope'])}"]
    lines += ['', '## 对应、区别与证据', '']
    for row in mapping['entries']:
        if row['mapping_kind'] == 'unmapped':
            target_description = '无对应（保留领域原词，理由见下文）'
        elif row['mapping_kind'] == 'not_applicable':
            target_description = '不适用（具体原因见下文）'
        else:
            target_description = _md(row['target_meaning'])
        lines += [f"### {_md(' / '.join(row['terms']))}（{_md(row['id'])}）", '',
                  f"语境：{_md(row['context'])}；层次：{_md(row['layer'])}；对应类型：{_md(row['mapping_kind'])}。", '',
                  f"词与语境匹配策略：{row.get('match_policy', 'normalized')}。", '',
                  f"当地含义：{_md(row['local_meaning'])}", '', f"目标含义：{target_description}", '',
                  f"来源：{_md(', '.join(row['source_ids']) or '未提供')}；理论小节：{_md(', '.join(row['theory_anchors']) or '未使用')}；"
                  f"依赖映射：{_md(', '.join(row['depends_on']) or '无已登记依赖')}。", '']
        for key, title in (('preserved', '保留的区别'), ('excluded', '不能推出与不对应'), ('unknowns', '未决事项')):
            lines += [f"**{title}：**", '']
            lines += [f'- {_md(item)}' for item in row[key]] or ['- 未登记；不表示该类问题不存在。']
            lines.append('')
        for name, label in (('semantic', '语义对应'), ('factual', '事实与机制证据'), ('formal', '正式实例资格')):
            assessment = row['assessments'][name]
            lines += [f"**{label}：{_md(assessment['status'])}**。{_md(assessment['rationale'])}", '',
                      f"范围：{_md(assessment['scope'])}；依据：{_md(', '.join(assessment['basis']) or '未提供')}。", '']
        for field in row.get('fields', []):
            lines += [f"字段 {_md(field['name'])}：单位={_md(field['unit'])}；分母={_md(field['denominator'])}；"
                      f"时间窗={_md(field['time_window'])}。{_md(field['missing_policy'])} "
                      f"来源：{_md(', '.join(field['source_ids']) or '未提供')}。", '']
        for method in row.get('methods', []):
            lines += [f"方法 {_md(method['name'])}（{_md(method['status'])}）：{_md(method['scope'])}；"
                      f"来源：{_md(', '.join(method['source_ids']) or '未提供')}。", '']
        if 'target_review' in row:
            review = row['target_review']
            lines += [f"目标侧独立复核：{_md(review['status'])}；{_md(review['rationale'])}；"
                      f"记录：{_md(', '.join(review['basis']) or '未提供')}。", '']
    if report['unresolved_fields']:
        lines += ['## 保留的未知或争议位置', '']
        lines += [f'- {_md(item)}' for item in report['unresolved_fields']]
        lines.append('')
    return _bounded_join(lines, '\n')


def write_document(text: str, output: Path) -> Path:
    """Publish a complete file without clobbering an existing path, even in a race."""
    if len(text.encode('utf-8')) > MAX_OUTPUT_BYTES:
        raise MappingError(f'输出超过{MAX_OUTPUT_BYTES}字节，请按实际任务拆分；未写出部分结果。')
    output = Path(output)
    require_external_output(output, __file__)
    if os.path.lexists(output):
        raise MappingError(f'输出已存在，请使用新路径: {output}')
    lock = output.with_name(output.name + '.lock')
    require_external_output(lock, __file__)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    owns_lock = False
    try:
        try:
            descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as error:
            raise MappingError(f'输出存在写锁，未覆盖: {lock}') from error
        owns_lock = True
        os.close(descriptor)
        require_external_output(output, __file__)
        descriptor, name = tempfile.mkstemp(prefix='.domain-mapping-', suffix='.tmp', dir=output.parent)
        temporary = Path(name)
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, output)
        except FileExistsError as error:
            raise MappingError(f'输出已由其他写入者创建，未覆盖: {output}') from error
        return output
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if owns_lock:
            lock.unlink(missing_ok=True)


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mapping', type=Path, required=True, help='有版本和来源的领域映射JSON')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('validate', help='核对结构、引用、循环及未知；不核实事实')
    query = commands.add_parser('lookup', help='精确词义查询，多义保留全部结果')
    query.add_argument('--term', required=True)
    query.add_argument('--context', help='可选：已登记语境的精确文本')
    changes = commands.add_parser('impact', help='追踪来源或映射变更后的已登记依赖')
    changes.add_argument('--changed', nargs='+', required=True)
    render = commands.add_parser('render', help='把已提供的映射和成文渲染为说明')
    render.add_argument('--output', '-o', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        mapping, snapshot_sha256 = read_snapshot(args.mapping)
        if args.command == 'validate':
            result = validate_mapping(mapping)
            result['snapshot_sha256'] = snapshot_sha256
        elif args.command == 'lookup':
            result = lookup(mapping, args.term, args.context)
        elif args.command == 'impact':
            result = impact(mapping, args.changed)
        else:
            if args.output.resolve() == args.mapping.resolve():
                raise MappingError('输出不能覆盖输入映射，请使用新路径。')
            target = write_document(render_markdown(mapping), args.output)
            result = {'output': str(target.resolve()), 'notice': NOTICE}
        print(_json_output(result))
        return 0
    except (OSError, UnicodeError, MappingError, ValueError) as error:
        print(f'领域映射处理失败：{error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
