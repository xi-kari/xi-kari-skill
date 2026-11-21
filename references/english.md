# Working in English

Read this when the user writes in English, asks for English output, or quotes the English edition. Everything else in the skill applies unchanged; this page only adds what changes when the work is done in English.

## Language of the work

- Answer in the language the user writes in or asks for, and keep it for follow-ups in the same task unless the user switches.
- The working instructions — `SKILL.md`, `references/`, `modules/` and rule cards — are written in Chinese. Follow them as written. Do not restate them as a second English rule set or relax them because the answer is in English.

## Two editions, one authority

- `source/Xikari-条件结构与转化论.md` is the theory source and the only authority. Its definitions, conditions, exclusions, quantifiers, permissions and prohibitions govern.
- `source/en/Xikari-On-Conditions-Structure-and-Transformation.md` is the English reference edition: the user-supplied English translation of Chinese v2, revised section by section to follow the current Chinese wording, v2.1. It shares every section ID (`1.1`, `4.17`, `C.12`, …), part anchor and paragraph with the Chinese source, so a § reference names the same passage in both. `source/en/source-manifest.json` records its identity and the edition it revises; structural alignment and matching hashes do not certify translation accuracy or author approval.
- Like the Chinese, the English edition calls every concept by its name. A code stands only at the end of the heading of the section that defines it, in parentheses (`## 3.3 Effective Feedback (D2)`), in the Appendix B table, and where the Chinese keeps one (the formal propositions F1–F6 in §4.18, §4.19 and Appendix C). To find the name behind a code in older material, use Appendix B; [theory-core.md](theory-core.md) gives the Chinese names.
- Use the English edition for English terminology, for quotations in English answers, and for readers who want to read the theory in English. It gains no authority of its own. Where it appears to differ from the Chinese on a definition, condition, quantifier, permission or prohibition, follow the Chinese, translate that passage directly, and tell the reader when the difference matters.
- The edition omits parenthetical Chinese glosses from the prose. It keeps the definitional tuples (`A*`, `C*`, `MC*`, `M(SP0→SP1)`) in their Chinese wording and gives their English in translator's notes. Translator's notes carry `[^tn-…]` identifiers; they are not the author's text and are never quoted as such. Copyright and license text is retained in full; it is not part of the Chinese–English body alignment.

## Reading

- The reading rules in `SKILL.md` and [full-source-study.md](full-source-study.md) do not change. `full` mode is complete, ordered study of the Chinese source with `read_source.py`.
- Reading the English edition in place of the Chinese source is not assumed to be equivalent. Like `layered`, it is a reading condition that may be used only in an explicitly authorized experiment, and it cannot become a default before a same-task, same-materials, same-model A/B comparison with tolerances fixed in advance and the author's decision on the result.
- Locating and quoting English wording after study:

```powershell
python "$skillRoot/scripts/read_source.py" --parallel --section 4.17
python "$skillRoot/scripts/read_source.py" --lang en --section 12.2
python "$skillRoot/scripts/read_source.py" --lang en --search "action ceiling"
```

`--parallel` prints the Chinese and then the English text of the same sections. `--lang en` works with `--section`, `--part`, `--front`, `--chunk`, `--chunks`, `--list` and `--search`. `--check` verifies both editions and reports whether the English edition translates the current Chinese wording or the earlier wording that the current text revises.

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
| 修复、恢复 | repair, recovery | never *restoration* for 修复 or 恢复; *restoration* is 恢复原状 |
| 分组增益、对象事实 | grouping gain, object facts | a grouping-gain test supports a task-relative gain, not object existence; *object identification* is not the name of its result |
| 构成关系、因果关系 | constitutive relation, causal relation | evidence that a status holds is distinct from evidence of its effects |
| 形成、维持、恢复、复制 | formation, maintenance, recovery, replication | four descriptive outcomes; none proves another or authorizes continuation |
| 承接、承担、承载 | take up / uptake, bear, carry | three different relations |
| 退出、退场、有序退场 | exit (an actor leaves), exit (an object leaves), orderly exit | |
| 正当、合法性、合法 | justification, legitimacy, lawful | normative justification is not perceived legitimacy |
| 变换、转换、转移、转义、迁移 | transformation, conversion, transition, recasting, transfer or migration | |
| 运转、存续、演化、解体 | operation, persistence, evolution, dissolution | |
| 正向支持、有限正向支持、未获正向支持、未决 | positive support, limited positive support, not positively supported, unresolved | *not positively supported* is never *rejected* |
| 圈层、多圈层、联合状态 | circle, multi-circle, joint state | a circle implies no hierarchy |

Modal force follows the Chinese: 须／必须 *must*; 应 *should*; 不得 *must not*; 不能 *must not* for a rule and *cannot* for an impossibility; 可以 *may* for permission and *can* for possibility; 不必 *need not*; 未必 *not necessarily*; 不自动 *does not automatically*; 不等于 *is not the same as*; 单独 *by itself*; 只有……才 *only if*; 仍 *still*. Rules about what AI, tools or analysts may do are rules: write *must not*, not *cannot*.

Preserve the scope of the normative distinctions as well. In §14.4.1, proportionality concerns identifying indirect and more distant positions, not reduced protection for identified positions or permission to omit directly affected and known low-power positions. In §14.8, maintaining protection does not guarantee unchanged outcomes. In §14.9.1, a justified analytical recommendation when every option involves loss does not confer “authorized” status or waive non-waivable requirements. Do not turn a restriction on adoption into a ban on giving the analysis.

