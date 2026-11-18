---
{"id":"REF-RESEARCH-FORMAT","theory_sha256":"6ef2e508474d4ac1ad07d7e4e068955342c405b5f680afcfc40d68cca3d0149c","anchors":["1.10","2.13","2.14","4.17.4","16.3","16.21"]}
---

# 研究双成果的数据与工具

`research.py` 接收研究者已经完成的材料分析和公开论证，生成一份完整稿或完整研究报告与独立问题报告，并沿声明的依赖定位修订范围。工具不取得材料、不替作者完成研究、不认证正文质量，也不因记录齐全提高事实或因果判断的强度。实际工作入口见[研究模块](../modules/research/MODULE.md)。

§1.10 允许研究按其问题形成不同类型的认识成果；§2.13、§4.17.4、§16.3、§16.21 所涉及的识别、评估与方法责任不能由字段检查替代。这里的数据分类和命令是派生工程约定，不是追加理论定义。问题重开仍按 §2.14 保留旧问题与已有结果。

## 调用

```bash
python scripts/research.py --research assets/examples/research.json validate
python scripts/research.py --research assets/examples/research.json render --answer /outside/task/xi-kari-answer.md
python scripts/research.py --research assets/examples/research.json render --output /outside/task/research-result
python scripts/research.py --research assets/examples/research.json impact --changed S-register
```

`render --answer` 写出一份完整稿，供作为 `xi-kari-answer.md` 交付：标题、研究问题、当前判断与重大未决在前，接范围与方法、研究论证，再以“解释边界与问题”为末章，逐项写出已做工作、未解决原因、对前文判断的影响和下一项工作，最后是材料、前提与映射。问题章与主体同在一稿，阅读页的目录和 Word 导航都能到达它，摘要和相关结论旁的重大限制照常显示。目标须是安装目录外尚不存在的文件，工具不覆盖已有稿件；修订后另写新文件。

`render --output` 改为同时发布 `research-report.md` 与 `research-issues.md` 两份文件，用于用户要求问题报告单独流转的情形；两份文件以相对链接互指，须放在同一目录一起交付。`--output` 须是尚不存在的目录；Windows 可使用 `C:\Tasks\example\research-result`。两种输出都可加 `--lang en`，只把固定标题、标签和提示换成英文，作者正文保持原样。阅读页和 Word 用 `render_answer.py`、`render_docx.py` 从完整稿生成，不把 JSON 或问题台账当作最终正文。

重复 `--changed` 可以同时列出若干变更 ID。变更可以是来源、前提、映射或已有结论；工具返回受影响和相对独立的结论、关联问题、一条传播路径及摘要是否需要复核。它不自动撤回结论，不声称记录之外没有隐藏依赖。

## 输入合同

`schema_version` 为整数 `1`。顶层字段都须显式提供：

| 字段 | 内容 |
| --- | --- |
| `title`, `question`, `scope`, `method` | 成果标题、问题、实际范围及实际采用的方法 |
| `summary`, `summary_refs` | 作者综合判断正文及它所依赖的结论 ID |
| `inputs` | 来源、前提与映射，不混为一种证据 |
| `findings` | 有身份、依据、公开论证、限制及改判条件的具体判断 |
| `issues`, `issue_assessment` | 具体未决或问题；本次评估覆盖的范围与未发现项的含义 |

每项输入有 `id`, `kind`, `label`, `content`, `locator`, `status`。`kind` 为 `source`、`premise` 或 `mapping`；`status` 为 `known`、`unknown` 或 `synthetic`，表示记录者申明的材料状态，不是工具确认。已提供的来源须有可回查的 `locator`。未知来源可将位置留为空字符串，但应在 `content` 说明缺失的具体内容。合成来源要明确标识，渲染时会在主报告开头提示其使用范围。

`known` 表示本稿使用的内容已取得或前提已明确，不表示其中的叙述、前提或映射已经证实。例如已取得一份有争议的访谈可记为来源 `known`，相关结论仍可为 `unknown` 或 `contested`；明确写出的假设也不因此成为现实事实。`unknown` 表示真正缺失的输入，不能用它隐藏已取得的反向材料。

这份 JSON 是一次研究成稿的快照。已有 `evidence` 或 `claims` 时，`content` 只写本稿实际使用的必要摘要，`locator` 指既有来源、片段或主张 ID 与位置；原始片段及历史仍由原记录保存，不再复制整份台账。普通 `locator` 仅供作者回查，程序不会自动读取、下载或同步它。

每项结论有 `id`, `title`, `kind`, `status`, `body`, `depends_on`, `limitations`, `change_conditions`。`body` 是作者的实际论证，不是让程序补写的提纲。`depends_on` 引用输入或其他结论 ID；它表示实质依赖，不能拿相互争论的立场制造循环。`limitations` 可以为空列表，不能用空字符串伪装限制；`change_conditions` 至少说明一个可能改判的条件。

