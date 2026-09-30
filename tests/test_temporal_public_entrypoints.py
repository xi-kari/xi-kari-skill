from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from tests.test_p04_instance_results_v4 import requested_graph, instance_inputs
from tests.test_causal_judgment_v4_graph import empirical_graph
from tests.test_causal_judgment_effects import history_contract, history_result
from tests.test_v4_stage_chain_integration import static_inputs
from tests.temporal_materials import record_temporal_inputs
from xi_kari_runtime import claims
from xi_kari_runtime.causality import freeze_history_contract
from xi_kari_runtime.causal_results_v4 import recompute_causal_results_v4
from xi_kari_runtime.empirical_instances import freeze_empirical_instance
from xi_kari_runtime.formal_results import bind_formal_claim_results, rebuild_instance_registry
from xi_kari_runtime.stage_consumers_v4 import validate_stage_chain_v4
from xi_kari_runtime.temporal_audit import SCHEMA_ID


def observed_inputs(tmp_path, *, human=False):
    graph = requested_graph()
    raw = instance_inputs()[0]
    if human:
        raw["preregistration"].pop("root_id")
        raw["preregistration"].update(claim_id="H1", selected_subtype="H1-coordination-outcome",
            selected_success_criterion="meaning_arrangement_coordination_outcome_effect",
            evaluation_metric="meaning_arrangement_coordination_outcome_effect",
            candidate_specification={"meaning_arrangement": "synthetic-public-arrangement"})
        raw["evaluation"]["metrics"]["meaning_arrangement_coordination_outcome_effect"] = 0.2
        raw["evaluation"]["prerequisite_claim_ids"] = {key: ["CLAIM-FACTUAL"] for key in (
            "selected_meaning_arrangement", "identification", "measurement_protocol")}
        graph["claims"][0]["formal_qualification"].update(family="H", concept_ref="V90-CANON-H1")
    contract, evaluation, audit = record_temporal_inputs(tmp_path, raw["preregistration"], raw["evaluation"])
    return graph, [{"preregistration": contract, "evaluation": evaluation}], audit


@pytest.mark.parametrize("human", [False, True])
def test_public_formal_binder_uses_actual_audit_and_locally_withdraws_changed_material(tmp_path, human):
    graph, inputs, audit = observed_inputs(tmp_path, human=human)
    before = bind_formal_claim_results(graph, empirical_instances=inputs, repository_root=ROOT, temporal_audit=audit)
    qualification = before["claim_mechanism_graph"]["claims"][0]["formal_qualification"]
    assert (qualification["status"], qualification["result_status"]) == ("qualified", "supported")
    registry = rebuild_instance_registry(inputs, graph=graph, repository_root=ROOT, temporal_audit=audit)
    identifier = inputs[0]["preregistration"]["instance_id"]
    assert registry[identifier]["formal_result"] == "supported"
    (audit.run_dir / "analysis.json").write_text('{"synthetic": "changed"}', encoding="utf-8")
    after = bind_formal_claim_results(graph, empirical_instances=inputs, repository_root=ROOT, temporal_audit=audit)
    qualification = after["claim_mechanism_graph"]["claims"][0]["formal_qualification"]
    assert (qualification["status"], qualification["result_status"]) == ("unqualified", "unsupported_or_undecided")
    assert registry[identifier]["formal_result"] == "unsupported_or_undecided"
    assert claims.claim_constraints(after["claim_mechanism_graph"])["CLAIM-FACTUAL"]["blocked"] is False


def test_public_history_recomputation_preserves_ordinary_history_after_audit_failure(tmp_path):
    evaluation = history_result()
    evaluation.update(predictive_gain=0.2, out_of_sample_claim_ids=["CLAIM-FACTUAL"], analysis_artifact_claim_ids=["CLAIM-FACTUAL"])
    contract, evaluation, audit = record_temporal_inputs(tmp_path, history_contract(), evaluation, kind="history")
    assessments = [{"assessment_id": "HISTORY", "kind": "history", "record": {
        "frozen_contract": freeze_history_contract(contract), "evaluation": evaluation,
        "ordinary_history_claim_ids": ["CLAIM-FACTUAL"]}}]
    def run():
        return recompute_causal_results_v4(assessments, graph=empirical_graph(), mode="open-world", repository_root=ROOT, temporal_audit=audit)["assessments"][0]["result"]
    assert (run()["formal_result"], run()["ordinary_history"]) == ("supported", "supported")
    (audit.run_dir / "analysis.json").unlink()
    assert (run()["formal_result"], run()["ordinary_history"]) == ("unsupported_or_undecided", "supported")


def test_claim_validator_rejects_dictionary_proof_while_accepting_observed_materials(tmp_path):
    graph, inputs, audit = observed_inputs(tmp_path)
    frozen = [{"frozen": freeze_empirical_instance(row["preregistration"]), "evaluation": row["evaluation"]} for row in inputs]
    checked = claims.validate_empirical_instances(frozen, claim_mechanism_graph=graph, repository_root=ROOT, temporal_audit=audit)
    result = checked["instances"][0]
    assert result["qualification"] == "qualified"
    proof = deepcopy(result["temporal_audit"])
    denied = claims.validate_empirical_instances(frozen, claim_mechanism_graph=graph, repository_root=ROOT, temporal_audit=proof)
    assert denied["instances"][0]["qualification"] == "unqualified"


