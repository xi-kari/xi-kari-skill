"""Subset the two faces used by the project introduction page.

`docs/index.html` and `docs/404.html` set headings, signs and plaques in a
heavy sans, and the introduction sets quoted source text in Song. Both are cut from Noto Sans SC and Noto Serif SC (SIL OFL
1.1) down to the characters those pages actually set in them, at one weight
each, so neither page carries an external font request.

Rebuild after changing any text inside an element whose class list contains
`display`, `sign`, `plaque` or `song`:

    python website/scripts/build_page_fonts.py --sans <NotoSansSC-VF.ttf> --serif <NotoSerifSC-VF.ttf>

Without `--sans` and `--serif` the script looks for those two files in the
operating system's font directory. `--check` only reads: it reports any page
character that the committed subsets do not cover and changes nothing.

Building requires fontTools with WOFF2 support (`pip install fonttools brotli`).
Source fonts: https://github.com/notofonts/noto-cjk
"""

from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
PAGES = [ROOT / "docs" / "index.html", ROOT / "docs" / "404.html"]
FONT_DIR = ROOT / "docs" / "assets" / "fonts"
RECORD = FONT_DIR / "source.json"
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
FACES = {
    "display": {"family": "XK Display", "file": "xk-display.woff2", "weight": 900, "classes": {"display", "sign", "plaque"}},
    "song": {"family": "XK Song", "file": "xk-song.woff2", "weight": 600, "classes": {"song"}},
}
ASCII = "".join(chr(code) for code in range(0x20, 0x7F))
PUNCTUATION = "，。：；、？！“”‘’《》（）·—…→"
# Headings the page script rewrites from published data.
SCRIPTED = {"display": "项研究任务已完成的情况待", "song": ""}


class FaceText(HTMLParser):
    """Collect the text set in each face, following class tokens down the tree."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, str | None]] = []
        self.text: dict[str, set[str]] = {name: set() for name in FACES}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tokens = set((dict(attrs).get("class") or "").split())
        face = self.stack[-1][1] if self.stack else None
        for name, spec in FACES.items():
            if tokens & spec["classes"]:
                face = name
        if tag not in VOID_TAGS:
            self.stack.append((tag, face))

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        face = self.stack[-1][1] if self.stack else None
        if face:
            self.text[face].update(char for char in data if not char.isspace())


def page_characters(html: str) -> dict[str, str]:
    """Return, per face, every character the page needs from it."""
    parser = FaceText()
    parser.feed(html)
    needed = {}
    for name in FACES:
        chars = parser.text[name] | set(ASCII) | set(PUNCTUATION) | set(SCRIPTED[name])
        needed[name] = "".join(sorted(chars))
    return needed


def missing_characters(html: str, record: dict) -> dict[str, str]:
    """Characters the page sets in a face that its committed subset lacks."""
    needed = page_characters(html)
    gaps = {}
    for name in FACES:
        covered = set(record["faces"][name]["characters"])
        gap = "".join(char for char in needed[name] if char not in covered)
        if gap:
            gaps[name] = gap
    return gaps


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


def build_face(source: Path, name: str, characters: str) -> dict:
    from fontTools import subset
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    spec = FACES[name]
    font = TTFont(source, recalcTimestamp=False)
    original = font["name"]
    source_record = {
        "family": original.getDebugName(1),
        "version": original.getDebugName(5),
        "copyright": original.getDebugName(0),
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
    font = instancer.instantiateVariableFont(font, {"wght": spec["weight"]})
    for record in list(font["name"].names):
        if record.nameID in (1, 4, 16):
            font["name"].setName(spec["family"], record.nameID, record.platformID, record.platEncID, record.langID)
        elif record.nameID == 6:
            font["name"].setName(spec["family"].replace(" ", ""), 6, record.platformID, record.platEncID, record.langID)
        elif record.nameID in (2, 17):
            font["name"].setName("Regular", record.nameID, record.platformID, record.platEncID, record.langID)
    font["OS/2"].usWeightClass = spec["weight"]
    font.flavor = "woff2"
    target = FONT_DIR / spec["file"]
    font.save(target)
    covered = "".join(sorted(chr(code) for code in font.getBestCmap() if chr(code) in set(characters)))
    return {
        "family": spec["family"],
        "file": spec["file"],
        "weight": spec["weight"],
        "bytes": target.stat().st_size,
        "sha256": sha256(target),
        "source": source_record,
        "characters": covered,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sans", type=Path, help="Noto Sans SC variable font")
    parser.add_argument("--serif", type=Path, help="Noto Serif SC variable font")
    parser.add_argument("--check", action="store_true", help="report uncovered page characters and change nothing")
    args = parser.parse_args()
    html = "".join(page.read_text(encoding="utf-8") for page in PAGES)

    if args.check:
        record = json.loads(RECORD.read_text(encoding="utf-8"))
        gaps = missing_characters(html, record)
        stale = [face["file"] for face in record["faces"].values() if sha256(FONT_DIR / face["file"]) != face["sha256"]]
        for name, gap in gaps.items():
            print(f"{name}: {len(gap)} uncovered: {gap}")
        for file in stale:
            print(f"{file}: bytes differ from source.json")
        if not gaps and not stale:
            print("page fonts cover every character set in them")
        return 1 if gaps or stale else 0

    sources = {"display": args.sans or system_font("NotoSansSC-VF.ttf"), "song": args.serif or system_font("NotoSerifSC-VF.ttf")}
    absent = [name for name, path in sources.items() if not path or not path.is_file()]
    if absent:
        print("source font not found for: " + ", ".join(absent) + "; pass --sans and --serif", file=sys.stderr)
        return 2
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    needed = page_characters(html)
    faces = {name: build_face(sources[name], name, needed[name]) for name in FACES}
    record = {"license": "SIL Open Font License 1.1", "licenseFile": "OFL.txt", "faces": faces}
    RECORD.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, face in faces.items():
        print(f"{face['file']}: {len(face['characters'])} characters, {face['bytes']} bytes")
        uncovered = "".join(char for char in needed[name] if char not in set(face["characters"]))
        if uncovered:
            print(f"  not in the source font: {uncovered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
