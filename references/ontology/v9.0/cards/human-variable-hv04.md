---
id: V90-CANON-HUMAN-VARIABLE-HV04
source_concept_id: human_variable:HV04
framework_version: v9.0
---

# human_variable:HV04

## 原文层

来源：`V90-P01022`

7.3.4　HV04 生成节点

来源：`V90-P01023`

生成节点必须拆成 GC、GS 与 GE 三个独立合同，分别记录条件、主体与事件所在的九轴尺度。类型分流路由不硬依赖 HV03，也不因强类型字段齐全就宣称因果生成；只有机制路由另有符合资格的 G2-instance，才登记指定通道内的候选生成机制。可观察信号包括条件变化、主体能力和实际行动、事件前后状态转移，以及无主体涌现的局部—总体桥接。科技、危机和资源窗口只能作为 GC 候选，不能获得意图；生成事件与生成主体也不能互相替代。

来源：`V90-P03109`

A.4　HV04 生成节点（完整接口卡）

来源：`V90-P03110`

A. 身份、命题与适用范围

来源：`V90-P03111`, `V90-P03112`, `V90-P03113`, `V90-P03114`, `V90-P03115`, `V90-P03116`, `V90-P03117`, `V90-P03118`, `V90-P03119`, `V90-P03120`, `V90-P03121`, `V90-P03122`, `V90-P03123`, `V90-P03124`, `V90-P03125`, `V90-P03126`, `V90-P03127`, `V90-P03128`

字段登记内容接口 ID（id）HV04限定 ID（qualified_id）human_variable:HV04名称（name）生成节点主张类型（claim_type）H合同角色（contract_role）human_variable_interface命题（proposition）生成必须分流为生成条件GC、生成主体GS与生成事件GE，允许无可识别主体的涌现型生成。适用范围（scope）人类结构中新行动、组织、制度或状态转移的形成暂停条件（pause_condition）条件被人格化、事件被当作主体或主体资格不明

来源：`V90-P03129`



来源：`V90-P03130`

B. 正式依赖与推论边界

来源：`V90-P03131`, `V90-P03132`, `V90-P03133`, `V90-P03134`, `V90-P03135`, `V90-P03136`, `V90-P03137`, `V90-P03138`, `V90-P03139`, `V90-P03140`, `V90-P03141`, `V90-P03142`, `V90-P03143`, `V90-P03144`, `V90-P03145`, `V90-P03146`

字段登记内容推论依赖（inferential_requires）无（空集合）协议依赖（protocol_requires）1. EVIDENCE2. SOURCE限定／特化（specializes）无（空集合）适用对象引用（applies_to）无（空集合）条件支持路由（conditional_support_routes）1. route_id=HV04-R0-generation-typing；claim_level=descriptive_classification；when=GC、GS与GE的规定字段可分别登记，并保留无主体涌现与未识别主体状态。；additional_inferential_requires=无（空集合）；additional_protocol_requires=无（空集合）；allowed_conclusion=分别登记候选生成条件、候选生成主体与候选生成事件，不将三者互相替代。；result_ceiling=只到强类型分类；条件、主体或事件任一存在都不证明另两项或因果生成机制。2. route_id=HV04-R1-generation-mechanism；claim_level=mechanism_explanation；when=预注册G2-instance识别GC、GS或无主体涌现通道对指定GE状态转移的超过阈值效应。；additional_inferential_requires=G2-instance；additional_protocol_requires=CAUSAL、E4；allowed_conclusion=登记指定尺度、窗口和通道内的候选生成机制及其GC、GS、GE分型。；result_ceiling=不得把条件人格化、把事件倒推为主体，或从生成事实推出正当性、责任与授权。允许推论（allowed_inference）1. 条件性生成路径2. 有主体或无主体生成禁止跳跃（prohibited_leap）1. 技术或危机具有意图2. 生成主体自动拥有持续授权

来源：`V90-P03147`



来源：`V90-P03148`

C. 九轴尺度与对象合同

来源：`V90-P03149`, `V90-P03150`, `V90-P03151`, `V90-P03152`, `V90-P03153`, `V90-P03154`, `V90-P03155`, `V90-P03156`, `V90-P03157`, `V90-P03158`, `V90-P03159`, `V90-P03160`, `V90-P03161`, `V90-P03162`, `V90-P03163`, `V90-P03164`

字段登记内容九轴尺度画像（scale_profile）SP=<A,X,T,O,C,R,I,N,J>；A=聚合层次：条件暴露、主体行动与生成事件单元，各自个案总体、分布及聚合规则；X=空间范围：生成现场、组织或平台边界、扩散区域与跨域环境；T=时间跨度：条件积累期、主体行动窗、事件时点与扩散时滞；O=组织层级：行动角色、生成团队、组织、制度至治理生态；C=因果层次：生成事件、主体—条件互动机制、中观生成结构、制度安排与系统条件；R=观察分辨率：原始条件行动事件、生成序列、个案、结果分布、转移指标与摘要，并登记压缩损失；I=影响范围：直接生成参与者、承接者、间接受影响者、二阶后果、跨域与代际影响；N=网络拓扑范围：条件传播、主体协作、事件扩散与涌现连接；J=管辖与授权范围：生成识别、启动改变、资源投入及扩散处置分别登记授权；GC、GS、GE分别登记尺度有效对象（effective_object）形成可检测状态转移的条件、主体与事件组合跨尺度保持项（scale_invariants）1. GC、GS、GE强类型分离升格必补项（required_scale_additions）1. 新单位与总体2. 代表关系3. 责任类型4. 外部影响随尺度改变项（changing_semantics）1. 生成主体、条件与事件可随尺度改变不适用对象（non_applicable_objects）1. 没有新状态形成或生成主张的稳定描述禁止升格（forbidden_elevation）1. 把条件或事件升格为有意图主体

