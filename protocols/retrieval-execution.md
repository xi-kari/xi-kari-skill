# Xi-Kari v2 检索执行投影与宿主回执

## 权责边界

生产型开放世界运行把检索语义与执行事实分开。模型只提交五向查询意图、候选来源、
模型生成的来源摘述、逐来源语义评价、饱和判断和剩余未知。模型来源记录中的 `source_id`
仅是供语义交叉引用的临时别名，不是执行权威；投影后的来源 ID、`query_id`、执行状态、
执行时间、访问时间、内容哈希、进程 ID、事件哈希和回执哈希全部由 runtime 生成。
`accessed_at`、`content_authority`、`content_sha256`、`run_id` 等运行字段，以及查询执行
字段，模型提交时必须在写入运行包之前失败。

开放世界和封闭输入使用不同的模型字段合同。开放世界来源必须携带 HTTPS URL、发布者和
摘述；封闭输入来源只能引用 runtime 预冻结的材料身份、标题、正文和可选日期，不能携带
外部 URL、发布者或任何运行字段。封闭材料 manifest 与执行元数据只能由 runtime 注入，
不能由模型预占。

检索投影不得改变模型数组项对应的 canonical visibility 路径。查询按 `direction + query`、
开放世界来源按 URL、封闭输入来源按 `source_id`、逐来源评价按其来源身份逐项比较；任何
重排或身份漂移都在正式 run 目录创建前失败。Runtime 只可按模式各自冻结的 allowlist
为 projection 新增路径补固定 visibility 分类：开放世界是
`query_id/status/executed_at/result_source_ids`、来源
`source_id/accessed_at/content_authority` 和评价 `source_id`；封闭输入是查询执行字段、
来源 `accessed_at` 和冻结材料 manifest 的 `source_id`。两种 allowlist 不合并，也不存在
其它默认 `public/include` 路径。模型 visibility ledger 若预占运行专属路径，必须拒绝；
projection 新增的未知路径也必须拒绝。

纯投影函数不自行形成执行权威。只有仓库绑定、拥有子进程句柄的正式 adapter 直接提供
provider 和 adapter 文件哈希、实际 PID、pipe 字节、退出状态与起止时间，并由 runtime
封存其输入和产物后，投影结果才可成为宿主回执。调用者传入的一组同形字段不能替代该边界。

## Codex JSONL 证据

宿主保存一次 fresh Codex 进程的完整 UTF-8 JSONL 标准输出。有效流必须有唯一
`thread.started`、唯一 `turn.started`、唯一且位于末尾的 `turn.completed`，并且不含
`turn.failed`、顶层 `error` 或 error item。只有已完成的 `web_search` item 可以形成执行证据。

五向顺序固定为当前基线、机制支持、反证、可比案例、低权力位置。每个意图必须按该顺序
对应恰好一个同文本 `search` action，并在下一个五向 `search` 之前至少完成一个进入来源
账本的 HTTPS `open_page` action。Runtime 仅按这段可观察的先后关系生成查询会话关联，
并绑定 action event ID、event SHA-256、原始 JSONL SHA-256、provider binding、adapter
executable、运行绑定输入、父子进程、起止时间和运行 ID。

## 证明范围

正式回执证明宿主观察到绑定进程完成了所列搜索与打开页面动作，并证明模型语义输出与
运行时检索投影之间的字节哈希关系。Codex JSONL 不暴露搜索结果列表；按事件先后生成的
查询会话关联不声称 URL 是搜索服务返回的结果。回执也不证明页面陈述为真，来源 `content`
明确是 `model-authored-excerpt`，不冒充宿主抓取的网页正文。来源真值仍由逐来源评价、
交叉来源关系、证据边和不能证明项约束。

Fresh validator 必须同时重读封存的 adapter 输入、原始 JSONL、模型语义检索输入、
运行时检索投影和回执，重新执行完整投影并重算全部哈希与逐查询、逐来源绑定。只验证调用者
自报的 PID、状态、时间或摘要哈希不能形成检索执行权威。运行绑定输入必须包含同一 run ID；
回执不能跨 run 重放；完成时间不得晚于冻结的 evidence cutoff。
