from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_xi_kari_runtime as checker
from xi_kari_runtime import validation


@pytest.fixture(params=["checker", "fresh"])
def registry(request):
    def build(root):
        if request.param == "checker":
            return checker._runtime_schema_registry(root)
        errors = []
        return validation._runtime_schema_registry(root, errors), errors

    return build


def _schema(identifier, *, uri=None):
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": uri or f"https://xi-kari.local/schemas/{identifier}.schema.json",
        "type": "object",
        "required": ["schema_id"],
        "properties": {"schema_id": {"const": identifier}},
    }


def _write(root, filename, value):
    directory = root / "schemas"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_published_schemas_register_without_nested_owner_collisions(registry):
    registered, errors = registry(ROOT)
    assert errors == []
    assert {
        "xi-kari.v4.analysis-packet",
        "xi-kari.v4.xk.claim-mechanism-graph",
        "xi-kari.v4.semantic-read-trace-input",
        "xi-kari.v3.prose-plan",
        "xi-kari.v3.source-lock",
        "xi-kari.v3.terminal-record",
    } <= set(registered)
    assert "xi-kari.v3.base-authoring-output" not in registered
    assert "xi-kari.v4.evidence-ledger" not in registered


@pytest.mark.parametrize("module", [checker, validation])
def test_only_same_instance_root_branches_supply_identity(module):
    value = {
        "oneOf": [{"$ref": "#/$defs/a"}, {"$ref": "#/$defs/b"}],
        "$defs": {
            "a": {
                "allOf": [
                    {"properties": {"schema_id": {"const": "xi-kari.v3.a"}}},
                    {"$ref": "#/$defs/cycle"},
                ],
                "properties": {
                    "child": {"$ref": "#/$defs/unused"},
                },
            },
            "b": {"properties": {"schema_id": {"const": "xi-kari.v3.b"}}},
            "cycle": {"$ref": "#/$defs/a"},
            "unused": {"properties": {"schema_id": {"const": "xi-kari.v3.unused"}}},
        },
        "if": {"properties": {"schema_id": {"const": "xi-kari.v3.predicate"}}},
        "not": {"properties": {"schema_id": {"const": "xi-kari.v3.forbidden"}}},
        "items": {"properties": {"schema_id": {"const": "xi-kari.v3.item"}}},
    }
    assert module._schema_id_constants(value) == {"xi-kari.v3.a", "xi-kari.v3.b"}


def test_unreferenced_compatibility_marker_cannot_own_an_artifact(tmp_path, registry):
    schema = _schema("xi-kari.v3.envelope")
    schema.pop("required")
    schema["properties"] = {"data": {"type": "object"}}
    schema["$defs"] = {"marker": _schema("xi-kari.v3.compatibility-marker")}
    _write(tmp_path, "xk-envelope.schema.json", schema)
    registered, errors = registry(tmp_path)
    assert errors == []
    assert registered == {}


def test_two_root_owners_are_rejected(tmp_path, registry):
    identifier = "xi-kari.v3.duplicate"
    _write(tmp_path, "xk-first.schema.json", _schema(identifier))
    _write(
        tmp_path,
        "xk-second.schema.json",
        _schema(identifier, uri="https://xi-kari.local/schemas/xi-kari.v3.second.schema.json"),
    )
    _, errors = registry(tmp_path)
    assert any("multiple owners" in error and identifier in error for error in errors)


def test_duplicate_resource_uri_is_rejected(tmp_path, registry):
    first = _schema("xi-kari.v3.first")
    second = _schema("xi-kari.v3.second", uri=first["$id"])
    _write(tmp_path, "xk-first.schema.json", first)
    _write(tmp_path, "xk-second.schema.json", second)
    _, errors = registry(tmp_path)
    assert any("$id has multiple owners" in error for error in errors)


@pytest.mark.parametrize("uri", [
    "https://xi-kari.local/schemas/xi-kari.v4.unknown.schema.json",
    "https://xi-kari.local/schemas/xi-kari.v40.common.schema.json",
    "https://example.invalid/schemas/xi-kari.v3.common.schema.json",
])
def test_unpublished_schema_uri_is_rejected(tmp_path, registry, uri):
    _write(tmp_path, "xk-unknown.schema.json", _schema("xi-kari.v4.unknown", uri=uri))
    registered, errors = registry(tmp_path)
    assert errors
    assert "xi-kari.v4.unknown" not in registered


@pytest.mark.parametrize("mutation", ["unknown_id", "missing_id", "invalid_type"])
def test_published_v4_root_identity_tampering_is_rejected(tmp_path, registry, mutation):
    schema = json.loads((ROOT / "schemas/xk-v4-claim-mechanism.schema.json").read_text("utf-8"))
    if mutation == "unknown_id":
        schema["properties"]["schema_id"]["const"] = "xi-kari.v4.unknown"
    elif mutation == "missing_id":
        schema["properties"].pop("schema_id")
    else:
        schema["type"] = "invalid-type"
    _write(tmp_path, "xk-v4-claim-mechanism.schema.json", schema)
    _, errors = registry(tmp_path)
    assert errors


@pytest.mark.parametrize("reference", [
    "https://xi-kari.local/schemas/xi-kari.v3.absent.schema.json#/$defs/value",
    "#/$defs/absent",
])
def test_missing_reference_is_rejected_without_retrieval(tmp_path, registry, reference):
    schema = _schema("xi-kari.v3.references")
    schema["properties"]["value"] = {"$ref": reference}
    _write(tmp_path, "xk-references.schema.json", schema)
    _, errors = registry(tmp_path)
    assert any("runtime schema reference" in error for error in errors)


def test_published_runtime_schema_checks_are_read_only():
    paths = sorted((ROOT / "schemas").glob("*.json"))
    before = {path: path.read_bytes() for path in paths}
    assert checker._check_runtime_schemas(ROOT) == []
    assert {path: path.read_bytes() for path in paths} == before


def test_missing_published_v4_schema_is_rejected(tmp_path):
    shutil.copytree(ROOT / "schemas", tmp_path / "schemas")
    shutil.copytree(ROOT / "scripts", tmp_path / "scripts")
    (tmp_path / "schemas/xk-v4-common.schema.json").unlink()
    errors = checker._check_runtime_schemas(tmp_path)
    assert any("xk-v4-common" in error or "xi-kari.v4.xk.common" in error for error in errors)


@pytest.mark.parametrize("identifier", ["xi-kari.v3.unknown", "xi-kari.v4.unknown"])
def test_run_artifacts_with_unknown_ids_are_rejected(tmp_path, identifier):
    path = tmp_path / "run-contract.json"
    path.write_text(json.dumps({"schema_id": identifier}), encoding="utf-8")
    original = path.read_bytes()
    errors = checker.check_run(ROOT, tmp_path)
    assert any("schema owner" in error and identifier in error for error in errors)
    assert path.read_bytes() == original


@pytest.mark.parametrize("changes", [
    {"schema_version": 4},
    {"source_version": "v9.0"},
    {"source_version": "v8.2"},
])
def test_active_v3_contract_rejects_version_or_source_mismatch(registry, changes):
    registered, errors = registry(ROOT)
    assert errors == []
    value = {"schema_id": "xi-kari.v3.run-contract", "schema_version": 3, "source_version": "v8.3"}
    value.update(deepcopy(changes))
    fields = {tuple(error.path) for error in registered["xi-kari.v3.run-contract"].iter_errors(value)}
    assert set(changes) <= {field[0] for field in fields if field}
