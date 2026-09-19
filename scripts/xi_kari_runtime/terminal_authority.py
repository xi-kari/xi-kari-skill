"""Run-local one-time terminal authority for cancellation and completion."""

from __future__ import annotations

import hashlib
from pathlib import Path
import secrets
from typing import Any, Mapping

from .canonical_json import (
    atomic_write_json,
    canonical_bytes,
    read_json,
    sha256_file,
    sha256_json,
)


ALGORITHM = "lamport-sha256-v1"
DOMAIN = "xi-kari.v3.terminal-record/v1"
LAMPORT_BITS = 256
KEY_RELATIVE = "continuation/terminal-authority-key.json"
TERMINAL_RELATIVE = "continuation/terminal-record.json"
COMPLETION_RELATIVE = "continuation/completion.json"
OFFICIAL_REPORT_RELATIVE = "validation/attempts/official/validator-report.json"
TRANSACTION_RELATIVE = "continuation/xk12-transaction.json"


def _digest_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _authority_commitment(public_key: list[list[str]]) -> str:
    return sha256_json(
        {"algorithm": ALGORITHM, "domain": DOMAIN, "public_key": public_key}
    )


def generate_terminal_authority(
    run_id: str,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Generate one Lamport key and the commitment frozen by XK0."""

    private_key: list[list[str]] = []
    public_key: list[list[str]] = []
    for _ in range(LAMPORT_BITS):
        private_pair = [secrets.token_bytes(32), secrets.token_bytes(32)]
        private_key.append([value.hex() for value in private_pair])
        public_key.append([_digest_hex(value) for value in private_pair])
    commitment = _authority_commitment(public_key)
    authority = {
        "algorithm": ALGORITHM,
        "domain": DOMAIN,
        "public_key_commitment_sha256": commitment,
    }
    private_record = {
        "schema_id": "xi-kari.v3.terminal-authority-key",
        "schema_version": 3,
        "run_id": run_id,
        "algorithm": ALGORITHM,
        "domain": DOMAIN,
        "authority_key_id": commitment,
        "public_key": public_key,
        "private_key": private_key,
    }
    return authority, private_record


def _message_digest(payload: Mapping[str, Any]) -> bytes:
    return hashlib.sha256(
        DOMAIN.encode("utf-8") + b"\x00" + canonical_bytes(payload)
    ).digest()


def _bits(value: bytes) -> tuple[int, ...]:
    return tuple((byte >> shift) & 1 for byte in value for shift in range(7, -1, -1))


def _validate_key_shape(value: Any, *, label: str) -> list[list[str]]:
    if not isinstance(value, list) or len(value) != LAMPORT_BITS:
        raise ValueError(f"terminal authority {label} must contain 256 pairs")
    result: list[list[str]] = []
    for pair in value:
        if (
            not isinstance(pair, list)
            or len(pair) != 2
            or any(
                not isinstance(item, str)
                or len(item) != 64
                or any(character not in "0123456789abcdef" for character in item)
                for item in pair
            )
        ):
            raise ValueError(f"terminal authority {label} contains an invalid pair")
        result.append(pair)
    return result


def commit_terminal_record(
    run_dir: Path,
    run_contract: Mapping[str, Any],
    signed_payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Sign one terminal payload, persist it, then consume the private key."""

    root = Path(run_dir).resolve()
    terminal_path = root / TERMINAL_RELATIVE
    if terminal_path.exists():
        raise ValueError("terminal authority has already been consumed")
    key_path = root / KEY_RELATIVE
    key = read_json(key_path)
    if not isinstance(key, Mapping):
        raise ValueError("terminal authority private key is missing")
    run_id = run_contract.get("run_id")
    authority = run_contract.get("terminal_authority")
    if not isinstance(authority, Mapping):
        raise ValueError("run contract has no terminal authority commitment")
    if key.get("run_id") != run_id:
        raise ValueError("terminal authority private key run_id mismatch")
    public_key = _validate_key_shape(key.get("public_key"), label="public key")
    private_key = _validate_key_shape(key.get("private_key"), label="private key")
    commitment = _authority_commitment(public_key)
    if (
        authority.get("algorithm") != ALGORITHM
        or authority.get("domain") != DOMAIN
        or authority.get("public_key_commitment_sha256") != commitment
        or key.get("authority_key_id") != commitment
    ):
        raise ValueError("terminal authority key differs from the XK0 commitment")
    for public_pair, private_pair in zip(public_key, private_key, strict=True):
        if [_digest_hex(bytes.fromhex(item)) for item in private_pair] != public_pair:
            raise ValueError("terminal authority private key does not match its public key")
    payload = dict(signed_payload)
    if payload.get("run_id") != run_id:
        raise ValueError("terminal payload run_id differs from the run contract")
    signature = [
        private_key[index][bit]
        for index, bit in enumerate(_bits(_message_digest(payload)))
    ]
    record = {
        "schema_id": "xi-kari.v3.terminal-record",
        "schema_version": 3,
        "authority_key_id": commitment,
        "public_key": public_key,
        "signed_payload": payload,
        "payload_sha256": sha256_json(payload),
        "signature": signature,
    }
    atomic_write_json(terminal_path, record)
    key_path.unlink()
    return record


def verify_terminal_record(
    run_dir: Path,
    run_contract: Mapping[str, Any],
    *,
    require_consumed_key: bool = True,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Verify the signed terminal record against the immutable XK0 commitment."""

    root = Path(run_dir).resolve()
    path = root / TERMINAL_RELATIVE
    if not path.is_file():
        return None, []
    errors: list[str] = []
    try:
        record = read_json(path)
    except Exception as exc:
        return None, [f"terminal authority record is unreadable: {exc}"]
    if not isinstance(record, Mapping):
        return None, ["terminal authority record is not an object"]
    authority = run_contract.get("terminal_authority")
    if not isinstance(authority, Mapping):
        return None, ["terminal authority commitment is missing from the run contract"]
    try:
        public_key = _validate_key_shape(record.get("public_key"), label="public key")
    except ValueError as exc:
        return None, [str(exc)]
    commitment = _authority_commitment(public_key)
    if (
        authority.get("algorithm") != ALGORITHM
        or authority.get("domain") != DOMAIN
        or authority.get("public_key_commitment_sha256") != commitment
        or record.get("authority_key_id") != commitment
    ):
        errors.append("terminal authority public key differs from the XK0 commitment")
    payload = record.get("signed_payload")
    if not isinstance(payload, Mapping):
        errors.append("terminal authority signed payload is not an object")
        return None, errors
    if payload.get("run_id") != run_contract.get("run_id"):
        errors.append("terminal authority run_id differs from the run contract")
    if record.get("payload_sha256") != sha256_json(payload):
        errors.append("terminal authority payload hash mismatch")
    signature = record.get("signature")
    if (
        not isinstance(signature, list)
        or len(signature) != LAMPORT_BITS
        or any(
            not isinstance(item, str)
            or len(item) != 64
            or any(character not in "0123456789abcdef" for character in item)
            for item in signature
        )
    ):
        errors.append("terminal authority signature has an invalid shape")
    else:
        for index, bit in enumerate(_bits(_message_digest(payload))):
            if _digest_hex(bytes.fromhex(signature[index])) != public_key[index][bit]:
                errors.append("terminal authority signature verification failed")
                break
    if require_consumed_key and (root / KEY_RELATIVE).exists():
        errors.append("terminal authority private key was not consumed")
    return (dict(record) if not errors else None), errors


def validate_terminal_closure(
    run_dir: Path,
    run_contract: Mapping[str, Any],
    *,
    phase_count: int,
    chain_head_sha256: str | None,
    required: bool,
) -> tuple[str | None, list[str]]:
    """Validate the signed terminal and, for completion, its official closure."""

    root = Path(run_dir).resolve()
    record, errors = verify_terminal_record(root, run_contract)
    if record is None:
        if required and not errors:
            errors.append("terminal authority record is missing")
        return None, errors
    payload = record["signed_payload"]
    state = payload.get("terminal_state")
    if state not in {"cancelled", "complete"}:
        return None, ["terminal authority state is invalid"]
    if payload.get("phase_count") != phase_count:
        errors.append("terminal authority phase count mismatch")
    if payload.get("chain_head_sha256") != chain_head_sha256:
        errors.append("terminal authority chain head mismatch")
    if state == "cancelled":
        if not isinstance(payload.get("reason"), str) or not payload["reason"].strip():
            errors.append("terminal authority cancellation reason is missing")
        return (state if not errors else None), errors

    if phase_count != 13:
        errors.append("terminal authority completion requires all 13 phases")
    completion_path = root / COMPLETION_RELATIVE
    official_path = root / OFFICIAL_REPORT_RELATIVE
    transaction_path = root / TRANSACTION_RELATIVE
    manifest_path = root / "artifacts/artifact-manifest.json"
    final_chat_path = root / "delivery/final-chat.json"
    for path, label in (
        (completion_path, "completion authority"),
        (official_path, "official validation report"),
        (transaction_path, "XK12 transaction"),
        (manifest_path, "artifact manifest"),
        (final_chat_path, "final chat"),
    ):
        if not path.is_file():
            errors.append(f"terminal authority {label} is missing")
    if errors:
        return None, errors
    try:
        completion = read_json(completion_path)
        official = read_json(official_path)
        transaction = read_json(transaction_path)
        final_chat = read_json(final_chat_path)
    except Exception as exc:
        return None, [f"terminal authority closure is unreadable: {exc}"]
    if payload.get("completion_sha256") != sha256_file(completion_path):
        errors.append("terminal authority completion hash mismatch")
    expected_completion = {
        "schema_id": "xi-kari.v3.completion",
        "schema_version": 3,
        "run_id": run_contract.get("run_id"),
        "official_validation_path": OFFICIAL_REPORT_RELATIVE,
        "official_validation_sha256": sha256_file(official_path),
        "chain_head_sha256": chain_head_sha256,
        "phase_count": phase_count,
        "validator_set_sha256": run_contract.get("validator_set_sha256"),
        "manifest_sha256": sha256_file(manifest_path),
        "final_chat_sha256": sha256_file(final_chat_path),
        "xk12_transaction_sha256": sha256_file(transaction_path),
        "completed_at": completion.get("completed_at") if isinstance(completion, Mapping) else None,
    }
    if completion != expected_completion:
        errors.append("terminal authority completion closure mismatch")
    if not isinstance(official, Mapping) or any(
        (
            official.get("schema_id") != "xi-kari.v3.validator-report",
            official.get("run_id") != run_contract.get("run_id"),
            official.get("fresh") is not True,
            official.get("fresh_process") is not True,
            official.get("validation_boundary") != "official",
            official.get("valid") is not True,
            official.get("phase_count") != phase_count,
            official.get("validated_phase") != "XK12",
            official.get("chain_head_sha256") != chain_head_sha256,
            official.get("validator_set_sha256")
            != run_contract.get("validator_set_sha256"),
        )
    ):
        errors.append("terminal authority official validation report is not authoritative")
    if not isinstance(transaction, Mapping) or transaction.get("state") != "official_validated":
        errors.append("terminal authority XK12 transaction is not finalized")
    if not isinstance(final_chat, Mapping) or final_chat.get(
        "validation_authority_path"
    ) != COMPLETION_RELATIVE:
        errors.append("terminal authority final chat does not point to completion")
    return (state if not errors else None), errors


__all__ = (
    "ALGORITHM",
    "COMPLETION_RELATIVE",
    "DOMAIN",
    "KEY_RELATIVE",
    "OFFICIAL_REPORT_RELATIVE",
    "TERMINAL_RELATIVE",
    "TRANSACTION_RELATIVE",
    "commit_terminal_record",
    "generate_terminal_authority",
    "validate_terminal_closure",
    "verify_terminal_record",
)
