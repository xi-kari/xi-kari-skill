from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from xi_kari_runtime import world_volume


def identity():
    return {
        "object_id": "collective", "object_type": "human",
        "K": {"version": "1", "definition": "shared recurring work on the same problem"},
        "SP": dict.fromkeys("AXTOCRINJ", "declared scope"), "window": {"start": "2026-09-01", "end": "2026-09-30"},
        "subsystem": "formation", "source_revision": "v9.0", "members": ["participant-1"],
    }


def test_member_changes_preserve_frozen_K_but_definition_changes_do_not():
    first = identity()
    second = deepcopy(first)
    second["members"] = ["participant-2", "participant-3"]
    assert world_volume.validate_identity_continuation(first, second) == "same_K"
    second["K"]["definition"] = "formally employed staff only"
    with pytest.raises(world_volume.WorldVolumeError, match="K"):
        world_volume.validate_identity_continuation(first, second)
    second["K"]["version"] = "2"
    with pytest.raises(world_volume.WorldVolumeError, match="recheck"):
        world_volume.validate_identity_continuation(first, second)


def prototype():
    obj = identity()
    record = {
        "record_id": "PROTO-1", "material_version": "1", "object_id": "collective",
        "identity_binding_sha256": world_volume.freeze_object_identity(obj)["binding_sha256"],
        "classification_mode": "single_dominant", "candidate_states": ["S0"], "path_candidates": [],
        "conditions": {}, "missing_data": [], "object_evidence_refs": ["E-1"],
        "uncertainty": "Formation is provisional", "reviewers": [{
            "reviewer_id": "independent-observer", "independent": True,
            "reviewed_at": "2026-09-30T00:00:00Z", "material_version": "1", "outcome": "bounded",
        }],
        "appeal": {"procedure_id": "APPEAL-1", "status": "available"},
        "rollback": {"procedure_id": "ROLLBACK-1", "status": "available"},
        "normative_status": "descriptive_only", "action_authorization": "none",
    }
    for category in ("entry", "exit", "observation", "counterexample", "falsification"):
        record["conditions"][category] = [{
            "item_id": "ITEM-" + category, "state_id": "S0",
            "status": "supported" if category in {"entry", "observation"} else "unsupported_or_undecided",
            "evidence_refs": ["E-1"], "reason": "Synthetic item-level observation",
        }]
    evidence = {"E-1": {"evidence_id": "E-1", "source_refs": ["SYNTHETIC-FIXTURE"], "object_id": "collective", "identity": "observed"}}
    return obj, record, evidence


def test_forming_S0_may_have_changing_members_and_remains_descriptive():
    obj, record, evidence = prototype()
    obj["members"].append("new-member")
    result = world_volume.validate_prototype_record(record, identity_record=obj, evidence_registry=evidence)
    assert result["candidate_states"] == ["S0"]
    assert result["action_authorization"] == "none"


@pytest.mark.parametrize("mutation", ["falsified", "ghost", "alias_review", "stale_K", "authorization", "missing_item", "unknown_candidate"])
def test_prototype_rejects_failed_or_unbound_classification(mutation):
    obj, record, evidence = prototype()
    if mutation == "falsified": record["conditions"]["falsification"][0]["status"] = "supported"
    if mutation == "ghost": evidence.clear()
    if mutation == "alias_review": record["reviewers"][0]["reviewer_id"] = " ＣＯＬＬＥＣＴＩＶＥ/reviewer "
    if mutation == "stale_K": obj["K"]["definition"] = "new definition"
    if mutation == "authorization": record["action_authorization"] = "remove member"
    if mutation == "missing_item": record["conditions"]["exit"] = []
    if mutation == "unknown_candidate": record["classification_mode"] = "unknown"
    with pytest.raises(world_volume.WorldVolumeError):
        world_volume.validate_prototype_record(record, identity_record=obj, evidence_registry=evidence)


@pytest.mark.parametrize("alias", ["collective:reviewer", "reviewer@collective", "collective.reviewer", "collective reviewer"])
def test_reviewer_alias_does_not_create_independent_review(alias):
    obj, record, evidence = prototype()
    record["reviewers"][0]["reviewer_id"] = alias
    with pytest.raises(world_volume.WorldVolumeError, match="independent"):
        world_volume.validate_prototype_record(record, identity_record=obj, evidence_registry=evidence)


def test_unknown_mode_is_valid_with_no_candidates_and_explicit_missing_distinction():
    obj, record, evidence = prototype()
    record.update(classification_mode="unknown", candidate_states=[], conditions={key: [] for key in record["conditions"]}, missing_data=[{"status": "unknown", "reason": "No observed entry or falsification distinguishes candidates"}])
    assert world_volume.validate_prototype_record(record, identity_record=obj, evidence_registry=evidence)["classification_mode"] == "unknown"


def test_S0_can_enter_X0_without_becoming_S7_or_completed_exit():
    obj, record, evidence = prototype()
    record["path_candidates"] = [{"path_id": "PATH-X0", "path_type": "X0", "origin_state": "S0", "exit_status": "partial", "reason": "Unresolved receivers and debt", "evidence_refs": ["E-1"]}]
    assert world_volume.validate_prototype_record(record, identity_record=obj, evidence_registry=evidence)["path_candidates"][0]["exit_status"] == "partial"
    record["path_candidates"][0]["exit_status"] = "completed"
    with pytest.raises(world_volume.WorldVolumeError, match="X0"):
        world_volume.validate_prototype_record(record, identity_record=obj, evidence_registry=evidence)
