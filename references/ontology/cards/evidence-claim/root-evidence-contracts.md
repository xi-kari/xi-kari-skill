---
id: V82-CANON-CORE-CAUSAL-CONTRACT
covered_ids: V82-CANON-CORE-CAUSAL-CONTRACT,V82-CANON-CORE-ANALOGY-CONTRACT,V82-CANON-CORE-G1-CONDITIONAL-GAIN,V82-CANON-CORE-G2-CHANNEL-EFFECT,V82-CANON-CORE-G3-HISTORY-INCREMENT,V82-CANON-CORE-G4-SCALE-CLOSURE,V82-CANON-CORE-EPISTEMIC-E1-E5,V82-CANON-CORE-INFERENCE-C1-C12,V82-CANON-CORE-ROOT-INSTANCE-CONTRACT,V82-CANON-CORE-HUMAN-EMPIRICAL-INSTANCE-CONTRACT
source_authority: v8.2
card_kind: shared
---

# 根假设、因果与证据合同

## 联读范围

本卡覆盖 G1—G4、E1—E5、C1—C12 的核心责任。G 是实例化的经验门，E 是认识论限制，C 是条件推论，不是一个由框架自证的世界定律集合。

## 原文锚点

- V82-P0587—V82-P0685：根实例、G1—G4、E1—E5 与推论合同入口
- V82-T006、V82-P0588—V82-P0626：结果前/结果后两段、决策规则、四态结果与支持资格
- V82-P0628—V82-P0647、V82-T007：人类经验实例合同、H1/H4/H5 子型与支持边界
- V82-P0688—V82-P0829：C1—C12
- V82-P0842—V82-P0860：组合推论树与停止位置
- V82-P0484—V82-P0486：因果契约

## 权威定义

- G1 询问候选分组相对复杂度匹配基线是否有条件增益；G2 询问指定通道/载体在注册干预或自然变异下是否产生目标转移；G3 询问历史项在控制当前状态后是否增加未来路径信息；G4 询问尺度映射、对象或干预转换是否按预注册标准闭合（V82-P0648—V82-P0663）。
- E1—E5 分别约束对象声明、观察位置/模型限制、条件性观测参与、竞争解释与残差、跨尺度迁移（V82-P0671—V82-P0680）。
- C1—C12 是依赖条件、证据门和规范桥接组成的条件推论合同；它们只有在对应实例和前提成立时才可使用，根层到达预先声明的停止位置（V82-P0685—V82-P0846）。
- 因果主张必须登记原因、结果、时间顺序、通道、对象/尺度、窗口、目标变量和可区分反事实；相关、时序和机制故事只能产生候选路径（V82-P0485—V82-P0486）。
- 根实例把结果前冻结段与结果后追加段分开，并封闭为 `supported`、`unsupported_or_undecided`、`null_supported`、`not_evaluated` 四态；只有合格的 confirmatory/replication 实例可支撑 C 推论（V82-P0585—V82-P0626）。
- `human_empirical_instance_contract` 是 H1、H4、H5 的独立正式实例合同：身份字段以 `claim_id` 取代 `root_id`，其余冻结、结果、缺失、版本、偏离、正向门、零结论门与证据制品纪律和根实例合同同构；经验真值只属于具体 H-instance（V82-P0628—V82-P0647）。

## 解释层（非原文定义）

把 G 当作四种不同实验问题，把 E 当作“不能越过的认识边界”，把 C 当作“只有满足前提才可走的推理边”。模型可以提出最小检验，但不能把模板名称当结果。

## 适用前提

- 结果前冻结对象、子型、目标、基线/零模型、阈值、控制、评价指标、决策规则、证伪与暂停条件。
- 对因果路径至少登记可阻断/替换的通道和替代解释。
- 需跨尺度时，补齐 D3/E5 桥接证据和损失审计。

## 允许推论

- 可将支持状态区分为 supported、unsupported_or_undecided、null_supported、not_evaluated。
- 可根据失败门定位降档位置，保留残差和最小补证。
- 可把 C 合同用于条件性一至三阶路径，而非无条件预测。

## 禁止替换与常见误用

