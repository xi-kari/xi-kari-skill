import errno
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from xi_kari_runtime import execution, materialization
from xi_kari_runtime.authoring import bind_base_authoring_provider
from xi_kari_runtime.problem_contract import build_natural_request_envelope, draft_problem_contract_from_natural_request


@pytest.mark.parametrize("timeout", [1200, 7200])
def test_execute_preserves_timeout_in_every_provider_binding(tmp_path, monkeypatch, timeout):
    observed = []

    def adapter(*args, **kwargs):
        observed.append(("adapter", kwargs["timeout_seconds"]))
        return {"provider_binding": {}}

    def provider(*args, **kwargs):
        observed.append(("provider", kwargs["timeout_seconds"]))
        return {"timeout_seconds": kwargs["timeout_seconds"]}

    def contract(**kwargs):
        observed.append(("contract-execution", kwargs["timeout_seconds"]))
        assert kwargs["provider"]["timeout_seconds"] == kwargs["timeout_seconds"]
        return kwargs["draft_problem_contract"], {}

    class Captured(Exception):
        pass

    def stop(*args, **kwargs):
        raise Captured

    monkeypatch.setattr(execution, "bind_semantic_authoring_adapter", adapter)
    monkeypatch.setattr(execution, "bind_base_authoring_provider", provider)
    monkeypatch.setattr(execution, "_author_natural_contract", contract)
    monkeypatch.setattr(execution, "build_full_source_lock", stop)
    with pytest.raises(Captured):
        execution.execute_authored_run(tmp_path, request_text="解释建议与授权的区别", repository_root=ROOT,
            codex_provider_executable=Path(sys.executable).resolve(), timeout_seconds=timeout)
    assert observed == [("adapter", timeout), ("provider", timeout), ("provider", timeout), ("contract-execution", timeout)]
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("failure", ["missing", "permission", "timeout"])
def test_contract_failure_preserves_observed_bytes_and_cause(tmp_path, monkeypatch, failure):
    provider_path = tmp_path / "provider.py"
    provider_path.write_text(f"#!{Path(sys.executable).resolve()}\n" + '''import json, pathlib, sys, time
sys.stdin.read()
print(json.dumps({"type":"thread.started","thread_id":"failure-fixture"}), flush=True)
print(json.dumps({"type":"turn.started"}), flush=True)
print("provider diagnostic", file=sys.stderr, flush=True)
''' + ("time.sleep(30)\n" if failure == "timeout" else '''pathlib.Path(sys.argv[sys.argv.index("--output-last-message") + 1]).write_text("SEMANTIC_OUTPUT_READY", encoding="utf-8")
print(json.dumps({"type":"turn.completed"}), flush=True)
''') + ('pathlib.Path("semantic-output.json").write_text(\'{"observed":true}\', encoding="utf-8")\n' if failure == "permission" else ""), encoding="utf-8")
    provider_path.chmod(0o755)
    request = build_natural_request_envelope("解释建议与授权的区别", mode="closed-input", evidence_cutoff="2026-09-21T00:00:00Z")
    draft = draft_problem_contract_from_natural_request(request["text"], mode="closed-input", evidence_cutoff=request["evidence_cutoff"])
    provider = bind_base_authoring_provider(provider_path, mode="closed-input", repository_root=ROOT, timeout_seconds=1)
    if failure == "permission":
        def denied(workspace, **kwargs):
            try:
                raise PermissionError(errno.EACCES, "Permission denied", str(workspace / "semantic-output.json"))
            except PermissionError as cause:
                raise ValueError("regular file is unavailable") from cause
        monkeypatch.setattr(execution, "read_semantic_output", denied)
    destination = tmp_path / "failures"
    monkeypatch.setattr(materialization, "default_runs_root", lambda: destination)
    with pytest.raises(ValueError) as captured:
        execution._author_natural_contract(run_id="failure-test", natural_request=request,
            draft_problem_contract=draft, repository_root=ROOT, provider=provider, timeout_seconds=1)
    diagnostic_path = Path(captured.value.diagnostics_path)
    assert diagnostic_path.parent == destination
    report = json.loads((diagnostic_path / "failure.json").read_text("utf-8"))
    assert report["state"] == "failed"
    assert report["stage"] == "natural-contract"
    assert report["child_pid"] != report["parent_pid"]
    assert report["timeout_seconds"] == 1
    assert Path(report["workspace"]).is_relative_to(destination)
    assert report["input_complete"] is True
    assert b"failure-fixture" in (diagnostic_path / "events.jsonl").read_bytes()
    assert b"provider diagnostic" in (diagnostic_path / "stderr.bin").read_bytes()
    assert "SEMANTIC_OUTPUT_READY" in (diagnostic_path / "prompt.txt").read_text("utf-8")
    assert not list(diagnostic_path.glob("*receipt*"))
    assert not (diagnostic_path / "run-contract.json").exists()
    assert not (diagnostic_path / "terminal-record.json").exists()
    if failure == "permission":
        assert any(cause.get("errno") == errno.EACCES for cause in report["error_chain"])
        assert (diagnostic_path / "semantic-output.bin").read_bytes() == b'{"observed":true}'
    if failure == "timeout":
        assert "timed out" in str(captured.value)
    else:
        assert (diagnostic_path / "completion-notice.bin").read_bytes() == b"SEMANTIC_OUTPUT_READY"


