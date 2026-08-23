# 第六部分　运转与演化

Source: `v8.2`
Raw SHA256: `670e90e0073eb1a7575a75c4e0a410630ce16bd5a10f2456b83c82480333de3f`
Semantic SHA256: `4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0`
List structure SHA256: `8b4a40f8559ac61c1bb8c224054de7978bb93298efbbd41f40ed065f89bab050`
Paragraph range: `V82-P1083`-`V82-P1159`
Tables: `V82-T017`

<!-- This is a lossless reader edition; anchors are source coordinates. -->

<!-- source-paragraph:V82-P1083 style=PartTitle -->
# 第六部分　运转与演化

<!-- source-paragraph:V82-P1084 style=BodyCJK -->
本部分把对象合同展开为过程解释。运转、反馈、学习、维护、负荷、相位与筛选不是一组可以互换的叙事词，而是具有不同推理前提、使能条件、反事实和停止位置的条件机制。机制名称本身不构成充分条件；只有依赖、条件、最低证据和竞争解释同时通过，才能在指定 SP/T/K 内登记一个机制实例。

<!-- source-paragraph:V82-P1085 style=SecH2 -->
## 6.1　运转登记

<!-- source-paragraph:V82-P1086 style=BodyCJK -->
一次运转至少登记输入、指定载体或通道、状态转移、输出、环境条件、时间窗和可能留痕。若输出返回，还要登记返回通道、接收位置和被改变字段；若主张历史效应，还要比较历史感知模型与当前状态充分模型；若跨尺度，还要完成 D3/E5 映射。这样的登记不是把复杂过程强行压成线性链，而是让每一处时延、损耗、替代通道、证据断点和外推边界可被检验。

<!-- source-paragraph:V82-P1087 style=SecH2 -->
## 6.2　CM-FEEDBACK 有效反馈

<!-- source-paragraph:V82-P1088 style=BodyCJK -->
推理依赖：D2、G2。 E4、CAUSAL 与 EVIDENCE 是方法门，不是额外经验原因。有效反馈不以 G3 为前提。

<!-- source-paragraph:V82-P1089 style=BodyCJK -->
使能条件是：先前状态或输出经已由 G2-instance 识别的指定返回通道进入后续过程；相对于无返回或阻断条件，至少一个后续状态、转移概率或约束发生超过阈值的差异；时间顺序和被改变字段在结果前已登记。机制链为：

<!-- source-paragraph:V82-P1090 style=BodyCJK -->
先前状态或输出 → 返回信号 → 指定通道传导 → 接收位置摄取 → 后续状态、概率或约束改变 → 阻断反事实复核

<!-- source-paragraph:V82-P1091 style=BodyCJK -->
最低证据包括通过预注册门的 G2-instance、返回通道与接收位置、时间顺序、被改变字段、后续差异，以及无返回或通道阻断比较。信号到达但后续转移不变，变化由独立共同输入解释，或切断返回通道后差异仍保持不变时，不登记有效反馈。有效反馈只说明返回造成了一次后续改变；它不等于学习、修复、正向结果，也不要求持久历史留痕。

<!-- source-paragraph:V82-P1092 style=SecH2 -->
## 6.3　CM-LEARNING 反馈介导学习

<!-- source-paragraph:V82-P1093 style=BodyCJK -->
推理依赖：CM-FEEDBACK、G3。 E4、CAUSAL 与 EVIDENCE 是方法门。学习不是反馈的同义词，而是反馈经过可保留更新并在重复轮次中产生历史条件增量的更窄机制。

<!-- source-paragraph:V82-P1094 style=BodyCJK -->
使能条件是：有效反馈改变可定位的内部状态、参数、规则、记忆或结构；更新经明确载体持久保留，并在重复或多轮后续处理中继续参与；G3-instance 证明该历史项在控制当前注册状态后仍提供条件增量；相对于预注册基线或替代模型，预定任务的样本外结果出现可复核改变。机制链为：

