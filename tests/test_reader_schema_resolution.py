from pathlib import Path

from scripts.xi_kari_runtime.validation import _runtime_schema_registry
from scripts.xi_kari_runtime.world_volume import _schema_validator


ROOT = Path(__file__).resolve().parents[1]


def prose_plan():
    return {
        "schema_id": "xi-kari.v3.prose-plan", "schema_version": 3, "run_id": "test",
        "formats": ["answer", "dossier", "atlas", "casebook"],
        "deliverable_type": "analysis", "delivery_mode": "full",
        "reader_sections": [{
            "section_id": "claim", "heading": "实际通道尚未成立", "local_judgment": "目前只支持局部变化。",
            "paragraphs": ["下一步需要验证变化能否持续。"], "source_bindings": [],
        }],
        "reader_beats": ["结论", "事实", "机制", "反方"], "direct_answer": "目前只支持局部变化。",
        "coverage": {}, "jargon_dump_forbidden": True, "input_packet_sha256": "0" * 64,
    }


def test_fresh_validator_resolves_reader_schema_without_network() -> None:
    errors = []
    registry = _runtime_schema_registry(ROOT, errors)
    assert errors == []
    assert list(registry["xi-kari.v3.prose-plan"].iter_errors(prose_plan())) == []


def test_semantic_schema_validator_uses_repository_bound_references() -> None:
    validator = _schema_validator("xk-prose.schema.json", str(ROOT))
    assert list(validator.iter_errors(prose_plan())) == []
