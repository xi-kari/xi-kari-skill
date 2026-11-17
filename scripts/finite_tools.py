#!/usr/bin/env python3
"""Validate and compute explicitly supplied finite models, using Python 3.10+.

Results concern the supplied model, never certify its real-world completeness,
permissions, causal effectiveness, or the source theory. Standard library only.
"""

from __future__ import annotations

import argparse
from collections import deque
from decimal import Decimal, DecimalException
from fractions import Fraction
from itertools import combinations, product
import hashlib
import io
import json
import math
import os
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from xikari_paths import require_external_output
finally:
    sys.path.pop(0)

FORMAT = "xikari-finite-tools-1"
MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_OUTPUT_BYTES = 32 * 1024 * 1024
NOTICE = ("仅对所列有限模型作条件计算；不认证理论、现实资料、因果机制、权限或实践效果。")


class InputError(ValueError):
    """The supplied finite model does not meet this tool's contract."""


def _names(values, label, *, nonempty=True):
    if not isinstance(values, (list, tuple)):
        raise InputError(f"{label} must be a list or tuple")
    if len(values) > 256:
        raise InputError(f"{label} exceeds the 256 identifier limit")
    if nonempty and not values:
        raise InputError(f"{label} must not be empty")
    if any(not isinstance(v, str) or not v.strip() or len(v) > 256 for v in values):
        raise InputError(f"{label} must contain nonempty string identifiers")
    if len(set(values)) != len(values):
        raise InputError(f"{label} contains duplicate identifiers")
    return list(values)


def _texts(values, label, *, max_items=256, max_length=4000):
    """Prose statements such as assumptions: nonempty, distinct and bounded."""
    if not isinstance(values, list) or not values or len(values) > max_items:
        raise InputError(f"{label} must be a nonempty list of at most {max_items} statements")
    if any(not isinstance(v, str) or not v.strip() or len(v) > max_length for v in values):
        raise InputError(f"{label} must contain nonempty statements of at most {max_length} characters each")
    if len(set(values)) != len(values):
        raise InputError(f"{label} contains duplicate statements")
    return list(values)


def _mapping(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise InputError(f"{label} must define exactly the declared keys")


def _scalar(value):
    # Numeric equality is mathematical; booleans remain a different type.
    if value is None:
        raise InputError("unknown/null task values are unsupported; supply known values or retain an unresolved model")
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, str):
        return ("string", value)
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise InputError("numeric values must be finite")
        return ("number", Fraction(str(value)))
    raise InputError("task outputs and decoder values must be JSON scalars")


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _quantity(value):
    """Keep an exact decimal-rational value even outside float range."""
    exact = str(value.numerator) if value.denominator == 1 else str(value)
    try:
        approx = float(value)
    except OverflowError:
        approx = None
    if approx is not None and not math.isfinite(approx):
        approx = None
    return {"exact": exact, "value": approx}


def _partition(states, signatures):
    buckets = {}
    for state in states:
        buckets.setdefault(signatures[state], []).append(state)
    return list(buckets.values())


def _block_ids(blocks):
    return {state: i for i, block in enumerate(blocks) for state in block}


def _shortest_word(left, right, actions, transitions, task, horizon):
    queue = deque([(left, right, [])])
    seen = {(left, right)}
    while queue:
        a, b, word = queue.popleft()
        if task[a] != task[b]:
            return word
        if horizon is not None and len(word) >= horizon:
            continue
        for action in actions:
            pair = (transitions[a][action], transitions[b][action])
            if pair not in seen:
                seen.add(pair)
                queue.append((pair[0], pair[1], word + [action]))
    return None


