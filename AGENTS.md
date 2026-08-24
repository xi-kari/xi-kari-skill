# Xi-Kari Skill 工作区说明

本目录是独立的 `xi-kari-skill` Skill 包。框架原文位于 `source/`，通过校验的
阅读快照位于 `references/source/v8.2/`（目录名中的版本号被完整性校验锁定，
不要重命名）。行为合同以 `SKILL.md` 为准，本文件只补充工作区边界。

## 运行边界

- 每次语义运行必须创建一个隔离 run 包，并按 `XK0—XK12` 保存阶段散列、
  检查点、验证尝试、局部修复和可读交付。run 包不得写入本 Skill 包目录。
- 运行状态只存在于该 run 包内；不得创建任何跨运行的全局共享状态、
  固定输出根或发布流水线。
- 默认运行根遵循平台状态目录，避开云同步目录与系统临时目录；用户或测试可以
  显式提供全新的隔离 run 目录。
- 宿主级全局模板（通用文件事务、回滚类仪式）的产物只落 run 包，不得顶替
  交付命名或进入聊天投影。
- 封存运行仅在用户明确要求时启用：由 Codex CLI 兼容 provider 担任语义作者，
  `XI_KARI_PROVIDER_MODEL` 与 `XI_KARI_REASONING_EFFORT` 覆盖模型与档位，
  `XI_KARI_PROVIDER_BASE_URL`（可选 `XI_KARI_PROVIDER_WIRE_API`）注入自定义
  端点；同一 run 的 execute、validate 与修复必须使用相同的环境变量取值。
- 外部检索只支持现实事实和案例，不能改写框架定义。
- 任何外部框架、注册表或旧版本内容都不得混入框架原文。
- 新变量使用 `XK-PROV-*`，除非源文档有锚点，不得升级成正式概念。
- `open-world` 是普通问题默认模式；`closed-input` 只在用户明确要求仅使用给定
  材料时启用，两种证据不得混合。

## 诚实规则

- 运行时控制字段由 runtime 写入，模型只填写语义字段；验证必须从磁盘重新读取。
- 超时、取消、无总结或未经 runtime 封存的运行，不得写成完成；
  不得补 marker、改状态 sidecar 或改报告伪装通过。
- 封存运行在 `execute` 后必须以相同环境变量立即 `validate` 新鲜复验，
  复验通过且存在签名终态后才交付最终答案。
- 指令层运行按合同完整执行，在交付的运行边界段（不作全文最后一段）用日常语言
  声明未经 runtime 封存及原因；21 卷逐卷读取方式表写入 source-read-receipt.md，
  读者可见层至多一句话概括。
- 指令层的包完整性校验必须本轮实际执行并记录执行时间；确因宿主限制无法执行时
  不得伪称已执行，引用往轮结果必须明标来源运行并按能力缺口降档。
- 主答案固定命名 xi-kari-answer.md；交付前执行投影卫生检查
  （`python scripts/check_projection_hygiene.py <主答案与投影文本>`，或等价扫描），
  散列、退出码、回执表行不得进入读者可见层。

## 包完整性自检

```text
python scripts/check_source_snapshot.py --all
python scripts/build_knowledge_index.py --check
python scripts/check_ontology.py --all
python scripts/check_xi_kari_skill.py --all
python scripts/check_xi_kari_runtime.py --all
```

五条命令都应以退出码 0 结束；任何一条失败说明包不完整或被改动，先修复再运行语义链。
