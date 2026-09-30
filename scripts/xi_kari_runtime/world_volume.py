"""Pure v8.3 semantics for a local multi-circle world volume.

This module deliberately has no run-directory, phase, lease, host, or publication
authority.  It validates authored semantic documents and returns deterministic
state differences without mutating the supplied volume.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import copy
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from .authority import repository_root as resolve_repository_root


AXES = tuple("AXTOCRINJ")
CLOCK_KINDS = frozenset(
    {"immediate", "interaction", "organizational", "institutional", "long-term"}
)
REQUIRED_WORLD_ONTOLOGY = frozenset(
    {
        "V83-CANON-JOINT-STATE",
        "V83-CANON-DUAL-CONDITIONS",
        "V83-CANON-EVENT",
    }
)
_ROOT = Path(__file__).resolve().parents[2]
_DURATION_RE = re.compile(
    r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?$"
)


class WorldVolumeError(ValueError):
    """Raised when an Omega document violates v8.3 world semantics."""


def _duration_seconds(value: object) -> float | None:
    if not isinstance(value, str):
        return None
    match = _DURATION_RE.fullmatch(value)
    if match is None or all(part is None for part in match.groups()):
        return None
    days, hours, minutes, seconds = (
        float(part or 0) for part in match.groups()
    )
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


@dataclass(frozen=True, slots=True)
class StateDiff:
    """Deterministic semantic delta produced by one declared event."""

    state_diff_id: str
    source_volume_sha256: str
    event_id: str
    evidence_refs: tuple[str, ...]
    changed_positions: tuple[str, ...]
    unchanged_positions: tuple[str, ...]
    changed_relations: tuple[str, ...]
    advanced_clocks: tuple[str, ...]
    inherited_unknown_ids: tuple[str, ...]
    inherited_residual_ids: tuple[str, ...]
    position_deltas: tuple[dict[str, Any], ...]
    relation_deltas: tuple[dict[str, Any], ...]
    clock_deltas: tuple[dict[str, Any], ...]
    relation_delta_sha256: str
    result_volume_sha256: str

    def replay(self, volume: Mapping[str, object]) -> dict[str, Any]:
        """Apply this immutable delta to an exact source Omega snapshot."""

        return replay_state_diff(volume, self)

    def replay_sha256(self, volume: Mapping[str, object]) -> str:
        """Return the semantic Omega hash for a replayed snapshot."""

        snapshot = _native_snapshot(
            volume, label="replayed world volume", error_type=WorldVolumeError
        )
        if not isinstance(snapshot, dict):
            raise WorldVolumeError("replayed world volume must be a mapping")
        return _semantic_volume_sha256(snapshot)


def _native_snapshot(value: object, *, label: str, error_type: type[ValueError]) -> Any:
    try:
        snapshot = copy.deepcopy(value)
    except (MemoryError, RecursionError, TypeError, ValueError) as error:
        raise error_type(f"{label} cannot be snapshotted: {error}") from error

    def check(item: object) -> None:
        if type(item) is dict:
            for key, child in item.items():
                if type(key) is not str:
                    raise error_type(f"{label} has a non-native JSON key")
                check(child)
            return
        if type(item) is list:
            for child in item:
                check(child)
            return
        if type(item) not in {str, int, float, bool, type(None)}:
            raise error_type(f"{label} contains a non-native JSON value")

    check(snapshot)
    return snapshot


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _semantic_volume_sha256(volume: Mapping[str, Any]) -> str:
    semantic = copy.deepcopy(dict(volume))
    semantic.pop("evidence_state", None)
    return _canonical_sha256(semantic)


def _same_json_value(left: object, right: object) -> bool:
    return type(left) is type(right) and left == right


def _value_sha256(value: object) -> str:
    return _canonical_sha256(value)


def _advance_clock_time(current_time: str, delta: str) -> str:
    seconds = _duration_seconds(delta)
    if seconds is None or seconds <= 0:
        raise WorldVolumeError("clock delta must be a positive parseable duration")
    try:
        instant = datetime.fromisoformat(current_time.replace("Z", "+00:00"))
    except ValueError as error:
        raise WorldVolumeError("clock has an invalid current_time") from error
    result = instant + timedelta(seconds=seconds)
    return result.isoformat().replace("+00:00", "Z")


def _world_evidence_target_catalog(
    volume: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    """Derive the runtime-owned target paths covered by every evidence alias.

    Evidence aliases are not sufficient proof by themselves: the same alias can
    only support a field when the frozen XK3 claim explicitly binds that exact
    target path and value hash.  The catalog is derived from the authored Omega
    and deliberately excludes ``evidence_state`` so its hashes are stable before
    and after runtime binding.
    """

    targets: dict[str, dict[str, Any]] = {}
    by_ref: dict[str, dict[tuple[str, str], dict[str, Any]]] = {}

    def visit(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if key == "evidence_state":
                    continue
                child_path = f"{path}.{key}" if path else str(key)
                if key in {"evidence_refs", "authorization_evidence_refs"}:
                    if not isinstance(child, Sequence) or isinstance(child, (str, bytes)):
                        continue
                    relation = (
                        "authorization"
                        if key == "authorization_evidence_refs"
                        else "context"
                    )
                    target_path = path or "$"
                    target_value = _canonical_sha256(value)
                    target = {
                        "target_path": target_path,
                        "target_sha256": target_value,
                        "relation": relation,
                    }
                    targets[target_path] = {
                        "target_path": target_path,
                        "target_sha256": target_value,
                    }
                    for ref in child:
                        if isinstance(ref, str) and ref:
                            by_ref.setdefault(ref, {})[(target_path, relation)] = target
                    continue
                visit(child, child_path)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for index, child in enumerate(value):
                child_path = f"{path}[{index}]" if path else f"[{index}]"
                visit(child, child_path)

    visit(volume, "")
    return targets, {
        ref: [entry for _key, entry in sorted(entries.items())]
        for ref, entries in sorted(by_ref.items())
    }


def world_evidence_target_catalog(
    volume: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Return deterministic evidence-alias target paths for an authored Omega."""

    _targets, by_ref = _world_evidence_target_catalog(volume)
    return copy.deepcopy(by_ref)


def world_evidence_target_hashes(volume: Mapping[str, Any]) -> dict[str, str]:
    """Return target-path hashes used to bind XK3 claims to XK5 fields."""

    targets, _by_ref = _world_evidence_target_catalog(volume)
    return {path: value["target_sha256"] for path, value in sorted(targets.items())}


def _repository_root(repository_root: Path | None) -> Path:
    try:
        return resolve_repository_root(Path(repository_root or _ROOT))
    except ValueError as error:
        raise WorldVolumeError(f"repository authority is invalid: {error}") from error


@lru_cache(maxsize=None)
def _schema_validator(schema_name: str, root_value: str) -> Draft202012Validator:
    path = Path(root_value) / "schemas" / schema_name
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorldVolumeError(f"runtime schema is unavailable: {path}: {error}") from error
    Draft202012Validator.check_schema(schema)
    resources = Registry()
    for candidate in sorted((Path(root_value) / "schemas").glob("*.json")):
        document = json.loads(candidate.read_text(encoding="utf-8"))
        identity = document.get("$id")
        if isinstance(identity, str) and identity:
            resources = resources.with_resource(identity, Resource.from_contents(document))
    return Draft202012Validator(schema, format_checker=FormatChecker(), registry=resources)


