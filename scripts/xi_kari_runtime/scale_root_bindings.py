"""Scale root registries rebuilt from empirical inputs and frozen object scope."""

from __future__ import annotations

from collections.abc import Mapping, Iterator, Sequence
import copy
import json
from typing import Any

from .world_volume import _canonical_sha256, freeze_object_identity


class ScaleRootBindingError(ValueError):
    pass


_REGISTRY_CREATION_KEY = object()


class EvaluatedScaleRootRegistry(Mapping[str, Mapping[str, Any]]):
    def __init__(self, results: Mapping[str, Any], *, graph_sha256: str, inputs_sha256: str, _creation_key: object):
        if _creation_key is not _REGISTRY_CREATION_KEY:
            raise ScaleRootBindingError("evaluated root registry requires actual runtime recomputation")
        self._results_json = json.dumps(results, ensure_ascii=False, sort_keys=True, allow_nan=False)
        self.graph_sha256 = graph_sha256
        self.inputs_sha256 = inputs_sha256

    def __getitem__(self, identifier: str) -> Mapping[str, Any]:
        return json.loads(self._results_json)[identifier]

    def __iter__(self) -> Iterator[str]:
        return iter(json.loads(self._results_json))

    def __len__(self) -> int:
        return len(json.loads(self._results_json))


