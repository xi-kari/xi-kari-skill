"""Validate the versioned Xi-Kari v9.0 ontology and its consumers."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from build_knowledge_index import run as build_knowledge_index
from xi_kari_runtime.canonical_json import sha256_bytes
from xi_kari_runtime.concept_authority import load_concept_authority
from xi_kari_runtime.ontology_read_trace import (
    build_ontology_read_plan,
    read_ontology_item_bytes,
)


TERMINAL_DISPOSITIONS = {"canonical", "alias", "subordinate_value", "out_of_scope"}
DEPENDENCY_ROLES = {
    "inferential_requires",
    "protocol_requires",
    "specializes",
    "applies_to",
    "input_dependencies",
}
SOURCE_RAW_SHA256 = "ffc45afdc288ecd268fd02e46d47318b7ddf17bf7b47605aa6c413c95398544b"


def _load_json(path: Path, label: str) -> tuple[object | None, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"cannot read {label}: {exc}"]


def _load_jsonl(path: Path, label: str) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [f"cannot read {label}: {exc}"]
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{label}:{line_number}: invalid JSON: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"{label}:{line_number}: row is not an object")
            continue
        rows.append(value)
    return rows, errors


def check(root: Path) -> list[str]:
    root = Path(root).resolve()
    errors = build_knowledge_index(root, check=True, source_version="v9.0")
    source_root = root / "references" / "source" / "v9.0"
    ontology_root = root / "references" / "ontology" / "v9.0"
    source_rows, load_errors = _load_jsonl(
        source_root / "indexes" / "candidates.jsonl", "v9.0 source candidates"
    )
    errors.extend(load_errors)
    census_rows, load_errors = _load_jsonl(
        ontology_root / "candidate-census.jsonl", "v9.0 candidate census"
    )
    errors.extend(load_errors)
    ledger_rows, load_errors = _load_jsonl(
        ontology_root / "concept-disposition-ledger.jsonl", "v9.0 disposition ledger"
    )
    errors.extend(load_errors)
    registry, load_errors = _load_json(
        ontology_root / "concept-registry.json", "v9.0 concept registry"
    )
    errors.extend(load_errors)
    graph, load_errors = _load_json(
        ontology_root / "dependency-graph.json", "v9.0 dependency graph"
    )
    errors.extend(load_errors)
    domains, load_errors = _load_json(
        root / "references" / "domains" / "index.json", "v9.0 domain index"
    )
    errors.extend(load_errors)
    knowledge, load_errors = _load_json(
        ontology_root / "knowledge-index.json", "v9.0 knowledge index"
    )
    errors.extend(load_errors)
    migration, load_errors = _load_json(
        ontology_root / "concept-migration-map.json", "v9.0 concept migration map"
    )
    errors.extend(load_errors)
    source_undefined, load_errors = _load_json(
        ontology_root / "source-undefined-and-conflicts.json",
        "v9.0 source undefined register",
    )
    errors.extend(load_errors)
    source_manifest, load_errors = _load_json(
        source_root / "source-manifest.json", "v9.0 source manifest"
    )
    errors.extend(load_errors)
    if not all(
        isinstance(value, dict)
        for value in (
            registry,
            graph,
            domains,
            knowledge,
            source_manifest,
            migration,
            source_undefined,
        )
    ):
        return list(dict.fromkeys(errors))
    expected_candidate_count = source_manifest.get("candidate_count")
    if not isinstance(expected_candidate_count, int):
        errors.append("v9.0 source manifest candidate count is invalid")
        expected_candidate_count = len(source_rows)
    preserved = migration.get("preserved_identities")
    forbidden_merges = migration.get("forbidden_merges")
    if not isinstance(preserved, list) or len(preserved) != 93:
        errors.append("v9.0 migration map does not preserve the accepted 93 identities")
    if migration.get("new_official_roots") != [] or migration.get(
        "new_official_scale_operators"
    ) != []:
        errors.append("v9.0 migration map invents a root or scale operator")
    if not isinstance(forbidden_merges, list) or not {
        "U01-U11 with HV01-HV11",
        "ordinary learning with CM-LEARNING",
        "all externalities with C7",
        "X0 with S7",
    }.issubset(set(forbidden_merges)):
        errors.append("v9.0 migration map omits a forbidden identity merge")
    correction = source_undefined.get("forbidden_inference_correction")
    if not isinstance(correction, dict) or correction.get("disposition") != (
        "forbidden_inference_not_open_parameter"
    ):
        errors.append("ordinary learning was not removed from source_undefined")

    schema_targets = (
        (
            root / "schemas" / "identity-register-v90.schema.json",
            ontology_root / "authored" / "identity-register.json",
            "json",
        ),
        (
            root / "schemas" / "identity-register-v90.schema.json",
            ontology_root / "authored" / "extended-identities.json",
            "json",
        ),
        (
            root / "schemas" / "candidate-decision-v90.schema.json",
            ontology_root / "authored" / "candidate-decisions.jsonl",
            "jsonl",
        ),
        (
            root / "schemas" / "dependency-graph-v90.schema.json",
            ontology_root / "dependency-graph.json",
            "json",
        ),
        (
            root / "schemas" / "domain-index-v90.schema.json",
            root / "references" / "domains" / "index.json",
            "json",
        ),
        (
            root / "schemas" / "concept-registry-v90.schema.json",
            ontology_root / "concept-registry.json",
            "json",
        ),
    )
    for schema_path, value_path, kind in schema_targets:
        schema, schema_errors = _load_json(schema_path, f"schema {schema_path.name}")
        errors.extend(schema_errors)
        if not isinstance(schema, dict):
            continue
        validator = Draft202012Validator(schema)
        values: list[object]
        if kind == "jsonl":
            values, value_errors = _load_jsonl(value_path, value_path.name)
            errors.extend(value_errors)
        else:
            value, value_errors = _load_json(value_path, value_path.name)
            errors.extend(value_errors)
            values = [value]
        for index, value in enumerate(values, 1):
            for schema_error in sorted(
                validator.iter_errors(value), key=lambda item: list(item.path)
            ):
                location = ".".join(str(part) for part in schema_error.path) or "<root>"
                errors.append(
                    f"{value_path.name}:{index} schema {location}: {schema_error.message}"
                )

    if len(source_rows) != expected_candidate_count or len(census_rows) != len(source_rows):
        errors.append("v9.0 candidate census is not the complete current source closure")
    if len(ledger_rows) != len(census_rows):
        errors.append("v9.0 disposition ledger count differs from the candidate census")
    if [row.get("candidate_id") for row in source_rows] != [
        row.get("candidate_id") for row in census_rows
    ]:
        errors.append("v9.0 candidate census order differs from source authority")
    for source, census in zip(source_rows, census_rows, strict=False):
        candidate_id = source.get("candidate_id")
        for field in (
            "candidate_id",
            "source_anchors",
            "source_span",
            "text_sha256",
            "semantic_fingerprint_sha256",
            "source_raw_sha256",
        ):
            if census.get(field) != source.get(field):
                errors.append(
                    f"{candidate_id}: candidate census differs from source field {field}"
                )
        if census.get("disposition") not in TERMINAL_DISPOSITIONS:
            errors.append(f"{candidate_id}: candidate disposition is not terminal")
        if census.get("disposition_status") != "final":
            errors.append(f"{candidate_id}: candidate disposition is not final")

    concepts = registry.get("concepts")
    if (
        registry.get("framework_version") != "v9.0"
        or registry.get("source_raw_sha256") != SOURCE_RAW_SHA256
        or registry.get("unresolved_candidate_count") != 0
        or not isinstance(concepts, list)
        or registry.get("concept_count") != len(concepts)
        or len(concepts) != knowledge.get("identity_count")
        or knowledge.get("preserved_identity_count") != 93
    ):
        errors.append("v9.0 concept registry identity or count is invalid")
        concepts = [] if not isinstance(concepts, list) else concepts
    concept_ids: set[str] = set()
    for concept in concepts:
        if not isinstance(concept, dict):
            errors.append("v9.0 concept registry contains a non-object")
            continue
        concept_id = concept.get("concept_id")
        card_path = concept.get("card_path")
        if not isinstance(concept_id, str) or concept_id in concept_ids:
            errors.append(f"v9.0 concept identity is invalid or duplicated: {concept_id}")
            continue
        concept_ids.add(concept_id)
        if not isinstance(card_path, str):
            errors.append(f"{concept_id}: concept card path is missing")
            continue
        card = root / card_path
        if card.is_symlink() or not card.is_file():
            errors.append(f"{concept_id}: concept card is missing or unsafe")
            continue
        text = card.read_text(encoding="utf-8")
        for heading in ("## 原文层", "## 解释层", "## 依赖角色", "## source_undefined"):
            if heading not in text:
                errors.append(f"{concept_id}: card lacks separated section {heading}")
        expected_hash = concept.get("hashes", {}).get("card_sha256")
        if expected_hash != sha256(card.read_bytes()).hexdigest():
            errors.append(f"{concept_id}: concept card hash differs")

    edges = graph.get("edges")
    hard_edges = graph.get("hard_inference_edges")
    if not isinstance(edges, list) or not isinstance(hard_edges, list):
        errors.append("v9.0 dependency graph edge lists are invalid")
    else:
        if any(
            not isinstance(edge, dict) or edge.get("role") not in DEPENDENCY_ROLES
            for edge in edges
        ):
            errors.append("v9.0 dependency graph contains an invalid role")
        expected_hard = [
            edge for edge in edges if edge.get("role") == "inferential_requires"
        ]
        if hard_edges != expected_hard:
            errors.append("v9.0 hard DAG contains non-inferential or missing edges")

    domain_entries = domains.get("entries")
    expected_domains = [f"D.{ordinal:02d}" for ordinal in range(1, 33)]
    if not isinstance(domain_entries, list) or [
        entry.get("domain_id") for entry in domain_entries if isinstance(entry, dict)
    ] != expected_domains:
        errors.append("v9.0 domain identity index is incomplete or out of order")
        domain_entries = [] if not isinstance(domain_entries, list) else domain_entries
    for entry in domain_entries:
        if not isinstance(entry, dict):
            continue
        domain_id = entry.get("domain_id")
        if entry.get("content_status") == "identity_only":
            if (
                entry.get("content_path") is not None
                or entry.get("content_sha256") is not None
                or entry.get("read_trace_status") != "not_yet_available"
            ):
                errors.append(f"{domain_id}: domain identity claims unavailable content or reading")
            continue
        if entry.get("content_status") != "available":
            errors.append(f"{domain_id}: unsupported domain content status")
            continue
        expected_path = f"references/learning-packs/domains/{domain_id}.md"
        if entry.get("content_path") != expected_path:
            errors.append(f"{domain_id}: domain content path does not match its identity")
        if entry.get("read_trace_status") != "requires_run_trace":
            errors.append(f"{domain_id}: available content still requires a run-owned read trace")
        if domains.get("source_raw_sha256") != source_manifest.get("raw_sha256"):
            errors.append(f"{domain_id}: domain source identity differs from current source")
        content_path = root / expected_path
        try:
            content_path.resolve(strict=True).relative_to(root)
            content = content_path.read_bytes()
        except (OSError, ValueError):
            errors.append(f"{domain_id}: domain content is missing or outside the repository")
            continue
        if entry.get("content_sha256") != sha256(content).hexdigest():
            errors.append(
                f"{domain_id}: domain content hash differs from the current bytes"
            )

    assets = knowledge.get("assets")
    if not isinstance(assets, list):
        errors.append("v9.0 knowledge index has no asset manifest")
    else:
        for asset in assets:
            if not isinstance(asset, dict) or not isinstance(asset.get("path"), str):
                errors.append("v9.0 knowledge asset record is invalid")
                continue
            path = root / asset["path"]
            if path.is_symlink() or not path.is_file():
                errors.append(f"v9.0 knowledge asset is missing or unsafe: {asset['path']}")
                continue
            payload = path.read_bytes()
            if asset.get("bytes") != len(payload) or asset.get("sha256") != sha256(
                payload
            ).hexdigest():
                errors.append(f"v9.0 knowledge asset hash differs: {asset['path']}")

    authored_text = (
        ontology_root / "authored" / "identity-register.json"
    ).read_text(encoding="utf-8")
    if '"source_undefined":["ordinary learning automatic G status"' in authored_text:
        errors.append("forbidden ordinary-learning inference remains source_undefined")

    try:
        census, binding = load_concept_authority(root, source_version="v9.0")
        plan = build_ontology_read_plan(
            root,
            source_version="v9.0",
            run_id="ontology-v90-check",
            problem_contract_sha256="1" * 64,
            content_access_challenge="2" * 64,
        )
        if (
            len(census) != expected_candidate_count
            or binding.get("framework_version") != "v9.0"
        ):
            errors.append("v9.0 concept authority consumer binding is incomplete")
        records = plan.get("records")
        if not isinstance(records, list) or plan.get("record_count") != len(records):
            errors.append("v9.0 ontology read plan is incomplete")
        else:
            for record in records:
                content = read_ontology_item_bytes(root, record)
                if record.get("content_sha256") != sha256_bytes(content):
                    errors.append(
                        f"v9.0 ontology read plan content hash differs: {record.get('item_id')}"
                    )
    except (OSError, TypeError, ValueError) as exc:
        errors.append(f"v9.0 ontology consumer validation failed: {exc}")
    return list(dict.fromkeys(errors))
