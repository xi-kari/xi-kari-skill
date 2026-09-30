---
id: V90-CANON-SELECTED-ACTION-V90-B01204-E9E02DC68B
source_concept_id: selected_action@V90-B01204
framework_version: v9.0
---

# selected_action@V90-B01204

## 原文层

来源：`V90-P02506`

SEL-SYS 的另一类方案是 system_variant，用于比较不同环境或保留机制下的差异结果，不是让系统作决定。SEL-AGT 和 SEL-GOV 可以包含 external_action，但进入 authorized 时必须冻结一个外部行动方案；随后由外部 selected_action 记录逐项绑定同一选项、主体、对象、动作、地域和期限。

来源：`V90-P02519`

jurisdiction_axis 固定来源、范围和期限。每个方案的 territory 必须等于该范围，validity_interval 必须落在该期限内。进入外部行动时，选择记录、所选方案、selected_action 和 J 元组必须逐项相同。授权来源存在不等于法律有效，法律有效也不等于规范正当；O3 必须分别登记。

来源：`V90-P02561`

干涉只消费已经存在的选择与授权，不制造授权。现实行动必须绑定唯一 selected_action，并同时具备：通过的 C12 十项桥接记录、运行时显式 N 前提、O1-O4、完整保护底板、当前有效且经独立复核的 J 原子授权。J 元组必须同时覆盖同一决策主体、同一对象、同一动作、同一地域和完整期限；一条无关但有效的授权不能为拟议行动背书。

## 解释层

允许边界：SEL-SYS 的另一类方案是 system_variant，用于比较不同环境或保留机制下的差异结果，不是让系统作决定。SEL-AGT 和 SEL-GOV 可以包含 external_action，但进入 authorized 时必须冻结一个外部行动方案；随后由外部 selected_action 记录逐项绑定同一选项、主体、对象、动作、地域和期限。

禁止边界：唯一已选外部行动与同方案主体对象动作地域期限及J逐项绑定

## 依赖角色

| role | target | condition | basis |
| --- | --- | --- | --- |
| `protocol_requires` | `V90-CANON-SCALE-AXIS-J` | 与已选external_action逐项同一原子J，不选no_action | application candidate adjudication |

## source_undefined

- 无作为开放默认值登记的源未定义字段。