def test_stage_controls_contain_serializable_binding_without_original_audit_content(tmp_path):
    _, _, audit = observed_inputs(tmp_path)
    packet, contract = static_inputs()
    result = validate_stage_chain_v4(packet, run_contract=contract, repository_root=ROOT, temporal_audit=audit)
    summary = result["temporal_audit_binding"]
    assert summary == {"status": "supplied", "audit_sha256": audit.expected_audit_sha256, "evidence_scope": "isolated_runtime_reads"}
    serialized = json.dumps(result, ensure_ascii=False)
    assert str(audit.run_dir) not in serialized
    assert "preregistration.json" not in serialized
    assert "events" not in summary


def test_temporal_schema_has_an_explicit_runtime_owner(tmp_path):
    import check_xi_kari_runtime as checker
    graph, inputs, audit = observed_inputs(tmp_path)
    registry, errors = checker._runtime_schema_registry(ROOT)
    assert errors == []
    assert SCHEMA_ID in registry
    document = json.loads((audit.run_dir / "temporal-audit/audit.json").read_text(encoding="utf-8"))
    assert list(registry[SCHEMA_ID].iter_errors(document)) == []
    document["events"][0]["contract_sha256"] = "not-a-hash"
    assert list(registry[SCHEMA_ID].iter_errors(document))


def test_public_scale_root_binder_receives_audit_and_rechecks_loaded_registry(tmp_path):
    from tests.test_p06_empirical_root_binding import empirical_scale_fixture
    from xi_kari_runtime.transformations import bind_scale_root_instances
    record, _, frozen, graph, objects = empirical_scale_fixture()
    contract, evaluation, audit = record_temporal_inputs(tmp_path, frozen[0]["frozen"]["preregistration"], frozen[0]["evaluation"])
    frozen = [{"frozen": freeze_empirical_instance(contract), "evaluation": evaluation}]
    def bind():
        return bind_scale_root_instances(record, instance_inputs=frozen, claim_mechanism_graph=graph, object_contracts=objects, temporal_audit=audit)
    registry = bind()["root_instances"]
    assert registry["ROOT-1"]["eligibility_status"] == "eligible"
    (audit.run_dir / "analysis.json").unlink()
    assert registry["ROOT-1"]["eligibility_status"] == "ineligible"
    assert bind()["root_instances"]["ROOT-1"]["result_state"] == "unsupported_or_undecided"


def test_stage_chain_passes_actual_audit_into_its_scale_root_consumer(tmp_path):
    from tests.test_v4_stage_chain_integration import empirical_scale_inputs
    packet, run_contract = empirical_scale_inputs()
    original = packet["empirical_instances"][0]
    contract, evaluation, audit = record_temporal_inputs(tmp_path, original["preregistration"], original["evaluation"])
    packet["empirical_instances"] = [{"preregistration": contract, "evaluation": evaluation}]
    result = validate_stage_chain_v4(packet, run_contract=run_contract, repository_root=ROOT, temporal_audit=audit)
    roots = result["stage_results"]["transformation"]["result"]["root_results"][0]
    identifier = contract["instance_id"]
    assert roots[identifier]["eligibility_status"] == "eligible"
    (audit.run_dir / "analysis.json").unlink()
    changed = validate_stage_chain_v4(packet, run_contract=run_contract, repository_root=ROOT, temporal_audit=audit)
    assert changed["stage_results"]["transformation"]["result"]["root_results"][0][identifier]["eligibility_status"] == "ineligible"


def test_missing_audit_from_public_binder_preserves_ordinary_effect(tmp_path):
    graph, inputs, _ = observed_inputs(tmp_path)
    rebound = bind_formal_claim_results(graph, empirical_instances=inputs, repository_root=ROOT)
    graph = rebound["claim_mechanism_graph"]
    scope = graph["claims"][0]["claim_basis"]["scope"]
    assessment = {"assessment_id": "ORDINARY", "kind": "effect", "record": {
        "treatment_version": scope["object"], "estimand": "controlled contrast",
        "population": scope["population"], "outcome": scope["target"], "window": scope["window"],
        "scale": "registered-team", "identification_assumptions": ["bounded controlled input"],
        "identification_claim_ids": ["CLAIM-FACTUAL"], "mechanism_claim_ids": [],
        "transport_claim_ids": [], "measured_dimensions": {}}}
    result = recompute_causal_results_v4([assessment], graph=graph, empirical_instances=inputs,
        mode="open-world", repository_root=ROOT)
    assert result["empirical_instances"][0]["qualification"] == "unqualified"
    assert result["assessments"][0]["result"]["total_effect"] == "supported"
