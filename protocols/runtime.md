# Xi-Kari v3 运行协议

每次真实调用都建立一个新的隔离 run 包；本协议不提供轻量旁路。宿主可以把内部语义字段交给运行时物化，但运行时只信任磁盘重载后的字节。

## XK0—XK12

| 阶段 | 固定责任 | 主要绑定文件 |
| --- | --- | --- |
| XK0 | 问题合同、时间窗、模式、能力、立场中和键、隐私用途与交付对象 | `run-contract.json`、`capability-snapshot.json` |
| XK1 | v8.3 源锁、21 卷和 4631 段+122 表全单元读取 | `source-lock.json`、`authoring/XK01-read-plan.json`、`authoring/XK01-read-events.jsonl`；生产 profile 另含 `authoring/XK01-semantic-read-trace.json` |
| XK2 | 开放/封闭检索、查询前沿、来源材料与逐来源评价输入 | `authoring/XK02-retrieval-ledger.json` |
| XK3 | 证据身份、谱系、冲突、不能证明什么和未知冻结 | `authoring/XK03-evidence-ledger.json`、`authoring/XK03-unknown-register.json` |
| XK4 | 全候选逐项终态处置、概念卡/邻接/bundle 实际联读和 census hash | `authoring/XK04-concept-disposition.json`、`authoring/XK04-concept-closure-report.json`；生产 profile 另含 `XK04-ontology-read-plan.json`、`XK04-ontology-read-trace.json` |
| XK5 | 局部联合状态 Ω：对象、圈层、位置、M/Ψ、九轴、五时钟、通道、W、K、未知和残差 | `authoring/XK05-local-world-model.json`；W 精确绑定本 run 冻结的 XK3 支持身份，对象边界、身份/尺度、成员/包含及局部状态都不得无证据填充 |
| XK6 | 尺度、圈层关系、表示/表达三类变换及逐跳级联验证 | `authoring/XK06-transformation-ledger.json`、`authoring/XK06-cascade.json` |
| XK7 | 简单基线、主机制、最强竞争、混合、残差、案例和反例 | `authoring/XK07-claim-mechanism-graph.json`、`XK07-case-ledger.json` |
| XK8 | 一至三阶递归、四分支、状态继承、剪枝和合法停止 | `authoring/XK08-recursive-lineage.json`、`authoring/recursive-state/` |
| XK9 | 逐阶评价、敏感性、红队、成对立场稳定性 | `authoring/XK09-*` |
| XK10 | 事实/结构/机制/预测/价值/责任/授权裁决，行动排序、前瞻和框架缺口隔离 | `authoring/XK10-verdict.json`、`authoring/XK10-action-ranking.json`、`authoring/XK10-forecast-ledger.json`、`authoring/XK10-framework-gap-ledger.json` |
| XK11 | 类型化读者投影、隐私处置、普通语言表达、主答案完整性与确定性规则检查 | `authoring/XK11-output-plan.json`、`authoring/XK11-semantic-coverage.json`、`authoring/XK11-prose-review.json`、`delivery/artifact-index.md` 与其余 `delivery/*` |
| XK12 | preseal、候选、正式目录和终态四重 fresh-disk 验证，事务恢复与最终索引 | `validation/attempts/*`、`artifacts/artifact-manifest.json`、`continuation/xk12-transaction.json` |

## 生命周期边界

`init` 与 `prepare` 只执行只读生产预检并返回 JSON，不创建正式 run、阶段记录或终态权威。`execute` 启动真实基础作者，观察执行证据并创建正式运行；模型自报回执不能替代这一边界。正式运行冻结一次性 Lamport SHA-256 终态公钥承诺。`materialize` 必须先把请求包写入 `continuation/input-packet.json`，再从磁盘重新读取，依次封存 XK2—XK11。XK12 先在候选目录验证，再用可恢复 journal 推广到正式目录；正式目录通过独立 fresh validation 后，写入 `completion.json`，签发 `terminal-record.json` 并销毁私钥。只有有效签名终态可以产生 `complete` 或 `cancelled`；`state.json` 只是非权威投影。

正式运行只接受 `contract_profile=production-authoring-v3` 与 `semantic_authoring_profile=production-codex`，绑定仓库内 adapter、外部 provider、按 manifest 顺序排列的 21 卷语义轨迹，以及覆盖全部候选、正式/结构卡、必读邻接和连续性 bundle 的 ontology read plan/trace。旧源、旧 profile 或混版绑定均在创建正式 run 前拒绝，不自动迁移或重签。runtime 只接受模型语义字段，自行追加卷路径、卷散列、manifest 绑定和 import receipt；import receipt 证明导入边界，不证明作者进程。`fork`/`repair` 必须从父合同重新验证并冻结同一 adapter/provider 路径与散列，在创建子目录前重新执行基础作者并持久化新鲜的 request、prompt、完整语义文件、events、base receipt、21 卷语义读痕和 ontology read trace；不得仅导入父 trace。

