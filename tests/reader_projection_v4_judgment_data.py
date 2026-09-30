"""Synthetic helper-backed records and independently authored projection bodies."""

from copy import deepcopy

from tests.test_causal_judgment_choice import authorization_inputs, comparison_inputs
from tests.test_causal_judgment_forecasts import forecast_inputs
from tests.test_causal_judgment_probability import conditional_model, frequency
from xi_kari_runtime import choice, forecasting, judgment_boundaries
from xi_kari_runtime.semantic_projection import semantic_atom_paths


DIRECT = '本例全部使用合成材料，只核对语义助手结果在读者正文中的保留。'
BOUNDARY = '主观信念的数值为保护而不公开；未取得该数值的披露同意。'
BASELINE = '维持现有职责'
PILOT = '限定试行'


def supported(*references):
    return {reference: {'blocked': False} for reference in references}


def bindings(prefix, paragraph_index, text, fields):
    return [{'source_path': f'{prefix}.{field}', 'paragraph_index': paragraph_index,
             'excerpt': text} for field in fields]


def section(identifier, heading, judgment, paragraphs, source_bindings):
    return {'section_id': identifier, 'heading': heading, 'local_judgment': judgment,
            'paragraphs': paragraphs, 'source_bindings': source_bindings}


def public_visibility(payload):
    payload['visibility_ledger'] = {'entries': [
        {'canonical_path': path, 'classification': 'public', 'disclosure': 'include',
         'purpose': 'synthetic reader projection', 'authority_refs': [],
         'protection_reason': None}
        for path in semantic_atom_paths(payload)
    ]}
    return payload


def projection(root, record, sections):
    opening = section('synthetic-scope', '本例的适用范围', DIRECT,
        ['语义身份与证据范围由被调用的助手校验；正文排版不能增加事实支持或行动权限。'],
        bindings('answer', 0, DIRECT, ['direct_answer']))
    return public_visibility({'schema_version': 4, root: deepcopy(record),
        'answer': {'direct_answer': DIRECT}, 'reader_sections': [opening, *sections]})


def unknown_projection():
    record, state, transition = forecast_inputs()
    record['target'] = record['expression']['event'] = '合成演练的交接延迟下降'
    record['expression'].update(reason='尚不能识别发生方向或数值概率。',
                                minimal_observations=['补测交接延迟并区分自然波动'])
    frozen = forecasting.freeze_forecast(record, parent_state=state,
        parent_transition=transition, claim_constraints={})
    expression = frozen['contract']['expression']
    judgment = '合成演练的交接延迟下降这一目标当前保持未知；尚不能识别发生方向或数值概率。'
    paragraph = '最少需要补测交接延迟并区分自然波动；未知不能被改写为方向、数值概率或执行许可。'
    body = section('unknown-event', '无法定量的目标', judgment, [paragraph],
        bindings('forecast', 0, judgment, ['kind', 'event', 'reason'])
        + bindings('forecast', 1, paragraph, ['minimal_observations[0]']))
    return projection('forecast', expression, [body]), frozen


