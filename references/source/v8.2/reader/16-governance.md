# 第十六部分　治理

Source: `v8.2`
Raw SHA256: `670e90e0073eb1a7575a75c4e0a410630ce16bd5a10f2456b83c82480333de3f`
Semantic SHA256: `4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0`
List structure SHA256: `8b4a40f8559ac61c1bb8c224054de7978bb93298efbbd41f40ed065f89bab050`
Paragraph range: `V82-P2777`-`V82-P2905`
Tables: `none`

<!-- This is a lossless reader edition; anchors are source coordinates. -->

<!-- source-paragraph:V82-P2777 style=PartTitle -->
# 第十六部分　治理

<!-- source-paragraph:V82-P2778 style=BodyCJK -->
框架用来解释别的对象，不意味着它自己没有结构问题。文档会膨胀，概念会固化，工具会被权力捕获，使用者会对已投入的语言产生身份依赖。因此，治理层不是一组装饰性原则，而是一套能让概念降级、断言暂停、发布阻断、版本回滚、框架被替代的实际接口。

<!-- source-paragraph:V82-P2779 style=BodyCJK -->
本部分治理四个不同对象：当前文本与模板，概念之间的关系，使用者的实际实践，以及维护者、批评者、反例提供者和受影响者所构成的社群。四者不能混成一个“框架”：文档自洽，不等于实践没有误用；社群活跃，不等于根假设已被验证。

<!-- source-paragraph:V82-P2780 style=BodyCJK -->
框架不能用自己的语言证明自己安全。内部一致、压力测试通过、校验器通过和报告齐全，都只能证明某些过程产物已完成。它们不能证明现实安全、修复有效、受影响者同意，更不产生现实行动授权。

<!-- source-paragraph:V82-P2781 style=BodyCJK -->
这条边界同时写入机器不变量：框架不得自证，治理记录不得自发生成现实行动授权，已替代或已退休的终态不得回到 active，applied 变更必须有可解析的外部批准，别名、自报 independent=true 和自签发授权均不构成通过。任何相反许可文字都不能覆盖这些结构化约束。

<!-- source-paragraph:V82-P2782 style=SecH2 -->
## 16.1　GOV-01 框架自诊与对象分离

<!-- source-paragraph:V82-P2783 style=BodyCJK -->
自诊的第一步不是给整套框架一个笼统的“健康”结论，而是先说明正在检查什么。

<!-- source-paragraph:V82-P2784 style=ListPara -->
● 文档对象：文本、目录、定义、模板和规则是否相互矛盾。

<!-- source-paragraph:V82-P2785 style=ListPara -->
● 概念对象：根假设、通用变量、人类适配器、规范选择与行动程序是否越界。

<!-- source-paragraph:V82-P2786 style=ListPara -->
● 实践对象：使用者实际如何做诊断、管理、教学、公开表达和 AI 调用。

<!-- source-paragraph:V82-P2787 style=ListPara -->
● 社群对象：谁掌握命名、合并、解释与发布权，谁承担误用后果。

<!-- source-paragraph:V82-P2788 style=BodyCJK -->
每次自诊的最低记录包括：对象类型、版本、权利持有者、反例入口、已观察伤害、证伪条件和判断上限。若术语依赖、认知锁定、专家垄断、商业化迎合或 AI 合规包装已经产生伤害，可将相关模块收缩、暂停或送入替代评估。

<!-- source-paragraph:V82-P2789 style=SecH2 -->
## 16.2　GOV-02 共识程序与版本权限

<!-- source-paragraph:V82-P2790 style=BodyCJK -->
“大家最后同意”不是有效共识。有效共识指不同意见能安全进入、被记录、被回应，并能实质改变文本与实践。程序至少有七个环节：

<!-- source-paragraph:V82-P2791 style=ListPara -->
1. 议题登记：概念引入、重大改写、根假设调整、误用案例和反例先成为可追踪议题。

<!-- source-paragraph:V82-P2792 style=ListPara -->
2. 材料公开：列出案例、反例、用户反馈、外部研究、实践失败与伦理风险。

<!-- source-paragraph:V82-P2793 style=ListPara -->
3. 影响对象识别：指明改动会影响哪些使用者、被诊断者、低权力主体与场景。

