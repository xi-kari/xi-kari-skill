"""Code-owned author workspace inputs and read-only contract guidance."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import sys
from typing import Any
from urllib.parse import unquote

from .canonical_json import (
    atomic_write_bytes, canonical_bytes, confined_path, read_bounded_regular_file,
    read_json, read_json_text, sha256_bytes, sha256_json,
)


SUPPORT_PATH = "runtime-inputs/support.json"
CONTEXT_PATH = "runtime-inputs/authoring-context.json"
MAX_INPUT_BYTES = 64 * 1024 * 1024
READ_LOCATION_FIELDS = ("item_id", "kind", "subject_id", "related_subject_id", "path", "disposition")


def describe_authoring_contract_v4(repository_root: Path) -> dict[str, Any]:
    """Describe real schema requirements without supplying semantic values."""
    repo = Path(repository_root).resolve()
    documents = {value["$id"]: value for path in sorted((repo / "schemas").glob("*.json"))
                 if isinstance((value := read_json(path)), dict) and isinstance(value.get("$id"), str)}
    schema = read_json(repo / "schemas/xk-v4-base-authoring-output.schema.json")

    def describe(node: Any, document: Mapping[str, Any], depth: int, seen: frozenset[str]) -> dict[str, Any]:
        if not isinstance(node, Mapping):
            return {"schema": node}
        reference = node.get("$ref")
        if isinstance(reference, str):
            uri, _, fragment = reference.partition("#")
            identity = (uri or document["$id"]) + "#" + fragment
            if identity in seen:
                return {"schema_ref": identity}
            target_document = documents[uri] if uri else document
            target: Any = target_document
            for part in unquote(fragment).split("/")[1:]:
                target = target[part.replace("~1", "/").replace("~0", "~")]
            result = describe(target, target_document, depth, seen | {identity})
            result["schema_ref"] = identity
            if "description" in node:
                result["description"] = node["description"]
            return result
        result = {key: node[key] for key in ("type", "required", "const", "enum", "description", "format", "minItems", "maxItems", "uniqueItems", "minLength", "pattern", "minimum", "maximum") if key in node}
        if isinstance(node.get("additionalProperties"), bool):
            result["additionalProperties"] = node["additionalProperties"]
        if depth > 0:
            if isinstance(node.get("properties"), Mapping):
                result["properties"] = {key: describe(value, document, depth - 1, seen) for key, value in node["properties"].items()}
            if "items" in node:
                result["items"] = describe(node["items"], document, depth - 1, seen)
            for key in ("allOf", "oneOf", "anyOf"):
                if key in node:
                    result[key] = [describe(value, document, depth - 1, seen) for value in node[key]]
            for key in ("if", "then", "else", "not"):
                if key in node:
                    result[key] = describe(node[key], document, depth - 1, seen)
        return result

    from .execution import MODEL_AUTHORITY_KEYS
    return {
        "contract_version": 4, "source_version": "v9.0",
        "schema": "schemas/xk-v4-base-authoring-output.schema.json",
        "envelope": describe(schema, schema, 4, frozenset()),
        "record_contracts": {name: describe(value, schema, 3, frozenset()) for name, value in schema.get("$defs", {}).items()},
        "reading_bytes_api": {
            "function": "xi_kari_runtime.ontology_read_trace.read_ontology_item_bytes(repository_root, location_record)",
            "input": "Use one row from ontology-read-plan.json records; no expected digest is required.",
            "bytes": "Candidates return the actual UTF-8 census row without its line ending; other items return actual file bytes.",
            "boundary": "Inspect all returned content and form the problem relation yourself. Hashing bytes or locating a file alone is not semantic full reading.",
        },
        "runtime_owned_semantic_packet_keys": sorted(MODEL_AUTHORITY_KEYS),
        "responsibilities": {
            "semantic_packet": "作者填写本题实质判断、引用、六项适用性与完整读者正文；正式资格状态由代码重算。",
            "semantic_read_trace": "依据实际完整读取填写；使用当前源锁与阅读计划，不能用 schema 正确替代真实读取。",
            "ontology_read_trace": "逐项匹配阅读定位视图，读取真实字节后形成内容依据、witness 和问题关系；预检独立重建期望，不提供逐项期待答案。",
            "frozen_problem": "逐字段保留请求中已经冻结的问题边界。",
            "completion": "完整 semantic-output.json 通过只读预检后只输出 SEMANTIC_OUTPUT_READY；预检不生成任何运行回执或封存资格。",
        },
        "guide_boundary": "This guide is derived from actual schemas; conditional branches and runtime semantic validators remain authoritative. It supplies no output values or read-trace records.",
    }


def prepare_authoring_workspace_v4(workspace: Path, *, request: Mapping[str, Any],
        ontology_read_plan: Mapping[str, Any], source_events: list[dict[str, Any]],
        repository_root: Path) -> dict[str, dict[str, Any]]:
    repo, root = Path(repository_root).resolve(), Path(workspace).resolve()
    if request.get("contract_version") != 4 or request.get("source_inputs", {}).get("source_version") != "v9.0":
        raise ValueError("author workspace requires the actual version-four request")
    if request["source_inputs"]["ontology_read_plan"]["plan_sha256"] != sha256_json(ontology_read_plan):
        raise ValueError("author workspace ontology plan differs from the frozen request")
    if request["source_inputs"]["source_lock"]["source_unit_event_sha256"] != sha256_json(source_events):
        raise ValueError("author workspace source events differ from the frozen request")
    python = Path(sys.executable).resolve()
    checker = repo / "scripts/check_authoring_output.py"
    if not python.is_file() or not checker.is_file():
        raise ValueError("author workspace interpreter or read-only validator is unavailable")
    if (root / "runtime-inputs").exists():
        raise ValueError("author workspace inputs cannot replace existing files")
    context = {"contract_version": 4, "request": dict(request)}
    context_bytes = canonical_bytes(context) + b"\n"
    arguments = ["-B", str(checker), "semantic-output.json", "--contract-version", "4",
                 "--context", CONTEXT_PATH, "--context-sha256", sha256_bytes(context_bytes)]
    support = {
        "python_executable": str(python), "preflight_arguments": arguments,
        "context_path": CONTEXT_PATH, "context_sha256": sha256_bytes(context_bytes),
        "schema_guide_path": "runtime-inputs/output-contract.json",
        "ontology_plan_path": "runtime-inputs/ontology-read-plan.json",
        "source_plan_path": "runtime-inputs/source-read-plan.json",
        "output_path": "semantic-output.json", "completion_notice": "SEMANTIC_OUTPUT_READY",
        "validation_scope": "Read-only author feedback using the frozen inputs; no receipts, automatic repairs, trace generation or runtime sealing.",
    }
    locations = []
    for record in ontology_read_plan["records"]:
        row = {field: record[field] for field in READ_LOCATION_FIELDS}
        if any(not isinstance(value, str) and not (field == "related_subject_id" and value is None) for field, value in row.items()):
            raise ValueError("author reading location has an invalid identity or responsibility")
        locations.append(row)
    reading_view = {"view_kind": "reading_locations_only", "framework_version": "v9.0",
        "record_count": len(locations), "records": locations,
        "boundary": "Identity, location and responsibility only. The author must read actual bytes; no item expected digest or witness is supplied."}
    documents = {
        CONTEXT_PATH: context_bytes,
        SUPPORT_PATH: canonical_bytes(support) + b"\n",
        support["schema_guide_path"]: canonical_bytes(describe_authoring_contract_v4(repo)) + b"\n",
        support["ontology_plan_path"]: canonical_bytes(reading_view) + b"\n",
        support["source_plan_path"]: canonical_bytes(request["source_inputs"]["read_plan"]) + b"\n",
    }
    for relative, raw in documents.items():
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("author workspace input exceeds the bounded input limit")
        atomic_write_bytes(confined_path(root, relative), raw)
    return {relative: {"sha256": sha256_bytes(raw), "bytes": len(raw)} for relative, raw in documents.items()}


def verify_authoring_workspace_v4(workspace: Path, binding: Mapping[str, Mapping[str, Any]]) -> None:
    try:
        for relative, expected in binding.items():
            raw = read_bounded_regular_file(confined_path(Path(workspace), relative, must_exist=True), limit=MAX_INPUT_BYTES)
            if sha256_bytes(raw) != expected["sha256"] or len(raw) != expected["bytes"]:
                raise ValueError()
    except (OSError, ValueError, TypeError, KeyError):
        raise ValueError("author changed or removed a frozen workspace input") from None


def read_authoring_context_v4(path: Path, *, expected_sha256: str) -> dict[str, Any]:
    raw = read_bounded_regular_file(path, limit=MAX_INPUT_BYTES)
    if not isinstance(expected_sha256, str) or sha256_bytes(raw) != expected_sha256:
        raise ValueError("authoring context differs from its runtime-provided digest")
    context = read_json_text(raw.decode("utf-8"))
    if not isinstance(context, dict) or set(context) != {"contract_version", "request"} or context["contract_version"] != 4:
        raise ValueError("authoring context has an incompatible structure")
    request = context["request"]
    if not isinstance(request, Mapping) or request.get("contract_version") != 4 or request.get("source_inputs", {}).get("source_version") != "v9.0":
        raise ValueError("authoring context does not bind a version-four source request")
    return context


__all__ = ("prepare_authoring_workspace_v4", "verify_authoring_workspace_v4",
           "describe_authoring_contract_v4", "read_authoring_context_v4")
