# Windows / PowerShell 宿主命令卡

本卡只解决宿主环境摩擦，不改变任何语义合同。适用对象：在 Windows PowerShell 或 pwsh
中执行读取、检索与校验的宿主。同类命令反复失败时，先查本卡，不要现场反复试错。

## 检索（rg / Select-String）

- rg 模式一律用单引号包裹；多个分支不要写成 `"a|b"`，用 `-e` 逐项传参：
  `rg -n -e 'pattern-a' -e 'pattern-b' <文件>`。
- 双引号内的 `|` 会被 PowerShell 当作管道解析，是最常见的失败点；出现解析报错先检查
  引号，不要连续重试同型写法。
- rg 不可用或反复失败时，直接换 Select-String 等价式：
  `Select-String -LiteralPath <文件> -Pattern 'pattern' -Encoding utf8`。
- `--glob` 带引号在部分宿主下失败：先试不带引号，再退回
  `Get-ChildItem -Recurse | Where-Object`。

## 长卷分段读取

- 先取总行数再规划分段：`(Get-Content -LiteralPath <文件>).Count`。
- 用 `Get-Content -LiteralPath <文件> | Select-Object -Skip <N> -First <M>` 分段接续，
  段间保持少量重叠、连续读到文件末尾，不留缺口。
- 每读完一卷，按 runtime-read-map 的读取进度账本条款把卷号与行位落盘；
  上下文压缩或断流后凭账本续读，不重读已回执卷。账本仅对同一 run 有效，
  新 run 一律从第一卷重新完整读取。

## source manifest 字段名

- 清单位于 `references/source/v8.2/source-manifest.json`：按序卷名在 `reader_units`
  （与 `sequence` 同序），逐卷散列在 `reader_file_sha256`（键形如 `reader/<卷名>`），
  全部 reader 文件路径（含索引）在 `reader_files`。不要猜测不存在的字段名。

## 路径与环境

- Git Bash 路径是 `/c/...`，WSL 是 `/mnt/c/...`；bash 脚本失败先确认当前是哪一种 bash。
- 补丁与回滚脚本注意 CRLF/LF 混杂：git 操作显式加 `-c core.autocrlf=false`。
- `Format-Table` 按终端宽度截断输出；取完整值用 `Select-Object -ExpandProperty`
  或 `ConvertTo-Json`。
- run 目录建在稳定的本地数据目录（平台状态根或显式指定）：避开云同步目录
  （同步冲突会破坏散列自证工件），也避开系统临时目录（会被清理）。

## 交付前自查

- 投影卫生：`python scripts/check_projection_hygiene.py <主答案与投影文本文件>`，
  命中散列、退出码、回执表行等机器残留即退出码 1；细则见 answer-contract 第 7 节。
- 包完整性五项校验命令见 AGENTS.md「包完整性自检」；每脚本本轮至多一轮，
  并记录执行时间。
