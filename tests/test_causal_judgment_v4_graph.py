from copy import deepcopy
from pathlib import Path
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from tests.test_p04_v4_claim_contracts import _v4_graph
from xi_kari_runtime import claims


def effect_graph():
    graph = _v4_graph()
    primary = graph["claims"][0]
    primary["claim_basis"] = {"kind": "domain_empirical", "scope": {"object": "synthetic-offer-v1", "population": "synthetic-enrollees", "window": "six-weeks", "target": "score"}, "material_refs": primary["evidence_refs"]}
    for row in graph["claims"]:
        row["formal_qualification"].update(requested=False, family="not_applicable", concept_ref=None, instance_refs=[], status="not_requested", result_status="not_evaluated")
    record = {"assessment_id": "synthetic-effect-1", "kind": "effect", "record": {"treatment_version": "synthetic-offer-v1", "estimand": "intention_to_treat", "population": "synthetic-enrollees", "outcome": "score", "window": "six-weeks", "scale": "individual", "identification_assumptions": ["random-assignment"], "identification_claim_ids": [primary["claim_id"]], "mechanism_claim_ids": ["CLAIM-MECHANISM"], "transport_claim_ids": [], "measured_dimensions": {}}}
    return graph, record


def empirical_graph():
    graph, _ = effect_graph()
    graph["claims"][0]["statement"] = "Synthetic controlled handoff delay experiment in its registered team and January window."
    graph["claims"][0]["claim_basis"]["scope"] = {"object": "synthetic-object", "population": "registered-team", "window": "January", "target": "task-delay"}
    return graph


def test_real_v4_graph_preserves_total_effect_after_local_mechanism_failure():
    graph, record = effect_graph()
    next(evidence for evidence in graph["evidence"] if evidence["evidence_id"] == "E-MECHANISM")["support_status"] = "invalidated"
    result = claims.validate_causal_assessments([record], claim_mechanism_graph=graph)
    assert result["assessments"][0]["result"]["total_effect"] == "supported"
    assert result["assessments"][0]["result"]["mechanism"] == "unsupported_or_undecided"


@pytest.mark.parametrize("change", ["simulated", "definition", "wrong-scope", "empty-support"])
def test_causal_total_effect_cannot_be_laundered_from_wrong_evidence_scope(change):
    graph, record = effect_graph()
    if change == "simulated":
        graph["evidence"][0]["identity"] = "simulated-result"
    elif change == "definition":
        graph["claims"][0]["claim_basis"]["kind"] = "formal_proof"
    elif change == "wrong-scope":
        record["record"]["population"] = "unregistered-population"
    else:
        graph["claims"][0]["evidence_refs"] = []
    with pytest.raises(claims.ClaimMechanismError):
        claims.validate_causal_assessments([record], claim_mechanism_graph=graph)


def test_fresh_process_recomputes_causal_support_from_disk(tmp_path):
    graph, record = effect_graph()
    graph_path, record_path = tmp_path / "graph.json", tmp_path / "causal.json"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    record_path.write_text(json.dumps([record]), encoding="utf-8")
    program = "import json,sys; from scripts.xi_kari_runtime.claims import validate_causal_assessments; from pathlib import Path; print(json.dumps(validate_causal_assessments(json.loads(Path(sys.argv[2]).read_text()),claim_mechanism_graph=json.loads(Path(sys.argv[1]).read_text()))))"
    def fresh():
        process = subprocess.run([sys.executable, "-B", "-c", program, str(graph_path), str(record_path)], cwd=Path(__file__).resolve().parents[1], env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, text=True, capture_output=True, check=True)
        return json.loads(process.stdout)
    before = fresh()
    graph["evidence"][0]["support_checks"]["world_fact_supported"]["status"] = "failed"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    after = fresh()
    assert before["assessments"][0]["result"]["total_effect"] == "supported"
    assert after["assessments"][0]["result"]["total_effect"] == "unsupported_or_undecided"
    assert before["claim_graph_sha256"] != after["claim_graph_sha256"]


def test_actual_empirical_instance_uses_v4_material_identity_and_checks():
    from tests.test_causal_judgment_instances import root_contract, root_result
    from xi_kari_runtime.empirical_instances import freeze_empirical_instance
    graph = empirical_graph()
    evaluation = root_result()
    evaluation["evidence_claim_ids"] = ["CLAIM-FACTUAL"]
    evaluation["analysis_artifact_claim_ids"] = ["CLAIM-FACTUAL"]
    evaluation["prerequisite_claim_ids"] = {key: ["CLAIM-FACTUAL"] for key in evaluation["prerequisite_claim_ids"]}
    evaluation["null_gate_claim_ids"] = {key: ["CLAIM-FACTUAL"] for key in evaluation["null_gate_claim_ids"]}
    evaluation["dimension_claim_ids"] = {"delay": ["CLAIM-FACTUAL"]}
    bundle = [{"frozen": freeze_empirical_instance(root_contract()), "evaluation": evaluation}]
    checked = claims.validate_empirical_instances(bundle, claim_mechanism_graph=graph)
    assert checked["instances"][0]["result"]["result_state"] == "supported"
    assert set(checked["instances"][0]["measured_dimensions"]) == {"delay"}
    graph["evidence"][0]["identity"] = "simulated-result"
    with pytest.raises(claims.ClaimMechanismError, match="empirical"):
        claims.validate_empirical_instances(bundle, claim_mechanism_graph=graph)


