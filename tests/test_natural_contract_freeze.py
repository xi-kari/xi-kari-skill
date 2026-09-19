from copy import deepcopy
from pathlib import Path
import json
import os
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from xi_kari_runtime import execution
from xi_kari_runtime.canonical_json import canonical_bytes
from xi_kari_runtime.authoring import bind_base_authoring_provider
from xi_kari_runtime.contract_authoring import validate_contract_authoring_evidence, validate_contract_authoring_binding
from xi_kari_runtime.ontology_read_trace import build_ontology_read_trace, build_ontology_read_plan, content_access_witness, OntologyReadTraceError
from xi_kari_runtime.problem_contract import build_natural_request_envelope, contract_hash, draft_problem_contract_from_natural_request


def request_and_final():
    request = build_natural_request_envelope("评价这项六周轮班计划", mode="open-world", evidence_cutoff="2026-09-21T00:00:00Z")
    final = draft_problem_contract_from_natural_request(request["text"], mode="open-world", evidence_cutoff=request["evidence_cutoff"])
    final.update(object_of_analysis="六周轮班计划", boundary="仅评价人员排班与补偿规则", identity_criterion="同一组成员和同一份计划",
        spatial_scale="同一工作场所", organizational_scale="同一团队", time_window="未来六周")
    return request, final


class PlanObserved(Exception):
    pass


def test_natural_refinement_is_frozen_before_read_plan(tmp_path, monkeypatch):
    observed = []
    expected = {}
    def author(**kwargs):
        candidate = dict(kwargs["draft_problem_contract"])
        candidate.update(boundary="作者明确的六周人员安排边界", time_window="未来六周")
        expected.update(candidate)
        observed.append("contract-author")
        return candidate, {"receipt": {"receipt_sha256": "a" * 64}}
    monkeypatch.setattr(execution, "_author_natural_contract", author, raising=False)
    monkeypatch.setattr(execution, "bind_semantic_authoring_adapter", lambda *a, **k: {"provider_binding": {}, "executable_sha256": "b" * 64})
    monkeypatch.setattr(execution, "bind_base_authoring_provider", lambda *a, **k: {})
    monkeypatch.setattr(execution, "build_full_source_lock", lambda *a, **k: ({}, []))
    def plan(*args, **kwargs):
        assert observed == ["contract-author"]
        assert kwargs["problem_contract_sha256"] == contract_hash(expected)
        raise PlanObserved
    monkeypatch.setattr(execution, "build_ontology_read_plan", plan)
    with pytest.raises(PlanObserved):
        execution.execute_authored_run(tmp_path, request_text="评价六周轮班计划", repository_root=ROOT, codex_provider_executable=Path(sys.executable).resolve())
    assert not list(tmp_path.iterdir())