def frequency_projection(calibration_status='not_tested'):
    record = frequency()
    record.update(event='合成演练中按时完成任务', reference_class='预先登记的三次合成演练',
        measurement_unit='每次登记任务', sampling_selection='纳入全部登记任务',
        support_claim_ids=['频次观察记录'])
    constraints = supported('频次观察记录', '独立结果校准记录')
    if calibration_status == 'evaluated':
        record['calibration'] = {'status': 'evaluated', 'model_version': '合成频次模型第一版',
            'window': '登记的二月留出窗', 'domain': '合成任务域', 'metric': '登记的布里尔评分',
            'result_claim_ids': ['独立结果校准记录']}
        calibration = ('校准已评估，评估对象是合成频次模型第一版，'
            '窗口为登记的二月留出窗，领域为合成任务域，指标为登记的布里尔评分；'
            '结果依据为独立结果校准记录。这只保留本例给出的评估窗口和证据引用，'
            '不证明样本预登记、现实校准或外域表现。')
        calibration_fields = ['calibration.status', 'calibration.model_version',
            'calibration.window', 'calibration.domain', 'calibration.metric',
            'calibration.result_claim_ids[0]']
    elif calibration_status == 'insufficient':
        record['calibration'] = {'status': 'insufficient', 'reason': '留出试次太少，覆盖误差仍未知。'}
        calibration = '校准证据不足；留出试次太少，覆盖误差仍未知。不得把有限观察数量写成校准完成。'
        calibration_fields = ['calibration.status', 'calibration.reason']
    else:
        record['calibration'] = {'status': 'not_tested', 'reason': '尚无独立未来结果样本。'}
        calibration = '校准尚未检验；尚无独立未来结果样本。这一频率不能自动获得可靠的未来现实概率身份。'
        calibration_fields = ['calibration.status', 'calibration.reason']
    checked = forecasting.validate_probability_expression(record, claim_constraints=constraints)
    judgment = ('合成演练中按时完成任务的经验频率是0.6666666666666666，'
                '这是3次登记任务中2次达标的比例。')
    sample = ('参照群为预先登记的三次合成演练，以每次登记任务为单位，纳入全部登记任务，'
              '资料截止2026-01-01T00:00:00Z。频次观察记录只记录已观察试次，'
              '不能把模型抽样当成实际试次。')
    body = section('empirical-frequency', '观察比例及其校准边界', judgment, [sample, calibration],
        bindings('forecast', 0, judgment, ['kind', 'event', 'value', 'positive_outcomes', 'sample_size'])
        + bindings('forecast', 1, sample, ['reference_class', 'measurement_unit', 'cutoff',
            'sampling_selection', 'support_claim_ids[0]', 'population_kind'])
        + bindings('forecast', 2, calibration, calibration_fields))
    return projection('forecast', checked, [body]), checked, constraints


def conditional_inputs():
    record = conditional_model()
    record.update(event='合成演练下次任务按时完成', model_version='合成模型第一版',
        assumptions=['同域任务可交换'], domain='合成任务域',
        uncertainty='三次观测之下的模型不确定性尚未收敛',
        model_claim_ids=['登记模型依据'], analysis_claim_ids=['登记计算依据'])
    record['prior']['basis_claim_ids'] = ['登记先验依据']
    record['data']['basis_claim_ids'] = ['任务观测依据']
    record['calibration'] = {'status': 'not_tested', 'reason': '尚无模型外的校准样本。'}
    return record, supported('登记模型依据', '登记计算依据', '登记先验依据', '任务观测依据')


def conditional_section(prefix='forecast'):
    judgment = ('合成演练下次任务按时完成的模型条件概率为0.5714285714285714，'
        '表达式是条件模型。它以合成模型第一版和同域任务可交换为条件，'
        '作用域限于合成任务域；生成方法为贝塔二项后验均值。')
    prior = ('先验已明确指定为beta分布，参数alpha=2、beta=2，依据登记先验依据；'
        '观测为直接观察的3次任务、2次达标，来自任务观测依据。')
    uncertainty = ('登记模型依据与登记计算依据支持这一计算，三次观测之下的模型不确定性尚未收敛。'
        '校准尚未检验；尚无模型外的校准样本。模型内数值不能自动成为现实事件概率。')
    source_bindings = (
        bindings(prefix, 0, judgment, ['kind', 'event', 'value', 'model_version', 'assumptions[0]',
            'domain', 'generation_method', 'probability_scope'])
        + bindings(prefix, 1, prior, ['prior.mode', 'prior.distribution', 'prior.alpha', 'prior.beta',
            'prior.basis_claim_ids[0]', 'data.status', 'data.sample_size',
            'data.positive_outcomes', 'data.basis_claim_ids[0]'])
        + bindings(prefix, 2, uncertainty, ['uncertainty', 'model_claim_ids[0]',
            'analysis_claim_ids[0]', 'calibration.status', 'calibration.reason']))
    return section('conditional-model', '模型条件、数据与未知', judgment, [prior, uncertainty], source_bindings)


