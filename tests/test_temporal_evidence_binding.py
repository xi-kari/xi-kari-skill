from copy import deepcopy
from importlib import import_module
import json
from pathlib import Path
import subprocess
import sys

import pytest

from tests.test_causal_judgment_effects import history_contract, history_result
from tests.test_causal_judgment_instances import root_contract, root_result
from tests.temporal_materials import record_temporal_inputs


def _support():
    return {ref: {"blocked": False} for ref in (
        "experiment", "analysis", "null-analysis", "training", "conditional-test",
    )}


def test_author_dates_and_status_do_not_prove_empirical_preregistration():
    instances = import_module("xi_kari_runtime.empirical_instances")
    checked = instances.evaluate_empirical_instance(
        instances.freeze_empirical_instance(root_contract()), root_result(),
        claim_constraints=_support(),
    )
    assert checked["qualification"] == "unqualified"
    assert checked["result"]["result_state"] == "unsupported_or_undecided"
    assert checked["measured_dimensions"]["delay"] == "supported"


def test_author_dates_do_not_prove_g3_but_preserve_ordinary_history():
    causal = import_module("xi_kari_runtime.causality")
    evaluation = history_result()
    evaluation["predictive_gain"] = 0.2
    checked = causal.assess_history(
        causal.freeze_history_contract(history_contract()), evaluation,
        claim_constraints=_support(), ordinary_history_claim_ids=["training"],
    )
    assert checked["formal_result"] == "unsupported_or_undecided"
    assert checked["ordinary_history"] == "supported"


def test_cached_temporal_flags_cannot_create_qualification():
    instances = import_module("xi_kari_runtime.empirical_instances")
    frozen = instances.freeze_empirical_instance(root_contract())
    frozen["temporal_audit"] = {"verified": True, "status": "verified"}
    frozen["qualification"] = "qualified"
    frozen["result"]["result_state"] = "supported"
    evaluation = deepcopy(root_result())
    evaluation["temporal_audit"] = {"verified": True, "status": "verified"}
    checked = instances.evaluate_empirical_instance(frozen, evaluation, claim_constraints=_support())
    assert checked["qualification"] == "unqualified"
    assert checked["result"]["result_state"] == "unsupported_or_undecided"


def _empirical(contract, evaluation, audit):
    instances = import_module("xi_kari_runtime.empirical_instances")
    return instances.evaluate_empirical_instance(
        instances.freeze_empirical_instance(contract), evaluation,
        claim_constraints=_support(), temporal_audit=audit,
    )


def test_actual_registration_reads_and_completion_bind_positive_result(tmp_path):
    contract, evaluation, audit = record_temporal_inputs(tmp_path, root_contract(), root_result())
    checked = _empirical(contract, evaluation, audit)
    assert checked["qualification"] == "qualified"
    assert checked["result"]["result_state"] == "supported"
    proof = checked["temporal_audit"]
    assert proof["status"] == "verified"
    assert proof["evidence_scope"] == "isolated_runtime_reads"
    assert proof["registration_event_id"] < proof["first_access_event_id"] < proof["completion_event_id"]
    assert contract["preregistration_timestamp"] != root_contract()["preregistration_timestamp"]
    assert evaluation["first_result_access_timestamp"] != root_result()["first_result_access_timestamp"]


def test_first_access_is_global_across_claim_aliases(tmp_path):
    contract, evaluation, audit = record_temporal_inputs(tmp_path, root_contract(), root_result(), before_freeze=True)
    checked = _empirical(contract, evaluation, audit)
    assert checked["qualification"] == "unqualified"
    assert checked["result"]["result_state"] == "unsupported_or_undecided"
    assert checked["measured_dimensions"]["delay"] == "supported"


@pytest.mark.parametrize("material", ["preregistration.json", "result-evidence.json", "analysis.json", "evaluation.json", "temporal-audit/contracts/1.json", "temporal-audit/evaluations/4.json", "temporal-audit/audit.json"])
def test_disk_material_mutation_invalidates_an_already_loaded_audit(tmp_path, material):
    contract, evaluation, audit = record_temporal_inputs(tmp_path, root_contract(), root_result())
    assert _empirical(contract, evaluation, audit)["qualification"] == "qualified"
    path = audit.run_dir / material
    value = json.loads(path.read_text(encoding="utf-8"))
    value["changed"] = True
    path.write_text(json.dumps(value), encoding="utf-8")
    checked = _empirical(contract, evaluation, audit)
    assert checked["qualification"] == "unqualified"
    assert checked["temporal_audit"]["status"] == "unverified"


