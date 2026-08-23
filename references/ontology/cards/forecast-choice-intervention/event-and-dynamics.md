---
id: V82-CANON-EVENT
qualified_id: dynamic:event-contract
name: 事件合同与动态推演入口
family: forecast-choice-intervention
disposition: canonical_concept
source_authority: v8.2
---

# 事件合同与动态推演入口

## 权威定义（v8.2）

动态推演不是断言世界必然如何，而是从冻结联合状态出发，检查事件后哪些变量先改变、影响沿何通道传播、何处有时延/阈值/反馈/级联/分叉（`V82-P1931`-`V82-P1935`）。事件类型必须区分观察到、被报告、计划中、假设性和模拟；模拟只属于模型状态，不能回写现实事实（`V82-P1954`-`V82-P1980`）。

## 允许推论

- 冻结对象、A/C/R、M/Ψ、时钟、证据截止、未知和模型版本。
- 每个事件记录 ID、时间/窗口、观察时间、来源、受影响行动者/圈层、通道、直接变化、证据、争议、竞争解释、可逆性、持续时间和后续观测。
- 传播必须分开记录信号到达、体验变化和实际资源/行为/规则/关系改变（`V82-P2007`-`V82-P2033`）。

## 禁止跳跃

传闻不等于事实，计划不等于执行，假设不等于现实，模拟不等于观察；相关共现不等于通道或反馈。

## 反例与失败条件

对象/事件类型不明、通道缺失、参数伪精确、无竞争解释或路径只是叙事续写时，停止在未知或候选变量。

## 判断与行动上限

事件推演最多生成条件路径、信号和残差；未经外部授权的行动只能作为假设情景，不能写成执行指令。

## 申诉与回滚

每次运行冻结并追加，不覆盖原运行；真实结果到达后记录支持/偏离、基线、校准和模型降级。

## 三阶推演接口

- 一阶：直接效应（事件触达的状态差）。
- 二阶：行动、资源、反馈、策略和生成条件变化。
- 三阶：制度化、自我复制、锁定、逆转或跨圈层级联；每一步都要有通道、条件、证据、反向机制、失败条件和早期信号。

## source_undefined

v8.2 不提供唯一真实更新函数 F、无条件概率或“叙事连贯即可能”规则；这些字段标 `source_undefined`。

## 来源锚点

- [v8.2 reader 11](../../../source/v8.2/reader/11-event-dynamic-inference.md): `V82-P1931`-`V82-P2086`。

## 原文定义区段

本卡的权威定义必须与无损阅读版连续联读；以下锚点是定位索引，不是删减后的替代文本。运行时先完整读取 21 卷，再回到这些锚点核对相邻段落、表格和适用边界。

- `V82-P1932`, `V82-P1954`, `V82-P1955`, `V82-P1980`

## 解释层（非原文定义）

本卡解释层只说明如何把条件路径、规范前提、保护和授权边界接入回答；它不把预测、模型能力或内部闸门升级为现实许可。

## 必须联读的邻接概念

- `V82-CANON-APP-GATE`：`references/ontology/cards/forecast-choice-intervention/intervention-levels.md`

- `V82-CANON-AUTHORIZATION`：`references/ontology/cards/forecast-choice-intervention/choice-authorization.md`

- `V82-CANON-FORECAST`：`references/ontology/cards/forecast-choice-intervention/conditional-forecast.md`

- `V82-CANON-NO-ACTION`：`references/ontology/cards/forecast-choice-intervention/choice-authorization.md`

- `V82-CANON-PF`：`references/ontology/cards/forecast-choice-intervention/protection-and-intervention.md`

- `V82-CANON-SELECTION`：`references/ontology/cards/forecast-choice-intervention/choice-authorization.md`

- `V82-CANON-T0-T4`：`references/ontology/cards/forecast-choice-intervention/intervention-levels.md`

- `V82-CANON-THREE-ORDER`：`references/ontology/cards/forecast-choice-intervention/three-order-recursion.md`

## 撤回条件

若对象边界、同一性 K、适用时间窗、关键源锚点、通道或竞争解释失效，撤回本卡支持的高档判断，保留候选、未知或 `source_undefined`；不得用解释层补齐缺失证据。