`kind` 可为 `descriptive`、`causal`、`interpretive`、`normative`、`model_result`、`candidate`、`unknown`、`conditional_projection`；`status` 可为 `supported`、`proposed`、`contested`、`unknown`、`refuted`、`withdrawn`。这些身份按作者实质判断填写，程序不会把描述升级为因果、模型内结果升级为现实事实，或把未知补为零。未知输入的依赖会在对应结论旁提示。

已撤回或已被反驳的结论仍可保留作历史对象或反驳证据。若摘要或其他结论声明依赖它们，工具在相关位置显示状态与一条依赖路径，提醒作者区分“记录反驳结果”和“继续把旧判断当作成立前提”；它不自动撤回下游判断。提示路径不穷举全部依赖，也不判断正文是否已经恰当处理。

现实前瞻仍由既有 `forecast.py` 登记和回写。研究格式不提供一个可绕过该责任的 `forecast` 身份。需要在研究中报告已登记前瞻时，引用其真实登记作为材料，并保持原判断的身份、期限与评价口径；不能把前瞻改名为条件推演来省略登记。

## 领域映射的跨文件修订

需要自动定位领域包更正的影响时，仅在相应 `kind: "mapping"` 输入增加可选的 `mapping_ref`：

```json
{"id":"具体领域包ID","version":"所据版本","sha256":"所据JSON原始字节的小写SHA-256","node_ids":["实际使用的条目或成果ID"]}
```

`node_ids` 可以引用映射包的来源、对应条目或已成文成果，只记录实际使用部分。用 `domain_mapping.py --mapping <文件> validate` 返回的 `id`、`version`、`snapshot_sha256` 填入前三项；它们是文件身份，不是语义认可。普通研究仍可使用没有绑定的人工映射说明。

```text
python scripts/research.py --research /outside/task/research.json impact-mapping --mapping /outside/task/mapping-old.json --changed s-definition
python scripts/research.py --research /outside/task/research.json impact-mapping --mapping /outside/task/mapping-old.json --against /outside/task/mapping-new.json
```

命令显式读取原稿所据旧快照，核对包 ID、版本、原始字节摘要与节点存在，再从领域来源、条目或已成文成果沿映射成果、研究输入、结论传播到摘要和问题；成文成果本身被更正时，也可直接把它列为变更。可重复 `--changed`；也可改用 `--against <新快照>`，由两份快照的逐记录比较自动取出删除或改动的节点，比较结果放在 `mapping_diff`，两种方式只能选一种。新快照只有新增或排版变化时，绑定照常核验，受影响结论为空。仅文件换行或格式变化也会改变字节摘要；保留原始快照，不用重新排版文件冒充同一文件。缺快照或指定快照没有任何匹配绑定时明确失败；同 ID、同版本的摘要冲突或节点缺失一律失败，不返回假“无影响”。同时存在其他版本的绑定按下述未核验范围处理。

一次处理一个指定快照。其他包、其他版本和人工映射列入 `unverified_mapping_inputs`，其下游列为 `unassessed_findings`，不会归入 `independent_findings`。已有受影响结论同时依赖未核验输入时仍列为受影响，未核验输入清单和 `summary_has_unassessed_dependencies` 保留覆盖缺口。跨包相同节点名不自动连接。确认绑定但变更与本稿无已声明依赖时，才允许受影响集合为空。

完整稿需要附上所据领域映射时，重复 `--mapping <快照>` 指定绑定的快照：

```text
python scripts/research.py --research /outside/task/research.json render --answer /outside/task/xi-kari-answer.md --mapping /outside/task/mapping-old.json
```

每份快照须与某项 `mapping_ref` 的包 ID、版本和原始字节摘要一致，引用的节点也须存在；它们按给出顺序附为“领域映射与使用说明”章，置于材料一章之后、结尾提示之前。未绑定、已改动或重新排版的文件明确失败，不把未核验的映射附入成稿。附章只展示该快照的内容与身份，不证明对应正确。

除此之外，`validate` 和 `render` 只检查、展示绑定字段，均不读取外部映射文件，不宣称绑定已经核实。`impact-mapping` 的核验只证明这一份显式快照的引用关系；漏记依赖、对应是否正确、作者正文是否充分仍需实际审查。作者读取新材料、修订对应与研究正文和问题报告后，才更新绑定并另存新版；只替换摘要或散列不算完成修订。

## 问题与主报告同步

每项问题显式填写：