def _validate_schema(
    schema_name: str,
    value: Mapping[str, object],
    *,
    label: str,
    error_type: type[ValueError],
    repository_root: Path | None = None,
) -> None:
    errors = sorted(
        _schema_validator(
            schema_name, str(_repository_root(repository_root))
        ).iter_errors(value),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise error_type(f"invalid {label} at {location}: {error.message}")


@lru_cache(maxsize=None)
def _ontology_ids(root_value: str) -> frozenset[str]:
    identifiers: set[str] = set()
    inventory_root = Path(root_value) / "references" / "ontology" / "inventory"
    for path in sorted(inventory_root.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            identifier = record.get("concept_id", record.get("id"))
            if isinstance(identifier, str):
                identifiers.add(identifier)
    if not identifiers:
        raise WorldVolumeError("current v8.3 ontology inventory is unavailable")
    return frozenset(identifiers)


@lru_cache(maxsize=None)
def _source_anchor_ids(root_value: str) -> frozenset[str]:
    path = Path(root_value) / "references" / "source" / "v8.3" / "indexes" / "anchors.json"
    try:
        index = json.loads(path.read_text(encoding="utf-8"))
        identifiers = {*index["paragraphs"], *index["tables"]}
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise WorldVolumeError(
            f"current v8.3 source anchor index is unavailable: {error}"
        ) from error
    if not identifiers or any(not isinstance(item, str) for item in identifiers):
        raise WorldVolumeError("current v8.3 source anchor index is invalid")
    return frozenset(identifiers)


def _declared_source_anchors(value: object) -> set[str]:
    declared: set[str] = set()
    if isinstance(value, Mapping):
        anchors = value.get("source_anchors")
        if isinstance(anchors, Sequence) and not isinstance(anchors, (str, bytes)):
            declared.update(anchor for anchor in anchors if isinstance(anchor, str))
        for child in value.values():
            declared.update(_declared_source_anchors(child))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for child in value:
            declared.update(_declared_source_anchors(child))
    return declared


def _evidence_ref_groups(
    value: object,
) -> tuple[list[tuple[str, ...]], list[tuple[str, ...]]]:
    descriptive: list[tuple[str, ...]] = []
    authorization: list[tuple[str, ...]] = []

    def visit(item: object) -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                if key in {"evidence_refs", "authorization_evidence_refs"}:
                    if isinstance(child, Sequence) and not isinstance(
                        child, (str, bytes)
                    ):
                        refs = tuple(ref for ref in child if isinstance(ref, str))
                        if key == "authorization_evidence_refs":
                            authorization.append(refs)
                        else:
                            descriptive.append(refs)
                    continue
                if key != "evidence_state":
                    visit(child)
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
            for child in item:
                visit(child)

    visit(value)
    return descriptive, authorization


def _validate_evidence_state(
    volume: Mapping[str, Any],
    *,
    evidence_ledger: Mapping[str, Any] | None,
    expected_run_id: str | None,
) -> None:
    state = volume.get("evidence_state")
    if not isinstance(state, Mapping):
        raise WorldVolumeError("XK5 evidence_state is missing")
    raw_bindings = state.get("bindings")
    if not isinstance(raw_bindings, list) or not raw_bindings:
        raise WorldVolumeError("XK5 evidence_state has no support bindings")
    bindings: dict[str, Mapping[str, Any]] = {}
    for binding in raw_bindings:
        if not isinstance(binding, Mapping):
            raise WorldVolumeError("XK5 evidence_state binding is not an object")
        evidence_ref = binding.get("evidence_ref")
        if not isinstance(evidence_ref, str) or not evidence_ref:
            raise WorldVolumeError("XK5 evidence_state binding has no evidence_ref")
        if evidence_ref in bindings:
            raise WorldVolumeError(
                f"duplicate XK5 evidence_state binding: {evidence_ref}"
            )
        bindings[evidence_ref] = binding

    descriptive_groups, authorization_groups = _evidence_ref_groups(volume)
    referenced = {
        evidence_ref
        for group in (*descriptive_groups, *authorization_groups)
        for evidence_ref in group
    }
    unresolved = referenced - set(bindings)
    if unresolved:
        raise WorldVolumeError(
            "evidence reference does not resolve through XK5 evidence_state: "
            f"{sorted(unresolved)}"
        )
    unused = set(bindings) - referenced
    if unused:
        raise WorldVolumeError(
            f"XK5 evidence_state contains unused bindings: {sorted(unused)}"
        )

    if evidence_ledger is None:
        _target_paths, expected_targets_by_ref = _world_evidence_target_catalog(volume)
        for evidence_ref, binding in bindings.items():
            if "targets" not in binding:
                continue
            if binding.get("targets") != expected_targets_by_ref.get(evidence_ref, []):
                raise WorldVolumeError(
                    f"XK5 runtime target bindings differ from authored fields: {evidence_ref}"
                )
        if expected_run_id is not None:
            raise WorldVolumeError(
                "frozen XK3 evidence ledger is required with expected_run_id"
            )
        return
    if expected_run_id is None or not isinstance(expected_run_id, str):
        raise WorldVolumeError("expected XK3 run_id is required")
    ledger_run_id = evidence_ledger.get("run_id")
    if ledger_run_id != expected_run_id or state.get("run_id") != ledger_run_id:
        raise WorldVolumeError("evidence_state run_id differs from frozen XK3")
    if state.get("xk3_evidence_ledger_sha256") != _canonical_sha256(
        evidence_ledger
    ):
        raise WorldVolumeError("evidence_state hash differs from frozen XK3")

    claims = evidence_ledger.get("claims")
    evidence = evidence_ledger.get("evidence")
    support_edges = evidence_ledger.get("support_edges")
    if not all(isinstance(items, list) for items in (claims, evidence, support_edges)):
        raise WorldVolumeError("frozen XK3 evidence ledger is incomplete")
    claim_by_id = {
        claim.get("claim_id"): claim
        for claim in claims
        if isinstance(claim, Mapping) and isinstance(claim.get("claim_id"), str)
    }
    evidence_by_id = {
        item.get("evidence_id"): item
        for item in evidence
        if isinstance(item, Mapping) and isinstance(item.get("evidence_id"), str)
    }
    exact_edges = {
        (edge.get("claim_id"), edge.get("evidence_id"), edge.get("source_id"))
        for edge in support_edges
        if isinstance(edge, Mapping)
    }
    target_hashes = world_evidence_target_hashes(volume)
    claim_targets: dict[str, list[Mapping[str, Any]]] = {}
    for claim_id, claim in claim_by_id.items():
        raw_targets = claim.get("world_targets")
        if not isinstance(raw_targets, list):
            raise WorldVolumeError(
                f"XK3 claim has no world target bindings: {claim_id}"
            )
        claim_targets[claim_id] = []
        for target in raw_targets:
            if not isinstance(target, Mapping) or set(target) != {
                "target_path",
                "target_sha256",
                "relation",
            }:
                raise WorldVolumeError(
                    f"XK3 claim world target is malformed: {claim_id}"
                )
            if target.get("relation") not in {"descriptive", "authorization"}:
                raise WorldVolumeError(
                    f"XK3 claim world target relation is invalid: {claim_id}"
                )
            if target.get("target_sha256") != target_hashes.get(target.get("target_path")):
                raise WorldVolumeError(
                    f"XK3 claim world target does not resolve in XK5: {claim_id}"
                )
            claim_targets[claim_id].append(target)

    _target_paths, expected_targets_by_ref = _world_evidence_target_catalog(volume)
    authorization_refs: set[str] = set()
    descriptive_refs: set[str] = set()
    declared_authorization_refs = {
        evidence_ref for group in authorization_groups for evidence_ref in group
    }
    for evidence_ref, binding in bindings.items():
        bound_edges = binding.get("support_edges")
        if not isinstance(bound_edges, list) or not bound_edges:
            raise WorldVolumeError(
                f"XK5 evidence_state binding has no support identity: {evidence_ref}"
            )
        binding_kinds: set[str] = set()
        for edge in bound_edges:
            if not isinstance(edge, Mapping):
                raise WorldVolumeError(
                    "XK5 evidence_state support identity is not an object"
                )
            triple = (
                edge.get("claim_id"),
                edge.get("evidence_id"),
                edge.get("source_id"),
            )
            claim = claim_by_id.get(triple[0])
            evidence_item = evidence_by_id.get(triple[1])
            if (
                triple not in exact_edges
                or not isinstance(claim, Mapping)
                or not isinstance(evidence_item, Mapping)
                or evidence_item.get("claim_id") != triple[0]
                or evidence_item.get("source_id") != triple[2]
                or evidence_item.get("status") not in {"supports", "partially_supports"}
                or triple[1] not in claim.get("evidence_refs", [])
            ):
                raise WorldVolumeError(
                    "support identity does not resolve in frozen XK3: "
                    f"{evidence_ref}"
                )
            binding_kinds.add(str(claim.get("kind")))
        if evidence_ref in declared_authorization_refs and not any(
            kind == "authorization_boundary" for kind in binding_kinds
        ):
            raise WorldVolumeError(
                "authorization evidence does not resolve to an authorization claim"
            )
        raw_targets = binding.get("targets")
        expected_targets = expected_targets_by_ref.get(evidence_ref, [])
        if not isinstance(raw_targets, list):
            raise WorldVolumeError(
                f"XK5 evidence_state binding has no runtime target paths: {evidence_ref}"
            )
        if raw_targets != expected_targets:
            raise WorldVolumeError(
                f"XK5 evidence_state target paths differ from authored fields: {evidence_ref}"
            )
        for target in expected_targets:
            matching_claim = False
            for edge in bound_edges:
                claim_id = edge.get("claim_id")
                for claim_target in claim_targets.get(str(claim_id), []):
                    if (
                        claim_target.get("target_path") == target["target_path"]
                        and claim_target.get("target_sha256")
                        == target["target_sha256"]
                        and (
                            (
                                target["relation"] == "authorization"
                                and claim_target.get("relation") == "authorization"
                            )
                            or (
                                target["relation"] == "context"
                                and claim_target.get("relation") == "descriptive"
                            )
                        )
                    ):
                        matching_claim = True
                        break
                if matching_claim:
                    break
            if not matching_claim:
                raise WorldVolumeError(
                    "XK3 support edge does not bind the XK5 target path: "
                    f"{evidence_ref}:{target['target_path']}"
                )
        if binding_kinds == {"authorization_boundary"}:
            authorization_refs.add(evidence_ref)
        if any(kind != "authorization_boundary" for kind in binding_kinds):
            descriptive_refs.add(evidence_ref)

    for refs in authorization_groups:
        if not refs or any(ref not in authorization_refs for ref in refs):
            raise WorldVolumeError(
                "authorization evidence does not resolve to an authorization claim"
            )
    for refs in descriptive_groups:
        if not refs or not any(ref in descriptive_refs for ref in refs):
            raise WorldVolumeError(
                "descriptive evidence does not resolve to a non-authorization claim"
            )

    _validate_authorization_scopes(
        volume,
        claim_by_id=claim_by_id,
        bindings=bindings,
    )


def _validate_authorization_scopes(
    volume: Mapping[str, Any],
    *,
    claim_by_id: Mapping[str, Mapping[str, Any]],
    bindings: Mapping[str, Mapping[str, Any]],
) -> None:
    """Require every channel ACL to match its frozen atomic authorization tuple."""

    clocks = {
        clock.get("clock_id"): clock
        for clock in volume.get("clocks", [])
        if isinstance(clock, Mapping)
    }
    for channel in volume.get("channels", []):
        if not isinstance(channel, Mapping):
            continue
        acl = channel.get("acl")
        if not isinstance(acl, Mapping):
            continue
        scope = acl.get("authorization_scope")
        if not isinstance(scope, Mapping):
            raise WorldVolumeError(
                f"channel ACL has no atomic authorization_scope: {channel.get('channel_id')}"
            )
        matching_boundaries: list[Mapping[str, Any]] = []
        for ref in acl.get("authorization_evidence_refs", []):
            binding = bindings.get(ref)
            if not isinstance(binding, Mapping):
                continue
            for edge in binding.get("support_edges", []):
                claim = claim_by_id.get(edge.get("claim_id"))
                if isinstance(claim, Mapping) and claim.get("kind") == "authorization_boundary":
                    boundary = claim.get("authorization_boundary")
                    if isinstance(boundary, Mapping):
                        matching_boundaries.append(boundary)
        if not matching_boundaries or any(dict(boundary) != dict(scope) for boundary in matching_boundaries):
            raise WorldVolumeError(
                f"channel ACL authorization_scope differs from frozen XK3: {channel.get('channel_id')}"
            )
        threshold = channel.get("threshold")
        clock = clocks.get(threshold.get("clock_id")) if isinstance(threshold, Mapping) else None
        current_time = clock.get("current_time") if isinstance(clock, Mapping) else None
        interval = scope.get("validity_interval")
        try:
            now = datetime.fromisoformat(str(current_time).replace("Z", "+00:00"))
            starts = datetime.fromisoformat(str(interval["starts_at"]).replace("Z", "+00:00"))
            ends = datetime.fromisoformat(str(interval["ends_at"]).replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError) as error:
            raise WorldVolumeError(
                f"channel ACL authorization validity interval is invalid: {channel.get('channel_id')}"
            ) from error
        if not starts <= now <= ends:
            raise WorldVolumeError(
                f"channel ACL authorization is expired or not yet valid: {channel.get('channel_id')}"
            )


def bind_world_evidence_state(
    volume: Mapping[str, object],
    *,
    evidence_ledger: Mapping[str, Any],
    run_id: str,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    """Return the runtime-owned XK5 projection bound to frozen XK3 bytes."""

    snapshot = _native_snapshot(
        volume, label="world volume", error_type=WorldVolumeError
    )
    if not isinstance(snapshot, dict):
        raise WorldVolumeError("world volume must be a mapping")
    state = snapshot.get("evidence_state")
    if not isinstance(state, dict):
        raise WorldVolumeError("XK5 evidence_state is missing")
    _target_paths, targets_by_ref = _world_evidence_target_catalog(snapshot)
    for binding in state.get("bindings", []):
        if not isinstance(binding, dict):
            raise WorldVolumeError("XK5 evidence_state binding is not an object")
        evidence_ref = binding.get("evidence_ref")
        if not isinstance(evidence_ref, str) or evidence_ref not in targets_by_ref:
            raise WorldVolumeError(
                f"XK5 evidence_state binding has no authored target: {evidence_ref}"
            )
        binding["targets"] = copy.deepcopy(targets_by_ref[evidence_ref])
    state["run_id"] = run_id
    state["xk3_evidence_ledger_sha256"] = _canonical_sha256(evidence_ledger)
    validate_world_volume(
        snapshot,
        repository_root=repository_root,
        evidence_ledger=evidence_ledger,
        expected_run_id=run_id,
    )
    return snapshot


def _validate_ontology_binding(
    value: Mapping[str, Any],
    *,
    required: frozenset[str],
    label: str,
    error_type: type[ValueError],
    repository_root: Path | None = None,
) -> None:
    if value.get("source_version") != "v8.3":
        raise error_type(f"{label} is not bound to source version v8.3")
    refs = value.get("ontology_refs")
    if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes)):
        raise error_type(f"{label} ontology_refs must be a sequence")
    refs_set = set(refs)
    root_value = str(_repository_root(repository_root))
    unknown = refs_set - _ontology_ids(root_value)
    if unknown:
        raise error_type(f"{label} has unknown current-v8.3 ontology refs: {sorted(unknown)}")
    missing = required - refs_set
    if missing:
        raise error_type(f"{label} omits required v8.3 ontology refs: {sorted(missing)}")
    try:
        unknown_anchors = _declared_source_anchors(value) - _source_anchor_ids(root_value)
    except WorldVolumeError as error:
        raise error_type(str(error)) from error
    if unknown_anchors:
        raise error_type(
            f"{label} has unknown current-v8.3 source anchors: {sorted(unknown_anchors)}"
        )


def _records_by_id(
    records: Sequence[Mapping[str, Any]], field: str, *, label: str
) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for record in records:
        identifier = record[field]
        if identifier in result:
            raise WorldVolumeError(f"duplicate {label} identifier: {identifier}")
        result[identifier] = record
    return result


def _represented(volume: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    return tuple(volume["actors"]) + tuple(volume["circles"]) + tuple(
        volume["positions"]
    )


def _validate_unique_ids(volume: Mapping[str, Any]) -> None:
    groups = (
        (volume["actors"], "actor_id", "actor"),
        (volume["circles"], "circle_id", "circle"),
        (volume["positions"], "position_id", "position"),
        (volume["clocks"], "clock_id", "clock"),
        (volume["channels"], "channel_id", "channel"),
        (volume["events"], "event_id", "event"),
        (volume["circle_relations"], "relation_id", "circle relation"),
        (volume["local_distributions"], "distribution_id", "distribution"),
        (volume["unknowns"], "unknown_id", "unknown"),
        (volume["residuals"], "residual_id", "residual"),
    )
    all_ids: list[str] = [volume["volume_id"]]
    for records, field, label in groups:
        catalog = _records_by_id(records, field, label=label)
        all_ids.extend(catalog)
    for location in _represented(volume):
        for state_field in ("M_state", "Psi_state"):
            state = location[state_field]
            all_ids.append(state["state_id"])
            names = [item["name"] for item in state["variables"]]
            if len(names) != len(set(names)):
                raise WorldVolumeError(f"duplicate local {state_field} variable")
    if len(all_ids) != len(set(all_ids)):
        raise WorldVolumeError("stable identifiers collide across Omega domains")


def _validate_local_state(volume: Mapping[str, Any]) -> None:
    clocks = {clock["clock_id"] for clock in volume["clocks"]}
    clock_scopes = {
        volume["volume_id"],
        *(record["actor_id"] for record in volume["actors"]),
        *(record["circle_id"] for record in volume["circles"]),
        *(record["position_id"] for record in volume["positions"]),
    }
    if any(clock["scope_id"] not in clock_scopes for clock in volume["clocks"]):
        raise WorldVolumeError("clock scope does not resolve inside its parent Omega")
    for location in _represented(volume):
        if set(location["scale_profile"]) != set(AXES):
            raise WorldVolumeError("represented location lacks the nine v8.3 scale axes")
        for state_field in ("M_state", "Psi_state"):
            variables = location[state_field]["variables"]
            if not variables:
                raise WorldVolumeError("represented location lacks local M or Psi state")
            if any(variable["clock_id"] not in clocks for variable in variables):
                raise WorldVolumeError("local M/Psi variable has an unresolved clock")
    if {clock["kind"] for clock in volume["clocks"]} != CLOCK_KINDS:
        raise WorldVolumeError("Omega must preserve all five asynchronous clock kinds")


def _validate_containment(volume: Mapping[str, Any]) -> None:
    circle_ids = {circle["circle_id"] for circle in volume["circles"]}
    parents: dict[str, set[str]] = {circle_id: set() for circle_id in circle_ids}
    edges: set[tuple[str, str]] = set()
    for edge in volume["containment_relations"]:
        child = edge["child_circle_id"]
        parent = edge["parent_circle_id"]
        if child not in circle_ids or parent not in circle_ids or child == parent:
            raise WorldVolumeError("containment edge has invalid endpoints")
        pair = (child, parent)
        if pair in edges:
            raise WorldVolumeError("duplicate containment edge")
        edges.add(pair)
        parents[child].add(parent)

    visiting: set[str] = set()
    memo: dict[str, set[str]] = {}

    def ancestors(circle_id: str) -> set[str]:
        if circle_id in memo:
            return set(memo[circle_id])
        if circle_id in visiting:
            raise WorldVolumeError("containment graph contains a cycle")
        visiting.add(circle_id)
        found: set[str] = set()
        for parent in parents[circle_id]:
            found.add(parent)
            found.update(ancestors(parent))
        visiting.remove(circle_id)
        memo[circle_id] = set(found)
        return found

    declared = _records_by_id(
        volume["containment_closure"], "circle_id", label="containment closure"
    )
    if set(declared) != circle_ids:
        raise WorldVolumeError("containment closure does not cover every circle")
    for circle_id in circle_ids:
        actual = declared[circle_id]["ancestor_circle_ids"]
        if len(actual) != len(set(actual)) or set(actual) != ancestors(circle_id):
            raise WorldVolumeError("containment closure differs from the multi-parent DAG")


def _predicate_result(
    positions: Mapping[str, Mapping[str, Any]], predicate: Mapping[str, Any]
) -> bool:
    position = positions.get(predicate["position_id"])
    if position is None:
        raise WorldVolumeError("channel structured threshold has an unknown position")
    state = next(
        (
            position[field]
            for field in ("M_state", "Psi_state")
            if position[field]["state_id"] == predicate["state_id"]
        ),
        None,
    )
    if state is None:
        raise WorldVolumeError("channel structured threshold has an unknown local state")
    variable = next(
        (
            item
            for item in state["variables"]
            if item["name"] == predicate["variable_name"]
        ),
        None,
    )
    if (
        variable is None
        or variable["clock_id"] != predicate["clock_id"]
        or variable["unit"] != predicate["unit"]
    ):
        raise WorldVolumeError(
            "channel structured threshold does not resolve a local variable and clock"
        )
    actual = variable["value"]
    expected = predicate["value"]
    operator = predicate["operator"]
    if operator in {"eq", "ne"}:
        equal = type(actual) is type(expected) and actual == expected
        return equal if operator == "eq" else not equal
    if (
        isinstance(actual, bool)
        or isinstance(expected, bool)
        or not isinstance(actual, (int, float))
        or not isinstance(expected, (int, float))
    ):
        raise WorldVolumeError(
            "ordered channel threshold requires comparable numeric values"
        )
    return {
        "lt": actual < expected,
        "lte": actual <= expected,
        "gt": actual > expected,
        "gte": actual >= expected,
    }[operator]


def _validate_topology(volume: Mapping[str, Any]) -> None:
    actors = _records_by_id(volume["actors"], "actor_id", label="actor")
    circles = _records_by_id(volume["circles"], "circle_id", label="circle")
    positions = _records_by_id(volume["positions"], "position_id", label="position")
    channels = _records_by_id(volume["channels"], "channel_id", label="channel")
    relations = _records_by_id(
        volume["circle_relations"], "relation_id", label="circle relation"
    )
    location_refs = {
        volume["volume_id"],
        *actors,
        *circles,
        *positions,
        *channels,
        *relations,
        *(location["M_state"]["state_id"] for location in _represented(volume)),
        *(location["Psi_state"]["state_id"] for location in _represented(volume)),
    }
    if not set(volume["object_boundary"]["object_ids"]).issubset(location_refs):
        raise WorldVolumeError("object boundary references an ID outside Omega")

    position_tuples: list[tuple[str, str, str]] = []
    for position in positions.values():
        if position["actor_id"] not in actors or position["circle_id"] not in circles:
            raise WorldVolumeError("position has an unknown actor or circle")
        position_tuples.append(
            (position["actor_id"], position["circle_id"], position["role_id"])
        )
    if len(position_tuples) != len(set(position_tuples)):
        raise WorldVolumeError(
            "each actor-circle-role tuple must resolve exactly one position"
        )
    membership_tuples = [
        (membership["actor_ref"], membership["circle_ref"], role)
        for membership in volume["memberships"]
        for role in membership["roles"]
    ]
    if len(membership_tuples) != len(set(membership_tuples)) or set(
        membership_tuples
    ) != set(position_tuples):
        raise WorldVolumeError("memberships do not exactly cover actor-circle-role positions")

    for channel in channels.values():
        source = channel["from_position_id"]
        target = channel["to_position_id"]
        if source not in positions or target not in positions:
            raise WorldVolumeError("channel has an unknown endpoint")
        mapping = channel["identity_mapping"]
        acl = channel["acl"]
        if mapping["source_k_ref"] != source or mapping["target_k_ref"] != target:
            raise WorldVolumeError("channel identity mapping does not bind its endpoints")
        if source not in acl["authorized_position_ids"]:
            raise WorldVolumeError("channel source is absent from its ACL")
        if not set(acl["authorization_evidence_refs"]).issubset(
            set(channel["evidence_refs"])
        ):
            raise WorldVolumeError("channel ACL evidence is outside channel evidence")
        capacity = channel["capacity"]
        if (
            not isinstance(capacity, Mapping)
            or (_duration_seconds(capacity["window"]) or 0) <= 0
        ):
            raise WorldVolumeError("channel requires structured capacity in a real window")
        if _duration_seconds(channel["delay"]) is None:
            raise WorldVolumeError("channel delay must be a parseable duration")
        threshold = channel["threshold"]
        if not isinstance(threshold, Mapping):
            raise WorldVolumeError(
                "channel requires a structured threshold bound to local state"
            )
        _predicate_result(positions, threshold)
        if not set(threshold["evidence_refs"]).issubset(
            set(channel["evidence_refs"])
        ):
            raise WorldVolumeError(
                "channel structured threshold evidence is outside channel evidence"
            )
        blocking_conditions = channel["blocking_conditions"]
        if not isinstance(blocking_conditions, list) or not blocking_conditions:
            raise WorldVolumeError(
                "channel active flag requires structured blocking conditions"
            )
        blocked = False
        for blocker in blocking_conditions:
            blocked = _predicate_result(positions, blocker) or blocked
            if not set(blocker["evidence_refs"]).issubset(
                set(channel["evidence_refs"])
            ):
                raise WorldVolumeError(
                    "channel blocking condition evidence is outside channel evidence"
                )
        if channel["active"] is blocked:
            raise WorldVolumeError(
                "channel active flag differs from its structured blocking conditions"
            )

    for relation in relations.values():
        source_circle = relation["source_circle_ref"]
        target_circle = relation["target_circle_ref"]
        if source_circle not in circles or target_circle not in circles:
            raise WorldVolumeError("circle relation has an unknown endpoint")
        channel_id = relation["channel_id"]
        if channel_id is not None:
            channel = channels.get(channel_id)
            if channel is None:
                raise WorldVolumeError("circle relation has an unknown channel")
            source = positions[channel["from_position_id"]]
            target = positions[channel["to_position_id"]]
            if (
                source["circle_id"] != source_circle
                or target["circle_id"] != target_circle
            ):
                raise WorldVolumeError("circle relation channel crosses different circles")

    for record in (*volume["unknowns"], *volume["residuals"]):
        if record["location_ref"] not in location_refs:
            raise WorldVolumeError("unknown or residual has an unresolved local position")
    for distribution in volume["local_distributions"]:
        if distribution["location_ref"] not in location_refs:
            raise WorldVolumeError("local distribution has an unresolved location")


def _state_variables(
    position: Mapping[str, Any], state_field: str
) -> dict[str, Mapping[str, Any]]:
    return {
        variable["name"]: variable
        for variable in position[state_field]["variables"]
    }


_MUTABLE_RELATION_FIELDS = frozenset(
    {"source_circle_ref", "target_circle_ref", "relation_type", "channel_id"}
)


def _event_deltas(
    volume: Mapping[str, Any], event: Mapping[str, Any]
) -> tuple[
    tuple[dict[str, Any], ...],
    tuple[dict[str, Any], ...],
    tuple[dict[str, Any], ...],
]:
    positions = _records_by_id(volume["positions"], "position_id", label="position")
    clocks = _records_by_id(volume["clocks"], "clock_id", label="clock")
    position_deltas: list[dict[str, Any]] = []
    for state_field, updates_field in (("M_state", "M_updates"), ("Psi_state", "Psi_updates")):
        for update in event[updates_field]:
            position = positions[update["position_id"]]
            variables = _state_variables(position, state_field)
            for change in update["variable_changes"]:
                position_deltas.append(
                    {
                        "position_id": update["position_id"],
                        "state_field": state_field,
                        "state_id": update["state_id"],
                        "variable_name": change["name"],
                        "clock_id": change["clock_id"],
                        "source_value": copy.deepcopy(change["source_value"]),
                        "target_value": copy.deepcopy(change["target_value"]),
                        "source_value_sha256": _value_sha256(change["source_value"]),
                        "target_value_sha256": _value_sha256(change["target_value"]),
                        "unit": variables[change["name"]]["unit"],
                    }
                )
    relation_deltas = tuple(
        {
            "relation_id": update["relation_id"],
            "field_name": update["field_name"],
            "source_value": copy.deepcopy(update["source_value"]),
            "target_value": copy.deepcopy(update["target_value"]),
            "source_value_sha256": _value_sha256(update["source_value"]),
            "target_value_sha256": _value_sha256(update["target_value"]),
        }
        for update in event["relation_updates"]
    )
    clock_deltas = tuple(
        {
            "clock_id": delta["clock_id"],
            "delta": delta["delta"],
            "source_time": clocks[delta["clock_id"]]["current_time"],
            "target_time": _advance_clock_time(
                clocks[delta["clock_id"]]["current_time"], delta["delta"]
            ),
        }
        for delta in event["clock_deltas"]
    )
    return tuple(position_deltas), relation_deltas, clock_deltas


def _apply_deltas(
    volume: Mapping[str, Any],
    *,
    position_deltas: Sequence[Mapping[str, Any]],
    relation_deltas: Sequence[Mapping[str, Any]],
    clock_deltas: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    candidate = _native_snapshot(
        volume, label="world volume", error_type=WorldVolumeError
    )
    if not isinstance(candidate, dict):
        raise WorldVolumeError("world volume must be a mapping")
    positions = _records_by_id(candidate["positions"], "position_id", label="position")
    relations = _records_by_id(
        candidate["circle_relations"], "relation_id", label="circle relation"
    )
    clocks = _records_by_id(candidate["clocks"], "clock_id", label="clock")
    for delta in position_deltas:
        position = positions.get(delta["position_id"])
        if position is None or delta["state_field"] not in {"M_state", "Psi_state"}:
            raise WorldVolumeError("StateDiff position delta cannot be replayed")
        state = position[delta["state_field"]]
        if state["state_id"] != delta["state_id"]:
            raise WorldVolumeError("StateDiff position state binding cannot be replayed")
        variable = next(
            (
                item
                for item in state["variables"]
                if item["name"] == delta["variable_name"]
            ),
            None,
        )
        if (
            variable is None
            or variable["clock_id"] != delta["clock_id"]
            or variable["unit"] != delta["unit"]
            or not _same_json_value(variable["value"], delta["source_value"])
            or delta["source_value_sha256"] != _value_sha256(delta["source_value"])
            or delta["target_value_sha256"] != _value_sha256(delta["target_value"])
        ):
            raise WorldVolumeError("StateDiff position source cannot be replayed")
        variable["value"] = copy.deepcopy(delta["target_value"])
    for delta in relation_deltas:
        relation = relations.get(delta["relation_id"])
        field_name = delta["field_name"]
        if (
            relation is None
            or field_name not in _MUTABLE_RELATION_FIELDS
            or field_name not in relation
            or not _same_json_value(relation[field_name], delta["source_value"])
            or delta["source_value_sha256"] != _value_sha256(delta["source_value"])
            or delta["target_value_sha256"] != _value_sha256(delta["target_value"])
        ):
            raise WorldVolumeError("StateDiff relation source cannot be replayed")
        relation[field_name] = copy.deepcopy(delta["target_value"])
    for delta in clock_deltas:
        clock = clocks.get(delta["clock_id"])
        if (
            clock is None
            or clock["current_time"] != delta["source_time"]
            or _advance_clock_time(clock["current_time"], delta["delta"])
            != delta["target_time"]
        ):
            raise WorldVolumeError("StateDiff clock source cannot be replayed")
        clock["current_time"] = delta["target_time"]
    return candidate


def _validate_event_post_state(
    volume: Mapping[str, Any],
    event: Mapping[str, Any],
    *,
    repository_root: Path | None = None,
) -> tuple[
    tuple[dict[str, Any], ...],
    tuple[dict[str, Any], ...],
    tuple[dict[str, Any], ...],
    dict[str, Any],
]:
    position_deltas, relation_deltas, clock_deltas = _event_deltas(volume, event)
    candidate = _apply_deltas(
        volume,
        position_deltas=position_deltas,
        relation_deltas=relation_deltas,
        clock_deltas=clock_deltas,
    )
    try:
        _validate_schema(
            "xk-world-volume.schema.json",
            candidate,
            label="world volume",
            error_type=WorldVolumeError,
            repository_root=repository_root,
        )
        _validate_unique_ids(candidate)
        _validate_local_state(candidate)
        _validate_containment(candidate)
        _validate_topology(candidate)
    except WorldVolumeError as error:
        raise WorldVolumeError(f"relation update post-state is invalid: {error}") from error
    return position_deltas, relation_deltas, clock_deltas, candidate


def _evaluate_event(
    volume: Mapping[str, Any],
    event: Mapping[str, Any],
    *,
    repository_root: Path | None = None,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    if event["target_volume_id"] != volume["volume_id"]:
        raise WorldVolumeError("event targets a different Omega")
    positions = _records_by_id(volume["positions"], "position_id", label="position")
    channels = _records_by_id(volume["channels"], "channel_id", label="channel")
    clocks = _records_by_id(volume["clocks"], "clock_id", label="clock")
    relations = _records_by_id(
        volume["circle_relations"], "relation_id", label="circle relation"
    )

    channel_ids = event["channel_ids"]
    conditions = event["channel_conditions"]
    condition_ids = [condition["channel_id"] for condition in conditions]
    if len(condition_ids) != len(set(condition_ids)) or set(condition_ids) != set(
        channel_ids
    ):
        raise WorldVolumeError("event channels and conditions are not one-to-one")
    if not channel_ids:
        if any(
            event[field]
            for field in (
                "target_position_ids",
                "M_updates",
                "Psi_updates",
                "relation_updates",
                "clock_deltas",
            )
        ):
            raise WorldVolumeError("event without a channel cannot update a target position")
        return (), (), ()

    valid_channels: dict[str, Mapping[str, Any]] = {}
    source_position = event["source_position_id"]
    if event["origin_kind"] == "endogenous" and source_position not in positions:
        raise WorldVolumeError("endogenous event lacks a real source position")
    for condition in conditions:
        channel_id = condition["channel_id"]
        channel = channels.get(channel_id)
        if channel is None:
            raise WorldVolumeError("event references an unknown channel")
        if source_position is not None and channel["from_position_id"] != source_position:
            raise WorldVolumeError("event channel does not start at its source position")
        mapping = channel["identity_mapping"]
        acl = channel["acl"]
        threshold = channel["threshold"]
        threshold_met = _predicate_result(positions, threshold)
        condition_evidence = set(condition["evidence_refs"])
        if condition["threshold_met"] is not threshold_met:
            raise WorldVolumeError(
                "event threshold boolean differs from the structured local predicate"
            )
        valid = (
            channel["active"] is True
            and threshold_met
            and condition["identity_preserved"] is True
            and condition["acl_authorized"] is True
            and mapping["preserves_identity"] is True
            and channel["from_position_id"] in acl["authorized_position_ids"]
            and bool(condition_evidence)
            and condition_evidence.issubset(set(channel["evidence_refs"]))
            and set(threshold["evidence_refs"]).issubset(condition_evidence)
            and set(acl["authorization_evidence_refs"]).issubset(condition_evidence)
        )
        if valid:
            valid_channels[channel_id] = channel

    changed_positions: set[str] = set()
    changed_relations: list[str] = []
    variable_clock_ids: set[str] = set()
    variable_targets: dict[tuple[str, str, str, str], object] = {}
    updates_by_channel: dict[str, int] = {
        channel_id: 0 for channel_id in event["channel_ids"]
    }
    for state_field, updates_field in (("M_state", "M_updates"), ("Psi_state", "Psi_updates")):
        for update in event[updates_field]:
            channel = valid_channels.get(update["via_channel_id"])
            position = positions.get(update["position_id"])
            if channel is None or position is None:
                raise WorldVolumeError("state update is not reachable over a valid channel")
            if channel["to_position_id"] != update["position_id"]:
                raise WorldVolumeError("state update targets a position outside its channel")
            updates_by_channel[update["via_channel_id"]] += 1
            state = position[state_field]
            if state["state_id"] != update["state_id"]:
                raise WorldVolumeError("state update does not bind the local M/Psi state")
            variables = _state_variables(position, state_field)
            for change in update["variable_changes"]:
                update_key = (
                    update["position_id"],
                    update["state_id"],
                    change["name"],
                    change["clock_id"],
                )
                if (
                    update_key in variable_targets
                    and not _same_json_value(
                        variable_targets[update_key], change["target_value"]
                    )
                ):
                    raise WorldVolumeError(
                        "event contains a conflicting local variable update"
                    )
                variable_targets[update_key] = change["target_value"]
                current = variables.get(change["name"])
                if (
                    current is None
                    or not _same_json_value(
                        current["value"], change["source_value"]
                    )
                    or current["unit"] != change["unit"]
                    or current["clock_id"] != change["clock_id"]
                    or _same_json_value(
                        change["source_value"], change["target_value"]
                    )
                ):
                    raise WorldVolumeError("state update differs from its local source state")
                variable_clock_ids.add(change["clock_id"])
            changed_positions.add(update["position_id"])

    for update in event["relation_updates"]:
        channel = valid_channels.get(update["via_channel_id"])
        relation = relations.get(update["relation_id"])
        if channel is None or relation is None:
            raise WorldVolumeError("relation update lacks a valid local channel")
        if update["field_name"] not in _MUTABLE_RELATION_FIELDS:
            raise WorldVolumeError("relation update names an immutable or unknown field")
        updates_by_channel[update["via_channel_id"]] += 1
        if (
            not _same_json_value(
                relation[update["field_name"]], update["source_value"]
            )
            or _same_json_value(update["source_value"], update["target_value"])
        ):
            raise WorldVolumeError("relation update differs from its source relation")
        changed_relations.append(update["relation_id"])
        changed_positions.add(channel["to_position_id"])

    targets = set(event["target_position_ids"])
    if targets != changed_positions:
        raise WorldVolumeError("event target positions differ from reachable local updates")

    for channel_id, update_count in updates_by_channel.items():
        if update_count > channels[channel_id]["capacity"]["max_updates"]:
            raise WorldVolumeError(
                "event update count exceeds the channel structured capacity"
            )

    advanced_clocks: list[str] = []
    for delta in event["clock_deltas"]:
        clock_id = delta["clock_id"]
        if (
            clock_id not in clocks
            or clock_id in advanced_clocks
            or (_duration_seconds(delta["delta"]) or 0) <= 0
        ):
            raise WorldVolumeError("clock delta is unresolved, duplicate, or not positive")
        advanced_clocks.append(clock_id)
    if set(advanced_clocks) != variable_clock_ids:
        raise WorldVolumeError("changed local variables lack exact clock-delta coverage")

    ordered_changed = tuple(
        position["position_id"]
        for position in volume["positions"]
        if position["position_id"] in changed_positions
    )
    _validate_event_post_state(
        volume,
        event,
        repository_root=repository_root,
    )
    return ordered_changed, tuple(changed_relations), tuple(advanced_clocks)


def validate_world_volume(
    volume: Mapping[str, object],
    *,
    repository_root: Path | None = None,
    evidence_ledger: Mapping[str, Any] | None = None,
    expected_run_id: str | None = None,
) -> None:
    """Validate one v8.3-bound Omega document without mutating it."""

    snapshot = _native_snapshot(
        volume, label="world volume", error_type=WorldVolumeError
    )
    if not isinstance(snapshot, dict):
        raise WorldVolumeError("world volume must be a mapping")
    try:
        _validate_schema(
            "xk-world-volume.schema.json",
            snapshot,
            label="world volume",
            error_type=WorldVolumeError,
            repository_root=repository_root,
        )
    except WorldVolumeError as error:
        if ".capacity" in str(error):
            raise WorldVolumeError(
                "channel requires structured capacity in a real window"
            ) from error
        if ".threshold" in str(error):
            raise WorldVolumeError(
                "channel requires a structured threshold bound to local state"
            ) from error
        if "blocking_conditions" in str(error):
            raise WorldVolumeError(
                "channel active flag requires structured blocking conditions"
            ) from error
        raise
    _validate_ontology_binding(
        snapshot,
        required=REQUIRED_WORLD_ONTOLOGY,
        label="world volume",
        error_type=WorldVolumeError,
        repository_root=repository_root,
    )
    _validate_unique_ids(snapshot)
    _validate_local_state(snapshot)
    _validate_containment(snapshot)
    _validate_topology(snapshot)
    _validate_evidence_state(
        snapshot,
        evidence_ledger=evidence_ledger,
        expected_run_id=expected_run_id,
    )
    for event in snapshot["events"]:
        _evaluate_event(
            snapshot,
            event,
            repository_root=repository_root,
        )


def apply_event(
    volume: Mapping[str, object],
    event: Mapping[str, object],
    *,
    repository_root: Path | None = None,
) -> StateDiff:
    """Return the declared event's deterministic StateDiff; never mutate Omega."""

    snapshot = _native_snapshot(
        volume, label="world volume", error_type=WorldVolumeError
    )
    event_snapshot = _native_snapshot(
        event, label="event", error_type=WorldVolumeError
    )
    if not isinstance(snapshot, dict) or not isinstance(event_snapshot, dict):
        raise WorldVolumeError("world volume and event must be mappings")
    validate_world_volume(snapshot, repository_root=repository_root)
    event_id = event_snapshot.get("event_id")
    matches = [
        stored
        for stored in snapshot["events"]
        if stored["event_id"] == event_id and stored == event_snapshot
    ]
    if len(matches) != 1:
        raise WorldVolumeError("event must deep-equal one declared Omega event")
    changed, changed_relations, advanced = _evaluate_event(
        snapshot,
        event_snapshot,
        repository_root=repository_root,
    )
    position_deltas, relation_deltas, clock_deltas, result = _validate_event_post_state(
        snapshot,
        event_snapshot,
        repository_root=repository_root,
    )
    channels = {
        channel["channel_id"]: channel for channel in snapshot["channels"]
    }
    evidence_refs = set(event_snapshot["evidence_refs"])
    for condition in event_snapshot["channel_conditions"]:
        evidence_refs.update(condition["evidence_refs"])
    for channel_id in event_snapshot["channel_ids"]:
        channel = channels[channel_id]
        evidence_refs.update(channel["evidence_refs"])
        evidence_refs.update(channel["acl"]["authorization_evidence_refs"])
    changed_set = set(changed)
    unchanged = tuple(
        position["position_id"]
        for position in snapshot["positions"]
        if position["position_id"] not in changed_set
    )
    source_volume_sha256 = _semantic_volume_sha256(snapshot)
    relation_delta_sha256 = _canonical_sha256(list(relation_deltas))
    result_volume_sha256 = _semantic_volume_sha256(result)
    diff_payload = {
        "source_volume_sha256": source_volume_sha256,
        "event_id": event_snapshot["event_id"],
        "evidence_refs": sorted(evidence_refs),
        "changed_positions": list(changed),
        "unchanged_positions": list(unchanged),
        "changed_relations": list(changed_relations),
        "advanced_clocks": list(advanced),
        "inherited_unknown_ids": [
            record["unknown_id"] for record in snapshot["unknowns"]
        ],
        "inherited_residual_ids": [
            record["residual_id"] for record in snapshot["residuals"]
        ],
        "position_deltas": list(position_deltas),
        "relation_deltas": list(relation_deltas),
        "clock_deltas": list(clock_deltas),
        "relation_delta_sha256": relation_delta_sha256,
        "result_volume_sha256": result_volume_sha256,
    }
    return StateDiff(
        state_diff_id=(
            f"DIFF-{event_snapshot['event_id']}-"
            f"{_canonical_sha256(diff_payload)[:20].upper()}"
        ),
        source_volume_sha256=source_volume_sha256,
        event_id=event_snapshot["event_id"],
        evidence_refs=tuple(diff_payload["evidence_refs"]),
        changed_positions=changed,
        unchanged_positions=unchanged,
        changed_relations=changed_relations,
        advanced_clocks=advanced,
        inherited_unknown_ids=tuple(diff_payload["inherited_unknown_ids"]),
        inherited_residual_ids=tuple(diff_payload["inherited_residual_ids"]),
        position_deltas=position_deltas,
        relation_deltas=relation_deltas,
        clock_deltas=clock_deltas,
        relation_delta_sha256=relation_delta_sha256,
        result_volume_sha256=result_volume_sha256,
    )


def replay_state_diff(
    volume: Mapping[str, object],
    state_diff: StateDiff,
) -> dict[str, Any]:
    """Replay a StateDiff against its exact source Omega without mutating it."""

    snapshot = _native_snapshot(
        volume, label="world volume", error_type=WorldVolumeError
    )
    if not isinstance(snapshot, dict):
        raise WorldVolumeError("world volume must be a mapping")
    if _semantic_volume_sha256(snapshot) != state_diff.source_volume_sha256:
        raise WorldVolumeError("StateDiff source Omega hash does not match replay input")
    if state_diff.relation_delta_sha256 != _canonical_sha256(
        list(state_diff.relation_deltas)
    ):
        raise WorldVolumeError("StateDiff relation delta hash does not match its content")
    candidate = _apply_deltas(
        snapshot,
        position_deltas=state_diff.position_deltas,
        relation_deltas=state_diff.relation_deltas,
        clock_deltas=state_diff.clock_deltas,
    )
    try:
        _validate_schema(
            "xk-world-volume.schema.json",
            candidate,
            label="world volume",
            error_type=WorldVolumeError,
        )
        _validate_unique_ids(candidate)
        _validate_local_state(candidate)
        _validate_containment(candidate)
        _validate_topology(candidate)
    except WorldVolumeError as error:
        raise WorldVolumeError(f"StateDiff replay produces an invalid Omega: {error}") from error
    if _semantic_volume_sha256(candidate) != state_diff.result_volume_sha256:
        raise WorldVolumeError("StateDiff replay hash does not match its declared result")
    return candidate


@dataclass(frozen=True, slots=True)
class RegisteredTransition:
    state_diff_id: str
    source_state_sha256: str
    result_state_sha256: str
    event_id: str
    event_role: str
    evidence_identity: str
    authorization_status: str
    external_action_authorized: bool
    reported_content_status: str | None
    _output_json: str

    @property
    def output_state(self) -> dict[str, Any]:
        return json.loads(self._output_json)

    def replay(self, parent: Mapping[str, Any]) -> dict[str, Any]:
        if _canonical_sha256(parent) != self.source_state_sha256:
            raise WorldVolumeError("registered transition parent content changed")
        result = self.output_state
        if _canonical_sha256(result) != self.result_state_sha256:
            raise WorldVolumeError("registered transition output content changed")
        return result


def _registered_time(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise WorldVolumeError(f"{label} requires an aware timestamp")
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise WorldVolumeError(f"{label} requires an aware timestamp") from error
    if instant.tzinfo is None:
        raise WorldVolumeError(f"{label} requires an aware timestamp")
    return instant


def freeze_object_identity(record: Mapping[str, Any]) -> dict[str, Any]:
    """Bind tracking criteria independently of changing observed membership."""

    obj = _native_snapshot(record, label="object identity", error_type=WorldVolumeError)
    fields = ("object_id", "object_type", "K", "SP", "window", "subsystem", "source_revision")
    if not isinstance(obj, dict) or any(key not in obj for key in fields):
        raise WorldVolumeError("object identity requires frozen object/K/SP/window/subsystem/source")
    if not all(isinstance(obj[key], str) and obj[key].strip() for key in ("object_id", "object_type", "subsystem", "source_revision")):
        raise WorldVolumeError("object identity has an empty scope")
    if not isinstance(obj["K"], dict) or set(obj["K"]) != {"version", "definition"} or not all(obj["K"].values()):
        raise WorldVolumeError("object K requires a version and tracking definition")
    if not isinstance(obj["SP"], dict) or set(obj["SP"]) != set(AXES):
        raise WorldVolumeError("object identity requires exactly nine SP axes")
    if not isinstance(obj["window"], dict) or not obj["window"]:
        raise WorldVolumeError("object identity requires a frozen window")
    frozen = {key: obj[key] for key in fields}
    return {**frozen, "K_sha256": _canonical_sha256(obj["K"]), "binding_sha256": _canonical_sha256(frozen)}


def validate_identity_continuation(
    previous: Mapping[str, Any], current: Mapping[str, Any], *,
    recheck_id: str | None = None,
    identity_rechecks: Mapping[str, Mapping[str, Any]] | None = None,
) -> str:
    before, after = freeze_object_identity(previous), freeze_object_identity(current)
    if before["K"]["definition"] != after["K"]["definition"] and before["K"]["version"] == after["K"]["version"]:
        raise WorldVolumeError("changed K definition requires a new immutable version")
    compatible = all(before[key] == after[key] for key in ("object_id", "object_type", "K", "SP", "subsystem", "source_revision"))
    if compatible:
        return "same_K"
    check = (identity_rechecks or {}).get(recheck_id)
    if (
        not isinstance(check, Mapping) or check.get("recheck_id") != recheck_id
        or check.get("previous_binding_sha256") != before["binding_sha256"]
        or check.get("current_binding_sha256") != after["binding_sha256"]
        or check.get("status") != "supported" or not check.get("evidence_refs")
        or check.get("independent") is not True
    ):
        raise WorldVolumeError("cross-K or scope continuation requires an independent identity recheck")
    return "rechecked"


def validate_prototype_record(
    record: Mapping[str, Any], *, identity_record: Mapping[str, Any],
    evidence_registry: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate item-level descriptive prototype responsibilities."""

    snapshot = _native_snapshot(record, label="prototype", error_type=WorldVolumeError)
    frozen = freeze_object_identity(identity_record)
    if snapshot.get("object_id") != frozen["object_id"] or snapshot.get("identity_binding_sha256") != frozen["binding_sha256"]:
        raise WorldVolumeError("prototype does not bind the immutable object/K/scope")
    if frozen["object_type"] != "human":
        raise WorldVolumeError("human prototypes require a human collective object")
    if snapshot.get("normative_status") != "descriptive_only" or snapshot.get("action_authorization") != "none":
        raise WorldVolumeError("prototype classification cannot grant action authority")
    candidates = snapshot.get("candidate_states")
    if not isinstance(candidates, list) or len(candidates) != len(set(candidates)) or not set(candidates).issubset({f"S{i}" for i in range(7)}):
        raise WorldVolumeError("prototype candidates must be unique S0-S6 states")
    mode = snapshot.get("classification_mode")
    if mode == "single_dominant" and len(candidates) != 1 or mode in {"mixed", "parallel"} and (len(candidates) < 2 or not snapshot.get("path_candidates")) or mode == "unknown" and candidates or mode not in {"single_dominant", "mixed", "parallel", "unknown"}:
        raise WorldVolumeError("prototype classification mode differs from candidate coverage")
    conditions = snapshot.get("conditions")
    categories = {"entry", "exit", "observation", "counterexample", "falsification"}
    if not isinstance(conditions, dict) or set(conditions) != categories:
        raise WorldVolumeError("prototype requires all five item-level condition families")
    object_refs = snapshot.get("object_evidence_refs")
    if not isinstance(object_refs, list) or not object_refs:
        raise WorldVolumeError("prototype requires independently resolved object evidence")

    def evidence_check(refs: object, *, supported: bool = False) -> None:
        if not isinstance(refs, list) or supported and not refs:
            raise WorldVolumeError("prototype supported item requires object evidence")
        for ref in refs:
            item = evidence_registry.get(ref)
            if ref not in object_refs or not isinstance(item, Mapping) or item.get("evidence_id") != ref or item.get("object_id") != frozen["object_id"] or not item.get("source_refs"):
                raise WorldVolumeError("prototype evidence does not resolve the external object registry")
            if supported and item.get("identity") != "observed":
                raise WorldVolumeError("prototype cannot upgrade report content or simulation to object observation")

    evidence_check(object_refs)
    seen: set[str] = set()
    for category, rows in conditions.items():
        if not isinstance(rows, list) or candidates and {row.get("state_id") for row in rows} != set(candidates):
            raise WorldVolumeError("prototype condition items do not cover each candidate")
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"item_id", "state_id", "status", "evidence_refs", "reason"} or row["item_id"] in seen or not row["reason"]:
                raise WorldVolumeError("prototype condition item is missing, duplicate or unexplained")
            seen.add(row["item_id"])
            if row["status"] not in {"supported", "null_supported", "unsupported_or_undecided", "not_evaluated"}:
                raise WorldVolumeError("prototype condition result is invalid")
            evidence_check(row["evidence_refs"], supported=row["status"] in {"supported", "null_supported"})
            if mode == "unknown" and row["status"] in {"supported", "null_supported"}:
                raise WorldVolumeError("unknown prototype cannot retain supported condition results")
            if category == "falsification" and row["status"] == "supported" and row["state_id"] in candidates:
                raise WorldVolumeError("supported falsification blocks the candidate")
    for category in ("entry", "observation"):
        if any(not any(row["state_id"] == candidate and row["status"] == "supported" for row in conditions[category]) for candidate in candidates):
            raise WorldVolumeError("candidate lacks supported entry and observation evidence")
    for missing in snapshot.get("missing_data", []):
        if missing.get("status") not in {"not_collected", "not_observable", "not_applicable", "conflicted", "unknown"} or not missing.get("reason"):
            raise WorldVolumeError("prototype missing-data state is not explicit")
    if mode == "unknown" and not snapshot.get("missing_data"):
        raise WorldVolumeError("unknown prototype must explain missing distinctions")
    for path in snapshot.get("path_candidates", []):
        if path.get("origin_state") not in candidates or not path.get("path_id") or not path.get("reason"):
            raise WorldVolumeError("prototype path must bind a registered origin")
        evidence_check(path.get("evidence_refs", []))
        if path.get("path_type") == "X0" and path.get("exit_status") == "completed" and not all(path.get(key) for key in ("receiver_refs", "debt_disposition_refs", "commitment_disposition_refs")):
            raise WorldVolumeError("completed X0 requires resolved receivers, debt and commitments")
    reviewers = snapshot.get("reviewers")
    if not isinstance(reviewers, list) or not reviewers:
        raise WorldVolumeError("prototype requires structured independent review")
    object_alias = unicodedata.normalize("NFKC", frozen["object_id"]).strip().casefold()
    for reviewer in reviewers:
        reviewer_id = reviewer.get("reviewer_id")
        if not isinstance(reviewer_id, str):
            raise WorldVolumeError("prototype reviewer identity is missing")
        normalized = unicodedata.normalize("NFKC", reviewer_id).strip().casefold()
        if not normalized or re.search(r"(?<!\w)" + re.escape(object_alias) + r"(?!\w)", normalized) or normalized.startswith(object_alias + "_") or reviewer.get("independent") is not True or reviewer.get("material_version") != snapshot.get("material_version") or not reviewer.get("outcome"):
            raise WorldVolumeError("prototype review is not independently identity-bound")
        _registered_time(reviewer.get("reviewed_at"), "prototype review time")
    for field in ("appeal", "rollback"):
        procedure = snapshot.get(field)
        if not isinstance(procedure, dict) or not procedure.get("procedure_id") or not procedure.get("status"):
            raise WorldVolumeError("prototype requires structured appeal and rollback")
    return snapshot


def apply_registered_event(
    parent: Mapping[str, Any],
    event: Mapping[str, Any],
    *,
    evidence_registry: Mapping[str, Mapping[str, Any]],
    channel_registry: Mapping[str, Mapping[str, Any]] | None = None,
    authorization_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> RegisteredTransition:
    """Apply evidence-bound direct observations to a frozen registered state."""

    state = _native_snapshot(parent, label="registered state", error_type=WorldVolumeError)
    record = _native_snapshot(event, label="registered event", error_type=WorldVolumeError)
    evidence = _native_snapshot(dict(evidence_registry), label="event evidence", error_type=WorldVolumeError)
    if not isinstance(state, dict) or not isinstance(record, dict):
        raise WorldVolumeError("registered state and event must be objects")
    path = record.get("update_path")
    kind = record.get("kind")
    allowed_kinds = {
        "observed_direct": {"observed"}, "reported_belief": {"reported"},
        "scenario": {"planned", "hypothetical", "simulated"},
        "mechanism_inference": {"hypothetical", "simulated", "inferred"},
    }
    if kind not in allowed_kinds.get(path, set()):
        raise WorldVolumeError("unsupported event update path")
    if path in {"observed_direct", "reported_belief"} and record.get("occurrence_status") != "occurred":
        raise WorldVolumeError("direct observation requires actual occurrence")
    if path in {"scenario", "mechanism_inference"} and record.get("occurrence_status") != "not_occurred":
        raise WorldVolumeError("scenario cannot claim actual occurrence")
    if path == "observed_direct" and record.get("mechanism_id") is not None:
        raise WorldVolumeError("direct observation cannot manufacture a mechanism inference")
    cutoff = _registered_time(state.get("evidence_cutoff"), "evidence cutoff")
    occurred = _registered_time(record.get("occurred_at"), "event occurrence")
    if path in {"observed_direct", "reported_belief"} and occurred > cutoff:
        raise WorldVolumeError("event occurs after frozen evidence cutoff")
    if record.get("authorization_status") not in {"authorized", "unauthorized", "unknown"}:
        raise WorldVolumeError("event authorization status is missing")
    refs = record.get("evidence_refs")
    if not isinstance(refs, list) or not refs or len(refs) != len(set(refs)):
        raise WorldVolumeError("event occurrence requires independent evidence references")
    used_evidence: dict[str, Mapping[str, Any]] = {}
    for ref in refs:
        item = evidence.get(ref)
        if not isinstance(item, dict) or item.get("evidence_id") != ref or item.get("event_id") != record.get("event_id") or item.get("identity") != kind or not item.get("source_refs"):
            raise WorldVolumeError("event occurrence evidence is unresolved or has a different identity")
        availability = _registered_time(item.get("available_at"), "event evidence availability")
        if availability > cutoff or path in {"observed_direct", "reported_belief"} and availability < occurred:
            raise WorldVolumeError("event occurrence evidence exceeds its frozen observation window")
        used_evidence[ref] = item
    if record["authorization_status"] == "authorized":
        authorization = (authorization_registry or {}).get(record.get("authorization_ref"))
        if (
            not isinstance(authorization, Mapping)
            or authorization.get("authorization_id") != record.get("authorization_ref")
            or authorization.get("status") != "valid"
            or not authorization.get("source_refs")
            or any(authorization.get(key) != record.get(key) for key in ("actor_id", "object_id", "event_id"))
            or not (_registered_time(authorization.get("starts_at"), "authorization start") <= occurred <= _registered_time(authorization.get("ends_at"), "authorization end"))
        ):
            raise WorldVolumeError("event lacks exact independent external authorization")
    objects = _records_by_id(state["objects"], "object_id", label="registered object")
    if record.get("object_id") not in objects:
        raise WorldVolumeError("event object does not resolve the registered state")
    channel: Mapping[str, Any] | None = None
    if path == "mechanism_inference":
        channel = (channel_registry or {}).get(record.get("channel_id"))
        if (
            not isinstance(channel, Mapping) or channel.get("channel_id") != record.get("channel_id")
            or channel.get("mechanism_id") != record.get("mechanism_id") or not record.get("mechanism_id")
            or channel.get("from_object_id") != record["object_id"]
            or channel.get("to_object_id") not in objects
            or channel.get("active") is not True or channel.get("identity_preserved") is not True
            or channel.get("acl_authorized") is not True
            or type(channel.get("capacity")) is not int or channel["capacity"] < len(record["deltas"])
            or type(channel.get("lag_seconds")) not in {int, float} or channel["lag_seconds"] < 0
            or not channel.get("evidence_refs") or not isinstance(channel.get("threshold_conditions"), list)
        ):
            raise WorldVolumeError("inferred propagation requires a real identity/ACL/capacity-bound channel")
        source_time = _registered_time(record.get("source_time", record.get("occurred_at")), "channel source time")
        if not (_registered_time(channel.get("valid_from"), "channel start") <= source_time <= occurred <= _registered_time(channel.get("valid_until"), "channel end")) or (occurred - source_time).total_seconds() < channel["lag_seconds"]:
            raise WorldVolumeError("inferred propagation exceeds channel temporal validity")
        for ref in channel["evidence_refs"]:
            item = evidence.get(ref)
            if not isinstance(item, Mapping) or item.get("evidence_id") != ref or item.get("channel_id") != channel["channel_id"] or item.get("mechanism_id") != record["mechanism_id"] or item.get("support_status") != "supported" or item.get("identity") != "observed" or not item.get("source_refs") or _registered_time(item.get("available_at"), "channel evidence time") > cutoff:
                raise WorldVolumeError("channel lacks independent causal/timing evidence")
            used_evidence[ref] = item
        for condition in channel["threshold_conditions"]:
            target = objects.get(condition.get("object_id"))
            variable = next((v for v in target["variables"] if v["variable_id"] == condition.get("variable_id")), None) if target else None
            if variable is None:
                raise WorldVolumeError("channel threshold targets an unknown variable")
            value, operand, op = variable["value"], condition.get("operand"), condition.get("operator")
            matches = _same_json_value(value, operand) if op == "eq" else type(value) in {int, float} and type(operand) in {int, float} and (value >= operand if op == "ge" else value <= operand if op == "le" else False)
            if not matches:
                raise WorldVolumeError("channel structured local threshold is not met")
    seen: set[tuple[str, str]] = set()
    for delta in record["deltas"]:
        key = (delta["object_id"], delta["variable_id"])
        if key in seen or delta["object_id"] not in objects:
            raise WorldVolumeError("event has a duplicate or unknown target")
        seen.add(key)
        variables = _records_by_id(objects[delta["object_id"]]["variables"], "variable_id", label="registered variable")
        variable = variables.get(delta["variable_id"])
        if path == "reported_belief" and delta.get("category") != "beliefs":
            raise WorldVolumeError("reported content can only update source-labelled beliefs")
        if channel is not None and delta["object_id"] != channel["to_object_id"]:
            raise WorldVolumeError("propagation delta is outside channel target")
        if delta.get("category") not in {"resources", "rules", "relations", "beliefs", "feasible_actions"} or delta.get("clock_id") not in CLOCK_KINDS:
            raise WorldVolumeError("delta category or clock is not registered")
        if (
            variable is None
            or variable["category"] != delta["category"]
            or variable["clock_id"] != delta["clock_id"]
            or not _same_json_value(variable["value"], delta["before"])
            or _same_json_value(delta["before"], delta["after"])
        ):
            raise WorldVolumeError("event delta differs from registered variable")
        refs = delta["evidence_refs"]
        if not refs or not set(refs).issubset(set(record["evidence_refs"])):
            raise WorldVolumeError("event delta has no exact evidence coverage")
        for ref in refs:
            item = evidence.get(ref)
            if (
                item is None or item.get("evidence_id") != ref
                or item.get("identity") != kind or not item.get("source_refs")
                or item.get("event_id") != record["event_id"]
                or item.get("object_id") != delta["object_id"]
                or item.get("variable_id") != delta["variable_id"]
                or not _same_json_value(item.get("observed_value"), delta["after"])
            ):
                raise WorldVolumeError("direct observation lacks independently resolved target evidence")
            if _registered_time(item.get("available_at"), "evidence availability") > cutoff:
                raise WorldVolumeError("late evidence requires a new frozen run")
        variable["value"] = copy.deepcopy(delta["after"])
        variable["provenance"] = {"event_id": record["event_id"], "identity": kind, "update_path": path, "evidence_refs": list(refs), "conditions": copy.deepcopy(record["conditions"]), "channel_id": record.get("channel_id"), "mechanism_id": record.get("mechanism_id")}
    payload = {"parent": parent, "event": record, "evidence": used_evidence, "channel": channel, "authorization": (authorization_registry or {}).get(record.get("authorization_ref")), "output": state}
    return RegisteredTransition(
        state_diff_id="DIFF-" + _canonical_sha256(payload)[:20].upper(),
        source_state_sha256=_canonical_sha256(parent), result_state_sha256=_canonical_sha256(state),
        event_id=record["event_id"], event_role=(path if path in {"scenario", "mechanism_inference"} else "u(t)" if path == "observed_direct" and record["authorization_status"] == "authorized" else "e(t)"), evidence_identity=kind,
        authorization_status=record["authorization_status"], external_action_authorized=False,
        reported_content_status="unknown" if kind == "reported" else None,
        _output_json=json.dumps(state, ensure_ascii=False, allow_nan=False, sort_keys=True),
    )


def apply_registered_events(
    parent: Mapping[str, Any], events: Sequence[Mapping[str, Any]], *,
    evidence_registry: Mapping[str, Mapping[str, Any]],
    channel_registry: Mapping[str, Mapping[str, Any]] | None = None,
    authorization_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[RegisteredTransition, ...]:
    times = [_registered_time(event.get("occurred_at"), "event time order") for event in events]
    if times != sorted(times) or len({event.get("event_id") for event in events}) != len(events):
        raise WorldVolumeError("events require unique identities and frozen time order")
    state: Mapping[str, Any] = parent
    transitions: list[RegisteredTransition] = []
    for event in events:
        transition = apply_registered_event(state, event, evidence_registry=evidence_registry, channel_registry=channel_registry, authorization_registry=authorization_registry)
        transitions.append(transition)
        state = transition.output_state
    return tuple(transitions)


def registered_event_target_hashes(events: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    catalog: dict[str, str] = {}
    seen: set[str] = set()
    for event in events:
        identifier = event.get("event_id")
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise WorldVolumeError("registered event target catalog requires unique event IDs")
        seen.add(identifier)
        for index, delta in enumerate(event["deltas"]):
            catalog[f"events.{identifier}.deltas[{index}]"] = _canonical_sha256(delta)
    return catalog


def bind_registered_event_evidence(
    parent: Mapping[str, Any], events: Sequence[Mapping[str, Any]], *,
    evidence_ledger: Mapping[str, Any], retrieval_index: Mapping[str, Any],
    bindings: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Adapt frozen version-four material support to exact registered deltas."""

    from .evidence import validate_evidence_ledger
    from .v4_contracts import evidence_supports_claim

    ledger = _native_snapshot(evidence_ledger, label="registered XK3 ledger", error_type=WorldVolumeError)
    retrieval = _native_snapshot(retrieval_index, label="registered XK2 sources", error_type=WorldVolumeError)
    if ledger.get("schema_version") != 4 or ledger.get("run_id") != parent.get("run_id") or retrieval.get("run_id") != parent.get("run_id"):
        raise WorldVolumeError("registered events require a same-run version-four evidence ledger")
    if validate_evidence_ledger(ledger, retrieval):
        raise WorldVolumeError("registered event evidence failed the frozen P04 ledger validator")
    by_event = _records_by_id(events, "event_id", label="registered event")
    by_claim = _records_by_id(ledger["claims"], "claim_id", label="registered claim")
    by_evidence = _records_by_id(ledger["evidence"], "evidence_id", label="registered evidence")
    by_source = _records_by_id(retrieval["sources"], "source_id", label="registered source")
    edges = {(edge["claim_id"], edge["evidence_id"], edge["source_id"]) for edge in ledger["support_edges"]}
    targets = registered_event_target_hashes(events)
    registry: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        if not isinstance(binding, Mapping) or set(binding) != {"event_id", "delta_index", "evidence_ref", "xk3_evidence_id"}:
            raise WorldVolumeError("event evidence binding has an inexact field set")
        event = by_event.get(binding["event_id"])
        index, ref = binding["delta_index"], binding["evidence_ref"]
        item = by_evidence.get(binding["xk3_evidence_id"])
        if event is None or type(index) is not int or not 0 <= index < len(event["deltas"]) or ref in registry or item is None:
            raise WorldVolumeError("event evidence binding is duplicate or unresolved")
        delta = event["deltas"][index]
        claim = by_claim[item["claim_id"]]
        source = by_source[item["source_id"]]
        target_path = f"events.{event['event_id']}.deltas[{index}]"
        expected_target = {"target_path": target_path, "target_sha256": targets[target_path], "relation": "descriptive"}
        if expected_target not in claim["world_targets"] or ref not in event["evidence_refs"] or ref not in delta["evidence_refs"] or (claim["claim_id"], item["evidence_id"], item["source_id"]) not in edges or not evidence_supports_claim(item, claim):
            raise WorldVolumeError("P04 material support does not bind the exact event delta")
        if event["kind"] == "observed" and (claim["claim_basis"]["kind"] != "domain_empirical" or item["support_checks"]["world_fact_supported"]["status"] != "passed"):
            raise WorldVolumeError("a source assertion or unconfirmed content cannot become an observed world update")
        available_at = source.get("accessed_at")
        _registered_time(available_at, "frozen material access time")
        registry[ref] = {
            "evidence_id": ref, "identity": event["kind"], "source_refs": [item["source_id"]],
            "available_at": available_at, "event_id": event["event_id"],
            "object_id": delta["object_id"], "variable_id": delta["variable_id"],
            "observed_value": copy.deepcopy(delta["after"]),
            "xk3_evidence_id": item["evidence_id"], "claim_id": claim["claim_id"],
            "material_identity": copy.deepcopy(item["evidence_identity"]),
            "support_checks": copy.deepcopy(item["support_checks"]),
            "research_context": copy.deepcopy(item["research_context"]),
            "claim_basis": copy.deepcopy(claim["claim_basis"]),
            "formal_qualification": copy.deepcopy(claim["formal_qualification"]),
            "visibility": item["visibility"], "protected_review": copy.deepcopy(item["protected_review"]),
            "target_binding": expected_target,
        }
    required_refs = {ref for event in events for delta in event["deltas"] for ref in delta["evidence_refs"]}
    if set(registry) != required_refs:
        raise WorldVolumeError("registered event deltas lack exact external evidence coverage")
    return registry


__all__ = (
    "RegisteredTransition",
    "StateDiff",
    "WorldVolumeError",
    "apply_event",
    "bind_world_evidence_state",
    "replay_state_diff",
    "world_evidence_target_catalog",
    "world_evidence_target_hashes",
    "validate_world_volume",
    "apply_registered_event",
    "apply_registered_events",
    "freeze_object_identity",
    "validate_identity_continuation",
    "validate_prototype_record",
    "registered_event_target_hashes",
    "bind_registered_event_evidence",
)
