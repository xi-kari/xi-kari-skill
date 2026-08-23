# 附录A　人类变量接口卡册

Source: `v8.2`
Raw SHA256: `670e90e0073eb1a7575a75c4e0a410630ce16bd5a10f2456b83c82480333de3f`
Semantic SHA256: `4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0`
List structure SHA256: `8b4a40f8559ac61c1bb8c224054de7978bb93298efbbd41f40ed065f89bab050`
Paragraph range: `V82-P2906`-`V82-P4477`
Tables: `V82-T064`, `V82-T065`, `V82-T066`, `V82-T067`, `V82-T068`, `V82-T069`, `V82-T070`, `V82-T071`, `V82-T072`, `V82-T073`, `V82-T074`, `V82-T075`, `V82-T076`, `V82-T077`, `V82-T078`, `V82-T079`, `V82-T080`, `V82-T081`, `V82-T082`, `V82-T083`, `V82-T084`, `V82-T085`, `V82-T086`, `V82-T087`, `V82-T088`, `V82-T089`, `V82-T090`, `V82-T091`, `V82-T092`, `V82-T093`, `V82-T094`, `V82-T095`, `V82-T096`, `V82-T097`, `V82-T098`, `V82-T099`, `V82-T100`, `V82-T101`, `V82-T102`, `V82-T103`, `V82-T104`, `V82-T105`, `V82-T106`, `V82-T107`, `V82-T108`, `V82-T109`, `V82-T110`, `V82-T111`, `V82-T112`, `V82-T113`, `V82-T114`, `V82-T115`, `V82-T116`, `V82-T117`, `V82-T118`, `V82-T119`

<!-- This is a lossless reader edition; anchors are source coordinates. -->

<!-- source-paragraph:V82-P2906 style=PartTitle -->
# 附录A　人类变量接口卡册

<!-- source-paragraph:V82-P2907 style=BodyCJK -->
本附录完整收录第七部分十一项人类变量(HV01-HV11)的接口卡。每张卡按 A-E 五区登记:A 身份、命题与适用范围;B 正式依赖与推论边界;C 九轴尺度与对象合同;D 状态、证据与变量流;E 承接、责任、规范、上限与纠错。卡片内容与 v8.0 逐字一致,仅调整了表格版式与单元格内分行。

<!-- source-paragraph:V82-P2908 style=BodyCJK -->
以下 11 张卡片逐项展开每个变量的全部 39 个正式字段，并与合同 JSON 逐值同步。依赖项的空集合明确写作“无（空集合）”；它只表示该类依赖没有登记对象，不表示证据充分或经验成立。条件支持路由必须逐条整体读取，不能把不同路由的有利条件事后并取。

<!-- source-paragraph:V82-P2909 style=SecH2 -->
## A.1　HV01 结构域（完整接口卡）

<!-- source-paragraph:V82-P2910 style=CardLabel -->
A. 身份、命题与适用范围

## V82-T064

<table data-source-table="V82-T064">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P2911">
<!-- source-paragraph:V82-P2911 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P2912">
<!-- source-paragraph:V82-P2912 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P2913">
<!-- source-paragraph:V82-P2913 style=TableText -->
<pre>接口 ID（id）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P2914">
<!-- source-paragraph:V82-P2914 style=TableText -->
<pre>HV01</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P2915">
<!-- source-paragraph:V82-P2915 style=TableText -->
<pre>限定 ID（qualified_id）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P2916">
<!-- source-paragraph:V82-P2916 style=TableText -->
<pre>human_variable:HV01</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P2917">
<!-- source-paragraph:V82-P2917 style=TableText -->
<pre>名称（name）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P2918">
<!-- source-paragraph:V82-P2918 style=TableText -->
<pre>结构域</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P2919">
<!-- source-paragraph:V82-P2919 style=TableText -->
<pre>主张类型（claim_type）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P2920">
<!-- source-paragraph:V82-P2920 style=TableText -->
<pre>H</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P2921">
<!-- source-paragraph:V82-P2921 style=TableText -->
<pre>合同角色（contract_role）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P2922">
<!-- source-paragraph:V82-P2922 style=TableText -->
<pre>human_variable_interface</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P2923">
<!-- source-paragraph:V82-P2923 style=TableText -->
<pre>命题（proposition）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P2924">
<!-- source-paragraph:V82-P2924 style=TableText -->
<pre>D0只声明候选人类对象；只有预注册G1-instance显示候选分组相对匹配N0在预选结果上取得超过阈值的样本外或外推增益时，才在该实例范围登记有限有效结构域。</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P2925">
<!-- source-paragraph:V82-P2925 style=TableText -->
<pre>适用范围（scope）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P2926">
<!-- source-paragraph:V82-P2926 style=TableText -->
<pre>关系、团队、组织、制度与公共议题</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P2927">
<!-- source-paragraph:V82-P2927 style=TableText -->
<pre>暂停条件（pause_condition）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P2928">
<!-- source-paragraph:V82-P2928 style=TableText -->
<pre>对象、边界、尺度、时间窗、同一性或零模型不完整</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P2929 style=CardLabel -->
B. 正式依赖与推论边界

## V82-T065

<table data-source-table="V82-T065">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P2930">
<!-- source-paragraph:V82-P2930 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P2931">
<!-- source-paragraph:V82-P2931 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P2932">
<!-- source-paragraph:V82-P2932 style=TableText -->
<pre>推论依赖（inferential_requires）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P2933">
<!-- source-paragraph:V82-P2933 style=TableText -->
<pre>1. D0</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P2934">
<!-- source-paragraph:V82-P2934 style=TableText -->
<pre>协议依赖（protocol_requires）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P2935,V82-P2936,V82-P2937">
<!-- source-paragraph:V82-P2935 style=TableText -->
<!-- source-paragraph:V82-P2936 style=TableText -->
<!-- source-paragraph:V82-P2937 style=TableText -->
<pre>1. E1
2. EVIDENCE
3. SOURCE</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P2938">
<!-- source-paragraph:V82-P2938 style=TableText -->
<pre>限定／特化（specializes）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P2939">
<!-- source-paragraph:V82-P2939 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P2940">
<!-- source-paragraph:V82-P2940 style=TableText -->
<pre>适用对象引用（applies_to）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P2941">
<!-- source-paragraph:V82-P2941 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P2942">
<!-- source-paragraph:V82-P2942 style=TableText -->
<pre>条件支持路由（conditional_support_routes）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P2943,V82-P2944,V82-P2945,V82-P2946,V82-P2947,V82-P2948,V82-P2949,V82-P2950,V82-P2951,V82-P2952,V82-P2953,V82-P2954,V82-P2955,V82-P2956">
<!-- source-paragraph:V82-P2943 style=TableText -->
<!-- source-paragraph:V82-P2944 style=TableText -->
<!-- source-paragraph:V82-P2945 style=TableText -->
<!-- source-paragraph:V82-P2946 style=TableText -->
<!-- source-paragraph:V82-P2947 style=TableText -->
<!-- source-paragraph:V82-P2948 style=TableText -->
<!-- source-paragraph:V82-P2949 style=TableText -->
<!-- source-paragraph:V82-P2950 style=TableText -->
<!-- source-paragraph:V82-P2951 style=TableText -->
<!-- source-paragraph:V82-P2952 style=TableText -->
<!-- source-paragraph:V82-P2953 style=TableText -->
<!-- source-paragraph:V82-P2954 style=TableText -->
<!-- source-paragraph:V82-P2955 style=TableText -->
<!-- source-paragraph:V82-P2956 style=TableText -->
<pre>1. route_id=HV01-R0-candidate-object；
claim_level=candidate_description；
when=D0对象合同完整，但尚无符合资格且result_state=supported的G1-instance。；
additional_inferential_requires=无（空集合）；
additional_protocol_requires=无（空集合）；
allowed_conclusion=登记候选人类对象、材料集合、边界争议与G1补证需求。；
result_ceiling=仅到候选对象描述；不得称有限有效结构域，也不得限定HV02-HV11的经验对象范围。
2. route_id=HV01-R1-effective-domain；
claim_level=descriptive_classification；
when=同一对象、尺度、窗口、K与外推单元内的预注册G1-instance取得supported。；
additional_inferential_requires=G1-instance；
additional_protocol_requires=E4；
allowed_conclusion=登记该实例范围内的有限有效结构域、对象识别强度、边界可信度和适用窗。；
result_ceiling=只限预注册SP/T/K与generalization_unit；不得作终极本体、统一意志或授权判断。</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P2957">
<!-- source-paragraph:V82-P2957 style=TableText -->
<pre>允许推论（allowed_inference）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P2958">
<!-- source-paragraph:V82-P2958 style=TableText -->
<pre>1. 只在G1-instance预注册对象、尺度、窗口、结果与外推单位内登记有限有效结构域及识别强度</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P2959">
<!-- source-paragraph:V82-P2959 style=TableText -->
<pre>禁止跳跃（prohibited_leap）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P2960">
<!-- source-paragraph:V82-P2960 style=TableText -->
<pre>1. 命名即客观共同体2. 共同处境即共同意愿</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P2961 style=CardLabel -->
C. 九轴尺度与对象合同

## V82-T066

<table data-source-table="V82-T066">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P2962">
<!-- source-paragraph:V82-P2962 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P2963">
<!-- source-paragraph:V82-P2963 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P2964">
<!-- source-paragraph:V82-P2964 style=TableText -->
<pre>九轴尺度画像（scale_profile）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P2965">
<!-- source-paragraph:V82-P2965 style=TableText -->
<pre>SP=&lt;A,X,T,O,C,R,I,N,J&gt;；A=聚合层次：关系或事件单元、候选成员总体、边界内外分布及分组规则；X=空间范围：共同场所、组织边界、数字平台与跨域外部环境；T=时间跨度：识别窗口、成员变动周期与边界历史；O=组织层级：角色、团队、组织、制度至治理生态；C=因果层次：原始事件、互动机制、中观关系结构、制度与系统条件；R=观察分辨率：原始互动、事件序列、成员个案、边界分布、指标与摘要，并登记压缩损失；I=影响范围：直接成员、被排除者、间接受影响者、二阶外溢、跨域与代际位置；N=网络拓扑范围：成员关系、边界连接、孤立点与跨域桥接；J=管辖与授权范围：对象命名、边界采用及后续处置分别登记授权；不适用轴须登记not_applicable理由</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P2966">
<!-- source-paragraph:V82-P2966 style=TableText -->
<pre>有效对象（effective_object）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P2967">
<!-- source-paragraph:V82-P2967 style=TableText -->
<pre>由D0声明的候选对象；只有通过预注册G1-instance相对匹配N0的阈值检验后，才在该实例范围登记为有限有效结构域</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P2968">
<!-- source-paragraph:V82-P2968 style=TableText -->
<pre>跨尺度保持项（scale_invariants）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P2969">
<!-- source-paragraph:V82-P2969 style=TableText -->
<pre>1. 对象合同2. 参与与受影响位置</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P2970">
<!-- source-paragraph:V82-P2970 style=TableText -->
<pre>升格必补项（required_scale_additions）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P2971,V82-P2972,V82-P2973,V82-P2974">
<!-- source-paragraph:V82-P2971 style=TableText -->
<!-- source-paragraph:V82-P2972 style=TableText -->
<!-- source-paragraph:V82-P2973 style=TableText -->
<!-- source-paragraph:V82-P2974 style=TableText -->
<pre>1. 单位与总体
2. 代表性
3. J轴
4. 低可见位置</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P2975">
<!-- source-paragraph:V82-P2975 style=TableText -->
<pre>随尺度改变项（changing_semantics）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P2976">
<!-- source-paragraph:V82-P2976 style=TableText -->
<pre>1. 有效成员、关系和同一性可随尺度改变</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P2977">
<!-- source-paragraph:V82-P2977 style=TableText -->
<pre>不适用对象（non_applicable_objects）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P2978">
<!-- source-paragraph:V82-P2978 style=TableText -->
<pre>1. 无意向、制度或责任接口的非人系统</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P2979">
<!-- source-paragraph:V82-P2979 style=TableText -->
<pre>禁止升格（forbidden_elevation）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P2980">
<!-- source-paragraph:V82-P2980 style=TableText -->
<pre>1. 局部群体直接代表全部受影响者</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P2981 style=CardLabel -->
D. 状态、证据与变量流

## V82-T067

<table data-source-table="V82-T067">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P2982">
<!-- source-paragraph:V82-P2982 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P2983">
<!-- source-paragraph:V82-P2983 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P2984">
<!-- source-paragraph:V82-P2984 style=TableText -->
<pre>状态集合（state）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P2985">
<!-- source-paragraph:V82-P2985 style=TableText -->
<pre>1. 候选2. 可识别3. 边界争议4. 不成立</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P2986">
<!-- source-paragraph:V82-P2986 style=TableText -->
<pre>可观测项（observables）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P2987,V82-P2988,V82-P2989,V82-P2990">
<!-- source-paragraph:V82-P2987 style=TableText -->
<!-- source-paragraph:V82-P2988 style=TableText -->
<!-- source-paragraph:V82-P2989 style=TableText -->
<!-- source-paragraph:V82-P2990 style=TableText -->
<pre>1. 边界内外关系密度与约束差异
2. 成员进入、退出与被排除记录
3. 共同问题、资源通道或制度规则的重复共现
4. 改变分组规则后对象识别是否稳定</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P2991">
<!-- source-paragraph:V82-P2991 style=TableText -->
<pre>证据要求（evidence）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P2992,V82-P2993,V82-P2994,V82-P2995">
<!-- source-paragraph:V82-P2992 style=TableText -->
<!-- source-paragraph:V82-P2993 style=TableText -->
<!-- source-paragraph:V82-P2994 style=TableText -->
<!-- source-paragraph:V82-P2995 style=TableText -->
<pre>1. D0候选对象与同一性记录
2. G1-instance预注册表及匹配N0
3. 训练与样本外或外推结果
4. 候选分组与竞争分组的增益比较</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P2996">
<!-- source-paragraph:V82-P2996 style=TableText -->
<pre>输入依赖与接口内容（input_dependencies）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P2997,V82-P2998,V82-P2999">
<!-- source-paragraph:V82-P2997 style=TableText -->
<!-- source-paragraph:V82-P2998 style=TableText -->
<!-- source-paragraph:V82-P2999 style=TableText -->
<pre>1. D0只提供候选对象字段，不构成结构成立证据
2. 预注册G1-instance及匹配N0、阈值、模型类、样本或外推单位
3. 观察位置、竞争分组与E1协议</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3000">
<!-- source-paragraph:V82-P3000 style=TableText -->
<pre>输出效应与变量流（output_effects）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3001">
<!-- source-paragraph:V82-P3001 style=TableText -->
<pre>1. 仅在G1-instance通过后限定其余十变量的对象范围；未通过时保持候选或材料集合</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3002">
<!-- source-paragraph:V82-P3002 style=TableText -->
<pre>时间窗与时滞（time_window_and_lag）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3003">
<!-- source-paragraph:V82-P3003 style=TableText -->
<pre>登记识别窗口、边界变动与成员变化时滞</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3004">
<!-- source-paragraph:V82-P3004 style=TableText -->
<pre>不确定性（uncertainty）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3005">
<!-- source-paragraph:V82-P3005 style=TableText -->
<pre>记录边界争议、成员缺席和观察覆盖</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3006">
<!-- source-paragraph:V82-P3006 style=TableText -->
<pre>局部排除区（local_exclusion_zone）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3007">
<!-- source-paragraph:V82-P3007 style=TableText -->
<pre>无法安全表达或未被采样的位置不得被总体代表</pre>
</td>
</tr>
<tr>
<td data-source-cell="10,1" data-paragraphs="V82-P3008">
<!-- source-paragraph:V82-P3008 style=TableText -->
<pre>受影响位置（affected_positions）</pre>
</td>
<td data-source-cell="10,2" data-paragraphs="V82-P3009">
<!-- source-paragraph:V82-P3009 style=TableText -->
<pre>1. 成员2. 被排除者3. 边界外成本承担者</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3010 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

## V82-T068

<table data-source-table="V82-T068">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3011">
<!-- source-paragraph:V82-P3011 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3012">
<!-- source-paragraph:V82-P3012 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3013">
<!-- source-paragraph:V82-P3013 style=TableText -->
<pre>承接载体（carrier）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3014">
<!-- source-paragraph:V82-P3014 style=TableText -->
<pre>1. 关系网络2. 组织边界3. 制度记录</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3015">
<!-- source-paragraph:V82-P3015 style=TableText -->
<pre>责任主体（responsible_subject）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3016,V82-P3017">
<!-- source-paragraph:V82-P3016 style=TableText -->
<!-- source-paragraph:V82-P3017 style=TableText -->
<pre>1. 提出结构域判断的分析者
2. 使用该判断的决策者</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3018">
<!-- source-paragraph:V82-P3018 style=TableText -->
<pre>规范地位（normative_status）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3019">
<!-- source-paragraph:V82-P3019 style=TableText -->
<pre>描述性H-World接口，不产生正当性</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3020">
<!-- source-paragraph:V82-P3020 style=TableText -->
<pre>判断上限（judgment_ceiling）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3021">
<!-- source-paragraph:V82-P3021 style=TableText -->
<pre>只有G1-instance通过时，且仅限预注册对象、尺度、窗口、结果与外推单位，才可登记解释级有限有效对象；否则仅为候选对象或材料集合</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3022">
<!-- source-paragraph:V82-P3022 style=TableText -->
<pre>行动上限（action_ceiling）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3023">
<!-- source-paragraph:V82-P3023 style=TableText -->
<pre>本变量只生成候选结构域、边界争议与补证需求描述，不授权纳入、排除或处置；任何现实调整须另过C12、运行时显式N前提、J授权与O程序</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3024">
<!-- source-paragraph:V82-P3024 style=TableText -->
<pre>反例（counterexamples）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3025,V82-P3026">
<!-- source-paragraph:V82-P3025 style=TableText -->
<!-- source-paragraph:V82-P3026 style=TableText -->
<pre>1. 同一场所中反复共现的人群没有稳定关系或共同约束
2. 分析者划定的群组在改变分组规则后立即消失</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3027">
<!-- source-paragraph:V82-P3027 style=TableText -->
<pre>申诉（appeal）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3028">
<!-- source-paragraph:V82-P3028 style=TableText -->
<pre>依appeal_and_rollback_rule，成员与受影响位置可经安全可达、反报复通道挑战边界、代表性和同一性判据，并触发与原命名或决策链独立的复核</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3029">
<!-- source-paragraph:V82-P3029 style=TableText -->
<pre>回滚（rollback）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3030">
<!-- source-paragraph:V82-P3030 style=TableText -->
<pre>依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销结构域登记、移除其对下游对象范围的效力并恢复为材料集合，保留版本与完成验证</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3031 style=SecH2 -->
## A.2　HV02 边界与接口（完整接口卡）

<!-- source-paragraph:V82-P3032 style=CardLabel -->
A. 身份、命题与适用范围

## V82-T069

<table data-source-table="V82-T069">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3033">
<!-- source-paragraph:V82-P3033 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3034">
<!-- source-paragraph:V82-P3034 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3035">
<!-- source-paragraph:V82-P3035 style=TableText -->
<pre>接口 ID（id）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3036">
<!-- source-paragraph:V82-P3036 style=TableText -->
<pre>HV02</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3037">
<!-- source-paragraph:V82-P3037 style=TableText -->
<pre>限定 ID（qualified_id）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3038">
<!-- source-paragraph:V82-P3038 style=TableText -->
<pre>human_variable:HV02</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3039">
<!-- source-paragraph:V82-P3039 style=TableText -->
<pre>名称（name）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3040">
<!-- source-paragraph:V82-P3040 style=TableText -->
<pre>边界与接口</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3041">
<!-- source-paragraph:V82-P3041 style=TableText -->
<pre>主张类型（claim_type）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3042">
<!-- source-paragraph:V82-P3042 style=TableText -->
<pre>H</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3043">
<!-- source-paragraph:V82-P3043 style=TableText -->
<pre>合同角色（contract_role）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3044">
<!-- source-paragraph:V82-P3044 style=TableText -->
<pre>human_variable_interface</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3045">
<!-- source-paragraph:V82-P3045 style=TableText -->
<pre>命题（proposition）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3046">
<!-- source-paragraph:V82-P3046 style=TableText -->
<pre>人类边界必须同时登记成员、资源、信息、权利、责任与跨界接口。</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3047">
<!-- source-paragraph:V82-P3047 style=TableText -->
<pre>适用范围（scope）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3048">
<!-- source-paragraph:V82-P3048 style=TableText -->
<pre>存在纳入、排除、交换或管辖的人类结构</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3049">
<!-- source-paragraph:V82-P3049 style=TableText -->
<pre>暂停条件（pause_condition）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3050">
<!-- source-paragraph:V82-P3050 style=TableText -->
<pre>正式边界与实际边界混同或排除项不可见</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3051 style=CardLabel -->
B. 正式依赖与推论边界

## V82-T070

<table data-source-table="V82-T070">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3052">
<!-- source-paragraph:V82-P3052 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3053">
<!-- source-paragraph:V82-P3053 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3054">
<!-- source-paragraph:V82-P3054 style=TableText -->
<pre>推论依赖（inferential_requires）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3055">
<!-- source-paragraph:V82-P3055 style=TableText -->
<pre>1. human_variable:HV01</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3056">
<!-- source-paragraph:V82-P3056 style=TableText -->
<pre>协议依赖（protocol_requires）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3057,V82-P3058,V82-P3059">
<!-- source-paragraph:V82-P3057 style=TableText -->
<!-- source-paragraph:V82-P3058 style=TableText -->
<!-- source-paragraph:V82-P3059 style=TableText -->
<pre>1. E1
2. EVIDENCE
3. SOURCE</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3060">
<!-- source-paragraph:V82-P3060 style=TableText -->
<pre>限定／特化（specializes）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3061">
<!-- source-paragraph:V82-P3061 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3062">
<!-- source-paragraph:V82-P3062 style=TableText -->
<pre>适用对象引用（applies_to）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3063">
<!-- source-paragraph:V82-P3063 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3064">
<!-- source-paragraph:V82-P3064 style=TableText -->
<pre>条件支持路由（conditional_support_routes）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3065,V82-P3066,V82-P3067,V82-P3068,V82-P3069,V82-P3070,V82-P3071,V82-P3072,V82-P3073,V82-P3074,V82-P3075,V82-P3076,V82-P3077,V82-P3078">
<!-- source-paragraph:V82-P3065 style=TableText -->
<!-- source-paragraph:V82-P3066 style=TableText -->
<!-- source-paragraph:V82-P3067 style=TableText -->
<!-- source-paragraph:V82-P3068 style=TableText -->
<!-- source-paragraph:V82-P3069 style=TableText -->
<!-- source-paragraph:V82-P3070 style=TableText -->
<!-- source-paragraph:V82-P3071 style=TableText -->
<!-- source-paragraph:V82-P3072 style=TableText -->
<!-- source-paragraph:V82-P3073 style=TableText -->
<!-- source-paragraph:V82-P3074 style=TableText -->
<!-- source-paragraph:V82-P3075 style=TableText -->
<!-- source-paragraph:V82-P3076 style=TableText -->
<!-- source-paragraph:V82-P3077 style=TableText -->
<!-- source-paragraph:V82-P3078 style=TableText -->
<pre>1. route_id=HV02-R0-boundary-inventory；
claim_level=descriptive_classification；
when=成员、资源、信息、权利、责任、跨界接口及正式—实际边界差异可逐项登记。；
additional_inferential_requires=无（空集合）；
additional_protocol_requires=无（空集合）；
allowed_conclusion=描述边界状态、接口通达性、守门位置、拒绝记录与排除风险。；
result_ceiling=只到边界与接口清单；不得断言边界已产生因果选择效应。
2. route_id=HV02-R1-selective-effect；
claim_level=conditional_effect；
when=预注册边界或接口变动经符合资格的G2-instance显示对指定跨界流、准入或拒绝结果有超过阈值的通道效应。；
additional_inferential_requires=G2-instance；
additional_protocol_requires=CAUSAL、E4；
allowed_conclusion=登记指定通道、窗口与位置上的边界选择效应及跨界成本分布。；
result_ceiling=只限已检验通道与结果；不得从空间、组织或影响范围推出J轴管辖与处置权。</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3079">
<!-- source-paragraph:V82-P3079 style=TableText -->
<pre>允许推论（allowed_inference）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3080">
<!-- source-paragraph:V82-P3080 style=TableText -->
<pre>1. 边界选择性2. 接口通达性3. 跨界成本</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3081">
<!-- source-paragraph:V82-P3081 style=TableText -->
<pre>禁止跳跃（prohibited_leap）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3082,V82-P3083,V82-P3084">
<!-- source-paragraph:V82-P3082 style=TableText -->
<!-- source-paragraph:V82-P3083 style=TableText -->
<!-- source-paragraph:V82-P3084 style=TableText -->
<pre>1. 边界等于封闭
2. 成员身份等于同意
3. 影响范围等于管辖权</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3085 style=CardLabel -->
C. 九轴尺度与对象合同

## V82-T071

