from copy import deepcopy
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from xi_kari_runtime.packet_v4 import prepare_analysis_packet_v4, require_packet_contract_v4
from xi_kari_runtime.semantic_projection import semantic_atom_paths
from tests.test_p04_v4_packet import _packet_inputs
from tests.test_causal_judgment_v4_graph import effect_graph


def inputs():
    semantic, contract = _packet_inputs()
    graph, assessment = effect_graph()
    primary = semantic['claim_mechanism_graph']['claims'][0]
    primary['claim_basis'] = deepcopy(graph['claims'][0]['claim_basis'])
    primary['claim_basis']['material_refs'] = ['E-FACTUAL']
    for row in semantic['claim_mechanism_graph']['evidence'] + semantic['evidence']['evidence']:
        row['support_checks']['world_fact_supported']['status'] = 'passed'
    assessment['record']['mechanism_claim_ids'] = []
    semantic['causal_assessments'] = [assessment]
    return semantic, contract


def test_packet_recomputes_scoped_total_effect_without_creating_mechanism_support():
    semantic, contract = inputs()
    packet = prepare_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT)
    causal = packet['causal_results']['assessments'][0]['result']
    assert causal['total_effect'] == 'supported'
    assert causal['mechanism'] == 'unsupported_or_undecided'
    assert 'causal_results.assessments[0].result.total_effect' in semantic_atom_paths(packet)
    packet['causal_results']['assessments'][0]['result']['mechanism'] = 'supported'
    with pytest.raises(ValueError, match='freshly recomputed'):
        require_packet_contract_v4(packet, mode=contract['mode'], run_contract=contract, repository_root=ROOT)


def test_causal_packet_cannot_relabel_definition_as_empirical_total_effect():
    semantic, contract = inputs()
    semantic['claim_mechanism_graph']['claims'][0]['claim_basis']['kind'] = 'formal_proof'
    with pytest.raises(ValueError, match='empirical'):
        prepare_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT)
