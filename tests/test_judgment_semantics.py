from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from xi_kari_runtime import claims, judgment


@pytest.fixture(autouse=True)
def isolate_ontology_snapshot(monkeypatch):
    """Exercise real schemas and semantics; source integrity has its own suite."""
    monkeypatch.setattr(claims, "_validate_ontology_binding", lambda *a, **k: None)
    monkeypatch.setattr(judgment, "_validate_ontology_binding", lambda *a, **k: None)


def base_graph():
    kinds = ("factual", "structural", "mechanism", "prediction", "value", "responsibility", "authorization")
    boundary = {
        "decision_subject": "committee", "target_object": "pilot",
        "single_action": "Run a reversible pilot", "territory": "team",
        "validity_interval": {"starts_at": "2026-09-20T00:00:00Z", "ends_at": "2026-10-20T00:00:00Z"},
    }
    graph = {
        "schema_id": "xi-kari.v3.xk.claim-mechanism-graph", "source_version": "v8.3",
        "ontology_refs": ["V83-CANON-CORE-CLAIM-ROLES"], "source_anchors": ["V83-P0001"],
        "world_volume_id": "WORLD-1", "central_claim_id": "CLAIM-STRUCTURAL",
        "evidence": [], "claims": [], "mechanisms": [], "explanations": [],
        "cases": [], "countercases": [], "missing_inputs": [],
    }
    for kind in kinds:
        identifier = kind.upper()
        graph["evidence"].append({
            "evidence_id": "E-" + identifier, "identity": "observed", "source_refs": ["SOURCE-" + identifier],
            "xk3_evidence_refs": ["XK3-" + identifier], "support_status": "available", "support_reason": "Documented evidence.",
        })
        graph["claims"].append({
            "claim_id": "CLAIM-" + identifier, "kind": kind, "statement": "Bounded " + kind + " proposition.",
            "evidence_refs": ["E-" + identifier], "mechanism_ids": [], "depends_on_claim_ids": [],
            "withdrawal_conditions": ["New contrary evidence"], "authorization_boundary": boundary if kind == "authorization" else None,
        })
    for number, claim_kind in ((1, "mechanism"), (2, "prediction")):
        claim_id = "CLAIM-" + claim_kind.upper()
        mechanism_id = f"MECHANISM-{number}"
        graph["claims"][number + 1]["mechanism_ids"] = [mechanism_id]
        graph["mechanisms"].append({
            "mechanism_id": mechanism_id, "name": f"Channel {number}", "input_state": "work accumulates",
            "carrier": f"role {number}", "channel": f"handoff {number}", "clock": "weekly",
            "conditions": ["Scope remains stable"], "output_state": "delay changes", "evidence_refs": ["E-" + claim_kind.upper()],
            "transition_refs": [{"event_id": "EVENT-1", "state_diff_id": "DIFF-1"}], "transformation_ids": ["TRANSFORM-1"],
            "discriminating_observations": ["Compare transfer delays"], "countermechanism": "capacity may offset delay", "failure_condition": "No transferred work",
        })
        for case_kind in ("documented-real", "conditional-scenario"):
            graph["cases"].append({
                "case_id": f"CASE-{number}-{case_kind.upper()}", "kind": case_kind, "title": "Handoff comparison",
                "tests_claim_ids": [claim_id], "source_refs": ["SOURCE-" + claim_kind.upper()] if case_kind == "documented-real" else [],
                "conditions": ["Comparable scope"], "stop_conditions": ["Different task"], "cannot_prove": ["Universal causality"],
            })
        graph["countercases"].append({
            "countercase_id": f"COUNTER-{number}", "attacks_claim_ids": [claim_id], "attacks_mechanism_ids": [mechanism_id],
            "conditions": ["No work moved"], "expected_signal": "delay unchanged", "reverse_signal": "delay falls",
            "decision_impact": "Reassess recommendation", "source_refs": [],
        })
    for kind, claim_ids, mechanism_ids, residuals in (
        ("simple-baseline", ["CLAIM-FACTUAL"], [], []),
        ("main", ["CLAIM-MECHANISM"], ["MECHANISM-1"], []),
        ("strongest-rival", ["CLAIM-PREDICTION"], ["MECHANISM-2"], []),
        ("mixture", ["CLAIM-MECHANISM", "CLAIM-PREDICTION"], ["MECHANISM-1", "MECHANISM-2"], []),
        ("residual", ["CLAIM-FACTUAL"], [], ["RESIDUAL-1"]),
    ):
        graph["explanations"].append({
            "explanation_id": "EXPLAIN-" + kind.upper(), "kind": kind, "claim_ids": claim_ids,
            "mechanism_ids": mechanism_ids, "residual_ids": residuals, "rationale": "Evidence for " + kind,
            "applicability": "applicable", "explanandum": "Delay in the handoff process",
        })
    return graph


