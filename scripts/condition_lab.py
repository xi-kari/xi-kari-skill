#!/usr/bin/env python3
"""Evaluate an explicit, bounded model and export offline scenario comparisons."""

from __future__ import annotations

import argparse
import ast
import base64
import csv
from dataclasses import dataclass
import hashlib
import html
import io
import itertools
import json
import keyword
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


TOOL = "xikari-condition-lab-1"
MAX_CASES = 512
MAX_ITEMS = 64
MAX_NUMBER = 1e100
IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,63}\Z")
FUNCTIONS = {"min", "max", "abs"}
OUTPUTS = {"json": "condition-results.json", "csv": "condition-results.csv", "html": "condition-results.html"}
CSV_FIELDS = ["format", "case_id", "scenario", "explore", "plan", "case_state", "kind", "id", "label", "value", "state", "unit", "formula", "basis", "role", "source", "note"]


class ModelError(Exception):
    pass


@dataclass(frozen=True)
class Value:
    state: str
    value: object = None
    reason: str = ""

    def as_dict(self):
        return {"state": self.state, "value": self.value, "reason": self.reason}


def number(value):
    return type(value) in {int, float}


def validate_scalar(value, where):
    if value is None or type(value) is bool:
        return
    if not number(value) or abs(value) > MAX_NUMBER or not math.isfinite(value):
        raise ModelError(f"{where}须为有限数字、布尔或null；数字绝对值不超过1e100。")


def known(value):
    if number(value) and (abs(value) > MAX_NUMBER or not math.isfinite(value)):
        return Value("error", reason="结果超出有限数值范围。")
    return Value("known", value)


def text_field(item, field, where, required=False):
    value = item.get(field, "")
    if not isinstance(value, str) or len(value) > 8000 or (required and not value.strip()):
        raise ModelError(f"{where}.{field}须为{'非空' if required else ''}文本，不超过8000字符。")
    return value


def named(value, where):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value) or value in FUNCTIONS or keyword.iskeyword(value):
        raise ModelError(f"{where}须为英文字母开头的字母、数字、下划线名称，且不能是min/max/abs。")
    return value


def item_list(model, field, limit=MAX_ITEMS):
    value = model.get(field, [])
    if not isinstance(value, list) or len(value) > limit or any(not isinstance(v, dict) for v in value):
        raise ModelError(f"{field}须为对象列表，最多{limit}项。")
    return value


