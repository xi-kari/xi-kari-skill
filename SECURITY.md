# 安全政策

## 报告方式

涉及完整性与可信边界的缺陷——例如安装包或随包资源被篡改、理论原文身份校验（`scripts/read_source.py --check`）可被绕过、离线阅读页或条件模型页面中的脚本注入、脚本以超范围路径读写文件——请使用 GitHub 的私密漏洞报告提交（仓库 Security 标签页 → Report a vulnerability），不要开公开 issue。

一般性缺陷（运行报错、文档问题、排版错误）走普通 issue 即可。

## 范围

- `scripts/` 中的只读工具与安装包构建：路径处理、归档内容与文件散列
- `source/source-manifest.json` 记录的理论原文身份，以及 `read_source.py` 的校验路径
- `assets/reader.js`、`assets/reader.css`、`assets/condition-lab.js` 及其生成的离线 HTML
- 随包第三方资源（KaTeX）的来源与许可证完整性

本技能是本地运行的 Markdown 指令与标准库脚本，不含服务端、后台进程、网络回执或账号系统。涉及宿主模型行为、生成内容正确性或理论有效性的问题不属于安全报告，请改走 issue 或 Discussions。

## 支持版本

仅 `main` 分支最新提交受支持。历史归档版本（`archive/*` 标签）不再维护。
