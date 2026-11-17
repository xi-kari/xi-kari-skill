"""Independent finite-model checks; these do not test empirical usefulness."""

from itertools import combinations, product
import random
import unittest

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "finite_tools.py"
spec = importlib.util.spec_from_file_location("xikari_finite_tools", SCRIPT)
ft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ft)
InputError = ft.InputError
f1_representation_audit = ft.f1_representation_audit
f3_common_actions = ft.f3_common_actions
f6_task_partition = ft.f6_task_partition

# Kept independent enumeration checks from the finite prototype.


def words(actions, horizon):
    for length in range(horizon + 1):
        yield from product(actions, repeat=length)


def apply_word(state, word, transitions):
    for action in word:
        state = transitions[state][action]
    return state


def brute_partition(states, actions, transitions, query, horizon):
    # Independent reference: enumerate complete action words, never refine blocks.
    all_words = list(words(actions, horizon))
    signatures = {}
    for state in states:
        signature = tuple(query[apply_word(state, word, transitions)] for word in all_words)
        signatures.setdefault(signature, set()).add(state)
    return {frozenset(group) for group in signatures.values()}


def brute_task_family(states, actions, transitions, queries, horizon):
    # Complete word/task Cartesian product, independent of refinement.
    observations = [(word, query_id) for word in words(actions, horizon) for query_id in queries]
    signatures = {}
    for state in states:
        signature = tuple(queries[q][apply_word(state, word, transitions)] for word, q in observations)
        signatures.setdefault(signature, set()).add(state)
    return {frozenset(group) for group in signatures.values()}


