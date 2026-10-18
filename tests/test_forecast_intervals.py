import json
import math
from pathlib import Path
import tempfile
import unittest

from test_forecast import module, outcome, sample


def interval_record(identifier='interval-1', unit='items', nominal=0.8):
    record = sample(identifier=identifier)
    record['target'] = 'Synthetic numeric target ' + identifier
    record['expression'] = {'type': 'interval', 'lower': 3, 'upper': 4, 'unit': unit,
                            'basis': 'Synthetic arithmetic fixture', 'nominal_coverage': nominal}
    record['baselines'][0].update(type='recent_state')
    record['baselines'][0]['expression'] = dict(record['expression'], lower=0, upper=1000)
    record['calibration_plan']['metrics'] = ['interval_score', 'interval_coverage']
    return record


class ForecastIntervalIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tool = module()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.registry = self.root / 'registry.json'

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False), encoding='utf-8')
        return path

    def register(self, record):
        return self.tool.register_forecast(self.registry, self.write('input.json', record))

    def resolve(self, identifier='interval-1', value=5):
        result = outcome(identifier)
        result['observed']['value'] = value
        return self.tool.resolve_forecast(self.registry, self.write('result.json', result))

    def report(self):
        result = self.tool.report_registry(self.tool.load_registry(self.registry))
        json.dumps(result, allow_nan=False)
        return result

    def ratio(self, pairs):
        rows = [({'interval_score': a, 'interval_score_infinite': ai},
                 {'interval_score': b, 'interval_score_infinite': bi}) for a, b, ai, bi in pairs]
        result = self.tool.paired_metric_summary(rows, 'interval_score')
        json.dumps(result, allow_nan=False)
        return result

    def test_numeric_interval_score_controls_comparison_instead_of_wide_coverage(self):
        self.register(interval_record())
        saved = self.resolve()
        self.assertAlmostEqual(saved['scores']['interval_score'], 11)
        self.assertEqual(saved['baseline_scores']['state']['interval_score'], 1000)
        report = self.report()
        contract = report['by_contract'][0]['baseline_comparisons'][0]
        self.assertAlmostEqual(contract['gain']['interval_score'], 989)
        for metric in ('interval_coverage', 'interval_width', 'window_coverage', 'window_length_days'):
            self.assertNotIn(metric, contract['gain'])
        pooled = report['pooled'][0]['baseline_comparisons'][0]['metrics']
        self.assertNotIn('interval_coverage', pooled)
        self.assertEqual((pooled['interval_score']['better'], pooled['interval_score']['worse']), (1, 0))

    def test_new_and_version_two_intervals_require_nominal_for_model_and_baselines(self):
        for side in ('model', 'baseline'):
            for mode in ('new', 'version_two'):
                with self.subTest(side=side, mode=mode):
                    record = interval_record()
                    expr = record['expression'] if side == 'model' else record['baselines'][0]['expression']
                    expr.pop('nominal_coverage')
                    if mode == 'version_two':
                        record['validation_version'] = 2
                    with self.assertRaisesRegex(ValueError, 'nominal_coverage'):
                        self.tool.validate_forecast(record, new=mode == 'new')

    def test_model_and_baseline_nominal_coverages_must_match(self):
        record = interval_record()
        record['baselines'][0]['expression']['nominal_coverage'] = 0.9
        with self.assertRaises(ValueError):
            self.register(record)
        self.assertFalse(self.registry.exists())

    def test_cross_unit_pool_uses_geometric_score_ratios_without_raw_averages(self):
        for identifier, unit, model_width, baseline_width in [('a', 'days', 2, 4), ('b', 'years', 8, 2)]:
            record = interval_record(identifier, unit)
            record['expression'].update(lower=0, upper=model_width)
            record['baselines'][0]['expression'].update(lower=0, upper=baseline_width)
            self.register(record)
            self.resolve(identifier, value=1)
        report = self.report()
        self.assertEqual(len(report['by_contract']), 2)
        self.assertEqual(len(report['pooled']), 1)
        group = report['pooled'][0]
        comparison = group['baseline_comparisons'][0]['metrics']['interval_score']
        self.assertEqual(comparison['n'], 2)
        self.assertAlmostEqual(comparison['geometric_mean_ratio'], math.sqrt(2))
        self.assertEqual((comparison['better'], comparison['worse'], comparison['tied']), (1, 1, 0))
        for key in ('model_mean', 'baseline_mean', 'mean_difference'):
            self.assertNotIn(key, comparison)
        for metric in ('interval_score', 'interval_width', 'interval_coverage'):
            self.assertNotIn(metric, group['metrics'])

    def test_log_ratios_avoid_overflow_before_averaging(self):
        result = self.ratio([(1e300, 1e-300, False, False), (1e-300, 1e300, False, False)])
        self.assertAlmostEqual(result['geometric_mean_ratio'], 1)
        self.assertEqual(result['ratio_status'], 'finite')
        self.assertAlmostEqual(result['mean_log_ratio'], 0)

    def test_zero_ratio_cases_are_explicit_and_json_safe(self):
        both = self.ratio([(0, 0, False, False)])
        self.assertEqual(both['geometric_mean_ratio'], 1)
        self.assertEqual(both['ratio_counts']['both_zero'], 1)
        self.assertIn('1', both['both_zero_convention'])
        zero = self.ratio([(0, 1, False, False), (1, 2, False, False)])
        self.assertEqual(zero['geometric_mean_ratio'], 0)
        self.assertEqual(zero['ratio_status'], 'zero')
        infinite = self.ratio([(1, 0, False, False)])
        self.assertIsNone(infinite['geometric_mean_ratio'])
        self.assertEqual(infinite['ratio_status'], 'infinite')
        mixed = self.ratio([(0, 1, False, False), (1, 0, False, False)])
        self.assertIsNone(mixed['geometric_mean_ratio'])
        self.assertEqual(mixed['ratio_status'], 'undefined')

    def test_overflow_scores_never_claim_exact_ratios_or_false_ties(self):
        for rows, expected in [([(None, 1, True, False)], (0, 1, 0, 0)),
                               ([(1, None, False, True)], (1, 0, 0, 0)),
                               ([(None, None, True, True)], (0, 0, 0, 1))]:
            with self.subTest(rows=rows):
                result = self.ratio(rows)
                self.assertIsNone(result['geometric_mean_ratio'])
                self.assertEqual(result['ratio_status'], 'undefined')
                self.assertEqual(tuple(result[key] for key in ('better', 'worse', 'tied', 'undetermined')), expected)

    def test_unrepresentable_geometric_mean_retains_log_value_without_infinity(self):
        for rows, status in [([(1e300, 1e-300, False, False)], 'overflow'),
                             ([(1e-300, 1e300, False, False)], 'underflow')]:
            result = self.ratio(rows)
            self.assertIsNone(result['geometric_mean_ratio'])
            self.assertEqual(result['ratio_status'], status)
            self.assertTrue(math.isfinite(result['mean_log_ratio']))

    def test_interval_coverage_is_calibrated_separately_at_each_nominal_level(self):
        for identifier, nominal, value in [('a', 0.8, 3.5), ('b', 0.8, 5), ('c', 0.9, 5)]:
            self.register(interval_record(identifier, nominal=nominal))
            self.resolve(identifier, value=value)
        group = self.report()['pooled'][0]
        calibration = group['interval_calibration']
        self.assertEqual(calibration['purpose'], 'calibration_only')
        self.assertEqual(calibration['model'], [
            {'nominal_coverage': 0.8, 'n': 2, 'observed_coverage': 0.5},
            {'nominal_coverage': 0.9, 'n': 1, 'observed_coverage': 0.0},
        ])
        self.assertEqual(calibration['baselines'][0]['baseline_type'], 'recent_state')
        self.assertTrue(all(row['observed_coverage'] == 1 for row in calibration['baselines'][0]['bins']))
        self.assertNotIn('interval_coverage', group['baseline_comparisons'][0]['metrics'])

    def test_metric_infinite_flags_count_in_means_and_reports(self):
        record = interval_record()
        record['expression'].update(lower=-1e308, upper=1e308)
        self.register(record)
        self.resolve(value=0)
        report = self.report()
        metrics = report['by_contract'][0]['metrics']
        for metric in ('interval_score', 'interval_width'):
            self.assertEqual(metrics[metric], {'n': 1, 'mean': None, 'infinite': True})
        summary = report['pooled'][0]['baseline_comparisons'][0]['metrics']['interval_score']
        self.assertEqual(summary['ratio_status'], 'undefined')
        self.assertEqual(summary['worse'], 1)

    def test_finite_mean_does_not_overflow_while_summing_large_scores(self):
        result = self.tool.mean_scores([{'interval_score': 1e308, 'interval_score_infinite': False}] * 4)
        self.assertEqual(result['interval_score']['mean'], 1e308)
        self.assertFalse(result['interval_score']['infinite'])
        json.dumps(result, allow_nan=False)

    def test_legacy_interval_records_remain_readable_and_new_outcomes_keep_old_scores(self):
        frozen = interval_record()
        frozen['expression'].pop('nominal_coverage')
        frozen['baselines'][0]['expression'].pop('nominal_coverage')
        frozen['calibration_plan']['metrics'] = ['interval_coverage', 'window_coverage']
        frozen['registered_at'] = '2026-01-01T13:00:00Z'
        frozen['record_sha256'] = self.tool.digest(frozen)
        prior = outcome('interval-1')
        prior['observed'] = {'value': 5, 'event_time': '2026-01-15T00:00:00Z'}
        prior.update(scores={'interval_coverage': 0, 'window_coverage': 1},
                     baseline_scores={'state': {'interval_coverage': 1, 'window_coverage': 1}},
                     scoring_notes=[], appended_at='2026-02-02T01:00:00Z')
        prior['record_sha256'] = self.tool.digest(prior)
        legacy = {'format': self.tool.FORMAT, 'schema_version': 1, 'forecasts': [frozen], 'resolutions': [prior]}
        self.write('registry.json', legacy)
        before = self.registry.read_bytes()
        self.tool.load_registry(self.registry)
        self.assertEqual(before, self.registry.read_bytes())
        next_result = outcome('interval-1', status='supported')
        next_result['resolved_at'] = '2026-02-03T00:00:00Z'
        next_result['observed'] = {'value': 3, 'event_time': '2026-01-15T00:00:00Z'}
        saved = self.tool.resolve_forecast(self.registry, self.write('next.json', next_result))
        self.assertEqual(saved['scores'], {'interval_coverage': 1, 'window_coverage': 1})
        loaded = self.tool.load_registry(self.registry)
        self.assertEqual(loaded['forecasts'], [frozen])
        self.assertEqual(loaded['resolutions'][0], prior)

    def test_frozen_legacy_interval_version_two_score_keeps_its_original_semantics(self):
        frozen = interval_record()
        frozen['calibration_plan']['metrics'] = ['interval_coverage', 'window_coverage']
        frozen['registered_at'] = '2026-01-01T13:00:00Z'
        frozen['record_sha256'] = self.tool.digest(frozen)
        prior = outcome('interval-1')
        prior['observed'] = {'value': 5, 'event_time': '2026-01-15T00:00:00Z'}
        prior.update(scores={'interval_coverage': 0}, baseline_scores={'state': {'interval_coverage': 1}},
                     scoring_notes=['window_coverage仅适用于time_window表达，不把共同评价窗当预测区间'],
                     scoring_version=2, appended_at='2026-02-02T01:00:00Z')
        prior['record_sha256'] = self.tool.digest(prior)
        registry = {'format': self.tool.FORMAT, 'schema_version': 1, 'forecasts': [frozen], 'resolutions': [prior]}
        self.write('registry.json', registry)
        before = self.registry.read_bytes()
        loaded = self.tool.load_registry(self.registry)
        self.assertEqual(loaded['resolutions'][0], prior)
        self.assertEqual(before, self.registry.read_bytes())

    def test_time_window_coverage_and_lengths_never_vote_on_model_quality(self):
        record = interval_record()
        record['expression'] = {'type': 'time_window', **record['window'], 'basis': 'Synthetic time window'}
        record['baselines'][0]['expression'] = dict(record['expression'])
        record['calibration_plan']['metrics'] = ['window_coverage']
        self.register(record)
        result = outcome('interval-1')
        result['observed'] = {'value': 1, 'event_time': '2026-01-15T00:00:00Z'}
        self.tool.resolve_forecast(self.registry, self.write('time.json', result))
        report = self.report()
        self.assertEqual(report['by_contract'][0]['baseline_comparisons'][0]['gain'], {})
        self.assertEqual(report['pooled'][0]['baseline_comparisons'][0]['metrics'], {})

    def test_new_legacy_interval_outcome_keeps_new_validation_separate_from_old_scoring(self):
        frozen=interval_record()
        frozen['evidence_kind']='live'
        frozen['expression'].pop('nominal_coverage')
        frozen['baselines'][0]['expression'].pop('nominal_coverage')
        frozen['calibration_plan']['metrics']=['interval_coverage']
        frozen['registered_at']='2026-01-01T13:00:00Z'
        frozen['record_sha256']=self.tool.digest(frozen)
        self.write('registry.json',{'format':self.tool.FORMAT,'schema_version':1,'forecasts':[frozen],'resolutions':[]})
        result=outcome('interval-1');result['observed']={'value':5,'event_time':'2026-01-15T00:00:00Z'}
        saved=self.tool.resolve_forecast(self.registry,self.write('result.json',result))
        self.assertEqual(saved['scoring_version'],1)
        self.assertEqual(saved['validation_version'],2)
        saved['observed']['event_time']=None
        with self.assertRaisesRegex(ValueError,'event_time'):
            self.tool.validate_resolution(saved,frozen)


if __name__ == '__main__':
    unittest.main()
