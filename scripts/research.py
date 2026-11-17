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
    import domain_mapping
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
MAX_RENDER_BYTES = 32 * 1024 * 1024

LABELS = {
    'zh': {
        'kinds': KINDS, 'statuses': STATUSES, 'categories': CATEGORIES, 'issue_statuses': ISSUE_STATUSES,
        'input_kinds': {'source': '来源', 'premise': '前提', 'mapping': '映射'},
        'input_statuses': {'known': '已取得或已明确', 'unknown': '未知，尚未取得', 'synthetic': '合成材料'},
        'materiality': {'major': '重大', 'minor': '次要'},
        'notice': NOTICE, 'ref': '{label}（{id}）', 'sep': '；', 'cat_sep': '、',
        'question': '研究问题：{}', 'current': '## 当前判断', 'summary_refs': '综合所据结论：{}。',
        'stopped_head': '**综合判断引用了已撤回或已被反驳的结论，须复核其用法：**',
        'stopped_item': '- {path}（起点状态：{status}）。',
        'stopped_tail': '该提示不自动撤回下游判断：记录反驳结果与继续把旧结论当作成立前提须由作者区分。路径仅示例，不穷举所有依赖。',
        'synthetic': '本报告使用合成材料：{}。相应结果只用于教学或模型示意，不作现实效果证据。',
        'theory_report': '**理论版本提示：** 理论问题候选 {} 所据原文与当前随包原文不是同一版本，相关命题尚未对当前原文复核。',
        'major': '**影响当前判断的重大未决：**', 'major_item': '- {label}：{consequence}',
        'scope': '## 范围与方法', 'argument': '## 研究论证',
        'identity': '判断身份：{kind}；状态：{status}。', 'depends': '依据及前提：{}。',
        'unknown_dep': '**尚依赖未知输入：** {path}。该部分仍需作者复核，未由本工具补成事实。',
        'stopped_dep': ('**依赖状态复核：** {path}（起点状态：{status}）。'
                        '请区分记录反驳结果与继续使用旧前提；不自动判定本项失效。'),
        'limits': '本项限制：', 'related': '关联问题 {label}：{consequence}', 'successors': '后继问题：{}。',
        'change': '可能改判的条件：', 'assessment': '## 解释范围与问题评估',
        'see_issues': '问题的已做工作、剩余缺口和下一步见同目录的 [问题报告](research-issues.md)。',
        'sources': '## 材料、前提与映射',
        'bound_note': '下列快照仅展示作者绑定；用 impact-mapping 显式提供所据快照后核验依赖，不证明语义正确。',
        'input_identity': '类型：{kind}；记录状态：{status}。', 'locator': '出处或位置：{}',
        'no_locator': '尚未取得，保留未知',
        'snapshot': '映射快照：{id} / {version}；字节 SHA-256：{sha}；引用节点：{nodes}。',
        'manual_mapping': '本项为人工映射说明，未绑定可自动追踪的领域包快照；来源更正须人工回查下游。',
        'issues_title': '# {} · 解释边界与问题', 'issues_question': '对应研究问题：{}',
        'see_report': '主体论证见 [研究报告](research-report.md)。',
        'no_issues': '本次记录未提出具体问题项；这一结果只覆盖上述评估范围，不表示理论或研究普遍无误。',
        'categories_line': '分类：{}。', 'affected_line': '受影响结论：{findings}；影响程度：{materiality}。',
        'successors_issue': '后继问题：{}。替代不表示原缺口已经解决。',
        'fields': (('current_work', '已经完成的工作'), ('why_unresolved', '仍未解决的具体原因'),
                   ('consequence', '对主报告的影响'), ('next_work', '下一项工作'),
                   ('status_reason', '当前状态依据'), ('resolution_scope', '已解决与仍未解决的范围')),
        'theory_head': '### 理论问题候选的具体命中位置', 'theory_anchor': '原文位置：§{}',
        'theory_sha': '所据原文字节 SHA-256：{}', 'theory_notice': '**理论版本提示：** {}',
        'theory_subject': '本候选', 'theory_scope': '原命题范围与前提：{}', 'theory_challenge': '具体挑战：{}',
        'theory_tail': '这是待评估的理论问题候选；记录结构不证明原命题已被反驳。',
        'issue_label': '{id}：{title}（{status}）',
    },
    'en': {
        'kinds': {'descriptive': 'descriptive judgment', 'causal': 'causal judgment',
                  'interpretive': 'interpretive judgment', 'normative': 'normative judgment',
                  'model_result': 'result within a model', 'candidate': 'candidate', 'unknown': 'unknown',
                  'conditional_projection': 'conditional projection'},
        'statuses': {'supported': 'supported within the stated scope', 'proposed': 'proposed for examination',
                     'contested': 'contested', 'unknown': 'unknown', 'refuted': 'refuted', 'withdrawn': 'withdrawn'},
        'categories': {'material_gap': 'insufficient material',
                       'identification_limit': 'limits of method and identification',
                       'domain_method': 'domain knowledge or method needed',
                       'mapping_gap': 'gap in mapping or concepts', 'theory_candidate': 'candidate theory problem',
                       'normative_disagreement': 'normative disagreement',
                       'implementation_gap': 'gap in the skill or the product'},
        'issue_statuses': {'open': 'open', 'under_investigation': 'under investigation',
                           'partially_resolved': 'partly resolved', 'resolved_within_scope': 'resolved within a stated scope',
                           'withdrawn': 'withdrawn', 'superseded': 'superseded by later issues'},
        'input_kinds': {'source': 'source', 'premise': 'premise', 'mapping': 'mapping'},
        'input_statuses': {'known': 'obtained or stated', 'unknown': 'unknown, not yet obtained',
                           'synthetic': 'synthetic material'},
        'materiality': {'major': 'major', 'minor': 'minor'},
        'notice': ('This tool checks only the record structure, references and dependencies and typesets the '
                   "author's text. It does not show that sources are true, that the argument suffices, that the "
                   'research is complete or that any real-world effect has occurred.'),
        'ref': '{label} ({id})', 'sep': '; ', 'cat_sep': '; ',
        'question': 'Research question: {}', 'current': '## Current judgment', 'summary_refs': 'Findings the judgment rests on: {}.',
        'stopped_head': '**The overall judgment cites findings that have been withdrawn or refuted; review how they are used:**',
        'stopped_item': '- {path} (status at the start: {status}).',
        'stopped_tail': ('This notice does not withdraw any downstream judgment. The author must distinguish recording a '
                         'refutation from still treating the old finding as a premise. The path is an example, not '
                         'every dependency.'),
        'synthetic': 'This report uses synthetic material: {}. The results serve teaching or illustrating a model and are not evidence of real-world effects.',
        'theory_report': ('**Theory version notice:** candidate theory problem {} rests on a source text that differs from '
                          'the bundled text; the proposition has not been rechecked against the current text.'),
        'major': '**Major open issues affecting the current judgment:**', 'major_item': '- {label}: {consequence}',
        'scope': '## Scope and method', 'argument': '## Research argument',
        'identity': 'Kind of judgment: {kind}; status: {status}.', 'depends': 'Rests on: {}.',
        'unknown_dep': ('**Still depends on unknown input:** {path}. This part still needs the author\'s review; '
                        'the tool has not filled it in as fact.'),
        'stopped_dep': ('**Dependency status to review:** {path} (status at the start: {status}). Distinguish recording '
                        'a refutation from still using the old premise; this finding is not judged void automatically.'),
        'limits': 'Limits of this finding:', 'related': 'Related issue {label}: {consequence}',
        'successors': 'Succeeded by: {}.', 'change': 'What would change this judgment:',
        'assessment': '## Scope of explanation and assessment of issues',
        'see_issues': 'Work done, remaining gaps and next steps for each issue are in the [issues report](research-issues.md) in the same folder.',
        'sources': '## Materials, premises and mappings',
        'bound_note': ('The snapshots below only show the author\'s bindings; supply the bound snapshot to impact-mapping '
                       'to check dependencies. A binding does not show that the mapping is right.'),
        'input_identity': 'Kind: {kind}; record status: {status}.', 'locator': 'Source or location: {}',
        'no_locator': 'not yet obtained; kept as unknown',
        'snapshot': 'Mapping snapshot: {id} / {version}; byte SHA-256: {sha}; nodes cited: {nodes}.',
        'manual_mapping': ('This is a manual mapping note with no traceable domain-pack snapshot; after a source '
                           'correction, check its dependents by hand.'),
        'issues_title': '# {} · Limits of explanation and issues', 'issues_question': 'Research question: {}',
        'see_report': 'The main argument is in the [research report](research-report.md).',
        'no_issues': ('No specific issue was raised in this record. That covers only the assessment scope above; '
                      'it does not mean the theory or the research is free of problems.'),
        'categories_line': 'Categories: {}.', 'affected_line': 'Findings affected: {findings}; materiality: {materiality}.',
        'successors_issue': 'Succeeded by: {}. Being superseded does not mean the original gap is resolved.',
        'fields': (('current_work', 'Work already done'), ('why_unresolved', 'Why it is still unresolved'),
                   ('consequence', 'Consequence for the main report'), ('next_work', 'Next piece of work'),
                   ('status_reason', 'Basis for the current status'), ('resolution_scope', 'What is and is not resolved')),
        'theory_head': '### Where the candidate theory problem bears', 'theory_anchor': 'Source location: §{}',
        'theory_sha': 'Byte SHA-256 of the source text relied on: {}', 'theory_notice': '**Theory version notice:** {}',
        'theory_subject': 'This candidate', 'theory_scope': 'Scope and premises of the proposition: {}',
        'theory_challenge': 'Specific challenge: {}',
        'theory_tail': 'This is a candidate theory problem awaiting assessment; the record does not show that the proposition has been refuted.',
        'issue_label': '{id}: {title} ({status})',
    },
}