class Formula:
    ALLOWED = (ast.Expression, ast.Constant, ast.Name, ast.Load, ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
               ast.Call, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.UAdd, ast.USub,
               ast.Not, ast.And, ast.Or, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)

    def __init__(self, expression, available):
        if not isinstance(expression, str) or not expression.strip() or len(expression) > 2000:
            raise ModelError("公式须为非空字符串，最多2000字符。")
        self.expression = expression
        try:
            self.tree = ast.parse(expression, mode="eval")
        except (SyntaxError, RecursionError) as exc:
            raise ModelError(f"公式语法错误: {expression}") from exc
        nodes = list(ast.walk(self.tree))
        if len(nodes) > 160:
            raise ModelError("公式过于复杂，AST节点不得超过160。")
        for node in nodes:
            if not isinstance(node, self.ALLOWED):
                raise ModelError(f"公式不允许 {type(node).__name__}: {expression}")
            if isinstance(node, ast.Name) and node.id not in available | FUNCTIONS:
                raise ModelError(f"公式引用未知或尚未定义的变量 {node.id}: {expression}")
            if isinstance(node, ast.Constant):
                validate_scalar(node.value, "公式常量")
            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS or node.keywords:
                    raise ModelError("公式只允许min/max/abs的位置参数调用。")
                if not 1 <= len(node.args) <= 16 or (node.func.id == "abs" and len(node.args) != 1):
                    raise ModelError("min/max须有1—16个数值参数，abs须有1个。")

    def evaluate(self, environment):
        def failure(values):
            for state in ("error", "unknown"):
                for value in values:
                    if value.state == state:
                        return value
            return None

        def evaluate(node):
            if isinstance(node, ast.Expression):
                return evaluate(node.body)
            if isinstance(node, ast.Constant):
                return Value("unknown", reason="公式含null/None未知常量。") if node.value is None else known(node.value)
            if isinstance(node, ast.Name):
                return environment.get(node.id, Value("error", reason=f"{node.id}不是数值变量。"))
            if isinstance(node, ast.UnaryOp):
                value = evaluate(node.operand)
                if value.state != "known":
                    return value
                if isinstance(node.op, ast.Not):
                    return known(not value.value) if type(value.value) is bool else Value("error", reason="not只接受布尔量。")
                if not number(value.value):
                    return Value("error", reason="正负号只接受数字。")
                return known(value.value if isinstance(node.op, ast.UAdd) else -value.value)
            if isinstance(node, ast.BoolOp):
                values = [evaluate(child) for child in node.values]
                invalid = next((v for v in values if v.state == "error" or (v.state == "known" and type(v.value) is not bool)), None)
                if invalid:
                    return invalid if invalid.state == "error" else Value("error", reason="and/or只接受布尔量。")
                decisive = False if isinstance(node.op, ast.And) else True
                if any(v.state == "known" and v.value is decisive for v in values):
                    return known(decisive)
                absent = failure(values)
                return absent or known(not decisive)
            if isinstance(node, ast.BinOp):
                values = [evaluate(node.left), evaluate(node.right)]
                if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)) and values[1].state == "known" and number(values[1].value) and values[1].value == 0:
                    return Value("error", reason="不可计算: ZeroDivisionError")
                absent = failure(values)
                if absent:
                    return absent
                left, right = (v.value for v in values)
                if not number(left) or not number(right):
                    return Value("error", reason="算术只接受数字，布尔量不作0/1处理。")
                try:
                    if isinstance(node.op, ast.Add): result = left + right
                    elif isinstance(node.op, ast.Sub): result = left - right
                    elif isinstance(node.op, ast.Mult): result = left * right
                    elif isinstance(node.op, ast.Div): result = left / right
                    elif isinstance(node.op, ast.FloorDiv): result = left // right
                    elif isinstance(node.op, ast.Mod): result = left % right
                    elif isinstance(node.op, ast.Pow):
                        if abs(right) > 12:
                            return Value("error", reason="幂指数绝对值上限为12。")
                        result = left ** right
                    else: return Value("error", reason="不支持的运算。")
                    if not number(result):
                        return Value("error", reason="结果不是实数。")
                    return known(result)
                except (ZeroDivisionError, OverflowError, ValueError) as exc:
                    return Value("error", reason=f"不可计算: {type(exc).__name__}")
            if isinstance(node, ast.Compare):
                values = [evaluate(node.left)] + [evaluate(child) for child in node.comparators]
                absent = failure(values)
                if absent:
                    return absent
                answers = []
                for left_value, op, right_value in zip(values, node.ops, values[1:]):
                    left, right = left_value.value, right_value.value
                    valid = number(left) and number(right)
                    valid |= type(left) is bool and type(right) is bool and isinstance(op, (ast.Eq, ast.NotEq))
                    if not valid:
                        return Value("error", reason="比较需要同类数字；布尔量仅可作==或!=比较。")
                    if isinstance(op, ast.Eq): answers.append(left == right)
                    elif isinstance(op, ast.NotEq): answers.append(left != right)
                    elif isinstance(op, ast.Lt): answers.append(left < right)
                    elif isinstance(op, ast.LtE): answers.append(left <= right)
                    elif isinstance(op, ast.Gt): answers.append(left > right)
                    elif isinstance(op, ast.GtE): answers.append(left >= right)
                return known(all(answers))
            if isinstance(node, ast.Call):
                values = [evaluate(child) for child in node.args]
                absent = failure(values)
                if absent:
                    return absent
                numbers = [value.value for value in values]
                if not all(number(v) for v in numbers):
                    return Value("error", reason="min/max/abs只接受数字。")
                function = {"min": min, "max": max, "abs": abs}[node.func.id]
                return known(function(numbers[0]) if node.func.id == "abs" else function(numbers))
            return Value("error", reason="公式节点不可计算。")
        return evaluate(self.tree)


