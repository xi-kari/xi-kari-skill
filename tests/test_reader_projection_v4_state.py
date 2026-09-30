"""Reader responsibilities at a synthetic fixture projection seam.

The helpers validate separate synthetic event, scale and recursive examples. Selected
checked fields enter minimal projection payloads; these tests do not validate a full
analysis packet, invoke a provider, accept a stage or prove a runtime seal.
"""

from copy import deepcopy
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from xi_kari_runtime import evidence, prose, recursion, transformations, world_volume
from xi_kari_runtime.coverage import build_semantic_coverage
from xi_kari_runtime.semantic_projection import (
    semantic_atom_paths, substantive_semantic_atoms, typed_semantic_atoms,
    validate_reader_sections, validate_visibility_ledger,
)
from tests.reader_projection_v4_state_data import (
    ALTERNATIVE_COST_BODY, IDENTITY_PROTECTED_BODY, IDENTITY_PROTECTION_REASON, SCALE_BODY,
    SCALE_SECTION_NAMES,
)
from tests.test_p06_scale_instances import scale_fixture
from tests.test_p07_v4_evidence_adapter import v4_event_fixture
from tests.test_p07_v4_world_bundle import bundle_fixture
from tests.test_p07_event_records import frozen_state, observed_event
from tests.test_p08_recursive_transitions import recursive_fixture


DIRECT_ANSWER = "现有材料支持有限的描述；共同输出没有消除损失，也没有授予执行权。"
SCALE_BASE = "transformation_ledger.transformations[0]"


def section(identifier, heading, judgment, paragraph, bindings):
    return {
        "section_id": identifier, "heading": heading,
        "local_judgment": judgment, "paragraphs": [paragraph],
        "source_bindings": [
            {"source_path": path, "paragraph_index": 1, "excerpt": excerpt}
            for path, excerpt in bindings.items()
        ],
    }


def visibility(payload):
    payload["visibility_ledger"] = {"entries": [
        {"canonical_path": path, "classification": "public", "disclosure": "include",
         "purpose": "synthetic reader projection", "authority_refs": [],
         "protection_reason": None}
        for path in semantic_atom_paths(payload)
    ]}
    return payload


def projection(root, value, sections):
    payload = {
        "schema_version": 4, "answer": {"direct_answer": DIRECT_ANSWER},
        root: value,
        "reader_sections": [section(
            "judgment", "当前判断", "本轮判断仍有用途边界。", DIRECT_ANSWER,
            {"answer.direct_answer": DIRECT_ANSWER},
        ), *sections],
    }
    return visibility(payload)


def semantic_coverage(payload, outputs=None):
    return build_semantic_coverage(
        run_id="synthetic-state-projection", packet=payload,
        source_read_complete=False, candidate_closure_complete=False,
        reader_outputs=outputs if outputs is not None else prose.render_reader_outputs(payload),
    )


def assert_complete(payload):
    validate_visibility_ledger(payload)
    assert validate_reader_sections(payload) == []
    answer = prose.render_answer(payload)
    assert prose.render_chat_projection(payload) == answer
    coverage = semantic_coverage(payload)
    assert coverage["source_read_complete"] is False
    assert coverage["candidate_closure_complete"] is False
    assert coverage["main_answer_complete"] is True
    assert coverage["reader_projection_complete"] is True
    assert coverage["substantive_unprojected_paths"] == []
    return answer, coverage


