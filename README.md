# Xikari Skill

依据Xikari著《Xikari-条件结构与转化论》，帮助智能体辨明问题的主导条件、作用通道、承接与反馈，作出明确判断和方案取舍，交付可以理解和使用的分析、制度条款、计划与评论。

技能包版本：5.3.0。宿主：Windows上的Codex、Claude及兼容技能目录的智能体。

## 使用

将安装包中的文件放入宿主的`skills/xi-kari-skill`目录，通过`$xi-kari-skill`或明确点名Xikari Skill调用。

例如：“使用Xikari Skill评估这套规则，给出具体修订条款。”

每个新的Xikari分析任务，主作者先完整阅读并学习理论全文，再沿XK0—XK11正序完成取证、概念扫描、建模、变换、机制比较、一至三阶适用推演、批判、裁决与完整成文。作者自定义概念不能由模型既有同名词义替代。默认不设字数上限，复杂问题充分展开全部实质论证，配合真实案例、图表和适合的长文阅读页面。技能不生成学习证书、验签回执或流程回放。

同一问题可以持续追问、补材、反驳、深化和打磨，不需要每轮重新点名技能。后续保留有效成果，从真正受影响处深入，既不每轮重跑全链，也不只改措辞；已授权打磨时，成熟修订进入当前完整稿及相关图表。独立承担案例判断的协作者各自全文学习，然后按问题与视角分工。

按任务需要使用材料定位与引用、具体研究设计、可运行条件模型、稿件分支与合稿、现实结果接续和选定案例积累。可选工具不替代完整分析，不要求普通回答创建统一工件。离线阅读版支持脚注、公式、章节定位和选段追问。

## 文件

- `SKILL.md`：共同执行原则。
- `references/full-source-study.md`：全文学习、分块读取与理解接续。
- `references/continuation.md`：持续对话、观点接续、深化与完整成果打磨。
- `references/collaboration.md`：各自全文学习基础上的语义分工与辅助协作。
- `references/forward-workflow.md`：XK0—XK11实质正序。
- `references/reasoning-capabilities.md`：材料解释、因果、反事实、跨领域与建设性分析。
- `references/critique-and-invention.md`：反方、批判、举一反三、构想与反思。
- `references/complete-answer.md`：完整论证与成果。
- `references/presentation.md`：分区总装与视觉阅读。
- `references/theory-core.md`：理论怎样产生解释与决断，以及何时需要深入。
- `references/decision.md`：明确判断与决策成果。
- `references/routing.md`：全文学习后的重点复查与方法适用。
- `references/analysis.md`：对象、证据与结构判断。
- `references/dynamics.md`：条件路径、前瞻与结果更新。
- `references/choice-execution.md`：方案、条款与工具结果。
- `references/communication.md`：普通语言、真实案例与图表。
- `references/state.md`：必要时保存与恢复工作。
- `references/evidence-work.md`：多格式材料、来源位置、片段与版本。
- `references/research-work.md`：从竞争解释到可开展的具体研究。
- `references/condition-lab.md`：可复算模型与离散条件探索。
- `references/manuscript-work.md`：稿件快照、分支比较与文本合稿。
- `references/real-world-use.md`：采用材料、过渡安排与现实反馈。
- `references/case-library.md`：用户选定的案例积累及迁移边界。
- `references/domain-and-host.md`：专业材料、宿主工具与完整格式交付。
- `source/`：完整理论原文及来源身份。
- `scripts/read_source.py`：可选的标准库章节读取器。
- `scripts/render_answer.py`：可选的离线完整长文阅读器生成工具。
- `scripts/evidence.py`：材料定位及明确选择的引用片段。
- `scripts/condition_lab.py`：受限表达式与完整离散情景计算。
- `scripts/manuscript.py`：只读输入、冲突明确的新稿合并与依赖查询。
- `scripts/casebook.py`：在明确目录保存选择的案例与结果身份。
- `assets/examples/`：明确标注为教学的模型与资料格式。
- `assets/vendor/katex/`：公式排版资源与许可证。

## 维护

Python供可选工作与维护工具使用，最低版本3.10；核心工具使用标准库，PDF材料读取可选使用宿主的pypdf或已有文档能力。普通分析由宿主模型完成，不需要另设模型后端。生成后的HTML可离线阅读；公式资源随包提供，不访问在线排版服务。

```powershell
python -m unittest discover -s tests
python scripts/read_source.py --check
python scripts/build_install_package.py --output D:/XikariPackage
```

安装包只包含技能必需资源。测试、开发文档、旧版本与运行记录不进入安装目录。软件检查证明文件与工具的实际检查结果，不能代替答案质量或现实效益。