<!-- source-paragraph:V82-P2794 style=ListPara -->
4. 异议入口：低权力使用者、被诊断对象、非专业读者与外部批评者都能提交。

<!-- source-paragraph:V82-P2795 style=ListPara -->
5. 决策分级：小修订、核心概念改动与根假设变更不共用同一权限。

<!-- source-paragraph:V82-P2796 style=ListPara -->
6. 少数意见保留：未采纳反对意见不删除，进入保留反例与未决问题。

<!-- source-paragraph:V82-P2797 style=ListPara -->
7. 版本写回：说明引入、删除、降级、理由和会让该项改动撤回的证据。

<!-- source-paragraph:V82-P2798 style=BodyCJK -->
若异议不能改变文本，程序只能记为 nominal_only，不能用来恢复已暂停模块。不同组织、法域和社群的人员抽选、任期、时限与法定权限必须按具体场景另行预注册；任何统一数值都不得脱离组织、法域、风险和资源条件直接照搬。

<!-- source-paragraph:V82-P2799 style=BodyCJK -->
异议不能只留一个“已阅”标记。每条异议必须有 disposition、处置理由，以及对文本、流程或行动上限的具体效果；已采纳效果要绑定版本日志中的实际 change_id。若所有异议都被拒绝、忽略或仍未解决，治理变更不得进入 applied。

<!-- source-paragraph:V82-P2800 style=SecH2 -->
## 16.3　GOV-03 根假设证伪、断言降级与暂停

<!-- source-paragraph:V82-P2801 style=BodyCJK -->
根假设和公开断言都有生命周期，不是一旦写进文本就永久生效。

<!-- source-paragraph:V82-P2802 style=BodyCJK -->
根假设的五个状态依次为：

<!-- source-paragraph:V82-P2803 style=ListPara -->
● normal_use：在明示边界内正常使用，但每个实例仍需证据。

<!-- source-paragraph:V82-P2804 style=ListPara -->
● boundary_restricted：对象、尺度、文化、制度或极端场景中解释力下降，必须缩小范围。

<!-- source-paragraph:V82-P2805 style=ListPara -->
● suspended：在某类对象中持续制造误判，只能作历史候选，不得进入强诊断。

<!-- source-paragraph:V82-P2806 style=ListPara -->
● replacement_competition：替代假设用更低概念成本、更少误伤和更清证据边界解释同一批现象。

<!-- source-paragraph:V82-P2807 style=ListPara -->
● retired_from_core：根假设只保留为领域规则、表达隐喻或历史阶段产物，不再约束整体。

<!-- source-paragraph:V82-P2808 style=BodyCJK -->
公开断言的状态是 internal_draft → open_assertion → publishable，但任何阶段都可转向 downgraded、suspended、publication_blocked、withdrawn 或 replaced。框架整体也只能在 active、boundary_restricted、suspended、replacement_competition、replaced 和 retired 之间运行。

<!-- source-paragraph:V82-P2809 style=BodyCJK -->
retired_from_core、withdrawn、replaced 与 retired 是终态：没有指向 active 或其他在役状态的出边，也不能借回滚恢复旧授权。后继方法若重新进入，只能使用新的可识别身份、重新取得外部授权并保留旧终态的历史轨迹。

<!-- source-paragraph:V82-P2810 style=BodyCJK -->
重复反例、稳定误判某类主体、不断扩大解释范围、只靠“对方不是系统”“时间还不够”“证据还不够深”逃避反驳，都会触发暂停审查。反例必须产生文本后果：轻微反例改边界，重复反例降级，高伤害反例暂停，系统性反例开启替代竞争，误用反例阻断公开使用，不可修复案例转交 T4 评估。

<!-- source-paragraph:V82-P2811 style=SecH2 -->
## 16.4　GOV-04 案例、反例、断言与前瞻追踪

<!-- source-paragraph:V82-P2812 style=BodyCJK -->
五类权威记录彼此关联，却不互相代替：

<!-- source-paragraph:V82-P2813 style=ListPara -->
● COUNTEREXAMPLE-REGISTRY：记反例对象、尺度窗口、可观察事实、非噪声理由、原解释、替代解释、处置要求和后续信号。

