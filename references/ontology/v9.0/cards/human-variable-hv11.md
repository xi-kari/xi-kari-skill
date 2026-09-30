---
id: V90-CANON-HUMAN-VARIABLE-HV11
source_concept_id: human_variable:HV11
framework_version: v9.0
---

# human_variable:HV11

## 原文层

来源：`V90-P01038`

7.3.11　HV11 开放性承担行动

来源：`V90-P01039`

有效对象是具有真实成本、自愿性、方向和可检测结构后果的人类行动。HV11 不硬依赖 HV05：基础路由可先登记行动、成本、方向、强制风险与停止权缺口；只有自愿性、真实拒绝与退出、替代解释和后果均可见，才登记有限开放性承担描述；若进一步主张结构后果，则另需 G2-instance。HV11 受 H6 与 N4 约束，不自行授权任何保护措施；不得诊断人格或爱，也不得把个体承担升格为群体义务。

来源：`V90-P01040`

开放性承担行动是用于审查特定行动及承担安排的有限类别，不是爱的定义、检测器或人格等级。轻松相伴、能力受限者的关切、未成功的创造、私人哀悼或没有产生新结构的拒绝，不因缺少高成本和可检测结构后果而失去经验与价值。反过来，高成本、持久付出和善意自述也不自动证明自由同意、公平分配或正当义务。材料不足时降低外部命名强度，不取消当事人的听取、保护与拒绝资格。

来源：`V90-P03802`

A.11　HV11 开放性承担行动（完整接口卡）

来源：`V90-P03803`

A. 身份、命题与适用范围

来源：`V90-P03804`, `V90-P03805`, `V90-P03806`, `V90-P03807`, `V90-P03808`, `V90-P03809`, `V90-P03810`, `V90-P03811`, `V90-P03812`, `V90-P03813`, `V90-P03814`, `V90-P03815`, `V90-P03816`, `V90-P03817`, `V90-P03818`, `V90-P03819`, `V90-P03820`, `V90-P03821`

字段登记内容接口 ID（id）HV11限定 ID（qualified_id）human_variable:HV11名称（name）开放性承担行动主张类型（claim_type）H合同角色（contract_role）human_variable_interface命题（proposition）开放性承担只观察真实成本、自愿性、方向、替代解释和结构后果，不诊断某人有没有爱。适用范围（scope）人类关系、组织、制度与公共行动中的承担暂停条件（pause_condition）无法安全确认自愿、拒绝和退出，或分析转向人格与爱的诊断

来源：`V90-P03822`



来源：`V90-P03823`

B. 正式依赖与推论边界

来源：`V90-P03824`, `V90-P03825`, `V90-P03826`, `V90-P03827`, `V90-P03828`, `V90-P03829`, `V90-P03830`, `V90-P03831`, `V90-P03832`, `V90-P03833`, `V90-P03834`, `V90-P03835`, `V90-P03836`, `V90-P03837`, `V90-P03838`, `V90-P03839`

字段登记内容推论依赖（inferential_requires）无（空集合）协议依赖（protocol_requires）1. N42. EVIDENCE3. SOURCE限定／特化（specializes）1. H62. H2适用对象引用（applies_to）无（空集合）条件支持路由（conditional_support_routes）1. route_id=HV11-R0-action-cost-record；claim_level=normative_boundary；when=行动、真实成本、方向、替代解释、受益与后果可观察，但自愿性、拒绝或退出尚不充分。；additional_inferential_requires=无（空集合）；additional_protocol_requires=无（空集合）；allowed_conclusion=描述候选承担行动、成本分布、强制风险、停止权缺口与保护需求。；result_ceiling=不得称开放性承担，不得诊断爱、人格或要求继续承担。2. route_id=HV11-R1-voluntary-limited-action；claim_level=normative_boundary；when=真实成本、自愿性、真实拒绝与退出、方向、替代解释和结构后果均分别可见。；additional_inferential_requires=无（空集合）；additional_protocol_requires=无（空集合）；allowed_conclusion=登记有限、自愿且具有方向和可观察后果的开放性承担行动描述。；result_ceiling=只到行动描述；不把个体承担升格为群体义务，也不授权征用、保护或资源安排。3. route_id=HV11-R2-structural-consequence；claim_level=conditional_effect；when=符合资格的G2-instance显示该行动经指定通道对预选结构结果产生超过阈值的效应。；additional_inferential_requires=G2-instance；additional_protocol_requires=CAUSAL、E4；allowed_conclusion=登记指定通道、对象与窗口内的行动结构后果。；result_ceiling=结构效应不证明爱、善、正当性、无限责任或行动授权。允许推论（allowed_inference）1. 描述有限承担行动与后果禁止跳跃（prohibited_leap）1. 诊断有没有爱2. 牺牲等于爱3. 责任等于无限承担4. 拒绝等于道德失败

