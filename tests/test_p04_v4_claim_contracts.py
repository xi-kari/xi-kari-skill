from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from tests.test_judgment_semantics import base_graph
from tests.test_natural_contract_freeze import request_and_final
from xi_kari_runtime import claims, materialization
from xi_kari_runtime.evidence import build_evidence_ledger
from xi_kari_runtime.semantic_projection import semantic_atom_paths


STAGES = (
    "world_state",
    "transformation",
    "mechanism",
    "recursion",
    "forecast",
    "action_choice",
)
DEPENDENCY_ROLES = (
    "inferential_requires",
    "protocol_requires",
    "specializes",
    "applies_to",
)
BASIS_KINDS = (
    "source_fact",
    "domain_empirical",
    "text_interpretation",
    "formal_proof",
    "normative_argument",
    "formal_framework_instance",
)


def _stage_record(status: str, rationale: str) -> dict[str, object]:
    return {
        "status": status,
        "rationale": rationale,
        "source_refs": ["V90-P00111"],
        "dependency_refs": [],
    }


def _six_stage_applicability(
    *, mechanism: str = "applicable"
) -> dict[str, dict[str, object]]:
    statuses = {
        "world_state": "applicable",
        "transformation": "applicable",
        "mechanism": mechanism,
        "recursion": "applicable",
        "forecast": "applicable",
        "action_choice": "not_applicable",
    }
    return {
        stage: _stage_record(statuses[stage], f"Bounded {stage} disposition.")
        for stage in STAGES
    }


def _basis(kind: str, material_ref: str) -> dict[str, object]:
    return {
        "kind": kind,
        "scope": {
            "object": "bounded proposition",
            "population": "unit-test materials",
            "window": "six weeks",
            "target": "the stated claim only",
        },
        "material_refs": [material_ref],
    }


def _qualification(
    *, requested: bool = False, qualified: bool = False
) -> dict[str, object]:
    return {
        "requested": requested,
        "family": "G" if requested else "not_applicable",
        "concept_ref": "V90-CANON-G2" if requested else None,
        "instance_refs": ["INSTANCE-G2-1"] if requested else [],
        "status": "qualified" if qualified else "unqualified" if requested else "not_requested",
        "result_status": "supported" if qualified else "unsupported_or_undecided" if requested else "not_evaluated",
        "reason": "Formal qualification is recorded independently of ordinary support.",
    }


def _support_checks() -> dict[str, dict[str, object]]:
    return {
        "source_exists": {
            "status": "passed",
            "basis_refs": ["V90-P00142"],
            "reason": "The bound material exists.",
        },
        "quotation_accurate": {
            "status": "not_applicable",
            "basis_refs": [],
            "reason": "This claim does not quote the material verbatim.",
        },
        "passage_supports_claim": {
            "status": "passed",
            "basis_refs": ["V90-P00144"],
            "reason": "The passage supports the bounded proposition.",
        },
        "world_fact_supported": {
            "status": "passed",
            "basis_refs": ["V90-P00190"],
            "reason": "The factual use has independent support.",
        },
    }


def _upgrade_evidence(record: dict[str, object]) -> None:
    source_ref = str(record["source_refs"][0])
    record.update(
        evidence_identity={
            "source_revision": "REV-1",
            "canonical_locator": f"{source_ref}:P1",
            "content_sha256": hashlib.sha256(source_ref.encode()).hexdigest(),
            "lineage_refs": [f"LINEAGE-{source_ref}"],
        },
        support_checks=_support_checks(),
        research_context={
            "research_design": "bounded documentary comparison",
            "read_extent": "the cited passage and its immediate context",
            "provenance_refs": [source_ref],
            "independence_key": f"LINEAGE-{source_ref}",
        },
        availability_status="available",
        visibility="public",
        protected_review=None,
    )


