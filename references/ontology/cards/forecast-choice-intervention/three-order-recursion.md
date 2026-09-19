---
id: V83-CANON-THREE-ORDER
qualified_id: dynamic:recursive-three-orders
name: 递归三阶推演
family: forecast-choice-intervention
disposition: canonical_concept
source_authority: v8.3
---

# 一至三阶推演合同

## 权威定义（v8.3）

默认递归上限是三阶：第一阶滚动直接状态；第二阶使用一阶状态改变行动集合、资源、反馈和策略；第三阶展开制度化、锁定、逆转和跨圈层溢出。每阶分别冻结、评价，不能合成总命中率；没有新外部材料时，递归深度不提升证据等级（`V83-P2187`-`V83-P2189`）。

## 允许推论

每个节点至少记录 `parent`、`input_state`、`state_delta`、`carrier/channel`、`scale_or_circle`、`clock`、`conditions`、`evidence`、`countermechanism`、`failure_condition`、`early_signal`、`reverse_signal`、`next` 和 `termination_reason`（`V83-P2061`-`V83-P2083`）。

## 禁止跳跃

三阶不是“短期/中期/长期”换名，不是因果必然，也不是层数越深证据越强；二阶已失败时不得无条件续写三阶。

## 反例与失败条件

关键通道缺失、身份/K 失效、分叉无区分信号、路径对小参数极敏感、隐私风险超过信息价值或复杂模型不优于简单基线时，暂停/降阶。

## 判断与行动上限

输出条件路径、竞争机制、信号和终止理由；不得把模拟三阶当事实、概率或授权。

## 申诉与回滚

保留原起点和每阶版本；真实中间结果到达后建立新冻结运行，不倒灌旧路径。错误路径可撤回下游结论并保留失败轨迹。

## 三阶推演接口

- 一阶：`event → direct state delta`。
- 二阶：`state delta → changed actions/resources/feedback/strategy`。
- 三阶：`changed conditions → institutionalization/lock-in/reversal/cross-circle spillover`。
- 每阶明确早期/反向信号、支持状态和停止条件；停止就输出“此路径在第 N 阶终止”。

## source_undefined

v8.3 未定义跨领域通用的三阶概率、深度评分或“第三阶必然制度化”；这些字段标 `source_undefined`。

## 来源锚点

- [v8.3 reader 11](../../../source/v8.3/reader/11-event-dynamic-inference.md): `V83-P1988`-`V83-P2063`。
- [v8.3 reader 12](../../../source/v8.3/reader/12-conditional-forecast-choice.md): `V83-P2184`-`V83-P2189`。

## 原文定义区段

本卡的权威定义必须与无损阅读版连续联读；以下锚点是定位索引，不是删减后的替代文本。运行时先完整读取 21 卷，再回到这些锚点核对相邻段落、表格和适用边界。

- `V83-P1988`, `V83-P1990`, `V83-P2006`, `V83-P2187`, `V83-P2189`

## 解释层（非原文定义）

本卡解释层只说明如何把条件路径、规范前提、保护和授权边界接入回答；它不把预测、模型能力或内部闸门升级为现实许可。

## 必须联读的邻接概念

- `V83-CANON-APP-GATE`：`references/ontology/cards/forecast-choice-intervention/intervention-levels.md`

- `V83-CANON-AUTHORIZATION`：`references/ontology/cards/forecast-choice-intervention/choice-authorization.md`

- `V83-CANON-EVENT`：`references/ontology/cards/forecast-choice-intervention/event-and-dynamics.md`

- `V83-CANON-FORECAST`：`references/ontology/cards/forecast-choice-intervention/conditional-forecast.md`

- `V83-CANON-NO-ACTION`：`references/ontology/cards/forecast-choice-intervention/choice-authorization.md`

- `V83-CANON-PF`：`references/ontology/cards/forecast-choice-intervention/protection-and-intervention.md`

- `V83-CANON-SELECTION`：`references/ontology/cards/forecast-choice-intervention/choice-authorization.md`

- `V83-CANON-T0-T4`：`references/ontology/cards/forecast-choice-intervention/intervention-levels.md`

## 撤回条件

若对象边界、同一性 K、适用时间窗、关键源锚点、通道或竞争解释失效，撤回本卡支持的高档判断，保留候选、未知或 `source_undefined`；不得用解释层补齐缺失证据。