<!-- source-paragraph:V82-P1095 style=BodyCJK -->
有效反馈 → 内部更新 → 更新载体持久保留 → 进入重复后续轮次 → 历史条件增量 → 预定任务结果改变

<!-- source-paragraph:V82-P1096 style=BodyCJK -->
一次参数变化、一次成功、一次写回或材料被归档都不足以证明学习。更新未保留、不进入后续轮次，结果只在一个样本出现，当前完整状态吸收全部历史增量，或变化只改善代理指标而不改变预定任务时，学习解释失效。即使学习成立，也不表示变得更好、拥有目标或获得行动授权。

<!-- source-paragraph:V82-P1097 style=SecH2 -->
## 6.4　反馈、制度写回与学习的虚拟申诉例

<!-- source-paragraph:V82-P1098 style=BodyCJK -->
设一个虚拟制度收到申诉。本例只展示分类方法，不引用现实材料，也不构成外部经验证明。

<!-- source-paragraph:V82-P1099 style=ListPara -->
1. 申诉被收件并生成回执，但记录、规则、资源、角色、责任、记忆和停止条件均未改变：这是信号到达，不是有效反馈，也不是制度写回。

<!-- source-paragraph:V82-P1100 style=ListPara -->
2. 申诉经指定通道使案件状态字段改变，但改变没有进入执行：这可以是 D2 意义上的有效反馈，却仍不是 H3 意义上的完整制度写回。

<!-- source-paragraph:V82-P1101 style=ListPara -->
3. 字段变化进入实际执行，并记录受理、字段变化、执行和持续时间：这是一次制度写回。写回事实不证明制度正当，也不等于长期修复。

<!-- source-paragraph:V82-P1102 style=ListPara -->
4. 只有当该写回形成可保留规则或状态更新，进入后续多轮相似案件，且 G3-instance 显示历史项在控制当前状态后仍对预定任务提供样本外增量时，才可提出反馈介导学习候选。

<!-- source-paragraph:V82-P1103 style=BodyCJK -->
因此，反馈不等于学习，写回也不等于学习。三者的证据门逐级增加，不能因制度拥有申诉入口或公开回应就一次性跨越。

<!-- source-paragraph:V82-P1104 style=SecH2 -->
## 6.5　CM-MAINTENANCE 维护与存护—消解

<!-- source-paragraph:V82-P1105 style=BodyCJK -->
基础推理依赖：D0、G2。 E4、CAUSAL 与 EVIDENCE 是方法门，D1 提供状态词特化。维护要求预先声明当前 K 或功能判据 F 与维护窗口；补给、替换、校正或清除必须经 G2-instance 识别为改变 K/F 保持的指定通道；还要比较维护、减维护、错配维护与停止维护条件。

<!-- source-paragraph:V82-P1106 style=BodyCJK -->
机制链为：

<!-- source-paragraph:V82-P1107 style=BodyCJK -->
磨损、漂移、损耗或组件退出 → 指定维护通道 → 补给/替换/校正/清除 → K/F 保持时间或失效概率改变

<!-- source-paragraph:V82-P1108 style=BodyCJK -->
CM-MAINTENANCE-current 是即时分支，条件为“维护输入即时改变K/F保持”，不要求 G3。CM-MAINTENANCE-cumulative 是累积分支，条件为“磨损历史项提供条件增量、累积或迟恢复”，才追加 G3。对象在目标窗口内无需持续维护仍保持 K/F、维护输入变化不改变 K/F，或所谓磨损由独立冲击解释时，撤回维护机制。对象 K 已改变却继续沿用旧维护判据，也属于合同失效。

<!-- source-paragraph:V82-P1109 style=BodyCJK -->
维护需要不等于对象应永久存续，维护通道存在也不能直接指定具名承接者、责任或牺牲义务。错配维护可能延长旧 K 却破坏目标 F；有序停止、对象转换或解体也可能是合同允许的结果。

