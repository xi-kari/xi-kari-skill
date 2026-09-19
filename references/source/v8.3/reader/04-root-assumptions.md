# 第四部分　根假设与推论

Source: `v8.3`
Raw SHA256: `4a3ad8e8692b7a906f733096bbc8e05d0ac4f8cfbf79d3926eb1729df828c7f5`
Semantic SHA256: `f190a80be88033ba21d717a310f4419c00489b3a6dea17b6a1e2b14af1447d9f`
List structure SHA256: `967dd396860e4b5d246ae2e3699eb33b8ab8ee46ca12bb72959e1249216d7a5f`
Paragraph range: `V83-P0585`-`V83-P0862`
Tables: `V83-T006`, `V83-T007`, `V83-T008`, `V83-T009`, `V83-T010`, `V83-T011`

<!-- This is a lossless reader edition; anchors are source coordinates. -->

<!-- source-paragraph:V83-P0585 style=PartTitle -->
# 第四部分　根假设与推论

<!-- source-paragraph:V83-P0586 style=BodyCJK -->
根假设是通用经验问题的预注册模板，不是关于一切对象的无条件定律。G1—G4 分别询问：候选分组是否带来条件增益，指定通道是否对目标转移具有可识别效应，历史项是否在当前状态之外提供条件增量，以及尺度变换是否破坏闭合、对象或干预的同一性。抽象模板没有独立的经验真值；只有完成实例合同并通过预定门槛的 G-instance，才能在其 SP/T/K 与外推单元内获得有限支持。

<!-- source-paragraph:V83-P0587 style=SecH2 -->
## 4.1　根实例合同

<!-- source-paragraph:V83-P0588 style=BodyCJK -->
每个根实例分成不可混写的两段：预注册段必须在读取结果前完成，结果段只能在执行后追加且不得改写预注册版本。为保持机器字段稳定，草案或冻结快照仍保留结果字段的键：result_state=not_evaluated，其余结果字段使用带理由的 not_evaluated 缺失对象，而不是虚构时间、观测值或制品引用。实例运行后才以具体结果替换这些缺失状态。两段共同确定什么结果算支持、什么结果算反驳，以及结论可以外推到哪里。

## V83-T006

<table data-source-table="V83-T006">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P0589">
<!-- source-paragraph:V83-P0589 style=TableHead -->
<pre>合同部分</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P0590">
<!-- source-paragraph:V83-P0590 style=TableHead -->
<pre>必填字段</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P0591">
<!-- source-paragraph:V83-P0591 style=TableHead -->
<pre>作用</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P0592">
<!-- source-paragraph:V83-P0592 style=TableText -->
<pre>身份与冻结</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P0593">
<!-- source-paragraph:V83-P0593 style=TableText -->
<pre>instance_id、root_id、contract_version、preregistration_timestamp</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P0594">
<!-- source-paragraph:V83-P0594 style=TableText -->
<pre>区分实例与根模板，以不可变版本和早于结果访问的可审计时间戳证明合同先于证据</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P0595">
<!-- source-paragraph:V83-P0595 style=TableText -->
<pre>候选对象</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P0596">
<!-- source-paragraph:V83-P0596 style=TableText -->
<pre>candidate_object_id、object_contract_id</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P0597">
<!-- source-paragraph:V83-P0597 style=TableText -->
<pre>指向 D0 候选对象及其合同，防止把名称当作对象支持</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P0598">
<!-- source-paragraph:V83-P0598 style=TableText -->
<pre>尺度与目标</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P0599">
<!-- source-paragraph:V83-P0599 style=TableText -->
<pre>scale_profile、time_window、identity_criterion、target_variables</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P0600">
<!-- source-paragraph:V83-P0600 style=TableText -->
<pre>冻结 SP、T、K 与待解释变量</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V83-P0601">
<!-- source-paragraph:V83-P0601 style=TableText -->
<pre>命题实例化</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V83-P0602">
<!-- source-paragraph:V83-P0602 style=TableText -->
<pre>selected_subtype、selected_success_criterion、candidate_specification、zero_model、controls、model_classes</pre>
</td>
<td data-source-cell="5,3" data-paragraphs="V83-P0603">
<!-- source-paragraph:V83-P0603 style=TableText -->
<pre>在证据出现前只选一个子型，再从该子型的允许列表中只选一个成功判据，并声明候选命题、N0、控制和模型族</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V83-P0604">
<!-- source-paragraph:V83-P0604 style=TableText -->
<pre>抽样与外推</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V83-P0605">
<!-- source-paragraph:V83-P0605 style=TableText -->
<pre>sampling_unit、generalization_unit</pre>
</td>
<td data-source-cell="6,3" data-paragraphs="V83-P0606">
<!-- source-paragraph:V83-P0606 style=TableText -->
<pre>分开资料来自何处与结论允许推广到何处</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V83-P0607">
<!-- source-paragraph:V83-P0607 style=TableText -->
<pre>决策规则</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V83-P0608">
<!-- source-paragraph:V83-P0608 style=TableText -->
<pre>evaluation_metric、decision_threshold、decision_rule、null_decision_rule</pre>
</td>
<td data-source-cell="7,3" data-paragraphs="V83-P0609">
<!-- source-paragraph:V83-P0609 style=TableText -->
<pre>分开正向门与零结论门；冻结主目标或聚合、模型选择或集成、多重比较、等价性或充分性、功效或灵敏度及容差</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V83-P0610">
<!-- source-paragraph:V83-P0610 style=TableText -->
<pre>模式与失败</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V83-P0611">
<!-- source-paragraph:V83-P0611 style=TableText -->
<pre>evidence_mode、falsifier、pause_condition</pre>
</td>
<td data-source-cell="8,3" data-paragraphs="V83-P0612">
<!-- source-paragraph:V83-P0612 style=TableText -->
<pre>声明探索、确认、复制或反驳模式，以及各自的结论上限、证伪和暂停条件</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V83-P0613">
<!-- source-paragraph:V83-P0613 style=TableText -->
<pre>偏离与状态</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V83-P0614">
<!-- source-paragraph:V83-P0614 style=TableText -->
<pre>deviation_record、preregistration_status</pre>
</td>
<td data-source-cell="9,3" data-paragraphs="V83-P0615">
<!-- source-paragraph:V83-P0615 style=TableText -->
<pre>逐项记录偏离、时间、原因与影响；无偏离也登记 none，并区分草案、证据前冻结、按冻结合同完成和证据后偏离</pre>
</td>
</tr>
<tr>
<td data-source-cell="10,1" data-paragraphs="V83-P0616">
<!-- source-paragraph:V83-P0616 style=TableText -->
<pre>结果与时间</pre>
</td>
<td data-source-cell="10,2" data-paragraphs="V83-P0617">
<!-- source-paragraph:V83-P0617 style=TableText -->
<pre>result_timestamp、observed_primary_result、decision_rule_outcome、null_decision_rule_outcome、result_state</pre>
</td>
<td data-source-cell="10,3" data-paragraphs="V83-P0618">
<!-- source-paragraph:V83-P0618 style=TableText -->
<pre>结果时间晚于冻结时间；只记录预冻结主目标和规则的观测结果，分别登记正向门与零结论三门是否通过，并使用封闭四态结案</pre>
</td>
</tr>
<tr>
<td data-source-cell="11,1" data-paragraphs="V83-P0619">
<!-- source-paragraph:V83-P0619 style=TableText -->
<pre>证据与分析制品</pre>
</td>
<td data-source-cell="11,2" data-paragraphs="V83-P0620">
<!-- source-paragraph:V83-P0620 style=TableText -->
<pre>evidence_refs、analysis_artifact_refs</pre>
</td>
<td data-source-cell="11,3" data-paragraphs="V83-P0621">
<!-- source-paragraph:V83-P0621 style=TableText -->
<pre>指向可解析外部材料、数据冻结、代码、模型或日志；内部概念编号、字符串前缀和自报结论不能代替实例</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P0622 style=BodyCJK -->
选择规则记为 one_subtype_and_success_criterion_before_evidence：一个实例只能在结果出现前选择一个 selected_subtype，并从该子型的 allowed_success_criteria 中只选择一个 selected_success_criterion。评价指标、正向阈值、零模型、decision_rule、null_decision_rule 和证伪条件都围绕该判据冻结。若结果不利，不能把多个子型或多个成功判据事后并取，也不能改换目标、模型、指标或阈值来挽救根假设。

