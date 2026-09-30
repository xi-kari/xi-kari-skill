from importlib import import_module
from hashlib import sha256
from pathlib import Path
import json
import shutil
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
TERMINAL_DISPOSITIONS = {"canonical", "alias", "subordinate_value", "out_of_scope"}
DEPENDENCY_ROLES = {
    "inferential_requires",
    "protocol_requires",
    "specializes",
    "applies_to",
    "input_dependencies",
}


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _tree_digest(path: Path) -> str:
    digest = sha256()
    for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _expected_source_ids() -> set[str]:
    return {
        *(f"D{ordinal}" for ordinal in range(4)),
        *(f"U{ordinal:02d}" for ordinal in range(1, 12)),
        *(f"G{ordinal}" for ordinal in range(1, 5)),
        *(f"E{ordinal}" for ordinal in range(1, 6)),
        *(f"C{ordinal}" for ordinal in range(1, 13)),
        "CM-FEEDBACK",
        "CM-LEARNING",
        "CM-MAINTENANCE",
        "CM-LOAD",
        "CM-PHASE",
        "CM-SELECTION",
        *(f"scale_axis:{value}" for value in "AXTOCRINJ"),
        *(f"scale_operator:M{ordinal:02d}" for ordinal in range(1, 10)),
        *(f"H{ordinal}" for ordinal in range(1, 7)),
        *(f"human_strong_type:{value}" for value in ("GC", "GS", "GE", "CV", "RS", "IS", "IM", "IB")),
        *(f"human_variable:HV{ordinal:02d}" for ordinal in range(1, 12)),
        *(f"S{ordinal}" for ordinal in range(7)),
        "X0",
    }


def test_explicit_knowledge_profiles_preserve_the_active_default() -> None:
    builder = import_module("build_knowledge_index")

    profile = builder.get_knowledge_profile("v9.0")
    legacy = builder.get_knowledge_profile("v8.3")

    assert builder.DEFAULT_KNOWLEDGE_SOURCE_VERSION == builder.get_knowledge_profile().source_version == "v9.0"
    assert legacy.source_version == "v8.3"
    assert profile.source_version == "v9.0"
    assert profile.source_root == "references/source/v9.0"
    assert profile.ontology_root == "references/ontology/v9.0"
    assert profile.learning_pack_root == "references/learning-packs/v9.0"


def test_v90_identity_register_preserves_exact_source_identities_and_layers() -> None:
    path = ROOT / "references" / "ontology" / "v9.0" / "authored" / "identity-register.json"
    register = _json(path)
    identities = register["identities"]

    assert register["framework_version"] == "v9.0"
    assert register["source_raw_sha256"] == "ffc45afdc288ecd268fd02e46d47318b7ddf17bf7b47605aa6c413c95398544b"
    assert register["identity_count"] == len(identities) == 93
    assert {row["source_concept_id"] for row in identities} == _expected_source_ids()
    assert len({row["concept_id"] for row in identities}) == 93
    for identity in identities:
        assert identity["source_layer"]["source_refs"]
        assert identity["source_layer"]["source_text_sha256"]
        assert identity["interpretation_layer"]["positive_boundary"]
        assert identity["interpretation_layer"]["negative_boundary"]
        assert isinstance(identity["source_undefined"], list)
        assert "ordinary learning automatic G status" not in identity["source_undefined"]
        if identity["primary_candidate_id"] is None:
            assert identity["source_concept_id"] == "human_strong_type:CV"
            assert identity["definition_source_units"] == ["V90-P01000"]
        else:
            assert identity["primary_candidate_id"].startswith("V90-CANDIDATE-")
        assert identity["card_path"].startswith("references/ontology/v9.0/cards/")


def test_v90_candidate_dispositions_are_an_exact_terminal_closure() -> None:
    source = _jsonl(ROOT / "references" / "source" / "v9.0" / "indexes" / "candidates.jsonl")
    census = _jsonl(ROOT / "references" / "ontology" / "v9.0" / "candidate-census.jsonl")
    registry = _json(ROOT / "references" / "ontology" / "v9.0" / "concept-registry.json")
    domains = _json(ROOT / "references" / "domains" / "index.json")
    valid_identity_ids = {row["concept_id"] for row in registry["concepts"]} | {
        row["identity_id"] for row in domains["entries"]
    }

    assert len(source) == len(census) == 3105
    assert [row["candidate_id"] for row in census] == [row["candidate_id"] for row in source]
    assert registry["candidate_count"] == 3105
    assert registry["unresolved_candidate_count"] == 0
    for source_row, row in zip(source, census, strict=True):
        assert row["disposition"] in TERMINAL_DISPOSITIONS
        assert row["disposition_status"] == "final"
        assert row["source_anchors"] == source_row["source_anchors"]
        assert row["source_span"] == source_row["source_span"]
        assert row["text_sha256"] == source_row["text_sha256"]
        assert row["semantic_fingerprint_sha256"] == source_row["semantic_fingerprint_sha256"]
        assert row["source_raw_sha256"] == source_row["source_raw_sha256"]
        external = row["review_basis"]["external_disposition"]
        expected_mapping = {
            "canonical_concept": "canonical",
            "structural_rule": "canonical",
            "alias": "alias",
            "subordinate_value": "subordinate_value",
            "example_only": "subordinate_value",
            "source_undefined": "subordinate_value",
            "heading_only": "out_of_scope",
        }
        assert row["disposition"] == expected_mapping[external]
        if row["disposition"] in {"canonical", "alias"}:
            assert row["bound_concept_ids"]
            assert set(row["bound_concept_ids"]) <= valid_identity_ids
        if row["disposition"] == "subordinate_value":
            assert row["parent_concept_ids"]
            assert set(row["parent_concept_ids"]) <= valid_identity_ids
        if row["disposition"] == "out_of_scope":
            assert row["out_of_scope_kind"] in {
                "navigation",
                "editorial",
                "bibliographic",
                "historical_only",
                "duplicate_source_unit",
            }


