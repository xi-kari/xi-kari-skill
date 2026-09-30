from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from tests.test_v4_stage_chain_integration import dynamic_inputs,static_inputs
from xi_kari_runtime.stage_consumers_v4 import validate_stage_chain_v4
from xi_kari_runtime.semantic_executions_v4 import (
    bind_semantic_execution_fixture_v4,build_semantic_execution_request_v4,
    execute_semantic_request_v4,execute_next_author_v4,execute_semantic_probes_v4,
    execute_final_reader_v4,validate_semantic_execution_v4,
)


@pytest.fixture(scope='module')
def dynamic():
    packet,contract=dynamic_inputs()
    controls=validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)
    request=controls['stage_results']['recursion']['result']['paths'][0]['nodes'][1]['author_request']
    return packet,contract,controls,request


def fixture_binding(tmp_path,*,behavior='valid',timeout=5):
    script=tmp_path/'controlled_provider.py'
    script.write_text('''import json,os,pathlib,sys,time
r=json.loads(sys.stdin.read().split("REQUEST_JSON\\n",1)[1])
behavior=sys.argv[1]
if behavior=='timeout': time.sleep(20)
kind=r['kind']
refs=[row['evidence_id'] for row in r['material_context']['evidence']['evidence']]
claims=r['material_context']['claim_mechanism_graph']['claims']
bindings=[{'claim_id':row['claim_id'],'material_refs':row['claim_basis']['material_refs']} for row in claims]
if kind=='next_author':
    response={'possible_choice_ids':['WAIT'],'choice_basis':'Conditional baseline'}
elif kind in {'red_team','stance_stability','sensitivity'}:
    assessments=[{'claim_id':row['claim_id'],'position':'withhold','classification':row['claim_basis']['kind'],'judgment':'The frozen materials retain a bounded claim; further observation can change it.','evidence_refs':row['evidence_refs'],'limits':['No new permission or qualification follows.'],'withdrawal_conditions':row['withdrawal_conditions']} for row in claims]
    response={'claim_assessments':assessments,'counterarguments':[{'claim_id':claims[0]['claim_id'],'evidence_refs':claims[0]['evidence_refs'],'argument':'The registered observation does not identify every competing mechanism.','defeat_condition':'An independent discriminating measurement rejects the assumed channel.','scope':claims[0]['claim_basis']['scope'],'costs':['Additional measurement has a real resource cost.']}],'source_undefined_refs':r['source_undefined_refs']}
    if kind=='sensitivity': response['changes_considered']=r['task']['sensitivity_changes']
else:
    atoms=r['reader_requirements']['atoms']
    sections=[{'section_id':'reader-'+str(i),'heading':'依据与边界','local_judgment':a['projected_text'],'paragraphs':['这项材料限定了本题可以成立的判断范围，追加资料时仍需重新检查。'],'source_bindings':[{'source_path':a['canonical_path'],'paragraph_index':0,'excerpt':a['projected_text']}]} for i,a in enumerate(atoms) if a['projection_status']!='withheld_for_protection']
    visibility=[{'canonical_path':a['canonical_path'],'classification':'public','disclosure':'include','purpose':r['reader_requirements']['purpose'],'authority_refs':[],'protection_reason':None} for a in atoms]
    response={'reader_sections':sections,'visibility_ledger':{'entries':visibility}}
if behavior=='passed': response={'passed':True}
if behavior=='mismatch': response={'possible_choice_ids':['CURRENT'],'choice_basis':'A different frozen continuation'}
output={'semantic_response':response,'source_bindings':bindings}
if behavior!='missing': pathlib.Path('semantic-output.json').write_text(json.dumps(output),encoding='utf-8')
pathlib.Path('completion-notice.txt').write_bytes(b'SEMANTIC_OUTPUT_READY')
events=[{'type':'thread.started','thread_id':'fixture-'+str(os.getpid()),'pid':os.getpid()},{'type':'turn.started'},{'type':'item.completed','item':{'type':'agent_message','text':'SEMANTIC_OUTPUT_READY'}},{'type':'turn.completed','usage':{'input_tokens':11,'cached_input_tokens':0,'output_tokens':17}}]
for event in events: print(json.dumps(event),flush=True)
print('controlled fixture diagnostic',file=sys.stderr)
''',encoding='utf-8')
    return bind_semantic_execution_fixture_v4([sys.executable,'-B',str(script),behavior],repository_root=ROOT,timeout_seconds=timeout)


