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
    if kind=='sensitivity':
        response['changes_considered']=r['task']['sensitivity_changes']
        response['change_assessments']=[{'path':row['path'],'affected_claim_ids':[claims[0]['claim_id']],'evidence_refs':claims[0]['evidence_refs'],'impact':'unchanged','explanation':'The hypothetical rule variation does not identify a new real observation or grant permission.','limits':['Further discriminating observations remain necessary.']} for row in r['task']['sensitivity_changes']]
    if behavior=='affirm':
        for row in response['claim_assessments']:row['position']='affirm'
else:
    atoms=r['reader_requirements']['atoms']
    sections=[{'section_id':'reader-'+str(i),'heading':'依据与边界','local_judgment':a['public_text'],'paragraphs':['这项材料限定了本题可以成立的判断范围，追加资料时仍需重新检查。'],'source_bindings':[{'source_path':a['canonical_path'],'paragraph_index':0,'excerpt':a['public_text']}]} for i,a in enumerate(atoms) if a['projection_status']!='withheld_for_protection']
    visibility=[{'canonical_path':a['canonical_path'],'classification':'public','disclosure':'include','purpose':r['reader_requirements']['purpose'],'authority_refs':[],'protection_reason':None} for a in atoms]
    response={'reader_sections':sections,'visibility_ledger':{'entries':visibility}}
if behavior=='passed': response={'passed':True}
if behavior=='mismatch': response={'possible_choice_ids':['CURRENT'],'choice_basis':'A different frozen continuation'}
if behavior=='incomplete_reader' and kind=='final_reader': response['reader_sections']=response['reader_sections'][:1]
if behavior=='protected_leak' and kind=='final_reader': response['reader_sections'][0]['paragraphs'].append('PRIVATE-EXECUTION-V4-SECRET-8122')
if behavior=='bad_pid': pass
output={'semantic_response':response,'source_bindings':bindings}
if behavior!='missing': pathlib.Path('semantic-output.json').write_text(json.dumps(output),encoding='utf-8')
pathlib.Path('completion-notice.txt').write_bytes(b'SEMANTIC_OUTPUT_READY')
events=[{'type':'thread.started','thread_id':'fixture-'+str(os.getpid()),'pid':os.getpid()+1 if behavior=='bad_pid' else os.getpid()},{'type':'turn.started'},{'type':'item.completed','item':{'type':'agent_message','text':'SEMANTIC_OUTPUT_READY'}},{'type':'turn.completed','usage':{'input_tokens':11,'cached_input_tokens':0,'output_tokens':17}}]
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


def pending_reader_inputs():
    from xi_kari_runtime.packet_v4 import prepare_analysis_packet_v4
    packet,contract=static_inputs()
    pending=prepare_analysis_packet_v4(packet,run_contract=contract,repository_root=ROOT)
    return pending,contract,validate_stage_chain_v4(pending,run_contract=contract,repository_root=ROOT)


def test_final_reader_actual_process_authors_only_two_fields_and_full_body(tmp_path):
    from xi_kari_runtime.semantic_projection import validate_reader_sections,validate_visibility_ledger
    packet,contract,controls=pending_reader_inputs()
    before=deepcopy(packet)
    result=execute_final_reader_v4(packet,controls,run_contract=contract,binding=fixture_binding(tmp_path),run_directory=tmp_path/'run',repository_root=ROOT)
    assert result['status']=='executed'
    assert set(result['reader_finalization'])=={'reader_sections','visibility_ledger'}
    after={**packet,**result['reader_finalization']}
    assert {key:value for key,value in after.items() if key not in {'reader_sections','visibility_ledger'}}=={key:value for key,value in before.items() if key not in {'reader_sections','visibility_ledger'}}
    validate_visibility_ledger(after)
    assert validate_reader_sections(after)==[]
    assert packet==before and result['actual_model_execution'] is False


def test_final_reader_missing_analysis_is_not_autofilled(tmp_path):
    packet,contract,controls=pending_reader_inputs()
    result=execute_final_reader_v4(packet,controls,run_contract=contract,binding=fixture_binding(tmp_path,behavior='incomplete_reader'),run_directory=tmp_path/'run',repository_root=ROOT)
    assert result['status']=='failed'
    assert result['reader_finalization'] is None