def _v4_graph() -> dict[str, object]:
    graph = deepcopy(base_graph())
    graph.update(
        schema_id="xi-kari.v4.xk.claim-mechanism-graph",
        schema_version=4,
        source_version="v9.0",
        ontology_refs=["V90-CANON-D0", "V90-CANON-G2"],
        source_anchors=["V90-P00111", "V90-P00142", "V90-P00158"],
        applicability=_six_stage_applicability(),
    )
    for evidence in graph["evidence"]:
        _upgrade_evidence(evidence)
    for index, claim in enumerate(graph["claims"]):
        claim.pop("depends_on_claim_ids")
        claim["claim_basis"] = _basis(
            BASIS_KINDS[index % len(BASIS_KINDS)], claim["evidence_refs"][0]
        )
        claim["formal_qualification"] = _qualification(requested=index == 1)
        claim["responsibility_refs"] = ["V90-CANON-G2"] if index == 1 else []
    for countercase in graph["countercases"]:
        countercase["rival_target"] = "mechanism"
    root = "CLAIM-FACTUAL"
    children = (
        "CLAIM-MECHANISM",
        "CLAIM-STRUCTURAL",
        "CLAIM-PREDICTION",
        "CLAIM-VALUE",
    )
    graph["dependency_edges"] = [
        {
            "edge_id": f"EDGE-{index}",
            "from_id": child,
            "to_ref": {"kind": "claim", "id": root},
            "role": role,
            "source_refs": ["V90-P00158"],
            "condition": "This bounded route is selected.",
            "scope": f"Only the {child} use governed by this edge.",
        }
        for index, (child, role) in enumerate(
            zip(children, DEPENDENCY_ROLES, strict=True), start=1
        )
    ]
    graph["input_requirements"] = [
        {
            "requirement_id": "INPUT-REQ-1",
            "from_id": "CLAIM-RESPONSIBILITY",
            "input_ref": "INPUT-PRIVATE-MOTIVE",
            "status": "undetermined",
            "source_refs": ["V90-P00209"],
            "condition": "Only if motive attribution is requested.",
            "scope": "Motive attribution only.",
        }
    ]
    return graph


def _nonmechanistic_interpretation_graph() -> dict[str, object]:
    graph = _v4_graph()
    graph["applicability"] = {
        stage: _stage_record(
            "not_applicable", f"Text interpretation does not request the {stage} stage."
        )
        for stage in STAGES
    }
    graph["central_claim_id"] = "CLAIM-FACTUAL"
    graph["mechanisms"] = []
    graph["claims"] = [
        claim
        for claim in graph["claims"]
        if claim["claim_id"] in {"CLAIM-FACTUAL", "CLAIM-STRUCTURAL"}
    ]
    for claim in graph["claims"]:
        claim["mechanism_ids"] = []
        claim["claim_basis"] = _basis("text_interpretation", claim["evidence_refs"][0])
        claim["formal_qualification"] = _qualification()
        claim["responsibility_refs"] = []
    graph["dependency_edges"] = []
    graph["input_requirements"] = []
    graph["cases"] = []
    graph["explanations"] = [
        {
            "explanation_id": f"EXPLAIN-{kind.upper()}",
            "kind": kind,
            "claim_ids": claim_ids,
            "mechanism_ids": [],
            "residual_ids": [],
            "rationale": rationale,
            "applicability": applicability,
            "explanandum": "Meaning of the supplied passage.",
        }
        for kind, claim_ids, rationale, applicability in (
            ("simple-baseline", ["CLAIM-FACTUAL"], "The literal reading is the bounded baseline.", "applicable"),
            ("main", ["CLAIM-FACTUAL"], "Context and wording support the main interpretation.", "applicable"),
            ("strongest-rival", ["CLAIM-STRUCTURAL"], "A competing reading is retained without inventing a mechanism.", "applicable"),
            ("mixture", [], "No mixture claim is requested for this text-only question.", "not_applicable"),
            ("residual", [], "Search limits are recorded without fabricating a residual mechanism.", "not_applicable"),
        )
    ]
    graph["countercases"] = [
        {
            "countercase_id": "COUNTER-MEANING",
            "attacks_claim_ids": ["CLAIM-FACTUAL"],
            "attacks_mechanism_ids": [],
            "rival_target": "meaning",
            "conditions": ["The disputed phrase is read in its wider paragraph."],
            "expected_signal": "The rival reading fits the wider paragraph better.",
            "reverse_signal": "The rival reading contradicts the wider paragraph.",
            "decision_impact": "Narrow or withdraw the main interpretation.",
            "source_refs": ["SOURCE-FACTUAL"],
        }
    ]
    return graph