<table data-source-table="V82-T071">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3086">
<!-- source-paragraph:V82-P3086 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3087">
<!-- source-paragraph:V82-P3087 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3088">
<!-- source-paragraph:V82-P3088 style=TableText -->
<pre>九轴尺度画像（scale_profile）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3089">
<!-- source-paragraph:V82-P3089 style=TableText -->
<pre>SP=&lt;A,X,T,O,C,R,I,N,J&gt;；A=聚合层次：单次跨界事件、接口使用个案、成员类别总体、准入拒绝分布及聚合规则；X=空间范围：物理入口、组织边界、数字接口、司法辖区与跨域通道；T=时间跨度：边界生效期、接口等待、迁移时滞与重组周期；O=组织层级：使用者角色、守门团队、组织、制度至治理生态；C=因果层次：跨界事件、守门互动机制、接口结构、制度规则与系统条件；R=观察分辨率：原始准入拒绝记录、使用序列、个案、流量分布、服务指标与摘要，并登记压缩损失；I=影响范围：直接使用者、被排除者、间接受益或成本位置、二阶外溢、跨域与代际影响；N=网络拓扑范围：接口节点、守门瓶颈、替代路径与跨域连接；J=管辖与授权范围：纳入、排除、接口改变及权利责任调整分别登记授权；升格须记录逐轴差值</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3090">
<!-- source-paragraph:V82-P3090 style=TableText -->
<pre>有效对象（effective_object）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3091">
<!-- source-paragraph:V82-P3091 style=TableText -->
<pre>对资源、信息、权利或责任流产生选择性的边界</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3092">
<!-- source-paragraph:V82-P3092 style=TableText -->
<pre>跨尺度保持项（scale_invariants）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3093">
<!-- source-paragraph:V82-P3093 style=TableText -->
<pre>1. 内外位置2. 跨界通道3. 权利责任边界</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3094">
<!-- source-paragraph:V82-P3094 style=TableText -->
<pre>升格必补项（required_scale_additions）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3095,V82-P3096,V82-P3097,V82-P3098">
<!-- source-paragraph:V82-P3095 style=TableText -->
<!-- source-paragraph:V82-P3096 style=TableText -->
<!-- source-paragraph:V82-P3097 style=TableText -->
<!-- source-paragraph:V82-P3098 style=TableText -->
<pre>1. 新成员类别
2. 跨域接口
3. 代表与授权
4. 保护继承</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3099">
<!-- source-paragraph:V82-P3099 style=TableText -->
<pre>随尺度改变项（changing_semantics）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3100">
<!-- source-paragraph:V82-P3100 style=TableText -->
<pre>1. 成员、接口与实际控制边界可改变</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3101">
<!-- source-paragraph:V82-P3101 style=TableText -->
<pre>不适用对象（non_applicable_objects）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3102">
<!-- source-paragraph:V82-P3102 style=TableText -->
<pre>1. 无成员、权利或责任概念的非人边界</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3103">
<!-- source-paragraph:V82-P3103 style=TableText -->
<pre>禁止升格（forbidden_elevation）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3104">
<!-- source-paragraph:V82-P3104 style=TableText -->
<pre>1. 空间或组织范围扩大自动产生管辖权</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3105 style=CardLabel -->
D. 状态、证据与变量流

## V82-T072

<table data-source-table="V82-T072">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3106">
<!-- source-paragraph:V82-P3106 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3107">
<!-- source-paragraph:V82-P3107 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3108">
<!-- source-paragraph:V82-P3108 style=TableText -->
<pre>状态集合（state）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3109,V82-P3110,V82-P3111,V82-P3112,V82-P3113">
<!-- source-paragraph:V82-P3109 style=TableText -->
<!-- source-paragraph:V82-P3110 style=TableText -->
<!-- source-paragraph:V82-P3111 style=TableText -->
<!-- source-paragraph:V82-P3112 style=TableText -->
<!-- source-paragraph:V82-P3113 style=TableText -->
<pre>1. 开放
2. 选择性开放
3. 封闭
4. 争议
5. 重组</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3114">
<!-- source-paragraph:V82-P3114 style=TableText -->
<pre>可观测项（observables）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3115,V82-P3116,V82-P3117,V82-P3118">
<!-- source-paragraph:V82-P3115 style=TableText -->
<!-- source-paragraph:V82-P3116 style=TableText -->
<!-- source-paragraph:V82-P3117 style=TableText -->
<!-- source-paragraph:V82-P3118 style=TableText -->
<pre>1. 成员资格、准入与退出决定
2. 资源、信息、权利和责任的跨界流量
3. 守门节点、等待时间与拒绝理由
4. 正式边界与实际通行边界的差异</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3119">
<!-- source-paragraph:V82-P3119 style=TableText -->
<pre>证据要求（evidence）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3120,V82-P3121,V82-P3122">
<!-- source-paragraph:V82-P3120 style=TableText -->
<!-- source-paragraph:V82-P3121 style=TableText -->
<!-- source-paragraph:V82-P3122 style=TableText -->
<pre>1. 成员名单与例外
2. 接口使用记录
3. 跨界流和拒绝记录</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3123">
<!-- source-paragraph:V82-P3123 style=TableText -->
<pre>输入依赖与接口内容（input_dependencies）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3124">
<!-- source-paragraph:V82-P3124 style=TableText -->
<pre>1. HV01结构域2. 角色与授权</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3125">
<!-- source-paragraph:V82-P3125 style=TableText -->
<pre>输出效应与变量流（output_effects）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3126,V82-P3127,V82-P3128">
<!-- source-paragraph:V82-P3126 style=TableText -->
<!-- source-paragraph:V82-P3127 style=TableText -->
<!-- source-paragraph:V82-P3128 style=TableText -->
<pre>1. HV05承接
2. HV07写回
3. PF-9退出</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3129">
<!-- source-paragraph:V82-P3129 style=TableText -->
<pre>时间窗与时滞（time_window_and_lag）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3130">
<!-- source-paragraph:V82-P3130 style=TableText -->
<pre>记录边界生效、变更、退出和申诉时滞</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3131">
<!-- source-paragraph:V82-P3131 style=TableText -->
<pre>不确定性（uncertainty）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3132">
<!-- source-paragraph:V82-P3132 style=TableText -->
<pre>记录非正式边界、代理访问和数字空间漂移</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3133">
<!-- source-paragraph:V82-P3133 style=TableText -->
<pre>局部排除区（local_exclusion_zone）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3134">
<!-- source-paragraph:V82-P3134 style=TableText -->
<pre>无法接入接口、无法退出或受保护不公开的位置</pre>
</td>
</tr>
<tr>
<td data-source-cell="10,1" data-paragraphs="V82-P3135">
<!-- source-paragraph:V82-P3135 style=TableText -->
<pre>受影响位置（affected_positions）</pre>
</td>
<td data-source-cell="10,2" data-paragraphs="V82-P3136,V82-P3137,V82-P3138,V82-P3139">
<!-- source-paragraph:V82-P3136 style=TableText -->
<!-- source-paragraph:V82-P3137 style=TableText -->
<!-- source-paragraph:V82-P3138 style=TableText -->
<!-- source-paragraph:V82-P3139 style=TableText -->
<pre>1. 成员
2. 申请者
3. 被排除者
4. 边界外承担者</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3140 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

## V82-T073

<table data-source-table="V82-T073">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3141">
<!-- source-paragraph:V82-P3141 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3142">
<!-- source-paragraph:V82-P3142 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3143">
<!-- source-paragraph:V82-P3143 style=TableText -->
<pre>承接载体（carrier）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3144,V82-P3145,V82-P3146,V82-P3147">
<!-- source-paragraph:V82-P3144 style=TableText -->
<!-- source-paragraph:V82-P3145 style=TableText -->
<!-- source-paragraph:V82-P3146 style=TableText -->
<!-- source-paragraph:V82-P3147 style=TableText -->
<pre>1. 成员规则
2. 访问机制
3. 法律或制度边界
4. 技术接口</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3148">
<!-- source-paragraph:V82-P3148 style=TableText -->
<pre>责任主体（responsible_subject）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3149">
<!-- source-paragraph:V82-P3149 style=TableText -->
<pre>1. 边界制定者2. 接口运营者3. 授权者</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3150">
<!-- source-paragraph:V82-P3150 style=TableText -->
<pre>规范地位（normative_status）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3151">
<!-- source-paragraph:V82-P3151 style=TableText -->
<pre>边界事实与边界正当性分离</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3152">
<!-- source-paragraph:V82-P3152 style=TableText -->
<pre>判断上限（judgment_ceiling）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3153">
<!-- source-paragraph:V82-P3153 style=TableText -->
<pre>接口与影响证据充分时至诊断级</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3154">
<!-- source-paragraph:V82-P3154 style=TableText -->
<pre>行动上限（action_ceiling）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3155">
<!-- source-paragraph:V82-P3155 style=TableText -->
<pre>本变量只生成边界状态、接口障碍、排除风险与测试需求描述，不授权改变准入、退出、权利或资源流；任何现实调整须另过C12、运行时显式N前提、J授权与O程序</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3156">
<!-- source-paragraph:V82-P3156 style=TableText -->
<pre>反例（counterexamples）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3157,V82-P3158">
<!-- source-paragraph:V82-P3157 style=TableText -->
<!-- source-paragraph:V82-P3158 style=TableText -->
<pre>1. 正式成员边界与实际资源控制边界相反
2. 数字接口开放但物理、语言或安全门槛使部分位置无法进入</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3159">
<!-- source-paragraph:V82-P3159 style=TableText -->
<pre>申诉（appeal）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3160">
<!-- source-paragraph:V82-P3160 style=TableText -->
<pre>依appeal_and_rollback_rule，边界内外受影响者可经安全可达、反报复通道挑战纳入、排除和接口障碍，并触发与原边界决策链独立的复核</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3161">
<!-- source-paragraph:V82-P3161 style=TableText -->
<pre>回滚（rollback）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3162">
<!-- source-paragraph:V82-P3162 style=TableText -->
<pre>依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内纠正成员与拒绝记录、实际恢复受影响的准入权利或接口状态并撤销错误边界行动，保留版本与完成验证</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3163 style=SecH2 -->
## A.3　HV03 指向锚点（完整接口卡）

<!-- source-paragraph:V82-P3164 style=CardLabel -->
A. 身份、命题与适用范围

## V82-T074

<table data-source-table="V82-T074">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3165">
<!-- source-paragraph:V82-P3165 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3166">
<!-- source-paragraph:V82-P3166 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3167">
<!-- source-paragraph:V82-P3167 style=TableText -->
<pre>接口 ID（id）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3168">
<!-- source-paragraph:V82-P3168 style=TableText -->
<pre>HV03</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3169">
<!-- source-paragraph:V82-P3169 style=TableText -->
<pre>限定 ID（qualified_id）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3170">
<!-- source-paragraph:V82-P3170 style=TableText -->
<pre>human_variable:HV03</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3171">
<!-- source-paragraph:V82-P3171 style=TableText -->
<pre>名称（name）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3172">
<!-- source-paragraph:V82-P3172 style=TableText -->
<pre>指向锚点</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3173">
<!-- source-paragraph:V82-P3173 style=TableText -->
<pre>主张类型（claim_type）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3174">
<!-- source-paragraph:V82-P3174 style=TableText -->
<pre>H</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3175">
<!-- source-paragraph:V82-P3175 style=TableText -->
<pre>合同角色（contract_role）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3176">
<!-- source-paragraph:V82-P3176 style=TableText -->
<pre>human_variable_interface</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3177">
<!-- source-paragraph:V82-P3177 style=TableText -->
<pre>命题（proposition）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3178">
<!-- source-paragraph:V82-P3178 style=TableText -->
<pre>目标、身份、记忆、承诺、恐惧或共同问题只有改变资源与行动时才构成指向锚点。</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3179">
<!-- source-paragraph:V82-P3179 style=TableText -->
<pre>适用范围（scope）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3180">
<!-- source-paragraph:V82-P3180 style=TableText -->
<pre>具有意向、协调或共同问题的人类结构</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3181">
<!-- source-paragraph:V82-P3181 style=TableText -->
<pre>暂停条件（pause_condition）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3182">
<!-- source-paragraph:V82-P3182 style=TableText -->
<pre>只有口号、解释者投射或被强制的一致表达</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3183 style=CardLabel -->
B. 正式依赖与推论边界

## V82-T075

<table data-source-table="V82-T075">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3184">
<!-- source-paragraph:V82-P3184 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3185">
<!-- source-paragraph:V82-P3185 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3186">
<!-- source-paragraph:V82-P3186 style=TableText -->
<pre>推论依赖（inferential_requires）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3187">
<!-- source-paragraph:V82-P3187 style=TableText -->
<pre>1. human_variable:HV01</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3188">
<!-- source-paragraph:V82-P3188 style=TableText -->
<pre>协议依赖（protocol_requires）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3189,V82-P3190,V82-P3191">
<!-- source-paragraph:V82-P3189 style=TableText -->
<!-- source-paragraph:V82-P3190 style=TableText -->
<!-- source-paragraph:V82-P3191 style=TableText -->
<pre>1. E2
2. EVIDENCE
3. SOURCE</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3192">
<!-- source-paragraph:V82-P3192 style=TableText -->
<pre>限定／特化（specializes）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3193">
<!-- source-paragraph:V82-P3193 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3194">
<!-- source-paragraph:V82-P3194 style=TableText -->
<pre>适用对象引用（applies_to）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3195">
<!-- source-paragraph:V82-P3195 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3196">
<!-- source-paragraph:V82-P3196 style=TableText -->
<pre>条件支持路由（conditional_support_routes）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3197,V82-P3198,V82-P3199,V82-P3200,V82-P3201,V82-P3202,V82-P3203,V82-P3204,V82-P3205,V82-P3206,V82-P3207,V82-P3208,V82-P3209,V82-P3210">
<!-- source-paragraph:V82-P3197 style=TableText -->
<!-- source-paragraph:V82-P3198 style=TableText -->
<!-- source-paragraph:V82-P3199 style=TableText -->
<!-- source-paragraph:V82-P3200 style=TableText -->
<!-- source-paragraph:V82-P3201 style=TableText -->
<!-- source-paragraph:V82-P3202 style=TableText -->
<!-- source-paragraph:V82-P3203 style=TableText -->
<!-- source-paragraph:V82-P3204 style=TableText -->
<!-- source-paragraph:V82-P3205 style=TableText -->
<!-- source-paragraph:V82-P3206 style=TableText -->
<!-- source-paragraph:V82-P3207 style=TableText -->
<!-- source-paragraph:V82-P3208 style=TableText -->
<!-- source-paragraph:V82-P3209 style=TableText -->
<!-- source-paragraph:V82-P3210 style=TableText -->
<pre>1. route_id=HV03-R0-candidate-anchor；
claim_level=candidate_description；
when=目标、身份、记忆、承诺、恐惧或共同问题有可追踪表达与承载形式，但尚无符合资格的H1-instance。；
additional_inferential_requires=无（空集合）；
additional_protocol_requires=无（空集合）；
allowed_conclusion=登记候选意义材料、异质表达、代表性争议与H1补证需求。；
result_ceiling=仅称候选意义表达；不得称有效指向锚点或共同意志。
2. route_id=HV03-R1-effective-anchor；
claim_level=conditional_effect；
when=预注册H1-instance在资源配置、行动选择或协调结果中唯一预选的判据取得supported。；
additional_inferential_requires=H1-instance；
additional_protocol_requires=CAUSAL、E4；
allowed_conclusion=登记该实例、结果家族、尺度与窗口内的条件性有效指向锚点。；
result_ceiling=不外推到未选资源、行动或协调结果，也不推出真实同意、统一内心或强制统一意义。</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3211">
<!-- source-paragraph:V82-P3211 style=TableText -->
<pre>允许推论（allowed_inference）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3212">
<!-- source-paragraph:V82-P3212 style=TableText -->
<pre>1. 条件性的协调方向与冲突锚点</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3213">
<!-- source-paragraph:V82-P3213 style=TableText -->
<pre>禁止跳跃（prohibited_leap）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3214,V82-P3215,V82-P3216">
<!-- source-paragraph:V82-P3214 style=TableText -->
<!-- source-paragraph:V82-P3215 style=TableText -->
<!-- source-paragraph:V82-P3216 style=TableText -->
<pre>1. 群体具有统一内心
2. 共同语言等于真实同意
3. 目标正当</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3217 style=CardLabel -->
C. 九轴尺度与对象合同

## V82-T076

<table data-source-table="V82-T076">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3218">
<!-- source-paragraph:V82-P3218 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3219">
<!-- source-paragraph:V82-P3219 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3220">
<!-- source-paragraph:V82-P3220 style=TableText -->
<pre>九轴尺度画像（scale_profile）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3221">
<!-- source-paragraph:V82-P3221 style=TableText -->
<pre>SP=&lt;A,X,T,O,C,R,I,N,J&gt;；A=聚合层次：单次表达或行动、主体个案、候选参与总体、立场分布及聚合规则；X=空间范围：关系现场、组织空间、数字公共空间与跨域传播范围；T=时间跨度：表达—行动窗口、承诺周期、漂移与解耦时滞；O=组织层级：行动角色、团队、组织、制度至公共治理生态；C=因果层次：表达事件、意义—行动互动机制、中观协调结构、制度安排与系统条件；R=观察分辨率：原始表达与行动、事件序列、个案、立场分布、协调指标与摘要，并登记压缩损失；I=影响范围：直接参与者、异议者、间接受影响者、二阶协调后果、跨域与代际影响；N=网络拓扑范围：表达传播、协调连接、异质簇群与桥接节点；J=管辖与授权范围：锚点命名、代表性采用、协调或统一要求分别登记授权；必须保留异质锚点</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3222">
<!-- source-paragraph:V82-P3222 style=TableText -->
<pre>有效对象（effective_object）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3223">
<!-- source-paragraph:V82-P3223 style=TableText -->
<pre>能改变资源或行动的目标、身份、记忆、承诺、恐惧或共同问题</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3224">
<!-- source-paragraph:V82-P3224 style=TableText -->
<pre>跨尺度保持项（scale_invariants）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3225">
<!-- source-paragraph:V82-P3225 style=TableText -->
<pre>1. 意义到资源或行动的桥接</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3226">
<!-- source-paragraph:V82-P3226 style=TableText -->
<pre>升格必补项（required_scale_additions）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3227,V82-P3228,V82-P3229,V82-P3230">
<!-- source-paragraph:V82-P3227 style=TableText -->
<!-- source-paragraph:V82-P3228 style=TableText -->
<!-- source-paragraph:V82-P3229 style=TableText -->
<!-- source-paragraph:V82-P3230 style=TableText -->
<pre>1. 代表规则
2. 异质性
3. 成本收益分布
4. J轴</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3231">
<!-- source-paragraph:V82-P3231 style=TableText -->
<pre>随尺度改变项（changing_semantics）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3232">
<!-- source-paragraph:V82-P3232 style=TableText -->
<pre>1. 锚点内容、强度和承载主体可改变</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3233">
<!-- source-paragraph:V82-P3233 style=TableText -->
<pre>不适用对象（non_applicable_objects）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3234">
<!-- source-paragraph:V82-P3234 style=TableText -->
<pre>1. 无意向、意义或承诺能力的非人系统</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3235">
<!-- source-paragraph:V82-P3235 style=TableText -->
<pre>禁止升格（forbidden_elevation）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3236">
<!-- source-paragraph:V82-P3236 style=TableText -->
<pre>1. 局部表达直接升级为共同意志</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3237 style=CardLabel -->
D. 状态、证据与变量流

## V82-T077

<table data-source-table="V82-T077">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3238">
<!-- source-paragraph:V82-P3238 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3239">
<!-- source-paragraph:V82-P3239 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3240">
<!-- source-paragraph:V82-P3240 style=TableText -->
<pre>状态集合（state）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3241,V82-P3242,V82-P3243,V82-P3244,V82-P3245">
<!-- source-paragraph:V82-P3241 style=TableText -->
<!-- source-paragraph:V82-P3242 style=TableText -->
<!-- source-paragraph:V82-P3243 style=TableText -->
<!-- source-paragraph:V82-P3244 style=TableText -->
<!-- source-paragraph:V82-P3245 style=TableText -->
<pre>1. 分散
2. 凝聚
3. 竞争
4. 固化
5. 解耦</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3246">
<!-- source-paragraph:V82-P3246 style=TableText -->
<pre>可观测项（observables）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3247,V82-P3248,V82-P3249,V82-P3250">
<!-- source-paragraph:V82-P3247 style=TableText -->
<!-- source-paragraph:V82-P3248 style=TableText -->
<!-- source-paragraph:V82-P3249 style=TableText -->
<!-- source-paragraph:V82-P3250 style=TableText -->
<pre>1. 预注册意义表达出现前后的资源配置差异
2. 行动选择、协作完成率或冲突模式变化
3. 不同位置对锚点的接受、拒绝与替代表述
4. 比较条件下结果差异是否超过预定阈值</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3251">
<!-- source-paragraph:V82-P3251 style=TableText -->
<pre>证据要求（evidence）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3252,V82-P3253,V82-P3254,V82-P3255">
<!-- source-paragraph:V82-P3252 style=TableText -->
<!-- source-paragraph:V82-P3253 style=TableText -->
<!-- source-paragraph:V82-P3254 style=TableText -->
<!-- source-paragraph:V82-P3255 style=TableText -->
<pre>1. 资源调整
2. 行动序列
3. 承诺与退出记录
4. 冲突证据</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3256">
<!-- source-paragraph:V82-P3256 style=TableText -->
<pre>输入依赖与接口内容（input_dependencies）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3257">
<!-- source-paragraph:V82-P3257 style=TableText -->
<pre>1. 参与位置2. 表达安全3. 资源与行动数据</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3258">
<!-- source-paragraph:V82-P3258 style=TableText -->
<pre>输出效应与变量流（output_effects）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3259">
<!-- source-paragraph:V82-P3259 style=TableText -->
<pre>1. 生成事件2. 承接动员3. 规范选择议程</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3260">
<!-- source-paragraph:V82-P3260 style=TableText -->
<pre>时间窗与时滞（time_window_and_lag）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3261">
<!-- source-paragraph:V82-P3261 style=TableText -->
<pre>区分短期口号、长期承诺与代际记忆</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3262">
<!-- source-paragraph:V82-P3262 style=TableText -->
<pre>不确定性（uncertainty）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3263">
<!-- source-paragraph:V82-P3263 style=TableText -->
<pre>记录沉默、强制一致与内部异质性</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3264">
<!-- source-paragraph:V82-P3264 style=TableText -->
<pre>局部排除区（local_exclusion_zone）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3265">
<!-- source-paragraph:V82-P3265 style=TableText -->
<pre>低安全位置的不同目标不得被聚合抹去</pre>
</td>
</tr>
<tr>
<td data-source-cell="10,1" data-paragraphs="V82-P3266">
<!-- source-paragraph:V82-P3266 style=TableText -->
<pre>受影响位置（affected_positions）</pre>
</td>
<td data-source-cell="10,2" data-paragraphs="V82-P3267,V82-P3268,V82-P3269,V82-P3270">
<!-- source-paragraph:V82-P3267 style=TableText -->
<!-- source-paragraph:V82-P3268 style=TableText -->
<!-- source-paragraph:V82-P3269 style=TableText -->
<!-- source-paragraph:V82-P3270 style=TableText -->
<pre>1. 认同者
2. 异议者
3. 被代表者
4. 成本承担者</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3271 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

## V82-T078

<table data-source-table="V82-T078">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3272">
<!-- source-paragraph:V82-P3272 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3273">
<!-- source-paragraph:V82-P3273 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3274">
<!-- source-paragraph:V82-P3274 style=TableText -->
<pre>承接载体（carrier）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3275,V82-P3276,V82-P3277,V82-P3278,V82-P3279">
<!-- source-paragraph:V82-P3275 style=TableText -->
<!-- source-paragraph:V82-P3276 style=TableText -->
<!-- source-paragraph:V82-P3277 style=TableText -->
<!-- source-paragraph:V82-P3278 style=TableText -->
<!-- source-paragraph:V82-P3279 style=TableText -->
<pre>1. 叙事
2. 承诺
3. 共同记忆
4. 制度目标
5. 问题定义</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3280">
<!-- source-paragraph:V82-P3280 style=TableText -->
<pre>责任主体（responsible_subject）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3281">
<!-- source-paragraph:V82-P3281 style=TableText -->
<pre>1. 提出代表性主张者2. 据此配置资源者</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3282">
<!-- source-paragraph:V82-P3282 style=TableText -->
<pre>规范地位（normative_status）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3283">
<!-- source-paragraph:V82-P3283 style=TableText -->
<pre>锚点存在不证明其正当</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3284">
<!-- source-paragraph:V82-P3284 style=TableText -->
<pre>判断上限（judgment_ceiling）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3285">
<!-- source-paragraph:V82-P3285 style=TableText -->
<pre>有行动桥接时至解释级，无桥接时仅描述表达</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3286">
<!-- source-paragraph:V82-P3286 style=TableText -->
<pre>行动上限（action_ceiling）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3287">
<!-- source-paragraph:V82-P3287 style=TableText -->
<pre>本变量只生成候选锚点、异质表达、比较结果与补证需求描述，不授权统一意义、代表意愿或协调行动；任何现实调整须另过C12、运行时显式N前提、J授权与O程序</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3288">
<!-- source-paragraph:V82-P3288 style=TableText -->
<pre>反例（counterexamples）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3289,V82-P3290">
<!-- source-paragraph:V82-P3289 style=TableText -->
<!-- source-paragraph:V82-P3290 style=TableText -->
<pre>1. 反复出现的口号没有改变任何资源配置或行动
2. 高压场景中的一致表达掩盖相互冲突的真实目标</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3291">
<!-- source-paragraph:V82-P3291 style=TableText -->
<pre>申诉（appeal）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3292">
<!-- source-paragraph:V82-P3292 style=TableText -->
<pre>依appeal_and_rollback_rule，成员可经安全可达、反报复通道否认代表性、提交异质目标或拒绝被锚定，并触发与原锚点判断链独立的复核</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3293">
<!-- source-paragraph:V82-P3293 style=TableText -->
<pre>回滚（rollback）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3294">
<!-- source-paragraph:V82-P3294 style=TableText -->
<pre>依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销锚点命名、移除其代表性与下游协调效力并恢复异质表达状态，保留版本与完成验证</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3295 style=SecH2 -->
## A.4　HV04 生成节点（完整接口卡）