def validate_model(model):
    if not isinstance(model, dict) or type(model.get("schema_version")) is not int or model.get("schema_version") != 1:
        raise ModelError("模型须为schema_version=1的JSON对象。")
    extra = set(model) - {"schema_version", "title", "purpose", "fictional", "assumptions", "boundaries", "inputs", "derived", "constraints", "plans", "scenarios", "explore"}
    if extra:
        raise ModelError("模型含未知字段，不能静默忽略: " + ", ".join(sorted(extra)))
    text_field(model, "title", "模型", True)
    text_field(model, "purpose", "模型", True)
    if type(model.get("fictional")) is not bool:
        raise ModelError("fictional须明确为true或false。")
    for field in ("assumptions", "boundaries"):
        if not isinstance(model.get(field), list) or not model[field] or len(model[field]) > MAX_ITEMS or any(not isinstance(v, str) or not v.strip() or len(v) > 8000 for v in model[field]):
            raise ModelError(f"{field}须为非空文本列表，明确模型假设与解释边界。")
    inputs = model.get("inputs")
    if not isinstance(inputs, dict) or not 1 <= len(inputs) <= MAX_ITEMS:
        raise ModelError("inputs须为具名对象，包含1—64个输入。")
    for key, item in inputs.items():
        named(key, "输入名")
        if not isinstance(item, dict) or "value" not in item:
            raise ModelError(f"输入 {key}须包含value字段。")
        validate_scalar(item["value"], key)
        text_field(item, "label", key, True)
        text_field(item, "unit", key)
        text_field(item, "note", key)
        text_field(item, "source", key)
        if item.get("basis") not in {"observed", "assumed", "unknown"} or item.get("role") not in {"condition", "decision"}:
            raise ModelError(f"{key}须声明basis和role。")
        if (item["value"] is None) != (item["basis"] == "unknown"):
            raise ModelError(f"{key}: null值与basis=unknown必须对应；未知不能被数值假冒。")
        if item["basis"] == "observed" and not item.get("source", "").strip():
            raise ModelError(f"{key}: observed输入需明确source；工具不验证来源真实性。")
    available = set(inputs)
    formulas = {}
    for item in item_list(model, "derived"):
        key = named(item.get("id"), "派生量ID")
        if key in available:
            raise ModelError(f"变量名重复: {key}")
        text_field(item, "label", key, True)
        text_field(item, "unit", key)
        text_field(item, "note", key)
        formulas[key] = Formula(item.get("formula"), available)
        available.add(key)
    constraint_formulas = {}
    for item in item_list(model, "constraints"):
        key = named(item.get("id"), "约束ID")
        if key in constraint_formulas:
            raise ModelError(f"约束ID重复: {key}")
        text_field(item, "description", key, True)
        constraint_formulas[key] = Formula(item.get("formula"), available)
    explore = model.get("explore", {})
    if not isinstance(explore, dict) or len(explore) > 8:
        raise ModelError("explore须为条件名到离散值列表的对象，最多8个条件。")
    grid_size = 1
    for key, values in explore.items():
        if key not in inputs or inputs[key]["role"] != "condition":
            raise ModelError(f"explore只能改变condition输入: {key}")
        if not isinstance(values, list) or not 1 <= len(values) <= 16:
            raise ModelError(f"explore.{key}须含1—16个离散值。")
        for value in values:
            validate_scalar(value, f"explore.{key}")
            check_override_type(inputs[key]["value"], value, key)
        if len({json.dumps(v) for v in values}) != len(values):
            raise ModelError(f"explore.{key}含重复值。")
        grid_size *= len(values)
    groups = {}
    for field, role in (("plans", "decision"), ("scenarios", "condition")):
        items = item_list(model, field, 16)
        seen = {"baseline"}
        for item in items:
            key = named(item.get("id"), field + "ID")
            if key in seen:
                raise ModelError(f"{field}中ID重复或使用保留ID baseline。")
            seen.add(key)
            text_field(item, "label", key, True)
            text_field(item, "note", key)
            if not isinstance(item.get("overrides"), dict):
                raise ModelError(f"{field}.{key}需overrides对象。")
            for variable, value in item["overrides"].items():
                if variable not in inputs or inputs[variable]["role"] != role:
                    raise ModelError(f"{field}只能改变{role}输入: {variable}")
                if field == "scenarios" and variable in explore:
                    raise ModelError(f"情景与explore同时覆盖 {variable} 会掩盖设定，请选择一处表达。")
                validate_scalar(value, f"{field}.{key}.{variable}")
                check_override_type(inputs[variable]["value"], value, variable)
        groups[field] = [{"id": "baseline", "label": "输入中的决策值" if field == "plans" else "输入中的条件值", "overrides": {}}] + items
    count = grid_size * len(groups["plans"]) * len(groups["scenarios"])
    if count > MAX_CASES:
        raise ModelError(f"组合数 {count} 超过 {MAX_CASES}；缩小离散网格、情景或方案数量。未抽样、未截断。")
    return formulas, constraint_formulas, groups


