"""Plain-language answer, dossier, atlas, and casebook materialization."""

from __future__ import annotations

from hashlib import sha256
import re
from pathlib import Path
from typing import Any

from .canonical_json import atomic_write_text, sha256_file
from .contracts import DYNAMIC_PHASE_FIELDS
from .retrieval import _normalise_lineage_token
from .semantic_projection import (
    INTERNAL_ID_TOKEN,
    authored_reader_units,
    redact_payload_for_delivery,
    validate_reader_sections,
)


MACHINE_TOKENS = (
    "schema_version",
    "record_sha256",
    "predecessor_sha256",
    "validator_set_sha256",
    "artifact_sha256",
)
PHASE_TOKEN = re.compile(r"(?<![A-Za-z0-9_-])XK(?:[0-9]|1[0-2])(?![A-Za-z0-9_-])", re.IGNORECASE)
CONCEPT_TOKEN = re.compile(
    r"(?<![A-Za-z0-9_-])(?:V[0-9]+|XK-PROV)-[A-Za-z0-9-]+(?![A-Za-z0-9_-])",
    re.IGNORECASE,
)
HOST_CAPTURE_ID_TOKEN = re.compile(
    r"(?<![A-Za-z0-9_-])CAPTURE-WEB-[A-Za-z0-9_.:-]+(?![A-Za-z0-9_.:-])",
    re.IGNORECASE,
)
HOST_CAPTURE_FIELD_TOKEN = re.compile(r"\bcapture_id\b", re.IGNORECASE)
INTERNAL_ID_TOKEN_CASEFOLD = re.compile(INTERNAL_ID_TOKEN.pattern, re.IGNORECASE)
HEX_DIGEST_TOKEN = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{64}(?![0-9A-Fa-f])")
MACHINE_FIELD_TOKEN = re.compile(
    r"\b(?:schema_id|[a-z][a-z0-9_]*(?:_sha256|_hash)|(?:sha256|hash)_[a-z0-9_]+)\b",
    re.IGNORECASE,
)
MACHINE_HASH_LABEL = re.compile(r"\b(?:sha-?256|hash)\b\s*[:=]", re.IGNORECASE)
CONCEPT_WALL_SPLIT = re.compile(r"[、，,；;|/\n]+")
CONCEPT_LIKE_ENDING = re.compile(
    r"(?:性|化|机制|结构|尺度|模型|系统|效应|反馈|闭环|耦合|转移|映射|投影|"
    r"解离|治理|权力|主体|递归|回流|承接|势场|封闭)$"
)
EXPLANATION_CUE = re.compile(
    r"(?:也就是|是指|意味着|例如|比如|因为|所以|如果|那么|通过|导致|使得|"
    r"表现为|具体来说|换句话说|：|:)"
)
CASE_LABELS = {
    "documented_real_case": "有记录的现实案例",
    "documented-real": "有记录的现实案例",
    "user_material_case": "用户提供的案例",
    "conditional_scenario": "条件情景",
    "conditional-scenario": "条件情景",
    "structural_analogy": "结构类比",
}
EVIDENCE_IDENTITY_LABELS = {
    "observed": "直接观察",
    "reported": "来源报告",
    "inferred-from-material": "基于材料的推断",
    "competing-explanation": "竞争解释",
    "user-claim": "用户陈述",
    "model-candidate": "模型候选",
    "simulated-result": "模拟结果，不是现实事实",
    "unknown": "未知",
}
ORDER_LABELS = {1: "一阶", 2: "二阶", 3: "三阶"}
USER_DELIVERY_ARTIFACTS = (
    ("主答案", "delivery/xi-kari-answer.md"),
    ("判断底稿", "delivery/xi-kari-dossier.md"),
    ("概念图谱", "delivery/xi-kari-concept-atlas.md"),
    ("案例与反例册", "delivery/xi-kari-case-and-countercase.md"),
)