<!-- source-paragraph:V82-P3296 style=CardLabel -->
A. 身份、命题与适用范围

## V82-T079

<table data-source-table="V82-T079">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3297">
<!-- source-paragraph:V82-P3297 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3298">
<!-- source-paragraph:V82-P3298 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3299">
<!-- source-paragraph:V82-P3299 style=TableText -->
<pre>接口 ID（id）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3300">
<!-- source-paragraph:V82-P3300 style=TableText -->
<pre>HV04</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3301">
<!-- source-paragraph:V82-P3301 style=TableText -->
<pre>限定 ID（qualified_id）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3302">
<!-- source-paragraph:V82-P3302 style=TableText -->
<pre>human_variable:HV04</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3303">
<!-- source-paragraph:V82-P3303 style=TableText -->
<pre>名称（name）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3304">
<!-- source-paragraph:V82-P3304 style=TableText -->
<pre>生成节点</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3305">
<!-- source-paragraph:V82-P3305 style=TableText -->
<pre>主张类型（claim_type）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3306">
<!-- source-paragraph:V82-P3306 style=TableText -->
<pre>H</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3307">
<!-- source-paragraph:V82-P3307 style=TableText -->
<pre>合同角色（contract_role）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3308">
<!-- source-paragraph:V82-P3308 style=TableText -->
<pre>human_variable_interface</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3309">
<!-- source-paragraph:V82-P3309 style=TableText -->
<pre>命题（proposition）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3310">
<!-- source-paragraph:V82-P3310 style=TableText -->
<pre>生成必须分流为生成条件GC、生成主体GS与生成事件GE，允许无可识别主体的涌现型生成。</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3311">
<!-- source-paragraph:V82-P3311 style=TableText -->
<pre>适用范围（scope）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3312">
<!-- source-paragraph:V82-P3312 style=TableText -->
<pre>人类结构中新行动、组织、制度或状态转移的形成</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3313">
<!-- source-paragraph:V82-P3313 style=TableText -->
<pre>暂停条件（pause_condition）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3314">
<!-- source-paragraph:V82-P3314 style=TableText -->
<pre>条件被人格化、事件被当作主体或主体资格不明</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3315 style=CardLabel -->
B. 正式依赖与推论边界

## V82-T080

<table data-source-table="V82-T080">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3316">
<!-- source-paragraph:V82-P3316 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3317">
<!-- source-paragraph:V82-P3317 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3318">
<!-- source-paragraph:V82-P3318 style=TableText -->
<pre>推论依赖（inferential_requires）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3319">
<!-- source-paragraph:V82-P3319 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3320">
<!-- source-paragraph:V82-P3320 style=TableText -->
<pre>协议依赖（protocol_requires）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3321">
<!-- source-paragraph:V82-P3321 style=TableText -->
<pre>1. EVIDENCE2. SOURCE</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3322">
<!-- source-paragraph:V82-P3322 style=TableText -->
<pre>限定／特化（specializes）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3323">
<!-- source-paragraph:V82-P3323 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3324">
<!-- source-paragraph:V82-P3324 style=TableText -->
<pre>适用对象引用（applies_to）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3325">
<!-- source-paragraph:V82-P3325 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3326">
<!-- source-paragraph:V82-P3326 style=TableText -->
<pre>条件支持路由（conditional_support_routes）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3327,V82-P3328,V82-P3329,V82-P3330,V82-P3331,V82-P3332,V82-P3333,V82-P3334,V82-P3335,V82-P3336,V82-P3337,V82-P3338,V82-P3339,V82-P3340">
<!-- source-paragraph:V82-P3327 style=TableText -->
<!-- source-paragraph:V82-P3328 style=TableText -->
<!-- source-paragraph:V82-P3329 style=TableText -->
<!-- source-paragraph:V82-P3330 style=TableText -->
<!-- source-paragraph:V82-P3331 style=TableText -->
<!-- source-paragraph:V82-P3332 style=TableText -->
<!-- source-paragraph:V82-P3333 style=TableText -->
<!-- source-paragraph:V82-P3334 style=TableText -->
<!-- source-paragraph:V82-P3335 style=TableText -->
<!-- source-paragraph:V82-P3336 style=TableText -->
<!-- source-paragraph:V82-P3337 style=TableText -->
<!-- source-paragraph:V82-P3338 style=TableText -->
<!-- source-paragraph:V82-P3339 style=TableText -->
<!-- source-paragraph:V82-P3340 style=TableText -->
<pre>1. route_id=HV04-R0-generation-typing；
claim_level=descriptive_classification；
when=GC、GS与GE的规定字段可分别登记，并保留无主体涌现与未识别主体状态。；
additional_inferential_requires=无（空集合）；
additional_protocol_requires=无（空集合）；
allowed_conclusion=分别登记候选生成条件、候选生成主体与候选生成事件，不将三者互相替代。；
result_ceiling=只到强类型分类；条件、主体或事件任一存在都不证明另两项或因果生成机制。
2. route_id=HV04-R1-generation-mechanism；
claim_level=mechanism_explanation；
when=预注册G2-instance识别GC、GS或无主体涌现通道对指定GE状态转移的超过阈值效应。；
additional_inferential_requires=G2-instance；
additional_protocol_requires=CAUSAL、E4；
allowed_conclusion=登记指定尺度、窗口和通道内的候选生成机制及其GC、GS、GE分型。；
result_ceiling=不得把条件人格化、把事件倒推为主体，或从生成事实推出正当性、责任与授权。</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3341">
<!-- source-paragraph:V82-P3341 style=TableText -->
<pre>允许推论（allowed_inference）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3342">
<!-- source-paragraph:V82-P3342 style=TableText -->
<pre>1. 条件性生成路径2. 有主体或无主体生成</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3343">
<!-- source-paragraph:V82-P3343 style=TableText -->
<pre>禁止跳跃（prohibited_leap）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3344,V82-P3345">
<!-- source-paragraph:V82-P3344 style=TableText -->
<!-- source-paragraph:V82-P3345 style=TableText -->
<pre>1. 技术或危机具有意图
2. 生成主体自动拥有持续授权</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3346 style=CardLabel -->
C. 九轴尺度与对象合同

## V82-T081

<table data-source-table="V82-T081">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3347">
<!-- source-paragraph:V82-P3347 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3348">
<!-- source-paragraph:V82-P3348 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3349">
<!-- source-paragraph:V82-P3349 style=TableText -->
<pre>九轴尺度画像（scale_profile）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3350">
<!-- source-paragraph:V82-P3350 style=TableText -->
<pre>SP=&lt;A,X,T,O,C,R,I,N,J&gt;；A=聚合层次：条件暴露、主体行动与生成事件单元，各自个案总体、分布及聚合规则；X=空间范围：生成现场、组织或平台边界、扩散区域与跨域环境；T=时间跨度：条件积累期、主体行动窗、事件时点与扩散时滞；O=组织层级：行动角色、生成团队、组织、制度至治理生态；C=因果层次：生成事件、主体—条件互动机制、中观生成结构、制度安排与系统条件；R=观察分辨率：原始条件行动事件、生成序列、个案、结果分布、转移指标与摘要，并登记压缩损失；I=影响范围：直接生成参与者、承接者、间接受影响者、二阶后果、跨域与代际影响；N=网络拓扑范围：条件传播、主体协作、事件扩散与涌现连接；J=管辖与授权范围：生成识别、启动改变、资源投入及扩散处置分别登记授权；GC、GS、GE分别登记尺度</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3351">
<!-- source-paragraph:V82-P3351 style=TableText -->
<pre>有效对象（effective_object）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3352">
<!-- source-paragraph:V82-P3352 style=TableText -->
<pre>形成可检测状态转移的条件、主体与事件组合</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3353">
<!-- source-paragraph:V82-P3353 style=TableText -->
<pre>跨尺度保持项（scale_invariants）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3354">
<!-- source-paragraph:V82-P3354 style=TableText -->
<pre>1. GC、GS、GE强类型分离</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3355">
<!-- source-paragraph:V82-P3355 style=TableText -->
<pre>升格必补项（required_scale_additions）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3356,V82-P3357,V82-P3358,V82-P3359">
<!-- source-paragraph:V82-P3356 style=TableText -->
<!-- source-paragraph:V82-P3357 style=TableText -->
<!-- source-paragraph:V82-P3358 style=TableText -->
<!-- source-paragraph:V82-P3359 style=TableText -->
<pre>1. 新单位与总体
2. 代表关系
3. 责任类型
4. 外部影响</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3360">
<!-- source-paragraph:V82-P3360 style=TableText -->
<pre>随尺度改变项（changing_semantics）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3361">
<!-- source-paragraph:V82-P3361 style=TableText -->
<pre>1. 生成主体、条件与事件可随尺度改变</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3362">
<!-- source-paragraph:V82-P3362 style=TableText -->
<pre>不适用对象（non_applicable_objects）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3363">
<!-- source-paragraph:V82-P3363 style=TableText -->
<pre>1. 没有新状态形成或生成主张的稳定描述</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3364">
<!-- source-paragraph:V82-P3364 style=TableText -->
<pre>禁止升格（forbidden_elevation）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3365">
<!-- source-paragraph:V82-P3365 style=TableText -->
<pre>1. 把条件或事件升格为有意图主体</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3366 style=CardLabel -->
D. 状态、证据与变量流

## V82-T082

<table data-source-table="V82-T082">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3367">
<!-- source-paragraph:V82-P3367 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3368">
<!-- source-paragraph:V82-P3368 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3369">
<!-- source-paragraph:V82-P3369 style=TableText -->
<pre>状态集合（state）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3370,V82-P3371,V82-P3372,V82-P3373,V82-P3374">
<!-- source-paragraph:V82-P3370 style=TableText -->
<!-- source-paragraph:V82-P3371 style=TableText -->
<!-- source-paragraph:V82-P3372 style=TableText -->
<!-- source-paragraph:V82-P3373 style=TableText -->
<!-- source-paragraph:V82-P3374 style=TableText -->
<pre>1. 潜在
2. 触发
3. 形成
4. 中断
5. 扩散</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3375">
<!-- source-paragraph:V82-P3375 style=TableText -->
<pre>可观测项（observables）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3376,V82-P3377,V82-P3378,V82-P3379">
<!-- source-paragraph:V82-P3376 style=TableText -->
<!-- source-paragraph:V82-P3377 style=TableText -->
<!-- source-paragraph:V82-P3378 style=TableText -->
<!-- source-paragraph:V82-P3379 style=TableText -->
<pre>1. 候选条件出现、改变或移除的时间记录
2. 生成主体的能力、授权、决策与实际行动
3. 生成事件前后预注册状态转移
4. 无主体涌现时局部互动与总体结果的桥接记录</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3380">
<!-- source-paragraph:V82-P3380 style=TableText -->
<pre>证据要求（evidence）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3381,V82-P3382,V82-P3383,V82-P3384">
<!-- source-paragraph:V82-P3381 style=TableText -->
<!-- source-paragraph:V82-P3382 style=TableText -->
<!-- source-paragraph:V82-P3383 style=TableText -->
<!-- source-paragraph:V82-P3384 style=TableText -->
<pre>1. 启动记录
2. 条件窗口
3. 主体行动
4. 无主体互动机制</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3385">
<!-- source-paragraph:V82-P3385 style=TableText -->
<pre>输入依赖与接口内容（input_dependencies）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3386">
<!-- source-paragraph:V82-P3386 style=TableText -->
<pre>1. 指向锚点2. 资源与制度条件3. 因果合同</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3387">
<!-- source-paragraph:V82-P3387 style=TableText -->
<pre>输出效应与变量流（output_effects）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3388">
<!-- source-paragraph:V82-P3388 style=TableText -->
<pre>1. 承接需求2. 状态转移3. 责任链起点</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3389">
<!-- source-paragraph:V82-P3389 style=TableText -->
<pre>时间窗与时滞（time_window_and_lag）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3390">
<!-- source-paragraph:V82-P3390 style=TableText -->
<pre>登记条件积累、触发事件与形成时滞</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3391">
<!-- source-paragraph:V82-P3391 style=TableText -->
<pre>不确定性（uncertainty）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3392">
<!-- source-paragraph:V82-P3392 style=TableText -->
<pre>记录共同生成、无主体涌现和不可识别主体</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3393">
<!-- source-paragraph:V82-P3393 style=TableText -->
<pre>局部排除区（local_exclusion_zone）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3394">
<!-- source-paragraph:V82-P3394 style=TableText -->
<pre>被遗漏的非正式启动者与受影响位置</pre>
</td>
</tr>
<tr>
<td data-source-cell="10,1" data-paragraphs="V82-P3395">
<!-- source-paragraph:V82-P3395 style=TableText -->
<pre>受影响位置（affected_positions）</pre>
</td>
<td data-source-cell="10,2" data-paragraphs="V82-P3396,V82-P3397,V82-P3398,V82-P3399">
<!-- source-paragraph:V82-P3396 style=TableText -->
<!-- source-paragraph:V82-P3397 style=TableText -->
<!-- source-paragraph:V82-P3398 style=TableText -->
<!-- source-paragraph:V82-P3399 style=TableText -->
<pre>1. 启动者
2. 承接者
3. 受益者
4. 受影响者</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3400 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

## V82-T083

<table data-source-table="V82-T083">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3401">
<!-- source-paragraph:V82-P3401 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3402">
<!-- source-paragraph:V82-P3402 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3403">
<!-- source-paragraph:V82-P3403 style=TableText -->
<pre>承接载体（carrier）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3404,V82-P3405,V82-P3406,V82-P3407">
<!-- source-paragraph:V82-P3404 style=TableText -->
<!-- source-paragraph:V82-P3405 style=TableText -->
<!-- source-paragraph:V82-P3406 style=TableText -->
<!-- source-paragraph:V82-P3407 style=TableText -->
<pre>1. 启动者
2. 程序
3. 技术设施
4. 关系网络</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3408">
<!-- source-paragraph:V82-P3408 style=TableText -->
<pre>责任主体（responsible_subject）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3409">
<!-- source-paragraph:V82-P3409 style=TableText -->
<pre>1. 实际行动者2. 决策者3. 授权者</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3410">
<!-- source-paragraph:V82-P3410 style=TableText -->
<pre>规范地位（normative_status）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3411">
<!-- source-paragraph:V82-P3411 style=TableText -->
<pre>生成事实不证明正当或责任完整</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3412">
<!-- source-paragraph:V82-P3412 style=TableText -->
<pre>判断上限（judgment_ceiling）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3413">
<!-- source-paragraph:V82-P3413 style=TableText -->
<pre>机制链完整时至解释级</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3414">
<!-- source-paragraph:V82-P3414 style=TableText -->
<pre>行动上限（action_ceiling）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3415">
<!-- source-paragraph:V82-P3415 style=TableText -->
<pre>本变量只生成GC、GS、GE候选分型、状态转移描述与补证需求，不授权启动、扩散或停止生成过程；任何现实调整须另过C12、运行时显式N前提、J授权与O程序</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3416">
<!-- source-paragraph:V82-P3416 style=TableText -->
<pre>反例（counterexamples）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3417,V82-P3418">
<!-- source-paragraph:V82-P3417 style=TableText -->
<!-- source-paragraph:V82-P3418 style=TableText -->
<pre>1. 技术条件被错误描述成具有目标的生成主体
2. 无统一发起者的涌现过程被强行归因给一个可见人物</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3419">
<!-- source-paragraph:V82-P3419 style=TableText -->
<pre>申诉（appeal）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3420">
<!-- source-paragraph:V82-P3420 style=TableText -->
<pre>依appeal_and_rollback_rule，被归为生成主体者可经安全可达、反报复通道挑战意图、角色与授权归因，并触发与原分型或决策链独立的复核</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3421">
<!-- source-paragraph:V82-P3421 style=TableText -->
<pre>回滚（rollback）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3422">
<!-- source-paragraph:V82-P3422 style=TableText -->
<pre>依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内纠正GC、GS、GE类型，实际移除错误意图或责任归因及其下游效力，保留版本与完成验证</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3423 style=SecH2 -->
## A.5　HV05 行动承接层（完整接口卡）

<!-- source-paragraph:V82-P3424 style=CardLabel -->
A. 身份、命题与适用范围

## V82-T084

<table data-source-table="V82-T084">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3425">
<!-- source-paragraph:V82-P3425 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3426">
<!-- source-paragraph:V82-P3426 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3427">
<!-- source-paragraph:V82-P3427 style=TableText -->
<pre>接口 ID（id）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3428">
<!-- source-paragraph:V82-P3428 style=TableText -->
<pre>HV05</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3429">
<!-- source-paragraph:V82-P3429 style=TableText -->
<pre>限定 ID（qualified_id）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3430">
<!-- source-paragraph:V82-P3430 style=TableText -->
<pre>human_variable:HV05</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3431">
<!-- source-paragraph:V82-P3431 style=TableText -->
<pre>名称（name）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3432">
<!-- source-paragraph:V82-P3432 style=TableText -->
<pre>行动承接层</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3433">
<!-- source-paragraph:V82-P3433 style=TableText -->
<pre>主张类型（claim_type）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3434">
<!-- source-paragraph:V82-P3434 style=TableText -->
<pre>H</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3435">
<!-- source-paragraph:V82-P3435 style=TableText -->
<pre>合同角色（contract_role）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3436">
<!-- source-paragraph:V82-P3436 style=TableText -->
<pre>human_variable_interface</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3437">
<!-- source-paragraph:V82-P3437 style=TableText -->
<pre>命题（proposition）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3438">
<!-- source-paragraph:V82-P3438 style=TableText -->
<pre>执行、传导、维护、记录、照护与修复的承接载体CV必须和责任主体RS、成本承担者、受益者及停止权分别登记。</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3439">
<!-- source-paragraph:V82-P3439 style=TableText -->
<pre>适用范围（scope）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3440">
<!-- source-paragraph:V82-P3440 style=TableText -->
<pre>需要持续行动、维护、照护或执行的人类结构</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3441">
<!-- source-paragraph:V82-P3441 style=TableText -->
<pre>暂停条件（pause_condition）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3442">
<!-- source-paragraph:V82-P3442 style=TableText -->
<pre>低权限执行者被默认归为主要责任人或承接能力被当作义务</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3443 style=CardLabel -->
B. 正式依赖与推论边界

## V82-T085

<table data-source-table="V82-T085">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3444">
<!-- source-paragraph:V82-P3444 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3445">
<!-- source-paragraph:V82-P3445 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3446">
<!-- source-paragraph:V82-P3446 style=TableText -->
<pre>推论依赖（inferential_requires）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3447">
<!-- source-paragraph:V82-P3447 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3448">
<!-- source-paragraph:V82-P3448 style=TableText -->
<pre>协议依赖（protocol_requires）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3449">
<!-- source-paragraph:V82-P3449 style=TableText -->
<pre>1. EVIDENCE2. SOURCE</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3450">
<!-- source-paragraph:V82-P3450 style=TableText -->
<pre>限定／特化（specializes）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3451">
<!-- source-paragraph:V82-P3451 style=TableText -->
<pre>1. H2</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3452">
<!-- source-paragraph:V82-P3452 style=TableText -->
<pre>适用对象引用（applies_to）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3453">
<!-- source-paragraph:V82-P3453 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3454">
<!-- source-paragraph:V82-P3454 style=TableText -->
<pre>条件支持路由（conditional_support_routes）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3455,V82-P3456,V82-P3457,V82-P3458,V82-P3459,V82-P3460,V82-P3461,V82-P3462,V82-P3463,V82-P3464,V82-P3465,V82-P3466,V82-P3467,V82-P3468,V82-P3469,V82-P3470,V82-P3471,V82-P3472,V82-P3473,V82-P3474,V82-P3475,V82-P3476,V82-P3477,V82-P3478,V82-P3479,V82-P3480,V82-P3481,V82-P3482">
<!-- source-paragraph:V82-P3455 style=TableText -->
<!-- source-paragraph:V82-P3456 style=TableText -->
<!-- source-paragraph:V82-P3457 style=TableText -->
<!-- source-paragraph:V82-P3458 style=TableText -->
<!-- source-paragraph:V82-P3459 style=TableText -->
<!-- source-paragraph:V82-P3460 style=TableText -->
<!-- source-paragraph:V82-P3461 style=TableText -->
<!-- source-paragraph:V82-P3462 style=TableText -->
<!-- source-paragraph:V82-P3463 style=TableText -->
<!-- source-paragraph:V82-P3464 style=TableText -->
<!-- source-paragraph:V82-P3465 style=TableText -->
<!-- source-paragraph:V82-P3466 style=TableText -->
<!-- source-paragraph:V82-P3467 style=TableText -->
<!-- source-paragraph:V82-P3468 style=TableText -->
<!-- source-paragraph:V82-P3469 style=TableText -->
<!-- source-paragraph:V82-P3470 style=TableText -->
<!-- source-paragraph:V82-P3471 style=TableText -->
<!-- source-paragraph:V82-P3472 style=TableText -->
<!-- source-paragraph:V82-P3473 style=TableText -->
<!-- source-paragraph:V82-P3474 style=TableText -->
<!-- source-paragraph:V82-P3475 style=TableText -->
<!-- source-paragraph:V82-P3476 style=TableText -->
<!-- source-paragraph:V82-P3477 style=TableText -->
<!-- source-paragraph:V82-P3478 style=TableText -->
<!-- source-paragraph:V82-P3479 style=TableText -->
<!-- source-paragraph:V82-P3480 style=TableText -->
<!-- source-paragraph:V82-P3481 style=TableText -->
<!-- source-paragraph:V82-P3482 style=TableText -->
<pre>1. route_id=HV05-R0-carrier-responsibility-split；
claim_level=descriptive_classification；
when=CV、同型成本承担者、受益者、停止权、RS、资源与容量可依H2分别登记。；
additional_inferential_requires=无（空集合）；
additional_protocol_requires=无（空集合）；
allowed_conclusion=登记当前承接载体、任务、成本、容量、停止权、责任类型与承接缺口。；
result_ceiling=只到当前分型与缺口描述；承接能力不成为义务，CV不成为RS。
2. route_id=HV05-R1-functional-carrier-effect；
claim_level=conditional_effect；
when=符合资格的G2-instance显示指定载体替换、中断、补给或减载对预选功能结果有超过阈值的通道效应。；
additional_inferential_requires=G2-instance；
additional_protocol_requires=CAUSAL、E4；
allowed_conclusion=登记指定载体在已测功能、容量、时延或损耗维度上的候选承接效应。；
result_ceiling=未测维度保持未知；功能效应不得直接生成责任、牺牲义务或资源重配授权。
3. route_id=HV05-R2-intertemporal-reproduction；
claim_level=intertemporal_explanation；
when=当前承接通道已有G2-instance支持，且G3-instance显示其历史变量对后续承接或再生产结果具有条件增量。；
additional_inferential_requires=G2-instance、G3-instance；
additional_protocol_requires=CAUSAL、E4；
allowed_conclusion=登记指定窗口与载体内的跨期承接或再生产候选。；
result_ceiling=不推出历史宿命、不可逆、责任归属或继续承担义务。
4. route_id=HV05-R3-historical-carrier-trace；
claim_level=descriptive_classification；
when=H5-instance对唯一预选的具体载体与持久判据取得supported。；
additional_inferential_requires=H5-instance；
additional_protocol_requires=E4；
allowed_conclusion=登记指定载体、留痕可观察量与窗口内的持久人类留痕，并向G3-instance提交预先定义的历史变量候选。；
result_ceiling=H5-instance不证明未来路径效应、跨期再生产、修复窗口、责任或行动；这些结论仍须各自的G3、推论与规范程序。</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3483">
<!-- source-paragraph:V82-P3483 style=TableText -->
<pre>允许推论（allowed_inference）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3484">
<!-- source-paragraph:V82-P3484 style=TableText -->
<pre>1. 承接缺口2. 任务资源错配3. 责任分流</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3485">
<!-- source-paragraph:V82-P3485 style=TableText -->
<pre>禁止跳跃（prohibited_leap）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3486,V82-P3487,V82-P3488">
<!-- source-paragraph:V82-P3486 style=TableText -->
<!-- source-paragraph:V82-P3487 style=TableText -->
<!-- source-paragraph:V82-P3488 style=TableText -->
<pre>1. 最可见者等于主要责任人
2. 能承担所以应承担
3. 非人载体承担责任</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3489 style=CardLabel -->
C. 九轴尺度与对象合同

## V82-T086

