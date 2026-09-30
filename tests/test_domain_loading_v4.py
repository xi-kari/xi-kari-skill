from copy import deepcopy
from importlib import import_module
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
IDS = tuple(f"D.{ordinal:02d}" for ordinal in range(1, 33))
PROBLEM = "1" * 64
CHALLENGE = "2" * 64


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def api():
    return import_module("xi_kari_runtime.domains")


@pytest.fixture
def repository(tmp_path):
    for relative in (
        "references/source/v9.0/source-manifest.json",
        "references/source/v9.0/indexes/anchors.json",
        "references/source/v9.0/indexes/body-blocks.json",
        "references/ontology/v9.0/authored/domain-identities.json",
    ):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    destination = tmp_path / "references/learning-packs/domains"
    shutil.copytree(ROOT / "references/learning-packs/domains", destination)
    from xi_kari_runtime.canonical_json import sha256_file
    catalog = _json(ROOT / "references/domains/index.json")
    for entry in catalog["entries"]:
        path = f"references/learning-packs/domains/{entry['domain_id']}.md"
        entry.update(content_status="available", content_path=path,
                     content_sha256=sha256_file(tmp_path / path),
                     read_trace_status="requires_run_trace")
    index = tmp_path / "references/domains/index.json"
    index.parent.mkdir(parents=True, exist_ok=True)
    index.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def plan(api, repository, ids=("D.04",)):
    return api.build_domain_read_plan(repository, domain_ids=ids,
        problem_contract_sha256=PROBLEM, run_id="run-test-domain",
        challenge=CHALLENGE)


def semantic_input(api, repository, read_plan, status="applied"):
    records = []
    for item in read_plan["records"]:
        raw = api.read_domain_item_bytes(repository, item)
        excerpt = next(line for line in raw.decode("utf-8").splitlines()
                       if line and not line.startswith("#"))
        records.append({
            "domain_id": item["domain_id"],
            "content_witness": api.domain_content_witness(read_plan, item, raw),
            "content_excerpt": excerpt,
            "problem_relation": {"status": status,
                "rationale": "本任务只检查已给观测如何支持有限结论。"},
            "reader_responsibilities": {
                "native_method": "原生方法已经回答当前观测任务。",
                "additional_distinction": "目标状态可观测并不等于全部状态已经重建。",
                "inputs_outputs": "观测支持有限输出，其余状态保持未知。",
                "limits_counterargument": "同一输出仍可能对应多个隐藏状态。",
                "costs_exit": "追加全状态重建会增加成本，可以在目标任务完成时退出。",
            },
        })
    return records


def reader_text(records):
    return "\n\n".join(value for record in records
                         for value in record["reader_responsibilities"].values())


@pytest.mark.parametrize("domain_id", IDS)
def test_each_domain_has_real_readable_product(domain_id):
    path = ROOT / f"references/learning-packs/domains/{domain_id}.md"
    assert path.is_file(), f"No actual domain content: {domain_id}"
    assert path.read_text(encoding="utf-8").startswith(f"# {domain_id} ")


@pytest.mark.parametrize("domain_id", IDS)
def test_each_domain_loads_exact_bytes_and_p03_source_binding(api, repository, domain_id):
    read_plan = plan(api, repository, (domain_id,))
    record = read_plan["records"][0]
    assert record["domain_id"] == domain_id
    assert record["identity_id"] == "V90-DOMAIN-" + domain_id.replace(".", "")
    assert api.read_domain_item_bytes(repository, record) == (repository / record["path"]).read_bytes()
    assert record["source_anchors"]
    assert record["source_fingerprint_sha256"]
    assert len(read_plan["records"]) == 1


def test_native_exit_preserves_reader_work_without_formal_upgrade(api, repository):
    read_plan = plan(api, repository)
    records = semantic_input(api, repository, read_plan, "native_exit")
    trace = api.build_domain_read_trace(repository, read_plan, records)
    text = reader_text(records)
    api.validate_domain_read_trace(repository, read_plan, trace, reader_text=text)
    delivery = api.domain_reader_records(trace)
    assert delivery[0]["problem_relation"]["status"] == "native_exit"
    assert delivery[0]["reader_responsibilities"]["costs_exit"] in text
    assert "content_sha256" not in delivery[0]
    assert "formal_qualification" not in delivery[0]
    assert "source_fingerprint_sha256" not in delivery[0]