def base_verdict(graph=None):
    graph = graph or base_graph()
    records = []
    local = []
    for claim in graph["claims"]:
        kind = "fact" if claim["kind"] == "factual" else "structure" if claim["kind"] == "structural" else claim["kind"]
        records.append({
            "verdict_id": "VERDICT-" + kind.upper(), "kind": kind, "proposition": claim["statement"],
            "evidence_refs": claim["evidence_refs"], "claim_ids": [claim["claim_id"]],
            "claim_evidence_edges": [{"claim_id": claim["claim_id"], "evidence_id": claim["evidence_refs"][0]}],
            "mechanism_ids": claim["mechanism_ids"], "recursive_node_ids": [], "status": "bounded",
            "authorization_scope": {"source_evidence_id": claim["evidence_refs"][0], **claim["authorization_boundary"]} if kind == "authorization" else None,
        })
        local.append({
            "claim_id": claim["claim_id"], "status": "bounded", "judgment": claim["statement"], "reason": "Independent recorded evidence.",
            "blocking_claim_ids": [], "blocking_evidence_refs": [], "missing_input_ids": [],
        })
    return {
        "schema_id": "xi-kari.v3.xk.verdict", "source_version": "v8.3", "ontology_refs": ["V83-CANON-AUTHORIZATION"],
        "source_anchors": ["V83-P0001"], "judgment_kind": "best-current", "non_decidability": None,
        "current_best_judgment": {
            "proposition": "Improve the handoff first.", "strength": "conditional", "best_explanation_id": "EXPLAIN-MAIN",
            "runner_up_explanation_id": "EXPLAIN-STRONGEST-RIVAL", "strongest_counterevidence_refs": ["E-PREDICTION"],
            "unexplained_residual_ids": ["RESIDUAL-1"], "withdrawal_conditions": ["Handoff delay does not change"],
            "time_window": "six weeks", "indicator_ids": ["INDICATOR-1"], "action_ceiling": "Recommendation only",
        },
        "explanation_ranking": [
            {"explanation_id": item["explanation_id"], "rank": rank, "role": role, "reason": item["rationale"], "claim_ids": item["claim_ids"]}
            for item, rank, role in zip(graph["explanations"], [None, 1, 1, None, None], ["background", "primary", "supplementary", "supplementary", "unresolved"])
        ],
        "five_verdicts": records, "claim_verdicts": local, "assumptions": ["Stable workload"], "decisive_unknown_ids": [],
    }


def base_actions(verdict=None):
    verdict = verdict or base_verdict()
    options = []
    for kind in ("active", "no-action"):
        options.append({
            "option_id": "OPTION-" + kind.upper(), "kind": kind, "description": "Run a reversible pilot" if kind == "active" else "Make no change",
            "target_object": "pilot", "territory": "team", "validity_interval": {"starts_at": "2026-09-20T00:00:00Z", "ends_at": "2026-10-20T00:00:00Z"},
            "affected_positions": ["POSITION-1"], "costs": ["One coordinator hour weekly"], "lock_in_risks": ["Routine may persist"],
            "reversibility": "high", "information_value": "Observe transfer time", "executor": "committee", "authorized": False,
            "execution_status": "analysis_only", "authorization_verdict_id": None, "stop_conditions": ["Costs increase"],
            "rollback": "Return to prior schedule", "appeal": "Independent review", "remedy": "Restore lost time",
            "comparison_reason": "Pilot yields discriminating evidence" if kind == "active" else "Retains current delay burden",
        })
    return {
        "schema_id": "xi-kari.v3.xk.action-ranking", "source_version": "v8.3", "ontology_refs": ["V83-CANON-SELECTION"], "source_anchors": ["V83-P0001"],
        "considered_verdict_ids": [r["verdict_id"] for r in verdict["five_verdicts"]], "requested_choice": True,
        "selection_status": "recommended", "options": options, "ranking": [o["option_id"] for o in options],
        "display_order": [o["option_id"] for o in options], "preferred_option_id": "OPTION-ACTIVE", "second_option_id": "OPTION-NO-ACTION",
        "switch_conditions": ["Observed delay is negligible"], "stop_conditions": ["Unacceptable burden"], "no_action_consequences": ["Current delay remains"],
        "supporting_claim_ids": ["CLAIM-STRUCTURAL"],
        "category_dispositions": [
            {"kind": kind, "applicability": "applicable" if kind in {"active", "no-action"} else "not-applicable",
             "option_ids": ["OPTION-" + kind.upper()] if kind in {"active", "no-action"} else [], "reason": "Compared within this task" if kind in {"active", "no-action"} else "No feasible distinct option within the resource boundary"}
            for kind in judgment.OPTION_KINDS
        ],
    }


