from copy import deepcopy
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from tests.reader_projection_v4_judgment_data import (
    BOUNDARY, authorization_projection, comparison_projection, conditional_projection,
    endpoint_projection, frequency_projection, interval_projection, nonprobability_projection,
    observed_no_action_projection, stopped_projection, unknown_projection,
)
from xi_kari_runtime import choice, forecasting, prose
from xi_kari_runtime.coverage import build_semantic_coverage
from xi_kari_runtime.semantic_projection import (
    substantive_semantic_atoms, typed_semantic_atoms, validate_reader_sections,
    validate_visibility_ledger,
)


def coverage(payload, outputs=None):
    return build_semantic_coverage(run_id='synthetic-reader-judgment', packet=payload,
        source_read_complete=False, candidate_closure_complete=False,
        reader_outputs=prose.render_reader_outputs(payload) if outputs is None else outputs)


def assert_complete_body(payload):
    validate_visibility_ledger(payload)
    assert validate_reader_sections(payload) == []
    result = coverage(payload)
    assert result['main_answer_complete'] is True
    assert result['reader_projection_complete'] is True
    assert result['source_read_complete'] is False
    assert result['candidate_closure_complete'] is False
    assert result['substantive_unprojected_paths'] == []
    assert prose.render_chat_projection(payload) == prose.render_answer(payload)


@pytest.mark.parametrize('factory', [
    unknown_projection, frequency_projection, conditional_projection, interval_projection,
    comparison_projection, observed_no_action_projection, authorization_projection,
])
def test_checked_judgment_records_have_complete_authored_bodies(factory):
    payload = factory()[0]
    assert_complete_body(payload)


@pytest.mark.parametrize('kind,expected_identity', [
    ('subjective_belief', '主观信念'),
    ('decision_weight', '决策权重'),
    ('computation_priority', '计算优先级'),
])
def test_nonprobability_types_are_visible_without_becoming_reality_probability(kind, expected_identity):
    payload, checked = nonprobability_projection(kind)
    assert checked['kind'] == kind
    assert 'numeric_probability' not in checked
    assert 'calibration' not in checked
    atoms = {atom['canonical_path']: atom for atom in typed_semantic_atoms(payload)}
    assert atoms['forecast.kind']['value_type'] == 'enum'
    assert atoms['forecast.kind']['public_text'].endswith('：' + expected_identity)
    assert_complete_body(payload)
    answer = prose.render_answer(payload)
    assert expected_identity in answer
    assert '不能' in answer
    if kind == 'decision_weight':
        assert '现实事件发生概率' in answer
    forged = deepcopy(checked)
    forged['numeric_probability'] = 0.8
    with pytest.raises(forecasting.ForecastError):
        forecasting.validate_probability_expression(forged, claim_constraints={})


def test_empirical_ratio_model_probability_and_interval_keep_distinct_numeric_atoms():
    empirical, empirical_checked, _ = frequency_projection()
    conditional, conditional_checked = conditional_projection()
    interval, interval_checked = interval_projection()
    expected = [
        (empirical, '经验频率', {'forecast.value': 2 / 3, 'forecast.sample_size': 3,
                              'forecast.positive_outcomes': 2}),
        (conditional, '条件模型', {'forecast.value': 4 / 7, 'forecast.prior.alpha': 2,
                                'forecast.data.sample_size': 3}),
        (interval, '概率区间', {'forecast.lower': 0.2, 'forecast.upper': 0.8,
                            'forecast.level': 0.9}),
    ]
    assert empirical_checked['kind'] == 'empirical_frequency'
    assert conditional_checked['probability_scope'] == 'model_conditional'
    assert interval_checked['base_expression']['kind'] == 'conditional_model'
    for payload, kind_label, fields in expected:
        atoms = {atom['canonical_path']: atom for atom in typed_semantic_atoms(payload)}
        substantive = {atom['canonical_path'] for atom in substantive_semantic_atoms(payload)}
        assert atoms['forecast.kind']['public_text'].endswith('：' + kind_label)
        for path, value in fields.items():
            assert atoms[path]['value_type'] == 'number'
            assert atoms[path]['public_text'].endswith('：' + str(value))
            assert path in substantive
        assert 'forecast.calibration.status' in substantive
        assert_complete_body(payload)


