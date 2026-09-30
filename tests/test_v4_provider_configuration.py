from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
CHILD = r'''
import json
import os
from pathlib import Path
import sys
from copy import deepcopy

root, work, mode = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "scripts"))
from xi_kari_runtime import authoring
if mode == "frozen":
    os.environ["XI_KARI_PROVIDER_MODEL"] = "different-after-import"
    os.environ["XI_KARI_REASONING_EFFORT"] = "low"
from xi_kari_runtime import semantic_executions_v4 as semantic

provider = semantic.bind_semantic_execution_provider_v4(
    Path(sys.executable), repository_root=root, timeout_seconds=10
)["provider"]
authoring.require_base_authoring_provider(provider, mode="closed-input")
result = {"model": provider["model"], "reasoning_effort": provider["reasoning_effort"],
          "argv": provider["argv"], "base_model": authoring.CODEX_MODEL,
          "base_effort": authoring.CODEX_REASONING_EFFORT}
if mode == "entry":
    from tests.test_natural_contract_freeze import request_and_final
    from xi_kari_runtime.execution import execute_authored_run
    provider_script = work / "entry_provider.py"
    observation = work / "entry_observed.json"
    program = "#!" + str(Path(sys.executable).resolve()) + "\n"
    program += "OBSERVATION = " + repr(str(observation)) + "\n"
    program += "import json, os, pathlib, sys\n"
    program += "prompt = sys.stdin.read()\n"
    program += "pathlib.Path(OBSERVATION).write_text(json.dumps({'pid': os.getpid(), 'argv': sys.argv, 'input_bytes': len(prompt.encode('utf-8')), 'synthetic': True}), encoding='utf-8')\n"
    program += "raise SystemExit(19)\n"
    provider_script.write_text(program, encoding="utf-8", newline="\n")
    provider_script.chmod(0o755)
    _, problem = request_and_final()
    try:
        execute_authored_run(work / "entry", problem_contract=problem, mode="open-world",
            run_id="config-entry", repository_root=root, codex_provider_executable=provider_script,
            contract_version=4, source_version="v9.0", timeout_seconds=30)
    except Exception as exc:
        result["entry_stop"] = type(exc).__name__ + ": " + str(exc)
    result["entry_observation"] = json.loads(observation.read_text(encoding="utf-8")) if observation.exists() else None
elif mode == "verify":
    saved = json.loads((work / "saved.json").read_text(encoding="utf-8"))
    try:
        verified = semantic.validate_semantic_execution_v4(
            saved["execution"], expected_request=saved["request"],
            binding=saved["binding"], repository_root=root,
        )
    except ValueError as exc:
        result.update(accepted=False, diagnostic=str(exc))
    else:
        result.update(accepted=True, verified_status=verified["status"],
                      actual_model_execution=verified["actual_model_execution"])
elif mode not in {"binding", "frozen"}:
    from tests.test_v4_stage_chain_integration import dynamic_inputs
    from tests.test_v4_semantic_executions import fixture_binding
    from xi_kari_runtime.stage_consumers_v4 import validate_stage_chain_v4
    packet, contract = dynamic_inputs()
    controls = validate_stage_chain_v4(packet, run_contract=contract, repository_root=root)
    author_request = controls["stage_results"]["recursion"]["result"]["paths"][0]["nodes"][1]["author_request"]
    request = semantic.build_semantic_execution_request_v4(
        packet, controls, run_contract=contract, kind="next_author",
        author_request=author_request, repository_root=root,
    )
    binding = None if mode == "not_run" else fixture_binding(work, timeout=15)
    if mode == "forged":
        from xi_kari_runtime.canonical_json import sha256_json
        rejected = []
        for target in ("request", "provider", "fixture"):
            for field, forged_value in (("model", "self-declared-model"), ("reasoning_effort", "self-declared-effort")):
                changed_request, changed_binding = deepcopy(request), deepcopy(binding)
                if target == "request":
                    changed_request[field] = forged_value
                elif target == "fixture":
                    changed_binding[field] = forged_value
                else:
                    changed_binding = {"kind": "codex_provider", "provider": deepcopy(provider)}
                    selected = changed_binding["provider"]
                    selected[field] = forged_value
                    if field == "model":
                        selected["argv"][selected["argv"].index("--model") + 1] = forged_value
                    else:
                        selected["argv"] = [f'model_reasoning_effort="{forged_value}"' if item.startswith("model_reasoning_effort=") else item for item in selected["argv"]]
                    selected["argv_sha256"] = sha256_json(selected["argv"])
                attempt = work / (target + "-" + field)
                try:
                    outcome = semantic.execute_semantic_request_v4(
                        changed_request, binding=changed_binding, run_directory=attempt, repository_root=root
                    )
                except ValueError as exc:
                    rejected.append({"target": target, "field": field, "rejected": True,
                                     "launched": False, "run_created": attempt.exists(), "diagnostic": str(exc)})
                else:
                    rejected.append({"target": target, "field": field,
                        "rejected": outcome["status"] == "not_run",
                        "launched": outcome["receipt"]["signed_payload"]["child_pid"] is not None,
                        "run_created": attempt.exists(), "diagnostic": outcome["errors"]})
        result["forged_configurations"] = rejected
    else:
        execution = semantic.execute_semantic_request_v4(
            request, binding=binding, run_directory=work / "run", repository_root=root
        )
        verified = semantic.validate_semantic_execution_v4(
            execution, expected_request=request, binding=binding, repository_root=root
        )
        result.update({"request": request, "fixture_binding": binding,
                       "receipt": execution["receipt"]["signed_payload"],
                       "verified_status": verified["status"],
                       "actual_model_execution": verified["actual_model_execution"]})
        (work / "saved.json").write_text(json.dumps({"execution": execution, "request": request,
                                                    "binding": binding}), encoding="utf-8")
print(json.dumps(result))
'''