来源：`V90-P03840`



来源：`V90-P03841`

C. 九轴尺度与对象合同

来源：`V90-P03842`, `V90-P03843`, `V90-P03844`, `V90-P03845`, `V90-P03846`, `V90-P03847`, `V90-P03848`, `V90-P03849`, `V90-P03850`, `V90-P03851`, `V90-P03852`, `V90-P03853`, `V90-P03854`, `V90-P03855`, `V90-P03856`, `V90-P03857`

字段登记内容九轴尺度画像（scale_profile）SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：单次承担行动、行动者个案、关系或组织总体、成本自愿性分布及聚合规则；X=空间范围：关系与照护现场、组织边界、数字公共空间与跨域受益范围；T=时间跨度：即时行动、持续承担、耗竭、恢复与代际窗口；O=组织层级：行动角色、关系或团队、组织、制度至治理生态；C=因果层次：承担事件、行动—成本互动机制、中观关系结构、制度责任安排与系统条件；R=观察分辨率：原始行动与成本、承担序列、行动者个案、成本自愿性分布、后果指标与摘要，并登记压缩损失；I=影响范围：直接行动者与受益者、依赖者、间接替代承接者、二阶外溢、跨域与代际影响；N=网络拓扑范围：依赖照护、受益连接、替代承接、退出路径与跨域成本网络；J=管辖与授权范围：承担要求、资源使用、拒绝、停止、保护与补救分别登记授权；保留自愿成本退出差异有效对象（effective_object）满足真实成本、自愿性、方向和结构后果条件的人类行动跨尺度保持项（scale_invariants）1. 成本、自愿性、方向、替代解释、后果与停止权升格必补项（required_scale_additions）1. 自愿性分布2. 代表关系3. 成本外溢4. 真实退出与代理保护随尺度改变项（changing_semantics）1. 承担形式、成本位置和受益对象可改变不适用对象（non_applicable_objects）1. 无意向、自愿性、责任或意义能力的非人系统禁止升格（forbidden_elevation）1. 个体承担升格为群体义务2. 人类承担概念迁入非人核心

来源：`V90-P03858`



来源：`V90-P03859`

D. 状态、证据与变量流

来源：`V90-P03860`, `V90-P03861`, `V90-P03862`, `V90-P03863`, `V90-P03864`, `V90-P03865`, `V90-P03866`, `V90-P03867`, `V90-P03868`, `V90-P03869`, `V90-P03870`, `V90-P03871`, `V90-P03872`, `V90-P03873`, `V90-P03874`, `V90-P03875`, `V90-P03876`, `V90-P03877`, `V90-P03878`, `V90-P03879`

字段登记内容状态集合（state）1. 候选2. 自愿且有限3. 强制风险4. 单方耗竭5. 停止或退出可观测项（observables）1. 行动投入的时间、资源、机会与身体心理成本2. 拒绝、退出、停止和重新协商是否真实可用3. 行动方向、受益位置和可检测结构后果4. 强制、恐惧、依赖、利益与表演等替代解释证据要求（evidence）1. 行动与成本2. 拒绝和退出条件3. 替代解释4. 受益与后果输入依赖与接口内容（input_dependencies）1. 指向锚点2. 承接层3. 条件势场4. 权力与安全输出效应与变量流（output_effects）1. 成本分布2. 关系和制度状态3. 停止与修复时间窗与时滞（time_window_and_lag）登记即时成本、持续承担、耗竭与恢复时滞不确定性（uncertainty）记录依赖、恐惧、隐性强制与表达安全局部排除区（local_exclusion_zone）无法安全拒绝、无法退出或被道德压力遮蔽的位置受影响位置（affected_positions）1. 行动者2. 受益者3. 依赖者4. 替代承接者

