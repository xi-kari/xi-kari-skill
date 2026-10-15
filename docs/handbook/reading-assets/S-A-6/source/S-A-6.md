## A.6　HV06 动力—承接链（完整接口卡）

A. 身份、命题与适用范围

| 字段 | 登记内容 |
| --- | --- |
| 接口 ID（id） | HV06 |
| 限定 ID（qualified_id） | human_variable:HV06 |
| 名称（name） | 动力—承接链 |
| 主张类型（claim_type） | H |
| 合同角色（contract_role） | human_variable_interface |
| 命题（proposition） | 从指向、生成到执行、维护与偿付的链条必须逐段登记通道、资源、成本、责任和时滞。 |
| 适用范围（scope） | 人类集体行动、项目、组织与制度运行 |
| 暂停条件（pause_condition） | 用热情、愿景或命令替代承接与偿付证据 |

B. 正式依赖与结论边界

| 字段 | 登记内容 |
| --- | --- |
| 推理依赖（inferential_requires） | 无（空集合） |
| 协议依赖（protocol_requires） | 1. EVIDENCE<br>2. SOURCE |
| 限定／特化（specializes） | 无（空集合） |
| 适用对象引用（applies_to） | 无（空集合） |
| 条件支持路由（conditional_support_routes） | 1. route_id=HV06-R0-segment-map；<br>claim_level=descriptive_classification；<br>when=至少一个链段的输入、输出、时延、损耗、中断、资源、成本与边界可观察。；<br>additional_inferential_requires=无（空集合）；<br>additional_protocol_requires=无（空集合）；<br>allowed_conclusion=登记局部链段、缺失桥、时滞、损耗、中断点与成本位置。；<br>result_ceiling=不得由单一链段或动力语言宣称完整链条或有效通道。<br>2. route_id=HV06-R1-complete-chain-composition；<br>claim_level=descriptive_classification；<br>when=指向、生成与承接三个接口记录可在同一对象、尺度、窗口与量的映射中逐段连接。；<br>additional_inferential_requires=human_variable:HV03、human_variable:HV04、human_variable:HV05；<br>additional_protocol_requires=无（空集合）；<br>allowed_conclusion=登记完整候选动力—承接链及逐段证据覆盖。；<br>result_ceiling=只到候选链条组成；接口记录齐全不等于各链段具有因果效力。<br>3. route_id=HV06-R2-effective-channel；<br>claim_level=mechanism_explanation；<br>when=完整候选链已组成，符合资格的G2-instance支持指定通道，并且同案对应、共同支持范围、联合响应、时序、容量与终端结果足以支持所问整链效应；不能只将边的平均效应相乘。；<br>additional_inferential_requires=human_variable:HV03、human_variable:HV04、human_variable:HV05、G2-instance；<br>additional_protocol_requires=CAUSAL、E4；<br>allowed_conclusion=登记已检验链段和窗口内的有效动力—承接通道、损耗与中断机制。；<br>result_ceiling=不得从一次贯通推出跨期再生产、责任、正当性或行动授权。 |
| 允许推论（allowed_inference） | 1. 链条瓶颈2. 动力与承接脱节3. 隐性偿付 |
| 禁止跳跃（prohibited_leap） | 1. 动力强等于可持续<br>2. 失败归因意愿不足<br>3. 承接者应自行补洞 |

C. 九轴尺度与对象合同

| 字段 | 登记内容 |
| --- | --- |
| 九轴尺度画像（scale_profile） | SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单个链节事件、链条个案、同类链总体、输入输出分布及聚合规则；X=空间范围：行动现场、项目或组织边界、数字协作空间与跨域外溢；T=时间跨度：启动、维持、中断、恢复窗口及跨期周期；O=组织层级：发起角色、执行团队、组织、制度至治理生态；C=因果层次：链节事件、动力—资源—任务互动机制、中观承接链、制度安排与系统条件；R=观察分辨率：原始任务资源记录、链节序列、链条个案、损耗分布、绩效指标与摘要，并登记压缩损失；I=影响范围：直接发起与承接位置、间接受益或成本位置、二阶外溢、跨域与代际影响；N=网络拓扑范围：依赖链、替代路径、瓶颈、反馈连接与跨域桥接；J=管辖与授权范围：目标采用、任务分配、资源投入、停止与试验分别登记授权；逐段标明跨轴位置 |
| 有效对象（effective_object） | 把指向和生成转为持续行动的可追踪链条 |
| 跨尺度保持项（scale_invariants） | 1. 指向、生成、承接、资源、成本和责任链 |
| 升格必补项（required_scale_additions） | 1. 跨层桥接<br>2. 聚合损失<br>3. 责任继承<br>4. 保护底板 |
| 随尺度改变项（changing_semantics） | 1. 节点、通道和瓶颈可随组织尺度改变 |
| 不适用对象（non_applicable_objects） | 1. 无意向动力与人类承接的非人过程 |
| 禁止升格（forbidden_elevation） | 1. 局部动力或单一节点直接代表完整链条 |

D. 状态、证据与变量流

| 字段 | 登记内容 |
| --- | --- |
| 状态集合（state） | 1. 贯通<br>2. 迟滞<br>3. 过载<br>4. 断裂<br>5. 替代 |
| 可观测项（observables） | 1. 锚点转化为任务、预算、规则或排程的记录<br>2. 每段输入输出、时延、损耗与中断点<br>3. 承接者容量、停止与替代路径变化<br>4. 链条输出对目标结果的实际贡献 |
| 证据要求（evidence） | 1. 资源流<br>2. 任务与维护记录<br>3. 偿付与成本<br>4. 时滞 |
| 输入依赖与接口内容（input_dependencies） | 1. 指向锚点2. 生成节点3. 承接层 |
| 输出效应与变量流（output_effects） | 1. 行动结果2. 负荷3. 反馈与演化痕迹 |
| 时间窗与时滞（time_window_and_lag） | 逐段登记启动、传导、维护和偿付时滞 |
| 不确定性（uncertainty） | 记录断点、替代通道与边界外偿付 |
| 局部排除区（local_exclusion_zone） | 非正式、低可见和跨组织承接位置 |
| 受影响位置（affected_positions） | 1. 发起者<br>2. 承接者<br>3. 受益者<br>4. 成本承担者 |

E. 承接、责任、规范、上限与纠错

| 字段 | 登记内容 |
| --- | --- |
| 承接载体（carrier） | 1. 人员与岗位<br>2. 程序<br>3. 预算<br>4. 基础设施 |
| 责任主体（responsible_subject） | 1. 各节点行为、决策、授权、监督与补救责任者 |
| 规范地位（normative_status） | 链条有效不证明目标正当 |
| 判断上限（judgment_ceiling） | 全链证据充分时至解释或诊断级 |
| 行动上限（action_ceiling） | 本变量只生成链条连通、时滞、损耗、中断、成本与承接需求描述，不授权减载、资源调整或试验；任何现实调整须另过C12、运行时显式N前提、J授权与O程序 |
| 反例（counterexamples） | 1. 强烈愿景和集中动员没有持续资源、维护或偿付<br>2. 表面贯通的链条把关键成本转移给边界外承接者 |
| 申诉（appeal） | 依appeal_and_rollback_rule，链上承接或受影响位置可经安全可达、反报复通道挑战资源、成本与链条归因，并触发与原链条判断或决策链独立的复核 |
| 回滚（rollback） | 依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销整体链条归因及其下游效力、恢复为节点级描述与未决状态，保留版本与完成验证 |

