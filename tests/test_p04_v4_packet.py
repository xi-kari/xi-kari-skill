from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from tests.test_p04_v4_authoring import _authoring_input
from xi_kari_runtime import contracts
from xi_kari_runtime.evidence import build_evidence_ledger
from xi_kari_runtime.problem_contract import contract_hash, stance_neutrality_key
from xi_kari_runtime.semantic_projection import semantic_atom_paths


def _packet_inputs():
    value, problem, _, _, _ = _authoring_input()
    semantic = value['semantic_packet']
    retrieval = deepcopy(semantic['retrieval'])
    retrieval['run_id'] = 'p04-packet'
    for source in retrieval['sources']:
        source['assessment_verdict'] = 'admitted'
        source['content_sha256'] = hashlib.sha256(source['content'].encode()).hexdigest()
    semantic['evidence'] = build_evidence_ledger(
        run_id='p04-packet', claims=semantic['evidence']['claims'], retrieval_index=retrieval,
        contract_version=4,
    )
    semantic['retrieval'] = retrieval
    semantic['visibility_ledger'] = {'entries': [
        {'canonical_path': path, 'classification': 'public', 'disclosure': 'include',
         'purpose': 'bounded source-scope analysis', 'authority_refs': [], 'protection_reason': None}
        for path in semantic_atom_paths(semantic)
    ]}
    contract = {
        'run_id': 'p04-packet', 'question': problem['question'], 'mode': 'open-world',
        'evidence_cutoff': problem['evidence_cutoff'], 'problem_contract': problem,
        'problem_contract_sha256': contract_hash(problem),
        'stance_neutrality_key': stance_neutrality_key(problem, mode='open-world'),
        'privacy_contract': None, 'contract_profile': 'production-authoring-v4',
    }
    return semantic, contract


def test_packet_builder_preserves_static_claims_and_validates_v4_contract():
    semantic, contract = _packet_inputs()
    packet = contracts.build_analysis_packet(semantic, run_contract=contract, repository_root=ROOT)
    contracts.require_packet_contract(packet, mode='open-world', run_contract=contract)
    assert packet['schema_version'] == 4
    assert packet['claim_mechanism_graph']['claims'][0]['claim_basis']['kind'] == 'text_interpretation'
    assert 'local_world_model' not in packet


def test_packet_rejects_an_applicable_stage_with_a_missing_real_consumer():
    semantic, contract = _packet_inputs()
    semantic['applicability']['world_state']['status'] = 'applicable'
    semantic['claim_mechanism_graph']['applicability']['world_state']['status'] = 'applicable'
    with pytest.raises(ValueError, match='local_world_model'):
        contracts.build_analysis_packet(semantic, run_contract=contract, repository_root=ROOT)


def test_packet_rejects_an_empty_world_used_to_satisfy_a_required_stage():
    semantic, contract = _packet_inputs()
    semantic['applicability']['world_state']['status'] = 'applicable'
    semantic['claim_mechanism_graph']['applicability']['world_state']['status'] = 'applicable'
    semantic['local_world_model'] = {}
    with pytest.raises(ValueError, match='world|state|consumer'):
        contracts.build_analysis_packet(semantic, run_contract=contract, repository_root=ROOT)