来源：`V90-P03165`



来源：`V90-P03166`

D. 状态、证据与变量流

来源：`V90-P03167`, `V90-P03168`, `V90-P03169`, `V90-P03170`, `V90-P03171`, `V90-P03172`, `V90-P03173`, `V90-P03174`, `V90-P03175`, `V90-P03176`, `V90-P03177`, `V90-P03178`, `V90-P03179`, `V90-P03180`, `V90-P03181`, `V90-P03182`, `V90-P03183`, `V90-P03184`, `V90-P03185`, `V90-P03186`

字段登记内容状态集合（state）1. 潜在2. 触发3. 形成4. 中断5. 扩散可观测项（observables）1. 候选条件出现、改变或移除的时间记录2. 生成主体的能力、授权、决策与实际行动3. 生成事件前后预注册状态转移4. 无主体涌现时局部互动与总体结果的桥接记录证据要求（evidence）1. 启动记录2. 条件窗口3. 主体行动4. 无主体互动机制输入依赖与接口内容（input_dependencies）1. 指向锚点2. 资源与制度条件3. 因果合同输出效应与变量流（output_effects）1. 承接需求2. 状态转移3. 责任链起点时间窗与时滞（time_window_and_lag）登记条件积累、触发事件与形成时滞不确定性（uncertainty）记录共同生成、无主体涌现和不可识别主体局部排除区（local_exclusion_zone）被遗漏的非正式启动者与受影响位置受影响位置（affected_positions）1. 启动者2. 承接者3. 受益者4. 受影响者

来源：`V90-P03187`



来源：`V90-P03188`

E. 承接、责任、规范、上限与纠错

来源：`V90-P03189`, `V90-P03190`, `V90-P03191`, `V90-P03192`, `V90-P03193`, `V90-P03194`, `V90-P03195`, `V90-P03196`, `V90-P03197`, `V90-P03198`, `V90-P03199`, `V90-P03200`, `V90-P03201`, `V90-P03202`, `V90-P03203`, `V90-P03204`, `V90-P03205`, `V90-P03206`

字段登记内容承接载体（carrier）1. 启动者2. 程序3. 技术设施4. 关系网络责任主体（responsible_subject）1. 实际行动者2. 决策者3. 授权者规范地位（normative_status）生成事实不证明正当或责任完整判断上限（judgment_ceiling）机制链完整时至解释级行动上限（action_ceiling）本变量只生成GC、GS、GE候选分型、状态转移描述与补证需求，不授权启动、扩散或停止生成过程；任何现实调整须另过C12、运行时显式N前提、J授权与O程序反例（counterexamples）1. 技术条件被错误描述成具有目标的生成主体2. 无统一发起者的涌现过程被强行归因给一个可见人物申诉（appeal）依appeal_and_rollback_rule，被归为生成主体者可经安全可达、反报复通道挑战意图、角色与授权归因，并触发与原分型或决策链独立的复核回滚（rollback）依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内纠正GC、GS、GE类型，实际移除错误意图或责任归因及其下游效力，保留版本与完成验证

来源：`V90-P03207`



## 解释层

允许边界：仅在本项原文全部适用条件与分支条件内使用human_variable:HV04；独立对象材料支持实例，定义和接口只确定意义。

禁止边界：R0不被高档前提封死；input_dependencies非推理图。

## 依赖角色

| role | target | condition | basis |
| --- | --- | --- | --- |
| `inferential_requires` | `V90-CANON-G2` | HV04-R1-generation-mechanism | body 1563, conditional_support_routes; target requires a qualified instance | appendix candidate adjudication |
| `inferential_requires` | `V90-EXTERNAL-GATE-G2-INSTANCE` | HV04-R1-generation-mechanism | body 1563, conditional_support_routes |
| `input_dependencies` | `V90-EXTERNAL-GATE-INPUT-HUMAN-VARIABLE-HV04` | base | source interface field at body 1569 |
| `protocol_requires` | `V90-CANON-E4` | HV04-R1-generation-mechanism | body 1563, conditional_support_routes |
| `protocol_requires` | `V90-CANON-E4` | HV04-R1-generation-mechanism | body 1563, conditional_support_routes | appendix candidate adjudication |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL` | HV04-R1-generation-mechanism | body 1563, conditional_support_routes |
| `protocol_requires` | `V90-EXTERNAL-GATE-CAUSAL-DE06B986` | HV04-R1-generation-mechanism | body 1563, conditional_support_routes | appendix candidate adjudication |
| `protocol_requires` | `V90-EXTERNAL-GATE-EVIDENCE` | base | body 1563, field protocol_requires |
| `protocol_requires` | `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0` | base | body 1563, field protocol_requires | read at declared role and conditional route ceiling |
| `protocol_requires` | `V90-EXTERNAL-GATE-SOURCE` | base | body 1563, field protocol_requires |
| `protocol_requires` | `V90-EXTERNAL-GATE-SOURCE-56CCD012` | base | body 1563, field protocol_requires | read at declared role and conditional route ceiling |

## source_undefined

- Task-specific empirical parameters and evidence cannot be supplied by the concept definition.

## 条件路由

- `HV04-R0-generation-typing`：GC、GS与GE的规定字段可分别登记，并保留无主体涌现与未识别主体状态。；结论上限：只到强类型分类；条件、主体或事件任一存在都不证明另两项或因果生成机制。
- `HV04-R1-generation-mechanism`：预注册G2-instance识别GC、GS或无主体涌现通道对指定GE状态转移的超过阈值效应。；结论上限：不得把条件人格化、把事件倒推为主体，或从生成事实推出正当性、责任与授权。
