---
id: V90-CANON-B493-OPERATOR-IDS-SELECTED-OPERATOR-BRANCH-CLAIM-E248C6B5E6
source_concept_id: 原文规则@B493:每条原子记录的 operator_ids 必须且只能包含一个算子，selected_operator_branch 再从该算子的分支注册表中唯一选择内部支路，最后用 claim_mode 声明本次评价的模式：descriptive_mapping（描述映射）、root_hypothesis（根假设实例）、causal（因果桥）、object_conversion（对象转换）或 intervention_conversion（干预转换）
framework_version: v9.0
---

# 原文规则@B493:每条原子记录的 operator_ids 必须且只能包含一个算子，selected_operator_branch 再从该算子的分支注册表中唯一选择内部支路，最后用 claim_mode 声明本次评价的模式：descriptive_mapping（描述映射）、root_hypothesis（根假设实例）、causal（因果桥）、object_conversion（对象转换）或 intervention_conversion（干预转换）

## 原文层

来源：`V90-P00701`

每条原子记录的 operator_ids 必须且只能包含一个算子，selected_operator_branch 再从该算子的分支注册表中唯一选择内部支路，最后用 claim_mode 声明本次评价的模式：descriptive_mapping（描述映射）、root_hypothesis（根假设实例）、causal（因果桥）、object_conversion（对象转换）或 intervention_conversion（干预转换）。分支注册表明确每个支路允许哪些模式；三者必须相容并在看结果前冻结，不能因正向门失败切换支路或退回较宽松的描述模式，也不能把一个模式的材料用于救援另一个模式。若一个实际过程包含多个算子，须拆成有序原子记录链：前一步的目标对象与 SP1 对齐后一步的源对象与 SP0，每一步各自登记结果状态、证据、损失和误差。一个总结果不能替多步分别结案。

## 解释层

允许边界：每条原子记录的 operator_ids 必须且只能包含一个算子，selected_operator_branch 再从该算子的分支注册表中唯一选择内部支路，最后用 claim_mode 声明本次评价的模式：descriptive_mapping（描述映射）、root_hypothesis（根假设实例）、causal（因果桥）、object_conversion（对象转换）或 intervention_conversion（干预转换）。分支注册表明确每个支路允许哪些模式；三者必须相容并在看结果前冻结，不能因正向门失败切换支路或退回较宽松的描述模式，也不能把一个模式的材料用于救援另一个模式。若一个实际过程包含多个算子，须拆成有序原子记录链：前一步的目标对象与 SP1 对齐后一步的源对象与 SP0，每一步各自登记结果状态、证据、损失和误差。一个总结果不能替多步分别结案。

禁止边界：每原子记录唯一算子分支模式且结果前冻结；多算子拆链逐步结案，不事后退描述救援。

## 依赖角色

本身份没有登记跨身份依赖边；这不免除具体任务中的输入与方法条件。

## source_undefined

- 无作为开放默认值登记的源未定义字段。