def test_receipt_requires_bytes_witness_and_content_excerpt(api, repository):
    read_plan = plan(api, repository)
    records = semantic_input(api, repository, read_plan)
    records[0]["content_witness"] = "0" * 64
    with pytest.raises(api.DomainReadError, match="witness"):
        api.build_domain_read_trace(repository, read_plan, records)
    records = semantic_input(api, repository, read_plan)
    records[0]["content_excerpt"] = "UNREAD FILE EXISTS ONLY"
    with pytest.raises(api.DomainReadError, match="excerpt"):
        api.build_domain_read_trace(repository, read_plan, records)


def test_consumed_content_mutation_invalidates_old_plan_trace_and_authority(api, repository):
    read_plan = plan(api, repository)
    records = semantic_input(api, repository, read_plan)
    trace = api.build_domain_read_trace(repository, read_plan, records)
    binding = api.domain_authority_binding(repository, read_plan)
    api.validate_domain_read_trace(repository, read_plan, trace, reader_text=reader_text(records))
    path = repository / read_plan["records"][0]["path"]
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(api.DomainReadError, match="content"):
        api.validate_domain_read_trace(repository, read_plan, trace)
    with pytest.raises(api.DomainReadError, match="content"):
        api.validate_domain_authority(repository, read_plan, binding)


def test_unselected_missing_domain_does_not_force_all_domains(api, repository):
    (repository / "references/learning-packs/domains/D.32.md").unlink()
    read_plan = plan(api, repository, ("D.04",))
    assert len(read_plan["records"]) == 1
    with pytest.raises(api.DomainReadError, match="file|path|content"):
        plan(api, repository, ("D.32",))


@pytest.mark.parametrize("ids", [("D.04", "D.04"), ("D.00",), ("D.33",), ("01.01",)])
def test_routing_rejects_duplicate_unknown_or_research_topic_ids(api, repository, ids):
    with pytest.raises(api.DomainReadError):
        plan(api, repository, ids)


def test_empty_domain_route_is_legitimate(api, repository):
    read_plan = plan(api, repository, ())
    trace = api.build_domain_read_trace(repository, read_plan, [])
    assert trace["records"] == []
    api.validate_domain_read_trace(repository, read_plan, trace, reader_text="原生方法回答问题。")


def test_domain_source_identity_cannot_be_replaced_by_topic_or_title(api, repository):
    path = repository / "references/domains/index.json"
    catalog = _json(path)
    catalog["entries"][3]["primary_candidate_id"] = "01.01"
    path.write_text(json.dumps(catalog), encoding="utf-8")
    with pytest.raises(api.DomainReadError, match="source|identity"):
        plan(api, repository)


@pytest.mark.parametrize("unsafe", ["../outside.md", "/outside.md", "C:/outside.md",
    "references/learning-packs/domains/../D.04.md", "references\\learning-packs\\domains\\D.04.md"])
def test_index_path_escape_is_rejected_before_read(api, repository, unsafe):
    path = repository / "references/domains/index.json"
    catalog = _json(path)
    catalog["entries"][3]["content_path"] = unsafe
    path.write_text(json.dumps(catalog), encoding="utf-8")
    with pytest.raises(api.DomainReadError, match="path"):
        plan(api, repository)


def test_source_index_mutation_rejects_binding(api, repository):
    path = repository / "references/source/v9.0/indexes/body-blocks.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(api.DomainReadError, match="source"):
        plan(api, repository)


def test_old_problem_or_run_witness_cannot_be_replayed(api, repository):
    original = plan(api, repository)
    records = semantic_input(api, repository, original)
    new_plan = api.build_domain_read_plan(repository, domain_ids=("D.04",),
        problem_contract_sha256="3" * 64, run_id="different-run", challenge=CHALLENGE)
    with pytest.raises(api.DomainReadError, match="witness"):
        api.build_domain_read_trace(repository, new_plan, records)


def test_model_cannot_write_control_or_formal_qualification_fields(api, repository):
    read_plan = plan(api, repository)
    records = semantic_input(api, repository, read_plan)
    records[0]["formal_qualification"] = "G3"
    with pytest.raises(api.DomainReadError, match="fields"):
        api.build_domain_read_trace(repository, read_plan, records)
    records = semantic_input(api, repository, read_plan)
    records[0]["content_sha256"] = "0" * 64
    with pytest.raises(api.DomainReadError, match="fields"):
        api.build_domain_read_trace(repository, read_plan, records)