def test_validate_claim_graph_dispatches_v4_and_preserves_orthogonal_fields() -> None:
    checked = claims.validate_claim_graph(_v4_graph(), repository_root=ROOT)

    assert checked["schema_version"] == 4
    assert tuple(checked["applicability"]) == STAGES
    assert {claim["claim_basis"]["kind"] for claim in checked["claims"]} >= set(BASIS_KINDS)
    domain_claim = next(
        claim for claim in checked["claims"] if claim["claim_basis"]["kind"] == "domain_empirical"
    )
    assert domain_claim["evidence_refs"]
    assert domain_claim["formal_qualification"]["status"] == "unqualified"
    assert domain_claim["formal_qualification"]["result_status"] == "unsupported_or_undecided"
    assert {edge["role"] for edge in checked["dependency_edges"]} == set(DEPENDENCY_ROLES)
    assert checked["input_requirements"][0]["input_ref"] == "INPUT-PRIVATE-MOTIVE"


def test_evidence_builder_v4_preserves_basis_qualification_and_material_checks() -> None:
    basis = _basis("text_interpretation", "SOURCE-1")
    qualification = _qualification()
    ledger = build_evidence_ledger(
        run_id="p04-evidence",
        contract_version=4,
        retrieval_index={
            "run_id": "p04-evidence",
            "sources": [
                {
                    "source_id": "SOURCE-1",
                    "origin": "user_material",
                    "assessment_verdict": "admitted",
                    "source_revision": "REV-1",
                    "canonical_locator": "SOURCE-1:P1",
                    "content_sha256": "c" * 64,
                    "lineage_refs": ["LINEAGE-1"],
                    "research_design": "bounded textual comparison",
                    "read_extent": "the cited passage and immediate context",
                    "provenance_refs": ["SOURCE-1"],
                    "independence_key": "LINEAGE-1",
                    "availability_status": "available",
                    "visibility": "public",
                    "protected_review": None,
                }
            ],
        },
        claims=[
            {
                "claim_id": "CLAIM-1",
                "text": "The passage supports a bounded interpretation.",
                "kind": "interpretation",
                "support": [
                    {
                        "source_id": "SOURCE-1",
                        "summary": "The cited passage is the interpretation material.",
                        "support_checks": _support_checks(),
                    }
                ],
                "claim_basis": basis,
                "formal_qualification": qualification,
                "responsibility_refs": [],
            }
        ],
    )

    assert ledger["schema_version"] == 4
    assert ledger["claims"][0]["claim_basis"] == basis
    assert ledger["claims"][0]["formal_qualification"] == qualification
    assert ledger["evidence"][0]["evidence_identity"]["canonical_locator"] == "SOURCE-1:P1"
    assert ledger["evidence"][0]["support_checks"] == _support_checks()


def test_only_inferential_dependency_propagates_as_a_hard_failure() -> None:
    graph = _v4_graph()
    next(
        evidence for evidence in graph["evidence"] if evidence["evidence_id"] == "E-FACTUAL"
    )["support_status"] = "invalidated"

    constraints = claims.claim_constraints(graph)

    assert constraints["CLAIM-MECHANISM"]["blocked"] is True
    assert constraints["CLAIM-MECHANISM"]["blocking_claim_ids"] == ["CLAIM-FACTUAL"]
    for claim_id in ("CLAIM-STRUCTURAL", "CLAIM-PREDICTION", "CLAIM-VALUE", "CLAIM-RESPONSIBILITY"):
        assert constraints[claim_id]["blocked"] is False
        assert constraints[claim_id]["blocking_claim_ids"] == []