| 字段 | 内容 |
| --- | --- |
| `id`, `title`, `categories` | 唯一标识、具体问题、一个或多个分类 |
| `affected_findings` | 直接受影响的已有结论 ID |
| `materiality`, `status` | `major` 或 `minor`；当前处理状态 |
| `current_work`, `why_unresolved` | 实际已经做过什么，具体为何仍未解决 |
| `consequence`, `next_work` | 改变主报告什么，下一项有区分力的工作 |
| `status_reason`, `resolution_scope` | 状态依据，已解决与尚未解决的范围 |

分类选项为 `material_gap`（材料不足）、`identification_limit`（方法识别限度）、`domain_method`（领域方法需要接入）、`mapping_gap`（映射或概念缺口）、`theory_candidate`（理论问题候选）、`normative_disagreement`（规范分歧）、`implementation_gap`（技能实现缺口）。允许多类并存，不要求每份报告都找齐七类问题。

问题状态可为 `open`、`under_investigation`、`partially_resolved`、`resolved_within_scope`、`withdrawn`、`superseded`。未决和部分解决项须保留 `next_work`；部分解决或限定解决项须具体填写 `resolution_scope`。已讨论、已回复或已归档不能单独作为解决依据。工具检查文字是否提供，实际理由是否充分仍由作者核对。

`superseded` 还须填写非空 `superseded_by` 列表，引用本记录中的后继问题 ID；允许拆为多个后继问题，不允许未知引用、自指或循环。其他状态不填写此字段。旧格式中仅写了 `superseded` 的记录应先补齐真实后继或改回与实际工作相符的状态，不能编造后继来通过校验。主体与问题部分均保留后继指向，替代不表示缺口已经解决。

`theory_candidate` 还须提供 `theory` 对象，字段为 `proposition`、`anchor`、`source_sha256`、`scope`、`challenge`：原命题、随包原文的小节号、所据原文字节散列、命题的前提与范围，以及具体反例、冲突或遗漏。`source_sha256` 记录所据原文的字节散列。与当前随包原文一致时，工具核对锚点确实存在；理论更新后，绑定旧版本的记录仍可校验、渲染和追踪，`validate` 列出 `theory_bindings_not_current` 与警告，主体与问题部分都显示版本提示，锚点不按当前原文核对。版本不同时应回查受影响命题，不能只改散列来消除提示。工具不证明引述准确或反例命中。理论对象只允许用于此分类，避免将材料空白误写为理论漏洞。

重大且仍活跃的问题会在摘要后集中显示，其影响也会出现在对应结论及声明依赖的下游结论旁。问题章（或分文件时的独立问题报告）展开全部已做工作、缺口、影响与下一步。不能只修改问题附篇，却让主报告继续无条件宣称受影响结论。

没有具体问题项时，`issues: []` 合法，但 `issue_assessment` 仍须说明评估范围。渲染结果会明确“本次未提出”不等于“普遍无问题”。

## 写入与修订

记录使用全局唯一的 ASCII ID，拒绝未知字段、重复 JSON 键、重复 ID、未知引用、循环依赖、NUL 字符及非有限数。输入最大 4 MiB，每类记录最多 2000 项。大量问题向下游传播会放大最终文本，完整稿或双成果的渲染总量另限 32 MiB，在写入前超限失败；超过范围时按实际专题拆分，并保留跨专题所需依赖与限制。字符串不执行为代码，正文中保留的 Markdown 仍是作者内容。

完整稿先写入同目录临时文件并刷新，再在独占写锁内以硬链接无覆盖发布。双成果先在同一父目录的临时目录中写完并刷新，再在独占写锁内无覆盖发布。已有目录、文件或符号链接均被拒绝，没有 `--force`；修改后另写新版本目录，审阅后再由用户或宿主安排采用。Linux 使用无覆盖目录重命名，Windows 使用其拒绝覆盖的重命名行为；平台或文件系统不支持所需发布语义时明确失败，不退化成可能覆盖的写法。临时目录或锁因进程被强制终止而遗留时，不宣称发布成功，也不自动删除其他写入者的锁。

API 对应 `validate_research(data)`、`render_answer(data, lang, appendices)`、`mapping_chapter(data, mapping_path, lang)`、`write_answer(text, output)`、`render_documents(data, lang)`、`write_documents(documents, output)`、`impact(data, changed)`、`impact_mapping(data, mapping_path, changed, against)`。CLI JSON 结果也限制为 32 MiB，超限在输出任何部分前失败。`validate` 返回的 `structure_valid` 只指结构与引用合同。正文的论证、竞争解释、材料质量以及边界是否充分，仍须回到[实际研究](research-work.md)、[完整答案](complete-answer.md)和原问题审阅。

完整合成示例见 [`assets/examples/research.json`](../assets/examples/research.json)。其中计算为 30/50 与 40/50，原因识别和就业随访分别保留未决；更正 `S-register` 会影响比例与其下游，`F-definition` 的本地词义区别仍保持相对独立。示例用于说明流程，不作为现实使用增益证据。
