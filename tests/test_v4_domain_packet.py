from copy import deepcopy
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from xi_kari_runtime.packet_v4 import prepare_analysis_packet_v4, build_analysis_packet_v4, require_packet_contract_v4
from xi_kari_runtime.domain_pipeline_v4 import prepare_domain_inputs
from xi_kari_runtime.semantic_projection import semantic_atom_paths
from tests.test_p04_v4_packet import _packet_inputs
from tests.test_v4_domain_pipeline import _author_trace


def inputs():
    semantic, contract = _packet_inputs()
    prepared = prepare_domain_inputs(['D.04', 'D.09'], run_id=contract['run_id'], problem_contract_sha256=contract['problem_contract_sha256'], repository_root=ROOT)
    semantic['domain_trace'] = _author_trace(prepared)
    for link in semantic['domain_trace']['claim_links']:
        link['claim_ids'] = ['CLAIM-FACTUAL']
    return semantic, contract, prepared['plan']


def finalize(pending, purpose):
    return {'reader_sections': pending['reader_sections'], 'visibility_ledger': {'entries': [
        {'canonical_path': path, 'classification': 'public', 'disclosure': 'include',
         'purpose': purpose, 'authority_refs': [], 'protection_reason': None}
        for path in semantic_atom_paths(pending)
    ]}}


def test_domain_preparation_reads_real_selected_bytes_before_explicit_disclosure():
    semantic, contract, plan = inputs()
    pending = prepare_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT, domain_read_plan=plan)
    assert pending['domain_binding']['result']['domain_ids'] == ['D.04', 'D.09']
    assert any('domain_read_trace.records[0].reader_responsibilities.costs_exit' == path for path in semantic_atom_paths(pending))
    with pytest.raises(ValueError, match='visibility'):
        require_packet_contract_v4(pending, mode=contract['mode'], run_contract=contract)
    final = build_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT, domain_read_plan=plan,
        reader_finalization=finalize(pending, 'bounded source-scope analysis'))
    final['domain_binding']['authority']['fingerprint_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='freshly'):
        require_packet_contract_v4(final, mode=contract['mode'], run_contract=contract)


def test_domain_inputs_cannot_choose_another_runtime_plan_or_modify_code_outputs():
    semantic, contract, plan = inputs()
    changed = deepcopy(plan)
    changed['problem_contract_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='problem'):
        prepare_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT, domain_read_plan=changed)
    semantic['domain_binding'] = {'status': 'passed'}
    with pytest.raises(ValueError, match='runtime-owned'):
        prepare_analysis_packet_v4(semantic, run_contract=contract, repository_root=ROOT, domain_read_plan=plan)
