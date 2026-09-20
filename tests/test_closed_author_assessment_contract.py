import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from xi_kari_runtime import execution
from xi_kari_runtime.closed_input import _normalize_closed_semantic, freeze_closed_input_materials


@pytest.mark.parametrize("field", ("source_lineage", "conflict_source_ids"))
def test_closed_prompt_names_reference_fields_and_frozen_ids(field):
    request = {"mode": "closed-input", "source_inputs": {"closed_input_materials": [
        {"source_id": "SOURCE-A", "title": "First", "content": "First material"},
        {"source_id": "SOURCE-B", "title": "Second", "content": "Second material"},
    ]}}
    instructions = execution._base_prompt(request).decode("utf-8").split("运行时请求（只读绑定）：")[0]
    assert field in instructions
    assert "SOURCE-A" in instructions and "SOURCE-B" in instructions
    assert "空数组" in instructions
    assert "解释文字" in instructions


@pytest.mark.parametrize("field", ("source_lineage", "conflict_source_ids"))
def test_closed_reference_schema_requires_unique_text_ids(field):
    schema = json.loads((ROOT / "schemas/xk-base-authoring-output.schema.json").read_text("utf-8"))
    closed = schema["$defs"]["modelRetrieval"]["oneOf"][1]
    validator = Draft202012Validator({"$defs": schema["$defs"], **closed})
    for values in ([], ["SOURCE-A"], ["SOURCE-A", "SOURCE-B"]):
        assert validator.is_valid({"mode": "closed-input", "assessments": [{field: values}]})
    for values in ([{}], [7], ["SOURCE-A", "SOURCE-A"]):
        assert not validator.is_valid({"mode": "closed-input", "assessments": [{field: values}]})


@pytest.mark.parametrize("field", ("source_lineage", "conflict_source_ids"))
def test_reference_resolution_still_rejects_explanation_and_unknown_ids(field):
    materials = [{"source_id": "SOURCE-TERMS", "title": "Terms", "content": "A recommendation is not authorization."}]
    retrieval = {"mode": "closed-input", "queries": [
        {"direction": "authoritative_definition", "query": "Recommendation and permission", "purpose": "Interpret the material"}
    ], "sources": [{**materials[0], "origin": "user_material"}], "assessments": [
        {"source_id": "SOURCE-TERMS", "source_lineage": [], "conflict_source_ids": []}
    ], "saturation_status": "bounded", "capability_gap": "none", "remaining_unknowns": []}
    frozen, manifest = freeze_closed_input_materials(materials)
    kwargs = {"manifest": manifest, "run_id": "reference-contract", "completed_at": "2026-09-20T00:00:00Z"}
    for invalid in ("材料由请求直接提供，未经过外部检索补充。", "SOURCE-MISSING"):
        retrieval["assessments"][0][field] = [invalid]
        with pytest.raises(ValueError, match=field + " does not resolve"):
            _normalize_closed_semantic(retrieval, frozen, **kwargs)
    retrieval["assessments"][0][field] = []
    semantic, *_ = _normalize_closed_semantic(retrieval, frozen, **kwargs)
    assert semantic["assessments"][0][field] == []


def test_closed_reference_constraints_do_not_change_open_schema_branch():
    schema = json.loads((ROOT / "schemas/xk-base-authoring-output.schema.json").read_text("utf-8"))
    branch = schema["$defs"]["modelRetrieval"]["oneOf"][0]
    validator = Draft202012Validator({"$defs": schema["$defs"], **branch})
    assert validator.is_valid({"mode": "open-world", "assessments": [{
        "source_lineage": ["https://example.org/upstream"], "conflict_source_ids": ["source-b"]
    }]})


@pytest.mark.parametrize("mode", ("closed-input", "open-world"))
def test_author_prompt_preserves_table_relationships_and_raw_read_fallback(mode):
    prompt = execution._base_prompt({"mode": mode}).decode("utf-8")
    assert "表格的表、行、单元格关系" in prompt
    assert "原样分段阅读" in prompt
    assert "截断" in prompt
