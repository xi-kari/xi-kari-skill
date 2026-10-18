import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_forecast import module, outcome, sample


REGISTERED = '2026-10-17T12:00:00Z'
REGISTER_CLOCK = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)
RESOLVE_CLOCK = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)


class ForecastLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tool = module()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.registry = self.directory / 'forecasts.json'
        clock = mock.patch.object(self.tool, 'utcnow', return_value=REGISTER_CLOCK)
        self.now = clock.start()
        self.addCleanup(clock.stop)

    def write(self, name, value):
        path = self.directory / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
        return path

    def live(self, identifier='live-1'):
        record = sample(identifier=identifier)
        record.update(evidence_kind='live', created_at='2026-10-17T00:00:00Z',
                      input_cutoff='2026-10-16T00:00:00Z', baseline_time='2026-10-15T00:00:00Z')
        record['window'] = {'start': '2026-10-18T00:00:00Z', 'end': '2026-11-01T00:00:00Z'}
        record['calibration_plan']['metrics'] = ['brier']
        return record

    def result(self, identifier='live-1', status='not_supported'):
        record = outcome(identifier, status)
        record['resolved_at'] = '2026-11-02T00:00:00Z'
        record['observed'] = {'value': 0, 'event_time': '2026-10-20T00:00:00Z'}
        return record

    def register(self, record):
        return self.tool.register_forecast(self.registry, self.write('registration.json', record))

    def resolve(self, record):
        self.now.return_value = RESOLVE_CLOCK
        return self.tool.resolve_forecast(self.registry, self.write('resolution.json', record))

    def frozen_fixture(self, *, validation_version=None, scoring_version=None, with_result=True):
        forecast = self.live()
        forecast['registered_at'] = REGISTERED
        if validation_version is None or validation_version == 1:
            forecast['window']['start'] = '2026-10-01T00:00:00Z'
        if validation_version is not None:
            forecast['validation_version'] = validation_version
        forecast['record_sha256'] = self.tool.digest(forecast)
        result = self.result()
        result['observed']['event_time'] = None
        if scoring_version is not None:
            result['scoring_version'] = scoring_version
        result['scores'], result['baseline_scores'], result['scoring_notes'] = self.tool.computed_result(result, forecast)
        result['appended_at'] = '2026-11-02T01:00:00Z'
        result['record_sha256'] = self.tool.digest(result)
        registry = {'format': self.tool.FORMAT, 'schema_version': 1,
                    'forecasts': [forecast], 'resolutions': [result] if with_result else []}
        self.write(self.registry.name, registry)
        self.now.return_value = RESOLVE_CLOCK
        return registry

    def test_live_registration_rejects_started_window_with_actual_timestamp(self):
        record = self.live()
        record['window']['start'] = '2026-10-01T00:00:00Z'
        with self.assertRaisesRegex(ValueError, REGISTERED):
            self.register(record)
        self.assertFalse(self.registry.exists())

    def test_live_window_may_start_at_or_after_actual_registration(self):
        for index, start in enumerate([REGISTERED, '2026-10-17T20:00:00+08:00', '2026-10-18T00:00:00Z']):
            with self.subTest(start=start):
                record = self.live(f'live-{index}')
                record['window']['start'] = start
                frozen = self.register(record)
                self.assertEqual(frozen['registered_at'], REGISTERED)
                self.assertEqual(frozen['validation_version'], 2)

    def test_new_live_numeric_zero_and_one_require_measurement_time(self):
        for value in (0, 1):
            with self.subTest(value=value):
                self.registry = self.directory / f'value-{value}.json'
                self.now.return_value = REGISTER_CLOCK
                self.register(self.live())
                before = self.registry.read_bytes()
                record = self.result(status='supported' if value else 'not_supported')
                record['observed'] = {'value': value, 'event_time': None}
                with self.assertRaisesRegex(ValueError, 'event_time'):
                    self.resolve(record)
                self.assertEqual(self.registry.read_bytes(), before)

    def test_new_live_category_requires_event_time_without_numeric_value(self):
        forecast = self.live()
        forecast['expression'] = {'type': 'direction', 'value': '达到', 'options': ['达到', '未达'], 'basis': '合成分类'}
        forecast['baselines'][0]['expression'] = copy.deepcopy(forecast['expression'])
        forecast['calibration_plan']['metrics'] = ['direction_hit']
        self.register(forecast)
        record = self.result(status='supported')
        record['observed'] = {'value': None, 'category': '达到', 'event_time': None}
        with self.assertRaisesRegex(ValueError, 'event_time'):
            self.resolve(record)
        record['observed']['event_time'] = '2026-10-20T00:00:00Z'
        self.assertEqual(self.resolve(record)['scores']['direction_hit'], 1)

    def test_live_event_must_be_strictly_after_registration(self):
        self.register(self.live())
        before = self.registry.read_bytes()
        for occurred in ('2026-10-17T11:59:59Z', REGISTERED, '2026-10-17T20:00:00+08:00'):
            with self.subTest(occurred=occurred):
                record = self.result()
                record['observed']['event_time'] = occurred
                with self.assertRaises(ValueError):
                    self.resolve(record)
                self.assertEqual(self.registry.read_bytes(), before)
        record['observed']['event_time'] = '2026-10-20T00:00:00Z'
        self.assertEqual(self.resolve(record)['observed']['value'], 0)

    def test_live_all_null_observation_can_remain_undetermined(self):
        self.register(self.live())
        record = self.result(status='undetermined')
        record['observed'] = {'value': None, 'category': None, 'event_time': None}
        saved = self.resolve(record)
        self.assertEqual(saved['status'], 'undetermined')
        self.assertEqual(saved['scores'], {})
        self.assertEqual(saved['baseline_scores'], {})

    def test_non_null_undetermined_observation_still_needs_event_time(self):
        self.register(self.live())
        record = self.result(status='undetermined')
        record['observed']['event_time'] = None
        with self.assertRaisesRegex(ValueError, 'event_time'):
            self.resolve(record)

    def test_non_live_records_keep_historical_windows_and_optional_event_time(self):
        for kind in ('teaching', 'backtest', 'synthetic'):
            with self.subTest(kind=kind):
                self.registry = self.directory / f'{kind}.json'
                self.now.return_value = REGISTER_CLOCK
                record = self.live()
                record['evidence_kind'] = kind
                record['window']['start'] = '2026-10-01T00:00:00Z'
                self.register(record)
                result = self.result()
                result['observed']['event_time'] = None
                saved = self.resolve(result)
                self.assertAlmostEqual(saved['scores']['brier'], 0.64)

    def test_legacy_frozen_live_results_remain_readable_without_rewriting(self):
        for validation_version in (None, 1, 2):
            for scoring_version in (None, 1):
                with self.subTest(validation_version=validation_version, scoring_version=scoring_version):
                    expected = self.frozen_fixture(validation_version=validation_version, scoring_version=scoring_version)
                    before = self.registry.read_bytes()
                    actual = self.tool.load_registry(self.registry)
                    self.assertEqual(actual['forecasts'], expected['forecasts'])
                    self.assertEqual(actual['resolutions'], expected['resolutions'])
                    self.assertEqual(self.registry.read_bytes(), before)

    def test_new_resolution_of_legacy_live_forecast_uses_new_time_rule(self):
        self.frozen_fixture(with_result=False)
        result = self.result()
        result['observed']['event_time'] = None
        with self.assertRaisesRegex(ValueError, 'event_time'):
            self.resolve(result)
        result['observed']['event_time'] = '2026-10-20T00:00:00Z'
        self.assertEqual(self.resolve(result)['scoring_version'], 2)

    def test_stored_version_two_live_window_is_revalidated(self):
        registry = self.frozen_fixture(validation_version=2, with_result=False)
        forecast = registry['forecasts'][0]
        forecast['window']['start'] = '2026-10-01T00:00:00Z'
        forecast['record_sha256'] = self.tool.digest(forecast)
        self.write(self.registry.name, registry)
        with self.assertRaisesRegex(ValueError, REGISTERED):
            self.tool.load_registry(self.registry)

    def test_stored_version_two_resolution_requires_event_time(self):
        self.frozen_fixture(validation_version=2, scoring_version=2)
        with self.assertRaisesRegex(ValueError, 'event_time'):
            self.tool.load_registry(self.registry)


if __name__ == '__main__':
    unittest.main()
