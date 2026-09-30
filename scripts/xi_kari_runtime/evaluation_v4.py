"""Frozen, failure-preserving P14 process execution and isolated grader export."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import secrets
import subprocess
import sys
import time
import zipfile

from .canonical_json import canonical_bytes, read_json_text

MODEL = "gpt-6.1-sol"
EFFORT = "max"
OUTPUT_TOKENS = 6000
TIMEOUT_SECONDS = 1200
ARMS = ("S", "O", "N")
SEED = "xikari-p14-holdout-v1-20260930"
OLD_COMMIT = "81f51aadb3ba1927eac95f8be33b4b9c2545f098"
OLD_TREE = "a33bd5e69e8347a8fbea9eb0d4159341ddc96cb5"
OLD_SOURCE = "4a3ad8e8692b7a906f733096bbc8e05d0ac4f8cfbf79d3926eb1729df828c7f5"
NEW_SOURCE = "ffc45afdc288ecd268fd02e46d47318b7ddf17bf7b47605aa6c413c95398544b"
FROZEN_PREPARATION_SHA = "1a9eacb077b9606c1f1cecedb60851b21464f9538a8d35f9773fbe11de3fefe5"
FROZEN_READY_SHA = "082dbc8452bb60c3f66b0fc2ec384e1034e4d6b490efb7060170c7933e435ac1"
PUBLIC_CONTROLS = ("protocol.md", "tasks.json", "sources-manifest.json", "arm-execution-config.json",
                   "arm-contexts/common-author-instructions.md", "arm-contexts/simple-method.md")


class EvaluationError(ValueError):
    """Frozen identities, process receipts or author/grader boundaries are invalid."""


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _root(value: Path) -> Path:
    path = Path(value).expanduser().absolute()
    if "grader-only" in path.parts:
        raise EvaluationError("grader-only paths cannot be evaluation runner inputs")
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise EvaluationError("evaluation root contains a symlink or junction")
    return path.resolve()


def _relative(value: str) -> str:
    if (not isinstance(value, str) or not value or "\\" in value or ":" in value
            or PurePosixPath(value).is_absolute() or PureWindowsPath(value).drive
            or ".." in PurePosixPath(value).parts or str(PurePosixPath(value)) != value
            or "grader-only" in PurePosixPath(value).parts):
        raise EvaluationError("unsafe or grader-only evaluation input path")
    return value


def _read(root: Path, relative: str) -> bytes:
    relative = _relative(relative)
    path = root
    for part in PurePosixPath(relative).parts:
        path = path / part
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise EvaluationError("evaluation input path contains a symlink or junction")
    try:
        path.resolve(strict=True).relative_to(root)
        return path.read_bytes()
    except (OSError, ValueError) as exc:
        raise EvaluationError(f"cannot read frozen evaluation input {relative}") from exc


def _json(root: Path, relative: str):
    try:
        return read_json_text(_read(root, relative).decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise EvaluationError(f"invalid evaluation JSON {relative}") from exc


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".pending")
    temporary.write_bytes(canonical_bytes(value) + b"\n")
    temporary.replace(path)


def _identity(path: str, raw: bytes) -> dict:
    return {"path": path, "bytes": len(raw), "sha256": _sha(raw)}


def _outside(path: Path, boundaries: list[Path]) -> None:
    if any(path.is_relative_to(boundary) or boundary.is_relative_to(path) for boundary in boundaries):
        raise EvaluationError("evaluation and grader outputs must be outside product and preparation boundaries")


def inspect_preparation(preparation_root: Path) -> dict:
    """Validate only public frozen control and author files; never read grader keys."""
    root = _root(preparation_root)
    ready = _json(root, "READY.json")
    if ready.get("preparation_ready") is not True or ready.get("actual_model_runs") != 0:
        raise EvaluationError("preparation is not the frozen pre-execution public receipt")
    frozen_raw = _read(root, "FROZEN-MANIFEST.json")
    frozen = read_json_text(frozen_raw.decode("utf-8"))
    manifested = {row["path"]: row for row in frozen["files"]}
    controls = {row["path"]: row for row in ready["control_files"]}
    expected_manifest = controls.get("FROZEN-MANIFEST.json", {})
    if expected_manifest.get("sha256") != _sha(frozen_raw):
        raise EvaluationError("frozen preparation manifest differs from READY")
    tasks = _json(root, "tasks.json")
    config = _json(root, "arm-execution-config.json")
    required = {"model": MODEL, "reasoning_effort": EFFORT, "fact_scope": "closed-input",
        "network": "disabled", "requested_max_output_tokens": OUTPUT_TOKENS,
        "author_turns": 1, "substitution_allowed": False}
    for requirement in [tasks["author_model_requirement"], *config["arms"].values()]:
        if any(requirement.get(field) != value for field, value in required.items()):
            raise EvaluationError("frozen exact model, reasoning, input or budget contract differs")
    if set(config["arms"]) != set(ARMS):
        raise EvaluationError("evaluation must preserve all three frozen arms")
    if [row["id"] for row in tasks["debug_tasks"]] != ["D01", "D02"] or [row["id"] for row in tasks["holdout_tasks"]] != [f"H{i:02d}" for i in range(1, 7)]:
        raise EvaluationError("evaluation must preserve two debug and six holdout tasks")
    public_paths = set(PUBLIC_CONTROLS)
    for row in [*tasks["debug_tasks"], *tasks["holdout_tasks"]]:
        prefix = "author-inputs/" + row["slug"] + "/"
        for relative in [row["prompt"], *row["author_materials"]]:
            _relative(relative)
            if not relative.startswith(prefix):
                raise EvaluationError("author file is outside its task's listed public inputs")
            public_paths.add(relative)
    verified = []
    for relative in sorted(public_paths):
        raw = _read(root, relative)
        expected = manifested.get(relative) or controls.get(relative)
        if not expected or expected.get("sha256") != _sha(raw) or expected.get("bytes") != len(raw):
            raise EvaluationError(f"frozen public bytes differ: {relative}")
        verified.append(_identity(relative, raw))
    schedule = tasks["execution_schedule"]
    if schedule.get("seed") != SEED or len(schedule["passes"]) != 3:
        raise EvaluationError("frozen holdout order seed or passes differ")
    route = []
    seen = set()
    for ordinal, row in enumerate(schedule["passes"], 1):
        ids = [f"H{i:02d}" for i in range(1, 7)]
        expected_order = sorted(ids, key=lambda task_id: _sha(f"{SEED}|{ordinal}|{task_id}".encode()))
        if row.get("pass") != ordinal or row.get("task_order") != expected_order or set(row["arms"]) != set(ids):
            raise EvaluationError("frozen balanced holdout order differs")
        for task_id in expected_order:
            arm = row["arms"][task_id]
            if arm not in ARMS or (task_id, arm) in seen:
                raise EvaluationError("balanced holdout schedule repeats or changes an arm")
            seen.add((task_id, arm))
            route.append({"task_id": task_id, "arm": arm, "pass": ordinal, "split": "holdout"})
    return {"preparation_root": str(root), "ready_sha256": _sha(_read(root, "READY.json")),
        "frozen_manifest_sha256": _sha(frozen_raw), "public_files": verified,
        "tasks": tasks, "holdout_route": route, "grader_files_read": 0,
        "actual_model_runs": 0, "p14_complete": False}


def _git(root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(["git", *arguments], cwd=root, capture_output=True, check=False)
    if completed.returncode:
        raise EvaluationError("package Git identity or tracked bytes cannot be verified")
    return completed.stdout


def _package(descriptor: Mapping, *, arm: str, fixture_mode: bool) -> tuple[dict, dict[str, bytes]]:
    repository = _root(descriptor["repository_root"])
    commit = _git(repository, "rev-parse", "HEAD").decode().strip()
    tree = _git(repository, "rev-parse", "HEAD^{tree}").decode().strip()
    if commit != descriptor.get("commit") or tree != descriptor.get("git_tree") or _git(repository, "status", "--porcelain=v1"):
        raise EvaluationError("package repository identity or clean tree differs")
    archive = _root(descriptor["package_path"])
    raw = archive.read_bytes()
    if _sha(raw) != descriptor.get("package_sha256"):
        raise EvaluationError("package bytes differ from their frozen hash")
    contents = {}
    with zipfile.ZipFile(archive) as bundle:
        for entry in bundle.infolist():
            if entry.is_dir():
                continue
            name = _relative(entry.filename)
            if name in contents or ((entry.external_attr >> 16) & 0o170000) == 0o120000:
                raise EvaluationError("package archive repeats a file or includes a symlink")
            content = bundle.read(entry)
            if content != _git(repository, "cat-file", "blob", commit + ":" + name):
                raise EvaluationError("package archive does not contain its exact committed bytes")
            contents[name] = content
    source = contents.get(_relative(descriptor["source_path"]))
    if source is None or _sha(source) != descriptor.get("source_sha256") or "SKILL.md" not in contents:
        raise EvaluationError("package active source or Skill entrypoint is missing or changed")
    if not fixture_mode and ((arm == "O" and (commit, tree, _sha(source)) != (OLD_COMMIT, OLD_TREE, OLD_SOURCE)) or (arm == "N" and _sha(source) != NEW_SOURCE)):
        raise EvaluationError("package does not match the frozen old or accepted v9 source identity")
    identity = {field: deepcopy(descriptor[field]) for field in ("commit", "git_tree", "package_sha256", "source_path", "source_sha256", "schema_versions")}
    identity.update(package_bytes=len(raw), content_bytes=sum(map(len, contents.values())),
        members=[_identity(name, content) for name, content in sorted(contents.items())])
    if arm == "N":
        receipt_ref = descriptor.get("p13_receipt")
        if not isinstance(receipt_ref, Mapping):
            raise EvaluationError("P13 accepted candidate receipt is missing")
        receipt_path = _root(receipt_ref["path"])
        receipt_raw = receipt_path.read_bytes()
        receipt = read_json_text(receipt_raw.decode("utf-8"))
        if _sha(receipt_raw) != receipt_ref.get("sha256") or receipt.get("accepted") is not True:
            raise EvaluationError("P13 receipt is not an immutable acceptance")
        for field, name in (("commit", "candidate_commit"), ("git_tree", "git_tree"),
                            ("package_sha256", "package_sha256"), ("source_sha256", "source_sha256"),
                            ("schema_versions", "schema_versions")):
            if receipt.get(name) != identity[field]:
                raise EvaluationError("P13 receipt differs from actual candidate identity")
        if receipt.get("fixture_only") and not fixture_mode:
            raise EvaluationError("fixture P13 receipts cannot authorize real trials")
        identity["p13_receipt"] = {"path": str(receipt_path), "sha256": _sha(receipt_raw)}
    return identity, contents


def _profile(profile: Mapping | None, *, fixture_mode: bool) -> tuple[dict, list[str]]:
    value = deepcopy(dict(profile or {}))
    if set(value) - {"kind", "executable", "executable_sha256", "model", "reasoning_effort",
                     "preflight_receipt", "isolation_command_prefix", "launcher_files"}:
        raise EvaluationError("execution profile contains unsupported or credential-bearing fields")
    value.setdefault("isolation_command_prefix", [])
    value.setdefault("launcher_files", {})
    issues = []
    expected_kind = "deterministic_fixture" if fixture_mode else "codex_subscription"
    if value.get("kind") != expected_kind:
        issues.append("execution_profile_unavailable")
    if value.get("model") != MODEL or value.get("reasoning_effort") != EFFORT:
        issues.append("exact_model_effort_unavailable")
    executable = value.get("executable")
    if not isinstance(executable, str) or not Path(executable).is_file():
        issues.append("subscription_executable_unavailable")
    else:
        value["executable"] = str(_root(executable))
        value["executable_sha256"] = _sha(Path(executable).read_bytes())
    launcher_files = value["launcher_files"]
    if not isinstance(launcher_files, Mapping):
        issues.append("isolation_launcher_files_invalid")
        launcher_files = {}
    for path, expected_hash in launcher_files.items():
        try:
            if not isinstance(path, str) or not Path(path).is_absolute() or not isinstance(expected_hash, str) or re.fullmatch(r"[0-9a-f]{64}", expected_hash) is None:
                raise EvaluationError("invalid launcher file binding")
            if _sha(_root(path).read_bytes()) != expected_hash:
                issues.append("isolation_launcher_artifact_changed")
        except (EvaluationError, OSError):
            issues.append("isolation_launcher_artifact_unavailable")
    prefix = value["isolation_command_prefix"]
    if isinstance(prefix, list):
        for item in prefix:
            if isinstance(item, str) and Path(item).is_absolute() and Path(item).is_file() and item not in launcher_files:
                issues.append("isolation_launcher_artifact_unbound")
    if not fixture_mode:
        if not sys.platform.startswith("linux"):
            issues.append("isolated_author_requires_linux")
        prefix = value["isolation_command_prefix"]
        if not isinstance(prefix, list) or not prefix or any(not isinstance(item, str) or not item for item in prefix):
            issues.append("isolation_launcher_missing")
        elif not Path(prefix[0]).is_absolute() or not Path(prefix[0]).is_file() or not launcher_files:
            issues.append("isolation_launcher_artifact_unbound")
        reference = value.get("preflight_receipt")
        if not isinstance(reference, Mapping):
            issues.append("independent_execution_preflight_missing")
        else:
            raw = _root(reference["path"]).read_bytes()
            receipt = read_json_text(raw.decode("utf-8"))
            required = ("subscription_only", "model_effort_available", "author_filesystem_isolated",
                "network_tools_disabled", "external_context_disabled", "one_author_turn")
            profile_binding = {name: value.get(name) for name in ("kind", "executable", "executable_sha256",
                "model", "reasoning_effort", "isolation_command_prefix", "launcher_files")}
            if (_sha(raw) != reference.get("sha256") or receipt.get("executable_sha256") != value.get("executable_sha256")
                    or receipt.get("model") != MODEL or receipt.get("reasoning_effort") != EFFORT
                    or receipt.get("launch_profile_sha256") != _sha(canonical_bytes(profile_binding))
                    or any(receipt.get(field) is not True for field in required)):
                issues.append("independent_execution_preflight_failed")
            evidence = receipt.get("evidence", {})
            for field in required:
                binding = evidence.get(field)
                if not isinstance(binding, Mapping) or not binding.get("path") or not binding.get("sha256"):
                    issues.append("independent_preflight_evidence_missing:" + field)
                elif _sha(_root(binding["path"]).read_bytes()) != binding["sha256"]:
                    issues.append("independent_preflight_evidence_changed:" + field)
    return value, issues


def prepare_evaluation(preparation_root: Path, output_root: Path, *, repository_root: Path,
        package_descriptors: Mapping | None = None, execution_profile: Mapping | None = None,
        fixture_mode: bool = False) -> dict:
    """Freeze 24 isolated cells; preparing never submits an author request."""
    product = _root(repository_root)
    output = _root(output_root)
    preparation = inspect_preparation(preparation_root)
    if not isinstance(fixture_mode, bool):
        raise EvaluationError("fixture mode must be an explicit Boolean")
    if not fixture_mode and (preparation["frozen_manifest_sha256"] != FROZEN_PREPARATION_SHA or preparation["ready_sha256"] != FROZEN_READY_SHA):
        raise EvaluationError("real trials require the exact approved public preparation freeze")
    _outside(output, [product, _root(preparation_root)])
    if output.exists() and any(output.iterdir()):
        raise EvaluationError("evaluation run root must be new and empty")
    profile, blockers = _profile(execution_profile, fixture_mode=fixture_mode)
    packages, package_bytes = {}, {}
    for arm in ("O", "N"):
        descriptor = (package_descriptors or {}).get(arm)
        if not descriptor:
            blockers.append("old_package_missing" if arm == "O" else "p13_candidate_missing")
            continue
        _outside(output, [_root(descriptor["repository_root"])])
        try:
            packages[arm], package_bytes[arm] = _package(descriptor, arm=arm, fixture_mode=fixture_mode)
        except (EvaluationError, OSError, KeyError, zipfile.BadZipFile) as exc:
            blockers.append(f"{arm}_package_invalid: {exc}")
    output.mkdir(parents=True, exist_ok=True)
    (output / "controller").mkdir()
    (output / "trials").mkdir()
    prep = _root(preparation_root)
    tasks = {row["id"]: row for row in [*preparation["tasks"]["debug_tasks"], *preparation["tasks"]["holdout_tasks"]]}
    route = [{"task_id": task_id, "arm": arm, "split": "debug", "pass": 0}
             for task_id in ("D01", "D02") for arm in ARMS] + preparation["holdout_route"]
    cells = []
    common = _read(prep, "arm-contexts/common-author-instructions.md")
    for row in route:
        opaque = secrets.token_hex(16)
        relative = "trials/" + opaque
        workspace = output / relative / "workspace"
        workspace.mkdir(parents=True)
        task = tasks[row["task_id"]]
        task_bytes = _read(prep, task["prompt"])
        (workspace / "task.md").write_bytes(task_bytes)
        (workspace / "instructions.md").write_bytes(common)
        source_members = []
        for material in task["author_materials"]:
            raw = _read(prep, material)
            name = "sources/" + PurePosixPath(material).name
            if (workspace / name).exists():
                raise EvaluationError("author sources collide after isolated mounting")
            (workspace / name).parent.mkdir(exist_ok=True)
            (workspace / name).write_bytes(raw)
            source_members.append({**_identity(name, raw), "frozen_preparation_path": material})
        if row["arm"] == "S":
            (workspace / "method.md").write_bytes(_read(prep, "arm-contexts/simple-method.md"))
            method = "Read method.md and apply its source-grounded method."
        else:
            for name, raw in package_bytes.get(row["arm"], {}).items():
                target = workspace / "framework" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            method = "Read framework/SKILL.md and its needed local references as the method. Framework text supplies no new world facts."
        prompt = common.decode("utf-8") + "\n\n" + method + (
            "\nRead task.md and the listed local sources only. Use a fresh single author response. "
            "Do not invoke another model, browse, access external paths, or reveal package identity. "
            "Requested maximum output is 6000 tokens. Do not continue after truncation. "
            "Write the substantive final Chinese answer in the last assistant message.\n"
            + "\n".join(member["path"] for member in source_members) + "\n")
        (workspace / "prompt.txt").write_bytes(prompt.encode("utf-8"))
        frozen_inputs = [_identity(path.relative_to(workspace).as_posix(), path.read_bytes())
            for path in sorted(workspace.rglob("*")) if path.is_file()]
        mounted_characters = binary_bytes = 0
        for path in workspace.rglob("*"):
            if path.is_file():
                raw = path.read_bytes()
                try:
                    mounted_characters += len(raw.decode("utf-8").replace("\r\n", "\n"))
                except UnicodeDecodeError:
                    binary_bytes += len(raw)
        input_receipt = {"task_sha256": _sha(task_bytes), "task_bytes": len(task_bytes),
            "fact_materials": source_members, "fact_material_bytes": sum(member["bytes"] for member in source_members),
            "framework": packages.get(row["arm"]), "prompt_sha256": _sha(prompt.encode("utf-8")),
            "prompt_bytes": len(prompt.encode("utf-8")), "normalized_prompt_characters": len(prompt.replace("\r\n", "\n")),
            "mounted_utf8_normalized_characters": mounted_characters, "mounted_binary_bytes": binary_bytes,
            "character_accounting_scope": "exact mounted UTF-8 files; binary and unread files are not model-read attestations",
            "frozen_files": frozen_inputs, "tool_manifest": {"fact_scope": "closed-input", "network": "disabled",
                "local_file_reading": True, "model_followups": False, "grader_materials": False}}
        receipt_path = relative + "/receipt.json"
        cell = {**row, "trial_id": opaque, "workspace_path": relative + "/workspace", "receipt_path": receipt_path,
            "answer_path": relative + "/answer.md", "status": "not_run", "comparability": "notComparable",
            "comparison_issues": list(blockers) or ["not_executed"]}
        receipt = {"schema_id": "xi-kari.v4.evaluation-cell", "fixture_only": fixture_mode,
            "task_id": row["task_id"], "arm": row["arm"], "split": row["split"], "input_receipt": input_receipt,
            "requested_budget": {"max_output_tokens": OUTPUT_TOKENS, "timeout_seconds": TIMEOUT_SECONDS,
                "author_turns": 1, "infrastructure_retries": 1, "semantic_retries": 0,
                "hard_output_ceiling": "unavailable; requested in the prompt"}, "attempts": [], "status": "not_run",
            "comparability": "notComparable", "comparison_issues": cell["comparison_issues"], "output": None}
        _write(output / receipt_path, receipt)
        cell["receipt_sha256"] = _sha(_read(output, receipt_path))
        cells.append(cell)
    plan = {"schema_id": "xi-kari.v4.evaluation-plan", "created_at_utc": _utc(), "fixture_only": fixture_mode,
        "repository_root": str(product), "preparation": preparation, "execution_profile": profile,
        "package_descriptors": deepcopy(dict(package_descriptors or {})), "packages": packages,
        "launch_blockers": blockers, "cells": cells, "planned_holdout_cells": 18,
        "planned_holdout_pairwise_comparisons": 18, "planned_debug_cells": 6,
        "actual_model_runs": 0, "actual_grader_runs": 0, "p14_complete": False}
    _write(output / "controller/plan.json", plan)
    _write(output / "controller/plan-binding.json", {"plan_sha256": _sha(_read(output, "controller/plan.json"))})
    return plan


def _load_plan(root: Path) -> dict:
    binding = _json(root, "controller/plan-binding.json")
    if _sha(_read(root, "controller/plan.json")) != binding.get("plan_sha256"):
        raise EvaluationError("frozen evaluation plan differs from its binding")
    return _json(root, "controller/plan.json")


def _environment(attempt: Path) -> dict[str, str]:
    allowed = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "USERPROFILE", "HOMEDRIVE", "HOMEPATH",
        "HOME", "APPDATA", "LOCALAPPDATA", "CODEX_HOME", "LANG", "LC_ALL"}
    environment = {name: value for name, value in os.environ.items() if name.upper() in allowed}
    temporary = attempt / "temporary"
    temporary.mkdir(exist_ok=True)
    environment.update(TMP=str(temporary), TEMP=str(temporary), PYTHONDONTWRITEBYTECODE="1")
    return environment


def execute_process(request: Mapping) -> dict:
    """Launch a real child, preserve raw bytes, reap it, and read completion files."""
    attempt = _root(request["attempt_directory"])
    start = time.monotonic()
    process = {"submitted_at_utc": _utc(), "pid": None, "return_code": None, "timed_out": False,
        "launched": False, "launch_error": None}
    stdout = stderr = b""
    try:
        child = subprocess.Popen(list(request["argv"]), cwd=request["workspace"], env=_environment(attempt),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            start_new_session=os.name != "nt")
        process.update(pid=child.pid, launched=True)
        try:
            stdout, stderr = child.communicate(request["input_bytes"], timeout=request["timeout_seconds"])
        except subprocess.TimeoutExpired:
            process["timed_out"] = True
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"], capture_output=True, check=False)
            else:
                import signal
                os.killpg(child.pid, signal.SIGKILL)
            stdout, stderr = child.communicate()
        process["return_code"] = child.returncode
    except OSError as exc:
        process["launch_error"] = f"{type(exc).__name__}: {exc}"
    (attempt / "stdout.jsonl").write_bytes(stdout)
    (attempt / "stderr.txt").write_bytes(stderr)
    process.update(completed_at_utc=_utc(), wall_time_seconds=time.monotonic() - start)
    _write(attempt / "process.json", process)
    return process


def _codex_argv(profile: Mapping, workspace: Path, last_message: Path) -> list[str]:
    runtime_roots = {Path(profile["executable"]).resolve().parent.parent,
                     Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()}
    filesystem = {":root": "deny", ":minimal": "read", workspace.resolve().as_posix(): "write",
                  **{path.as_posix(): "read" for path in sorted(runtime_roots)}}
    filesystem_toml = "{" + ",".join(json.dumps(key) + "=" + json.dumps(value) for key, value in filesystem.items()) + "}"
    settings = {'model_reasoning_effort': '"max"', 'model_provider': '"openai"',
        'forced_login_method': '"chatgpt"', 'approval_policy': '"never"',
        'default_permissions': '"xikari_p14_author"',
        'permissions.xikari_p14_author': '{filesystem=' + filesystem_toml + ',network={enabled=false}}',
        'web_search': '"disabled"',
        'features.apps': 'false', 'features.multi_agent': 'false', 'features.skill_mcp_dependency_install': 'false',
        'features.plugins': 'false', 'features.memories': 'false', 'features.hooks': 'false',
        'features.shell_snapshot': 'false', 'check_for_update_on_startup': 'false',
        'project_doc_max_bytes': '0', 'mcp_servers': '{}'}
    argv = [profile["executable"], "--no-daemon", "exec", "--ignore-user-config", "--ignore-rules",
        "--strict-config", "--json", "--skip-git-repo-check", "--model", MODEL,
        "--cd", str(workspace), "--output-last-message", str(last_message)]
    for name, value in settings.items():
        argv.extend(["--config", name + "=" + value])
    return [*profile.get("isolation_command_prefix", []), *argv, "-"]


def _observed_session(thread_id: str | None, *, session_root: Path | None = None) -> dict:
    """Inspect only the newly emitted thread ID's session, never old conversations."""
    if not thread_id or re.fullmatch(r"[0-9a-f-]{36}", thread_id) is None:
        return {}
    sessions = (_root(session_root) if session_root is not None else
                Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "sessions")
    candidates = list(sessions.glob(f"*/*/*/*{thread_id}.jsonl"))
    if len(candidates) != 1:
        return {}
    value = {}
    for line in candidates[0].read_bytes().splitlines():
        try:
            event = read_json_text(line.decode("utf-8"))
        except (UnicodeError, ValueError):
            continue
        payload = event.get("payload", {})
        if event.get("type") == "turn_context":
            value.update(model=payload.get("model"), reasoning_effort=payload.get("effort") or payload.get("reasoning_effort"))
        if event.get("type") == "session_meta":
            value["provider"] = payload.get("model_provider")
    value["session_metadata_sha256"] = _sha(canonical_bytes(value))
    value["observation_source"] = "new Codex session metadata; remote resolved model version is not exposed"
    return value


