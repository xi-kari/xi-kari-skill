import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timezone

from test_forecast import ROOT, module, sample, outcome


class ForecastRevisionTests(unittest.TestCase):
    def setUp(self):
        self.tool = module()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.registry = self.root / 'registry.json'

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
        return path

    def register(self, value):
        return self.tool.register_forecast(self.registry, self.write('input.json', value))

    def resolve(self, value):
        return self.tool.resolve_forecast(self.registry, self.write('result.json', value))

    def direction(self):
        record = sample()
        record['expression'] = {'type':'direction', 'options':['达到','未达'], 'value':'达到', 'basis':'构造测试'}
        record['baselines'][0]['expression'] = dict(record['expression'], value='未达')
        record['calibration_plan']['metrics'] = ['direction_hit']
        return record

    def test_direction_hit_and_baseline_are_scored(self):
        self.register(self.direction())
        result = outcome()
        result['observed']['category'] = '未达'
        saved = self.resolve(result)
        self.assertEqual(saved['scores']['direction_hit'], 0)
        self.assertEqual(saved['baseline_scores']['state']['direction_hit'], 1)

    def test_direction_contract_and_outcome_consistency(self):
        for index,mutate in enumerate([
            lambda r:r['expression'].pop('options'),
            lambda r:r['expression'].update(options=['达到']),
            lambda r:r['expression'].update(options=['达到','达到']),
            lambda r:r['expression'].update(value='其他'),
            lambda r:r['baselines'][0]['expression'].update(options=['达到','其他']),
            lambda r:r['baselines'][0]['expression'].update(value='其他'),
        ]):
            self.registry=self.root/f'invalid-{index}.json'
            record=self.direction();mutate(record)
            with self.subTest(record=record), self.assertRaises(ValueError):self.register(record)
        self.registry=self.root/'registry.json'
        self.register(self.direction())
        for category,status in [('达到','not_supported'),('未达','supported'),('其他','not_supported'),(None,'not_supported')]:
            result=outcome(status=status);result['observed']['category']=category
            with self.subTest(category=category,status=status),self.assertRaises(ValueError):self.resolve(result)

    def test_unregistered_direction_stays_unscored(self):
        record=self.direction();record['calibration_plan']['metrics']=['qualitative_path_match']
        record['expression'].pop('options');record['baselines'][0]['expression'].pop('options')
        self.register(record)
        self.assertEqual(self.resolve(outcome())['scores'],{})

    def test_teaching_direction_scores_all_three_orders(self):
        expected=[(1,[1,1]),(0,[1,1,0]),(1,[1,1,1])]
        for order,(model,baselines) in enumerate(expected,1):
            case=ROOT/'cases/forecast-public-resignation'
            self.register(json.loads((case/f'order-{order}.json').read_text(encoding='utf-8')))
            saved=self.resolve(json.loads((case/f'outcome-{order}.json').read_text(encoding='utf-8')))
            self.assertEqual(saved['scores']['direction_hit'],model)
            self.assertEqual([x['direction_hit'] for x in saved['baseline_scores'].values()],baselines)

    def test_different_targets_pool_paired_baselines_and_degrade(self):
        for i in range(4):
            record=sample(identifier=f'pool-{i}')
            record['evidence_kind']='backtest'
            record['target']=f'不同目标{i}'
            record['expression']['value']=0.9
            record['baselines'][0].update(id=f'baseline-{i}',type='recent_state')
            record['baselines'][0]['expression']['value']=0.5
            record['calibration_plan']['degradation_policy']={'metric':'brier','minimum_per_period':4,'consecutive_months':1}
            self.register(record);self.resolve(outcome(record['id']))
        report=self.tool.report_registry(self.tool.load_registry(self.registry))
        self.assertEqual(len(report['by_contract']),4)
        self.assertEqual(len(report['pooled']),1)
        comparison=report['pooled'][0]['baseline_comparisons'][0]
        score=comparison['metrics']['brier']
        self.assertEqual(score['n'],4)
        self.assertAlmostEqual(score['model_mean'],0.81)
        self.assertAlmostEqual(score['baseline_mean'],0.25)
        self.assertEqual((score['better'],score['worse'],score['tied']),(0,4,0))
        self.assertEqual(report['pooled'][0]['calibration_bins'][0]['n'],4)
        self.assertEqual(report['capability'],'scenario_only')
        self.assertEqual(report['degradation_decisions'][0]['baseline_type'],'recent_state')

    def test_new_duplicate_baseline_type_rejected_and_unknown_type_excluded(self):
        record=sample();record['baselines'].append(copy.deepcopy(record['baselines'][0]))
        record['baselines'][1]['id']='second'
        with self.assertRaises(ValueError):self.register(record)
        record=sample();record['baselines'][0]['type']='custom_unknown'
        self.register(record);self.resolve(outcome())
        pooled=self.tool.report_registry(self.tool.load_registry(self.registry))['pooled'][0]
        self.assertEqual(pooled['baseline_comparisons'],[])
        self.assertEqual(pooled['excluded_baseline_types'],['custom_unknown'])

    def test_time_window_registry_distinguishes_interval_lengths(self):
        record=sample()
        record['window']={'start':'2026-10-01T00:00:00Z','end':'2026-12-31T00:00:00Z'}
        record['expression']={'type':'time_window','start':'2026-11-01T00:00:00Z','end':'2026-11-15T00:00:00Z','basis':'构造测试'}
        record['baselines'][0]['expression']=dict(record['expression'],**record['window'])
        record['calibration_plan']['metrics']=['window_coverage']
        result=outcome(status='supported');result['resolved_at']='2027-01-01T00:00:00Z'
        result['observed']={'value':1,'event_time':'2026-11-05T00:00:00Z'}
        with mock.patch.object(self.tool,'utcnow',return_value=datetime(2027,1,2,tzinfo=timezone.utc)):
            self.register(record);saved=self.resolve(result)
            self.assertEqual(saved['scores'],{'window_length_days':14,'window_coverage':1})
            self.assertEqual(saved['baseline_scores']['state'],{'window_length_days':91,'window_coverage':1})
            self.tool.load_registry(self.registry)

    def test_frozen_v1_window_scores_still_load(self):
        forecast=self.register(sample())
        forecast.pop('validation_version')
        forecast['record_sha256']=self.tool.digest(forecast)
        result=outcome();result['observed']['event_time']='2026-01-15T00:00:00Z'
        result['scores'],result['baseline_scores'],result['scoring_notes']=self.tool.computed_result(result,forecast)
        result['appended_at']=self.tool.timestamp();result['record_sha256']=self.tool.digest(result)
        registry={'format':self.tool.FORMAT,'schema_version':1,'forecasts':[forecast],'resolutions':[result]}
        self.write('registry.json',registry)
        before=self.registry.read_bytes()
        loaded=self.tool.load_registry(self.registry)
        self.assertEqual(loaded['resolutions'][0]['scores']['window_coverage'],1)
        self.assertEqual(self.registry.read_bytes(),before)


if __name__ == '__main__':
    unittest.main()
