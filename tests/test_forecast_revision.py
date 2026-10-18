import copy
import json
from pathlib import Path
import tempfile
import unittest

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


if __name__ == '__main__':
    unittest.main()
