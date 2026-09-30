from copy import deepcopy
from pathlib import Path
import json
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from xi_kari_runtime import claims
from xi_kari_runtime.empirical_instances import EvaluatedInstanceRegistry, freeze_empirical_instance
from tests.test_causal_judgment_instances import root_contract, root_result
from tests.test_causal_judgment_v4_graph import empirical_graph


def instance_inputs():
    evaluation = root_result()
    evaluation.update(
        evidence_claim_ids=['CLAIM-FACTUAL'], analysis_artifact_claim_ids=['CLAIM-FACTUAL'],
        prerequisite_claim_ids={key: ['CLAIM-FACTUAL'] for key in evaluation['prerequisite_claim_ids']},
        dimension_claim_ids={'delay': ['CLAIM-FACTUAL']},
        null_gate_claim_ids={key: ['CLAIM-FACTUAL'] for key in evaluation['null_gate_claim_ids']},
    )
    return [{'preregistration': root_contract(), 'evaluation': evaluation}]


def requested_graph():
    graph = empirical_graph()
    graph['claims'][0]['formal_qualification'].update(
        requested=True, family='G', concept_ref='V90-CANON-G2',
        instance_refs=[root_contract()['instance_id']], status='not_evaluated', result_status='not_evaluated',
    )
    return graph


def bind(graph=None, inputs=None):
    from xi_kari_runtime.formal_results import bind_formal_claim_results
    return bind_formal_claim_results(graph or requested_graph(), empirical_instances=inputs or instance_inputs())


def test_public_binder_recomputes_qualification_and_keeps_actual_input_hashes():
    before = requested_graph()
    checked = bind(before)
    after = checked['claim_mechanism_graph']
    assert before['claims'][0]['formal_qualification']['status'] == 'not_evaluated'
    assert after['claims'][0]['formal_qualification']['status'] == 'qualified'
    assert after['claims'][0]['formal_qualification']['result_status'] == 'supported'
    result = checked['instance_results'][root_contract()['instance_id']]
    assert result['preregistration_sha256'] == freeze_empirical_instance(root_contract())['preregistration_sha256']
    assert result['evaluation_sha256']
    assert checked['source_version'] == 'v9.0'


def test_checked_graph_requires_its_actual_registry_and_rejects_changed_material():
    from xi_kari_runtime.formal_results import rebuild_instance_registry
    graph, inputs = requested_graph(), instance_inputs()
    checked = bind(graph, inputs)['claim_mechanism_graph']
    registry = rebuild_instance_registry(inputs, graph=graph)
    assert claims.validate_claim_graph(checked, verified_instance_results=registry) == checked
    with pytest.raises(claims.ClaimMechanismError, match='verified real instance'):
        claims.validate_claim_graph(checked)
    checked['evidence'][0]['evidence_identity']['content_sha256'] = '9' * 64
    with pytest.raises(claims.ClaimMechanismError, match='same graph'):
        claims.validate_claim_graph(checked, verified_instance_results=registry)


@pytest.mark.parametrize('field,value', [('object', 'another-object'), ('population', 'another-team'), ('window', 'another-window'), ('target', 'another-target')])
def test_claim_qualification_cannot_borrow_an_instance_outside_its_scope(field, value):
    graph = requested_graph()
    graph['claims'][0]['claim_basis']['scope'][field] = value
    with pytest.raises(ValueError, match='scope'):
        bind(graph)


def test_concept_template_and_different_root_family_do_not_qualify_the_claim():
    graph = requested_graph()
    graph['claims'][0]['formal_qualification']['concept_ref'] = 'V90-CANON-G1'
    with pytest.raises(ValueError, match='family'):
        bind(graph)


def test_negative_formal_result_preserves_independent_ordinary_support():
    inputs = instance_inputs()
    inputs[0]['evaluation']['prerequisite_claim_ids'] = {}
    result = bind(inputs=inputs)
    qualification = result['claim_mechanism_graph']['claims'][0]['formal_qualification']
    assert qualification['status'] == 'unqualified'
    assert qualification['result_status'] == 'unsupported_or_undecided'
    assert claims.claim_constraints(result['claim_mechanism_graph'])['CLAIM-FACTUAL']['blocked'] is False