class TaskPartitionTests(unittest.TestCase):
    def test_adding_queries_or_actions_never_merges_old_blocks(self):
        states = ["a", "b", "c"]
        queries = {"q": {"a": 0, "b": 0, "c": 1}}
        transitions = {"a": {"stay": "a", "go": "c"},
                       "b": {"stay": "b", "go": "b"},
                       "c": {"stay": "c", "go": "a"}}
        for horizon in [0, 1, 2, None]:
            original = f6_task_partition(states, ["stay"],
                                        {state: {"stay": transitions[state]["stay"]} for state in states},
                                        queries=queries, H=horizon)
            with_action = f6_task_partition(states, ["stay", "go"], transitions, queries=queries, H=horizon)
            with_query = f6_task_partition(states, ["stay", "go"], transitions,
                                          queries={**queries, "other": {"a": 1, "b": 0, "c": 1}}, H=horizon)
            for coarse, finer in ((original, with_action), (with_action, with_query)):
                self.assertTrue(all(any(set(block) <= set(old) for old in coarse["blocks"])
                                    for block in finer["blocks"]))

    def test_required_four_state_example(self):
        states = ["a", "b", "c", "d"]
        transitions = {"a": {"go": "c"}, "b": {"go": "b"},
                       "c": {"go": "d"}, "d": {"go": "d"}}
        query = {"a": 0, "b": 0, "c": 0, "d": 1}
        h1 = f6_task_partition(states, ["go"], transitions, query, H=1)
        h2 = f6_task_partition(states, ["go"], transitions, query, H=2)
        stable = f6_task_partition(states, ["go"], transitions, query)
        self.assertEqual(h1["blocks"], [["a", "b"], ["c"], ["d"]])
        self.assertFalse(h1["dynamically_closed"])
        self.assertEqual(h2["blocks"], [["a"], ["b"], ["c"], ["d"]])
        self.assertTrue(h2["dynamically_closed"])
        self.assertEqual(stable["blocks"], h2["blocks"])
        ab = next(w for w in h2["separated_pairs"] if w["states"] == ["a", "b"])
        self.assertEqual(ab["shortest_action_word"], ["go", "go"])

    def test_all_two_state_two_action_systems_against_word_enumeration(self):
        states, actions = ["s0", "s1"], ["a", "b"]
        for targets in product(states, repeat=4):
            transitions = {state: dict(zip(actions, targets[i * 2:i * 2 + 2]))
                           for i, state in enumerate(states)}
            for outputs in product([0, 1], repeat=2):
                query = dict(zip(states, outputs))
                for horizon in range(5):
                    result = f6_task_partition(states, actions, transitions, query, H=horizon)
                    actual = {frozenset(block) for block in result["blocks"]}
                    self.assertEqual(actual, brute_partition(states, actions, transitions, query, horizon))
                    for witness in result["separated_pairs"]:
                        left, right = witness["states"]
                        distinguishing = [word for word in words(actions, horizon)
                                          if query[apply_word(left, word, transitions)]
                                          != query[apply_word(right, word, transitions)]]
                        self.assertEqual(witness["length"], min(map(len, distinguishing)))
                stable = f6_task_partition(states, actions, transitions, query, H=None)
                self.assertEqual({frozenset(b) for b in stable["blocks"]},
                                 brute_partition(states, actions, transitions, query, 4))
                self.assertTrue(stable["dynamically_closed"])

    def test_three_state_multiple_action_samples_against_words(self):
        generator = random.Random(20261116)
        states, actions = ["a", "b", "c"], ["x", "y"]
        for _ in range(60):
            transitions = {s: {a: generator.choice(states) for a in actions} for s in states}
            query = {s: generator.randrange(2) for s in states}
            for horizon in range(5):
                result = f6_task_partition(states, actions, transitions, query, H=horizon)
                self.assertEqual({frozenset(b) for b in result["blocks"]},
                                 brute_partition(states, actions, transitions, query, horizon))
            stable = f6_task_partition(states, actions, transitions, query)
            self.assertEqual({frozenset(b) for b in stable["blocks"]},
                             brute_partition(states, actions, transitions, query, 8))
            for witness in stable["separated_pairs"]:
                left, right = witness["states"]
                word = witness["shortest_action_word"]
                self.assertNotEqual(query[apply_word(left, word, transitions)],
                                    query[apply_word(right, word, transitions)])
                self.assertTrue(all(
                    query[apply_word(left, shorter, transitions)] == query[apply_word(right, shorter, transitions)]
                    for shorter in words(actions, len(word) - 1)
                ))

    def test_boolean_and_number_outputs_are_distinct(self):
        result = f6_task_partition(["a", "b"], ["x"],
                                   {"a": {"x": "a"}, "b": {"x": "b"}},
                                   {"a": True, "b": 1}, H=0)
        self.assertEqual(result["blocks"], [["a"], ["b"]])

    def test_two_query_families_against_exhaustive_word_enumeration(self):
        states, actions = ["s0", "s1"], ["a", "b"]
        for targets in product(states, repeat=4):
            transitions = {state: dict(zip(actions, targets[i * 2:i * 2 + 2]))
                           for i, state in enumerate(states)}
            for answers in product([0, 1], repeat=4):
                queries = {"first": dict(zip(states, answers[:2])),
                           "second": dict(zip(states, answers[2:]))}
                for horizon in range(4):
                    result = f6_task_partition(states, actions, transitions, queries=queries, H=horizon)
                    self.assertEqual({frozenset(block) for block in result["blocks"]},
                                     brute_task_family(states, actions, transitions, queries, horizon))
                    for witness in result["separated_pairs"]:
                        left, right = witness["states"]
                        candidates = [word for word in words(actions, horizon)
                                      if any(queries[q][apply_word(left, word, transitions)]
                                             != queries[q][apply_word(right, word, transitions)] for q in queries)]
                        self.assertEqual(witness["length"], min(map(len, candidates)))
                        for difference in witness["distinguishing_queries"]:
                            q = difference["query_id"]
                            word = witness["shortest_action_word"]
                            self.assertEqual(difference["left_answer"], queries[q][apply_word(left, word, transitions)])
                            self.assertEqual(difference["right_answer"], queries[q][apply_word(right, word, transitions)])
                            self.assertNotEqual(difference["left_answer"], difference["right_answer"])
                stable = f6_task_partition(states, actions, transitions, queries=queries)
                self.assertEqual({frozenset(block) for block in stable["blocks"]},
                                 brute_task_family(states, actions, transitions, queries, 4))

    def test_empty_actions_preserve_only_current_task_vector(self):
        states = ["a", "b", "c", "d"]
        transitions = {state: {} for state in states}
        queries = {"terminal": {"a": 0, "b": 0, "c": 0, "d": 1},
                   "is_b": {"a": 0, "b": 1, "c": 0, "d": 0}}
        expected = {frozenset(["a", "c"]), frozenset(["b"]), frozenset(["d"])}
        for horizon in [0, 1, 5, None]:
            result = f6_task_partition(states, [], transitions, queries=queries, H=horizon)
            self.assertEqual({frozenset(block) for block in result["blocks"]}, expected)
            self.assertEqual(expected, brute_task_family(states, [], transitions, queries, 5))
            self.assertTrue(result["empty_action_set"])
            self.assertTrue(result["dynamically_closed"])
            self.assertTrue(all(witness["shortest_action_word"] == [] for witness in result["separated_pairs"]))

    def test_empty_task_family_is_explicit_and_has_one_block(self):
        states = ["a", "b", "c"]
        transitions = {"a": {"go": "b"}, "b": {"go": "c"}, "c": {"go": "a"}}
        for horizon in [0, 2, None]:
            result = f6_task_partition(states, ["go"], transitions, queries={}, H=horizon)
            self.assertEqual(result["blocks"], [states])
            self.assertEqual({frozenset(block) for block in result["blocks"]},
                             brute_task_family(states, ["go"], transitions, {}, 4))
            self.assertTrue(result["empty_task_family"])
            self.assertEqual(result["query_ids"], [])
            self.assertEqual(result["separated_pairs"], [])
        both_empty = f6_task_partition(states, [], {s: {} for s in states}, queries={})
        self.assertEqual(both_empty["blocks"], [states])
        self.assertTrue(both_empty["empty_action_set"])


