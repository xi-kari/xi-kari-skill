---
id: V90-CANON-HUMAN-VARIABLE-HV05
source_concept_id: human_variable:HV05
framework_version: v9.0
---

# human_variable:HV05

## 原文层

来源：`V90-P01024`

7.3.5　HV05 行动承接层

来源：`V90-P01025`

有效对象是实际执行、传导、维护、记录、照护或修复的人、岗位、程序、设施或制度。基础分型不硬依赖 HV04；须依 H2 分开观察任务日志、资源容量、成本、停止权、替代安排，以及决策、授权、监督、受益与补救依据。载体功能效应另需 G2-instance，跨期再生产另需 G2-instance 与 G3-instance。历史载体留痕是独立路由：只有 H5-instance 对唯一预选且家族—子型一致的具体载体原子引用和持久判据取得 supported，才登记指定载体与窗口内的持久留痕，并把它作为候选历史变量提交 G3-instance；H5-instance 本身不证明未来路径效应。非人载体不承担道德或法律责任，承接能力也不产生无限承接义务。

来源：`V90-P03208`

A.5　HV05 行动承接层（完整接口卡）

来源：`V90-P03209`

A. 身份、命题与适用范围

来源：`V90-P03210`, `V90-P03211`, `V90-P03212`, `V90-P03213`, `V90-P03214`, `V90-P03215`, `V90-P03216`, `V90-P03217`, `V90-P03218`, `V90-P03219`, `V90-P03220`, `V90-P03221`, `V90-P03222`, `V90-P03223`, `V90-P03224`, `V90-P03225`, `V90-P03226`, `V90-P03227`

字段登记内容接口 ID（id）HV05限定 ID（qualified_id）human_variable:HV05名称（name）行动承接层主张类型（claim_type）H合同角色（contract_role）human_variable_interface命题（proposition）执行、传导、维护、记录、照护与修复的承接载体CV必须和责任主体RS、成本承担者、受益者及停止权分别登记。适用范围（scope）需要持续行动、维护、照护或执行的人类结构暂停条件（pause_condition）低权限执行者被默认归为主要责任人或承接能力被当作义务

来源：`V90-P03228`



来源：`V90-P03229`

B. 正式依赖与推论边界

来源：`V90-P03230`, `V90-P03231`, `V90-P03232`, `V90-P03233`, `V90-P03234`, `V90-P03235`, `V90-P03236`, `V90-P03237`, `V90-P03238`, `V90-P03239`, `V90-P03240`, `V90-P03241`, `V90-P03242`, `V90-P03243`, `V90-P03244`, `V90-P03245`

字段登记内容推论依赖（inferential_requires）无（空集合）协议依赖（protocol_requires）1. EVIDENCE2. SOURCE限定／特化（specializes）1. H2适用对象引用（applies_to）无（空集合）条件支持路由（conditional_support_routes）1. route_id=HV05-R0-carrier-responsibility-split；claim_level=descriptive_classification；when=CV、同型成本承担者、受益者、停止权、RS、资源与容量可依H2分别登记。；additional_inferential_requires=无（空集合）；additional_protocol_requires=无（空集合）；allowed_conclusion=登记当前承接载体、任务、成本、容量、停止权、责任类型与承接缺口。；result_ceiling=只到当前分型与缺口描述；承接能力不成为义务，CV不成为RS。2. route_id=HV05-R1-functional-carrier-effect；claim_level=conditional_effect；when=符合资格的G2-instance显示指定载体替换、中断、补给或减载对预选功能结果有超过阈值的通道效应。；additional_inferential_requires=G2-instance；additional_protocol_requires=CAUSAL、E4；allowed_conclusion=登记指定载体在已测功能、容量、时延或损耗维度上的候选承接效应。；result_ceiling=未测维度保持未知；功能效应不得直接生成责任、牺牲义务或资源重配授权。3. route_id=HV05-R2-intertemporal-reproduction；claim_level=intertemporal_explanation；when=当前承接通道已有G2-instance支持，且G3-instance显示其历史变量对后续承接或再生产结果具有条件增量。；additional_inferential_requires=G2-instance、G3-instance；additional_protocol_requires=CAUSAL、E4；allowed_conclusion=登记指定窗口与载体内的跨期承接或再生产候选。；result_ceiling=不推出历史宿命、不可逆、责任归属或继续承担义务。4. route_id=HV05-R3-historical-carrier-trace；claim_level=descriptive_classification；when=H5-instance对唯一预选的具体载体与持久判据取得supported。；additional_inferential_requires=H5-instance；additional_protocol_requires=E4；allowed_conclusion=登记指定载体、留痕可观察量与窗口内的持久人类留痕，并向G3-instance提交预先定义的历史变量候选。；result_ceiling=H5-instance不证明未来路径效应、跨期再生产、修复窗口、责任或行动；这些结论仍须各自的G3、推论与规范程序。允许推论（allowed_inference）1. 承接缺口2. 任务资源错配3. 责任分流禁止跳跃（prohibited_leap）1. 最可见者等于主要责任人2. 能承担所以应承担3. 非人载体承担责任

