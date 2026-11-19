#!/usr/bin/env python3
"""List and check domain cards: header, theory binding and cited sections.

Read-only. A card records usages verified in an earlier task. Nothing here
shows that a definition is right, a source reliable or a correspondence holds.
"""

from __future__ import annotations

import argparse
import datetime
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from read_source import build_index
finally:
    sys.path.pop(0)

FORMAT = 'xikari-domain-cards-1'
ROOT = Path(__file__).resolve().parents[1]
BUNDLED = ROOT / 'references' / 'domains'
MAX_BYTES = 1024 * 1024
NOTICE = ('只读检查：卡头是否完整、所据原文是否为当前随包版本、小节引用是否存在。'
          '不说明卡片里的定义正确、来源可信或对应成立；卡片是以前核实的记录，不是本题证据。')
HEADER = re.compile(r'\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)', re.S)
ANCHOR = re.compile(r'(?:[1-9][0-9]*|[A-D])(?:\.[0-9]+)+\Z')
CITED = re.compile(r'§\s*((?:[1-9][0-9]*|[A-D])(?:\.[0-9]+)+)')
SHA256 = re.compile(r'[0-9a-f]{64}\Z')
SECTIONS = (('来源', 'source'), ('修订记录', 'revision'))


class CardError(ValueError):
    """The given location cannot be read as a card or a library."""


@lru_cache(maxsize=1)
def theory() -> dict:
    """Identify the bundled theory text and its section ids; not a content review."""
    raw = (ROOT / 'source' / 'Xikari-条件结构与转化论.md').read_bytes()
    sections, _ = build_index(raw.decode('utf-8-sig').splitlines())
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'sections': frozenset(sections)}


def card_files(location: Path | None) -> tuple[Path, list[Path]]:
    """Return the base folder and the Markdown files to read, never following a guess."""
    if location is None:
        base = BUNDLED
    elif location.is_file():
        return location.parent, [location]
    elif location.is_dir():
        base = location
    else:
        raise CardError(f'找不到领域库目录或卡片：{location}')
    files = sorted(path for path in base.rglob('*.md')
                   if path.is_file() and path.name.lower() != 'readme.md')
    return base, files


def _covered(section: str, anchors: list[str]) -> bool:
    return any(section == anchor or section.startswith(anchor + '.') for anchor in anchors)


def examine(path: Path, base: Path) -> dict:
    """Read one card and report what a careful reader would need fixed."""
    try:
        name = path.relative_to(base).as_posix()
    except ValueError:
        name = path.name
    row = {'file': name, 'id': None, 'title': None, 'scope': None, 'updated': None,
           'theory': 'not_bound', 'anchors': [], 'errors': [], 'warnings': []}
    try:
        data = path.read_bytes()
    except OSError as exc:
        row['errors'].append(f'读不到文件：{exc}')
        return row
    if len(data) > MAX_BYTES:
        row['errors'].append('卡片超过 1 MiB；按任务拆成几张。')
        return row
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        row['errors'].append('卡片须为 UTF-8 文本。')
        return row
    match = HEADER.match(text)
    if not match:
        row['errors'].append('没有卡头：首行写 ---，下一行写一行 JSON，再写 ---。')
        return row
    try:
        header = json.loads(match.group(1))
    except ValueError as exc:
        row['errors'].append(f'卡头不是合法 JSON：{exc}')
        return row
    if not isinstance(header, dict):
        row['errors'].append('卡头须为 JSON 对象。')
        return row
    for key in ('id', 'title', 'scope'):
        value = header.get(key)
        if isinstance(value, str) and value.strip():
            row[key] = value.strip()
        else:
            row['errors'].append(f'卡头缺少 {key}。' + ('scope 写机构或系统、规则版本与材料期间。' if key == 'scope' else ''))
    updated = header.get('updated')
    try:
        row['updated'] = datetime.date.fromisoformat(updated).isoformat()
    except (TypeError, ValueError):
        row['errors'].append('卡头的 updated 须为 YYYY-MM-DD 形式的日期。')
    anchors = header.get('anchors', [])
    if not isinstance(anchors, list) or any(not isinstance(a, str) or not ANCHOR.fullmatch(a) for a in anchors):
        row['errors'].append('卡头的 anchors 须为原文小节编号的列表，例如 ["2.4.3","D.25"]；没有用到时写 []。')
        anchors = []
    row['anchors'] = anchors
    body = text[match.end():]
    cited = sorted(set(CITED.findall(body)))
    digest = header.get('theory_sha256')
    reference = theory()
    if digest is None:
        if anchors or cited:
            row['errors'].append('引用了原文小节，卡头须写所据原文的 theory_sha256。')
    elif not isinstance(digest, str) or not SHA256.fullmatch(digest):
        row['errors'].append('theory_sha256 须为 64 位小写十六进制。')
    elif digest == reference['sha256']:
        row['theory'] = 'current'
        for section in sorted(set(anchors) | set(cited)):
            if section not in reference['sections']:
                row['errors'].append(f'随包原文中没有 §{section}。')
    else:
        row['theory'] = 'other_version'
        row['warnings'].append('卡片所据原文不是当前随包版本：小节引用未按当前原文核对。'
                               '复核用到的小节后更新 theory_sha256 与修订记录。')
    for section in cited:
        if not _covered(section, anchors):
            row['warnings'].append(f'正文提到 §{section}，卡头 anchors 未列；列入后使用者才知道要读它。')
    headings = [line.lstrip('#').strip().lower() for line in body.splitlines() if line.startswith('#')]
    for chinese, english in SECTIONS:
        if not any(chinese in heading or english in heading for heading in headings):
            row['warnings'].append(f'没有“{chinese}”一节。' + ('本地用法应能回到材料位置。' if chinese == '来源'
                                                           else '改义时保留原说法、日期与理由。'))
    return row


def survey(location: Path | None) -> dict:
    base, files = card_files(location)
    rows = [examine(path, base) for path in files]
    seen = {}
    for row in rows:
        if row['id'] is None:
            continue
        if row['id'] in seen:
            row['errors'].append(f'卡片 id 与 {seen[row["id"]]} 重复。')
        else:
            seen[row['id']] = row['file']
    return {'format': FORMAT, 'library': str(base), 'bundled_samples': location is None,
            'theory_sha256': theory()['sha256'], 'cards': rows, 'notice': NOTICE}


def list_cards(location: Path | None) -> dict:
    """Headers only, for choosing which card to read in full."""
    result = survey(location)
    result['cards'] = [{key: row[key] for key in ('file', 'id', 'title', 'scope', 'updated', 'theory', 'anchors')}
                       | {'problems': len(row['errors'])} for row in result['cards']]
    return result


def check_cards(location: Path | None) -> dict:
    result = survey(location)
    result['error_count'] = sum(len(row['errors']) for row in result['cards'])
    result['warning_count'] = sum(len(row['warnings']) for row in result['cards'])
    result['ok'] = result['error_count'] == 0
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--library', type=Path, help='领域库目录或单张卡片；省略时为随包样例卡')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('list', help='列出卡片的标题、适用范围、更新日期与所据原文版本')
    commands.add_parser('check', help='核对卡头、原文版本与小节引用；只读')
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    try:
        result = list_cards(args.library) if args.command == 'list' else check_cards(args.library)
    except (CardError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if args.command == 'list' or result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