<table data-source-table="V82-T086">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3490">
<!-- source-paragraph:V82-P3490 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3491">
<!-- source-paragraph:V82-P3491 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3492">
<!-- source-paragraph:V82-P3492 style=TableText -->
<pre>九轴尺度画像（scale_profile）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3493">
<!-- source-paragraph:V82-P3493 style=TableText -->
<pre>SP=&lt;A,X,T,O,C,R,I,N,J&gt;；A=聚合层次：单项任务或承接事件、载体个案、承接总体、成本容量分布及聚合规则；X=空间范围：岗位现场、团队或组织边界、数字系统与跨域服务范围；T=时间跨度：任务周期、维护窗口、恢复时滞与责任有效期；O=组织层级：执行角色、团队、组织、制度至治理生态；C=因果层次：执行事件、任务—资源互动机制、中观承接结构、制度责任安排与系统条件；R=观察分辨率：原始任务日志、承接序列、载体个案、成本容量分布、绩效指标与摘要，并登记压缩损失；I=影响范围：直接承接者、服务依赖者、间接受益或成本位置、二阶外溢、跨域与代际影响；N=网络拓扑范围：承接依赖、替代路径、单点瓶颈与跨域服务网络；J=管辖与授权范围：任务分配、停止、资源调整、归责与补救分别登记授权；CV与RS分别登记尺度</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3494">
<!-- source-paragraph:V82-P3494 style=TableText -->
<pre>有效对象（effective_object）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3495">
<!-- source-paragraph:V82-P3495 style=TableText -->
<pre>实际执行、传导、维护、记录、照护或修复的人、岗位、程序、设施或制度</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3496">
<!-- source-paragraph:V82-P3496 style=TableText -->
<pre>跨尺度保持项（scale_invariants）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3497,V82-P3498,V82-P3499">
<!-- source-paragraph:V82-P3497 style=TableText -->
<!-- source-paragraph:V82-P3498 style=TableText -->
<!-- source-paragraph:V82-P3499 style=TableText -->
<pre>1. CV不等于RS
2. 成本与受益分别登记
3. 停止权</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3500">
<!-- source-paragraph:V82-P3500 style=TableText -->
<pre>升格必补项（required_scale_additions）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3501,V82-P3502,V82-P3503,V82-P3504">
<!-- source-paragraph:V82-P3501 style=TableText -->
<!-- source-paragraph:V82-P3502 style=TableText -->
<!-- source-paragraph:V82-P3503 style=TableText -->
<!-- source-paragraph:V82-P3504 style=TableText -->
<pre>1. 任务聚合
2. 代表和委托
3. 六类责任
4. 外部成本</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3505">
<!-- source-paragraph:V82-P3505 style=TableText -->
<pre>随尺度改变项（changing_semantics）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3506">
<!-- source-paragraph:V82-P3506 style=TableText -->
<pre>1. 承接载体和责任主体可随层级改变</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3507">
<!-- source-paragraph:V82-P3507 style=TableText -->
<pre>不适用对象（non_applicable_objects）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3508">
<!-- source-paragraph:V82-P3508 style=TableText -->
<pre>1. 无主体行动、责任或维护要求的非人过程</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3509">
<!-- source-paragraph:V82-P3509 style=TableText -->
<pre>禁止升格（forbidden_elevation）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3510">
<!-- source-paragraph:V82-P3510 style=TableText -->
<pre>1. 个体承接直接等于组织责任</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3511 style=CardLabel -->
D. 状态、证据与变量流

## V82-T087

<table data-source-table="V82-T087">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3512">
<!-- source-paragraph:V82-P3512 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3513">
<!-- source-paragraph:V82-P3513 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3514">
<!-- source-paragraph:V82-P3514 style=TableText -->
<pre>状态集合（state）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3515,V82-P3516,V82-P3517,V82-P3518,V82-P3519">
<!-- source-paragraph:V82-P3515 style=TableText -->
<!-- source-paragraph:V82-P3516 style=TableText -->
<!-- source-paragraph:V82-P3517 style=TableText -->
<!-- source-paragraph:V82-P3518 style=TableText -->
<!-- source-paragraph:V82-P3519 style=TableText -->
<pre>1. 充足
2. 脆弱
3. 过载
4. 断裂
5. 替代</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3520">
<!-- source-paragraph:V82-P3520 style=TableText -->
<pre>可观测项（observables）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3521,V82-P3522,V82-P3523,V82-P3524">
<!-- source-paragraph:V82-P3521 style=TableText -->
<!-- source-paragraph:V82-P3522 style=TableText -->
<!-- source-paragraph:V82-P3523 style=TableText -->
<!-- source-paragraph:V82-P3524 style=TableText -->
<pre>1. 任务实际执行、维护、记录与修复日志
2. 资源、容量、时间和成本流向
3. 停止权、替代安排与承接转移记录
4. 决策、授权、监督、受益与补救依据</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3525">
<!-- source-paragraph:V82-P3525 style=TableText -->
<pre>证据要求（evidence）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3526,V82-P3527,V82-P3528,V82-P3529">
<!-- source-paragraph:V82-P3526 style=TableText -->
<!-- source-paragraph:V82-P3527 style=TableText -->
<!-- source-paragraph:V82-P3528 style=TableText -->
<!-- source-paragraph:V82-P3529 style=TableText -->
<pre>1. 任务流
2. 工时与资源
3. 维护记录
4. 停止和拒绝记录</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3530">
<!-- source-paragraph:V82-P3530 style=TableText -->
<pre>输入依赖与接口内容（input_dependencies）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3531">
<!-- source-paragraph:V82-P3531 style=TableText -->
<pre>1. 生成需求2. 资源3. 授权4. 角色</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3532">
<!-- source-paragraph:V82-P3532 style=TableText -->
<pre>输出效应与变量流（output_effects）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3533">
<!-- source-paragraph:V82-P3533 style=TableText -->
<pre>1. 实现状态转移2. 成本分布3. 结构负荷</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3534">
<!-- source-paragraph:V82-P3534 style=TableText -->
<pre>时间窗与时滞（time_window_and_lag）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3535">
<!-- source-paragraph:V82-P3535 style=TableText -->
<pre>登记排班、维护周期、积压与恢复时滞</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3536">
<!-- source-paragraph:V82-P3536 style=TableText -->
<pre>不确定性（uncertainty）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3537">
<!-- source-paragraph:V82-P3537 style=TableText -->
<pre>记录隐性劳动、非正式照护和边界外成本</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3538">
<!-- source-paragraph:V82-P3538 style=TableText -->
<pre>局部排除区（local_exclusion_zone）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3539">
<!-- source-paragraph:V82-P3539 style=TableText -->
<pre>低权限、非正式与不可退出承接者</pre>
</td>
</tr>
<tr>
<td data-source-cell="10,1" data-paragraphs="V82-P3540">
<!-- source-paragraph:V82-P3540 style=TableText -->
<pre>受影响位置（affected_positions）</pre>
</td>
<td data-source-cell="10,2" data-paragraphs="V82-P3541,V82-P3542,V82-P3543,V82-P3544">
<!-- source-paragraph:V82-P3541 style=TableText -->
<!-- source-paragraph:V82-P3542 style=TableText -->
<!-- source-paragraph:V82-P3543 style=TableText -->
<!-- source-paragraph:V82-P3544 style=TableText -->
<pre>1. 承接者
2. 受益者
3. 被服务者
4. 替代者</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3545 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

## V82-T088

<table data-source-table="V82-T088">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3546">
<!-- source-paragraph:V82-P3546 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3547">
<!-- source-paragraph:V82-P3547 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3548">
<!-- source-paragraph:V82-P3548 style=TableText -->
<pre>承接载体（carrier）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3549,V82-P3550,V82-P3551,V82-P3552,V82-P3553">
<!-- source-paragraph:V82-P3549 style=TableText -->
<!-- source-paragraph:V82-P3550 style=TableText -->
<!-- source-paragraph:V82-P3551 style=TableText -->
<!-- source-paragraph:V82-P3552 style=TableText -->
<!-- source-paragraph:V82-P3553 style=TableText -->
<pre>1. 人员
2. 岗位
3. 程序
4. 设施
5. 制度</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3554">
<!-- source-paragraph:V82-P3554 style=TableText -->
<pre>责任主体（responsible_subject）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3555,V82-P3556,V82-P3557,V82-P3558,V82-P3559,V82-P3560">
<!-- source-paragraph:V82-P3555 style=TableText -->
<!-- source-paragraph:V82-P3556 style=TableText -->
<!-- source-paragraph:V82-P3557 style=TableText -->
<!-- source-paragraph:V82-P3558 style=TableText -->
<!-- source-paragraph:V82-P3559 style=TableText -->
<!-- source-paragraph:V82-P3560 style=TableText -->
<pre>1. 行为责任者
2. 决策责任者
3. 授权责任者
4. 监督责任者
5. 受益责任者
6. 补救责任者</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3561">
<!-- source-paragraph:V82-P3561 style=TableText -->
<pre>规范地位（normative_status）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3562">
<!-- source-paragraph:V82-P3562 style=TableText -->
<pre>承接事实不产生继续承担义务</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3563">
<!-- source-paragraph:V82-P3563 style=TableText -->
<pre>判断上限（judgment_ceiling）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3564">
<!-- source-paragraph:V82-P3564 style=TableText -->
<pre>资源与责任链完整时至诊断级</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3565">
<!-- source-paragraph:V82-P3565 style=TableText -->
<pre>行动上限（action_ceiling）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3566">
<!-- source-paragraph:V82-P3566 style=TableText -->
<pre>本变量只生成CV、RS、成本、容量、停止权与承接缺口描述，以及减载、补资源或重分配需求，不授权任务调整、资源配置、归责或保护；任何现实调整须另过C12、运行时显式N前提、J授权与O程序</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3567">
<!-- source-paragraph:V82-P3567 style=TableText -->
<pre>反例（counterexamples）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3568,V82-P3569">
<!-- source-paragraph:V82-P3568 style=TableText -->
<!-- source-paragraph:V82-P3569 style=TableText -->
<pre>1. 最可见的低权限执行者不是决策、授权或受益责任主体
2. 自动化设施承担传导任务但不能承担道德或法律责任</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3570">
<!-- source-paragraph:V82-P3570 style=TableText -->
<pre>申诉（appeal）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3571">
<!-- source-paragraph:V82-P3571 style=TableText -->
<pre>依appeal_and_rollback_rule，承接者可经安全可达、反报复通道挑战任务、资源、成本、停止权受限和归责，并触发与原任务分配或归责链独立的复核</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3572">
<!-- source-paragraph:V82-P3572 style=TableText -->
<pre>回滚（rollback）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3573">
<!-- source-paragraph:V82-P3573 style=TableText -->
<pre>依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销错误任务、资源或归责状态，实际恢复先前任务与记录状态并执行经授权补救，保留版本与完成验证</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3574 style=SecH2 -->
## A.6　HV06 动力—承接链（完整接口卡）

<!-- source-paragraph:V82-P3575 style=CardLabel -->
A. 身份、命题与适用范围

## V82-T089

<table data-source-table="V82-T089">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3576">
<!-- source-paragraph:V82-P3576 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3577">
<!-- source-paragraph:V82-P3577 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3578">
<!-- source-paragraph:V82-P3578 style=TableText -->
<pre>接口 ID（id）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3579">
<!-- source-paragraph:V82-P3579 style=TableText -->
<pre>HV06</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3580">
<!-- source-paragraph:V82-P3580 style=TableText -->
<pre>限定 ID（qualified_id）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3581">
<!-- source-paragraph:V82-P3581 style=TableText -->
<pre>human_variable:HV06</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3582">
<!-- source-paragraph:V82-P3582 style=TableText -->
<pre>名称（name）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3583">
<!-- source-paragraph:V82-P3583 style=TableText -->
<pre>动力—承接链</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3584">
<!-- source-paragraph:V82-P3584 style=TableText -->
<pre>主张类型（claim_type）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3585">
<!-- source-paragraph:V82-P3585 style=TableText -->
<pre>H</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3586">
<!-- source-paragraph:V82-P3586 style=TableText -->
<pre>合同角色（contract_role）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3587">
<!-- source-paragraph:V82-P3587 style=TableText -->
<pre>human_variable_interface</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3588">
<!-- source-paragraph:V82-P3588 style=TableText -->
<pre>命题（proposition）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3589">
<!-- source-paragraph:V82-P3589 style=TableText -->
<pre>从指向、生成到执行、维护与偿付的链条必须逐段登记通道、资源、成本、责任和时滞。</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3590">
<!-- source-paragraph:V82-P3590 style=TableText -->
<pre>适用范围（scope）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3591">
<!-- source-paragraph:V82-P3591 style=TableText -->
<pre>人类集体行动、项目、组织与制度运行</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3592">
<!-- source-paragraph:V82-P3592 style=TableText -->
<pre>暂停条件（pause_condition）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3593">
<!-- source-paragraph:V82-P3593 style=TableText -->
<pre>用热情、愿景或命令替代承接与偿付证据</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3594 style=CardLabel -->
B. 正式依赖与推论边界

## V82-T090

<table data-source-table="V82-T090">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3595">
<!-- source-paragraph:V82-P3595 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3596">
<!-- source-paragraph:V82-P3596 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3597">
<!-- source-paragraph:V82-P3597 style=TableText -->
<pre>推论依赖（inferential_requires）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3598">
<!-- source-paragraph:V82-P3598 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3599">
<!-- source-paragraph:V82-P3599 style=TableText -->
<pre>协议依赖（protocol_requires）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3600">
<!-- source-paragraph:V82-P3600 style=TableText -->
<pre>1. EVIDENCE2. SOURCE</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3601">
<!-- source-paragraph:V82-P3601 style=TableText -->
<pre>限定／特化（specializes）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3602">
<!-- source-paragraph:V82-P3602 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3603">
<!-- source-paragraph:V82-P3603 style=TableText -->
<pre>适用对象引用（applies_to）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3604">
<!-- source-paragraph:V82-P3604 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3605">
<!-- source-paragraph:V82-P3605 style=TableText -->
<pre>条件支持路由（conditional_support_routes）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3606,V82-P3607,V82-P3608,V82-P3609,V82-P3610,V82-P3611,V82-P3612,V82-P3613,V82-P3614,V82-P3615,V82-P3616,V82-P3617,V82-P3618,V82-P3619,V82-P3620,V82-P3621,V82-P3622,V82-P3623,V82-P3624,V82-P3625,V82-P3626">
<!-- source-paragraph:V82-P3606 style=TableText -->
<!-- source-paragraph:V82-P3607 style=TableText -->
<!-- source-paragraph:V82-P3608 style=TableText -->
<!-- source-paragraph:V82-P3609 style=TableText -->
<!-- source-paragraph:V82-P3610 style=TableText -->
<!-- source-paragraph:V82-P3611 style=TableText -->
<!-- source-paragraph:V82-P3612 style=TableText -->
<!-- source-paragraph:V82-P3613 style=TableText -->
<!-- source-paragraph:V82-P3614 style=TableText -->
<!-- source-paragraph:V82-P3615 style=TableText -->
<!-- source-paragraph:V82-P3616 style=TableText -->
<!-- source-paragraph:V82-P3617 style=TableText -->
<!-- source-paragraph:V82-P3618 style=TableText -->
<!-- source-paragraph:V82-P3619 style=TableText -->
<!-- source-paragraph:V82-P3620 style=TableText -->
<!-- source-paragraph:V82-P3621 style=TableText -->
<!-- source-paragraph:V82-P3622 style=TableText -->
<!-- source-paragraph:V82-P3623 style=TableText -->
<!-- source-paragraph:V82-P3624 style=TableText -->
<!-- source-paragraph:V82-P3625 style=TableText -->
<!-- source-paragraph:V82-P3626 style=TableText -->
<pre>1. route_id=HV06-R0-segment-map；
claim_level=descriptive_classification；
when=至少一个链段的输入、输出、时延、损耗、中断、资源、成本与边界可观察。；
additional_inferential_requires=无（空集合）；
additional_protocol_requires=无（空集合）；
allowed_conclusion=登记局部链段、缺失桥、时滞、损耗、中断点与成本位置。；
result_ceiling=不得由单一链段或动力语言宣称完整链条或有效通道。
2. route_id=HV06-R1-complete-chain-composition；
claim_level=descriptive_classification；
when=指向、生成与承接三个接口记录可在同一对象、尺度、窗口与量的映射中逐段连接。；
additional_inferential_requires=human_variable:HV03、human_variable:HV04、human_variable:HV05；
additional_protocol_requires=无（空集合）；
allowed_conclusion=登记完整候选动力—承接链及逐段证据覆盖。；
result_ceiling=只到候选链条组成；接口记录齐全不等于各链段具有因果效力。
3. route_id=HV06-R2-effective-channel；
claim_level=mechanism_explanation；
when=完整候选链已组成，且符合资格的G2-instance逐段识别指定通道对目标转移的效应。；
additional_inferential_requires=human_variable:HV03、human_variable:HV04、human_variable:HV05、G2-instance；
additional_protocol_requires=CAUSAL、E4；
allowed_conclusion=登记已检验链段和窗口内的有效动力—承接通道、损耗与中断机制。；
result_ceiling=不得从一次贯通推出跨期再生产、责任、正当性或行动授权。</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3627">
<!-- source-paragraph:V82-P3627 style=TableText -->
<pre>允许推论（allowed_inference）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3628">
<!-- source-paragraph:V82-P3628 style=TableText -->
<pre>1. 链条瓶颈2. 动力与承接脱节3. 隐性偿付</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3629">
<!-- source-paragraph:V82-P3629 style=TableText -->
<pre>禁止跳跃（prohibited_leap）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3630,V82-P3631,V82-P3632">
<!-- source-paragraph:V82-P3630 style=TableText -->
<!-- source-paragraph:V82-P3631 style=TableText -->
<!-- source-paragraph:V82-P3632 style=TableText -->
<pre>1. 动力强等于可持续
2. 失败归因意愿不足
3. 承接者应自行补洞</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3633 style=CardLabel -->
C. 九轴尺度与对象合同

## V82-T091

<table data-source-table="V82-T091">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3634">
<!-- source-paragraph:V82-P3634 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3635">
<!-- source-paragraph:V82-P3635 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3636">
<!-- source-paragraph:V82-P3636 style=TableText -->
<pre>九轴尺度画像（scale_profile）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3637">
<!-- source-paragraph:V82-P3637 style=TableText -->
<pre>SP=&lt;A,X,T,O,C,R,I,N,J&gt;；A=聚合层次：单个链节事件、链条个案、同类链总体、输入输出分布及聚合规则；X=空间范围：行动现场、项目或组织边界、数字协作空间与跨域外溢；T=时间跨度：启动、维持、中断、恢复窗口及跨期周期；O=组织层级：发起角色、执行团队、组织、制度至治理生态；C=因果层次：链节事件、动力—资源—任务互动机制、中观承接链、制度安排与系统条件；R=观察分辨率：原始任务资源记录、链节序列、链条个案、损耗分布、绩效指标与摘要，并登记压缩损失；I=影响范围：直接发起与承接位置、间接受益或成本位置、二阶外溢、跨域与代际影响；N=网络拓扑范围：依赖链、替代路径、瓶颈、反馈连接与跨域桥接；J=管辖与授权范围：目标采用、任务分配、资源投入、停止与试验分别登记授权；逐段标明跨轴位置</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3638">
<!-- source-paragraph:V82-P3638 style=TableText -->
<pre>有效对象（effective_object）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3639">
<!-- source-paragraph:V82-P3639 style=TableText -->
<pre>把指向和生成转为持续行动的可追踪链条</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3640">
<!-- source-paragraph:V82-P3640 style=TableText -->
<pre>跨尺度保持项（scale_invariants）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3641">
<!-- source-paragraph:V82-P3641 style=TableText -->
<pre>1. 指向、生成、承接、资源、成本和责任链</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3642">
<!-- source-paragraph:V82-P3642 style=TableText -->
<pre>升格必补项（required_scale_additions）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3643,V82-P3644,V82-P3645,V82-P3646">
<!-- source-paragraph:V82-P3643 style=TableText -->
<!-- source-paragraph:V82-P3644 style=TableText -->
<!-- source-paragraph:V82-P3645 style=TableText -->
<!-- source-paragraph:V82-P3646 style=TableText -->
<pre>1. 跨层桥接
2. 聚合损失
3. 责任继承
4. 保护底板</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3647">
<!-- source-paragraph:V82-P3647 style=TableText -->
<pre>随尺度改变项（changing_semantics）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3648">
<!-- source-paragraph:V82-P3648 style=TableText -->
<pre>1. 节点、通道和瓶颈可随组织尺度改变</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3649">
<!-- source-paragraph:V82-P3649 style=TableText -->
<pre>不适用对象（non_applicable_objects）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3650">
<!-- source-paragraph:V82-P3650 style=TableText -->
<pre>1. 无意向动力与人类承接的非人过程</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3651">
<!-- source-paragraph:V82-P3651 style=TableText -->
<pre>禁止升格（forbidden_elevation）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3652">
<!-- source-paragraph:V82-P3652 style=TableText -->
<pre>1. 局部动力或单一节点直接代表完整链条</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3653 style=CardLabel -->
D. 状态、证据与变量流

## V82-T092

<table data-source-table="V82-T092">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3654">
<!-- source-paragraph:V82-P3654 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3655">
<!-- source-paragraph:V82-P3655 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3656">
<!-- source-paragraph:V82-P3656 style=TableText -->
<pre>状态集合（state）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3657,V82-P3658,V82-P3659,V82-P3660,V82-P3661">
<!-- source-paragraph:V82-P3657 style=TableText -->
<!-- source-paragraph:V82-P3658 style=TableText -->
<!-- source-paragraph:V82-P3659 style=TableText -->
<!-- source-paragraph:V82-P3660 style=TableText -->
<!-- source-paragraph:V82-P3661 style=TableText -->
<pre>1. 贯通
2. 迟滞
3. 过载
4. 断裂
5. 替代</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3662">
<!-- source-paragraph:V82-P3662 style=TableText -->
<pre>可观测项（observables）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3663,V82-P3664,V82-P3665,V82-P3666">
<!-- source-paragraph:V82-P3663 style=TableText -->
<!-- source-paragraph:V82-P3664 style=TableText -->
<!-- source-paragraph:V82-P3665 style=TableText -->
<!-- source-paragraph:V82-P3666 style=TableText -->
<pre>1. 锚点转化为任务、预算、规则或排程的记录
2. 每段输入输出、时延、损耗与中断点
3. 承接者容量、停止与替代路径变化
4. 链条输出对目标结果的实际贡献</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3667">
<!-- source-paragraph:V82-P3667 style=TableText -->
<pre>证据要求（evidence）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3668,V82-P3669,V82-P3670,V82-P3671">
<!-- source-paragraph:V82-P3668 style=TableText -->
<!-- source-paragraph:V82-P3669 style=TableText -->
<!-- source-paragraph:V82-P3670 style=TableText -->
<!-- source-paragraph:V82-P3671 style=TableText -->
<pre>1. 资源流
2. 任务与维护记录
3. 偿付与成本
4. 时滞</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3672">
<!-- source-paragraph:V82-P3672 style=TableText -->
<pre>输入依赖与接口内容（input_dependencies）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3673">
<!-- source-paragraph:V82-P3673 style=TableText -->
<pre>1. 指向锚点2. 生成节点3. 承接层</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3674">
<!-- source-paragraph:V82-P3674 style=TableText -->
<pre>输出效应与变量流（output_effects）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3675">
<!-- source-paragraph:V82-P3675 style=TableText -->
<pre>1. 行动结果2. 负荷3. 反馈与演化痕迹</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3676">
<!-- source-paragraph:V82-P3676 style=TableText -->
<pre>时间窗与时滞（time_window_and_lag）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3677">
<!-- source-paragraph:V82-P3677 style=TableText -->
<pre>逐段登记启动、传导、维护和偿付时滞</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3678">
<!-- source-paragraph:V82-P3678 style=TableText -->
<pre>不确定性（uncertainty）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3679">
<!-- source-paragraph:V82-P3679 style=TableText -->
<pre>记录断点、替代通道与边界外偿付</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3680">
<!-- source-paragraph:V82-P3680 style=TableText -->
<pre>局部排除区（local_exclusion_zone）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3681">
<!-- source-paragraph:V82-P3681 style=TableText -->
<pre>非正式、低可见和跨组织承接位置</pre>
</td>
</tr>
<tr>
<td data-source-cell="10,1" data-paragraphs="V82-P3682">
<!-- source-paragraph:V82-P3682 style=TableText -->
<pre>受影响位置（affected_positions）</pre>
</td>
<td data-source-cell="10,2" data-paragraphs="V82-P3683,V82-P3684,V82-P3685,V82-P3686">
<!-- source-paragraph:V82-P3683 style=TableText -->
<!-- source-paragraph:V82-P3684 style=TableText -->
<!-- source-paragraph:V82-P3685 style=TableText -->
<!-- source-paragraph:V82-P3686 style=TableText -->
<pre>1. 发起者
2. 承接者
3. 受益者
4. 成本承担者</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3687 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

## V82-T093