@pytest.mark.parametrize("change", ["contract_version", "time_window", "candidate_object_id", "decision_threshold", "metric", "evaluation_version", "claim_binding"])
def test_audit_cannot_be_reused_for_a_different_scope_or_result(tmp_path, change):
    contract, evaluation, audit = record_temporal_inputs(tmp_path, root_contract(), root_result())
    if change in {"contract_version", "time_window", "candidate_object_id"}:
        contract[change] += "-different"
    elif change == "decision_threshold":
        contract[change] = 0.01
    elif change == "metric":
        evaluation["metrics"]["controlled_perturbation_effect"] = 0.8
    elif change == "evaluation_version":
        evaluation["contract_version"] += "-different"
    else:
        evaluation["evidence_claim_ids"] = ["training"]
    assert _empirical(contract, evaluation, audit)["qualification"] == "unqualified"


def test_dictionary_copy_of_a_verified_audit_cannot_authorize(tmp_path):
    contract, evaluation, audit = record_temporal_inputs(tmp_path, root_contract(), root_result())
    proof = _empirical(contract, evaluation, audit)["temporal_audit"]
    assert proof["status"] == "verified"
    assert _empirical(contract, evaluation, proof)["qualification"] == "unqualified"


def test_actual_null_result_needs_both_temporal_binding_and_null_gates(tmp_path):
    evaluation = root_result()
    evaluation["metrics"].update(controlled_perturbation_effect=0.01, **{"equivalence-upper": 0.02})
    contract, evaluation, audit = record_temporal_inputs(tmp_path, root_contract(), evaluation)
    assert _empirical(contract, evaluation, audit)["result"]["result_state"] == "null_supported"
    assert _empirical(contract, evaluation, None)["result"]["result_state"] == "unsupported_or_undecided"


def test_actual_history_audit_and_missing_audit_keep_ordinary_result_separate(tmp_path):
    causal = import_module("xi_kari_runtime.causality")
    evaluation = history_result()
    evaluation["predictive_gain"] = 0.2
    contract, evaluation, audit = record_temporal_inputs(tmp_path, history_contract(), evaluation, kind="history")
    frozen = causal.freeze_history_contract(contract)
    checked = causal.assess_history(frozen, evaluation, claim_constraints=_support(), ordinary_history_claim_ids=["training"], temporal_audit=audit)
    assert (checked["formal_result"], checked["ordinary_history"]) == ("supported", "supported")
    (audit.run_dir / "result-evidence.json").unlink()
    checked = causal.assess_history(frozen, evaluation, claim_constraints=_support(), ordinary_history_claim_ids=["training"], temporal_audit=audit)
    assert (checked["formal_result"], checked["ordinary_history"]) == ("unsupported_or_undecided", "supported")


def test_missing_temporal_evidence_does_not_change_independent_total_effect():
    causal = import_module("xi_kari_runtime.causality")
    from tests.test_causal_judgment_effects import effect_record
    constraints = {ref: {"blocked": False} for ref in ("random-assignment", "mediator", "new-population", "delay")}
    checked = causal.assess_effect(effect_record(), claim_constraints=constraints)
    assert checked["total_effect"] == "supported"


def test_fresh_process_rereads_materials_and_runtime_pin(tmp_path):
    contract, evaluation, audit = record_temporal_inputs(tmp_path, root_contract(), root_result())
    inputs = audit.run_dir / "validation-inputs.json"
    inputs.write_text(json.dumps({"contract": contract, "evaluation": evaluation, "support": _support()}), encoding="utf-8")
    script = """import json,sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from xi_kari_runtime.temporal_audit import load_temporal_audit,TemporalAuditError
from xi_kari_runtime.empirical_instances import freeze_empirical_instance,evaluate_empirical_instance
run=Path(sys.argv[2]); data=json.loads((run/'validation-inputs.json').read_text())
try:
 audit=load_temporal_audit(run,expected_audit_sha256=sys.argv[3])
except TemporalAuditError:
 audit=None
checked=evaluate_empirical_instance(freeze_empirical_instance(data['contract']),data['evaluation'],claim_constraints=data['support'],temporal_audit=audit)
print(checked['qualification'])
"""
    command = [sys.executable, "-c", script, str(Path(__file__).resolve().parents[1] / "scripts"), str(audit.run_dir), audit.expected_audit_sha256]
    assert subprocess.check_output(command, text=True).strip() == "qualified"
    (audit.run_dir / "analysis.json").write_text('{"synthetic": "changed"}', encoding="utf-8")
    assert subprocess.check_output(command, text=True).strip() == "unqualified"


def test_run_copy_cannot_replay_another_run_audit(tmp_path):
    import shutil
    from xi_kari_runtime.temporal_audit import load_temporal_audit, TemporalAuditError
    _, _, audit = record_temporal_inputs(tmp_path, root_contract(), root_result())
    other = tmp_path / "another-run"
    shutil.copytree(audit.run_dir, other)
    with pytest.raises(TemporalAuditError, match="identity"):
        load_temporal_audit(other, expected_audit_sha256=audit.expected_audit_sha256)