def event_projection():
    state, event, ledger, retrieval, bindings = v4_event_fixture()
    assert evidence.validate_evidence_ledger(ledger, retrieval) == []
    registry = world_volume.bind_registered_event_evidence(
        state, [event], evidence_ledger=ledger, retrieval_index=retrieval,
        bindings=bindings,
    )
    transition = world_volume.apply_registered_event(state, event, evidence_registry=registry)
    bundle, bundle_ledger, bundle_retrieval = bundle_fixture()
    world_volume.validate_world_volume(
        bundle, repository_root=ROOT, evidence_ledger=bundle_ledger,
        retrieval_index=bundle_retrieval, expected_run_id=state["run_id"],
    )
    checked = world_volume.validate_registered_world_bundle(
        bundle, repository_root=ROOT, evidence_ledger=bundle_ledger,
        retrieval_index=bundle_retrieval,
    )
    assert transition.output_state == checked["final_state"]
    assert transition.event_role == "e(t)"
    assert transition.external_action_authorized is False
    assert transition.authorization_status == "unauthorized"
    value = {
        "event_records": [{key: deepcopy(event[key]) for key in (
            "kind", "occurrence_status", "authorization_status", "mechanism_id",
        )}],
        "registered_state": {
            "objects": [{"variables": [{key: checked["final_state"]["objects"][0]
                ["variables"][0][key] for key in ("category", "value", "clock_id")}]}],
            "unknowns": [{"reason": state["unknowns"][0]["reason"]}],
            "residuals": [{"reason": state["residuals"][0]["reason"]}],
        },
        "applicability": {"mechanism": {
            key: bundle["applicability"]["mechanism"][key] for key in ("status", "rationale")
        }},
    }
    observed = (
        "事件证据身份为直接观察，发生状态为 occurred，授权状态仍是 unauthorized。"
        "这次未经授权的变化是已发生的 e(t)，观察事实不授予继续执行的权利。"
        "机制记录为未记录，因此不能把事件观察直接提升为已证明的机制。"
    )
    state_text = (
        "更新后的变量类别是 rules，变量值是 new，作用时钟是 institutional。"
        "仍未知的内容是 Cause not identified；残差是 Indirect effects unmeasured。"
        "这些未识别因果和间接效果仍约束后续判断。"
    )
    mechanism = (
        "机制分析在本例中不适用，理由为 Observed rule record only; no inferred "
        "mechanism or future action requested。当前任务支持观察记录；"
        "若另行推断原因，需重新确定条件和材料，不能借观察结果获得推断资格。"
    )
    return projection("local_world_model", value, [
        section("observed-event", "已发生的变化与执行权限", "事实与权限各有边界。",
            observed, {
                "local_world_model.event_records[0].kind": "证据身份为直接观察",
                "local_world_model.event_records[0].occurrence_status": "发生状态为 occurred",
                "local_world_model.event_records[0].authorization_status": "授权状态仍是 unauthorized",
                "local_world_model.event_records[0].mechanism_id": "机制记录为未记录",
            }),
        section("post-state", "更新的状态与保留的未知", "观察只改变有证据的变量。",
            state_text, {
                "local_world_model.registered_state.objects[0].variables[0].category": "变量类别是 rules",
                "local_world_model.registered_state.objects[0].variables[0].value": "变量值是 new",
                "local_world_model.registered_state.objects[0].variables[0].clock_id": "作用时钟是 institutional",
                "local_world_model.registered_state.unknowns[0].reason": "Cause not identified",
                "local_world_model.registered_state.residuals[0].reason": "Indirect effects unmeasured",
            }),
        section("mechanism-limit", "机制推断的任务边界", "未申请的机制推断没有完成。",
            mechanism, {
                "local_world_model.applicability.mechanism.status": "机制分析在本例中不适用",
                "local_world_model.applicability.mechanism.rationale": "Observed rule record only; no inferred mechanism or future action requested",
            }),
    ])


