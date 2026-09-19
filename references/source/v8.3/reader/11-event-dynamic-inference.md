# 第十一部分　事件驱动的动态推演

Source: `v8.3`
Raw SHA256: `4a3ad8e8692b7a906f733096bbc8e05d0ac4f8cfbf79d3926eb1729df828c7f5`
Semantic SHA256: `f190a80be88033ba21d717a310f4419c00489b3a6dea17b6a1e2b14af1447d9f`
List structure SHA256: `967dd396860e4b5d246ae2e3699eb33b8ab8ee46ca12bb72959e1249216d7a5f`
Paragraph range: `V83-P1931`-`V83-P2131`
Tables: `V83-T042`, `V83-T043`, `V83-T044`, `V83-T045`, `V83-T046`, `V83-T047`

<!-- This is a lossless reader edition; anchors are source coordinates. -->

<!-- source-paragraph:V83-P1931 style=PartTitle -->
# 第十一部分　事件驱动的动态推演

<!-- source-paragraph:V83-P1932 style=BodyCJK -->
动态推演回答的不是“世界接下来一定会怎样”，而是：从一个冻结的联合状态出发，在某个观察事件、情景事件或已授权行动发生后，哪些变量会先改变，影响沿什么通道传播，何处出现时延、阈值、反馈、跨圈层级联与分叉，哪些信号会提高或降低某条路径的支持度。

<!-- source-paragraph:V83-P1933 style=SecH2 -->
## 11.1　推演与叙事续写的区别

<!-- source-paragraph:V83-P1934 style=BodyCJK -->
叙事续写可以凭连贯性选择一个后续；结构推演必须保留条件、通道、竞争路径和失败语义。若缺少关键变量，推演应停在未知或生成变量候选，而不是用最顺畅的故事补齐。若多个后续都与现有证据一致，就保持分叉；若路径无法比较，就不强制排序。

<!-- source-paragraph:V83-P1935 style=BodyCJK -->
推演的最小输入为冻结快照、事件记录、机制假设、参数范围、时钟政策、传播政策、未知项和停止条件。最小输出为路径图、每一步状态差、支持状态、早期信号、反向信号、残差、变量候选和回写要求。

## V83-T042

<table data-source-table="V83-T042">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P1936">
<!-- source-paragraph:V83-P1936 style=TableHead -->
<pre>输入</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P1937">
<!-- source-paragraph:V83-P1937 style=TableHead -->
<pre>必须冻结的内容</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P1938">
<!-- source-paragraph:V83-P1938 style=TableHead -->
<pre>不冻结的后果</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P1939">
<!-- source-paragraph:V83-P1939 style=TableText -->
<pre>联合快照</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P1940">
<!-- source-paragraph:V83-P1940 style=TableText -->
<pre>行动者、圈层、关系、M/Ψ、时钟、证据截止</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P1941">
<!-- source-paragraph:V83-P1941 style=TableText -->
<pre>结果后改写起点</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P1942">
<!-- source-paragraph:V83-P1942 style=TableText -->
<pre>事件</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P1943">
<!-- source-paragraph:V83-P1943 style=TableText -->
<pre>类型、时间、来源、触达对象与通道</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P1944">
<!-- source-paragraph:V83-P1944 style=TableText -->
<pre>把传闻、计划和事实混装</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P1945">
<!-- source-paragraph:V83-P1945 style=TableText -->
<pre>机制</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P1946">
<!-- source-paragraph:V83-P1946 style=TableText -->
<pre>方向、载体、时延、阈值、失效条件</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P1947">
<!-- source-paragraph:V83-P1947 style=TableText -->
<pre>任意解释每个结果</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V83-P1948">
<!-- source-paragraph:V83-P1948 style=TableText -->
<pre>参数</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V83-P1949">
<!-- source-paragraph:V83-P1949 style=TableText -->
<pre>值、区间、等级或明确未知</pre>
</td>
<td data-source-cell="5,3" data-paragraphs="V83-P1950">
<!-- source-paragraph:V83-P1950 style=TableText -->
<pre>用伪精确掩盖不确定</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V83-P1951">
<!-- source-paragraph:V83-P1951 style=TableText -->
<pre>停止</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V83-P1952">
<!-- source-paragraph:V83-P1952 style=TableText -->
<pre>信息、风险、越界与资源条件</pre>
</td>
<td data-source-cell="6,3" data-paragraphs="V83-P1953">
<!-- source-paragraph:V83-P1953 style=TableText -->
<pre>无限制向后讲故事</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P1954 style=SecH2 -->
## 11.2　事件合同

