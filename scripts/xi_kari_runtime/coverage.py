"""Coverage accounting for source reads, assessments, support, and outputs."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .prose import build_reader_trace
from .source_profile import get_source_profile
from .semantic_projection import (
    authored_reader_units,
    substantive_semantic_atoms,
    typed_semantic_atoms,
    validate_reader_sections,
)


REQUIRED_OUTPUTS = ("answer", "dossier", "atlas", "casebook")
READER_OUTPUT_PATHS = {
    "answer": "delivery/xi-kari-answer.md",
    "dossier": "delivery/xi-kari-dossier.md",
    "atlas": "delivery/xi-kari-concept-atlas.md",
    "casebook": "delivery/xi-kari-case-and-countercase.md",
}


def build_coverage(
    *,
    run_id: str,
    source_lock: dict[str, Any],
    retrieval_index: dict[str, Any],
    evidence_ledger: dict[str, Any],
    planned_outputs: list[str] | tuple[str, ...] = REQUIRED_OUTPUTS,
) -> dict[str, Any]:
    receipts = source_lock.get("reader_receipts", source_lock.get("receipts", []))
    mismatched = [
        item.get("unit")
        for item in receipts
        if item.get("expected_sha256") != item.get("observed_sha256")
    ]
    sources = retrieval_index.get("sources", [])
    unsupported = list(evidence_ledger.get("unsupported_claims", []))
    outputs = list(planned_outputs)
    missing_outputs = sorted(set(REQUIRED_OUTPUTS) - set(outputs))
    complete = (
        source_lock.get("complete") is True
        and source_lock.get("reader_unit_count") == len(receipts)
        and source_lock.get("source_unit_count") == 4753
        and not mismatched
        and retrieval_index.get("source_count") == len(sources)
        and retrieval_index.get("all_sources_assessed") is True
        and not missing_outputs
    )
    return {
        "schema_id": "xi-kari.v3.coverage",
        "schema_version": 3,
        "run_id": run_id,
        "source_read": {
            "expected": source_lock.get("reader_unit_count"),
            "observed": len(receipts),
            "source_units_expected": 4753,
            "source_units_observed": source_lock.get("source_unit_count"),
            "mismatched": mismatched,
            "complete": source_lock.get("complete") is True and not mismatched,
        },
        "source_assessment": {
            "sources": len(sources),
            "assessments": len(sources) if retrieval_index.get("all_sources_assessed") else 0,
            "unassessed": [] if retrieval_index.get("all_sources_assessed") else ["unknown"],
        },
        "claim_support": {
            "claims": len(evidence_ledger.get("claims", [])),
            "supported": len(evidence_ledger.get("claims", [])) - len(unsupported),
            "unsupported": unsupported,
        },
        "outputs": {"required": list(REQUIRED_OUTPUTS), "planned": outputs, "missing": missing_outputs},
        "complete": complete,
    }


def build_coverage_v4(
    *, run_id: str, source_lock: dict[str, Any], retrieval_index: dict[str, Any],
    evidence_ledger: dict[str, Any],
    planned_outputs: list[str] | tuple[str, ...] = REQUIRED_OUTPUTS,
) -> dict[str, Any]:
    """Account for source-nine intake after the source lock's independent validation."""

    profile = get_source_profile('v9.0')
    result = build_coverage(run_id=run_id, source_lock=source_lock,
        retrieval_index=retrieval_index, evidence_ledger=evidence_ledger,
        planned_outputs=planned_outputs)
    result.update(schema_id='xi-kari.v4.coverage', schema_version=4)
    read = result['source_read']
    read.update(expected=profile.expected_reader_units,
                source_units_expected=profile.expected_paragraphs + profile.expected_tables)
    identity_matches = (source_lock.get('framework_version') == profile.source_version
        and source_lock.get('source_raw_sha256') == profile.raw_sha256
        and source_lock.get('paragraph_count') == profile.expected_paragraphs
        and source_lock.get('table_count') == profile.expected_tables)
    receipts = source_lock.get('reader_receipts', [])
    receipt_units = [item.get('unit') for item in receipts]
    ordered_receipts = (len(receipt_units) == len(set(receipt_units))
        and receipt_units == source_lock.get('reader_sequence'))
    read['complete'] = (identity_matches and ordered_receipts
        and source_lock.get('complete') is True
        and source_lock.get('reader_unit_count') == read['expected'] == read['observed']
        and read['source_units_expected'] == read['source_units_observed']
        and not read['mismatched'])
    result['complete'] = (read['complete']
        and retrieval_index.get('source_count') == len(retrieval_index.get('sources', []))
        and retrieval_index.get('all_sources_assessed') is True
        and not result['outputs']['missing'])
    return result


