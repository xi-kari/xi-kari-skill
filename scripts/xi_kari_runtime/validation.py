"""Fresh, disk-authoritative validation for Xi-Kari v2 runs."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from .authority import repository_root as resolve_repository_root
from .authority import validator_set_sha256 as compute_validator_set_sha256
from .authoring import validate_semantic_probe_authorings
from .canonical_json import confined_path, read_json, read_json_text, sha256_file, sha256_json
from .concept_authority import load_concept_authority
from .contracts import (
    COMPLETE_STATE_MISMATCH_ERROR,
    PREMATURE_COMPLETE_STATE_ERROR,
    DELIVERY_PATHS,
    DYNAMIC_PHASE_FIELDS,
    PHASE_RESPONSIBILITIES,
    PRODUCTION_CONTRACT_PROFILE,
    build_phase_artifact_bindings,
    derive_repair_scope,
    expected_phase_artifact_paths,
    is_safe_run_id,
    provisional_delivery_paths,
    require_packet_contract,
    required_delivery_paths,
    build_continuity_bundle_binding,
    validate_lifecycle_sidecars,
    validate_packet_references,
    validate_repair_packet_binding,
    validate_runtime_control_bindings,
)
from .coverage import (
    build_coverage,
    build_semantic_coverage,
    load_reader_outputs,
    validate_coverage,
)
from .evidence import build_evidence_ledger, validate_evidence_ledger
from .judgment import (
    empty_framework_gap_ledger,
    validate_action_ranking,
    validate_framework_gap_isolation,
    validate_verdict_bundle,
)
from .phase_chain import (
    PHASES,
    compute_record_sha256,
    load_phase_records,
    validate_phase_chain,
)
from .prose import (
    build_prose_plan,
    check_plain_language,
    render_answer,
    render_artifact_index,
    render_atlas,
    render_casebook,
    render_dossier,
)
from .semantic_chain import validate_semantic_chain
from .semantic_projection import protected_retrieval_values
from .semantic_read_trace import validate_semantic_read_trace
from .ontology_read_trace import validate_ontology_read_trace
from .problem_contract import contract_hash
from .stability import validate_sensitivity_report, validate_stance_stability_report
from .retrieval import validate_full_source_lock, validate_retrieval_bundle
from .transformations import validate_cascade
from .world_volume import (
    bind_world_evidence_state,
    validate_world_volume,
    world_evidence_target_hashes,
)
from .terminal_authority import (
    COMPLETION_RELATIVE,
    KEY_RELATIVE,
    OFFICIAL_REPORT_RELATIVE,
    TERMINAL_RELATIVE,
    TRANSACTION_RELATIVE,
    validate_terminal_closure,
)


VALIDATOR_VERSION = "xk-fresh-validator-3"
DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def validator_fingerprint(report: Mapping[str, Any]) -> str:
    """Hash the stable portion of a fresh validator report."""

    stable = {
        key: report.get(key)
        for key in (
            "schema_id",
            "schema_version",
            "validator_version",
            "validator_set_sha256",
            "run_id",
            "fresh",
            "fresh_process",
            "validation_boundary",
            "complete",
            "validated_phase",
            "chain_head_sha256",
            "phase_count",
            "checks",
            "valid",
            "errors",
        )
    }
    return sha256_json(stable)

ARTIFACT_SCHEMA_IDS = {
    "artifacts/artifact-manifest.json": {"xi-kari.v2.artifact-manifest"},
    "authoring/XK01-read-events.jsonl": {"xi-kari.v2.source-read-event"},
    "authoring/XK01-read-plan.json": {"xi-kari.v2.read-plan"},
    "authoring/XK01-semantic-read-trace.json": {
        "xi-kari.v2.semantic-read-trace"
    },
    "authoring/XK01-base-authoring-receipt.json": {
        "xi-kari.v2.base-authoring-execution"
    },
    "authoring/XK04-ontology-read-plan.json": {
        "xi-kari.v2.ontology-read-plan"
    },
    "authoring/XK04-ontology-read-trace.json": {
        "xi-kari.v2.ontology-read-trace"
    },
    "authoring/XK01-base-authoring-events.jsonl": {
        "xi-kari.v2.codex-jsonl-event"
    },
    "authoring/XK01-base-authoring-request.json": {
        "xi-kari.v2.base-authoring-request"
    },
    "authoring/XK02-semantic-retrieval.json": {
        "xi-kari.v2.retrieval-semantic-input"
    },
    "authoring/XK02-retrieval-execution-receipt.json": {
        "xi-kari.v2.retrieval-execution-receipt",
        "xi-kari.v2.closed-input-execution",
    },
    "authoring/XK02-host-capture-index.json": {
        "xi-kari.v2.host-capture-index"
    },
    "authoring/XK02-retrieval-ledger.json": {"xi-kari.v2.retrieval-ledger"},
    "authoring/XK03-evidence-ledger.json": {"xi-kari.v2.evidence-ledger"},
    "authoring/XK03-unknown-register.json": {"xi-kari.v2.unknown-register"},
    "authoring/XK04-concept-closure-report.json": {
        "xi-kari.v2.concept-closure-report"
    },
    "authoring/XK04-concept-disposition.json": {"xi-kari.v2.concept-disposition"},
    "authoring/XK05-local-world-model.json": {
        "xi-kari.v2.xk.world-volume",
        "xi-kari.v2.not-applicable",
    },
    "authoring/XK06-transformation-ledger.json": {
        "xi-kari.v2.xk.transformation-ledger",
        "xi-kari.v2.not-applicable",
    },
    "authoring/XK06-cascade.json": {
        "xi-kari.v2.xk.transform-cascade",
        "xi-kari.v2.not-applicable",
    },
    "authoring/XK07-case-ledger.json": {"xi-kari.v2.case-ledger"},
    "authoring/XK07-claim-mechanism-graph.json": {
        "xi-kari.v2.xk.claim-mechanism-graph",
        "xi-kari.v2.not-applicable",
    },
    "authoring/XK08-recursive-lineage.json": {
        "xi-kari.v2.xk.recursive-lineage",
        "xi-kari.v2.not-applicable",
    },
    "authoring/XK09-order-evaluation.json": {"xi-kari.v2.order-evaluation"},
    "authoring/XK09-semantic-authoring-bundle.json": {
        "xi-kari.v2.semantic-probe-authorings",
        "xi-kari.v2.not-applicable",
    },
    "authoring/XK09-red-team-report.json": {"xi-kari.v2.red-team-report"},
    "authoring/XK09-stance-pair.json": {"xi-kari.v2.stance-pair"},
    "authoring/XK09-sensitivity-report.json": {
        "xi-kari.v2.sensitivity-report",
        "xi-kari.v2.not-applicable",
    },
    "authoring/XK09-stance-stability-report.json": {
        "xi-kari.v2.stance-stability-report",
        "xi-kari.v2.not-applicable",
    },
    "authoring/XK10-action-ranking.json": {
        "xi-kari.v2.xk.action-ranking",
        "xi-kari.v2.not-applicable",
    },
    "authoring/XK10-forecast-ledger.json": {"xi-kari.v2.forecast-ledger"},
    "authoring/XK10-framework-gap-ledger.json": {
        "xi-kari.v2.xk.framework-gap-ledger",
        "xi-kari.v2.not-applicable",
    },
    "authoring/XK10-verdict.json": {
        "xi-kari.v2.xk.verdict",
        "xi-kari.v2.not-applicable",
    },
    "authoring/XK11-output-plan.json": {"xi-kari.v2.prose-plan"},
    "authoring/XK11-prose-review.json": {"xi-kari.v2.prose-review"},
    "authoring/XK11-semantic-coverage.json": {"xi-kari.v2.semantic-coverage"},
    "capability-snapshot.json": {"xi-kari.v2.capability-snapshot"},
    "continuation/cancel.json": {"xi-kari.v2.cancel"},
    COMPLETION_RELATIVE: {"xi-kari.v2.completion"},
    "continuation/input-packet.json": {"xi-kari.v2.analysis-packet"},
    "continuation/parent.json": {"xi-kari.v2.parent-binding"},
    "continuation/repair-plan.json": {"xi-kari.v2.repair-plan"},
    "continuation/repair-record.json": {"xi-kari.v2.repair-record"},
    "continuation/state.json": {"xi-kari.v2.continuation-state"},
    KEY_RELATIVE: {"xi-kari.v2.terminal-authority-key"},
    TERMINAL_RELATIVE: {"xi-kari.v2.terminal-record"},
    TRANSACTION_RELATIVE: {"xi-kari.v2.xk12-transaction"},
    "delivery/final-chat.json": {"xi-kari.v2.final-chat"},
    "phase-events.jsonl": {"xi-kari.v2.phase-event"},
    "retrieval/index.json": {"xi-kari.v2.retrieval-index"},
    "run-contract.json": {"xi-kari.v2.run-contract"},
    "source-lock.json": {"xi-kari.v2.source-lock"},
    "validation/attempts/final/validator-report.json": {
        "xi-kari.v2.validator-report"
    },
    OFFICIAL_REPORT_RELATIVE: {"xi-kari.v2.validator-report"},
}
ARTIFACT_SCHEMA_PATTERNS = (
    ("authoring/recursive-state/*.json", {"xi-kari.v2.xk.recursive-state"}),
    ("retrieval/assessments/*.json", {"xi-kari.v2.source-assessment"}),
    ("retrieval/sources/*.json", {"xi-kari.v2.source-record"}),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def validator_set_sha256(repository_root: Path | None = None) -> str:
    return compute_validator_set_sha256(
        Path(repository_root or DEFAULT_REPOSITORY_ROOT),
        require_complete=False,
    )


def _read(path: Path, errors: list[str], label: str) -> Any:
    try:
        return read_json(path)
    except Exception as exc:
        errors.append(f"cannot read {label}: {exc}")
        return None


def _expected_artifact_schema_ids(relative: str) -> set[str] | None:
    expected = ARTIFACT_SCHEMA_IDS.get(relative)
    if expected is not None:
        return expected
    path = Path(relative)
    for pattern, schema_ids in ARTIFACT_SCHEMA_PATTERNS:
        if path.match(pattern):
            return schema_ids
    return None


def _schema_id_constants(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        properties = value.get("properties")
        if isinstance(properties, dict):
            schema_id = properties.get("schema_id")
            if isinstance(schema_id, dict) and isinstance(schema_id.get("const"), str):
                found.add(schema_id["const"])
        for child in value.values():
            found.update(_schema_id_constants(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_schema_id_constants(child))
    return found


def _runtime_schema_registry(
    repository_root: Path, errors: list[str]
) -> dict[str, Draft202012Validator]:
    validators: dict[str, Draft202012Validator] = {}
    owners: dict[str, Path] = {}
    documents: list[tuple[Path, dict[str, Any]]] = []
    resources: Registry[Any] = Registry()
    schema_paths = sorted((repository_root / "schemas").glob("xk-*.json"))
    if not schema_paths:
        errors.append("no Xi-Kari v2 runtime schemas found")
        return validators
    for path in schema_paths:
        schema = _read(path, errors, f"runtime schema {path}")
        if not isinstance(schema, dict):
            continue
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            errors.append(f"invalid runtime schema {path}: {exc}")
            continue
        schema_uri = schema.get("$id")
        if isinstance(schema_uri, str) and schema_uri:
            try:
                resources = resources.with_resource(
                    schema_uri, Resource.from_contents(schema)
                )
            except Exception as exc:
                errors.append(f"invalid runtime schema resource {path}: {exc}")
                continue
        documents.append((path, schema))
    for path, schema in documents:
        for schema_id in sorted(_schema_id_constants(schema)):
            previous = owners.setdefault(schema_id, path)
            if previous != path:
                errors.append(
                    "runtime schema_id has multiple owners: "
                    f"{schema_id}: {previous}, {path}"
                )
                continue
            validators[schema_id] = Draft202012Validator(
                schema,
                format_checker=FormatChecker(),
                registry=resources,
            )
    return validators


def _json_records(path: Path) -> list[tuple[int | None, Any]]:
    if path.suffix == ".jsonl":
        return [
            (line_number, read_json_text(line))
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            )
            if line.strip()
        ]
    return [(None, read_json(path))]


def _validate_path_owned_json(
    run_dir: Path, repository_root: Path, errors: list[str]
) -> None:
    registry = _runtime_schema_registry(repository_root, errors)
    allowed_non_json = {
        relative
        for relative in required_delivery_paths()
        if Path(relative).suffix not in {".json", ".jsonl"}
    }
    allowed_non_json.update(
        {
            "authoring/XK01-base-authoring-prompt.txt",
            "authoring/XK01-base-authoring-output.bin",
        }
    )
    capture_index_path = run_dir / "authoring/XK02-host-capture-index.json"
    capture_paths: set[str] = set()
    if capture_index_path.is_file() and not capture_index_path.is_symlink():
        try:
            capture_index = read_json(capture_index_path)
            rows = capture_index.get("captures", [])
            if not isinstance(rows, list):
                raise ValueError("host capture index captures is not a list")
            for row in rows:
                relative = row.get("body_path") if isinstance(row, dict) else None
                if (
                    not isinstance(relative, str)
                    or not relative.startswith("retrieval/captures/")
                    or Path(relative).suffix != ".bin"
                    or Path(relative).is_absolute()
                    or ".." in Path(relative).parts
                ):
                    errors.append("host capture body path is invalid")
                    continue
                capture_paths.add(relative)
                allowed_non_json.add(relative)
        except Exception as exc:
            errors.append(f"cannot read host capture index: {exc}")
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file() or path.suffix in {".json", ".jsonl"}:
            continue
        relative = path.relative_to(run_dir).as_posix()
        if relative not in allowed_non_json:
            errors.append(f"run artifact has no path owner: {relative}")
    observed_capture_paths = {
        path.relative_to(run_dir).as_posix()
        for path in run_dir.glob("retrieval/captures/*.bin")
        if path.is_file() and not path.is_symlink()
    }
    if observed_capture_paths != capture_paths:
        errors.append("host capture body paths differ from the capture index")
    paths = sorted([*run_dir.rglob("*.json"), *run_dir.rglob("*.jsonl")])
    if not paths:
        errors.append("run contains no JSON artifacts")
        return
    for path in paths:
        relative = path.relative_to(run_dir).as_posix()
        try:
            records = _json_records(path)
        except Exception as exc:
            errors.append(f"cannot parse run artifact {relative}: {exc}")
            continue
        if path.suffix == ".jsonl" and not records:
            errors.append(f"JSONL artifact is empty: {relative}")
        expected_schema_ids = _expected_artifact_schema_ids(relative)
        for line_number, value in records:
            location = relative if line_number is None else f"{relative}:{line_number}"
            if not isinstance(value, dict):
                errors.append(f"run artifact record is not an object: {location}")
                continue
            if relative == "authoring/XK01-base-authoring-events.jsonl":
                # Codex JSONL is a host protocol, not a Xi-Kari artifact
                # envelope.  Its event objects intentionally have no
                # schema_id; the execution and retrieval validators bind the
                # complete stream hash and event grammar separately.
                if not isinstance(value.get("type"), str) or not value["type"]:
                    errors.append(f"Codex event has no type: {location}")
                continue
            schema_id = value.get("schema_id")
            if not isinstance(schema_id, str) or not schema_id.startswith("xi-kari.v2."):
                errors.append(f"run artifact has no v2 schema_id: {location}")
                continue
            if expected_schema_ids is None:
                errors.append(f"run artifact has no path owner: {location}")
            elif schema_id not in expected_schema_ids:
                expected = ", ".join(sorted(expected_schema_ids))
                errors.append(
                    f"artifact path/schema mismatch: {location}: "
                    f"expected {expected}, observed {schema_id}"
                )
            validator = registry.get(schema_id)
            if validator is None:
                errors.append(f"run artifact has no schema owner: {location}: {schema_id}")
                continue
            for schema_error in sorted(
                validator.iter_errors(value), key=lambda item: list(item.path)
            ):
                field = ".".join(str(part) for part in schema_error.path) or "<record>"
                errors.append(
                    f"run artifact schema {location} {field}: {schema_error.message}"
                )


def _validate_wildcard_artifact_index(
    run_dir: Path,
    records: list[dict[str, Any]],
    retrieval_index: dict[str, Any] | None,
    errors: list[str],
) -> None:
    expected: set[str] = set()
    for record in records:
        if record.get("phase") != "XK8":
            continue
        fixed = set(expected_phase_artifact_paths("XK8"))
        for binding in record.get("artifact_bindings", []):
            if not isinstance(binding, dict):
                continue
            relative = binding.get("path")
            if isinstance(relative, str) and relative not in fixed:
                expected.add(relative)
    if isinstance(retrieval_index, dict):
        for binding in retrieval_index.get("sources", []):
            if not isinstance(binding, dict):
                continue
            for field in ("source_path", "assessment_path"):
                relative = binding.get(field)
                if isinstance(relative, str):
                    expected.add(relative)

    observed: set[str] = set()
    for pattern, _schema_ids in ARTIFACT_SCHEMA_PATTERNS:
        observed.update(
            path.relative_to(run_dir).as_posix()
            for path in run_dir.glob(pattern)
            if path.is_file()
        )
    for relative in sorted(observed - expected):
        errors.append(f"wildcard artifact is not indexed: {relative}")


def _run_symlinks(run_dir: Path) -> list[str]:
    found: list[str] = []
    for directory, dirnames, filenames in os.walk(run_dir, followlinks=False):
        parent = Path(directory)
        for name in [*dirnames, *filenames]:
            path = parent / name
            if path.is_symlink():
                found.append(path.relative_to(run_dir).as_posix())
    return sorted(set(found))


def _run_path_symlink(path: Path) -> Path | None:
    candidate = Path(path).expanduser().absolute()
    current = Path(candidate.anchor)
    for part in candidate.parts[1:]:
        current = current / part
        if current.is_symlink():
            return current
    return None


def _parent_run_candidates(run_dir: Path, parent_run_id: str) -> list[Path]:
    candidates: set[Path] = set()
    direct = run_dir.parent / parent_run_id
    if direct.is_dir() and not direct.is_symlink():
        candidates.add(direct.resolve())
    family_root = run_dir.parent.parent
    try:
        run_roots = list(family_root.iterdir())
    except OSError:
        run_roots = []
    for runs_root in run_roots:
        if not runs_root.is_dir() or runs_root.is_symlink():
            continue
        candidate = runs_root / parent_run_id
        if candidate.is_dir() and not candidate.is_symlink():
            candidates.add(candidate.resolve())
    return sorted(candidates)


def _structural_chain_errors(records: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    predecessor: str | None = None
    run_id: str | None = None
    for index, record in enumerate(records):
        phase = f"XK{index}"
        if record.get("phase") != phase or record.get("index") != index:
            errors.append(f"parent phase identity mismatch at index {index}")
        if run_id is None:
            run_id = record.get("run_id")
        elif record.get("run_id") != run_id:
            errors.append(f"parent run_id mismatch at {phase}")
        if record.get("predecessor_sha256") != predecessor:
            errors.append(f"parent predecessor mismatch at {phase}")
        if record.get("record_sha256") != compute_record_sha256(record):
            errors.append(f"parent record sha256 mismatch at {phase}")
        predecessor = record.get("record_sha256")
    if len(records) > len(PHASES):
        errors.append("parent phase chain has more than XK12")
    return errors


def _validate_parent_lineage(
    run_dir: Path,
    contract: dict[str, Any],
    repository_root: Path,
    errors: list[str],
    *,
    lineage_ancestors: frozenset[Path],
) -> None:
    continuation = contract.get("continuation", {})
    kind = continuation.get("kind")
    parent_path = run_dir / "continuation" / "parent.json"
    if kind == "original":
        if (
            continuation.get("generation") != 0
            or continuation.get("parent_run_id") is not None
            or continuation.get("parent_chain_head_sha256") is not None
            or parent_path.exists()
        ):
            errors.append("original run has forged continuation bindings")
        return
    if kind not in {"fork", "repair"}:
        errors.append("run continuation kind is invalid")
        return
    parent_run_id = continuation.get("parent_run_id")
    parent_chain_head = continuation.get("parent_chain_head_sha256")
    if not isinstance(parent_run_id, str) or not isinstance(parent_chain_head, str):
        errors.append("child run has incomplete parent continuation bindings")
        return
    if not is_safe_run_id(parent_run_id):
        errors.append(f"unsafe parent_run_id: {parent_run_id}")
        return
    binding = _read(parent_path, errors, "parent binding")
    if not isinstance(binding, dict):
        return
    expected_binding = {
        "run_id": contract.get("run_id"),
        "parent_run_id": parent_run_id,
        "parent_chain_head_sha256": parent_chain_head,
    }
    if any(binding.get(field) != value for field, value in expected_binding.items()):
        errors.append("parent binding differs from the child run contract")
    repair_path = run_dir / "continuation" / "repair-record.json"
    repair: dict[str, Any] | None = None
    if kind == "repair":
        repair_value = _read(repair_path, errors, "repair record")
        if isinstance(repair_value, dict):
            repair = repair_value
        if repair is not None and (
            repair.get("run_id") != contract.get("run_id")
            or repair.get("parent_run_id") != parent_run_id
            or repair.get("earliest_invalid_phase") != binding.get("base_phase")
        ):
            errors.append("repair record differs from the parent continuation binding")
    elif repair_path.exists():
        errors.append("fork run contains a repair record")
    candidates = _parent_run_candidates(run_dir, parent_run_id)
    if not candidates:
        errors.append("parent run is not present on disk")
        return
    if len(candidates) != 1:
        errors.append("parent run identity is ambiguous on disk")
        return
    parent = candidates[0]
    if parent in lineage_ancestors:
        errors.append("parent run lineage contains a cycle")
        return
    parent_symlinks = _run_symlinks(parent)
    if parent_symlinks:
        errors.extend(
            f"parent run path contains a symlink: {relative}"
            for relative in parent_symlinks
        )
        return
    parent_contract = _read(parent / "run-contract.json", errors, "parent run contract")
    if not isinstance(parent_contract, dict):
        return
    if parent_contract.get("run_id") != parent_run_id:
        errors.append("parent disk contract has a different run_id")
    if (
        parent_contract.get("repository_root") != str(repository_root)
        or parent_contract.get("validator_set_sha256")
        != contract.get("validator_set_sha256")
    ):
        errors.append("parent disk authority differs from the child run")
    if continuation.get("generation") != (
        parent_contract.get("continuation", {}).get("generation", -1) + 1
    ):
        errors.append("child generation does not follow the parent disk contract")
    if kind == "repair" and repair is not None:
        parent_plan_path = parent / "continuation" / "repair-plan.json"
        parent_plan = _read(parent_plan_path, errors, "parent repair plan")
        if isinstance(parent_plan, dict):
            expected_plan_sha256 = sha256_file(parent_plan_path)
            if (
                repair.get("parent_repair_plan_sha256") != expected_plan_sha256
                or binding.get("parent_repair_plan_sha256")
                != expected_plan_sha256
            ):
                errors.append("parent repair plan differs from child repair binding")
            if (
                repair.get("parent_repair_reset_phases")
                != parent_plan.get("reset_phases")
                or binding.get("parent_repair_reset_phases")
                != parent_plan.get("reset_phases")
            ):
                errors.append("parent repair reset phases differ from child repair binding")
            expected_phase = parent_plan.get("earliest_invalid_phase")
            observed_phase = repair.get("earliest_invalid_phase")
            if (
                observed_phase != expected_phase
                or binding.get("base_phase") != expected_phase
            ):
                errors.append(
                    f"repair earliest invalid phase {observed_phase} differs from "
                    f"parent disk plan {expected_phase}"
                )
            parent_report = validate_run(
                parent,
                repository_root=repository_root,
                require_complete=False,
                validation_boundary="final",
                _lineage_ancestors=lineage_ancestors,
            )
            derived_phase, derived_reset = derive_repair_scope(
                parent_report.get("errors", [])
            )
            if (
                parent_plan.get("earliest_invalid_phase") != derived_phase
                or parent_plan.get("reset_phases") != derived_reset
            ):
                errors.append(
                    "parent repair plan differs from the parent disk failure scope"
                )
    try:
        parent_records = load_phase_records(parent)
    except Exception as exc:
        errors.append(f"cannot read parent phase chain: {exc}")
        return
    errors.extend(_structural_chain_errors(parent_records))
    if kind == "fork":
        _, parent_chain_errors = validate_phase_chain(parent)
        errors.extend(
            f"parent run validation: {error}" for error in parent_chain_errors
        )
    matching = [
        record for record in parent_records if record.get("record_sha256") == parent_chain_head
    ]
    if len(matching) != 1:
        errors.append("parent chain binding does not resolve on parent disk")
        return
    if kind == "fork" and binding.get("base_phase") != matching[0].get("phase"):
        errors.append("fork base phase differs from the bound parent phase")
    manifest_path = parent / "artifacts" / "artifact-manifest.json"
    if manifest_path.is_file():
        manifest = _read(manifest_path, errors, "parent artifact manifest")
        if isinstance(manifest, dict):
            if len(parent_records) < len(PHASES):
                errors.append("parent manifest exists before the parent XK12 phase")
            else:
                manifest_bindings = {
                    item.get("path"): item.get("sha256")
                    for item in parent_records[12].get("artifact_bindings", [])
                    if isinstance(item, dict)
                }
                if manifest_bindings.get("artifacts/artifact-manifest.json") != sha256_file(
                    manifest_path
                ):
                    errors.append("parent manifest bytes differ from the parent chain")
            if manifest.get("run_id") != parent_run_id:
                errors.append("parent manifest has a different run_id")
            if manifest.get("validator_set_sha256") != contract.get(
                "validator_set_sha256"
            ):
                errors.append("parent manifest authority differs from the child run")
            if len(parent_records) >= 12 and manifest.get(
                "validated_chain_head_sha256"
            ) != parent_records[11].get("record_sha256"):
                errors.append("parent manifest chain binding differs from parent disk")


def _phase_values(run_dir: Path, records: list[dict[str, Any]], phase: str, errors: list[str]) -> list[Any]:
    index = PHASES.index(phase)
    if len(records) <= index:
        return []
    values: list[Any] = []
    for binding in records[index].get("artifact_bindings", []):
        try:
            path = confined_path(run_dir, binding["path"], must_exist=True)
            if path.suffix == ".jsonl":
                values.append(
                    [
                        read_json_text(line)
                        for line in path.read_text(encoding="utf-8").splitlines()
                        if line.strip()
                    ]
                )
            elif path.suffix in {".bin", ".txt"}:
                values.append(path.read_bytes())
            else:
                values.append(read_json(path))
        except Exception as exc:
            errors.append(f"cannot read {phase} artifact: {exc}")
    return values


def _load_packet(run_dir: Path, errors: list[str]) -> dict[str, Any] | None:
    path = run_dir / "continuation" / "input-packet.json"
    if not path.is_file():
        errors.append("missing disk-reloaded input packet")
        return None
    value = _read(path, errors, "input packet")
    return value if isinstance(value, dict) else None


def _validate_bound_run_ids(
    run_dir: Path,
    records: list[dict[str, Any]],
    contract_run_id: Any,
    errors: list[str],
) -> None:
    for record in records:
        for binding in record.get("artifact_bindings", []):
            relative = binding.get("path")
            try:
                path = confined_path(run_dir, relative, must_exist=True)
                if path.suffix == ".jsonl":
                    values = [
                        read_json_text(line)
                        for line in path.read_text(encoding="utf-8").splitlines()
                        if line.strip()
                    ]
                elif path.suffix == ".json":
                    values = [read_json(path)]
                else:
                    continue
            except Exception as exc:
                errors.append(f"cannot inspect artifact run_id {relative}: {exc}")
                continue
            for value in values:
                if (
                    isinstance(value, dict)
                    and "run_id" in value
                    and value.get("run_id") != contract_run_id
                ):
                    errors.append(f"artifact run_id differs from run contract: {relative}")


def _validate_phase_artifact_bindings(
    records: list[dict[str, Any]],
    errors: list[str],
    *,
    contract_profile: str,
    mode: str,
) -> None:
    for record in records:
        phase = record.get("phase")
        if not isinstance(phase, str) or phase not in PHASES:
            continue
        bindings = record.get("artifact_bindings")
        if not isinstance(bindings, list):
            continue
        actual_paths = [
            binding.get("path") if isinstance(binding, dict) else None
            for binding in bindings
        ]
        expected_paths = list(
            expected_phase_artifact_paths(
                phase, contract_profile=contract_profile, mode=mode
            )
        )
        if phase == "XK8":
            recursive_paths = actual_paths[len(expected_paths) :]
            all_paths_are_strings = all(
                isinstance(path, str) for path in actual_paths
            )
            valid = (
                actual_paths[: len(expected_paths)] == expected_paths
                and all_paths_are_strings
                and len(actual_paths) == len(set(actual_paths))
                and all(
                    path.startswith("authoring/recursive-state/")
                    and path.endswith(".json")
                    for path in recursive_paths
                )
                and recursive_paths == sorted(recursive_paths)
            )
        else:
            valid = actual_paths == expected_paths
        if not valid:
            errors.append(
                f"{phase} artifact binding paths differ from the runtime contract"
            )


def _validate_candidate_closure(run_dir: Path, repository_root: Path, value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("XK4 concept disposition is not an object")
        return
    try:
        census_rows, authority = load_concept_authority(repository_root)
    except ValueError as exc:
        errors.append(f"candidate authority is invalid: {exc}")
        return
    rows = value.get("dispositions")
    if (
        value.get("schema_id") != "xi-kari.v2.concept-disposition"
        or value.get("schema_version") != 3
        or value.get("complete") is not True
    ):
        errors.append("XK4 concept disposition contract is invalid")
    if (
        value.get("source_candidate_index_sha256")
        != authority["source_candidate_index_sha256"]
    ):
        errors.append("XK4 source candidate index hash mismatch")
    if value.get("candidate_census_sha256") != authority["candidate_census_sha256"]:
        errors.append("XK4 candidate census hash mismatch")
    if (
        value.get("concept_disposition_ledger_sha256")
        != authority["concept_disposition_ledger_sha256"]
    ):
        errors.append("XK4 concept disposition ledger hash mismatch")
    if (
        value.get("source_candidate_count") != authority["source_candidate_count"]
        or not isinstance(rows, list)
        or len(rows) != authority["source_candidate_count"]
    ):
        errors.append("XK4 candidate disposition order/count mismatch")
    if isinstance(rows, list) and any(row.get("disposition") == "unresolved" for row in rows):
        errors.append("XK4 contains unresolved candidate disposition")
    if rows != census_rows:
        errors.append("XK4 differs from the reviewed candidate census")


def _validate_concept_closure_report(
    repository_root: Path,
    concept: Any,
    report: Any,
    errors: list[str],
    *,
    run_id: str,
    contract_profile: str,
    problem_contract_sha256: str,
    ontology_read_plan: Any = None,
    ontology_read_trace: Any = None,
) -> None:
    if not isinstance(concept, dict) or not isinstance(report, dict):
        errors.append("XK4 concept closure report is missing or incomplete")
        return
    ontology = repository_root / "references" / "ontology"
    registry_path = ontology / "concept-registry.json"
    relations_path = ontology / "concept-relations.json"
    continuity_path = ontology / "continuity-map.md"
    if not all(path.is_file() for path in (registry_path, relations_path, continuity_path)):
        errors.append("XK4 ontology authority is unavailable")
        return
    registry = read_json(registry_path)
    relations = read_json(relations_path)
    if not isinstance(registry, dict) or not isinstance(relations, dict):
        errors.append("XK4 ontology authority is invalid")
        return

    if report.get("candidate_census_sha256") != concept.get("candidate_census_sha256"):
        errors.append("XK4 closure candidate census hash mismatch")
    if report.get("source_candidate_count") != concept.get("source_candidate_count"):
        errors.append("XK4 closure source candidate count mismatch")
    disposition_counts: dict[str, int] = {}
    for row in concept.get("dispositions", []):
        if isinstance(row, dict):
            disposition = str(row.get("disposition"))
            disposition_counts[disposition] = disposition_counts.get(disposition, 0) + 1
    if report.get("disposition_counts") != disposition_counts:
        errors.append("XK4 closure disposition counts mismatch")
    if report.get("unresolved_count") != disposition_counts.get("unresolved", 0):
        errors.append("XK4 closure unresolved count mismatch")

    if report.get("concept_registry_sha256") != sha256_file(registry_path):
        errors.append("XK4 concept registry hash mismatch")
    if report.get("concept_relations_sha256") != sha256_file(relations_path):
        errors.append("XK4 concept relations hash mismatch")
    if report.get("continuity_map_sha256") != sha256_file(continuity_path):
        errors.append("XK4 continuity map hash mismatch")
    if report.get("concept_count") != registry.get("concept_count"):
        errors.append("XK4 concept count mismatch")
    if report.get("concept_count_semantics") != (
        "inventory record count; not a complete ontology concept count"
    ):
        errors.append("XK4 concept count semantics mismatch")

    relation_ids = set(relations)
    relation_edge_count = 0
    dangling_neighbor_count = 0
    semantic_without_neighbors_count = 0
    for concept_id, value in relations.items():
        if not isinstance(value, dict) or not isinstance(value.get("required_neighbors"), list):
            errors.append(f"XK4 invalid relation record: {concept_id}")
            continue
        neighbors = value["required_neighbors"]
        relation_edge_count += len(neighbors)
        dangling_neighbor_count += sum(
            not isinstance(neighbor, str) or neighbor not in relation_ids
            for neighbor in neighbors
        )
        if (
            value.get("disposition") in {"canonical_concept", "structural_rule"}
            and not neighbors
        ):
            semantic_without_neighbors_count += 1
    if report.get("relation_edge_count") != relation_edge_count:
        errors.append("XK4 relation edge count mismatch")
    if report.get("dangling_neighbor_count") != dangling_neighbor_count:
        errors.append("XK4 dangling neighbor count mismatch")
    if report.get("semantic_without_neighbors_count") != semantic_without_neighbors_count:
        errors.append("XK4 semantic neighbor closure mismatch")

    expected_bundle_bindings = []
    for path in sorted((ontology / "bundles").glob("*.md")):
        try:
            expected_bundle_bindings.append(
                build_continuity_bundle_binding(repository_root, path)
            )
        except ValueError as exc:
            errors.append(f"XK4 {exc}")
    if report.get("bundle_count") != len(expected_bundle_bindings):
        errors.append("XK4 bundle count mismatch")
    if report.get("bundle_bindings") != expected_bundle_bindings:
        errors.append("XK4 bundle bindings mismatch")
    ontology_read_complete = contract_profile != PRODUCTION_CONTRACT_PROFILE
    if contract_profile == PRODUCTION_CONTRACT_PROFILE:
        if not isinstance(ontology_read_plan, dict) or not isinstance(
            ontology_read_trace, dict
        ):
            errors.append("XK4 production ontology read plan/trace is missing")
        else:
            trace_errors = validate_ontology_read_trace(
                ontology_read_trace,
                plan=ontology_read_plan,
                expected_run_id=run_id,
                expected_problem_contract_sha256=problem_contract_sha256,
                repository_root=repository_root,
            )
            errors.extend(f"XK4 {error}" for error in trace_errors)
            ontology_read_complete = not trace_errors
            if report.get("ontology_read_plan_sha256") != sha256_json(
                ontology_read_plan
            ):
                errors.append("XK4 ontology read plan hash mismatch")
            if report.get("ontology_read_trace_sha256") != sha256_json(
                ontology_read_trace
            ):
                errors.append("XK4 ontology read trace hash mismatch")
            if report.get("ontology_read_record_count") != ontology_read_trace.get(
                "record_count"
            ):
                errors.append("XK4 ontology read record count mismatch")
            if report.get("ontology_read_complete") is not True:
                errors.append("XK4 ontology read completion is false")
    elif any(
        field in report
        for field in (
            "ontology_read_plan_sha256",
            "ontology_read_trace_sha256",
            "ontology_read_record_count",
            "ontology_read_complete",
        )
    ):
        errors.append("legacy XK4 cannot claim a production ontology read trace")
    if (
        report.get("complete") is not True
        or disposition_counts.get("unresolved", 0) != 0
        or dangling_neighbor_count != 0
        or semantic_without_neighbors_count != 0
        or not expected_bundle_bindings
        or not all(binding["source_anchors"] for binding in expected_bundle_bindings)
        or not ontology_read_complete
    ):
        errors.append("XK4 concept closure report is missing or incomplete")


def _validate_semantics(
    packet: dict[str, Any],
    repository_root: Path,
    run_contract: dict[str, Any],
    errors: list[str],
) -> None:
    try:
        require_packet_contract(
            packet,
            mode=run_contract.get("mode", "open-world"),
            run_contract=run_contract,
        )
    except Exception as exc:
        errors.append(f"packet contract: {exc}")
        return
    if packet.get("dynamic_applicability") == "not_applicable":
        return
    try:
        world = packet["local_world_model"]
        if packet.get("cascade") is not None:
            validate_cascade(
                packet["cascade"], world, repository_root=repository_root
            )
        chain = validate_semantic_chain(
            world_volume=world,
            transformation_ledger=packet["transformation_ledger"],
            claim_mechanism_graph=packet["claim_mechanism_graph"],
            recursive_lineage=packet["recursive_lineage"],
            recursive_states=packet["recursive_states"],
            evidence_mode=str(run_contract.get("mode", "open-world")),
            repository_root=repository_root,
        )
        graph = chain.graph
        recursive_validation = chain.recursive
        validate_verdict_bundle(
            packet["verdict"],
            claim_mechanism_graph=graph,
            recursive_validation=recursive_validation,
            recursive_states=packet["recursive_states"],
            evidence_mode=str(run_contract.get("mode", "open-world")),
            repository_root=repository_root,
        )
        validate_action_ranking(
            packet["action_ranking"],
            verdict_bundle=packet["verdict"],
            repository_root=repository_root,
        )
        validate_framework_gap_isolation(
            (
                packet["framework_gap"]
                if packet.get("framework_gap") is not None
                else empty_framework_gap_ledger()
            ),
            claim_mechanism_graph=graph,
            verdict_bundle=packet["verdict"],
            action_ranking=packet["action_ranking"],
            recursive_validation=recursive_validation,
            recursive_states=packet["recursive_states"],
            evidence_mode=str(run_contract.get("mode", "open-world")),
            repository_root=repository_root,
        )
    except Exception as exc:
        errors.append(f"semantic validation: {exc}")


def _runtime_document_projection(
    value: dict[str, Any], *, kind: str, run_id: str
) -> dict[str, Any]:
    document = dict(value)
    document["schema_id"] = f"xi-kari.v2.{kind}"
    document["schema_version"] = 3
    document["run_id"] = run_id
    return document


def _reader_payload_projection(
    packet: dict[str, Any], run_contract: dict[str, Any]
) -> dict[str, Any]:
    payload = dict(packet)
    if packet.get("dynamic_applicability") == "not_applicable":
        for field in DYNAMIC_PHASE_FIELDS:
            payload.pop(field, None)
    payload["question"] = run_contract.get("question")
    retrieval = packet.get("retrieval")
    if not isinstance(retrieval, dict):
        retrieval = {}
    payload["sources"] = list(retrieval.get("sources", []))
    payload["assessments"] = list(retrieval.get("assessments", []))
    return payload


def _scan_delivery_for_protected_retrieval_values(
    run_dir: Path,
    packet: Mapping[str, Any],
    delivery_paths: tuple[str, ...],
    errors: list[str],
) -> None:
    protected = protected_retrieval_values(packet)
    if not protected:
        return
    expected_paths = {run_dir / relative for relative in delivery_paths}
    delivery_root = run_dir / "delivery"
    actual_paths = (
        {
            path
            for path in delivery_root.rglob("*")
            if path.is_file() and not path.is_symlink()
        }
        if delivery_root.is_dir()
        else set()
    )
    actual_paths.update(
        candidate
        for candidate in expected_paths
        if candidate.is_file() and not candidate.is_symlink()
    )
    for path in sorted(actual_paths):
        try:
            relative = path.relative_to(run_dir).as_posix()
        except ValueError:
            relative = str(path)
        try:
            delivery_bytes = path.read_bytes()
        except OSError as exc:
            errors.append(f"cannot scan delivery privacy boundary {relative}: {exc}")
            continue
        for source_path, value in protected.items():
            escaped = json.dumps(value, ensure_ascii=True)[1:-1].encode("ascii")
            if value.encode("utf-8") in delivery_bytes or escaped in delivery_bytes:
                errors.append(
                    "protected retrieval value appears in delivery bytes: "
                    f"{source_path} -> {relative}"
                )


def _not_applicable_projection(packet: dict[str, Any], *, run_id: str) -> dict[str, Any]:
    document: dict[str, Any] = {
        "schema_id": "xi-kari.v2.not-applicable",
        "schema_version": 3,
        "run_id": run_id,
        "dynamic_applicability": "not_applicable",
        "status": "not_run",
    }
    reason = packet.get("not_applicable_reason")
    if isinstance(reason, str) and reason.strip():
        document["reason"] = reason.strip()
    return document


def _validate_semantic_artifact_projection(
    run_dir: Path,
    records: list[dict[str, Any]],
    packet: dict[str, Any],
    *,
    run_id: str,
    evidence_cutoff: Any,
    retrieval_index: dict[str, Any] | None,
    evidence_ledger: dict[str, Any] | None,
    repository_root: Path,
    errors: list[str],
) -> None:
    applicability = packet.get("dynamic_applicability")
    not_applicable = _not_applicable_projection(packet, run_id=run_id)
    static_phase = {
        "dynamic_applicability": "not_applicable",
        "status": "not_run",
    }
    expected_world: Any = packet.get("local_world_model")
    if applicability == "applicable" and evidence_ledger is not None:
        try:
            expected_world = bind_world_evidence_state(
                packet["local_world_model"],
                evidence_ledger=evidence_ledger,
                run_id=run_id,
                repository_root=repository_root,
            )
        except Exception as exc:
            errors.append(f"XK5 evidence-state projection: {exc}")
            expected_world = None
    expected: dict[str, list[tuple[str, Any]]] = {
        "XK5": [
            (
                "local-world-model",
                expected_world
                if applicability == "applicable"
                else not_applicable,
            )
        ],
        "XK6": [
            (
                "transformation-ledger",
                packet["transformation_ledger"]
                if applicability == "applicable"
                else not_applicable,
            ),
            (
                "cascade",
                packet["cascade"]
                if applicability == "applicable"
                else not_applicable,
            ),
        ],
        "XK7": [
            (
                "claim-mechanism-graph",
                packet["claim_mechanism_graph"]
                if applicability == "applicable"
                else not_applicable,
            ),
            (
                "case-ledger",
                _runtime_document_projection(
                    packet["case_ledger"], kind="case-ledger", run_id=run_id
                ),
            ),
        ],
        "XK8": [
            (
                "recursive-lineage",
                packet["recursive_lineage"]
                if applicability == "applicable"
                else not_applicable,
            )
        ],
        "XK9": [
            (
                "semantic-authoring-bundle",
                _not_applicable_projection(packet, run_id=run_id)
                if applicability != "applicable"
                else None,
            ),
            (
                "order-evaluation",
                _runtime_document_projection(
                    (
                        packet["order_evaluation"]
                        if applicability == "applicable"
                        else static_phase
                    ),
                    kind="order-evaluation",
                    run_id=run_id,
                ),
            ),
            (
                "red-team",
                _runtime_document_projection(
                    (
                        packet["red_team"]
                        if applicability == "applicable"
                        else static_phase
                    ),
                    kind="red-team-report",
                    run_id=run_id,
                ),
            ),
            (
                "stance-pair",
                _runtime_document_projection(
                    (
                        packet["stance_pair"]
                        if applicability == "applicable"
                        else static_phase
                    ),
                    kind="stance-pair",
                    run_id=run_id,
                ),
            ),
            (
                "sensitivity-report",
                _not_applicable_projection(packet, run_id=run_id)
                if applicability != "applicable"
                else None,
            ),
            (
                "stance-stability-report",
                _not_applicable_projection(packet, run_id=run_id)
                if applicability != "applicable"
                else None,
            ),
        ],
        "XK10": [
            (
                "verdict",
                packet["verdict"] if applicability == "applicable" else not_applicable,
            ),
            (
                "action-ranking",
                packet["action_ranking"]
                if applicability == "applicable"
                else not_applicable,
            ),
            (
                "forecast",
                _runtime_document_projection(
                    (
                        packet["forecast"]
                        if applicability == "applicable"
                        else static_phase
                    ),
                    kind="forecast-ledger",
                    run_id=run_id,
                ),
            ),
            (
                "framework-gap-ledger",
                (
                    packet["framework_gap"]
                    if packet.get("framework_gap") is not None
                    else empty_framework_gap_ledger()
                )
                if applicability == "applicable"
                else not_applicable,
            ),
        ],
    }
    if retrieval_index is not None:
        expected_evidence = packet["evidence"]
        if (
            isinstance(expected_evidence, dict)
            and "claims" in expected_evidence
            and "support_edges" not in expected_evidence
        ):
            expected_evidence = build_evidence_ledger(
                run_id=run_id,
                claims=[
                    {
                        **dict(claim),
                        **(
                            {"world_targets": []}
                            if packet.get("dynamic_applicability") != "applicable"
                            else {}
                        ),
                    }
                    for claim in expected_evidence["claims"]
                ],
                retrieval_index=retrieval_index,
                world_target_hashes=(
                    world_evidence_target_hashes(packet["local_world_model"])
                    if packet.get("dynamic_applicability") == "applicable"
                    else None
                ),
            )
        expected["XK3"] = [
            ("evidence-ledger", expected_evidence),
            (
                "unknown-register",
                {
                    "schema_id": "xi-kari.v2.unknown-register",
                    "schema_version": 3,
                    "run_id": run_id,
                    "evidence_cutoff": evidence_cutoff,
                    "unknowns": list(packet.get("facts", {}).get("unknown", [])),
                    "unsupported_claim_ids": list(
                        expected_evidence.get("unsupported_claims", [])
                    ),
                    "frozen": True,
                },
            ),
        ]
    for phase, expected_values in expected.items():
        if len(records) <= PHASES.index(phase):
            continue
        actual_values = _phase_values(run_dir, records, phase, errors)
        for index, (label, expected_value) in enumerate(expected_values):
            if expected_value is None:
                continue
            if len(actual_values) <= index or actual_values[index] != expected_value:
                suffix = (
                    "disk packet projection" if phase == "XK3" else "disk packet"
                )
                errors.append(f"{phase} {label} artifact differs from the {suffix}")


def validate_run(
    run_dir: Path,
    *,
    repository_root: Path | None = None,
    require_complete: bool = True,
    check_manifest: bool = True,
    validation_boundary: str = "final",
    fresh_process: bool = False,
    _lineage_ancestors: frozenset[Path] | None = None,
) -> dict[str, Any]:
    if validation_boundary not in {"preseal", "promotion", "official", "final"}:
        raise ValueError(f"unsupported validation boundary: {validation_boundary}")
    run_dir = Path(run_dir).expanduser()
    errors: list[str] = []
    supplied_repository_root = None
    if repository_root is not None:
        try:
            supplied_repository_root = resolve_repository_root(repository_root)
        except Exception as exc:
            errors.append(f"supplied repository root is invalid: {exc}")
    report_root = supplied_repository_root or DEFAULT_REPOSITORY_ROOT
    linked_component = _run_path_symlink(run_dir)
    if linked_component is not None:
        errors.append(
            f"run directory path contains a symlink: {linked_component}"
        )
        return _report(
            None,
            [],
            errors,
            repository_root=report_root,
            validation_boundary=validation_boundary,
            fresh_process=fresh_process,
        )
    run_dir = run_dir.resolve()
    lineage_ancestors = frozenset(_lineage_ancestors or ()) | {run_dir}
    symlinks = _run_symlinks(run_dir)
    if symlinks:
        errors.extend(f"run path contains a symlink: {path}" for path in symlinks)
        return _report(
            None,
            [],
            errors,
            repository_root=report_root,
            validation_boundary=validation_boundary,
            fresh_process=fresh_process,
        )
    contract = _read(run_dir / "run-contract.json", errors, "run-contract.json")
    if not isinstance(contract, dict):
        return _report(
            None,
            [],
            errors,
            repository_root=report_root,
            validation_boundary=validation_boundary,
            fresh_process=fresh_process,
        )
    bound_root_value = contract.get("repository_root")
    if not isinstance(bound_root_value, str) or not bound_root_value:
        errors.append("run contract has no repository root authority")
        repository_root = report_root.resolve()
    else:
        try:
            repository_root = resolve_repository_root(Path(bound_root_value))
        except Exception as exc:
            errors.append(f"bound repository root is invalid: {exc}")
            repository_root = report_root.resolve()
        if (
            supplied_repository_root is not None
            and supplied_repository_root != repository_root
        ):
            errors.append("supplied repository root differs from the run contract")
    for forbidden_root in {
        Path(repository_root).resolve(),
        DEFAULT_REPOSITORY_ROOT.resolve(),
    }:
        try:
            run_dir.relative_to(forbidden_root)
        except ValueError:
            continue
        errors.append("run directory is inside the repository or Skill installation")
        break
    records, chain_errors = validate_phase_chain(run_dir)
    errors.extend(chain_errors)
    try:
        observed_validator_set = compute_validator_set_sha256(repository_root)
    except Exception as exc:
        errors.append(f"cannot load repository authority: {exc}")
        observed_validator_set = None
    if contract.get("validator_set_sha256") != observed_validator_set:
        errors.append("repository authority differs from the run contract")
    errors.extend(validate_repair_packet_binding(run_dir, contract))
    _validate_path_owned_json(run_dir, repository_root, errors)
    _validate_parent_lineage(
        run_dir,
        contract,
        repository_root,
        errors,
        lineage_ancestors=lineage_ancestors,
    )
    chain_head = records[-1].get("record_sha256") if records else None
    terminal_state, terminal_errors = validate_terminal_closure(
        run_dir,
        contract,
        phase_count=len(records),
        chain_head_sha256=chain_head,
        required=(validation_boundary == "final" and len(records) == len(PHASES)),
    )
    if terminal_errors:
        errors.extend(terminal_errors)
    errors.extend(
        validate_runtime_control_bindings(
            run_dir,
            contract,
            verify_external_bindings=terminal_state != "complete",
        )
    )
    lifecycle_errors = validate_lifecycle_sidecars(
        run_dir, contract, phase_count=len(records)
    )
    if terminal_state is not None:
        lifecycle_errors = [
            error
            for error in lifecycle_errors
            if error
            not in {
                "cancel record and continuation state disagree",
                COMPLETE_STATE_MISMATCH_ERROR,
                PREMATURE_COMPLETE_STATE_ERROR,
            }
        ]
    if validation_boundary in {"promotion", "official"}:
        lifecycle_errors = [
            error
            for error in lifecycle_errors
            if error != COMPLETE_STATE_MISMATCH_ERROR
        ]
        try:
            continuation_state = read_json(
                run_dir / "continuation" / "state.json"
            )
        except Exception as exc:
            errors.append(f"cannot read promotion continuation state: {exc}")
        else:
            if (
                not isinstance(continuation_state, dict)
                or continuation_state.get("state")
                not in {"in_progress", "needs_attention"}
                or continuation_state.get("next_phase") != "XK12"
            ):
                errors.append(
                    f"{validation_boundary} validation requires an uncommitted XK12 continuation state"
                )
    errors.extend(lifecycle_errors)
    _validate_phase_artifact_bindings(
        records,
        errors,
        contract_profile=str(contract.get("contract_profile", "")),
        mode=str(contract.get("mode", "")),
    )
    contract_run_id = contract.get("run_id")
    if any(record.get("run_id") != contract_run_id for record in records):
        errors.append("phase chain run_id differs from run contract")
    _validate_bound_run_ids(run_dir, records, contract_run_id, errors)
    if require_complete and len(records) != len(PHASES):
        errors.append(f"run is incomplete: {len(records)}/13 phases")
    if len(records) < len(PHASES):
        for relative in expected_phase_artifact_paths("XK12"):
            if (run_dir / relative).exists():
                errors.append(
                    "premature XK12 declaration without an XK12 phase: "
                    f"{relative}"
                )
    if records and records[0].get("phase") != "XK0":
        errors.append("chain does not begin at XK0")
    source_lock_document: dict[str, Any] | None = None
    evidence_ledger_document: dict[str, Any] | None = None
    concept_closure_document: dict[str, Any] | None = None
    source_lock_values = _phase_values(run_dir, records, "XK1", errors)
    if source_lock_values:
        lock = source_lock_values[0]
        if isinstance(lock, dict):
            source_lock_document = lock
        event_path = run_dir / "authoring" / "XK01-read-events.jsonl"
        events = []
        if event_path.is_file():
            import json

            events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        errors.extend(validate_full_source_lock(lock, events, repository_root))
        if contract.get("contract_profile") == PRODUCTION_CONTRACT_PROFILE:
            if len(source_lock_values) < 9:
                errors.append("XK1 production semantic read trace is missing")
            elif records:
                errors.extend(
                    validate_semantic_read_trace(
                        source_lock_values[3],
                        repository_root=repository_root,
                        run_contract=contract,
                        source_lock=lock,
                        source_events=events,
                        xk0_record_sha256=str(
                            records[0].get("record_sha256", "")
                        ),
                    )
                )
    retrieval_index: dict[str, Any] | None = None
    if len(records) > 2:
        retrieval_artifact = _phase_values(run_dir, records, "XK2", errors)
        if retrieval_artifact:
            # The materializer writes a separate retrieval index under the run.
            index = _read(run_dir / "retrieval" / "index.json", errors, "retrieval index")
            if isinstance(index, dict):
                retrieval_index = index
                errors.extend(
                    validate_retrieval_bundle(
                        run_dir,
                        index,
                        mode=contract.get("mode", "open-world"),
                        evidence_cutoff=contract.get("evidence_cutoff"),
                    )
                )
    if (
        contract.get("contract_profile") == PRODUCTION_CONTRACT_PROFILE
        and len(records) == 2
    ):
        try:
            from .materialization import _validate_base_authoring_and_retrieval

            prepared_packet = _read(
                run_dir / "continuation/input-packet.json",
                errors,
                "prepared production input packet",
            )
            if isinstance(prepared_packet, Mapping):
                _validate_base_authoring_and_retrieval(
                    run_dir,
                    contract=contract,
                    retrieval=prepared_packet.get("retrieval", {}),
                    packet=prepared_packet,
                )
        except Exception as exc:
            errors.append(f"production base/retrieval execution: {exc}")
    _validate_wildcard_artifact_index(
        run_dir, records, retrieval_index, errors
    )
    if len(records) > 3:
        evidence_values = _phase_values(run_dir, records, "XK3", errors)
        if evidence_values and retrieval_index is not None:
            if isinstance(evidence_values[0], dict):
                evidence_ledger_document = evidence_values[0]
            from .evidence import validate_evidence_ledger

            errors.extend(validate_evidence_ledger(evidence_values[0], retrieval_index))
            if len(evidence_values) < 2 or evidence_values[1].get("frozen") is not True:
                errors.append("XK3 unknown register is missing or not frozen")
    if len(records) > 4:
        concept_values = _phase_values(run_dir, records, "XK4", errors)
        if concept_values:
            _validate_candidate_closure(run_dir, repository_root, concept_values[0], errors)
            if len(concept_values) < 2:
                errors.append("XK4 concept closure report is missing or incomplete")
            else:
                if isinstance(concept_values[1], dict):
                    concept_closure_document = concept_values[1]
                _validate_concept_closure_report(
                    repository_root,
                    concept_values[0],
                    concept_values[1],
                    errors,
                    run_id=str(contract_run_id),
                    contract_profile=str(contract.get("contract_profile", "")),
                    problem_contract_sha256=contract_hash(
                        contract["problem_contract"]
                    ),
                    ontology_read_plan=(
                        concept_values[2] if len(concept_values) > 2 else None
                    ),
                    ontology_read_trace=(
                        concept_values[3] if len(concept_values) > 3 else None
                    ),
                )
    packet = _load_packet(run_dir, errors) if len(records) > 2 else None
    if packet is not None:
        packet_sha256 = sha256_file(run_dir / "continuation" / "input-packet.json")
        retrieval_values = _phase_values(run_dir, records, "XK2", errors)
        if retrieval_values and retrieval_values[0].get("input_packet_sha256") != packet_sha256:
            errors.append("input packet hash differs from sealed XK2")
        packet = dict(packet)
        packet["mode"] = contract.get("mode")
        if contract.get("contract_profile") == PRODUCTION_CONTRACT_PROFILE:
            try:
                from .materialization import _validate_base_authoring_and_retrieval

                _validate_base_authoring_and_retrieval(
                    run_dir,
                    contract=contract,
                    retrieval=packet.get("retrieval", {}),
                    packet=packet,
                )
            except Exception as exc:
                errors.append(f"production base/retrieval execution: {exc}")
        semantic_packet = dict(packet)
        if (
            packet.get("dynamic_applicability") == "applicable"
            and len(records) > PHASES.index("XK5")
        ):
            world_values = _phase_values(run_dir, records, "XK5", errors)
            if world_values and isinstance(world_values[0], dict):
                semantic_packet["local_world_model"] = world_values[0]
                if evidence_ledger_document is None:
                    errors.append("XK5 cannot bind evidence without frozen XK3")
                else:
                    try:
                        validate_world_volume(
                            world_values[0],
                            repository_root=repository_root,
                            evidence_ledger=evidence_ledger_document,
                            expected_run_id=str(contract_run_id),
                        )
                    except Exception as exc:
                        errors.append(f"XK5 evidence-state binding: {exc}")
        _validate_semantics(semantic_packet, repository_root, contract, errors)
        _validate_semantic_artifact_projection(
            run_dir,
            records,
            packet,
            run_id=str(contract_run_id),
            evidence_cutoff=contract.get("evidence_cutoff"),
            retrieval_index=retrieval_index,
            evidence_ledger=evidence_ledger_document,
            repository_root=repository_root,
            errors=errors,
        )
        if len(records) > PHASES.index("XK9"):
            xk9_values = _phase_values(run_dir, records, "XK9", errors)
            if len(xk9_values) >= 6:
                if packet.get("dynamic_applicability") == "applicable":
                    try:
                        validate_semantic_probe_authorings(
                            xk9_values[0],
                            packet,
                            contract,
                            source_lock=read_json(run_dir / "source-lock.json"),
                            read_plan=read_json(
                                run_dir / "authoring/XK01-read-plan.json"
                            ),
                            input_packet_sha256=packet_sha256,
                            verify_executable=False,
                        )
                    except Exception as exc:
                        errors.append(f"XK9 semantic authoring bundle: {exc}")
                    errors.extend(
                        validate_sensitivity_report(
                            xk9_values[4],
                            packet_path=run_dir / "continuation/input-packet.json",
                            authoring_bundle_path=run_dir
                            / "authoring/XK09-semantic-authoring-bundle.json",
                            run_contract_path=run_dir / "run-contract.json",
                            source_lock_path=run_dir / "source-lock.json",
                            read_plan_path=run_dir
                            / "authoring/XK01-read-plan.json",
                            repository_root=repository_root,
                            baseline_projection_sha256=xk9_values[5].get(
                                "invariant_projection_sha256", ""
                            ),
                        )
                    )
                    errors.extend(
                        validate_stance_stability_report(
                            xk9_values[5],
                            packet_path=run_dir / "continuation/input-packet.json",
                            authoring_bundle_path=run_dir
                            / "authoring/XK09-semantic-authoring-bundle.json",
                            run_contract_path=run_dir / "run-contract.json",
                            source_lock_path=run_dir / "source-lock.json",
                            read_plan_path=run_dir
                            / "authoring/XK01-read-plan.json",
                            repository_root=repository_root,
                        )
                    )
                else:
                    for index, value in (
                        (0, xk9_values[0]),
                        (4, xk9_values[4]),
                        (5, xk9_values[5]),
                    ):
                        if not isinstance(value, Mapping) or value.get(
                            "schema_id"
                        ) != "xi-kari.v2.not-applicable":
                            errors.append(
                                f"XK9 auxiliary artifact {index} is not marked not-applicable"
                            )
        if len(records) > 3:
            evidence_values = _phase_values(run_dir, records, "XK3", errors)
            if len(evidence_values) >= 2 and evidence_values[1].get("unknowns") != packet.get("facts", {}).get("unknown", []):
                errors.append("XK3 unknown register differs from the disk packet")
            if evidence_values and retrieval_index is not None:
                try:
                    validate_packet_references(
                        packet,
                        evidence_ledger=evidence_values[0],
                        retrieval_index=retrieval_index,
                        repository_root=repository_root,
                    )
                except ValueError as exc:
                    errors.append(f"packet reference validation: {exc}")
        if len(records) > 8:
            recursive_values = _phase_values(run_dir, records, "XK8", errors)
            expected_states = packet.get("recursive_states", {})
            state_records = [
                value
                for value in recursive_values[1:]
                if isinstance(value, dict)
            ]
            actual_state_ids = [value.get("state_id") for value in state_records]
            actual_states = {
                value.get("state_id"): value
                for value in state_records
                if isinstance(value, dict) and value.get("state_id")
            }
            state_ids_are_text = all(
                isinstance(state_id, str) and state_id
                for state_id in actual_state_ids
            )
            one_to_one = (
                isinstance(expected_states, dict)
                and state_ids_are_text
                and len(state_records) == len(expected_states)
                and len(actual_state_ids) == len(set(actual_state_ids))
                and set(actual_state_ids) == set(expected_states)
            )
            if not one_to_one:
                errors.append(
                    "XK8 recursive-state artifacts are not one-to-one with "
                    "disk packet states"
                )
            elif actual_states != expected_states:
                errors.append("XK8 recursive-state artifacts differ from the disk packet")
    if len(records) > 10:
        # Every public delivery file is reread and hash checked.
        delivery_paths = (
            provisional_delivery_paths()
            if validation_boundary == "preseal"
            else required_delivery_paths()
        )
        for relative in delivery_paths:
            path = run_dir / relative
            if not path.is_file():
                errors.append(f"missing delivery file: {relative}")
        if isinstance(packet, dict):
            _scan_delivery_for_protected_retrieval_values(
                run_dir, packet, delivery_paths, errors
            )
        for relative in ("delivery/xi-kari-answer.md", "delivery/xi-kari-dossier.md", "delivery/xi-kari-concept-atlas.md", "delivery/xi-kari-case-and-countercase.md"):
            path = run_dir / relative
            if path.is_file():
                errors.extend(f"{relative}: {error}" for error in check_plain_language(path.read_text(encoding="utf-8")))
        if isinstance(packet, dict):
            payload = _reader_payload_projection(packet, contract)
            try:
                expected_delivery = {
                    "delivery/xi-kari-answer.md": render_answer(payload),
                    "delivery/xi-kari-dossier.md": render_dossier(payload),
                    "delivery/xi-kari-concept-atlas.md": render_atlas(payload),
                    "delivery/xi-kari-case-and-countercase.md": render_casebook(
                        payload
                    ),
                }
            except Exception as exc:
                errors.append(f"fresh delivery projection failed: {exc}")
                expected_delivery = {}
            for relative, expected_text in expected_delivery.items():
                path = run_dir / relative
                if path.is_file() and path.read_text(encoding="utf-8") != expected_text:
                    errors.append(
                        f"delivery differs from disk packet projection: {relative}"
                    )
            runtime_binding = packet.get("runtime_binding", {})
            try:
                expected_index = render_artifact_index(
                    run_dir,
                    contract_profile=str(contract.get("contract_profile")),
                    authoring_profile=str(
                        runtime_binding.get("semantic_authoring_profile")
                    ),
                )
            except Exception as exc:
                errors.append(f"cannot rebuild XK11 artifact index: {exc}")
            else:
                index_path = run_dir / "delivery/artifact-index.md"
                if (
                    index_path.is_file()
                    and index_path.read_text(encoding="utf-8") != expected_index
                ):
                    errors.append("XK11 artifact index differs from fresh projection")
        output_plan = _read(run_dir / "authoring" / "XK11-output-plan.json", errors, "XK11 output plan")
        if isinstance(output_plan, dict):
            errors.extend(validate_coverage(output_plan.get("coverage", {})))
        semantic_coverage = _read(
            run_dir / "authoring" / "XK11-semantic-coverage.json",
            errors,
            "XK11 semantic coverage",
        )
        if isinstance(semantic_coverage, dict) and (
            semantic_coverage.get("source_read_complete") is not True
            or semantic_coverage.get("candidate_closure_complete") is not True
            or semantic_coverage.get("reader_projection_complete") is not True
        ):
            errors.append("XK11 semantic coverage is incomplete")
        prose_review = _read(
            run_dir / "authoring" / "XK11-prose-review.json", errors, "XK11 prose review"
        )
        if isinstance(prose_review, dict) and prose_review.get("valid") is not True:
            errors.append("XK11 prose review is not valid")
        if (
            isinstance(packet, dict)
            and isinstance(source_lock_document, dict)
            and isinstance(retrieval_index, dict)
            and isinstance(evidence_ledger_document, dict)
            and isinstance(concept_closure_document, dict)
        ):
            payload = _reader_payload_projection(packet, contract)
            expected_coverage = build_coverage(
                run_id=str(contract_run_id),
                source_lock=source_lock_document,
                retrieval_index=retrieval_index,
                evidence_ledger=evidence_ledger_document,
            )
            expected_output_plan = build_prose_plan(
                run_id=str(contract_run_id),
                payload=payload,
                coverage=expected_coverage,
            )
            expected_output_plan["input_packet_sha256"] = sha256_file(
                run_dir / "continuation" / "input-packet.json"
            )
            if output_plan != expected_output_plan:
                errors.append("XK11 output plan differs from fresh projection")
            try:
                expected_semantic_coverage = build_semantic_coverage(
                    run_id=str(contract_run_id),
                    packet=packet,
                    source_read_complete=(
                        expected_coverage.get("source_read", {}).get("complete") is True
                    ),
                    candidate_closure_complete=(
                        concept_closure_document.get("complete") is True
                    ),
                    reader_outputs=load_reader_outputs(run_dir),
                )
            except Exception as exc:
                errors.append(f"fresh semantic coverage projection failed: {exc}")
                expected_semantic_coverage = None
            if (
                expected_semantic_coverage is not None
                and semantic_coverage != expected_semantic_coverage
            ):
                errors.append(
                    "XK11 semantic coverage differs from fresh projection"
                )
            expected_prose_errors: list[str] = []
            for relative in (
                "delivery/xi-kari-answer.md",
                "delivery/xi-kari-dossier.md",
                "delivery/xi-kari-concept-atlas.md",
                "delivery/xi-kari-case-and-countercase.md",
            ):
                path = run_dir / relative
                if path.is_file():
                    expected_prose_errors.extend(
                        f"{relative}: {error}"
                        for error in check_plain_language(
                            path.read_text(encoding="utf-8")
                        )
                    )
            expected_prose_review = {
                "schema_id": "xi-kari.v2.prose-review",
                "schema_version": 3,
                "run_id": str(contract_run_id),
                "check_method": "deterministic-plain-language-rules",
                "independent_reviewer": False,
                "required_reader_beats": expected_output_plan["reader_beats"],
                "errors": expected_prose_errors,
                "valid": (
                    not expected_prose_errors
                    and isinstance(expected_semantic_coverage, Mapping)
                    and expected_semantic_coverage["reader_projection_complete"]
                ),
            }
            if prose_review != expected_prose_review:
                errors.append("XK11 prose review differs from fresh projection")
        if validation_boundary in {"promotion", "official", "final"}:
            final_chat = _read(
                run_dir / "delivery" / "final-chat.json", errors, "final chat"
            )
            if isinstance(final_chat, dict) and final_chat.get(
                "validation_authority_path"
            ) != COMPLETION_RELATIVE:
                errors.append("final chat does not point to completion authority")
    if len(records) == len(PHASES):
        final_values = _phase_values(run_dir, records, "XK12", errors)
        if final_values and isinstance(final_values[0], dict):
            sealed_report = final_values[0]
            expected_report_metadata = {
                "validator_set_sha256": observed_validator_set,
                "run_id": contract_run_id,
                "fresh": True,
                "fresh_process": True,
                "validation_boundary": "preseal",
                "complete": False,
                "validated_phase": "XK11",
                "chain_head_sha256": records[11].get("record_sha256"),
                "phase_count": 12,
                "valid": True,
                "errors": [],
            }
            for field, expected_value in expected_report_metadata.items():
                if sealed_report.get(field) != expected_value:
                    errors.append(
                        f"sealed validator report metadata mismatch: {field}"
                    )
        elif final_values:
            errors.append("XK12 validator report is not valid")
        if len(final_values) >= 3 and isinstance(final_values[2], dict):
            manifest = final_values[2]
            packet_path = run_dir / "continuation" / "input-packet.json"
            if manifest.get("input_packet_sha256") != sha256_file(packet_path):
                errors.append("artifact manifest input packet hash mismatch")
            if manifest.get("validated_chain_head_sha256") != records[11].get("record_sha256"):
                errors.append("artifact manifest validated chain head mismatch")
            if manifest.get("validator_set_sha256") != observed_validator_set:
                errors.append("artifact manifest validator set mismatch")
            expected_candidate_sha256 = sha256_file(
                repository_root
                / "references"
                / "ontology"
                / "candidate-census.jsonl"
            )
            if (
                manifest.get("candidate_census_sha256")
                != expected_candidate_sha256
            ):
                errors.append("artifact manifest candidate census mismatch")
            if manifest.get("phase_responsibilities") != PHASE_RESPONSIBILITIES:
                errors.append("artifact manifest phase responsibilities mismatch")
            try:
                expected_phase_artifacts = build_phase_artifact_bindings(
                    run_dir, records[:12]
                )
            except Exception as exc:
                errors.append(f"cannot rebuild manifest phase artifacts: {exc}")
            else:
                if manifest.get("phase_artifacts") != expected_phase_artifacts:
                    errors.append("artifact manifest phase artifacts mismatch")
            expected_continuation_bindings = {}
            for relative in (
                "continuation/parent.json",
                "continuation/repair-record.json",
            ):
                path = run_dir / relative
                if path.is_file():
                    expected_continuation_bindings[relative] = sha256_file(path)
            observed_continuation_bindings = manifest.get(
                "continuation_bindings"
            )
            if observed_continuation_bindings != expected_continuation_bindings:
                for relative, expected_sha256 in expected_continuation_bindings.items():
                    if not isinstance(observed_continuation_bindings, dict) or (
                        observed_continuation_bindings.get(relative) != expected_sha256
                    ):
                        errors.append(
                            f"continuation binding hash mismatch: {relative}"
                        )
                if isinstance(observed_continuation_bindings, dict):
                    for relative in sorted(
                        set(observed_continuation_bindings)
                        - set(expected_continuation_bindings)
                    ):
                        errors.append(
                            f"manifest has an unowned continuation binding: {relative}"
                        )
            delivery = manifest.get("delivery")
            canonical_delivery = isinstance(delivery, dict) and set(
                delivery
            ) == set(DELIVERY_PATHS)
            observed_paths: list[str] = []
            if isinstance(delivery, dict):
                for key, binding in delivery.items():
                    if isinstance(binding, dict) and isinstance(
                        binding.get("path"), str
                    ):
                        observed_paths.append(binding["path"])
                    if (
                        key not in DELIVERY_PATHS
                        or not isinstance(binding, dict)
                        or binding.get("path") != DELIVERY_PATHS.get(key)
                    ):
                        canonical_delivery = False
            if len(observed_paths) != len(set(observed_paths)):
                canonical_delivery = False
            if not canonical_delivery:
                errors.append(
                    "artifact manifest delivery mapping/path is not canonical"
                )
            if isinstance(delivery, dict):
                for key, relative in DELIVERY_PATHS.items():
                    binding = delivery.get(key)
                    if not isinstance(binding, dict):
                        continue
                    try:
                        path = confined_path(run_dir, relative, must_exist=True)
                        if sha256_file(path) != binding.get("sha256"):
                            errors.append(f"delivery hash mismatch: {relative}")
                        if path.stat().st_size != binding.get("bytes"):
                            errors.append(f"delivery byte count mismatch: {relative}")
                    except Exception as exc:
                        errors.append(f"invalid delivery binding: {exc}")
    try:
        final_validator_set = compute_validator_set_sha256(repository_root)
    except Exception as exc:
        errors.append(f"cannot reload repository authority after validation: {exc}")
    else:
        if final_validator_set != observed_validator_set:
            errors.append("repository authority changed during fresh validation")
    return _report(
        contract.get("run_id"),
        records,
        errors,
        repository_root=repository_root,
        validation_boundary=validation_boundary,
        fresh_process=fresh_process,
    )


def _report(
    run_id: str | None,
    records: list[dict[str, Any]],
    errors: list[str],
    *,
    repository_root: Path,
    validation_boundary: str,
    fresh_process: bool,
) -> dict[str, Any]:
    try:
        validator_hash = compute_validator_set_sha256(repository_root)
    except Exception:
        validator_hash = "0" * 64
    return {
        "schema_id": "xi-kari.v2.validator-report",
        "schema_version": 3,
        "validator_version": VALIDATOR_VERSION,
        "validator_set_sha256": validator_hash,
        "run_id": run_id,
        "fresh": True,
        "fresh_process": fresh_process,
        "validator_pid": os.getpid(),
        "validation_boundary": validation_boundary,
        "complete": (
            validation_boundary == "final"
            and len(records) == len(PHASES)
            and not errors
        ),
        "checked_at": _utc_now(),
        "validated_phase": records[-1].get("phase") if records else None,
        "chain_head_sha256": records[-1].get("record_sha256") if records else None,
        "phase_count": len(records),
        "checks": sorted(set(PHASE_RESPONSIBILITIES.get(record.get("phase"), "chain") for record in records)),
        "valid": not errors,
        "errors": list(dict.fromkeys(errors)),
    }


def build_preseal_report(run_dir: Path, *, repository_root: Path | None = None) -> dict[str, Any]:
    report = validate_run(
        run_dir,
        repository_root=repository_root,
        require_complete=False,
        validation_boundary="preseal",
    )
    if report["validated_phase"] != "XK11":
        report["errors"].append("pre-seal validation requires XK11")
        report["valid"] = False
    return report


def run_fresh_validator(
    run_dir: Path,
    *,
    repository_root: Path,
    preseal: bool,
    promotion: bool = False,
    official: bool = False,
    require_complete: bool = True,
) -> dict[str, Any]:
    if sum((preseal, promotion, official)) > 1:
        raise ValueError("fresh validator boundary is ambiguous")
    root = Path(repository_root).expanduser().resolve()
    command = [
        sys.executable,
        str(root / "scripts" / "xi_kari_runtime.py"),
        "validate",
        "--run-dir",
        str(Path(run_dir).expanduser()),
        "--repository-root",
        str(root),
    ]
    if preseal:
        command.append("--preseal")
    if promotion:
        command.append("--promotion")
    if official:
        command.append("--official")
    if not require_complete:
        command.append("--allow-incomplete")
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        command,
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        report = read_json_text(completed.stdout)
    except Exception as exc:
        raise ValueError(
            f"fresh validator produced no readable report: {completed.stderr.strip()}"
        ) from exc
    if not isinstance(report, dict):
        raise ValueError("fresh validator report is not an object")
    expected_boundary = (
        "preseal"
        if preseal
        else "promotion"
        if promotion
        else "official"
        if official
        else "final"
    )
    if (
        report.get("fresh_process") is not True
        or report.get("validator_pid") == os.getpid()
        or report.get("validation_boundary") != expected_boundary
    ):
        raise ValueError("validator report did not come from the required fresh process")
    if (completed.returncode == 0) != (report.get("valid") is True):
        raise ValueError("fresh validator exit status differs from its report")
    return report


fresh_validate = validate_run