def test_base_transport_failure_keeps_diagnostics_without_creating_a_run(tmp_path):
    provider_path = tmp_path / "two_stage_provider.py"
    provider_path.write_text(f"#!{Path(sys.executable).resolve()}\n" + '''import json, pathlib, sys
prompt = sys.stdin.read()
if "运行时请求（只读绑定）：\\n" not in prompt:
 request = json.loads(prompt.rsplit("运行时请求（只读）：\\n", 1)[1])
 pathlib.Path("semantic-output.json").write_text(json.dumps(request["draft_problem_contract"], ensure_ascii=False), encoding="utf-8")
pathlib.Path(sys.argv[sys.argv.index("--output-last-message") + 1]).write_text("SEMANTIC_OUTPUT_READY", encoding="utf-8")
for event in ({"type":"thread.started","thread_id":"two-stage-fixture"}, {"type":"turn.started"}, {"type":"turn.completed"}):
 print(json.dumps(event), flush=True)
''', encoding="utf-8")
    provider_path.chmod(0o755)
    destination = tmp_path / "runs"
    with pytest.raises(ValueError) as captured:
        execution.execute_authored_run(destination, request_text="解释建议与授权的区别", run_id="base-failure",
            repository_root=ROOT, codex_provider_executable=provider_path, timeout_seconds=30)
    diagnostic_path = Path(captured.value.diagnostics_path)
    report = json.loads((diagnostic_path / "failure.json").read_text("utf-8"))
    assert report["stage"] == "base-authoring"
    assert Path(report["workspace"]).is_relative_to(destination)
    assert b"two-stage-fixture" in (diagnostic_path / "events.jsonl").read_bytes()
    assert not (destination / "base-failure").exists()


def test_adapter_failure_retains_a_private_state_workspace(tmp_path, monkeypatch):
    import importlib.util

    spec = importlib.util.spec_from_file_location("adapter_workspace_test", ROOT / "scripts/xi_kari_codex_authoring_adapter.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    destination = tmp_path / "state"
    monkeypatch.setattr(materialization, "default_runs_root", lambda: destination)
    monkeypatch.setattr(adapter, "_build_prompt", lambda request: b"test prompt")

    def fail_launch(*args, **kwargs):
        workspace = Path(kwargs["cwd"])
        assert workspace.is_relative_to(destination)
        raise OSError(errno.EACCES, "fixture launch denied")

    monkeypatch.setattr(adapter.subprocess, "Popen", fail_launch)
    with pytest.raises(ValueError) as captured:
        adapter._run_codex({"argv": [str(Path(sys.executable).resolve())], "timeout_seconds": 1},
            {"generation_context_id": "workspace-fixture"}, repository_root=ROOT,
            executable=Path(sys.executable).resolve(), output_schema_sha256="unused")
    diagnostic_path = Path(captured.value.diagnostics_path)
    assert diagnostic_path.parent == destination
    assert (diagnostic_path / "prompt.txt").read_bytes() == b"test prompt"
    report = json.loads((diagnostic_path / "failure.json").read_text("utf-8"))
    assert report["state"] == "failed"
    assert report["error_chain"][0]["errno"] == errno.EACCES