<!-- source-paragraph:V83-P0623 style=BodyCJK -->
decision_rule 还封闭多目标与多模型的研究自由度：目标变量多于一个时，结果前必须冻结唯一主目标或聚合规则；模型类别多于一个时，必须冻结模型选择或集成规则；存在多重比较时，必须冻结校正规则。没有这些规则，一个实例只能有一个主目标和一个主模型。null_decision_rule 则另行声明：何种等价性或充分性检验、功效或灵敏度门与容差可以支持 N0。执行后，decision_rule_outcome 必须结构化记录阈值、观测值、是否通过及分析制品；null_decision_rule_outcome 分别记录零结论三门。正向判据未通过，不等于零模型已获支持；零结论门未冻结或未全部通过时，结果保持 unsupported_or_undecided。

<!-- source-paragraph:V83-P0624 style=BodyCJK -->
根实例结果只允许四态：supported、unsupported_or_undecided、null_supported、not_evaluated。supported 要求合格实例的正向门通过；null_supported 要求等价性或充分性、功效或灵敏度及容差全部通过；not_evaluated 只表示尚未运行。结果记录必须链接 evidence_refs 与 analysis_artifact_refs，并保留结果时间、合同版本和偏离记录。抽象根族或格式正确的实例 ID 都不能独立产生支持。

<!-- source-paragraph:V83-P0625 style=BodyCJK -->
实例能否支撑 C 推论还受 support_eligibility_rule 约束。正向支持只来自带可审计版本和时间戳、在结果前状态为 frozen_before_evidence、并按冻结合同完成为 completed_from_frozen 的 confirmatory 或 replication 实例，同时要求 decision_rule_outcome.passed=true、结果状态和外部证据/分析制品可解析。falsification 实例只可支持预注册的反驳或零模型判断，不能反向救援正向 G。exploratory、draft、deviated_after_evidence 或存在未披露偏离的实例只能生成候选、记录偏离或保持未决，不得支撑 C。内部定义、概念标签和框架自身说明均不构成实例的经验支持。

<!-- source-paragraph:V83-P0626 style=BodyCJK -->
四个根的尺度不变量共同包括预选子型、成功判据、decision_rule 与 null_decision_rule；尺度迁移时必须保留，不能改换。申诉可以挑战候选对象、子型、成功判据、N0、主目标或聚合、模型选择或集成、多重比较、控制、正向阈值、零结论规则、数据分割、外推单元、合同版本、预注册状态、偏离记录和证伪条件。任何一项被证明在结果后改变，都要降低支持资格，不得以事后版本覆盖已经冻结的记录。

<!-- source-paragraph:V83-P0627 style=SecH2 -->
## 4.2　人类经验实例合同

<!-- source-paragraph:V83-P0628 style=BodyCJK -->
H1、H4、H5 不是通用根假设，却同样是抽象经验假设族，不能靠名称、接口字段或框架定义获得真值。它们使用独立的 human_empirical_instance_contract：身份字段以 claim_id 取代 root_id，且只允许 H1、H4、H5；其余预注册段、结果段、缺失编码、版本冻结、阶段、结果四态、偏离披露、正向门、零结论门、证据引用和分析制品纪律与根实例合同同构。相应实例正式称为 H1-instance、H4-instance、H5-instance；经验真值属于这些具体 H-instance，不属于抽象 H 命题。

<!-- source-paragraph:V83-P0629 style=BodyCJK -->
H-instance 也必须在读取结果前唯一预选一个子型和该子型的一个成功判据。三类命题的选择空间如下。

## V83-T007

<table data-source-table="V83-T007">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P0630">
<!-- source-paragraph:V83-P0630 style=TableHead -->
<pre>命题</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P0631">
<!-- source-paragraph:V83-P0631 style=TableHead -->
<pre>必须唯一预选的子型或结果家族</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P0632">
<!-- source-paragraph:V83-P0632 style=TableHead -->
<pre>允许的成功判据</pre>
</td>
<td data-source-cell="1,4" data-paragraphs="V83-P0633">
<!-- source-paragraph:V83-P0633 style=TableHead -->
<pre>结论停止位置</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P0634">
<!-- source-paragraph:V83-P0634 style=TableText -->
<pre>H1 意义与协调</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P0635">
<!-- source-paragraph:V83-P0635 style=TableText -->
<pre>资源配置结果、行动选择结果、协调结果三选一</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P0636">
<!-- source-paragraph:V83-P0636 style=TableText -->
<pre>meaning_arrangement_resource_allocation_effect、meaning_arrangement_action_choice_effect、meaning_arrangement_coordination_outcome_effect 中与所选子型对应的一项</pre>
</td>
<td data-source-cell="2,4" data-paragraphs="V83-P0637">
<!-- source-paragraph:V83-P0637 style=TableText -->
<pre>只登记指定对象、尺度、窗口和结果家族内的条件性指向锚点；不推出统一内心、真实同意或共同意志</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P0638">
<!-- source-paragraph:V83-P0638 style=TableText -->
<pre>H4 权力、中介与反身性</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P0639">
<!-- source-paragraph:V83-P0639 style=TableText -->
<pre>证据覆盖、表达安全、对象行为、反身响应四选一</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P0640">
<!-- source-paragraph:V83-P0640 style=TableText -->
<pre>position_or_mediation_evidence_coverage_effect、position_or_mediation_expression_safety_effect、mediation_or_publicity_behavioral_response_effect、observation_or_publication_reflexive_response_effect 中与所选子型对应的一项</pre>
</td>
<td data-source-cell="3,4" data-paragraphs="V83-P0641">
<!-- source-paragraph:V83-P0641 style=TableText -->
<pre>只登记指定位置、中介、公开条件、通道和结果家族内的遮蔽、放大、行为或反身响应；不推出恶意、责任或自动处置</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P0642">
<!-- source-paragraph:V83-P0642 style=TableText -->
<pre>H5 历史留痕载体</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P0643">
<!-- source-paragraph:V83-P0643 style=TableText -->
<pre>先在 institutional_or_textual_record、role_or_organizational_arrangement、habit_or_practice、trauma_record、collective_memory_carrier 五个载体家族中唯一预选一个子型，再填写与该子型一致的 selected_carrier_family_id 和一个具体 selected_carrier 原子引用</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P0644">
<!-- source-paragraph:V83-P0644 style=TableText -->
<pre>threshold_persistence_over_preregistered_window、repeat_detection_across_preregistered_windows、persistence_after_event_or_exposure_end 三选一</pre>
</td>
<td data-source-cell="4,4" data-paragraphs="V83-P0645">
<!-- source-paragraph:V83-P0645 style=TableText -->
<pre>只登记指定载体、可观察量和窗口内的候选留痕；未来路径效应仍须独立 G3-instance</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P0646 style=BodyCJK -->
H1 不能在资源、行动、协调三个结果中“任一有利即成立”；H4 不能在证据覆盖、表达安全、行为和反身响应之间事后择优；H5 不能在多个载体或多个持久判据中寻找一个幸存结果。H5 的 selected_carrier 必须是一个非空原子引用而不是列表，selected_carrier_family_id 必须与所选子型的 carrier_family_id 完全一致；否则实例在读取结果前就不具备资格。多目标、多模型与多重比较仍须在 decision_rule 中冻结唯一主目标或聚合、模型选择或集成及校正规则。正向门未过时默认是 unsupported_or_undecided；只有预注册 null_decision_rule 中的等价性或充分性、功效或灵敏度及容差全部通过，才是 null_supported。探索性、证据后偏离或未披露偏离的 H-instance 只生成候选或未决，不能把 HV03、HV08 或 H5 历史载体路由升级为经验成立。

<!-- source-paragraph:V83-P0647 style=BodyCJK -->
H2、H3、H6 不进入这份经验实例合同。H2 是承接与责任分型规则，H3 是制度写回分类规则，H6 是开放性承担的规范边界；它们可以限定接口怎样分类或停止，却不能凭分类成功产生经验机制支持。任何 H-instance 即使获得 supported，也只提高描述或解释强度，不产生价值、责任、义务、正当性、授权或现实处置。

<!-- source-paragraph:V83-P0648 style=SecH2 -->
## 4.3　G1 候选分组的条件增益

<!-- source-paragraph:V83-P0649 style=BodyCJK -->
命题：在对象、尺度、时间窗、K、候选分组和阈值均已预先登记的实例中，若候选分组在控制共同环境、采样或分类偏差及分组泄漏后，相对于复杂度匹配的N0仍取得预定样本外增益，并通过边界扰动及独立时间块或地点复核，则该分组在该SP/T/K下获得有限的对象识别支持。

<!-- source-paragraph:V83-P0650 style=BodyCJK -->
G1 检验的不是“世界上是否终极存在这个对象”，而是当前候选分组是否比复杂度匹配、且不使用该分组信息的 N0 更能解释预定的样本外差异。G1a 只允许选择 out_of_sample_predictive_gain，G1b 只允许选择 out_of_sample_intervention_gain；子型与判据都不能在结果后互换。共同环境、采样程序、分类偏差、分组泄漏和模型复杂度必须进入控制或竞争解释。

