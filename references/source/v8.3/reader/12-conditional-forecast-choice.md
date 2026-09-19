# 第十二部分　条件前瞻与有限选择

Source: `v8.3`
Raw SHA256: `4a3ad8e8692b7a906f733096bbc8e05d0ac4f8cfbf79d3926eb1729df828c7f5`
Semantic SHA256: `f190a80be88033ba21d717a310f4419c00489b3a6dea17b6a1e2b14af1447d9f`
List structure SHA256: `967dd396860e4b5d246ae2e3699eb33b8ab8ee46ca12bb72959e1249216d7a5f`
Paragraph range: `V83-P2132`-`V83-P2348`
Tables: `V83-T048`, `V83-T049`, `V83-T050`, `V83-T051`, `V83-T052`, `V83-T053`, `V83-T054`, `V83-T055`

<!-- This is a lossless reader edition; anchors are source coordinates. -->

<!-- source-paragraph:V83-P2132 style=PartTitle -->
# 第十二部分　条件前瞻与有限选择

<!-- source-paragraph:V83-P2133 style=BodyCJK -->
推演把条件和路径展开，条件前瞻进一步承担可失败的未来判断，有限选择则在价值、保护和授权边界内比较可做、如何做、何时停以及何时不做。本部分把二者放在相邻位置，是为了形成工作闭环；把二者分成不同合同，是为了防止“预测了某个后果”被偷换成“因此有权让别人承担某项行动”。比较和推荐方案属于分析交付，可以在规范前提与限制明确时完成；现实采用与执行则须另行通过适用的保护、复核和授权。

<!-- source-paragraph:V83-P2134 style=SecH2 -->
## 12.1　四类输出的隔离

<!-- source-paragraph:V83-P2135 style=BodyCJK -->
解释、推演、条件前瞻和有限选择必须分别标记。

## V83-T048

<table data-source-table="V83-T048">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P2136">
<!-- source-paragraph:V83-P2136 style=TableHead -->
<pre>输出</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P2137">
<!-- source-paragraph:V83-P2137 style=TableHead -->
<pre>核心问题</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P2138">
<!-- source-paragraph:V83-P2138 style=TableHead -->
<pre>必需输入</pre>
</td>
<td data-source-cell="1,4" data-paragraphs="V83-P2139">
<!-- source-paragraph:V83-P2139 style=TableHead -->
<pre>输出上限</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P2140">
<!-- source-paragraph:V83-P2140 style=TableText -->
<pre>解释</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P2141">
<!-- source-paragraph:V83-P2141 style=TableText -->
<pre>已发生什么，可能为何发生</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P2142">
<!-- source-paragraph:V83-P2142 style=TableText -->
<pre>对象、尺度、证据、机制、反例</pre>
</td>
<td data-source-cell="2,4" data-paragraphs="V83-P2143">
<!-- source-paragraph:V83-P2143 style=TableText -->
<pre>有边界的机制说明</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P2144">
<!-- source-paragraph:V83-P2144 style=TableText -->
<pre>推演</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P2145">
<!-- source-paragraph:V83-P2145 style=TableText -->
<pre>条件或事件后可能沿哪些路径演化</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P2146">
<!-- source-paragraph:V83-P2146 style=TableText -->
<pre>冻结快照、更新规则、时钟、分叉</pre>
</td>
<td data-source-cell="3,4" data-paragraphs="V83-P2147">
<!-- source-paragraph:V83-P2147 style=TableText -->
<pre>条件路径和区分信号</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P2148">
<!-- source-paragraph:V83-P2148 style=TableText -->
<pre>条件前瞻</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P2149">
<!-- source-paragraph:V83-P2149 style=TableText -->
<pre>在目标与期限内哪条路径更值得期待</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P2150">
<!-- source-paragraph:V83-P2150 style=TableText -->
<pre>结果前登记、简单基线、指标、回写</pre>
</td>
<td data-source-cell="4,4" data-paragraphs="V83-P2151">
<!-- source-paragraph:V83-P2151 style=TableText -->
<pre>可校准、可失败的判断</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V83-P2152">
<!-- source-paragraph:V83-P2152 style=TableText -->
<pre>有限选择</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V83-P2153">
<!-- source-paragraph:V83-P2153 style=TableText -->
<pre>在明示规范前提下比较与推荐方案；现实采用另经保护、复核和授权</pre>
</td>
<td data-source-cell="5,3" data-paragraphs="V83-P2154">
<!-- source-paragraph:V83-P2154 style=TableText -->
<pre>分析需规范前提、证据、方案、代价与受影响者；现实采用另需 N、PF、J、O、C12</pre>
</td>
<td data-source-cell="5,4" data-paragraphs="V83-P2155">
<!-- source-paragraph:V83-P2155 style=TableText -->
<pre>可反驳的分析推荐或经授权的有限选择记录；两者身份分开</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P2156 style=BodyCJK -->
解释可以生成推演候选，却不能自动证明未来；推演可以生成前瞻候选，却不能把所有路径都算成功；前瞻可以进入方案比较，却不能自动生成价值或权限；有限选择即使通过，也不保证现实执行会成功，仍需停止、回滚与结果回写。

