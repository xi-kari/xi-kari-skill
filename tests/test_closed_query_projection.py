from copy import deepcopy
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from xi_kari_runtime import execution, retrieval_execution
from xi_kari_runtime.canonical_json import canonical_bytes, sha256_text
from xi_kari_runtime.closed_input import _normalize_closed_semantic, freeze_closed_input_materials
from xi_kari_runtime.semantic_projection import semantic_atom_paths, validate_reader_sections


QUERY = {"direction": "authoritative_definition", "query": "Recommendation and permission",
         "purpose": "核对授权状态的明示条件"}
COMPLETED = "2026-09-20T00:00:00Z"


def closed_projection(extra=None):
    materials = [{"source_id": "SOURCE-TERMS", "title": "Terms", "content": "Recommendation is not authorization."}]
    authored = {"mode": "closed-input", "queries": [{**QUERY, **(extra or {})}],
                "sources": [{**materials[0], "origin": "user_material"}],
                "assessments": [{"source_id": "SOURCE-TERMS", "source_lineage": [], "conflict_source_ids": []}],
                "saturation_status": "bounded", "capability_gap": "none", "remaining_unknowns": []}
    before = deepcopy(authored)
    frozen, manifest = freeze_closed_input_materials(materials)
    semantic, projected, bindings, _ = _normalize_closed_semantic(
        authored, frozen, manifest=manifest, run_id="projection-test", completed_at=COMPLETED)
    assert authored == before
    return semantic, projected, bindings


def test_closed_projection_preserves_authored_query_purpose_and_body_binding():
    packet = {"retrieval": {"mode": "closed-input", "queries": [deepcopy(QUERY)]},
              "reader_sections": [{"section_id": "sources", "heading": "材料核对",
                                   "local_judgment": "先核对给定材料的语义边界。",
                                   "paragraphs": [QUERY["purpose"]], "source_bindings": [{
                                       "source_path": "retrieval.queries[0].purpose",
                                       "paragraph_index": 1, "excerpt": QUERY["purpose"]}]}]}
    purpose_path = "retrieval.queries[0].purpose"
    assert not any(purpose_path in error for error in validate_reader_sections(packet))
    packet["visibility_ledger"] = {"entries": [
        {"canonical_path": path, "classification": "public", "disclosure": "include",
         "purpose": "projection test", "authority_refs": [], "protection_reason": None}
        for path in semantic_atom_paths(packet)
    ]}
    original_visibility = next(row for row in packet["visibility_ledger"]["entries"]
                               if row["canonical_path"] == purpose_path)
    semantic, projected, bindings = closed_projection()
    packet["retrieval"]["queries"] = projected["queries"]
    execution._rebind_visibility_ledger(packet, privacy_purpose="projection test")
    assert not any(purpose_path in error for error in validate_reader_sections(packet))
    assert projected["queries"][0]["purpose"] == semantic["queries"][0]["purpose"] == QUERY["purpose"]
    assert original_visibility in packet["visibility_ledger"]["entries"]
    assert bindings[0]["purpose_sha256"] == sha256_text(QUERY["purpose"])
    assert projected["queries"][0]["status"] == "executed"
    assert projected["queries"][0]["executed_at"] == COMPLETED
    assert projected["queries"][0]["query_id"].startswith("QUERY-CLOSED-01-")


@pytest.mark.parametrize("field,value", [("status", "executed"), ("query_id", "MODEL-ID"),
                                         ("executed_at", COMPLETED), ("result_source_ids", ["SOURCE-TERMS"])])
def test_closed_projection_still_rejects_model_owned_execution_fields(field, value):
    with pytest.raises(ValueError, match="query 1 fields are not exact"):
        closed_projection({field: value})


def test_open_projection_also_retains_query_semantics_with_host_owned_controls(monkeypatch):
    semantic = {"queries": [deepcopy(QUERY)], "sources": [], "assessments": [], "capability_gap": "fixture"}
    monkeypatch.setattr(retrieval_execution, "_normalise_semantic", lambda value: deepcopy(semantic))
    monkeypatch.setattr(retrieval_execution, "_event_stream", lambda raw: ("thread", [], []))
    monkeypatch.setattr(retrieval_execution, "_query_sessions", lambda *args: [
        {"source_urls": [], "search_event_ids": ["EVENT-1"]}])
    monkeypatch.setattr(retrieval_execution, "_directional_evidence", lambda *args: {})
    monkeypatch.setattr(retrieval_execution, "_runtime_saturation", lambda *args: ("bounded", []))
    projected, receipt = retrieval_execution.project_runtime_retrieval(
        semantic, b"synthetic observed events", run_id="projection-test", execution_context_id="fixture",
        provider_binding_sha256="1" * 64, adapter_executable_sha256="2" * 64,
        adapter_input=canonical_bytes({"run_id": "projection-test"}) + b"\n", parent_pid=101, child_pid=102,
        started_at=COMPLETED, completed_at=COMPLETED, exit_status=0,
        stderr_sha256="3" * 64, evidence_cutoff=COMPLETED)
    assert projected["queries"][0]["purpose"] == QUERY["purpose"]
    assert receipt["query_bindings"][0]["purpose_sha256"] == sha256_text(QUERY["purpose"])
    assert projected["queries"][0]["status"] == "executed"
    assert projected["queries"][0]["executed_at"] == COMPLETED
    assert projected["queries"][0]["query_id"].startswith("QUERY-WEB-01-")