<!-- source-paragraph:V82-P2814 style=ListPara -->
● CASE-REGISTRY：同时保存成功、失败、早期消散、进程未结、反例、无法判定和被排除案例。被排除案例要记录“资料不足本身是否是框架盲区”。

<!-- source-paragraph:V82-P2815 style=ListPara -->
● CLAIM-REGISTRY：记断言文本、类型、对象、尺度、受影响位置、证据、反证、替代解释、撤回条件、行动上限与公开状态。

<!-- source-paragraph:V82-P2816 style=ListPara -->
● FORECAST-REGISTRY：记预测、时间窗口、触发、早期信号、反向信号、竞争预测与到期结果。它是条件前瞻，不是命运判决。

<!-- source-paragraph:V82-P2817 style=ListPara -->
● VERSION-LOG：把反例、边界收缩、降级、暂停、发布阻断、撤回、替代、退休、回滚和补救写成公开账本。

<!-- source-paragraph:V82-P2818 style=BodyCJK -->
没有 CLAIM-REGISTRY 记录的判断只能是内部思路，不能成为公开文本、组织处置或自动化输出。案例留痕多不等于更普遍，内部挑选案例也不等于外部验证。

<!-- source-paragraph:V82-P2819 style=BodyCJK -->
治理变更另有七类运行时注册表：canonical actor、证据、利益关系、授权、外部评审、异议和结构化 VERSION-LOG。所有 evidence_ref 必须解析到完整性为 verified 的证据记录；评审者、决定成员与授权主体必须使用 canonical actor ID，并逐对检查其与提案者的经费、评价、身份、晋升、控制和商业利益关系。别名只能检索，不能代替身份；授权签发者不得同时是持有人或提案者。

<!-- source-paragraph:V82-P2820 style=SecH2 -->
## 16.5　GOV-05 前概念闸与概念有效性上限

<!-- source-paragraph:V82-P2821 style=BodyCJK -->
框架不能先把一个东西硬套成“结构域”，再用自己的概念证明它是结构域。正式映射前先用白话回答：它是否能被一起观察，是否有最低边界，内部行动是否反复影响，是否有共同问题、方向、风险或约束，谁在承担维持成本，结果或坏消息能否改变后续做法。

<!-- source-paragraph:V82-P2822 style=BodyCJK -->
前概念闸不通过，只能进行现象描述、风险登记或叙事分析。通过后，概念仍只能处在五个强度之一：

<!-- source-paragraph:V82-P2823 style=ListPara -->
● 表达级：只帮助说清感受或相似性。

<!-- source-paragraph:V82-P2824 style=ListPara -->
● 探索级：只能生成问题和观察信号。

<!-- source-paragraph:V82-P2825 style=ListPara -->
● 诊断级：有外部可观察材料，可形成低到中置信判断。

<!-- source-paragraph:V82-P2826 style=ListPara -->
● 强判断级：对象、证据、尺度、责任和观测门均通过。

<!-- source-paragraph:V82-P2827 style=ListPara -->
● 处置级：额外需外部复核、申诉、反报复、补偿和撤回，且仍需第十四部分规范选择、J 授权和 O 程序。

<!-- source-paragraph:V82-P2828 style=SecH2 -->
## 16.6　GOV-06 缺席信号、保护性不透明与压制性不透明

<!-- source-paragraph:V82-P2829 style=BodyCJK -->
不可见不是无信息。锚点缺席可能表示从未形成共同指向；反馈缺席可能表示通道不存在或主体不敢说；冲突缺席可能来自恐惧、依赖与惩罚；修复缺席可能意味着没有修复接口；退出缺席可能是离开代价不可承受；语言缺席则可能是没有可用的表达工具。

<!-- source-paragraph:V82-P2830 style=BodyCJK -->
不透明分三类：

<!-- source-paragraph:V82-P2831 style=ListPara -->
● protected：保护脆弱主体、隐私、证人安全、未成熟经验和低权力反馈。

<!-- source-paragraph:V82-P2832 style=ListPara -->
● functional：降低信息过载，保留必要的专业判断、仪式空间、缓冲区或决策安静区，但必须事后复核和责任追踪。

<!-- source-paragraph:V82-P2833 style=ListPara -->
● suppressive：遮蔽责任、阻断反馈、逃避复核、制造恐惧、维持权力垄断或让受损者无法证明伤害。

