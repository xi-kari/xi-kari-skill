#!/usr/bin/env python3
"""Read-only author feedback for the base semantic output, without run authority."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

from xi_kari_runtime.canonical_json import read_bounded_regular_file, read_json_text
from xi_kari_runtime.contracts import validate_answer_basis_references
from xi_kari_runtime.semantic_projection import (
    validate_reader_section_privacy, validate_reader_sections, validate_visibility_ledger,
)
from xi_kari_runtime.world_volume import _schema_validator


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
            for check in (validate_answer_basis_references, validate_visibility_ledger, validate_reader_section_privacy):
                try:
                    check(packet)
                except (ValueError, TypeError, KeyError) as error:
                    errors.append(str(error))
            try:
                errors.extend(validate_reader_sections(packet))
            except (ValueError, TypeError, KeyError) as error:
                errors.append(str(error))
    except (OSError, UnicodeError, ValueError, TypeError) as error:
        errors.append(str(error))
    return {
        "passed": not errors, "errors": errors, "runtime_sealed": False,
        "scope": "Schema, answer reference identities, disclosure and authored body coverage only; source reading, host observations, complete semantic execution and sealing require runtime validation.",
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
