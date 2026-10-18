"""Check derived resources against source text; never certify understanding."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from read_source import build_index
sys.path.pop(0)

ROOT = Path(__file__).resolve().parents[1]
ANCHOR = re.compile(r"§\s*((?:\d+|[A-D])(?:\.\d+)+)(?!\d|\.\d)")
RANGE = re.compile(r"§\s*((?:\d+|[A-D])(?:\.\d+)+)\s*[—–-]\s*§?\s*((?:\d+|[A-D])(?:\.\d+)+)")
CARD_TYPES = {'mechanism', 'path', 'state-transition', 'cascade', 'clock', 'signal'}
STATUSES = {'draft', 'author-confirmed', 'retired'}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_units(text: str) -> dict[str, str]:
    lines = text.replace('\r\n', '\n').splitlines()
    sections, parts = build_index(lines)
    units = {key: '\n'.join(lines[row['start']:row['end']]).strip()
             for key, row in sections.items()}
    units.update({f'part:{key}': '\n'.join(lines[row['start']:row['end']]).strip()
                  for key, row in parts.items()})
    units['front'] = '\n'.join(lines[:min((row['start'] for row in parts.values()), default=0)]).strip()
    units['all'] = '\n'.join(lines).strip()
    return units


def metadata(text: str) -> dict:
    match = re.search(r'(?m)^---\s*\n(.*?)\n---\s*(?:\n|$)', text, re.S)
    if not match:
        raise ValueError('missing JSON-compatible frontmatter')
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError('frontmatter must be a JSON object (a YAML subset)') from exc
    if not isinstance(value, dict):
        raise ValueError('frontmatter must be an object')
    return value


def references(text: str) -> set[str]:
    result = set(ANCHOR.findall(text))
    for first, last in RANGE.findall(text):
        result.update((first, last))
    return result


def check(root: Path, previous_source: Path | None = None) -> dict:
    root = root.resolve()
    errors, affected, resources = [], [], []
    manifest = json.loads((root / 'source/source-manifest.json').read_text(encoding='utf-8-sig'))
    source = root / 'source' / manifest['source_file']
    if not source.resolve().is_relative_to(root / 'source'):
        raise ValueError('source file escapes source directory')
    raw = source.read_bytes()
    actual = digest(raw)
    if actual != manifest.get('sha256'):
        errors.append('source bytes differ from source manifest')
    if manifest.get('bytes', len(raw)) != len(raw):
        errors.append('source byte count differs from source manifest')
    units = source_units(raw.decode('utf-8-sig'))
    old = source_units(previous_source.read_text(encoding='utf-8-sig')) if previous_source else None
    cards = {}
    paths = (sorted((root / 'modules').glob('*/MODULE.md'))
             + sorted((root / 'rules').glob('*/*.md'))
             + sorted((root / 'cases').glob('*.md')))
    for path in paths:
        name = path.relative_to(root).as_posix()
        if not path.resolve().is_relative_to(root):
            errors.append(f'{name}: derived resource escapes package')
            continue
        text = path.read_text(encoding='utf-8-sig')
        try:
            meta = metadata(text)
        except ValueError as exc:
            errors.append(f'{name}: {exc}')
            continue
        is_card = name.startswith('rules/')
        is_module = name.startswith('modules/')
        field = 'reading' if is_module else 'anchors'
        anchors = meta.get(field)
        if not isinstance(anchors, list) or not anchors or any(not isinstance(a, str) or not a for a in anchors):
            errors.append(f'{name}: {field} must contain explicit section/part identifiers')
            anchors = []
        used = set(anchors) | references(text)
        for anchor in sorted(used):
            if anchor not in units:
                errors.append(f'{name}: unknown source anchor {anchor}')
        if meta.get('theory_sha256') != actual:
            errors.append(f'{name}: stale theory_sha256')
        if not isinstance(meta.get('id'), str) or not meta['id'].strip():
            errors.append(f'{name}: missing id')
        if is_module and len(text.splitlines()) > 300:
            errors.append(f'{name}: module exceeds 300 lines')
        if is_card:
            if meta.get('type') not in CARD_TYPES:
                errors.append(f'{name}: invalid rule type')
            if meta.get('status') not in STATUSES:
                errors.append(f'{name}: invalid rule status')
            for key in ('applies_to', 'triggers', 'competes_with'):
                value = meta.get(key)
                if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
                    errors.append(f'{name}: {key} must be a string list')
            key = meta.get('id')
            if isinstance(key, str):
                if key in cards:
                    errors.append(f'{name}: duplicate rule id {key}')
                cards[key] = (name, meta)
        changed = sorted(a for a in used if old is not None and old.get(a) != units.get(a))
        if changed:
            affected.append({'file': name, 'changed_anchors': changed, 'review': 'required'})
        resources.append({'file': name, 'id': meta.get('id'), 'anchors': sorted(used)})
    for key, (name, meta) in cards.items():
        for competitor in meta.get('competes_with', []):
            if isinstance(competitor, str) and competitor not in cards:
                errors.append(f'{name}: unknown competing rule {competitor}')
    index_path = root / 'rules/index.json'
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding='utf-8-sig'))
        rows = index.get('rules', []) if isinstance(index, dict) else index
        if isinstance(index, dict) and index.get('theory_sha256') != actual:
            errors.append('rules/index.json: stale theory_sha256')
        if not isinstance(rows, list):
            errors.append('rules/index.json: rules must be a list')
            rows = []
        seen = set()
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get('id'), str):
                errors.append('rules/index.json: every row requires id')
                continue
            key = row['id']
            if key in seen:
                errors.append(f'rules/index.json: duplicate id {key}')
            seen.add(key)
            if key not in cards:
                errors.append(f'rules/index.json: unknown card {key}')
                continue
            name, meta = cards[key]
            if row.get('file', row.get('path')) != name:
                errors.append(f'rules/index.json: incorrect file for {key}')
            for field in ('type', 'anchors', 'status', 'applies_to', 'triggers', 'competes_with'):
                if row.get(field) != meta.get(field):
                    errors.append(f'rules/index.json: {key}.{field} differs from card')
        for missing in sorted(set(cards) - seen):
            errors.append(f'rules/index.json: missing card {missing}')
    elif cards:
        errors.append('missing rules/index.json')
    if not paths:
        errors.append('no derived resources found')
    skill = root / 'SKILL.md'
    if skill.exists() and len(skill.read_text(encoding='utf-8-sig').splitlines()) > 500:
        errors.append('SKILL.md exceeds 500 lines')
    return {'ok': not errors, 'theory_sha256': actual, 'resource_count': len(resources),
            'rule_count': len(cards), 'errors': errors, 'affected': affected,
            'comparison': 'provided' if old is not None else 'not_requested',
            'scope': 'source bindings and structure only; no semantic or capability certification'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--previous-source', type=Path)
    parser.add_argument('--check', action='store_true', help='Read-only check (all modes are read-only)')
    parser.add_argument('--json', action='store_true', help='Emit machine-readable results')
    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    try:
        result = check(args.root, args.previous_source)
    except (OSError, ValueError, KeyError) as exc:
        result = {'ok': False, 'errors': [str(exc)]}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for error in result.get('errors', []):
            print(error)
        for item in result.get('affected', []):
            print(f"REVIEW {item['file']}: {', '.join(item['changed_anchors'])}")
        print(f"{'OK' if result['ok'] else 'FAILED'}: {result.get('resource_count', 0)} derived resources")
    return 0 if result['ok'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