- G1—G4 模板 ≠ 普遍定律。
- 通过 G1 ≠ 证明对象本体；通过 G2 ≠ 证明所有通道都有效；G3 ≠ 命运；G4 ≠ 任意尺度迁移必然成功。
- 相关、叙事顺序、单一案例或模型拟合 ≠ 因果桥。
- 正向门未通过 ≠ 自动支持零模型。

## 反例与失效条件

- 复杂模型与简单基线无样本外增益：G1 未通过。
- 阻断通道后结果不变或替代通道同样解释：G2 不足。
- 历史标签在控制当前状态后没有条件增量：G3 不足。
- 尺度映射丢失关键变量、误差超适用窗或对象 K 不闭合：G4 不足。

## 非等价锁

- G 模板 ≠ G-instance；结果前合同 ≠ 结果后解释；正向门未过 ≠ 零模型已获支持。
- H1/H4/H5 的抽象命题、名称或接口字段 ≠ H1-instance/H4-instance/H5-instance；`human_empirical_instance_contract` ≠ 根实例合同的别名。
- `supported`、`unsupported_or_undecided`、`null_supported` 与 `not_evaluated` 不互换。
- 探索、草案、证据后偏离或内部模拟 ≠ 可支撑 C 的确认/复制实例。

## 案例与失效条件

- 看到结果后改换子型、成功判据、N0、阈值或主目标：实例失去支持资格，旧结果只保留为偏离记录。
- 正向门失败但未冻结零结论三门：结论保持 `unsupported_or_undecided`，不能改写为 `null_supported`。
- 只有框架内部定义、标签或分析日志而无外部材料：根实例记 `not_evaluated` 或候选，不进入经验推论。

## 撤回条件

出现事后改写阈值/子型/目标、独立复核失败、竞争解释未能区分、样本外失效或关键桥接证据撤回时，撤回经验支持并回到候选/未决。

## 三阶接口

一阶对应指定通道的状态效应；二阶对应历史/反馈/尺度条件如何改变后续概率或约束；三阶只在重复写回、制度化或跨圈层传导有证据时展开。未过 G2/G3/G4 的路径不得进入三阶。

## 必须联读

core-boundary-contracts.md、universal-primitives.md、scale-profiles-and-operators.md、event-and-recursive-inference.md。

## source_undefined

具体实验设计、样本量、阈值和现实概率不由 v8.2 自动提供，必须由问题领域和外部资料补足。

## 原文定义区段

本卡的权威定义必须与无损阅读版连续联读；以下锚点是定位索引，不是删减后的替代文本。运行时先完整读取 21 卷，再回到这些锚点核对相邻段落、表格和适用边界。

- `V82-P0484`, `V82-P0485`, `V82-P0486`, `V82-P0490`, `V82-P0491`, `V82-P0492`, `V82-P0585`, `V82-P0587`, `V82-P0588`, `V82-T006`, `V82-P0622`, `V82-P0623`, `V82-P0624`, `V82-P0625`, `V82-P0626`, `V82-P0628`, `V82-P0629`, `V82-T007`, `V82-P0646`, `V82-P0647`, `V82-P0648`, `V82-P0649`, `V82-P0650`, `V82-P0651`, `V82-P0652`, `V82-P0653`, `V82-P0654`, `V82-P0655`, `V82-P0656`, `V82-P0657`, `V82-P0658`, `V82-P0659`, `V82-P0660`, `V82-P0661`, `V82-P0662`, `V82-P0663`, `V82-P0671`, `V82-P0672`, `V82-P0674`, `V82-P0676`, `V82-P0678`, `V82-P0680`, `V82-P0683`, `V82-P0684`, `V82-P0685`, `V82-P0687`, `V82-P0726`, `V82-P0776`, `V82-P0828`, `V82-P0842`, `V82-P0846`

## 必须联读的邻接概念

- `V82-CANON-CORE-D0-OBJECT`：`references/ontology/cards/foundation-boundary/core-boundary-contracts.md`

- `V82-CANON-CORE-EVIDENCE-CONTRACT`：`references/ontology/cards/foundation-boundary/claim-roles-and-missing-states.md`

- `V82-CANON-CORE-HUMAN-EMPIRICAL-INSTANCE-CONTRACT`：本卡中的人类经验实例合同区段。

- `V82-CANON-H1`、`V82-CANON-H4`、`V82-CANON-H5`：`references/ontology/cards/human-actor/h1-h6-boundaries.md`
