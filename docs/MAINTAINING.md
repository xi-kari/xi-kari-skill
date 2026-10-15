# Maintaining the project page

The introduction is a static site. It reads published JSON files and does not
write to the repository, offer an editor API, or store research completion in a
visitor's browser. The theme preference is the only local preference saved by
the page.

## Published sources

- `data/research-status.json` describes the current manuscript identity and a
  dated research-completion status. `theory.version` is `null` when the source
  does not assign a version. The manuscript baseline, status-confirmation date,
  and page update date are separate fields. An author-confirmed status records
  `delivery.provenance.kind` as `author-confirmation`; its confirmation date is
  not a substitute for the actual completion date of each task.
- `data/research-topics.json` contains the 32 domain titles from the current
  manuscript's appendix D and the 296 preserved historical topic IDs, titles
  and questions. It is a directory, not an evaluation score.
- `data/research-outline.md` is the same directory in a readable download.
- `data/research-progress.json` preserves the historical completion records
  dated 2026-10-01. The page links to this archive but does not use its checkmarks
  to compute current progress. Do not replace those timestamps with today's
  date or reinterpret them as verification of the current theory.
- `data/history/research-status-20261013.json` is the dated earlier delivery
  snapshot. Historical counts and their forward/reverse breakdown stay in that
  archive and are not used to calculate the current status.

The current status covers the 620 follow-up research tasks, from baseline
materials and topic research through domain consolidation and final review.
The page shows all 620 tasks complete. A zero pending count means an empty
`pendingItems` list and a hidden pending section, not a list of old unfinished
tasks. For a status with pending work, name each current pending task.

## Updating the page

1. Review the actual source manuscript and the latest research status or author
   confirmation. Record the status basis in the data; do not infer completion
   from the presence of a manuscript or a successful software test.
2. Edit `research-status.json`. Group totals must sum to `delivery.total` and
   group completed counts to `delivery.delivered`. Completed plus pending must
   equal total. `pendingItems` must enumerate current pending tasks with unique
   IDs and plain-language descriptions, and must be empty when pending is zero.
   Do not invent a new forward/reverse breakdown when updating from a different
   status basis.
3. Update the fallback snapshot in `index.html` to match the same data: dates,
   total progress, named group rows, pending items and scope explanation. This
   keeps the research status readable without JavaScript or a working fetch.
   The script replaces these rows only after checking the JSON's consistency.
4. If the source's domain titles change, update `research-topics.json` and the
   matching outline. Preserve stable topic IDs and original questions unless
   the research directory itself changes.
5. Update capability text in `index.html` together with the repository README,
   and installation guidance with `docs/INSTALL.md`. A release link must name
   the exact published asset. State only the operating systems and capabilities
   actually tested.
6. Check the diff and publish through the repository's configured GitHub Pages
   process. All visitors then receive the same published snapshot.

Public files must not include machine-local paths, personal case material,
private research inventories, scheduler locations, credentials, internal thread
IDs or private receipts. Use an aggregate public snapshot with named work and
its meaning. Keep installation artifacts and research-run outputs outside the
website assets.

## Handbook

The concept lessons, real cases and full-text reading site are authored in
`website/` and built to `docs/handbook/`. The installed Skill is selected by
`skill-package.json` and does not include this website.

Run `npm ci --prefix website`, then `npm run build --prefix website` to generate
the static handbook. The build reads the unchanged canonical manuscript in
`source/`, checks its identity, splits it into reading pages and preserves the
complete Markdown and Word downloads. To supply a missing Word download, run
`python website/scripts/build_theory.py --docx <path>` with the matching edition.

The source, concept lessons and case explanations have separate responsibilities.
Keep original text unchanged; cite actual primary sources for real case facts.
Explanatory diagrams and interactive teaching models must retain their assumptions.
New case research belongs outside the repository until its content is ready to
be used. Do not publish private research inventories or prompt handoffs with
the static site.

The handbook has its own VitePress theme in `website/.vitepress/theme/`
(layout, book index, outline, lesson modules, teaching models, page-turn and
theme transitions); its design is recorded in `.impeccable/surfaces/handbook.md`.
The display face is Zhuque Fangsong (SIL OFL 1.1), cut into unicode-range WOFF2
slices by `python website/scripts/build_fonts.py --font <ZhuqueFangsong-Regular.ttf>`
(needs `fonttools` and `brotli`); rerun it only when lessons bring in many rare
characters. The slices and `styles/fonts.css` are committed.

Section explanations live in `website/content/section-lessons.json`, keyed by
the stable reading unit. `website/LESSONS.md` lists every field and the module it
draws; the build attaches each page's lessons to that page only. The generator recreates `reading-units.json` from the
canonical source and accepts all 412 numbered and unnumbered units. Each
explanation follows its own original text; a parent section's introduction
precedes the original child sections. Merge reviewed `sections.json` results
into the matching keys and keep all substantive text in renderable fields.
Search includes those explanations and resolves them to the source section.

Verify source coverage with `python -m unittest discover -s tests -p test_handbook_source.py`.
The full build checks page links. Before publication, also check native static
URLs, section anchors, Chinese search, download identities, diagrams, teaching
interactions, desktop/mobile layouts and both themes in a browser.

## Project page verification

Check the data arithmetic, unique domain/topic/pending IDs, source-domain title
alignment, release links, static fallback consistency and absence of obsolete
editor endpoints. Preserve the original artwork and the 96-mark desktop /
48-mark mobile icon field.

On the actual published page, check desktop and mobile together: light/night
theme, reduced motion, keyboard focus, copy success and failure feedback,
research search and empty results, expand/collapse, domain jumps, source links,
progress labels, completion state and any current pending tasks. Simulated DOM checks can exercise
logic but do not replace actual layout and browser inspection. If data loading
fails, the fallback research snapshot remains visible and the topic directory
offers retry and a text download.
