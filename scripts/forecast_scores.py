"""Expression validation, comparison and interval scoring used by forecast.py."""

from __future__ import annotations

from datetime import datetime, timezone
from collections import defaultdict
import json
import math


def _text(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 16000:
        raise ValueError(f'{name}须为非空文本，不超过16000字符')
    return value


def _number(value, name):
    try:
        finite = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError(f'{name}须为有限数值，不能是布尔值或字符串')
    return value


def _instant(value, name):
    _text(value, name)
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError(f'{name}须声明时区')
        return result.astimezone(timezone.utc)
    except (ValueError, OverflowError) as error:
        raise ValueError(f'{name}须为有效且带时区的ISO8601时间') from error


def _window(value, name):
    if not isinstance(value, dict) or set(value) != {'start', 'end'}:
        raise ValueError(f'{name}须含start和end')
    start = _instant(value['start'], name + '.start')
    end = _instant(value['end'], name + '.end')
    if start >= end:
        raise ValueError(f'{name}.start必须早于end')
    return start, end


def _nominal(expr, required=False):
    if 'nominal_coverage' not in expr:
        if required:
            raise ValueError('expression.nominal_coverage必须登记')
        return None
    nominal = _number(expr['nominal_coverage'], 'expression.nominal_coverage')
    if not 0 < nominal < 1:
        raise ValueError('expression.nominal_coverage须大于0且小于1')
    return nominal


def validate_expression(expr, evaluation_window, *, require_nominal=False):
    """Validate an expression without modifying its frozen values."""
    if not isinstance(expr, dict) or expr.get('type') not in ('time_window', 'interval'):
        raise ValueError('forecast_scores只接受time_window或interval表达')
    _text(expr.get('basis'), 'expression.basis')
    evaluation_start, evaluation_end = _window(evaluation_window, 'window')
    if expr['type'] == 'interval':
        lower = _number(expr.get('lower'), 'expression.lower')
        upper = _number(expr.get('upper'), 'expression.upper')
        if lower > upper:
            raise ValueError('expression区间上下界倒置')
        _text(expr.get('unit'), 'expression.unit')
        if expr.get('quantity', 'numeric') != 'numeric':
            raise ValueError('interval只支持数值目标区间')
        _nominal(expr, required=require_nominal)
        return
    start, end = _window({'start': expr.get('start'), 'end': expr.get('end')}, 'expression')
    if start < evaluation_start or end > evaluation_end:
        raise ValueError('expression预测时间区间须在评价窗内')
    _nominal(expr)


def _interval_score(lower, upper, value, nominal):
    try:
        result = upper - lower
        if value < lower:
            result += 2 * (lower - value) / (1 - nominal)
        elif value > upper:
            result += 2 * (value - upper) / (1 - nominal)
        return result
    except OverflowError:
        return math.inf


def _store_finite(scores, metric, value):
    try:
        infinite = not math.isfinite(value)
    except OverflowError:
        infinite = True
    scores[metric] = None if infinite else value
    scores[metric + '_infinite'] = infinite


def _numeric_interval_score(expr, observed, metrics):
    notes = [f'interval不支持预登记指标{metric}，不伪造评分'
             for metric in metrics if metric not in {'interval_coverage', 'interval_score'}]
    scores = {}
    lower, upper = expr['lower'], expr['upper']
    _store_finite(scores, 'interval_width', upper - lower)
    value = observed.get('value')
    if value is None:
        notes.append('数值结果未知，不将缺失标签计为零或覆盖失败')
        return scores, notes
    _number(value, 'observed.value')
    if 'interval_coverage' in metrics:
        scores['interval_coverage'] = int(lower <= value <= upper)
    if 'interval_score' in metrics:
        _store_finite(scores, 'interval_score', _interval_score(lower, upper, value, expr['nominal_coverage']))
    return scores, notes


def score(expr, observed, window, metrics):
    """Return registered scores and explanatory notes for forecast.py."""
    validate_expression(expr, window, require_nominal=True)
    if not isinstance(observed, dict):
        raise ValueError('observed须为对象')
    if not isinstance(metrics, (list, tuple, set)) or any(not isinstance(item, str) for item in metrics):
        raise ValueError('metrics须为指标名称集合')
    if expr['type'] == 'interval':
        return _numeric_interval_score(expr, observed, metrics)
    notes = [f'time_window不支持预登记指标{metric}，不伪造评分'
             for metric in metrics if metric not in {'window_coverage', 'interval_score'}]
    start = _instant(expr['start'], 'expression.start')
    end = _instant(expr['end'], 'expression.end')
    length = (end - start).total_seconds() / 86400
    scores = {'window_length_days': length}
    value, event_time = observed.get('value'), observed.get('event_time')
    if value is None:
        if event_time is not None:
            raise ValueError('time_window提供event_time时observed.value须为1')
        notes.append('事件是否发生未知，不将缺失标签计为未发生或覆盖失败')
        return scores, notes
    _number(value, 'observed.value')
    if value not in {0, 1}:
        raise ValueError('time_window的observed.value须为0或1')
    if value == 0:
        if event_time is not None:
            measured_at = _instant(event_time, 'observed.event_time')
            _, evaluation_end = _window(window, 'window')
            if measured_at < evaluation_end:
                raise ValueError('time_window的未发生标签须在评价窗结束后或终点完成测量')
        if 'window_coverage' in metrics:
            scores['window_coverage'] = 0
        if 'interval_score' in metrics:
            notes.append('评价窗内事件未发生，不虚构事件时间计算interval_score')
        return scores, notes
    if event_time is None:
        raise ValueError('time_window的已发生标签须提供observed.event_time')
    event = _instant(event_time, 'observed.event_time')
    evaluation_start, evaluation_end = _window(window, 'window')
    if not evaluation_start <= event <= evaluation_end:
        raise ValueError('observed.event_time须在评价窗内')
    if 'window_coverage' in metrics:
        scores['window_coverage'] = int(start <= event <= end)
    if 'interval_score' in metrics:
        nominal = _nominal(expr)
        if nominal is None:
            notes.append('未登记nominal_coverage，不计算interval_score')
        else:
            offset = (event - start).total_seconds() / 86400
            _store_finite(scores, 'interval_score', _interval_score(0, length, offset, nominal))
    return scores, notes


def prediction_signature(expr):
    """Separate the comparable prediction domain from its frozen forecast value."""
    kind = expr.get('type')
    if kind == 'probability':
        value = _number(expr.get('value'), 'expression.value')
        if not 0 <= value <= 1:
            raise ValueError('概率表达须在0与1之间')
        return (kind,), value
    if kind in {'direction', 'rank'}:
        options = expr.get('options')
        if (not isinstance(options, list) or len(options) < 2
                or any(not isinstance(item, str) or not item.strip() for item in options)
                or len(set(options)) != len(options)):
            raise ValueError('类别或排序缺少可比较的互斥options')
        values = expr.get('value')
        if kind == 'direction':
            values = [values]
        if (not isinstance(values, list) or not values
                or any(not isinstance(item, str) or item not in options for item in values)
                or len(set(values)) != len(values)):
            raise ValueError('预测值不属于登记的类别空间')
        return (kind, tuple(sorted(options))), tuple(values)
    if kind == 'interval':
        nominal = _nominal(expr, required=True)
        unit = _text(expr.get('unit'), 'expression.unit')
        lower = _number(expr.get('lower'), 'expression.lower')
        upper = _number(expr.get('upper'), 'expression.upper')
        if lower > upper or expr.get('quantity', 'numeric') != 'numeric':
            raise ValueError('数值区间不可比较')
        return (kind, unit, nominal), (lower, upper)
    if kind == 'time_window':
        start, end = _window({'start': expr.get('start'), 'end': expr.get('end')}, 'expression')
        return (kind, _nominal(expr)), (start, end)
    raise ValueError('未知或未提供可比较的预测表达')


def prediction_disagreement(record, baseline_selector):
    """Return None with a reason unless every registered baseline is comparable."""
    baselines = record.get('baselines', [])
    if not baselines:
        return None, '未登记基线'
    comparable = baseline_selector(record)
    if len(comparable) != len(baselines):
        return None, '存在未知或重复的基线类型，无法与全部基线比较'
    try:
        domain, value = prediction_signature(record['expression'])
        signatures = [prediction_signature(baseline['expression']) for baseline in baselines]
    except (ValueError, TypeError, KeyError) as error:
        return None, str(error)
    if any(other_domain != domain for other_domain, _ in signatures):
        return None, '模型与基线的表达类型、类别空间、单位或名义覆盖率不一致'
    return all(other_value != value for _, other_value in signatures), None


def disagreement_summary(records, baseline_selector):
    """Describe registered disagreement independently of whether outcomes exist."""
    rows, grouped = [], defaultdict(list)
    names = ('order', 'evidence_kind', 'expression_type', 'theory_sha256', 'skill_version', 'host_model')
    for record in records:
        different, reason = prediction_disagreement(record, baseline_selector)
        row = (record['id'], different, reason)
        rows.append(row)
        policy = record['calibration_plan'].get('degradation_policy')
        key = (record['order'], record['evidence_kind'], record['expression']['type'], record['theory_sha256'],
               record['skill_version'], record['host_model'], json.dumps(policy, sort_keys=True))
        grouped[key].append(row)

    def summarize(items):
        eligible = sum(different is not None for _, different, _ in items)
        ids = sorted(identifier for identifier, different, _ in items if different is True)
        excluded = sorted(({'forecast_id': identifier, 'reason': reason}
                           for identifier, different, reason in items if different is None),
                          key=lambda row: row['forecast_id'])
        return {'registered': len(items), 'eligible_records': eligible, 'disagreement_records': len(ids),
                'rate': len(ids) / eligible if eligible else None, 'forecast_ids': ids,
                'excluded_records': len(excluded), 'excluded': excluded}

    summary = summarize(rows)
    summary['definition'] = 'model_prediction_differs_from_every_registered_comparable_baseline'
    summary['by_group'] = [dict(zip(names, key[:6]), degradation_policy=json.loads(key[6]), **summarize(items))
                           for key, items in sorted(grouped.items())]
    return summary
