import copy
import json
from pathlib import Path
import tempfile
import unittest

from test_forecast import module, outcome, sample


class ForecastStatusRevisionTests(unittest.TestCase):
    def setUp(self):
        self.tool = module()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.registry_path = self.root / 'registry.json'

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
        return path

    def add_forecast(self, identifier):
        record = sample(identifier=identifier)
        record['calibration_plan']['metrics'] = ['brier']
        record['baselines'][0]['type'] = 'recent_state'
        self.tool.register_forecast(self.registry_path, self.write('forecast.json', record))

    def add_outcomes(self, identifier, statuses):
        for index, status in enumerate(statuses, 2):
            record = outcome(identifier, status=status)
            record['resolved_at'] = f'2026-02-{index:02d}T00:00:00Z'
            record['observed']['value'] = 1 if status == 'supported' else 0 if status == 'not_supported' else None
            self.tool.resolve_forecast(self.registry_path, self.write('outcome.json', record))

    def report(self):
        registry = self.tool.load_registry(self.registry_path)
        before = copy.deepcopy(registry)
        result = self.tool.report_registry(registry)
        self.assertEqual(registry, before)
        return result

    def test_undetermined_then_supported_is_reported_as_a_changed_forecast(self):
        self.add_forecast('F1')
        self.add_outcomes('F1', ['undetermined', 'supported'])
        result = self.report()
        self.assertEqual(result['status_revisions'], {
            'count': 1,
            'forecast_ids': ['F1'],
            'state_history': {'F1': [
                {'status': 'undetermined', 'resolved_at': '2026-02-02T00:00:00Z'},
                {'status': 'supported', 'resolved_at': '2026-02-03T00:00:00Z'},
            ]},
        })
        self.assertEqual(result['orders']['1']['statuses']['supported'], 1)
        self.assertEqual(result['orders']['1']['statuses']['undetermined'], 0)

    def test_returning_to_original_state_keeps_intermediate_reversal_visible(self):
        self.add_forecast('F1')
        self.add_outcomes('F1', ['supported', 'not_supported', 'supported'])
        result = self.report()
        revisions = result['status_revisions']
        self.assertEqual(revisions['count'], 1)
        self.assertEqual(revisions['forecast_ids'], ['F1'])
        self.assertEqual([entry['status'] for entry in revisions['state_history']['F1']],
                         ['supported', 'not_supported', 'supported'])
        self.assertEqual([entry['resolved_at'] for entry in revisions['state_history']['F1']],
                         ['2026-02-02T00:00:00Z', '2026-02-03T00:00:00Z', '2026-02-04T00:00:00Z'])
        self.assertEqual(result['orders']['1']['resolution_records'], 3)
        self.assertEqual(result['orders']['1']['resolved'], 1)
        self.assertEqual(result['orders']['1']['statuses']['supported'], 1)
        self.assertEqual(result['orders']['1']['statuses']['not_supported'], 0)
        self.assertEqual(result['by_contract'][0]['metrics']['brier']['n'], 1)
        self.assertAlmostEqual(result['by_contract'][0]['metrics']['brier']['mean'], 0.04)
        self.assertEqual(result['pooled'][0]['metrics']['brier']['n'], 1)
        self.assertAlmostEqual(result['pooled'][0]['metrics']['brier']['mean'], 0.04)

    def test_identical_status_rewrites_are_not_changes(self):
        self.add_forecast('F1')
        self.add_outcomes('F1', ['supported', 'supported', 'supported'])
        result = self.report()
        self.assertEqual(result['status_revisions'], {'count': 0, 'forecast_ids': [], 'state_history': {}})
        self.assertEqual(result['orders']['1']['resolution_records'], 3)
        self.assertEqual(result['orders']['1']['statuses']['supported'], 1)

    def test_transition_history_collapses_repeated_states_only(self):
        self.add_forecast('F1')
        self.add_outcomes('F1', ['undetermined', 'undetermined', 'supported', 'supported'])
        result = self.report()
        self.assertEqual(result['status_revisions']['state_history']['F1'], [
            {'status': 'undetermined', 'resolved_at': '2026-02-02T00:00:00Z'},
            {'status': 'supported', 'resolved_at': '2026-02-04T00:00:00Z'},
        ])
        self.assertEqual(result['orders']['1']['resolution_records'], 4)

    def test_changed_forecasts_are_deduplicated_and_ids_are_stable(self):
        self.add_forecast('Z')
        self.add_forecast('A')
        self.add_forecast('unchanged')
        self.add_forecast('unresolved')
        self.add_outcomes('Z', ['supported', 'not_supported', 'supported'])
        self.add_outcomes('A', ['undetermined', 'supported'])
        self.add_outcomes('unchanged', ['supported', 'supported'])
        result = self.report()
        self.assertEqual(result['status_revisions']['count'], 2)
        self.assertEqual(result['status_revisions']['forecast_ids'], ['A', 'Z'])
        self.assertEqual(list(result['status_revisions']['state_history']), ['A', 'Z'])
        self.assertEqual(result['orders']['1']['unresolved'], 1)

    def test_single_resolution_is_not_a_revision_and_latest_failure_is_scored_once(self):
        self.add_forecast('single')
        self.add_forecast('revised')
        self.add_outcomes('single', ['not_supported'])
        self.add_outcomes('revised', ['supported', 'not_supported'])
        result = self.report()
        self.assertEqual(result['status_revisions']['forecast_ids'], ['revised'])
        self.assertEqual(result['orders']['1']['statuses']['not_supported'], 2)
        self.assertEqual(result['orders']['1']['statuses']['supported'], 0)
        self.assertEqual(result['by_contract'][0]['metrics']['brier']['n'], 2)
        self.assertAlmostEqual(result['by_contract'][0]['metrics']['brier']['mean'], 0.64)
        self.assertAlmostEqual(result['pooled'][0]['metrics']['brier']['mean'], 0.64)

    def test_empty_registry_reports_no_state_changes(self):
        registry = {'format': 'xikari-forecasts-1', 'schema_version': 1, 'forecasts': [], 'resolutions': []}
        before = copy.deepcopy(registry)
        result = self.tool.report_registry(registry)
        self.assertEqual(result['status_revisions'], {'count': 0, 'forecast_ids': [], 'state_history': {}})
        self.assertEqual(registry, before)


if __name__ == '__main__':
    unittest.main()