def conditional_projection():
    record, constraints = conditional_inputs()
    checked = forecasting.validate_probability_expression(record, claim_constraints=constraints)
    return projection('forecast', checked, [conditional_section()]), checked


def interval_projection():
    base, constraints = conditional_inputs()
    constraints.update(supported('区间计算依据'))
    record = {'kind': 'probability_interval', 'event': base['event'], 'lower': 0.2, 'upper': 0.8,
        'method': '登记的贝塔后验分位数', 'interpretation': '模型条件可信区域',
        'level': 0.9, 'level_status': 'provided', 'base_expression': base,
        'analysis_claim_ids': ['区间计算依据'],
        'calibration': {'status': 'not_tested', 'reason': '区间覆盖尚未用独立结果检验。'}}
    checked = forecasting.validate_probability_expression(record, claim_constraints=constraints)
    judgment = ('合成演练下次任务按时完成的概率区间下界为0.2、上界为0.8；'
        '这是登记的贝塔后验分位数产生的模型条件可信区域。')
    interpretation = ('登记层级已提供，数值为0.9；区间计算依据支持该表达式，'
        '校准尚未检验，区间覆盖尚未用独立结果检验。层级和区间端点不能被当成实测成功率。')
    interval = section('conditional-interval', '区间方法和覆盖责任', judgment, [interpretation],
        bindings('forecast', 0, judgment, ['kind', 'event', 'lower', 'upper', 'method', 'interpretation'])
        + bindings('forecast', 1, interpretation, ['level', 'level_status', 'analysis_claim_ids[0]',
            'calibration.status', 'calibration.reason']))
    return projection('forecast', checked, [interval, conditional_section('forecast.base_expression')]), checked


def nonprobability_projection(kind, *, protected=False):
    event = '同一合成任务按时完成'
    if kind == 'subjective_belief':
        record = {'kind': kind, 'event': event, 'subject': '合成值班人',
            'information': '当前演练报告', 'time': '2026-01-01T00:00:00Z', 'value': 0.8,
            'basis_claim_ids': ['信念报告依据']}
        judgment = ('合成值班人对同一合成任务按时完成持有主观信念，'
            '在2026-01-01T00:00:00Z依据当前演练报告表达；信念报告依据支持的是这一报告。')
        meaning = ('报告的信念值为0.8，归属该主体和该信息时点；'
            '同一个数值不能因此成为现实事件概率或行动授权。')
        fields = ['kind', 'event', 'subject', 'information', 'time', 'basis_claim_ids[0]']
    elif kind == 'decision_weight':
        record = {'kind': kind, 'event': event, 'value': 0.8,
            'weight_model': '明示的规范权衡模型', 'premise_or_model_claim_ids': ['价值前提依据']}
        judgment = ('同一合成任务按时完成在明示的规范权衡模型中取得决策权重0.8，'
            '依据是价值前提依据。')
        meaning = '该权重比较的是决策中的重要程度，其数值不能成为现实事件发生概率或执行许可。'
        fields = ['kind', 'event', 'value', 'weight_model', 'premise_or_model_claim_ids[0]']
    else:
        record = {'kind': kind, 'event': event, 'priority': 1, 'reasons': ['后果严重且窗口短'],
            'budget': {'unit': '分析分钟', 'amount': 15}}
        judgment = '同一合成任务按时完成的计算优先级为1，因为后果严重且窗口短，本轮预算为15分析分钟。'
        meaning = '计算优先级安排有限计算资源的先后顺序；排在前面不能证明事件更可能发生或取得行动授权。'
        fields = ['kind', 'event', 'priority', 'reasons[0]', 'budget.unit', 'budget.amount']
    checked = forecasting.validate_probability_expression(record,
        claim_constraints=supported('信念报告依据', '价值前提依据'))
    source_bindings = bindings('forecast', 0, judgment, fields)
    if kind == 'subjective_belief':
        if protected:
            meaning = BOUNDARY + '其余信息只说明谁在何时持有何种信念，不能形成现实概率或行动授权。'
            source_bindings += bindings('forecast', 1, BOUNDARY, ['value'])
        else:
            source_bindings += bindings('forecast', 1, meaning, ['value'])
    body = section('expression-meaning', '数值所属的判断类型', judgment, [meaning], source_bindings)
    payload = projection('forecast', checked, [body])
    if protected:
        entry = next(entry for entry in payload['visibility_ledger']['entries']
                     if entry['canonical_path'] == 'forecast.value')
        entry.update(classification='sensitive', disclosure='withhold',
            authority_refs=['合成披露合同'], protection_reason='未取得该数值的披露同意')
    return payload, checked


