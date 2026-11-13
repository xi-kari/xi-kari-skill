---
{"id":"REF-CANDIDATE-LEDGER","theory_sha256":"18a7cc167faa3eda68a04b21313f833be6583abf1a2a47523a246a5f8a7eaee6","anchors":["2.6","2.13","4.17.2","11.8","13.11","16.5","16.19"]}
---

# 候选账本

用于生成工作里候选较多、彼此有父子关系，或需要跨轮追踪检验的场合：记住每条候选从哪些起点、经哪种走法得到，是什么身份，凭什么与竞争项分开，检验走到了哪一步。先按 [M10](../modules/generate/MODULE.md) 和[生成指南](generation.md)完成实际的推出与筛选，需要管理时再建账本。

两三条候选直接写进回答即可。建账本的理由是不让三种失真发生：子项悄悄丢掉父项的条件；候选在几轮讨论之后被当成已经证实；被否决的想法换个说法又回来。

它与[主张台账](claim-ledger.md)分工不同：主张台账管一项已作出的判断靠什么成立；候选账本管尚未成为判断的东西从哪里来、要怎样检验。候选得到支持并经相应模块判断之后，才作为主张进入台账或正文。

## 记录什么

一份记录是一个 JSON 对象，含 `question`（可选）、`base` 和 `candidates`。一份账本只装一个问题：`question` 第一次登记后，再登记的须与它逐字相同，别的问题另建账本。

起点 `base` 的每一项：

| 字段 | 含义 |
| --- | --- |
| `id` | 稳定标识：以字母或数字开头，只含英文字母、数字、点、下划线和连字符，不超过 96 个字符；起点与候选共用一个标识空间 |
| `statement` | 起点本身 |
| `kind` | `observed` 观察、`supported` 已有支持的判断、`conditional` 条件结论、`definition` 所用定义、`assumption` 明示假设、`stated` 未核陈述 |
| `source` | 出处或所在位置；`observed`、`supported`、`stated` 必填 |
| `conditions` | 成立条件；`conditional` 必填 |
| `section` | 原文小节；`definition` 必填 |

候选 `candidates` 的每一项：

| 字段 | 含义 | 何时必填 |
| --- | --- | --- |
| `id`、`statement` | 标识与陈述 | 总是 |
| `identity` | `formal` 模型内推论、`definitional` 定义要求、`empirical` 经验候选、`variable` 变量候选、`analogy` 启发性类比、`question` 新问题、`proposal` 构想 | 总是 |
| `move` | `commit` 展开承诺、`compose` 核对组合、`task` 改换任务、`scale` 换尺度、`relation` 换关系、`representation` 换表示、`position` 换位置、`clock` 换时钟、`invert` 反过来问、`residual` 追残差、`transfer` 跨域借问、`association` 联想 | 总是 |
| `parents` | 父项标识，可以是起点或别的候选 | 除联想外总是；联想不得有父项，也不能是模型内推论或定义要求 |
| `record` | `kept`、`changed`、`lost` 三个列表 | 换尺度、换关系、换表示、跨域借问 |
| `model`、`derivation` | 模型与前提；推导步骤 | 模型内推论两项都要；定义要求须有推导 |
| `theory` | 实际承担这条推导的原文小节，如 `{"section": "3.3"}`；推导靠领域数学或材料口径时不填，不为显得有出处而补 | 定义要求 |
| `analogy` | `source_domain`、`target_domain`、`shared`、`differences`、`not_transferable`、`mapping`、`test` 七项 | 启发性类比与跨域借问 |
| `residual` | 来源残差 | 追残差与变量候选 |
| `novelty` | `level`（`restated` 重述、`known` 已有、`recalled` 可能已有、`new_here` 对本题新、`unseen_in_scope` 所查范围内未见）、`scope` 查过与没查的范围及阅读深度、`prior` 已有说法或所忆内容 | 总是；后三级须写 `scope`，`known` 与 `recalled` 须写 `prior` |
| `observables` | 成立时应看到什么 | 经验候选、变量候选 |
| `rivals` | 竞争项，每项含 `statement` 与 `distinguishing` | 经验候选、变量候选至少一项 |
| `minimal_test` | 风险可接受的最小检验 | 经验候选、变量候选 |
| `reject_conditions` | 出现什么就放弃 | 经验候选、变量候选、启发性类比 |
| `upgrade_conditions`、`forbidden_uses` | 升级条件；禁止用途 | 变量候选 |
| `sensitive`、`necessity`、`risk` | 是否涉及隐私、健康、安全、法律地位或低权力位置；取得的必要性；隐私与风险 | `sensitive` 为真时后两项必填 |
| `strength` | `expression` 表达级、`exploration` 探索级 | 经验候选、变量候选、启发性类比 |
| `changes` | 成立后改变什么 | 建议填写；未填时 `check` 提示 |
| `post_outcome` | 是在哪项结果出来之后才提出的 | 属于这种情形时 |
| `supersedes` | 所取代的旧候选；不能指向自己的父项或祖先，取代关系不能成环 | 候选进入检验之后要改动时 |

