#!/usr/bin/env python3
"""Freeze conditional forecasts, append outcomes and compare preregistered baselines.

Each record concerns one recursive order. Structural checks and computed losses do
not certify a source, a prediction, a model, or authority to act. Local digests
detect accidental edits; they are not signatures or proof of prior knowledge.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
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
    import read_source
    import forecast_scores
    import forecast_chain
finally:
    sys.path.pop(0)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'source' / 'Xikari-条件结构与转化论.md'
MANIFEST = ROOT / 'source' / 'source-manifest.json'
FORMAT = 'xikari-forecasts-1'
STATUSES = {'supported', 'not_supported', 'undetermined', 'target_invalid', 'not_evaluable'}
EVIDENCE_KINDS = {'live', 'backtest', 'teaching', 'synthetic'}
EXPRESSION_TYPES = {'probability', 'interval', 'time_window', 'rank', 'direction', 'none'}
BASELINE_TYPES = {'recent_state', 'trend', 'historical_frequency', 'actor_only', 'primary_circle_only', 'domain_model'}
RECURSIVE_BASELINE_TYPES = {'state_continuation', 'direct_long_term', 'shallower_continuation'}
LOSS_METRICS = {'brier', 'log_loss', 'interval_score'}
HIT_METRICS = {'direction_hit', 'rank_top_hit'}
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z')
REQUIRED = {
    'id', 'created_at', 'theory_sha256', 'skill_version', 'host_model', 'evidence_kind', 'order',
    'question', 'target', 'resolution_rule', 'window', 'input_cutoff', 'baseline_time', 'scope',
    'baselines', 'mechanisms', 'paths', 'expression', 'calibration_plan', 'decision_threshold',
    'pause_conditions', 'retire_conditions', 'evidence_refs',
}
RESOLUTION_FIELDS = {'forecast_id', 'resolved_at', 'outcome_source', 'observed', 'status', 'path_match', 'model_updates'}


class ForecastError(ValueError):
    """Invalid registration or result."""


def fail(message):
    raise ForecastError(message)


def utcnow():
    return datetime.now(timezone.utc)


def timestamp():
    return utcnow().isoformat().replace('+00:00', 'Z')


def canonical(value):
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (ValueError, TypeError) as error:
        raise ForecastError('JSON不得含NaN、Infinity或非JSON数据') from error


def digest(record):
    return hashlib.sha256(canonical({key: value for key, value in record.items() if key != 'record_sha256'})).hexdigest()


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                fail(f'JSON含重复字段：{key}')
            result[key] = value
        return result
    try:
        return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=pairs,
                          parse_constant=lambda value: fail(f'JSON含非法数值：{value}'))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ForecastError(f'无法读取JSON {path}: {error}') from error


def text(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 16000:
        fail(f'{name}须为非空文本，不超过16000字符')
    return value


def identifier(value, name):
    if not isinstance(value, str) or not ID.fullmatch(value):
        fail(f'{name}须为不超过96字符的字母、数字、点、下划线或连字符标识')
    return value


def string_list(value, name, nonempty=True):
    if not isinstance(value, list) or (nonempty and not value):
        fail(f'{name}须为{"非空" if nonempty else ""}文字列表')
    for item in value:
        text(item, name)
    return value


def number(value, name):
    try:
        finite = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        fail(f'{name}须为有限数值，不能是布尔值或字符串')
    return value


def instant(value, name):
    text(value, name)
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise ForecastError(f'{name}须为带时区的ISO8601时间') from error
    if result.tzinfo is None or result.utcoffset() is None:
        fail(f'{name}须声明时区')
    return result.astimezone(timezone.utc)


def window(value, name):
    if not isinstance(value, dict) or set(value) != {'start', 'end'}:
        fail(f'{name}须含start和end')
    start, end = instant(value['start'], name + '.start'), instant(value['end'], name + '.end')
    if start >= end:
        fail(f'{name}.start必须早于end')
    return start, end


def expression(value, name):
    if not isinstance(value, dict) or not isinstance(value.get('type'), str) or value['type'] not in EXPRESSION_TYPES:
        fail(f'{name}.type须为probability、interval、time_window、rank、direction或none')
    text(value.get('basis'), name + '.basis')
    kind = value['type']
    if kind == 'probability':
        probability = number(value.get('value'), name + '.value')
        if not 0 <= probability <= 1:
            fail(f'{name}.value概率须在0与1之间')
    elif kind == 'interval':
        lower, upper = number(value.get('lower'), name + '.lower'), number(value.get('upper'), name + '.upper')
        if lower > upper:
            fail(f'{name}区间上下界倒置')
        text(value.get('unit'), name + '.unit')
        if value.get('quantity', 'numeric') != 'numeric':
            fail('本工具的interval只支持数值目标区间；不将概率区间与二元标签比较')
    elif kind == 'rank':
        values = string_list(value.get('value'), name + '.value')
        if len(values) != len(set(values)):
            fail(f'{name}排序中有重复项')
    elif kind == 'direction':
        text(value.get('value'), name + '.value')
    elif kind == 'time_window':
        window({'start': value.get('start'), 'end': value.get('end')}, name)
    elif value.get('value') is not None:
        fail(f'{name}的none表达只能使用null值')


def validate_forecast(record, *, new=False):
    if not isinstance(record, dict):
        fail('前瞻须为JSON对象')
    missing = REQUIRED - set(record)
    if missing:
        fail('前瞻缺少字段：' + ', '.join(sorted(missing)))
    unknown = set(record) - REQUIRED - {'supersedes', 'registered_at', 'record_sha256', 'validation_version', 'parent'}
    if unknown:
        fail('不支持的前瞻字段：' + ', '.join(sorted(unknown)))
    canonical(record)
    if type(record.get('validation_version', 1)) is not int or record.get('validation_version', 1) not in {1, 2}:
        fail('不支持的validation_version')
    strict = new or record.get('validation_version', 1) >= 2
    identifier(record['id'], 'id')
    for name in ['question', 'target', 'resolution_rule', 'skill_version', 'host_model']:
        text(record[name], name)
    if not isinstance(record['theory_sha256'], str) or not re.fullmatch('[0-9a-f]{64}', record['theory_sha256']):
        fail('theory_sha256须为小写SHA-256')
    if not isinstance(record['evidence_kind'], str) or record['evidence_kind'] not in EVIDENCE_KINDS:
        fail('evidence_kind须为live、backtest、teaching或synthetic')
    if type(record['order']) is not int or record['order'] not in {1, 2, 3}:
        fail('order须为整数1、2或3；各阶分开登记')
    if strict and record['order'] > 1 and 'parent' not in record:
        fail('新登记的二、三阶前瞻须声明parent.forecast_id和parent.path_id')
    if 'parent' in record:
        parent = record['parent']
        if not isinstance(parent, dict) or set(parent) != {'forecast_id', 'path_id'}:
            fail('parent须含forecast_id和path_id，不能为null或附加其他字段')
        identifier(parent['forecast_id'], 'parent.forecast_id')
        identifier(parent['path_id'], 'parent.path_id')
    created = instant(record['created_at'], 'created_at')
    cutoff = instant(record['input_cutoff'], 'input_cutoff')
    baseline = instant(record['baseline_time'], 'baseline_time')
    _, end = window(record['window'], 'window')
    if not baseline <= cutoff <= created < end:
        fail('时间关系须为baseline_time <= input_cutoff <= created_at < window.end')
    if created > utcnow():
        fail('created_at不能在未来')
    scope = record['scope']
    if not isinstance(scope, dict):
        fail('scope须为对象')
    text(scope.get('object'), 'scope.object')
    for name in ['circles', 'affected_positions']:
        string_list(scope.get(name), 'scope.' + name)
    expression(record['expression'], 'expression')
    if record['expression']['type'] == 'time_window' or (strict and record['expression']['type'] == 'interval'):
        forecast_scores.validate_expression(record['expression'], record['window'], require_nominal=strict)
    if not isinstance(record['baselines'], list) or not record['baselines']:
        fail('至少登记一个简单基线')
    baseline_ids, baseline_types = set(), set()
    for entry in record['baselines']:
        if not isinstance(entry, dict):
            fail('baseline须为对象')
        key = identifier(entry.get('id'), 'baseline.id')
        if key in baseline_ids:
            fail('baseline.id重复')
        baseline_ids.add(key)
        baseline_type = text(entry.get('type'), 'baseline.type')
        if strict and baseline_type in baseline_types:
            fail('同一前瞻内baseline.type不能重复')
        baseline_types.add(baseline_type)
        expression(entry.get('expression'), 'baseline.expression')
        if entry['expression']['type'] == 'time_window' or (strict and entry['expression']['type'] == 'interval'):
            forecast_scores.validate_expression(entry['expression'], record['window'], require_nominal=strict)
        if entry['expression']['type'] != record['expression']['type']:
            fail('基线与前瞻须采用相同表达类型以保留同目标比较')
        if record['expression']['type'] == 'interval' and entry['expression']['unit'] != record['expression']['unit']:
            fail('基线与前瞻区间必须使用相同单位')
        if (strict and record['expression']['type'] == 'interval'
                and entry['expression']['nominal_coverage'] != record['expression']['nominal_coverage']):
            fail('基线与前瞻区间必须使用相同nominal_coverage')
        if 'window' in entry and window(entry['window'], 'baseline.window') != window(record['window'], 'window'):
            fail('基线与前瞻须使用相同评价期限')
    if record['order'] > 1 and not {'state_continuation', 'direct_long_term', 'shallower_continuation'} <= baseline_types:
        fail('递归二三阶须比较state_continuation、direct_long_term、shallower_continuation三类基线（§12.2.2）')
    if not isinstance(record['mechanisms'], list) or not record['mechanisms']:
        fail('mechanisms须为非空列表')
    for entry in record['mechanisms']:
        if not isinstance(entry, dict):
            fail('mechanism须为对象')
        identifier(entry.get('rule_id'), 'mechanism.rule_id')
        string_list(entry.get('anchors'), 'mechanism.anchors')
    if not isinstance(record['paths'], list) or not record['paths']:
        fail('paths须为非空列表')
    path_ids = set()
    for entry in record['paths']:
        if not isinstance(entry, dict) or 'parent' not in entry:
            fail('每条路径须为对象并声明parent，无上游时为null')
        key = identifier(entry.get('id'), 'path.id')
        if key in path_ids:
            fail('path.id重复')
        path_ids.add(key)
        if entry['parent'] is not None:
            text(entry['parent'], 'path.parent')
        if type(entry.get('order')) is not int or entry['order'] != record['order']:
            fail('path.order须与本条前瞻order相同；不同阶次另建登记')
        text(entry.get('description'), 'path.description')
        for name in ['conditions', 'early_signals', 'reverse_signals', 'stop_conditions']:
            string_list(entry.get(name), 'path.' + name)
    parents = {entry['id']: entry['parent'] for entry in record['paths']}
    for path_id, parent in parents.items():
        if parent is not None and parent not in parents:
            fail(f'路径{path_id}引用了不存在的本记录父路径：{parent}')
    for path_id, parent in parents.items():
        visited = {path_id}
        while parent is not None:
            if parent in visited:
                fail('path.parent不能形成自指或循环')
            visited.add(parent)
            parent = parents[parent]
    calibration = record['calibration_plan']
    if not isinstance(calibration, dict):
        fail('calibration_plan须为对象')
    string_list(calibration.get('metrics'), 'calibration_plan.metrics')
    text(calibration.get('description'), 'calibration_plan.description')
    if new and record['expression']['type'] == 'time_window' and 'interval_score' in calibration['metrics']:
        nominal = record['expression'].get('nominal_coverage')
        if nominal is None or any(entry['expression'].get('nominal_coverage') != nominal for entry in record['baselines']):
            fail('time_window的interval_score须为模型与全部基线登记相同nominal_coverage')
    for metric, kind in [('direction_hit', 'direction'), ('rank_top_hit', 'rank')]:
        if not strict or metric not in calibration['metrics']:
            continue
        if record['expression']['type'] != kind:
            fail(f'{metric}仅用于{kind}表达')
        options = string_list(record['expression'].get('options'), 'expression.options')
        if len(options) < 2 or len(options) != len(set(options)):
            fail('options须含至少两个互斥且不重复的结果类别')
        for expr in [record['expression']] + [b['expression'] for b in record['baselines']]:
            values = expr['value'] if kind == 'rank' else [expr['value']]
            if expr.get('options') != options or any(value not in options for value in values):
                fail('模型与基线须使用相同options，value须属于预登记类别')
    policy = calibration.get('degradation_policy')
    if policy is not None:
        if not isinstance(policy, dict) or not isinstance(policy.get('metric'), str) or policy['metric'] not in {'brier', 'log_loss'}:
            fail('degradation_policy须声明metric为brier或log_loss')
        for field in ['minimum_per_period', 'consecutive_months']:
            if type(policy.get(field)) is not int or policy[field] < 1:
                fail(f'degradation_policy.{field}须为正整数')
        if record['expression']['type'] != 'probability':
            fail('当前自动降级仅支持预登记的二元概率损失')
        if policy['metric'] not in calibration['metrics']:
            fail('降级所用指标须在calibration_plan.metrics中预登记')
    threshold = record['decision_threshold']
    if not isinstance(threshold, dict) or type(threshold.get('applicable')) is not bool:
        fail('decision_threshold须声明布尔applicable')
    text(threshold.get('reason'), 'decision_threshold.reason')
    if threshold['applicable']:
        number(threshold.get('value'), 'decision_threshold.value')
    for name in ['pause_conditions', 'retire_conditions', 'evidence_refs']:
        string_list(record[name], name)
    if 'supersedes' in record:
        identifier(record['supersedes'], 'supersedes')


def validate_parent(record, forecasts):
    if 'parent' not in record:
        return
    parent = forecasts.get(record['parent']['forecast_id'])
    if parent is None:
        fail('parent.forecast_id须引用已存在的父前瞻')
    if parent['order'] != record['order'] - 1:
        fail('parent前瞻阶次须恰好低一阶')
    if record['parent']['path_id'] not in {path['id'] for path in parent['paths']}:
        fail('parent.path_id不存在于父前瞻')
    if parent['theory_sha256'] != record['theory_sha256']:
        fail('parent与子前瞻的theory_sha256必须相同')
    if instant(record['input_cutoff'], 'input_cutoff') < instant(parent['input_cutoff'], 'parent.input_cutoff'):
        fail('子前瞻input_cutoff不得早于parent.input_cutoff')


def current_theory():
    manifest = read_json(MANIFEST)
    expected = manifest.get('sha256') if isinstance(manifest, dict) else None
    actual = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if actual != expected:
        fail('理论原文与source-manifest.json不一致，须先处理来源身份')
    return actual


def validate_resolution(record, forecast, *, new=False):
    if not isinstance(record, dict) or not RESOLUTION_FIELDS <= set(record):
        fail('结果缺少forecast_id、resolved_at、outcome_source、observed、status、path_match或model_updates')
    if record['forecast_id'] != forecast['id']:
        fail('结果未引用本条前瞻')
    canonical(record)
    validation_version = record.get('validation_version', record.get('scoring_version', 1))
    if type(validation_version) is not int or validation_version not in {1, 2}:
        fail('不支持的结果validation_version')
    resolved = instant(record['resolved_at'], 'resolved_at')
    if resolved < instant(forecast['window']['end'], 'window.end') or resolved > utcnow():
        fail('到期回写须在window.end之后，resolved_at不能在未来')
    text(record['outcome_source'], 'outcome_source')
    if not isinstance(record['status'], str) or record['status'] not in STATUSES:
        fail('status须为supported、not_supported、undetermined、target_invalid或not_evaluable')
    if record['status'] not in {'supported', 'not_supported'} or 'reason' in record:
        text(record.get('reason'), 'reason')
    matches = string_list(record['path_match'], 'path_match', nonempty=False)
    if len(matches) != len(set(matches)) or not set(matches) <= {path['id'] for path in forecast['paths']}:
        fail('path_match含重复或未冻结的路径')
    string_list(record['model_updates'], 'model_updates', nonempty=False)
    observed = record['observed']
    if not isinstance(observed, dict) or not {'value', 'event_time'} <= set(observed) or set(observed) - {'value', 'event_time', 'details', 'category'}:
        fail('observed须含value和event_time；未知时分别填null')
    if 'details' in observed:
        text(observed['details'], 'observed.details')
    if observed['value'] is not None:
        number(observed['value'], 'observed.value')
    categorical = forecast.get('validation_version', 1) >= 2 and bool(HIT_METRICS & set(forecast['calibration_plan']['metrics']))
    category = observed.get('category')
    if category is not None and (not categorical or category not in forecast['expression']['options']):
        fail('observed.category须取自预登记options')
    if (forecast['evidence_kind'] == 'live'
            and (new or validation_version >= 2)
            and (observed['value'] is not None or category is not None)
            and observed['event_time'] is None):
        fail('live结果带value或category时必须填写observed.event_time（事件发生或测量完成的时间）')
    if observed['event_time'] is not None:
        occurred = instant(observed['event_time'], 'observed.event_time')
        if occurred > resolved:
            fail('event_time不能晚于resolved_at')
        if forecast['evidence_kind'] == 'live' and occurred <= instant(forecast['registered_at'], 'registered_at'):
            fail('live结果不得在实际registered_at之前发生；不能倒填预测命中')
    if record['status'] in {'supported', 'not_supported'}:
        if categorical:
            if category is None:
                fail('类别命中指标的已判定结果须含observed.category')
            predicted = forecast['expression']['value'][0] if forecast['expression']['type'] == 'rank' else forecast['expression']['value']
            if (record['status'] == 'supported') != (category == predicted):
                fail('status与observed.category及冻结方向不一致')
        if forecast['expression']['type'] == 'probability' and (type(observed['value']) not in {int, float} or observed['value'] not in {0, 1}):
            fail('概率评分需要完整二元标签0或1，缺失标签不能填零')
        if forecast['expression']['type'] == 'interval':
            number(observed['value'], 'observed.value')
        if forecast['expression']['type'] == 'time_window':
            number(observed['value'], 'observed.value')
            forecast_scores.score(forecast['expression'], observed, forecast['window'], forecast['calibration_plan']['metrics'])


def score_expression(expr, observed, prediction_window, metrics, scoring_version=2, *, legacy_interval=False):
    if (expr['type'] == 'time_window'
            or (expr['type'] == 'interval' and not legacy_interval and scoring_version >= 2 and 'nominal_coverage' in expr)):
        return forecast_scores.score(expr, observed, prediction_window, metrics)
    scores, notes = {}, []
    for metric in metrics:
        if metric not in ({'brier', 'log_loss', 'interval_coverage', 'window_coverage'} | (HIT_METRICS if scoring_version >= 2 else set())):
            notes.append(f'尚未实现预登记指标{metric}，不伪造评分')
    kind, value = expr['type'], observed['value']
    if kind == 'probability':
        probability = expr['value']
        if 'brier' in metrics:
            scores['brier'] = (probability - value) ** 2
        if 'log_loss' in metrics:
            likelihood = probability if value == 1 else 1 - probability
            scores['log_loss'] = -math.log(likelihood) if likelihood else None
            scores['log_loss_infinite'] = likelihood == 0
    elif kind == 'interval':
        if 'interval_coverage' in metrics:
            scores['interval_coverage'] = int(expr['lower'] <= value <= expr['upper'])
    elif kind == 'direction' and scoring_version >= 2 and 'direction_hit' in metrics and expr.get('options'):
        scores['direction_hit'] = int(expr['value'] == observed['category'])
    elif kind == 'rank' and scoring_version >= 2 and 'rank_top_hit' in metrics and expr.get('options'):
        scores['rank_top_hit'] = int(expr['value'][0] == observed['category'])
    else:
        notes.append(f'{kind}未实现相应数值评分；保留结果语义，不换算概率或命中率')
    if scoring_version == 1 and observed['event_time'] is not None and 'window_coverage' in metrics:
        event = instant(observed['event_time'], 'event_time')
        start, end = window(prediction_window, 'prediction_window')
        scores['window_coverage'] = int(start <= event <= end)
    elif scoring_version >= 2 and 'window_coverage' in metrics:
        notes.append('window_coverage仅适用于time_window表达，不把共同评价窗当预测区间')
    return scores, notes


def computed_result(record, forecast):
    if record['status'] not in {'supported', 'not_supported'}:
        return {}, {}, ['未决、目标失效和无法评价不计为命中或失败；缺失标签不填零']
    metrics = forecast['calibration_plan']['metrics']
    scoring_version = record.get('scoring_version', 1)
    legacy_interval = forecast['expression']['type'] == 'interval' and forecast.get('validation_version', 1) < 2
    scores, notes = score_expression(forecast['expression'], record['observed'], forecast['window'], metrics,
                                    scoring_version, legacy_interval=legacy_interval)
    baseline_scores = {}
    for baseline in forecast['baselines']:
        baseline_scores[baseline['id']], _ = score_expression(baseline['expression'], record['observed'],
                                                             baseline.get('window', forecast['window']), metrics,
                                                             scoring_version, legacy_interval=legacy_interval)
    return scores, baseline_scores, notes


def load_registry(path):
    if not Path(path).exists():
        return {'format': FORMAT, 'schema_version': 1, 'forecasts': [], 'resolutions': []}
    registry = read_json(path)
    if not isinstance(registry, dict) or registry.get('format') != FORMAT or type(registry.get('schema_version')) is not int or registry['schema_version'] not in {1, 2} or not isinstance(registry.get('forecasts'), list) or not isinstance(registry.get('resolutions'), list):
        fail('目标不是可识别的前瞻注册表，不会覆盖')
    forecast_chain.validate(registry)
    forecasts, resolved_times = {}, {}
    for record in registry['forecasts']:
        validate_forecast(record)
        if record['id'] in forecasts:
            fail('前瞻id重复')
        if record.get('record_sha256') != digest(record):
            fail('冻结前瞻内容发生改变；保留原记录并另建版本')
        registered = instant(record.get('registered_at'), 'registered_at')
        if registered < instant(record['created_at'], 'created_at') or registered > utcnow():
            fail('registered_at时序无效')
        if record['evidence_kind'] == 'live' and registered >= instant(record['window']['end'], 'window.end'):
            fail('live登记晚于预测窗口')
        if (record['evidence_kind'] == 'live' and record.get('validation_version', 1) >= 2
                and instant(record['window']['start'], 'window.start') < registered):
            fail(f'live前瞻window.start不得早于实际registered_at={record["registered_at"]}；请把window.start设在该登记时间或之后')
        if record.get('supersedes') and record['supersedes'] not in forecasts:
            fail('supersedes未引用已存在的前瞻')
        validate_parent(record, forecasts)
        forecasts[record['id']] = record
    last_append = None
    for record in registry['resolutions']:
        if not isinstance(record, dict) or record.get('forecast_id') not in forecasts:
            fail('结果引用的前瞻不存在')
        allowed = RESOLUTION_FIELDS | {'reason', 'scores', 'baseline_scores', 'scoring_notes', 'scoring_version', 'validation_version', 'appended_at', 'record_sha256'}
        if set(record) - allowed:
            fail('结果记录含不支持的字段')
        forecast = forecasts[record['forecast_id']]
        if type(record.get('scoring_version', 1)) is not int or record.get('scoring_version', 1) not in {1, 2}:
            fail('不支持的scoring_version')
        validate_resolution(record, forecast)
        if record.get('record_sha256') != digest(record):
            fail('结果记录内容发生改变；应追加新回写')
        at = instant(record['resolved_at'], 'resolved_at')
        appended = instant(record.get('appended_at'), 'appended_at')
        if appended < at or appended < instant(forecast['registered_at'], 'registered_at') or appended > utcnow():
            fail('appended_at时序无效')
        if last_append is not None and appended < last_append:
            fail('追加时间不能在注册表中倒退')
        last_append = appended
        if record['forecast_id'] in resolved_times and at <= resolved_times[record['forecast_id']]:
            fail('结果重复或回写时间倒退')
        resolved_times[record['forecast_id']] = at
        scores, baselines, notes = computed_result(record, forecast)
        if (record.get('scores'), record.get('baseline_scores'), record.get('scoring_notes')) != (scores, baselines, notes):
            fail('结果分数与冻结表达、标签或评价指标不一致')
    return registry


def save_registry(path, registry, expected):
    require_external_output(path, __file__)
    require_external_output(Path(path).with_name(Path(path).name + '.lock'), __file__)
    path = Path(path).resolve()
    lock = path.with_name(path.name + '.lock')
    require_external_output(lock, __file__)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(registry, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    temporary, owns_lock = None, False
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.forecast-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise ForecastError('前瞻注册表存在其他写入者或遗留写锁；不自动移除锁') from error
        owns_lock = True
        os.close(descriptor)
        if (path.read_bytes() if path.exists() else None) != expected:
            fail('前瞻注册表已改变；重读后重新处理')
        if expected is None:
            try:
                os.link(temporary, path)
            except FileExistsError as error:
                raise ForecastError('首次提交时注册表已出现，本次未覆盖') from error
        else:
            os.replace(temporary, path)
            temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if owns_lock:
            lock.unlink(missing_ok=True)


def register_forecast(registry_path, record_path, *, include_chain_head=False):
    registry_path = Path(registry_path)
    require_external_output(registry_path, __file__)
    if registry_path.resolve() == Path(record_path).resolve():
        fail('输入记录不能与注册表是同一文件')
    expected = registry_path.read_bytes() if registry_path.exists() else None
    registry = load_registry(registry_path)
    record = read_json(record_path)
    validate_forecast(record, new=True)
    if {'registered_at', 'record_sha256', 'validation_version'} & set(record):
        fail('registered_at、record_sha256与validation_version由工具生成，不能自行填入')
    if record['theory_sha256'] != current_theory():
        fail('新登记的theory_sha256与当前manifest不一致')
    sections, _ = read_source.build_index(SOURCE.read_text(encoding='utf-8-sig').splitlines())
    for mechanism in record['mechanisms']:
        for anchor in mechanism['anchors']:
            if anchor not in sections:
                fail(f'原文锚点不存在：{anchor}')
    existing = {entry['id'] for entry in registry['forecasts']}
    if record['id'] in existing:
        fail('前瞻id已冻结；改目标、期限或范围必须用新id及supersedes')
    if 'supersedes' in record and record['supersedes'] not in existing:
        fail('supersedes所指旧前瞻不存在')
    validate_parent(record, {entry['id']: entry for entry in registry['forecasts']})
    record['registered_at'] = timestamp()
    record['validation_version'] = 2
    if (record['evidence_kind'] == 'live'
            and instant(record['window']['start'], 'window.start') < instant(record['registered_at'], 'registered_at')):
        fail(f'live前瞻window.start不得早于实际registered_at={record["registered_at"]}；请把window.start设在该登记时间或之后')
    record['record_sha256'] = digest(record)
    forecast_chain.upgrade(registry)
    registry['forecasts'].append(record)
    chain_head = forecast_chain.append_entry(registry, 'forecast', record)
    save_registry(registry_path, registry, expected)
    return {**record, 'chain_head': chain_head} if include_chain_head else record


def resolve_forecast(registry_path, record_path, *, include_chain_head=False):
    registry_path = Path(registry_path)
    require_external_output(registry_path, __file__)
    if registry_path.resolve() == Path(record_path).resolve():
        fail('结果记录不能与注册表是同一文件')
    expected = registry_path.read_bytes() if registry_path.exists() else None
    registry = load_registry(registry_path)
    record = read_json(record_path)
    if not isinstance(record, dict) or not RESOLUTION_FIELDS <= set(record) or set(record) - RESOLUTION_FIELDS - {'reason'}:
        fail('结果只接受规定字段及可选reason；scores、baseline_scores和追加时间由工具生成')
    forecast = next((item for item in registry['forecasts'] if item['id'] == record['forecast_id']), None)
    if forecast is None:
        fail('forecast_id不存在')
    validate_resolution(record, forecast, new=True)
    previous = [item for item in registry['resolutions'] if item['forecast_id'] == record['forecast_id']]
    if previous and instant(record['resolved_at'], 'resolved_at') <= instant(previous[-1]['resolved_at'], 'resolved_at'):
        fail('相同或更早的resolved_at不能重复追加')
    record['scoring_version'] = 1 if forecast.get('validation_version', 1) < 2 else 2
    record['validation_version'] = 2
    record['scores'], record['baseline_scores'], record['scoring_notes'] = computed_result(record, forecast)
    record['appended_at'] = timestamp()
    record['record_sha256'] = digest(record)
    forecast_chain.upgrade(registry)
    registry['resolutions'].append(record)
    chain_head = forecast_chain.append_entry(registry, 'resolution', record)
    save_registry(registry_path, registry, expected)
    return {**record, 'chain_head': chain_head} if include_chain_head else record


def mean_scores(values):
    result = {}
    for metric in ['brier', 'log_loss', 'interval_coverage', 'window_coverage', 'window_length_days',
                   'interval_width', 'interval_score', 'direction_hit', 'rank_top_hit']:
        numbers = [loss_value(entry, metric) for entry in values]
        numbers = [number for number in numbers if number is not None]
        if numbers:
            mean = arithmetic_mean(numbers)
            infinite = not math.isfinite(mean)
            result[metric] = {'n': len(numbers), 'mean': None if infinite else mean}
            if infinite or any(metric + '_infinite' in entry for entry in values):
                result[metric]['infinite'] = infinite
    return result


def loss_value(scores, metric):
    return math.inf if scores.get(metric + '_infinite') else scores.get(metric)


def baseline_methods(forecast):
    return {(baseline['id'], baseline['type']) for baseline in forecast['baselines']}


def evaluation_contract(record):
    start, end = window(record['window'], 'window')
    return {'target': record['target'], 'resolution_rule': record['resolution_rule'], 'scope': record['scope'],
            'unit': record['expression'].get('unit'), 'nominal_coverage': record['expression'].get('nominal_coverage'),
            'metrics': sorted(set(record['calibration_plan']['metrics'])),
            'window_seconds': (end - start).total_seconds(),
            'lead_seconds': (start - instant(record['input_cutoff'], 'input_cutoff')).total_seconds()}


def comparable_baselines(forecast):
    allowed = BASELINE_TYPES | (RECURSIVE_BASELINE_TYPES if forecast['order'] > 1 else set())
    counts = Counter(entry['type'] for entry in forecast['baselines'])
    return {entry['type']: entry['id'] for entry in forecast['baselines']
            if entry['type'] in allowed and counts[entry['type']] == 1}


def arithmetic_mean(values):
    if any(math.isinf(value) for value in values):
        return math.inf
    try:
        return math.fsum(value / len(values) for value in values)
    except OverflowError:
        return math.inf


def interval_ratio_summary(values):
    counts = Counter(finite_positive=0, both_zero=0, zero=0, infinite=0, undefined=0)
    log_ratios = []
    better = worse = tied = undetermined = 0
    for own, other in values:
        if math.isinf(own) and math.isinf(other):
            undetermined += 1
        elif own < other:
            better += 1
        elif own > other:
            worse += 1
        else:
            tied += 1
        if not math.isfinite(own) or not math.isfinite(other):
            counts['undefined'] += 1
        elif own == 0 and other == 0:
            counts['both_zero'] += 1
            log_ratios.append(0.0)
        elif own == 0:
            counts['zero'] += 1
        elif other == 0:
            counts['infinite'] += 1
        else:
            counts['finite_positive'] += 1
            log_ratios.append(math.log(own) - math.log(other))
    ratio, mean_log = None, None
    if counts['undefined'] or (counts['zero'] and counts['infinite']):
        status = 'undefined'
    elif counts['infinite']:
        status = 'infinite'
    elif counts['zero']:
        status, ratio = 'zero', 0.0
    else:
        mean_log = arithmetic_mean(log_ratios)
        try:
            ratio = math.exp(mean_log)
        except OverflowError:
            status = 'overflow'
        else:
            status = 'finite' if ratio else 'underflow'
            if not ratio:
                ratio = None
    return {'n': len(values), 'geometric_mean_ratio': ratio, 'ratio_status': status,
            'mean_log_ratio': mean_log, 'ratio_counts': dict(counts),
            'ratio_definition': 'model_interval_score / baseline_interval_score',
            'both_zero_convention': 'Both scores zero use ratio 1 as a neutral pair.',
            'better': better, 'worse': worse, 'tied': tied, 'undetermined': undetermined}


def paired_metric_summary(rows, metric):
    if metric not in LOSS_METRICS | HIT_METRICS:
        return None
    values = [(loss_value(own, metric), loss_value(other, metric)) for own, other in rows]
    values = [(a, b) for a, b in values if a is not None and b is not None]
    if not values:
        return None
    if metric == 'interval_score':
        return interval_ratio_summary(values)
    lower_better = metric in LOSS_METRICS
    better = sum((a < b if lower_better else a > b) for a, b in values)
    worse = sum((a > b if lower_better else a < b) for a, b in values)
    own, other = arithmetic_mean([a for a, _ in values]), arithmetic_mean([b for _, b in values])
    differences = [a - b for a, b in values]
    finite_difference = all(math.isfinite(value) for value in differences)
    return {'n': len(values), 'model_mean': own if math.isfinite(own) else None,
            'baseline_mean': other if math.isfinite(other) else None,
            'model_infinite': math.isinf(own), 'baseline_infinite': math.isinf(other),
            'mean_difference': arithmetic_mean(differences) if finite_difference else None,
            'difference_definition': 'model_minus_baseline', 'nonfinite_difference_pairs': sum(not math.isfinite(d) for d in differences),
            'better': better, 'worse': worse, 'tied': len(values) - better - worse}


def add_calibration(group, pairs):
    binary = [(forecast['expression']['value'], result['observed']['value']) for forecast, result in pairs
              if forecast['expression']['type'] == 'probability' and result['status'] in {'supported', 'not_supported'}]
    if not binary:
        return
    bins = defaultdict(list)
    for probability, label in binary:
        bins[min(int(probability * 10), 9)].append((probability, label))
    prevalence = sum(label for _, label in binary) / len(binary)
    group['calibration_bins'] = [{'lower': index / 10, 'upper': (index + 1) / 10, 'n': len(rows),
                                  'mean_probability': sum(p for p, _ in rows) / len(rows),
                                  'observed_frequency': sum(y for _, y in rows) / len(rows)}
                                 for index, rows in sorted(bins.items())]
    group['resolution'] = sum(len(rows) * (sum(y for _, y in rows) / len(rows) - prevalence) ** 2
                              for rows in bins.values()) / len(binary)


def add_interval_calibration(group, pairs):
    model_bins, baseline_bins = defaultdict(list), defaultdict(lambda: defaultdict(list))
    for forecast, result in pairs:
        kind = forecast['expression']['type']
        if kind not in {'interval', 'time_window'}:
            continue
        metric = 'interval_coverage' if kind == 'interval' else 'window_coverage'
        nominal = forecast['expression'].get('nominal_coverage')
        if type(nominal) in {int, float} and 0 < nominal < 1 and metric in result['scores']:
            model_bins[nominal].append(result['scores'][metric])
        methods = comparable_baselines(forecast)
        for baseline in forecast['baselines']:
            nominal = baseline['expression'].get('nominal_coverage')
            scores = result['baseline_scores'].get(baseline['id'], {})
            if baseline['type'] in methods and type(nominal) in {int, float} and 0 < nominal < 1 and metric in scores:
                baseline_bins[baseline['type']][nominal].append(scores[metric])
    if not model_bins and not baseline_bins:
        return

    def rows(bins):
        return [{'nominal_coverage': nominal, 'n': len(values), 'observed_coverage': arithmetic_mean(values)}
                for nominal, values in sorted(bins.items())]

    group['interval_calibration'] = {
        'purpose': 'calibration_only', 'model': rows(model_bins),
        'baselines': [{'baseline_type': method, 'bins': rows(bins)} for method, bins in sorted(baseline_bins.items())],
    }


def paired_score_views(forecast, result, baseline_id):
    own = dict(result['scores'])
    other = dict(result['baseline_scores'][baseline_id])
    baseline = next(item for item in forecast['baselines'] if item['id'] == baseline_id)
    nominal = forecast['expression'].get('nominal_coverage')
    baseline_nominal = baseline['expression'].get('nominal_coverage')
    incomparable = []
    if ('interval_score' in own or 'interval_score' in other) and (nominal is None or nominal != baseline_nominal):
        incomparable.append('interval_score')
        for scores in (own, other):
            scores.pop('interval_score', None)
            scores.pop('interval_score_infinite', None)
    return own, other, incomparable


def pooled_groups(registry, latest):
    grouped = defaultdict(list)
    names = ['order', 'evidence_kind', 'expression_type', 'theory_sha256', 'skill_version', 'host_model']
    for record in registry['forecasts']:
        if record['id'] not in latest:
            continue
        key = (record['order'], record['evidence_kind'], record['expression']['type'], record['theory_sha256'],
               record['skill_version'], record['host_model'], canonical(record['calibration_plan'].get('degradation_policy')))
        grouped[key].append((record, latest[record['id']]))
    result = []
    for key, pairs in sorted(grouped.items()):
        group = dict(zip(names, key[:6]))
        group.update(resolved=len(pairs), metrics=mean_scores([outcome['scores'] for _, outcome in pairs]),
                     degradation_policy=pairs[0][0]['calibration_plan'].get('degradation_policy'), _pairs=pairs)
        if group['expression_type'] == 'interval':
            for metric in ('interval_score', 'interval_width', 'interval_coverage'):
                group['metrics'].pop(metric, None)
        methods = set().union(*(comparable_baselines(forecast) for forecast, _ in pairs))
        group['excluded_baseline_types'] = sorted({baseline['type'] for forecast, _ in pairs for baseline in forecast['baselines']
                                                   if baseline['type'] not in comparable_baselines(forecast)})
        comparisons = []
        for method in sorted(methods):
            views = [paired_score_views(forecast, outcome, comparable_baselines(forecast)[method])
                    for forecast, outcome in pairs if method in comparable_baselines(forecast)
                    and comparable_baselines(forecast)[method] in outcome['baseline_scores']]
            rows = [(own, other) for own, other, _ in views]
            metrics = {}
            for metric in ['brier', 'log_loss', 'interval_score', 'direction_hit', 'rank_top_hit']:
                value = paired_metric_summary(rows, metric)
                if value is not None:
                    metrics[metric] = value
            comparisons.append({'baseline_type': method, 'paired_records': len(rows), 'metrics': metrics,
                                'incomparable_metrics': sorted({metric for _, _, excluded in views for metric in excluded})})
        group['baseline_comparisons'] = comparisons
        add_calibration(group, pairs)
        add_interval_calibration(group, pairs)
        result.append(group)
    return result


def parent_path_match(record, latest):
    if 'parent' not in record:
        return 'unknown_legacy'
    parent = record['parent']
    outcome = latest.get(parent['forecast_id'])
    if outcome is None or outcome['status'] not in {'supported', 'not_supported'}:
        return 'unresolved'
    return 'matched' if parent['path_id'] in outcome['path_match'] else 'not_matched'


def pooled_parent_groups(registry, latest):
    subsets = defaultdict(list)
    for record in registry['forecasts']:
        if record['order'] > 1:
            subsets[parent_path_match(record, latest)].append(record)
    result = []
    for match, forecasts in sorted(subsets.items()):
        for group in pooled_groups({'forecasts': forecasts}, latest):
            pairs = group.pop('_pairs')
            group['parent_match'] = match
            group['forecast_ids'] = sorted(record['id'] for record, _ in pairs)
            result.append(group)
    return result


def degradation(groups):
    decisions = []
    for group in groups:
        pairs = group.pop('_pairs')
        policy = group['degradation_policy']
        if policy is None or group['evidence_kind'] not in {'live', 'backtest'}:
            continue
        methods = set().union(*(comparable_baselines(forecast) for forecast, _ in pairs))
        for method in sorted(methods):
            periods = defaultdict(list)
            for forecast, result in pairs:
                mapping = comparable_baselines(forecast)
                if method not in mapping or result['status'] not in {'supported', 'not_supported'}:
                    continue
                own = loss_value(result['scores'], policy['metric'])
                baseline = loss_value(result['baseline_scores'][mapping[method]], policy['metric'])
                if own is None or baseline is None:
                    continue
                at = instant(result['resolved_at'], 'resolved_at')
                periods[at.year * 12 + at.month].append((own, baseline))
            consecutive, previous = 0, None
            for month, rows in sorted(periods.items()):
                underperforming = (len(rows) >= policy['minimum_per_period'] and
                                   arithmetic_mean([a for a, _ in rows]) >= arithmetic_mean([b for _, b in rows]))
                consecutive = (consecutive + 1 if previous == month - 1 else 1) if underperforming else 0
                previous = month
                if consecutive >= policy['consecutive_months']:
                    decisions.append({key: group[key] for key in ['order', 'skill_version', 'host_model', 'theory_sha256',
                                                                  'expression_type', 'evidence_kind']} |
                                     {'capability': 'scenario_only', 'basis': '16.22', 'baseline_type': method,
                                      'policy': policy, 'reason': '同一汇总组及基线类型在预登记的连续月份内未优于简单基线；仅相应前瞻能力声明降级。'})
                    break
    return decisions


def status_revisions(registry):
    histories = defaultdict(list)
    for result in registry['resolutions']:
        states = histories[result['forecast_id']]
        if not states or states[-1]['status'] != result['status']:
            states.append({'status': result['status'], 'resolved_at': result['resolved_at']})
    changed = {identifier: histories[identifier] for identifier in sorted(histories)
               if len(histories[identifier]) > 1}
    return {'count': len(changed), 'forecast_ids': list(changed), 'state_history': changed}


def report_registry(registry):
    latest = {result['forecast_id']: result for result in registry['resolutions']}
    orders, grouped = {}, defaultdict(list)
    for order in [1, 2, 3]:
        records = [record for record in registry['forecasts'] if record['order'] == order]
        outcomes = [latest[record['id']] for record in records if record['id'] in latest]
        counts = Counter(result['status'] for result in outcomes)
        ids = {record['id'] for record in records}
        orders[str(order)] = {'registered': len(records), 'resolved': len(outcomes), 'unresolved': len(records) - len(outcomes),
                              'resolution_records': sum(result['forecast_id'] in ids for result in registry['resolutions']),
                              'statuses': {status: counts[status] for status in sorted(STATUSES)}}
    for record in registry['forecasts']:
        if record['id'] in latest:
            key = (record['order'], record['theory_sha256'], record['skill_version'], record['host_model'], record['evidence_kind'], record['expression']['type'],
                   canonical(evaluation_contract(record)))
            grouped[key].append((record, latest[record['id']]))
    groups = []
    for key, pairs in sorted(grouped.items()):
        group = dict(zip(['order', 'theory_sha256', 'skill_version', 'host_model', 'evidence_kind', 'expression_type'], key))
        group['evaluation_contract'] = evaluation_contract(pairs[0][0])
        group.update({'resolved': len(pairs), 'metrics': mean_scores([result['scores'] for _, result in pairs]), '_pairs': pairs})
        comparisons = []
        for baseline_id, baseline_type in sorted(set.union(*(baseline_methods(forecast) for forecast, _ in pairs))):
            eligible = [(forecast, result) for forecast, result in pairs
                        if (baseline_id, baseline_type) in baseline_methods(forecast) and baseline_id in result['baseline_scores']]
            views = [paired_score_views(forecast, result, baseline_id) for forecast, result in eligible]
            own = mean_scores([scores for scores, _, _ in views])
            other = mean_scores([scores for _, scores, _ in views])
            gains = {}
            for metric in own.keys() & other.keys():
                if metric not in LOSS_METRICS | HIT_METRICS:
                    continue
                model_mean, baseline_mean = own[metric]['mean'], other[metric]['mean']
                gain = (baseline_mean - model_mean if metric in LOSS_METRICS else model_mean - baseline_mean) if model_mean is not None and baseline_mean is not None else None
                gains[metric] = gain if gain is not None and math.isfinite(gain) else None
            comparisons.append({'baseline_id': baseline_id, 'baseline_type': baseline_type, 'paired_records': len(eligible), 'model': own, 'baseline': other, 'gain': gains,
                                'incomparable_metrics': sorted({metric for _, _, excluded in views for metric in excluded})})
        group['baseline_comparisons'] = comparisons
        binary = [(forecast['expression']['value'], result['observed']['value']) for forecast, result in pairs
                  if forecast['expression']['type'] == 'probability' and result['status'] in {'supported', 'not_supported'}]
        if binary:
            bins = defaultdict(list)
            for probability, label in binary:
                bins[min(int(probability * 10), 9)].append((probability, label))
            prevalence = sum(label for _, label in binary) / len(binary)
            group['calibration_bins'] = [{'lower': index / 10, 'upper': (index + 1) / 10, 'n': len(rows),
                                          'mean_probability': sum(p for p, _ in rows) / len(rows), 'observed_frequency': sum(y for _, y in rows) / len(rows)}
                                         for index, rows in sorted(bins.items())]
            group['resolution'] = sum(len(rows) * (sum(y for _, y in rows) / len(rows) - prevalence) ** 2 for rows in bins.values()) / len(binary)
        groups.append(group)
    for group in groups:
        group.pop('_pairs')
    pooled = pooled_groups(registry, latest)
    decisions = degradation(pooled)
    disagreement = forecast_scores.disagreement_summary(registry['forecasts'], comparable_baselines)
    disagreement_ids = set(disagreement['forecast_ids'])
    disagreement_groups = pooled_groups(
        {'forecasts': [record for record in registry['forecasts'] if record['id'] in disagreement_ids]}, latest)
    for group in disagreement_groups:
        group['forecast_ids'] = sorted(record['id'] for record, _ in group.pop('_pairs'))
    policies = [record['calibration_plan'].get('degradation_policy') for record in registry['forecasts']]
    threshold_status = 'pending' if not any(policies) else 'preregistered' if all(policies) else 'partial'
    return {'format': FORMAT, 'orders': orders, 'by_contract': groups, 'groups': groups, 'pooled': pooled, 'capability': 'scenario_only' if decisions else 'unverified',
            'disagreement': disagreement, 'pooled_on_disagreement': disagreement_groups,
            'pooled_by_parent_match': pooled_parent_groups(registry, latest),
            'capability_scope': 'matching_degradation_decisions_only',
            'status_revisions': status_revisions(registry),
            'capability_evidence_records': sum(record['evidence_kind'] in {'live', 'backtest'} and record['id'] in latest
                                               and latest[record['id']]['status'] in {'supported', 'not_supported'} for record in registry['forecasts']),
            'degradation_threshold': threshold_status, 'degradation_decisions': decisions,
            'scope': '仅统计已登记结果；教学和合成记录不作经验支持。回测隔离、来源真实性、样本外增益与持续能力须外部复核；无自动认证或总命中率。',
            'limitations': ['未预登记的排序和方向不自动评分；区间覆盖只用于校准，不衡量优于基线的增益。', '校准分箱与分辨率是描述统计，单例不证明长期校准。',
                            '分配误差、因果响应效果和外部评测未在本工具中自动识别。', '未预登记持续退化阈值时保留pending，不自行设定合入阈值。']}


def check_registry(registry, expect_head=None):
    current = current_theory()
    chain_head = forecast_chain.validate(registry, expect_head)
    warnings = []
    for record in registry['forecasts']:
        if record['theory_sha256'] != current:
            warnings.append(f'{record["id"]}: 绑定旧理论版本，保留历史登记，不改写为当前版本')
    return {'ok': True, 'forecasts': len(registry['forecasts']), 'resolution_records': len(registry['resolutions']),
            'schema_version': registry['schema_version'], 'chain_head': chain_head, 'legacy_prefix': registry.get('legacy_prefix'),
            'capability': 'unverified',
            'errors': [], 'warnings': warnings,
            'scope': '结构、引用身份和冻结内容检查；不认证来源、事前知识状态、判定正确性或预测能力。'}


def main():
    for stream in [sys.stdout, sys.stderr]:
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', required=True, type=Path, help='安装目录以外的前瞻注册表')
    commands = parser.add_subparsers(dest='command', required=True)
    for command in ['register', 'resolve']:
        commands.add_parser(command).add_argument('--record', required=True, type=Path)
    for command in ['list', 'report']:
        commands.add_parser(command)
    commands.add_parser('check').add_argument('--expect-head', help='注册表外保存的SHA-256链头')
    commands.add_parser('show').add_argument('id')
    args = parser.parse_args()
    try:
        if args.command == 'register':
            result = register_forecast(args.registry, args.record, include_chain_head=True)
        elif args.command == 'resolve':
            result = resolve_forecast(args.registry, args.record, include_chain_head=True)
        else:
            if not args.registry.exists():
                fail('注册表不存在')
            registry = load_registry(args.registry)
            if args.command == 'list':
                resolved = {item['forecast_id']: item['status'] for item in registry['resolutions']}
                result = [{key: record[key] for key in ['id', 'order', 'target', 'window', 'evidence_kind']} | {'status': resolved.get(record['id'], 'pending')}
                          for record in registry['forecasts']]
            elif args.command == 'show':
                forecast = next((record for record in registry['forecasts'] if record['id'] == args.id), None)
                if forecast is None:
                    fail('前瞻id不存在')
                result = {'forecast': forecast, 'resolutions': [record for record in registry['resolutions'] if record['forecast_id'] == args.id]}
            elif args.command == 'report':
                result = report_registry(registry)
            else:
                result = check_registry(registry, args.expect_head)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as error:
        print(f'前瞻注册表处理失败：{error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
