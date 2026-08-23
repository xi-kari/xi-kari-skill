#!/usr/bin/env python3
"""Read-only repository and run-contract checker for Xi-Kari v2."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import re
import sys
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from build_source_snapshot import build as check_source_build
from check_ontology import check as check_ontology
from check_source_snapshot import check_candidate_index, check_coverage


EXPECTED_COMMANDS = {
    "init",
    "prepare",
    "execute",
    "materialize",
    "validate",
    "repair-plan",
    "resume",
    "fork",
    "cancel",
    "status",
}
FORBIDDEN_FLAGS = {"--fallback", "--use-promax", "--use-crossframe"}
EXPECTED_PHASES = tuple(f"XK{index}" for index in range(13))
EXPECTED_RESPONSIBILITIES = {
    "XK0": "问题合同",
    "XK1": "源锁",
    "XK2": "检索",
    "XK3": "证据",
    "XK4": "候选",
    "XK5": "联合状态",
    "XK6": "变换",
    "XK7": "机制",
    "XK8": "三阶",
    "XK9": "红队",
    "XK10": "裁决",
    "XK11": "读者",
    "XK12": "验证",
}
EXPECTED_EXECUTE_OWNED_BINDING_FIELDS = {
    "protocol",
    "owner",
    "run_id",
    "parent_pid",
    "child_pid",
    "exit_status",
    "provider_binding_sha256",
    "provider_executable_sha256",
    "provider_argv_sha256",
    "adapter_executable_sha256",
    "command_sha256",
    "input_sha256",
    "prompt_sha256",
    "stdout_sha256",
    "stderr_sha256",
    "semantic_output_sha256",
    "semantic_read_trace_sha256",
    "ontology_read_plan_sha256",
    "ontology_read_trace_sha256",
    "base_receipt_sha256",
    "retrieval_receipt_sha256",
    "retrieval_sha256",
}
EXPECTED_RUNTIME_OWNED_VISIBILITY_POLICIES = {
    "open-world": {
        "retrieval.queries[*].query_id": ("public", "include"),
        "retrieval.queries[*].status": ("public", "include"),
        "retrieval.queries[*].executed_at": ("public", "include"),
        "retrieval.queries[*].result_source_ids[*]": ("public", "include"),
        "retrieval.sources[*].source_id": ("public", "include"),
        "retrieval.sources[*].accessed_at": ("public", "include"),
        "retrieval.sources[*].content_authority": ("public", "include"),
        "retrieval.sources[*].host_observation.status": ("public", "include"),
        "retrieval.sources[*].host_observation.open_event_ids[*]": (
            "public",
            "include",
        ),
        "retrieval.sources[*].host_observation.capture_id": ("public", "include"),
        "retrieval.sources[*].host_observation.requested_url": ("public", "include"),
        "retrieval.sources[*].host_observation.final_url": ("public", "include"),
        "retrieval.sources[*].host_observation.peer_ip": ("public", "include"),
        "retrieval.sources[*].host_observation.response_status": ("public", "include"),
        "retrieval.sources[*].host_observation.content_type": ("public", "include"),
        "retrieval.sources[*].host_observation.charset": ("public", "include"),
        "retrieval.sources[*].host_observation.body_sha256": ("public", "include"),
        "retrieval.sources[*].host_observation.text_sha256": ("public", "include"),
        "retrieval.sources[*].host_observation.body_byte_count": ("public", "include"),
        "retrieval.sources[*].host_observation.text_character_count": ("public", "include"),
        "retrieval.sources[*].host_observation.redirect_chain[*]": ("public", "include"),
        "retrieval.sources[*].host_observation.excerpt_sha256": ("public", "include"),
        "retrieval.sources[*].host_observation.excerpt_start": ("public", "include"),
        "retrieval.sources[*].host_observation.excerpt_end": ("public", "include"),
        "retrieval.assessments[*].source_id": ("public", "include"),
        "retrieval.directional_evidence[*].direction": ("public", "include"),
        "retrieval.directional_evidence[*].search_event_id": ("public", "include"),
        "retrieval.directional_evidence[*].stop_boundary": ("public", "include"),
        "retrieval.directional_evidence[*].source_urls[*]": ("public", "include"),
        "retrieval.directional_evidence[*].source_ids[*]": ("public", "include"),
        "retrieval.directional_evidence[*].distinct_url_count": ("public", "include"),
        "retrieval.directional_evidence[*].distinct_source_count": ("public", "include"),
        "retrieval.directional_evidence[*].distinct_content_count": ("public", "include"),
        "retrieval.directional_evidence[*].distinct_independence_count": ("public", "include"),
        "retrieval.directional_evidence[*].new_information_count": ("public", "include"),
        "retrieval.directional_evidence[*].stop_reason": ("public", "include"),
    },
    "closed-input": {
        "retrieval.queries[*].query_id": ("public", "include"),
        "retrieval.queries[*].status": ("public", "include"),
        "retrieval.queries[*].executed_at": ("public", "include"),
        "retrieval.queries[*].result_source_ids[*]": ("public", "include"),
        "retrieval.sources[*].accessed_at": ("public", "include"),
        "retrieval.frozen_material_manifest.materials[*].source_id": (
            "public",
            "include",
        ),
    },
}
EXPECTED_RUNTIME_ONLY_VISIBILITY_PATHS = {
    "open-world": (
        "retrieval.queries[*].query_id",
        "retrieval.queries[*].status",
        "retrieval.queries[*].executed_at",
        "retrieval.queries[*].result_source_ids[*]",
        "retrieval.sources[*].accessed_at",
        "retrieval.sources[*].content_authority",
        "retrieval.sources[*].host_observation.status",
        "retrieval.sources[*].host_observation.open_event_ids[*]",
        "retrieval.sources[*].host_observation.capture_id",
        "retrieval.sources[*].host_observation.requested_url",
        "retrieval.sources[*].host_observation.final_url",
        "retrieval.sources[*].host_observation.peer_ip",
        "retrieval.sources[*].host_observation.response_status",
        "retrieval.sources[*].host_observation.content_type",
        "retrieval.sources[*].host_observation.charset",
        "retrieval.sources[*].host_observation.body_sha256",
        "retrieval.sources[*].host_observation.text_sha256",
        "retrieval.sources[*].host_observation.body_byte_count",
        "retrieval.sources[*].host_observation.text_character_count",
        "retrieval.sources[*].host_observation.redirect_chain[*]",
        "retrieval.sources[*].host_observation.excerpt_sha256",
        "retrieval.sources[*].host_observation.excerpt_start",
        "retrieval.sources[*].host_observation.excerpt_end",
        "retrieval.directional_evidence[*].direction",
        "retrieval.directional_evidence[*].search_event_id",
        "retrieval.directional_evidence[*].stop_boundary",
        "retrieval.directional_evidence[*].source_urls[*]",
        "retrieval.directional_evidence[*].source_ids[*]",
        "retrieval.directional_evidence[*].distinct_url_count",
        "retrieval.directional_evidence[*].distinct_source_count",
        "retrieval.directional_evidence[*].distinct_content_count",
        "retrieval.directional_evidence[*].distinct_independence_count",
        "retrieval.directional_evidence[*].new_information_count",
        "retrieval.directional_evidence[*].stop_reason",
    ),
    "closed-input": (
        "retrieval.queries[*].query_id",
        "retrieval.queries[*].status",
        "retrieval.queries[*].executed_at",
        "retrieval.queries[*].result_source_ids[*]",
        "retrieval.sources[*].accessed_at",
        "retrieval.frozen_material_manifest.materials[*].source_id",
    ),
}
EXPECTED_PROJECTION_OMITTED_VISIBILITY_PATHS = {
    "open-world": ("retrieval.queries[*].purpose",),
    "closed-input": ("retrieval.queries[*].purpose",),
}
EXPECTED_MODEL_SOURCE_FIELDS = {
    "open-world": {
        "source_id",
        "origin",
        "title",
        "url",
        "publisher",
        "content",
        "published_at",
        "event_at",
    },
    "closed-input": {
        "source_id",
        "origin",
        "title",
        "content",
        "published_at",
        "event_at",
    },
}
EXPECTED_MODEL_RETRIEVAL_FIELDS = {
    "open-world": {
        "mode",
        "queries",
        "sources",
        "assessments",
        "saturation_status",
        "capability_gap",
        "remaining_unknowns",
    },
    "closed-input": {
        "mode",
        "queries",
        "sources",
        "assessments",
        "saturation_status",
        "capability_gap",
        "remaining_unknowns",
    },
}
EXPECTED_MODEL_QUERY_FIELDS = {
    "open-world": {"direction", "query", "purpose"},
    "closed-input": {"direction", "query", "purpose"},
}
EXPECTED_MODEL_ASSESSMENT_FIELDS = {
    "open-world": {
        "source_id",
        "authority",
        "independence",
        "independence_identity",
        "source_lineage",
        "interest_relevance",
        "affected_positions",
        "low_power_positions",
        "conflict_source_ids",
        "freshness",
        "relevance",
        "verdict",
        "limitations",
        "cannot_prove",
    },
    "closed-input": {
        "source_id",
        "authority",
        "independence",
        "independence_identity",
        "source_lineage",
        "interest_relevance",
        "affected_positions",
        "low_power_positions",
        "conflict_source_ids",
        "freshness",
        "relevance",
        "verdict",
        "limitations",
        "cannot_prove",
    },
}
EXPECTED_RUNTIME_OWNED_MODEL_FIELDS = {
    "open-world": {
        "query": {"query_id", "status", "executed_at", "result_source_ids"},
        "source": {
            "accessed_at",
            "content_authority",
            "content_sha256",
            "run_id",
        },
        "assessment": set(),
    },
    "closed-input": {
        "query": {"query_id", "status", "executed_at", "result_source_ids"},
        "source": {
            "accessed_at",
            "content_authority",
            "content_sha256",
            "run_id",
        },
        "assessment": set(),
    },
}
FORBIDDEN_EXECUTABLE_PATTERNS = {
    "PhaseStore": re.compile(r"\bPhaseStore\b"),
    "writer lease": re.compile(r"\bwriter[_ -]?lease\b", re.IGNORECASE),
    "heartbeat": re.compile(r"\bheartbeat\b", re.IGNORECASE),
    "host handshake": re.compile(r"\bhost[_ -]?handshake\b", re.IGNORECASE),
    "pending action": re.compile(r"\bpending[_ -]?action(?:\.json)?\b", re.IGNORECASE),
    "release promotion": re.compile(r"\brelease[_ -]?promotion\b", re.IGNORECASE),
    "legacy U phase": re.compile(r"\bU(?:[0-9]|1[0-2])\b"),
}

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
    "authoring/XK01-base-authoring-request.json": {
        "xi-kari.v2.base-authoring-request"
    },
    "authoring/XK01-base-authoring-events.jsonl": {
        "xi-kari.v2.codex-jsonl-event"
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
    "continuation/completion.json": {"xi-kari.v2.completion"},
    "continuation/input-packet.json": {"xi-kari.v2.analysis-packet"},
    "continuation/parent.json": {"xi-kari.v2.parent-binding"},
    "continuation/repair-plan.json": {"xi-kari.v2.repair-plan"},
    "continuation/repair-record.json": {"xi-kari.v2.repair-record"},
    "continuation/state.json": {"xi-kari.v2.continuation-state"},
    "continuation/terminal-authority-key.json": {
        "xi-kari.v2.terminal-authority-key"
    },
    "continuation/terminal-record.json": {"xi-kari.v2.terminal-record"},
    "continuation/xk12-transaction.json": {"xi-kari.v2.xk12-transaction"},
    "delivery/final-chat.json": {"xi-kari.v2.final-chat"},
    "phase-events.jsonl": {"xi-kari.v2.phase-event"},
    "retrieval/index.json": {"xi-kari.v2.retrieval-index"},
    "run-contract.json": {"xi-kari.v2.run-contract"},
    "source-lock.json": {"xi-kari.v2.source-lock"},
    "validation/attempts/final/validator-report.json": {"xi-kari.v2.validator-report"},
    "validation/attempts/official/validator-report.json": {
        "xi-kari.v2.validator-report"
    },
}
ARTIFACT_SCHEMA_PATTERNS = (
    ("authoring/recursive-state/*.json", {"xi-kari.v2.xk.recursive-state"}),
    ("retrieval/assessments/*.json", {"xi-kari.v2.source-assessment"}),
    ("retrieval/sources/*.json", {"xi-kari.v2.source-record"}),
)


def _reject_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _loads_json(text: str) -> Any:
    return json.loads(
        text,
        parse_constant=_reject_constant,
        object_pairs_hook=_unique_object,
    )


def _expected_artifact_schema_ids(relative: str) -> set[str] | None:
    expected = ARTIFACT_SCHEMA_IDS.get(relative)
    if expected is not None:
        return expected
    path = Path(relative)
    for pattern, schema_ids in ARTIFACT_SCHEMA_PATTERNS:
        if path.match(pattern):
            return schema_ids
    return None


def _read_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        value = _loads_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        errors.append(f"cannot read JSON {path}: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"JSON schema must be an object: {path}")
        return None
    return value


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
    root: Path,
) -> tuple[dict[str, Draft202012Validator], list[str]]:
    errors: list[str] = []
    schema_paths = sorted((root / "schemas").glob("xk-*.json"))
    if not schema_paths:
        return {}, ["no Xi-Kari v2 runtime schemas found"]
    owners: dict[str, Path] = {}
    validators: dict[str, Draft202012Validator] = {}
    documents: list[tuple[Path, dict[str, Any]]] = []
    resources: Registry[Any] = Registry()
    for path in schema_paths:
        schema = _read_json(path, errors)
        if schema is None:
            continue
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            errors.append(f"invalid runtime schema {path}: {exc}")
            continue
        schema_uri = schema.get("$id")
        if not isinstance(schema_uri, str) or not schema_uri.startswith(
            "https://xi-kari.local/schemas/xi-kari.v2."
        ):
            errors.append(f"runtime schema has a non-v2 $id: {path}")
        elif schema_uri:
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
            if not schema_id.startswith("xi-kari.v2."):
                errors.append(f"runtime schema contains a legacy schema_id {schema_id}: {path}")
            previous = owners.setdefault(schema_id, path)
            if previous != path:
                errors.append(
                    f"runtime schema_id has multiple owners: {schema_id}: {previous}, {path}"
                )
            validators[schema_id] = Draft202012Validator(
                schema,
                format_checker=FormatChecker(),
                registry=resources,
            )
    return validators, errors


def _check_runtime_schemas(root: Path) -> list[str]:
    registry, errors = _runtime_schema_registry(root)
    emitted: set[str] = set()
    runtime_paths = [root / "scripts" / "xi_kari_runtime.py"]
    runtime_paths.extend(sorted((root / "scripts" / "xi_kari_runtime").glob("*.py")))
    for path in runtime_paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            errors.append(f"cannot inspect runtime schema emitters {path}: {exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if re.fullmatch(r"xi-kari\.v2\.[a-z0-9.-]+", node.value):
                    emitted.add(node.value)
            if not isinstance(node, ast.Call):
                continue
            function_name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else None
            )
            if function_name != "_runtime_document":
                continue
            for keyword in node.keywords:
                if (
                    keyword.arg == "kind"
                    and isinstance(keyword.value, ast.Constant)
                    and isinstance(keyword.value.value, str)
                ):
                    emitted.add(f"xi-kari.v2.{keyword.value.value}")
    missing = sorted(emitted - set(registry))
    if missing:
        errors.append(f"runtime emits schema_id values with no schema owner: {missing}")
    return errors


def _cli_commands(tree: ast.AST) -> set[str]:
    commands: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "add_parser" or not node.args:
            continue
        value = node.args[0]
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            commands.add(value.value)
    return commands


def _check_cli(root: Path) -> list[str]:
    path = root / "scripts" / "xi_kari_runtime.py"
    if not path.is_file():
        return [f"missing runtime CLI: {path}"]
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
    except (OSError, SyntaxError) as exc:
        return [f"cannot parse runtime CLI: {exc}"]
    errors: list[str] = []
    commands = _cli_commands(tree)
    if commands != EXPECTED_COMMANDS:
        errors.append(
            "runtime CLI command surface mismatch: "
            f"missing={sorted(EXPECTED_COMMANDS - commands)}, "
            f"extra={sorted(commands - EXPECTED_COMMANDS)}"
        )
    flags = set(re.findall(r"--[a-z][a-z-]*", text))
    forbidden = sorted(flags & FORBIDDEN_FLAGS)
    if forbidden:
        errors.append(f"runtime CLI exposes forbidden fallback flags: {forbidden}")
    if "--request-stdin" not in flags:
        errors.append("runtime CLI does not expose --request-stdin")
    return errors


def _literal_assignment(path: Path, name: str) -> Any:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"missing literal assignment: {name}")


def _check_phase_contract(root: Path) -> list[str]:
    errors: list[str] = []
    contracts = root / "scripts" / "xi_kari_runtime" / "contracts.py"
    try:
        responsibilities = _literal_assignment(contracts, "PHASE_RESPONSIBILITIES")
    except (OSError, SyntaxError, ValueError) as exc:
        return [f"cannot read phase responsibilities: {exc}"]
    if responsibilities != EXPECTED_RESPONSIBILITIES:
        errors.append("XK0-XK12 phase responsibilities differ from the frozen v2 contract")
    for relative in ("SKILL.md", "protocols/runtime.md", "references/runtime-read-map.md"):
        path = root / relative
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"cannot read phase contract {relative}: {exc}")
            continue
        for phase in EXPECTED_PHASES:
            if phase not in text:
                errors.append(f"{relative} omits {phase}")
    return errors


def _check_visibility_contract(root: Path) -> list[str]:
    errors: list[str] = []
    execution = root / "scripts" / "xi_kari_runtime" / "execution.py"
    try:
        policies = _literal_assignment(
            execution, "RUNTIME_OWNED_VISIBILITY_POLICIES"
        )
        runtime_only = _literal_assignment(
            execution, "RUNTIME_ONLY_VISIBILITY_PATHS"
        )
        omitted = _literal_assignment(
            execution, "PROJECTION_OMITTED_VISIBILITY_PATHS"
        )
        source_fields = _literal_assignment(execution, "MODEL_SOURCE_FIELDS")
        retrieval_fields = _literal_assignment(
            execution, "MODEL_RETRIEVAL_FIELDS"
        )
        query_fields = _literal_assignment(execution, "MODEL_QUERY_FIELDS")
        assessment_fields = _literal_assignment(
            execution, "MODEL_ASSESSMENT_FIELDS"
        )
        runtime_model_fields = _literal_assignment(
            execution, "RUNTIME_OWNED_MODEL_FIELDS"
        )
    except (OSError, SyntaxError, ValueError) as exc:
        return [f"cannot read production visibility policy: {exc}"]
    if policies != EXPECTED_RUNTIME_OWNED_VISIBILITY_POLICIES:
        errors.append(
            "mode-specific runtime-owned visibility allowlists differ from the frozen policy"
        )
    if runtime_only != EXPECTED_RUNTIME_ONLY_VISIBILITY_PATHS:
        errors.append(
            "mode-specific runtime-only visibility paths differ from the frozen policy"
        )
    if omitted != EXPECTED_PROJECTION_OMITTED_VISIBILITY_PATHS:
        errors.append("projection visibility omission list differs from the frozen policy")
    if source_fields != EXPECTED_MODEL_SOURCE_FIELDS:
        errors.append("mode-specific model retrieval source fields differ from policy")
    if retrieval_fields != EXPECTED_MODEL_RETRIEVAL_FIELDS:
        errors.append("mode-specific model retrieval root fields differ from policy")
    if query_fields != EXPECTED_MODEL_QUERY_FIELDS:
        errors.append("mode-specific model retrieval query fields differ from policy")
    if assessment_fields != EXPECTED_MODEL_ASSESSMENT_FIELDS:
        errors.append(
            "mode-specific model retrieval assessment fields differ from policy"
        )
    if runtime_model_fields != EXPECTED_RUNTIME_OWNED_MODEL_FIELDS:
        errors.append("runtime-owned model retrieval fields differ from policy")

    output_schema = _read_json(
        root / "schemas" / "xk-base-authoring-output.schema.json", errors
    )
    if output_schema is not None:
        try:
            ledger = output_schema["properties"]["semantic_packet"]["properties"][
                "visibility_ledger"
            ]
            retrieval_ref = output_schema["properties"]["semantic_packet"][
                "properties"
            ]["retrieval"]
            model_retrieval = output_schema["$defs"]["modelRetrieval"]
            model_query = output_schema["$defs"]["modelQuery"]
            model_assessment = output_schema["$defs"]["modelAssessment"]
            open_source = output_schema["$defs"]["openModelSource"]
            closed_source = output_schema["$defs"]["closedModelSource"]
            entries = ledger["properties"]["entries"]
            entry = output_schema["$defs"]["visibilityEntry"]
            required = set(entry["required"])
        except (KeyError, TypeError):
            errors.append("base authoring output schema has no exact visibility ledger")
        else:
            expected_fields = {
                "canonical_path",
                "classification",
                "disclosure",
                "purpose",
                "authority_refs",
                "protection_reason",
            }
            if (
                ledger.get("additionalProperties") is not False
                or ledger.get("required") != ["entries"]
                or entries.get("minItems") != 1
                or entries.get("items") != {"$ref": "#/$defs/visibilityEntry"}
                or entry.get("additionalProperties") is not False
                or required != expected_fields
            ):
                errors.append(
                    "base authoring output visibility ledger schema is not fail-closed"
                )
            expected_root_fields = {
                "mode",
                "queries",
                "sources",
                "assessments",
                "saturation_status",
                "capability_gap",
                "remaining_unknowns",
            }
            expected_query_fields = {"direction", "query", "purpose"}
            expected_assessment_fields = EXPECTED_MODEL_ASSESSMENT_FIELDS["open-world"]
            if (
                retrieval_ref != {"$ref": "#/$defs/modelRetrieval"}
                or model_retrieval.get("additionalProperties") is not False
                or set(model_retrieval.get("properties", {}))
                != expected_root_fields
                or set(model_retrieval.get("required", [])) != expected_root_fields
                or model_query.get("additionalProperties") is not False
                or set(model_query.get("properties", {})) != expected_query_fields
                or set(model_query.get("required", [])) != expected_query_fields
                or model_assessment.get("additionalProperties") is not False
                or set(model_assessment.get("properties", {}))
                != expected_assessment_fields
                or set(model_assessment.get("required", []))
                != expected_assessment_fields
                or open_source.get("additionalProperties") is not False
                or set(open_source.get("properties", {}))
                != EXPECTED_MODEL_SOURCE_FIELDS["open-world"]
                or set(open_source.get("required", []))
                != EXPECTED_MODEL_SOURCE_FIELDS["open-world"]
                or closed_source.get("additionalProperties") is not False
                or set(closed_source.get("properties", {}))
                != EXPECTED_MODEL_SOURCE_FIELDS["closed-input"]
                or not {
                    "source_id",
                    "origin",
                    "title",
                    "content",
                }.issubset(set(closed_source.get("required", [])))
            ):
                errors.append(
                    "base authoring output retrieval schema does not freeze mode-specific ownership"
                )

    request_schema = _read_json(
        root / "schemas" / "xk-base-authoring-request.schema.json", errors
    )
    if request_schema is not None:
        required = request_schema.get("required", [])
        privacy = request_schema.get("properties", {}).get("privacy_contract")
        definition = request_schema.get("$defs", {}).get("privacyContract")
        if (
            "privacy_contract" not in required
            or privacy != {"$ref": "#/$defs/privacyContract"}
            or not isinstance(definition, dict)
            or definition.get("additionalProperties") is not False
            or definition.get("properties", {}).get("fail_closed")
            != {"const": True}
        ):
            errors.append("base authoring request does not freeze the privacy contract")
    return errors


def _profile_then(schema: dict[str, Any], profile: str) -> dict[str, Any] | None:
    for branch in schema.get("allOf", []):
        if not isinstance(branch, dict):
            continue
        condition = branch.get("if", {})
        properties = condition.get("properties", {}) if isinstance(condition, dict) else {}
        profile_rule = properties.get("contract_profile", {}) if isinstance(properties, dict) else {}
        if isinstance(profile_rule, dict) and profile_rule.get("const") == profile:
            then = branch.get("then")
            return then if isinstance(then, dict) else None
    return None


def _function_source(path: Path, name: str) -> str:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            segment = ast.get_source_segment(text, node)
            if segment is not None:
                return segment
    raise ValueError(f"missing function: {name}")


def _check_production_prepare_authority(root: Path) -> list[str]:
    errors: list[str] = []
    schemas = (
        (root / "schemas/xk-run.schema.json", True),
        (root / "schemas/xk-capability.schema.json", False),
    )
    for path, nested in schemas:
        schema = _read_json(path, errors)
        if schema is None:
            continue
        container = (
            schema.get("properties", {}).get("capability_snapshot")
            if nested
            else schema
        )
        if not isinstance(container, dict) or container.get("additionalProperties") is not False:
            errors.append(f"execute-owned binding schema is not closed: {path}")
            continue
        binding_ref = container.get("properties", {}).get("execute_owned_binding")
        if binding_ref != {"$ref": "#/$defs/execute_owned_binding"}:
            errors.append(f"execute-owned binding schema property is missing: {path}")
        definition = schema.get("$defs", {}).get("execute_owned_binding")
        if (
            not isinstance(definition, dict)
            or definition.get("additionalProperties") is not False
            or set(definition.get("required", []))
            != EXPECTED_EXECUTE_OWNED_BINDING_FIELDS
            or set(definition.get("properties", {}))
            != EXPECTED_EXECUTE_OWNED_BINDING_FIELDS
            or definition.get("properties", {}).get("protocol")
            != {"const": "xi-kari.v2.execute-owned-binding/v1"}
            or definition.get("properties", {}).get("owner")
            != {"const": "execute_authored_run"}
        ):
            errors.append(f"execute-owned binding schema is not exact: {path}")
        production = _profile_then(schema, "production-authoring-v2")
        legacy = _profile_then(schema, "legacy-fixture-v3")
        production_container = (
            production.get("properties", {}).get("capability_snapshot")
            if nested and isinstance(production, dict)
            else production
        )
        legacy_container = (
            legacy.get("properties", {}).get("capability_snapshot")
            if nested and isinstance(legacy, dict)
            else legacy
        )
        if not isinstance(production_container, dict) or "execute_owned_binding" not in set(
            production_container.get("required", [])
        ):
            errors.append(f"production schema does not require execute-owned binding: {path}")
        if not isinstance(legacy_container, dict) or legacy_container.get("not") != {
            "required": ["execute_owned_binding"]
        }:
            errors.append(f"legacy schema does not reject execute-owned binding: {path}")

    materialization = root / "scripts/xi_kari_runtime/materialization.py"
    execution = root / "scripts/xi_kari_runtime/execution.py"
    contracts = root / "scripts/xi_kari_runtime/contracts.py"
    try:
        public_prepare = _function_source(materialization, "prepare_run")
        private_prepare = _function_source(materialization, "_prepare_production_run")
        prepare_impl = _function_source(materialization, "_prepare_run_impl")
        capability_consume = materialization.read_text(encoding="utf-8")
        execute = _function_source(execution, "execute_authored_run")
        runtime_controls = _function_source(contracts, "validate_runtime_control_bindings")
    except (OSError, SyntaxError, ValueError) as exc:
        return errors + [f"cannot inspect production preparation authority: {exc}"]
    if (
        "PRODUCTION_CONTRACT_PROFILE" not in public_prepare
        or "public prepare_run only supports legacy-fixture-v3" not in public_prepare
        or "_prepare_run_impl" not in public_prepare
    ):
        errors.append("public prepare_run does not fail closed for production")
    if (
        "_production_capability=capability" not in private_prepare
        or "_prepare_run_impl" not in private_prepare
        or "_production_capability.consume_for" not in prepare_impl
        or "self._base_authoring_execution is not base_authoring_execution"
        not in capability_consume
    ):
        errors.append("private production preparation lacks object-identity authority")
    required_order = (
        "subprocess.Popen",
        "_strict_event_stream",
        "_parse_base_output",
        "validate_semantic_read_trace_input",
        "_project_retrieval",
        "build_execute_owned_binding",
        "_issue_production_preparation_capability",
        "_prepare_production_run",
    )
    positions = [execute.find(marker) for marker in required_order]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        errors.append("execute_authored_run preparation authority order is invalid")
    if not all(
        marker in runtime_controls
        for marker in (
            "validate_execute_owned_binding",
            "XK01-base-authoring-receipt.json",
            "XK02-retrieval-execution-receipt.json",
        )
    ):
        errors.append("fresh runtime controls do not cross-check execute-owned binding")
    return errors


def _check_forbidden_control_plane(root: Path) -> list[str]:
    errors: list[str] = []
    runtime_paths = [root / "scripts" / "xi_kari_runtime.py"]
    runtime_paths.extend(sorted((root / "scripts" / "xi_kari_runtime").glob("*.py")))
    for path in runtime_paths:
        try:
            text = path.read_text(encoding="utf-8")
            ast.parse(text, filename=str(path))
        except (OSError, SyntaxError) as exc:
            errors.append(f"cannot parse runtime module {path}: {exc}")
            continue
        for label, pattern in FORBIDDEN_EXECUTABLE_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"runtime contains forbidden {label} control surface: {path}")
    for path in sorted((root / "scripts" / "xi_kari_runtime").rglob("*")):
        lowered = path.name.lower().replace("-", "_")
        if lowered in {
            "phasestore",
            "phase_store.py",
            "host_handshake.py",
            "pending_action.json",
            "heartbeat.py",
            "writer_lease.py",
        }:
            errors.append(f"forbidden legacy control-plane path exists: {path}")
    return errors


def check_repository(root: Path, *, all_checks: bool) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    errors.extend(_check_cli(root))
    errors.extend(_check_phase_contract(root))
    errors.extend(_check_visibility_contract(root))
    errors.extend(_check_production_prepare_authority(root))
    errors.extend(_check_runtime_schemas(root))
    errors.extend(_check_forbidden_control_plane(root))
    if all_checks:
        errors.extend(check_source_build(root, check=True))
        errors.extend(check_coverage(root))
        errors.extend(check_candidate_index(root))
        errors.extend(check_ontology(root))
    return list(dict.fromkeys(errors))


def _json_records(path: Path) -> list[tuple[int | None, Any]]:
    if path.suffix == ".jsonl":
        records: list[tuple[int | None, Any]] = []
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if line.strip():
                records.append((line_number, _loads_json(line)))
        return records
    return [(None, _loads_json(path.read_text(encoding="utf-8")))]


def check_run(root: Path, run_dir: Path) -> list[str]:
    root = root.resolve()
    run_dir = run_dir.expanduser()
    errors: list[str] = []
    if run_dir.is_symlink():
        return ["run directory must not be a symlink"]
    run_dir = run_dir.resolve()
    if not run_dir.is_dir():
        return [f"run directory does not exist: {run_dir}"]

    registry, schema_errors = _runtime_schema_registry(root)
    errors.extend(schema_errors)
    try:
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from scripts.xi_kari_runtime.validation import validate_run

        report = validate_run(run_dir, repository_root=root)
        if report.get("valid") is not True:
            errors.extend(
                f"fresh run validation: {error}"
                for error in report.get("errors", ["validator returned invalid"])
            )
    except Exception as exc:
        errors.append(f"fresh run validation failed: {exc}")

    paths = sorted([*run_dir.rglob("*.json"), *run_dir.rglob("*.jsonl")])
    if not paths:
        errors.append("run contains no JSON artifacts")
    for path in paths:
        relative = path.relative_to(run_dir).as_posix()
        if path.is_symlink():
            errors.append(f"run artifact must not be a symlink: {relative}")
            continue
        try:
            records = _json_records(path)
        except (OSError, ValueError) as exc:
            errors.append(f"cannot parse run artifact {relative}: {exc}")
            continue
        if path.suffix == ".jsonl" and not records:
            errors.append(f"JSONL artifact is empty: {relative}")
        for line_number, value in records:
            location = relative if line_number is None else f"{relative}:{line_number}"
            if not isinstance(value, dict):
                errors.append(f"run artifact record is not an object: {location}")
                continue
            if relative == "authoring/XK01-base-authoring-events.jsonl":
                if not isinstance(value.get("type"), str) or not value["type"]:
                    errors.append(f"Codex event has no type: {location}")
                continue
            schema_id = value.get("schema_id")
            if not isinstance(schema_id, str) or not schema_id.startswith("xi-kari.v2."):
                errors.append(f"run artifact has no v2 schema_id: {location}")
                continue
            expected_schema_ids = _expected_artifact_schema_ids(relative)
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
    return list(dict.fromkeys(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the Xi-Kari v2 runtime contract")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    errors = check_repository(args.root, all_checks=args.all)
    if args.run_dir is not None:
        errors.extend(check_run(args.root, args.run_dir))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("xi-kari runtime: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