def one_at_a_time(cases, model, explore):
    """Report whether varying one declared condition alone changes the model's state.

    Reads only already computed cases: no interpolation, no new values, and no
    ranking. It answers "which declared condition actually moves the outcome",
    which the full grid alone does not surface.
    """
    if not explore:
        return []
    keys = list(explore)
    report = []
    for key in keys:
        others = [name for name in keys if name != key]
        groups = {}
        for case in cases:
            signature = (case["scenario"], case["plan"],
                         tuple((name, json.dumps(case["explore"][name], ensure_ascii=False)) for name in others))
            groups.setdefault(signature, {})[json.dumps(case["explore"][key], ensure_ascii=False)] = case["state"]
        flips, states, examples = 0, set(), []
        for group in groups.values():
            states.update(group.values())
            if len(set(group.values())) > 1:
                flips += 1
                if len(examples) < 2:
                    declared = [json.dumps(value, ensure_ascii=False) for value in explore[key]]
                    ordered = [value for value in declared if value in group]
                    examples.append({"values": ordered, "states": [group[value] for value in ordered]})
        report.append({
            "condition": key,
            "label": model["inputs"][key].get("label", key),
            "values": explore[key],
            "groups": len(groups),
            "state_changing_groups": flips,
            "decisive": flips > 0,
            "observed_states": sorted(states),
            "examples": examples,
        })
    return report


def check_override_type(original, value, key):
    if original is not None and value is not None and (type(original) is bool) != (type(value) is bool):
        raise ModelError(f"{key}的布尔与数值类型不能在覆盖时互换。")


def evaluate_model(model):
    formulas, constraint_formulas, groups = validate_model(model)
    explore = model.get("explore", {})
    combinations = [dict(zip(explore, values)) for values in itertools.product(*explore.values())]
    cases = []
    for scenario, combination_item, plan in itertools.product(groups["scenarios"], enumerate(combinations), groups["plans"]):
        combination_index, combination = combination_item
        inputs = {key: {**item, "origin": "input"} for key, item in model["inputs"].items()}
        for overrides, origin in ((scenario["overrides"], "scenario:" + scenario["id"]), (combination, "explore"), (plan["overrides"], "plan:" + plan["id"])):
            for key, value in overrides.items():
                inputs[key] = {**inputs[key], "value": value, "basis": "unknown" if value is None else "assumed", "origin": origin,
                               "original_source": model["inputs"][key].get("source", ""),
                               "source": f"显式 {origin} 设定；原输入来源不为这个覆盖值作证。"}
        environment = {key: Value("unknown", reason=f"输入 {key} 未知。") if item["value"] is None else known(item["value"]) for key, item in inputs.items()}
        derived = []
        for item in model.get("derived", []):
            value = formulas[item["id"]].evaluate(environment)
            environment[item["id"]] = value
            derived.append({**item, **value.as_dict()})
        constraints = []
        for item in model.get("constraints", []):
            value = constraint_formulas[item["id"]].evaluate(environment)
            if value.state == "known" and type(value.value) is not bool:
                value = Value("error", reason="约束公式结果须为布尔值。")
            state = ("satisfied" if value.value else "violated") if value.state == "known" else value.state
            constraints.append({**item, **value.as_dict(), "state": state})
        states = [item["state"] for item in constraints]
        if "error" in states or any(item["state"] == "error" for item in derived): overall = "calculation_error"
        elif "violated" in states: overall = "violates_model_constraints"
        elif "unknown" in states: overall = "undetermined"
        elif not constraints: overall = "no_constraints"
        else: overall = "satisfies_model_constraints"
        cases.append({"id": f"case-{len(cases) + 1}", "scenario": scenario["id"], "scenario_label": scenario["label"], "plan": plan["id"], "plan_label": plan["label"], "explore_index": combination_index, "explore": combination, "inputs": inputs, "derived": derived, "constraints": constraints, "state": overall})
    return {"format": TOOL, "schema_version": 1, "model": model, "scenarios": groups["scenarios"], "plans": groups["plans"], "explore_combinations": combinations, "case_count": len(cases), "cases": cases, "sensitivity": one_at_a_time(cases, model, explore), "interpretation": "约束满足仅在此模型、这些输入与公式下成立；不证明现实可实施、最优、概率或因果关系。未知未作0处理。未列入的条件仍可能改变判断。敏感性只说明所列离散条件下模型状态是否改变，不代表现实中最重要，也不代替对未列入条件的核查。"}


