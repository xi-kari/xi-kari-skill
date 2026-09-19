"""Runtime-owned fresh-process stance stability for XK9."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

from .canonical_json import read_json, sha256_file


def _probe(
    *,
    packet_path: Path,
    authoring_bundle_path: Path,
    run_contract_path: Path,
    source_lock_path: Path,
    read_plan_path: Path,
    repository_root: Path,
    requested_stance: str,
    time_window: str | None = None,
    mutation: str | None = None,
) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "scripts.xi_kari_runtime.semantic_probe",
        "--packet",
        str(packet_path),
        "--authoring-bundle",
        str(authoring_bundle_path),
        "--run-contract",
        str(run_contract_path),
        "--source-lock",
        str(source_lock_path),
        "--read-plan",
        str(read_plan_path),
        "--repository-root",
        str(repository_root),
        "--requested-stance",
        requested_stance,
    ]
    if time_window is not None:
        command.extend(("--time-window", time_window))
    if mutation is not None:
        command.extend(("--mutation", mutation))
    completed = subprocess.run(
        command,
        cwd=repository_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    if completed.returncode != 0:
        raise ValueError(
            "fresh semantic probe process failed: "
            + (completed.stderr.strip() or f"exit {completed.returncode}")
        )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("fresh semantic probe returned invalid JSON") from exc
    if not isinstance(result, dict):
        raise ValueError("fresh semantic probe result is not an object")
    return result


def _semantic_run_projection(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: record.get(key)
        for key in (
            "requested_stance",
            "authoring_id",
            "authoring_provenance_sha256",
            "input_variant_sha256",
            "invariant_projection_sha256",
            "downstream_projection_sha256",
            "verdict_sha256",
            "action_ranking_sha256",
            "valid",
            "errors",
        )
    }


def build_stance_stability_report(
    *,
    packet_path: Path,
    authoring_bundle_path: Path,
    run_contract_path: Path,
    source_lock_path: Path,
    read_plan_path: Path,
    repository_root: Path,
) -> dict[str, Any]:
    contract = read_json(run_contract_path)
    runs = [
        _probe(
            packet_path=packet_path,
            authoring_bundle_path=authoring_bundle_path,
            run_contract_path=run_contract_path,
            source_lock_path=source_lock_path,
            read_plan_path=read_plan_path,
            repository_root=repository_root,
            requested_stance=stance,
        )
        for stance in ("support", "oppose")
    ]
    if runs[0].get("process_pid") == runs[1].get("process_pid"):
        runs[1] = _probe(
            packet_path=packet_path,
            authoring_bundle_path=authoring_bundle_path,
            run_contract_path=run_contract_path,
            source_lock_path=source_lock_path,
            read_plan_path=read_plan_path,
            repository_root=repository_root,
            requested_stance="oppose",
        )
    invariant_hashes = {
        record.get("invariant_projection_sha256") for record in runs
    }
    verdict_hashes = {record.get("verdict_sha256") for record in runs}
    action_hashes = {record.get("action_ranking_sha256") for record in runs}
    authoring_ids = {record.get("authoring_id") for record in runs}
    authoring_provenance = {
        record.get("authoring_provenance_sha256") for record in runs
    }
    stable = (
        all(record.get("valid") is True and record.get("errors") == [] for record in runs)
        and {record.get("requested_stance") for record in runs}
        == {"support", "oppose"}
        and len({record.get("process_pid") for record in runs}) == 2
        and len(authoring_ids) == 2
        and None not in authoring_ids
        and len(authoring_provenance) == 2
        and None not in authoring_provenance
        and len(invariant_hashes) == 1
        and len(verdict_hashes) == 1
        and len(action_hashes) == 1
    )
    if not stable:
        raise ValueError("fresh semantic stance pair is not evidence-invariant")
    return {
        "schema_id": "xi-kari.v3.stance-stability-report",
        "schema_version": 3,
        "run_id": contract["run_id"],
        "input_packet_sha256": sha256_file(packet_path),
        "neutrality_key": contract["stance_neutrality_key"],
        "runs": runs,
        "invariant_projection_sha256": next(iter(invariant_hashes)),
        "stable": True,
    }


def validate_stance_stability_report(
    report: Mapping[str, Any],
    *,
    packet_path: Path,
    authoring_bundle_path: Path,
    run_contract_path: Path,
    source_lock_path: Path,
    read_plan_path: Path,
    repository_root: Path,
) -> list[str]:
    errors: list[str] = []
    try:
        fresh = build_stance_stability_report(
            packet_path=packet_path,
            authoring_bundle_path=authoring_bundle_path,
            run_contract_path=run_contract_path,
            source_lock_path=source_lock_path,
            read_plan_path=read_plan_path,
            repository_root=repository_root,
        )
    except Exception as exc:
        return [f"XK9 fresh stance stability probe failed: {exc}"]
    for field in (
        "schema_id",
        "schema_version",
        "run_id",
        "input_packet_sha256",
        "neutrality_key",
        "invariant_projection_sha256",
        "stable",
    ):
        if report.get(field) != fresh.get(field):
            errors.append("XK9 stance stability differs from fresh semantic probes")
            return errors
    authored_runs = report.get("runs")
    if not isinstance(authored_runs, list) or len(authored_runs) != 2:
        return ["XK9 stance stability differs from fresh semantic probes"]
    authored_by_stance = {
        record.get("requested_stance"): _semantic_run_projection(record)
        for record in authored_runs
        if isinstance(record, Mapping)
    }
    fresh_by_stance = {
        record.get("requested_stance"): _semantic_run_projection(record)
        for record in fresh["runs"]
    }
    if authored_by_stance != fresh_by_stance:
        errors.append("XK9 stance stability differs from fresh semantic probes")
    if len(
        {
            record.get("process_pid")
            for record in authored_runs
            if isinstance(record, Mapping)
        }
    ) != 2:
        errors.append("XK9 stance stability lacks two independent process receipts")
    return errors


def build_sensitivity_report(
    *,
    packet_path: Path,
    authoring_bundle_path: Path,
    run_contract_path: Path,
    source_lock_path: Path,
    read_plan_path: Path,
    repository_root: Path,
    baseline_projection_sha256: str,
) -> dict[str, Any]:
    contract = read_json(run_contract_path)
    stance_support = _probe(
        packet_path=packet_path,
        authoring_bundle_path=authoring_bundle_path,
        run_contract_path=run_contract_path,
        source_lock_path=source_lock_path,
        read_plan_path=read_plan_path,
        repository_root=repository_root,
        requested_stance="support",
    )
    shifted = _probe(
        packet_path=packet_path,
        authoring_bundle_path=authoring_bundle_path,
        run_contract_path=run_contract_path,
        source_lock_path=source_lock_path,
        read_plan_path=read_plan_path,
        repository_root=repository_root,
        requested_stance="support",
        time_window="sensitivity-shifted-window",
    )
    bridge = _probe(
        packet_path=packet_path,
        authoring_bundle_path=authoring_bundle_path,
        run_contract_path=run_contract_path,
        source_lock_path=source_lock_path,
        read_plan_path=read_plan_path,
        repository_root=repository_root,
        requested_stance="support",
        mutation="remove-scale-bridge",
    )
    feedback = _probe(
        packet_path=packet_path,
        authoring_bundle_path=authoring_bundle_path,
        run_contract_path=run_contract_path,
        source_lock_path=source_lock_path,
        read_plan_path=read_plan_path,
        repository_root=repository_root,
        requested_stance="support",
        mutation="remove-second-order-feedback",
    )
    if not (
        stance_support.get("valid")
        and stance_support.get("invariant_projection_sha256")
        == baseline_projection_sha256
    ):
        raise ValueError(
            "semantic sensitivity stance inversion changed an invariant projection"
        )
    if not shifted.get("valid"):
        raise ValueError("semantic sensitivity time-window shift did not validate")
    if bridge.get("valid"):
        raise ValueError(
            "semantic sensitivity probe accepted removal of the sole scale bridge"
        )
    if feedback.get("valid"):
        raise ValueError(
            "semantic sensitivity probe accepted removal of required second-order feedback"
        )
    time_window_status = (
        "changed-downstream"
        if shifted.get("downstream_projection_sha256")
        != stance_support.get("downstream_projection_sha256")
        else "invariant"
    )
    probes = [
        {
            "probe_id": "stance-inversion",
            "expected_effect": "改变用户立场标签不应改变同一证据下的结构判断和行动排序。",
            "observed_status": "invariant"
            if stance_support.get("valid")
            and stance_support.get("invariant_projection_sha256") == baseline_projection_sha256
            else "changed-downstream",
            "authoring_id": stance_support.get("authoring_id"),
            "authoring_provenance_sha256": stance_support.get(
                "authoring_provenance_sha256"
            ),
            "process_pid": stance_support.get("process_pid"),
            "invariant_projection_sha256": stance_support.get(
                "invariant_projection_sha256"
            ),
            "downstream_projection_sha256": stance_support.get(
                "downstream_projection_sha256"
            ),
            "errors": list(stance_support.get("errors", [])),
            "complete": True,
        },
        {
            "probe_id": "time-window-shift",
            "expected_effect": "时间窗变化只改变合法下游绑定，不重写静态结构投影。",
            "observed_status": time_window_status,
            "authoring_id": shifted.get("authoring_id"),
            "authoring_provenance_sha256": shifted.get(
                "authoring_provenance_sha256"
            ),
            "process_pid": shifted.get("process_pid"),
            "invariant_projection_sha256": shifted.get(
                "invariant_projection_sha256"
            ),
            "downstream_projection_sha256": shifted.get(
                "downstream_projection_sha256"
            ),
            "errors": list(shifted.get("errors", [])),
            "complete": True,
        },
        {
            "probe_id": "remove-scale-bridge",
            "expected_effect": "删除唯一跨尺度桥接证据时，尺度变换必须被拒绝。",
            "observed_status": "rejected",
            "authoring_id": bridge.get("authoring_id"),
            "authoring_provenance_sha256": bridge.get(
                "authoring_provenance_sha256"
            ),
            "process_pid": bridge.get("process_pid"),
            "downstream_projection_sha256": bridge.get(
                "downstream_projection_sha256"
            ),
            "errors": list(bridge.get("errors", [])),
            "complete": True,
        },
        {
            "probe_id": "remove-second-order-feedback",
            "expected_effect": "二阶反馈被击穿时，依赖它的三阶路径不得继续。",
            "observed_status": "rejected",
            "authoring_id": feedback.get("authoring_id"),
            "authoring_provenance_sha256": feedback.get(
                "authoring_provenance_sha256"
            ),
            "process_pid": feedback.get("process_pid"),
            "downstream_projection_sha256": feedback.get(
                "downstream_projection_sha256"
            ),
            "errors": list(feedback.get("errors", [])),
            "complete": True,
        },
    ]
    return {
        "schema_id": "xi-kari.v3.sensitivity-report",
        "schema_version": 3,
        "run_id": contract["run_id"],
        "input_packet_sha256": sha256_file(packet_path),
        "probes": probes,
    }


def validate_sensitivity_report(
    report: Mapping[str, Any],
    *,
    packet_path: Path,
    authoring_bundle_path: Path,
    run_contract_path: Path,
    source_lock_path: Path,
    read_plan_path: Path,
    repository_root: Path,
    baseline_projection_sha256: str,
) -> list[str]:
    try:
        fresh = build_sensitivity_report(
            packet_path=packet_path,
            authoring_bundle_path=authoring_bundle_path,
            run_contract_path=run_contract_path,
            source_lock_path=source_lock_path,
            read_plan_path=read_plan_path,
            repository_root=repository_root,
            baseline_projection_sha256=baseline_projection_sha256,
        )
    except Exception as exc:
        return [f"XK9 fresh sensitivity probes failed: {exc}"]
    if dict(report) != fresh:
        # Process IDs are intentionally not trusted as semantic content.
        def normalise(value: Mapping[str, Any]) -> dict[str, Any]:
            copy = json.loads(json.dumps(value))
            for probe in copy.get("probes", []):
                probe.pop("process_pid", None)
            return copy

        if normalise(report) != normalise(fresh):
            return ["XK9 sensitivity report differs from fresh semantic probes"]
    return []


__all__ = (
    "build_stance_stability_report",
    "build_sensitivity_report",
    "validate_stance_stability_report",
    "validate_sensitivity_report",
)