填写时的几处取舍：一项结果用到不止一种走法时，`move` 填决定这条陈述的那一步，其余写进 `derivation`；联想通常登记为新问题，登记成经验候选就要填齐经验候选的全部字段；凭回忆觉得领域里早有、却没有可核出处的说法填 `recalled`，不填 `new_here`；标识不必连续，删去的编号不重用。

状态、经过、修订记录和登记时间由工具写入，记录里不得自带。新候选一律从“提出”开始。账本不生成置信度、新颖性分数或“值得研究”的认证；未知字段一律拒绝，不静默忽略。

篇幅有上限：单个文字字段不超过 8000 字符，列表至多 200 项，一份账本至多 2000 项起点与候选，账本文件不超过 4 MiB；会使账本超限的写入整批不提交。只含空格、控制符或零宽字符的文字按空处理。

## 状态怎样变化

候选按原文 §2.13 与 §11.8 的顺序经过：提出、检验中、得到支持的候选，或被拒绝、退役。工具只允许相邻的变化，旧状态保留在经过里，不删除失败的轨迹。

- 还停在“提出”的候选可以用 `revise` 修订，例如自我攻击后补上竞争项、收窄表述；修订须写明理由，修订前的内容留在账本里。进入检验之后不再原地修订，改动用新标识并以 `supersedes` 指向旧记录。
- 提出到得到支持之间必须经过检验中。
- 标为得到支持的候选，须随这次变化提交至少一条支持性证据；续推、复述和模型之间的一致都不是证据。
- 拒绝、退役，以及把已得到支持的候选重新打开检验，须写明理由。
- 拒绝与退役是终态；要重新提出，用新标识并以 `supersedes` 指向旧记录。
- 新问题与构想不在这里判定：它们只在交给相应路线或不再使用时退役，理由里写明去向。
- 诊断级强度只能随“得到支持的候选”一并登记；离开该状态时自动退回探索级。

各身份的“支持性证据”指什么，由作者按身份负责：经验候选与变量候选指外部可观察材料；模型内推论指独立复算或经核对的反例；定义要求指找到了合同要求的那项痕迹；启发性类比指目标域自己的检验。工具只核对有没有提交，不判断它是否充分。

变量候选得到支持后仍是候选，须进入相应的对象或变量合同才成为可用的变量；这一步不在账本里发生。

## 命令

工具需要 Python 3.10 以上，仅使用标准库。以下 PowerShell 命令用 `$skillRoot` 表示当前 `SKILL.md` 所在安装目录，`$taskRoot` 表示安装外的用户任务目录；路径设置见[宿主接入](host-setup.md)。账本放在任务文件旁，不写入技能目录或全局记忆。