<!-- source-paragraph:V82-P2834 style=BodyCJK -->
分类必须回答四问：保护谁，谁受益，谁能独立复核，何时解除。四问、独立复核、时间边界和解除条件不完整，不得将不透明登记为健康边界。压制性不透明直接触发反捕获、外部复核和公开发布阻断。

<!-- source-paragraph:V82-P2835 style=SecH2 -->
## 16.7　GOV-07 阶段6运作边界与观测递归收束

<!-- source-paragraph:V82-P2836 style=BodyCJK -->
本模块的限定引用是 governance.module.GOV-07 → hsp.domain.human_intentional_collective → hsp.state.S6。它只适用于已由独立运行时记录确认为“人类有意图集体”且状态包含 hsp.state.S6 的对象；不适用于个体人类、非人系统，也不适用于尚未满足 S6 的人类集体。这里的阶段6不是广义世界的普遍层级。

<!-- source-paragraph:V82-P2837 style=BodyCJK -->
阶段6不是超越熵增或完美系统，只表示在有限时间窗内，发现、修复、写回和承接者再生产暂时快于损耗累积。不能只因“现在运转良好”就宣称阶段6，必须记录发现时滞、修复时滞、复发率、修复副产物和修复负荷分布。

<!-- source-paragraph:V82-P2838 style=BodyCJK -->
观测递归可扩张，仅当新反应改变边界、身份、资源、行动通道、承接关系、反馈写回、风险或公共记忆，或提供新高成本信号。连续两轮只有同类反应、对象开始操纵诊断规则、继续追踪会增加暴露、信息收益低于结构扰动，或诊断者已不能区分对象状态与观测产物时，必须收束。

<!-- source-paragraph:V82-P2839 style=BodyCJK -->
收束后不再追问“对象到底是什么”，只说：在当前观测条件下，可确认某种反应模式；若要继续判断，需外部复核或新高成本证据。

<!-- source-paragraph:V82-P2840 style=SecH2 -->
## 16.8　GOV-08 恶意合规与选择性证据审计

<!-- source-paragraph:V82-P2841 style=BodyCJK -->
恶意合规不是公然违规，而是选择性地完成表格、证据链、复核和申诉程序，同时继续操纵来源、过滤弱信号、包装不作为或责任漂白。十个信号必须逐项检查：来源单一；反例被降为噪声或情绪；开放断言变成标签；申诉从不改结果；独立者受同一权力链控制；AI 报告无原始材料和外部核验；诊断语言被用于不行动或不追责；势场、熵增、阶段被用来包装不作为；爱、使命、大局、专业被用来继续抽取低权力主体；申诉者因申诉被反写为不理性。

<!-- source-paragraph:V82-P2842 style=BodyCJK -->
三项及以上，阻断强判断；五项及以上，记为高度恶意合规风险，只输出风险登记、外部复核请求和保护性试探。被审计方不能自行确认复核者独立。

<!-- source-paragraph:V82-P2843 style=SecH2 -->
## 16.9　GOV-09 AI 边界与过程性产物非证明性

<!-- source-paragraph:V82-P2844 style=BodyCJK -->
AI 可以整理材料、对齐来源、生成问题、提示反例、压缩表达、生成模板、开放断言草案和复核清单。它不能虚构来源，不能证明委托方诚信，不能确认反报复和弱信号保护确实存在，不能替代现实复核和责任承担，不能独立作高风险决定。

<!-- source-paragraph:V82-P2845 style=BodyCJK -->
AI 输出必须列出原始事实记录、受影响位置证言、反例、低权力反馈、外部复核、申诉改结果的记录、证据控制关系和 AI 是否筛选或改写材料等缺失项。缺失超过三项时，自动降为轻量观察或问题清单。这是保守的使用上限，不是经过经验校准的风险分数。

<!-- source-paragraph:V82-P2846 style=BodyCJK -->
过程性产物不是现实证明。流畅文字、自动评分、内部压力测试、一致性矩阵、校验器通过、报告数量和表格完整，都不能证明修复、同意、安全或有效。

<!-- source-paragraph:V82-P2847 style=SecH2 -->
## 16.10　GOV-10 弱信号六件套保护

<!-- source-paragraph:V82-P2848 style=BodyCJK -->
弱信号不能只靠诊断者“愿意听”。WEAK-SIGNAL-PROTECTION 必须逐项登记：

