"""Problem-bound domain byte access, source identity, and reader responsibility."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import hashlib
import hmac
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from typing import Any

from .authority import repository_root
from .canonical_json import canonical_bytes, read_json_text, sha256_bytes, sha256_json
from .source_profile import get_source_profile


PLAN_SCHEMA_ID = "xi-kari.v4.domain-read-plan"
TRACE_SCHEMA_ID = "xi-kari.v4.domain-read-trace"
CONTENT_PROOF_KIND = "byte-access+problem-bound-semantic-trace"
DOMAIN_IDS = tuple(f"D.{ordinal:02d}" for ordinal in range(1, 33))
SEMANTIC_FIELDS = frozenset({"domain_id", "content_witness", "content_excerpt",
    "problem_relation", "reader_responsibilities"})
READER_RESPONSIBILITIES = frozenset({"native_method", "additional_distinction",
    "inputs_outputs", "limits_counterargument", "costs_exit"})
RELATION_STATUSES = frozenset({"applied", "boundary_only", "native_exit"})
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class DomainReadError(ValueError):
    """A domain source, content, access, or delivery binding is invalid."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainReadError(f"domain {field} must be nonempty text")
    return value


def _hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise DomainReadError(f"domain {field} must be a lowercase SHA-256")
    return value


def _path(root: Path, relative: Any) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise DomainReadError("domain path must be a relative POSIX path")
    parts = PurePosixPath(relative).parts
    if (PurePosixPath(relative).is_absolute() or PureWindowsPath(relative).drive
            or ".." in parts or ":" in relative or str(PurePosixPath(relative)) != relative):
        raise DomainReadError("domain path escapes its repository boundary")
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise DomainReadError("domain path contains a symlink or junction")
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(root)
        if not resolved.is_file():
            raise ValueError("not a file")
    except (OSError, ValueError) as exc:
        raise DomainReadError("domain file path is unavailable or outside repository") from exc
    return resolved


def _bytes(root: Path, relative: str) -> bytes:
    try:
        return _path(root, relative).read_bytes()
    except OSError as exc:
        raise DomainReadError("domain content file cannot be read") from exc


def _json(raw: bytes, label: str) -> Any:
    try:
        return read_json_text(raw.decode("utf-8"))
    except (ValueError, TypeError, UnicodeDecodeError) as exc:
        raise DomainReadError(f"domain {label} is invalid JSON") from exc