def test_nested_identification_check_cannot_use_a_normative_argument_as_empirical_evidence():
    from tests.test_causal_judgment_instances import root_contract, root_result
    from xi_kari_runtime.empirical_instances import freeze_empirical_instance
    graph = empirical_graph()
    evaluation = root_result()
    evaluation.update(evidence_claim_ids=["CLAIM-FACTUAL"], analysis_artifact_claim_ids=["CLAIM-FACTUAL"], prerequisite_claim_ids={key: ["CLAIM-FACTUAL"] for key in evaluation["prerequisite_claim_ids"]}, dimension_claim_ids={"delay": ["CLAIM-FACTUAL"]}, null_gate_claim_ids={key: ["CLAIM-FACTUAL"] for key in evaluation["null_gate_claim_ids"]})
    evaluation["prerequisite_claim_ids"]["common_inputs"] = ["CLAIM-VALUE"]
    with pytest.raises(claims.ClaimMechanismError, match="empirical"):
        claims.validate_empirical_instances([{"frozen": freeze_empirical_instance(root_contract()), "evaluation": evaluation}], claim_mechanism_graph=graph)


def test_passed_instance_target_marker_cannot_manufacture_a_hard_root_premise():
    graph, _ = effect_graph()
    graph["dependency_edges"].append({"edge_id": "EDGE-FORMAL-ROOT", "from_id": "CLAIM-STRUCTURAL", "to_ref": {"kind": "instance", "id": "INSTANCE-NOT-ACTUALLY-EVALUATED"}, "role": "inferential_requires", "source_refs": ["V90-P00158"], "condition": "Selected formal root route", "scope": "formal effect only"})
    graph["dependency_targets"] = [{"kind": "instance", "id": "INSTANCE-NOT-ACTUALLY-EVALUATED", "status": "passed", "reason": "A self-declared marker"}]
    checked = claims.validate_claim_graph(graph)
    result = claims.claim_constraints(checked)
    assert result["CLAIM-STRUCTURAL"]["blocked"] is True
    assert result["CLAIM-FACTUAL"]["blocked"] is False


def test_plain_cached_result_dictionary_is_not_an_evaluated_instance_registry():
    graph, _ = effect_graph()
    forged = {"FAKE": {"instance_id": "FAKE", "qualification": "qualified", "formal_result": "supported"}}
    with pytest.raises(claims.ClaimMechanismError, match="evaluated"):
        claims.claim_constraints(claims.validate_claim_graph(graph), verified_instance_results=forged)


def test_recomputed_registry_can_supply_a_real_root_premise_and_detects_graph_change():
    from tests.test_causal_judgment_instances import root_contract, root_result
    from xi_kari_runtime.empirical_instances import EvaluatedInstanceRegistry, freeze_empirical_instance
    graph = empirical_graph()
    instance_id = root_contract()["instance_id"]
    graph["dependency_edges"].append({"edge_id": "EDGE-ACTUAL-ROOT", "from_id": "CLAIM-STRUCTURAL", "to_ref": {"kind": "instance", "id": instance_id}, "role": "inferential_requires", "source_refs": ["V90-P00158"], "condition": "Selected registered G2", "scope": "Formal effect only"})
    graph["dependency_targets"] = [{"kind": "instance", "id": instance_id, "status": "not_run", "reason": "Code must evaluate the real root"}]
    evaluation = root_result()
    evaluation.update(evidence_claim_ids=["CLAIM-FACTUAL"], analysis_artifact_claim_ids=["CLAIM-FACTUAL"], prerequisite_claim_ids={key: ["CLAIM-FACTUAL"] for key in evaluation["prerequisite_claim_ids"]}, dimension_claim_ids={"delay": ["CLAIM-FACTUAL"]}, null_gate_claim_ids={key: ["CLAIM-FACTUAL"] for key in evaluation["null_gate_claim_ids"]})
    registry = EvaluatedInstanceRegistry([{"frozen": freeze_empirical_instance(root_contract()), "evaluation": evaluation}], graph=graph)
    assert claims.claim_constraints(graph, verified_instance_results=registry)["CLAIM-STRUCTURAL"]["blocked"] is False
    graph["evidence"][0]["support_checks"]["world_fact_supported"]["status"] = "failed"
    with pytest.raises(claims.ClaimMechanismError, match="same graph"):
        claims.claim_constraints(graph, verified_instance_results=registry)


def test_instance_scope_mismatch_cannot_be_cured_by_passed_world_checks():
    from tests.test_causal_judgment_instances import root_contract, root_result
    from xi_kari_runtime.empirical_instances import freeze_empirical_instance
    graph, _ = effect_graph()
    evaluation = root_result()
    evaluation.update(evidence_claim_ids=["CLAIM-FACTUAL"], analysis_artifact_claim_ids=["CLAIM-FACTUAL"], prerequisite_claim_ids={key: ["CLAIM-FACTUAL"] for key in evaluation["prerequisite_claim_ids"]}, dimension_claim_ids={"delay": ["CLAIM-FACTUAL"]}, null_gate_claim_ids={key: ["CLAIM-FACTUAL"] for key in evaluation["null_gate_claim_ids"]})
    with pytest.raises(claims.ClaimMechanismError, match="scope"):
        claims.validate_empirical_instances([{"frozen": freeze_empirical_instance(root_contract()), "evaluation": evaluation}], claim_mechanism_graph=graph)
