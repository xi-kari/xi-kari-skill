"""Runtime-owned base authoring execution for Xi-Kari v3.

The ordinary ``prepare`` seam is a read-only preflight. Production execution
starts the base author in a private writable workspace, captures its JSONL
event stream and complete semantic output file, and only
then hands the bytes to the existing materializer.  This module owns that
boundary.  It never treats a model-authored PID, timestamp, receipt, or phase
marker as evidence.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import secrets
import signal
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any
import uuid

from .authoring import (
    FORMAL_ADAPTER_PROFILE,
    FORMAL_ADAPTER_RELATIVE_PATH,
    FORMAL_ADAPTER_PROTOCOL,
    MAX_ADAPTER_STDERR_BYTES,
    MAX_ADAPTER_STDOUT_BYTES,
    DEFAULT_ADAPTER_TIMEOUT_SECONDS,
    MAX_AUTHORING_TIMEOUT_SECONDS,
    AuthoringCommunicationError,
    _communicate_limited,
    _ordinary_executable,
    bind_semantic_authoring_adapter,
    bind_base_authoring_provider,
)
from .canonical_json import (
    atomic_write_bytes,
    atomic_write_json,
    canonical_bytes,
    canonical_dumps,
    read_bounded_regular_file,
    read_json,
    read_json_text,
    sha256_bytes,
    sha256_file,
    sha256_json,
)
from .authoring_workspace import AuthoringFailure, failure_causes, private_authoring_directory
from .concept_authority import load_concept_authority
from .closed_input import (
    CLOSED_QUERY_DIRECTIONS,
    _event_objects,
    _normalize_closed_semantic,
    freeze_closed_input_materials,
)
from .contracts import build_execute_owned_binding, build_runtime_packet_binding
from .contract_authoring import (
    contract_authoring_request, contract_authoring_prompt, parse_contract_authoring_output,
    contract_authoring_evidence, validate_contract_authoring_evidence,
)
from .materialization import (
    _issue_production_preparation_capability,
    _prepare_production_run,
    materialize_run,
    status_run,
)
from .ontology_read_trace import (
    INPUT_SCHEMA_ID as ONTOLOGY_TRACE_INPUT_SCHEMA_ID,
    build_ontology_read_plan,
    build_ontology_read_trace,
)
from .problem_contract import (
    FROZEN_FIELDS,
    build_natural_request_envelope,
    contract_hash,
    draft_problem_contract_from_natural_request,
    freeze_natural_problem_contract,
    normalize_natural_request,
    validate_problem_contract,
)
from .retrieval import build_full_source_lock
from .retrieval_execution import (
    HostCapture,
    build_host_capture_index,
    capture_host_sources,
    project_runtime_retrieval,
    write_host_capture_bundle,
)
from .semantic_projection import semantic_atom_paths, validate_visibility_ledger
from .semantic_read_trace import validate_semantic_read_trace_input
from .validation import run_fresh_validator
from .world_volume import _schema_validator
from .output_transport import (
    COMPLETION_NOTICE, SEMANTIC_OUTPUT_FILENAME, OUTPUT_TRANSPORT,
    parse_provider_events, read_semantic_output,
)


BASE_REQUEST_SCHEMA_ID = "xi-kari.v3.base-authoring-request"
BASE_OUTPUT_SCHEMA_ID = "xi-kari.v3.base-authoring-output"
BASE_EXECUTION_RECEIPT_SCHEMA_ID = "xi-kari.v3.base-authoring-execution"
BASE_PROTOCOL = "xi-kari.v3.base-authoring/v1"
BASE_OUTPUT_SCHEMA_RELATIVE = Path("schemas/xk-base-authoring-output.schema.json")
BASE_EVENTS_RELATIVE = Path("authoring/XK01-base-authoring-events.jsonl")
BASE_RECEIPT_RELATIVE = Path("authoring/XK01-base-authoring-receipt.json")
BASE_REQUEST_RELATIVE = Path("authoring/XK01-base-authoring-request.json")
BASE_PROMPT_RELATIVE = Path("authoring/XK01-base-authoring-prompt.txt")
BASE_OUTPUT_RELATIVE = Path("authoring/XK01-base-authoring-output.bin")
SEMANTIC_RETRIEVAL_RELATIVE = Path("authoring/XK02-semantic-retrieval.json")
RETRIEVAL_RECEIPT_RELATIVE = Path(
    "authoring/XK02-retrieval-execution-receipt.json"
)
HOST_CAPTURE_INDEX_RELATIVE = Path("authoring/XK02-host-capture-index.json")
MAX_BASE_INPUT_BYTES = 1024 * 1024
MAX_BASE_OUTPUT_BYTES = 16 * 1024 * 1024
MAX_BASE_EVENT_BYTES = 16 * 1024 * 1024
MAX_BASE_EVENT_LINES = 10000


def _read_bounded_regular_file(
    path: Path,
    *,
    limit: int = MAX_BASE_OUTPUT_BYTES,
) -> bytes:
    return read_bounded_regular_file(path, limit=limit)


BASE_SEMANTIC_FIELDS = (
    "deliverable_type",
    "reader_sections",
    "problem_contract",
    "dynamic_applicability",
    "facts",
    "case_ledger",
    "cases",
    "answer",
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
    "visibility_ledger",
    "retrieval",
    "evidence",
)
BASE_COMMON_FIELDS = (
    "deliverable_type",
    "reader_sections",
    "problem_contract",
    "dynamic_applicability",
    "facts",
    "case_ledger",
    "cases",
    "answer",
    "visibility_ledger",
    "retrieval",
    "evidence",
)
BASE_DYNAMIC_FIELDS = tuple(
    field for field in BASE_SEMANTIC_FIELDS if field not in BASE_COMMON_FIELDS
)
MODEL_AUTHORITY_KEYS = frozenset(
    {
        "run_id",
        "pid",
        "child_pid",
        "parent_pid",
        "phase",
        "phase_record",
        "phase_records",
        "receipt",
        "runtime_receipt",
        "validator",
        "validator_receipt",
        "terminal_record",
        "completion",
        "artifact_manifest",
        "artifact_hash",
        "execution_id",
        "execution_context_id",
        "semantic_probe_authorings",
        "runtime_binding",
        "concept_disposition",
    }
)
RUNTIME_OWNED_VISIBILITY_POLICIES = {
    "open-world": {
        "retrieval.queries[*].query_id": ("public", "include"),
        "retrieval.queries[*].status": ("public", "include"),
        "retrieval.queries[*].executed_at": ("public", "include"),
        "retrieval.queries[*].result_source_ids[*]": ("public", "include"),
        "retrieval.sources[*].source_id": ("public", "include"),
        "retrieval.sources[*].accessed_at": ("public", "include"),
        "retrieval.sources[*].content_authority": ("public", "include"),
        "retrieval.sources[*].host_observation.status": ("public", "include"),
        "retrieval.sources[*].host_observation.open_event_ids[*]": (
            "public",
            "include",
        ),
        "retrieval.sources[*].host_observation.capture_id": ("public", "include"),
        "retrieval.sources[*].host_observation.requested_url": ("public", "include"),
        "retrieval.sources[*].host_observation.final_url": ("public", "include"),
        "retrieval.sources[*].host_observation.peer_ip": ("public", "include"),
        "retrieval.sources[*].host_observation.response_status": ("public", "include"),
        "retrieval.sources[*].host_observation.content_type": ("public", "include"),
        "retrieval.sources[*].host_observation.charset": ("public", "include"),
        "retrieval.sources[*].host_observation.body_sha256": ("public", "include"),
        "retrieval.sources[*].host_observation.text_sha256": ("public", "include"),
        "retrieval.sources[*].host_observation.body_byte_count": ("public", "include"),
        "retrieval.sources[*].host_observation.text_character_count": ("public", "include"),
        "retrieval.sources[*].host_observation.redirect_chain[*]": ("public", "include"),
        "retrieval.sources[*].host_observation.excerpt_sha256": ("public", "include"),
        "retrieval.sources[*].host_observation.excerpt_start": ("public", "include"),
        "retrieval.sources[*].host_observation.excerpt_end": ("public", "include"),
        "retrieval.assessments[*].source_id": ("public", "include"),
        "retrieval.directional_evidence[*].direction": ("public", "include"),
        "retrieval.directional_evidence[*].search_event_id": ("public", "include"),
        "retrieval.directional_evidence[*].stop_boundary": ("public", "include"),
        "retrieval.directional_evidence[*].source_urls[*]": ("public", "include"),
        "retrieval.directional_evidence[*].source_ids[*]": ("public", "include"),
        "retrieval.directional_evidence[*].distinct_url_count": ("public", "include"),
        "retrieval.directional_evidence[*].distinct_source_count": ("public", "include"),
        "retrieval.directional_evidence[*].distinct_content_count": ("public", "include"),
        "retrieval.directional_evidence[*].distinct_independence_count": ("public", "include"),
        "retrieval.directional_evidence[*].new_information_count": ("public", "include"),
        "retrieval.directional_evidence[*].stop_reason": ("public", "include"),
    },
    "closed-input": {
        "retrieval.queries[*].query_id": ("public", "include"),
        "retrieval.queries[*].status": ("public", "include"),
        "retrieval.queries[*].executed_at": ("public", "include"),
        "retrieval.queries[*].result_source_ids[*]": ("public", "include"),
        "retrieval.sources[*].accessed_at": ("public", "include"),
        "retrieval.frozen_material_manifest.materials[*].source_id": (
            "public",
            "include",
        ),
    },
}
RUNTIME_ONLY_VISIBILITY_PATHS = {
    "open-world": (
        "retrieval.queries[*].query_id",
        "retrieval.queries[*].status",
        "retrieval.queries[*].executed_at",
        "retrieval.queries[*].result_source_ids[*]",
        "retrieval.sources[*].accessed_at",
        "retrieval.sources[*].content_authority",
        "retrieval.sources[*].host_observation.status",
        "retrieval.sources[*].host_observation.open_event_ids[*]",
        "retrieval.sources[*].host_observation.capture_id",
        "retrieval.sources[*].host_observation.requested_url",
        "retrieval.sources[*].host_observation.final_url",
        "retrieval.sources[*].host_observation.peer_ip",
        "retrieval.sources[*].host_observation.response_status",
        "retrieval.sources[*].host_observation.content_type",
        "retrieval.sources[*].host_observation.charset",
        "retrieval.sources[*].host_observation.body_sha256",
        "retrieval.sources[*].host_observation.text_sha256",
        "retrieval.sources[*].host_observation.body_byte_count",
        "retrieval.sources[*].host_observation.text_character_count",
        "retrieval.sources[*].host_observation.redirect_chain[*]",
        "retrieval.sources[*].host_observation.excerpt_sha256",
        "retrieval.sources[*].host_observation.excerpt_start",
        "retrieval.sources[*].host_observation.excerpt_end",
        "retrieval.directional_evidence[*].direction",
        "retrieval.directional_evidence[*].search_event_id",
        "retrieval.directional_evidence[*].stop_boundary",
        "retrieval.directional_evidence[*].source_urls[*]",
        "retrieval.directional_evidence[*].source_ids[*]",
        "retrieval.directional_evidence[*].distinct_url_count",
        "retrieval.directional_evidence[*].distinct_source_count",
        "retrieval.directional_evidence[*].distinct_content_count",
        "retrieval.directional_evidence[*].distinct_independence_count",
        "retrieval.directional_evidence[*].new_information_count",
        "retrieval.directional_evidence[*].stop_reason",
    ),
    "closed-input": (
        "retrieval.queries[*].query_id",
        "retrieval.queries[*].status",
        "retrieval.queries[*].executed_at",
        "retrieval.queries[*].result_source_ids[*]",
        "retrieval.sources[*].accessed_at",
        "retrieval.frozen_material_manifest.materials[*].source_id",
    ),
}
PROJECTION_OMITTED_VISIBILITY_PATHS = {
    "open-world": ("retrieval.queries[*].purpose",),
    "closed-input": ("retrieval.queries[*].purpose",),
}
MODEL_RETRIEVAL_FIELDS = {
    "open-world": {
        "mode",
        "queries",
        "sources",
        "assessments",
        "saturation_status",
        "capability_gap",
        "remaining_unknowns",
    },
    "closed-input": {
        "mode",
        "queries",
        "sources",
        "assessments",
        "saturation_status",
        "capability_gap",
        "remaining_unknowns",
    },
}
MODEL_QUERY_FIELDS = {
    "open-world": {"direction", "query", "purpose"},
    "closed-input": {"direction", "query", "purpose"},
}
MODEL_SOURCE_FIELDS = {
    "open-world": {
        "source_id",
        "origin",
        "title",
        "url",
        "publisher",
        "content",
        "published_at",
        "event_at",
    },
    "closed-input": {
        "source_id",
        "origin",
        "title",
        "content",
        "published_at",
        "event_at",
    },
}
MODEL_ASSESSMENT_FIELDS = {
    "open-world": {
        "source_id",
        "authority",
        "independence",
        "independence_identity",
        "source_lineage",
        "interest_relevance",
        "affected_positions",
        "low_power_positions",
        "conflict_source_ids",
        "freshness",
        "relevance",
        "verdict",
        "limitations",
        "cannot_prove",
    },
    "closed-input": {
        "source_id",
        "authority",
        "independence",
        "independence_identity",
        "source_lineage",
        "interest_relevance",
        "affected_positions",
        "low_power_positions",
        "conflict_source_ids",
        "freshness",
        "relevance",
        "verdict",
        "limitations",
        "cannot_prove",
    },
}
RUNTIME_OWNED_MODEL_FIELDS = {
    "open-world": {
        "query": {"query_id", "status", "executed_at", "result_source_ids"},
        "source": {
            "accessed_at",
            "content_authority",
            "content_sha256",
            "run_id",
        },
        "assessment": set(),
    },
    "closed-input": {
        "query": {"query_id", "status", "executed_at", "result_source_ids"},
        "source": {
            "accessed_at",
            "content_authority",
            "content_sha256",
            "run_id",
        },
        "assessment": set(),
    },
}
_VISIBILITY_INDEX = re.compile(r"\[[0-9]+\]")
VISIBILITY_CLASSIFICATION_SCHEME = (
    "public",
    "context_limited",
    "sensitive",
    "highly_sensitive",
    "refused_disclosure",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


# Every downstream cutoff authority (retrieval execution windows, per-source
# accessed_at, red-team repair verified_at) requires its in-run instants to be
# at or before the frozen evidence cutoff, so a runtime-owned cutoff must bound
# the end of the authoring budget, not the moment the request was received.
# The grace term covers pre-spawn work (source lock and ontology plan hashing)
# plus process reaping and timestamping after the provider deadline.
EVIDENCE_CUTOFF_GRACE_SECONDS = 600


def _natural_evidence_cutoff(timeout_seconds: int) -> str:
    horizon = datetime.now(timezone.utc) + timedelta(
        seconds=timeout_seconds + EVIDENCE_CUTOFF_GRACE_SECONDS
    )
    return horizon.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _safe_run_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._:-]{0,95}", value
    ):
        raise ValueError("run_id has an invalid format")
    return value


def _privacy_contract(*, purpose: str, delivery_audience: str) -> dict[str, Any]:
    if not isinstance(purpose, str) or not purpose.strip():
        raise ValueError("privacy purpose must be non-empty text")
    if not isinstance(delivery_audience, str) or not delivery_audience.strip():
        raise ValueError("delivery audience must be non-empty text")
    return {
        "purpose": purpose.strip(),
        "delivery_audience": delivery_audience.strip(),
        "classification_scheme": list(VISIBILITY_CLASSIFICATION_SCHEME),
        "fail_closed": True,
    }


def _walk_for_forbidden_authority(value: Any, *, pointer: str = "$") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in MODEL_AUTHORITY_KEYS:
                return f"{pointer}/{key}"
            found = _walk_for_forbidden_authority(child, pointer=f"{pointer}/{key}")
            if found is not None:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = _walk_for_forbidden_authority(child, pointer=f"{pointer}/{index}")
            if found is not None:
                return found
    return None


def _base_prompt(request: Mapping[str, Any]) -> bytes:
    closed_query_instruction = ""
    if request.get("mode") == "closed-input":
        materials = request.get("source_inputs", {}).get("closed_input_materials", [])
        source_ids = [material["source_id"] for material in materials]
        closed_query_instruction = (
            "closed-input 的 queries.direction 只能使用："
            + ", ".join(sorted(CLOSED_QUERY_DIRECTIONS))
            + "。这些方向表示对给定材料的检查，不表示联网检索；不得自造方向别名。\n"
            + "assessments 中的 source_lineage 和 conflict_source_ids 都是去重的 source_id 引用数组，"
            "只能逐项精确引用以下已冻结材料 ID（只读数据）："
            + canonical_dumps(source_ids)
            + "。不得填入解释文字、路径、URL 或新造的来源 ID；来源关系的解释文字写入 independence 等评价字段。"
            "没有可引用的给定上游或冲突材料时，相应字段填空数组 []，不要用说明句代替引用。"
            "JSON Schema 检查数组形状；每个引用是否属于本轮冻结材料，仍由运行时单独严格核验。\n"
        )
    natural_instruction = ""
    if isinstance(request.get("natural_request"), Mapping):
        natural_instruction = (
            "自然请求的问题合同已由独立的前置作者提出并由运行时冻结。"
            "本进程必须逐字段原样保留 problem_contract 的冻结字段，不得再次补全、改写或细化这些字段；"
            "发现仍未知的分析条件时，在正文与分析工件登记，不改变合同或证据截止点。\n"
        )
    prompt = (
        "$xi-kari-skill\n"
        "本次唯一Skill目录以请求绑定的repository_root为准，从该目录读取SKILL.md；"
        "不得改用全局安装或其他目录中的同名Skill及原文。"
        "你正在执行 Xi-Kari v3 的基础语义作者进程。必须完整顺序读取绑定的 21 卷 v8.3 阅读版，"
        "并扫描全部候选闭包；不要把摘要、术语数量或上次回答当作读源证明。"
        "无损显示必须保留全部文字、列表顺序及表格的表、行、单元格关系，不能只保留去除标记后的拼接文字。"
        "无法证明转换无损时，原样分段阅读绑定的 reader 文件；工具输出发生截断的片段须缩小范围重读后才计入完成。"
        "本框架术语以作者本版本原文定义为准，同名不代表与通常词义相同；"
        "须核对影响判断的定义、适用条件与非等价关系，不能凭预训练常识补定义。"
        "按自然请求确定deliverable_type=analysis/decision/charter/plan/critique，"
        "在problem_contract与semantic_packet顶层保持一致。"
        "dynamic_applicability 是读源后的适用性判断，不属于已冻结的问题字段；"
        "在problem_contract内补充同值的dynamic_applicability和作者撰写的applicability_rationale，"
        "并为这些语义字段明确登记披露分类。静态分析还须在顶层提供not_applicable_reason。"
        "形成明确中心判断与各部分局部裁决，完成可支持的机制比较和方案取舍，"
        "分析推荐不等于执行授权；无授权时可以recommended，不可伪造selected。"
        "必须给出reader_sections完整成文；每节含section_id、承载内容的heading、"
        "local_judgment、paragraphs与source_bindings，绑定source_path、paragraph_index和真实excerpt。"
        "paragraph_index=0指local_judgment，1起对应paragraphs；"
        "全部实质分析都要进入正文并绑定，不按是否改变主结论删减。"
        "不得把次要机制、反例、失败路径或落选理由只放附件，不倾倒机器字段。"
        "只有原始用户明确要求简答时，answer_delivery才能含visible_mode=brief、"
        "原始explicit_user_request及brief_text；reader_sections仍须完整。"
        "还必须按 ontology_read_plan 的四类责任逐项读取每个 candidate、每个 canonical/structural card、"
        "每条 required neighbor 和每个 continuity bundle，并逐项记录 read、问题关系与理由；"
        "每条记录还必须从实际源字节计算 content_witness，并给出能在实际源字节中逐字找到的 content_excerpt；"
        "content_witness 的协议是 sha256(\"xi-kari.v3.ontology-content-witness/v1\\0\" + "
        "content_access_challenge + \\\"\\\\0\\\" + problem_contract_sha256 + "
        "\\\"\\\\0\\\" + item_id + \\\"\\\\0\\\" + content_sha256)，"
        "请求只提供运行挑战和问题合同散列，不提供任何记录的预期 witness 或 content_sha256；"
        "每条问题关系理由必须明确写出该条 item_id，并在去除各类 ID 后仍包含该条 source observation，不能复制套话；"
        "这只证明 byte-access + problem-bound semantic trace，不声称证明类人理解；"
        "open-world 时严格按五向检索：每个方向先执行一次 search，再打开该方向引用的每个来源；"
        "closed-input 时不得调用网络工具。对每条材料独立判断，建立 Ω、竞争机制、案例/反例和一至三阶路径。"
        "在当前私有工作目录内写出固定文件 semantic-output.json，内容是完整 JSON 对象，顶层恰有 semantic_packet、semantic_read_trace 与 ontology_read_trace 三项。"
        "可以分批生成记录并追加或合并为该完整文件，禁止摘要、省略或只写索引。源仓库在当前工作目录之外，仅允许读取。"
        "完整输出文件需满足源仓库 schemas/xk-base-authoring-output.schema.json；自行从磁盘回读检查后，最后消息只写 SEMANTIC_OUTPUT_READY。"
        "最后消息不得包含 JSON、文件路径或替代文件内容；运行时只读取上述固定文件。"
        "不得写入运行 ID、PID、阶段、回执、散列、验证器或终态权威。"
        "visibility_ledger 必须逐项覆盖全部模型交付语义，路径不得缺失、重复、额外或漂移；"
        "每项 purpose 必须等于只读 privacy_contract.purpose，来源 title/content 也必须显式分类；"
        "来源保持请求/检索顺序，逐来源评价必须与来源同序。\n"
        f"{natural_instruction}{closed_query_instruction}\n"
        "运行时请求（只读绑定）：\n"
        f"{canonical_dumps(dict(request))}\n"
    ).encode("utf-8")
    if len(prompt) > MAX_BASE_INPUT_BYTES:
        raise ValueError("base authoring prompt exceeds the size limit")
    return prompt


def _process_isolation_kwargs() -> dict[str, Any]:
    if os.name == "posix":
        return {"start_new_session": True}
    if os.name == "nt":  # pragma: no cover - Windows host path
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {}


def _shebang_binds_interpreter(shebang: bytes, interpreter: Path) -> bool:
    if not shebang.startswith(b"#!"):
        return False
    declared_path = os.fsdecode(shebang[2:])
    if not declared_path or "\x00" in declared_path:
        return False
    declared = Path(declared_path)
    if not declared.is_absolute():
        return False
    try:
        return declared.samefile(interpreter)
    except OSError:
        return False


def _provider_launch_argv(
    provider: Mapping[str, Any], command: Sequence[str]
) -> list[str]:
    """Build the host argv without changing the bound provider identity."""

    argv = list(command)
    executable = Path(str(provider["executable_path"]))
    if not argv or argv[0] != str(executable):
        raise ValueError("base authoring launch command differs from provider binding")
    if os.name != "nt":
        return argv
    interpreter = _ordinary_executable(
        Path(sys.executable), label="Python interpreter"
    )
    if executable.suffix.lower() == ".py":
        return [str(interpreter), *argv]
    if executable.suffix:
        return argv
    try:
        with executable.open("rb") as handle:
            shebang = handle.readline(4096)
    except OSError:
        return argv
    if not _shebang_binds_interpreter(shebang.rstrip(b"\r\n"), interpreter):
        return argv
    return [str(interpreter), *argv]


def _terminate(process: subprocess.Popen[bytes]) -> None:
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif os.name == "nt":  # pragma: no cover
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass
    if process.poll() is None:
        try:
            process.kill()
        except ProcessLookupError:
            pass


def _strict_event_stream(raw: bytes) -> tuple[str, list[dict[str, Any]]]:
    return parse_provider_events(raw)


def _project_base_applicability(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Project authored applicability without changing frozen fields or disclosure."""

    problem = packet["problem_contract"]
    additions: dict[str, str] = {}
    if "dynamic_applicability" not in problem:
        additions["dynamic_applicability"] = "dynamic_applicability"
    if "applicability_rationale" not in problem:
        if packet["dynamic_applicability"] != "not_applicable":
            raise ValueError("base authoring needs an authored applicability rationale")
        additions["applicability_rationale"] = "not_applicable_reason"
    rationale = (
        packet[additions["applicability_rationale"]]
        if "applicability_rationale" in additions
        else problem["applicability_rationale"]
    )
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError("base authoring applicability rationale must be non-empty text")
    if not additions:
        return dict(packet)
    projected = deepcopy(dict(packet))
    ledger = projected.get("visibility_ledger")
    entries = ledger.get("entries") if isinstance(ledger, Mapping) else None
    if not isinstance(entries, list):
        raise ValueError("applicability projection requires an explicit visibility ledger")
    rationale_path = (
        "not_applicable_reason"
        if "applicability_rationale" in additions
        else "problem_contract.applicability_rationale"
    )
    for field, source_path in additions.items():
        target_path = "problem_contract." + field
        source_entries = [
            entry for entry in entries
            if isinstance(entry, Mapping) and entry.get("canonical_path") == rationale_path
        ]
        if len(source_entries) != 1 or any(
            isinstance(entry, Mapping) and entry.get("canonical_path") == target_path
            for entry in entries
        ):
            raise ValueError("applicability projection visibility source or target is invalid")
        projected["problem_contract"][field] = packet[source_path]
        entries.append({**deepcopy(dict(source_entries[0])), "canonical_path": target_path})
    return projected