def scale_projection(*, alternative_cost=False):
    record, registries = scale_fixture()
    partition = transformations.evaluate_task_partition(
        {"x1": "z", "x2": "z"}, {"x1": "same answer", "x2": "same answer"},
    )
    assert partition["task_sufficient"] is True
    assert partition["reconstructable"] is False
    record["transformation"]["equivalence_or_sufficiency"] = partition
    record["loss"]["irrecoverable_information"] = [
        "unmeasured audit constraints" if alternative_cost else "unmeasured care constraints",
    ]
    record["responsibility"]["cost_bearers"] = [
        "synthetic reviewer" if alternative_cost else "synthetic analyst",
    ]
    record["normative"]["value_premises"] = [
        "Descriptions do not settle the normative acceptability of cost.",
    ]
    checked = transformations.validate_scale_instance(record, **registries)
    assert checked["result_state"] == "supported"
    assert checked["mapping_class"] == "same_object"
    assert set(record) == set(SCALE_SECTION_NAMES)
    selected = {
        "identity": {"purpose": deepcopy(record["identity"]["purpose"])},
        "scale": {"transformation_class": record["scale"]["transformation_class"]},
        "objects": {key: deepcopy(record["objects"][key]) for key in ("source_K", "target_K")},
        "semantics": {
            "preserved_core": deepcopy(record["semantics"]["preserved_core"]),
            "prohibited_mappings": deepcopy(record["semantics"]["prohibited_mappings"]),
            "task_preservation": {"validity_conditions": deepcopy(record["semantics"]
                ["task_preservation"]["validity_conditions"])},
        },
        "transformation": {
            key: deepcopy(record["transformation"][key])
            for key in ("claim_mode", "result_state", "equivalence_or_sufficiency")
        },
        "variables": {"dependencies": deepcopy(record["variables"]["dependencies"])},
        "evidence": {"task_checks": [{key: record["evidence"]["task_checks"][0][key]
            for key in ("task_ref", "result", "scope")}]},
        "loss": {"irrecoverable_information": deepcopy(record["loss"]["irrecoverable_information"])},
        "responsibility": {"cost_bearers": deepcopy(record["responsibility"]["cost_bearers"])},
        "normative": {key: deepcopy(record["normative"][key])
            for key in ("value_premises", "selection_kind")},
        "protection": {
            "applicability": {key: deepcopy(record["protection"]["applicability"][key])
                for key in ("object_type", "downstream_uses", "reason")},
            "safe_submission": deepcopy(record["protection"]["safe_submission"]),
        },
        "action": {key: deepcopy(record["action"][key])
            for key in ("judgment_ceiling", "action_ceiling", "stop_conditions")},
        "correction": {"repair": deepcopy(record["correction"]["repair"])},
        "lifecycle": deepcopy(record["lifecycle"]),
    }
    selected["objects"]["identity_mapping"] = {
        "classification": record["objects"]["identity_mapping"]["classification"],
    }
    sections = []
    for name in SCALE_SECTION_NAMES:
        expected = ALTERNATIVE_COST_BODY if alternative_cost and name in ALTERNATIVE_COST_BODY else SCALE_BODY
        heading, judgment, paragraph, bindings = expected[name]
        sections.append(section("scale-" + name, heading, judgment, paragraph, {
            f"{SCALE_BASE}.{name}.{path}": excerpt for path, excerpt in bindings.items()
        }))
    return projection("transformation_ledger", {"transformations": [selected]}, sections)


