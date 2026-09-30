from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from xi_kari_runtime import authoring, execution
from xi_kari_runtime.concept_authority import load_concept_authority
from tests.test_p04_v4_authoring import _authoring_input

ROOT = Path(__file__).resolve().parents[1]


def test_public_v4_base_request_uses_actual_source_and_ontology_identity():
    _, problem, plan, lock, _ = _authoring_input()
    _, authority = load_concept_authority(ROOT, source_version='v9.0')
    request = execution.build_base_authoring_request(
        run_id=plan['run_id'], mode='open-world', problem_contract=problem,
        repository_root=ROOT, source_lock=lock, read_plan=execution._read_plan(lock, run_id=plan['run_id']),
        concept_authority=authority, privacy_contract=execution._privacy_contract(purpose='fixture', delivery_audience='requesting-user'),
        ontology_read_plan=plan,
    )
    assert request['schema_id'] == 'xi-kari.v4.base-authoring-request'
    assert request['source_inputs']['source_version'] == 'v9.0'
    assert request['source_inputs']['reader_root'] == str(ROOT / 'references/source/v9.0/reader')
    assert request['source_inputs']['ontology_root'] == str(ROOT / 'references/ontology/v9.0')
    prompt = execution.build_base_authoring_prompt(request).decode('utf-8')
    assert 'xk-v4-base-authoring-output.schema.json' in prompt
    assert 'claim_basis' in prompt and 'formal_qualification' in prompt
    assert 'empirical_instances' in prompt and 'applicability' in prompt


def test_provider_default_records_exact_authorized_model_and_effort():
    binding = authoring.bind_base_authoring_provider(Path(sys.executable), mode='closed-input', repository_root=ROOT, timeout_seconds=30)
    assert binding['model'] == 'gpt-6.1-sol'
    assert binding['reasoning_effort'] == 'max'
    assert binding['argv'][binding['argv'].index('--model') + 1] == 'gpt-6.1-sol'
    assert 'model_reasoning_effort="max"' in binding['argv']


def test_v4_execution_rejects_mixed_source_before_launch(tmp_path):
    with pytest.raises(ValueError, match='version-four.*v9.0'):
        execution.execute_authored_run(tmp_path, request_text='Explain a bounded passage.', repository_root=ROOT,
            codex_provider_executable=Path(sys.executable), contract_version=4, source_version='v8.3')
    assert not list(tmp_path.iterdir())


def test_v4_preflight_checks_actual_source_without_creating_a_run(tmp_path):
    from xi_kari_runtime.materialization import prepare_run
    _, problem, _, _, _ = _authoring_input()
    result = prepare_run(tmp_path, problem_contract=problem, mode='open-world', repository_root=ROOT,
        contract_profile='production-authoring-v4', semantic_authoring_profile='production-codex',
        codex_provider_executable=Path(sys.executable))
    assert result['source_version'] == 'v9.0'
    assert result['source_unit_count'] == 4418
    assert result['run_created'] is False and result['preflight_only'] is True
    assert not list(tmp_path.iterdir())