def _collect(root: Path, attempt: Path, process: Mapping, *, fixture_only: bool) -> dict:
    process_raw = _read(attempt, "process.json")
    if read_json_text(process_raw.decode("utf-8")) != dict(process):
        raise EvaluationError("process completion receipt differs from disk")
    stdout = (attempt / "stdout.jsonl").read_bytes()
    stderr = (attempt / "stderr.txt").read_bytes()
    events, parse_errors = [], 0
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = read_json_text(line.decode("utf-8"))
            if not isinstance(event, dict):
                raise ValueError("event is not an object")
            events.append(event)
        except (UnicodeError, ValueError):
            parse_errors += 1
    usage = {"input_tokens": None, "output_tokens": None, "cached_input_tokens": None, "reasoning_output_tokens": None}
    observed, messages, items = {}, [], {}
    turns, completed, failed = 0, False, False
    thread_id = None
    finish_reason = None
    for event in events:
        kind = event.get("type")
        if kind == "thread.started":
            thread_id = event.get("thread_id")
        if kind == "runner.observed" and fixture_only:
            observed.update({key: event.get(key) for key in ("model", "reasoning_effort", "provider", "generation_started")})
            finish_reason = event.get("finish_reason")
        if kind == "turn.started":
            turns += 1
        if kind in {"turn.completed", "turn.failed"}:
            completed |= kind == "turn.completed"
            failed |= kind == "turn.failed"
            for name in usage:
                tokens = event.get("usage", {}).get(name)
                if isinstance(tokens, int) and not isinstance(tokens, bool) and tokens >= 0:
                    usage[name] = tokens
            finish_reason = event.get("finish_reason", finish_reason)
        if kind.startswith("item.") and isinstance(event.get("item"), Mapping):
            item = event["item"]
            items[item.get("id") or str(len(items))] = item
            if kind == "item.completed" and item.get("type") == "agent_message" and isinstance(item.get("text"), str):
                messages.append(item["text"])
    if not fixture_only:
        observed.update(_observed_session(thread_id, session_root=attempt / "codex-sessions"))
    last_message = attempt / "last-message.md"
    answer = last_message.read_bytes() if last_message.is_file() else (messages[-1].encode("utf-8") if messages else b"")
    try:
        answer.decode("utf-8")
        answer_utf8 = True
    except UnicodeDecodeError:
        answer_utf8 = False
    generation = observed.get("generation_started")
    if generation is None:
        generation = True if messages or any((value or 0) > 0 for value in usage.values()) else None
    before = generation is False and usage["output_tokens"] == 0 and not messages
    error_text = "\n".join(str(event) for event in events if event.get("type") in {"error", "turn.failed"})
    configuration_unavailable = re.search(
        r"model_not_found|unsupported_reasoning_effort|model[^\n]*(?:not supported|does not exist)|reasoning[^\n]*not supported",
        error_text, re.IGNORECASE) is not None
    status = "completed"
    if not process.get("launched"):
        status = "not_run"
    elif process.get("timed_out"):
        status = "timeout_after_generation"
    elif configuration_unavailable:
        status = "not_run"
    elif finish_reason in {"length", "max_output_tokens"} or (usage["output_tokens"] or 0) > OUTPUT_TOKENS:
        status = "incomplete_truncated"
    elif any(event.get("type") == "refusal" or event.get("refusal") for event in events):
        status = "refused"
    elif failed or process.get("return_code") != 0:
        status = "provider_error_before_generation" if before else "invalid_artifact"
    elif not completed or not answer.strip() or parse_errors or not answer_utf8:
        status = "invalid_artifact"
    issues = []
    for field, expected, label in (("model", MODEL, "model"), ("reasoning_effort", EFFORT, "reasoning_effort"),
                                   ("provider", "fixture" if fixture_only else "openai", "provider")):
        if observed.get(field) != expected:
            issues.append(label + ("_unavailable" if observed.get(field) is None else "_mismatch"))
    if turns > 1:
        issues.append("multiple_author_turns")
    if configuration_unavailable:
        issues.append("exact_model_effort_unavailable")
    if status != "completed":
        issues.append(status)
    if any(item.get("type") in {"web_search", "mcp_tool_call", "browser_action"} for item in items.values()):
        issues.append("external_tool_use")
    forbidden_reference = any(re.search(r"grader-only[\\/]", str({field: item.get(field)
        for field in ("command", "arguments", "input", "path")})) is not None for item in items.values())
    if forbidden_reference:
        issues.append("grader_path_reference")
    record = {"process": deepcopy(dict(process)), "status": status, "observed_configuration": observed,
        "attempt_directory": attempt.relative_to(root).as_posix(),
        "requested_configuration": {"model": MODEL, "reasoning_effort": EFFORT,
            "provider": "codex_subscription" if not fixture_only else "deterministic_fixture"},
        "usage": usage, "token_accounting": ("deterministic_fixture" if fixture_only else "provider_reported_through_codex") if usage["input_tokens"] is not None else "unavailable",
        "finish_reason": finish_reason if finish_reason is not None else "unavailable",
        "cache_status": "unavailable" if usage["cached_input_tokens"] is None else "reported",
        "turns": turns, "tool_calls": sum(item.get("type") not in {"agent_message", "reasoning", "plan_update"} for item in items.values()),
        "generation_started": generation, "zero_generation_confirmed": before,
        "comparison_issues": issues, "grader_path_reference_detected": forbidden_reference,
        "grader_only_access_detected": None,
        "raw_stdout": _identity(str((attempt / "stdout.jsonl").relative_to(root).as_posix()), stdout),
        "raw_stderr": _identity(str((attempt / "stderr.txt").relative_to(root).as_posix()), stderr),
        "launch_receipt": _identity(str((attempt / "launch.json").relative_to(root).as_posix()), _read(attempt, "launch.json")),
        "process_receipt": _identity(str((attempt / "process.json").relative_to(root).as_posix()), process_raw),
        "answer_sha256": _sha(answer), "answer_bytes": len(answer), "fixture_only": fixture_only}
    (attempt / "collected-answer.md").write_bytes(answer)
    _write(attempt / "attempt-receipt.json", record)
    return record