<!-- source-paragraph:V83-P1955 style=BodyCJK -->
事件包括观察到、被报告、计划中、假设性和模拟五类。类型必须进入记录：被报告的事件可以影响相信它的人，但不能自动当作已发生；计划可能改变预期，却不等于执行；假设事件用于条件分析；模拟事件只属于模型运行，不能回写现实事实。

<!-- source-paragraph:V83-P1956 style=BodyCJK -->
事件记录至少包含：事件 ID、发生时间或窗口、观察时间、来源、受影响行动者、受影响圈层、通道、直接变化、证据状态、争议、竞争解释、可逆性、持续时间和后续观测。

## V83-T043

<table data-source-table="V83-T043">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P1957">
<!-- source-paragraph:V83-P1957 style=TableHead -->
<pre>事件类型</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P1958">
<!-- source-paragraph:V83-P1958 style=TableHead -->
<pre>可以进入哪种推演</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P1959">
<!-- source-paragraph:V83-P1959 style=TableHead -->
<pre>事实地位</pre>
</td>
<td data-source-cell="1,4" data-paragraphs="V83-P1960">
<!-- source-paragraph:V83-P1960 style=TableHead -->
<pre>必须附加的限制</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P1961">
<!-- source-paragraph:V83-P1961 style=TableText -->
<pre>观察到</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P1962">
<!-- source-paragraph:V83-P1962 style=TableText -->
<pre>解释、回放、前向推演</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P1963">
<!-- source-paragraph:V83-P1963 style=TableText -->
<pre>在观察合同内成立</pre>
</td>
<td data-source-cell="2,4" data-paragraphs="V83-P1964">
<!-- source-paragraph:V83-P1964 style=TableText -->
<pre>来源、遗漏和测量误差</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P1965">
<!-- source-paragraph:V83-P1965 style=TableText -->
<pre>被报告</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P1966">
<!-- source-paragraph:V83-P1966 style=TableText -->
<pre>信念传播和条件推演</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P1967">
<!-- source-paragraph:V83-P1967 style=TableText -->
<pre>报告发生，不等于内容为真</pre>
</td>
<td data-source-cell="3,4" data-paragraphs="V83-P1968">
<!-- source-paragraph:V83-P1968 style=TableText -->
<pre>报告者位置、核验和争议</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P1969">
<!-- source-paragraph:V83-P1969 style=TableText -->
<pre>计划中</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P1970">
<!-- source-paragraph:V83-P1970 style=TableText -->
<pre>预期、准备与策略互动</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P1971">
<!-- source-paragraph:V83-P1971 style=TableText -->
<pre>计划存在，不等于执行</pre>
</td>
<td data-source-cell="4,4" data-paragraphs="V83-P1972">
<!-- source-paragraph:V83-P1972 style=TableText -->
<pre>授权、资源和取消条件</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V83-P1973">
<!-- source-paragraph:V83-P1973 style=TableText -->
<pre>假设性</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V83-P1974">
<!-- source-paragraph:V83-P1974 style=TableText -->
<pre>反事实与情景比较</pre>
</td>
<td data-source-cell="5,3" data-paragraphs="V83-P1975">
<!-- source-paragraph:V83-P1975 style=TableText -->
<pre>非现实事实</pre>
</td>
<td data-source-cell="5,4" data-paragraphs="V83-P1976">
<!-- source-paragraph:V83-P1976 style=TableText -->
<pre>条件、目的和可实现性</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V83-P1977">
<!-- source-paragraph:V83-P1977 style=TableText -->
<pre>模拟</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V83-P1978">
<!-- source-paragraph:V83-P1978 style=TableText -->
<pre>模型内部路径展开</pre>
</td>
<td data-source-cell="6,3" data-paragraphs="V83-P1979">
<!-- source-paragraph:V83-P1979 style=TableText -->
<pre>仅模型状态</pre>
</td>
<td data-source-cell="6,4" data-paragraphs="V83-P1980">
<!-- source-paragraph:V83-P1980 style=TableText -->
<pre>模型版本、参数和禁止外推</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P1981 style=SecH2 -->
## 11.3　联合状态更新式

<!-- source-paragraph:V83-P1982 style=BodyCJK -->
联合状态可写为：

<!-- source-paragraph:V83-P1983 style=BodyCJK -->
Ω(t) = &lt;A(t), C(t), R(t), M(t), Ψ(t), Q(t), E≤t, SP(t), W(t), K(t)&gt;。

