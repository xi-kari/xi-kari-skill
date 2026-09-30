"""Synthetic program regressions across author, packet, disk, and reader boundaries."""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from tests.test_v4_pipeline_e2e_fixtures import (
    BODY, CLOSED_MATERIALS, deterministic_provider, domain_repository, fresh_boundary, packet_inputs,
    public_visibility, static_author_output, write_json,
)
from xi_kari_runtime import contracts, domains, execution, prose, validation
from xi_kari_runtime.canonical_json import canonical_bytes
from xi_kari_runtime.semantic_projection import reader_projection_units, typed_semantic_atoms, validate_reader_sections


def fresh_result(process):
    assert process.returncode == 0, process.stderr
    value = json.loads(process.stdout)
    assert value["pid"] != os.getpid()
    return value["result"]


@pytest.mark.parametrize("mode", ["open-world", "closed-input"])
def test_v4_pipeline_e2e_static_author_preflight_is_legal_without_recursion(mode):
    value, problem, plan, lock, events = static_author_output(mode=mode)
    packet, _, _ = execution.parse_base_authoring_output(
        canonical_bytes(value), problem_contract=problem, mode=mode, repository_root=ROOT,
        ontology_read_plan=plan, source_lock=lock, source_events=events, contract_version=4,
    )
    assert packet["applicability"]["recursion"]["status"] == "not_applicable"
    assert "recursive_lineage" not in packet
    assert packet["claim_mechanism_graph"]["claims"][0]["formal_qualification"]["status"] == "not_requested"
    assert validate_reader_sections(packet) == []


def test_v4_pipeline_e2e_production_static_author_reaches_fresh_validation_and_full_body(tmp_path):
    _, problem, _, _, _ = static_author_output(mode="closed-input")
    problem['evidence_cutoff'] = '2030-01-01T00:00:00Z'
    transport = tmp_path.parent / "prod"
    transport.mkdir()
    provider, observation = deterministic_provider(transport)
    result = execution.execute_authored_run(
        transport / "runs", problem_contract=problem, run_id="synthetic-v4-e2e",
        repository_root=ROOT, codex_provider_executable=provider, timeout_seconds=60,
        mode="closed-input", closed_input_materials=CLOSED_MATERIALS,
    )
    observed = json.loads(observation.read_text("utf-8"))
    assert observed["pid"] != os.getpid()
    assert observed["source_version"] == "v9.0"
    assert observed['contract_version'] == 4
    assert observed['synthetic'] is True and observed['actual_model_runs'] == 0
    run_dir = Path(result["run_dir"])
    contract = json.loads((run_dir / 'run-contract.json').read_text('utf-8'))
    assert contract['schema_version'] == 4 and contract['source_version'] == 'v9.0'
    report = validation.run_fresh_validator(run_dir, repository_root=ROOT, preseal=False)
    assert report["valid"] is report['complete'] is True, report.get("errors")
    assert report["fresh_process"] is True
    assert report['phase_count'] == 13
    reader = (run_dir / "delivery" / "xi-kari-answer.md").read_text("utf-8")
    assert all(paragraph in reader for paragraph in BODY)
    assert "实际执行情况仍未知" in reader


def test_v4_pipeline_e2e_static_packet_disk_reader_subchain_retains_every_authored_paragraph(tmp_path):
    semantic, contract = packet_inputs()
    packet = contracts.build_analysis_packet(semantic, run_contract=contract, repository_root=ROOT)
    result = fresh_result(fresh_boundary(tmp_path, "packet", {"packet": packet, "contract": contract}))
    assert {"applicability.recursion.status", "claim_mechanism_graph.claims[0].claim_basis.kind",
            "claim_mechanism_graph.claims[0].formal_qualification.status"}.issubset(result["atom_paths"])
    assert all(paragraph in result["body"] for paragraph in BODY)
    assert result["formal_qualification"]["status"] == "not_requested"
    packet["runtime_binding"]["problem_contract_sha256"] = "0" * 64
    rejected = fresh_boundary(tmp_path, "packet", {"packet": packet, "contract": contract})
    assert rejected.returncode != 0
    assert "frozen problem" in rejected.stderr