def test_actual_fixture_process_records_exact_request_bytes_pid_usage_and_output(dynamic,tmp_path):
    packet,contract,controls,author_request=dynamic
    binding=fixture_binding(tmp_path)
    result=execute_next_author_v4(packet,controls,author_request=author_request,run_contract=contract,binding=binding,run_directory=tmp_path/'run',repository_root=ROOT)
    assert result['status']=='executed'
    assert result['actual_model_execution'] is False
    assert result['matches_frozen_response'] is True
    receipt=result['receipt']['signed_payload']
    assert receipt['child_pid']>0 and receipt['child_pid']!=os.getpid()
    assert receipt['usage']['input_tokens']==11
    assert receipt['model']=='gpt-6.1-sol' and receipt['reasoning_effort']=='max'
    root=Path(result['attempt_directory'])
    assert (root/'capture/stdout.jsonl').read_bytes()
    assert (root/'capture/stderr.bin').read_bytes()
    request=build_semantic_execution_request_v4(packet,controls,run_contract=contract,kind='next_author',author_request=author_request,repository_root=ROOT)
    verified=validate_semantic_execution_v4(result,expected_request=request,binding=binding,repository_root=ROOT)
    assert verified['semantic_response']==result['semantic_response']


@pytest.mark.parametrize('behavior',['missing','passed','mismatch','timeout'])
def test_no_fake_process_success_or_semantic_boolean_can_close_next_author(dynamic,tmp_path,behavior):
    packet,contract,controls,author_request=dynamic
    binding=fixture_binding(tmp_path,behavior=behavior,timeout=1 if behavior=='timeout' else 5)
    result=execute_next_author_v4(packet,controls,author_request=author_request,run_contract=contract,binding=binding,run_directory=tmp_path/'run',repository_root=ROOT)
    assert result['actual_model_execution'] is False
    assert result['status']=='failed' or result['semantic_gate']=='failed' or result.get('continuation_gate')=='needs_restaging'
    assert result['errors']


def test_receipt_pid_and_output_disk_mutation_fail_fresh_validation(dynamic,tmp_path):
    packet,contract,controls,author_request=dynamic
    binding=fixture_binding(tmp_path)
    request=build_semantic_execution_request_v4(packet,controls,run_contract=contract,kind='next_author',author_request=author_request,repository_root=ROOT)
    result=execute_semantic_request_v4(request,binding=binding,run_directory=tmp_path/'run',repository_root=ROOT)
    root=Path(result['attempt_directory'])
    receipt=json.loads((root/'capture/receipt.json').read_text(encoding='utf-8'))
    receipt['signed_payload']['child_pid']=0
    (root/'capture/receipt.json').write_text(json.dumps(receipt),encoding='utf-8')
    with pytest.raises(ValueError,match='signature|receipt|PID'):
        validate_semantic_execution_v4(result,expected_request=request,binding=binding,repository_root=ROOT)
    (root/'capture/receipt.json').write_text(json.dumps(result['receipt']),encoding='utf-8')
    (root/'provider/semantic-output.json').write_text('{"semantic_response":{"passed":true}}',encoding='utf-8')
    with pytest.raises(ValueError,match='bytes|output|receipt'):
        validate_semantic_execution_v4(result,expected_request=request,binding=binding,repository_root=ROOT)


def test_stale_next_author_input_is_rejected_before_launch(dynamic,tmp_path):
    packet,contract,controls,author_request=dynamic
    stale=deepcopy(author_request)
    stale['input_state']['objects'][0]['variables'][0]['value']='stale state'
    with pytest.raises(ValueError,match='replayed|author request'):
        build_semantic_execution_request_v4(packet,controls,run_contract=contract,kind='next_author',author_request=stale,repository_root=ROOT)


def test_independent_probe_calls_keep_equal_stance_information_and_no_reality_gate(dynamic,tmp_path):
    packet,contract,controls,_=dynamic
    binding=fixture_binding(tmp_path)
    changes=[{'path':'local_world_model.registered_state.objects[0].variables[0].value','before':'old','after':'different hypothetical rule','reason':'Registered hypothetical boundary perturbation'}]
    result=execute_semantic_probes_v4(packet,controls,run_contract=contract,binding=binding,run_directory=tmp_path/'run',sensitivity_changes=changes,repository_root=ROOT)
    assert len(result['executions'])==5
    assert len({row['receipt']['signed_payload']['child_pid'] for row in result['executions']})==5
    assert result['actual_model_execution'] is False
    assert result['gates']['stance_stability']['equal_information'] is True
    assert result['gates']['sensitivity']['status'] in {'stable','changed'}
    assert result['gates']['red_team']['counterarguments']
