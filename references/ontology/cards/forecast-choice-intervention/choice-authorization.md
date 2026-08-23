---
id: V82-CANON-SELECTION
qualified_id: choice:SEL-SYS-AGT-GOV
name: 三类选择、方案集与有限授权
family: forecast-choice-intervention
disposition: canonical_concept
source_authority: v8.2
covered_ids: V82-CANON-SELECTION,V82-CANON-NO-ACTION,V82-CANON-AUTHORIZATION,V82-CANON-CHOICE-AUTHORIZATION-BOUNDARY
---

# 选择、方案与授权桥

## 权威定义（v8.2）

选择至少分为 `SEL-SYS`（无统一主体的环境/反馈筛选）、`SEL-AGT`（有识别主体且受权限、选项、信息、能力、地域、期限约束的主体选择）和 `SEL-GOV`（有程序授权的集体治理）；三者不能互相偷换（`V82-P2609`-`V82-P2614`）。

方案集必须包含维持现状、主动行动、延迟、可逆试探、退出/转移和明确的 `no_action`；不行动仍有既有规则、时钟和不作为责任（`V82-P2245`-`V82-P2268`）。

## 允许推论

- 先登记事实、规范前提、价值冲突、受影响位置、权利底线、分配、风险、可逆性和信息价值，再比较选项。
- 检查“说不”的条件：强制、默认锁定、信息不对称、能力、拒绝安全和真实退出。
- 只有 SEL-AGT/SEL-GOV 能进入 `authorized`，且只限原子 J 元组覆盖的单一方案（`V82-P2637`-`V82-P2647`）。

## 非等价锁

预测、影响力、人数、效率、职位或技术能力都不能替换授权；SEL-SYS、SEL-AGT 和 SEL-GOV 的对象、责任和程序边界保持独立。

## 禁止跳跃

SEL-SYS 不具意图/正当性；SEL-AGT 不越过本人权限替别人决定；SEL-GOV 不以人数、效率、自称代表或法律形式替代少数保护；预测不能自动授权。

## 反例与失败条件

案例：一个可逆试探可以增加信息，却不能因为信息价值高就自动获得对他人施加不可逆干预的许可；反例是把“代表多数”写成无限期授权。

删掉 no_action、将维持现状和不行动混为一项、代表未获授权、异议未解决、O1-O3/PF/J 缺失或方案执行中变形时，最多 `under_review/paused`。

## 判断与行动上限

事实与前瞻只产生候选后果；有限选择是有条件、可撤回记录，不是模型命令。行动上限取描述、规范、保护、方案、J、O4、可逆性和期限的最窄交集。

## 申诉与回滚

状态迁移保留历史；停止触发器、授权撤销或期限到期进入 `stopped`；完成真实恢复、补救和版本写回才可 `rolled_back`/`closed`。

## 三阶推演接口

- 一阶：每个选项改变直接对象/资源/风险。
- 二阶：受影响位置、反馈、分配、退出和策略改变后续路径。
- 三阶：制度化、锁定、逆转、代际/跨圈层溢出必须单独评估；不行动也沿现有路径继续。

## source_undefined

v8.2 未定义跨法域统一的价值权重、效用总分或自动“最佳方案”；规范冲突和权利不可平均时标 `source_undefined` 并交由有资格主体/程序。

## 来源锚点

- [v8.2 reader 12](../../../source/v8.2/reader/12-conditional-forecast-choice.md): `V82-P2242`-`V82-P2301`。
- [v8.2 reader 14](../../../source/v8.2/reader/14-normative-selection.md): `V82-P2602`-`V82-P2667`。

## 原文定义区段

本卡的权威定义必须与无损阅读版连续联读；以下锚点是定位索引，不是删减后的替代文本。运行时先完整读取 21 卷，再回到这些锚点核对相邻段落、表格和适用边界。

- `V82-P2242`, `V82-P2245`, `V82-P2268`, `V82-P2606`, `V82-P2609`, `V82-P2611`, `V82-P2614`, `V82-P2637`, `V82-P2647`

## 解释层（非原文定义）

本卡解释层只说明如何把条件路径、规范前提、保护和授权边界接入回答；它不把预测、模型能力或内部闸门升级为现实许可。

## 必须联读的邻接概念

- `V82-CANON-APP-GATE`：`references/ontology/cards/forecast-choice-intervention/intervention-levels.md`

- `V82-CANON-EVENT`：`references/ontology/cards/forecast-choice-intervention/event-and-dynamics.md`

- `V82-CANON-FORECAST`：`references/ontology/cards/forecast-choice-intervention/conditional-forecast.md`

- `V82-CANON-PF`：`references/ontology/cards/forecast-choice-intervention/protection-and-intervention.md`

## 撤回条件

若对象边界、同一性 K、适用时间窗、关键源锚点、通道或竞争解释失效，撤回本卡支持的高档判断，保留候选、未知或 `source_undefined`；不得用解释层补齐缺失证据。