<!-- source-paragraph:V83-P0651 style=BodyCJK -->
最低正向支持需要预定评价指标与阈值、相对 N0 的样本外增益、边界扰动稳健性，以及独立时间块或地点复核，并且实例满足支持资格。样本外增益未过正向阈值，或边界扰动、独立复核未再现，默认只表示 G1 未获支持或结果未决；只有预注册 null_decision_rule 中的等价性或充分性检验以及功效、灵敏度与容差门通过，才可支持 N0 或反驳对应 G1-instance。对象、分组、成功判据、N0、决策规则、阈值、数据分割或泄漏控制未在结果前冻结时，实例暂停。通过 G1 只允许登记限定 SP/T/K 内的对象识别强度、边界可信度和分组适用窗，不允许作终极本体裁决，也不生成主体、目标、价值、责任或授权。

<!-- source-paragraph:V83-P0652 style=SecH2 -->
## 4.4　G2 指定通道效应与逐维有限性

<!-- source-paragraph:V83-P0653 style=BodyCJK -->
命题：G2必须在结果出现前唯一预选一个子型及成功判据。在预先指定的载体或通道实例中，只有预选的受控扰动、受控干预或具备识别条件的自然变异使指定状态转移出现超过预定阈值的差异，才把该通道登记为该转移的候选因果承载。容量、时延、可靠性、可控性和损耗必须逐通道、逐维度分别测量；未测维度不随命题成立。

<!-- source-paragraph:V83-P0654 style=BodyCJK -->
G2a 预注册受控识别，并必须在 controlled_perturbation_effect 与 controlled_intervention_effect 中唯一预选一个；不能把“扰动或干预任一成功”写成一个事后析取判据。G2b 预注册具备识别条件的自然变异，唯一允许判据为 identified_natural_variation_channel_effect。两种子型都要先指定通道、目标转移、量的类型与单位、比较阈值和待测维度。零模型只按被选判据书写：预选的扰动、干预或自然变异不使目标转移出现超过阈值的差异；未预选判据不参与实例成败。各有限维度分别以无差异或预定基线为 N0。

<!-- source-paragraph:V83-P0655 style=BodyCJK -->
G2 不宣称所有因果过程都有当前可见通道，也不宣称所有通道在所有维度都有限。只测得时延，不能连带宣布容量、可靠性、可控性和损耗已经成立。只有同型量，或具有明确类型转换、单位、核算边界与会计规则的量，才可进一步追踪转移。预选判据未产生阈值以上差异，默认只记正向 G2 未获支持或未决；只有预注册为反驳或零判断、且相应零结论规则通过，才可反驳该实例。共同输入、替代通道或测量协议能够解释差异时，应撤回候选通道支持；未预选判据的有利结果不能救援。G2 只能定位候选因果承载与已测维度的限制，不能创造跨领域统一成本，更不能把载体变成责任主体。

<!-- source-paragraph:V83-P0656 style=SecH2 -->
## 4.5　G3 历史项的条件增量

<!-- source-paragraph:V83-P0657 style=BodyCJK -->
命题：G3必须在结果出现前唯一预选一个子型及成功判据。若历史变量在观察未来结果前已经定义，并在控制当前注册状态、环境与测量协议后，对预定结果提供可复核的样本外条件增量信息，则G3a可支持预测性路径依赖；G3b除该条件增量外，还必须在历史擦除、历史恢复或等价干预中预选一个判据，并且只有该判据超过预定阈值时才支持因果路径依赖。

<!-- source-paragraph:V83-P0658 style=BodyCJK -->
G3a 检验预测性路径依赖，唯一允许判据为 historical_conditional_predictive_gain。G3b 检验因果路径依赖，必须在 history_erasure_effect、history_restoration_effect、equivalent_intervention_effect 中唯一预选一个；不能等结果出来后再从擦除、恢复或等价干预中挑选有利结果。前者要求历史变量在当前注册状态之外，对预定未来结果提供样本外条件增量；后者还要求被预选的因果判据改变结果。G3a 与 G3b 都以当前注册状态构成充分统计量、历史项不提供条件增量为零；G3b 还要求自己预选的干预判据不改变结果，未预选判据不参与成败。

<!-- source-paragraph:V83-P0659 style=BodyCJK -->
痕迹被保存，不等于痕迹进入未来转移；预测增益存在，也不等于历史具有因果效力。历史变量若在见到未来结果后才定义、当前状态明显遗漏，或子型与成功判据未唯一预选，实例暂停。控制当前状态、环境和测量协议后历史项未提供正向增量，或 G3b 预选判据未过正向阈值，默认只记未获支持或未决；只有按冻结的反驳或零结论规则完成，才形成相应反驳。其他未选判据不能用于救援。通过 G3 只允许在预注册窗口内登记预测性或因果性路径差异，不能推出历史宿命、绝对不可逆、责任或授权。

<!-- source-paragraph:V83-P0660 style=SecH2 -->
## 4.6　G4 尺度闭合与对象或干预转换

<!-- source-paragraph:V83-P0661 style=BodyCJK -->
命题：G4必须在结果出现前唯一预选一个子型及该子型的一个成功判据：G4a闭合失败可检验被排除尺度变量在给定目标尺度保留变量后的条件增量信息、条件预测增益或条件干预增益；G4b对象或干预转换可检验尺度变换M与对象动力或干预的非交换、目标映射不满足预冻结K、有效关系改变或干预响应改变；只有预选判据超过预定阈值或容差，才支持对应实例。

<!-- source-paragraph:V83-P0662 style=BodyCJK -->
G4a 与 G4b 回答不同问题。G4a 允许的成功判据是 conditional_information_gain、conditional_predictive_gain、conditional_intervention_gain；每个实例只能预选其中一个。其零模型是：按预选判据，被排除尺度变量在保留变量条件下不提供超过阈值的条件增量。G4b 允许的成功判据是 object_dynamics_non_commutation、intervention_non_commutation、identity_criterion_violation、effective_relation_change、intervention_response_change；每个实例同样只能预选其中一个。零模型也只按被选项书写：对象动力可交换、干预可交换、目标映射满足预冻结 K、有效关系未超容差，或干预响应未超容差，不得把五项合成一个析取兜底。

<!-- source-paragraph:V83-P0663 style=BodyCJK -->
一般相关、无条件耦合、相似叙述和同尺度遗漏变量都不足以支持 G4。结果前未唯一预选子型与成功判据，或 D3/E5 映射、比较模型、正向阈值、null_decision_rule、功效或灵敏度门与容差未冻结，实例暂停。正向判据通过时，G4a 只登记预注册变量、指标、尺度和窗口内的闭合失败，G4b 只登记预注册映射、K、尺度和窗口内的预选转换候选。正向判据未通过，默认只记 G4 未获支持或未决；只有零结论规则中的等价性或充分性检验、功效或灵敏度门及容差实际通过，G4a 才可登记判据限定闭合，G4b 才可登记未发现该预选转换。单纯“未显著”或未过正向阈值，不能直接登记闭合、对象未转换或干预等价。未选判据不得参与救援或反驳。通过 G4 也不表示高尺度更真、更重要或拥有更大处置权。

<!-- source-paragraph:V83-P0664 style=SecH2 -->
## 4.7　一个虚拟的根实例组

<!-- source-paragraph:V83-P0665 style=BodyCJK -->
下面的 m1—m4 只用于展示合同怎样工作。它们描述一个虚构的多层输运模型，没有引用外部观察，不构成任何 G 命题的经验支持。

<!-- source-paragraph:V83-P0666 style=ListPara -->
● m1 / G1a。 候选对象是若干相互连接的单元组，预先冻结 B、X、T、SP、K、分组方式、复杂度匹配 N0，并唯一选择 out_of_sample_predictive_gain 及其指标和阈值。若候选分组只在训练样本有效，或边界轻微扰动后增益消失，m1 失败；只有独立时间块也复现，才得到该窗口内的有限对象识别支持。

<!-- source-paragraph:V83-P0667 style=ListPara -->
● m2 / G2a。 在 m1 的候选对象上，预先指定一条传导通道和目标状态转移，并唯一选择 controlled_perturbation_effect，再对通道作受控阻断。若阻断使目标转移超过阈值地改变，只能把该通道登记为候选因果承载。假设本例只测了时延，则容量、可靠性、可控性和损耗仍是未知，不能随 m2 一并成立。

