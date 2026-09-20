import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RULE_PARAGRAPHS = (
    392, 847, 1025, 1506, 1546, 1547, 1595, 1865, 1919, 2159,
    2622, 2720, 2744, 2768, 2818, 2869, 2872, 2898, 4618, 4626,
)


def rows(relative):
    return [json.loads(line) for line in (ROOT / relative).read_text(encoding="utf-8").splitlines()]


def census():
    return {row["candidate_id"]: row for row in rows("references/ontology/candidate-census.jsonl")}


@pytest.mark.parametrize("ordinal", RULE_PARAGRAPHS)
def test_rule_mentioning_examples_keeps_its_constraint_role_and_exact_source(ordinal):
    candidate_id = f"V83-CANDIDATE-P{ordinal:04d}"
    row = census()[candidate_id]
    source = next(item for item in rows("references/source/v8.3/indexes/candidates.jsonl")
                  if item["candidate_id"] == candidate_id)
    assert row["disposition"] == "subordinate_value"
    assert row["parent_concept_ids"]
    assert row["bound_concept_ids"] == []
    assert row["source_text"] == source["source_text"]


@pytest.mark.parametrize("ordinal", (1304, 1305, 1307, 1544, 1549))
def test_shared_prototype_contract_is_not_limited_to_one_state(ordinal):
    row = census()[f"V83-CANDIDATE-P{ordinal:04d}"]
    assert row["disposition"] == "subordinate_value"
    assert row["parent_concept_ids"] == [f"V83-CANON-S{i}" for i in range(7)]


@pytest.mark.parametrize("ordinal", (4450, 4451, 4452, 4477))
def test_appendix_shared_human_contract_covers_all_eleven_interfaces(ordinal):
    row = census()[f"V83-CANDIDATE-P{ordinal:04d}"]
    assert row["disposition"] == "subordinate_value"
    assert {f"V83-CANON-HV{i:02d}" for i in range(1, 12)} <= set(row["parent_concept_ids"])


def test_formal_human_output_limit_table_is_not_navigation():
    records = census()
    whole = records["V83-CANDIDATE-T119"]
    assert whole["disposition"] == "subordinate_value"
    assert whole["parent_concept_ids"] == [f"V83-CANON-HV{i:02d}" for i in range(1, 12)]
    assert records["V83-CANDIDATE-T119-R001"]["disposition"] == "heading_only"
    for i in range(1, 12):
        row = records[f"V83-CANDIDATE-T119-R{i+1:03d}"]
        assert row["disposition"] == "subordinate_value"
        assert row["parent_concept_ids"] == [f"V83-CANON-HV{i:02d}"]
        alias = records[f"V83-CANDIDATE-P{4453+2*i:04d}"]
        assert alias["disposition"] == "alias"
        assert alias["parent_concept_ids"] == row["parent_concept_ids"]


def test_table_column_headers_cannot_be_promoted_by_shared_anchors_or_example_words():
    headers = [row for row in census().values()
               if row["source_unit_type"] == "paragraph" and row["source_style"] == "TableHead"]
    assert headers
    assert {row["disposition"] for row in headers} == {"heading_only"}
    assert all(not row["bound_concept_ids"] and not row["parent_concept_ids"] for row in headers)


@pytest.mark.parametrize("candidate_id", ("V83-CANDIDATE-P1642", "V83-CANDIDATE-T039", "V83-CANDIDATE-T054"))
def test_actual_examples_remain_examples(candidate_id):
    assert census()[candidate_id]["disposition"] == "example_only"


def test_circle_identity_and_relation_change_are_not_intervention_or_exit_types():
    records = census()
    assert records["V83-CANDIDATE-P1760"]["parent_concept_ids"] == ["V83-CANON-CIRCLE"]
    assert set(records["V83-CANDIDATE-P1837"]["parent_concept_ids"]) == {
        "V83-CANON-CIRCLE-RELATIONS", "V83-CANON-CORE-CIRCLE-TRANSFORMATION",
    }


@pytest.mark.parametrize("number", (4, 5, 6, 7, 9, 10))
def test_numbered_protocol_dependencies_are_separate_without_rewriting_raw_source(number):
    concept = next(row for row in rows("references/ontology/inventory/human.jsonl")
                   if row["concept_id"] == f"V83-CANON-HV{number:02d}")
    assert concept["protocol_requires"] == ["EVIDENCE", "SOURCE"]
    original = concept["appendix_a_contract"]["fields"]["protocol_requires"]
    assert original == "1. EVIDENCE2. SOURCE"
    anchors = concept["appendix_a_contract"]["field_anchors"]["protocol_requires"]
    paragraphs = {row["anchor"]: row["text"] for row in rows("references/source/v8.3/audit/paragraphs.jsonl")}
    assert original == paragraphs[anchors[-1]]


def test_human_bundle_keeps_the_four_source_missing_states():
    text = (ROOT / "references/ontology/bundles/human-variable-interface-complete.md").read_text(encoding="utf-8")
    for state in ("unknown", "not_observable", "not_applicable", "withheld_for_protection"):
        assert state in text
    assert "原因" in text and "不得替代" in text
