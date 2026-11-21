# 安装与宿主适配

本版本的安装包为 **`xi-kari-skill-6.9.0-windows.zip`**。使用实际交付的安装包，或通过对应 Release 页面提供的下载链接取得。解压后只得到一个`xi-kari-skill`文件夹，将整个文件夹放入宿主的技能目录，使最终位置为`<技能目录>/xi-kari-skill/SKILL.md`。

同一 Release 页面还提供逐文件清单 `install-manifest.json` 与 `SHA256SUMS` 的下载链接。安装前，在下载目录运行下面的命令，把输出的哈希与该版本`SHA256SUMS`中的对应行对照，一致后再解压：

```powershell
Get-FileHash -Path .\xi-kari-skill-*-windows.zip -Algorithm SHA256
```

请使用Release安装包。GitHub的“Code → Download ZIP”和仓库克隆包含测试、网页及开发文件，不是供技能目录使用的安装包。

| 宿主 | 常用本地位置 | 调用示例 |
| --- | --- | --- |
| Codex | 用户目录下`.agents/skills/xi-kari-skill/`；项目内可用`.agents/skills/xi-kari-skill/` | `$xi-kari-skill`或明确点名 |
| Claude Code | 用户目录下`.claude/skills/xi-kari-skill/`；项目内可用`.claude/skills/xi-kari-skill/` | `/xi-kari-skill`或明确点名 |
| Gemini CLI、GitHub Copilot CLI、Cursor、OpenCode、Kimi Code CLI、Qwen Code | 同样读取用户目录下`.agents/skills/xi-kari-skill/`，与Codex共用一份；项目内也读`.agents/skills/` | 在请求里明确点名`xi-kari-skill` |
| Google Antigravity | 全局`~/.gemini/config/skills/xi-kari-skill/`；工作区内可用`.agents/skills/xi-kari-skill/` | 明确点名 |
| 其他支持Agent Skills的本地智能体 | 宿主实际配置的技能根目录 | 让宿主加载该目录的`SKILL.md` |

具体发现位置与调用策略由宿主决定，参见[Codex官方说明](https://learn.chatgpt.com/docs/build-skills)和[Claude Code官方说明](https://code.claude.com/docs/en/skills)。表中其他宿主的位置取自它们的官方说明（[Gemini CLI](https://geminicli.com/docs/cli/skills/)、[GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills)、[Cursor](https://cursor.com/docs/skills)、[OpenCode](https://opencode.ai/docs/skills/)、[Kimi Code CLI](https://moonshotai.github.io/kimi-cli/en/customization/skills.html)、[Qwen Code](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/)、[Google Antigravity](https://antigravity.google/docs/skills)，2026年11月核对），本项目没有在这些宿主中逐一验证。VS Code中的GitHub Copilot读取用户目录下`.copilot/skills/`，其本地会话也读`.claude/skills/`与`.agents/skills/`，见[VS Code说明](https://code.visualstudio.com/docs/agent-customization/agent-skills)。

同一宿主通常只安装一份同名技能，避免重复入口。Cursor、OpenCode与Kimi Code CLI也读取`.claude/skills/`，Cursor与Kimi Code CLI还读取`.codex/skills/`；如果在这些目录里另放了一份，这些宿主会看到几份同名副本。几处副本保持同一版本，升级时一起替换。`agents/openai.yaml`为Codex提供界面信息与显式调用策略；其他宿主可以忽略该文件，按共同`SKILL.md`执行。云端服务的上传、目录发现及文件能力须按相应服务另行确认。

更新时，先把旧技能目录完整备份到**技能扫描目录之外**，再换入新文件夹。不要将新旧文件混合，也不要把带`SKILL.md`的备份留在扫描目录中。若旧目录混入了自己的案例或工作文件，先迁到独立任务目录。

安装包不包含开发用`AGENTS.md`、测试、网页、运行记录、个人案例、模型配置或作者机器路径；不会自动设置模型后端、权限、账户、全局记忆或定时任务。第三方公式排版资源保留其许可证。

## 理论版本与双语阅读

6.9.0 安装包使用《Xikari-条件结构与转化论》v2.1，包含中文权威正文、按 v2.1 修订的英文参考译本及中英术语表。中文与英文共用全部 397 个编号小节、分部编号和段落；文本身份分别见 `source/source-manifest.json` 和 `source/en/source-manifest.json`，更新时两份一起替换。

[中文精读站](https://xi-kari.github.io/xi-kari-skill/handbook/)和[英文阅读站](https://xi-kari.github.io/xi-kari-skill/handbook/en/)都可直接在浏览器阅读，无需安装技能。站点与安装包共用 v2.1 正文；中英文均提供全部 421 个网页讲解单元，英文包含完整参考正文以及讲解、例子、问答和来源说明的译文。原图配英文说明，历史研究附件保留中文并明确标注。下载页另保留 v2 中文正文、作者的 v2 英译原件和标为第一版的旧 Word，它们都不是当前正文。

英文工作仍按 `references/english.md` 使用中文权威正文和英文参考稿。网页上的译文、讲解与案例不替代技能要求的原文学习。

## 所需能力与目录边界


最低需要宿主能够读取包内完整Markdown、保持或恢复长任务上下文，并输出足够完整的答案。联网检索、Python、文档转换和多智能体协作均使用宿主实际已有能力，不假定所有代理都具备同样工具。当前可移植运行测试覆盖Windows；不把其他操作系统或每一种云端产品描述为已验证支持。

可选Python工具需要Python 3.10或更新版本。核心功能使用标准库；PDF材料读取可选使用`pypdf`或宿主已有文档工具。生成的HTML可离线使用，公式字体与脚本随包提供。

技能目录是只读资源；结果、材料目录、模型输出、案例库及快照写到安装目录外的任务位置。脚本从自身位置寻找随包资源，不要求固定盘符或从安装目录启动。首次接入与可复制命令见[宿主接入与干净工作目录](../references/host-setup.md)。


## 阅读模式与前瞻记录

默认完整阅读；在请求中明确指定 `layered` 可进行分层阅读实验。日常问题想要一个快速判断，在请求中写“用十句话”：技能只按随包的十句话核对后作答，并在开头写明没有读原文。能力等效与合入阈值尚待评价，不能把实验入口当成结论。理论评估仍须全读。没有旧完整正序兼容路线。

前瞻登记放在安装外的用户任务目录。先保存输入 JSON，再运行 `python scripts/forecast.py --registry <任务目录>/forecasts.json register --record <输入.json>`；到期以 `resolve --record <结果.json>` 追加。`report` 读取当前注册表，不自动调度到期任务，也不改写冻结记录。
