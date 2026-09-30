"""Causal recomputation at the real v4 graph/instance seam, without model calls."""

from copy import deepcopy
from importlib import import_module
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from tests.test_p04_instance_results_v4 import requested_graph, instance_inputs
from tests.test_causal_judgment_effects import history_contract, history_result
from xi_kari_runtime import claims
from xi_kari_runtime.canonical_json import sha256_json
from xi_kari_runtime.empirical_instances import freeze_empirical_instance
from xi_kari_runtime.formal_results import bind_formal_claim_results, rebuild_instance_registry
from xi_kari_runtime.v4_contracts import claim_graph_input


@pytest.fixture
def api():
    return import_module("xi_kari_runtime.causal_results_v4")


def inputs(*, hard_root=False):
    graph = requested_graph()
    next(row for row in graph["evidence"] if row["evidence_id"] == "E-MECHANISM")["support_status"] = "invalidated"
    empirical = instance_inputs()
    if hard_root:
        instance_id = empirical[0]["preregistration"]["instance_id"]
        graph["dependency_edges"].append({"edge_id": "EDGE-REAL-G2", "from_id": "CLAIM-STRUCTURAL",
            "to_ref": {"kind": "instance", "id": instance_id}, "role": "inferential_requires",
            "source_refs": ["V90-P00158"], "condition": "The actual evaluated G2 route is selected.",
            "scope": "Only this structural use."})
        graph["dependency_targets"] = [{"kind": "instance", "id": instance_id, "status": "not_run",
            "reason": "A result label cannot supply this prerequisite."}]
    qualified = bind_formal_claim_results(graph, empirical_instances=empirical,
        repository_root=ROOT)["claim_mechanism_graph"]
    scope = qualified["claims"][0]["claim_basis"]["scope"]
    assessment = {"assessment_id": "EFFECT-G2", "kind": "effect", "record": {
        "treatment_version": scope["object"], "estimand": "registered controlled contrast",
        "population": scope["population"], "outcome": scope["target"], "window": scope["window"],
        "scale": "registered-team", "identification_assumptions": ["registered controlled inputs"],
        "identification_claim_ids": ["CLAIM-FACTUAL"], "mechanism_claim_ids": ["CLAIM-MECHANISM"],
        "transport_claim_ids": [], "measured_dimensions": {}}}
    return qualified, empirical, [assessment]


def recompute(api, graph, empirical, assessments, *, derived=()):
    return api.recompute_causal_results_v4(assessments, graph=graph, empirical_instances=empirical,
        derived_instances=derived, mode="open-world", repository_root=ROOT)


def test_real_g2_qualified_graph_keeps_total_effect_after_local_mechanism_failure(api):
    graph, empirical, assessments = inputs()
    before = deepcopy((graph, empirical, assessments))
    result = recompute(api, graph, empirical, assessments)
    json.dumps(result, allow_nan=False)
    assert set(result) == {"claim_graph_sha256", "assessments_sha256", "assessments", "empirical_instances", "derived_instances"}
    assert result["claim_graph_sha256"] == sha256_json(graph)
    assert result["claim_graph_sha256"] != sha256_json(claim_graph_input(graph))
    assert result["assessments_sha256"] == sha256_json(assessments)
    effect = result["assessments"][0]["result"]
    assert effect["total_effect"] == "supported"
    assert effect["mechanism"] == effect["transport"] == "unsupported_or_undecided"
    assert result["empirical_instances"][0]["qualification"] == "qualified"
    assert result["empirical_instances"][0]["result"]["result_state"] == "supported"
    assert (graph, empirical, assessments) == before


