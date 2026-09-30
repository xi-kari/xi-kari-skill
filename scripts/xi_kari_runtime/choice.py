"""Bounded recommendations, real no-new-action decisions and atomic permission."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from .canonical_json import sha256_json
from .causality import claim_support
from .problem_contract import parse_instant


class ChoiceError(ValueError):
    """A choice exceeds its factual, normative or permission boundary."""


def _required(record: Mapping[str, Any], fields: tuple[str, ...]) -> None:
    if any(not record.get(field) for field in fields):
        raise ChoiceError("choice lacks a required basis, scope or control")


def validate_action_comparison(
    record: Mapping[str, Any], *, action_state: Mapping[str, Any], claim_constraints: Mapping[str, Any]
) -> dict[str, Any]:
    _required(record, ("comparison_id", "scope", "options", "no_action_option_id", "normative_premises", "affected_positions", "cost_distribution", "reasons", "counterarguments", "switch_conditions", "baseline_time", "natural_changes", "observation_plan", "reopen_conditions", "responsible_subject"))
    options = record["options"]
    if not isinstance(options, list) or len({option.get("option_id") for option in options}) != len(options):
        raise ChoiceError("choice option identities must be unique")
    baselines = [option for option in options if option.get("option_kind") == "no_action"]
    if len(baselines) != 1 or baselines[0].get("option_id") != record["no_action_option_id"] or record["no_action_option_id"] != action_state.get("no_action_option_id"):
        raise ChoiceError("comparison requires exactly one bound no_action baseline")
    available = {option["option_id"]: option for option in action_state["available_actions"]}
    for option in options:
        origin = available.get(option.get("option_id"))
        if origin is None or any(origin.get(key) != option.get(key) for key in ("option_kind", "action_type", "target_object")):
            raise ChoiceError("comparison option differs from the actual feasible action set")
    if record.get("existing_items") != action_state.get("existing_obligations"):
        raise ChoiceError("no_action comparison must preserve existing obligations and conditions")
    if record.get("selection_status") not in {"recommended", "undecided"} or record.get("execution_status") != "analysis_only" or "selected_action" in record:
        raise ChoiceError("comparison or recommendation cannot become external selection")
    if record["selection_status"] == "recommended" and record.get("recommended_option_id") not in {option["option_id"] for option in options}:
        raise ChoiceError("recommended option does not resolve")
    if claim_support(record.get("normative_basis_claim_ids", []), claim_constraints) != "supported":
        raise ChoiceError("recommendation requires its own normative argument")
    parse_instant(record["baseline_time"], field="comparison baseline")
    result = deepcopy(dict(record))
    result["permission_effect"] = "none"
    result["action_state_sha256"] = sha256_json(action_state)
    return result


def validate_no_new_action_choice(
    record: Mapping[str, Any], *, comparison: Mapping[str, Any],
    decision_evidence_registry: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    _required(record, ("subject", "scope", "chosen_baseline", "evidence_refs"))
    if record.get("permission_effect") != "none" or "selected_action" in record or "authorization_ref" in record:
        raise ChoiceError("no-new-action decision cannot grant external authority")
    if record["chosen_baseline"] != comparison["no_action_option_id"] or record["scope"] != comparison["scope"] or record.get("existing_items") != comparison.get("existing_items"):
        raise ChoiceError("no-new-action decision differs from its comparison or existing obligations")
    for ref in record["evidence_refs"]:
        evidence = decision_evidence_registry.get(ref)
        if not isinstance(evidence, Mapping) or evidence.get("evidence_id") != ref or evidence.get("identity") != "observed" or not evidence.get("source_refs") or evidence.get("decision_subject") != record["subject"] or evidence.get("scope") != record["scope"] or evidence.get("chosen_baseline") != record["chosen_baseline"]:
            raise ChoiceError("actual no-new-action choice requires matching observed decision evidence")
    return deepcopy(dict(record))


def validate_external_selection(
    record: Mapping[str, Any], *, comparison: Mapping[str, Any],
    authorization_registry: Mapping[str, Mapping[str, Any]],
    mechanism_registry: Mapping[str, Mapping[str, Any]], review_registry: Mapping[str, Mapping[str, Any]],
    actor_registry: Mapping[str, Mapping[str, Any]], interest_registry: Mapping[tuple[str, str], Mapping[str, Any]],
    claim_constraints: Mapping[str, Any], used_at: str,
    outer_impact_domain: str, downstream_impact_domain: str,
) -> dict[str, Any]:
    _required(record, ("selection_id", "selection_type", "proposer", "selected_option_id", "authorization_tuple_id", "normative_premises", "affected_positions", "low_power_positions", "protection_floor_bindings", "coercion_and_choice", "minimum_harm", "proportionality", "independent_review_ref", "O_records", "control_mechanism_refs"))
    if record["selection_type"] not in {"SEL-AGT", "SEL-GOV"}:
        raise ChoiceError("SEL-SYS cannot receive external authorization")
    options = [option for option in comparison["options"] if option["option_id"] == record["selected_option_id"]]
    if len(options) != 1 or options[0].get("option_kind") != "external_action":
        raise ChoiceError("selected_action must refer to one external_action")
    option = options[0]
    atom = authorization_registry.get(record["authorization_tuple_id"])
    now = parse_instant(used_at, field="external action use time")
    if not isinstance(atom, Mapping) or atom.get("tuple_id") != record["authorization_tuple_id"] or atom.get("status") != "valid" or atom.get("revoked_at") is not None or not atom.get("source_ref"):
        raise ChoiceError("external action requires one current effective atomic authorization")
    for key, other in (("decision_subject", "decision_subject"), ("target_object", "target_object"), ("single_action", "action_type"), ("territory", "territory"), ("validity_interval", "validity_interval")):
        if not isinstance(atom.get(key), (str, Mapping)) or atom.get(key) != option.get(other):
            raise ChoiceError("external action differs from its single atomic authorization tuple")
    interval = atom["validity_interval"]
    if not parse_instant(interval["starts_at"], field="authorization start") <= now < parse_instant(interval["ends_at"], field="authorization expiry"):
        raise ChoiceError("external action authorization is expired or not effective")
    def supported(refs: object) -> None:
        if claim_support(refs, claim_constraints) != "supported":
            raise ChoiceError("external action gate lacks supported evidence")
    supported(atom.get("basis_claim_ids", []))
    premises = set(record["normative_premises"])
    if not premises or premises - {"N1", "N2", "N3", "N4", "N5"} or premises == {"N1"}:
        raise ChoiceError("authorization requires explicit N premises beyond N1 alone")
    supported(record.get("normative_basis_claim_ids", []))
    if "value_conflicts" not in record or "objections" not in record or any(objection.get("status") in {"open", "protected_and_pending", "unresolved_action_paused"} for objection in record["objections"]):
        raise ChoiceError("unresolved substantive conflict or objection blocks authorization")
    if not isinstance(record["value_conflicts"], list) or any(not conflict.get("conflict_id") or conflict.get("status") not in {"resolved", "bounded_for_this_choice"} for conflict in record["value_conflicts"]):
        raise ChoiceError("unresolved value conflict blocks authorization")
    checks = record["coercion_and_choice"]
    names = {"no_coercion", "no_default_lock", "understandable_information", "decision_capacity", "safe_refusal", "real_exit"}
    if set(checks) != names:
        raise ChoiceError("authorization requires all refusal and exit checks")
    for check in checks.values():
        if check.get("status") != "passed":
            raise ChoiceError("unknown consent or exit conditions cannot grant authorization")
        supported(check.get("basis_claim_ids", []))
    bindings = record["protection_floor_bindings"]
    if not isinstance(bindings, list) or len(bindings) != 10 or {item.get("pf_id") for item in bindings} != {f"PF-{i}" for i in range(1, 11)}:
        raise ChoiceError("authorization requires the complete unique protection floor")
    pure_nonhuman = outer_impact_domain == downstream_impact_domain == "nonhuman_only"
    active = set()
    for binding in bindings:
        _required(binding, ("reason", "expires_at"))
        if parse_instant(binding["expires_at"], field="protection expiry") <= now:
            raise ChoiceError("protection floor has expired")
        if binding.get("status") == "not_applicable":
            if not pure_nonhuman:
                raise ChoiceError("human or downstream impact cannot waive the protection floor")
        elif binding.get("status") == "active" and binding.get("check_status") == "passed":
            active.add(binding["pf_id"])
            supported(binding.get("basis_claim_ids", []))
            if not binding.get("mechanism_refs") or set(binding["mechanism_refs"]) - set(record["control_mechanism_refs"]):
                raise ChoiceError("protection mechanism does not bind the selected controls")
        else:
            raise ChoiceError("protection failure or unknown cannot be offset by benefits")
    if set(record.get("rights_floor", [])) != active:
        raise ChoiceError("rights floor differs from current active protection bindings")
    required_controls = {"stop", "safe_submission", "anti_retaliation", "appeal", "independent_review", "rollback", "remedy", "residual_harm_tracking", "version_writeback", "expiry"}
    controls = []
    for ref in record["control_mechanism_refs"]:
        control = mechanism_registry.get(ref)
        if not isinstance(control, Mapping) or control.get("mechanism_id") != ref or control.get("owner") not in actor_registry or parse_instant(control["expires_at"], field="control expiry") <= now:
            raise ChoiceError("correction control does not resolve to a current responsible mechanism")
        supported(control.get("operability_claim_ids", []))
        controls.append(control)
    if {control["kind"] for control in controls} != required_controls:
        raise ChoiceError("authorization requires every usable correction control")
    for binding in bindings:
        if binding["status"] != "active":
            continue
        owners = binding.get("mechanism_bindings", [])
        if not isinstance(owners, list) or len(owners) != len(binding["mechanism_refs"]) or {item.get("mechanism_ref") for item in owners} != set(binding["mechanism_refs"]):
            raise ChoiceError("protection needs each actual mechanism owner binding")
        if any(mechanism_registry[item["mechanism_ref"]]["owner"] != item.get("responsible_subject") for item in owners):
            raise ChoiceError("protection responsible subject differs from actual mechanism owner")
    for field in ("minimum_harm", "proportionality"):
        if record[field].get("selected") is not True or not record[field].get("reason"):
            raise ChoiceError("minimum harm and proportionality require explicit independent review")
        supported(record[field].get("basis_claim_ids", []))
    procedures = record["O_records"]
    if set(procedures) != {"O1", "O2", "O3", "O4"}:
        raise ChoiceError("authorization requires O1 through O4")
    for i in range(1, 5):
        row = procedures[f"O{i}"]
        if not row.get("record_id") or any(row.get(key) != value for key, value in {"comparison_id": comparison["comparison_id"], "selected_option_id": option["option_id"], "authorization_tuple_id": atom["tuple_id"], "previous_record_ref": procedures[f"O{i-1}"]["record_id"] if i > 1 else None}.items()):
            raise ChoiceError("O1 through O4 do not bind the same choice and atomic scope")
        supported(row.get("basis_claim_ids", []))
    review = review_registry.get(record["independent_review_ref"])
    if not isinstance(review, Mapping) or review.get("review_id") != record["independent_review_ref"] or review.get("selection_id") != record["selection_id"]:
        raise ChoiceError("independent review does not resolve to this selection")
    supported(review.get("basis_claim_ids", []))
    actor_ids = {record["proposer"], atom.get("issuer"), atom["decision_subject"], review.get("reviewer")}
    if any(actor not in actor_registry or actor_registry[actor].get("actor_id") != actor for actor in actor_ids) or atom["issuer"] in {record["proposer"], atom["decision_subject"]} or review["reviewer"] in {record["proposer"], atom["decision_subject"]}:
        raise ChoiceError("canonical actors and independent issuers/reviewers are required")
    for independent in (atom["issuer"], review["reviewer"]):
        for dependent in (record["proposer"], atom["decision_subject"]):
            relation = interest_registry.get((independent, dependent))
            if not isinstance(relation, Mapping) or relation.get("actors") != [independent, dependent] or set(relation.get("relationships", {})) != {"funding", "evaluation", "identity", "promotion", "control", "commercial"} or any(status != "none_found" for status in relation["relationships"].values()):
                raise ChoiceError("actual interest relationships do not support independence")
            supported(relation.get("basis_claim_ids", []))
    return {"selection_id": record["selection_id"], "status": "authorized", "c12_gate": "passed", "selected_action": {"option_id": option["option_id"], **{key: deepcopy(atom[key]) for key in ("decision_subject", "target_object", "single_action", "territory", "validity_interval")}}, "authorization_tuple_id": atom["tuple_id"], "selection_sha256": sha256_json(record), "comparison_sha256": sha256_json(comparison), "used_at": used_at}


class IsolatedChoiceExecutor:
    """One run's explicitly bound local actions and effective stop signal."""
    def __init__(self, selection_id: str, actions: Mapping[str, Any], *, authorizer: Any = None):
        if not selection_id or not actions or any(not callable(action) for action in actions.values()):
            raise ChoiceError("isolated executor requires explicit bounded action callables")
        self.selection_id = selection_id
        self.actions = dict(actions)
        self.authorizer = authorizer
        self.stopped = False
        self.executed_option_ids: list[str] = []
        self._stop_receipt: dict[str, Any] | None = None

    def execute(self, option_id: str) -> dict[str, Any]:
        if self.stopped:
            raise ChoiceError("isolated executor is stopped")
        if option_id not in self.actions:
            raise ChoiceError("isolated executor cannot expand its bound action set")
        if not callable(self.authorizer):
            raise ChoiceError("isolated executor requires fresh atomic authorization before execution")
        checked = self.authorizer(option_id)
        if not isinstance(checked, Mapping) or checked.get("status") != "authorized" or checked.get("selection_id") != self.selection_id or checked.get("selected_action", {}).get("option_id") != option_id or checked.get("c12_gate") != "passed":
            raise ChoiceError("fresh atomic authorization does not cover the bound action")
        result = self.actions[option_id]()
        self.executed_option_ids.append(option_id)
        try:
            content_sha256 = sha256_json(result)
        except (ValueError, TypeError):
            content_sha256 = None
        return {"selection_id": self.selection_id, "option_id": option_id, "application_execution": "returned", "return_content_sha256": content_sha256, "external_state": "not_evaluated", "consequences": "not_evaluated"}

    def stop(self, reason: str, *, received_at: str) -> dict[str, Any]:
        if not reason:
            raise ChoiceError("stop requires a registered reason")
        parse_instant(received_at, field="stop receipt time")
        self.stopped = True
        self._stop_receipt = {"selection_id": self.selection_id, "executor_status": "stopped", "stop_reached_executor": True, "received_at": received_at, "reason": reason, "before_any_execution": not self.executed_option_ids, "executed_option_ids": list(self.executed_option_ids), "consequences": "not_evaluated"}
        return deepcopy(self._stop_receipt)

    def validates_stop(self, receipt: Mapping[str, Any]) -> bool:
        return self.stopped and self._stop_receipt is not None and receipt == self._stop_receipt


