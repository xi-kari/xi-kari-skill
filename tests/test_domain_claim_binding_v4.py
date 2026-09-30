from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest

from tests.test_domain_loading_v4 import api, repository, plan, semantic_input, ROOT, save_domain_run, reader_text
from tests.test_p04_v4_claim_contracts import _nonmechanistic_interpretation_graph, _qualification
from xi_kari_runtime.semantic_projection import reader_projection_units, semantic_atom_paths


@pytest.fixture
def claim_repository(repository):
    shutil.copytree(ROOT / "schemas", repository / "schemas")
    for relative in (
        "references/source/v9.0/indexes/candidates.jsonl",
        "references/ontology/v9.0/candidate-census.jsonl",
        "references/ontology/v9.0/concept-disposition-ledger.jsonl",
        "references/ontology/v9.0/concept-registry.json",
        "references/ontology/v9.0/concept-relations.json",
        "references/ontology/v9.0/dependency-graph.json",
    ):
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, path)
    return repository


def inputs(api, repository, *, native_exit=False):
    read_plan = plan(api, repository)
    records = semantic_input(api, repository, read_plan, "native_exit" if native_exit else "boundary_only")
    trace = api.build_domain_read_trace(repository, read_plan, records)
    graph = _nonmechanistic_interpretation_graph()
    links = [{"domain_id": "D.04", "claim_ids": ["CLAIM-FACTUAL", "CLAIM-STRUCTURAL"],
              "use_kind": "native_exit" if native_exit else "boundary_reference",
              "rationale": "目标观测的有限解释不要求全状态重建；保留相邻但独立的解释。"}]
    return read_plan, trace, graph, links


def build(api, root, values):
    read_plan, trace, graph, links = values
    return api.build_domain_claim_links(root, read_plan, trace, graph, links)


def test_public_p04_ordinary_support_does_not_create_formal_qualification(api, claim_repository):
    values = inputs(api, claim_repository)
    before = deepcopy(values[2])
    binding = build(api, claim_repository, values)
    assert values[2] == before
    assert binding["links"][0]["claim_ids"] == ["CLAIM-FACTUAL", "CLAIM-STRUCTURAL"]
    assert all(c["formal_qualification"]["status"] == "not_requested" for c in values[2]["claims"])
    api.validate_domain_claim_links(claim_repository, values[0], values[1], values[2], binding)


def test_unqualified_formal_request_retains_independent_domain_conclusion_and_projection(api, claim_repository):
    values = inputs(api, claim_repository)
    values[2]["claims"][1]["formal_qualification"] = _qualification(requested=True)
    values[2]["claims"][1]["responsibility_refs"] = ["V90-CANON-G2"]
    binding = build(api, claim_repository, values)
    paths = {path for unit in reader_projection_units(projection_payload(values[2]))
             for path in unit["source_paths"]}
    assert "claim_mechanism_graph.claims[0].claim_basis.kind" in paths
    assert "claim_mechanism_graph.claims[1].formal_qualification.status" in paths
    assert values[2]["claims"][0]["formal_qualification"]["status"] == "not_requested"
    assert values[2]["claims"][1]["formal_qualification"]["status"] == "unqualified"
    assert binding["links"][0]["claim_ids"] == ["CLAIM-FACTUAL", "CLAIM-STRUCTURAL"]


def test_public_p04_rejects_formal_upgrade_from_loaded_domain_or_instance_template(api, claim_repository):
    values = inputs(api, claim_repository)
    values[2]["claims"][0]["formal_qualification"] = _qualification(requested=True, qualified=True)
    values[2]["claims"][0]["responsibility_refs"] = ["V90-CANON-G2"]
    with pytest.raises(api.DomainReadError, match="P04"):
        build(api, claim_repository, values)


def test_topic_number_and_domain_method_cannot_become_empirical_material(api, claim_repository):
    values = inputs(api, claim_repository)
    values[3][0]["use_kind"] = "empirical_evidence"
    with pytest.raises(api.DomainReadError, match="use"):
        build(api, claim_repository, values)
    values = inputs(api, claim_repository)
    values[3][0]["claim_ids"] = ["01.01"]
    with pytest.raises(api.DomainReadError, match="claim"):
        build(api, claim_repository, values)
    values = inputs(api, claim_repository)
    values[2]["claims"][0]["claim_basis"]["material_refs"] = ["D.04"]
    with pytest.raises(api.DomainReadError, match="P04"):
        build(api, claim_repository, values)


def test_native_exit_is_valid_in_public_p04_static_problem(api, claim_repository):
    values = inputs(api, claim_repository, native_exit=True)
    binding = build(api, claim_repository, values)
    assert binding["links"][0]["use_kind"] == "native_exit"
    assert all(row["status"] == "not_applicable" for row in values[2]["applicability"].values())
    assert values[2]["mechanisms"] == []


