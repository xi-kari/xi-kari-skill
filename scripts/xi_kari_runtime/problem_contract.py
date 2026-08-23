"""Frozen XK0 problem contract and instant semantics."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Mapping

from .canonical_json import sha256_json, sha256_text


FROZEN_FIELDS = (
    "question",
    "object_of_analysis",
    "boundary",
    "identity_criterion",
    "spatial_scale",
    "organizational_scale",
    "time_window",
    "evidence_cutoff",
    "retrieval_profile",
    "requested_stance",
    "problem_action",
    "advice_requested",
)
NATURAL_REQUEST_SCHEMA_ID = "xi-kari.v2.natural-request"
NATURAL_REQUEST_SCHEMA_VERSION = 1
MAX_NATURAL_REQUEST_CHARS = 64 * 1024
RETRIEVAL_PROFILES = {"authority-first", "five-direction", "closed-input"}
REQUESTED_STANCES = {"neutral", "support", "oppose"}
PROBLEM_ACTIONS = {"explain", "compare", "infer", "choose", "express"}
RFC3339_INSTANT = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def parse_instant(value: Any, *, field: str = "instant") -> datetime:
    if not isinstance(value, str) or RFC3339_INSTANT.fullmatch(value) is None:
        raise ValueError(f"{field} must be an RFC3339 instant with timezone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid RFC3339 instant") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed


def validate_problem_contract(
    value: Mapping[str, Any], *, mode: str
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("problem contract must be an object")
    missing = [field for field in FROZEN_FIELDS if field not in value]
    if missing:
        raise ValueError("problem contract is missing field: " + missing[0])
    extra = sorted(set(value) - set(FROZEN_FIELDS))
    if extra:
        raise ValueError("problem contract contains unrecognized field: " + extra[0])
    normalized: dict[str, Any] = {}
    for field in FROZEN_FIELDS:
        item = value[field]
        if field == "evidence_cutoff":
            parse_instant(item, field="problem_contract.evidence_cutoff")
            normalized[field] = item
            continue
        if field == "advice_requested":
            if not isinstance(item, bool):
                raise ValueError(
                    "problem_contract.advice_requested must be a boolean"
                )
            normalized[field] = item
            continue
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"problem_contract.{field} must be non-empty text")
        normalized[field] = item.strip()
    profile = normalized["retrieval_profile"]
    if profile not in RETRIEVAL_PROFILES:
        raise ValueError("problem_contract.retrieval_profile is invalid")
    if mode == "closed-input" and profile != "closed-input":
        raise ValueError("closed-input problem contract must use closed-input retrieval profile")
    if mode == "open-world" and profile == "closed-input":
        raise ValueError("open-world problem contract cannot use closed-input retrieval profile")
    if normalized["requested_stance"] not in REQUESTED_STANCES:
        raise ValueError("problem_contract.requested_stance is invalid")
    if normalized["problem_action"] not in PROBLEM_ACTIONS:
        raise ValueError("problem_contract.problem_action is invalid")
    return normalized


def contract_hash(problem_contract: Mapping[str, Any]) -> str:
    return sha256_json(dict(problem_contract))


def normalize_natural_request(value: Any) -> str:
    """Normalize the user-facing request before any semantic authoring.

    The runtime owns this boundary: it rejects NULs and oversized input, and
    retains the exact normalized text so a provider cannot silently replace the
    user's question while filling the remaining XK0 fields.
    """

    if not isinstance(value, str) or "\x00" in value:
        raise ValueError("natural request must be text without NUL bytes")
    text = value.strip()
    if not text:
        raise ValueError("natural request must be non-empty text")
    if len(text) > MAX_NATURAL_REQUEST_CHARS:
        raise ValueError("natural request exceeds the size limit")
    return text


def build_natural_request_envelope(
    value: Any, *, mode: str, evidence_cutoff: str
) -> dict[str, Any]:
    """Create the runtime-owned raw request record used by the public seam."""

    text = normalize_natural_request(value)
    if mode not in {"open-world", "closed-input"}:
        raise ValueError("natural request mode is invalid")
    parse_instant(evidence_cutoff, field="natural_request.evidence_cutoff")
    return {
        "schema_id": NATURAL_REQUEST_SCHEMA_ID,
        "schema_version": NATURAL_REQUEST_SCHEMA_VERSION,
        "mode": mode,
        "text": text,
        "text_sha256": sha256_text(text),
        "evidence_cutoff": evidence_cutoff,
    }


def draft_problem_contract_from_natural_request(
    value: Any, *, mode: str, evidence_cutoff: str
) -> dict[str, Any]:
    """Build a conservative XK0 draft for the runtime-owned authoring call.

    The draft is deliberately explicit about unresolved boundaries.  A
    provider may refine those fields, but the runtime later validates and
    freezes the resulting contract before creating the run directory.
    """

    envelope = build_natural_request_envelope(
        value, mode=mode, evidence_cutoff=evidence_cutoff
    )
    text = envelope["text"]
    return {
        "question": text,
        "object_of_analysis": "待在 XK0 中由基础作者从用户问题确定的对象；不得超出问题文本",
        "boundary": "待在 XK0 中冻结对象、关系、尺度和时间边界；未明确部分登记为未知",
        "identity_criterion": "待在 XK0 中冻结同一对象的可复核身份判据",
        "spatial_scale": "待在 XK0 中冻结；不可从共享环境自动推出因果范围",
        "organizational_scale": "待在 XK0 中冻结；影响或规模不自动生成授权",
        "time_window": "待在 XK0 中冻结，并与证据截止点分开",
        "evidence_cutoff": evidence_cutoff,
        "retrieval_profile": (
            "closed-input" if mode == "closed-input" else "five-direction"
        ),
        "requested_stance": "neutral",
        "problem_action": "explain",
        "advice_requested": False,
    }


def freeze_natural_problem_contract(
    candidate: Mapping[str, Any],
    *,
    request: Mapping[str, Any],
    mode: str,
) -> dict[str, Any]:
    """Validate a provider's XK0 proposal and freeze it under runtime control."""

    if not isinstance(request, Mapping) or set(request) != {
        "schema_id",
        "schema_version",
        "mode",
        "text",
        "text_sha256",
        "evidence_cutoff",
    }:
        raise ValueError("natural request envelope is not exact")
    if request.get("schema_id") != NATURAL_REQUEST_SCHEMA_ID or request.get(
        "schema_version"
    ) != NATURAL_REQUEST_SCHEMA_VERSION:
        raise ValueError("natural request envelope identity is invalid")
    if request.get("mode") != mode:
        raise ValueError("natural request mode differs from execution mode")
    text = normalize_natural_request(request.get("text"))
    if request.get("text_sha256") != sha256_text(text):
        raise ValueError("natural request text hash differs")
    cutoff = request.get("evidence_cutoff")
    parse_instant(cutoff, field="natural_request.evidence_cutoff")
    normalized = validate_problem_contract(candidate, mode=mode)
    if normalized["question"] != text:
        raise ValueError("XK0 authoring changed the user's natural request")
    if normalized["evidence_cutoff"] != cutoff:
        raise ValueError("XK0 authoring changed the runtime evidence cutoff")
    expected_profile = "closed-input" if mode == "closed-input" else "five-direction"
    if normalized["retrieval_profile"] != expected_profile:
        raise ValueError("XK0 authoring changed the retrieval mode contract")
    return normalized


def stance_neutrality_key(
    problem_contract: Mapping[str, Any], *, mode: str
) -> str:
    neutral = {
        key: value
        for key, value in problem_contract.items()
        if key != "requested_stance"
    }
    return sha256_json({"mode": mode, "problem_contract": neutral})
