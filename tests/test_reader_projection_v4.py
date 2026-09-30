from copy import deepcopy
from pathlib import Path
import json
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from xi_kari_runtime import domains, prose
from xi_kari_runtime.canonical_json import sha256_file
from xi_kari_runtime.coverage import build_semantic_coverage
from xi_kari_runtime.semantic_projection import (
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