<!-- source-paragraph:V82-P1110 style=SecH2 -->
## 6.6　CM-LOAD 负荷、容量与恢复

<!-- source-paragraph:V82-P1111 style=BodyCJK -->
基础推理依赖：D0、G2。 E4、CAUSAL 与 EVIDENCE 是方法门。需求与容量必须是同型量，或具有明确单位与转换映射；需求、可用容量、补给和溢出按同一窗口、同一位置测量；G2-instance 只支持已测通道及其相关维度。

<!-- source-paragraph:V82-P1112 style=BodyCJK -->
机制链为：

<!-- source-paragraph:V82-P1113 style=BodyCJK -->
同型需求进入指定通道 → 占用可用容量 → 形成即时缺口或跨边界溢出 → 减载/补给/扩容改变缺口 → 历史条件增量决定是否累积或迟恢复

<!-- source-paragraph:V82-P1114 style=BodyCJK -->
CM-LOAD-instant 是瞬时分支，只要求同型需求—容量和同窗即时缺口，不要求 G3。CM-LOAD-cumulative 是累积分支：只有历史项改变后续容量或恢复，并由 G3-instance 支持时，才登记累积损伤或迟恢复。容量同步扩展可以吸收需求；瞬时缺口解除后可以没有任何持久差异。因此，负荷不必单调累积，瞬时过载不必导致损伤或崩溃。

<!-- source-paragraph:V82-P1115 style=BodyCJK -->
负荷必须按位置与分布登记，不能只报告平均值；容量要区分峰值、持续值、替代通道与补给；恢复要区分表面输出恢复、K/F 恢复和内部余量恢复。不同类型量不能直接相减，恢复需求也不能直接生成任何主体的牺牲义务或授权。

<!-- source-paragraph:V82-P1116 style=SecH2 -->
## 6.7　CM-PHASE 相位与阈值转换

<!-- source-paragraph:V82-P1117 style=BodyCJK -->
基础推理依赖：D0、D1。 E4 与 EVIDENCE 是相位模式分支的共同方法门；CAUSAL 只在因果触发与迟滞分支追加，不是基础模式分类的前置门。相位的基础识别不要求 G3：同一候选对象合同和 K 下，只要预先登记状态变量、候选参数或触发条件、阈值，以及噪声和分箱稳健性，就可以检验至少两个可重复区分的运转区间。

<!-- source-paragraph:V82-P1118 style=BodyCJK -->
机制链分为三层：

<!-- source-paragraph:V82-P1119 style=ListPara -->
● CM-PHASE-pattern：相位模式。 条件为“同一K、两个可复核区间、预定阈值模式”。它只登记区间—阈值关系，不宣称触发因果。

<!-- source-paragraph:V82-P1120 style=ListPara -->
● CM-PHASE-causal-trigger：因果触发。 条件为“指定触发通道、通道干预或可识别自然变异”，并另加 G2-instance 定位触发作用。

<!-- source-paragraph:V82-P1121 style=ListPara -->
● CM-PHASE-hysteretic：迟滞分支。 只有主张迟滞、路径或迟恢复时才追加 G3-instance，检验历史条件增量。

<!-- source-paragraph:V82-P1122 style=BodyCJK -->
连续趋势若在同一状态分布内充分解释变化、阈值随分箱任意移动，或转移前 K 已失效，应撤回相位结论，分别改记为连续变化、测量划分效应或对象转换/解体。可逆相位不必具有历史路径；只有迟滞分支才需要 G3。相位也不构成 S0—S6 的必经成熟序列，新相位不因此更高、更好或拥有更大授权。

<!-- source-paragraph:V82-P1123 style=SecH2 -->
## 6.8　CM-SELECTION 变异—差异保留—再生产

<!-- source-paragraph:V82-P1124 style=BodyCJK -->
基础推理依赖：D1。 E4、CAUSAL 与 EVIDENCE 是方法门。该机制是独立操作化，不由“发生演化”这个定义自动推出，也不能由概念说明或框架叙述直接证明。

