import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

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

    def material_catalog(self, root):
        source = root / 'source.txt'
        raw = '访谈中的虚构观察。\n'.encode('utf-8')
        source.write_bytes(raw)
        digest = hashlib.sha256(raw).hexdigest()
        return {
            'format': 'xikari-materials-1',
            'sources': {'interview-1': {'id': 'interview-1', 'path': str(source), 'sha256': digest,
                                        'kind': 'txt', 'title': '虚构访谈', 'extraction': 'evidence.py/2'}},
            'clips': {'appeal-observation': {'id': 'appeal-observation', 'source_id': 'interview-1',
                       'source_sha256': digest, 'source_extracts': [{'locator': 'L1', 'text': '访谈中的虚构观察。', 'location': {'line': 1}}],
                       'support_boundary': '只支持本条虚构观察'}},
        }

    def referencing_ledger(self, catalog):
        return {'schema_version': 1, 'claims': [{**MINIMAL, 'status': 'supported',
                'evidence': [{'catalog': str(catalog), 'clip': 'appeal-observation', 'direction': 'supports'}]}]}

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
            self.write(catalog, self.material_catalog(root))
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
            self.assertFalse(any('材料目录无法读取' in error for error in report['errors']))

    def test_check_rejects_invalid_clip_and_source_structures_without_writes(self):
        target = module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / 'materials.json'
            valid = self.material_catalog(root)
            source = root / 'source.txt'
            mutations = [
                ('null clip', ('clips', 'appeal-observation'), None),
                ('string clip', ('clips', 'appeal-observation'), 'not a clip'),
                ('list clip', ('clips', 'appeal-observation'), []),
                ('mismatched clip id', ('clips', 'appeal-observation', 'id'), 'different'),
                ('unknown source', ('clips', 'appeal-observation', 'source_id'), 'absent'),
                ('null source id', ('clips', 'appeal-observation', 'source_id'), None),
                ('list source id', ('clips', 'appeal-observation', 'source_id'), []),
                ('object source id', ('clips', 'appeal-observation', 'source_id'), {}),
                ('null extracts', ('clips', 'appeal-observation', 'source_extracts'), None),
                ('string extracts', ('clips', 'appeal-observation', 'source_extracts'), 'not excerpts'),
                ('object extracts', ('clips', 'appeal-observation', 'source_extracts'), {}),
                ('missing linked source', ('sources',), {}),
                ('null sources', ('sources',), None),
                ('list sources', ('sources',), []),
                ('null source record', ('sources', 'interview-1'), None),
                ('mismatched source id', ('sources', 'interview-1', 'id'), 'different'),
                ('invalid source path', ('sources', 'interview-1', 'path'), None),
                ('invalid source hash', ('sources', 'interview-1', 'sha256'), None),
                ('invalid source kind', ('sources', 'interview-1', 'kind'), 1),
                ('invalid source title', ('sources', 'interview-1', 'title'), []),
                ('source aliases catalog', ('sources', 'interview-1', 'path'), str(catalog)),
            ]
            for name, keys, value in mutations:
                with self.subTest(name=name):
                    payload = copy.deepcopy(valid)
                    destination = payload
                    for key in keys[:-1]:
                        destination = destination[key]
                    destination[keys[-1]] = value
                    self.write(catalog, payload)
                    ledger = self.referencing_ledger(catalog)
                    ledger_before = copy.deepcopy(ledger)
                    before = (catalog.read_bytes(), source.read_bytes())
                    report = target.check_ledger(ledger, set())
                    self.assertEqual((catalog.read_bytes(), source.read_bytes()), before)
                    self.assertEqual(ledger, ledger_before)
                    self.assertFalse(report['ok'])
                    self.assertTrue(any(str(catalog) in error and '材料目录无法读取' in error for error in report['errors']))

    def test_check_warns_when_a_valid_clip_has_no_support_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = self.material_catalog(root)
            payload['clips']['appeal-observation'].pop('support_boundary')
            catalog = self.write(root / 'materials.json', payload)
            before = catalog.read_bytes()
            report = module().check_ledger(self.referencing_ledger(catalog), set())
            self.assertTrue(report['ok'])
            self.assertEqual(report['errors'], [])
            self.assertTrue(any('support_boundary' in warning for warning in report['warnings']))
            self.assertEqual(catalog.read_bytes(), before)

    def test_check_resolves_saved_snapshots_without_reading_current_source(self):
        target = module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / 'materials.json'
            source = root / 'source.txt'
            original_open = Path.open

            def protect_source(path, *args, **kwargs):
                if path.resolve() == source.resolve():
                    raise AssertionError('Checking a saved clip must not open its original source')
                return original_open(path, *args, **kwargs)

            for state in ('unchanged', 'changed', 'missing'):
                for extraction in ('evidence.py/2', 'evidence.py/1', None):
                    with self.subTest(state=state, extraction=extraction):
                        payload = self.material_catalog(root)
                        if extraction is None:
                            payload['sources']['interview-1'].pop('extraction')
                        else:
                            payload['sources']['interview-1']['extraction'] = extraction
                        self.write(catalog, payload)
                        if state == 'changed':
                            source.write_bytes(b'changed source\r\n')
                        elif state == 'missing':
                            source.unlink()
                        before = catalog.read_bytes()
                        source_before = source.read_bytes() if source.exists() else None
                        with mock.patch.object(Path, 'open', protect_source):
                            report = target.check_ledger(self.referencing_ledger(catalog), set())
                        self.assertTrue(report['ok'])
                        self.assertEqual(report['errors'], [])
                        self.assertEqual(report['warnings'], [])
                        self.assertEqual(catalog.read_bytes(), before)
                        self.assertEqual(source.read_bytes() if source.exists() else None, source_before)

    def test_cli_checks_real_evidence_catalog_from_a_foreign_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            foreign = root / 'elsewhere'
            foreign.mkdir()
            source = root / 'source.txt'
            source.write_bytes('仅用于结构测试的片段。\n'.encode('utf-8'))
            catalog, ledger, record = root / 'materials.json', root / 'claims.json', root / 'claim.json'

            def run(script, *arguments):
                return subprocess.run([sys.executable, str(ROOT / 'scripts' / script), *map(str, arguments)],
                                      cwd=foreign, capture_output=True, encoding='utf-8')

            for arguments in [
                ('add', source, '--id', 'interview-1'),
                ('clip', '--id', 'interview-1', '--clip-id', 'appeal-observation', '--at', 'L1', '--support', 'Synthetic snapshot'),
            ]:
                result = run('evidence.py', '--catalog', catalog, *arguments)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.write(record, self.referencing_ledger(catalog)['claims'][0])
            added = run('claims.py', '--ledger', ledger, 'add', '--record', record)
            self.assertEqual(added.returncode, 0, added.stderr)
            valid = json.loads(catalog.read_text(encoding='utf-8'))
            for name, malformed_source_id in (('valid', None), ('valid BOM', None), ('null clip', None), ('null clip BOM', None), ('list source id', []), ('object source id', {}), ('old snapshot without source', None)):
                with self.subTest(name=name):
                    payload = copy.deepcopy(valid)
                    if name in ('null clip', 'null clip BOM'):
                        payload['clips']['appeal-observation'] = None
                    elif name in ('list source id', 'object source id'):
                        payload['clips']['appeal-observation']['source_id'] = malformed_source_id
                    elif name == 'old snapshot without source':
                        payload['sources']['interview-1']['extraction'] = 'evidence.py/1'
                        source.unlink()
                    self.write(catalog, payload)
                    if name.endswith('BOM'):
                        catalog.write_bytes(b'\xef\xbb\xbf' + catalog.read_bytes())
                    watched = (catalog, ledger, record, source)
                    before = {path: path.read_bytes() if path.exists() else None for path in watched}
                    result = run('claims.py', '--ledger', ledger, 'check')
                    self.assertEqual({path: path.read_bytes() if path.exists() else None for path in watched}, before)
                    expected_ok = name in ('valid', 'valid BOM', 'old snapshot without source')
                    self.assertEqual(result.returncode, 0 if expected_ok else 1, result.stderr or result.stdout)
                    self.assertEqual(result.stderr, '')
                    report = json.loads(result.stdout)
                    self.assertEqual(report['ok'], expected_ok)
                    if not expected_ok:
                        self.assertTrue(any('材料目录无法读取' in error for error in report['errors']))

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

    def test_forward_reference_can_replace_inline_registration(self):
        module().validate_claim({**MINIMAL, 'kind': 'forward',
                                 'forecast_ref': {'registry': 'C:/task/forecasts.json', 'id': 'forecast-1'}})

    def test_forecast_reference_is_only_for_forward_and_is_well_formed(self):
        for reference in [None, {}, {'id': 'x'}, {'registry': 'x', 'id': '../x'}]:
            with self.subTest(reference=reference), self.assertRaises(ValueError):
                module().validate_claim({**MINIMAL, 'kind': 'forward', 'forecast_ref': reference})
        with self.assertRaises(ValueError):
            module().validate_claim({**MINIMAL, 'forecast_ref': {'registry': 'x', 'id': 'forecast-1'}})

    def test_check_reports_missing_forecast_registry(self):
        record = {**MINIMAL, 'kind': 'forward', 'forecast_ref': {'registry': 'missing/forecasts.json', 'id': 'forecast-1'}}
        result = module().check_ledger({'claims': [record]}, set())
        self.assertFalse(result['ok'])
        self.assertTrue(any('forecast-1' in error for error in result['errors']))

    def test_forecast_link_resolves_and_supported_requires_actual_result(self):
        from test_forecast import module as forecast_module, sample, outcome
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root / 'forecasts.json'
            forecast_module().register_forecast(registry, self.write(root / 'forecast.json', sample()))
            record = {**MINIMAL, 'kind': 'forward', 'forecast_ref': {'registry': str(registry), 'id': 'forecast-1'}}
            saved = module().add_claim(root / 'claims.json', self.write(root / 'claim.json', record))
            self.assertEqual(saved['forecast_ref']['id'], 'forecast-1')
            self.assertTrue(module().check_ledger({'claims': [record]}, set())['ok'])
            supported = {**record, 'id': 'supported', 'status': 'supported', 'theory': [{'section': '12.2'}]}
            with self.assertRaises(ValueError):
                module().add_claim(root / 'claims.json', self.write(root / 'claim.json', supported))
            result = outcome(status='supported')
            result['observed']['value'] = 1
            forecast_module().resolve_forecast(registry, self.write(root / 'outcome.json', result))
            module().add_claim(root / 'claims.json', self.write(root / 'claim.json', supported))

    def test_forward_link_to_unknown_id_refused_without_ledger_write(self):
        from test_forecast import module as forecast_module, sample
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root / 'forecasts.json'
            forecast_module().register_forecast(registry, self.write(root / 'forecast.json', sample()))
            record = {**MINIMAL, 'kind': 'forward', 'forecast_ref': {'registry': str(registry), 'id': 'absent'}}
            with self.assertRaises(ValueError):
                module().add_claim(root / 'claims.json', self.write(root / 'claim.json', record))
            self.assertFalse((root / 'claims.json').exists())

    def test_json_duplicates_and_nonfinite_values_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / 'claim.json'
            for payload in ['{"id":"a","id":"b"}', '{"weight":NaN}', '{"weight":1e400}']:
                record.write_text(payload, encoding='utf-8')
                with self.subTest(payload=payload), self.assertRaises(ValueError):
                    module().read_json(record)

    def test_collection_fields_must_be_lists(self):
        for field in ['evidence', 'theory', 'counterclaims']:
            for value in [None, {}, '']:
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    module().validate_claim({**MINIMAL, field: value})

    def test_ledger_schema_version_is_not_boolean(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(Path(directory) / 'claims.json', {'schema_version': True, 'claims': []})
            with self.assertRaises(ValueError):
                module().load_ledger(path)

    def test_forecast_reference_report_identifies_teaching_without_promoting_it(self):
        from test_forecast import module as forecast_module, sample, outcome
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root / 'forecasts.json'
            record = sample()
            record['evidence_kind'] = 'teaching'
            forecast_module().register_forecast(registry, self.write(root / 'forecast.json', record))
            forecast_module().resolve_forecast(registry, self.write(root / 'outcome.json', outcome(status='supported')))
            claim = {**MINIMAL, 'kind': 'forward', 'status': 'supported', 'theory': [{'section': '12.2'}],
                     'forecast_ref': {'registry': str(registry), 'id': record['id']}}
            checked = module().check_ledger({'claims': [claim]}, {'12.2'})
            self.assertTrue(checked['ok'])
            self.assertEqual(checked['forecast_references'][0]['evidence_kind'], 'teaching')
            self.assertFalse(checked['forecast_references'][0]['empirical_support'])


if __name__ == '__main__':
    unittest.main()