def f6_task_partition(states, actions, transitions, query=None, H=None, *, queries=None, _validate_only=False):
    """Coarsest partition preserving a task family after words of length <= H.

    All declared actions must be deterministic and defined at every state.
    H=None computes the stable partition. Refinement is synchronous.
    Supply query (one state-to-answer map), or queries (task ID to such a map).
    Empty actions preserve only current tasks; queries={} declares no tasks.
    """
    states = _names(states, "states")
    actions = _names(actions, "actions", nonempty=False)
    if len(states) > 64 or len(actions) > 16:
        raise InputError("task_partition supports at most 64 states and 16 actions")
    if H is not None and (isinstance(H, bool) or not isinstance(H, int) or H < 0):
        raise InputError("H must be a nonnegative integer or None")
    _mapping(transitions, states, "transitions")
    if query is not None and queries is not None:
        raise InputError("supply query or queries, not both")
    if queries is None:
        if query is None:
            raise InputError("supply query or explicitly declare queries={}")
        queries = {"query": query}
    if not isinstance(queries, dict):
        raise InputError("queries must map task identifiers to state-to-answer mappings")
    query_ids = _names(list(queries), "query identifiers", nonempty=False)
    if len(query_ids) > 32:
        raise InputError("task_partition supports at most 32 queries")
    for query_id in query_ids:
        _mapping(queries[query_id], states, f"queries[{query_id}]")
    task = {state: tuple(_scalar(queries[q][state]) for q in query_ids) for state in states}
    for state in states:
        _mapping(transitions[state], actions, f"transitions[{state}]")
        if any(target not in states for target in transitions[state].values()):
            raise InputError("every transition target must be a declared state")
    if _validate_only:
        return
    blocks = _partition(states, task)
    history = [{"h": 0, "blocks": blocks}]
    rounds = 0
    stable = False
    while H is None or rounds < H:
        old_ids = _block_ids(blocks)
        signatures = {
            state: (old_ids[state], tuple(old_ids[transitions[state][a]] for a in actions))
            for state in states
        }
        refined = _partition(states, signatures)
        rounds += 1
        history.append({"h": rounds, "blocks": refined})
        stable = refined == blocks
        blocks = refined
        if stable:
            break
    ids = _block_ids(blocks)
    closed = all(
        len({ids[transitions[state][action]] for state in block}) == 1
        for block in blocks for action in actions
    )
    witnesses = []
    for left, right in combinations(states, 2):
        if ids[left] == ids[right]:
            continue
        word = _shortest_word(left, right, actions, transitions, task, H)
        if word is None:
            raise RuntimeError("internal error: separated pair has no witness")
        lpath, rpath = [left], [right]
        for action in word:
            lpath.append(transitions[lpath[-1]][action])
            rpath.append(transitions[rpath[-1]][action])
        differences = [
            {"query_id": q, "left_answer": queries[q][lpath[-1]],
             "right_answer": queries[q][rpath[-1]]}
            for q in query_ids
            if _scalar(queries[q][lpath[-1]]) != _scalar(queries[q][rpath[-1]])
        ]
        witnesses.append({
            "states": [left, right], "shortest_action_word": word,
            "length": len(word), "left_path": lpath, "right_path": rpath,
            "query_id": differences[0]["query_id"],
            "terminal_queries": [differences[0]["left_answer"], differences[0]["right_answer"]],
            "distinguishing_queries": differences,
            "left_query_vector": {q: queries[q][lpath[-1]] for q in query_ids},
            "right_query_vector": {q: queries[q][rpath[-1]] for q in query_ids},
        })
    return {
        "contract": "F6 finite deterministic task partition", "requested_H": H,
        "query_ids": query_ids, "empty_task_family": not query_ids,
        "empty_action_set": not actions,
        "computed_refinement_rounds": rounds, "blocks": blocks,
        "history": history, "dynamically_closed": closed,
        "stable_partition": closed, "separated_pairs": witnesses,
        "scope": "All declared queries after action words up to H; all finite words when H is null. "
                 "Finite-horizon sufficiency alone does not imply dynamic closure. "
                 "Empty actions allow only the empty word; an empty task family imposes no task distinctions.",
    }