def recursion_projection():
    parent, event, evidence_registry, actions = recursive_fixture()
    failed = deepcopy(parent)
    failed.update(
        status="failed", stop_reason="invalid cross-scale map", can_say="bounded observed facts",
        cannot_say="dependent future", next_observation="test channel",
        continuation_risk="invented pathway",
    )
    requests = []
    blocked = recursion.execute_recursive_step(
        failed, event, action_catalog=actions, author=lambda request: requests.append(request),
        evidence_registry=evidence_registry, independent_question="next",
        incremental_gain="gain",
    )
    assert requests == []
    assert blocked["status"] == "not_run"
    assert [item["order"] for item in blocked["not_run_orders"]] == [2, 3]
    state = failed["output_state"]
    branch = {key: failed[key] for key in (
        "status", "order", "stop_reason", "can_say", "cannot_say",
        "next_observation", "continuation_risk",
    )}
    branch["output_state"] = {
        key: [{"content": state[key][0]["content"]}]
        for key in ("unknowns", "losses", "residuals", "existing_obligations")
    }
    value = {
        "branches": [branch, {key: blocked[key] for key in ("status", "order", "reason")}],
        "not_run_orders": deepcopy(blocked["not_run_orders"]),
    }
    failed_text = (
        "第一阶的状态为 failed，当前阶次为 1，停止理由是 invalid cross-scale map。"
        "当前可说的是 bounded observed facts，不可说的是 dependent future；"
        "下一观察为 test channel，继续的风险为 invented pathway。"
        "失败所阻断的是依赖这项映射的后续推断，已支持的独立观察仍可保留。"
    )
    retained = (
        "失败分支保留的未知是 choice remains uncertain，损失是 unmeasured care "
        "constraints，残差是 unmodeled cost，既有义务为 existing duty persists。"
        "停止推断不等于这些约束消失，也不等于免除既有义务。"
    )
    dependent = (
        "依赖分支的状态为没有开展，当前阶次为 2，理由仍是 invalid cross-scale map。"
        "没有开展与预测已经失败不同，不能写成已得到新的后果。"
    )
    downstream = (
        "下游第 2 阶没有开展，由推演节点 1 阻断，理由为 invalid cross-scale map。"
        "下游第 3 阶也没有开展，由推演节点 1 阻断，理由为 invalid cross-scale map。"
        "本例没有补写一个依赖失败前提的未来故事。"
    )
    return projection("recursive_lineage", value, [
        section("failed-branch", "失败后的判断边界", "第一阶失败限制了依赖分支。",
            failed_text, {
                "recursive_lineage.branches[0].status": "状态为 failed",
                "recursive_lineage.branches[0].order": "当前阶次为 1",
                "recursive_lineage.branches[0].stop_reason": "停止理由是 invalid cross-scale map",
                "recursive_lineage.branches[0].can_say": "可说的是 bounded observed facts",
                "recursive_lineage.branches[0].cannot_say": "不可说的是 dependent future",
                "recursive_lineage.branches[0].next_observation": "下一观察为 test channel",
                "recursive_lineage.branches[0].continuation_risk": "继续的风险为 invented pathway",
            }),
        section("failed-retention", "未知、损失、残差与既有义务", "合法停止仍须保留责任。",
            retained, {
                "recursive_lineage.branches[0].output_state.unknowns[0].content": "choice remains uncertain",
                "recursive_lineage.branches[0].output_state.losses[0].content": "unmeasured care constraints",
                "recursive_lineage.branches[0].output_state.residuals[0].content": "unmodeled cost",
                "recursive_lineage.branches[0].output_state.existing_obligations[0].content": "existing duty persists",
            }),
        section("dependent-not-run", "未运行的依赖分支", "未运行不能冒充后续结果。",
            dependent, {
                "recursive_lineage.branches[1].status": "状态为没有开展",
                "recursive_lineage.branches[1].order": "当前阶次为 2",
                "recursive_lineage.branches[1].reason": "理由仍是 invalid cross-scale map",
            }),
        section("downstream-not-run", "各阶次的停止范围", "阻断记录逐阶保留。",
            downstream, {
                "recursive_lineage.not_run_orders[0].order": "下游第 2 阶没有开展",
                "recursive_lineage.not_run_orders[0].blocked_by_node_id": "由推演节点 1 阻断",
                "recursive_lineage.not_run_orders[0].reason": "理由为 invalid cross-scale map",
                "recursive_lineage.not_run_orders[1].order": "下游第 3 阶也没有开展",
                "recursive_lineage.not_run_orders[1].blocked_by_node_id": "由推演节点 1 阻断",
                "recursive_lineage.not_run_orders[1].reason": "理由为 invalid cross-scale map",
            }),
    ])


def test_observed_unauthorized_event_is_not_a_mechanism_or_execution_right():
    payload = event_projection()
    paths = {atom["canonical_path"] for atom in substantive_semantic_atoms(payload)}
    assert "local_world_model.event_records[0].authorization_status" in paths
    assert "local_world_model.registered_state.unknowns[0].reason" in paths
    assert "local_world_model.applicability.mechanism.rationale" in paths
    answer, coverage = assert_complete(payload)
    assert "已发生的 e(t)" in answer
    assert "观察事实不授予继续执行的权利" in answer
    assert "不能把事件观察直接提升为已证明的机制" in answer
    assert "Indirect effects unmeasured" in answer
    assert all(entry["projection_status"] == "projected"
               for entry in coverage["typed_atom_ledger"])