<!-- source-paragraph:V82-P2849 style=ListPara -->
1. WS1 匿名或低暴露入口：提交事实不必先暴露身份。

<!-- source-paragraph:V82-P2850 style=ListPara -->
2. WS2 独立承接者：不只交给被质疑的权力链。

<!-- source-paragraph:V82-P2851 style=ListPara -->
3. WS3 反报复登记：反馈后的降权、孤立、污名、惩罚和资源变化都记录。

<!-- source-paragraph:V82-P2852 style=ListPara -->
4. WS4 分组校准：不用总体满意度或平均表现遮蔽边缘群体恶化。

<!-- source-paragraph:V82-P2853 style=ListPara -->
5. WS5 延迟公开：有安全风险时，先保护提供者，再讨论公开。

<!-- source-paragraph:V82-P2854 style=ListPara -->
6. WS6 写回证明：信号被采纳后，必须能看见规则、资源、责任或权威记录的实际变化。

<!-- source-paragraph:V82-P2855 style=BodyCJK -->
任一件缺失，只能说“已意识到弱信号风险”，不能说“已保护弱信号”。单一弱信号不直接生成定论，但它也不因低频、匿名、情绪化或形式不完整自动消失。

<!-- source-paragraph:V82-P2856 style=SecH2 -->
## 16.11　GOV-11 无制度基础设施的中间路径

<!-- source-paragraph:V82-P2857 style=BodyCJK -->
家庭、亲密关系、朋友、小团队和临时社群往往没有独立复核者、稳定申诉和完整证据链，却可能存在持续伤害、信息控制、关系依赖、声誉或安全风险。NO-INFRASTRUCTURE-PATH 不强行模拟不存在的制度，不要求受影响者冒险取证，也不把“无法复核”等同于“所有事实都不能记录”。

<!-- source-paragraph:V82-P2858 style=BodyCJK -->
它只能输出保护性开放断言：明示当前材料、最值得警惕的持续模式、禁止用途、升级信号、撤回信号和低风险下一步。行动目标从“证明谁错”改为降低暴露、保留记录、恢复支持、寻求外部视角和观察后续信号。它不能被用于惩罚、档案、资格、公开定性或资源剥夺。

<!-- source-paragraph:V82-P2859 style=SecH2 -->
## 16.12　GOV-12 无法退出主体保护

<!-- source-paragraph:V82-P2860 style=BodyCJK -->
儿童、严重依赖者、经济来源受控者、被监禁者、被照护绑定者或极低资源主体可能无法退出。不退出不等于同意。INABILITY-TO-EXIT-PROTECTION 要求六项保护：安全优先，可信代理，恢复最小选择、信息、记录和支持连接，低暴露记录，局部缓冲与替代出口，以及禁止把无法退出浪漫化为爱、忠诚、成熟、牺牲或大局。

<!-- source-paragraph:V82-P2861 style=BodyCJK -->
当事人不应被要求用继续暴露来证明自己的处境。允许代理提交、延迟表达、分阶段披露、外部承接、证据保全和拒绝直接对话。保护目标不是强迫理想退出，而是在不可退出条件下减少伤害、保存主体性并扩大未来选择。

<!-- source-paragraph:V82-P2862 style=SecH2 -->
## 16.13　GOV-13 复杂创伤与无健康基准

<!-- source-paragraph:V82-P2863 style=BodyCJK -->
不是所有结构都曾有健康状态。问题需先区分：曾有较健康结构后偏离，名义锚点仍在但实际空心，从未形成健康锚点的初建型，以及规则、身份、边界和关系本就由创伤建成的创伤建材型。

<!-- source-paragraph:V82-P2864 style=BodyCJK -->
对后两者，TRAUMA-NO-HEALTHY-BASELINE 不问“怎样回到原来”，而问：当前最低安全是什么，主体是否首次获得可预测支持，是否有不被惩罚的表达入口，是否有可重复的小信任，哪些生存策略曾经起保护作用却正在形成限制，新锚点是被发现还是需要共同建造。

<!-- source-paragraph:V82-P2865 style=BodyCJK -->
治疗性、临床、照护、儿童保护或法律判断必须由相应专业程序接管，框架不能用自己的理论发明一个健康过去。

