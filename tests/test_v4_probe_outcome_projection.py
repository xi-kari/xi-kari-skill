from copy import deepcopy
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from xi_kari_runtime.semantic_projection import semantic_atom_paths
from xi_kari_runtime.v4_contracts import validate_versioned_schema


def outcomes():
    probe = {
        'claim_assessments': [{'claim_id': 'CLAIM-FACTUAL', 'position': 'withhold', 'classification': 'text_interpretation',
            'judgment': 'The supplied passage admits a bounded alternative interpretation.',
            'evidence_refs': ['E-FACTUAL'], 'limits': ['This passage alone.'], 'withdrawal_conditions': ['Additional context resolves the ambiguity.']}],
        'counterarguments': [{'claim_id': 'CLAIM-FACTUAL', 'evidence_refs': ['E-FACTUAL'],
            'argument': 'An adjacent passage may restrict the interpretation in this particular example.',
            'defeat_condition': 'The wider passage supports only the initial reading.',
            'scope': {'object': 'passage', 'population': 'bounded text', 'window': 'given material', 'target': 'interpretation'},
            'costs': ['Read and compare the adjacent passage.']}],
        'source_undefined_refs': [],
    }
    sensitive = {**deepcopy(probe), 'changes_considered': []}
    return {'red_team': probe, 'stance': {'support': deepcopy(probe), 'oppose': deepcopy(probe)},
        'sensitivity': {'baseline': sensitive, 'changed': deepcopy(sensitive), 'changes': []},
        'comparison': {'red_team': {'status': 'examined', 'counterarguments': deepcopy(probe['counterarguments'])},
            'stance_stability': {'status': 'stable', 'equal_information': True, 'different_claim_ids': []},
            'sensitivity': {'status': 'stable', 'changed_claim_ids': [], 'changes': []}}}


def test_actual_probe_semantics_have_typed_counterargument_cost_and_scope_paths():
    value = outcomes()
    validate_versioned_schema('xk-v4-probe-outcomes.schema.json', value, repository_root=ROOT)
    paths = semantic_atom_paths({'probe_outcomes': value})
    assert 'probe_outcomes.red_team.counterarguments[0].costs[0]' in paths
    assert 'probe_outcomes.red_team.counterarguments[0].defeat_condition' in paths
    assert 'probe_outcomes.stance.oppose.claim_assessments[0].withdrawal_conditions[0]' in paths


def test_semantic_probe_outcomes_cannot_carry_self_declared_model_or_permission_gates():
    value = outcomes()
    value['actual_model_execution'] = True
    with pytest.raises(ValueError, match='constraint'):
        validate_versioned_schema('xk-v4-probe-outcomes.schema.json', value, repository_root=ROOT)