def test_checked_mechanism_inference_remains_conditional_in_plain_body():
    state = frozen_state()
    event, evidence_registry = observed_event(state)
    event.update(kind="inferred", update_path="mechanism_inference",
        occurrence_status="not_occurred", authorization_status="unknown",
        channel_id="CHANNEL-1", mechanism_id="MECH-1")
    evidence_registry["EV-1"]["identity"] = "inferred"
    channel = {
        "channel_id": "CHANNEL-1", "mechanism_id": "MECH-1",
        "from_object_id": "OBJECT-1", "to_object_id": "OBJECT-1",
        "active": True, "identity_preserved": True, "acl_authorized": True,
        "evidence_refs": ["EV-CHANNEL"], "lag_seconds": 0, "capacity": 1,
        "threshold_conditions": [], "valid_from": "2026-09-30T00:00:00Z",
        "valid_until": "2026-10-01T00:00:00Z",
    }
    evidence_registry["EV-CHANNEL"] = {
        "evidence_id": "EV-CHANNEL", "identity": "observed",
        "source_refs": ["SYNTHETIC-MECHANISM"], "available_at": "2026-09-30T10:00:00Z",
        "channel_id": "CHANNEL-1", "mechanism_id": "MECH-1", "support_status": "supported",
    }
    transition = world_volume.apply_registered_event(state, event,
        evidence_registry=evidence_registry, channel_registry={"CHANNEL-1": channel})
    assert transition.event_role == "mechanism_inference"
    assert transition.evidence_identity == "inferred"
    assert transition.external_action_authorized is False
    value = {
        "event_records": [{key: event[key] for key in (
            "kind", "update_path", "occurrence_status", "authorization_status",
        )}],
        "channels": [{key: channel[key] for key in (
            "active", "identity_preserved", "acl_authorized", "capacity", "lag_seconds",
        )}],
        "registered_state": {"objects": [{"variables": [{
            "value": transition.output_state["objects"][0]["variables"][0]["value"],
        }]}]},
    }
    text = (
        "本例的证据身份是 inferred，更新方式是 mechanism_inference，"
        "发生状态是 not_occurred，授权状态为未知。"
        "通道启用为是，同一性保持为是，访问授权成立为是，容量为 1，时延为 0。"
        "条件状态中的变量值为 new。这项结果是依赖通道条件的机制推断，"
        "尚未发生；通道条件成立不能把它变成直接观察的现实事实，也没有授予执行权。"
    )
    payload = projection("local_world_model", value, [section(
        "inferred-mechanism", "机制推断的条件与事实边界", "推断仍服从条件和证据身份。",
        text, {
            "local_world_model.event_records[0].kind": "证据身份是 inferred",
            "local_world_model.event_records[0].update_path": "更新方式是 mechanism_inference",
            "local_world_model.event_records[0].occurrence_status": "发生状态是 not_occurred",
            "local_world_model.event_records[0].authorization_status": "授权状态为未知",
            "local_world_model.channels[0].active": "通道启用为是",
            "local_world_model.channels[0].identity_preserved": "同一性保持为是",
            "local_world_model.channels[0].acl_authorized": "访问授权成立为是",
            "local_world_model.channels[0].capacity": "容量为 1",
            "local_world_model.channels[0].lag_seconds": "时延为 0",
            "local_world_model.registered_state.objects[0].variables[0].value": "变量值为 new",
        },
    )])
    answer, _ = assert_complete(payload)
    assert "尚未发生" in answer
    assert "不能把它变成直接观察的现实事实" in answer
    assert "没有授予执行权" in answer


@pytest.mark.parametrize("field,value", [
    ("kind", "inferred"),
    ("authorization_status", "authorized"),
])
def test_unchanged_observation_body_cannot_cover_changed_identity_or_authorization(field, value):
    payload = event_projection()
    payload["local_world_model"]["event_records"][0][field] = value
    path = "local_world_model.event_records[0]." + field
    assert any(path in error for error in validate_reader_sections(payload))
    assert semantic_coverage(payload)["main_answer_complete"] is False


def test_all_fourteen_scale_responsibilities_reach_plain_authored_body():
    payload = scale_projection()
    record = payload["transformation_ledger"]["transformations"][0]
    assert set(record) == set(SCALE_SECTION_NAMES)
    paths = {atom["canonical_path"] for atom in typed_semantic_atoms(payload)}
    for name in SCALE_SECTION_NAMES:
        assert any(path.startswith(f"{SCALE_BASE}.{name}.") for path in paths)
    answer, _ = assert_complete(payload)
    for name in SCALE_SECTION_NAMES:
        assert SCALE_BODY[name][2] in answer
    assert "任务充分性为是；对原始状态，可重建性为否" in answer
    assert "description does not authorize intervention" in answer
    assert "unmeasured care constraints" in answer
    assert "安全提交程序在本例中不适用" in answer
    assert "退出本轮描述不能取消另行成立的既有义务" in answer


@pytest.mark.parametrize("name", SCALE_SECTION_NAMES)
def test_same_main_conclusion_cannot_omit_any_scale_responsibility(name):
    payload = scale_projection()
    payload["reader_sections"] = [value for value in payload["reader_sections"]
        if value["section_id"] != "scale-" + name]
    prefix = f"{SCALE_BASE}.{name}."
    assert payload["answer"]["direct_answer"] == DIRECT_ANSWER
    assert any(prefix in error for error in validate_reader_sections(payload))
    coverage = semantic_coverage(payload)
    assert coverage["main_answer_complete"] is False
    assert any(path.startswith(prefix) for path in coverage["substantive_unprojected_paths"])


