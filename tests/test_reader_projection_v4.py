from copy import deepcopy
from pathlib import Path
import json
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from xi_kari_runtime import domains, prose
from xi_kari_runtime import coverage as coverage_api
from xi_kari_runtime.canonical_json import sha256_file
from xi_kari_runtime.coverage import build_semantic_coverage
from xi_kari_runtime.semantic_projection import (
    authored_reader_units,
    reader_projection_units, semantic_projection_units,
    semantic_atom_paths, substantive_semantic_atoms, typed_semantic_atoms,
    validate_reader_sections, validate_visibility_ledger,
)


@pytest.fixture
def domain_trace(tmp_path):
    repository = tmp_path / 'domain-repository'
    for relative in (
        'references/source/v9.0/source-manifest.json',
        'references/source/v9.0/indexes/anchors.json',
        'references/source/v9.0/indexes/body-blocks.json',
        'references/ontology/v9.0/authored/domain-identities.json',
    ):
        destination = repository / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    shutil.copytree(ROOT / 'references/learning-packs/domains',
                    repository / 'references/learning-packs/domains')
    catalog = json.loads((ROOT / 'references/domains/index.json').read_text(encoding='utf-8'))
    for entry in catalog['entries']:
        relative = f"references/learning-packs/domains/{entry['domain_id']}.md"
        entry.update(content_status='available', content_path=relative,
                     content_sha256=sha256_file(repository / relative),
                     read_trace_status='requires_run_trace')
    index = repository / 'references/domains/index.json'
    index.parent.mkdir(parents=True, exist_ok=True)
    index.write_text(json.dumps(catalog, ensure_ascii=False), encoding='utf-8')
    plan = domains.build_domain_read_plan(repository, domain_ids=['D.04'],
        problem_contract_sha256='1' * 64, run_id='reader-domain', challenge='2' * 64)
    controlled = plan['records'][0]
    raw = domains.read_domain_item_bytes(repository, controlled)
    semantic = {
        'domain_id': 'D.04',
        'content_witness': domains.domain_content_witness(plan, controlled, raw),
        'content_excerpt': next(line for line in raw.decode('utf-8').splitlines()
                                if line and not line.startswith('#')),
        'problem_relation': {'status': 'native_exit', 'rationale': '本题的有限观测已由领域方法回答。'},
        'reader_responsibilities': {
            'native_method': '原生观测方法已经回答当前目标。',
            'additional_distinction': '目标可观测不等于全状态已重建。',
            'inputs_outputs': '观测只支持声明的有限输出。',
            'limits_counterargument': '同一输出仍可能对应不同隐藏状态。',
            'costs_exit': '追加重建会增加成本，目标任务完成时可以退出。',
        },
    }
    trace = domains.build_domain_read_trace(repository, plan, [semantic])
    domains.validate_domain_read_trace(repository, plan, trace)
    return trace


def visibility(payload):
    payload['visibility_ledger'] = {'entries': [
        {'canonical_path': path, 'classification': 'public', 'disclosure': 'include',
         'purpose': 'reader projection', 'authority_refs': [], 'protection_reason': None}
        for path in semantic_atom_paths(payload)
    ]}
    return payload


def test_actual_domain_trace_requires_visibility_for_its_cost_and_exit(domain_trace):
    payload = {'schema_version': 4, 'domain_read_trace': domain_trace}
    path = 'domain_read_trace.records[0].reader_responsibilities.costs_exit'
    assert path in semantic_atom_paths(payload)
    visibility(payload)
    payload['visibility_ledger']['entries'] = [entry for entry in payload['visibility_ledger']['entries']
                                               if entry['canonical_path'] != path]
    with pytest.raises(ValueError, match='missing semantic atom'):
        validate_visibility_ledger(payload)