def _public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized = redact_payload_for_delivery(payload)
    if sanitized.get("dynamic_applicability") != "not_applicable":
        return sanitized
    for field in DYNAMIC_PHASE_FIELDS:
        sanitized.pop(field, None)
    return sanitized


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _plain(value: Any, fallback: str = "未写明") -> str:
    if isinstance(value, str) and value.strip():
        stripped = value.strip()
        if INTERNAL_ID_TOKEN.fullmatch(stripped):
            prefix = stripped.split("-", maxsplit=1)[0]
            return {
                "POS": "已记录的受影响位置",
                "CLOCK": "已记录的运行时钟",
                "CIRCLE": "已记录的局部圈层",
            }.get(prefix, fallback)
        return stripped
    if isinstance(value, dict):
        for field in (
            "text",
            "summary",
            "description",
            "claim",
            "proposition",
            "statement",
            "change",
            "state_delta",
        ):
            candidate = value.get(field)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    return fallback


def _plain_source_identity(value: Any) -> str:
    rendered = _plain(value, "未标明来源身份")
    if INTERNAL_ID_TOKEN_CASEFOLD.search(rendered):
        return rendered.replace("-", " ")
    return rendered


def _fragment(value: Any, fallback: str = "未写明") -> str:
    return _plain(value, fallback).rstrip("。；;，, ")


def _joined(values: Any, *, fallback: str = "未写明") -> str:
    rendered = [_fragment(value, "") for value in _list(values)]
    rendered = [value for value in rendered if value]
    return "；".join(rendered) if rendered else fallback


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def _items(values: Any, *, fallback: str = "暂无。") -> str:
    if not values:
        return fallback
    rendered: list[str] = []
    for value in values:
        if isinstance(value, dict):
            value = value.get("text", value.get("summary", value.get("description", "未写明。")))
        rendered.append(f"- {value}")
    return "\n".join(rendered)