@pytest.mark.parametrize("name", SCALE_SECTION_NAMES)
def test_every_scale_section_requires_explicit_visibility(name):
    payload = scale_projection()
    prefix = f"{SCALE_BASE}.{name}."
    missing = next(entry["canonical_path"] for entry in payload["visibility_ledger"]["entries"]
                   if entry["canonical_path"].startswith(prefix))
    payload["visibility_ledger"]["entries"] = [entry for entry in payload["visibility_ledger"]["entries"]
                                              if entry["canonical_path"] != missing]
    with pytest.raises(ValueError, match="missing semantic atom"):
        validate_visibility_ledger(payload)


@pytest.mark.parametrize("field,changed", [("task_sufficient", False), ("reconstructable", True)])
def test_finite_task_sufficiency_cannot_be_substituted_for_reconstruction(field, changed):
    payload = scale_projection()
    partition = payload["transformation_ledger"]["transformations"][0]["transformation"]["equivalence_or_sufficiency"]
    partition[field] = changed
    path = f"{SCALE_BASE}.transformation.equivalence_or_sufficiency.{field}"
    assert any(path in error for error in validate_reader_sections(payload))
    assert semantic_coverage(payload)["main_answer_complete"] is False


@pytest.mark.parametrize("replacement", [
    "其余损失见[附件](xi-kari-dossier.md)。", "仅保留结论。", "覆盖标记。",
])
def test_summary_link_or_marker_cannot_replace_the_loss_argument(replacement):
    payload = scale_projection()
    lost = next(value for value in payload["reader_sections"] if value["section_id"] == "scale-loss")
    lost["paragraphs"] = [replacement]
    lost["source_bindings"][0]["excerpt"] = replacement
    assert any(f"{SCALE_BASE}.loss.irrecoverable_information[0]" in error
               for error in validate_reader_sections(payload))
    assert semantic_coverage(payload)["main_answer_complete"] is False


def test_same_conclusion_keeps_different_cost_and_loss_paths_in_the_body():
    payload = scale_projection()
    second = scale_projection(alternative_cost=True)
    payload["transformation_ledger"]["transformations"].append(
        deepcopy(second["transformation_ledger"]["transformations"][0]),
    )
    for original in second["reader_sections"][1:]:
        authored = deepcopy(original)
        authored["section_id"] = "second-" + authored["section_id"]
        for binding in authored["source_bindings"]:
            binding["source_path"] = binding["source_path"].replace(
                "transformation_ledger.transformations[0].", "transformation_ledger.transformations[1].", 1,
            )
        payload["reader_sections"].append(authored)
    visibility(payload)
    answer, _ = assert_complete(payload)
    assert payload["answer"]["direct_answer"] == DIRECT_ANSWER
    assert "不可恢复的信息是 unmeasured care constraints" in answer
    assert "不可恢复的信息是 unmeasured audit constraints" in answer
    assert "复核成本由 synthetic analyst 承担" in answer
    assert "复核成本由 synthetic reviewer 承担" in answer
    outputs = prose.render_reader_outputs(payload)
    cut = "不可恢复的信息是 unmeasured audit constraints。"
    outputs["dossier"] += "\n" + cut
    outputs["answer"] = outputs["answer"].replace(cut, "")
    assert semantic_coverage(payload, outputs)["main_answer_complete"] is False


def protected_identity_projection():
    payload = scale_projection()
    paths = [f"{SCALE_BASE}.objects.{side}_K.definition" for side in ("source", "target")]
    for entry in payload["visibility_ledger"]["entries"]:
        if entry["canonical_path"] in paths:
            entry.update(classification="sensitive", disclosure="withhold",
                authority_refs=["fixture-privacy-authority"], protection_reason=IDENTITY_PROTECTION_REASON)
    identity = next(value for value in payload["reader_sections"] if value["section_id"] == "scale-objects")
    identity["paragraphs"] = [IDENTITY_PROTECTED_BODY]
    for binding in identity["source_bindings"]:
        if binding["source_path"] in paths:
            binding["excerpt"] = "同一性判据的具体内容为保护而不公开，原因是未取得当事人披露同意"
    return payload, paths


