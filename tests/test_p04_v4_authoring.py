from __future__ import annotations

from copy import deepcopy
import hashlib
import re
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from tests.test_natural_contract_freeze import envelope, request_and_final
from tests.test_p04_v4_claim_contracts import _nonmechanistic_interpretation_graph
from tests.test_v90_source_lock import _trace_input
from xi_kari_runtime import execution
from xi_kari_runtime.canonical_json import canonical_bytes
from xi_kari_runtime.retrieval import build_full_source_lock
from xi_kari_runtime.ontology_read_trace import (
    build_ontology_read_plan, content_access_witness, read_ontology_item_bytes,
)
from xi_kari_runtime.problem_contract import contract_hash


def _authoring_input():
    _, problem = request_and_final()
    value = envelope(problem)
    packet = value['semantic_packet']
    packet.pop('dynamic_applicability')
    packet.pop('not_applicable_reason')
    packet['problem_contract'].pop('dynamic_applicability')
    graph = _nonmechanistic_interpretation_graph()
    graph['world_volume_id'] = None
    graph['claims'] = graph['claims'][:1]
    graph['evidence'] = graph['evidence'][:1]
    graph['explanations'] = graph['explanations'][:2]
    graph['countercases'] = []
    graph['rival_assessment'] = {
        'status': 'no_reasonable_rival', 'reason': 'No alternative is supported by this fixture.',
        'search_scope': 'This supplied fixture only.', 'failure_conditions': ['A wider passage supports an alternative.'],
    }
    material = packet['retrieval']['sources'][0]
    source_id = material['source_id']
    material.update(
        source_revision='REV-1', canonical_locator='SOURCE-1:P1',
        lineage_refs=['LINEAGE-SOURCE-1'], independence_key='LINEAGE-SOURCE-1',
        research_design='bounded textual comparison', read_extent='the supplied paragraph',
        provenance_refs=[source_id], availability_status='available', visibility='public', protected_review=None,
    )
    graph['evidence'][0]['source_refs'] = [source_id]
    graph['evidence'][0]['xk3_evidence_refs'] = ['CLAIM-FACTUAL-e1']
    graph['evidence'][0]['evidence_identity'].update(
        canonical_locator='SOURCE-1:P1', content_sha256=hashlib.sha256(material['content'].encode()).hexdigest(),
        lineage_refs=['LINEAGE-SOURCE-1'],
    )
    graph['evidence'][0]['research_context'].update(provenance_refs=[source_id], independence_key='LINEAGE-SOURCE-1')
    packet['claim_mechanism_graph'] = graph
    packet['applicability'] = deepcopy(graph['applicability'])
    packet['evidence']['claims'] = [{
        'claim_id': 'CLAIM-FACTUAL', 'text': graph['claims'][0]['statement'], 'kind': 'interpretation',
        'support': [{'source_id': source_id, 'summary': 'A source-scope fixture.', 'support_checks': graph['evidence'][0]['support_checks']}],
        'claim_basis': {**deepcopy(graph['claims'][0]['claim_basis']), 'material_refs': [source_id]},
        'formal_qualification': deepcopy(graph['claims'][0]['formal_qualification']), 'responsibility_refs': [],
    }]
    packet['answer']['basis_refs'] = ['CLAIM-FACTUAL']
    value['semantic_read_trace'] = _trace_input()
    plan = build_ontology_read_plan(ROOT, run_id='p04-authoring', problem_contract_sha256=contract_hash(problem), content_access_challenge='b'*64, source_version='v9.0')
    records = []
    for row in plan['records']:
        content = read_ontology_item_bytes(ROOT, row).decode('utf-8')
        excerpt = next((line.strip() for line in content.splitlines() if len(line.strip()) >= 50 and re.search(r'[\u4e00-\u9fff]{8}', line)), max(content.splitlines(), key=len).strip())[:600]
        records.append({
            'item_id': row['item_id'], 'read_status': 'read', 'content_excerpt': excerpt,
            'content_witness': content_access_witness(challenge=plan['content_access_challenge'], problem_contract_sha256=contract_hash(problem), item_id=row['item_id'], content_sha256=row['content_sha256']),
            'problem_relation': {'status': 'boundary_only', 'rationale': f"{row['item_id']} supplies the source observation {excerpt}; it bounds the fixture's interpretation of the supplied clause and supplies no empirical-instance qualification or external authorization."},
        })
    value['ontology_read_trace']['records'] = records
    lock, events = build_full_source_lock(ROOT, run_id='p04-authoring', source_version='v9.0')
    return value, problem, plan, lock, events


def test_v4_author_parser_accepts_bounded_interpretation_without_dynamic_artifacts():
    value, problem, plan, lock, events = _authoring_input()
    packet, source_trace, ontology_trace = execution.parse_base_authoring_output(
        canonical_bytes(value), problem_contract=problem, mode='open-world', repository_root=ROOT,
        ontology_read_plan=plan, source_lock=lock, source_events=events, contract_version=4,
    )
    assert packet['applicability']['mechanism']['status'] == 'not_applicable'
    assert packet['claim_mechanism_graph']['world_volume_id'] is None
    assert 'local_world_model' not in packet
    assert source_trace['schema_id'] == 'xi-kari.v4.semantic-read-trace-input'
    assert len(ontology_trace['records']) == plan['record_count']


def test_v4_author_parser_rejects_a_changed_frozen_problem():
    value, problem, plan, lock, events = _authoring_input()
    value['semantic_packet']['problem_contract']['boundary'] = 'Changed after the source read plan.'
    with pytest.raises(ValueError, match='frozen problem contract'):
        execution.parse_base_authoring_output(
            canonical_bytes(value), problem_contract=problem, mode='open-world', repository_root=ROOT,
            ontology_read_plan=plan, source_lock=lock, source_events=events, contract_version=4,
        )
