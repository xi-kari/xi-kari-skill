## 5.3　积偏序与变换分类

SP0≼SP1 当且仅当九轴全部为 equal 或 expands；严格关系 SP0≺SP1 还要求至少一轴 expands。机器分类按以下顺序执行：

任一轴 incomparable：horizontal_or_incomparable；已知不可比不会被另一轴的未知覆盖；

否则同时出现扩展和收缩：mixed；两种已知方向已经足以排除积偏序，即使还有轴未知；

否则任一轴 unknown：unresolved；

九轴全 equal：all_equal；

仅含 equal/expands 且至少一轴扩展：elevation；

仅含 equal/contracts 且至少一轴收缩：reduction。

因此，宏观聚合同时压缩观察分辨率时通常是 mixed，不应笼统叫升格；领域类比常是 horizontal_or_incomparable；材料不足时是 unresolved。只有分类为 elevation 的实例才使用“尺度升格”。观察范围、空间范围、组织范围、影响范围或网络范围扩大，都不会改变 J；J 只能由新的有效授权元组见证扩展。

J 状态不是“一个来源 + 一组主体 + 一组对象 + 一组动作”的独立字段拼盘，因为那会凭空生成未被授权的对象—动作组合。authorization_tuple_contract 要求每个原子元组只绑定一个来源、一个决策主体、一个对象和一个动作，同时保存地域、有效期、撤回条件、证据和独立复核；多对象或多动作必须拆成多个元组。只有状态为有效的规范化原子元组进入集合比较。J 轴扩展的见证要在 comparison_payload 中列出目标新增而源端没有的完整元组及其独立有效性证据，并与记录的 j_authorization 对齐。任意字符串、tuple ID、自称、实际控制、观察覆盖、影响扩大、上位组织位置或其他轴的扩展都不能使 J 变为 expands。