def _parse_base_output(
    raw: bytes,
    *,
    problem_contract: Mapping[str, Any],
    mode: str,
    ontology_read_plan: Mapping[str, Any],
    repository_root: Path,
    natural_request: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    try:
        value = read_json_text(raw.decode("utf-8"))
    except Exception as exc:
        raise ValueError("base authoring output is not strict UTF-8 JSON") from exc
    if not isinstance(value, Mapping) or set(value) != {
        "semantic_packet",
        "semantic_read_trace",
        "ontology_read_trace",
    }:
        raise ValueError("base authoring output is not the required semantic envelope")
    validator = _schema_validator(BASE_OUTPUT_SCHEMA_RELATIVE.name, str(repository_root))
    violations = sorted(validator.iter_errors(value), key=lambda error: str(list(error.absolute_path)))
    if violations:
        raise ValueError(f"base authoring output file fails schema validation: {violations[0].message}")
    packet = value.get("semantic_packet")
    if not isinstance(packet, Mapping):
        raise ValueError("base authoring semantic packet is not an object")
    packet_fields = set(packet)
    allowed_fields = set(BASE_COMMON_FIELDS) | set(BASE_DYNAMIC_FIELDS) | {
        "not_applicable_reason", "answer_delivery"
    }
    if not packet_fields.issubset(allowed_fields) or not set(BASE_COMMON_FIELDS).issubset(
        packet_fields
    ):
        raise ValueError("base authoring semantic packet fields are not exact")
    pointer = _walk_for_forbidden_authority(packet)
    if pointer is not None:
        raise ValueError(f"base authoring output contains runtime authority at {pointer}")
    expected_problem = validate_problem_contract(problem_contract, mode=mode)
    authored_problem = packet.get("problem_contract")
    if not isinstance(authored_problem, Mapping):
        raise ValueError("base authoring packet has no problem contract")
    authored_frozen_fields = {
        field: authored_problem.get(field) for field in FROZEN_FIELDS
    }
    frozen = validate_problem_contract(authored_frozen_fields, mode=mode)
    if frozen != expected_problem:
        raise ValueError("base authoring packet differs from the frozen problem contract")
    if natural_request is not None:
        freeze_natural_problem_contract(frozen, request=natural_request, mode=mode)
    if packet.get("dynamic_applicability") not in {"applicable", "not_applicable"}:
        raise ValueError("base authoring applicability is invalid")
    if "dynamic_applicability" in authored_problem and authored_problem[
        "dynamic_applicability"
    ] != packet.get(
        "dynamic_applicability"
    ):
        raise ValueError("base authoring applicability is inconsistent")
    if packet.get("dynamic_applicability") == "applicable":
        if not set(BASE_DYNAMIC_FIELDS).issubset(packet_fields):
            raise ValueError("dynamic base authoring packet is missing semantic fields")
        if "not_applicable_reason" in packet:
            raise ValueError("dynamic base authoring packet cannot carry static reason")
    else:
        if any(field in packet_fields for field in BASE_DYNAMIC_FIELDS):
            raise ValueError("static base authoring packet contains dynamic fields")
        if not isinstance(packet.get("not_applicable_reason"), str) or not packet[
            "not_applicable_reason"
        ].strip():
            raise ValueError("static base authoring packet needs a not-applicable reason")
    retrieval = packet.get("retrieval")
    if not isinstance(retrieval, Mapping) or retrieval.get("mode") != mode:
        raise ValueError("base authoring retrieval mode differs from the contract")
    _validate_model_retrieval_ownership(retrieval, mode=mode)
    packet = _project_base_applicability(packet)
    trace = value.get("semantic_read_trace")
    if not isinstance(trace, Mapping):
        raise ValueError("base authoring semantic read trace is not an object")
    if trace.get("schema_id") != "xi-kari.v3.semantic-read-trace-input" or trace.get(
        "schema_version"
    ) != 1:
        raise ValueError("base authoring semantic read trace schema is invalid")
    records = trace.get("records")
    if not isinstance(records, list) or len(records) != 21:
        raise ValueError("base authoring semantic read trace must contain 21 records")
    ontology_trace = value.get("ontology_read_trace")
    if not isinstance(ontology_trace, Mapping):
        raise ValueError("base authoring ontology read trace is not an object")
    if (
        ontology_trace.get("schema_id") != ONTOLOGY_TRACE_INPUT_SCHEMA_ID
        or ontology_trace.get("schema_version") != 1
    ):
        raise ValueError("base authoring ontology read trace schema is invalid")
    build_ontology_read_trace(
        ontology_trace,
        plan=ontology_read_plan,
        run_id=str(ontology_read_plan.get("run_id")),
        repository_root=repository_root,
        problem_contract_sha256=contract_hash(problem_contract),
    )
    return dict(packet), dict(trace), dict(ontology_trace)


def _read_plan(lock: Mapping[str, Any], *, run_id: str) -> dict[str, Any]:
    return {
        "schema_id": "xi-kari.v3.read-plan",
        "schema_version": 3,
        "run_id": run_id,
        "framework_version": lock.get("framework_version"),
        "reader_sequence": lock.get("reader_sequence"),
        "reader_unit_count": lock.get("reader_unit_count"),
        "paragraph_count": lock.get("paragraph_count"),
        "table_count": lock.get("table_count"),
        "source_unit_count": lock.get("source_unit_count"),
        "requires_complete_semantic_read": True,
    }


def _base_request(
    *,
    run_id: str,
    mode: str,
    problem_contract: Mapping[str, Any],
    repository_root: Path,
    source_lock: Mapping[str, Any],
    read_plan: Mapping[str, Any],
    concept_authority: Mapping[str, Any],
    privacy_contract: Mapping[str, Any],
    ontology_read_plan: Mapping[str, Any],
    closed_input_materials: Sequence[Mapping[str, Any]] | None = None,
    frozen_material_manifest: Mapping[str, Any] | None = None,
    base_provider_binding: Mapping[str, Any] | None = None,
    natural_request: Mapping[str, Any] | None = None,
    contract_authoring_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source_inputs: dict[str, Any] = {
        "source_version": "v8.3",
        "repository_root": str(repository_root),
        "reader_root": str(repository_root / "references/source/v8.3/reader"),
        "source_manifest_path": str(
            repository_root / "references/source/v8.3/source-manifest.json"
        ),
        "source_lock": deepcopy(dict(source_lock)),
        "read_plan": deepcopy(dict(read_plan)),
        "concept_authority": deepcopy(dict(concept_authority)),
        "ontology_root": str(repository_root / "references/ontology"),
        "ontology_read_plan": {
            key: deepcopy(ontology_read_plan[key])
            for key in (
                "schema_version",
                "run_id",
                "problem_contract_sha256",
                "content_access_challenge",
                "proof_kind",
                "witness_protocol",
                "authority_bindings",
                "candidate_count",
                "card_count",
                "required_neighbor_count",
                "continuity_bundle_count",
                "record_count",
                "complete",
            )
        }
        | {
            "schema_id": "xi-kari.v3.ontology-read-plan-binding",
            "plan_sha256": sha256_json(ontology_read_plan),
            "item_id_protocol": (
                "candidate:{candidate_id}; card:{concept_id}; "
                "neighbor:{concept_id}:{required_neighbor_id}; bundle:{path}"
            ),
        },
    }
    if closed_input_materials is not None or frozen_material_manifest is not None:
        if closed_input_materials is None or frozen_material_manifest is None:
            raise ValueError("closed-input request materials and manifest must be paired")
        source_inputs["closed_input_materials"] = deepcopy(
            [dict(item) for item in closed_input_materials]
        )
        source_inputs["frozen_material_manifest"] = deepcopy(
            dict(frozen_material_manifest)
        )
    if base_provider_binding is not None:
        source_inputs["base_provider_binding"] = deepcopy(dict(base_provider_binding))
    request = {
        "schema_id": BASE_REQUEST_SCHEMA_ID,
        "schema_version": 1,
        "protocol": BASE_PROTOCOL,
        "run_id": run_id,
        "mode": mode,
        "problem_contract": deepcopy(dict(problem_contract)),
        "privacy_contract": deepcopy(dict(privacy_contract)),
        "source_inputs": source_inputs,
    }
    if natural_request is not None:
        request["natural_request"] = deepcopy(dict(natural_request))
    if contract_authoring_binding is not None:
        request["contract_authoring_binding"] = deepcopy(dict(contract_authoring_binding))
    return request


def _receipt(
    *,
    run_id: str,
    request_bytes: bytes,
    prompt_bytes: bytes,
    event_stream: bytes,
    stderr: bytes,
    output: bytes,
    trace: bytes,
    ontology_trace: bytes,
    ontology_read_plan_sha256: str,
    ontology_problem_contract_sha256: str,
    ontology_content_access_challenge: str,
    provider: Mapping[str, Any],
    adapter_sha256: str,
    command: Sequence[str],
    child_pid: int,
    started_at: str,
    completed_at: str,
    thread_id: str,
) -> dict[str, Any]:
    return {
        "schema_id": BASE_EXECUTION_RECEIPT_SCHEMA_ID,
        "schema_version": 1,
        "protocol": BASE_PROTOCOL,
        "run_id": run_id,
        "provider_binding_sha256": sha256_json(dict(provider)),
        "provider_executable_sha256": provider["executable_sha256"],
        "provider_argv_sha256": provider["argv_sha256"],
        "adapter_executable_sha256": adapter_sha256,
        "command_sha256": sha256_json(list(command)),
        "parent_pid": os.getpid(),
        "child_pid": child_pid,
        "started_at": started_at,
        "completed_at": completed_at,
        "exit_status": 0,
        "thread_id": thread_id,
        "input_sha256": sha256_bytes(request_bytes),
        "input_byte_count": len(request_bytes),
        "prompt_sha256": sha256_bytes(prompt_bytes),
        "prompt_byte_count": len(prompt_bytes),
        "stdout_sha256": sha256_bytes(event_stream),
        "stdout_byte_count": len(event_stream),
        "stderr_sha256": sha256_bytes(stderr),
        "stderr_byte_count": len(stderr),
        "semantic_output_sha256": sha256_bytes(output),
        "semantic_output_byte_count": len(output),
        "semantic_read_trace_sha256": sha256_json(read_json_text(trace.decode("utf-8"))),
        "semantic_read_trace_byte_count": len(trace),
        "ontology_read_plan_sha256": ontology_read_plan_sha256,
        "ontology_problem_contract_sha256": ontology_problem_contract_sha256,
        "ontology_content_access_challenge_sha256": sha256_bytes(
            ontology_content_access_challenge.encode("utf-8")
        ),
        "ontology_proof_kind": "byte-access+problem-bound-semantic-trace",
        "ontology_read_trace_sha256": sha256_json(
            read_json_text(ontology_trace.decode("utf-8"))
        ),
        "ontology_read_trace_byte_count": len(ontology_trace),
        "events_path": BASE_EVENTS_RELATIVE.as_posix(),
        "request_path": BASE_REQUEST_RELATIVE.as_posix(),
        "prompt_path": BASE_PROMPT_RELATIVE.as_posix(),
        "output_path": BASE_OUTPUT_RELATIVE.as_posix(),
        "receipt_sha256": "",
    }


def _remap_source_ids(value: Any, mapping: Mapping[str, str]) -> Any:
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, list):
        return [_remap_source_ids(item, mapping) for item in value]
    if isinstance(value, Mapping):
        return {key: _remap_source_ids(child, mapping) for key, child in value.items()}
    return value


def _validate_model_retrieval_ownership(
    retrieval: Mapping[str, Any], *, mode: str
) -> None:
    """Reject non-semantic and runtime-owned retrieval fields before projection."""

    if mode not in MODEL_RETRIEVAL_FIELDS:
        raise ValueError("unsupported model retrieval mode")
    if not isinstance(retrieval, Mapping):
        raise ValueError(f"{mode} model retrieval must be an object")
    if set(retrieval) != MODEL_RETRIEVAL_FIELDS[mode]:
        extra = set(retrieval) - MODEL_RETRIEVAL_FIELDS[mode]
        if "frozen_material_manifest" in extra:
            raise ValueError(
                "runtime-owned retrieval field is forbidden in model authoring: "
                "frozen_material_manifest"
            )
        raise ValueError(f"{mode} model retrieval fields are not exact")
    if retrieval.get("mode") != mode:
        raise ValueError("base authoring retrieval mode differs from the contract")

    collections = (
        ("query", retrieval.get("queries"), MODEL_QUERY_FIELDS[mode]),
        ("source", retrieval.get("sources"), MODEL_SOURCE_FIELDS[mode]),
        (
            "assessment",
            retrieval.get("assessments"),
            MODEL_ASSESSMENT_FIELDS[mode],
        ),
    )
    for kind, values, allowed in collections:
        if not isinstance(values, list):
            raise ValueError(f"{mode} model retrieval {kind} collection is invalid")
        for index, value in enumerate(values, start=1):
            if not isinstance(value, Mapping):
                raise ValueError(
                    f"{mode} model retrieval {kind} {index} is not an object"
                )
            observed = set(value)
            runtime_owned = observed & RUNTIME_OWNED_MODEL_FIELDS[mode][kind]
            if runtime_owned:
                raise ValueError(
                    "runtime-owned retrieval field is forbidden in model authoring: "
                    + sorted(runtime_owned)[0]
                )
            if kind == "source" and mode == "closed-input":
                required = {"source_id", "origin", "title", "content"}
                if observed - allowed or not required.issubset(observed):
                    raise ValueError(
                        f"{mode} model retrieval {kind} {index} fields are not exact"
                    )
            elif observed != allowed:
                raise ValueError(
                    f"{mode} model retrieval {kind} {index} fields are not exact"
                )


def _semantic_retrieval_input(retrieval: Mapping[str, Any]) -> dict[str, Any]:
    """Project model retrieval into the exact host-execution input shape."""

    semantic = deepcopy(dict(retrieval))
    semantic.pop("mode", None)
    queries = semantic.get("queries")
    if not isinstance(queries, list):
        raise ValueError("base authoring retrieval queries are invalid")
    semantic["queries"] = []
    for index, query in enumerate(queries, start=1):
        if not isinstance(query, Mapping):
            raise ValueError(f"base authoring retrieval query {index} is invalid")
        required = {"direction", "query", "purpose"}
        if set(query) != required:
            raise ValueError(
                f"base authoring retrieval query {index} must contain only semantic fields"
            )
        semantic["queries"].append(
            {field: query[field] for field in ("direction", "query", "purpose")}
        )

    original_sources = semantic.get("sources")
    if not isinstance(original_sources, list):
        raise ValueError("base authoring retrieval sources are invalid")
    semantic["sources"] = []
    url_by_id: dict[str, str] = {}
    for index, raw_source in enumerate(original_sources, start=1):
        if not isinstance(raw_source, Mapping):
            raise ValueError(f"base authoring retrieval source {index} is invalid")
        source_id = raw_source.get("source_id")
        url = raw_source.get("url")
        if isinstance(source_id, str) and isinstance(url, str):
            url_by_id[source_id] = url
        source = {
            key: raw_source[key]
            for key in (
                "origin",
                "title",
                "url",
                "publisher",
                "content",
                "excerpt",
                "published_at",
                "event_at",
            )
            if key in raw_source
        }
        if "excerpt" not in source and "content" in source:
            source["excerpt"] = source.pop("content")
        semantic["sources"].append(source)

    raw_assessments = semantic.get("assessments")
    if not isinstance(raw_assessments, list):
        raise ValueError("base authoring retrieval assessments are invalid")
    semantic["assessments"] = []
    for index, raw_assessment in enumerate(raw_assessments, start=1):
        if not isinstance(raw_assessment, Mapping):
            raise ValueError(
                f"base authoring retrieval assessment {index} is invalid"
            )
        assessment = dict(raw_assessment)
        if "source_url" not in assessment and isinstance(
            assessment.get("source_id"), str
        ):
            assessment["source_url"] = url_by_id.get(assessment["source_id"])
        if "source_lineage_urls" not in assessment and "source_lineage" in assessment:
            assessment["source_lineage_urls"] = [
                url_by_id.get(item, item) for item in assessment["source_lineage"]
            ]
        if "conflict_source_urls" not in assessment and "conflict_source_ids" in assessment:
            assessment["conflict_source_urls"] = [
                url_by_id.get(item, item) for item in assessment["conflict_source_ids"]
            ]
        semantic["assessments"].append(
            {
                key: assessment[key]
                for key in (
                    "source_url",
                    "authority",
                    "independence",
                    "independence_identity",
                    "source_lineage_urls",
                    "interest_relevance",
                    "affected_positions",
                    "low_power_positions",
                    "conflict_source_urls",
                    "freshness",
                    "relevance",
                    "verdict",
                    "limitations",
                    "cannot_prove",
                )
                if key in assessment
            }
        )
    return semantic


def _validate_retrieval_projection_paths(
    model_retrieval: Mapping[str, Any], projected: Mapping[str, Any]
) -> None:
    """Keep index-addressed model visibility decisions on the same semantics."""

    mode = model_retrieval.get("mode")
    model_queries = model_retrieval.get("queries")
    projected_queries = projected.get("queries")
    if not isinstance(model_queries, list) or not isinstance(projected_queries, list):
        raise ValueError("retrieval projection query paths are unavailable")
    model_query_identities = [
        (query.get("direction"), query.get("query"))
        for query in model_queries
        if isinstance(query, Mapping)
    ]
    projected_query_identities = [
        (query.get("direction"), query.get("query"))
        for query in projected_queries
        if isinstance(query, Mapping)
    ]
    if (
        len(model_query_identities) != len(model_queries)
        or model_query_identities != projected_query_identities
    ):
        raise ValueError("retrieval projection changed model-owned query paths")

    model_sources = model_retrieval.get("sources")
    projected_sources = projected.get("sources")
    if not isinstance(model_sources, list) or not isinstance(projected_sources, list):
        raise ValueError("retrieval projection source paths are unavailable")
    identity_field = "url" if mode == "open-world" else "source_id"
    model_source_identities = [
        source.get(identity_field)
        for source in model_sources
        if isinstance(source, Mapping)
    ]
    projected_source_identities = [
        source.get(identity_field)
        for source in projected_sources
        if isinstance(source, Mapping)
    ]
    if (
        len(model_source_identities) != len(model_sources)
        or model_source_identities != projected_source_identities
    ):
        raise ValueError("retrieval projection changed model-owned source paths")

    model_assessments = model_retrieval.get("assessments")
    projected_assessments = projected.get("assessments")
    if not isinstance(model_assessments, list) or not isinstance(
        projected_assessments, list
    ):
        raise ValueError("retrieval projection assessment paths are unavailable")
    if mode == "open-world":
        model_url_by_id = {
            source.get("source_id"): source.get("url")
            for source in model_sources
            if isinstance(source, Mapping)
        }
        projected_url_by_id = {
            source.get("source_id"): source.get("url")
            for source in projected_sources
            if isinstance(source, Mapping)
        }
        model_assessment_identities = [
            assessment.get("source_url")
            or model_url_by_id.get(assessment.get("source_id"))
            for assessment in model_assessments
            if isinstance(assessment, Mapping)
        ]
        projected_assessment_identities = [
            projected_url_by_id.get(assessment.get("source_id"))
            for assessment in projected_assessments
            if isinstance(assessment, Mapping)
        ]
    else:
        model_assessment_identities = [
            assessment.get("source_id")
            for assessment in model_assessments
            if isinstance(assessment, Mapping)
        ]
        projected_assessment_identities = [
            assessment.get("source_id")
            for assessment in projected_assessments
            if isinstance(assessment, Mapping)
        ]
    if (
        len(model_assessment_identities) != len(model_assessments)
        or model_assessment_identities != projected_assessment_identities
    ):
        raise ValueError("retrieval projection changed model-owned assessment paths")


def _project_retrieval(
    packet: dict[str, Any],
    *,
    event_stream: bytes,
    receipt: Mapping[str, Any],
    request_bytes: bytes,
    run_id: str,
    provider: Mapping[str, Any],
    adapter_sha256: str,
    child_pid: int,
    started_at: str,
    completed_at: str,
    evidence_cutoff: str,
    closed_input_materials: Sequence[Mapping[str, Any]] | None = None,
    frozen_material_manifest: Mapping[str, Any] | None = None,
    host_captures: Mapping[str, HostCapture] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    mode = packet["retrieval"]["mode"]
    _validate_model_retrieval_ownership(packet["retrieval"], mode=mode)
    if mode == "closed-input":
        if closed_input_materials is None or frozen_material_manifest is None:
            raise ValueError("closed-input projection has no frozen material binding")
        _events, thread_id = _event_objects(event_stream)
        semantic, projected, query_bindings, source_bindings = _normalize_closed_semantic(
            packet["retrieval"],
            closed_input_materials,
            manifest=frozen_material_manifest,
            run_id=run_id,
            completed_at=completed_at,
        )
        _validate_retrieval_projection_paths(packet["retrieval"], projected)
        packet = deepcopy(packet)
        packet["retrieval"] = projected
        closed_receipt: dict[str, Any] = {
            "schema_id": "xi-kari.v3.closed-input-execution",
            "schema_version": 1,
            "run_id": run_id,
            "web_search_executed": False,
            "event_stream_sha256": sha256_bytes(event_stream),
            "event_count": len(event_stream.splitlines()),
            "base_request_sha256": sha256_bytes(request_bytes),
            "semantic_retrieval_sha256": sha256_json(semantic),
            "frozen_material_manifest_sha256": sha256_json(
                dict(frozen_material_manifest)
            ),
            "retrieval_sha256": sha256_json(projected),
            "provider_binding_sha256": sha256_json(dict(provider)),
            "adapter_executable_sha256": adapter_sha256,
            "child_pid": child_pid,
            "started_at": started_at,
            "completed_at": completed_at,
            "exit_status": 0,
            "thread_id": thread_id,
            "query_bindings": query_bindings,
            "source_bindings": source_bindings,
            "receipt_sha256": "",
        }
        closed_receipt["receipt_sha256"] = sha256_json(
            {
                key: value
                for key, value in closed_receipt.items()
                if key != "receipt_sha256"
            }
        )
        return packet, closed_receipt, semantic
    semantic = _semantic_retrieval_input(packet["retrieval"])
    if host_captures is not None and not isinstance(host_captures, Mapping):
        raise ValueError("host capture binding is invalid")
    original_sources = list(packet["retrieval"].get("sources", []))
    # The host projection intentionally strips model-controlled IDs.  Keep a
    # private alias map so evidence authored with an ID or URL still resolves
    # to the runtime-owned source ID after projection.
    aliases: dict[str, str] = {}
    for source in original_sources:
        if isinstance(source, Mapping):
            source_id = source.get("source_id")
            url = source.get("url")
            if isinstance(source_id, str) and isinstance(url, str):
                aliases[source_id] = url
    # ``semantic`` is already stripped to the host projection shape above.
    url_by_id = {
        source.get("source_id"): source.get("url")
        for source in original_sources
        if isinstance(source, Mapping)
        and isinstance(source.get("source_id"), str)
        and isinstance(source.get("url"), str)
    }
    projected, host_receipt = project_runtime_retrieval(
        semantic,
        event_stream,
        run_id=run_id,
        execution_context_id=f"XK-BASE-{uuid.uuid4().hex}",
        provider_binding_sha256=sha256_json(dict(provider)),
        adapter_executable_sha256=adapter_sha256,
        adapter_input=request_bytes,
        parent_pid=os.getpid(),
        child_pid=child_pid,
        started_at=started_at,
        completed_at=completed_at,
        exit_status=0,
        stderr_sha256=str(receipt["stderr_sha256"]),
        evidence_cutoff=evidence_cutoff,
        host_captures=host_captures,
    )
    _validate_retrieval_projection_paths(packet["retrieval"], projected)
    runtime_ids = {
        source.get("url"): source.get("source_id")
        for source in projected.get("sources", [])
        if isinstance(source, Mapping)
    }
    for key, url in list(aliases.items()):
        if url in runtime_ids:
            aliases[key] = runtime_ids[url]
    packet = _remap_source_ids(packet, aliases)
    packet["retrieval"] = projected
    return packet, host_receipt, semantic


def _write_raw_events(path: Path, raw: bytes) -> None:
    if path.exists() and path.is_symlink():
        raise ValueError("base authoring event path is a symlink")
    atomic_write_bytes(path, raw)


def _rebind_visibility_ledger(
    packet: dict[str, Any], *, privacy_purpose: str
) -> None:
    """Rebind disclosure decisions after runtime-only retrieval projection.

    The model's pre-projection ledger can contain semantic fields (such as a
    query ``purpose``) that the host deliberately removes, while the host adds
    observed execution fields (query IDs, status and timestamps).  Retaining
    the stale ledger would either leave dangling paths or silently omit the
    new fields.  Preserve every decision whose path survived and mark only the
    runtime-generated metadata as public; model-authored content paths retain
    their original classification.
    """

    retrieval = packet.get("retrieval")
    mode = retrieval.get("mode") if isinstance(retrieval, Mapping) else None
    if mode not in RUNTIME_OWNED_VISIBILITY_POLICIES:
        raise ValueError("visibility projection has an unsupported retrieval mode")
    runtime_policy = RUNTIME_OWNED_VISIBILITY_POLICIES[mode]
    runtime_only_paths = set(RUNTIME_ONLY_VISIBILITY_PATHS[mode])
    omitted_paths = set(PROJECTION_OMITTED_VISIBILITY_PATHS[mode])
    original = packet.get("visibility_ledger")
    original_entries = original.get("entries") if isinstance(original, Mapping) else None
    if not isinstance(original_entries, list):
        raise ValueError("visibility ledger entries must be a list")
    paths = [
        entry.get("canonical_path")
        for entry in original_entries
        if isinstance(entry, Mapping)
    ]
    if len(paths) != len(original_entries) or any(
        not isinstance(path, str) or not path for path in paths
    ):
        raise ValueError("visibility ledger canonical path must be non-empty")
    if len(paths) != len(set(paths)):
        raise ValueError("visibility ledger contains duplicate semantic atom")
    by_path = {
        str(entry["canonical_path"]): dict(entry) for entry in original_entries
    }
    ownership_collisions = sorted(
        path
        for path in by_path
        if _VISIBILITY_INDEX.sub("[*]", path) in runtime_only_paths
    )
    if ownership_collisions:
        raise ValueError(
            "runtime-owned visibility path was preoccupied by model authoring: "
            + ownership_collisions[0]
        )
    final_paths = set(semantic_atom_paths(packet))
    model_paths = set(by_path)
    projection_added_paths = final_paths - model_paths
    dangling = sorted(
        path
        for path in by_path
        if path not in final_paths
        and _VISIBILITY_INDEX.sub("[*]", path) not in omitted_paths
    )
    if dangling:
        raise ValueError(
            "visibility ledger contains dangling semantic atom: " + dangling[0]
        )
    entries: list[dict[str, Any]] = []
    # JSON object key order is not semantic.  Sort the atom paths before
    # sealing the ledger so the pre-materialization packet and a fresh
    # disk-replay (which has passed through canonical JSON key sorting) produce
    # the same ordered evidence, regardless of how a provider ordered fields.
    for path in sorted(final_paths):
        if path in projection_added_paths:
            policy = runtime_policy.get(_VISIBILITY_INDEX.sub("[*]", path))
            if policy is None:
                raise ValueError(
                    "retrieval projection added an unowned visibility path: " + path
                )
            classification, disclosure = policy
            entry = {
                "canonical_path": path,
                "classification": classification,
                "disclosure": disclosure,
                "purpose": privacy_purpose,
                "authority_refs": [],
                "protection_reason": None,
            }
        else:
            entry = by_path.get(path)
            if entry is None:
                raise ValueError("visibility ledger is missing semantic atom: " + path)
        if entry.get("purpose") != privacy_purpose:
            raise ValueError(
                "visibility ledger purpose differs from XK0 privacy contract"
            )
        entries.append(entry)
    packet["visibility_ledger"] = {"entries": entries}
    validate_visibility_ledger(packet, expected_purpose=privacy_purpose)


def _preserve_authoring_failure(
    error: Exception, *, stage: str, run_id: str, repository_root: Path,
    diagnostics_root: Path | None, process: subprocess.Popen[bytes], command: list[str],
    provider: Mapping[str, Any], request: bytes, prompt: bytes, events: bytes, stderr: bytes,
    input_complete: bool, started_at: str, workspace: Path, notice_path: Path, output_limit: int,
) -> AuthoringFailure:
    from .materialization import default_runs_root, _require_external_runs_root

    root = Path(diagnostics_root or default_runs_root()).expanduser().resolve()
    _require_external_runs_root(root, repository_root)
    root.mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix=f"failed-{_safe_run_id(run_id)}-", dir=root))
    if isinstance(error, AuthoringCommunicationError):
        events, stderr, input_complete = error.stdout, error.stderr, error.input_complete
    for name, raw in (("request.bin", request), ("prompt.txt", prompt),
                      ("events.jsonl", events), ("stderr.bin", stderr)):
        atomic_write_bytes(destination / name, raw)
    file_observations = {}
    for name, path, limit in (("completion-notice.bin", notice_path, 4096),
                              ("semantic-output.bin", workspace / SEMANTIC_OUTPUT_FILENAME, output_limit)):
        try:
            raw = read_bounded_regular_file(path, limit=limit)
        except (OSError, ValueError) as capture_error:
            file_observations[name] = {"captured": False, "error": str(capture_error)}
        else:
            atomic_write_bytes(destination / name, raw)
            file_observations[name] = {"captured": True, "byte_count": len(raw)}
    atomic_write_json(destination / "failure.json", {
        "state": "failed", "stage": stage, "run_id": run_id,
        "parent_pid": os.getpid(), "child_pid": process.pid, "exit_status": process.returncode,
        "started_at": started_at, "failed_at": _utc_now(), "input_complete": input_complete,
        "timeout_seconds": provider["timeout_seconds"], "command": command,
        "provider_binding": dict(provider), "workspace": str(workspace),
        "error_chain": failure_causes(error), "file_observations": file_observations,
    })
    return AuthoringFailure(str(error), destination)


