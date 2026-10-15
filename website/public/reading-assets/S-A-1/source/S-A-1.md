# 附录A　人类变量接口卡册

本附录完整收录第七部分十一项人类变量（HV01—HV11）的接口卡。每张卡按A—E五区登记：A，身份、命题与适用范围；B，正式依赖与结论边界；C，九轴尺度与对象合同；D，状态、证据与变量流；E，承接、责任、规范、上限与纠错。

以下11张卡片逐项展开每个变量的全部39个正式字段。字段表达合同结构，具体证据按所选路由和任务相关性取得；不适用、未知、尚未收集与受保护不可得分别记录，不把表格填满作为普通服务或理解的资格。依赖项的空集合明确写作“无（空集合）”；它只表示该类依赖没有登记对象，不表示证据充分或经验成立。条件支持路由必须逐条整体读取，不能把不同路由的有利条件事后并取。

## A.1　HV01 结构域（完整接口卡）

A. 身份、命题与适用范围

| 字段 | 登记内容 |
| --- | --- |
| 接口 ID（id） | HV01 |
| 限定 ID（qualified_id） | human_variable:HV01 |
| 名称（name） | 结构域 |
| 主张类型（claim_type） | H |
| 合同角色（contract_role） | human_variable_interface |
| 命题（proposition） | D0只声明候选人类对象；只有预注册G1-instance显示候选分组相对匹配N0在预选结果上取得超过阈值的样本外或外推增益时，才在该实例范围登记有限有效结构域。 |
| 适用范围（scope） | 关系、团队、组织、制度与公共议题 |
| 暂停条件（pause_condition） | 对象、边界、尺度、时间窗或同一性不足以支持所选路由；申请G1正式支持时，相应零模型或实例合同不完整 |

B. 正式依赖与结论边界

| 字段 | 登记内容 |
| --- | --- |
| 推理依赖（inferential_requires） | 1. D0 |
| 协议依赖（protocol_requires） | 1. E1<br>2. EVIDENCE<br>3. SOURCE |
| 限定／特化（specializes） | 无（空集合） |
| 适用对象引用（applies_to） | 无（空集合） |
| 条件支持路由（conditional_support_routes） | 1. route_id=HV01-R0-candidate-object；<br>claim_level=candidate_description；<br>when=D0对象合同完整，但尚无符合资格且result_state=supported的G1-instance。；<br>additional_inferential_requires=无（空集合）；<br>additional_protocol_requires=无（空集合）；<br>allowed_conclusion=登记候选人类对象、材料集合、边界争议与G1补证需求。；<br>result_ceiling=仅到候选对象描述；可向HV02-HV11提供带边界与不确定性的对象引用，不把这一引用当作G1已支持的有效结构域。<br>2. route_id=HV01-R1-effective-domain；<br>claim_level=descriptive_classification；<br>when=同一对象、尺度、窗口、K与外推单元内的预注册G1-instance取得supported。；<br>additional_inferential_requires=G1-instance；<br>additional_protocol_requires=E4；<br>allowed_conclusion=登记该实例范围内的有限有效结构域、对象识别强度、边界可信度和适用窗。；<br>result_ceiling=只限预注册SP/T/K与generalization_unit；不得作终极本体、统一意志或授权判断。 |
| 允许推论（allowed_inference） | 1. R0可登记候选对象、边界争议与有限描述引用<br>2. 只在G1-instance预注册对象、尺度、窗口、结果与外推单位内登记其增益所支持的有限有效结构域及识别强度 |
| 禁止跳跃（prohibited_leap） | 1. 命名即客观共同体2. 共同处境即共同意愿 |

C. 九轴尺度与对象合同

