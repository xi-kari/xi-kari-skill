---
id: V90-CANON-FLOW-EXECUTION-RECORD-V90-B01161-1DF320BE64
source_concept_id: flow_execution_record@V90-B01161
framework_version: v9.0
---

# flow_execution_record@V90-B01161

## 原文层

来源：`V90-P02434`

每次工具运行生成一个字段闭合的 flow_execution_record。它登记对象和尺度记录、L1-L3 档位、IT1-IT4 结果、IG1-IG7 结果、是否运行五闸十三步、是否触发 SJ1-SJ8、证据、替代解释、不确定性、输出类别、判断/行动上限、规范移交、申诉、回滚和状态。

来源：`V90-P02435`

行动上限使用封闭输出上限格：description_only、diagnostic_only、requirements_only。每一档都固定可出现的输出类别，并且 can_authorize=false、can_execute=false；调用者不能在自由文本中自报“已经授权”，也不能自行扩展允许类别。action_requirements 只是对外部选择与授权程序提出所需条件，不是可执行命令。

来源：`V90-P02436`

normative_handoff 中的选择记录、C12 闸与 J 授权只能写成规范缺失状态，或写成带 record_type、外部记录 ID、报告状态和独立 verification_ref 的外部核验引用。所有 record_id、verification_ref 和程序 ID 都必须是无首尾空白的外部引用；none、self、self:* 及其大小写或空白变体一律无效。selection:passed、C12:passed、J:authorized 之类字符串自报同样无效；工具只链接和核验外部记录，不在本记录中生成这些状态。

来源：`V90-P02437`

结果状态要保持可区分：passed 表示该项记录门通过，failed 表示已运行但失败，not_run 表示因前闸或范围限制没有运行；unknown、not_applicable、not_observable 与 withheld_for_protection 仍是四种不同缺失状态。失败不能改写成不适用，保护性隐匿不能改写成不存在。

来源：`V90-P02438`

运行记录的 authorization_effect 恒为 none。即使规范选择、C12、J 和 O 的外部引用均已存在，本记录也只是核对和移交它们，不自行铸造授权。所有已复核输出必须保留可达申诉与实际撤回/纠正路径；不能撤回的工具结论不得进入高影响难逆用途。

## 解释层

允许边界：每次工具运行生成一个字段闭合的 flow_execution_record。它登记对象和尺度记录、L1-L3 档位、IT1-IT4 结果、IG1-IG7 结果、是否运行五闸十三步、是否触发 SJ1-SJ8、证据、替代解释、不确定性、输出类别、判断/行动上限、规范移交、申诉、回滚和状态。

禁止边界：字段闭合运行记录与缺失/结果词表；authorization_effect恒none，外部核验不能自发状态

## 依赖角色

| role | target | condition | basis |
| --- | --- | --- | --- |
| `protocol_requires` | `V90-CANON-C12` | 只核外部normative_handoff引用或记录缺失，不在记录内自铸状态 | application candidate adjudication |

## source_undefined

- 实际外部record_id
- 独立verification_ref
- 程序ID