class RepresentationTests(unittest.TestCase):
    def test_required_two_kinds_of_error_coexist(self):
        result = f1_representation_audit(
            {"s0": "0", "s1": "0", "s2": "1"},
            {"s0": 0, "s1": 1, "s2": 1}, {"0": 0, "1": 0})
        self.assertEqual([pair["states"] for pair in result["conflict_pairs"]], [["s0", "s1"]])
        errors = {error["state"]: error for error in result["actual_decoder_errors"]}
        self.assertTrue(errors["s1"]["fiber_ambiguous"])
        self.assertFalse(errors["s1"]["information_sufficient_but_rule_wrong"])
        self.assertFalse(errors["s2"]["fiber_ambiguous"])
        self.assertTrue(errors["s2"]["information_sufficient_but_rule_wrong"])
        self.assertEqual(result["scalar_error_bound"]["minimum_possible_global_worst_case_error"]["exact"], "1/2")
        self.assertEqual(result["scalar_error_bound"]["actual_decoder_global_worst_case_error"]["value"], 1.0)

    def test_scalar_bound_midpoint_attainment(self):
        result = f1_representation_audit(
            {"a": "left", "b": "left", "c": "right"},
            {"a": -3, "b": 7, "c": 100}, {"left": 2, "right": 100})
        scalar = result["scalar_error_bound"]
        self.assertEqual(scalar["minimum_possible_global_worst_case_error"]["value"], 5.0)
        self.assertEqual(scalar["actual_decoder_global_worst_case_error"]["value"], 5.0)

    def test_non_numeric_and_absent_decoder_do_not_get_numeric_results(self):
        result = f1_representation_audit({"a": "same", "b": "same"}, {"a": "yes", "b": "no"})
        self.assertIsNone(result["scalar_error_bound"])
        self.assertIsNone(result["actual_decoder_correct_on_all_states"])

    def test_large_finite_scalar_values_preserve_exact_bound(self):
        result = f1_representation_audit({"a": "same", "b": "same"}, {"a": -1e308, "b": 1e308}, {"same": -1e308})
        bound = result["scalar_error_bound"]
        self.assertEqual(bound["minimum_possible_global_worst_case_error"]["value"], 1e308)
        self.assertIsNone(bound["actual_decoder_global_worst_case_error"]["value"])
        self.assertEqual(bound["actual_decoder_global_worst_case_error"]["exact"], str(2 * 10 ** 308))


class CommonActionTests(unittest.TestCase):
    def test_triple_empty_intersection_but_every_pair_intersects(self):
        admissible = {"s1": ["A", "B"], "s2": ["B", "C"], "s3": ["A", "C"]}
        result = f3_common_actions(admissible, ["A", "B", "C"])
        self.assertEqual(result["common_actions"], [])
        self.assertTrue(result["every_state_has_some_action"])
        self.assertEqual(result["inclusion_minimal_empty_intersection_states"], ["s1", "s2", "s3"])
        for a, b in combinations(admissible, 2):
            self.assertTrue(set(admissible[a]) & set(admissible[b]))
        for actions in result["core_deletion_common_actions"].values():
            self.assertTrue(actions)

    def test_observation_groupwise_common_actions(self):
        admissible = {"s1": ["A", "B"], "s2": ["B", "C"], "s3": ["A", "C"]}
        bad = f3_common_actions(admissible, ["A", "B", "C"], dict.fromkeys(admissible, "same"))
        good = f3_common_actions(admissible, ["A", "B", "C"], {"s1": "g1", "s2": "g1", "s3": "g2"})
        self.assertFalse(bad["observation_sufficient_for_groupwise_common_action"])
        self.assertTrue(good["observation_sufficient_for_groupwise_common_action"])
        self.assertEqual(good["observation_groups"][0]["common_actions"], ["B"])
        self.assertEqual(good["observation_groups"][1]["common_actions"], ["A", "C"])

    def test_all_three_state_three_action_families_have_valid_minimal_cores(self):
        universe = ["A", "B", "C"]
        subsets = [[a for i, a in enumerate(universe) if mask & (1 << i)] for mask in range(8)]
        for family in product(subsets, repeat=3):
            admissible = dict(zip(["s0", "s1", "s2"], family))
            result = f3_common_actions(admissible, universe)
            direct = set(universe).intersection(*(set(s) for s in family))
            self.assertEqual(set(result["common_actions"]), direct)
            core = result["inclusion_minimal_empty_intersection_states"]
            if direct:
                self.assertIsNone(core)
            else:
                self.assertTrue(core)
                self.assertFalse(set(universe).intersection(*(set(admissible[s]) for s in core)))
                for removed in core:
                    remaining = [set(admissible[s]) for s in core if s != removed]
                    self.assertTrue(set(universe).intersection(*remaining))


