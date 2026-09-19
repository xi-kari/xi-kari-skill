"""Authoritative Xi-Kari v3 run lifecycle and semantic phase materialization."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Mapping
import uuid

from .authority import repository_root as resolve_repository_root
from .authority import validator_set_sha256
from .authoring import (
    BASE_CLOSED_INPUT_WEB_SEARCH,
    BASE_OPEN_WORLD_WEB_SEARCH,
    FORMAL_ADAPTER_PROFILE,
    DEFAULT_ADAPTER_TIMEOUT_SECONDS,
    MAX_AUTHORING_TIMEOUT_SECONDS,
    FORMAL_ADAPTER_RELATIVE_PATH,
    author_semantic_probe_variants,
    bind_semantic_authoring_adapter,
    require_semantic_authoring_adapter,
    require_base_authoring_provider,
    validate_semantic_probe_authorings,
)
from .canonical_json import (
    atomic_write_bytes,
    atomic_write_json,
    atomic_write_text,
    canonical_bytes,
    confined_path,
    read_bounded_regular_file,
    read_json,
    sha256_bytes,
    sha256_file,
    sha256_json,
    sha256_text,
)
from .concept_authority import load_concept_authority
from .continuation_input import load_runtime_bound_closed_input_materials
from .contracts import (
    CONTRACT_PROFILES,
    COMPLETE_STATE_MISMATCH_ERROR,
    DELIVERY_PATHS,
    DYNAMIC_PHASE_FIELDS,
    EXECUTE_OWNED_BINDING_FIELDS,
    PREMATURE_COMPLETE_STATE_ERROR,
    PHASE_RESPONSIBILITIES,
    PRODUCTION_CONTRACT_PROFILE,
    build_phase_artifact_bindings,
    build_continuity_bundle_binding,
    build_execute_owned_binding,
    validate_execute_owned_binding,
    build_runtime_packet_binding,
    derive_repair_scope,
    expected_phase_artifact_paths,
    repair_phase_events_sha256,
    is_safe_run_id,
    require_packet_contract,
    required_delivery_paths,
    validate_lifecycle_sidecars,
    validate_packet_references,
    validate_repair_packet_binding,
    validate_runtime_control_bindings,
)
from .coverage import build_coverage, build_semantic_coverage, load_reader_outputs
from .evidence import build_evidence_ledger, validate_evidence_ledger
from .judgment import (
    empty_framework_gap_ledger,
    validate_action_ranking,
    validate_framework_gap_isolation,
    validate_verdict_bundle,
)
from .phase_chain import PHASES, append_phase, load_phase_records, validate_phase_chain
from .ontology_read_trace import (
    build_ontology_read_plan,
    build_ontology_read_trace,
    validate_ontology_read_trace,
)
from .prose import (
    assemble_outputs,
    build_prose_plan,
    check_plain_language,
    render_artifact_index,
)
from .problem_contract import (
    FROZEN_FIELDS,
    contract_hash,
    stance_neutrality_key,
    validate_problem_contract,
)
from .semantic_chain import validate_semantic_chain
from .semantic_projection import validate_visibility_ledger
from .semantic_read_trace import build_semantic_read_trace
from .stability import build_sensitivity_report, build_stance_stability_report
from .retrieval import (
    ALLOWED_MODES,
    build_full_source_lock,
    build_retrieval_plan,
    materialize_retrieval_bundle,
    validate_full_source_lock,
    validate_retrieval_bundle,
)
from .retrieval_execution import HOST_CAPTURE_INDEX_RELATIVE, load_host_capture_bundle
from .transformations import validate_cascade
from .terminal_authority import (
    COMPLETION_RELATIVE,
    KEY_RELATIVE,
    OFFICIAL_REPORT_RELATIVE,
    TERMINAL_RELATIVE,
    TRANSACTION_RELATIVE,
    commit_terminal_record,
    generate_terminal_authority,
    validate_terminal_closure,
)
from .validation import run_fresh_validator, validate_run, validator_fingerprint
from .world_volume import bind_world_evidence_state, world_evidence_target_hashes


from .source_profile import RUNTIME_VERSION, require_current_source
ARTIFACT_SCHEMA_VERSION = 3
DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRIVACY_PURPOSE = "回答冻结问题并仅向请求用户交付"
DEFAULT_DELIVERY_AUDIENCE = "requesting-user"
_PRODUCTION_CAPABILITY_SEAL = object()


class _ProductionPreparationCapability:
    """One-shot in-process authority for the production materializer."""

    __slots__ = (
        "_seal",
        "_run_id",
        "_problem_contract",
        "_semantic_trace_path",
        "_ontology_trace_path",
        "_base_authoring_execution",
        "_base_authoring_events",
        "_execute_owned_binding",
        "_process",
        "_consumed",
    )

    def __init__(
        self,
        *,
        run_id: str,
        problem_contract: Mapping[str, Any],
        semantic_trace_path: Path,
        ontology_trace_path: Path,
        base_authoring_execution: Mapping[str, Any],
        base_authoring_events: bytes,
        execute_owned_binding: Mapping[str, Any],
        process: subprocess.Popen[bytes],
    ) -> None:
        self._seal = _PRODUCTION_CAPABILITY_SEAL
        self._run_id = run_id
        self._problem_contract = problem_contract
        self._semantic_trace_path = semantic_trace_path
        self._ontology_trace_path = ontology_trace_path
        self._base_authoring_execution = base_authoring_execution
        self._base_authoring_events = base_authoring_events
        self._execute_owned_binding = execute_owned_binding
        self._process = process
        self._consumed = False

    def consume_for(
        self,
        *,
        run_id: str,
        problem_contract: Mapping[str, Any],
        semantic_trace_path: Path,
        ontology_trace_path: Path,
        base_authoring_execution: Mapping[str, Any],
        base_authoring_events: bytes,
    ) -> Mapping[str, Any]:
        if self._seal is not _PRODUCTION_CAPABILITY_SEAL:
            raise ValueError("production preparation capability is invalid")
        if self._consumed:
            raise ValueError("production preparation capability was already consumed")
        if self._process.poll() != 0:
            raise ValueError("production provider process is not successfully complete")
        if (
            self._run_id != run_id
            or self._problem_contract is not problem_contract
            or self._semantic_trace_path is not semantic_trace_path
            or self._ontology_trace_path is not ontology_trace_path
            or self._base_authoring_execution is not base_authoring_execution
            or self._base_authoring_events is not base_authoring_events
        ):
            raise ValueError("production preparation inputs are not execute-owned")
        self._consumed = True
        return self._execute_owned_binding

    def __reduce__(self) -> Any:
        raise TypeError("production preparation capability is not serializable")


def _issue_production_preparation_capability(
    *,
    run_id: str,
    problem_contract: Mapping[str, Any],
    semantic_trace_path: Path,
    ontology_trace_path: Path,
    base_authoring_execution: Mapping[str, Any],
    base_authoring_events: bytes,
    execute_owned_binding: Mapping[str, Any],
    process: subprocess.Popen[bytes],
    request_bytes: bytes,
    prompt_bytes: bytes,
    stderr_bytes: bytes,
    output_bytes: bytes,
    retrieval_receipt: Mapping[str, Any],
) -> _ProductionPreparationCapability:
    if set(execute_owned_binding) != EXECUTE_OWNED_BINDING_FIELDS:
        raise ValueError("execute-owned binding fields are not exact")
    if not isinstance(process, subprocess.Popen) or process.poll() != 0:
        raise ValueError("production provider process is not successfully complete")
    if process.pid != base_authoring_execution.get("child_pid"):
        raise ValueError("production provider PID differs from execution evidence")
    if sha256_json(list(process.args)) != base_authoring_execution.get(
        "command_sha256"
    ):
        raise ValueError("production provider argv differs from execution evidence")
    observed_hashes = {
        "input_sha256": sha256_bytes(request_bytes),
        "prompt_sha256": sha256_bytes(prompt_bytes),
        "stdout_sha256": sha256_bytes(base_authoring_events),
        "stderr_sha256": sha256_bytes(stderr_bytes),
        "semantic_output_sha256": sha256_bytes(output_bytes),
        "semantic_read_trace_sha256": sha256_json(read_json(semantic_trace_path)),
        "ontology_read_trace_sha256": sha256_json(read_json(ontology_trace_path)),
    }
    for field, observed in observed_hashes.items():
        if base_authoring_execution.get(field) != observed:
            raise ValueError(
                f"production execution evidence differs from observed bytes: {field}"
            )
    expected_binding = build_execute_owned_binding(
        base_authoring_execution,
        retrieval_receipt,
    )
    if dict(execute_owned_binding) != expected_binding:
        raise ValueError("execute-owned binding differs from observed execution")
    return _ProductionPreparationCapability(
        run_id=run_id,
        problem_contract=problem_contract,
        semantic_trace_path=semantic_trace_path,
        ontology_trace_path=ontology_trace_path,
        base_authoring_execution=base_authoring_execution,
        base_authoring_events=base_authoring_events,
        execute_owned_binding=execute_owned_binding,
        process=process,
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def default_runs_root() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "xi-kari-skill" / "runs"
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "xi-kari-skill" / "runs"


def _new_run_id() -> str:
    return f"xk-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:12]}"


def _safe_run_id(value: str) -> str:
    if not is_safe_run_id(value):
        raise ValueError("run_id must match the safe 1-96 character grammar")
    return value


def _require_mutable_contract_profile(contract: Mapping[str, Any]) -> None:
    require_current_source(contract)
    if contract.get("schema_id") != "xi-kari.v3.run-contract" or contract.get("schema_version") != ARTIFACT_SCHEMA_VERSION or contract.get("runtime_version") != RUNTIME_VERSION:
        raise ValueError("run identity is incompatible with runtime 3.0.0; automatic migration is not supported")
    profile = contract.get("contract_profile")
    if profile is None:
        raise ValueError(
            "historical run without contract profile is read-only"
        )
    if profile not in CONTRACT_PROFILES:
        raise ValueError(f"unsupported contract profile: {profile}")


def _require_external_runs_root(root: Path, repository_root: Path) -> None:
    forbidden_roots = {
        Path(repository_root).resolve(),
        DEFAULT_REPOSITORY_ROOT.resolve(),
    }
    for forbidden in forbidden_roots:
        try:
            root.relative_to(forbidden)
        except ValueError:
            continue
        raise ValueError(
            "run root must be outside the repository and Skill installation directory"
        )


def _resolve_run_directory(path: Path) -> Path:
    candidate = Path(path).expanduser().absolute()
    current = Path(candidate.anchor)
    for part in candidate.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"run directory path contains a symlink: {current}")
    return candidate.resolve()


def _write(run_dir: Path, relative: str, value: Any) -> None:
    atomic_write_json(confined_path(run_dir, relative), value)


def _phase_input(previous: dict[str, Any] | None, value: Any) -> str:
    return sha256_json({"predecessor": previous.get("record_sha256") if previous else None, "value": value})


def _seal(
    run_dir: Path,
    *,
    run_id: str,
    phase: str,
    paths: list[str],
    value: Any,
    predecessor: dict[str, Any] | None,
) -> dict[str, Any]:
    # All semantic values are serialized before the event is appended.  The
    # event therefore binds bytes on disk, not a caller-owned in-memory object.
    if isinstance(value, Mapping):
        main_path = paths[0]
        _write(run_dir, main_path, value)
    record = append_phase(
        run_dir,
        run_id=run_id,
        phase=phase,
        artifact_path=paths,
        input_sha256=_phase_input(predecessor, value),
        created_at=utc_now(),
    )
    return record


def _set_state(run_dir: Path, state: str, *, next_phase: str | None = None) -> None:
    run_id = read_json(run_dir / "run-contract.json").get("run_id")
    _write(
        run_dir,
        "continuation/state.json",
        {
            "schema_id": "xi-kari.v3.continuation-state",
            "schema_version": 3,
            "run_id": run_id,
            "state": state,
            "next_phase": next_phase,
            "updated_at": utc_now(),
        },
    )


def _status_from_records(run_dir: Path, records: list[dict[str, Any]], request: dict[str, Any]) -> dict[str, Any]:
    state_file = run_dir / "continuation" / "state.json"
    continuation = read_json(state_file) if state_file.is_file() else {}
    explicit = continuation.get("state")
    derived = (
        "complete"
        if len(records) == len(PHASES)
        else "initialized"
        if len(records) == 1 and explicit == "initialized"
        else "prepared"
        if len(records) <= 2
        else "in_progress"
    )
    if explicit == "needs_attention":
        state = explicit
    elif len(records) == len(PHASES):
        state = "needs_attention"
    elif explicit in {"complete", "cancelled"}:
        state = "needs_attention"
    else:
        state = derived
    return {
        "schema_id": "xi-kari.v3.run-status",
        "schema_version": 3,
        "run_id": request.get("run_id"),
        "run_dir": str(run_dir),
        "mode": request.get("mode"),
        "state": state,
        "phase_count": len(records),
        "current_phase": records[-1]["phase"] if records else None,
        "next_phase": PHASES[len(records)] if len(records) < len(PHASES) else None,
        "chain_head_sha256": records[-1].get("record_sha256") if records else None,
        "generation": request.get("continuation", {}).get("generation", 0),
        "parent_run_id": request.get("continuation", {}).get("parent_run_id"),
    }


def _write_run_contract(
    run_dir: Path,
    *,
    run_id: str,
    problem_contract: Mapping[str, Any],
    mode: str,
    generation: int,
    parent_run_id: str | None,
    parent_chain_head_sha256: str | None,
    kind: str,
    repository_root: Path,
    authority_sha256: str,
    terminal_authority: Mapping[str, str],
    semantic_authoring_adapter_binding: Mapping[str, Any] | None,
    execute_owned_binding: Mapping[str, Any] | None,
    contract_profile: str,
    privacy_purpose: str,
    delivery_audience: str,
    natural_request: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    question = str(problem_contract["question"])
    privacy_contract = {
        "purpose": privacy_purpose,
        "delivery_audience": delivery_audience,
        "classification_scheme": [
            "public",
            "context_limited",
            "sensitive",
            "highly_sensitive",
            "refused_disclosure",
        ],
        "fail_closed": True,
    }
    contract = {
        "schema_id": "xi-kari.v3.run-contract",
        "schema_version": 3,
        "runtime_version": RUNTIME_VERSION,
        "run_id": run_id,
        "question": question,
        "problem_contract": dict(problem_contract),
        "problem_contract_sha256": contract_hash(problem_contract),
        "mode": mode,
        "source_version": "v8.3",
        "contract_profile": contract_profile,
        "repository_root": str(repository_root),
        "validator_set_sha256": authority_sha256,
        "created_at": utc_now(),
        "evidence_cutoff": problem_contract["evidence_cutoff"],
        "dynamic_applicability": "pending",
        "privacy_contract": privacy_contract,
        "continuation": {
            "kind": kind,
            "generation": generation,
            "parent_run_id": parent_run_id,
            "parent_chain_head_sha256": parent_chain_head_sha256,
        },
        "capability_snapshot": {
            "contract_profile": contract_profile,
            "network_retrieval": mode == "open-world",
            "full_source_read_required": True,
            "source_unit_count": 4753,
            "reader_unit_count": 21,
            "semantic_authoring_adapter": (
                dict(semantic_authoring_adapter_binding)
                if semantic_authoring_adapter_binding is not None
                else None
            ),
        },
        "stance_neutrality_key": stance_neutrality_key(
            problem_contract, mode=mode
        ),
        "terminal_authority": dict(terminal_authority),
    }
    if natural_request is not None:
        contract["natural_request"] = dict(natural_request)
    if execute_owned_binding is not None:
        contract["capability_snapshot"]["execute_owned_binding"] = dict(
            execute_owned_binding
        )
    atomic_write_json(run_dir / "run-contract.json", contract)
    return contract


def _bound_repository_root(
    run_dir: Path, supplied_root: Path | None
) -> Path:
    contract = read_json(run_dir / "run-contract.json")
    value = contract.get("repository_root")
    if not isinstance(value, str) or not value:
        raise ValueError("run contract has no repository root authority")
    bound = resolve_repository_root(Path(value))
    if supplied_root is not None:
        supplied = resolve_repository_root(supplied_root)
        if supplied != bound:
            raise ValueError("supplied repository root differs from the run contract")
    observed = validator_set_sha256(bound)
    if contract.get("validator_set_sha256") != observed:
        raise ValueError("repository authority differs from the run contract")
    return bound


def _require_stable_repository_authority(
    repository_root: Path,
    contract: Mapping[str, Any],
    *,
    boundary: str,
) -> None:
    if validator_set_sha256(repository_root) != contract.get(
        "validator_set_sha256"
    ):
        raise ValueError(f"repository authority changed during {boundary}")


def _prepare_run_impl(
    runs_root: Path | None = None,
    *,
    question: str | None = None,
    problem_contract: Mapping[str, Any] | None = None,
    mode: str = "open-world",
    run_id: str | None = None,
    repository_root: Path | None = None,
    generation: int = 0,
    parent_run_id: str | None = None,
    parent_chain_head_sha256: str | None = None,
    continuation_kind: str = "original",
    semantic_authoring_adapter: str | Path | None = None,
    semantic_authoring_timeout_seconds: int = DEFAULT_ADAPTER_TIMEOUT_SECONDS,
    contract_profile: str | None = None,
    semantic_read_trace_path: str | Path | None = None,
    ontology_read_trace_path: str | Path | None = None,
    ontology_read_plan: Mapping[str, Any] | None = None,
    semantic_authoring_profile: str | None = None,
    codex_provider_executable: str | Path | None = None,
    privacy_purpose: str = DEFAULT_PRIVACY_PURPOSE,
    delivery_audience: str = DEFAULT_DELIVERY_AUDIENCE,
    base_authoring_execution: Mapping[str, Any] | None = None,
    base_authoring_events: bytes | None = None,
    base_authoring_request: bytes | None = None,
    base_authoring_prompt: bytes | None = None,
    base_authoring_output: bytes | None = None,
    semantic_retrieval_input: Mapping[str, Any] | None = None,
    retrieval_execution_receipt: Mapping[str, Any] | None = None,
    natural_request: Mapping[str, Any] | None = None,
    _production_capability: _ProductionPreparationCapability | None = None,
) -> Path:
    if problem_contract is None:
        raise ValueError("prepare_run requires a complete problem_contract")
    if mode not in ALLOWED_MODES:
        raise ValueError(f"unsupported mode: {mode}")
    frozen_problem = validate_problem_contract(problem_contract, mode=mode)
    if contract_profile is None:
        raise ValueError("prepare_run requires an explicit contract profile")
    if semantic_authoring_profile is None:
        raise ValueError(
            "prepare_run requires an explicit semantic authoring profile"
        )
    if contract_profile not in CONTRACT_PROFILES:
        raise ValueError(f"unsupported contract profile: {contract_profile}")
    if contract_profile == PRODUCTION_CONTRACT_PROFILE and not isinstance(
        _production_capability, _ProductionPreparationCapability
    ):
        raise ValueError("production preparation requires execute-owned capability")
    if (
        contract_profile == PRODUCTION_CONTRACT_PROFILE
        and semantic_authoring_profile != FORMAL_ADAPTER_PROFILE
    ):
        raise ValueError(
            "production-authoring-v3 requires the production-codex "
            "semantic authoring profile"
        )
    if (
        contract_profile == PRODUCTION_CONTRACT_PROFILE
        and semantic_read_trace_path is None
    ):
        raise ValueError(
            "production-authoring-v3 requires a semantic read trace"
        )
    if (
        contract_profile == PRODUCTION_CONTRACT_PROFILE
        and base_authoring_execution is not None
        and ontology_read_trace_path is None
    ):
        raise ValueError(
            "production base authoring requires an ontology read trace"
        )
    if question is not None and question.strip() != frozen_problem["question"]:
        raise ValueError("question differs from problem_contract.question")
    if not isinstance(privacy_purpose, str) or not privacy_purpose.strip():
        raise ValueError("privacy purpose must be non-empty text")
    if not isinstance(delivery_audience, str) or not delivery_audience.strip():
        raise ValueError("delivery audience must be non-empty text")
    repo = resolve_repository_root(repository_root or DEFAULT_REPOSITORY_ROOT)
    authority_sha256 = validator_set_sha256(repo)
    semantic_authoring_adapter_binding = bind_semantic_authoring_adapter(
        semantic_authoring_adapter,
        timeout_seconds=semantic_authoring_timeout_seconds,
        profile=semantic_authoring_profile,
        codex_provider_executable=codex_provider_executable,
        repository_root=repo,
    )
    run_id = _safe_run_id(run_id or _new_run_id())
    execute_owned_binding = None
    if _production_capability is not None:
        if (
            semantic_read_trace_path is None
            or ontology_read_trace_path is None
            or base_authoring_execution is None
            or base_authoring_events is None
            or base_authoring_request is None
            or base_authoring_prompt is None
            or base_authoring_output is None
            or semantic_retrieval_input is None
            or retrieval_execution_receipt is None
        ):
            raise ValueError("production preparation evidence is incomplete")
        execute_owned_binding = _production_capability.consume_for(
            run_id=run_id,
            problem_contract=problem_contract,
            semantic_trace_path=semantic_read_trace_path,
            ontology_trace_path=ontology_read_trace_path,
            base_authoring_execution=base_authoring_execution,
            base_authoring_events=base_authoring_events,
        )
        binding_errors = validate_execute_owned_binding(
            execute_owned_binding,
            run_contract={"run_id": run_id},
        )
        if binding_errors:
            raise ValueError(binding_errors[0])
    terminal_authority, terminal_private_key = generate_terminal_authority(run_id)
    if parent_run_id is not None and not is_safe_run_id(parent_run_id):
        raise ValueError(f"unsafe parent_run_id: {parent_run_id}")
    root = _resolve_run_directory(runs_root or default_runs_root())
    _require_external_runs_root(root, repo)
    root.mkdir(parents=True, exist_ok=True)
    run_dir = root / run_id
    if run_dir.exists():
        raise FileExistsError(f"run directory already exists: {run_dir}")
    run_dir.mkdir(mode=0o700)
    for relative in ("authoring", "artifacts", "delivery", "validation/attempts", "continuation"):
        (run_dir / relative).mkdir(parents=True, exist_ok=True)
    contract = _write_run_contract(
        run_dir,
        run_id=run_id,
        problem_contract=frozen_problem,
        mode=mode,
        generation=generation,
        parent_run_id=parent_run_id,
        parent_chain_head_sha256=parent_chain_head_sha256,
        kind=continuation_kind,
        repository_root=repo,
        authority_sha256=authority_sha256,
        terminal_authority=terminal_authority,
        semantic_authoring_adapter_binding=semantic_authoring_adapter_binding,
        execute_owned_binding=execute_owned_binding,
        contract_profile=contract_profile,
        privacy_purpose=privacy_purpose.strip(),
        delivery_audience=delivery_audience.strip(),
        natural_request=natural_request,
    )
    atomic_write_json(run_dir / KEY_RELATIVE, terminal_private_key)
    capability_snapshot = {
        "schema_id": "xi-kari.v3.capability-snapshot",
        "schema_version": 3,
        "run_id": run_id,
        "mode": mode,
        **contract["capability_snapshot"],
        "captured_at": contract["created_at"],
    }
    atomic_write_json(run_dir / "capability-snapshot.json", capability_snapshot)
    xk0_record = append_phase(
        run_dir,
        run_id=run_id,
        phase="XK0",
        artifact_path=["run-contract.json", "capability-snapshot.json"],
        input_sha256=sha256_json(
            {
                "question": frozen_problem["question"],
                "mode": mode,
                "problem_contract": frozen_problem,
                "privacy_contract": contract["privacy_contract"],
            }
        ),
        created_at=contract["created_at"],
    )
    lock, events = build_full_source_lock(repo, run_id=run_id)
    atomic_write_json(run_dir / "source-lock.json", lock)
    atomic_write_text(
        run_dir / "authoring" / "XK01-read-events.jsonl",
        "".join(__import__("json").dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for event in events),
    )
    read_plan = {
        "schema_id": "xi-kari.v3.read-plan",
        "schema_version": 3,
        "run_id": run_id,
        "framework_version": lock["framework_version"],
        "reader_sequence": lock["reader_sequence"],
        "reader_unit_count": lock["reader_unit_count"],
        "paragraph_count": lock["paragraph_count"],
        "table_count": lock["table_count"],
        "source_unit_count": lock["source_unit_count"],
        "requires_complete_semantic_read": True,
    }
    atomic_write_json(run_dir / "authoring" / "XK01-read-plan.json", read_plan)
    semantic_read_trace = None
    ontology_read_trace = None
    if contract_profile == PRODUCTION_CONTRACT_PROFILE:
        semantic_read_trace = build_semantic_read_trace(
            semantic_read_trace_path,
            repository_root=repo,
            run_contract=contract,
            source_lock=lock,
            source_events=events,
            xk0_record_sha256=xk0_record["record_sha256"],
            imported_at=utc_now(),
            base_authoring_execution=base_authoring_execution,
        )
        atomic_write_json(
            run_dir / "authoring" / "XK01-semantic-read-trace.json",
            semantic_read_trace,
        )
        if base_authoring_events is not None:
            if not isinstance(base_authoring_events, bytes) or not base_authoring_events:
                raise ValueError("base authoring event stream must be non-empty bytes")
            atomic_write_bytes(
                run_dir / "authoring" / "XK01-base-authoring-events.jsonl",
                base_authoring_events,
            )
        if contract_profile == PRODUCTION_CONTRACT_PROFILE:
            if not all(
                isinstance(value, bytes)
                for value in (
                    base_authoring_request,
                    base_authoring_prompt,
                    base_authoring_output,
                )
            ) or not isinstance(semantic_retrieval_input, Mapping) or not isinstance(
                retrieval_execution_receipt, Mapping
            ):
                raise ValueError("production authoring evidence is incomplete")
            atomic_write_bytes(
                run_dir / "authoring" / "XK01-base-authoring-request.json",
                base_authoring_request,
            )
            atomic_write_bytes(
                run_dir / "authoring" / "XK01-base-authoring-prompt.txt",
                base_authoring_prompt,
            )
            atomic_write_bytes(
                run_dir / "authoring" / "XK01-base-authoring-output.bin",
                base_authoring_output,
            )
            atomic_write_json(
                run_dir / "authoring" / "XK01-base-authoring-receipt.json",
                base_authoring_execution,
            )
            atomic_write_json(
                run_dir / "authoring" / "XK02-semantic-retrieval.json",
                semantic_retrieval_input,
            )
            atomic_write_json(
                run_dir / "authoring" / "XK02-retrieval-execution-receipt.json",
                retrieval_execution_receipt,
            )
        if ontology_read_trace_path is not None:
            if not isinstance(ontology_read_plan, Mapping):
                raise ValueError(
                    "production ontology read requires the runtime-owned plan"
                )
            fresh_ontology_read_plan = build_ontology_read_plan(
                repo,
                run_id=run_id,
                problem_contract_sha256=contract_hash(frozen_problem),
                content_access_challenge=ontology_read_plan.get(
                    "content_access_challenge"
                ),
            )
            if dict(ontology_read_plan) != fresh_ontology_read_plan:
                raise ValueError(
                    "production ontology read plan differs from current authority"
                )
            raw_ontology_trace = read_json(Path(ontology_read_trace_path))
            if not isinstance(raw_ontology_trace, Mapping):
                raise ValueError("ontology read trace input is not an object")
            ontology_read_trace = build_ontology_read_trace(
                raw_ontology_trace,
                plan=ontology_read_plan,
                run_id=run_id,
                repository_root=repo,
                problem_contract_sha256=contract_hash(frozen_problem),
            )
            if base_authoring_execution is not None:
                if base_authoring_execution.get(
                    "ontology_read_plan_sha256"
                ) != sha256_json(ontology_read_plan):
                    raise ValueError(
                        "base authoring receipt ontology read plan hash differs"
                    )
                if base_authoring_execution.get(
                    "ontology_read_trace_sha256"
                ) != sha256_json(raw_ontology_trace):
                    raise ValueError(
                        "base authoring receipt ontology read trace hash differs"
                    )
            atomic_write_json(
                run_dir / "authoring" / "XK04-ontology-read-plan.json",
                ontology_read_plan,
            )
            atomic_write_json(
                run_dir / "authoring" / "XK04-ontology-read-trace.json",
                ontology_read_trace,
            )
    previous = load_phase_records(run_dir)[-1]
    append_phase(
        run_dir,
        run_id=run_id,
        phase="XK1",
        artifact_path=expected_phase_artifact_paths(
            "XK1", contract_profile=contract_profile
        ),
        input_sha256=_phase_input(
            previous,
            {
                "source_lock": lock,
                "semantic_read_trace": semantic_read_trace,
            },
        ),
        created_at=utc_now(),
    )
    # XK2 is intentionally left unsealed: the model must perform retrieval and
    # supply its ledger before the evidence boundary can be frozen.
    atomic_write_json(
        run_dir / "authoring" / "XK02-retrieval-ledger.json",
        {"schema_id": "xi-kari.v3.retrieval-ledger", "schema_version": 3, "run_id": run_id, "mode": mode, "status": "awaiting_retrieval"},
    )
    _set_state(run_dir, "prepared", next_phase="XK2")
    return run_dir


def prepare_run(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Read-only production preflight; only execute can create a sealed run."""

    if len(args) > 1:
        raise TypeError("prepare accepts only the runs root as a positional argument")
    if kwargs.get("semantic_read_trace_path") is not None or kwargs.get("ontology_read_trace_path") is not None:
        raise ValueError("read trace evidence is owned by execute; preflight does not accept caller receipts")
    if kwargs.get("contract_profile") != PRODUCTION_CONTRACT_PROFILE:
        raise ValueError("preflight requires the current production contract profile")
    if kwargs.get("semantic_authoring_profile") != FORMAL_ADAPTER_PROFILE:
        raise ValueError("preflight requires the production-codex semantic authoring profile")
    allowed = {
        "problem_contract", "mode", "run_id", "repository_root", "runs_root",
        "semantic_authoring_adapter", "semantic_authoring_timeout_seconds",
        "contract_profile", "semantic_authoring_profile", "codex_provider_executable",
        "semantic_read_trace_path", "privacy_purpose", "delivery_audience",
    }
    if set(kwargs) - allowed:
        raise ValueError("preflight cannot accept execute-owned or continuation controls")
    mode = kwargs.get("mode", "open-world")
    problem = validate_problem_contract(kwargs.get("problem_contract"), mode=mode)
    repo = resolve_repository_root(kwargs.get("repository_root") or DEFAULT_REPOSITORY_ROOT)
    adapter = bind_semantic_authoring_adapter(
        kwargs.get("semantic_authoring_adapter") or repo / FORMAL_ADAPTER_RELATIVE_PATH,
        timeout_seconds=kwargs.get("semantic_authoring_timeout_seconds", DEFAULT_ADAPTER_TIMEOUT_SECONDS),
        profile=FORMAL_ADAPTER_PROFILE,
        codex_provider_executable=kwargs.get("codex_provider_executable"),
        repository_root=repo,
    )
    requested_id = kwargs.get("run_id")
    if requested_id is not None:
        _safe_run_id(requested_id)
    runs_root = _resolve_run_directory((args[0] if args else kwargs.get("runs_root")) or default_runs_root())
    _require_external_runs_root(runs_root, repo)
    source_lock, _events = build_full_source_lock(repo, run_id="preflight")
    return {
        "status": "ready-for-execute", "preflight_only": True, "run_created": False,
        "analysis_complete": False, "runtime_version": RUNTIME_VERSION,
        "contract_profile": PRODUCTION_CONTRACT_PROFILE,
        "source_version": source_lock["framework_version"],
        "problem_contract_sha256": contract_hash(problem),
        "source_unit_count": source_lock["source_unit_count"],
        "semantic_authoring_adapter": adapter, "runs_root": str(runs_root),
        "next_command": "execute",
    }


