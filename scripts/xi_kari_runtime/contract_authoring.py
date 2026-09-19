"""Runtime-owned evidence for freezing a natural request before semantic reading."""

from __future__ import annotations

import base64
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .authoring import require_base_authoring_provider
from .canonical_json import canonical_bytes, canonical_dumps, read_json_text, sha256_bytes, sha256_json
from .output_transport import parse_provider_events
from .problem_contract import (
    contract_hash, draft_problem_contract_from_natural_request,
    freeze_natural_problem_contract, parse_instant,
)
from .world_volume import _schema_validator


PROTOCOL = "xi-kari.v3.natural-contract-authoring/v1"
OUTPUT_SCHEMA = "xk-natural-contract-output.schema.json"
EVIDENCE_FIELDS = {
    "receipt", "provider_binding", "command", "request_text", "prompt_text",
    "output_text", "event_stream_text", "stderr_base64",
}


def contract_authoring_request(*, run_id: str, natural_request: Mapping[str, Any],
                               draft_problem_contract: Mapping[str, Any],
                               repository_root: Path, provider: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_id": "xi-kari.v3.natural-contract-request", "schema_version": 1,
        "protocol": PROTOCOL, "run_id": run_id,
        "repository_root": str(repository_root),
        "natural_request": dict(natural_request),
        "draft_problem_contract": dict(draft_problem_contract),
        "provider_binding_sha256": sha256_json(dict(provider)),
    }


def contract_authoring_prompt(request: Mapping[str, Any]) -> bytes:
    return (
        "本次只负责将用户原始请求整理成待冻结的问题合同，不开展理论分析、检索或推演。"
        "保留作者自定义术语，不用通常词义替换；尚不明确的范围要具体登记未知，不能扩大任务。"
        "必须原样保留自然请求的 question、evidence_cutoff、检索模式；"
        "只完善对象、边界、同一性、空间与组织尺度、时间窗、立场、行动类型和交付用途。"
        "只返回 FROZEN_FIELDS 对应的十三个语义字段，不能写PID、散列、回执或运行完成声明。"
        "精确字段与类型见请求 repository_root 下 schemas/xk-natural-contract-output.schema.json。"
        "在当前私有工作目录写完整 semantic-output.json，内容是单个合同对象；回读后，"
        "最后消息只写 SEMANTIC_OUTPUT_READY。不得用最后消息、摘要或另一个文件替代。"
        "源仓库位于工作目录之外，只能读取。运行时将在本步骤结束后验证并冻结合同，"
        "再启动完整阅读与分析作者；本步骤不形成任何读源证明。\n\n"
        "运行时请求（只读）：\n" + canonical_dumps(dict(request)) + "\n"
    ).encode("utf-8")


