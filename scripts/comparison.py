#!/usr/bin/env python3
"""Preserve each cell's basis identity in a reproducible candidate comparison.

The table never decides which option is better. Unknown stays unknown and never
becomes zero, worst, or best; a dimension that cannot be ordered produces no
ranking at all; an assumed value is marked wherever it appears. Anything
directional is stated with the conditions it holds under.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import math
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


TOOL = 'xikari-comparison-1'
MD_MARK = '<!-- xikari-comparison-table -->'
HTML_MARK = '<meta name="generator" content="Xikari comparison table">'
OUTPUTS = {'json': 'comparison-results.json', 'md': 'comparison-table.md', 'html': 'comparison-table.html'}
BASIS = {'observed', 'assumed', 'unknown'}
DIRECTIONS = {'higher_is_better', 'lower_is_better', 'not_orderable'}
MAX_CANDIDATES = 16
MAX_DIMENSIONS = 24
IDENTIFIER = re.compile(r'[A-Za-z][A-Za-z0-9._-]{0,63}\Z')
LABEL = {'observed': '事实', 'assumed': '假设', 'unknown': '未知'}
BOUNDARY = '本表只呈现各选项在各维度上的取值与依据身份，不判断方案价值，也不给出整体最优方案。'


class ComparisonError(ValueError):
    """Invalid comparison data."""


def text_field(item, field, where, required=False, limit=8000):
    value = item.get(field, '')
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise ComparisonError(f'{where}.{field}须为{"非空" if required else ""}文本，不超过{limit}字符。')
    return value


def text_list(item, field, where, required=False):
    value = item.get(field, [])
    if not isinstance(value, list) or any(not isinstance(entry, str) or not entry.strip() for entry in value):
        raise ComparisonError(f'{where}.{field}应是文字列表。')
    if required and not value:
        raise ComparisonError(f'{where}.{field}不能为空。')
    return value


def validate_comparison(model) -> None:
    if not isinstance(model, dict) or model.get('schema_version') != 1:
        raise ComparisonError('比较模型须为schema_version=1的JSON对象。')
    extra = set(model) - {'schema_version', 'title', 'purpose', 'fictional', 'assumptions', 'boundaries',
                          'candidates', 'dimensions', 'cells'}
    if extra:
        raise ComparisonError('比较模型含未知字段，不能静默忽略: ' + ', '.join(sorted(extra)))
    text_field(model, 'title', '比较模型', True)
    text_field(model, 'purpose', '比较模型', True)
    if type(model.get('fictional')) is not bool:
        raise ComparisonError('fictional须明确为true或false。')
    text_list(model, 'assumptions', '比较模型', required=True)
    text_list(model, 'boundaries', '比较模型', required=True)
    candidates = model.get('candidates')
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= MAX_CANDIDATES:
        raise ComparisonError(f'candidates须为1—{MAX_CANDIDATES}项的列表。')
    seen = set()
    for item in candidates:
        if not isinstance(item, dict):
            raise ComparisonError('每个候选须为对象。')
        key = item.get('id')
        if not isinstance(key, str) or not IDENTIFIER.fullmatch(key):
            raise ComparisonError(f'候选ID须为英文字母开头的名称: {key!r}')
        if key in seen:
            raise ComparisonError(f'候选ID重复: {key}')
        seen.add(key)
        text_field(item, 'label', f'候选 {key}', True)
    dimensions = model.get('dimensions')
    if not isinstance(dimensions, list) or not 1 <= len(dimensions) <= MAX_DIMENSIONS:
        raise ComparisonError(f'dimensions须为1—{MAX_DIMENSIONS}项的列表。')
    dim_ids = set()
    for item in dimensions:
        if not isinstance(item, dict):
            raise ComparisonError('每个维度须为对象。')
        key = item.get('id')
        if not isinstance(key, str) or not IDENTIFIER.fullmatch(key):
            raise ComparisonError(f'维度ID须为英文字母开头的名称: {key!r}')
        if key in dim_ids:
            raise ComparisonError(f'维度ID重复: {key}')
        dim_ids.add(key)
        text_field(item, 'label', f'维度 {key}', True)
        text_field(item, 'unit', f'维度 {key}')
        if item.get('direction') not in DIRECTIONS:
            raise ComparisonError(f'维度 {key} 的direction须为higher_is_better、lower_is_better或not_orderable。')
    cells = model.get('cells')
    if not isinstance(cells, dict):
        raise ComparisonError('cells须为「候选ID到维度取值」的对象。')
    for key in cells:
        if key not in seen:
            raise ComparisonError(f'cells含未知候选: {key}')
    for key in seen:
        if key not in cells:
            raise ComparisonError(f'候选 {key} 缺少cells条目。')
        row = cells[key]
        if not isinstance(row, dict):
            raise ComparisonError(f'候选 {key} 的cells须为对象。')
        for dim in row:
            if dim not in dim_ids:
                raise ComparisonError(f'候选 {key} 含未知维度: {dim}')
        for dim in dim_ids:
            if dim not in row:
                raise ComparisonError(f'候选 {key} 缺少维度 {dim}；缺失须显式写作unknown，不能省略。')
            cell = row[dim]
            if not isinstance(cell, dict):
                raise ComparisonError(f'候选 {key} 的 {dim} 单元格须为对象。')
            if 'basis' not in cell:
                raise ComparisonError(f'候选 {key} 的 {dim} 单元格须声明basis；缺失不能默认为事实。')
            if cell['basis'] not in BASIS:
                raise ComparisonError(f'候选 {key} 的 {dim} 单元格basis须为observed、assumed或unknown。')
            if 'value' not in cell:
                raise ComparisonError(f'候选 {key} 的 {dim} 单元格须包含value；unknown也须显式写出。')
            value = cell['value']
            if cell['basis'] == 'unknown' and value is not None:
                raise ComparisonError(f'候选 {key} 的 {dim} 标为unknown时value须为null，不能用数值冒充未知。')
            if cell['basis'] != 'unknown' and value is None:
                raise ComparisonError(f'候选 {key} 的 {dim} 有basis={cell["basis"]}却无value。')
            if cell['basis'] == 'observed' and not str(cell.get('source', '')).strip():
                raise ComparisonError(f'候选 {key} 的 {dim} 标为observed须给出source；工具不验证来源真实性。')
            if 'source' in cell:
                text_field(cell, 'source', f'候选 {key} 的 {dim}')
            if value is not None and not (isinstance(value, str) or type(value) in {int, float, bool}):
                raise ComparisonError(f'候选 {key} 的 {dim} value须为文本、数字、布尔或null。')
            if type(value) is float and not math.isfinite(value):
                raise ComparisonError(f'候选 {key} 的 {dim} value须为有限数。')
            text_field(cell, 'note', f'候选 {key} 的 {dim}', limit=8000) if 'note' in cell else None


def read_comparison(path: Path) -> dict:
    data = Path(path).read_bytes()
    if len(data) > 8 * 1024 * 1024:
        raise ComparisonError('比较模型超过8MiB，请拆分为多个比较。')
    text = data.decode('utf-8-sig')
    def reject_duplicates(pairs):
        seen = {}
        for key, value in pairs:
            if key in seen:
                raise ComparisonError(f'JSON含重复键: {key}')
            seen[key] = value
        return seen
    try:
        return json.loads(text, object_pairs_hook=reject_duplicates)
    except json.JSONDecodeError as exc:
        raise ComparisonError(f'比较模型不是有效JSON: {exc}') from exc


def display(value, basis):
    if value is None:
        return '未知'
    if type(value) is bool:
        return '是' if value else '否'
    return str(value)


def build_comparison(model: dict) -> dict:
    """Pure evaluation: no filesystem access, so results are reproducible."""
    validate_comparison(model)
    dimensions = []
    cells_have_assumed = False
    cells_have_unknown = False
    for dimension in model['dimensions']:
        key = dimension['id']
        entry = {
            'id': key, 'label': dimension['label'], 'unit': dimension.get('unit', ''),
            'direction': dimension['direction'],
        }
        values = []
        for candidate in model['candidates']:
            cell = model['cells'][candidate['id']][key]
            values.append({
                'id': candidate['id'], 'label': candidate['label'],
                'value': cell.get('value'), 'basis': cell['basis'],
                'display': display(cell.get('value'), cell['basis']),
                'note': cell.get('note', ''), 'source': cell.get('source', ''),
            })
            if cell['basis'] == 'assumed':
                cells_have_assumed = True
            if cell['basis'] == 'unknown':
                cells_have_unknown = True
        entry['values'] = values
        if dimension['direction'] == 'not_orderable':
            entry['reason'] = 'not_orderable：此维度没有共同的比较尺度，本工具不生成排序。'
            entry['unranked'] = [
                {'id': item['id'], 'label': item['label'], 'reason': 'not_orderable'}
                for item in values
            ]
        else:
            orderable = [item for item in values
                         if item['value'] is not None and type(item['value']) in {int, float}
                         and not isinstance(item['value'], bool)]
            ranked = sorted(orderable, key=lambda item: item['value'],
                            reverse=dimension['direction'] == 'higher_is_better')
            entry['ranking'] = [
                {'id': item['id'], 'label': item['label'], 'value': item['value'], 'basis': item['basis'],
                 'rank': position, 'holds_when': '仅在本次列出的取值与依据条件下成立'}
                for position, item in enumerate(ranked, 1)
            ]
            entry['unranked'] = [
                {'id': item['id'], 'label': item['label'],
                 'reason': 'unknown' if item['basis'] == 'unknown' else '非数值取值，不能参与数值排序'}
                for item in values
                if item not in orderable
            ]
        dimensions.append(entry)
    return {
        'format': TOOL, 'schema_version': 1,
        'title': model['title'], 'purpose': model['purpose'],
        'fictional': model['fictional'],
        'assumptions': model['assumptions'], 'boundaries': model['boundaries'],
        'candidate_count': len(model['candidates']),
        'dimension_count': len(model['dimensions']),
        'candidates': [{'id': item['id'], 'label': item['label']} for item in model['candidates']],
        'dimensions': dimensions,
        'cells_have_assumed': cells_have_assumed,
        'cells_have_unknown': cells_have_unknown,
        'boundary': BOUNDARY,
        'interpretation': '依据身份分别为事实（作者声明有来源，未经验证）、假设与未知。未知未作0、最差或最好处理；'
                          '不可排序维度不产生排序。排序只在本次列出的取值与依据条件下成立，不代表现实中最优或可实施。',
    }


def render_json(result: dict) -> str:
    rows = []
    for candidate in result['candidates']:
        values = {}
        for dimension in result['dimensions']:
            cell = next(item for item in dimension['values'] if item['id'] == candidate['id'])
            values[dimension['id']] = {
                'label': dimension['label'], 'value': cell['value'], 'basis': cell['basis'],
                'display': cell['display'], 'note': cell['note'], 'source': cell['source'],
            }
        rows.append({'candidate': candidate['id'], 'label': candidate['label'], 'values': values})
    return json.dumps({**result, 'rows': rows}, ensure_ascii=False, indent=2, allow_nan=False)


def render_markdown(result: dict) -> str:
    lines = [MD_MARK, '', f"# {result['title']}", '', result['purpose'], '']
    lines.append(('这是明确虚构的教学比较，取值不是现实事实。' if result['fictional']
                  else '这是作者提供的比较；各单元格的来源与假设仍需分别判断。'))
    lines.append('')
    candidates = result['candidates']
    lines.append('| 维度 | ' + ' | '.join(candidate['label'] for candidate in candidates) + ' |')
    lines.append('| --- | ' + ' | '.join('---' for _ in candidates) + ' |')
    for dimension in result['dimensions']:
        unit = f"（{dimension['unit']}）" if dimension['unit'] else ''
        cells = []
        for candidate in candidates:
            cell = next(item for item in dimension['values'] if item['id'] == candidate['id'])
            mark = LABEL[cell['basis']]
            if cell['basis'] == 'unknown':
                cells.append(f"未知")
            else:
                cells.append(f"{cell['display']}·{mark}")
        lines.append(f"| {dimension['label']}{unit} | " + ' | '.join(cells) + ' |')
    lines.append('')
    lines.append(f'标记：事实=作者声明有来源；假设=作者设定；未知=尚无可信取值。{BOUNDARY}')
    lines.append('')
    lines.append('## 各维度排序与不可排序说明')
    lines.append('')
    for dimension in result['dimensions']:
        lines.append(f"### {dimension['label']}")
        lines.append('')
        if 'ranking' in dimension:
            lines.append('本次取值下的顺序（不代表现实最优）：')
            lines.append('')
            for item in dimension['ranking']:
                lines.append(f"{item['rank']}. {item['label']}：{item['value']}（{LABEL[item['basis']]}）")
        else:
            lines.append(dimension['reason'])
        for item in dimension['unranked']:
            lines.append(f"- 未参与排序：{item['label']}（{item['reason']}）")
        lines.append('')
    lines.append('## 明确假设')
    lines.append('')
    for entry in result['assumptions']:
        lines.append(f'- {entry}')
    lines.append('')
    lines.append('## 解释边界')
    lines.append('')
    for entry in result['boundaries']:
        lines.append(f'- {entry}')
    lines.append('')
    lines.append(f"> {result['interpretation']}")
    lines.append('')
    return '\n'.join(lines)


def render_html(result: dict) -> str:
    header = ''.join(f'<th scope="col">{html.escape(item["label"])}</th>' for item in result['candidates'])
    dimension_rows = []
    for dimension in result['dimensions']:
        unit = f"（{dimension['unit']}）" if dimension['unit'] else ''
        if 'ranking' in dimension:
            ordered = '；'.join(f"{item['rank']}. {html.escape(item['label'])}（{LABEL[item['basis']]}）"
                                for item in dimension['ranking']) or '没有可参与排序的取值'
            extra = ''.join(f"<li>未参与排序：{html.escape(item['label'])}（{html.escape(item['reason'])}）</li>"
                            for item in dimension['unranked'])
            body = f'<p>本次取值下的顺序（不代表现实最优）：{ordered}</p>'
            if extra:
                body += f'<ul>{extra}</ul>'
        else:
            body = f'<p>{html.escape(dimension["reason"])}</p>'
        dimension_rows.append(f'<section><h3>{html.escape(dimension["label"])}{html.escape(unit)}</h3>{body}</section>')
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{HTML_MARK}<title>{html.escape(result['title'])}</title>
<style>{CSS}</style></head>
<body><main>
<header><h1>{html.escape(result['title'])}</h1><p>{html.escape(result['purpose'])}</p>
<p class="notice">{'这是明确虚构的教学比较，取值不是现实事实。' if result['fictional'] else '这是作者提供的比较；各单元格的来源与假设仍需分别判断。'}</p></header>
<section><h2>比较表</h2>
<div class="table-scroll" tabindex="0" role="region" aria-label="方案比较，可横向滚动"><table>
<thead><tr><th scope="col">维度</th>{header}</tr></thead>
<tbody>{''.join(dimension_row(item, result) for item in result['dimensions'])}</tbody>
</table></div>
<p class="legend">标记：事实＝作者声明有来源（工具未验证）；假设＝作者设定；未知＝尚无可信取值。{html.escape(BOUNDARY)}</p></section>
<section><h2>各维度排序与不可排序说明</h2>{''.join(dimension_rows)}</section>
<section class="two-columns"><div><h2>明确假设</h2><ul>{''.join(f'<li>{html.escape(t)}</li>' for t in result['assumptions'])}</ul></div>
<div><h2>解释边界</h2><ul>{''.join(f'<li>{html.escape(t)}</li>' for t in result['boundaries'])}</ul></div></section>
<footer><p>{html.escape(result['interpretation'])}</p>
<a download="comparison-results.json" href="data:application/json;charset=utf-8;base64,{base64.b64encode(render_json(result).encode('utf-8')).decode('ascii')}">下载完整比较结果</a></footer>
</main></body></html>'''


def type_note(cell):
    if cell['basis'] == 'observed' and cell['source']:
        return f'来源：{cell["source"]}（由作者声明，未经验证）'
    if cell['basis'] == 'assumed':
        return '作者设定的假设值'
    return ''


def dimension_row(dimension, result):
    cells = []
    for candidate in result['candidates']:
        cell = next(item for item in dimension['values'] if item['id'] == candidate['id'])
        notes = [text for text in (cell['note'], type_note(cell)) if text]
        cells.append('<td>' + html.escape('未知' if cell['basis'] == 'unknown' else cell['display'])
                     + f'<span class="basis basis-{cell["basis"]}">{LABEL[cell["basis"]]}</span>'
                     + (f'<span class="note">{html.escape("；".join(notes))}</span>' if notes else '')
                     + '</td>')
    unit = f'（{dimension["unit"]}）' if dimension['unit'] else ''
    return (f'<tr><th scope="row">{html.escape(dimension["label"])}{html.escape(unit)}</th>'
            + ''.join(cells) + '</tr>')


CSS = """
:root{color-scheme:light;--ink:#1d2b28;--ink-strong:#0f1a17;--muted:#4d5f5a;--paper:#f6f5ef;--page:#fffef9;
--line:#ccd6ce;--line-strong:#93a89b;--accent:#1c5a47;--accent-soft:#e4ece5;--accent-line:#8fb3a2;--raise:#eff1e9;
--serif:"Noto Serif SC","Source Han Serif SC","Songti SC","SimSun",serif;--radius:6px;--radius-lg:10px}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:"Segoe UI","Microsoft YaHei",system-ui,sans-serif;font-size:16px;line-height:1.75}
main{max-width:1200px;margin:auto;padding:52px 32px 76px}
h1{font-family:var(--serif);font-size:2.1rem;line-height:1.3;margin:12px 0 18px;color:var(--ink-strong);padding-bottom:.45em;border-bottom:1px solid var(--line)}
h1::after{content:"";display:block;width:64px;height:3px;background:var(--accent);margin:.5em 0 -.45em}
h2{font-family:var(--serif);font-size:1.22rem;margin:0 0 16px;color:var(--ink-strong)}
h3{font-family:var(--serif);font-size:1.02rem;margin:0 0 8px;color:var(--ink-strong)}
p{margin:0 0 14px}section{padding:30px 0;border-top:1px solid var(--line)}section:first-of-type{border-top:none}
.notice{border-left:3px solid var(--accent);padding:14px 20px;background:var(--accent-soft);border-radius:0 var(--radius) var(--radius) 0;color:var(--muted)}
.table-scroll{overflow:auto;border:1px solid var(--line);border-radius:var(--radius-lg);background:var(--page)}
table{border-collapse:collapse;width:100%;font-size:.92rem;text-align:left}
th,td{padding:13px 15px;border-bottom:1px solid var(--line);vertical-align:top;min-width:110px}
th{background:var(--accent-soft);font-weight:700;color:var(--ink-strong);white-space:nowrap}
tbody tr:nth-child(even){background:var(--raise)}tbody tr:last-child td,tbody tr:last-child th{border-bottom:none}
.basis{display:inline-block;margin-left:8px;padding:1px 7px;border-radius:10px;font-size:.72rem;line-height:1.7}
.basis-observed{background:#dce9df;color:#1c5a47}.basis-assumed{background:#f2e6cd;color:#7a5a12}.basis-unknown{background:#e6e6e6;color:#5a5a5a}
.note{display:block;margin-top:4px;font-size:.76rem;color:var(--muted)}
.legend{font-size:.86rem;color:var(--muted)}
.two-columns{display:grid;grid-template-columns:1fr 1fr;gap:40px}
ul{padding-left:1.4em;margin:0}li{margin:0 0 10px}li::marker{color:var(--accent)}
footer{padding-top:26px;color:var(--muted);font-size:.9rem;border-top:1px solid var(--line)}
a{color:var(--accent)}::selection{background:#dce9df}
@media(max-width:760px){main{padding:30px 18px 52px}.two-columns{grid-template-columns:1fr;gap:18px}th,td{padding:10px;min-width:96px}h1{font-size:1.8rem}}
@media print{body{background:#fff}main{padding:0;max-width:none}.table-scroll{overflow:visible;border:1px solid #999;border-radius:0}
table{font-size:9pt}th,td{min-width:0;padding:7px}tbody tr:nth-child(even){background:none}section{break-inside:avoid}
.basis{border:1px solid #999;background:none!important;color:#000!important}}
""".strip()


def owned_output(path: Path, kind: str) -> bool:
    try:
        if kind == 'json':
            return json.loads(path.read_text(encoding='utf-8')).get('format') == TOOL
        if kind == 'html':
            return HTML_MARK in path.read_text(encoding='utf-8')[:4096]
        return path.read_text(encoding='utf-8').startswith(MD_MARK)
    except (OSError, ValueError, AttributeError):
        return False


def same_path(first: Path, second: Path) -> bool:
    if Path(first).resolve() == Path(second).resolve():
        return True
    try:
        return Path(first).samefile(second)
    except OSError:
        return False


def write_outputs(result: dict, source: Path, output: Path, output_format: str = 'all', force: bool = False) -> dict:
    require_external_output(output, __file__)
    kinds = list(OUTPUTS) if output_format == 'all' else [output_format]
    paths = {kind: Path(output) / OUTPUTS[kind] for kind in kinds}
    for kind, path in paths.items():
        require_external_output(path, __file__)
        if same_path(path, source):
            raise ComparisonError('输出路径与输入文件相同，--force也不能覆盖输入。')
        if path.is_symlink():
            raise ComparisonError(f'输出是符号链接，拒绝替换: {path}')
        if path.exists() and (not force or not owned_output(path, kind)):
            raise ComparisonError(f'输出已存在且未授权覆盖本工具产物: {path}；使用新目录，或仅对已有本工具产物使用--force。')
    rendered = {}
    for kind in kinds:
        if kind == 'json':
            rendered[kind] = render_json(result) + '\n'
        elif kind == 'md':
            rendered[kind] = render_markdown(result)
        else:
            rendered[kind] = render_html(result)
        if len(rendered[kind].encode('utf-8')) > 32 * 1024 * 1024:
            raise ComparisonError('单项输出超过32MiB；减少候选或维度数量。')
    lock = Path(output) / '.comparison.lock'
    require_external_output(lock, __file__)
    if same_path(lock, source):
        raise ComparisonError('输出锁路径与输入相同，拒绝写入。')
    Path(output).mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ComparisonError(f'输出目录正在写入或存在遗留锁: {lock}；未自动覆盖。') from exc
    os.close(descriptor)
    staged, previous, changed = {}, {}, []
    try:
        for kind, path in paths.items():
            if path.exists() and (not force or not owned_output(path, kind)):
                raise ComparisonError(f'输出路径在处理期间出现冲突: {path}')
            previous[kind] = path.read_bytes() if path.exists() else None
            fd, name = tempfile.mkstemp(prefix=f'.comparison-{kind}-', suffix='.tmp', dir=Path(output))
            with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
                stream.write(rendered[kind])
                stream.flush()
                os.fsync(stream.fileno())
            staged[kind] = Path(name)
        for kind, path in paths.items():
            current = path.read_bytes() if path.exists() else None
            if current != previous[kind]:
                raise ComparisonError(f'输出在处理期间被其他工作改变: {path}')
            os.replace(staged[kind], path)
            changed.append((kind, path))
            staged[kind] = None
    except BaseException:
        for kind, path in reversed(changed):
            saved = previous[kind]
            try:
                if saved is None:
                    path.unlink(missing_ok=True)
                else:
                    descriptor, name = tempfile.mkstemp(
                        prefix=f'.comparison-restore-{kind}-', suffix='.tmp', dir=path.parent)
                    with os.fdopen(descriptor, 'wb') as stream:
                        stream.write(saved)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(name, path)
            except OSError:
                pass
        raise
    finally:
        for temporary in staged.values():
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        lock.unlink(missing_ok=True)
    return {kind: str(path.resolve()) for kind, path in paths.items()}


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model', type=Path, help='比较模型 JSON')
    parser.add_argument('--output', '-o', type=Path, required=True, help='安装目录之外的输出目录')
    parser.add_argument('--format', choices=['json', 'md', 'html', 'all'], default='all')
    parser.add_argument('--force', action='store_true', help='仅覆盖本工具先前生成的同名产物')
    args = parser.parse_args(argv)
    try:
        model = read_comparison(args.model)
        result = build_comparison(model)
        outputs = write_outputs(result, args.model, args.output, args.format, args.force)
        print(json.dumps({
            'outputs': outputs,
            'candidates': result['candidate_count'],
            'dimensions': result['dimension_count'],
            'boundary': result['boundary'],
        }, ensure_ascii=False))
        return 0
    except (OSError, UnicodeError, ComparisonError, ValueError) as error:
        print(f'比较表生成失败：{error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