def domain_body(trace):
    responsibilities = trace['records'][0]['reader_responsibilities']
    paragraphs = {
        'answer.direct_answer': '当前材料可以支持有限输出，其余状态保持未知。',
        'domain_read_trace.records[0].problem_relation.status': '本题由领域方法独立完成',
        'domain_read_trace.records[0].problem_relation.rationale': '本题的有限观测已由领域方法回答。',
        **{f'domain_read_trace.records[0].reader_responsibilities.{field}': value
           for field, value in responsibilities.items()},
    }
    payload = {'schema_version': 4, 'domain_read_trace': trace,
               'answer': {'direct_answer': paragraphs['answer.direct_answer']},
               'reader_sections': [
        {'section_id': f'domain-{number}', 'heading': '有限观测的依据和边界',
         'local_judgment': text, 'paragraphs': ['这一条件约束了本题可以成立的判断范围。'],
         'source_bindings': [{'source_path': path, 'paragraph_index': 0, 'excerpt': text}]}
        for number, (path, text) in enumerate(paragraphs.items())
    ]}
    return visibility(payload)


def semantic_coverage(payload, outputs=None):
    return build_semantic_coverage(run_id='reader-v4', packet=payload,
        source_read_complete=True, candidate_closure_complete=True,
        reader_outputs=outputs if outputs is not None else prose.render_reader_outputs(payload))


def test_v4_domain_body_uses_native_exit_without_demanding_a_formal_instance(domain_trace):
    payload = domain_body(domain_trace)
    assert validate_reader_sections(payload) == []
    assert semantic_coverage(payload)['main_answer_complete']
    answer = prose.render_answer(payload)
    for text in domain_trace['records'][0]['reader_responsibilities'].values():
        assert text in answer
    assert '追加重建会增加成本' in answer
    assert prose.render_chat_projection(payload) == answer
    assert all('content_witness' not in path and not path.endswith('_sha256')
               for path in semantic_atom_paths(payload))


def test_v4_missing_body_reports_gaps_without_legacy_global_applicability(domain_trace):
    payload = domain_body(domain_trace)
    payload['reader_sections'] = payload['reader_sections'][:-1]
    answer = prose.render_answer(payload)
    assert any('costs_exit' in error for error in prose.reader_contract_gaps(payload, answer))
    assert not semantic_coverage(payload)['main_answer_complete']


def protect(payload, path):
    entry = next(entry for entry in payload['visibility_ledger']['entries']
                 if entry['canonical_path'] == path)
    entry.update(classification='sensitive', disclosure='withhold',
                 authority_refs=['privacy-contract'], protection_reason='未取得当事人披露同意')


@pytest.mark.parametrize('renderer', [
    prose.render_answer, prose.render_chat_projection, prose.render_dossier,
    prose.render_atlas, prose.render_casebook,
])
def test_protected_domain_value_cannot_be_copied_into_a_public_closing(domain_trace, renderer):
    payload = domain_body(domain_trace)
    value = domain_trace['records'][0]['reader_responsibilities']['costs_exit']
    payload['reader_sections'] = payload['reader_sections'][:-1]
    payload['answer']['closing'] = '目前仍需考虑：' + value
    visibility(payload)
    protect(payload, 'domain_read_trace.records[0].reader_responsibilities.costs_exit')
    with pytest.raises(ValueError) as caught:
        renderer(payload)
    assert value not in str(caught.value)


def test_unknown_source_binding_diagnostics_do_not_echo_protected_values(domain_trace):
    payload = domain_body(domain_trace)
    value = domain_trace['records'][0]['reader_responsibilities']['costs_exit']
    payload['reader_sections'] = payload['reader_sections'][:-1]
    protect(payload, 'domain_read_trace.records[0].reader_responsibilities.costs_exit')
    payload['reader_sections'][0]['source_bindings'].append(
        {'source_path': value, 'paragraph_index': 0, 'excerpt': '非法路径'})
    errors = validate_reader_sections(payload)
    assert errors
    assert value not in '\n'.join(errors)


def test_dangling_visibility_diagnostics_do_not_echo_protected_values(domain_trace):
    payload = domain_body(domain_trace)
    value = domain_trace['records'][0]['reader_responsibilities']['costs_exit']
    payload['reader_sections'] = payload['reader_sections'][:-1]
    protect(payload, 'domain_read_trace.records[0].reader_responsibilities.costs_exit')
    entry = deepcopy(payload['visibility_ledger']['entries'][0])
    entry['canonical_path'] = value
    payload['visibility_ledger']['entries'].append(entry)
    with pytest.raises(ValueError) as caught:
        prose.render_answer(payload)
    assert value not in str(caught.value)


