---
id: V90-CANON-GOV-04
source_concept_id: GOV-04
framework_version: v9.0
---

# GOV-04

## 原文层

来源：`V90-P02708`

COUNTEREXAMPLE-REGISTRY：记反例对象、尺度窗口、可观察事实、非噪声理由、原解释、替代解释、处置要求和后续信号。

来源：`V90-P02710`

CLAIM-REGISTRY：记断言文本、类型、对象、尺度、受影响位置、证据、反证、替代解释、撤回条件、行动上限与公开状态。

来源：`V90-P02711`

FORECAST-REGISTRY：记预测、时间窗口、触发、早期信号、反向信号、竞争预测与到期结果。它是条件前瞻，不是命运判决。

来源：`V90-P02713`

以本框架名义形成的正式判断，必须有相应CLAIM-REGISTRY记录，才能取得框架的公开发布或高影响使用资格。普通讨论、独立领域研究和有依据的局部意见，按其自身任务承担来源、纠错与用途责任，不因没有本框架编号就失去知识地位。案例留痕多不等于更普遍，内部挑选案例也不等于外部验证；进入组织处置或自动化决定时，继续适用强判断与授权条件。

来源：`V90-P02714`

治理变更另有七类运行时注册表：canonical actor、证据、利益关系、授权、外部评审、异议和结构化 VERSION-LOG。所有 evidence_ref 必须解析到完整性为 verified 的证据记录；评审者、决定成员与授权主体必须使用 canonical actor ID，并逐对检查其与提案者的经费、评价、身份、晋升、控制和商业利益关系。别名只能检索，不能代替身份；授权签发者不得同时是持有人或提案者。

来源：`V90-P02707`

五类权威记录彼此关联，却不互相代替：

来源：`V90-P02709`

CASE-REGISTRY：同时保存成功、失败、早期消散、进程未结、反例、无法判定和被排除案例。被排除案例要记录“资料不足本身是否是框架盲区”。

来源：`V90-P02712`

VERSION-LOG：把反例、边界收缩、降级、暂停、发布阻断、撤回、替代、退休、回滚和补救写成公开账本。

## 解释层

允许边界：五类权威记录彼此关联，却不互相代替：

禁止边界：五权威记录与七治理registry分工，正式发布资格不否认普通知识

## 依赖角色

| role | target | condition | basis |
| --- | --- | --- | --- |
| `protocol_requires` | `V90-CANON-CLAIM-REGISTRY` | 五类记录关联但不互代，正式框架发布资格非普通知识存在门 | application candidate adjudication |
| `protocol_requires` | `V90-CANON-COUNTEREXAMPLE-REGISTRY` | 五类记录关联但不互代，正式框架发布资格非普通知识存在门 | application candidate adjudication |
| `protocol_requires` | `V90-CANON-FORECAST-REGISTRY` | 五类记录关联但不互代，正式框架发布资格非普通知识存在门 | application candidate adjudication |
| `protocol_requires` | `V90-CANON-VERSION-LOG` | 五类记录关联但不互代，正式框架发布资格非普通知识存在门 | application candidate adjudication |
| `protocol_requires` | `V90-EXTERNAL-GATE-CASE-REGISTRY-7AA5992D` | 五类记录关联但不互代，正式框架发布资格非普通知识存在门 | application candidate adjudication |

## source_undefined

- 无作为开放默认值登记的源未定义字段。