def f1_representation_audit(representation, query, actual_decoder=None, *, _validate_only=False):
    """Find same-representation/different-query pairs and audit a given decoder.

    Representation identifiers are strings. Query/decoder outputs are finite
    JSON scalars. Scalar minimax bounds use unrestricted real decoder outputs.
    """
    if not isinstance(representation, dict):
        raise InputError("representation must be a state-to-identifier mapping")
    states = _names(list(representation), "states")
    _mapping(query, states, "query")
    if any(not isinstance(v, str) or not v.strip() for v in representation.values()):
        raise InputError("representation values must be nonempty string identifiers")
    tokens = {state: _scalar(query[state]) for state in states}
    fibers = {}
    for state in states:
        fibers.setdefault(representation[state], []).append(state)
    if actual_decoder is not None:
        _mapping(actual_decoder, fibers, "actual_decoder")
        for value in actual_decoder.values():
            _scalar(value)
    if _validate_only:
        return
    numeric = all(_number(query[state]) for state in states)
    conflicts, fiber_results, rule_errors = [], [], []
    radii, actual_abs = [], []
    for label, members in fibers.items():
        ambiguous = len({tokens[state] for state in members}) > 1
        record = {"representation": label, "states": members,
                  "identifiable": not ambiguous}
        for left, right in combinations(members, 2):
            if tokens[left] != tokens[right]:
                conflicts.append({"states": [left, right], "representation": label,
                                  "query_values": [query[left], query[right]]})
        if numeric:
            numbers = [Fraction(str(query[state])) for state in members]
            lo, hi = min(numbers), max(numbers)
            radius, center = (hi - lo) / 2, (hi + lo) / 2
            radii.append(radius)
            record["scalar_minimax"] = {
                "minimum": _quantity(lo), "maximum": _quantity(hi),
                "optimal_unrestricted_real_value": _quantity(center),
                "unavoidable_worst_case_error": _quantity(radius),
            }
        if actual_decoder is not None:
            decoded = actual_decoder[label]
            for state in members:
                if _scalar(decoded) != tokens[state]:
                    rule_errors.append({
                        "state": state, "representation": label,
                        "query": query[state], "decoded": decoded,
                        "fiber_ambiguous": ambiguous,
                        "information_sufficient_but_rule_wrong": not ambiguous,
                    })
                if numeric and _number(decoded):
                    actual_abs.append(abs(Fraction(str(decoded)) - Fraction(str(query[state]))))
        fiber_results.append(record)
    scalar_summary = None
    if numeric:
        scalar_summary = {
            "metric": "absolute_error", "decoder_domain": "unrestricted real values",
            "minimum_possible_global_worst_case_error": _quantity(max(radii)),
            "actual_decoder_global_worst_case_error": (
                _quantity(max(actual_abs)) if actual_decoder is not None
                and len(actual_abs) == len(states) else None
            ),
            "number_semantics": "Finite numeric inputs interpreted as their decimal strings.",
        }
    return {
        "contract": "F1 finite representation audit", "fibers": fiber_results,
        "query_identifiable_from_representation": not conflicts,
        "conflict_pairs": conflicts, "scalar_error_bound": scalar_summary,
        "actual_decoder_supplied": actual_decoder is not None,
        "actual_decoder_correct_on_all_states": (
            not rule_errors if actual_decoder is not None else None
        ),
        "actual_decoder_errors": rule_errors,
        "scope": "Ambiguous fibers and wrong decoding rules may coexist. "
                 "The scalar bound concerns only this supplied finite state set.",
    }


def f3_common_actions(admissible, action_universe, observation=None, *, _validate_only=False):
    """Intersect admissible actions over a given compatible finite state set.

    A nonempty declared action universe fixes the empty-family convention.
    Observation is a pre-given deterministic state-to-label map, not an
    optimized observation or a claim of real-world observability.
    """
    if not isinstance(admissible, dict):
        raise InputError("admissible must be a state-to-action-list mapping")
    states = _names(list(admissible), "states")
    actions = _names(action_universe, "action_universe")
    universe = set(actions)
    sets = {}
    for state in states:
        sets[state] = set(_names(admissible[state], f"admissible[{state}]", nonempty=False))
        if not sets[state] <= universe:
            raise InputError("admissible actions must belong to action_universe")

    if observation is not None:
        _mapping(observation, states, "observation")
        if any(not isinstance(v, str) or not v.strip() or len(v) > 256
               for v in observation.values()):
            raise InputError("observation labels must be nonempty strings of at most 256 characters")
    if _validate_only:
        return

    def common(members):
        result = universe.copy()
        for state in members:
            result &= sets[state]
        return result

    def ordered(values):
        return [action for action in actions if action in values]

    shared = common(states)
    core = None
    deletion_witnesses = None
    if not shared:
        core = list(states)
        for state in states:
            trial = [other for other in core if other != state]
            if not common(trial):
                core = trial
        deletion_witnesses = {
            state: ordered(common([other for other in core if other != state]))
            for state in core
        }
    groups = None
    sufficient = None
    if observation is not None:
        _mapping(observation, states, "observation")
        raw_groups = {}
        for state in states:
            label = observation[state]
            if not isinstance(label, str) or not label.strip():
                raise InputError("observation labels must be nonempty strings")
            raw_groups.setdefault(label, []).append(state)
        groups = [
            {"observation": label, "states": members,
             "common_actions": ordered(common(members))}
            for label, members in raw_groups.items()
        ]
        sufficient = all(group["common_actions"] for group in groups)
    return {
        "contract": "F3 finite common-action intersection",
        "common_actions": ordered(shared),
        "every_state_has_some_action": all(bool(sets[state]) for state in states),
        "inclusion_minimal_empty_intersection_states": core,
        "core_deletion_common_actions": deletion_witnesses,
        "minimality": "inclusion-minimal; not necessarily minimum cardinality",
        "observation_groups": groups,
        "observation_sufficient_for_groupwise_common_action": sufficient,
        "scope": "Only the supplied compatible states and declared admissibility. "
                 "No optimality, probability, information value, or authorization is inferred.",
    }


