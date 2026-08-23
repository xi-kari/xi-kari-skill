"""Pure v8.2 transformation and cascade semantics."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .world_volume import (
    WorldVolumeError,
    _native_snapshot,
    _predicate_result,
    _validate_ontology_binding,
    _validate_schema,
    apply_event,
    validate_world_volume,
)


AXES = tuple("AXTOCRINJ")
TRANSFORM_KINDS = frozenset(
    {"scale", "circle-relation", "representation-translation"}
)
REQUIRED_TRANSFORM_ONTOLOGY = frozenset(
    {
        "V82-CANON-CORE-D3-SCALE-TRANSFORMATION",
        "V82-CANON-CORE-CIRCLE-TRANSFORMATION",
        "V82-HEADING-CORE-V82-P0554",
    }
)
REQUIRED_CASCADE_ONTOLOGY = frozenset(
    {"V82-CANON-CORE-CIRCLE-TRANSFORMATION", "V82-CANON-EVENT"}
)


class TransformationError(ValueError):
    """Raised when a transformation flattens or invents semantic structure."""


class ChannelContinuityError(TransformationError):
    """Raised when a cascade hop lacks a revalidated real channel."""


def _world_catalogs(volume: Mapping[str, Any]) -> tuple[set[str], set[str]]:
    represented = [*volume["actors"], *volume["circles"], *volume["positions"]]
    locations = {
        volume["volume_id"],
        *(record["actor_id"] for record in volume["actors"]),
        *(record["circle_id"] for record in volume["circles"]),
        *(record["position_id"] for record in volume["positions"]),
        *(record["channel_id"] for record in volume["channels"]),
        *(record["relation_id"] for record in volume["circle_relations"]),
        *(record["distribution_id"] for record in volume["local_distributions"]),
        *(record["M_state"]["state_id"] for record in represented),
        *(record["Psi_state"]["state_id"] for record in represented),
    }
    residual_ids = {record["residual_id"] for record in volume["residuals"]}
    return locations, residual_ids


def _classification(relations: set[str]) -> str:
    if "incomparable" in relations:
        return "horizontal-or-incomparable"
    if "expands" in relations and "contracts" in relations:
        return "mixed"
    if "unknown" in relations:
        return "unresolved"
    if relations == {"equal"}:
        return "all-equal"
    if relations <= {"equal", "expands"}:
        return "elevation"
    return "reduction"


def _validate_partition_and_effects(
    transform: Mapping[str, Any],
    *,
    locations: set[str],
    identity_criteria_by_location: Mapping[str, str],
    residual_ids: set[str],
    used_component_ids: set[str],
    used_variable_ids: set[str],
    used_loss_ids: set[str],
) -> None:
    transform_id = transform["transform_id"]
    for identity_field in ("input_identity", "output_identity"):
        location_ref = transform[identity_field]["location_ref"]
        if location_ref not in locations:
            raise TransformationError(
                f"{transform_id} {identity_field} does not resolve the source Omega"
            )
        if (
            identity_criteria_by_location.get(location_ref)
            != transform[identity_field]["identity_criteria"]
        ):
            raise TransformationError(
                f"{transform_id} {identity_field} does not bind the source Omega K"
            )

    local_component_ids: set[str] = set()
    for field in ("preserved", "changed", "folded", "omitted", "unknown"):
        for component in transform[field]:
            component_id = component["component_id"]
            if component_id in local_component_ids or component_id in used_component_ids:
                raise TransformationError("transformation component IDs must be unique")
            local_component_ids.add(component_id)
            used_component_ids.add(component_id)
            if component["location_ref"] not in locations:
                raise TransformationError("transformation component location is unresolved")

    for variable in transform["effective_variables"]:
        variable_id = variable["variable_id"]
        if variable_id in used_variable_ids:
            raise TransformationError("effective variable IDs must be unique")
        used_variable_ids.add(variable_id)
        if variable["location_ref"] not in locations:
            raise TransformationError("effective variable location is unresolved")

    loss_locations: set[str] = set()
    for loss in transform["task_relative_losses"]:
        loss_id = loss["loss_id"]
        if loss_id in used_loss_ids:
            raise TransformationError("task-relative loss IDs must be unique")
        used_loss_ids.add(loss_id)
        if loss["location_ref"] not in locations:
            raise TransformationError("task-relative loss location is unresolved")
        loss_locations.add(loss["location_ref"])

    if not set(transform["residual_ids"]).issubset(residual_ids):
        raise TransformationError("transformation residual does not resolve the source Omega")
    affected = transform["affected_location_refs"]
    effect_locations = [record["location_ref"] for record in transform["location_effects"]]
    if (
        not affected
        or len(affected) != len(set(affected))
        or len(effect_locations) != len(set(effect_locations))
        or set(effect_locations) != set(affected)
        or not set(affected).issubset(locations)
    ):
        raise TransformationError(
            "each affected location requires one explicit local effect audit"
        )
    if not loss_locations.issubset(set(affected)):
        raise TransformationError(
            "each task-relative loss location must be affected and have an effect audit"
        )

    nontrivial = any(
        transform[field]
        for field in (
            "changed",
            "folded",
            "omitted",
            "unknown",
            "effective_variables",
            "task_relative_losses",
            "residual_ids",
        )
    )
    if nontrivial and not transform["location_effects"]:
        raise TransformationError(
            "a net effect cannot replace local benefit, harm, exit-cost, and spillover fields"
        )


def _validate_scale(
    transform: Mapping[str, Any],
    *,
    scale_profiles: Mapping[str, Mapping[str, str]],
) -> None:
    differences = transform["axis_differences"]
    axes = [record["axis_id"] for record in differences]
    if len(axes) != 9 or len(axes) != len(set(axes)) or set(axes) != set(AXES):
        raise TransformationError("scale transform must contain nine unique v8.2 axes")
    relations = {record["relation"] for record in differences}
    expected = _classification(relations)
    if transform["transformation_class"] != expected:
        raise TransformationError(
            "scale transformation classification differs from its axis relations"
        )
    source_profile = scale_profiles.get(transform["input_identity"]["location_ref"])
    target_profile = scale_profiles.get(transform["output_identity"]["location_ref"])
    if source_profile is None or target_profile is None:
        raise TransformationError("scale transformation lacks an actual Omega scale profile")
    for difference in differences:
        axis = difference["axis_id"]
        same_value = source_profile[axis] == target_profile[axis]
        if (difference["relation"] == "equal") != same_value and difference[
            "relation"
        ] != "unknown":
            raise TransformationError(
                "scale axis relation differs from the actual Omega scale profile"
            )
        if difference["relation"] != "unknown" and not difference["evidence_refs"]:
            raise TransformationError("known scale comparison lacks bridge evidence")


def validate_transformations(
    document: Mapping[str, object],
    *,
    source_volume: Mapping[str, object],
    repository_root: Path | None = None,
) -> tuple[str, ...]:
    """Validate all three transformation contracts against one Omega."""

    snapshot = _native_snapshot(
        document, label="transformation ledger", error_type=TransformationError
    )
    world = _native_snapshot(
        source_volume, label="source world volume", error_type=TransformationError
    )
    if not isinstance(snapshot, dict) or not isinstance(world, dict):
        raise TransformationError("transformation ledger and source volume must be mappings")
    try:
        _validate_schema(
            "xk-transformation-ledger.schema.json",
            snapshot,
            label="transformation ledger",
            error_type=TransformationError,
            repository_root=repository_root,
        )
    except TransformationError as error:
        transforms = snapshot.get("transformations")
        if isinstance(transforms, list) and {
            record.get("kind")
            for record in transforms
            if isinstance(record, Mapping)
        } != TRANSFORM_KINDS:
            raise TransformationError(
                "ledger must preserve all three transformation kinds"
            ) from error
        if ".location_effects:" in str(error):
            raise TransformationError(
                "each affected location requires one explicit local effect audit"
            ) from error
        if any(
            field in str(error)
            for field in (
                "circle_relation_id",
                "representation_parent_state_id",
                "representation_output_state_id",
            )
        ):
            raise TransformationError(
                "transformation lacks its kind-specific Omega semantic binding"
            ) from error
        raise
    try:
        validate_world_volume(
            world,
            repository_root=repository_root,
        )
    except WorldVolumeError as error:
        raise TransformationError(f"invalid source Omega: {error}") from error
    _validate_ontology_binding(
        snapshot,
        required=REQUIRED_TRANSFORM_ONTOLOGY,
        label="transformation ledger",
        error_type=TransformationError,
        repository_root=repository_root,
    )
    if snapshot["world_volume_id"] != world["volume_id"]:
        raise TransformationError("transformation ledger binds a different Omega")

    transforms = snapshot["transformations"]
    transform_ids = [record["transform_id"] for record in transforms]
    if len(transform_ids) != len(set(transform_ids)):
        raise TransformationError("transformation IDs must be unique")
    if {record["kind"] for record in transforms} != TRANSFORM_KINDS:
        raise TransformationError("ledger must preserve all three transformation kinds")

    locations, residual_ids = _world_catalogs(world)
    identity_criteria_by_location = {
        record[identifier_field]: record["identity_criteria"]
        for records, identifier_field in (
            (world["actors"], "actor_id"),
            (world["circles"], "circle_id"),
            (world["positions"], "position_id"),
        )
        for record in records
    }
    scale_profiles = {
        record[identifier_field]: record["scale_profile"]
        for records, identifier_field in (
            (world["actors"], "actor_id"),
            (world["circles"], "circle_id"),
            (world["positions"], "position_id"),
        )
        for record in records
    }
    positions = {record["position_id"]: record for record in world["positions"]}
    circle_relations = {
        record["relation_id"]: record for record in world["circle_relations"]
    }
    events = {record["event_id"]: record for record in world["events"]}
    state_diffs = {
        event["event_id"]: apply_event(
            world, event, repository_root=repository_root
        )
        for event in world["events"]
    }
    used_components: set[str] = set()
    used_variables: set[str] = set()
    used_losses: set[str] = set()
    for transform in transforms:
        _validate_partition_and_effects(
            transform,
            locations=locations,
            identity_criteria_by_location=identity_criteria_by_location,
            residual_ids=residual_ids,
            used_component_ids=used_components,
            used_variable_ids=used_variables,
            used_loss_ids=used_losses,
        )
        if transform["kind"] == "scale":
            _validate_scale(transform, scale_profiles=scale_profiles)
        elif transform["axis_differences"] or transform["transformation_class"] is not None:
            raise TransformationError(
                "circle or representation transformation cannot impersonate scale axes"
            )
        if transform["kind"] == "circle-relation":
            source = positions.get(transform["input_identity"]["location_ref"])
            target = positions.get(transform["output_identity"]["location_ref"])
            relation = circle_relations.get(transform["circle_relation_id"])
            if (
                source is None
                or target is None
                or relation is None
                or relation["source_circle_ref"] != source["circle_id"]
                or relation["target_circle_ref"] != target["circle_id"]
            ):
                raise TransformationError(
                    "circle transform does not bind its actual Omega circle relation endpoints"
                )
        if transform["kind"] == "representation-translation":
            source = positions.get(transform["input_identity"]["location_ref"])
            target = positions.get(transform["output_identity"]["location_ref"])
            if (
                source is None
                or target is None
                or transform["representation_parent_state_id"]
                not in {source["M_state"]["state_id"], source["Psi_state"]["state_id"]}
            ):
                raise TransformationError(
                    "representation state binding does not resolve its source Omega state"
                )
        required_evidence: set[str] = set()
        for transition in transform["transition_refs"]:
            state_diff = state_diffs.get(transition["event_id"])
            event = events.get(transition["event_id"])
            if state_diff is None:
                raise TransformationError(
                    "transformation transition references an unknown Omega event"
                )
            if transition["state_diff_id"] != state_diff.state_diff_id:
                raise TransformationError(
                    "transformation transition pairs an event with the wrong StateDiff"
                )
            nontrivial = any(
                transform[field]
                for field in (
                    "changed",
                    "folded",
                    "omitted",
                    "unknown",
                    "effective_variables",
                    "task_relative_losses",
                    "residual_ids",
                )
            )
            if nontrivial and not (
                state_diff.changed_positions
                or state_diff.changed_relations
                or state_diff.advanced_clocks
            ):
                raise TransformationError(
                    "a nontrivial transformation cannot bind a no-op StateDiff"
                )
            if nontrivial and (
                event is None
                or event["source_position_id"]
                != transform["input_identity"]["location_ref"]
                or transform["output_identity"]["location_ref"]
                not in event["target_position_ids"]
            ):
                raise TransformationError(
                    "transformation transition does not bind its Omega endpoints"
                )
            if transform["kind"] == "circle-relation":
                relation = circle_relations[transform["circle_relation_id"]]
                if relation["channel_id"] not in event["channel_ids"]:
                    raise TransformationError(
                        "circle transform transition does not use its relation channel"
                    )
            if transform["kind"] == "representation-translation":
                updated_state_ids = {
                    update["state_id"]
                    for field in ("M_updates", "Psi_updates")
                    for update in event[field]
                    if update["position_id"]
                    == transform["output_identity"]["location_ref"]
                }
                if (
                    transform["representation_output_state_id"]
                    not in updated_state_ids
                ):
                    raise TransformationError(
                        "representation state binding differs from its transition payload"
                    )
            required_evidence.update(state_diff.evidence_refs)
        if not required_evidence.issubset(set(transform["evidence_refs"])):
            raise TransformationError(
                "transformation evidence does not cover its bound StateDiff"
            )
    return tuple(transform_ids)


def validate_cascade(
    cascade: Mapping[str, object],
    volume: Mapping[str, object],
    *,
    repository_root: Path | None = None,
) -> tuple[str, ...]:
    """Revalidate boundary, channel, identity, representation, ACL, and evidence per hop."""

    snapshot = _native_snapshot(
        cascade, label="cascade", error_type=ChannelContinuityError
    )
    world = _native_snapshot(
        volume, label="cascade source Omega", error_type=ChannelContinuityError
    )
    if not isinstance(snapshot, dict) or not isinstance(world, dict):
        raise ChannelContinuityError("cascade and source Omega must be mappings")
    _validate_schema(
        "xk-transform-cascade.schema.json",
        snapshot,
        label="cascade",
        error_type=ChannelContinuityError,
        repository_root=repository_root,
    )
    try:
        validate_world_volume(world, repository_root=repository_root)
    except WorldVolumeError as error:
        raise ChannelContinuityError(f"invalid cascade source Omega: {error}") from error
    _validate_ontology_binding(
        snapshot,
        required=REQUIRED_CASCADE_ONTOLOGY,
        label="cascade",
        error_type=ChannelContinuityError,
        repository_root=repository_root,
    )
    if snapshot["world_volume_id"] != world["volume_id"]:
        raise ChannelContinuityError("cascade binds a different Omega")

    positions = {record["position_id"]: record for record in world["positions"]}
    channels = {record["channel_id"]: record for record in world["channels"]}
    relations = {
        record["relation_id"]: record for record in world["circle_relations"]
    }
    events = {record["event_id"]: record for record in world["events"]}
    state_diffs = {
        event_id: apply_event(
            world, event, repository_root=repository_root
        )
        for event_id, event in events.items()
    }
    hop_ids: set[str] = set()
    previous_target: str | None = None
    ordered_channels: list[str] = []
    gates = (
        "boundary_validated",
        "channel_validated",
        "identity_preserved",
        "representation_qualified",
        "threshold_met",
        "acl_authorized",
    )
    for ordinal, hop in enumerate(snapshot["hops"], start=1):
        if hop["hop_id"] in hop_ids:
            raise ChannelContinuityError("cascade hop IDs must be unique")
        hop_ids.add(hop["hop_id"])
        for gate in gates:
            if hop[gate] is not True:
                raise ChannelContinuityError(f"cascade hop {ordinal} fails {gate}")
        source_id = hop["from_position_id"]
        target_id = hop["to_position_id"]
        source = positions.get(source_id)
        target = positions.get(target_id)
        channel = channels.get(hop["channel_id"])
        if source is None or target is None or channel is None:
            raise ChannelContinuityError("cascade hop has an unresolved endpoint or channel")
        if previous_target is not None and source_id != previous_target:
            raise ChannelContinuityError("cascade hop is disconnected from its predecessor")
        if (
            channel["active"] is not True
            or channel["from_position_id"] != source_id
            or channel["to_position_id"] != target_id
            or channel["identity_mapping"]["source_k_ref"] != source_id
            or channel["identity_mapping"]["target_k_ref"] != target_id
            or channel["identity_mapping"]["preserves_identity"] is not True
            or source_id not in channel["acl"]["authorized_position_ids"]
        ):
            raise ChannelContinuityError("cascade hop fails its real channel or identity")
        try:
            actual_threshold = _predicate_result(positions, channel["threshold"])
        except WorldVolumeError as error:
            raise ChannelContinuityError(
                f"cascade hop has an invalid actual channel threshold: {error}"
            ) from error
        if hop["threshold_met"] is not actual_threshold or not actual_threshold:
            raise ChannelContinuityError(
                "cascade hop fails its actual channel threshold"
            )

        hop_evidence = set(hop["evidence_refs"])
        if (
            not hop_evidence
            or not hop_evidence.issubset(set(channel["evidence_refs"]))
            or not set(channel["acl"]["authorization_evidence_refs"]).issubset(
                hop_evidence
            )
        ):
            raise ChannelContinuityError("cascade hop fails channel evidence or ACL")

        source_circle = source["circle_id"]
        target_circle = target["circle_id"]
        if source_circle != target_circle:
            relation_id = hop["boundary_relation_id"]
            relation = relations.get(relation_id) if relation_id is not None else None
            if (
                relation is None
                or relation["source_circle_ref"] != source_circle
                or relation["target_circle_ref"] != target_circle
            ):
                raise ChannelContinuityError(
                    "cross-circle cascade hop lacks its declared boundary relation"
                )
            if relation["channel_id"] != channel["channel_id"]:
                raise ChannelContinuityError(
                    "cross-circle boundary relation channel differs from the actual channel"
                )
            relation_evidence = set(relation["evidence_refs"])
            if (
                not relation_evidence
                or not relation_evidence.issubset(hop_evidence)
                or not relation_evidence.issubset(set(channel["evidence_refs"]))
            ):
                raise ChannelContinuityError(
                    "cross-circle boundary relation evidence does not reach the hop channel"
                )
        elif hop["boundary_relation_id"] is not None:
            relation = relations.get(hop["boundary_relation_id"])
            if relation is None:
                raise ChannelContinuityError("cascade hop names an unknown boundary relation")

        event = events.get(hop["event_id"])
        state_diff = state_diffs.get(hop["event_id"])
        if event is None or state_diff is None:
            raise ChannelContinuityError(
                "cascade hop does not bind a declared Omega event"
            )
        if hop["state_diff_id"] != state_diff.state_diff_id:
            raise ChannelContinuityError(
                "cascade hop does not bind the exact Omega StateDiff"
            )
        if (
            event["source_position_id"] != source_id
            or target_id not in event["target_position_ids"]
            or hop["channel_id"] not in event["channel_ids"]
            or target_id not in state_diff.changed_positions
        ):
            raise ChannelContinuityError(
                "cascade hop event and StateDiff do not bind its actual channel endpoints"
            )
        source_state_ids = {
            source["M_state"]["state_id"],
            source["Psi_state"]["state_id"],
        }
        target_state_ids = {
            target["M_state"]["state_id"],
            target["Psi_state"]["state_id"],
        }
        updated_state_ids = {
            update["state_id"]
            for field in ("M_updates", "Psi_updates")
            for update in event[field]
            if update["position_id"] == target_id
        }
        source_state_fields = {
            field
            for field in ("M_state", "Psi_state")
            if source[field]["state_id"] == hop["representation_parent_state_id"]
        }
        target_state_fields = {
            field
            for field in ("M_state", "Psi_state")
            if target[field]["state_id"] == hop["representation_output_state_id"]
        }
        updated_state_fields = {
            field.replace("_updates", "_state")
            for field in ("M_updates", "Psi_updates")
            if any(
                update["position_id"] == target_id
                and update["state_id"] == hop["representation_output_state_id"]
                for update in event[field]
            )
        }
        if (
            hop["representation_parent_state_id"] not in source_state_ids
            or hop["representation_output_state_id"] not in target_state_ids
            or hop["representation_output_state_id"] not in updated_state_ids
            or not source_state_fields
            or source_state_fields != target_state_fields
            or target_state_fields != updated_state_fields
        ):
            raise ChannelContinuityError(
                "cascade hop representation transition is not bound to its Omega event"
            )
        ordered_channels.append(channel["channel_id"])
        previous_target = target_id
    return tuple(ordered_channels)


__all__ = (
    "ChannelContinuityError",
    "TransformationError",
    "validate_cascade",
    "validate_transformations",
)