def test_reader_omission_cannot_be_called_delivery(api, repository):
    read_plan = plan(api, repository)
    records = semantic_input(api, repository, read_plan)
    trace = api.build_domain_read_trace(repository, read_plan, records)
    with pytest.raises(api.DomainReadError, match="reader"):
        api.validate_domain_read_trace(repository, read_plan, trace, reader_text="只有结论。")


def test_tampered_trace_control_cannot_be_rehashed_into_validity(api, repository):
    from xi_kari_runtime.canonical_json import sha256_json
    read_plan = plan(api, repository)
    records = semantic_input(api, repository, read_plan)
    trace = api.build_domain_read_trace(repository, read_plan, records)
    changed = deepcopy(trace)
    changed["records"][0]["source_fingerprint_sha256"] = "0" * 64
    changed["trace_sha256"] = sha256_json({k: v for k, v in changed.items() if k != "trace_sha256"})
    with pytest.raises(api.DomainReadError, match="binding"):
        api.validate_domain_read_trace(repository, read_plan, changed)


def test_symlinked_domain_is_rejected(api, repository, tmp_path):
    path = repository / "references/learning-packs/domains/D.04.md"
    outside = tmp_path / "outside-domain.md"
    outside.write_bytes(path.read_bytes())
    path.unlink()
    try:
        path.symlink_to(outside)
    except OSError:
        pytest.skip("Host does not allow filesystem symlink creation")
    with pytest.raises(api.DomainReadError, match="path|symlink"):
        plan(api, repository)


def test_directory_junction_is_rejected_on_windows(api, repository):
    import base64
    import os
    import subprocess
    if os.name != "nt":
        pytest.skip("Windows junction case is platform-specific")
    path = repository / "references/learning-packs/domains"
    outside = repository.parent / (repository.name + "_junction_target")
    assert outside.resolve().is_relative_to(repository.parent.resolve())
    assert not outside.exists()
    path.rename(outside)
    command = "New-Item -ItemType Junction -Path '" + str(path).replace("'", "''") + "' -Target '" + str(outside).replace("'", "''") + "' | Out-Null"
    encoded = base64.b64encode(command.encode("utf-16-le")).decode("ascii")
    completed = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive",
        "-EncodedCommand", encoded], cwd=repository, capture_output=True, text=True)
    assert completed.returncode == 0, "Host junction creation failed"
    with pytest.raises(api.DomainReadError, match="path|junction"):
        plan(api, repository)


def test_updated_catalog_cannot_validate_old_content_binding(api, repository):
    from xi_kari_runtime.canonical_json import sha256_file
    read_plan = plan(api, repository)
    binding = api.domain_authority_binding(repository, read_plan)
    content = repository / read_plan["records"][0]["path"]
    content.write_bytes(content.read_bytes() + b" ")
    index_path = repository / "references/domains/index.json"
    index = _json(index_path)
    index["entries"][3]["content_sha256"] = sha256_file(content)
    index_path.write_text(json.dumps(index), encoding="utf-8")
    with pytest.raises(api.DomainReadError, match="binding"):
        api.validate_domain_authority(repository, read_plan, binding)


def test_trace_rejects_omitted_selected_domain(api, repository):
    read_plan = plan(api, repository, ("D.04", "D.08"))
    records = semantic_input(api, repository, read_plan)
    with pytest.raises(api.DomainReadError, match="coverage"):
        api.build_domain_read_trace(repository, read_plan, records[:1])


def save_domain_run(api, repository, run_dir, read_plan, records, text):
    run_dir.mkdir()
    trace = api.build_domain_read_trace(repository, read_plan, records)
    binding = api.domain_authority_binding(repository, read_plan)
    for filename, value in (("domain-read-plan.json", read_plan),
        ("domain-read-trace.json", trace), ("domain-authority.json", binding)):
        (run_dir / filename).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    (run_dir / "xi-kari-answer.md").write_bytes(text.encode("utf-8"))
    return trace