def comparison_checked():
    state, record = comparison_inputs()
    for index, option in enumerate(state['available_actions']):
        option.update(option_id=BASELINE if index == 0 else PILOT,
            target_object='合成服务对象',
            action_type='no_new_action' if index == 0 else '有边界的可撤回试行')
    state['no_action_option_id'] = BASELINE
    state['existing_obligations'] = [{'obligation_id': 'maintenance',
        'condition': '日常维护义务持续有效', 'scope': '合成服务对象'}]
    record.update(options=deepcopy(state['available_actions']), no_action_option_id=BASELINE,
        recommended_option_id=BASELINE, existing_items=deepcopy(state['existing_obligations']),
        scope={'object_id': 'synthetic-object', 'window': '十月合成观察窗'},
        normative_basis_claim_ids=['本轮规范依据'], affected_positions=['服务使用者', '维护人员'],
        cost_distribution=[{'position': '服务使用者', 'cost': '持续等待成本'},
                           {'position': '维护人员', 'cost': '监测和维护人力成本'}],
        reasons=['试行的净收益证据仍不足'], counterarguments=['继续等待可能延长受损'],
        switch_conditions=['登记比较支持试行且停止机制仍可用'], natural_changes=['需求仍在自然变化'],
        observation_plan=['持续监测服务延迟'], reopen_conditions=['安全触发时重新比较'],
        responsible_subject='合成委员会')
    checked = choice.validate_action_comparison(record, action_state=state,
        claim_constraints=supported('本轮规范依据'))
    return checked, state


def comparison_projection():
    checked, state = comparison_checked()
    judgment = ('本轮建议在十月合成观察窗内采用不新增动作的比较基线，其动作是不新增动作，'
        '目标为合成服务对象。当前状态是建议优先采用，尚未取得执行授权；'
        '本轮仅形成分析建议，权限效果为无，即不新增授权。')
    alternative = '备选的外部行动方案是对合成服务对象开展有边界的可撤回试行；它仍是比较选项，尚未被实施。'
    duties = ('合成服务对象的日常维护义务持续有效，合成委员会负责持续履行。'
        '本轮建议明示N2前提，由本轮规范依据支持；不新增行动不能免除原有职责。')
    costs = '服务使用者承担持续等待成本，维护人员承担监测和维护人力成本，两个位置的负担必须分别保留。'
    opposition = '建议理由是试行的净收益证据仍不足；最强反对意见是继续等待可能延长受损，这一代价不能因建议等待而消失。'
    switches = ('比较基线时点为2026-09-30T00:00:00Z；需求仍在自然变化，观察计划是持续监测服务延迟。'
        '登记比较支持试行且停止机制仍可用时，应切换建议；安全触发时重新比较。')
    source_bindings = (
        bindings('action_ranking', 0, judgment, ['scope.window', 'selection_status',
            'execution_status', 'permission_effect', 'options[0].option_kind',
            'options[0].action_type', 'options[0].target_object'])
        + bindings('action_ranking', 1, alternative, ['options[1].option_kind',
            'options[1].action_type', 'options[1].target_object'])
        + bindings('action_ranking', 2, duties, ['existing_items[0].condition',
            'existing_items[0].scope', 'responsible_subject', 'normative_premises[0]',
            'normative_basis_claim_ids[0]'])
        + bindings('action_ranking', 3, costs, ['affected_positions[0]', 'affected_positions[1]',
            'cost_distribution[0].position', 'cost_distribution[0].cost',
            'cost_distribution[1].position', 'cost_distribution[1].cost'])
        + bindings('action_ranking', 4, opposition, ['reasons[0]', 'counterarguments[0]'])
        + bindings('action_ranking', 5, switches, ['baseline_time', 'natural_changes[0]',
            'observation_plan[0]', 'switch_conditions[0]', 'reopen_conditions[0]']))
    body = section('no-action-comparison', '比较、成本、反对意见与切换条件', judgment,
        [alternative, duties, costs, opposition, switches], source_bindings)
    return projection('action_ranking', checked, [body]), checked, state