<!-- source-paragraph:V83-P0668 style=ListPara -->
● m3 / G3a。 先定义“前三轮积压”这一历史变量，并唯一选择 historical_conditional_predictive_gain，再控制当前队列、环境输入和测量协议。若历史项对下一轮结果仍有样本外条件增量，可登记预测性路径依赖；没有历史擦除或恢复干预时，不能升级为因果路径依赖。

<!-- source-paragraph:V83-P0669 style=ListPara -->
● m4 / G4a。 结果前只选择闭合失败子型及 conditional_information_gain，冻结微观与聚合尺度、M、保留变量、被排除变量、指标和阈值。只有被排除的局部时序在给定聚合变量后按该判据提供超过阈值的条件增量，才登记该窗口内的闭合失败；不能在看到结果后改用预测或干预增益，也不能改写为 G4b 的对象转换。

<!-- source-paragraph:V83-P0670 style=BodyCJK -->
这个例子显示，四个实例可以相互提供后续问题，却不会互相替代。m1 通过不保证 m2 的通道有效，m2 通过不保证 m3 的历史效应，m3 通过也不保证 m4 的尺度闭合失败。

<!-- source-paragraph:V83-P0671 style=SecH2 -->
## 4.8　认识论约束 E1—E5

<!-- source-paragraph:V83-P0672 style=SecH3 -->
### 4.8.1　E1 对象声明约束

<!-- source-paragraph:V83-P0673 style=BodyCJK -->
判断前声明对象、尺度、时间窗、变量、零模型和同一性判据。E1 是准入门：字段不全时只允许探索性提问，不能把分析者分组宣布为客观结构域。这里的 N0 属于待检验的具体根实例，而不是 D0 对象向量。

<!-- source-paragraph:V83-P0674 style=SecH3 -->
### 4.8.2　E2 观察位置与模型限制

<!-- source-paragraph:V83-P0675 style=BodyCJK -->
观察位置、测量通道和模型选择限制可见范围；单一视角不完备属于认识论约束。不可见不等于不存在，测量结果也不等于全部状态。盲区显著时，应补证、降级或采用可逆试探。

<!-- source-paragraph:V83-P0676 style=SecH3 -->
### 4.8.3　E3 条件性观测参与

<!-- source-paragraph:V83-P0677 style=BodyCJK -->
只有观察、命名、评分或发布与对象发生实际因果耦合时，才登记观测参与。仅有时序先后或“被观察会改变对象”的机制故事不足以通过；必须定位通道，并建立未观测、替代观测或阻断反事实。

<!-- source-paragraph:V83-P0678 style=SecH3 -->
### 4.8.4　E4 竞争解释与残差保留

<!-- source-paragraph:V83-P0679 style=BodyCJK -->
每项解释都要保留至少一个可区分的竞争解释、反例和未解释残差。开放性、爱、复杂性或理论整体感不能填补证据空白。竞争解释未区分时，不实施高影响、不可逆行动。

<!-- source-paragraph:V83-P0680 style=SecH3 -->
### 4.8.5　E5 跨尺度迁移检验

<!-- source-paragraph:V83-P0681 style=BodyCJK -->
跨尺度迁移必须通过 D3 的映射、不变量、改变项、丢失项、误差、竞争解释与残差检验。E5 的推理硬前提只有 D3；E1、E4、EVIDENCE 与 ANALOGY 都是方法门，不进入推理无环图，也不伪装成额外经验原因。E5 不依赖 G4 为真；反过来，任何 G4-instance 都必须通过 E5。观察范围扩大不意味着授权范围扩大，J 轴不得随其他尺度轴自动外推。

<!-- source-paragraph:V83-P0682 style=SecH2 -->
## 4.9　人类经验条款的证据状态

<!-- source-paragraph:V83-P0683 style=BodyCJK -->
H1（意义与协调）、H4（权力、中介与反身性）与 H5（历史载体）是待检验的经验假设族。三者的经验真值只属于完成 human_empirical_instance_contract 的 H-instance；定义、接口和框架自身表述均不是外部经验支持。没有合格外部实例记录时，empirical_evidence_records=[]，证据状态为 requires_instance_evidence。

<!-- source-paragraph:V83-P0684 style=BodyCJK -->
因此，H1 需逐案在资源、行动或协调中唯一预选一个结果家族并检验意义安排的差异；H4 需逐案在证据覆盖、表达安全、对象行为或反身响应中唯一预选一个结果家族，再建立位置、中介或公开条件的通道和反事实。H5“历史留痕载体”必须唯一预选载体家族、一个具体载体原子引用和一个持久判据；只有家族与子型一致，且历史事件、基线、留痕可观察量、阈值和持久窗口均在结果前冻结，所选判据通过时，才允许登记指定载体与窗口内的候选留痕，并向 G3-instance 提交预先定义的历史变量候选。路径效应与修复窗口另经 G3/C4，保护、减伤或修复行动另经 C12、显式 N 前提与 O 程序。命题名称、内部定义或本框架自身叙述都不能替三者完成实例检验。

<!-- source-paragraph:V83-P0685 style=SecH2 -->
## 4.10　推论合同 C1—C12

<!-- source-paragraph:V83-P0686 style=BodyCJK -->
推论是从已经通过的根实例、定义与明确附加条件得到的受限输出。推理依赖列出进入无环推理图的硬前提；方法门列出协议要求，它们决定能否发布，却不充当经验原因；领域特化与适用关系在正文另行说明。下面四个固定合同字段保持与推论合同同步，证据、反例与失效边界则按推论组集中呈现。

<!-- source-paragraph:V83-P0687 style=SecH2 -->
## 4.11　第一组：对象、承载与反馈

<!-- source-paragraph:V83-P0688 style=SecH3 -->
### 4.11.1　C1 对象与边界强度

<!-- source-paragraph:V83-P0689 style=ListPara -->
● 推理依赖：D0；G1

<!-- source-paragraph:V83-P0690 style=ListPara -->
● 附加条件：使用已完成预注册并取得当前实例支持的G1-instance；候选对象S*、N0、评价阈值、外推单元和边界扰动方案已冻结

<!-- source-paragraph:V83-P0691 style=ListPara -->
● 允许结论：可以在该SP/T/K及外推单元内登记对象识别强度、边界可信度和候选分组适用窗。

<!-- source-paragraph:V83-P0692 style=ListPara -->
● 禁止跳跃：把有限对象识别支持改写为终极本体裁决；推出天然边界、统一主体、共同目标或S0-S6阶段；推出存续价值、责任分配、选择或处置授权

<!-- source-paragraph:V83-P0693 style=ListPara -->
● 方法门：E1；E4；EVIDENCE

<!-- source-paragraph:V83-P0694 style=BodyCJK -->
推导时先用 D0 冻结候选对象而不预设其有效，再读取同一 G1-instance 相对复杂度匹配 N0 的样本外增益，最后结合边界扰动与独立复核登记支持强度和适用窗。

<!-- source-paragraph:V83-P0695 style=SecH3 -->
### 4.11.2　C2 承载与通道约束

<!-- source-paragraph:V83-P0696 style=ListPara -->
● 推理依赖：D0；G2

<!-- source-paragraph:V83-P0697 style=ListPara -->
● 附加条件：使用已预注册且取得当前实例支持的G2-instance；讨论转移时，源量与目标量必须是同一类型或给出明确类型转换；量的单位、恒等判据、时间窗、核算边界及转换映射或会计规则已冻结；容量、时延、可靠性、可控性与损耗逐通道逐维登记，未测维度保持未知

<!-- source-paragraph:V83-P0698 style=ListPara -->
● 允许结论：可以登记指定状态转移的候选因果承载，以及已测类型、单位、窗口和维度内的通道限制；满足同型量与映射条件时才可追踪转移。

<!-- source-paragraph:V83-P0699 style=ListPara -->
● 禁止跳跃：把不同类型或不可换算量合并为统一成本；把一个已测有限维度推广到全部维度或全部通道；把载体或通道自动认定为责任主体或成本承担者；从资源占用推导跨领域守恒

<!-- source-paragraph:V83-P0700 style=ListPara -->
● 方法门：E1；E4；CAUSAL；EVIDENCE

<!-- source-paragraph:V83-P0701 style=BodyCJK -->
推导只对指定通道、目标转移和已测维度成立。同型量可用单位恒等追踪；异型量必须经过明确转换或会计映射。未测维度与边界外量保持未知，而不是被写成守恒、消失或成本已经转移。

<!-- source-paragraph:V83-P0702 style=SecH3 -->
### 4.11.3　C3 有效反馈与反馈介导学习

<!-- source-paragraph:V83-P0703 style=ListPara -->
● 推理依赖：D2；G2

