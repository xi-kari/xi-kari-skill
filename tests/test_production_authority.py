import importlib.util
import json
from pathlib import Path
import sys

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from xi_kari_runtime import authoring, materialization
from xi_kari_runtime.canonical_json import canonical_bytes
from xi_kari_runtime.source_profile import RUNTIME_VERSION


def test_legacy_adapter_cannot_be_bound():
    with pytest.raises(ValueError, match="profile|production"):
        authoring.bind_semantic_authoring_adapter(sys.executable, profile="legacy-fixture")


def test_legacy_receipt_protocol_is_not_a_supported_authority():
    binding = {
        "protocol": "xi-kari.v3.semantic-authoring-adapter/v1", "argv": [sys.executable],
        "argv_sha256": authoring.sha256_json([sys.executable]), "executable_path": sys.executable,
        "executable_sha256": "0" * 64, "timeout_seconds": 120,
    }
    with pytest.raises(ValueError, match="unavailable|production"):
        authoring.require_semantic_authoring_adapter(binding, verify_executable=False)


def test_current_runtime_version_comes_from_source_profile():
    assert materialization.RUNTIME_VERSION == RUNTIME_VERSION == "3.0.0"


def test_full_source_provider_timeout_accepts_two_hours():
    binding = authoring.bind_base_authoring_provider(Path(sys.executable).resolve(), mode="closed-input", repository_root=ROOT, timeout_seconds=7200)
    assert authoring.require_base_authoring_provider(binding, mode="closed-input", verify_executable=False)["timeout_seconds"] == 7200


@pytest.mark.parametrize("value", [True, 0, -1, 7201])
def test_provider_timeout_rejects_invalid_or_unbounded_values(value):
    with pytest.raises(ValueError, match="timeout"):
        authoring.bind_base_authoring_provider(sys.executable, mode="closed-input", repository_root=ROOT, timeout_seconds=value)


def test_full_source_timeout_default_is_twenty_minutes():
    assert authoring.DEFAULT_ADAPTER_TIMEOUT_SECONDS == 1200


def test_semantic_variants_keep_the_full_reader_output():
    assert {"reader_sections", "deliverable_type", "answer_delivery"}.issubset(authoring.SEMANTIC_AUTHORING_FIELDS)
    payload = {field: None for field in authoring.SEMANTIC_AUTHORING_FIELDS}
    payload["reader_sections"] = [{"text": "Complete chapter"}]
    payload["deliverable_type"] = "analysis"
    payload.pop("answer_delivery", None)
    assert authoring._parse_semantic_payload(canonical_bytes(payload))["reader_sections"] == payload["reader_sections"]
    payload.pop("reader_sections")
    with pytest.raises(ValueError, match="semantic-only|incomplete"):
        authoring._parse_semantic_payload(canonical_bytes(payload))


@pytest.mark.parametrize("filename", ["xk-run.schema.json", "xk-capability.schema.json"])
def test_active_schema_rejects_legacy_contract_profiles(filename):
    schema = json.loads((ROOT / "schemas" / filename).read_text("utf-8"))
    profile = schema["properties"]["contract_profile"]
    validator = Draft202012Validator(profile)
    assert not validator.is_valid("legacy-fixture-v3")
    assert not validator.is_valid("production-authoring-v2")
    assert validator.is_valid("production-authoring-v3")


def test_public_preflight_rejects_caller_supplied_read_receipts(tmp_path):
    with pytest.raises(ValueError, match="read trace|execute"):
        materialization.prepare_run(tmp_path / "untouched", problem_contract={}, contract_profile="production-authoring-v3", semantic_authoring_profile="production-codex", semantic_read_trace_path=tmp_path / "claimed-read.json")
    assert not (tmp_path / "untouched").exists()


def test_cli_default_timeout_and_legacy_profile_rejection():
    spec = importlib.util.spec_from_file_location("xi_kari_cli_test", ROOT / "scripts/xi_kari_runtime.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parser = module.build_parser()
    args = parser.parse_args(["execute", "--request-text", "Analyze", "--codex-provider-executable", sys.executable])
    assert args.timeout_seconds == 1200
    with pytest.raises(SystemExit):
        parser.parse_args(["prepare", "--contract-profile", "legacy-fixture-v3", "--semantic-authoring-profile", "legacy-fixture"])


def test_production_preflight_reads_real_source_without_creating_a_run(tmp_path):
    from xi_kari_runtime.problem_contract import FROZEN_FIELDS

    problem = {field: "bounded task" for field in FROZEN_FIELDS}
    problem.update(evidence_cutoff="2026-09-20T00:00:00Z", retrieval_profile="closed-input", requested_stance="neutral", problem_action="explain", advice_requested=False, deliverable_type="analysis")
    destination = tmp_path / "never-created"
    result = materialization.prepare_run(
        destination, problem_contract=problem, mode="closed-input", repository_root=ROOT,
        contract_profile="production-authoring-v3", semantic_authoring_profile="production-codex",
        codex_provider_executable=Path(sys.executable).resolve(),
    )
    assert result["preflight_only"] is True
    assert result["run_created"] is result["analysis_complete"] is False
    assert result["source_unit_count"] > 0
    assert not destination.exists()


def test_historical_run_status_is_rejected_without_rewriting(tmp_path):
    contract = {"schema_id": "xi-kari.v2.run-contract", "schema_version": 2, "source_version": "v8.2", "runtime_version": "2.1.0", "contract_profile": "legacy-fixture-v2"}
    path = tmp_path / "run-contract.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    original = path.read_bytes()
    with pytest.raises(ValueError, match="v8.3|incompatible"):
        materialization.status_run(tmp_path)
    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]