来源：`V90-P03880`



来源：`V90-P03881`

E. 承接、责任、规范、上限与纠错

来源：`V90-P03882`, `V90-P03883`, `V90-P03884`, `V90-P03885`, `V90-P03886`, `V90-P03887`, `V90-P03888`, `V90-P03889`, `V90-P03890`, `V90-P03891`, `V90-P03892`, `V90-P03893`, `V90-P03894`, `V90-P03895`, `V90-P03896`, `V90-P03897`, `V90-P03898`, `V90-P03899`

字段登记内容承接载体（carrier）1. 具体行动者2. 关系实践3. 照护或责任安排责任主体（responsible_subject）1. 提出要求者2. 授权者3. 受益责任者4. 补救责任者规范地位（normative_status）受N4约束，不可命令或征用判断上限（judgment_ceiling）按R0/R1/R2分别限制：R0只作成本、方向、风险及候选行动描述；R1在相应证据下作自愿性、拒绝和退出条件的行动描述；R2只有在相应G2及因果条件成立时，才作限定范围的结构后果判断。任何一级均不得进入人格诊断、证明爱或善、推出承担义务或生成现实授权。伦理命名另受GOV-14的规范前提约束，不能以达到R2代替该要求。行动上限（action_ceiling）本变量只生成自愿性、真实成本、方向、替代解释、结构后果与停止保护需求描述，不授权保护措施、承担要求、资源征用或人格裁决；任何现实调整须另过C12、运行时显式N前提、J授权与O程序反例（counterexamples）1. 无法拒绝的单方牺牲被赞美为爱或责任2. 承担宣称没有真实成本、行动方向或可检测结构后果申诉（appeal）依appeal_and_rollback_rule，行动者可经安全可达、反报复通道拒绝被代表，说明强制、成本、替代解释和退出限制，并触发与原承担判断或要求链独立的复核回滚（rollback）依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销承担命名与相关要求，实际恢复拒绝、退出、记录和资源状态，保留版本与完成验证

来源：`V90-P03900`



来源：`V90-P03901`

scale_profile 不是“微观—宏观”的单轴标签，而是 SP=<A,X,T,O,C,R,I,N,J> 的完整九轴记录：A 是聚合层次，必须声明单元、总体、分布和聚合规则；X 是物理空间与数字边界；T 是窗口、时滞和周期；O 是角色、团队、组织、制度与治理生态的组织层级；C 是事件、互动机制、中观结构、制度和系统条件的因果层次；R 是原始事件、序列、个案、分布、指标与摘要的观察分辨率，并记录压缩损失；I 是直接、间接、二阶、跨域与代际的受影响范围；N 是网络拓扑范围；J 是管辖与授权范围。扩大 A、X、O 或 I 不会自动扩大 J；观察更多不能产生更大处置权。

来源：`V90-P03902`

身份与同一性判据属于对象合同 K，关系与作用通道进入 input_dependencies、carrier 或因果合同，成员与受影响位置进入 affected_positions、local_exclusion_zone 和观察字段；它们都不能冒充尺度轴。尺度轴 N 指网络拓扑；下文“运行时显式 N 前提”指规范选择层 N1-N5，两者不可混用。

来源：`V90-P03903`

十一项变量共享同一行动边界：变量本身只生成描述、证据缺口与行动需求，不授权现实调整。其输出上限如下。

来源：`V90-P03904`, `V90-P03905`, `V90-P03906`, `V90-P03907`, `V90-P03908`, `V90-P03909`, `V90-P03910`, `V90-P03911`, `V90-P03912`, `V90-P03913`, `V90-P03914`, `V90-P03915`, `V90-P03916`, `V90-P03917`, `V90-P03918`, `V90-P03919`, `V90-P03920`, `V90-P03921`, `V90-P03922`, `V90-P03923`, `V90-P03924`, `V90-P03925`, `V90-P03926`, `V90-P03927`

