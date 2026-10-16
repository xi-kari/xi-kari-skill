import copy
import csv
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "condition_lab.py"
spec = importlib.util.spec_from_file_location("xikari_condition_lab", SCRIPT)
lab = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = lab
spec.loader.exec_module(lab)


def example(name):
    return json.loads((ROOT / "assets" / "examples" / f"condition-{name}.json").read_text(encoding="utf-8"))


def minimal():
    return {
        "schema_version": 1, "title": "虚构测试", "purpose": "验证表达式与数据边界", "fictional": True,
        "assumptions": ["仅用于测试"], "boundaries": ["不代表现实可行性"],
        "inputs": {
            "capacity": {"label": "容量", "value": 10, "unit": "小时", "basis": "assumed", "role": "condition"},
            "selected": {"label": "选择", "value": 4, "unit": "小时", "basis": "assumed", "role": "decision"},
        },
        "derived": [{"id": "remaining", "label": "余量", "formula": "capacity - selected", "unit": "小时"}],
        "constraints": [{"id": "fits", "formula": "remaining >= 0", "description": "容量可覆盖"}],
    }


class ConditionLabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "model.json"
        self.source.write_text(json.dumps(minimal()), encoding="utf-8")
        self.output = self.root / "output"

    def tearDown(self):
        self.temp.cleanup()

    def case(self, result, scenario="baseline", plan="baseline", **combination):
        return next(item for item in result["cases"] if item["scenario"] == scenario and item["plan"] == plan and item["explore"] == combination)

    def test_university_numeric_capacity_and_eligibility_are_separate(self):
        result = lab.evaluate_model(example("university"))
        self.assertEqual(result["case_count"], 27)
        baseline = self.case(result, total_hours=40)
        self.assertEqual({d["id"]: d["value"] for d in baseline["derived"]}, {"committed_hours": 42, "remaining_hours": -2, "uncovered_need": 0})
        self.assertEqual(baseline["state"], "violates_model_constraints")
        alternative = self.case(result, plan="appeals_first", total_hours=40)
        self.assertEqual(alternative["derived"][1]["value"], 0)
        self.assertEqual(alternative["state"], "undetermined")
        self.assertEqual(alternative["constraints"][-1]["state"], "unknown")
        hypothetical = self.case(result, scenario="eligibility_assumed", plan="appeals_first", total_hours=40)
        self.assertEqual(hypothetical["state"], "satisfies_model_constraints")
        self.assertEqual(hypothetical["inputs"]["all_cases_eligible"]["basis"], "assumed")
        demand = self.case(result, scenario="demand_rises", plan="appeals_first", total_hours=50)
        self.assertEqual(demand["derived"][2]["value"], 3)
        self.assertEqual(demand["state"], "violates_model_constraints")

    def test_sensitivity_reports_which_declared_condition_moves_the_state(self):
        result = lab.evaluate_model(example("university"))
        report = {item["condition"]: item for item in result["sensitivity"]}
        self.assertEqual(set(report), {"total_hours"})
        total = report["total_hours"]
        self.assertTrue(total["decisive"])
        self.assertGreater(total["state_changing_groups"], 0)
        self.assertEqual(total["values"], [30, 40, 50])
        self.assertEqual(total["label"], "总工时")
        for sample in total["examples"]:
            self.assertEqual(len(sample["values"]), len(sample["states"]))
            self.assertGreater(len(set(sample["states"])), 1)

    def test_sensitivity_is_empty_without_declared_explore_conditions(self):
        result = lab.evaluate_model(minimal())
        self.assertEqual(result["sensitivity"], [])

    def test_sensitivity_reuses_computed_cases_without_adding_any(self):
        model = example("university")
        result = lab.evaluate_model(model)
        self.assertEqual(result["case_count"], 27)
        self.assertEqual(len(result["cases"]), 27)
        states = {case["id"]: case["state"] for case in result["cases"]}
        self.assertEqual(len(states), 27)

    def test_sensitivity_does_not_invent_values_outside_the_declared_grid(self):
        model = minimal()
        model["explore"] = {"capacity": [2, 10]}
        result = lab.evaluate_model(model)
        report = result["sensitivity"][0]
        self.assertEqual(report["condition"], "capacity")
        self.assertEqual(set(report["values"]), {2, 10})
        self.assertTrue(report["decisive"])
        self.assertEqual(set(report["observed_states"]), {"violates_model_constraints", "satisfies_model_constraints"})

    def test_a_condition_that_never_crosses_a_constraint_is_not_reported_decisive(self):
        model = minimal()
        model["explore"] = {"capacity": [6, 10]}
        report = lab.evaluate_model(model)["sensitivity"][0]
        self.assertFalse(report["decisive"])
        self.assertEqual(report["state_changing_groups"], 0)
        self.assertEqual(set(report["observed_states"]), {"satisfies_model_constraints"})

    def test_project_capacity_does_not_resolve_external_dependency(self):
        result = lab.evaluate_model(example("project"))
        self.assertEqual(self.case(result, available=24)["state"], "satisfies_model_constraints")
        self.assertEqual(self.case(result, scenario="dependency_delayed", available=32)["state"], "violates_model_constraints")
        self.assertEqual(self.case(result, scenario="dependency_unknown", available=32)["state"], "undetermined")
        self.assertEqual(self.case(result, plan="four_features", available=24)["derived"][1]["value"], -6)

    def test_unknown_propagates_without_zero_and_division_errors_remain_distinct(self):
        model = minimal()
        model["inputs"]["capacity"].update(value=None, basis="unknown")
        result = lab.evaluate_model(model)["cases"][0]
        self.assertEqual(result["derived"][0]["state"], "unknown")
        self.assertIsNone(result["derived"][0]["value"])
        self.assertEqual(result["state"], "undetermined")
        model["derived"][0]["formula"] = "capacity / 0"
        result = lab.evaluate_model(model)["cases"][0]
        self.assertEqual(result["derived"][0]["state"], "error")
        self.assertIn("ZeroDivisionError", result["derived"][0]["reason"])
        self.assertEqual(result["state"], "calculation_error")

    def test_boolean_unknown_can_have_a_decisive_false_but_errors_not_hidden(self):
        values = {"missing": lab.Value("unknown", reason="未知")}
        self.assertEqual(lab.Formula("missing and False", {"missing"}).evaluate(values).value, False)
        self.assertEqual(lab.Formula("missing or True", {"missing"}).evaluate(values).value, True)
        self.assertEqual(lab.Formula("True or (1 / 0 > 0)", set()).evaluate({}).state, "error")

    def test_model_arithmetic_known_boolean_errors_are_not_hidden_by_unknown(self):
        for operator in ("+", "-", "*", "/", "//", "%", "**"):
            for boolean in (False, True):
                for left, right in (("selected", "capacity"), ("capacity", "selected")):
                    formula = f"{left} {operator} {right}"
                    with self.subTest(formula=formula, boolean=boolean):
                        model = minimal()
                        model["inputs"]["capacity"].update(value=None, basis="unknown")
                        model["inputs"]["selected"]["value"] = boolean
                        model["derived"][0]["formula"] = formula
                        case = lab.evaluate_model(model)["cases"][0]
                        self.assertEqual(case["derived"][0]["state"], "error")
                        self.assertIsNone(case["derived"][0]["value"])
                        self.assertTrue(case["derived"][0]["reason"])
                        self.assertEqual(case["constraints"][0]["state"], "error")
                        self.assertEqual(case["state"], "calculation_error")

    def test_model_exponent_bounds_are_checked_with_unknown_base(self):
        for exponent in ("13", "-13", "selected + 9", "-(selected + 9)"):
            with self.subTest(exponent=exponent):
                model = minimal()
                model["inputs"]["capacity"].update(value=None, basis="unknown")
                model["derived"][0]["formula"] = f"capacity ** ({exponent})"
                case = lab.evaluate_model(model)["cases"][0]
                self.assertEqual(case["derived"][0]["state"], "error")
                self.assertIn("12", case["derived"][0]["reason"])
                self.assertEqual(case["constraints"][0]["state"], "error")
                self.assertEqual(case["state"], "calculation_error")

    def test_model_min_max_known_boolean_errors_are_not_hidden_by_unknown(self):
        for function in ("min", "max"):
            for boolean in (False, True):
                for arguments in ("selected, capacity", "capacity, selected", "1, capacity, selected", "selected, 1, capacity"):
                    formula = f"{function}({arguments})"
                    with self.subTest(formula=formula, boolean=boolean):
                        model = minimal()
                        model["inputs"]["capacity"].update(value=None, basis="unknown")
                        model["inputs"]["selected"]["value"] = boolean
                        model["derived"][0]["formula"] = formula
                        case = lab.evaluate_model(model)["cases"][0]
                        self.assertEqual(case["derived"][0]["state"], "error")
                        self.assertIsNone(case["derived"][0]["value"])
                        self.assertEqual(case["constraints"][0]["state"], "error")
                        self.assertEqual(case["state"], "calculation_error")

    def test_model_relational_known_boolean_errors_are_not_hidden_by_unknown(self):
        for operator in ("<", "<=", ">", ">="):
            for boolean in (False, True):
                for left, right in (("selected", "capacity"), ("capacity", "selected")):
                    formula = f"{left} {operator} {right}"
                    with self.subTest(formula=formula, boolean=boolean):
                        model = minimal()
                        model["inputs"]["capacity"].update(value=None, basis="unknown")
                        model["inputs"]["selected"]["value"] = boolean
                        model["derived"] = []
                        model["constraints"][0]["formula"] = formula
                        case = lab.evaluate_model(model)["cases"][0]
                        self.assertEqual(case["constraints"][0]["state"], "error")
                        self.assertIsNone(case["constraints"][0]["value"])
                        self.assertEqual(case["state"], "calculation_error")

    def test_model_numeric_operations_preserve_unknown_without_known_errors(self):
        formulas = [f"{left} {operator} {right}" for operator in ("+", "-", "*", "/", "//", "%", "**")
                    for left, right in (("capacity", "2"), ("2", "capacity"))]
        formulas += ["capacity ** 12", "capacity ** -12", "13 ** capacity", "(-13) ** capacity",
                     "min(1, capacity)", "min(capacity, 1)", "max(1, capacity)", "max(capacity, 1)"]
        for formula in formulas:
            with self.subTest(formula=formula):
                model = minimal()
                model["inputs"]["capacity"].update(value=None, basis="unknown")
                model["derived"][0]["formula"] = formula
                case = lab.evaluate_model(model)["cases"][0]
                self.assertEqual(case["derived"][0]["state"], "unknown")
                self.assertIsNone(case["derived"][0]["value"])
                self.assertEqual(case["constraints"][0]["state"], "unknown")
                self.assertEqual(case["state"], "undetermined")

    def test_model_boolean_unknowns_preserve_decisive_values_and_equality(self):
        cases = [(f"{left} {operator} {right}", "unknown", None, "undetermined")
                 for operator in ("==", "!=") for boolean in ("False", "True")
                 for left, right in ((boolean, "capacity"), ("capacity", boolean))]
        cases += [
            ("capacity and False", "violated", False, "violates_model_constraints"),
            ("False and capacity", "violated", False, "violates_model_constraints"),
            ("capacity or True", "satisfied", True, "satisfies_model_constraints"),
            ("True or capacity", "satisfied", True, "satisfies_model_constraints"),
            ("capacity and True", "unknown", None, "undetermined"),
            ("True and capacity", "unknown", None, "undetermined"),
            ("capacity or False", "unknown", None, "undetermined"),
            ("False or capacity", "unknown", None, "undetermined"),
        ]
        for formula, state, value, overall in cases:
            with self.subTest(formula=formula):
                model = minimal()
                model["inputs"]["capacity"].update(value=None, basis="unknown")
                model["derived"] = []
                model["constraints"][0]["formula"] = formula
                case = lab.evaluate_model(model)["cases"][0]
                self.assertEqual((case["constraints"][0]["state"], case["constraints"][0]["value"]), (state, value))
                self.assertEqual(case["state"], overall)

    def test_model_comparison_chains_prioritize_known_errors_over_false_or_unknown(self):
        cases = [
            ("10 <= 5 <= capacity < True", "error", "calculation_error"),
            ("True < capacity <= 10 <= 5", "error", "calculation_error"),
            ("True == capacity < False", "error", "calculation_error"),
            ("capacity < True == True", "error", "calculation_error"),
            ("True == capacity < 2", "unknown", "undetermined"),
            ("False != capacity < 2", "unknown", "undetermined"),
            ("10 <= 5 <= capacity == True", "violated", "violates_model_constraints"),
        ]
        for formula, state, overall in cases:
            with self.subTest(formula=formula):
                model = minimal()
                model["inputs"]["capacity"].update(value=None, basis="unknown")
                model["derived"] = []
                model["constraints"][0]["formula"] = formula
                case = lab.evaluate_model(model)["cases"][0]
                self.assertEqual(case["constraints"][0]["state"], state)
                self.assertEqual(case["state"], overall)

    def test_cli_json_and_csv_preserve_known_errors_unknowns_and_boolean_decisions(self):
        cases = [
            ("derived", "True + capacity", "error", None, "calculation_error"),
            ("derived", "capacity ** -13", "error", None, "calculation_error"),
            ("derived", "max(capacity, False)", "error", None, "calculation_error"),
            ("derived", "2 + capacity", "unknown", None, "undetermined"),
            ("derived", "capacity ** 12", "unknown", None, "undetermined"),
            ("constraint", "capacity < True", "error", None, "calculation_error"),
            ("constraint", "10 <= 5 <= capacity < True", "error", None, "calculation_error"),
            ("constraint", "True == capacity", "unknown", None, "undetermined"),
            ("constraint", "capacity != False", "unknown", None, "undetermined"),
            ("constraint", "capacity and False", "violated", False, "violates_model_constraints"),
            ("constraint", "capacity or True", "satisfied", True, "satisfies_model_constraints"),
        ]
        for index, (kind, formula, state, value, overall) in enumerate(cases):
            with self.subTest(kind=kind, formula=formula):
                model = minimal()
                model["inputs"]["capacity"].update(value=None, basis="unknown")
                if kind == "derived":
                    model["derived"][0]["formula"] = formula
                else:
                    model["derived"] = []
                    model["constraints"][0]["formula"] = formula
                self.source.write_text(json.dumps(model), encoding="utf-8")
                output = self.output / str(index)
                process = subprocess.run([sys.executable, str(SCRIPT), str(self.source), "--output", str(output)], capture_output=True, encoding="utf-8")
                self.assertEqual(process.returncode, 0, process.stderr)
                result = json.loads((output / lab.OUTPUTS["json"]).read_text(encoding="utf-8"))
                case = result["cases"][0]
                item = case["derived" if kind == "derived" else "constraints"][0]
                rows = list(csv.DictReader(io.StringIO((output / lab.OUTPUTS["csv"]).read_text(encoding="utf-8"))))
                exported = next(row for row in rows if row["kind"] == kind)
                csv_value = "" if value is None else str(value).lower()
                with self.subTest(format="json"):
                    self.assertEqual((item["state"], item["value"]), (state, value))
                    self.assertEqual(case["state"], overall)
                with self.subTest(format="csv"):
                    self.assertEqual((exported["state"], exported["value"]), (state, csv_value))
                    self.assertEqual({row["case_state"] for row in rows}, {overall})

    def test_comparison_chains_match_conjunctions_with_unknowns_and_errors(self):
        values = {"missing": lab.Value("unknown", reason="未知")}
        cases = [
            ("10 <= 5 <= missing", "(10 <= 5) and (5 <= missing)", "known", False),
            ("missing <= 10 <= 5", "(missing <= 10) and (10 <= 5)", "known", False),
            ("10 <= 5 <= missing <= 20", "(10 <= 5) and (5 <= missing) and (missing <= 20)", "known", False),
            ("missing <= missing <= missing", "(missing <= missing) and (missing <= missing)", "unknown", None),
            ("1 <= 2 <= missing", "(1 <= 2) and (2 <= missing)", "unknown", None),
            ("1 <= 2 <= 3", "(1 <= 2) and (2 <= 3)", "known", True),
            ("False == True == missing", "(False == True) and (True == missing)", "known", False),
            ("True == True == missing", "(True == True) and (True == missing)", "unknown", None),
            ("10 <= 5 <= missing <= (1 / 0)", "(10 <= 5) and (5 <= missing) and (missing <= (1 / 0))", "error", None),
            ("10 <= 5 <= missing <= False < True", "(10 <= 5) and (5 <= missing) and (missing <= False) and (False < True)", "error", None),
            ("missing < 1 == True", "(missing < 1) and (1 == True)", "error", None),
        ]
        for chain, conjunction, state, expected in cases:
            with self.subTest(chain=chain):
                actual = lab.Formula(chain, {"missing"}).evaluate(values)
                expanded = lab.Formula(conjunction, {"missing"}).evaluate(values)
                self.assertEqual((actual.state, actual.value), (state, expected))
                self.assertEqual((actual.state, actual.value), (expanded.state, expanded.value))

    def test_comparison_chain_model_state_preserves_false_unknown_and_error(self):
        model = minimal()
        model["inputs"]["capacity"].update(value=None, basis="unknown")
        model["derived"] = []
        cases = [
            ("10 <= 5 <= capacity", "violated", "violates_model_constraints"),
            ("capacity <= 10 <= 5", "violated", "violates_model_constraints"),
            ("1 <= 2 <= capacity", "unknown", "undetermined"),
            ("1 <= 2 <= 3", "satisfied", "satisfies_model_constraints"),
            ("10 <= 5 <= capacity <= (1 / 0)", "error", "calculation_error"),
            ("10 <= 5 <= capacity <= 1 == True", "error", "calculation_error"),
        ]
        for formula, constraint_state, case_state in cases:
            with self.subTest(formula=formula):
                model["constraints"][0]["formula"] = formula
                actual = lab.evaluate_model(model)["cases"][0]
                self.assertEqual(actual["constraints"][0]["state"], constraint_state)
                self.assertEqual(actual["state"], case_state)

    def test_cli_comparison_chain_json_and_csv_preserve_known_violation(self):
        model = minimal()
        model["inputs"]["capacity"].update(value=None, basis="unknown")
        model["derived"] = []
        model["constraints"][0]["formula"] = "10 <= 5 <= capacity"
        self.source.write_text(json.dumps(model), encoding="utf-8")
        process = subprocess.run([sys.executable, str(SCRIPT), str(self.source), "--output", str(self.output)], capture_output=True, encoding="utf-8")
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads((self.output / lab.OUTPUTS["json"]).read_text(encoding="utf-8"))
        case = result["cases"][0]
        self.assertEqual(case["state"], "violates_model_constraints")
        self.assertEqual((case["constraints"][0]["state"], case["constraints"][0]["value"]), ("violated", False))
        rows = list(csv.DictReader(io.StringIO((self.output / lab.OUTPUTS["csv"]).read_text(encoding="utf-8"))))
        self.assertEqual({row["case_state"] for row in rows}, {"violates_model_constraints"})
        constraint = next(row for row in rows if row["kind"] == "constraint")
        self.assertEqual((constraint["state"], constraint["value"]), ("violated", "false"))

    def test_formulas_support_ordered_derived_values_and_limited_math(self):
        model = minimal()
        model["derived"].append({"id": "scaled", "label": "计算", "formula": "min(remaining, 5) + max(2, 3) + abs(-2) + 8 // 3 + 8 % 3 + 2 ** 3", "unit": "小时"})
        result = lab.evaluate_model(model)["cases"][0]
        self.assertEqual(result["derived"][1]["value"], 22)
        self.assertEqual(result["state"], "satisfies_model_constraints")

    def test_unsafe_ast_and_forward_references_rejected(self):
        for expression in ["__import__('os').getcwd()", "capacity.real", "[capacity][0]", "sum([1,2])", "(lambda: 2)()", "'text'", "capacity if True else 0", "future + 1", "min(a=1)", "max()"]:
            with self.subTest(expression=expression):
                model = minimal()
                model["derived"][0]["formula"] = expression
                with self.assertRaises(lab.ModelError):
                    lab.evaluate_model(model)

    def test_numeric_boolean_type_and_nonboolean_constraint_errors(self):
        for expression in ["True + 2", "capacity and selected", "capacity == True", "2 ** 13", "(-1) ** 0.5", "1e100 ** 12"]:
            with self.subTest(expression=expression):
                model = minimal()
                model["derived"][0]["formula"] = expression
                self.assertEqual(lab.evaluate_model(model)["cases"][0]["state"], "calculation_error")
        model = minimal()
        model["constraints"][0]["formula"] = "remaining"
        self.assertEqual(lab.evaluate_model(model)["cases"][0]["constraints"][0]["state"], "error")

    def test_override_roles_conflicts_and_types_are_enforced(self):
        variants = [
            {"plans": [{"id": "bad", "label": "坏方案", "overrides": {"capacity": 20}}]},
            {"scenarios": [{"id": "bad", "label": "坏情景", "overrides": {"selected": 2}}]},
            {"explore": {"selected": [2, 4]}},
            {"explore": {"capacity": [10, 20]}, "scenarios": [{"id": "bad", "label": "重复覆盖", "overrides": {"capacity": 30}}]},
            {"plans": [{"id": "bad", "label": "类型改变", "overrides": {"selected": True}}]},
        ]
        for variant in variants:
            with self.subTest(variant=variant):
                model = {**minimal(), **variant}
                with self.assertRaises(lab.ModelError):
                    lab.evaluate_model(model)

    def test_grid_exhaustive_count_no_truncation_and_limit(self):
        model = minimal()
        model["inputs"]["second"] = {"label": "第二条件", "value": 1, "basis": "assumed", "role": "condition"}
        model["explore"] = {"capacity": [8, 10, 12], "second": [1, 2]}
        model["plans"] = [{"id": "less", "label": "减少", "overrides": {"selected": 2}}]
        self.assertEqual(lab.evaluate_model(model)["case_count"], 12)
        model["explore"] = {"capacity": list(range(16)), "second": list(range(16))}
        model["plans"].append({"id": "more", "label": "增加", "overrides": {"selected": 5}})
        with self.assertRaisesRegex(lab.ModelError, "超过 512"):
            lab.evaluate_model(model)

    def test_unknown_basis_observed_source_and_finite_values(self):
        for changes in [{"value": None}, {"basis": "unknown"}, {"basis": "observed", "source": ""}, {"value": float("nan")}, {"value": 10 ** 1000}]:
            with self.subTest(changes=changes):
                model = minimal()
                model["inputs"]["capacity"].update(changes)
                with self.assertRaises(lab.ModelError):
                    lab.evaluate_model(model)
        model = minimal()
        model["inputs"]["capacity"].update(basis="observed", source="作者提供的表1")
        model["explore"] = {"capacity": [20]}
        self.assertEqual(lab.evaluate_model(model)["cases"][0]["inputs"]["capacity"]["basis"], "assumed")

    def test_duplicate_json_unknown_fields_and_no_constraints(self):
        self.source.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
        with self.assertRaisesRegex(lab.ModelError, "重复JSON字段"):
            lab.read_model(self.source)
        model = minimal()
        model["contraints"] = []
        with self.assertRaisesRegex(lab.ModelError, "未知字段"):
            lab.evaluate_model(model)
        model = minimal()
        model["constraints"] = []
        self.assertEqual(lab.evaluate_model(model)["cases"][0]["state"], "no_constraints")

    def test_exports_are_complete_and_html_has_safe_embedded_precomputed_data(self):
        model = example("university")
        model["title"] = '</script><img src=x onerror="alert(1)">'
        result = lab.evaluate_model(model)
        original = self.source.read_bytes()
        outputs = lab.write_outputs(result, self.source, self.output)
        self.assertEqual(set(outputs), {"json", "csv", "html"})
        saved = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
        self.assertEqual(len(saved["cases"]), 27)
        page = Path(outputs["html"]).read_text(encoding="utf-8")
        self.assertNotIn('</script><img src=x', page)
        marker = '<script type="application/json" id="condition-data">'
        payload = page.split(marker, 1)[1].split("</script>", 1)[0]
        self.assertEqual(json.loads(payload)["cases"], result["cases"])
        rows = list(csv.DictReader(io.StringIO(Path(outputs["csv"]).read_text(encoding="utf-8"))))
        self.assertEqual(len(rows), 27 * (8 + 3 + 5))
        self.assertEqual(len({row["case_id"] for row in rows}), 27)
        self.assertEqual(self.source.read_bytes(), original)

    def test_csv_text_cannot_be_interpreted_as_formula(self):
        model = minimal()
        model["inputs"]["capacity"]["label"] = "=SUM(A1:A2)"
        rows = list(csv.DictReader(io.StringIO(lab.render_csv(lab.evaluate_model(model)))))
        self.assertEqual(rows[0]["label"], "'=SUM(A1:A2)")

    def test_default_output_conflict_is_all_or_nothing_and_force_is_scoped(self):
        result = lab.evaluate_model(minimal())
        self.output.mkdir()
        unrelated = self.output / lab.OUTPUTS["html"]
        unrelated.write_text("用户文件", encoding="utf-8")
        for force in (False, True):
            with self.assertRaises(lab.ModelError):
                lab.write_outputs(result, self.source, self.output, force=force)
            self.assertFalse((self.output / lab.OUTPUTS["json"]).exists())
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "用户文件")
        unrelated.unlink()
        lab.write_outputs(result, self.source, self.output)
        with self.assertRaises(lab.ModelError):
            lab.write_outputs(result, self.source, self.output)
        result["model"]["title"] = "经授权替换产物"
        lab.write_outputs(result, self.source, self.output, force=True)
        self.assertEqual(json.loads((self.output / lab.OUTPUTS["json"]).read_text(encoding="utf-8"))["model"]["title"], "经授权替换产物")

    def test_force_cannot_overwrite_input_even_if_input_looks_owned(self):
        result = lab.evaluate_model(minimal())
        self.output.mkdir()
        source = self.output / lab.OUTPUTS["json"]
        source.write_text(json.dumps(result), encoding="utf-8")
        original = source.read_bytes()
        with self.assertRaisesRegex(lab.ModelError, "不能覆盖输入"):
            lab.write_outputs(result, source, self.output, force=True)
        self.assertEqual(source.read_bytes(), original)

    def test_interrupted_multi_output_write_restores_existing_outputs(self):
        result = lab.evaluate_model(minimal())
        lab.write_outputs(result, self.source, self.output)
        originals = {name: (self.output / name).read_bytes() for name in lab.OUTPUTS.values()}
        actual_replace = lab.os.replace
        calls = []
        def fail_second(source, destination):
            calls.append(destination)
            if len(calls) == 2:
                raise OSError("模拟第二文件替换失败")
            return actual_replace(source, destination)
        with mock.patch.object(lab.os, "replace", side_effect=fail_second):
            with self.assertRaises(OSError):
                lab.write_outputs(result, self.source, self.output, force=True)
        self.assertEqual({name: (self.output / name).read_bytes() for name in lab.OUTPUTS.values()}, originals)
        self.assertFalse((self.output / ".condition-lab.lock").exists())

    def test_cli_is_runnable_and_leaves_input_unchanged(self):
        original = self.source.read_bytes()
        process = subprocess.run([sys.executable, str(SCRIPT), str(self.source), "--output", str(self.output), "--format", "json"], capture_output=True, encoding="utf-8")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["case_count"], 1)
        self.assertEqual(self.source.read_bytes(), original)
        process = subprocess.run([sys.executable, str(SCRIPT), str(self.source), "--output", str(self.output), "--format", "json"], capture_output=True, encoding="utf-8")
        self.assertEqual(process.returncode, 2)
        self.assertIn("输出已存在", json.loads(process.stderr)["error"])


if __name__ == "__main__":
    unittest.main()
