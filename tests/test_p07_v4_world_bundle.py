from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from xi_kari_runtime import world_volume
from tests.test_p07_v4_evidence_adapter import v4_event_fixture


def bundle_fixture():
    state, event, ledger, retrieval, bindings = v4_event_fixture()
    raw_hash = json.loads((ROOT / "references/source/v9.0/source-manifest.json").read_text(encoding="utf-8"))["raw_sha256"]
    anchor = "V90-P01827"
    scope = {"object_id": "OBJECT-1", "object_type": "human", "K": deepcopy(state["objects"][0]["K"]), "SP": dict.fromkeys("AXTOCRINJ", "synthetic declared scope"), "window": {"start": "2026-09-30T00:00:00Z", "end": "2026-09-30T12:00:00Z"}, "subsystem": "rule record", "source_revision": raw_hash, "members": []}
    bundle = {"schema_id": "xi-kari.v4.xk.world-volume", "schema_version": 4, "source_version": "v9.0", "ontology_refs": ["V90-CANON-U01", "V90-CANON-U02", "V90-CANON-U03"], "source_anchors": [anchor], "applicability": {}, "registered_state": state, "identity_records": [scope], "prototype_records": [], "event_records": [event], "event_evidence_bindings": bindings}
    for stage in ("world_state", "transformation", "mechanism", "recursion", "forecast", "action_choice"):
        bundle["applicability"][stage] = {"status": "applicable" if stage == "world_state" else "not_applicable", "rationale": "Observed rule record only; no inferred mechanism or future action requested", "source_refs": [anchor], "dependency_refs": []}
    return bundle, ledger, retrieval


def test_public_world_validator_consumes_P04_binding_applicability_and_evidence():
    bundle, ledger, retrieval = bundle_fixture()
    world_volume.validate_world_volume(bundle, repository_root=ROOT, evidence_ledger=ledger, retrieval_index=retrieval, expected_run_id=bundle["registered_state"]["run_id"])
    result = world_volume.validate_registered_world_bundle(bundle, repository_root=ROOT, evidence_ledger=ledger, retrieval_index=retrieval)
    assert result["transitions"][0].event_role == "e(t)"
    assert result["final_state"]["objects"][0]["variables"][0]["value"] == "new"
    assert result["identity_bindings"][0]["K"]["version"] == "1"


@pytest.mark.parametrize("mutation", ["legacy_source", "body_alias", "ghost_concept", "changed_source_hash", "stale_K", "missing_applicability"])
def test_version_four_world_binding_cannot_bypass_actual_authority(mutation):
    bundle, ledger, retrieval = bundle_fixture()
    if mutation == "legacy_source": bundle["source_version"] = "v8.3"
    if mutation == "body_alias": bundle["source_anchors"] = ["XK9-B00961"]
    if mutation == "ghost_concept": bundle["ontology_refs"] = ["V90-CANON-M02"]
    if mutation == "changed_source_hash": bundle["identity_records"][0]["source_revision"] = "a" * 64
    if mutation == "stale_K": bundle["identity_records"][0]["K"]["definition"] = "a different K"
    if mutation == "missing_applicability": del bundle["applicability"]["mechanism"]
    with pytest.raises(world_volume.WorldVolumeError):
        world_volume.validate_world_volume(bundle, repository_root=ROOT, evidence_ledger=ledger, retrieval_index=retrieval)
