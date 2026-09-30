"""Pure one-to-three-order recursive semantics grounded in v8.3."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .world_volume import (
    WorldVolumeError,
    _canonical_sha256,
    _native_snapshot,
    _validate_ontology_binding,
    _validate_schema,
    validate_world_volume,
    apply_registered_event,
)


BRANCH_KINDS = ("main", "strongest-rival", "mixture", "residual")
INHERITED_FIELDS = (
    "inherited_fact_ids",
    "inherited_evidence_ids",
    "inherited_unknown_ids",
    "inherited_loss_ids",
    "inherited_residual_ids",
)
GRADE_ORDER = {"unknown": 0, "low": 1, "medium": 2, "high": 3}
REQUIRED_RECURSION_ONTOLOGY = frozenset(
    {
        "V83-CANON-THREE-ORDER",
        "V83-CANON-CORE-BRANCH-PATH",
        "V83-CANON-CORE-COMMON-KERNEL",
    }
)


class RecursiveInferenceError(ValueError):
    """Raised when recursive state or lineage invents continuity or evidence."""


@dataclass(frozen=True, slots=True)
class LineageValidation:
    node_ids: tuple[str, ...]
    maximum_order: int
    early_stop_nodes: tuple[str, ...]
    not_run_orders: tuple[tuple[str, int], ...]
    inherited_unknown_ids: tuple[str, ...]
    inherited_residual_ids: tuple[str, ...]


def current_action_set(
    state: Mapping[str, Any], action_catalog: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    catalog = _native_snapshot(list(action_catalog), label="action catalog", error_type=RecursiveInferenceError)
    objects = {obj["object_id"]: obj for obj in state["objects"]}
    if not catalog or len({option.get("option_id") for option in catalog}) != len(catalog) or any(not option.get("option_id") for option in catalog):
        raise RecursiveInferenceError("action options require unique stable IDs")
    no_action = [option for option in catalog if option.get("option_kind") == "no_action"]
    if len(no_action) != 1:
        raise RecursiveInferenceError("action comparison requires exactly one no_action baseline")
    available, excluded = [], []
    for option in catalog:
        if option.get("target_object") not in objects or option.get("option_kind") not in {"no_action", "external_action"} or not option.get("action_type") or not isinstance(option.get("requirements"), list):
            raise RecursiveInferenceError("action option has an unregistered target, type or constraints")
        reasons = []
        for condition in option["requirements"]:
            obj = objects.get(condition.get("object_id"))
            variable = next((item for item in obj["variables"] if item["variable_id"] == condition.get("variable_id")), None) if obj else None
            if variable is None or not condition.get("source_refs"):
                raise RecursiveInferenceError("action restriction must bind a registered variable and its source")
            actual, operand, operator = variable["value"], condition.get("operand"), condition.get("operator")
            if operator == "eq":
                met = _canonical_sha256(actual) == _canonical_sha256(operand)
            elif operator in {"ge", "le"} and type(actual) in {int, float} and type(operand) in {int, float}:
                met = actual >= operand if operator == "ge" else actual <= operand
            else:
                raise RecursiveInferenceError("action restriction requires a typed supported comparator")
            if not met:
                reasons.append({"constraint": copy.deepcopy(condition), "actual_value": copy.deepcopy(actual), "status": "constraint_not_met"})
        if reasons:
            excluded.append({"option_id": option["option_id"], "reasons": reasons, "option": option})
        else:
            available.append(option)
    return {"available_actions": available, "excluded_actions": excluded, "no_action_option_id": no_action[0]["option_id"], "existing_obligations": copy.deepcopy(state.get("existing_obligations", []))}


def registered_parent_binding(parent: Mapping[str, Any]) -> dict[str, Any]:
    return {"run_id": parent["run_id"], "path_id": parent["path_id"], "node_id": parent["node_id"], "order": parent["order"], "node_sha256": _canonical_sha256(parent), "output_state_sha256": _canonical_sha256(parent["output_state"])}


def execute_recursive_step(
    parent: Mapping[str, Any], event: Mapping[str, Any], *,
    action_catalog: Sequence[Mapping[str, Any]], author: Any,
    evidence_registry: Mapping[str, Mapping[str, Any]],
    independent_question: str | None, incremental_gain: str | None,
    channel_registry: Mapping[str, Mapping[str, Any]] | None = None,
    authorization_registry: Mapping[str, Mapping[str, Any]] | None = None,
    proposed_input_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Call the next author with the actual replayed conditional state."""

    frozen = _native_snapshot(parent, label="recursive parent", error_type=RecursiveInferenceError)
    if not isinstance(frozen, dict) or type(frozen.get("order")) is not int or frozen["order"] not in {1, 2, 3} or frozen.get("declared_evidence_grade") not in GRADE_ORDER:
        raise RecursiveInferenceError("recursive parent order or evidence grade is invalid")
    binding = registered_parent_binding(frozen)
    if frozen.get("status") in {"stopped", "failed", "not_run"}:
        return {"status": "not_run", "order": frozen["order"] + 1, "blocked_by_node_id": frozen["node_id"], "reason": frozen.get("stop_reason", frozen.get("reason", "parent premise failed")), "parent_binding": binding}
    if not independent_question or not incremental_gain or frozen.get("status") == "completed":
        return {**frozen, "status": "completed", "completion_reason": "no_independent_next_question" if not independent_question else "no_incremental_gain", "parent_binding": binding}
    if frozen["order"] == 3:
        return {**frozen, "status": "completed", "completion_reason": "third_order_limit", "parent_binding": binding}
    if event.get("kind") == "observed" and frozen.get("evidence_identity") != "observed":
        raise RecursiveInferenceError("new observed feedback requires a new frozen run, not promotion of a simulated child")
    try:
        transition = apply_registered_event(frozen["output_state"], event, evidence_registry=evidence_registry, channel_registry=channel_registry, authorization_registry=authorization_registry)
        child_input = transition.replay(frozen["output_state"])
    except WorldVolumeError as error:
        raise RecursiveInferenceError(str(error)) from error
    if proposed_input_state is not None and _canonical_sha256(proposed_input_state) != _canonical_sha256(child_input):
        raise RecursiveInferenceError("proposed child input differs from the actual typed post-state")
    if not event.get("deltas") or _canonical_sha256(frozen["output_state"]) == _canonical_sha256(child_input):
        raise RecursiveInferenceError("next recursive step requires a substantive registered state change")
    action_state = current_action_set(child_input, action_catalog)
    request = {"parent_binding": binding, "order": frozen["order"] + 1, "independent_question": independent_question, "incremental_gain": incremental_gain, "input_state": child_input, "input_state_sha256": _canonical_sha256(child_input), "state_diff_id": transition.state_diff_id, "event_identity": transition.evidence_identity, "event_role": transition.event_role, "inherited_conditions": copy.deepcopy(frozen.get("conditions", [])), "new_conditions": copy.deepcopy(event.get("conditions", [])), "model_version": frozen["model_version"], "dimensions": copy.deepcopy(frozen.get("dimensions", {})), **action_state}
    request_hash = _canonical_sha256(request)
    response = _native_snapshot(author(copy.deepcopy(request)), label="next author response", error_type=RecursiveInferenceError)
    if not isinstance(response, dict) or set(response) - {"possible_choice_ids", "choice_basis", "rationale"}:
        raise RecursiveInferenceError("next author may only fill semantic choice fields")
    choices = response.get("possible_choice_ids", [])
    available_ids = {option["option_id"] for option in action_state["available_actions"]}
    if not isinstance(choices, list) or len(choices) != len(set(choices)) or not set(choices).issubset(available_ids):
        raise RecursiveInferenceError("author choice is not in the derived current action set")
    node_payload = {"parent": binding, "event": event, "request": request, "response": response}
    return {"node_id": "NODE-" + _canonical_sha256(node_payload)[:20].upper(), "path_id": frozen["path_id"], "run_id": frozen["run_id"], "order": request["order"], "status": "active", "input_state": child_input, "output_state": copy.deepcopy(child_input), "state_diff_id": transition.state_diff_id, "event_record": copy.deepcopy(event), "parent_binding": binding, "author_request": request, "author_request_sha256": request_hash, "author_response": response, "evidence_identity": "simulated", "event_identity": transition.evidence_identity, "declared_evidence_grade": frozen["declared_evidence_grade"], "model_version": frozen["model_version"], "conditions": [*copy.deepcopy(frozen.get("conditions", [])), *copy.deepcopy(event.get("conditions", []))], "history": [*copy.deepcopy(frozen.get("history", [])), event["event_id"]], "dimensions": request["dimensions"]}


