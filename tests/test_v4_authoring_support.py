from copy import deepcopy
from importlib import import_module
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from xi_kari_runtime import execution, authoring
from xi_kari_runtime.canonical_json import canonical_bytes
from xi_kari_runtime.concept_authority import load_concept_authority
from tests.test_v4_pipeline_e2e_fixtures import static_author_output


@pytest.fixture(scope="module")
def inputs():
    value, problem, plan, lock, events = static_author_output()
    _, authority = load_concept_authority(ROOT, source_version="v9.0")
    request = execution.build_base_authoring_request(
        run_id=plan["run_id"], mode="open-world", problem_contract=problem, repository_root=ROOT,
        source_lock=lock, read_plan=execution._read_plan(lock, run_id=plan["run_id"]),
        concept_authority=authority, privacy_contract=execution._privacy_contract(
            purpose="Synthetic program boundary verification", delivery_audience="requesting-user"),
        ontology_read_plan=plan,
        base_provider_binding=authoring.bind_base_authoring_provider(Path(sys.executable), mode="open-world", repository_root=ROOT, timeout_seconds=30),
    )
    return value, request, plan, events


def test_v4_prompt_points_to_prepared_interpreter_and_readonly_validation(inputs):
    _, request, _, _ = inputs
    prompt = execution.build_base_authoring_prompt(request).decode("utf-8")
    assert "runtime-inputs/support.json" in prompt
    assert "check_authoring_output.py" in prompt
    assert "--contract-version 4" in prompt


def test_readonly_cli_supports_explicit_v4_and_reports_its_real_schema(tmp_path):
    output = tmp_path / "semantic-output.json"
    output.write_text('{}', encoding="utf-8")
    process = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/check_authoring_output.py"),
        str(output), "--contract-version", "4"], capture_output=True, text=True, encoding="utf-8")
    assert process.returncode == 1, process.stderr
    report = json.loads(process.stdout)
    assert report["contract_version"] == 4
    assert report["schema"] == "xk-v4-base-authoring-output.schema.json"
    assert report["passed"] is False and report["runtime_sealed"] is False


def test_runtime_workspace_support_supplies_actual_python_and_no_authored_output(tmp_path, inputs):
    api = import_module("xi_kari_runtime.authoring_support_v4")
    _, request, plan, events = inputs
    binding = api.prepare_authoring_workspace_v4(tmp_path, request=request, ontology_read_plan=plan,
        source_events=events, repository_root=ROOT)
    support = json.loads((tmp_path / "runtime-inputs/support.json").read_text(encoding="utf-8"))
    assert Path(support["python_executable"]).resolve() == Path(sys.executable).resolve()
    assert support["preflight_arguments"][0] == "-B"
    assert Path(support["preflight_arguments"][1]).resolve() == ROOT / "scripts/check_authoring_output.py"
    assert not (tmp_path / "semantic-output.json").exists()
    assert not any("trace" in path.name for path in (tmp_path / "runtime-inputs").iterdir())
    api.verify_authoring_workspace_v4(tmp_path, binding)


@pytest.mark.parametrize("filename", ["ontology-read-plan.json", "authoring-context.json"])
def test_generated_support_never_exposes_item_expected_digests_or_witnesses_recursively(tmp_path, inputs, filename):
    from xi_kari_runtime.canonical_json import sha256_json
    from xi_kari_runtime.ontology_read_trace import content_access_witness
    _, request, plan, events = deepcopy(inputs)
    def strings(value):
        if isinstance(value, dict):
            return set().union(*(strings(child) for child in value.values())) if value else set()
        if isinstance(value, list):
            return set().union(*(strings(child) for child in value)) if value else set()
        return {value} if isinstance(value, str) else set()
    permitted_request_values = strings(request)
    expected = {row["content_sha256"] for row in plan["records"]} - permitted_request_values
    expected.update(content_access_witness(challenge=plan["content_access_challenge"],
        problem_contract_sha256=plan["problem_contract_sha256"], item_id=row["item_id"],
        content_sha256=row["content_sha256"]) for row in plan["records"])
    expected.update(row["source_sha256"] for row in events if row["source_sha256"] not in permitted_request_values)
    plan["records"][0]["private_validation"] = {"nested": [{"expected": next(iter(expected))}]}
    request["source_inputs"]["ontology_read_plan"]["plan_sha256"] = sha256_json(plan)
    import_module("xi_kari_runtime.authoring_support_v4").prepare_authoring_workspace_v4(tmp_path,
        request=request, ontology_read_plan=plan, source_events=events, repository_root=ROOT)
    path = tmp_path / "runtime-inputs" / filename
    visible = json.loads(path.read_text(encoding="utf-8"))
    assert not strings(visible).intersection(expected), "item-level expected answers leaked into " + filename
    for generated in (tmp_path / "runtime-inputs").glob("*.json"):
        assert not strings(json.loads(generated.read_text(encoding="utf-8"))).intersection(expected)
    locations = json.loads((tmp_path / "runtime-inputs/ontology-read-plan.json").read_text(encoding="utf-8"))
    assert [row["item_id"] for row in locations["records"]] == [row["item_id"] for row in plan["records"]]
    assert all(set(row) == {"item_id", "kind", "subject_id", "related_subject_id", "path", "disposition"} for row in locations["records"])
    context = json.loads((tmp_path / "runtime-inputs/authoring-context.json").read_text(encoding="utf-8"))
    assert set(context) == {"contract_version", "request"}


