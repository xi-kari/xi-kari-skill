---
id: V90-CANON-CM-PHASE
source_concept_id: CM-PHASE
framework_version: v9.0
---

# CM-PHASE

## 原文层

来源：`V90-P00905`

6.7　CM-PHASE 相位与阈值转换

来源：`V90-P00906`

基础推理依赖：D0、D1。 E4 与 EVIDENCE 是相位模式分支的共同方法门；CAUSAL 只在因果触发与迟滞分支追加，不是基础模式分类的前置门。相位的基础识别不要求 G3：同一候选对象合同和 K 下，只要预先登记状态变量、候选参数或触发条件、阈值，以及噪声和分箱稳健性，就可以检验至少两个可重复区分的运转区间。

来源：`V90-P00907`

机制链分为三层：

来源：`V90-P00908`

CM-PHASE-pattern：相位模式。 条件为“同一K、两个可复核区间、预定阈值模式”。它只登记区间—阈值关系，不宣称触发因果。

来源：`V90-P00909`

CM-PHASE-causal-trigger：因果触发。 条件为“指定触发通道、通道干预或可识别自然变异”，并另加 G2-instance 定位触发作用。

来源：`V90-P00910`

CM-PHASE-hysteretic：迟滞分支。 只有主张迟滞、路径或迟恢复时才追加 G3-instance，检验历史条件增量。

来源：`V90-P00911`

连续趋势若在同一状态分布内充分解释变化、阈值随分箱任意移动，或转移前 K 已失效，应撤回相位结论，分别改记为连续变化、测量划分效应或对象转换/解体。可逆相位不必具有历史路径；只有迟滞分支才需要 G3。相位也不构成 S0—S6 的必经成熟序列，新相位不因此更高、更好或拥有更大授权。

## 解释层

允许边界：仅在本项原文全部适用条件与分支条件内使用CM-PHASE；独立对象材料支持实例，定义和接口只确定意义。

禁止边界：普通学习不是CM-LEARNING别名；瞬时/基础模式不硬加G3。

## 依赖角色

| role | target | condition | basis |
| --- | --- | --- | --- |
| `inferential_requires` | `V90-CANON-D0` | base | source_layer/dependency_statements |
| `inferential_requires` | `V90-CANON-D1` | base | source_layer/dependency_statements |
| `inferential_requires` | `V90-CANON-G2` | causal-trigger | source_layer/blocks |
| `inferential_requires` | `V90-CANON-G3` | hysteretic | source_layer/blocks |
| `protocol_requires` | `V90-CANON-E4` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL` | causal-trigger_or_hysteretic_only | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL-DE06B986` | causal-trigger_or_hysteretic_only | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-EVIDENCE` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0` | base | source_layer/dependency_statements |

## source_undefined

- Task-specific empirical parameters and evidence cannot be supplied by the concept definition.
