# Working in English

Read this when the user writes in English, asks for English output, or quotes the English edition. Everything else in the skill applies unchanged; this page only adds what changes when the work is done in English.

## Language of the work

- Answer in the language the user writes in or asks for, and keep it for follow-ups in the same task unless the user switches.
- The working instructions — `SKILL.md`, `references/`, `modules/` and rule cards — are written in Chinese. Follow them as written. Do not restate them as a second English rule set or relax them because the answer is in English.

## Two editions, one authority

- `source/Xikari-条件结构与转化论.md` is the theory source and the only authority. Its definitions, conditions, exclusions, quantifiers, permissions and prohibitions govern.
- `source/en/Xikari-On-Conditions-Structure-and-Transformation.md` is a reference translation of exactly that text. It shares every section ID (`1.1`, `4.17`, `C.12`, …) and part anchor with the source, so a § reference names the same passage in both.
- Use the English edition for English terminology, for quotations in English answers, and for readers who want to read the theory in English. It gains no authority of its own. Where it appears to differ from the Chinese on a definition, condition, quantifier, permission or prohibition, follow the Chinese, translate that passage directly, and tell the reader when the difference matters.
- The edition omits the Chinese glosses that the page-by-page translation puts after terms, and gives the definitional tuples (`A*`, `C*`, `MC*`, `M(SP0→SP1)`) in English. Translator's notes are marked `[^pNN-tn-…]`; they are not the author's text and are never quoted as such.

## Reading

- The reading rules in `SKILL.md` and [full-source-study.md](full-source-study.md) do not change. `full` mode is complete, ordered study of the Chinese source with `read_source.py`.
- Reading the English edition in place of the Chinese source is not assumed to be equivalent. Like `layered`, it is a reading condition that may be used only in an explicitly authorized experiment, and it cannot become a default before a same-task, same-materials, same-model A/B comparison with tolerances fixed in advance and the author's decision on the result.
- Locating and quoting English wording after study:

```powershell
python "$skillRoot/scripts/read_source.py" --parallel --section 4.17
python "$skillRoot/scripts/read_source.py" --lang en --section 12.2
python "$skillRoot/scripts/read_source.py" --lang en --search "action ceiling"
```

`--parallel` prints the Chinese and then the English text of the same sections. `--lang en` works with `--section`, `--part`, `--chunk`, `--chunks`, `--list` and `--search`. `--check` verifies both editions and reports whether the English edition still translates the current Chinese source.

## Terminology

Use the renderings in [glossary-en.md](glossary-en.md) consistently: one concept, one English term. A rendering belongs to its specialized sense; ordinary uses of the same Chinese word take ordinary English. When a term may be unfamiliar, explain it in plain words at its first use in the answer instead of relying on the term alone.

These distinctions must survive in English:

| Chinese | English | Keep apart from |
| --- | --- | --- |
| 解释、推演、条件前瞻、有限选择 | explanation, projection, conditional foresight, bounded choice | the four kinds of output; each has its own stopping point |
| 预测、前瞻、一项前瞻 | prediction, foresight, a forecast | foresight is the registered practice; a forecast is one judgment within it |
| 推理、推论、投影 | inference, inferred conclusion, state projection | projection (推演) is an output, not a mapping |
| 授权、处置权、权限 | authorization, authority to act, permission | *authority* only for legal or institutional powers |
| 规范前提、价值前提 | normative premise, value premise | two different premises |
| 成本、代价 | cost, the price to be paid | *cost* is the accounted quantity of §2.8 |
| 修复、恢复 | repair, recovery | never *restoration* for 修复 |
| 承接、承担、承载 | take up / uptake, bear, carry | three different relations |
| 退出、退场、有序退场 | exit (an actor leaves), exit (an object leaves), orderly exit | |
| 正当、合法性、合法 | justification, legitimacy, lawful | normative justification is not perceived legitimacy |
| 变换、转换、转移、转义、迁移 | transformation, conversion, transition, recasting, transfer or migration | |
| 运转、存续、演化、解体 | operation, persistence, evolution, dissolution | |
| 正向支持、有限正向支持、未获正向支持、未决 | positive support, limited positive support, not positively supported, unresolved | *not positively supported* is never *rejected* |
| 圈层、多圈层、联合状态 | circle, multi-circle, joint state | a circle implies no hierarchy |