<!-- source-paragraph:V82-P2866 style=SecH2 -->
## 16.14　GOV-14 开放承担、规范前提与隐喻漂移分流

<!-- source-paragraph:V82-P2867 style=BodyCJK -->
爱不是“结构解释不了的剩余”，也不是一个首选动机标签。开放承担的记录必须有两条线：既有利益、恐惧、身份收益、制度激励、惯性和依附能解释多少的结构线，也有某个行动是否承担本可回避的真实成本并打开新可能的生成事件线。只有承担者的行动，没有受影响位置更安全、更可拒绝、更可申诉的现实条件，不称开放承担。

<!-- source-paragraph:V82-P2868 style=BodyCJK -->
规范前提必须公开转交第十四部分。保护低权力主体、反对用结构语言取消责任、倾向可申诉、可撤回与承接者再生产，都是本框架公开承担的价值边界，不是从事实中自动推出的中性结论。

<!-- source-paragraph:V82-P2869 style=BodyCJK -->
跨域概念必须标记身份：隐喻、类比、机制候选、经验旁证、形式模型或已验证规则。“像”不能改写成“遵循”；物理、生物和动物行为案例不直接证明人类组织和制度结论。每个隐喻都要说明相似点、不相似点、误用风险和停用证据。

<!-- source-paragraph:V82-P2870 style=SecH2 -->
## 16.15　GOV-15 知识谱系与来源透明

<!-- source-paragraph:V82-P2871 style=BodyCJK -->
每个能追溯的概念都要记录其思想亲缘、具体来源、版本、保留了什么、改造了什么、放弃了什么、跨文化和跨领域风险，以及来源能支持什么和不能支持什么。标注思想亲缘不会削弱框架，反而能降低神秘化和教条化。

<!-- source-paragraph:V82-P2872 style=BodyCJK -->
理论材料不代替案例证据，单一案例不代替普遍规则，内部总结不代替原始记录，AI 摘要不代替可追踪来源。本框架与其他理论建立互操作接口，不把自己写成吞并所有理论的总框架。

<!-- source-paragraph:V82-P2873 style=SecH2 -->
## 16.16　GOV-16 使用门槛债与可及性审计

<!-- source-paragraph:V82-P2874 style=BodyCJK -->
框架越复杂，越可能防止粗暴套用，也越容易形成六类门槛债：学习需时间与认知资源；白话与术语之间有翻译损失；证据难以安全收集；外部复核可能不存在；投入越多越难退出；“懂框架”的身份会带来解释权与社交资本。

<!-- source-paragraph:V82-P2875 style=BodyCJK -->
可及性不是给完整文本加一个简版就结束。必须提供白话、分级使用上限、代理或辅助表达、非文本材料入口、同等申诉权重，以及不学完框架也能先保护自己的路径。必须在适当时候明说：你不需要学会框架，也可以先保护自己、记录事实、寻求支持。

<!-- source-paragraph:V82-P2876 style=BodyCJK -->
没有等价申诉、保护和撤回入口，不得进入高影响、公开或自动化使用。术语熟练、阅读完整、内部认证或付费学习不构成外部资格。

<!-- source-paragraph:V82-P2877 style=SecH2 -->
## 16.17　GOV-17 工具化、商业化、武器化与分支风险

<!-- source-paragraph:V82-P2878 style=BodyCJK -->
课程、咨询、AI 工具、组织软件、评分表、审核表和公共标准在使用框架时，必须保留证据追踪、判断降级、低权力保护、申诉入口、反报复、人工复核、停止和撤回。不得把轻量模板包装成完整诊断，把内部认证包装成外部复核，把 AI 输出包装成独立调查，把客户满意度当成有效性证据，为交付强行出强诊断，让付费方单方控制证据、反馈和发布口径，或让“框架认证”成为新资格垄断。

<!-- source-paragraph:V82-P2879 style=BodyCJK -->
使用者围绕核心承诺持续分歧时，可形成分支版本。分支不是背叛；不承认分支，却在同一名称下运行不同框架，才是更大风险。每个分支必须说明保留的根假设、放弃的边界、修改的概念和新增的误用风险。

<!-- source-paragraph:V82-P2880 style=SecH2 -->
## 16.18　GOV-18 开放断言的权力捕获退场

