"""Validate separate evaluation inputs and rubrics and verify frozen files."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

INPUT_FIELDS = {'id', 'question', 'request', 'materials', 'response_instruction'}


def _rows(path: Path) -> dict:
    result = {}
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict) or not isinstance(item.get('id'), str) or not item['id'].strip():
            raise ValueError('Each item needs a nonempty string id')
        if item['id'] in result:
            raise ValueError(f'duplicate id: {item["id"]}')
        result[item['id']] = item
    if not result:
        raise ValueError('Empty evaluation set')
    return result


def validate_item_set(input_path: Path, rubric_path: Path, *, known_anchors=None,
                      expected_categories=None) -> dict:
    inputs, rubrics = _rows(input_path), _rows(rubric_path)
    if inputs.keys() != rubrics.keys():
        raise ValueError('Input and rubric ids do not match')
    total = 0
    for identifier, item in inputs.items():
        if set(item) - INPUT_FIELDS:
            raise ValueError(f'Unexpected input fields: {identifier}')
        if not any(isinstance(item.get(field), str) and item[field].strip() for field in ('question', 'request')):
            raise ValueError(f'Missing question/request: {identifier}')
        if 'materials' in item and (not isinstance(item['materials'], list)
                                   or any(not isinstance(value, str) for value in item['materials'])):
            raise ValueError(f'Materials must be plain strings: {identifier}')
        for field in ('question', 'request', 'response_instruction'):
            if field in item and not isinstance(item[field], str):
                raise ValueError(f'Input fields must be strings: {identifier}')
        rubric = rubrics[identifier]
        anchors = rubric.get('anchors')
        if not isinstance(anchors, list) or not anchors or any(not isinstance(a, str) or not a.strip() for a in anchors):
            raise ValueError(f'Missing rubric anchors: {identifier}')
        if known_anchors is not None and not set(anchors).issubset(known_anchors):
            raise ValueError(f'Unknown source anchor: {identifier}')
        criteria = rubric.get('criteria')
        if not isinstance(criteria, list) or not criteria:
            raise ValueError(f'Missing scoring criteria: {identifier}')
        criterion_ids = set()
        subtotal = 0
        for criterion in criteria:
            if not isinstance(criterion, dict):
                raise ValueError(f'Invalid scoring criterion: {identifier}')
            key, points = criterion.get('id'), criterion.get('points')
            if not isinstance(key, str) or not key or key in criterion_ids:
                raise ValueError(f'Invalid or duplicate criterion: {identifier}')
            if type(points) is not int or points < 1:
                raise ValueError(f'Invalid criterion score: {identifier}')
            if not isinstance(criterion.get('requirement'), str) or not criterion['requirement'].strip():
                raise ValueError(f'Missing criterion requirement: {identifier}')
            criterion_ids.add(key)
            subtotal += points
        if type(rubric.get('max_score')) is not int or rubric['max_score'] != subtotal:
            raise ValueError(f'Incorrect max score: {identifier}')
        if rubric.get('author_rating') is not None:
            raise ValueError(f'Frozen rubric contains author rating: {identifier}')
        total += subtotal
    categories = Counter(row.get('category') for row in rubrics.values())
    if expected_categories is not None and categories != Counter(expected_categories):
        raise ValueError('Unexpected category counts')
    return {'items': len(inputs), 'max_score': total, 'categories': dict(categories)}


def _contained(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError('Expected relative package path')
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Package path escapes root')
    return path


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def freeze_files(root: Path, relative_paths: list[str], manifest_path: Path, *,
                 protocol_id: str, subject_runs_completed: int) -> dict:
    root, manifest_path = Path(root).resolve(), Path(manifest_path).resolve()
    if subject_runs_completed != 0 or type(subject_runs_completed) is not int:
        raise ValueError('Freeze must occur before subject runs')
    if not isinstance(protocol_id, str) or not protocol_id.strip():
        raise ValueError('Protocol id is required')
    if not manifest_path.is_relative_to(root):
        raise ValueError('Manifest path escapes root')
    if manifest_path.exists():
        raise FileExistsError('Frozen manifest already exists; create a new version')
    if not relative_paths:
        raise ValueError('No files selected')
    selected, records = set(), []
    for name in relative_paths:
        path = _contained(root, name)
        if path == manifest_path:
            raise ValueError('Manifest cannot include itself')
        if path in selected:
            raise ValueError('duplicate package file')
        selected.add(path)
        data = path.read_bytes()
        records.append({'path': path.relative_to(root).as_posix(), 'bytes': len(data), 'sha256': _sha(data)})
    manifest = {'schema_version': 1, 'protocol_id': protocol_id,
                'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
                'subject_runs_completed_at_freeze': 0, 'files': records}
    data = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    with manifest_path.open('xb') as stream:
        stream.write(data)
    return {'files': len(records), 'manifest_sha256': _sha(data)}


def check_frozen(root: Path, manifest_path: Path, *, expect_manifest_sha256: str | None = None) -> dict:
    root = Path(root).resolve()
    data = Path(manifest_path).read_bytes()
    manifest_hash = _sha(data)
    if expect_manifest_sha256 is not None and manifest_hash != expect_manifest_sha256:
        raise ValueError('Frozen manifest hash differs from external reference')
    manifest = json.loads(data)
    if type(manifest.get('subject_runs_completed_at_freeze')) is not int or manifest['subject_runs_completed_at_freeze'] != 0:
        raise ValueError('Manifest does not establish freeze before runs')
    records = manifest.get('files')
    if not isinstance(records, list) or not records:
        raise ValueError('Manifest has no frozen files')
    selected = set()
    for item in records:
        if not isinstance(item, dict):
            raise ValueError('Invalid manifest file record')
        path = _contained(root, item.get('path'))
        if path in selected:
            raise ValueError('duplicate manifest path')
        selected.add(path)
        if type(item.get('bytes')) is not int or item['bytes'] < 0 or not isinstance(item.get('sha256'), str) or not re.fullmatch(r'[0-9a-f]{64}', item['sha256']):
            raise ValueError('Invalid file hash or size')
        if not path.is_file():
            raise ValueError(f'Frozen file missing: {item["path"]}')
        raw = path.read_bytes()
        if len(raw) != item['bytes'] or _sha(raw) != item['sha256']:
            raise ValueError(f'Frozen file hash/size mismatch: {item["path"]}')
    return {'files': len(records), 'manifest_sha256': manifest_hash}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)
    check = subparsers.add_parser('check')
    check.add_argument('--root', type=Path, required=True)
    check.add_argument('--manifest', type=Path, required=True)
    check.add_argument('--expect-manifest-sha256')
    validate = subparsers.add_parser('validate')
    validate.add_argument('--inputs', type=Path, required=True)
    validate.add_argument('--rubric', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = (check_frozen(args.root, args.manifest, expect_manifest_sha256=args.expect_manifest_sha256)
                  if args.command == 'check' else validate_item_set(args.inputs, args.rubric))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
