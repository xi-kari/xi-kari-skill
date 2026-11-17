"""Extend the handbook's committed display subset without replacing its glyphs.

Titles, strip numbers, signs and the theme's fixed headings are set in a heavy
sans cut from Noto Sans SC (SIL OFL 1.1) at weight 900. The subset holds the
characters of the theme's own strings, the book index, and every first- and
second-level heading, so one small file serves the whole site. Body text,
quotations and lesson content use the reader's system fonts.

The committed subset retains the original display face. After headings, index
titles or theme strings gain new characters, add only the missing glyphs:

    python website/scripts/build_fonts.py --font <NotoSansSC-VF.ttf>

Without `--font` the script looks for that file in the operating system's font
directory. Its hash must match the recorded original source or the pinned
supplement source below. No source font is needed when coverage is complete.
`--check` reports uncovered characters and changes nothing.

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
import tempfile


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
SUPPLEMENT_SHA256 = "d68bafcb48a2707749396aa12bbbd833cb70401f3a9a689fd2902c7e0d295964"
SUPPLEMENT_URL = "https://raw.githubusercontent.com/notofonts/noto-cjk/f8d157532fbfaeda587e826d4cd5b21a49186f7c/Sans/Variable/TTF/Subset/NotoSansSC-VF.ttf"


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


def write_outputs(payloads: dict[Path, bytes]) -> None:
    """Stage the complete font set, and restore prior files if a replacement fails."""
    staged, backups, previous, changed = {}, {}, {}, []

    def stage(path: Path, data: bytes, collection: dict) -> None:
        descriptor, name = tempfile.mkstemp(prefix=".xikari-font-", suffix=".tmp", dir=path.parent)
        collection[path] = Path(name)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())

    try:
        for path, data in payloads.items():
            previous[path] = path.read_bytes() if path.exists() else None
            stage(path, data, staged)
            if previous[path] is not None:
                stage(path, previous[path], backups)
        for path in payloads:
            current = path.read_bytes() if path.exists() else None
            if current != previous[path]:
                raise ValueError(f"output changed while the font set was staged: {path}")
            os.replace(staged[path], path)
            changed.append(path)
    except BaseException as error:
        failed = []
        for path in reversed(changed):
            try:
                if previous[path] is None:
                    path.unlink()
                else:
                    os.replace(backups[path], path)
            except OSError:
                backup = backups.pop(path, None)
                failed.append(f"{path} (backup: {backup})")
        if failed:
            raise OSError("font set could not be restored; recover from the retained backups: " + "; ".join(failed)) from error
        raise
    finally:
        for temporary in (*staged.values(), *backups.values()):
            temporary.unlink(missing_ok=True)


def build(source: Path) -> dict:
    from fontTools import merge, subset
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    previous = json.loads(RECORD.read_text(encoding="utf-8"))
    target = FONT_DIR / FILE
    if sha256(target) != previous["sha256"]:
        raise ValueError("committed display subset differs from source.json")
    source_hash = sha256(source)
    if source_hash not in {previous["source"]["sha256"], SUPPLEMENT_SHA256}:
        raise ValueError("source font differs from the original or pinned supplement; existing glyphs must be retained")
    baseline = TTFont(target, recalcTimestamp=False)
    existing = set(chr(code) for code in baseline.getBestCmap())
    characters = "".join(char for char in needed_characters() if char not in existing)
    if not characters:
        return previous
    font = TTFont(source, recalcTimestamp=False)
    names = font["name"]
    origin = {
        "family": names.getDebugName(1),
        "version": names.getDebugName(5),
        "copyright": names.getDebugName(0),
        "sha256": source_hash,
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
    added = set(chr(code) for code in font.getBestCmap())
    absent = "".join(char for char in characters if char not in added)
    if absent:
        raise ValueError(f"not in the source font: {absent}")
    with tempfile.TemporaryDirectory(prefix="xikari-display-") as temporary:
        base_path = Path(temporary) / "base.ttf"
        extra_path = Path(temporary) / "extra.ttf"
        baseline.flavor = None
        baseline.save(base_path)
        font.save(extra_path)
        combined = merge.Merger().merge([str(base_path), str(extra_path)])
        # The merger stamps both fields independently of TTFont.recalcTimestamp.
        combined["head"].created = baseline["head"].created
        combined["head"].modified = max(baseline["head"].modified, font["head"].modified)
        combined.recalcTimestamp = False
        combined.flavor = "woff2"
        font_path = Path(temporary) / FILE
        combined.save(font_path)
        font_data = font_path.read_bytes()
        combined.close()
    baseline.close()
    font.close()
    covered = existing | added
    supplements = previous.get("supplementalSources", [])
    supplement = next((item for item in supplements if item["sha256"] == source_hash), None)
    if supplement is None:
        supplement = {**origin, "characters": ""}
        if source_hash == SUPPLEMENT_SHA256:
            supplement["url"] = SUPPLEMENT_URL
        supplements.append(supplement)
    supplement["characters"] = "".join(sorted(set(supplement["characters"]) | added))
    record = {
        "license": "SIL Open Font License 1.1",
        "licenseFile": "public/licenses/NotoSansSC-OFL.txt",
        "family": FAMILY,
        "file": FILE,
        "weight": WEIGHT,
        "bytes": len(font_data),
        "sha256": hashlib.sha256(font_data).hexdigest(),
        "source": previous["source"],
        "baseline": previous.get("baseline", {
            "sha256": previous["sha256"],
            "characters": previous["characters"],
        }),
        "supplementalSources": supplements,
        "characters": "".join(sorted(covered)),
    }
    css = (
        f"/* Preserved by website/scripts/build_fonts.py from {record['source']['family']} {record['source']['version']}.\n"
        "   Missing glyphs only are supplemented; see fonts/source.json.\n"
        "   SIL Open Font License 1.1, see public/licenses/NotoSansSC-OFL.txt. */\n"
        "@font-face {\n"
        f"  font-family: \"{FAMILY}\";\n  font-style: normal;\n  font-weight: {WEIGHT};\n"
        "  font-display: swap;\n"
        f"  src: url(\"../fonts/{FILE}\") format(\"woff2\");\n}}\n"
    )
    write_outputs({
        target: font_data,
        RECORD: (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        CSS_PATH: css.encode("utf-8"),
    })
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

    record = json.loads(RECORD.read_text(encoding="utf-8"))
    if not missing_characters(record) and sha256(FONT_DIR / record["file"]) == record["sha256"]:
        print("the committed display subset already covers every character; unchanged")
        return 0
    source = args.font or system_font("NotoSansSC-VF.ttf")
    if not source or not source.is_file():
        print("source font not found; pass --font", file=sys.stderr)
        return 2
    try:
        record = build(source)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    needed = needed_characters()
    print(f"{record['file']}: {len(record['characters'])} characters, {record['bytes']} bytes")
    absent = "".join(char for char in needed if char not in set(record["characters"]))
    if absent:
        print(f"not in the source font: {absent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
