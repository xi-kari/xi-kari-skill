## A.2　HV02 边界与接口（完整接口卡）

A. 身份、命题与适用范围

| 字段 | 登记内容 |
| --- | --- |
| 接口 ID（id） | HV02 |
| 限定 ID（qualified_id） | human_variable:HV02 |
| 名称（name） | 边界与接口 |
| 主张类型（claim_type） | H |
| 合同角色（contract_role） | human_variable_interface |
| 命题（proposition） | 人类边界必须同时登记成员、资源、信息、权利、责任与跨界接口。 |
| 适用范围（scope） | 存在纳入、排除、交换或管辖的人类结构 |
| 暂停条件（pause_condition） | 正式边界与实际边界混同或排除项不可见 |

B. 正式依赖与结论边界

| 字段 | 登记内容 |
| --- | --- |
| 推理依赖（inferential_requires） | 1. human_variable:HV01 |
| 协议依赖（protocol_requires） | 1. E1<br>2. EVIDENCE<br>3. SOURCE |
| 限定／特化（specializes） | 无（空集合） |
| 适用对象引用（applies_to） | 无（空集合） |
| 条件支持路由（conditional_support_routes） | 1. route_id=HV02-R0-boundary-inventory；<br>claim_level=descriptive_classification；<br>when=成员、资源、信息、权利、责任、跨界接口及正式—实际边界差异可逐项登记。；<br>additional_inferential_requires=无（空集合）；<br>additional_protocol_requires=无（空集合）；<br>allowed_conclusion=描述边界状态、接口通达性、守门位置、拒绝记录与排除风险。；<br>result_ceiling=只到边界与接口清单；不得断言边界已产生因果选择效应。<br>2. route_id=HV02-R1-selective-effect；<br>claim_level=conditional_effect；<br>when=预注册边界或接口变动经符合资格的G2-instance显示对指定跨界流、准入或拒绝结果有超过阈值的通道效应。；<br>additional_inferential_requires=G2-instance；<br>additional_protocol_requires=CAUSAL、E4；<br>allowed_conclusion=登记指定通道、窗口与位置上的边界选择效应及跨界成本分布。；<br>result_ceiling=只限已检验通道与结果；不得从空间、组织或影响范围推出J轴管辖与处置权。 |
| 允许推论（allowed_inference） | 1. 边界选择性2. 接口通达性3. 跨界成本 |
| 禁止跳跃（prohibited_leap） | 1. 边界等于封闭<br>2. 成员身份等于同意<br>3. 影响范围等于管辖权 |

C. 九轴尺度与对象合同

| 字段 | 登记内容 |
| --- | --- |
| 九轴尺度画像（scale_profile） | SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次跨界事件、接口使用个案、成员类别总体、准入拒绝分布及聚合规则；X=空间范围：物理入口、组织边界、数字接口、司法辖区与跨域通道；T=时间跨度：边界生效期、接口等待、迁移时滞与重组周期；O=组织层级：使用者角色、守门团队、组织、制度至治理生态；C=因果层次：跨界事件、守门互动机制、接口结构、制度规则与系统条件；R=观察分辨率：原始准入拒绝记录、使用序列、个案、流量分布、服务指标与摘要，并登记压缩损失；I=影响范围：直接使用者、被排除者、间接受益或成本位置、二阶外溢、跨域与代际影响；N=网络拓扑范围：接口节点、守门瓶颈、替代路径与跨域连接；J=管辖与授权范围：纳入、排除、接口改变及权利责任调整分别登记授权；升格须记录逐轴差值 |
| 有效对象（effective_object） | 对资源、信息、权利或责任流产生选择性的边界 |
| 跨尺度保持项（scale_invariants） | 1. 内外位置2. 跨界通道3. 权利责任边界 |
| 升格必补项（required_scale_additions） | 1. 新成员类别<br>2. 跨域接口<br>3. 代表与授权<br>4. 保护继承 |
| 随尺度改变项（changing_semantics） | 1. 成员、接口与实际控制边界可改变 |
| 不适用对象（non_applicable_objects） | 1. 无成员、权利或责任概念的非人边界 |
| 禁止升格（forbidden_elevation） | 1. 空间或组织范围扩大自动产生管辖权 |

D. 状态、证据与变量流

| 字段 | 登记内容 |
| --- | --- |
| 状态集合（state） | 1. 开放<br>2. 选择性开放<br>3. 封闭<br>4. 争议<br>5. 重组 |
| 可观测项（observables） | 1. 成员资格、准入与退出决定<br>2. 资源、信息、权利和责任的跨界流量<br>3. 守门节点、等待时间与拒绝理由<br>4. 正式边界与实际通行边界的差异 |
| 证据要求（evidence） | 1. 成员名单与例外<br>2. 接口使用记录<br>3. 跨界流和拒绝记录 |
| 输入依赖与接口内容（input_dependencies） | 1. HV01候选对象或已支持结构域及其证据状态<br>2. 角色与授权；R0不要求G1预先通过 |
| 输出效应与变量流（output_effects） | 1. HV05承接<br>2. HV07写回<br>3. PF-9退出 |
| 时间窗与时滞（time_window_and_lag） | 记录边界生效、变更、退出和申诉时滞 |
| 不确定性（uncertainty） | 记录非正式边界、代理访问和数字空间漂移 |
| 局部排除区（local_exclusion_zone） | 无法接入接口、无法退出或受保护不公开的位置 |
| 受影响位置（affected_positions） | 1. 成员<br>2. 申请者<br>3. 被排除者<br>4. 边界外承担者 |

E. 承接、责任、规范、上限与纠错

| 字段 | 登记内容 |
| --- | --- |
| 承接载体（carrier） | 1. 成员规则<br>2. 访问机制<br>3. 法律或制度边界<br>4. 技术接口 |
| 责任主体（responsible_subject） | 1. 边界制定者2. 接口运营者3. 授权者 |
| 规范地位（normative_status） | 边界事实与边界正当性分离 |
| 判断上限（judgment_ceiling） | 接口与影响证据充分时至诊断级 |
| 行动上限（action_ceiling） | 本变量只生成边界状态、接口障碍、排除风险与测试需求描述，不授权改变准入、退出、权利或资源流；任何现实调整须另过C12、运行时显式N前提、J授权与O程序 |
| 反例（counterexamples） | 1. 正式成员边界与实际资源控制边界相反<br>2. 数字接口开放但物理、语言或安全门槛使部分位置无法进入 |
| 申诉（appeal） | 依appeal_and_rollback_rule，边界内外受影响者可经安全可达、反报复通道挑战纳入、排除和接口障碍，并触发与原边界决策链独立的复核 |
| 回滚（rollback） | 依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内纠正成员与拒绝记录、实际恢复受影响的准入权利或接口状态并撤销错误边界行动，保留版本与完成验证 |

