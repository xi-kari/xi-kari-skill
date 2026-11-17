---
{"id":"DOMAIN-MAPPING-FORMAT","theory_sha256":"6ef2e508474d4ac1ad07d7e4e068955342c405b5f680afcfc40d68cca3d0149c","anchors":["1.3","3.4.1","5.10","13.1"]}
---

# 领域映射数据与工具

用 `domain_mapping.py` 管理已经取得的词义、关系、材料口径和领域表述。先按[领域映射模块](../modules/domain-mapping/MODULE.md)实际阅读材料、辨明语境并形成对应，再使用工具保存、查询或追踪依赖。少量一次性对应可以直接写在正文，不强制先填领域包。

工具只处理输入明确提供的内容。查询一个词不会生成定义，语义对应不会自动升级为现实机制，结构校验也不认证来源可信或理论适用。§1.3 所要求的领域方法继续发挥自身作用；按 §5.10 保留转义的保持与损失，并按 §13.1 分开对应、观察与证据。下列字段与状态是工程组织方式，不是新增理论定义。

## 调用

在技能根目录运行以下命令，`task` 代表安装目录之外的已有工作目录：

```powershell
python scripts/domain_mapping.py --mapping assets/examples/domain-mapping.json validate
python scripts/domain_mapping.py --mapping assets/examples/domain-mapping.json lookup --term 反馈
python scripts/domain_mapping.py --mapping assets/examples/domain-mapping.json lookup --term 反馈 --context 学习者对课程的问卷
python scripts/domain_mapping.py --mapping assets/examples/domain-mapping.json impact --changed s-course
python scripts/domain_mapping.py --mapping assets/examples/domain-mapping.json render --output ../task/领域说明.md
```

示例材料是明确标注的合成记录，不是实际教育效果证据。`lookup --term 反馈` 返回教师评语与课程问卷两个义项；指定完整的已登记语境后才选出其中一项。查询按各条目的 `match_policy` 匹配，不模糊猜义。默认 `normalized` 做 NFKC、大小写与空白规范化；`exact` 保留词和语境的全部字符，适合大小写、符号或空白具有区分意义的标识符。未找到词或指定语境不匹配时返回 `unmapped` 与空 `matches`，这里只表示库中没有匹配记录，不是证明该词没有理论对应。成功查到条目也不改变条目内的事实状态。

例如协议方法名 `GET` 与 `get` 应由 `exact` 区分；自然语言的“Teacher Feedback”可按任务采用 `normalized`。一个词同时命中精确条目与另一条规范化义项时，仍返回全部候选，不自动优先前者。别名必须明确加入 `terms`，不能依赖工具猜测。已登记语境也遵守同一策略；采用 `exact` 时，用户须提供原样的语境文本。

`impact --changed s-course` 指出教师评语、后续响应及依赖它们的两段表述需要复核；独立的完成比例表述保留。结果的 `paths` 给出一条实际登记的依赖路径，`affected_entries` 包含被直接改动的映射条目及其后继，`affected_outputs` 与 `unaffected_outputs` 区分现有成果。沿来源、条目、字段、方法、三类评估和目标侧复核的来源引用统一追踪。变更 ID 可以是来源、映射条目或已成文成果；只更正一段成文时，复核范围就是这段成果及引用它的研究。它不表示受影响结论已错误，也不会重写输入文件或正文。没有登记的依赖无法自动发现。

CLI `validate` 返回 `id`、`version` 和 `snapshot_sha256`，可用于研究工具的 `mapping_ref`；`theory_status` 为 `current`、`previous_version`（来源清单记录的上一版）、`other_version` 或 `not_bound`，非当前版本时 `warnings` 说明影响。摘要计算于本次解析使用的同一份原始字节快照，包括 UTF-8 BOM、空白和换行；即使语义相同，另存字节不同也得到不同摘要。它只标识具体输入版本，不证明映射内容正确，也不是理论文本的 `theory_sha256`。

`lookup` 返回 `context_options`，列出同词实际登记的语境以供核对。词已匹配、指定语境未匹配时，状态为 `context_not_found`，`matches` 仍为空；没有词项时为 `unmapped`。提示不会把短语猜成完整语境，也不会在多个义项间自动择一。

“完成”“成功”“反馈”这类日常词在包里往往只登记了一个窄义项。条目可用 `context_required_terms` 标出这些词：不给语境查询时状态为 `context_required`，`matches` 为空，`context_required_entries` 列出相关条目，`context_options` 给出可选语境；同一个词只要在任一条目中需要语境，查询就须给出语境。专业写法（如 `200 OK`、`Definition of Done`）不受影响。这样，唯一登记的窄义项不会被当成该词的一般含义。