def validate_coverage(coverage: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    source_read = coverage.get("source_read", {})
    if source_read.get("expected") != source_read.get("observed"):
        errors.append("source read coverage count mismatch")
    if source_read.get("mismatched"):
        errors.append("source read coverage contains mismatches")
    if source_read.get("source_units_expected") != source_read.get("source_units_observed"):
        errors.append('source unit coverage count mismatch' if coverage.get('schema_version') == 4
                      else 'source unit coverage is not 4753')
    if coverage.get('schema_version') == 4:
        profile = get_source_profile('v9.0')
        if (source_read.get('source_units_expected') != profile.expected_paragraphs + profile.expected_tables
                or source_read.get('expected') != profile.expected_reader_units
                or source_read.get('complete') is not True):
            errors.append('version-four source coverage is incomplete or differs from its source profile')
    source_assessment = coverage.get("source_assessment", {})
    if source_assessment.get("sources") != source_assessment.get("assessments"):
        errors.append("not every source has a separate assessment")
    if coverage.get("outputs", {}).get("missing"):
        errors.append("required readable output is missing from plan")
    if not coverage.get("complete"):
        errors.append("coverage is not complete")
    return errors


def load_reader_outputs(run_dir: Path) -> dict[str, str]:
    root = Path(run_dir)
    return {
        name: path.read_text(encoding="utf-8") if path.is_file() else ""
        for name, relative in READER_OUTPUT_PATHS.items()
        for path in (root / relative,)
    }


def build_semantic_coverage(
    *, run_id: str, packet: dict[str, Any], source_read_complete: bool,
    candidate_closure_complete: bool, reader_outputs: Mapping[str, str],
) -> dict[str, Any]:
    """Account for every substantive analysis atom against the actual full body."""

    errors = validate_reader_sections(packet)
    units = authored_reader_units(packet)
    trace = build_reader_trace(packet, units, dict(reader_outputs))
    trace["run_id"] = run_id
    matches = {item["output"]: item["matches_observed"] for item in trace["outputs"]}
    units_by_path: dict[str, list[str]] = {}
    for unit in units:
        for path in unit.get("source_paths", []):
            units_by_path.setdefault(path, []).append(unit["unit_id"])
    substantive = substantive_semantic_atoms(packet)
    graph = packet.get('claim_mechanism_graph')
    v4 = packet.get('schema_version') == 4 or (
        isinstance(graph, Mapping) and graph.get('schema_version') == 4)
    unprojected_paths = [atom["canonical_path"] for atom in substantive
        if (v4 or atom["projection_status"] != "withheld_for_protection")
        and atom["canonical_path"] not in units_by_path]
    typed_ledger = []
    for atom in typed_semantic_atoms(packet):
        unit_ids = sorted(set(units_by_path.get(atom["canonical_path"], [])))
        status = atom["projection_status"]
        if status != "withheld_for_protection":
            status = "projected" if unit_ids else "audit_only"
        typed_ledger.append({
            "canonical_path": atom["canonical_path"], "value_type": atom["value_type"],
            "visibility": atom["visibility"], "projection_status": status,
            "reader_unit_ids": unit_ids,
        })
    traced = {(entry["unit_id"], entry["output"], entry["fragment_index"])
              for entry in trace["entries"]}
    checks = []
    for unit in units:
        missing = [fragment for index, fragment in enumerate(unit["fragments"])
                   if not matches.get("answer") or (unit["unit_id"], "answer", index) not in traced]
        checks.append({
            "unit_id": unit["unit_id"], "unit_kind": unit["unit_kind"],
            "fragments": unit["fragments"], "required_outputs": ["answer"],
            "atom_statuses": [], "projected_outputs": [] if missing else ["answer"],
            "missing_fragments": missing, "complete": not missing,
        })
    unprojected = [item["unit_id"] for item in checks if not item["complete"]]
    unprojected.extend(f"substance:{path}" for path in unprojected_paths)
    if errors:
        unprojected.append("reader.authored.invalid")
    complete = bool(units) and not errors and not unprojected and matches.get("answer") is True
    stance = packet.get("stance_pair", {})
    stance_projection = {
        "preferred": stance.get("preferred"), "required_fragments": [],
        "missing_required_fragments": [], "forbidden_fragments": [],
        "present_forbidden_fragments": [], "complete": complete,
    }
    return {
        "schema_id": "xi-kari.v3.semantic-coverage", "schema_version": 3, "run_id": run_id,
        "dynamic_applicability": packet.get("dynamic_applicability"),
        "not_applicable_reason": packet.get("not_applicable_reason"),
        "conclusion_units": {"substantive_paths": [atom["canonical_path"] for atom in substantive]},
        "typed_atom_ledger": typed_ledger, "projection_checks": checks,
        "reader_trace": trace, "stance_projection": stance_projection,
        "unprojected_unit_ids": unprojected, "source_read_complete": source_read_complete,
        "candidate_closure_complete": candidate_closure_complete,
        "main_answer_complete": complete,
        "reader_projection_complete": complete and all(matches.values()),
        "substantive_unprojected_paths": unprojected_paths,
        "reader_section_errors": errors,
    }