def test_protected_identity_retains_a_safe_bound_body_boundary():
    payload, paths = protected_identity_projection()
    answer, coverage = assert_complete(payload)
    assert "same bounded synthetic units" not in answer
    assert IDENTITY_PROTECTED_BODY in answer
    status = {entry["canonical_path"]: entry["projection_status"] for entry in coverage["typed_atom_ledger"]}
    assert all(status[path] == "withheld_for_protection" for path in paths)


def test_protected_identity_cannot_silently_disappear_from_a_v4_body():
    payload, paths = protected_identity_projection()
    identity = next(value for value in payload["reader_sections"] if value["section_id"] == "scale-objects")
    identity["source_bindings"] = [binding for binding in identity["source_bindings"]
                                   if binding["source_path"] not in paths]
    assert any(paths[0] in error for error in validate_reader_sections(payload))
    assert semantic_coverage(payload)["main_answer_complete"] is False


@pytest.mark.parametrize("renderer", [prose.render_answer, prose.render_chat_projection])
def test_protected_identity_cannot_reappear_in_an_unbound_paragraph(renderer):
    payload, _ = protected_identity_projection()
    payload["reader_sections"][0]["paragraphs"].append(
        "仍可披露判据为 same bounded synthetic units。",
    )
    with pytest.raises(ValueError) as caught:
        renderer(payload)
    assert "same bounded synthetic units" not in str(caught.value)


def test_failed_recursion_keeps_not_run_orders_and_bounded_claims():
    payload = recursion_projection()
    answer, coverage = assert_complete(payload)
    assert "状态为 failed" in answer
    assert "当前可说的是 bounded observed facts，不可说的是 dependent future" in answer
    assert "下游第 2 阶没有开展" in answer
    assert "下游第 3 阶也没有开展" in answer
    assert "既有义务为 existing duty persists" in answer
    atoms = {entry["canonical_path"]: entry for entry in coverage["typed_atom_ledger"]}
    assert atoms["recursive_lineage.branches[0].order"]["value_type"] == "number"
    assert atoms["recursive_lineage.branches[1].status"]["value_type"] == "enum"
    assert atoms["recursive_lineage.branches[0].output_state.unknowns[0].content"]["projection_status"] == "projected"


@pytest.mark.parametrize("section_id,path", [
    ("failed-branch", "recursive_lineage.branches[0].cannot_say"),
    ("failed-retention", "recursive_lineage.branches[0].output_state.unknowns[0].content"),
    ("failed-retention", "recursive_lineage.branches[0].output_state.residuals[0].content"),
    ("failed-retention", "recursive_lineage.branches[0].output_state.existing_obligations[0].content"),
    ("dependent-not-run", "recursive_lineage.branches[1].status"),
    ("downstream-not-run", "recursive_lineage.not_run_orders[1].reason"),
])
def test_unchanged_conclusion_cannot_erase_failed_branch_responsibility(section_id, path):
    payload = recursion_projection()
    payload["reader_sections"] = [value for value in payload["reader_sections"]
                                  if value["section_id"] != section_id]
    assert any(path in error for error in validate_reader_sections(payload))
    assert semantic_coverage(payload)["main_answer_complete"] is False


