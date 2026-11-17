---
{"id":"REF-RESEARCH-FORMAT","theory_sha256":"6ef2e508474d4ac1ad07d7e4e068955342c405b5f680afcfc40d68cca3d0149c","anchors":["1.10","2.13","2.14","4.17.4","16.3","16.21"]}
---

# 研究双成果的数据与工具

`research.py` 接收研究者已经完成的材料分析和公开论证，生成完整研究报告与独立问题报告，并沿声明的依赖定位修订范围。工具不取得材料、不替作者完成研究、不认证正文质量，也不因记录齐全提高事实或因果判断的强度。实际工作入口见[研究模块](../modules/research/MODULE.md)。

§1.10 允许研究按其问题形成不同类型的认识成果；§2.13、§4.17.4、§16.3、§16.21 所涉及的识别、评估与方法责任不能由字段检查替代。这里的数据分类和命令是派生工程约定，不是追加理论定义。问题重开仍按 §2.14 保留旧问题与已有结果。

## 调用

```bash
python scripts/research.py --research assets/examples/research.json validate
python scripts/research.py --research assets/examples/research.json render --output /outside/task/research-result
python scripts/research.py --research assets/examples/research.json impact --changed S-register
```

`--output` 使用宿主认可的安装目录外路径，并须是尚不存在的目录；Windows 可使用 `C:\Tasks\example\research-result`。`render` 同时发布 `research-report.md` 与 `research-issues.md`。如需 Word 或阅读版，继续使用现有的 `render_docx.py`、`render_answer.py`，不把 JSON 或问题台账当作最终正文。

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

每项结论有 `id`, `title`, `kind`, `status`, `body`, `depends_on`, `limitations`, `change_conditions`。`body` 是作者的实际论证，不是让程序补写的提纲。`depends_on` 引用输入或其他结论 ID；它表示实质依赖，不能拿相互争论的立场制造循环。`limitations` 可以为空列表，不能用空字符串伪装限制；`change_conditions` 至少说明一个可能改判的条件。

`kind` 可为 `descriptive`、`causal`、`interpretive`、`normative`、`model_result`、`candidate`、`unknown`、`conditional_projection`；`status` 可为 `supported`、`proposed`、`contested`、`unknown`、`refuted`、`withdrawn`。这些身份按作者实质判断填写，程序不会把描述升级为因果、模型内结果升级为现实事实，或把未知补为零。未知输入的依赖会在对应结论旁提示。

现实前瞻仍由既有 `forecast.py` 登记和回写。研究格式不提供一个可绕过该责任的 `forecast` 身份。需要在研究中报告已登记前瞻时，引用其真实登记作为材料，并保持原判断的身份、期限与评价口径；不能把前瞻改名为条件推演来省略登记。

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

`theory_candidate` 还须提供 `theory` 对象，字段为 `proposition`、`anchor`、`source_sha256`、`scope`、`challenge`：原命题、随包原文的小节号、所据原文字节散列、命题的前提与范围，以及具体反例、冲突或遗漏。`source_sha256` 须与当前随包原文一致；版本不同就先回查受影响命题，不能只改散列以消除错误。工具检查版本和锚点确实存在，但不证明引述准确或反例命中。理论对象只允许用于此分类，避免将材料空白误写为理论漏洞。

重大且仍活跃的问题会在摘要后集中显示，其影响也会出现在对应结论及声明依赖的下游结论旁。独立的问题报告展开全部已做工作、缺口、影响与下一步。不能只修改问题附篇，却让主报告继续无条件宣称受影响结论。

没有具体问题项时，`issues: []` 合法，但 `issue_assessment` 仍须说明评估范围。渲染结果会明确“本次未提出”不等于“普遍无问题”。

## 写入与修订

记录使用全局唯一的 ASCII ID，拒绝未知字段、重复 JSON 键、重复 ID、未知引用、循环依赖及非有限数。输入最大 4 MiB，每类记录最多 2000 项；超过范围时按实际专题拆分。字符串不执行为代码，正文中保留的 Markdown 仍是作者内容。

双成果先在同一父目录的临时目录中写完并刷新，再在独占写锁内无覆盖发布。已有目录、文件或符号链接均被拒绝，没有 `--force`；修改后另写新版本目录，审阅后再由用户或宿主安排采用。Linux 使用无覆盖目录重命名，Windows 使用其拒绝覆盖的重命名行为；平台或文件系统不支持所需发布语义时明确失败，不退化成可能覆盖的写法。临时目录或锁因进程被强制终止而遗留时，不宣称发布成功，也不自动删除其他写入者的锁。

API 对应 `validate_research(data)`、`render_documents(data)`、`impact(data, changed)`、`write_documents(documents, output)`。`validate` 返回的 `structure_valid` 只指结构与引用合同。正文的论证、竞争解释、材料质量以及边界是否充分，仍须回到[实际研究](research-work.md)、[完整答案](complete-answer.md)和原问题审阅。

完整合成示例见 [`assets/examples/research.json`](../assets/examples/research.json)。其中计算为 30/50 与 40/50，原因识别和就业随访分别保留未决；更正 `S-register` 会影响比例与其下游，`F-definition` 的本地词义区别仍保持相对独立。示例用于说明流程，不作为现实使用增益证据。