class InputContractTests(unittest.TestCase):
    def test_f6_rejects_incomplete_or_invalid_models(self):
        cases = [
            ([], ["go"], {}, {}, None),
            (["a", "a"], ["go"], {"a": {"go": "a"}}, {"a": 0}, None),
            (["a"], ["go"], {"a": {}}, {"a": 0}, None),
            (["a"], ["go"], {"a": {"go": "missing"}}, {"a": 0}, None),
            (["a"], ["go"], {"a": {"go": "a", "extra": "a"}}, {"a": 0}, None),
            (["a"], ["go"], {"a": {"go": "a"}}, {"a": float("nan")}, None),
        ]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(InputError):
                f6_task_partition(*args)
        for horizon in [-1, 1.5, True, "2"]:
            with self.subTest(H=horizon), self.assertRaises(InputError):
                f6_task_partition(["a"], ["go"], {"a": {"go": "a"}}, {"a": 0}, horizon)

    def test_f6_rejects_ambiguous_or_incomplete_task_families(self):
        base = (["a"], ["go"], {"a": {"go": "a"}})
        with self.assertRaises(InputError):
            f6_task_partition(*base)
        with self.assertRaises(InputError):
            f6_task_partition(*base, query={"a": 0}, queries={})
        for invalid in [[], {"task": {}}, {0: {"a": 0}}, {"task": {"a": float("inf")}}]:
            with self.subTest(queries=invalid), self.assertRaises(InputError):
                f6_task_partition(*base, queries=invalid)

    def test_f1_rejects_missing_keys_and_invalid_scalars(self):
        cases = [
            ({}, {}, None),
            ({"a": "r"}, {}, None),
            ({"a": 0}, {"a": 1}, None),
            ({"a": "r"}, {"a": []}, None),
            ({"a": "r"}, {"a": 1}, {}),
            ({"a": "r"}, {"a": 1}, {"r": 0, "extra": 1}),
            ({"a": "r"}, {"a": 1}, {"r": float("inf")}),
        ]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(InputError):
                f1_representation_audit(*args)

    def test_f3_rejects_unknown_actions_duplicates_and_partial_observation(self):
        cases = [
            ({}, ["A"], None),
            ({"s": ["A"]}, [], None),
            ({"s": ["A"]}, ["A", "A"], None),
            ({"s": ["missing"]}, ["A"], None),
            ({"s": ["A", "A"]}, ["A"], None),
            ({"s": ["A"]}, ["A"], {}),
            ({"s": ["A"]}, ["A"], {"s": ""}),
        ]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(InputError):
                f3_common_actions(*args)


def envelope(operator, data):
    return {"schema_version": 1, "title": "Synthetic finite contract",
            "fictional": True, "assumptions": ["Explicit finite teaching inputs"],
            "boundaries": ["No empirical validation"], "operator": operator, "input": data}


def task(name, starts, duration=1, predecessors=(), demand=1, **changes):
    value = {"id": name, "duration": duration, "start_slots": starts,
             "demands": {"reviewer": demand}, "predecessors": list(predecessors),
             "ready_at": 0, "end_by": 3, "eligible": True,
             "authorized": True, "materials_ready": True}
    value.update(changes)
    return value


def schedule_input(tasks, capacity=None, budget=1000):
    return {"horizon": 3, "resources": [{"id": "reviewer", "capacity": capacity or [1, 1, 1]}],
            "tasks": tasks, "search_budget": budget}


def independent_schedule_valid(data, starts):
    """Evaluate complete assignments directly; no implementation DFS/pruning."""
    tasks_by_id = {value["id"]: value for value in data["tasks"]}
    for value in data["tasks"]:
        start = starts[value["id"]]
        end = start + value["duration"]
        if (start not in value["start_slots"] or start < value["ready_at"]
                or end > value["end_by"] or end > data["horizon"]
                or not all(value[flag] for flag in ("eligible", "authorized", "materials_ready"))):
            return False
        if any(starts[pred] + tasks_by_id[pred]["duration"] > start for pred in value["predecessors"]):
            return False
    for resource in data["resources"]:
        for slot, capacity in enumerate(resource["capacity"]):
            demand = sum(value["demands"][resource["id"]] for value in data["tasks"]
                         if starts[value["id"]] <= slot < starts[value["id"]] + value["duration"])
            if demand > capacity:
                return False
    return True


def independent_schedule_exists(data):
    ids = [value["id"] for value in data["tasks"]]
    return any(independent_schedule_valid(data, dict(zip(ids, starts)))
               for starts in product(*(value["start_slots"] for value in data["tasks"])))


