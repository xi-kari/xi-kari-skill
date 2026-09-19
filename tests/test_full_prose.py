from copy import deepcopy

import pytest

from scripts.xi_kari_runtime import prose
from scripts.xi_kari_runtime.coverage import build_semantic_coverage
from scripts.xi_kari_runtime.semantic_projection import validate_reader_sections, semantic_atom_paths, substantive_semantic_atoms, _binding_preserves_atom


def packet():
    values = {
        "answer.direct_answer": "两条路径都能交付，但应优先安排有补偿的轮班。",
        "answer.why[0]": "共同的交付结果不能抵消成本承担位置的差异。",
        "answer.uncertainties[0]": "尚不能判断长期人员流失。",
        "answer.withdrawal_conditions[0]": "若补偿不能兑现，应重新比较安排。",
        "mechanisms[0].name": "有补偿轮班",
        "mechanisms[0].explanation": "组织支付轮班费用，员工获得可执行的补休。",
        "mechanisms[0].failure_condition": "预算未到账时无法保持补偿。",
        "mechanisms[1].name": "无偿加班",
        "mechanisms[1].explanation": "员工用私人时间完成同一交付，照护者承担额外损失。",
        "mechanisms[1].failure_condition": "照护时间无法转移时，这一路径停止。",
    }
    result = {
        "dynamic_applicability": "applicable",
        "deliverable_type": "decision",
        "answer": {
            "direct_answer": values["answer.direct_answer"],
            "why": [values["answer.why[0]"]],
            "uncertainties": [values["answer.uncertainties[0]"]],
            "withdrawal_conditions": [values["answer.withdrawal_conditions[0]"]],
        },
        "mechanisms": [
            {key: values[f"mechanisms[{i}].{key}"] for key in ("name", "explanation", "failure_condition")}
            for i in range(2)
        ],
        "reader_sections": [],
    }
    for i, (path, value) in enumerate(values.items()):
        result["reader_sections"].append({
            "section_id": f"s{i}", "heading": f"本题依据 {i + 1}",
            "local_judgment": value, "paragraphs": [f"这一点限制了本题可以成立的选择：{value}"],
            "source_bindings": [{"source_path": path, "paragraph_index": 0, "excerpt": value}],
        })
    result["visibility_ledger"] = {"entries": [
        {"canonical_path": path, "classification": "public", "disclosure": "include",
         "purpose": "comparison", "authority_refs": [], "protection_reason": None}
        for path in semantic_atom_paths(result)
    ]}
    return result


def coverage(value, outputs=None):
    return build_semantic_coverage(run_id="test", packet=value, source_read_complete=True,
        candidate_closure_complete=True, reader_outputs=outputs or prose.render_reader_outputs(value))


def test_complete_prose_retains_same_conclusion_different_costs():
    value = packet()
    answer = prose.render_answer(value)
    assert "员工用私人时间完成同一交付，照护者承担额外损失。" in answer
    assert "照护时间无法转移时，这一路径停止。" in answer
    assert validate_reader_sections(value) == []
    assert coverage(value)["main_answer_complete"]


def test_analysis_cannot_be_hidden_by_naming_a_field_content():
    value = packet()
    value["facts"] = {"content": "次要参与者仍需承担人工复核成本。"}
    value["visibility_ledger"]["entries"].append({
        "canonical_path": "facts.content", "classification": "public", "disclosure": "include",
        "purpose": "comparison", "authority_refs": [], "protection_reason": None,
    })
    assert any(atom["canonical_path"] == "facts.content" for atom in substantive_semantic_atoms(value))
    assert any("facts.content" in error for error in validate_reader_sections(value))


def test_raw_source_body_remains_a_source_instead_of_becoming_the_answer():
    value = packet()
    value["retrieval"] = {"sources": [{"source_id": "SOURCE-A", "content": "原始材料全文，不是分析论证。"}]}
    paths = {atom["canonical_path"] for atom in substantive_semantic_atoms(value)}
    assert "retrieval.sources[0].content" not in paths


def test_explained_stopping_condition_is_not_mistaken_for_compression():
    value = packet()
    path = "mechanisms[1].failure_condition"
    reason = "如果照护时间无法转移，这一路径不再展开。"
    value["mechanisms"][1]["failure_condition"] = reason
    section = next(section for section in value["reader_sections"] if section["source_bindings"][0]["source_path"] == path)
    section["local_judgment"] = reason
    section["source_bindings"][0]["excerpt"] = reason
    assert validate_reader_sections(value) == []


@pytest.mark.parametrize(("original", "changed"), [
    ("-10", "10"), ("0.5", "05"), ("1/2", "12"), ("A>B", "A<B"), ("1", "10"), ("1", "-1"),
])
def test_binding_preserves_numeric_and_relational_meaning(original, changed):
    assert not _binding_preserves_atom({"public_text": "判断依据：" + original}, "该值为" + changed)


@pytest.mark.parametrize("missing_path", [
    "mechanisms[1].explanation", "mechanisms[1].failure_condition", "answer.withdrawal_conditions[0]",
])
def test_unchanged_main_judgment_does_not_excuse_omission(missing_path):
    value = packet()
    value["reader_sections"] = [s for s in value["reader_sections"] if s["source_bindings"][0]["source_path"] != missing_path]
    assert any(missing_path in error for error in validate_reader_sections(value))
    assert not coverage(value)["main_answer_complete"]


