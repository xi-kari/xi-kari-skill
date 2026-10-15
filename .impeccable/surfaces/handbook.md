---
version: 2
slug: handbook
primary_target: website/index.md
related_targets: [website/.vitepress/theme/Layout.vue, website/.vitepress/theme/styles/tokens.css, website/.vitepress/theme/components/lesson/SectionLesson.vue, website/LESSONS.md, docs/handbook/index.html]
---

# Xikari handbook

Primary target: `website/`

Related targets: `docs/handbook/`

Mode: Read.

Purpose: Help readers understand the entire original work through section-by-section reading, with explanations, diagrams and sourced cases immediately following the corresponding original section.

North star: "One set of drawings." Each part of the book is a sheet in a drawing set. The original text is printed on the sheet in Prussian ink; explanations are tracing-paper overlays laid on top; structural art is a cyanotype print. Night mode turns the whole set into a blueprint.

Composition: The home page opens with a single cyanotype print: the book title in Fangsong, an animated structure drawing that re-forms into four arrangements the book names (structure object, local and whole chain, effective feedback, cross-scale transformation), and a drawing title block with title, author, text date and structure. Below it: the opening paragraph quoted exactly, the sixteen parts and four appendices as a four-column drawing index, every written lesson, real cases and downloads. Reading pages use a custom VitePress theme: a book index on the left (sheet numbers, collapsible groups, yellow dots where lessons exist), the sheet in the middle inside a double drawing frame with zone ticks, and the page outline with reading settings on the right. Theory pages open with a title block (number, group, length, lessons, a small structure sigil generated from the sheet number). Section numbers hang in the margin; part titles carry their prefix as a kicker.

Lessons: Each lesson is a tracing-paper sheet (faint grid, drafting tape, detail-callout bubble with the section number). Every module has its own drafting convention: steps as a dimension chain, distinctions as a section cut with a yellow ≠ seam, teaching scenarios dashed (assumed), real cases solid with a folded corner and a separate source box (sourced), limits behind caution tape, questions as numbered checks with expanding answers. Field reference: `website/LESSONS.md`. Each page carries only its own lessons; the site ships a small index of where lessons are.

Type: Zhuque Fangsong (SIL OFL 1.1, subset into unicode-range slices by `website/scripts/build_fonts.py`) for titles, lesson headings and an optional Fangsong reading mode; the system sans stack for body text and interface. Fangsong is the lettering of Chinese engineering drawings, which is why it carries the titles.

Color: cool paper `#fbfcfc` on a drafting table `#e7ebee`, Prussian ink `#13233f`, cyanotype blue `#1f4a8a` / print field `#1c4279`, highlighter yellow `#ffd447` for the one thing to notice. Night: table `#0a1630`, sheet `#0f2244`, ink `#e6eef9`, links `#a3c4ff`.

Motion: Motion answers the reader. Moving between pages turns the sheet (View Transitions: the old sheet slides out as it fades, the new one slides in from the side it lies on in the book; top bar, index and outline stay still; the sheet number rolls like an odometer; the index marker glides). The theme switch exposes the blueprint from the button outward. Source-only reading lifts the tracing paper off and folds it away. Models animate the connection that just changed. Figures zoom from their place. The home print develops once on arrival and its structure drawing pauses when out of view. Reduced motion removes all of it.

Interaction: Search (Ctrl/⌘ K or /), section links, collapsible index, outline scroll-spy, reading settings that persist (source only, text size, Fangsong body), copy link, figure zoom, three interactive teaching models. Keyboard use, narrow screens (index drawer, outline bottom sheet), reduced motion, print and dark mode keep full content.

Content authority: Source text is generated from the authoritative manuscript and never edited by the theme; heading numbers are wrapped in spans for layout only. Editorial pages link their source sections. Teaching examples are identified; historical reports are not relabeled as current analyses.
