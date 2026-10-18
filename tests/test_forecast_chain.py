import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def module():
    spec = importlib.util.spec_from_file_location('forecast_chain', ROOT / 'scripts' / 'forecast_chain.py')
    target = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(target)
    return target


def frozen(record):
    data = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return {**record, 'record_sha256': hashlib.sha256(data.encode('utf-8')).hexdigest()}


def legacy():
    return {
        'format': 'xikari-forecasts-1', 'schema_version': 1,
        'forecasts': [frozen({'id': 'F1', 'target': '甲'}), frozen({'id': 'F2', 'target': '乙'})],
        'resolutions': [frozen({'forecast_id': 'F1', 'resolved_at': '2026-01-03T00:00:00Z', 'status': 'not_supported'})],
    }


class ForecastChainTests(unittest.TestCase):
    def setUp(self):
        self.target = module()

    def test_upgrade_preserves_frozen_records_and_marks_legacy_array_order(self):
        registry = legacy()
        before = copy.deepcopy(registry)
        forecast_array = registry['forecasts']
        resolution_array = registry['resolutions']
        self.assertIsNone(self.target.upgrade(registry))
        self.assertEqual(registry['schema_version'], 2)
        self.assertEqual(registry['legacy_prefix'], 3)
        self.assertIs(registry['forecasts'], forecast_array)
        self.assertIs(registry['resolutions'], resolution_array)
        self.assertEqual(registry['forecasts'], before['forecasts'])
        self.assertEqual(registry['resolutions'], before['resolutions'])
        self.assertEqual([(x['seq'], x['kind'], x['id']) for x in registry['chain']], [
            (1, 'forecast', 'F1'), (2, 'forecast', 'F2'),
            (3, 'resolution', 'F1@2026-01-03T00:00:00Z'),
        ])
        self.assertEqual(set(registry['chain'][0]), {'seq', 'kind', 'id', 'record_sha256', 'prev'})
        self.assertIsNone(registry['chain'][0]['prev'])
        self.assertEqual(self.target.chain_head(registry), self.target.validate(registry))
        migrated = copy.deepcopy(registry)
        self.target.upgrade(registry)
        self.assertEqual(registry, migrated)

    def test_record_and_chain_deletions_or_reordering_are_detected(self):
        original = legacy()
        original['resolutions'].append(frozen({
            'forecast_id': 'F2', 'resolved_at': '2026-01-04T00:00:00Z', 'status': 'supported',
        }))
        self.target.upgrade(original)
        changes = {
            'record_without_chain': lambda r: r['forecasts'].pop(1),
            'chain_without_record': lambda r: r['chain'].pop(1),
            'middle_record_and_entry': lambda r: (r['forecasts'].pop(1), r['chain'].pop(1)),
            'forecast_array_order': lambda r: r['forecasts'].reverse(),
            'resolution_array_order': lambda r: r['resolutions'].reverse(),
            'record_payload': lambda r: r['forecasts'][0].update(target='changed'),
            'record_digest': lambda r: r['forecasts'][0].update(record_sha256='0' * 64),
        }
        for label, change in changes.items():
            with self.subTest(label=label):
                registry = copy.deepcopy(original)
                change(registry)
                with self.assertRaises(self.target.ChainError):
                    self.target.validate(registry)

    def test_append_records_real_interleaving_without_rewriting_legacy_prefix(self):
        registry = legacy()
        self.target.upgrade(registry)
        before = copy.deepcopy(registry)
        additional = [
            ('forecast', frozen({'id': 'F3', 'target': '丙'})),
            ('resolution', frozen({'forecast_id': 'F3', 'resolved_at': '2026-01-05T00:00:00Z', 'status': 'supported'})),
            ('forecast', frozen({'id': 'F4', 'target': '丁'})),
        ]
        for kind, record in additional:
            array = 'forecasts' if kind == 'forecast' else 'resolutions'
            previous = self.target.chain_head(registry)
            registry[array].append(record)
            head = self.target.append_entry(registry, kind, record)
            self.assertEqual(registry['chain'][-1]['prev'], previous)
            self.assertEqual(head, self.target.validate(registry, expect_head=head))
            self.assertIs(registry[array][-1], record)
        self.assertEqual([x['kind'] for x in registry['chain'][3:]], ['forecast', 'resolution', 'forecast'])
        self.assertEqual(registry['chain'][:3], before['chain'])
        self.assertEqual(registry['legacy_prefix'], 3)

    def test_external_head_detects_self_consistent_tail_deletion(self):
        registry = legacy()
        self.target.upgrade(registry)
        old_head = self.target.chain_head(registry)
        record = frozen({'id': 'F3', 'target': 'later'})
        registry['forecasts'].append(record)
        anchored_head = self.target.append_entry(registry, 'forecast', record)
        registry['forecasts'].pop()
        registry['chain'].pop()
        self.assertEqual(self.target.validate(registry), old_head)
        with self.assertRaisesRegex(self.target.ChainError, 'expect.head|链头'):
            self.target.validate(registry, expect_head=anchored_head)

    def test_legacy_read_remains_unchained_and_rejects_external_head(self):
        registry = legacy()
        before = copy.deepcopy(registry)
        self.assertIsNone(self.target.validate(registry))
        self.assertIsNone(self.target.chain_head(registry))
        self.assertEqual(registry, before)
        with self.assertRaisesRegex(self.target.ChainError, 'schema_version 1没有chain'):
            self.target.validate(registry, expect_head='a' * 64)
        self.assertEqual(registry, before)

    def test_empty_registry_can_migrate_and_start_its_chain(self):
        registry = {'format': 'xikari-forecasts-1', 'schema_version': 1, 'forecasts': [], 'resolutions': []}
        self.target.upgrade(registry)
        self.assertEqual(registry['legacy_prefix'], 0)
        self.assertEqual(registry['chain'], [])
        self.assertIsNone(self.target.chain_head(registry))
        record = frozen({'id': 'F1', 'target': 'first'})
        registry['forecasts'].append(record)
        head = self.target.append_entry(registry, 'forecast', record)
        self.assertRegex(head, r'^[0-9a-f]{64}$')
        self.assertIsNone(registry['chain'][0]['prev'])
        self.assertEqual(registry['chain'][0]['seq'], 1)
        self.assertEqual(registry['legacy_prefix'], 0)

    def test_malformed_registry_chain_fields_and_duplicate_records_are_rejected(self):
        original = legacy()
        self.target.upgrade(original)
        changes = {
            'schema_bool': lambda r: r.update(schema_version=True),
            'schema_float': lambda r: r.update(schema_version=2.0),
            'schema_unknown': lambda r: r.update(schema_version=3),
            'top_unknown': lambda r: r.update(chain_head='a' * 64),
            'format': lambda r: r.update(format='other'),
            'array_type': lambda r: r.update(forecasts={}),
            'chain_type': lambda r: r.update(chain={}),
            'prefix_bool': lambda r: r.update(legacy_prefix=True),
            'prefix_float': lambda r: r.update(legacy_prefix=3.0),
            'prefix_negative': lambda r: r.update(legacy_prefix=-1),
            'prefix_exceeds_chain': lambda r: r.update(legacy_prefix=4),
            'entry_type': lambda r: r['chain'].__setitem__(0, []),
            'entry_extra_field': lambda r: r['chain'][0].update(signature='self-signed'),
            'entry_missing_field': lambda r: r['chain'][0].pop('prev'),
            'seq_bool': lambda r: r['chain'][0].update(seq=True),
            'seq_float': lambda r: r['chain'][0].update(seq=1.0),
            'seq_gap': lambda r: r['chain'][0].update(seq=2),
            'kind_unknown': lambda r: r['chain'][0].update(kind='other'),
            'kind_list': lambda r: r['chain'][0].update(kind=[]),
            'entry_id_mismatch': lambda r: r['chain'][0].update(id='F9'),
            'entry_hash_mismatch': lambda r: r['chain'][0].update(record_sha256='0' * 64),
            'first_prev_not_null': lambda r: r['chain'][0].update(prev='0' * 64),
            'later_prev_null': lambda r: r['chain'][1].update(prev=None),
            'duplicate_forecast': lambda r: r['forecasts'].append(copy.deepcopy(r['forecasts'][0])),
            'duplicate_resolution': lambda r: r['resolutions'].append(copy.deepcopy(r['resolutions'][0])),
            'duplicate_chain_item': lambda r: r['chain'].append(copy.deepcopy(r['chain'][-1])),
            'record_not_object': lambda r: r['forecasts'].__setitem__(0, None),
            'record_missing_id': lambda r: r['forecasts'][0].pop('id'),
            'record_hash_not_string': lambda r: r['forecasts'][0].update(record_sha256=True),
            'record_id_not_string': lambda r: r['forecasts'][0].update(id=[]),
            'resolution_missing_time': lambda r: r['resolutions'][0].pop('resolved_at'),
            'resolution_unknown_parent': lambda r: r['resolutions'].__setitem__(0, frozen({'forecast_id': 'F9', 'resolved_at': '2026-01-03T00:00:00Z'})),
        }
        for label, change in changes.items():
            with self.subTest(label=label):
                registry = copy.deepcopy(original)
                change(registry)
                before = copy.deepcopy(registry)
                with self.assertRaises(self.target.ChainError):
                    self.target.validate(registry)
                self.assertEqual(registry, before)
        for bad in [None, [], True, 2]:
            with self.subTest(registry=bad), self.assertRaises(self.target.ChainError):
                self.target.validate(bad)

    def test_failed_append_does_not_mutate_registry(self):
        original = legacy()
        self.target.upgrade(original)
        record = frozen({'id': 'F3', 'target': 'new'})
        for label in ['not_appended', 'wrong_record', 'multiple_pending', 'corrupt_existing_chain', 'already_linked', 'unknown_kind']:
            with self.subTest(label=label):
                registry = copy.deepcopy(original)
                supplied = record
                kind = 'forecast'
                if label != 'not_appended':
                    registry['forecasts'].append(record)
                if label == 'wrong_record':
                    supplied = frozen({'id': 'F4', 'target': 'different'})
                if label == 'multiple_pending':
                    registry['forecasts'].insert(-1, frozen({'id': 'F4', 'target': 'another'}))
                if label == 'corrupt_existing_chain':
                    registry['chain'][0]['prev'] = '0' * 64
                if label == 'already_linked':
                    self.target.append_entry(registry, kind, record)
                if label == 'unknown_kind':
                    kind = []
                before = copy.deepcopy(registry)
                with self.assertRaises(self.target.ChainError):
                    self.target.append_entry(registry, kind, supplied)
                self.assertEqual(registry, before)

    def test_upgrade_rejects_invalid_input_without_partial_migration(self):
        registry = legacy()
        registry['forecasts'][0]['target'] = 'changed'
        before = copy.deepcopy(registry)
        with self.assertRaises(self.target.ChainError):
            self.target.upgrade(registry)
        self.assertEqual(registry, before)

    def test_append_requires_explicit_migration_before_adding_new_record(self):
        registry = legacy()
        record = frozen({'id': 'F3', 'target': 'new'})
        registry['forecasts'].append(record)
        before = copy.deepcopy(registry)
        with self.assertRaisesRegex(self.target.ChainError, 'upgrade'):
            self.target.append_entry(registry, 'forecast', record)
        self.assertEqual(registry, before)

    def test_non_json_and_recursive_records_raise_chain_error(self):
        for value in [float('nan'), float('inf'), (1, 2), {1: 'non-text-key'}]:
            with self.subTest(value=repr(value)):
                registry = legacy()
                registry['forecasts'][0]['invalid'] = value
                with self.assertRaises(self.target.ChainError):
                    self.target.upgrade(registry)
        registry = legacy()
        registry['forecasts'][0]['cycle'] = registry['forecasts'][0]
        with self.assertRaises(self.target.ChainError):
            self.target.upgrade(registry)

    def test_invalid_expected_heads_are_rejected(self):
        registry = legacy()
        self.target.upgrade(registry)
        for expected in ['', True, [], 'a' * 63, 'A' * 64, 'z' * 64, '0' * 64]:
            with self.subTest(expected=expected), self.assertRaises(self.target.ChainError):
                self.target.validate(registry, expect_head=expected)


if __name__ == '__main__':
    unittest.main()