def transition_choice_state(
    record: Mapping[str, Any], new_state: str, *, at: str, responsible_subject: str,
    basis_refs: list[str], executor_receipt: Mapping[str, Any] | None = None,
    restoration_receipt: Mapping[str, Any] | None = None,
    formal_transfer_refs: list[str] | None = None,
    transfer_registry: Mapping[str, Mapping[str, Any]] | None = None,
    claim_constraints: Mapping[str, Any] | None = None,
    executor: IsolatedChoiceExecutor | None = None,
) -> dict[str, Any]:
    states = {"draft", "under_review", "authorized", "paused", "stopped", "rolled_back", "closed"}
    previous = record.get("status")
    if previous not in states or new_state not in states or previous == "closed" or not responsible_subject or not basis_refs:
        raise ChoiceError("choice state transition is invalid or lacks responsibility")
    parse_instant(at, field="choice transition time")
    if new_state == "authorized":
        raise ChoiceError("authorized transition requires recomputing the full atomic choice validator")
    if new_state == "stopped" and (not isinstance(executor, IsolatedChoiceExecutor) or executor.selection_id != record.get("selection_id") or not isinstance(executor_receipt, Mapping) or not executor.validates_stop(executor_receipt)):
        raise ChoiceError("stopped state requires the actual executor and its effective matching signal")
    if new_state == "stopped" and (not isinstance(executor_receipt, Mapping) or executor_receipt.get("selection_id") != record.get("selection_id") or executor_receipt.get("executor_status") != "stopped" or executor_receipt.get("stop_reached_executor") is not True or parse_instant(executor_receipt["received_at"], field="executor stop time") > parse_instant(at, field="state transition time")):
        raise ChoiceError("stopped state requires the matching actual executor stop receipt")
    if new_state == "rolled_back" and (not isinstance(restoration_receipt, Mapping) or restoration_receipt.get("selection_id") != record.get("selection_id") or not restoration_receipt.get("restored_state_sha256") or not restoration_receipt.get("remedy_started_refs") or not restoration_receipt.get("version_writeback_ref")):
        raise ChoiceError("rolled_back requires actual restoration, remedy start and version writeback")
    if new_state == "rolled_back" and any(claim_support(restoration_receipt.get(field, []), claim_constraints or {}) != "supported" for field in ("restoration_claim_ids", "remedy_started_claim_ids", "version_writeback_claim_ids")):
        raise ChoiceError("rolled_back requires evidenced actual restoration and remedy/version effects")
    if new_state == "closed":
        open_ids = {identifier for field in ("open_harm_ids", "open_appeal_ids", "open_remedy_ids", "open_record_ids") for identifier in record.get(field, [])}
        if open_ids and not formal_transfer_refs:
            raise ChoiceError("open harm, appeal, remedy or record duties prevent closed")
        if formal_transfer_refs:
            accepted = set()
            for ref in formal_transfer_refs:
                transfer = (transfer_registry or {}).get(ref)
                if not isinstance(transfer, Mapping) or transfer.get("transfer_id") != ref or transfer.get("selection_id") != record["selection_id"] or not transfer.get("recipient") or claim_support(transfer.get("accepted_claim_ids", []), claim_constraints or {}) != "supported":
                    raise ChoiceError("formal transfer requires the actual recipient's evidenced acceptance")
                accepted.update(transfer.get("accepted_obligation_ids", []))
            if open_ids - accepted:
                raise ChoiceError("formal transfer does not cover every open responsibility")
    result = deepcopy(dict(record))
    history = result.setdefault("history", [])
    if history and parse_instant(at, field="transition time") <= parse_instant(history[-1]["at"], field="previous transition"):
        raise ChoiceError("choice state history must append in time")
    history.append({"previous_state": previous, "state": new_state, "at": at, "responsible_subject": responsible_subject, "basis_refs": list(basis_refs), "executor_receipt": deepcopy(executor_receipt), "restoration_receipt": deepcopy(restoration_receipt), "formal_transfer_refs": list(formal_transfer_refs or [])})
    result["status"] = new_state
    result["permission_effect"] = "none"
    return result


__all__ = ("ChoiceError", "validate_action_comparison", "validate_no_new_action_choice", "validate_external_selection", "IsolatedChoiceExecutor", "transition_choice_state")
