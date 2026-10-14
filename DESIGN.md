---
name: Xi-Kari project introduction
description: Visual system for docs/index.html only; the existing blog identity adapted to project reading and research navigation.
colors:
  accent: "rgb(68 91 159)"
  background: "rgb(245 248 252)"
  surface: "rgb(255 255 255)"
  ink: "rgb(31 48 73)"
  muted: "rgb(88 105 128)"
  line: "rgb(208 219 233)"
  soft: "rgb(231 237 249)"
  night-accent: "rgb(177 193 245)"
  night-background: "rgb(20 29 45)"
  night-surface: "rgb(28 40 59)"
  night-ink: "rgb(229 237 250)"
  night-muted: "rgb(168 186 210)"
  night-line: "rgb(59 77 104)"
  night-soft: "rgb(35 49 73)"
typography:
  display:
    fontFamily: "'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', serif"
    fontSize: "clamp(28px, 2.7vw, 39px)"
    fontWeight: 500
    lineHeight: 1.35
  headline:
    fontFamily: "'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', serif"
    fontSize: "clamp(29px, 3.5vw, 43px)"
    fontWeight: 500
    lineHeight: 1.65
    letterSpacing: ".04em"
  title:
    fontFamily: "'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', serif"
    fontSize: "19px"
    fontWeight: 500
    lineHeight: 1.65
  body:
    fontFamily: "'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 2.1
  label:
    fontFamily: "'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.8
  command:
    fontFamily: "ui-monospace, Consolas, monospace"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 2
rounded:
  control: "8px"
  command: "12px"
  round: "50%"
spacing:
  small: "8px"
  control: "12px"
  row: "18px"
  section-detail: "24px"
  group: "34px"
  intermediate-gap: "48px"
  desktop-gap: "90px"
components:
  icon-button:
    rounded: "{rounded.round}"
    padding: "9px"
    width: "40px"
    height: "40px"
  icon-button-hover:
    backgroundColor: "{colors.soft}"
  status-filter:
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "9px 14px"
  status-filter-selected:
    backgroundColor: "{colors.soft}"
    textColor: "{colors.accent}"
  command:
    backgroundColor: "rgb(255 255 255 / .65)"
    rounded: "{rounded.command}"
    padding: "24px 56px 24px 22px"
  search:
    padding: "8px 0"
  domain-title:
    typography: "{typography.title}"
---

# Design System: Xi-Kari project introduction

## Overview

**Creative North Star: "The existing blog, carried into a reading page"**

This document applies only to `docs/index.html` and its page assets. It does not define Xi-Kari theory, source documents, Skill semantics, or the design of the original blog. The visual authority is the user's existing [blog homepage](https://xi-kari.com/): blue-white surfaces, dark blue text, muted indigo, Chinese serif lettering, the original Chinese wordmark and Hiiragi Shinonome vector signature.

One static landscape anchors the opening scene. Below it, generous open sections, fine dividers and a grouped research list support reading. The page has no shadow-based card system. Asset identity and original image bytes are recorded in `docs/assets/provenance.json`.

**Key Characteristics:**

- Original signature, ink lettering, icon color field and three tide layers.
- Open reading columns that become one column on small screens.
- Quiet controls with explicit focus and selected states.
- Shared published research-completion status, with a separate historical topic directory.

## Colors

The light palette is cool paper, blue ink and muted indigo; night mode preserves those roles with dark blue surfaces and pale text. The frontmatter records the actual RGB values from `docs/assets/project.css`.

### Primary

The accent colors identify signatures, links, focus rings, the active domain and research-progress bars. The icon field also mixes the current accent with cyan and lilac during its cycle; those mixtures are decorative animation colors, not additional interface palettes.

### Neutral

Background fills the page and tides. Surface supports the command block and skip link. Ink carries primary text; muted carries explanations, counts and dates. Line separates sections and rows; soft marks button hover.

The initial theme is light (`lace`). Only an explicitly saved `night` preference changes startup appearance. The theme toggle persists the preference locally; research completion does not use local storage. Night mode applies brightness `.7` and saturation `.9` to the wallpaper.

