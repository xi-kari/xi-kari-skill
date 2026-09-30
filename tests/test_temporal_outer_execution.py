from copy import deepcopy
from importlib import import_module
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from tests.test_p04_instance_results_v4 import packet_inputs
from tests.temporal_materials import record_temporal_inputs
from tests.test_v4_semantic_executions import fixture_binding
from xi_kari_runtime.canonical_json import sha256_json
from xi_kari_runtime.packet_v4 import prepare_analysis_packet_v4
from xi_kari_runtime.stage_consumers_v4 import validate_stage_chain_v4
from xi_kari_runtime.semantic_executions_v4 import (
    build_semantic_execution_request_v4, execute_semantic_request_v4,
    validate_semantic_execution_v4,
)


def observed_packet(tmp_path):
    semantic, contract = packet_inputs()
    row = semantic["empirical_instances"][0]
    preregistration, evaluation, audit = record_temporal_inputs(tmp_path, row["preregistration"], row["evaluation"])
    semantic["empirical_instances"] = [{"preregistration": preregistration, "evaluation": evaluation}]
    return semantic, contract, audit


def test_packet_outer_preparation_recomputes_real_audit_and_refuses_cached_proof(tmp_path):
    semantic, contract, audit = observed_packet(tmp_path)
    packet = prepare_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT, temporal_audit=audit)
    assert packet["claim_mechanism_graph"]["claims"][0]["formal_qualification"]["status"] == "qualified"
    denied = prepare_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT, temporal_audit={"verified": True})
    assert denied["claim_mechanism_graph"]["claims"][0]["formal_qualification"]["status"] == "unqualified"
    (audit.run_dir / "analysis.json").unlink()
    changed = prepare_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT, temporal_audit=audit)
    assert changed["claim_mechanism_graph"]["claims"][0]["formal_qualification"]["status"] == "unqualified"


def test_context_import_keeps_original_root_identity_and_exact_snapshot_bytes(tmp_path):
    context_api = import_module("xi_kari_runtime.temporal_context")
    _, contract, audit = observed_packet(tmp_path)
    context = context_api.freeze_temporal_context_v4(audit, run_id=contract["run_id"],
        problem_contract_sha256=contract["problem_contract_sha256"], repository_root=ROOT)
    run = tmp_path / "execution"
    context_api.persist_temporal_context_v4(context, run_dir=run, run_contract=contract)
    loaded = context_api.load_temporal_context_v4(run, run_contract=contract,
        expected_binding=context.binding, repository_root=ROOT)
    assert loaded.audit.run_dir == audit.run_dir
    assert loaded.audit.run_dir != run
    for relative in loaded.artifact_paths:
        assert (run / relative).is_file()
    snapshot = run / "temporal-evidence/source/analysis.json"
    assert snapshot.read_bytes() == (audit.run_dir / "analysis.json").read_bytes()
    snapshot.write_text('{"changed":true}', encoding="utf-8")
    with pytest.raises(ValueError):
        context_api.load_temporal_context_v4(run, run_contract=contract,
            expected_binding=context.binding, repository_root=ROOT)


def test_real_semantic_execution_signature_binds_temporal_pin_and_rereads_originals(tmp_path):
    semantic, contract, audit = observed_packet(tmp_path)
    packet = prepare_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT, temporal_audit=audit)
    controls = validate_stage_chain_v4(packet, run_contract=contract, repository_root=ROOT, temporal_audit=audit)
    request = build_semantic_execution_request_v4(packet, controls, run_contract=contract,
        kind="red_team", repository_root=ROOT, temporal_audit=audit)
    assert request["material_context"]["stage_controls"]["temporal_audit_binding"]["audit_sha256"] == audit.expected_audit_sha256
    binding = fixture_binding(tmp_path)
    execution = execute_semantic_request_v4(request, binding=binding, run_directory=tmp_path / "execution",
        repository_root=ROOT, temporal_audit=audit)
    assert execution["status"] == "executed"
    assert execution["receipt"]["signed_payload"]["bindings"]["base_information_sha256"] == sha256_json(request["material_context"])
    verified = validate_semantic_execution_v4(execution, expected_request=request,
        binding=binding, repository_root=ROOT, temporal_audit=audit)
    assert verified["status"] == "executed"
    (audit.run_dir / "analysis.json").write_text('{"changed":true}', encoding="utf-8")
    with pytest.raises(ValueError):
        validate_semantic_execution_v4(execution, expected_request=request,
            binding=binding, repository_root=ROOT, temporal_audit=audit)


