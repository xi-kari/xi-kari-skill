# HV01-HV11 完整接口字段联读包

附录 A 要求每张 HV 卡按 A-E 五区登记同一组 39 个字段（`V82-P2907`-`V82-P2908`、`V82-P1216`-`V82-P1218`）。本仓库的逐卡文件提供人类可读的定义、上限、反例和三阶接口；完整字段仍以 v8.2 reader 的附录 A 为权威，不能用本包的压缩替代原文。

## 字段闭包

`id`、`qualified_id`、`name`、`proposition`、`scope`、`claim_type`、`contract_role`、`pause_condition`、`allowed_inference`、`prohibited_leap`、`inferential_requires`、`protocol_requires`、`specializes`、`applies_to`、`conditional_support_routes`、`scale_profile`、`effective_object`、`state`、`observables`、`evidence`、`input_dependencies`、`output_effects`、`carrier`、`responsible_subject`、`time_window_and_lag`、`uncertainty`、`local_exclusion_zone`、`affected_positions`、`normative_status`、`scale_invariants`、`required_scale_additions`、`changing_semantics`、`non_applicable_objects`、`forbidden_elevation`、`judgment_ceiling`、`action_ceiling`、`counterexamples`、`appeal`、`rollback`。

## 读取规则

- `inferential_requires`、`protocol_requires`、`specializes`、`applies_to` 四类依赖不可混用；只在某条结论路由需要的条件进入 `conditional_support_routes`（`V82-P1217`）。
- 空集合只表示没有登记依赖，不表示证据充分。
- H1/H4/H5 的实例证据、H2/H3/H6 的分类/规范边界和 CM 条件机制不能互相冒充。
- 跨尺度时逐轴登记保持、改变、丢失、低可见位置和局部排除区；判断上限不超过证据，行动上限不超过 J。
- 新变量若没有 v8.2 定义，写入 `source_undefined_fields` 或运行时 `XK-PROV-*`，不得静默升格。

## 覆盖

`hv01-structure-domain.md` 至 `hv11-open-bearing-action.md` 分别对应 HV01-HV11；原始全文位于 `references/source/v8.2/reader/17-appendix-a-human-variable-cards.md`，每张卡必须与相应 `V82-P` 锚点逐项核对。

## 三阶接口

字段级推演仍遵守：一阶直接状态差；二阶行动/资源/反馈和生成条件；三阶制度化、锁定、逆转或跨圈层溢出。没有字段、通道或外部证据时，路径在当前阶终止。

## source_undefined

v8.2 没有为 39 字段提供跨场景默认值、统一权重或自动填充器；所有缺失必须标明缺失类型（not_collected、not_observable、not_applicable、conflicted、unknown），不得补成零值或“正常”。

## 来源锚点

- [v8.2 reader 07](../../source/v8.2/reader/07-human-structured-world.md): `V82-P1215`-`V82-P1244`。
- [v8.2 reader 附录 A](../../source/v8.2/reader/17-appendix-a-human-variable-cards.md): `V82-P2906`-`V82-P4477`。
