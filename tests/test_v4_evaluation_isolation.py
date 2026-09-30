from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tomllib

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from xi_kari_runtime import evaluation_v4 as evaluation
from xi_kari_runtime.canonical_json import canonical_bytes


def test_real_author_arguments_grant_only_workspace_and_runtime_reads(tmp_path: Path) -> None:
    executable = tmp_path / "runtime/bin/codex"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"synthetic executable identity")
    workspace = tmp_path / "author"
    workspace.mkdir()
    argv = evaluation._codex_argv({"executable": str(executable)}, workspace, workspace / "answer.md")
    overrides = [argv[index + 1] for index, value in enumerate(argv[:-1]) if value == "--config"]
    permissions = [tomllib.loads(value)["permissions"] for value in overrides if value.startswith("permissions.")]

    assert permissions, "workspace-write alone does not restrict author reads"
    selected = permissions[0]["xikari_p14_author"]
    assert selected["filesystem"][":root"] == "deny"
    assert selected["filesystem"][":minimal"] == "read"
    assert selected["filesystem"][workspace.as_posix()] == "write"
    assert selected["network"]["enabled"] is False
    assert "--sandbox" not in argv
    for feature in ("plugins", "memories", "hooks", "apps", "multi_agent"):
        assert f"features.{feature}=false" in overrides


def test_true_flags_and_hashed_text_do_not_replace_an_isolation_launcher(tmp_path: Path) -> None:
    executable = Path(sys.executable).resolve()
    profile = {"kind": "codex_subscription", "executable": str(executable),
        "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "model": "gpt-6.1-sol", "reasoning_effort": "max", "isolation_command_prefix": []}
    evidence = tmp_path / "claim.txt"
    evidence.write_bytes(b"Synthetic assertion, not an operating-system boundary observation")
    fields = ("subscription_only", "model_effort_available", "author_filesystem_isolated",
              "network_tools_disabled", "external_context_disabled", "one_author_turn")
    receipt = {"executable_sha256": profile["executable_sha256"], "model": "gpt-6.1-sol",
        "reasoning_effort": "max", "launch_profile_sha256": hashlib.sha256(canonical_bytes(profile)).hexdigest(),
        **{field: True for field in fields},
        "evidence": {field: {"path": str(evidence), "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest()} for field in fields}}
    path = tmp_path / "preflight.json"
    path.write_bytes(canonical_bytes(receipt))
    profile["preflight_receipt"] = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    _, issues = evaluation._profile(profile, fixture_mode=False)

    assert "isolation_launcher_missing" in issues


def test_launcher_contents_are_bound_and_mutation_is_not_rehashed_away(tmp_path: Path) -> None:
    executable = Path(sys.executable).resolve()
    launcher = tmp_path / "isolated_launcher.py"
    launcher.write_text("raise SystemExit(0)\n", encoding="utf-8")
    profile = {"kind": "deterministic_fixture", "executable": str(executable),
        "model": "gpt-6.1-sol", "reasoning_effort": "max",
        "isolation_command_prefix": [str(executable), "-I", "-B", str(launcher)],
        "launcher_files": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in (executable, launcher)}}

    frozen, issues = evaluation._profile(profile, fixture_mode=True)
    assert issues == []
    assert frozen["launcher_files"] == profile["launcher_files"]
    launcher.write_text("raise SystemExit(99)\n", encoding="utf-8")

    checked, issues = evaluation._profile(frozen, fixture_mode=True)

    assert "isolation_launcher_artifact_changed" in issues
    assert checked["launcher_files"] == profile["launcher_files"]


def test_model_observation_uses_only_the_private_attempt_session(tmp_path: Path) -> None:
    thread_id = "12345678-1234-1234-1234-123456789abc"
    sessions = tmp_path / "codex-sessions"
    path = sessions / "2026/09/30" / ("rollout-" + thread_id + ".jsonl")
    path.parent.mkdir(parents=True)
    events = [
        {"type": "session_meta", "payload": {"model_provider": "openai"}},
        {"type": "turn_context", "payload": {"model": "gpt-6.1-sol", "effort": "max"}},
    ]
    path.write_text("\n".join(json.dumps(row) for row in events) + "\n", encoding="utf-8")

    observed = evaluation._observed_session(thread_id, session_root=sessions)

    assert (observed["model"], observed["reasoning_effort"], observed["provider"]) == ("gpt-6.1-sol", "max", "openai")
    assert evaluation._observed_session("99999999-1234-1234-1234-123456789abc", session_root=sessions) == {}


def test_subscription_arguments_keep_the_builtin_openai_provider_and_cell_retry_budget(tmp_path: Path) -> None:
    executable = tmp_path / "runtime/bin/codex"
    workspace = tmp_path / "workspace"
    argv = evaluation._codex_argv({"executable": str(executable)}, workspace, workspace / "answer.md")
    overrides = [argv[index + 1] for index, value in enumerate(argv[:-1]) if value == "--config"]

    assert not any(value.startswith("model_providers.") for value in overrides)
    assert 'model_provider="openai"' in overrides
    assert 'forced_login_method="chatgpt"' in overrides
    assert argv[argv.index("--model") + 1] == "gpt-6.1-sol"
    assert 'model_reasoning_effort="max"' in overrides
    assert (evaluation.OUTPUT_TOKENS, evaluation.TIMEOUT_SECONDS) == (6000, 1200)
