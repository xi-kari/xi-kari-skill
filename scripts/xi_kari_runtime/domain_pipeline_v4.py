"""Exact domain-byte intake and problem-bound version-four authoring assembly."""

from __future__ import annotations

import base64
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
import secrets
from typing import Any

from .authority import repository_root as checked_repository_root
from .canonical_json import read_json_text
from .domains import (
    DomainReadError, build_domain_claim_links, build_domain_read_plan,
    build_domain_read_trace, domain_authority_binding, domain_content_witness,
    domain_reader_records, read_domain_item_bytes, validate_domain_authority,
    validate_domain_claim_links, validate_domain_claim_run, validate_domain_read_trace,
)
from .problem_contract import contract_hash


def _root(value: Path) -> Path:
    try:
        return checked_repository_root(Path(value))
    except (TypeError, ValueError, OSError) as exc:
        raise DomainReadError("domain pipeline repository root is invalid") from exc


def _contract(plan: Mapping[str, Any], run_contract: Mapping[str, Any]) -> str:
    if not isinstance(plan, Mapping) or not isinstance(run_contract, Mapping):
        raise DomainReadError("domain pipeline plan and run contract must be objects")
    if not isinstance(run_contract.get("run_id"), str) or not run_contract["run_id"].strip():
        raise DomainReadError("domain pipeline run identity is missing")
    if plan.get("run_id") != run_contract["run_id"]:
        raise DomainReadError("domain pipeline run binding differs from the current run")
    problem_hash = run_contract.get("problem_contract_sha256")
    if not isinstance(problem_hash, str) or plan.get("problem_contract_sha256") != problem_hash:
        raise DomainReadError("domain pipeline problem binding differs from the current problem")
    if "problem_contract" in run_contract:
        problem = run_contract["problem_contract"]
        if not isinstance(problem, Mapping) or contract_hash(problem) != problem_hash:
            raise DomainReadError("domain pipeline problem content differs from its frozen hash")
    mode = run_contract.get("mode")
    if mode not in {"open-world", "closed-input"}:
        raise DomainReadError("domain pipeline evidence mode must be explicit")
    return mode


def prepare_domain_inputs(selected_domain_ids: Sequence[str], *, run_id: str,
        problem_contract_sha256: str, repository_root: Path) -> dict[str, Any]:
    """Load selected indexed bytes before authoring; return no reading claim."""
    root = _root(repository_root)
    plan = build_domain_read_plan(root, domain_ids=selected_domain_ids,
        run_id=run_id, problem_contract_sha256=problem_contract_sha256,
        challenge=secrets.token_hex(32))
    author_inputs = []
    for record in plan["records"]:
        raw = read_domain_item_bytes(root, record)
        author_inputs.append({"domain_id": record["domain_id"],
            "content_utf8": raw.decode("utf-8"),
            "content_bytes_base64": base64.b64encode(raw).decode("ascii"),
            "content_witness": domain_content_witness(plan, record, raw)})
    return {"plan": plan, "author_inputs": author_inputs}


def validate_domain_inputs(plan: Mapping[str, Any], trace: Mapping[str, Any], *,
        graph: Mapping[str, Any], run_contract: Mapping[str, Any], repository_root: Path,
        verified_instance_results: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Stamp author semantics or revalidate persisted controls against current bytes."""
    root = _root(repository_root)
    mode = _contract(plan, run_contract)
    if not isinstance(trace, Mapping):
        raise DomainReadError("domain pipeline trace envelope must be an object")
    if set(trace) == {"records", "claim_links"}:
        read_trace = build_domain_read_trace(root, plan, trace["records"])
        authority = domain_authority_binding(root, plan)
        claim_links = build_domain_claim_links(root, plan, read_trace, graph,
            trace["claim_links"], evidence_mode=mode,
            verified_instance_results=verified_instance_results)
    elif set(trace) == {"read_trace", "authority", "claim_links"}:
        read_trace = trace["read_trace"]
        authority = trace["authority"]
        claim_links = trace["claim_links"]
        validate_domain_authority(root, plan, authority)
        validate_domain_read_trace(root, plan, read_trace)
        validate_domain_claim_links(root, plan, read_trace, graph, claim_links,
            evidence_mode=mode, verified_instance_results=verified_instance_results)
    else:
        raise DomainReadError("domain pipeline trace envelope contains missing or runtime-controlled fields")
    return {"read_trace": deepcopy(dict(read_trace)),
        "authority": deepcopy(dict(authority)), "claim_links": deepcopy(dict(claim_links)),
        "domain_reader_records": domain_reader_records(read_trace),
        "result": {"domain_ids": [record["domain_id"] for record in read_trace["records"]],
            "plan_sha256": plan["plan_sha256"], "trace_sha256": read_trace["trace_sha256"],
            "fingerprint_sha256": authority["fingerprint_sha256"],
            "claim_graph_sha256": claim_links["claim_graph_sha256"],
            "claim_links_sha256": claim_links["binding_sha256"]}}


def validate_materialized_domain_inputs(run_directory: Path, *,
        run_contract: Mapping[str, Any], repository_root: Path,
        verified_instance_results: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Re-read an external run's source, controls, final graph and domain prose."""
    root = _root(repository_root)
    run = _root(run_directory)
    if not isinstance(run_contract, Mapping):
        raise DomainReadError("domain pipeline run contract must be an object")
    validate_domain_claim_run(root, run,
        problem_contract_sha256=run_contract.get("problem_contract_sha256"),
        run_id=run_contract.get("run_id"), evidence_mode=run_contract.get("mode"),
        verified_instance_results=verified_instance_results)

    def load(name: str) -> Any:
        try:
            path = run / name
            if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
                raise ValueError("unsafe run artifact")
            return read_json_text(path.read_bytes().decode("utf-8"))
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            raise DomainReadError(f"domain pipeline cannot read materialized {name}") from exc

    return validate_domain_inputs(load("domain-read-plan.json"),
        {"read_trace": load("domain-read-trace.json"),
         "authority": load("domain-authority.json"),
         "claim_links": load("domain-claim-links.json")},
        graph=load("claim-mechanism-graph.json"), run_contract=run_contract,
        repository_root=root, verified_instance_results=verified_instance_results)