def test_v90_dependency_roles_remain_distinct_and_only_inferential_is_hard() -> None:
    graph = _json(ROOT / "references" / "ontology" / "v9.0" / "dependency-graph.json")
    edges = graph["edges"]
    hard_edges = graph["hard_inference_edges"]

    assert graph["framework_version"] == "v9.0"
    assert {edge["role"] for edge in edges} <= DEPENDENCY_ROLES
    assert hard_edges == [edge for edge in edges if edge["role"] == "inferential_requires"]
    assert all(edge["role"] == "inferential_requires" for edge in hard_edges)
    assert all(edge["from_id"] != edge["to_id"] for edge in edges)

    aliases = _json(ROOT / "references" / "ontology" / "v9.0" / "identity-aliases.json")["aliases"]
    edge_keys = {(edge["from_id"], edge["role"], edge["to_id"]) for edge in edges}
    assert (aliases["E5"], "inferential_requires", aliases["D3"]) in edge_keys
    assert (aliases["human_variable:HV05"], "specializes", aliases["H2"]) in edge_keys
    assert any(edge["role"] == "input_dependencies" for edge in edges)
    assert not any(edge["role"] == "input_dependencies" for edge in hard_edges)

    hard_graph: dict[str, set[str]] = {}
    for edge in hard_edges:
        hard_graph.setdefault(edge["from_id"], set()).add(edge["to_id"])
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise AssertionError(f"hard inference cycle at {node}")
        if node in visited:
            return
        visiting.add(node)
        for target in hard_graph.get(node, set()):
            visit(target)
        visiting.remove(node)
        visited.add(node)

    for node in hard_graph:
        visit(node)


def test_v90_domain_index_establishes_identities_without_faking_p11_content() -> None:
    index = _json(ROOT / "references" / "domains" / "index.json")
    entries = index["entries"]
    candidates = {
        row["candidate_id"]: row
        for row in _jsonl(
            ROOT / "references" / "source" / "v9.0" / "indexes" / "candidates.jsonl"
        )
    }

    assert index["framework_version"] == "v9.0"
    assert [row["domain_id"] for row in entries] == [f"D.{ordinal:02d}" for ordinal in range(1, 33)]
    assert len({row["identity_id"] for row in entries}) == 32
    assert entries[0]["source_anchors"][0] == "V90-P04075"
    assert entries[-1]["source_anchors"][0] == "V90-P04292"
    for entry in entries:
        assert entry["candidate_ids"]
        relative = f"references/learning-packs/domains/{entry['domain_id']}.md"
        raw = (ROOT / relative).read_bytes()
        assert raw.decode("utf-8").startswith(f"# {entry['domain_id']} ")
        assert entry["content_status"] == "available"
        assert entry["content_path"] == relative
        assert entry["content_sha256"] == sha256(raw).hexdigest()
        assert entry["read_trace_status"] == "requires_run_trace"
        assert not {"content_witness", "problem_relation", "reader_responsibilities", "trace_sha256"}.intersection(entry)
        assert len(entry["source_anchors"]) >= 7
        primary = candidates[entry["primary_candidate_id"]]
        assert primary["domain_id"] == entry["domain_id"]
        assert "domain_entry" in primary["candidate_kinds"]


def test_v90_migration_and_aliases_are_explicit_and_non_mechanical() -> None:
    ontology = ROOT / "references" / "ontology" / "v9.0"
    migration = _json(ontology / "concept-migration-map.json")
    aliases = _json(ontology / "identity-aliases.json")["aliases"]

    assert len(migration["preserved_identities"]) == 93
    assert migration["new_official_roots"] == []
    assert migration["new_official_scale_operators"] == []
    assert "U01-U11 with HV01-HV11" in migration["forbidden_merges"]
    assert "ordinary learning with CM-LEARNING" in migration["forbidden_merges"]
    assert "all externalities with C7" in migration["forbidden_merges"]
    assert "X0 with S7" in migration["forbidden_merges"]
    assert any(
        row["old"] == "appendix D shared core"
        and row["new"] == "appendix C shared methods"
        for row in migration["cross_document_aliases"]
    )
    assert any(
        row["old"] == "appendix C revision history" and row["new"] is None
        for row in migration["cross_document_aliases"]
    )
    assert aliases["D0"] != aliases["D.01"]
    assert not any(key.startswith(("XK9-", "V83-P", "V83-T")) for key in aliases)


