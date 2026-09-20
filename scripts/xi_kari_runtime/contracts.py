"""Small runtime contracts shared by prepare, materialize and fresh validation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime, time, timezone
from pathlib import Path
import re
from typing import Any

from .authoring import (
    FORMAL_ADAPTER_PROFILE,
    FORMAL_ADAPTER_PROTOCOL,
    require_semantic_authoring_adapter,
)
from .canonical_json import (
    confined_path,
    read_json,
    sha256_file,
    sha256_json,
    sha256_text,
)
from .problem_contract import (
    DELIVERABLE_TYPES,
    FROZEN_FIELDS,
    build_natural_request_envelope,
    contract_hash,
    parse_instant,
    stance_neutrality_key,
    validate_problem_contract,
)
from .retrieval import (
    ADMITTED_ASSESSMENT_VERDICTS,
    CLOSED_INPUT_ORIGINS,
    has_bound_host_observation,
    validate_external_source_metadata,
    validate_source_assessment_payload,
)
from .semantic_projection import validate_visibility_ledger as validate_projection_visibility_ledger


PHASE_RESPONSIBILITIES = {
    "XK0": "问题合同",
    "XK1": "源锁",
    "XK2": "检索",
    "XK3": "证据",
    "XK4": "候选",
    "XK5": "联合状态",
    "XK6": "变换",
    "XK7": "机制",
    "XK8": "三阶",
    "XK9": "红队",
    "XK10": "裁决",
    "XK11": "读者",
    "XK12": "验证",
}
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
DELIVERY_PATHS = {
    "answer": "delivery/xi-kari-answer.md",
    "dossier": "delivery/xi-kari-dossier.md",
    "atlas": "delivery/xi-kari-concept-atlas.md",
    "casebook": "delivery/xi-kari-case-and-countercase.md",
    "artifact_index": "delivery/artifact-index.md",
    "final_chat": "delivery/final-chat.json",
}
XK_PHASES = tuple(f"XK{index}" for index in range(13))
PRODUCTION_CONTRACT_PROFILE = "production-authoring-v3"
EXECUTE_OWNED_BINDING_PROTOCOL = "xi-kari.v3.execute-owned-binding/v1"
EXECUTE_OWNED_BINDING_OWNER = "execute_authored_run"
EXECUTE_OWNED_BINDING_FIELDS = frozenset(
    {
        "protocol",
        "owner",
        "run_id",
        "parent_pid",
        "child_pid",
        "exit_status",
        "provider_binding_sha256",
        "provider_executable_sha256",
        "provider_argv_sha256",
        "adapter_executable_sha256",
        "command_sha256",
        "input_sha256",
        "prompt_sha256",
        "stdout_sha256",
        "stderr_sha256",
        "semantic_output_sha256",
        "semantic_read_trace_sha256",
        "ontology_read_plan_sha256",
        "ontology_read_trace_sha256",
        "base_receipt_sha256",
        "retrieval_receipt_sha256",
        "retrieval_sha256",
    }
)
CONTRACT_PROFILES = frozenset({PRODUCTION_CONTRACT_PROFILE})


def build_execute_owned_binding(
    base_receipt: Mapping[str, Any],
    retrieval_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Project independently observed execution evidence into the run contract."""

    run_id = base_receipt.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("base authoring receipt has no run_id")
    if retrieval_receipt.get("run_id") != run_id:
        raise ValueError("retrieval receipt run_id differs from base authoring")
    required_base = (
        "parent_pid",
        "child_pid",
        "exit_status",
        "provider_binding_sha256",
        "provider_executable_sha256",
        "provider_argv_sha256",
        "adapter_executable_sha256",
        "command_sha256",
        "input_sha256",
        "prompt_sha256",
        "stdout_sha256",
        "stderr_sha256",
        "semantic_output_sha256",
        "semantic_read_trace_sha256",
        "ontology_read_plan_sha256",
        "ontology_read_trace_sha256",
        "receipt_sha256",
    )
    missing = [field for field in required_base if field not in base_receipt]
    if missing:
        raise ValueError(
            "base authoring receipt is missing execution evidence: " + missing[0]
        )
    if base_receipt.get("exit_status") != 0:
        raise ValueError("base authoring execution did not exit successfully")
    if retrieval_receipt.get("retrieval_sha256") is None:
        raise ValueError("retrieval receipt has no retrieval binding")
    if retrieval_receipt.get("receipt_sha256") is None:
        raise ValueError("retrieval receipt has no receipt binding")
    return {
        "protocol": EXECUTE_OWNED_BINDING_PROTOCOL,
        "owner": EXECUTE_OWNED_BINDING_OWNER,
        "run_id": run_id,
        "parent_pid": base_receipt["parent_pid"],
        "child_pid": base_receipt["child_pid"],
        "exit_status": base_receipt["exit_status"],
        "provider_binding_sha256": base_receipt["provider_binding_sha256"],
        "provider_executable_sha256": base_receipt["provider_executable_sha256"],
        "provider_argv_sha256": base_receipt["provider_argv_sha256"],
        "adapter_executable_sha256": base_receipt["adapter_executable_sha256"],
        "command_sha256": base_receipt["command_sha256"],
        "input_sha256": base_receipt["input_sha256"],
        "prompt_sha256": base_receipt["prompt_sha256"],
        "stdout_sha256": base_receipt["stdout_sha256"],
        "stderr_sha256": base_receipt["stderr_sha256"],
        "semantic_output_sha256": base_receipt["semantic_output_sha256"],
        "semantic_read_trace_sha256": base_receipt["semantic_read_trace_sha256"],
        "ontology_read_plan_sha256": base_receipt["ontology_read_plan_sha256"],
        "ontology_read_trace_sha256": base_receipt["ontology_read_trace_sha256"],
        "base_receipt_sha256": base_receipt["receipt_sha256"],
        "retrieval_receipt_sha256": retrieval_receipt["receipt_sha256"],
        "retrieval_sha256": retrieval_receipt["retrieval_sha256"],
    }


def validate_execute_owned_binding(
    binding: Any,
    *,
    run_contract: Mapping[str, Any],
    base_receipt: Mapping[str, Any] | None = None,
    retrieval_receipt: Mapping[str, Any] | None = None,
) -> list[str]:
    """Check the disk binding against runtime-owned execution observations."""

    errors: list[str] = []
    if not isinstance(binding, Mapping):
        return ["production run is missing execute-owned binding"]
    if set(binding) != EXECUTE_OWNED_BINDING_FIELDS:
        return ["execute-owned binding fields are not exact"]
    if binding.get("protocol") != EXECUTE_OWNED_BINDING_PROTOCOL:
        errors.append("execute-owned binding protocol is invalid")
    if binding.get("owner") != EXECUTE_OWNED_BINDING_OWNER:
        errors.append("execute-owned binding owner is invalid")
    if binding.get("run_id") != run_contract.get("run_id"):
        errors.append("execute-owned binding run_id differs from run contract")
    if binding.get("exit_status") != 0:
        errors.append("execute-owned binding exit status is not successful")
    for field in (
        "parent_pid",
        "child_pid",
    ):
        value = binding.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            errors.append(f"execute-owned binding {field} is invalid")
    if base_receipt is not None:
        try:
            expected = build_execute_owned_binding(
                base_receipt,
                retrieval_receipt or {},
            )
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"execute-owned binding evidence is invalid: {exc}")
        else:
            for field, value in expected.items():
                if binding.get(field) != value:
                    errors.append(
                        f"execute-owned binding differs from execution evidence: {field}"
                    )
    return errors