<!-- source-paragraph:V83-P2157 style=SecH2 -->
## 12.2　条件前瞻登记

<!-- source-paragraph:V83-P2158 style=BodyCJK -->
每条前瞻在输入截止后、结果出现前冻结。最低字段包括：前瞻 ID、模型版本、目标、期限、对象与圈层范围、基线时点、输入截止、简单基线、候选机制、路径集合、概率或排序表达、校准计划、决策阈值、早期信号、反向信号、暂停条件、退役条件、结果回写、登记时间和证据引用。

<!-- source-paragraph:V83-P2159 style=BodyCJK -->
目标必须可判定。例如“关系会变好”需要改写为指定时间窗内哪些可观察量改变、由谁观察、达到什么阈值以及何种结果视为未决。期限可以是窗口，不必伪造精确日期。对象和圈层范围必须冻结，避免结果后缩小到成功子群。

## V83-T049

<table data-source-table="V83-T049">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P2160">
<!-- source-paragraph:V83-P2160 style=TableHead -->
<pre>登记项</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P2161">
<!-- source-paragraph:V83-P2161 style=TableHead -->
<pre>最低问题</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P2162">
<!-- source-paragraph:V83-P2162 style=TableHead -->
<pre>防止的偏差</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P2163">
<!-- source-paragraph:V83-P2163 style=TableText -->
<pre>目标</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P2164">
<!-- source-paragraph:V83-P2164 style=TableText -->
<pre>到期时如何知道发生、未发生或无法判断</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P2165">
<!-- source-paragraph:V83-P2165 style=TableText -->
<pre>模糊成功</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P2166">
<!-- source-paragraph:V83-P2166 style=TableText -->
<pre>期限</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P2167">
<!-- source-paragraph:V83-P2167 style=TableText -->
<pre>从何时到何时，何时停止收集输入</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P2168">
<!-- source-paragraph:V83-P2168 style=TableText -->
<pre>无限等待</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P2169">
<!-- source-paragraph:V83-P2169 style=TableText -->
<pre>简单基线</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P2170">
<!-- source-paragraph:V83-P2170 style=TableText -->
<pre>不用多圈层机制时的比较预测是什么</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P2171">
<!-- source-paragraph:V83-P2171 style=TableText -->
<pre>复杂故事自我胜利</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V83-P2172">
<!-- source-paragraph:V83-P2172 style=TableText -->
<pre>路径</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V83-P2173">
<!-- source-paragraph:V83-P2173 style=TableText -->
<pre>哪些路径互斥、并行或不可比较</pre>
</td>
<td data-source-cell="5,3" data-paragraphs="V83-P2174">
<!-- source-paragraph:V83-P2174 style=TableText -->
<pre>事后挑选</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V83-P2175">
<!-- source-paragraph:V83-P2175 style=TableText -->
<pre>表达</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V83-P2176">
<!-- source-paragraph:V83-P2176 style=TableText -->
<pre>概率、区间、等级还是仅方向</pre>
</td>
<td data-source-cell="6,3" data-paragraphs="V83-P2177">
<!-- source-paragraph:V83-P2177 style=TableText -->
<pre>伪精确</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V83-P2178">
<!-- source-paragraph:V83-P2178 style=TableText -->
<pre>信号</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V83-P2179">
<!-- source-paragraph:V83-P2179 style=TableText -->
<pre>什么提高或降低路径支持</pre>
</td>
<td data-source-cell="7,3" data-paragraphs="V83-P2180">
<!-- source-paragraph:V83-P2180 style=TableText -->
<pre>只找支持证据</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V83-P2181">
<!-- source-paragraph:V83-P2181 style=TableText -->
<pre>回写</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V83-P2182">
<!-- source-paragraph:V83-P2182 style=TableText -->
<pre>结果由何来源、何时追加</pre>
</td>
<td data-source-cell="8,3" data-paragraphs="V83-P2183">
<!-- source-paragraph:V83-P2183 style=TableText -->
<pre>失败消失</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P2184 style=SecH3 -->
### 12.2.1　局部可预测性边界

<!-- source-paragraph:V83-P2185 style=BodyCJK -->
任何可预测性主张都必须绑定对象、状态区域、尺度与圈层、时间窗、允许误差、可用信息、计算和观测资源、模型版本、基线、弃权与失效条件。世界整体是否可预测不是本框架能够直接回答的问题；只能检验某项任务在明确边界内是否获得有限增量。

<!-- source-paragraph:V83-P2186 style=BodyCJK -->
量化按名义分类、顺序等级、区间和概率逐级准入。没有测量、样本、单位、生成方法和校准时，停在较低档位；不得由文字结构或人工智能补造参数。引用现有数学或物理理论时，必须一并登记原对象、假设、极限或尺度律、误差、有效域、对象映射、反例和退出条件，不能只借公式外形。

<!-- source-paragraph:V83-P2187 style=SecH3 -->
### 12.2.2　递归前瞻的按阶评价

