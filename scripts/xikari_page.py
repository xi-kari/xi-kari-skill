"""Pieces every generated page shares: the chart foundation stylesheet, the display cut and icons.

The foundation is `assets/xikari-base.css` preceded by the heavy display face, inlined as a
data URI so a page stays one offline file. The cut holds numerals, Latin and the words the
pages themselves set in that face; text a document wrote is set in the reader's own fonts.

Callers pass their own assets directory, so two installed copies of the Skill imported into
one process each read their own files.
"""

from __future__ import annotations

import base64
from pathlib import Path


FACES = {'zh': 'xk-display.woff2', 'en': 'xk-display-latin.woff2'}
STATION = ('<path d="M12 2.6 20.1 7.3v9.4L12 21.4 3.9 16.7V7.3Z"/>'
           '<circle cx="12" cy="12" r="1.7" fill="currentColor" stroke="none"/>')
DOWNLOAD = '<path d="M12 4v11"/><path d="m7.5 10.5 4.5 4.5 4.5-4.5"/><path d="M5 19.5h14"/>'


def icon(paths: str, extra: str = '') -> str:
    """A stroked drawing on the 24-unit grid."""
    return (f'<svg class="icon{extra}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{paths}</svg>')


def page_bar(kind: str, sheet: str) -> str:
    """The bar that opens a computed sheet: the station mark, what kind of sheet it is, and its format name.

    Both arguments are written into the page as given; the caller escapes anything it did not write itself.
    """
    return (f'<header class="page-bar"><span class="page-mark">{icon(STATION, " station")}</span>'
            f'<span class="page-kind">{kind}</span><span class="page-sheet">{sheet}</span></header>')


def display_face(assets: Path, lang: str = 'zh') -> str:
    """The @font-face rule for the display cut, or nothing when the cut is not installed."""
    try:
        data = (Path(assets) / 'fonts' / FACES.get(lang, FACES['zh'])).read_bytes()
    except OSError:
        return ''
    encoded = base64.b64encode(data).decode('ascii')
    return ('@font-face{font-family:"XK Display";font-weight:900;font-style:normal;font-display:swap;'
            f'src:url("data:font/woff2;base64,{encoded}") format("woff2")}}\n')


def foundation(assets: Path, lang: str = 'zh') -> str:
    """The display face followed by the shared chart stylesheet."""
    return display_face(assets, lang) + (Path(assets) / 'xikari-base.css').read_text(encoding='utf-8')
