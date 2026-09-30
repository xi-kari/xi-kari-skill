"""Author instructions for source-bound version-four semantic outputs."""

from collections.abc import Mapping
from typing import Any

from .canonical_json import canonical_dumps


def build_prompt(request: Mapping[str, Any], *, byte_limit: int) -> bytes:
    instructions = (
        '根据冻结的问题合同，完整读取 source_inputs 中 v9.0 的 reader、源清单和本体读取计划，完成问题相关的分析。\n'
        '理论定义、适用条件和源未定义边界以当前原文为准；外部资料用于现实事实和案例。\n'
        '按实际读到的字节及问题关系填写 semantic_read_trace 和 ontology_read_trace。源单位必须对应真实 reader 文件，完整范围和顺序由读取计划确定。\n'
        '本体计划的每个候选、概念卡、必须邻居和连续性包分别读取并生成 content_witness；协议沿用 xi-kari.v3.ontology-content-witness/v1，'
        '其输入依次为 protocol、content_access_challenge、problem_contract_sha256、item_id、content_sha256，中间用空字符分隔。'
        '每条理由须含其 item_id 以及当前文件的具体 source observation。\n'
        '输出遵守 schemas/xk-v4-base-authoring-output.schema.json。semantic_packet.applicability 六项 world_state、transformation、mechanism、recursion、forecast、action_choice '
        '分别给出 applicable、not_applicable 或 undetermined，以及具体理由、原文来源和依赖。\n'
        '每条声明独立填写 claim_basis 和 formal_qualification。普通事实、文本解释、形式证明和规范论证按各自证据责任成立。'
        '正式资格请求使用准确的概念与实例引用，status 和 result_status 填 not_evaluated，由运行代码从实例输入重新计算。\n'
        'empirical_instances 仅提供 preregistration 和 evaluation 原始语义；derived_instances 提供实际前提和方法引用。实例记录须保留对象、总体、窗口、目标、'
        '所选亚型和成功判据、零模型、复杂度与泄漏控制、分析工件、独立时间记录、偏离和三个零结论门。\n'
        'inferential_requires 仅为当前激活的事实推论前提；protocol_requires、specializes、applies_to 分别记录程序与范围责任。'
        'input_requirements 单独记录材料是否可用。依赖不得冒充现实支持。\n'
        '每个材料保存实际版本、定位、谱系、研究设计、阅读范围、可得性与披露范围。source_exists、quotation_accurate、passage_supports_claim、world_fact_supported '
        '四项分别给出理由和依据。来源原文确实说过某事与现实中确实发生某事分别判断。\n'
        '具体机制给出通道、条件、中介、替代解释和击败条件。存在合理反方时作具体比较；无合理反方时给出检索范围与会改变判断的条件。\n'
        '适用世界状态时填写对象身份 K、九轴 SP、联合状态与类型化事件输入。观察、推断、模拟和 reported_statement 保持不同责任。'
        '运行 ID、状态差分散列、授权校验结果、实际执行回执由运行代码生成。\n'
        '适用尺度变换时使用十四段原文责任，绑定源/目标对象、K、SP、变量、算子分支、损失、残差、比较工件与实际根实例。'
        '适用递归时给出真实事件变化、下一轮问题输入、分支、停止/剪枝/合并条件与增量；深度不能增加证据等级。\n'
        '概率前瞻区分经验频率、条件模型、区间、支持顺序、方向、未知、主观信念、决策权重和计算优先级。'
        '选择记录含 no_action 基线、义务、行动状态、影响域、权限依据、审查和纠错端点，实际授权与执行由运行代码校验。\n'
        '若 source_inputs.domain_inputs 存在，逐项阅读其完整内容，返回 domain_trace.records 和 claim_links，填写 native_method、additional_distinction、'
        'inputs_outputs、limits_counterargument、costs_exit 与本题的具体关系。领域方法引用按方法或边界使用。\n'
        'open-world 按冻结的五向检索执行 search 并打开引用来源；closed-input 使用冻结给定材料，保持网络禁用。逐来源评价与材料顺序一致。\n'
        'facts 包含 known、claimed、inferred、unknown；案例区分真实案例、条件场景和反例；answer.basis_refs 引用本包存在的声明、证据或机制。\n'
        'reader_sections 写完整中文可读正文，并通过 source_bindings 精确引用责任字段。visibility_ledger 对全部语义逐项分类，purpose 等于隐私合同的 purpose。\n'
        '在当前私有工作目录写完整 semantic-output.json，顶层恰为 semantic_packet、semantic_read_trace、ontology_read_trace；'
        '自磁盘回读核对 schema 与引用。最后消息只写 SEMANTIC_OUTPUT_READY。运行权威、回执、终态和散列由代码保存。\n'
        '运行时请求：\n'
    )
    prompt = (instructions + canonical_dumps(dict(request)) + '\n').encode('utf-8')
    if len(prompt) > byte_limit:
        raise ValueError('base authoring prompt exceeds the size limit')
    return prompt