def test_protected_numeric_forecast_value_cannot_be_copied_into_a_public_summary():
    payload = visibility({'schema_version': 4,
        'forecast': {'expression': {'kind': 'conditional_model', 'value': 0.742938}},
        'answer': {'direct_answer': '私密模型输出不能作为公开结果。',
                   'closing': '模型给出的数值是0.742938。'}, 'reader_sections': []})
    protect(payload, 'forecast.expression.value')
    with pytest.raises(ValueError) as caught:
        prose.render_chat_projection(payload)
    assert '0.742938' not in str(caught.value)


def test_v4_protected_responsibility_requires_a_safe_bound_body_boundary(domain_trace):
    payload = domain_body(domain_trace)
    payload['reader_sections'] = payload['reader_sections'][:-1]
    path = 'domain_read_trace.records[0].reader_responsibilities.costs_exit'
    protect(payload, path)
    assert any(path in error for error in validate_reader_sections(payload))
    report = semantic_coverage(payload)
    assert not report['main_answer_complete']
    assert path in report['substantive_unprojected_paths']


def test_safe_withholding_boundary_preserves_identity_without_disclosing_the_value(domain_trace):
    payload = domain_body(domain_trace)
    path = 'domain_read_trace.records[0].reader_responsibilities.costs_exit'
    protect(payload, path)
    section = payload['reader_sections'][-1]
    boundary = '有关成本与退出的细节暂不披露，原因是未取得当事人披露同意。'
    section.update(local_judgment=boundary,
        paragraphs=['当前判断因此保留负担比较的限制，后续需要在授权范围内核验。'],
        source_bindings=[{'source_path': path, 'paragraph_index': 0, 'excerpt': boundary}])
    assert validate_reader_sections(payload) == []
    answer = prose.render_answer(payload)
    assert boundary in answer
    assert domain_trace['records'][0]['reader_responsibilities']['costs_exit'] not in answer
    report = semantic_coverage(payload)
    assert report['main_answer_complete']
    atom = next(item for item in report['typed_atom_ledger'] if item['canonical_path'] == path)
    assert atom['projection_status'] == 'withheld_for_protection'
    assert atom['reader_unit_ids']


def test_full_chat_accepts_the_same_safe_withholding_text_as_the_full_file(domain_trace):
    payload = domain_body(domain_trace)
    path = 'domain_read_trace.records[0].reader_responsibilities.costs_exit'
    protect(payload, path)
    boundary = '有关成本的细节为保护而不公开（未取得当事人披露同意）。'
    payload['reader_sections'][-1].update(local_judgment=boundary,
        source_bindings=[{'source_path': path, 'paragraph_index': 0, 'excerpt': boundary}])
    full = prose.render_answer(payload)
    assert prose.render_chat_projection(payload) == full


def checked_empirical_projection_input():
    from tests.test_causal_judgment_v4_graph import empirical_graph
    from tests.test_causal_judgment_instances import root_contract, root_result
    from xi_kari_runtime.empirical_instances import EvaluatedInstanceRegistry, freeze_empirical_instance

    graph = empirical_graph()
    preregistration, evaluation = root_contract(), root_result()
    evaluation.update(evidence_claim_ids=['CLAIM-FACTUAL'], analysis_artifact_claim_ids=['CLAIM-FACTUAL'],
        prerequisite_claim_ids={key: ['CLAIM-FACTUAL'] for key in evaluation['prerequisite_claim_ids']},
        null_gate_claim_ids={key: ['CLAIM-FACTUAL'] for key in evaluation['null_gate_claim_ids']},
        dimension_claim_ids={'delay': ['CLAIM-FACTUAL']})
    registry = EvaluatedInstanceRegistry(
        [{'frozen': freeze_empirical_instance(preregistration), 'evaluation': evaluation}], graph=graph)
    return preregistration, evaluation, registry


