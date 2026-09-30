---
id: V90-CANON-CM-LOAD
source_concept_id: CM-LOAD
framework_version: v9.0
---

# CM-LOAD

## 原文层

来源：`V90-P00897`

6.6　CM-LOAD 负荷、容量与恢复

来源：`V90-P00898`

基础推理依赖：D0、G2。 E4、CAUSAL 与 EVIDENCE 是方法门。需求与容量必须是同型量，或具有明确单位与转换映射；需求、可用容量、补给和溢出按同一窗口、同一位置测量；G2-instance 只支持已测通道及其相关维度。

来源：`V90-P00899`

机制链为：

来源：`V90-P00900`

同型需求进入指定通道 → 占用可用容量 → 形成即时缺口或跨边界溢出 → 减载/补给/扩容改变缺口 → 历史条件增量决定是否累积或迟恢复

来源：`V90-P00901`

CM-LOAD-instant 是瞬时分支，只要求同型需求—容量和同窗即时缺口，不要求 G3。CM-LOAD-cumulative 是累积分支：只有历史项改变后续容量或恢复，并由 G3-instance 支持时，才登记累积损伤或迟恢复。容量同步扩展可以吸收需求；瞬时缺口解除后可以没有任何持久差异。因此，负荷不必单调累积，瞬时过载不必导致损伤或崩溃。

来源：`V90-P00902`

负荷必须按位置与分布登记，不能只报告平均值；容量要区分峰值、持续值、替代通道与补给；恢复要区分表面输出恢复、K/F 恢复和内部余量恢复。不同类型量不能直接相减，恢复需求也不能直接生成任何主体的牺牲义务或授权。

来源：`V90-P00903`

恢复判断应同时说明恢复了什么、对谁、在什么支持条件下以及截至何时。实际输出的数量、质量、持续性与可达性，内部人员休整、备件、维护积压和资金接续，边界外新增的照护、通勤、借款或替代服务负担，以及后续中断和近失误，分别取证。灾前人口、当前人口、符合资格者和实际使用者不能在计算恢复比例时默默互换。对某项有限功能的确认，不要求其他全部结果同时恢复。

来源：`V90-P00904`

临时场所、持续外援或辅助设备可以构成真实的功能修复；依赖支持本身不是恢复失败。应核实支持的可持续性、到期点与替代承接是否已运行，并明确尚未经历的需求高峰、维护周期或季节性暴露。所谓假恢复，只宜指声明超出了证据支持的对象、人群、功能或持续条件，不由此推定欺骗。恢复后的再次失稳须分别比较旧损伤延续、储备未补回、支持中断、新冲击与测量口径改变，不能用一次新失败抹去此前准确限定的成果，也不能为验证恢复而撤走必要支持。

## 解释层

允许边界：仅在本项原文全部适用条件与分支条件内使用CM-LOAD；独立对象材料支持实例，定义和接口只确定意义。

禁止边界：普通学习不是CM-LEARNING别名；瞬时/基础模式不硬加G3。

## 依赖角色

| role | target | condition | basis |
| --- | --- | --- | --- |
| `inferential_requires` | `V90-CANON-D0` | base | source_layer/dependency_statements |
| `inferential_requires` | `V90-CANON-G2` | base | source_layer/dependency_statements |
| `inferential_requires` | `V90-CANON-G3` | cumulative | source_layer/blocks |
| `protocol_requires` | `V90-CANON-E4` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL-DE06B986` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-EVIDENCE` | base | source_layer/dependency_statements |
| `protocol_requires` | `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0` | base | source_layer/dependency_statements |

## source_undefined

- Task-specific empirical parameters and evidence cannot be supplied by the concept definition.