## Typography

Chinese serif headings use the display stack in the frontmatter; body text uses the system sans-serif stack. The quotation adds `'Kaiti SC', 'STKaiti', 'KaiTi'` before the serif fallback. The Latin signature is original SVG artwork, not replacement type.

Project title, section headings and domain titles correspond to display, headline and title. Introductory body paragraphs use the body role and stop at `65ch`; usage and research lead text use `14px` with line-height `2`. Topic labels use `14px / 1.9`; question descriptions use `12px / 1.95` and stop at `68ch`. Counts, identifiers and dates use tabular numerals.

At widths up to `760px`, the project title is `28px`, section headings are `29px / 1.6`, domain titles are `17px`, introductory copy is `14px`, and usage, research lead and topic labels are `13px`. The Chinese wordmark is `38px` with `.28em` tracking on desktop and `28px` on mobile.

## Layout

The opening cover is `100svh` with a desktop minimum height of `800px`. Its fixed wallpaper fills the clipped scene using cover cropping. Content is `min(1240px, 91.2%)`; the signature and project explanation sit to the left. The same original landscape is used by the full-image dialog.

The reading container is `min(1180px, calc(100% - 112px))`. Introduction and usage use `.85fr 1.15fr` columns with a `90px` gap. Research uses a `244px` sticky domain navigator and a flexible list, separated by `55px`. The navigator starts `100px` below the top and scrolls within `calc(100svh - 125px)`.

Research completion precedes the topic directory in the same open reading flow. A full-width progress bar accompanies the completion count; a table names each task group and its counts. When pending tasks exist, they use two columns of open, ruled rows, becoming one column on mobile. A zero pending count hides that section. Tables preserve readable numeric columns and may scroll inside their own wrapper rather than widening the page.

At widths up to `1050px`, reading gutters become `36px`, introduction/usage gaps become `48px`, and the research split becomes `200px` plus the list with a `34px` gap.

At widths up to `760px`, gutters become `22px`; introduction and usage become single columns with `22px` gaps and `58px` vertical padding. The research toolbar stacks, and a native domain select replaces the sticky navigator. Topic rows lose the desktop list indent. The cover minimum becomes `890px`; the wallpaper occupies the upper `52%` of its fixed scene, crops at `58% top`, and fades vertically into the page. Cover text begins at `clamp(295px, 38svh, 350px)`.

For desktop widths from `761px` with viewport height up to `850px`, the cover uses `90px` top padding, a smaller signature and tighter heading spacing. These are the three implemented responsive conditions; they are not a general device taxonomy.

## Elevation & Depth

Depth comes from the fixed landscape, translucent paper overlays, fine grain and layered tides. Sections remain flat, with one-pixel dividers and no box shadows. The fixed navigation uses the page background at `.93` opacity; its border appears after scrolling. The full-image dialog uses the page background over an ink backdrop at `.7` opacity.

## Shapes

Controls use restrained rounded corners as recorded in the frontmatter. Icon buttons are circles; the mobile domain selector is native. Search uses a single bottom border. Domain groups, research tables, pending tasks and capability rows use horizontal rules rather than enclosed cards. The opening scene clips at its boundary; only the original tide paths shape the transition into reading content.

## Components

### Identity and scene

Keep the Chinese wordmark and original SVG signature intact. The signature contains 23 Latin stroke masks and 3 dawn ornament masks; the final mask completes at `3500ms`. Signature strokes use `cubic-bezier(.33, 0, .36, 1)`. Chinese letters settle over `350ms`, staggered by `80ms` after a `75ms` start; the guide lasts `520ms`.

The page icon field contains 96 marks in a 12-by-8 grid, with 48 visible marks in a 6-by-8 grid on mobile. Its color cycle lasts `5200ms` per mark with spatial staggering. Three tides run at `29s`, `21s` in reverse and `17s`. Continuous field and tide motion pauses when hidden or outside its observed viewport.