def test_v90_generated_knowledge_assets_are_reproducible() -> None:
    builder = import_module("build_knowledge_index")
    assert builder.run(ROOT, check=True, source_version="v9.0") == []

    index = _json(ROOT / "references" / "ontology" / "v9.0" / "knowledge-index.json")
    assert index["framework_version"] == "v9.0"
    assert index["preserved_identity_count"] == 93
    assert index["identity_count"] >= 93
    assert index["domain_identity_count"] == 32
    assert index["candidate_count"] == 3105
    assert index["unresolved_candidate_count"] == 0
    assert index["cards"]
    assert index["bundles"]
    assert index["learning_packs"]


def test_v90_concept_authority_and_read_plan_consume_versioned_assets() -> None:
    authority = import_module("scripts.xi_kari_runtime.concept_authority")
    trace = import_module("scripts.xi_kari_runtime.ontology_read_trace")

    census, binding = authority.load_concept_authority(ROOT, source_version="v9.0")
    plan = trace.build_ontology_read_plan(
        ROOT,
        source_version="v9.0",
        run_id="p03-v90-consumer",
        problem_contract_sha256="1" * 64,
        content_access_challenge="2" * 64,
    )

    assert len(census) == binding["source_candidate_count"] == 3105
    assert binding["framework_version"] == "v9.0"
    assert plan["candidate_count"] == 3105
    assert plan["framework_version"] == "v9.0"
    assert plan["record_count"] == len(plan["records"])
    assert plan["card_count"] == binding["ontology_concept_count"]
    assert plan["learning_pack_count"] == 9
    assert any(row["kind"] == "domain_identity_index" for row in plan["records"])
    first = plan["records"][0]
    assert not trace._rationale_mentions_observation(
        f"{first['item_id']} V90-CANDIDATE-P00002 V90-P00002 {first['content_sha256']}",
        "这是一段足够长但没有被理由实际引用的可观察语义内容",
        plan_record=first,
    )


def test_v90_t119_navigation_does_not_inherit_the_v83_hv_table_parent() -> None:
    census = _jsonl(ROOT / "references" / "ontology" / "v9.0" / "candidate-census.jsonl")
    rows = [
        row
        for row in census
        if row.get("source_anchor") == "V90-T119"
        or row.get("source_table_anchor") == "V90-T119"
    ]
    assert rows
    for row in rows:
        if row["source_unit_type"] in {"table", "table_row"}:
            assert row["disposition"] == "out_of_scope"
            assert row["out_of_scope_kind"] in {"navigation", "duplicate_source_unit"}
            assert not any("HV" in value for value in row["parent_concept_ids"])


def test_v90_full_source_binding_rejects_body_anchor_tamper(tmp_path: Path) -> None:
    authority = import_module("scripts.xi_kari_runtime.concept_authority")
    repo = tmp_path / "repo"
    shutil.copytree(ROOT, repo)
    census_path = repo / "references" / "ontology" / "v9.0" / "candidate-census.jsonl"
    rows = census_path.read_text(encoding="utf-8").splitlines()
    first = json.loads(rows[0])
    first["body_anchor"] = "V90-B01952"
    rows[0] = json.dumps(first, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    census_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    registry_path = repo / "references" / "ontology" / "v9.0" / "concept-registry.json"
    registry = _json(registry_path)
    registry["candidate_census_sha256"] = sha256(census_path.read_bytes()).hexdigest()
    registry_path.write_text(
        json.dumps(registry, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="candidate census differs from source authority"):
        authority.load_concept_authority(repo, source_version="v9.0")


def test_v90_builder_check_is_read_only_and_rejects_missing_parent(
    tmp_path: Path,
) -> None:
    builder = import_module("build_knowledge_index")
    repo = tmp_path / "repo"
    shutil.copytree(ROOT, repo)
    ontology = repo / "references" / "ontology" / "v9.0"
    before = _tree_digest(ontology)
    assert builder.run(repo, check=True, source_version="v9.0") == []
    assert _tree_digest(ontology) == before

    decisions_path = ontology / "authored" / "candidate-decisions.jsonl"
    decisions = _jsonl(decisions_path)
    row = next(value for value in decisions if value["disposition"] == "subordinate_value")
    row["parent_identity_ids"] = []
    decisions_path.write_text(
        "".join(
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for value in decisions
        ),
        encoding="utf-8",
    )
    invalid_before = _tree_digest(ontology)
    errors = builder.run(repo, check=True, source_version="v9.0")
    assert any("subordinate decision has no explicit parent" in error for error in errors)
    assert _tree_digest(ontology) == invalid_before
