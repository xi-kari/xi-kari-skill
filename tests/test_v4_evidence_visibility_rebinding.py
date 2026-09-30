from copy import deepcopy
from pathlib import Path
import hashlib
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from tests.test_p04_v4_authoring import _authoring_input
from xi_kari_runtime.evidence import build_evidence_ledger
from xi_kari_runtime.semantic_projection import semantic_atom_paths
from xi_kari_runtime.visibility_rebinding_v4 import rebase_evidence_visibility_v4


def normalized():
    value, _, _, _, _ = _authoring_input()
    packet = value['semantic_packet']
    claims = deepcopy(packet['evidence']['claims'])
    purpose = packet['visibility_ledger']['entries'][0]['purpose']
    packet['visibility_ledger'] = {'entries': [
        {'canonical_path': path, 'classification': 'public', 'disclosure': 'include', 'purpose': purpose,
         'authority_refs': [], 'protection_reason': None}
        for path in semantic_atom_paths(packet)
    ]}
    for source in packet['retrieval']['sources']:
        source['assessment_verdict'] = 'admitted'
        source['content_sha256'] = hashlib.sha256(source['content'].encode()).hexdigest()
    packet['evidence'] = build_evidence_ledger(run_id='rebase', claims=claims, retrieval_index=packet['retrieval'], contract_version=4)
    return packet, claims


def test_normalization_preserves_protected_support_and_requires_new_outcome_decisions():
    packet, claims = normalized()
    old = 'evidence.claims[0].support[0].summary'
    entry = next(row for row in packet['visibility_ledger']['entries'] if row['canonical_path'] == old)
    entry.update(classification='sensitive', disclosure='withhold', protection_reason='Private supplied material')
    purpose = entry['purpose']
    rebase_evidence_visibility_v4(packet, author_claims=claims, purpose=purpose)
    by_path = {row['canonical_path']: row for row in packet['visibility_ledger']['entries']}
    mapped = by_path['evidence.evidence[0].summary']
    assert mapped['classification'] == 'sensitive' and mapped['disclosure'] == 'withhold'
    assert old not in by_path
    assert set(by_path) <= set(semantic_atom_paths(packet))
    assert 'evidence.evidence[0].research_context.research_design' not in by_path


def test_unresolvable_protected_decision_cannot_be_discarded():
    packet, claims = normalized()
    purpose = packet['visibility_ledger']['entries'][0]['purpose']
    packet['visibility_ledger']['entries'].append({'canonical_path': 'evidence.removed_secret', 'classification': 'sensitive',
        'disclosure': 'withhold', 'purpose': purpose, 'authority_refs': [], 'protection_reason': 'Private material'})
    with pytest.raises(ValueError, match='cannot be discarded'):
        rebase_evidence_visibility_v4(packet, author_claims=claims, purpose=purpose)
