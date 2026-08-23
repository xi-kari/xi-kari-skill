"""Typed plain-language projection shared by prose, privacy, and coverage."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any


_SKIP_KEYS = {
    "$schema",
    "schema_id",
    "schema_version",
    "source_version",
    "ontology_refs",
    "source_anchors",
    "run_id",
    "input_packet_sha256",
    "visibility_ledger",
    "evidence_state",
}
_SKIP_SUFFIXES = ("_sha256",)
_ID_PREFIX_LABELS = {
    "ACTOR": "行动者",
    "BRANCH": "分支",
    "CHANNEL": "通道",
    "CIRCLE": "圈层",
    "CLAIM": "命题",
    "CLOCK": "时钟",
    "COMP": "组成部分",
    "DIFF": "状态差",
    "DIST": "局部分布",
    "EVIDENCE": "证据",
    "EVENT": "事件",
    "EXPLANATION": "解释",
    "INDICATOR": "指标",
    "LOSS": "损失",
    "M": "物质状态",
    "MECHANISM": "机制",
    "NODE": "推演节点",
    "OPTION": "方案",
    "PATH": "路径",
    "POS": "位置",
    "PSI": "体验意义状态",
    "QUERY": "查询",
    "RAC": "行动者圈层关系",
    "RCC": "圈层关系",
    "RELATION": "关系",
    "RESIDUAL": "残差",
    "ROLE": "角色",
    "SIGNAL": "信号",
    "SOURCE": "来源",
    "STATE": "状态",
    "TRANSFORM": "变换",
    "UNKNOWN": "未知",
    "VAR": "变量",
    "VERDICT": "裁决",
    "VOLUME": "局部世界",
}
_ID_TOKEN = re.compile(
    r"(?<![A-Z0-9_-])(?:"
    + "|".join(sorted(_ID_PREFIX_LABELS, key=len, reverse=True))
    + r")-[A-Z0-9_.:-]+\b"
)
INTERNAL_ID_TOKEN = _ID_TOKEN
_EXACT_ID = re.compile(r"^([A-Z][A-Z0-9]*)-[A-Z0-9_.:-]+$")

_FIELD_LABELS = {
    "A": "聚合尺度",
    "C": "因果尺度",
    "I": "影响尺度",
    "J": "授权尺度",
    "N": "网络尺度",
    "O": "组织尺度",
    "R": "观察分辨率",
    "T": "时间尺度",
    "X": "空间尺度",
    "M_state": "物质状态",
    "Psi_state": "体验意义状态",
    "active": "通道启用",
    "actor_id": "行动者",
    "actor_ref": "行动者",
    "acl_authorized": "访问授权成立",
    "ancestor_circle_ids": "上位圈层",
    "authorization_evidence_refs": "授权证据",
    "authorization_scope": "原子授权范围",
    "authorized_position_ids": "获授权位置",
    "baseline": "简单基线",
    "basis": "关系依据",
    "blocked_by_node_id": "被哪个节点阻断",
    "boundary_rule": "对象边界规则",
    "capacity": "通道容量",
    "carrier": "载体",
    "channel_id": "通道",
    "channel_ids": "通道",
    "circle_id": "圈层",
    "circle_ref": "圈层",
    "clock": "作用时钟",
    "clock_id": "时钟",
    "closed": "变换闭合",
    "conditions": "成立条件",
    "current_time": "当前时间",
    "decision_subject": "决策主体",
    "declared_evidence_grade": "证据等级",
    "delay": "通道时延",
    "description": "说明",
    "direction": "方向",
    "discriminating_observations": "区分性观察",
    "evidence_identity": "证据身份",
    "evidence_refs": "证据边界",
    "executor": "执行主体",
    "failure_condition": "失败条件",
    "from_position_id": "通道起点",
    "horizon": "时间范围",
    "identity_criteria": "同一性判据",
    "identity_preserved": "同一性保持",
    "input_identity": "输入身份",
    "input_state": "输入状态",
    "kind": "类型",
    "local_predictability": "局部可预测性",
    "location_ref": "所在位置",
    "loss_ratio": "任务相对损失比例",
    "mapping_rule": "身份映射规则",
    "membership_basis": "成员关系依据",
    "name": "名称",
    "numeric_probability": "条件数值概率",
    "object_ids": "对象",
    "order": "推演阶次",
    "origin_kind": "事件来源类型",
    "output_identity": "输出身份",
    "output_state": "输出状态",
    "parent_circle_id": "父圈层",
    "parent_node_ids": "父节点",
    "parent_state_ids": "父状态",
    "preserves_identity": "保持同一性",
    "proposition": "裁决命题",
    "relation_type": "圈层关系类型",
    "reverse_signal": "反向信号",
    "reverse_signals": "反向信号",
    "role_id": "角色",
    "roles": "角色",
    "scale_or_circle": "尺度或圈层",
    "scale_profile": "九轴尺度剖面",
    "scope_id": "时钟作用范围",
    "single_action": "单一动作",
    "source_circle_ref": "关系起点",
    "source_evidence_id": "授权来源证据",
    "source_k_ref": "输入同一性判据",
    "state_delta": "状态变化",
    "status": "状态",
    "stop_reason": "停止理由",
    "target_circle_ref": "关系终点",
    "target_k_ref": "输出同一性判据",
    "target_object": "目标对象",
    "threshold": "通道阈值",
    "threshold_met": "阈值已满足",
    "to_position_id": "通道终点",
    "territory": "授权地域",
    "unit": "计量单位",
    "validity_interval": "有效期",
    "value": "变量值",
    "writeback": "制度或状态写回",
}
_ENUM_LABELS = {
    "active": "启用",
    "bounded": "有限成立",
    "circle-relation": "圈层关系变换",
    "competing-explanation": "竞争解释",
    "conditional": "条件成立",
    "directed": "有向",
    "fact": "事实裁决",
    "factual": "事实命题",
    "high": "高",
    "inferred-from-material": "基于材料的推断",
    "locked": "已锁定",
    "low": "低",
    "main": "主路径",
    "medium": "中",
    "mixture": "混合路径",
    "model-candidate": "模型候选",
    "non-decidability": "当前不可定选",
    "observed": "直接观察",
    "prediction": "预测裁决",
    "pruned": "已剪枝",
    "reported": "来源报告",
    "representation-translation": "表示或表达转义",
    "residual": "残差路径",
    "responsibility": "责任裁决",
    "scale": "尺度变换",
    "simulated-result": "模拟结果，不是现实事实",
    "stopped": "已停止",
    "strongest-rival": "最强竞争路径",
    "structural": "结构命题",
    "supported": "有支持",
    "unknown": "未知",
    "user-claim": "用户陈述",
    "user-material": "用户材料",
    "value": "价值裁决",
    "authorization": "授权裁决",
}
_BRANCH_LABELS = {
    "main": "主路径",
    "strongest-rival": "最强竞争路径",
    "mixture": "混合路径",
    "residual": "残差路径",
}
_REGISTRY_FIELDS = {"recursive_states"}
_DELIVERY_VISIBILITY_ROOTS = (
    "problem_contract",
    "facts",
    "retrieval",
    "evidence",
    "case_ledger",
    "cases",
    "local_world_model",
    "transformation_ledger",
    "cascade",
    "claim_mechanism_graph",
    "recursive_lineage",
    "recursive_states",
    "order_evaluation",
    "red_team",
    "stance_pair",
    "verdict",
    "action_ranking",
    "forecast",
    "mechanisms",
    "orders",
    "answer",
    "not_applicable_reason",
)
VISIBILITY_CLASSES = {
    "public",
    "context_limited",
    "sensitive",
    "highly_sensitive",
    "refused_disclosure",
}


def _field_label(key: str | None) -> str:
    if key is None:
        return "内容"
    return _FIELD_LABELS.get(key, key.replace("_", " "))


def _value_type(value: Any, *, key: str | None = None) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if value is None:
        return "null"
    if key in {"kind", "status", "identity", "evidence_identity", "declared_evidence_grade"}:
        return "enum"
    if isinstance(value, str) and _exact_id_prefix(value) is not None:
        return "reference"
    return "string"


def _exact_id_prefix(value: str) -> str | None:
    match = _EXACT_ID.fullmatch(value)
    if match and match.group(1) in _ID_PREFIX_LABELS:
        return match.group(1)
    return None


def _collect_ids(value: Any, result: set[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key == "visibility_ledger":
                continue
            _collect_ids(child, result)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            _collect_ids(child, result)
    elif isinstance(value, str) and _exact_id_prefix(value) is not None:
        result.add(value)


def _alias_book(payload: Mapping[str, Any]) -> dict[str, str]:
    identifiers: set[str] = set()
    _collect_ids(payload, identifiers)
    counters: dict[str, int] = {}
    aliases: dict[str, str] = {}
    for identifier in sorted(identifiers):
        prefix = _exact_id_prefix(identifier)
        if prefix is None:
            continue
        counters[prefix] = counters.get(prefix, 0) + 1
        aliases[identifier] = f"{_ID_PREFIX_LABELS[prefix]} {counters[prefix]}"
    return aliases


def _replace_embedded_ids(text: str, aliases: Mapping[str, str]) -> str:
    return _ID_TOKEN.sub(lambda match: aliases.get(match.group(0), "已登记对象"), text)


def _public_scalar(value: Any, aliases: Mapping[str, str]) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    if value is None:
        return "未记录"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).strip()
    if not text:
        return "未记录"
    if text.startswith(("http://", "https://")):
        return "外部来源地址已在来源表登记"
    if text in aliases:
        return aliases[text]
    return _ENUM_LABELS.get(text, _replace_embedded_ids(text, aliases))


def _visibility_entries(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    ledger = payload.get("visibility_ledger")
    if not isinstance(ledger, Mapping):
        return {}
    entries = ledger.get("entries")
    if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes, bytearray)):
        return {}
    return {
        str(entry.get("canonical_path")): entry
        for entry in entries
        if isinstance(entry, Mapping) and isinstance(entry.get("canonical_path"), str)
    }


def _canonical_child(base: str, key: str) -> str:
    return f"{base}.{key}" if base else key


def _atom(
    *,
    path: str,
    key: str | None,
    value: Any,
    aliases: Mapping[str, str],
    visibility: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    entry = visibility.get(path, {})
    classification = str(entry.get("classification", "public"))
    disclosure = str(entry.get("disclosure", "include"))
    label = _field_label(key)
    if disclosure == "withhold":
        reason = str(entry.get("protection_reason") or "披露风险超过本题的信息价值")
        public_text = f"{label}：为保护而不公开（{reason}）"
        projection_status = "withheld_for_protection"
    else:
        public_text = f"{label}：{_public_scalar(value, aliases)}"
        projection_status = "audit_only"
    return {
        "atom_id": path,
        "canonical_path": path,
        "value_type": _value_type(value, key=key),
        "public_text": public_text,
        "required_outputs": [],
        "visibility": classification,
        "projection_status": projection_status,
    }


def _walk_atoms(
    value: Any,
    *,
    base_path: str,
    key: str | None,
    aliases: Mapping[str, str],
    visibility: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    atoms: list[dict[str, Any]] = []
    if isinstance(value, Mapping):
        if key in _REGISTRY_FIELDS:
            for index, registry_key in enumerate(sorted(value, key=str)):
                atoms.extend(
                    _walk_atoms(
                        value[registry_key],
                        base_path=f"{base_path}[{index}]",
                        key=None,
                        aliases=aliases,
                        visibility=visibility,
                    )
                )
            return atoms
        for child_key, child in value.items():
            child_key = str(child_key)
            if child_key in _SKIP_KEYS or child_key.endswith(_SKIP_SUFFIXES):
                continue
            atoms.extend(
                _walk_atoms(
                    child,
                    base_path=_canonical_child(base_path, child_key),
                    key=child_key,
                    aliases=aliases,
                    visibility=visibility,
                )
            )
        return atoms
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            atoms.extend(
                _walk_atoms(
                    child,
                    base_path=f"{base_path}[{index}]",
                    key=key,
                    aliases=aliases,
                    visibility=visibility,
                )
            )
        return atoms
    if isinstance(value, str) and not value.strip():
        return atoms
    atoms.append(
        _atom(
            path=base_path,
            key=key,
            value=value,
            aliases=aliases,
            visibility=visibility,
        )
    )
    return atoms


def semantic_fragments(value: Any, *, _key: str | None = None) -> list[str]:
    """Compatibility helper returning typed public text for one value."""

    aliases = _alias_book({"value": value})
    atoms = _walk_atoms(
        value,
        base_path=_key or "value",
        key=_key,
        aliases=aliases,
        visibility={},
    )
    return [atom["public_text"] for atom in atoms]


def _unit(
    *,
    unit_id: str,
    unit_kind: str,
    heading: str,
    atoms: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not atoms:
        return None
    return {
        "unit_id": unit_id,
        "unit_kind": unit_kind,
        "heading": heading,
        "atoms": atoms,
        "fragments": [atom["public_text"] for atom in atoms],
    }


def semantic_projection_units(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Build typed, destination-bound readable authority units for XK5-XK10."""

    if payload.get("dynamic_applicability") == "not_applicable":
        return []
    aliases = _alias_book(payload)
    visibility = _visibility_entries(payload)
    units: list[dict[str, Any]] = []

    def add(
        unit_id: str,
        unit_kind: str,
        heading: str,
        value: Any,
        *,
        base_path: str,
        key: str | None = None,
    ) -> None:
        unit = _unit(
            unit_id=unit_id,
            unit_kind=unit_kind,
            heading=heading,
            atoms=_walk_atoms(
                value,
                base_path=base_path,
                key=key,
                aliases=aliases,
                visibility=visibility,
            ),
        )
        if unit is not None:
            units.append(unit)

    add(
        "semantic.omega",
        "local_world_model",
        "局部世界模型：对象、关系、未知与残差",
        payload.get("local_world_model"),
        base_path="local_world_model",
    )

    ledger = payload.get("transformation_ledger")
    transformations = ledger.get("transformations", []) if isinstance(ledger, Mapping) else []
    for index, transformation in enumerate(transformations):
        add(
            f"semantic.transformation.{index + 1}",
            "transformation",
            f"第 {index + 1} 条尺度、圈层或表示变换",
            transformation,
            base_path=f"transformation_ledger.transformations[{index}]",
        )

    graph = payload.get("claim_mechanism_graph")
    explanations = graph.get("explanations", []) if isinstance(graph, Mapping) else []
    for index, explanation in enumerate(explanations):
        kind = explanation.get("kind") if isinstance(explanation, Mapping) else None
        heading = {
            "simple-baseline": "简单基线",
            "main": "主解释",
            "strongest-rival": "最强竞争解释",
            "mixture": "混合解释",
            "residual": "残差解释",
        }.get(kind, f"解释 {index + 1}")
        add(
            f"semantic.explanation.{index + 1}",
            "explanation",
            heading,
            explanation,
            base_path=f"claim_mechanism_graph.explanations[{index}]",
        )

    verdict = payload.get("verdict")
    five_verdicts = verdict.get("five_verdicts", []) if isinstance(verdict, Mapping) else []
    for index, record in enumerate(five_verdicts):
        kind = record.get("kind") if isinstance(record, Mapping) else None
        heading = {
            "fact": "事实裁决",
            "prediction": "预测裁决",
            "value": "价值裁决",
            "responsibility": "责任裁决",
            "authorization": "授权裁决",
        }.get(kind, f"裁决 {index + 1}")
        add(
            f"semantic.verdict.{index + 1}",
            "verdict",
            heading,
            record,
            base_path=f"verdict.five_verdicts[{index}]",
        )

    add(
        "semantic.forecast",
        "forecast",
        "前瞻目标、时间窗、条件路径与反向信号",
        payload.get("forecast"),
        base_path="forecast",
    )

    lineage = payload.get("recursive_lineage")
    states = payload.get("recursive_states")
    state_items = (
        [states[key] for key in sorted(states, key=str)]
        if isinstance(states, Mapping)
        else []
    )
    state_by_node = {
        state.get("node_id"): (index, state)
        for index, state in enumerate(state_items)
        if isinstance(state, Mapping) and isinstance(state.get("node_id"), str)
    }
    branches = lineage.get("branches", []) if isinstance(lineage, Mapping) else []
    for index, branch in enumerate(branches):
        if not isinstance(branch, Mapping):
            continue
        kind = str(branch.get("kind", ""))
        atoms = _walk_atoms(
            branch,
            base_path=f"recursive_lineage.branches[{index}]",
            key=None,
            aliases=aliases,
            visibility=visibility,
        )
        for node_id in branch.get("node_ids", []):
            state_item = state_by_node.get(node_id)
            if state_item is None:
                continue
            state_index, state = state_item
            atoms.extend(
                _walk_atoms(
                    state,
                    base_path=f"recursive_states[{state_index}]",
                    key=None,
                    aliases=aliases,
                    visibility=visibility,
                )
            )
        unit = _unit(
            unit_id=f"semantic.recursive-branch.{index + 1}",
            unit_kind="recursive_branch",
            heading=_BRANCH_LABELS.get(kind, f"递归分支 {index + 1}"),
            atoms=atoms,
        )
        if unit is not None:
            units.append(unit)

    not_run_orders = lineage.get("not_run_orders", []) if isinstance(lineage, Mapping) else []
    for index, record in enumerate(not_run_orders):
        add(
            f"semantic.not-run.{index + 1}",
            "not_run_order",
            "合法停止",
            record,
            base_path=f"recursive_lineage.not_run_orders[{index}]",
        )
    return units