@pytest.fixture
def case_dir(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("cfg")


def run_child(case_dir: Path, mode: str, overrides: dict[str, str]) -> dict:
    script = case_dir / "config_child.py"
    script.write_text(CHILD, encoding="utf-8")
    environment = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    environment.pop("XI_KARI_PROVIDER_MODEL", None)
    environment.pop("XI_KARI_REASONING_EFFORT", None)
    environment.update(overrides)
    completed = subprocess.run(
        [sys.executable, "-B", str(script), str(ROOT), str(case_dir), mode],
        cwd=ROOT, env=environment, capture_output=True, text=True, encoding="utf-8", timeout=90,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(completed.stdout)


def test_authorized_override_reaches_provider_binding(case_dir: Path) -> None:
    result = run_child(case_dir, "binding", {
        "XI_KARI_PROVIDER_MODEL": "gpt-6-astra", "XI_KARI_REASONING_EFFORT": "max"
    })

    assert result["model"] == result["base_model"] == "gpt-6-astra"
    assert result["reasoning_effort"] == result["base_effort"] == "max"
    assert result["argv"][result["argv"].index("--model") + 1] == "gpt-6-astra"


@pytest.mark.parametrize(("overrides", "model", "effort"), [
    ({}, "gpt-6-astra", "max"),
    ({"XI_KARI_PROVIDER_MODEL": "gpt-6-sol"}, "gpt-6-sol", "max"),
    ({"XI_KARI_PROVIDER_MODEL": "gpt-6-astra", "XI_KARI_REASONING_EFFORT": "high"}, "gpt-6-astra", "high"),
    ({"XI_KARI_REASONING_EFFORT": ""}, "gpt-6-astra", ""),
], ids=["defaults", "model_override", "effort_override", "provider_default_effort"])
def test_override_reaches_request_fixture_receipt_and_fresh_readback(
    case_dir: Path, overrides: dict[str, str], model: str, effort: str
) -> None:
    result = run_child(case_dir, "roundtrip", overrides)

    for record in (result["request"], result["fixture_binding"], result["receipt"]):
        assert (record["model"], record["reasoning_effort"]) == (model, effort)
    assert result["verified_status"] == "executed"
    assert result["actual_model_execution"] is False
    assert result["receipt"]["binding_kind"] == "controlled_process_fixture"
    fresh = run_child(case_dir, "verify", overrides)
    assert fresh["accepted"] is True
    assert fresh["verified_status"] == "executed"
    assert fresh["actual_model_execution"] is False


@pytest.mark.parametrize("drift", [
    {"XI_KARI_PROVIDER_MODEL": "gpt-6.1-sol", "XI_KARI_REASONING_EFFORT": "max"},
    {"XI_KARI_PROVIDER_MODEL": "gpt-6-astra", "XI_KARI_REASONING_EFFORT": "high"},
], ids=["model", "effort"])
def test_new_process_rejects_configuration_drift_even_without_provider_launch(
    case_dir: Path, drift: dict[str, str]
) -> None:
    original = run_child(case_dir, "not_run", {
        "XI_KARI_PROVIDER_MODEL": "gpt-6-astra", "XI_KARI_REASONING_EFFORT": "max"
    })
    assert original["verified_status"] == "not_run"
    assert original["receipt"]["child_pid"] is None

    result = run_child(case_dir, "verify", drift)

    assert result["accepted"] is False
    assert "frozen provider configuration" in result["diagnostic"]


def test_execution_entry_accepts_override_and_launches_only_the_controlled_stub(case_dir: Path) -> None:
    result = run_child(case_dir, "entry", {
        "XI_KARI_PROVIDER_MODEL": "gpt-6-astra", "XI_KARI_REASONING_EFFORT": "high"
    })

    observed = result["entry_observation"]
    assert observed is not None, result.get("entry_stop")
    assert observed["synthetic"] is True
    assert observed["input_bytes"] > 0
    assert observed["argv"][observed["argv"].index("--model") + 1] == "gpt-6-astra"
    assert 'model_reasoning_effort="high"' in observed["argv"]
    assert result["entry_stop"].startswith("AuthoringFailure:")


def test_process_uses_authoring_configuration_frozen_before_semantic_import(case_dir: Path) -> None:
    result = run_child(case_dir, "frozen", {
        "XI_KARI_PROVIDER_MODEL": "gpt-6-astra", "XI_KARI_REASONING_EFFORT": "max"
    })

    assert (result["model"], result["reasoning_effort"]) == ("gpt-6-astra", "max")


def test_request_and_bindings_cannot_supply_their_own_model_or_effort(case_dir: Path) -> None:
    result = run_child(case_dir, "forged", {
        "XI_KARI_PROVIDER_MODEL": "gpt-6-astra", "XI_KARI_REASONING_EFFORT": "max"
    })

    attempts = result["forged_configurations"]
    assert len(attempts) == 6
    assert all(row["rejected"] and not row["launched"] for row in attempts)
    assert all(not row["run_created"] for row in attempts if row["target"] == "request")