def bind_scale_root_instances(
    record: Mapping[str, Any], *, instance_inputs: Sequence[Mapping[str, Any]],
    claim_mechanism_graph: Mapping[str, Any], object_contracts: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    from .claims import ClaimMechanismError, validate_empirical_instances
    from .v4_contracts import v4_authority

    try:
        evaluated = validate_empirical_instances(list(instance_inputs), claim_mechanism_graph=claim_mechanism_graph)
        _concepts, _anchors, dependencies = v4_authority()
    except ClaimMechanismError as error:
        raise ScaleRootBindingError(str(error)) from error
    identity, objects, scale, transform = (record[key] for key in ("identity", "objects", "scale", "transformation"))
    task = identity["purpose"]
    scope = {"SP0": scale["SP0"], "SP1": scale["SP1"], "source_K": objects["source_K"], "target_K": objects["target_K"], "task": task}
    requested = transform["root_instance_ids"]
    if not isinstance(requested, list) or not requested or len(set(requested)) != len(requested):
        raise ScaleRootBindingError("root scope requires distinct actual instance IDs")
    input_by_id = {item["frozen"]["preregistration"]["instance_id"]: item for item in instance_inputs}
    result_by_id = {item["preregistration"]["instance_id"]: item for item in evaluated["instances"]}
    claims = {claim["claim_id"]: claim for claim in claim_mechanism_graph["claims"]}
    evidence = {item["evidence_id"]: item for item in claim_mechanism_graph["evidence"]}
    roots: dict[str, Any] = {}
    verification: dict[str, Any] = {}
    root_evidence: dict[str, Any] = {}

    def claim_materials(claim_id: str) -> dict[str, Any]:
        claim = claims.get(claim_id)
        if claim is None:
            raise ScaleRootBindingError("root material claim does not resolve actual P04 graph")
        materials = [copy.deepcopy(evidence[ref]) for ref in claim["evidence_refs"]]
        sources = sorted({ref for material in materials for ref in material["source_refs"]})
        root_evidence[claim_id] = {"evidence_id": claim_id, "identity": "domain_empirical", "source_refs": sources, "claim_sha256": _canonical_sha256(claim), "materials": materials}
        return {"claim": copy.deepcopy(claim), "materials": materials}

    for identifier in requested:
        checked = result_by_id.get(identifier)
        if checked is None:
            raise ScaleRootBindingError("root scope instance does not resolve actual evaluated P05 input")
        contract = checked["preregistration"]
        frozen_object = object_contracts.get(contract["object_contract_id"])
        if frozen_object is None:
            raise ScaleRootBindingError("root scope object contract does not resolve the frozen P07 identity")
        object_binding = freeze_object_identity(frozen_object)
        candidate = contract["candidate_specification"]
        expected = {
            "candidate_object_id": objects["source_object"]["object_id"],
            "contract_version": identity["version"],
            "scale_profile": scale["SP0"], "identity_criterion": objects["source_K"],
            "time_window": object_binding["window"],
            "selected_subtype": transform["selected_subtype"],
            "selected_success_criterion": transform["selected_success_criterion"],
        }
        expected_candidate = {"mapping_id": objects["identity_mapping"]["mapping_id"], "source_scale": scale["SP0"], "target_scale": scale["SP1"], "source_K": objects["source_K"], "target_K": objects["target_K"], "target_task": task, "operator_ids": transform["operator_ids"], "selected_operator_branch": transform["selected_operator_branch"], "claim_mode": transform["claim_mode"], "retained_variables": record["variables"]["states"]}
        if object_binding["object_id"] != objects["source_object"]["object_id"] or object_binding["source_revision"] != dependencies["source_raw_sha256"] or _canonical_sha256(object_binding["K"]) != _canonical_sha256(objects["source_K"]) or _canonical_sha256(object_binding["SP"]) != _canonical_sha256(scale["SP0"]) or any(_canonical_sha256(contract.get(key)) != _canonical_sha256(value) for key, value in expected.items()) or any(_canonical_sha256(candidate.get(key)) != _canonical_sha256(value) for key, value in expected_candidate.items()) or task["target_quantity"] not in contract["target_variables"]:
            raise ScaleRootBindingError("actual root scope differs from frozen object/K/mapping/scale/window/task")
        if contract.get("root_id") not in {"G1", "G2", "G3", "G4"}:
            raise ScaleRootBindingError("scale root scope requires a G empirical instance")
        result = checked["result"]
        analysis_refs = []
        for claim_id in result["analysis_artifact_refs"]:
            artifact_id = identifier + ":analysis:" + claim_id
            artifact = {"artifact_id": artifact_id, "content": claim_materials(claim_id), "claim_graph_sha256": evaluated["claim_graph_sha256"], "instance_inputs_sha256": evaluated["instance_inputs_sha256"]}
            verification[artifact_id] = {**artifact, "artifact_sha256": _canonical_sha256(artifact)}
            analysis_refs.append(artifact_id)
        for claim_id in result["evidence_refs"]:
            claim_materials(claim_id)
        root = {
            "instance_id": identifier, "root_id": contract["root_id"],
            "contract_version": contract["contract_version"], "selected_subtype": contract["selected_subtype"],
            "selected_success_criterion": contract["selected_success_criterion"],
            "operator_ids": candidate["operator_ids"], "selected_operator_branch": candidate["selected_operator_branch"], "claim_mode": candidate["claim_mode"],
            "retained_variables": candidate["retained_variables"],
            "result_state": result["result_state"], "eligibility_status": "eligible" if checked["qualification"] == "qualified" else "ineligible",
            "scope_sha256": _canonical_sha256(scope), "object_contract_sha256": object_binding["binding_sha256"],
            "preregistration_timestamp": contract["preregistration_timestamp"], "result_timestamp": result["result_timestamp"],
            "evidence_refs": result["evidence_refs"], "analysis_artifact_refs": analysis_refs,
            "preregistration_sha256": checked["preregistration_sha256"], "evaluation_sha256": checked["evaluation_sha256"],
            "instance_input_sha256": _canonical_sha256(input_by_id[identifier]),
            "claim_graph_sha256": evaluated["claim_graph_sha256"],
            "decision_rule_outcome": result["decision_rule_outcome"], "null_decision_rule_outcome": result["null_decision_rule_outcome"],
        }
        roots[identifier] = {**root, "artifact_sha256": _canonical_sha256(root)}
    return {"root_instances": EvaluatedScaleRootRegistry(roots, graph_sha256=evaluated["claim_graph_sha256"], inputs_sha256=evaluated["instance_inputs_sha256"], _creation_key=_REGISTRY_CREATION_KEY), "verification_artifacts": verification, "evidence_registry": root_evidence}
