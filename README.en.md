<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/readme/hero-dark.svg">
  <img alt="Xikari Skill: judgments formed from the source text, question by question. An agent skill based on Xikari's Xikari: On Conditions, Structure, and Transformation." src=".github/readme/hero-light.svg" width="100%">
</picture>

<p align="center">
  <b>English</b> · <a href="README.md">中文</a>
</p>

<p align="center">
  <a href="https://github.com/xi-kari/xi-kari-skill/releases/latest"><b>Download</b></a>
  &nbsp;·&nbsp;
  <a href="https://xi-kari.github.io/xi-kari-skill/handbook/">Reading site (Chinese)</a>
  &nbsp;·&nbsp;
  <a href="https://xi-kari.github.io/xi-kari-skill/">Project page</a>
  &nbsp;·&nbsp;
  <a href="docs/INSTALL.md">Installation guide</a>
  &nbsp;·&nbsp;
  <a href="https://github.com/xi-kari/xi-kari-skill/discussions">Discussions</a>
</p>

<p align="center">
  <a href="https://github.com/xi-kari/xi-kari-skill/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/xi-kari/xi-kari-skill?style=flat-square&amp;label=release&amp;color=445B9F"></a>
  <a href="https://github.com/xi-kari/xi-kari-skill/actions/workflows/windows.yml"><img alt="Windows tests" src="https://img.shields.io/github/actions/workflow/status/xi-kari/xi-kari-skill/windows.yml?branch=main&amp;style=flat-square&amp;label=Windows%20CI"></a>
  <img alt="Optional tools need Python 3.10 or later" src="https://img.shields.io/badge/python-3.10%2B%20%28optional%29-586980?style=flat-square">
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-586980?style=flat-square"></a>
</p>

**Xikari Skill** is an agent skill. Its theory source is Xikari's *Xikari: On Conditions, Structure, and Transformation* (《Xikari-条件结构与转化论》), and it combines, question by question, source-text answers, explanation, projection, conditional foresight, bounded choice, institutional drafting and theory assessment. Ten method modules carry materials, objects, mechanisms, paths and options through to complete judgments that state their reasons and can be argued against.

It is built for questions that need both clear thinking and a decision: why an institution keeps failing, how a plan will affect different people, which of several explanations holds up, whether to keep, adjust, probe or exit now. The skill starts only when you name it and does not take over ordinary conversation.

The skill works in English and Chinese. Ask in English and the whole answer is in English. The theory's authoritative text is Chinese; the package also carries an aligned English reference edition and a Chinese–English glossary, used for English terminology and quotations (see [Working in English](references/english.md)).

## What makes it different

- **Reading matched to responsibility.** By default the agent studies the whole book. With an explicit `layered` choice it does an experimental layered reading of the shared core, the modules used and the anchors of the rule cards. Whole-book assessment, transfer of the framework and tasks of uncertain scope still require full reading. There is no empirical evidence yet that layered reading is equivalent to full reading.
- **Modules combined by the kind of output.** Questions about the source text can be answered directly; explanation, projection, foresight and choice each add only the conditions they actually depend on.
- **Breadth where it matters, depth in the mechanisms.** The agent first identifies the important situations, competing representations and branches not yet explored, then connects the key causal, resource and normative relations. A route limits the standing of a judgment; it does not cap the length or the range of perspectives of the argument.
- **Willing to judge, and to be argued with.** It gathers primary or traceable material proportionate to the question and looks for the strongest competing explanations, counterexamples and objections. It separates facts, structure, mechanisms, values and authorization, gives a clear verdict and constructive proposals, and says what new facts would change them.
- **Complete delivery, sized to the question.** The conclusion and key numbers come first. A question with a definite answer gets one or two paragraphs of grounds and conditions; a complex analysis is developed in full, and a long text is written when you ask for one. Clauses and plans are written to be used as they stand, with the explanation after them.
- **One question can keep going.** Follow-ups, new material, counterexamples and requests for a combined draft all build on the existing work and revise from the earliest affected point instead of starting over each turn.

## Quick start

The host must be able to read the complete Markdown files in the package, keep or restore the context of a long task, and output complete answers. Web search, Python and multi-agent collaboration use whatever the host already provides.