<table data-source-table="V82-T093">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3688">
<!-- source-paragraph:V82-P3688 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3689">
<!-- source-paragraph:V82-P3689 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3690">
<!-- source-paragraph:V82-P3690 style=TableText -->
<pre>承接载体（carrier）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3691,V82-P3692,V82-P3693,V82-P3694">
<!-- source-paragraph:V82-P3691 style=TableText -->
<!-- source-paragraph:V82-P3692 style=TableText -->
<!-- source-paragraph:V82-P3693 style=TableText -->
<!-- source-paragraph:V82-P3694 style=TableText -->
<pre>1. 人员与岗位
2. 程序
3. 预算
4. 基础设施</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3695">
<!-- source-paragraph:V82-P3695 style=TableText -->
<pre>责任主体（responsible_subject）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3696">
<!-- source-paragraph:V82-P3696 style=TableText -->
<pre>1. 各节点行为、决策、授权、监督与补救责任者</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3697">
<!-- source-paragraph:V82-P3697 style=TableText -->
<pre>规范地位（normative_status）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3698">
<!-- source-paragraph:V82-P3698 style=TableText -->
<pre>链条有效不证明目标正当</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3699">
<!-- source-paragraph:V82-P3699 style=TableText -->
<pre>判断上限（judgment_ceiling）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3700">
<!-- source-paragraph:V82-P3700 style=TableText -->
<pre>全链证据充分时至解释或诊断级</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3701">
<!-- source-paragraph:V82-P3701 style=TableText -->
<pre>行动上限（action_ceiling）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3702">
<!-- source-paragraph:V82-P3702 style=TableText -->
<pre>本变量只生成链条连通、时滞、损耗、中断、成本与承接需求描述，不授权减载、资源调整或试验；任何现实调整须另过C12、运行时显式N前提、J授权与O程序</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3703">
<!-- source-paragraph:V82-P3703 style=TableText -->
<pre>反例（counterexamples）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3704,V82-P3705">
<!-- source-paragraph:V82-P3704 style=TableText -->
<!-- source-paragraph:V82-P3705 style=TableText -->
<pre>1. 强烈愿景和集中动员没有持续资源、维护或偿付
2. 表面贯通的链条把关键成本转移给边界外承接者</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3706">
<!-- source-paragraph:V82-P3706 style=TableText -->
<pre>申诉（appeal）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3707">
<!-- source-paragraph:V82-P3707 style=TableText -->
<pre>依appeal_and_rollback_rule，链上承接或受影响位置可经安全可达、反报复通道挑战资源、成本与链条归因，并触发与原链条判断或决策链独立的复核</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3708">
<!-- source-paragraph:V82-P3708 style=TableText -->
<pre>回滚（rollback）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3709">
<!-- source-paragraph:V82-P3709 style=TableText -->
<pre>依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销整体链条归因及其下游效力、恢复为节点级描述与未决状态，保留版本与完成验证</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3710 style=SecH2 -->
## A.7　HV07 反馈写回（完整接口卡）

<!-- source-paragraph:V82-P3711 style=CardLabel -->
A. 身份、命题与适用范围

## V82-T094

<table data-source-table="V82-T094">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3712">
<!-- source-paragraph:V82-P3712 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3713">
<!-- source-paragraph:V82-P3713 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3714">
<!-- source-paragraph:V82-P3714 style=TableText -->
<pre>接口 ID（id）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3715">
<!-- source-paragraph:V82-P3715 style=TableText -->
<pre>HV07</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3716">
<!-- source-paragraph:V82-P3716 style=TableText -->
<pre>限定 ID（qualified_id）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3717">
<!-- source-paragraph:V82-P3717 style=TableText -->
<pre>human_variable:HV07</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3718">
<!-- source-paragraph:V82-P3718 style=TableText -->
<pre>名称（name）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3719">
<!-- source-paragraph:V82-P3719 style=TableText -->
<pre>反馈写回</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3720">
<!-- source-paragraph:V82-P3720 style=TableText -->
<pre>主张类型（claim_type）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3721">
<!-- source-paragraph:V82-P3721 style=TableText -->
<pre>H</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3722">
<!-- source-paragraph:V82-P3722 style=TableText -->
<pre>合同角色（contract_role）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3723">
<!-- source-paragraph:V82-P3723 style=TableText -->
<pre>human_variable_interface</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3724">
<!-- source-paragraph:V82-P3724 style=TableText -->
<pre>命题（proposition）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3725">
<!-- source-paragraph:V82-P3725 style=TableText -->
<pre>申诉、审计和反馈只有改变记录、规则、资源、角色、责任、记忆或停止条件时才构成人类制度写回。</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3726">
<!-- source-paragraph:V82-P3726 style=TableText -->
<pre>适用范围（scope）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3727">
<!-- source-paragraph:V82-P3727 style=TableText -->
<pre>具有反馈、申诉、审计或治理程序的人类结构</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3728">
<!-- source-paragraph:V82-P3728 style=TableText -->
<pre>暂停条件（pause_condition）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3729">
<!-- source-paragraph:V82-P3729 style=TableText -->
<pre>只有接收回执、表态或发布而无状态更新</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3730 style=CardLabel -->
B. 正式依赖与推论边界

## V82-T095

<table data-source-table="V82-T095">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3731">
<!-- source-paragraph:V82-P3731 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3732">
<!-- source-paragraph:V82-P3732 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3733">
<!-- source-paragraph:V82-P3733 style=TableText -->
<pre>推论依赖（inferential_requires）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3734">
<!-- source-paragraph:V82-P3734 style=TableText -->
<pre>1. D2</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3735">
<!-- source-paragraph:V82-P3735 style=TableText -->
<pre>协议依赖（protocol_requires）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3736">
<!-- source-paragraph:V82-P3736 style=TableText -->
<pre>1. EVIDENCE2. SOURCE</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3737">
<!-- source-paragraph:V82-P3737 style=TableText -->
<pre>限定／特化（specializes）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3738">
<!-- source-paragraph:V82-P3738 style=TableText -->
<pre>1. H3</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3739">
<!-- source-paragraph:V82-P3739 style=TableText -->
<pre>适用对象引用（applies_to）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3740">
<!-- source-paragraph:V82-P3740 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3741">
<!-- source-paragraph:V82-P3741 style=TableText -->
<pre>条件支持路由（conditional_support_routes）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3742,V82-P3743,V82-P3744,V82-P3745,V82-P3746,V82-P3747,V82-P3748,V82-P3749,V82-P3750,V82-P3751,V82-P3752,V82-P3753,V82-P3754,V82-P3755,V82-P3756,V82-P3757,V82-P3758,V82-P3759,V82-P3760,V82-P3761,V82-P3762">
<!-- source-paragraph:V82-P3742 style=TableText -->
<!-- source-paragraph:V82-P3743 style=TableText -->
<!-- source-paragraph:V82-P3744 style=TableText -->
<!-- source-paragraph:V82-P3745 style=TableText -->
<!-- source-paragraph:V82-P3746 style=TableText -->
<!-- source-paragraph:V82-P3747 style=TableText -->
<!-- source-paragraph:V82-P3748 style=TableText -->
<!-- source-paragraph:V82-P3749 style=TableText -->
<!-- source-paragraph:V82-P3750 style=TableText -->
<!-- source-paragraph:V82-P3751 style=TableText -->
<!-- source-paragraph:V82-P3752 style=TableText -->
<!-- source-paragraph:V82-P3753 style=TableText -->
<!-- source-paragraph:V82-P3754 style=TableText -->
<!-- source-paragraph:V82-P3755 style=TableText -->
<!-- source-paragraph:V82-P3756 style=TableText -->
<!-- source-paragraph:V82-P3757 style=TableText -->
<!-- source-paragraph:V82-P3758 style=TableText -->
<!-- source-paragraph:V82-P3759 style=TableText -->
<!-- source-paragraph:V82-P3760 style=TableText -->
<!-- source-paragraph:V82-P3761 style=TableText -->
<!-- source-paragraph:V82-P3762 style=TableText -->
<pre>1. route_id=HV07-R0-writeback-classification；
claim_level=descriptive_classification；
when=输入通道、回执、字段前后版本、执行记录、生效时间、持续时间及停止或回滚状态可分别检查。；
additional_inferential_requires=无（空集合）；
additional_protocol_requires=无（空集合）；
allowed_conclusion=区分未提交、已提交、已受理、字段改变、已执行、持续或失效的写回状态。；
result_ceiling=只有字段改变且实际执行才称制度性写回；一次写回不称学习。
2. route_id=HV07-R1-causal-feedback；
claim_level=mechanism_explanation；
when=符合资格的G2-instance显示制度返回通道相对无返回或阻断条件改变预选后续状态或转移。；
additional_inferential_requires=G2-instance；
additional_protocol_requires=CAUSAL、E4；
allowed_conclusion=登记指定字段、通道和窗口内的有效反馈与制度写回效应。；
result_ceiling=不得从反馈存在推出学习、长期修复、正当性或授权扩大。
3. route_id=HV07-R2-feedback-mediated-learning；
claim_level=intertemporal_explanation；
when=有效反馈已有G2-instance支持，且G3-instance显示可保留更新在重复轮次对预定任务提供历史条件增量。；
additional_inferential_requires=G2-instance、G3-instance；
additional_protocol_requires=CAUSAL、E4；
allowed_conclusion=登记限定任务、轮次和窗口内的反馈介导学习候选。；
result_ceiling=不得称整体制度已经学习、修复完成或价值方向正确。</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3763">
<!-- source-paragraph:V82-P3763 style=TableText -->
<pre>允许推论（allowed_inference）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3764">
<!-- source-paragraph:V82-P3764 style=TableText -->
<pre>1. 有效写回、阻塞写回与表面反馈</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3765">
<!-- source-paragraph:V82-P3765 style=TableText -->
<pre>禁止跳跃（prohibited_leap）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3766,V82-P3767,V82-P3768">
<!-- source-paragraph:V82-P3766 style=TableText -->
<!-- source-paragraph:V82-P3767 style=TableText -->
<!-- source-paragraph:V82-P3768 style=TableText -->
<pre>1. 有渠道即会学习
2. 一次更新即长期修复
3. 沉默即同意</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3769 style=CardLabel -->
C. 九轴尺度与对象合同

## V82-T096

<table data-source-table="V82-T096">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3770">
<!-- source-paragraph:V82-P3770 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3771">
<!-- source-paragraph:V82-P3771 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3772">
<!-- source-paragraph:V82-P3772 style=TableText -->
<pre>九轴尺度画像（scale_profile）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3773">
<!-- source-paragraph:V82-P3773 style=TableText -->
<pre>SP=&lt;A,X,T,O,C,R,I,N,J&gt;；A=聚合层次：单次反馈或申诉、写回个案、反馈总体、受理执行分布及聚合规则；X=空间范围：提交渠道、组织或平台边界、制度辖区与跨域申诉范围；T=时间跨度：提交、受理、字段变化、执行、持续与复核时滞；O=组织层级：反馈角色、受理团队、组织、制度至治理生态；C=因果层次：反馈事件、写回互动机制、中观程序结构、制度规则与系统条件；R=观察分辨率：原始反馈、处理序列、写回个案、结果分布、时效指标与摘要，并登记压缩损失；I=影响范围：直接申诉人与承接者、间接受影响者、二阶制度后果、跨域与代际影响；N=网络拓扑范围：反馈通道、受理节点、复核路径、阻塞点与跨层连接；J=管辖与授权范围：受理、字段修改、执行、停止、回滚与补救分别登记授权；登记跨层路径</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3774">
<!-- source-paragraph:V82-P3774 style=TableText -->
<pre>有效对象（effective_object）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3775">
<!-- source-paragraph:V82-P3775 style=TableText -->
<pre>改变后续制度状态或转移的返回通道</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3776">
<!-- source-paragraph:V82-P3776 style=TableText -->
<pre>跨尺度保持项（scale_invariants）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3777">
<!-- source-paragraph:V82-P3777 style=TableText -->
<pre>1. 反馈来源、通道、写回字段和后续变化</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3778">
<!-- source-paragraph:V82-P3778 style=TableText -->
<pre>升格必补项（required_scale_additions）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3779,V82-P3780,V82-P3781,V82-P3782">
<!-- source-paragraph:V82-P3779 style=TableText -->
<!-- source-paragraph:V82-P3780 style=TableText -->
<!-- source-paragraph:V82-P3781 style=TableText -->
<!-- source-paragraph:V82-P3782 style=TableText -->
<pre>1. 反馈代表性
2. 跨层写回路径
3. 聚合损失
4. 外部复核</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3783">
<!-- source-paragraph:V82-P3783 style=TableText -->
<pre>随尺度改变项（changing_semantics）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3784">
<!-- source-paragraph:V82-P3784 style=TableText -->
<pre>1. 写回载体、时滞和责任主体可改变</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3785">
<!-- source-paragraph:V82-P3785 style=TableText -->
<pre>不适用对象（non_applicable_objects）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3786">
<!-- source-paragraph:V82-P3786 style=TableText -->
<pre>1. 无记录、规则、资源、角色或停止条件的过程</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3787">
<!-- source-paragraph:V82-P3787 style=TableText -->
<pre>禁止升格（forbidden_elevation）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3788">
<!-- source-paragraph:V82-P3788 style=TableText -->
<pre>1. 个案反馈直接代表总体意见</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3789 style=CardLabel -->
D. 状态、证据与变量流

## V82-T097

<table data-source-table="V82-T097">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3790">
<!-- source-paragraph:V82-P3790 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3791">
<!-- source-paragraph:V82-P3791 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3792">
<!-- source-paragraph:V82-P3792 style=TableText -->
<pre>状态集合（state）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3793,V82-P3794,V82-P3795,V82-P3796,V82-P3797">
<!-- source-paragraph:V82-P3793 style=TableText -->
<!-- source-paragraph:V82-P3794 style=TableText -->
<!-- source-paragraph:V82-P3795 style=TableText -->
<!-- source-paragraph:V82-P3796 style=TableText -->
<!-- source-paragraph:V82-P3797 style=TableText -->
<pre>1. 到达
2. 受理
3. 写回
4. 阻塞
5. 失真</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3798">
<!-- source-paragraph:V82-P3798 style=TableText -->
<pre>可观测项（observables）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3799,V82-P3800,V82-P3801,V82-P3802">
<!-- source-paragraph:V82-P3799 style=TableText -->
<!-- source-paragraph:V82-P3800 style=TableText -->
<!-- source-paragraph:V82-P3801 style=TableText -->
<!-- source-paragraph:V82-P3802 style=TableText -->
<pre>1. 反馈或申诉的提交与受理凭证
2. 记录、规则、资源、角色、责任或停止条件的版本差异
3. 变更的执行记录、生效时间与持续时间
4. 复核、撤销、补救及后续状态变化</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3803">
<!-- source-paragraph:V82-P3803 style=TableText -->
<pre>证据要求（evidence）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3804,V82-P3805,V82-P3806,V82-P3807">
<!-- source-paragraph:V82-P3804 style=TableText -->
<!-- source-paragraph:V82-P3805 style=TableText -->
<!-- source-paragraph:V82-P3806 style=TableText -->
<!-- source-paragraph:V82-P3807 style=TableText -->
<pre>1. 反馈原文
2. 受理轨迹
3. 字段版本
4. 后续规则或资源变化</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3808">
<!-- source-paragraph:V82-P3808 style=TableText -->
<pre>输入依赖与接口内容（input_dependencies）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3809,V82-P3810,V82-P3811,V82-P3812">
<!-- source-paragraph:V82-P3809 style=TableText -->
<!-- source-paragraph:V82-P3810 style=TableText -->
<!-- source-paragraph:V82-P3811 style=TableText -->
<!-- source-paragraph:V82-P3812 style=TableText -->
<pre>1. 反馈来源
2. 安全通道
3. 责任人
4. 复核程序</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3813">
<!-- source-paragraph:V82-P3813 style=TableText -->
<pre>输出效应与变量流（output_effects）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3814">
<!-- source-paragraph:V82-P3814 style=TableText -->
<pre>1. 记录、规则、资源、角色、责任、记忆或停止条件更新</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3815">
<!-- source-paragraph:V82-P3815 style=TableText -->
<pre>时间窗与时滞（time_window_and_lag）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3816">
<!-- source-paragraph:V82-P3816 style=TableText -->
<pre>登记提交、受理、决定、执行和复审时限</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3817">
<!-- source-paragraph:V82-P3817 style=TableText -->
<pre>不确定性（uncertainty）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3818">
<!-- source-paragraph:V82-P3818 style=TableText -->
<pre>记录未达反馈、保护性匿名与不可见处理</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3819">
<!-- source-paragraph:V82-P3819 style=TableText -->
<pre>局部排除区（local_exclusion_zone）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3820">
<!-- source-paragraph:V82-P3820 style=TableText -->
<pre>无法安全提交、受反报复威胁或无数字接入的位置</pre>
</td>
</tr>
<tr>
<td data-source-cell="10,1" data-paragraphs="V82-P3821">
<!-- source-paragraph:V82-P3821 style=TableText -->
<pre>受影响位置（affected_positions）</pre>
</td>
<td data-source-cell="10,2" data-paragraphs="V82-P3822,V82-P3823,V82-P3824,V82-P3825">
<!-- source-paragraph:V82-P3822 style=TableText -->
<!-- source-paragraph:V82-P3823 style=TableText -->
<!-- source-paragraph:V82-P3824 style=TableText -->
<!-- source-paragraph:V82-P3825 style=TableText -->
<pre>1. 提交者
2. 被评价者
3. 执行者
4. 制度受益者</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3826 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

## V82-T098

<table data-source-table="V82-T098">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3827">
<!-- source-paragraph:V82-P3827 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3828">
<!-- source-paragraph:V82-P3828 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3829">
<!-- source-paragraph:V82-P3829 style=TableText -->
<pre>承接载体（carrier）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3830,V82-P3831,V82-P3832,V82-P3833,V82-P3834">
<!-- source-paragraph:V82-P3830 style=TableText -->
<!-- source-paragraph:V82-P3831 style=TableText -->
<!-- source-paragraph:V82-P3832 style=TableText -->
<!-- source-paragraph:V82-P3833 style=TableText -->
<!-- source-paragraph:V82-P3834 style=TableText -->
<pre>1. 申诉系统
2. 审计程序
3. 会议记录
4. 规则库
5. 责任链</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3835">
<!-- source-paragraph:V82-P3835 style=TableText -->
<pre>责任主体（responsible_subject）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3836,V82-P3837,V82-P3838,V82-P3839">
<!-- source-paragraph:V82-P3836 style=TableText -->
<!-- source-paragraph:V82-P3837 style=TableText -->
<!-- source-paragraph:V82-P3838 style=TableText -->
<!-- source-paragraph:V82-P3839 style=TableText -->
<pre>1. 受理者
2. 决策者
3. 写回执行者
4. 监督者</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3840">
<!-- source-paragraph:V82-P3840 style=TableText -->
<pre>规范地位（normative_status）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3841">
<!-- source-paragraph:V82-P3841 style=TableText -->
<pre>反馈有效性与反馈内容正当性分别判断</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3842">
<!-- source-paragraph:V82-P3842 style=TableText -->
<pre>判断上限（judgment_ceiling）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3843">
<!-- source-paragraph:V82-P3843 style=TableText -->
<pre>确认写回字段和后续变化时至解释级</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3844">
<!-- source-paragraph:V82-P3844 style=TableText -->
<pre>行动上限（action_ceiling）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3845">
<!-- source-paragraph:V82-P3845 style=TableText -->
<pre>本变量只生成受理、字段变化、执行、持续时间与写回缺口描述，以及复核或程序修复需求，不授权改写记录规则、执行修复或关闭申诉；任何现实调整须另过C12、运行时显式N前提、J授权与O程序</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3846">
<!-- source-paragraph:V82-P3846 style=TableText -->
<pre>反例（counterexamples）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3847,V82-P3848">
<!-- source-paragraph:V82-P3847 style=TableText -->
<!-- source-paragraph:V82-P3848 style=TableText -->
<pre>1. 申诉获得接收回执但记录、规则、资源和停止条件均未改变
2. 审计报告被发布却没有责任人、时限或后续状态更新</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3849">
<!-- source-paragraph:V82-P3849 style=TableText -->
<pre>申诉（appeal）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3850">
<!-- source-paragraph:V82-P3850 style=TableText -->
<pre>依appeal_and_rollback_rule，反馈提交者可经安全可达、反报复通道要求状态、时限、责任人与写回结果，并触发与原受理、写回或决策链独立的复核</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3851">
<!-- source-paragraph:V82-P3851 style=TableText -->
<pre>回滚（rollback）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3852">
<!-- source-paragraph:V82-P3852 style=TableText -->
<pre>依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销错误更新，实际恢复先前记录、规则、资源、角色或停止条件状态，保留版本与完成验证</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3853 style=SecH2 -->
## A.8　HV08 条件势场（完整接口卡）

<!-- source-paragraph:V82-P3854 style=CardLabel -->
A. 身份、命题与适用范围

## V82-T099

<table data-source-table="V82-T099">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3855">
<!-- source-paragraph:V82-P3855 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3856">
<!-- source-paragraph:V82-P3856 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3857">
<!-- source-paragraph:V82-P3857 style=TableText -->
<pre>接口 ID（id）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3858">
<!-- source-paragraph:V82-P3858 style=TableText -->
<pre>HV08</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3859">
<!-- source-paragraph:V82-P3859 style=TableText -->
<pre>限定 ID（qualified_id）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3860">
<!-- source-paragraph:V82-P3860 style=TableText -->
<pre>human_variable:HV08</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3861">
<!-- source-paragraph:V82-P3861 style=TableText -->
<pre>名称（name）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3862">
<!-- source-paragraph:V82-P3862 style=TableText -->
<pre>条件势场</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3863">
<!-- source-paragraph:V82-P3863 style=TableText -->
<pre>主张类型（claim_type）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3864">
<!-- source-paragraph:V82-P3864 style=TableText -->
<pre>H</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3865">
<!-- source-paragraph:V82-P3865 style=TableText -->
<pre>合同角色（contract_role）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3866">
<!-- source-paragraph:V82-P3866 style=TableText -->
<pre>human_variable_interface</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3867">
<!-- source-paragraph:V82-P3867 style=TableText -->
<pre>命题（proposition）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3868">
<!-- source-paragraph:V82-P3868 style=TableText -->
<pre>资源、制度、关系、权力、安全、指标、平台与历史条件只有通过可检测机制改变人类行动概率或约束时进入解释。</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3869">
<!-- source-paragraph:V82-P3869 style=TableText -->
<pre>适用范围（scope）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3870">
<!-- source-paragraph:V82-P3870 style=TableText -->
<pre>人类行动受情境、制度与权力位置影响的场景</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3871">
<!-- source-paragraph:V82-P3871 style=TableText -->
<pre>暂停条件（pause_condition）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3872">
<!-- source-paragraph:V82-P3872 style=TableText -->
<pre>势场被当作万能背景、意图主体或道德标签</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3873 style=CardLabel -->
B. 正式依赖与推论边界

## V82-T100

<table data-source-table="V82-T100">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3874">
<!-- source-paragraph:V82-P3874 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3875">
<!-- source-paragraph:V82-P3875 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3876">
<!-- source-paragraph:V82-P3876 style=TableText -->
<pre>推论依赖（inferential_requires）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3877">
<!-- source-paragraph:V82-P3877 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3878">
<!-- source-paragraph:V82-P3878 style=TableText -->
<pre>协议依赖（protocol_requires）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3879,V82-P3880,V82-P3881">
<!-- source-paragraph:V82-P3879 style=TableText -->
<!-- source-paragraph:V82-P3880 style=TableText -->
<!-- source-paragraph:V82-P3881 style=TableText -->
<pre>1. E2
2. EVIDENCE
3. SOURCE</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3882">
<!-- source-paragraph:V82-P3882 style=TableText -->
<pre>限定／特化（specializes）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3883">
<!-- source-paragraph:V82-P3883 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3884">
<!-- source-paragraph:V82-P3884 style=TableText -->
<pre>适用对象引用（applies_to）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3885">
<!-- source-paragraph:V82-P3885 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3886">
<!-- source-paragraph:V82-P3886 style=TableText -->
<pre>条件支持路由（conditional_support_routes）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3887,V82-P3888,V82-P3889,V82-P3890,V82-P3891,V82-P3892,V82-P3893,V82-P3894,V82-P3895,V82-P3896,V82-P3897,V82-P3898,V82-P3899,V82-P3900,V82-P3901,V82-P3902,V82-P3903,V82-P3904,V82-P3905,V82-P3906,V82-P3907">
<!-- source-paragraph:V82-P3887 style=TableText -->
<!-- source-paragraph:V82-P3888 style=TableText -->
<!-- source-paragraph:V82-P3889 style=TableText -->
<!-- source-paragraph:V82-P3890 style=TableText -->
<!-- source-paragraph:V82-P3891 style=TableText -->
<!-- source-paragraph:V82-P3892 style=TableText -->
<!-- source-paragraph:V82-P3893 style=TableText -->
<!-- source-paragraph:V82-P3894 style=TableText -->
<!-- source-paragraph:V82-P3895 style=TableText -->
<!-- source-paragraph:V82-P3896 style=TableText -->
<!-- source-paragraph:V82-P3897 style=TableText -->
<!-- source-paragraph:V82-P3898 style=TableText -->
<!-- source-paragraph:V82-P3899 style=TableText -->
<!-- source-paragraph:V82-P3900 style=TableText -->
<!-- source-paragraph:V82-P3901 style=TableText -->
<!-- source-paragraph:V82-P3902 style=TableText -->
<!-- source-paragraph:V82-P3903 style=TableText -->
<!-- source-paragraph:V82-P3904 style=TableText -->
<!-- source-paragraph:V82-P3905 style=TableText -->
<!-- source-paragraph:V82-P3906 style=TableText -->
<!-- source-paragraph:V82-P3907 style=TableText -->
<pre>1. route_id=HV08-R0-condition-inventory；
claim_level=candidate_description；
when=资源、规则、位置、安全、指标、平台、AI中介或历史沉积可按位置、尺度和时间窗列出，但尚无符合资格的H4-instance。；
additional_inferential_requires=无（空集合）；
additional_protocol_requires=无（空集合）；
allowed_conclusion=登记候选条件、位置异质性、观察盲区、竞争解释与补证需求。；
result_ceiling=仅称条件清单或候选通道；不得把条件人格化，也不得称权力、中介或反身效应已成立。
2. route_id=HV08-R1-position-or-mediation-effect；
claim_level=conditional_effect；
when=H4-instance在证据覆盖、表达安全或对象行为中唯一预选的成功判据取得supported。；
additional_inferential_requires=H4-instance；
additional_protocol_requires=CAUSAL、E4；
allowed_conclusion=登记该实例位置、中介、结果家族和窗口内的遮蔽、放大或行为响应通道。；
result_ceiling=不外推到未选结果家族，不从位置或中介效应推出恶意、责任或自动处置。
3. route_id=HV08-R2-reflexive-response；
claim_level=mechanism_explanation；
when=H4-instance唯一预选反身响应判据，且观测、命名、评分或发布经实际通道到达对象并取得supported。；
additional_inferential_requires=H4-instance；
additional_protocol_requires=E3、CAUSAL、E4；
allowed_conclusion=登记指定观测或发布通道与窗口内的反身响应。；
result_ceiling=一次响应不称持久反身性；不得据此隐藏观察、压制表达或扩大授权。</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3908">
<!-- source-paragraph:V82-P3908 style=TableText -->
<pre>允许推论（allowed_inference）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3909">
<!-- source-paragraph:V82-P3909 style=TableText -->
<pre>1. 条件性机会、约束、遮蔽与放大</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3910">
<!-- source-paragraph:V82-P3910 style=TableText -->
<pre>禁止跳跃（prohibited_leap）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3911,V82-P3912,V82-P3913">
<!-- source-paragraph:V82-P3911 style=TableText -->
<!-- source-paragraph:V82-P3912 style=TableText -->
<!-- source-paragraph:V82-P3913 style=TableText -->
<pre>1. 条件决定个体行为
2. 权力位置证明恶意
3. 环境具有意图</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3914 style=CardLabel -->
C. 九轴尺度与对象合同

