"""Deterministic process fixtures, never real P14 model or grader observations."""

from importlib import import_module
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SEED = "xikari-p14-holdout-v1-20260930"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def api():
    return import_module("xi_kari_runtime.evaluation_v4")


@pytest.fixture
def preparation(tmp_path):
    root = tmp_path / "public-preparation"
    root.mkdir()
    requirement = dict(model="gpt-6.1-sol", reasoning_effort="max", fact_scope="closed-input",
        network="disabled", requested_max_output_tokens=6000, author_turns=1, substitution_allowed=False)
    tasks = dict(schema="xikari-p14-evaluation-tasks/1", actual_model_runs=0,
        author_model_requirement=requirement, debug_tasks=[], holdout_tasks=[],
        sampling_rule=dict(infrastructure_retries=1, semantic_retries=0, responses_per_task_arm=1))
    for split, ids in (("debug_tasks", ["D01", "D02"]), ("holdout_tasks", [f"H{i:02d}" for i in range(1, 7)])):
        for task_id in ids:
            prefix = "author-inputs/" + task_id
            row = dict(id=task_id, slug=task_id, prompt=prefix + "/task.md",
                author_materials=[prefix + "/sources.txt"], source_ids=["FIXTURE-" + task_id],
                evidence_cutoff="2026-09-30", primary_dimensions=["evidence_fidelity"])
            tasks[split].append(row)
            for name, text in (("task.md", "Synthetic process fixture; not an actual held-out task."),
                               ("sources.txt", "Synthetic fixture source; no evaluation answer.")):
                path = root / prefix / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
    assignments = [dict(zip([f"H{i:02d}" for i in range(1, 7)], arms))
                   for arms in ("SONSON", "ON SNSO".replace(" ", ""), "NSOONS")]
    passes = [dict(pass_index=i, arms=arms, task_order=sorted(arms,
        key=lambda task_id: digest(f"{SEED}|{i}|{task_id}".encode()))) for i, arms in enumerate(assignments, 1)]
    for row in passes:
        row["pass"] = row.pop("pass_index")
    tasks["execution_schedule"] = dict(seed=SEED, arm_codes=dict(S="simple", O="old_v8_3", N="new_v9_0"), passes=passes)
    save(root / "tasks.json", tasks)
    save(root / "arm-execution-config.json", dict(arms={arm: requirement for arm in "SON"}, actual_model_runs=0))
    save(root / "sources-manifest.json", dict(sources=[]))
    for relative in ("protocol.md", "arm-contexts/common-author-instructions.md", "arm-contexts/simple-method.md"):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Frozen synthetic fixture; no real P14 evaluation.", encoding="utf-8")
    poison = root / "grader-only/never-read.txt"
    poison.parent.mkdir()
    poison.write_text("FORBIDDEN TEST CANARY", encoding="utf-8")
    files = [dict(path=path.relative_to(root).as_posix(), bytes=len(path.read_bytes()), sha256=digest(path.read_bytes()))
             for path in root.rglob("*") if path.is_file()]
    save(root / "FROZEN-MANIFEST.json", dict(schema="xikari.p14-frozen-manifest/1", files=files))
    control = [row for row in files if not row["path"].startswith("author-inputs/")]
    manifest_raw = (root / "FROZEN-MANIFEST.json").read_bytes()
    control.append(dict(path="FROZEN-MANIFEST.json", bytes=len(manifest_raw), sha256=digest(manifest_raw)))
    save(root / "READY.json", dict(preparation_ready=True, actual_model_runs=0, actual_grader_runs=0,
        control_files=control, old_arm_predeclared_identity={}, new_arm_required_identity={}))
    return root