def envelope(problem):
    record = {"reader_unit": "guide", "synthesis": "原文边界的完整测试观察。",
        "semantic_observations": [{"proposition": "同名不代表同義。", "role": "definition", "source_anchor_refs": ["V83-P0001"]}],
        "continuity_with_previous": {"previous_reader_unit": None, "relation": "root", "explanation": "测试入口。"},
        "problem_relation": {"status": "applied", "rationale": "用于问题边界。"}, "source_undefined_refs": []}
    return {
        "semantic_packet": {
            "problem_contract": {**problem, "dynamic_applicability": "not_applicable", "applicability_rationale": "只评价条文"},
            "deliverable_type": problem["deliverable_type"], "dynamic_applicability": "not_applicable", "not_applicable_reason": "只评价条文",
            "facts": {}, "case_ledger": {}, "cases": [], "answer": {}, "evidence": {}, "visibility_ledger": {"entries": [{"canonical_path": "problem_contract.question", "classification": "public", "disclosure": "include", "purpose": "unit test", "authority_refs": [], "protection_reason": None}]},
            "reader_sections": [{"section_id": "one", "heading": "轮班有补偿", "local_judgment": "补偿条款需要保留。", "paragraphs": ["执行记录仍须检验。"], "source_bindings": []}],
            "retrieval": {"mode": "open-world", "queries": [{"direction": "current_baseline", "query": "schedule", "purpose": "test source"}],
                "sources": [{"source_id": "SOURCE-1", "origin": "external", "title": "Schedule", "url": "https://example.org/schedule", "publisher": "Example", "content": "Schedule text", "published_at": "2026-09-01T00:00:00Z", "event_at": "2026-09-01T00:00:00Z"}],
                "assessments": [{"source_id": "SOURCE-1", "authority": "source statement", "independence": "independent", "independence_identity": "publisher", "source_lineage": [], "interest_relevance": "draft", "affected_positions": [], "low_power_positions": [], "conflict_source_ids": [], "freshness": "current", "relevance": "direct", "verdict": "usable", "limitations": [], "cannot_prove": []}],
                "saturation_status": "bounded_saturation", "capability_gap": "unit fixture", "remaining_unknowns": []},
        },
        "semantic_read_trace": {"schema_id": "xi-kari.v3.semantic-read-trace-input", "schema_version": 1, "records": [deepcopy(record) for _ in range(21)]},
        "ontology_read_trace": {"schema_id": "xi-kari.v3.ontology-read-trace-input", "schema_version": 1, "records": [{"item_id": "candidate:test", "read_status": "read", "content_witness": "a" * 64, "content_excerpt": "完整的只读测试材料和定义边界。", "problem_relation": {"status": "applied", "rationale": "测试绑定"}}]},
    }


def test_second_author_cannot_refine_the_frozen_contract(monkeypatch):
    request, final = request_and_final()
    changed = dict(final, boundary="扩大至所有组织")
    monkeypatch.setattr(execution, "build_ontology_read_trace", lambda *a, **k: {})
    with pytest.raises(ValueError, match="frozen problem contract"):
        execution._parse_base_output(canonical_bytes(envelope(changed)), problem_contract=final,
            mode="open-world", ontology_read_plan={}, repository_root=ROOT, natural_request=request)


def test_final_read_trace_rejects_a_draft_bound_plan():
    request, final = request_and_final()
    draft = draft_problem_contract_from_natural_request(request["text"], mode="open-world", evidence_cutoff=request["evidence_cutoff"])
    assert contract_hash(final) != contract_hash(draft)
    with pytest.raises(OntologyReadTraceError, match="bound to this run"):
        build_ontology_read_trace({}, plan={"run_id": "test", "complete": True, "problem_contract_sha256": contract_hash(draft)},
            run_id="test", repository_root=ROOT, problem_contract_sha256=contract_hash(final))


def test_draft_witness_is_rejected_even_with_a_final_bound_plan():
    request, final = request_and_final()
    draft = draft_problem_contract_from_natural_request(request["text"], mode="open-world", evidence_cutoff=request["evidence_cutoff"])
    plan = build_ontology_read_plan(ROOT, run_id="test", problem_contract_sha256=contract_hash(final), content_access_challenge="b" * 64)
    records = [{"item_id": row["item_id"], "read_status": "read", "content_excerpt": "not used before witness verification",
                "content_witness": content_access_witness(challenge=plan["content_access_challenge"], problem_contract_sha256=contract_hash(draft),
                    item_id=row["item_id"], content_sha256=row["content_sha256"]),
                "problem_relation": {"status": "applied", "rationale": "test"}} for row in plan["records"]]
    with pytest.raises(OntologyReadTraceError, match="content witness does not prove"):
        build_ontology_read_trace({"schema_id": "xi-kari.v3.ontology-read-trace-input", "schema_version": 1, "records": records},
            plan=plan, run_id="test", repository_root=ROOT, problem_contract_sha256=contract_hash(final))