def validate_registered_child(
    child: Mapping[str, Any], *, parent: Mapping[str, Any], event: Mapping[str, Any],
    action_catalog: Sequence[Mapping[str, Any]],
    evidence_registry: Mapping[str, Mapping[str, Any]],
    channel_registry: Mapping[str, Mapping[str, Any]] | None = None,
    authorization_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    snapshot = _native_snapshot(child, label="recursive child", error_type=RecursiveInferenceError)
    binding = registered_parent_binding(parent)
    if parent.get("status") not in {"active"} or snapshot.get("parent_binding") != binding or snapshot.get("order") != parent["order"] + 1 or snapshot["order"] > 3 or snapshot.get("node_id") == parent["node_id"]:
        raise RecursiveInferenceError("recursive child lacks exact immediate parent content continuity")
    if snapshot.get("event_record") != event:
        raise RecursiveInferenceError("recursive event content differs from its frozen record")
    try:
        transition = apply_registered_event(parent["output_state"], event, evidence_registry=evidence_registry, channel_registry=channel_registry, authorization_registry=authorization_registry)
        derived = transition.replay(parent["output_state"])
    except WorldVolumeError as error:
        raise RecursiveInferenceError(str(error)) from error
    if any(_canonical_sha256(snapshot.get(key)) != _canonical_sha256(derived) for key in ("input_state", "output_state")) or snapshot.get("state_diff_id") != transition.state_diff_id:
        raise RecursiveInferenceError("recursive state differs from the recomputed typed post-state")
    if snapshot.get("evidence_identity") != "simulated" or snapshot.get("declared_evidence_grade") != parent["declared_evidence_grade"] or snapshot.get("model_version") != parent["model_version"]:
        raise RecursiveInferenceError("recursive depth cannot promote evidence identity, grade or model version")
    for field in ("run_id", "path_id", "dimensions"):
        if snapshot.get(field) != parent.get(field):
            raise RecursiveInferenceError("recursive scope or orthogonal dimensions changed without a new binding")
    if snapshot.get("conditions") != [*parent.get("conditions", []), *event.get("conditions", [])] or snapshot.get("history") != [*parent.get("history", []), event["event_id"]]:
        raise RecursiveInferenceError("recursive child erased inherited conditions or history")
    request = snapshot.get("author_request")
    if not isinstance(request, dict) or snapshot.get("author_request_sha256") != _canonical_sha256(request):
        raise RecursiveInferenceError("actual author request content binding changed")
    actions = current_action_set(derived, action_catalog)
    expected_fields = {"parent_binding": binding, "order": snapshot["order"], "input_state": derived, "input_state_sha256": _canonical_sha256(derived), "state_diff_id": transition.state_diff_id, "event_identity": transition.evidence_identity, "event_role": transition.event_role, "inherited_conditions": parent.get("conditions", []), "new_conditions": event.get("conditions", []), "model_version": parent["model_version"], "dimensions": parent.get("dimensions", {}), **actions}
    if any(request.get(key) != value for key, value in expected_fields.items()) or not request.get("independent_question") or not request.get("incremental_gain"):
        raise RecursiveInferenceError("actual next author input or action set differs from the typed post-state")
    response = snapshot.get("author_response")
    if not isinstance(response, dict) or set(response) - {"possible_choice_ids", "choice_basis", "rationale"}:
        raise RecursiveInferenceError("recursive author response includes runtime control fields")
    choices = response.get("possible_choice_ids", [])
    if not isinstance(choices, list) or len(set(choices)) != len(choices) or not set(choices).issubset({option["option_id"] for option in actions["available_actions"]}):
        raise RecursiveInferenceError("recursive choice does not resolve the actual action set")
    expected_node_id = "NODE-" + _canonical_sha256({"parent": binding, "event": event, "request": request, "response": response})[:20].upper()
    if snapshot.get("node_id") != expected_node_id:
        raise RecursiveInferenceError("recursive node identity differs from its actual transition content")
    return snapshot


def _validate_identity_roles(state: Mapping[str, Any]) -> None:
    scalar_roles = {
        state["state_id"],
        state["node_id"],
        state["event_id"],
        state["state_diff_id"],
    }
    other_roles = (
        set(state["mechanism_ids"])
        | set(state["transformation_ids"])
        | set(state["signal_ids"])
    )
    if len(scalar_roles) != 4 or scalar_roles.intersection(other_roles):
        raise RecursiveInferenceError(
            "recursive state, node, event, diff, mechanism, and signal IDs must be distinct"
        )


def recursive_state_diff_id(
    state: Mapping[str, object],
    *,
    parent_states: Sequence[Mapping[str, object]],
) -> str:
    """Derive a deterministic deeper-order StateDiff identity from semantic fields."""

    payload = {
        key: state[key]
        for key in (
            "event_id",
            "parent_state_ids",
            "parent_node_ids",
            "input_state",
            "state_delta",
            "carrier",
            "scale_or_circle",
            "clock",
            "conditions",
            "evidence_refs",
            "countermechanism",
            "failure_condition",
            "early_signal",
            "reverse_signal",
            "writeback",
            "mechanism_ids",
            "transformation_ids",
            "parent_state_bindings",
        )
    }
    payload["resolved_parent_state_ids"] = sorted(
        str(parent["state_id"]) for parent in parent_states
    )
    return f"DIFF-RECURSIVE-{_canonical_sha256(payload)[:20].upper()}"


def recursive_parent_binding(parent: Mapping[str, object]) -> dict[str, str]:
    return {
        "state_id": str(parent["state_id"]),
        "state_sha256": _canonical_sha256(parent),
        "output_sha256": _canonical_sha256(
            {
                "status": parent["status"],
                "state_delta": parent["state_delta"],
                "early_signal": parent["early_signal"],
                "reverse_signal": parent["reverse_signal"],
            }
        ),
        "writeback_sha256": _canonical_sha256(parent["writeback"]),
    }


def validate_recursive_state(
    state: Mapping[str, object],
    *,
    parent_states: Sequence[Mapping[str, object]] = (),
    repository_root: Path | None = None,
) -> dict[str, Any]:
    """Validate one state and its exact immediate parents without mutation."""

    snapshot = _native_snapshot(
        state, label="recursive state", error_type=RecursiveInferenceError
    )
    raw_parents = _native_snapshot(
        list(parent_states),
        label="recursive state parents",
        error_type=RecursiveInferenceError,
    )
    if not isinstance(snapshot, dict) or not isinstance(raw_parents, list):
        raise RecursiveInferenceError("recursive state and parents must be JSON mappings")
    _validate_schema(
        "xk-recursive-state.schema.json",
        snapshot,
        label="recursive state",
        error_type=RecursiveInferenceError,
        repository_root=repository_root,
    )
    _validate_ontology_binding(
        snapshot,
        required=REQUIRED_RECURSION_ONTOLOGY,
        label="recursive state",
        error_type=RecursiveInferenceError,
        repository_root=repository_root,
    )
    _validate_identity_roles(snapshot)

    parent_ids = [parent["state_id"] for parent in raw_parents]
    parent_node_ids = [parent["node_id"] for parent in raw_parents]
    if len(parent_ids) != len(set(parent_ids)) or len(parent_node_ids) != len(
        set(parent_node_ids)
    ):
        raise RecursiveInferenceError("recursive state parents must be unique")
    if set(snapshot["parent_state_ids"]) != set(parent_ids) or set(
        snapshot["parent_node_ids"]
    ) != set(parent_node_ids):
        raise RecursiveInferenceError(
            "recursive state parent identities do not match the supplied parents"
        )
    expected_parent_bindings = sorted(
        (recursive_parent_binding(parent) for parent in raw_parents),
        key=lambda binding: binding["state_id"],
    )
    if snapshot["parent_state_bindings"] != expected_parent_bindings:
        raise RecursiveInferenceError(
            "recursive child parent content binding differs from state output or writeback"
        )

    if snapshot["order"] == 1:
        if raw_parents:
            raise RecursiveInferenceError("order-1 recursive state cannot have a parent")
        return snapshot
    if not raw_parents:
        raise RecursiveInferenceError("deeper recursive state requires an immediate parent")
    if any(parent["order"] != snapshot["order"] - 1 for parent in raw_parents):
        raise RecursiveInferenceError(
            "recursive state parents must be at the immediately preceding order"
        )
    terminal_statuses = {"stopped", "not-applicable"}
    if any(parent["status"] in terminal_statuses for parent in raw_parents):
        terminal = next(
            parent
            for parent in raw_parents
            if parent["status"] in terminal_statuses
        )
        status = terminal["status"]
        if any(parent["order"] == 2 for parent in raw_parents):
            raise RecursiveInferenceError(
                f"a {status} second order cannot be followed by a third-order story"
            )
        raise RecursiveInferenceError(
            f"a {status} recursive state cannot produce a child"
        )

    if snapshot["state_diff_id"] != recursive_state_diff_id(
        snapshot, parent_states=raw_parents
    ):
        raise RecursiveInferenceError(
            "deeper recursive StateDiff identity differs from its semantic transition"
        )

    for field in INHERITED_FIELDS:
        required = {
            identifier
            for parent in raw_parents
            for identifier in parent[field]
        }
        if not required.issubset(set(snapshot[field])):
            raise RecursiveInferenceError(
                f"child recursive state dropped inherited parent identity in {field}"
            )

    maximum_parent_grade = min(
        GRADE_ORDER[parent["declared_evidence_grade"]] for parent in raw_parents
    )
    if GRADE_ORDER[snapshot["declared_evidence_grade"]] > maximum_parent_grade:
        raise RecursiveInferenceError(
            "recursive depth cannot increase the declared evidence grade"
        )
    if snapshot["evidence_identity"] == "observed":
        raise RecursiveInferenceError(
            "simulated recursive depth cannot be relabelled as observed"
        )
    return snapshot


def _validate_nodes_and_states(
    lineage: Mapping[str, Any],
    recursive_states: Mapping[str, Mapping[str, object]],
    *,
    inherited_unknown_ids: set[str],
    inherited_residual_ids: set[str],
    repository_root: Path | None,
) -> dict[str, dict[str, Any]]:
    nodes = lineage["nodes"]
    node_ids = [node["node_id"] for node in nodes]
    state_ids = [node["state_id"] for node in nodes]
    if len(node_ids) != len(set(node_ids)) or len(state_ids) != len(set(state_ids)):
        raise RecursiveInferenceError("recursive lineage node and state IDs must be unique")
    by_node = {node["node_id"]: node for node in nodes}
    if set(recursive_states) != set(state_ids):
        raise RecursiveInferenceError(
            "every lineage node must resolve exactly one recursive state"
        )
    states_by_node: dict[str, dict[str, Any]] = {}
    for node in sorted(nodes, key=lambda item: item["order"]):
        state_value = recursive_states[node["state_id"]]
        if state_value.get("state_id") != node["state_id"]:
            raise RecursiveInferenceError(
                "recursive state registry key differs from its state identity"
            )
        parents: list[Mapping[str, object]] = []
        for parent_id in node["parent_node_ids"]:
            parent_node = by_node.get(parent_id)
            if parent_node is None or parent_id not in states_by_node:
                raise RecursiveInferenceError("recursive lineage parent does not resolve")
            if parent_node["order"] != node["order"] - 1:
                raise RecursiveInferenceError(
                    "recursive lineage parent must be at the immediately preceding order"
                )
            parents.append(states_by_node[parent_id])
        state = validate_recursive_state(
            state_value,
            parent_states=parents,
            repository_root=repository_root,
        )
        if (
            state["node_id"] != node["node_id"]
            or state["path_id"] != node["path_id"]
            or state["order"] != node["order"]
        ):
            raise RecursiveInferenceError(
                "lineage node identity differs from its recursive state"
            )
        if node["order"] == 1:
            if not inherited_unknown_ids.issubset(
                set(state["inherited_unknown_ids"])
            ):
                raise RecursiveInferenceError(
                    "order-1 state dropped Omega inherited_unknown_ids"
                )
            if not inherited_residual_ids.issubset(
                set(state["inherited_residual_ids"])
            ):
                raise RecursiveInferenceError(
                    "order-1 state dropped Omega inherited_residual_ids"
                )
        states_by_node[node["node_id"]] = state
    return states_by_node


def _validate_branches(
    lineage: Mapping[str, Any], states_by_node: Mapping[str, Mapping[str, Any]]
) -> tuple[tuple[str, ...], tuple[tuple[str, int], ...]]:
    nodes = {node["node_id"]: node for node in lineage["nodes"]}
    branches = lineage["branches"]
    branch_ids = [branch["branch_id"] for branch in branches]
    kinds = [branch["kind"] for branch in branches]
    if len(branch_ids) != len(set(branch_ids)):
        raise RecursiveInferenceError("recursive lineage branch IDs must be unique")
    if len(branches) != 4 or set(kinds) != set(BRANCH_KINDS):
        raise RecursiveInferenceError(
            "recursive lineage must preserve exactly the four branch kinds"
        )
    by_branch = {branch["branch_id"]: branch for branch in branches}
    covered: set[str] = set()
    early_stops: list[str] = []
    for branch in branches:
        branch_nodes = branch["node_ids"]
        if any(node_id not in nodes for node_id in branch_nodes):
            raise RecursiveInferenceError("branch references an unknown recursive node")
        branch_orders = [nodes[node_id]["order"] for node_id in branch_nodes]
        if branch["status"] != "merged" and branch_orders != list(
            range(1, len(branch_orders) + 1)
        ):
            raise RecursiveInferenceError(
                "non-merged branch must start at order one and remain continuous"
            )
        for parent_id, child_id in zip(branch_nodes, branch_nodes[1:]):
            if parent_id not in nodes[child_id]["parent_node_ids"]:
                raise RecursiveInferenceError("branch path is not parent-connected")
        covered.update(branch_nodes)
        terminal_id = branch_nodes[-1]
        terminal_state = states_by_node[terminal_id]
        terminal_order = nodes[terminal_id]["order"]
        if branch["status"] != "stopped" and terminal_state["status"] == "stopped":
            raise RecursiveInferenceError(
                "a stopped state cannot be relabelled as a non-stopped branch"
            )
        if branch["status"] in {"active", "merged"} and terminal_order != 3:
            raise RecursiveInferenceError(
                "active or merged branch must reach order 3"
            )
        if branch["status"] == "stopped":
            if terminal_state["status"] != "stopped" or not branch["stop_reason"]:
                raise RecursiveInferenceError(
                    "stopped branch must end at a state with an explicit stop reason"
                )
            if not branch["retained_residual_ids"] or not set(
                branch["retained_residual_ids"]
            ).issubset(set(terminal_state["inherited_residual_ids"])):
                raise RecursiveInferenceError(
                    "stopped branch must retain an inherited residual"
                )
            early_stops.append(terminal_id)
        else:
            if branch["stop_reason"] is not None:
                raise RecursiveInferenceError(
                    "non-stopped branch cannot carry a stop reason"
                )
        if branch["status"] == "pruned":
            if not branch["prune_reason"] or not branch["retained_residual_ids"]:
                raise RecursiveInferenceError(
                    "pruned branch requires a reason and retained residual"
                )
            if not set(branch["retained_residual_ids"]).issubset(
                set(terminal_state["inherited_residual_ids"])
            ):
                raise RecursiveInferenceError(
                    "pruned branch residual does not resolve to its validated terminal state"
                )
        elif branch["prune_reason"] is not None:
            raise RecursiveInferenceError("non-pruned branch cannot carry a prune reason")
        if branch["status"] == "merged":
            merge_parents = branch["merge_parent_branch_ids"]
            if (
                not merge_parents
                or branch["branch_id"] in merge_parents
                or any(parent_id not in by_branch for parent_id in merge_parents)
            ):
                raise RecursiveInferenceError("merged branch has invalid parent branches")
        elif branch["merge_parent_branch_ids"]:
            raise RecursiveInferenceError("non-merged branch cannot name merge parents")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit_merge(branch_id: str) -> None:
        if branch_id in visiting:
            raise RecursiveInferenceError("recursive merge graph contains a cycle")
        if branch_id in visited:
            return
        visiting.add(branch_id)
        for parent_id in by_branch[branch_id]["merge_parent_branch_ids"]:
            visit_merge(parent_id)
        visiting.remove(branch_id)
        visited.add(branch_id)

    for branch_id in by_branch:
        visit_merge(branch_id)
    if covered != set(nodes):
        raise RecursiveInferenceError(
            "every recursive node must belong to at least one declared branch"
        )
    declared_not_run: dict[tuple[str, int], Mapping[str, Any]] = {}
    for record in lineage["not_run_orders"]:
        key = (record["branch_id"], record["order"])
        if key in declared_not_run:
            raise RecursiveInferenceError("duplicate recursive not_run order")
        branch = by_branch.get(record["branch_id"])
        if branch is None:
            raise RecursiveInferenceError("not_run order references an unknown branch")
        terminal_node_id = branch["node_ids"][-1]
        if record["blocked_by_node_id"] != terminal_node_id:
            raise RecursiveInferenceError(
                "not_run order is not bound to the branch terminal node"
            )
        if record["order"] <= nodes[terminal_node_id]["order"]:
            raise RecursiveInferenceError(
                "not_run order cannot replace an executed recursive state"
            )
        declared_not_run[key] = record
    expected_not_run = {
        (branch["branch_id"], order)
        for branch in branches
        if branch["status"] in {"stopped", "pruned"}
        for order in range(nodes[branch["node_ids"][-1]]["order"] + 1, 4)
    }
    if set(declared_not_run) != expected_not_run:
        raise RecursiveInferenceError(
            "stopped branch must declare every downstream order as not_run"
        )
    return tuple(early_stops), tuple(sorted(expected_not_run))


def validate_recursive_lineage(
    lineage: Mapping[str, object],
    parent_volume: Mapping[str, object],
    *,
    recursive_states: Mapping[str, Mapping[str, object]],
    repository_root: Path | None = None,
) -> LineageValidation:
    """Validate the one-to-three-order DAG, its states, branches, and stops."""

    snapshot = _native_snapshot(
        lineage, label="recursive lineage", error_type=RecursiveInferenceError
    )
    world = _native_snapshot(
        parent_volume, label="parent Omega", error_type=RecursiveInferenceError
    )
    state_registry = _native_snapshot(
        recursive_states,
        label="recursive state registry",
        error_type=RecursiveInferenceError,
    )
    if (
        not isinstance(snapshot, dict)
        or not isinstance(world, dict)
        or not isinstance(state_registry, dict)
    ):
        raise RecursiveInferenceError("lineage, Omega, and state registry must be mappings")
    _validate_schema(
        "xk-recursive-lineage.schema.json",
        snapshot,
        label="recursive lineage",
        error_type=RecursiveInferenceError,
        repository_root=repository_root,
    )
    try:
        validate_world_volume(world, repository_root=repository_root)
    except WorldVolumeError as error:
        raise RecursiveInferenceError(f"invalid parent Omega: {error}") from error
    _validate_ontology_binding(
        snapshot,
        required=REQUIRED_RECURSION_ONTOLOGY,
        label="recursive lineage",
        error_type=RecursiveInferenceError,
        repository_root=repository_root,
    )
    if snapshot["world_volume_id"] != world["volume_id"]:
        raise RecursiveInferenceError("recursive lineage binds a different Omega")

    orders = {node["order"] for node in snapshot["nodes"]}
    maximum_order = max(orders)
    if orders != set(range(1, maximum_order + 1)):
        raise RecursiveInferenceError("recursive orders must be contiguous from order one")
    if snapshot["maximum_order"] != maximum_order:
        raise RecursiveInferenceError("maximum_order differs from the lineage nodes")
    inherited_unknown_ids = {
        record["unknown_id"] for record in world["unknowns"]
    }
    inherited_residual_ids = {
        record["residual_id"] for record in world["residuals"]
    }
    states_by_node = _validate_nodes_and_states(
        snapshot,
        state_registry,
        inherited_unknown_ids=inherited_unknown_ids,
        inherited_residual_ids=inherited_residual_ids,
        repository_root=repository_root,
    )
    early_stops, not_run_orders = _validate_branches(snapshot, states_by_node)
    return LineageValidation(
        node_ids=tuple(node["node_id"] for node in snapshot["nodes"]),
        maximum_order=maximum_order,
        early_stop_nodes=early_stops,
        not_run_orders=not_run_orders,
        inherited_unknown_ids=tuple(sorted(inherited_unknown_ids)),
        inherited_residual_ids=tuple(sorted(inherited_residual_ids)),
    )


__all__ = (
    "BRANCH_KINDS",
    "LineageValidation",
    "RecursiveInferenceError",
    "recursive_state_diff_id",
    "recursive_parent_binding",
    "validate_recursive_lineage",
    "validate_recursive_state",
)
