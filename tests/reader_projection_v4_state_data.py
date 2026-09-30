"""Hand-authored expectations for synthetic state projection fixtures."""

SCALE_SECTION_NAMES = (
    "identity", "scale", "objects", "semantics", "transformation", "variables",
    "evidence", "loss", "responsibility", "normative", "protection", "action",
    "correction", "lifecycle",
)

# Relative paths and excerpts are authored independently of the runtime atom ledger.
SCALE_BODY = {
    "identity": (
        "声明的任务范围",
        "本例仅回答已经冻结的成员描述任务。",
        "目标任务是 describe nested boundary，目标量是 membership；用途限于 "
        "description_only，允许操作为 describe，时间范围为 frozen window，"
        "环境为 synthetic，容差为 exact。这些范围共同限制描述可以支持的判断。",
        {
            "purpose.target_task": "目标任务是 describe nested boundary",
            "purpose.target_quantity": "目标量是 membership",
            "purpose.use_scope[0]": "用途限于 description_only",
            "purpose.allowed_operations[0]": "允许操作为 describe",
            "purpose.horizon": "时间范围为 frozen window",
            "purpose.environment": "环境为 synthetic",
            "purpose.tolerance": "容差为 exact",
        },
    ),
    "scale": (
        "尺度比较的结果",
        "各轴相等只成立于本例的比较范围。",
        "独立比较给出的变换分类是 all_equal；它描述当前九轴相等，"
        "没有证明其他用途或时窗中的关系也相等。",
        {"transformation_class": "变换分类是 all_equal"},
    ),
    "objects": (
        "对象同一性的条件",
        "相同名称仍须服从来源与目标各自的判据。",
        "来源判据版本为 1，定义为 same bounded synthetic units；"
        "目标判据版本为 1，定义也为 same bounded synthetic units。"
        "本例的已检查映射分类是 same_object，成立范围只包括这组边界单位。",
        {
            "source_K.version": "来源判据版本为 1",
            "source_K.definition": "定义为 same bounded synthetic units",
            "target_K.version": "目标判据版本为 1",
            "target_K.definition": "定义也为 same bounded synthetic units",
            "identity_mapping.classification": "映射分类是 same_object",
        },
    ),
    "semantics": (
        "保留内容与禁止跨越的用途",
        "成员描述的保留不能授予干预权。",
        "保留的核心是 boundary and member identity；禁止跨越的用途是 "
        "description does not authorize intervention。任务保留的条件仍为 "
        "frozen description only，目标或用途改变后需要重新核查。",
        {
            "preserved_core[0]": "保留的核心是 boundary and member identity",
            "prohibited_mappings[0]": "description does not authorize intervention",
            "task_preservation.validity_conditions[0]": "条件仍为 frozen description only",
        },
    ),
    "transformation": (
        "任务充分与状态重建",
        "共同任务输出不能证明所有原状态已经恢复。",
        "本例按 descriptive_mapping 作描述，登记结果为有支持。"
        "对共同成员输出，任务充分性为是；对原始状态，可重建性为否。"
        "检查的原始状态是 x1 与 x2，其适用范围为 declared finite domain only。"
        "因此充分性只适用于声明的有限任务，不能推到隐藏差异已经消失。",
        {
            "claim_mode": "按 descriptive_mapping 作描述",
            "result_state": "登记结果为有支持",
            "equivalence_or_sufficiency.task_sufficient": "任务充分性为是",
            "equivalence_or_sufficiency.reconstructable": "可重建性为否",
            "equivalence_or_sufficiency.source_domain[0]": "原始状态是 x1 与 x2",
            "equivalence_or_sufficiency.source_domain[1]": "原始状态是 x1 与 x2",
            "equivalence_or_sufficiency.scope": "适用范围为 declared finite domain only",
        },
    ),
    "variables": (
        "尚未展开的变量依赖",
        "纯描述没有另立变量依赖推断。",
        "额外依赖在本例中不适用，给定理由为 "
        "Not applicable to the synthetic pure description。"
        "这个范围说明不能当作其他任务没有依赖关系的证据。",
        {
            "dependencies.status": "额外依赖在本例中不适用",
            "dependencies.reason": "Not applicable to the synthetic pure description",
        },
    ),
    "evidence": (
        "检查支持的任务",
        "观察检查支持描述任务本身。",
        "检查所指任务为 describe nested boundary，结果为有支持，"
        "范围为 description。这个支持没有越过描述任务的用途边界。",
        {
            "task_checks[0].task_ref": "任务为 describe nested boundary",
            "task_checks[0].result": "结果为有支持",
            "task_checks[0].scope": "范围为 description",
        },
    ),
    "loss": (
        "共同输出仍留下的损失",
        "同一成员答案保留了照护约束的损失。",
        "不可恢复的信息是 unmeasured care constraints。"
        "共同成员输出没有回答照护时间如何安排，后续改变任务时必须重新观察。",
        {"irrecoverable_information[0]": "不可恢复的信息是 unmeasured care constraints"},
    ),
    "responsibility": (
        "成本承担位置",
        "描述过程的复核成本仍有承担者。",
        "当前复核成本由 synthetic analyst 承担。"
        "共同描述结果没有使这项成本消失，也没有替其他主体承担成本作出选择。",
        {"cost_bearers[0]": "复核成本由 synthetic analyst 承担"},
    ),
    "normative": (
        "价值前提的边界",
        "可描述的结果不能直接裁定成本是否可接受。",
        "本例明示的前提为 Descriptions do not settle the normative acceptability "
        "of cost.；选择程序在本例中不适用，理由为 "
        "Not applicable to the synthetic pure description。"
        "因此当前描述不能替受影响主体接受这项成本。",
        {
            "value_premises[0]": "Descriptions do not settle the normative acceptability of cost.",
            "selection_kind.status": "选择程序在本例中不适用",
            "selection_kind.reason": "Not applicable to the synthetic pure description",
        },
    ),
    "protection": (
        "保护条件与用途变化",
        "当前纯描述的保护适用性有明确范围。",
        "对象类型为 nonhuman，用途为 description_only，给定理由为 "
        "Synthetic natural-object description。安全提交程序在本例中不适用，"
        "理由为 Not applicable to the synthetic pure description。"
        "这没有证明涉及人或分配用途时也可省去保护程序。",
        {
            "applicability.object_type": "对象类型为 nonhuman",
            "applicability.downstream_uses[0]": "用途为 description_only",
            "applicability.reason": "Synthetic natural-object description",
            "safe_submission.status": "安全提交程序在本例中不适用",
            "safe_submission.reason": "Not applicable to the synthetic pure description",
        },
    ),
    "action": (
        "判断与行动上限",
        "描述判断仍停留在讨论范围。",
        "判断上限为 bounded_description，行动上限为 deliberation_only；"
        "停止条件为 purpose change。即使当前描述有支持，也未选定或授权外部行动。",
        {
            "judgment_ceiling": "判断上限为 bounded_description",
            "action_ceiling": "行动上限为 deliberation_only",
            "stop_conditions[0]": "停止条件为 purpose change",
        },
    ),
    "correction": (
        "修复责任的范围",
        "当前纯描述没有声称已经实施修复。",
        "执行性修复在本例中不适用，给定理由为 "
        "Not applicable to the synthetic pure description。"
        "后来若触发更改用途或边界，应按新任务重新确定修复责任。",
        {
            "repair.status": "执行性修复在本例中不适用",
            "repair.reason": "Not applicable to the synthetic pure description",
        },
    ),
    "lifecycle": (
        "复核、暂停与退出",
        "描述的生命周期服从冻结时窗。",
        "当前有效时窗为 frozen；复核点为 purpose change，"
        "暂停条件为 identity failure，退出条件为 window end。"
        "退出本轮描述不能取消另行成立的既有义务。",
        {
            "validity.window": "有效时窗为 frozen",
            "review_points[0]": "复核点为 purpose change",
            "pause[0]": "暂停条件为 identity failure",
            "exit[0]": "退出条件为 window end",
        },
    ),
}

IDENTITY_PROTECTION_REASON = "未取得当事人披露同意"
IDENTITY_PROTECTED_BODY = (
    "来源与目标同一性判据的具体内容为保护而不公开，原因是未取得当事人披露同意。"
    "来源判据版本为 1，目标判据版本为 1；本例的映射分类是 same_object。"
    "仍须检查各自的判据和映射，公开边界不能当作对象可互换的证明。"
)

ALTERNATIVE_COST_BODY = {
    "loss": (
        "共同输出仍留下的损失",
        "同一成员答案仍留下稽核约束的损失。",
        "不可恢复的信息是 unmeasured audit constraints。"
        "共同成员输出没有回答稽核工时如何安排，后续改变任务时必须重新观察。",
        {"irrecoverable_information[0]": "不可恢复的信息是 unmeasured audit constraints"},
    ),
    "responsibility": (
        "成本承担位置",
        "另一条描述路径的复核成本仍有承担者。",
        "当前复核成本由 synthetic reviewer 承担。"
        "共同描述结果没有使这项成本消失，也没有替其他主体承担成本作出选择。",
        {"cost_bearers[0]": "复核成本由 synthetic reviewer 承担"},
    ),
}
