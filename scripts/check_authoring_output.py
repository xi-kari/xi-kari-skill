#!/usr/bin/env python3
"""Read-only author feedback for the base semantic output, without run authority."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from copy import deepcopy
import json
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


def check_output(path: Path, repository_root: Path) -> dict:
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
        "scope": "Schema, answer identities, closed-input claim/source/evidence reference preview, static/dynamic delivery boundaries, provenance shape, disclosure and authored body coverage only. The preview trusts declared inputs and creates no receipts; frozen material authenticity, source reading, host observations, complete semantic execution and sealing require runtime validation.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = check_output(args.output, Path(__file__).resolve().parents[1])
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
