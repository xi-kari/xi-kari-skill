"""Root artifact identities and repository-bound schema references."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any
from urllib.parse import unquote

from referencing import Registry, Resource


V4_SCHEMA_IDENTITIES = {
    "xk-semantic-read-trace-input-v4.schema.json": (
        "xi-kari.v4.semantic-read-trace-input",
        frozenset({"xi-kari.v4.semantic-read-trace-input"}),
    ),
    "xk-v4-analysis-packet.schema.json": (
        "xi-kari.v4.analysis-packet",
        frozenset({"xi-kari.v4.analysis-packet"}),
    ),
    "xk-v4-base-authoring-output.schema.json": (
        "xi-kari.v4.base-authoring-output", frozenset(),
    ),
    "xk-v4-base-authoring-request.schema.json": (
        "xi-kari.v4.base-authoring-request",
        frozenset({"xi-kari.v4.base-authoring-request"}),
    ),
    "xk-v4-claim-mechanism.schema.json": (
        "xi-kari.v4.xk.claim-mechanism-graph",
        frozenset({"xi-kari.v4.xk.claim-mechanism-graph"}),
    ),
    "xk-v4-common.schema.json": ("xi-kari.v4.xk.common", frozenset()),
    "xk-v4-formal-input.schema.json": ("xi-kari.v4.formal-input", frozenset()),
    "xk-v4-production-capability.schema.json": (
        "xi-kari.v4.capability-snapshot", frozenset({"xi-kari.v4.capability-snapshot"}),
    ),
    "xk-v4-production-completion.schema.json": (
        "xi-kari.v4.completion", frozenset({"xi-kari.v4.completion"}),
    ),
    "xk-v4-production-manifest.schema.json": (
        "xi-kari.v4.artifact-manifest", frozenset({"xi-kari.v4.artifact-manifest"}),
    ),
    "xk-v4-production-output.schema.json": (
        "xi-kari.v4.final-chat", frozenset({"xi-kari.v4.final-chat"}),
    ),
    "xk-v4-production-phase.schema.json": (
        "xi-kari.v4.production-phase-artifact", frozenset({"xi-kari.v4.production-phase-artifact"}),
    ),
    "xk-v4-production-read-plan.schema.json": (
        "xi-kari.v4.read-plan", frozenset({"xi-kari.v4.read-plan"}),
    ),
    "xk-v4-production-run.schema.json": (
        "xi-kari.v4.run-contract", frozenset({"xi-kari.v4.run-contract"}),
    ),
    "xk-v4-production-status.schema.json": (
        "xi-kari.v4.run-status", frozenset({"xi-kari.v4.run-status"}),
    ),
    "xk-v4-production-validation-execution.schema.json": (
        "xi-kari.v4.validation-execution", frozenset({"xi-kari.v4.validation-execution"}),
    ),
    "xk-v4-production-validator.schema.json": (
        "xi-kari.v4.validator-report", frozenset({"xi-kari.v4.validator-report"}),
    ),
    "xk-v4-semantic-read-trace.schema.json": (
        "xi-kari.v4.semantic-read-trace", frozenset({"xi-kari.v4.semantic-read-trace"}),
    ),
    "xk-v4-semantic-execution-request.schema.json": (
        "xi-kari.v4.xk.semantic-execution-request", frozenset({"xi-kari.v4.xk.semantic-execution-request"}),
    ),
    "xk-v4-semantic-execution-response.schema.json": (
        "xi-kari.v4.xk.semantic-execution-response", frozenset(),
    ),
    "xk-v4-semantic-execution-receipt.schema.json": (
        "xi-kari.v4.xk.semantic-execution-receipt", frozenset({"xi-kari.v4.xk.semantic-execution-receipt"}),
    ),
    "xk-v4-semantic-execution-attestation.schema.json": (
        "xi-kari.v4.xk.semantic-execution-attestation", frozenset({"xi-kari.v4.xk.semantic-execution-attestation"}),
    ),
    "xk-v4-source.schema.json": (
        "xi-kari.v4.source-artifact",
        frozenset({"xi-kari.v4.source-lock", "xi-kari.v4.source-read-event"}),
    ),
    "xk-v4-stage-inputs.schema.json": ("xi-kari.v4.xk.stage-inputs", frozenset()),
}


def root_schema_ids(document: Any) -> set[str]:
    found: set[str] = set()
    visited: set[int] = set()

    def visit(schema: Any) -> None:
        if not isinstance(schema, dict) or id(schema) in visited:
            return
        visited.add(id(schema))
        properties = schema.get("properties")
        marker = properties.get("schema_id") if isinstance(properties, dict) else None
        if isinstance(marker, dict) and isinstance(marker.get("const"), str):
            found.add(marker["const"])
        reference = schema.get("$ref")
        if isinstance(reference, str) and reference.startswith("#"):
            target = document
            pointer = unquote(reference[1:])
            if not pointer or pointer.startswith("/"):
                try:
                    for part in pointer.split("/")[1:]:
                        key = part.replace("~1", "/").replace("~0", "~")
                        target = target[int(key)] if isinstance(target, list) else target[key]
                except (KeyError, IndexError, TypeError, ValueError):
                    target = None
                visit(target)
        for keyword in ("allOf", "anyOf", "oneOf"):
            branches = schema.get(keyword)
            if isinstance(branches, list):
                for branch in branches:
                    visit(branch)
        for keyword in ("then", "else"):
            visit(schema.get(keyword))
        dependent = schema.get("dependentSchemas")
        if isinstance(dependent, dict):
            for branch in dependent.values():
                visit(branch)

    visit(document)
    return found


def schema_identity_errors(path: Path, schema: dict[str, Any]) -> list[str]:
    schema_uri = schema.get("$id")
    identifiers = root_schema_ids(schema)
    expected = V4_SCHEMA_IDENTITIES.get(path.name)
    if expected is not None:
        identity, root_ids = expected
        if schema_uri != f"https://xi-kari.local/schemas/{identity}.schema.json":
            return [f"runtime schema has an unsupported $id: {path}: {schema_uri}"]
        if identifiers != root_ids:
            return [f"runtime schema root identity mismatch: {path}: {sorted(identifiers)}"]
        return []
    if not isinstance(schema_uri, str) or not re.fullmatch(
        r"https://xi-kari\.local/schemas/xi-kari\.v3\.[a-z0-9.-]+\.schema\.json",
        schema_uri,
    ):
        return [f"runtime schema has an unsupported $id: {path}: {schema_uri}"]
    return [
        f"runtime schema has an unsupported root schema_id: {path}: {identifier}"
        for identifier in sorted(identifiers)
        if not re.fullmatch(r"xi-kari\.v3\.[a-z0-9.-]+", identifier)
    ]


def schema_reference_errors(
    path: Path, schema: dict[str, Any], registry: Registry[Any]
) -> list[str]:
    errors: list[str] = []
    resource = Resource.from_contents(schema)

    def visit(current: Resource[Any], resolver: Any) -> None:
        if isinstance(current.contents, dict):
            for keyword in ("$ref", "$dynamicRef"):
                reference = current.contents.get(keyword)
                if isinstance(reference, str):
                    try:
                        resolver.lookup(reference)
                    except Exception as exc:
                        errors.append(
                            f"invalid runtime schema reference {path}: {reference}: {exc}"
                        )
        for child in current.subresources():
            visit(child, resolver.in_subresource(child))

    visit(resource, registry.resolver_with_root(resource))
    return errors
