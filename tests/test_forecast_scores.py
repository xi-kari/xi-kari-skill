import copy
import importlib.util
import json
import math
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('forecast_scores', ROOT / 'scripts/forecast_scores.py')
scoring = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scoring)


def evaluation_window():
    return {'start': '2026-10-01T00:00:00Z', 'end': '2026-12-31T00:00:00Z'}


def time_expression(**changes):
    result = {'type': 'time_window', 'start': '2026-11-01T00:00:00Z',
              'end': '2026-11-15T00:00:00Z', 'basis': 'Synthetic interval for arithmetic checks.'}
    result.update(changes)
    return result


def interval_expression(**changes):
    result = {'type': 'interval', 'lower': 3, 'upper': 4, 'unit': 'items',
              'nominal_coverage': 0.8, 'basis': 'Synthetic interval for arithmetic checks.'}
    result.update(changes)
    return result


class TimeWindowScoringTests(unittest.TestCase):
    def test_model_and_baseline_cover_event_with_distinct_lengths(self):
        observed = {'value': 1, 'event_time': '2026-11-05T00:00:00Z'}
        window = evaluation_window()
        model, notes = scoring.score(time_expression(), observed, window, ['window_coverage'])
        baseline, _ = scoring.score(time_expression(**window), observed, window, ['window_coverage'])
        self.assertEqual(model, {'window_coverage': 1, 'window_length_days': 14.0})
        self.assertEqual(baseline, {'window_coverage': 1, 'window_length_days': 91.0})
        self.assertEqual(notes, [])

    def test_prediction_interval_not_evaluation_window_determines_coverage(self):
        observed = {'value': 1, 'event_time': '2026-11-16T00:00:00Z'}
        scores, _ = scoring.score(time_expression(), observed, evaluation_window(), ['window_coverage'])
        self.assertEqual(scores['window_coverage'], 0)

    def test_explicit_no_event_scores_zero_without_inventing_event_time(self):
        scores, notes = scoring.score(time_expression(nominal_coverage=0.8),
                                     {'value': 0, 'event_time': None}, evaluation_window(),
                                     ['window_coverage', 'interval_score'])
        self.assertEqual(scores['window_coverage'], 0)
        self.assertEqual(scores['window_length_days'], 14.0)
        self.assertNotIn('interval_score', scores)
        self.assertTrue(notes)

    def test_absence_measurement_at_or_after_evaluation_end_scores_zero(self):
        for measured_at in ('2026-12-31T00:00:00Z', '2027-01-01T00:00:00Z',
                            '2026-12-30T19:00:00-05:00'):
            with self.subTest(measured_at=measured_at):
                scores, notes = scoring.score(time_expression(nominal_coverage=0.8),
                                             {'value': 0, 'event_time': measured_at}, evaluation_window(),
                                             ['window_coverage', 'interval_score'])
                self.assertEqual(scores, {'window_coverage': 0, 'window_length_days': 14.0})
                self.assertNotIn('interval_score', scores)
                self.assertTrue(notes)

    def test_absence_measurement_cannot_precede_evaluation_end_or_lack_timezone(self):
        for measured_at in ('2026-12-30T23:59:59Z', '2026-11-05T00:00:00Z',
                            '2026-12-31T00:00:00', 'invalid'):
            with self.subTest(measured_at=measured_at), self.assertRaises(ValueError):
                scoring.score(time_expression(), {'value': 0, 'event_time': measured_at},
                              evaluation_window(), ['window_coverage'])

    def test_unknown_event_is_not_scored_as_absent(self):
        for observed in ({}, {'value': None, 'event_time': None}):
            with self.subTest(observed=observed):
                scores, notes = scoring.score(time_expression(), observed, evaluation_window(), ['window_coverage'])
                self.assertEqual(scores, {'window_length_days': 14.0})
                self.assertTrue(notes)

    def test_prediction_and_evaluation_boundaries_are_inclusive(self):
        window = evaluation_window()
        for expr in (time_expression(), time_expression(**window)):
            for event in (expr['start'], expr['end']):
                with self.subTest(event=event):
                    scores, _ = scoring.score(expr, {'value': 1, 'event_time': event}, window, ['window_coverage'])
                    self.assertEqual(scores['window_coverage'], 1)

    def test_duration_and_coverage_use_absolute_instants(self):
        expr = time_expression(start='2026-11-01T00:00:00-04:00', end='2026-11-15T00:00:00-05:00')
        scores, _ = scoring.score(expr, {'value': 1, 'event_time': '2026-11-01T04:00:00Z'},
                                  evaluation_window(), ['window_coverage'])
        self.assertAlmostEqual(scores['window_length_days'], 14 + 1 / 24)
        self.assertEqual(scores['window_coverage'], 1)

    def test_predicted_window_must_be_ordered_and_contained(self):
        for changes in ({'start': '2026-09-30T23:59:59Z'}, {'end': '2026-12-31T00:00:01Z'},
                        {'start': '2026-11-15T00:00:00Z'}, {'start': '2026-11-16T00:00:00Z'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                scoring.validate_expression(time_expression(**changes), evaluation_window())

    def test_evaluation_window_must_be_valid(self):
        for window in (None, {}, {'start': '2026-10-01T00:00:00Z'},
                       {'start': '2026-10-01T00:00:00Z', 'end': '2026-10-01T00:00:00Z'},
                       {'start': '2026-10-02T00:00:00Z', 'end': '2026-10-01T00:00:00Z'}):
            with self.subTest(window=window), self.assertRaises(ValueError):
                scoring.validate_expression(time_expression(), window)

    def test_timezones_and_basis_are_required(self):
        for changes in ({'start': '2026-11-01'}, {'end': '2026-11-15T00:00:00'},
                        {'start': None}, {'end': 'not a date'}, {'basis': ''}, {'basis': None}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                scoring.validate_expression(time_expression(**changes), evaluation_window())

    def test_optional_nominal_coverage_is_strict(self):
        scoring.validate_expression(time_expression(), evaluation_window())
        scoring.validate_expression(time_expression(nominal_coverage=0.8), evaluation_window())
        for nominal in (None, 0, 1, -0.1, 1.1, True, '0.8', math.nan, math.inf, 10 ** 400):
            with self.subTest(nominal=nominal), self.assertRaises(ValueError):
                scoring.validate_expression(time_expression(nominal_coverage=nominal), evaluation_window())

    def test_interval_score_uses_days_and_outside_distance(self):
        expr = time_expression(nominal_coverage=0.8)
        for event, expected in (('2026-11-05T00:00:00Z', 14),
                                ('2026-10-31T00:00:00Z', 24),
                                ('2026-11-16T00:00:00Z', 24)):
            with self.subTest(event=event):
                scores, notes = scoring.score(expr, {'value': 1, 'event_time': event}, evaluation_window(),
                                               ['window_coverage', 'interval_score'])
                self.assertAlmostEqual(scores['interval_score'], expected)
                self.assertFalse(scores['interval_score_infinite'])
                self.assertEqual(notes, [])
                json.dumps(scores, allow_nan=False)

    def test_interval_score_requires_nominal_and_metric_registration(self):
        observed = {'value': 1, 'event_time': '2026-11-05T00:00:00Z'}
        scores, notes = scoring.score(time_expression(), observed, evaluation_window(), ['interval_score'])
        self.assertNotIn('interval_score', scores)
        self.assertTrue(notes)
        scores, _ = scoring.score(time_expression(nominal_coverage=0.8), observed,
                                  evaluation_window(), ['window_coverage'])
        self.assertNotIn('interval_score', scores)
        scores, _ = scoring.score(time_expression(nominal_coverage=0.8), observed,
                                  evaluation_window(), ['interval_score'])
        self.assertNotIn('window_coverage', scores)

    def test_invalid_or_contradictory_event_labels_are_rejected(self):
        for observed in ({'value': 1, 'event_time': None},
                         {'value': 0, 'event_time': '2026-11-05T00:00:00Z'},
                         {'value': None, 'event_time': '2026-11-05T00:00:00Z'},
                         {'value': True, 'event_time': None}, {'value': '0', 'event_time': None},
                         {'value': 0.3, 'event_time': None}, {'value': math.nan, 'event_time': None},
                         {'value': 1, 'event_time': '2026-09-30T23:59:59Z'},
                         {'value': 1, 'event_time': '2026-12-31T00:00:01Z'},
                         {'value': 1, 'event_time': '2026-11-05T00:00:00'}):
            with self.subTest(observed=observed), self.assertRaises(ValueError):
                scoring.score(time_expression(), observed, evaluation_window(), ['window_coverage'])

    def test_other_expression_types_are_not_silently_scored(self):
        for kind in ('probability', 'direction', 'none', 'unknown'):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                scoring.score({'type': kind, 'basis': 'fixture'}, {'value': 0},
                              evaluation_window(), ['window_coverage'])

    def test_inputs_are_not_modified(self):
        args = [time_expression(nominal_coverage=0.8), {'value': 1, 'event_time': '2026-11-05T00:00:00Z'},
                evaluation_window(), ['window_coverage', 'interval_score']]
        before = copy.deepcopy(args)
        scoring.validate_expression(args[0], args[2])
        scoring.score(*args)
        self.assertEqual(args, before)


class NumericIntervalScoringTests(unittest.TestCase):
    def test_narrow_interval_beats_wide_interval_despite_missing_coverage(self):
        observed = {'value': 5, 'event_time': None}
        metrics = ['interval_score', 'interval_coverage']
        model, notes = scoring.score(interval_expression(), observed, evaluation_window(), metrics)
        baseline, _ = scoring.score(interval_expression(lower=0, upper=1000), observed,
                                    evaluation_window(), metrics)
        self.assertAlmostEqual(model['interval_score'], 11)
        self.assertEqual(baseline['interval_score'], 1000)
        self.assertLess(model['interval_score'], baseline['interval_score'])
        self.assertEqual(model['interval_coverage'], 0)
        self.assertEqual(baseline['interval_coverage'], 1)
        self.assertEqual(model['interval_width'], 1)
        self.assertEqual(notes, [])
        self.assertFalse(any('gain' in key for key in model))

    def test_inside_and_boundary_values_cost_only_width(self):
        for value in (3, 3.5, 4):
            with self.subTest(value=value):
                scores, _ = scoring.score(interval_expression(), {'value': value}, evaluation_window(),
                                          ['interval_score', 'interval_coverage'])
                self.assertEqual(scores['interval_score'], 1)
                self.assertFalse(scores['interval_score_infinite'])
                self.assertEqual(scores['interval_coverage'], 1)

    def test_outside_penalties_are_symmetric_and_follow_nominal_coverage(self):
        for nominal, expected in ((0.5, 9), (0.8, 21), (0.9, 41)):
            for value in (1, 6):
                with self.subTest(nominal=nominal, value=value):
                    scores, _ = scoring.score(interval_expression(nominal_coverage=nominal),
                                              {'value': value}, evaluation_window(), ['interval_score'])
                    self.assertAlmostEqual(scores['interval_score'], expected)

    def test_degenerate_numeric_interval_is_valid_and_scores_point_hit(self):
        expr = interval_expression(lower=4, upper=4)
        scoring.validate_expression(expr, evaluation_window(), require_nominal=True)
        scores, _ = scoring.score(expr, {'value': 4}, evaluation_window(), ['interval_score', 'interval_coverage'])
        self.assertEqual(scores['interval_score'], 0)
        self.assertEqual(scores['interval_width'], 0)
        self.assertEqual(scores['interval_coverage'], 1)

    def test_nominal_can_be_optional_for_validation_but_required_for_new_scoring(self):
        expr = interval_expression()
        expr.pop('nominal_coverage')
        scoring.validate_expression(expr, evaluation_window())
        with self.assertRaises(ValueError):
            scoring.validate_expression(expr, evaluation_window(), require_nominal=True)
        with self.assertRaises(ValueError):
            scoring.score(expr, {'value': 5}, evaluation_window(), ['interval_score'])
        scoring.validate_expression(time_expression(), evaluation_window(), require_nominal=True)

    def test_interval_nominal_must_be_finite_and_strictly_between_zero_and_one(self):
        for nominal in (None, 0, 1, -0.1, 1.1, True, '0.8', math.nan, math.inf, 10 ** 400):
            with self.subTest(nominal=nominal), self.assertRaises(ValueError):
                scoring.validate_expression(interval_expression(nominal_coverage=nominal), evaluation_window())

    def test_interval_bounds_unit_and_quantity_are_checked(self):
        invalid = [{'lower': 5}, {'lower': None}, {'lower': True}, {'upper': '4'}, {'lower': math.nan},
                   {'upper': math.inf}, {'upper': 10 ** 400}, {'unit': ''}, {'unit': None},
                   {'quantity': 'probability'}, {'basis': ''}]
        for changes in invalid:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                scoring.validate_expression(interval_expression(**changes), evaluation_window())

    def test_missing_observation_is_not_replaced_by_zero(self):
        for observed in ({}, {'value': None}):
            with self.subTest(observed=observed):
                scores, notes = scoring.score(interval_expression(), observed, evaluation_window(),
                                              ['interval_score', 'interval_coverage'])
                self.assertEqual(scores, {'interval_width': 1, 'interval_width_infinite': False})
                self.assertTrue(notes)

    def test_observations_must_be_finite_numbers(self):
        for value in (True, '5', math.nan, math.inf, -math.inf, 10 ** 400):
            with self.subTest(value=value), self.assertRaises(ValueError):
                scoring.score(interval_expression(), {'value': value}, evaluation_window(), ['interval_score'])

    def test_only_registered_metrics_are_scored_and_window_coverage_is_not_applicable(self):
        observed = {'value': 5, 'event_time': '2026-11-05T00:00:00Z'}
        scores, notes = scoring.score(interval_expression(), observed, evaluation_window(), ['interval_score'])
        self.assertIn('interval_score', scores)
        self.assertNotIn('interval_coverage', scores)
        self.assertEqual(notes, [])
        scores, notes = scoring.score(interval_expression(), observed, evaluation_window(),
                                      ['interval_coverage', 'window_coverage'])
        self.assertIn('interval_coverage', scores)
        self.assertNotIn('interval_score', scores)
        self.assertNotIn('window_coverage', scores)
        self.assertTrue(notes)

    def test_finite_float_input_overflow_has_null_and_explicit_metric_flags(self):
        for expr, value, width_overflows in (
            (interval_expression(lower=-1e308, upper=1e308), 0, True),
            (interval_expression(lower=0, upper=1), 1e308, False),
            (interval_expression(lower=0, upper=1, nominal_coverage=math.nextafter(1.0, 0.0)), 1e300, False),
        ):
            with self.subTest(expr=expr):
                scores, _ = scoring.score(expr, {'value': value}, evaluation_window(),
                                          ['interval_score', 'interval_coverage'])
                self.assertIsNone(scores['interval_score'])
                self.assertTrue(scores['interval_score_infinite'])
                self.assertEqual(scores['interval_width_infinite'], width_overflows)
                self.assertEqual(scores['interval_coverage'], int(expr['lower'] <= value <= expr['upper']))
                json.dumps(scores, allow_nan=False)

    def test_large_finite_integer_width_overflow_is_json_safe(self):
        scores, _ = scoring.score(interval_expression(lower=-(10 ** 308), upper=10 ** 308),
                                  {'value': 0}, evaluation_window(), ['interval_score'])
        self.assertIsNone(scores['interval_width'])
        self.assertTrue(scores['interval_width_infinite'])
        self.assertIsNone(scores['interval_score'])
        self.assertTrue(scores['interval_score_infinite'])
        json.dumps(scores, allow_nan=False)

    def test_large_finite_score_is_not_misclassified_as_infinite(self):
        scores, _ = scoring.score(interval_expression(lower=0, upper=1e307), {'value': 1e307},
                                  evaluation_window(), ['interval_score'])
        self.assertEqual(scores['interval_score'], 1e307)
        self.assertFalse(scores['interval_score_infinite'])
        json.dumps(scores, allow_nan=False)

    def test_numeric_inputs_are_not_modified(self):
        args = [interval_expression(), {'value': 5}, evaluation_window(), ['interval_score', 'interval_coverage']]
        before = copy.deepcopy(args)
        scoring.validate_expression(args[0], args[2], require_nominal=True)
        scoring.score(*args)
        self.assertEqual(args, before)


if __name__ == '__main__':
    unittest.main()