来源：`V90-P03246`



来源：`V90-P03247`

C. 九轴尺度与对象合同

来源：`V90-P03248`, `V90-P03249`, `V90-P03250`, `V90-P03251`, `V90-P03252`, `V90-P03253`, `V90-P03254`, `V90-P03255`, `V90-P03256`, `V90-P03257`, `V90-P03258`, `V90-P03259`, `V90-P03260`, `V90-P03261`, `V90-P03262`, `V90-P03263`

字段登记内容九轴尺度画像（scale_profile）SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单项任务或承接事件、载体个案、承接总体、成本容量分布及聚合规则；X=空间范围：岗位现场、团队或组织边界、数字系统与跨域服务范围；T=时间跨度：任务周期、维护窗口、恢复时滞与责任有效期；O=组织层级：执行角色、团队、组织、制度至治理生态；C=因果层次：执行事件、任务—资源互动机制、中观承接结构、制度责任安排与系统条件；R=观察分辨率：原始任务日志、承接序列、载体个案、成本容量分布、绩效指标与摘要，并登记压缩损失；I=影响范围：直接承接者、服务依赖者、间接受益或成本位置、二阶外溢、跨域与代际影响；N=网络拓扑范围：承接依赖、替代路径、单点瓶颈与跨域服务网络；J=管辖与授权范围：任务分配、停止、资源调整、归责与补救分别登记授权；CV与RS分别登记尺度有效对象（effective_object）实际执行、传导、维护、记录、照护或修复的人、岗位、程序、设施或制度跨尺度保持项（scale_invariants）1. CV不等于RS2. 成本与受益分别登记3. 停止权升格必补项（required_scale_additions）1. 任务聚合2. 代表和委托3. 六类责任4. 外部成本随尺度改变项（changing_semantics）1. 承接载体和责任主体可随层级改变不适用对象（non_applicable_objects）1. 无主体行动、责任或维护要求的非人过程禁止升格（forbidden_elevation）1. 个体承接直接等于组织责任

来源：`V90-P03264`



来源：`V90-P03265`

D. 状态、证据与变量流

来源：`V90-P03266`, `V90-P03267`, `V90-P03268`, `V90-P03269`, `V90-P03270`, `V90-P03271`, `V90-P03272`, `V90-P03273`, `V90-P03274`, `V90-P03275`, `V90-P03276`, `V90-P03277`, `V90-P03278`, `V90-P03279`, `V90-P03280`, `V90-P03281`, `V90-P03282`, `V90-P03283`, `V90-P03284`, `V90-P03285`