def test_actual_registry_supplies_formal_premise_to_causal_constraints(api):
    graph, empirical, assessments = inputs(hard_root=True)
    assessments.append({"assessment_id": "MEASURE-ROOT", "kind": "measurement", "record": {
        "construct": "registered structural use", "indicator": "task delay", "indicator_role": "direct_record",
        "unit": "hours", "version": "v1", "selection_mechanism": "registered team",
        "recording_mechanism": "registered observations", "reporting_mechanism": "all outcomes",
        "indicator_claim_ids": ["CLAIM-FACTUAL"], "construct_claim_ids": ["CLAIM-STRUCTURAL"],
        "cross_group_comparison": False, "cross_time_comparison": False}})
    result = recompute(api, graph, empirical, assessments)
    assert result["assessments"][1]["result"]["construct"] == "supported"
    registry = rebuild_instance_registry(empirical, graph=graph, repository_root=ROOT)
    frozen = [{"frozen": freeze_empirical_instance(item["preregistration"]), "evaluation": item["evaluation"]} for item in empirical]
    assert claims.validate_causal_assessments(assessments, claim_mechanism_graph=graph,
        empirical_instances=frozen, repository_root=ROOT, verified_instance_results=registry) == result
    with pytest.raises(claims.ClaimMechanismError, match="registry|verified|evaluated"):
        claims.validate_causal_assessments(assessments, claim_mechanism_graph=graph,
            empirical_instances=frozen, repository_root=ROOT, verified_instance_results=dict(registry))


def test_changed_prerequisite_rejects_stale_qualified_graph_but_preserves_ordinary_effect_after_rebinding(api):
    graph, empirical, assessments = inputs()
    empirical[0]["evaluation"]["prerequisite_claim_ids"] = {}
    with pytest.raises(ValueError):
        recompute(api, graph, empirical, assessments)
    unqualified = bind_formal_claim_results(claim_graph_input(graph), empirical_instances=empirical,
        repository_root=ROOT)["claim_mechanism_graph"]
    result = recompute(api, unqualified, empirical, assessments)
    assert unqualified["claims"][0]["formal_qualification"]["status"] == "unqualified"
    assert result["empirical_instances"][0]["qualification"] == "unqualified"
    assert result["assessments"][0]["result"]["total_effect"] == "supported"
    assert result["assessments"][0]["result"]["mechanism"] == "unsupported_or_undecided"


@pytest.mark.parametrize("change", ["scope", "normative_basis", "family", "model_material"])
def test_original_scope_basis_family_and_material_rules_remain_authoritative(api, change):
    graph, empirical, assessments = inputs()
    if change == "scope":
        assessments[0]["record"]["population"] = "another population"
    elif change == "normative_basis":
        assessments[0]["record"]["identification_claim_ids"] = ["CLAIM-VALUE"]
    elif change == "family":
        empirical[0]["preregistration"]["root_id"] = "G4"
    else:
        graph["evidence"][0]["identity"] = "model-candidate"
    with pytest.raises(ValueError):
        recompute(api, graph, empirical, assessments)


@pytest.mark.parametrize("change", ["record_result", "envelope_result", "instance_result", "duplicate_id"])
def test_cached_outcomes_and_duplicate_ids_cannot_enter_semantic_inputs(api, change):
    graph, empirical, assessments = inputs()
    if change == "record_result":
        assessments[0]["record"]["total_effect"] = "supported"
    elif change == "envelope_result":
        assessments[0]["result"] = {"total_effect": "supported"}
    elif change == "instance_result":
        empirical[0]["qualification"] = "qualified"
    else:
        assessments.append(deepcopy(assessments[0]))
    with pytest.raises(ValueError):
        recompute(api, graph, empirical, assessments)