class ResourceScheduleTests(unittest.TestCase):
    def test_individual_feasibility_does_not_compose(self):
        first, second = task("a", [0], 2), task("b", [0], 2)
        for value in (first, second):
            self.assertEqual(ft.resource_schedule(**schedule_input([value]))["status"], "feasible_in_model")
        result = ft.resource_schedule(**schedule_input([first, second]))
        self.assertEqual(result["status"], "infeasible_in_model")
        self.assertEqual(result["tasks_without_individual_start"], [])

    def test_total_capacity_is_not_a_contiguous_slot(self):
        data = schedule_input([task("a", [0, 1], 2)], [1, 0, 1])
        self.assertEqual(sum(data["resources"][0]["capacity"]), 2)
        result = ft.resource_schedule(**data)
        self.assertEqual(result["status"], "infeasible_in_model")
        self.assertEqual(result["tasks_without_individual_start"], ["a"])

    def test_predecessor_and_final_deadline_and_half_open_boundary(self):
        values = [task("a", [0]), task("b", [0, 1], 2, ["a"], end_by=2)]
        self.assertEqual(ft.resource_schedule(**schedule_input(values))["status"], "infeasible_in_model")
        values[1]["end_by"] = 3
        result = ft.resource_schedule(**schedule_input(values))
        self.assertEqual(result["status"], "feasible_in_model")
        self.assertEqual([(row["start"], row["end"]) for row in result["schedule"]], [(0, 1), (1, 3)])

    def test_each_readiness_flag_is_independently_binding_and_unknown_rejected(self):
        for field in ("eligible", "authorized", "materials_ready"):
            value = task("a", [0], **{field: False})
            self.assertEqual(ft.resource_schedule(**schedule_input([value]))["status"], "infeasible_in_model")
            value[field] = None
            with self.assertRaises(InputError):
                ft.resource_schedule(**schedule_input([value]))

    def test_budget_exhaustion_not_infeasibility_and_empty_tasks_trivial(self):
        data = schedule_input([task("a", [0])], budget=0)
        result = ft.resource_schedule(**data)
        self.assertEqual(result["status"], "search_incomplete")
        self.assertFalse(result["decision_complete"])
        self.assertEqual(ft.resource_schedule(**schedule_input([], budget=0))["schedule"], [])
        impossible = schedule_input([task("a", [], duration=2)], budget=0)
        self.assertEqual(ft.resource_schedule(**impossible)["status"], "infeasible_in_model")

    def test_complete_small_models_against_independent_cartesian_enumeration(self):
        for capacity in product([0, 1, 2], repeat=3):
            for durations in product([1, 2], repeat=2):
                for dependent in (False, True):
                    data = schedule_input([task("a", [0, 1, 2], durations[0]),
                                           task("b", [0, 1, 2], durations[1], ["a"] if dependent else [])], list(capacity))
                    expected = independent_schedule_exists(data)
                    actual = ft.resource_schedule(**data)
                    self.assertEqual(actual["status"] == "feasible_in_model", expected)
                    self.assertTrue(actual["decision_complete"])
                    if expected:
                        starts = {row["task_id"]: row["start"] for row in actual["schedule"]}
                        self.assertTrue(independent_schedule_valid(data, starts))
                        more = copy.deepcopy(data)
                        more["resources"][0]["capacity"] = [v + 1 for v in capacity]
                        self.assertEqual(ft.resource_schedule(**more)["status"], "feasible_in_model")

    def test_task_order_is_not_an_implicit_sequential_constraint(self):
        data = schedule_input([task("late", [2]), task("early", [0])])
        result = ft.resource_schedule(**data)
        self.assertEqual(result["status"], "feasible_in_model")
        reversed_data = copy.deepcopy(data)
        reversed_data["tasks"].reverse()
        self.assertEqual(ft.resource_schedule(**reversed_data)["status"], result["status"])

    def test_resources_are_separate_and_explicit_zero_demand_is_allowed(self):
        data = schedule_input([task("a", [0]), task("b", [0])], capacity=[2, 2, 2])
        data["resources"].append({"id": "console", "capacity": [1, 1, 1]})
        for value in data["tasks"]:
            value["demands"]["console"] = 1
        self.assertEqual(ft.resource_schedule(**data)["status"], "infeasible_in_model")
        data["tasks"][1]["demands"]["console"] = 0
        result = ft.resource_schedule(**data)
        self.assertEqual(result["status"], "feasible_in_model")
        self.assertEqual(result["resource_usage"], {"reviewer": [2, 0, 0], "console": [1, 0, 0]})

    def test_empty_resource_set_preserves_time_and_predecessor_constraints(self):
        data = schedule_input([task("a", [0]), task("b", [0], predecessors=["a"])])
        data["resources"] = []
        for value in data["tasks"]:
            value["demands"] = {}
        self.assertEqual(ft.resource_schedule(**data)["status"], "infeasible_in_model")
        data["tasks"][1]["start_slots"] = [1]
        self.assertEqual(ft.resource_schedule(**data)["status"], "feasible_in_model")

    def test_invalid_and_hidden_late_records_are_rejected_before_search(self):
        for field, value in (("duration", True), ("duration", 1.0), ("duration", 0),
                             ("ready_at", None), ("end_by", float("inf")),
                             ("predecessors", ["missing"]), ("start_slots", [0, 0]),
                             ("demands", {})):
            bad = task("b", [0], **{field: value})
            with self.subTest(field=field), self.assertRaises(InputError):
                ft.resource_schedule(**schedule_input([task("a", [0]), bad]))
        for values in ([task("a", [0]), task("a", [1])],
                       [task("a", [0], predecessors=["b"]), task("b", [1], predecessors=["a"]) ]):
            with self.assertRaises(InputError):
                ft.resource_schedule(**schedule_input(values))


