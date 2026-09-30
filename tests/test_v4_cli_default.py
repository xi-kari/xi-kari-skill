"""Public command defaults select the active production contract."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_cli():
    spec = importlib.util.spec_from_file_location(
        "xi_kari_cli_default_test", ROOT / "scripts" / "xi_kari_runtime.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_execute_without_version_uses_current_production_contract(tmp_path, monkeypatch):
    cli = load_cli()
    observed = {}

    def execute(runs_root, **kwargs):
        observed.update(kwargs)
        return {"state": "prepared", "valid": True}

    monkeypatch.setattr(cli, "execute_authored_run", execute)
    assert cli.main([
        "execute", "--runs-root", str(tmp_path / "runs"),
        "--request-text", "只解释这段材料的含义。",
        "--codex-provider-executable", str(tmp_path / "provider.exe"),
    ]) == 0
    assert observed["contract_version"] == 4
    assert observed["source_version"] is None
    assert observed["mode"] == "open-world"


def test_execute_preserves_explicit_version_for_runtime_compatibility_check():
    cli = load_cli()
    args = cli.build_parser().parse_args([
        "execute", "--request-text", "解释材料。",
        "--codex-provider-executable", "provider.exe",
        "--contract-version", "3", "--source-version", "v8.3",
    ])
    assert args.contract_version == 3
    assert args.source_version == "v8.3"
