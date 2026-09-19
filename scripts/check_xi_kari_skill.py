#!/usr/bin/env python3
"""Repository-wide structural contract checker."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from check_ontology import check as check_ontology
from check_source_snapshot import check_coverage
from build_source_snapshot import build as check_source


LINK_RE = re.compile(r"\]\(([^)#]+)(?:#[^)]+)?\)")
FORBIDDEN_EVAL_KEYS = {
    "answer",
    "expected_answer",
    "gold_answer",
    "reference_answer",
    "ideal_response",
}
FORBIDDEN_RUNTIME_PATHS = {
    "recovery",
    "runs",
    "pending-action.json",
    "release-manifest.json",
    "PhaseStore",
    "writer lease",
    "heartbeat",
    "host handshake",
}


def _validate_json_schemas(root: Path) -> list[str]:
    """Check schema syntax and validate the generated registry artifact."""

    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:  # pragma: no cover - minimal host diagnostic
        return [f"jsonschema is required for schema checks: {exc}"]
    errors: list[str] = []
    schemas: dict[str, dict] = {}
    for schema_path in sorted((root / "schemas").glob("*.json")):
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            schemas[schema_path.name] = schema
        except Exception as exc:
            # `check_schema` raises several jsonschema-specific exception
            # classes; keeping the message at the file boundary is enough for
            # a deterministic maintenance failure.
            errors.append(f"invalid schema {schema_path}: {exc}")
    registry_path = root / "references" / "ontology" / "concept-registry.json"
    registry_schema = schemas.get("concept-registry.schema.json")
    if registry_schema and registry_path.is_file():
        validator = Draft202012Validator(registry_schema)
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            for error in validator.iter_errors(registry):
                location = ".".join(str(part) for part in error.path) or "<registry>"
                errors.append(f"registry schema {location}: {error.message}")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"cannot read generated registry: {exc}")
    elif registry_schema:
        errors.append(f"missing generated registry: {registry_path}")
    for artifact_name, schema_name in (
        ("concept-relations.json", "concept-relations.schema.json"),
        ("source-to-concept-map.json", "source-to-concept-map.schema.json"),
    ):
        artifact_path = root / "references" / "ontology" / artifact_name
        artifact_schema = schemas.get(schema_name)
        if not artifact_schema:
            continue
        if not artifact_path.is_file():
            errors.append(f"missing generated ontology artifact: {artifact_path}")
            continue
        try:
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            for error in Draft202012Validator(artifact_schema).iter_errors(artifact):
                location = ".".join(str(part) for part in error.path) or f"<{artifact_name}>"
                errors.append(f"{artifact_name} schema {location}: {error.message}")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"cannot read generated {artifact_name}: {exc}")
    manifest_path = root / "references" / "source" / "v8.3" / "source-manifest.json"
    manifest_schema = schemas.get("source-manifest.schema.json")
    if manifest_schema and manifest_path.is_file():
        validator = Draft202012Validator(manifest_schema)
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for error in validator.iter_errors(manifest):
                location = ".".join(str(part) for part in error.path) or "<manifest>"
                errors.append(f"manifest schema {location}: {error.message}")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"cannot read source manifest: {exc}")
    return errors


def _check_markdown_links(root: Path) -> list[str]:
    errors: list[str] = []
    search_roots = [root / "references", root / "protocols", root / "templates"]
    for search_root in search_roots:
        for path in sorted(search_root.glob("**/*.md")):
            # The lossless reader is source data; its HTML/comments are
            # checked by the source snapshot validator, not this route pass.
            if "references/source/v8.3/reader" in path.relative_to(root).as_posix():
                continue
            text = path.read_text(encoding="utf-8")
            for target in LINK_RE.findall(text):
                if target.startswith(("http://", "https://", "#")):
                    continue
                resolved = (path.parent / target).resolve()
                try:
                    resolved.relative_to(root.resolve())
                except ValueError:
                    errors.append(f"markdown link escapes repository: {path} -> {target}")
                    continue
                if not resolved.is_file():
                    errors.append(f"broken markdown link: {path} -> {target}")
    return errors


def check(root: Path, *, all_checks: bool) -> list[str]:
    errors: list[str] = []
    entry = root / "SKILL.md"
    if not entry.is_file():
        return [f"missing entry: {entry}"]
    text = entry.read_text(encoding="utf-8")
    if len(text.splitlines()) > 500:
        errors.append("SKILL.md exceeds 500 lines")
    for required in ("xi-kari-skill", "21 卷", "完整读取", "主动检索", "一至三阶", "不得被动触发"):
        if required not in text:
            errors.append(f"SKILL.md missing contract phrase: {required}")
    for link in LINK_RE.findall(text):
        if link.startswith(("http://", "https://", "#")):
            continue
        target = (root / link).resolve()
        if not target.is_file():
            errors.append(f"broken SKILL link: {link}")
    errors.extend(_validate_json_schemas(root))
    if not (root / "agents" / "openai.yaml").is_file():
        errors.append("missing agents/openai.yaml")
    errors.extend(_check_markdown_links(root))
    runtime_files = list((root / "protocols").glob("*.md")) + [entry]
    for path in runtime_files:
        lower = path.read_text(encoding="utf-8").lower()
        if "crossframe-ultra" in lower and path.name != "SKILL.md":
            errors.append(f"runtime file names Ultra as an executable dependency: {path}")
        # A runtime contract may explain that a control plane is forbidden, but
        # it must not require or invoke one.  Detect concrete path/API forms,
        # while allowing the explicit negative wording in SKILL.md.
        for token in FORBIDDEN_RUNTIME_PATHS:
            token_lower = token.lower()
            if token_lower in {"phaseStore".lower(), "writer lease", "heartbeat", "host handshake"}:
                if re.search(rf"(?:use|call|create|require|invoke|depends on|through)\s+[^.\n]*{re.escape(token_lower)}", lower):
                    errors.append(f"runtime protocol invokes forbidden control plane {token}: {path}")
            elif token_lower in lower and token_lower.endswith(".json"):
                if re.search(rf"(?:/|\\|`){re.escape(token_lower)}", lower):
                    errors.append(f"runtime protocol contains forbidden control path {token}: {path}")
    # Old shallow route validators and duplicate runtime reference surfaces are
    # not part of v1.0; keeping them would create a second, competing reader.
    for stale in (
        root / "scripts" / "validate_routes.py",
        root / "scripts" / "validate_source_coverage.py",
        root / "references" / "question-routing-map.md",
    ):
        if stale.exists():
            errors.append(f"stale pre-v1 surface remains: {stale}")
    if all_checks:
        errors.extend(check_source(root, check=True))
        errors.extend(check_coverage(root))
        if (root / "references" / "ontology" / "inventory").is_dir():
            errors.extend(check_ontology(root))
    return list(dict.fromkeys(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    errors = check(args.root.resolve(), all_checks=args.all)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("xi-kari skill: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
