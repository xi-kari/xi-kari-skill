from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from xi_kari_runtime import execution
from xi_kari_runtime.authoring import bind_base_authoring_provider
from xi_kari_runtime.closed_input import freeze_closed_input_materials
from xi_kari_runtime.contract_authoring import contract_authoring_request, validate_contract_authoring_binding
from xi_kari_runtime.problem_contract import build_natural_request_envelope, contract_hash, draft_problem_contract_from_natural_request


def material_context():
    natural = build_natural_request_envelope('只用给定材料解释这个决定', mode='closed-input', evidence_cutoff='2026-09-20T00:00:00Z')
    draft = draft_problem_contract_from_natural_request(natural['text'], mode='closed-input', evidence_cutoff=natural['evidence_cutoff'])
    materials, manifest = freeze_closed_input_materials([
        {'source_id': 'SOURCE-1', 'title': '组内决定', 'content': '十二人小组尚未表决，只同意起草。'}
    ], evidence_cutoff=natural['evidence_cutoff'])
    return natural, draft, materials, manifest


def test_contract_author_receives_exact_frozen_materials():
    natural, draft, materials, manifest = material_context()
    request = contract_authoring_request(run_id='material-context', natural_request=natural,
        draft_problem_contract=draft, repository_root=ROOT, provider={},
        closed_input_materials=materials, frozen_material_manifest=manifest)
    assert request['source_inputs']['closed_input_materials'] == materials
    assert request['source_inputs']['frozen_material_manifest'] == manifest
    request['source_inputs']['closed_input_materials'][0]['content'] = 'changed'
    assert materials[0]['content'] == '十二人小组尚未表决，只同意起草。'


def test_execute_passes_frozen_materials_before_author_freezes_scope(tmp_path, monkeypatch):
    observed = {}
    class Captured(Exception):
        pass
    def author(**kwargs):
        observed.update(kwargs)
        raise Captured
    monkeypatch.setattr(execution, '_author_natural_contract', author)
    monkeypatch.setattr(execution, 'bind_semantic_authoring_adapter', lambda *a, **k: {'provider_binding': {}})
    monkeypatch.setattr(execution, 'bind_base_authoring_provider', lambda *a, **k: {})
    raw = [{'source_id': 'SOURCE-1', 'title': '组内决定', 'content': '十二人小组尚未表决，只同意起草。'}]
    with pytest.raises(Captured):
        execution.execute_authored_run(tmp_path, request_text='只用给定材料解释这个决定',
            mode='closed-input', repository_root=ROOT, codex_provider_executable=Path(sys.executable),
            closed_input_materials=raw)
    expected, manifest = freeze_closed_input_materials(raw)
    assert observed['closed_input_materials'] == expected
    assert observed['frozen_material_manifest'] == manifest
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('changed', ['content', 'manifest', 'missing_manifest', 'open_world'])
def test_contract_material_context_rejects_unbound_or_wrong_mode(changed):
    natural, draft, materials, manifest = material_context()
    if changed == 'content':
        materials[0]['content'] = '小组已经表决通过。'
    elif changed == 'manifest':
        manifest['manifest_sha256'] = '0' * 64
    elif changed == 'missing_manifest':
        manifest = None
    else:
        natural['mode'] = 'open-world'
    with pytest.raises(ValueError):
        contract_authoring_request(run_id='material-context', natural_request=natural,
            draft_problem_contract=draft, repository_root=ROOT, provider={},
            closed_input_materials=materials, frozen_material_manifest=manifest)


