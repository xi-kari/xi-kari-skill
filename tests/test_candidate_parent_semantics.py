"""Source-grounded regressions for shared rules and formal contract tables."""

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def census():
    return {
        row["candidate_id"]: row
        for row in map(
            json.loads,
            (ROOT / "references/ontology/candidate-census.jsonl").read_text(encoding="utf-8").splitlines(),
        )
    }


def test_prototype_review_is_shared_by_all_prototypes():
    row = census()["V83-CANDIDATE-P1306"]
    assert row["disposition"] == "subordinate_value"
    assert row["parent_concept_ids"] == [f"V83-CANON-S{i}" for i in range(7)]
    assert row["parent_card_paths"] == ["references/ontology/cards/circles-collectives/s0-s6-prototypes.md"]


def test_recursive_unknowns_are_not_human_meaning_evidence():
    row = census()["V83-CANDIDATE-P2115"]
    assert row["disposition"] == "subordinate_value"
    assert row["parent_concept_ids"] == ["V83-CANON-CORE-RECURSIVE-FUTURE"]


@pytest.mark.parametrize(
    ("table", "parent", "last_row"),
    [
        ("T047", "V83-CANON-CORE-VARIABLE-CANDIDATE", 6),
        ("T057", "V83-CANON-CORE-SEVEN-GATES", 8),
        ("T062", "V83-CANON-CORE-TOOL-BOUNDARY", 7),
    ],
)
def test_case_word_inside_formal_table_does_not_make_it_an_example(table, parent, last_row):
    rows = census()
    main = rows[f"V83-CANDIDATE-{table}"]
    assert main["disposition"] == "subordinate_value"
    assert main["parent_concept_ids"] == [parent]
    assert rows[f"V83-CANDIDATE-{table}-R001"]["disposition"] == "heading_only"
    for i in range(2, last_row + 1):
        row = rows[f"V83-CANDIDATE-{table}-R{i:03d}"]
        assert row["disposition"] == "subordinate_value"
        assert row["parent_concept_ids"] == [parent]


def test_explicit_example_tables_remain_examples():
    rows = census()
    for table in ("T039", "T054"):
        assert rows[f"V83-CANDIDATE-{table}"]["disposition"] == "example_only"
