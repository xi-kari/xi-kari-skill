from pathlib import Path
import hashlib
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from build_install_package import selected
from check_xi_kari_skill import check as check_skill
from check_xi_kari_runtime import check_repository
from xi_kari_runtime.validation_v4 import validator_set_sha256_v4


@pytest.fixture(scope='module')
def installation(tmp_path_factory):
    target = tmp_path_factory.mktemp('pure-v9-skill')
    for path in ROOT.rglob('*'):
        if not path.is_file() or '.git' in path.parts:
            continue
        relative = path.relative_to(ROOT).as_posix()
        if not selected(relative):
            continue
        if relative.startswith('references/source/') and not relative.startswith('references/source/v9.0/'):
            continue
        if relative.startswith('references/ontology/') and not relative.startswith('references/ontology/v9.0/'):
            continue
        if relative.startswith('references/learning-packs/') and relative.count('/') == 2:
            continue
        if relative.startswith('source/') and not relative.endswith('v9.0.docx'):
            continue
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    return target


def test_installation_selection_has_only_current_theory_and_runtime_resources():
    assert selected('source/跨尺度多圈层结构推演框架v9.0.docx')
    assert selected('references/source/v9.0/source-manifest.json')
    assert selected('references/ontology/v9.0/cards/c1.md')
    assert selected('references/learning-packs/domains/01.md')
    for name in ('source/跨尺度多圈层结构推演框架v8.3.docx',
                 'references/source/v8.3/source-manifest.json',
                 'references/ontology/concept-registry.json',
                 'references/ontology/cards/core/example.md',
                 'references/learning-packs/01-object-boundary.md',
                 'scripts/evaluate_xi_kari_v4.py',
                 'scripts/xi_kari_runtime/evaluation_v4.py',
                 'scripts/build_install_package.py',
                 'schemas/source-manifest.schema.json',
                 'schemas/concept-registry.schema.json',
                 'scripts/__pycache__/source.pyc'):
        assert not selected(name), name


def test_current_integrity_checks_work_without_legacy_theory(installation):
    assert check_skill(installation, all_checks=True) == []
    assert check_repository(installation, all_checks=True) == []


def test_current_runtime_authority_uses_current_theory_and_detects_tampering(installation):
    initial = validator_set_sha256_v4(installation)
    assert len(initial) == 64
    source = installation / 'source/跨尺度多圈层结构推演框架v9.0.docx'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == 'ffc45afdc288ecd268fd02e46d47318b7ddf17bf7b47605aa6c413c95398544b'
    card = installation / 'references/ontology/v9.0/cards/c1.md'
    original = card.read_bytes()
    try:
        card.write_bytes(original + b'\nchanged\n')
        assert validator_set_sha256_v4(installation) != initial
    finally:
        card.write_bytes(original)
    assert validator_set_sha256_v4(installation) == initial


def test_current_preflight_loads_the_full_source_from_the_installation(installation, tmp_path):
    from xi_kari_runtime.materialization import prepare_run
    from xi_kari_runtime.problem_contract import FROZEN_FIELDS

    problem = {field: 'bounded task' for field in FROZEN_FIELDS}
    problem.update(evidence_cutoff='2026-09-30T00:00:00Z', retrieval_profile='closed-input',
                   requested_stance='neutral', problem_action='explain', advice_requested=False,
                   deliverable_type='analysis')
    destination = tmp_path / 'run-not-created'
    result = prepare_run(destination, problem_contract=problem, mode='closed-input',
                         contract_profile='production-authoring-v4', semantic_authoring_profile='production-codex',
                         repository_root=installation, codex_provider_executable=Path(sys.executable).resolve())
    assert result['preflight_only'] is True
    assert result['run_created'] is result['analysis_complete'] is False
    assert result['source_version'] == 'v9.0'
    assert result['source_unit_count'] == 4418
    assert not destination.exists()


def test_installed_runtime_executes_and_freshly_validates_a_synthetic_run(installation, tmp_path):
    from tests.test_v4_pipeline_e2e_fixtures import CLOSED_MATERIALS, deterministic_provider, static_author_output
    from xi_kari_runtime.execution import execute_authored_run
    from xi_kari_runtime.canonical_json import read_json
    from xi_kari_runtime.validation_v4 import run_fresh_validator_v4

    _, problem, _, _, _ = static_author_output(mode='closed-input')
    problem['evidence_cutoff'] = '2030-01-01T00:00:00Z'
    provider, observation = deterministic_provider(tmp_path)
    result = execute_authored_run(tmp_path / 'runs', problem_contract=problem,
                                  run_id='pure-v9-synthetic', repository_root=installation,
                                  codex_provider_executable=provider, timeout_seconds=60,
                                  mode='closed-input', closed_input_materials=CLOSED_MATERIALS,
                                  contract_version=4, source_version='v9.0')
    run = Path(result['run_dir'])
    report = run_fresh_validator_v4(run, repository_root=installation)
    assert report['valid'] is report['complete'] is True
    assert report['phase_count'] == 13
    assert report['fresh_process'] is True
    assert read_json(observation)['actual_model_runs'] == 0
    assert (run / 'continuation/terminal-record.json').is_file()
