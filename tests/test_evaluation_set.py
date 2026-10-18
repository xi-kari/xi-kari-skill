import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module():
    spec = importlib.util.spec_from_file_location('evaluation_set', ROOT / 'scripts/evaluation_set.py')
    target = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(target)
    return target


class EvaluationSetTests(unittest.TestCase):
    def setUp(self):
        self.target = module()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.input = self.directory / 'inputs.jsonl'
        self.rubric = self.directory / 'rubric.jsonl'
        self.write_rows(self.input, [{'id': 'N1', 'question': '怎样区分两种情况？'}])
        self.write_rows(self.rubric, [{'id': 'N1', 'category': 'cross_section', 'anchors': ['4.5'], 'criteria': [{'id': 'a', 'points': 1, 'requirement': '区分所给两种情况'}], 'max_score': 1, 'author_rating': None}])

    def write_rows(self, path, values):
        path.write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in values), encoding='utf-8')

    def rubric_rows(self):
        return [json.loads(x) for x in self.rubric.read_text(encoding='utf-8').splitlines()]

    def freeze(self):
        return self.target.freeze_files(self.directory, ['inputs.jsonl', 'rubric.jsonl'], self.directory / 'manifest.json', protocol_id='fixture', subject_runs_completed=0)

    def test_inputs_and_rubric_are_paired_without_modifying_them(self):
        before = [p.read_bytes() for p in (self.input, self.rubric)]
        result = self.target.validate_item_set(self.input, self.rubric, known_anchors={'4.5'}, expected_categories={'cross_section': 1})
        self.assertEqual(result['items'], 1)
        self.assertEqual(result['max_score'], 1)
        self.assertEqual(before, [p.read_bytes() for p in (self.input, self.rubric)])

    def test_rubric_fields_must_not_leak_into_subject_input(self):
        self.write_rows(self.input, [{'id': 'N1', 'question': '题目', 'expected': '答案'}])
        with self.assertRaisesRegex(ValueError, 'input fields'):
            self.target.validate_item_set(self.input, self.rubric)

    def test_duplicate_ids_and_unpaired_items_rejected(self):
        self.write_rows(self.input, [{'id': 'N1', 'question': '甲'}, {'id': 'N1', 'question': '乙'}])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.target.validate_item_set(self.input, self.rubric)
        self.write_rows(self.input, [{'id': 'N2', 'question': '乙'}])
        with self.assertRaisesRegex(ValueError, 'ids'):
            self.target.validate_item_set(self.input, self.rubric)

    def test_anchors_and_category_counts_checked(self):
        with self.assertRaisesRegex(ValueError, 'anchor'):
            self.target.validate_item_set(self.input, self.rubric, known_anchors={'3.1'})
        with self.assertRaisesRegex(ValueError, 'categor'):
            self.target.validate_item_set(self.input, self.rubric, expected_categories={'cross_section': 2})

    def test_score_totals_and_duplicate_criteria_rejected(self):
        rows = self.rubric_rows()
        rows[0]['max_score'] = 2
        self.write_rows(self.rubric, rows)
        with self.assertRaisesRegex(ValueError, 'score'):
            self.target.validate_item_set(self.input, self.rubric)
        rows[0]['criteria'] *= 2
        self.write_rows(self.rubric, rows)
        with self.assertRaisesRegex(ValueError, 'criteri'):
            self.target.validate_item_set(self.input, self.rubric)

    def test_author_rating_cannot_be_prefilled_in_frozen_rubric(self):
        rows = self.rubric_rows()
        rows[0]['author_rating'] = 'good'
        self.write_rows(self.rubric, rows)
        with self.assertRaisesRegex(ValueError, 'author'):
            self.target.validate_item_set(self.input, self.rubric)

    def test_freeze_requires_no_prior_subject_runs(self):
        with self.assertRaisesRegex(ValueError, 'before'):
            self.target.freeze_files(self.directory, ['inputs.jsonl'], self.directory / 'manifest.json', protocol_id='fixture', subject_runs_completed=1)
        self.assertFalse((self.directory / 'manifest.json').exists())

    def test_frozen_manifest_cannot_be_overwritten(self):
        self.freeze()
        original = (self.directory / 'manifest.json').read_bytes()
        with self.assertRaises(FileExistsError):
            self.freeze()
        self.assertEqual(original, (self.directory / 'manifest.json').read_bytes())

    def test_missing_modified_and_reordered_files_fail(self):
        self.freeze()
        raw = self.input.read_bytes()
        self.input.write_bytes(raw + b'\n')
        with self.assertRaisesRegex(ValueError, 'hash|size'):
            self.target.check_frozen(self.directory, self.directory / 'manifest.json')
        self.input.write_bytes(raw)
        self.rubric.unlink()
        with self.assertRaisesRegex(ValueError, 'missing'):
            self.target.check_frozen(self.directory, self.directory / 'manifest.json')

    def test_manifest_expected_hash_detects_resealing(self):
        result = self.freeze()
        manifest = self.directory / 'manifest.json'
        data = json.loads(manifest.read_text(encoding='utf-8'))
        data['protocol_id'] = 'changed'
        manifest.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'manifest hash'):
            self.target.check_frozen(self.directory, manifest, expect_manifest_sha256=result['manifest_sha256'])

    def test_paths_cannot_escape_package_or_duplicate_files(self):
        with self.assertRaisesRegex(ValueError, 'path'):
            self.target.freeze_files(self.directory, ['../outside.json'], self.directory / 'manifest.json', protocol_id='fixture', subject_runs_completed=0)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.target.freeze_files(self.directory, ['inputs.jsonl', 'inputs.jsonl'], self.directory / 'manifest.json', protocol_id='fixture', subject_runs_completed=0)

    def test_check_is_read_only_and_returns_external_reference(self):
        frozen = self.freeze()
        files = sorted(self.directory.iterdir())
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in files}
        result = self.target.check_frozen(self.directory, self.directory / 'manifest.json', expect_manifest_sha256=frozen['manifest_sha256'])
        self.assertEqual(result['files'], 2)
        self.assertEqual(result['manifest_sha256'], hashlib.sha256((self.directory / 'manifest.json').read_bytes()).hexdigest())
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in files})


if __name__ == '__main__':
    unittest.main()
