from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from xi_kari_runtime import world_volume


def frozen_state():
    return {
        "snapshot_id": "STATE-0", "model_version": "test-model-1",
        "run_id": "RUN-SYNTHETIC", "evidence_cutoff": "2026-09-30T12:00:00Z",
        "objects": [{
            "object_id": "OBJECT-1", "K": {"version": "1", "definition": "track participants in the named task"},
            "variables": [
                {"variable_id": "XK-PROV-RULE", "category": "rules", "value": "old", "clock_id": "institutional"},
                {"variable_id": "XK-PROV-BELIEF", "category": "beliefs", "value": "unknown", "clock_id": "interaction"},
            ],
        }],
        "unknowns": [{"unknown_id": "UNKNOWN-CAUSE", "reason": "Cause not identified"}],
        "losses": [], "residuals": [{"residual_id": "RES-1", "reason": "Indirect effects unmeasured"}],
    }


def observed_event(state):
    event = {
        "event_id": "EVENT-UNAUTHORIZED", "actor_id": "ACTOR-1", "object_id": "OBJECT-1",
        "kind": "observed", "update_path": "observed_direct", "occurrence_status": "occurred",
        "authorization_status": "unauthorized", "occurred_at": "2026-09-30T11:00:00Z",
        "evidence_refs": ["EV-1"], "conditions": [], "deltas": [{
            "object_id": "OBJECT-1", "variable_id": "XK-PROV-RULE", "category": "rules",
            "before": "old", "after": "new", "clock_id": "institutional", "evidence_refs": ["EV-1"],
        }],
        "channel_id": None, "mechanism_id": None, "authorization_ref": None,
    }
    evidence = {"EV-1": {
        "evidence_id": "EV-1", "identity": "observed", "source_refs": ["SYNTHETIC-UNIT-FIXTURE"],
        "available_at": "2026-09-30T11:30:00Z", "event_id": event["event_id"],
        "object_id": "OBJECT-1", "variable_id": "XK-PROV-RULE", "observed_value": "new",
    }}
    return event, evidence


def test_observed_unauthorized_rule_change_updates_fact_without_granting_permission():
    state = frozen_state()
    before = deepcopy(state)
    event, evidence = observed_event(state)
    transition = world_volume.apply_registered_event(state, event, evidence_registry=evidence)
    assert transition.output_state["objects"][0]["variables"][0]["value"] == "new"
    assert transition.event_role == "e(t)"
    assert transition.authorization_status == "unauthorized"
    assert transition.external_action_authorized is False
    assert transition.output_state["unknowns"] == before["unknowns"]
    assert transition.output_state["residuals"] == before["residuals"]
    assert state == before


def test_report_updates_source_labelled_belief_but_not_reported_fact():
    state = frozen_state()
    event, evidence = observed_event(state)
    event.update(kind="reported", update_path="reported_belief", authorization_status="unknown")
    event["deltas"][0].update(variable_id="XK-PROV-BELIEF", category="beliefs", before="unknown", after="report received", clock_id="interaction")
    evidence["EV-1"].update(identity="reported", variable_id="XK-PROV-BELIEF", observed_value="report received")
    transition = world_volume.apply_registered_event(state, event, evidence_registry=evidence)
    assert transition.output_state["objects"][0]["variables"][0]["value"] == "old"
    assert transition.output_state["objects"][0]["variables"][1]["value"] == "report received"
    assert transition.evidence_identity == "reported"
    assert transition.reported_content_status == "unknown"
    event["deltas"][0].update(variable_id="XK-PROV-RULE", category="rules", before="old", after="new", clock_id="institutional")
    with pytest.raises(world_volume.WorldVolumeError, match="belief"):
        world_volume.apply_registered_event(state, event, evidence_registry=evidence)


@pytest.mark.parametrize("kind", ["planned", "hypothetical", "simulated"])
def test_scenario_state_remains_conditional(kind):
    state = frozen_state()
    event, evidence = observed_event(state)
    event.update(kind=kind, update_path="scenario", occurrence_status="not_occurred")
    evidence["EV-1"]["identity"] = kind
    transition = world_volume.apply_registered_event(state, event, evidence_registry=evidence)
    assert transition.evidence_identity == kind
    assert transition.event_role == "scenario"
    assert transition.external_action_authorized is False
    assert transition.output_state["objects"][0]["variables"][0]["value"] == "new"


def test_u_requires_exact_external_authorization_and_actual_occurrence():
    state = frozen_state()
    event, evidence = observed_event(state)
    event.update(authorization_status="authorized", authorization_ref="AUTH-1")
    authorization = {"AUTH-1": {
        "authorization_id": "AUTH-1", "status": "valid", "actor_id": "ACTOR-1",
        "object_id": "OBJECT-1", "event_id": "EVENT-UNAUTHORIZED", "source_refs": ["SYNTHETIC-AUTH"],
        "starts_at": "2026-09-30T00:00:00Z", "ends_at": "2026-10-01T00:00:00Z",
    }}
    with pytest.raises(world_volume.WorldVolumeError, match="authorization"):
        world_volume.apply_registered_event(state, event, evidence_registry=evidence)
    transition = world_volume.apply_registered_event(state, event, evidence_registry=evidence, authorization_registry=authorization)
    assert transition.event_role == "u(t)"
    assert transition.external_action_authorized is False
    event["occurrence_status"] = "not_occurred"
    with pytest.raises(world_volume.WorldVolumeError, match="occurrence"):
        world_volume.apply_registered_event(state, event, evidence_registry=evidence, authorization_registry=authorization)


