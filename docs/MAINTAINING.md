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

The pages the Skill generates carry their own cut of the same heavy sans, kept
with the Skill in the repository's `assets/fonts/` and inlined into every page:
`xk-display.woff2` for the Chinese interface and `xk-display-latin.woff2` for
the English one. It holds numerals, Latin, the words a heading number is made
of, and the strings each generator returns from `display_strings()`; text a
document wrote is set in the reader's own fonts. After changing one of those
strings, rebuild and check:

```powershell
python website/scripts/build_output_fonts.py --sans <NotoSansSC-VF.ttf>
python website/scripts/build_output_fonts.py --check
```

`assets/provenance.json` records every raster the page ships. The output
screenshots (`outputs-*.png`, the same files as in `.github/readme/`) and
`social-card.png` (the page's own briefing strip and plan view at 1200 by 630)
are taken together with the README figures below, and the script updates their
recorded hashes. The plan view,
profile view, compass rose and wind rose are drawn in the browser from the
page's own data and need no image files.

## README figures

The two READMEs show figures from `.github/readme/`, each in a day and a night
printing:

| Files | What they show |
| --- | --- |
| `hero-*.png` | the project page's briefing strip and plan view |
| `hero-en-*.png` | the same view with its words set in English, for `README.en.md` |
| `routes-*.png`, `routes-en-*.png` | the eight routes against the eleven modules, drawn by `src/routes.html` |
| `handbook-*.png` | the station band of the handbook's home page |
| `outputs-*.png` | the three generated pages, built by the packaged tools and framed by `src/outputs.html`; also used by the project page |

`src/capture.cjs` takes every one of them, together with the project page's
social card. It writes an origin note into each file, writes nothing unless all
requested captures succeed, and updates the hashes in `assets/provenance.json`.
For the generated pages it runs `render_answer.py` on Part 1 of the source
text, and `condition_lab.py` and `comparison.py` on the bundled examples, in a
temporary folder.

The figures are taken on Windows, in an installed Google Chrome that the
script drives through `playwright-core` (Playwright's `chrome` channel;
`playwright-core` brings no browser of its own). `src/routes.html` and the
labels of `src/outputs.html` are set in an installed Noto Sans SC (the variable
`NotoSansSC-VF.ttf` from noto-cjk, SIL OFL), and the script stops if it is
missing; the frame's file names use Cascadia Mono, or Consolas without it. The
project page's body text and the generated pages use their own font stacks,
which the script reports. Retaking on another system changes the type.

Once, from the repository root, install the page-test and handbook packages
and build the handbook (the build rewrites `docs/handbook/`; skip it when the
committed build is current, because the preview serves that build):

```powershell
npm ci --prefix tests/dom --ignore-scripts --no-audit --no-fund
npm ci --prefix website --ignore-scripts --no-audit --no-fund
npm run build --prefix website
```

Then serve the project page in one terminal and the built handbook in another:

```powershell
python -m http.server 4321 --bind 127.0.0.1 --directory docs
```

```powershell
npx --prefix website vitepress preview website --port 4173
```

and take the figures in a third:

```powershell
node .github/readme/src/capture.cjs "$PWD/tests/dom/node_modules/playwright-core"
```

`--only hero`, `hero-en`, `handbook`, `routes`, `outputs` or `card` retakes a
single figure. On one machine repeated runs give identical files.

Retake after the opening of either site changes, after a route or module
changes in `SKILL.md` (update `src/routes.html` with it), and after
`render_answer.py`, `condition_lab.py`, `comparison.py`, their assets or Part 1
of the source change. The hero figures leave out the version, the baseline date
and the download signs, so a release alone needs no retake. The English hero
takes its words from the table in `capture.cjs`; the script stops when the
page shows a phrase the table does not cover, or when a phrase it replaces
whole has changed. Look at the new files before committing: a longer label can
run into a line of the drawing.

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
the stable reading unit; reviewed supplements in
`website/content/lesson-overrides.json` replace whole fields of an imported
lesson or supply the whole lesson for a unit the import lacks. `website/LESSONS.md` lists every field and the module it
draws; the build attaches each page's lessons to that page only. The generator recreates `reading-units.json` from the
canonical source and accepts all 415 numbered and unnumbered units; once the
supplements apply, every unit has a lesson. Each
explanation follows its own original text; a parent section's introduction
precedes the original child sections. Merge reviewed `sections.json` results
into the matching keys and keep all substantive text in renderable fields.
Search includes those explanations and resolves them to the source section.

Verify source coverage with `python -m unittest discover -s tests -p test_handbook_source.py`.
The full build checks page links. Before publication, also check native static
URLs, section anchors, Chinese search, download identities, diagrams, teaching
interactions, desktop/mobile layouts and both themes in a browser.

## English reference edition

`source/en/` holds the English reference edition of the manuscript and its
manifest. The Chinese manuscript in `source/` remains the only theory authority;
the edition serves English terminology, quotation and English readers, and the
skill reads it only as `references/english.md` describes.

The edition is generated, not edited by hand. It is built from the page-by-page
translation, which is maintained outside this repository:

```powershell
python scripts/build_english_edition.py --from <translation directory>
python scripts/build_english_edition.py --check
```

The translation directory holds `source-manifest.json`, the Chinese page
snapshots, the English pages and `termbase.csv`. The build refuses a translation
made from Chinese text other than `source/`, omits the Chinese glosses that the
web pages place after terms, gives the definitional tuples in English while
keeping the Chinese in translator's notes, turns links between web pages into
in-book anchors, prefixes each page's translator's notes, and regenerates
`references/glossary-en.md` from the termbase.

`--check` only reads. It verifies the edition's bytes against its manifest, that
the manifest translates the current Chinese source, and that every section ID,
part anchor and paragraph block aligns with the Chinese text; CI runs it. When the
Chinese source changes, the check fails until the affected passages of the
translation are revised and the edition is rebuilt. Rebuilding also changes the
English edition hash recorded in the install manifest.

## Project page verification

Check the data arithmetic, unique domain/topic/pending IDs, source-domain title
alignment, release links, static fallback consistency and absence of obsolete
editor endpoints. Check the route table and module list against `SKILL.md`, the
quotation and part titles against the manuscript, font coverage and the
recorded asset hashes; `tests/test_project_page.py` covers each of these.

On the actual published page, check desktop and mobile together: day/night
theme, reduced motion, keyboard focus, the eight questions and each condition
switch, the flown route in the wide and the narrow plan view, the host switch,
copy success and failure feedback, research search and empty results,
expand/collapse, domain jumps, source links, progress labels, completion state
and any current pending tasks. Simulated DOM checks can exercise
logic but do not replace actual layout and browser inspection. If data loading
fails, the fallback research snapshot remains visible and the topic directory
offers retry and a text download.