def _prepare_production_run(
    runs_root: Path | None = None,
    *,
    capability: _ProductionPreparationCapability,
    problem_contract: Mapping[str, Any],
    mode: str,
    run_id: str,
    repository_root: Path,
    semantic_read_trace_path: Path,
    ontology_read_trace_path: Path,
    ontology_read_plan: Mapping[str, Any],
    semantic_authoring_adapter: str | Path,
    semantic_authoring_timeout_seconds: int,
    semantic_authoring_profile: str,
    codex_provider_executable: str | Path,
    privacy_purpose: str,
    delivery_audience: str,
    base_authoring_execution: Mapping[str, Any],
    base_authoring_events: bytes,
    base_authoring_request: bytes,
    base_authoring_prompt: bytes,
    base_authoring_output: bytes,
    semantic_retrieval_input: Mapping[str, Any],
    retrieval_execution_receipt: Mapping[str, Any],
    natural_request: Mapping[str, Any] | None,
    continuation_kind: str,
    generation: int,
    parent_run_id: str | None,
    parent_chain_head_sha256: str | None,
) -> Path:
    if not isinstance(capability, _ProductionPreparationCapability):
        raise ValueError("production preparation requires execute-owned capability")
    return _prepare_run_impl(
        runs_root,
        problem_contract=problem_contract,
        mode=mode,
        run_id=run_id,
        repository_root=repository_root,
        semantic_authoring_adapter=semantic_authoring_adapter,
        semantic_authoring_timeout_seconds=semantic_authoring_timeout_seconds,
        contract_profile=PRODUCTION_CONTRACT_PROFILE,
        semantic_read_trace_path=semantic_read_trace_path,
        ontology_read_trace_path=ontology_read_trace_path,
        ontology_read_plan=ontology_read_plan,
        semantic_authoring_profile=semantic_authoring_profile,
        codex_provider_executable=codex_provider_executable,
        privacy_purpose=privacy_purpose,
        delivery_audience=delivery_audience,
        base_authoring_execution=base_authoring_execution,
        base_authoring_events=base_authoring_events,
        base_authoring_request=base_authoring_request,
        base_authoring_prompt=base_authoring_prompt,
        base_authoring_output=base_authoring_output,
        semantic_retrieval_input=semantic_retrieval_input,
        retrieval_execution_receipt=retrieval_execution_receipt,
        natural_request=natural_request,
        continuation_kind=continuation_kind,
        generation=generation,
        parent_run_id=parent_run_id,
        parent_chain_head_sha256=parent_chain_head_sha256,
        _production_capability=capability,
    )