def test_unknown_expression_from_frozen_forecast_has_no_invented_number_or_direction():
    payload, frozen = unknown_projection()
    assert frozen['contract']['expression']['kind'] == 'unknown'
    assert frozen['evaluations'] == []
    assert frozen['contract']['parent_state_diff_id'] == 'synthetic-diff-1'
    substantive = {atom['canonical_path'] for atom in substantive_semantic_atoms(payload)}
    assert substantive >= {'forecast.kind', 'forecast.reason', 'forecast.minimal_observations[0]'}
    assert 'forecast.value' not in substantive
    assert 'forecast.direction' not in substantive
    assert_complete_body(payload)
    assert '未知不能被改写为方向、数值概率或执行许可' in prose.render_answer(payload)


@pytest.mark.parametrize('status,label', [
    ('not_tested', '尚未检验'), ('insufficient', '证据不足'), ('evaluated', '已评估'),
])
def test_calibration_status_and_evidence_survive_body_and_coverage(status, label):
    payload, checked, constraints = frequency_projection(status)
    assert checked['calibration']['status'] == status
    assert_complete_body(payload)
    assert label in prose.render_answer(payload)
    if status == 'evaluated':
        assert checked['calibration']['result_claim_ids'] == ['独立结果校准记录']
        unsupported = deepcopy(constraints)
        unsupported['独立结果校准记录']['blocked'] = True
        with pytest.raises(forecasting.ForecastError, match='basis'):
            forecasting.validate_probability_expression(checked, claim_constraints=unsupported)
    else:
        assert checked['calibration']['reason'] in prose.render_answer(payload)


@pytest.mark.parametrize('factory,path', [
    (frequency_projection, 'forecast.calibration.status'),
    (conditional_projection, 'forecast.probability_scope'),
    (interval_projection, 'forecast.interpretation'),
    (comparison_projection, 'action_ranking.existing_items[0].condition'),
    (authorization_projection, 'action_ranking.selected_action.validity_interval.ends_at'),
])
def test_judgment_visibility_requires_every_calibration_duty_and_scope_atom(factory, path):
    payload = factory()[0]
    payload['visibility_ledger']['entries'] = [entry for entry in payload['visibility_ledger']['entries']
                                               if entry['canonical_path'] != path]
    with pytest.raises(ValueError, match='missing semantic atom'):
        validate_visibility_ledger(payload)


@pytest.mark.parametrize('factory,path', [
    (frequency_projection, 'forecast.sample_size'),
    (frequency_projection, 'forecast.calibration.reason'),
    (conditional_projection, 'forecast.probability_scope'),
    (conditional_projection, 'forecast.prior.basis_claim_ids[0]'),
    (interval_projection, 'forecast.interpretation'),
    (comparison_projection, 'action_ranking.cost_distribution[1].cost'),
    (comparison_projection, 'action_ranking.counterarguments[0]'),
    (comparison_projection, 'action_ranking.switch_conditions[0]'),
    (observed_no_action_projection, 'action_ranking.existing_items[0].condition'),
    (authorization_projection, 'action_ranking.selected_action.territory'),
    (authorization_projection, 'action_ranking.selected_action.validity_interval.ends_at'),
])
def test_judgment_atom_cannot_disappear_from_binding_while_other_atoms_remain(factory, path):
    payload = factory()[0]
    for body in payload['reader_sections']:
        body['source_bindings'] = [binding for binding in body['source_bindings']
                                   if binding['source_path'] != path]
    errors = validate_reader_sections(payload)
    assert any(path in error and 'absent from the body' in error for error in errors)
    result = coverage(payload)
    assert result['main_answer_complete'] is False
    assert path in result['substantive_unprojected_paths']


def test_equal_numbers_cannot_replace_subjective_belief_identity_with_reality_probability():
    payload, _ = nonprobability_projection('subjective_belief')
    body = payload['reader_sections'][1]
    body['local_judgment'] = '现实事件发生概率为0.8，已有可靠校准。'
    body['paragraphs'] = ['这一概率数值足以支持马上执行。']
    for binding in body['source_bindings']:
        binding.update(paragraph_index=0, excerpt=body['local_judgment'])
    errors = validate_reader_sections(payload)
    assert any('forecast.kind' in error for error in errors)
    assert any('forecast.subject' in error for error in errors)
    assert coverage(payload)['main_answer_complete'] is False