def test_stale_claim_graph_invalidates_old_domain_claim_links(api, claim_repository):
    values = inputs(api, claim_repository)
    binding = build(api, claim_repository, values)
    values[2]["claims"][0]["statement"] += " 界限需要重审。"
    with pytest.raises(api.DomainReadError, match="binding"):
        api.validate_domain_claim_links(claim_repository, values[0], values[1], values[2], binding)


def test_unread_domain_or_missing_domain_link_is_not_accepted(api, claim_repository):
    values = inputs(api, claim_repository)
    values[3][0]["domain_id"] = "D.08"
    with pytest.raises(api.DomainReadError, match="domain|coverage"):
        build(api, claim_repository, values)
    values = inputs(api, claim_repository)
    values[3].clear()
    with pytest.raises(api.DomainReadError, match="coverage"):
        build(api, claim_repository, values)


def projection_payload(graph):
    payload = {"claim_mechanism_graph": graph}
    payload["visibility_ledger"] = {"entries": [{
        "canonical_path": path, "classification": "public", "disclosure": "include",
        "purpose": "Domain P04 bounded projection test", "authority_refs": [],
        "protection_reason": None} for path in semantic_atom_paths(payload)]}
    return payload


def test_domain_public_contract_errors_do_not_disclose_protected_values(api, claim_repository):
    values = inputs(api, claim_repository)
    secret = "PRIVATE-DOMAIN-VALUE-MUST-STAY-OUT"
    values[2]["evidence"][0]["support_checks"]["source_exists"]["status"] = secret
    with pytest.raises(api.DomainReadError) as caught:
        build(api, claim_repository, values)
    assert secret not in str(caught.value)


def test_domain_claim_reader_projection_obeys_public_visibility_gate(api, claim_repository):
    values = inputs(api, claim_repository)
    secret = "PRIVATE-DOMAIN-STATEMENT-MUST-STAY-OUT"
    values[2]["claims"][0]["statement"] = secret
    build(api, claim_repository, values)
    payload = projection_payload(values[2])
    for entry in payload["visibility_ledger"]["entries"]:
        if entry["canonical_path"] == "claim_mechanism_graph.claims[0].statement":
            entry.update(classification="sensitive", disclosure="withhold",
                         authority_refs=["XK0-PRIVACY-CONTRACT-TEST"],
                         protection_reason="Keep the protected statement private.")
    rendered = json.dumps(reader_projection_units(payload), ensure_ascii=False)
    assert secret not in rendered


def test_p03_p04_disk_delivery_chain_is_revalidated_in_new_process(api, claim_repository):
    import os
    import subprocess
    import sys
    from tests.test_domain_loading_v4 import PROBLEM
    values = inputs(api, claim_repository)
    read_plan, trace, graph, links = values
    semantic_records = [{key: record[key] for key in api.SEMANTIC_FIELDS} for record in trace["records"]]
    prose = reader_text(semantic_records) + "\n\n" + "\n\n".join(
        fragment for unit in reader_projection_units(projection_payload(graph)) for fragment in unit["fragments"])
    run_dir = claim_repository.parent / (claim_repository.name + "_public_claim_run")
    save_domain_run(api, claim_repository, run_dir, read_plan, semantic_records, prose)
    binding = build(api, claim_repository, values)
    (run_dir / "claim-mechanism-graph.json").write_text(json.dumps(graph, ensure_ascii=False), encoding="utf-8")
    (run_dir / "domain-claim-links.json").write_text(json.dumps(binding, ensure_ascii=False), encoding="utf-8")
    command = [sys.executable, "-B", "-c",
        "from pathlib import Path; import sys; from xi_kari_runtime.domains import validate_domain_claim_run; "
        "validate_domain_claim_run(Path(sys.argv[1]), Path(sys.argv[2]), problem_contract_sha256=sys.argv[3], run_id=sys.argv[4])",
        str(claim_repository), str(run_dir), PROBLEM, "run-test-domain"]
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "scripts"), PYTHONDONTWRITEBYTECODE="1")
    valid = subprocess.run(command, cwd=claim_repository, env=environment, capture_output=True, text=True)
    assert valid.returncode == 0, valid.stderr
    graph["claims"][0]["statement"] += " Changed after receipt."
    (run_dir / "claim-mechanism-graph.json").write_text(json.dumps(graph, ensure_ascii=False), encoding="utf-8")
    invalid = subprocess.run(command, cwd=claim_repository, env=environment, capture_output=True, text=True)
    assert invalid.returncode != 0
    assert "claim-link binding" in invalid.stderr