变量本变量可生成的描述或需求HV01候选结构域、边界争议与补证需求HV02边界状态、接口障碍、排除风险与测试需求HV03候选锚点、异质表达、比较结果与补证需求HV04GC、GS、GE 候选分型、状态转移与补证需求HV05CV、RS、成本、容量、停止权、承接缺口及减载、补资源或重分配需求HV06链条连通、时滞、损耗、中断、成本与承接需求HV07受理、字段变化、执行、持续时间、写回缺口与程序修复需求HV08候选条件通道、位置异质性、证据遮蔽与风险降低需求HV09负荷、容量、恢复、局部过载与减载补资源需求HV10相位原型匹配、混合状态、不确定性与观察需求HV11自愿性、真实成本、方向、替代解释、结构后果与停止保护需求

来源：`V90-P03928`



来源：`V90-P03929`

无论需求看起来多么明显，任何现实调整都须另过 C12、运行时显式 N 前提、J 授权与 O 程序。变量不得自行授权测试、减载、补资源、修复、保护、归责、试探、推进、退出安排或处置。

## 解释层

允许边界：R1可观察后果限描述；R2因果须G2；伦理命名另过GOV-14。

禁止边界：R1后果等于因果，R2等于爱；低成本等于无价值。

## 依赖角色

| role | target | condition | basis |
| --- | --- | --- | --- |
| `inferential_requires` | `V90-CANON-G2` | HV11-R2-structural-consequence | body 1675, conditional_support_routes; target requires a qualified instance | appendix candidate adjudication |
| `inferential_requires` | `V90-EXTERNAL-GATE-G2-INSTANCE` | HV11-R2-structural-consequence | body 1675, conditional_support_routes |
| `input_dependencies` | `V90-EXTERNAL-GATE-INPUT-HUMAN-VARIABLE-HV11` | base | source interface field at body 1681 |
| `protocol_requires` | `V90-CANON-E4` | HV11-R2-structural-consequence | body 1675, conditional_support_routes |
| `protocol_requires` | `V90-CANON-E4` | HV11-R2-structural-consequence | body 1675, conditional_support_routes | appendix candidate adjudication |
| `protocol_requires` | `V90-CANON-N4` | base | body 1675, field protocol_requires |
| `protocol_requires` | `V90-CANON-N4` | base | body 1675, field protocol_requires | read at declared role and conditional route ceiling |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL` | HV11-R2-structural-consequence | body 1675, conditional_support_routes |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL-DE06B986` | HV11-R2-structural-consequence | body 1675, conditional_support_routes | appendix candidate adjudication |
| `protocol_requires` | `V90-EXTERNAL-GATE-EVIDENCE` | base | body 1675, field protocol_requires |
| `protocol_requires` | `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0` | base | body 1675, field protocol_requires | read at declared role and conditional route ceiling |
| `protocol_requires` | `V90-EXTERNAL-GATE-SOURCE` | base | body 1675, field protocol_requires |
| `protocol_requires` | `V90-EXTERNAL-GATE-SOURCE-56CCD012` | base | body 1675, field protocol_requires | read at declared role and conditional route ceiling |
| `specializes` | `V90-CANON-H2` | base | body 1675, field specializes |
| `specializes` | `V90-CANON-H2` | base | body 1675, field specializes | read at declared role and conditional route ceiling |
| `specializes` | `V90-CANON-H6` | base | body 1675, field specializes |
| `specializes` | `V90-CANON-H6` | base | body 1675, field specializes | read at declared role and conditional route ceiling |

## source_undefined

- Task-specific empirical parameters and evidence cannot be supplied by the concept definition.

## 条件路由

- `HV11-R0-action-cost-record`：行动、真实成本、方向、替代解释、受益与后果可观察，但自愿性、拒绝或退出尚不充分。；结论上限：不得称开放性承担，不得诊断爱、人格或要求继续承担。
- `HV11-R1-voluntary-limited-action`：真实成本、自愿性、真实拒绝与退出、方向、替代解释和结构后果均分别可见。；结论上限：只到行动描述；不把个体承担升格为群体义务，也不授权征用、保护或资源安排。
- `HV11-R2-structural-consequence`：符合资格的G2-instance显示该行动经指定通道对预选结构结果产生超过阈值的效应。；结论上限：结构效应不证明爱、善、正当性、无限责任或行动授权。