<!-- source-paragraph:V83-P1984 style=BodyCJK -->
一次更新可写为：

<!-- source-paragraph:V83-P1985 style=BodyCJK -->
Ω(t+Δ) = F[Ω(t), e(t), u(t), ξ(t) | θ, h]。

<!-- source-paragraph:V83-P1986 style=BodyCJK -->
e(t) 是事件，u(t) 是已获外部授权且实际发生的行动，ξ(t) 是外生扰动或未建模残差，θ 是冻结的机制与参数假设，h 是历史项。这个式子只规定记录责任，不宣称存在唯一真实的 F，也不允许用函数符号替代具体机制。

<!-- source-paragraph:V83-P1987 style=BodyCJK -->
每次更新都要区分：直接观察的状态差；由机制合同支持的推断；为探索路径设定的情景值；尚未解释的残差。四者在后续路径中保持来源，不因共同出现在一个快照中而获得相同证据地位。

<!-- source-paragraph:V83-P1988 style=SecH2 -->
## 11.4　九步推演闭环

<!-- source-paragraph:V83-P1989 style=SecH3 -->
### 11.4.1　第一步：冻结当前状态

<!-- source-paragraph:V83-P1990 style=BodyCJK -->
记录证据截止、对象、变量、未知、争议和模型版本。截止后获得的信息不能倒灌到起点；若需使用，建立新运行版本。

<!-- source-paragraph:V83-P1991 style=SecH3 -->
### 11.4.2　第二步：识别行动者与圈层

<!-- source-paragraph:V83-P1992 style=BodyCJK -->
调用第九、十部分。圈层不足以获得对象支持时保留候选分组；人格不足以获得支持时保留变量候选。不能为了使图完整而强行实体化。

<!-- source-paragraph:V83-P1993 style=SecH3 -->
### 11.4.3　第三步：分离双通道条件

<!-- source-paragraph:V83-P1994 style=BodyCJK -->
把物质条件和体验—意义条件分别列出，并声明可能的跨通道桥。若只有一种条件有证据，另一种保持未知，不用对称假设补齐。

<!-- source-paragraph:V83-P1995 style=SecH3 -->
### 11.4.4　第四步：声明时钟、阈值、容量与时延

<!-- source-paragraph:V83-P1996 style=BodyCJK -->
每个变量标明更新时钟。通道若有容量、延迟、损耗、饱和、反转或恢复窗口，应在传播前登记。

<!-- source-paragraph:V83-P1997 style=SecH3 -->
### 11.4.5　第五步：注入事件或行动

<!-- source-paragraph:V83-P1998 style=BodyCJK -->
一次运行可以包含多个按时间排序的事件，但每个事件必须保留独立记录。行动必须有外部授权引用；没有授权时只能作为假设情景，而不能写成待执行指令。未获执行授权不阻止在明确目标、规范前提、代价与限制下推荐供审议的方案；推荐须与事件身份和实际执行状态分开。

<!-- source-paragraph:V83-P1999 style=SecH3 -->
### 11.4.6　第六步：沿已声明通道传播

<!-- source-paragraph:V83-P2000 style=BodyCJK -->
先记录直接效应，再记录返回信号、间接效应和跨圈层级联。没有通道的影响保持候选，不因相关同时出现而连接。

<!-- source-paragraph:V83-P2001 style=SecH3 -->
### 11.4.7　第七步：在分叉点生成路径

<!-- source-paragraph:V83-P2002 style=BodyCJK -->
条件、阈值、行动者选择、外部扰动或机制不确定都可能产生分叉。互斥路径分开；可以同时发生的路径保留并行；只有合并条件明确时才建立汇合节点。

<!-- source-paragraph:V83-P2003 style=SecH3 -->
### 11.4.8　第八步：登记信号、残差与变量候选

<!-- source-paragraph:V83-P2004 style=BodyCJK -->
每条路径列出早期信号和反向信号。无法由当前变量解释的状态差进入残差；残差可以触发变量候选账本，但不能自动生成现实取值。

<!-- source-paragraph:V83-P2005 style=SecH3 -->
### 11.4.9　第九步：结果回写

<!-- source-paragraph:V83-P2006 style=BodyCJK -->
真实结果到来后追加记录：哪条路径得到支持，哪些时点偏离，简单基线是否更好，校准如何，哪些机制或变量应降级、分裂、修改边界或退役。回写不覆盖原运行。

<!-- source-paragraph:V83-P2007 style=SecH2 -->
## 11.5　传播、时延与阈值

