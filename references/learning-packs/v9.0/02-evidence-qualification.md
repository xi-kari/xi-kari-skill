# 经验资格与认识约束

本学习包从 v9.0 身份卡与类型化依赖图生成；它组织阅读，不替代原文或候选处置。

## 必读身份

- `G1` → `V90-CANON-G1`；卡片：`references/ontology/v9.0/cards/g1.md`
- `G2` → `V90-CANON-G2`；卡片：`references/ontology/v9.0/cards/g2.md`
- `G3` → `V90-CANON-G3`；卡片：`references/ontology/v9.0/cards/g3.md`
- `G4` → `V90-CANON-G4`；卡片：`references/ontology/v9.0/cards/g4.md`
- `E1` → `V90-CANON-E1`；卡片：`references/ontology/v9.0/cards/e1.md`
- `E2` → `V90-CANON-E2`；卡片：`references/ontology/v9.0/cards/e2.md`
- `E4` → `V90-CANON-E4`；卡片：`references/ontology/v9.0/cards/e4.md`
- `E3` → `V90-CANON-E3`；卡片：`references/ontology/v9.0/cards/e3.md`
- `E5` → `V90-CANON-E5`；卡片：`references/ontology/v9.0/cards/e5.md`

## 边界

- `G1`：无第五根；正式实例门不扩为全知识真值门。
- `G2`：把总效应当指定通道支持，或无G2便删除总效应。
- `G3`：遗漏已知S制造G3增益；以一般学习改写G3b；无G3便否认技能习得。
- `G4`：预测充分自动推出干预充分；不显著自动推出闭合；用同尺度遗漏冒充G4。
- `E1`：一字段缺失删除所有来源事实。
- `E2`：每题机械增加视角；一种记录当全部状态。
- `E4`：凑数虚构竞争解释，或用整体感填证据空白。
- `E3`：仅有时序先后或“被观察会改变对象”的机制故事不足以通过；必须定位通道，并建立未观测、替代观测或阻断反事实。
- `E5`：添加E5→G4硬依赖构成循环，或把方法门当经验原因。

## 依赖

- `inferential_requires`：`V90-CANON-E5` → `V90-CANON-D3`；base
- `protocol_requires`：`V90-CANON-E5` → `V90-CANON-E1`；cross_scale_transfer
- `protocol_requires`：`V90-CANON-E5` → `V90-CANON-E4`；cross_scale_transfer
- `protocol_requires`：`V90-CANON-E5` → `V90-EXTERNAL-GATE-ANALOGY`；cross_scale_transfer
- `protocol_requires`：`V90-CANON-E5` → `V90-EXTERNAL-GATE-ANALOGY-D39ADDF3`；cross_scale_transfer
- `protocol_requires`：`V90-CANON-E5` → `V90-EXTERNAL-GATE-EVIDENCE`；cross_scale_transfer
- `protocol_requires`：`V90-CANON-E5` → `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0`；cross_scale_transfer
- `protocol_requires`：`V90-CANON-G4` → `V90-CANON-E5`；formal_instance
