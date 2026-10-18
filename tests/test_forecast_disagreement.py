import copy
import json
from pathlib import Path
import tempfile
import unittest

from test_forecast import module, outcome, sample


class ForecastDisagreementTests(unittest.TestCase):
    def setUp(self):
        self.tool = module()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.registry = self.root / 'forecasts.json'

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
        return path

    def register(self, record):
        return self.tool.register_forecast(self.registry, self.write('input.json', record))

    def report(self):
        return self.tool.report_registry(self.tool.load_registry(self.registry))

    def record(self, identifier, model=0.8, baselines=(0.2, 0.4)):
        record = sample(identifier=identifier)
        record['expression']['value'] = model
        record['baselines'] = [
            {'id': f'baseline-{index}', 'type': method,
             'expression': {'type': 'probability', 'value': value, 'basis': 'Synthetic comparison.'}}
            for index, (method, value) in enumerate(zip(('recent_state', 'trend'), baselines))
        ]
        return record

    def test_all_baselines_must_differ_and_pending_records_count(self):
        for record in (self.record('different'), self.record('pending'),
                       self.record('matches-one', baselines=(0.8, 0.4)),
                       self.record('matches-both', baselines=(0.8, 0.8))):
            self.register(record)
        for identifier in ('different', 'matches-one'):
            self.tool.resolve_forecast(self.registry, self.write('outcome.json', outcome(identifier)))
        report = self.report()
        summary = report['disagreement']
        self.assertEqual(summary['registered'], 4)
        self.assertEqual(summary['eligible_records'], 4)
        self.assertEqual(summary['disagreement_records'], 2)
        self.assertEqual(summary['rate'], 0.5)
        self.assertEqual(summary['forecast_ids'], ['different', 'pending'])
        groups = report['pooled_on_disagreement']
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]['forecast_ids'], ['different'])
        self.assertEqual(groups[0]['resolved'], 1)
        comparisons = {row['baseline_type']: row for row in groups[0]['baseline_comparisons']}
        for method, baseline in [('recent_state', 0.04), ('trend', 0.16)]:
            scores = comparisons[method]['metrics']['brier']
            self.assertEqual(scores['n'], 1)
            self.assertAlmostEqual(scores['model_mean'], 0.64)
            self.assertAlmostEqual(scores['baseline_mean'], baseline)
            self.assertEqual((scores['better'], scores['worse'], scores['tied']), (0, 1, 0))
        self.assertNotIn('_pairs', groups[0])
        self.assertEqual(report['pooled'][0]['resolved'], 2)

    def test_unknown_and_incomparable_baselines_are_excluded(self):
        unknown = self.record('unknown')
        unknown['expression'] = {'type': 'none', 'value': None, 'basis': 'Unknown.'}
        for baseline in unknown['baselines']:
            baseline['expression'] = copy.deepcopy(unknown['expression'])
        missing_options = self.record('missing-options')
        missing_options['expression'] = {'type': 'direction', 'value': 'up', 'basis': 'Qualitative.'}
        missing_options['calibration_plan']['metrics'] = ['qualitative_path_match']
        for baseline in missing_options['baselines']:
            baseline['expression'] = dict(missing_options['expression'], value='down')
        unknown_method = self.record('unknown-method')
        unknown_method['baselines'][1]['type'] = 'unrecognized'
        for record in (unknown, missing_options, unknown_method, self.record('eligible')):
            self.register(record)
        summary = self.report()['disagreement']
        self.assertEqual((summary['registered'], summary['eligible_records'], summary['excluded_records']), (4, 1, 3))
        self.assertEqual(summary['rate'], 1.0)
        self.assertEqual(summary['forecast_ids'], ['eligible'])
        self.assertEqual({row['forecast_id'] for row in summary['excluded']},
                         {'unknown', 'missing-options', 'unknown-method'})
        self.assertTrue(all(row['reason'] for row in summary['excluded']))

    def test_empty_or_no_eligible_denominator_is_null(self):
        report = self.tool.report_registry({'forecasts': [], 'resolutions': []})
        self.assertIsNone(report['disagreement']['rate'])
        self.assertEqual(report['pooled_on_disagreement'], [])
        record = self.record('unsupported')
        for baseline in record['baselines']:
            baseline['type'] = 'unrecognized-' + baseline['id']
        self.register(record)
        self.assertIsNone(self.report()['disagreement']['rate'])

    def test_prediction_semantics_ignore_basis_and_optional_metadata(self):
        expressions = [
            ({'type': 'probability', 'value': 0.8}, {'value': 0.7}),
            ({'type': 'direction', 'value': 'up', 'options': ['up', 'down']}, {'value': 'down'}),
            ({'type': 'rank', 'value': ['up', 'down'], 'options': ['up', 'down']}, {'value': ['down', 'up']}),
            ({'type': 'interval', 'lower': 3, 'upper': 4, 'unit': 'items', 'nominal_coverage': 0.8}, {'upper': 5}),
            ({'type': 'time_window', 'start': '2026-01-03T00:00:00Z', 'end': '2026-01-15T00:00:00Z'},
             {'end': '2026-01-16T00:00:00Z'}),
        ]
        for index, (expression, change) in enumerate(expressions):
            for different in (False, True):
                record = self.record(f'expression-{index}-{different}')
                record['expression'] = dict(expression, basis='Model explanation.')
                record['calibration_plan']['metrics'] = ['qualitative_path_match']
                for baseline in record['baselines']:
                    baseline['expression'] = dict(expression, basis='Different explanation.', note='Metadata.')
                    if different:
                        baseline['expression'].update(change)
                self.register(record)
        summary = self.report()['disagreement']
        self.assertEqual((summary['eligible_records'], summary['disagreement_records']), (10, 5))
        self.assertEqual(summary['rate'], 0.5)

    def test_time_zones_numeric_types_and_option_order_do_not_create_disagreement(self):
        records = []
        probability = self.record('numeric', model=1, baselines=(1.0, 1.0))
        records.append(probability)
        time_window = self.record('time')
        time_window['expression'] = {'type': 'time_window', 'start': '2026-01-03T00:00:00Z',
                                     'end': '2026-01-15T00:00:00Z', 'basis': 'Model.'}
        time_window['calibration_plan']['metrics'] = ['window_coverage']
        for baseline in time_window['baselines']:
            baseline['expression'] = dict(time_window['expression'], start='2026-01-02T19:00:00-05:00',
                                          end='2026-01-14T19:00:00-05:00')
        records.append(time_window)
        direction = self.record('options')
        direction['expression'] = {'type': 'direction', 'value': 'up', 'options': ['up', 'down'], 'basis': 'Model.'}
        direction['calibration_plan']['metrics'] = ['qualitative_path_match']
        for baseline in direction['baselines']:
            baseline['expression'] = dict(direction['expression'], options=['down', 'up'])
        records.append(direction)
        for record in records:
            self.register(record)
        summary = self.report()['disagreement']
        self.assertEqual(summary['eligible_records'], 3)
        self.assertEqual(summary['disagreement_records'], 0)
        self.assertEqual(summary['rate'], 0.0)

    def test_incompatible_domains_are_not_counted_as_different_predictions(self):
        for kind in ('direction', 'rank', 'time_window'):
            record = self.record(kind)
            record['calibration_plan']['metrics'] = ['qualitative_path_match']
            if kind == 'time_window':
                expression = {'type': kind, 'start': '2026-01-03T00:00:00Z', 'end': '2026-01-15T00:00:00Z',
                              'nominal_coverage': 0.8, 'basis': 'Model.'}
                change = {'nominal_coverage': 0.9}
            else:
                expression = {'type': kind, 'value': 'up' if kind == 'direction' else ['up'],
                              'options': ['up', 'down'], 'basis': 'Model.'}
                change = {'options': ['up', 'flat']}
            record['expression'] = expression
            for baseline in record['baselines']:
                baseline['expression'] = dict(expression, **change)
            self.register(record)
        summary = self.report()['disagreement']
        self.assertEqual(summary['eligible_records'], 0)
        self.assertEqual(summary['excluded_records'], 3)
        self.assertIsNone(summary['rate'])

    def test_full_rank_disagreement_can_have_a_tied_top_rank_score(self):
        record = self.record('rank')
        record['expression'] = {'type': 'rank', 'value': ['a', 'b', 'c'], 'options': ['a', 'b', 'c'], 'basis': 'Model.'}
        for baseline in record['baselines']:
            baseline['expression'] = dict(record['expression'], value=['a', 'c', 'b'])
        record['calibration_plan']['metrics'] = ['rank_top_hit']
        self.register(record)
        result = outcome('rank', status='supported')
        result['observed'] = {'category': 'a', 'value': None, 'event_time': None}
        self.tool.resolve_forecast(self.registry, self.write('outcome.json', result))
        report = self.report()
        self.assertEqual(report['disagreement']['rate'], 1.0)
        for comparison in report['pooled_on_disagreement'][0]['baseline_comparisons']:
            self.assertEqual(comparison['metrics']['rank_top_hit']['tied'], 1)

    def test_legacy_single_baseline_report_is_read_only(self):
        record = self.register(self.record('legacy', baselines=(0.2,)))
        record.pop('validation_version')
        record['record_sha256'] = self.tool.digest(record)
        self.write('forecasts.json', {'format': self.tool.FORMAT, 'schema_version': 1,
                                     'forecasts': [record], 'resolutions': []})
        before = self.registry.read_bytes()
        report = self.report()
        self.assertEqual(report['disagreement']['eligible_records'], 1)
        self.assertEqual(report['disagreement']['rate'], 1.0)
        self.assertEqual(report['pooled_on_disagreement'], [])
        self.assertEqual(self.registry.read_bytes(), before)

    def test_evidence_kinds_have_separate_disagreement_rates(self):
        teaching = self.record('teaching')
        teaching['evidence_kind'] = 'teaching'
        backtest = self.record('backtest', baselines=(0.8, 0.4))
        backtest['evidence_kind'] = 'backtest'
        for record in (teaching, backtest):
            self.register(record)
        groups = {row['evidence_kind']: row for row in self.report()['disagreement']['by_group']}
        self.assertEqual(groups['teaching']['rate'], 1.0)
        self.assertEqual(groups['backtest']['rate'], 0.0)

    def test_legacy_missing_nominal_duplicate_types_and_absent_baselines_are_excluded(self):
        missing_nominal = self.record('missing-nominal')
        expression = {'type': 'interval', 'lower': 3, 'upper': 4, 'unit': 'items', 'basis': 'Legacy.'}
        missing_nominal['expression'] = expression
        for baseline in missing_nominal['baselines']:
            baseline['expression'] = dict(expression, upper=5)
        duplicate = self.record('duplicate')
        duplicate['baselines'][1]['type'] = 'recent_state'
        absent = self.record('absent')
        absent['baselines'] = []
        summary = self.tool.forecast_scores.disagreement_summary(
            [missing_nominal, duplicate, absent], self.tool.comparable_baselines)
        self.assertEqual(summary['eligible_records'], 0)
        self.assertEqual(summary['excluded_records'], 3)
        self.assertIsNone(summary['rate'])

    def test_disagreement_interval_subset_uses_paired_ratios(self):
        record = self.record('interval')
        expression = {'type': 'interval', 'lower': 3, 'upper': 4, 'unit': 'items',
                      'nominal_coverage': 0.8, 'basis': 'Synthetic.'}
        record['expression'] = expression
        record['calibration_plan']['metrics'] = ['interval_score', 'interval_coverage']
        for baseline in record['baselines']:
            baseline['expression'] = dict(expression, lower=0, upper=1000)
        self.register(record)
        result = outcome('interval')
        result['observed']['value'] = 5
        self.tool.resolve_forecast(self.registry, self.write('outcome.json', result))
        group = self.report()['pooled_on_disagreement'][0]
        for comparison in group['baseline_comparisons']:
            scores = comparison['metrics']['interval_score']
            self.assertAlmostEqual(scores['geometric_mean_ratio'], 0.011)
            self.assertEqual(scores['better'], 1)


if __name__ == '__main__':
    unittest.main()
