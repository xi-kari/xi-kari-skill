# 安全政策

## 报告方式

涉及防伪与完整性的问题——例如完整性校验绕过、封存运行的哈希链或签名终态伪造、runtime 子进程边界逃逸——请通过 GitHub 的私密漏洞报告提交（仓库 Security 标签页 → Report a vulnerability），不要开公开 issue。

一般性缺陷（运行报错、文档问题）走普通 issue 即可。

## 范围

- `scripts/xi_kari_runtime/` 与五条完整性自检脚本
- `schemas/` 中的结构字段与拒绝条件
- 封存运行的阶段哈希链、XK12 事务与 Lamport 签名终态

## 支持版本

仅 `main` 分支最新提交受支持。
