from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
import pytest

from tests.test_p04_v4_authoring import _authoring_input
from xi_kari_runtime.execution import _base_request
from xi_kari_runtime.ontology_read_trace import build_ontology_read_trace

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def source_inputs():
    return _authoring_input()


def test_actual_v9_ontology_binding_registers_its_authority_hashes(source_inputs):
    _, problem, plan, lock, _ = source_inputs
    request = _base_request(
        run_id=plan['run_id'], mode='open-world', problem_contract=problem,
        repository_root=ROOT, source_lock=lock, read_plan={}, concept_authority={},
        privacy_contract={}, ontology_read_plan=plan,
    )
    schema = json.loads((ROOT/'schemas/xk-v4-base-authoring-request.schema.json').read_text('utf8'))
    validator = Draft202012Validator({'$defs': schema['$defs'], '$ref': '#/$defs/ontologyReadPlanBinding'})
    binding = request['source_inputs']['ontology_read_plan']
    assert list(validator.iter_errors(binding)) == []
    for key in ('domain_index_sha256', 'knowledge_index_sha256'):
        bad = deepcopy(binding)
        bad['authority_bindings'].pop(key)
        assert list(validator.iter_errors(bad))
    bad = deepcopy(binding)
    bad['authority_bindings']['invented_hash'] = 'a'*64
    assert list(validator.iter_errors(bad))


def test_actual_v9_learning_pack_read_records_have_an_exact_schema_kind(source_inputs):
    value, _, plan, _, _ = source_inputs
    trace = build_ontology_read_trace(
        value['ontology_read_trace'], plan=plan, run_id=plan['run_id'],
        repository_root=ROOT, problem_contract_sha256=plan['problem_contract_sha256'],
    )
    schema = json.loads((ROOT/'schemas/xk-ontology-read-trace.schema.json').read_text('utf8'))
    validator = Draft202012Validator(schema)
    assert {'learning_pack', 'domain_identity_index'} <= {row['kind'] for row in trace['records']}
    assert list(validator.iter_errors(trace)) == []
    bad = deepcopy(trace)
    next(row for row in bad['records'] if row['kind'] == 'learning_pack')['kind'] = 'unregistered_pack'
    assert list(validator.iter_errors(bad))
