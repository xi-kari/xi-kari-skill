# 机制、反馈与学习

本学习包从 v9.0 身份卡与类型化依赖图生成；它组织阅读，不替代原文或候选处置。

## 必读身份

- `CM-FEEDBACK` → `V90-CANON-CM-FEEDBACK`；卡片：`references/ontology/v9.0/cards/cm-feedback.md`
- `CM-LEARNING` → `V90-CANON-CM-LEARNING`；卡片：`references/ontology/v9.0/cards/cm-learning.md`
- `CM-MAINTENANCE` → `V90-CANON-CM-MAINTENANCE`；卡片：`references/ontology/v9.0/cards/cm-maintenance.md`
- `CM-LOAD` → `V90-CANON-CM-LOAD`；卡片：`references/ontology/v9.0/cards/cm-load.md`
- `CM-PHASE` → `V90-CANON-CM-PHASE`；卡片：`references/ontology/v9.0/cards/cm-phase.md`
- `CM-SELECTION` → `V90-CANON-CM-SELECTION`；卡片：`references/ontology/v9.0/cards/cm-selection.md`

## 边界

- `CM-FEEDBACK`：普通学习不是CM-LEARNING别名；瞬时/基础模式不硬加G3。
- `CM-LEARNING`：一次更新或普通学习直接通过；更换目标抹去旧失败。
- `CM-MAINTENANCE`：普通学习不是CM-LEARNING别名；瞬时/基础模式不硬加G3。
- `CM-LOAD`：普通学习不是CM-LEARNING别名；瞬时/基础模式不硬加G3。
- `CM-PHASE`：普通学习不是CM-LEARNING别名；瞬时/基础模式不硬加G3。
- `CM-SELECTION`：普通学习不是CM-LEARNING别名；瞬时/基础模式不硬加G3。

## 依赖

- `inferential_requires`：`V90-CANON-CM-FEEDBACK` → `V90-CANON-D2`；base
- `inferential_requires`：`V90-CANON-CM-FEEDBACK` → `V90-CANON-G2`；base
- `protocol_requires`：`V90-CANON-CM-FEEDBACK` → `V90-CANON-E4`；base
- `protocol_requires`：`V90-CANON-CM-FEEDBACK` → `V90-EXTERNAL-GATE-CAUSAL`；base
- `protocol_requires`：`V90-CANON-CM-FEEDBACK` → `V90-EXTERNAL-GATE-CAUSAL-DE06B986`；base
- `protocol_requires`：`V90-CANON-CM-FEEDBACK` → `V90-EXTERNAL-GATE-EVIDENCE`；base
- `protocol_requires`：`V90-CANON-CM-FEEDBACK` → `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0`；base
- `inferential_requires`：`V90-CANON-CM-LEARNING` → `V90-CANON-CM-FEEDBACK`；base
- `inferential_requires`：`V90-CANON-CM-LEARNING` → `V90-CANON-G3`；base
- `protocol_requires`：`V90-CANON-CM-LEARNING` → `V90-CANON-E4`；base
- `protocol_requires`：`V90-CANON-CM-LEARNING` → `V90-EXTERNAL-GATE-CAUSAL`；base
- `protocol_requires`：`V90-CANON-CM-LEARNING` → `V90-EXTERNAL-GATE-CAUSAL-DE06B986`；base
- `protocol_requires`：`V90-CANON-CM-LEARNING` → `V90-EXTERNAL-GATE-EVIDENCE`；base
- `protocol_requires`：`V90-CANON-CM-LEARNING` → `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0`；base
- `inferential_requires`：`V90-CANON-CM-LOAD` → `V90-CANON-D0`；base
- `inferential_requires`：`V90-CANON-CM-LOAD` → `V90-CANON-G2`；base
- `inferential_requires`：`V90-CANON-CM-LOAD` → `V90-CANON-G3`；cumulative
- `protocol_requires`：`V90-CANON-CM-LOAD` → `V90-CANON-E4`；base
- `protocol_requires`：`V90-CANON-CM-LOAD` → `V90-EXTERNAL-GATE-CAUSAL`；base
- `protocol_requires`：`V90-CANON-CM-LOAD` → `V90-EXTERNAL-GATE-CAUSAL-DE06B986`；base
- `protocol_requires`：`V90-CANON-CM-LOAD` → `V90-EXTERNAL-GATE-EVIDENCE`；base
- `protocol_requires`：`V90-CANON-CM-LOAD` → `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0`；base
- `inferential_requires`：`V90-CANON-CM-MAINTENANCE` → `V90-CANON-D0`；base
- `inferential_requires`：`V90-CANON-CM-MAINTENANCE` → `V90-CANON-G2`；base
- `inferential_requires`：`V90-CANON-CM-MAINTENANCE` → `V90-CANON-G3`；cumulative
- `protocol_requires`：`V90-CANON-CM-MAINTENANCE` → `V90-CANON-E4`；base
- `protocol_requires`：`V90-CANON-CM-MAINTENANCE` → `V90-EXTERNAL-GATE-CAUSAL`；base
- `protocol_requires`：`V90-CANON-CM-MAINTENANCE` → `V90-EXTERNAL-GATE-CAUSAL-DE06B986`；base
- `protocol_requires`：`V90-CANON-CM-MAINTENANCE` → `V90-EXTERNAL-GATE-EVIDENCE`；base
- `protocol_requires`：`V90-CANON-CM-MAINTENANCE` → `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0`；base
- `specializes`：`V90-CANON-CM-MAINTENANCE` → `V90-CANON-D1`；state_vocabulary
- `inferential_requires`：`V90-CANON-CM-PHASE` → `V90-CANON-D0`；base
- `inferential_requires`：`V90-CANON-CM-PHASE` → `V90-CANON-D1`；base
- `inferential_requires`：`V90-CANON-CM-PHASE` → `V90-CANON-G2`；causal-trigger
- `inferential_requires`：`V90-CANON-CM-PHASE` → `V90-CANON-G3`；hysteretic
- `protocol_requires`：`V90-CANON-CM-PHASE` → `V90-CANON-E4`；base
- `protocol_requires`：`V90-CANON-CM-PHASE` → `V90-EXTERNAL-GATE-CAUSAL`；causal-trigger_or_hysteretic_only
- `protocol_requires`：`V90-CANON-CM-PHASE` → `V90-EXTERNAL-GATE-CAUSAL-DE06B986`；causal-trigger_or_hysteretic_only
- `protocol_requires`：`V90-CANON-CM-PHASE` → `V90-EXTERNAL-GATE-EVIDENCE`；base
- `protocol_requires`：`V90-CANON-CM-PHASE` → `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0`；base
- `inferential_requires`：`V90-CANON-CM-SELECTION` → `V90-CANON-D1`；base
- `inferential_requires`：`V90-CANON-CM-SELECTION` → `V90-CANON-G2`；carrier
- `inferential_requires`：`V90-CANON-CM-SELECTION` → `V90-CANON-G3`；history
- `protocol_requires`：`V90-CANON-CM-SELECTION` → `V90-CANON-E4`；base
- `protocol_requires`：`V90-CANON-CM-SELECTION` → `V90-EXTERNAL-GATE-CAUSAL`；base
- `protocol_requires`：`V90-CANON-CM-SELECTION` → `V90-EXTERNAL-GATE-CAUSAL-DE06B986`；base
- `protocol_requires`：`V90-CANON-CM-SELECTION` → `V90-EXTERNAL-GATE-EVIDENCE`；base
- `protocol_requires`：`V90-CANON-CM-SELECTION` → `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0`；base