<!-- source-paragraph:V83-P0704 style=ListPara -->
● 附加条件：反馈分支须有返回通道、时间顺序、被改变字段及无返回或阻断反事实；有效反馈只要求改变至少一个后续状态、概率或约束，不要求持久历史留痕；学习分支另需G3-instance、可保留更新、重复轮次和预定任务比较

<!-- source-paragraph:V83-P0705 style=ListPara -->
● 允许结论：基础分支可登记有效反馈及其时滞和作用字段；另有G3-instance、可保留更新和重复轮次时，才可登记反馈介导学习候选。

<!-- source-paragraph:V83-P0706 style=ListPara -->
● 禁止跳跃：反馈入口或接收证明等于有效反馈；一次状态更新等于学习、修复或正向改进；反馈或学习事实直接推出价值方向或行动授权

<!-- source-paragraph:V83-P0707 style=ListPara -->
● 方法门：E4；CAUSAL；EVIDENCE

<!-- source-paragraph:V83-P0708 style=BodyCJK -->
基础分支以 G2-instance 识别返回通道的候选因果承载，再按 D2 比较有返回与无返回或阻断条件。学习是附加分支：只有再加入 G3、可保留更新、重复轮次和预定任务的样本外比较，才可从有效反馈升级为反馈介导学习候选。

<!-- source-paragraph:V83-P0709 style=BodyCJK -->
分支登记为 C3-feedback（返回通道、后续状态或转移改变、阻断反事实）与 C3-learning（另加 G3，并有可保留更新、重复轮次、预定任务外样本比较）。

## V83-T008

<table data-source-table="V83-T008">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P0710">
<!-- source-paragraph:V83-P0710 style=TableHead -->
<pre>推论</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P0711">
<!-- source-paragraph:V83-P0711 style=TableHead -->
<pre>最低证据</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P0712">
<!-- source-paragraph:V83-P0712 style=TableHead -->
<pre>关键反例</pre>
</td>
<td data-source-cell="1,4" data-paragraphs="V83-P0713">
<!-- source-paragraph:V83-P0713 style=TableHead -->
<pre>失效边界</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P0714">
<!-- source-paragraph:V83-P0714 style=TableText -->
<pre>C1</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P0715">
<!-- source-paragraph:V83-P0715 style=TableText -->
<pre>完整 D0；通过预注册门的 G1-instance；样本外增益、边界扰动与独立复核</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P0716">
<!-- source-paragraph:V83-P0716 style=TableText -->
<pre>增益在独立块消失；边界轻扰即失效；N0 吸收全部增益</pre>
</td>
<td data-source-cell="2,4" data-paragraphs="V83-P0717">
<!-- source-paragraph:V83-P0717 style=TableText -->
<pre>G1 未通过或超出 SP/T/K 时退回候选分组</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P0718">
<!-- source-paragraph:V83-P0718 style=TableText -->
<pre>C2</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P0719">
<!-- source-paragraph:V83-P0719 style=TableText -->
<pre>通过门槛的 G2；量类型、单位、恒等或转换映射；逐通道逐维测量；核算边界与窗口</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P0720">
<!-- source-paragraph:V83-P0720 style=TableText -->
<pre>冗余通道完整替代；异型量无映射；共同输入解释差异</pre>
</td>
<td data-source-cell="3,4" data-paragraphs="V83-P0721">
<!-- source-paragraph:V83-P0721 style=TableText -->
<pre>通道、同型量、单位恒等或转换映射不足时，只描述输入、占用、损耗或候选限制</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P0722">
<!-- source-paragraph:V83-P0722 style=TableText -->
<pre>C3</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P0723">
<!-- source-paragraph:V83-P0723 style=TableText -->
<pre>返回通道、时序、阻断反事实与被改变字段；学习分支另有 G3、保留载体、重复轮次和预定任务结果</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P0724">
<!-- source-paragraph:V83-P0724 style=TableText -->
<pre>信号到达但转移不变；更新未保留；共同输入或代理指标解释差异</pre>
</td>
<td data-source-cell="4,4" data-paragraphs="V83-P0725">
<!-- source-paragraph:V83-P0725 style=TableText -->
<pre>无返回或后续改变时只称信号到达；缺学习条件时止于有效反馈</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P0726 style=SecH2 -->
## 4.12　第二组：历史、负荷、尺度与溢出

<!-- source-paragraph:V83-P0727 style=SecH3 -->
### 4.12.1　C4 历史增量与路径差异

<!-- source-paragraph:V83-P0728 style=ListPara -->
● 推理依赖：D1；G3

<!-- source-paragraph:V83-P0729 style=ListPara -->
● 附加条件：历史变量在未来结果前定义，当前注册状态、环境与测量协议已控制；预测性与因果路径依赖子型不得混同；讨论修复窗口时另需预先公开的K或F及不同时点介入比较

<!-- source-paragraph:V83-P0730 style=ListPara -->
● 允许结论：可以在预注册窗口内登记预测性或因果性路径差异；另有K*/F*和时点比较时可登记条件性修复窗口。

<!-- source-paragraph:V83-P0731 style=ListPara -->
● 禁止跳跃：痕迹保存等于历史效应；预测增益等于因果或不可逆；路径差异等于命运、进步、衰退、责任或阶段回退；K*/F*未公开即宣称修复

<!-- source-paragraph:V83-P0732 style=ListPara -->
● 方法门：E1；E4；CAUSAL；EVIDENCE

<!-- source-paragraph:V83-P0733 style=BodyCJK -->
演化先按 D1 分类，不能从定义推出路径。预测性路径差异读取 G3a 的条件增量；因果路径差异另需 G3b 的历史擦除、恢复或等价干预。修复窗口又是更窄的分支，必须比较不同介入时点对预先公开 K*/F* 的可达性和代价。

<!-- source-paragraph:V83-P0734 style=SecH3 -->
### 4.12.2　C5 负荷、容量与恢复

<!-- source-paragraph:V83-P0735 style=ListPara -->
● 推理依赖：D0；G2

<!-- source-paragraph:V83-P0736 style=ListPara -->
● 附加条件：瞬时分支须有同型需求—容量定义、单位或转换映射、同窗测量和分布位置；瞬时过载不要求G3；累积损伤或迟恢复分支另需G3-instance和可定位历史载体

<!-- source-paragraph:V83-P0737 style=ListPara -->
● 允许结论：基础分支可登记指定窗口和位置上的瞬时负荷—容量缺口；另有G3-instance时可登记累积损伤或迟恢复候选。

<!-- source-paragraph:V83-P0738 style=ListPara -->
● 禁止跳跃：负荷必然单调累积或过载必然崩溃；把不同类型需求和容量直接相减；瞬时缺口自动证明持久损伤；恢复需要直接生成具名主体的牺牲义务

<!-- source-paragraph:V83-P0739 style=ListPara -->
● 方法门：E1；E4；CAUSAL；EVIDENCE

<!-- source-paragraph:V83-P0740 style=BodyCJK -->
基础分支冻结需求、容量、补给、损耗和时间窗的类型与单位，以 G2-instance 确认承载通道，再比较同窗即时缺口与溢出位置。只有累积损伤或迟恢复分支才追加 G3，检验历史项是否改变后续容量或恢复。

<!-- source-paragraph:V83-P0741 style=BodyCJK -->
分支登记为 C5-instant（同型需求—容量映射、同窗测量）与 C5-cumulative（另加 G3，并有历史载体、后续容量或恢复差异）。

<!-- source-paragraph:V83-P0742 style=SecH3 -->
### 4.12.3　C6 尺度闭合与对象转换

<!-- source-paragraph:V83-P0743 style=ListPara -->
● 推理依赖：D3；G4

<!-- source-paragraph:V83-P0744 style=ListPara -->
● 附加条件：结果前唯一预选G4a或G4b，并从该子型allowed_success_criteria中唯一冻结selected_success_criterion；M(SP0→SP1)、保留项、改变项、丢失项、误差、比较模型、正向阈值和容差已冻结；若要登记限定单尺度闭合或未发现预选转换，null_decision_rule中的等价性或充分性检验、功效或灵敏度门及容差必须结果前冻结并实际通过

<!-- source-paragraph:V83-P0745 style=ListPara -->
● 允许结论：可以分别登记G4a在预注册变量、指标、尺度与窗口内的单尺度闭合失败，或G4b在预注册映射、K、尺度与窗口内的对象/干预转换；正向判据未通过默认只登记未获支持或未决。只有预注册等价性或充分性检验及功效、灵敏度与容差门通过，才可对G4a登记判据限定闭合，或对G4b登记未发现预选转换；不得外推至未选判据。

