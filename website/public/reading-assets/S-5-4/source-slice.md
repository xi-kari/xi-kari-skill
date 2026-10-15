## 5.4　算子的结果状态与零结论门

每条原子记录的 operator_ids 必须且只能包含一个算子，selected_operator_branch 再从该算子的分支注册表中唯一选择内部支路，最后用 claim_mode 声明本次评价的模式：descriptive_mapping（描述映射）、root_hypothesis（经验问题族实例）、causal（因果桥）、object_conversion（对象转换）或 intervention_conversion（干预转换）。分支注册表明确每个支路允许哪些模式；三者必须相容并在看结果前冻结，不能因正向门失败切换支路或退回较宽松的描述模式，也不能把一个模式的材料用于救援另一个模式。若一个实际过程包含多个算子，须拆成有序原子记录链：前一步的目标对象与 SP1 对齐后一步的源对象与 SP0，每一步各自登记结果状态、证据、损失和误差。一个总结果不能替多步分别结案。

算子程序统一使用四个结果状态：

supported：本次选定分支的桥、决策规则和正向阈值已预注册且通过；只有 G、因果、对象/干预转换分支才强制 root-instance、预选子型和唯一成功判据，纯描述分支可把这些 G 专用字段记为 not_applicable；

unsupported_or_undecided：桥接不足，或正向门未通过而零结论门也未通过；

null_supported：只有预注册 null_decision_rule、等价性或充分性检验、功效或灵敏度及容差全部通过时，才支持限定零结论；

not_evaluated：算子或相应分支尚未运行；已运行且描述桥成立的分支可以是 supported，不能因不需要 G-instance 而降为未评估。

“未显著”“切断后看似不变”“效应消失”“简单模型表现相当”或“目标证据不足”都不能自动写成 null_supported。这条纪律适用于 M01—M09，而不只适用于跨层因果。

