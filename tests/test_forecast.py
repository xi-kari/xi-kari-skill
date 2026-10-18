import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def module():
    spec = importlib.util.spec_from_file_location('forecast', ROOT / 'scripts' / 'forecast.py')
    target = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(target)
    return target


def sample(order=1, identifier='forecast-1'):
    return {
        'id': identifier, 'created_at': '2026-01-01T12:00:00Z',
        'theory_sha256': json.loads((ROOT / 'source/source-manifest.json').read_text(encoding='utf-8-sig'))['sha256'],
        'skill_version': '6.0.0.dev1', 'host_model': 'synthetic-test-model',
        'evidence_kind': 'synthetic', 'order': order, 'question': '虚构队列是否积压？',
        'target': '窗口内队列长度超过十', 'resolution_rule': '由测试记录的完整标签判定；标签缺失为未决。',
        'window': {'start': '2026-01-02T00:00:00Z', 'end': '2026-02-01T00:00:00Z'},
        'input_cutoff': '2026-01-01T00:00:00Z', 'baseline_time': '2025-12-31T00:00:00Z',
        'scope': {'object': '虚构队列', 'circles': ['工作组'], 'affected_positions': ['等待者']},
        'baselines': [{'id': 'state', 'type': 'state_continuation' if order > 1 else 'recent_state',
                       'expression': {'type': 'probability', 'value': 0.2, 'basis': '仅用于手算测试的固定参数。'}}],
        'mechanisms': [{'rule_id': 'CM-LOAD', 'anchors': ['6.6']}],
        'paths': [{'id': 'path-1', 'parent': None, 'order': order, 'conditions': ['到达持续'],
                   'description': '积压增加', 'early_signals': ['等待增长'], 'reverse_signals': ['到达减少'],
                   'stop_conditions': ['口径改变']}],
        'expression': {'type': 'probability', 'value': 0.8, 'basis': '仅用于手算测试的固定参数。'},
        'calibration_plan': {'metrics': ['brier', 'log_loss', 'window_coverage'], 'description': '保留完整标签；不作经验支持。'},
        'decision_threshold': {'applicable': False, 'reason': '不作行动决定'},
        'pause_conditions': ['监测离线'], 'retire_conditions': ['对象失效'], 'evidence_refs': ['synthetic-fixture'],
    }


def outcome(identifier='forecast-1', status='not_supported'):
    return {'forecast_id': identifier, 'resolved_at': '2026-02-02T00:00:00Z',
            'outcome_source': '完整的合成测试标签', 'observed': {'value': 0, 'event_time': None},
            'status': status, 'path_match': [], 'model_updates': [],
            **({'reason': '完整标签暂不可获得或原对象合同不再适用。'} if status not in {'supported', 'not_supported'} else {})}