def test_execute_default_selects_active_source_before_provider_launch(tmp_path, monkeypatch):
    from xi_kari_runtime import execution
    from tests.test_natural_contract_freeze import request_and_final
    _, problem = request_and_final()
    seen = []
    class StopBeforeReading(Exception):
        pass
    def observe_source(*args, **kwargs):
        seen.append(kwargs["source_version"])
        raise StopBeforeReading()
    monkeypatch.setattr(execution, "build_full_source_lock", observe_source)
    with pytest.raises(StopBeforeReading):
        execution.execute_authored_run(tmp_path / "runs", problem_contract=problem,
            repository_root=ROOT, codex_provider_executable=Path(sys.executable))
    assert seen == ["v9.0"]
    assert not (tmp_path / "runs").exists()


@pytest.mark.parametrize("selection", [{"source_version": "v8.3"}, {"contract_version": 3}])
def test_explicit_legacy_execution_is_rejected_before_any_provider_or_run_effect(tmp_path, monkeypatch, selection):
    from xi_kari_runtime import execution
    from tests.test_natural_contract_freeze import request_and_final
    _, problem = request_and_final()
    def forbidden(*args, **kwargs):
        raise AssertionError("provider binding was reached for a legacy execution")
    monkeypatch.setattr(execution, "bind_semantic_authoring_adapter", forbidden)
    with pytest.raises(ValueError, match="current|active|v9"):
        execution.execute_authored_run(tmp_path / "runs", problem_contract=problem,
            repository_root=ROOT, codex_provider_executable=Path(sys.executable), **selection)
    assert not (tmp_path / "runs").exists()


@pytest.mark.parametrize("change", ["original", "missing_origin", "descriptor", "audit", "extra_snapshot", "relocated_origin"])
def test_bound_context_cannot_restore_qualification_from_changed_or_relocated_materials(tmp_path, change):
    import shutil
    context_api = import_module("xi_kari_runtime.temporal_context")
    _, contract, audit = observed_packet(tmp_path)
    context = context_api.freeze_temporal_context_v4(audit, run_id=contract["run_id"],
        problem_contract_sha256=contract["problem_contract_sha256"], repository_root=ROOT)
    run = tmp_path / "bound"
    context_api.persist_temporal_context_v4(context, run_dir=run, run_contract=contract)
    binding = context.binding
    if change == "original":
        (audit.run_dir / "analysis.json").write_text('{"changed":true}', encoding="utf-8")
    elif change == "missing_origin":
        (audit.run_dir / "analysis.json").unlink()
    elif change == "audit":
        (audit.run_dir / "temporal-audit/audit.json").write_text('{}', encoding="utf-8")
    elif change == "extra_snapshot":
        (run / "temporal-evidence/source/unbound.json").write_text('{}', encoding="utf-8")
    else:
        path = run / context_api.CONTEXT_PATH
        descriptor = json.loads(path.read_text(encoding="utf-8"))
        if change == "relocated_origin":
            copied = tmp_path / "copy-of-origin"
            shutil.copytree(audit.run_dir, copied)
            descriptor["origin_run_directory"] = str(copied.resolve())
            descriptor["origin_run_path_sha256"] = sha256_json(str(copied.resolve()))
        else:
            descriptor["run_id"] = "wrong-run"
        path.write_text(json.dumps(descriptor), encoding="utf-8")
        if change == "relocated_origin":
            from xi_kari_runtime.canonical_json import sha256_file
            binding["context_sha256"] = sha256_file(path)
    with pytest.raises(ValueError, match="temporal"):
        context_api.load_temporal_context_v4(run, run_contract=contract, expected_binding=binding, repository_root=ROOT)


