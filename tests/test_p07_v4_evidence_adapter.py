from copy import deepcopy
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from xi_kari_runtime import evidence, world_volume, v4_contracts
from tests.test_p04_v4_claim_contracts import _basis, _qualification, _support_checks
from tests.test_p07_event_records import frozen_state, observed_event


def v4_event_fixture():
    state = frozen_state()
    event, _ = observed_event(state)
    source = {"source_id": "SYNTHETIC-SOURCE", "origin": "user_material", "assessment_verdict": "admitted", "source_revision": "fixture-revision-1", "canonical_locator": "SYNTHETIC-SOURCE:1", "content_sha256": "c" * 64, "lineage_refs": ["SYNTHETIC-LINEAGE"], "research_design": "synthetic event-adapter test", "read_extent": "entire synthetic fixture", "provenance_refs": ["SYNTHETIC-SOURCE"], "independence_key": "SYNTHETIC-LINEAGE", "availability_status": "available", "visibility": "public", "protected_review": None, "accessed_at": "2026-09-30T11:30:00Z", "content_authority": "host-observed"}
    observation = {"status": "bound", "event_stream_sha256": "d" * 64, "open_event_ids": ["SYNTHETIC-OPEN"]}
    observation["binding_sha256"] = world_volume._canonical_sha256({"source_id": source["source_id"], "content_sha256": source["content_sha256"], "event_stream_sha256": observation["event_stream_sha256"], "open_event_ids": observation["open_event_ids"]})
    source["host_observation"] = observation
    retrieval = {"run_id": state["run_id"], "sources": [source]}
    targets = world_volume.registered_event_target_hashes([event])
    path = next(iter(targets))
    claim = {"claim_id": "CLAIM-RULE", "text": "Synthetic observation of a rule change", "kind": "external_fact", "support": [{"source_id": source["source_id"], "summary": "Synthetic observational fixture", "support_checks": _support_checks()}], "claim_basis": _basis("domain_empirical", source["source_id"]), "formal_qualification": _qualification(), "responsibility_refs": [], "world_targets": [{"target_path": path, "relation": "descriptive"}]}
    ledger = evidence.build_evidence_ledger(run_id=state["run_id"], claims=[claim], retrieval_index=retrieval, world_target_hashes=targets, contract_version=4)
    bindings = [{"event_id": event["event_id"], "delta_index": 0, "evidence_ref": "EV-1", "xk3_evidence_id": "CLAIM-RULE-e1"}]
    return state, event, ledger, retrieval, bindings


def test_real_P04_evidence_builder_and_validator_feed_exact_event_targets():
    state, event, ledger, retrieval, bindings = v4_event_fixture()
    assert evidence.validate_evidence_ledger(ledger, retrieval) == []
    registry = world_volume.bind_registered_event_evidence(state, [event], evidence_ledger=ledger, retrieval_index=retrieval, bindings=bindings)
    transition = world_volume.apply_registered_event(state, event, evidence_registry=registry)
    assert transition.output_state["objects"][0]["variables"][0]["value"] == "new"
    assert registry["EV-1"]["material_identity"] == ledger["evidence"][0]["evidence_identity"]
    assert registry["EV-1"]["support_checks"] == ledger["evidence"][0]["support_checks"]
    assert transition.external_action_authorized is False


@pytest.mark.parametrize("mutation", ["source_assertion", "world_check_failed", "target_changed", "run_changed", "source_changed"])
def test_v4_adapter_does_not_erase_P04_responsibility(mutation):
    state, event, ledger, retrieval, bindings = v4_event_fixture()
    if mutation == "source_assertion": ledger["claims"][0]["claim_basis"].update(kind="source_fact"); ledger["claims"][0]["claim_basis"]["scope"]["target"] = "author_statement"
    if mutation == "world_check_failed": ledger["evidence"][0]["support_checks"]["world_fact_supported"]["status"] = "failed"
    if mutation == "target_changed": event["deltas"][0]["after"] = "altered after freezing evidence"
    if mutation == "run_changed": state["run_id"] = "OTHER-RUN"
    if mutation == "source_changed": retrieval["sources"][0]["content_sha256"] = "e" * 64
    with pytest.raises(world_volume.WorldVolumeError):
        world_volume.bind_registered_event_evidence(state, [event], evidence_ledger=ledger, retrieval_index=retrieval, bindings=bindings)
