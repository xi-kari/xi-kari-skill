from copy import deepcopy
from pathlib import Path
import json
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from xi_kari_runtime import transformations, world_volume, empirical_instances
from tests.test_p04_v4_claim_contracts import _v4_graph
from tests.test_p06_scale_instances import scale_fixture, attach_mapping
from tests.test_causal_judgment_instances import root_contract, root_result


def empirical_scale_fixture():
    record, registries = scale_fixture()
    record["objects"]["target_object"]["boundary"].append("unit-3")
    record["objects"]["target_K"] = {"version": "2", "definition": "same three bounded synthetic units"}
    record["evidence"]["target_refs"] = ["E-TARGET"]
    registries["evidence_registry"]["E-TARGET"] = {"evidence_id": "E-TARGET", "identity": "observed", "source_refs": ["SYNTHETIC-TARGET-FIXTURE"], "object_sha256": world_volume._canonical_sha256(record["objects"]["target_object"])}
    attach_mapping(record, registries, "converted_object")
    criterion = "identity_criterion_violation"
    record["variables"]["states"] = ["membership"]
    record["transformation"].update(claim_mode="object_conversion", selected_operator_branch="object_conversion", root_instance_ids=["ROOT-1"], selected_subtype="G4b", selected_success_criterion=criterion, causal_bridge=["synthetic predeclared mapping bridge"])
    raw_hash = json.loads((ROOT / "references/source/v9.0/source-manifest.json").read_text(encoding="utf-8"))["raw_sha256"]
    identity = {"object_id": record["objects"]["source_object"]["object_id"], "object_type": "nonhuman", "K": deepcopy(record["objects"]["source_K"]), "SP": deepcopy(record["scale"]["SP0"]), "window": {"start": "2026-09-01", "end": "2026-09-30"}, "subsystem": "synthetic boundary", "source_revision": raw_hash}
    contract = root_contract()
    contract.update(instance_id="ROOT-1", root_id="G4", contract_version="4.0.0", preregistration_timestamp="2026-09-29T00:00:00Z", candidate_object_id=identity["object_id"], object_contract_id="OBJECT-CONTRACT-1", scale_profile=record["scale"]["SP0"], time_window=identity["window"], identity_criterion=identity["K"], target_variables=["membership"], selected_subtype="G4b", selected_success_criterion=criterion, evaluation_metric=criterion, candidate_specification={"mapping_id": "MAP-1", "source_scale": record["scale"]["SP0"], "target_scale": record["scale"]["SP1"], "retained_variables": ["membership"], "source_K": record["objects"]["source_K"], "target_K": record["objects"]["target_K"], "target_task": record["identity"]["purpose"]})
    contract["candidate_specification"].update(operator_ids=record["transformation"]["operator_ids"], selected_operator_branch=record["transformation"]["selected_operator_branch"], claim_mode=record["transformation"]["claim_mode"])
    result = root_result()
    result.update(contract_version="4.0.0", first_result_access_timestamp="2026-09-30T11:00:00Z", result_timestamp="2026-09-30T12:00:00Z", evidence_claim_ids=["CLAIM-FACTUAL"], analysis_artifact_claim_ids=["CLAIM-FACTUAL"], prerequisite_claim_ids={key: ["CLAIM-FACTUAL"] for key in ("D3_E5_mapping", "comparison_model", "retained_variable_conditioning")}, null_gate_claim_ids={key: ["CLAIM-FACTUAL"] for key in ("equivalence", "sensitivity", "tolerance")}, dimension_claim_ids={})
    result["metrics"][criterion] = 1
    graph = _v4_graph()
    factual = next(claim for claim in graph["claims"] if claim["claim_id"] == "CLAIM-FACTUAL")
    factual["claim_basis"]["kind"] = "domain_empirical"
    factual["claim_basis"]["scope"]["object"] = identity["object_id"]
    factual["claim_basis"]["scope"]["window"] = deepcopy(identity["window"])
    factual["claim_basis"]["scope"]["target"] = "membership"
    return record, registries, [{"frozen": empirical_instances.freeze_empirical_instance(contract), "evaluation": result}], graph, {"OBJECT-CONTRACT-1": identity}