def block_claim(verdict, claim_id, *, evidence=(), parents=(), missing=()):
    record = next(r for r in verdict["claim_verdicts"] if r["claim_id"] == claim_id)
    record.update(status="undecidable", blocking_evidence_refs=list(evidence), blocking_claim_ids=list(parents), missing_input_ids=list(missing))
    for total in verdict["five_verdicts"]:
        if claim_id in total["claim_ids"]:
            total.update(status="undecidable", evidence_refs=[], claim_ids=[], claim_evidence_edges=[], mechanism_ids=[], recursive_node_ids=[], authorization_scope=None)


def test_recommendation_does_not_require_execution_permission():
    verdict = base_verdict()
    result = judgment.validate_action_ranking(base_actions(verdict), verdict_bundle=verdict)
    assert result["selection_status"] == "recommended"
    assert result["options"][0]["execution_status"] == "analysis_only"


def test_recommendation_cannot_be_relabelled_selected():
    actions = base_actions()
    actions["selection_status"] = "selected"
    with pytest.raises(judgment.JudgmentError, match="authorized and executable"):
        judgment.validate_action_ranking(actions, verdict_bundle=base_verdict())


def test_no_requested_choice_does_not_fabricate_options():
    actions = base_actions()
    actions.update(requested_choice=False, selection_status="not-requested", options=[], ranking=None, display_order=[], preferred_option_id=None, second_option_id=None, supporting_claim_ids=[])
    for category in actions["category_dispositions"]:
        category.update(applicability="not-applicable", option_ids=[], reason="This task evaluates an argument and requests no choice.")
    assert judgment.validate_action_ranking(actions, verdict_bundle=base_verdict())["options"] == []


def test_requested_choice_retains_no_action_baseline():
    actions = base_actions()
    actions["options"] = actions["options"][:1]
    actions["ranking"] = actions["display_order"] = ["OPTION-ACTIVE"]
    actions["second_option_id"] = None
    actions["category_dispositions"][-1].update(applicability="not-applicable", option_ids=[])
    with pytest.raises(judgment.JudgmentError, match="no-action"):
        judgment.validate_action_ranking(actions, verdict_bundle=base_verdict())


def test_compatible_mechanisms_keep_a_partial_order():
    graph = base_graph()
    result = judgment.validate_verdict_bundle(base_verdict(graph), claim_mechanism_graph=graph)
    assert [r["rank"] for r in result["explanation_ranking"]] == [None, 1, 1, None, None]


def test_irrelevant_explanation_category_is_not_invented():
    graph = base_graph()
    graph["explanations"][-1].update(applicability="not-applicable", claim_ids=[], mechanism_ids=[], residual_ids=[], rationale="No unexplained residual in this bounded argument.")
    verdict = base_verdict(graph)
    verdict["explanation_ranking"][-1].update(role="not-applicable", rank=None, claim_ids=[])
    assert judgment.validate_verdict_bundle(verdict, claim_mechanism_graph=graph)