def observed_no_action_projection():
    comparison, _ = comparison_checked()
    record = {'subject': '合成委员会', 'scope': comparison['scope'], 'chosen_baseline': BASELINE,
        'evidence_refs': ['合成会议观察记录'], 'existing_items': comparison['existing_items'],
        'permission_effect': 'none'}
    registry = {'合成会议观察记录': {'evidence_id': '合成会议观察记录', 'identity': 'observed',
        'decision_subject': '合成委员会', 'scope': comparison['scope'], 'chosen_baseline': BASELINE,
        'source_refs': ['SYNTHETIC-UNIT-FIXTURE']}}
    checked = choice.validate_no_new_action_choice(record, comparison=comparison,
        decision_evidence_registry=registry)
    judgment = ('合成会议观察记录确认合成委员会在十月合成观察窗选择维持现有职责作为基线；'
        '这是有观察证据的不新增行动决定，区别于模型的建议。')
    duties = ('合成服务对象的日常维护义务持续有效，该决定的权限效果为无，即不新增授权。'
        '观察到不新增行动决定，仍不能写成外部动作已获准或已执行。')
    body = section('observed-no-action', '建议与观察到的决定', judgment, [duties],
        bindings('action_ranking', 0, judgment, ['subject', 'scope.window', 'chosen_baseline', 'evidence_refs[0]'])
        + bindings('action_ranking', 1, duties, ['existing_items[0].condition',
            'existing_items[0].scope', 'permission_effect']))
    return projection('action_ranking', checked, [body]), checked, comparison, registry


def authorization_fixture():
    record, kwargs = authorization_inputs()
    replacements = {'actor-holder': '现场执行主体', 'actor-issuer': '独立授权主体',
        'actor-reviewer': '独立复核主体', 'actor-proposer': '试行提议主体',
        'synthetic-object': '合成服务对象', 'registered-team': '登记服务班组',
        'reversible-pilot': '有边界的可撤回试行'}

    def translate(value):
        if isinstance(value, dict):
            return {translate(key): translate(child) for key, child in value.items()}
        if isinstance(value, list):
            return [translate(child) for child in value]
        if isinstance(value, tuple):
            return tuple(translate(child) for child in value)
        return replacements.get(value, value) if isinstance(value, str) else value

    return translate(record), translate(kwargs)


def authorization_projection():
    record, kwargs = authorization_fixture()
    checked = choice.validate_external_selection(record, **kwargs)
    seam = {field: deepcopy(checked[field]) for field in
            ('status', 'selected_action', 'authorization_tuple_id', 'used_at')}
    judgment = ('本例的限定试行在登记范围内获准：决策主体是现场执行主体，'
        '目标仅为合成服务对象，单一动作仅为有边界的可撤回试行，地域仅为登记服务班组。')
    expiry = ('该原子授权从2026-09-30T00:00:00Z起生效，到2026-10-30T00:00:00Z止；'
        '本次使用时点为2026-10-01T00:00:00Z。越过对象、动作、地域或有效期都需要重新检查，'
        '已获准不代表执行成功、损害解除或补救完成。')
    body = section('atomic-authority', '单一授权范围和失效时间', judgment, [expiry],
        bindings('action_ranking', 0, judgment, ['status', 'selected_action.decision_subject',
            'selected_action.target_object', 'selected_action.single_action', 'selected_action.territory'])
        + bindings('action_ranking', 1, expiry, ['selected_action.validity_interval.starts_at',
            'selected_action.validity_interval.ends_at', 'used_at']))
    return projection('action_ranking', seam, [body]), checked, record, kwargs


