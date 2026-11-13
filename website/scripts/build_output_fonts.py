"""Cut the display face the generated pages inline.

The reading page, the condition page and the comparison table set numerals,
designators, signs and strip values in a heavy sans. It is cut from Noto Sans SC
(SIL OFL 1.1) at weight 900 down to ASCII, the numerals and ordinal words a
heading number can carry, and the words those pages themselves set in it. Text a
document wrote is never in the cut; the pages set it in the reader's own fonts.

Two files are written to `assets/fonts/`: `xk-display.woff2` for the Chinese
interface and `xk-display-latin.woff2` for the English one. Rebuild after
changing any string returned by a generator's `display_strings()`:

    python website/scripts/build_output_fonts.py --sans <NotoSansSC-VF.ttf>

Without `--sans` the script looks for that file in the operating system's font
directory. `--check` only reads: it reports any character the committed cuts do
not cover and changes nothing.

Building requires fontTools with WOFF2 support (`pip install fonttools brotli`).
Source fonts: https://github.com/notofonts/noto-cjk
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = ROOT / 'assets' / 'fonts'
RECORD = FONT_DIR / 'source.json'
GENERATORS = ('render_answer', 'condition_lab', 'comparison')
ASCII = ''.join(chr(code) for code in range(0x20, 0x7F))
# What a heading's own number can be made of, and the marks that sit beside numerals.
NUMERALS = '〇零一二三四五六七八九十百千万亿两第部分篇编卷章节回条款项'
MARKS = '、．。，：；（）·—…％‰→×±≈≤≥′″'
CUTS = {
    'zh': {'family': 'XK Display', 'file': 'xk-display.woff2', 'weight': 900},
    'en': {'family': 'XK Display', 'file': 'xk-display-latin.woff2', 'weight': 900},
}


def generator(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    sys.modules[name] = module  # dataclasses look their module up while it is being defined
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


def needed() -> dict[str, str]:
    """Every character each cut has to hold, in a stable order."""
    characters = {}
    for lang in CUTS:
        text = set(ASCII) | set(MARKS)
        if lang == 'zh':
            text |= set(NUMERALS)
        for name in GENERATORS:
            for string in getattr(generator(name), 'display_strings', lambda _lang: [])(lang):
                text.update(char for char in string if not char.isspace())
        text.add(' ')
        characters[lang] = ''.join(sorted(text))
    return characters


def find_source(given: Path | None) -> Path:
    if given:
        return given
    folders = [Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts',
               Path(os.environ.get('LOCALAPPDATA', '')) / 'Microsoft' / 'Windows' / 'Fonts',
               Path('/usr/share/fonts'), Path('/Library/Fonts'), Path.home() / 'Library' / 'Fonts']
    for folder in folders:
        if folder.is_dir():
            for path in sorted(folder.rglob('NotoSansSC*VF*.ttf')) + sorted(folder.rglob('NotoSansSC*wght*.ttf')):
                return path
    raise SystemExit('Noto Sans SC variable font not found; pass --sans <path>.')


def check() -> int:
    """Report characters the committed cuts do not cover; change nothing."""
    try:
        record = json.loads(RECORD.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        print(f'missing or unreadable {RECORD}: {error}', file=sys.stderr)
        return 1
    failures = 0
    for lang, characters in needed().items():
        face = record.get('faces', {}).get(lang, {})
        missing = sorted(set(characters) - set(face.get('characters', '')))
        path = FONT_DIR / CUTS[lang]['file']
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ''
        if missing:
            failures += 1
            print(f'{lang}: the cut does not cover {"".join(missing)!r}', file=sys.stderr)
        if digest != face.get('sha256'):
            failures += 1
            print(f'{lang}: {path.name} does not match the recorded hash', file=sys.stderr)
    if not failures:
        print('output display cuts cover every display string')
    return 1 if failures else 0


def build(source: Path) -> int:
    from fontTools.subset import Options, Subsetter
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont

    FONT_DIR.mkdir(parents=True, exist_ok=True)
    source_bytes = source.read_bytes()
    faces = {}
    for lang, characters in needed().items():
        font = TTFont(source, recalcTimestamp=False)  # keep the source's own dates, so the same input cuts to the same bytes
        if 'fvar' in font:
            font = instantiateVariableFont(font, {'wght': CUTS[lang]['weight']}, inplace=False)
            font.recalcTimestamp = False
        names = {record.nameID: record.toUnicode() for record in font['name'].names if record.platformID == 3}
        options = Options()
        options.flavor = 'woff2'
        options.layout_features = ['kern', 'tnum', 'palt']
        options.name_IDs = [0, 1, 2]
        options.notdef_outline = True
        options.desubroutinize = True
        options.hinting = False
        subsetter = Subsetter(options)
        subsetter.populate(text=characters)
        subsetter.subset(font)
        covered = set()
        for table in font['cmap'].tables:
            covered.update(chr(code) for code in table.cmap)
        missing = sorted(set(characters) - covered - {' '})
        if missing:
            raise SystemExit(f'{source.name} has no glyph for {"".join(missing)!r}')
        target = FONT_DIR / CUTS[lang]['file']
        font.flavor = 'woff2'
        font.save(target)
        data = target.read_bytes()
        faces[lang] = {
            **CUTS[lang], 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'source': {'family': names.get(1, 'Noto Sans SC'), 'version': names.get(5, ''), 'copyright': names.get(0, ''),
                       'sha256': hashlib.sha256(source_bytes).hexdigest()},
            'characters': characters,
        }
        print(f'{target.relative_to(ROOT).as_posix()}: {len(characters)} characters, {len(data)} bytes')
    RECORD.write_text(json.dumps({'license': 'SIL Open Font License 1.1', 'licenseFile': 'OFL.txt', 'faces': faces},
                                 ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    return 0


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--sans', type=Path, help='Noto Sans SC variable font')
    parser.add_argument('--check', action='store_true', help='report uncovered characters; write nothing')
    args = parser.parse_args()
    return check() if args.check else build(find_source(args.sans))


if __name__ == '__main__':
    raise SystemExit(main())