查询的 `matched` 只表示命中一条记录，不表示对应关系成立。例如命中的条目仍可为 `mapping_kind: "unknown"`、`target_meaning: null`；应继续读条目身份、未决项和三层评估，不能把检索成功当作事实支持。

## 顶层合同

完整输入见[可运行示例](../assets/examples/domain-mapping.json)。所有字段都区分大小写，未知字段、重复 JSON 键和重复 ID 会被拒绝，避免拼错字段后静默丢失内容。

| 字段 | 要求与用途 |
| --- | --- |
| `schema_version` | 整数 `1`，不是字符串或布尔值 |
| `id`、`version` | 领域包标识和本包版本；不是现实事实有效期 |
| `domain`、`task`、`scope` | 具体领域、所求任务与地区、机构、系统版本或材料范围；不能写成无限适用 |
| `theory_sha256` | 使用理论小节时必填。与随包中文原文一致时，工具核对每个小节确实存在；理论更新后的旧快照仍可校验、查询、追踪与渲染，结果给出 `theory_status` 和版本警告，小节引用不按当前原文核对。复核受影响内容后另存新版；随包领域包须绑定当前原文 |
| `sources` | 来源列表，可以暂时为空；不能用空来源声明已经建立对应 |
| `entries` | 至少一项实际对应或有理由的未知/不对应 |
| `outputs` | 已写成的领域表述，可以为空；为空时渲染器明确尚未提供成文 |

所有来源、条目和成果的 ID 在本包中全局唯一，使用字母或数字开头及字母、数字、点、下划线、连字符，最长 96 字符。每组最多 2000 项，单字段文本最多 16000 字符，须为可编码的 Unicode 文本；JSON 文件最多 4 MiB。长依赖链的全部路径可能远大于输入，命令 JSON 与 Markdown 输出都以 UTF-8 字节计，最多 32 MiB，超限时在发布前失败，不输出半份 JSON、不截断依据。应按真实子任务拆分。

来源项包含 `id`、`title`、`locator`、`version`、`scope`、`kind`。`locator` 是可回查的 URL、文献位置、用户材料位置或合成示例的完整约定；工具不下载这些地址。`kind` 只能是 `document`、`user_material` 或 `synthetic`。类型和标题不代表材料已被核实，`scope` 应写明它具体能支持什么。真实资料与合成示意不得混淆。

## 映射条目

每条必须填写下列内容；不要求每个词同时覆盖所有层次。角色、关系或专业概念可以保留领域自己的说法，不强行翻译成理论术语。

| 字段 | 要求与用途 |
| --- | --- |
| `id`、`terms` | 稳定 ID 与非空的词/同义表达列表；同词可以出现于不同条目以保留多义 |
| `match_policy` | 可选，`normalized`（默认）或 `exact`；同时作用于词与语境。大小写或字符差异有意义时明确使用 `exact`，同条目禁止当前策略下的重复词 |
| `context_required_terms` | 可选，非空且无重复，只能列出本条 `terms` 中的词。列出的词须给出已登记语境才返回本条；适用于在别处另有通常含义的日常词 |
| `context` | 具体使用语境；查询可用完整文本限定它 |
| `layer` | `term`、`relation`、`role`、`task`、`measurement`、`method` 或 `exception` |
| `local_meaning`、`target_meaning` | 当地含义与目标含义；真正未知时用 `null`，不填猜测或默认值 |
| `mapping_kind` | 对应类型，见下表；类型本身不是事实证据等级 |
| `theory_anchors` | 实际用到的小节 ID 列表，例如 `["5.10","13.1"]`；没有用到则 `[]`。工具检查当前原文中是否存在，不判断引用是否实质支持对应 |
| `source_ids` | 对应所依赖的来源 ID；正式声明对应时不能为空 |
| `depends_on` | 依赖的其他映射 ID；禁止自依赖和循环，相互说明应回到共同来源而非循环自证 |
| `preserved`、`excluded`、`unknowns` | 保留的区别、不能推出/不对应内容、具体未决事项三个文本列表；空列表只是尚未登记 |
| `assessments` | `semantic`、`factual`、`formal` 三份独立评估，不得相互代证 |