def _runtime_packet_binding(contract: Mapping[str, Any]) -> dict[str, Any]:
    return build_runtime_packet_binding(contract)


def _load_packet_from_disk(
    run_dir: Path,
    packet: Mapping[str, Any] | None,
    *,
    contract: Mapping[str, Any],
    repository_root: Path,
) -> dict[str, Any]:
    path = run_dir / "continuation" / "input-packet.json"
    if packet is not None:
        incoming = dict(packet)
        if "semantic_probe_authorings" in incoming:
            raise ValueError("semantic probe authoring control is runtime-owned")
        authoritative_dispositions, _ = load_concept_authority(repository_root)
        omitted_dispositions = object()
        supplied_dispositions = incoming.pop(
            "concept_disposition", omitted_dispositions
        )
        if (
            supplied_dispositions is not omitted_dispositions
            and supplied_dispositions != authoritative_dispositions
        ):
            raise ValueError(
                "caller concept disposition differs from repository authority"
            )
        incoming["concept_disposition"] = authoritative_dispositions
        supplied_binding = incoming.pop("runtime_binding", None)
        runtime_binding = _runtime_packet_binding(contract)
        if supplied_binding is not None:
            if not isinstance(supplied_binding, Mapping) or any(
                key not in runtime_binding or runtime_binding[key] != value
                for key, value in supplied_binding.items()
            ):
                raise ValueError(
                    "caller-supplied runtime binding differs from the run contract"
                )
        incoming["runtime_binding"] = runtime_binding
        problem = incoming.get("problem_contract")
        if not isinstance(problem, Mapping):
            raise ValueError("problem contract differs from the run contract")
        if problem.get("question") != contract.get("question"):
            raise ValueError(
                "problem contract question differs from the run contract"
            )
        try:
            frozen = validate_problem_contract(
                {field: problem.get(field) for field in FROZEN_FIELDS},
                mode=contract["mode"],
            )
        except ValueError as exc:
            raise ValueError("problem contract differs from the run contract") from exc
        if frozen != contract.get("problem_contract"):
            raise ValueError("problem contract differs from the run contract")
        if path.is_file():
            disk_packet = read_json(path)
            if not isinstance(disk_packet, dict):
                raise ValueError("input packet must be a JSON object")
            if sha256_json(disk_packet) != sha256_json(incoming):
                raise ValueError("input packet differs from this run; fork before changing it")
        if not path.is_file():
            atomic_write_json(path, incoming)
    if not path.is_file():
        raise ValueError("materialize requires an analysis packet")
    # Crucial authority boundary: downstream only sees bytes reread from disk.
    value = read_json(path)
    if not isinstance(value, dict):
        raise ValueError("input packet must be a JSON object")
    return value


def _concept_closure(repo: Path, packet: Mapping[str, Any]) -> dict[str, Any]:
    census_rows, authority = load_concept_authority(repo)
    if packet.get("concept_disposition") != census_rows:
        raise ValueError("persisted candidate disposition differs from repository authority")
    return {
        "schema_id": "xi-kari.v3.concept-disposition",
        "schema_version": 3,
        "source_candidate_index_sha256": authority[
            "source_candidate_index_sha256"
        ],
        "candidate_census_sha256": authority["candidate_census_sha256"],
        "concept_disposition_ledger_sha256": authority[
            "concept_disposition_ledger_sha256"
        ],
        "source_candidate_count": authority["source_candidate_count"],
        "dispositions": census_rows,
        "complete": True,
    }


def _concept_closure_report(
    repo: Path,
    *,
    run_id: str,
    concept: Mapping[str, Any],
    problem_contract_sha256: str,
    ontology_read_plan: Mapping[str, Any] | None = None,
    ontology_read_trace: Mapping[str, Any] | None = None,
    require_ontology_trace: bool = False,
) -> dict[str, Any]:
    ontology = repo / "references" / "ontology"
    registry_path = ontology / "concept-registry.json"
    relations_path = ontology / "concept-relations.json"
    continuity_path = ontology / "continuity-map.md"
    if not all(path.is_file() for path in (registry_path, relations_path, continuity_path)):
        raise ValueError("complete ontology authority is unavailable")
    registry = read_json(registry_path)
    relations = read_json(relations_path)
    if not isinstance(registry, Mapping) or not isinstance(relations, Mapping):
        raise ValueError("ontology registry or relation graph is invalid")

    relation_ids = set(relations)
    relation_edge_count = 0
    dangling_neighbor_count = 0
    semantic_without_neighbors_count = 0
    for concept_id, value in relations.items():
        if not isinstance(value, Mapping):
            raise ValueError(f"invalid ontology relation record: {concept_id}")
        neighbors = value.get("required_neighbors")
        if not isinstance(neighbors, list) or any(
            not isinstance(neighbor, str) for neighbor in neighbors
        ):
            raise ValueError(f"invalid ontology neighbors: {concept_id}")
        relation_edge_count += len(neighbors)
        dangling_neighbor_count += sum(
            neighbor not in relation_ids for neighbor in neighbors
        )
        if (
            value.get("disposition") in {"canonical_concept", "structural_rule"}
            and not neighbors
        ):
            semantic_without_neighbors_count += 1

    bundle_bindings: list[dict[str, Any]] = []
    for path in sorted((ontology / "bundles").glob("*.md")):
        bundle_bindings.append(build_continuity_bundle_binding(repo, path))

    disposition_counts: dict[str, int] = {}
    for row in concept["dispositions"]:
        disposition = str(row.get("disposition"))
        disposition_counts[disposition] = disposition_counts.get(disposition, 0) + 1
    unresolved_count = disposition_counts.get("unresolved", 0)
    ontology_trace_complete = not require_ontology_trace
    if require_ontology_trace:
        if not isinstance(ontology_read_plan, Mapping) or not isinstance(
            ontology_read_trace, Mapping
        ):
            ontology_trace_complete = False
        else:
            ontology_trace_complete = not validate_ontology_read_trace(
                ontology_read_trace,
                plan=ontology_read_plan,
                expected_run_id=run_id,
                expected_problem_contract_sha256=problem_contract_sha256,
                repository_root=repo,
            )
    complete = (
        concept.get("complete") is True
        and unresolved_count == 0
        and dangling_neighbor_count == 0
        and semantic_without_neighbors_count == 0
        and bool(bundle_bindings)
        and all(binding["source_anchors"] for binding in bundle_bindings)
        and ontology_trace_complete
    )
    report = {
        "schema_id": "xi-kari.v3.concept-closure-report",
        "schema_version": 3,
        "run_id": run_id,
        "candidate_census_sha256": concept["candidate_census_sha256"],
        "source_candidate_count": concept["source_candidate_count"],
        "disposition_counts": disposition_counts,
        "unresolved_count": unresolved_count,
        "concept_registry_sha256": sha256_file(registry_path),
        "concept_relations_sha256": sha256_file(relations_path),
        "continuity_map_sha256": sha256_file(continuity_path),
        "concept_count": registry.get("concept_count"),
        "concept_count_semantics": (
            "inventory record count; not a complete ontology concept count"
        ),
        "relation_edge_count": relation_edge_count,
        "dangling_neighbor_count": dangling_neighbor_count,
        "semantic_without_neighbors_count": semantic_without_neighbors_count,
        "bundle_count": len(bundle_bindings),
        "bundle_bindings": bundle_bindings,
        "complete": complete,
    }
    if require_ontology_trace and isinstance(ontology_read_plan, Mapping) and isinstance(
        ontology_read_trace, Mapping
    ):
        report.update(
            {
                "ontology_read_plan_sha256": sha256_json(ontology_read_plan),
                "ontology_read_trace_sha256": sha256_json(ontology_read_trace),
                "ontology_read_record_count": ontology_read_trace.get("record_count"),
                "ontology_read_complete": ontology_trace_complete,
            }
        )
    return report