<!-- source-paragraph:V83-P2188 style=BodyCJK -->
第一、第二、第三阶分别冻结并分别评价，不能合成一个总命中率。每一阶都要与不继续递归的状态延续、直接远期判断和更浅阶次加简单延续比较。若三阶只增加故事而没有稳定样本外增益，它可以保留为探索情景，但不得取得前瞻能力资格。

<!-- source-paragraph:V83-P2189 style=BodyCJK -->
没有新外部材料进入时，全部子运行的来源谱系仍终止于同一冻结起点。后处理可以增加模型内部的推理内容、暴露敏感性和隐藏后果，却不能自造现实证据。真实中间结果到达后，应建立新的冻结运行，与原递归路径比较，不能把结果倒灌进旧路径。

<!-- source-paragraph:V83-P2190 style=SecH2 -->
## 12.3　简单基线与增量能力

<!-- source-paragraph:V83-P2191 style=BodyCJK -->
多圈层模型只有在相对于复杂度匹配的单焦点、单圈层或历史频率基线取得稳定样本外增益时，才能声称增加了前瞻能力。基线不能故意过弱，也不能把多圈层模型使用的信息泄漏给比较的一方。

<!-- source-paragraph:V83-P2192 style=BodyCJK -->
常用基线包括：延续当前趋势；沿用最近状态；历史频率；只使用行动者状态；只使用主圈层状态；领域已有模型。比较应使用相同目标、期限、数据截止和评价指标。若复杂模型改善解释但不改善预测，应如实登记“解释增益存在、前瞻增益未获支持”。

<!-- source-paragraph:V83-P2193 style=BodyCJK -->
模型复杂度也有成本：更多变量增加缺失、测量误差、隐私风险、过拟合和维护债。若多圈层模型只在少量案例中有效，应限定适用域；若增益随时间消失，应降级或退役；若简单基线表现相同，应优先简单模型。

<!-- source-paragraph:V83-P2194 style=SecH2 -->
## 12.4　概率、等级与时间窗

<!-- source-paragraph:V83-P2195 style=BodyCJK -->
证据允许时，可以给出概率区间；样本不足时，可以给出高/中/低支持或路径排序；连排序都不稳时，只给出条件方向和关键观察点。表达强度由证据和校准决定，不由用户希望的确定性决定。

## V83-T050

<table data-source-table="V83-T050">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P2196">
<!-- source-paragraph:V83-P2196 style=TableHead -->
<pre>证据状态</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P2197">
<!-- source-paragraph:V83-P2197 style=TableHead -->
<pre>合适表达</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P2198">
<!-- source-paragraph:V83-P2198 style=TableHead -->
<pre>必须同时给出</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P2199">
<!-- source-paragraph:V83-P2199 style=TableText -->
<pre>有充分历史样本和稳定目标</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P2200">
<!-- source-paragraph:V83-P2200 style=TableText -->
<pre>概率或概率区间</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P2201">
<!-- source-paragraph:V83-P2201 style=TableText -->
<pre>校准、分辨率、基线和置信区间</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P2202">
<!-- source-paragraph:V83-P2202 style=TableText -->
<pre>样本有限但路径可区分</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P2203">
<!-- source-paragraph:V83-P2203 style=TableText -->
<pre>支持等级或排序</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P2204">
<!-- source-paragraph:V83-P2204 style=TableText -->
<pre>依据、不可比较项和反向信号</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P2205">
<!-- source-paragraph:V83-P2205 style=TableText -->
<pre>机制候选多、数据稀疏</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P2206">
<!-- source-paragraph:V83-P2206 style=TableText -->
<pre>条件方向</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P2207">
<!-- source-paragraph:V83-P2207 style=TableText -->
<pre>触发点、最小观察和停止条件</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V83-P2208">
<!-- source-paragraph:V83-P2208 style=TableText -->
<pre>目标或对象不稳定</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V83-P2209">
<!-- source-paragraph:V83-P2209 style=TableText -->
<pre>不发布前瞻</pre>
</td>
<td data-source-cell="5,3" data-paragraphs="V83-P2210">
<!-- source-paragraph:V83-P2210 style=TableText -->
<pre>需要重新定义的合同</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P2211 style=BodyCJK -->
时间窗应与机制时钟相符。即时反应可以使用短窗，组织或制度变化需要更长窗。把长期机制压缩到短期，会误判无效；把短期信号无限外推，会误判趋势。多个时钟并存时，可以为不同中间结果分别登记期限。

<!-- source-paragraph:V83-P2212 style=SecH2 -->
## 12.5　校准与评价

<!-- source-paragraph:V83-P2213 style=BodyCJK -->
前瞻能力不是文风上的“说得准”，而是长期登记的结果。概率任务适用时使用 Brier 分数、对数损失、校准曲线、分辨率和区间覆盖率；排序任务使用预登记的排序指标；事件检测使用精确率、召回率或领域指标；时间预测使用窗口覆盖和提前量。

<!-- source-paragraph:V83-P2214 style=BodyCJK -->
任何指标都要与实际用途匹配。若低概率高损害事件需要谨慎，评价不能只看总体准确率；若输出只用于提醒观察，假阳性成本与用于强制行动不同。指标表现良好也不证明模型解释正确，更不证明行动正当。

## V83-T051