## V82-T101

<table data-source-table="V82-T101">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3915">
<!-- source-paragraph:V82-P3915 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3916">
<!-- source-paragraph:V82-P3916 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3917">
<!-- source-paragraph:V82-P3917 style=TableText -->
<pre>九轴尺度画像（scale_profile）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3918">
<!-- source-paragraph:V82-P3918 style=TableText -->
<pre>SP=&lt;A,X,T,O,C,R,I,N,J&gt;；A=聚合层次：单次暴露或评价事件、位置个案、受条件总体、响应分布及聚合规则；X=空间范围：互动现场、组织或平台边界、公开数字空间与跨域环境；T=时间跨度：暴露积累、响应、反身变化与消退窗口；O=组织层级：行动与评价角色、团队、组织、制度至治理生态；C=因果层次：暴露事件、条件—行为互动机制、中观权力结构、制度规则与系统条件；R=观察分辨率：原始暴露表达行为、时间序列、位置个案、响应分布、平台指标与摘要，并登记压缩损失；I=影响范围：直接被评价者、间接受影响者、二阶反身后果、跨域与代际影响；N=网络拓扑范围：权力与信息连接、中介节点、遮蔽区、放大路径与跨域传播；J=管辖与授权范围：规则配置、指标使用、公开评价、人工复核与处置分别登记授权；比较位置异质性</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3919">
<!-- source-paragraph:V82-P3919 style=TableText -->
<pre>有效对象（effective_object）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3920">
<!-- source-paragraph:V82-P3920 style=TableText -->
<pre>经实际通道改变行动概率、表达安全或证据分布的条件集合</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3921">
<!-- source-paragraph:V82-P3921 style=TableText -->
<pre>跨尺度保持项（scale_invariants）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3922">
<!-- source-paragraph:V82-P3922 style=TableText -->
<pre>1. 条件到行为或证据的机制链</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3923">
<!-- source-paragraph:V82-P3923 style=TableText -->
<pre>升格必补项（required_scale_additions）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3924,V82-P3925,V82-P3926,V82-P3927">
<!-- source-paragraph:V82-P3924 style=TableText -->
<!-- source-paragraph:V82-P3925 style=TableText -->
<!-- source-paragraph:V82-P3926 style=TableText -->
<!-- source-paragraph:V82-P3927 style=TableText -->
<pre>1. 位置分布
2. 条件异质性
3. 跨域外部性
4. J轴</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3928">
<!-- source-paragraph:V82-P3928 style=TableText -->
<pre>随尺度改变项（changing_semantics）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3929">
<!-- source-paragraph:V82-P3929 style=TableText -->
<pre>1. 关键条件与作用强度可随尺度改变</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3930">
<!-- source-paragraph:V82-P3930 style=TableText -->
<pre>不适用对象（non_applicable_objects）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3931">
<!-- source-paragraph:V82-P3931 style=TableText -->
<pre>1. 无意向行动、权力或制度位置的非人系统</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3932">
<!-- source-paragraph:V82-P3932 style=TableText -->
<pre>禁止升格（forbidden_elevation）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3933">
<!-- source-paragraph:V82-P3933 style=TableText -->
<pre>1. 局部条件直接普遍化为所有主体的动机</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3934 style=CardLabel -->
D. 状态、证据与变量流

## V82-T102

<table data-source-table="V82-T102">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3935">
<!-- source-paragraph:V82-P3935 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3936">
<!-- source-paragraph:V82-P3936 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3937">
<!-- source-paragraph:V82-P3937 style=TableText -->
<pre>状态集合（state）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3938,V82-P3939,V82-P3940,V82-P3941,V82-P3942">
<!-- source-paragraph:V82-P3938 style=TableText -->
<!-- source-paragraph:V82-P3939 style=TableText -->
<!-- source-paragraph:V82-P3940 style=TableText -->
<!-- source-paragraph:V82-P3941 style=TableText -->
<!-- source-paragraph:V82-P3942 style=TableText -->
<pre>1. 支持
2. 约束
3. 遮蔽
4. 放大
5. 混合</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3943">
<!-- source-paragraph:V82-P3943 style=TableText -->
<pre>可观测项（observables）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3944,V82-P3945,V82-P3946,V82-P3947">
<!-- source-paragraph:V82-P3944 style=TableText -->
<!-- source-paragraph:V82-P3945 style=TableText -->
<!-- source-paragraph:V82-P3946 style=TableText -->
<!-- source-paragraph:V82-P3947 style=TableText -->
<pre>1. 资源、规则、平台或公开条件改变前后的行为差异
2. 不同位置的表达安全、证据覆盖和缺席率
3. 指标、评分或AI中介前后的可见性与处置变化
4. 比较条件下候选通道效应是否超过预定阈值</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3948">
<!-- source-paragraph:V82-P3948 style=TableText -->
<pre>证据要求（evidence）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3949,V82-P3950,V82-P3951,V82-P3952">
<!-- source-paragraph:V82-P3949 style=TableText -->
<!-- source-paragraph:V82-P3950 style=TableText -->
<!-- source-paragraph:V82-P3951 style=TableText -->
<!-- source-paragraph:V82-P3952 style=TableText -->
<pre>1. 资源与规则
2. 位置差异
3. 平台或指标变化
4. 行为响应</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3953">
<!-- source-paragraph:V82-P3953 style=TableText -->
<pre>输入依赖与接口内容（input_dependencies）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3954">
<!-- source-paragraph:V82-P3954 style=TableText -->
<pre>1. 边界与接口2. 观察位置3. 因果合同</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3955">
<!-- source-paragraph:V82-P3955 style=TableText -->
<pre>输出效应与变量流（output_effects）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3956">
<!-- source-paragraph:V82-P3956 style=TableText -->
<pre>1. 可行路径2. 表达和证据3. 生成与失稳</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3957">
<!-- source-paragraph:V82-P3957 style=TableText -->
<pre>时间窗与时滞（time_window_and_lag）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3958">
<!-- source-paragraph:V82-P3958 style=TableText -->
<pre>登记条件积累、响应与消退时滞</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3959">
<!-- source-paragraph:V82-P3959 style=TableText -->
<pre>不确定性（uncertainty）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3960">
<!-- source-paragraph:V82-P3960 style=TableText -->
<pre>记录不可观察条件、共线性和反身变化</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3961">
<!-- source-paragraph:V82-P3961 style=TableText -->
<pre>局部排除区（local_exclusion_zone）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3962">
<!-- source-paragraph:V82-P3962 style=TableText -->
<pre>因安全、身份或平台门槛而不可见的位置</pre>
</td>
</tr>
<tr>
<td data-source-cell="10,1" data-paragraphs="V82-P3963">
<!-- source-paragraph:V82-P3963 style=TableText -->
<pre>受影响位置（affected_positions）</pre>
</td>
<td data-source-cell="10,2" data-paragraphs="V82-P3964,V82-P3965,V82-P3966,V82-P3967">
<!-- source-paragraph:V82-P3964 style=TableText -->
<!-- source-paragraph:V82-P3965 style=TableText -->
<!-- source-paragraph:V82-P3966 style=TableText -->
<!-- source-paragraph:V82-P3967 style=TableText -->
<pre>1. 优势位置
2. 低权力位置
3. 中介者
4. 被评价者</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3968 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

## V82-T103

<table data-source-table="V82-T103">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3969">
<!-- source-paragraph:V82-P3969 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3970">
<!-- source-paragraph:V82-P3970 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P3971">
<!-- source-paragraph:V82-P3971 style=TableText -->
<pre>承接载体（carrier）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P3972,V82-P3973,V82-P3974,V82-P3975,V82-P3976,V82-P3977">
<!-- source-paragraph:V82-P3972 style=TableText -->
<!-- source-paragraph:V82-P3973 style=TableText -->
<!-- source-paragraph:V82-P3974 style=TableText -->
<!-- source-paragraph:V82-P3975 style=TableText -->
<!-- source-paragraph:V82-P3976 style=TableText -->
<!-- source-paragraph:V82-P3977 style=TableText -->
<pre>1. 制度
2. 资源配置
3. 平台
4. 指标
5. 关系网络
6. 历史沉积</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P3978">
<!-- source-paragraph:V82-P3978 style=TableText -->
<pre>责任主体（responsible_subject）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P3979,V82-P3980,V82-P3981,V82-P3982">
<!-- source-paragraph:V82-P3979 style=TableText -->
<!-- source-paragraph:V82-P3980 style=TableText -->
<!-- source-paragraph:V82-P3981 style=TableText -->
<!-- source-paragraph:V82-P3982 style=TableText -->
<pre>1. 规则制定者
2. 平台运营者
3. 资源配置者
4. 行动决策者</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P3983">
<!-- source-paragraph:V82-P3983 style=TableText -->
<pre>规范地位（normative_status）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P3984">
<!-- source-paragraph:V82-P3984 style=TableText -->
<pre>条件优势或筛选结果不构成正当性</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P3985">
<!-- source-paragraph:V82-P3985 style=TableText -->
<pre>判断上限（judgment_ceiling）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P3986">
<!-- source-paragraph:V82-P3986 style=TableText -->
<pre>机制链与反事实充分时至解释级</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P3987">
<!-- source-paragraph:V82-P3987 style=TableText -->
<pre>行动上限（action_ceiling）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P3988">
<!-- source-paragraph:V82-P3988 style=TableText -->
<pre>本变量只生成候选条件通道、位置异质性、证据遮蔽与风险降低需求描述，不授权改变规则平台、资源配置、评价或处置主体；任何现实调整须另过C12、运行时显式N前提、J授权与O程序</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P3989">
<!-- source-paragraph:V82-P3989 style=TableText -->
<pre>反例（counterexamples）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P3990,V82-P3991">
<!-- source-paragraph:V82-P3990 style=TableText -->
<!-- source-paragraph:V82-P3991 style=TableText -->
<pre>1. 相同制度条件下不同安全和权力位置出现相反行动
2. 以权力或平台标签替代实际因果通道后无法解释状态变化</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P3992">
<!-- source-paragraph:V82-P3992 style=TableText -->
<pre>申诉（appeal）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P3993">
<!-- source-paragraph:V82-P3993 style=TableText -->
<pre>依appeal_and_rollback_rule，不同位置可经安全可达、反报复通道提交机制差异、缺席信号与安全影响，并触发与原势场判断或决策链独立的复核</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P3994">
<!-- source-paragraph:V82-P3994 style=TableText -->
<pre>回滚（rollback）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P3995">
<!-- source-paragraph:V82-P3995 style=TableText -->
<pre>依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内实际撤销不成立的势场归因、移除位置标签及其下游评价处置效力并恢复未决状态，保留版本与完成验证</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P3996 style=SecH2 -->
## A.9　HV09 结构负荷（完整接口卡）

<!-- source-paragraph:V82-P3997 style=CardLabel -->
A. 身份、命题与适用范围

## V82-T104

<table data-source-table="V82-T104">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P3998">
<!-- source-paragraph:V82-P3998 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P3999">
<!-- source-paragraph:V82-P3999 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P4000">
<!-- source-paragraph:V82-P4000 style=TableText -->
<pre>接口 ID（id）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P4001">
<!-- source-paragraph:V82-P4001 style=TableText -->
<pre>HV09</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P4002">
<!-- source-paragraph:V82-P4002 style=TableText -->
<pre>限定 ID（qualified_id）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P4003">
<!-- source-paragraph:V82-P4003 style=TableText -->
<pre>human_variable:HV09</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P4004">
<!-- source-paragraph:V82-P4004 style=TableText -->
<pre>名称（name）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P4005">
<!-- source-paragraph:V82-P4005 style=TableText -->
<pre>结构负荷</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P4006">
<!-- source-paragraph:V82-P4006 style=TableText -->
<pre>主张类型（claim_type）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P4007">
<!-- source-paragraph:V82-P4007 style=TableText -->
<pre>H</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P4008">
<!-- source-paragraph:V82-P4008 style=TableText -->
<pre>合同角色（contract_role）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P4009">
<!-- source-paragraph:V82-P4009 style=TableText -->
<pre>human_variable_interface</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P4010">
<!-- source-paragraph:V82-P4010 style=TableText -->
<pre>命题（proposition）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P4011">
<!-- source-paragraph:V82-P4011 style=TableText -->
<pre>人类结构负荷必须把任务、协调损耗、维护要求、容量、恢复余量和成本承担位置共同登记。</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P4012">
<!-- source-paragraph:V82-P4012 style=TableText -->
<pre>适用范围（scope）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P4013">
<!-- source-paragraph:V82-P4013 style=TableText -->
<pre>持续运转、维护、照护或高压条件下的人类结构</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P4014">
<!-- source-paragraph:V82-P4014 style=TableText -->
<pre>暂停条件（pause_condition）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P4015">
<!-- source-paragraph:V82-P4015 style=TableText -->
<pre>只用熵、脆弱或韧性隐喻而无任务、容量和恢复机制</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P4016 style=CardLabel -->
B. 正式依赖与推论边界

## V82-T105

<table data-source-table="V82-T105">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P4017">
<!-- source-paragraph:V82-P4017 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P4018">
<!-- source-paragraph:V82-P4018 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P4019">
<!-- source-paragraph:V82-P4019 style=TableText -->
<pre>推论依赖（inferential_requires）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P4020">
<!-- source-paragraph:V82-P4020 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P4021">
<!-- source-paragraph:V82-P4021 style=TableText -->
<pre>协议依赖（protocol_requires）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P4022">
<!-- source-paragraph:V82-P4022 style=TableText -->
<pre>1. EVIDENCE2. SOURCE</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P4023">
<!-- source-paragraph:V82-P4023 style=TableText -->
<pre>限定／特化（specializes）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P4024">
<!-- source-paragraph:V82-P4024 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P4025">
<!-- source-paragraph:V82-P4025 style=TableText -->
<pre>适用对象引用（applies_to）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P4026">
<!-- source-paragraph:V82-P4026 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P4027">
<!-- source-paragraph:V82-P4027 style=TableText -->
<pre>条件支持路由（conditional_support_routes）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P4028,V82-P4029,V82-P4030,V82-P4031,V82-P4032,V82-P4033,V82-P4034,V82-P4035,V82-P4036,V82-P4037,V82-P4038,V82-P4039,V82-P4040,V82-P4041,V82-P4042,V82-P4043,V82-P4044,V82-P4045,V82-P4046,V82-P4047,V82-P4048">
<!-- source-paragraph:V82-P4028 style=TableText -->
<!-- source-paragraph:V82-P4029 style=TableText -->
<!-- source-paragraph:V82-P4030 style=TableText -->
<!-- source-paragraph:V82-P4031 style=TableText -->
<!-- source-paragraph:V82-P4032 style=TableText -->
<!-- source-paragraph:V82-P4033 style=TableText -->
<!-- source-paragraph:V82-P4034 style=TableText -->
<!-- source-paragraph:V82-P4035 style=TableText -->
<!-- source-paragraph:V82-P4036 style=TableText -->
<!-- source-paragraph:V82-P4037 style=TableText -->
<!-- source-paragraph:V82-P4038 style=TableText -->
<!-- source-paragraph:V82-P4039 style=TableText -->
<!-- source-paragraph:V82-P4040 style=TableText -->
<!-- source-paragraph:V82-P4041 style=TableText -->
<!-- source-paragraph:V82-P4042 style=TableText -->
<!-- source-paragraph:V82-P4043 style=TableText -->
<!-- source-paragraph:V82-P4044 style=TableText -->
<!-- source-paragraph:V82-P4045 style=TableText -->
<!-- source-paragraph:V82-P4046 style=TableText -->
<!-- source-paragraph:V82-P4047 style=TableText -->
<!-- source-paragraph:V82-P4048 style=TableText -->
<pre>1. route_id=HV09-R0-instant-task-capacity；
claim_level=descriptive_classification；
when=同一窗口、位置与类型映射下的任务或协调要求、容量、恢复余量及其分布可观察。；
additional_inferential_requires=无（空集合）；
additional_protocol_requires=无（空集合）；
allowed_conclusion=登记瞬时任务—容量关系、余量、积压、局部缺口与恢复状态。；
result_ceiling=只到同窗描述；瞬时峰值或缺口不自动成为过载机制、累积损伤或崩溃。
2. route_id=HV09-R1-overload-mechanism；
claim_level=mechanism_explanation；
when=CM-LOAD的适用条件完整，且符合资格的G2-instance显示负荷、补给、减载或恢复通道对预选结果有超过阈值效应。；
additional_inferential_requires=G2-instance、CM-LOAD；
additional_protocol_requires=CAUSAL、E4；
allowed_conclusion=登记指定位置、类型、窗口和通道内的过载或恢复机制候选。；
result_ceiling=不得普遍化为熵、韧性或所有位置必然崩溃，也不直接生成减载或牺牲义务。
3. route_id=HV09-R2-cumulative-overload；
claim_level=intertemporal_explanation；
when=过载机制已有G2-instance与CM-LOAD支持，且G3-instance显示历史负荷对后续容量、错误或恢复具有条件增量。；
additional_inferential_requires=G2-instance、CM-LOAD、G3-instance；
additional_protocol_requires=CAUSAL、E4；
allowed_conclusion=登记预注册载体、窗口和结果内的累积损伤或迟恢复候选。；
result_ceiling=不推出不可逆、必然崩溃、责任归属或具名主体承担义务。</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P4049">
<!-- source-paragraph:V82-P4049 style=TableText -->
<pre>允许推论（allowed_inference）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P4050">
<!-- source-paragraph:V82-P4050 style=TableText -->
<pre>1. 候选过载、余量不足、维护缺口与恢复差异</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P4051">
<!-- source-paragraph:V82-P4051 style=TableText -->
<pre>禁止跳跃（prohibited_leap）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P4052,V82-P4053,V82-P4054">
<!-- source-paragraph:V82-P4052 style=TableText -->
<!-- source-paragraph:V82-P4053 style=TableText -->
<!-- source-paragraph:V82-P4054 style=TableText -->
<pre>1. 承接者应继续承担
2. 高负荷证明奉献
3. 过载主体等于失稳机制</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P4055 style=CardLabel -->
C. 九轴尺度与对象合同

## V82-T106

<table data-source-table="V82-T106">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P4056">
<!-- source-paragraph:V82-P4056 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P4057">
<!-- source-paragraph:V82-P4057 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P4058">
<!-- source-paragraph:V82-P4058 style=TableText -->
<pre>九轴尺度画像（scale_profile）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P4059">
<!-- source-paragraph:V82-P4059 style=TableText -->
<pre>SP=&lt;A,X,T,O,C,R,I,N,J&gt;；A=聚合层次：单项任务负荷、承接个案、岗位或群体总体、负荷容量分布及聚合规则；X=空间范围：工作或照护现场、组织边界、数字劳动空间与跨域外包范围；T=时间跨度：瞬时峰值、持续积压、恢复时滞、跨期与代际窗口；O=组织层级：承接角色、团队、组织、制度至治理生态；C=因果层次：任务事件、任务—容量互动机制、中观瓶颈结构、制度分配与系统条件；R=观察分辨率：原始任务工时记录、负荷序列、承接个案、容量分布、时延错误指标与摘要，并登记压缩损失；I=影响范围：直接承接者、服务依赖者、间接替代者、二阶外溢、跨域与代际成本；N=网络拓扑范围：任务依赖、关键瓶颈、替代节点、恢复路径与跨域外包网络；J=管辖与授权范围：任务分配、资源调整、停止、绩效使用与补救分别登记授权；保留负荷容量分布</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P4060">
<!-- source-paragraph:V82-P4060 style=TableText -->
<pre>有效对象（effective_object）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P4061">
<!-- source-paragraph:V82-P4061 style=TableText -->
<pre>给定窗口内任务和协调要求相对可用容量与恢复余量的结构关系</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P4062">
<!-- source-paragraph:V82-P4062 style=TableText -->
<pre>跨尺度保持项（scale_invariants）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P4063">
<!-- source-paragraph:V82-P4063 style=TableText -->
<pre>1. 负荷、容量、恢复与成本位置</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P4064">
<!-- source-paragraph:V82-P4064 style=TableText -->
<pre>升格必补项（required_scale_additions）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P4065,V82-P4066,V82-P4067,V82-P4068">
<!-- source-paragraph:V82-P4065 style=TableText -->
<!-- source-paragraph:V82-P4066 style=TableText -->
<!-- source-paragraph:V82-P4067 style=TableText -->
<!-- source-paragraph:V82-P4068 style=TableText -->
<pre>1. 负荷分布
2. 聚合遮蔽
3. 责任继承
4. 代际影响</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P4069">
<!-- source-paragraph:V82-P4069 style=TableText -->
<pre>随尺度改变项（changing_semantics）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P4070">
<!-- source-paragraph:V82-P4070 style=TableText -->
<pre>1. 瓶颈、容量和恢复方式可随层级改变</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P4071">
<!-- source-paragraph:V82-P4071 style=TableText -->
<pre>不适用对象（non_applicable_objects）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P4072">
<!-- source-paragraph:V82-P4072 style=TableText -->
<pre>1. 无持续非平衡、维护或人类承接要求的过程</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P4073">
<!-- source-paragraph:V82-P4073 style=TableText -->
<pre>禁止升格（forbidden_elevation）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P4074">
<!-- source-paragraph:V82-P4074 style=TableText -->
<pre>1. 平均负荷掩盖局部过载</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P4075 style=CardLabel -->
D. 状态、证据与变量流

## V82-T107