def _catalog(root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    source_root = "references/source/v9.0/"
    manifest_raw = _bytes(root, source_root + "source-manifest.json")
    manifest = _json(manifest_raw, "source manifest")
    expected_source = get_source_profile("v9.0").raw_sha256
    if not isinstance(manifest, dict) or manifest.get("raw_sha256") != expected_source:
        raise DomainReadError("domain source manifest identity differs from v9.0")
    indexes = {}
    for relative in ("indexes/anchors.json", "indexes/body-blocks.json"):
        raw = _bytes(root, source_root + relative)
        if sha256_bytes(raw) != manifest.get("index_file_sha256", {}).get(relative):
            raise DomainReadError("domain source index content differs from manifest")
        indexes[relative] = _json(raw, "source index")
    identity_raw = _bytes(root, "references/ontology/v9.0/authored/domain-identities.json")
    identity = _json(identity_raw, "P03 source identities")
    catalog_raw = _bytes(root, "references/domains/index.json")
    catalog = _json(catalog_raw, "catalog")
    if (not isinstance(identity, dict) or not isinstance(catalog, dict)
            or identity.get("source_raw_sha256") != expected_source
            or catalog.get("source_raw_sha256") != expected_source
            or catalog.get("framework_version") != "v9.0"
            or catalog.get("schema_id") != "xi-kari.v9.0.domain-index"
            or catalog.get("entry_count") != len(DOMAIN_IDS)):
        raise DomainReadError("domain catalog source identity is invalid")
    entries = catalog.get("entries")
    originals = identity.get("entries")
    if (not isinstance(entries, list) or not isinstance(originals, list)
            or [v.get("domain_id") for v in entries if isinstance(v, dict)] != list(DOMAIN_IDS)
            or [v.get("domain_id") for v in originals if isinstance(v, dict)] != list(DOMAIN_IDS)):
        raise DomainReadError("domain catalog must preserve the D.01-D.32 source identities")
    body_blocks = {v["anchor"]: v for v in indexes["indexes/body-blocks.json"]}
    paragraph_ids = set(indexes["indexes/anchors.json"]["paragraphs"])
    for entry, original in zip(entries, originals, strict=True):
        if any(entry.get(key) != value for key, value in original.items()):
            raise DomainReadError("domain source identity does not match P03")
        source_refs = entry.get("source_refs", [])
        for ref in source_refs:
            block = body_blocks.get(ref.get("body_anchor"))
            paragraphs = ref.get("paragraph_anchors")
            if (block is None or not isinstance(paragraphs, list)
                    or paragraphs != [block.get("paragraph_anchor")]
                    or not set(paragraphs).issubset(paragraph_ids)):
                raise DomainReadError("domain source reference does not resolve")
        payload = {key: entry[key] for key in ("domain_id", "source_refs", "candidate_ids")}
        if sha256_bytes(canonical_bytes(payload) + b"\n") != entry.get("source_fingerprint_sha256"):
            raise DomainReadError("domain source fingerprint does not match P03")
    return catalog, {"source_raw_sha256": expected_source,
        "source_manifest_sha256": sha256_bytes(manifest_raw),
        "domain_catalog_sha256": sha256_bytes(catalog_raw),
        "p03_identity_sha256": sha256_bytes(identity_raw)}


def _record(entry: Mapping[str, Any]) -> dict[str, Any]:
    expected_path = f"references/learning-packs/domains/{entry['domain_id']}.md"
    if entry.get("content_path") != expected_path:
        raise DomainReadError("domain content path must match its exact indexed identity")
    if entry.get("content_status") != "available":
        raise DomainReadError("domain content is not available in the catalog")
    _hash(entry.get("content_sha256"), "content hash")
    return {"domain_id": entry["domain_id"], "identity_id": entry["identity_id"],
        "path": expected_path, "content_sha256": entry["content_sha256"],
        **{key: deepcopy(entry[key]) for key in ("source_fingerprint_sha256",
            "source_anchors", "source_refs", "candidate_ids", "primary_candidate_id")}}


def read_domain_item_bytes(repository: Path, record: Mapping[str, Any]) -> bytes:
    """Read exact indexed bytes; metadata and file presence alone are insufficient."""
    try:
        root = repository_root(repository)
    except ValueError as exc:
        raise DomainReadError("domain repository path is invalid") from exc
    domain_id = record.get("domain_id") if isinstance(record, Mapping) else None
    if domain_id not in DOMAIN_IDS or record.get("path") != f"references/learning-packs/domains/{domain_id}.md":
        raise DomainReadError("domain content path or identity is invalid")
    raw = _bytes(root, record["path"])
    if sha256_bytes(raw) != record.get("content_sha256"):
        raise DomainReadError("domain content hash differs from the indexed binding")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DomainReadError("domain content is not UTF-8") from exc
    if not text.startswith(f"# {domain_id} "):
        raise DomainReadError("domain content title identity is invalid")
    return raw


def build_domain_read_plan(repository: Path, *, domain_ids: Sequence[str],
        problem_contract_sha256: str, run_id: str, challenge: str) -> dict[str, Any]:
    """Select only requested domains; an empty route permits a native-method exit."""
    if isinstance(domain_ids, (str, bytes)) or not isinstance(domain_ids, Sequence):
        raise DomainReadError("domain routing must be an explicit sequence")
    if any(not isinstance(value, str) or value not in DOMAIN_IDS for value in domain_ids):
        raise DomainReadError("domain routing contains an unknown or research-topic identity")
    if len(set(domain_ids)) != len(domain_ids):
        raise DomainReadError("domain routing repeats an identity")
    _hash(problem_contract_sha256, "problem contract hash")
    _hash(challenge, "access challenge")
    _text(run_id, "run identity")
    try:
        root = repository_root(repository)
    except ValueError as exc:
        raise DomainReadError("domain repository path is invalid") from exc
    catalog, binding = _catalog(root)
    lookup = {entry["domain_id"]: entry for entry in catalog["entries"]}
    records = [_record(lookup[domain_id]) for domain_id in domain_ids]
    for record in records:
        read_domain_item_bytes(root, record)
    result = {"schema_id": PLAN_SCHEMA_ID, "schema_version": 1,
        "framework_version": "v9.0", **binding, "run_id": run_id,
        "problem_contract_sha256": problem_contract_sha256,
        "challenge": challenge, "records": records}
    result["plan_sha256"] = sha256_json(result)
    return result


def _validate_plan(repository: Path, plan: Mapping[str, Any]) -> None:
    if not isinstance(plan, Mapping) or not isinstance(plan.get("records"), list):
        raise DomainReadError("domain plan binding is invalid")
    try:
        expected = build_domain_read_plan(repository,
            domain_ids=[record["domain_id"] for record in plan["records"]],
            problem_contract_sha256=plan["problem_contract_sha256"],
            run_id=plan["run_id"], challenge=plan["challenge"])
    except (KeyError, TypeError) as exc:
        raise DomainReadError("domain plan binding is incomplete") from exc
    if expected != dict(plan):
        raise DomainReadError("domain plan binding differs from current disk authority")


def domain_content_witness(plan: Mapping[str, Any], record: Mapping[str, Any], raw: bytes) -> str:
    """Bind byte access to this run and problem; this does not prove understanding."""
    challenge = _hash(plan.get("challenge"), "access challenge")
    payload = canonical_bytes({"protocol": "xi-kari.v4.domain-content-witness/1",
        "run_id": plan["run_id"], "problem_contract_sha256": plan["problem_contract_sha256"],
        "domain_id": record["domain_id"], "content_sha256": record["content_sha256"]})
    return hmac.new(bytes.fromhex(challenge), payload + b"\0" + raw, hashlib.sha256).hexdigest()


def build_domain_read_trace(repository: Path, plan: Mapping[str, Any],
        semantic_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate author semantic fields and stamp control bindings from disk."""
    _validate_plan(repository, plan)
    if (not isinstance(semantic_records, (list, tuple))
            or len(semantic_records) != len(plan["records"])):
        raise DomainReadError("domain trace coverage does not match the selected route")
    records = []
    for controlled, semantic in zip(plan["records"], semantic_records, strict=True):
        if not isinstance(semantic, Mapping) or set(semantic) != SEMANTIC_FIELDS:
            raise DomainReadError("domain semantic fields contain missing or runtime-controlled fields")
        if semantic["domain_id"] != controlled["domain_id"]:
            raise DomainReadError("domain trace routing identity differs from plan")
        raw = read_domain_item_bytes(repository, controlled)
        witness = domain_content_witness(plan, controlled, raw)
        if not isinstance(semantic["content_witness"], str) or not hmac.compare_digest(witness, semantic["content_witness"]):
            raise DomainReadError("domain byte access witness is invalid")
        excerpt = _text(semantic["content_excerpt"], "content excerpt")
        if excerpt not in raw.decode("utf-8"):
            raise DomainReadError("domain content excerpt is not in the loaded bytes")
        relation = semantic["problem_relation"]
        if (not isinstance(relation, Mapping) or set(relation) != {"status", "rationale"}
                or relation.get("status") not in RELATION_STATUSES):
            raise DomainReadError("domain problem relation fields or status are invalid")
        _text(relation["rationale"], "problem relation rationale")
        responsibilities = semantic["reader_responsibilities"]
        if not isinstance(responsibilities, Mapping) or set(responsibilities) != READER_RESPONSIBILITIES:
            raise DomainReadError("domain reader responsibility fields are incomplete")
        for key, value in responsibilities.items():
            _text(value, f"reader responsibility {key}")
        records.append({**deepcopy(dict(controlled)), **deepcopy(dict(semantic))})
    result = {"schema_id": TRACE_SCHEMA_ID, "schema_version": 1,
        "content_proof_kind": CONTENT_PROOF_KIND, "plan_sha256": plan["plan_sha256"],
        "run_id": plan["run_id"], "problem_contract_sha256": plan["problem_contract_sha256"],
        "source_raw_sha256": plan["source_raw_sha256"], "records": records}
    result["trace_sha256"] = sha256_json(result)
    return result


def validate_domain_read_trace(repository: Path, plan: Mapping[str, Any],
        trace: Mapping[str, Any], *, reader_text: str | None = None) -> None:
    """Re-read the catalog and content; reject stale controls and omitted prose."""
    if not isinstance(trace, Mapping) or not isinstance(trace.get("records"), list):
        raise DomainReadError("domain trace binding is invalid")
    try:
        semantics = [{key: record[key] for key in SEMANTIC_FIELDS} for record in trace["records"]]
    except (KeyError, TypeError) as exc:
        raise DomainReadError("domain trace binding is incomplete") from exc
    expected = build_domain_read_trace(repository, plan, semantics)
    if expected != dict(trace):
        raise DomainReadError("domain trace binding differs from current disk controls")
    if reader_text is not None:
        _text(reader_text, "reader text")
        for record in expected["records"]:
            for value in record["reader_responsibilities"].values():
                if value.replace("\r\n", "\n") not in reader_text.replace("\r\n", "\n"):
                    raise DomainReadError("domain reader text omits an attested responsibility")


def domain_reader_records(trace: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return only domain semantics for the trusted typed-visibility consumer."""
    return [{key: deepcopy(record[key]) for key in ("domain_id", "problem_relation",
        "reader_responsibilities")} for record in trace["records"]]


def domain_authority_binding(repository: Path, plan: Mapping[str, Any]) -> dict[str, Any]:
    """Fingerprint selected content and its frozen source and problem identities."""
    _validate_plan(repository, plan)
    value = {"schema_id": "xi-kari.v4.domain-authority", "schema_version": 1,
        **{key: plan[key] for key in ("plan_sha256", "domain_catalog_sha256",
            "source_manifest_sha256", "p03_identity_sha256", "source_raw_sha256")},
        "records": [{key: record[key] for key in ("domain_id", "content_sha256",
            "source_fingerprint_sha256")} for record in plan["records"]]}
    value["fingerprint_sha256"] = sha256_json(value)
    return value


def validate_domain_authority(repository: Path, plan: Mapping[str, Any], binding: Mapping[str, Any]) -> None:
    if domain_authority_binding(repository, plan) != binding:
        raise DomainReadError("domain authority binding differs from current disk content")


def validate_domain_run(repository: Path, run_directory: Path, *,
        problem_contract_sha256: str, run_id: str) -> dict[str, Any]:
    """Validate materialized domain artifacts and prose from an external run."""
    try:
        root = repository_root(repository)
        run = repository_root(run_directory)
    except ValueError as exc:
        raise DomainReadError("domain run path is invalid") from exc
    if run.is_relative_to(root) or root.is_relative_to(run):
        raise DomainReadError("domain run must be outside the product repository")
    _hash(problem_contract_sha256, "problem contract hash")
    _text(run_id, "run identity")
    plan = _json(_bytes(run, "domain-read-plan.json"), "materialized plan")
    trace = _json(_bytes(run, "domain-read-trace.json"), "materialized trace")
    binding = _json(_bytes(run, "domain-authority.json"), "materialized authority")
    if not isinstance(plan, dict) or plan.get("problem_contract_sha256") != problem_contract_sha256:
        raise DomainReadError("domain run problem binding differs from the current problem")
    if plan.get("run_id") != run_id:
        raise DomainReadError("domain run identity differs from the current run")
    try:
        reader = _bytes(run, "xi-kari-answer.md").decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DomainReadError("domain reader artifact is not UTF-8") from exc
    validate_domain_authority(root, plan, binding)
    validate_domain_read_trace(root, plan, trace, reader_text=reader)
    return {"domain_ids": [record["domain_id"] for record in plan["records"]],
        "plan_sha256": plan["plan_sha256"], "trace_sha256": trace["trace_sha256"],
        "fingerprint_sha256": binding["fingerprint_sha256"]}


def build_domain_claim_links(repository: Path, plan: Mapping[str, Any],
        trace: Mapping[str, Any], claim_graph: Mapping[str, Any],
        links: Sequence[Mapping[str, Any]], *, evidence_mode: str = "open-world",
        verified_instance_results: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Bind domain method use to P04 claims without manufacturing evidence or status."""
    from .claims import validate_claim_graph

    validate_domain_read_trace(repository, plan, trace)
    if not isinstance(claim_graph, Mapping) or claim_graph.get("schema_version") != 4:
        raise DomainReadError("domain-linked claims require the public P04 v4 contract")
    if not isinstance(links, (list, tuple)) or len(links) != len(trace["records"]):
        raise DomainReadError("domain claim-link coverage differs from the actual read route")
    known_claims = {claim.get("claim_id") for claim in claim_graph.get("claims", [])
                    if isinstance(claim, Mapping)}
    normalized_links = []
    for link, record in zip(links, trace["records"], strict=True):
        if not isinstance(link, Mapping) or set(link) != {"domain_id", "claim_ids", "use_kind", "rationale"}:
            raise DomainReadError("domain claim-link fields are invalid")
        if link["domain_id"] != record["domain_id"]:
            raise DomainReadError("domain claim-link identity is not in the actual read route")
        if link["use_kind"] not in {"method_reference", "boundary_reference", "native_exit"}:
            raise DomainReadError("domain use cannot serve as empirical evidence or formal qualification")
        if link["use_kind"] == "native_exit" and record["problem_relation"]["status"] != "native_exit":
            raise DomainReadError("domain native exit differs from its read trace")
        refs = link["claim_ids"]
        if (not isinstance(refs, list) or not refs or any(not isinstance(v, str) for v in refs)
                or len(set(refs)) != len(refs) or set(refs) - known_claims):
            raise DomainReadError("domain claim references must resolve to distinct P04 claims")
        _text(link["rationale"], "claim-link rationale")
        normalized_links.append(deepcopy(dict(link)))
    try:
        checked = validate_claim_graph(claim_graph, evidence_mode=evidence_mode,
            repository_root=Path(repository), verified_instance_results=verified_instance_results)
    except ValueError as exc:
        raise DomainReadError("public P04 validation rejected a domain-linked claim graph") from exc
    value = {"schema_id": "xi-kari.v4.domain-claim-links", "schema_version": 1,
        "plan_sha256": plan["plan_sha256"], "trace_sha256": trace["trace_sha256"],
        "claim_graph_sha256": sha256_json(checked), "evidence_mode": evidence_mode,
        "links": normalized_links}
    value["binding_sha256"] = sha256_json(value)
    return value


def validate_domain_claim_links(repository: Path, plan: Mapping[str, Any],
        trace: Mapping[str, Any], claim_graph: Mapping[str, Any], binding: Mapping[str, Any],
        *, evidence_mode: str = "open-world",
        verified_instance_results: Mapping[str, Any] | None = None) -> None:
    if not isinstance(binding, Mapping):
        raise DomainReadError("domain claim-link binding is invalid")
    expected = build_domain_claim_links(repository, plan, trace, claim_graph,
        binding.get("links"), evidence_mode=evidence_mode,
        verified_instance_results=verified_instance_results)
    if expected != dict(binding):
        raise DomainReadError("domain claim-link binding differs from the current claim graph")


def validate_domain_claim_run(repository: Path, run_directory: Path, *,
        problem_contract_sha256: str, run_id: str,
        evidence_mode: str = "open-world", claim_graph_path: str = "claim-mechanism-graph.json",
        verified_instance_results: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Re-read the materialized P04 graph and links after domain/prose validation."""
    result = validate_domain_run(repository, run_directory,
        problem_contract_sha256=problem_contract_sha256, run_id=run_id)
    run = repository_root(run_directory)
    plan = _json(_bytes(run, "domain-read-plan.json"), "materialized plan")
    trace = _json(_bytes(run, "domain-read-trace.json"), "materialized trace")
    graph = _json(_bytes(run, claim_graph_path), "materialized P04 claim graph")
    binding = _json(_bytes(run, "domain-claim-links.json"), "materialized P04 domain links")
    validate_domain_claim_links(repository, plan, trace, graph, binding, evidence_mode=evidence_mode,
        verified_instance_results=verified_instance_results)
    return {**result, "claim_graph_sha256": binding["claim_graph_sha256"],
        "claim_links_sha256": binding["binding_sha256"]}