def test_manual_contract_skips_the_contract_author(tmp_path, monkeypatch):
    _, final = request_and_final()
    def forbidden(**kwargs):
        raise AssertionError("manual contract must not be reauthored")
    monkeypatch.setattr(execution, "_author_natural_contract", forbidden, raising=False)
    monkeypatch.setattr(execution, "bind_semantic_authoring_adapter", lambda *a, **k: {"provider_binding": {}, "executable_sha256": "b" * 64})
    monkeypatch.setattr(execution, "bind_base_authoring_provider", lambda *a, **k: {})
    monkeypatch.setattr(execution, "build_full_source_lock", lambda *a, **k: ({}, []))
    def plan(*args, **kwargs):
        assert kwargs["problem_contract_sha256"] == contract_hash(final)
        raise PlanObserved
    monkeypatch.setattr(execution, "build_ontology_read_plan", plan)
    with pytest.raises(PlanObserved):
        execution.execute_authored_run(tmp_path, problem_contract=final, repository_root=ROOT, codex_provider_executable=Path(sys.executable).resolve())


def captured_contract(tmp_path):
    provider_path = tmp_path / "contract_provider.py"
    provider_path.write_text(f"#!{Path(sys.executable).resolve()}\n" + '''import json, pathlib, sys
request = json.loads(sys.stdin.read().split("运行时请求（只读）：\\n", 1)[1])
contract = dict(request["draft_problem_contract"])
contract.update(boundary="仅限本团队的六周排班与补偿", time_window="未来六周")
pathlib.Path("semantic-output.json").write_text(json.dumps(contract, ensure_ascii=False), encoding="utf-8")
notice = pathlib.Path(sys.argv[sys.argv.index("--output-last-message") + 1])
notice.write_text("SEMANTIC_OUTPUT_READY", encoding="utf-8")
for event in ({"type":"thread.started","thread_id":"transport-test"}, {"type":"turn.started"}, {"type":"turn.completed"}):
 print(json.dumps(event), flush=True)
''', encoding="utf-8")
    provider_path.chmod(0o755)
    request, _ = request_and_final()
    draft = draft_problem_contract_from_natural_request(request["text"], mode="open-world", evidence_cutoff=request["evidence_cutoff"])
    provider = bind_base_authoring_provider(provider_path, mode="closed-input", repository_root=ROOT, timeout_seconds=30)
    return execution._author_natural_contract(run_id="test", natural_request=request,
        draft_problem_contract=draft, repository_root=ROOT, provider=provider, timeout_seconds=30)


def test_contract_stage_captures_real_process_file_and_final_hash(tmp_path):
    final, evidence = captured_contract(tmp_path)
    request, _ = request_and_final()
    assert final["boundary"] == "仅限本团队的六周排班与补偿"
    assert evidence["receipt"]["problem_contract_sha256"] == contract_hash(final)
    assert evidence["receipt"]["parent_pid"] == os.getpid()
    assert evidence["receipt"]["child_pid"] != os.getpid()
    assert evidence["receipt"]["exit_status"] == 0
    assert json.loads(evidence["output_text"])["boundary"] == final["boundary"]
    validate_contract_authoring_evidence(evidence, run_id="test", natural_request=request,
        frozen_problem_contract=final, repository_root=ROOT)
    from xi_kari_runtime.world_volume import _schema_validator
    _schema_validator("xk-natural-contract-execution.schema.json", str(ROOT)).validate(evidence)
    base_request = {"problem_contract": final, "contract_authoring_binding": {
        "receipt_sha256": evidence["receipt"]["receipt_sha256"], "problem_contract_sha256": contract_hash(final)}}
    run = {"run_id": "test", "problem_contract": final, "natural_request": request, "continuation": {"kind": "original"}}
    validate_contract_authoring_binding(base_request=base_request,
        base_receipt={"contract_authoring_evidence": evidence, "started_at": evidence["receipt"]["completed_at"]},
        run_contract=run, repository_root=ROOT)


