---
id: V90-CANON-SCALE-OPERATOR-M08
source_concept_id: scale_operator:M08
framework_version: v9.0
---

# scale_operator:M08

## 原文层

来源：`V90-P00732`

5.5.8　M08　压缩/抽象

来源：`V90-P00733`

签名是“多对一表示压缩”。源材料、算法、阈值、版本、误差、不可恢复信息和任务所需不变量必须可追踪。unknown、not_applicable、not_observable、withheld_for_protection 必须保持区分，任何一种都不能压成“不存在”。高损失表示不得支持高影响行动。

来源：`V90-P00734`

可用一个精确的任务充分性条件说明压缩：源状态为x，表示为z=f(x)，当前所需答案为q(x)。当且仅当任意f(x₁)=f(x₂)都意味着q(x₁)=q(x₂)，才存在函数g使q=g∘f。它说明原状态未必能恢复，而当前问题仍可能准确回答；它没有保证g易于计算，也没有保证换一个问题、环境或干预后仍充分。〔研究05.01—05.02、05.05—05.06；此处为形式说明〕

## 解释层

允许边界：仅在本项原文全部适用条件与分支条件内使用scale_operator:M08；独立对象材料支持实例，定义和接口只确定意义。

禁止边界：转义不是M10，算子结果四态不合并。

## 依赖角色

本身份没有登记跨身份依赖边；这不免除具体任务中的输入与方法条件。

## source_undefined

- Task-specific empirical parameters and evidence cannot be supplied by the concept definition.
