"""Recompute scoped causal results from semantic inputs and actual v4 registries."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from .canonical_json import canonical_bytes
from .causality import freeze_history_contract
from .claims import validate_causal_assessments
from .empirical_instances import freeze_empirical_instance
from .formal_results import rebuild_instance_registry
from .v4_contracts import validate_versioned_schema


def _inputs(value: Sequence[Mapping[str, Any]], label: str) -> list[dict[str, Any]]:
    if not isinstance(value, (list, tuple)) or any(not isinstance(row, Mapping) for row in value):
        raise ValueError(f"causal {label} must be a semantic record array")
    snapshot = [deepcopy(dict(row)) for row in value]
    canonical_bytes(snapshot)
    return snapshot


def recompute_causal_results_v4(assessments: Sequence[Mapping[str, Any]], *,
        graph: Mapping[str, Any], empirical_instances: Sequence[Mapping[str, Any]] = (),
        derived_instances: Sequence[Mapping[str, Any]] = (), mode: str,
        repository_root: Path) -> dict[str, Any]:
    """Return public causal results; cached qualification/result maps are not inputs."""
    if mode not in {"open-world", "closed-input"}:
        raise ValueError("causal evidence mode must be explicit")
    semantic = _inputs(assessments, "assessments")
    empirical = _inputs(empirical_instances, "empirical instances")
    derived = _inputs(derived_instances, "derived instances")
    root = Path(repository_root)
    validate_versioned_schema("xk-v4-causal-inputs.schema.json", semantic, repository_root=root)
    for row in semantic:
        if row["kind"] == "history":
            frozen = row["record"]["frozen_contract"]
            if freeze_history_contract(frozen["contract"]) != frozen:
                raise ValueError("causal history contract differs from its code-frozen identity")
    forbidden = {"qualification", "formal_result", "result", "method_gates_passed"}
    if any(set(row) & forbidden for row in derived):
        raise ValueError("derived causal inputs contain cached result fields")
    registry = rebuild_instance_registry(empirical, graph=graph, derived_instances=derived,
        evidence_mode=mode, repository_root=root)
    frozen_inputs = [{"frozen": freeze_empirical_instance(row["preregistration"]),
        "evaluation": deepcopy(row["evaluation"])} for row in empirical]
    return validate_causal_assessments(semantic, claim_mechanism_graph=graph,
        empirical_instances=frozen_inputs, derived_instances=derived, evidence_mode=mode,
        repository_root=root, verified_instance_results=registry)


__all__ = ("recompute_causal_results_v4",)
