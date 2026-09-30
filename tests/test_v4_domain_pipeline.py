from copy import deepcopy
from importlib import import_module
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
IDS = [f"D.{number:02d}" for number in range(1, 33)]
PROBLEM = "1" * 64
RUN_ID = "domain-pipeline-test"


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def api():
    return import_module("xi_kari_runtime.domain_pipeline_v4")


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "repository"
    for relative in (
        "references/source/v9.0",
        "references/ontology/v9.0",
        "references/learning-packs/domains",
        "references/learning-packs/v9.0",
        "references/domains",
        "schemas",
    ):
        shutil.copytree(ROOT / relative, root / relative)
    return root


def _prepare(api, root, ids=("D.04", "D.09"), *, problem=PROBLEM):
    return api.prepare_domain_inputs(ids, run_id=RUN_ID,
        problem_contract_sha256=problem, repository_root=root)


def _contract(*, problem=PROBLEM, run_id=RUN_ID, mode="open-world"):
    return {"run_id": run_id, "problem_contract_sha256": problem, "mode": mode}


def _graph():
    from tests.test_p04_v4_claim_contracts import _nonmechanistic_interpretation_graph
    return _nonmechanistic_interpretation_graph()


def _author_trace(prepared, *, status="boundary_only"):
    records = []
    links = []
    for row in prepared["author_inputs"]:
        excerpt = next(line for line in row["content_utf8"].splitlines()
                       if line and not line.startswith("#"))
        records.append({"domain_id": row["domain_id"],
            "content_witness": row["content_witness"], "content_excerpt": excerpt,
            "problem_relation": {"status": status,
                "rationale": "只评估给定文本的有限解释及其原生方法边界。"},
            "reader_responsibilities": {
                "native_method": row["domain_id"] + "：领域原生文本解释回答当前问题。",
                "additional_distinction": "语义解释与经验性因果推断各需独立依据。",
                "inputs_outputs": "输入是给定段落，输出是有范围的含义解释。",
                "limits_counterargument": "上下文变化可能支持相邻但不同的解读。",
                "costs_exit": "追查上下文有成本；原生方法满足任务时可以退出。",
            }})
        links.append({"domain_id": row["domain_id"],
            "claim_ids": ["CLAIM-FACTUAL", "CLAIM-STRUCTURAL"],
            "use_kind": "native_exit" if status == "native_exit" else "boundary_reference",
            "rationale": "领域稿件提供方法与边界，不充当目标问题的经验材料。"})
    return {"records": records, "claim_links": links}


def _validate(api, root, prepared, trace, *, graph=None, contract=None, **kwargs):
    return api.validate_domain_inputs(prepared["plan"], trace,
        graph=_graph() if graph is None else graph,
        run_contract=_contract() if contract is None else contract,
        repository_root=root, **kwargs)


def _materialized(value):
    return {key: deepcopy(value[key]) for key in ("read_trace", "authority", "claim_links")}


def _save_run(path, prepared, value, graph):
    path.mkdir()
    for filename, content in (
        ("domain-read-plan.json", prepared["plan"]),
        ("domain-read-trace.json", value["read_trace"]),
        ("domain-authority.json", value["authority"]),
        ("domain-claim-links.json", value["claim_links"]),
        ("claim-mechanism-graph.json", graph),
    ):
        (path / filename).write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
    reader = "\n\n".join(text for record in value["domain_reader_records"]
        for text in record["reader_responsibilities"].values())
    (path / "xi-kari-answer.md").write_text(reader, encoding="utf-8")


def _snapshot(root):
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file()}


def test_generated_domain_index_is_available_and_schema_valid_for_actual_32_files():
    catalog = _json(ROOT / "references/domains/index.json")
    schema = _json(ROOT / "schemas/domain-index-v90.schema.json")
    Draft202012Validator(schema).validate(catalog)
    assert [row["domain_id"] for row in catalog["entries"]] == IDS
    for row in catalog["entries"]:
        path = f"references/learning-packs/domains/{row['domain_id']}.md"
        raw = (ROOT / path).read_bytes()
        assert row["content_status"] == "available"
        assert row["content_path"] == path
        assert row["content_sha256"] == hashlib.sha256(raw).hexdigest()
        assert row["read_trace_status"] == "requires_run_trace"


def test_canonical_builder_reproduces_domains_and_check_is_read_only(repository):
    from build_knowledge_index import run
    assert run(repository, check=False, source_version="v9.0") == []
    assert (repository / "references/domains/index.json").read_bytes() == (
        ROOT / "references/domains/index.json").read_bytes()
    before = _snapshot(repository)
    assert run(repository, check=True, source_version="v9.0") == []
    assert run(repository, check=True, source_version="v9.0") == []
    assert _snapshot(repository) == before
    path = repository / "references/learning-packs/domains/D.09.md"
    path.write_bytes(path.read_bytes() + b" ")
    before = _snapshot(repository)
    errors = run(repository, check=True, source_version="v9.0")
    assert any("references/domains/index.json" in error for error in errors)
    assert _snapshot(repository) == before


