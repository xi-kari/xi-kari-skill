"""Source-bound responsibility and evidence fields for version-four contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from .canonical_json import read_json, sha256_json
from .concept_authority import load_concept_authority


STAGES = ('world_state', 'transformation', 'mechanism', 'recursion', 'forecast', 'action_choice')
DEPENDENCY_ROLES = ('inferential_requires', 'protocol_requires', 'specializes', 'applies_to')
FORMAL_RESULT_STATUSES = ('supported', 'null_supported', 'unsupported_or_undecided', 'not_evaluated')
COMMON_SCHEMA_ID = 'https://xi-kari.local/schemas/xi-kari.v4.xk.common.schema.json'


def repository_path(repository_root: Path | None = None) -> Path:
    return Path(repository_root or Path(__file__).resolve().parents[2]).resolve()


def _schema_failure(error: Any, label: str) -> str:
    location = '.'.join(map(str, error.absolute_path)) or '<root>'
    detail = f'{error.validator} constraint failed'
    if error.validator == 'required' and isinstance(error.instance, Mapping):
        missing = [field for field in error.validator_value if field not in error.instance]
        detail = 'required fields are missing: ' + ', '.join(missing)
    return f'invalid {label} at {location}: {detail}'


def validate_versioned_schema(
    schema_name: str, value: Any, *, repository_root: Path | None = None
) -> None:
    repo = repository_path(repository_root)
    resources = Registry()
    for path in sorted((repo / 'schemas').glob('*.json')):
        schema = read_json(path)
        if isinstance(schema.get('$id'), str):
            resources = resources.with_resource(schema['$id'], Resource.from_contents(schema))
    schema = read_json(repo / 'schemas' / schema_name)
    validator = Draft202012Validator(schema, format_checker=FormatChecker(), registry=resources)
    errors = sorted(validator.iter_errors(value), key=lambda error: tuple(map(str, error.absolute_path)))
    if errors:
        raise ValueError(_schema_failure(errors[0], schema_name))


def validate_semantic_field(
    field: str, value: Any, *, repository_root: Path | None = None
) -> None:
    repo = repository_path(repository_root)
    resources = Registry()
    for path in sorted((repo / 'schemas').glob('*.json')):
        schema = read_json(path)
        if isinstance(schema.get('$id'), str):
            resources = resources.with_resource(schema['$id'], Resource.from_contents(schema))
    schema = {'$ref': COMMON_SCHEMA_ID + '#/$defs/' + field}
    validator = Draft202012Validator(schema, format_checker=FormatChecker(), registry=resources)
    errors = sorted(validator.iter_errors(value), key=lambda error: tuple(map(str, error.absolute_path)))
    if errors:
        raise ValueError(_schema_failure(errors[0], field))


def v4_authority(repository_root: Path | None = None) -> tuple[dict[str, Any], set[str], dict[str, Any]]:
    repo = repository_path(repository_root)
    load_concept_authority(repo, source_version='v9.0')
    registry = read_json(repo / 'references/ontology/v9.0/concept-registry.json')
    manifest = read_json(repo / 'references/source/v9.0/source-manifest.json')
    dependencies = read_json(repo / 'references/ontology/v9.0/dependency-graph.json')
    concepts = {row['concept_id']: row for row in registry['concepts']}
    anchors = set(manifest['source_unit_sequence'])
    return concepts, anchors, dependencies


def validate_v4_binding(value: Mapping[str, Any], *, repository_root: Path | None = None) -> dict[str, Any]:
    if value.get('schema_version') != 4 or value.get('source_version') != 'v9.0':
        raise ValueError('version-four semantic contracts require source v9.0')
    concepts, anchors, dependencies = v4_authority(repository_root)
    refs = value.get('ontology_refs')
    declared_anchors = value.get('source_anchors')
    if not isinstance(refs, list) or not refs or set(refs) - set(concepts):
        raise ValueError('version-four ontology references do not resolve')
    if not isinstance(declared_anchors, list) or not declared_anchors or set(declared_anchors) - anchors:
        raise ValueError('version-four source anchors do not resolve')
    return {'concepts': concepts, 'anchors': anchors, 'dependencies': dependencies}


def validate_applicability(
    applicability: Mapping[str, Any],
    *,
    claims: Sequence[Mapping[str, Any]] = (),
    anchors: set[str] | None = None,
    dependency_ids: set[str] | None = None,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    validate_semantic_field('applicability', applicability, repository_root=repository_root)
    for stage, row in applicability.items():
        if anchors is not None and set(row['source_refs']) - anchors:
            raise ValueError(f'{stage} applicability source reference does not resolve')
        if dependency_ids is not None and set(row['dependency_refs']) - dependency_ids:
            raise ValueError(f'{stage} applicability dependency reference does not resolve')
    required = set()
    if any(row.get('kind') == 'mechanism' for row in claims):
        required.add('mechanism')
    if any(row.get('kind') == 'prediction' for row in claims):
        required.add('forecast')
    for stage in required:
        if applicability[stage]['status'] == 'not_applicable':
            raise ValueError(f'{stage} claim cannot use not_applicable to bypass its validation')
    return dict(applicability)


def formal_responsibility_kind(concept: Mapping[str, Any]) -> str:
    identity = concept.get('source_concept_id', '')
    if identity in {'H2', 'H3'}:
        return 'classification_rule'
    if identity == 'H6':
        return 'normative_boundary'
    if identity in {'G1', 'G2', 'G3', 'G4', 'H1', 'H4', 'H5'}:
        return 'empirical_instance'
    return 'derived_framework_instance'


def claim_graph_input(graph: Mapping[str, Any]) -> dict[str, Any]:
    """Return semantic graph inputs without runtime qualification outcomes."""
    value = deepcopy(dict(graph))
    for claim in value.get('claims', []):
        qualification = claim.get('formal_qualification', {})
        if qualification.get('requested') is True:
            qualification['status'] = 'not_evaluated'
            qualification['result_status'] = 'not_evaluated'
    return value


def formal_claim_outcome(
    claim: Mapping[str, Any], *, concepts: Mapping[str, Any], verified_instance_results: Mapping[str, Any],
) -> tuple[str, str]:
    qualification = claim['formal_qualification']
    references = qualification['instance_refs']
    if not references or any(ref not in verified_instance_results for ref in references):
        return 'not_evaluated', 'not_evaluated'
    concept = concepts[qualification['concept_ref']]
    identity = concept['source_concept_id'].upper()
    outcomes = []
    for ref in references:
        result = verified_instance_results[ref]
        if result.get('instance_family', '').upper() != identity:
            raise ValueError('formal claim instance family differs from the actual source concept')
        preregistration = result.get('preregistration')
        if not isinstance(preregistration, Mapping):
            scope = verified_instance_results.instance_input(ref).get('scope')
            if not isinstance(scope, Mapping) or sha256_json(scope) != sha256_json(claim['claim_basis']['scope']):
                raise ValueError('derived formal claim scope differs from its actual instance input')
        else:
            scope = claim['claim_basis']['scope']
            if (
                scope['object'] != preregistration['candidate_object_id']
                or scope['population'] != preregistration['generalization_unit']
                or sha256_json(scope['window']) != sha256_json(preregistration['time_window'])
                or scope['target'] not in preregistration['target_variables']
            ):
                raise ValueError('formal claim scope differs from its actual frozen instance')
            if result.get('preregistration_sha256') != sha256_json(preregistration) or not result.get('evaluation_sha256'):
                raise ValueError('formal instance lacks recomputed preregistration and evaluation bindings')
        outcomes.append((result['qualification'], result.get('result', {}).get('result_state', result.get('formal_result'))))
    status = 'qualified' if all(row[0] == 'qualified' for row in outcomes) else 'unqualified'
    result = outcomes[0][1] if all(row[1] == outcomes[0][1] for row in outcomes) else 'unsupported_or_undecided'
    return status, result


def validate_claim_responsibilities(
    claim: Mapping[str, Any],
    *,
    material_ids: set[str] | None = None,
    concepts: Mapping[str, Any] | None = None,
    repository_root: Path | None = None,
    verified_instance_results: Mapping[str, Any] | None = None,
) -> None:
    for field, schema in (('claim_basis', 'claimBasis'), ('formal_qualification', 'formalQualification')):
        if field not in claim:
            raise ValueError(f'claim requires {field}')
        validate_semantic_field(schema, claim[field], repository_root=repository_root)
    basis = claim['claim_basis']
    qualification = claim['formal_qualification']
    if material_ids is not None and set(basis['material_refs']) - material_ids:
        raise ValueError('claim basis material reference does not resolve')
    if 'responsibility_refs' not in claim or not isinstance(claim['responsibility_refs'], list):
        raise ValueError('claim requires independent responsibility_refs')
    if concepts is not None and set(claim['responsibility_refs']) - set(concepts):
        raise ValueError('claim responsibility reference does not resolve')
    if not qualification['requested']:
        if (
            qualification['family'] != 'not_applicable'
            or qualification['concept_ref'] is not None
            or qualification['instance_refs']
            or qualification['status'] != 'not_requested'
            or qualification['result_status'] != 'not_evaluated'
        ):
            raise ValueError('unrequested formal qualification cannot assert an instance result')
        return
    if qualification['family'] == 'not_applicable' or qualification['concept_ref'] is None:
        raise ValueError('requested formal qualification requires a source concept')
    if qualification['status'] == 'not_requested':
        raise ValueError('requested formal qualification cannot be not_requested')
    if concepts is not None:
        concept = concepts.get(qualification['concept_ref'])
        if concept is None:
            raise ValueError('formal qualification concept reference does not resolve')
        identity = concept.get('source_concept_id', '')
        if not identity.startswith(qualification['family']):
            raise ValueError('formal qualification family differs from its source concept')
    if verified_instance_results is not None:
        if concepts is None:
            raise ValueError('formal instance validation requires source concepts')
        status, result = formal_claim_outcome(claim, concepts=concepts, verified_instance_results=verified_instance_results)
        if (qualification['status'], qualification['result_status']) != (status, result):
            raise ValueError('formal qualification differs from its verified real instance result')
    elif qualification['status'] == 'qualified' or qualification['result_status'] in {'supported', 'null_supported'}:
        raise ValueError('formal qualification requires a verified real instance, not a concept template or instance obligation')


def dependency_is_active(edge: Mapping[str, Any], graph: Mapping[str, Any]) -> bool:
    route = edge.get('route_ref')
    if route is None:
        return True
    selected = graph.get('selected_route_ids')
    if not isinstance(selected, list):
        raise ValueError('conditional dependency requires explicit selected_route_ids')
    return route in selected


def hard_claim_dependencies(graph: Mapping[str, Any]) -> dict[str, list[str]]:
    claims = {row['claim_id']: row for row in graph['claims']}
    if graph.get('schema_version') != 4:
        return {identifier: list(row['depends_on_claim_ids']) for identifier, row in claims.items()}
    result = {identifier: [] for identifier in claims}
    for edge in graph['dependency_edges']:
        if edge['role'] not in DEPENDENCY_ROLES:
            raise ValueError('input availability is not a semantic dependency role')
        if not dependency_is_active(edge, graph):
            continue
        if edge['role'] == 'inferential_requires' and edge['to_ref']['kind'] == 'claim':
            source, target = edge['from_id'], edge['to_ref']['id']
            if source not in claims or target not in claims:
                raise ValueError('hard claim dependency does not resolve')
            if target not in result[source]:
                result[source].append(target)
    for identifier, row in claims.items():
        if 'depends_on_claim_ids' in row and set(row['depends_on_claim_ids']) != set(result[identifier]):
            raise ValueError('legacy hard dependency projection differs from typed active edges')
    return result


def validate_evidence_responsibilities(
    record: Mapping[str, Any], *, repository_root: Path | None = None
) -> None:
    for field, schema in (('evidence_identity', 'evidenceIdentity'), ('support_checks', 'supportChecks'), ('research_context', 'researchContext')):
        if field not in record:
            raise ValueError(f'evidence requires {field}')
        validate_semantic_field(schema, record[field], repository_root=repository_root)
    context = record['research_context']
    if context['independence_key'] not in record['evidence_identity']['lineage_refs']:
        raise ValueError('evidence independence must bind an actual source lineage')
    if record.get('availability_status') not in {'available', 'unavailable', 'not_observable', 'unknown'}:
        raise ValueError('evidence availability must remain independent from visibility')
    if record.get('visibility') not in {'public', 'withheld_for_protection'}:
        raise ValueError('evidence requires a public or protected visibility state')
    review = record.get('protected_review')
    if record['visibility'] == 'withheld_for_protection':
        if review is None:
            raise ValueError('protected evidence requires a scoped trusted review path')
        validate_semantic_field('protectedReview', review, repository_root=repository_root)
    elif review is not None:
        raise ValueError('public evidence cannot impersonate a protected review')


def evidence_supports_claim(record: Mapping[str, Any], claim: Mapping[str, Any]) -> bool:
    checks = record['support_checks']
    required = {'source_exists', 'passage_supports_claim'}
    if checks['quotation_accurate']['status'] != 'not_applicable':
        required.add('quotation_accurate')
    basis = claim['claim_basis']
    source_statement = basis['kind'] == 'source_fact' and basis['scope']['target'] in {'author_statement', 'source_statement'}
    if basis['kind'] == 'domain_empirical' or (claim.get('kind') in {'factual', 'external_fact', 'documented_real_case'} and not source_statement):
        required.add('world_fact_supported')
    if any(checks[field]['status'] != 'passed' for field in required):
        return False
    if record['availability_status'] == 'available':
        return True
    review = record.get('protected_review')
    if record['visibility'] != 'withheld_for_protection' or not isinstance(review, Mapping):
        return False
    expires = datetime.fromisoformat(review['review_at'].replace('Z', '+00:00'))
    return expires > datetime.now(timezone.utc)


__all__ = (
    'STAGES', 'DEPENDENCY_ROLES', 'FORMAL_RESULT_STATUSES',
    'validate_semantic_field', 'validate_versioned_schema', 'v4_authority', 'validate_v4_binding',
    'validate_applicability', 'formal_responsibility_kind',
    'validate_claim_responsibilities', 'dependency_is_active',
    'hard_claim_dependencies', 'validate_evidence_responsibilities',
    'evidence_supports_claim',
)
