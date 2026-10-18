# 主张台账

用于一个任务里有多项判断需要分别追踪依据、反方与改判条件的场合：结论较多、材料与判断交织，或用户需要跨轮追踪前瞻。先按相应模块完成判断，需要管理时再使用台账；正文写清预测及其时点、条件和依据，也可以保留原判断，不必另建清单。

少量、容易记住的结论可以直接在正文里写清依据。台账的意义在于不让“这项判断到底靠什么成立、什么会推翻它”散落在长文各处。

## 记录什么

每条主张是一个JSON对象，至少包含：

| 字段 | 含义 |
| --- | --- |
| `id` | 稳定标识；修订时用新`id`加`supersedes`保留旧记录，不覆盖 |
| `statement` | 主张本身，用可以判断真假的陈述句 |
| `kind` | `fact`、`structure`、`mechanism`、`forward`、`value`或`interpretation` |
| `status` | `proposed`、`supported`、`contested`、`refuted`、`withdrawn`或`unknown` |
| `theory` | 所依据的原文小节，如`{"section": "4.17"}` |
| `evidence` | 所依据的材料片段：`catalog`、`clip`与`direction`（`supports`/`undercuts`/`context`） |
| `reasons` | 从依据到该主张的实际推理步骤，不是重复结论 |
| `change_conditions` | 出现什么会使该主张改变；承担关键结论的主张必须填写 |
| `counterclaims` | 仍然成立的竞争主张；`status=contested`时必填 |
| `load_bearing` | 是否为关键结论；为真时强制要求`change_conditions`与`counterclaims` |
| `registration` | `kind=forward`时，在结果之前登记的`window`、`baseline`与`criteria` |
| `forecast_ref` | `kind=forward`时关联`forecast.py`的冻结登记：`{"registry":"外部注册表绝对路径","id":"前瞻id"}`；可以替代`registration`摘要 |

`theory`与`evidence`分开：前者是理论定义或合同，后者是本题的现实材料。理论小节只证明理论内部关系，材料片段只支持其声明的范围，两者都不能自动互换。

`references/`把判断与依据分开，`open_questions`保留尚未分清的实质分歧。台账不生成置信度、可靠性分数或“证据充分”的认证。

## 前瞻判断

需要用台账追踪前瞻时，先按[条件前瞻模块](../modules/forecast/MODULE.md)冻结预测窗口、基线和判据，再以`forecast_ref`关联登记。`registry`使用外部注册表的绝对路径，`id`指向其中一个固定阶次的前瞻。结果实际到来后由`forecast.py resolve`追加，原判断继续保留。已有`registration`摘要仍可读取；新前瞻使用完整登记。

有`forecast_ref`时，`add`与`check`读取注册表、核对冻结记录完整性与前瞻标识。关联主张标为`supported`时，所指前瞻必须已有最新的`supported`到期结果，并保留主张原有的依据要求；链接存在本身不表示预测成立。未关联完整登记的旧主张仍要求非空`outcome`。结构检查不判断现实来源、目标判定或支持性依据是否充分。

第一、第二、第三阶分别使用前瞻标识；不得把一阶结果当成二三阶的支持。更换目标、期限、范围或路径时，新建前瞻及主张，用`supersedes`保留旧记录。结果从未决转为可判定时继续追加，旧回写保留在原注册表。

## 命令

工具需要Python 3.10以上，仅使用标准库。以下PowerShell命令使用`$skillRoot`表示当前`SKILL.md`所在安装目录，`$taskRoot`表示安装外的用户任务目录，可从任意当前目录调用；路径设置见[宿主接入](host-setup.md)。台账放在任务文件旁，不写入技能目录或全局记忆。

```powershell
python "$skillRoot/scripts/claims.py" --ledger "$taskRoot/主张.json" add --record "$taskRoot/claim-capacity.json"
python "$skillRoot/scripts/claims.py" --ledger "$taskRoot/主张.json" list
python "$skillRoot/scripts/claims.py" --ledger "$taskRoot/主张.json" search "容量 复核"
python "$skillRoot/scripts/claims.py" --ledger "$taskRoot/主张.json" show capacity-1
python "$skillRoot/scripts/claims.py" --ledger "$taskRoot/主张.json" check
```

`check`从磁盘重新读取台账，使用材料工具相同的规则校验材料目录结构，再核对`theory`小节是否在原文索引中，以及`evidence`片段是否在相应材料目录中，并报告缺少支持范围或结构不齐的地方。目录中的来源或片段结构损坏、关联不存在、引用片段缺失时均返回错误。它回答的是“引用能否解析、已声明结构是否齐全”，不是“依据是否充分、来源是否可信、分析是否完成”。退出码为1表示存在需要处理的错误。

台账与材料目录配合使用：先用[材料与证据](evidence-work.md)登记材料并保存片段，再在主张里引用片段标识。`check`读取已保存的片段；原文件变化、丢失或提取版本更新，不会使结构合法的旧片段无法解析，也不表示旧片段仍描述当前事实。目录结构和片段引用可解析，不表示片段支持该主张；支持范围由作者在登记片段与写主张时分别声明。材料目录JSON支持UTF-8及可选的BOM。

同一台账同时由一位作者负责写入。工具用同目录独占写锁保护最后的重读、比较和原子提交，拒绝重复标识、不可识别的台账文件、已经变化的旧内容以及所指旧主张不存在的`supersedes`；遇到写锁或版本冲突，重读后重新处理，不静默重放。

## 交付时的用途

- 组装长文时，逐条核对承担关键结论的主张是否都有依据、理由与改判条件，避免结论与依据脱节。
- 主张改变时，沿依赖找出真正受影响的解释、方案、条款与图表，而不是只改一处措辞。
- 跨轮接续时，先读台账恢复“哪些已经成立、哪些仍在争、哪些已撤回”，再决定本轮深入哪里。
- 对外交付时，把`id`还原成读者能用的标题、日期、来源与位置，不把管理字段当引用。

台账是工作材料，不是正文。最终成果仍然完整写出论证；台账只帮助作者不遗漏已有依据和未决分歧。