def typed_semantic_atoms(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return the complete typed atom ledger for every delivery-readable root."""

    atoms: list[dict[str, Any]] = []
    aliases = _alias_book(payload)
    visibility = _visibility_entries(payload)
    for root in _DELIVERY_VISIBILITY_ROOTS:
        if root not in payload:
            continue
        atoms.extend(
            _walk_atoms(
                payload[root],
                base_path=root,
                key=root,
                aliases=aliases,
                visibility=visibility,
            )
        )
    return list(
        {
            atom["canonical_path"]: atom
            for atom in atoms
        }.values()
    )


def semantic_atom_paths(payload: Mapping[str, Any]) -> list[str]:
    """Return the exact typed paths that require an explicit visibility decision."""

    return [atom["canonical_path"] for atom in typed_semantic_atoms(payload)]


def protected_retrieval_values(payload: Mapping[str, Any]) -> dict[str, str]:
    """Return exact non-public retrieval title/content values by source path."""

    retrieval = payload.get("retrieval")
    sources = retrieval.get("sources") if isinstance(retrieval, Mapping) else None
    if not isinstance(sources, list):
        return {}
    visibility = _visibility_entries(payload)
    protected: dict[str, str] = {}
    for index, source in enumerate(sources):
        if not isinstance(source, Mapping):
            continue
        for field in ("title", "content"):
            path = f"retrieval.sources[{index}].{field}"
            entry = visibility.get(path)
            value = source.get(field)
            if (
                isinstance(entry, Mapping)
                and entry.get("classification") != "public"
                and entry.get("disclosure") == "withhold"
                and isinstance(value, str)
                and value
            ):
                protected[path] = value
    return protected


def _validate_protected_retrieval_value_isolation(
    payload: Mapping[str, Any], entries: Sequence[Mapping[str, Any]]
) -> None:
    protected = protected_retrieval_values(payload)
    if not protected:
        return
    by_path = {
        str(entry["canonical_path"]): entry
        for entry in entries
        if isinstance(entry.get("canonical_path"), str)
    }
    for protected_path, protected_value in protected.items():
        for entry in entries:
            reason = entry.get("protection_reason")
            if isinstance(reason, str) and protected_value in reason:
                raise ValueError(
                    "protected retrieval value appears in visibility protection_reason: "
                    + protected_path
                )
        for public_path in semantic_atom_paths(payload):
            if public_path == protected_path:
                continue
            entry = by_path.get(public_path)
            if (
                not isinstance(entry, Mapping)
                or entry.get("classification") != "public"
                or entry.get("disclosure") != "include"
            ):
                continue
            resolved = _resolve_path_parent(payload, public_path)
            if resolved is None:
                raise ValueError(
                    "cannot resolve public visibility path while checking protected values: "
                    + public_path
                )
            parent, leaf = resolved
            if isinstance(leaf, int) and isinstance(parent, list) and leaf < len(parent):
                public_value = parent[leaf]
            elif isinstance(leaf, str) and isinstance(parent, Mapping) and leaf in parent:
                public_value = parent[leaf]
            else:
                raise ValueError(
                    "cannot resolve public visibility path while checking protected values: "
                    + public_path
                )
            if protected_value in str(public_value):
                raise ValueError(
                    "protected retrieval value appears in public semantic atom: "
                    f"{protected_path} -> {public_path}"
                )


def _protected_atom_reason_forms(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, bool):
        return ("true", "True", "是") if value else ("false", "False", "否")
    if isinstance(value, (int, float)):
        return (str(value),)
    return ()


def _validate_protection_reason_value_isolation(
    payload: Mapping[str, Any], entries: Sequence[Mapping[str, Any]]
) -> None:
    for entry in entries:
        if entry.get("disclosure") != "withhold":
            continue
        path = entry.get("canonical_path")
        reason = entry.get("protection_reason")
        if not isinstance(path, str) or not isinstance(reason, str):
            continue
        resolved = _resolve_path_parent(payload, path)
        if resolved is None:
            raise ValueError("cannot resolve withheld visibility path: " + path)
        parent, leaf = resolved
        if isinstance(leaf, int) and isinstance(parent, list) and leaf < len(parent):
            value = parent[leaf]
        elif isinstance(leaf, str) and isinstance(parent, Mapping) and leaf in parent:
            value = parent[leaf]
        else:
            raise ValueError("cannot resolve withheld visibility path: " + path)
        if any(form and form in reason for form in _protected_atom_reason_forms(value)):
            raise ValueError("protection_reason contains a withheld atom: " + path)


def validate_visibility_ledger(
    payload: Mapping[str, Any], *, expected_purpose: str | None = None
) -> None:
    """Require an exact, explicit visibility decision for every delivery atom."""

    ledger = payload.get("visibility_ledger")
    if not isinstance(ledger, Mapping):
        raise ValueError("analysis packet requires an explicit visibility ledger")
    entries = ledger.get("entries")
    if not isinstance(entries, list):
        raise ValueError("visibility ledger entries must be a list")
    paths: list[str] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError("visibility ledger entry must be an object")
        path = entry.get("canonical_path")
        if not isinstance(path, str) or not path:
            raise ValueError("visibility ledger canonical path must be non-empty")
        paths.append(path)
        classification = entry.get("classification")
        disclosure = entry.get("disclosure")
        if classification not in VISIBILITY_CLASSES:
            raise ValueError("visibility ledger classification is invalid")
        if disclosure not in {"include", "withhold"}:
            raise ValueError("visibility ledger disclosure is invalid")
        purpose = entry.get("purpose")
        if not isinstance(purpose, str) or not purpose.strip():
            raise ValueError("visibility ledger purpose must be non-empty")
        if expected_purpose is not None and purpose != expected_purpose:
            raise ValueError("visibility ledger purpose differs from XK0 privacy contract")
        authority_refs = entry.get("authority_refs")
        protection_reason = entry.get("protection_reason")
        if (
            not isinstance(authority_refs, list)
            or any(
                not isinstance(reference, str) or not reference.strip()
                for reference in authority_refs
            )
            or len(authority_refs) != len(set(authority_refs))
        ):
            raise ValueError(
                "visibility authority refs must be unique non-empty text"
            )
        if classification == "public":
            if disclosure != "include":
                raise ValueError("public visibility cannot be marked withheld")
        else:
            if disclosure != "withhold":
                raise ValueError("non-public visibility must remain withheld")
            if (
                not authority_refs
                or not isinstance(protection_reason, str)
                or not protection_reason.strip()
            ):
                raise ValueError(
                    "non-public visibility requires protection authority and reason"
                )
    if len(paths) != len(set(paths)):
        raise ValueError("visibility ledger contains duplicate semantic atom")
    expected_paths = set(semantic_atom_paths(payload))
    observed_paths = set(paths)
    dangling = sorted(observed_paths - expected_paths)
    if dangling:
        raise ValueError(
            "visibility ledger contains dangling semantic atom: " + dangling[0]
        )
    missing = sorted(expected_paths - observed_paths)
    if missing:
        raise ValueError("visibility ledger is missing semantic atom: " + missing[0])
    _validate_protection_reason_value_isolation(payload, entries)
    _validate_protected_retrieval_value_isolation(payload, entries)


_PATH_TOKEN = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*)|\[([0-9]+)\]")


def _resolve_path_parent(root: Any, path: str) -> tuple[Any, str | int] | None:
    tokens: list[str | int] = []
    for match in _PATH_TOKEN.finditer(path):
        tokens.append(
            int(match.group(2)) if match.group(2) is not None else match.group(1)
        )
    if not tokens:
        return None
    current = root
    for token in tokens[:-1]:
        if isinstance(token, int):
            if isinstance(current, list):
                if token >= len(current):
                    return None
                current = current[token]
            elif isinstance(current, Mapping):
                keys = sorted(current, key=str)
                if token >= len(keys):
                    return None
                current = current[keys[token]]
            else:
                return None
        elif isinstance(current, Mapping) and token in current:
            current = current[token]
        else:
            return None
    return current, tokens[-1]


def redact_payload_for_delivery(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Apply explicit withholding decisions before any delivery renderer runs."""

    validate_visibility_ledger(payload)
    sanitized = deepcopy(dict(payload))
    for path, entry in _visibility_entries(payload).items():
        if entry.get("disclosure") != "withhold":
            continue
        resolved = _resolve_path_parent(sanitized, path)
        if resolved is None:
            raise ValueError(f"cannot resolve withheld visibility path: {path}")
        parent, leaf = resolved
        reason = str(entry.get("protection_reason") or "披露风险超过本题的信息价值")
        text_replacement = f"为保护而不公开（{reason}）"
        applied = False
        if isinstance(leaf, int) and isinstance(parent, list) and leaf < len(parent):
            parent[leaf] = (
                text_replacement if isinstance(parent[leaf], str) else None
            )
            applied = True
        elif isinstance(leaf, str) and isinstance(parent, dict) and leaf in parent:
            parent[leaf] = (
                text_replacement if isinstance(parent[leaf], str) else None
            )
            applied = True
        if not applied:
            raise ValueError(f"cannot resolve withheld visibility path: {path}")
    problem = sanitized.get("problem_contract")
    if isinstance(problem, Mapping) and "question" in problem:
        sanitized["question"] = problem["question"]
    retrieval = sanitized.get("retrieval")
    if isinstance(retrieval, Mapping):
        sanitized["sources"] = deepcopy(list(retrieval.get("sources", [])))
        sanitized["assessments"] = deepcopy(
            list(retrieval.get("assessments", []))
        )
    return sanitized


@dataclass(frozen=True)
class ReaderValue:
    text: str
    exact_source_paths: tuple[str, ...]


@dataclass(frozen=True)
class ReaderFragment:
    text: str
    exact_source_paths: tuple[str, ...]


def _reader_value(
    value: Any,
    path: str,
    aliases: Mapping[str, str],
) -> ReaderValue:
    if isinstance(value, Mapping):
        for field in (
            "description",
            "summary",
            "rationale",
            "statement",
            "proposition",
            "text",
            "consequence",
            "identity_criteria",
            "location_ref",
        ):
            candidate = value.get(field)
            if candidate not in (None, "", [], {}):
                return _reader_value(
                    candidate,
                    _canonical_child(path, field),
                    aliases,
                )
        return ReaderValue("", ())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        rendered = [
            _reader_value(item, f"{path}[{index}]", aliases)
            for index, item in enumerate(value)
            if item not in (None, "", [], {})
        ]
        return ReaderValue(
            "、".join(item.text for item in rendered if item.text),
            tuple(
                dict.fromkeys(
                    source_path
                    for item in rendered
                    for source_path in item.exact_source_paths
                )
            ),
        )
    source_paths = (
        (path,)
        if path and value not in (None, "")
        else ()
    )
    return ReaderValue(_public_scalar(value, aliases), source_paths)


def _reader_values(value: Any, aliases: Mapping[str, str]) -> str:
    return _reader_value(value, "", aliases).text


def _reader_fragment(
    text: str,
    *values: ReaderValue,
    source_paths: Sequence[str] = (),
) -> ReaderFragment:
    return ReaderFragment(
        text=text,
        exact_source_paths=tuple(
            dict.fromkeys(
                [
                    path
                    for value in values
                    for path in value.exact_source_paths
                ]
                + list(source_paths)
            )
        ),
    )


def _reader_unit(
    unit_id: str,
    unit_kind: str,
    heading: str,
    fragments: Sequence[ReaderFragment],
    *,
    atom_statuses: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any] | None:
    merged: dict[str, list[str]] = {}
    for fragment in fragments:
        text = fragment.text.strip()
        if not text:
            continue
        paths = merged.setdefault(text, [])
        paths.extend(
            path for path in fragment.exact_source_paths if path not in paths
        )
    if not merged:
        return None
    fragment_traces = [
        {"text": text, "exact_source_paths": paths}
        for text, paths in merged.items()
    ]
    return {
        "unit_id": unit_id,
        "unit_kind": unit_kind,
        "heading": heading,
        "fragments": list(merged),
        "fragment_traces": fragment_traces,
        "required_outputs": ["answer"],
        "atom_statuses": [dict(status) for status in atom_statuses],
        "source_paths": list(
            dict.fromkeys(
                path
                for fragment in fragment_traces
                for path in fragment["exact_source_paths"]
            )
        ),
    }


def _identity_value(
    value: Any,
    path: str,
    aliases: Mapping[str, str],
) -> ReaderValue:
    if not isinstance(value, Mapping):
        return _reader_value(value, path, aliases)
    location = _reader_value(
        value.get("location_ref"),
        _canonical_child(path, "location_ref"),
        aliases,
    )
    criterion = _reader_value(
        value.get("identity_criteria"),
        _canonical_child(path, "identity_criteria"),
        aliases,
    )
    if location.text and criterion.text:
        text = f"{location.text}（按“{criterion.text}”识别）"
    else:
        text = location.text or criterion.text
    return ReaderValue(
        text,
        tuple(dict.fromkeys(location.exact_source_paths + criterion.exact_source_paths)),
    )


def reader_projection_units(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Select decision-relevant relation sentences from the complete typed atom ledger."""

    sanitized = redact_payload_for_delivery(payload)
    if sanitized.get("dynamic_applicability") == "not_applicable":
        return []
    aliases = _alias_book(sanitized)
    units: list[dict[str, Any]] = []

    world = sanitized.get("local_world_model")
    if isinstance(world, Mapping):
        fragments: list[ReaderFragment] = []
        boundary = world.get("object_boundary")
        if isinstance(boundary, Mapping):
            base = "local_world_model.object_boundary"
            objects = _reader_value(
                boundary.get("object_ids"), f"{base}.object_ids", aliases
            )
            rule = _reader_value(
                boundary.get("boundary_rule"), f"{base}.boundary_rule", aliases
            )
            if objects.text or rule.text:
                fragments.append(
                    _reader_fragment(
                        f"本题把{objects.text or '已声明对象'}纳入局部世界，"
                        f"边界按“{rule.text or '已声明规则'}”划定。",
                        objects,
                        rule,
                    )
                )
        for index, relation in enumerate(world.get("containment_relations", [])):
            if not isinstance(relation, Mapping):
                continue
            base = f"local_world_model.containment_relations[{index}]"
            child = _reader_value(
                relation.get("child_circle_id"), f"{base}.child_circle_id", aliases
            )
            parent = _reader_value(
                relation.get("parent_circle_id"), f"{base}.parent_circle_id", aliases
            )
            basis = _reader_value(relation.get("basis"), f"{base}.basis", aliases)
            fragments.append(
                _reader_fragment(
                    f"{child.text or '子圈层'}由{parent.text or '上位圈层'}承接，"
                    f"依据是{basis.text or '已登记关系'}。",
                    child,
                    parent,
                    basis,
                )
            )
        for index, relation in enumerate(world.get("circle_relations", [])):
            if not isinstance(relation, Mapping):
                continue
            base = f"local_world_model.circle_relations[{index}]"
            source = _reader_value(
                relation.get("source_circle_ref"), f"{base}.source_circle_ref", aliases
            )
            target = _reader_value(
                relation.get("target_circle_ref"), f"{base}.target_circle_ref", aliases
            )
            relation_type = _reader_value(
                relation.get("relation_type"), f"{base}.relation_type", aliases
            )
            direction = _reader_value(
                relation.get("direction"), f"{base}.direction", aliases
            )
            fragments.append(
                _reader_fragment(
                    f"{source.text or '起点圈层'}以{relation_type.text or '已登记关系'}"
                    f"{('、方向为' + direction.text) if direction.text else ''}"
                    f"指向{target.text or '目标圈层'}。",
                    source,
                    target,
                    relation_type,
                    direction,
                )
            )
        for index, channel in enumerate(world.get("channels", [])):
            if not isinstance(channel, Mapping):
                continue
            base = f"local_world_model.channels[{index}]"
            source = _reader_value(
                channel.get("from_position_id"), f"{base}.from_position_id", aliases
            )
            target = _reader_value(
                channel.get("to_position_id"), f"{base}.to_position_id", aliases
            )
            active = channel.get("active")
            active_value = _reader_value(active, f"{base}.active", aliases)
            state = "开放" if active is True else "关闭" if active is False else "状态未定"
            details: list[str] = []
            detail_values: list[ReaderValue] = []
            for field, label in (
                ("capacity", "容量"),
                ("delay", "时延"),
                ("threshold", "门槛"),
            ):
                if field in channel:
                    value = _reader_value(channel.get(field), f"{base}.{field}", aliases)
                    details.append(f"{label}为{value.text}")
                    detail_values.append(value)
            suffix = f"，{'，'.join(details)}" if details else ""
            fragments.append(
                _reader_fragment(
                    f"现实通道从{source.text or '已登记起点'}通往"
                    f"{target.text or '已登记终点'}，当前{state}{suffix}。",
                    source,
                    target,
                    active_value,
                    *detail_values,
                )
            )
            acl = channel.get("acl")
            if isinstance(acl, Mapping):
                acl_base = f"{base}.acl"
                authorized_positions = _reader_value(
                    acl.get("authorized_position_ids"),
                    f"{acl_base}.authorized_position_ids",
                    aliases,
                )
                authorization_evidence = _reader_value(
                    acl.get("authorization_evidence_refs"),
                    f"{acl_base}.authorization_evidence_refs",
                    aliases,
                )
                scope = acl.get("authorization_scope")
                if isinstance(scope, Mapping):
                    scope_base = f"{acl_base}.authorization_scope"
                    subject = _reader_value(
                        scope.get("decision_subject"),
                        f"{scope_base}.decision_subject",
                        aliases,
                    )
                    target_object = _reader_value(
                        scope.get("target_object"),
                        f"{scope_base}.target_object",
                        aliases,
                    )
                    action = _reader_value(
                        scope.get("single_action"),
                        f"{scope_base}.single_action",
                        aliases,
                    )
                    territory = _reader_value(
                        scope.get("territory"),
                        f"{scope_base}.territory",
                        aliases,
                    )
                    interval = scope.get("validity_interval")
                    starts_at = _reader_value(
                        (
                            interval.get("starts_at")
                            if isinstance(interval, Mapping)
                            else None
                        ),
                        f"{scope_base}.validity_interval.starts_at",
                        aliases,
                    )
                    ends_at = _reader_value(
                        (
                            interval.get("ends_at")
                            if isinstance(interval, Mapping)
                            else None
                        ),
                        f"{scope_base}.validity_interval.ends_at",
                        aliases,
                    )
                    fragments.append(
                        _reader_fragment(
                            f"该通道仅向{authorized_positions.text or '已登记位置'}开放，"
                            f"授权依据为{authorization_evidence.text or '已登记授权证据'}；"
                            f"仅允许{subject.text or '已登记主体'}对"
                            f"{target_object.text or '已登记对象'}执行"
                            f"{action.text or '已登记单一动作'}，"
                            f"地域限于{territory.text or '已登记范围'}，"
                            f"有效期自{starts_at.text or '已登记开始时间'}至"
                            f"{ends_at.text or '已登记结束时间'}。",
                            authorized_positions,
                            authorization_evidence,
                            subject,
                            target_object,
                            action,
                            territory,
                            starts_at,
                            ends_at,
                        )
                    )
        for field, prefix in (
            ("unknowns", "仍未知"),
            ("residuals", "仍未解释的残差"),
            ("local_distributions", "必须保留的局部代价或分布"),
        ):
            for index, record in enumerate(world.get(field, [])):
                value = _reader_value(
                    record,
                    f"local_world_model.{field}[{index}]",
                    aliases,
                )
                if value.text:
                    fragments.append(
                        _reader_fragment(f"{prefix}：{value.text}。", value)
                    )
        unit = _reader_unit(
            "reader.world-relations",
            "local_world_relations",
            "局部世界中的对象、圈层与现实通道",
            fragments,
        )
        if unit is not None:
            units.append(unit)

    ledger = sanitized.get("transformation_ledger")
    transformations = ledger.get("transformations", []) if isinstance(ledger, Mapping) else []
    for index, transformation in enumerate(transformations):
        if not isinstance(transformation, Mapping):
            continue
        base = f"transformation_ledger.transformations[{index}]"
        kind = _reader_value(transformation.get("kind"), f"{base}.kind", aliases)
        source = _identity_value(
            transformation.get("input_identity"), f"{base}.input_identity", aliases
        )
        target = _identity_value(
            transformation.get("output_identity"), f"{base}.output_identity", aliases
        )
        preserved = _reader_value(
            transformation.get("preserved"), f"{base}.preserved", aliases
        )
        changed = _reader_value(
            transformation.get("changed"), f"{base}.changed", aliases
        )
        omitted = _reader_value(
            transformation.get("omitted"), f"{base}.omitted", aliases
        )
        unknown = _reader_value(
            transformation.get("unknown"), f"{base}.unknown", aliases
        )
        losses = _reader_value(
            transformation.get("task_relative_losses"),
            f"{base}.task_relative_losses",
            aliases,
        )
        returns = _reader_value(
            transformation.get("return_conditions"),
            f"{base}.return_conditions",
            aliases,
        )
        closure_field = (
            "closure_status" if "closure_status" in transformation else "closed"
        )
        closure = _reader_value(
            transformation.get(closure_field), f"{base}.{closure_field}", aliases
        )
        fragments = [
            _reader_fragment(
                f"这条{kind.text or '结构变换'}把{source.text or '已登记输入'}"
                f"转到{target.text or '已登记输出'}；"
                f"保留{preserved.text or '尚未声明'}，改变{changed.text or '尚未声明'}，"
                f"遗漏{omitted.text or '无已登记项'}，未知{unknown.text or '无已登记项'}；"
                f"任务相对损失是{losses.text or '尚未记录'}，"
                f"闭合状态为{closure.text or '尚未记录'}；"
                f"需要回到源材料的条件是{returns.text or '身份或证据不再成立'}。",
                kind,
                source,
                target,
                preserved,
                changed,
                omitted,
                unknown,
                losses,
                closure,
                returns,
            )
        ]
        unit = _reader_unit(
            f"reader.transformation.{index + 1}",
            "transformation_relation",
            f"第 {index + 1} 条尺度、圈层或表示变换",
            fragments,
        )
        if unit is not None:
            units.append(unit)

    graph = sanitized.get("claim_mechanism_graph")
    explanations = graph.get("explanations", []) if isinstance(graph, Mapping) else []
    mechanism_names: dict[Any, tuple[ReaderValue, ReaderValue]] = {}
    for mechanism_index, record in enumerate(
        graph.get("mechanisms", []) if isinstance(graph, Mapping) else []
    ):
        if not isinstance(record, Mapping):
            continue
        base = f"claim_mechanism_graph.mechanisms[{mechanism_index}]"
        identifier = record.get("mechanism_id")
        mechanism_names[identifier] = (
            _reader_value(record.get("name"), f"{base}.name", aliases),
            _reader_value(identifier, f"{base}.mechanism_id", aliases),
        )
    for index, explanation in enumerate(explanations):
        if not isinstance(explanation, Mapping):
            continue
        base = f"claim_mechanism_graph.explanations[{index}]"
        kind = _reader_value(explanation.get("kind"), f"{base}.kind", aliases)
        rationale = _reader_value(
            explanation.get("rationale"), f"{base}.rationale", aliases
        )
        mechanism_values: list[ReaderValue] = []
        mechanism_link_values: list[ReaderValue] = []
        mechanism_texts: list[str] = []
        for mechanism_index, identifier in enumerate(
            explanation.get("mechanism_ids", [])
        ):
            name, record_identifier = mechanism_names.get(
                identifier,
                (ReaderValue(_public_scalar(identifier, aliases), ()), ReaderValue("", ())),
            )
            link_identifier = _reader_value(
                identifier,
                f"{base}.mechanism_ids[{mechanism_index}]",
                aliases,
            )
            mechanism_values.extend((name, record_identifier))
            mechanism_link_values.append(link_identifier)
            mechanism_texts.append(name.text or _public_scalar(identifier, aliases))
        mechanisms = "、".join(mechanism_texts)
        residuals = _reader_value(
            explanation.get("residual_ids"), f"{base}.residual_ids", aliases
        )
        sentence = f"{kind.text or f'解释 {index + 1}'}认为：{rationale.text or '当前只保留条件性说明'}"
        if mechanisms:
            sentence += f"；它依赖{mechanisms}"
        if residuals.text:
            sentence += f"；尚未解释的部分是{residuals.text}"
        unit = _reader_unit(
            f"reader.explanation.{index + 1}",
            "competing_explanation_relation",
            f"竞争解释 {index + 1}",
            [
                _reader_fragment(
                    sentence + "。",
                    kind,
                    rationale,
                    residuals,
                    *mechanism_values,
                    *mechanism_link_values,
                )
            ],
        )
        if unit is not None:
            units.append(unit)

    verdict = sanitized.get("verdict")
    five_verdicts = verdict.get("five_verdicts", []) if isinstance(verdict, Mapping) else []
    for index, record in enumerate(five_verdicts):
        if not isinstance(record, Mapping):
            continue
        base = f"verdict.five_verdicts[{index}]"
        kind = _reader_value(record.get("kind"), f"{base}.kind", aliases)
        proposition = _reader_value(
            record.get("proposition"), f"{base}.proposition", aliases
        )
        status = _reader_value(record.get("status"), f"{base}.status", aliases)
        used_values = [kind, proposition, status]
        sentence = (
            f"{kind.text or '裁决'}的命题是“{proposition.text or '尚未形成'}”，"
            f"当前状态为{status.text or '未定'}"
        )
        scope = record.get("authorization_scope")
        if isinstance(scope, Mapping):
            scope_base = f"{base}.authorization_scope"
            subject = _reader_value(
                scope.get("decision_subject"), f"{scope_base}.decision_subject", aliases
            )
            target = _reader_value(
                scope.get("target_object"), f"{scope_base}.target_object", aliases
            )
            action = _reader_value(
                scope.get("single_action"), f"{scope_base}.single_action", aliases
            )
            territory = _reader_value(
                scope.get("territory"), f"{scope_base}.territory", aliases
            )
            validity = scope.get("validity_interval")
            validity_text = _reader_value(
                validity, f"{scope_base}.validity_interval", aliases
            )
            used_values.extend((subject, target, action, territory, validity_text))
            sentence += (
                f"；授权仅限{subject.text or '已登记主体'}对{target.text or '已登记对象'}执行"
                f"{action.text or '已登记单一动作'}，地域为{territory.text or '已登记范围'}，"
                f"有效期为{validity_text.text or '已登记期间'}"
            )
        unit = _reader_unit(
            f"reader.verdict.{index + 1}",
            "verdict_relation",
            f"第 {index + 1} 类裁决",
            [_reader_fragment(sentence + "。", *used_values)],
        )
        if unit is not None:
            units.append(unit)

    forecast = sanitized.get("forecast")
    if isinstance(forecast, Mapping):
        target = _reader_value(forecast.get("target"), "forecast.target", aliases)
        deadline = _reader_value(
            forecast.get("deadline"), "forecast.deadline", aliases
        )
        baseline = _reader_value(
            forecast.get("baseline"), "forecast.baseline", aliases
        )
        paths = _reader_value(
            forecast.get("conditional_paths"), "forecast.conditional_paths", aliases
        )
        early = _reader_value(
            forecast.get("early_signals"), "forecast.early_signals", aliases
        )
        reverse = _reader_value(
            forecast.get("reverse_signals"), "forecast.reverse_signals", aliases
        )
        probability = forecast.get("numeric_probability")
        probability_value = _reader_value(
            probability, "forecast.numeric_probability", aliases
        )
        calibration = _reader_value(
            forecast.get("calibration_basis"), "forecast.calibration_basis", aliases
        )
        sentence = (
            f"前瞻对象是{target.text or '已登记目标'}，观察到{deadline.text or '已登记截止点'}；"
            f"简单基线是{baseline.text or '尚未记录'}，条件路径是{paths.text or '尚未记录'}；"
            f"早期信号为{early.text or '尚未记录'}，反向信号为{reverse.text or '尚未记录'}"
        )
        if isinstance(probability, (int, float)):
            sentence += (
                f"；条件概率为{probability}，校准依据是{calibration.text or '缺失'}"
            )
        unit = _reader_unit(
            "reader.forecast",
            "forecast_relation",
            "条件前瞻",
            [
                _reader_fragment(
                    sentence + "。",
                    target,
                    deadline,
                    baseline,
                    paths,
                    early,
                    reverse,
                    probability_value,
                    calibration,
                )
            ],
        )
        if unit is not None:
            units.append(unit)

    lineage = sanitized.get("recursive_lineage")
    states = sanitized.get("recursive_states")
    state_values = (
        [states[key] for key in sorted(states, key=str)]
        if isinstance(states, Mapping)
        else []
    )
    state_by_node = {
        state.get("node_id"): state
        for state in state_values
        if isinstance(state, Mapping)
    }
    state_prefix_by_node = {
        state.get("node_id"): f"recursive_states[{index}]"
        for index, state in enumerate(state_values)
        if isinstance(state, Mapping)
    }
    branches = lineage.get("branches", []) if isinstance(lineage, Mapping) else []
    for index, branch in enumerate(branches):
        if not isinstance(branch, Mapping):
            continue
        branch_base = f"recursive_lineage.branches[{index}]"
        kind = _reader_value(branch.get("kind"), f"{branch_base}.kind", aliases)
        status = _reader_value(
            branch.get("status"), f"{branch_base}.status", aliases
        )
        fragments = [
            _reader_fragment(
                f"{kind.text or f'分支 {index + 1}'}当前为{status.text or '未定'}。",
                kind,
                status,
            )
        ]
        for node_index, node_id in enumerate(branch.get("node_ids", [])):
            state = state_by_node.get(node_id)
            if not isinstance(state, Mapping):
                continue
            state_base = state_prefix_by_node[node_id]
            order = _reader_value(state.get("order"), f"{state_base}.order", aliases)
            input_state = _reader_value(
                state.get("input_state"), f"{state_base}.input_state", aliases
            )
            delta = _reader_value(
                state.get("state_delta"), f"{state_base}.state_delta", aliases
            )
            carrier = _reader_value(
                state.get("carrier"), f"{state_base}.carrier", aliases
            )
            location = _reader_value(
                state.get("scale_or_circle"), f"{state_base}.scale_or_circle", aliases
            )
            clock = _reader_value(state.get("clock"), f"{state_base}.clock", aliases)
            conditions = _reader_value(
                state.get("conditions"), f"{state_base}.conditions", aliases
            )
            failure = _reader_value(
                state.get("failure_condition"),
                f"{state_base}.failure_condition",
                aliases,
            )
            early = _reader_value(
                state.get("early_signal"), f"{state_base}.early_signal", aliases
            )
            reverse = _reader_value(
                state.get("reverse_signal"), f"{state_base}.reverse_signal", aliases
            )
            writeback = _reader_value(
                state.get("writeback"), f"{state_base}.writeback", aliases
            )
            evidence_grade = _reader_value(
                state.get("declared_evidence_grade"),
                f"{state_base}.declared_evidence_grade",
                aliases,
            )
            evidence_clause = (
                f"，证据等级为{evidence_grade.text}" if evidence_grade.text else ""
            )
            branch_node_ref = _reader_value(
                node_id,
                f"{branch_base}.node_ids[{node_index}]",
                aliases,
            )
            state_node_ref = _reader_value(
                state.get("node_id"), f"{state_base}.node_id", aliases
            )
            fragments.append(
                _reader_fragment(
                    f"第{order.text or '当前'}阶从{input_state.text or '已登记输入状态'}出发，"
                    f"经{carrier.text or '已登记载体'}在{location.text or '已登记范围'}、"
                    f"{clock.text or '已登记时钟'}上产生{delta.text or '已登记变化'}"
                    f"{evidence_clause}；"
                    f"成立条件是{conditions.text or '尚未记录'}，"
                    f"失败条件是{failure.text or '尚未记录'}，"
                    f"早期信号是{early.text or '尚未记录'}，"
                    f"反向信号是{reverse.text or '尚未记录'}，"
                    f"写回是{writeback.text or '尚未记录'}。",
                    branch_node_ref,
                    state_node_ref,
                    order,
                    input_state,
                    delta,
                    carrier,
                    location,
                    clock,
                    conditions,
                    failure,
                    early,
                    reverse,
                    writeback,
                    evidence_grade,
                )
            )
        stop_reason = _reader_value(
            branch.get("stop_reason"), f"{branch_base}.stop_reason", aliases
        )
        if stop_reason.text:
            fragments.append(
                _reader_fragment(
                    f"这条分支在此停止，因为{stop_reason.text}。", stop_reason
                )
            )
        unit = _reader_unit(
            f"reader.recursive-branch.{index + 1}",
            "recursive_relation",
            f"递进分支 {index + 1}",
            fragments,
        )
        if unit is not None:
            units.append(unit)

    statuses = []
    visibility = _visibility_entries(payload)
    for path in semantic_atom_paths(payload):
        entry = visibility.get(path, {})
        classification = str(entry.get("classification", "public"))
        disclosure = str(entry.get("disclosure", "include"))
        statuses.append(
            {
                "canonical_path": path,
                "visibility": classification,
                "projection_status": (
                    "withheld_for_protection"
                    if disclosure == "withhold"
                    else "audit_only"
                ),
            }
        )
    withheld = [
        status
        for status in statuses
        if status["projection_status"] == "withheld_for_protection"
    ]
    if withheld:
        unit = _reader_unit(
            "reader.privacy-boundary",
            "privacy_boundary",
            "隐私与披露边界",
            [
                _reader_fragment(
                    f"本次有 {len(withheld)} 个语义单元按既定用途为保护而不公开；"
                    "其原值没有进入任何交付。",
                    source_paths=[status["canonical_path"] for status in withheld],
                )
            ],
            atom_statuses=withheld,
        )
        if unit is not None:
            units.append(unit)
    return units


def render_semantic_projection(payload: Mapping[str, Any]) -> str:
    """Render decision-relevant relation sentences without dumping the atom ledger."""

    chunks: list[str] = []
    for unit in reader_projection_units(payload):
        body = "\n\n".join(unit["fragments"])
        chunks.append(f"### {unit['heading']}\n\n{body}")
    return "\n\n".join(chunks)


__all__ = (
    "INTERNAL_ID_TOKEN",
    "redact_payload_for_delivery",
    "protected_retrieval_values",
    "reader_projection_units",
    "render_semantic_projection",
    "semantic_atom_paths",
    "semantic_fragments",
    "semantic_projection_units",
    "typed_semantic_atoms",
    "validate_visibility_ledger",
)