def test_text_interpretation_accepts_a_nonmechanistic_countercase() -> None:
    checked = claims.validate_claim_graph(
        _nonmechanistic_interpretation_graph(), repository_root=ROOT
    )

    assert checked["mechanisms"] == []
    assert checked["countercases"][0]["rival_target"] == "meaning"
    assert checked["countercases"][0]["attacks_mechanism_ids"] == []
    assert all(
        checked["applicability"][stage]["status"] == "not_applicable"
        for stage in STAGES
    )


def test_specific_mechanism_claim_cannot_escape_with_not_applicable() -> None:
    graph = _v4_graph()
    graph["applicability"]["mechanism"] = _stage_record(
        "not_applicable", "The author attempted to skip mechanism validation."
    )

    with pytest.raises(
        claims.ClaimMechanismError,
        match=r"mechanism.*not[_ -]applicable|not[_ -]applicable.*mechanism",
    ):
        claims.validate_claim_graph(graph, repository_root=ROOT)


def test_disk_reread_and_fresh_reader_projection_keep_v4_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, problem = request_and_final()
    packet = {
        "problem_contract": problem,
        "applicability": _six_stage_applicability(),
        "claim_mechanism_graph": _v4_graph(),
    }
    packet["visibility_ledger"] = {
        "entries": [
            {
                "canonical_path": path,
                "classification": "public",
                "disclosure": "include",
                "purpose": "P04 fresh-process projection test",
                "authority_refs": [],
                "protection_reason": None,
            }
            for path in semantic_atom_paths(packet)
        ]
    }
    contract = {
        "run_id": "p04-roundtrip",
        "question": problem["question"],
        "mode": "open-world",
        "evidence_cutoff": problem["evidence_cutoff"],
        "problem_contract": problem,
        "problem_contract_sha256": "a" * 64,
        "stance_neutrality_key": "b" * 64,
        "privacy_contract": None,
        "contract_profile": "production-authoring-v3",
    }
    run_dir = tmp_path / "run"
    (run_dir / "continuation").mkdir(parents=True)
    monkeypatch.setattr(materialization, "load_concept_authority", lambda root: ([], {}))

    persisted = materialization._load_packet_from_disk(
        run_dir,
        packet,
        contract=contract,
        repository_root=ROOT,
    )
    assert persisted["applicability"] == packet["applicability"]
    assert (
        persisted["claim_mechanism_graph"]["claims"][0]["claim_basis"]
        == packet["claim_mechanism_graph"]["claims"][0]["claim_basis"]
    )

    probe = r'''
import json
from pathlib import Path
import sys

run_dir = Path(sys.argv[1])
repo = Path(sys.argv[2])
sys.path.insert(0, str(repo / "scripts"))
from xi_kari_runtime.semantic_projection import reader_projection_units
from xi_kari_runtime.validation import _load_packet

errors = []
packet = _load_packet(run_dir, errors)
if errors or packet is None:
    raise SystemExit("; ".join(errors) or "disk packet missing")
paths = sorted({
    path
    for unit in reader_projection_units(packet)
    for path in unit.get("source_paths", [])
})
print(json.dumps(paths))
'''
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run(
        [sys.executable, "-c", probe, str(run_dir), str(ROOT)],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    projected_paths = set(json.loads(result.stdout))
    assert {
        "applicability.mechanism.status",
        "claim_mechanism_graph.claims[0].claim_basis.kind",
        "claim_mechanism_graph.claims[0].formal_qualification.status",
        "claim_mechanism_graph.claims[0].formal_qualification.result_status",
    } <= projected_paths


def test_formal_template_cannot_grant_instance_qualification() -> None:
    graph = _v4_graph()
    graph['claims'][1]['formal_qualification'] = _qualification(requested=True, qualified=True)
    with pytest.raises(claims.ClaimMechanismError, match='verified real instance'):
        claims.validate_claim_graph(graph, repository_root=ROOT)


def test_instance_result_cannot_replace_qualification_state() -> None:
    graph = _v4_graph()
    graph['claims'][1]['formal_qualification']['status'] = 'supported'
    with pytest.raises(claims.ClaimMechanismError, match='formal_qualification.status'):
        claims.validate_claim_graph(graph, repository_root=ROOT)


def test_input_availability_cannot_be_a_fifth_dependency_role() -> None:
    graph = _v4_graph()
    graph['dependency_edges'][0]['role'] = 'input_dependencies'
    with pytest.raises(claims.ClaimMechanismError, match='role'):
        claims.validate_claim_graph(graph, repository_root=ROOT)


def test_six_stage_contract_rejects_a_missing_applicability_record() -> None:
    graph = _v4_graph()
    del graph['applicability']['forecast']
    with pytest.raises(claims.ClaimMechanismError, match='forecast'):
        claims.validate_claim_graph(graph, repository_root=ROOT)


def test_protocol_cycles_limit_use_without_becoming_hard_premises() -> None:
    graph = _v4_graph()
    edge = deepcopy(graph['dependency_edges'][0])
    edge.update(edge_id='EDGE-METHOD-1', from_id='CLAIM-STRUCTURAL', role='protocol_requires')
    reverse = deepcopy(edge)
    reverse.update(edge_id='EDGE-METHOD-2', from_id='CLAIM-FACTUAL', to_ref={'kind': 'claim', 'id': 'CLAIM-STRUCTURAL'})
    graph['dependency_edges'] = [edge, reverse]
    graph['evidence'][0]['support_status'] = 'invalidated'
    checked = claims.validate_claim_graph(graph, repository_root=ROOT)
    constraints = claims.claim_constraints(checked)
    assert constraints['CLAIM-FACTUAL']['blocked'] is True
    assert constraints['CLAIM-STRUCTURAL']['blocked'] is False
    assert constraints['CLAIM-STRUCTURAL']['blocked_use_refs'] == ['EDGE-METHOD-1']


def test_unselected_route_does_not_add_an_inferential_parent() -> None:
    graph = _v4_graph()
    graph['dependency_edges'][0]['route_ref'] = 'ROUTE-R2'
    graph['selected_route_ids'] = ['ROUTE-R0']
    graph['evidence'][0]['support_status'] = 'invalidated'
    constraints = claims.claim_constraints(graph)
    assert constraints['CLAIM-MECHANISM']['blocked'] is False
    assert constraints['CLAIM-MECHANISM']['blocking_claim_ids'] == []


def test_no_reasonable_rival_preserves_search_limits_without_inventing_one() -> None:
    graph = _nonmechanistic_interpretation_graph()
    graph['explanations'] = graph['explanations'][:2]
    graph['countercases'] = []
    graph['rival_assessment'] = {
        'status': 'no_reasonable_rival',
        'reason': 'No material in the bounded supplied passage supports another reading.',
        'search_scope': 'The passage and its immediate paragraph only.',
        'failure_conditions': ['A wider paragraph supplies a supported competing reading.'],
    }
    checked = claims.validate_claim_graph(graph, repository_root=ROOT)
    assert checked['mechanisms'] == []
    assert len(checked['explanations']) == 2
    assert checked['rival_assessment']['search_scope'] == graph['rival_assessment']['search_scope']


def test_invalid_protected_material_does_not_leak_its_value_in_validation_errors() -> None:
    graph = _v4_graph()
    secret = 'PRIVATE-P04-VALUE-MUST-STAY-OUT-OF-ERRORS'
    graph['evidence'][0]['support_checks']['source_exists']['status'] = secret
    graph['evidence'][0]['visibility'] = 'withheld_for_protection'
    graph['evidence'][0]['protected_review'] = {
        'basis': 'Keep the source material private.',
        'minimal_scope': 'Only the source record.',
        'review_at': '2030-01-01T00:00:00Z',
        'trusted_verifier_ref': 'VERIFIER-1',
    }
    with pytest.raises(claims.ClaimMechanismError) as caught:
        claims.validate_claim_graph(graph, repository_root=ROOT)
    assert secret not in str(caught.value)
