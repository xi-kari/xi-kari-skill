---
{"id":"capability-quickstart","theory_sha256":"6ef2e508474d4ac1ad07d7e4e068955342c405b5f680afcfc40d68cca3d0149c","anchors":["1.3","1.10","2.14","3.4.1","4.18","4.19","5.10.2","13.1"]}
---

# 研究与领域工作的调用方式

以下请求在已启用 Xikari Skill 后按需选用。默认完整理论学习仍适用；同一问题的续问承接已有工作。示例结果演示工作方法，不代表任何真实机构或项目的效果。

## 从自然语言开始

| 所需成果 | 可直接使用的请求 | 接入位置 |
| --- | --- | --- |
| 完整研究与问题附篇 | 研究这些材料，写出充分的成果；另列当前解释不了、有争议或实现有缺口的部分，指明影响哪些结论。 | [研究入口](../modules/research/MODULE.md) |
| 领域对应与具体表达 | 把这些术语和关系接到本领域，保留当地定义、数据口径和专业方法；用它们写出一段可直接使用的说明。 | [领域映射](../modules/domain-mapping/MODULE.md) |
| 比较两套理论 | 准确重建双方主张，判断真冲突、异题与互补，给出比较专论及未决争点。 | [成果模式](output-modes.md) |
| 重建形成过程 | 用这些有日期的材料解释形成和转折，分开当时已知与事后取得的资料。 | [成果模式](output-modes.md) |
| 可审议安排 | 在真实人员、资源和时段内给出不同安排与取舍，并写完整约定及过渡。 | [成果模式](output-modes.md) |
| 经验或作品解释 | 细读这份完整材料，解释语境与不同声音，比较读法，理解本身可以是终点。 | [成果模式](output-modes.md) |
| 概念、中层模型或议程 | 针对具体混淆提出定义和改写；或构造有边界模型；或保留旧问题并提出可继续研究的新问法。 | [成果模式](output-modes.md) |
| 更正后的局部修订 | 这份来源已更正，找出真正受影响的结论，保留独立部分，同步主报告与问题附篇。 | 研究或映射工具的 `impact`，作者完成语义修订 |

## 可选的本地工具

先按本题需要选择主要工作记录。普通研究直接写完整正文与问题附篇；需要多结论排版和依赖修订时才使用研究 JSON，作为本次成稿快照。有既有记录时引用它们，不要求按表依次填五套文件。

| 眼前需要 | 保留的主要记录 |
| --- | --- |
| 找回多份材料、版本和原文片段 | `evidence` 来源目录 |
| 长期维护独立主张、反方和历史 | `claims` 主张台账 |
| 形成当前完整研究与问题附篇 | 自然语言成稿；需要程序排版和依赖修订时用 `research` 快照 |
| 跨作者或跨轮恢复实际工作 | 需要时使用 `task_state` |
| 需要他人继续采集可区分的材料 | 需要时使用 `study_design` |

这些工具使用 Python 标准库。进入技能目录运行命令，输出路径必须在技能目录之外。示例输入可以直接验证；真实任务先由作者完成相应研究内容，不能把运行示例当作任务已完成。

```text
python scripts/research.py --research assets/examples/research.json validate
python scripts/research.py --research assets/examples/research.json render --output ../xikari-task/research
python scripts/research.py --research assets/examples/research.json impact --changed S-register

python scripts/domain_mapping.py --mapping assets/examples/domain-mapping.json validate
python scripts/domain_mapping.py --mapping assets/examples/domain-mapping.json lookup --term 反馈
python scripts/domain_mapping.py --mapping assets/examples/domain-mapping.json impact --changed s-course
python scripts/domain_mapping.py --mapping assets/examples/domain-mapping.json render --output ../xikari-task/mapping.md
```

研究工具生成主体与问题两个文件，重大问题同时出现在相应正文处；映射查询遇到多个义项会返回歧义，不选一个假装唯一。变更影响只定位需要复核的内容，不自动宣布结论错误，也不自动改写源材料。输出已存在时换一个新位置，保留旧结果。

研究确实使用了一个领域包时，可用 [`mapping_ref`](research-format.md#领域映射的跨文件修订) 绑定实际用到的节点，再用 `research.py ... impact-mapping --mapping <所据旧快照> --changed <来源ID>` 跨文件定位。没有绑定的人工映射仍可用，但不属于自动传播范围；普通来源位置也不会被程序自动打开。修订仍须落实到完整正文，而不只是更新散列。

有限工具使用独立模型的 `validate` 和 `compute`，六种模型与命令见[有限工具指南](finite-tools.md)。分组、排程、组合搜索等结果只在输入合同内成立；搜索未完成与已证明无解分开。

## 使用真实领域包

从[领域包索引](domains/README.md)选任务范围相符的一包；先读来源、定义和限制，再核本题的机构、课程或技术版本。文档用于理解，配套 JSON 用于精确词查询、关系回查与变更定位。定义已取得并不表示本题的能力、权限、效果或恢复已经发生，真实任务还需要自己的材料。

正文应直接说谁、做什么、在何种条件下、依据什么、得到什么结果。理论术语帮助保留区别，不能替代领域细节；字段齐全也不能替代完整论述。