def parse_contract_authoring_output(raw: bytes, *, natural_request: Mapping[str, Any],
                                   repository_root: Path) -> dict[str, Any]:
    try:
        value = read_json_text(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as error:
        raise ValueError("contract author output is not strict UTF-8 JSON") from error
    validator = _schema_validator(OUTPUT_SCHEMA, str(repository_root))
    errors = sorted(validator.iter_errors(value), key=lambda error: str(list(error.absolute_path)))
    if errors:
        raise ValueError("contract author output fails schema validation: " + errors[0].message)
    return freeze_natural_problem_contract(value, request=natural_request, mode=str(natural_request["mode"]))


def contract_authoring_evidence(*, run_id: str, provider: Mapping[str, Any], command: list[str],
                               request_bytes: bytes, prompt_bytes: bytes, output_bytes: bytes,
                               events_bytes: bytes, stderr_bytes: bytes,
                               parent_pid: int, child_pid: int, started_at: str, completed_at: str,
                               frozen_problem_contract: Mapping[str, Any]) -> dict[str, Any]:
    thread_id, _ = parse_provider_events(events_bytes)
    receipt = {
        "schema_id": "xi-kari.v3.natural-contract-execution", "schema_version": 1,
        "protocol": PROTOCOL, "run_id": run_id,
        "provider_binding_sha256": sha256_json(dict(provider)),
        "command_sha256": sha256_json(command), "parent_pid": parent_pid,
        "child_pid": child_pid, "exit_status": 0, "thread_id": thread_id,
        "started_at": started_at, "completed_at": completed_at,
        "problem_contract_sha256": contract_hash(frozen_problem_contract),
    }
    for name, raw in (("request", request_bytes), ("prompt", prompt_bytes), ("output", output_bytes),
                      ("events", events_bytes), ("stderr", stderr_bytes)):
        receipt[f"{name}_sha256"] = sha256_bytes(raw)
        receipt[f"{name}_byte_count"] = len(raw)
    receipt["receipt_sha256"] = sha256_json(receipt)
    return {
        "receipt": receipt, "provider_binding": dict(provider), "command": list(command),
        "request_text": request_bytes.decode("utf-8"), "prompt_text": prompt_bytes.decode("utf-8"),
        "output_text": output_bytes.decode("utf-8"), "event_stream_text": events_bytes.decode("utf-8"),
        "stderr_base64": base64.b64encode(stderr_bytes).decode("ascii"),
    }


def validate_contract_authoring_evidence(evidence: Any, *, run_id: str,
                                         natural_request: Mapping[str, Any],
                                         frozen_problem_contract: Mapping[str, Any],
                                         repository_root: Path,
                                         base_started_at: str | None = None) -> None:
    if not isinstance(evidence, Mapping) or set(evidence) != EVIDENCE_FIELDS:
        raise ValueError("natural contract authoring evidence fields are not exact")
    provider = evidence["provider_binding"]
    require_base_authoring_provider(provider, mode="closed-input", verify_executable=False)
    if provider.get("repository_root") != str(repository_root):
        raise ValueError("contract author provider repository differs")
    try:
        request_bytes = evidence["request_text"].encode("utf-8")
        prompt_bytes = evidence["prompt_text"].encode("utf-8")
        output_bytes = evidence["output_text"].encode("utf-8")
        events_bytes = evidence["event_stream_text"].encode("utf-8")
        stderr_bytes = base64.b64decode(evidence["stderr_base64"], validate=True)
        request = read_json_text(evidence["request_text"])
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError("contract author evidence contains invalid raw bytes") from error
    draft = draft_problem_contract_from_natural_request(natural_request["text"],
        mode=str(natural_request["mode"]), evidence_cutoff=str(natural_request["evidence_cutoff"]))
    expected_request = contract_authoring_request(run_id=run_id, natural_request=natural_request,
        draft_problem_contract=draft, repository_root=repository_root, provider=provider)
    if request != expected_request or request_bytes != canonical_bytes(expected_request) + b"\n":
        raise ValueError("contract author request differs from the original natural request")
    if prompt_bytes != contract_authoring_prompt(expected_request):
        raise ValueError("contract author prompt differs from its request")
    parsed = parse_contract_authoring_output(output_bytes, natural_request=natural_request, repository_root=repository_root)
    if parsed != dict(frozen_problem_contract):
        raise ValueError("contract author output differs from the final frozen problem contract")
    receipt = evidence.get("receipt")
    if not isinstance(receipt, Mapping):
        raise ValueError("contract author receipt is not an object")
    for field in ("parent_pid", "child_pid"):
        value = receipt.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError("contract author receipt has an invalid " + field)
    if receipt["child_pid"] == receipt["parent_pid"]:
        raise ValueError("contract author requires a separate observed process")
    started = parse_instant(receipt.get("started_at"), field="contract author start")
    completed = parse_instant(receipt.get("completed_at"), field="contract author completion")
    if completed < started or (base_started_at is not None and completed > parse_instant(base_started_at)):
        raise ValueError("contract author did not complete before the base author")
    command = evidence.get("command")
    if not isinstance(command, list) or any(not isinstance(value, str) for value in command):
        raise ValueError("contract author command is invalid")
    if len(command) < 5 or not Path(command[-2]).is_absolute() or Path(command[-2]).name != "completion-notice.txt":
        raise ValueError("contract author completion path is not runtime-owned")
    from .execution import _provider_launch_argv
    expected_command = _provider_launch_argv(provider, [*provider["argv"], "--json", "--output-last-message", command[-2], "-"])
    if command != expected_command:
        raise ValueError("contract author command differs from its provider binding")
    expected = contract_authoring_evidence(run_id=run_id, provider=provider, command=command,
        request_bytes=request_bytes, prompt_bytes=prompt_bytes, output_bytes=output_bytes,
        events_bytes=events_bytes, stderr_bytes=stderr_bytes, parent_pid=receipt["parent_pid"],
        child_pid=receipt["child_pid"], started_at=receipt["started_at"], completed_at=receipt["completed_at"],
        frozen_problem_contract=parsed)
    if dict(receipt) != expected["receipt"]:
        raise ValueError("contract author receipt differs from captured execution bytes")


def validate_contract_authoring_binding(*, base_request: Mapping[str, Any],
                                         base_receipt: Mapping[str, Any],
                                         run_contract: Mapping[str, Any],
                                         repository_root: Path) -> None:
    """Replay the intake evidence as part of the existing execute-owned base receipt."""

    natural = run_contract.get("natural_request")
    binding = base_request.get("contract_authoring_binding")
    evidence = base_receipt.get("contract_authoring_evidence")
    original_natural = natural is not None and run_contract.get("continuation", {}).get("kind", "original") == "original"
    if binding is None and evidence is None and not original_natural:
        return
    if not isinstance(natural, Mapping) or not isinstance(binding, Mapping) or not isinstance(evidence, Mapping):
        raise ValueError("natural request requires its separate contract authoring evidence")
    frozen = run_contract["problem_contract"]
    validate_contract_authoring_evidence(evidence, run_id=str(run_contract["run_id"]),
        natural_request=natural, frozen_problem_contract=frozen, repository_root=repository_root,
        base_started_at=base_receipt.get("started_at"))
    if base_receipt.get("parent_pid") is not None and evidence["receipt"]["parent_pid"] != base_receipt["parent_pid"]:
        raise ValueError("contract author and base author have different runtime parents")
    expected_binding = {"receipt_sha256": evidence["receipt"]["receipt_sha256"],
                        "problem_contract_sha256": contract_hash(frozen)}
    if dict(binding) != expected_binding or base_request.get("problem_contract") != dict(frozen):
        raise ValueError("base author request is not bound to the final contract authoring receipt")
