---
version: 1
slug: "scripts-render-answer-py"
primary_target: "scripts/render_answer.py"
related_targets: ["assets/xikari-base.css","assets/reader.css","assets/reader.js","scripts/condition_lab.py","assets/condition-lab.css","assets/condition-lab.js","scripts/comparison.py","assets/comparison.css"]
---

# Generated pages

Primary target: `scripts/render_answer.py`

Related targets: `assets/xikari-base.css`, `assets/reader.css`, `assets/reader.js`, `scripts/condition_lab.py`, `assets/condition-lab.css`, `assets/condition-lab.js`, `scripts/comparison.py`, `assets/comparison.css`

Mode: Read for the reading page; Operate for the condition page and the comparison table. Each page is one offline file built by standard-library Python from the reader's own task material. The generator never adds, summarizes or reorders the text it is given; whatever the page draws is computed from that text.

Audience and job: someone who asked the Skill a hard question opens the file it produced. They need to see what kind of page it is and how long, read the central judgment at once, know where they are in a long argument, jump, search, quote a passage back into the conversation, and print.

Constraints: strict Content-Security-Policy with hashed inline style and script, no network, no inline style attributes unless a formula needs them, Chinese and English interface, readable without script, printable.

## Direction contract

THESIS: A generated page is what the route delivers, and it prints its own chart from its own data. The reading page draws the document as a flown track: sections are fixes at their true distances, the reader is the aircraft. It refuses the article-reader default of a title, a hairline and a column, and the earlier quiet monograph in moon-white and indigo.

OWN-WORLD: The chart system of the project page and the handbook: white chart paper, blue-black ink in three strengths, cobalt for structure, magenta for position, sign yellow for the action and the one thing to notice, red for what is refused or blocked. Ruled strips, square frames, no shadows. Solid is sourced or required, dashed is assumed or conditional, dotted is unknown. Heavy numerals are designators; text the document wrote is set in the body sans; quoted material is Song.

STORY: The reader sees what the file is and how long it runs, reads the judgment, sees the whole argument as a route with distances, then reads. At any point they know which fix they are at and how far remains; they jump by fix, see search hits on the route, and carry a passage into a follow-up question.

FIRST VIEWPORT: A 56px bar with the station mark, an ink sign that says where the reader is (the opening, on arrival), search and the yellow follow-up sign. On the sheet: the title at display scale, then one framed plate directly under it: the briefing strip (reading time, length, sections, tables and figures, notes) over the track chart (entry, fixes spaced by length, runway, key, scale) over the dock (current fix, share read, distance to go in yellow). The first paragraph follows at lede size. The fix rack stands on the desk ground at the left and opens with the strip for the opening. At any later scroll depth the same track stands in a strip under the bar with the current fix, the flown fixes, the aircraft, search hits and what remains; on a phone the plate's track runs down the sheet with names beside their fixes.

FORM: Document track plate, candidate 1 of 7 on the grounded list; seed 8c242e3b. Code-led. The strip rack stays as the plate's text twin. Signature interaction: the track is flown by reading. Scrolling moves the aircraft and fills the fixes behind it, a search prints its hits on the track, and choosing a fix flies there.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Sibling pages

The condition page opens with a case field: every computed case is one mark on the plate, a scenario a block, a plan a row, a combination of conditions a column. A mark's line style states its result, the held case carries a magenta ring that travels, and the tables below are the field's text. The comparison table carries its key and its refusal on the plate so the table follows at once; each cell keeps its basis as a tag whose line style carries it (filled is a stated fact, dashed is an assumption, dotted is unknown and stays hatched and unranked); each option carries a letter, and a dimension with a common scale draws its ranked values on a line of its own, where an unknown has no place.

## Reading aids kept

Contents, in-place search, footnote preview and return, stable section anchors, follow-up question from a selection or a section, text size, day and night, print, Markdown download, offline formulas.
