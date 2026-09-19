#!/usr/bin/env python3
"""Validate the authored v8.3 ontology and deterministic aggregate indexes.

The validator treats inventory shards as the identity authority.  Markdown
cards are deliberately allowed to cover several IDs (for example H1-H6 or
S0-S6), so a card must be bound by path, never by guessing the first ID found
in its prose.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from typing import Any

from build_knowledge_index import run as check_index


ID_RE = re.compile(r"^V83-(?:CANON|CANDIDATE|HEADING|PROVISIONAL|SOURCE)(?:-[A-Z0-9]+)+$")
ANCHOR_RE = re.compile(r"^V83-(?:P\d{4}|T\d{3})$")
MARKDOWN_LINK_RE = re.compile(r"\]\(([^)#]+)(?:#[^)]+)?\)")
DISPOSITIONS = {
    "canonical_concept",
    "structural_rule",
    "subordinate_value",
    "alias",
    "example_only",
    "heading_only",
    "source_undefined",
    "unresolved",
}
SEMANTIC_DISPOSITIONS = {"canonical_concept", "structural_rule"}
CARD_REQUIRED_HEADINGS = (
    "## 原文定义区段",
    "## 解释层（非原文定义）",
    "## 必须联读的邻接概念",
    "## 撤回条件",
)
CANONICAL_FIDELITY_CARD_PATHS = {
    "references/ontology/cards/circles-collectives/s0-s6-prototypes.md",
    "references/ontology/cards/forecast-choice-intervention/choice-authorization.md",
}
CANONICAL_FIDELITY_HEADINGS = (
    "## 禁止跳跃",
    "## 反例与失败条件",
    "## 三阶推演接口",
    "## 来源锚点",
)
LEGACY_FIDELITY_HEADINGS = (
    "## 禁止替换与常见误用",
    "## 案例与失效条件",
    "## 反例与失效条件",
    "## 三阶接口",
    "## 原文锚点",
)
SOURCE_DEFINITION_GAP_RE = re.compile(r"未定义|未给出|未规定|尚未定义|待定义")


def _normalise(value: dict[str, Any], path: Path, root: Path) -> dict[str, Any]:
    """Map both authored shard vocabularies to the validator vocabulary."""

    result = dict(value)
    result.setdefault("concept_id", result.get("id"))
    result.setdefault("name_zh", result.get("canonical_name_zh", result.get("name")))
    result.setdefault("concept_family", result.get("family"))
    result.setdefault("card_path", result.get("card"))
    result.setdefault("source_anchors", result.get("anchors", []))
    result.setdefault("source_undefined_fields", [])
    result.setdefault("required_neighbors", result.get("required_neighbor_ids", []))
    result["_inventory_path"] = path.relative_to(root).as_posix()
    return result


def _load_entries(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    inventory_root = root / "references" / "ontology" / "inventory"
    errors: list[str] = []
    entries: list[dict[str, Any]] = []
    for path in sorted(inventory_root.glob("*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            errors.append(f"cannot read {path}: {exc}")
            continue
        for line_number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{line_number}: invalid JSON: {exc}")
                continue
            if not isinstance(value, dict):
                errors.append(f"{path}:{line_number}: entry is not an object")
                continue
            entries.append(_normalise(value, path, root))
    if not entries:
        errors.append(f"no ontology inventory entries under {inventory_root}")
    return entries, errors


def _schema_errors(root: Path, entries: list[dict[str, Any]]) -> list[str]:
    """Run real JSON Schema validation when the declared dev dependency exists."""

    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:  # pragma: no cover - exercised in minimal hosts
        return [f"jsonschema is required for ontology validation: {exc}"]
    schema_path = root / "schemas" / "concept-inventory.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read {schema_path}: {exc}"]
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    for entry in entries:
        clean = {key: value for key, value in entry.items() if not key.startswith("_")}
        for error in sorted(validator.iter_errors(clean), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in error.path) or "<record>"
            errors.append(f"{entry.get('concept_id')} schema {location}: {error.message}")
    return errors


def _candidate_review_schema_errors(root: Path) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:  # pragma: no cover - exercised in minimal hosts
        return [f"jsonschema is required for ontology validation: {exc}"]
    document_path = root / "references" / "ontology" / "candidate-semantic-scopes.json"
    schema_path = root / "schemas" / "concept-candidate-semantic-scopes.schema.json"
    try:
        document = json.loads(document_path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read exact candidate review contract: {exc}"]
    validator = Draft202012Validator(schema)
    return [
        f"exact candidate reviews schema {'.'.join(str(part) for part in error.path) or '<document>'}: {error.message}"
        for error in sorted(validator.iter_errors(document), key=lambda item: list(item.path))
    ]


def _title_navigation_conflicts(root: Path) -> list[str]:
    """Reject semantic census rows that contradict heading/navigation authority."""

    source_path = root / "references/source/v8.3/indexes/candidates.jsonl"
    census_path = root / "references/ontology/candidate-census.jsonl"
    inventory_root = root / "references/ontology/inventory"
    try:
        source_rows = [
            json.loads(line)
            for line in source_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        census_rows = [
            json.loads(line)
            for line in census_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        inventory_rows = [
            json.loads(line)
            for path in sorted(inventory_root.glob("*.jsonl"))
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read candidate navigation authority: {exc}"]

    census_by_id = {
        str(row.get("candidate_id")): row
        for row in census_rows
        if isinstance(row, dict) and isinstance(row.get("candidate_id"), str)
    }
    heading_anchors: set[str] = set()
    for row in inventory_rows:
        if not isinstance(row, dict) or row.get("disposition") != "heading_only":
            continue
        for anchor in row.get("source_anchors", []) or []:
            if isinstance(anchor, str):
                heading_anchors.add(anchor)

    source_by_id = {
        str(row.get("candidate_id")): row
        for row in source_rows
        if isinstance(row, dict) and isinstance(row.get("candidate_id"), str)
    }

    def owning_table_row(source: dict[str, object]) -> dict[str, object] | None:
        current = source
        visited: set[str] = set()
        while current.get("source_style") == "TableText":
            previous = current.get("previous_candidate_id")
            if not isinstance(previous, str) or previous in visited:
                return None
            visited.add(previous)
            current = source_by_id.get(previous)
            if not isinstance(current, dict):
                return None
        if current.get("source_unit_type") != "table_row":
            return None
        if not isinstance(current.get("source_table_anchor"), str):
            return None
        if not isinstance(current.get("source_table_row_index"), int):
            return None
        return current


    conflicts: list[str] = []
    for source in source_rows:
        if not isinstance(source, dict):
            continue
        candidate_id = source.get("candidate_id")
        census = census_by_id.get(str(candidate_id))
        if not isinstance(census, dict):
            continue
        kinds = {
            str(value)
            for value in source.get("candidate_kinds", []) or []
            if isinstance(value, str)
        }
        title_or_variable = bool(kinds) and kinds <= {"heading", "variable"}
        same_anchor_heading = title_or_variable and any(
            anchor in heading_anchors
            for anchor in source.get("source_anchors", []) or []
            if isinstance(anchor, str)
        )
        owner_heading = False
        if (
            source.get("source_unit_type") == "paragraph"
            and source.get("source_style") == "TableText"
        ):
            owner = owning_table_row(source)
            owner_census = (
                census_by_id.get(str(owner.get("candidate_id")))
                if isinstance(owner, dict)
                else None
            )
            owner_heading = isinstance(owner_census, dict) and owner_census.get(
                "disposition"
            ) == "heading_only"
        navigation_enumeration = (
            source.get("source_unit_type") == "paragraph"
            and source.get("source_style") == "TableText"
            and len(str(source.get("source_text", "")).strip()) <= 100
            and title_or_variable
            and owner_heading
        )
        if census.get("disposition") in SEMANTIC_DISPOSITIONS and (
            same_anchor_heading or navigation_enumeration
        ):
            conflicts.append(
                f"{candidate_id}: semantic disposition contradicts heading/navigation authority"
            )
        if census.get("disposition") == "heading_only" and census.get(
            "disposition_reason"
        ) in {"source_heading_navigation_conflict", "source_navigation_enumeration"}:
            bindings = (
                list(census.get("bound_concept_ids", []) or [])
                + list(census.get("bound_card_paths", []) or [])
                + list(census.get("parent_concept_ids", []) or [])
                + list(census.get("parent_card_paths", []) or [])
            )
            parent_authority = census.get("review_basis", {}).get(
                "parent_authority", {}
            )
            if bindings or parent_authority.get("derived_parent_concept_ids"):
                conflicts.append(
                    f"{candidate_id}: heading_only disposition carries semantic bindings"
                )
    return conflicts


def _markdown_section(text: str, heading: str) -> str | None:
    marker = f"{heading}\n"
    if marker not in text:
        return None
    return text.split(marker, 1)[1].split("\n## ", 1)[0].strip()


def check(root: Path) -> list[str]:
    errors: list[str] = []
    ontology = root / "references" / "ontology"
    inventory_paths = sorted((ontology / "inventory").glob("*.jsonl"))
    if not inventory_paths:
        return [f"missing ontology inventory: {ontology / 'inventory'}"]

    anchor_index_path = root / "references" / "source" / "v8.3" / "indexes" / "anchors.json"
    try:
        anchors = json.loads(anchor_index_path.read_text(encoding="utf-8"))
        known_anchors = set(anchors["paragraphs"]) | set(anchors["tables"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        return [f"cannot read source anchor index: {exc}"]

    entries, load_errors = _load_entries(root)
    errors.extend(load_errors)
    errors.extend(_schema_errors(root, entries))
    errors.extend(_candidate_review_schema_errors(root))
    source_definition_gap_anchors: set[str] = set()
    paragraph_path = root / "references" / "source" / "v8.3" / "audit" / "paragraphs.jsonl"
    try:
        for line_number, line in enumerate(
            paragraph_path.read_text(encoding="utf-8").splitlines(), 1
        ):
            if not line.strip():
                continue
            row = json.loads(line)
            if (
                isinstance(row, dict)
                and isinstance(row.get("anchor"), str)
                and isinstance(row.get("text"), str)
                and SOURCE_DEFINITION_GAP_RE.search(row["text"])
            ):
                source_definition_gap_anchors.add(row["anchor"])
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read source definition gaps: {exc}")
    table_index_path = root / "references" / "source" / "v8.3" / "indexes" / "tables.json"
    try:
        table_rows = json.loads(table_index_path.read_text(encoding="utf-8"))
        for row in table_rows:
            if (
                isinstance(row, dict)
                and isinstance(row.get("anchor"), str)
                and SOURCE_DEFINITION_GAP_RE.search(
                    json.dumps(row.get("rows", []), ensure_ascii=False)
                )
            ):
                source_definition_gap_anchors.add(row["anchor"])
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        errors.append(f"cannot read table definition gaps: {exc}")
    # Collect the complete namespace before checking edges; inventory order is
    # not a topological order and shared cards commonly reference later IDs.
    ids: set[str] = set()
    for entry in entries:
        concept_id = entry.get("concept_id")
        if isinstance(concept_id, str) and ID_RE.fullmatch(concept_id):
            if concept_id in ids:
                errors.append(f"duplicate concept_id: {concept_id}")
            ids.add(concept_id)
    for entry in entries:
        concept_id = entry.get("concept_id")
        disposition = entry.get("disposition")
        if not isinstance(concept_id, str) or not ID_RE.fullmatch(concept_id):
            errors.append(f"invalid concept_id: {concept_id!r}")
            continue
        if disposition not in DISPOSITIONS:
            errors.append(f"{concept_id}: invalid disposition {disposition!r}")
        if disposition in SEMANTIC_DISPOSITIONS and not concept_id.startswith("V83-CANON-"):
            errors.append(
                f"{concept_id}: {disposition} must use a V83-CANON-* identity; "
                "source candidates/headings cannot be promoted"
            )
        if disposition not in SEMANTIC_DISPOSITIONS and concept_id.startswith("V83-CANON-"):
            errors.append(
                f"{concept_id}: non-semantic disposition {disposition} cannot use a "
                "V83-CANON-* identity; use a candidate/heading ID"
            )
        if disposition == "unresolved":
            errors.append(f"{concept_id}: unresolved disposition is forbidden")
        raw_anchors = entry.get("source_anchors", [])
        if not isinstance(raw_anchors, list) or not raw_anchors:
            errors.append(f"{concept_id}: missing source_anchors")
        else:
            for anchor in raw_anchors:
                if not isinstance(anchor, str) or not ANCHOR_RE.fullmatch(anchor):
                    errors.append(f"{concept_id}: malformed source anchor {anchor!r}")
                elif anchor not in known_anchors:
                    errors.append(f"{concept_id}: unknown source anchor {anchor}")
        undefined = entry.get("source_undefined_fields", [])
        if not isinstance(undefined, list):
            errors.append(f"{concept_id}: source_undefined_fields must be a list")
        elif disposition == "source_undefined" and not undefined:
            errors.append(f"{concept_id}: source_undefined requires explicit fields")
        if disposition == "source_undefined" and not (
            set(raw_anchors) & source_definition_gap_anchors
            if isinstance(raw_anchors, list)
            else set()
        ):
            errors.append(
                f"{concept_id}: source_undefined has no explicit source definition gap"
            )

        card_path_value = entry.get("card_path")
        if not isinstance(card_path_value, str) or not card_path_value:
            if disposition in SEMANTIC_DISPOSITIONS:
                errors.append(f"{concept_id}: semantic entry has no card_path")
            continue
        card_path = (root / card_path_value).resolve()
        try:
            card_path.relative_to(root.resolve())
        except ValueError:
            errors.append(f"{concept_id}: card_path escapes repository: {card_path_value}")
            continue
        if not card_path.is_file():
            errors.append(f"{concept_id}: missing card_path {card_path_value!r}")
            continue
        card = card_path.read_text(encoding="utf-8")
        # A shared card is valid even when its prose does not repeat every
        # inventory ID.  The path + source anchors are the binding contract.
        if disposition in SEMANTIC_DISPOSITIONS:
            for heading in CARD_REQUIRED_HEADINGS:
                if heading not in card:
                    errors.append(f"{concept_id}: card has no explicit {heading} section")
            for marker, alternatives in (
                ("## 权威定义", ("## 权威定义",)),
                ("## 反例", ("## 反例", "## 反例与失效条件")),
                ("## 三阶", ("## 三阶",)),
                ("## 来源锚点", ("## 来源锚点", "## 原文锚点")),
                ("source_undefined", ("source_undefined",)),
            ):
                if not any(option in card for option in alternatives):
                    errors.append(f"{concept_id}: card has no required fidelity marker {marker}")
            if not re.search(r"^id:\s+V83-", card, re.MULTILINE):
                errors.append(f"{concept_id}: card has no stable front-matter id")
            covered_match = re.search(r"^covered_ids:\s*(.+)$", card, re.MULTILINE)
            if covered_match and concept_id not in covered_match.group(1):
                errors.append(f"{concept_id}: shared card covered_ids omits the inventory ID")
        for neighbor in entry.get("required_neighbors", []) or []:
            if neighbor not in ids:
                errors.append(f"{concept_id}: dangling neighbor {neighbor}")
        neighbors = entry.get("required_neighbors", []) or []
        if len(neighbors) > 16:
            errors.append(f"{concept_id}: too many required neighbors ({len(neighbors)}; max 16)")
        if disposition in SEMANTIC_DISPOSITIONS and not neighbors:
            errors.append(f"{concept_id}: semantic entry needs at least one bounded neighbor")

    by_id = {str(entry.get("concept_id")): entry for entry in entries}
    human_contract = "V83-CANON-CORE-HUMAN-EMPIRICAL-INSTANCE-CONTRACT"
    required_edges = {
        human_contract: {
            "V83-CANON-CORE-ROOT-INSTANCE-CONTRACT",
            "V83-CANON-CORE-EVIDENCE-CONTRACT",
            "V83-CANON-H1",
            "V83-CANON-H4",
            "V83-CANON-H5",
        },
        "V83-CANON-CORE-ROOT-INSTANCE-CONTRACT": {human_contract},
        "V83-CANON-H1": {human_contract},
        "V83-CANON-H4": {human_contract},
        "V83-CANON-H5": {human_contract},
    }
    for concept_id, required in required_edges.items():
        entry = by_id.get(concept_id)
        if entry is None:
            errors.append(f"missing core-human closure concept: {concept_id}")
            continue
        missing = required - set(entry.get("required_neighbors", []) or [])
        if missing:
            errors.append(
                f"{concept_id}: missing core-human closure neighbors {sorted(missing)}"
            )
    contract_entry = by_id.get(human_contract)
    if contract_entry is not None and "V83-P0628" not in set(
        contract_entry.get("source_anchors", []) or []
    ):
        errors.append(f"{human_contract}: missing formal V83-P0628 anchor")

    bundle_path = ontology / "bundles" / "core-human-empirical-instance.md"
    if not bundle_path.is_file():
        errors.append(f"missing core-human continuity bundle: {bundle_path}")
    else:
        bundle_text = bundle_path.read_text(encoding="utf-8")
        for concept_id in required_edges:
            if concept_id not in bundle_text:
                errors.append(f"core-human continuity bundle omits {concept_id}")

    for card_path in sorted((ontology / "cards").glob("**/*.md")):
        text = card_path.read_text(encoding="utf-8")
        relative = card_path.relative_to(root).as_posix()
        if "V8-CANON-" in text:
            errors.append(f"legacy ProMax v8 ID appears in {card_path}")
        if relative in CANONICAL_FIDELITY_CARD_PATHS:
            for heading in CANONICAL_FIDELITY_HEADINGS:
                body = _markdown_section(text, heading)
                if body is None:
                    errors.append(
                        f"{relative}: missing canonical fidelity section {heading}"
                    )
                elif not body or "本节与" in body or "保留旧卡片索引名称" in body:
                    errors.append(
                        f"{relative}: canonical fidelity section {heading} is alias-only"
                    )
            for heading in LEGACY_FIDELITY_HEADINGS:
                if re.search(rf"^{re.escape(heading)}$", text, re.MULTILINE):
                    errors.append(f"{relative}: legacy fidelity heading remains: {heading}")
        for target in MARKDOWN_LINK_RE.findall(text):
            if target.startswith(("http://", "https://", "#")):
                continue
            resolved = (card_path.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(f"card link escapes repository: {card_path} -> {target}")
                continue
            if not resolved.is_file():
                errors.append(f"broken card link: {card_path} -> {target}")

    errors.extend(_title_navigation_conflicts(root))
    bundles = sorted((ontology / "bundles").glob("*.md"))
    if len(bundles) < 10:
        errors.append(f"too few continuity bundles: {len(bundles)}")
    for bundle in bundles:
        text = bundle.read_text(encoding="utf-8")
        if "V83-P" not in text and "V83-T" not in text:
            errors.append(f"bundle has no v8.3 source anchor: {bundle}")
    bundle_registry_path = ontology / "continuity-bundle-registry.json"
    try:
        bundle_registry = json.loads(
            bundle_registry_path.read_text(encoding="utf-8")
        )
        registered = bundle_registry["bundles"]
    except Exception as exc:
        errors.append(f"invalid continuity bundle registry: {exc}")
        registered = {}
    expected_bundle_paths = {
        bundle.relative_to(root).as_posix() for bundle in bundles
    }
    if set(registered) != expected_bundle_paths:
        errors.append("continuity bundle registry paths differ from authored bundles")
    for bundle in bundles:
        relative = bundle.relative_to(root).as_posix()
        entry = registered.get(relative)
        if not isinstance(entry, dict):
            continue
        if entry.get("sha256") != sha256(bundle.read_bytes()).hexdigest():
            errors.append(f"continuity bundle registry hash mismatch: {relative}")
        if entry.get("route_kind") != "curated_semantic_closure":
            errors.append(f"continuity bundle registry route is invalid: {relative}")

    errors.extend(check_index(root, check=True))
    return list(dict.fromkeys(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    errors = check(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("ontology: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
