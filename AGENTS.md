# Xikari Skill 工作区

本目录维护供宿主智能体使用的Xikari技能。行为入口为`SKILL.md`，理论来源为Xikari著`source/Xikari-条件结构与转化论.md`。书名、理论文本身份、技能版本与实际安装状态分别管理。

正文、技能指令和用户成果保持清洁。开发评估、安装回执、备份和试用记录放在仓库之外。不得在原文中加入工程说明，不得将领域事实或模型推断改写为作者定义。

技能先由主作者完整学习理论全文，再沿XK0—XK11实质正序形成深入解释、明确判断、批判、方案与构想，完整呈现全部实质论证，不设默认字数上限。不以节约token缩减理论学习、分析或正文；不添加运行审计、全源回执、阶段回放、自我评分或签名封存。

维护命令：

```powershell
python -m unittest discover -s tests
python scripts/read_source.py --check
python scripts/build_install_package.py --output <外部交付目录>
```

这些命令用于开发与安装，不是每次调用技能的前置条件。只维护Windows本地使用；安装文件由`skill-package.json`明确选择。发布、外部消息和活跃任务数据修改须有相应用户授权。