<!-- source-paragraph:V83-P0746 style=ListPara -->
● 禁止跳跃：用一般相关、无条件耦合或同尺度遗漏支持G4；把G4a和G4b事后并取；在同一子型内事后改换成功判据或用未选判据救援；把未显著或未过正向阈值直接称为单尺度闭合、对象未转换或干预等价；尺度范围扩大即解释更真或授权更大；同名术语证明对象或干预同一

<!-- source-paragraph:V83-P0747 style=ListPara -->
● 方法门：E4；E5；EVIDENCE

<!-- source-paragraph:V83-P0748 style=BodyCJK -->
G4a 单独检验被排除尺度变量的条件增量；G4b 只检验其预选的对象动力非交换、干预非交换、预冻结 K 失效、有效关系改变或干预响应改变之一。C6 所引用的 G4-instance 必须已在结果前同时冻结一个子型和一个成功判据；子型之间或子型内部都不能在结果后互换。

<!-- source-paragraph:V83-P0749 style=SecH3 -->
### 4.12.4　C7 局部改善与跨边界溢出

<!-- source-paragraph:V83-P0750 style=ListPara -->
● 推理依赖：G2；G4

<!-- source-paragraph:V83-P0751 style=ListPara -->
● 附加条件：局部目标、对象边界、源目标SP、影响窗口和边界外变量已预注册；G2-instance定位跨边界通道，G4-instance确认跨尺度闭合失败或对象/干预转换；局部改变与边界外结果之间具有时间顺序、机制桥和阻断或替代反事实；只有制度或会计规则已定义成本归属时才使用“外部性”

<!-- source-paragraph:V83-P0752 style=ListPara -->
● 允许结论：可以在机制桥与反事实成立时登记局部改善伴随的跨边界溢出及分布位置；只有另有制度或会计定义时才称外部性。

<!-- source-paragraph:V83-P0753 style=ListPara -->
● 禁止跳跃：任何局部改善都必然伤害更大尺度；把跨边界相关直接称为溢出机制；没有制度或会计定义仍称外部性；发现溢出自动指定补偿、责任或处置方案

<!-- source-paragraph:V83-P0754 style=ListPara -->
● 方法门：E4；E5；CAUSAL；EVIDENCE

<!-- source-paragraph:V83-P0755 style=BodyCJK -->
推导先测量局部目标的预定改善，再沿 G2 指定通道追踪跨边界输出、风险、资源占用或信号，并以 G4/D3 检查目标尺度的闭合与对象转换。只有阻断或替代反事实区分了共同冲击，才可称跨边界溢出；只有制度或会计定义明确成本归属，才进一步分类为外部性。

## V83-T009

<table data-source-table="V83-T009">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P0756">
<!-- source-paragraph:V83-P0756 style=TableHead -->
<pre>推论</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P0757">
<!-- source-paragraph:V83-P0757 style=TableHead -->
<pre>最低证据</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P0758">
<!-- source-paragraph:V83-P0758 style=TableHead -->
<pre>关键反例</pre>
</td>
<td data-source-cell="1,4" data-paragraphs="V83-P0759">
<!-- source-paragraph:V83-P0759 style=TableHead -->
<pre>失效边界</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P0760">
<!-- source-paragraph:V83-P0760 style=TableText -->
<pre>C4</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P0761">
<!-- source-paragraph:V83-P0761 style=TableText -->
<pre>G3-instance；当前状态、环境与测量协议控制；因果分支的擦除/恢复干预；修复分支的 K*/F* 与时点比较</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P0762">
<!-- source-paragraph:V83-P0762 style=TableText -->
<pre>当前状态已充分；历史变量只是遗漏状态代理；干预历史项无效；介入时点无稳定差异</pre>
</td>
<td data-source-cell="2,4" data-paragraphs="V83-P0763">
<!-- source-paragraph:V83-P0763 style=TableText -->
<pre>无增量只保留演化记录；无因果证据只称预测性路径；无 K*/F* 与时点比较不称修复窗口</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P0764">
<!-- source-paragraph:V83-P0764 style=TableText -->
<pre>C5</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P0765">
<!-- source-paragraph:V83-P0765 style=TableText -->
<pre>G2-instance；同型需求—容量或转换映射；同窗逐位置测量与减载/补给比较；累积分支另有 G3</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P0766">
<!-- source-paragraph:V83-P0766 style=TableText -->
<pre>容量同步扩展；需求容量不可比；缺口解除后无后续差异</pre>
</td>
<td data-source-cell="3,4" data-paragraphs="V83-P0767">
<!-- source-paragraph:V83-P0767 style=TableText -->
<pre>类型、单位、窗口或通道不足时只称资源紧张；无 G3 不称累积损伤或迟恢复</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P0768">
<!-- source-paragraph:V83-P0768 style=TableText -->
<pre>C6</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P0769">
<!-- source-paragraph:V83-P0769 style=TableText -->
<pre>完整 D3/E5；唯一 G4 子型与成功判据实例；按预选判据取得正向结果；竞争解释与外样本复核；若输出零结论，另有等价性或充分性、功效或灵敏度及容差通过记录</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P0770">
<!-- source-paragraph:V83-P0770 style=TableText -->
<pre>保留变量构成充分统计量；增益来自同尺度遗漏或复杂度；M 与动力/干预交换且映射稳定；样本或测量灵敏度不足导致正向门未过但也不能支持零</pre>
</td>
<td data-source-cell="4,4" data-paragraphs="V83-P0771">
<!-- source-paragraph:V83-P0771 style=TableText -->
<pre>合同不全、子型或判据未预选、未选判据被用于救援或结果不复现时退回源尺度；正向门未过且零结论规则未通过时保持未决</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V83-P0772">
<!-- source-paragraph:V83-P0772 style=TableText -->
<pre>C7</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V83-P0773">
<!-- source-paragraph:V83-P0773 style=TableText -->
<pre>局部与边界外变量的预注册测量；G2/G4 实例；跨界机制、时序和反事实；使用外部性时另有制度/会计定义</pre>
</td>
<td data-source-cell="5,3" data-paragraphs="V83-P0774">
<!-- source-paragraph:V83-P0774 style=TableText -->
<pre>扩边后两侧同时改善；阻断通道无效；共同冲击充分解释</pre>
</td>
<td data-source-cell="5,4" data-paragraphs="V83-P0775">
<!-- source-paragraph:V83-P0775 style=TableText -->
<pre>无跨界因果只登记核算缺口或相关；无制度/会计定义不得称外部性</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P0776 style=SecH2 -->
## 4.13　第三组：演化模式、观测、人类承接与制度写回

<!-- source-paragraph:V83-P0777 style=SecH3 -->
### 4.13.1　C8 变异—差异保留—再生产

<!-- source-paragraph:V83-P0778 style=ListPara -->
● 推理依赖：D1

<!-- source-paragraph:V83-P0779 style=ListPara -->
● 附加条件：V：在结果前定义可区分变异及其来源；D：在可比环境中出现超过阈值的差异结果；R：差异进入下一轮并在重复轮次中可复核；漂变、共同外因、抽样偏差和一次性冲击作为竞争解释；主张具体承载机制时另需G2-instance

<!-- source-paragraph:V83-P0780 style=ListPara -->
● 允许结论：V、D、R、下一轮进入、重复轮次和漂变竞争均成立时，可以登记限定环境内的变异—差异保留—再生产模式；另有G2-instance时才登记具体承载机制。

<!-- source-paragraph:V83-P0781 style=ListPara -->
● 禁止跳跃：任何演化都由筛选解释；一次存续或一次样本差异等于差异保留；被保留者更优、更高级或更正当；系统筛选等于主体选择、集体治理或授权

<!-- source-paragraph:V83-P0782 style=ListPara -->
● 方法门：E4；CAUSAL；EVIDENCE

<!-- source-paragraph:V83-P0783 style=BodyCJK -->
C8 是独立的操作化推论，不能由定义或框架叙述直接证明。基础模式分支要求 V、D、R、进入下一轮、重复轮次和漂变竞争同时成立；具体机制分支另加 G2-instance，定位保留或再生产通道。它描述系统筛选，不描述行动主体的有意选择，更不描述治理授权。

<!-- source-paragraph:V83-P0784 style=BodyCJK -->
分支登记为 C8-pattern（V、D、R、下一轮、重复轮次、漂变竞争）与 C8-mechanism（另加 G2，并有指定保留或再生产通道、通道扰动或自然变异）。

<!-- source-paragraph:V83-P0785 style=SecH3 -->
### 4.13.2　C9 观测通道与反身响应

<!-- source-paragraph:V83-P0786 style=ListPara -->
● 推理依赖：G2