def _check_inputs(root: Path, cell: Mapping, receipt: Mapping) -> None:
    workspace = root / cell["workspace_path"]
    for binding in receipt["input_receipt"]["frozen_files"]:
        raw = _read(workspace, binding["path"])
        if _sha(raw) != binding["sha256"] or len(raw) != binding["bytes"]:
            raise EvaluationError("frozen author input bytes changed")


def _summary(root: Path, plan: Mapping, cells: list[dict]) -> dict:
    launches = actual = 0
    for cell in cells:
        receipt = _json(root, cell["receipt_path"])
        for attempt in receipt["attempts"]:
            launches += int(attempt["process"].get("launched") is True)
            actual += int(not plan["fixture_only"] and attempt.get("generation_started") is True)
    return {"schema_id": "xi-kari.v4.evaluation-results", "fixture_only": plan["fixture_only"],
        "cells": cells, "author_process_launches": launches, "actual_model_runs": actual, "actual_grader_runs": 0,
        "planned_holdout_cells": 18, "planned_holdout_pairwise_comparisons": 18,
        "scored_holdout_comparisons": 0, "debug_in_comparative_claims": False, "p14_complete": False,
        "scores": None, "score_status": "not_graded", "capability_result_available": False}


def run_evaluation(output_root: Path, *, split: str = "holdout", execute: Callable | None = None) -> dict:
    """Run or resume in frozen order; completed and failed observations never rerun."""
    root = _root(output_root)
    plan = _load_plan(root)
    if split not in {"debug", "holdout"}:
        raise EvaluationError("execution split must be debug or holdout")
    if not plan["fixture_only"] and execute is not None:
        raise EvaluationError("injected process fixtures cannot authorize real evaluation")
    cells = deepcopy(_json(root, "controller/results.json")["cells"] if (root / "controller/results.json").exists() else plan["cells"])
    audit_evaluation(root)
    if not plan["launch_blockers"]:
        for arm in ("O", "N"):
            identity, _ = _package(plan["package_descriptors"][arm], arm=arm, fixture_mode=plan["fixture_only"])
            if identity != plan["packages"][arm]:
                raise EvaluationError("frozen package identity changed before execution")
        profile, issues = _profile(plan["execution_profile"], fixture_mode=plan["fixture_only"])
        if issues or profile != plan["execution_profile"]:
            raise EvaluationError("frozen execution profile changed before execution")
    else:
        result = _summary(root, plan, cells)
        _write(root / "controller/results.json", result)
        return result
    for cell in cells:
        if cell["split"] != split:
            continue
        receipt = _json(root, cell["receipt_path"])
        if receipt["attempts"] or receipt["comparison_issues"] == ["interrupted_attempt_preserved"] or "exact_model_effort_unavailable" in receipt["comparison_issues"]:
            continue
        workspace = root / cell["workspace_path"]
        for ordinal in (1, 2):
            if not plan["fixture_only"]:
                checked_profile, profile_issues = _profile(plan["execution_profile"], fixture_mode=False)
                if profile_issues or checked_profile != plan["execution_profile"]:
                    raise EvaluationError("frozen isolation launcher or provider changed before execution")
            attempt = root / cell["workspace_path"]
            attempt = attempt.parent / ("attempt-" + str(ordinal))
            if attempt.exists():
                receipt["status"] = "invalid_artifact"
                receipt["comparison_issues"] = ["interrupted_attempt_preserved"]
                break
            attempt.mkdir()
            argv = _codex_argv(plan["execution_profile"], workspace, workspace / "answer.md") if not plan["fixture_only"] else [plan["execution_profile"]["executable"]]
            request = {"argv": argv, "workspace": str(workspace), "attempt_directory": str(attempt),
                "input_bytes": _read(workspace, "prompt.txt"), "timeout_seconds": TIMEOUT_SECONDS,
                "output_path": str(workspace / "answer.md"), "fixture_only": plan["fixture_only"]}
            _write(attempt / "launch.json", {key: value for key, value in request.items() if key != "input_bytes"})
            process = None
            try:
                process = (execute or execute_process)(request)
                if not isinstance(process, Mapping):
                    raise EvaluationError("process executor returned no completion receipt")
                if (workspace / "answer.md").is_file():
                    (attempt / "last-message.md").write_bytes((workspace / "answer.md").read_bytes())
                record = _collect(root, attempt, process, fixture_only=plan["fixture_only"])
            except Exception as exc:
                process_path = attempt / "process.json"
                preserved_process = _json(attempt, "process.json") if process_path.is_file() else (
                    dict(process) if isinstance(process, Mapping) else {"launched": None, "return_code": None, "launch_error": str(exc)})
                record = {"process": preserved_process, "attempt_directory": attempt.relative_to(root).as_posix(),
                    "status": "invalid_artifact", "comparison_issues": ["executor_or_artifact_failure"],
                    "generation_started": None, "zero_generation_confirmed": False,
                    "fixture_only": plan["fixture_only"]}
                _write(attempt / "attempt-receipt.json", record)
            receipt["attempts"].append(record)
            receipt.update(status=record["status"], comparison_issues=record["comparison_issues"],
                comparability="notComparable" if record["comparison_issues"] else "comparable")
            answer = attempt / "collected-answer.md"
            if answer.is_file():
                final = root / cell["answer_path"]
                final.write_bytes(answer.read_bytes())
                receipt["output"] = _identity(cell["answer_path"], final.read_bytes())
            _write(root / cell["receipt_path"], receipt)
            if not (ordinal == 1 and record["status"] == "provider_error_before_generation" and record["zero_generation_confirmed"] is True):
                break
        cell.update(status=receipt["status"], comparability=receipt["comparability"], comparison_issues=receipt["comparison_issues"],
            receipt_sha256=_sha(_read(root, cell["receipt_path"])))
        if "exact_model_effort_unavailable" in receipt["comparison_issues"]:
            for remaining in cells:
                remaining_receipt = _json(root, remaining["receipt_path"])
                if not remaining_receipt["attempts"]:
                    remaining_receipt.update(status="not_run", comparability="notComparable",
                        comparison_issues=["exact_model_effort_unavailable"])
                    _write(root / remaining["receipt_path"], remaining_receipt)
                    remaining.update(status="not_run", comparability="notComparable", comparison_issues=remaining_receipt["comparison_issues"],
                        receipt_sha256=_sha(_read(root, remaining["receipt_path"])))
        _write(root / "controller/results.json", _summary(root, plan, cells))
    result = _summary(root, plan, cells)
    _write(root / "controller/results.json", result)
    return result