def stopped_projection(executor, receipt):
    record = {'selection_id': executor.selection_id, 'status': 'authorized', 'history': [],
        'existing_obligations': [{'obligation_id': 'maintenance', 'condition': '日常维护义务持续有效'}],
        'open_harm_ids': ['尚未补救的合成损害'], 'open_appeal_ids': [],
        'open_remedy_ids': ['仍在进行的合成补救'], 'open_record_ids': []}
    checked = choice.transition_choice_state(record, 'stopped', at='2026-10-01T00:00:01Z',
        responsible_subject='现场执行主体', basis_refs=['合成停止回执'],
        executor_receipt=receipt, executor=executor)
    seam = {field: deepcopy(checked[field]) for field in
            ('status', 'permission_effect', 'existing_obligations', 'open_harm_ids', 'open_remedy_ids')}
    seam['history'] = [{'executor_receipt': {field: deepcopy(receipt[field]) for field in
        ('executor_status', 'reason', 'received_at', 'consequences')}}]
    judgment = '实际隔离执行器与选择状态都已停止，停止理由是保护先于动作，信号在2026-10-01T00:00:00Z送达。'
    duties = ('日常维护义务持续有效，尚未补救的合成损害和仍在进行的合成补救仍保持开放；'
        '权限效果为无，即不新增授权，停止后的后果仍未评估。停止动作不等于资源恢复或补救完成。')
    body = section('actual-stop', '真实停止与仍未履行的责任', judgment, [duties],
        bindings('action_ranking', 0, judgment, ['status', 'history[0].executor_receipt.executor_status',
            'history[0].executor_receipt.reason', 'history[0].executor_receipt.received_at'])
        + bindings('action_ranking', 1, duties, ['permission_effect', 'existing_obligations[0].condition',
            'open_harm_ids[0]', 'open_remedy_ids[0]', 'history[0].executor_receipt.consequences']))
    return projection('action_ranking', seam, [body]), checked


def endpoint_projection(supported_endpoints):
    names = ('safe_hearing', 'evidence_understood', 'authorized_decision_changed', 'resources_restored')
    references = {'safe_hearing': '安全听取记录', 'evidence_understood': '证据理解记录',
        'authorized_decision_changed': '授权决定变更记录', 'resources_restored': '资源恢复记录'}
    record = {f'{name}_claim_ids': [references[name]] if name in supported_endpoints else []
              for name in names}
    checked = judgment_boundaries.assess_correction_endpoints(record,
        claim_constraints=supported(*references.values()))
    paragraphs = [
        '安全听取这一终点有支持；它说明申诉已被安全接收，不能证明授权决定或资源已改变。'
        if 'safe_hearing' in supported_endpoints else
        '安全听取这一终点未获支持或仍未决；不能用其他纠正终点的成功代替安全接收证据。',
        '证据理解这一终点有支持；它说明材料已被理解，不能证明理解已改变决定或资源。'
        if 'evidence_understood' in supported_endpoints else
        '证据理解这一终点未获支持或仍未决；安全听取不能代替对材料的实际理解。',
        '授权决定改变这一终点有支持；仍需另行检查资源是否恢复。'
        if 'authorized_decision_changed' in supported_endpoints else
        '授权决定改变这一终点未获支持或仍未决；安全听取和证据理解不能代替有权限主体的真实变更。',
        '资源恢复这一终点有支持；其证据仅覆盖登记资源，其他损害仍需各自处置。'
        if 'resources_restored' in supported_endpoints else
        '资源恢复这一终点未获支持或仍未决；决定改变或停止动作都不能被写成补救已完成。',
    ]
    judgment = '纠正的四个终点逐项独立判断，不能相互代替。'
    source_bindings = [binding for index, (name, text) in enumerate(zip(names, paragraphs), 1)
                       for binding in bindings('verdict', index, text, [name])]
    body = section('correction-endpoints', '听取、理解、决定改变与资源恢复', judgment,
                   paragraphs, source_bindings)
    return projection('verdict', checked, [body]), checked
