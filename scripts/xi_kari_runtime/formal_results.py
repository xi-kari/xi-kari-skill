"""Runtime qualification outcomes rebuilt from source-bound semantic inputs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from .claims import validate_claim_graph
from .empirical_instances import EvaluatedInstanceRegistry, freeze_empirical_instance
from .v4_contracts import claim_graph_input, formal_claim_outcome, v4_authority, validate_versioned_schema


def rebuild_instance_registry(
    empirical_instances: Sequence[Mapping[str, Any]], *, graph: Mapping[str, Any],
    derived_instances: Sequence[Mapping[str, Any]] = (), evidence_mode: str = 'open-world',
    repository_root: Path | None = None,
) -> EvaluatedInstanceRegistry:
    inputs = []
    for item in empirical_instances:
        if not isinstance(item, Mapping) or set(item) != {'preregistration', 'evaluation'} or not isinstance(item['preregistration'], Mapping) or not isinstance(item['evaluation'], Mapping):
            raise ValueError('semantic instance input requires only preregistration and evaluation')
        inputs.append({'frozen': freeze_empirical_instance(item['preregistration']), 'evaluation': deepcopy(dict(item['evaluation']))})
    validate_versioned_schema('xk-v4-claim-mechanism.schema.json', graph, repository_root=repository_root)
    return EvaluatedInstanceRegistry(inputs, graph=graph, derived_instances=list(derived_instances), evidence_mode=evidence_mode, repository_root=repository_root)


def bind_formal_claim_results(
    graph: Mapping[str, Any], *, empirical_instances: Sequence[Mapping[str, Any]],
    derived_instances: Sequence[Mapping[str, Any]] = (), evidence_mode: str = 'open-world',
    repository_root: Path | None = None,
) -> dict[str, Any]:
    registry = rebuild_instance_registry(empirical_instances, graph=graph, derived_instances=derived_instances, evidence_mode=evidence_mode, repository_root=repository_root)
    resolved = claim_graph_input(graph)
    concepts, _, dependencies = v4_authority(repository_root)
    for claim in resolved['claims']:
        qualification = claim['formal_qualification']
        if qualification['requested']:
            qualification['status'], qualification['result_status'] = formal_claim_outcome(claim, concepts=concepts, verified_instance_results=registry)
    validate_claim_graph(resolved, evidence_mode=evidence_mode, repository_root=repository_root, verified_instance_results=registry)
    return {
        'source_version': 'v9.0', 'source_revision': dependencies['source_raw_sha256'],
        'claim_mechanism_graph': resolved, 'claim_input_sha256': registry.graph_sha256,
        'instance_inputs_sha256': registry.inputs_sha256, 'instance_results': dict(registry),
    }


__all__ = ('bind_formal_claim_results', 'rebuild_instance_registry')