def _pre_evidence_world_projection(
    world: Mapping[str, Any],
) -> tuple[dict[str, Any], bool]:
    projection = copy.deepcopy(dict(world))
    state = projection.get("evidence_state")
    if not isinstance(state, dict):
        return projection, False
    bindings = state.get("bindings")
    if not isinstance(bindings, list) or not bindings:
        return projection, False

    template = next(
        (
            binding
            for binding in bindings
            if isinstance(binding, Mapping)
            and isinstance(binding.get("support_edges"), list)
            and binding["support_edges"]
        ),
        None,
    )
    if template is None:
        return projection, False

    referenced: set[str] = set()

    def collect(value: object) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if key == "evidence_state":
                    continue
                if key in {"evidence_refs", "authorization_evidence_refs"}:
                    if isinstance(child, list):
                        referenced.update(
                            item for item in child if isinstance(item, str)
                        )
                    continue
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(projection)
    existing = {
        binding["evidence_ref"]: binding
        for binding in bindings
        if isinstance(binding, Mapping)
        and isinstance(binding.get("evidence_ref"), str)
        and isinstance(binding.get("support_edges"), list)
        and binding["support_edges"]
    }
    deferred_alias_validation = bool(referenced - set(existing))
    state["bindings"] = [
        copy.deepcopy(
            existing.get(
                evidence_ref,
                {
                    "evidence_ref": evidence_ref,
                    "support_edges": template["support_edges"],
                },
            )
        )
        for evidence_ref in sorted(referenced)
    ]
    return projection, deferred_alias_validation


def _semantic_validate(
    packet: Mapping[str, Any], *, repo: Path, evidence_mode: str = "open-world"
) -> None:
    if packet["dynamic_applicability"] == "not_applicable":
        return
    world = packet["local_world_model"]
    if packet.get("cascade") is not None:
        validate_cascade(packet["cascade"], world, repository_root=repo)
    states = packet["recursive_states"]
    if not isinstance(states, Mapping):
        raise ValueError("recursive_states must be a mapping")
    chain = validate_semantic_chain(
        world_volume=world,
        transformation_ledger=packet["transformation_ledger"],
        claim_mechanism_graph=packet["claim_mechanism_graph"],
        recursive_lineage=packet["recursive_lineage"],
        recursive_states=states,
        evidence_mode=evidence_mode,
        repository_root=repo,
    )
    graph = chain.graph
    recursive_validation = chain.recursive
    validate_verdict_bundle(
        packet["verdict"],
        claim_mechanism_graph=graph,
        recursive_validation=recursive_validation,
        recursive_states=states,
        evidence_mode=evidence_mode,
        repository_root=repo,
    )
    validate_action_ranking(
        packet["action_ranking"],
        verdict_bundle=packet["verdict"],
        repository_root=repo,
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
        recursive_states=states,
        evidence_mode=evidence_mode,
        repository_root=repo,
    )