def test_builder_rejects_missing_domain_without_changing_generated_assets(repository):
    from build_knowledge_index import run
    (repository / "references/learning-packs/domains/D.09.md").unlink()
    before = _snapshot(repository)
    errors = run(repository, check=False, source_version="v9.0")
    assert any("D.09" in error and "content" in error for error in errors)
    assert _snapshot(repository) == before


def test_prepare_supplies_all_32_exact_bytes_and_problem_bound_witnesses(api):
    from xi_kari_runtime.domains import domain_content_witness
    prepared = _prepare(api, ROOT, IDS)
    json.dumps(prepared)
    assert [row["domain_id"] for row in prepared["author_inputs"]] == IDS
    for controlled, row in zip(prepared["plan"]["records"], prepared["author_inputs"], strict=True):
        raw = (ROOT / controlled["path"]).read_bytes()
        assert base64.b64decode(row["content_bytes_base64"], validate=True) == raw
        assert row["content_utf8"].encode("utf-8") == raw
        assert row["content_witness"] == domain_content_witness(prepared["plan"], controlled, raw)
    assert "\r\n" in prepared["author_inputs"][8]["content_utf8"]
    assert "read_trace" not in prepared


def test_validate_real_domain_route_stamps_controls_and_sanitizes_reader_records(api):
    prepared = _prepare(api, ROOT)
    authored = _author_trace(prepared)
    before = deepcopy(authored)
    graph = _graph()
    graph_before = deepcopy(graph)
    value = _validate(api, ROOT, prepared, authored, graph=graph)
    json.dumps(value)
    assert authored == before
    assert graph == graph_before
    assert value["result"]["domain_ids"] == ["D.04", "D.09"]
    assert value["claim_links"]["claim_graph_sha256"]
    for controlled, reader in zip(value["read_trace"]["records"], value["domain_reader_records"], strict=True):
        assert set(reader) == {"domain_id", "problem_relation", "reader_responsibilities"}
        assert controlled["content_sha256"] not in json.dumps(reader)
        assert controlled["content_witness"] not in json.dumps(reader)
        assert controlled["source_fingerprint_sha256"] not in json.dumps(reader)
    assert _validate(api, ROOT, prepared, _materialized(value), graph=graph) == value


def test_materialized_validator_reads_domain_prose_and_rejects_omissions(api, repository, tmp_path):
    prepared = _prepare(api, repository)
    graph = _graph()
    value = _validate(api, repository, prepared, _author_trace(prepared), graph=graph)
    run = tmp_path / "run"
    _save_run(run, prepared, value, graph)
    assert api.validate_materialized_domain_inputs(run, run_contract=_contract(),
        repository_root=repository) == value
    (run / "xi-kari-answer.md").write_text("只有结论。", encoding="utf-8")
    with pytest.raises(api.DomainReadError, match="reader"):
        api.validate_materialized_domain_inputs(run, run_contract=_contract(), repository_root=repository)


def test_fresh_process_rejects_changed_domain_bytes_after_success(api, repository, tmp_path):
    prepared = _prepare(api, repository)
    graph = _graph()
    value = _validate(api, repository, prepared, _author_trace(prepared), graph=graph)
    run = tmp_path / "run"
    _save_run(run, prepared, value, graph)
    command = [sys.executable, "-B", "-c",
        "import json,sys; from pathlib import Path; "
        "from xi_kari_runtime.domain_pipeline_v4 import validate_materialized_domain_inputs; "
        "validate_materialized_domain_inputs(Path(sys.argv[1]), repository_root=Path(sys.argv[2]), "
        "run_contract=json.loads(sys.argv[3]))", str(run), str(repository), json.dumps(_contract())]
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "scripts"), PYTHONDONTWRITEBYTECODE="1")
    before = subprocess.run(command, cwd=repository, env=environment, capture_output=True, text=True)
    assert before.returncode == 0, before.stderr
    path = repository / "references/learning-packs/domains/D.09.md"
    path.write_bytes(path.read_bytes() + b" ")
    after = subprocess.run(command, cwd=repository, env=environment, capture_output=True, text=True)
    assert after.returncode != 0
    assert "content hash" in after.stderr