Modal force follows the Chinese: 须／必须 *must*; 应 *should*; 不得 *must not*; 不能 *must not* for a rule and *cannot* for an impossibility; 可以 *may* for permission and *can* for possibility; 不必 *need not*; 未必 *not necessarily*; 不自动 *does not automatically*; 不等于 *is not the same as*; 单独 *by itself*; 只有……才 *only if*; 仍 *still*. Rules about what AI, tools or analysts may do are rules: write *must not*, not *cannot*.

Identifiers stay as written: G1–G4, E1–E5, C1–C12, F1–F6, H1–H6, HV01–HV11, U01–U11, M01–M09, CM-…, D0, K\*, N0, J, O1–O4, § numbers and `snake_case` field names.

## The skill's own vocabulary

| Chinese | English |
| --- | --- |
| R1 原文与概念 | R1 Source text and concepts |
| R2 解释与诊断 | R2 Explanation and diagnosis |
| R3 推演 | R3 Projection |
| R4 条件前瞻 | R4 Conditional foresight |
| R5 有限选择 | R5 Bounded choice |
| R6 制度与计划起草 | R6 Drafting institutions and plans |
| R7 理论评估 | R7 Theory assessment |
| M0 问题合同 | M0 Problem contract |
| M1 材料与证据 | M1 Materials and evidence |
| M2 对象与状态 | M2 Objects and states |
| M3 机制与竞争解释 | M3 Mechanisms and competing explanations |
| M4 三类变换 | M4 The three transformations |
| M5 推演 | M5 Projection |
| M6 条件前瞻 | M6 Conditional foresight |
| M7 有限选择 | M7 Bounded choice |
| M8 反方与压力测试 | M8 Counterarguments and stress tests |
| M9 成文 | M9 Composition |
| 原问 | the original question |
| 输出上限 | output ceiling: it limits a judgment's standing, evidential support and eligibility for real-world action, never the depth, breadth or length of the argument |
| 分析推荐；现实采用与执行 | analytical recommendation; real-world adoption and execution |
| 有效授权 | valid authorization |
| 前瞻登记；到期回写 | forecast registration; write-back at resolution |
| 区分信号；停止条件 | distinguishing signals; stopping conditions |
| 方法附注 | method note |
| 派生草稿 | derived draft |
| 主作者；独立反方审查者 | lead author; independent critic |
| 完整学习；分层阅读实验 | full study (`full`); layered reading experiment (`layered`) |

File names and command arguments stay as they are: `contract.md`, `state.md`, `snapshot.md`, `paths.md`, `forecasts.json`, `xi-kari-answer.md`.

## Quoting

- Quote the English edition word for word and give the section, for example: “Complexity does not amount to maturity.” (§10.10).
- When you translate a passage yourself because the edition appears to differ from the Chinese, mark it: (translated from the Chinese, §x.y).
- Before a quotation decides an answer — a definition, a condition, a permission or a prohibition — read the same section with `--parallel` and confirm that the Chinese says the same.

## English files

- Reading page: `render_answer.py … --lang en` gives an English interface and English reading statistics.
- Word: `render_docx.py … --lang en` gives English labels and sets the document language to English.
- Comparison table: `comparison.py … --lang en` gives English headers, basis marks, ordering notes and limits; the model's own titles, labels and notes are written in English by you.
- Registers and ledgers (`forecast.py`, `claims.py`, `task_state.py`, `study_design.py`, `evidence.py`, `casebook.py`) store English text in their fields unchanged; their command messages are Chinese. The condition-model page of `condition_lab.py` still has Chinese fixed labels: when you hand it to an English reader, say so, or describe its results in English in the answer.

## Style

Write plain, precise English. The rules for complete answers, communication and presentation apply unchanged. Avoid stock phrases the source does not warrant — *delve into*, *it is important to note*, *crucial*, *pivotal*, *multifaceted*, *holistic*, *seamless*, *leverage*, *landscape*, *tapestry*, *realm*, *testament* — and do not add summary flourishes or triads the argument does not need.