def test_real_contract_process_reads_materials_and_replay_binds_the_same_set(tmp_path):
    provider_path = tmp_path / 'material_provider.py'
    provider_path.write_text(f'#!{Path(sys.executable).resolve()}\n' + '''import json, pathlib, sys
request = json.loads(sys.stdin.read().rsplit("运行时请求（只读）：\\n", 1)[1])
result = dict(request["draft_problem_contract"])
result["boundary"] = request["source_inputs"]["closed_input_materials"][0]["content"]
pathlib.Path("semantic-output.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
pathlib.Path(sys.argv[sys.argv.index("--output-last-message") + 1]).write_text("SEMANTIC_OUTPUT_READY", encoding="utf-8")
for event in ({"type":"thread.started","thread_id":"material-test"}, {"type":"turn.started"}, {"type":"turn.completed"}):
    print(json.dumps(event), flush=True)
''', encoding='utf-8')
    provider_path.chmod(0o755)
    natural, draft, materials, manifest = material_context()
    provider = bind_base_authoring_provider(provider_path, mode='closed-input', repository_root=ROOT, timeout_seconds=30)
    final, evidence = execution._author_natural_contract(run_id='material-context', natural_request=natural,
        draft_problem_contract=draft, repository_root=ROOT, provider=provider, timeout_seconds=30,
        failure_diagnostics_root=tmp_path/'runs', closed_input_materials=materials,
        frozen_material_manifest=manifest)
    assert final['boundary'] == materials[0]['content']
    assert json.loads(evidence['request_text'])['source_inputs']['closed_input_materials'] == materials
    base = {'problem_contract': final, 'source_inputs': {'closed_input_materials':materials, 'frozen_material_manifest':manifest},
        'contract_authoring_binding': {'receipt_sha256':evidence['receipt']['receipt_sha256'], 'problem_contract_sha256':contract_hash(final)}}
    receipt = {'contract_authoring_evidence':evidence, 'started_at':evidence['receipt']['completed_at']}
    run = {'run_id':'material-context', 'problem_contract':final, 'natural_request':natural, 'continuation':{'kind':'original'}}
    validate_contract_authoring_binding(base_request=base, base_receipt=receipt, run_contract=run, repository_root=ROOT)
    altered = deepcopy(base)
    other, other_manifest = freeze_closed_input_materials([
        {'source_id':'SOURCE-1', 'title':'组内决定', 'content':'十二人小组已经通过章程。'}])
    altered['source_inputs'] = {'closed_input_materials':other, 'frozen_material_manifest':other_manifest}
    with pytest.raises(ValueError, match='original natural request'):
        validate_contract_authoring_binding(base_request=altered, base_receipt=receipt, run_contract=run, repository_root=ROOT)
    assert not list((tmp_path/'runs').glob('failed-*'))


def test_execute_replays_contract_with_materials_after_base_author(tmp_path, monkeypatch):
    provider_path = tmp_path / 'two_stage_material_provider.py'
    provider_path.write_text(f'#!{Path(sys.executable).resolve()}\n' + '''import json, pathlib, sys
prompt = sys.stdin.read()
if "运行时请求（只读绑定）：\\n" in prompt:
    result = {}
else:
    request = json.loads(prompt.rsplit("运行时请求（只读）：\\n", 1)[1])
    result = dict(request["draft_problem_contract"])
    result["boundary"] = request["source_inputs"]["closed_input_materials"][0]["content"]
pathlib.Path("semantic-output.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
pathlib.Path(sys.argv[sys.argv.index("--output-last-message") + 1]).write_text("SEMANTIC_OUTPUT_READY", encoding="utf-8")
for event in ({"type":"thread.started","thread_id":"two-stage-material"}, {"type":"turn.started"}, {"type":"turn.completed"}):
    print(json.dumps(event), flush=True)
''', encoding='utf-8')
    provider_path.chmod(0o755)
    raw = [{'source_id':'SOURCE-1', 'title':'组内决定', 'content':'十二人小组尚未表决，只同意起草。'}]
    materials, manifest = freeze_closed_input_materials(raw)
    observed = []
    original = execution.validate_contract_authoring_evidence
    class ReplayObserved(Exception):
        pass
    def validate(evidence, **kwargs):
        observed.append(kwargs)
        assert kwargs.get('closed_input_materials') == materials
        assert kwargs.get('frozen_material_manifest') == manifest
        original(evidence, **kwargs)
        if len(observed) == 2:
            raise ReplayObserved
    monkeypatch.setattr(execution, 'validate_contract_authoring_evidence', validate)
    monkeypatch.setattr(execution, '_parse_base_output', lambda *a, **k: ({}, {}, {}))
    monkeypatch.setattr(execution, 'validate_semantic_read_trace_input', lambda *a, **k: None)
    monkeypatch.setattr(execution, 'validate_visibility_ledger', lambda *a, **k: None)
    with pytest.raises(ReplayObserved):
        execution.execute_authored_run(tmp_path/'runs', request_text='只用给定材料解释这个决定',
            mode='closed-input', repository_root=ROOT, codex_provider_executable=provider_path,
            closed_input_materials=raw, timeout_seconds=30)
    assert len(observed) == 2
