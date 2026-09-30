"""Build the versioned Xi-Kari v9.0 ontology and knowledge assets."""

from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping


SOURCE_RAW_SHA256 = "ffc45afdc288ecd268fd02e46d47318b7ddf17bf7b47605aa6c413c95398544b"
TERMINAL_DISPOSITIONS = frozenset(
    {"canonical", "alias", "subordinate_value", "out_of_scope"}
)
OUT_OF_SCOPE_KINDS = frozenset(
    {
        "navigation",
        "editorial",
        "bibliographic",
        "historical_only",
        "duplicate_source_unit",
    }
)
DEPENDENCY_ROLES = frozenset(
    {
        "inferential_requires",
        "protocol_requires",
        "specializes",
        "applies_to",
        "input_dependencies",
    }
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _pretty(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _jsonl(values: list[dict[str, object]]) -> bytes:
    return b"".join(_canonical(value) for value in values)


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


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "identity"


def _source_id_map(identities: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(identity["source_concept_id"]): str(identity["concept_id"])
        for identity in identities
    }


def _external_gate_id(source_id: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", source_id).strip("-").upper()
    return f"V90-EXTERNAL-GATE-{slug or 'UNNAMED'}"


def _validate_identity_register(
    root: Path,
    register: Mapping[str, Any],
    candidates: Mapping[str, Mapping[str, Any]],
    paragraphs: Mapping[str, Mapping[str, Any]],
    *,
    expected_count: int | None = 93,
) -> list[str]:
    errors: list[str] = []
    if register.get("framework_version") != "v9.0":
        errors.append("v9.0 identity register framework version differs")
    if register.get("source_raw_sha256") != SOURCE_RAW_SHA256:
        errors.append("v9.0 identity register source hash differs")
    identities = register.get("identities")
    if not isinstance(identities, list):
        return [*errors, "v9.0 identity register has no identities"]
    if register.get("identity_count") != len(identities):
        errors.append("v9.0 identity register count differs from its identities")
    if expected_count is not None and len(identities) != expected_count:
        errors.append(
            f"v9.0 preserved identity register must contain exactly {expected_count} accepted identities"
        )
    concept_ids: set[str] = set()
    source_ids: set[str] = set()
    card_paths: set[str] = set()
    for identity in identities:
        if not isinstance(identity, dict):
            errors.append("v9.0 identity record is not an object")
            continue
        concept_id = identity.get("concept_id")
        source_id = identity.get("source_concept_id")
        card_path = identity.get("card_path")
        if not isinstance(concept_id, str) or not concept_id.startswith("V90-CANON-"):
            errors.append(f"invalid v9.0 concept identity: {concept_id!r}")
            continue
        if concept_id in concept_ids:
            errors.append(f"duplicate v9.0 concept identity: {concept_id}")
        concept_ids.add(concept_id)
        if not isinstance(source_id, str) or not source_id:
            errors.append(f"{concept_id}: missing source concept identity")
        elif source_id in source_ids:
            errors.append(f"duplicate source concept identity: {source_id}")
        else:
            source_ids.add(source_id)
        if not isinstance(card_path, str) or not card_path.startswith(
            "references/ontology/v9.0/cards/"
        ):
            errors.append(f"{concept_id}: invalid card path")
        elif card_path in card_paths:
            errors.append(f"duplicate v9.0 card path: {card_path}")
        else:
            card_paths.add(card_path)
        primary = identity.get("primary_candidate_id")
        candidate_ids = identity.get("candidate_ids")
        if (
            not isinstance(candidate_ids, list)
            or any(value not in candidates for value in candidate_ids)
        ):
            errors.append(f"{concept_id}: candidate binding is incomplete")
        elif isinstance(primary, str):
            if primary not in candidate_ids or primary not in candidates:
                errors.append(f"{concept_id}: primary candidate binding is invalid")
        elif primary is None:
            definition_units = identity.get("definition_source_units")
            if not isinstance(definition_units, list) or not definition_units or any(
                value not in paragraphs for value in definition_units
            ):
                errors.append(
                    f"{concept_id}: non-candidate definition identity has no exact source units"
                )
        else:
            errors.append(f"{concept_id}: primary candidate identity is invalid")
        source_layer = identity.get("source_layer")
        interpretation = identity.get("interpretation_layer")
        if not isinstance(source_layer, dict) or not isinstance(interpretation, dict):
            errors.append(f"{concept_id}: source and interpretation layers are not separate")
            continue
        anchors = source_layer.get("source_anchors")
        refs = source_layer.get("source_refs")
        if not isinstance(anchors, list) or not anchors or not isinstance(refs, list):
            errors.append(f"{concept_id}: source layer has no exact source references")
            continue
        flattened = [
            anchor
            for ref in refs
            if isinstance(ref, dict)
            for anchor in ref.get("paragraph_anchors", [])
            if isinstance(anchor, str)
        ]
        if anchors != flattened or len(anchors) != len(set(anchors)):
            errors.append(f"{concept_id}: source layer anchors are not exact and unique")
        exact_paragraph_texts: list[str] = []
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            text = ref.get("text")
            text_hash = ref.get("text_sha256")
            if not isinstance(text, str) or sha256(text.encode("utf-8")).hexdigest() != text_hash:
                errors.append(f"{concept_id}: source text hash differs")
            for anchor in ref.get("paragraph_anchors", []):
                paragraph = paragraphs.get(anchor)
                if paragraph is None:
                    errors.append(f"{concept_id}: source anchor does not resolve: {anchor}")
                else:
                    exact_paragraph_texts.append(str(paragraph.get("text", "")))
        if source_layer.get("source_text_sha256") != sha256(
            _canonical(exact_paragraph_texts)
        ).hexdigest():
            errors.append(f"{concept_id}: source layer aggregate hash differs")
        if not interpretation.get("positive_boundary") or not interpretation.get(
            "negative_boundary"
        ):
            errors.append(f"{concept_id}: interpretation boundaries are incomplete")
        source_undefined = identity.get("source_undefined")
        if not isinstance(source_undefined, list):
            errors.append(f"{concept_id}: source_undefined is not a list")
        elif "ordinary learning automatic G status" in source_undefined:
            errors.append(
                f"{concept_id}: forbidden ordinary-learning inference was left source_undefined"
            )
    return errors


def _validate_domains(
    register: Mapping[str, Any],
    candidates: Mapping[str, Mapping[str, Any]],
    paragraphs: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    errors: list[str] = []
    entries = register.get("entries")
    if not isinstance(entries, list):
        return ["v9.0 domain identity register has no entries"]
    expected_ids = [f"D.{ordinal:02d}" for ordinal in range(1, 33)]
    if [entry.get("domain_id") for entry in entries if isinstance(entry, dict)] != expected_ids:
        errors.append("v9.0 domain identity register is not the exact D.01-D.32 sequence")
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("v9.0 domain identity is not an object")
            continue
        domain_id = entry.get("domain_id")
        identity_id = entry.get("identity_id")
        candidate_ids = entry.get("candidate_ids")
        primary = entry.get("primary_candidate_id")
        anchors = entry.get("source_anchors")
        if not isinstance(identity_id, str) or not identity_id.startswith("V90-DOMAIN-D"):
            errors.append(f"{domain_id}: invalid domain machine identity")
        if (
            not isinstance(candidate_ids, list)
            or not candidate_ids
            or any(value not in candidates for value in candidate_ids)
            or primary not in candidate_ids
        ):
            errors.append(f"{domain_id}: domain candidate binding is incomplete")
        if not isinstance(anchors, list) or not anchors or any(
            anchor not in paragraphs for anchor in anchors
        ):
            errors.append(f"{domain_id}: domain source anchors do not resolve")
    return errors


def _decision_rows(
    source_rows: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    identities: list[dict[str, Any]],
    domains: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    source_ids = [str(row.get("candidate_id")) for row in source_rows]
    decision_ids = [str(row.get("candidate_id")) for row in decisions]
    if len(decision_ids) != len(set(decision_ids)):
        errors.append("v9.0 candidate decisions contain duplicate IDs")
    if decision_ids != source_ids:
        errors.append("v9.0 candidate decisions are not an ordered exact source closure")
    decision_by_id = {
        str(row.get("candidate_id")): row for row in decisions
    }
    identity_by_id = {
        str(row["concept_id"]): row for row in identities
    }
    domain_by_id = {str(row["identity_id"]): row for row in domains}
    valid_ids = set(identity_by_id) | set(domain_by_id)
    required_canonical = {
        str(row["primary_candidate_id"]): str(row["concept_id"])
        for row in identities
        if isinstance(row.get("primary_candidate_id"), str)
    }
    required_canonical.update(
        {
            str(row["primary_candidate_id"]): str(row["identity_id"])
            for row in domains
        }
    )
    census: list[dict[str, Any]] = []
    for source in source_rows:
        candidate_id = str(source.get("candidate_id"))
        decision = decision_by_id.get(candidate_id)
        if decision is None:
            continue
        disposition = decision.get("disposition")
        bound_ids = decision.get("bound_identity_ids", [])
        parent_ids = decision.get("parent_identity_ids", [])
        if disposition not in TERMINAL_DISPOSITIONS:
            errors.append(f"{candidate_id}: disposition is not terminal")
        if not isinstance(bound_ids, list) or not isinstance(parent_ids, list):
            errors.append(f"{candidate_id}: identity bindings are not lists")
            bound_ids = []
            parent_ids = []
        if any(value not in valid_ids for value in [*bound_ids, *parent_ids]):
            errors.append(f"{candidate_id}: decision references an unknown identity")
        if disposition in {"canonical", "alias"} and not bound_ids:
            errors.append(f"{candidate_id}: {disposition} decision has no identity target")
        if disposition == "subordinate_value" and not parent_ids:
            errors.append(f"{candidate_id}: subordinate decision has no explicit parent")
        out_kind = decision.get("out_of_scope_kind")
        if disposition == "out_of_scope" and out_kind not in OUT_OF_SCOPE_KINDS:
            errors.append(f"{candidate_id}: out-of-scope reason is not allowed")
        expected_identity = required_canonical.get(candidate_id)
        if expected_identity is not None and (
            disposition != "canonical" or expected_identity not in bound_ids
        ):
            errors.append(
                f"{candidate_id}: primary identity candidate is not canonical for {expected_identity}"
            )
        reason = decision.get("semantic_review_note")
        reason_code = decision.get("disposition_reason")
        if not isinstance(reason, str) or len(reason.strip()) < 12:
            errors.append(f"{candidate_id}: semantic review note is missing")
        if not isinstance(reason_code, str) or not reason_code:
            errors.append(f"{candidate_id}: disposition reason code is missing")
        bound_cards = [
            str(identity_by_id[value]["card_path"])
            for value in bound_ids
            if value in identity_by_id
        ]
        parent_cards = [
            str(identity_by_id[value]["card_path"])
            for value in parent_ids
            if value in identity_by_id
        ]
        row = dict(source)
        row.update(
            {
                "candidate_review_version": 5,
                "disposition": disposition,
                "disposition_status": "final",
                "disposition_reason": reason_code,
                "semantic_review_note": reason,
                "bound_concept_ids": list(bound_ids),
                "bound_card_paths": bound_cards,
                "parent_concept_ids": list(parent_ids),
                "parent_card_paths": parent_cards,
                "out_of_scope_kind": out_kind,
                "source_undefined_fields": list(
                    source.get("source_undefined_fields", [])
                ),
                "review_basis": decision.get("review_basis", {}),
            }
        )
        census.append(row)
    return census, errors


def _dependency_graph(
    identities: list[dict[str, Any]],
    authored_edges: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    source_ids = _source_id_map(identities)
    external_nodes: dict[str, dict[str, str]] = {}
    edges: list[dict[str, Any]] = []
    seen: set[bytes] = set()
    for identity in identities:
        from_id = str(identity["concept_id"])
        interpretation = identity.get("interpretation_layer", {})
        for raw in interpretation.get("dependency_edges", []):
            if not isinstance(raw, dict):
                errors.append(f"{from_id}: dependency edge is not an object")
                continue
            role = raw.get("role")
            target_source_id = raw.get("target_source_concept_id")
            if role not in DEPENDENCY_ROLES or not isinstance(target_source_id, str):
                errors.append(f"{from_id}: dependency edge role or target is invalid")
                continue
            to_id = source_ids.get(target_source_id)
            if to_id is None:
                to_id = _external_gate_id(target_source_id)
                external_nodes[to_id] = {
                    "node_id": to_id,
                    "source_label": target_source_id,
                    "node_kind": "external_gate",
                }
            edge = {
                "from_id": from_id,
                "to_id": to_id,
                "target_source_concept_id": target_source_id,
                "role": role,
                "condition": str(raw.get("condition", "base")),
                "scope": raw.get("scope"),
                "basis": str(raw.get("basis", "source interpretation")),
            }
            key = _canonical(edge)
            if key not in seen:
                seen.add(key)
                edges.append(edge)
        for field in identity.get("source_interface_fields", []):
            if not isinstance(field, dict) or field.get("field") != "input_dependencies":
                continue
            source_value = field.get("source_value")
            if not isinstance(source_value, str) or not source_value.strip():
                continue
            target_source_id = f"input:{identity['source_concept_id']}"
            to_id = _external_gate_id(target_source_id)
            external_nodes[to_id] = {
                "node_id": to_id,
                "source_label": source_value,
                "node_kind": "external_gate",
            }
            edge = {
                "from_id": from_id,
                "to_id": to_id,
                "target_source_concept_id": target_source_id,
                "role": "input_dependencies",
                "condition": "base",
                "scope": "input_availability_only",
                "basis": f"source interface field at body {field.get('body_index_1based')}",
            }
            key = _canonical(edge)
            if key not in seen:
                seen.add(key)
                edges.append(edge)
    known_ids = {str(identity["concept_id"]) for identity in identities}
    for raw in authored_edges:
        if not isinstance(raw, dict):
            errors.append("authored dependency edge is not an object")
            continue
        from_id = raw.get("from_id")
        to_id = raw.get("to_id")
        role = raw.get("role")
        if from_id not in known_ids or role not in DEPENDENCY_ROLES:
            errors.append(f"authored dependency edge source or role is invalid: {raw}")
            continue
        if not isinstance(to_id, str):
            errors.append(f"authored dependency edge target is invalid: {raw}")
            continue
        if to_id not in known_ids:
            if not to_id.startswith("V90-EXTERNAL-GATE-"):
                errors.append(f"authored dependency edge target does not resolve: {to_id}")
                continue
            external_nodes[to_id] = {
                "node_id": to_id,
                "source_label": str(raw.get("target_source_concept_id", to_id)),
                "node_kind": "external_gate",
            }
        edge = {
            "from_id": from_id,
            "to_id": to_id,
            "target_source_concept_id": str(
                raw.get("target_source_concept_id", to_id)
            ),
            "role": role,
            "condition": str(raw.get("condition", "base")),
            "scope": raw.get("scope"),
            "basis": str(raw.get("basis", "candidate adjudication")),
        }
        if raw.get("source_candidate_ids"):
            edge["source_candidate_ids"] = list(raw["source_candidate_ids"])
        if raw.get("source_anchors"):
            edge["source_anchors"] = list(raw["source_anchors"])
        key = _canonical(edge)
        if key not in seen:
            seen.add(key)
            edges.append(edge)
    edges.sort(
        key=lambda edge: (
            str(edge["from_id"]),
            str(edge["role"]),
            str(edge["to_id"]),
            str(edge["condition"]),
        )
    )
    hard_edges = [edge for edge in edges if edge["role"] == "inferential_requires"]
    hard_graph: dict[str, set[str]] = defaultdict(set)
    for edge in hard_edges:
        if edge["to_id"] in known_ids:
            hard_graph[str(edge["from_id"])].add(str(edge["to_id"]))
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            errors.append(f"hard inference dependency cycle includes {node}")
            return
        if node in visited:
            return
        visiting.add(node)
        for target in sorted(hard_graph.get(node, set())):
            visit(target)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(hard_graph):
        visit(node)
    relations: dict[str, dict[str, Any]] = {}
    for identity in identities:
        concept_id = str(identity["concept_id"])
        own_edges = [edge for edge in edges if edge["from_id"] == concept_id]
        relations[concept_id] = {
            "disposition": "canonical_concept",
            "required_neighbors": sorted(
                {
                    str(edge["to_id"])
                    for edge in own_edges
                    if edge["role"] == "inferential_requires"
                    and edge["to_id"] in known_ids
                }
            ),
            "dependency_roles": {
                role: sorted(
                    {
                        str(edge["to_id"])
                        for edge in own_edges
                        if edge["role"] == role
                    }
                )
                for role in sorted(DEPENDENCY_ROLES)
                if any(edge["role"] == role for edge in own_edges)
            },
        }
    graph = {
        "schema_id": "xi-kari.v9.0.dependency-graph",
        "schema_version": 1,
        "framework_version": "v9.0",
        "source_raw_sha256": SOURCE_RAW_SHA256,
        "role_contract": {
            "inferential_requires": "necessary premise and the only role entering the hard inference DAG",
            "protocol_requires": "method, authorization, or release gate; not empirical support",
            "specializes": "type or domain restriction; not evidence",
            "applies_to": "normative or procedural target; not evidence",
            "input_dependencies": "input availability only; not automatically a hard edge",
        },
        "external_nodes": [external_nodes[key] for key in sorted(external_nodes)],
        "edges": edges,
        "hard_inference_edges": hard_edges,
    }
    return graph, relations, errors


def _render_card(identity: Mapping[str, Any], graph: Mapping[str, Any]) -> bytes:
    concept_id = str(identity["concept_id"])
    source_id = str(identity["source_concept_id"])
    source_layer = identity["source_layer"]
    interpretation = identity["interpretation_layer"]
    lines = [
        "---",
        f"id: {concept_id}",
        f"source_concept_id: {source_id}",
        "framework_version: v9.0",
        "---",
        "",
        f"# {source_id}",
        "",
        "## 原文层",
        "",
    ]
    for ref in source_layer["source_refs"]:
        anchors = ", ".join(f"`{anchor}`" for anchor in ref["paragraph_anchors"])
        lines.extend([f"来源：{anchors}", "", str(ref["text"]), ""])
    lines.extend(
        [
            "## 解释层",
            "",
            f"允许边界：{interpretation['positive_boundary']}",
            "",
            f"禁止边界：{interpretation['negative_boundary']}",
            "",
            "## 依赖角色",
            "",
        ]
    )
    own_edges = [
        edge for edge in graph["edges"] if edge["from_id"] == concept_id
    ]
    if own_edges:
        lines.extend(
            [
                "| role | target | condition | basis |",
                "| --- | --- | --- | --- |",
            ]
        )
        for edge in own_edges:
            lines.append(
                f"| `{edge['role']}` | `{edge['to_id']}` | {edge['condition']} | {edge['basis']} |"
            )
    else:
        lines.append("本身份没有登记跨身份依赖边；这不免除具体任务中的输入与方法条件。")
    lines.extend(["", "## source_undefined", ""])
    undefined = identity.get("source_undefined", [])
    if undefined:
        lines.extend(f"- {value}" for value in undefined)
    else:
        lines.append("- 无作为开放默认值登记的源未定义字段。")
    routes = identity.get("conditional_support_routes", [])
    if routes:
        lines.extend(["", "## 条件路由", ""])
        for route in routes:
            lines.append(
                f"- `{route.get('route_id', 'unnamed')}`：{route.get('when', '')}；"
                f"结论上限：{route.get('result_ceiling', '')}"
            )
    lines.append("")
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def _render_family_bundle(
    family: str,
    identities: list[dict[str, Any]],
    graph: Mapping[str, Any],
) -> bytes:
    selected = [identity for identity in identities if identity["semantic_family"] == family]
    selected_ids = {identity["concept_id"] for identity in selected}
    lines = [
        f"# {family} identity bundle",
        "",
        "This bundle is a co-reading boundary over source identities. It is not a new source definition.",
        "",
        "## Identities",
        "",
    ]
    for identity in selected:
        anchors = ", ".join(f"`{anchor}`" for anchor in identity["source_layer"]["source_anchors"])
        lines.append(
            f"- `{identity['concept_id']}` ({identity['source_concept_id']}): {anchors}"
        )
    lines.extend(["", "## Typed dependencies", ""])
    for edge in graph["edges"]:
        if edge["from_id"] in selected_ids:
            lines.append(
                f"- `{edge['from_id']}` --`{edge['role']}`--> `{edge['to_id']}` ({edge['condition']})"
            )
    lines.append("")
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


PACK_SPECS = (
    ("01-object-boundary.md", {"D"}, "对象、边界与通用定义"),
    ("02-evidence-qualification.md", {"G", "E"}, "经验资格与认识约束"),
    ("03-scale-transformation.md", {"O"}, "尺度轴与变换算子"),
    ("04-dynamics-feedback.md", {"CM"}, "机制、反馈与学习"),
    ("05-human-contracts.md", {"H"}, "人类强类型、假设与变量接口"),
    ("06-state-paths.md", {"S"}, "状态原型与退出路径"),
    ("07-claim-bridges.md", {"C"}, "条件桥接与裁决边界"),
    ("08-conditional-routes.md", {"H", "C"}, "条件路由与结论上限"),
    ("09-dependency-roles.md", {"D", "E", "G", "C", "CM", "H", "O", "S", "additional", "extended-source-identity"}, "依赖角色总览"),
)


def _render_learning_pack(
    filename: str,
    families: set[str],
    title: str,
    identities: list[dict[str, Any]],
    graph: Mapping[str, Any],
) -> bytes:
    selected = [identity for identity in identities if identity["semantic_family"] in families]
    selected_ids = {identity["concept_id"] for identity in selected}
    lines = [
        f"# {title}",
        "",
        "本学习包从 v9.0 身份卡与类型化依赖图生成；它组织阅读，不替代原文或候选处置。",
        "",
        "## 必读身份",
        "",
    ]
    for identity in selected:
        lines.append(
            f"- `{identity['source_concept_id']}` → `{identity['concept_id']}`；"
            f"卡片：`{identity['card_path']}`"
        )
    lines.extend(["", "## 边界", ""])
    for identity in selected:
        lines.append(
            f"- `{identity['source_concept_id']}`：{identity['interpretation_layer']['negative_boundary']}"
        )
    lines.extend(["", "## 依赖", ""])
    for edge in graph["edges"]:
        if edge["from_id"] in selected_ids:
            lines.append(
                f"- `{edge['role']}`：`{edge['from_id']}` → `{edge['to_id']}`；{edge['condition']}"
            )
    lines.append("")
    del filename
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def _render_outputs(
    root: Path,
    profile: Any,
    identity_register: Mapping[str, Any],
    extended_register: Mapping[str, Any],
    domain_register: Mapping[str, Any],
    authored_dependencies: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    paragraphs: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, bytes], list[str]]:
    preserved_identities = [
        dict(value) for value in identity_register["identities"]
    ]
    extended_identities = [
        dict(value) for value in extended_register["identities"]
    ]
    identities = [*preserved_identities, *extended_identities]
    domains = [dict(value) for value in domain_register["entries"]]
    candidates = {str(row["candidate_id"]): row for row in source_rows}
    errors = _validate_identity_register(
        root,
        identity_register,
        candidates,
        paragraphs,
        expected_count=93,
    )
    errors.extend(
        _validate_identity_register(
            root,
            extended_register,
            candidates,
            paragraphs,
            expected_count=None,
        )
    )
    if len({identity["concept_id"] for identity in identities}) != len(identities):
        errors.append("v9.0 preserved and extended concept identities collide")
    if len({identity["source_concept_id"] for identity in identities}) != len(
        identities
    ):
        errors.append("v9.0 preserved and extended source identities collide")
    errors.extend(_validate_domains(domain_register, candidates, paragraphs))
    graph, relations, graph_errors = _dependency_graph(
        identities, authored_dependencies
    )
    errors.extend(graph_errors)
    census, decision_errors = _decision_rows(source_rows, decisions, identities, domains)
    errors.extend(decision_errors)
    census_bytes = _jsonl(census)
    files: dict[str, bytes] = {}

    for identity in identities:
        files[str(identity["card_path"])] = _render_card(identity, graph)
    bundle_registry: dict[str, dict[str, Any]] = {}
    for family in sorted({str(identity["semantic_family"]) for identity in identities}):
        path = f"{profile.ontology_root}/bundles/family-{_slug(family)}.md"
        content = _render_family_bundle(family, identities, graph)
        files[path] = content
        bundle_registry[path] = {
            "sha256": sha256(content).hexdigest(),
            "route_kind": "typed_identity_family",
            "semantic_family": family,
        }
    for filename, families, title in PACK_SPECS:
        path = f"{profile.learning_pack_root}/{filename}"
        files[path] = _render_learning_pack(
            filename, families, title, identities, graph
        )

    domain_entries = []
    for domain in domains:
        fingerprint_payload = {
            "domain_id": domain["domain_id"],
            "source_refs": domain["source_refs"],
            "candidate_ids": domain["candidate_ids"],
        }
        domain_entries.append(
            {
                **domain,
                "source_fingerprint_sha256": sha256(
                    _canonical(fingerprint_payload)
                ).hexdigest(),
                "content_status": "identity_only",
                "content_path": None,
                "content_sha256": None,
                "read_trace_status": "not_yet_available",
            }
        )
    domain_index = {
        "schema_id": "xi-kari.v9.0.domain-index",
        "schema_version": 1,
        "framework_version": "v9.0",
        "source_raw_sha256": SOURCE_RAW_SHA256,
        "entry_count": len(domain_entries),
        "entry_count_semantics": "source-defined domain entry identities; P11 content and P12 consumption remain separate",
        "entries": domain_entries,
    }
    files[profile.domain_index] = _pretty(domain_index)

    disposition_counts = Counter(str(row.get("disposition")) for row in census)
    concepts = []
    for identity in identities:
        concept_id = str(identity["concept_id"])
        card_path = str(identity["card_path"])
        card_content = files[card_path]
        concepts.append(
            {
                "concept_id": concept_id,
                "source_concept_id": identity["source_concept_id"],
                "disposition": "canonical_concept",
                "inventory_path": f"{profile.ontology_root}/authored/identity-register.json",
                "card_path": card_path,
                "source_anchors": identity["source_layer"]["source_anchors"],
                "required_neighbors": relations[concept_id]["required_neighbors"],
                "hashes": {
                    "raw_sha256": SOURCE_RAW_SHA256,
                    "card_sha256": sha256(card_content).hexdigest(),
                    "source_text_sha256": identity["source_layer"][
                        "source_text_sha256"
                    ],
                },
                "validation": {
                    "status": "failed" if errors else "passed",
                    "source_anchor_binding": "declared",
                    "card_binding": "declared",
                    "relation_binding": "bounded"
                    if relations[concept_id]["required_neighbors"]
                    else "not_applicable",
                },
            }
        )
    registry = {
        "schema_id": "xi-kari.concept-registry",
        "schema_version": 2,
        "framework_version": "v9.0",
        "source_raw_sha256": SOURCE_RAW_SHA256,
        "identity_register_sha256": sha256(
            _canonical(identity_register)
        ).hexdigest(),
        "extended_identity_register_sha256": sha256(
            _canonical(extended_register)
        ).hexdigest(),
        "concept_count": len(concepts),
        "concept_count_semantics": "accepted source identity register count; not a complete or eternal ontology concept count",
        "candidate_count": len(census),
        "candidate_count_semantics": "reviewed source candidates under ruleset 5; not ontology cardinality",
        "unresolved_candidate_count": 0,
        "candidate_disposition_counts": dict(sorted(disposition_counts.items())),
        "candidate_census_sha256": sha256(census_bytes).hexdigest(),
        "neighbor_policy": "typed dependency graph; only inferential_requires is projected into required_neighbors",
        "concepts": concepts,
    }
    ledger_fields = (
        "bound_card_paths",
        "bound_concept_ids",
        "candidate_id",
        "disposition",
        "disposition_reason",
        "disposition_status",
        "parent_card_paths",
        "parent_concept_ids",
        "semantic_review_note",
        "source_anchor",
        "source_undefined_fields",
    )
    ledger = [
        {field: row.get(field) for field in ledger_fields} for row in census
    ]
    source_map: dict[str, list[str]] = defaultdict(list)
    for identity in identities:
        for anchor in identity["source_layer"]["source_anchors"]:
            source_map[anchor].append(identity["concept_id"])
    aliases = {
        str(identity["source_concept_id"]): str(identity["concept_id"])
        for identity in identities
    }
    aliases.update(
        {
            str(domain["domain_id"]): str(domain["identity_id"])
            for domain in domains
        }
    )
    migration_contract = identity_register.get("migration_contract", {})
    migration_map = {
        "schema_id": "xi-kari.v9.0.concept-migration-map",
        "schema_version": 1,
        "framework_version": "v9.0",
        "source_raw_sha256": SOURCE_RAW_SHA256,
        "preserved_identities": [
            {
                "source_concept_id": identity["source_concept_id"],
                "concept_id": identity["concept_id"],
                "identity_disposition": identity["identity_disposition"],
                "legacy_identity_decision": identity["legacy_identity_decision"],
            }
            for identity in preserved_identities
        ],
        "independently_defined_additions": [
            {
                "source_identity_ref": identity["source_concept_id"],
                "concept_id": identity["concept_id"],
                "primary_candidate_id": identity["primary_candidate_id"],
                "source_anchors": identity["source_layer"]["source_anchors"],
            }
            for identity in extended_identities
        ],
        "cross_document_aliases": migration_contract.get(
            "cross_document_aliases", []
        ),
        "forbidden_merges": migration_contract.get("forbidden_merges", []),
        "new_official_roots": migration_contract.get("new_official_roots", []),
        "new_official_scale_operators": migration_contract.get(
            "new_official_scale_operators", []
        ),
    }
    source_undefined = {
        "schema_id": "xi-kari.v9.0.source-undefined-and-conflicts",
        "schema_version": 1,
        "framework_version": "v9.0",
        "source_raw_sha256": SOURCE_RAW_SHA256,
        "forbidden_inference_correction": identity_register.get(
            "source_undefined_correction"
        ),
        "declared_source_undefined": migration_contract.get(
            "declared_source_undefined", []
        ),
        "identity_source_undefined": {
            str(identity["concept_id"]): list(identity.get("source_undefined", []))
            for identity in identities
            if identity.get("source_undefined")
        },
        "unresolved_candidate_count": 0,
        "unresolved_semantic_conflicts": [],
    }
    files.update(
        {
            f"{profile.ontology_root}/candidate-census.jsonl": census_bytes,
            f"{profile.ontology_root}/concept-disposition-ledger.jsonl": _jsonl(
                ledger
            ),
            f"{profile.ontology_root}/candidate-semantic-scopes.json": _pretty(
                {
                    "schema_id": "xi-kari.v9.0.candidate-semantic-scopes",
                    "schema_version": 1,
                    "framework_version": "v9.0",
                    "review_count_semantics": "one explicit terminal review per ruleset-5 source candidate",
                    "reviews": decisions,
                }
            ),
            f"{profile.ontology_root}/concept-registry.json": _pretty(registry),
            f"{profile.ontology_root}/concept-relations.json": _pretty(relations),
            f"{profile.ontology_root}/dependency-graph.json": _pretty(graph),
            f"{profile.ontology_root}/source-to-concept-map.json": _pretty(
                {key: sorted(set(value)) for key, value in sorted(source_map.items())}
            ),
            f"{profile.ontology_root}/identity-aliases.json": _pretty(
                {
                    "schema_id": "xi-kari.v9.0.identity-aliases",
                    "schema_version": 1,
                    "framework_version": "v9.0",
                    "aliases": aliases,
                }
            ),
            f"{profile.ontology_root}/concept-migration-map.json": _pretty(
                migration_map
            ),
            f"{profile.ontology_root}/source-undefined-and-conflicts.json": _pretty(
                source_undefined
            ),
            f"{profile.ontology_root}/continuity-bundle-registry.json": _pretty(
                {
                    "schema_id": "xi-kari.v9.0.continuity-bundle-registry",
                    "schema_version": 1,
                    "framework_version": "v9.0",
                    "bundles": bundle_registry,
                }
            ),
        }
    )

    family_lines = [
        "# Xi-Kari v9.0 identity families",
        "",
        "This generated index organizes accepted identities; it does not assert a complete concept universe.",
        "",
        "| family | source identity | machine identity | card |",
        "| --- | --- | --- | --- |",
    ]
    for identity in identities:
        family_lines.append(
            f"| `{identity['semantic_family']}` | `{identity['source_concept_id']}` | "
            f"`{identity['concept_id']}` | `{identity['card_path']}` |"
        )
    files[f"{profile.ontology_root}/concept-family-map.md"] = (
        "\n".join(family_lines) + "\n"
    ).encode("utf-8")
    continuity_lines = [
        "# Xi-Kari v9.0 continuity bundles",
        "",
        "Each bundle is a co-reading boundary, not a new source definition.",
        "",
    ]
    continuity_lines.extend(
        f"- `{path}`: `{binding['sha256']}`"
        for path, binding in sorted(bundle_registry.items())
    )
    files[f"{profile.ontology_root}/continuity-map.md"] = (
        "\n".join(continuity_lines) + "\n"
    ).encode("utf-8")

    authored_paths = [
        f"{profile.ontology_root}/authored/identity-register.json",
        f"{profile.ontology_root}/authored/extended-identities.json",
        f"{profile.ontology_root}/authored/domain-identities.json",
        f"{profile.ontology_root}/authored/candidate-decisions.jsonl",
        f"{profile.ontology_root}/authored/dependency-bindings.json",
    ]
    asset_rows = [
        {
            "path": path,
            "sha256": sha256(content).hexdigest(),
            "bytes": len(content),
        }
        for path, content in sorted(files.items())
    ]
    for path in authored_paths:
        source = root / path
        if source.is_file() and not source.is_symlink():
            payload = source.read_bytes()
            asset_rows.append(
                {"path": path, "sha256": sha256(payload).hexdigest(), "bytes": len(payload)}
            )
    cards = [row for row in asset_rows if "/cards/" in row["path"]]
    bundles = [row for row in asset_rows if "/bundles/" in row["path"]]
    learning_packs = [
        row for row in asset_rows if row["path"].startswith(profile.learning_pack_root + "/")
    ]
    knowledge_index = {
        "schema_id": "xi-kari.v9.0.knowledge-index",
        "schema_version": 1,
        "framework_version": "v9.0",
        "source_raw_sha256": SOURCE_RAW_SHA256,
        "preserved_identity_count": len(preserved_identities),
        "identity_count": len(identities),
        "identity_count_semantics": "accepted preserved and independently defined candidate identities; not a complete concept universe",
        "domain_identity_count": len(domains),
        "candidate_count": len(census),
        "unresolved_candidate_count": 0,
        "cards": cards,
        "bundles": bundles,
        "learning_packs": learning_packs,
        "assets": sorted(asset_rows, key=lambda row: row["path"]),
    }
    files[f"{profile.ontology_root}/knowledge-index.json"] = _pretty(knowledge_index)
    return files, errors


def _generated_paths(profile: Any) -> tuple[str, ...]:
    return (
        f"{profile.ontology_root}/candidate-census.jsonl",
        f"{profile.ontology_root}/concept-disposition-ledger.jsonl",
        f"{profile.ontology_root}/candidate-semantic-scopes.json",
        f"{profile.ontology_root}/concept-registry.json",
        f"{profile.ontology_root}/concept-relations.json",
        f"{profile.ontology_root}/dependency-graph.json",
        f"{profile.ontology_root}/source-to-concept-map.json",
        f"{profile.ontology_root}/identity-aliases.json",
        f"{profile.ontology_root}/concept-migration-map.json",
        f"{profile.ontology_root}/source-undefined-and-conflicts.json",
        f"{profile.ontology_root}/continuity-bundle-registry.json",
        f"{profile.ontology_root}/concept-family-map.md",
        f"{profile.ontology_root}/continuity-map.md",
        f"{profile.ontology_root}/knowledge-index.json",
        profile.domain_index,
    )


def run(root: Path, *, check: bool, profile: Any) -> list[str]:
    root = Path(root).resolve()
    ontology_root = root / profile.ontology_root
    identity_register, errors = _load_json(
        ontology_root / "authored" / "identity-register.json",
        "v9.0 identity register",
    )
    extended_register, load_errors = _load_json(
        ontology_root / "authored" / "extended-identities.json",
        "v9.0 extended identity register",
    )
    errors.extend(load_errors)
    domain_register, load_errors = _load_json(
        ontology_root / "authored" / "domain-identities.json",
        "v9.0 domain identity register",
    )
    errors.extend(load_errors)
    decisions, load_errors = _load_jsonl(
        ontology_root / "authored" / "candidate-decisions.jsonl",
        "v9.0 candidate decisions",
    )
    errors.extend(load_errors)
    authored_dependency_value, load_errors = _load_json(
        ontology_root / "authored" / "dependency-bindings.json",
        "v9.0 authored dependency bindings",
    )
    errors.extend(load_errors)
    source_rows, load_errors = _load_jsonl(
        root / profile.source_root / "indexes" / "candidates.jsonl",
        "v9.0 source candidates",
    )
    errors.extend(load_errors)
    paragraph_rows, load_errors = _load_jsonl(
        root / profile.source_root / "audit" / "paragraphs.jsonl",
        "v9.0 source paragraphs",
    )
    errors.extend(load_errors)
    if (
        not isinstance(identity_register, dict)
        or not isinstance(extended_register, dict)
        or not isinstance(domain_register, dict)
        or not isinstance(authored_dependency_value, dict)
    ):
        return sorted(set(errors))
    authored_dependencies = authored_dependency_value.get("edges")
    if not isinstance(authored_dependencies, list):
        errors.append("v9.0 authored dependency bindings have no edge list")
        return sorted(set(errors))
    paragraphs = {
        str(row["anchor"]): row
        for row in paragraph_rows
        if isinstance(row.get("anchor"), str)
    }
    generated, generation_errors = _render_outputs(
        root,
        profile,
        identity_register,
        extended_register,
        domain_register,
        authored_dependencies,
        source_rows,
        decisions,
        paragraphs,
    )
    errors.extend(generation_errors)
    if errors:
        return sorted(set(errors))
    if check:
        for relative, content in generated.items():
            path = root / relative
            if path.is_symlink() or not path.is_file():
                errors.append(f"missing or unsafe generated v9.0 knowledge asset: {relative}")
            elif path.read_bytes() != content:
                errors.append(f"generated v9.0 knowledge asset differs: {relative}")
        return sorted(set(errors))
    for relative, content in sorted(generated.items()):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    expected = set(generated)
    generated_roots = (
        root / profile.ontology_root / "cards",
        root / profile.ontology_root / "bundles",
        root / profile.learning_pack_root,
    )
    for generated_root in generated_roots:
        if not generated_root.exists():
            continue
        for path in generated_root.rglob("*"):
            if path.is_file() and path.relative_to(root).as_posix() not in expected:
                path.unlink()
    return []