@pytest.mark.parametrize("domain_id", IDS)
def test_every_domain_preserves_specific_content_through_disk_reader_delivery(api, repository, domain_id):
    read_plan = plan(api, repository, (domain_id,))
    item = read_plan["records"][0]
    raw = api.read_domain_item_bytes(repository, item)
    text = raw.decode("utf-8")
    sections = text.replace("\r\n", "\n").split("\n## ")
    records = [{"domain_id": domain_id,
        "content_witness": api.domain_content_witness(read_plan, item, raw),
        "content_excerpt": next(line for line in text.splitlines() if line and not line.startswith("#")),
        "problem_relation": {"status": "boundary_only",
            "rationale": "本工程用例审查" + text.splitlines()[0][2:] + "的原生方法、限制和退出如何进入读者正文。"},
        "reader_responsibilities": {
            "native_method": sections[1], "additional_distinction": sections[2],
            "inputs_outputs": sections[2], "limits_counterargument": sections[-1],
            "costs_exit": sections[-1]},}]
    run_dir = repository.parent / (repository.name + "_run")
    save_domain_run(api, repository, run_dir, read_plan, records, text)
    result = api.validate_domain_run(repository, run_dir,
        problem_contract_sha256=PROBLEM, run_id="run-test-domain")
    assert result["domain_ids"] == [domain_id]
    assert (run_dir / "xi-kari-answer.md").read_bytes() == raw
    (run_dir / "xi-kari-answer.md").write_text(sections[0], encoding="utf-8")
    with pytest.raises(api.DomainReadError, match="reader"):
        api.validate_domain_run(repository, run_dir,
            problem_contract_sha256=PROBLEM, run_id="run-test-domain")


def test_disk_validator_rejects_wrong_problem_and_in_repository_run(api, repository):
    read_plan = plan(api, repository)
    records = semantic_input(api, repository, read_plan)
    run_dir = repository.parent / (repository.name + "_run")
    save_domain_run(api, repository, run_dir, read_plan, records, reader_text(records))
    with pytest.raises(api.DomainReadError, match="problem"):
        api.validate_domain_run(repository, run_dir,
            problem_contract_sha256="9" * 64, run_id="run-test-domain")
    with pytest.raises(api.DomainReadError, match="outside"):
        api.validate_domain_run(repository, repository,
            problem_contract_sha256=PROBLEM, run_id="run-test-domain")


def test_disk_validator_rejects_content_change_on_fresh_process(api, repository):
    import os
    import subprocess
    read_plan = plan(api, repository)
    records = semantic_input(api, repository, read_plan)
    run_dir = repository.parent / (repository.name + "_run")
    save_domain_run(api, repository, run_dir, read_plan, records, reader_text(records))
    command = [sys.executable, "-B", "-c",
        "from pathlib import Path; import sys; from xi_kari_runtime.domains import validate_domain_run; "
        "validate_domain_run(Path(sys.argv[1]), Path(sys.argv[2]), problem_contract_sha256=sys.argv[3], run_id=sys.argv[4])",
        str(repository), str(run_dir), PROBLEM, "run-test-domain"]
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "scripts"), PYTHONDONTWRITEBYTECODE="1")
    before = subprocess.run(command, cwd=repository, env=environment, capture_output=True, text=True)
    assert before.returncode == 0, before.stderr
    path = repository / read_plan["records"][0]["path"]
    path.write_bytes(path.read_bytes() + b" ")
    after = subprocess.run(command, cwd=repository, env=environment, capture_output=True, text=True)
    assert after.returncode != 0
    assert "content hash" in after.stderr


def test_reader_line_ending_rendering_does_not_change_semantic_binding(api, repository):
    read_plan = plan(api, repository)
    records = semantic_input(api, repository, read_plan)
    records[0]["reader_responsibilities"]["limits_counterargument"] = "目标输出可观测。\n全状态重建仍未成立。"
    trace = api.build_domain_read_trace(repository, read_plan, records)
    api.validate_domain_read_trace(repository, read_plan, trace,
        reader_text=reader_text(records).replace("\n", "\r\n"))


@pytest.mark.parametrize("domain_id", ("D.01", "D.09"))
def test_product_git_filters_preserve_exact_reviewed_domain_bytes(domain_id):
    import subprocess
    relative = f"references/learning-packs/domains/{domain_id}.md"
    raw = subprocess.check_output(["git", "hash-object", "--no-filters", relative], cwd=ROOT, text=True).strip()
    filtered = subprocess.check_output(["git", "hash-object", "--path=" + relative, relative], cwd=ROOT, text=True).strip()
    assert raw == filtered, "Git newline filters would change reviewed content bytes and break the domain binding"
