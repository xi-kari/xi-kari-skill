"""Build references/domain-index.md from Appendix D of the bundled theory text.

The index repeats, word for word, each domain's title, its links back to the
main text and its topic numbers, so a research task can find where the theory
itself places a field. `--check` only reads and reports.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'source' / 'Xikari-条件结构与转化论.md'
TARGET = ROOT / 'references' / 'domain-index.md'
GROUPS = (
    ('研究方法与知识', 'D.01', 'D.05'),
    ('人的能力、经验与意义', 'D.06', 'D.09'),
    ('伦理、思想传统与文化', 'D.10', 'D.13'),
    ('社会、合作与组织', 'D.14', 'D.16'),
    ('经济与金融', 'D.17', 'D.18'),
    ('政治、治理与法律', 'D.19', 'D.21'),
    ('不平等、家庭与人口', 'D.22', 'D.24'),
    ('教育、媒体与文化生活', 'D.25', 'D.27'),
    ('技术、空间、生态、风险与历史', 'D.28', 'D.32'),
)
INTRO = '''# 领域入口索引

原文附录 D 为 32 个领域各写了一节：先保留这个领域自己的问题，再连回正文中适用的表示、证据、规范和行动边界。研究或映射进入一个领域时，从这里找到对应的小节。下表的标题、正文连接和专题编号照录原文，分组只是为了查找方便，不是原文的分类。

## 怎样用

1. **按问题找领域，通常不止一个。** 一个现实问题常同时落在几节里，例如一项公共服务的研究可能同时涉及治理、法律、组织和测量。先看标题，再看各节末尾的专题定位。
2. **读完整小节，再读与本题有关的正文连接。** 用 `read_source.py --section D.16` 读小节全文；“正文连接”列出的是原文自己指回的位置，挑与本题有关的读。默认的完整阅读已经包含这些内容，这里只帮助定位；分层阅读时它们属于必须补读的依赖。
3. **它是理论对这个领域的定位，不是这个领域的操作手册。** 小节告诉你哪些区别必须保留、哪些说法不能互相顶替。领域里的定义、数据、机制和程序仍取自领域自己的来源，见[领域映射](../modules/domain-mapping/MODULE.md)。
4. **要把一个领域做深时**，按[领域专论](output-modes/domain-study.md)的要求组织：领域自己的问题和已有答案、理论的定位、逐条映射、用公认的案例检验、贡献与限度。

## 三十二个领域

'''


def domains(text: str) -> list[dict]:
    rows, current = [], None
    for line in text.splitlines():
        heading = re.match(r'^## (D\.\d\d)　(.+)$', line)
        if heading:
            current = {'id': heading.group(1), 'title': heading.group(2).strip(), 'links': '', 'topics': ''}
            rows.append(current)
        elif line.startswith('<a id="part_21"'):
            current = None
        elif current is not None and line.startswith('正文连接：'):
            links, _, entry = line[len('正文连接：'):].partition('研究入口：')
            current['links'] = links.strip().rstrip('。')
            current['topics'] = entry.strip().rstrip('。')
    if len(rows) != 32 or any(not row['links'] or not row['topics'] for row in rows):
        raise ValueError('Appendix D no longer has 32 domain sections with links and topic numbers')
    return rows


def render(raw: bytes) -> str:
    rows = domains(raw.decode('utf-8-sig'))
    header = {'id': 'DOMAIN-INDEX', 'title': '领域入口索引', 'theory_sha256': hashlib.sha256(raw).hexdigest(),
              'anchors': [row['id'] for row in rows]}
    parts = ['---\n' + json.dumps(header, ensure_ascii=False, separators=(',', ':')) + '\n---\n\n' + INTRO]
    by_id = {row['id']: row for row in rows}
    ordered = [row['id'] for row in rows]
    for name, first, last in GROUPS:
        chosen = ordered[ordered.index(first):ordered.index(last) + 1]
        parts.append(f'### {name}\n\n| 小节 | 领域 | 正文连接 | 专题编号 |\n| --- | --- | --- | --- |\n')
        for key in chosen:
            row = by_id[key]
            parts.append(f"| {row['id']} | {row['title']} | {row['links']} | {row['topics']} |\n")
        parts.append('\n')
    covered = [key for _, first, last in GROUPS for key in ordered[ordered.index(first):ordered.index(last) + 1]]
    if covered != ordered:
        raise ValueError('The groups must cover D.01 to D.32 once each, in order')
    return ''.join(parts).rstrip('\n') + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='report whether the index matches the source; write nothing')
    args = parser.parse_args()
    expected = render(SOURCE.read_bytes())
    if args.check:
        current = TARGET.read_text(encoding='utf-8') if TARGET.is_file() else ''
        if current != expected:
            print('references/domain-index.md does not match Appendix D; run scripts/build_domain_index.py', file=sys.stderr)
            return 1
        print('references/domain-index.md matches Appendix D')
        return 0
    TARGET.write_text(expected, encoding='utf-8', newline='\n')
    print(f'wrote {TARGET.relative_to(ROOT).as_posix()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