@pytest.mark.parametrize("terminal_kind", ["completed", "stopped"])
def test_legal_recursive_terminal_state_retains_obligations_without_inventing_another_order(terminal_kind):
    parent, event, evidence_registry, actions = recursive_fixture()
    calls = []
    if terminal_kind == "stopped":
        parent.update(order=3, status="failed", stop_reason="third-order mechanism failed")
    terminal = recursion.execute_recursive_step(
        parent, event, action_catalog=actions, author=lambda request: calls.append(request),
        evidence_registry=evidence_registry, independent_question=None,
        incremental_gain=None,
    )
    assert calls == []
    assert terminal["status"] == terminal_kind
    assert terminal["output_state"]["existing_obligations"] == parent["output_state"]["existing_obligations"]
    if terminal_kind == "completed":
        state = {"status": terminal["status"], "completion_reason": terminal["completion_reason"]}
        text = "本分支状态为 completed，完成理由为 no_independent_next_question；没有独立的新问题时可以停止。"
        bindings = {
            "recursive_lineage.branches[0].status": "状态为 completed",
            "recursive_lineage.branches[0].completion_reason": "完成理由为 no_independent_next_question",
        }
    else:
        assert terminal["order"] == 3
        assert terminal["not_run_orders"] == []
        state = {"status": terminal["status"], "order": terminal["order"], "stop_reason": terminal["stop_reason"]}
        text = "本分支状态为已停止，停止阶次为 3，理由为 third-order mechanism failed；没有虚构第四阶。"
        bindings = {
            "recursive_lineage.branches[0].status": "状态为已停止",
            "recursive_lineage.branches[0].order": "停止阶次为 3",
            "recursive_lineage.branches[0].stop_reason": "理由为 third-order mechanism failed",
        }
    state["output_state"] = {"existing_obligations": [{"content": terminal["output_state"]["existing_obligations"][0]["content"]}]}
    text += "既有义务仍为 existing duty persists，停止推断不会免除这项义务。"
    bindings["recursive_lineage.branches[0].output_state.existing_obligations[0].content"] = "既有义务仍为 existing duty persists"
    payload = projection("recursive_lineage", {"branches": [state]}, [
        section("terminal", "合法停止的范围", "停止仍保留已经成立的责任。", text, bindings),
    ])
    answer, _ = assert_complete(payload)
    assert text in answer


def test_independent_no_new_action_path_keeps_its_unknowns_residuals_and_duties():
    parent, event, evidence_registry, actions = recursive_fixture()
    child = recursion.execute_recursive_step(
        parent, event, action_catalog=actions,
        author=lambda request: {"possible_choice_ids": ["WAIT"], "choice_basis": "conditional no new action"},
        evidence_registry=evidence_registry, independent_question="Available choices?",
        incremental_gain="New resources",
    )
    assert child["author_request"]["no_action_option_id"] == "WAIT"
    assert "selected_action" not in child
    assert child["output_state"]["unknowns"] == parent["output_state"]["unknowns"]
    assert child["output_state"]["residuals"] == parent["output_state"]["residuals"]
    state = {key: child[key] for key in ("status", "order", "evidence_identity", "declared_evidence_grade")}
    state["conditions"] = deepcopy(child["conditions"])
    state["author_response"] = {"choice_basis": child["author_response"]["choice_basis"]}
    state["output_state"] = {key: [{"content": child["output_state"][key][0]["content"]}]
        for key in ("unknowns", "losses", "residuals", "existing_obligations")}
    text = (
        "第二阶的当前状态为启用，当前阶次为 2，证据身份仍是 simulated，证据等级仍为低。"
        "继承条件为 assume current rules remain，新增条件为 conditional spend occurs。"
        "可讨论的选择依据为 conditional no new action，没有替行动者选定行动。"
        "未知仍为 choice remains uncertain，损失仍为 unmeasured care constraints，"
        "残差仍为 unmodeled cost，既有义务仍为 existing duty persists。"
        "不新增干预不能取消维护或其他已经成立的义务。"
    )
    payload = projection("recursive_lineage", {"branches": [state]}, [
        section("independent", "独立分支的条件与义务", "独立可讨论的路径仍保留约束。", text, {
            "recursive_lineage.branches[0].status": "当前状态为启用",
            "recursive_lineage.branches[0].order": "当前阶次为 2",
            "recursive_lineage.branches[0].evidence_identity": "证据身份仍是 simulated",
            "recursive_lineage.branches[0].declared_evidence_grade": "证据等级仍为低",
            "recursive_lineage.branches[0].conditions[0]": "assume current rules remain",
            "recursive_lineage.branches[0].conditions[1]": "conditional spend occurs",
            "recursive_lineage.branches[0].author_response.choice_basis": "conditional no new action",
            "recursive_lineage.branches[0].output_state.unknowns[0].content": "choice remains uncertain",
            "recursive_lineage.branches[0].output_state.losses[0].content": "unmeasured care constraints",
            "recursive_lineage.branches[0].output_state.residuals[0].content": "unmodeled cost",
            "recursive_lineage.branches[0].output_state.existing_obligations[0].content": "existing duty persists",
        }),
    ])
    answer, _ = assert_complete(payload)
    assert "没有替行动者选定行动" in answer
    assert "既有义务仍为 existing duty persists" in answer
