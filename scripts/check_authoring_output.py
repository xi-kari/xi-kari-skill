#!/usr/bin/env python3
"""Read-only author feedback for the base semantic output, without run authority."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from copy import deepcopy
import json
from itertools import islice
from pathlib import Path
import sys

sys.dont_write_bytecode = True

from xi_kari_runtime.canonical_json import read_bounded_regular_file, read_json_text
from xi_kari_runtime.contracts import (
    validate_answer_basis_references, validate_delivery_binding,
    validate_packet_references, validate_provenance,
)
from xi_kari_runtime.evidence import build_evidence_ledger, validate_evidence_ledger
from xi_kari_runtime.retrieval import validate_source_assessment_payload
from xi_kari_runtime.semantic_projection import (
    validate_reader_section_privacy, validate_reader_sections, validate_visibility_ledger,
)
from xi_kari_runtime.world_volume import _schema_validator, world_evidence_target_hashes


def check_closed_references(packet: Mapping, repository_root: Path) -> None:
    """Preview local identities, without receipts or accepting material authenticity."""

    retrieval = packet["retrieval"]
    assessments = {row["source_id"]: row for row in retrieval["assessments"]}
    sources = []
    for source in retrieval["sources"]:
        assessment = assessments[source["source_id"]]
        verdict = assessment["verdict"]
        sources.append({**source, "assessment_verdict": "admitted" if verdict == "usable" else verdict,
                        "independence_identity": assessment.get("independence_identity")})
    preview_index = {"run_id": "authoring-preflight", "sources": sources}
    claims = deepcopy(packet["evidence"]["claims"])
    dynamic = packet.get("dynamic_applicability") == "applicable"
    if not dynamic:
        for claim in claims:
            claim["world_targets"] = []
    ledger = build_evidence_ledger(
        run_id="authoring-preflight", claims=claims, retrieval_index=preview_index,
        world_target_hashes=world_evidence_target_hashes(packet["local_world_model"]) if dynamic else None,
    )
    problems = validate_evidence_ledger(ledger, preview_index)
    if problems:
        raise ValueError("evidence preview: " + "; ".join(problems))
    validate_packet_references(packet, evidence_ledger=ledger, retrieval_index=preview_index,
                               repository_root=repository_root)


def _check_legacy_output(path: Path, repository_root: Path) -> dict:
    errors: list[str] = []
    try:
        value = read_json_text(read_bounded_regular_file(path, limit=16 * 1024 * 1024).decode("utf-8"))
        validator = _schema_validator("xk-base-authoring-output.schema.json", str(repository_root))
        errors.extend(
            f"schema {list(error.absolute_path)}: {error.message}"
            for error in sorted(validator.iter_errors(value), key=lambda error: str(list(error.absolute_path)))
        )
        packet = value.get("semantic_packet") if isinstance(value, Mapping) else None
        if isinstance(packet, Mapping):
            for check in (validate_answer_basis_references, validate_delivery_binding, validate_visibility_ledger, validate_reader_section_privacy):
                try:
                    check(packet)
                except (ValueError, TypeError, KeyError) as error:
                    errors.append(str(error))
            retrieval = packet.get("retrieval", {})
            if isinstance(retrieval, Mapping):
                try:
                    validate_provenance(packet, mode=retrieval.get("mode", "open-world"))
                except (ValueError, TypeError, KeyError, AttributeError) as error:
                    errors.append(str(error))
                sources = retrieval.get("sources", [])
                source_ids = {row.get("source_id") for row in sources
                              if isinstance(row, Mapping) and isinstance(row.get("source_id"), str)}
                for assessment in retrieval.get("assessments", []):
                    try:
                        validate_source_assessment_payload(
                            assessment, source_ids=source_ids,
                            require_provenance=(retrieval.get("mode") == "open-world"
                                                and packet.get("dynamic_applicability") == "applicable"
                                                and packet.get("problem_contract", {}).get("retrieval_profile") == "five-direction"),
                        )
                    except (ValueError, TypeError, KeyError, AttributeError) as error:
                        errors.append(str(error))
                if retrieval.get("mode") == "closed-input":
                    try:
                        check_closed_references(packet, repository_root)
                    except (ValueError, TypeError, KeyError, AttributeError) as error:
                        errors.append(str(error))
            try:
                errors.extend(validate_reader_sections(packet))
            except (ValueError, TypeError, KeyError) as error:
                errors.append(str(error))
    except (OSError, UnicodeError, ValueError, TypeError) as error:
        errors.append(str(error))
    return {
        "passed": not errors, "errors": errors, "runtime_sealed": False,
        "contract_version": 3, "schema": "xk-base-authoring-output.schema.json",
        "scope": "Schema, answer identities, closed-input claim/source/evidence reference preview, static/dynamic delivery boundaries, provenance shape, disclosure and authored body coverage only. The preview trusts declared inputs and creates no receipts; frozen material authenticity, source reading, host observations, complete semantic execution and sealing require runtime validation.",
    }


def _check_v4_output(path: Path, repository_root: Path, *, context_path: Path | None,
                     context_sha256: str | None) -> dict:
    from xi_kari_runtime.authoring_support_v4 import read_authoring_context_v4
    from xi_kari_runtime.execution import parse_base_authoring_output
    from xi_kari_runtime.ontology_read_trace import build_ontology_read_plan
    from xi_kari_runtime.problem_contract import contract_hash
    from xi_kari_runtime.retrieval import build_full_source_lock
    from xi_kari_runtime.canonical_json import sha256_json
    from xi_kari_runtime.v4_contracts import _schema_failure
    errors: list[str] = []
    checks = {name: "not_checked" for name in ("schema", "frozen_context", "author_contract_and_read_traces", "reader_and_visibility")}
    truncated = False
    try:
        raw = read_bounded_regular_file(path, limit=16 * 1024 * 1024)
        value = read_json_text(raw.decode("utf-8"))
        validator = _schema_validator("xk-v4-base-authoring-output.schema.json", str(repository_root))
        violations = list(islice(validator.iter_errors(value), 41))
        truncated = len(violations) > 40
        errors.extend(_schema_failure(error, "version-four authoring output") for error in violations[:40])
        checks["schema"] = "failed" if violations else "passed"
        if context_path is None or context_sha256 is None:
            errors.append("version-four preflight requires the runtime-prepared --context and --context-sha256 from runtime-inputs/support.json")
        elif not violations:
            context = read_authoring_context_v4(context_path, expected_sha256=context_sha256)
            request = context["request"]
            if Path(request["source_inputs"]["repository_root"]).resolve() != repository_root.resolve():
                raise ValueError("authoring context repository differs from the validator repository")
            request_validator = _schema_validator("xk-v4-base-authoring-request.schema.json", str(repository_root))
            invalid_request = next(request_validator.iter_errors(request), None)
            if invalid_request is not None:
                raise ValueError(_schema_failure(invalid_request, "frozen authoring request"))
            plan_binding = request["source_inputs"]["ontology_read_plan"]
            problem_sha256 = contract_hash(request["problem_contract"])
            if plan_binding["problem_contract_sha256"] != problem_sha256:
                raise ValueError("frozen ontology plan differs from the actual problem contract")
            plan = build_ontology_read_plan(repository_root, run_id=request["run_id"], source_version="v9.0",
                problem_contract_sha256=problem_sha256, content_access_challenge=plan_binding["content_access_challenge"])
            if sha256_json(plan) != plan_binding["plan_sha256"]:
                raise ValueError("rebuilt ontology plan differs from the frozen source binding")
            bound_lock = request["source_inputs"]["source_lock"]
            source_lock, source_events = build_full_source_lock(repository_root, run_id=bound_lock["run_id"], source_version="v9.0")
            if source_lock != bound_lock:
                raise ValueError("rebuilt source lock differs from the frozen source binding")
            checks["frozen_context"] = "passed"
            packet, _, _ = parse_base_authoring_output(raw, problem_contract=request["problem_contract"],
                mode=request["mode"], ontology_read_plan=plan,
                repository_root=repository_root, natural_request=request.get("natural_request"),
                source_lock=source_lock, source_events=source_events,
                contract_version=4)
            checks["author_contract_and_read_traces"] = "passed"
            validate_visibility_ledger(packet, expected_purpose=request["privacy_contract"]["purpose"])
            validate_reader_section_privacy(packet)
            errors.extend(validate_reader_sections(packet))
            checks["reader_and_visibility"] = "failed" if errors else "passed"
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, AttributeError) as error:
        errors.append(str(error))
    return {
        "passed": not errors and all(status == "passed" for status in checks.values()),
        "errors": errors[:40], "errors_truncated": truncated or len(errors) > 40,
        "checks": checks, "runtime_sealed": False, "contract_version": 4,
        "schema": "xk-v4-base-authoring-output.schema.json",
        "scope": "Read-only preview against actual v4 schemas, the code-prepared frozen request, claim/reference checks, source/ontology trace validators, disclosure and reader coverage. It writes no output, repairs no values, generates no read trace or receipt, and grants no runtime seal or external fact/authorization.",
    }


def check_output(path: Path, repository_root: Path, *, contract_version: int | None = None,
                 context_path: Path | None = None, context_sha256: str | None = None) -> dict:
    if contract_version is None:
        try:
            value = read_json_text(read_bounded_regular_file(path, limit=16 * 1024 * 1024).decode("utf-8"))
            marker = value.get("semantic_read_trace", {}).get("schema_id", "")
            contract_version = 4 if marker == "xi-kari.v4.semantic-read-trace-input" or context_path is not None else 3
        except (OSError, UnicodeError, ValueError, TypeError, AttributeError):
            contract_version = 4 if context_path is not None else 3
    if contract_version == 4:
        return _check_v4_output(path, repository_root, context_path=context_path, context_sha256=context_sha256)
    if contract_version != 3 or context_path is not None or context_sha256 is not None:
        return {"passed": False, "errors": ["author preflight contract and context versions differ"],
                "runtime_sealed": False, "contract_version": contract_version,
                "scope": "No authoring contract was accepted."}
    return _check_legacy_output(path, repository_root)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--contract-version", type=int, choices=(3, 4))
    parser.add_argument("--context", type=Path)
    parser.add_argument("--context-sha256")
    parser.add_argument("--describe", action="store_true", help="Print actual v4 schema responsibilities without generating an output template")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.describe:
        if args.contract_version == 3:
            parser.error("--describe provides the current version-four contract only")
        from xi_kari_runtime.authoring_support_v4 import describe_authoring_contract_v4
        print(json.dumps(describe_authoring_contract_v4(root), ensure_ascii=False, indent=2))
        return 0
    if args.output is None:
        parser.error("output is required unless --describe is selected")
    report = check_output(args.output, root, contract_version=args.contract_version,
                          context_path=args.context, context_sha256=args.context_sha256)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
