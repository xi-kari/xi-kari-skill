<div align="center">

<a href="https://github.com/xi-kari"><img src="https://github.com/xi-kari.png" width="118" alt="xi-kari 的头像"></a>

# xi-kari-skill

**框架 v9.0 · 软件 4.0.0 · 运行合同 v4**

**Hello There — I am xi-kari.**

<p align="center">
<strong>『真理是溶解世界万物的溶剂，因而绝无法在客观上存在』</strong><br>
<sub>——《阿那克萨戈拉斯的最后定理》</sub>
</p>

<p align="left">
真正的求知会不断拆掉我们原以为已经稳固的答案。
</p>

<p align="left">
可如果有人说自己已经掌握了一套能够解释一切、永远不必再被质疑的终极真理，那么这套真理恰恰没有把自身纳入审查。真理不是终点处的一件奖品，而是不断迫使我们重新理解世界、重新检查自己立场的过程。
</p>

<p align="left">
我的证明是否被完整留下并不最重要；重要的是，后来的人读到这里以后，还愿不愿意继续思考。
</p>

<p>
  <a href="https://xi-kari.github.io/xi-kari-skill/"><b>在线介绍页</b></a> ·
  <a href="https://github.com/xi-kari">@xi-kari</a>
</p>

<img src="https://img.shields.io/badge/%E5%85%A8%E6%BA%90%E9%98%85%E8%AF%BB-21%20%E5%8D%B7-8f641b?style=flat-square&labelColor=3a301e" alt="全源阅读 21 卷">
<img src="https://img.shields.io/badge/%E6%8E%A8%E6%BC%94%E9%98%B6%E6%AE%B5-XK0%E2%80%93XK12-7ce1ff?style=flat-square&labelColor=0d1117" alt="推演阶段 XK0–XK12">
<img src="https://img.shields.io/badge/%E5%85%81%E8%AE%B8%E8%B7%B3%E6%AD%A5-0-99cfbc?style=flat-square&labelColor=3a301e" alt="允许跳步 0">
<a href="https://github.com/xi-kari/xi-kari-skill/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/xi-kari/xi-kari-skill/ci.yml?style=flat-square&labelColor=0d1117&label=%E5%AE%8C%E6%95%B4%E6%80%A7%E8%87%AA%E6%A3%80" alt="完整性自检"></a>

</div>

## 它解决什么问题

普通的"把资料塞进上下文"无法证明模型真的按资料推理。常见的失败方式：

- 只引用概念，不使用概念之间的关系；
- 把相关性写成因果性；
- 把"短期、中期、长期"换个名字冒充递进推演；
- 明知上一步已经被反例击穿，仍为了显得完整硬写下一步；
- 把模型自己的模拟或假设写成现实事实。

xi-kari-skill 用合同把回答约束为：什么对象发生了什么变化、变化走哪条真实通道、改变了谁的状态和行动集、在什么条件下会失败或逆转。每一阶推演必须继承上一阶的状态差；上一阶不成立时，下一阶必须诚实标注 `not_run`，而不是继续编故事。

当前权威原文为完整 v9.0，软件为 4.0.0，活动运行合同为 v4。原文中的部分术语由作者自定义，调用时须先按原文核对含义、成立资格和适用范围，不能用通常词义替代。正常调用应给出明确中心判断、各部分的局部结论和有依据的取舍；推荐与现实执行授权分别说明。

普通领域知识可以在自身证据范围内成立，正式 G/C/CM 资格须另外满足原文实例条件；框架不能靠统一术语替代领域方法。总效应、具体通道和跨域外推分别承担证据责任，部分机制未识别不抹去已识别的限定效应，也不能凭机制故事补出整个效果。附录 D 的 32 个领域入口用于加载原生方法、框架增加的检查、反例、成本与退出条件，不增设经验公理。

默认答案完整展开本题已开展的实质分析，不设默认字数上限。次要解释、失败路径、反例和落选理由不能因为不改变主结论而删去。可读性通过主次组织、具体解释和连贯论证改善；只有用户明确要求简答时才压缩可见投影，完整正文仍保留。

可用于分析、决策建议、制度章程、计划和评论：需要章程时交付可直接审议的完整条款，需要计划时交付资源、依赖和检验安排，不只给原则或问题清单。

## 安装

