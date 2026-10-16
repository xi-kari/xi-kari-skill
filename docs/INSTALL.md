# 安装与宿主适配

下载Release中的 **`xi-kari-skill-5.5.0-windows.zip`**。解压后只得到一个`xi-kari-skill`文件夹，将整个文件夹放入宿主的技能目录，使最终位置为`<技能目录>/xi-kari-skill/SKILL.md`。

请使用Release安装包。GitHub的“Code → Download ZIP”和仓库克隆包含测试、网页及开发文件，不是供技能目录使用的安装包。

| 宿主 | 常用本地位置 | 调用示例 |
| --- | --- | --- |
| Codex | 用户目录下`.agents/skills/xi-kari-skill/`；项目内可用`.agents/skills/xi-kari-skill/` | `$xi-kari-skill`或明确点名 |
| Claude Code | 用户目录下`.claude/skills/xi-kari-skill/`；项目内可用`.claude/skills/xi-kari-skill/` | `/xi-kari-skill`或明确点名 |
| 其他支持Agent Skills的本地智能体 | 宿主实际配置的技能根目录 | 让宿主加载该目录的`SKILL.md` |

具体发现位置与调用策略由宿主决定，参见[Codex官方说明](https://learn.chatgpt.com/docs/build-skills)和[Claude Code官方说明](https://code.claude.com/docs/en/skills)。同一宿主通常只安装一份同名技能，避免重复入口。`agents/openai.yaml`为Codex提供界面信息与显式调用策略；其他宿主可以忽略该文件，按共同`SKILL.md`执行。云端服务的上传、目录发现及文件能力须按相应服务另行确认。

更新时，先把旧技能目录完整备份到**技能扫描目录之外**，再换入新文件夹。不要将新旧文件混合，也不要把带`SKILL.md`的备份留在扫描目录中。若旧目录混入了自己的案例或工作文件，先迁到独立任务目录。

安装包不包含开发用`AGENTS.md`、测试、网页、运行记录、个人案例、模型配置或作者机器路径；不会自动设置模型后端、权限、账户、全局记忆或定时任务。第三方公式排版资源保留其许可证。

## 所需能力与目录边界


最低需要宿主能够读取包内完整Markdown、保持或恢复长任务上下文，并输出足够完整的答案。联网检索、Python、文档转换和多智能体协作均使用宿主实际已有能力，不假定所有代理都具备同样工具。当前可移植运行测试覆盖Windows；不把其他操作系统或每一种云端产品描述为已验证支持。

可选Python工具需要Python 3.10或更新版本。核心功能使用标准库；PDF材料读取可选使用`pypdf`或宿主已有文档工具。生成的HTML可离线使用，公式字体与脚本随包提供。

技能目录是只读资源；结果、材料目录、模型输出、案例库及快照写到安装目录外的任务位置。脚本从自身位置寻找随包资源，不要求固定盘符或从安装目录启动。首次接入与可复制命令见[宿主接入与干净工作目录](../references/host-setup.md)。