def test_recommendation_observed_no_action_and_external_selection_remain_distinct():
    recommended, comparison, state = comparison_projection()
    observed, decision, _, registry = observed_no_action_projection()
    selected, authorized, _, _ = authorization_projection()
    assert state['existing_obligations'] == comparison['existing_items'] == decision['existing_items']
    assert comparison['options'][0]['option_kind'] == 'no_action'
    assert comparison['execution_status'] == 'analysis_only'
    assert comparison['permission_effect'] == decision['permission_effect'] == 'none'
    assert 'selected_action' not in comparison and 'selected_action' not in decision
    assert registry['合成会议观察记录']['identity'] == 'observed'
    assert authorized['status'] == 'authorized'
    assert authorized['selected_action']['option_id'] == 'PILOT'
    original = deepcopy(comparison)
    for payload in (recommended, observed, selected):
        assert_complete_body(payload)
    assert comparison == original
    assert choice.validate_action_comparison(comparison, action_state=state,
        claim_constraints={'本轮规范依据': {'blocked': False}})['permission_effect'] == 'none'
    registry['合成会议观察记录']['identity'] = 'model-candidate'
    with pytest.raises(choice.ChoiceError, match='decision evidence'):
        choice.validate_no_new_action_choice(decision, comparison=comparison,
                                            decision_evidence_registry=registry)


def test_full_answer_keeps_both_costs_opposition_and_switch_conditions_as_prose():
    payload, _, _ = comparison_projection()
    assert_complete_body(payload)
    answer = prose.render_answer(payload)
    for sentence in (
        '服务使用者承担持续等待成本，维护人员承担监测和维护人力成本',
        '最强反对意见是继续等待可能延长受损',
        '登记比较支持试行且停止机制仍可用时，应切换建议',
        '不新增行动不能免除原有职责',
    ):
        assert sentence in answer
        assert sentence in prose.render_chat_projection(payload)
    assert '详见附件' not in answer and '覆盖标记' not in answer


@pytest.mark.parametrize('substitute', ['详见附件', '覆盖标记'])
def test_appendix_or_marker_cannot_replace_costs_in_the_main_answer(substitute):
    payload, _, _ = comparison_projection()
    body = payload['reader_sections'][1]
    body['paragraphs'][2] = substitute
    for binding in body['source_bindings']:
        if binding['paragraph_index'] == 3:
            binding['excerpt'] = substitute
    outputs = prose.render_reader_outputs(payload)
    outputs['dossier'] += '\n服务使用者承担持续等待成本，维护人员承担监测和维护人力成本。\n'
    errors = validate_reader_sections(payload)
    assert any('summary or appendix substitution' in error for error in errors)
    assert coverage(payload, outputs)['main_answer_complete'] is False


@pytest.mark.parametrize('change', ['holder', 'object', 'action', 'territory', 'expiry'])
def test_atomic_scope_changes_or_expiry_block_real_executor_despite_complete_prose(tmp_path, change):
    payload, checked, record, kwargs = authorization_projection()
    assert_complete_body(payload)
    assert checked['authorization_tuple_id'] == 'J-1'
    invalid = deepcopy(kwargs)
    atom = invalid['authorization_registry']['J-1']
    if change == 'expiry':
        invalid['used_at'] = atom['validity_interval']['ends_at']
    else:
        field = {'holder': 'decision_subject', 'object': 'target_object',
                 'action': 'single_action', 'territory': 'territory'}[change]
        atom[field] = '另一独立授权范围'
    artifact = tmp_path / 'bounded-action.txt'
    executor = choice.IsolatedChoiceExecutor(record['selection_id'],
        {'PILOT': lambda: artifact.write_text('applied', encoding='utf-8')},
        authorizer=lambda option: choice.validate_external_selection(record, **invalid))
    with pytest.raises(choice.ChoiceError):
        executor.execute('PILOT')
    assert not artifact.exists()
    assert executor.executed_option_ids == []