<!-- source-paragraph:V83-P2008 style=BodyCJK -->
传播至少区分信号到达和有效状态改变。信息被看到但没有改变后续转移，只登记到达；改变了信念但没有行动，登记体验—意义状态变化；改变了资源、行为、规则或关系，才登记相应结构变化。

## V83-T044

<table data-source-table="V83-T044">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P2009">
<!-- source-paragraph:V83-P2009 style=TableHead -->
<pre>传播要素</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P2010">
<!-- source-paragraph:V83-P2010 style=TableHead -->
<pre>记录问题</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P2011">
<!-- source-paragraph:V83-P2011 style=TableHead -->
<pre>可能的非线性</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P2012">
<!-- source-paragraph:V83-P2012 style=TableText -->
<pre>通道</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P2013">
<!-- source-paragraph:V83-P2013 style=TableText -->
<pre>什么载体把影响从源带到目标</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P2014">
<!-- source-paragraph:V83-P2014 style=TableText -->
<pre>通道关闭、过滤或替代</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P2015">
<!-- source-paragraph:V83-P2015 style=TableText -->
<pre>容量</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P2016">
<!-- source-paragraph:V83-P2016 style=TableText -->
<pre>单位时间可承载多少</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P2017">
<!-- source-paragraph:V83-P2017 style=TableText -->
<pre>饱和、拥堵、排队</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P2018">
<!-- source-paragraph:V83-P2018 style=TableText -->
<pre>时延</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P2019">
<!-- source-paragraph:V83-P2019 style=TableText -->
<pre>何时到达、何时产生效果</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P2020">
<!-- source-paragraph:V83-P2020 style=TableText -->
<pre>延迟反馈、误判无效</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V83-P2021">
<!-- source-paragraph:V83-P2021 style=TableText -->
<pre>阈值</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V83-P2022">
<!-- source-paragraph:V83-P2022 style=TableText -->
<pre>达到什么条件才改变状态</pre>
</td>
<td data-source-cell="5,3" data-paragraphs="V83-P2023">
<!-- source-paragraph:V83-P2023 style=TableText -->
<pre>突变、迟滞、级联</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V83-P2024">
<!-- source-paragraph:V83-P2024 style=TableText -->
<pre>损耗</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V83-P2025">
<!-- source-paragraph:V83-P2025 style=TableText -->
<pre>传播中丢失或转化什么</pre>
</td>
<td data-source-cell="6,3" data-paragraphs="V83-P2026">
<!-- source-paragraph:V83-P2026 style=TableText -->
<pre>意义漂移、资源耗散</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V83-P2027">
<!-- source-paragraph:V83-P2027 style=TableText -->
<pre>方向</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V83-P2028">
<!-- source-paragraph:V83-P2028 style=TableText -->
<pre>影响是否对称</pre>
</td>
<td data-source-cell="7,3" data-paragraphs="V83-P2029">
<!-- source-paragraph:V83-P2029 style=TableText -->
<pre>单向依赖、反向抵消</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V83-P2030">
<!-- source-paragraph:V83-P2030 style=TableText -->
<pre>恢复</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V83-P2031">
<!-- source-paragraph:V83-P2031 style=TableText -->
<pre>冲击后如何回到或转到新状态</pre>
</td>
<td data-source-cell="8,3" data-paragraphs="V83-P2032">
<!-- source-paragraph:V83-P2032 style=TableText -->
<pre>弹性、累积损伤、锁定</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P2033 style=BodyCJK -->
同一事件经不同通道到达不同圈层时，效果可以相反。资源增加可能降低一个圈层的负荷，却提高另一个圈层的竞争；公开说明可能修复外部合法性，却激活内部羞耻或不信任。推演应逐通道记录，不能用净效应掩盖分配差异。

<!-- source-paragraph:V83-P2034 style=SecH2 -->
## 11.6　反馈与跨圈层级联

<!-- source-paragraph:V83-P2035 style=BodyCJK -->
反馈要求先前状态或输出经返回通道改变后续状态、转移概率或约束。级联要求一个局部变化经成员重叠、桥接、共享资源、制度下行或网络传播触发其他圈层变化。两者都要有时间顺序和通道证据。

## V83-T045