<table data-source-table="V83-T051">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P2215">
<!-- source-paragraph:V83-P2215 style=TableHead -->
<pre>评价维度</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P2216">
<!-- source-paragraph:V83-P2216 style=TableHead -->
<pre>说明</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P2217">
<!-- source-paragraph:V83-P2217 style=TableHead -->
<pre>失败后的动作</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P2218">
<!-- source-paragraph:V83-P2218 style=TableText -->
<pre>校准</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P2219">
<!-- source-paragraph:V83-P2219 style=TableText -->
<pre>说 70% 的事件长期是否约 70% 发生</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P2220">
<!-- source-paragraph:V83-P2220 style=TableText -->
<pre>调整表达或降级概率输出</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P2221">
<!-- source-paragraph:V83-P2221 style=TableText -->
<pre>分辨率</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P2222">
<!-- source-paragraph:V83-P2222 style=TableText -->
<pre>模型能否区分不同风险或路径</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P2223">
<!-- source-paragraph:V83-P2223 style=TableText -->
<pre>删除无贡献变量、退回基线</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P2224">
<!-- source-paragraph:V83-P2224 style=TableText -->
<pre>覆盖率</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P2225">
<!-- source-paragraph:V83-P2225 style=TableText -->
<pre>区间或时间窗是否覆盖实际结果</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P2226">
<!-- source-paragraph:V83-P2226 style=TableText -->
<pre>扩大区间或修正时钟</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V83-P2227">
<!-- source-paragraph:V83-P2227 style=TableText -->
<pre>基线增益</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V83-P2228">
<!-- source-paragraph:V83-P2228 style=TableText -->
<pre>是否优于简单模型</pre>
</td>
<td data-source-cell="5,3" data-paragraphs="V83-P2229">
<!-- source-paragraph:V83-P2229 style=TableText -->
<pre>停止复杂模型的前瞻声明</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V83-P2230">
<!-- source-paragraph:V83-P2230 style=TableText -->
<pre>稳定性</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V83-P2231">
<!-- source-paragraph:V83-P2231 style=TableText -->
<pre>跨时间、地点和边界是否保持</pre>
</td>
<td data-source-cell="6,3" data-paragraphs="V83-P2232">
<!-- source-paragraph:V83-P2232 style=TableText -->
<pre>限定适用域或退役</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V83-P2233">
<!-- source-paragraph:V83-P2233 style=TableText -->
<pre>分配误差</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V83-P2234">
<!-- source-paragraph:V83-P2234 style=TableText -->
<pre>哪些位置持续被低估或误报</pre>
</td>
<td data-source-cell="7,3" data-paragraphs="V83-P2235">
<!-- source-paragraph:V83-P2235 style=TableText -->
<pre>受影响者复核、补救和保护升级</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P2236 style=SecH2 -->
## 12.6　早期信号、反向信号与触发点

<!-- source-paragraph:V83-P2237 style=BodyCJK -->
早期信号不是结果的缩小版，而是路径机制应当先产生的可观察变化。反向信号表示该路径的关键条件正在失效或竞争路径得到支持。两者必须在结果前登记，避免只收集支持材料。

<!-- source-paragraph:V83-P2238 style=BodyCJK -->
触发点把前瞻连接到复核：观察到信号后，不是自动行动，而是重新评估对象、路径、概率、规范和授权。高风险情形还应设置否决触发点，例如保护底板被突破、关键受影响者无法退出、数据来源失真或模型校准恶化。

<!-- source-paragraph:V83-P2239 style=SecH2 -->
## 12.7　前瞻的失败语义

<!-- source-paragraph:V83-P2240 style=BodyCJK -->
到期后结果可以是支持、未支持、未决、目标失效或无法评价。未决不是成功与失败的折中，而是合同规定的证据不足状态；无法评价必须说明数据、对象、期限或执行出了什么问题。目标失效表示预测对象或同一性判据已转换，不能把它计为命中。

<!-- source-paragraph:V83-P2241 style=BodyCJK -->
结果后改目标、改期限、改圈层范围或把多个路径合并成“某种程度发生”，都不能保留原前瞻的成功资格。新解释可以建立新版本，但旧记录继续存在。

<!-- source-paragraph:V83-P2242 style=SecH2 -->
## 12.8　从前瞻到有限选择的桥

<!-- source-paragraph:V83-P2243 style=BodyCJK -->
前瞻输出只回答条件后果。形成分析推荐前须明示规范前提、证据、受影响位置、方案、成本收益和改判条件；推荐不产生执行权限。进入现实采用前，必须补入：明示规范前提、选择主体、管辖权、受影响位置、权利底线、方案、成本与收益分布、授权、停止、申诉、回滚和补救。这里继续调用 N、PF、J、O 与 C12，不建立预测捷径。

<!-- source-paragraph:V83-P2244 style=BodyCJK -->
预测不能自动生成授权。即使某条路径概率极高，也不说明任何人有权强迫他人承担避免该路径的成本；即使某行动平均收益最大，也不说明少数位置的权利可以被忽略；即使模型推荐不行动，也要审查不行动造成的持续伤害和责任。