def test_all_six_native_record_shapes_recompute_without_word_quota_or_output_flags(api):
    from xi_kari_runtime.causality import freeze_history_contract
    graph, empirical, assessments = inputs()
    evaluation = history_result()
    evaluation.update(out_of_sample_claim_ids=["CLAIM-FACTUAL"], analysis_artifact_claim_ids=["CLAIM-FACTUAL"])
    assessments.extend([
        {"assessment_id": "HISTORY", "kind": "history", "record": {"frozen_contract": freeze_history_contract(history_contract()),
            "evaluation": evaluation, "ordinary_history_claim_ids": ["CLAIM-FACTUAL"]}},
        {"assessment_id": "FEEDBACK", "kind": "feedback", "record": {"receipt_claim_ids": ["CLAIM-FACTUAL"],
            "institutional_writeback_claim_ids": ["CLAIM-STRUCTURAL"]}},
        {"assessment_id": "MEASUREMENT", "kind": "measurement", "record": {"construct": "performance", "indicator": "delay",
            "indicator_role": "direct_record", "unit": "hours", "version": "v1", "selection_mechanism": "registered team",
            "recording_mechanism": "observation", "reporting_mechanism": "all cases", "indicator_claim_ids": ["CLAIM-FACTUAL"],
            "construct_claim_ids": ["CLAIM-FACTUAL"], "cross_group_comparison": False, "cross_time_comparison": False}},
        {"assessment_id": "PROPAGATION", "kind": "propagation", "record": {"hops": [{"from_id": "A", "to_id": "B",
            "channel": "handoff", "window": "January", "temporal_claim_ids": [], "causal_claim_ids": []}],
            "common_cause_claim_ids": ["CLAIM-FACTUAL"], "ordinary_externality_claim_ids": ["CLAIM-STRUCTURAL"],
            "formal_c7_instance_id": None}},
        {"assessment_id": "RECOVERY", "kind": "recovery", "record": {"function": "task completion", "population": "registered team",
            "window": "January", "support_conditions": ["temporary support"], "function_claim_ids": ["CLAIM-FACTUAL"],
            "sustainability_claim_ids": [], "unexperienced_conditions": ["different load"], "backup_count": 0}},
    ])
    result = recompute(api, graph, empirical, assessments)
    assert [row["kind"] for row in result["assessments"]] == ["effect", "history", "feedback", "measurement", "propagation", "recovery"]
    assert result["assessments"][1]["result"]["ordinary_history"] == "supported"
    assert result["assessments"][1]["result"]["formal_result"] == "unsupported_or_undecided"
    assert result["assessments"][2]["result"]["cm_learning"] == "unsupported_or_undecided"
    assert result["assessments"][4]["result"]["cascade"] == "unsupported_or_undecided"
    assert result["assessments"][5]["result"]["function_recovery"] == "supported"


def test_fresh_process_rejects_changed_disk_prerequisite_after_success(api, tmp_path):
    graph, empirical, assessments = inputs()
    for name, value in (("graph.json", graph), ("instances.json", empirical), ("assessments.json", assessments)):
        (tmp_path / name).write_text(json.dumps(value), encoding="utf-8")
    program = "import json,sys;from pathlib import Path;from xi_kari_runtime.causal_results_v4 import recompute_causal_results_v4;r=Path(sys.argv[1]);print(json.dumps(recompute_causal_results_v4(json.loads((r/'assessments.json').read_text()),graph=json.loads((r/'graph.json').read_text()),empirical_instances=json.loads((r/'instances.json').read_text()),mode='open-world',repository_root=Path(sys.argv[2]))))"
    command = [sys.executable, "-B", "-c", program, str(tmp_path), str(ROOT)]
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "scripts"), PYTHONDONTWRITEBYTECODE="1")
    before = subprocess.run(command, cwd=tmp_path, env=environment, capture_output=True, text=True)
    assert before.returncode == 0, before.stderr
    assert json.loads(before.stdout)["claim_graph_sha256"] == sha256_json(graph)
    empirical[0]["evaluation"]["prerequisite_claim_ids"] = {}
    (tmp_path / "instances.json").write_text(json.dumps(empirical), encoding="utf-8")
    after = subprocess.run(command, cwd=tmp_path, env=environment, capture_output=True, text=True)
    assert after.returncode != 0
    assert "formal" in after.stderr or "qualification" in after.stderr