def test_actual_stop_prevents_isolated_action_and_retains_open_duties(tmp_path):
    _, _, selection, kwargs = authorization_projection()
    artifact = tmp_path / 'bounded-action.txt'
    executor = choice.IsolatedChoiceExecutor(selection['selection_id'],
        {'PILOT': lambda: artifact.write_text('applied', encoding='utf-8')},
        authorizer=lambda option: choice.validate_external_selection(selection, **kwargs))
    receipt = executor.stop('保护先于动作', received_at='2026-10-01T00:00:00Z')
    assert receipt['stop_reached_executor'] is True
    assert receipt['before_any_execution'] is True
    assert executor.validates_stop(receipt)
    with pytest.raises(choice.ChoiceError, match='stopped'):
        executor.execute('PILOT')
    assert not artifact.exists()
    payload, stopped = stopped_projection(executor, receipt)
    assert stopped['existing_obligations'][0]['condition'] == '日常维护义务持续有效'
    assert stopped['open_harm_ids'] == ['尚未补救的合成损害']
    assert stopped['open_remedy_ids'] == ['仍在进行的合成补救']
    assert_complete_body(payload)
    with pytest.raises(choice.ChoiceError, match='open'):
        choice.transition_choice_state(stopped, 'closed', at='2026-10-01T00:00:02Z',
            responsible_subject='现场执行主体', basis_refs=['合成关闭建议'])
    with pytest.raises(choice.ChoiceError, match='actual executor'):
        choice.transition_choice_state({'selection_id': selection['selection_id'],
            'status': 'authorized', 'history': []}, 'stopped', at='2026-10-01T00:00:01Z',
            responsible_subject='现场执行主体', basis_refs=['复制的停止标记'], executor_receipt=receipt)


@pytest.mark.parametrize('supported_names', [
    ('safe_hearing', 'evidence_understood'),
    ('safe_hearing', 'evidence_understood', 'authorized_decision_changed'),
    ('safe_hearing', 'evidence_understood', 'authorized_decision_changed', 'resources_restored'),
])
def test_four_correction_endpoints_project_their_own_evidence_and_unknowns(supported_names):
    payload, checked = endpoint_projection(supported_names)
    assert set(checked) == {'safe_hearing', 'evidence_understood',
                            'authorized_decision_changed', 'resources_restored'}
    for name, status in checked.items():
        assert status == ('supported' if name in supported_names else 'unsupported_or_undecided')
    assert_complete_body(payload)
    assert '不能相互代替' in prose.render_answer(payload)


@pytest.mark.parametrize('name', [
    'safe_hearing', 'evidence_understood', 'authorized_decision_changed', 'resources_restored',
])
def test_other_correction_successes_cannot_cover_an_omitted_endpoint(name):
    payload, _ = endpoint_projection(('safe_hearing', 'evidence_understood',
        'authorized_decision_changed', 'resources_restored'))
    path = 'verdict.' + name
    body = payload['reader_sections'][1]
    body['source_bindings'] = [binding for binding in body['source_bindings']
                               if binding['source_path'] != path]
    errors = validate_reader_sections(payload)
    assert any(path in error for error in errors)
    assert coverage(payload)['main_answer_complete'] is False


def test_protected_subjective_number_requires_a_safe_bound_body_boundary():
    payload, checked = nonprobability_projection('subjective_belief', protected=True)
    assert checked['value'] == 0.8
    assert_complete_body(payload)
    result = coverage(payload)
    atom = next(item for item in result['typed_atom_ledger']
                if item['canonical_path'] == 'forecast.value')
    assert atom['projection_status'] == 'withheld_for_protection'
    assert atom['reader_unit_ids']
    assert BOUNDARY in prose.render_answer(payload)
    assert '0.8' not in prose.render_answer(payload)
    body = payload['reader_sections'][1]
    body['paragraphs'] = ['其余信息仍只说明谁在何时持有何种信念。']
    body['source_bindings'] = [binding for binding in body['source_bindings']
                               if binding['source_path'] != 'forecast.value']
    assert any('forecast.value' in error for error in validate_reader_sections(payload))
    assert coverage(payload)['main_answer_complete'] is False


@pytest.mark.parametrize('renderer', [prose.render_answer, prose.render_chat_projection])
def test_protected_numeric_value_cannot_return_through_an_unbound_paragraph(renderer):
    payload, _ = nonprobability_projection('subjective_belief', protected=True)
    payload['reader_sections'][1]['paragraphs'].append('补充：原始信念数值为0.8。')
    with pytest.raises(ValueError) as caught:
        renderer(payload)
    assert '0.8' not in str(caught.value)