def _fields(value, required, optional=(), *, label="object"):
    if not isinstance(value, dict):
        raise InputError(f"{label} must be an object")
    missing = set(required) - set(value)
    extra = set(value) - set(required) - set(optional)
    if missing or extra:
        raise InputError(f"{label}: missing fields {sorted(missing)}; unsupported fields {sorted(extra)}")


def _integer(value, label, lower=0, upper=1_000_000):
    if isinstance(value, bool) or not isinstance(value, int) or not lower <= value <= upper:
        raise InputError(f"{label} must be an integer in [{lower}, {upper}], not unknown or boolean")
    return value


def _boolean(value, label):
    if not isinstance(value, bool):
        raise InputError(f"{label} must be an explicit boolean; unknown is not false")


def _records(value, label, maximum, *, nonempty=False):
    if not isinstance(value, list) or len(value) > maximum or (nonempty and not value):
        raise InputError(f"{label} must be a {'nonempty ' if nonempty else ''}list of at most {maximum} records")
    if any(not isinstance(record, dict) for record in value):
        raise InputError(f"{label} must contain objects")
    _names([record.get("id") for record in value], label + " IDs", nonempty=nonempty)


def _capacity_certificate(tasks, starts_by_task, resource_ids, capacities):
    """Sound infeasibility proof found before search, or None.

    Every allowed placement of a task lies inside the span from its earliest
    allowed start to its latest allowed finish. Tasks whose span lies inside
    [a, b) must use demand x duration of a resource there; if that exceeds the
    calendar's total capacity in [a, b), no schedule exists. A None result
    proves nothing; the complete search still decides.
    """
    spans = {task["id"]: (min(starts_by_task[task["id"]]),
                          max(starts_by_task[task["id"]]) + task["duration"]) for task in tasks}
    edges = sorted({edge for span in spans.values() for edge in span})
    for resource in resource_ids:
        prefix = [0]
        for value in capacities[resource]:
            prefix.append(prefix[-1] + value)
        for index, left in enumerate(edges):
            for right in edges[index + 1:]:
                inside = [task for task in tasks if task["demands"][resource]
                          and spans[task["id"]][0] >= left and spans[task["id"]][1] <= right]
                required = sum(task["demands"][resource] * task["duration"] for task in inside)
                available = prefix[right] - prefix[left]
                if required > available:
                    return {"resource_id": resource, "interval": [left, right], "required": required,
                            "available": available, "task_ids": [task["id"] for task in inside]}
    return None


