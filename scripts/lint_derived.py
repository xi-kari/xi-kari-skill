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
from read_source import build_index, merge_ranges
sys.path.pop(0)

ROOT = Path(__file__).resolve().parents[1]
ANCHOR = re.compile(r"§\s*((?:\d+|[A-D])(?:\.\d+)+)(?!\d|\.\d)")
RANGE = re.compile(r"§\s*((?:\d+|[A-D])(?:\.\d+)+)\s*[—–-]\s*§?\s*((?:\d+|[A-D])(?:\.\d+)+)")
SECTION_ID = re.compile(r"(?<![\w.])((?:\d+|[A-D])(?:\.\d+)+)(?!\d|\.\d)")
QUOTE_TOKEN = re.compile(r'「([^「」]*)」|〔([^〕]*)〕|\n[ \t]*\n')
CARD_TYPES = {'mechanism', 'path', 'state-transition', 'cascade', 'clock', 'signal'}
STATUSES = {'draft', 'author-confirmed', 'retired'}
DEPENDENCY_DEFINITIONS = {
    **{f'D{i}': f'3.{i + 1}' for i in range(4)},
    **{f'G{i}': f'4.{i + 2}' for i in range(1, 5)},
    **{f'E{i}': '4.8' for i in range(1, 6)},
    **{f'F{i}': '4.18' for i in range(1, 6)},
    'F6': '4.19',
    **{f'H{i}': '7.1' for i in range(1, 7)},
    **{f'N{i}': '14.3' for i in range(1, 6)},
    **{f'T{i}': '15.2' for i in range(5)},
    'IT': '13.1', 'IG': '13.3', 'SJ': '13.5', 'DF': '13.10',
    'J': '14.6', 'O': '14.6', 'PF': '14.8',
}
for _prefix, _count in (('IT', 4), ('IG', 7), ('SJ', 8), ('DF', 9), ('O', 4), ('PF', 10)):
    for _number in range(1, _count + 1):
        DEPENDENCY_DEFINITIONS[f'{_prefix}{_number}'] = DEPENDENCY_DEFINITIONS[_prefix]
        if _prefix == 'PF':
            DEPENDENCY_DEFINITIONS[f'PF-{_number}'] = DEPENDENCY_DEFINITIONS[_prefix]
DEPENDENCY_TOKEN = re.compile(r'(?<![A-Za-z0-9_])(?:'
                              + '|'.join(sorted(map(re.escape, DEPENDENCY_DEFINITIONS), key=len, reverse=True))
                              + r')(?![A-Za-z0-9_])')
DEPENDENCY_RANGE = re.compile(r'(?<![A-Za-z0-9_])(IT|IG|SJ|DF|PF-?|D|G|E|F|H|N|T|O)(\d+)'
                              r'\s*[—–-]\s*(?:\1)?(\d+)(?![A-Za-z0-9_])')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_ranges(lines: list[str]) -> dict[str, tuple[int, int]]:
    sections, parts = build_index(lines)
    ranges = {key: (row['start'], row['end']) for key, row in sections.items()}
    ranges.update({f'part:{key}': (row['start'], row['end']) for key, row in parts.items()})
    ranges['front'] = (0, min((row['start'] for row in parts.values()), default=0))
    ranges['all'] = (0, len(lines))
    return ranges


def source_units(text: str) -> dict[str, str]:
    lines = text.replace('\r\n', '\n').splitlines()
    return {key: '\n'.join(lines[start:end]).strip()
            for key, (start, end) in source_ranges(lines).items()}


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


def reading_core(root: Path, units: dict[str, str], errors: list[str]) -> list[str]:
    name = 'references/reading-core.json'
    path = root / name
    if not path.resolve().is_relative_to(root):
        errors.append(f'{name}: reading core escapes package')
        return []
    try:
        value = json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as exc:
        errors.append(f'{name}: cannot read reading core: {exc}')
        return []
    anchors = value.get('reading') if isinstance(value, dict) else None
    if (not isinstance(anchors, list) or not anchors
            or any(not isinstance(anchor, str) or not anchor for anchor in anchors)):
        errors.append(f'{name}: reading must contain explicit section/part identifiers')
        return []
    for anchor in sorted(set(anchors)):
        if anchor not in units:
            errors.append(f'{name}: unknown source anchor {anchor}')
    return anchors


def original_quotes(text: str) -> list[dict]:
    quotes, pending = [], []
    for token in QUOTE_TOKEN.finditer(text):
        if token.group(1) is not None:
            pending.append({'text': token.group(1), 'line': text.count('\n', 0, token.start()) + 1})
            continue
        if token.group(2) is not None:
            citation = token.group(2).strip()
            if re.match(r'^原文\s*§', citation):
                anchors = sorted(set(SECTION_ID.findall(citation)))
                quotes.extend(dict(quote, anchors=anchors) for quote in pending)
        pending = []
    return quotes


def compact_whitespace(text: str) -> str:
    return re.sub(r'\s+', '', text)


def dependency_codes(text: str) -> set[str]:
    codes = set()
    for token in DEPENDENCY_TOKEN.finditer(text):
        code = token.group()
        before, after = text[max(0, token.start() - 40):token.start()], text[token.end():token.end() + 40]
        if code == 'J':
            if (re.search(r'(?<![A-Za-z0-9_])(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\s*$', before)
                    or re.match(r'\s*[/·⋅]\s*(?:s|K|mol|kg)\b', after)
                    or re.search(r'(?:单位|焦耳|能量)\s*(?:为|是|以|用)?\s*$', before)):
                continue
        if code == 'O':
            if (re.match(r'\s*[（(₀-₉]', after)
                    or re.search(r'(?:scale_axis:|(?:ker|rank|det|tr)\(\s*)$', before)
                    or re.search(r'(?:算子|矩阵|函数)\s*(?:为|是)?\s*$', before)):
                continue
        if code in {'J', 'O'} and re.match(r'\.\s+[A-Z][a-z]', after):
            continue
        codes.add(code)
    for match in DEPENDENCY_RANGE.finditer(text):
        prefix, first, last = match.groups()
        first, last = int(first), int(last)
        if 0 <= last - first <= 10:
            codes.update(f'{prefix}{number}' for number in range(first, last + 1)
                         if f'{prefix}{number}' in DEPENDENCY_DEFINITIONS)
    return codes


