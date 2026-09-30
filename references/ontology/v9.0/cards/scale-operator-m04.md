---
id: V90-CANON-SCALE-OPERATOR-M04
source_concept_id: scale_operator:M04
framework_version: v9.0
---

# scale_operator:M04

## 原文层

来源：`V90-P00722`

5.5.4　M04　时间累积

来源：`V90-P00723`

签名是“带窗口的纵向组合”。必须冻结时间基准、基线、窗口、时滞、持久阈值和累积/衰减/恢复规则，并比较共同趋势、季节、队列和替代窗口。效应在控制后消失或随窗口变化，只表示正向支持不足；没有通过零结论门，不能发布“无累积”。基础时间组合不预证 G3；只有历史项在控制当前状态后仍提供条件增量时，才链接 G3-instance。

## 解释层

允许边界：仅在本项原文全部适用条件与分支条件内使用scale_operator:M04；独立对象材料支持实例，定义和接口只确定意义。

禁止边界：转义不是M10，算子结果四态不合并。

## 依赖角色

本身份没有登记跨身份依赖边；这不免除具体任务中的输入与方法条件。

## source_undefined

- Task-specific empirical parameters and evidence cannot be supplied by the concept definition.
