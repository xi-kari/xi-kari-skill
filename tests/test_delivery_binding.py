from copy import deepcopy

import pytest

from scripts.xi_kari_runtime import contracts


def packet():
    return {
        "deliverable_type": "plan",
        "problem_contract": {"deliverable_type": "plan", "question": "制定六周计划。"},
        "reader_sections": [{
            "section_id": "schedule", "heading": "先调整审核安排",
            "local_judgment": "应先增加审核容量。",
            "paragraphs": ["第一周调整审核安排。"], "source_bindings": [],
        }],
    }


def test_delivery_type_cannot_change_between_question_and_answer() -> None:
    value = packet()
    value["deliverable_type"] = "critique"
    with pytest.raises(ValueError, match="deliverable"):
        contracts.validate_delivery_binding(value)


def test_formal_answer_requires_authored_sections() -> None:
    value = packet()
    value["reader_sections"] = []
    with pytest.raises(ValueError, match="reader_sections"):
        contracts.validate_delivery_binding(value)


def test_default_request_cannot_be_silently_shortened() -> None:
    value = packet()
    value["answer_delivery"] = {
        "visible_mode": "brief", "explicit_user_request": "请简答", "brief_text": "只调整审核。"
    }
    with pytest.raises(ValueError, match="explicit"):
        contracts.validate_delivery_binding(value)


def test_explicit_short_answer_preserves_full_sections() -> None:
    value = packet()
    value["problem_contract"]["question"] += "请简答。"
    value["answer_delivery"] = {
        "visible_mode": "brief", "explicit_user_request": "请简答", "brief_text": "先调整审核。"
    }
    before = deepcopy(value)
    contracts.validate_delivery_binding(value)
    assert value == before


def test_do_not_compress_is_not_a_request_for_brief_output() -> None:
    value = packet()
    value["problem_contract"]["question"] += "不要简答。"
    value["answer_delivery"] = {
        "visible_mode": "brief", "explicit_user_request": "简答", "brief_text": "先调整审核。"
    }
    with pytest.raises(ValueError, match="explicit"):
        contracts.validate_delivery_binding(value)


def test_malformed_authored_paragraphs_are_rejected_cleanly() -> None:
    value = packet()
    value["reader_sections"][0]["paragraphs"] = None
    with pytest.raises(ValueError, match="reader_sections"):
        contracts.validate_delivery_binding(value)


def test_static_answer_cannot_hide_inference_in_reader_sections() -> None:
    value = packet()
    value["dynamic_applicability"] = "not_applicable"
    value["answer"] = {"direct_answer": "这是一个静态定义问题。", "why": []}
    value["reader_sections"][0]["paragraphs"] = ["二阶导致成员失去选择空间。"]
    with pytest.raises(ValueError, match="static.*reader_sections"):
        contracts.validate_delivery_binding(value)


def test_static_brief_cannot_add_inference_absent_from_full_answer() -> None:
    value = packet()
    value["dynamic_applicability"] = "not_applicable"
    value["answer"] = {"direct_answer": "这是一个静态定义问题。", "why": []}
    value["problem_contract"]["question"] += "请简答。"
    value["answer_delivery"] = {
        "visible_mode": "brief", "explicit_user_request": "请简答",
        "brief_text": "三阶导致治理规则改变。",
    }
    with pytest.raises(ValueError, match="static.*brief"):
        contracts.validate_delivery_binding(value)