```powershell
python "$skillRoot/scripts/candidates.py" --ledger "$taskRoot/候选.json" add --record "$taskRoot/candidates-round1.json"
python "$skillRoot/scripts/candidates.py" --ledger "$taskRoot/候选.json" revise --record "$taskRoot/c3-revised.json" --note '自我攻击后补上更省的竞争项'
python "$skillRoot/scripts/candidates.py" --ledger "$taskRoot/候选.json" list
python "$skillRoot/scripts/candidates.py" --ledger "$taskRoot/候选.json" show C3
python "$skillRoot/scripts/candidates.py" --ledger "$taskRoot/候选.json" lineage C4
python "$skillRoot/scripts/candidates.py" --ledger "$taskRoot/候选.json" advance --id C3 --to testing --note '开始比对已有记录'
python "$skillRoot/scripts/candidates.py" --ledger "$taskRoot/候选.json" advance --id C3 --to supported --evidence "$taskRoot/evidence-c3.json"
python "$skillRoot/scripts/candidates.py" --ledger "$taskRoot/候选.json" check
python "$skillRoot/scripts/candidates.py" --ledger "$taskRoot/候选.json" render --output "$taskRoot/候选账本.md"
```

`add` 一次登记一批起点和候选；同一批里的候选可以互为父子，整批要么全部写入，要么都不写入。`revise` 的记录是单条候选的完整内容，`id` 与原候选相同，按新登记的同一套规则核对。`advance` 的证据文件是一个列表，每项含 `ref`（材料位置）、`direction`（`supports`、`undercuts` 或 `context`）和可选的 `note`。`list`、`show`、`lineage`、`check` 只读。`render` 生成可读的《候选账本》，输出须在安装目录之外；只覆盖本工具先前生成的文件，且须加 `--force`。

`lineage` 给出一条候选的全部来路、代次，以及它仍然依赖的东西：尚未得到支持的祖先候选，以及身份为条件结论、明示假设或未核陈述的起点。交付这条候选时，这些条件要随它一起写出。

每个命令读入账本时都会核对状态经过：只有本工具自己能写出的经过才被接受，例如标为得到支持的一步必须带支持性证据，拒绝、退役和重新打开必须带理由，新问题与构想只能退役。被直接改写而不合这些规则的账本一律拒绝处理并指出是哪一条候选，不静默修补。

`check` 核对起点与候选引用的原文小节是否存在，并提示需要再看的地方：标为重述却仍在役的候选；没有起点的联想；没有写明成立后改变什么；变换记录里没有丢失项；超过第三代；父项已被拒绝或退役；父项在它登记之后修订过；已被取代却仍在役；涉及敏感位置；结果后提出；得到支持却仍依赖未决条件。它回答的是“登记是否自洽、哪里该再看一眼”，不判断候选是否为真、是否真的新、区分观察是否有区分力。提示不是待办清单：作者看过并在正文相应位置处理即可，例如敏感位置的提示对应正文里的风险与禁止用途说明。退出码 1 表示存在需要处理的错误。

`$skillRoot/assets/examples/candidates-example.json` 是一份可以直接 `add` 的示例记录，全部为教学占位内容，不含任何现实机构的数据。

## 写入与并发

同一账本同时由一位作者负责写入。工具用同目录独占写锁保护最后的重读、比较和原子提交，拒绝重复标识、成环的谱系、不可识别的账本文件和已经变化的旧内容。遇到写锁或版本冲突，重读后重新处理，不静默重放；异常遗留的写锁须确认没有写入者后再处理，工具不自动清除。

## 交付时的用途

- 成文前按代次读一遍：每条候选的条件是否随它写出，身份词是否与依据相称。
- 父项改变时，沿谱系找出依赖它的子项逐条复核，而不是只改父项的措辞。
- 跨轮接续时，先读账本恢复“哪些还只是提出、哪些在查、哪些已被否决”，再决定本轮推进哪里。
- 对外交付时，把标识还原成读者能用的说法；走法名称和字段名是工作用语，不进入正文。

账本是工作材料。最终成果仍按[生成指南](generation.md)完整写出每条候选的来路、竞争项与检验办法。