@pytest.mark.parametrize("field", ["request_text", "prompt_text", "output_text", "event_stream_text"])
def test_contract_stage_replay_rejects_changed_evidence(tmp_path, field):
    final, evidence = captured_contract(tmp_path)
    evidence[field] += " "
    request, _ = request_and_final()
    with pytest.raises(ValueError):
        validate_contract_authoring_evidence(evidence, run_id="test", natural_request=request,
            frozen_problem_contract=final, repository_root=ROOT)


def test_original_natural_run_requires_its_contract_stage_evidence():
    request, final = request_and_final()
    with pytest.raises(ValueError, match="separate contract authoring"):
        validate_contract_authoring_binding(base_request={"problem_contract": final}, base_receipt={},
            run_contract={"run_id": "test", "natural_request": request, "problem_contract": final}, repository_root=ROOT)


def test_contract_stage_rejects_runtime_authority_and_question_rewrite():
    from xi_kari_runtime.contract_authoring import parse_contract_authoring_output
    request, final = request_and_final()
    for changed in (dict(final, child_pid=123), dict(final, question="另一个问题"), dict(final, evidence_cutoff="2027-01-01T00:00:00Z")):
        with pytest.raises(ValueError):
            parse_contract_authoring_output(canonical_bytes(changed), natural_request=request, repository_root=ROOT)


def test_two_real_provider_processes_receive_the_frozen_contract_in_order(tmp_path, monkeypatch):
    provider_path = tmp_path / "two_stage_provider.py"
    provider_path.write_text(f"#!{Path(sys.executable).resolve()}\n" + '''import json, os, pathlib, sys
prompt = sys.stdin.read()
if "运行时请求（只读绑定）：\\n" in prompt:
 request = json.loads(prompt.rsplit("运行时请求（只读绑定）：\\n", 1)[1])
 result = {"observed_contract": request["problem_contract"], "ontology_hash": request["source_inputs"]["ontology_read_plan"]["problem_contract_sha256"], "contract_binding": request["contract_authoring_binding"], "observed_base_pid": os.getpid()}
else:
 request = json.loads(prompt.rsplit("运行时请求（只读）：\\n", 1)[1])
 result = dict(request["draft_problem_contract"])
 result.update(boundary="唯一允许的本团队排班边界", time_window="六周")
pathlib.Path("semantic-output.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
pathlib.Path(sys.argv[sys.argv.index("--output-last-message") + 1]).write_text("SEMANTIC_OUTPUT_READY", encoding="utf-8")
for event in ({"type":"thread.started","thread_id":str(os.getpid())}, {"type":"turn.started"}, {"type":"turn.completed"}):
 print(json.dumps(event), flush=True)
''', encoding="utf-8")
    provider_path.chmod(0o755)
    observed_contract_pid = []
    original = execution._author_natural_contract
    def author(**kwargs):
        result = original(**kwargs)
        observed_contract_pid.append(result[1]["receipt"]["child_pid"])
        return result
    monkeypatch.setattr(execution, "_author_natural_contract", author)
    def stop_after_transport(raw, **kwargs):
        result = json.loads(raw)
        final = kwargs["problem_contract"]
        assert final["boundary"] == "唯一允许的本团队排班边界"
        assert result["observed_contract"] == final
        assert result["ontology_hash"] == contract_hash(final)
        assert result["contract_binding"]["problem_contract_sha256"] == contract_hash(final)
        assert len(observed_contract_pid) == 1
        assert result["observed_base_pid"] != observed_contract_pid[0]
        raise PlanObserved
    monkeypatch.setattr(execution, "_parse_base_output", stop_after_transport)
    destination = tmp_path / "runs-not-created"
    with pytest.raises(execution.AuthoringFailure) as captured:
        execution.execute_authored_run(destination, request_text="评价六周轮班计划", repository_root=ROOT,
            codex_provider_executable=provider_path, timeout_seconds=60)
    assert isinstance(captured.value.__cause__, PlanObserved)
    assert captured.value.diagnostics_path.parent == destination
    assert not list(destination.rglob("run-contract.json"))