def test_missing_motive_does_not_retract_independent_procedural_judgment():
    graph = base_graph()
    graph["missing_inputs"] = [{"missing_id": "MISSING-MOTIVE", "description": "Private motive unavailable", "effect": "blocking", "scope": "local", "affected_claim_ids": ["CLAIM-RESPONSIBILITY"]}]
    verdict = base_verdict(graph)
    block_claim(verdict, "CLAIM-RESPONSIBILITY", missing=["MISSING-MOTIVE"])
    checked = judgment.validate_verdict_bundle(verdict, claim_mechanism_graph=graph)
    assert next(r for r in checked["claim_verdicts"] if r["claim_id"] == "CLAIM-STRUCTURAL")["status"] == "bounded"
    assert judgment.validate_action_ranking(base_actions(checked), verdict_bundle=checked)


def test_failed_dependency_propagates_and_cannot_reenter_recommendation():
    graph = base_graph()
    graph["claims"][1]["depends_on_claim_ids"] = ["CLAIM-FACTUAL"]
    graph["evidence"][0]["support_status"] = "invalidated"
    verdict = base_verdict(graph)
    block_claim(verdict, "CLAIM-FACTUAL", evidence=["E-FACTUAL"])
    with pytest.raises(judgment.JudgmentError, match="dependency|blocked|blocking"):
        judgment.validate_verdict_bundle(verdict, claim_mechanism_graph=graph)
    block_claim(verdict, "CLAIM-STRUCTURAL", evidence=["E-FACTUAL"], parents=["CLAIM-FACTUAL"])
    checked = judgment.validate_verdict_bundle(verdict, claim_mechanism_graph=graph)
    with pytest.raises(judgment.JudgmentError, match="supporting.*claim|undecidable"):
        judgment.validate_action_ranking(base_actions(checked), verdict_bundle=checked)


def test_renamed_evidence_cannot_launder_a_failed_source_atom():
    graph = base_graph()
    graph["evidence"][0]["support_status"] = "invalidated"
    alias = deepcopy(graph["evidence"][0])
    alias.update(evidence_id="E-ALIAS", support_status="available")
    graph["evidence"].append(alias)
    graph["claims"][1]["evidence_refs"] = ["E-ALIAS"]
    verdict = base_verdict(graph)
    block_claim(verdict, "CLAIM-FACTUAL", evidence=["E-FACTUAL", "E-ALIAS"])
    with pytest.raises(judgment.JudgmentError, match="blocked|blocking"):
        judgment.validate_verdict_bundle(verdict, claim_mechanism_graph=graph)


def test_global_identity_gap_blocks_all_claims():
    graph = base_graph()
    graph["missing_inputs"] = [{"missing_id": "MISSING-IDENTITY", "description": "The object identity is invalid", "effect": "blocking", "scope": "global", "affected_claim_ids": [c["claim_id"] for c in graph["claims"]]}]
    with pytest.raises(judgment.JudgmentError, match="blocked|blocking|dependency"):
        judgment.validate_verdict_bundle(base_verdict(graph), claim_mechanism_graph=graph)


def test_claim_dependency_cycle_is_rejected():
    graph = base_graph()
    graph["claims"][0]["depends_on_claim_ids"] = ["CLAIM-STRUCTURAL"]
    graph["claims"][1]["depends_on_claim_ids"] = ["CLAIM-FACTUAL"]
    with pytest.raises(claims.ClaimMechanismError, match="cycle"):
        claims.validate_claim_graph(graph)


def test_limiting_missing_input_prevents_factual_lock():
    graph = base_graph()
    graph["missing_inputs"] = [{"missing_id": "MISSING-COVERAGE", "description": "Some shifts were not observed", "effect": "limiting", "scope": "local", "affected_claim_ids": ["CLAIM-FACTUAL"]}]
    verdict = base_verdict(graph)
    verdict["claim_verdicts"][0].update(status="locked", missing_input_ids=["MISSING-COVERAGE"])
    with pytest.raises(judgment.JudgmentError, match="limiting|locked"):
        judgment.validate_verdict_bundle(verdict, claim_mechanism_graph=graph)


def test_input_snapshots_are_not_mutated():
    graph = base_graph()
    verdict = base_verdict(graph)
    before = deepcopy((graph, verdict))
    judgment.validate_verdict_bundle(verdict, claim_mechanism_graph=graph)
    assert (graph, verdict) == before


