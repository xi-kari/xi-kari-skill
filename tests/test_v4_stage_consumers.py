from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from tests.test_p07_v4_evidence_adapter import v4_event_fixture
from xi_kari_runtime import packet_v4


def test_world_consumer_replays_material_bound_unauthorized_observation():
    state, event, ledger, retrieval, bindings = v4_event_fixture()
    world = {
        'initial_state': state, 'events': [event], 'event_bindings': bindings,
        'channel_registry': {}, 'authorization_registry': {},
        'identities': [], 'prototypes': [], 'identity_changes': [],
    }
    result = packet_v4.validate_world_stage(world, evidence_ledger=ledger, retrieval_index=retrieval)
    assert result['output_state']['objects'][0]['variables'][0]['value'] == 'new'
    assert result['transitions'][0]['event_role'] == 'e(t)'
    assert result['transitions'][0]['external_action_authorized'] is False
    assert result['output_state']['unknowns'] == state['unknowns']


def test_world_consumer_rejects_post_materialization_target_changes():
    state, event, ledger, retrieval, bindings = v4_event_fixture()
    event['deltas'][0]['after'] = 'unbound replacement'
    world = {
        'initial_state': state, 'events': [event], 'event_bindings': bindings,
        'channel_registry': {}, 'authorization_registry': {},
        'identities': [], 'prototypes': [], 'identity_changes': [],
    }
    with pytest.raises(ValueError, match='delta|target|bind'):
        packet_v4.validate_world_stage(world, evidence_ledger=ledger, retrieval_index=retrieval)
