---
id: V90-CANON-B478-EQUAL-EXPANDS-CONTRACTS-INCOMPARABLE-UNKNOW-E7E090F5DA
source_concept_id: 原文规则@B478:每轴关系只有五种：equal、expands、contracts、incomparable、unknown
framework_version: v9.0
---

# 原文规则@B478:每轴关系只有五种：equal、expands、contracts、incomparable、unknown

## 原文层

来源：`V90-P00686`

每轴关系只有五种：equal、expands、contracts、incomparable、unknown。轴比较记录固定包含 axis_id、源/目标状态、关系、顺序见证、信息损失和不确定性。非未知关系的 order_witness 不是一句说明，而是闭合对象：comparator_id 与 comparator_version 必须对应该轴比较器，verifier_id 明确谁或什么执行验证，evidence_refs 非空，comparison_payload 给出实际映射、集合、区间、图或授权差异，verification_artifact_ref 与 verification_hash 指向可复核产物，validation_status 必须为 valid。unknown 使用带理由的缺失状态。完全相同的两状态可用内置深相等复算 equal；其他相等以及全部扩展、收缩和不可比关系，都必须从外部比较器结果注册表核对轴、版本、源/目标摘要、关系和哈希。相同状态申报扩展或收缩直接失败。没有可解析见证，只能记 unknown；contracts 是同轴 expands 的逆关系，不是凭语言印象标注。

## 解释层

允许边界：每轴关系只有五种：equal、expands、contracts、incomparable、unknown。轴比较记录固定包含 axis_id、源/目标状态、关系、顺序见证、信息损失和不确定性。非未知关系的 order_witness 不是一句说明，而是闭合对象：comparator_id 与 comparator_version 必须对应该轴比较器，verifier_id 明确谁或什么执行验证，evidence_refs 非空，comparison_payload 给出实际映射、集合、区间、图或授权差异，verification_artifact_ref 与 verification_hash 指向可复核产物，validation_status 必须为 valid。unknown 使用带理由的缺失状态。完全相同的两状态可用内置深相等复算 equal；其他相等以及全部扩展、收缩和不可比关系，都必须从外部比较器结果注册表核对轴、版本、源/目标摘要、关系和哈希。相同状态申报扩展或收缩直接失败。没有可解析见证，只能记 unknown；contracts 是同轴 expands 的逆关系，不是凭语言印象标注。

禁止边界：逐轴五关系与独立结构见证，深相等可内建，其余外部注册复核；无见证unknown，同状态不可报扩收。

## 依赖角色

本身份没有登记跨身份依赖边；这不免除具体任务中的输入与方法条件。

## source_undefined

- 无作为开放默认值登记的源未定义字段。