def test_v4_pipeline_e2e_total_effect_and_mechanism_are_recomputed_separately_from_disk(tmp_path):
    from tests.test_causal_judgment_v4_graph import effect_graph
    graph, assessment = effect_graph()
    for row in graph["evidence"]:
        if row["evidence_id"] == "E-MECHANISM":
            row["support_status"] = "invalidated"
    inputs = {"graph": graph, "assessments": [assessment]}
    first = fresh_result(fresh_boundary(tmp_path, "causal", inputs))
    result = first["assessments"][0]["result"]
    assert result["total_effect"] == "supported"
    assert result["mechanism"] == "unsupported_or_undecided"
    graph["evidence"][0]["support_checks"]["world_fact_supported"]["status"] = "failed"
    second = fresh_result(fresh_boundary(tmp_path, "causal", inputs))
    assert second["assessments"][0]["result"]["total_effect"] == "unsupported_or_undecided"


@pytest.mark.parametrize("label", ["passed", "not_run"])
def test_v4_pipeline_e2e_instance_target_label_cannot_create_qualification(tmp_path, label):
    from tests.test_causal_judgment_v4_graph import effect_graph
    graph, _ = effect_graph()
    graph["dependency_edges"].append({
        "edge_id": "EDGE-SYNTHETIC-FORMAL", "from_id": "CLAIM-STRUCTURAL",
        "to_ref": {"kind": "instance", "id": "INSTANCE-SYNTHETIC-UNTESTED"},
        "role": "inferential_requires", "source_refs": ["V90-P00158"],
        "condition": "A formal result is explicitly requested", "scope": "This formal route only",
    })
    graph["dependency_targets"] = [{"kind": "instance", "id": "INSTANCE-SYNTHETIC-UNTESTED",
                                    "status": label, "reason": "Synthetic caller label with no evaluation"}]
    result = fresh_result(fresh_boundary(tmp_path, "formal", {"graph": graph}))
    assert result["CLAIM-STRUCTURAL"]["blocked"] is True
    assert result["CLAIM-FACTUAL"]["blocked"] is False


def test_v4_pipeline_e2e_observed_unauthorized_event_changes_fact_without_granting_action(tmp_path):
    from tests.test_p07_v4_world_bundle import bundle_fixture
    bundle, ledger, retrieval = bundle_fixture()
    data = {"world": bundle, "ledger": ledger, "retrieval": retrieval}
    result = fresh_result(fresh_boundary(tmp_path, "world", data))
    assert result["output_state"]["objects"][0]["variables"][0]["value"] == "new"
    assert result["transitions"][0]["event_role"] == "e(t)"
    assert result["transitions"][0]["external_action_authorized"] is False
    bundle["event_records"][0]["deltas"][0]["after"] = "Changed without a new evidence binding"
    rejected = fresh_boundary(tmp_path, "world", data)
    assert rejected.returncode != 0
    assert "target" in rejected.stderr or "delta" in rejected.stderr