def resource_schedule(horizon, resources, tasks, search_budget, *, _validate_only=False):
    """Exact finite search over declared integer starts; tasks are nonpreemptive.

    Each task has a fixed demand vector, qualification/authorization/material
    flags, release time, finish deadline and finish-to-start predecessors.
    No assignment of people, splitting, uncertain durations or optimization.
    """
    _integer(horizon, "horizon", 1, 256)
    _integer(search_budget, "search_budget")
    _records(resources, "resources", 16)
    _records(tasks, "tasks", 20)
    resource_ids = [resource["id"] for resource in resources]
    capacities = {}
    for resource in resources:
        _fields(resource, ("id", "capacity"), label="resource")
        values = resource["capacity"]
        if not isinstance(values, list) or len(values) != horizon:
            raise InputError("each resource capacity must cover exactly horizon slots")
        for value in values:
            _integer(value, "resource capacity")
        capacities[resource["id"]] = values
    task_ids = [task["id"] for task in tasks]
    task_by_id = {task["id"]: task for task in tasks}
    for task in tasks:
        _fields(task, ("id", "duration", "start_slots", "demands", "predecessors",
                       "ready_at", "end_by", "eligible", "authorized", "materials_ready"), label="task")
        _integer(task["duration"], "duration", 1, 256)
        _integer(task["ready_at"], "ready_at", 0, horizon)
        _integer(task["end_by"], "end_by", 0, horizon)
        starts = task["start_slots"]
        if not isinstance(starts, list) or len(starts) > horizon:
            raise InputError("start_slots must be a list with at most horizon entries")
        for start in starts:
            _integer(start, "start slot", 0, horizon - 1)
        if len(set(starts)) != len(starts):
            raise InputError("start_slots contains duplicates")
        _mapping(task["demands"], resource_ids, "demands (explicit zero required for unused resources)")
        for demand in task["demands"].values():
            _integer(demand, "resource demand")
        predecessors = _names(task["predecessors"], "predecessors", nonempty=False)
        if any(predecessor not in task_by_id or predecessor == task["id"] for predecessor in predecessors):
            raise InputError("predecessors must name other declared tasks")
        for flag in ("eligible", "authorized", "materials_ready"):
            _boolean(task[flag], flag)
    # Fixed topological traversal is complete: start times remain freely chosen
    # from each task's finite menu, including times before independent tasks.
    ordered = []
    pending = list(task_ids)
    while pending:
        available = [name for name in pending
                     if set(task_by_id[name]["predecessors"]) <= set(ordered)]
        if not available:
            raise InputError("predecessor cycle is outside this finish-to-start model")
        ordered.extend(available)
        pending = [name for name in pending if name not in available]
    if _validate_only:
        return
    starts_by_task = {}
    blockers = []
    for name in ordered:
        task = task_by_id[name]
        flags = all(task[flag] for flag in ("eligible", "authorized", "materials_ready"))
        candidates = [start for start in task["start_slots"]
                      if flags and start >= task["ready_at"]
                      and start + task["duration"] <= task["end_by"]
                      and all(task["demands"][resource] <= capacities[resource][slot]
                              for resource in resource_ids
                              for slot in range(start, start + task["duration"]))]
        starts_by_task[name] = candidates
        if not candidates:
            blockers.append(name)
    usage = {resource: [0] * horizon for resource in resource_ids}
    assignment = {}
    attempts = 0
    exhausted = False

    def search(index):
        nonlocal attempts, exhausted
        if index == len(ordered):
            return True
        name = ordered[index]
        task = task_by_id[name]
        for start in starts_by_task[name]:
            if attempts >= search_budget:
                exhausted = True
                return False
            attempts += 1
            end = start + task["duration"]
            if any(assignment[pred][1] > start for pred in task["predecessors"]):
                continue
            if any(usage[resource][slot] + task["demands"][resource] > capacities[resource][slot]
                   for resource in resource_ids for slot in range(start, end)):
                continue
            assignment[name] = (start, end)
            for resource in resource_ids:
                for slot in range(start, end):
                    usage[resource][slot] += task["demands"][resource]
            if search(index + 1):
                return True
            del assignment[name]
            for resource in resource_ids:
                for slot in range(start, end):
                    usage[resource][slot] -= task["demands"][resource]
            if exhausted:
                return False
        return False

    certificate = None if blockers else _capacity_certificate(tasks, starts_by_task, resource_ids, capacities)
    found = False if blockers or certificate else search(0)
    status = "feasible_in_model" if found else "search_incomplete" if exhausted else "infeasible_in_model"
    return {
        "contract": "finite integer-slot nonpreemptive resource schedule", "status": status,
        "attempted_starts": attempts, "search_budget": search_budget,
        "decision_complete": not exhausted, "tasks_without_individual_start": blockers,
        "capacity_certificate": certificate,
        "schedule": ([{"task_id": name, "start": assignment[name][0], "end": assignment[name][1],
                       "demands": task_by_id[name]["demands"]} for name in task_ids] if found else None),
        "resource_usage": usage if found else None,
        "scope": "Only listed starts, integer half-open intervals [start,end), fixed demands and explicit flags. "
                 "All declared tasks must finish by their individual deadlines. No unlisted resource, "
                 "person assignment, authority, review quality or actual intervention is inferred. "
                 "Infeasibility concerns this finite model; an exhausted budget does not prove infeasibility. "
                 "A capacity certificate shows tasks that must run inside one interval needing more of a resource "
                 "than its calendar offers there.",
    }


