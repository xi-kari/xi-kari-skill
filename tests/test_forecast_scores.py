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


if __name__ == '__main__':
    unittest.main()