class ForecastTests(unittest.TestCase):
    def setUp(self):
        self.target = module()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.registry = self.directory / 'forecasts.json'

    def write(self, name, payload):
        path = self.directory / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
        return path

    def register(self, record=None):
        return self.target.register_forecast(self.registry, self.write('input.json', record or sample()))

    def resolve(self, record=None):
        return self.target.resolve_forecast(self.registry, self.write('outcome.json', record or outcome()))

    def test_missing_every_required_field_is_rejected(self):
        for field in sample():
            with self.subTest(field=field):
                record = sample()
                record.pop(field)
                with self.assertRaises(ValueError):
                    self.target.validate_forecast(record)

    def test_register_preserves_input_and_freezes_record(self):
        path = self.write('input.json', sample())
        before = path.read_bytes()
        result = self.target.register_forecast(self.registry, path)
        self.assertEqual(path.read_bytes(), before)
        self.assertIn('registered_at', result)
        self.assertEqual(self.target.load_registry(self.registry)['forecasts'][0], result)

    def test_duplicate_id_cannot_change_target_window_or_scope(self):
        self.register()
        before = self.registry.read_bytes()
        for field, value in [('target', '另一个目标'), ('scope', {'object': '别人', 'circles': ['外部'], 'affected_positions': ['别人']}),
                             ('window', {'start': '2026-02-02T00:00:00Z', 'end': '2026-03-01T00:00:00Z'})]:
            record = sample()
            record[field] = value
            with self.assertRaises(ValueError):
                self.register(record)
            self.assertEqual(self.registry.read_bytes(), before)

    def test_manual_record_change_is_detected(self):
        self.register()
        ledger = json.loads(self.registry.read_text(encoding='utf-8'))
        ledger['forecasts'][0]['target'] = 'changed'
        self.write('forecasts.json', ledger)
        with self.assertRaises(ValueError):
            self.target.load_registry(self.registry)

    def test_resolve_only_appends_and_scores_brier_example(self):
        saved = self.register()
        result = self.resolve()
        ledger = self.target.load_registry(self.registry)
        self.assertEqual(ledger['forecasts'], [saved])
        self.assertEqual(len(ledger['resolutions']), 1)
        self.assertAlmostEqual(result['scores']['brier'], 0.64)
        self.assertAlmostEqual(result['scores']['log_loss'], -math.log(0.2))
        self.assertAlmostEqual(result['baseline_scores']['state']['brier'], 0.04)

    def test_later_resolution_retains_both_and_report_counts_once(self):
        self.register()
        first = outcome(status='undetermined')
        first['observed']['value'] = None
        self.resolve(first)
        final = outcome()
        final['resolved_at'] = '2026-02-03T00:00:00Z'
        final['model_updates'] = ['取得完整标签后追加，保留未决记录。']
        self.resolve(final)
        ledger = self.target.load_registry(self.registry)
        self.assertEqual(len(ledger['resolutions']), 2)
        report = self.target.report_registry(ledger)
        self.assertEqual(report['orders']['1']['resolved'], 1)
        self.assertEqual(report['orders']['1']['resolution_records'], 2)

    def test_all_five_statuses_preserved_missing_labels_never_zero(self):
        for index, status in enumerate(sorted(self.target.STATUSES)):
            identifier = f'forecast-{index}'
            self.register(sample(identifier=identifier))
            record = outcome(identifier, status)
            if status not in {'supported', 'not_supported'}:
                record['observed']['value'] = None
            saved = self.resolve(record)
            if status not in {'supported', 'not_supported'}:
                self.assertEqual(saved['scores'], {})
        report = self.target.report_registry(self.target.load_registry(self.registry))
        self.assertEqual(report['orders']['1']['statuses'], {key: 1 for key in sorted(self.target.STATUSES)})

    def test_probability_numbers_and_nonfinite_values_are_strict(self):
        for value in [-0.1, 1.1, True, '0.8', None, math.nan, math.inf]:
            with self.subTest(value=value):
                record = sample()
                record['expression']['value'] = value
                with self.assertRaises(ValueError):
                    self.target.validate_forecast(record)

    def test_timezones_and_temporal_order_are_required(self):
        for field, value in [('created_at', '2026-01-01'), ('created_at', '2026-01-01T12:00:00'),
                             ('input_cutoff', '2026-01-02T00:00:00Z'), ('baseline_time', '2026-01-03T00:00:00Z')]:
            record = sample()
            record[field] = value
            with self.assertRaises(ValueError):
                self.target.validate_forecast(record)
        record = sample()
        record['window']['end'] = record['window']['start']
        with self.assertRaises(ValueError):
            self.target.validate_forecast(record)

    def test_resolution_before_deadline_or_future_is_rejected(self):
        self.register()
        for value in ['2026-01-10T00:00:00Z', '2099-01-01T00:00:00Z', '2026-02-02']:
            record = outcome()
            record['resolved_at'] = value
            with self.assertRaises(ValueError):
                self.resolve(record)

    def test_duplicate_or_out_of_order_resolution_is_rejected(self):
        self.register()
        self.resolve()
        before = self.registry.read_bytes()
        with self.assertRaises(ValueError):
            self.resolve()
        self.assertEqual(self.registry.read_bytes(), before)

    def test_unknown_forecast_path_and_injected_scores_are_rejected(self):
        self.register()
        for field, value in [('forecast_id', 'missing'), ('path_match', ['missing']), ('scores', {'brier': 0})]:
            record = outcome()
            record[field] = value
            with self.assertRaises(ValueError):
                self.resolve(record)

    def test_probability_labels_are_binary_and_missing_labels_rejected(self):
        self.register()
        for value in [None, 0.3, True, '0', math.nan]:
            record = outcome()
            record['observed']['value'] = value
            with self.assertRaises(ValueError):
                self.resolve(record)

    def test_log_loss_boundary_is_infinite_without_nonstandard_json(self):
        record = sample()
        record['expression']['value'] = 1.0
        self.register(record)
        saved = self.resolve()
        self.assertIsNone(saved['scores']['log_loss'])
        self.assertTrue(saved['scores']['log_loss_infinite'])
        self.assertNotIn('Infinity', self.registry.read_text(encoding='utf-8'))

    def test_interval_and_window_coverage_include_exact_boundaries(self):
        record = sample()
        record['expression'] = {'type': 'interval', 'lower': 2, 'upper': 5, 'unit': 'days', 'basis': '合成数字区间'}
        record['baselines'][0]['expression'] = {'type': 'interval', 'lower': 0, 'upper': 1, 'unit': 'days', 'basis': '合成基线'}
        record['calibration_plan']['metrics'] = ['interval_coverage', 'window_coverage']
        self.register(record)
        result = outcome()
        result['observed'] = {'value': 2, 'event_time': record['window']['start']}
        saved = self.resolve(result)
        self.assertEqual(saved['scores']['interval_coverage'], 1)
        self.assertNotIn('window_coverage', saved['scores'])
        self.assertEqual(saved['baseline_scores']['state']['interval_coverage'], 0)

    def test_rank_direction_and_none_do_not_fabricate_scores(self):
        for kind, value in [('rank', ['path-1']), ('direction', '增加'), ('none', None)]:
            identifier = f'forecast-{kind}'
            record = sample(identifier=identifier)
            record['expression'] = {'type': kind, 'value': value, 'basis': '没有数值测量依据'}
            record['baselines'][0]['expression'] = copy.deepcopy(record['expression'])
            self.register(record)
            result = outcome(identifier, 'supported')
            result['observed']['value'] = None
            saved = self.resolve(result)
            self.assertEqual(saved['scores'], {})
            self.assertTrue(saved['scoring_notes'])

    def test_orders_are_separate_and_recursive_baselines_required(self):
        for order in [1, 2, 3]:
            record = sample(order, f'forecast-{order}')
            if order > 1:
                with self.assertRaises(ValueError):
                    self.target.validate_forecast(record)
                for kind in ['direct_long_term', 'shallower_continuation']:
                    record['baselines'].append({'id': kind, 'type': kind, 'expression': copy.deepcopy(record['expression'])})
            self.register(record)
            self.resolve(outcome(f'forecast-{order}'))
        report = self.target.report_registry(self.target.load_registry(self.registry))
        self.assertEqual(set(report['orders']), {'1', '2', '3'})
        for value in report['orders'].values():
            self.assertEqual(value['resolved'], 1)
        self.assertNotIn('total_hit_rate', report)
        self.assertEqual(report['capability'], 'unverified')

    def test_teaching_records_never_count_as_capability_evidence(self):
        record = sample()
        record['evidence_kind'] = 'teaching'
        self.register(record)
        self.resolve()
        report = self.target.report_registry(self.target.load_registry(self.registry))
        self.assertEqual(report['capability_evidence_records'], 0)
        self.assertEqual(report['degradation_threshold'], 'pending')

    def test_theory_mismatch_and_modified_source_are_rejected(self):
        record = sample()
        record['theory_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            self.register(record)
        with mock.patch.object(self.target, 'SOURCE', self.write('other-source.md', 'changed')):
            with self.assertRaises(ValueError):
                self.register()

    def test_supersedes_keeps_old_forecast(self):
        self.register()
        newer = sample(identifier='forecast-2')
        newer['supersedes'] = 'forecast-1'
        self.register(newer)
        self.assertEqual(len(self.target.load_registry(self.registry)['forecasts']), 2)
        newer['id'] = 'forecast-3'
        newer['supersedes'] = 'absent'
        with self.assertRaises(ValueError):
            self.register(newer)

    def test_package_and_lock_writes_are_rejected(self):
        record = self.write('input.json', sample())
        forbidden = ROOT / 'tests' / 'must-not-exist-forecast.json'
        with self.assertRaises(OSError):
            self.target.register_forecast(forbidden, record)
        self.assertFalse(forbidden.exists())

    def test_write_conflict_and_existing_lock_preserve_bytes(self):
        self.register()
        before = self.registry.read_bytes()
        with self.assertRaises(ValueError):
            self.target.save_registry(self.registry, self.target.load_registry(self.registry), b'stale')
        lock = self.registry.with_name(self.registry.name + '.lock')
        lock.write_bytes(b'owned')
        with self.assertRaises(ValueError):
            self.resolve()
        self.assertEqual(self.registry.read_bytes(), before)
        self.assertEqual(lock.read_bytes(), b'owned')

    def test_invalid_existing_file_is_never_overwritten(self):
        self.registry.write_text('{}', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.register()
        self.assertEqual(self.registry.read_text(encoding='utf-8'), '{}')

    def test_check_reports_scope_without_certification(self):
        self.register()
        result = self.target.check_registry(self.target.load_registry(self.registry))
        self.assertTrue(result['ok'])
        self.assertNotIn('registration_completeness', result)
        self.assertEqual(result['capability'], 'unverified')

    def test_live_registration_cannot_backfill_expired_window(self):
        record = sample()
        record['evidence_kind'] = 'live'
        with self.assertRaises(ValueError):
            self.register(record)

    def test_cli_foreign_working_directory_all_commands(self):
        record = self.write('input.json', sample())
        result = self.write('outcome.json', outcome())
        def run(*args):
            process = subprocess.run([sys.executable, str(ROOT / 'scripts/forecast.py'), '--registry', str(self.registry), *map(str, args)],
                                     cwd=self.directory, capture_output=True, encoding='utf-8')
            self.assertEqual(process.returncode, 0, process.stderr)
            return json.loads(process.stdout)
        run('register', '--record', record)
        self.assertEqual(len(run('list')), 1)
        self.assertEqual(run('show', 'forecast-1')['forecast']['id'], 'forecast-1')
        run('resolve', '--record', result)
        self.assertTrue(run('check')['ok'])
        self.assertEqual(run('report')['capability'], 'unverified')

    def test_nonevaluable_status_requires_reason(self):
        self.register()
        record = outcome(status='not_evaluable')
        record['observed']['value'] = None
        record.pop('reason')
        with self.assertRaises(ValueError):
            self.resolve(record)

    def test_observed_details_preserve_qualitative_results(self):
        record = sample()
        record['expression'] = {'type': 'direction', 'value': '增加', 'basis': '合成方向'}
        record['baselines'][0]['expression'] = copy.deepcopy(record['expression'])
        self.register(record)
        result = outcome(status='supported')
        result['observed'] = {'value': None, 'event_time': None, 'details': '公开离职之后未出现持续级联。'}
        saved = self.resolve(result)
        self.assertEqual(saved['observed']['details'], result['observed']['details'])
        self.assertEqual(saved['scores'], {})

    def test_preregistered_persistent_underperformance_downgrades(self):
        for index, month in enumerate([2, 2, 3, 3]):
            record = sample(identifier=f'forecast-{index}')
            record['evidence_kind'] = 'backtest'
            record['calibration_plan']['degradation_policy'] = {'metric': 'brier', 'minimum_per_period': 2, 'consecutive_months': 2}
            self.register(record)
            result = outcome(record['id'])
            result['resolved_at'] = f'2026-{month:02d}-02T00:00:00Z'
            self.resolve(result)
        report = self.target.report_registry(self.target.load_registry(self.registry))
        self.assertEqual(report['capability'], 'scenario_only')
        self.assertEqual(report['degradation_decisions'][0]['basis'], '16.22')
        self.assertEqual(report['degradation_decisions'][0]['theory_sha256'], sample()['theory_sha256'])
        self.assertEqual(report['degradation_decisions'][0]['expression_type'], 'probability')
        self.assertEqual(report['capability_scope'], 'matching_degradation_decisions_only')

    def test_missing_month_and_small_samples_do_not_invent_persistence(self):
        for index, month in enumerate([2, 4]):
            record = sample(identifier=f'forecast-{index}')
            record['evidence_kind'] = 'backtest'
            record['calibration_plan']['degradation_policy'] = {'metric': 'brier', 'minimum_per_period': 1, 'consecutive_months': 2}
            self.register(record)
            result = outcome(record['id'])
            result['resolved_at'] = f'2026-{month:02d}-02T00:00:00Z'
            self.resolve(result)
        report = self.target.report_registry(self.target.load_registry(self.registry))
        self.assertEqual(report['capability'], 'unverified')
        self.assertFalse(report['degradation_decisions'])

    def test_unknown_metrics_are_explicitly_unscored(self):
        record = sample()
        record['calibration_plan']['metrics'] = ['domain_metric_not_implemented']
        self.register(record)
        saved = self.resolve()
        self.assertEqual(saved['scores'], {})
        self.assertTrue(any('domain_metric_not_implemented' in note for note in saved['scoring_notes']))

    def test_duplicate_json_keys_are_rejected(self):
        path = self.directory / 'duplicate.json'
        path.write_text('{"id":"a","id":"b"}', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.target.read_json(path)

    def test_baseline_interval_units_and_mixed_orders_are_rejected(self):
        record = sample()
        record['paths'][0]['order'] = 2
        with self.assertRaises(ValueError):
            self.target.validate_forecast(record)
        record = sample()
        record['expression'] = {'type': 'interval', 'lower': 0, 'upper': 1, 'unit': 'days', 'basis': 'test'}
        record['baselines'][0]['expression'] = {'type': 'interval', 'lower': 0, 'upper': 1, 'unit': 'years', 'basis': 'test'}
        with self.assertRaises(ValueError):
            self.target.validate_forecast(record)

    def test_score_corruption_is_rejected_even_if_digest_recalculated(self):
        self.register()
        self.resolve()
        data = self.target.load_registry(self.registry)
        data['resolutions'][0]['scores']['brier'] = 0
        data['resolutions'][0]['record_sha256'] = self.target.digest(data['resolutions'][0])
        self.write('forecasts.json', data)
        with self.assertRaises(ValueError):
            self.target.load_registry(self.registry)

    def test_parent_paths_must_form_a_local_acyclic_graph(self):
        for parents in [('absent',), ('path-1',), ('path-2', 'path-1'), ('path-2', 'absent')]:
            with self.subTest(parents=parents):
                record = sample()
                record['paths'] = [{**copy.deepcopy(record['paths'][0]), 'id': f'path-{index + 1}', 'parent': parent}
                                   for index, parent in enumerate(parents)]
                with self.assertRaises(ValueError):
                    self.target.validate_forecast(record)
        record = sample()
        record['paths'].append({**copy.deepcopy(record['paths'][0]), 'id': 'path-2', 'parent': 'path-1'})
        self.target.validate_forecast(record)

    def test_baselines_cannot_change_the_evaluation_window(self):
        record = sample()
        record['baselines'][0]['window'] = {'start': record['window']['start'], 'end': '2026-01-20T00:00:00Z'}
        with self.assertRaises(ValueError):
            self.target.validate_forecast(record)

    def test_report_separates_target_scope_rule_units_and_metrics(self):
        changes = [('target', '另一目标'), ('scope', {'object': '另一对象', 'circles': ['工作组'], 'affected_positions': ['等待者']}),
                   ('resolution_rule', '另一标签口径'), ('calibration_plan', {'metrics': ['brier'], 'description': '仅Brier'})]
        for index, (field, value) in enumerate(changes):
            record = sample(identifier=f'variant-{index}')
            record[field] = value
            self.register(record)
            self.resolve(outcome(record['id']))
        self.register()
        self.resolve()
        report = self.target.report_registry(self.target.load_registry(self.registry))
        self.assertEqual(len(report['groups']), 5)
        self.assertTrue(all(group['resolved'] == 1 for group in report['groups']))

    def test_degradation_does_not_pool_different_baseline_methods(self):
        for index, method in enumerate(['state_continuation', 'historical_frequency']):
            record = sample(identifier=f'forecast-{index}')
            record['evidence_kind'] = 'backtest'
            record['baselines'][0]['type'] = method
            record['calibration_plan']['degradation_policy'] = {'metric': 'brier', 'minimum_per_period': 2, 'consecutive_months': 1}
            self.register(record)
            self.resolve(outcome(record['id']))
        report = self.target.report_registry(self.target.load_registry(self.registry))
        self.assertFalse(report['degradation_decisions'])
        self.assertEqual(len(report['groups'][0]['baseline_comparisons']), 2)

    def test_registry_schema_version_is_not_boolean(self):
        self.write('forecasts.json', {'format': self.target.FORMAT, 'schema_version': True, 'forecasts': [], 'resolutions': []})
        with self.assertRaises(ValueError):
            self.target.load_registry(self.registry)

    def test_append_time_cannot_precede_registration(self):
        self.register()
        self.resolve()
        data = self.target.load_registry(self.registry)
        result = data['resolutions'][0]
        result['appended_at'] = result['resolved_at']
        result['record_sha256'] = self.target.digest(result)
        self.write('forecasts.json', data)
        with self.assertRaises(ValueError):
            self.target.load_registry(self.registry)

    def test_unresolved_labels_are_not_capability_evidence(self):
        record = sample()
        record['evidence_kind'] = 'backtest'
        self.register(record)
        result = outcome(status='not_evaluable')
        result['observed']['value'] = None
        self.resolve(result)
        report = self.target.report_registry(self.target.load_registry(self.registry))
        self.assertEqual(report['capability_evidence_records'], 0)

    def test_numbers_too_large_for_computation_fail_as_validation_errors(self):
        record = sample()
        record['expression']['value'] = 10 ** 400
        with self.assertRaises(ValueError):
            self.target.validate_forecast(record)

    def test_live_window_starts_after_registration_and_rejects_prior_event(self):
        record = sample()
        record['evidence_kind'] = 'live'
        record['window']['start'] = '2026-01-16T00:00:00Z'
        with mock.patch.object(self.target, 'utcnow', return_value=datetime(2026, 1, 15, tzinfo=timezone.utc)):
            self.register(record)
        result = outcome(status='supported')
        result['observed'] = {'value': 1, 'event_time': '2026-01-10T00:00:00Z'}
        with mock.patch.object(self.target, 'utcnow', return_value=datetime(2026, 2, 3, tzinfo=timezone.utc)):
            with self.assertRaises(ValueError):
                self.resolve(result)
            result['observed']['event_time'] = '2026-01-16T00:00:00Z'
            self.resolve(result)
        self.assertEqual(len(self.target.load_registry(self.registry)['resolutions']), 1)

    def test_log_loss_infinite_pairs_remain_explicit_and_json_safe(self):
        for index, (prediction, baseline) in enumerate([(1, 0), (0, 1)]):
            record = sample(identifier=f'boundary-{index}')
            record['expression']['value'] = prediction
            record['baselines'][0]['expression']['value'] = baseline
            self.register(record)
            self.resolve(outcome(record['id']))
        report = self.target.report_registry(self.target.load_registry(self.registry))
        pair = report['groups'][0]['baseline_comparisons'][0]
        for side in ['model', 'baseline']:
            self.assertEqual(pair[side]['log_loss'], {'n': 2, 'mean': None, 'infinite': True})
        self.assertIsNone(pair['gain']['log_loss'])
        json.dumps(report, allow_nan=False)

    def test_report_separates_interval_units(self):
        for unit in ['days', 'years']:
            record = sample(identifier=unit)
            record['expression'] = {'type': 'interval', 'lower': 0, 'upper': 1, 'unit': unit, 'basis': 'synthetic'}
            record['baselines'][0]['expression'] = copy.deepcopy(record['expression'])
            record['calibration_plan']['metrics'] = ['interval_coverage']
            self.register(record)
            self.resolve(outcome(unit))
        self.assertEqual(len(self.target.report_registry(self.target.load_registry(self.registry))['groups']), 2)

    def test_report_retains_rolling_windows_as_comparable_when_contract_matches(self):
        for identifier, start, end in [('a', '2026-01-02T00:00:00Z', '2026-02-01T00:00:00Z'),
                                        ('b', '2026-02-02T00:00:00Z', '2026-03-04T00:00:00Z')]:
            record = sample(identifier=identifier)
            record['window'] = {'start': start, 'end': end}
            if identifier == 'b':
                record['baseline_time'] = '2026-01-31T00:00:00Z'
                record['input_cutoff'] = '2026-02-01T00:00:00Z'
                record['created_at'] = '2026-02-01T12:00:00Z'
            self.register(record)
            result = outcome(identifier)
            result['resolved_at'] = '2026-03-05T00:00:00Z'
            self.resolve(result)
        groups = self.target.report_registry(self.target.load_registry(self.registry))['groups']
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]['resolved'], 2)

    def test_report_does_not_label_partly_missing_thresholds_as_preregistered(self):
        self.register()
        record = sample(identifier='with-policy')
        record['calibration_plan']['degradation_policy'] = {'metric': 'brier', 'minimum_per_period': 2, 'consecutive_months': 2}
        self.register(record)
        report = self.target.report_registry(self.target.load_registry(self.registry))
        self.assertEqual(report['degradation_threshold'], 'partial')


if __name__ == '__main__':
    unittest.main()