def _source_relation_lookup(sources: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    candidates: dict[str, list[dict[str, Any]]] = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        for reference in (source.get("source_id"), source.get("url")):
            token = _normalise_lineage_token(reference)
            if token is not None:
                candidates.setdefault(token, []).append(source)
    return {
        token: matches[0]
        for token, matches in candidates.items()
        if len(matches) == 1
    }


def _source_relation_titles(
    refs: Any,
    source_by_id: dict[str, dict[str, Any]],
    relation_by_token: dict[str, dict[str, Any]],
) -> list[str]:
    titles: list[str] = []
    for reference in _list(refs):
        source = source_by_id.get(reference) if isinstance(reference, str) else None
        if source is None:
            token = _normalise_lineage_token(reference)
            source = relation_by_token.get(token) if token is not None else None
        if source is not None:
            titles.append(_plain(source.get("title"), "未命名来源"))
    return _dedupe(titles)


def _source_label(source: dict[str, Any]) -> str:
    title = _plain(source.get("title"), "未命名来源")
    url = source.get("url")
    return (
        f"[{title}]({url})"
        if isinstance(url, str) and url.startswith(("https://", "http://"))
        else title
    )


def _reader_mechanisms(payload: dict[str, Any]) -> list[dict[str, Any]]:
    explicit = [item for item in _list(payload.get("mechanisms")) if isinstance(item, dict)]
    graph = payload.get("claim_mechanism_graph", {})
    derived = []
    if isinstance(graph, dict):
        for mechanism in _list(graph.get("mechanisms")):
            if not isinstance(mechanism, dict):
                continue
            derived.append(
                {
                    "name": mechanism.get("name"),
                    "explanation": (
                        f"从“{_plain(mechanism.get('input_state'))}”出发，经由"
                        f"“{_plain(mechanism.get('channel'))}”使状态变为“{_plain(mechanism.get('output_state'))}”。"
                    ),
                    "conditions": mechanism.get("conditions", []),
                    "countermechanism": mechanism.get("countermechanism"),
                    "failure_condition": mechanism.get("failure_condition"),
                }
            )
    if len(derived) >= 2:
        return derived
    if len(explicit) >= 2:
        return explicit
    combined = explicit + [item for item in derived if item not in explicit]
    return combined


def _case_records(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ledger = payload.get("case_ledger", {})
    cases = [item for item in _list(ledger.get("cases") if isinstance(ledger, dict) else None) if isinstance(item, dict)]
    countercases = [
        item
        for item in _list(ledger.get("countercases") if isinstance(ledger, dict) else None)
        if isinstance(item, dict)
    ]
    if not cases:
        cases = [item for item in _list(payload.get("cases")) if isinstance(item, dict)]
    return cases, countercases


def _normalized_order(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "order": value.get("order"),
        "status": value.get("status", "conditional"),
        "input_state": value.get("input_state", "上一阶已满足的局部状态"),
        "change": value.get("state_delta", value.get("change")),
        "carrier": value.get("carrier", value.get("channel")),
        "scale_or_circle": value.get("scale_or_circle", value.get("scale", "本题局部范围")),
        "clock": value.get("clock", "本题时间窗"),
        "conditions": value.get("conditions", []),
        "evidence_identity": value.get("evidence_identity", "条件推断"),
        "countermechanism": value.get("countermechanism", "竞争机制仍可能阻断这一路径"),
        "failure_condition": value.get("failure_condition", value.get("stop_condition")),
        "early_signal": value.get("early_signal", value.get("early_signals", [])),
        "reverse_signal": value.get("reverse_signal", value.get("reverse_signals", [])),
        "writeback": value.get("writeback", "新观察进入下一轮判断"),
        "stop_reason": value.get("stop_reason"),
    }


def _reader_order_path(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    lineage = payload.get("recursive_lineage")
    states = payload.get("recursive_states")
    if isinstance(lineage, dict) and isinstance(states, dict):
        branches = [item for item in _list(lineage.get("branches")) if isinstance(item, dict)]
        branch = next((item for item in branches if item.get("kind") == "main"), None)
        state_by_node = {
            item.get("node_id"): item
            for item in states.values()
            if isinstance(item, dict) and item.get("node_id")
        }
        if branch is not None:
            path = [
                _normalized_order(state_by_node[node_id])
                for node_id in _list(branch.get("node_ids"))
                if node_id in state_by_node
            ]
            path.sort(key=lambda item: item.get("order") or 99)
            stop_reason = branch.get("stop_reason")
            for item in path:
                if item.get("status") == "stopped":
                    stop_reason = item.get("stop_reason") or stop_reason or "上一阶路径已经失败"
                    break
            return path, _plain(stop_reason, "") or None
    path = [_normalized_order(item) for item in _list(payload.get("orders")) if isinstance(item, dict)]
    path.sort(key=lambda item: item.get("order") or 99)
    stop_reason = next(
        (_plain(item.get("stop_reason"), "") for item in path if item.get("status") == "stopped"),
        "",
    )
    return path, stop_reason or None


def _order_text(payload: dict[str, Any]) -> str:
    if payload.get("dynamic_applicability") == "not_applicable":
        reason = _plain(payload.get("not_applicable_reason"), "没有真实动态载体或连续状态链")
        return f"**三阶推演不适用。** {reason}"
    path, stop_reason = _reader_order_path(payload)
    by_order = {item.get("order"): item for item in path if item.get("order") in ORDER_LABELS}
    order_evaluation = payload.get("order_evaluation", {})
    evaluation_by_order = {
        item.get("order"): item
        for item in _list(
            order_evaluation.get("orders")
            if isinstance(order_evaluation, dict)
            else []
        )
        if isinstance(item, dict) and item.get("order") in ORDER_LABELS
    }
    chunks: list[str] = []
    stopped = False
    for order in (1, 2, 3):
        label = ORDER_LABELS[order]
        item = by_order.get(order)
        if stopped or item is None:
            reason = stop_reason or "当前证据没有建立连续到这一阶的合法路径"
            chunks.append(f"### {label}：未运行\n\n{reason}；不补写后续故事。")
            stopped = True
            continue
        evaluation = evaluation_by_order.get(order, {})
        evaluation_text = ""
        if evaluation:
            local_predictability = evaluation.get("local_predictability")
            local_predictability_line = (
                f"\n- 局部可预测性：{_fragment(local_predictability)}"
                if local_predictability
                else ""
            )
            evaluation_text = (
                f"\n- 简单基线：{_fragment(evaluation.get('baseline'))}"
                f"\n- 解释增量：{_fragment(evaluation.get('explanatory_increment'))}"
                f"\n- 预测增量：{_fragment(evaluation.get('predictive_increment'))}"
                f"\n- 新增假设：{_joined(evaluation.get('new_assumptions'))}"
                f"\n- 新增损失：{_joined(evaluation.get('new_losses'))}"
                f"{local_predictability_line}"
                f"\n- 继续递归价值：{_fragment(evaluation.get('continue_value'))}"
            )
        chunks.append(
            f"### {label}：{_plain(item.get('change'), '状态变化未写明')}\n\n"
            f"- 起点：{_plain(item.get('input_state'))}\n"
            f"- 载体或通道：{_plain(item.get('carrier'))}\n"
            f"- 范围与时钟：{_plain(item.get('scale_or_circle'))}；{_plain(item.get('clock'))}\n"
            f"- 成立条件：{_joined(item.get('conditions'))}\n"
            f"- 证据边界：{EVIDENCE_IDENTITY_LABELS.get(item.get('evidence_identity'), _plain(item.get('evidence_identity'), '条件推断'))}\n"
            f"- 竞争机制：{_plain(item.get('countermechanism'))}\n"
            f"- 失败条件：{_plain(item.get('failure_condition'))}\n"
            f"- 早期信号：{_joined(item.get('early_signal'))}\n"
            f"- 反向信号：{_joined(item.get('reverse_signal'))}\n"
            f"- 如何写回：{_plain(item.get('writeback'))}"
            f"{evaluation_text}"
        )
        if item.get("status") == "stopped":
            stopped = True
            stop_reason = _plain(item.get("stop_reason"), stop_reason or "这一阶路径已经失败")
    return "\n\n".join(chunks)


def _selected_stance_pair(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], bool]:
    stance = (
        payload.get("stance_pair")
        if isinstance(payload.get("stance_pair"), dict)
        else {}
    )
    position = stance.get("position") if isinstance(stance, dict) else None
    counterposition = (
        stance.get("counterposition") if isinstance(stance, dict) else None
    )
    position = position if isinstance(position, dict) else {}
    counterposition = counterposition if isinstance(counterposition, dict) else {}
    preferred = stance.get("preferred") if isinstance(stance, dict) else None
    if preferred == "counterposition":
        return counterposition, position, False
    if preferred == "position":
        return position, counterposition, False
    answer = payload.get("answer", {})
    direct_answer = answer.get("direct_answer") if isinstance(answer, dict) else None
    alternatives = _dedupe(
        [
            _plain(position.get("claim"), ""),
            _plain(counterposition.get("claim"), ""),
        ]
    )
    return (
        {"claim": direct_answer},
        {"claim": "；另一立场：".join(alternatives), "limits": []},
        True,
    )


def _source_lines(
    sources: list[dict[str, Any]], assessments: list[dict[str, Any]] | None = None
) -> str:
    if not sources:
        return "- 本次没有使用外部或用户材料来源；现实性主张因此保持有限。"
    lines: list[str] = []
    origin_labels = {
        "external": "外部材料",
        "user": "用户材料",
        "user_material": "用户材料",
        "provided": "给定材料",
        "v8.3": "v8.3 源材料",
    }
    verdict_labels = {
        "admitted": "暂时采用",
        "usable": "可用",
        "usable_with_limits": "有边界地可用",
        "conflicted": "存在冲突",
        "insufficient": "不足以支持判断",
        "rejected": "不采用",
        "nonprobative": "不具证明力",
    }
    assessment_by_id = {
        item.get("source_id"): item
        for item in _list(assessments)
        if isinstance(item, dict) and item.get("source_id")
    }
    source_by_id = {
        source.get("source_id"): source
        for source in sources
        if isinstance(source, dict) and isinstance(source.get("source_id"), str)
    }
    relation_by_token = _source_relation_lookup(sources)
    for source in sources:
        label = _source_label(source)
        origin = origin_labels.get(source.get("origin"), "来源身份未标明")
        dates = []
        if source.get("event_at"):
            dates.append(f"事件日期：{source['event_at']}")
        if source.get("published_at"):
            dates.append(f"发布日期：{source['published_at']}")
        date_note = f"；{'；'.join(dates)}" if dates else ""
        assessment = assessment_by_id.get(source.get("source_id"), {})
        verdict = verdict_labels.get(assessment.get("verdict"), "尚未单独评价")
        limits = _joined(assessment.get("limitations"), fallback="未记录额外限制")
        cannot_prove = _joined(assessment.get("cannot_prove"), fallback="未记录")
        lineage = _source_relation_titles(
            assessment.get("source_lineage"), source_by_id, relation_by_token
        )
        conflicts = _source_relation_titles(
            assessment.get("conflict_source_ids"), source_by_id, relation_by_token
        )
        adoption_reason = _plain(
            assessment.get("interest_relevance"),
            "；".join(
                (
                    f"权威性：{_plain(assessment.get('authority'))}",
                    f"时效性：{_plain(assessment.get('freshness'))}",
                    f"关联性：{_plain(assessment.get('relevance'))}",
                )
            ),
        )
        revision_evidence = (
            f"对照冲突来源：{'、'.join(conflicts)}；当前证明边界：{cannot_prove}"
            if conflicts
            else f"未登记冲突来源；当前证明边界：{cannot_prove}"
        )
        lines.append(
            f"- {label}（{origin}{date_note}）：{verdict}；限制：{limits}；证明边界：{cannot_prove}；"
            f"来源身份：{_plain_source_identity(assessment.get('independence_identity'))}；"
            f"来源谱系：{'、'.join(lineage) if lineage else '未登记'}；"
            f"暂时采用项：{verdict}；采用理由：{adoption_reason}；改判证据：{revision_evidence}。"
        )
    return "\n".join(lines)


def render_answer(payload: dict[str, Any]) -> str:
    """Render the full authored argument; sections are never shortened by the renderer."""

    payload = _public_payload(payload)
    answer = payload.get("answer", {})
    chunks = ["# 回答", _plain(answer.get("direct_answer"), "现有材料还不足以给出可靠结论。")]
    for section in payload.get("reader_sections", []):
        if not isinstance(section, dict):
            continue
        heading = section.get("heading")
        if isinstance(heading, str) and heading.strip():
            chunks.append(f"## {heading.strip()}")
        for paragraph in [section.get("local_judgment"), *section.get("paragraphs", [])]:
            if isinstance(paragraph, str) and paragraph.strip():
                chunks.append(paragraph.strip())
    sources = payload.get("sources", [])
    if sources:
        chunks.extend(("## 来源", _source_lines(sources, payload.get("assessments", []))))
    closing = answer.get("closing")
    if isinstance(closing, str) and closing.strip():
        chunks.append(closing.strip())
    return "\n\n".join(chunks) + "\n"


def render_chat_projection(payload: dict[str, Any]) -> str:
    """The normal chat view is the complete file; only an explicit request permits a brief view."""

    payload = _public_payload(payload)
    delivery = payload.get("answer_delivery", {})
    if not isinstance(delivery, dict) or delivery.get("visible_mode", "full") == "full":
        return render_answer(payload)
    if delivery.get("visible_mode") != "brief":
        raise ValueError("unknown visible delivery mode")
    if not isinstance(delivery.get("explicit_user_request"), str) or not delivery["explicit_user_request"].strip():
        raise ValueError("brief projection requires an explicit user request")
    question = payload.get("problem_contract", {}).get("question", payload.get("question", ""))
    if delivery["explicit_user_request"] not in question:
        raise ValueError("explicit brief request must occur in the bound user question")
    text = delivery.get("brief_text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("brief projection requires visible text")
    return text.strip() + "\n"


def reader_contract_gaps(payload: dict[str, Any], text: str) -> list[str]:
    """Report user-visible omissions without treating prose length as proof."""

    section_errors = validate_reader_sections(payload)
    payload = _public_payload(payload)
    applicability = payload.get("dynamic_applicability")
    if applicability not in {"applicable", "not_applicable"}:
        return []
    gaps: list[str] = list(section_errors)
    for unit in authored_reader_units(payload):
        for fragment in unit["fragments"]:
            if fragment not in text:
                gaps.append(f"full body paragraph is absent: {unit['unit_id']}")
    direct = payload.get("answer", {}).get("direct_answer")
    if not isinstance(direct, str) or direct not in text:
        gaps.append("direct judgment is absent")
    # Natural sections carry their own wording. Requiring the former fixed
    # headings would force authored arguments back into the renderer's template.
    return _dedupe(gaps)


def render_dossier(payload: dict[str, Any]) -> str:
    payload = _public_payload(payload)
    facts = payload.get("facts", {})
    stance = (
        payload.get("stance_pair")
        if isinstance(payload.get("stance_pair"), dict)
        else {}
    )
    selected, rival, undecided = _selected_stance_pair(payload)
    if payload.get("dynamic_applicability") == "not_applicable":
        stance_summary = "本题是静态辨析，不形成动态立场定选或前瞻裁决。"
    elif undecided:
        stance_summary = (
            f"当前尚未定选：{selected.get('claim', '尚未形成。')}\n\n"
            f"待比较立场一：{stance.get('position', {}).get('claim', '尚未形成。')}\n\n"
            f"待比较立场二：{stance.get('counterposition', {}).get('claim', '尚未形成。')}\n\n"
            f"未定选原因：{stance.get('selection_reason', '两侧证据尚不能稳定区分。')}"
        )
    else:
        stance_summary = (
            f"当前较强的立场：{selected.get('claim', '尚未形成。')}\n\n"
            f"最强反方：{rival.get('claim', '尚未形成。')}\n\n"
            f"暂时选择的理由：{stance.get('selection_reason', '尚无选择理由。')}"
        )
    assessments = {item.get("source_id"): item for item in payload.get("assessments", [])}
    source_notes: list[str] = []
    for source in payload.get("sources", []):
        assessment = assessments.get(source.get("source_id"), {})
        limits = _joined(assessment.get("limitations"), fallback="未记录额外限制")
        cannot_prove = _joined(assessment.get("cannot_prove"), fallback="未记录")
        source_notes.append(
            f"{source.get('title', '未命名来源')}：{assessment.get('verdict', '尚未评价')}；"
            f"限制：{limits}；不能证明：{cannot_prove}。"
        )
    return (
        "# 判断底稿\n\n"
        "这份底稿保留可复核理由，不展示隐藏推理过程。\n\n"
        "## 问题\n\n"
        f"{payload.get('question', '未记录问题。')}\n\n"
        "## 事实边界\n\n"
        "已知：\n\n"
        f"{_items(facts.get('known'))}\n\n"
        "来自当事人或材料的说法：\n\n"
        f"{_items(facts.get('claimed'))}\n\n"
        "分析推断：\n\n"
        f"{_items(facts.get('inferred'))}\n\n"
        "仍未知：\n\n"
        f"{_items(facts.get('unknown'))}\n\n"
        "## 每个来源的单独评价\n\n"
        f"{_items(source_notes)}\n\n"
        "## 两种立场\n\n"
        f"{stance_summary}\n\n"
        "切换条件：\n\n"
        f"{_items(stance.get('switch_conditions'))}\n"
    )


def render_atlas(payload: dict[str, Any]) -> str:
    payload = _public_payload(payload)
    mechanisms = _reader_mechanisms(payload)
    paths = []
    for mechanism in mechanisms:
        paths.append(
            f"**{mechanism.get('name', '未命名解释')}**："
            f"{mechanism.get('explanation', '暂无说明')} 反向信号："
            f"{mechanism.get('failure_condition', '尚未记录')}"
        )
    return (
        "# 结构图谱\n\n"
        "图谱只保留这次问题里真正起作用的关系，不罗列术语。\n\n"
        "## 竞争解释\n\n"
        f"{_items(paths)}\n\n"
        "## 条件路径\n\n"
        f"{_order_text(payload)}\n\n"
        "## 观察重点\n\n"
        f"{_items(payload.get('answer', {}).get('uncertainties'))}\n"
    )


def render_casebook(payload: dict[str, Any]) -> str:
    payload = _public_payload(payload)
    chunks: list[str] = ["# 案例册", "", "案例只说明它实际支持的部分，不代替因果证明。"]
    cases, countercases = _case_records(payload)
    if not cases:
        chunks.extend(["", "## 暂无可核验案例", "", "需要补充真实记录或明确标为条件情景的材料。"])
    for case in cases:
        boundary = case.get("boundary") or _joined(case.get("cannot_prove"), fallback="尚未记录")
        chunks.extend(
            [
                "",
                f"## {case.get('summary', case.get('case_id', '未命名案例'))}",
                "",
                f"材料身份：{CASE_LABELS.get(case.get('kind'), '身份未明确')}。",
                "",
                f"它能说明：{_fragment(case.get('summary'), '尚未记录')}。",
                "",
                f"它不能越过的边界：{_fragment(boundary)}。",
            ]
        )
    if countercases:
        chunks.extend(["", "## 反例与失效案例"])
    for case in countercases:
        chunks.extend(
            [
                "",
                f"- 条件：{_joined(case.get('conditions'))}",
                f"- 预期信号：{_plain(case.get('expected_signal'))}",
                f"- 反向信号：{_plain(case.get('reverse_signal'))}",
                f"- 对判断的影响：{_plain(case.get('decision_impact'))}",
            ]
        )
    chunks.append("")
    return "\n".join(chunks)


def render_reader_outputs(payload: dict[str, Any]) -> dict[str, str]:
    """Render the four deterministic reader documents from one frozen packet."""

    return {
        "answer": render_answer(payload),
        "dossier": render_dossier(payload),
        "atlas": render_atlas(payload),
        "casebook": render_casebook(payload),
    }


def build_reader_trace(
    payload: dict[str, Any],
    units: list[dict[str, Any]],
    observed_outputs: dict[str, str],
) -> dict[str, Any]:
    """Bind renderer-owned fragments to exact UTF-8 byte ranges and source paths."""

    canonical_outputs = render_reader_outputs(payload)
    output_bindings: list[dict[str, Any]] = []
    for name, text in canonical_outputs.items():
        encoded = text.encode("utf-8")
        observed = observed_outputs.get(name, "")
        output_bindings.append(
            {
                "output": name,
                "bytes": len(encoded),
                "sha256": sha256(encoded).hexdigest(),
                "observed_sha256": sha256(observed.encode("utf-8")).hexdigest(),
                "matches_observed": observed == text,
            }
        )
    output_hashes = {
        item["output"]: item["sha256"] for item in output_bindings
    }
    entries: list[dict[str, Any]] = []
    missing_renderer_fragments: list[dict[str, Any]] = []
    for unit in units:
        fragment_sources = {
            str(item.get("text")): list(item.get("exact_source_paths", []))
            for item in unit.get("fragment_traces", [])
            if isinstance(item, dict)
        }
        for output in unit.get("required_outputs", ["answer"]):
            text = canonical_outputs.get(output, "")
            for fragment_index, fragment in enumerate(unit.get("fragments", [])):
                exact_fragment = str(fragment).rstrip("。；;，, ")
                if not exact_fragment:
                    continue
                start_character = text.find(exact_fragment)
                if start_character < 0:
                    missing_renderer_fragments.append(
                        {
                            "output": output,
                            "unit_id": unit.get("unit_id"),
                            "fragment": exact_fragment,
                        }
                    )
                    continue
                end_character = start_character + len(exact_fragment)
                start_byte = len(text[:start_character].encode("utf-8"))
                end_byte = len(text[:end_character].encode("utf-8"))
                fragment_bytes = exact_fragment.encode("utf-8")
                source_paths = fragment_sources.get(str(fragment), [])
                entries.append(
                    {
                        "output": output,
                        "unit_id": unit.get("unit_id"),
                        "unit_kind": unit.get("unit_kind"),
                        "fragment_index": fragment_index,
                        "start_byte": start_byte,
                        "end_byte": end_byte,
                        "fragment_sha256": sha256(fragment_bytes).hexdigest(),
                        "output_sha256": output_hashes[output],
                        "exact_source_paths": list(dict.fromkeys(source_paths)),
                    }
                )
    return {
        "schema_id": "xi-kari.v3.reader-trace",
        "schema_version": 3,
        "outputs": output_bindings,
        "entries": entries,
        "missing_renderer_fragments": missing_renderer_fragments,
    }


def check_plain_language(text: str) -> list[str]:
    errors: list[str] = []
    lower = text.lower()
    for token in MACHINE_TOKENS:
        if token in lower:
            errors.append(f"machine field leaked into prose: {token}")
    if PHASE_TOKEN.search(text):
        errors.append("runtime phase leaked into prose")
    if CONCEPT_TOKEN.search(text):
        errors.append("concept identifier leaked into prose")
    if HOST_CAPTURE_FIELD_TOKEN.search(text):
        errors.append("host capture machine field leaked into prose")
    if HOST_CAPTURE_ID_TOKEN.search(text):
        errors.append("host capture identifier leaked into prose")
    if HEX_DIGEST_TOKEN.search(text):
        errors.append("raw hash digest leaked into prose")
    if MACHINE_FIELD_TOKEN.search(text) or MACHINE_HASH_LABEL.search(text):
        errors.append("machine hash or schema field leaked into prose")
    if INTERNAL_ID_TOKEN_CASEFOLD.search(text):
        errors.append("internal runtime identifier leaked into prose")
    for paragraph in re.split(r"\n\s*\n", text):
        compact = paragraph.strip()
        if not compact or len(compact) > 240 or EXPLANATION_CUE.search(compact):
            continue
        phrases = [
            phrase.strip(" \t\r-*#。.!！?？()（）[]【】\"")
            for phrase in CONCEPT_WALL_SPLIT.split(compact)
        ]
        phrases = [phrase for phrase in phrases if 2 <= len(phrase) <= 20]
        concept_like = [
            phrase for phrase in phrases if CONCEPT_LIKE_ENDING.search(phrase)
        ]
        if len(phrases) >= 5 and len(concept_like) >= 4:
            errors.append("unexplained concept wall detected")
            break
    for line in text.splitlines():
        if line.count("`") >= 10:
            errors.append("jargon list detected")
            break
    return errors


def build_prose_plan(*, run_id: str, payload: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_id": "xi-kari.v3.prose-plan",
        "schema_version": 3,
        "run_id": run_id,
        "formats": ["answer", "dossier", "atlas", "casebook"],
        "deliverable_type": payload.get("deliverable_type", payload.get("problem_contract", {}).get("deliverable_type", "analysis")),
        "delivery_mode": "full",
        "reader_sections": payload.get("reader_sections", []),
        "reader_beats": [
            "direct_plain_answer",
            "fact_and_uncertainty_boundary",
            "competing_explanations",
            "concrete_case_and_limit",
            "continuous_three_order_or_explicit_non_applicability",
            "early_reverse_failure_and_withdrawal_signals",
            "paired_stance_and_switch_condition",
            "authorization_stop_rollback_appeal_and_remedy",
        ],
        "direct_answer": payload.get("answer", {}).get("direct_answer"),
        "coverage": coverage,
        "jargon_dump_forbidden": True,
    }


def render_artifact_index(
    run_dir: Path,
    *,
    contract_profile: str,
    authoring_profile: str,
) -> str:
    """Render the deterministic receipt for the XK11 reader artifacts."""

    lines = [
        "# 交付索引",
        "",
        f"合同 profile：`{contract_profile}`",
        f"authoring profile：`{authoring_profile}`",
        "",
        "## XK11 用户可见正文工件",
        "",
        "| 工件 | 运行内相对路径 | phase owner | SHA-256 | bytes |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for label, relative in USER_DELIVERY_ARTIFACTS:
        path = Path(run_dir) / relative
        if not path.is_file():
            raise ValueError(f"missing user delivery artifact: {relative}")
        lines.append(
            f"| [{label}]({path.name}) | `{relative}` | `XK11` | "
            f"`{sha256_file(path)}` | {path.stat().st_size} |"
        )
    lines.extend(
        [
            "",
            "## 终态与验证权威",
            "",
            "- [签名终态](../continuation/terminal-record.json)",
            "- [完成权威](../continuation/completion.json)",
            "- [官方 fresh validation](../validation/attempts/official/validator-report.json)",
            "",
            "## 正文检查边界",
            "",
            "[XK11 正文检查](../authoring/XK11-prose-review.json)是运行时执行的确定性普通语言规则检查，不是独立 reviewer，也不构成语义盲审。",
            "",
        ]
    )
    return "\n".join(lines)


def assemble_outputs(output_dir: Path, payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    answer_text = render_answer(payload)
    gaps = reader_contract_gaps(payload, answer_text)
    if gaps:
        raise ValueError(f"reader contract gaps: {gaps}")
    rendered = render_reader_outputs(payload)
    rendered["answer"] = answer_text
    result: dict[str, dict[str, Any]] = {}
    for name, text in rendered.items():
        errors = check_plain_language(text)
        if errors:
            raise ValueError(f"{name} is not plain-language safe: {errors}")
        path = output_dir / f"{name}.md"
        atomic_write_text(path, text)
        result[name] = {
            "path": path.name,
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
    return result