@pytest.fixture
def packages(tmp_path):
    result = {}
    for arm in "ON":
        root = tmp_path / ("package-repository-" + arm)
        root.mkdir()
        for relative, raw in (("SKILL.md", b"Synthetic package fixture"), ("source.txt", arm.encode()),
                              ("schemas/example.json", b"{}")):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        for arguments in (["init", "-q"], ["config", "user.name", "Fixture"],
                          ["config", "user.email", "fixture@example.invalid"], ["add", "."], ["commit", "-qm", "fixture"]):
            subprocess.run(["git", *arguments], cwd=root, check=True, capture_output=True)
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=root, text=True).strip()
        archive = tmp_path / ("package-" + arm + ".zip")
        with zipfile.ZipFile(archive, "w") as bundle:
            for relative in ("SKILL.md", "source.txt", "schemas/example.json"):
                bundle.write(root / relative, relative)
        result[arm] = dict(repository_root=str(root), commit=commit, git_tree=tree,
            package_path=str(archive), package_sha256=digest(archive.read_bytes()),
            source_path="source.txt", source_sha256=digest((root / "source.txt").read_bytes()),
            schema_versions={"example": 4})
    receipt = tmp_path / "synthetic-p13-receipt.json"
    save(receipt, dict(accepted=True, candidate_commit=result["N"]["commit"], git_tree=result["N"]["git_tree"],
        package_sha256=result["N"]["package_sha256"], source_sha256=result["N"]["source_sha256"],
        schema_versions=result["N"]["schema_versions"], fixture_only=True))
    result["N"]["p13_receipt"] = dict(path=str(receipt), sha256=digest(receipt.read_bytes()))
    return result


def profile():
    return dict(kind="deterministic_fixture", executable=sys.executable, model="gpt-6.1-sol", reasoning_effort="max")


def prepare(api, preparation, tmp_path, packages=None):
    root = tmp_path / "evaluation-run"
    api.prepare_evaluation(preparation, root, repository_root=ROOT, package_descriptors=packages,
        execution_profile=profile(), fixture_mode=True)
    return root


def fixture_executor(api, behavior="completed", *, token_count=20, model="gpt-6.1-sol"):
    def execute(request):
        metadata = dict(type="runner.observed", model=model, reasoning_effort="max", provider="fixture",
            generation_started=behavior != "before_generation", finish_reason="length" if behavior == "truncated" else "stop")
        events = [metadata]
        if behavior == "before_generation":
            events += [dict(type="turn.failed", error=dict(message="Synthetic infrastructure failure"),
                usage=dict(input_tokens=0, output_tokens=0))]
        else:
            events += [dict(type="item.completed", item=dict(type="agent_message", text="合成夹具输出；没有真实模型或评测结论。")),
                dict(type="turn.completed", usage=dict(input_tokens=100, output_tokens=token_count, cached_input_tokens=0))]
        program = "import json,sys;sys.stdin.buffer.read();events=json.loads(sys.argv[1]);[print(json.dumps(e,ensure_ascii=False),flush=True) for e in events];sys.exit(int(sys.argv[2]))"
        request = dict(request, argv=[sys.executable, "-B", "-c", program, json.dumps(events),
            "2" if behavior == "before_generation" else "0"])
        return api.execute_process(request)
    return execute


def test_frozen_public_plan_has_18_holdout_and_6_debug_cells_without_reading_grader(api, preparation, tmp_path, monkeypatch):
    original = Path.read_bytes
    def guarded(path):
        assert "grader-only" not in path.parts, "Runner attempted a grader-only read"
        return original(path)
    monkeypatch.setattr(Path, "read_bytes", guarded)
    run = prepare(api, preparation, tmp_path)
    plan = read(run / "controller/plan.json")
    assert len([row for row in plan["cells"] if row["split"] == "holdout"]) == 18
    assert len([row for row in plan["cells"] if row["split"] == "debug"]) == 6
    assert plan["fixture_only"] is True
    assert all(row["status"] == "not_run" for row in plan["cells"])
    assert not any("grader-only" in str(path) for path in (run / "trials").rglob("*"))


def test_real_process_fixtures_freeze_actual_output_receipts_and_cannot_complete_p14(api, preparation, packages, tmp_path):
    run = prepare(api, preparation, tmp_path, packages)
    result = api.run_evaluation(run, split="debug", execute=fixture_executor(api))
    assert result["author_process_launches"] == 6
    assert result["actual_model_runs"] == 0
    assert result["p14_complete"] is False
    assert all(row["status"] == "completed" for row in result["cells"] if row["split"] == "debug")
    assert all(row["status"] == "not_run" for row in result["cells"] if row["split"] == "holdout")
    receipt = read(run / result["cells"][0]["receipt_path"])
    assert receipt["attempts"][0]["process"]["pid"] > 0
    assert receipt["attempts"][0]["usage"]["input_tokens"] == 100
    assert receipt["attempts"][0]["usage"]["output_tokens"] == 20
    assert receipt["requested_budget"]["max_output_tokens"] == 6000
    assert receipt["input_receipt"]["task_sha256"]
    assert api.audit_evaluation(run)["integrity_passed"] is True