`final-chat.json` 只能指向 `continuation/completion.json`，不能预先自称有效。13 个阶段、manifest 或可改写的状态旁路都不能单独铸造完成；只有 Lamport 验证得到 `terminal_state=complete` 后，fresh validation 才可依赖已封存 receipt 而不再要求外部 provider 文件仍存在。XK12 中断时只按 journal 中的 before/after 字节恢复；出现第三种未知字节时停止，不猜测覆盖。有效终态签发后，本 run 的写接口全部关闭；新的输入使用 `fork`。真实验证失败先由 `repair-plan` 绑定父 run 全文件快照、合同、phase chain、validator authority、实际错误和最早可归属阶段；`resume` 只消费仍与磁盘和 fresh validation 完全一致的计划，并建立 fresh repair 子 run。缺失、改写、过期计划或 cancelled parent 均不得创建子目录。

支持的生命周期命令为 `init`、`prepare`、`execute`、`materialize`、`validate`、`repair-plan`、`resume`、`fork`、`cancel`、`status`。`execute` 是 runtime-owned 作者入口：调用者提供完整 problem-contract JSON，或提供 `--request-text/--request-text-stdin`。自然请求先由独立的 XK0 合同作者补全语义边界，父运行时校验原问题、模式和截止点后冻结最终合同；随后依据最终合同散列生成源与本体阅读绑定，再启动完整基础作者。基础作者不得再次改写冻结合同。第一步的请求、提示、完整输出、事件、实际进程与散列证据保存在基础回执中并接受新鲜回放核验；不得事后给旧合同的阅读证明补签。完整 problem-contract 入口直接使用已验证合同。closed-input 仍必须提供精确的冻结材料 envelope。不存在任何 fallback 或降级替代流程。

## 语义权威链

运行时只接受以下连续链条：`XK3 精确证据身份 → XK5 W 的命题—证据—来源支持绑定 → XK7 命题—证据边 → XK8 已验证节点证明 → XK10 裁决与授权元组 → XK11 类型化公开投影 → XK12 fresh-disk 终态`。后段不能自行补造前段不存在的引用。

- 每项裁决分别保存命题、证据和二者之间的精确边；只同时列出两个 ID 不构成支持。
- 递归引用只接受 XK8 验证器返回的节点集合。原始谱系中的字符串、模拟节点或不存在节点不能进入裁决。
- 授权裁决使用一个不可拼接的原子范围：授权证据、决策主体、目标对象、单一动作、地域和有效期。获授权方案的执行者、动作、对象、地域和期限必须全部匹配同一范围。
- 数值预测必须保存非空校准依据；递归深度、模拟次数或措辞强度都不能替代校准。
- 静态问题在 packet 合同处拒绝 XK5—XK10 动态工件；物化器和 fresh validator 仍再次净化，不能把夹带的立场或预测投影给读者。

## 隐私与读者可见性

XK0 冻结用途、交付对象、`public/context_limited/sensitive/highly_sensitive/refused_disclosure` 五级分类和 fail-closed 规则。生产 `execute` 把这份隐私合同写入只读基础作者请求；模型必须为共享投影器识别的每个交付语义原子提供唯一 visibility 记录，来源 `title` 与 `content` 也不例外。缺失、额外、重复、悬空、用途不符或投影后索引归属漂移，必须在正式 run 目录创建前失败。

只有 `public` 项可进入交付。其余四级非公开项必须给出保护依据并统一扣留；语义覆盖保留该原子并标为 `withheld_for_protection`，主答案写保护性边界，但任何交付都不得泄露原值。Runtime 不得为模型语义补写默认公开决定；检索投影只可按代码与 checker 共同冻结的精确 allowlist，为 runtime 生成的 query/source 执行元数据补固定分类。任何未列入 allowlist 的新路径都 fail closed。隐私扣留不是删除语义单元，也不能被用来伪装 coverage 完整。

## 运行目录

```text
run/
├── run-contract.json
├── capability-snapshot.json
├── source-lock.json
├── phase-events.jsonl
├── authoring/
│   ├── XK01-read-plan.json
│   ├── XK01-semantic-read-trace.json  # production-authoring-v3
│   ├── XK03-unknown-register.json
│   ├── XK04-concept-closure-report.json
│   ├── XK06-cascade.json
│   ├── XK10-framework-gap-ledger.json
│   ├── recursive-state/
│   ├── XK11-semantic-coverage.json
│   └── XK11-prose-review.json
├── artifacts/
├── delivery/
│   └── artifact-index.md
├── validation/attempts/
└── continuation/
    ├── terminal-authority-key.json  # 终态签发后删除
    ├── xk12-transaction.json
    ├── completion.json
    └── terminal-record.json
```

运行目录遵循平台状态根或显式 `--runs-root`；不写仓库、安装目录或固定输出根，不创建任何跨运行共享的控制面或发布流水线。