def test_v4_pipeline_e2e_packet_world_consumer_rejects_stale_registered_parent_data(tmp_path):
    from tests.test_p07_v4_world_bundle import bundle_fixture
    from xi_kari_runtime.packet_v4 import prepare_analysis_packet_v4
    bundle, world_ledger, world_retrieval = bundle_fixture()
    _, problem, _, _, _ = static_author_output()
    problem["evidence_cutoff"] = bundle["registered_state"]["evidence_cutoff"]
    semantic, contract = packet_inputs(problem=problem)
    bundle["registered_state"]["run_id"] = contract["run_id"]
    semantic["retrieval"]["sources"].extend(world_retrieval["sources"])
    for key in ("claims", "evidence", "support_edges", "unsupported_claims"):
        semantic["evidence"][key].extend(world_ledger[key])
    semantic["local_world_model"] = bundle
    semantic["applicability"] = deepcopy(bundle["applicability"])
    semantic["claim_mechanism_graph"]["applicability"] = deepcopy(bundle["applicability"])
    semantic["claim_mechanism_graph"]["world_volume_id"] = "WORLD-SYNTHETIC-1"
    semantic["visibility_ledger"] = public_visibility(semantic)
    pending = prepare_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT)
    packet = contracts.build_analysis_packet(semantic, run_contract=contract, repository_root=ROOT,
        reader_finalization={"reader_sections": semantic["reader_sections"],
                             "visibility_ledger": public_visibility(pending)})
    result = fresh_result(fresh_boundary(tmp_path, "packet", {"packet": packet, "contract": contract}))
    assert "local_world_model.registered_state.objects[0].variables[0].value" in result["atom_paths"]
    packet["local_world_model"]["registered_state"]["objects"][0]["variables"][0]["value"] = "stale parent"
    rejected = fresh_boundary(tmp_path, "packet", {"packet": packet, "contract": contract})
    assert rejected.returncode != 0
    assert "event delta" in rejected.stderr


def test_v4_pipeline_e2e_scale_consumes_frozen_objects_comparators_and_task_from_disk(tmp_path):
    from tests.test_p06_scale_instances import scale_fixture
    record, registries = scale_fixture()
    inputs = {"record": record, "registries": registries}
    first = fresh_result(fresh_boundary(tmp_path, "scale", inputs))
    assert first["result_state"] == "supported"
    assert first["transformation_class"] == "all_equal"
    record["objects"]["target_object"]["boundary"].append("new-unit-with-no-mapping-proof")
    rejected = fresh_boundary(tmp_path, "scale", inputs)
    assert rejected.returncode != 0


def test_v4_pipeline_e2e_recursive_author_consumes_updated_state_and_preserved_unknowns(tmp_path):
    from tests.test_p08_recursive_transitions import recursive_fixture
    parent, event, evidence, actions = recursive_fixture()
    inputs = {"parent": parent, "event": event, "evidence": evidence, "actions": actions}
    result = fresh_result(fresh_boundary(tmp_path, "recursion", inputs))
    request = result["observed_request"]
    assert request["input_state"]["objects"][0]["variables"][0]["value"] == 4
    assert {action["option_id"] for action in request["available_actions"]} == {"WAIT", "CHEAP"}
    assert request["input_state"]["unknowns"] == parent["output_state"]["unknowns"]
    assert request["input_state"]["losses"] == parent["output_state"]["losses"]
    assert request["existing_obligations"] == parent["output_state"]["existing_obligations"]
    assert result["child"]["evidence_identity"] == "simulated"
    event["deltas"][0]["before"] = 99
    rejected = fresh_boundary(tmp_path, "recursion", inputs)
    assert rejected.returncode != 0
    assert "event delta" in rejected.stderr


def test_v4_pipeline_e2e_domain_byte_change_invalidates_fresh_materialized_delivery(tmp_path):
    from tests.test_domain_loading_v4 import semantic_input, reader_text
    repository = domain_repository(tmp_path)
    problem_hash = "1" * 64
    run_id = "synthetic-v4-domain-e2e"
    plan = domains.build_domain_read_plan(repository, domain_ids=["D.04"],
                                         problem_contract_sha256=problem_hash,
                                         run_id=run_id, challenge="2" * 64)
    records = semantic_input(domains, repository, plan)
    trace = domains.build_domain_read_trace(repository, plan, records)
    run = tmp_path / "domain-run"
    write_json(run / "domain-read-plan.json", plan)
    write_json(run / "domain-read-trace.json", trace)
    write_json(run / "domain-authority.json", domains.domain_authority_binding(repository, plan))
    (run / "xi-kari-answer.md").write_text(reader_text(records), encoding="utf-8")
    inputs = {"run_dir": str(run), "problem_hash": problem_hash, "run_id": run_id}
    assert fresh_result(fresh_boundary(tmp_path, "domain", inputs, repository=repository))["domain_ids"] == ["D.04"]
    content = repository / "references/learning-packs/domains/D.04.md"
    content.write_bytes(content.read_bytes() + b"\nChanged domain bytes after materialization\n")
    rejected = fresh_boundary(tmp_path, "domain", inputs, repository=repository)
    assert rejected.returncode != 0
    assert "content" in rejected.stderr or "fingerprint" in rejected.stderr