class ResearchError(ValueError):
    """An invalid or unsafe research operation."""


@lru_cache(maxsize=1)
def theory_index():
    """Locate bundled section IDs and source version; not a theory-content review."""
    reference = domain_mapping.theory_reference()
    return {'anchors': reference['sections'], 'sha256': reference['sha256'],
            'previous': reference['previous']}


def read_snapshot(path: Path) -> tuple[dict, str]:
    """Read once so the parsed record and its byte identity cannot diverge."""
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
        data = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique,
                          parse_constant=nonfinite)
        return data, hashlib.sha256(raw).hexdigest()
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ResearchError(f'无效研究 JSON：{exc}') from exc


def read_research(path: Path) -> dict:
    return read_snapshot(path)[0]


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
            or any(not isinstance(v, str) or not v.strip() or '\x00' in v or len(v) > 100000 for v in value)
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
        object_fields(item, {'id', 'kind', 'label', 'content', 'locator', 'status'}, {'mapping_ref'}, '输入')
        identifier(item, '输入')
        choice(item, 'kind', {'source', 'premise', 'mapping'}, item['id'])
        choice(item, 'status', {'known', 'unknown', 'synthetic'}, item['id'])
        for key in ('label', 'content'):
            text(item, key, item['id'])
        text(item, 'locator', item['id'], required=item['kind'] == 'source' and item['status'] != 'unknown')
        if 'mapping_ref' in item:
            if item['kind'] != 'mapping':
                raise ResearchError('只有 mapping 输入可声明 mapping_ref。')
            ref = item['mapping_ref']
            object_fields(ref, {'id', 'version', 'sha256', 'node_ids'}, set(), item['id'] + '.mapping_ref')
            for key in ('id', 'version', 'sha256'):
                text(ref, key, item['id'] + '.mapping_ref')
            if not ID.fullmatch(ref['id']) or not re.fullmatch(r'[0-9a-f]{64}', ref['sha256']):
                raise ResearchError('mapping_ref 须提供有效包 ID 和小写字节 SHA-256。')
            text_list(ref, 'node_ids', item['id'] + '.mapping_ref', required=True)
            if any(not ID.fullmatch(key) for key in ref['node_ids']):
                raise ResearchError('mapping_ref.node_ids 须为映射来源、条目或成果的 ID。')
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
    older_theory = []
    for item in issues:
        object_fields(item, {'id', 'title', 'categories', 'affected_findings', 'materiality',
                             'status', 'current_work', 'why_unresolved', 'consequence', 'next_work',
                             'status_reason', 'resolution_scope'}, {'theory', 'superseded_by'}, '问题')
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
        if item['status'] == 'superseded':
            if 'superseded_by' not in item:
                raise ResearchError(f'{item["id"]} 被替代问题须用 superseded_by 引用后继问题。')
            text_list(item, 'superseded_by', item['id'], required=True)
        elif 'superseded_by' in item:
            raise ResearchError(f'{item["id"]} 只有 superseded 状态可声明 superseded_by。')
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
            if not re.fullmatch(r'[0-9a-f]{64}', theory['source_sha256']):
                raise ResearchError('theory.source_sha256 须为所据原文字节的小写 SHA-256。')
            binding = domain_mapping.theory_binding(theory['source_sha256'])
            if binding == 'current':
                if theory['anchor'] not in theory_index()['anchors']:
                    raise ResearchError(f'theory.anchor 不存在于随包原文：{theory["anchor"]}')
            else:
                # Kept readable after a theory update; the anchor belongs to the
                # bound text, and both reports carry the version notice.
                older_theory.append({'issue': item['id'], 'source_sha256': theory['source_sha256'],
                                     'binding': binding})
    issue_ids = {item['id'] for item in issues}
    successor_graph = {}
    for item in issues:
        successors = item.get('superseded_by', [])
        if set(successors) - issue_ids:
            raise ResearchError(f'{item["id"]} superseded_by 须引用已有问题 ID。')
        successor_graph[item['id']] = successors
    try:
        topological_order(successor_graph, set())
    except ResearchError as exc:
        raise ResearchError('问题替代关系存在循环；请保留可追踪的后继问题。') from exc
    warnings = [domain_mapping.theory_version_warning(row['binding'], f'理论问题候选 {row["issue"]} ')
                for row in older_theory]
    return {
        'format': FORMAT, 'structure_valid': True,
        'input_count': len(inputs), 'finding_count': len(findings), 'issue_count': len(issues),
        'unknown_inputs': [item['id'] for item in inputs if item['status'] == 'unknown'],
        'synthetic_inputs': [item['id'] for item in inputs if item['status'] == 'synthetic'],
        'unverified_mapping_inputs': [item['id'] for item in inputs if item['kind'] == 'mapping'],
        'theory_bindings_not_current': older_theory, 'warnings': warnings,
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


def dependency_children(data):
    """Build one reverse index after validation."""
    nodes = {item['id'] for item in data['inputs'] + data['findings']}
    children = {key: [] for key in nodes}
    for item in data['findings']:
        for ref in item['depends_on']:
            children[ref].append(item['id'])
    return children


def dependency_paths(children, changed):
    """One shortest declared path per reachable node, not all supporting paths."""
    paths = {key: [key] for key in dict.fromkeys(changed)}
    queue = deque(paths)
    while queue:
        key = queue.popleft()
        for child in children[key]:
            if child not in paths:
                paths[child] = paths[key] + [child]
                queue.append(child)
    return paths


def impact(data, changed) -> dict:
    """Find dependent findings; changes request review, never automatic rejection."""
    validation = validate_research(data)
    if (not isinstance(changed, (list, tuple)) or not changed
            or any(not isinstance(key, str) for key in changed)):
        raise ResearchError('changed 须为至少一个已知输入或结论 ID。')
    children = dependency_children(data)
    if set(changed) - set(children):
        raise ResearchError(f'未知变更 ID：{sorted(set(changed) - set(children))}')
    paths = dependency_paths(children, changed)
    affected = [item['id'] for item in data['findings'] if item['id'] in paths]
    return {
        'changed': list(dict.fromkeys(changed)), 'affected_findings': affected,
        'independent_findings': [item['id'] for item in data['findings'] if item['id'] not in paths],
        'affected_issues': [item['id'] for item in data['issues'] if set(item['affected_findings']) & set(affected)],
        'summary_needs_review': bool(set(data['summary_refs']) & set(affected)),
        'paths': {key: paths[key] for key in affected},
        'warnings': validation['warnings'],
        'notice': '这里只沿已声明依赖定位需复核范围，不自动撤回、改写或升级判断；漏记依赖须由作者补足。',
    }


def impact_mapping(data, mapping_path: Path, changed) -> dict:
    """Bridge one explicitly supplied, frozen mapping snapshot to research.

    A locator is never opened implicitly. Unbound or other-snapshot inputs stay
    outside this check; their downstream findings are not called independent.
    """
    validation = validate_research(data)
    mapping, digest = read_snapshot(mapping_path)
    mapping_result = domain_mapping.impact(mapping, changed)
    nodes = {row['id'] for group in ('sources', 'entries', 'outputs') for row in mapping[group]}
    verified = []
    unchecked = []
    affected_inputs = []
    matched_nodes = {}
    for item in data['inputs']:
        if item['kind'] != 'mapping':
            continue
        ref = item.get('mapping_ref')
        if not ref or (ref['id'], ref['version']) != (mapping['id'], mapping['version']):
            unchecked.append(item['id'])
            continue
        if ref['sha256'] != digest:
            raise ResearchError(f'{item["id"]} 绑定的映射字节 SHA-256 不匹配；请提供所据旧快照，不要用新版替代。')
        absent = set(ref['node_ids']) - nodes
        if absent:
            raise ResearchError(f'{item["id"]} 引用映射快照中不存在的节点：{sorted(absent)}')
        verified.append(item['id'])
        affected_nodes = sorted(set(ref['node_ids']) & set(mapping_result['paths']))
        if affected_nodes:
            affected_inputs.append(item['id'])
            matched_nodes[item['id']] = affected_nodes
    if not verified:
        raise ResearchError('没有与该包 ID、版本和字节摘要匹配的 mapping_ref；不能把未核验解释为空影响。')
    children = dependency_children(data)
    paths = dependency_paths(children, affected_inputs)
    unchecked_paths = dependency_paths(children, unchecked)
    affected = [item['id'] for item in data['findings'] if item['id'] in paths]
    unassessed = [item['id'] for item in data['findings']
                  if item['id'] in unchecked_paths and item['id'] not in paths]
    affected_set = set(affected)
    unassessed_set = set(unassessed)
    return {
        'mapping_snapshot': {'id': mapping['id'], 'version': mapping['version'], 'sha256': digest},
        'changed_mapping_nodes': mapping_result['changed'],
        'verified_mapping_inputs': verified, 'affected_mapping_inputs': affected_inputs,
        'unverified_mapping_inputs': unchecked, 'matched_mapping_nodes': matched_nodes,
        'affected_findings': affected, 'unassessed_findings': unassessed,
        'independent_findings': [item['id'] for item in data['findings']
                                 if item['id'] not in affected_set | unassessed_set],
        'affected_issues': [item['id'] for item in data['issues']
                            if set(item['affected_findings']) & affected_set],
        'unassessed_issues': [item['id'] for item in data['issues']
                              if set(item['affected_findings']) & unassessed_set],
        'summary_needs_review': bool(set(data['summary_refs']) & affected_set),
        'summary_has_unassessed_dependencies': bool(set(data['summary_refs']) & set(unchecked_paths)),
        'paths': {key: paths[key] for key in affected},
        'mapping_paths': mapping_result['paths'],
        'mapping_theory_status': mapping_result['theory_status'],
        'warnings': validation['warnings'] + mapping_result['warnings'],
        'notice': '只对显式给定的已绑定映射快照和已声明依赖定位复核；未绑定或其他快照的映射列为未核验，其下游不宣称独立。作者仍须读新材料、修订正文及问题，并更新绑定；字节匹配不证明映射正确。',
    }


def _source_lines(data, text):
    lines = [text['sources'], '']
    if any('mapping_ref' in item for item in data['inputs']):
        lines += [text['bound_note'], '']
    for item in data['inputs']:
        lines += [f'### {item["id"]} · {item["label"]}', '',
                  text['input_identity'].format(kind=text['input_kinds'][item['kind']],
                                                status=text['input_statuses'][item['status']]), '',
                  item['content'], '', text['locator'].format(item['locator'] or text['no_locator']), '']
        if item['kind'] == 'mapping':
            if 'mapping_ref' in item:
                ref = item['mapping_ref']
                lines += [text['snapshot'].format(id=ref['id'], version=ref['version'], sha=ref['sha256'],
                                                  nodes=', '.join(ref['node_ids'])), '']
            else:
                lines += [text['manual_mapping'], '']
    return lines


class _DocumentLines(list):
    """Bound the complete rendered pair before retaining an amplified report."""

    def __init__(self, values, budget):
        super().__init__()
        self.budget = budget
        self += values

    def __iadd__(self, values):
        for value in values:
            self.budget[0] += len(value.encode('utf-8')) + 1
            if self.budget[0] > MAX_RENDER_BYTES:
                raise ResearchError('双成果渲染超过 32 MiB；请按实际专题拆分，保留相关依赖与限制。')
            self.append(value)
        return self


def render_documents(data, lang: str = 'zh') -> dict[str, str]:
    """Typeset the authored pair; lang selects fixed labels, never translates the author's text."""
    if lang not in LABELS:
        raise ResearchError(f'不支持的语言：{lang}；可用 zh 或 en。')
    text = LABELS[lang]
    validation = validate_research(data)
    children = dependency_children(data)
    unknown_paths = dependency_paths(children, validation['unknown_inputs'])
    stopped = {item['id']: item for item in data['findings'] if item['status'] in {'refuted', 'withdrawn'}}
    stopped_paths = dependency_paths(children, stopped)
    names = {item['id']: item['label'] for item in data['inputs']}
    names.update({item['id']: item['title'] for item in data['findings']})

    def refs(keys):
        # Readers see what a judgment rests on; the ID stays for tracing.
        return text['sep'].join(text['ref'].format(label=names[key], id=key) for key in keys)

    def issue_label(item):
        return text['issue_label'].format(id=item['id'], title=item['title'],
                                          status=text['issue_statuses'][item['status']])

    # Propagate issue membership once in dependency order. Per-issue calls to
    # impact would repeatedly validate the whole record and build unused paths.
    issue_bits = {item['id']: 0 for item in data['findings']}
    for index, issue in enumerate(data['issues']):
        for finding in issue['affected_findings']:
            issue_bits[finding] |= 1 << index
    for finding in validation['finding_order']:
        for child in children[finding]:
            issue_bits[child] |= issue_bits[finding]
    budget = [0]
    major = [item for item in data['issues'] if item['materiality'] == 'major' and item['status'] in ACTIVE]
    lines = _DocumentLines(['<!-- xikari-research-report -->', '', f'# {data["title"]}', '',
                            text['question'].format(data['question']), '', text['current'], '', data['summary'], '',
                            text['summary_refs'].format(refs(data['summary_refs'])), ''], budget)
    affected_summary = [key for key in data['summary_refs'] if key in stopped_paths]
    if affected_summary:
        lines += [text['stopped_head'], '']
        for key in affected_summary:
            path = stopped_paths[key]
            lines += [text['stopped_item'].format(path=' → '.join(path),
                                                  status=text['statuses'][stopped[path[0]]['status']]), '']
        lines += [text['stopped_tail'], '']
    if validation['synthetic_inputs']:
        lines += [text['synthetic'].format(refs(validation['synthetic_inputs'])), '']
    if validation['theory_bindings_not_current']:
        lines += [text['theory_report'].format(
            ', '.join(row['issue'] for row in validation['theory_bindings_not_current'])), '']
    if major:
        lines += [text['major'], '']
        for item in major:
            lines += [text['major_item'].format(label=issue_label(item), consequence=item['consequence']), '']
    lines += [text['scope'], '', data['scope'], '', data['method'], '', text['argument'], '']
    for item in data['findings']:
        lines += [f'### {item["id"]} · {item["title"]}', '',
                  text['identity'].format(kind=text['kinds'][item['kind']], status=text['statuses'][item['status']]), '',
                  item['body'], '', text['depends'].format(refs(item['depends_on'])), '']
        if item['id'] in unknown_paths:
            lines += [text['unknown_dep'].format(path=' → '.join(unknown_paths[item['id']])), '']
        if item['id'] in stopped_paths and item['id'] not in stopped:
            path = stopped_paths[item['id']]
            lines += [text['stopped_dep'].format(path=' → '.join(path),
                                                 status=text['statuses'][stopped[path[0]]['status']]), '']
        if item['limitations']:
            lines += [text['limits'], ''] + [f'- {entry}' for entry in item['limitations']] + ['']
        related = [issue for index, issue in enumerate(data['issues']) if issue_bits[item['id']] & (1 << index)]
        for issue in related:
            lines += [text['related'].format(label=issue_label(issue), consequence=issue['consequence']), '']
            if issue['status'] == 'superseded':
                lines += [text['successors'].format(', '.join(issue['superseded_by'])), '']
        lines += [text['change'], ''] + [f'- {entry}' for entry in item['change_conditions']] + ['']
    lines += [text['assessment'], '', data['issue_assessment'], '', text['see_issues'], '']
    lines += _source_lines(data, text) + [f'> {text["notice"]}', '']

    boundary = _DocumentLines(['<!-- xikari-research-issues -->', '', text['issues_title'].format(data['title']), '',
                               text['issues_question'].format(data['question']), '', data['issue_assessment'], '',
                               text['see_report'], ''], budget)
    if not data['issues']:
        boundary += [text['no_issues'], '']
    for item in data['issues']:
        boundary += [f'## {issue_label(item)}', '',
                     text['categories_line'].format(text['cat_sep'].join(text['categories'][key]
                                                                         for key in item['categories'])), '',
                     text['affected_line'].format(findings=refs(item['affected_findings']),
                                                  materiality=text['materiality'][item['materiality']]), '']
        if item['status'] == 'superseded':
            boundary += [text['successors_issue'].format(', '.join(item['superseded_by'])), '']
        for key, label in text['fields']:
            # Optional fields that are empty for this status are left out rather
            # than shown as an empty promise of further work.
            if item[key]:
                boundary += [f'**{label}{"：" if lang == "zh" else ":"}**', '', item[key], '']
        if 'theory' in item:
            theory = item['theory']
            boundary += [text['theory_head'], '', text['theory_anchor'].format(theory['anchor']), '',
                         theory['proposition'], '', text['theory_sha'].format(theory['source_sha256']), '']
            if theory['source_sha256'] != theory_index()['sha256']:
                boundary += [text['theory_notice'].format(domain_mapping.theory_version_warning(
                    domain_mapping.theory_binding(theory['source_sha256']), text['theory_subject'], lang)), '']
            boundary += [text['theory_scope'].format(theory['scope']), '',
                         text['theory_challenge'].format(theory['challenge']), '', text['theory_tail'], '']
    boundary += [f'> {text["notice"]}', '']
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
    render.add_argument('--lang', choices=sorted(LABELS), default='zh',
                        help='固定标签与说明的语言：zh（默认）或 en；不翻译作者正文')
    changes = commands.add_parser('impact', help='由变更 ID 追踪受影响结论')
    changes.add_argument('--changed', action='append', required=True, help='可重复的输入或结论 ID')
    bridge = commands.add_parser('impact-mapping', help='由显式映射旧快照追踪研究中的已绑定依赖')
    bridge.add_argument('--mapping', required=True, type=Path, help='mapping_ref 所据的原始映射快照')
    bridge.add_argument('--changed', action='append', required=True, help='可重复的映射来源、条目或成文成果 ID')
    args = parser.parse_args(argv)
    try:
        data = read_research(args.research)
        if args.command == 'validate':
            result = validate_research(data)
        elif args.command == 'impact':
            result = impact(data, args.changed)
        elif args.command == 'impact-mapping':
            result = impact_mapping(data, args.mapping, args.changed)
        else:
            output = write_documents(render_documents(data, args.lang), args.output)
            result = {'output': str(output.resolve()), 'files': ['research-report.md', 'research-issues.md'],
                      'notice': NOTICE}
        chunks = []
        size = 0
        for chunk in json.JSONEncoder(ensure_ascii=False, indent=2, allow_nan=False).iterencode(result):
            size += len(chunk.encode('utf-8'))
            if size > MAX_RENDER_BYTES:
                raise ResearchError('JSON 结果超过 32 MiB；请按实际专题拆分。')
            chunks.append(chunk)
        print(''.join(chunks))
        return 0
    except (OSError, UnicodeError, ResearchError, ValueError) as exc:
        print(f'研究成果处理失败：{exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