<!-- source-paragraph:V83-P0787 style=ListPara -->
● 附加条件：观察、命名、评分或发布经实际指定通道到达对象；对象响应具有时间顺序及未观测、不同观测或通道阻断反事实；持久反身性分支另需G3-instance

<!-- source-paragraph:V83-P0788 style=ListPara -->
● 允许结论：可以登记限定通道和窗口内的观测参与或反身响应；另有G3-instance时可登记持久反身性。

<!-- source-paragraph:V83-P0789 style=ListPara -->
● 禁止跳跃：所有观察都会改变对象；观测后反应等于对象原本本质；反身性自动授权隐藏、压制观察或处置对象

<!-- source-paragraph:V83-P0790 style=ListPara -->
● 方法门：E2；E3；E4；CAUSAL；EVIDENCE

<!-- source-paragraph:V83-P0791 style=BodyCJK -->
推导先冻结观察位置、测量协议与原有盲区，再以 G2-instance 识别观测事件的指定传播通道，并用未观测、替代观测或通道阻断条件建立反事实。一次反应止于反身响应；只有 G3 显示跨窗口历史增量时，才进入持久反身性分支。

<!-- source-paragraph:V83-P0792 style=BodyCJK -->
分支登记为 C9-response（实际通道、反事实）与 C9-persistent（另加 G3，并有历史条件增量、跨窗口复核）。

<!-- source-paragraph:V83-P0793 style=SecH3 -->
### 4.13.3　C10 人类承接与跨期再生产

<!-- source-paragraph:V83-P0794 style=ListPara -->
● 推理依赖：G2

<!-- source-paragraph:V83-P0795 style=ListPara -->
● 附加条件：对象属于有人类行动、照护、维护或制度执行的结构；H2分别登记承接载体、同型成本承担者、受益者、停止权和责任主体；跨期再生产分支另需G3-instance；历史沉积主张另需H5领域特化及其实例证据

<!-- source-paragraph:V83-P0796 style=ListPara -->
● 允许结论：基础分支可登记人类承接链及当前分布；另有G3时可登记跨期再生产候选，另有H5实例时可限定历史载体。

<!-- source-paragraph:V83-P0797 style=ListPara -->
● 禁止跳跃：承接能力等于承接义务；最可见执行者等于责任主体；H2分类本身证明再生产机制；承接链存在直接授权特定主体牺牲、继续或退出

<!-- source-paragraph:V83-P0798 style=ListPara -->
● 方法门：H2；E4；CAUSAL；EVIDENCE

<!-- source-paragraph:V83-P0799 style=BodyCJK -->
C10 特化到有人类行动、照护、维护或制度执行的结构。当前承接分支用 G2 定位指定通道，并依 H2 分开承接载体、同型成本承担者、受益者、停止权与责任主体；跨期再生产另加 G3，历史载体归因再加 H5 的实例证据。H2 是操作门，不是经验原因。

<!-- source-paragraph:V83-P0800 style=BodyCJK -->
分支登记为 C10-current（H2分型、G2指定通道）、C10-intertemporal（另加 G3，并有跨期历史增量）与 C10-historical-carrier（另加 G3、H5，并有人类历史载体实例）。

<!-- source-paragraph:V83-P0801 style=SecH3 -->
### 4.13.4　C11 制度写回

<!-- source-paragraph:V83-P0802 style=ListPara -->
● 推理依赖：D2；G2

<!-- source-paragraph:V83-P0803 style=ListPara -->
● 附加条件：对象具有记录、规则、资源、角色、责任、记忆或停止条件等制度字段；H3作为分类门，要求反馈导致字段变化且实际执行；分别记录受理、字段变化、执行和持续时间

<!-- source-paragraph:V83-P0804 style=ListPara -->
● 允许结论：可以区分制度中的受理、字段变化、实际执行、有效写回及其持续时间。

<!-- source-paragraph:V83-P0805 style=ListPara -->
● 禁止跳跃：有申诉或审计入口等于有效写回；一次写回等于长期修复或正向改善；制度写回事实证明制度正当或授权扩大

<!-- source-paragraph:V83-P0806 style=ListPara -->
● 方法门：H3；E4；CAUSAL；EVIDENCE

<!-- source-paragraph:V83-P0807 style=BodyCJK -->
C11 用 G2 定位制度返回通道，以 D2 比较有返回与无返回或阻断条件，再用 H3 区分受理、字段变化和实际执行。持续时间是写回合同的一部分，但一次写回不称学习；学习还需要可保留更新、重复轮次与 G3。

## V83-T010

<table data-source-table="V83-T010">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P0808">
<!-- source-paragraph:V83-P0808 style=TableHead -->
<pre>推论</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P0809">
<!-- source-paragraph:V83-P0809 style=TableHead -->
<pre>最低证据</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P0810">
<!-- source-paragraph:V83-P0810 style=TableHead -->
<pre>关键反例</pre>
</td>
<td data-source-cell="1,4" data-paragraphs="V83-P0811">
<!-- source-paragraph:V83-P0811 style=TableHead -->
<pre>失效边界</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P0812">
<!-- source-paragraph:V83-P0812 style=TableText -->
<pre>C8</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P0813">
<!-- source-paragraph:V83-P0813 style=TableText -->
<pre>V 来源；可比环境中的 D；R 通道、下一轮与重复轮次；漂变/共同外因竞争；机制分支另有 G2</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P0814">
<!-- source-paragraph:V83-P0814 style=TableText -->
<pre>共同输入同步产生；差异不进下一轮；漂变充分；扰动再生产通道无效</pre>
</td>
<td data-source-cell="2,4" data-paragraphs="V83-P0815">
<!-- source-paragraph:V83-P0815 style=TableText -->
<pre>V/D/R/下一轮/重复轮次缺一，只登记变化或一次差异；无 G2 不称具体机制</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P0816">
<!-- source-paragraph:V83-P0816 style=TableText -->
<pre>C9</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P0817">
<!-- source-paragraph:V83-P0817 style=TableText -->
<pre>观察位置、传播通道、G2-instance、时序与未观测/替代/阻断反事实；持久分支另有 G3</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P0818">
<!-- source-paragraph:V83-P0818 style=TableText -->
<pre>阻断通道后不变；变化早于观测；不同观测条件无差异</pre>
</td>
<td data-source-cell="3,4" data-paragraphs="V83-P0819">
<!-- source-paragraph:V83-P0819 style=TableText -->
<pre>无通道或反事实不登记观测参与；无 G3 不称持久反身性</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P0820">
<!-- source-paragraph:V83-P0820 style=TableText -->
<pre>C10</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P0821">
<!-- source-paragraph:V83-P0821 style=TableText -->
<pre>G2-instance；H2 分型和同型成本映射；补给/轮换/减载/退出/替代比较；跨期另有 G3，历史归因另有 H5</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P0822">
<!-- source-paragraph:V83-P0822 style=TableText -->
<pre>替代通道无历史依赖地接续；当前状态吸收跨期差异；角色和责任透明重合</pre>
</td>
<td data-source-cell="4,4" data-paragraphs="V83-P0823">
<!-- source-paragraph:V83-P0823 style=TableText -->
<pre>H2 字段不能分离只登记资料缺口；无 G3 不称跨期再生产；无 H5 不归因特定历史载体</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V83-P0824">
<!-- source-paragraph:V83-P0824 style=TableText -->
<pre>C11</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V83-P0825">
<!-- source-paragraph:V83-P0825 style=TableText -->
<pre>G2-instance；制度返回通道与阻断反事实；字段前后变化和实际执行；持续时间</pre>
</td>
<td data-source-cell="5,3" data-paragraphs="V83-P0826">
<!-- source-paragraph:V83-P0826 style=TableText -->
<pre>只有回执或表态；字段变化未执行；独立命令解释变化</pre>
</td>
<td data-source-cell="5,4" data-paragraphs="V83-P0827">
<!-- source-paragraph:V83-P0827 style=TableText -->
<pre>无字段变化只称受理；无执行只称记录更新；不得从一次写回外推跨期机制</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P0828 style=SecH2 -->
## 4.14　第四组：规范桥接门

<!-- source-paragraph:V83-P0829 style=SecH3 -->
### 4.14.1　C12 规范桥接有效性门

<!-- source-paragraph:V83-P0830 style=ListPara -->
● 推理依赖：N1；O1；O2；O3；O4

<!-- source-paragraph:V83-P0831 style=ListPara -->
● 附加条件：O1已冻结可审计描述、证据状态和描述性行动上限；O2在运行时登记explicit_normative_premise_ids、正向目标或约束属性、冲突与异议；O3登记授权主体、来源、管辖、期限、J轴、候选方案和不行动方案；O4登记受限执行、监测、停止、申诉、复核、回滚、补救、到期失效和再授权；保护底板完成逐项检查；N1单独只能阻止越权，不能产生正向方案