<table data-source-table="V83-T045">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P2036">
<!-- source-paragraph:V83-P2036 style=TableHead -->
<pre>级联类型</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P2037">
<!-- source-paragraph:V83-P2037 style=TableHead -->
<pre>典型链条</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P2038">
<!-- source-paragraph:V83-P2038 style=TableHead -->
<pre>观察重点</pre>
</td>
<td data-source-cell="1,4" data-paragraphs="V83-P2039">
<!-- source-paragraph:V83-P2039 style=TableHead -->
<pre>停止条件</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P2040">
<!-- source-paragraph:V83-P2040 style=TableText -->
<pre>成员级联</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P2041">
<!-- source-paragraph:V83-P2041 style=TableText -->
<pre>重叠成员把行为、情绪或信息带入另一圈层</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P2042">
<!-- source-paragraph:V83-P2042 style=TableText -->
<pre>真实传导而非共同背景</pre>
</td>
<td data-source-cell="2,4" data-paragraphs="V83-P2043">
<!-- source-paragraph:V83-P2043 style=TableText -->
<pre>成员不再参与或信息未被接收</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P2044">
<!-- source-paragraph:V83-P2044 style=TableText -->
<pre>资源级联</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P2045">
<!-- source-paragraph:V83-P2045 style=TableText -->
<pre>一个圈层占用、释放或重配资源</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P2046">
<!-- source-paragraph:V83-P2046 style=TableText -->
<pre>会计边界、转换和损耗</pre>
</td>
<td data-source-cell="3,4" data-paragraphs="V83-P2047">
<!-- source-paragraph:V83-P2047 style=TableText -->
<pre>资源隔离或替代来源</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P2048">
<!-- source-paragraph:V83-P2048 style=TableText -->
<pre>意义级联</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P2049">
<!-- source-paragraph:V83-P2049 style=TableText -->
<pre>事件解释改变身份、合法性或信任</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P2050">
<!-- source-paragraph:V83-P2050 style=TableText -->
<pre>不同位置的解释差异</pre>
</td>
<td data-source-cell="4,4" data-paragraphs="V83-P2051">
<!-- source-paragraph:V83-P2051 style=TableText -->
<pre>意义未改变行动或规则</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V83-P2052">
<!-- source-paragraph:V83-P2052 style=TableText -->
<pre>制度级联</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V83-P2053">
<!-- source-paragraph:V83-P2053 style=TableText -->
<pre>申诉、审计或事件改变规则并下行执行</pre>
</td>
<td data-source-cell="5,3" data-paragraphs="V83-P2054">
<!-- source-paragraph:V83-P2054 style=TableText -->
<pre>决定、执行和实际写回</pre>
</td>
<td data-source-cell="5,4" data-paragraphs="V83-P2055">
<!-- source-paragraph:V83-P2055 style=TableText -->
<pre>规则未落实或被局部抵消</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V83-P2056">
<!-- source-paragraph:V83-P2056 style=TableText -->
<pre>平台级联</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V83-P2057">
<!-- source-paragraph:V83-P2057 style=TableText -->
<pre>推荐、指标或公开评价放大传播</pre>
</td>
<td data-source-cell="6,3" data-paragraphs="V83-P2058">
<!-- source-paragraph:V83-P2058 style=TableText -->
<pre>算法、选择性可见和反身性</pre>
</td>
<td data-source-cell="6,4" data-paragraphs="V83-P2059">
<!-- source-paragraph:V83-P2059 style=TableText -->
<pre>曝光不再增长或受众不响应</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P2060 style=BodyCJK -->
级联不是规模越大越重要。小圈层可能通过关键桥接产生高影响，大圈层可能因通道阻断而没有有效传播。推演应关注位置、通道和阈值，而不是只看成员数量。

<!-- source-paragraph:V83-P2061 style=SecH2 -->
## 11.7　分叉路径图

<!-- source-paragraph:V83-P2062 style=BodyCJK -->
路径节点至少包含父节点、条件集、触发事件或行动、状态差、受影响时钟、支持状态、概率或排序表达、早期信号、反向信号、下一节点和终止理由。路径图应是有向无环图；若现实出现循环反馈，用时间展开后的新节点表示，不能让一个节点在同一次运行中既是自己的原因又是结果。

<!-- source-paragraph:V83-P2063 style=BodyCJK -->
分叉可由四类不确定产生：事实不确定、机制不确定、行动者选择和外生扰动。不同类型不应合并成一个模糊概率。事实不确定优先核验；机制不确定通过区分性观察；选择不确定保留策略与授权；外生扰动通过情景范围和韧性检查。

## V83-T046