def csv_cell(value):
    if value is None:
        return ""
    if type(value) is bool:
        return "true" if value else "false"
    if isinstance(value, str) and value[:1] in {"=", "+", "-", "@", "\t", "\r", "\n"}:
        return "'" + value
    return value


def render_csv(result):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for case in result["cases"]:
        common = {"format": TOOL, "case_id": case["id"], "scenario": case["scenario"], "explore": json.dumps(case["explore"], ensure_ascii=False), "plan": case["plan"], "case_state": case["state"]}
        entries = [("input", {"id": key, **item, "state": "unknown" if item["value"] is None else "known"}) for key, item in case["inputs"].items()]
        entries += [("derived", item) for item in case["derived"]] + [("constraint", item) for item in case["constraints"]]
        for kind, item in entries:
            record = {**common, "kind": kind, **{key: item.get(key, "") for key in CSV_FIELDS if key not in common and key != "kind"}}
            record["label"] = item.get("label", item.get("description", ""))
            record["note"] = "；".join(v for v in [item.get("note", ""), item.get("reason", ""), item.get("origin", "")] if v)
            writer.writerow({key: csv_cell(value) for key, value in record.items()})
    return output.getvalue()


DOWNLOAD_ICON = ('<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" '
                 'stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M12 4v11"/><path d="m7.5 10.5 4.5 4.5 4.5-4.5"/>'
                 '<path d="M5 19.5h14"/></svg>')
STATE_LEGEND = ('<dl class="state-legend" aria-label="状态图例">'
                '<div><dt><span class="state state-ok">满足</span></dt><dd>所列约束都成立</dd></div>'
                '<div><dt><span class="state state-bad">不满足</span></dt><dd>至少一项约束不成立</dd></div>'
                '<div><dt><span class="state state-unsure">尚不能确定</span></dt><dd>结果依赖未知输入</dd></div>'
                '<div><dt><span class="state state-err">计算错误</span></dt><dd>公式在此组合下算不出</dd></div></dl>')


def title_html(title):
    head, mark, tail = title.partition("：")
    if mark and head.strip() and tail.strip():
        return (f'<span class="title-main">{html.escape(head)}<span class="title-colon">：</span></span>'
                f'<span class="title-sub">{html.escape(tail)}</span>')
    return html.escape(title)