def supported_workspace(tmp_path, inputs):
    api = import_module("xi_kari_runtime.authoring_support_v4")
    value, request, plan, events = deepcopy(inputs)
    binding = api.prepare_authoring_workspace_v4(tmp_path, request=request, ontology_read_plan=plan,
        source_events=events, repository_root=ROOT)
    (tmp_path / "semantic-output.json").write_bytes(canonical_bytes(value))
    support = json.loads((tmp_path / "runtime-inputs/support.json").read_text(encoding="utf-8"))
    return value, binding, support


def run_preflight(tmp_path, support):
    return subprocess.run([support["python_executable"], *support["preflight_arguments"]],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8")


def test_actual_v4_preflight_validates_full_input_without_writing_or_sealing(tmp_path, inputs):
    _, binding, support = supported_workspace(tmp_path, inputs)
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    result = run_preflight(tmp_path, support)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["passed"] is True and report["runtime_sealed"] is False
    assert all(status == "passed" for status in report["checks"].values())
    assert before == {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    import_module("xi_kari_runtime.authoring_support_v4").verify_authoring_workspace_v4(tmp_path, binding)


@pytest.mark.parametrize("change", ["missing_read_record", "false_reference", "changed_context", "invalid_private_enum", "wrong_witness", "wrong_plan_binding", "wrong_source_binding"])
def test_v4_preflight_rejects_real_errors_without_repairing_values(tmp_path, inputs, change):
    value, _, support = supported_workspace(tmp_path, inputs)
    secret = "PRIVATE-ENUM-CONTENT-821744"
    expected_witness = value["ontology_read_trace"]["records"][0]["content_witness"]
    if change == "missing_read_record":
        value["ontology_read_trace"]["records"].pop()
    elif change == "false_reference":
        value["semantic_packet"]["answer"]["basis_refs"] = ["SOURCE-1"]
    elif change == "invalid_private_enum":
        value["semantic_packet"]["deliverable_type"] = secret
    elif change == "wrong_witness":
        value["ontology_read_trace"]["records"][0]["content_witness"] = "0" * 64
    elif change in {"wrong_plan_binding", "wrong_source_binding"}:
        from xi_kari_runtime.canonical_json import sha256_file
        context = tmp_path / support["context_path"]
        data = json.loads(context.read_text(encoding="utf-8"))
        if change == "wrong_plan_binding":
            data["request"]["source_inputs"]["ontology_read_plan"]["plan_sha256"] = "0" * 64
        else:
            data["request"]["source_inputs"]["source_lock"]["source_unit_event_sha256"] = "0" * 64
        context.write_bytes(canonical_bytes(data))
        support["preflight_arguments"][-1] = sha256_file(context)
    else:
        context = tmp_path / support["context_path"]
        context.write_bytes(context.read_bytes() + b" ")
    (tmp_path / "semantic-output.json").write_bytes(canonical_bytes(value))
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    result = run_preflight(tmp_path, support)
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert report["passed"] is False and report["errors"]
    assert report["runtime_sealed"] is False
    assert secret not in result.stdout + result.stderr
    assert expected_witness not in result.stdout + result.stderr
    assert before == {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}


def test_guide_uses_the_actual_envelope_and_runtime_fields(inputs):
    guide = import_module("xi_kari_runtime.authoring_support_v4").describe_authoring_contract_v4(ROOT)
    schema = json.loads((ROOT / "schemas/xk-v4-base-authoring-output.schema.json").read_text(encoding="utf-8"))
    assert guide["envelope"]["required"] == schema["required"]
    assert guide["envelope"]["properties"]["semantic_packet"]["required"] == schema["properties"]["semantic_packet"]["required"]
    assert "semantic_packet" not in guide
    assert "runtime_binding" in guide["runtime_owned_semantic_packet_keys"]


def test_navigation_view_supports_real_byte_reads_without_expected_digest(tmp_path, inputs):
    from xi_kari_runtime.ontology_read_trace import read_ontology_item_bytes
    _, _, support = supported_workspace(tmp_path, inputs)
    locations = json.loads((tmp_path / support["ontology_plan_path"]).read_text(encoding="utf-8"))["records"]
    for kind in ("candidate", "canonical_or_structural_card"):
        row = next(row for row in locations if row["kind"] == kind)
        assert "content_sha256" not in row
        assert read_ontology_item_bytes(ROOT, row)


def test_changed_code_owned_workspace_input_is_rejected(tmp_path, inputs):
    _, binding, _ = supported_workspace(tmp_path, inputs)
    (tmp_path / "runtime-inputs/ontology-read-plan.json").write_text('{}', encoding="utf-8")
    with pytest.raises(ValueError, match="frozen workspace input"):
        import_module("xi_kari_runtime.authoring_support_v4").verify_authoring_workspace_v4(tmp_path, binding)


def test_describe_cli_prints_utf8_schema_guidance_without_creating_files(tmp_path):
    result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/check_authoring_output.py"),
        "--describe", "--contract-version", "4"], cwd=tmp_path, capture_output=True)
    assert result.returncode == 0, result.stderr
    guide = json.loads(result.stdout.decode("utf-8"))
    assert guide["contract_version"] == 4
    assert guide["envelope"]["required"] == ["semantic_packet", "semantic_read_trace", "ontology_read_trace"]
    assert "作者" in guide["responsibilities"]["semantic_packet"]
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("mutate", [False, True])
def test_public_execute_prepares_usable_inputs_before_the_actual_author_process(tmp_path, inputs, mutate):
    observation = tmp_path / "observed.json"
    provider = tmp_path / "inspect_author_workspace.py"
    program = "#!" + str(Path(sys.executable).resolve()) + "\n"
    program += "import json,os,pathlib,subprocess,sys\n"
    program += "sys.stdin.read()\n"
    program += "root=pathlib.Path('runtime-inputs')\n"
    program += "support=json.loads((root/'support.json').read_text(encoding='utf-8'))\n"
    program += "context=json.loads((root/'authoring-context.json').read_text(encoding='utf-8'))\n"
    program += "result=subprocess.run([support['python_executable'],*support['preflight_arguments']],capture_output=True,text=True,encoding='utf-8')\n"
    program += "report=json.loads(result.stdout)\n"
    program += "locations=json.loads((root/'ontology-read-plan.json').read_text(encoding='utf-8'))\n"
    program += "observation={'pid':os.getpid(),'python':support['python_executable'],'preflight_exit':result.returncode,'preflight_contract':report['contract_version'],'runtime_sealed':report['runtime_sealed'],'source_version':context['request']['source_inputs']['source_version'],'plan_records':len(locations['records'])}\n"
    program += "pathlib.Path(" + repr(str(observation)) + ").write_text(json.dumps(observation),encoding='utf-8')\n"
    if mutate:
        program += "(root/'ontology-read-plan.json').write_text('{}',encoding='utf-8')\n"
        program += "raise SystemExit(0)\n"
    else:
        program += "raise SystemExit(19)\n"
    provider.write_text(program, encoding="utf-8", newline="\n")
    provider.chmod(0o755)
    with pytest.raises(ValueError) as caught:
        execution.execute_authored_run(tmp_path / "runs", problem_contract=inputs[1]["problem_contract"],
            repository_root=ROOT, codex_provider_executable=provider, timeout_seconds=30,
            privacy_purpose="Synthetic program boundary verification")
    observed = json.loads(observation.read_text(encoding="utf-8"))
    assert observed["pid"] > 0
    assert Path(observed["python"]).resolve() == Path(sys.executable).resolve()
    assert observed["preflight_exit"] == 1
    assert observed["preflight_contract"] == 4 and observed["runtime_sealed"] is False
    assert observed["source_version"] == "v9.0" and observed["plan_records"] == inputs[2]["record_count"]
    if mutate:
        assert "frozen workspace input" in str(caught.value)
    else:
        assert "exited with status 19" in str(caught.value)