<!-- source-paragraph:V83-P0832 style=ListPara -->
● 允许结论：只有可审计描述、运行时显式N前提、保护底板、J轴授权及O1-O4全部通过时，才可形成可进入现实采用的受限建议；形成供审议的分析推荐须明示规范前提、证据和代价，但不要求尚未发生的现实执行已获授权；若只有N1或缺少正向N，只能输出不行动、补证或继续审议。

<!-- source-paragraph:V83-P0833 style=ListPara -->
● 禁止跳跃：从稳定、效率、存续、相干、路径或筛选事实直接推出应当；把专家解释、模型置信度、广泛影响或法律有效单独当作规范正当；从G1-G4、C1-C11或S0-S6推出爱、责任、牺牲要求或处置权；用未显式引用的规范原则填补方案目标

<!-- source-paragraph:V83-P0834 style=ListPara -->
● 方法门：EVIDENCE；PF-1；PF-2；PF-3；PF-4；PF-5；PF-6；PF-7；PF-8；PF-9；PF-10

<!-- source-paragraph:V83-P0835 style=BodyCJK -->
C12 不是经验推论，而是描述进入现实选择之前的程序有效性门。它要求十项桥接组件完整出现：descriptive_or_explanatory_claim_ids、current_evidence_and_epistemic_constraints、explicit_normative_premise_ids、normative_conflict_record、protection_floor_status、authorization_and_jurisdiction_record、options_including_no_action、operational_procedure_records、action_ceiling、stop_review_rollback_and_remedy。N1 是否定性越权门，单独不能生产正向方案。

## V83-T011

<table data-source-table="V83-T011">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P0836">
<!-- source-paragraph:V83-P0836 style=TableHead -->
<pre>最低证据</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P0837">
<!-- source-paragraph:V83-P0837 style=TableHead -->
<pre>关键反例</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P0838">
<!-- source-paragraph:V83-P0838 style=TableHead -->
<pre>失效边界</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P0839">
<!-- source-paragraph:V83-P0839 style=TableText -->
<pre>O1 描述冻结与证据审计；O2 显式 N 前提与冲突；O3 授权和方案比较；O4 受限执行与纠错；保护底板与 J 轴</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P0840">
<!-- source-paragraph:V83-P0840 style=TableText -->
<pre>相同事实因不同 N 产生不同选择；只有 N1 而无正向目标；授权不覆盖行动；停止、纠错或回滚不可达</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P0841">
<!-- source-paragraph:V83-P0841 style=TableText -->
<pre>任一显式 N、保护底板、J 轴授权或 O1—O4 记录缺失，都不得进入现实处置；只有 N1 时保持否定性越权门</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P0842 style=SecH2 -->
## 4.15　组合推论树

<!-- source-paragraph:V83-P0843 style=BodyCJK -->
根实例与附加条件的关系可以压缩为下列条件树：

<!-- source-paragraph:V83-P0844 style=CodeBlock -->
G1-instance + 对象/变量桥 + G2-instance
  └─ 指定组织依赖的通道候选
      ├─ + 返回通道与阻断反事实
      │    └─ 有效反馈
      │         └─ + G3-instance + 可保留更新 + 重复轮次
      │              └─ 反馈介导学习候选
      └─ + G4a/G4b + D3/E5 映射
           └─ 闭合失败或对象/干预转换候选

G2-instance + 同型需求/容量映射
  └─ 瞬时过载候选
       └─ + G3-instance + 历史载体
            └─ 累积损伤或迟恢复候选

D1 + V + D + R + 下一轮 + 重复轮次 + 漂变竞争
  └─ 变异—差异保留—再生产模式
       ├─ + G2-instance → 指定保留/再生产机制
       └─ + G3-instance → 跨轮历史路径候选

<!-- source-paragraph:V83-P0845 style=BodyCJK -->
任何根组合都不构成充分条件；附加条件、方法门、桥接证据或适用边界缺失时，只生成检查问题。“根模板并列不构成充分条件”是每条 C 合同的共同约束，而不是可被经验结果取消的措辞。即使 G1—G4 的某组实例全部通过，也不推出 S0—S6 阶段、方向、价值、责任、选择或授权；这些结论分别需要自己的分类、规范和程序合同。

<!-- source-paragraph:V83-P0846 style=SecH2 -->
## 4.16　根层输出的停止位置

<!-- source-paragraph:V83-P0847 style=BodyCJK -->
根层的最高输出是受对象、尺度、时间窗、证据和外推单元约束的描述或候选机制。G 模板仍待实例检验，C 是受限推理规则，条件机制还需独立实例证据。定义、编号、示例和内部说明不能回答经验命题是否在世界中成立。因此，根层一旦触及价值、责任、牺牲、选择或处置，就必须停止并把问题交给人类领域分型、规范原则与 O1—O4 程序。

<!-- source-paragraph:V83-P0848 style=SecH2 -->
## 4.17　双文本共同内核与新增方法公理

<!-- source-paragraph:V83-P0849 style=BodyCJK -->
本节只把已经散布在框架中的方法约束汇成共同内核，并新增模拟再入的身份规则。所谓方法公理，是模型构造和记录必须遵守的起点，不是关于世界必然怎样运行的经验定律。

<!-- source-paragraph:V83-P0850 style=SecH3 -->
### 4.17.1　六条共同方法公理

<!-- source-paragraph:V83-P0851 style=BodyCJK -->
法一｜分层表示的任务相对性。分层、粗细尺度和目标变量都绑定对象、任务、观察位置、时间窗与用途；它们不宣布世界本体天然是一张固定层级图。

<!-- source-paragraph:V83-P0852 style=BodyCJK -->
法二｜信息身份不得静默升级。报告不能自动成为观测，观测不能自动成为完整现实，模型信念不能自动成为事实，模拟不能自动成为证据或授权。

<!-- source-paragraph:V83-P0853 style=BodyCJK -->
法三｜非平凡转义不预设无损。跨尺度、跨圈层、跨语境或跨词汇系统的转换必须接受损失审计；但不得反过来断言每次转换必然发生任务相关损失。

<!-- source-paragraph:V83-P0854 style=BodyCJK -->
法四｜目标表示不预设闭合，路径不预设等价。被排除变量是否仍有条件增量、不同转换顺序是否等价或可交换，必须分别检验。

<!-- source-paragraph:V83-P0855 style=BodyCJK -->
法五｜模拟再入不得提升认识地位。模拟状态可以成为下一轮模拟的起点；没有新外部观测、执行回执或独立裁定进入时，递归深度不能提高事实地位、经验支持或能力等级。

<!-- source-paragraph:V83-P0856 style=BodyCJK -->
法六｜事实、前瞻和能力不生成价值、责任与授权。任何现实选择和行动仍须公开规范前提、权利底线、责任主体、程序与授权。

<!-- source-paragraph:V83-P0857 style=SecH3 -->
### 4.17.2　根假设和推论不升级

<!-- source-paragraph:V83-P0858 style=BodyCJK -->
G1 至 G4 继续作为四类可检验根假设的权威合同，分别对应候选分组的条件增益、指定通道效应、历史项条件增量、尺度闭合及对象或干预转换。本版不增加第五根假设。转义保真先由转义合同、通道检验与尺度闭合合同组合判断；只有未来出现不可约化的独立状态机、输入输出、失败语义和成功判据时，才讨论新的根族。

<!-- source-paragraph:V83-P0859 style=BodyCJK -->
C1 至 C12 仍是条件推论，不因进入共同内核而变成普遍事实。世界模型中的实践展开可以作为运行接口和候选实现，却不能替任何根实例通过经验检验；本框架也不能凭形式合同证明世界模型已有经验能力。

<!-- source-paragraph:V83-P0860 style=SecH3 -->
### 4.17.3　可推出的新限制

<!-- source-paragraph:V83-P0861 style=BodyCJK -->
由六条方法公理可以推出：目标尺度上有用的有效变量仍只是绑定任务和适用窗的候选；转义损失不等于现实对象中的物理损失；条件分支变窄不等于证据增加；递归更深不等于前瞻更准；新外部材料到达后必须建立新运行，不能倒灌修补原预测。

<!-- source-paragraph:V83-P0862 style=BodyCJK -->
“每次尺度迁移必然丢失信息”“信息丢失等于熵增”“残差必然来自被压缩变量”“第三阶天然优于第一阶”均不属于本框架结论。它们若在特定领域提出，必须另给对象映射、假设、可观察量、误差与反例。