def conditions(accepted, *, budget=100, mutable=(True, True)):
    return {"variables": [{"id": name, "current": 0, "values": [0, 1], "mutable": can_change}
                           for name, can_change in zip(["x", "y"], mutable)],
            "admissible_assignments": [dict(zip(["x", "y"], values)) for values in accepted],
            "admissible_table_complete": True, "search_budget": budget}


class ConditionSearchTests(unittest.TestCase):
    def test_complementary_changes_and_protected_fixed_variable(self):
        result = ft.condition_search(**conditions([(1, 1)]))
        self.assertEqual(result["inclusion_minimal_changes"][0]["changed_variables"], ["x", "y"])
        fixed = ft.condition_search(**conditions([(1, 1)], mutable=(False, True)))
        self.assertEqual(fixed["status"], "infeasible_in_model")
        self.assertEqual(fixed["fixed_variables"], ["x"])

    def test_already_admissible_requires_no_change(self):
        result = ft.condition_search(**conditions([(0, 0), (1, 1)]))
        self.assertEqual(result["inclusion_minimal_changes"], [{"assignment": {"x": 0, "y": 0}, "changed_variables": []}])

    def test_inclusion_minimal_not_minimum_cardinality(self):
        data = conditions([])
        data["variables"].append({"id": "z", "current": 0, "values": [0, 1], "mutable": True})
        data["admissible_assignments"] = [{"x": 1, "y": 0, "z": 0}, {"x": 0, "y": 1, "z": 1}]
        result = ft.condition_search(**data)
        self.assertEqual({frozenset(row["changed_variables"]) for row in result["inclusion_minimal_changes"]},
                         {frozenset(["x"]), frozenset(["y", "z"])})

    def test_partial_search_preserves_witnesses_without_global_minimality(self):
        data = conditions([(0, 1), (1, 0), (1, 1)], budget=2)
        result = ft.condition_search(**data)
        self.assertEqual(result["status"], "search_incomplete")
        self.assertEqual(result["found_feasible_assignments"], [{"assignment": {"x": 0, "y": 1}, "changed_variables": ["y"]}])
        self.assertIsNone(result["inclusion_minimal_changes"])

    def test_all_two_boolean_tables_and_mutability_patterns(self):
        all_values = list(product([0, 1], repeat=2))
        for membership in product([False, True], repeat=4):
            accepted = [values for values, included in zip(all_values, membership) if included]
            for mutable in product([False, True], repeat=2):
                result = ft.condition_search(**conditions(accepted, mutable=mutable))
                expected = {values for values in accepted if all(can_change or value == 0
                           for value, can_change in zip(values, mutable))}
                actual = {tuple(row["assignment"][key] for key in ["x", "y"])
                          for row in result["found_feasible_assignments"]}
                self.assertEqual(actual, expected)
                expected_sets = [set(i for i, value in enumerate(values) if value) for values in expected]
                expected_minimal = {frozenset(subset) for subset in expected_sets
                                    if not any(other < subset for other in expected_sets)}
                actual_minimal = {frozenset(["x", "y"].index(key) for key in row["changed_variables"])
                                  for row in result["inclusion_minimal_changes"]}
                self.assertEqual(actual_minimal, expected_minimal)

    def test_boolean_is_not_numeric_one_and_expanding_menu_keeps_solution(self):
        data = {"variables": [{"id": "x", "current": False, "values": [False, 0, True, 1], "mutable": True}],
                "admissible_assignments": [{"x": True}], "admissible_table_complete": True, "search_budget": 10}
        result = ft.condition_search(**data)
        self.assertEqual(result["menu_assignments"], 4)
        self.assertIs(result["found_feasible_assignments"][0]["assignment"]["x"], True)
        data["variables"][0]["values"].append("new")
        self.assertEqual(ft.condition_search(**data)["inclusion_minimal_changes"], result["inclusion_minimal_changes"])

    def test_incomplete_duplicate_unknown_or_out_of_menu_table_rejected(self):
        updates = [{"admissible_table_complete": False}, {"admissible_table_complete": None},
                   {"admissible_assignments": [{"x": 2, "y": 1}]},
                   {"admissible_assignments": [{"x": None, "y": 1}]},
                   {"admissible_assignments": [{"x": 1, "y": 1}, {"x": 1, "y": 1}]},
                   {"admissible_assignments": [{"x": 1}]}]
        for update in updates:
            data = conditions([(1, 1)])
            data.update(update)
            with self.subTest(update=update), self.assertRaises(InputError):
                ft.condition_search(**data)