<table data-source-table="V83-T046">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P2064">
<!-- source-paragraph:V83-P2064 style=TableHead -->
<pre>分叉来源</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P2065">
<!-- source-paragraph:V83-P2065 style=TableHead -->
<pre>例子</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P2066">
<!-- source-paragraph:V83-P2066 style=TableHead -->
<pre>合适输出</pre>
</td>
<td data-source-cell="1,4" data-paragraphs="V83-P2067">
<!-- source-paragraph:V83-P2067 style=TableHead -->
<pre>不合适输出</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P2068">
<!-- source-paragraph:V83-P2068 style=TableText -->
<pre>事实</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P2069">
<!-- source-paragraph:V83-P2069 style=TableText -->
<pre>事件是否真实发生</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P2070">
<!-- source-paragraph:V83-P2070 style=TableText -->
<pre>核验前的条件路径</pre>
</td>
<td data-source-cell="2,4" data-paragraphs="V83-P2071">
<!-- source-paragraph:V83-P2071 style=TableText -->
<pre>选一个版本当事实</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P2072">
<!-- source-paragraph:V83-P2072 style=TableText -->
<pre>机制</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P2073">
<!-- source-paragraph:V83-P2073 style=TableText -->
<pre>沉默来自恐惧还是策略</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P2074">
<!-- source-paragraph:V83-P2074 style=TableText -->
<pre>区分信号和并行路径</pre>
</td>
<td data-source-cell="3,4" data-paragraphs="V83-P2075">
<!-- source-paragraph:V83-P2075 style=TableText -->
<pre>用人格标签封口</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P2076">
<!-- source-paragraph:V83-P2076 style=TableText -->
<pre>选择</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P2077">
<!-- source-paragraph:V83-P2077 style=TableText -->
<pre>行动者合作、抵抗或退出</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P2078">
<!-- source-paragraph:V83-P2078 style=TableText -->
<pre>各选择的条件与后果</pre>
</td>
<td data-source-cell="4,4" data-paragraphs="V83-P2079">
<!-- source-paragraph:V83-P2079 style=TableText -->
<pre>宣称自由选择可精确预测</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V83-P2080">
<!-- source-paragraph:V83-P2080 style=TableText -->
<pre>扰动</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V83-P2081">
<!-- source-paragraph:V83-P2081 style=TableText -->
<pre>政策、价格、灾害或技术变化</pre>
</td>
<td data-source-cell="5,3" data-paragraphs="V83-P2082">
<!-- source-paragraph:V83-P2082 style=TableText -->
<pre>压力情景与恢复条件</pre>
</td>
<td data-source-cell="5,4" data-paragraphs="V83-P2083">
<!-- source-paragraph:V83-P2083 style=TableText -->
<pre>把未建模残差归因于命运</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P2084 style=SecH2 -->
## 11.8　变量候选账本

<!-- source-paragraph:V83-P2085 style=BodyCJK -->
模型无法解释的残差不能被删除，也不能立即命名成真实变量。候选账本把“我们可能漏了什么”转成可检验任务。每个候选至少记录来源残差、名称、可能类型、可能通道、可观察含义、竞争候选、最小检验、隐私与风险、当前状态、证据、升级和拒绝条件。

<!-- source-paragraph:V83-P2086 style=BodyCJK -->
候选状态包括提出、检验中、得到支持的候选、拒绝和退役。即使得到支持，它仍要进入相应对象或变量合同，不能直接变成稳定人格、有效圈层或因果机制。结果后提出的候选可以改善下一轮模型，不能回头支撑原预测。

## V83-T047

