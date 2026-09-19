# Core bundle: event → path → three orders

## 联读目的

把冻结事件、联合状态更新、分叉路径和多阶推演组成连续闭环，确保三阶不是时间跨度换名。

## 必须一起读取

1. event-and-recursive-inference.md：事件合同、路径节点和递归停止。
2. operation-mechanisms.md：通道、反馈、负荷、相位和级联。
3. core-boundary-contracts.md：D0、D2、D3 和 K。

## 原文锚点

V83-P0401—V83-P0405；V83-P1933—V83-P2131；V83-P2566—V83-P2600。

## 禁止孤立推断

- 事件来源、时间和争议未冻结时不建立路径。
- 每条边缺 carrier、clock、evidence、countermechanism 或 failure_condition 时只能保留候选。
- 二阶通道失败后禁止继续生成制度化、锁定或跨圈层三阶。
- 模拟递归不提升事实等级。

## 运行接口

一阶记录直接状态差分；二阶记录行动、资源、反馈、策略和事件生成条件改变；三阶记录制度化、自我复制、锁定、逆转或跨圈层溢出，并附早期/反向信号。