def render_html(result):
    assets = Path(__file__).resolve().parents[1] / "assets"
    try:
        css = (assets / "xikari-base.css").read_text(encoding="utf-8") + "\n" + (assets / "condition-lab.css").read_text(encoding="utf-8")
        javascript = (assets / "condition-lab.js").read_text(encoding="utf-8")
    except OSError as exc:
        raise ModelError(f"缺少离线展示资源: {exc}") from exc
    payload = json.dumps(result, ensure_ascii=False, allow_nan=False).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    model = result["model"]
    title = html.escape(model["title"])
    purpose = html.escape(model["purpose"])
    script_hash = base64.b64encode(hashlib.sha256(javascript.encode('utf-8')).digest()).decode('ascii')
    style_hash = base64.b64encode(hashlib.sha256(css.encode('utf-8')).digest()).decode('ascii')
    csp = f"default-src 'none'; script-src 'sha256-{script_hash}'; style-src 'sha256-{style_hash}'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"
    download = base64.b64encode(json.dumps(result, ensure_ascii=False, allow_nan=False).encode('utf-8')).decode('ascii')
    scope = ('这是明确虚构的教学模型，输入不是现实事实。' if model['fictional'] else '这是作者提供的情境模型；输入来源与假设仍需分别判断。') + f" 已计算 {result['case_count']} 个组合。"
    scope_class = 'notice notice-fictional' if model['fictional'] else 'notice'
    counts = (f"{len(result['scenarios'])} 种外部情景、{len(result['explore_combinations'])} 组离散条件、{len(result['plans'])} 个方案，"
              "每个组合都已按模型公式算出。页面只在这些结果之间切换，不插值，也不预测。")
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="generator" content="Xikari condition lab"><meta http-equiv="Content-Security-Policy" content="{html.escape(csp)}"><meta name="color-scheme" content="light dark"><title>{title}</title><style>{css}</style></head>
<body><main class="lab">
<header class="lab-header"><h1>{title_html(model["title"])}</h1><p class="lab-purpose">{purpose}</p><p id="scope" class="{scope_class}">{html.escape(scope)}</p><p class="lab-counts">{html.escape(counts)}</p></header>
<div class="lab-body">
<aside class="lab-controls" aria-labelledby="controls-heading">
<h2 id="controls-heading">选择已经计算的组合</h2>
<div class="controls"><label>外部情景<select id="scenario"></select></label><label>条件组合<select id="combination"></select></label><label>展开方案<select id="plan"></select></label></div>
<div id="current-state" class="current-state" role="status" aria-live="polite"></div>
{STATE_LEGEND}
</aside>
<div class="lab-results">
<section class="lab-section" aria-labelledby="overview-heading"><h2 id="overview-heading">全部已计算组合</h2><p class="section-note">所选外部情景下，每个方案在每组条件中的模型状态。点选一格即可展开它的计算。</p><div id="overview" class="table-scroll" tabindex="0" role="region" aria-label="全部已计算组合，可横向滚动"></div></section>
<section class="lab-section" aria-labelledby="comparison-heading"><h2 id="comparison-heading">同组条件下的方案</h2><p class="section-note">外部情景与条件组合不变，只换方案，逐项列出每条约束的结果。</p><div id="comparison" class="table-scroll" tabindex="0" role="region" aria-label="方案比较，可横向滚动"></div></section>
<section class="lab-section" aria-labelledby="constraints-heading"><h2 id="constraints-heading">逐项约束</h2><div id="constraints" class="table-scroll" tabindex="0" role="region" aria-label="逐项约束，可横向滚动"></div></section>
<section class="lab-section" aria-labelledby="derived-heading"><h2 id="derived-heading">计算关系</h2><div id="derived" class="table-scroll" tabindex="0" role="region" aria-label="计算关系，可横向滚动"></div></section>
<section class="lab-section" aria-labelledby="inputs-heading"><h2 id="inputs-heading">输入与来源</h2><p class="section-note">“作者声明的观察值”表示作者给出了来源，工具没有核验它。情景、条件网格和方案覆盖后的值一律标为假设或未知。</p><div id="inputs" class="table-scroll" tabindex="0" role="region" aria-label="输入与来源，可横向滚动"></div></section>
<section class="lab-section" aria-labelledby="sensitivity-heading"><h2 id="sensitivity-heading">单项条件的影响</h2><p class="section-note">固定其余条件、只改变一项离散条件时，模型状态是否随之改变。它只描述所列取值，不说明现实中哪一项最重要。</p><div id="sensitivity" class="sensitivity"></div></section>
<section class="lab-section lab-limits" aria-label="假设与边界"><div><h2>明确假设</h2><ul id="assumptions"></ul></div><div><h2>解释边界</h2><ul id="boundaries"></ul></div></section>
<section class="lab-section" aria-labelledby="definitions-heading"><h2 id="definitions-heading">方案与情景的定义</h2><div id="definitions" class="definitions"></div></section>
</div>
</div>
<footer class="lab-footer"><p>{html.escape(result['interpretation'])}</p><p>数值单位由作者声明；相同单位、明确公式和模型内的结果，仍需结合现实材料解释。</p><a class="download" href="data:application/json;charset=utf-8;base64,{download}" download="condition-results.json">{DOWNLOAD_ICON}下载全部条件、公式与计算结果</a></footer>
<noscript><p class="no-script">启用本地JavaScript后可以切换已计算的情景；不开启脚本时，仍可下载本页内嵌的完整JSON结果。</p></noscript>
</main><script type="application/json" id="condition-data">{payload}</script><script>{javascript}</script></body></html>'''


def owned_output(path, kind):
    try:
        if kind == "json":
            return json.loads(path.read_text(encoding="utf-8")).get("format") == TOOL
        if kind == "html":
            return '<meta name="generator" content="Xikari condition lab">' in path.read_text(encoding="utf-8")[:4096]
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            first, second = next(reader, []), next(reader, [])
            return first == CSV_FIELDS and bool(second) and second[0] == TOOL
    except (OSError, ValueError, AttributeError):
        return False


def same_path(first, second):
    if first.resolve() == second.resolve():
        return True
    try:
        return first.samefile(second)
    except OSError:
        return False


def write_outputs(result, source, output, output_format="all", force=False):
    require_external_output(output, __file__)
    kinds = list(OUTPUTS) if output_format == "all" else [output_format]
    paths = {kind: output / OUTPUTS[kind] for kind in kinds}
    for kind, path in paths.items():
        require_external_output(path, __file__)
        if same_path(path, source):
            raise ModelError("输出路径与输入文件相同，--force也不能覆盖输入。")
        if path.is_symlink():
            raise ModelError(f"输出是符号链接，拒绝替换: {path}")
        if path.exists() and (not force or not owned_output(path, kind)):
            raise ModelError(f"输出已存在且未授权覆盖本工具产物: {path}；使用新目录，或仅对已有本工具产物使用--force。")
    rendered = {}
    for kind in kinds:
        if kind == "json": rendered[kind] = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
        elif kind == "csv": rendered[kind] = render_csv(result)
        else: rendered[kind] = render_html(result)
        if len(rendered[kind].encode("utf-8")) > 32 * 1024 * 1024:
            raise ModelError("单项输出超过32MiB；缩小模型说明或组合数量。")
    lock = output / ".condition-lab.lock"
    require_external_output(lock, __file__)
    if same_path(lock, source):
        raise ModelError("输出锁路径与输入相同，拒绝写入。")
    output.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ModelError(f"输出目录正在写入或存在遗留锁: {lock}；未自动覆盖。") from exc
    os.close(fd)
    staged, previous, changed = {}, {}, []
    try:
        for kind, path in paths.items():
            if path.exists() and (not force or not owned_output(path, kind)):
                raise ModelError(f"输出路径在处理期间出现冲突: {path}")
            previous[kind] = path.read_bytes() if path.exists() else None
            fd, temporary = tempfile.mkstemp(prefix=".condition-", suffix=".tmp", dir=output)
            staged[kind] = temporary
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(rendered[kind])
                handle.flush()
                os.fsync(handle.fileno())
        for kind, path in paths.items():
            current = path.read_bytes() if path.exists() else None
            if current != previous[kind]:
                raise ModelError(f"输出在处理期间被修改: {path}")
            os.replace(staged[kind], path)
            changed.append(kind)
        return {kind: str(path.resolve()) for kind, path in paths.items()}
    except Exception:
        for kind in reversed(changed):
            path = paths[kind]
            if previous[kind] is None:
                path.unlink()
            else:
                path.write_bytes(previous[kind])
        raise
    finally:
        for temporary in staged.values():
            if os.path.exists(temporary):
                os.unlink(temporary)
        lock.unlink()


def read_model(path):
    data = path.read_bytes()
    if len(data) > 2 * 1024 * 1024:
        raise ModelError("模型文件上限2MiB。")
    try:
        def unique_pairs(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"重复JSON字段: {key}")
                result[key] = value
            return result
        model = json.loads(data.decode("utf-8-sig"), object_pairs_hook=unique_pairs, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"非有限JSON常量: {value}")))
    except (ValueError, UnicodeDecodeError, RecursionError) as exc:
        raise ModelError(f"无效模型JSON: {exc}") from exc
    return model, hashlib.sha256(data).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description="计算明确且有界的条件、情景与方案组合；结果不证明现实有效或最优。")
    parser.add_argument("model", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--format", choices=["all", "json", "csv", "html"], default="all")
    parser.add_argument("--force", action="store_true", help="仅覆盖固定文件名且可识别的已有本工具产物，不覆盖输入")
    args = parser.parse_args(argv)
    try:
        model, digest = read_model(args.model)
        result = evaluate_model(model)
        result["source_model"] = {"path": str(args.model.resolve()), "sha256": digest}
        outputs = write_outputs(result, args.model.resolve(), args.output, args.format, args.force)
    except (ModelError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"case_count": result["case_count"], "outputs": outputs, "interpretation": result["interpretation"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    raise SystemExit(main())
