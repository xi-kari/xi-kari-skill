---
id: V83-CANON-FORECAST
qualified_id: forecast:conditional
name: 条件前瞻
family: forecast-choice-intervention
disposition: canonical_concept
source_authority: v8.3
---

# 条件前瞻

## 权威定义（v8.3）

条件前瞻承担可失败的未来判断，但必须与解释、推演和有限选择分层。每条前瞻在输入截止、结果出现前冻结目标、期限、对象/圈层、基线、机制、路径、表达、校准、信号、暂停、退役和回写字段（`V83-P2133`-`V83-P2156`；`V83-P2157`-`V83-P2183`）。

## 允许推论

- 目标必须可判定，期限与机制时钟匹配；比较复杂模型与复杂度匹配的简单基线。
- 证据足够才给概率；样本有限给支持等级/排序；稀疏时给条件方向和最小观察。
- 到期状态可为 supported、unsupported、undecided、target_invalid 或 unevaluable（`V83-P2239`-`V83-P2241`）。

## 禁止跳跃

解释不证明未来；前瞻不生成价值或权限；结果后改变目标/期限/圈层/路径不能保留原成功资格。

## 反例与失败条件

目标同一性不稳、输入泄漏、无简单基线、只挑命中案例、校准恶化、误差集中于低权力位置或新变量事后提出时，降级或不发布。

## 判断与行动上限

输出可校准、可失败的条件判断；不能因高概率或模型推荐强迫他人承担成本。

## 申诉与回滚

保留失败、未决、目标失效和无法评价；前瞻记录公开可复核，误用为筛选/监控/惩罚时阻断并撤回。

## 三阶推演接口

- 一阶：目标窗口内直接路径和早期信号。
- 二阶：行动者选择、资源、反馈和策略改变前瞻路径。
- 三阶：制度化、锁定、逆转、跨圈层溢出需独立观测/新运行；没有新外部材料仍为模拟。

## source_undefined

v8.3 未给任意领域默认概率、校准阈值或预测“命中”定义；场景参数必须由外部程序确定并标 `source_undefined`。

## 来源锚点

- [v8.3 reader 12](../../../source/v8.3/reader/12-conditional-forecast-choice.md): `V83-P2157`-`V83-P2244`。
- [v8.3 reader 16](../../../source/v8.3/reader/16-governance.md): `V83-P2896`-`V83-P2898`。

## 原文定义区段

本卡的权威定义必须与无损阅读版连续联读；以下锚点是定位索引，不是删减后的替代文本。运行时先完整读取 21 卷，再回到这些锚点核对相邻段落、表格和适用边界。

- `V83-P2133`, `V83-P2157`, `V83-P2184`, `V83-P2240`

## 解释层（非原文定义）

本卡解释层只说明如何把条件路径、规范前提、保护和授权边界接入回答；它不把预测、模型能力或内部闸门升级为现实许可。

## 必须联读的邻接概念

- `V83-CANON-APP-GATE`：`references/ontology/cards/forecast-choice-intervention/intervention-levels.md`

- `V83-CANON-AUTHORIZATION`：`references/ontology/cards/forecast-choice-intervention/choice-authorization.md`

- `V83-CANON-EVENT`：`references/ontology/cards/forecast-choice-intervention/event-and-dynamics.md`

- `V83-CANON-NO-ACTION`：`references/ontology/cards/forecast-choice-intervention/choice-authorization.md`

- `V83-CANON-PF`：`references/ontology/cards/forecast-choice-intervention/protection-and-intervention.md`

- `V83-CANON-SELECTION`：`references/ontology/cards/forecast-choice-intervention/choice-authorization.md`

- `V83-CANON-T0-T4`：`references/ontology/cards/forecast-choice-intervention/intervention-levels.md`

- `V83-CANON-THREE-ORDER`：`references/ontology/cards/forecast-choice-intervention/three-order-recursion.md`

## 撤回条件

若对象边界、同一性 K、适用时间窗、关键源锚点、通道或竞争解释失效，撤回本卡支持的高档判断，保留候选、未知或 `source_undefined`；不得用解释层补齐缺失证据。