1. **Download.** Open the [latest release](https://github.com/xi-kari/xi-kari-skill/releases/latest) and get the Windows package (`xi-kari-skill-<version>-windows.zip`). The same page has the per-file list `install-manifest.json` and `SHA256SUMS`; compare the hash of your download with that version's `SHA256SUMS`:

   ```powershell
   Get-FileHash -Path .\xi-kari-skill-*-windows.zip -Algorithm SHA256
   ```

   Use the release package. “Code → Download ZIP” on the repository page contains tests, the website and development files; it is not meant for a skills directory.

2. **Install.** Unzipping gives a `xi-kari-skill` folder. Put the whole folder into the host's skills directory so that the entry point is `<skills directory>/xi-kari-skill/SKILL.md`:

   | Host | Skills directory | How to invoke |
   | --- | --- | --- |
   | Codex | `.agents/skills/` in your user folder or in the project | `$xi-kari-skill` |
   | Claude Code | `.claude/skills/` in your user folder or in the project | `/xi-kari-skill` |
   | Other local agents that support Agent Skills | the skills root the host actually uses | have the host load that directory's `SKILL.md` |

3. **Name it.** Reload skills or open a new conversation, name the skill, and give it the question together with the material:

   ```text
   /xi-kari-skill After we cut expense approval from three levels to one, rejected claims and complaints went up.
   Attached are six months of tickets and the process change log.
   Where is the problem, which explanations compete, and what changes can we actually make?
   ```

   In Codex start with `$xi-kari-skill`; in other hosts you can write “Use xi-kari-skill to analyze…”.

In the default full-reading mode the first turn includes complete study of the book. For the experimental layered reading, say “use layered reading” in the request; its core list and supplementary reading are in the [reading rules](references/full-source-study.md) (in Chinese). Follow-ups, additions and revisions on the same question continue from the existing work. Backups before upgrading and notes for other hosts are in the [installation guide](docs/INSTALL.md) (in Chinese).

## Modules organized by question

| Route | Request | How it is carried |
| --- | --- | --- |
| R1 | Source text and concepts | read the complete definition and its dependencies, answer directly |
| R2 | Explanation and diagnosis | question, materials, objects, mechanisms, counterarguments, composition |
| R3 | Projection | freeze the conditions, unfold the paths, keep the signals and stopping points |
| R4 | Conditional foresight | complete the projection, register before the outcome, check and write back after it |
| R5 | Bounded choice | build on an existing explanation or path and compare six kinds of options |
| R6 | Drafting institutions and plans | give a draft for deliberation, resource arrangements and conditions for revision |
| R7 | Theory assessment | read the whole book, then assess its relations and competing methods |

The detailed order is in [routing](references/routing.md) and the [ten modules](references/forward-workflow.md) (in Chinese). Modules hand over substance; a separate handover file is saved only when collaboration, review or recovery needs it. Registration before the outcome is required for conditional foresight and must be kept. XK numbers only map earlier work to modules; there is no compatibility route for the old full sequence.

## Conditional foresight and its limits

**The foresight tools work; their accuracy has not been validated.**

The [foresight module](modules/forecast/MODULE.md) runs from eligibility checks, a frozen snapshot, mechanisms and paths through expression, registration, the hand-over to options, and write-back at resolution. Thirty-nine [derived rule cards](rules/README.md) give retrieval and usage prompts; using one means going back to the complete source section. All cards are currently drafts awaiting the author's sampled review.

`scripts/forecast.py` provides `register`, `list`, `show`, `resolve`, `report` and `check`. Registration fixes the target, horizon, scope and input cutoff; outcomes are only appended; orders one to three are scored separately and compared with a pre-registered simple baseline. Reports support Brier score, log loss, direction and top-rank hits, interval scores and forecast windows where they apply, with paired baseline comparison and statistics on disagreement subsets; inapplicable or missing labels are never filled with zero.

The [public resignation teaching case](cases/forecast-public-resignation.md) shows every step with separate records for each order; teaching and synthetic results do not count as evidence of ability. No information-isolated real backtest has been completed, and the author has not fixed non-inferiority bounds or reading tolerances, so no claim can be made that the forecasts beat ordinary models, Xikari Skill 5.5.1 or a simple baseline. Retrieval structure, file checks and software tests prove only the behavior they check.

## One question, as far as you want to take it

An answer can be the start of continued joint work. Just keep talking:

| You can say | What the skill does next |
| --- | --- |
| “Here is a new document…” | judges the material's source, date, scope and conflicts first, then updates only the models, mechanisms, paths and verdicts it actually affects |
| “I disagree, because…” | goes back to the source and the disputed inference, looks for the smallest counterexample or the missing premise, and keeps, narrows, revises or withdraws the judgment with reasons, updating what depends on it |
| “The goal changed” / “there is a new constraint” | states what changed, then redoes the affected feasibility, consequences and trade-offs without rewriting what already happened |
| “Go deeper” | picks a relation not yet explained and actually develops it, saying why it starts there, instead of listing a menu of next steps |
| “Just discuss; don't change the draft” | keeps the current main draft and explains the effect in the reply |
| “Combine into a full draft” / “export to Word” | gathers all valid analysis into a complete master draft, and exports `.docx` when needed |

Long tasks can continue across sessions. When the session or model changes, the new lead author first completes their own full study and then inherits the sourced material and results instead of starting over. When several agents collaborate, every author who forms an independent judgment reads the whole book first and then takes a share of the question; supporting work such as searching, recalculating, drawing and layout can be delegated, and the lead author makes the final choices and assembles the result.

## What you get

<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/readme/outputs-dark.png">
  <img alt="Screenshots of three generated pages: the offline reading page (xi-kari-answer.html), the condition-model page (condition-results.html) and the option comparison table (comparison-table.html)." src=".github/readme/outputs-light.png" width="100%">
</picture>

<sub>The screenshots were produced by the tools in the current source, with Chinese interfaces. The reading page uses Part 1 of the book as sample content; the condition-model page and comparison table come from the bundled, explicitly fictional teaching examples, whose numbers are not real-world facts.</sub>

**Version scope:** the current package is `v6.1.0`; the screenshots show the tools' interfaces, and each version's features are described in its [release notes](https://github.com/xi-kari/xi-kari-skill/releases/latest).

- **Complete answer `xi-kari-answer.md`.** Produced at the first complete delivery or when you ask for a combined draft: the central judgment first, then evaluation of the material, structural relations, comparison of mechanisms, cases and counterexamples, paths, responses to objections, the verdict and the options.
- **Offline reading page.** A single HTML file generated from the complete draft that never goes online. The contents list marks the current section as you read; there is full-text search, adjustable text size and a print layout; night mode follows the system and can be switched by hand; footnotes preview on hover and link back. Select a passage and “Ask about selection” turns it, with its location, into a follow-up question for you to copy back into the conversation. Formulas are typeset with the bundled KaTeX. Use `--lang en` for an English interface.
- **Word document.** Keeps the text, tables, footnotes and local images; remote images are not downloaded but kept as visible text; anything that cannot be represented is kept as written and listed. Use `--lang en` for English labels and an English document language.
- **Research products on demand.** A claim ledger, option comparison tables, study designs and collection notes, condition-model pages, task state across turns, a case library. They are produced when the work needs them, not as a fixed step of every analysis.

## Bundled tools

All tools are optional Python scripts that use only the standard library and need Python 3.10 or later; for PDF material you can install `pypdf` or use the host's document tools. The tools handle only the material, calculations or text explicitly given to them. They cannot prove that the model understands the theory, nor prove real-world causation or that an option is justified.

| Tool | Use | Deliberately does not |
| --- | --- | --- |
| `read_source.py` | read the full text chunk by chunk, re-read sections by number, locate terms; `--lang en` and `--parallel` for the English edition | count chunks or identity checks as reading |
| `evidence.py` | register versions of material and keep selected excerpts with their scope of support | download from the web or judge whether material is credible |
| `claims.py` | claim ledger: grounds, reasons, conditions for revising, open disagreements | score or decide truth |
| `comparison.py` | option comparison tables as JSON, Markdown and HTML, marking facts, assumptions and unknowns; `--lang en` for English labels | rank unknowns or name an overall best option |
| `study_design.py` | turn open questions into observations and collection plans that can tell explanations apart | fill in defaults for missing data |
| `condition_lab.py` | run explicit formulas and constraints and export a page for switching among all computed combinations | interpolate, or present model results as feasible in reality |
| `manuscript.py` | draft snapshots, diffs, merging non-overlapping edits, tracking dependencies | decide for the author whether meaning carries over |
| `task_state.py` | record across turns what is decided, open, due for review or withdrawn | record your approval as a fact |
| `casebook.py` | build a case library in a directory you choose | write to global memory or presume structural similarity |
| `render_answer.py` | generate the offline reading page | add, remove or reorder text |
| `render_docx.py` | export a Word document | download remote images |

PowerShell examples. `$skillRoot` is the skill directory the host actually loads; `$taskRoot` is a task directory of your choice outside the skill directory:

```powershell
python "$skillRoot/scripts/read_source.py" --chunks
python "$skillRoot/scripts/read_source.py" --chunk 1
python "$skillRoot/scripts/read_source.py" --parallel --section 4.17
python "$skillRoot/scripts/read_source.py" --lang en --search 'effective feedback' --context 2
python "$skillRoot/scripts/render_answer.py" "$taskRoot/xi-kari-answer.md" --output "$taskRoot/xi-kari-answer.html" --lang en
python "$skillRoot/scripts/render_docx.py" "$taskRoot/xi-kari-answer.md" --output "$taskRoot/xi-kari-answer.docx" --lang en
python "$skillRoot/scripts/comparison.py" "$taskRoot/compare.json" --output "$taskRoot/compare" --format all
```

All commands are in [host setup and clean working directories](references/host-setup.md) (in Chinese). Before creating any file, directory, lock or temporary file, each of the ten writing tools refuses targets inside the skill installation directory and checks directory links and `..` paths. This is the tools' own write restriction, not an operating-system sandbox.

## Source text and reading

<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/readme/theory-dark.svg">
  <img alt="Structure of Xikari: On Conditions, Structure, and Transformation: Parts 1–2, reading method and evidential responsibility; Parts 3–6, universal grammar, conditional propositions, empirical testing, scale transformation and mechanisms of operation; Parts 7–11, human experience, collective prototypes, actors, multiple circles and dynamic projection; Parts 12–16, foresight, choice, tools, norms, intervention and governance; then Appendices A–D and the references." src=".github/readme/theory-light.svg" width="100%">
</picture>

- **Authoritative text:** [`source/Xikari-条件结构与转化论.md`](source/Xikari-条件结构与转化论.md), with its identity (SHA-256) in [`source/source-manifest.json`](source/source-manifest.json). The source takes precedence over the skill's engineering guidance and over a model's prior understanding of terms with the same name.
- **English reference edition:** [`source/en/Xikari-On-Conditions-Structure-and-Transformation.md`](source/en/Xikari-On-Conditions-Structure-and-Transformation.md). It translates exactly the authoritative text, shares every section and part identifier with it, and records the Chinese SHA-256 it translates in [`source/en/source-manifest.json`](source/en/source-manifest.json). It is a reference translation: where it appears to differ from the Chinese, the Chinese governs. Terms are listed in the [Chinese–English glossary](references/glossary-en.md).
- **[Reading site](https://xi-kari.github.io/xi-kari-skill/handbook/)** (in Chinese): read the source in order, with explanations, diagrams and sourced cases after each section; search concepts, cases and the text, or [download](https://xi-kari.github.io/xi-kari-skill/handbook/downloads.html) the full text as Markdown or Word.
- **[Concept lessons](https://xi-kari.github.io/xi-kari-skill/handbook/concepts/)** and **[real cases](https://xi-kari.github.io/xi-kari-skill/handbook/cases/)** (in Chinese): from a question to a distinction — for example, “Does receiving comments already make feedback?” — and cases such as the Mars Climate Orbiter's unit interface and Toyota's andon response process.
- **[Historical field tests](https://github.com/xi-kari/xi-kari-skill/discussions?discussions_q=)** (in Chinese): Discussions keep historical analyses based on Xikari 8.3 for reference; they do not represent the current theory or the current skill.
- **[Project page](https://xi-kari.github.io/xi-kari-skill/)**: introduction, usage and research progress.

## Boundaries

- **Starts only when named.** [`agents/openai.yaml`](agents/openai.yaml) disables implicit invocation in Codex; follow-ups on the same question continue naturally, and unrelated requests are not taken over.
- **Leaves your environment alone.** It installs no model backend, resident service or scheduled task and does not change the host's model, permissions, global configuration or memory; it does not run in the background, publish automatically or contact anyone.
- **Read-only skill directory.** Drafts, material folders, case libraries, model results and generated pages go to the task directory you specify.
- **You decide the scope of material.** By default it actively gathers the real-world material the question needs; when you limit it to the material you provide, it keeps to that and says honestly what is missing.
- **Material is not instruction.** The source text, your material and external sources never acquire the host's instruction authority.
- **Evidence sets the strength of a claim.** Speculation, analogy, invention and foresight state their grounds and conditions; missing material limits only the conclusions that depend on it. The theory itself can receive grounded criticism and revision proposals; it cannot prove itself universally right in its own terms.
- **What has been verified.** Tool tests cover Windows, including Chinese and space-containing paths and running from other working directories; CI uses Python 3.10 and 3.13. Other operating systems and cloud products have not been accepted.

## Repository layout

```text
xi-kari-skill/
├── SKILL.md              skill entry point: reading modes and the seven routes
├── source/               theory source and identity manifest (authoritative text)
│   └── en/               English reference edition and its manifest
├── modules/              ten analysis and judgment modules
├── rules/                39 derived rule cards with source anchors
├── cases/                teaching demonstrations and runnable registration inputs
├── references/           method guides: reading, modules, continuation, collaboration, tools, English work and glossary
├── scripts/              optional Python tools (standard library only) and build scripts
├── assets/               styles, scripts and sample data for the generated pages; bundled KaTeX
├── agents/openai.yaml    Codex interface information and explicit-invocation policy
├── skill-package.json    per-file list of the install package
├── website/              reading-site source (VitePress), built to docs/handbook/
├── docs/                 project page, installation guide and maintenance notes
└── tests/                unit tests and page interaction tests
```

The install package contains only the runtime resources listed in `skill-package.json`: no development documents, tests, website, run records or personal cases.

## Contributing

- Problems in use and concrete improvements: [Issues](https://github.com/xi-kari/xi-kari-skill/issues/new/choose)
- Theory discussion, experience and open questions: [Discussions](https://github.com/xi-kari/xi-kari-skill/discussions)
- Integrity and trust-boundary problems (a tampered package, a bypass of source identity checks, script injection in the offline pages, reading or writing outside allowed paths): report privately under the [security policy](SECURITY.md), not in a public issue.

Development happens on Windows; CI uses Python 3.10, 3.13 and Node.js 22.x. After changing tools, source reading or the install list:

```powershell
python -m pip install pypdf==6.19.0
npm ci --prefix tests/dom --ignore-scripts --no-audit --no-fund
python -m unittest discover -s tests -v
python scripts/read_source.py --check
python scripts/build_english_edition.py --check
python scripts/build_install_package.py --output <a directory outside the repository>
```

The reading site is built to `docs/handbook/` with `npm ci --prefix website` and `npm run build --prefix website`. Revisions of the theory text are committed separately from engineering changes; the boundaries and checks for each kind of change are in [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/MAINTAINING.md](docs/MAINTAINING.md).

## License

This repository is released under the [MIT License](LICENSE), © 2026 xi-kari. The bundled KaTeX keeps its [license](assets/vendor/katex/LICENSE); third-party resources of the reading site are listed in [THIRD_PARTY_NOTICES.txt](website/public/THIRD_PARTY_NOTICES.txt).

<br>

<p align="center">
  <sub>Xikari · 柊東雲 / Hiiragi Shinonome · <a href="https://xi-kari.com/">Blog</a> · <a href="https://xi-kari.github.io/xi-kari-skill/">Project page</a></sub>
</p>
