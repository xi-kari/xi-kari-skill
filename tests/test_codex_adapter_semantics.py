from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import xi_kari_codex_authoring_adapter as adapter
from xi_kari_runtime import authoring
from xi_kari_runtime.canonical_json import canonical_bytes
from xi_kari_runtime.problem_contract import FROZEN_FIELDS


def problem():
    value = {field: "bounded argument" for field in FROZEN_FIELDS}
    value.update(evidence_cutoff="2026-09-20T00:00:00Z", retrieval_profile="closed-input", requested_stance="support", problem_action="express", advice_requested=False, deliverable_type="critique")
    return value


def output_payload():
    value = {field: {} for field in authoring.SEMANTIC_AUTHORING_FIELDS}
    value.update(
        problem_contract={**problem(), "dynamic_applicability": "applicable", "applicability_rationale": "The argument concerns repeated organizational choices."},
        dynamic_applicability="applicable", deliverable_type="critique", answer_delivery=None,
        cases=[], mechanisms=[], orders=[],
        reader_sections=[{"section_id": "section-1", "heading": "A bounded judgment", "local_judgment": "The premise does not establish the conclusion.", "paragraphs": ["The text gives no link from measured speed to responsibility allocation."], "source_bindings": []}],
    )
    return value


def test_variant_adapter_accepts_current_reader_sections_and_deliverable():
    schema = json.loads((ROOT / "schemas/xk-codex-semantic-authoring-output.schema.json").read_text("utf-8"))
    result = adapter._validate_model_output(canonical_bytes(output_payload()), schema=schema, semantic_request={"problem_contract": problem()})
    assert result["reader_sections"][0]["local_judgment"]


def test_variant_adapter_accepts_absent_optional_delivery():
    schema = json.loads((ROOT / "schemas/xk-codex-semantic-authoring-output.schema.json").read_text("utf-8"))
    schema["required"] = [field for field in schema["required"] if field != "answer_delivery"]
    payload = output_payload()
    payload.pop("answer_delivery")
    assert adapter._validate_model_output(canonical_bytes(payload), schema=schema, semantic_request={"problem_contract": problem()})


def test_variant_adapter_rejects_changed_deliverable():
    payload = output_payload()
    payload["deliverable_type"] = "decision"
    with pytest.raises(adapter.AdapterError, match="deliverable"):
        adapter._validate_model_output(canonical_bytes(payload), schema={}, semantic_request={"problem_contract": problem()})


def test_variant_request_includes_frozen_deliverable():
    authority = {field: "0" * 64 for field in adapter.CONCEPT_AUTHORITY_FIELDS}
    authority.update(schema_id="xi-kari.v3.concept-authority-binding", schema_version=1, source_candidate_count=3320, ontology_concept_count=138)
    request = authoring._adapter_request(
        {"retrieval": {}, "evidence": {}, "facts": {}},
        {"problem_contract": problem(), "mode": "closed-input", "repository_root": str(ROOT), "source_version": "v8.3", "validator_set_sha256": "0" * 64},
        {}, {}, authority, variant_kind="stance-support", generation_context_id="TEST-CONTEXT",
    )
    assert adapter._validate_semantic_request(request, repository_root=ROOT)["problem_contract"]["deliverable_type"] == "critique"
