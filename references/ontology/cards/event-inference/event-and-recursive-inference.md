---
id: V82-CANON-CORE-EVENT-CONTRACT
covered_ids: V82-CANON-CORE-EVENT-CONTRACT,V82-CANON-CORE-JOINT-STATE-UPDATE,V82-CANON-CORE-INFERENCE-LOOP,V82-CANON-CORE-PROPAGATION-THRESHOLD,V82-CANON-CORE-FEEDBACK-CASCADE,V82-CANON-CORE-BRANCH-PATH,V82-CANON-CORE-VARIABLE-CANDIDATE,V82-CANON-CORE-SIMULATION-COUNTERFACTUAL,V82-CANON-CORE-RECURSIVE-FUTURE,V82-CANDIDATE-EVENT-EXAMPLE,V82-CANDIDATE-PROVISIONAL-VARIABLE
source_authority: v8.2
card_kind: shared
---

# 事件、路径图与多阶推演

## 联读范围

本卡覆盖第十一部分的事件合同、联合状态更新、九步闭环、分叉路径、模拟/反事实和多阶递归未来推演，并与第十二部分的前瞻登记相接。

## 原文锚点

- V82-P1933—V82-P1954：推演与叙事续写、事件合同
- V82-P1981—V82-P2131：更新式、九步闭环、传播/反馈、路径图、变量候选、模拟和递归未来
- V82-P0404—V82-P0405、V82-P2566—V82-P2598：停止与九闸边界

## 权威定义

事件推演从冻结快照注入事件，沿有证据的通道登记直接效应、返回反馈和跨圈层级联；在条件、阈值、行动者选择或外部扰动处建立分叉，并为每条路径登记早期信号、反向信号和停止条件（V82-P0404）。联合状态更新须记录对象、变量、通道、时间和不确定性，而不是把故事续写当作推演（V82-P1933、V82-P1954、V82-P1981）。模拟和反事实可以生成条件路径，但没有新外部观察、执行回执或独立裁定，递归深度不能提高事实地位（V82-P2106—V82-P2118、V82-P4613）。

## 解释层（非原文定义）

每个阶次都必须是状态/约束的真实更新，而非“短期/中期/长期”的换名：一阶写直接差分，二阶写反馈/资源/策略/事件生成条件，三阶写制度化、锁定、逆转或跨圈层溢出。路径节点要让读者能看到为什么、由什么承载、何时会失败。

## 适用前提

- 冻结事件、资料截止、对象/圈层、SP/T/K、状态和争议。
- 每条边登记 input_state、state_delta、carrier、scale_or_circle、clock、conditions、evidence、countermechanism、failure_condition、early_signal。
- 二阶边未成立时，不生成无条件三阶；保持分叉和残差。

## 允许推论

- 可生成并行条件路径、最小检验和早期/反向信号。
- 可提出变量候选，但标记为模型候选，不能升级为事实。
- 可把多阶递归作为情景展开；只有前瞻登记后才能使用有目标、有期限、可校准的前瞻语气。

## 禁止替换与常见误用

- 故事连贯 ≠ 事件证据；模拟 ≠ 观测；递归深度 ≠ 事实等级。
- 三阶 ≠ 把时间跨度换成三段文字。
- “将会/一定”不能替代条件和基线。
- 路径数量 ≠ 预测准确性；单一路径 ≠ 唯一未来。

## 反例与失效条件

- 事件来源、时间或争议未冻结。
- 通道、阈值、时延或受影响变量缺失。
- 路径节点没有反向信号或竞争机制。
- 二阶反馈被阻断，仍继续写制度化三阶。
- 仅靠内部模拟重复运行，没有新材料。

## 非等价锁

- 事件推演 ≠ 叙事续写；模拟/反事实 ≠ 观测；递归深度 ≠ 事实等级。
- 一阶直接差分 ≠ 二阶反馈/资源/策略条件；二阶未成立 ≠ 可以凑写三阶制度化。
- 路径数量 ≠ 预测准确性；单一路径 ≠ 唯一未来；变量候选 ≠ 现实变量。

## 案例与失效条件

- 事件来源、争议和时间窗未冻结：不建立路径图，只列事实问题清单。
- 路径节点缺 carrier、clock、evidence、countermechanism 或 failure_condition：该边保持候选并停止后续阶次。
- 仅重复内部模拟而没有外部观察、执行回执或独立裁定：递归结果仍是模拟，不提高证据档位。

## 撤回条件

新证据反驳关键边、对象 K 转换、路径早期信号失效、反向信号出现或新外部事实改变基线时，撤回对应阶次并保留失败记录。

## 三阶接口

- 一阶：直接状态后果。
- 二阶：行动、资源、反馈、策略和事件生成条件改变。
- 三阶：制度化、自我复制、锁定、逆转或跨圈层溢出。
- 三阶输出必须携带成立条件、早期信号、反向机制、失败和停止条件。

## 必须联读

core-boundary-contracts.md、operation-mechanisms.md、forecast-and-choice-interface.md、claim-roles-and-missing-states.md。

## source_undefined

具体事件事实、路径概率、行动者选择和制度落地由问题实例与外部材料提供；框架本身不填空。

## 原文定义区段

本卡的权威定义必须与无损阅读版连续联读；以下锚点是定位索引，不是删减后的替代文本。运行时先完整读取 21 卷，再回到这些锚点核对相邻段落、表格和适用边界。

- `V82-P0401`, `V82-P0402`, `V82-P0404`, `V82-P1933`, `V82-P1954`, `V82-P1960`, `V82-P1981`, `V82-P1982`, `V82-P1988`, `V82-P2007`, `V82-P2008`, `V82-P2029`, `V82-P2034`, `V82-P2035`, `V82-P2059`, `V82-P2061`, `V82-P2062`, `V82-P2083`, `V82-P2084`, `V82-P2085`, `V82-P2105`, `V82-P2106`, `V82-P2107`, `V82-P2109`, `V82-P2110`, `V82-P2118`, `V82-P2131`, `V82-P2599`

## 必须联读的邻接概念

- `V82-CANON-CORE-D0-OBJECT`：`references/ontology/cards/foundation-boundary/core-boundary-contracts.md`

- `V82-CANON-CORE-EVIDENCE-CONTRACT`：`references/ontology/cards/foundation-boundary/claim-roles-and-missing-states.md`