下载 [干净安装包](https://github.com/xi-kari/xi-kari-skill/releases/latest/download/xi-kari-skill-v4.0.0-theory-v9.0.zip)，解压后得到一个 `xi-kari-skill` 文件夹。把整个文件夹放入宿主的技能目录，保持 `skills/xi-kari-skill/SKILL.md` 这一层级，再从新一轮对话中精确点名调用。

| 宿主 | 技能目录（Windows 示例） |
| --- | --- |
| Codex 桌面端 / CLI | `C:\Users\<你>\.codex\skills\`；自定义过 `CODEX_HOME` 时使用对应目录 |
| Claude Code | `C:\Users\<你>\.claude\skills\` |
| 已使用共享技能目录的宿主 | `C:\Users\<你>\.agents\skills\` |
| 其他支持 Skill 的代理 | 使用该宿主的技能目录，并提供完整文件夹 |

安装包只包含 9.0 原文及阅读快照、9.0 概念卡与学习包、领域资源、行为合同、运行脚本和交付模板。网站、开发测试、比较评测工具、运行记录与虚拟环境不在安装包中。已有安装时先保留旧目录备份，再替换为完整新文件夹；不同版本的 run 不混用。

默认指令层沿用宿主的模型与工具，不需要 Python。完整性自检与可选封存模式需要 Python 3.11+，可在独立 Python 环境中执行 `python -m pip install -r requirements.txt` 安装检查依赖。安装不等于一次分析已经完成，也不等于运行已封存。

Windows 可选封存模式使用 CPython 3.11.10+、3.12.4+ 或 3.13+，以支持私有运行目录的权限设置；推荐使用所在分支的最新补丁版本。

[发行说明与校验清单](https://github.com/xi-kari/xi-kari-skill/releases/latest)提供安装包的文件清单和哈希。需要开发或查看测试、网站源码时，可以克隆仓库到独立工作目录：

```bash
git clone https://github.com/xi-kari/xi-kari-skill.git
```

## 使用

一行即可，精确点名＋问题本身：

```
/xi-kari-skill 你的问题
```

或在对话里写"使用 xi-kari-skill 分析：……"。想让它只用你给的材料，就加一句"只使用我提供的材料"。

预期：

- 完整运行需要逐卷阅读原文，并处理与问题有关的证据和候选。耗时随模型、材料与任务而变，不保证固定时长；可通过读取回执和实际工具活动核对进度。
- 它的价值区是动态推演类问题（"某个变化接下来会怎么传导"）。静态问题（事实、翻译、算术）会在完成边界检查后明确告知"三阶推演不适用"。
- 话题不设限，但底层模型自身的内容政策照常生效。

## 交付里有什么

- 直接结论与事实边界（分清观察、来源主张、推断、模拟、条件情景与未知）；
- 适用时完整比较真正不同的机制，各带支持条件、失败条件、可区分观察与反向信号；不适用时说明原因，不为凑数编造机制；
- 一至三阶递归推演与每一阶的撤回信号；
- 最强反方与失效条件；
- 真实选项的比较与推荐（含上限、停止、回滚与"不行动"的比较）；尚未授权实施也可以给出明示前提的分析推荐；
- 配套读取回执中的 21 卷逐卷读取方式表——你可以核对它到底读没读；正文只用一句话指向明细。

## 完整性自检

在 Skill 文件夹中，使用已安装上述依赖的 Python 环境执行：

```bash
python scripts/check_source_snapshot.py --all
python scripts/build_knowledge_index.py --check
python scripts/check_ontology.py --all
python scripts/check_xi_kari_skill.py --all
python scripts/check_xi_kari_runtime.py --all
```

五条全部退出码 0，表示当前包通过相应完整性与合同检查。仓库 CI 另在 Linux / Windows、Python 3.11 / 3.13 上执行工程回归与公开卫生检查。软件检查、来源限定语义回答、真实模型表现和 runtime 封存是不同证据；不能把工程通过写成所有现实判断都正确或新版必然优于其他方法。

默认检查 v9.0：21 卷、4298 个段落和 120 张表，共 4418 个源单元；其中非空段落 4175 个。
当前提取规则得到 3105 条候选，候选数不是永恒或完备的概念总数。软件测试通过、源文件完整、
领域内容可用和语义封存分别验证，不能互相替代。

## 进阶：封存运行（默认关闭）

默认的指令层运行靠合同与回执表约束，产物由你抽查。若需要机器级防伪（独立作者子进程＋哈希链＋磁盘重验的签名终态），可显式要求"封存运行"，由 `scripts/xi_kari_runtime.py` 执行：

```bash
python scripts/xi_kari_runtime.py execute --runs-root <输出目录> --run-id <本次编号> --request-text "<问题>" --mode open-world --repository-root <本包绝对路径> --codex-provider-executable <codex可执行文件路径> --timeout-seconds 1200
```

- provider 与 adapter 使用实体文件路径；符号链接或目录链接会被拒绝。
- 模型与端点由环境变量控制：`XI_KARI_PROVIDER_MODEL`（模型名）、`XI_KARI_REASONING_EFFORT`（推理档位）、`XI_KARI_PROVIDER_BASE_URL`（自定义 API 端点）、`XI_KARI_PROVIDER_WIRE_API`（默认 `responses`）。`execute` 与 `validate` 必须在相同的环境变量取值下执行。
- 跑完用 `python scripts/xi_kari_runtime.py validate --run-dir <run目录>` 复验；退出码 0 且存在签名终态才算封存完成，可读答案在 run 包 `delivery/` 下。
- 边界说明：封存证明的是"产物出自被观察的独立进程且未被改动"，不证明端点背后的模型真实身份。

## 目录结构

```
SKILL.md        行为合同（指挥层）
AGENTS.md       工作区边界
agents/         宿主界面元数据
references/     框架原文阅读版、概念卡、阅读地图与各项政策
protocols/      各阶段执行细则
schemas/        结构字段与拒绝条件
scripts/        完整性自检脚本与封存 runtime
templates/      交付模板
source/         框架原文
docs/           在线介绍页（GitHub Pages，仅完整源码归档）
requirements.txt  自检与封存功能的 Python 依赖
```

## 关于作者

<table>
<tr>
<td width="110" align="center"><a href="https://github.com/xi-kari"><img src="https://github.com/xi-kari.png" width="92" alt="柊東雲"></a></td>
<td>

**柊東雲**（Hiiragi Shinonome / ひいらぎしののめ），网名 **xi-kari**——这个 skill 就是以它命名的。

> 致力于ai理解世界，ai服务人，为人民服务。

[GitHub @xi-kari](https://github.com/xi-kari)

</td>
</tr>
</table>