def test_context_binding_cannot_be_invented_by_author_json_or_an_unbound_descriptor(tmp_path):
    context_api = import_module("xi_kari_runtime.temporal_context")
    _, contract, audit = observed_packet(tmp_path)
    with pytest.raises(ValueError, match="author JSON"):
        context_api.freeze_temporal_context_v4({"verified": True}, run_id=contract["run_id"],
            problem_contract_sha256=contract["problem_contract_sha256"], repository_root=ROOT)
    run = tmp_path / "bound"
    assert context_api.load_temporal_context_v4(run, run_contract=contract, expected_binding=None, repository_root=ROOT) is None
    context = context_api.freeze_temporal_context_v4(audit, run_id=contract["run_id"],
        problem_contract_sha256=contract["problem_contract_sha256"], repository_root=ROOT)
    context_api.persist_temporal_context_v4(context, run_dir=run, run_contract=contract)
    with pytest.raises(ValueError, match="independent"):
        context_api.load_temporal_context_v4(run, run_contract=contract, expected_binding=None, repository_root=ROOT)


def test_semantic_pin_replacement_or_missing_runtime_object_fails_before_process(tmp_path):
    semantic, contract, audit = observed_packet(tmp_path)
    packet = prepare_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT, temporal_audit=audit)
    controls = validate_stage_chain_v4(packet, run_contract=contract, repository_root=ROOT, temporal_audit=audit)
    request = build_semantic_execution_request_v4(packet, controls, run_contract=contract,
        kind="red_team", repository_root=ROOT, temporal_audit=audit)
    for context in (None, {"verified": True, "audit_sha256": audit.expected_audit_sha256}):
        with pytest.raises(ValueError, match="temporal"):
            execute_semantic_request_v4(request, binding=None, run_directory=tmp_path / "not-created",
                repository_root=ROOT, temporal_audit=context)
    changed = deepcopy(request)
    changed["material_context"]["stage_controls"]["temporal_audit_binding"]["audit_sha256"] = "f" * 64
    changed["bindings"]["base_information_sha256"] = sha256_json(changed["material_context"])
    with pytest.raises(ValueError, match="temporal"):
        execute_semantic_request_v4(changed, binding=None, run_directory=tmp_path / "not-created",
            repository_root=ROOT, temporal_audit=audit)
    assert not (tmp_path / "not-created").exists()


def test_contract_dispatch_checks_real_audit_and_does_not_trust_packet_result_cache(tmp_path):
    from xi_kari_runtime.contracts import build_analysis_packet, require_packet_contract
    from xi_kari_runtime.semantic_projection import semantic_atom_paths
    semantic, contract, audit = observed_packet(tmp_path)
    prepared = prepare_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT, temporal_audit=audit)
    finalization = {"reader_sections": semantic["reader_sections"], "visibility_ledger": {"entries": [
        {"canonical_path": path, "classification": "public", "disclosure": "include",
         "purpose": "bounded source-scope analysis", "authority_refs": [], "protection_reason": None}
        for path in semantic_atom_paths(prepared)]}}
    packet = build_analysis_packet(semantic, run_contract=contract, repository_root=ROOT,
        reader_finalization=finalization, temporal_audit=audit)
    require_packet_contract(packet, mode=contract["mode"], run_contract=contract, temporal_audit=audit)
    assert packet["claim_mechanism_graph"]["claims"][0]["formal_qualification"]["status"] == "qualified"
    with pytest.raises(ValueError, match="recomputed"):
        require_packet_contract(packet, mode=contract["mode"], run_contract=contract)


def test_final_reader_cannot_replace_the_readonly_packet_after_temporal_verification(tmp_path):
    semantic, contract, audit = observed_packet(tmp_path)
    packet = prepare_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT, temporal_audit=audit)
    controls = validate_stage_chain_v4(packet, run_contract=contract, repository_root=ROOT, temporal_audit=audit)
    request = build_semantic_execution_request_v4(packet, controls, run_contract=contract,
        kind="final_reader", repository_root=ROOT, temporal_audit=audit)
    request["task"]["readonly_packet"]["claim_mechanism_graph"]["claims"][0]["formal_qualification"]["result_status"] = "null_supported"
    with pytest.raises(ValueError, match="readonly|frozen|temporal|material"):
        execute_semantic_request_v4(request, binding=None, run_directory=tmp_path / "not-created",
            repository_root=ROOT, temporal_audit=audit)
    assert not (tmp_path / "not-created").exists()


def test_natural_entry_cannot_accept_a_json_temporal_authority(tmp_path):
    from xi_kari_runtime.execution import execute_natural_request
    with pytest.raises(ValueError, match="runtime-observed"):
        execute_natural_request(tmp_path / "not-created", request_text="Explain the bounded observation.",
            repository_root=ROOT, temporal_audit={"verified": True})
    assert not (tmp_path / "not-created").exists()
