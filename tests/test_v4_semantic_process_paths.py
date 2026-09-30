import os
import json
from pathlib import Path
import stat
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from xi_kari_runtime.semantic_executions_v4 import _execution_directories


@pytest.mark.skipif(os.name != 'nt', reason='Windows process current-directory limit')
def test_semantic_process_starts_in_a_deep_run_directory(tmp_path):
    padding = 198 - len(str(tmp_path)) - 1
    if padding < 1:
        pytest.skip('Test root already exceeds the fixed Windows boundary fixture')
    run = tmp_path / ('r' * padding)
    attempt, capture, workspace = _execution_directories(run)
    completed = subprocess.run(
        [sys.executable, '-c', 'print("semantic-cwd-opened")'],
        cwd=workspace, capture_output=True, timeout=10, check=True,
    )
    assert completed.stdout.strip() == b'semantic-cwd-opened'
    assert workspace.parent == capture.parent == attempt
    assert attempt.is_relative_to(run)


@pytest.mark.skipif(os.name != 'nt', reason='Windows inherited workspace ACL')
def test_semantic_provider_directory_preserves_host_acl_inheritance(tmp_path):
    attempt, capture, workspace = _execution_directories(tmp_path / 'run')
    control = attempt / 'inherited-control'
    control.mkdir()
    program = '''
$ErrorActionPreference = 'Stop'
$paths = @($env:XIKARI_PROVIDER_PATH, $env:XIKARI_CAPTURE_PATH, $env:XIKARI_CONTROL_PATH)
$rows = foreach ($path in $paths) {
    $acl = Get-Acl -LiteralPath $path
    [pscustomobject]@{ protected = $acl.AreAccessRulesProtected; inherited = @($acl.Access | Where-Object IsInherited).Count }
}
$rows | ConvertTo-Json -Compress
'''
    environment = dict(os.environ, XIKARI_PROVIDER_PATH=str(workspace),
        XIKARI_CAPTURE_PATH=str(capture), XIKARI_CONTROL_PATH=str(control))
    environment.pop('PSModulePath', None)
    environment.pop('PSMODULEPATH', None)
    completed = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', program],
        env=environment, capture_output=True, timeout=15,
        creationflags=subprocess.CREATE_NO_WINDOW)
    assert completed.returncode == 0, completed.stderr.decode(errors='replace')
    provider_acl, capture_acl, control_acl = json.loads(completed.stdout)
    assert control_acl['protected'] is False
    assert provider_acl == control_acl
    assert capture_acl['protected'] is True


@pytest.mark.skipif(os.name != 'posix', reason='POSIX private directory modes')
def test_semantic_provider_and_capture_directories_remain_private_on_posix(tmp_path):
    _, capture, workspace = _execution_directories(tmp_path / 'run')
    assert stat.S_IMODE(workspace.stat().st_mode) == 0o700
    assert stat.S_IMODE(capture.stat().st_mode) == 0o700
