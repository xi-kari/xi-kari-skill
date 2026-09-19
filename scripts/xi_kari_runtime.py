#!/usr/bin/env python3
"""Xi-Kari v3 isolated semantic run CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    package_path = Path(__file__).with_suffix("")
    __path__ = [str(package_path)]
    sys.modules.setdefault("scripts.xi_kari_runtime", sys.modules[__name__])

from scripts.xi_kari_runtime.authoring import DEFAULT_ADAPTER_TIMEOUT_SECONDS
from scripts.xi_kari_runtime.canonical_json import canonical_dumps, read_json
from scripts.xi_kari_runtime.contracts import (
    CONTRACT_PROFILES,
)
from scripts.xi_kari_runtime.materialization import (
    cancel_run,
    default_runs_root,
    fork_run,
    materialize_run,
    prepare_run,
    status_run,
)
from scripts.xi_kari_runtime.lifecycle import (
    initialize_run,
    require_cli_start_profile,
    resume_lifecycle_run,
    validate_lifecycle_run,
    write_bound_repair_plan,
)
from scripts.xi_kari_runtime.execution import execute_authored_run
from scripts.xi_kari_runtime.closed_input import (
    CLOSED_INPUT_SCHEMA_ID,
    CLOSED_INPUT_SCHEMA_VERSION,
)


def _json_value(path: str | None) -> dict | None:
    if path is None:
        return None
    value = read_json(Path(path).expanduser().resolve())
    if not isinstance(value, dict):
        raise ValueError(f"JSON input must be an object: {path}")
    return value


def _stdin_text() -> str:
    value = sys.stdin.read()
    if not value.strip():
        raise ValueError("stdin request is empty")
    return value.strip()


def _natural_request_text(args: argparse.Namespace) -> str | None:
    """Read the raw natural-language public input for ``execute`` only."""

    direct = getattr(args, "request_text", None)
    from_stdin = bool(getattr(args, "request_text_stdin", False))
    if direct is not None and from_stdin:
        raise ValueError("provide exactly one natural request input")
    if direct is not None:
        if not isinstance(direct, str) or not direct.strip():
            raise ValueError("request text is empty")
        return direct
    if from_stdin:
        return _stdin_text()
    return None


def _problem_contract(args: argparse.Namespace) -> dict:
    sources = [
        value
        for value in (
            getattr(args, "problem_contract", None),
            getattr(args, "problem_contract_stdin", False),
            getattr(args, "request_stdin", False),
        )
        if value
    ]
    if len(sources) > 1:
        raise ValueError("provide exactly one problem contract input")
    if getattr(args, "problem_contract", None) is not None:
        value = _json_value(str(args.problem_contract))
        if value is None:
            raise ValueError("problem contract JSON is empty")
        return value
    if getattr(args, "problem_contract_stdin", False) or getattr(
        args, "request_stdin", False
    ):
        try:
            value = json.loads(_stdin_text())
        except json.JSONDecodeError as exc:
            raise ValueError(
                "problem contract stdin must contain a JSON object"
            ) from exc
        if not isinstance(value, dict):
            raise ValueError("problem contract stdin must contain a JSON object")
        return value
    raise ValueError(
        "provide --problem-contract, --problem-contract-stdin, or --request-stdin"
    )


def _closed_input_materials(args: argparse.Namespace) -> list[dict] | None:
    path = getattr(args, "closed_input_materials", None)
    mode = getattr(args, "mode", "open-world")
    if mode == "open-world":
        if path is not None:
            raise ValueError(
                "--closed-input-materials is only valid with --mode closed-input"
            )
        return None
    if path is None:
        raise ValueError(
            "closed-input execute requires --closed-input-materials"
        )
    value = read_json(Path(path).expanduser().resolve())
    if not isinstance(value, dict) or set(value) != {
        "schema_id",
        "schema_version",
        "materials",
    }:
        raise ValueError("closed-input materials file must be the exact envelope")
    if (
        value.get("schema_id") != CLOSED_INPUT_SCHEMA_ID
        or value.get("schema_version") != CLOSED_INPUT_SCHEMA_VERSION
        or not isinstance(value.get("materials"), list)
    ):
        raise ValueError("closed-input materials file identity is invalid")
    return value["materials"]


def _start_options(
    args: argparse.Namespace,
    *,
    repository_root: Path | None,
) -> dict:
    return {
        "problem_contract": _problem_contract(args),
        "mode": args.mode,
        "run_id": args.run_id,
        "repository_root": repository_root,
        "semantic_authoring_adapter": args.semantic_authoring_adapter,
        "semantic_authoring_timeout_seconds": (
            args.semantic_authoring_timeout_seconds
        ),
        "contract_profile": args.contract_profile,
        "semantic_read_trace_path": args.semantic_read_trace,
        "semantic_authoring_profile": args.semantic_authoring_profile,
        "codex_provider_executable": args.codex_provider_executable,
        "privacy_purpose": args.privacy_purpose,
        "delivery_audience": args.delivery_audience,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Xi-Kari v3 semantic run runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="read-only production preflight; execute creates the run")
    init.add_argument("--runs-root", type=Path)
    init.add_argument("--run-id")
    init_input = init.add_mutually_exclusive_group()
    init_input.add_argument(
        "--request-stdin",
        action="store_true",
        help="read the complete XK0 problem-contract JSON from stdin",
    )
    init_input.add_argument("--problem-contract", type=Path)
    init_input.add_argument("--problem-contract-stdin", action="store_true")
    init.add_argument("--mode", choices=("open-world", "closed-input"), default="open-world")
    init.add_argument("--privacy-purpose", default="回答冻结问题并仅向请求用户交付")
    init.add_argument("--delivery-audience", default="requesting-user")
    init.add_argument("--repository-root", type=Path)
    init.add_argument(
        "--contract-profile",
        choices=tuple(sorted(CONTRACT_PROFILES)),
        required=True,
    )
    init.add_argument("--semantic-read-trace", type=Path)
    init.add_argument(
        "--semantic-authoring-adapter",
        type=Path,
        metavar="EXECUTABLE",
    )
    init.add_argument(
        "--semantic-authoring-timeout-seconds",
        type=int,
        default=DEFAULT_ADAPTER_TIMEOUT_SECONDS,
    )
    init.add_argument(
        "--semantic-authoring-profile",
        choices=("production-codex",),
        required=True,
    )
    init.add_argument("--codex-provider-executable", type=Path, metavar="EXECUTABLE")

    prepare = sub.add_parser("prepare", help="read-only full-source and provider preflight")
    prepare.add_argument("--runs-root", type=Path)
    prepare.add_argument("--run-id")
    prepare_input = prepare.add_mutually_exclusive_group()
    prepare_input.add_argument(
        "--request-stdin",
        action="store_true",
        help="read the complete XK0 problem-contract JSON from stdin",
    )
    prepare_input.add_argument("--problem-contract", type=Path)
    prepare_input.add_argument("--problem-contract-stdin", action="store_true")
    prepare.add_argument("--mode", choices=("open-world", "closed-input"), default="open-world")
    prepare.add_argument("--privacy-purpose", default="回答冻结问题并仅向请求用户交付")
    prepare.add_argument("--delivery-audience", default="requesting-user")
    prepare.add_argument("--repository-root", type=Path)
    prepare.add_argument(
        "--contract-profile",
        choices=tuple(sorted(CONTRACT_PROFILES)),
        required=True,
    )
    prepare.add_argument("--semantic-read-trace", type=Path)
    prepare.add_argument(
        "--semantic-authoring-adapter",
        type=Path,
        metavar="EXECUTABLE",
    )
    prepare.add_argument(
        "--semantic-authoring-timeout-seconds",
        type=int,
        default=DEFAULT_ADAPTER_TIMEOUT_SECONDS,
    )
    prepare.add_argument(
        "--semantic-authoring-profile",
        choices=("production-codex",),
        required=True,
    )
    prepare.add_argument(
        "--codex-provider-executable", type=Path, metavar="EXECUTABLE"
    )

    execute = sub.add_parser(
        "execute",
        help="start a runtime-owned base author and materialize a production run",
    )
    execute.add_argument("--runs-root", type=Path)
    execute.add_argument("--run-id")
    execute_input = execute.add_mutually_exclusive_group()
    execute_input.add_argument(
        "--request-stdin",
        action="store_true",
        help="read the complete XK0 problem-contract JSON from stdin",
    )
    execute_input.add_argument("--problem-contract", type=Path)
    execute_input.add_argument("--problem-contract-stdin", action="store_true")
    execute_input.add_argument(
        "--request-text",
        help="freeze a plain natural-language request at XK0 before authoring",
    )
    execute_input.add_argument(
        "--request-text-stdin",
        action="store_true",
        help="read a plain natural-language request from stdin",
    )
    execute.add_argument(
        "--mode", choices=("open-world", "closed-input"), default="open-world"
    )
    execute.add_argument("--privacy-purpose", default="回答冻结问题并仅向请求用户交付")
    execute.add_argument("--delivery-audience", default="requesting-user")
    execute.add_argument("--repository-root", type=Path)
    execute.add_argument(
        "--codex-provider-executable", type=Path, required=True, metavar="EXECUTABLE"
    )
    execute.add_argument(
        "--closed-input-materials",
        type=Path,
        metavar="JSON",
        help="read a xi-kari.v3.closed-input-materials envelope",
    )
    execute.add_argument("--timeout-seconds", type=int, default=DEFAULT_ADAPTER_TIMEOUT_SECONDS)

    materialize = sub.add_parser("materialize", help="materialize the disk-reloaded semantic packet")
    materialize.add_argument("--run-dir", required=True, type=Path)
    materialize.add_argument("--packet", type=Path)
    materialize.add_argument("--repository-root", type=Path)

    validate = sub.add_parser("validate", help="freshly reread and validate a run")
    validate.add_argument("--run-dir", required=True, type=Path)
    validate.add_argument("--repository-root", type=Path)
    validation_boundary = validate.add_mutually_exclusive_group()
    validation_boundary.add_argument("--preseal", action="store_true")
    validation_boundary.add_argument("--promotion", action="store_true")
    validation_boundary.add_argument("--official", action="store_true")
    validate.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="validate an incomplete parent run without treating phase count as the primary error",
    )

    repair = sub.add_parser("repair-plan", help="write a bound earliest-invalid-stage repair plan")
    repair.add_argument("--run-dir", required=True, type=Path)
    repair.add_argument("--repository-root", type=Path)

    resume = sub.add_parser(
        "resume",
        help="advance initialized state, resume work, or consume a bound repair plan",
    )
    resume.add_argument("--run-dir", required=True, type=Path)
    resume.add_argument("--packet", type=Path)
    resume.add_argument("--repository-root", type=Path)

    fork = sub.add_parser("fork", help="create an isolated child run")
    fork.add_argument("--run-dir", required=True, type=Path)
    fork.add_argument("--runs-root", type=Path)
    fork.add_argument("--run-id")
    fork.add_argument("--base-phase")
    fork.add_argument("--repository-root", type=Path)
    fork.add_argument("--semantic-read-trace", type=Path)

    cancel = sub.add_parser("cancel", help="cancel a run without rewriting sealed phases")
    cancel.add_argument("--run-dir", required=True, type=Path)
    cancel.add_argument("--reason", required=True)

    status = sub.add_parser("status", help="derive state from disk")
    status.add_argument("--run-dir", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repository_root = getattr(args, "repository_root", None)
        if args.command == "init":
            require_cli_start_profile(args.contract_profile)
            result = initialize_run(
                args.runs_root or default_runs_root(),
                **_start_options(args, repository_root=repository_root),
            )
        elif args.command == "prepare":
            require_cli_start_profile(args.contract_profile)
            result = prepare_run(
                args.runs_root or default_runs_root(),
                **_start_options(args, repository_root=repository_root),
            )
        elif args.command == "execute":
            request_text = _natural_request_text(args)
            result = execute_authored_run(
                args.runs_root or default_runs_root(),
                problem_contract=(
                    None if request_text is not None else _problem_contract(args)
                ),
                request_text=request_text,
                mode=args.mode,
                run_id=args.run_id,
                repository_root=repository_root,
                codex_provider_executable=args.codex_provider_executable,
                closed_input_materials=_closed_input_materials(args),
                timeout_seconds=args.timeout_seconds,
                privacy_purpose=args.privacy_purpose,
                delivery_audience=args.delivery_audience,
            )
        elif args.command == "materialize":
            result = materialize_run(args.run_dir, _json_value(str(args.packet) if args.packet else None), repository_root=repository_root)
        elif args.command == "validate":
            validation_boundary = (
                "preseal"
                if args.preseal
                else "promotion"
                if args.promotion
                else "official"
                if args.official
                else "final"
            )
            result = validate_lifecycle_run(
                args.run_dir,
                repository_root=repository_root,
                require_complete=not args.preseal and not args.allow_incomplete,
                validation_boundary=validation_boundary,
            )
        elif args.command == "repair-plan":
            result = write_bound_repair_plan(
                args.run_dir,
                repository_root=repository_root,
            )
        elif args.command == "resume":
            result = resume_lifecycle_run(
                args.run_dir,
                _json_value(str(args.packet) if args.packet else None),
                repository_root=repository_root,
            )
        elif args.command == "fork":
            result = status_run(
                fork_run(
                    args.run_dir,
                    runs_root=args.runs_root,
                    run_id=args.run_id,
                    base_phase=args.base_phase,
                    repository_root=repository_root,
                    semantic_read_trace_path=args.semantic_read_trace,
                )
            )
        elif args.command == "cancel":
            result = cancel_run(args.run_dir, reason=args.reason)
        elif args.command == "status":
            result = status_run(args.run_dir)
        else:  # pragma: no cover
            raise ValueError(f"unsupported command: {args.command}")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(canonical_dumps(result))
    if result.get("valid", True) is False or result.get("state") in {
        "invalid",
        "needs_attention",
    }:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
