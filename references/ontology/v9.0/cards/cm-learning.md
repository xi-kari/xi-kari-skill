---
id: V90-CANON-CM-LEARNING
source_concept_id: CM-LEARNING
framework_version: v9.0
---

# CM-LEARNING

## 原文层

来源：`V90-P00875`

6.3　CM-LEARNING 反馈介导学习

来源：`V90-P00876`

推理依赖：CM-FEEDBACK、G3。 E4、CAUSAL 与 EVIDENCE 是方法门。学习不是反馈的同义词，而是反馈经过可保留更新并在重复轮次中产生历史条件增量的更窄机制。

来源：`V90-P00877`

使能条件是：有效反馈改变可定位的内部状态、参数、规则、记忆或结构；更新经明确载体持久保留，并在重复或多轮后续处理中继续参与；G3-instance 证明该历史项在控制当前注册状态后仍提供条件增量；相对于预注册基线或替代模型，预定任务的样本外结果出现可复核改变。机制链为：

来源：`V90-P00878`

有效反馈 → 内部更新 → 更新载体持久保留 → 进入重复后续轮次 → 历史条件增量 → 预定任务结果改变

来源：`V90-P00879`

一次参数变化、一次成功、一次写回或材料被归档都不足以证明学习。更新未保留、不进入后续轮次，结果只在一个样本出现，当前完整状态吸收全部历史增量，或变化只改善代理指标而不改变预定任务时，本节CM-LEARNING解释失效。即使学习成立，也不表示变得更好、拥有目标或获得行动授权。

来源：`V90-P00880`

目标本身发生改变时，应说明形成新目标的理由与决定程序，保留旧目标下的结果、失败和成本，再为新任务建立比较。不能用后来重构的目标把旧任务失败改写为成功。

来源：`V90-P00881`

本节的“学习解释失效”专指CM-LEARNING机制资格，不是说实际技能、知识或制度实践没有改变。一般学习的证据可以是可重复完成的新任务、保留并调用的技能、可追查的教学或组织过程；它是否有效、持久、跨情境迁移和改善生活，仍须分别判断。报告可以同时写明“做法已改变”“后续净效果尚未确定”“未满足CM-LEARNING窄合同”，而不将前三者压成一个通过或失败。〔研究16.02、25.01—25.08、31.08〕

## 解释层

允许边界：反馈、保留、多轮、G3及任务比较均满足才登记窄机制。

禁止边界：一次更新或普通学习直接通过；更换目标抹去旧失败。

## 依赖角色

| role | target | condition | basis |
| --- | --- | --- | --- |
| `inferential_requires` | `V90-CANON-CM-FEEDBACK` | base | source_layer/dependency_statements |
| `inferential_requires` | `V90-CANON-G3` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-CANON-E4` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL-DE06B986` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-EVIDENCE` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0` | base | source_layer/dependency_statements |

## source_undefined

- Task-specific empirical parameters and evidence cannot be supplied by the concept definition.
