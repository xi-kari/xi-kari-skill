"""Material responsibility bindings on independently observed retrieval bytes."""

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from .canonical_json import sha256_json, sha256_text


MATERIAL_FIELDS = (
    'source_revision', 'canonical_locator', 'lineage_refs', 'research_design',
    'read_extent', 'provenance_refs', 'independence_key', 'availability_status',
    'visibility', 'protected_review',
)
BINDING_FIELD = 'material_responsibility_binding'
PROJECTED_FIELDS = (*MATERIAL_FIELDS, 'assessment_verdict')


def host_retrieval_view(retrieval: Mapping[str, Any]) -> dict[str, Any]:
    value = deepcopy(dict(retrieval))
    binding = value.pop(BINDING_FIELD, None)
    if not isinstance(binding, Mapping):
        raise ValueError('retrieval has no actual host material responsibility binding')
    originals = {row['source_id']: row['fields'] for row in binding['original_fields']}
    for field in binding.get('added_root_fields', []):
        value.pop(field, None)
    for source in value['sources']:
        for field in PROJECTED_FIELDS:
            source.pop(field, None)
        source.update(originals[source['source_id']])
    if sha256_json(value) != binding['host_index_sha256']:
        raise ValueError('material binding differs from the frozen host retrieval index')
    return value


def bind_material_responsibilities(
    retrieval: Mapping[str, Any], authored_retrieval: Mapping[str, Any],
    *, run_id: str | None = None,
) -> dict[str, Any]:
    if BINDING_FIELD in retrieval:
        raise ValueError('host retrieval cannot supply a precomputed material responsibility binding')
    value = deepcopy(dict(retrieval))
    authors = authored_retrieval.get('sources')
    if not isinstance(authors, list) or len(authors) != len(value.get('sources', [])):
        raise ValueError('material responsibilities do not cover the actual host sources')
    originals = []
    verdicts = {}
    for assessment in value.get('assessments', []):
        identifier = assessment.get('source_id')
        if identifier in verdicts:
            raise ValueError('actual host retrieval source assessment is duplicated')
        verdicts[identifier] = assessment.get('verdict')
    for host, author in zip(value['sources'], authors, strict=True):
        if not isinstance(author, Mapping) or set(MATERIAL_FIELDS) - set(author):
            raise ValueError('source material responsibilities are incomplete')
        identity_field = 'url' if value['mode'] == 'open-world' else 'source_id'
        if host.get(identity_field) != author.get(identity_field):
            raise ValueError('material responsibilities refer to a different actual source')
        content = host.get('content', host.get('excerpt'))
        if not isinstance(content, str) or host.get('content_sha256') != sha256_text(content):
            raise ValueError('actual host material content hash differs')
        authored_content = author.get('content', author.get('excerpt'))
        if not isinstance(authored_content, str) or authored_content not in content:
            raise ValueError('authored content does not occur in the frozen host material')
        locator = author['canonical_locator']
        base = host.get('url') if value['mode'] == 'open-world' else host['source_id']
        authored_id = author.get('source_id')
        if isinstance(authored_id, str) and (locator == authored_id or locator.startswith(authored_id + ':') or locator.startswith(authored_id + '#')):
            locator = base + locator[len(authored_id):]
        if not isinstance(locator, str) or not (locator == base or locator.startswith(base + ':') or locator.startswith(base + '#')):
            raise ValueError('material canonical locator refers outside its actual source')
        originals.append({'source_id': host['source_id'], 'fields': {field: deepcopy(host[field]) for field in PROJECTED_FIELDS if field in host}})
        for field in MATERIAL_FIELDS:
            host[field] = deepcopy(author[field])
        host['canonical_locator'] = locator
        if host['source_id'] in verdicts:
            verdict = verdicts[host['source_id']]
            if 'assessment_verdict' in host and host['assessment_verdict'] != verdict:
                raise ValueError('material admission differs from its actual source assessment')
            host['assessment_verdict'] = verdict
    added = []
    if run_id is not None:
        if 'run_id' in value and value['run_id'] != run_id:
            raise ValueError('material projection differs from the actual runtime run identity')
        if 'run_id' not in value:
            added.append('run_id')
        value['run_id'] = run_id
    value[BINDING_FIELD] = {'host_index_sha256': sha256_json(retrieval), 'original_fields': originals, 'added_root_fields': added}
    return value


def bind_graph_materials(graph: Mapping[str, Any], ledger: Mapping[str, Any]) -> dict[str, Any]:
    value = deepcopy(dict(graph))
    evidence = {row['evidence_id']: row for row in ledger['evidence']}
    for row in value['evidence']:
        materials = [evidence[ref] for ref in row['xk3_evidence_refs'] if ref in evidence]
        if not materials or len(materials) != len(row['xk3_evidence_refs']):
            raise ValueError('claim graph evidence does not resolve actual frozen material')
        first = materials[0]
        for material in materials:
            if material['evidence_identity'] != first['evidence_identity'] or material['support_checks'] != row['support_checks']:
                raise ValueError('claim graph material differs from its actual support relation')
        row['source_refs'] = sorted({material['source_id'] for material in materials})
        for field in ('evidence_identity', 'research_context', 'support_checks', 'availability_status', 'visibility', 'protected_review'):
            row[field] = deepcopy(first[field])
    return value


__all__ = ('bind_material_responsibilities', 'host_retrieval_view', 'bind_graph_materials')