def test_missing_unrelated_material_does_not_retract_an_independent_instance(tmp_path):
    from xi_kari_runtime.canonical_json import atomic_write_json
    from xi_kari_runtime.temporal_audit import TemporalAuditWriter
    run = tmp_path / "two-instances"
    writer = TemporalAuditWriter(run)
    registrations, evaluations = {}, {}
    for suffix in ("A", "B"):
        contract, evaluation = root_contract(), root_result()
        contract["instance_id"] += suffix
        for field in ("evidence_claim_ids", "analysis_artifact_claim_ids"):
            evaluation[field] = [suffix]
        evaluation["prerequisite_claim_ids"] = {key: [suffix] for key in evaluation["prerequisite_claim_ids"]}
        evaluation["null_gate_claim_ids"] = {key: [suffix] for key in evaluation["null_gate_claim_ids"]}
        evaluation["dimension_claim_ids"] = {"delay": [suffix]}
        atomic_write_json(run / (suffix + "-contract.json"), contract)
        atomic_write_json(run / (suffix + "-result.json"), evaluation)
        registrations[suffix] = writer.freeze_preregistration(suffix + "-contract.json", kind="empirical")
        writer.read_material(suffix + "-result.json", claim_ids=[suffix], role="evidence")
        writer.read_material(suffix + "-result.json", claim_ids=[suffix], role="analysis")
        evaluations[suffix] = writer.complete_evaluation(contract["instance_id"], suffix + "-result.json")
    audit = writer.seal()
    instances = import_module("xi_kari_runtime.empirical_instances")
    def check(suffix):
        return instances.evaluate_empirical_instance(instances.freeze_empirical_instance(registrations[suffix]), evaluations[suffix], claim_constraints={"A": {"blocked": False}, "B": {"blocked": False}}, temporal_audit=audit)
    assert check("A")["qualification"] == check("B")["qualification"] == "qualified"
    (run / "A-result.json").unlink()
    assert check("A")["qualification"] == "unqualified"
    assert check("B")["qualification"] == "qualified"


def test_first_access_is_retained_across_identical_file_copies(tmp_path):
    from xi_kari_runtime.canonical_json import atomic_write_json
    from xi_kari_runtime.temporal_audit import TemporalAuditWriter
    run = tmp_path / "aliases"
    writer = TemporalAuditWriter(run)
    contract, evaluation = root_contract(), root_result()
    atomic_write_json(run / "old-name.json", evaluation)
    atomic_write_json(run / "new-name.json", evaluation)
    atomic_write_json(run / "contract.json", contract)
    writer.read_material("old-name.json", claim_ids=["unrelated-label"], role="evidence")
    registered = writer.freeze_preregistration("contract.json", kind="empirical")
    writer.read_material("new-name.json", claim_ids=["experiment", "analysis", "null-analysis"], role="evidence")
    writer.read_material("new-name.json", claim_ids=["experiment", "analysis", "null-analysis"], role="analysis")
    completed = writer.complete_evaluation(contract["instance_id"], "new-name.json")
    assert _empirical(registered, completed, writer.seal())["qualification"] == "unqualified"


@pytest.mark.parametrize("change", ["exploratory", "deviation", "evaluation_deviation", "missing_identification"])
def test_real_temporal_proof_does_not_replace_other_empirical_gates(tmp_path, change):
    contract, evaluation = root_contract(), root_result()
    if change == "exploratory":
        contract["evidence_mode"] = "exploratory"
    elif change == "deviation":
        contract["deviation_record"] = ["changed registered target"]
    elif change == "evaluation_deviation":
        evaluation["deviation_record"] = ["changed registered analysis"]
    else:
        evaluation["prerequisite_claim_ids"].pop("identification")
    contract, evaluation, audit = record_temporal_inputs(tmp_path, contract, evaluation)
    checked = _empirical(contract, evaluation, audit)
    assert checked["temporal_audit"]["status"] == "verified"
    assert checked["qualification"] == "unqualified"


def test_missing_original_analysis_cannot_be_replaced_by_a_claim_id(tmp_path):
    from xi_kari_runtime.canonical_json import atomic_write_json
    from xi_kari_runtime.temporal_audit import TemporalAuditWriter, TemporalAuditError
    writer = TemporalAuditWriter(tmp_path / "incomplete")
    atomic_write_json(writer.run_dir / "contract.json", root_contract())
    atomic_write_json(writer.run_dir / "result.json", root_result())
    writer.freeze_preregistration("contract.json", kind="empirical")
    writer.read_material("result.json", claim_ids=["experiment", "analysis", "null-analysis"], role="evidence")
    with pytest.raises(TemporalAuditError, match="cover"):
        writer.complete_evaluation(root_contract()["instance_id"], "result.json")


def test_sealed_audit_does_not_accept_further_runtime_events(tmp_path):
    from xi_kari_runtime.temporal_audit import TemporalAuditWriter, TemporalAuditError
    writer = TemporalAuditWriter(tmp_path / "closed")
    writer.seal()
    with pytest.raises(TemporalAuditError, match="sealed"):
        writer.read_material("unread.json", claim_ids=["result"], role="evidence")