def bind(record, inputs, graph, objects):
    return transformations.bind_scale_root_instances(record, instance_inputs=inputs, claim_mechanism_graph=graph, object_contracts=objects)


def test_P06_consumes_code_recomputed_P05_root_and_frozen_P07_identity():
    record, registries, inputs, graph, objects = empirical_scale_fixture()
    bundle = bind(record, inputs, graph, objects)
    root = bundle["root_instances"]["ROOT-1"]
    assert root["eligibility_status"] == "eligible"
    assert root["selected_success_criterion"] == "identity_criterion_violation"
    assert root["preregistration_sha256"] == inputs[0]["frozen"]["preregistration_sha256"]
    registries["root_instances"] = bundle["root_instances"]
    registries["verification_artifacts"].update(bundle["verification_artifacts"])
    registries["evidence_registry"].update(bundle["evidence_registry"])
    assert transformations.validate_scale_instance(record, **registries)["mapping_class"] == "converted_object"


def test_root_status_labels_cannot_replace_actual_P05_recomputation():
    record, registries, inputs, graph, objects = empirical_scale_fixture()
    inputs[0]["evaluation"]["prerequisite_claim_ids"] = {}
    inputs[0]["frozen"].update(qualification="qualified", result={"result_state": "supported"})
    root = bind(record, inputs, graph, objects)["root_instances"]["ROOT-1"]
    assert root["eligibility_status"] == "ineligible"
    assert root["result_state"] == "unsupported_or_undecided"


@pytest.mark.parametrize("mutation", ["target_K", "task", "mapping", "identity_version"])
def test_root_scope_must_match_actual_K_mapping_and_task(mutation):
    record, registries, inputs, graph, objects = empirical_scale_fixture()
    if mutation == "target_K": record["objects"]["target_K"]["definition"] = "changed after results"
    if mutation == "task": record["identity"]["purpose"]["allowed_operations"] = ["intervene"]
    if mutation == "mapping": record["objects"]["identity_mapping"]["mapping_id"] = "GHOST"
    if mutation == "identity_version": objects["OBJECT-CONTRACT-1"]["K"]["version"] = "later version"
    with pytest.raises(transformations.TransformationError, match="scope"):
        bind(record, inputs, graph, objects)


def test_native_result_dictionary_cannot_impersonate_runtime_root_registry():
    record, registries, inputs, graph, objects = empirical_scale_fixture()
    bundle = bind(record, inputs, graph, objects)
    registries["root_instances"] = {key: bundle["root_instances"][key] for key in bundle["root_instances"]}
    registries["verification_artifacts"].update(bundle["verification_artifacts"])
    registries["evidence_registry"].update(bundle["evidence_registry"])
    with pytest.raises(transformations.TransformationError, match="recomputed"):
        transformations.validate_scale_instance(record, **registries)


def test_preselected_operator_branch_and_mode_cannot_change_after_root_evaluation():
    record, registries, inputs, graph, objects = empirical_scale_fixture()
    bundle = bind(record, inputs, graph, objects)
    record["transformation"].update(claim_mode="causal", selected_operator_branch="cross_layer_causal")
    with pytest.raises(transformations.TransformationError, match="scope"):
        bind(record, inputs, graph, objects)
    registries["root_instances"] = bundle["root_instances"]
    registries["verification_artifacts"].update(bundle["verification_artifacts"])
    registries["evidence_registry"].update(bundle["evidence_registry"])
    with pytest.raises(transformations.TransformationError):
        transformations.validate_scale_instance(record, **registries)


def test_root_retained_variables_cannot_be_changed_in_the_formal_record():
    record, registries, inputs, graph, objects = empirical_scale_fixture()
    record["variables"]["states"] = ["a different retained variable"]
    with pytest.raises(transformations.TransformationError, match="scope"):
        bind(record, inputs, graph, objects)


@pytest.mark.parametrize("field,value", [("window", "another observation window"), ("target", "another measured target")])
def test_root_empirical_material_cannot_use_a_different_window_or_target(field, value):
    record, registries, inputs, graph, objects = empirical_scale_fixture()
    graph["claims"][0]["claim_basis"]["scope"][field] = value
    with pytest.raises(transformations.TransformationError, match="scope"):
        bind(record, inputs, graph, objects)