def test_missing_p13_package_blocks_all_author_launches(api, preparation, tmp_path):
    run = prepare(api, preparation, tmp_path)
    def forbidden(request):
        raise AssertionError("P13 absence must prevent process launch")
    result = api.run_evaluation(run, split="holdout", execute=forbidden)
    assert result["author_process_launches"] == 0
    assert result["actual_model_runs"] == 0
    assert all(row["status"] == "not_run" for row in result["cells"])


def test_changed_frozen_inputs_fail_before_process_launch(api, preparation, packages, tmp_path):
    run = prepare(api, preparation, tmp_path, packages)
    path = next((run / "trials").glob("*/workspace/task.md"))
    path.write_bytes(path.read_bytes() + b" changed")
    with pytest.raises(api.EvaluationError, match="input|frozen"):
        api.run_evaluation(run, split="debug", execute=fixture_executor(api))


def test_infrastructure_retry_only_before_confirmed_zero_generation(api, preparation, packages, tmp_path):
    run = prepare(api, preparation, tmp_path, packages)
    result = api.run_evaluation(run, split="debug", execute=fixture_executor(api, "before_generation"))
    assert result["author_process_launches"] == 12
    assert all(row["status"] == "provider_error_before_generation" for row in result["cells"] if row["split"] == "debug")
    resumed = api.run_evaluation(run, split="debug", execute=lambda request: pytest.fail("Failure must not be erased"))
    assert resumed == result


def test_truncation_and_model_mismatch_are_preserved_without_semantic_retry(api, preparation, packages, tmp_path):
    run = prepare(api, preparation, tmp_path, packages)
    result = api.run_evaluation(run, split="debug", execute=fixture_executor(api, "truncated", token_count=6001, model="different-model"))
    assert result["author_process_launches"] == 6
    rows = [row for row in result["cells"] if row["split"] == "debug"]
    assert all(row["status"] == "incomplete_truncated" for row in rows)
    assert all(row["comparability"] == "notComparable" for row in rows)
    assert all("model_mismatch" in row["comparison_issues"] for row in rows)


def test_opaque_grader_export_has_no_arm_map_or_provider_trace(api, preparation, packages, tmp_path):
    run = prepare(api, preparation, tmp_path, packages)
    api.run_evaluation(run, split="debug", execute=fixture_executor(api))
    grader = tmp_path / "independent-grader"
    result = api.blind_evaluation(run, grader, split="debug")
    assert len(result["outputs"]) == 6
    assert result["fixture_only"] is True
    manifest_text = (grader / "manifest.json").read_text(encoding="utf-8")
    assert "package-repository" not in manifest_text
    assert "arm" not in manifest_text
    assert not (grader / "blinding-map.json").exists()
    for row in result["outputs"]:
        assert len(row["opaque_id"]) >= 16
        assert (grader / row["answer_path"]).is_file()
    assert (run / "controller/blinding-map-debug.json").is_file()
    assert api.audit_evaluation(run)["integrity_passed"] is True
    assert len(result["public_tasks"]) == 2
    manifest = read(grader / "manifest.json")
    exported_source = grader / manifest["public_tasks"][0]["files"][1]["path"]
    exported_source.write_text("tampered", encoding="utf-8")
    with pytest.raises(api.EvaluationError, match="grader public source"):
        api.audit_evaluation(run)


def test_output_mutation_invalidates_fresh_disk_audit(api, preparation, packages, tmp_path):
    run = prepare(api, preparation, tmp_path, packages)
    result = api.run_evaluation(run, split="debug", execute=fixture_executor(api))
    path = run / result["cells"][0]["answer_path"]
    path.write_text("altered", encoding="utf-8")
    with pytest.raises(api.EvaluationError, match="output|frozen"):
        api.audit_evaluation(run)


def test_product_and_preparation_boundaries_reject_run_roots(api, preparation, tmp_path):
    with pytest.raises(api.EvaluationError, match="outside"):
        api.prepare_evaluation(preparation, preparation / "run", repository_root=ROOT, fixture_mode=True)
    with pytest.raises(api.EvaluationError, match="outside"):
        api.prepare_evaluation(preparation, ROOT / "forbidden-evaluation-run", repository_root=ROOT, fixture_mode=True)