def chain(pairs1=None, pairs2=None):
    return {"layers": [{"id": "start", "members": ["a"]},
                       {"id": "middle", "members": ["b1", "b2"]},
                       {"id": "end", "members": ["c"]}],
            "relations": [{"id": "r", "from_layer": "start", "to_layer": "middle",
                           "pairs": [["a", "b1"]] if pairs1 is None else pairs1},
                          {"id": "s", "from_layer": "middle", "to_layer": "end",
                           "pairs": [["b2", "c"]] if pairs2 is None else pairs2}]}


class RelationChainTests(unittest.TestCase):
    def test_local_existence_has_no_common_intermediate_object(self):
        result = ft.relation_chain(**chain())
        self.assertTrue(result["local_existence_counterexample"])
        self.assertIsNone(result["joint_witness"])
        self.assertEqual(result["first_empty_join"]["relation_id"], "s")
        self.assertEqual(result["first_empty_join"]["reachable_sources"], ["b1"])
        self.assertEqual(result["first_empty_join"]["relation_sources"], ["b2"])

    def test_adding_bridge_yields_complete_witness(self):
        result = ft.relation_chain(**chain(pairs2=[["b2", "c"], ["b1", "c"]]))
        self.assertFalse(result["local_existence_counterexample"])
        self.assertEqual([row["member_id"] for row in result["joint_witness"]], ["a", "b1", "c"])
        self.assertIsNone(result["first_empty_join"])

    def test_empty_edge_is_not_nonempty_local_premise_counterexample(self):
        result = ft.relation_chain(**chain(pairs1=[]))
        self.assertEqual(result["status"], "no_joint_witness")
        self.assertFalse(result["all_local_relations_nonempty"])
        self.assertFalse(result["local_existence_counterexample"])

    def test_all_small_relations_against_independent_path_enumeration(self):
        left = [["a", "b1"], ["a", "b2"]]
        right = [["b1", "c"], ["b2", "c"]]
        for flags in product([False, True], repeat=4):
            pairs1 = [pair for pair, use in zip(left, flags[:2]) if use]
            pairs2 = [pair for pair, use in zip(right, flags[2:]) if use]
            data = chain(pairs1, pairs2)
            result = ft.relation_chain(**data)
            expected = [path for path in product(*(layer["members"] for layer in data["layers"]))
                        if all([path[index], path[index + 1]] in relation["pairs"]
                               for index, relation in enumerate(data["relations"]))]
            self.assertEqual(result["joint_witness"] is not None, bool(expected))
            if expected:
                witness = tuple(row["member_id"] for row in result["joint_witness"])
                self.assertIn(witness, expected)

    def test_layers_relations_and_pair_references_are_validated(self):
        cases = []
        for field, value in (("pairs", [["a", "b1"], ["a", "b1"]]),
                             ("pairs", [["a", "missing"]]), ("pairs", [["a", None]]),
                             ("from_layer", "middle")):
            data = chain()
            data["relations"][0][field] = value
            cases.append(data)
        duplicate = chain()
        duplicate["layers"][1]["id"] = "start"
        cases.append(duplicate)
        for data in cases:
            with self.assertRaises(InputError):
                ft.relation_chain(**data)