@pytest.mark.parametrize("mutation", ["mixed-source", "legacy-trace", "missing-material"])
def test_v4_pipeline_e2e_author_rejects_mixed_source_legacy_trace_and_missing_material(mutation):
    value, problem, plan, lock, events = static_author_output()
    if mutation == "mixed-source":
        value["semantic_packet"]["claim_mechanism_graph"]["source_version"] = "v8.3"
    elif mutation == "legacy-trace":
        value["semantic_read_trace"]["schema_id"] = "xi-kari.v3.semantic-read-trace-input"
    else:
        value["semantic_packet"]["retrieval"]["sources"] = []
    with pytest.raises(ValueError):
        execution.parse_base_authoring_output(
            canonical_bytes(value), problem_contract=problem, mode="open-world", repository_root=ROOT,
            ontology_read_plan=plan, source_lock=lock, source_events=events, contract_version=4,
        )


@pytest.mark.parametrize("stage", ["world_state", "transformation", "recursion", "forecast", "action_choice"])
def test_v4_pipeline_e2e_applicable_stage_cannot_pass_without_its_actual_inputs(stage):
    semantic, contract = packet_inputs()
    semantic["applicability"][stage]["status"] = "applicable"
    semantic["claim_mechanism_graph"]["applicability"][stage]["status"] = "applicable"
    field = {"world_state": "local_world_model", "transformation": "transformation_ledger",
             "recursion": "recursive_lineage", "forecast": "forecast", "action_choice": "action_ranking"}[stage]
    with pytest.raises(ValueError, match=field):
        contracts.build_analysis_packet(semantic, run_contract=contract, repository_root=ROOT)


def test_v4_pipeline_e2e_reader_rejects_missing_body_for_v4_even_without_legacy_applicability():
    semantic, _ = packet_inputs()
    semantic["reader_sections"] = []
    assert prose.reader_contract_gaps(semantic, prose.render_answer(semantic)), "Missing v4 body was accepted"


def test_v4_pipeline_e2e_domain_reader_semantics_require_typed_visibility_and_real_body(tmp_path):
    from tests.test_domain_loading_v4 import semantic_input
    repository = domain_repository(tmp_path)
    plan = domains.build_domain_read_plan(repository, domain_ids=["D.04"],
                                         problem_contract_sha256="1" * 64,
                                         run_id="synthetic-domain-visibility", challenge="2" * 64)
    trace = domains.build_domain_read_trace(repository, plan, semantic_input(domains, repository, plan))
    payload = {"domain_read_trace": trace}
    required = "domain_read_trace.records[0].reader_responsibilities.costs_exit"
    atoms = {atom["canonical_path"]: atom for atom in typed_semantic_atoms(payload)}
    assert required in atoms, "A validated domain cost/exit responsibility disappeared from the typed ledger"
    assert "追加全状态重建会增加成本，可以在目标任务完成时退出。" in atoms[required]["public_text"]
    assert not any("content_witness" in path or "fingerprint" in path for path in atoms)
    payload["visibility_ledger"] = public_visibility(payload)
    assert "追加全状态重建会增加成本，可以在目标任务完成时退出。" in json.dumps(
        reader_projection_units(payload), ensure_ascii=False,
    )


