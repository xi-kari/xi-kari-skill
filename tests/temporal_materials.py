"""Synthetic original materials observed through the actual run-local reader."""

from pathlib import Path
import tempfile

from xi_kari_runtime.canonical_json import atomic_write_json, sha256_json
from xi_kari_runtime.temporal_audit import TemporalAuditWriter


def _claim_ids(value):
    if isinstance(value, dict):
        return set().union(*(_claim_ids(item) for item in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(_claim_ids(item) for item in value)) if value else set()
    return {value} if isinstance(value, str) else set()


def record_temporal_inputs(tmp_path, contract, evaluation, *, kind="empirical", before_freeze=False):
    run_dir = Path(tempfile.mkdtemp(prefix="temporal-", dir=tmp_path))
    atomic_write_json(run_dir / "preregistration.json", contract)
    atomic_write_json(run_dir / "result-evidence.json", {"synthetic": True, "observations": evaluation})
    atomic_write_json(run_dir / "analysis.json", {"synthetic": True, "analysis": evaluation})
    atomic_write_json(run_dir / "evaluation.json", evaluation)
    writer = TemporalAuditWriter(run_dir)
    if before_freeze:
        writer.read_material("result-evidence.json", claim_ids=["previous-reader"], role="evidence")
    registered = writer.freeze_preregistration("preregistration.json", kind=kind)
    refs = set().union(*(_claim_ids(value) for key, value in evaluation.items() if key.endswith("claim_ids")))
    writer.read_material("result-evidence.json", claim_ids=sorted(refs), role="evidence")
    writer.read_material("analysis.json", claim_ids=sorted(refs), role="analysis")
    completed = writer.complete_evaluation(contract["instance_id"], "evaluation.json")
    return registered, completed, writer.seal()


def evaluate_empirical_with_materials(tmp_path, frozen, evaluation, *, claim_constraints):
    from xi_kari_runtime.causality import CausalError
    from xi_kari_runtime.empirical_instances import freeze_empirical_instance, evaluate_empirical_instance
    if sha256_json(frozen["preregistration"]) != frozen["preregistration_sha256"]:
        raise CausalError("empirical preregistration changed")
    contract, evaluation, audit = record_temporal_inputs(tmp_path, frozen["preregistration"], evaluation)
    return evaluate_empirical_instance(freeze_empirical_instance(contract), evaluation, claim_constraints=claim_constraints, temporal_audit=audit)


def assess_history_with_materials(tmp_path, frozen, evaluation, *, claim_constraints, ordinary_history_claim_ids):
    from xi_kari_runtime.causality import CausalError, freeze_history_contract, assess_history
    if sha256_json(frozen["contract"]) != frozen["contract_sha256"]:
        raise CausalError("frozen history contract changed")
    contract, evaluation, audit = record_temporal_inputs(tmp_path, frozen["contract"], evaluation, kind="history")
    return assess_history(freeze_history_contract(contract), evaluation, claim_constraints=claim_constraints, ordinary_history_claim_ids=ordinary_history_claim_ids, temporal_audit=audit)
