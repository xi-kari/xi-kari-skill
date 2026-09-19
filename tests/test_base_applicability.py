from copy import deepcopy
import json

import pytest
from jsonschema import Draft202012Validator

from tests.test_natural_contract_freeze import ROOT, envelope, request_and_final
from xi_kari_runtime import execution
from xi_kari_runtime.canonical_json import canonical_bytes
from xi_kari_runtime.problem_contract import FROZEN_FIELDS, contract_hash
from xi_kari_runtime.semantic_projection import semantic_atom_paths, validate_visibility_ledger


def base_envelope(*, dynamic=False, rationale=None):
    request, frozen = request_and_final()
    value = envelope(frozen)
    packet = value['semantic_packet']
    packet['problem_contract'] = deepcopy(frozen)
    if rationale is not None:
        packet['problem_contract']['applicability_rationale'] = rationale
    if dynamic:
        packet['dynamic_applicability'] = 'applicable'
        packet.pop('not_applicable_reason')
        schema = json.loads((ROOT / execution.BASE_OUTPUT_SCHEMA_RELATIVE).read_text(encoding='utf-8'))
        fields = schema['properties']['semantic_packet']['properties']
        for name in execution.BASE_DYNAMIC_FIELDS:
            packet[name] = [] if fields[name].get('type') == 'array' else {}
    packet['visibility_ledger'] = {'entries': [
        {'canonical_path': path, 'classification': 'public', 'disclosure': 'include',
         'purpose': 'unit test', 'authority_refs': [], 'protection_reason': None}
        for path in semantic_atom_paths(packet)
    ]}
    return request, frozen, value


def parse(value, request, frozen, monkeypatch):
    monkeypatch.setattr(execution, 'build_ontology_read_trace', lambda *args, **kwargs: {})
    return execution._parse_base_output(
        canonical_bytes(value), problem_contract=frozen, mode='open-world',
        ontology_read_plan={}, repository_root=ROOT, natural_request=request,
    )[0]


def test_static_exact_frozen_echo_projects_authored_applicability(monkeypatch):
    request, frozen, value = base_envelope()
    original = deepcopy(value)
    frozen_hash = contract_hash(frozen)
    packet = parse(value, request, frozen, monkeypatch)
    assert value == original
    assert contract_hash(frozen) == frozen_hash
    assert {field: packet['problem_contract'][field] for field in FROZEN_FIELDS} == frozen
    assert packet['problem_contract']['dynamic_applicability'] == 'not_applicable'
    assert packet['problem_contract']['applicability_rationale'] == packet['not_applicable_reason']
    schema = json.loads((ROOT/'schemas/xk-analysis-packet.schema.json').read_text(encoding='utf-8'))
    Draft202012Validator(schema['properties']['problem_contract']).validate(packet['problem_contract'])
    validate_visibility_ledger(packet, expected_purpose='unit test')
    replay = deepcopy(value)
    replay['semantic_packet'] = packet
    assert parse(replay, request, frozen, monkeypatch) == packet


def test_projected_reason_inherits_withheld_visibility(monkeypatch):
    request, frozen, value = base_envelope()
    packet = value['semantic_packet']
    entry = next(row for row in packet['visibility_ledger']['entries']
                 if row['canonical_path'] == 'not_applicable_reason')
    entry.update(classification='sensitive', disclosure='withhold',
                 authority_refs=['test:private-authority'], protection_reason='private test condition')
    projected = parse(value, request, frozen, monkeypatch)
    inherited = next(row for row in projected['visibility_ledger']['entries']
                     if row['canonical_path'] == 'problem_contract.applicability_rationale')
    assert inherited == {**entry, 'canonical_path': 'problem_contract.applicability_rationale'}
    validate_visibility_ledger(projected, expected_purpose='unit test')


def test_explicit_conflicting_applicability_still_rejected(monkeypatch):
    request, frozen, value = base_envelope()
    value['semantic_packet']['problem_contract']['dynamic_applicability'] = 'applicable'
    with pytest.raises(ValueError, match='applicability is inconsistent'):
        parse(value, request, frozen, monkeypatch)


def test_dynamic_projection_requires_author_supplied_rationale(monkeypatch):
    request, frozen, value = base_envelope(dynamic=True)
    with pytest.raises(ValueError, match='applicability[ _]rationale'):
        parse(value, request, frozen, monkeypatch)


def test_dynamic_projection_retains_author_supplied_rationale(monkeypatch):
    rationale = '题目涉及排程改变后的状态与条件路径。'
    request, frozen, value = base_envelope(dynamic=True, rationale=rationale)
    packet = parse(value, request, frozen, monkeypatch)
    assert packet['problem_contract']['dynamic_applicability'] == 'applicable'
    assert packet['problem_contract']['applicability_rationale'] == rationale
    validate_visibility_ledger(packet, expected_purpose='unit test')


@pytest.mark.parametrize('invalid', ['', None])
def test_present_invalid_reason_is_not_overwritten(monkeypatch, invalid):
    request, frozen, value = base_envelope()
    value['semantic_packet']['problem_contract']['applicability_rationale'] = invalid
    with pytest.raises(ValueError, match='schema validation|applicability rationale'):
        parse(value, request, frozen, monkeypatch)


def test_projection_does_not_supply_a_missing_visibility_decision(monkeypatch):
    request, frozen, value = base_envelope()
    ledger = value['semantic_packet']['visibility_ledger']
    ledger['entries'] = [entry for entry in ledger['entries']
                         if entry['canonical_path'] != 'not_applicable_reason']
    with pytest.raises(ValueError, match='visibility'):
        parse(value, request, frozen, monkeypatch)


def test_base_schema_exposes_dynamic_rationale_requirement():
    _, _, value = base_envelope(dynamic=True)
    errors = list(execution._schema_validator(execution.BASE_OUTPUT_SCHEMA_RELATIVE.name, str(ROOT)).iter_errors(value))
    assert any('applicability_rationale' in error.message for error in errors)
