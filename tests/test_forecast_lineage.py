import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_forecast import ROOT, module, outcome, sample


class ForecastLineageTests(unittest.TestCase):
    def setUp(self):
        self.tool = module()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.registry = self.directory / 'forecasts.json'
        clock = mock.patch.object(self.tool, 'utcnow', return_value=datetime(2026, 3, 2, tzinfo=timezone.utc))
        clock.start()
        self.addCleanup(clock.stop)

    def write(self, name, value):
        path = self.directory / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
        return path

    def record(self, order, identifier, parent=None):
        record = sample(order, identifier)
        record['calibration_plan']['metrics'] = ['brier']
        if order > 1:
            for kind in ('direct_long_term', 'shallower_continuation'):
                record['baselines'].append({'id': kind, 'type': kind, 'expression': copy.deepcopy(record['expression'])})
        if parent is not None:
            record['parent'] = parent
        return record

    def register(self, record):
        return self.tool.register_forecast(self.registry, self.write('registration.json', record))

    def resolve(self, identifier, *, paths=(), status='not_supported', resolved_at='2026-02-02T00:00:00Z'):
        record = outcome(identifier, status)
        record['path_match'] = list(paths)
        record['resolved_at'] = resolved_at
        if status not in {'supported', 'not_supported'}:
            record['observed']['value'] = None
        return self.tool.resolve_forecast(self.registry, self.write('resolution.json', record))

    def fixture(self, records):
        records = copy.deepcopy(records)
        for record in records:
            record['registered_at'] = '2026-03-01T00:00:00Z'
            record['record_sha256'] = self.tool.digest(record)
        registry = {'format': self.tool.FORMAT, 'schema_version': 1, 'forecasts': records, 'resolutions': []}
        self.write(self.registry.name, registry)
        return registry

    def test_second_and_third_orders_register_against_existing_parent_paths(self):
        first = self.register(self.record(1, 'first'))
        second = self.register(self.record(2, 'second', {'forecast_id': 'first', 'path_id': 'path-1'}))
        third = self.register(self.record(3, 'third', {'forecast_id': 'second', 'path_id': 'path-1'}))
        self.assertEqual(second['parent']['forecast_id'], first['id'])
        self.assertEqual(third['parent']['forecast_id'], second['id'])
        self.assertIsNone(second['paths'][0]['parent'])
        self.assertEqual(len(self.tool.load_registry(self.registry)['forecasts']), 3)

    def test_new_recursive_orders_require_parent_and_validate_its_shape(self):
        for order in (2, 3):
            with self.subTest(order=order), self.assertRaisesRegex(ValueError, 'parent'):
                self.register(self.record(order, f'order-{order}'))
        for parent in (None, {}, [], 'first', {'forecast_id': 'first'},
                       {'forecast_id': 'first', 'path_id': 'path-1', 'extra': True},
                       {'forecast_id': '', 'path_id': 'path-1'}, {'forecast_id': 'first', 'path_id': ''}):
            with self.subTest(parent=parent), self.assertRaisesRegex(ValueError, 'parent'):
                record = self.record(2, 'second')
                record['parent'] = parent
                self.register(record)

    def test_parent_forecast_and_path_must_exist(self):
        self.register(self.record(1, 'first'))
        for parent, error in (({'forecast_id': 'absent', 'path_id': 'path-1'}, 'parent.forecast_id'),
                              ({'forecast_id': 'first', 'path_id': 'absent'}, 'parent.path_id')):
            before = self.registry.read_bytes()
            with self.subTest(parent=parent), self.assertRaisesRegex(ValueError, error):
                self.register(self.record(2, 'second', parent))
            self.assertEqual(self.registry.read_bytes(), before)

    def test_parent_must_be_exactly_one_order_lower(self):
        self.register(self.record(1, 'first'))
        with self.assertRaisesRegex(ValueError, '阶次'):
            self.register(self.record(3, 'third', {'forecast_id': 'first', 'path_id': 'path-1'}))
        with self.assertRaisesRegex(ValueError, '阶次'):
            self.register(self.record(1, 'another-first', {'forecast_id': 'first', 'path_id': 'path-1'}))

    def test_parent_theory_and_input_cutoff_are_compatible(self):
        parent = self.record(1, 'first')
        parent['theory_sha256'] = '0' * 64
        self.fixture([parent])
        with self.assertRaisesRegex(ValueError, 'theory_sha256'):
            self.register(self.record(2, 'second', {'forecast_id': 'first', 'path_id': 'path-1'}))
        self.fixture([self.record(1, 'first')])
        child = self.record(2, 'second', {'forecast_id': 'first', 'path_id': 'path-1'})
        child['input_cutoff'] = '2025-12-31T12:00:00Z'
        with self.assertRaisesRegex(ValueError, 'input_cutoff'):
            self.register(child)
        child['input_cutoff'] = '2026-01-01T00:00:00Z'
        self.register(child)

    def test_record_parent_does_not_replace_local_path_dag(self):
        self.register(self.record(1, 'first'))
        child = self.record(2, 'second', {'forecast_id': 'first', 'path_id': 'path-1'})
        child['paths'][0]['id'] = 'child-root'
        child['paths'].append({**copy.deepcopy(child['paths'][0]), 'id': 'child-next', 'parent': 'child-root'})
        self.register(child)
        child['id'] = 'invalid-child'
        child['paths'][0]['parent'] = 'path-1'
        with self.assertRaisesRegex(ValueError, '本记录父路径'):
            self.register(child)

    def test_legacy_records_without_parent_remain_readable(self):
        records = [self.record(2, 'legacy-second'), self.record(3, 'legacy-third')]
        expected = self.fixture(records)
        before = self.registry.read_bytes()
        actual = self.tool.load_registry(self.registry)
        self.assertEqual(actual['forecasts'], expected['forecasts'])
        self.assertEqual(self.registry.read_bytes(), before)
        for record in records:
            record['validation_version'] = 2
            self.fixture([record])
            with self.subTest(order=record['order']), self.assertRaisesRegex(ValueError, 'parent'):
                self.tool.load_registry(self.registry)

    def test_parent_references_are_checked_in_legacy_and_new_frozen_records(self):
        for version in (None, 1, 2):
            first = self.record(1, 'first')
            second = self.record(2, 'second', {'forecast_id': 'first', 'path_id': 'path-1'})
            if version is not None:
                second['validation_version'] = version
            self.fixture([first, second])
            with self.subTest(version=version):
                self.assertEqual(len(self.tool.load_registry(self.registry)['forecasts']), 2)
                for mutate, error in ((lambda row: row['parent'].update(forecast_id='absent'), 'parent.forecast_id'),
                                      (lambda row: row['parent'].update(path_id='absent'), 'parent.path_id'),
                                      (lambda row: row.update(theory_sha256='0' * 64), 'theory_sha256'),
                                      (lambda row: row.update(input_cutoff='2025-12-31T12:00:00Z'), 'input_cutoff'),
                                      (lambda row: row.update(order=3, paths=[dict(row['paths'][0], order=3)]), '阶次')):
                    changed = copy.deepcopy(second)
                    mutate(changed)
                    self.fixture([first, changed])
                    with self.assertRaisesRegex(ValueError, error):
                        self.tool.load_registry(self.registry)

    def test_frozen_parent_must_precede_child_in_registry(self):
        first = self.record(1, 'first')
        second = self.record(2, 'second', {'forecast_id': 'first', 'path_id': 'path-1'})
        self.fixture([second, first])
        with self.assertRaisesRegex(ValueError, 'parent.forecast_id'):
            self.tool.load_registry(self.registry)

    def test_report_splits_parent_path_matches_without_changing_main_pool(self):
        first = self.record(1, 'first')
        first['paths'].append({**copy.deepcopy(first['paths'][0]), 'id': 'other-path'})
        self.register(first)
        for identifier, path in (('matching', 'path-1'), ('not-matching', 'other-path')):
            self.register(self.record(2, identifier, {'forecast_id': 'first', 'path_id': path}))
            self.resolve(identifier)
        before = self.tool.report_registry(self.tool.load_registry(self.registry))
        self.assertEqual(before['pooled_by_parent_match'][0]['parent_match'], 'unresolved')
        self.resolve('first', paths=['path-1'])
        report = self.tool.report_registry(self.tool.load_registry(self.registry))
        split = {group['parent_match']: group for group in report['pooled_by_parent_match']}
        self.assertEqual(set(split), {'matched', 'not_matched'})
        self.assertEqual(split['matched']['forecast_ids'], ['matching'])
        self.assertEqual(split['not_matched']['forecast_ids'], ['not-matching'])
        for group in split.values():
            self.assertEqual(group['resolved'], 1)
            self.assertAlmostEqual(group['metrics']['brier']['mean'], 0.64)
            self.assertNotIn('_pairs', group)
        main = [group for group in report['pooled'] if group['order'] == 2]
        self.assertEqual(len(main), 1)
        self.assertEqual(main[0]['resolved'], 2)
        self.assertEqual(main, [group for group in before['pooled'] if group['order'] == 2])

    def test_report_uses_latest_parent_resolution_and_preserves_child_scores(self):
        self.register(self.record(1, 'first'))
        self.register(self.record(2, 'second', {'forecast_id': 'first', 'path_id': 'path-1'}))
        saved = self.resolve('second')
        self.resolve('first', paths=['path-1'])
        self.assertEqual(self.tool.report_registry(self.tool.load_registry(self.registry))['pooled_by_parent_match'][0]['parent_match'], 'matched')
        self.resolve('first', paths=[], resolved_at='2026-02-03T00:00:00Z')
        registry = self.tool.load_registry(self.registry)
        self.assertEqual(self.tool.report_registry(registry)['pooled_by_parent_match'][0]['parent_match'], 'not_matched')
        self.assertEqual(next(row for row in registry['resolutions'] if row['forecast_id'] == 'second'), saved)
        for day, status in enumerate(('undetermined', 'target_invalid', 'not_evaluable'), 4):
            with self.subTest(status=status):
                self.resolve('first', paths=['path-1'], status=status, resolved_at=f'2026-02-{day:02d}T00:00:00Z')
                self.assertEqual(self.tool.report_registry(self.tool.load_registry(self.registry))['pooled_by_parent_match'][0]['parent_match'], 'unresolved')

    def test_report_preserves_unknown_legacy_lineage_as_separate_group(self):
        self.fixture([self.record(2, 'legacy-second'), self.record(3, 'legacy-third')])
        self.resolve('legacy-second')
        self.resolve('legacy-third')
        groups = self.tool.report_registry(self.tool.load_registry(self.registry))['pooled_by_parent_match']
        self.assertEqual({group['order'] for group in groups}, {2, 3})
        self.assertTrue(all(group['parent_match'] == 'unknown_legacy' for group in groups))

    def test_teaching_case_records_choose_explicit_parent_branches(self):
        case = ROOT / 'cases/forecast-public-resignation'
        records = [json.loads((case / f'order-{order}.json').read_text(encoding='utf-8-sig')) for order in (1, 2, 3)]
        self.assertEqual(records[1]['parent'], {'forecast_id': 'TEACH-RESIGN-O1', 'path_id': 'P1-load'})
        self.assertEqual(records[2]['parent'], {'forecast_id': 'TEACH-RESIGN-O2', 'path_id': 'P2-exits-alternative'})
        for order, record in enumerate(records, 1):
            self.register(record)
            self.tool.resolve_forecast(self.registry, case / f'outcome-{order}.json')
        report = self.tool.report_registry(self.tool.load_registry(self.registry))
        self.assertEqual({group['order']: group['parent_match'] for group in report['pooled_by_parent_match']}, {2: 'matched', 3: 'matched'})
        self.assertEqual(report['capability'], 'unverified')
        self.assertEqual(report['capability_evidence_records'], 0)


if __name__ == '__main__':
    unittest.main()