def test_appendix_link_or_summary_cannot_satisfy_source_binding():
    for replacement in ("其余细节见[附件](xi-kari-dossier.md)。", "两条路径结果相同，成本问题不再展开。"):
        value = packet()
        section = value["reader_sections"][-1]
        section["local_judgment"] = replacement
        section["source_bindings"][0]["excerpt"] = replacement
        assert validate_reader_sections(value)
        assert not coverage(value)["main_answer_complete"]


def test_source_binding_must_resolve_to_real_paragraph():
    value = packet()
    value["reader_sections"][1]["source_bindings"][0]["paragraph_index"] = 9
    assert validate_reader_sections(value)


def test_cutting_reader_answer_fails_even_when_dossier_retains_content():
    value = packet()
    outputs = prose.render_reader_outputs(value)
    outputs["dossier"] += outputs["answer"]
    outputs["answer"] = value["answer"]["direct_answer"]
    assert not coverage(value, outputs)["main_answer_complete"]


def test_brief_view_requires_explicit_request_and_preserves_full_file():
    value = packet()
    value["question"] = "请简答"
    value["answer_delivery"] = {"visible_mode": "brief", "explicit_user_request": "请简答", "brief_text": "优先选择有补偿轮班；完整论证见正文。"}
    full = prose.render_answer(value)
    assert prose.render_chat_projection(value) == value["answer_delivery"]["brief_text"] + "\n"
    assert "照护时间无法转移时，这一路径停止。" in full
    invalid = deepcopy(value)
    invalid["answer_delivery"]["explicit_user_request"] = ""
    with pytest.raises(ValueError, match="explicit"):
        prose.render_chat_projection(invalid)
    assert prose.render_chat_projection(packet()) == prose.render_answer(packet())

    forged = deepcopy(value)
    forged["question"] = "完整分析轮班方案"
    with pytest.raises(ValueError, match="bound user question"):
        prose.render_chat_projection(forged)


def test_full_prose_plan_binds_deliverable_type():
    plan = prose.build_prose_plan(run_id="test", payload=packet(), coverage={})
    assert plan["deliverable_type"] == "decision"
    assert plan["delivery_mode"] == "full"
    assert plan["reader_sections"] == packet()["reader_sections"]


def test_missing_authored_sections_is_not_a_complete_v3_answer():
    value = packet()
    value.pop("reader_sections")
    assert validate_reader_sections(value)
    assert not coverage(value)["main_answer_complete"]


def test_authored_paragraph_cannot_reintroduce_protected_unbound_value():
    value = packet()
    entry = next(item for item in value["visibility_ledger"]["entries"]
                 if item["canonical_path"] == "mechanisms[1].explanation")
    entry.update(classification="sensitive", disclosure="withhold",
                 authority_refs=["privacy-contract"], protection_reason="未取得披露同意")
    section = value["reader_sections"][-2]
    section["source_bindings"] = []
    with pytest.raises(ValueError, match="protected source value"):
        prose.render_answer(value)


def test_static_analysis_still_requires_full_substantive_body():
    value = packet()
    value["dynamic_applicability"] = "not_applicable"
    value["mechanisms"] = []
    value["reader_sections"] = value["reader_sections"][:4]
    value["visibility_ledger"]["entries"] = [entry for entry in value["visibility_ledger"]["entries"]
                                           if not entry["canonical_path"].startswith("mechanisms")]
    assert coverage(value)["main_answer_complete"]
    value["reader_sections"].pop()
    assert not coverage(value)["main_answer_complete"]


def test_long_body_is_never_truncated_or_replaced_by_a_link():
    value = packet()
    paragraph = "组织承担有偿安排的预算，私人照护时间不能被视为免费资源。" * 3000
    value["reader_sections"][0]["paragraphs"].append(paragraph)
    assert paragraph in prose.render_answer(value)
    assert prose.render_chat_projection(value) == prose.render_answer(value)


def test_new_local_judgments_and_rejected_options_remain_substantive():
    value = packet()
    value["verdict"] = {"claim_verdicts": [{"claim_id": "CLAIM-PROCEDURE", "status": "bounded",
        "judgment": "程序缺陷已经成立。", "reason": "缺少动机证据不撤销已记录的申诉阻塞。"}],
        "explanation_ranking": [{"role": "supplementary", "reason": "同时解释员工的恢复成本。", "rank": None}]}
    value["action_ranking"] = {"selection_status": "recommended", "preferred_option_id": "OPTION-PAID",
        "options": [{"comparison_reason": "无偿安排把成本转给照护者，故不建议采用。"}],
        "category_dispositions": [{"kind": "exit-or-transfer", "applicability": "not-applicable", "reason": "六周内没有可承接岗位。"}]}
    paths = {atom["canonical_path"] for atom in substantive_semantic_atoms(value)}
    for path in (
        "verdict.claim_verdicts[0].judgment", "verdict.claim_verdicts[0].reason",
        "verdict.explanation_ranking[0].role", "verdict.explanation_ranking[0].rank",
        "action_ranking.selection_status", "action_ranking.preferred_option_id",
        "action_ranking.options[0].comparison_reason", "action_ranking.category_dispositions[0].reason",
    ):
        assert path in paths
        assert any(path in error for error in validate_reader_sections(value))