<table data-source-table="V83-T047">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P2087">
<!-- source-paragraph:V83-P2087 style=TableHead -->
<pre>候选来源</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P2088">
<!-- source-paragraph:V83-P2088 style=TableHead -->
<pre>合法动作</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P2089">
<!-- source-paragraph:V83-P2089 style=TableHead -->
<pre>必须避免</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P2090">
<!-- source-paragraph:V83-P2090 style=TableText -->
<pre>系统残差</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P2091">
<!-- source-paragraph:V83-P2091 style=TableText -->
<pre>提出多个竞争候选和区分性观察</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P2092">
<!-- source-paragraph:V83-P2092 style=TableText -->
<pre>用一个神秘变量吸收全部误差</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P2093">
<!-- source-paragraph:V83-P2093 style=TableText -->
<pre>当事人叙述</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P2094">
<!-- source-paragraph:V83-P2094 style=TableText -->
<pre>保留其位置、含义和可核验部分</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P2095">
<!-- source-paragraph:V83-P2095 style=TableText -->
<pre>自动降格为主观噪声或升格为事实全貌</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P2096">
<!-- source-paragraph:V83-P2096 style=TableText -->
<pre>跨案例重复</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P2097">
<!-- source-paragraph:V83-P2097 style=TableText -->
<pre>建立候选机制与外推边界</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P2098">
<!-- source-paragraph:V83-P2098 style=TableText -->
<pre>把相似叙事当通用规律</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V83-P2099">
<!-- source-paragraph:V83-P2099 style=TableText -->
<pre>模型搜索</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V83-P2100">
<!-- source-paragraph:V83-P2100 style=TableText -->
<pre>预注册下一轮检验</pre>
</td>
<td data-source-cell="5,3" data-paragraphs="V83-P2101">
<!-- source-paragraph:V83-P2101 style=TableText -->
<pre>结果后择优报告</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V83-P2102">
<!-- source-paragraph:V83-P2102 style=TableText -->
<pre>AI 建议</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V83-P2103">
<!-- source-paragraph:V83-P2103 style=TableText -->
<pre>生成和比较候选，并在证据、用途与明示规范前提允许时形成判断及分析推荐</pre>
</td>
<td data-source-cell="6,3" data-paragraphs="V83-P2104">
<!-- source-paragraph:V83-P2104 style=TableText -->
<pre>让 AI 输出验证现实或授权行动</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P2105 style=BodyCJK -->
框架只能主动识别当前变量集无法解释的残差，提出多个可区分的变量候选，并为每个候选设计风险可接受的最小检验；它不能自主决定候选在现实中为真。

<!-- source-paragraph:V83-P2106 style=SecH2 -->
## 11.9　情景、反事实与模拟

<!-- source-paragraph:V83-P2107 style=BodyCJK -->
情景推演问“如果这些条件成立，会出现什么路径”；反事实问“若某个事件或机制不同，已发生结果可能如何变化”；模拟把明确规则和参数展开。三者都需要与事实描述分开。

<!-- source-paragraph:V83-P2108 style=BodyCJK -->
反事实尤其需要可比条件。删除一个事件时，还要说明哪些后续状态、行动者信息和圈层关系随之改变；不能只删除不喜欢的原因而保留其全部后果。模拟的精度不能超过输入和机制证据，参数未知时使用区间、等级或敏感性分析，不生成没有依据的小数点。

<!-- source-paragraph:V83-P2109 style=SecH2 -->
## 11.9.1　多阶递归未来推演

<!-- source-paragraph:V83-P2110 style=BodyCJK -->
多步时间滚动、模拟状态再入和预期反身是三个正交维度。多步时间滚动在同一次运行中把状态沿时间推进；模拟再入把第一轮生成的某个模拟未来作为子运行起点；预期反身表示模拟中的行动者对更远未来或他人反应形成预期并改变当前策略。三者不得用一个“递归”词混写。

<!-- source-paragraph:V83-P2111 style=BodyCJK -->
本版把三阶设为默认探索上限：第一阶展开直接后果和竞争路径；第二阶考察第一阶状态如何改变行动集合、资源、圈层、反馈和适应；第三阶考察制度化、锁定、反转、跨圈层溢出以及生成条件本身的改变。三阶不是三个时间点，也不是自然阶段；条件不足时必须提前停止。

<!-- source-paragraph:V83-P2112 style=BodyCJK -->
总原则是：生成层可以大胆，状态层必须严格，证据层不得自我升级，行动层仍须另行授权。大胆用于扩大合理的机制空间、竞争路径和低概率高后果分支，也用于完成证据范围内的明确判断；判断强度只由证据、适用条件和用途支持，不能由语气或生成数量抬高。

<!-- source-paragraph:V83-P2113 style=SecH3 -->
### 11.9.2　递归界面与谱系

<!-- source-paragraph:V83-P2114 style=BodyCJK -->
每次再入前都执行一次转义审计，记录当前阶次、父运行、父路径、父节点、模拟时点、本阶和累计时间窗、模型版本、继承假设、新增条件、保持、改变、折叠、遗漏、新增未知、目标有效变量、残差、同一性、返回路径和停止原因。模拟起点不得改写成当前现实。

<!-- source-paragraph:V83-P2115 style=BodyCJK -->
子运行必须继承父运行尚未解决的未知、损失和残差。选择某一假设分支只会缩小条件范围，不表示不确定性被现实材料消除；增加抽样次数只可能降低计算误差，不会提高关于现实结果的经验支持。

<!-- source-paragraph:V83-P2116 style=SecH3 -->
### 11.9.3　分支、合并与剪枝

<!-- source-paragraph:V83-P2117 style=BodyCJK -->
每阶至少保留当前主要路径、最强竞争路径、低概率高后果路径和残差出口。分支只来自可说明的条件、机制差异、行动者选择、外部扰动或类型化未知，不靠叙事趣味增加。

