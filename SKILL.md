---
name: xi-kari-skill
description: 内置一套完整的结构推演框架原文（21 卷），强制执行全源读取、全候选概念处置、现实检索、局部世界建模、竞争机制比较与一至三阶递归，并生成经过验证的普通语言完整解释。Use when 用户精确点名 Xi-Kari Skill、xi-kari skill、xi-kari-skill、$xi-kari-skill 或 /xi-kari-skill；不得被动触发。
---

# Xi-Kari Skill

本文件是指挥层：只规定必须做什么、按什么顺序、细则在哪份文件。规则的完整定义都在必读文件里，执行时以那些文件为准，不要凭印象复述，也不要复制成第二套实现合同。

## 激活

仅在用户精确点名后运行。不要由“深度”“最大算力”“完整分析”等近似表达推断激活，也不要用任何其他技能、框架或简化流程替代本 Skill。

## 必读文件

- 读取顺序、全源与全候选闭包：[runtime-read-map.md](references/runtime-read-map.md)
- 源加载与降档规则：[worldview-loading.md](protocols/worldview-loading.md)
- 面向用户的交付合同：[answer-contract.md](references/answer-contract.md)
- 外部材料与来源质量：[retrieval-policy.md](references/retrieval-policy.md)、[source-quality-policy.md](references/source-quality-policy.md)
- 各阶段执行细则：`protocols/`；结构字段与严格拒绝条件：`schemas/xk-*.schema.json`
- 概念阅读材料：`references/ontology/cards/`、`references/ontology/bundles/`、`references/learning-packs/`

## 输入模式与运行方式

- 普通自然语言问题使用 `open-world`：主动检索现实材料并逐来源独立判断。
- 用户明确要求只使用给定材料时使用 `closed-input`：禁止外部事实混入。
- 默认以指令层完整执行 XK0—XK12 后直接作答，交付末尾附读取回执（见“读者交付”）。仅当用户明确要求“封存运行”时才使用 `scripts/xi_kari_runtime.py`：启动前核对 provider 可用（环境变量与流程见 [runtime.md](protocols/runtime.md) 与仓库 README），不可达时如实说明并回到指令层，不得带病启动；`execute` 与 `validate` 必须在相同环境变量取值下执行，复验退出码 0 且存在签名终态后才交付答案。
- 网络、权限或材料不足时保留条件路径并降档，不把记忆、模拟或用户立场冒充事实。

## 执行顺序（XK0—XK12，不得跳步）

`XK0` 问题合同、隐私与能力；`XK1` 源锁与全读；`XK2` 检索；`XK3` 证据冻结；`XK4` 全候选闭包；`XK5` 联合状态；`XK6` 三类变换；`XK7` 命题、机制与案例；`XK8` 三阶谱系；`XK9` 逐阶评价、红队与成对立场；`XK10` 五类裁决、选择与前瞻；`XK11` 读者投影与语义覆盖；`XK12` 新鲜验证与不可改写终态。阶段编号是本 Skill 的内部记号，每个阶段读什么、产出什么，以必读文件为准。

## 硬规则

1. 每次运行按序完整读取全部 21 卷框架原文并校验 source manifest；任何摘要、registry 或旧回答都不能替代原文。框架原文是本 Skill 的语义基准：外部材料只能校准现实事实、机制和案例，不得改写框架定义。
2. 扫描完整候选 census 和 registry，对所有候选给出独立终态；路由只决定深推演优先级，不能删减全候选处置。
3. 建立现实检索前沿、逐来源 assessment、证据谱系、冲突、未知和截止点；每条来源分别判断权威性、独立性、时间、谱系与利益关系。
4. 按 [local-world-model.md](protocols/local-world-model.md) 建立局部联合世界模型；对象边界、身份、尺度、成员关系、通道、时钟、分布、未知与残差不得无证据填充，每个证据引用必须解析到本轮冻结的命题—证据—来源支持身份。
5. 分开验证尺度变换、圈层关系变换和表示/表达转义；无真实通道不得更新状态，跨圈层每一跳重新检查边界、通道、身份和表示资格。
6. 按 [mechanism-and-case.md](protocols/mechanism-and-case.md) 比较简单基线、主解释、最强竞争解释、混合解释和残差解释；为主要机制配置明确标型的案例与反例。
7. 按 [three-order-inference.md](protocols/three-order-inference.md) 运行一至三阶递归、逐阶基线与敏感性，并按 [red-team-and-repair.md](protocols/red-team-and-repair.md) 执行红队与成对立场检验；前一阶失败时终止下游并如实标 `not_run`，递归深度不增加证据等级。
8. 按 [judgment-and-choice.md](protocols/judgment-and-choice.md) 分别冻结事实、结构、机制、预测、价值、责任、授权和行动排序；裁决只能引用已验证的命题—证据边与递归节点，授权必须由同一个主体—对象—单一动作—地域—有效期原子元组约束，数值预测保留校准依据。
9. 在 XK0 冻结用途、交付对象和隐私分类；逐个读者语义原子显式记录公开或保护性扣留，不存在默认公开，保护性扣留的原值不得进入任何交付。
10. 结束前从磁盘重读本轮工件做新鲜验证；只有验证闭合的终态才能完成或取消。失败时只修复真实且可归属的最早失效阶段及下游，不能补 marker、改状态记录或改报告伪装通过。

## 读者交付

按 [answer-contract.md](references/answer-contract.md)、[prose.md](protocols/prose.md) 与 [answer-composition.md](protocols/answer-composition.md)：先说现实关系和直接结论，再解释机制、竞争解释、案例、反例、三阶路径、撤回条件和行动边界。术语首次出现时立即用日常语言解释其额外区分；删除全部术语后，普通读者仍应能复述中心判断、因果链、成本承担者、最强反方和停止条件。禁止概念墙、机器字段、散列、JSON、未解释专业词和以篇幅冒充深度。

动态问题默认交付完整答案与配套工件，并把完整可读答案投影到聊天；用户要求简答时只压缩可见投影，不跳过内部运行。静态问题明确写“三阶推演不适用”，不得硬造递进故事。指令层运行在交付末尾明确声明本次未经 runtime 封存，并附一张 21 卷逐卷读取方式表（亲读全文／分段／子代理／未读）。

只公开证据边界、机制、状态变化、反例、判断理由和撤回条件，不公开隐藏思维链、工具试错或内部自我规划。

## 运行边界

每次运行建立独立的 run 输出目录；不得写入本 Skill 包目录或安装目录，运行状态只存在于该 run 目录内，不得创建任何跨运行共享状态。运行中新发现而未被框架定义的变量只能使用 `XK-PROV-*` 临时编号，不得偷偷升级为正式概念；框架缺口只能进入隔离候选台账，不能反向支持本轮命题、裁决或授权。