class EnvelopeAndCLITests(unittest.TestCase):
    def setUp(self):
        self.data = envelope("representation_audit", {"representation": {"a": "r", "b": "r"},
                                                       "query": {"a": 0, "b": 1}})

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)

    def test_validate_is_not_compute_and_preserves_supplied_model(self):
        data = envelope("task_partition", {"states": ["a", "b"], "actions": [],
                                            "transitions": {"a": {}, "b": {}},
                                            "queries": {"q": {"a": 0, "b": 1}}, "H": None})
        with mock.patch.object(ft, "_shortest_word", side_effect=AssertionError("must not solve")):
            report = ft.validate_model(data)
        self.assertEqual(report["status"], "valid_model")
        self.assertFalse(report["computed"])
        self.assertEqual(report["model"], data)
        self.assertNotIn("result", report)
        impossible = envelope("resource_schedule", schedule_input([task("a", [])]))
        self.assertEqual(ft.validate_model(impossible)["status"], "valid_model")

    def test_unknown_null_nonfinite_and_unsupported_fields_rejected(self):
        for value in (None, float("inf"), float("nan")):
            bad = copy.deepcopy(self.data)
            bad["input"]["query"]["b"] = value
            with self.assertRaises(InputError):
                ft.validate_model(bad)
        for key, value in (("actual_decoder", None), ("ignored_typo", 1)):
            bad = copy.deepcopy(self.data)
            bad["input"][key] = value
            with self.assertRaises(InputError):
                ft.validate_model(bad)

    def test_cli_duplicate_json_keys_and_nonfinite_numbers(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "model.json"
            for content in ('{"a":1,"a":2}', '{"nested":{"x":0,"x":1}}', '{"a":NaN}', '{"a":Infinity}'):
                source.write_text(content, encoding="utf-8")
                result = self.run_cli("--model", source, "validate")
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("error", json.loads(result.stderr))

    def test_all_shipped_examples_run_through_the_cli(self):
        source = ROOT / "assets" / "examples" / "finite-tools.json"
        collection = json.loads(source.read_text(encoding="utf-8"))
        covered = set()
        for case, model in collection["models"].items():
            with self.subTest(case=case):
                result = self.run_cli("--model", source, "--case", case, "compute")
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report["input_file"]["case"], case)
                self.assertEqual(report["model"], model)
                self.assertTrue(report["computed"])
                covered.add(report["operator"])
        self.assertEqual(covered, set(ft.OPERATORS))
        missing_case = self.run_cli("--model", source, "validate")
        self.assertEqual(missing_case.returncode, 2)
        self.assertIn("select --case", json.loads(missing_case.stderr)["error"])

    def test_collection_checks_unselected_records_and_rejects_case_for_single_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "model.json"
            bad = copy.deepcopy(self.data)
            bad["input"]["query"]["b"] = None
            collection = {"schema_version": 1, "title": "examples", "fictional": True,
                          "models": {"good": self.data, "bad": bad}}
            source.write_text(json.dumps(collection), encoding="utf-8")
            with self.assertRaises(InputError):
                ft.read_model(source, "good")
            source.write_text(json.dumps(self.data), encoding="utf-8")
            with self.assertRaises(InputError):
                ft.read_model(source, "unavailable")

    def test_cli_success_hash_identity_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            source, output = Path(temporary) / "model.json", Path(temporary) / "result.json"
            source.write_text(json.dumps(self.data), encoding="utf-8")
            result = self.run_cli("--model", source, "validate")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertFalse(report["computed"])
            self.assertEqual(report["input_file"]["sha256"], ft.hashlib.sha256(source.read_bytes()).hexdigest())
            result = self.run_cli("--model", source, "compute", "--output", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = output.read_bytes()
            report = json.loads(expected)
            self.assertEqual(report["model"], self.data)
            self.assertTrue(report["computed"])
            result = self.run_cli("--model", source, "compute", "--output", output)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(output.read_bytes(), expected)
            original = source.read_bytes()
            result = self.run_cli("--model", source, "compute", "--output", source)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(sorted(p.name for p in Path(temporary).iterdir()), ["model.json", "result.json"])

    def test_installation_and_symlink_boundary_before_directory_creation(self):
        target = ROOT / "assets" / "finite-test-must-not-exist" / "result.json"
        self.assertFalse(target.parent.exists())
        with self.assertRaises(OSError):
            ft.write_result({}, target)
        self.assertFalse(target.parent.exists())
        with tempfile.TemporaryDirectory() as temporary:
            alias = Path(temporary) / "alias"
            try:
                alias.symlink_to(ROOT / "assets", target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with self.assertRaises(OSError):
                ft.write_result({}, alias / "finite-test-must-not-exist" / "result.json")
            self.assertFalse(target.parent.exists())
            dangling = Path(temporary) / "dangling.json"
            dangling.symlink_to(Path(temporary) / "absent.json")
            with self.assertRaises(InputError):
                ft.write_result({}, dangling)
            self.assertTrue(dangling.is_symlink())

    def test_existing_lock_preserved_and_commit_race_does_not_clobber(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "result.json"
            lock = output.with_name(output.name + ".lock")
            lock.write_text("other owner", encoding="utf-8")
            with self.assertRaises(InputError):
                ft.write_result({}, output)
            self.assertEqual(lock.read_text(), "other owner")
            self.assertFalse(output.exists())
            lock.unlink()
            original_link = ft.os.link

            def concurrent_link(source, destination):
                Path(destination).write_text("concurrent writer", encoding="utf-8")
                return original_link(source, destination)

            with mock.patch.object(ft.os, "link", side_effect=concurrent_link):
                with self.assertRaises(InputError):
                    ft.write_result({}, output)
            self.assertEqual(output.read_text(), "concurrent writer")
            self.assertEqual([p.name for p in Path(temporary).iterdir()], ["result.json"])

    def test_atomic_creation_io_failure_leaves_no_output_lock_or_temporary(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "result.json"
            with mock.patch.object(ft.os, "link", side_effect=OSError("filesystem does not support links")):
                with self.assertRaises(OSError):
                    ft.write_result({}, output)
            self.assertEqual(list(Path(temporary).iterdir()), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