<!-- source-paragraph:V83-P2118 style=BodyCJK -->
只有对象同一性保持、关键状态在预定容差内等价、历史差异不改变后续转移、后续可用行动和约束一致时，分支才可合并。剪枝规则必须事前声明，并保留被剪分支、理由、可能的概率质量和伤害等级；低概率不能单独删除高后果路径。

<!-- source-paragraph:V83-P2119 style=SecH3 -->
### 11.9.4　提前停止

<!-- source-paragraph:V83-P2120 style=BodyCJK -->
出现对象或尺度同一性失效、关键假设无法继承、转移机制超出适用域、递归界面不闭合、分支爆炸且无区分信号、结果对微小变化全面反转、残差超过用途门槛、深一阶相对浅一阶和简单基线无增量、超出校准时间窗、触及权利或授权边界，或到达第三阶上限时，停止或降级。停止记录必须说明还能说什么和不能说什么。

<!-- source-paragraph:V83-P2121 style=SecH2 -->
## 11.10　推演运行的停止条件

<!-- source-paragraph:V83-P2122 style=BodyCJK -->
出现以下任一情况时，受影响命题及其依赖路径应暂停或降级；共同前提或整体使用条件失败时全部相关运行停止：关键对象没有获得有限支持；事件事实地位不清；传播通道缺失；跨尺度映射失败；路径数量增长而没有区分性信号；模型对参数微小变化极度敏感；隐私或安全风险超过信息价值；推演被要求直接生成诊断、处罚或授权；简单基线已经表现相同或更好。

<!-- source-paragraph:V83-P2123 style=BodyCJK -->
停止不是失败掩盖，而是输出的一部分。停止记录应说明停在哪里、已获得什么、哪些未知阻止继续、下一项最有信息价值的观察是什么，以及继续推演会增加何种风险。

<!-- source-paragraph:V83-P2124 style=SecH2 -->
## 11.11　一个跨圈层级联示例

<!-- source-paragraph:V83-P2125 style=BodyCJK -->
继续第十部分的公开离职事件。起点快照显示：员工处于高工时和照护压力，团队信任下降，公司管理层关注声誉，职业社群提供外部机会，平台舆论尚未形成。事件是员工发布离职说明，内容真实性部分可核验、部分为个人叙述。

<!-- source-paragraph:V83-P2126 style=BodyCJK -->
直接效应包括团队收到信息、平台获得可传播文本、管理层面临回应压力。路径一：公司只做公开否认，短期外部舆论可能分叉为消退或放大；若内部成员把否认解释为压制，团队信任下降，经职业社群桥接出现更多离职。路径二：公司承认问题并启动可核验的资源与申诉调整；若实际执行，组织时钟上出现工时和流程变化，体验—意义时钟上信任恢复可能更慢。路径三：家庭照护条件变化降低员工退出后的压力，但这不直接改变团队状态，除非员工继续桥接信息或资源。

<!-- source-paragraph:V83-P2127 style=BodyCJK -->
早期信号可以是内部申诉数量、工时执行记录、成员公开表达、招聘和离职变化；反向信号可以是政策发布后没有实际资源变化、外部曝光下降但内部沉默增加、职业社群没有形成桥接。残差可能来自关键管理者状态、平台推荐机制或未观察的法律约束，这些只进入变量候选账本。

<!-- source-paragraph:V83-P2128 style=BodyCJK -->
该推演仍不能回答公司“应该”采取哪条路径。它提供条件后果和区分信号；前瞻登记、方案比较、规范前提和授权由下一部分处理。

<!-- source-paragraph:V83-P2129 style=SecH2 -->
## 11.12　本部分的输出

<!-- source-paragraph:V83-P2130 style=BodyCJK -->
一次合格推演输出应包含：冻结联合快照；事件类型与证据；机制和参数假设；更新步骤；路径图；每条路径的条件、时钟、支持状态、早期与反向信号；残差和变量候选；停止条件；结果回写计划；预测和行动的明确隔离声明。

<!-- source-paragraph:V83-P2131 style=BodyCJK -->
推演可以提高对后续的结构化准备，但它仍是条件性的。没有结果前登记、简单基线、校准和持续回写，不能据此宣称前瞻能力已经提高；没有规范与授权，不能据此宣称某项行动应当执行。依据明示规范前提给出分析性首选、否决或暂缓意见，不等于宣称该方案已经获准执行；其依据、代价、反方和改判条件必须完整说明。