<table data-source-table="V82-T107">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P4076">
<!-- source-paragraph:V82-P4076 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P4077">
<!-- source-paragraph:V82-P4077 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P4078">
<!-- source-paragraph:V82-P4078 style=TableText -->
<pre>状态集合（state）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P4079,V82-P4080,V82-P4081,V82-P4082,V82-P4083">
<!-- source-paragraph:V82-P4079 style=TableText -->
<!-- source-paragraph:V82-P4080 style=TableText -->
<!-- source-paragraph:V82-P4081 style=TableText -->
<!-- source-paragraph:V82-P4082 style=TableText -->
<!-- source-paragraph:V82-P4083 style=TableText -->
<pre>1. 低负荷
2. 可承受
3. 临界
4. 过载
5. 恢复</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P4084">
<!-- source-paragraph:V82-P4084 style=TableText -->
<pre>可观测项（observables）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P4085,V82-P4086,V82-P4087,V82-P4088">
<!-- source-paragraph:V82-P4085 style=TableText -->
<!-- source-paragraph:V82-P4086 style=TableText -->
<!-- source-paragraph:V82-P4087 style=TableText -->
<!-- source-paragraph:V82-P4088 style=TableText -->
<pre>1. 单位时间任务量、积压、时延和错误率
2. 人员资源容量、隐性劳动与替代可用性
3. 停止、缺席、退出和恢复曲线
4. 平均负荷与关键局部承接位置的分布差异</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P4089">
<!-- source-paragraph:V82-P4089 style=TableText -->
<pre>证据要求（evidence）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P4090,V82-P4091,V82-P4092,V82-P4093,V82-P4094">
<!-- source-paragraph:V82-P4090 style=TableText -->
<!-- source-paragraph:V82-P4091 style=TableText -->
<!-- source-paragraph:V82-P4092 style=TableText -->
<!-- source-paragraph:V82-P4093 style=TableText -->
<!-- source-paragraph:V82-P4094 style=TableText -->
<pre>1. 任务量
2. 时延与错误
3. 人员与资源
4. 恢复记录
5. 退出和缺席</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P4095">
<!-- source-paragraph:V82-P4095 style=TableText -->
<pre>输入依赖与接口内容（input_dependencies）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P4096,V82-P4097,V82-P4098,V82-P4099">
<!-- source-paragraph:V82-P4096 style=TableText -->
<!-- source-paragraph:V82-P4097 style=TableText -->
<!-- source-paragraph:V82-P4098 style=TableText -->
<!-- source-paragraph:V82-P4099 style=TableText -->
<pre>1. 承接层
2. 动力—承接链
3. 条件势场
4. 瞬时负荷只调用G2与CM-LOAD；累积损伤、迟恢复或历史条件增量另需预注册G3-instance，H5候选留痕不能替代G3</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P4100">
<!-- source-paragraph:V82-P4100 style=TableText -->
<pre>输出效应与变量流（output_effects）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P4101">
<!-- source-paragraph:V82-P4101 style=TableText -->
<pre>1. 状态更新2. 失稳行为3. 维护和修复需求</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P4102">
<!-- source-paragraph:V82-P4102 style=TableText -->
<pre>时间窗与时滞（time_window_and_lag）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P4103">
<!-- source-paragraph:V82-P4103 style=TableText -->
<pre>区分即时峰值、持续积压、恢复时滞与代际成本</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P4104">
<!-- source-paragraph:V82-P4104 style=TableText -->
<pre>不确定性（uncertainty）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P4105">
<!-- source-paragraph:V82-P4105 style=TableText -->
<pre>记录隐性劳动、外包成本和保护性缺席</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P4106">
<!-- source-paragraph:V82-P4106 style=TableText -->
<pre>局部排除区（local_exclusion_zone）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P4107">
<!-- source-paragraph:V82-P4107 style=TableText -->
<pre>非正式劳动、家庭照护、外包和低可见承接位置</pre>
</td>
</tr>
<tr>
<td data-source-cell="10,1" data-paragraphs="V82-P4108">
<!-- source-paragraph:V82-P4108 style=TableText -->
<pre>受影响位置（affected_positions）</pre>
</td>
<td data-source-cell="10,2" data-paragraphs="V82-P4109,V82-P4110,V82-P4111,V82-P4112">
<!-- source-paragraph:V82-P4109 style=TableText -->
<!-- source-paragraph:V82-P4110 style=TableText -->
<!-- source-paragraph:V82-P4111 style=TableText -->
<!-- source-paragraph:V82-P4112 style=TableText -->
<pre>1. 承接者
2. 依赖服务者
3. 替代者
4. 成本外溢位置</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P4113 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

## V82-T108

<table data-source-table="V82-T108">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P4114">
<!-- source-paragraph:V82-P4114 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P4115">
<!-- source-paragraph:V82-P4115 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P4116">
<!-- source-paragraph:V82-P4116 style=TableText -->
<pre>承接载体（carrier）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P4117,V82-P4118,V82-P4119,V82-P4120,V82-P4121">
<!-- source-paragraph:V82-P4117 style=TableText -->
<!-- source-paragraph:V82-P4118 style=TableText -->
<!-- source-paragraph:V82-P4119 style=TableText -->
<!-- source-paragraph:V82-P4120 style=TableText -->
<!-- source-paragraph:V82-P4121 style=TableText -->
<pre>1. 人员
2. 岗位
3. 程序
4. 设施
5. 预算</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P4122">
<!-- source-paragraph:V82-P4122 style=TableText -->
<pre>责任主体（responsible_subject）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P4123,V82-P4124,V82-P4125,V82-P4126,V82-P4127">
<!-- source-paragraph:V82-P4123 style=TableText -->
<!-- source-paragraph:V82-P4124 style=TableText -->
<!-- source-paragraph:V82-P4125 style=TableText -->
<!-- source-paragraph:V82-P4126 style=TableText -->
<!-- source-paragraph:V82-P4127 style=TableText -->
<pre>1. 任务分配者
2. 资源配置者
3. 授权者
4. 监督者
5. 补救责任者</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P4128">
<!-- source-paragraph:V82-P4128 style=TableText -->
<pre>规范地位（normative_status）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P4129">
<!-- source-paragraph:V82-P4129 style=TableText -->
<pre>高效率或高承载不构成正当性</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P4130">
<!-- source-paragraph:V82-P4130 style=TableText -->
<pre>判断上限（judgment_ceiling）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P4131">
<!-- source-paragraph:V82-P4131 style=TableText -->
<pre>负荷容量和恢复证据充分时至诊断级</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P4132">
<!-- source-paragraph:V82-P4132 style=TableText -->
<pre>行动上限（action_ceiling）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P4133">
<!-- source-paragraph:V82-P4133 style=TableText -->
<pre>本变量只生成负荷、容量、恢复、局部过载与减载补资源需求描述，不授权任务削减、资源投入、绩效处置或强迫承担；任何现实调整须另过C12、运行时显式N前提、J授权与O程序</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P4134">
<!-- source-paragraph:V82-P4134 style=TableText -->
<pre>反例（counterexamples）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P4135,V82-P4136">
<!-- source-paragraph:V82-P4135 style=TableText -->
<!-- source-paragraph:V82-P4136 style=TableText -->
<pre>1. 总体平均容量充足但少数关键承接位置持续过载
2. 只用熵或韧性隐喻却无法识别任务、容量和恢复通道</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P4137">
<!-- source-paragraph:V82-P4137 style=TableText -->
<pre>申诉（appeal）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P4138">
<!-- source-paragraph:V82-P4138 style=TableText -->
<pre>依appeal_and_rollback_rule，承接者可经安全可达、反报复通道报告隐性劳动、过载和恢复需求，并触发与原负荷判断、绩效或任务决策链独立的复核</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P4139">
<!-- source-paragraph:V82-P4139 style=TableText -->
<pre>回滚（rollback）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P4140">
<!-- source-paragraph:V82-P4140 style=TableText -->
<pre>依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销错误负荷判断及绩效或责任效力，实际恢复任务、资源与记录状态，保留版本与完成验证</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P4141 style=SecH2 -->
## A.10　HV10 演化相位（完整接口卡）

<!-- source-paragraph:V82-P4142 style=CardLabel -->
A. 身份、命题与适用范围

## V82-T109

<table data-source-table="V82-T109">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P4143">
<!-- source-paragraph:V82-P4143 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P4144">
<!-- source-paragraph:V82-P4144 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P4145">
<!-- source-paragraph:V82-P4145 style=TableText -->
<pre>接口 ID（id）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P4146">
<!-- source-paragraph:V82-P4146 style=TableText -->
<pre>HV10</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P4147">
<!-- source-paragraph:V82-P4147 style=TableText -->
<pre>限定 ID（qualified_id）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P4148">
<!-- source-paragraph:V82-P4148 style=TableText -->
<pre>human_variable:HV10</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P4149">
<!-- source-paragraph:V82-P4149 style=TableText -->
<pre>名称（name）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P4150">
<!-- source-paragraph:V82-P4150 style=TableText -->
<pre>演化相位</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P4151">
<!-- source-paragraph:V82-P4151 style=TableText -->
<pre>主张类型（claim_type）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P4152">
<!-- source-paragraph:V82-P4152 style=TableText -->
<pre>H</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P4153">
<!-- source-paragraph:V82-P4153 style=TableText -->
<pre>合同角色（contract_role）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P4154">
<!-- source-paragraph:V82-P4154 style=TableText -->
<pre>human_variable_interface</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P4155">
<!-- source-paragraph:V82-P4155 style=TableText -->
<pre>命题（proposition）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P4156">
<!-- source-paragraph:V82-P4156 style=TableText -->
<pre>S0-S6和X0只适用于存在方向、生成主体或事件、承接层与制度化过程的人类意向性集体，且允许跳阶、并行、混合、回退、分裂、合并、休眠、吞并和功能转移。</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P4157">
<!-- source-paragraph:V82-P4157 style=TableText -->
<pre>适用范围（scope）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P4158">
<!-- source-paragraph:V82-P4158 style=TableText -->
<pre>符合适用条件的人类意向性集体</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P4159">
<!-- source-paragraph:V82-P4159 style=TableText -->
<pre>暂停条件（pause_condition）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P4160">
<!-- source-paragraph:V82-P4160 style=TableText -->
<pre>适用条件缺失、阶段被道德化或标题与判据不一致</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P4161 style=CardLabel -->
B. 正式依赖与推论边界

## V82-T110

<table data-source-table="V82-T110">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P4162">
<!-- source-paragraph:V82-P4162 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P4163">
<!-- source-paragraph:V82-P4163 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P4164">
<!-- source-paragraph:V82-P4164 style=TableText -->
<pre>推论依赖（inferential_requires）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P4165,V82-P4166,V82-P4167,V82-P4168">
<!-- source-paragraph:V82-P4165 style=TableText -->
<!-- source-paragraph:V82-P4166 style=TableText -->
<!-- source-paragraph:V82-P4167 style=TableText -->
<!-- source-paragraph:V82-P4168 style=TableText -->
<pre>1. human_variable:HV03
2. human_variable:HV04
3. human_variable:HV05
4. human_variable:HV07</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P4169">
<!-- source-paragraph:V82-P4169 style=TableText -->
<pre>协议依赖（protocol_requires）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P4170">
<!-- source-paragraph:V82-P4170 style=TableText -->
<pre>1. EVIDENCE2. SOURCE</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P4171">
<!-- source-paragraph:V82-P4171 style=TableText -->
<pre>限定／特化（specializes）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P4172">
<!-- source-paragraph:V82-P4172 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P4173">
<!-- source-paragraph:V82-P4173 style=TableText -->
<pre>适用对象引用（applies_to）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P4174">
<!-- source-paragraph:V82-P4174 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P4175">
<!-- source-paragraph:V82-P4175 style=TableText -->
<pre>条件支持路由（conditional_support_routes）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P4176,V82-P4177,V82-P4178,V82-P4179,V82-P4180,V82-P4181,V82-P4182,V82-P4183,V82-P4184,V82-P4185,V82-P4186,V82-P4187,V82-P4188,V82-P4189,V82-P4190,V82-P4191,V82-P4192,V82-P4193,V82-P4194,V82-P4195,V82-P4196,V82-P4197,V82-P4198,V82-P4199,V82-P4200,V82-P4201,V82-P4202,V82-P4203">
<!-- source-paragraph:V82-P4176 style=TableText -->
<!-- source-paragraph:V82-P4177 style=TableText -->
<!-- source-paragraph:V82-P4178 style=TableText -->
<!-- source-paragraph:V82-P4179 style=TableText -->
<!-- source-paragraph:V82-P4180 style=TableText -->
<!-- source-paragraph:V82-P4181 style=TableText -->
<!-- source-paragraph:V82-P4182 style=TableText -->
<!-- source-paragraph:V82-P4183 style=TableText -->
<!-- source-paragraph:V82-P4184 style=TableText -->
<!-- source-paragraph:V82-P4185 style=TableText -->
<!-- source-paragraph:V82-P4186 style=TableText -->
<!-- source-paragraph:V82-P4187 style=TableText -->
<!-- source-paragraph:V82-P4188 style=TableText -->
<!-- source-paragraph:V82-P4189 style=TableText -->
<!-- source-paragraph:V82-P4190 style=TableText -->
<!-- source-paragraph:V82-P4191 style=TableText -->
<!-- source-paragraph:V82-P4192 style=TableText -->
<!-- source-paragraph:V82-P4193 style=TableText -->
<!-- source-paragraph:V82-P4194 style=TableText -->
<!-- source-paragraph:V82-P4195 style=TableText -->
<!-- source-paragraph:V82-P4196 style=TableText -->
<!-- source-paragraph:V82-P4197 style=TableText -->
<!-- source-paragraph:V82-P4198 style=TableText -->
<!-- source-paragraph:V82-P4199 style=TableText -->
<!-- source-paragraph:V82-P4200 style=TableText -->
<!-- source-paragraph:V82-P4201 style=TableText -->
<!-- source-paragraph:V82-P4202 style=TableText -->
<!-- source-paragraph:V82-P4203 style=TableText -->
<pre>1. route_id=HV10-R0-component-applicability；
claim_level=descriptive_classification；
when=HV03、HV04、HV05与HV07已有可审计评估记录；记录允许为missing、not_applicable或unsupported，不要求四组件经验成立。；
additional_inferential_requires=无（空集合）；
additional_protocol_requires=无（空集合）；
allowed_conclusion=登记适用、不适用、组件缺失、混合状态与继续观察需求。；
result_ceiling=组件检查本身不产生S0-S6或X0相位匹配。
2. route_id=HV10-R1-pattern-phase-match；
claim_level=descriptive_classification；
when=CM-PHASE的状态判据、观察窗、混合与转换规则完整，并在重复窗口匹配。；
additional_inferential_requires=CM-PHASE；
additional_protocol_requires=E4；
allowed_conclusion=登记S0-S6或X0的原型匹配、混合、并行、回退、休眠或转换描述。；
result_ceiling=只到模式相位；相位不是健康、成功、正当性或淘汰等级。
3. route_id=HV10-R2-causal-transition；
claim_level=mechanism_explanation；
when=CM-PHASE匹配成立，且G2-instance识别指定相位转移通道对预选状态变化的效应。；
additional_inferential_requires=CM-PHASE、G2-instance；
additional_protocol_requires=CAUSAL、E4；
allowed_conclusion=登记指定对象、窗口和通道内的候选因果相位转移。；
result_ceiling=不得从转移机制推出必然阶段序列、价值方向或推进与淘汰授权。
4. route_id=HV10-R3-path-dependent-phase；
claim_level=intertemporal_explanation；
when=CM-PHASE匹配成立，且G3-instance显示历史相位变量对后续状态、迟滞或回退具有条件增量。；
additional_inferential_requires=CM-PHASE、G3-instance；
additional_protocol_requires=CAUSAL、E4；
allowed_conclusion=登记预注册窗口内的路径依赖、迟滞或历史相位差异候选。；
result_ceiling=不得称命运、绝对不可逆或自动规定修复、退出与退场方案。</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P4204">
<!-- source-paragraph:V82-P4204 style=TableText -->
<pre>允许推论（allowed_inference）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P4205,V82-P4206,V82-P4207">
<!-- source-paragraph:V82-P4205 style=TableText -->
<!-- source-paragraph:V82-P4206 style=TableText -->
<!-- source-paragraph:V82-P4207 style=TableText -->
<pre>1. 条件性状态坐标
2. 非线性路径
3. 有序退场X0</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P4208">
<!-- source-paragraph:V82-P4208 style=TableText -->
<pre>禁止跳跃（prohibited_leap）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P4209,V82-P4210,V82-P4211">
<!-- source-paragraph:V82-P4209 style=TableText -->
<!-- source-paragraph:V82-P4210 style=TableText -->
<!-- source-paragraph:V82-P4211 style=TableText -->
<pre>1. 所有系统必经S0-S6
2. 阶段越高越正当
3. 解体等于失败</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P4212 style=CardLabel -->
C. 九轴尺度与对象合同

## V82-T111

<table data-source-table="V82-T111">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P4213">
<!-- source-paragraph:V82-P4213 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P4214">
<!-- source-paragraph:V82-P4214 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P4215">
<!-- source-paragraph:V82-P4215 style=TableText -->
<pre>九轴尺度画像（scale_profile）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P4216">
<!-- source-paragraph:V82-P4216 style=TableText -->
<pre>SP=&lt;A,X,T,O,C,R,I,N,J&gt;；A=聚合层次：单次状态事件、局部群体个案、意向集体总体、相位分布及聚合规则；X=空间范围：行动现场、组织或制度边界、数字协作空间与跨域演化范围；T=时间跨度：状态窗口、转移时滞、回退、休眠、迟滞与代际周期；O=组织层级：成员角色、团队、组织、制度至治理生态；C=因果层次：状态事件、转移互动机制、中观相位结构、制度化过程与系统条件；R=观察分辨率：原始状态事件、转移序列、局部个案、相位分布、状态指标与摘要，并登记压缩损失；I=影响范围：直接成员与承接者、退出者、间接受影响者、二阶后果、跨域与代际影响；N=网络拓扑范围：局部相位簇群、跨层连接、分裂合并、功能转移与继承路径；J=管辖与授权范围：相位命名、监测采用、试探、推进、退场与淘汰分别登记授权；保留混合相位</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P4217">
<!-- source-paragraph:V82-P4217 style=TableText -->
<pre>有效对象（effective_object）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P4218">
<!-- source-paragraph:V82-P4218 style=TableText -->
<pre>具有人类意向、生成、承接和制度化的集体状态</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P4219">
<!-- source-paragraph:V82-P4219 style=TableText -->
<pre>跨尺度保持项（scale_invariants）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P4220,V82-P4221,V82-P4222,V82-P4223">
<!-- source-paragraph:V82-P4220 style=TableText -->
<!-- source-paragraph:V82-P4221 style=TableText -->
<!-- source-paragraph:V82-P4222 style=TableText -->
<!-- source-paragraph:V82-P4223 style=TableText -->
<pre>1. 适用条件
2. 相位判据
3. 非线性路径
4. X0不计为第八阶段</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P4224">
<!-- source-paragraph:V82-P4224 style=TableText -->
<pre>升格必补项（required_scale_additions）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P4225,V82-P4226,V82-P4227,V82-P4228">
<!-- source-paragraph:V82-P4225 style=TableText -->
<!-- source-paragraph:V82-P4226 style=TableText -->
<!-- source-paragraph:V82-P4227 style=TableText -->
<!-- source-paragraph:V82-P4228 style=TableText -->
<pre>1. 局部相位分布
2. 跨层转移
3. 承接继承
4. 保护与退出</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P4229">
<!-- source-paragraph:V82-P4229 style=TableText -->
<pre>随尺度改变项（changing_semantics）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P4230">
<!-- source-paragraph:V82-P4230 style=TableText -->
<pre>1. 承接者、制度载体和有效对象可随相位改变</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P4231">
<!-- source-paragraph:V82-P4231 style=TableText -->
<pre>不适用对象（non_applicable_objects）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P4232">
<!-- source-paragraph:V82-P4232 style=TableText -->
<pre>1. 无方向、生成、承接或制度化过程的系统</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P4233">
<!-- source-paragraph:V82-P4233 style=TableText -->
<pre>禁止升格（forbidden_elevation）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P4234,V82-P4235">
<!-- source-paragraph:V82-P4234 style=TableText -->
<!-- source-paragraph:V82-P4235 style=TableText -->
<pre>1. 个案相位直接代表总体
2. 人类阶段迁入通用核心</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P4236 style=CardLabel -->
D. 状态、证据与变量流

## V82-T112

<table data-source-table="V82-T112">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P4237">
<!-- source-paragraph:V82-P4237 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P4238">
<!-- source-paragraph:V82-P4238 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P4239">
<!-- source-paragraph:V82-P4239 style=TableText -->
<pre>状态集合（state）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P4240,V82-P4241,V82-P4242,V82-P4243,V82-P4244,V82-P4245,V82-P4246,V82-P4247">
<!-- source-paragraph:V82-P4240 style=TableText -->
<!-- source-paragraph:V82-P4241 style=TableText -->
<!-- source-paragraph:V82-P4242 style=TableText -->
<!-- source-paragraph:V82-P4243 style=TableText -->
<!-- source-paragraph:V82-P4244 style=TableText -->
<!-- source-paragraph:V82-P4245 style=TableText -->
<!-- source-paragraph:V82-P4246 style=TableText -->
<!-- source-paragraph:V82-P4247 style=TableText -->
<pre>1. S0
2. S1
3. S2
4. S3
5. S4
6. S5
7. S6
8. X0转换路径</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P4248">
<!-- source-paragraph:V82-P4248 style=TableText -->
<pre>可观测项（observables）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P4249,V82-P4250,V82-P4251,V82-P4252">
<!-- source-paragraph:V82-P4249 style=TableText -->
<!-- source-paragraph:V82-P4250 style=TableText -->
<!-- source-paragraph:V82-P4251 style=TableText -->
<!-- source-paragraph:V82-P4252 style=TableText -->
<pre>1. 方向、生成、承接、制度化和反馈变量的同期状态
2. 相位判据跨观察窗的重复匹配记录
3. 跳阶、并行、混合、回退、分裂、合并与休眠轨迹
4. X0中的功能转移、责任继承与有序退场记录</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P4253">
<!-- source-paragraph:V82-P4253 style=TableText -->
<pre>证据要求（evidence）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P4254,V82-P4255,V82-P4256,V82-P4257">
<!-- source-paragraph:V82-P4254 style=TableText -->
<!-- source-paragraph:V82-P4255 style=TableText -->
<!-- source-paragraph:V82-P4256 style=TableText -->
<!-- source-paragraph:V82-P4257 style=TableText -->
<pre>1. 相位变量
2. 转移记录
3. 留痕
4. 承接与制度状态</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P4258">
<!-- source-paragraph:V82-P4258 style=TableText -->
<pre>输入依赖与接口内容（input_dependencies）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P4259,V82-P4260,V82-P4261,V82-P4262,V82-P4263,V82-P4264">
<!-- source-paragraph:V82-P4259 style=TableText -->
<!-- source-paragraph:V82-P4260 style=TableText -->
<!-- source-paragraph:V82-P4261 style=TableText -->
<!-- source-paragraph:V82-P4262 style=TableText -->
<!-- source-paragraph:V82-P4263 style=TableText -->
<!-- source-paragraph:V82-P4264 style=TableText -->
<pre>1. 指向锚点
2. 生成节点
3. 承接层
4. 反馈写回
5. 结构负荷
6. 模式相位不要求G3；因果转移另需CAUSAL；迟滞、路径依赖或历史效应另需预注册G3-instance，H5只登记候选留痕</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P4265">
<!-- source-paragraph:V82-P4265 style=TableText -->
<pre>输出效应与变量流（output_effects）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P4266">
<!-- source-paragraph:V82-P4266 style=TableText -->
<pre>1. 相位判断2. 承接继承3. 退场和修复需求</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P4267">
<!-- source-paragraph:V82-P4267 style=TableText -->
<pre>时间窗与时滞（time_window_and_lag）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P4268">
<!-- source-paragraph:V82-P4268 style=TableText -->
<pre>登记相位观察窗、转移时滞、回退与休眠</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P4269">
<!-- source-paragraph:V82-P4269 style=TableText -->
<pre>不确定性（uncertainty）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P4270">
<!-- source-paragraph:V82-P4270 style=TableText -->
<pre>记录混合相位、分裂、合并与尺度差异</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P4271">
<!-- source-paragraph:V82-P4271 style=TableText -->
<pre>局部排除区（local_exclusion_zone）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P4272">
<!-- source-paragraph:V82-P4272 style=TableText -->
<pre>总体相位无法代表的局部群体和角色</pre>
</td>
</tr>
<tr>
<td data-source-cell="10,1" data-paragraphs="V82-P4273">
<!-- source-paragraph:V82-P4273 style=TableText -->
<pre>受影响位置（affected_positions）</pre>
</td>
<td data-source-cell="10,2" data-paragraphs="V82-P4274,V82-P4275,V82-P4276,V82-P4277,V82-P4278">
<!-- source-paragraph:V82-P4274 style=TableText -->
<!-- source-paragraph:V82-P4275 style=TableText -->
<!-- source-paragraph:V82-P4276 style=TableText -->
<!-- source-paragraph:V82-P4277 style=TableText -->
<!-- source-paragraph:V82-P4278 style=TableText -->
<pre>1. 成员
2. 承接者
3. 异议者
4. 退出者
5. 继承者</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P4279 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

## V82-T113

<table data-source-table="V82-T113">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P4280">
<!-- source-paragraph:V82-P4280 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P4281">
<!-- source-paragraph:V82-P4281 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P4282">
<!-- source-paragraph:V82-P4282 style=TableText -->
<pre>承接载体（carrier）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P4283,V82-P4284,V82-P4285,V82-P4286">
<!-- source-paragraph:V82-P4283 style=TableText -->
<!-- source-paragraph:V82-P4284 style=TableText -->
<!-- source-paragraph:V82-P4285 style=TableText -->
<!-- source-paragraph:V82-P4286 style=TableText -->
<pre>1. 集体行动
2. 组织结构
3. 制度记录
4. 共同记忆</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P4287">
<!-- source-paragraph:V82-P4287 style=TableText -->
<pre>责任主体（responsible_subject）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P4288,V82-P4289">
<!-- source-paragraph:V82-P4288 style=TableText -->
<!-- source-paragraph:V82-P4289 style=TableText -->
<pre>1. 作出相位判断的分析者
2. 据此行动的决策与授权者</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P4290">
<!-- source-paragraph:V82-P4290 style=TableText -->
<pre>规范地位（normative_status）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P4291">
<!-- source-paragraph:V82-P4291 style=TableText -->
<pre>相位不构成健康、成功或正当性等级</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P4292">
<!-- source-paragraph:V82-P4292 style=TableText -->
<pre>判断上限（judgment_ceiling）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P4293">
<!-- source-paragraph:V82-P4293 style=TableText -->
<pre>适用条件和相位证据充分时至原型匹配级</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P4294">
<!-- source-paragraph:V82-P4294 style=TableText -->
<pre>行动上限（action_ceiling）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P4295">
<!-- source-paragraph:V82-P4295 style=TableText -->
<pre>本变量只生成相位原型匹配、混合状态、不确定性与观察需求描述，不授权试探、推进、合并、退场或淘汰；任何现实调整须另过C12、运行时显式N前提、J授权与O程序</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P4296">
<!-- source-paragraph:V82-P4296 style=TableText -->
<pre>反例（counterexamples）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P4297,V82-P4298">
<!-- source-paragraph:V82-P4297 style=TableText -->
<!-- source-paragraph:V82-P4298 style=TableText -->
<pre>1. 同一集体同时呈现S2承接成形与S5漏洞积累的混合相位
2. 有序退场X0保持功能转移而不是阶段失败</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P4299">
<!-- source-paragraph:V82-P4299 style=TableText -->
<pre>申诉（appeal）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P4300">
<!-- source-paragraph:V82-P4300 style=TableText -->
<pre>依appeal_and_rollback_rule，成员可经安全可达、反报复通道挑战相位证据、线性假设和道德化使用，并触发与原相位判断或决策链独立的复核</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P4301">
<!-- source-paragraph:V82-P4301 style=TableText -->
<pre>回滚（rollback）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P4302">
<!-- source-paragraph:V82-P4302 style=TableText -->
<pre>依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销相位命名及其下游决策效力、实际恢复变量级描述与未决状态，保留版本与完成验证</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P4303 style=SecH2 -->
## A.11　HV11 开放性承担行动（完整接口卡）

