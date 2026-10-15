## 5.7　统一尺度变换记录

每个实例都必须出现十四节和全部字段：

| 节 | 必填字段 |
| --- | --- |
| identity | contract_id、concept_id、version、proposition_ids、purpose |
| scale | SP0、SP1、九条 axis_differences、unchanged_axes、transformation_class、j_authorization |
| objects | 源/目标有效对象、source_K、target_K、identity_mapping、单位、总体、边界、成员、排除项 |
| semantics | preserved_core、allowed_changes、lost_elements、prohibited_mappings |
| transformation | 单一算子、selected_operator_branch、claim_mode、规则、因果桥、时滞、映射误差、有效期、root-instance、子型、成功判据、正向和零决策规则、正向阈值、等价/充分性检验、功效/灵敏度、容差、结果状态 |
| variables | 输入、状态、输出和跨变量依赖 |
| evidence | 源/目标证据、覆盖、异质性、反例、缺席信号、替代解释、残差检验、复制或外部验证 |
| loss | 压缩细节、不可恢复信息、低可见位置和局部排除区 |
| responsibility | 行动者、决策者、授权者、承接载体、责任主体、受益者和成本承担者 |
| normative | 价值前提、选择类型、规范选择记录、运行时 N 原则、授权来源、C12 门和 O1-O4 程序 |
| protection | 保护适用性、低权力位置、安全提交和反报复 |
| action | 判断上限、行动上限、禁止动作、停止条件、责任人和机器可指向的 selected_action |
| correction | 申诉、复核、回滚、修复和写回 |
| lifecycle | 有效期、复审点、暂停和退场 |

source_K、target_K 和 identity_mapping 共同决定对象保持、转换或不可比；同名不是同一性证据。映射记录必须同时保存源、目标 K 的摘要，源对象与目标对象分别在两套 K 下的四项判据结果，正向与反向映射，保持和违反的判据，结果前冻结的预注册引用，以及可复核的验证制品与哈希。判据结果只允许 passed、failed 或 undetermined，不能用一个布尔值掩盖是哪一项没有通过。

| K 映射分类 | 最低成立条件 | 结果上限 |
| --- | --- | --- |
| same_object | 双向映射均有效；源对象与目标对象在 source_K、target_K 下四项检查均通过；保持判据非空且违反判据为空 | 可在当前合同内沿用对象身份，但不推出语义、因果或规范性质也保持 |
| converted_object | source_under_source_K 与 target_under_target_K 通过，target_under_source_K 失败；违反项和结果前预注册引用具体；另有 object_conversion 模式及取得支持的 G4b 实例 | 只登记预注册 K 下的对象转换，不得在结果后改写 K 制造转换 |
| incomparable | 两端各自在本方 K 下通过，至少一个交叉 K 检查失败；正反向映射保存完整尝试记录且至少一项验证为无效，并有可解析证据 | 表示已知不可比，只能 unsupported_or_undecided；不是“尚未评估” |
| undetermined | 必要映射、判据或证据尚不足以完成分类；四项判据分别保留已知的 passed、failed 与尚未确定的 undetermined，并指出哪一项阻断整体判断 | 只能 unsupported_or_undecided 或 not_evaluated；不把部分已知清空，也不据整体未决推定不可比或对象转换 |

对象同一性必须允许独立复算或复核。相同对象与相同判据可直接核对；非平凡保持或转换须保留两端对象、两套 K、映射方向、四项判据结果及支持材料。一个名称、编号、自报有效状态或散列值都不能代替这种语义核验。

对象转换模式与结果四态必须一致：supported 才对应 converted_object；null_supported 对应通过零结论三门的 same_object；unsupported_or_undecided 只允许保持、已知不可比或未决；对象转换尚未运行时，整体分类保持 undetermined，已独立核得的局部判据仍保留。因此，未检验和检验失败都不能先把目标写成“已经转换”。其他 claim_mode 也不得在同一条原子记录里兼报 converted_object，对象转换必须拆成自己的原子检验。

claim_mode 为 root_hypothesis、causal、object_conversion 或 intervention_conversion 时必须填写 root_instance_ids，后三者还必须给出非空因果桥；只有 descriptive_mapping 可把 root-instance、子型和成功判据标为 not_applicable。非描述模式登记 supported 或 null_supported 时，还必须向验证器提交可解析的 root-instance 注册表，并核对实例 ID、根族、合同版本、预选子型、唯一成功判据与实例状态；一个看似正确的字符串前缀不能充当实例。描述桥正向门通过时可以记 supported，只有所选模式没有运行时才记 not_evaluated。

十四节是稳定接口，不是把人类治理语义投射给所有对象。protection.applicability 必须显式登记对象类型、下游用途、理由和证据引用，不能从 actors 等空列表反推。对象类型为 nonhuman，且用途只含 description_only 或有证据证明不影响人类/有感主体的 nonhuman_intervention_without_human_or_sentient_effect 时，safe_submission 与 anti_retaliation 可带理由记 not_applicable；但现实实验或工程干预仍有行动主体和对象，必须填写具体 J、行动责任人、停止、复核与回滚，只有纯描述用途才允许 J 不适用。自然系统中的能量、物质或计算资源本身不触发这套人类保护合同。对象为人类、有感非人、混合或未知，或用途涉及人的评价、其稀缺资源配置、权利、暴露风险或现实处置时，保护字段立即成为强制项，不得沿用先前的不适用状态。保护不适用绝不推出行动正当，规范选择仍另行判断。

action_owner 只说明谁负责执行或停止，不能反推 claim_mode=intervention_conversion，也不能证明行动有效或正当。任何外部行动必须链接 selection_record_id，公开 value_premises 与运行时 normative_principle_ids；N1 单独只能阻止越权，不能产生正向方案。选择记录中的 feasible_alternatives 不是名称列表，而是带稳定 option_id 的结构化方案；每项冻结 option_kind、动作类型、目标对象、地域、有效期、可逆性、预期影响和分配影响，并且恰有一项 option_kind=no_action，由 no_action_option_id 唯一指向。selected_action.selected_option_id 必须解析到一项 external_action，而且其动作、对象、地域和有效期与该方案逐项相等；选择不行动 ID、只对上自然语言标签，或同时改写动作与 J 而不改获准方案，都必须被拒绝。至少一条当前有效且独立复核的 J 原子授权元组还必须同时覆盖该主体、对象、动作、地域和期限，并与授权来源一致；一条无关但形式有效的授权不能为拟议行动背书。记录还必须有通过的十组件 c12_gate、O1-O4 procedure_ids、行动责任人、禁止动作、停止、保护、申诉、复核和回滚。缺任一项时，行动上限只能是不行动或继续审议；经验上的干预转换另由相应 root-instance 判断。

记录链只提供组合次序，不把前一步的支持自动传递给后一步。链校验必须保证每步 contract_id 唯一、每步只有一个算子、相邻对象引用及同一性判据兼容、前一 SP1 与后一 SP0 一致；任一步未决、失效或损失超限，都要在链级输出中保留，不能被最终一步的成功覆盖。

链级评价还要明确最终任务是否与逐步任务一致，以及共享资源是否被重复承诺。两项任务可以分别在一单位容量下可行，却在同一期共用这一单位时不可联合完成；期限、资源或允许策略合法改变后，应评价新的联合方案。表示充分性、联合因果响应与联合资源可行性各有判据，不能用其中一项通过代替其余两项。