| 字段 | 登记内容 |
| --- | --- |
| 九轴尺度画像（scale_profile） | SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：关系或事件单元、候选成员总体、边界内外分布及分组规则；X=空间范围：共同场所、组织边界、数字平台与跨域外部环境；T=时间跨度：识别窗口、成员变动周期与边界历史；O=组织层级：角色、团队、组织、制度至治理生态；C=因果层次：原始事件、互动机制、中观关系结构、制度与系统条件；R=观察分辨率：原始互动、事件序列、成员个案、边界分布、指标与摘要，并登记压缩损失；I=影响范围：直接成员、被排除者、间接受影响者、二阶外溢、跨域与代际位置；N=网络拓扑范围：成员关系、边界连接、孤立点与跨域桥接；J=管辖与授权范围：对象命名、边界采用及后续处置分别登记授权；不适用轴须登记not_applicable理由 |
| 有效对象（effective_object） | 由D0声明的候选对象；只有通过预注册G1-instance相对匹配N0的阈值检验后，才在该实例范围登记为有限有效结构域 |
| 跨尺度保持项（scale_invariants） | 1. 对象合同2. 参与与受影响位置 |
| 升格必补项（required_scale_additions） | 1. 单位与总体<br>2. 代表性<br>3. J轴<br>4. 低可见位置 |
| 随尺度改变项（changing_semantics） | 1. 有效成员、关系和同一性可随尺度改变 |
| 不适用对象（non_applicable_objects） | 1. 无意向、制度或责任接口的非人系统 |
| 禁止升格（forbidden_elevation） | 1. 局部群体直接代表全部受影响者 |

D. 状态、证据与变量流

| 字段 | 登记内容 |
| --- | --- |
| 状态集合（state） | 1. 候选2. 可识别3. 边界争议4. 不成立 |
| 可观测项（observables） | 1. 边界内外关系密度与约束差异<br>2. 成员进入、退出与被排除记录<br>3. 共同问题、资源通道或制度规则的重复共现<br>4. 改变分组规则后对象识别是否稳定 |
| 证据要求（evidence） | 1. D0候选对象与同一性记录<br>2. G1-instance预注册表及匹配N0<br>3. 训练与样本外或外推结果<br>4. 候选分组与竞争分组的增益比较 |
| 输入依赖与接口内容（input_dependencies） | 1. D0只提供候选对象字段，不构成结构成立证据<br>2. 预注册G1-instance及匹配N0、阈值、模型类、样本或外推单位<br>3. 观察位置、竞争分组与E1协议 |
| 输出效应与变量流（output_effects） | 1. R0向其余变量提供候选对象引用、边界、时间窗与不确定性；R1另提供G1所支持的有限有效范围<br>2. 对象存在及领域事实的依据与分组增益分别保留 |
| 时间窗与时滞（time_window_and_lag） | 登记识别窗口、边界变动与成员变化时滞 |
| 不确定性（uncertainty） | 记录边界争议、成员缺席和观察覆盖 |
| 局部排除区（local_exclusion_zone） | 无法安全表达或未被采样的位置不得被总体代表 |
| 受影响位置（affected_positions） | 1. 成员2. 被排除者3. 边界外成本承担者 |

E. 承接、责任、规范、上限与纠错

| 字段 | 登记内容 |
| --- | --- |
| 承接载体（carrier） | 1. 关系网络2. 组织边界3. 制度记录 |
| 责任主体（responsible_subject） | 1. 提出结构域判断的分析者<br>2. 使用该判断的决策者 |
| 规范地位（normative_status） | 描述性H-World接口，不产生正当性 |
| 判断上限（judgment_ceiling） | 只有G1-instance通过时，且仅限预注册对象、尺度、窗口、结果与外推单位，才可登记解释级有限有效对象；否则仅为候选对象或材料集合 |
| 行动上限（action_ceiling） | 本变量只生成候选结构域、边界争议与补证需求描述，不授权纳入、排除或处置；任何现实调整须另过C12、运行时显式N前提、J授权与O程序 |
| 反例（counterexamples） | 1. 同一场所中反复共现的人群没有稳定关系或共同约束<br>2. 分析者划定的群组在改变分组规则后立即消失 |
| 申诉（appeal） | 依appeal_and_rollback_rule，成员与受影响位置可经安全可达、反报复通道挑战边界、代表性和同一性判据，并触发与原命名或决策链独立的复核 |
| 回滚（rollback） | 依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销结构域登记、移除其对下游对象范围的效力并恢复为材料集合，保留版本与完成验证 |