def condition_search(variables, admissible_assignments, admissible_table_complete,
                     search_budget, *, _validate_only=False):
    """Search finite condition menus under a caller-declared complete truth table.

    Fixed variables cannot change. Minimality concerns inclusion of changed
    variable IDs, not cost, change magnitude or the number of changed variables.
    """
    _records(variables, "variables", 16, nonempty=True)
    _integer(search_budget, "search_budget")
    if admissible_table_complete is not True:
        raise InputError("admissible_table_complete must be true; an incomplete table cannot make omissions false")
    ids = [variable["id"] for variable in variables]
    menus, current, immutable = {}, {}, set()
    full_size = 1
    for variable in variables:
        _fields(variable, ("id", "current", "values", "mutable"), label="variable")
        _boolean(variable["mutable"], "mutable")
        values = variable["values"]
        if not isinstance(values, list) or not 1 <= len(values) <= 16:
            raise InputError("each values menu must contain 1 to 16 known scalars")
        tokens = [_scalar(value) for value in values]
        if len(set(tokens)) != len(tokens):
            raise InputError("values menu contains duplicate values")
        now = _scalar(variable["current"])
        if now not in tokens:
            raise InputError("current value must belong to its declared values menu")
        menus[variable["id"]] = set(tokens)
        current[variable["id"]] = now
        if not variable["mutable"]:
            immutable.add(variable["id"])
        full_size *= len(values) if variable["mutable"] else 1
    if full_size > 1_000_000:
        raise InputError("mutable menu product exceeds 1,000,000 assignments")
    if not isinstance(admissible_assignments, list) or len(admissible_assignments) > 4096:
        raise InputError("admissible_assignments must be a list of at most 4096 complete assignments")
    accepted = set()
    for assignment in admissible_assignments:
        _mapping(assignment, ids, "admissible assignment")
        tokens = tuple(_scalar(assignment[name]) for name in ids)
        if any(token not in menus[name] for name, token in zip(ids, tokens)):
            raise InputError("admissible assignment contains a value outside its declared menu")
        if tokens in accepted:
            raise InputError("admissible table contains duplicate assignments")
        accepted.add(tokens)
    if _validate_only:
        return
    domains = [variable["values"] if variable["mutable"] else [variable["current"]]
               for variable in variables]
    feasible = []
    examined = 0
    for values in product(*domains):
        if examined >= search_budget:
            break
        examined += 1
        tokens = tuple(_scalar(value) for value in values)
        if tokens in accepted:
            changes = [name for name, token in zip(ids, tokens) if token != current[name]]
            feasible.append({"assignment": dict(zip(ids, values)), "changed_variables": changes})
    complete = examined == full_size
    minimal = None
    if complete:
        change_sets = {frozenset(candidate["changed_variables"]) for candidate in feasible}
        minimal_sets = set()
        for changes in sorted(change_sets, key=len):
            if not any(smaller < changes for smaller in minimal_sets):
                minimal_sets.add(changes)
        minimal = [candidate for candidate in feasible
                   if frozenset(candidate["changed_variables"]) in minimal_sets]
    return {
        "contract": "finite condition menu with complete caller-supplied admissibility table",
        "status": ("search_incomplete" if not complete else
                   "feasible_in_model" if feasible else "infeasible_in_model"),
        "search_complete": complete, "menu_assignments": full_size, "examined_assignments": examined,
        "search_budget": search_budget, "fixed_variables": [name for name in ids if name in immutable],
        "found_feasible_assignments": feasible, "inclusion_minimal_changes": minimal,
        "minimality": "inclusion of changed variable IDs; not minimum count, cost or magnitude",
        "scope": "Only the declared menus and complete admissibility table. Missing table rows mean inadmissible "
                 "only under that explicit completeness assumption. Values and effects are not discovered, "
                 "and fixed conditions are never relaxed. Partial search does not establish global minimality.",
    }