def reading_dependencies(name: str, reading: list[str], lines: list[str],
                         ranges: dict[str, tuple[int, int]]) -> list[dict]:
    covered = merge_ranges([ranges[anchor] for anchor in reading if anchor in ranges])
    codes = set()
    for start, end in covered:
        codes.update(dependency_codes('\n'.join(lines[start:end])))
    missing = {}
    for code in sorted(codes):
        definition = DEPENDENCY_DEFINITIONS[code]
        target = ranges.get(definition)
        if target is None or not any(start <= target[0] and end >= target[1] for start, end in covered):
            missing.setdefault(definition, []).append(code)
    return [{'file': name, 'codes': codes, 'definition': definition}
            for definition, codes in sorted(missing.items())]


def check(root: Path, previous_source: Path | None = None) -> dict:
    root = root.resolve()
    errors, affected, resources = [], [], []
    warnings = []
    quote_count = 0
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
    lines = raw.decode('utf-8-sig').splitlines()
    ranges = source_ranges(lines)
    compact_units = {anchor: compact_whitespace(text) for anchor, text in units.items()}
    core = reading_core(root, units, errors)
    old = source_units(previous_source.read_text(encoding='utf-8-sig')) if previous_source else None
    cards = {}
    paths = (sorted((root / 'modules').glob('*/MODULE.md'))
             + sorted((root / 'rules').glob('*/*.md'))
             + sorted((root / 'cases').glob('*.md'))
             + sorted((root / 'references').rglob('*.md'))
             + sorted((root / 'agents').rglob('*.md')))
    for path in paths:
        name = path.relative_to(root).as_posix()
        if not path.resolve().is_relative_to(root):
            errors.append(f'{name}: derived resource escapes package')
            continue
        text = path.read_text(encoding='utf-8-sig')
        optional_metadata = name.startswith(('references/', 'agents/'))
        if optional_metadata and not re.match(r'---[ \t]*\r?\n', text):
            continue
        try:
            meta = metadata(text)
        except ValueError as exc:
            errors.append(f'{name}: {exc}')
            continue
        is_card = name.startswith('rules/')
        is_module = name.startswith('modules/')
        fields = ['reading' if is_module else 'anchors']
        if optional_metadata:
            fields = [field for field in ('anchors', 'reading') if field in meta] or ['anchors']
        anchors = []
        for field in fields:
            value = meta.get(field)
            if not isinstance(value, list) or not value or any(not isinstance(a, str) or not a for a in value):
                errors.append(f'{name}: {field} must contain explicit section/part identifiers')
            else:
                anchors.extend(value)
        used = set(anchors) | references(text)
        declared = {anchor for field in ('anchors', 'reading')
                    for anchor in (meta.get(field) if isinstance(meta.get(field), list) else [])
                    if isinstance(anchor, str)}
        for quote in original_quotes(text):
            quote_count += 1
            where = f"{name}:{quote['line']}"
            used.update(quote['anchors'])
            for anchor in quote['anchors']:
                if anchor not in declared:
                    errors.append(f'{where}: original quote anchor {anchor} is not declared in anchors or reading')
            value = compact_whitespace(quote['text'])
            if not value or not any(value in compact_units.get(anchor, '') for anchor in quote['anchors']):
                errors.append(f"{where}: original quote does not match cited source section(s) {', '.join(quote['anchors'])}: 「{quote['text']}」")
        for anchor in sorted(used):
            if anchor not in units:
                errors.append(f'{name}: unknown source anchor {anchor}')
        if meta.get('theory_sha256') != actual:
            errors.append(f'{name}: stale theory_sha256')
        if not isinstance(meta.get('id'), str) or not meta['id'].strip():
            errors.append(f'{name}: missing id')
        if is_module and len(text.splitlines()) > 300:
            errors.append(f'{name}: module exceeds 300 lines')
        if is_module:
            warnings.extend(reading_dependencies(name, core + anchors, lines, ranges))
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
    if not resources:
        errors.append('no derived resources found')
    skill = root / 'SKILL.md'
    if skill.exists() and len(skill.read_text(encoding='utf-8-sig').splitlines()) > 500:
        errors.append('SKILL.md exceeds 500 lines')
    return {'ok': not errors, 'theory_sha256': actual, 'resource_count': len(resources),
            'rule_count': len(cards), 'quote_count': quote_count, 'errors': errors,
            'warnings': warnings, 'affected': affected,
            'comparison': 'provided' if old is not None else 'not_requested',
            'scope': 'source bindings, literal quotations, structure and lexical reading-dependency warnings only; '
                     'no semantic or capability certification'}


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
        for warning in result.get('warnings', []):
            print(f"WARNING {warning['file']}: {', '.join(warning['codes'])} definition §{warning['definition']} is outside declared reading")
        for item in result.get('affected', []):
            print(f"REVIEW {item['file']}: {', '.join(item['changed_anchors'])}")
        print(f"{'OK' if result['ok'] else 'FAILED'}: {result.get('resource_count', 0)} derived resources")
    return 0 if result['ok'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
