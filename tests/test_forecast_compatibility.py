import copy
import json
import math
from pathlib import Path
import tempfile
import unittest

from test_forecast import module,sample,outcome


class ForecastCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.tool=module();self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.registry=self.root/'registry.json'

    def write(self,name,value):
        p=self.root/name;p.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8');return p

    def freeze(self,record,result=None):
        record['registered_at']='2026-01-01T13:00:00Z';record['record_sha256']=self.tool.digest(record)
        resolutions=[]
        if result is not None:
            result['scores'],result['baseline_scores'],result['scoring_notes']=self.tool.computed_result(result,record)
            result['appended_at']='2026-02-02T01:00:00Z';result['record_sha256']=self.tool.digest(result)
            resolutions.append(result)
        self.write('registry.json',{'format':self.tool.FORMAT,'schema_version':1,'forecasts':[record],'resolutions':resolutions})

    def time_record(self):
        record=sample()
        record['expression']={'type':'time_window','start':'2026-01-02T00:00:00Z','end':'2026-01-06T00:00:00Z','nominal_coverage':0.8,'basis':'合成测试'}
        record['baselines'][0]['expression']=dict(record['expression'])
        record['calibration_plan']['metrics']=['window_coverage','interval_score']
        return record

    def test_all_legacy_expression_new_outcomes_keep_original_scoring(self):
        for kind,value,metrics in [('probability',0.8,['brier','window_coverage']),('none',None,['window_coverage']),
                                   ('direction','A',['direction_hit']),('rank',['A','B'],['rank_top_hit'])]:
            with self.subTest(kind=kind):
                record=sample();record['expression']={'type':kind,'value':value,'basis':'历史记录'}
                if kind in {'rank','direction'}:record['expression']['options']=['A','B']
                record['baselines'][0]['expression']=copy.deepcopy(record['expression'])
                record['calibration_plan']['metrics']=metrics
                self.freeze(record)
                result=outcome();result['observed']['event_time']='2026-01-15T00:00:00Z'
                expected=self.tool.computed_result(result,record)
                saved=self.tool.resolve_forecast(self.registry,self.write('result.json',result))
                self.assertEqual((saved['scores'],saved['baseline_scores'],saved['scoring_notes']),expected)
                self.assertEqual(saved['scoring_version'],1)
                self.assertEqual(saved['validation_version'],2)

    def test_new_time_scores_need_equal_declared_nominal_coverage(self):
        for side in ('model','baseline'):
            record=self.time_record()
            expr=record['expression'] if side=='model' else record['baselines'][0]['expression']
            expr.pop('nominal_coverage')
            with self.subTest(side=side),self.assertRaises(ValueError):self.tool.validate_forecast(record,new=True)
        record=self.time_record();record['baselines'][0]['expression']['nominal_coverage']=0.95
        with self.assertRaises(ValueError):self.tool.validate_forecast(record,new=True)
        record['calibration_plan']['metrics']=['window_coverage']
        record['expression'].pop('nominal_coverage');record['baselines'][0]['expression'].pop('nominal_coverage')
        self.tool.validate_forecast(record,new=True)

    def test_old_different_nominal_time_scores_read_but_do_not_compare(self):
        record=self.time_record();record['validation_version']=2
        record['baselines'][0]['expression']['nominal_coverage']=0.95
        result=outcome();result['scoring_version']=2
        result['observed']={'value':1,'event_time':'2026-01-07T00:00:00Z'}
        self.freeze(record,result)
        before=self.registry.read_bytes();loaded=self.tool.load_registry(self.registry)
        self.assertEqual(self.registry.read_bytes(),before)
        report=self.tool.report_registry(loaded)
        contract=report['by_contract'][0]['baseline_comparisons'][0]
        self.assertNotIn('interval_score',contract['gain'])
        self.assertEqual(contract['incomparable_metrics'],['interval_score'])
        pooled=report['pooled'][0]['baseline_comparisons'][0]
        self.assertNotIn('interval_score',pooled['metrics'])
        self.assertEqual(pooled['incomparable_metrics'],['interval_score'])
        self.assertAlmostEqual(loaded['resolutions'][0]['scores']['interval_score'],14)
        self.assertAlmostEqual(loaded['resolutions'][0]['baseline_scores']['state']['interval_score'],44)


if __name__=='__main__':unittest.main()