def relation_chain(layers, relations, *, _validate_only=False):
    """Natural-join a finite chain, requiring the same intermediate object IDs."""
    _records(layers, "layers", 32, nonempty=True)
    if len(layers) < 2:
        raise InputError("relation_chain needs at least two layers")
    _records(relations, "relations", 31, nonempty=True)
    if len(relations) != len(layers) - 1:
        raise InputError("one relation is required for each consecutive layer pair")
    members = {}
    for layer in layers:
        _fields(layer, ("id", "members"), label="layer")
        members[layer["id"]] = set(_names(layer["members"], "layer members", nonempty=False))
    for index, relation in enumerate(relations):
        _fields(relation, ("id", "from_layer", "to_layer", "pairs"), label="relation")
        if relation["from_layer"] != layers[index]["id"] or relation["to_layer"] != layers[index + 1]["id"]:
            raise InputError("relations must connect their declared consecutive layers in order")
        pairs = relation["pairs"]
        if not isinstance(pairs, list) or len(pairs) > 4096:
            raise InputError("relation pairs must be a list of at most 4096 pairs")
        seen = set()
        for pair in pairs:
            if (not isinstance(pair, list) or len(pair) != 2
                    or any(not isinstance(value, str) for value in pair)):
                raise InputError("each relation pair must contain two declared string member IDs")
            if pair[0] not in members[relation["from_layer"]] or pair[1] not in members[relation["to_layer"]]:
                raise InputError("relation pair references a member outside its layer")
            if tuple(pair) in seen:
                raise InputError("relation contains duplicate pairs")
            seen.add(tuple(pair))
    if _validate_only:
        return
    reachable = set(layers[0]["members"])
    reachability = [{"layer_id": layers[0]["id"], "members": list(layers[0]["members"])}]
    parents = []
    first_break = None
    for index, relation in enumerate(relations):
        parent = {}
        for left, right in relation["pairs"]:
            if left in reachable:
                parent.setdefault(right, left)
        next_members = [value for value in layers[index + 1]["members"] if value in parent]
        if not next_members and first_break is None:
            first_break = {
                "relation_id": relation["id"], "from_layer": relation["from_layer"],
                "reachable_sources": [value for value in layers[index]["members"] if value in reachable],
                "relation_sources": [value for value in layers[index]["members"]
                                     if any(pair[0] == value for pair in relation["pairs"])],
                "reason": "No relation pair starts at a source reachable from the first layer.",
            }
        parents.append(parent)
        reachable = set(next_members)
        reachability.append({"layer_id": layers[index + 1]["id"], "members": next_members})
    witness = None
    if reachable:
        path = [reachability[-1]["members"][0]]
        for parent in reversed(parents):
            path.append(parent[path[-1]])
        path.reverse()
        witness = [{"layer_id": layer["id"], "member_id": value} for layer, value in zip(layers, path)]
    all_nonempty = all(relation["pairs"] for relation in relations)
    return {
        "contract": "finite layered binary relation natural join",
        "status": "joint_witness_found" if witness is not None else "no_joint_witness",
        "all_local_relations_nonempty": all_nonempty,
        "local_existence_counterexample": all_nonempty and witness is None,
        "joint_witness": witness, "reachable_by_layer": reachability, "first_empty_join": first_break,
        "scope": "Object IDs are local to their declared layer; a shared intermediate layer must use the same "
                 "member. A finite empty join refutes only the sufficiency of these local-existence premises "
                 "for this supplied chain. It does not identify a real causal mechanism or negate an independently "
                 "established total effect.",
    }


OPERATORS = {
    "task_partition": (f6_task_partition, ("states", "actions", "transitions", "H"), ("query", "queries")),
    "representation_audit": (f1_representation_audit, ("representation", "query"), ("actual_decoder",)),
    "common_actions": (f3_common_actions, ("admissible", "action_universe"), ("observation",)),
    "resource_schedule": (resource_schedule, ("horizon", "resources", "tasks", "search_budget"), ()),
    "condition_search": (condition_search, ("variables", "admissible_assignments", "admissible_table_complete", "search_budget"), ()),
    "relation_chain": (relation_chain, ("layers", "relations"), ()),
}


def validate_model(model):
    _fields(model, ("schema_version", "title", "fictional", "assumptions", "boundaries", "operator", "input"))
    if type(model["schema_version"]) is not int or model["schema_version"] != 1:
        raise InputError("schema_version must be integer 1")
    if not isinstance(model["title"], str) or not model["title"].strip():
        raise InputError("title must be nonempty text")
    _boolean(model["fictional"], "fictional")
    for field in ("assumptions", "boundaries"):
        _texts(model[field], field)
    operator = model["operator"]
    if not isinstance(operator, str) or operator not in OPERATORS:
        raise InputError(f"operator must be one of {', '.join(OPERATORS)}")
    function, required, optional = OPERATORS[operator]
    _fields(model["input"], required, optional, label="input")
    for field in optional:
        if field in model["input"] and model["input"][field] is None:
            raise InputError(f"{field}: omit an unavailable optional field; null is not a known value")
    function(**model["input"], _validate_only=True)
    return {
        "format": FORMAT, "status": "valid_model", "operator": operator,
        "computed": False, "model": model, "notice": NOTICE,
        "validation_scope": "Declared types, finite scope, required fields and references only; no feasibility search or evidence validation.",
    }


def compute_model(model):
    report = validate_model(model)
    function = OPERATORS[model["operator"]][0]
    report.update(status="computed", computed=True, result=function(**model["input"]))
    return report


def _object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _nonfinite(value):
    raise InputError(f"non-finite JSON number is unsupported: {value}")


def _decimal_float(value):
    """Never silently identify distinct decimal JSON numbers through rounding.

    Operators work with Fraction(str(number)).  A parsed float is therefore
    usable only when its decimal spelling retains the number the caller wrote.
    This is decimal round-trip preservation, not exact binary representation:
    ordinary 0.1 is supported, but underflow and excess precision are rejected.
    Keep the float type, so integer-only fields still reject JSON 1.0.
    """
    parsed = float(value)
    if not math.isfinite(parsed):
        raise InputError("decimal number exceeds the supported finite range")
    try:
        preserved = Decimal(value) == Decimal(str(parsed))
    except DecimalException as error:
        raise InputError("decimal number exceeds the supported precision/range") from error
    if not preserved:
        raise InputError("decimal number would lose precision or underflow; "
                         "use exact scaled integers and state the unit, or retain this model unresolved")
    return parsed