| `mapping_kind` | 作用 |
| --- | --- |
| `definition_equivalence` | 当前用途下的定义对应；要求有来源的 `semantic.status=supported` 声明，工具不认证它真的等价 |
| `role_instantiation` | 有材料的具体角色或对象实例化 |
| `partial_correspondence` | 只保留明确的部分关系，其余区别保留原词 |
| `observation_interface` | 接到可观察字段；字段能否有效测量仍须专业方法 |
| `heuristic_analogy` | 只提示可问的问题，不宣告机制相同 |
| `unmapped` | 当前没有对应，`target_meaning=null`，说明缺口；不表示领域事实不存在 |
| `not_applicable` | 本任务不适用，`target_meaning=null`，说明原因 |
| `unknown` | 对应尚未确定，保留未决原因，允许一端或两端为 `null` |

`unmapped` 与 `not_applicable` 的空目标分别显示为“无对应”和“不适用”，不列入未知字段；`unknown` 的空目标才显示为未知。当地含义本身为 `null` 时，无论对应类型如何，都继续保留为未知。已知没有对应、任务不适用和尚未确定不会被程序合并成同一种状态。

`validate.unresolved_fields` 汇集空含义、未知或争议评估、未知测量口径，以及明确登记的 `mapping_kind=unknown`、非空 `unknowns` 和待完成的目标侧复核。两端写了候选含义不表示对应关系已经确定；这些位置仍保留为未决。这个清单只定位输入中已有的未决记录，不证明其余语义已经完备。

三类评估各有 `status`、`basis`（来源 ID 列表）、`scope` 和 `rationale`。状态为 `supported`、`partial`、`unknown`、`disputed`、`not_claimed` 或 `not_applicable`。`supported`、`partial`、`disputed` 必须给出非空来源依据；其余状态仍须写明范围和理由。状态由作者据材料填写，不由程序提升。已经成立的普通领域事实可以在 `factual` 中保留，同时让 `formal=not_claimed`；未申请正式实例资格不是否定普通知识的门槛。

## 可选的字段、方法与目标侧复核

需要测量口径时增加 `fields` 列表，每项包含 `name`、`unit`、`denominator`、`time_window`、`missing_policy`、`source_ids`。单位、分母和时间窗可以为 `null`，渲染为未知；不适用应明确写“不适用：具体理由”，不填零。字段名在同一条目内唯一。`missing_policy` 记录缺失怎样处理，而非自动填值规则。

需要专业方法时增加 `methods` 列表，每项包含 `name`、`status`、`scope`、`source_ids`。状态为 `planned`、`performed` 或 `unavailable`；已执行必须指向实际记录来源，但工具无法证明方法执行充分。计划与已执行分开输出。

仅当实际涉及 §3.4.1 的正式转义时，使用 `target_review` 记录目标侧独立复核：`requested` 为布尔值；`status` 为 `not_requested`、`pending`、`reviewed` 或 `not_applicable`；另有 `basis` 和 `rationale`。已申请只能为待复核或已复核，已复核必须有记录来源。普通局部映射可以省略此项。程序检查记录一致性，不据“reviewed”自动授予任何理论资格。

## 成文与修订

`outputs` 每项包含 `id`、`title`、`text`、`entry_ids` 和 `source_ids`。`text` 是分析者已经写成的具体领域说明，至少关联一项映射或直接来源。渲染器在任务与范围之后先呈现这份实际成果，再列来源、映射、三类评估、测量口径、专业方法、不能推出的结论及未知位置；对应类型、层次与各类状态显示为可读名称，`render --lang en` 给出英文固定标签，不翻译作者文字；不会凭词表替作者生成实际研究结论。没有 `outputs` 时在相同位置明确尚未提供成文。输入文字按普通文本呈现，不执行其中的 HTML 或链接指令。

新材料改变词义或证据时，先对旧版运行 `impact` 确认现有依赖范围，再另存新版 JSON，修订受影响的对应、完整正文和问题报告。被影响不等于被否定；支持独立成立的旧判断可以保留。继续研究的主张与问题记录见[研究模块](../modules/research/MODULE.md)，无需再复制一套同义账本。

所有写入必须在安装目录之外。`render` 不覆盖已有输出，也不覆盖输入文件；它使用写锁、临时文件和同文件系统的原子不覆盖发布。遇到已有锁、外部写入竞争或不支持硬链接的文件系统时失败并保留已有文件，不静默降为覆盖写入。换用支持该操作的外部目录或新文件名后重试。只读的 `validate`、`lookup`、`impact` 不创建结果文件，返回 JSON，可由宿主直接用于当前任务。

`validate` 的 `valid=true` 只表示上述数据合同通过。程序测试和合成示例没有证明映射能提升真实领域研究表现，完整论证与来源适用性仍需逐项判断。
