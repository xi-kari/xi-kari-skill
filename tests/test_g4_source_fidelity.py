import json
from pathlib import Path
import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(("concept_id", "ordinals"), [
    ("V83-CANON-CORE-G4-SCALE-CLOSURE", (661, 662, 663)),
    ("V83-CANON-CORE-FORECAST-FAILURE", (2240, 2241)),
])
def test_authoritative_definition_preserves_distinct_result_states(concept_id, ordinals):
    paragraphs = [json.loads(line) for line in (ROOT / "references/source/v8.3/audit/paragraphs.jsonl").read_text(encoding="utf-8").splitlines()]
    expected = "\n".join(row["text"] for row in paragraphs if row["ordinal"] in ordinals)
    assert expected
    inventory = [json.loads(line) for line in (ROOT / "references/ontology/inventory/core.jsonl").read_text(encoding="utf-8").splitlines()]
    concept = next(row for row in inventory if row["concept_id"] == concept_id)
    assert concept["authoritative_definition"] == expected
    assert concept["definition"] == expected
    card = (ROOT / concept["card_path"]).read_text(encoding="utf-8")
    for paragraph in expected.splitlines():
        assert paragraph in card


def test_root_card_keeps_conditional_recursion_and_evidence_limits():
    paragraphs = [json.loads(line) for line in (ROOT / "references/source/v8.3/audit/paragraphs.jsonl").read_text(encoding="utf-8").splitlines()]
    card = (ROOT / "references/ontology/cards/evidence-claim/root-evidence-contracts.md").read_text(encoding="utf-8")
    for row in paragraphs:
        if row["ordinal"] in (2111, 2112, 2114, 2115):
            assert row["text"] in card