Reduced-motion mode displays complete lettering, a static colored icon field and stationary tides; CSS transitions and animations stop, and anchor navigation becomes immediate. Section entrances otherwise use a single `660ms` reveal with `cubic-bezier(.16,1,.3,1)`.

### Navigation and actions

Navigation is fixed, `72px` tall on desktop and `68px` on mobile. For a fine pointer with hover, it is tucked above the opening scene until pointer proximity, keyboard focus or scrolling reveals it. Mobile keeps the primary navigation visible and hides secondary links. Text links move their arrow `4px` on hover. The return-to-top control appears after `600px` of scrolling.

Icon buttons use soft hover fill. The theme toggle exposes its state through `aria-pressed`; the active domain link uses `aria-current="location"` and accent text. A visible keyboard focus ring uses the accent at `2px` with a `5px` offset. The command block wraps long text and offers a copy action with a live success or failure message.

### Research status and directory

The research section presents three distinct objects: the current manuscript's identity, a dated research-completion status, and a directory of preserved historical topics. Manuscript baseline, status-confirmation date and page update date remain separate. A confirmation date is not the actual completion date of each task. The scope note connects the completed research to the 32-domain, 296-topic directory below.

The current status shows all 620 research tasks complete, with completed totals for every group and no pending-task list. The overall bar has numeric accessible values, and each native group progress bar has a descriptive accessible name. The same full status exists in static HTML and `docs/data/research-status.json`; the script checks the JSON's arithmetic before replacing the fallback. Without JavaScript or a successful fetch, the published HTML status remains readable. An unobtrusive historical link provides the earlier snapshot without mixing its counts into the current state.

Native `details`/`summary` groups contain topic identifiers, titles and research questions. The first domain opens initially. Search matches every entered term against domain and topic text. Filtering opens matching groups and restores their prior open states when cleared. Domain navigation opens the destination, focuses its summary and updates its fragment. A native selector offers the same navigation on mobile.

The directory reads `docs/data/research-topics.json`: 32 current appendix-D domain titles and 296 preserved historical topics. `docs/data/research-progress.json` remains a separately linked historical record dated 2026-10-01; its checkmarks do not become the current theory's completion percentage. The page has no editing controls, research-write endpoint or visitor-local completion state. Maintainers update the public files and fallback together, then publish through the repository's static-site workflow described in `docs/MAINTAINING.md`.

Loading keeps directory controls disabled. A directory failure exposes retry and the downloadable text outline while the research snapshot and project text remain readable. Empty search results explain how to recover. Load and copy messages use live status regions. The full outline remains available without JavaScript.

### Artwork dialog and accessibility

The native modal dialog presents the same full landscape with descriptive alternative text and an original-image link. It supports a close button, native Escape dismissal and focus restoration to its trigger. A skip link precedes navigation. Decorative SVGs and the icon field are hidden from assistive technology; wordmarks, icon-only controls, search, domain selection and progress have accessible names.

## Do's and Don'ts

### Do

- **Do** preserve the original blog identity assets and use the single landscape recorded in the provenance file.
- **Do** use the current semantic color roles, open reading layout and native research controls.
- **Do** retain keyboard focus, reduced-motion behavior, loading feedback and recoverable failures.
- **Do** keep public progress read-only, show pending tasks only when they remain pending and publish matching data and HTML fallback.

### Don't

- **Don't** replace the signatures, invent another theme, introduce a dashboard card system or add a rotating wallpaper gallery.
- **Don't** present visitor-local checkmarks as official project progress.
- **Don't** apply this page's visual rules to theory sources or alter the original blog through this document.

## Output surfaces

The rules above define `docs/index.html`. The generated reading pages and condition
exploration pages are separate surfaces with their own systems, documented here so
the two are not confused.

### Reading page (`assets/reader.css`, `assets/reader.js`)

**North Star: "a long argument on quiet paper."** The page carries a complete
work-product; its design exists to keep a dense Chinese argument readable over
thousands of words. Warm paper, dark ink, restrained blue accent, generous line
height.

