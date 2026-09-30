---
id: V90-CANON-CM-FEEDBACK
source_concept_id: CM-FEEDBACK
framework_version: v9.0
---

# CM-FEEDBACK

## 原文层

来源：`V90-P00870`

6.2　CM-FEEDBACK 有效反馈

来源：`V90-P00871`

推理依赖：D2、G2。 E4、CAUSAL 与 EVIDENCE 是方法门，不是额外经验原因。有效反馈不以 G3 为前提。

来源：`V90-P00872`

使能条件是：先前状态或输出经已由 G2-instance 识别的指定返回通道进入后续过程；相对于无返回或阻断条件，至少一个后续状态、转移概率或约束发生超过阈值的差异；时间顺序和被改变字段在结果前已登记。机制链为：

来源：`V90-P00873`

先前状态或输出 → 返回信号 → 指定通道传导 → 接收位置摄取 → 后续状态、概率或约束改变 → 阻断反事实复核

来源：`V90-P00874`

最低证据包括通过预注册门的 G2-instance、返回通道与接收位置、时间顺序、被改变字段、后续差异，以及无返回或通道阻断比较。信号到达但后续转移不变，变化由独立共同输入解释，或切断返回通道后差异仍保持不变时，不登记有效反馈。有效反馈只说明返回造成了一次后续改变；它不等于学习、修复、正向结果，也不要求持久历史留痕。

## 解释层

允许边界：仅在本项原文全部适用条件与分支条件内使用CM-FEEDBACK；独立对象材料支持实例，定义和接口只确定意义。

禁止边界：普通学习不是CM-LEARNING别名；瞬时/基础模式不硬加G3。

## 依赖角色

| role | target | condition | basis |
| --- | --- | --- | --- |
| `inferential_requires` | `V90-CANON-D2` | base | source_layer/dependency_statements |
| `inferential_requires` | `V90-CANON-G2` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-CANON-E4` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL-DE06B986` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-EVIDENCE` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0` | base | source_layer/dependency_statements |

## source_undefined

- Task-specific empirical parameters and evidence cannot be supplied by the concept definition.