def audit_evaluation(output_root: Path) -> dict:
    """Fresh read-only verification of frozen inputs, output and raw-process receipts."""
    root = _root(output_root)
    plan = _load_plan(root)
    cells = _json(root, "controller/results.json")["cells"] if (root / "controller/results.json").exists() else plan["cells"]
    for cell in cells:
        raw = _read(root, cell["receipt_path"])
        if _sha(raw) != cell["receipt_sha256"]:
            raise EvaluationError("frozen cell receipt changed")
        receipt = read_json_text(raw.decode("utf-8"))
        _check_inputs(root, cell, receipt)
        if receipt.get("output"):
            binding = receipt["output"]
            raw = _read(root, binding["path"])
            if _sha(raw) != binding["sha256"] or len(raw) != binding["bytes"]:
                raise EvaluationError("frozen output changed")
        for attempt in receipt["attempts"]:
            persisted = _json(root, attempt["attempt_directory"] + "/attempt-receipt.json")
            if persisted != attempt:
                raise EvaluationError("frozen attempt receipt changed")
            for field in ("raw_stdout", "raw_stderr", "launch_receipt", "process_receipt"):
                binding = attempt.get(field)
                if binding and _sha(_read(root, binding["path"])) != binding["sha256"]:
                    raise EvaluationError("frozen raw process output changed")
    for split in ("debug", "holdout"):
        export_path = root / f"controller/blinding-export-{split}.json"
        if export_path.is_file():
            export = _json(root, export_path.relative_to(root).as_posix())
            grader = _root(export["grader_root"])
            manifest_raw = _read(grader, "manifest.json")
            if (_sha(manifest_raw) != export["manifest_sha256"] or
                    _sha(_read(root, f"controller/blinding-map-{split}.json")) != export["map_sha256"]):
                raise EvaluationError("frozen blinding manifest or map changed")
            manifest = read_json_text(manifest_raw.decode("utf-8"))
            for row in manifest["outputs"]:
                if _sha(_read(grader, row["answer_path"])) != row["answer_sha256"]:
                    raise EvaluationError("frozen blinded output changed")
            for task in manifest["public_tasks"]:
                for binding in task["files"]:
                    if _sha(_read(grader, binding["path"])) != binding["sha256"]:
                        raise EvaluationError("frozen grader public source changed")
    return {"integrity_passed": True, "checked_cells": len(cells), "fixture_only": plan["fixture_only"],
        "actual_grader_runs": 0, "p14_complete": False}