<!-- source-paragraph:V82-P2881 style=BodyCJK -->
开放断言只是不确定中可修正的靶点。若它被重复引用为结论，进入考核、档案、处分、资格、资源分配或公共记忆，被用来压制申诉，被媒体、组织或 AI 截断成标签，成为“先观察”名义下的长期排斥与资源剥夺，或只保留判断内容而丢掉撤回条件，就必须退场。

<!-- source-paragraph:V82-P2882 style=BodyCJK -->
退场后，明确声明不得继续处置，重申证据边界、替代解释和撤回条件，删除或标注已误用记录。已有伤害则进入修复、补偿和责任链检查。若无法阻止误用，框架必须拒绝背书。

<!-- source-paragraph:V82-P2883 style=SecH2 -->
## 16.19　GOV-19 版本写回与反馈闭环

<!-- source-paragraph:V82-P2884 style=BodyCJK -->
版本日志不是发布说明的附属品，而是反例与治理决定的权威写回对象。每条反例、边界收缩、判断降级、暂停、阻断、撤回、替代、退休、回滚和补救，都要记录事件、时间、责任人、受影响 ID、旧状态、新状态、证据、反例、文本后果、流程后果、行动上限后果和下游写回。

<!-- source-paragraph:V82-P2885 style=BodyCJK -->
反例只被归档而不改文本、流程或行动上限，就没有形成反馈闭环。版本日志长期空白，不表示框架完美，反而触发“反馈通道可能已经中断”的外部审计。日志可用新条目更正，不删除原条目与失败轨迹。

<!-- source-paragraph:V82-P2886 style=BodyCJK -->
运行时 VERSION-LOG 不是一组自由文本引用。每条记录必须结构化解析并精确绑定治理 record_id、subject、source/target version、transition、旧状态、新状态和事件类型；版本号只接受规范的数字版本，source_version 必须等于当前受验证框架的 schema_version，target_version 必须严格递增，不能由同一包材料把 none、别名或虚构版本相互引用后自证。applied 还必须至少包含一项真实文本、流程或行动上限变更，并以不同的 before_hash 与 after_hash 证明发生了实际写回。评审、异议效果和下游修复都要指向同一条日志。

<!-- source-paragraph:V82-P2887 style=SecH2 -->
## 16.20　GOV-20 外部评审材料包与公开发布门禁

<!-- source-paragraph:V82-P2888 style=BodyCJK -->
内部压力测试只是内部风洞，用来发现术语误用、路径误判和内部不一致，禁止用来证明框架在现实中可靠、比替代方案更优，或用于营销和认证。

<!-- source-paragraph:V82-P2889 style=BodyCJK -->
外部评审材料包包含待评断言、追溯矩阵、公开状态、已知缺陷、评审问题与标准、评审者身份与利益冲突、反馈写回和评审者保护。评审类型包括来源追溯、受影响位置、领域专家、误用红队、公开语言和发布门禁评审。某类评审长期缺失，尤其是受影响位置评审长期为空，缺失本身就是发布阻断。

<!-- source-paragraph:V82-P2890 style=BodyCJK -->
外部性不能由评审者自报。评审者、决定成员、决定机构、授权签发者、授权范围、主体、目标版本、有效期和利益关系都必须从运行时注册表解析；外部批准记录还要精确绑定本次治理记录、subject、target version、transition 与异议清单。applied 只能消费决定为 approved 的外部评审，不能用同名别名、内部签章或自签发授权替代。

<!-- source-paragraph:V82-P2891 style=BodyCJK -->
每个对外强判断要逐项通过九项门禁：追溯完整性、来源质量、反例处理、受影响位置、负担转移、误用红队、公开语言、外部评审与强判断八件套。任一项不通过，不得作为强判断公开发布。全部通过只能得到 publishable，仍不产生行动授权。

<!-- source-paragraph:V82-P2892 style=SecH2 -->
## 16.21　GOV-21 框架良性消亡与替代接口

<!-- source-paragraph:V82-P2893 style=BodyCJK -->
框架的成熟不是解释一切，而是知道何时退场。良性消亡不一定是整套文本消失，也可以是某个概念、模块或根假设离开核心层。五类触发是：模块长期被更简单、更低误伤、更可证伪的方法替代；概念只增加理解成本而不增加诊断能力；根假设在关键领域持续依赖例外补丁；使用者为保住框架而压制外理论或现实反例；框架身份、商业或权力收益高于判断质量收益。