字段登记内容状态集合（state）1. 充足2. 脆弱3. 过载4. 断裂5. 替代可观测项（observables）1. 任务实际执行、维护、记录与修复日志2. 资源、容量、时间和成本流向3. 停止权、替代安排与承接转移记录4. 决策、授权、监督、受益与补救依据证据要求（evidence）1. 任务流2. 工时与资源3. 维护记录4. 停止和拒绝记录输入依赖与接口内容（input_dependencies）1. 生成需求2. 资源3. 授权4. 角色输出效应与变量流（output_effects）1. 实现状态转移2. 成本分布3. 结构负荷时间窗与时滞（time_window_and_lag）登记排班、维护周期、积压与恢复时滞不确定性（uncertainty）记录隐性劳动、非正式照护和边界外成本局部排除区（local_exclusion_zone）低权限、非正式与不可退出承接者受影响位置（affected_positions）1. 承接者2. 受益者3. 被服务者4. 替代者

来源：`V90-P03286`



来源：`V90-P03287`

E. 承接、责任、规范、上限与纠错

来源：`V90-P03288`, `V90-P03289`, `V90-P03290`, `V90-P03291`, `V90-P03292`, `V90-P03293`, `V90-P03294`, `V90-P03295`, `V90-P03296`, `V90-P03297`, `V90-P03298`, `V90-P03299`, `V90-P03300`, `V90-P03301`, `V90-P03302`, `V90-P03303`, `V90-P03304`, `V90-P03305`

字段登记内容承接载体（carrier）1. 人员2. 岗位3. 程序4. 设施5. 制度责任主体（responsible_subject）1. 行为责任者2. 决策责任者3. 授权责任者4. 监督责任者5. 受益责任者6. 补救责任者规范地位（normative_status）承接事实不产生继续承担义务判断上限（judgment_ceiling）资源与责任链完整时至诊断级行动上限（action_ceiling）本变量只生成CV、RS、成本、容量、停止权与承接缺口描述，以及减载、补资源或重分配需求，不授权任务调整、资源配置、归责或保护；任何现实调整须另过C12、运行时显式N前提、J授权与O程序反例（counterexamples）1. 最可见的低权限执行者不是决策、授权或受益责任主体2. 自动化设施承担传导任务但不能承担道德或法律责任申诉（appeal）依appeal_and_rollback_rule，承接者可经安全可达、反报复通道挑战任务、资源、成本、停止权受限和归责，并触发与原任务分配或归责链独立的复核回滚（rollback）依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销错误任务、资源或归责状态，实际恢复先前任务与记录状态并执行经授权补救，保留版本与完成验证

来源：`V90-P03306`



## 解释层

允许边界：仅在本项原文全部适用条件与分支条件内使用human_variable:HV05；独立对象材料支持实例，定义和接口只确定意义。

禁止边界：R0不被高档前提封死；input_dependencies非推理图。

## 依赖角色

