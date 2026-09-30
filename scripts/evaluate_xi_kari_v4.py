#!/usr/bin/env python3
"""Freeze, execute, audit and blind the public P14 three-package comparison."""

import argparse
import json
from pathlib import Path

from xi_kari_runtime.evaluation_v4 import (
    EvaluationError, audit_evaluation, blind_evaluation, inspect_preparation,
    prepare_evaluation, run_evaluation,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="Read-only public preparation validation; never submit a request")
    inspect.add_argument("--preparation-root", required=True, type=Path)
    prepare = commands.add_parser("prepare", help="Freeze isolated trials; P13/profile absence is recorded as not_run")
    prepare.add_argument("--preparation-root", required=True, type=Path)
    prepare.add_argument("--run-root", required=True, type=Path)
    prepare.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[1])
    prepare.add_argument("--package-identities", type=Path)
    prepare.add_argument("--execution-profile", type=Path)
    for name in ("run", "audit", "blind"):
        command = commands.add_parser(name)
        command.add_argument("--run-root", required=True, type=Path)
        if name != "audit":
            command.add_argument("--split", choices=("debug", "holdout"), default="holdout")
        if name == "blind":
            command.add_argument("--grader-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "inspect":
            result = inspect_preparation(args.preparation_root)
            result = {key: result[key] for key in ("ready_sha256", "frozen_manifest_sha256", "grader_files_read", "actual_model_runs", "p14_complete")}
        elif args.command == "prepare":
            def load(path):
                return json.loads(path.read_text(encoding="utf-8")) if path else None
            result = prepare_evaluation(args.preparation_root, args.run_root, repository_root=args.repository_root,
                package_descriptors=load(args.package_identities), execution_profile=load(args.execution_profile))
            result = {key: result[key] for key in ("planned_holdout_cells", "planned_debug_cells", "launch_blockers", "actual_model_runs", "p14_complete")}
        elif args.command == "run":
            result = run_evaluation(args.run_root, split=args.split)
        elif args.command == "blind":
            result = blind_evaluation(args.run_root, args.grader_root, split=args.split)
        else:
            result = audit_evaluation(args.run_root)
    except (EvaluationError, OSError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(2, f"evaluation error: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
