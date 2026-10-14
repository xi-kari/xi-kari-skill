# Maintaining the project page

The introduction is a static site. It reads published JSON files and does not
write to the repository, offer an editor API, or store research completion in a
visitor's browser. The theme preference is the only local preference saved by
the page.

## Published sources

- `data/research-status.json` describes the current manuscript identity and a
  dated research-delivery snapshot. `theory.version` is `null` when the source
  does not assign a version. The manuscript baseline, research snapshot date,
  and page update date are separate fields.
- `data/research-topics.json` contains the 32 domain titles from the current
  manuscript's appendix D and the 296 preserved historical topic IDs, titles
  and questions. It is a directory, not an evaluation score.
- `data/research-outline.md` is the same directory in a readable download.
- `data/research-progress.json` preserves the historical completion records
  dated 2026-10-01. The page links to this archive but does not use its checkmarks
  to compute current progress. Do not replace those timestamps with today's
  date or reinterpret them as verification of the current theory.

The delivery snapshot counts distinct tasks with delivered research material.
It does not measure the truth of the theory, independent empirical support, or
completion of the final source and semantic review. Keep the remaining task
names visible, including quality review and final synthesis tasks.

## Updating the page

1. Review the actual source manuscript and research handoff records. Publish
   only supported counts and status; do not infer completion from the presence
   of a manuscript or a successful software test.
2. Edit `research-status.json`. Group totals must sum to `delivery.total` and
   group delivered counts to `delivery.delivered`. Delivered plus pending must
   equal total. Forward plus reverse minus overlap must equal the distinct
   delivered count. `pendingItems` must enumerate all pending tasks with unique
   IDs and plain-language descriptions.
3. Update the fallback snapshot in `index.html` to match the same data: dates,
   total progress, named group rows, pending items and scope explanation. This
   keeps the research status readable without JavaScript or a working fetch.
   The script replaces these rows only after checking the JSON's consistency.
4. If the source's domain titles change, update `research-topics.json` and the
   matching outline. Preserve stable topic IDs and original questions unless
   the research directory itself changes.
5. Update release, installation and capability text in `index.html` together
   with the repository README. A release link must name the exact published
   asset. State only the operating systems and capabilities actually tested.
6. Check the diff and publish through the repository's configured GitHub Pages
   process. All visitors then receive the same published snapshot.

Public files must not include machine-local paths, personal case material,
private research inventories, scheduler locations, credentials, internal thread
IDs or private receipts. Use an aggregate public snapshot with named work and
its meaning. Keep installation artifacts and research-run outputs outside the
website assets.

## Verification

Check the data arithmetic, unique domain/topic/pending IDs, source-domain title
alignment, release links, static fallback consistency and absence of obsolete
editor endpoints. Preserve the original artwork and the 96-mark desktop /
48-mark mobile icon field.

On the actual published page, check desktop and mobile together: light/night
theme, reduced motion, keyboard focus, copy success and failure feedback,
research search and empty results, expand/collapse, domain jumps, source links,
progress labels and readable pending tasks. Simulated DOM checks can exercise
logic but do not replace actual layout and browser inspection. If data loading
fails, the fallback research snapshot remains visible and the topic directory
offers retry and a text download.