| role | target | condition | basis |
| --- | --- | --- | --- |
| `inferential_requires` | `V90-CANON-G2` | HV05-R1-functional-carrier-effect | body 1579, conditional_support_routes; target requires a qualified instance | appendix candidate adjudication |
| `inferential_requires` | `V90-CANON-G2` | HV05-R2-intertemporal-reproduction | body 1579, conditional_support_routes; target requires a qualified instance | appendix candidate adjudication |
| `inferential_requires` | `V90-CANON-G3` | HV05-R2-intertemporal-reproduction | body 1579, conditional_support_routes; target requires a qualified instance | appendix candidate adjudication |
| `inferential_requires` | `V90-CANON-H5` | HV05-R3-historical-carrier-trace | body 1579, conditional_support_routes; target requires a qualified instance | appendix candidate adjudication |
| `inferential_requires` | `V90-EXTERNAL-GATE-G2-INSTANCE` | HV05-R1-functional-carrier-effect | body 1579, conditional_support_routes |
| `inferential_requires` | `V90-EXTERNAL-GATE-G2-INSTANCE` | HV05-R2-intertemporal-reproduction | body 1579, conditional_support_routes |
| `inferential_requires` | `V90-EXTERNAL-GATE-G3-INSTANCE` | HV05-R2-intertemporal-reproduction | body 1579, conditional_support_routes |
| `inferential_requires` | `V90-EXTERNAL-GATE-H5-INSTANCE` | HV05-R3-historical-carrier-trace | body 1579, conditional_support_routes |
| `input_dependencies` | `V90-EXTERNAL-GATE-INPUT-HUMAN-VARIABLE-HV05` | base | source interface field at body 1585 |
| `protocol_requires` | `V90-CANON-E4` | HV05-R1-functional-carrier-effect | body 1579, conditional_support_routes |
| `protocol_requires` | `V90-CANON-E4` | HV05-R1-functional-carrier-effect | body 1579, conditional_support_routes | appendix candidate adjudication |
| `protocol_requires` | `V90-CANON-E4` | HV05-R2-intertemporal-reproduction | body 1579, conditional_support_routes |
| `protocol_requires` | `V90-CANON-E4` | HV05-R2-intertemporal-reproduction | body 1579, conditional_support_routes | appendix candidate adjudication |
| `protocol_requires` | `V90-CANON-E4` | HV05-R3-historical-carrier-trace | body 1579, conditional_support_routes |
| `protocol_requires` | `V90-CANON-E4` | HV05-R3-historical-carrier-trace | body 1579, conditional_support_routes | appendix candidate adjudication |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL` | HV05-R1-functional-carrier-effect | body 1579, conditional_support_routes |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL` | HV05-R2-intertemporal-reproduction | body 1579, conditional_support_routes |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL-DE06B986` | HV05-R1-functional-carrier-effect | body 1579, conditional_support_routes | appendix candidate adjudication |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL-DE06B986` | HV05-R2-intertemporal-reproduction | body 1579, conditional_support_routes | appendix candidate adjudication |
| `protocol_requires` | `V90-EXTERNAL-GATE-EVIDENCE` | base | body 1579, field protocol_requires |
| `protocol_requires` | `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0` | base | body 1579, field protocol_requires | read at declared role and conditional route ceiling |
| `protocol_requires` | `V90-EXTERNAL-GATE-SOURCE` | base | body 1579, field protocol_requires |
| `protocol_requires` | `V90-EXTERNAL-GATE-SOURCE-56CCD012` | base | body 1579, field protocol_requires | read at declared role and conditional route ceiling |
| `specializes` | `V90-CANON-H2` | base | body 1579, field specializes |
| `specializes` | `V90-CANON-H2` | base | body 1579, field specializes | read at declared role and conditional route ceiling |

## source_undefined

- Task-specific empirical parameters and evidence cannot be supplied by the concept definition.

## 条件路由

- `HV05-R0-carrier-responsibility-split`：CV、同型成本承担者、受益者、停止权、RS、资源与容量可依H2分别登记。；结论上限：只到当前分型与缺口描述；承接能力不成为义务，CV不成为RS。
- `HV05-R1-functional-carrier-effect`：符合资格的G2-instance显示指定载体替换、中断、补给或减载对预选功能结果有超过阈值的通道效应。；结论上限：未测维度保持未知；功能效应不得直接生成责任、牺牲义务或资源重配授权。
- `HV05-R2-intertemporal-reproduction`：当前承接通道已有G2-instance支持，且G3-instance显示其历史变量对后续承接或再生产结果具有条件增量。；结论上限：不推出历史宿命、不可逆、责任归属或继续承担义务。
- `HV05-R3-historical-carrier-trace`：H5-instance对唯一预选的具体载体与持久判据取得supported。；结论上限：H5-instance不证明未来路径效应、跨期再生产、修复窗口、责任或行动；这些结论仍须各自的G3、推论与规范程序。
