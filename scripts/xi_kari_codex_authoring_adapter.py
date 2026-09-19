#!/usr/bin/env python3
"""Production Codex provider for runtime-owned semantic authoring requests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any

sys.dont_write_bytecode = True

from jsonschema import Draft202012Validator, FormatChecker

from xi_kari_runtime.canonical_json import (
    canonical_bytes,
    canonical_dumps,
    read_json_text,
    sha256_file,
    sha256_bytes,
    sha256_json,
)

from xi_kari_runtime.output_transport import (
    COMPLETION_NOTICE, SEMANTIC_OUTPUT_FILENAME, OUTPUT_TRANSPORT,
    parse_provider_events, read_semantic_output,
)


ADAPTER_PROTOCOL = "xi-kari.v3.codex-semantic-authoring-adapter/v1"
PROVIDER_PROTOCOL = "xi-kari.v3.codex-provider-binding/v1"
MODEL = os.environ.get("XI_KARI_PROVIDER_MODEL", "gpt-5.6-sol")
REASONING_EFFORT = os.environ.get("XI_KARI_REASONING_EFFORT", "")
PROVIDER_BASE_URL = os.environ.get("XI_KARI_PROVIDER_BASE_URL", "")
PROVIDER_WIRE_API = os.environ.get("XI_KARI_PROVIDER_WIRE_API", "responses")
PROVIDER_NAME = "xi_kari_local"
APPROVAL_POLICY = "never"
SANDBOX = "workspace-write"
WEB_SEARCH = "disabled"
MAX_REQUEST_BYTES = 256 * 1024
MAX_PROMPT_BYTES = MAX_REQUEST_BYTES + 16 * 1024
MAX_MODEL_OUTPUT_BYTES = 16 * 1024 * 1024
MAX_DIAGNOSTIC_BYTES = 1024 * 1024
MAX_SCHEMA_BYTES = 1024 * 1024
SCRIPT_PATH = Path(__file__).resolve(strict=True)
REPOSITORY_ROOT = SCRIPT_PATH.parent.parent
OUTPUT_SCHEMA = (
    REPOSITORY_ROOT / "schemas/xk-codex-semantic-authoring-output.schema.json"
)
SEMANTIC_FIELDS = (
    "deliverable_type",
    "reader_sections",
    "answer_delivery",
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
)
PROBLEM_FIELDS = (
    "question",
    "object_of_analysis",
    "boundary",
    "identity_criterion",
    "spatial_scale",
    "organizational_scale",
    "time_window",
    "evidence_cutoff",
    "retrieval_profile",
    "requested_stance",
    "problem_action",
    "advice_requested",
    "deliverable_type",
)
PROBLEM_STRING_FIELDS = tuple(
    field
    for field in PROBLEM_FIELDS
    if field not in {"problem_action", "advice_requested"}
)
PROBLEM_ACTIONS = {"explain", "compare", "infer", "choose", "express"}
DELIVERABLE_TYPES = {"analysis", "decision", "charter", "plan", "critique"}
PROVIDER_FIELDS = {
    "protocol",
    "repository_root",
    "executable_path",
    "executable_sha256",
    "argv",
    "argv_sha256",
    "model",
    "reasoning_effort",
    "approval_policy",
    "sandbox",
    "ephemeral",
    "ignore_user_config",
    "strict_config",
    "web_search",
    "timeout_seconds",
}
SEMANTIC_REQUEST_FIELDS = {
    "schema_id",
    "schema_version",
    "variant_kind",
    "generation_context_id",
    "mode",
    "requested_stance",
    "time_window",
    "problem_contract",
    "source_inputs",
}
SOURCE_INPUT_FIELDS = {
    "source_version",
    "validator_set_sha256",
    "repository_root",
    "reader_root",
    "source_manifest_path",
    "source_lock",
    "read_plan",
    "retrieval",
    "evidence",
    "concept_authority",
    "facts",
}
CONCEPT_AUTHORITY_FIELDS = {
    "schema_id",
    "schema_version",
    "source_candidate_count",
    "source_candidate_index_sha256",
    "candidate_census_sha256",
    "concept_disposition_ledger_sha256",
    "ontology_concept_count",
    "concept_registry_sha256",
    "concept_relations_sha256",
}
CONCEPT_AUTHORITY_HASH_FIELDS = CONCEPT_AUTHORITY_FIELDS - {
    "schema_id",
    "schema_version",
    "source_candidate_count",
    "ontology_concept_count",
}
VARIANT_STANCES = {
    "stance-support": "support",
    "stance-oppose": "oppose",
    "time-window-shift": "support",
}
MODEL_AUTHORITY_FIELDS = {
    "adapter_argv_sha256",
    "adapter_binding",
    "adapter_binding_sha256",
    "adapter_executable_sha256",
    "argv_sha256",
    "child_pid",
    "completion",
    "completion_record",
    "exit_status",
    "executable_sha256",
    "input_sha256",
    "official_validation",
    "parent_pid",
    "phase_record",
    "phase_records",
    "provider_binding",
    "run_id",
    "runtime_binding",
    "runtime_receipt",
    "runtime_receipt_sha256",
    "semantic_probe_authorings",
    "semantic_packet_sha256",
    "stderr_sha256",
    "stdout_sha256",
    "terminal_record",
    "validator_receipt",
}


class AdapterError(ValueError):
    """Raised when the production provider cannot author a trusted payload."""


def _require_mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AdapterError(f"{field} must be one JSON object")
    return value


def _ordinary_path(path: str, *, kind: str, executable: bool = False) -> Path:
    if not isinstance(path, str) or not path or "\x00" in path:
        raise AdapterError(f"{kind} path is invalid")
    candidate = Path(path)
    if not candidate.is_absolute() or os.path.normpath(path) != path:
        raise AdapterError(f"{kind} path must be canonical and absolute")
    current = Path(candidate.anchor)
    for part in candidate.parts[1:]:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise AdapterError(f"{kind} path is unavailable: {current}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise AdapterError(f"{kind} path contains a symlink: {current}")
    try:
        resolved = candidate.resolve(strict=True)
        metadata = resolved.stat(follow_symlinks=False)
    except OSError as exc:
        raise AdapterError(f"{kind} path is unavailable: {candidate}") from exc
    if executable:
        if not stat.S_ISREG(metadata.st_mode) or not os.access(resolved, os.X_OK):
            raise AdapterError(f"{kind} must be an executable regular file")
    elif not stat.S_ISDIR(metadata.st_mode):
        raise AdapterError(f"{kind} must be a directory")
    if str(resolved) != path:
        raise AdapterError(f"{kind} path must be canonical and absolute")
    return resolved


def _expected_argv(executable: Path) -> list[str]:
    argv = [
        str(executable),
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--model",
        MODEL,
    ]
    if REASONING_EFFORT:
        argv += ["--config", f'model_reasoning_effort="{REASONING_EFFORT}"']
    if PROVIDER_BASE_URL:
        argv += [
            "--config",
            f'model_provider="{PROVIDER_NAME}"',
            "--config",
            f'model_providers.{PROVIDER_NAME}.name="{PROVIDER_NAME}"',
            "--config",
            f'model_providers.{PROVIDER_NAME}.base_url="{PROVIDER_BASE_URL}"',
            "--config",
            f'model_providers.{PROVIDER_NAME}.wire_api="{PROVIDER_WIRE_API}"',
        ]
    argv += [
        "--config",
        f'web_search="{WEB_SEARCH}"',
        "--config",
        f'approval_policy="{APPROVAL_POLICY}"',
        "--config",
        "sandbox_workspace_write.exclude_tmpdir_env_var=true",
        "--config",
        "sandbox_workspace_write.exclude_slash_tmp=true",
        "--config",
        "sandbox_workspace_write.writable_roots=[]",
        "--sandbox",
        SANDBOX,
        "--skip-git-repo-check",
        "--color",
        "never",
    ]
    if os.name == "nt":
        argv += ["--config", 'windows.sandbox="elevated"']
    return argv


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


def _provider_launch_argv(command: Sequence[str], executable: Path) -> list[str]:
    """Build the host argv without changing the bound provider identity."""

    argv = list(command)
    if not argv or argv[0] != str(executable):
        raise AdapterError("Codex launch command differs from provider binding")
    if os.name != "nt":
        return argv
    interpreter = _ordinary_path(
        str(Path(sys.executable).resolve(strict=True)),
        kind="Python interpreter",
        executable=True,
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


def _validate_provider_binding(value: Any) -> tuple[Mapping[str, Any], Path, Path]:
    binding = _require_mapping(value, field="provider_binding")
    if set(binding) != PROVIDER_FIELDS:
        raise AdapterError("provider_binding fields are not exact")
    if (
        binding.get("protocol") != PROVIDER_PROTOCOL
        or binding.get("model") != MODEL
        or binding.get("reasoning_effort") != REASONING_EFFORT
        or binding.get("approval_policy") != APPROVAL_POLICY
        or binding.get("sandbox") != SANDBOX
        or binding.get("ephemeral") is not True
        or binding.get("ignore_user_config") is not True
        or not isinstance(binding.get("strict_config"), bool)
        or binding.get("web_search") != WEB_SEARCH
    ):
        raise AdapterError("provider_binding violates the fixed Codex policy")
    timeout_seconds = binding.get("timeout_seconds")
    if (
        not isinstance(timeout_seconds, int)
        or isinstance(timeout_seconds, bool)
        or not 1 <= timeout_seconds <= 7200
    ):
        raise AdapterError("provider_binding timeout_seconds must be 1-7200")
    repository_root = _ordinary_path(
        binding.get("repository_root"), kind="repository_root"
    )
    if repository_root != REPOSITORY_ROOT:
        raise AdapterError("provider_binding repository_root is not this Skill root")
    executable = _ordinary_path(
        binding.get("executable_path"), kind="Codex executable", executable=True
    )
    executable_sha256 = binding.get("executable_sha256")
    if (
        not isinstance(executable_sha256, str)
        or len(executable_sha256) != 64
        or sha256_file(executable) != executable_sha256
    ):
        raise AdapterError("Codex executable SHA-256 drifted")
    expected_argv = _expected_argv(executable)
    argv = binding.get("argv")
    if argv != expected_argv or binding.get("argv_sha256") != sha256_json(
        expected_argv
    ):
        raise AdapterError("provider_binding Codex argv drifted")
    return binding, repository_root, executable


def _validate_semantic_request(
    value: Any, *, repository_root: Path
) -> Mapping[str, Any]:
    request = _require_mapping(value, field="semantic_request")
    if set(request) != SEMANTIC_REQUEST_FIELDS:
        raise AdapterError("semantic_request fields are not exact")
    variant_kind = request.get("variant_kind")
    requested_stance = request.get("requested_stance")
    problem = _require_mapping(
        request.get("problem_contract"), field="semantic_request.problem_contract"
    )
    if (
        request.get("schema_id") != "xi-kari.v3.semantic-authoring-request"
        or request.get("schema_version") != 1
        or variant_kind not in VARIANT_STANCES
        or requested_stance != VARIANT_STANCES.get(variant_kind)
        or request.get("mode") not in {"open-world", "closed-input"}
        or not isinstance(request.get("generation_context_id"), str)
        or not request["generation_context_id"]
        or set(problem) != set(PROBLEM_FIELDS)
        or problem.get("requested_stance") != requested_stance
        or problem.get("time_window") != request.get("time_window")
    ):
        raise AdapterError("semantic_request variant contract is invalid")
    if any(
        not isinstance(problem.get(field), str) or not problem[field]
        for field in PROBLEM_STRING_FIELDS
    ):
        raise AdapterError("semantic_request problem fields must be non-empty strings")
    if (
        not isinstance(problem.get("problem_action"), str)
        or problem["problem_action"] not in PROBLEM_ACTIONS
    ):
        raise AdapterError("semantic_request problem_action is invalid")
    if not isinstance(problem.get("advice_requested"), bool):
        raise AdapterError(
            "semantic_request advice_requested must be a boolean"
        )
    if problem.get("deliverable_type") not in DELIVERABLE_TYPES:
        raise AdapterError("semantic_request deliverable_type is invalid")
    if variant_kind == "time-window-shift" and request.get("time_window") != (
        "sensitivity-shifted-window"
    ):
        raise AdapterError("semantic_request shifted window is invalid")
    source_inputs = _require_mapping(
        request.get("source_inputs"), field="semantic_request.source_inputs"
    )
    if set(source_inputs) != SOURCE_INPUT_FIELDS:
        raise AdapterError("semantic_request source_inputs fields are not exact")
    concept_authority = _require_mapping(
        source_inputs.get("concept_authority"),
        field="semantic_request.source_inputs.concept_authority",
    )
    if (
        set(concept_authority) != CONCEPT_AUTHORITY_FIELDS
        or concept_authority.get("schema_id")
        != "xi-kari.v3.concept-authority-binding"
        or concept_authority.get("schema_version") != 1
        or any(
            not isinstance(concept_authority.get(field), int)
            or isinstance(concept_authority[field], bool)
            or concept_authority[field] < 1
            for field in ("source_candidate_count", "ontology_concept_count")
        )
        or any(
            not isinstance(concept_authority.get(field), str)
            or len(concept_authority[field]) != 64
            or any(
                character not in "0123456789abcdef"
                for character in concept_authority[field]
            )
            for field in CONCEPT_AUTHORITY_HASH_FIELDS
        )
    ):
        raise AdapterError("semantic_request concept_authority is invalid")
    expected_reader_root = repository_root / "references/source/v8.3/reader"
    expected_manifest = (
        repository_root / "references/source/v8.3/source-manifest.json"
    )
    if (
        source_inputs.get("source_version") != "v8.3"
        or source_inputs.get("repository_root") != str(repository_root)
        or source_inputs.get("reader_root") != str(expected_reader_root)
        or source_inputs.get("source_manifest_path") != str(expected_manifest)
        or not expected_reader_root.is_dir()
        or not expected_manifest.is_file()
        or not isinstance(source_inputs.get("source_lock"), Mapping)
        or not isinstance(source_inputs.get("read_plan"), Mapping)
        or not isinstance(source_inputs.get("retrieval"), Mapping)
        or not isinstance(source_inputs.get("evidence"), Mapping)
        or not isinstance(source_inputs.get("facts"), Mapping)
    ):
        raise AdapterError("semantic_request source binding is invalid")
    return request


def _load_request() -> tuple[Mapping[str, Any], Mapping[str, Any], Path, Path]:
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    if len(raw) >= MAX_REQUEST_BYTES:
        raise AdapterError(
            f"stdin must be smaller than {MAX_REQUEST_BYTES} bytes"
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AdapterError("stdin is not UTF-8") from exc
    try:
        value = read_json_text(text)
    except Exception as exc:
        raise AdapterError("stdin is not strict JSON") from exc
    request = _require_mapping(value, field="stdin")
    if raw != canonical_bytes(request):
        raise AdapterError("stdin is not canonical JSON")
    if set(request) != {"protocol", "provider_binding", "semantic_request"}:
        raise AdapterError("adapter request fields are not exact")
    if request.get("protocol") != ADAPTER_PROTOCOL:
        raise AdapterError("adapter request protocol is invalid")
    binding, repository_root, executable = _validate_provider_binding(
        request.get("provider_binding")
    )
    semantic_request = _validate_semantic_request(
        request.get("semantic_request"), repository_root=repository_root
    )
    return binding, semantic_request, repository_root, executable


def _read_regular_file(path: Path, *, limit: int, label: str) -> bytes:
    try:
        before = path.lstat()
    except OSError as exc:
        raise AdapterError(f"{label} is unavailable") from exc
    if not stat.S_ISREG(before.st_mode):
        raise AdapterError(f"{label} must be a regular file")
    if before.st_size > limit:
        raise AdapterError(f"{label} exceeds {limit} bytes")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(
        os, "O_CLOEXEC", 0
    )
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise AdapterError(f"{label} is not readable without following links") from exc
    with os.fdopen(descriptor, "rb") as handle:
        opened = os.fstat(handle.fileno())
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)
        ):
            raise AdapterError(f"{label} changed while opening")
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise AdapterError(f"{label} exceeds {limit} bytes")
    return raw


def _load_output_schema() -> tuple[dict[str, Any], str]:
    raw = _read_regular_file(
        OUTPUT_SCHEMA, limit=MAX_SCHEMA_BYTES, label="Codex output schema"
    )
    try:
        value = read_json_text(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise AdapterError("Codex output schema is not strict UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise AdapterError("Codex output schema is not one JSON object")
    try:
        Draft202012Validator.check_schema(value)
    except Exception as exc:
        raise AdapterError("Codex output schema is invalid") from exc
    return value, sha256_file(OUTPUT_SCHEMA)


def _build_prompt(semantic_request: Mapping[str, Any]) -> bytes:
    prompt = (
        "$xi-kari-skill\n"
        "本次唯一Skill目录是semantic_request.source_inputs.repository_root；"
        "从该目录读取SKILL.md，不得改用全局安装或其他目录中的同名Skill。"
        "显式调用并严格遵循 Xi-Kari Skill。下面是运行时拥有且已冻结的语义稳定性变体请求。"
        "只进行该请求要求的独立语义创作；完整读取其绑定的 v8.3 source 与 reader 输入。"
        "原文有作者自定义概念，同名不得以常识或其他理论替换；核对定义、适用条件、排除项及源锚点后再判断。"
        "沿用冻结问题的 deliverable_type，给出中心判断、局部裁决、依据、竞争解释、反方和行动取舍。"
        "reader_sections 必须保存全部已开展的实质论证，不能按重要性删去次要解释、失败路径、成本、条件或停止理由。"
        "每节提供 section_id、heading、local_judgment、paragraphs、source_bindings。"
        "source_bindings 的 source_path 绑定本变体语义字段；paragraph_index 为 0 时指局部判断，为 1..N 时指正文段落；"
        "excerpt 必须是对应段落的真实摘录并承载该字段的实质含义，不得用链接、编号或标记代替。"
        "answer_delivery 可缺或为 null；只有用户明确要求简答才声明相应交付方式，变体仍保留完整 reader_sections。"
        "不得自报运行状态、进程、回执、阶段、签名或完成权威。"
        "把符合源仓库 schemas/xk-codex-semantic-authoring-output.schema.json 的完整 JSON 写入当前私有工作目录的 semantic-output.json。"
        "可分批生成并在磁盘合并完整内容；源仓库位于工作目录之外，仅允许读取。"
        "完成后回读该文件，最后消息只写 SEMANTIC_OUTPUT_READY，不得输出 JSON 或文件路径。\n\n"
        "semantic_request（canonical JSON）：\n"
        f"{canonical_dumps(semantic_request)}\n"
    ).encode("utf-8")
    if len(prompt) > MAX_PROMPT_BYTES:
        raise AdapterError(f"Codex prompt exceeds {MAX_PROMPT_BYTES} bytes")
    return prompt


def _kill_process_tree(process: subprocess.Popen[bytes]) -> None:
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif os.name == "nt":  # pragma: no cover - Windows host path
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


def _watch_process_group(
    read_descriptor: int, process_group_id: int, workspace: Path
) -> None:
    try:
        os.setsid()
        marker = os.read(read_descriptor, 1)
        if marker != b"D":
            try:
                os.killpg(process_group_id, signal.SIGKILL)
            except ProcessLookupError:
                pass
            shutil.rmtree(workspace, ignore_errors=True)
    finally:
        try:
            os.close(read_descriptor)
        except OSError:
            pass
        os._exit(0)


def _start_watchdog(
    process_group_id: int, workspace: Path
) -> tuple[int, int] | None:
    if os.name != "posix" or not hasattr(os, "fork"):
        return None
    read_descriptor, write_descriptor = os.pipe()
    watchdog_pid = os.fork()
    if watchdog_pid == 0:  # pragma: no cover - exercised through parent death
        os.close(write_descriptor)
        _watch_process_group(read_descriptor, process_group_id, workspace)
    os.close(read_descriptor)
    return watchdog_pid, write_descriptor


def _disarm_watchdog(watchdog: tuple[int, int] | None) -> None:
    if watchdog is None:
        return
    watchdog_pid, write_descriptor = watchdog
    try:
        os.write(write_descriptor, b"D")
    except (BrokenPipeError, OSError):
        pass
    finally:
        try:
            os.close(write_descriptor)
        except OSError:
            pass
    while True:
        try:
            os.waitpid(watchdog_pid, 0)
        except InterruptedError:
            continue
        except ChildProcessError:
            pass
        break


def _file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _diagnostic_excerpt(path: Path) -> str:
    try:
        raw = _read_regular_file(
            path, limit=MAX_DIAGNOSTIC_BYTES, label="Codex diagnostic output"
        )[:8192]
    except AdapterError:
        return ""
    return raw.decode("utf-8", errors="replace").strip()


def _run_codex(
    binding: Mapping[str, Any],
    semantic_request: Mapping[str, Any],
    *,
    repository_root: Path,
    executable: Path,
    output_schema_sha256: str,
) -> tuple[bytes, dict[str, Any]]:
    prompt = _build_prompt(semantic_request)
    environment = os.environ.copy()
    environment.update({"NO_COLOR": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    with tempfile.TemporaryDirectory(
        prefix="xi-kari-codex-authoring-"
    ) as temporary:
        capture_root = Path(temporary)
        workspace = capture_root / "author-workspace"
        workspace.mkdir()
        output_path = workspace / SEMANTIC_OUTPUT_FILENAME
        notice_path = capture_root / "completion-notice.txt"
        prompt_path = capture_root / "prompt.txt"
        stdout_path = capture_root / "codex.stdout.jsonl"
        stderr_path = capture_root / "codex.stderr"
        prompt_path.write_bytes(prompt)
        command = [
            *binding["argv"],
            "--json",
            "--output-last-message",
            str(notice_path),
            "-",
        ]
        with (
            prompt_path.open("rb") as prompt_handle,
            stdout_path.open("wb") as stdout_handle,
            stderr_path.open("wb") as stderr_handle,
        ):
            process = subprocess.Popen(
                _provider_launch_argv(command, executable),
                cwd=workspace,
                env=environment,
                stdin=prompt_handle,
                stdout=stdout_handle,
                stderr=stderr_handle,
                text=False,
                shell=False,
                start_new_session=(os.name == "posix"),
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP
                    if os.name == "nt"
                    else 0
                ),
            )
            watchdog = _start_watchdog(process.pid, capture_root)
            deadline = time.monotonic() + int(binding["timeout_seconds"])
            terminal_error: AdapterError | None = None
            try:
                while process.poll() is None:
                    if _file_size(output_path) > MAX_MODEL_OUTPUT_BYTES:
                        terminal_error = AdapterError(
                            "Codex semantic output file exceeds the size limit"
                        )
                        break
                    if (
                        _file_size(stdout_path) > MAX_MODEL_OUTPUT_BYTES
                        or _file_size(stderr_path) > MAX_DIAGNOSTIC_BYTES
                    ):
                        terminal_error = AdapterError(
                            "Codex diagnostic output exceeds the size limit"
                        )
                        break
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        terminal_error = AdapterError("Codex authoring timed out")
                        break
                    time.sleep(min(0.05, remaining))
            finally:
                try:
                    _kill_process_tree(process)
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        _kill_process_tree(process)
                        process.wait(timeout=2)
                finally:
                    _disarm_watchdog(watchdog)
            if terminal_error is None and (
                _file_size(stdout_path) > MAX_MODEL_OUTPUT_BYTES
                or _file_size(stderr_path) > MAX_DIAGNOSTIC_BYTES
            ):
                terminal_error = AdapterError(
                    "Codex diagnostic output exceeds the size limit"
                )
            if terminal_error is not None:
                raise terminal_error
        executable_after = _ordinary_path(
            str(executable), kind="Codex executable", executable=True
        )
        if (
            executable_after != executable
            or sha256_file(executable_after) != binding["executable_sha256"]
            or binding["argv"] != _expected_argv(executable_after)
            or binding["argv_sha256"] != sha256_json(binding["argv"])
        ):
            raise AdapterError("Codex provider binding drifted during execution")
        if sha256_file(OUTPUT_SCHEMA) != output_schema_sha256:
            raise AdapterError("Codex output schema drifted during execution")
        if process.returncode != 0:
            diagnostic = _diagnostic_excerpt(stderr_path)
            suffix = f": {diagnostic}" if diagnostic else ""
            raise AdapterError(f"Codex exec exited with status {process.returncode}{suffix}")
        try:
            notice = _read_regular_file(notice_path, limit=4096, label="completion notice")
            raw = read_semantic_output(workspace, notice=notice, limit=MAX_MODEL_OUTPUT_BYTES)
            events = _read_regular_file(stdout_path, limit=MAX_MODEL_OUTPUT_BYTES, label="provider events")
            thread_id, _ = parse_provider_events(events)
        except ValueError as error:
            raise AdapterError(str(error)) from error
        execution = {
            "protocol": OUTPUT_TRANSPORT,
            "provider_parent_pid": os.getpid(), "provider_child_pid": process.pid,
            "exit_status": process.returncode, "thread_id": thread_id,
            "events": events.decode("utf-8"), "events_sha256": sha256_bytes(events),
            "semantic_file_content": raw.decode("utf-8"),
            "semantic_file_sha256": sha256_bytes(raw), "semantic_file_byte_count": len(raw),
        }
        return raw, execution


def _find_model_authority(value: Any, *, pointer: str = "$") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in MODEL_AUTHORITY_FIELDS:
                return f"{pointer}/{key}"
            found = _find_model_authority(child, pointer=f"{pointer}/{key}")
            if found is not None:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = _find_model_authority(child, pointer=f"{pointer}/{index}")
            if found is not None:
                return found
    return None


def _validate_model_output(
    raw: bytes,
    *,
    schema: Mapping[str, Any],
    semantic_request: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AdapterError("Codex last message is not UTF-8") from exc
    try:
        value = read_json_text(text)
    except Exception as exc:
        raise AdapterError("Codex last message is not strict JSON") from exc
    required_fields = set(SEMANTIC_FIELDS) - {"answer_delivery"}
    if not isinstance(value, dict) or not required_fields.issubset(value) or not set(value).issubset(SEMANTIC_FIELDS):
        raise AdapterError("Codex output is not semantic-only")
    value = dict(value)
    value.setdefault("answer_delivery", None)
    errors = sorted(
        Draft202012Validator(
            dict(schema), format_checker=FormatChecker()
        ).iter_errors(value),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "$"
        raise AdapterError(
            f"Codex output does not satisfy the output schema at {location}"
        )
    authority_pointer = _find_model_authority(value)
    if authority_pointer is not None:
        raise AdapterError(
            f"Codex output contains model-authored authority at {authority_pointer}"
        )
    authored_problem = value["problem_contract"]
    requested_problem = semantic_request["problem_contract"]
    if value.get("deliverable_type") != requested_problem.get("deliverable_type"):
        raise AdapterError("Codex output deliverable_type differs from the requested variant")
    if any(
        authored_problem.get(field) != requested_problem.get(field)
        for field in PROBLEM_FIELDS
    ):
        raise AdapterError("Codex output differs from the requested variant")
    if (
        authored_problem.get("dynamic_applicability")
        != value["dynamic_applicability"]
    ):
        raise AdapterError("Codex output has inconsistent dynamic applicability")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    try:
        if argv:
            raise AdapterError("the adapter accepts no command-line arguments")
        schema, schema_sha256 = _load_output_schema()
        binding, semantic_request, repository_root, executable = _load_request()
        raw_output, provider_execution = _run_codex(
            binding,
            semantic_request,
            repository_root=repository_root,
            executable=executable,
            output_schema_sha256=schema_sha256,
        )
        payload = _validate_model_output(
            raw_output, schema=schema, semantic_request=semantic_request
        )
        sys.stdout.buffer.write(canonical_bytes({
            "protocol": OUTPUT_TRANSPORT,
            "semantic_packet": payload,
            "provider_execution": provider_execution,
        }))
        sys.stdout.buffer.flush()
        return 0
    except AdapterError as exc:
        sys.stderr.write(f"xi-kari Codex authoring adapter: {exc}\n")
        return 1
    except KeyboardInterrupt:
        sys.stderr.write("xi-kari Codex authoring adapter: interrupted\n")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
