# 主张台账

用于一个任务里有多项判断需要分别追踪依据、反方与改判条件的场合：结论较多、材料与判断交织、需要跨轮接续，或前瞻性判断要在取得结果之前先登记。它就是一张清单，不是评分器，也不是完成度证明。

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

`theory`与`evidence`分开：前者是理论定义或合同，后者是本题的现实材料。理论小节只证明理论内部关系，材料片段只支持其声明的范围，两者都不能自动互换。

`references/`把判断与依据分开，`open_questions`保留尚未分清的实质分歧。台账不生成置信度、可靠性分数或“证据充分”的认证。

## 前瞻判断

`kind=forward`的主张在取得结果之前先登记预测窗口、基线和判据，再在后来用新记录追加`outcome`。工具会拒绝把尚未登记结果的前瞻主张标成`supported`。这样，事后容易变成“本来就是这个意思”的判断保留其原来的登记时间与判据。

## 命令

工具需要Python 3.10以上，仅使用标准库。以下PowerShell命令使用`$skillRoot`表示当前`SKILL.md`所在安装目录，`$taskRoot`表示安装外的用户任务目录，可从任意当前目录调用；路径设置见[宿主接入](host-setup.md)。台账放在任务文件旁，不写入技能目录或全局记忆。

```powershell
python "$skillRoot/scripts/claims.py" --ledger "$taskRoot/主张.json" add --record "$taskRoot/claim-capacity.json"
python "$skillRoot/scripts/claims.py" --ledger "$taskRoot/主张.json" list
python "$skillRoot/scripts/claims.py" --ledger "$taskRoot/主张.json" search "容量 复核"
python "$skillRoot/scripts/claims.py" --ledger "$taskRoot/主张.json" show capacity-1
python "$skillRoot/scripts/claims.py" --ledger "$taskRoot/主张.json" check
```

`check`从磁盘重新读取台账，核对`theory`小节是否在原文索引中，以及`evidence`片段是否在相应材料目录中，并报告缺少支持范围或结构不齐的地方。它回答的是“引用能否解析、已声明结构是否齐全”，不是“依据是否充分、来源是否可信、分析是否完成”。退出码为1表示存在需要处理的错误。

台账与材料目录配合使用：先用[材料与证据](evidence-work.md)登记材料并保存片段，再在主张里引用片段标识。`check`只确认片段存在，不会因为片段存在就认为它支持该主张——支持范围由作者在登记片段与写主张时分别声明。

同一台账同时由一位作者负责写入。工具用同目录独占写锁保护最后的重读、比较和原子提交，拒绝重复标识、不可识别的台账文件、已经变化的旧内容以及所指旧主张不存在的`supersedes`；遇到写锁或版本冲突，重读后重新处理，不静默重放。

## 交付时的用途

- 组装长文时，逐条核对承担关键结论的主张是否都有依据、理由与改判条件，避免结论与依据脱节。
- 主张改变时，沿依赖找出真正受影响的解释、方案、条款与图表，而不是只改一处措辞。
- 跨轮接续时，先读台账恢复“哪些已经成立、哪些仍在争、哪些已撤回”，再决定本轮深入哪里。
- 对外交付时，把`id`还原成读者能用的标题、日期、来源与位置，不把管理字段当引用。

台账是工作材料，不是正文。最终成果仍然完整写出论证；台账只帮助作者不遗漏已有依据和未决分歧。