def test_v4_pipeline_e2e_author_cannot_grant_formal_instance_from_strong_result_labels():
    from tests.test_p04_v4_claim_contracts import _qualification
    value, problem, plan, lock, events = static_author_output()
    for claim in (value["semantic_packet"]["claim_mechanism_graph"]["claims"][0],
                  value["semantic_packet"]["evidence"]["claims"][0]):
        claim["formal_qualification"] = _qualification(requested=True, qualified=True)
        claim["responsibility_refs"] = ["V90-CANON-G2"]
    with pytest.raises(ValueError, match="instance|qualif|runtime"):
        execution.parse_base_authoring_output(
            canonical_bytes(value), problem_contract=problem, mode="open-world", repository_root=ROOT,
            ontology_read_plan=plan, source_lock=lock, source_events=events, contract_version=4,
        )


def test_v4_pipeline_e2e_protected_statement_is_absent_from_body_projection_and_errors():
    value, problem, plan, lock, events = static_author_output()
    packet = value["semantic_packet"]
    secret = "SYNTHETIC-CONFIDENTIAL-CLAUSE"
    packet["claim_mechanism_graph"]["claims"][0]["statement"] = secret
    for entry in packet["visibility_ledger"]["entries"]:
        if entry["canonical_path"] == "claim_mechanism_graph.claims[0].statement":
            entry.update(classification="sensitive", disclosure="withhold",
                         authority_refs=["XK0-PRIVACY-CONTRACT-SYNTHETIC"],
                         protection_reason="The protected statement is withheld for this audience")
    packet["reader_sections"] = [{
        "section_id": "safe-disclosure", "heading": "保护性扣留",
        "local_judgment": "受保护条文保持不公开，当前只交付其余可见的有限解释。",
        "paragraphs": list(BODY), "source_bindings": [],
    }]
    assert secret not in json.dumps(reader_projection_units(packet), ensure_ascii=False)
    assert secret not in prose.render_answer(packet)
    packet["claim_mechanism_graph"]["evidence"][0]["support_checks"]["source_exists"]["status"] = "invalid"
    with pytest.raises(ValueError) as caught:
        execution.parse_base_authoring_output(
            canonical_bytes(value), problem_contract=problem, mode="open-world", repository_root=ROOT,
            ontology_read_plan=plan, source_lock=lock, source_events=events, contract_version=4,
        )
    assert secret not in str(caught.value)


def test_v4_pipeline_e2e_production_schema_failure_cannot_disclose_protected_material(tmp_path):
    secret = "SYNTHETIC-PRIVATE-MATERIAL-MUST-STAY-OUT"
    materials = deepcopy(CLOSED_MATERIALS)
    materials[0]["content"] += " " + secret
    _, problem, _, _, _ = static_author_output(mode="closed-input", materials=materials)
    problem['evidence_cutoff'] = '2030-01-01T00:00:00Z'
    transport = tmp_path.parent / "private"
    transport.mkdir()
    provider, observation = deterministic_provider(transport, protected_content=secret)
    disclosed = False
    rejected = False
    try:
        execution.execute_authored_run(
            transport / "runs", problem_contract=problem, run_id="synthetic-v4-private-e2e",
            repository_root=ROOT, codex_provider_executable=provider, timeout_seconds=60,
            mode="closed-input", closed_input_materials=materials,
        )
    except ValueError as error:
        rejected = True
        disclosed = secret in str(error)
    assert observation.is_file(), "The synthetic author did not reach its output boundary"
    observed = json.loads(observation.read_text('utf-8'))
    assert observed['pid'] != os.getpid()
    assert observed['source_version'] == 'v9.0' and observed['contract_version'] == 4
    assert observed['synthetic'] is True and observed['actual_model_runs'] == 0
    assert rejected is True, "The intentionally invalid author schema was accepted"
    assert disclosed is False, "The production error disclosed protected synthetic material"