<!-- source-paragraph:V82-P2894 style=BodyCJK -->
替代时必须记明：本框架能判断到哪里，从哪里开始失效，后继方法接管什么，两者如何交叉校验，哪些记录与未解决伤害需移交，谁承担转接，何时生效。决策可以是 restrict、suspend、compete、replace、retire 或 handoff。框架创建者、维护者或商业受益者不得单方否决替代，也不得通过无限增加概念来永久保全自己。

<!-- source-paragraph:V82-P2895 style=BodyCJK -->
治理的总原则是：解释力越强，越要保留撤回；发布能力越强，越要保护低权力反例；自动化程度越高，越要将 AI 输出降为辅助材料。任何结构诊断都不能取消人的具体处境，也不能把责任溶解在复杂性、阶段、势场、熵增或爱之中。

<!-- source-paragraph:V82-P2896 style=SecH2 -->
## 16.22　GOV-22 多圈层复杂度与前瞻治理

<!-- source-paragraph:V82-P2897 style=BodyCJK -->
多圈层能力带来五类治理债：对象债，圈层因命名而被实体化；变量债，残差候选被自动补成事实；复杂度债，变量与路径增长但没有样本外增益；校准债，前瞻发布却不登记结果；权力债，预测被用于筛选、监控、惩罚或操纵。任一债务超过预先门槛时，框架应缩小模型、降低输出、暂停高影响用途或退役相应模块。

<!-- source-paragraph:V82-P2898 style=BodyCJK -->
前瞻注册表必须保留成功、失败、未决、目标失效和无法评价，不允许只公开命中案例。模型版本、输入截止、简单基线、指标和结果回写均可由外部审查者复核。长期校准恶化、跨群体误差集中、复杂模型不再优于基线或结果持续依赖事后变量时，前瞻能力声明自动降级。

<!-- source-paragraph:V82-P2899 style=SecH2 -->
## 16.23　GOV-23 人格、隐私与自动化越权治理

<!-- source-paragraph:V82-P2900 style=BodyCJK -->
人格假设属于高误用风险材料。治理必须检查收集目的、授权、隐私等级、允许用途、跨圈层传播、当事人申诉、删除或纠正、模型版本和下游影响。临床诊断、人格本质裁决、歧视性筛选、未经授权的风险评分和以沉默作为证据均为禁止用途。

<!-- source-paragraph:V82-P2901 style=BodyCJK -->
AI 可以提出变量候选和路径，不能验证现实、诊断人格、决定价值或签发权限。任何自动化系统若把 candidate 升级为 observed、把 simulated 升级为现实事件、把前瞻结果升级为授权，必须阻断运行并留下审计记录。所谓人工复核只有在复核者能看到证据、反例和不确定性，并拥有真实否决能力时才有效。

<!-- source-paragraph:V82-P2902 style=SecH2 -->
## 16.24　GOV-24 模型退化、退役与替代

<!-- source-paragraph:V82-P2903 style=BodyCJK -->
框架必须具备退役与替代机制。若某种更简单的方法在解释、前瞻、保护和可及性上持续更好，应通过替代接口移交案例、合同、失败记录和申诉，不以维护既有框架为目的。退役时保留必要的来源链、责任记录与伤害补救，停止把已退役模型用于新决定，并公开哪些结论仍有效、哪些降级、哪些不可迁移。

<!-- source-paragraph:V82-P2904 style=SecH2 -->
## 16.25　场景化参数与缺失处理

<!-- source-paragraph:V82-P2905 style=BodyCJK -->
以下参数必须由具体场景中的外部程序确定：共识参与者与时限；根假设恢复所需的观察窗、样本与决策者；弱信号安全渠道、托管者和补救机构；AI 缺失项之间的风险权重；以及跨学科、跨文化和跨法域的替代比较标准。登记时必须写明适用组织、法域、对象、风险等级、证据基础、有效期和复核条件，不得把一个场景的数值复制为普遍门槛。这些字段缺失时，结论保持降级、暂停或竞争，不由框架自行填满。