def _validate_base_authoring_and_retrieval(
    run_dir: Path,
    *,
    contract: Mapping[str, Any],
    retrieval: Mapping[str, Any],
    packet: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Verify runtime-owned base process and host retrieval evidence.

    Production packets may not reach XK2 from a caller-provided semantic
    retrieval ledger.  The base receipt and the raw JSONL stream are captured
    before materialization; this function re-reads both and checks the
    retrieval projection from those bytes.
    """

    if contract.get("contract_profile") != PRODUCTION_CONTRACT_PROFILE:
        return None, None
    trace_path = run_dir / "authoring/XK01-semantic-read-trace.json"
    base_receipt_path = run_dir / "authoring/XK01-base-authoring-receipt.json"
    request_path = run_dir / "authoring/XK01-base-authoring-request.json"
    prompt_path = run_dir / "authoring/XK01-base-authoring-prompt.txt"
    output_path = run_dir / "authoring/XK01-base-authoring-output.bin"
    events_path = run_dir / "authoring/XK01-base-authoring-events.jsonl"
    retrieval_input_path = run_dir / "authoring/XK02-semantic-retrieval.json"
    retrieval_receipt_path = run_dir / "authoring/XK02-retrieval-execution-receipt.json"
    host_capture_index_path = run_dir / HOST_CAPTURE_INDEX_RELATIVE
    ontology_plan_path = run_dir / "authoring/XK04-ontology-read-plan.json"
    ontology_trace_path = run_dir / "authoring/XK04-ontology-read-trace.json"
    for path in (
        trace_path,
        base_receipt_path,
        request_path,
        prompt_path,
        output_path,
        events_path,
        retrieval_input_path,
        retrieval_receipt_path,
        *(
            (host_capture_index_path,)
            if contract.get("mode") == "open-world"
            else ()
        ),
        ontology_plan_path,
        ontology_trace_path,
    ):
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"production runtime evidence is missing or unsafe: {path.name}")
    trace = read_json(trace_path)
    base_receipt = read_json(base_receipt_path)
    if not isinstance(trace, Mapping) or not isinstance(base_receipt, Mapping):
        raise ValueError("production base authoring evidence is not an object")
    embedded = trace.get("base_authoring_execution")
    if not isinstance(embedded, Mapping) or dict(embedded) != dict(base_receipt):
        raise ValueError("XK1 base authoring receipt is not bound to the semantic trace")
    raw_events = events_path.read_bytes()
    request_bytes = request_path.read_bytes()
    prompt_bytes = prompt_path.read_bytes()
    output_bytes = read_bounded_regular_file(
        output_path,
        limit=16 * 1024 * 1024,
    )
    base_request = read_json(request_path)
    from .contract_authoring import validate_contract_authoring_binding
    validate_contract_authoring_binding(
        base_request=base_request, base_receipt=base_receipt, run_contract=contract,
        repository_root=Path(str(contract.get("repository_root"))),
    )
    ontology_plan = read_json(ontology_plan_path)
    ontology_trace = read_json(ontology_trace_path)
    if not isinstance(ontology_plan, Mapping) or not isinstance(
        ontology_trace, Mapping
    ):
        raise ValueError("XK4 ontology read plan/trace is not an object")
    ontology_trace_errors = validate_ontology_read_trace(
        ontology_trace,
        plan=ontology_plan,
        expected_run_id=str(contract.get("run_id")),
        expected_problem_contract_sha256=contract_hash(
            contract["problem_contract"]
        ),
        repository_root=Path(str(contract.get("repository_root"))),
    )
    if ontology_trace_errors:
        raise ValueError(
            "XK4 ontology read trace validation failed: "
            + "; ".join(ontology_trace_errors)
        )
    source_inputs = (
        base_request.get("source_inputs")
        if isinstance(base_request, Mapping)
        else None
    )
    base_provider = (
        source_inputs.get("base_provider_binding")
        if isinstance(source_inputs, Mapping)
        else None
    )
    if not isinstance(base_provider, Mapping):
        raise ValueError("XK1 base authoring request has no provider binding")
    request_ontology_plan = (
        source_inputs.get("ontology_read_plan")
        if isinstance(source_inputs, Mapping)
        else None
    )
    if (
        not isinstance(request_ontology_plan, Mapping)
        or request_ontology_plan.get("plan_sha256") != sha256_json(ontology_plan)
        or request_ontology_plan.get("record_count")
        != ontology_plan.get("record_count")
    ):
        raise ValueError("XK1 base authoring request ontology read plan differs")
    require_base_authoring_provider(
        base_provider,
        mode=str(contract.get("mode")),
        verify_executable=False,
    )
    if base_receipt.get("provider_binding_sha256") != sha256_json(
        dict(base_provider)
    ):
        raise ValueError("XK1 base authoring provider binding hash differs")
    if base_receipt.get("provider_executable_sha256") != base_provider.get(
        "executable_sha256"
    ):
        raise ValueError("XK1 base authoring provider executable differs")
    if base_receipt.get("provider_argv_sha256") != base_provider.get("argv_sha256"):
        raise ValueError("XK1 base authoring provider argv differs")
    expected_web_policy = (
        BASE_OPEN_WORLD_WEB_SEARCH
        if contract.get("mode") == "open-world"
        else BASE_CLOSED_INPUT_WEB_SEARCH
    )
    if base_provider.get("web_search") != expected_web_policy:
        raise ValueError("XK1 base authoring provider web policy differs from mode")
    if base_receipt.get("events_path") != "authoring/XK01-base-authoring-events.jsonl":
        raise ValueError("XK1 base authoring event path is invalid")
    if base_receipt.get("request_path") != "authoring/XK01-base-authoring-request.json":
        raise ValueError("XK1 base authoring request path is invalid")
    if base_receipt.get("stdout_sha256") != sha256_file(events_path):
        raise ValueError("XK1 base authoring event stream hash differs")
    if base_receipt.get("input_sha256") != sha256_file(request_path):
        raise ValueError("XK1 base authoring request hash differs")
    if base_receipt.get("input_byte_count") != len(request_bytes):
        raise ValueError("XK1 base authoring request byte count differs")
    if base_receipt.get("prompt_path") != "authoring/XK01-base-authoring-prompt.txt":
        raise ValueError("XK1 base authoring prompt path is invalid")
    if base_receipt.get("prompt_sha256") != sha256_file(prompt_path):
        raise ValueError("XK1 base authoring prompt hash differs")
    if base_receipt.get("prompt_byte_count") != len(prompt_bytes):
        raise ValueError("XK1 base authoring prompt byte count differs")
    if base_receipt.get("output_path") != "authoring/XK01-base-authoring-output.bin":
        raise ValueError("XK1 base authoring output path is invalid")
    if base_receipt.get("semantic_output_sha256") != sha256_bytes(output_bytes):
        raise ValueError("XK1 base authoring semantic output hash differs")
    if base_receipt.get("semantic_output_byte_count") != len(output_bytes):
        raise ValueError("XK1 base authoring semantic output byte count differs")
    if base_receipt.get("ontology_read_plan_sha256") != sha256_json(
        ontology_plan
    ):
        raise ValueError("XK1 base authoring ontology read plan hash differs")
    if base_receipt.get("ontology_problem_contract_sha256") != contract_hash(
        contract["problem_contract"]
    ):
        raise ValueError("XK1 base authoring ontology problem binding differs")
    if base_receipt.get("ontology_content_access_challenge_sha256") != sha256_text(
        str(ontology_plan.get("content_access_challenge"))
    ):
        raise ValueError("XK1 base authoring ontology challenge binding differs")
    if base_receipt.get("ontology_proof_kind") != "byte-access+problem-bound-semantic-trace":
        raise ValueError("XK1 base authoring ontology proof kind differs")
    try:
        from .execution import (
            _base_prompt,
            _parse_base_output,
            _project_retrieval,
            _rebind_visibility_ledger,
        )

        if prompt_bytes != _base_prompt(base_request):
            raise ValueError("XK1 base authoring prompt differs from its request")
        natural_request = base_request.get("natural_request")
        contract_natural_request = contract.get("natural_request")
        if natural_request is not None:
            if not isinstance(contract_natural_request, Mapping) or dict(
                natural_request
            ) != dict(contract_natural_request):
                raise ValueError(
                    "XK0 natural request differs between base request and run contract"
                )
        request_privacy = base_request.get("privacy_contract")
        contract_privacy = contract.get("privacy_contract")
        if not isinstance(request_privacy, Mapping) or not isinstance(
            contract_privacy, Mapping
        ) or dict(request_privacy) != dict(contract_privacy):
            raise ValueError("XK0 privacy contract differs between base request and run contract")
        privacy_purpose = request_privacy.get("purpose")
        if not isinstance(privacy_purpose, str) or not privacy_purpose:
            raise ValueError("XK0 privacy purpose is unavailable")
        raw_packet, raw_trace, raw_ontology_trace = _parse_base_output(
            output_bytes,
            problem_contract=contract["problem_contract"],
            mode=str(contract["mode"]),
            ontology_read_plan=ontology_plan,
            repository_root=Path(str(contract.get("repository_root"))),
            natural_request=(
                dict(natural_request)
                if isinstance(natural_request, Mapping)
                else None
            ),
        )
        validate_visibility_ledger(raw_packet, expected_purpose=privacy_purpose)
        raw_problem = raw_packet.get("problem_contract")
        if not isinstance(raw_problem, Mapping):
            raise ValueError("XK0 authoring packet has no problem contract")
        raw_frozen = {
            field: raw_problem.get(field)
            for field in contract["problem_contract"]
        }
        if raw_frozen != contract.get("problem_contract"):
            raise ValueError("XK0 natural authoring contract differs from run contract")
        if base_receipt.get("semantic_read_trace_sha256") != sha256_json(raw_trace):
            raise ValueError("XK1 base authoring trace hash differs from raw output")
        if base_receipt.get("ontology_read_trace_sha256") != sha256_json(
            raw_ontology_trace
        ):
            raise ValueError(
                "XK1 base authoring ontology trace hash differs from raw output"
            )
        if base_receipt.get("ontology_read_trace_byte_count") != len(
            canonical_bytes(raw_ontology_trace) + b"\n"
        ):
            raise ValueError(
                "XK1 base authoring ontology trace byte count differs"
            )
        expected_bound_ontology_trace = build_ontology_read_trace(
            raw_ontology_trace,
            plan=ontology_plan,
            run_id=str(contract["run_id"]),
            repository_root=Path(str(contract.get("repository_root"))),
            problem_contract_sha256=contract_hash(contract["problem_contract"]),
        )
        if dict(ontology_trace) != expected_bound_ontology_trace:
            raise ValueError(
                "XK4 ontology trace differs from raw base authoring output"
            )
        projected_packet, _projected_receipt, _semantic_input = _project_retrieval(
            raw_packet,
            event_stream=raw_events,
            receipt=base_receipt,
            request_bytes=request_bytes,
            run_id=str(contract["run_id"]),
            provider=base_provider,
            adapter_sha256=str(base_receipt["adapter_executable_sha256"]),
            child_pid=int(base_receipt["child_pid"]),
            started_at=str(base_receipt["started_at"]),
            completed_at=str(base_receipt["completed_at"]),
            evidence_cutoff=str(contract["evidence_cutoff"]),
            closed_input_materials=(
                source_inputs.get("closed_input_materials")
                if isinstance(source_inputs, Mapping)
                else None
            ),
            frozen_material_manifest=(
                source_inputs.get("frozen_material_manifest")
                if isinstance(source_inputs, Mapping)
                else None
            ),
            host_captures=(
                load_host_capture_bundle(
                    run_dir, run_id=str(contract["run_id"])
                )[1]
                if contract.get("mode") == "open-world"
                else None
            ),
        )
        projected_packet["schema_id"] = "xi-kari.v3.analysis-packet"
        projected_packet["schema_version"] = 3
        _rebind_visibility_ledger(
            projected_packet, privacy_purpose=privacy_purpose
        )
        if packet is not None:
            disk_projection = {
                key: value
                for key, value in packet.items()
                if key not in {"concept_disposition", "runtime_binding", "mode"}
            }
            if projected_packet != disk_projection:
                raise ValueError(
                    "runtime packet differs from raw base authoring projection"
                )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"XK1 base authoring replay failed: {exc}") from exc
    if base_receipt.get("receipt_sha256") != sha256_json(
        {key: value for key, value in base_receipt.items() if key != "receipt_sha256"}
    ):
        raise ValueError("XK1 base authoring receipt hash differs")
    semantic_document = read_json(retrieval_input_path)
    if not isinstance(semantic_document, Mapping):
        raise ValueError("XK2 semantic retrieval input is not an object")
    if (
        semantic_document.get("schema_id") != "xi-kari.v3.retrieval-semantic-input"
        or semantic_document.get("schema_version") != 1
        or semantic_document.get("run_id") != contract.get("run_id")
        or semantic_document.get("mode") != contract.get("mode")
    ):
        raise ValueError("XK2 semantic retrieval input binding is invalid")
    semantic_retrieval = {
        key: value
        for key, value in semantic_document.items()
        if key not in {"schema_id", "schema_version", "run_id"}
    }
    # The persisted semantic input carries the packet mode for contract
    # binding; retrieval_execution validates the mode-specific body itself.
    semantic_retrieval_body = dict(semantic_retrieval)
    semantic_retrieval_body.pop("mode", None)
    execution_receipt = read_json(retrieval_receipt_path)
    if not isinstance(execution_receipt, Mapping):
        raise ValueError("XK2 retrieval execution receipt is not an object")
    if contract.get("mode") == "closed-input":
        from .closed_input import validate_closed_input_execution

        closed_errors = validate_closed_input_execution(
            execution_receipt,
            retrieval,
            run_id=str(contract["run_id"]),
            evidence_cutoff=str(contract["evidence_cutoff"]),
            semantic_document=semantic_document,
            event_stream=raw_events,
            base_request=base_request,
            base_request_bytes=request_bytes,
            base_receipt=base_receipt,
        )
        if closed_errors:
            raise ValueError(
                "closed-input execution receipt validation failed: "
                + "; ".join(closed_errors)
            )
        if execution_receipt.get("provider_binding_sha256") != sha256_json(
            dict(base_provider)
        ):
            raise ValueError("closed-input provider binding differs from base request")
        return dict(execution_receipt), dict(semantic_retrieval)
    if execution_receipt.get("schema_id") != "xi-kari.v3.retrieval-execution-receipt":
        raise ValueError("open-world production retrieval requires a host execution receipt")
    from .retrieval_execution import validate_retrieval_execution_receipt

    replay_host_captures = load_host_capture_bundle(
        run_dir, run_id=str(contract["run_id"])
    )[1]
    errors = validate_retrieval_execution_receipt(
        execution_receipt,
        retrieval,
        run_id=str(contract["run_id"]),
        evidence_cutoff=str(contract["evidence_cutoff"]),
        semantic_retrieval=semantic_retrieval_body,
        event_stream=raw_events,
        adapter_input=request_bytes,
        host_captures=replay_host_captures,
    )
    if errors:
        raise ValueError("host retrieval receipt validation failed: " + "; ".join(errors))
    if execution_receipt.get("provider_binding_sha256") != sha256_json(
        dict(base_provider)
    ):
        raise ValueError("host retrieval receipt provider binding differs from base request")
    capability = contract.get("capability_snapshot", {})
    adapter = (
        capability.get("semantic_authoring_adapter", {})
        if isinstance(capability, Mapping)
        else {}
    )
    if execution_receipt.get("adapter_executable_sha256") != adapter.get("executable_sha256"):
        raise ValueError("host retrieval receipt adapter differs from XK0")
    if execution_receipt.get("child_pid") != base_receipt.get("child_pid"):
        raise ValueError("host retrieval receipt child process differs from base authoring")
    return dict(execution_receipt), dict(semantic_retrieval)


def _phase_paths(
    phase: str,
    *,
    contract_profile: str = PRODUCTION_CONTRACT_PROFILE,
    mode: str | None = None,
) -> list[str]:
    return list(
        expected_phase_artifact_paths(
            phase,
            contract_profile=contract_profile,
            mode=mode,
        )
    )


def _seal_values(
    run_dir: Path,
    *,
    run_id: str,
    phase: str,
    values: list[Any],
    packet_sha256: str,
) -> dict[str, Any]:
    contract = read_json(run_dir / "run-contract.json")
    contract_profile = (
        str(contract.get("contract_profile"))
        if isinstance(contract, Mapping)
        else ""
    )
    mode = str(contract.get("mode")) if isinstance(contract, Mapping) else None
    paths = _phase_paths(phase, contract_profile=contract_profile, mode=mode)
    if len(paths) != len(values):
        raise ValueError(f"{phase} value/path arity differs")
    records = load_phase_records(run_dir)
    index = PHASES.index(phase)
    if len(records) > index:
        return records[index]
    if len(records) != index:
        raise ValueError(f"cannot seal {phase}; phase chain is at {len(records)}")
    for path, value in zip(paths, values, strict=True):
        _write(run_dir, path, value)
    predecessor = records[-1] if records else None
    return append_phase(
        run_dir,
        run_id=run_id,
        phase=phase,
        artifact_path=paths,
        input_sha256=_phase_input(
            predecessor,
            {"packet_sha256": packet_sha256, "phase": phase, "values": values},
        ),
        created_at=utc_now(),
    )


def _runtime_document(value: Mapping[str, Any], *, kind: str, run_id: str) -> dict[str, Any]:
    document = dict(value)
    document["schema_id"] = f"xi-kari.v3.{kind}"
    document["schema_version"] = 3
    document["run_id"] = run_id
    return document


def _not_applicable_document(
    *, run_id: str, reason: str | None = None
) -> dict[str, Any]:
    document: dict[str, Any] = {
        "schema_id": "xi-kari.v3.not-applicable",
        "schema_version": 3,
        "run_id": run_id,
        "dynamic_applicability": "not_applicable",
        "status": "not_run",
    }
    if isinstance(reason, str) and reason.strip():
        document["reason"] = reason.strip()
    return document


def _delivery_bindings(run_dir: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for key, relative in DELIVERY_PATHS.items():
        path = run_dir / relative
        result[key] = {
            "path": relative,
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
    return result


def _write_xk12_transaction_state(
    run_dir: Path, transaction: Mapping[str, Any], state: str
) -> dict[str, Any]:
    updated = dict(transaction)
    updated["state"] = state
    updated["updated_at"] = utc_now()
    atomic_write_json(run_dir / TRANSACTION_RELATIVE, updated)
    return updated


def _begin_xk12_transaction(run_dir: Path, candidate: Path) -> dict[str, Any]:
    event_path = run_dir / "phase-events.jsonl"
    state_path = run_dir / "continuation/state.json"
    original_events = event_path.read_text(encoding="utf-8")
    original_state = state_path.read_text(encoding="utf-8")
    targets: list[dict[str, Any]] = []
    for relative in _phase_paths("XK12"):
        target = run_dir / relative
        before_exists = target.is_file()
        targets.append(
            {
                "path": relative,
                "before_exists": before_exists,
                "before_sha256": sha256_file(target) if before_exists else None,
                "before_text": (
                    target.read_text(encoding="utf-8") if before_exists else None
                ),
                "after_sha256": sha256_file(candidate / relative),
            }
        )
    created_at = utc_now()
    transaction = {
        "schema_id": "xi-kari.v3.xk12-transaction",
        "schema_version": 3,
        "run_id": read_json(run_dir / "run-contract.json")["run_id"],
        "transaction_id": f"XK12-TXN-{uuid.uuid4().hex}",
        "candidate_name": candidate.name,
        "original_phase_events": original_events,
        "original_phase_events_sha256": sha256_text(original_events),
        "original_state": original_state,
        "original_state_sha256": sha256_text(original_state),
        "targets": targets,
        "phase_events_after_sha256": sha256_file(candidate / "phase-events.jsonl"),
        "state": "promoting",
        "created_at": created_at,
        "updated_at": created_at,
    }
    atomic_write_json(run_dir / TRANSACTION_RELATIVE, transaction)
    return transaction


def _promote_xk12_candidate(
    run_dir: Path,
    candidate: Path,
    transaction: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if transaction is None:
        transaction = _begin_xk12_transaction(run_dir, candidate)
    for target_record in transaction["targets"]:
        relative = target_record["path"]
        atomic_write_text(
            run_dir / relative,
            (candidate / relative).read_text(encoding="utf-8"),
        )
    atomic_write_text(
        run_dir / "phase-events.jsonl",
        (candidate / "phase-events.jsonl").read_text(encoding="utf-8"),
    )
    records, errors = validate_phase_chain(run_dir)
    if errors or len(records) != len(PHASES):
        raise ValueError(f"promoted XK12 candidate is invalid: {errors}")
    return _write_xk12_transaction_state(run_dir, transaction, "promoted")


def _rollback_xk12_transaction(
    run_dir: Path, transaction: Mapping[str, Any]
) -> dict[str, Any]:
    if sha256_text(str(transaction.get("original_phase_events", ""))) != transaction.get(
        "original_phase_events_sha256"
    ):
        raise ValueError("XK12 transaction original phase chain is corrupt")
    if sha256_text(str(transaction.get("original_state", ""))) != transaction.get(
        "original_state_sha256"
    ):
        raise ValueError("XK12 transaction original continuation state is corrupt")
    for target_record in transaction.get("targets", []):
        target = run_dir / target_record["path"]
        if target.exists():
            observed = sha256_file(target)
            allowed = {target_record.get("after_sha256")}
            if target_record.get("before_exists"):
                allowed.add(target_record.get("before_sha256"))
            if observed not in allowed:
                raise ValueError(
                    "XK12 transaction target has bytes outside before/after authority: "
                    f"{target_record['path']}"
                )
        if target_record.get("before_exists"):
            atomic_write_text(target, target_record["before_text"])
        else:
            target.unlink(missing_ok=True)
    event_path = run_dir / "phase-events.jsonl"
    if event_path.is_file() and sha256_file(event_path) not in {
        transaction.get("original_phase_events_sha256"),
        transaction.get("phase_events_after_sha256"),
    }:
        raise ValueError("XK12 transaction phase chain has unknown bytes")
    atomic_write_text(event_path, transaction["original_phase_events"])
    atomic_write_text(
        run_dir / "continuation/state.json", transaction["original_state"]
    )
    for relative in (OFFICIAL_REPORT_RELATIVE, COMPLETION_RELATIVE):
        (run_dir / relative).unlink(missing_ok=True)
    return _write_xk12_transaction_state(run_dir, transaction, "rolled_back")


def _recover_xk12_transaction(run_dir: Path) -> None:
    transaction_path = run_dir / TRANSACTION_RELATIVE
    if not transaction_path.is_file():
        return
    transaction = read_json(transaction_path)
    if not isinstance(transaction, Mapping):
        raise ValueError("XK12 transaction is not an object")
    if transaction.get("state") == "rolled_back":
        return
    contract = read_json(run_dir / "run-contract.json")
    records, chain_errors = validate_phase_chain(run_dir)
    chain_head = records[-1].get("record_sha256") if records else None
    terminal_state, terminal_errors = validate_terminal_closure(
        run_dir,
        contract,
        phase_count=len(records),
        chain_head_sha256=chain_head,
        required=False,
    )
    if terminal_state is not None:
        return
    if (run_dir / TERMINAL_RELATIVE).exists() or terminal_errors:
        raise ValueError(
            "cannot recover XK12 transaction with invalid terminal authority: "
            f"{terminal_errors}"
        )
    candidate_name = transaction.get("candidate_name")
    if (
        not isinstance(candidate_name, str)
        or Path(candidate_name).name != candidate_name
        or not candidate_name.startswith(f".{run_dir.name}.xk12-")
    ):
        raise ValueError("XK12 transaction candidate path is invalid")
    _rollback_xk12_transaction(run_dir, transaction)
    candidate = run_dir.parent / candidate_name
    if candidate.exists():
        if candidate.is_symlink() or not candidate.is_dir():
            raise ValueError("XK12 transaction candidate is not a regular directory")
        shutil.rmtree(candidate)


def materialize_run(
    run_dir: Path,
    packet: Mapping[str, Any] | None = None,
    *,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    run_dir = _resolve_run_directory(run_dir)
    contract = read_json(run_dir / "run-contract.json")
    if not isinstance(contract, Mapping):
        raise ValueError("run contract is not an object")
    _require_mutable_contract_profile(contract)
    _recover_xk12_transaction(run_dir)
    contract = read_json(run_dir / "run-contract.json")
    records, errors = validate_phase_chain(run_dir)
    if errors:
        raise ValueError(f"invalid phase chain: {errors}")
    chain_head = records[-1].get("record_sha256") if records else None
    terminal_state, terminal_errors = validate_terminal_closure(
        run_dir,
        contract,
        phase_count=len(records),
        chain_head_sha256=chain_head,
        required=False,
    )
    if terminal_errors:
        raise ValueError(f"invalid terminal authority: {terminal_errors}")
    if terminal_state == "cancelled":
        raise ValueError("cannot materialize cancelled run")
    if terminal_state == "complete":
        return status_run(run_dir)
    lifecycle_errors = validate_lifecycle_sidecars(
        run_dir, contract, phase_count=len(records)
    )
    if lifecycle_errors:
        raise ValueError(f"invalid lifecycle state: {lifecycle_errors}")
    control_errors = validate_runtime_control_bindings(
        run_dir, contract, verify_external_bindings=True
    )
    if control_errors:
        raise ValueError(f"invalid runtime control binding: {control_errors}")
    if (run_dir / "continuation" / "cancel.json").is_file():
        raise ValueError("cannot materialize cancelled run")
    if len(records) < 2:
        raise ValueError("run must be prepared through XK1")
    if len(records) == len(PHASES):
        return status_run(run_dir)

    repo = _bound_repository_root(run_dir, repository_root)
    source_lock = read_json(run_dir / "source-lock.json")
    read_plan = read_json(run_dir / "authoring/XK01-read-plan.json")
    persisted = _load_packet_from_disk(
        run_dir,
        packet,
        contract=contract,
        repository_root=repo,
    )
    repair_binding_errors = validate_repair_packet_binding(run_dir, contract)
    if repair_binding_errors:
        raise ValueError(f"invalid repair packet binding: {repair_binding_errors}")
    packet_path = run_dir / "continuation" / "input-packet.json"
    mode = contract["mode"]
    try:
        require_packet_contract(persisted, mode=mode, run_contract=contract)
    except ValueError as exc:
        raise ValueError(f"provenance or packet contract failed: {exc}") from exc
    packet_sha256 = sha256_file(packet_path)
    pre_evidence_packet = dict(persisted)
    deferred_alias_validation = False
    if persisted["dynamic_applicability"] == "applicable":
        (
            pre_evidence_packet["local_world_model"],
            deferred_alias_validation,
        ) = _pre_evidence_world_projection(
            persisted["local_world_model"],
        )
    try:
        _semantic_validate(pre_evidence_packet, repo=repo, evidence_mode=mode)
    except ValueError as exc:
        if not (
            deferred_alias_validation
            and str(exc)
            in {
                "transformation transition pairs an event with the wrong StateDiff",
                "cascade hop does not bind the exact Omega StateDiff",
            }
        ):
            raise
    _require_stable_repository_authority(
        repo, contract, boundary="semantic validation"
    )
    applicability = persisted["dynamic_applicability"]
    run_id = contract["run_id"]
    _set_state(run_dir, "in_progress", next_phase=PHASES[len(records)])

    retrieval = persisted["retrieval"]
    host_execution_receipt: dict[str, Any] | None = None
    semantic_retrieval_input: dict[str, Any] | None = None
    if contract.get("contract_profile") == PRODUCTION_CONTRACT_PROFILE:
        host_execution_receipt, semantic_retrieval_input = (
                _validate_base_authoring_and_retrieval(
                    run_dir,
                    contract=contract,
                    retrieval=retrieval,
                    packet=persisted,
                )
        )
    if len(load_phase_records(run_dir)) <= PHASES.index("XK2"):
        retrieval_index = materialize_retrieval_bundle(
            run_dir,
            list(retrieval.get("sources", [])),
            list(retrieval.get("assessments", [])),
            mode=mode,
            run_id=run_id,
            evidence_cutoff=contract["evidence_cutoff"],
        )
        retrieval_artifact = {
            **retrieval,
            "schema_id": "xi-kari.v3.retrieval-ledger",
            "schema_version": 3,
            "run_id": run_id,
            "input_packet_sha256": packet_sha256,
            "source_count": retrieval_index["source_count"],
            "all_sources_assessed": True,
        }
        if host_execution_receipt is not None:
            retrieval_artifact["execution_receipt_sha256"] = sha256_json(
                host_execution_receipt
            )
            retrieval_artifact["host_event_stream_sha256"] = host_execution_receipt.get(
                "event_stream_sha256",
                host_execution_receipt.get("stdout_sha256"),
            )
        retrieval_phase_values = [retrieval_artifact, retrieval_index]
        if contract.get("contract_profile") == PRODUCTION_CONTRACT_PROFILE:
            retrieval_phase_values.extend(
                [
                    read_json(run_dir / "authoring/XK02-semantic-retrieval.json"),
                    host_execution_receipt,
                    *(
                        [read_json(run_dir / HOST_CAPTURE_INDEX_RELATIVE)]
                        if mode == "open-world"
                        else []
                    ),
                ]
            )
        _seal_values(
            run_dir,
            run_id=run_id,
            phase="XK2",
            values=retrieval_phase_values,
            packet_sha256=packet_sha256,
        )
    else:
        retrieval_index = read_json(run_dir / "retrieval" / "index.json")
        retrieval_artifact = read_json(run_dir / "authoring" / "XK02-retrieval-ledger.json")
        if retrieval_artifact.get("input_packet_sha256") != packet_sha256:
            raise ValueError("input packet hash differs from sealed XK2")

    evidence = persisted["evidence"]
    if "claims" in evidence and "support_edges" not in evidence:
        raw_claims = [dict(claim) for claim in evidence["claims"]]
        if applicability != "applicable":
            for claim in raw_claims:
                claim["world_targets"] = []
        evidence = build_evidence_ledger(
            run_id=run_id,
            claims=raw_claims,
            retrieval_index=retrieval_index,
            world_target_hashes=(
                world_evidence_target_hashes(persisted["local_world_model"])
                if applicability == "applicable"
                else None
            ),
        )
    evidence_errors = validate_evidence_ledger(evidence, retrieval_index)
    if evidence_errors:
        raise ValueError(f"evidence validation failed: {evidence_errors}")
    validate_packet_references(
        persisted,
        evidence_ledger=evidence,
        retrieval_index=retrieval_index,
        repository_root=repo,
    )
    bound_world: dict[str, Any] | None = None
    if applicability == "applicable":
        bound_world = bind_world_evidence_state(
            persisted["local_world_model"],
            evidence_ledger=evidence,
            run_id=run_id,
            repository_root=repo,
        )
        semantic_packet = dict(persisted)
        semantic_packet["local_world_model"] = bound_world
        _semantic_validate(semantic_packet, repo=repo, evidence_mode=mode)
        _require_stable_repository_authority(
            repo, contract, boundary="semantic validation"
        )
    unknown_register = {
        "schema_id": "xi-kari.v3.unknown-register",
        "schema_version": 3,
        "run_id": run_id,
        "evidence_cutoff": contract["evidence_cutoff"],
        "unknowns": list(persisted.get("facts", {}).get("unknown", [])),
        "unsupported_claim_ids": list(evidence.get("unsupported_claims", [])),
        "frozen": True,
    }
    _seal_values(
        run_dir,
        run_id=run_id,
        phase="XK3",
        values=[evidence, unknown_register],
        packet_sha256=packet_sha256,
    )

    concept = _concept_closure(repo, persisted)
    production_profile = (
        contract.get("contract_profile") == PRODUCTION_CONTRACT_PROFILE
    )
    ontology_read_plan = None
    ontology_read_trace = None
    if production_profile:
        ontology_read_plan = read_json(
            run_dir / "authoring/XK04-ontology-read-plan.json"
        )
        ontology_read_trace = read_json(
            run_dir / "authoring/XK04-ontology-read-trace.json"
        )
        if not isinstance(ontology_read_plan, Mapping) or not isinstance(
            ontology_read_trace, Mapping
        ):
            raise ValueError("production ontology read plan/trace is unavailable")
    closure_report = _concept_closure_report(
        repo,
        run_id=run_id,
        concept=concept,
        problem_contract_sha256=contract_hash(contract["problem_contract"]),
        ontology_read_plan=ontology_read_plan,
        ontology_read_trace=ontology_read_trace,
        require_ontology_trace=production_profile,
    )
    if closure_report.get("complete") is not True:
        raise ValueError("XK4 concept closure is incomplete")
    _require_stable_repository_authority(
        repo, contract, boundary="concept closure"
    )
    _seal_values(
        run_dir,
        run_id=run_id,
        phase="XK4",
        values=[
            concept,
            closure_report,
            *(
                [ontology_read_plan, ontology_read_trace]
                if production_profile
                else []
            ),
        ],
        packet_sha256=packet_sha256,
    )
    not_applicable = _not_applicable_document(
        run_id=run_id, reason=persisted.get("not_applicable_reason")
    )
    world = (
        bound_world
        if applicability == "applicable"
        else not_applicable
    )
    _seal_values(run_dir, run_id=run_id, phase="XK5", values=[world], packet_sha256=packet_sha256)
    transform = (
        persisted["transformation_ledger"]
        if applicability == "applicable"
        else not_applicable
    )
    cascade = (
        persisted["cascade"] if applicability == "applicable" else not_applicable
    )
    _seal_values(
        run_dir,
        run_id=run_id,
        phase="XK6",
        values=[transform, cascade],
        packet_sha256=packet_sha256,
    )
    graph = (
        persisted["claim_mechanism_graph"]
        if applicability == "applicable"
        else not_applicable
    )
    case_ledger = _runtime_document(persisted["case_ledger"], kind="case-ledger", run_id=run_id)
    _seal_values(
        run_dir,
        run_id=run_id,
        phase="XK7",
        values=[graph, case_ledger],
        packet_sha256=packet_sha256,
    )
    lineage = (
        persisted["recursive_lineage"]
        if applicability == "applicable"
        else not_applicable
    )
    records = load_phase_records(run_dir)
    xk8_index = PHASES.index("XK8")
    if len(records) == xk8_index:
        state_dir = run_dir / "authoring" / "recursive-state"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_paths: list[str] = []
        recursive_states = (
            persisted["recursive_states"] if applicability == "applicable" else {}
        )
        if applicability == "applicable" and not isinstance(recursive_states, Mapping):
            raise ValueError("recursive_states must be a mapping")
        for index, (state_id, state) in enumerate(sorted(recursive_states.items()), start=1):
            safe_id = _safe_run_id(str(state_id))
            if not isinstance(state, Mapping) or state.get("state_id") != state_id:
                raise ValueError(f"recursive state identity mismatch: {state_id}")
            relative = f"authoring/recursive-state/{index:04d}-{safe_id}.json"
            _write(run_dir, relative, state)
            state_paths.append(relative)
        _write(run_dir, "authoring/XK08-recursive-lineage.json", lineage)
        append_phase(
            run_dir,
            run_id=run_id,
            phase="XK8",
            artifact_path=["authoring/XK08-recursive-lineage.json", *state_paths],
            input_sha256=_phase_input(
                records[-1],
                {
                    "packet_sha256": packet_sha256,
                    "phase": "XK8",
                    "lineage": lineage,
                    "recursive_states": recursive_states,
                },
            ),
            created_at=utc_now(),
        )
    elif len(records) < xk8_index:
        raise ValueError(f"cannot seal XK8; phase chain is at {len(records)}")
    static_phase = {
        "dynamic_applicability": "not_applicable",
        "status": "not_run",
    }
    evaluation = (
        persisted["order_evaluation"]
        if applicability == "applicable"
        else static_phase
    )
    red_team = (
        persisted["red_team"] if applicability == "applicable" else static_phase
    )
    stance = (
        persisted["stance_pair"] if applicability == "applicable" else static_phase
    )
    evaluation = _runtime_document(evaluation, kind="order-evaluation", run_id=run_id)
    red_team = _runtime_document(red_team, kind="red-team-report", run_id=run_id)
    stance = _runtime_document(stance, kind="stance-pair", run_id=run_id)
    authoring_bundle_path = run_dir / "authoring/XK09-semantic-authoring-bundle.json"
    if applicability == "applicable":
        records = load_phase_records(run_dir)
        if len(records) == PHASES.index("XK9"):
            authoring_bundle = author_semantic_probe_variants(
                persisted,
                contract,
                source_lock=source_lock,
                read_plan=read_plan,
                input_packet_sha256=packet_sha256,
            )
            atomic_write_json(authoring_bundle_path, authoring_bundle)
        else:
            authoring_bundle = read_json(authoring_bundle_path)
        validate_semantic_probe_authorings(
            authoring_bundle,
            persisted,
            contract,
            source_lock=source_lock,
            read_plan=read_plan,
            input_packet_sha256=packet_sha256,
            verify_executable=False,
        )
        stance_stability = build_stance_stability_report(
            packet_path=packet_path,
            authoring_bundle_path=authoring_bundle_path,
            run_contract_path=run_dir / "run-contract.json",
            source_lock_path=run_dir / "source-lock.json",
            read_plan_path=run_dir / "authoring/XK01-read-plan.json",
            repository_root=repo,
        )
        sensitivity = build_sensitivity_report(
            packet_path=packet_path,
            authoring_bundle_path=authoring_bundle_path,
            run_contract_path=run_dir / "run-contract.json",
            source_lock_path=run_dir / "source-lock.json",
            read_plan_path=run_dir / "authoring/XK01-read-plan.json",
            repository_root=repo,
            baseline_projection_sha256=stance_stability[
                "invariant_projection_sha256"
            ],
        )
    else:
        authoring_bundle = not_applicable
        stance_stability = not_applicable
        sensitivity = not_applicable
    _seal_values(
        run_dir,
        run_id=run_id,
        phase="XK9",
        values=[
            authoring_bundle,
            evaluation,
            red_team,
            stance,
            sensitivity,
            stance_stability,
        ],
        packet_sha256=packet_sha256,
    )
    verdict = persisted["verdict"] if applicability == "applicable" else not_applicable
    actions = (
        persisted["action_ranking"] if applicability == "applicable" else not_applicable
    )
    forecast = persisted["forecast"] if applicability == "applicable" else static_phase
    forecast = _runtime_document(forecast, kind="forecast-ledger", run_id=run_id)
    framework_gap = (
        (
            persisted["framework_gap"]
            if persisted.get("framework_gap") is not None
            else empty_framework_gap_ledger()
        )
        if applicability == "applicable"
        else not_applicable
    )
    _seal_values(
        run_dir,
        run_id=run_id,
        phase="XK10",
        values=[verdict, actions, forecast, framework_gap],
        packet_sha256=packet_sha256,
    )

    if len(load_phase_records(run_dir)) <= PHASES.index("XK11"):
        payload = dict(persisted)
        if applicability == "not_applicable":
            for field in DYNAMIC_PHASE_FIELDS:
                payload.pop(field, None)
        payload["question"] = contract["question"]
        payload["sources"] = list(retrieval.get("sources", []))
        payload["assessments"] = list(retrieval.get("assessments", []))
        coverage = build_coverage(
            run_id=run_id,
            source_lock=read_json(run_dir / "source-lock.json"),
            retrieval_index=retrieval_index,
            evidence_ledger=evidence,
        )
        prose_plan = build_prose_plan(run_id=run_id, payload=payload, coverage=coverage)
        outputs = assemble_outputs(run_dir / "delivery", payload)
        for old, new in (
            ("answer.md", "xi-kari-answer.md"),
            ("dossier.md", "xi-kari-dossier.md"),
            ("atlas.md", "xi-kari-concept-atlas.md"),
            ("casebook.md", "xi-kari-case-and-countercase.md"),
        ):
            old_path = run_dir / "delivery" / old
            if old_path.exists():
                old_path.replace(run_dir / "delivery" / new)
        runtime_binding = persisted.get("runtime_binding", {})
        atomic_write_text(
            run_dir / "delivery" / "artifact-index.md",
            render_artifact_index(
                run_dir,
                contract_profile=str(contract["contract_profile"]),
                authoring_profile=str(
                    runtime_binding.get("semantic_authoring_profile")
                ),
            ),
        )
        prose_plan["coverage"] = coverage
        prose_plan["input_packet_sha256"] = packet_sha256
        semantic_coverage = build_semantic_coverage(
            run_id=run_id,
            packet=dict(persisted),
            source_read_complete=(
                coverage.get("source_read", {}).get("complete") is True
            ),
            candidate_closure_complete=closure_report["complete"],
            reader_outputs=load_reader_outputs(run_dir),
        )
        prose_errors: list[str] = []
        for relative in (
            "delivery/xi-kari-answer.md",
            "delivery/xi-kari-dossier.md",
            "delivery/xi-kari-concept-atlas.md",
            "delivery/xi-kari-case-and-countercase.md",
        ):
            prose_errors.extend(
                f"{relative}: {error}"
                for error in check_plain_language((run_dir / relative).read_text(encoding="utf-8"))
            )
        prose_review = {
            "schema_id": "xi-kari.v3.prose-review",
            "schema_version": 3,
            "run_id": run_id,
            "check_method": "deterministic-plain-language-rules",
            "independent_reviewer": False,
            "required_reader_beats": prose_plan["reader_beats"],
            "errors": prose_errors,
            "valid": not prose_errors and semantic_coverage["reader_projection_complete"],
        }
        _write(run_dir, "authoring/XK11-output-plan.json", prose_plan)
        _write(run_dir, "authoring/XK11-semantic-coverage.json", semantic_coverage)
        _write(run_dir, "authoring/XK11-prose-review.json", prose_review)
        current_records = load_phase_records(run_dir)
        append_phase(
            run_dir,
            run_id=run_id,
            phase="XK11",
            artifact_path=_phase_paths("XK11"),
            input_sha256=_phase_input(
                current_records[-1],
                {"packet_sha256": packet_sha256, "phase": "XK11", "prose_plan": prose_plan},
            ),
            created_at=utc_now(),
        )
    records = load_phase_records(run_dir)
    if len(records) <= PHASES.index("XK12"):
        _require_stable_repository_authority(
            repo, contract, boundary="fresh preseal validation"
        )
        preseal = run_fresh_validator(
            run_dir,
            repository_root=repo,
            preseal=True,
        )
        if not preseal["valid"]:
            _set_state(run_dir, "needs_attention", next_phase="XK12")
            raise ValueError(f"pre-seal validation failed: {preseal['errors']}")
        _require_stable_repository_authority(
            repo, contract, boundary="XK12 sealing"
        )
        candidate = run_dir.parent / f".{run_dir.name}.xk12-{uuid.uuid4().hex}"
        transaction: dict[str, Any] | None = None
        try:
            shutil.copytree(run_dir, candidate, symlinks=True)
            (candidate / KEY_RELATIVE).unlink(missing_ok=True)
            final_chat = {
                "schema_id": "xi-kari.v3.final-chat",
                "schema_version": 3,
                "run_id": run_id,
                "answer_path": "delivery/xi-kari-answer.md",
                "validation_authority_path": COMPLETION_RELATIVE,
            }
            atomic_write_json(candidate / "delivery" / "final-chat.json", final_chat)
            output_bindings = _delivery_bindings(candidate)
            phase_records = load_phase_records(candidate)
            continuation_bindings = {}
            for relative in (
                "continuation/parent.json",
                "continuation/repair-record.json",
            ):
                path = candidate / relative
                if path.is_file():
                    continuation_bindings[relative] = sha256_file(path)
            manifest = {
                "schema_id": "xi-kari.v3.artifact-manifest",
                "schema_version": 3,
                "runtime_version": RUNTIME_VERSION,
                "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
                "run_id": run_id,
                "input_packet_sha256": packet_sha256,
                "candidate_census_sha256": concept["candidate_census_sha256"],
                "validated_chain_head_sha256": phase_records[-1]["record_sha256"],
                "validator_set_sha256": preseal["validator_set_sha256"],
                "phase_responsibilities": PHASE_RESPONSIBILITIES,
                "phase_artifacts": build_phase_artifact_bindings(
                    candidate, phase_records
                ),
                "delivery": output_bindings,
                "continuation_bindings": continuation_bindings,
            }
            _seal_values(
                candidate,
                run_id=run_id,
                phase="XK12",
                values=[preseal, final_chat, manifest],
                packet_sha256=packet_sha256,
            )
            _set_state(candidate, "in_progress", next_phase="XK12")
            final_report = run_fresh_validator(
                candidate,
                repository_root=repo,
                preseal=False,
                promotion=True,
            )
            if not final_report["valid"]:
                raise ValueError(f"final validation failed: {final_report['errors']}")
            _require_stable_repository_authority(
                repo, contract, boundary="final validation"
            )
            transaction = _promote_xk12_candidate(run_dir, candidate)
            _set_state(run_dir, "in_progress", next_phase="XK12")
            official_report = run_fresh_validator(
                run_dir,
                repository_root=repo,
                preseal=False,
                official=True,
            )
            if not official_report["valid"]:
                raise ValueError(
                    "official run validation failed: "
                    f"{official_report['errors']}"
                )
            _require_stable_repository_authority(
                repo, contract, boundary="official run validation"
            )
            atomic_write_json(run_dir / OFFICIAL_REPORT_RELATIVE, official_report)
            transaction = _write_xk12_transaction_state(
                run_dir, transaction, "official_validated"
            )
            shutil.rmtree(candidate)
            _set_state(run_dir, "complete", next_phase=None)
            records = load_phase_records(run_dir)
            chain_head_sha256 = records[-1]["record_sha256"]
            completion = {
                "schema_id": "xi-kari.v3.completion",
                "schema_version": 3,
                "run_id": run_id,
                "official_validation_path": OFFICIAL_REPORT_RELATIVE,
                "official_validation_sha256": sha256_file(
                    run_dir / OFFICIAL_REPORT_RELATIVE
                ),
                "chain_head_sha256": chain_head_sha256,
                "phase_count": len(records),
                "validator_set_sha256": contract["validator_set_sha256"],
                "manifest_sha256": sha256_file(
                    run_dir / "artifacts/artifact-manifest.json"
                ),
                "final_chat_sha256": sha256_file(
                    run_dir / "delivery/final-chat.json"
                ),
                "xk12_transaction_sha256": sha256_file(
                    run_dir / TRANSACTION_RELATIVE
                ),
                "completed_at": utc_now(),
            }
            atomic_write_json(run_dir / COMPLETION_RELATIVE, completion)
            commit_terminal_record(
                run_dir,
                contract,
                {
                    "run_id": run_id,
                    "terminal_state": "complete",
                    "terminal_at": utc_now(),
                    "phase_count": len(records),
                    "chain_head_sha256": chain_head_sha256,
                    "completion_sha256": sha256_file(
                        run_dir / COMPLETION_RELATIVE
                    ),
                },
            )
            terminal_report = run_fresh_validator(
                run_dir,
                repository_root=repo,
                preseal=False,
            )
            if not terminal_report["valid"] or not terminal_report["complete"]:
                raise ValueError(
                    "terminal validation failed: "
                    f"{terminal_report['errors']}"
                )
        except Exception as failure:
            compensation_errors: list[str] = []
            if transaction is None and (run_dir / TRANSACTION_RELATIVE).is_file():
                value = read_json(run_dir / TRANSACTION_RELATIVE)
                if isinstance(value, Mapping):
                    transaction = dict(value)
            if transaction is not None and not (run_dir / TERMINAL_RELATIVE).exists():
                try:
                    _rollback_xk12_transaction(run_dir, transaction)
                except Exception as exc:
                    compensation_errors.append(f"rollback helper: {exc}")
            if not (run_dir / TERMINAL_RELATIVE).exists():
                try:
                    _set_state(run_dir, "needs_attention", next_phase="XK12")
                except Exception as exc:
                    compensation_errors.append(
                        f"continuation state downgrade: {exc}"
                    )
            try:
                if candidate.exists():
                    shutil.rmtree(candidate)
            except Exception as exc:
                compensation_errors.append(f"candidate cleanup: {exc}")
            if transaction is not None and not (run_dir / TERMINAL_RELATIVE).exists():
                lingering = [
                    relative
                    for relative in _phase_paths("XK12")
                    if (run_dir / relative).exists()
                ]
                if lingering:
                    compensation_errors.append(
                        "official XK12 declarations remain: " + ", ".join(lingering)
                    )
            if compensation_errors:
                failure.add_note(
                    "XK12 compensation errors: " + "; ".join(compensation_errors)
                )
            raise
    return status_run(run_dir)


def status_run(run_dir: Path) -> dict[str, Any]:
    run_dir = _resolve_run_directory(run_dir)
    request = read_json(run_dir / "run-contract.json")
    _require_mutable_contract_profile(request)
    records, errors = validate_phase_chain(run_dir)
    status = _status_from_records(run_dir, records, request)
    chain_head = records[-1].get("record_sha256") if records else None
    terminal_required = len(records) == len(PHASES)
    terminal_state, terminal_errors = validate_terminal_closure(
        run_dir,
        request,
        phase_count=len(records),
        chain_head_sha256=chain_head,
        required=terminal_required,
    )
    lifecycle_errors = (
        []
        if terminal_state is not None
        else validate_lifecycle_sidecars(
            run_dir, request, phase_count=len(records)
        )
    )
    if terminal_state is not None:
        status["state"] = terminal_state
        status["next_phase"] = None
    elif terminal_errors:
        if (run_dir / TERMINAL_RELATIVE).exists():
            errors.extend(terminal_errors)
        else:
            status["state"] = "needs_attention"
            status["attention_errors"] = terminal_errors
    if status["state"] == "needs_attention":
        attention_errors = [
            error
            for error in lifecycle_errors
            if error
            in {
                COMPLETE_STATE_MISMATCH_ERROR,
                PREMATURE_COMPLETE_STATE_ERROR,
            }
        ]
        lifecycle_errors = [
            error
            for error in lifecycle_errors
            if error
            not in {
                COMPLETE_STATE_MISMATCH_ERROR,
                PREMATURE_COMPLETE_STATE_ERROR,
            }
        ]
        if attention_errors:
            status["attention_errors"] = attention_errors
    errors.extend(lifecycle_errors)
    errors.extend(
        validate_runtime_control_bindings(
            run_dir,
            request,
            verify_external_bindings=terminal_state != "complete",
        )
    )
    if errors:
        status["state"] = "invalid"
        status["integrity_errors"] = errors
    return status


def resume_run(run_dir: Path, packet: Mapping[str, Any] | None = None, *, repository_root: Path | None = None) -> dict[str, Any]:
    resolved_run = _resolve_run_directory(run_dir)
    contract = read_json(resolved_run / "run-contract.json")
    if not isinstance(contract, Mapping):
        raise ValueError("run contract is not an object")
    _require_mutable_contract_profile(contract)
    _recover_xk12_transaction(resolved_run)
    status = status_run(resolved_run)
    if status["state"] in {"invalid", "cancelled"}:
        raise ValueError(f"cannot resume {status['state']} run")
    if status["state"] == "complete":
        return status
    if status.get("attention_errors") == [COMPLETE_STATE_MISMATCH_ERROR]:
        contract = read_json(resolved_run / "run-contract.json")
        repo = _bound_repository_root(resolved_run, repository_root)
        if packet is not None:
            _load_packet_from_disk(
                resolved_run,
                packet,
                contract=contract,
                repository_root=repo,
            )
        report = run_fresh_validator(
            resolved_run,
            repository_root=repo,
            preseal=False,
            promotion=True,
        )
        if not report["valid"]:
            _set_state(resolved_run, "needs_attention", next_phase="XK12")
            raise ValueError(
                "pending XK12 promotion validation failed: "
                f"{report['errors']}"
            )
        _require_stable_repository_authority(
            repo, contract, boundary="resumed official run validation"
        )
        for candidate in sorted(
            resolved_run.parent.glob(f".{resolved_run.name}.xk12-*")
        ):
            if candidate.is_symlink() or not candidate.is_dir():
                raise ValueError(f"invalid pending XK12 candidate path: {candidate}")
            shutil.rmtree(candidate)
        _set_state(resolved_run, "complete", next_phase=None)
        return status_run(resolved_run)
    if status.get("attention_errors") == [PREMATURE_COMPLETE_STATE_ERROR]:
        recovered_state = "prepared" if status["phase_count"] <= 2 else "in_progress"
        _set_state(
            _resolve_run_directory(run_dir),
            recovered_state,
            next_phase=status["next_phase"],
        )
    return materialize_run(resolved_run, packet, repository_root=repository_root)


def fork_run(
    run_dir: Path,
    *,
    runs_root: Path | None = None,
    run_id: str | None = None,
    base_phase: str | None = None,
    repository_root: Path | None = None,
    continuation_kind: str = "fork",
    semantic_read_trace_path: str | Path | None = None,
) -> Path:
    parent = _resolve_run_directory(run_dir)
    contract = read_json(parent / "run-contract.json")
    if not isinstance(contract, Mapping):
        raise ValueError("run contract is not an object")
    _require_mutable_contract_profile(contract)
    parent_status = status_run(parent)
    if parent_status["state"] == "cancelled":
        raise ValueError("cancelled run is terminal and cannot be forked")
    child_runs_root = _resolve_run_directory(runs_root or parent.parent)
    if (
        child_runs_root != parent.parent
        and child_runs_root.parent != parent.parent.parent
    ):
        raise ValueError("child run root must remain in the parent lineage family")
    parent_adapter = contract.get("capability_snapshot", {}).get(
        "semantic_authoring_adapter"
    )
    parent_authoring_profile = (
        parent_adapter.get("profile", "")
        if isinstance(parent_adapter, Mapping)
        else ""
    )
    parent_provider = (
        parent_adapter.get("provider_binding")
        if isinstance(parent_adapter, Mapping)
        else None
    )
    if isinstance(parent_adapter, Mapping):
        try:
            require_semantic_authoring_adapter(
                parent_adapter,
                verify_executable=True,
            )
        except ValueError as exc:
            raise ValueError(
                f"parent runtime control binding is invalid: {exc}"
            ) from exc
    if parent_status["state"] == "invalid" and continuation_kind != "repair":
        raise ValueError(
            "cannot fork invalid run; production base authoring or closed-input "
            "evidence is invalid: "
            f"{parent_status.get('integrity_errors', [])}"
        )
    contract_profile = str(
        contract.get("contract_profile", "")
    )
    if contract_profile == PRODUCTION_CONTRACT_PROFILE:
        # A production continuation is a new base-authoring execution.  A
        # caller-supplied semantic trace can never stand in for the provider's
        # fresh request, prompt, output and event stream.
        if continuation_kind not in {"fork", "repair"}:
            raise ValueError("production continuation kind is invalid")
        if semantic_read_trace_path is not None:
            raise ValueError(
                "production continuation owns a fresh semantic read trace"
            )
        if not isinstance(parent_adapter, Mapping):
            raise ValueError(
                "production continuation requires the parent authoring adapter"
            )
        if parent_authoring_profile != FORMAL_ADAPTER_PROFILE:
            raise ValueError(
                "production continuation requires the production-codex profile"
            )
        if not isinstance(parent_provider, Mapping) or not isinstance(
            parent_provider.get("executable_path"), str
        ):
            raise ValueError(
                "production continuation requires the parent provider binding"
            )
        closed_input_materials = (
            load_runtime_bound_closed_input_materials(parent, contract)
            if contract.get("mode") == "closed-input"
            else None
        )
        child_id = _safe_run_id(run_id or _new_run_id())
        if child_id == contract.get("run_id"):
            raise ValueError("continuation run_id must differ from the parent")
        child_path = child_runs_root / child_id
        if child_path.exists():
            raise FileExistsError(f"run directory already exists: {child_path}")
        try:
            from .execution import execute_authored_run

            bound_repo = _bound_repository_root(parent, repository_root)
            execution_result = execute_authored_run(
                child_runs_root,
                problem_contract=contract["problem_contract"],
                mode=str(contract["mode"]),
                run_id=child_id,
                repository_root=bound_repo,
                codex_provider_executable=parent_provider["executable_path"],
                closed_input_materials=closed_input_materials,
                timeout_seconds=min(
                    int(parent_provider.get("timeout_seconds", DEFAULT_ADAPTER_TIMEOUT_SECONDS)), MAX_AUTHORING_TIMEOUT_SECONDS
                ),
                privacy_purpose=contract.get("privacy_contract", {}).get(
                    "purpose", DEFAULT_PRIVACY_PURPOSE
                ),
                delivery_audience=contract.get("privacy_contract", {}).get(
                    "delivery_audience", DEFAULT_DELIVERY_AUDIENCE
                ),
                _continuation_kind=continuation_kind,
                _parent_run_id=str(contract["run_id"]),
                _parent_chain_head_sha256=parent_status.get(
                    "chain_head_sha256"
                ),
                _generation=int(
                    contract.get("continuation", {}).get("generation", 0)
                )
                + 1,
                _natural_request=(
                    contract.get("natural_request")
                    if isinstance(contract.get("natural_request"), Mapping)
                    else None
                ),
                _prepare_only=True,
            )
        except Exception:
            # The continuation path is runtime-owned.  If a late staging
            # error occurs, do not leave a prepared-looking child behind.
            if child_path.is_dir() and not child_path.is_symlink():
                shutil.rmtree(child_path)
            raise
        if execution_result.get("run_id") != child_id:
            raise ValueError(
                "fresh production continuation returned a different run_id"
            )
        child = Path(str(execution_result["run_dir"])).resolve()
        child_contract = read_json(child / "run-contract.json")
        child_adapter = (
            child_contract.get("capability_snapshot", {}).get(
                "semantic_authoring_adapter"
            )
            if isinstance(child_contract, Mapping)
            else None
        )
        if child_adapter != parent_adapter:
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            raise ValueError(
                "child runtime control binding differs from parent runtime control binding"
            )
        _write(
            child,
            "continuation/parent.json",
            {
                "schema_id": "xi-kari.v3.parent-binding",
                "schema_version": 3,
                "run_id": status_run(child)["run_id"],
                "parent_run_id": contract["run_id"],
                "parent_chain_head_sha256": parent_status.get(
                    "chain_head_sha256"
                ),
                "base_phase": base_phase or parent_status.get("current_phase"),
            },
        )
        return child
    raise ValueError("continuation requires the current production contract profile")


def cancel_run(run_dir: Path, *, reason: str) -> dict[str, Any]:
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("cancel requires a reason")
    run_dir = _resolve_run_directory(run_dir)
    contract = read_json(run_dir / "run-contract.json")
    if not isinstance(contract, Mapping):
        raise ValueError("run contract is not an object")
    _require_mutable_contract_profile(contract)
    status = status_run(run_dir)
    if status["state"] == "complete":
        raise ValueError("complete run is immutable")
    if status["state"] == "cancelled":
        return status
    if status["state"] == "invalid":
        raise ValueError("cannot cancel invalid run")
    records = load_phase_records(run_dir)
    chain_head = records[-1].get("record_sha256") if records else None
    cancelled_at = utc_now()
    _write(
        run_dir,
        "continuation/cancel.json",
        {
            "schema_id": "xi-kari.v3.cancel",
            "schema_version": 3,
            "run_id": contract["run_id"],
            "reason": reason.strip(),
            "cancelled_at": cancelled_at,
        },
    )
    _set_state(run_dir, "cancelled", next_phase=None)
    commit_terminal_record(
        run_dir,
        contract,
        {
            "run_id": contract["run_id"],
            "terminal_state": "cancelled",
            "terminal_at": cancelled_at,
            "phase_count": len(records),
            "chain_head_sha256": chain_head,
            "reason": reason.strip(),
        },
    )
    return status_run(run_dir)


def repair_plan(run_dir: Path, *, repository_root: Path | None = None) -> dict[str, Any]:
    run_dir = _resolve_run_directory(run_dir)
    contract = read_json(run_dir / "run-contract.json")
    if not isinstance(contract, Mapping):
        raise ValueError("run contract is not an object")
    _require_mutable_contract_profile(contract)
    status = status_run(run_dir)
    if (run_dir / TERMINAL_RELATIVE).exists():
        if status["state"] == "complete":
            raise ValueError("complete run is immutable")
        if status["state"] == "cancelled":
            raise ValueError("cancelled run is terminal")
        raise ValueError("signed terminal run is immutable")
    if status["state"] == "complete":
        raise ValueError("complete run is immutable")
    if status["state"] == "cancelled":
        raise ValueError("cancelled run is terminal")

    repository = _bound_repository_root(run_dir, repository_root)
    report = run_fresh_validator(
        run_dir,
        repository_root=repository,
        preseal=False,
        require_complete=False,
    )
    errors = [
        str(error)
        for error in report.get("errors", [])
        if not str(error).startswith(
            "run artifact schema continuation/repair-plan.json"
        )
    ]
    if not errors:
        raise ValueError("repair requires at least one validation error")
    earliest, reset_phases = derive_repair_scope(errors)
    snapshot_entries: list[dict[str, Any]] = []
    for path in sorted(run_dir.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"repair snapshot cannot contain a symlink: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(run_dir).as_posix()
        if relative == "continuation/repair-plan.json":
            continue
        snapshot_entries.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    plan = {
        "schema_id": "xi-kari.v3.repair-plan",
        "schema_version": 3,
        "run_id": status["run_id"],
        "earliest_invalid_phase": earliest,
        "reset_phases": reset_phases,
        "reason": errors,
        "fresh": True,
        "planned_state": "invalid",
        "run_contract_sha256": sha256_file(run_dir / "run-contract.json"),
        "phase_events_sha256": repair_phase_events_sha256(run_dir),
        "run_snapshot_sha256": sha256_json(snapshot_entries),
        "validator_set_sha256": validator_set_sha256(repository),
        "validation_errors_sha256": sha256_json(errors),
        "validator_fresh_process": report.get("fresh_process") is True,
        "validator_fingerprint_sha256": validator_fingerprint(report),
    }
    _write(run_dir, "continuation/repair-plan.json", plan)
    return plan
