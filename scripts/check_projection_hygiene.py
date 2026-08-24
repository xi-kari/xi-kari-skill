#!/usr/bin/env python3
"""answer-contract 第 7 节的投影卫生检查：扫描读者可见文本中的机器残留。

用法：python scripts/check_projection_hygiene.py 文件 [文件 ...]

检查对象是磁盘主答案（xi-kari-answer.md）与聊天投影文本；xi-kari-dossier、
验证记录等审计工件不适用本检查。全部干净时退出码 0；任一命中退出码 1，
并逐条打印 文件:行号:规则:片段；文件不可读或编码不是 UTF-8 时退出码 2。

合同例外（见 answer-contract 第 7 节）：命中内容属于题目对象本身且已用日常
语言解释时不算机器残留——该判断由交付者在验证记录中说明，本脚本只负责扫描。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("sha256-hex", re.compile(r"\b[0-9a-f]{64}\b")),
    (
        "exit-code",
        re.compile(r"退出状态|退出码|exit\s+status|exit_code", re.IGNORECASE),
    ),
    ("command-dump", re.compile(r"精确命令|字面输出|literal\s+output", re.IGNORECASE)),
    (
        "receipt-row",
        re.compile(r"^\s*\|.*(?:亲读|分段|子代理|未读|\bMATCH\b).*\|"),
    ),
    (
        "machine-token",
        re.compile(r"\bnot_run\b|\binstruction-layer\b|\bruntime-sealed\b|\bundetermined\b"),
    ),
    ("transaction-field", re.compile(r"变更分支|变更字段|DELIVERY PASS")),
    (
        "kv-field",
        re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_]*(?:[._-][A-Za-z0-9_]+)+\s*=\s*\S+\s*$"),
    ),
)

STATUS_OPENING = re.compile(r"^(?:当前|判断强度)\s*[:：]")
OPENING_WINDOW = 5


def scan_text(name: str, text: str) -> list[str]:
    findings: list[str] = []
    lines = text.splitlines()
    seen = 0
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if STATUS_OPENING.match(stripped):
            findings.append(f"{name}:{number}:status-opening:{stripped[:60]}")
        seen += 1
        if seen >= OPENING_WINDOW:
            break
    for number, line in enumerate(lines, start=1):
        for rule, pattern in RULES:
            if pattern.search(line):
                findings.append(f"{name}:{number}:{rule}:{line.strip()[:60]}")
    return findings


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    findings: list[str] = []
    for raw in argv:
        path = Path(raw)
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"ERROR: cannot read {raw}: {exc}", file=sys.stderr)
            return 2
        findings.extend(scan_text(str(path), text))
    if findings:
        print("projection hygiene: FAIL", file=sys.stderr)
        for finding in findings:
            print(f"HIT: {finding}", file=sys.stderr)
        return 1
    print("projection hygiene: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