def test_protected_output_error_does_not_echo_raw_value(tmp_path):
    from xi_kari_runtime.semantic_projection import semantic_atom_paths
    packet,contract,controls=pending_reader_inputs()
    path='claim_mechanism_graph.claims[0].statement'
    packet['claim_mechanism_graph']['claims'][0]['statement']='PRIVATE-EXECUTION-V4-SECRET-8122'
    packet['visibility_ledger']={'entries':[{'canonical_path':p,'classification':'sensitive' if p==path else 'public','disclosure':'withhold' if p==path else 'include','purpose':'bounded source-scope analysis','authority_refs':['privacy-contract'] if p==path else [],'protection_reason':'当事人未同意公开该材料。' if p==path else None} for p in semantic_atom_paths(packet)]}
    controls=validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)
    result=execute_final_reader_v4(packet,controls,run_contract=contract,binding=fixture_binding(tmp_path,behavior='protected_leak'),run_directory=tmp_path/'run',repository_root=ROOT)
    assert result['status']=='failed'
    assert 'PRIVATE-EXECUTION-V4-SECRET-8122' not in json.dumps(result['errors'])


def test_missing_process_is_not_run_and_bad_declared_pid_is_failed(dynamic,tmp_path):
    packet,contract,controls,author_request=dynamic
    request=build_semantic_execution_request_v4(packet,controls,run_contract=contract,kind='next_author',author_request=author_request,repository_root=ROOT)
    missing=execute_semantic_request_v4(request,binding=None,run_directory=tmp_path/'no-process',repository_root=ROOT)
    assert missing['status']=='not_run'
    assert missing['receipt']['signed_payload']['child_pid'] is None
    bad=execute_semantic_request_v4(request,binding=fixture_binding(tmp_path,behavior='bad_pid'),run_directory=tmp_path/'bad-pid',repository_root=ROOT)
    assert bad['status']=='failed'
    assert bad['actual_model_execution'] is False


def test_probe_actual_registry_preserves_qualified_G_root_and_hard_premise(tmp_path):
    from tests.test_v4_stage_chain_integration import empirical_scale_inputs
    from tests.temporal_materials import record_temporal_inputs
    from xi_kari_runtime.formal_results import bind_formal_claim_results
    packet,contract=empirical_scale_inputs()
    original=packet['empirical_instances'][0]
    preregistration,evaluation,audit=record_temporal_inputs(tmp_path,original['preregistration'],original['evaluation'])
    packet['empirical_instances']=[{'preregistration':preregistration,'evaluation':evaluation}]
    claim=next(row for row in packet['claim_mechanism_graph']['claims'] if row['claim_id']=='CLAIM-OBJECT')
    prereg=packet['empirical_instances'][0]['preregistration']
    claim['claim_basis']['scope']['population']=prereg['generalization_unit']
    claim['formal_qualification'].update(requested=True,family='G',concept_ref='V90-CANON-G4',instance_refs=['ROOT-CHAIN'],status='not_evaluated',result_status='not_evaluated')
    packet['claim_mechanism_graph']['dependency_edges'].append({'edge_id':'EDGE-ACTUAL-PROBE-ROOT','from_id':'CLAIM-VALUE','to_ref':{'kind':'instance','id':'ROOT-CHAIN'},'role':'inferential_requires','source_refs':['V90-P00158'],'condition':'Actual G4 comparison required','scope':'Conditional ordinary recommendation'})
    packet['claim_mechanism_graph']['dependency_targets']=[{'kind':'instance','id':'ROOT-CHAIN','status':'not_run','reason':'Only code registry can establish support'}]
    packet['claim_mechanism_graph']=bind_formal_claim_results(packet['claim_mechanism_graph'],empirical_instances=packet['empirical_instances'],repository_root=ROOT,temporal_audit=audit)['claim_mechanism_graph']
    controls=validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT,temporal_audit=audit)
    request=build_semantic_execution_request_v4(packet,controls,run_contract=contract,kind='red_team',repository_root=ROOT,temporal_audit=audit)
    assert next(row for row in request['material_context']['claim_mechanism_graph']['claims'] if row['claim_id']=='CLAIM-OBJECT')['formal_qualification']['status']=='qualified'
    result=execute_semantic_request_v4(request,binding=fixture_binding(tmp_path,behavior='affirm'),run_directory=tmp_path/'run',repository_root=ROOT,temporal_audit=audit)
    assert result['status']=='executed'
    assert result['qualification_effect']=='none'
    assert result['actual_model_execution'] is False
