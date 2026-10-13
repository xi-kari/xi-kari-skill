# Xikari Skill

依据Xikari著《Xikari-条件结构与转化论》，帮助智能体辨明问题的主导条件、作用通道、承接与反馈，作出明确判断和方案取舍，交付可以理解和使用的分析、制度条款、计划与评论。

技能包版本：5.0.0。宿主：Windows上的Codex、Claude及兼容技能目录的智能体。

## 使用

将安装包中的文件放入宿主的`skills/xi-kari-skill`目录，通过`$xi-kari-skill`或明确点名Xikari Skill调用。

例如：“使用Xikari Skill评估这套规则，给出具体修订条款。”

技能按问题读取相关完整原文和必要依赖，不要求每次通读全书、建立运行包或重复验证执行流程。重要判断给出理由、真实案例和适合的图表；资料不足限定对应结论，仍完成有依据的取舍。

## 文件

- `SKILL.md`：共同执行原则。
- `references/theory-core.md`：理论怎样产生解释与决断，以及何时需要深入。
- `references/decision.md`：明确判断与决策成果。
- `references/routing.md`：按任务读取原文。
- `references/analysis.md`：对象、证据与结构判断。
- `references/dynamics.md`：条件路径、前瞻与结果更新。
- `references/choice-execution.md`：方案、条款与工具结果。
- `references/communication.md`：普通语言、真实案例与图表。
- `references/state.md`：必要时保存与恢复工作。
- `source/`：完整理论原文及来源身份。
- `scripts/read_source.py`：可选的标准库章节读取器。

## 维护

Python仅供可选章节读取和维护工具使用，最低版本3.10；普通分析由宿主模型完成，不需要另设模型后端。

```powershell
python -m unittest discover -s tests
python scripts/read_source.py --check
python scripts/build_install_package.py --output D:/XikariPackage
```

安装包只包含技能必需资源。测试、开发文档、旧版本与运行记录不进入安装目录。软件检查证明文件与工具的实际检查结果，不能代替答案质量或现实效益。
