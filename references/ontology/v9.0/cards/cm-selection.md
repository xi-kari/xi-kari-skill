---
id: V90-CANON-CM-SELECTION
source_concept_id: CM-SELECTION
framework_version: v9.0
---

# CM-SELECTION

## 原文层

来源：`V90-P00912`

6.8　CM-SELECTION 变异—差异保留—再生产

来源：`V90-P00913`

基础推理依赖：D1。 E4、CAUSAL 与 EVIDENCE 是方法门。该机制是独立操作化，不由“发生演化”这个定义自动推出，也不能由概念说明或框架叙述直接证明。

来源：`V90-P00914`

必须把三种输出分开：

来源：`V90-P00915`

CM-SELECTION-pattern：筛选模式。 条件为“V、D、R、下一轮、重复轮次、漂变竞争”：结果前定义可区分变异 V 及来源，在可比环境中观察超过阈值的差异结果 D，差异经保留 R 进入下一轮并在重复轮次中可复核，同时检验漂变、共同外因和抽样偏差。基础依赖只有 D1。

来源：`V90-P00916`

CM-SELECTION-carrier：具体机制。 条件为“指定保留或再生产通道、通道扰动或可识别自然变异”，在模式成立之外另加 G2-instance 定位承载机制。

来源：`V90-P00917`

CM-SELECTION-history：跨轮路径。 条件为“跨轮历史项条件增量、当前状态控制”，在模式成立之外另加 G3-instance。

来源：`V90-P00918`

只有变化而无 D，是变动；有一次差异而无 R、下一轮和重复轮次，是一次结果；漂变模型已经充分时，不登记筛选模式；候选再生产通道被扰动而保留不变时，不登记该具体机制。一次存续不等于差异保留，被保留者不因此更优、更高级或更正当。系统筛选不是行动主体选择，更不是集体治理选择：后两者分别需要主体、选项与决策证据，以及规范前提、J 轴授权和 O 程序。

## 解释层

允许边界：仅在本项原文全部适用条件与分支条件内使用CM-SELECTION；独立对象材料支持实例，定义和接口只确定意义。

禁止边界：普通学习不是CM-LEARNING别名；瞬时/基础模式不硬加G3。

## 依赖角色

| role | target | condition | basis |
| --- | --- | --- | --- |
| `inferential_requires` | `V90-CANON-D1` | base | source_layer/dependency_statements |
| `inferential_requires` | `V90-CANON-G2` | carrier | source_layer/blocks |
| `inferential_requires` | `V90-CANON-G3` | history | source_layer/blocks |
| `protocol_requires` | `V90-CANON-E4` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL-DE06B986` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-EVIDENCE` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0` | base | source_layer/dependency_statements |

## source_undefined

- Task-specific empirical parameters and evidence cannot be supplied by the concept definition.
