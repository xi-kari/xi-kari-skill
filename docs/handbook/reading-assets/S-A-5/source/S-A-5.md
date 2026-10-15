## A.5　HV05 行动承接层（完整接口卡）

A. 身份、命题与适用范围

| 字段 | 登记内容 |
| --- | --- |
| 接口 ID（id） | HV05 |
| 限定 ID（qualified_id） | human_variable:HV05 |
| 名称（name） | 行动承接层 |
| 主张类型（claim_type） | H |
| 合同角色（contract_role） | human_variable_interface |
| 命题（proposition） | 执行、传导、维护、记录、照护与修复的承接载体CV必须和责任主体RS、成本承担者、受益者及停止权分别登记。 |
| 适用范围（scope） | 需要持续行动、维护、照护或执行的人类结构 |
| 暂停条件（pause_condition） | 低权限执行者被默认归为主要责任人或承接能力被当作义务 |

B. 正式依赖与结论边界

| 字段 | 登记内容 |
| --- | --- |
| 推理依赖（inferential_requires） | 无（空集合） |
| 协议依赖（protocol_requires） | 1. EVIDENCE<br>2. SOURCE |
| 限定／特化（specializes） | 1. H2 |
| 适用对象引用（applies_to） | 无（空集合） |
| 条件支持路由（conditional_support_routes） | 1. route_id=HV05-R0-carrier-responsibility-split；<br>claim_level=descriptive_classification；<br>when=CV、同型成本承担者、受益者、停止权、RS、资源与容量可依H2分别登记。；<br>additional_inferential_requires=无（空集合）；<br>additional_protocol_requires=无（空集合）；<br>allowed_conclusion=登记当前承接载体、任务、成本、容量、停止权、责任类型与承接缺口。；<br>result_ceiling=只到当前分型与缺口描述；承接能力不成为义务，CV不成为RS。<br>2. route_id=HV05-R1-functional-carrier-effect；<br>claim_level=conditional_effect；<br>when=符合资格的G2-instance显示指定载体替换、中断、补给或减载对预选功能结果有超过阈值的通道效应。；<br>additional_inferential_requires=G2-instance；<br>additional_protocol_requires=CAUSAL、E4；<br>allowed_conclusion=登记指定载体在已测功能、容量、时延或损耗维度上的候选承接效应。；<br>result_ceiling=未测维度保持未知；功能效应不得直接生成责任、牺牲义务或资源重配授权。<br>3. route_id=HV05-R2-intertemporal-reproduction；<br>claim_level=intertemporal_explanation；<br>when=当前承接通道已有G2-instance支持，且G3-instance显示其历史变量对后续承接或再生产结果具有条件增量。；<br>additional_inferential_requires=G2-instance、G3-instance；<br>additional_protocol_requires=CAUSAL、E4；<br>allowed_conclusion=登记指定窗口与载体内、当前状态之外的历史增量型跨期承接或再生产候选。；<br>result_ceiling=不推出历史宿命、不可逆、责任归属或继续承担义务。<br>4. route_id=HV05-R3-historical-carrier-trace；<br>claim_level=descriptive_classification；<br>when=H5-instance对唯一预选的具体载体与持久判据取得supported。；<br>additional_inferential_requires=H5-instance；<br>additional_protocol_requires=E4；<br>allowed_conclusion=登记指定载体、留痕可观察量与窗口内的持久人类留痕，并向G3-instance提交预先定义的历史变量候选。；<br>result_ceiling=H5-instance不证明未来路径效应、跨期再生产、修复窗口、责任或行动；这些结论分别依载体或历史增量路线、结果合同与规范程序取证。<br>5. route_id=HV05-R4-carried-reproduction；<br>claim_level=intertemporal_explanation；<br>when=符合资格的G2-instance支持指定承接通道在所声明后续结果与窗口内的效应，且依§4.5核实当前能力、规则、资源或关系载体、多个周期的保留或补给、实际接续及区分性因果材料。；<br>additional_inferential_requires=G2-instance；<br>additional_protocol_requires=CAUSAL、E4；<br>allowed_conclusion=登记指定载体、周期和结果内的载体传递型跨期承接或再生产候选。；<br>result_ceiling=不登记当前状态之外的历史增量，不由一次功能效应外推长期，不从承接事实产生继续承担义务或授权。 |
| 允许推论（allowed_inference） | 1. 承接缺口2. 任务资源错配3. 责任分流 |
| 禁止跳跃（prohibited_leap） | 1. 最可见者等于主要责任人<br>2. 能承担所以应承担<br>3. 仅凭设施或程序执行功能就赋予责任；组织责任另据主体资格与具体规则 |

C. 九轴尺度与对象合同

