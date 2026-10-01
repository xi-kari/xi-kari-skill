"""Repository-owned semantic authority bindings for one Xi-Kari run."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .canonical_json import sha256_file, sha256_json


def _reject_symlink_components(path: Path, *, boundary: Path | None = None) -> None:
    candidate = Path(path).expanduser().absolute()
    if boundary is None:
        current = Path(candidate.anchor)
        parts = candidate.parts[1:]
    else:
        current = Path(boundary).expanduser().absolute()
        parts = candidate.relative_to(current).parts
    if current.is_symlink():
        raise ValueError(f"repository authority path contains a symlink: {current}")
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"repository authority path contains a symlink: {current}")


def repository_root(path: Path) -> Path:
    candidate = Path(path).expanduser()
    _reject_symlink_components(candidate)
    resolved = candidate.resolve()
    if not resolved.is_dir():
        raise ValueError(f"repository root does not exist: {resolved}")
    return resolved


def _required_glob(
    root: Path, pattern: str, label: str, *, require_complete: bool
) -> tuple[Path, ...]:
    paths = tuple(sorted(root.glob(pattern)))
    if require_complete and not paths:
        raise ValueError(f"repository authority is missing {label}")
    return paths


def authority_paths(root: Path, *, require_complete: bool = True, source_version: str = "v8.3") -> tuple[Path, ...]:
    from .source_profile import get_source_profile

    root = repository_root(root)
    profile = get_source_profile(source_version)
    ontology = root / "references" / "ontology"
    learning = "references/learning-packs"
    if source_version == "v9.0":
        ontology = ontology / source_version
        learning += "/" + source_version
    source = profile.source_directory(root)
    ontology_relative = ontology.relative_to(root).as_posix()
    paths: list[Path] = [
        root / "SKILL.md",
        root / "scripts" / "xi_kari_runtime.py",
        root / "scripts" / "xi_kari_codex_authoring_adapter.py",
        root / "scripts" / "check_xi_kari_runtime.py",
        root / "scripts" / "check_authoring_output.py",
        root / "references" / "answer-contract.md",
        root / "references" / "retrieval-policy.md",
        root / "references" / "runtime-read-map.md",
        root / "references" / "source-quality-policy.md",
        ontology / "candidate-census.jsonl",
        ontology / "candidate-semantic-scopes.json",
        ontology / "concept-disposition-ledger.jsonl",
        ontology / "concept-family-map.md",
        ontology / "concept-registry.json",
        ontology / "concept-relations.json",
        ontology / "continuity-bundle-registry.json",
        ontology / "continuity-map.md",
        ontology / "source-to-concept-map.json",
        source / "source-manifest.json",
        source / "indexes" / "anchors.json",
        source / "indexes" / "candidates.jsonl",
        source / "indexes" / "tables.json",
        source / "audit" / "paragraphs.jsonl",
    ]
    paths.extend(
        _required_glob(
            root,
            "protocols/*.md",
            "runtime protocols",
            require_complete=require_complete,
        )
    )
    paths.extend(
        _required_glob(
            root,
            "scripts/xi_kari_runtime/*.py",
            "runtime modules",
            require_complete=require_complete,
        )
    )
    paths.extend(
        _required_glob(
            root,
            "schemas/xk-*.json",
            "runtime schemas",
            require_complete=require_complete,
        )
    )
    paths.extend(
        _required_glob(
            root,
            "templates/*.md",
            "output templates",
            require_complete=require_complete,
        )
    )
    paths.extend(
        _required_glob(
            root,
            learning + "/*.md",
            "learning packs",
            require_complete=require_complete,
        )
    )
    paths.extend(
        _required_glob(
            root,
            (ontology_relative + "/authored/*.json*" if source_version == "v9.0" else ontology_relative + "/inventory/*.jsonl"),
            "ontology inventory",
            require_complete=require_complete,
        )
    )
    paths.extend(
        _required_glob(
            root,
            ontology_relative + "/cards/**/*.md",
            "ontology concept cards",
            require_complete=require_complete,
        )
    )
    paths.extend(
        _required_glob(
            root,
            ontology_relative + "/bundles/*.md",
            "ontology continuity bundles",
            require_complete=require_complete,
        )
    )
    paths.extend(
        _required_glob(
            root,
            profile.snapshot_directory + "/reader/*.md",
            "source reader volumes",
            require_complete=require_complete,
        )
    )
    paths.extend(
        _required_glob(
            root,
            profile.snapshot_directory + "/audit/tables/" + profile.anchor_prefix + ("-T*.json" if source_version == "v9.0" else "-T*.md"),
            "source tables",
            require_complete=require_complete,
        )
    )
    unique = tuple(sorted(set(paths)))
    for path in unique:
        _reject_symlink_components(path, boundary=root)
        if require_complete and not path.is_file():
            relative = path.relative_to(root)
            label = "ontology" if "ontology" in relative.parts else "authority input"
            raise ValueError(f"repository authority is missing {label}: {relative}")
    return tuple(path for path in unique if path.is_file())


def authority_bindings(
    root: Path, *, require_complete: bool = True
) -> tuple[dict[str, str], ...]:
    root = repository_root(root)
    return tuple(
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in authority_paths(root, require_complete=require_complete)
    )


def validator_set_sha256(root: Path, *, require_complete: bool = True) -> str:
    return sha256_json(
        authority_bindings(root, require_complete=require_complete)
    )


__all__ = (
    "authority_bindings",
    "authority_paths",
    "repository_root",
    "validator_set_sha256",
)
