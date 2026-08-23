"""Cross-phase semantic authority for Xi-Kari XK5 through XK8."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .claims import validate_claim_graph
from .recursion import LineageValidation, validate_recursive_lineage
from .transformations import validate_transformations
from .world_volume import apply_event, validate_world_volume


class SemanticChainError(ValueError):
    """Raised when individually valid phase artifacts do not form one inference chain."""


@dataclass(frozen=True, slots=True)
class SemanticChainValidation:
    graph: dict[str, Any]
    recursive: LineageValidation
    state_diff_ids: tuple[str, ...]
    transformation_ids: tuple[str, ...]


def _transition_key(record: Mapping[str, Any]) -> tuple[str, str]:
    return str(record["event_id"]), str(record["state_diff_id"])


def validate_semantic_chain(
    *,
    world_volume: Mapping[str, object],
    transformation_ledger: Mapping[str, object],
    claim_mechanism_graph: Mapping[str, object],
    recursive_lineage: Mapping[str, object],
    recursive_states: Mapping[str, Mapping[str, object]],
    evidence_mode: str = "open-world",
    repository_root: Path | None = None,
) -> SemanticChainValidation:
    """Rebuild and validate the Omega-to-recursion authority chain."""

    validate_world_volume(world_volume, repository_root=repository_root)
    transformation_ids = validate_transformations(
        transformation_ledger,
        source_volume=world_volume,
        repository_root=repository_root,
    )
    graph = validate_claim_graph(
        claim_mechanism_graph,
        evidence_mode=evidence_mode,
        repository_root=repository_root,
    )
    recursive = validate_recursive_lineage(
        recursive_lineage,
        world_volume,
        recursive_states=recursive_states,
        repository_root=repository_root,
    )
    if graph["world_volume_id"] != world_volume["volume_id"]:
        raise SemanticChainError("XK7 graph binds a different XK5 Omega")

    state_diffs = {
        event["event_id"]: apply_event(
            world_volume, event, repository_root=repository_root
        )
        for event in world_volume["events"]
    }
    diff_pairs = {
        (event_id, state_diff.state_diff_id): state_diff
        for event_id, state_diff in state_diffs.items()
    }
    transforms = {
        record["transform_id"]: record
        for record in transformation_ledger["transformations"]
    }
    graph_evidence = {
        record["evidence_id"]: record for record in graph["evidence"]
    }
    mechanisms = {
        record["mechanism_id"]: record for record in graph["mechanisms"]
    }
    explanations = {
        record["explanation_id"]: record for record in graph["explanations"]
    }

    for mechanism in mechanisms.values():
        named_transforms = set(mechanism["transformation_ids"])
        if not named_transforms.issubset(transforms):
            raise SemanticChainError(
                "XK7 mechanism transformation reference does not resolve"
            )
        expected_transitions = {
            _transition_key(transition)
            for transform_id in named_transforms
            for transition in transforms[transform_id]["transition_refs"]
        }
        actual_transitions = {
            _transition_key(transition)
            for transition in mechanism["transition_refs"]
        }
        if actual_transitions != expected_transitions:
            raise SemanticChainError(
                "XK7 mechanism transition differs from its XK6 transformations"
            )
        required_evidence = {
            evidence_id
            for transform_id in named_transforms
            for evidence_id in transforms[transform_id]["evidence_refs"]
        }
        if not required_evidence.issubset(set(mechanism["evidence_refs"])):
            raise SemanticChainError(
                "XK7 mechanism evidence does not cover its XK6 transformations"
            )
        if not set(mechanism["evidence_refs"]).issubset(graph_evidence):
            raise SemanticChainError(
                "XK7 mechanism evidence reference does not resolve"
            )

    states_by_node = {
        state["node_id"]: state for state in recursive_states.values()
    }
    event_ids = [state["event_id"] for state in recursive_states.values()]
    diff_ids = [state["state_diff_id"] for state in recursive_states.values()]
    if len(event_ids) != len(set(event_ids)):
        raise SemanticChainError("XK8 recursive event identities must be unique")
    if len(diff_ids) != len(set(diff_ids)):
        raise SemanticChainError("XK8 recursive StateDiff identities must be unique")

    locations = {
        world_volume["volume_id"],
        *(record["actor_id"] for record in world_volume["actors"]),
        *(record["circle_id"] for record in world_volume["circles"]),
        *(record["position_id"] for record in world_volume["positions"]),
    }
    for state in recursive_states.values():
        evidence_refs = set(state["evidence_refs"])
        mechanism_ids = set(state["mechanism_ids"])
        state_transform_ids = set(state["transformation_ids"])
        if not evidence_refs.issubset(graph_evidence):
            raise SemanticChainError("XK8 evidence reference does not resolve")
        if not mechanism_ids.issubset(mechanisms):
            raise SemanticChainError("XK8 mechanism reference does not resolve")
        if not state_transform_ids.issubset(transforms):
            raise SemanticChainError("XK8 transformation reference does not resolve")
        if state["scale_or_circle"] not in locations:
            raise SemanticChainError("XK8 scale_or_circle does not resolve XK5 Omega")
        if state["order"] == 1:
            state_diff = diff_pairs.get((state["event_id"], state["state_diff_id"]))
            if state_diff is None:
                raise SemanticChainError(
                    "XK8 order-1 event and StateDiff reference does not resolve XK5"
                )
            if not set(state_diff.evidence_refs).issubset(evidence_refs):
                raise SemanticChainError(
                    "XK8 order-1 evidence does not cover its XK5 StateDiff"
                )
        if mechanism_ids:
            required_transforms = {
                transform_id
                for mechanism_id in mechanism_ids
                for transform_id in mechanisms[mechanism_id]["transformation_ids"]
            }
            if state_transform_ids != required_transforms:
                raise SemanticChainError(
                    "XK8 transformation set differs from its XK7 mechanisms"
                )
            required_evidence = {
                evidence_id
                for mechanism_id in mechanism_ids
                for evidence_id in mechanisms[mechanism_id]["evidence_refs"]
            }
            if not required_evidence.issubset(evidence_refs):
                raise SemanticChainError(
                    "XK8 evidence does not cover its XK7 mechanisms"
                )

    node_use_counts = Counter(
        node_id
        for branch in recursive_lineage["branches"]
        for node_id in branch["node_ids"]
    )
    terminal_owners: dict[str, str] = {}
    for branch in recursive_lineage["branches"]:
        explanation = explanations.get(branch["explanation_id"])
        if explanation is None:
            raise SemanticChainError("XK8 branch explanation reference does not resolve")
        if explanation["kind"] != branch["kind"]:
            raise SemanticChainError(
                "XK8 branch kind differs from its XK7 explanation kind"
            )
        shared_nodes = {
            node_id
            for node_id in branch["node_ids"]
            if node_use_counts[node_id] > 1
        }
        if any(states_by_node[node_id]["mechanism_ids"] for node_id in shared_nodes):
            raise SemanticChainError(
                "XK8 shared branch node cannot carry a branch-specific mechanism"
            )
        exclusive_nodes = [
            node_id
            for node_id in branch["node_ids"]
            if node_use_counts[node_id] == 1
        ]
        if not exclusive_nodes:
            raise SemanticChainError("XK8 branch requires an exclusive semantic path")
        actual_mechanisms = {
            mechanism_id
            for node_id in exclusive_nodes
            for mechanism_id in states_by_node[node_id]["mechanism_ids"]
        }
        if actual_mechanisms != set(explanation["mechanism_ids"]):
            raise SemanticChainError(
                "XK8 branch mechanism set differs from its XK7 explanation"
            )
        if branch["kind"] == "residual":
            required_residuals = set(explanation["residual_ids"])
            if not required_residuals.issubset(branch["retained_residual_ids"]):
                raise SemanticChainError(
                    "XK8 residual branch dropped its XK7 residual explanation"
                )
        terminal_id = branch["node_ids"][-1]
        if branch["status"] != "merged":
            previous = terminal_owners.setdefault(terminal_id, branch["branch_id"])
            if previous != branch["branch_id"]:
                raise SemanticChainError(
                    "XK8 independent branches cannot share one terminal node"
                )

    return SemanticChainValidation(
        graph=graph,
        recursive=recursive,
        state_diff_ids=tuple(sorted(diff.state_diff_id for diff in state_diffs.values())),
        transformation_ids=tuple(transformation_ids),
    )


__all__ = (
    "SemanticChainError",
    "SemanticChainValidation",
    "validate_semantic_chain",
)