def test_actual_timeout_retains_partial_process_bytes_without_retry(api, preparation, packages, tmp_path):
    run = prepare(api, preparation, tmp_path, packages)
    def timeout(request):
        program = "import json,time;print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'fixture partial output'}}),flush=True);time.sleep(10)"
        return api.execute_process(dict(request, argv=[sys.executable, "-B", "-c", program], timeout_seconds=0.5))
    result = api.run_evaluation(run, split="debug", execute=timeout)
    assert result["author_process_launches"] == 6
    for cell in result["cells"]:
        if cell["split"] == "debug":
            assert cell["status"] == "timeout_after_generation"
            receipt = read(run / cell["receipt_path"])
            assert len(receipt["attempts"]) == 1
            assert receipt["attempts"][0]["process"]["timed_out"] is True
            assert (run / cell["answer_path"]).read_bytes() == b"fixture partial output"
    assert result["actual_model_runs"] == 0


def test_p13_receipt_mismatch_is_not_a_marker_that_authorizes_trial(api, preparation, packages, tmp_path):
    reference = packages["N"]["p13_receipt"]
    path = Path(reference["path"])
    receipt = read(path)
    receipt["candidate_commit"] = "0" * 40
    save(path, receipt)
    reference["sha256"] = digest(path.read_bytes())
    run = prepare(api, preparation, tmp_path, packages)
    result = api.run_evaluation(run, split="debug", execute=lambda request: pytest.fail("P13 identity mismatch"))
    assert result["author_process_launches"] == 0
    assert any("P13 receipt differs" in issue for issue in read(run / "controller/plan.json")["launch_blockers"])


def test_unavailable_exact_model_stops_all_remaining_cells_and_has_no_substitution(api, preparation, packages, tmp_path):
    run = prepare(api, preparation, tmp_path, packages)
    def unavailable(request):
        program = "import json;print(json.dumps({'type':'error','message':'model_not_found'}));print(json.dumps({'type':'turn.failed','error':{'message':'model_not_found'}}))"
        return api.execute_process(dict(request, argv=[sys.executable, "-B", "-c", program]))
    result = api.run_evaluation(run, split="debug", execute=unavailable)
    assert result["author_process_launches"] == 1
    assert all(row["status"] == "not_run" for row in result["cells"])
    assert all("exact_model_effort_unavailable" in row["comparison_issues"] for row in result["cells"])
    resumed = api.run_evaluation(run, split="holdout", execute=lambda request: pytest.fail("Cannot substitute or retry unavailable model"))
    assert resumed == result


def test_instruction_output_mentioning_private_boundary_is_not_reported_as_secret_access(api, preparation, packages, tmp_path):
    run = prepare(api, preparation, tmp_path, packages)
    def instruction_read(request):
        events = [dict(type="runner.observed", model="gpt-6.1-sol", reasoning_effort="max", provider="fixture", generation_started=True),
            dict(type="item.completed", item=dict(id="command", type="command_execution", command="cat instructions.md", exit_code=0,
                aggregated_output="You must not read any path under grader-only/")),
            dict(type="item.completed", item=dict(id="answer", type="agent_message", text="Synthetic fixture output")),
            dict(type="turn.completed", usage=dict(input_tokens=100, output_tokens=20))]
        program = "import json,sys;[print(json.dumps(e)) for e in json.loads(sys.argv[1])]"
        return api.execute_process(dict(request, argv=[sys.executable, "-B", "-c", program, json.dumps(events)]))
    result = api.run_evaluation(run, split="debug", execute=instruction_read)
    assert all(row["comparability"] == "comparable" for row in result["cells"] if row["split"] == "debug")
    receipt = read(run / result["cells"][0]["receipt_path"])
    assert receipt["attempts"][0]["grader_path_reference_detected"] is False
    assert receipt["attempts"][0]["grader_only_access_detected"] is None


def test_new_cli_help_is_read_only(tmp_path):
    script = ROOT / "scripts/evaluate_xi_kari_v4.py"
    result = subprocess.run([sys.executable, "-B", str(script), "--help"], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "prepare" in result.stdout and "blind" in result.stdout
    assert list(tmp_path.iterdir()) == []
