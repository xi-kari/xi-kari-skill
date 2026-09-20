from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from tests.test_base_applicability import ROOT, base_envelope, parse


def authored_envelope():
    request, frozen, value = base_envelope()
    packet = value["semantic_packet"]
    packet["evidence"] = {"claims": [{
        "claim_id": "CLAIM-1", "text": "A recommendation does not grant permission.",
        "kind": "interpretation", "support": [{"source_id": "SOURCE-1"}],
    }]}
    packet["answer"].update(basis_refs=["CLAIM-1", "CLAIM-1-e1"])
    return request, frozen, value


@pytest.mark.parametrize("reference", ["SOURCE-1", "MISSING-1"])
def test_base_parser_rejects_unresolved_answer_basis_before_read_receipts(monkeypatch, reference):
    request, frozen, value = authored_envelope()
    value["semantic_packet"]["answer"]["basis_refs"] = [reference]
    before = deepcopy(value)
    with pytest.raises(ValueError, match="answer.basis_refs.*" + reference):
        parse(value, request, frozen, monkeypatch)
    assert value == before


def test_base_parser_accepts_claim_and_derived_evidence_identity(monkeypatch):
    request, frozen, value = authored_envelope()
    parsed = parse(value, request, frozen, monkeypatch)
    assert parsed["answer"]["basis_refs"] == ["CLAIM-1", "CLAIM-1-e1"]


@pytest.mark.parametrize("references", [[], "CLAIM-1", [None], [""], ["CLAIM-1", "CLAIM-1"]])
def test_base_parser_rejects_malformed_answer_basis(monkeypatch, references):
    request, frozen, value = authored_envelope()
    value["semantic_packet"]["answer"]["basis_refs"] = references
    with pytest.raises(ValueError, match="schema validation|answer.basis_refs"):
        parse(value, request, frozen, monkeypatch)


def test_base_parser_rejects_missing_answer_basis(monkeypatch):
    request, frozen, value = authored_envelope()
    del value["semantic_packet"]["answer"]["basis_refs"]
    with pytest.raises(ValueError, match="schema validation|answer.basis_refs"):
        parse(value, request, frozen, monkeypatch)


def test_author_preflight_reports_real_reference_and_body_errors_without_writing(tmp_path):
    _, _, value = authored_envelope()
    value["semantic_packet"]["answer"]["basis_refs"] = ["SOURCE-1"]
    output = tmp_path / "semantic-output.json"
    raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
    output.write_bytes(raw)
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    result = subprocess.run(
        [sys.executable, "-B", str(ROOT / "scripts/check_authoring_output.py"), str(output)],
        capture_output=True, text=True, encoding="utf-8", cwd=tmp_path,
    )
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert report["passed"] is False
    assert any("answer.basis_refs" in error and "SOURCE-1" in error for error in report["errors"])
    assert any("body" in error for error in report["errors"])
    after = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    assert before == after
    assert report["runtime_sealed"] is False


def test_dynamic_answer_reference_validation_retains_red_team_context():
    from xi_kari_runtime.contracts import validate_packet_references
    from xi_kari_runtime.evidence import build_evidence_ledger

    statement = "A delayed handoff can postpone the next task."
    retrieval = {"sources": [{
        "source_id": "SOURCE-1", "origin": "user_material",
        "assessment_verdict": "admitted",
    }]}
    evidence = build_evidence_ledger(
        run_id="red-team-reference-test", retrieval_index=retrieval,
        claims=[{
            "claim_id": "CLAIM-1", "text": statement, "kind": "user_material",
            "support": [{"source_id": "SOURCE-1", "summary": statement}],
        }],
    )
    packet = {
        "dynamic_applicability": "applicable",
        "evidence": evidence,
        "claim_mechanism_graph": {
            "central_claim_id": "CLAIM-1",
            "claims": [{
                "claim_id": "CLAIM-1", "statement": statement, "kind": "mechanism",
                "evidence_refs": ["EVIDENCE-1"], "mechanism_ids": ["MECHANISM-1"],
            }],
            "evidence": [{
                "evidence_id": "EVIDENCE-1", "identity": "source_claim",
                "source_refs": ["SOURCE-1"], "xk3_evidence_refs": ["CLAIM-1-e1"],
            }],
            "mechanisms": [{"mechanism_id": "MECHANISM-1"}],
            "explanations": [{
                "explanation_id": "EXPLANATION-1", "claim_ids": ["CLAIM-1"],
                "mechanism_ids": ["MECHANISM-1"],
            }],
        },
        "answer": {"basis_refs": ["CLAIM-1", "MECHANISM-1", "EVIDENCE-1"]},
        "verdict": {
            "judgment_kind": "best-current",
            "current_best_judgment": {"best_explanation_id": "EXPLANATION-1"},
            "five_verdicts": [{"claim_evidence_edges": [{
                "claim_id": "CLAIM-1", "evidence_id": "EVIDENCE-1",
            }]}],
        },
        "red_team": {
            "status": "completed", "attacked_evidence_refs": ["EVIDENCE-1"],
            "surviving_claims": ["CLAIM-1"], "attacked_claim_ids": ["CLAIM-1"],
            "attacked_mechanism_ids": ["MECHANISM-1"],
            "attacked_explanation_ids": ["EXPLANATION-1"],
            "attacked_action_option_ids": [], "repair_required": False,
        },
    }
    before = deepcopy(packet)
    validate_packet_references(
        packet, evidence_ledger=evidence, retrieval_index=retrieval,
        repository_root=ROOT,
    )
    assert packet == before
    packet["red_team"]["attacked_mechanism_ids"] = ["MECHANISM-MISSING"]
    with pytest.raises(ValueError, match="red-team attack target does not resolve"):
        validate_packet_references(
            packet, evidence_ledger=evidence, retrieval_index=retrieval,
            repository_root=ROOT,
        )
