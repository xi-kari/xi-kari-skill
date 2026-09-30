import os
from pathlib import Path
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