When you quote the English edition, quote its words as written. In your own prose, name the concept, as both editions do; give a code only where the reader needs it to find a defining section or to read older material that uses codes.

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
| R8 生成 | R8 Generation |
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
| M10 生成 | M10 Generation |
| 起点；父项；走法；谱系 | starting point; parent; move; lineage |
| 推必然；挪位置；接外部 | deriving what must hold; moving one position; reaching outside |
| 展开承诺；核对组合；改换任务 | unfolding commitments; checking composition; changing the task |
| 换尺度；换关系；换表示；换位置；换时钟；反过来问 | shifting scale; shifting relation; shifting representation; shifting position; shifting clock; asking the reverse |
| 追残差；跨域借问；联想 | following the residual; borrowing a question across domains; association |
| 模型内推论；定义要求；经验候选；变量候选 | consequence within a model; definitional requirement; empirical candidate; variable candidate |
| 启发性类比；新问题；构想 | heuristic analogy; new question; proposal |
| 重述；已有；可能已有；对本题新；所查范围内未见 | restatement; already known; probably known; new to this question; not found in the scope searched |
| 候选账本 | candidate ledger |
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
| 研究与解释边界报告 | research and the limits of explanation |
| 完整稿；解释边界与问题（末章） | complete draft; Limits of explanation and issues (the closing chapter) |
| 影响哪些结论；不影响哪些结论；已经做了什么；为什么仍未解决；它把判断改成了什么；下一步 | conclusions affected; conclusions not affected; work already done; why it is still unresolved; what it changes in the judgment; next step |
| 材料不足；方法与识别限度；领域知识或方法需要接入；映射或概念表达不足；理论问题候选；规范分歧；技能实现或成品缺口 | insufficient material; limits of method and identification; domain knowledge or method needed; gap in mapping or concepts; candidate theory problem; normative disagreement; gap in the skill or the product |
| 领域映射与方法适配；领域卡；领域库 | domain mapping and method adaptation; domain card; domain library |
| 本题对照表 | table of usages for this task |
| 定义对应；角色或对象实例化；部分对应；观察接口；类比候选；不对应；不适用；未知 | definition correspondence; role or object instantiation; partial correspondence; observation interface; analogy candidate; no correspondence; not applicable; unknown |
| 语义对应；事实与机制证据；正式检验的资格 | semantic correspondence; factual and mechanism evidence; eligibility for a formal test |
| 目标侧独立复核；待检验转义 | independent review on the target side; recasting awaiting test |
| 成果模式 | output modes |
| 跨理论对话与争论重建；机制史与过程重建；制度与生活安排设计 | dialogue across theories and reconstruction of debates; mechanism history and process reconstruction; designing institutions and living arrangements |
| 经验、意义与作品阐释；概念重构与表达设计；中层理论与模型构造；共同问题与议程重开 | interpreting experience, meaning and works; concept reconstruction and expression design; building middle-range theories and models; shared problems and reopening the agenda |
| 领域专论；领域入口索引 | domain study; index of domain entries |
| 能力操作；有限工具 | capability operations; finite tools |

File names and command arguments stay as they are: `contract.md`, `state.md`, `snapshot.md`, `paths.md`, `forecasts.json`, `candidates.json`, `xi-kari-answer.md`.

In an R8 answer the identity word travels with each candidate: *must* is used only for a consequence within a model that the sentence names; an untested empirical statement is a *candidate*, never a *finding*; *not found in the scope searched* always states the scope.

## Quoting

- Quote the English edition word for word and give the section, for example: “Complexity does not amount to maturity.” (§10.10).
- When you translate a passage yourself because the edition appears to differ from the Chinese, mark it: (translated from the Chinese, §x.y).
- Before a quotation decides an answer — a definition, a condition, a permission or a prohibition — read the same section with `--parallel` and confirm that the Chinese says the same.

## English files

- Reading page: `render_answer.py … --lang en` gives an English interface and English reading statistics.
- Word: `render_docx.py … --lang en` gives English labels and sets the document language to English. Web and mail links become hyperlinks, links to headings jump to them, and a link a sent document cannot follow keeps its label with the destination in brackets.
- Comparison table: `comparison.py … --lang en` gives English headers, basis marks, ordering notes and limits; the model's own titles, labels and notes are written in English by you.
- Research: you write the complete draft in English, the report first and *Limits of explanation and issues* as its closing chapter. Each issue states the conclusions it affects and those it does not, the work already done, why it is still unresolved, what it changes in the judgment, and the next step.
- Domain cards: `domain_cards.py` reports in JSON with Chinese messages. The three bundled sample cards are written in Chinese; when you use one for an English reader, give its content in English in the answer. A card kept in an English-language library may use English headings; keep a *Sources* section and a *Revision record*.
- Finite models: `finite_tools.py` results use English field names and scope notes; only the one-line notice and command messages are Chinese.
- Registers and ledgers (`forecast.py`, `claims.py`, `candidates.py`, `task_state.py`, `study_design.py`, `evidence.py`, `casebook.py`) store English text in their fields unchanged; their command messages are Chinese. The candidate ledger rendered by `candidates.py` and the condition-model page of `condition_lab.py` still have Chinese fixed labels: when you hand it to an English reader, say so, or describe its results in English in the answer.

## Style

Write plain, precise English. The rules for complete answers, communication and presentation apply unchanged. Avoid stock phrases the source does not warrant — *delve into*, *it is important to note*, *crucial*, *pivotal*, *multifaceted*, *holistic*, *seamless*, *leverage*, *landscape*, *tapestry*, *realm*, *testament* — and do not add summary flourishes or triads the argument does not need.