def test_replayed_problem_and_run_are_rejected_at_public_pipeline(api):
    prepared = _prepare(api, ROOT)
    authored = _author_trace(prepared)
    for contract in (_contract(problem="3" * 64), _contract(run_id="other-run")):
        with pytest.raises(api.DomainReadError, match="problem|run"):
            _validate(api, ROOT, prepared, authored, contract=contract)
    changed = _prepare(api, ROOT, problem="3" * 64)
    with pytest.raises(api.DomainReadError, match="witness"):
        _validate(api, ROOT, changed, authored, contract=_contract(problem="3" * 64))


def test_author_cannot_supply_domain_control_fields(api):
    prepared = _prepare(api, ROOT)
    authored = _author_trace(prepared)
    authored["records"][0]["content_sha256"] = "0" * 64
    with pytest.raises(api.DomainReadError, match="fields"):
        _validate(api, ROOT, prepared, authored)


def test_domain_method_refs_cannot_be_laundered_into_empirical_evidence(api):
    prepared = _prepare(api, ROOT)
    authored = _author_trace(prepared)
    authored["claim_links"][0]["use_kind"] = "empirical_evidence"
    with pytest.raises(api.DomainReadError, match="use"):
        _validate(api, ROOT, prepared, authored)
    graph = _graph()
    graph["claims"][0]["claim_basis"]["material_refs"] = ["D.04"]
    with pytest.raises(api.DomainReadError, match="P04"):
        _validate(api, ROOT, prepared, _author_trace(prepared), graph=graph)


def test_fabricated_formal_registry_is_rejected_by_actual_public_graph_validator(api):
    prepared = _prepare(api, ROOT)
    with pytest.raises(api.DomainReadError, match="P04"):
        _validate(api, ROOT, prepared, _author_trace(prepared), verified_instance_results={})


def test_genuine_graph_bound_instance_registry_validates_final_qualification_and_disk_binding(api, tmp_path):
    from tests.test_p04_instance_results_v4 import requested_graph, observed_instance_inputs
    from xi_kari_runtime.formal_results import bind_formal_claim_results, rebuild_instance_registry
    from xi_kari_runtime.canonical_json import sha256_json
    inputs, audit = observed_instance_inputs(tmp_path)
    input_graph = requested_graph()
    graph = bind_formal_claim_results(input_graph, empirical_instances=inputs,
        repository_root=ROOT, temporal_audit=audit)["claim_mechanism_graph"]
    registry = rebuild_instance_registry(inputs, graph=input_graph, repository_root=ROOT, temporal_audit=audit)
    prepared = _prepare(api, ROOT, ("D.04",))
    authored = _author_trace(prepared)
    authored["claim_links"][0]["claim_ids"] = [graph["claims"][0]["claim_id"]]
    with pytest.raises(api.DomainReadError, match="P04"):
        _validate(api, ROOT, prepared, authored, graph=graph)
    value = _validate(api, ROOT, prepared, authored, graph=graph, verified_instance_results=registry)
    assert value["claim_links"]["claim_graph_sha256"] == sha256_json(graph)
    assert graph["claims"][0]["formal_qualification"]["status"] == "qualified"
    run = tmp_path / "qualified-run"
    _save_run(run, prepared, value, graph)
    assert api.validate_materialized_domain_inputs(run, run_contract=_contract(),
        repository_root=ROOT, verified_instance_results=registry) == value
    graph["evidence"][0]["evidence_identity"]["content_sha256"] = "9" * 64
    with pytest.raises(api.DomainReadError, match="P04"):
        _validate(api, ROOT, prepared, authored, graph=graph, verified_instance_results=registry)


def test_native_exit_and_empty_domain_route_need_no_fabricated_domain_reads(api):
    prepared = _prepare(api, ROOT, ("D.04",))
    value = _validate(api, ROOT, prepared, _author_trace(prepared, status="native_exit"))
    assert value["claim_links"]["links"][0]["use_kind"] == "native_exit"
    empty = _prepare(api, ROOT, ())
    value = _validate(api, ROOT, empty, _author_trace(empty))
    assert empty["author_inputs"] == []
    assert value["domain_reader_records"] == []
    assert value["result"]["domain_ids"] == []


def test_evidence_mode_is_explicit_and_materialized_binding_cannot_cross_modes(api):
    prepared = _prepare(api, ROOT)
    value = _validate(api, ROOT, prepared, _author_trace(prepared))
    contract = _contract()
    contract.pop("mode")
    with pytest.raises(api.DomainReadError, match="mode"):
        _validate(api, ROOT, prepared, _author_trace(prepared), contract=contract)
    with pytest.raises(api.DomainReadError, match="binding"):
        _validate(api, ROOT, prepared, _materialized(value), contract=_contract(mode="closed-input"))