def _author_natural_contract(
    *, run_id: str, natural_request: Mapping[str, Any], draft_problem_contract: Mapping[str, Any],
    repository_root: Path, provider: Mapping[str, Any], timeout_seconds: int,
    failure_diagnostics_root: Path | None = None,
    closed_input_materials: Sequence[Mapping[str, Any]] | None = None,
    frozen_material_manifest: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Capture a separate real author process before binding any source-read proof."""

    request = contract_authoring_request(run_id=run_id, natural_request=natural_request,
        draft_problem_contract=draft_problem_contract, repository_root=repository_root, provider=provider,
        closed_input_materials=closed_input_materials, frozen_material_manifest=frozen_material_manifest)
    request_bytes = canonical_bytes(request) + b"\n"
    prompt = contract_authoring_prompt(request)
    if len(prompt) > MAX_BASE_INPUT_BYTES:
        raise ValueError("contract author prompt exceeds the size limit")
    started_at = _utc_now()
    with private_authoring_directory(prefix="xi-kari-contract-authoring-",
            repository_root=repository_root, runs_root=failure_diagnostics_root) as temporary:
        capture_root = Path(temporary)
        workspace = capture_root / "author-workspace"
        workspace.mkdir()
        notice_path = capture_root / "completion-notice.txt"
        command = [*provider["argv"], "--json", "--output-last-message", str(notice_path), "-"]
        launch_command = _provider_launch_argv(provider, command)
        process = subprocess.Popen(launch_command, cwd=workspace, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, **_process_isolation_kwargs())
        events, stderr, input_complete = b"", b"", False
        try:
            events, stderr, input_complete = _communicate_limited(process, prompt,
                timeout_seconds=timeout_seconds, label="natural contract author")
            completed_at = _utc_now()
            if process.returncode != 0 or not input_complete:
                raise ValueError("natural contract author did not complete successfully")
            _strict_event_stream(events)
            notice = read_bounded_regular_file(notice_path, limit=4096)
            output = read_semantic_output(workspace, notice=notice, limit=MAX_BASE_INPUT_BYTES)
            frozen = parse_contract_authoring_output(output, natural_request=natural_request, repository_root=repository_root)
        except Exception as error:
            _terminate(process)
            raise _preserve_authoring_failure(error, stage="natural-contract", run_id=run_id,
                repository_root=repository_root, diagnostics_root=failure_diagnostics_root,
                process=process, command=launch_command, provider=provider, request=request_bytes,
                prompt=prompt, events=events, stderr=stderr, input_complete=input_complete,
                started_at=started_at, workspace=workspace, notice_path=notice_path,
                output_limit=MAX_BASE_INPUT_BYTES) from error
    evidence = contract_authoring_evidence(run_id=run_id, provider=provider, command=launch_command,
        request_bytes=request_bytes, prompt_bytes=prompt, output_bytes=output,
        events_bytes=events, stderr_bytes=stderr, parent_pid=os.getpid(), child_pid=process.pid,
        started_at=started_at, completed_at=completed_at, frozen_problem_contract=frozen)
    validate_contract_authoring_evidence(evidence, run_id=run_id, natural_request=natural_request,
        frozen_problem_contract=frozen, repository_root=repository_root,
        closed_input_materials=closed_input_materials, frozen_material_manifest=frozen_material_manifest)
    return frozen, evidence


def execute_authored_run(
    runs_root: Path,
    *,
    problem_contract: Mapping[str, Any] | None = None,
    request_text: str | None = None,
    mode: str = "open-world",
    run_id: str | None = None,
    repository_root: Path | None = None,
    codex_provider_executable: str | Path | None = None,
    closed_input_materials: Sequence[Mapping[str, Any]] | None = None,
    timeout_seconds: int = DEFAULT_ADAPTER_TIMEOUT_SECONDS,
    privacy_purpose: str = "回答冻结问题并仅向请求用户交付",
    delivery_audience: str = "requesting-user",
    _continuation_kind: str = "original",
    _parent_run_id: str | None = None,
    _parent_chain_head_sha256: str | None = None,
    _generation: int = 0,
    _natural_request: Mapping[str, Any] | None = None,
    _prepare_only: bool = False,
) -> dict[str, Any]:
    """Run one production base author and materialize a complete run.

    The public seam accepts either a complete XK0 contract or ordinary natural
    language.  Natural language first receives a runtime-owned conservative
    draft; a separate contract author fills semantic boundary fields and the
    runtime freezes the final contract before creating source-reading proofs.
    The full base author cannot revise that contract. The shipped adapter is bound
    into XK0 for the later XK9 probes; the base process itself is started here
    so its PID and raw JSONL cannot be supplied by the model or caller.
    """

    from .authority import repository_root as resolve_repository_root
    from .materialization import default_runs_root

    if mode not in {"open-world", "closed-input"}:
        raise ValueError("unsupported execution mode")
    if _continuation_kind not in {"original", "fork", "repair"}:
        raise ValueError("unsupported continuation kind")
    if (
        (_continuation_kind == "original" and _parent_run_id is not None)
        or (_continuation_kind != "original" and _parent_run_id is None)
    ):
        raise ValueError(
            "continuation parent binding is required for fork and repair"
        )
    if not isinstance(_generation, int) or isinstance(_generation, bool) or _generation < 0:
        raise ValueError("continuation generation is invalid")
    if (problem_contract is None) == (request_text is None):
        raise ValueError(
            "provide exactly one complete problem_contract or natural request_text"
        )
    if not isinstance(timeout_seconds, int) or isinstance(timeout_seconds, bool) or not 1 <= timeout_seconds <= MAX_AUTHORING_TIMEOUT_SECONDS:
        raise ValueError("base authoring timeout must be 1-7200 seconds")
    natural_request: dict[str, Any] | None = None
    frozen_privacy = _privacy_contract(
        purpose=privacy_purpose,
        delivery_audience=delivery_audience,
    )
    if request_text is not None:
        cutoff = _natural_evidence_cutoff(timeout_seconds)
        natural_request = build_natural_request_envelope(
            normalize_natural_request(request_text),
            mode=mode,
            evidence_cutoff=cutoff,
        )
        frozen = draft_problem_contract_from_natural_request(
            natural_request["text"],
            mode=mode,
            evidence_cutoff=cutoff,
        )
    else:
        frozen = validate_problem_contract(problem_contract or {}, mode=mode)
        if _natural_request is not None:
            if not isinstance(_natural_request, Mapping):
                raise ValueError("continuation natural request is not an object")
            natural_request = dict(_natural_request)
            frozen = freeze_natural_problem_contract(
                frozen,
                request=natural_request,
                mode=mode,
            )
    if mode == "closed-input" and not closed_input_materials:
        raise ValueError("closed-input materials must be frozen before execution")
    if mode == "open-world" and closed_input_materials is not None:
        raise ValueError("open-world execution cannot accept closed-input materials")
    frozen_material_records: list[dict[str, Any]] | None = None
    frozen_material_manifest: dict[str, Any] | None = None
    if mode == "closed-input":
        frozen_material_records, frozen_material_manifest = freeze_closed_input_materials(
            closed_input_materials or [],
            evidence_cutoff=frozen["evidence_cutoff"],
        )
    repo = resolve_repository_root(repository_root or Path(__file__).resolve().parents[2])
    if codex_provider_executable is None:
        raise ValueError("Codex provider executable is required for production execution")
    selected_run_id = _safe_run_id(
        run_id or f"xk-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:12]}"
    )
    formal_adapter = repo / FORMAL_ADAPTER_RELATIVE_PATH
    binding = bind_semantic_authoring_adapter(
        formal_adapter,
        timeout_seconds=timeout_seconds,
        profile=FORMAL_ADAPTER_PROFILE,
        codex_provider_executable=codex_provider_executable,
        repository_root=repo,
    )
    provider = binding["provider_binding"]
    base_provider = bind_base_authoring_provider(
        codex_provider_executable,
        mode=mode,
        repository_root=repo,
        timeout_seconds=timeout_seconds,
    )
    contract_evidence = None
    if request_text is not None:
        contract_provider = bind_base_authoring_provider(
            codex_provider_executable, mode="closed-input", repository_root=repo,
            timeout_seconds=timeout_seconds,
        )
        frozen, contract_evidence = _author_natural_contract(
            run_id=selected_run_id, natural_request=natural_request or {},
            draft_problem_contract=frozen, repository_root=repo, provider=contract_provider,
            timeout_seconds=timeout_seconds,
            failure_diagnostics_root=runs_root,
            closed_input_materials=frozen_material_records,
            frozen_material_manifest=frozen_material_manifest,
        )
    lock, source_events = build_full_source_lock(repo, run_id=selected_run_id)
    read_plan = _read_plan(lock, run_id=selected_run_id)
    problem_contract_sha256 = contract_hash(frozen)
    content_access_challenge = secrets.token_hex(32)
    ontology_read_plan = build_ontology_read_plan(
        repo,
        run_id=selected_run_id,
        problem_contract_sha256=problem_contract_sha256,
        content_access_challenge=content_access_challenge,
    )
    _rows, concept_authority = load_concept_authority(repo)
    request = _base_request(
        run_id=selected_run_id,
        mode=mode,
        problem_contract=frozen,
        repository_root=repo,
        source_lock=lock,
        read_plan=read_plan,
        concept_authority=concept_authority,
        privacy_contract=frozen_privacy,
        ontology_read_plan=ontology_read_plan,
        closed_input_materials=frozen_material_records,
        frozen_material_manifest=frozen_material_manifest,
        base_provider_binding=base_provider,
        natural_request=natural_request,
        contract_authoring_binding=(
            {"receipt_sha256": contract_evidence["receipt"]["receipt_sha256"],
             "problem_contract_sha256": contract_hash(frozen)} if contract_evidence is not None else None
        ),
    )
    request_bytes = canonical_bytes(request) + b"\n"
    prompt = _base_prompt(request)
    schema_path = repo / BASE_OUTPUT_SCHEMA_RELATIVE
    if not schema_path.is_file():
        raise ValueError(f"base authoring output schema is missing: {schema_path}")

    started_at = _utc_now()
    raw_events = b""
    stderr = b""
    output = b""
    child_pid = 0
    command = [
        *base_provider["argv"],
        "--json", "--output-last-message", "__runtime_owned_completion_notice__", "-",
    ]
    with private_authoring_directory(prefix="xi-kari-base-authoring-",
            repository_root=repo, runs_root=runs_root) as temporary:
        capture_root = Path(temporary)
        workspace = capture_root / "author-workspace"
        workspace.mkdir()
        notice_path = capture_root / "completion-notice.txt"
        command[-2] = str(notice_path)
        launch_command = _provider_launch_argv(base_provider, command)
        process = subprocess.Popen(
            launch_command, cwd=workspace, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,
            **_process_isolation_kwargs(),
        )
        child_pid = int(process.pid)
        input_complete = False
        failure_stage = "base-authoring"
        try:
            raw_events, stderr, input_complete = _communicate_limited(
                process, prompt, timeout_seconds=timeout_seconds,
                label="base authoring provider",
            )
            completed_at = _utc_now()
            if process.returncode != 0:
                excerpt = stderr[:4096].decode("utf-8", errors="replace").strip()
                suffix = f": {excerpt}" if excerpt else ""
                raise ValueError(f"base authoring process exited with status {process.returncode}{suffix}")
            if not input_complete:
                raise ValueError("base authoring process did not consume the complete request")
            thread_id, events = _strict_event_stream(raw_events)
            notice = read_bounded_regular_file(notice_path, limit=4096)
            output = read_semantic_output(workspace, notice=notice, limit=MAX_BASE_OUTPUT_BYTES)
            packet, trace_value, ontology_trace_value = _parse_base_output(
                output, problem_contract=frozen, mode=mode,
                ontology_read_plan=ontology_read_plan, repository_root=repo,
                natural_request=natural_request,
            )
            validate_semantic_read_trace_input(
                trace_value, repository_root=repo, source_lock=lock,
                source_events=source_events,
            )
            validate_visibility_ledger(
                packet, expected_purpose=str(frozen_privacy["purpose"])
            )
            failure_stage = "base-finalization"
            trace_bytes = canonical_bytes(trace_value) + b"\n"
            ontology_trace_bytes = canonical_bytes(ontology_trace_value) + b"\n"
            receipt = _receipt(
                run_id=selected_run_id,
                request_bytes=request_bytes,
                prompt_bytes=prompt,
                event_stream=raw_events,
                stderr=stderr,
                output=output,
                trace=trace_bytes,
                ontology_trace=ontology_trace_bytes,
                ontology_read_plan_sha256=sha256_json(ontology_read_plan),
                ontology_problem_contract_sha256=problem_contract_sha256,
                ontology_content_access_challenge=content_access_challenge,
                provider=base_provider,
                adapter_sha256=binding["executable_sha256"],
                command=launch_command,
                child_pid=child_pid,
                started_at=started_at,
                completed_at=completed_at,
                thread_id=str(thread_id),
            )
            if contract_evidence is not None:
                validate_contract_authoring_evidence(contract_evidence, run_id=selected_run_id,
                    natural_request=natural_request or {}, frozen_problem_contract=frozen,
                    repository_root=repo, base_started_at=started_at,
                    closed_input_materials=frozen_material_records,
                    frozen_material_manifest=frozen_material_manifest)
                receipt["contract_authoring_evidence"] = contract_evidence
            receipt["receipt_sha256"] = sha256_json(
                {key: value for key, value in receipt.items() if key != "receipt_sha256"}
            )

            # Validate and host-project retrieval before creating a run directory.  A
            # model that invents closed material, omits a source, or lacks observed web
            # events therefore leaves no resumable XK0/XK1 shell behind.
            host_captures: dict[str, HostCapture] | None = None
            failure_stage = "retrieval-projection"
            if mode == "open-world":
                host_captures = capture_host_sources(
                    _semantic_retrieval_input(packet["retrieval"])
                )
            packet, host_receipt, semantic_retrieval = _project_retrieval(
                packet,
                event_stream=raw_events,
                receipt=receipt,
                request_bytes=request_bytes,
                run_id=selected_run_id,
                provider=base_provider,
                adapter_sha256=binding["executable_sha256"],
                child_pid=child_pid,
                started_at=started_at,
                completed_at=completed_at,
                evidence_cutoff=frozen["evidence_cutoff"],
                closed_input_materials=frozen_material_records,
                frozen_material_manifest=frozen_material_manifest,
                host_captures=host_captures,
            )
            host_capture_index: dict[str, Any] | None = None
            if host_captures is not None:
                host_capture_index = build_host_capture_index(
                    run_id=selected_run_id,
                    event_stream_sha256=str(host_receipt["event_stream_sha256"]),
                    retrieval=packet["retrieval"],
                    semantic_retrieval=semantic_retrieval,
                    host_captures=host_captures,
                )
            packet["schema_id"] = "xi-kari.v3.analysis-packet"
            packet["schema_version"] = 3
            _rebind_visibility_ledger(
                packet, privacy_purpose=str(frozen_privacy["purpose"])
            )
            execute_owned_binding = build_execute_owned_binding(receipt, host_receipt)

            # Build the run only after both the semantic envelope and retrieval boundary
            # are valid; successful runs retain every captured byte below.
            staging_root = Path(runs_root or default_runs_root()).expanduser().resolve()
            failure_stage = "run-preparation"
            with tempfile.TemporaryDirectory(prefix="xi-kari-base-input-") as temporary:
                trace_path = Path(temporary) / "semantic-read-trace.json"
                trace_path.write_bytes(trace_bytes)
                ontology_trace_path = Path(temporary) / "ontology-read-trace.json"
                ontology_trace_path.write_bytes(ontology_trace_bytes)
                preparation_capability = _issue_production_preparation_capability(
                    run_id=selected_run_id,
                    problem_contract=frozen,
                    semantic_trace_path=trace_path,
                    ontology_trace_path=ontology_trace_path,
                    base_authoring_execution=receipt,
                    base_authoring_events=raw_events,
                    execute_owned_binding=execute_owned_binding,
                    process=process,
                    request_bytes=request_bytes,
                    prompt_bytes=prompt,
                    stderr_bytes=stderr,
                    output_bytes=output,
                    retrieval_receipt=host_receipt,
                )
                run_dir = _prepare_production_run(
                    staging_root,
                    capability=preparation_capability,
                    problem_contract=frozen,
                    mode=mode,
                    run_id=selected_run_id,
                    repository_root=repo,
                    semantic_read_trace_path=trace_path,
                    ontology_read_trace_path=ontology_trace_path,
                    ontology_read_plan=ontology_read_plan,
                    semantic_authoring_adapter=formal_adapter,
                    semantic_authoring_timeout_seconds=timeout_seconds,
                    semantic_authoring_profile=FORMAL_ADAPTER_PROFILE,
                    codex_provider_executable=codex_provider_executable,
                    privacy_purpose=str(frozen_privacy["purpose"]),
                    delivery_audience=str(frozen_privacy["delivery_audience"]),
                    base_authoring_execution=receipt,
                    base_authoring_events=raw_events,
                    base_authoring_request=request_bytes,
                    base_authoring_prompt=prompt,
                    base_authoring_output=output,
                    semantic_retrieval_input={
                        "schema_id": "xi-kari.v3.retrieval-semantic-input",
                        "schema_version": 1,
                        "run_id": selected_run_id,
                        "mode": mode,
                        **semantic_retrieval,
                    },
                    retrieval_execution_receipt=host_receipt,
                    natural_request=natural_request,
                    continuation_kind=_continuation_kind,
                    generation=_generation,
                    parent_run_id=_parent_run_id,
                    parent_chain_head_sha256=_parent_chain_head_sha256,
                )
            _write_raw_events(run_dir / BASE_EVENTS_RELATIVE, raw_events)
            atomic_write_bytes(run_dir / BASE_REQUEST_RELATIVE, request_bytes)
            atomic_write_bytes(run_dir / BASE_PROMPT_RELATIVE, prompt)
            atomic_write_bytes(run_dir / BASE_OUTPUT_RELATIVE, output)
            atomic_write_json(run_dir / BASE_RECEIPT_RELATIVE, receipt)
            atomic_write_json(
                run_dir / SEMANTIC_RETRIEVAL_RELATIVE,
                {
                    "schema_id": "xi-kari.v3.retrieval-semantic-input",
                    "schema_version": 1,
                    "run_id": selected_run_id,
                    "mode": mode,
                    **semantic_retrieval,
                },
            )
            atomic_write_json(run_dir / RETRIEVAL_RECEIPT_RELATIVE, host_receipt)
            if host_capture_index is not None:
                write_host_capture_bundle(
                    run_dir,
                    index=host_capture_index,
                    host_captures=host_captures or {},
                )
        except Exception as error:
            _terminate(process)
            raise _preserve_authoring_failure(error, stage=failure_stage, run_id=selected_run_id,
                repository_root=repo, diagnostics_root=runs_root, process=process,
                command=launch_command, provider=base_provider, request=request_bytes,
                prompt=prompt, events=raw_events, stderr=stderr, input_complete=input_complete,
                started_at=started_at, workspace=workspace, notice_path=notice_path,
                output_limit=MAX_BASE_OUTPUT_BYTES) from error
    if _prepare_only:
        # A continuation may intentionally stop at XK1, but it still carries
        # the exact packet that the fresh base author produced.  Persist only
        # runtime-owned bindings here; later materialization rereads these
        # bytes and revalidates the full base/retrieval replay.
        packet_for_disk = dict(packet)
        concept_dispositions, _authority = load_concept_authority(repo)
        packet_for_disk["concept_disposition"] = concept_dispositions
        packet_for_disk["runtime_binding"] = build_runtime_packet_binding(
            read_json(run_dir / "run-contract.json")
        )
        atomic_write_json(
            run_dir / "continuation" / "input-packet.json", packet_for_disk
        )
        return status_run(run_dir)
    # The materializer owns packet injection and all downstream phase seals.
    result = materialize_run(run_dir, packet, repository_root=repo)
    if result.get("state") != "complete":
        raise ValueError(f"production execution did not reach signed completion: {result}")
    return result


def execute_natural_request(
    runs_root: Path,
    *,
    request_text: str,
    mode: str = "open-world",
    run_id: str | None = None,
    repository_root: Path | None = None,
    codex_provider_executable: str | Path | None = None,
    closed_input_materials: Sequence[Mapping[str, Any]] | None = None,
    timeout_seconds: int = DEFAULT_ADAPTER_TIMEOUT_SECONDS,
    privacy_purpose: str = "回答冻结问题并仅向请求用户交付",
    delivery_audience: str = "requesting-user",
) -> dict[str, Any]:
    """Public natural-language entry point; all authority remains in runtime."""

    return execute_authored_run(
        runs_root,
        request_text=request_text,
        mode=mode,
        run_id=run_id,
        repository_root=repository_root,
        codex_provider_executable=codex_provider_executable,
        closed_input_materials=closed_input_materials,
        timeout_seconds=timeout_seconds,
        privacy_purpose=privacy_purpose,
        delivery_audience=delivery_audience,
    )


__all__ = [
    "BASE_EVENTS_RELATIVE",
    "BASE_RECEIPT_RELATIVE",
    "BASE_REQUEST_SCHEMA_ID",
    "BASE_OUTPUT_SCHEMA_ID",
    "RETRIEVAL_RECEIPT_RELATIVE",
    "SEMANTIC_RETRIEVAL_RELATIVE",
    "execute_authored_run",
    "execute_natural_request",
]
