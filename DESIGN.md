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
- Shared published progress, with a separate local maintenance state.

## Colors

The light palette is cool paper, blue ink and muted indigo; night mode preserves those roles with dark blue surfaces and pale text. The frontmatter records the actual RGB values from `docs/assets/project.css`.

### Primary

The accent colors identify signatures, links, focus rings, native checkbox selection and the completion bar. The icon field also mixes the current accent with cyan and lilac during its cycle; those mixtures are decorative animation colors, not additional interface palettes.

### Neutral

Background fills the page and tides. Surface supports the command block and skip link. Ink carries primary text; muted carries explanations, counts and dates. Line separates sections and rows; soft marks selected filters and button hover.

The initial theme is light (`lace`). Only an explicitly saved `night` preference changes startup appearance. The theme toggle persists the preference locally; research completion does not use local storage. Night mode applies brightness `.7` and saturation `.9` to the wallpaper.

## Typography

Chinese serif headings use the display stack in the frontmatter; body text uses the system sans-serif stack. The quotation adds `'Kaiti SC', 'STKaiti', 'KaiTi'` before the serif fallback. The Latin signature is original SVG artwork, not replacement type.

Project title, section headings and domain titles correspond to display, headline and title. Introductory body paragraphs use the body role and stop at `65ch`; usage and research lead text use `14px` with line-height `2`. Topic labels use `14px / 1.9`; question descriptions use `12px / 1.95` and stop at `68ch`. Counts, identifiers and dates use tabular numerals.

At widths up to `760px`, the project title is `28px`, section headings are `29px / 1.6`, domain titles are `17px`, introductory copy is `14px`, and usage, research lead and topic labels are `13px`. The Chinese wordmark is `38px` with `.28em` tracking on desktop and `28px` on mobile.

## Layout

The opening cover is `100svh` with a desktop minimum height of `800px`. Its fixed wallpaper fills the clipped scene using cover cropping. Content is `min(1240px, 91.2%)`; the signature and project explanation sit to the left. The same original landscape is used by the full-image dialog.

The reading container is `min(1180px, calc(100% - 112px))`. Introduction and usage use `.85fr 1.15fr` columns with a `90px` gap. Research uses a `244px` sticky domain navigator and a flexible list, separated by `55px`. The navigator starts `100px` below the top and scrolls within `calc(100svh - 125px)`.

At widths up to `1050px`, reading gutters become `36px`, introduction/usage gaps become `48px`, and the research split becomes `200px` plus the list with a `34px` gap.

At widths up to `760px`, gutters become `22px`; introduction and usage become single columns with `22px` gaps and `58px` vertical padding. The research toolbar stacks, and a native domain select replaces the sticky navigator. Topic rows lose the desktop list indent. The cover minimum becomes `890px`; the wallpaper occupies the upper `52%` of its fixed scene, crops at `58% top`, and fades vertically into the page. Cover text begins at `clamp(295px, 38svh, 350px)`.

For desktop widths from `761px` with viewport height up to `850px`, the cover uses `90px` top padding, a smaller signature and tighter heading spacing. These are the three implemented responsive conditions; they are not a general device taxonomy.

## Elevation & Depth

Depth comes from the fixed landscape, translucent paper overlays, fine grain and layered tides. Sections remain flat, with one-pixel dividers and no box shadows. The fixed navigation uses the page background at `.93` opacity; its border appears after scrolling. The full-image dialog uses the page background over an ink backdrop at `.7` opacity.

## Shapes

Controls use restrained rounded corners as recorded in the frontmatter. Icon buttons are circles; native checkboxes retain their platform shape. Search uses a single bottom border. Domain groups and capability rows use horizontal rules rather than enclosed cards. The opening scene clips at its boundary; only the original tide paths shape the transition into reading content.

## Components

### Identity and scene

Keep the Chinese wordmark and original SVG signature intact. The signature contains 23 Latin stroke masks and 3 dawn ornament masks; the final mask completes at `3500ms`. Signature strokes use `cubic-bezier(.33, 0, .36, 1)`. Chinese letters settle over `350ms`, staggered by `80ms` after a `75ms` start; the guide lasts `520ms`.

The page icon field contains 96 marks in a 12-by-8 grid, with 48 visible marks in a 6-by-8 grid on mobile. Its color cycle lasts `5200ms` per mark with spatial staggering. Three tides run at `29s`, `21s` in reverse and `17s`. Continuous field and tide motion pauses when hidden or outside its observed viewport.

Reduced-motion mode displays complete lettering, a static colored icon field and stationary tides; CSS transitions and animations stop, and anchor navigation becomes immediate. Section entrances otherwise use a single `660ms` reveal with `cubic-bezier(.16,1,.3,1)`.

### Navigation and actions

Navigation is fixed, `72px` tall on desktop and `68px` on mobile. For a fine pointer with hover, it is tucked above the opening scene until pointer proximity, keyboard focus or scrolling reveals it. Mobile keeps the primary navigation visible and hides secondary links. Text links move their arrow `4px` on hover. The return-to-top control appears after `600px` of scrolling.

Icon buttons use soft hover fill. Status filters expose selection through `aria-pressed`, accent text and soft fill. A visible keyboard focus ring uses the accent at `2px` with a `5px` offset. The command block wraps long text and offers a copy action with a live success or failure message.

### Research list

Native `details`/`summary` groups contain labeled native checkboxes, topic identifiers, questions and completion dates. The first domain opens initially. Search matches every entered term against domain and topic text; status filtering combines with search. Filtering opens matching groups and restores their prior open states when cleared. Domain navigation opens the destination, focuses its summary and updates its fragment.

The public page reads `docs/data/research-topics.json` and `docs/data/research-progress.json`. It displays the shared official completion state with disabled checkboxes; the maintenance action stays hidden. A local owner session must be supplied by the maintenance service before that action appears. Editing is explicit, saves through the service to the project progress file, disables controls while saving and restores the preceding state on failure. Completion counts and dates derive from returned progress, not a visitor's browser storage.

Loading keeps data controls disabled. Failure exposes a retry action and the downloadable full outline while project text remains readable. Empty search results explain how to recover. Progress and saving messages use live status regions; the progress bar has a numeric accessible value. A text outline remains available without JavaScript.

### Artwork dialog and accessibility

The native modal dialog presents the same full landscape with descriptive alternative text and an original-image link. It supports a close button, native Escape dismissal and focus restoration to its trigger. A skip link precedes navigation. Decorative SVGs and the icon field are hidden from assistive technology; wordmarks, icon-only controls, search, domain selection and progress have accessible names.

## Do's and Don'ts

### Do

- **Do** preserve the original blog identity assets and use the single landscape recorded in the provenance file.
- **Do** use the current semantic color roles, open reading layout and native research controls.
- **Do** retain keyboard focus, reduced-motion behavior, loading feedback and recoverable failures.
- **Do** keep public progress read-only and local maintenance explicit.

### Don't

- **Don't** replace the signatures, invent another theme, introduce a dashboard card system or add a rotating wallpaper gallery.
- **Don't** present visitor-local checkmarks as official project progress.
- **Don't** apply this page's visual rules to theory sources or alter the original blog through this document.