<!-- source-paragraph:V82-P1125 style=BodyCJK -->
必须把三种输出分开：

<!-- source-paragraph:V82-P1126 style=ListPara -->
● CM-SELECTION-pattern：筛选模式。 条件为“V、D、R、下一轮、重复轮次、漂变竞争”：结果前定义可区分变异 V 及来源，在可比环境中观察超过阈值的差异结果 D，差异经保留 R 进入下一轮并在重复轮次中可复核，同时检验漂变、共同外因和抽样偏差。基础依赖只有 D1。

<!-- source-paragraph:V82-P1127 style=ListPara -->
● CM-SELECTION-carrier：具体机制。 条件为“指定保留或再生产通道、通道扰动或可识别自然变异”，在模式成立之外另加 G2-instance 定位承载机制。

<!-- source-paragraph:V82-P1128 style=ListPara -->
● CM-SELECTION-history：跨轮路径。 条件为“跨轮历史项条件增量、当前状态控制”，在模式成立之外另加 G3-instance。

<!-- source-paragraph:V82-P1129 style=BodyCJK -->
只有变化而无 D，是变动；有一次差异而无 R、下一轮和重复轮次，是一次结果；漂变模型已经充分时，不登记筛选模式；候选再生产通道被扰动而保留不变时，不登记该具体机制。一次存续不等于差异保留，被保留者不因此更优、更高级或更正当。系统筛选不是行动主体选择，更不是集体治理选择：后两者分别需要主体、选项与决策证据，以及规范前提、J 轴授权和 O 程序。

<!-- source-paragraph:V82-P1130 style=SecH2 -->
## 6.9　共演化的条件

<!-- source-paragraph:V82-P1131 style=BodyCJK -->
当两个候选对象相互改变对方的环境、可行路径、指定通道或保留条件，并且双向作用在各自时间窗内可追踪时，可以提出共演化候选。必须分别登记两个对象的 D0 合同与 K、各自 SP/T、双向 G2 通道、时间顺序、速度差异和第三方共同环境；若主张历史锁定或跨轮路径，再分别追加相应 G3-instance。

<!-- source-paragraph:V82-P1132 style=BodyCJK -->
共同变化、同步波动或长期相关不能替代双向机制。单向依赖、共同冲击和测量协议同步都是必要的竞争解释。共演化也不表示双方对称、互利、价值一致或负有继续维持关系的义务。

<!-- source-paragraph:V82-P1133 style=SecH2 -->
## 6.10　解体、对象转换与修复边界

<!-- source-paragraph:V82-P1134 style=BodyCJK -->
解体以原 K 不再成立为判据。若原 K 失效但另一个对象合同可以成立，应区分对象转换与终止；相位变化只有在原 K 保持时才与解体分开。解体不自动等于失败，存续也不自动等于成功。

<!-- source-paragraph:V82-P1135 style=BodyCJK -->
修复以结果前公开的目标 K* 或 F* 为判据。它可以利用旧痕迹，也可以改变组件、边界、关系、接口、载体和尺度位置；它不是把时间倒回旧状态。若主张存在修复窗口，除了 K*/F*，还需比较不同时点介入对目标可达性与成本的影响；若主张历史限制，则另需 G3。即使这些经验条件成立，目标是否正当、由谁选择、谁负责任以及谁可实施，仍须由 N 层、J 轴和 O1—O4 审查。

<!-- source-paragraph:V82-P1136 style=SecH2 -->
## 6.11　机制输出总闸

<!-- source-paragraph:V82-P1137 style=BodyCJK -->
六个条件机制都必须依次完成对象与尺度声明、推理依赖、使能条件、机制链、最低证据、竞争解释、反例和失效边界。缺项时只保留候选机制或检查问题。反馈不偷带学习，瞬时负荷不偷带累积，基础相位不偷带迟滞，筛选模式不偷带机制或价值，维护和修复也不偷带存续义务。概念说明和教学例只展示合同如何使用，均不构成外部经验支持。