<!-- source-paragraph:V83-P2245 style=SecH2 -->
## 12.9　方案集必须包含行动与不行动

<!-- source-paragraph:V83-P2246 style=BodyCJK -->
方案生成逐项检查维持现状、主动行动、延迟行动、试探性小步行动、退出或转移，以及明确的不行动六种类别的适用性。适用类别形成真实、可比较的方案；不适用类别说明理由，不能为满足数量虚构方案。请求选择时不得删除明确的不行动基线，也不能把维持现状和不行动混为一项：维持现状可能需要持续资源和执行，不行动可能让现状自然变化。具体任务可以增加方案；未请求选择的任务不强制生成行动清单。

## V83-T052

<table data-source-table="V83-T052">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P2247">
<!-- source-paragraph:V83-P2247 style=TableHead -->
<pre>方案类型</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P2248">
<!-- source-paragraph:V83-P2248 style=TableHead -->
<pre>主要用途</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P2249">
<!-- source-paragraph:V83-P2249 style=TableHead -->
<pre>必须检查的风险</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P2250">
<!-- source-paragraph:V83-P2250 style=TableText -->
<pre>维持现状</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P2251">
<!-- source-paragraph:V83-P2251 style=TableText -->
<pre>保护已有稳定与承接</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P2252">
<!-- source-paragraph:V83-P2252 style=TableText -->
<pre>隐性成本、持续伤害、锁定</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P2253">
<!-- source-paragraph:V83-P2253 style=TableText -->
<pre>主动行动</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P2254">
<!-- source-paragraph:V83-P2254 style=TableText -->
<pre>快速改变路径或条件</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P2255">
<!-- source-paragraph:V83-P2255 style=TableText -->
<pre>权限、不可逆、跨圈层溢出</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P2256">
<!-- source-paragraph:V83-P2256 style=TableText -->
<pre>延迟行动</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P2257">
<!-- source-paragraph:V83-P2257 style=TableText -->
<pre>等待信息、程序或时机</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P2258">
<!-- source-paragraph:V83-P2258 style=TableText -->
<pre>延迟本身的损害和机会损失</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V83-P2259">
<!-- source-paragraph:V83-P2259 style=TableText -->
<pre>试探行动</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V83-P2260">
<!-- source-paragraph:V83-P2260 style=TableText -->
<pre>以可逆小步获取信息</pre>
</td>
<td data-source-cell="5,3" data-paragraphs="V83-P2261">
<!-- source-paragraph:V83-P2261 style=TableText -->
<pre>试验成本由谁承担、能否真正回滚</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V83-P2262">
<!-- source-paragraph:V83-P2262 style=TableText -->
<pre>退出或转移</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V83-P2263">
<!-- source-paragraph:V83-P2263 style=TableText -->
<pre>结束不合适的对象或关系</pre>
</td>
<td data-source-cell="6,3" data-paragraphs="V83-P2264">
<!-- source-paragraph:V83-P2264 style=TableText -->
<pre>无法退出者、责任与历史保存</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V83-P2265">
<!-- source-paragraph:V83-P2265 style=TableText -->
<pre>不行动</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V83-P2266">
<!-- source-paragraph:V83-P2266 style=TableText -->
<pre>避免越权或高风险动作</pre>
</td>
<td data-source-cell="7,3" data-paragraphs="V83-P2267">
<!-- source-paragraph:V83-P2267 style=TableText -->
<pre>默认偏向、持续后果和不作为责任</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P2268 style=BodyCJK -->
“不行动”不是不发生任何事。其他行动者、圈层、资源和时钟仍在变化。不行动方案要有基线时点、预期路径、观察计划、重新开启条件和责任主体。

<!-- source-paragraph:V83-P2269 style=SecH2 -->
## 12.10　统一方案比较卡

<!-- source-paragraph:V83-P2270 style=BodyCJK -->
每个方案使用同一基线比较，至少登记：方案描述、前瞻引用、规范前提、受影响者、权利底线、预期路径、最坏可接受结果、跨圈层溢出、成本与收益分布、信息价值、锁定风险、可逆性、资源成本、执行者、授权、停止、回滚和补救。

## V83-T053

