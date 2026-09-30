from copy import deepcopy
import json

from tests.test_v4_semantic_executions import pending_reader_inputs
from xi_kari_runtime.semantic_executions_v4 import (
    _prompt,
    build_semantic_execution_request_v4,
)
from xi_kari_runtime.semantic_projection import typed_semantic_atoms


def _public_atoms(packet):
    return {row['canonical_path']: row['public_text'] for row in typed_semantic_atoms(packet)}


def test_final_reader_exposure_preserves_reference_labels():
    packet, contract, controls = pending_reader_inputs()
    request = build_semantic_execution_request_v4(
        packet, controls, run_contract=contract, kind='final_reader',
    )
    exposed = json.loads(_prompt(request).split(b'REQUEST_JSON\n', 1)[1])
    assert 'runtime_binding' not in exposed['task']['readonly_packet']
    assert 'concept_disposition' not in exposed['task']['readonly_packet']
    assert _public_atoms(exposed['task']['readonly_packet']) == _public_atoms(packet)


def test_audit_only_identifiers_do_not_renumber_reader_references():
    packet = {'applicability': {'world_state': {'source_refs': ['V90-P00158']}}}
    changed = deepcopy(packet)
    changed['runtime_binding'] = {'source_units': ['V90-P00001']}
    changed['concept_disposition'] = [{'source_ref': 'V90-P00002'}]
    assert _public_atoms(changed) == _public_atoms(packet)