def test_code_rebuilt_empirical_inputs_and_results_require_visibility_and_body_bindings():
    preregistration, evaluation, registry = checked_empirical_projection_input()
    payload = {'schema_version': 4,
        'empirical_instances': [{'preregistration': preregistration, 'evaluation': evaluation}],
        'formal_results': {'source_version': 'v9.0', 'source_revision': 'a' * 64,
            'claim_input_sha256': registry.graph_sha256, 'instance_inputs_sha256': registry.inputs_sha256,
            'instance_results': dict(registry)},
        'reader_sections': [{'section_id': 'ordinary', 'heading': '普通结论的范围',
            'local_judgment': '观测支持有限结果。',
            'paragraphs': ['它没有替代正式实例的逐项责任。'], 'source_bindings': []}]}
    paths = set(semantic_atom_paths(payload))
    required = {
        'empirical_instances[0].preregistration.selected_success_criterion',
        'empirical_instances[0].evaluation.metrics.controlled_perturbation_effect',
        'formal_results.instance_results[0].qualification',
        'formal_results.instance_results[0].result.result_state',
        'formal_results.instance_results[0].result.observed_primary_result',
    }
    assert required <= paths
    assert not any(path.endswith(('_hash', '_sha256', '.source_revision')) for path in paths)
    visibility(payload)
    validate_visibility_ledger(payload)
    errors = validate_reader_sections(payload)
    assert all(any(path in error for error in errors) for path in required)
    payload['visibility_ledger']['entries'] = [entry for entry in payload['visibility_ledger']['entries']
        if entry['canonical_path'] != 'formal_results.instance_results[0].qualification']
    with pytest.raises(ValueError, match='missing semantic atom'):
        prose.render_answer(payload)


def test_domain_responsibility_units_preserve_costs_and_counterarguments(domain_trace):
    payload = domain_body(domain_trace)
    path = 'domain_read_trace.records[0].reader_responsibilities.costs_exit'
    units = reader_projection_units(payload)
    text = '\n'.join(fragment for unit in units for fragment in unit['fragments'])
    assert '追加重建会增加成本，目标任务完成时可以退出。' in text
    assert '同一输出仍可能对应不同隐藏状态。' in text
    assert path in {path for unit in units for path in unit['source_paths']}
    audit_units = semantic_projection_units(payload)
    assert path in {atom['canonical_path'] for unit in audit_units for atom in unit['atoms']}


def test_typed_protection_text_cannot_repeat_a_private_numeric_value():
    payload = visibility({'schema_version': 4, 'forecast': {'private_metric': 0.742938}})
    protect(payload, 'forecast.private_metric')
    payload['visibility_ledger']['entries'][0]['protection_reason'] = '私密估计0.742938未授权披露'
    with pytest.raises(ValueError) as caught:
        typed_semantic_atoms(payload)
    assert '0.742938' not in str(caught.value)


def test_six_stage_applicability_preserves_mechanism_analysis_despite_a_legacy_global_flag():
    from tests.test_p04_v4_claim_contracts import _v4_graph
    from xi_kari_runtime.claims import validate_claim_graph
    graph = validate_claim_graph(_v4_graph(), repository_root=ROOT)
    payload = visibility({'schema_version': 4, 'dynamic_applicability': 'not_applicable',
        'applicability': graph['applicability'], 'claim_mechanism_graph': graph})
    name = graph['mechanisms'][0]['name']
    assert name in prose.render_atlas(payload)


def test_per_stage_recursion_reason_is_used_instead_of_a_global_default():
    payload = visibility({'schema_version': 4, 'applicability': {
        'recursion': {'status': 'not_applicable', 'rationale': '本题已经由静态文本对照回答。'}},
        'reader_sections': []})
    text = prose.render_atlas(payload)
    assert '三阶推演不适用' in text
    assert '本题已经由静态文本对照回答。' in text


def test_safe_wording_cannot_hide_a_copied_private_value_in_authored_units(domain_trace):
    payload = domain_body(domain_trace)
    path = 'domain_read_trace.records[0].reader_responsibilities.costs_exit'
    private = domain_trace['records'][0]['reader_responsibilities']['costs_exit']
    protect(payload, path)
    unsafe = private + '该信息暂不披露，原因是未取得当事人披露同意。'
    payload['reader_sections'][-1].update(local_judgment=unsafe,
        source_bindings=[{'source_path': path, 'paragraph_index': 0, 'excerpt': unsafe}])
    errors = validate_reader_sections(payload)
    assert errors
    assert private not in '\n'.join(errors)
    with pytest.raises(ValueError) as caught:
        authored_reader_units(payload)
    assert private not in str(caught.value)


