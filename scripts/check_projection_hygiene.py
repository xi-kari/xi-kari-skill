#!/usr/bin/env python3
"""answer-contract 第 7 节的投影卫生检查：扫描读者可见文本中的机器残留。

用法：python scripts/check_projection_hygiene.py 文件 [文件 ...]

检查对象是磁盘主答案（xi-kari-answer.md）与聊天投影文本；xi-kari-dossier、
验证记录等审计工件不适用本检查。全部干净时退出码 0；任一命中退出码 1，
并逐条打印 文件:行号:规则:片段；文件不可读或编码不是 UTF-8 时退出码 2。

合同例外（见 answer-contract 第 7 节）：命中内容属于题目对象本身且已用日常
语言解释时不算机器残留——该判断由交付者在验证记录中说明，本脚本只负责扫描。
扫描只能定位显式机器残留，不能验证语义完整性或因果判断是否正确。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

if __package__:
    from .xi_kari_runtime.semantic_projection import INTERNAL_ID_TOKEN
else:
    from xi_kari_runtime.semantic_projection import INTERNAL_ID_TOKEN

RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "sha256-hex",
        re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{64}(?![0-9A-Fa-f])"),
    ),
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
        re.compile(
            r"(?<![A-Za-z0-9_-])"
            r"(?:not_run|instruction-layer|runtime-sealed|undetermined|MATCH)"
            r"(?![A-Za-z0-9_-])"
        ),
    ),
    (
        "machine-id",
        re.compile(INTERNAL_ID_TOKEN.pattern, re.ASCII),
    ),
    (
        "machine-id",
        re.compile(
            r"(?<![A-Za-z0-9_-])"
            r"(?:XK(?:[0-9]|1[0-2])|(?:K|HV)[0-9]+|(?:V82|XK-PROV)-[A-Za-z0-9-]+)"
            r"(?![A-Za-z0-9_-])",
            re.IGNORECASE,
        ),
    ),
    ("transaction-field", re.compile(r"变更分支|变更字段|DELIVERY PASS")),
    (
        "kv-field",
        re.compile(
            r"(?<![A-Za-z0-9_])"
            r"[A-Za-z_][A-Za-z0-9_]*(?:[.-][A-Za-z0-9_]+)*"
            r"[ \t]*=[ \t]*(?![=>])[^\s=]+"
        ),
    ),
)

STATUS_OPENING = re.compile(
    r"^(?:\*{1,3}|_{1,3})?(?:当前|判断强度)(?:\*{1,3}|_{1,3})?\s*[:：]"
)
BLOCKQUOTE_PREFIX = re.compile(r"^(?:[ \t]*>[ \t]?)+")
URL = re.compile(r"https?://[^\s<>\]\)\"'`，。；！？]+", re.IGNORECASE)
FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
COMMAND_LANGUAGES = {
    "bash", "bat", "batch", "cmd", "console", "powershell", "ps1", "pwsh",
    "py", "python", "python3", "sh", "shell", "shell-session", "terminal", "zsh",
}
COMMAND_LINE = re.compile(
    r"^\s*(?:(?:[$>])\s*|PS [^>]*>\s*)?"
    r"(?:python(?:[23](?:\.[0-9]+)?)?|py|uv|pip[23]?|pytest|git|gh|"
    r"npm|npx|pnpm|yarn|node|bash|sh|zsh|pwsh|powershell|cmd|curl|wget|docker|kubectl)"
    r"(?:\s|$)",
    re.IGNORECASE,
)


def scan_text(name: str, text: str) -> list[str]:
    findings: list[str] = []
    lines = text.splitlines()
    for number, line in enumerate(lines, start=1):
        stripped = BLOCKQUOTE_PREFIX.sub("", line).strip()
        if not stripped or stripped.startswith("#"):
            continue
        if STATUS_OPENING.match(stripped):
            findings.append(f"{name}:{number}:status-opening:{stripped[:60]}")
        break
    fence_marker = ""
    fence_language = ""
    for number, line in enumerate(lines, start=1):
        logical_line = BLOCKQUOTE_PREFIX.sub("", line)
        fence = FENCE.match(logical_line)
        if fence:
            marker, info = fence.groups()
            if not fence_marker:
                fence_marker = marker
                fence_language = info.strip().split(maxsplit=1)[0].lower() if info.strip() else ""
                if fence_language in COMMAND_LANGUAGES:
                    findings.append(f"{name}:{number}:command-dump:{line.strip()[:60]}")
            elif marker[0] == fence_marker[0] and len(marker) >= len(fence_marker) and not info.strip():
                fence_marker = ""
                fence_language = ""
        elif fence_marker and fence_language in {"", "text", "plaintext"} and COMMAND_LINE.match(logical_line):
            findings.append(f"{name}:{number}:command-dump:{line.strip()[:60]}")
        for rule, pattern in RULES:
            candidate = URL.sub(" ", logical_line) if rule == "kv-field" else logical_line
            if pattern.search(candidate):
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
