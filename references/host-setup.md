# 宿主接入与干净工作目录

将本技能作为独立资源目录加载，保留宿主原有模型、工具、权限与用户指令。技能不需要安装模型后端或常驻服务，也不获得更高的指令权限。

## 确定实际位置

技能根目录是当前`SKILL.md`所在目录，随包理论、指南、脚本和资产都相对于它定位。不要猜作者的用户名、盘符、代码仓库或其他机器位置。宿主提供文件路径时使用该实际路径；路径有空格或中文时正确引用。

任务目录由用户目标和宿主当前工作区决定，须位于技能根目录之外。主稿、材料目录、案例库、模型结果、快照、临时文件与生成页面都写到任务目录。为了读取理论而定位技能文件，不会把技能目录变成新的任务目录；只读理论与写工作产物分开。

没有可写文件能力时，继续完整阅读和回答可完成的内容，说明哪些文件产物无法保存；不可读理论时仍按全文学习规则处理，不把无文件访问的对话界面冒称已搭载完整技能。

## 调用与能力适配

用户明确点名技能后执行；同任务后续按持续对话规则接续。Codex可使用`$xi-kari-skill`，Claude Code可使用`/xi-kari-skill`；其他宿主以其实际技能加载方式为准。`agents/openai.yaml`仅提供Codex界面元数据与调用策略，不是跨宿主权限配置。

主作者使用宿主实际提供的文件读取、检索、计算、协作和文档能力。子智能体不可复用时，可以开新的语义作者，但新作者先独自学习全文；没有协作工具时主作者完整完成相关分析，不虚构团队执行。上下文恢复依靠任务内材料和实际文件，不修改全局记忆。

只按当前任务需要检查对应工具。缺少Python时，可用宿主连续读取理论；缺少PDF解析、OCR或文档导出时使用其他真实可用的能力，或说明具体产物限制。不为一项可选工具自动修改全局环境、模型配置、授权策略或安装目录。

## 可选脚本的统一路径

以下为PowerShell形式。先将`$skillRoot`设为宿主实际加载的技能目录，将`$taskRoot`设为用户选择的安装外任务目录。它们是本次调用变量，不更改`HOME`、`CODEX_HOME`或宿主配置。不要原样使用不存在的位置，也不需要切换当前工作目录。

```powershell
python "$skillRoot/scripts/read_source.py" --chunks
python "$skillRoot/scripts/read_source.py" --chunk 1
python "$skillRoot/scripts/read_source.py" --search '条件结构' --context 2
python "$skillRoot/scripts/evidence.py" --catalog "$taskRoot/materials.json" add "$taskRoot/material.md" --id material-1
python "$skillRoot/scripts/claims.py" --ledger "$taskRoot/claims.json" check
python "$skillRoot/scripts/comparison.py" "$taskRoot/compare.json" --output "$taskRoot/compare" --format all
python "$skillRoot/scripts/study_design.py" --design "$taskRoot/design.json" validate
python "$skillRoot/scripts/task_state.py" --state "$taskRoot/state.json" init --task '本轮要回答的问题'
python "$skillRoot/scripts/render_docx.py" "$taskRoot/xi-kari-answer.md" --output "$taskRoot/xi-kari-answer.docx"
python "$skillRoot/scripts/condition_lab.py" "$skillRoot/assets/examples/condition-project.json" --output "$taskRoot/project-model"
python "$skillRoot/scripts/render_answer.py" "$taskRoot/xi-kari-answer.md" --output "$taskRoot/xi-kari-answer.html"
```

全文读取仍须顺序完成到末块；上述单块命令只是调用形式。教学模型明确虚构，不能充当用户现实问题的数据或结论。

十个写入工具会在创建文件、目录、锁或临时文件前拒绝安装目录及其子目录中的目标，也检查解析后的目录链接和`..`路径。运行不会向技能目录写字节码缓存。该保护约束随包工具的写入，不是操作系统沙箱，不阻止用户自行用其他程序维护技能。

## 更新与工作继承

更新技能时将旧副本备份到技能扫描范围之外，再替换完整资源目录。不要把运行文件混入新包，不自动将过往案例转成交付材料。已在独立任务目录中的成果继续保留；恢复时以当前文件和有效上下文为准。

当前发行包的工具测试覆盖Windows、中文和空格路径以及异工作目录运行。Agent Skills目录结构可被不同宿主读取，不等于每种模型、宿主和操作系统都已经完成端到端行为验证。理论学习和实际判断仍由执行它的作者负责。
