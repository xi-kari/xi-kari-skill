from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from xi_kari_runtime import validation
from xi_kari_runtime.retrieval import build_full_source_lock


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _disk_bytes(*directories: Path) -> dict[Path, bytes]:
    return {
        path: path.read_bytes()
        for directory in directories
        for path in directory.rglob("*")
        if path.is_file()
    }


def _validate_without_writes(repository: Path, run_dir: Path) -> list[str]:
    before = _disk_bytes(repository / "schemas", run_dir)
    errors: list[str] = []
    validation._validate_path_owned_json(run_dir, repository, errors)
    assert _disk_bytes(repository / "schemas", run_dir) == before
    return errors


def _assert_schema_rejection(errors: list[str]) -> None:
    assert len(errors) == 1
    assert errors[0].startswith("run artifact schema source-lock.json <record>:")


@pytest.fixture(scope="module")
def current_source_lock() -> dict[str, Any]:
    lock, _ = build_full_source_lock(
        ROOT, run_id="schema-disk-boundaries", source_version="v8.3"
    )
    return lock


@pytest.fixture
def disk_artifact(
    tmp_path: Path, current_source_lock: dict[str, Any]
) -> tuple[Path, Path, Path]:
    repository = tmp_path / "repository"
    shutil.copytree(ROOT / "schemas", repository / "schemas")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    artifact = run_dir / "source-lock.json"
    _write_json(artifact, current_source_lock)
    assert _validate_without_writes(repository, run_dir) == []
    return repository, run_dir, artifact


def test_current_v3_source_lock_passes_disk_path_validation(disk_artifact) -> None:
    repository, run_dir, artifact = disk_artifact
    value = json.loads(artifact.read_text(encoding="utf-8"))
    assert value["schema_id"] == "xi-kari.v3.source-lock"
    assert value["schema_version"] == 3
    assert value["framework_version"] == "v8.3"
    assert _validate_without_writes(repository, run_dir) == []


def test_unknown_disk_artifact_schema_id_is_rejected(disk_artifact) -> None:
    repository, run_dir, artifact = disk_artifact
    identifier = "xi-kari.v3.unpublished-source-lock"
    value = json.loads(artifact.read_text(encoding="utf-8"))
    value["schema_id"] = identifier
    _write_json(artifact, value)
    assert _validate_without_writes(repository, run_dir) == [
        "artifact path/schema mismatch: source-lock.json: "
        f"expected xi-kari.v3.source-lock, observed {identifier}",
        f"run artifact has no schema owner: source-lock.json: {identifier}",
    ]


def test_known_disk_schema_is_rejected_at_another_artifact_path(disk_artifact) -> None:
    repository, run_dir, artifact = disk_artifact
    artifact.rename(run_dir / "run-contract.json")
    assert _validate_without_writes(repository, run_dir) == [
        "artifact path/schema mismatch: run-contract.json: "
        "expected xi-kari.v3.run-contract, observed xi-kari.v3.source-lock"
    ]


def test_known_disk_schema_requires_a_declared_path_owner(disk_artifact) -> None:
    repository, run_dir, artifact = disk_artifact
    artifact.rename(run_dir / "unowned-source-lock.json")
    assert _validate_without_writes(repository, run_dir) == [
        "run artifact has no path owner: unowned-source-lock.json"
    ]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("schema_version", 4, id="cross-schema-version"),
        pytest.param("framework_version", "v9.0", id="v90-source-version"),
        pytest.param("framework_version", "v8.2", id="v82-source-version"),
        pytest.param("source_raw_sha256", "a" * 64, id="raw-source-revision"),
        pytest.param("source_semantic_sha256", "b" * 64, id="semantic-source-revision"),
    ],
)
def test_disk_source_lock_rejects_version_or_revision_mismatch(
    disk_artifact, field: str, value: Any
) -> None:
    repository, run_dir, artifact = disk_artifact
    record = json.loads(artifact.read_text(encoding="utf-8"))
    assert record[field] != value
    record[field] = value
    _write_json(artifact, record)
    _assert_schema_rejection(_validate_without_writes(repository, run_dir))


def test_deleted_disk_schema_cannot_validate_its_artifact(disk_artifact) -> None:
    repository, run_dir, _ = disk_artifact
    (repository / "schemas/xk-source.schema.json").unlink()
    errors = _validate_without_writes(repository, run_dir)
    assert "run artifact has no schema owner: source-lock.json: xi-kari.v3.source-lock" in errors


@pytest.mark.parametrize("mutation", ["root_identity", "invalid_schema_type"])
def test_tampered_disk_schema_cannot_validate_its_artifact(
    disk_artifact, mutation: str
) -> None:
    repository, run_dir, _ = disk_artifact
    schema_path = repository / "schemas/xk-source.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if mutation == "root_identity":
        schema["$defs"]["source_lock"]["properties"]["schema_id"]["const"] = (
            "xi-kari.v3.changed-source-lock"
        )
    else:
        schema["type"] = "invalid-type"
    _write_json(schema_path, schema)
    errors = _validate_without_writes(repository, run_dir)
    assert "run artifact has no schema owner: source-lock.json: xi-kari.v3.source-lock" in errors
    if mutation == "invalid_schema_type":
        assert any(error.startswith(f"invalid runtime schema {schema_path}:") for error in errors)