@pytest.mark.parametrize("mutation", ["ghost", "wrong_object", "wrong_value", "late", "no_op", "wrong_before", "duplicate"])
def test_observation_delta_is_exact_and_cutoff_bound(mutation):
    state = frozen_state()
    event, evidence = observed_event(state)
    if mutation == "ghost": evidence.clear()
    if mutation == "wrong_object": evidence["EV-1"]["object_id"] = "OTHER"
    if mutation == "wrong_value": evidence["EV-1"]["observed_value"] = "unexpected"
    if mutation == "late": evidence["EV-1"]["available_at"] = "2026-10-01T00:00:00Z"
    if mutation == "no_op": event["deltas"][0]["after"] = "old"
    if mutation == "wrong_before": event["deltas"][0]["before"] = "not old"
    if mutation == "duplicate": event["deltas"].append(deepcopy(event["deltas"][0]))
    with pytest.raises(world_volume.WorldVolumeError):
        world_volume.apply_registered_event(state, event, evidence_registry=evidence)


def test_transition_replay_refuses_parent_K_or_unknown_content_change():
    state = frozen_state()
    event, evidence = observed_event(state)
    transition = world_volume.apply_registered_event(state, event, evidence_registry=evidence)
    assert transition.replay(state) == transition.output_state
    changed = deepcopy(state)
    changed["unknowns"][0]["reason"] = "Hidden cause claimed resolved"
    with pytest.raises(world_volume.WorldVolumeError, match="parent"):
        transition.replay(changed)


def test_mechanism_propagation_consumes_independent_channel_and_timing():
    state = frozen_state()
    event, evidence = observed_event(state)
    event.update(kind="simulated", update_path="mechanism_inference", occurrence_status="not_occurred", channel_id="CHANNEL-1", mechanism_id="MECH-1")
    evidence["EV-1"].update(identity="simulated")
    channel = {"CHANNEL-1": {
        "channel_id": "CHANNEL-1", "mechanism_id": "MECH-1", "from_object_id": "OBJECT-1", "to_object_id": "OBJECT-1",
        "active": True, "identity_preserved": True, "acl_authorized": True,
        "evidence_refs": ["EV-CHANNEL"], "lag_seconds": 0, "capacity": 1, "threshold_conditions": [],
        "valid_from": "2026-09-30T00:00:00Z", "valid_until": "2026-10-01T00:00:00Z",
    }}
    evidence["EV-CHANNEL"] = {"evidence_id": "EV-CHANNEL", "identity": "observed", "source_refs": ["SYNTHETIC-MECHANISM"], "available_at": "2026-09-30T10:00:00Z", "channel_id": "CHANNEL-1", "mechanism_id": "MECH-1", "support_status": "supported"}
    transition = world_volume.apply_registered_event(state, event, evidence_registry=evidence, channel_registry=channel)
    assert transition.evidence_identity == "simulated"
    assert transition.event_role == "mechanism_inference"
    for field, value in (("active", False), ("acl_authorized", False), ("capacity", 0), ("mechanism_id", "GHOST")):
        bad = deepcopy(channel)
        bad["CHANNEL-1"][field] = value
        with pytest.raises(world_volume.WorldVolumeError, match="channel"):
            world_volume.apply_registered_event(state, event, evidence_registry=evidence, channel_registry=bad)
    with pytest.raises(world_volume.WorldVolumeError, match="channel"):
        world_volume.apply_registered_event(state, event, evidence_registry=evidence)


def test_inferred_cause_cannot_be_laundered_into_direct_observation():
    state = frozen_state()
    event, evidence = observed_event(state)
    event["mechanism_id"] = "INFERRED-CAUSE"
    with pytest.raises(world_volume.WorldVolumeError, match="mechanism"):
        world_volume.apply_registered_event(state, event, evidence_registry=evidence)


def test_multiple_events_replay_in_time_order_with_independent_evidence():
    state = frozen_state()
    first, evidence = observed_event(state)
    second = deepcopy(first)
    second.update(event_id="EVENT-2", occurred_at="2026-09-30T11:15:00Z", evidence_refs=["EV-2"])
    second["deltas"][0].update(before="new", after="latest", evidence_refs=["EV-2"])
    evidence["EV-2"] = {**evidence["EV-1"], "evidence_id": "EV-2", "event_id": "EVENT-2", "observed_value": "latest"}
    output = world_volume.apply_registered_events(state, [first, second], evidence_registry=evidence)
    assert output[-1].output_state["objects"][0]["variables"][0]["value"] == "latest"
    with pytest.raises(world_volume.WorldVolumeError, match="time"):
        world_volume.apply_registered_events(state, [second, first], evidence_registry=evidence)
