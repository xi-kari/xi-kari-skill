# 世界观加载协议

本协议把 v8.3 当作每次运行都要重新读取的理论源，不把一张摘要卡伪装成完整学习。

## 读取前冻结

先用一句话写出：用户要解决的对象、问题动作（解释/比较/推演/选择/表达）、观察时间窗、空间或组织范围、事实截止点，以及当前是否要求建议。用户的立场、情绪和期待不是证据，也不能预先决定结论。

## 源身份检查

1. 打开 `references/source/v8.3/source-manifest.json`。
2. 核对固定版本、原始哈希、语义哈希、源单元总数和 `reader_unit_count`。
3. 读取 manifest 的 `reader_units`，确认 sequence 连续、路径在仓库内、每卷内容哈希匹配。
4. 若出现缺卷、重复、顺序错、散列漂移或只剩摘要，停止声称 v8.3 完整运行，说明实际缺口。

## 21 卷完整读取

按 sequence 从第一卷读到第二十一卷，逐字处理正文、标题、表格和表内关系。阅读目标是理解原文相邻承接，不是搜几个关键词：

- 不用目录数量、概念数量、检索命中数或旧回答证明已读。
- 不把注册表、学习包或联读包当作原文替身；它们只能帮助定位和保持连续性。
- 在 `XK1` 为每卷生成 hash-bound `read receipt`，并由 runtime 汇总 4753 个源单元的覆盖状态；生产 profile 同时封存 `XK01-semantic-read-trace.json`。read receipt 与 trace import receipt 只证明读取和导入边界，不能替模型理解原文，也不能冒充作者进程凭证。
- 发现源文没有定义的变量时标记 `source_undefined`，不得自行补成正式 v8.3 概念。

读取完成后冻结 source-read artifact：全部 21 卷顺序闭合、理论定义与解释层分开、相邻概念关系保留、未定义字段和不确定处未被填平。该 artifact 进入新鲜验证，但不转储到用户正文。

## 全候选加载

完整源读之后，读取 `candidate-census.jsonl`、完整 registry、两个 inventory shard 以及所有正式概念卡。生产运行按 runtime-owned plan 逐项记录每个 candidate、canonical/structural card、required neighbor 和 continuity bundle 的路径、散列、read 状态、问题关系与既有 disposition；base receipt 与 XK4 complete 同时绑定该 trace。对全候选给出独立终态；route、continuity bundle 和 learning pack 只决定哪些概念进入当前问题的深推演，不能跳过其余候选的处置。新增一个概念、圈层、尺度或变量时，说明它比简单基线多解释了什么；没有增量时保留简单表示。

## 源与现实的隔离

现实检索可以修正当前事实、案例和机制权重，但不能改写 v8.3 的定义、禁用替代或授权上限。若现实材料与源概念冲突，分别记录“事实不符”“适用条件不满足”或“源卡待修复”，不静默折中。

## 失败与降档

源缺失、网络不可用、材料受保护或专业边界触发时，继续能完成的结构工作，明确能力缺口，降低结论档位，并给出补证、转交或停止条件。不要用流畅叙述掩盖未读或未检索。

## Source anchors

权威来源：v8.3 前言、第一至第五部分、第十三部分和第十六部分；本协议只规定源读取和版本绑定方法。