<table data-source-table="V83-T053">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P2271">
<!-- source-paragraph:V83-P2271 style=TableHead -->
<pre>比较维度</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P2272">
<!-- source-paragraph:V83-P2272 style=TableHead -->
<pre>问题</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P2273">
<!-- source-paragraph:V83-P2273 style=TableHead -->
<pre>不能用什么替代</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P2274">
<!-- source-paragraph:V83-P2274 style=TableText -->
<pre>目标与路径</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P2275">
<!-- source-paragraph:V83-P2275 style=TableText -->
<pre>它试图改变哪条路径</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P2276">
<!-- source-paragraph:V83-P2276 style=TableText -->
<pre>抽象的“变好”</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P2277">
<!-- source-paragraph:V83-P2277 style=TableText -->
<pre>保护底板</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P2278">
<!-- source-paragraph:V83-P2278 style=TableText -->
<pre>谁可能受到不可接受损害</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P2279">
<!-- source-paragraph:V83-P2279 style=TableText -->
<pre>平均收益</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P2280">
<!-- source-paragraph:V83-P2280 style=TableText -->
<pre>分配</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P2281">
<!-- source-paragraph:V83-P2281 style=TableText -->
<pre>谁获益、谁付出、何时发生</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P2282">
<!-- source-paragraph:V83-P2282 style=TableText -->
<pre>总量净值</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V83-P2283">
<!-- source-paragraph:V83-P2283 style=TableText -->
<pre>跨圈层溢出</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V83-P2284">
<!-- source-paragraph:V83-P2284 style=TableText -->
<pre>局部改善是否外部化成本</pre>
</td>
<td data-source-cell="5,3" data-paragraphs="V83-P2285">
<!-- source-paragraph:V83-P2285 style=TableText -->
<pre>主圈层指标</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V83-P2286">
<!-- source-paragraph:V83-P2286 style=TableText -->
<pre>信息价值</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V83-P2287">
<!-- source-paragraph:V83-P2287 style=TableText -->
<pre>是否能区分机制或路径</pre>
</td>
<td data-source-cell="6,3" data-paragraphs="V83-P2288">
<!-- source-paragraph:V83-P2288 style=TableText -->
<pre>行动本身的戏剧性</pre>
</td>
</tr>
<tr>
<td data-source-cell="7,1" data-paragraphs="V83-P2289">
<!-- source-paragraph:V83-P2289 style=TableText -->
<pre>可逆与锁定</pre>
</td>
<td data-source-cell="7,2" data-paragraphs="V83-P2290">
<!-- source-paragraph:V83-P2290 style=TableText -->
<pre>错了能否停、退、补救</pre>
</td>
<td data-source-cell="7,3" data-paragraphs="V83-P2291">
<!-- source-paragraph:V83-P2291 style=TableText -->
<pre>口头承诺</pre>
</td>
</tr>
<tr>
<td data-source-cell="8,1" data-paragraphs="V83-P2292">
<!-- source-paragraph:V83-P2292 style=TableText -->
<pre>权限</pre>
</td>
<td data-source-cell="8,2" data-paragraphs="V83-P2293">
<!-- source-paragraph:V83-P2293 style=TableText -->
<pre>谁可以决定、执行和申诉</pre>
</td>
<td data-source-cell="8,3" data-paragraphs="V83-P2294">
<!-- source-paragraph:V83-P2294 style=TableText -->
<pre>模型建议或职位名称</pre>
</td>
</tr>
<tr>
<td data-source-cell="9,1" data-paragraphs="V83-P2295">
<!-- source-paragraph:V83-P2295 style=TableText -->
<pre>不行动</pre>
</td>
<td data-source-cell="9,2" data-paragraphs="V83-P2296">
<!-- source-paragraph:V83-P2296 style=TableText -->
<pre>不做会沿什么路径变化</pre>
</td>
<td data-source-cell="9,3" data-paragraphs="V83-P2297">
<!-- source-paragraph:V83-P2297 style=TableText -->
<pre>假定零成本</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P2298 style=BodyCJK -->
若方案之间无法用单一尺度比较，应保留多维结果和公开冲突，而不是强行求和。若价值前提之间冲突，应由有资格的主体和程序处理，模型应完整显示冲突位置与后果，可以在公开的规范前提下提出供审议的偏好与理由；不能替有资格的主体作具有约束力的最终决定。

<!-- source-paragraph:V83-P2299 style=SecH2 -->
## 12.11　行动上限与信息性试验

<!-- source-paragraph:V83-P2300 style=BodyCJK -->
证据、可逆性、权限和保护共同决定行动上限。证据弱、风险高、不可逆或权限不足时，合适输出可能是先观察、缩小动作、改善信息、保护受影响者、启动申诉或当前不行动。

<!-- source-paragraph:V83-P2301 style=BodyCJK -->
信息性试验不是免责任的“小动作”。它仍需说明试验对象、受影响者、最小范围、可逆性、停止、数据用途和补救。不能把低权力位置当作模型校准材料，也不能在没有真实退出能力时宣称自愿参与。

## V83-T054

<table data-source-table="V83-T054">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P2302">
<!-- source-paragraph:V83-P2302 style=TableHead -->
<pre>条件组合</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P2303">
<!-- source-paragraph:V83-P2303 style=TableHead -->
<pre>允许上限示例</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P2304">
<!-- source-paragraph:V83-P2304 style=TableText -->
<pre>证据弱、损害低、可逆、授权清楚</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P2305">
<!-- source-paragraph:V83-P2305 style=TableText -->
<pre>小范围观察或试探行动</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P2306">
<!-- source-paragraph:V83-P2306 style=TableText -->
<pre>证据中等、损害可控、可回滚</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P2307">
<!-- source-paragraph:V83-P2307 style=TableText -->
<pre>分阶段行动并设强停止门</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P2308">
<!-- source-paragraph:V83-P2308 style=TableText -->
<pre>证据强但权限不足</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P2309">
<!-- source-paragraph:V83-P2309 style=TableText -->
<pre>提交有权限主体，不自行执行</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V83-P2310">
<!-- source-paragraph:V83-P2310 style=TableText -->
<pre>证据强但不可逆且保护未满足</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V83-P2311">
<!-- source-paragraph:V83-P2311 style=TableText -->
<pre>暂停，补足程序与保护</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V83-P2312">
<!-- source-paragraph:V83-P2312 style=TableText -->
<pre>紧急安全威胁</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V83-P2313">
<!-- source-paragraph:V83-P2313 style=TableText -->
<pre>仅按外部紧急授权做最小保护动作，并尽快复核</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P2314 style=SecH2 -->
## 12.12　结果回写与模型学习