def blind_evaluation(output_root: Path, grader_root: Path, *, split: str = "holdout") -> dict:
    """Export immutable opaque outputs without keys, arm maps or raw provider traces."""
    root, grader = _root(output_root), _root(grader_root)
    plan = _load_plan(root)
    audit_evaluation(root)
    _outside(grader, [root, _root(plan["repository_root"]), _root(plan["preparation"]["preparation_root"])])
    if split not in {"debug", "holdout"} or (grader.exists() and any(grader.iterdir())):
        raise EvaluationError("grader root must be new and split must be explicit")
    results = _json(root, "controller/results.json")
    selected_cells = [row for row in results["cells"] if row["split"] == split]
    if any(row["comparison_issues"] == ["not_executed"] for row in selected_cells):
        raise EvaluationError("author observations must be finalized before blinding")
    mapping_path = root / f"controller/blinding-map-{split}.json"
    if mapping_path.exists():
        raise EvaluationError("blinding map is already frozen")
    grader.mkdir(parents=True, exist_ok=True)
    cells = selected_cells
    secrets.SystemRandom().shuffle(cells)
    mapping, outputs = [], []
    task_exports = {}
    for cell in cells:
        opaque = secrets.token_hex(16)
        answer_path = f"outputs/{opaque}/answer.md"
        source = root / cell["answer_path"]
        try:
            text = source.read_text(encoding="utf-8") if source.is_file() else ""
        except UnicodeDecodeError:
            text = "[答文不是UTF-8；原始输出已保留。]"
        replacements = [str(root), str(plan["repository_root"]), cell["trial_id"]]
        for descriptor in plan["package_descriptors"].values():
            replacements.extend([descriptor["repository_root"], descriptor["package_path"], descriptor["commit"], descriptor["git_tree"]])
        for value in sorted(replacements, key=len, reverse=True):
            text = text.replace(value, "[内部标识已隐藏]").replace(value.replace("\\", "/"), "[内部标识已隐藏]")
        text = re.sub(r"(?im)^\s*(?:实验臂|experiment arm|arm)\s*[:：=]\s*[SON].*$", "[内部标识已隐藏]", text)
        text = re.sub(r"(?i)\b(?:Xi-Kari|xi-kari-skill|old Skill|new Skill|simple method|gpt-6\.1-sol|v8\.3|v9\.0)\b", "[方法标识已隐藏]", text)
        target = grader / answer_path
        target.parent.mkdir(parents=True)
        target.write_text(text, encoding="utf-8")
        reader = {"opaque_id": opaque, "task_id": cell["task_id"], "split": split,
            "answer_path": answer_path, "answer_sha256": _sha(target.read_bytes()), "operational_status": cell["status"],
            "comparability": cell["comparability"], "identity_redaction_review_required": True}
        outputs.append(reader)
        if cell["task_id"] not in task_exports:
            receipt = _json(root, cell["receipt_path"])
            workspace = root / cell["workspace_path"]
            public_members = []
            for name in ["task.md", *[member["path"] for member in receipt["input_receipt"]["fact_materials"]]]:
                raw = _read(workspace, name)
                destination = "tasks/" + cell["task_id"] + "/" + name
                target = grader / destination
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                public_members.append(_identity(destination, raw))
            task_exports[cell["task_id"]] = {"task_id": cell["task_id"], "files": public_members}
        mapping.append({"opaque_id": opaque, "task_id": cell["task_id"], "arm": cell["arm"],
            "trial_id": cell["trial_id"], "original_answer_sha256": _sha(source.read_bytes()) if source.is_file() else None,
            "blinded_answer_sha256": reader["answer_sha256"]})
    _write(mapping_path, {"schema_id": "xi-kari.v4.sealed-evaluation-map", "split": split, "entries": mapping})
    manifest = {"schema_id": "xi-kari.v4.blinded-evaluation", "fixture_only": plan["fixture_only"],
        "outputs": outputs, "public_tasks": list(task_exports.values()), "scores": None,
        "score_status": "not_graded", "p14_complete": False,
        "private_keys_supplied_by_authorized_controller_separately": True}
    _write(grader / "manifest.json", manifest)
    _write(root / f"controller/blinding-export-{split}.json", {"grader_root": str(grader),
        "manifest_sha256": _sha(_read(grader, "manifest.json")), "map_sha256": _sha(mapping_path.read_bytes())})
    return manifest
