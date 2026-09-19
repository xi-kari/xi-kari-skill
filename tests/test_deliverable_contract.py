from copy import deepcopy

import pytest

from scripts.xi_kari_runtime.problem_contract import (
    build_natural_request_envelope,
    draft_problem_contract_from_natural_request,
    freeze_natural_problem_contract,
    validate_problem_contract,
)


CUTOFF = "2026-09-20T00:00:00+08:00"


@pytest.mark.parametrize(
    ("question", "kind", "advice"),
    [
        ("用 Xi-Kari 分析这个项目的延期原因。", "analysis", False),
        ("帮我比较两种方案，给我推荐。", "decision", True),
        ("帮我们拟一份可以讨论的排期章程。", "charter", True),
        ("给我们制定未来六周的执行计划。", "plan", True),
        ("评价这段论断，写一篇锐评。", "critique", False),
        ("评价这份章程中的论证。", "critique", False),
        ("Write a charter for our reading club.", "charter", True),
        ("Recommend which option we should choose.", "decision", True),
    ],
)
def test_natural_request_carries_delivery_intent(question: str, kind: str, advice: bool) -> None:
    contract = draft_problem_contract_from_natural_request(
        question, mode="closed-input", evidence_cutoff=CUTOFF
    )
    assert contract["deliverable_type"] == kind
    assert contract["advice_requested"] is advice
    assert contract["question"] == question


def test_semantic_author_can_refine_an_ambiguous_task_without_new_user_parameter() -> None:
    question = "帮我们看看接下来六周怎么安排。"
    envelope = build_natural_request_envelope(question, mode="closed-input", evidence_cutoff=CUTOFF)
    proposal = draft_problem_contract_from_natural_request(
        question, mode="closed-input", evidence_cutoff=CUTOFF
    )
    proposal.update(deliverable_type="plan", problem_action="choose", advice_requested=True)
    frozen = freeze_natural_problem_contract(proposal, request=envelope, mode="closed-input")
    assert frozen["deliverable_type"] == "plan"


def test_unrecognized_delivery_type_is_rejected_without_rewriting() -> None:
    contract = draft_problem_contract_from_natural_request(
        "分析材料", mode="closed-input", evidence_cutoff=CUTOFF
    )
    contract["deliverable_type"] = "authorized-decision"
    original = deepcopy(contract)
    with pytest.raises(ValueError, match="deliverable_type"):
        validate_problem_contract(contract, mode="closed-input")
    assert contract == original