def test_null_support_requires_all_three_actual_gates():
    inputs = instance_inputs()
    inputs[0]['evaluation']['metrics'].update(controlled_perturbation_effect=0.001, **{'equivalence-upper': 0.002})
    assert bind(inputs=inputs)['claim_mechanism_graph']['claims'][0]['formal_qualification']['result_status'] == 'null_supported'
    inputs[0]['evaluation']['metrics']['detectable-effect'] = 0.9
    assert bind(inputs=inputs)['claim_mechanism_graph']['claims'][0]['formal_qualification']['result_status'] == 'unsupported_or_undecided'


def test_author_result_labels_cannot_override_the_recomputed_result():
    inputs = instance_inputs()
    inputs[0]['qualification'] = 'qualified'
    inputs[0]['result'] = {'result_state': 'supported'}
    with pytest.raises(ValueError, match='semantic instance input'):
        bind(inputs=inputs)


def test_fresh_process_recomputes_changed_disk_evidence(tmp_path):
    graph, inputs = requested_graph(), instance_inputs()
    graph_path, inputs_path = tmp_path / 'graph.json', tmp_path / 'instances.json'
    graph_path.write_text(json.dumps(graph), encoding='utf-8')
    inputs_path.write_text(json.dumps(inputs), encoding='utf-8')
    program = "import json,sys; from pathlib import Path; from scripts.xi_kari_runtime.formal_results import bind_formal_claim_results; r=bind_formal_claim_results(json.loads(Path(sys.argv[1]).read_text()),empirical_instances=json.loads(Path(sys.argv[2]).read_text())); print(r['claim_mechanism_graph']['claims'][0]['formal_qualification']['result_status'])"
    def fresh():
        return subprocess.run([sys.executable, '-B', '-c', program, str(graph_path), str(inputs_path)], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=True).stdout.strip()
    assert fresh() == 'supported'
    graph['evidence'][0]['support_checks']['world_fact_supported']['status'] = 'failed'
    graph_path.write_text(json.dumps(graph), encoding='utf-8')
    assert fresh() == 'unsupported_or_undecided'


def packet_inputs():
    from tests.test_p04_v4_packet import _packet_inputs
    semantic, contract = _packet_inputs()
    scope = deepcopy(requested_graph()['claims'][0]['claim_basis']['scope'])
    graph_claim = semantic['claim_mechanism_graph']['claims'][0]
    graph_claim['claim_basis'].update(kind='domain_empirical', scope=scope)
    graph_claim['formal_qualification'] = deepcopy(requested_graph()['claims'][0]['formal_qualification'])
    for record in semantic['evidence']['evidence'] + semantic['claim_mechanism_graph']['evidence']:
        record['support_checks']['world_fact_supported']['status'] = 'passed'
        record['identity'] = 'observed'
    semantic['empirical_instances'] = instance_inputs()
    semantic['derived_instances'] = []
    from xi_kari_runtime.semantic_projection import semantic_atom_paths
    semantic['visibility_ledger'] = {'entries': [
        {'canonical_path': path, 'classification': 'public', 'disclosure': 'include',
         'purpose': 'bounded source-scope analysis', 'authority_refs': [], 'protection_reason': None}
        for path in semantic_atom_paths(semantic)
    ]}
    return semantic, contract


def test_packet_constructor_recomputes_actual_formal_results_and_rejects_tampering():
    from xi_kari_runtime.contracts import build_analysis_packet, require_packet_contract
    semantic, contract = packet_inputs()
    packet = build_analysis_packet(semantic, run_contract=contract, repository_root=Path(__file__).resolve().parents[1])
    assert packet['claim_mechanism_graph']['claims'][0]['formal_qualification']['status'] == 'qualified'
    assert packet['formal_results']['instance_results'][root_contract()['instance_id']]['result']['result_state'] == 'supported'
    packet['formal_results']['instance_results'][root_contract()['instance_id']]['result']['result_state'] = 'null_supported'
    with pytest.raises(ValueError, match='recomputed'):
        require_packet_contract(packet, mode=contract['mode'], run_contract=contract)


def test_packet_constructor_cannot_accept_author_supplied_formal_result_controls():
    from xi_kari_runtime.contracts import build_analysis_packet
    semantic, contract = packet_inputs()
    semantic['formal_results'] = {'instance_results': {'forged': {'qualification': 'qualified'}}}
    with pytest.raises(ValueError, match='runtime-owned'):
        build_analysis_packet(semantic, run_contract=contract, repository_root=Path(__file__).resolve().parents[1])
