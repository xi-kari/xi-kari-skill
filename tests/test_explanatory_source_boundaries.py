import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def concept(concept_id):
    rows = map(json.loads, read("references/ontology/inventory/core.jsonl").splitlines())
    return next(row for row in rows if row["concept_id"] == concept_id)


def test_df7_missing_authorization_preserves_independent_recommendations():
    row = concept("V83-CANON-CORE-DYNAMIC-NINE-GATES")
    counterexample = "\n".join(row["counterexamples"])
    assert "只能给需求清单" not in counterexample
    assert "独立成立的评价" in counterexample
    assert "条件建议" in counterexample
    assert "不能给可执行指令" in counterexample


def test_recursive_orders_are_not_protocol_gate_groups():
    row = concept("V83-CANON-CORE-DYNAMIC-NINE-GATES")
    interfaces = "\n".join(row["three_order_interfaces"])
    assert "模拟" in interfaces
    assert "继承" in interfaces
    assert all("经 DF" not in item for item in row["three_order_interfaces"])
    card = read(row["card_path"])
    assert "四次转换的一阶是可观测化" not in card
    assert "三阶不是三个时间点" in card


@pytest.mark.parametrize("relative", [
    "references/ontology/cards/foundation-boundary/claim-roles-and-missing-states.md",
    "references/ontology/inventory/core.jsonl",
])
def test_selection_includes_system_selection_without_conflating_actor_choice(relative):
    text = read(relative)
    assert "选择 ≠ 系统筛选" not in text
    assert "选择不等于系统筛选" not in text
    assert "主体决策" in text
    assert "系统筛选" in text


def test_g4a_closure_failure_is_not_a_blanket_stop():
    text = read("references/learning-packs/03-scale-transformation.md")
    assert "G4 不闭合时退回简单模型" not in text
    assert "G4a" in text and "正向" in text
    assert "未获支持或未决" in text
    assert "零结论" in text


def test_six_categories_require_applicability_not_six_fabricated_actions():
    text = read("references/learning-packs/08-forecast-choice.md")
    assert "选项至少包含" not in text
    assert "适用性" in text
    assert "不适用" in text
    assert "不能" in text and "虚构" in text


@pytest.mark.parametrize("relative", [
    "references/learning-packs/03-scale-transformation.md",
    "references/ontology/cards/event-inference/forecast-and-choice-interface.md",
])
def test_conditional_reentry_does_not_require_future_events_already_observed(relative):
    text = read(relative)
    assert "模拟状态" in text
    assert "未知" in text and "残差" in text
    assert "V83-P2114" in text and "V83-P2115" in text
