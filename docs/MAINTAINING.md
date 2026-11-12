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
6. Keep the route table and the module list identical to the routing and module
   tables in `SKILL.md`. They are also the data the page's drawings read: each
   route row lists its modules in order in `data-legs` (a trailing `?` marks a
   module used only when needed, `data-supplement` names modules added when
   necessary, `data-from` names the routes whose result it continues), and each
   module item carries its code, its short chart label and any named handoff
   file. The quoted sentence and the twenty part titles come from the
   manuscript word for word.
7. Check the diff and publish through the repository's configured GitHub Pages
   process. All visitors then receive the same published snapshot.

Public files must not include machine-local paths, personal case material,
private research inventories, scheduler locations, credentials, internal thread
IDs or private receipts. Use an aggregate public snapshot with named work and
its meaning. Keep installation artifacts and research-run outputs outside the
website assets.

## Page fonts and images

Headings, signs and plaques are set in a heavy sans and the quoted source text
in Song. Both are subsets of Noto Sans SC and Noto Serif SC (SIL OFL 1.1) cut to
the characters `index.html` and `404.html` set in them, so neither page makes an
external font request. After changing text inside an element whose class list
contains `display`, `sign`, `plaque` or `song` on either page, rebuild them:

```powershell
python website/scripts/build_page_fonts.py --sans <NotoSansSC-VF.ttf> --serif <NotoSerifSC-VF.ttf>
python website/scripts/build_page_fonts.py --check
```

Building needs `fonttools` and `brotli`; `--check` only reads and reports
characters the committed subsets do not cover. `assets/fonts/source.json`
records each subset's source version, hash and covered characters, and
`assets/fonts/OFL.txt` carries the licence.

`assets/provenance.json` records every raster the page ships. The output
screenshots are copies of `.github/readme/outputs-light.png` and
`outputs-dark.png`; replace both places together when the tools' pages change.
`social-card.png` is a capture of the page's own briefing strip and plan view at
1200 by 630; retake it after the opening changes. Update the recorded hashes
whenever a file changes. The plan view, profile view, compass rose and wind rose
are drawn in the browser from the page's own data and need no image files.

## Not-found page

`404.html` at the publishing root is what the host returns for every missing
address under the project. It shares `assets/project.css`, links back to the
project page and the handbook, and uses root-relative `/xi-kari-skill/` URLs
because it is served at any depth. A missing address inside
`/xi-kari-skill/handbook/` is handed to the handbook's own not-found page
(`handbook/404.html`, written by the handbook build) with the address kept. The
file is written by hand; the handbook build does not touch it.

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
It shares the project page's chart vocabulary: the same paper, ink, cobalt,
magenta and sign yellow, the source text drawn as a compass rose, and every
sheet of the book handled as a ruled strip.

The display face is one Noto Sans SC subset at weight 900 (SIL OFL 1.1), built
by `python website/scripts/build_fonts.py` (needs `fonttools` and `brotli`;
`--font` names the variable font when it is not installed). It holds the
characters of the theme's own strings, the book index and every first- and
second-level heading; lesson text, body text and quotations use system fonts.
Rerun it after headings, index titles or theme strings change, and use
`--check` to list uncovered characters without writing. The subset,
`fonts/source.json` and `styles/fonts.css` are committed; the licence is
`website/public/licenses/NotoSansSC-OFL.txt`. The home page's baseline date is
read from `docs/data/research-status.json`, the same record the project page
uses.

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
editor endpoints. Check the route table and module list against `SKILL.md`, the
quotation and part titles against the manuscript, font coverage and the
recorded asset hashes; `tests/test_project_page.py` covers each of these.

On the actual published page, check desktop and mobile together: day/night
theme, reduced motion, keyboard focus, the seven questions and each condition
switch, the flown route in the wide and the narrow plan view, the host switch,
copy success and failure feedback, research search and empty results,
expand/collapse, domain jumps, source links, progress labels, completion state
and any current pending tasks. Simulated DOM checks can exercise
logic but do not replace actual layout and browser inspection. If data loading
fails, the fallback research snapshot remains visible and the topic directory
offers retry and a text download.
