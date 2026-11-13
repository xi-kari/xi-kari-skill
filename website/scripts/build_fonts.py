"""Subset the handbook's display face.

Titles, strip numbers, signs and the theme's fixed headings are set in a heavy
sans cut from Noto Sans SC (SIL OFL 1.1) at weight 900. The subset holds the
characters of the theme's own strings, the book index, and every first- and
second-level heading, so one small file serves the whole site. Body text,
quotations and lesson content use the reader's system fonts.

Rebuild after headings, index titles or theme strings gain new characters:

    python website/scripts/build_fonts.py --font <NotoSansSC-VF.ttf>

Without `--font` the script looks for that file in the operating system's font
directory. `--check` only reads: it reports characters the committed subset
does not cover and changes nothing.

Building requires fontTools with WOFF2 support (`pip install fonttools brotli`).
Source font: https://github.com/notofonts/noto-cjk
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


WEBSITE = Path(__file__).resolve().parents[1]
THEME = WEBSITE / ".vitepress" / "theme"
FONT_DIR = THEME / "fonts"
CSS_PATH = THEME / "styles" / "fonts.css"
RECORD = FONT_DIR / "source.json"
FAMILY = "XK Display"
FILE = "xk-display.woff2"
WEIGHT = 900
ASCII = "".join(chr(code) for code in range(0x20, 0x7F))
PUNCTUATION = "，。：；、？！“”‘’《》（）〈〉【】·—–…→≠§"


def is_cjk(char: str) -> bool:
    code = ord(char)
    return 0x3400 <= code <= 0x4DBF or 0x4E00 <= code <= 0x9FFF or 0xF900 <= code <= 0xFAFF


def needed_characters() -> str:
    """Every character the site sets in the display face."""
    chars = set(ASCII) | set(PUNCTUATION)
    theme_files = [path for pattern in ("*.vue", "*.ts") for path in THEME.rglob(pattern)]
    theme_files += [WEBSITE / ".vitepress" / "config.mts", WEBSITE / ".vitepress" / "theory-sidebar.json"]
    for path in theme_files:
        chars.update(char for char in path.read_text(encoding="utf-8") if is_cjk(char))
    for path in WEBSITE.rglob("*.md"):
        if "node_modules" in path.parts or path.name == "LESSONS.md":
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# ") or line.startswith("## "):
                chars.update(char for char in line.lstrip("# ") if not char.isspace())
    return "".join(sorted(chars))


def missing_characters(record: dict) -> str:
    covered = set(record["characters"])
    return "".join(char for char in needed_characters() if char not in covered)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def system_font(name: str) -> Path | None:
    roots = [Path(os.environ[key]) / "Fonts" for key in ("WINDIR", "SystemRoot") if os.environ.get(key)]
    roots += [Path("/usr/share/fonts"), Path("/Library/Fonts"), Path.home() / "Library" / "Fonts"]
    for root in roots:
        if root.is_dir():
            for found in root.rglob(name):
                return found
    return None


def build(source: Path) -> dict:
    from fontTools import subset
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    characters = needed_characters()
    font = TTFont(source, recalcTimestamp=False)
    names = font["name"]
    origin = {
        "family": names.getDebugName(1),
        "version": names.getDebugName(5),
        "copyright": names.getDebugName(0),
        "sha256": sha256(source),
    }
    options = subset.Options()
    options.layout_features = ["kern", "locl", "ccmp", "mark", "mkmk"]
    options.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14]
    options.name_languages = ["*"]
    options.notdef_outline = True
    options.glyph_names = False
    options.hinting = False
    options.desubroutinize = True
    options.drop_tables += ["DSIG", "vhea", "vmtx", "VORG", "BASE"]
    cutter = subset.Subsetter(options)
    cutter.populate(text=characters)
    cutter.subset(font)
    font = instancer.instantiateVariableFont(font, {"wght": WEIGHT})
    for entry in list(font["name"].names):
        if entry.nameID in (1, 4, 16):
            font["name"].setName(FAMILY, entry.nameID, entry.platformID, entry.platEncID, entry.langID)
        elif entry.nameID == 6:
            font["name"].setName(FAMILY.replace(" ", ""), 6, entry.platformID, entry.platEncID, entry.langID)
        elif entry.nameID in (2, 17):
            font["name"].setName("Regular", entry.nameID, entry.platformID, entry.platEncID, entry.langID)
    font["OS/2"].usWeightClass = WEIGHT
    font.flavor = "woff2"
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    for old in FONT_DIR.glob("xk-fangsong-*.woff2"):
        old.unlink()
    target = FONT_DIR / FILE
    font.save(target)
    covered = set(chr(code) for code in font.getBestCmap())
    record = {
        "license": "SIL Open Font License 1.1",
        "licenseFile": "public/licenses/NotoSansSC-OFL.txt",
        "family": FAMILY,
        "file": FILE,
        "weight": WEIGHT,
        "bytes": target.stat().st_size,
        "sha256": sha256(target),
        "source": origin,
        "characters": "".join(char for char in characters if char in covered),
    }
    RECORD.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CSS_PATH.write_text(
        f"/* Generated by website/scripts/build_fonts.py from {origin['family']} {origin['version']}.\n"
        "   SIL Open Font License 1.1, see public/licenses/NotoSansSC-OFL.txt. */\n"
        "@font-face {\n"
        f"  font-family: \"{FAMILY}\";\n  font-style: normal;\n  font-weight: {WEIGHT};\n"
        "  font-display: swap;\n"
        f"  src: url(\"../fonts/{FILE}\") format(\"woff2\");\n}}\n",
        encoding="utf-8",
    )
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--font", type=Path, help="Noto Sans SC variable font")
    parser.add_argument("--check", action="store_true", help="report uncovered characters and change nothing")
    args = parser.parse_args()

    if args.check:
        record = json.loads(RECORD.read_text(encoding="utf-8"))
        gap = missing_characters(record)
        stale = sha256(FONT_DIR / record["file"]) != record["sha256"]
        if gap:
            print(f"{len(gap)} uncovered: {gap}")
        if stale:
            print(f"{record['file']}: bytes differ from source.json")
        if not gap and not stale:
            print("the display subset covers every character set in it")
        return 1 if gap or stale else 0

    source = args.font or system_font("NotoSansSC-VF.ttf")
    if not source or not source.is_file():
        print("source font not found; pass --font", file=sys.stderr)
        return 2
    record = build(source)
    needed = needed_characters()
    print(f"{record['file']}: {len(record['characters'])} characters, {record['bytes']} bytes")
    absent = "".join(char for char in needed if char not in set(record["characters"]))
    if absent:
        print(f"not in the source font: {absent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