| 字段 | 登记内容 |
| --- | --- |
| 九轴尺度画像（scale_profile） | SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单项任务或承接事件、载体个案、承接总体、成本容量分布及聚合规则；X=空间范围：岗位现场、团队或组织边界、数字系统与跨域服务范围；T=时间跨度：任务周期、维护窗口、恢复时滞与责任有效期；O=组织层级：执行角色、团队、组织、制度至治理生态；C=因果层次：执行事件、任务—资源互动机制、中观承接结构、制度责任安排与系统条件；R=观察分辨率：原始任务日志、承接序列、载体个案、成本容量分布、绩效指标与摘要，并登记压缩损失；I=影响范围：直接承接者、服务依赖者、间接受益或成本位置、二阶外溢、跨域与代际影响；N=网络拓扑范围：承接依赖、替代路径、单点瓶颈与跨域服务网络；J=管辖与授权范围：任务分配、停止、资源调整、归责与补救分别登记授权；CV与RS分别登记尺度 |
| 有效对象（effective_object） | 实际执行、传导、维护、记录、照护或修复的人、岗位、程序、设施或制度 |
| 跨尺度保持项（scale_invariants） | 1. CV不等于RS<br>2. 成本与受益分别登记<br>3. 停止权 |
| 升格必补项（required_scale_additions） | 1. 任务聚合<br>2. 代表和委托<br>3. 六类责任<br>4. 外部成本 |
| 随尺度改变项（changing_semantics） | 1. 承接载体和责任主体可随层级改变 |
| 不适用对象（non_applicable_objects） | 1. 无主体行动、责任或维护要求的非人过程 |
| 禁止升格（forbidden_elevation） | 1. 个体承接直接等于组织责任 |

D. 状态、证据与变量流

| 字段 | 登记内容 |
| --- | --- |
| 状态集合（state） | 1. 充足<br>2. 脆弱<br>3. 过载<br>4. 断裂<br>5. 替代 |
| 可观测项（observables） | 1. 任务实际执行、维护、记录与修复日志<br>2. 资源、容量、时间和成本流向<br>3. 停止权、替代安排与承接转移记录<br>4. 决策、授权、监督、受益与补救依据 |
| 证据要求（evidence） | 1. 任务流<br>2. 工时与资源<br>3. 维护记录<br>4. 停止和拒绝记录<br>5. 若目标涉及总体负担，分别核管理、待命、替代者条件及接续；单项任务判断不强制全部采集 |
| 输入依赖与接口内容（input_dependencies） | 1. 生成需求2. 资源3. 授权4. 角色 |
| 输出效应与变量流（output_effects） | 1. 实现状态转移2. 成本分布3. 结构负荷 |
| 时间窗与时滞（time_window_and_lag） | 登记排班、维护周期、积压与恢复时滞 |
| 不确定性（uncertainty） | 记录隐性劳动、非正式照护和边界外成本 |
| 局部排除区（local_exclusion_zone） | 低权限、非正式与不可退出承接者 |
| 受影响位置（affected_positions） | 1. 承接者<br>2. 受益者<br>3. 被服务者<br>4. 替代者 |

E. 承接、责任、规范、上限与纠错

| 字段 | 登记内容 |
| --- | --- |
| 承接载体（carrier） | 1. 人员<br>2. 岗位<br>3. 程序<br>4. 设施<br>5. 制度 |
| 责任主体（responsible_subject） | 1. 行为责任者<br>2. 决策责任者<br>3. 授权责任者<br>4. 监督责任者<br>5. 受益责任者<br>6. 补救责任者 |
| 规范地位（normative_status） | 承接事实不产生继续承担义务 |
| 判断上限（judgment_ceiling） | R0限于承接与责任分型；R1限于所识别的载体功能效应；R3限于H5支持的持久留痕；R4依§4.5与覆盖后续窗口的通道证据解释载体型再生产；R2另有G3时才解释当前表示之外的历史增量。材料和窗口各自限定，不以任一路线代替其余路线，也不产生无限承担义务。 |
| 行动上限（action_ceiling） | 本变量只生成CV、RS、成本、容量、停止权与承接缺口描述，以及减载、补资源或重分配需求，不授权任务调整、资源配置、归责或保护；任何现实调整须另过C12、运行时显式N前提、J授权与O程序 |
| 反例（counterexamples） | 1. 最可见的低权限执行者不是决策、授权或受益责任主体<br>2. 自动化设施承担传导任务但不能承担道德或法律责任 |
| 申诉（appeal） | 依appeal_and_rollback_rule，承接者可经安全可达、反报复通道挑战任务、资源、成本、停止权受限和归责，并触发与原任务分配或归责链独立的复核 |
| 回滚（rollback） | 依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销错误任务、资源或归责状态，实际恢复先前任务与记录状态并执行经授权补救，保留版本与完成验证 |

