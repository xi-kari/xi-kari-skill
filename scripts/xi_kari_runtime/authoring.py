"""Runtime-owned subprocess authoring for semantic stability variants."""

from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import threading
import time
from typing import Any, Mapping
import uuid

from .canonical_json import (
    canonical_bytes,
    read_json_text,
    sha256_bytes,
    sha256_file,
    sha256_json,
)
from .concept_authority import load_concept_authority
from .problem_contract import (
    FROZEN_FIELDS,
    contract_hash,
    stance_neutrality_key,
    validate_problem_contract,
)
from .output_transport import OUTPUT_TRANSPORT, parse_provider_events


FORMAL_ADAPTER_PROTOCOL = "xi-kari.v3.semantic-authoring-adapter/v3"
FORMAL_ADAPTER_PROFILE = "production-codex"
CODEX_ADAPTER_PROTOCOL = "xi-kari.v3.codex-semantic-authoring-adapter/v1"
CODEX_PROVIDER_PROTOCOL = "xi-kari.v3.codex-provider-binding/v1"
CODEX_MODEL = os.environ.get("XI_KARI_PROVIDER_MODEL", "gpt-5.6-sol")
CODEX_REASONING_EFFORT = os.environ.get("XI_KARI_REASONING_EFFORT", "")
CODEX_PROVIDER_BASE_URL = os.environ.get("XI_KARI_PROVIDER_BASE_URL", "")
CODEX_PROVIDER_WIRE_API = os.environ.get("XI_KARI_PROVIDER_WIRE_API", "responses")
CODEX_PROVIDER_NAME = "xi_kari_local"
CODEX_APPROVAL_POLICY = "never"
CODEX_SANDBOX = "workspace-write"
CODEX_WEB_SEARCH = "disabled"
BASE_OPEN_WORLD_WEB_SEARCH = "live"
BASE_CLOSED_INPUT_WEB_SEARCH = "disabled"
FORMAL_ADAPTER_RELATIVE_PATH = Path("scripts/xi_kari_codex_authoring_adapter.py")
FORMAL_RECEIPT_PROTOCOL = "xi-kari.v3.semantic-authoring-receipt/v3"
DEFAULT_ADAPTER_TIMEOUT_SECONDS = 1200
MAX_AUTHORING_TIMEOUT_SECONDS = 7200
MAX_ADAPTER_STDIN_BYTES = 256 * 1024
MAX_ADAPTER_STDOUT_BYTES = 64 * 1024 * 1024
MAX_ADAPTER_STDERR_BYTES = 1024 * 1024
SEMANTIC_AUTHORING_FIELDS = (
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
AUTHORING_VARIANTS = {
    "stance-support": ("support", None),
    "stance-oppose": ("oppose", None),
    "time-window-shift": ("support", "sensitivity-shifted-window"),
}
ADAPTER_BASE_BINDING_FIELDS = {
    "protocol",
    "argv",
    "argv_sha256",
    "executable_path",
    "executable_sha256",
    "timeout_seconds",
}
FORMAL_ADAPTER_BINDING_FIELDS = ADAPTER_BASE_BINDING_FIELDS | {
    "profile",
    "provider_binding",
    "provider_binding_sha256",
}
PROVIDER_BINDING_FIELDS = {
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
RECEIPT_BASE_FIELDS = {
    "protocol",
    "adapter_executable_sha256",
    "adapter_argv_sha256",
    "variant_kind",
    "requested_stance",
    "time_window",
    "generation_context_id",
    "input_sha256",
    "input_byte_count",
    "stdout_sha256",
    "stdout_byte_count",
    "stderr_sha256",
    "child_pid",
    "parent_pid",
    "exit_status",
    "semantic_packet_sha256",
}
FORMAL_RUNTIME_RECEIPT_FIELDS = RECEIPT_BASE_FIELDS | {
    "semantic_request_sha256",
    "semantic_request_byte_count",
    "outer_input_sha256",
    "outer_input_byte_count",
    "provider_binding_sha256",
    "provider_executable_sha256",
    "provider_argv_sha256",
    "provider_execution",
}
PROVIDER_EXECUTION_FIELDS = {
    "protocol", "provider_parent_pid", "provider_child_pid", "exit_status",
    "thread_id", "events", "events_sha256", "semantic_file_content",
    "semantic_file_sha256", "semantic_file_byte_count",
}


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _ordinary_executable(path: Path, *, label: str = "semantic authoring adapter") -> Path:
    candidate = path.expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    candidate = candidate.absolute()
    current = Path(candidate.anchor)
    for part in candidate.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise ValueError(
                f"{label} path contains a symlink: {current}"
            )
    try:
        metadata = candidate.stat(follow_symlinks=False)
    except OSError as exc:
        raise ValueError(
            f"{label} executable is unavailable: {candidate}"
        ) from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError(
            f"{label} is not a regular file: {candidate}"
        )
    if not os.access(candidate, os.X_OK):
        raise ValueError(
            f"{label} is not executable: {candidate}"
        )
    return candidate.resolve(strict=True)


def _codex_provider_argv(
    executable: Path, *, web_search: str = CODEX_WEB_SEARCH
) -> list[str]:
    if web_search not in {"live", "disabled"}:
        raise ValueError("Codex web-search policy is invalid")
    argv = [
        str(executable),
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--model",
        CODEX_MODEL,
    ]
    if CODEX_REASONING_EFFORT:
        argv += ["--config", f'model_reasoning_effort="{CODEX_REASONING_EFFORT}"']
    if CODEX_PROVIDER_BASE_URL:
        argv += [
            "--config",
            f'model_provider="{CODEX_PROVIDER_NAME}"',
            "--config",
            f'model_providers.{CODEX_PROVIDER_NAME}.name="{CODEX_PROVIDER_NAME}"',
            "--config",
            f'model_providers.{CODEX_PROVIDER_NAME}.base_url="{CODEX_PROVIDER_BASE_URL}"',
            "--config",
            f'model_providers.{CODEX_PROVIDER_NAME}.wire_api="{CODEX_PROVIDER_WIRE_API}"',
        ]
    argv += [
        "--config",
        f'web_search="{web_search}"',
        "--config",
        f'approval_policy="{CODEX_APPROVAL_POLICY}"',
        "--config",
        "sandbox_workspace_write.exclude_tmpdir_env_var=true",
        "--config",
        "sandbox_workspace_write.exclude_slash_tmp=true",
        "--config",
        "sandbox_workspace_write.writable_roots=[]",
        "--sandbox",
        CODEX_SANDBOX,
        "--skip-git-repo-check",
        "--color",
        "never",
    ]
    if os.name == "nt":
        argv += ["--config", 'windows.sandbox="elevated"']
    return argv


def _bind_codex_provider(
    executable_path: str | Path,
    *,
    repository_root: Path,
    timeout_seconds: int,
    web_search: str = CODEX_WEB_SEARCH,
) -> dict[str, Any]:
    if not isinstance(timeout_seconds, int) or isinstance(timeout_seconds, bool) or not 1 <= timeout_seconds <= MAX_AUTHORING_TIMEOUT_SECONDS:
        raise ValueError("provider timeout must be 1-7200 seconds")
    executable = _ordinary_executable(
        Path(str(executable_path)), label="Codex provider"
    )
    argv = _codex_provider_argv(executable, web_search=web_search)
    return {
        "protocol": CODEX_PROVIDER_PROTOCOL,
        "repository_root": str(repository_root),
        "executable_path": str(executable),
        "executable_sha256": sha256_file(executable),
        "argv": argv,
        "argv_sha256": sha256_json(argv),
        "model": CODEX_MODEL,
        "reasoning_effort": CODEX_REASONING_EFFORT,
        "approval_policy": CODEX_APPROVAL_POLICY,
        "sandbox": CODEX_SANDBOX,
        "ephemeral": True,
        "ignore_user_config": True,
        "strict_config": False,
        "web_search": web_search,
        "timeout_seconds": timeout_seconds,
    }


def bind_base_authoring_provider(
    executable_path: str | Path,
    *,
    mode: str,
    repository_root: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Bind the provider used for XK1 base authoring, by evidence mode.

    XK9 semantic variants intentionally use the formal adapter's disabled-web
    binding.  Base authoring has a separate policy: live retrieval is enabled
    only for open-world and is explicitly disabled for closed-input.
    """

    if mode not in {"open-world", "closed-input"}:
        raise ValueError("base authoring provider mode is invalid")
    if not isinstance(repository_root, Path):
        repository_root = Path(repository_root)
    return _bind_codex_provider(
        executable_path,
        repository_root=Path(repository_root).resolve(strict=True),
        timeout_seconds=timeout_seconds,
        web_search=(
            BASE_OPEN_WORLD_WEB_SEARCH
            if mode == "open-world"
            else BASE_CLOSED_INPUT_WEB_SEARCH
        ),
    )


def require_base_authoring_provider(
    binding: Any,
    *,
    mode: str,
    verify_executable: bool = True,
) -> Mapping[str, Any]:
    """Validate the mode-specific provider binding used by base authoring."""

    if mode not in {"open-world", "closed-input"}:
        raise ValueError("base authoring provider mode is invalid")
    if not isinstance(binding, Mapping) or set(binding) != PROVIDER_BINDING_FIELDS:
        raise ValueError("base authoring provider binding fields are not exact")
    expected_web = (
        BASE_OPEN_WORLD_WEB_SEARCH
        if mode == "open-world"
        else BASE_CLOSED_INPUT_WEB_SEARCH
    )
    path = binding.get("executable_path")
    argv = binding.get("argv")
    timeout = binding.get("timeout_seconds")
    repository = binding.get("repository_root")
    if (
        binding.get("protocol") != CODEX_PROVIDER_PROTOCOL
        or binding.get("model") != CODEX_MODEL
        or binding.get("reasoning_effort") != CODEX_REASONING_EFFORT
        or binding.get("approval_policy") != CODEX_APPROVAL_POLICY
        or binding.get("sandbox") != CODEX_SANDBOX
        or binding.get("ephemeral") is not True
        or binding.get("ignore_user_config") is not True
        or not isinstance(binding.get("strict_config"), bool)
        or binding.get("web_search") != expected_web
        or not isinstance(timeout, int)
        or isinstance(timeout, bool)
        or not 1 <= timeout <= MAX_AUTHORING_TIMEOUT_SECONDS
        or not isinstance(repository, str)
        or not Path(repository).is_absolute()
        or os.path.normpath(repository) != repository
        or not isinstance(path, str)
        or not Path(path).is_absolute()
        or os.path.normpath(path) != path
        or not isinstance(argv, list)
        or argv != _codex_provider_argv(Path(path), web_search=expected_web)
        or binding.get("argv_sha256") != sha256_json(argv)
        or not _is_sha256(binding.get("executable_sha256"))
    ):
        raise ValueError("base authoring provider binding is invalid")
    if verify_executable:
        executable = _ordinary_executable(Path(path), label="Codex provider")
        if str(executable) != path or sha256_file(executable) != binding.get(
            "executable_sha256"
        ):
            raise ValueError("base authoring provider executable drifted")
    return binding


def bind_semantic_authoring_adapter(
    executable_path: str | Path | None,
    *,
    timeout_seconds: int = DEFAULT_ADAPTER_TIMEOUT_SECONDS,
    profile: str = FORMAL_ADAPTER_PROFILE,
    codex_provider_executable: str | Path | None = None,
    repository_root: Path | None = None,
) -> dict[str, Any] | None:
    if profile != FORMAL_ADAPTER_PROFILE:
        raise ValueError("semantic authoring profile is invalid")
    if executable_path is None:
        raise ValueError("production Codex authoring requires the shipped adapter and provider executable")
    if not isinstance(executable_path, (str, Path)):
        raise ValueError("semantic authoring adapter must be one executable path")
    raw_path = str(executable_path)
    if not raw_path or "\x00" in raw_path:
        raise ValueError("semantic authoring adapter executable path is invalid")
    if (
        not isinstance(timeout_seconds, int)
        or isinstance(timeout_seconds, bool)
        or not 1 <= timeout_seconds <= MAX_AUTHORING_TIMEOUT_SECONDS
    ):
        raise ValueError("semantic authoring adapter timeout must be 1-7200 seconds")
    executable = _ordinary_executable(Path(raw_path))
    command = [str(executable)]
    adapter_binding = {
        "protocol": FORMAL_ADAPTER_PROTOCOL,
        "argv": command,
        "argv_sha256": sha256_json(command),
        "executable_path": str(executable),
        "executable_sha256": sha256_file(executable),
        "timeout_seconds": timeout_seconds,
    }
    if repository_root is None or codex_provider_executable is None:
        raise ValueError(
            "production Codex authoring requires the shipped adapter and provider executable"
        )
    repository = Path(repository_root).resolve(strict=True)
    expected_adapter = (repository / FORMAL_ADAPTER_RELATIVE_PATH).resolve(strict=True)
    if executable != expected_adapter:
        raise ValueError(
            "production Codex authoring requires the repository-shipped adapter"
        )
    provider_binding = _bind_codex_provider(
        codex_provider_executable,
        repository_root=repository,
        timeout_seconds=timeout_seconds,
    )
    return {
        **adapter_binding,
        "protocol": FORMAL_ADAPTER_PROTOCOL,
        "profile": FORMAL_ADAPTER_PROFILE,
        "provider_binding": provider_binding,
        "provider_binding_sha256": sha256_json(provider_binding),
    }


def require_semantic_authoring_adapter(
    binding: Any,
    *,
    verify_executable: bool = True,
) -> Mapping[str, Any]:
    if not isinstance(binding, Mapping):
        raise ValueError("runtime-owned semantic authoring adapter is unavailable")
    protocol = binding.get("protocol")
    if protocol != FORMAL_ADAPTER_PROTOCOL or set(binding) != FORMAL_ADAPTER_BINDING_FIELDS:
        raise ValueError("runtime-owned production semantic authoring adapter is unavailable")
    argv = binding.get("argv")
    if (
        not isinstance(argv, list)
        or len(argv) != 1
        or not all(
            isinstance(argument, str) and argument and "\x00" not in argument
            for argument in argv
        )
        or binding.get("argv_sha256") != sha256_json(argv)
        or argv[0] != binding.get("executable_path")
    ):
        raise ValueError("runtime-owned semantic authoring adapter binding is invalid")
    executable_path = binding.get("executable_path")
    executable_sha256 = binding.get("executable_sha256")
    if (
        not isinstance(executable_path, str)
        or not Path(executable_path).is_absolute()
        or not _is_sha256(executable_sha256)
    ):
        raise ValueError("runtime-owned semantic authoring adapter binding is invalid")
    if verify_executable:
        executable = _ordinary_executable(Path(argv[0]))
        if str(executable) != executable_path:
            raise ValueError("semantic authoring adapter executable path drifted")
        if sha256_file(executable) != executable_sha256:
            raise ValueError("semantic authoring adapter executable SHA-256 drifted")
    timeout_seconds = binding.get("timeout_seconds")
    if (
        not isinstance(timeout_seconds, int)
        or isinstance(timeout_seconds, bool)
        or not 1 <= timeout_seconds <= MAX_AUTHORING_TIMEOUT_SECONDS
    ):
        raise ValueError("semantic authoring adapter timeout binding is invalid")
    if protocol == FORMAL_ADAPTER_PROTOCOL:
        provider = binding.get("provider_binding")
        if (
            binding.get("profile") != FORMAL_ADAPTER_PROFILE
            or not isinstance(provider, Mapping)
            or set(provider) != PROVIDER_BINDING_FIELDS
            or binding.get("provider_binding_sha256")
            != sha256_json(dict(provider))
        ):
            raise ValueError("production Codex provider binding is invalid")
        provider_argv = provider.get("argv")
        repository_root = provider.get("repository_root")
        provider_path = provider.get("executable_path")
        provider_sha256 = provider.get("executable_sha256")
        expected_adapter = (
            Path(str(repository_root)) / FORMAL_ADAPTER_RELATIVE_PATH
            if isinstance(repository_root, str)
            and Path(repository_root).is_absolute()
            and os.path.normpath(repository_root) == repository_root
            else None
        )
        if (
            provider.get("protocol") != CODEX_PROVIDER_PROTOCOL
            or provider.get("model") != CODEX_MODEL
            or provider.get("reasoning_effort") != CODEX_REASONING_EFFORT
            or provider.get("approval_policy") != CODEX_APPROVAL_POLICY
            or provider.get("sandbox") != CODEX_SANDBOX
            or provider.get("ephemeral") is not True
            or provider.get("ignore_user_config") is not True
            or not isinstance(provider.get("strict_config"), bool)
            or provider.get("web_search") != CODEX_WEB_SEARCH
            or provider.get("timeout_seconds") != timeout_seconds
            or not isinstance(provider_path, str)
            or not Path(provider_path).is_absolute()
            or os.path.normpath(provider_path) != provider_path
            or not _is_sha256(provider_sha256)
            or not isinstance(provider_argv, list)
            or provider_argv != _codex_provider_argv(Path(provider_path))
            or provider.get("argv_sha256") != sha256_json(provider_argv)
            or expected_adapter is None
            or str(expected_adapter) != executable_path
        ):
            raise ValueError("production Codex provider binding is invalid")
        if verify_executable:
            provider_executable = _ordinary_executable(
                Path(provider_path), label="Codex provider"
            )
            if str(provider_executable) != provider_path:
                raise ValueError("Codex provider executable path drifted")
            if sha256_file(provider_executable) != provider_sha256:
                raise ValueError("Codex provider executable SHA-256 drifted")
    return binding


def adapter_binding_from_contract(
    run_contract: Mapping[str, Any],
    *,
    verify_executable: bool = True,
) -> Mapping[str, Any]:
    capability = run_contract.get("capability_snapshot")
    binding = (
        capability.get("semantic_authoring_adapter")
        if isinstance(capability, Mapping)
        else None
    )
    validated = require_semantic_authoring_adapter(
        binding,
        verify_executable=verify_executable,
    )
    if validated.get("protocol") == FORMAL_ADAPTER_PROTOCOL:
        repository_root = run_contract.get("repository_root")
        provider = validated["provider_binding"]
        if (
            not isinstance(repository_root, str)
            or provider.get("repository_root") != repository_root
            or validated.get("executable_path")
            != str(Path(repository_root) / FORMAL_ADAPTER_RELATIVE_PATH)
        ):
            raise ValueError(
                "production Codex provider differs from the run repository authority"
            )
    return validated


def variant_problem(
    run_contract: Mapping[str, Any],
    *,
    requested_stance: str,
    time_window: str | None,
) -> dict[str, Any]:
    frozen = deepcopy(dict(run_contract["problem_contract"]))
    frozen["requested_stance"] = requested_stance
    if time_window is not None:
        frozen["time_window"] = time_window
    return frozen


def variant_contract(
    run_contract: Mapping[str, Any],
    *,
    requested_stance: str,
    time_window: str | None,
) -> dict[str, Any]:
    updated = deepcopy(dict(run_contract))
    frozen = variant_problem(
        run_contract,
        requested_stance=requested_stance,
        time_window=time_window,
    )
    updated["problem_contract"] = frozen
    updated["problem_contract_sha256"] = contract_hash(frozen)
    updated["stance_neutrality_key"] = stance_neutrality_key(
        frozen, mode=str(updated["mode"])
    )
    return updated


def evidence_context_sha256(
    packet: Mapping[str, Any], concept_authority: Mapping[str, Any]
) -> str:
    return sha256_json(
        {
            "retrieval": packet.get("retrieval"),
            "evidence": packet.get("evidence"),
            "concept_authority": dict(concept_authority),
        }
    )


def _concept_authority_binding(
    packet: Mapping[str, Any], run_contract: Mapping[str, Any]
) -> dict[str, Any]:
    rows, binding = load_concept_authority(
        Path(str(run_contract["repository_root"]))
    )
    if packet.get("concept_disposition") != rows:
        raise ValueError(
            "semantic authoring candidate closure differs from repository authority"
        )
    return binding


def _semantic_inputs(packet: Mapping[str, Any]) -> dict[str, Any]:
    missing = [
        field
        for field in SEMANTIC_AUTHORING_FIELDS
        if field not in {"framework_gap", "answer_delivery"} and field not in packet
    ]
    if missing:
        raise ValueError(
            "semantic authoring input is incomplete: " + ", ".join(missing)
        )
    return {
        field: deepcopy(packet.get(field)) for field in SEMANTIC_AUTHORING_FIELDS
    }


def _adapter_request(
    packet: Mapping[str, Any],
    run_contract: Mapping[str, Any],
    source_lock: Mapping[str, Any],
    read_plan: Mapping[str, Any],
    concept_authority: Mapping[str, Any],
    *,
    variant_kind: str,
    generation_context_id: str,
) -> dict[str, Any]:
    requested_stance, shifted_window = AUTHORING_VARIANTS[variant_kind]
    problem = variant_problem(
        run_contract,
        requested_stance=requested_stance,
        time_window=shifted_window,
    )
    return {
        "schema_id": "xi-kari.v3.semantic-authoring-request",
        "schema_version": 1,
        "variant_kind": variant_kind,
        "generation_context_id": generation_context_id,
        "mode": run_contract["mode"],
        "requested_stance": requested_stance,
        "time_window": problem["time_window"],
        "problem_contract": problem,
        "source_inputs": {
            "source_version": run_contract["source_version"],
            "validator_set_sha256": run_contract["validator_set_sha256"],
            "repository_root": run_contract["repository_root"],
            "reader_root": str(
                Path(str(run_contract["repository_root"]))
                / "references/source/v8.3/reader"
            ),
            "source_manifest_path": str(
                Path(str(run_contract["repository_root"]))
                / "references/source/v8.3/source-manifest.json"
            ),
            "source_lock": deepcopy(dict(source_lock)),
            "read_plan": deepcopy(dict(read_plan)),
            "retrieval": deepcopy(packet.get("retrieval")),
            "evidence": deepcopy(packet.get("evidence")),
            "concept_authority": deepcopy(dict(concept_authority)),
            "facts": deepcopy(packet.get("facts")),
        },
    }


def _semantic_field_set_valid(payload: Mapping[str, Any]) -> bool:
    required = set(SEMANTIC_AUTHORING_FIELDS) - {"answer_delivery"}
    return required.issubset(payload) and set(payload).issubset(SEMANTIC_AUTHORING_FIELDS)


def _parse_semantic_payload(stdout: bytes) -> dict[str, Any]:
    try:
        text = stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("semantic authoring adapter stdout is not UTF-8") from exc
    try:
        payload = read_json_text(text)
    except Exception as exc:
        raise ValueError("semantic authoring adapter stdout is not valid JSON") from exc
    if not isinstance(payload, dict) or not _semantic_field_set_valid(payload):
        raise ValueError("semantic authoring adapter output is not semantic-only")
    if stdout != canonical_bytes(payload):
        raise ValueError("semantic authoring adapter stdout is not canonical JSON")
    return payload


def _validate_provider_execution(
    record: Any, *, payload: Mapping[str, Any], adapter_pid: int
) -> None:
    if not isinstance(record, Mapping) or set(record) != PROVIDER_EXECUTION_FIELDS:
        raise ValueError("provider file execution receipt fields are not exact")
    if record.get("protocol") != OUTPUT_TRANSPORT or record.get("exit_status") != 0:
        raise ValueError("provider file execution protocol or exit status is invalid")
    for field in ("provider_parent_pid", "provider_child_pid"):
        if not isinstance(record[field], int) or isinstance(record[field], bool) or record[field] < 1:
            raise ValueError("provider process identity is invalid")
    if record["provider_parent_pid"] != adapter_pid or record["provider_child_pid"] == adapter_pid:
        raise ValueError("provider process identity is not bound to its actual adapter")
    if not isinstance(record["events"], str) or not isinstance(record["semantic_file_content"], str):
        raise ValueError("provider file execution content is unavailable")
    events = record["events"].encode("utf-8")
    thread_id, _ = parse_provider_events(events)
    raw = record["semantic_file_content"].encode("utf-8")
    if not raw or len(raw) > 16 * 1024 * 1024:
        raise ValueError("provider semantic output file size is invalid")
    if record["events_sha256"] != sha256_bytes(events) or record["thread_id"] != thread_id:
        raise ValueError("provider event stream differs from its receipt")
    if record["semantic_file_sha256"] != sha256_bytes(raw) or record["semantic_file_byte_count"] != len(raw):
        raise ValueError("provider semantic output file differs from its receipt")
    file_payload = read_json_text(raw.decode("utf-8"))
    if not isinstance(file_payload, dict):
        raise ValueError("provider semantic output file is not an object")
    file_payload.setdefault("answer_delivery", None)
    normalized_payload = dict(payload)
    normalized_payload.setdefault("answer_delivery", None)
    if file_payload != normalized_payload:
        raise ValueError("provider semantic output file differs from its semantic packet")


def _adapter_input(
    binding: Mapping[str, Any], request: Mapping[str, Any]
) -> tuple[dict[str, Any], bytes, bytes]:
    semantic_request = canonical_bytes(request)
    require_semantic_authoring_adapter(binding, verify_executable=False)
    outer = {
        "protocol": CODEX_ADAPTER_PROTOCOL,
        "provider_binding": deepcopy(dict(binding["provider_binding"])),
        "semantic_request": deepcopy(dict(request)),
    }
    return outer, semantic_request, canonical_bytes(outer)


def _process_isolation_kwargs() -> dict[str, Any]:
    if os.name == "posix":
        return {"start_new_session": True}
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {}


def _adapter_launch_argv(binding: Mapping[str, Any]) -> list[str]:
    """Build the host process argv without changing the bound adapter identity."""

    argv = list(binding["argv"])
    executable = Path(str(binding["executable_path"]))
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
            shebang = handle.readline(4096).rstrip(b"\r\n")
    except OSError:
        return argv
    if not shebang.startswith(b"#!"):
        return argv
    if shebang in {b"#!/usr/bin/env python", b"#!/usr/bin/env python3"}:
        return [str(interpreter), *argv]
    declared_path = os.fsdecode(shebang[2:])
    if not declared_path or "\x00" in declared_path:
        return argv
    declared = Path(declared_path)
    if not declared.is_absolute():
        return argv
    try:
        if not declared.samefile(interpreter):
            return argv
    except OSError:
        return argv
    return [str(interpreter), *argv]


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif os.name == "nt":
        try:
            subprocess.run(
                [
                    "taskkill",
                    "/PID",
                    str(process.pid),
                    "/T",
                    "/F",
                ],
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


class AuthoringCommunicationError(ValueError):
    """A failed bounded exchange with its actual captured process streams."""

    def __init__(self, message: str, *, stdout: bytes, stderr: bytes, input_complete: bool):
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr
        self.input_complete = input_complete


def _communicate_limited(
    process: subprocess.Popen[bytes],
    stdin: bytes,
    *,
    timeout_seconds: int,
    label: str = "semantic authoring adapter",
) -> tuple[bytes, bytes, bool]:
    streams = {
        "stdout": (
            process.stdout,
            MAX_ADAPTER_STDOUT_BYTES,
            bytearray(),
        ),
        "stderr": (
            process.stderr,
            MAX_ADAPTER_STDERR_BYTES,
            bytearray(),
        ),
    }
    limit_exceeded = threading.Event()
    exceeded_channel: list[str] = []
    channel_lock = threading.Lock()
    reader_done = {
        channel: threading.Event() for channel in streams
    }
    writer_done = threading.Event()
    writer_failed = threading.Event()

    def read_stream(channel: str) -> None:
        stream, limit, output = streams[channel]
        try:
            if stream is None:
                return
            while True:
                chunk = os.read(stream.fileno(), 64 * 1024)
                if not chunk:
                    return
                remaining = limit + 1 - len(output)
                if remaining > 0:
                    output.extend(chunk[:remaining])
                if len(chunk) > remaining or len(output) > limit:
                    with channel_lock:
                        if not exceeded_channel:
                            exceeded_channel.append(channel)
                    limit_exceeded.set()
                    return
        except (OSError, ValueError):
            return
        finally:
            reader_done[channel].set()

    def write_stdin() -> None:
        try:
            if process.stdin is not None:
                view = memoryview(stdin)
                offset = 0
                descriptor = process.stdin.fileno()
                while offset < len(view):
                    written = os.write(
                        descriptor,
                        view[offset : offset + 64 * 1024],
                    )
                    if written < 1:
                        raise BrokenPipeError
                    offset += written
        except (BrokenPipeError, OSError, ValueError):
            writer_failed.set()
        finally:
            try:
                if process.stdin is not None:
                    process.stdin.close()
            except OSError:
                pass
            writer_done.set()

    readers = [
        threading.Thread(
            target=read_stream,
            args=(channel,),
            daemon=True,
            name=f"xi-kari-{channel}-reader",
        )
        for channel in streams
    ]
    writer = threading.Thread(
        target=write_stdin,
        daemon=True,
        name="xi-kari-stdin-writer",
    )
    started_threads: list[threading.Thread] = []
    cleanup_complete = False
    failure: str | None = None
    try:
        for thread in [*readers, writer]:
            thread.start()
            started_threads.append(thread)

        deadline = time.monotonic() + timeout_seconds
        while True:
            if limit_exceeded.is_set():
                failure = (
                    f"{label} "
                    f"{exceeded_channel[0]} exceeds the size limit"
                )
                break
            if (
                process.poll() is not None
                and writer_done.is_set()
                and all(done.is_set() for done in reader_done.values())
            ):
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                failure = f"{label} timed out"
                break
            limit_exceeded.wait(min(0.02, remaining))

        if failure is not None:
            _terminate_process_tree(process)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            _terminate_process_tree(process)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired as final_exc:
                raise ValueError(
                    "semantic authoring adapter could not be reaped"
                ) from final_exc
            if failure is None:
                failure = "semantic authoring adapter timed out"
        _terminate_process_tree(process)
        cleanup_complete = True
    finally:
        if not cleanup_complete:
            _terminate_process_tree(process)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                _terminate_process_tree(process)
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
            _terminate_process_tree(process)
        for stream in (process.stdin, process.stdout, process.stderr):
            try:
                if stream is not None:
                    stream.close()
            except OSError:
                pass
        for thread in started_threads:
            thread.join(timeout=1)
    if failure is not None:
        raise AuthoringCommunicationError(failure,
            stdout=bytes(streams["stdout"][2]), stderr=bytes(streams["stderr"][2]),
            input_complete=writer_done.is_set() and not writer_failed.is_set())
    return (
        bytes(streams["stdout"][2]),
        bytes(streams["stderr"][2]),
        not writer_failed.is_set(),
    )


def _execute_adapter(
    binding: Mapping[str, Any], request: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    require_semantic_authoring_adapter(binding, verify_executable=True)
    _outer, semantic_request, stdin = _adapter_input(binding, request)
    if len(stdin) >= MAX_ADAPTER_STDIN_BYTES:
        raise ValueError("semantic authoring adapter input exceeds the size limit")
    process = subprocess.Popen(
        _adapter_launch_argv(binding),
        cwd=Path(str(binding["executable_path"])).parent,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        **_process_isolation_kwargs(),
    )
    stdout, stderr, input_complete = _communicate_limited(
        process,
        stdin,
        timeout_seconds=int(binding["timeout_seconds"]),
    )
    returncode = process.returncode
    require_semantic_authoring_adapter(binding, verify_executable=True)
    if len(stdout) > MAX_ADAPTER_STDOUT_BYTES:
        raise ValueError("semantic authoring adapter stdout exceeds the size limit")
    if len(stderr) > MAX_ADAPTER_STDERR_BYTES:
        raise ValueError("semantic authoring adapter stderr exceeds the size limit")
    if returncode != 0:
        diagnostic = stderr[:4096].decode("utf-8", errors="replace").strip()
        suffix = f": {diagnostic}" if diagnostic else ""
        raise ValueError(
            f"semantic authoring adapter exited with status {returncode}{suffix}"
        )
    envelope = read_json_text(stdout.decode("utf-8"))
    if not isinstance(envelope, dict) or set(envelope) != {"protocol", "semantic_packet", "provider_execution"} or envelope.get("protocol") != OUTPUT_TRANSPORT or canonical_bytes(envelope) != stdout:
        raise ValueError("adapter did not return the fixed-file transport envelope")
    payload = _parse_semantic_payload(canonical_bytes(envelope["semantic_packet"]))
    _validate_provider_execution(envelope["provider_execution"], payload=payload, adapter_pid=process.pid)
    if not input_complete:
        raise ValueError(
            "semantic authoring adapter did not accept the complete input"
        )
    receipt: dict[str, Any] = {
        "protocol": FORMAL_RECEIPT_PROTOCOL,
        "adapter_executable_sha256": binding["executable_sha256"],
        "adapter_argv_sha256": binding["argv_sha256"],
        "variant_kind": request["variant_kind"],
        "requested_stance": request["requested_stance"],
        "time_window": request["time_window"],
        "generation_context_id": request["generation_context_id"],
        "input_sha256": sha256_bytes(stdin),
        "input_byte_count": len(stdin),
        "stdout_sha256": sha256_bytes(stdout),
        "stdout_byte_count": len(stdout),
        "stderr_sha256": sha256_bytes(stderr),
        "child_pid": process.pid,
        "parent_pid": os.getpid(),
        "exit_status": returncode,
        "semantic_packet_sha256": sha256_json(payload),
        "provider_execution": envelope["provider_execution"],
    }
    if binding.get("protocol") == FORMAL_ADAPTER_PROTOCOL:
        provider = binding["provider_binding"]
        receipt.update(
            {
                "semantic_request_sha256": sha256_bytes(semantic_request),
                "semantic_request_byte_count": len(semantic_request),
                "outer_input_sha256": sha256_bytes(stdin),
                "outer_input_byte_count": len(stdin),
                "provider_binding_sha256": binding["provider_binding_sha256"],
                "provider_executable_sha256": provider["executable_sha256"],
                "provider_argv_sha256": provider["argv_sha256"],
            }
        )
    return payload, receipt


def author_semantic_probe_variants(
    packet: Mapping[str, Any],
    run_contract: Mapping[str, Any],
    *,
    source_lock: Mapping[str, Any],
    read_plan: Mapping[str, Any],
    input_packet_sha256: str,
) -> dict[str, Any]:
    if "semantic_probe_authorings" in packet:
        raise ValueError("semantic probe authoring control is runtime-owned")
    binding = adapter_binding_from_contract(run_contract, verify_executable=True)
    concept_authority = _concept_authority_binding(packet, run_contract)
    context_hash = evidence_context_sha256(packet, concept_authority)
    records: list[dict[str, Any]] = []
    base_semantic_sha256 = sha256_json(_semantic_inputs(packet))
    for variant_kind, (requested_stance, shifted_window) in AUTHORING_VARIANTS.items():
        generation_context_id = f"XK-AUTH-{uuid.uuid4().hex}"
        request = _adapter_request(
            packet,
            run_contract,
            source_lock,
            read_plan,
            concept_authority,
            variant_kind=variant_kind,
            generation_context_id=generation_context_id,
        )
        semantic_packet, receipt = _execute_adapter(binding, request)
        expected_problem = variant_problem(
            run_contract,
            requested_stance=requested_stance,
            time_window=shifted_window,
        )
        authored_problem = semantic_packet.get("problem_contract")
        if not isinstance(authored_problem, Mapping):
            raise ValueError("semantic authoring adapter omitted problem_contract")
        frozen_problem = validate_problem_contract(
            {field: authored_problem.get(field) for field in FROZEN_FIELDS},
            mode=str(run_contract["mode"]),
        )
        if dict(frozen_problem) != expected_problem:
            raise ValueError(
                "semantic authoring adapter output differs from the requested variant"
            )
        semantic_packet_sha256 = sha256_json(semantic_packet)
        if sha256_json(_semantic_inputs(semantic_packet)) == base_semantic_sha256:
            raise ValueError(
                "semantic authoring adapter returned an unchanged input packet"
            )
        records.append(
            {
                "authoring_id": (
                    f"{variant_kind}-{semantic_packet_sha256[:16]}-"
                    f"{generation_context_id[-12:]}"
                ),
                "variant_kind": variant_kind,
                "generation_context_id": generation_context_id,
                "requested_stance": requested_stance,
                "time_window": expected_problem["time_window"],
                "problem_contract_sha256": contract_hash(expected_problem),
                "evidence_context_sha256": context_hash,
                "semantic_packet_sha256": semantic_packet_sha256,
                "runtime_receipt": receipt,
                "runtime_receipt_sha256": sha256_json(receipt),
                "semantic_packet": semantic_packet,
            }
        )
    if len({record["runtime_receipt"]["child_pid"] for record in records}) != len(
        records
    ):
        raise ValueError("semantic authoring variants lack distinct child processes")
    if len({sha256_json(_semantic_inputs(record["semantic_packet"])) for record in records}) != len(records):
        raise ValueError("semantic authoring adapter returned duplicate variant outputs")
    bundle = {
        "schema_id": "xi-kari.v3.semantic-probe-authorings",
        "schema_version": 3,
        "run_id": run_contract["run_id"],
        "input_packet_sha256": input_packet_sha256,
        "source_lock_sha256": sha256_json(dict(source_lock)),
        "read_plan_sha256": sha256_json(dict(read_plan)),
        "adapter_binding_sha256": sha256_json(dict(binding)),
        "authorings": records,
    }
    validate_semantic_probe_authorings(
        bundle,
        packet,
        run_contract,
        source_lock=source_lock,
        read_plan=read_plan,
        input_packet_sha256=input_packet_sha256,
        verify_executable=False,
    )
    return bundle


def validate_semantic_probe_authorings(
    bundle: Mapping[str, Any],
    packet: Mapping[str, Any],
    run_contract: Mapping[str, Any],
    *,
    source_lock: Mapping[str, Any],
    read_plan: Mapping[str, Any],
    input_packet_sha256: str,
    verify_executable: bool = False,
) -> dict[str, Mapping[str, Any]]:
    binding = adapter_binding_from_contract(
        run_contract,
        verify_executable=verify_executable,
    )
    if (
        not isinstance(bundle, Mapping)
        or bundle.get("schema_id") != "xi-kari.v3.semantic-probe-authorings"
        or bundle.get("schema_version") != 3
        or bundle.get("run_id") != run_contract.get("run_id")
        or bundle.get("input_packet_sha256") != input_packet_sha256
        or bundle.get("source_lock_sha256") != sha256_json(dict(source_lock))
        or bundle.get("read_plan_sha256") != sha256_json(dict(read_plan))
        or bundle.get("adapter_binding_sha256") != sha256_json(dict(binding))
    ):
        raise ValueError("runtime-owned semantic probe authoring is missing")
    records = bundle.get("authorings")
    if not isinstance(records, list) or len(records) != len(AUTHORING_VARIANTS):
        raise ValueError("runtime-owned semantic probe authoring set is incomplete")
    if not all(isinstance(record, Mapping) for record in records):
        raise ValueError("runtime-owned semantic probe authoring record is invalid")
    by_kind = {str(record.get("variant_kind")): record for record in records}
    authoring_ids = {record.get("authoring_id") for record in records}
    contexts = {record.get("generation_context_id") for record in records}
    receipts = [record.get("runtime_receipt") for record in records]
    process_ids = {
        receipt.get("child_pid")
        for receipt in receipts
        if isinstance(receipt, Mapping)
    }
    if (
        set(by_kind) != set(AUTHORING_VARIANTS)
        or len(authoring_ids) != len(records)
        or None in authoring_ids
        or len(contexts) != len(records)
        or None in contexts
        or len(process_ids) != len(records)
        or None in process_ids
    ):
        raise ValueError(
            "runtime-owned semantic authorings lack distinct process identities"
        )
    concept_authority = _concept_authority_binding(packet, run_contract)
    context_hash = evidence_context_sha256(packet, concept_authority)
    base_semantic_sha256 = sha256_json(_semantic_inputs(packet))
    output_hashes: set[str] = set()
    for variant_kind, record in by_kind.items():
        requested_stance, shifted_window = AUTHORING_VARIANTS[variant_kind]
        expected_problem = variant_problem(
            run_contract,
            requested_stance=requested_stance,
            time_window=shifted_window,
        )
        semantic_packet = record.get("semantic_packet")
        if not isinstance(semantic_packet, Mapping) or not _semantic_field_set_valid(semantic_packet):
            raise ValueError("runtime-owned semantic authoring payload is incomplete")
        authored_problem = semantic_packet.get("problem_contract")
        if not isinstance(authored_problem, Mapping):
            raise ValueError("runtime-owned semantic authoring problem is missing")
        frozen_problem = validate_problem_contract(
            {field: authored_problem.get(field) for field in FROZEN_FIELDS},
            mode=str(run_contract["mode"]),
        )
        semantic_packet_sha256 = sha256_json(dict(semantic_packet))
        generation_context_id = record.get("generation_context_id")
        request = _adapter_request(
            packet,
            run_contract,
            source_lock,
            read_plan,
            concept_authority,
            variant_kind=variant_kind,
            generation_context_id=str(generation_context_id),
        )
        _outer, semantic_request_bytes, outer_input_bytes = _adapter_input(
            binding, request
        )
        receipt = record.get("runtime_receipt")
        expected_receipt_fields = FORMAL_RUNTIME_RECEIPT_FIELDS
        if isinstance(receipt, Mapping):
            _validate_provider_execution(receipt.get("provider_execution"), payload=semantic_packet, adapter_pid=receipt.get("child_pid"))
        expected_stdout = canonical_bytes({
            "protocol": OUTPUT_TRANSPORT, "semantic_packet": semantic_packet,
            "provider_execution": receipt.get("provider_execution") if isinstance(receipt, Mapping) else None,
        })
        if (
            record.get("requested_stance") != requested_stance
            or record.get("time_window") != expected_problem["time_window"]
            or dict(frozen_problem) != expected_problem
            or record.get("problem_contract_sha256") != contract_hash(expected_problem)
            or record.get("evidence_context_sha256") != context_hash
            or record.get("semantic_packet_sha256") != semantic_packet_sha256
            or sha256_json(_semantic_inputs(semantic_packet)) == base_semantic_sha256
            or not isinstance(receipt, Mapping)
            or set(receipt) != expected_receipt_fields
            or receipt.get("protocol")
            != FORMAL_RECEIPT_PROTOCOL
            or receipt.get("adapter_executable_sha256")
            != binding["executable_sha256"]
            or receipt.get("adapter_argv_sha256") != binding["argv_sha256"]
            or receipt.get("variant_kind") != variant_kind
            or receipt.get("requested_stance") != requested_stance
            or receipt.get("time_window") != expected_problem["time_window"]
            or receipt.get("generation_context_id") != generation_context_id
            or receipt.get("input_sha256") != sha256_bytes(outer_input_bytes)
            or receipt.get("input_byte_count") != len(outer_input_bytes)
            or not 0 < receipt["input_byte_count"] < MAX_ADAPTER_STDIN_BYTES
            or receipt.get("stdout_sha256") != sha256_bytes(expected_stdout)
            or receipt.get("stdout_byte_count") != len(expected_stdout)
            or not isinstance(receipt.get("stderr_sha256"), str)
            or len(receipt["stderr_sha256"]) != 64
            or not isinstance(receipt.get("child_pid"), int)
            or isinstance(receipt.get("child_pid"), bool)
            or receipt["child_pid"] < 1
            or not isinstance(receipt.get("parent_pid"), int)
            or isinstance(receipt.get("parent_pid"), bool)
            or receipt["parent_pid"] < 1
            or receipt["child_pid"] == receipt["parent_pid"]
            or receipt.get("exit_status") != 0
            or receipt.get("semantic_packet_sha256") != semantic_packet_sha256
            or record.get("runtime_receipt_sha256") != sha256_json(dict(receipt))
        ):
            raise ValueError("runtime-owned semantic authoring receipt is invalid")
        if receipt.get("protocol") == FORMAL_RECEIPT_PROTOCOL:
            provider = binding["provider_binding"]
            if (
                receipt.get("semantic_request_sha256")
                != sha256_bytes(semantic_request_bytes)
                or receipt.get("semantic_request_byte_count")
                != len(semantic_request_bytes)
                or not 0
                < receipt["semantic_request_byte_count"]
                < MAX_ADAPTER_STDIN_BYTES
                or receipt.get("outer_input_sha256")
                != sha256_bytes(outer_input_bytes)
                or receipt.get("outer_input_byte_count") != len(outer_input_bytes)
                or receipt["outer_input_byte_count"] != receipt["input_byte_count"]
                or receipt.get("provider_binding_sha256")
                != binding["provider_binding_sha256"]
                or receipt.get("provider_executable_sha256")
                != provider["executable_sha256"]
                or receipt.get("provider_argv_sha256")
                != provider["argv_sha256"]
            ):
                raise ValueError("runtime-owned Codex provider receipt is invalid")
        output_hashes.add(sha256_json(_semantic_inputs(semantic_packet)))
    if len(output_hashes) != len(records):
        raise ValueError("runtime-owned semantic authorings contain duplicate outputs")
    return by_kind