<!-- source-paragraph:V83-P2315 style=BodyCJK -->
前瞻和选择的结果回写只能追加。记录包括结果观察时间、来源、实际结果、路径匹配、校准指标、简单基线比较、意外效应、受影响位置复核、模型更新、断言降级、退役变量或路径和下一次复核。

<!-- source-paragraph:V83-P2316 style=BodyCJK -->
行动结果不能只按主目标评价。还要检查副作用、跨圈层溢出、成本分配、申诉、无法退出者和长期时钟。一次成功不证明机制普遍成立，一次失败也可能来自执行偏离；两者要通过冻结合同区分，不能用执行解释随意救援模型。

<!-- source-paragraph:V83-P2317 style=SecH2 -->
## 12.13　一个完整的前瞻—选择示例

<!-- source-paragraph:V83-P2318 style=BodyCJK -->
继续公开离职事件。条件前瞻可以把目标设为“未来三个月团队自愿离职是否明显高于历史与同类团队基线”，输入截止为公开说明后一周。简单基线使用历史离职率和工时趋势；多圈层模型增加团队信任、管理回应、职业社群桥接、家庭照护与平台曝光。路径包括舆论消退而内部持续、制度调整并逐步修复、外部桥接触发连续退出等。

<!-- source-paragraph:V83-P2319 style=BodyCJK -->
早期信号包括工时实际变化、申诉处理、成员表达、招聘与外部机会；反向信号包括政策发布但执行缺失、公开安静而内部沉默增加。三个月后比较多圈层模型与简单基线，不能只挑中间某个命中信号宣布成功。

<!-- source-paragraph:V83-P2320 style=BodyCJK -->
有限选择至少比较：维持现状；只做公关回应；立即资源调整；先做可逆的工时与申诉试点；延迟重大重组以收集信息；允许团队成员转移；当前不做结构行动但加强保护与观察。每项都要检查权限、无法退出者、成本分配、跨圈层声誉与家庭影响、停止和补救。模型可以显示哪些方案在哪些条件下更可能改变路径，但最终选择仍取决于规范前提、合法授权和受影响者程序。在这些条件下，模型也应明确当前分析推荐、落选理由、代价及改判条件；推荐不改变尚未取得的执行权限。

<!-- source-paragraph:V83-P2321 style=SecH2 -->
## 12.14　何时选择不做

<!-- source-paragraph:V83-P2322 style=BodyCJK -->
不做可能是谨慎，也可能是逃避。以下情形支持当前不行动或只做保护性观察：对象与事实尚不清楚；行动不可逆而证据不足；权限缺失；保护底板未满足；预计行动会把成本转嫁给无法退出者；简单基线与复杂模型均无法区分路径；现有恢复过程可能被外部干预打断。

<!-- source-paragraph:V83-P2323 style=BodyCJK -->
以下情形使不行动必须接受更严格审查：持续伤害正在发生；不作为强化既得优势；负责主体有明确法定义务或承诺；低权力位置无法自行退出；延迟会造成不可逆锁定；以“等待更多证据”为由无限推迟。此时即使不采取主行动，也可能需要最小保护、信息公开、申诉通道或临时承接。

<!-- source-paragraph:V83-P2324 style=SecH2 -->
## 12.15　本部分的停止位置

<!-- source-paragraph:V83-P2325 style=BodyCJK -->
条件前瞻层可以发布有目标、有期限、有基线、有信号、有校准和有回写的判断。有限选择层可以在规范、保护与授权都明确时比较行动、延迟、试探、退出和不行动，并给出条件化、可撤回的选择记录。尚未取得执行授权时，仍可在证据与明示规范前提允许的范围内完成分析推荐，完整说明选项、反方、分配后果和改判条件；其现实采用状态须另行登记。

<!-- source-paragraph:V83-P2326 style=BodyCJK -->
它们不能保证未来，不能消除价值冲突，不能替代法律、专业规范、受影响者参与和现实授权，也不能把模型准确率兑换成统治资格。任何越过这些边界的调用都应由第十三部分的工具闸阻止，并由第十六部分治理、暂停或退役。

<!-- source-paragraph:V83-P2327 style=SecH2 -->
## 12.16　面向读者的发布格式

<!-- source-paragraph:V83-P2328 style=BodyCJK -->
对外发布时，默认交付完整分析，开头直接给出当前判断及范围，随后完整展开条件、证据与不确定性。正文应保留当前截止时点、目标与期限、对象和圈层范围、简单基线、全部已经开展的实质路径比较、每条路径成立条件、早期与反向信号、表达强度、暂停和下一次复核。不得以不改变主结论、属于次要分支或不是决定性理由为由删去实质分析；不得把条件藏在脚注，或用“模型认为”替代证据责任。只有用户明确要求简答或规定较短篇幅时才压缩可见答案，并继续保存完整分析。超出单次容量时按章节连续交付并提供完整文件，说明尚未交付范围；摘要、附件链接与覆盖标记不能替代正文论证。

