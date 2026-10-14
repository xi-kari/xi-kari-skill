import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

MINIMAL = {'id': 'claim-1', 'statement': '容量不足会阻断新增任务', 'kind': 'mechanism', 'status': 'proposed'}


def module():
    spec = importlib.util.spec_from_file_location('claims', ROOT / 'scripts' / 'claims.py')
    target = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(target)
    return target


class ClaimLedgerTests(unittest.TestCase):
    def write(self, path, payload):
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
        return path

    def test_minimal_claim_is_appended_and_the_record_is_left_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, record = root / 'ledger.json', root / 'claim.json'
            self.write(record, MINIMAL)
            original = record.read_bytes()
            saved = module().add_claim(ledger, record)
            self.assertEqual(saved['id'], 'claim-1')
            self.assertEqual(record.read_bytes(), original)
            self.assertEqual([case['id'] for case in module().load_ledger(ledger)['claims']], ['claim-1'])

    def test_duplicate_and_unknown_supersedes_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, record = root / 'ledger.json', root / 'claim.json'
            self.write(record, MINIMAL)
            module().add_claim(ledger, record)
            before = ledger.read_bytes()
            with self.assertRaises(ValueError):
                module().add_claim(ledger, record)
            self.assertEqual(ledger.read_bytes(), before)
            self.write(record, {**MINIMAL, 'id': 'claim-2', 'supersedes': 'not-there'})
            with self.assertRaises(ValueError):
                module().add_claim(ledger, record)

    def test_invalid_claims_are_refused_on_specific_grounds(self):
        validate = module().validate_claim
        with self.assertRaises(ValueError):
            validate({'id': 'a', 'kind': 'fact', 'status': 'proposed'})
        with self.assertRaises(ValueError):
            validate({**MINIMAL, 'kind': 'hunch'})
        with self.assertRaises(ValueError):
            validate({**MINIMAL, 'status': 'certain'})
        with self.assertRaises(ValueError):
            validate({**MINIMAL, 'status': 'supported'})
        with self.assertRaises(ValueError):
            validate({**MINIMAL, 'kind': 'forward'})
        with self.assertRaises(ValueError):
            validate({**MINIMAL, 'load_bearing': True})
        with self.assertRaises(ValueError):
            validate({**MINIMAL, 'evidence': [{'clip': 'x'}]})

    def test_a_fully_declared_load_bearing_forecast_is_accepted(self):
        module().validate_claim({
            'id': 'claim-3', 'statement': '缺员在多轮之后仍会复发', 'kind': 'forward', 'status': 'contested',
            'registration': {'window': '两轮排程', 'baseline': '当前两名复核者', 'criteria': '第三轮仍出现积压'},
            'load_bearing': True, 'change_conditions': ['出现第三名复核者'],
            'counterclaims': [{'statement': '积压只是入口记录改变', 'strength': '可检验'}],
            'theory': [{'section': '12.1'}], 'reasons': ['时延与增益不匹配'],
        })

    def test_check_resolves_theory_sections_and_evidence_clips_from_disk(self):
        target = module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / 'materials.json'
            catalog.write_text(json.dumps({
                'format': 'xikari-materials-1',
                'sources': {},
                'clips': {'appeal-observation': {'id': 'appeal-observation', 'source_id': 'interview-1'}},
            }, ensure_ascii=False), encoding='utf-8')
            ledger = {'schema_version': 1, 'claims': [
                {**MINIMAL, 'theory': [{'section': '4.17'}],
                 'evidence': [{'catalog': str(catalog), 'clip': 'appeal-observation', 'direction': 'supports'}]},
                {**MINIMAL, 'id': 'claim-9', 'theory': [{'section': '99.999'}],
                 'evidence': [{'catalog': str(catalog), 'clip': 'absent', 'direction': 'supports'}]},
            ]}
            report = target.check_ledger(ledger, {'4.17', '12.1'})
            self.assertFalse(report['ok'])
            self.assertEqual(report['claims'], 2)
            self.assertTrue(any('99.999' in error for error in report['errors']))
            self.assertTrue(any('absent' in error for error in report['errors']))

    def test_check_reports_a_missing_catalog_instead_of_assuming_evidence(self):
        target = module()
        ledger = {'schema_version': 1, 'claims': [
            {**MINIMAL, 'evidence': [{'catalog': 'nowhere/materials.json', 'clip': 'x', 'direction': 'supports'}]},
        ]}
        report = target.check_ledger(ledger, set())
        self.assertFalse(report['ok'])
        self.assertTrue(any('nowhere' in text for text in report['errors']))

    def test_save_refuses_to_replace_a_changed_ledger_and_a_foreign_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ledger.json'
            current = b'{"schema_version":1,"claims":[]}'
            path.write_bytes(current)
            with self.assertRaises(ValueError):
                module().save_ledger(path, {'schema_version': 1, 'claims': []}, b'old')
            self.assertEqual(path.read_bytes(), current)
            lock = path.with_name(path.name + '.lock')
            lock.write_bytes(b'another writer owns this')
            with self.assertRaises(ValueError):
                module().save_ledger(path, {'schema_version': 1, 'claims': []}, current)
            self.assertEqual(path.read_bytes(), current)
            self.assertEqual(lock.read_bytes(), b'another writer owns this')


if __name__ == '__main__':
    unittest.main()
