import copy
import json
from pathlib import Path
import tempfile
import unittest

from test_forecast import module,sample,outcome


class ForecastRankTests(unittest.TestCase):
    def setUp(self):
        self.tool=module()
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.registry=self.root/'registry.json'

    def write(self,name,value):
        p=self.root/name;p.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8');return p

    def record(self):
        record=sample()
        record['expression']={'type':'rank','options':['A','B','C'],'value':['A','B','C'],'basis':'合成排序'}
        record['baselines'][0]['expression']=dict(record['expression'],value=['B','A','C'])
        record['calibration_plan']['metrics']=['rank_top_hit']
        return record

    def test_top_choice_is_scored_and_compared_without_probabilities(self):
        self.tool.register_forecast(self.registry,self.write('input.json',self.record()))
        result=outcome();result['observed']['category']='B'
        saved=self.tool.resolve_forecast(self.registry,self.write('outcome.json',result))
        self.assertEqual(saved['scores'],{'rank_top_hit':0})
        self.assertEqual(saved['baseline_scores']['state'],{'rank_top_hit':1})
        group=self.tool.report_registry(self.tool.load_registry(self.registry))['pooled'][0]
        comparison=group['baseline_comparisons'][0]['metrics']['rank_top_hit']
        self.assertEqual((comparison['better'],comparison['worse'],comparison['tied']),(0,1,0))

    def test_rank_options_and_outcome_contract(self):
        for i,mutate in enumerate([
            lambda r:r['expression'].pop('options'),
            lambda r:r['expression'].update(value=['D']),
            lambda r:r['baselines'][0]['expression'].update(options=['A','B']),
        ]):
            record=self.record();mutate(record)
            with self.subTest(index=i),self.assertRaises(ValueError):
                self.tool.register_forecast(self.root/f'bad-{i}.json',self.write('input.json',record))
        self.tool.register_forecast(self.registry,self.write('input.json',self.record()))
        for category,status in [('A','not_supported'),('B','supported'),(None,'not_supported')]:
            result=outcome(status=status);result['observed']['category']=category
            with self.subTest(category=category,status=status),self.assertRaises(ValueError):
                self.tool.resolve_forecast(self.registry,self.write('outcome.json',result))

    def test_rank_without_registered_metric_stays_unscored(self):
        record=self.record();record['calibration_plan']['metrics']=['qualitative_path_match']
        record['expression'].pop('options');record['baselines'][0]['expression'].pop('options')
        self.tool.register_forecast(self.registry,self.write('input.json',record))
        saved=self.tool.resolve_forecast(self.registry,self.write('outcome.json',outcome()))
        self.assertEqual(saved['scores'],{})


if __name__=='__main__':unittest.main()