<!-- source-paragraph:V83-P2329 style=BodyCJK -->
有限选择的分析应明确已经进入规范层，完整列出价值前提、决定主体、受影响位置、保护底板、可选方案、行动与不行动的分配后果、授权状态、行动上限、停止、回滚和补救。可以先给出当前分析推荐，再完整说明接受与排除各方案的理由、代价、反对意见及改判条件。若授权尚未通过，明确推荐供审议、现实执行尚未获准，不能用祈使语气伪装成可执行决定，也不能因没有执行权限而把已有依据的分析取舍退回问题清单。

## V83-T055

<table data-source-table="V83-T055">
<tr>
<td data-source-cell="1,1" data-paragraphs="V83-P2330">
<!-- source-paragraph:V83-P2330 style=TableHead -->
<pre>发布状态</pre>
</td>
<td data-source-cell="1,2" data-paragraphs="V83-P2331">
<!-- source-paragraph:V83-P2331 style=TableHead -->
<pre>可使用的表述</pre>
</td>
<td data-source-cell="1,3" data-paragraphs="V83-P2332">
<!-- source-paragraph:V83-P2332 style=TableHead -->
<pre>必须避免</pre>
</td>
</tr>
<tr>
<td data-source-cell="2,1" data-paragraphs="V83-P2333">
<!-- source-paragraph:V83-P2333 style=TableText -->
<pre>仅解释</pre>
</td>
<td data-source-cell="2,2" data-paragraphs="V83-P2334">
<!-- source-paragraph:V83-P2334 style=TableText -->
<pre>“现有证据支持机制 A，并保留 B”</pre>
</td>
<td data-source-cell="2,3" data-paragraphs="V83-P2335">
<!-- source-paragraph:V83-P2335 style=TableText -->
<pre>“因此下一步必然发生”</pre>
</td>
</tr>
<tr>
<td data-source-cell="3,1" data-paragraphs="V83-P2336">
<!-- source-paragraph:V83-P2336 style=TableText -->
<pre>仅推演</pre>
</td>
<td data-source-cell="3,2" data-paragraphs="V83-P2337">
<!-- source-paragraph:V83-P2337 style=TableText -->
<pre>“若 X 持续且 Y 发生，路径 P 获得支持”</pre>
</td>
<td data-source-cell="3,3" data-paragraphs="V83-P2338">
<!-- source-paragraph:V83-P2338 style=TableText -->
<pre>“模型预测 P 已经确定”</pre>
</td>
</tr>
<tr>
<td data-source-cell="4,1" data-paragraphs="V83-P2339">
<!-- source-paragraph:V83-P2339 style=TableText -->
<pre>已登记前瞻</pre>
</td>
<td data-source-cell="4,2" data-paragraphs="V83-P2340">
<!-- source-paragraph:V83-P2340 style=TableText -->
<pre>“在期限 T 内，P 当前优先于 Q，见反向信号 S”</pre>
</td>
<td data-source-cell="4,3" data-paragraphs="V83-P2341">
<!-- source-paragraph:V83-P2341 style=TableText -->
<pre>隐去基线、期限和失败条件</pre>
</td>
</tr>
<tr>
<td data-source-cell="5,1" data-paragraphs="V83-P2342">
<!-- source-paragraph:V83-P2342 style=TableText -->
<pre>规范尚未通过</pre>
</td>
<td data-source-cell="5,2" data-paragraphs="V83-P2343">
<!-- source-paragraph:V83-P2343 style=TableText -->
<pre>“可在明示前提下分析推荐；若要现实执行，仍需 N、PF、J 与 O”</pre>
</td>
<td data-source-cell="5,3" data-paragraphs="V83-P2344">
<!-- source-paragraph:V83-P2344 style=TableText -->
<pre>“尚未取得授权但已可立即执行”</pre>
</td>
</tr>
<tr>
<td data-source-cell="6,1" data-paragraphs="V83-P2345">
<!-- source-paragraph:V83-P2345 style=TableText -->
<pre>已获外部授权</pre>
</td>
<td data-source-cell="6,2" data-paragraphs="V83-P2346">
<!-- source-paragraph:V83-P2346 style=TableText -->
<pre>“授权记录允许主体在上限内执行并按条件停止”</pre>
</td>
<td data-source-cell="6,3" data-paragraphs="V83-P2347">
<!-- source-paragraph:V83-P2347 style=TableText -->
<pre>把授权归因于模型</pre>
</td>
</tr>
</table>

<!-- source-paragraph:V83-P2348 style=BodyCJK -->
发布后的解释权也受治理。读者误把条件前瞻当确定预言、把人格候选当事实或把方案比较当命令时，发布者应更正，而不是利用误读扩大影响。任何更新都以新版本追加，原标题、概率、期限与失败记录保持可追踪。