def _encode_report(report):
    """Bound serialized UTF-8 bytes while encoding, before output or allocation
    of the full expanded result.  Repeated conflict pairs can greatly exceed
    the input size even though the in-memory report shares scalar objects.
    """
    encoder = json.JSONEncoder(ensure_ascii=False, indent=2, allow_nan=False)
    output = io.BytesIO()
    for fragment in encoder.iterencode(report):
        encoded = fragment.encode("utf-8")
        if output.tell() + len(encoded) + 1 > MAX_OUTPUT_BYTES:
            raise InputError("result exceeds the 32 MiB output limit; use a smaller declared model")
        output.write(encoded)
    output.write(b"\n")
    return output.getvalue()


def read_model(path, case=None):
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError("model exceeds the 2 MiB input limit")
    try:
        model = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_object_pairs,
                           parse_constant=_nonfinite, parse_float=_decimal_float)
    except RecursionError as error:
        raise InputError("model nesting is too deep") from error
    source = {"path": str(Path(path).resolve()), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    if isinstance(model, dict) and "models" in model:
        _fields(model, ("schema_version", "title", "fictional", "models"), label="example collection")
        if type(model["schema_version"]) is not int or model["schema_version"] != 1:
            raise InputError("collection schema_version must be integer 1")
        if not isinstance(model["title"], str) or not model["title"].strip():
            raise InputError("collection title must be nonempty text")
        _boolean(model["fictional"], "collection fictional")
        if not isinstance(model["models"], dict) or len(model["models"]) > 24:
            raise InputError("models must be a mapping of at most 24 case IDs to complete models")
        _names(list(model["models"]), "case IDs")
        for value in model["models"].values():
            validate_model(value)
        if case not in model["models"]:
            raise InputError(f"select --case from: {', '.join(model['models'])}")
        source["case"] = case
        model = model["models"][case]
    elif case is not None:
        raise InputError("--case applies only to an explicit example collection")
    return model, source


def write_result(report, output):
    """Create a new external file atomically; never overwrite, including races."""
    output = Path(output)
    require_external_output(output, __file__)
    require_external_output(output.with_name(output.name + ".lock"), __file__)
    if output.is_symlink() or output.exists():
        raise InputError("output already exists or is a symbolic link; choose a new external path")
    output = output.resolve()
    require_external_output(output, __file__)
    lock = output.with_name(output.name + ".lock")
    require_external_output(lock, __file__)
    payload = _encode_report(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    owns_lock = False
    try:
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise InputError("output has another writer or a leftover lock; lock was not removed") from error
        owns_lock = True
        os.close(descriptor)
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix=".finite-tools-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        # A hard link creates the destination only if absent on POSIX/Windows.
        # Filesystems without hard-link support fail safely; no replace fallback.
        try:
            os.link(temporary, output)
        except FileExistsError as error:
            raise InputError("output appeared during computation; existing content was preserved") from error
        return output
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if owns_lock:
            lock.unlink(missing_ok=True)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True, help="Explicit finite model JSON")
    parser.add_argument("--case", help="Case ID when the input is an example collection")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="Check the full contract without solving")
    compute = commands.add_parser("compute", help="Compute only inside the supplied finite model")
    compute.add_argument("--output", type=Path, help="New output file outside the installed skill; otherwise stdout")
    args = parser.parse_args(argv)
    try:
        if args.command == "compute" and args.output is not None:
            require_external_output(args.output, __file__)
            if args.output.resolve() == args.model.resolve():
                raise InputError("output must not be the input model")
            if args.output.exists() or args.output.is_symlink():
                raise InputError("output already exists or is a symbolic link; choose a new external path")
        model, source = read_model(args.model, args.case)
        report = validate_model(model) if args.command == "validate" else compute_model(model)
        report["input_file"] = source
        if args.command == "compute" and args.output is not None:
            target = write_result(report, args.output)
            print(json.dumps({"output": str(target), "format": FORMAT, "notice": NOTICE}, ensure_ascii=False))
        else:
            payload = _encode_report(report)
            sys.stdout.write(payload.decode("utf-8"))
        return 0
    except (InputError, OSError, UnicodeError, ValueError, RecursionError) as error:
        print(json.dumps({"format": FORMAT, "status": "invalid_input_or_io_error", "error": str(error)},
                         ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
