# Xikari Skill 工作区

本目录维护供宿主智能体使用的Xikari技能。行为入口为`SKILL.md`，理论来源为Xikari著`source/Xikari-条件结构与转化论.md`。书名、理论文本身份、技能版本与实际安装状态分别管理。

正文、技能指令和用户成果保持清洁。开发评估、安装回执、备份和试用记录放在仓库之外。不得在原文中加入工程说明，不得将领域事实或模型推断改写为作者定义。

技能以明确判断、方案取舍、完整成果和清楚表达为目标；不添加默认的运行审计、全源回执、阶段回放或签名封存。

维护命令：

```powershell
python -m unittest discover -s tests
python scripts/read_source.py --check
python scripts/build_install_package.py --output <外部交付目录>
```

这些命令用于开发与安装，不是每次调用技能的前置条件。只维护Windows本地使用；安装文件由`skill-package.json`明确选择。发布、外部消息和活跃任务数据修改须有相应用户授权。