def test_authorized_selection_keeps_atomic_scope_and_bound_controls():
    from xi_kari_runtime.canonical_json import sha256_json

    verdict = base_verdict()
    actions = base_actions(verdict)
    actions["selection_status"] = "selected"
    preferred = actions["options"][0]
    preferred.update(authorized=True, execution_status="executable", authorization_verdict_id="VERDICT-AUTHORIZATION")
    preferred["control_bindings"] = {
        field: {"authorization_verdict_id": "VERDICT-AUTHORIZATION", "evidence_refs": ["E-AUTHORIZATION"], "content_sha256": sha256_json(preferred[field])}
        for field in ("stop_conditions", "rollback", "appeal", "remedy")
    }
    assert judgment.validate_action_ranking(actions, verdict_bundle=verdict)["selection_status"] == "selected"
    preferred["territory"] = "all departments"
    with pytest.raises(judgment.JudgmentError, match="atomic authorization"):
        judgment.validate_action_ranking(actions, verdict_bundle=verdict)


def test_recommended_no_action_is_not_an_authorized_intervention():
    actions = base_actions()
    actions.update(ranking=["OPTION-NO-ACTION", "OPTION-ACTIVE"], preferred_option_id="OPTION-NO-ACTION", second_option_id="OPTION-ACTIVE")
    assert judgment.validate_action_ranking(actions, verdict_bundle=base_verdict())
    actions["selection_status"] = "selected"
    with pytest.raises(judgment.JudgmentError, match="authorized and executable"):
        judgment.validate_action_ranking(actions, verdict_bundle=base_verdict())


def test_option_category_cannot_hide_an_unlisted_option():
    actions = base_actions()
    actions["category_dispositions"][0]["option_ids"] = []
    with pytest.raises(judgment.JudgmentError, match="category disposition"):
        judgment.validate_action_ranking(actions, verdict_bundle=base_verdict())


def test_partial_action_order_preserves_unranked_comparison():
    actions = base_actions()
    actions.update(ranking=["OPTION-ACTIVE"], second_option_id=None)
    result = judgment.validate_action_ranking(actions, verdict_bundle=base_verdict())
    assert len(result["options"]) == 2
    assert result["options"][1]["comparison_reason"]


def test_argument_analysis_can_dispose_of_inapplicable_mechanism_categories():
    graph = base_graph()
    graph["mechanisms"] = graph["cases"] = graph["countercases"] = []
    for claim in graph["claims"]:
        claim["mechanism_ids"] = []
    for explanation in graph["explanations"][1:]:
        explanation.update(applicability="not-applicable", claim_ids=[], mechanism_ids=[], residual_ids=[], rationale="This logical argument has no empirical mechanism to assert.")
    assert claims.validate_claim_graph(graph)


def test_global_gap_cannot_omit_an_independently_named_claim():
    graph = base_graph()
    graph["missing_inputs"] = [{"missing_id": "MISSING-IDENTITY", "description": "Object identity failed", "effect": "blocking", "scope": "global", "affected_claim_ids": ["CLAIM-FACTUAL"]}]
    with pytest.raises(claims.ClaimMechanismError, match="global missing"):
        claims.validate_claim_graph(graph)


def test_total_verdict_cannot_promote_a_locally_undecidable_claim():
    graph = base_graph()
    verdict = base_verdict(graph)
    verdict["claim_verdicts"][0]["status"] = "undecidable"
    with pytest.raises(judgment.JudgmentError, match="promote an undecidable"):
        judgment.validate_verdict_bundle(verdict, claim_mechanism_graph=graph)


def test_source_failure_reaches_alias_with_a_different_evidence_atom():
    graph = base_graph()
    graph["evidence"][0]["support_status"] = "invalidated"
    graph["evidence"][1]["source_refs"] = ["SOURCE-FACTUAL"]
    verdict = base_verdict(graph)
    block_claim(verdict, "CLAIM-FACTUAL", evidence=["E-FACTUAL", "E-STRUCTURAL"])
    with pytest.raises(judgment.JudgmentError, match="dependency|blocked"):
        judgment.validate_verdict_bundle(verdict, claim_mechanism_graph=graph)


def test_bounded_parent_cannot_be_upgraded_by_a_locked_child():
    graph = base_graph()
    graph["claims"][1]["depends_on_claim_ids"] = ["CLAIM-FACTUAL"]
    verdict = base_verdict(graph)
    verdict["claim_verdicts"][1]["status"] = "locked"
    with pytest.raises(judgment.JudgmentError, match="bounded dependency"):
        judgment.validate_verdict_bundle(verdict, claim_mechanism_graph=graph)