def build_runtime_packet_binding(
    run_contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the runtime-owned provenance binding for a current run packet."""
    capability = run_contract.get("capability_snapshot")
    adapter = (
        capability.get("semantic_authoring_adapter")
        if isinstance(capability, Mapping)
        else None
    )
    if adapter is not None and not isinstance(adapter, Mapping):
        raise ValueError("run contract semantic authoring adapter is invalid")
    return {
        "run_id": run_contract.get("run_id"),
        "question": run_contract.get("question"),
        "mode": run_contract.get("mode"),
        "evidence_cutoff": run_contract.get("evidence_cutoff"),
        "problem_contract_sha256": run_contract.get("problem_contract_sha256"),
        "stance_neutrality_key": run_contract.get("stance_neutrality_key"),
        "privacy_contract_sha256": sha256_json(
            run_contract.get("privacy_contract")
        ),
        "contract_profile": run_contract.get("contract_profile"),
        "semantic_authoring_protocol": (
            adapter.get("protocol") if isinstance(adapter, Mapping) else None
        ),
        "semantic_authoring_profile": (
            adapter.get("profile", FORMAL_ADAPTER_PROFILE)
            if isinstance(adapter, Mapping)
            else FORMAL_ADAPTER_PROFILE
        ),
        "semantic_authoring_adapter_sha256": sha256_json(adapter),
        "provider_binding_sha256": (
            adapter.get("provider_binding_sha256")
            if isinstance(adapter, Mapping)
            and isinstance(adapter.get("provider_binding_sha256"), str)
            else sha256_json(None)
        ),
    }
COMPLETE_STATE_MISMATCH_ERROR = (
    "complete phase chain and continuation state disagree"
)
PREMATURE_COMPLETE_STATE_ERROR = (
    "continuation state claims complete before XK12 phase chain"
)
DYNAMIC_PHASE_FIELDS = (
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
    "framework_gap",
    "mechanisms",
    "orders",
)

# Retrieval profiles are part of the frozen XK0 problem contract.  The
# profile therefore changes the minimum query frontier, rather than being a
# descriptive label that can be left unused by a packet author.
FIVE_DIRECTION_QUERY_DIRECTIONS = frozenset(
    {
        "current_baseline",
        "mechanism_support",
        "counterevidence",
        "comparable_case",
        "affected_low_power_position",
    }
)
QUERY_DIRECTIONS = FIVE_DIRECTION_QUERY_DIRECTIONS | {
    "authoritative_definition",
}
QUERY_EXECUTED_STATES = frozenset({"executed", "saturated", "capability_limited"})
DIRECTIONAL_EVIDENCE_FIELDS = frozenset(
    {
        "direction",
        "search_event_id",
        "stop_boundary",
        "source_urls",
        "source_ids",
        "distinct_url_count",
        "distinct_source_count",
        "distinct_content_count",
        "distinct_independence_count",
        "new_information_count",
        "stop_reason",
    }
)
V83_CONCEPT_TOKEN = re.compile(r"(?<![A-Za-z0-9])V83-[A-Z0-9-]+(?![A-Za-z0-9])")
DEFINITION_ASSERTION = re.compile(
    r"(?:权威)?定义(?:是|为)|是指|means\b|defined\s+as\b",
    re.IGNORECASE,
)
PROVISIONAL_TOKEN = re.compile(
    r"(?<![A-Z0-9_.:-])(XK-PROV-[A-Z0-9_.:-]+)(?![A-Z0-9_.:-])"
)
ORDER_NARRATIVE_MARKER = re.compile(r"(?:第\s*)?[一二三123]\s*阶")
ORDER_NARRATIVE_PREDICATE = re.compile(
    r"(?:导致|引发|触发|推动|促使|使得|让|改变|改写|写回|回写|扩散|传导|"
    r"放大|累积|固化|制度化|形成|生成|演化|转化|转为|进入|升级|收敛|"
    r"迁移|重组|更新|发生|产生|延续|影响)"
)
ORDER_NARRATIVE_NEGATION = re.compile(
    r"(?:不适用|未运行|未发生|没有发生|尚未|并未|并非|不会|不能|不得|不应|"
    r"无需|无从|不再|拒绝|停止)"
)
ORDER_NARRATIVE_PREFIX_NEGATION = re.compile(
    r"(?:不进行|未发生(?:的)?|没有|不存在|不得进行|拒绝进行)\s*$"
)
ORDER_NARRATIVE_DEFINITION_PREFIX = re.compile(r"(?:所谓|术语|概念)\s*$")
ORDER_NARRATIVE_DEFINITION_LEAD = re.compile(
    r"^(?:\s|，|,)*(?:(?:的\s*)?(?:定义|含义)|是指|指的是|定义为|"
    r"用于(?:说明|描述|区分)|(?:分别)?表示(?:的是)?|(?:分别)?对应)"
)
ORDER_NARRATIVE_SENTENCE = re.compile(r"[。！？!?；;\n]+")


def _externally_redefines_v83(value: Mapping[str, Any]) -> bool:
    identity = value.get("identity") or value.get("fact_identity") or value.get("kind")
    if identity not in {"external_fact", "source_claim", "documented_real_case"}:
        return False
    text = next(
        (
            candidate
            for field in ("text", "statement", "proposition", "summary")
            if isinstance((candidate := value.get(field)), str)
        ),
        "",
    )
    return bool(V83_CONCEPT_TOKEN.search(text) and DEFINITION_ASSERTION.search(text))


def _asserts_dynamic_order_narrative(text: str) -> bool:
    for sentence in ORDER_NARRATIVE_SENTENCE.split(text):
        markers = list(ORDER_NARRATIVE_MARKER.finditer(sentence))
        for index, marker in enumerate(markers):
            end = markers[index + 1].start() if index + 1 < len(markers) else len(sentence)
            continuation = sentence[marker.end() : end]
            predicate = ORDER_NARRATIVE_PREDICATE.search(continuation)
            if predicate is None:
                continue
            lead = continuation[: predicate.start()]
            prefix = sentence[max(0, marker.start() - 16) : marker.start()]
            if ORDER_NARRATIVE_NEGATION.search(lead) or re.search(
                r"(?:不|未|无|没)(?!但|仅)[^，,]{0,6}$", lead
            ):
                continue
            if ORDER_NARRATIVE_PREFIX_NEGATION.search(prefix):
                continue
            if ORDER_NARRATIVE_DEFINITION_PREFIX.search(
                prefix
            ) or ORDER_NARRATIVE_DEFINITION_LEAD.search(lead):
                continue
            return True
    return False


def _static_answer_dynamic_narrative_path(answer: Mapping[str, Any]) -> str | None:
    direct = answer.get("direct_answer")
    if isinstance(direct, str) and _asserts_dynamic_order_narrative(direct):
        return "answer.direct_answer"
    why = answer.get("why")
    if isinstance(why, str) and _asserts_dynamic_order_narrative(why):
        return "answer.why"
    if isinstance(why, Sequence) and not isinstance(why, (str, bytes)):
        for index, value in enumerate(why):
            if isinstance(value, str) and _asserts_dynamic_order_narrative(value):
                return f"answer.why[{index}]"
    return None


def is_safe_run_id(value: Any) -> bool:
    return isinstance(value, str) and RUN_ID_PATTERN.fullmatch(value) is not None


def validate_visibility_ledger(
    packet: Mapping[str, Any], *, privacy_contract: Mapping[str, Any] | None
) -> None:
    expected_purpose = (
        privacy_contract.get("purpose")
        if isinstance(privacy_contract, Mapping)
        else None
    )
    validate_projection_visibility_ledger(
        packet,
        expected_purpose=(
            expected_purpose if isinstance(expected_purpose, str) else None
        ),
    )


def build_continuity_bundle_binding(
    repository_root: Path, path: Path
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    bundle = Path(path).resolve()
    text = bundle.read_text(encoding="utf-8")
    relative = bundle.relative_to(root).as_posix()
    source_anchors = sorted(
        set(re.findall(r"\bV83-(?:P\d{4}|T\d{3})\b", text))
    )
    anchor_index = read_json(
        root / "references" / "source" / "v8.3" / "indexes" / "anchors.json"
    )
    known_anchors = {
        anchor
        for field in ("paragraphs", "tables")
        for anchor in anchor_index.get(field, [])
        if isinstance(anchor, str)
    }
    if not source_anchors or any(
        anchor not in known_anchors for anchor in source_anchors
    ):
        raise ValueError(f"continuity bundle has invalid source anchors: {relative}")
    registry_path = (
        root
        / "references"
        / "ontology"
        / "continuity-bundle-registry.json"
    )
    registry = read_json(registry_path)
    entries = registry.get("bundles") if isinstance(registry, Mapping) else None
    entry = entries.get(relative) if isinstance(entries, Mapping) else None
    if (
        not isinstance(entry, Mapping)
        or entry.get("sha256") != sha256_file(bundle)
        or entry.get("source_anchors") != source_anchors
        or entry.get("route_kind") != "curated_semantic_closure"
    ):
        raise ValueError(
            f"continuity bundle differs from its curated registry: {relative}"
        )
    return {
        "path": relative,
        "sha256": sha256_file(bundle),
        "registry_sha256": sha256_file(registry_path),
        "source_anchors": source_anchors,
        "route_kind": "curated_semantic_closure",
    }


def derive_repair_scope(errors: Sequence[str]) -> tuple[str, list[str]]:
    if not errors:
        raise ValueError("repair requires at least one validation error")
    invalid_indices: list[int] = []
    for error in errors:
        message = str(error)
        owned_indices: list[int] = []
        if "phase-events.jsonl" in message:
            owned_indices.append(XK_PHASES.index("XK0"))
        else:
            owner = re.search(r"\bXK(0?[0-9]|1[0-2])\b", message)
            if owner is not None:
                owned_indices.append(int(owner.group(1)))
        if not owned_indices and "runtime control binding mismatch" in message:
            owned_indices.append(XK_PHASES.index("XK0"))
        elif not owned_indices and "input packet" in message:
            owned_indices.append(XK_PHASES.index("XK2"))
        elif not owned_indices and (
            "candidate census" in message or "concept disposition" in message
        ):
            owned_indices.append(XK_PHASES.index("XK4"))
        elif not owned_indices and any(
            marker in message
            for marker in ("delivery", "final chat", "output plan")
        ):
            owned_indices.append(XK_PHASES.index("XK11"))
        elif not owned_indices and any(
            marker in message
            for marker in (
                "terminal authority",
                "completion authority",
                "official validation",
                "XK12 transaction",
                "artifact manifest",
            )
        ):
            owned_indices.append(XK_PHASES.index("XK12"))
        if not owned_indices:
            raise ValueError(
                f"cannot assign validation error to an XK phase: {message}"
            )
        invalid_indices.extend(owned_indices)
    index = min(invalid_indices)
    return XK_PHASES[index], list(XK_PHASES[index:])


def repair_phase_events_sha256(run_dir: Path) -> str:
    """Return a stable binding for the phase journal, including its absence."""

    path = Path(run_dir) / "phase-events.jsonl"
    if path.is_file() and not path.is_symlink():
        return sha256_file(path)
    return sha256_json(
        {
            "path": "phase-events.jsonl",
            "status": "missing" if not path.exists() else "unsafe",
        }
    )


def validate_lifecycle_sidecars(
    run_dir: Path,
    run_contract: Mapping[str, Any],
    *,
    phase_count: int,
) -> list[str]:
    errors: list[str] = []
    state_path = Path(run_dir) / "continuation" / "state.json"
    cancel_path = Path(run_dir) / "continuation" / "cancel.json"
    try:
        state = read_json(state_path)
    except Exception as exc:
        return [f"cannot read continuation state: {exc}"]
    if not isinstance(state, Mapping):
        return ["continuation state is not an object"]
    run_id = run_contract.get("run_id")
    if state.get("run_id") != run_id:
        errors.append("continuation state run_id differs from run contract")

    cancel: Mapping[str, Any] | None = None
    if cancel_path.is_file():
        try:
            value = read_json(cancel_path)
        except Exception as exc:
            errors.append(f"cannot read cancel record: {exc}")
        else:
            if not isinstance(value, Mapping):
                errors.append("cancel record is not an object")
            else:
                cancel = value
                if cancel.get("run_id") != run_id:
                    errors.append("cancel record run_id differs from run contract")
    if cancel is not None and (
        state.get("state") != "cancelled" or state.get("next_phase") is not None
    ):
        errors.append("cancel record and continuation state disagree")
    if cancel is None and state.get("state") == "cancelled":
        errors.append("cancel record and continuation state disagree")
    if cancel is None and phase_count == 1:
        if state.get("state") != "initialized" or state.get("next_phase") != "XK1":
            errors.append(
                "XK0-only run must be initialized with next_phase XK1"
            )
        for relative in (
            *expected_phase_artifact_paths(
                "XK1",
                contract_profile=str(run_contract.get("contract_profile", "")),
                mode=str(run_contract.get("mode", "")),
            ),
            "authoring/XK02-retrieval-ledger.json",
        ):
            if (Path(run_dir) / relative).exists():
                errors.append(
                    f"initialized run contains premature XK1 artifact: {relative}"
                )
    elif state.get("state") == "initialized":
        errors.append("initialized state requires exactly one sealed phase")
    if phase_count == len(XK_PHASES):
        if state.get("state") != "complete" or state.get("next_phase") is not None:
            errors.append(COMPLETE_STATE_MISMATCH_ERROR)
    elif state.get("state") == "complete":
        errors.append(PREMATURE_COMPLETE_STATE_ERROR)
    return errors


def validate_repair_packet_binding(
    run_dir: Path, run_contract: Mapping[str, Any]
) -> list[str]:
    if run_contract.get("continuation", {}).get("kind") != "repair":
        return []
    repair_path = Path(run_dir) / "continuation" / "repair-record.json"
    packet_path = Path(run_dir) / "continuation" / "input-packet.json"
    try:
        repair = read_json(repair_path)
    except Exception as exc:
        return [f"cannot read repair record: {exc}"]
    try:
        packet = read_json(packet_path)
    except Exception as exc:
        return [f"cannot read repair child disk packet: {exc}"]
    if not isinstance(repair, Mapping):
        return ["repair record is not an object"]
    if repair.get("replacement_packet_sha256") != sha256_json(packet):
        return ["repair replacement packet hash differs from child disk packet"]
    return []


def validate_runtime_control_bindings(
    run_dir: Path,
    run_contract: Mapping[str, Any],
    *,
    verify_external_bindings: bool = False,
) -> list[str]:
    errors: list[str] = []
    mode = run_contract.get("mode")
    natural_request = run_contract.get("natural_request")
    if natural_request is not None:
        try:
            expected_natural_request = build_natural_request_envelope(
                natural_request.get("text") if isinstance(natural_request, Mapping) else None,
                mode=str(mode),
                evidence_cutoff=str(run_contract.get("evidence_cutoff")),
            )
            if dict(natural_request) != expected_natural_request:
                errors.append(
                    "runtime control binding mismatch: run-contract.json.natural_request"
                )
        except (AttributeError, TypeError, ValueError) as exc:
            errors.append(f"runtime control binding mismatch: natural request: {exc}")
    expected_network = mode == "open-world"
    contract_capability = run_contract.get("capability_snapshot")
    if not isinstance(contract_capability, Mapping) or contract_capability.get(
        "network_retrieval"
    ) is not expected_network:
        errors.append(
            "runtime control binding mismatch: "
            "run-contract.json.capability_snapshot.network_retrieval"
        )
    if (
        not isinstance(contract_capability, Mapping)
        or contract_capability.get("contract_profile")
        != run_contract.get("contract_profile")
    ):
        errors.append(
            "runtime control binding mismatch: "
            "run-contract.json.capability_snapshot.contract_profile"
        )
    contract_adapter = (
        contract_capability.get("semantic_authoring_adapter")
        if isinstance(contract_capability, Mapping)
        else None
    )
    contract_profile = run_contract.get("contract_profile")
    profile_pair_is_valid = (
        contract_profile == PRODUCTION_CONTRACT_PROFILE
        and isinstance(contract_adapter, Mapping)
        and contract_adapter.get("protocol") == FORMAL_ADAPTER_PROTOCOL
        and contract_adapter.get("profile") == FORMAL_ADAPTER_PROFILE
    )
    if contract_profile not in CONTRACT_PROFILES or not profile_pair_is_valid:
        errors.append(
            "runtime control binding mismatch: contract profile and semantic "
            "authoring adapter profile disagree"
        )
    execute_owned_binding = (
        contract_capability.get("execute_owned_binding")
        if isinstance(contract_capability, Mapping)
        else None
    )
    if contract_profile == PRODUCTION_CONTRACT_PROFILE:
        base_receipt = None
        retrieval_receipt = None
        base_receipt_path = Path(run_dir) / "authoring/XK01-base-authoring-receipt.json"
        retrieval_receipt_path = (
            Path(run_dir) / "authoring/XK02-retrieval-execution-receipt.json"
        )
        if base_receipt_path.is_file() and retrieval_receipt_path.is_file():
            try:
                raw_base_receipt = read_json(base_receipt_path)
                raw_retrieval_receipt = read_json(retrieval_receipt_path)
            except (OSError, TypeError, ValueError):
                pass
            else:
                if isinstance(raw_base_receipt, Mapping):
                    base_receipt = raw_base_receipt
                if isinstance(raw_retrieval_receipt, Mapping):
                    retrieval_receipt = raw_retrieval_receipt
        errors.extend(
            validate_execute_owned_binding(
                execute_owned_binding,
                run_contract=run_contract,
                base_receipt=base_receipt,
                retrieval_receipt=retrieval_receipt,
            )
        )
    else:
        errors.append("run requires the current production contract profile")
    if contract_adapter is not None:
        try:
            require_semantic_authoring_adapter(
                contract_adapter,
                verify_executable=verify_external_bindings,
            )
        except ValueError as exc:
            errors.append(f"runtime control binding mismatch: {exc}")

    checks = (
        ("capability-snapshot.json", "mode", mode),
        (
            "capability-snapshot.json",
            "contract_profile",
            run_contract.get("contract_profile"),
        ),
        (
            "capability-snapshot.json",
            "network_retrieval",
            expected_network,
        ),
        ("authoring/XK02-retrieval-ledger.json", "mode", mode),
        ("retrieval/index.json", "mode", mode),
        (
            "authoring/XK03-unknown-register.json",
            "evidence_cutoff",
            run_contract.get("evidence_cutoff"),
        ),
    )
    for relative, field, expected in checks:
        path = Path(run_dir) / relative
        if not path.is_file():
            continue
        try:
            document = read_json(path)
        except Exception:
            continue
        if not isinstance(document, Mapping) or document.get(field) != expected:
            errors.append(
                f"runtime control binding mismatch: {relative}.{field}"
            )
    capability_path = Path(run_dir) / "capability-snapshot.json"
    if capability_path.is_file():
        try:
            capability_document = read_json(capability_path)
        except Exception:
            capability_document = None
        if (
            not isinstance(capability_document, Mapping)
            or capability_document.get("semantic_authoring_adapter")
            != contract_adapter
        ):
            errors.append(
                "runtime control binding mismatch: "
                "capability-snapshot.json.semantic_authoring_adapter"
            )
    return errors


def _walk(value: Any, path: str = "$"):
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def _validate_case_source_origins(packet: Mapping[str, Any]) -> None:
    retrieval = packet.get("retrieval")
    if not isinstance(retrieval, Mapping):
        return
    source_origins = {
        record.get("source_id"): record.get("origin")
        for record in retrieval.get("sources", [])
        if isinstance(record, Mapping)
        and isinstance(record.get("source_id"), str)
    }
    graph = packet.get("claim_mechanism_graph")
    case_ledger = packet.get("case_ledger")
    containers = (
        graph.get("cases", []) if isinstance(graph, Mapping) else [],
        case_ledger.get("cases", []) if isinstance(case_ledger, Mapping) else [],
    )
    for records in containers:
        for case in records:
            if not isinstance(case, Mapping):
                continue
            expected_origin = CASE_ORIGIN_KINDS.get(case.get("kind"))
            if expected_origin is None:
                continue
            source_refs = case.get("source_refs")
            if not isinstance(source_refs, list):
                continue
            for source_id in source_refs:
                if source_id not in source_origins:
                    continue
                origin = source_origins[source_id]
                if origin not in expected_origin:
                    raise ValueError(
                        "case kind differs from source origin: "
                        f"{case.get('case_id')} -> {source_id} ({origin})"
                    )


FACT_IDENTITIES = {
    "user_material",
    "external_fact",
    "source_claim",
    "model_inference",
    "conditional_scenario",
    "structural_analogy",
    "unknown",
    "v8.3_definition",
}
CLOSED_ALLOWED_IDENTITIES = {
    "user_material",
    "v8.3_definition",
    "unknown",
    "model_inference",
    "conditional_scenario",
    "structural_analogy",
}
FACT_BUCKETS = ("known", "claimed", "inferred", "unknown")
CASE_KINDS = {
    "documented_real_case",
    "user_material_case",
    "conditional_scenario",
    "structural_analogy",
}
CASE_ORIGIN_KINDS = {
    "documented-real": {"external"},
    "documented_real_case": {"external"},
    "user-material": {"user", "user_material", "provided"},
    "user_material_case": {"user", "user_material", "provided"},
}
XK3_KINDS_BY_GRAPH_CLAIM_KIND = {
    "factual": {"external_fact", "user_material"},
    "structural": {
        "source_claim",
        "external_fact",
        "user_material",
        "model_inference",
        "structural_analogy",
    },
    "mechanism": {
        "source_claim",
        "external_fact",
        "user_material",
        "model_inference",
        "structural_analogy",
        "conditional_scenario",
    },
    "prediction": {
        "source_claim",
        "model_inference",
        "conditional_scenario",
    },
    "value": {"source_claim", "user_material", "normative_premise"},
    "responsibility": {"source_claim", "external_fact", "user_material"},
    "authorization": {"authorization_boundary"},
}


def _require_nonempty_text(value: Any, *, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")


def _require_dynamic_gate(
    packet: Mapping[str, Any], name: str, required_fields: tuple[str, ...]
) -> Mapping[str, Any]:
    value = packet.get(name)
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    if value.get("status") == "not_run":
        raise ValueError(f"{name} cannot be not_run for a dynamic problem")
    missing = [field for field in required_fields if field not in value]
    if missing:
        raise ValueError(f"{name} missing required fields: {missing}")
    return value


def validate_partial_explanation_order(verdict: Mapping[str, Any]) -> None:
    boundary = verdict.get("non_decidability")
    partial = boundary.get("remaining_partial_order") if isinstance(boundary, Mapping) else None
    if not isinstance(partial, list) or len(partial) < 2 or len(set(partial)) != len(partial):
        raise ValueError("non-decidability requires at least two unresolved explanations")
    ranking = verdict.get("explanation_ranking")
    if not isinstance(ranking, list) or any(
        isinstance(row, Mapping)
        and row.get("explanation_id") in partial
        and row.get("rank") is not None
        for row in ranking
    ):
        raise ValueError("unresolved explanations cannot receive a local rank")


def validate_dynamic_gates(packet: Mapping[str, Any]) -> None:
    cascade = _require_dynamic_gate(packet, "cascade", ("hops",))
    if not isinstance(cascade.get("hops"), list) or not cascade["hops"]:
        raise ValueError("cascade.hops must be a non-empty list")
    evaluation = _require_dynamic_gate(packet, "order_evaluation", ("orders",))
    orders = evaluation.get("orders")
    if not isinstance(orders, list) or not 1 <= len(orders) <= 3:
        raise ValueError("order_evaluation.orders must contain one to three evaluated orders")
    required_order_fields = {
        "order",
        "evaluated_node_ids",
        "evaluated_branch_ids",
        "not_run_branch_ids",
        "baseline",
        "baseline_binding",
        "explanatory_increment",
        "explanatory_increment_binding",
        "predictive_increment",
        "predictive_increment_binding",
        "new_assumptions",
        "new_losses",
        "local_predictability",
        "continue_value",
    }
    evaluation_signatures: set[tuple[str, str, str]] = set()
    for index, order in enumerate(orders, start=1):
        if not isinstance(order, Mapping) or required_order_fields - set(order):
            raise ValueError(f"order_evaluation.orders[{index - 1}] is incomplete")
        if order.get("order") != index:
            raise ValueError("order_evaluation orders must be continuous from one")
        comparison = tuple(
            str(order.get(field, "")).strip()
            for field in (
                "baseline",
                "explanatory_increment",
                "predictive_increment",
            )
        )
        if any(not value for value in comparison) or len(set(comparison)) != 3:
            raise ValueError(
                "order evaluation must add order-specific information"
            )
        if comparison in evaluation_signatures:
            raise ValueError(
                "order evaluation must add order-specific information"
            )
        evaluation_signatures.add(comparison)
    lineage = packet.get("recursive_lineage")
    maximum_order = (
        lineage.get("maximum_order") if isinstance(lineage, Mapping) else None
    )
    if not isinstance(maximum_order, int) or isinstance(maximum_order, bool):
        raise ValueError("recursive_lineage.maximum_order must be an integer")
    evaluated_orders = [order["order"] for order in orders]
    absent = next(
        (order for order in evaluated_orders if order > maximum_order), None
    )
    if absent is not None:
        raise ValueError(
            "order_evaluation cannot evaluate order absent from recursive lineage: "
            f"{absent}"
        )
    expected_orders = list(range(1, maximum_order + 1))
    if evaluated_orders != expected_orders:
        raise ValueError(
            "order_evaluation must cover every recursive lineage order exactly once"
        )
    lineage_nodes = lineage.get("nodes", []) if isinstance(lineage, Mapping) else []
    lineage_branches = (
        lineage.get("branches", []) if isinstance(lineage, Mapping) else []
    )
    not_run_orders = (
        lineage.get("not_run_orders", []) if isinstance(lineage, Mapping) else []
    )
    for row in orders:
        order_number = row["order"]
        expected_node_ids = {
            node.get("node_id")
            for node in lineage_nodes
            if isinstance(node, Mapping) and node.get("order") == order_number
        }
        expected_branch_ids = {
            branch.get("branch_id")
            for branch in lineage_branches
            if isinstance(branch, Mapping)
            and any(
                isinstance(node, Mapping)
                and node.get("order") == order_number
                and node.get("node_id") in branch.get("node_ids", [])
                for node in lineage_nodes
            )
        }
        expected_not_run_ids = {
            record.get("branch_id")
            for record in not_run_orders
            if isinstance(record, Mapping) and record.get("order") == order_number
        }
        if set(row["evaluated_node_ids"]) != expected_node_ids:
            raise ValueError(
                f"order_evaluation order {order_number} node binding differs from XK8"
            )
        if set(row["evaluated_branch_ids"]) != expected_branch_ids:
            raise ValueError(
                f"order_evaluation order {order_number} branch binding differs from XK8"
            )
        if set(row["not_run_branch_ids"]) != expected_not_run_ids:
            raise ValueError(
                f"order_evaluation order {order_number} not_run binding differs from XK8"
            )
        expected_delta_sha256 = sha256_json(
            {
                "new_assumptions": row["new_assumptions"],
                "new_losses": row["new_losses"],
            }
        )
        for field in (
            "baseline",
            "explanatory_increment",
            "predictive_increment",
        ):
            binding = row.get(f"{field}_binding")
            if (
                not isinstance(binding, Mapping)
                or set(binding.get("evaluated_node_ids", [])) != expected_node_ids
                or set(binding.get("evaluated_branch_ids", []))
                != expected_branch_ids
            ):
                raise ValueError(
                    f"order_evaluation order {order_number} {field} binding differs from XK8"
                )
            if binding.get("content_sha256") != sha256_json(row[field]):
                raise ValueError(
                    f"order_evaluation order {order_number} {field} binding differs from its increment"
                )
            if binding.get("delta_sha256") != expected_delta_sha256:
                raise ValueError(
                    f"order_evaluation order {order_number} {field} binding differs from its new delta"
                )
        if set(row["evaluated_branch_ids"]).intersection(row["not_run_branch_ids"]):
            raise ValueError(
                f"order_evaluation order {order_number} cannot execute and skip one branch"
            )
        _require_nonempty_text(
            row.get("local_predictability"),
            field=f"order_evaluation.orders[{order_number - 1}].local_predictability",
        )
    reader_orders = packet.get("orders")
    if not isinstance(reader_orders, list) or not reader_orders:
        raise ValueError("reader order projection must be a non-empty list")
    projected_orders = [
        row.get("order") if isinstance(row, Mapping) else None
        for row in reader_orders
    ]
    absent = next(
        (
            order
            for order in projected_orders
            if isinstance(order, int)
            and not isinstance(order, bool)
            and order > maximum_order
        ),
        None,
    )
    if absent is not None:
        raise ValueError(
            "reader projection cannot narrate order absent from recursive lineage: "
            f"{absent}"
        )
    if projected_orders != expected_orders:
        raise ValueError(
            "reader order projection must match recursive lineage orders"
        )

    red_team = _require_dynamic_gate(
        packet,
        "red_team",
        (
            "strongest_attack",
            "attacked_evidence_refs",
            "attacked_claim_ids",
            "attacked_mechanism_ids",
            "attacked_explanation_ids",
            "attacked_action_option_ids",
            "reverse_signals",
            "surviving_claims",
            "repair_required",
        ),
    )
    _require_nonempty_text(red_team.get("strongest_attack"), field="red_team.strongest_attack")
    for field in (
        "attacked_evidence_refs",
        "attacked_claim_ids",
        "attacked_mechanism_ids",
        "reverse_signals",
        "surviving_claims",
    ):
        if not isinstance(red_team.get(field), list) or not red_team[field]:
            raise ValueError(f"red_team.{field} must be a non-empty list")
    for field in ("attacked_explanation_ids", "attacked_action_option_ids"):
        if not isinstance(red_team.get(field), list):
            raise ValueError(f"red_team.{field} must be a list")
    if not isinstance(red_team.get("repair_required"), bool):
        raise ValueError("red_team.repair_required must be boolean")
    if red_team["repair_required"]:
        repair = red_team.get("repair")
        if (
            not isinstance(repair, Mapping)
            or repair.get("verification_status") != "verified"
            or not isinstance(repair.get("repaired_claim_ids"), list)
            or not repair["repaired_claim_ids"]
            or not isinstance(repair.get("repair_evidence_refs"), list)
            or not repair["repair_evidence_refs"]
            or not isinstance(repair.get("verification_evidence_refs"), list)
            or not repair["verification_evidence_refs"]
        ):
            raise ValueError("red_team repair is required but not verified")
        _require_nonempty_text(
            repair.get("repair_id"), field="red_team.repair.repair_id"
        )
        _require_nonempty_text(
            repair.get("description"), field="red_team.repair.description"
        )
        verified_at = parse_instant(
            repair.get("verified_at"), field="red_team.repair.verified_at"
        )
        problem = packet.get("problem_contract")
        evidence_cutoff = parse_instant(
            problem.get("evidence_cutoff")
            if isinstance(problem, Mapping)
            else None,
            field="problem_contract.evidence_cutoff",
        )
        if verified_at > evidence_cutoff:
            raise ValueError(
                "red_team repair verification is after evidence cutoff"
            )
    stance = _require_dynamic_gate(
        packet,
        "stance_pair",
        (
            "neutrality_key",
            "position",
            "counterposition",
            "preferred",
            "selection_reason",
            "switch_conditions",
            "evidence_invariant",
        ),
    )
    _require_nonempty_text(stance.get("neutrality_key"), field="stance_pair.neutrality_key")
    for side in ("position", "counterposition"):
        side_value = stance.get(side)
        if not isinstance(side_value, Mapping):
            raise ValueError(f"stance_pair.{side} must be an object")
        _require_nonempty_text(side_value.get("claim"), field=f"stance_pair.{side}.claim")
        if side_value.get("stance_id") != side:
            raise ValueError(f"stance_pair.{side}.stance_id differs from its role")
        _require_nonempty_text(
            side_value.get("explanation_id"),
            field=f"stance_pair.{side}.explanation_id",
        )
        if not isinstance(side_value.get("support_refs"), list):
            raise ValueError(f"stance_pair.{side}.support_refs must be a list")
    if stance.get("preferred") not in {"position", "counterposition", "undecided"}:
        raise ValueError("stance_pair.preferred is invalid")
    _require_nonempty_text(stance.get("selection_reason"), field="stance_pair.selection_reason")
    if not isinstance(stance.get("switch_conditions"), list) or not stance["switch_conditions"]:
        raise ValueError("stance_pair.switch_conditions must be a non-empty list")
    if stance.get("evidence_invariant") is not True:
        raise ValueError("stance_pair.evidence_invariant must be true")
    preferred = stance.get("preferred")
    verdict = packet.get("verdict")
    judgment_kind = (
        verdict.get("judgment_kind") if isinstance(verdict, Mapping) else None
    )
    if preferred in {"position", "counterposition"}:
        answer = packet.get("answer")
        selected = stance.get(preferred)
        if (
            not isinstance(answer, Mapping)
            or not isinstance(selected, Mapping)
            or answer.get("direct_answer") != selected.get("claim")
        ):
            raise ValueError(
                "answer.direct_answer differs from the preferred stance claim"
            )
        if judgment_kind == "best-current" and isinstance(verdict, Mapping):
            current_best = verdict.get("current_best_judgment")
            if not isinstance(current_best, Mapping):
                raise ValueError("best-current verdict lacks current_best_judgment")
            if (
                selected.get("explanation_id")
                == current_best.get("best_explanation_id")
                and not (
                    current_best.get("proposition")
                    == selected.get("claim")
                    == answer.get("direct_answer")
                )
            ):
                raise ValueError(
                    "current-best proposition differs from selected stance and direct answer"
                )
            if answer.get("withdrawal_conditions") != current_best.get(
                "withdrawal_conditions"
            ):
                raise ValueError(
                    "answer withdrawal conditions differ from current-best judgment"
                )
            if answer.get("action_ceiling") != current_best.get("action_ceiling"):
                raise ValueError(
                    "answer action ceiling differs from current-best judgment"
                )
    elif preferred == "undecided":
        answer = packet.get("answer")
        non_decidability = (
            verdict.get("non_decidability")
            if isinstance(verdict, Mapping)
            else None
        )
        if (
            not isinstance(answer, Mapping)
            or not isinstance(non_decidability, Mapping)
            or answer.get("direct_answer")
            != non_decidability.get("public_proposition")
        ):
                raise ValueError(
                    "undecided answer differs from canonical non-decidability proposition"
                )
        validate_partial_explanation_order(verdict)
    if judgment_kind == "best-current" and preferred == "undecided":
        raise ValueError(
            "XK10 best-current judgment requires a selected reader stance"
        )
    if judgment_kind == "best-current" and isinstance(verdict, Mapping):
        current_best = verdict.get("current_best_judgment")
        if not isinstance(current_best, Mapping) or current_best.get("strength") in {
            None,
            "undecided",
        }:
            raise ValueError("best-current judgment cannot use undecided strength")
    if judgment_kind == "non-decidability" and preferred != "undecided":
        raise ValueError("XK10 non-decidability requires an undecided reader stance")
    action_ranking = packet.get("action_ranking")
    if isinstance(action_ranking, Mapping):
        if action_ranking.get("selection_status") in {"recommended", "selected"}:
            local_verdicts = {
                item.get("claim_id"): item
                for item in verdict.get("claim_verdicts", [])
                if isinstance(item, Mapping)
            }
            supporting = action_ranking.get("supporting_claim_ids")
            if not isinstance(supporting, list) or not supporting or any(
                claim_id not in local_verdicts
                or local_verdicts[claim_id].get("status") not in {"locked", "bounded"}
                or local_verdicts[claim_id].get("blocking_claim_ids")
                or local_verdicts[claim_id].get("blocking_evidence_refs")
                for claim_id in supporting
            ):
                raise ValueError("action recommendation depends on an unsupported local judgment")
        problem = packet.get("problem_contract")
        evidence_cutoff = (
            problem.get("evidence_cutoff")
            if isinstance(problem, Mapping)
            else None
        )
        cutoff = parse_instant(
            evidence_cutoff,
            field="problem_contract.evidence_cutoff",
        )
        for option in action_ranking.get("options", []):
            if not isinstance(option, Mapping) or option.get("authorized") is not True:
                continue
            interval = option.get("validity_interval")
            if not isinstance(interval, Mapping):
                raise ValueError(
                    "authorized option requires a validity interval"
                )
            starts_at = parse_instant(
                interval.get("starts_at"),
                field="action validity_interval.starts_at",
            )
            ends_at = parse_instant(
                interval.get("ends_at"),
                field="action validity_interval.ends_at",
            )
            if not starts_at <= cutoff < ends_at:
                raise ValueError(
                    "authorization validity interval does not cover evidence cutoff"
                )
    forecast = _require_dynamic_gate(
        packet,
        "forecast",
        (
            "target",
            "deadline",
            "baseline",
            "conditional_paths",
            "early_signals",
            "reverse_signals",
            "numeric_probability",
        ),
    )
    for field in ("target", "deadline", "baseline"):
        _require_nonempty_text(forecast.get(field), field=f"forecast.{field}")
    for field in ("conditional_paths", "early_signals", "reverse_signals"):
        if not isinstance(forecast.get(field), list) or not forecast[field]:
            raise ValueError(f"forecast.{field} must be a non-empty list")
    probability = forecast.get("numeric_probability")
    if probability is not None:
        if not isinstance(probability, (int, float)) or isinstance(probability, bool):
            raise ValueError("forecast.numeric_probability must be a number or null")
        if not 0 <= probability <= 1:
            raise ValueError("forecast.numeric_probability must be between zero and one")
        calibration = forecast.get("calibration_basis")
        if not isinstance(calibration, Mapping):
            raise ValueError(
                "forecast.calibration_basis must be a structured calibration record"
            )
        for field in (
            "description",
            "reference_class",
            "measurement",
            "unit",
            "generation_method",
        ):
            _require_nonempty_text(
                calibration.get(field),
                field=f"forecast.calibration_basis.{field}",
            )
        if calibration.get("method") != "empirical-frequency":
            raise ValueError(
                "forecast.calibration_basis method is not verifiable"
            )
        sample_size = calibration.get("sample_size")
        positive_outcomes = calibration.get("positive_outcomes")
        observed_frequency = calibration.get("observed_frequency")
        if (
            not isinstance(sample_size, int)
            or isinstance(sample_size, bool)
            or sample_size < 1
            or not isinstance(positive_outcomes, int)
            or isinstance(positive_outcomes, bool)
            or not 0 <= positive_outcomes <= sample_size
            or not isinstance(observed_frequency, (int, float))
            or isinstance(observed_frequency, bool)
        ):
            raise ValueError(
                "forecast.calibration_basis empirical counts are invalid"
            )
        recomputed_frequency = positive_outcomes / sample_size
        if abs(float(observed_frequency) - recomputed_frequency) > 1e-12:
            raise ValueError(
                "forecast.calibration_basis observed frequency does not match its sample"
            )
        if abs(float(probability) - recomputed_frequency) > 1e-12:
            raise ValueError(
                "forecast.numeric_probability does not match its calibration basis"
            )
        source_refs = calibration.get("source_refs")
        retrieval = packet.get("retrieval")
        source_ids = {
            source.get("source_id")
            for source in (
                retrieval.get("sources", [])
                if isinstance(retrieval, Mapping)
                else []
            )
            if isinstance(source, Mapping)
        }
        if (
            not isinstance(source_refs, list)
            or not source_refs
            or len(source_refs) != len(set(source_refs))
            or not set(source_refs).issubset(source_ids)
        ):
            raise ValueError(
                "forecast.calibration_basis source refs do not resolve"
            )


def _validate_directional_evidence(
    retrieval: Mapping[str, Any],
    *,
    source_ids: set[str],
    queries: list[Any],
) -> None:
    directional = retrieval.get("directional_evidence")
    if directional is None:
        if retrieval.get("saturation_status") == "evidence_saturated":
            raise ValueError(
                "evidence_saturated retrieval requires event-derived directional_evidence"
            )
        return
    if not isinstance(directional, list) or len(directional) != len(
        FIVE_DIRECTION_QUERY_DIRECTIONS
    ):
        raise ValueError("retrieval directional_evidence must cover five directions")

    source_by_id = {
        source.get("source_id"): source
        for source in retrieval.get("sources", [])
        if isinstance(source, Mapping) and isinstance(source.get("source_id"), str)
    }
    assessment_by_source = {
        assessment.get("source_id"): assessment
        for assessment in retrieval.get("assessments", [])
        if isinstance(assessment, Mapping)
        and isinstance(assessment.get("source_id"), str)
    }
    query_by_direction = {
        query.get("direction"): query
        for query in queries
        if isinstance(query, Mapping) and isinstance(query.get("direction"), str)
    }
    directions: set[str] = set()
    seen_information: set[tuple[str, str]] = set()
    all_source_ids: set[str] = set()
    all_content_hashes: set[str] = set()
    all_independence_identities: set[str] = set()
    directions_with_new_information = 0

    for index, record in enumerate(directional):
        if not isinstance(record, Mapping) or set(record) != DIRECTIONAL_EVIDENCE_FIELDS:
            raise ValueError(
                f"retrieval directional_evidence fields are invalid: {index}"
            )
        direction = record.get("direction")
        if direction not in FIVE_DIRECTION_QUERY_DIRECTIONS or direction in directions:
            raise ValueError("retrieval directional_evidence directions are invalid")
        directions.add(direction)
        for field in ("search_event_id", "stop_boundary"):
            _require_nonempty_text(
                record.get(field),
                field=f"retrieval directional_evidence[{index}].{field}",
            )
        stop_boundary = record["stop_boundary"]
        expected_stop_reason = (
            "next_direction_search"
            if stop_boundary.startswith("next_search:")
            else "turn_completed"
            if stop_boundary == "turn.completed"
            else None
        )
        if record.get("stop_reason") != expected_stop_reason:
            raise ValueError("retrieval directional_evidence stop reason is invalid")

        urls = record.get("source_urls")
        ids = record.get("source_ids")
        if (
            not isinstance(urls, list)
            or not urls
            or not all(isinstance(item, str) and item for item in urls)
            or len(urls) != len(set(urls))
            or not isinstance(ids, list)
            or not ids
            or not all(isinstance(item, str) and item for item in ids)
            or len(ids) != len(set(ids))
            or not set(ids).issubset(source_ids)
        ):
            raise ValueError("retrieval directional_evidence source bindings are invalid")
        query = query_by_direction.get(direction)
        if not isinstance(query, Mapping) or query.get("result_source_ids") != ids:
            raise ValueError(
                "retrieval directional_evidence differs from query result bindings"
            )
        sources = [source_by_id[source_id] for source_id in ids]
        expected_urls = [source.get("url") for source in sources]
        if urls != expected_urls:
            raise ValueError(
                "retrieval directional_evidence differs from source URL bindings"
            )
        content_hashes = [source.get("content_sha256") for source in sources]
        independence_identities = [
            assessment_by_source.get(source_id, {}).get("independence_identity")
            for source_id in ids
        ]
        if not all(
            isinstance(value, str)
            and re.fullmatch(r"[0-9a-f]{64}", value) is not None
            for value in content_hashes
        ) or not all(
            isinstance(value, str) and value for value in independence_identities
        ):
            raise ValueError(
                "retrieval directional_evidence source identities are invalid"
            )
        expected_counts = {
            "distinct_url_count": len(set(urls)),
            "distinct_source_count": len(set(ids)),
            "distinct_content_count": len(set(content_hashes)),
            "distinct_independence_count": len(set(independence_identities)),
        }
        if any(record.get(field) != value for field, value in expected_counts.items()):
            raise ValueError("retrieval directional_evidence counts are invalid")
        trusted_indices = {
            index
            for index, source_id in enumerate(ids)
            if has_bound_host_observation(source_by_id[source_id])
        }
        information = {
            (content_hashes[index], independence_identities[index])
            for index in trusted_indices
        }
        expected_new_information = len(information - seen_information)
        if record.get("new_information_count") != expected_new_information:
            raise ValueError(
                "retrieval directional_evidence information increment is invalid"
            )
        seen_information.update(information)
        all_source_ids.update(ids[index] for index in trusted_indices)
        all_content_hashes.update(content_hashes[index] for index in trusted_indices)
        all_independence_identities.update(
            independence_identities[index] for index in trusted_indices
        )
        if expected_new_information:
            directions_with_new_information += 1

    if directions != FIVE_DIRECTION_QUERY_DIRECTIONS:
        raise ValueError("retrieval directional_evidence does not cover five directions")
    if retrieval.get("saturation_status") == "evidence_saturated":
        if (
            len(all_source_ids) < 2
            or len(all_content_hashes) < 2
            or len(all_independence_identities) < 2
            or directions_with_new_information < 2
        ):
            raise ValueError(
                "evidence_saturated retrieval lacks independent directional evidence"
            )
        if not retrieval.get("remaining_unknowns"):
            raise ValueError(
                "evidence_saturated retrieval must retain observed-scope unknowns"
            )


def validate_retrieval_contract(packet: Mapping[str, Any], *, mode: str) -> None:
    retrieval = packet.get("retrieval")
    if not isinstance(retrieval, Mapping):
        raise ValueError("retrieval must be an object")
    for field in ("queries", "sources", "assessments", "remaining_unknowns"):
        if not isinstance(retrieval.get(field), list):
            raise ValueError(f"retrieval.{field} must be a list")
    queries = retrieval["queries"]
    problem = packet.get("problem_contract")
    profile = problem.get("retrieval_profile") if isinstance(problem, Mapping) else None
    dynamic = packet.get("dynamic_applicability") == "applicable"
    if mode == "open-world" and not queries:
        raise ValueError("open-world retrieval requires a query frontier")
    source_ids = {
        source.get("source_id")
        for source in retrieval["sources"]
        if isinstance(source, Mapping)
    }
    source_ids.discard(None)
    if len(source_ids) != len(retrieval["sources"]):
        raise ValueError("retrieval sources require unique non-empty source_id values")
    if mode == "closed-input":
        for source in retrieval["sources"]:
            if (
                isinstance(source, Mapping)
                and source.get("origin") not in CLOSED_INPUT_ORIGINS
            ):
                raise ValueError(
                    f"closed-input rejects external source: {source['source_id']}"
                )
    for source in retrieval["sources"]:
        if isinstance(source, Mapping):
            validate_external_source_metadata(dict(source))
    if mode == "closed-input":
        user_materials: list[dict[str, str]] = []
        for source in retrieval["sources"]:
            if not isinstance(source, Mapping) or source.get("origin") not in {
                "user",
                "user_material",
                "provided",
            }:
                continue
            content = source.get("content")
            if not isinstance(content, str) or not content:
                raise ValueError(
                    "closed-input user material requires frozen non-empty content"
                )
            observed_hash = sha256_text(content)
            if source.get("content_sha256") != observed_hash:
                raise ValueError(
                    "closed-input user material content hash is missing or invalid"
                )
            user_materials.append(
                {
                    "source_id": str(source["source_id"]),
                    "content_sha256": observed_hash,
                }
            )
        if not user_materials:
            raise ValueError(
                "closed-input cannot invent user_material from an empty material set"
            )
        manifest = retrieval.get("frozen_material_manifest")
        expected_materials = sorted(
            user_materials, key=lambda item: item["source_id"]
        )
        if (
            not isinstance(manifest, Mapping)
            or manifest.get("materials") != expected_materials
            or manifest.get("manifest_sha256") != sha256_json(expected_materials)
        ):
            raise ValueError(
                "closed-input frozen material manifest differs from user content hashes"
            )

    # A packet must carry exactly one independent assessment for every source.
    # The disk materializer repeats this check after normalisation; doing it at
    # the packet seam prevents a malformed packet from reaching XK2 first.
    assessment_ids: list[str] = []
    for index, assessment in enumerate(retrieval["assessments"]):
        if not isinstance(assessment, Mapping):
            raise ValueError(f"retrieval.assessments[{index}] must be an object")
        source_id = assessment.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise ValueError(
                f"retrieval.assessments[{index}].source_id must be non-empty"
            )
        if source_id in assessment_ids:
            raise ValueError(f"duplicate source assessment: {source_id}")
        if source_id not in source_ids:
            raise ValueError(f"assessment has unknown source_id: {source_id}")
        assessment_ids.append(source_id)
        for field in (
            "authority",
            "independence",
            "freshness",
            "relevance",
            "verdict",
            "independence_identity",
        ):
            _require_nonempty_text(
                assessment.get(field),
                field=f"retrieval.assessments[{index}].{field}",
            )
        for field in ("limitations", "cannot_prove"):
            values = assessment.get(field)
            if not isinstance(values, list) or (
                field == "cannot_prove" and not values
            ) or not all(isinstance(item, str) and item.strip() for item in values):
                raise ValueError(
                    f"source assessment {field} must be "
                    f"{'non-empty ' if field == 'cannot_prove' else ''}text: {source_id}"
                )
        validate_source_assessment_payload(
            dict(assessment),
            source_ids={str(item) for item in source_ids if isinstance(item, str)},
            source_id=source_id,
            require_provenance=(
                mode == "open-world"
                and dynamic
                and profile == "five-direction"
            ),
        )
    if set(assessment_ids) != source_ids:
        missing = sorted(source_ids - set(assessment_ids))
        extra = sorted(set(assessment_ids) - source_ids)
        raise ValueError(
            "one separate assessment is required per source: "
            f"missing={missing}, extra={extra}"
        )
    query_ids: set[str] = set()
    bound_source_ids: set[Any] = set()
    allowed_statuses = {
        "executed",
        "saturated",
        "capability_limited",
        "not_applicable",
    }
    evidence_cutoff = packet.get("runtime_binding", {}).get("evidence_cutoff")
    cutoff = (
        parse_instant(evidence_cutoff, field="evidence_cutoff")
        if isinstance(evidence_cutoff, str)
        else None
    )
    for index, query in enumerate(queries):
        if not isinstance(query, Mapping):
            raise ValueError(f"retrieval.queries[{index}] must be an object")
        for field in ("query_id", "direction", "query", "status"):
            _require_nonempty_text(
                query.get(field), field=f"retrieval.queries[{index}].{field}"
            )
        query_id = query["query_id"]
        if query_id in query_ids:
            raise ValueError(f"duplicate retrieval query_id: {query_id}")
        query_ids.add(query_id)
        status = query["status"]
        if status not in allowed_statuses:
            raise ValueError("retrieval query status is invalid")
        if status in {"saturated", "capability_limited", "not_applicable"}:
            _require_nonempty_text(
                query.get("stop_reason"),
                field=f"retrieval.queries[{index}].stop_reason",
            )
        result_source_ids = query.get("result_source_ids")
        if not isinstance(result_source_ids, list) or not all(
            isinstance(source_id, str) and source_id for source_id in result_source_ids
        ) or len(result_source_ids) != len(set(result_source_ids)):
            raise ValueError("retrieval query result_source_ids must be a unique list")
        if not set(result_source_ids).issubset(source_ids):
            raise ValueError("retrieval query result source does not resolve")
        if status == "saturated" and not result_source_ids:
            raise ValueError(
                "saturated query requires an auditable result; use capability_limited for a capability gap"
            )
        bound_source_ids.update(result_source_ids)
        executed_at = query.get("executed_at")
        if status in {"executed", "saturated", "capability_limited"}:
            if not isinstance(executed_at, str) or not executed_at:
                raise ValueError("retrieval executed query requires executed_at")

            executed = parse_instant(
                executed_at,
                field="retrieval query executed_at",
            )
            if cutoff is not None and executed > cutoff:
                raise ValueError("retrieval query executed_at is after evidence cutoff")
        elif executed_at is not None:
            raise ValueError("not_applicable retrieval query cannot claim execution")
        if status in {"capability_limited", "not_applicable"} and result_source_ids:
            raise ValueError(
                "non-executed retrieval query cannot bind result sources"
            )
        direction = query.get("direction")
        if direction not in QUERY_DIRECTIONS:
            raise ValueError(f"retrieval query direction is invalid: {direction}")
    allowed_saturation = {
        "bounded_saturation",
        "evidence_saturated",
        "authority_exhausted",
        "capability_limited",
        "source_internal_only",
    }
    if retrieval.get("saturation_status") not in allowed_saturation:
        raise ValueError("retrieval saturation_status is invalid")
    _validate_directional_evidence(
        retrieval,
        source_ids={item for item in source_ids if isinstance(item, str)},
        queries=queries,
    )
    capability_limited_queries = [
        query for query in queries if query.get("status") == "capability_limited"
    ]
    if capability_limited_queries:
        _require_nonempty_text(
            retrieval.get("capability_gap"), field="retrieval.capability_gap"
        )
    missing_query_bindings = sorted(source_ids - bound_source_ids)
    if missing_query_bindings:
        raise ValueError(
            "retrieval source is not bound to an executed query: "
            + missing_query_bindings[0]
        )
    if mode != "open-world":
        return
    # Static definition/translation/tool questions are explicitly exempt from
    # real-world retrieval and three-order inference.  Their source-internal
    # query is still retained as a boundary receipt.
    if not dynamic:
        return

    by_direction: dict[str, list[Mapping[str, Any]]] = {}
    for query in queries:
        by_direction.setdefault(str(query.get("direction")), []).append(query)

    if profile == "five-direction":
        missing = sorted(FIVE_DIRECTION_QUERY_DIRECTIONS - set(by_direction))
        if missing:
            raise ValueError(
                "five-direction retrieval is incomplete; missing directions: "
                + ", ".join(missing)
            )
        failed = sorted(
            direction
            for direction in FIVE_DIRECTION_QUERY_DIRECTIONS
            if not any(
                query.get("status") in QUERY_EXECUTED_STATES
                for query in by_direction[direction]
            )
        )
        if failed:
            raise ValueError(
                "five-direction retrieval has no attempted query: "
                + ", ".join(failed)
            )
    elif profile == "authority-first":
        if not any(
            query.get("direction") in {"authoritative_definition", "current_baseline"}
            and query.get("status") in QUERY_EXECUTED_STATES
            for query in queries
        ):
            raise ValueError(
                "authority-first retrieval requires an authoritative or first-party query"
            )
    elif profile == "closed-input":
        raise ValueError("open-world dynamic retrieval cannot use closed-input profile")

    if retrieval["sources"]:
        if not any(
            query.get("status") in {"executed", "saturated"}
            for query in queries
        ):
            raise ValueError("open-world sources require an executed query receipt")
        if retrieval.get("saturation_status") in {
            "capability_limited",
            "source_internal_only",
        }:
            raise ValueError("open-world retrieved sources have an invalid saturation state")
        return
    if packet.get("dynamic_applicability") == "not_applicable":
        if retrieval.get("saturation_status") != "source_internal_only" or any(
            query.get("status") != "not_applicable" for query in queries
        ):
            raise ValueError(
                "static source-internal retrieval must be explicitly marked not_applicable"
            )
        return
    _require_nonempty_text(
        retrieval.get("capability_gap"), field="retrieval.capability_gap"
    )
    if retrieval.get("saturation_status") != "capability_limited":
        raise ValueError("source-free open-world retrieval must be capability_limited")
    if not retrieval["remaining_unknowns"]:
        raise ValueError("source-free open-world retrieval must retain unknowns")
    if any(query.get("status") != "capability_limited" for query in queries):
        raise ValueError("source-free open-world queries must record a failed capability state")


def validate_provenance(packet: Mapping[str, Any], *, mode: str) -> None:
    """Reject provenance-free factual strings and closed-input leakage."""

    facts = packet.get("facts")
    if not isinstance(facts, Mapping):
        raise ValueError("provenance requires a facts object")
    for bucket in FACT_BUCKETS:
        entries = facts.get(bucket)
        if not isinstance(entries, list):
            raise ValueError(f"provenance requires facts.{bucket} to be a list")
        for index, entry in enumerate(entries):
            if not isinstance(entry, Mapping):
                raise ValueError(
                    f"provenance requires an identity and refs at facts.{bucket}[{index}]"
                )
            text = entry.get("text")
            identity = entry.get("identity")
            refs = entry.get("source_refs", entry.get("evidence_refs"))
            if not isinstance(text, str) or not text.strip() or identity not in FACT_IDENTITIES:
                raise ValueError(
                    f"provenance is incomplete at facts.{bucket}[{index}]"
                )
            if not isinstance(refs, list):
                raise ValueError(
                    f"provenance refs are missing at facts.{bucket}[{index}]"
                )
            if identity not in {"unknown", "v8.3_definition"} and not refs:
                raise ValueError(
                    f"provenance refs are empty at facts.{bucket}[{index}]"
                )

    cases = packet.get("case_ledger")
    if not isinstance(cases, Mapping):
        raise ValueError("provenance requires a case_ledger object")
    for index, case in enumerate(cases.get("cases", [])):
        if not isinstance(case, Mapping) or case.get("kind") not in CASE_KINDS:
            raise ValueError(f"provenance case identity is invalid at case_ledger.cases[{index}]")
        if case.get("kind") in {"documented_real_case", "user_material_case"}:
            refs = case.get("source_refs")
            if not isinstance(refs, list) or not refs:
                raise ValueError(f"provenance case source refs are missing at case_ledger.cases[{index}]")
    _validate_case_source_origins(packet)

    framework_gap = packet.get("framework_gap")
    registered_provisional_ids = {
        identifier
        for candidate in (
            framework_gap.get("candidates", [])
            if isinstance(framework_gap, Mapping)
            else []
        )
        if isinstance(candidate, Mapping)
        for identifier in candidate.get("provisional_variable_ids", [])
        if isinstance(identifier, str)
    }
    for path, value in _walk(packet):
        if not isinstance(value, str):
            continue
        for token in PROVISIONAL_TOKEN.findall(value):
            if token not in registered_provisional_ids:
                raise ValueError(
                    f"unregistered XK-PROV token cannot enter this run: {token}"
                )
            if not path.startswith("$.framework_gap"):
                raise ValueError(
                    f"XK-PROV token cannot feed current judgment or authorization: {token}"
                )

    for path, value in _walk(packet):
        if not isinstance(value, Mapping):
            continue
        if _externally_redefines_v83(value):
            raise ValueError(
                f"external evidence cannot redefine v8.3 at {path}"
            )
        identity = value.get("identity") or value.get("fact_identity") or value.get("kind")
        if identity in FACT_IDENTITIES:
            if not isinstance(value.get("source_refs", value.get("evidence_refs", [])), list):
                raise ValueError(f"{path} with identity {identity} lacks source/evidence refs")
            if (
                mode == "closed-input"
                and identity not in CLOSED_ALLOWED_IDENTITIES
                and not (
                    identity in {"conditional_scenario", "structural_analogy"}
                    and not value.get("source_refs")
                )
            ):
                raise ValueError(f"closed-input rejects {identity} at {path}")
        if mode == "closed-input" and value.get("origin") == "external":
            raise ValueError(f"closed-input rejects external origin at {path}")


def _validate_red_team_repair_binding(
    red_team: Mapping[str, Any],
    *,
    evidence_ledger: Mapping[str, Any],
    claim_ids: set[str],
) -> None:
    if red_team.get("repair_required") is not True:
        return
    repair = red_team.get("repair")
    if not isinstance(repair, Mapping):
        raise ValueError("red-team repair binding requires a repair object")

    evidence_by_id = {
        record.get("evidence_id"): record
        for record in evidence_ledger.get("evidence", [])
        if isinstance(record, Mapping)
        and isinstance(record.get("evidence_id"), str)
    }
    attacked_evidence_refs = red_team.get("attacked_evidence_refs", [])
    surviving_claims = red_team.get("surviving_claims", [])
    if (
        not isinstance(attacked_evidence_refs, list)
        or not attacked_evidence_refs
        or any(
            not isinstance(reference, str) or reference not in evidence_by_id
            for reference in attacked_evidence_refs
        )
        or not isinstance(surviving_claims, list)
        or not surviving_claims
        or any(not isinstance(claim_id, str) for claim_id in surviving_claims)
    ):
        raise ValueError("red-team evidence reference does not resolve")
    attacked_claim_ids = {
        evidence_by_id[reference].get("claim_id")
        for reference in attacked_evidence_refs
    }
    required_claim_ids = attacked_claim_ids | set(surviving_claims)
    if None in required_claim_ids or not required_claim_ids.issubset(claim_ids):
        raise ValueError("red-team repair claim does not resolve")
    repaired_claim_ids = repair.get("repaired_claim_ids", [])
    if (
        not isinstance(repaired_claim_ids, list)
        or len(repaired_claim_ids) != len(set(repaired_claim_ids))
        or set(repaired_claim_ids) != required_claim_ids
    ):
        if not set(repaired_claim_ids).intersection(required_claim_ids):
            raise ValueError(
                "red_team repair does not address an attacked surviving claim; "
                "red-team repair claims differ from attacked and surviving claims"
            )
        raise ValueError(
            "red-team repair claims differ from attacked and surviving claims"
        )

    allowed_evidence_refs = set(attacked_evidence_refs)
    for edge in evidence_ledger.get("support_edges", []):
        evidence_id = edge.get("evidence_id") if isinstance(edge, Mapping) else None
        evidence_record = evidence_by_id.get(evidence_id)
        if (
            isinstance(edge, Mapping)
            and edge.get("claim_id") in required_claim_ids
            and isinstance(evidence_id, str)
            and isinstance(evidence_record, Mapping)
            and evidence_record.get("claim_id") == edge.get("claim_id")
        ):
            allowed_evidence_refs.add(edge["evidence_id"])
    for field, label in (
        ("repair_evidence_refs", "repair evidence"),
        ("verification_evidence_refs", "verification evidence"),
    ):
        references = repair.get(field, [])
        if (
            not isinstance(references, list)
            or not references
            or len(references) != len(set(references))
            or any(
                not isinstance(reference, str)
                or reference not in evidence_by_id
                or reference not in allowed_evidence_refs
                for reference in references
            )
        ):
            if field == "verification_evidence_refs":
                raise ValueError(
                    "red_team repair verification does not cover its repair evidence; "
                    "red-team verification evidence is unrelated to attacked or repaired claims"
                )
            raise ValueError(
                f"red-team {label} is unrelated to attacked or repaired claims"
            )

    outcomes = repair.get("claim_outcomes")
    if not isinstance(outcomes, list) or any(
        not isinstance(outcome, Mapping) for outcome in outcomes
    ):
        raise ValueError("red-team repair outcomes differ from repaired claims")
    outcome_claim_ids = [outcome.get("claim_id") for outcome in outcomes]
    if (
        len(outcome_claim_ids) != len(set(outcome_claim_ids))
        or set(outcome_claim_ids) != set(repaired_claim_ids)
    ):
        raise ValueError("red-team repair outcomes differ from repaired claims")

    dispositions = {"downgrade", "withdraw", "replace", "retain-with-bounds"}
    for outcome in outcomes:
        claim_id = outcome["claim_id"]
        disposition = outcome.get("disposition")
        replacement_claim_id = outcome.get("replacement_claim_id")
        bounds = outcome.get("bounds")
        if disposition not in dispositions:
            raise ValueError(
                f"red-team repair outcome has invalid disposition: {claim_id}"
            )
        if disposition == "replace":
            if (
                not isinstance(replacement_claim_id, str)
                or replacement_claim_id == claim_id
                or replacement_claim_id not in claim_ids
            ):
                raise ValueError(
                    "red-team replace outcome requires a different registered claim"
                )
        elif replacement_claim_id is not None:
            raise ValueError(
                "red-team only replace outcome may name a replacement claim"
            )
        if not isinstance(bounds, list) or any(
            not isinstance(bound, str) or not bound.strip() for bound in bounds
        ):
            raise ValueError("red-team repair outcome bounds must be text")
        if disposition == "retain-with-bounds" and not bounds:
            raise ValueError(
                "red-team retain-with-bounds outcome requires explicit bounds"
            )


def validate_answer_basis_references(
    packet: Mapping[str, Any],
    *,
    evidence_ledger: Mapping[str, Any] | None = None,
) -> None:
    """Check answer identities without granting source or execution authority."""

    graph = packet.get("claim_mechanism_graph", {})
    if not isinstance(graph, Mapping):
        graph = {}
    evidence = evidence_ledger if evidence_ledger is not None else packet.get("evidence", {})
    if not isinstance(evidence, Mapping):
        evidence = {}
    allowed: set[str] = set()
    for container, field, key in (
        (evidence, "claims", "claim_id"), (evidence, "evidence", "evidence_id"),
        (graph, "claims", "claim_id"), (graph, "evidence", "evidence_id"),
        (graph, "mechanisms", "mechanism_id"),
    ):
        for record in container.get(field, []):
            if isinstance(record, Mapping) and isinstance(record.get(key), str):
                allowed.add(record[key])
    if evidence_ledger is None and "support_edges" not in evidence:
        for claim in evidence.get("claims", []):
            if isinstance(claim, Mapping) and isinstance(claim.get("claim_id"), str):
                for index, _support in enumerate(claim.get("support", []), start=1):
                    allowed.add(f"{claim['claim_id']}-e{index}")
    answer = packet.get("answer", {})
    references = answer.get("basis_refs", []) if isinstance(answer, Mapping) else None
    if (not isinstance(references, list)
            or any(not isinstance(ref, str) or not ref.strip() for ref in references)
            or len(references) != len(set(references))):
        raise ValueError("answer.basis_refs must be a unique array of nonempty identity strings")
    unresolved = sorted(set(references) - allowed)
    if unresolved:
        raise ValueError(
            "answer basis reference does not resolve at answer.basis_refs: "
            + ", ".join(unresolved)
            + "; use claim_id, evidence_id or mechanism_id; source_id is only a source reference"
        )
    verdict = packet.get("verdict")
    if not isinstance(verdict, Mapping) or verdict.get("judgment_kind") != "best-current":
        return
    current_best = verdict.get("current_best_judgment")
    explanations = {
        record.get("explanation_id"): record
        for record in graph.get("explanations", []) if isinstance(record, Mapping)
    }
    best = explanations.get(current_best.get("best_explanation_id")) if isinstance(current_best, Mapping) else None
    if not isinstance(best, Mapping):
        raise ValueError("central judgment basis has no best explanation")
    claims = set(best.get("claim_ids", []))
    mechanisms = set(best.get("mechanism_ids", []))
    edges = {
        (edge.get("claim_id"), edge.get("evidence_id"))
        for record in verdict.get("five_verdicts", []) if isinstance(record, Mapping)
        for edge in record.get("claim_evidence_edges", []) if isinstance(edge, Mapping)
        and edge.get("claim_id") in claims
    }
    if {claim for claim, _ in edges} != claims:
        raise ValueError("central judgment basis lacks an exact claim support edge")
    if set(references) != claims | mechanisms | {ref for _, ref in edges}:
        raise ValueError("central judgment basis differs from its exact claim support edges")


def validate_packet_references(
    packet: Mapping[str, Any],
    *,
    evidence_ledger: Mapping[str, Any],
    retrieval_index: Mapping[str, Any],
    repository_root: Path,
) -> None:
    anchor_index = read_json(
        Path(repository_root)
        / "references"
        / "source"
        / "v8.3"
        / "indexes"
        / "anchors.json"
    )
    source_anchor_ids = {
        *anchor_index.get("paragraphs", []),
        *anchor_index.get("tables", []),
    }
    source_ids = {
        record.get("source_id")
        for record in retrieval_index.get("sources", [])
        if isinstance(record, Mapping)
    }
    source_ids.discard(None)
    assessment_verdicts = {
        record.get("source_id"): record.get("assessment_verdict")
        for record in retrieval_index.get("sources", [])
        if isinstance(record, Mapping)
    }
    source_origins = {
        record.get("source_id"): record.get("origin")
        for record in retrieval_index.get("sources", [])
        if isinstance(record, Mapping)
    }
    packet_retrieval = packet.get("retrieval")
    packet_sources_by_id = {
        record.get("source_id"): record
        for record in (
            packet_retrieval.get("sources", [])
            if isinstance(packet_retrieval, Mapping)
            else []
        )
        if isinstance(record, Mapping) and isinstance(record.get("source_id"), str)
    }
    xk3_claim_by_id = {
        record.get("claim_id"): record
        for record in evidence_ledger.get("claims", [])
        if isinstance(record, Mapping)
        and isinstance(record.get("claim_id"), str)
    }
    xk3_claim_ids = set(xk3_claim_by_id)
    xk3_claim_ids.discard(None)
    xk3_evidence_by_id = {
        record.get("evidence_id"): record
        for record in evidence_ledger.get("evidence", [])
        if isinstance(record, Mapping)
        and isinstance(record.get("evidence_id"), str)
    }
    xk3_support_sources_by_claim: dict[Any, set[Any]] = {}
    xk3_support_sources_by_evidence: dict[Any, set[Any]] = {}
    for edge in evidence_ledger.get("support_edges", []):
        if not isinstance(edge, Mapping):
            continue
        xk3_support_sources_by_claim.setdefault(edge.get("claim_id"), set()).add(
            edge.get("source_id")
        )
        xk3_support_sources_by_evidence.setdefault(
            edge.get("evidence_id"), set()
        ).add(edge.get("source_id"))
    xk3_support_sources = {
        source_id
        for source_ids in xk3_support_sources_by_claim.values()
        for source_id in source_ids
    }
    xk3_support_sources.discard(None)
    graph = packet.get("claim_mechanism_graph", {})
    if not isinstance(graph, Mapping):
        graph = {}
    claim_ids = {
        record.get("claim_id")
        for record in evidence_ledger.get("claims", [])
        if isinstance(record, Mapping)
    } | {
        record.get("claim_id")
        for record in graph.get("claims", [])
        if isinstance(record, Mapping)
    }
    evidence_ids = {
        record.get("evidence_id")
        for record in evidence_ledger.get("evidence", [])
        if isinstance(record, Mapping)
    } | {
        record.get("evidence_id")
        for record in graph.get("evidence", [])
        if isinstance(record, Mapping)
    }
    mechanism_ids = {
        record.get("mechanism_id")
        for record in graph.get("mechanisms", [])
        if isinstance(record, Mapping)
    }
    claim_ids.discard(None)
    evidence_ids.discard(None)
    mechanism_ids.discard(None)
    allowed = claim_ids | evidence_ids | mechanism_ids

    graph_claims = {
        record.get("claim_id"): record
        for record in graph.get("claims", [])
        if isinstance(record, Mapping)
        and isinstance(record.get("claim_id"), str)
    }
    graph_claim_ids_by_evidence: dict[Any, set[Any]] = {}
    for graph_claim in graph_claims.values():
        for evidence_id in graph_claim.get("evidence_refs", []):
            graph_claim_ids_by_evidence.setdefault(evidence_id, set()).add(
                graph_claim.get("claim_id")
            )

    for claim_id, graph_claim in graph_claims.items():
        if claim_id not in xk3_claim_ids:
            raise ValueError(
                f"claim graph claim has no XK3 claim contract: {claim_id}"
            )
        xk3_claim = xk3_claim_by_id[claim_id]
        if graph_claim.get("statement") != xk3_claim.get("text"):
            raise ValueError(
                "claim graph statement differs from the frozen XK3 claim: "
                f"{claim_id}"
            )
        allowed_xk3_kinds = XK3_KINDS_BY_GRAPH_CLAIM_KIND.get(
            graph_claim.get("kind"), set()
        )
        if xk3_claim.get("kind") not in allowed_xk3_kinds:
            raise ValueError(
                "claim graph kind differs from the frozen XK3 claim identity: "
                f"{claim_id}"
            )
        if graph_claim.get("kind") == "authorization" and (
            xk3_claim.get("kind") != "authorization_boundary"
            or graph_claim.get("authorization_boundary")
            != xk3_claim.get("authorization_boundary")
        ):
            raise ValueError(
                "authorization tuple differs from frozen XK3 authorization boundary: "
                f"{claim_id}"
            )

    for record in graph.get("evidence", []):
        if not isinstance(record, Mapping):
            continue
        evidence_id = record.get("evidence_id")
        for source_id in record.get("source_refs", []):
            if (
                source_id not in xk3_support_sources
                or assessment_verdicts.get(source_id)
                not in ADMITTED_ASSESSMENT_VERDICTS
            ):
                raise ValueError(
                    "claim graph evidence has no admitted XK3 support edge: "
                    f"{evidence_id} -> {source_id}"
                )
        xk3_evidence_refs = record.get("xk3_evidence_refs")
        if not isinstance(xk3_evidence_refs, list) or not xk3_evidence_refs:
            raise ValueError(
                f"claim graph evidence has no exact XK3 evidence binding: {evidence_id}"
            )
        if any(reference not in xk3_evidence_by_id for reference in xk3_evidence_refs):
            raise ValueError(
                "claim graph evidence differs from its exact XK3 evidence binding: "
                f"{evidence_id}"
            )
        bound_entries = [xk3_evidence_by_id[reference] for reference in xk3_evidence_refs]
        bound_claim_ids = {entry.get("claim_id") for entry in bound_entries}
        bound_source_ids = {entry.get("source_id") for entry in bound_entries}
        if (
            bound_claim_ids != graph_claim_ids_by_evidence.get(evidence_id, set())
            or bound_source_ids != set(record.get("source_refs", []))
        ):
            raise ValueError(
                "claim graph evidence differs from its exact XK3 evidence binding: "
                f"{evidence_id}"
            )
        if record.get("identity") == "observed":
            factual_claim_ids = {
                claim_id
                for claim_id in bound_claim_ids
                if graph_claims.get(claim_id, {}).get("kind") == "factual"
            }
            if not factual_claim_ids or any(
                xk3_claim_by_id[claim_id].get("kind") != "external_fact"
                for claim_id in factual_claim_ids
            ):
                raise ValueError(
                    "observed claim graph evidence lacks an external-fact XK3 identity: "
                    f"{evidence_id}"
                )

    graph_evidence = {
        record.get("evidence_id"): record
        for record in graph.get("evidence", [])
        if isinstance(record, Mapping)
    }
    for claim in graph.get("claims", []):
        if not isinstance(claim, Mapping):
            continue
        claim_id = claim.get("claim_id")
        claim_support_sources = xk3_support_sources_by_claim.get(claim_id, set())
        for evidence_id in claim.get("evidence_refs", []):
            evidence_record = graph_evidence.get(evidence_id)
            if not isinstance(evidence_record, Mapping):
                continue
            for source_id in evidence_record.get("source_refs", []):
                if source_id not in claim_support_sources:
                    raise ValueError(
                        "claim graph evidence lacks a claim-specific XK3 support "
                        f"edge: {claim_id} -> {evidence_id} -> {source_id}"
                    )

    facts = packet.get("facts", {})
    for bucket in FACT_BUCKETS:
        for index, record in enumerate(facts.get(bucket, [])):
            if not isinstance(record, Mapping):
                continue
            identity = record.get("identity")
            source_refs = record.get("source_refs")
            if (
                identity == "v8.3_definition"
                and isinstance(source_refs, list)
                and not set(source_refs).issubset(source_anchor_ids)
            ):
                raise ValueError("source anchor does not resolve")
            if (
                identity != "v8.3_definition"
                and isinstance(source_refs, list)
                and not set(source_refs).issubset(source_ids)
            ):
                raise ValueError("fact source reference does not resolve")
            if identity != "v8.3_definition" and isinstance(source_refs, list):
                for source_id in source_refs:
                    origin = source_origins.get(source_id)
                    if identity == "external_fact" and origin != "external":
                        raise ValueError(
                            "fact identity differs from source origin: "
                            f"facts.{bucket}[{index}] -> {source_id} ({origin})"
                        )
                    if (
                        identity == "external_fact"
                        and not has_bound_host_observation(
                            packet_sources_by_id.get(source_id, {})
                        )
                    ):
                        raise ValueError(
                            "external fact source lacks a bound host observation: "
                            f"facts.{bucket}[{index}] -> {source_id}"
                        )
                    if identity == "user_material" and origin not in {
                        "user",
                        "user_material",
                        "provided",
                    }:
                        raise ValueError(
                            "fact identity differs from source origin: "
                            f"facts.{bucket}[{index}] -> {source_id} ({origin})"
                        )
                    verdict = assessment_verdicts.get(source_id)
                    if verdict not in ADMITTED_ASSESSMENT_VERDICTS:
                        raise ValueError(
                            "public fact source is non-admitted: "
                            f"facts.{bucket}[{index}] -> {source_id} ({verdict})"
                        )
            evidence_refs = record.get("evidence_refs")
            if identity in {"external_fact", "source_claim", "user_material"}:
                if not isinstance(evidence_refs, list) or not evidence_refs:
                    raise ValueError(
                        "public fact has no claim-specific XK3 evidence reference: "
                        f"facts.{bucket}[{index}]"
                    )
                for source_id in source_refs or []:
                    if not any(
                        source_id
                        in xk3_support_sources_by_claim.get(reference, set())
                        or source_id
                        in xk3_support_sources_by_evidence.get(reference, set())
                        for reference in evidence_refs
                    ):
                        raise ValueError(
                            "public fact source lacks a claim-specific XK3 support "
                            f"edge: facts.{bucket}[{index}] -> {source_id}"
                        )
            if isinstance(evidence_refs, list) and not set(evidence_refs).issubset(
                allowed
            ):
                raise ValueError("fact evidence reference does not resolve")
    case_ledger = packet.get("case_ledger", {})
    case_containers = (
        graph.get("cases", []),
        case_ledger.get("cases", []) if isinstance(case_ledger, Mapping) else [],
    )
    for cases in case_containers:
        for record in cases:
            if not isinstance(record, Mapping):
                continue
            case_id = record.get("case_id")
            source_refs = record.get("source_refs")
            claim_refs = record.get("tests_claim_ids")
            if not isinstance(source_refs, list) or not set(source_refs).issubset(
                source_ids
            ):
                raise ValueError("case source reference does not resolve")
            if not isinstance(claim_refs, list) or not claim_refs:
                raise ValueError(f"case has no tested claim binding: {case_id}")
            if record.get("kind") in {"conditional-scenario", "conditional_scenario"}:
                if source_refs:
                    raise ValueError(
                        f"conditional scenario has external source refs: {case_id}"
                    )
                if not record.get("conditions") or not record.get(
                    "stop_conditions"
                ):
                    raise ValueError(
                        f"conditional scenario requires conditions and stop conditions: {case_id}"
                    )
                continue
            for source_id in source_refs:
                case_kind = record.get("kind")
                origin = source_origins.get(source_id)
                if case_kind in {"documented-real", "documented_real_case"} and origin != "external":
                    raise ValueError(
                        f"case kind differs from source origin: {case_id} -> {source_id} ({origin})"
                    )
                if (
                    case_kind in {"documented-real", "documented_real_case"}
                    and not has_bound_host_observation(
                        packet_sources_by_id.get(source_id, {})
                    )
                ):
                    raise ValueError(
                        "documented real case source lacks a bound host observation: "
                        f"{case_id} -> {source_id}"
                    )
                if case_kind in {"user-material", "user_material_case"} and origin not in {
                    "user",
                    "user_material",
                    "provided",
                }:
                    raise ValueError(
                        f"case kind differs from source origin: {case_id} -> {source_id} ({origin})"
                    )
                verdict = assessment_verdicts.get(source_id)
                if verdict not in ADMITTED_ASSESSMENT_VERDICTS:
                    raise ValueError(
                        f"case source is non-admitted: {case_id} -> {source_id} "
                        f"({verdict})"
                    )
                supported_claim = next(
                    (
                        claim_id
                        for claim_id in claim_refs
                        if source_id
                        in xk3_support_sources_by_claim.get(claim_id, set())
                    ),
                    None,
                )
                if supported_claim is None:
                    raise ValueError(
                        "case source lacks a claim-specific XK3 support edge: "
                        f"{case_id} -> {claim_refs[0]} -> {source_id}"
                    )
            for claim_id in claim_refs:
                if not any(
                    source_id
                    in xk3_support_sources_by_claim.get(claim_id, set())
                    for source_id in source_refs
                ):
                    raise ValueError(
                        "case claim has no supporting source in XK3: "
                        f"{case_id} -> {claim_id}"
                    )

    countercase_containers = (
        graph.get("countercases", []),
        (
            case_ledger.get("countercases", [])
            if isinstance(case_ledger, Mapping)
            else []
        ),
    )
    for countercases in countercase_containers:
        for record in countercases:
            if not isinstance(record, Mapping):
                continue
            countercase_id = record.get("countercase_id")
            source_refs = record.get("source_refs")
            claim_refs = record.get("attacks_claim_ids")
            if not isinstance(source_refs, list) or not set(source_refs).issubset(
                source_ids
            ):
                raise ValueError("countercase source reference does not resolve")
            if not isinstance(claim_refs, list) or not claim_refs:
                raise ValueError(
                    f"countercase has no attacked claim binding: {countercase_id}"
                )
            for source_id in source_refs:
                verdict = assessment_verdicts.get(source_id)
                if verdict not in ADMITTED_ASSESSMENT_VERDICTS:
                    raise ValueError(
                        "countercase source is non-admitted: "
                        f"{countercase_id} -> {source_id} ({verdict})"
                    )
                supported_claim = next(
                    (
                        claim_id
                        for claim_id in claim_refs
                        if source_id
                        in xk3_support_sources_by_claim.get(claim_id, set())
                    ),
                    None,
                )
                if supported_claim is None:
                    raise ValueError(
                        "countercase source lacks a claim-specific XK3 support "
                        f"edge: {countercase_id} -> {claim_refs[0]} -> {source_id}"
                    )
            if source_refs:
                for claim_id in claim_refs:
                    if not any(
                        source_id
                        in xk3_support_sources_by_claim.get(claim_id, set())
                        for source_id in source_refs
                    ):
                        raise ValueError(
                            "countercase claim has no supporting source in XK3: "
                            f"{countercase_id} -> {claim_id}"
                        )

    if isinstance(case_ledger, Mapping) and graph:
        graph_cases = {
            record.get("case_id"): record
            for record in graph.get("cases", [])
            if isinstance(record, Mapping)
        }
        ledger_cases = {
            record.get("case_id"): record
            for record in case_ledger.get("cases", [])
            if isinstance(record, Mapping)
        }
        if set(graph_cases) != set(ledger_cases):
            raise ValueError("case ledger identities differ from the XK7 claim graph")
        graph_case_kinds = {
            "documented-real": "documented_real_case",
            "user-material": "user_material_case",
            "conditional-scenario": "conditional_scenario",
            "structural-analogy": "structural_analogy",
        }
        for case_id, ledger_case in ledger_cases.items():
            graph_case = graph_cases[case_id]
            comparisons = {
                "kind": (
                    ledger_case.get("kind"),
                    graph_case_kinds.get(graph_case.get("kind")),
                ),
                "summary": (
                    ledger_case.get("summary"),
                    graph_case.get("title"),
                ),
                "tests_claim_ids": (
                    ledger_case.get("tests_claim_ids"),
                    graph_case.get("tests_claim_ids"),
                ),
                "source_refs": (
                    ledger_case.get("source_refs"),
                    graph_case.get("source_refs"),
                ),
                "conditions": (
                    ledger_case.get("conditions"),
                    graph_case.get("conditions"),
                ),
                "stop_conditions": (
                    ledger_case.get("stop_conditions"),
                    graph_case.get("stop_conditions"),
                ),
                "cannot_prove": (
                    ledger_case.get("cannot_prove"),
                    graph_case.get("cannot_prove"),
                ),
            }
            for field, (ledger_value, graph_value) in comparisons.items():
                if ledger_value != graph_value:
                    raise ValueError(
                        "case ledger field differs from the XK7 claim graph: "
                        f"{case_id}.{field}"
                    )
        graph_countercases = {
            record.get("countercase_id"): record
            for record in graph.get("countercases", [])
            if isinstance(record, Mapping)
        }
        ledger_countercases = {
            record.get("countercase_id"): record
            for record in case_ledger.get("countercases", [])
            if isinstance(record, Mapping)
        }
        if set(graph_countercases) != set(ledger_countercases):
            raise ValueError(
                "case ledger countercase identities differ from the XK7 claim graph"
            )
        for countercase_id, ledger_countercase in ledger_countercases.items():
            graph_countercase = graph_countercases[countercase_id]
            for field in (
                "attacks_claim_ids",
                "conditions",
                "expected_signal",
                "reverse_signal",
                "decision_impact",
                "source_refs",
            ):
                if ledger_countercase.get(field) != graph_countercase.get(field):
                    raise ValueError(
                        "case ledger countercase field differs from the XK7 claim "
                        f"graph: {countercase_id}.{field}"
                    )
    raw_evidence = packet.get("evidence", {})
    for record in raw_evidence.get("claims", []):
        if not isinstance(record, Mapping):
            continue
        source_refs = record.get("source_refs")
        if (
            record.get("kind") == "v8.3_definition"
            and isinstance(source_refs, list)
            and not set(source_refs).issubset(source_anchor_ids)
        ):
            raise ValueError("source anchor does not resolve")
        if (
            record.get("kind") != "v8.3_definition"
            and isinstance(source_refs, list)
            and not set(source_refs).issubset(source_ids)
        ):
            raise ValueError("claim source reference does not resolve")

    answer = packet.get("answer", {})
    verdict = packet.get("verdict")
    validate_answer_basis_references(packet, evidence_ledger=evidence_ledger)
    red_team = packet.get("red_team")
    if isinstance(red_team, Mapping) and red_team.get("status") != "not_run":
        if not set(red_team.get("attacked_evidence_refs", [])).issubset(
            evidence_ids
        ):
            raise ValueError("red-team evidence reference does not resolve")
        if not set(red_team.get("surviving_claims", [])).issubset(claim_ids):
            raise ValueError("red-team surviving claim reference does not resolve")
        attacked_claim_ids = red_team.get("attacked_claim_ids", [])
        attacked_mechanism_ids = red_team.get("attacked_mechanism_ids", [])
        attacked_explanation_ids = red_team.get("attacked_explanation_ids", [])
        attacked_action_option_ids = red_team.get("attacked_action_option_ids", [])
        explanations = {
            record.get("explanation_id"): record
            for record in graph.get("explanations", [])
            if isinstance(record, Mapping)
            and isinstance(record.get("explanation_id"), str)
        }
        graph_mechanism_ids = {
            record.get("mechanism_id")
            for record in graph.get("mechanisms", [])
            if isinstance(record, Mapping)
            and isinstance(record.get("mechanism_id"), str)
        }
        action_ranking = packet.get("action_ranking")
        action_option_ids = {
            option.get("option_id")
            for option in (
                action_ranking.get("options", [])
                if isinstance(action_ranking, Mapping)
                else []
            )
            if isinstance(option, Mapping)
            and isinstance(option.get("option_id"), str)
        }
        if (
            not isinstance(attacked_claim_ids, list)
            or not attacked_claim_ids
            or not set(attacked_claim_ids).issubset(graph_claims)
            or not isinstance(attacked_mechanism_ids, list)
            or not attacked_mechanism_ids
            or not set(attacked_mechanism_ids).issubset(graph_mechanism_ids)
            or not isinstance(attacked_explanation_ids, list)
            or not set(attacked_explanation_ids).issubset(explanations)
            or not isinstance(attacked_action_option_ids, list)
            or not set(attacked_action_option_ids).issubset(action_option_ids)
        ):
            raise ValueError("red-team attack target does not resolve")
        decisive_mechanism_ids = {
            mechanism_id
            for claim_id in attacked_claim_ids
            for mechanism_id in graph_claims[claim_id].get("mechanism_ids", [])
        }
        if (
            not decisive_mechanism_ids
            or set(attacked_mechanism_ids) != decisive_mechanism_ids
        ):
            raise ValueError(
                "red-team attack does not bind its decisive mechanism"
            )
        current_best = (
            verdict.get("current_best_judgment")
            if isinstance(verdict, Mapping)
            and verdict.get("judgment_kind") == "best-current"
            else None
        )
        best_explanation = (
            explanations.get(current_best.get("best_explanation_id"))
            if isinstance(current_best, Mapping)
            else None
        )
        reaches_best = isinstance(best_explanation, Mapping) and (
            best_explanation.get("explanation_id") in attacked_explanation_ids
            or bool(
                set(attacked_claim_ids).intersection(
                    best_explanation.get("claim_ids", [])
                )
            )
            or bool(
                set(attacked_mechanism_ids).intersection(
                    best_explanation.get("mechanism_ids", [])
                )
            )
        )
        central_claim_id = graph.get("central_claim_id")
        reaches_central_visible_claim = (
            isinstance(central_claim_id, str)
            and central_claim_id in attacked_claim_ids
            and central_claim_id in set(answer.get("basis_refs", []))
        )
        ranked_action_ids = (
            set(action_ranking.get("ranking") or [])
            if isinstance(action_ranking, Mapping)
            else set()
        )
        reaches_action_ranking = bool(
            set(attacked_action_option_ids).intersection(ranked_action_ids)
        )
        if not (
            reaches_best
            or reaches_central_visible_claim
            or reaches_action_ranking
        ):
            raise ValueError(
                "red-team strongest attack does not reach current best explanation, "
                "central visible claim, or action ranking"
            )
        repair = red_team.get("repair")
        if red_team.get("repair_required") is True:
            if not isinstance(repair, Mapping):
                raise ValueError("red-team repair binding requires a repair object")
            if (
                not set(repair.get("repaired_claim_ids", [])).issubset(claim_ids)
                or not set(repair.get("repair_evidence_refs", [])).issubset(
                    evidence_ids
                )
                or not set(
                    repair.get("verification_evidence_refs", [])
                ).issubset(evidence_ids)
            ):
                raise ValueError("red-team repair reference does not resolve")
            _validate_red_team_repair_binding(
                red_team,
                evidence_ledger=evidence_ledger,
                claim_ids=claim_ids,
            )
    stance = packet.get("stance_pair")
    if isinstance(stance, Mapping) and stance.get("status") != "not_run":
        explanations = {
            item.get("explanation_id"): item
            for item in graph.get("explanations", [])
            if isinstance(item, Mapping)
            and isinstance(item.get("explanation_id"), str)
        }
        for side in ("position", "counterposition"):
            side_value = stance.get(side, {})
            if not isinstance(side_value, Mapping) or not set(
                side_value.get("support_refs", [])
            ).issubset(allowed):
                raise ValueError("stance support reference does not resolve")
            explanation = explanations.get(side_value.get("explanation_id"))
            if not isinstance(explanation, Mapping):
                raise ValueError("stance explanation reference does not resolve")
            exact_refs = set(explanation.get("claim_ids", [])) | set(
                explanation.get("mechanism_ids", [])
            )
            if set(side_value.get("support_refs", [])) != exact_refs:
                raise ValueError(
                    "stance support reference does not resolve; stance support "
                    "set differs from its exact XK7 explanation; stance "
                    "explanations differ from XK10 best and runner-up"
                )
        preferred = stance.get("preferred")
        verdict = packet.get("verdict")
        if (
            isinstance(verdict, Mapping)
            and verdict.get("judgment_kind") == "best-current"
            and preferred in {"position", "counterposition"}
        ):
            current_best = verdict.get("current_best_judgment", {})
            best_explanation = explanations.get(
                current_best.get("best_explanation_id")
                if isinstance(current_best, Mapping)
                else None
            )
            selected_stance = stance.get(preferred)
            other_side = (
                "counterposition" if preferred == "position" else "position"
            )
            other_stance = stance.get(other_side)
            if (
                not isinstance(best_explanation, Mapping)
                or not isinstance(selected_stance, Mapping)
                or not isinstance(other_stance, Mapping)
                or selected_stance.get("explanation_id")
                != current_best.get("best_explanation_id")
                or other_stance.get("explanation_id")
                != current_best.get("runner_up_explanation_id")
            ):
                raise ValueError(
                    "XK10 best explanation differs from the selected reader stance; "
                    "stance explanations differ from XK10 best and runner-up"
                )
        if isinstance(verdict, Mapping) and verdict.get("judgment_kind") == "non-decidability":
            non_decidability = verdict.get("non_decidability")
            partial = (
                non_decidability.get("remaining_partial_order")
                if isinstance(non_decidability, Mapping)
                else None
            )
            if not isinstance(partial, list) or not set(partial).issubset(explanations):
                raise ValueError(
                    "non-decidability partial order references an unknown explanation"
                )
            stance_explanations = {
                stance[side].get("explanation_id")
                for side in ("position", "counterposition")
                if isinstance(stance.get(side), Mapping)
            }
            if not stance_explanations.issubset(set(partial)):
                raise ValueError(
                    "undecided stance explanations differ from the remaining partial order"
                )


def _validate_problem_and_runtime_binding(
    packet: Mapping[str, Any],
    *,
    mode: str,
    run_contract: Mapping[str, Any] | None,
) -> None:
    problem = packet.get("problem_contract")
    if not isinstance(problem, Mapping):
        raise ValueError("analysis packet requires an explicit problem contract")
    for field in ("question", "object_of_analysis", "boundary", "identity_criterion", "spatial_scale", "organizational_scale", "time_window", "evidence_cutoff", "retrieval_profile", "requested_stance", "applicability_rationale"):
        _require_nonempty_text(problem.get(field), field=f"problem_contract.{field}")
    frozen = validate_problem_contract(
        {field: problem.get(field) for field in FROZEN_FIELDS}, mode=mode
    )
    if problem.get("dynamic_applicability") != packet.get("dynamic_applicability"):
        raise ValueError("problem contract applicability differs from the semantic packet")
    if packet.get("dynamic_applicability") == "applicable":
        world = packet.get("local_world_model")
        if isinstance(world, Mapping) and world.get("problem_contract_sha256") != contract_hash(frozen):
            raise ValueError("local world model problem contract hash differs from XK0")

    binding = packet.get("runtime_binding")
    if not isinstance(binding, Mapping):
        raise ValueError("analysis packet has no runtime-owned binding")
    if binding.get("mode") != mode:
        raise ValueError("runtime binding mode differs from the run contract")
    for field in (
        "run_id",
        "question",
        "evidence_cutoff",
        "problem_contract_sha256",
        "stance_neutrality_key",
        "privacy_contract_sha256",
    ):
        _require_nonempty_text(binding.get(field), field=f"runtime_binding.{field}")
    stance_pair = packet.get("stance_pair")
    if isinstance(stance_pair, Mapping) and stance_pair.get(
        "neutrality_key"
    ) != binding.get("stance_neutrality_key"):
        raise ValueError(
            "stance_pair.neutrality_key differs from XK0 stance_neutrality_key"
        )
    if run_contract is None:
        return
    expected = (
        build_runtime_packet_binding(run_contract)
        if run_contract.get("contract_profile") in CONTRACT_PROFILES
        else {
            "run_id": run_contract.get("run_id"),
            "question": run_contract.get("question"),
            "mode": run_contract.get("mode"),
            "evidence_cutoff": run_contract.get("evidence_cutoff"),
            "problem_contract_sha256": run_contract.get(
                "problem_contract_sha256"
            ),
            "stance_neutrality_key": run_contract.get("stance_neutrality_key"),
            "privacy_contract_sha256": sha256_json(
                run_contract.get("privacy_contract")
            ),
        }
    )
    if dict(binding) != expected:
        raise ValueError("runtime binding differs from the run contract")
    expected_problem = run_contract.get("problem_contract")
    if not isinstance(expected_problem, Mapping):
        raise ValueError("run contract has no frozen problem contract")
    if dict(frozen) != dict(expected_problem):
        raise ValueError("problem contract differs from the run contract")
    if binding.get("problem_contract_sha256") != contract_hash(frozen):
        raise ValueError("runtime binding problem contract hash is invalid")
    if binding.get("stance_neutrality_key") != stance_neutrality_key(
        frozen, mode=mode
    ):
        raise ValueError("runtime binding stance neutrality key is invalid")


def validate_delivery_binding(packet: Mapping[str, Any]) -> None:
    problem = packet.get("problem_contract")
    kind = packet.get("deliverable_type")
    if (
        not isinstance(problem, Mapping)
        or kind not in DELIVERABLE_TYPES
        or kind != problem.get("deliverable_type")
    ):
        raise ValueError("deliverable_type differs from the frozen problem contract")
    sections = packet.get("reader_sections")
    if not isinstance(sections, list) or not sections:
        raise ValueError("reader_sections must contain the complete authored answer")
    from jsonschema import Draft202012Validator
    section_schema = read_json(
        Path(__file__).resolve().parents[2] / "schemas" / "xk-reader-sections.schema.json"
    )
    section_errors = list(Draft202012Validator(section_schema).iter_errors(sections))
    if section_errors:
        raise ValueError(f"reader_sections are invalid: {section_errors[0].message}")
    if packet.get("dynamic_applicability") == "not_applicable":
        for section_index, section in enumerate(sections):
            prose_values = [section["local_judgment"], *section["paragraphs"]]
            for paragraph_index, text in enumerate(prose_values):
                if _asserts_dynamic_order_narrative(text):
                    raise ValueError(
                        "static packet cannot assert dynamic order narrative: "
                        f"reader_sections[{section_index}].paragraph[{paragraph_index}]"
                    )
    delivery = packet.get("answer_delivery")
    if delivery is None:
        return
    if not isinstance(delivery, Mapping) or delivery.get("visible_mode") not in {"full", "brief"}:
        raise ValueError("answer_delivery has an invalid visible_mode")
    if delivery["visible_mode"] == "brief":
        question = str(problem.get("question", ""))
        evidence = delivery.get("explicit_user_request")
        brief = delivery.get("brief_text")
        if (
            not isinstance(evidence, str)
            or not evidence.strip()
            or evidence not in question
            or not isinstance(brief, str)
            or not brief.strip()
            or re.search(r"(?:不要|不得|不能|无需|不必).{0,6}(?:简答|缩略|压缩|摘要)", question)
            or not re.search(
                r"简答|简短|简要|摘要|压缩|(?:不超过|最多|限)[^。！？\n]{0,12}(?:字|句)|\bbrief\b|\bconcise\b|\bsummary\b|\bunder\s+\d+\s+words\b",
                evidence,
                re.IGNORECASE,
            )
        ):
            raise ValueError("brief projection requires an explicit user request; full sections remain mandatory")
        if packet.get("dynamic_applicability") == "not_applicable" and _asserts_dynamic_order_narrative(brief):
            raise ValueError("static packet cannot assert dynamic order narrative in brief projection")


def require_packet_contract(
    packet: Mapping[str, Any],
    *,
    mode: str,
    run_contract: Mapping[str, Any] | None = None,
) -> None:
    if not isinstance(packet, Mapping):
        raise ValueError("analysis packet must be an object")
    if packet.get("schema_id") != "xi-kari.v3.analysis-packet" or packet.get("schema_version") != 3:
        raise ValueError("analysis packet must use xi-kari.v3.analysis-packet schema version 3")
    if "stance" in packet:
        raise ValueError(
            "analysis packet contains unsealed top-level stance; use stance_pair"
        )
    for field in (
        "dynamic_applicability",
        "problem_contract",
        "runtime_binding",
        "retrieval",
        "evidence",
        "concept_disposition",
        "facts",
        "case_ledger",
        "answer",
    ):
        if field not in packet:
            raise ValueError(f"analysis packet missing required field: {field}")
    validate_delivery_binding(packet)
    retrieval = packet.get("retrieval")
    if not isinstance(retrieval, Mapping) or retrieval.get("mode") != mode:
        raise ValueError("analysis packet retrieval mode differs from the run contract")
    answer = packet.get("answer")
    if not isinstance(answer, Mapping):
        raise ValueError("analysis packet answer must be an object")
    for field in ("direct_answer", "basis_refs", "withdrawal_conditions", "judgment_strength", "action_ceiling"):
        value = answer.get(field)
        if value is None or value == "" or value == []:
            raise ValueError(f"analysis packet answer missing required field: {field}")
    applicability = packet.get("dynamic_applicability")
    if applicability not in {"applicable", "not_applicable"}:
        raise ValueError("dynamic_applicability must be applicable or not_applicable")
    if applicability == "not_applicable":
        narrative_path = _static_answer_dynamic_narrative_path(answer)
        if narrative_path is not None:
            raise ValueError(
                "static packet cannot assert dynamic order narrative: "
                f"{narrative_path}"
            )
        for field in DYNAMIC_PHASE_FIELDS:
            if field in packet:
                raise ValueError(
                    "static packet cannot contain dynamic semantic artifact: "
                    f"{field}"
                )
    _validate_problem_and_runtime_binding(
        packet,
        mode=mode,
        run_contract=run_contract,
    )
    validate_visibility_ledger(
        packet,
        privacy_contract=(
            run_contract.get("privacy_contract")
            if isinstance(run_contract, Mapping)
            else None
        ),
    )
    validate_retrieval_contract(packet, mode=mode)
    if applicability == "not_applicable":
        reason = packet.get("not_applicable_reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("static packet must explain why three-order inference is not applicable")
    else:
        for field in (
            "local_world_model",
            "transformation_ledger",
            "claim_mechanism_graph",
            "recursive_lineage",
            "recursive_states",
            "order_evaluation",
            "red_team",
            "stance_pair",
            "verdict",
            "action_ranking",
            "forecast",
        ):
            if field not in packet:
                raise ValueError(f"dynamic packet missing semantic artifact: {field}")
        validate_dynamic_gates(packet)
    validate_provenance(packet, mode=mode)


def provisional_delivery_paths() -> tuple[str, ...]:
    return tuple(
        path for key, path in DELIVERY_PATHS.items() if key != "final_chat"
    )


def required_delivery_paths() -> tuple[str, ...]:
    return tuple(DELIVERY_PATHS.values())


def build_phase_artifact_bindings(
    run_dir: Path, records: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """Project the sealed XK0-XK11 artifacts into the final manifest."""

    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        phase = record.get("phase")
        if phase == "XK12":
            continue
        if phase not in XK_PHASES[:-1]:
            raise ValueError(f"manifest has an invalid phase owner: {phase}")
        bindings = record.get("artifact_bindings")
        if not isinstance(bindings, Sequence) or isinstance(bindings, (str, bytes)):
            raise ValueError(f"manifest phase bindings are invalid: {phase}")
        for binding in bindings:
            if not isinstance(binding, Mapping):
                raise ValueError(f"manifest phase binding is invalid: {phase}")
            relative = binding.get("path")
            if not isinstance(relative, str) or not relative or relative in seen:
                raise ValueError(f"manifest phase artifact path is invalid: {relative}")
            path = confined_path(run_dir, relative, must_exist=True)
            observed_sha256 = sha256_file(path)
            if binding.get("sha256") != observed_sha256:
                raise ValueError(f"manifest phase artifact hash differs: {relative}")
            result.append(
                {
                    "path": relative,
                    "phase": phase,
                    "sha256": observed_sha256,
                    "bytes": path.stat().st_size,
                }
            )
            seen.add(relative)
    return result


def expected_phase_artifact_paths(
    phase: str,
    *,
    contract_profile: str = PRODUCTION_CONTRACT_PROFILE,
    mode: str | None = None,
) -> tuple[str, ...]:
    paths = {
        "XK0": ("run-contract.json", "capability-snapshot.json"),
        "XK1": (
            "source-lock.json",
            "authoring/XK01-read-plan.json",
            "authoring/XK01-read-events.jsonl",
            *(
                (
                    "authoring/XK01-semantic-read-trace.json",
                    "authoring/XK01-base-authoring-events.jsonl",
                    "authoring/XK01-base-authoring-request.json",
                    "authoring/XK01-base-authoring-prompt.txt",
                    "authoring/XK01-base-authoring-output.bin",
                    "authoring/XK01-base-authoring-receipt.json",
                )
                if contract_profile == PRODUCTION_CONTRACT_PROFILE
                else ()
            ),
        ),
        "XK2": (
            "authoring/XK02-retrieval-ledger.json",
            "retrieval/index.json",
            *(
                (
                    "authoring/XK02-semantic-retrieval.json",
                    "authoring/XK02-retrieval-execution-receipt.json",
                    *(
                        ("authoring/XK02-host-capture-index.json",)
                        if mode == "open-world"
                        else ()
                    ),
                )
                if contract_profile == PRODUCTION_CONTRACT_PROFILE
                else ()
            ),
        ),
        "XK3": (
            "authoring/XK03-evidence-ledger.json",
            "authoring/XK03-unknown-register.json",
        ),
        "XK4": (
            "authoring/XK04-concept-disposition.json",
            "authoring/XK04-concept-closure-report.json",
            *(
                (
                    "authoring/XK04-ontology-read-plan.json",
                    "authoring/XK04-ontology-read-trace.json",
                )
                if contract_profile == PRODUCTION_CONTRACT_PROFILE
                else ()
            ),
        ),
        "XK5": ("authoring/XK05-local-world-model.json",),
        "XK6": (
            "authoring/XK06-transformation-ledger.json",
            "authoring/XK06-cascade.json",
        ),
        "XK7": (
            "authoring/XK07-claim-mechanism-graph.json",
            "authoring/XK07-case-ledger.json",
        ),
        "XK8": ("authoring/XK08-recursive-lineage.json",),
        "XK9": (
            "authoring/XK09-semantic-authoring-bundle.json",
            "authoring/XK09-order-evaluation.json",
            "authoring/XK09-red-team-report.json",
            "authoring/XK09-stance-pair.json",
            "authoring/XK09-sensitivity-report.json",
            "authoring/XK09-stance-stability-report.json",
        ),
        "XK10": (
            "authoring/XK10-verdict.json",
            "authoring/XK10-action-ranking.json",
            "authoring/XK10-forecast-ledger.json",
            "authoring/XK10-framework-gap-ledger.json",
        ),
        "XK11": (
            "authoring/XK11-output-plan.json",
            "authoring/XK11-semantic-coverage.json",
            "authoring/XK11-prose-review.json",
            *provisional_delivery_paths(),
        ),
        "XK12": (
            "validation/attempts/final/validator-report.json",
            "delivery/final-chat.json",
            "artifacts/artifact-manifest.json",
        ),
    }
    try:
        return paths[phase]
    except KeyError as exc:
        raise ValueError(f"unknown Xi-Kari phase: {phase}") from exc
