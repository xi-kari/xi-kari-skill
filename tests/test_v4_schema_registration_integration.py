"""Exact published schema ownership; schema acceptance is not runtime completion."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_xi_kari_runtime as checker
from xi_kari_runtime import schema_ownership, validation
from xi_kari_runtime.source_profile import RUNTIME_VERSION, SOURCE_VERSION


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(root, name, document):
    path = root / "schemas" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document), encoding="utf-8")


@pytest.fixture(params=["checker", "fresh"])
def registry(request):
    def build(root):
        if request.param == "checker":
            return checker._runtime_schema_registry(root)
        errors = []
        return validation._runtime_schema_registry(root, errors), errors
    return build


@pytest.fixture
def repository(tmp_path):
    shutil.copytree(ROOT / "schemas", tmp_path / "schemas")
    return tmp_path


def test_all_actual_published_v4_schema_resources_and_artifact_roots_register(registry):
    paths = sorted((ROOT / "schemas").glob("xk-*v4*.schema.json"))
    before = {path: path.read_bytes() for path in paths}
    registered, errors = registry(ROOT)
    assert errors == []
    assert len(paths) >= 20
    for path in paths:
        document = _json(path)
        assert path.name in schema_ownership.V4_SCHEMA_IDENTITIES
        assert schema_ownership.schema_identity_errors(path, document) == []
        for identifier in schema_ownership.root_schema_ids(document):
            assert registered[identifier].schema["$id"] == document["$id"]
    assert {path: path.read_bytes() for path in paths} == before
    assert (RUNTIME_VERSION, SOURCE_VERSION) == ("4.0.0", "v9.0")


def test_source_v4_multi_root_and_pure_definition_resources_keep_distinct_ownership(registry):
    registered, errors = registry(ROOT)
    assert errors == []
    assert registered["xi-kari.v4.source-lock"].schema == registered["xi-kari.v4.source-read-event"].schema
    for filename in ("xk-v4-common.schema.json", "xk-v4-formal-input.schema.json", "xk-v4-stage-inputs.schema.json"):
        identity, roots = schema_ownership.V4_SCHEMA_IDENTITIES[filename]
        assert roots == frozenset()
        assert identity not in registered
        assert _json(ROOT / "schemas" / filename)["$id"] == f"https://xi-kari.local/schemas/{identity}.schema.json"


def test_real_production_completion_schema_accepts_its_artifact_shape_only(registry):
    registered, errors = registry(ROOT)
    assert errors == []
    artifact = {"schema_id": "xi-kari.v4.completion", "schema_version": 4, "run_id": "schema-shape-only",
        "official_validation_path": "validation/attempts/official/validator-report.json", "phase_count": 13,
        "completed_at": "2026-09-30T12:00:00Z"}
    for field in ("official_validation_sha256", "chain_head_sha256", "validator_set_sha256", "manifest_sha256",
                  "final_chat_sha256", "xk12_transaction_sha256", "provider_environment_sha256",
                  "official_validation_execution_sha256", "promotion_validation_execution_sha256"):
        artifact[field] = "0" * 64
    for boundary in ("official", "promotion"):
        artifact[f"{boundary}_validation_execution_path"] = (
            f"validation/attempts/{boundary}-{'0' * 32}/execution.json"
        )
    validator = registered["xi-kari.v4.completion"]
    assert list(validator.iter_errors(artifact)) == []
    for boundary in ("official", "promotion"):
        for suffix in ("path", "sha256"):
            missing_capture = deepcopy(artifact)
            del missing_capture[f"{boundary}_validation_execution_{suffix}"]
            assert list(validator.iter_errors(missing_capture))
    artifact["schema_version"] = 3
    assert list(validator.iter_errors(artifact))


@pytest.mark.parametrize("filename", ["xk-v4-production-run.schema.json", "xk-v4-formal-input.schema.json", "xk-v4-source.schema.json"])
def test_changed_resource_uri_is_rejected_for_real_new_schema(repository, registry, filename):
    document = _json(repository / "schemas" / filename)
    document["$id"] = "https://xi-kari.local/schemas/xi-kari.v4.unknown-published-alias.schema.json"
    _write(repository, filename, document)
    _, errors = registry(repository)
    assert any("unsupported $id" in error and filename in error for error in errors)


@pytest.mark.parametrize("mutation", ["unknown_v4", "duplicate_uri", "duplicate_root"])
def test_unknown_v4_prefix_and_duplicate_uri_or_root_are_not_registered(repository, registry, mutation):
    name, document = {
        "unknown_v4": ("xk-v4-unknown.schema.json", {"$id": "https://xi-kari.local/schemas/xi-kari.v4.unknown.schema.json", "properties": {"schema_id": {"const": "xi-kari.v4.unknown"}}}),
        "duplicate_uri": ("xk-duplicate-uri.schema.json", {"$id": "https://xi-kari.local/schemas/xi-kari.v3.source-artifact.schema.json"}),
        "duplicate_root": ("xk-duplicate-root.schema.json", {"$id": "https://xi-kari.local/schemas/xi-kari.v3.other-resource.schema.json", "properties": {"schema_id": {"const": "xi-kari.v3.source-lock"}}}),
    }[mutation]
    _write(repository, name, {"$schema": "https://json-schema.org/draft/2020-12/schema", **document})
    registered, errors = registry(repository)
    assert "xi-kari.v4.unknown" not in registered
    expected = {"unknown_v4": "unsupported $id", "duplicate_uri": "$id has multiple owners",
                "duplicate_root": "schema_id has multiple owners"}[mutation]
    assert any(expected in error for error in errors)


def test_real_new_schema_missing_external_definition_reference_is_rejected(repository, registry):
    document = _json(repository / "schemas/xk-v4-production-run.schema.json")
    document["properties"]["unavailable"] = {"$ref": "https://xi-kari.local/schemas/xi-kari.v4.unpublished.schema.json#/$defs/value"}
    _write(repository, "xk-v4-production-run.schema.json", document)
    _, errors = registry(repository)
    assert any("runtime schema reference" in error and "unpublished" in error for error in errors)


def test_deleted_new_published_schema_still_fails_the_checker(repository):
    (repository / "schemas/xk-v4-production-completion.schema.json").unlink()
    errors = checker._check_runtime_schemas(repository)
    assert any("published runtime schema is missing: xk-v4-production-completion.schema.json" == error for error in errors)


def test_source_version_and_unknown_artifact_root_are_not_softened_by_registration(registry):
    registered, errors = registry(ROOT)
    assert errors == []
    value = {"schema_id": "xi-kari.v4.source-read-event", "schema_version": 4,
        "run_id": "schema-shape-only", "event_id": "event-shape-only", "ordinal": 1,
        "source_anchor": "V90-P00001", "source_unit_type": "paragraph", "reader_unit": "source",
        "source_sha256": "0" * 64, "status": "read"}
    validator = registered["xi-kari.v4.source-read-event"]
    assert list(validator.iter_errors(value)) == []
    value["source_anchor"] = "V83-P0001"
    assert list(validator.iter_errors(value))
    changed = deepcopy(_json(ROOT / "schemas/xk-v4-production-completion.schema.json"))
    changed["properties"]["schema_id"]["const"] = "xi-kari.v4.completion-unknown"
    assert schema_ownership.schema_identity_errors(Path("xk-v4-production-completion.schema.json"), changed)


def test_committed_semantic_execution_resources_have_exact_body_and_envelope_owners(registry):
    expected = {
        "request": {"xi-kari.v4.xk.semantic-execution-request"},
        "response": set(),
        "receipt": {"xi-kari.v4.xk.semantic-execution-receipt"},
        "attestation": {"xi-kari.v4.xk.semantic-execution-attestation"},
    }
    registered, errors = registry(ROOT)
    assert errors == []
    for suffix, roots in expected.items():
        name = f"xk-v4-semantic-execution-{suffix}.schema.json"
        document = _json(ROOT / "schemas" / name)
        identity = f"xi-kari.v4.xk.semantic-execution-{suffix}"
        assert schema_ownership.V4_SCHEMA_IDENTITIES[name] == (identity, frozenset(roots))
        assert document["$id"] == f"https://xi-kari.local/schemas/{identity}.schema.json"
        assert schema_ownership.root_schema_ids(document) == roots
        assert schema_ownership.schema_identity_errors(Path(name), document) == []
        for root_id in roots:
            assert registered[root_id].schema["$id"] == document["$id"]
    assert "xi-kari.v4.xk.semantic-execution-response" not in registered


@pytest.mark.parametrize("suffix", ["request", "response", "receipt", "attestation"])
def test_semantic_execution_resource_uri_mutation_is_rejected(repository, registry, suffix):
    name = f"xk-v4-semantic-execution-{suffix}.schema.json"
    document = _json(repository / "schemas" / name)
    document["$id"] = "https://xi-kari.local/schemas/xi-kari.v4.xk.semantic-execution-unpublished.schema.json"
    _write(repository, name, document)
    _, errors = registry(repository)
    assert any("unsupported $id" in error and name in error for error in errors)


def test_deleted_semantic_execution_resource_remains_required(repository):
    name = "xk-v4-semantic-execution-response.schema.json"
    (repository / "schemas" / name).unlink()
    errors = checker._check_runtime_schemas(repository)
    assert f"published runtime schema is missing: {name}" in errors