<!-- source-paragraph:V82-P4304 style=CardLabel -->
A. 身份、命题与适用范围

## V82-T114

<table data-source-table="V82-T114">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P4305">
<!-- source-paragraph:V82-P4305 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P4306">
<!-- source-paragraph:V82-P4306 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P4307">
<!-- source-paragraph:V82-P4307 style=TableText -->
<pre>接口 ID（id）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P4308">
<!-- source-paragraph:V82-P4308 style=TableText -->
<pre>HV11</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P4309">
<!-- source-paragraph:V82-P4309 style=TableText -->
<pre>限定 ID（qualified_id）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P4310">
<!-- source-paragraph:V82-P4310 style=TableText -->
<pre>human_variable:HV11</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P4311">
<!-- source-paragraph:V82-P4311 style=TableText -->
<pre>名称（name）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P4312">
<!-- source-paragraph:V82-P4312 style=TableText -->
<pre>开放性承担行动</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P4313">
<!-- source-paragraph:V82-P4313 style=TableText -->
<pre>主张类型（claim_type）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P4314">
<!-- source-paragraph:V82-P4314 style=TableText -->
<pre>H</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P4315">
<!-- source-paragraph:V82-P4315 style=TableText -->
<pre>合同角色（contract_role）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P4316">
<!-- source-paragraph:V82-P4316 style=TableText -->
<pre>human_variable_interface</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P4317">
<!-- source-paragraph:V82-P4317 style=TableText -->
<pre>命题（proposition）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P4318">
<!-- source-paragraph:V82-P4318 style=TableText -->
<pre>开放性承担只观察真实成本、自愿性、方向、替代解释和结构后果，不诊断某人有没有爱。</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P4319">
<!-- source-paragraph:V82-P4319 style=TableText -->
<pre>适用范围（scope）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P4320">
<!-- source-paragraph:V82-P4320 style=TableText -->
<pre>人类关系、组织、制度与公共行动中的承担</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P4321">
<!-- source-paragraph:V82-P4321 style=TableText -->
<pre>暂停条件（pause_condition）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P4322">
<!-- source-paragraph:V82-P4322 style=TableText -->
<pre>无法安全确认自愿、拒绝和退出，或分析转向人格与爱的诊断</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P4323 style=CardLabel -->
B. 正式依赖与推论边界

## V82-T115

<table data-source-table="V82-T115">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P4324">
<!-- source-paragraph:V82-P4324 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P4325">
<!-- source-paragraph:V82-P4325 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P4326">
<!-- source-paragraph:V82-P4326 style=TableText -->
<pre>推论依赖（inferential_requires）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P4327">
<!-- source-paragraph:V82-P4327 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P4328">
<!-- source-paragraph:V82-P4328 style=TableText -->
<pre>协议依赖（protocol_requires）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P4329,V82-P4330,V82-P4331">
<!-- source-paragraph:V82-P4329 style=TableText -->
<!-- source-paragraph:V82-P4330 style=TableText -->
<!-- source-paragraph:V82-P4331 style=TableText -->
<pre>1. N4
2. EVIDENCE
3. SOURCE</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P4332">
<!-- source-paragraph:V82-P4332 style=TableText -->
<pre>限定／特化（specializes）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P4333">
<!-- source-paragraph:V82-P4333 style=TableText -->
<pre>1. H62. H2</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P4334">
<!-- source-paragraph:V82-P4334 style=TableText -->
<pre>适用对象引用（applies_to）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P4335">
<!-- source-paragraph:V82-P4335 style=TableText -->
<pre>无（空集合）</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P4336">
<!-- source-paragraph:V82-P4336 style=TableText -->
<pre>条件支持路由（conditional_support_routes）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P4337,V82-P4338,V82-P4339,V82-P4340,V82-P4341,V82-P4342,V82-P4343,V82-P4344,V82-P4345,V82-P4346,V82-P4347,V82-P4348,V82-P4349,V82-P4350,V82-P4351,V82-P4352,V82-P4353,V82-P4354,V82-P4355,V82-P4356,V82-P4357">
<!-- source-paragraph:V82-P4337 style=TableText -->
<!-- source-paragraph:V82-P4338 style=TableText -->
<!-- source-paragraph:V82-P4339 style=TableText -->
<!-- source-paragraph:V82-P4340 style=TableText -->
<!-- source-paragraph:V82-P4341 style=TableText -->
<!-- source-paragraph:V82-P4342 style=TableText -->
<!-- source-paragraph:V82-P4343 style=TableText -->
<!-- source-paragraph:V82-P4344 style=TableText -->
<!-- source-paragraph:V82-P4345 style=TableText -->
<!-- source-paragraph:V82-P4346 style=TableText -->
<!-- source-paragraph:V82-P4347 style=TableText -->
<!-- source-paragraph:V82-P4348 style=TableText -->
<!-- source-paragraph:V82-P4349 style=TableText -->
<!-- source-paragraph:V82-P4350 style=TableText -->
<!-- source-paragraph:V82-P4351 style=TableText -->
<!-- source-paragraph:V82-P4352 style=TableText -->
<!-- source-paragraph:V82-P4353 style=TableText -->
<!-- source-paragraph:V82-P4354 style=TableText -->
<!-- source-paragraph:V82-P4355 style=TableText -->
<!-- source-paragraph:V82-P4356 style=TableText -->
<!-- source-paragraph:V82-P4357 style=TableText -->
<pre>1. route_id=HV11-R0-action-cost-record；
claim_level=normative_boundary；
when=行动、真实成本、方向、替代解释、受益与后果可观察，但自愿性、拒绝或退出尚不充分。；
additional_inferential_requires=无（空集合）；
additional_protocol_requires=无（空集合）；
allowed_conclusion=描述候选承担行动、成本分布、强制风险、停止权缺口与保护需求。；
result_ceiling=不得称开放性承担，不得诊断爱、人格或要求继续承担。
2. route_id=HV11-R1-voluntary-limited-action；
claim_level=normative_boundary；
when=真实成本、自愿性、真实拒绝与退出、方向、替代解释和结构后果均分别可见。；
additional_inferential_requires=无（空集合）；
additional_protocol_requires=无（空集合）；
allowed_conclusion=登记有限、自愿且具有方向和可观察后果的开放性承担行动描述。；
result_ceiling=只到行动描述；不把个体承担升格为群体义务，也不授权征用、保护或资源安排。
3. route_id=HV11-R2-structural-consequence；
claim_level=conditional_effect；
when=符合资格的G2-instance显示该行动经指定通道对预选结构结果产生超过阈值的效应。；
additional_inferential_requires=G2-instance；
additional_protocol_requires=CAUSAL、E4；
allowed_conclusion=登记指定通道、对象与窗口内的行动结构后果。；
result_ceiling=结构效应不证明爱、善、正当性、无限责任或行动授权。</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P4358">
<!-- source-paragraph:V82-P4358 style=TableText -->
<pre>允许推论（allowed_inference）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P4359">
<!-- source-paragraph:V82-P4359 style=TableText -->
<pre>1. 描述有限承担行动与后果</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P4360">
<!-- source-paragraph:V82-P4360 style=TableText -->
<pre>禁止跳跃（prohibited_leap）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P4361,V82-P4362,V82-P4363,V82-P4364">
<!-- source-paragraph:V82-P4361 style=TableText -->
<!-- source-paragraph:V82-P4362 style=TableText -->
<!-- source-paragraph:V82-P4363 style=TableText -->
<!-- source-paragraph:V82-P4364 style=TableText -->
<pre>1. 诊断有没有爱
2. 牺牲等于爱
3. 责任等于无限承担
4. 拒绝等于道德失败</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P4365 style=CardLabel -->
C. 九轴尺度与对象合同

## V82-T116

<table data-source-table="V82-T116">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P4366">
<!-- source-paragraph:V82-P4366 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P4367">
<!-- source-paragraph:V82-P4367 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P4368">
<!-- source-paragraph:V82-P4368 style=TableText -->
<pre>九轴尺度画像（scale_profile）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P4369">
<!-- source-paragraph:V82-P4369 style=TableText -->
<pre>SP=&lt;A,X,T,O,C,R,I,N,J&gt;；A=聚合层次：单次承担行动、行动者个案、关系或组织总体、成本自愿性分布及聚合规则；X=空间范围：关系与照护现场、组织边界、数字公共空间与跨域受益范围；T=时间跨度：即时行动、持续承担、耗竭、恢复与代际窗口；O=组织层级：行动角色、关系或团队、组织、制度至治理生态；C=因果层次：承担事件、行动—成本互动机制、中观关系结构、制度责任安排与系统条件；R=观察分辨率：原始行动与成本、承担序列、行动者个案、成本自愿性分布、后果指标与摘要，并登记压缩损失；I=影响范围：直接行动者与受益者、依赖者、间接替代承接者、二阶外溢、跨域与代际影响；N=网络拓扑范围：依赖照护、受益连接、替代承接、退出路径与跨域成本网络；J=管辖与授权范围：承担要求、资源使用、拒绝、停止、保护与补救分别登记授权；保留自愿成本退出差异</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P4370">
<!-- source-paragraph:V82-P4370 style=TableText -->
<pre>有效对象（effective_object）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P4371">
<!-- source-paragraph:V82-P4371 style=TableText -->
<pre>满足真实成本、自愿性、方向和结构后果条件的人类行动</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P4372">
<!-- source-paragraph:V82-P4372 style=TableText -->
<pre>跨尺度保持项（scale_invariants）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P4373">
<!-- source-paragraph:V82-P4373 style=TableText -->
<pre>1. 成本、自愿性、方向、替代解释、后果与停止权</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P4374">
<!-- source-paragraph:V82-P4374 style=TableText -->
<pre>升格必补项（required_scale_additions）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P4375,V82-P4376,V82-P4377,V82-P4378">
<!-- source-paragraph:V82-P4375 style=TableText -->
<!-- source-paragraph:V82-P4376 style=TableText -->
<!-- source-paragraph:V82-P4377 style=TableText -->
<!-- source-paragraph:V82-P4378 style=TableText -->
<pre>1. 自愿性分布
2. 代表关系
3. 成本外溢
4. 真实退出与代理保护</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P4379">
<!-- source-paragraph:V82-P4379 style=TableText -->
<pre>随尺度改变项（changing_semantics）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P4380">
<!-- source-paragraph:V82-P4380 style=TableText -->
<pre>1. 承担形式、成本位置和受益对象可改变</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P4381">
<!-- source-paragraph:V82-P4381 style=TableText -->
<pre>不适用对象（non_applicable_objects）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P4382">
<!-- source-paragraph:V82-P4382 style=TableText -->
<pre>1. 无意向、自愿性、责任或意义能力的非人系统</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P4383">
<!-- source-paragraph:V82-P4383 style=TableText -->
<pre>禁止升格（forbidden_elevation）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P4384,V82-P4385">
<!-- source-paragraph:V82-P4384 style=TableText -->
<!-- source-paragraph:V82-P4385 style=TableText -->
<pre>1. 个体承担升格为群体义务
2. 人类承担概念迁入非人核心</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P4386 style=CardLabel -->
D. 状态、证据与变量流

## V82-T117

<table data-source-table="V82-T117">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P4387">
<!-- source-paragraph:V82-P4387 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P4388">
<!-- source-paragraph:V82-P4388 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P4389">
<!-- source-paragraph:V82-P4389 style=TableText -->
<pre>状态集合（state）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P4390,V82-P4391,V82-P4392,V82-P4393,V82-P4394">
<!-- source-paragraph:V82-P4390 style=TableText -->
<!-- source-paragraph:V82-P4391 style=TableText -->
<!-- source-paragraph:V82-P4392 style=TableText -->
<!-- source-paragraph:V82-P4393 style=TableText -->
<!-- source-paragraph:V82-P4394 style=TableText -->
<pre>1. 候选
2. 自愿且有限
3. 强制风险
4. 单方耗竭
5. 停止或退出</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P4395">
<!-- source-paragraph:V82-P4395 style=TableText -->
<pre>可观测项（observables）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P4396,V82-P4397,V82-P4398,V82-P4399">
<!-- source-paragraph:V82-P4396 style=TableText -->
<!-- source-paragraph:V82-P4397 style=TableText -->
<!-- source-paragraph:V82-P4398 style=TableText -->
<!-- source-paragraph:V82-P4399 style=TableText -->
<pre>1. 行动投入的时间、资源、机会与身体心理成本
2. 拒绝、退出、停止和重新协商是否真实可用
3. 行动方向、受益位置和可检测结构后果
4. 强制、恐惧、依赖、利益与表演等替代解释</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P4400">
<!-- source-paragraph:V82-P4400 style=TableText -->
<pre>证据要求（evidence）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P4401,V82-P4402,V82-P4403,V82-P4404">
<!-- source-paragraph:V82-P4401 style=TableText -->
<!-- source-paragraph:V82-P4402 style=TableText -->
<!-- source-paragraph:V82-P4403 style=TableText -->
<!-- source-paragraph:V82-P4404 style=TableText -->
<pre>1. 行动与成本
2. 拒绝和退出条件
3. 替代解释
4. 受益与后果</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P4405">
<!-- source-paragraph:V82-P4405 style=TableText -->
<pre>输入依赖与接口内容（input_dependencies）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P4406,V82-P4407,V82-P4408,V82-P4409">
<!-- source-paragraph:V82-P4406 style=TableText -->
<!-- source-paragraph:V82-P4407 style=TableText -->
<!-- source-paragraph:V82-P4408 style=TableText -->
<!-- source-paragraph:V82-P4409 style=TableText -->
<pre>1. 指向锚点
2. 承接层
3. 条件势场
4. 权力与安全</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P4410">
<!-- source-paragraph:V82-P4410 style=TableText -->
<pre>输出效应与变量流（output_effects）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P4411,V82-P4412,V82-P4413">
<!-- source-paragraph:V82-P4411 style=TableText -->
<!-- source-paragraph:V82-P4412 style=TableText -->
<!-- source-paragraph:V82-P4413 style=TableText -->
<pre>1. 成本分布
2. 关系和制度状态
3. 停止与修复</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P4414">
<!-- source-paragraph:V82-P4414 style=TableText -->
<pre>时间窗与时滞（time_window_and_lag）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P4415">
<!-- source-paragraph:V82-P4415 style=TableText -->
<pre>登记即时成本、持续承担、耗竭与恢复时滞</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P4416">
<!-- source-paragraph:V82-P4416 style=TableText -->
<pre>不确定性（uncertainty）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P4417">
<!-- source-paragraph:V82-P4417 style=TableText -->
<pre>记录依赖、恐惧、隐性强制与表达安全</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P4418">
<!-- source-paragraph:V82-P4418 style=TableText -->
<pre>局部排除区（local_exclusion_zone）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P4419">
<!-- source-paragraph:V82-P4419 style=TableText -->
<pre>无法安全拒绝、无法退出或被道德压力遮蔽的位置</pre>
</td>
</tr>
<tr>
<td data-source-cell="10,1" data-paragraphs="V82-P4420">
<!-- source-paragraph:V82-P4420 style=TableText -->
<pre>受影响位置（affected_positions）</pre>
</td>
<td data-source-cell="10,2" data-paragraphs="V82-P4421,V82-P4422,V82-P4423,V82-P4424">
<!-- source-paragraph:V82-P4421 style=TableText -->
<!-- source-paragraph:V82-P4422 style=TableText -->
<!-- source-paragraph:V82-P4423 style=TableText -->
<!-- source-paragraph:V82-P4424 style=TableText -->
<pre>1. 行动者
2. 受益者
3. 依赖者
4. 替代承接者</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P4425 style=CardLabel -->
E. 承接、责任、规范、上限与纠错

## V82-T118

<table data-source-table="V82-T118">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P4426">
<!-- source-paragraph:V82-P4426 style=TableHead -->
<pre>字段</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P4427">
<!-- source-paragraph:V82-P4427 style=TableHead -->
<pre>登记内容</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P4428">
<!-- source-paragraph:V82-P4428 style=TableText -->
<pre>承接载体（carrier）</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P4429,V82-P4430,V82-P4431">
<!-- source-paragraph:V82-P4429 style=TableText -->
<!-- source-paragraph:V82-P4430 style=TableText -->
<!-- source-paragraph:V82-P4431 style=TableText -->
<pre>1. 具体行动者
2. 关系实践
3. 照护或责任安排</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P4432">
<!-- source-paragraph:V82-P4432 style=TableText -->
<pre>责任主体（responsible_subject）</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P4433,V82-P4434,V82-P4435,V82-P4436">
<!-- source-paragraph:V82-P4433 style=TableText -->
<!-- source-paragraph:V82-P4434 style=TableText -->
<!-- source-paragraph:V82-P4435 style=TableText -->
<!-- source-paragraph:V82-P4436 style=TableText -->
<pre>1. 提出要求者
2. 授权者
3. 受益责任者
4. 补救责任者</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P4437">
<!-- source-paragraph:V82-P4437 style=TableText -->
<pre>规范地位（normative_status）</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P4438">
<!-- source-paragraph:V82-P4438 style=TableText -->
<pre>受N4约束，不可命令或征用</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P4439">
<!-- source-paragraph:V82-P4439 style=TableText -->
<pre>判断上限（judgment_ceiling）</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P4440">
<!-- source-paragraph:V82-P4440 style=TableText -->
<pre>证据充分时只到行动描述级，不进入人格诊断</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P4441">
<!-- source-paragraph:V82-P4441 style=TableText -->
<pre>行动上限（action_ceiling）</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P4442">
<!-- source-paragraph:V82-P4442 style=TableText -->
<pre>本变量只生成自愿性、真实成本、方向、替代解释、结构后果与停止保护需求描述，不授权保护措施、承担要求、资源征用或人格裁决；任何现实调整须另过C12、运行时显式N前提、J授权与O程序</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P4443">
<!-- source-paragraph:V82-P4443 style=TableText -->
<pre>反例（counterexamples）</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P4444,V82-P4445">
<!-- source-paragraph:V82-P4444 style=TableText -->
<!-- source-paragraph:V82-P4445 style=TableText -->
<pre>1. 无法拒绝的单方牺牲被赞美为爱或责任
2. 承担宣称没有真实成本、行动方向或可检测结构后果</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P4446">
<!-- source-paragraph:V82-P4446 style=TableText -->
<pre>申诉（appeal）</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P4447">
<!-- source-paragraph:V82-P4447 style=TableText -->
<pre>依appeal_and_rollback_rule，行动者可经安全可达、反报复通道拒绝被代表，说明强制、成本、替代解释和退出限制，并触发与原承担判断或要求链独立的复核</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P4448">
<!-- source-paragraph:V82-P4448 style=TableText -->
<pre>回滚（rollback）</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P4449">
<!-- source-paragraph:V82-P4449 style=TableText -->
<pre>依appeal_and_rollback_rule，获准回滚时，由指定责任人在规定时限内撤销承担命名与相关要求，实际恢复拒绝、退出、记录和资源状态，保留版本与完成验证</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P4450 style=BodyCJK -->
scale_profile 不是“微观—宏观”的单轴标签，而是 SP=&lt;A,X,T,O,C,R,I,N,J&gt; 的完整九轴记录：A 是聚合层次，必须声明单元、总体、分布和聚合规则；X 是物理空间与数字边界；T 是窗口、时滞和周期；O 是角色、团队、组织、制度与治理生态的组织层级；C 是事件、互动机制、中观结构、制度和系统条件的因果层次；R 是原始事件、序列、个案、分布、指标与摘要的观察分辨率，并记录压缩损失；I 是直接、间接、二阶、跨域与代际的受影响范围；N 是网络拓扑范围；J 是管辖与授权范围。扩大 A、X、O 或 I 不会自动扩大 J；观察更多不能产生更大处置权。

<!-- source-paragraph:V82-P4451 style=BodyCJK -->
身份与同一性判据属于对象合同 K，关系与作用通道进入 input_dependencies、carrier 或因果合同，成员与受影响位置进入 affected_positions、local_exclusion_zone 和观察字段；它们都不能冒充尺度轴。尺度轴 N 指网络拓扑；下文“运行时显式 N 前提”指规范选择层 N1-N5，两者不可混用。

<!-- source-paragraph:V82-P4452 style=BodyCJK -->
十一项变量共享同一行动边界：变量本身只生成描述、证据缺口与行动需求，不授权现实调整。其输出上限如下。

## V82-T119

<table data-source-table="V82-T119">
<tr>
<td data-source-cell="1,1" data-paragraphs="V82-P4453">
<!-- source-paragraph:V82-P4453 style=TableHead -->
<pre>变量</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V82-P4454">
<!-- source-paragraph:V82-P4454 style=TableHead -->
<pre>本变量可生成的描述或需求</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V82-P4455">
<!-- source-paragraph:V82-P4455 style=TableText -->
<pre>HV01</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V82-P4456">
<!-- source-paragraph:V82-P4456 style=TableText -->
<pre>候选结构域、边界争议与补证需求</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V82-P4457">
<!-- source-paragraph:V82-P4457 style=TableText -->
<pre>HV02</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V82-P4458">
<!-- source-paragraph:V82-P4458 style=TableText -->
<pre>边界状态、接口障碍、排除风险与测试需求</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V82-P4459">
<!-- source-paragraph:V82-P4459 style=TableText -->
<pre>HV03</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V82-P4460">
<!-- source-paragraph:V82-P4460 style=TableText -->
<pre>候选锚点、异质表达、比较结果与补证需求</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V82-P4461">
<!-- source-paragraph:V82-P4461 style=TableText -->
<pre>HV04</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V82-P4462">
<!-- source-paragraph:V82-P4462 style=TableText -->
<pre>GC、GS、GE 候选分型、状态转移与补证需求</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V82-P4463">
<!-- source-paragraph:V82-P4463 style=TableText -->
<pre>HV05</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V82-P4464">
<!-- source-paragraph:V82-P4464 style=TableText -->
<pre>CV、RS、成本、容量、停止权、承接缺口及减载、补资源或重分配需求</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V82-P4465">
<!-- source-paragraph:V82-P4465 style=TableText -->
<pre>HV06</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V82-P4466">
<!-- source-paragraph:V82-P4466 style=TableText -->
<pre>链条连通、时滞、损耗、中断、成本与承接需求</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V82-P4467">
<!-- source-paragraph:V82-P4467 style=TableText -->
<pre>HV07</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V82-P4468">
<!-- source-paragraph:V82-P4468 style=TableText -->
<pre>受理、字段变化、执行、持续时间、写回缺口与程序修复需求</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V82-P4469">
<!-- source-paragraph:V82-P4469 style=TableText -->
<pre>HV08</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V82-P4470">
<!-- source-paragraph:V82-P4470 style=TableText -->
<pre>候选条件通道、位置异质性、证据遮蔽与风险降低需求</pre>
</td>
</tr>
<tr>
<td data-source-cell="10,1" data-paragraphs="V82-P4471">
<!-- source-paragraph:V82-P4471 style=TableText -->
<pre>HV09</pre>
</td>
<td data-source-cell="10,2" data-paragraphs="V82-P4472">
<!-- source-paragraph:V82-P4472 style=TableText -->
<pre>负荷、容量、恢复、局部过载与减载补资源需求</pre>
</td>
</tr>
<tr>
<td data-source-cell="11,1" data-paragraphs="V82-P4473">
<!-- source-paragraph:V82-P4473 style=TableText -->
<pre>HV10</pre>
</td>
<td data-source-cell="11,2" data-paragraphs="V82-P4474">
<!-- source-paragraph:V82-P4474 style=TableText -->
<pre>相位原型匹配、混合状态、不确定性与观察需求</pre>
</td>
</tr>
<tr>
<td data-source-cell="12,1" data-paragraphs="V82-P4475">
<!-- source-paragraph:V82-P4475 style=TableText -->
<pre>HV11</pre>
</td>
<td data-source-cell="12,2" data-paragraphs="V82-P4476">
<!-- source-paragraph:V82-P4476 style=TableText -->
<pre>自愿性、真实成本、方向、替代解释、结构后果与停止保护需求</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V82-P4477 style=BodyCJK -->
无论需求看起来多么明显，任何现实调整都须另过 C12、运行时显式 N 前提、J 授权与 O 程序。变量不得自行授权测试、减载、补资源、修复、保护、归责、试探、推进、退出安排或处置。
