"""Build or check the English reference edition of the Xikari manuscript.

Maintenance tool for this repository; it is not part of the installed skill.

    python scripts/build_english_edition.py --from <translation-directory>
    python scripts/build_english_edition.py --check

``--from`` reads the page-by-page English translation (its ``source-manifest.json``,
Chinese page snapshots, English pages and ``termbase.csv``), verifies that the
Chinese pages are the same text as ``source/`` here, and writes
``source/en/`` plus ``references/glossary-en.md``. ``--check`` only reads the
vendored files and reports whether the edition still aligns with the Chinese
source; it never writes.

The Chinese manuscript remains the sole theory authority. The English edition is
a reference translation for terminology, quotation and English readers.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from read_source import build_index  # noqa: E402
sys.path.pop(0)

ROOT = Path(__file__).resolve().parents[1]
ZH_MANIFEST = ROOT / "source" / "source-manifest.json"
EN_DIR = ROOT / "source" / "en"
EN_MANIFEST = EN_DIR / "source-manifest.json"
EN_FILE = "Xikari-On-Conditions-Structure-and-Transformation.md"
GLOSSARY = ROOT / "references" / "glossary-en.md"
TITLE = "Xikari: On Conditions, Structure, and Transformation"

CJK = re.compile(r"[㐀-鿿]")
# A gloss is a parenthetical made only of Chinese characters and Chinese
# punctuation that follows an English term, e.g. "circle (圈层)".
GLOSS = re.compile(r" ?\((?=[^()\n]*[㐀-鿿])[㐀-鿿　-〿！-～·—–\-/ A-Z0-9]+\)")
CODE_OR_LINK = re.compile(r"`[^`\n]*`|\]\([^)\s]*\)")
PAGE_LINK = re.compile(r"\]\(/works/xikari-conditions/[^/#)\s]+/?(#[^)\s]*)?\)( \(in Chinese\))?")
NOTE_REF = re.compile(r"\[\^(tn-[^\]]+)\]")
NOTE_DEF = re.compile(r"^\[\^[^\]]+\]:.*?(?=\n\s*\n|\Z)", re.M | re.S)
FOOTNOTE_LINE = re.compile(r"^\[\^[^\]]+\]:")
ESCAPES = {"\\_": "_", "\\*": "*", "\\[": "[", "\\]": "]", "\\|": "|", "\\<": "<", "\\>": ">", "\\~": "~", "\\#": "#"}

# The translation keeps these definitional tuples in their Chinese wording so the
# web edition's literal checks pass, and gives the English in a translator's
# note. The reference edition puts the English inline and keeps the Chinese in
# the note. Each entry: page slug, Chinese literal, English literal, note id.
TUPLES = [
    ("03-grammar",
     "M(SP0→SP1)=<保留变量, 改变变量, 丢失变量, 转换算子, 误差, 适用区间>",
     "M(SP0→SP1)=<retained variables, changed variables, lost variables, conversion operator, error, applicable range>",
     "tn-fields"),
    ("10-actors",
     "A* = <行动者 ID，观察窗，圈层成员关系，角色，慢变量，中变量，快变量，物质条件，体验—意义条件，未知项，证据状态，隐私与允许用途>",
     None, "tn-actor-tuple"),
    ("11-circles",
     "C* = <圈层 ID，候选边界，成员资格，角色规则，进入与退出，内部状态，外部接口，物质通道，体验—意义通道，约束，时间窗，尺度剖面，同一性判据，证据状态，反例>",
     None, "tn-circle-tuple"),
    ("11-circles",
     "MC* = <行动者集合 A，圈层集合 C，圈层关系 Rcc，成员与角色映射 Rac，物质状态 M，体验—意义状态 Ψ，通道与约束 Q，事件流 E，多时钟 T，尺度剖面 SP，证据状态 W，同一性判据 K>",
     None, "tn-joint-tuple"),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end < 0:
            raise ValueError("unterminated frontmatter")
        text = text[end + 4:]
    return text.strip("\n")


def comparable_lines(text: str) -> list[str]:
    """Normalize a Markdown text to the lines both editions must share."""
    rows = []
    for line in text.splitlines():
        line = re.sub(r'<a id="[^"]*"></a>', "", line).replace("　", " ").strip()
        if not line:
            continue
        for escaped, plain in ESCAPES.items():
            line = line.replace(escaped, plain)
        line = line.replace("&lt;", "<").replace("&gt;", ">")
        line = re.sub(r"\]\(/works/xikari-conditions/[^/#)]*/?(#[^)]*)?\)", lambda m: "](" + (m.group(1) or "") + ")", line)
        rows.append(re.sub(r"\s+", " ", line))
    return rows


def blocks(text: str) -> list[str]:
    return [b.strip() for b in re.split(r"\n\s*\n", NOTE_DEF.sub("", text)) if b.strip()]


def strip_glosses(text: str) -> str:
    """Remove Chinese glosses outside code spans and link targets."""
    out, last = [], 0
    for match in CODE_OR_LINK.finditer(text):
        out.append(GLOSS.sub("", text[last:match.start()]))
        out.append(match.group())
        last = match.end()
    out.append(GLOSS.sub("", text[last:]))
    return "".join(out)


def english_tuple(note: str) -> str:
    match = re.search(r"`([^`]+)`", note)
    if not match or CJK.search(match.group(1)):
        raise ValueError(f"translator note does not give an English tuple: {note[:80]}")
    return match.group(1)


def convert_tuples(slug: str, body: str) -> str:
    for page, chinese, english, note_id in TUPLES:
        if page != slug:
            continue
        if body.count(chinese) != 1:
            raise ValueError(f"{slug}: expected the Chinese tuple once: {chinese[:24]}…")
        pattern = re.compile(rf"^\[\^{re.escape(note_id)}\]:(.*?)(?=\n\s*\n|\Z)", re.M | re.S)
        note = pattern.search(body)
        if not note:
            raise ValueError(f"{slug}: missing translator note {note_id}")
        english = english or english_tuple(note.group(1))
        body = body.replace(chinese, english)
        replacement = f"[^{note_id}]: Translator's note: The Chinese edition writes this as `{chinese}`."
        body, count = pattern.subn(lambda _: replacement, body, count=1)
        if count != 1:
            raise ValueError(f"{slug}: translator note {note_id} could not be rewritten")
    return body


def load_translation(directory: Path) -> tuple[list[dict], dict]:
    manifest = json.loads((directory / "source-manifest.json").read_text(encoding="utf-8"))
    pages = manifest.get("files")
    if not isinstance(pages, list) or not pages:
        raise ValueError("translation manifest lists no pages")
    return pages, manifest


def assemble(directory: Path) -> tuple[str, list[dict]]:
    pages, _ = load_translation(directory)
    zh_text = (ROOT / "source" / json.loads(ZH_MANIFEST.read_text(encoding="utf-8"))["source_file"]).read_text(encoding="utf-8")
    zh_pages, parts, provenance = [], [], []
    for number, page in enumerate(pages):
        slug = page["slug"]
        snapshot = (directory / page["snapshotPath"]).read_bytes()
        if sha256(snapshot) != page["sha256"]:
            raise ValueError(f"{slug}: Chinese page snapshot does not match the translation manifest")
        zh_pages.append(strip_frontmatter(snapshot.decode("utf-8")))
        english = (directory / page["targetPath"]).read_bytes()
        body = convert_tuples(slug, strip_frontmatter(english.decode("utf-8")).replace("\r\n", "\n"))
        body = PAGE_LINK.sub(lambda m: "](" + (m.group(1) or "#document") + ")", body)
        body = strip_glosses(body)
        prefix = f"p{number:02d}-"
        body = NOTE_REF.sub(lambda m: f"[^{prefix}{m.group(1)}]", body)
        parts.append(body.rstrip())
        provenance.append({"slug": slug, "sha256": sha256(english)})
    if comparable_lines("\n\n".join(zh_pages)) != comparable_lines(zh_text):
        raise ValueError("the translation was made from a different Chinese text than source/")
    return "\n\n".join(parts) + "\n", provenance


def alignment(zh_text: str, en_text: str) -> dict:
    zh_lines, en_lines = zh_text.splitlines(), en_text.splitlines()
    zs, zp = build_index(zh_lines)
    es, ep = build_index(en_lines)
    problems = []
    if list(zs) != list(es):
        problems.append("section identifiers or their order differ")
    if sorted(zp) != sorted(ep):
        problems.append("part anchors differ")

    def section_blocks(lines: list[str], index: dict) -> dict[str, int]:
        order = sorted(index.items(), key=lambda kv: kv[1]["start"])
        counts = {}
        for pos, (key, item) in enumerate(order):
            stop = order[pos + 1][1]["start"] if pos + 1 < len(order) else item["end"]
            counts[key] = len(blocks("\n".join(lines[item["start"]:max(item["start"] + 1, stop)])))
        return counts

    if not problems:
        zb, eb = section_blocks(zh_lines, zs), section_blocks(en_lines, es)
        uneven = [key for key in zb if zb[key] != eb.get(key)]
        if uneven:
            problems.append("paragraph blocks differ in sections " + ", ".join(uneven[:12]))
    body = NOTE_DEF.sub("", en_text)
    leftover = [m.group() for m in GLOSS.finditer(body)]
    if leftover:
        problems.append(f"{len(leftover)} Chinese gloss(es) remain, e.g. {leftover[0]}")
    zh_blocks, en_blocks = blocks(zh_text), blocks(en_text)
    if len(zh_blocks) != len(en_blocks):
        problems.append(f"paragraph blocks {len(en_blocks)} != Chinese {len(zh_blocks)}")
    return {"sections": len(es), "parts": len(ep), "blocks": len(en_blocks), "problems": problems}


def glossary(directory: Path, zh_text: str, en_text: str) -> str:
    rows = list(csv.DictReader((directory / "termbase.csv").open(encoding="utf-8", newline="")))
    lower = en_text.casefold()
    chosen = []
    for row in rows:
        zh, en = row["zh"].split("#")[0].strip(), row["en"].strip()
        if not zh or not en or row["status"] not in {"locked", "proposed"}:
            continue
        position = zh_text.find(zh)
        if position < 0 or en.casefold().split(" (")[0] not in lower:
            continue
        sense = re.sub(r"\s+", " ", row["sense"].replace("|", "／")).strip()
        if len(sense) > 60:
            sense = sense[:59].rstrip("，、；。 ") + "…"
        chosen.append((position, zh, en, row["status"], sense))
    chosen.sort()
    lines = [
        "# Chinese–English Glossary",
        "",
        "English renderings used by the reference edition in `source/en/`, in order of first appearance in the Chinese source. "
        "*Locked* renderings are settled; *proposed* ones are used consistently but await the author's decision. "
        "A term keeps its rendering only in its specialized sense; ordinary uses take ordinary English. "
        "When a rendering seems to conflict with the Chinese source, the Chinese governs.",
        "",
        "| 中文 | English | Status | Sense |",
        "| --- | --- | --- | --- |",
    ]
    seen = set()
    for _, zh, en, status, sense in chosen:
        key = (zh, en, sense)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"| {zh} | {en} | {status} | {sense} |")
    return "\n".join(lines) + "\n"


def build(directory: Path) -> dict:
    zh_manifest = json.loads(ZH_MANIFEST.read_text(encoding="utf-8"))
    zh_bytes = (ROOT / "source" / zh_manifest["source_file"]).read_bytes()
    if sha256(zh_bytes) != zh_manifest["sha256"]:
        raise ValueError("Chinese source does not match its manifest")
    en_text, provenance = assemble(directory)
    zh_text = zh_bytes.decode("utf-8-sig")
    report = alignment(zh_text, en_text)
    if report["problems"]:
        raise ValueError("; ".join(report["problems"]))
    data = en_text.encode("utf-8")
    EN_DIR.mkdir(parents=True, exist_ok=True)
    (EN_DIR / EN_FILE).write_bytes(data)
    manifest = {
        "title": TITLE,
        "author": "Xikari",
        "language": "en",
        "role": "reference translation; the Chinese source governs",
        "source_file": EN_FILE,
        "sha256": sha256(data),
        "bytes": len(data),
        "translates": {"source_file": zh_manifest["source_file"], "sha256": zh_manifest["sha256"]},
        "alignment": {key: report[key] for key in ("sections", "parts", "blocks")},
        "edition_notes": [
            "Chinese glosses after English terms are omitted; see references/glossary-en.md.",
            "Definitional tuples are given in English; the Chinese wording is kept in translator's notes.",
            "Translator's notes are marked [^pNN-tn-…] and are not part of the author's text.",
        ],
        "translation_pages": provenance,
    }
    EN_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    GLOSSARY.write_text(glossary(directory, zh_text, en_text), encoding="utf-8", newline="\n")
    return {"written": [f"source/en/{EN_FILE}", "source/en/source-manifest.json", "references/glossary-en.md"],
            "sha256": manifest["sha256"], **{k: report[k] for k in ("sections", "parts", "blocks")}}


def check() -> dict:
    zh_manifest = json.loads(ZH_MANIFEST.read_text(encoding="utf-8"))
    en_manifest = json.loads(EN_MANIFEST.read_text(encoding="utf-8"))
    zh_bytes = (ROOT / "source" / zh_manifest["source_file"]).read_bytes()
    en_bytes = (EN_DIR / en_manifest["source_file"]).read_bytes()
    problems = []
    if sha256(en_bytes) != en_manifest["sha256"] or len(en_bytes) != en_manifest["bytes"]:
        problems.append("English edition bytes differ from its manifest")
    if en_manifest.get("translates", {}).get("sha256") != zh_manifest["sha256"]:
        problems.append("English edition translates a different Chinese source; rebuild it after revising the translation")
    if b"\r\n" in en_bytes:
        problems.append("English edition must use LF line endings")
    report = alignment(zh_bytes.decode("utf-8-sig"), en_bytes.decode("utf-8"))
    problems.extend(report["problems"])
    return {"ok": not problems, "sha256": sha256(en_bytes), "translates": en_manifest.get("translates", {}).get("sha256"),
            **{k: report[k] for k in ("sections", "parts", "blocks")}, "problems": problems}


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--from", dest="source", type=Path, help="Translation directory to build from")
    group.add_argument("--check", action="store_true", help="Verify the vendored English edition; read-only")
    args = parser.parse_args()
    try:
        result = check() if args.check else build(args.source)
    except (OSError, ValueError, KeyError) as exc:
        print(f"English edition: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