def test_a_negated_qualification_does_not_preserve_the_code_rebuilt_positive_status():
    preregistration, _, registry = checked_empirical_projection_input()
    identifier = preregistration['instance_id']
    qualification = registry[identifier]['qualification']
    assert qualification == 'qualified'
    path = 'formal_results.instance_results[0].qualification'
    text = '这项实例尚未取得资格。'
    payload = visibility({'schema_version': 4,
        'formal_results': {'instance_results': {identifier: {'qualification': qualification}}},
        'reader_sections': [{'section_id': 'qualification', 'heading': '资格的状态',
            'local_judgment': text, 'paragraphs': ['资格与具体结果分别核验。'],
            'source_bindings': [{'source_path': path, 'paragraph_index': 0, 'excerpt': text}]}]})
    assert any(path in error for error in validate_reader_sections(payload))
    valid = '这项实例已取得资格，但资格本身不能代替具体结果。'
    payload['reader_sections'][0].update(local_judgment=valid,
        source_bindings=[{'source_path': path, 'paragraph_index': 0, 'excerpt': valid}])
    assert validate_reader_sections(payload) == []


@pytest.fixture(scope='module')
def source_locks():
    from xi_kari_runtime.retrieval import build_full_source_lock
    return {version: build_full_source_lock(ROOT, run_id='reader-source-' + version,
                                           source_version=version)[0]
            for version in ('v8.3', 'v9.0')}


def test_production_v4_coverage_uses_the_actual_v9_source_lock(source_locks):
    lock = source_locks['v9.0']
    before = deepcopy(lock)
    result = coverage_api.build_coverage_v4(run_id=lock['run_id'], source_lock=lock,
        retrieval_index={'sources': [], 'source_count': 0, 'all_sources_assessed': True},
        evidence_ledger={'claims': [], 'unsupported_claims': []})
    assert result['schema_id'] == 'xi-kari.v4.coverage'
    assert result['schema_version'] == 4
    assert result['source_read']['source_units_expected'] == 4418
    assert result['source_read']['source_units_observed'] == 4418
    assert result['source_read']['expected'] == result['source_read']['observed'] == 21
    assert result['source_read']['complete'] is True
    assert result['complete'] is True
    assert coverage_api.validate_coverage(result) == []
    assert lock == before


@pytest.mark.parametrize('mutation', ['source', 'revision', 'unit-count', 'reader-count', 'receipt', 'source-count', 'assessment', 'output'])
def test_production_v4_coverage_does_not_claim_incomplete_or_mixed_inputs(source_locks, mutation):
    lock = deepcopy(source_locks['v9.0'])
    retrieval = {'sources': [], 'source_count': 0, 'all_sources_assessed': True}
    outputs = coverage_api.REQUIRED_OUTPUTS
    if mutation == 'source':
        lock = deepcopy(source_locks['v8.3'])
    elif mutation == 'revision':
        lock['source_raw_sha256'] = '0' * 64
    elif mutation == 'unit-count':
        lock['source_unit_count'] = 4753
    elif mutation == 'reader-count':
        lock['reader_receipts'].pop()
        lock['reader_unit_count'] -= 1
    elif mutation == 'receipt':
        lock['reader_receipts'][0]['observed_sha256'] = '0' * 64
    elif mutation == 'source-count':
        retrieval['source_count'] = 1
    elif mutation == 'assessment':
        retrieval['all_sources_assessed'] = False
    elif mutation == 'output':
        outputs = ('answer',)
    result = coverage_api.build_coverage_v4(run_id=lock['run_id'], source_lock=lock,
        retrieval_index=retrieval, evidence_ledger={'claims': [], 'unsupported_claims': []},
        planned_outputs=outputs)
    assert result['complete'] is False
    assert coverage_api.validate_coverage(result)


def test_legacy_source_coverage_remains_explicitly_bound_to_its_actual_lock(source_locks):
    lock = source_locks['v8.3']
    result = coverage_api.build_coverage(run_id=lock['run_id'], source_lock=lock,
        retrieval_index={'sources': [], 'source_count': 0, 'all_sources_assessed': True},
        evidence_ledger={'claims': [], 'unsupported_claims': []})
    assert result['schema_version'] == 3
    assert result['source_read']['source_units_expected'] == 4753
    assert result['complete'] is True
    assert coverage_api.validate_coverage(result) == []