- **Roles.** `--paper` and `--page` separate the shell from the reading column;
  `--ink` and `--ink-strong` distinguish body from headings and emphasis;
  `--accent` marks links, markers, table headers, the current chapter and the
  progress line; `--soft`, `--raise` and `--accent-soft` fill code, tables and
  quotes; `--line` and `--line-strong` draw every divider. Night mode reassigns
  the same roles to dark surfaces; no structural rule changes with theme.
- **Typography.** Chinese serif for headings, system sans for body, monospace
  for code and unrendered formula source. Four body sizes step through
  `data-font`. Headings use `text-wrap: balance`.
- **Composition.** A sticky toolbar, a sticky directory column and one reading
  column capped at `74ch`. Paragraph rhythm is uniform; runs of long paragraphs
  stay whole rather than being broken into cards.
- **Structure marks.** The title carries a short accent rule; level-two headings
  a hairline above and a small accent dash before; clauses a left rule. These
  are orientation marks, not decoration; they must never introduce content.
- **Tables.** Each table sits in its own bordered, scrollable frame so a wide
  comparison never widens the page. Headers are tinted, rows alternate in the
  paper tone, numerals are tabular.
- **Reading aids.** A scroll-position progress line under the toolbar, search
  that highlights in place without hiding unmatched text, a "追问此处" panel
  that quotes the reader's own selection, footnote reference and return links,
  and a print stylesheet that drops chrome, flattens fills and keeps tables
  from splitting rows.
- **Constraints.** Everything stays one offline file: no network requests, no
  external stylesheet or script, KaTeX and its fonts inlined only when a formula
  is present. The reader does not add, summarize or reorder content.

### Condition page (`assets/condition-lab.css`, `assets/condition-lab.js`)

**North Star: "a worked calculation, shown honestly."** A cooler green-neutral
system, deliberately distinct from the reading page so a model result is never
mistaken for prose argument.

- The selectors, the current-state line and the result tables are the whole
  page. The current state is stated as a filled band, not a badge or a score.
- Every table names its own identity: inputs with basis and source, derived
  quantities with formula, constraints with their explicit test.
- Unknown, assumed and observed values keep separate wording; no state is
  rendered as a number it does not have.
- Print flattens the page to the calculation and drops the selectors.

Both surfaces are generated by standard-library Python from the same skill
assets. They read the assets at generation time and inline them, so editing
`assets/` changes the next generated document and never the repository site.

### Comparison table (`scripts/comparison.py`)

**North Star: "every cell keeps its own basis."** A third generated surface, in a
single self-contained HTML file with no external stylesheet, script, or font.

- Each cell carries one of three declared identities: fact (the author states a
  source; the tool does not verify it), assumption, or unknown. The identity is
  rendered as an inline tag, so it survives being read without color.
- Unknown is never drawn as a number, a zero, or the bottom of a scale, and never
  enters a ranking. A dimension that has no shared scale produces no order at all,
  only the values with their reasons.
- No cross-dimension weighting and no overall winner: the page states that
  boundary in its own text, in the Markdown, and in the JSON.
- Print flattens the tags to bordered words and drops the tinted fills.

### Word document (`scripts/render_docx.py`)

**North Star: "the same argument, in a document someone else can annotate."**
Not a web surface — a real `.docx` OOXML package written with `zipfile` and
hand-built parts, so the recipient opens it in Word, WPS, or LibreOffice with no
network and no original paths.

- Headings, paragraphs, bold and italic, nested lists, blockquotes, fenced code,
  pipe tables, rules, footnotes collected at the end, and byte-embedded local
  images.
- Remote images are never fetched. The alt text and address are kept as visible
  text, because an export that quietly reaches the network is not offline.
- Markdown it cannot represent is kept as visible source and listed in the
  command's `unsupported` field. Nothing is dropped in silence.
- The document is one version of the current manuscript. When the argument
  changes, it is re-exported rather than patched in Word.

These generated surfaces stay deliberately distinct — warm paper for long
argument, cool green for a worked calculation, this one for a comparison, and a
plain document for hand-off —
so a reader can tell at a glance what kind of artifact they are holding.
