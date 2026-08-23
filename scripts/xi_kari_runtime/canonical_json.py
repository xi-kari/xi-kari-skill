"""Canonical JSON, hashing, atomic writes, and confined-path helpers."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import stat
import tempfile
from typing import Any


def _validate_json_value(value: Any, *, pointer: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise TypeError(f"canonical JSON object key at {pointer} must be a string")
            _validate_json_value(child, pointer=f"{pointer}/{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _validate_json_value(child, pointer=f"{pointer}/{index}")
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"non-finite number at {pointer} is forbidden")


def canonical_dumps(value: Any) -> str:
    """Return the stable UTF-8 JSON representation used by runtime hashes."""

    _validate_json_value(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_bytes(value: Any) -> bytes:
    return canonical_dumps(value).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_bounded_regular_file(path: Path, *, limit: int) -> bytes:
    """Read at most ``limit + 1`` bytes from a regular, non-symlink file.

    The initial and opened descriptors are checked independently, and the
    final descriptor size is checked again so a provider cannot bypass the
    output bound by racing a sparse file or growing it while it is read.
    """

    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
        raise ValueError("file size limit is invalid")
    path = Path(path)
    parent = path.parent
    while parent != parent.parent:
        if parent.is_symlink():
            raise ValueError(f"refusing to read through symlink: {parent}")
        parent = parent.parent
    try:
        initial = os.stat(path, follow_symlinks=False)
    except OSError as exc:
        raise ValueError(f"regular file is unavailable: {path}") from exc
    if stat.S_ISLNK(initial.st_mode):
        raise ValueError(f"refusing to read symlink: {path}")
    if not stat.S_ISREG(initial.st_mode):
        raise ValueError(f"output is not a regular file: {path}")
    if initial.st_size > limit:
        raise ValueError("file exceeds size limit")
    flags = os.O_RDONLY
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if nofollow:
        flags |= nofollow
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValueError(f"regular file is unavailable: {path}") from exc
    try:
        opened = os.fstat(descriptor)
        if stat.S_ISLNK(opened.st_mode):
            raise ValueError(f"refusing to read symlink: {path}")
        if not stat.S_ISREG(opened.st_mode):
            raise ValueError(f"output is not a regular file: {path}")
        if opened.st_size > limit:
            raise ValueError("file exceeds size limit")
        data = bytearray()
        while len(data) <= limit:
            chunk = os.read(descriptor, min(1024 * 1024, limit + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > limit:
                raise ValueError("file exceeds size limit")
        final = os.fstat(descriptor)
        if final.st_size > limit or final.st_size != opened.st_size:
            raise ValueError("file exceeds size limit during read")
        return bytes(data)
    finally:
        os.close(descriptor)


def _reject_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        value = read_json_text(handle.read())
    return value


def read_json_text(text: str) -> Any:
    value = json.loads(
        text,
        parse_constant=_reject_constant,
        object_pairs_hook=_unique_object,
    )
    _validate_json_value(value)
    return value


def atomic_write_bytes(path: Path, value: bytes) -> None:
    """Replace *path* atomically without following an existing symlink."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    current = path.parent
    while current != current.parent:
        if current.is_symlink():
            raise ValueError(f"refusing to write through symlink: {current}")
        current = current.parent
    if path.is_symlink():
        raise ValueError(f"refusing to replace symlink: {path}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_text(path: Path, value: str) -> None:
    atomic_write_bytes(path, value.encode("utf-8"))


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_bytes(path, canonical_bytes(value) + b"\n")


def confined_path(root: Path, relative: str | Path, *, must_exist: bool = False) -> Path:
    """Resolve a relative artifact path and reject traversal or symlink hops."""

    root = Path(root).resolve()
    candidate_relative = Path(relative)
    if candidate_relative.is_absolute() or ".." in candidate_relative.parts:
        raise ValueError(f"artifact path escapes run directory: {relative}")
    candidate = root.joinpath(candidate_relative)
    current = root
    for part in candidate_relative.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ValueError(f"artifact path contains symlink: {relative}")
    resolved = candidate.resolve(strict=must_exist)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"artifact path escapes run directory: {relative}") from exc
    if must_exist and not resolved.is_file():
        raise ValueError(f"artifact is not a regular file: {relative}")
    return resolved


# Descriptive aliases kept small so callers can use the public vocabulary
# without duplicating hashing implementations.
canonical_json = canonical_dumps
canonical_sha256 = sha256_json
hash_file = sha256_file