<!-- source-paragraph:V82-P1138 style=SecH2 -->
## 6.12　异步多时钟的运转

<!-- source-paragraph:V82-P1139 style=BodyCJK -->
多圈层联合状态至少包含即时、互动、组织、制度和长期时钟。一个事件可以先改变快变量，随后经重复互动改变关系预期，再经组织决策改变资源，最后才可能进入制度写回。若把这些变化压成同一时间点，会把时延误判为无效，或把短时波动误判为长期演化。

<!-- source-paragraph:V82-P1140 style=BodyCJK -->
每个机制应声明自己的更新时钟和跨时钟桥。反馈信号到达不等于组织规则已经改变，组织决定不等于制度执行，制度文本变化也不等于每个局部位置已实际写回。跨时钟桥必须给出载体、执行、确认和失效条件。

## V82-T017

<table data-source-table="V82-T017">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P1141">
<!-- source-paragraph:V82-P1141 style=TableHead -->
<pre>时钟转换</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P1142">
<!-- source-paragraph:V82-P1142 style=TableHead -->
<pre>最低桥接证据</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V82-P1143">
<!-- source-paragraph:V82-P1143 style=TableHead -->
<pre>常见失败</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P1144">
<!-- source-paragraph:V82-P1144 style=TableText -->
<pre>即时→互动</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P1145">
<!-- source-paragraph:V82-P1145 style=TableText -->
<pre>多个回合中状态差持续并改变对方响应</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V82-P1146">
<!-- source-paragraph:V82-P1146 style=TableText -->
<pre>单次情绪消退</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P1147">
<!-- source-paragraph:V82-P1147 style=TableText -->
<pre>互动→组织</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P1148">
<!-- source-paragraph:V82-P1148 style=TableText -->
<pre>关系或策略变化进入角色、流程、资源或记录</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V82-P1149">
<!-- source-paragraph:V82-P1149 style=TableText -->
<pre>口头共识未执行</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P1150">
<!-- source-paragraph:V82-P1150 style=TableText -->
<pre>组织→制度</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P1151">
<!-- source-paragraph:V82-P1151 style=TableText -->
<pre>合法程序、规则文本、责任与实际执行</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V82-P1152">
<!-- source-paragraph:V82-P1152 style=TableText -->
<pre>发布文件但无写回</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P1153">
<!-- source-paragraph:V82-P1153 style=TableText -->
<pre>制度→长期</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P1154">
<!-- source-paragraph:V82-P1154 style=TableText -->
<pre>持续执行、维护、学习和替代路径</pre>
</td>
<td data-source-cell="5,3" data-paragraphs="V82-P1155">
<!-- source-paragraph:V82-P1155 style=TableText -->
<pre>短期合规后回弹</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P1156 style=SecH2 -->
## 6.13　跨圈层级联与共演化

<!-- source-paragraph:V82-P1157 style=BodyCJK -->
级联发生在一个圈层的局部变化经成员重叠、桥接接口、共享资源、网络传播或制度下行触发其他圈层变化。每一级都要重新检查对象、通道、尺度和证据，不能因为第一步成立就假定后续全部成立。级联可被容量、过滤、延迟、抵消和局部排除区截断。

<!-- source-paragraph:V82-P1158 style=BodyCJK -->
共演化要求至少两个对象在一段时间内相互改变对方的选择环境、转移概率或约束，并保留彼此独立的 K。若一个对象只是被另一个吸收，应记录嵌套或对象转换；若只有共同外部环境造成同步变化，不称共演化；若返回信号没有改变后续状态，只称耦合或共同暴露。

<!-- source-paragraph:V82-P1159 style=BodyCJK -->
多圈层级联和共演化都不带价值方向。更紧密耦合可能提高协同，也可能扩大脆弱性和责任扩散；解耦可能降低效率，也可能保护局部自主与止损。评价与行动仍交由规范层。
