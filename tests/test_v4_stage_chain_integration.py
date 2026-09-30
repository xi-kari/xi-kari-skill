from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from tests.test_p04_v4_packet import _packet_inputs
from tests.test_p07_v4_world_bundle import bundle_fixture
from tests.test_causal_judgment_forecasts import forecast_inputs
from tests.test_causal_judgment_choice import comparison_inputs
from xi_kari_runtime import evidence, world_volume
from xi_kari_runtime.stage_consumers_v4 import stage_input_target_hashes_v4, validate_stage_chain_v4


def static_inputs():
    return _packet_inputs()


def dynamic_inputs(*, choice=False):
    packet, contract = static_inputs()
    world, ledger, retrieval = bundle_fixture()
    run_id = ledger['run_id']
    contract.update(run_id=run_id, evidence_cutoff=world['registered_state']['evidence_cutoff'])
    packet['evidence'], packet['retrieval'] = ledger, retrieval
    graph = packet['claim_mechanism_graph']
    template_claim, template_material = deepcopy(graph['claims'][0]), deepcopy(graph['evidence'][0])
    graph['claims'], graph['evidence'] = [], []
    next_event = deepcopy(world['event_records'][0])
    next_event.update(event_id='SIMULATED-NEXT', kind='simulated', update_path='scenario', occurrence_status='not_occurred', authorization_status='unknown', occurred_at='2026-10-01T00:00:00Z', evidence_refs=['EV-NEXT'])
    next_event['deltas'][0].update(before='new', after='conditional', evidence_refs=['EV-NEXT'])
    next_claim = deepcopy(ledger['claims'][0])
    next_claim.update(claim_id='CLAIM-NEXT', text='Synthetic conditional rule update', kind='interpretation')
    next_claim['claim_basis']['kind'] = 'text_interpretation'
    next_claim['world_targets'] = [{'target_path': 'events.SIMULATED-NEXT.deltas[0]', 'relation': 'descriptive'}]
    value_claim = deepcopy(next_claim)
    value_claim.update(claim_id='CLAIM-VALUE', kind='normative', text='Synthetic explicit N2 premise', world_targets=[])
    value_claim['claim_basis']['kind'] = 'normative_argument'
    value_claim['responsibility_refs'] = ['V90-CANON-N2']
    authored_claims = []
    for row in (ledger['claims'][0], next_claim, value_claim):
        row = deepcopy(row)
        row['support'] = [{'source_id': retrieval['sources'][0]['source_id'], 'summary': row['text'], 'support_checks': deepcopy(ledger['evidence'][0]['support_checks'])}]
        row.pop('evidence_refs', None)
        authored_claims.append(row)
    targets = world_volume.registered_event_target_hashes([*world['event_records'], next_event])
    ledger = evidence.build_evidence_ledger(run_id=run_id, claims=authored_claims, retrieval_index=retrieval, world_target_hashes=targets, contract_version=4)
    for row in ledger['claims']:
        claim = deepcopy(template_claim)
        claim.update(claim_id=row['claim_id'], statement=row['text'], kind='value' if row['claim_id']=='CLAIM-VALUE' else 'factual', evidence_refs=[row['claim_id']+'-M'], claim_basis=deepcopy(row['claim_basis']), responsibility_refs=deepcopy(row['responsibility_refs']))
        claim['claim_basis']['material_refs'] = claim['evidence_refs']
        graph['claims'].append(claim)
        item = next(item for item in ledger['evidence'] if item['claim_id']==row['claim_id'])
        material = deepcopy(template_material)
        material.update(evidence_id=row['claim_id']+'-M', source_refs=[item['source_id']], xk3_evidence_refs=[item['evidence_id']])
        for field in ('evidence_identity', 'support_checks', 'research_context', 'availability_status', 'visibility', 'protected_review'):
            material[field] = deepcopy(item[field])
        graph['evidence'].append(material)
    graph['central_claim_id'] = 'CLAIM-RULE'
    for row in graph['explanations']:
        row['claim_ids'] = ['CLAIM-RULE']
    for stage in graph['applicability']:
        graph['applicability'][stage]['status'] = 'applicable' if stage in {'world_state','recursion','forecast'} or choice and stage=='action_choice' else 'not_applicable'
    packet['applicability'] = deepcopy(graph['applicability'])
    world['applicability'] = deepcopy(packet['applicability'])
    packet['local_world_model'], packet['evidence'] = world, ledger
    object_id = world['registered_state']['objects'][0]['object_id']
    actions = [
        {'option_id':'WAIT','option_kind':'no_action','action_type':'no_new_action','target_object':object_id,'requirements':[]},
        {'option_id':'STALE','option_kind':'external_action','action_type':'old rule action','target_object':object_id,'requirements':[{'object_id':object_id,'variable_id':next_event['deltas'][0]['variable_id'],'operator':'eq','operand':'new','source_refs':['SYNTHETIC-SOURCE']}]},
        {'option_id':'CURRENT','option_kind':'external_action','action_type':'conditional rule action','target_object':object_id,'requirements':[]},
    ]
    dispositions = {kind:{'status':'applicable' if kind=='main' else 'not_applicable','reason':'Synthetic bounded branch comparison','evidence_refs':['CLAIM-NEXT-M'] if kind=='main' else []} for kind in ('main','strongest_rival','low_probability_high_consequence','residual')}
    packet['recursive_lineage'] = {'input_kind':'recursive_lineage','conditions':['Original conditional scope'], 'dimensions':{'time_rolling':True,'simulation_reentry':True,'anticipatory_reflexivity':False}, 'action_catalog':actions,'branch_dispositions':dispositions, 'paths':[{'path_id':'PATH-1','branch_kind':'main','steps':[{'event':next_event,'event_evidence_bindings':[{'event_id':next_event['event_id'],'delta_index':0,'evidence_ref':'EV-NEXT','xk3_evidence_id':'CLAIM-NEXT-e1'}],'independent_question':'Which choices remain after the conditional update?','incremental_gain':'Exclude old-rule action','next_author_response':{'possible_choice_ids':['WAIT'],'choice_basis':'Conditional baseline'}}], 'stop':{'reason':'No independent third-order question','independent_question':None,'incremental_gain':None}}]}
    forecast, _, _ = forecast_inputs()
    for key in ('model_version','order','parent_state_diff_id'):
        forecast.pop(key)
    forecast.update(object_id=object_id, identity_criterion=world['registered_state']['objects'][0]['K'], baseline_time='2026-09-30T12:00:00Z',input_cutoff='2026-09-30T12:00:00Z',registered_at='2026-09-30T12:01:00Z',deadline='2026-10-30T12:00:00Z')
    packet['forecast'] = {'input_kind':'forecast','path_id':'PATH-1','contract':forecast,'result_observations':[]}
    if choice:
        _, comparison = comparison_inputs()
        comparison.pop('execution_status')
        comparison.update(options=[deepcopy(actions[0]),deepcopy(actions[2])],existing_items=world['registered_state'].get('existing_obligations',[]),normative_basis_claim_ids=['CLAIM-VALUE'],scope={'object_id':object_id,'window':'October'})
        packet['action_ranking'] = {'input_kind':'action_ranking','comparison':comparison,'governance_records':[],'boundary_records':[]}
    return packet, contract


def test_source_only_case_preserves_all_six_nonapplicability_responsibilities():
    packet, contract = static_inputs()
    before = deepcopy(packet)
    result = validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)
    assert set(result['stage_results']) == set(packet['applicability'])
    assert all(row['validation_status']=='not_applicable' for row in result['stage_results'].values())
    assert result['external_action_executed'] is False
    assert result['probe_boundary']['status'] == 'not_evaluated'
    assert packet == before
    assert json.loads(json.dumps(result,allow_nan=False)) == result


@pytest.mark.parametrize('stage,field',[('world_state','local_world_model'),('transformation','transformation_ledger'),('recursion','recursive_lineage'),('forecast','forecast'),('action_choice','action_ranking')])
def test_applicable_stage_rejects_missing_or_self_declared_result(stage,field):
    packet, contract = static_inputs()
    packet['applicability'][stage]['status'] = 'applicable'
    packet['claim_mechanism_graph']['applicability'][stage]['status'] = 'applicable'
    for value in (None,{}, {'status':'supported','authority':'runtime','validated':True}):
        packet[field] = value
        with pytest.raises(ValueError):
            validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)


def test_runtime_replays_world_recursive_author_input_and_forecast_from_same_child():
    packet, contract = dynamic_inputs()
    result = validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)
    world = result['stage_results']['world_state']['result']
    recursive = result['stage_results']['recursion']['result']['paths'][0]
    child = recursive['nodes'][1]
    assert world['final_state']['objects'][0]['variables'][0]['value'] == 'new'
    assert child['author_request']['input_state']['objects'][0]['variables'][0]['value'] == 'conditional'
    assert {item['option_id'] for item in child['author_request']['available_actions']} == {'WAIT','CURRENT'}
    assert child['author_request']['excluded_actions'][0]['option_id'] == 'STALE'
    assert child['output_state']['unknowns'] == world['final_state']['unknowns']
    forecast = result['stage_results']['forecast']['result']
    assert forecast['recursive_child_sha256'] == recursive['last_child_sha256']
    assert forecast['contract']['order'] == child['order'] == 2
    assert result == validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)


@pytest.mark.parametrize('mutation',['stale_event','author_control','missing_stop','wrong_forecast_path','forged_forecast_hash','missing_branch'])
def test_substantive_chain_rejects_stale_or_authored_controls(mutation):
    packet, contract = dynamic_inputs()
    lineage = packet['recursive_lineage']
    if mutation=='stale_event': lineage['paths'][0]['steps'][0]['event']['deltas'][0]['after']='changed without material rebind'
    if mutation=='author_control': lineage['paths'][0]['steps'][0]['next_author_response']['status']='authorized'
    if mutation=='missing_stop': del lineage['paths'][0]['stop']
    if mutation=='wrong_forecast_path': packet['forecast']['path_id']='unknown-path'
    if mutation=='forged_forecast_hash': packet['forecast']['contract']['contract_sha256']='a'*64
    if mutation=='missing_branch': del lineage['branch_dispositions']['strongest_rival']
    with pytest.raises(ValueError):
        validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)


def test_normative_comparison_preserves_duties_and_grants_no_permission():
    packet, contract = dynamic_inputs(choice=True)
    result = validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)
    comparison = result['stage_results']['action_choice']['result']['comparison']
    assert comparison['recommended_option_id']=='WAIT'
    assert comparison['execution_status']=='analysis_only'
    assert comparison['permission_effect']=='none'
    assert result['external_action_executed'] is False
    packet['action_ranking']['comparison']['normative_basis_claim_ids']=['CLAIM-NEXT']
    with pytest.raises(ValueError):
        validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)


def test_not_applicable_cannot_hide_mechanism_or_prediction_claim():
    packet, contract = static_inputs()
    packet['claim_mechanism_graph']['claims'][0]['kind']='prediction'
    with pytest.raises(ValueError):
        validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)


def scale_inputs():
    from tests.test_p06_scale_instances import scale_fixture
    packet,contract=dynamic_inputs()
    record,registries=scale_fixture()
    record['scale'].pop('axis_differences')
    record['scale'].pop('unchanged_axes')
    record['scale'].pop('transformation_class')
    record['transformation'].pop('result_state')
    record['objects']['identity_mapping'].pop('classification')
    record['evidence']['task_checks']={'status':'not_applicable','reason':'No separate finite task check requested'}
    world=packet['local_world_model']
    state=world['registered_state']
    state['objects']=[{**record['objects']['source_object'],'K':record['objects']['source_K'],'variables':[{'variable_id':'XK-PROV-MEMBERS','category':'resources','value':2,'clock_id':'interaction'}]}]
    identity=world['identity_records'][0]
    identity.update(object_id=record['objects']['source_object']['object_id'],object_type='nonhuman',K=record['objects']['source_K'],SP=record['scale']['SP0'])
    world['event_records'],world['event_evidence_bindings']=[],[]
    for stage,row in packet['applicability'].items():
        row['status']='applicable' if stage in {'world_state','transformation'} else 'not_applicable'
    packet['claim_mechanism_graph']['applicability']=deepcopy(packet['applicability'])
    world['applicability']=deepcopy(packet['applicability'])
    packet.pop('recursive_lineage')
    packet.pop('forecast')
    evaluation={'evaluation_id':'EVAL-1','contract_id':'SCALE-1','metric':'membership','observed_value':1,'relation':'ge','threshold':1,'preregistered_at':'2026-09-29T00:00:00Z','result_accessed_at':'2026-09-30T00:00:00Z','gate':None,'evidence_refs':['E-EVAL']}
    envelope={'input_kind':'transformation','contracts':[record],'material_bindings':[{'evidence_id':'E-OBJECT','xk3_evidence_id':'CLAIM-OBJECT-e1','target_path':'transformations.SCALE-1.source_object'},{'evidence_id':'E-EVAL','xk3_evidence_id':'CLAIM-EVAL-e1','target_path':'transformations.SCALE-1.evaluations.EVAL-1'}],'comparators':[{'contract_id':'SCALE-1','result_id':'CMP-'+axis,'axis_id':axis,'method':'equality','evidence_refs':['E-OBJECT']} for axis in 'AXTOCRINJ'],'identity_mappings':[],'evaluations':[evaluation],'task_checks':[],'representations':[],'object_contract_bindings':[]}
    packet['transformation_ledger']=envelope
    targets=stage_input_target_hashes_v4(packet)
    targets['transformations.SCALE-1.target_object']=targets['transformations.SCALE-1.source_object']
    add_materials(packet,[(identifier,[path]) for identifier,path in [('CLAIM-OBJECT','transformations.SCALE-1.source_object'),('CLAIM-EVAL','transformations.SCALE-1.evaluations.EVAL-1')]],targets)
    return packet,contract


def add_materials(packet, declarations, targets):
    graph=packet['claim_mechanism_graph']
    ledger=packet['evidence']
    claims=[]
    template=deepcopy(ledger['claims'][0])
    source_id=packet['retrieval']['sources'][0]['source_id']
    checks=deepcopy(ledger['evidence'][0]['support_checks'])
    for row in ledger['claims']:
        row=deepcopy(row)
        row.pop('evidence_refs',None)
        row['world_targets']=[target for target in row['world_targets'] if target['target_path'] in targets]
        row['support']=[{'source_id':source_id,'summary':row['text'],'support_checks':checks}]
        claims.append(row)
    for identifier,paths in declarations:
        claim=deepcopy(template)
        claim.update(claim_id=identifier,text='Synthetic source-bound stage observation',kind='external_fact',world_targets=[{'target_path':path,'relation':'descriptive'} for path in paths],support=[{'source_id':source_id,'summary':'Synthetic observed stage input','support_checks':checks}])
        claim.pop('evidence_refs',None)
        claim['claim_basis']['kind']='domain_empirical'
        claims.append(claim)
        graph_claim=deepcopy(graph['claims'][0])
        graph_claim.update(claim_id=identifier,kind='factual',statement=claim['text'],evidence_refs=[identifier+'-M'],claim_basis=deepcopy(claim['claim_basis']))
        graph_claim['claim_basis']['material_refs']=[identifier+'-M']
        graph['claims'].append(graph_claim)
        graph_material=deepcopy(graph['evidence'][0])
        graph_material.update(evidence_id=identifier+'-M',xk3_evidence_refs=[identifier+'-e1'])
        graph['evidence'].append(graph_material)
    packet['evidence']=evidence.build_evidence_ledger(run_id=ledger['run_id'],claims=claims,retrieval_index=packet['retrieval'],world_target_hashes=targets,contract_version=4)
    by_id={row['evidence_id']:row for row in packet['evidence']['evidence']}
    for material in graph['evidence']:
        item=by_id[material['xk3_evidence_refs'][0]]
        for field in ('evidence_identity','support_checks','research_context','availability_status','visibility','protected_review'):
            material[field]=deepcopy(item[field])


def test_public_transformation_consumer_recomputes_comparators_and_fourteen_sections():
    packet,contract=scale_inputs()
    result=validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)
    stage=result['stage_results']['transformation']['result']
    assert stage['steps'][0]['result_state']=='supported'
    assert stage['steps'][0]['transformation_class']=='all_equal'
    assert set(stage['steps'][0]['consumed_comparator_ids'])=={'CMP-'+axis for axis in 'AXTOCRINJ'}
    assert len(stage['contracts'][0])==14
    assert 'result_state' not in packet['transformation_ledger']['contracts'][0]['transformation']


@pytest.mark.parametrize('mutation',['forged_result','forged_comparator','changed_object','fifteenth_section','changed_evaluation','missing_axis'])
def test_scale_public_consumer_rejects_unsupported_registry_or_stale_material(mutation):
    packet,contract=scale_inputs()
    envelope=packet['transformation_ledger']
    if mutation=='forged_result':envelope['contracts'][0]['transformation']['result_state']='supported'
    if mutation=='forged_comparator':envelope['comparators'][0]['valid']=True
    if mutation=='changed_object':envelope['contracts'][0]['objects']['source_object']['boundary'].append('unbound-unit')
    if mutation=='fifteenth_section':envelope['contracts'][0]['new_registry']={'status':'passed'}
    if mutation=='changed_evaluation':envelope['evaluations'][0]['observed_value']=999
    if mutation=='missing_axis':envelope['comparators'].pop()
    with pytest.raises(ValueError):
        validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)


def test_descriptive_scale_cannot_replace_both_profiles_without_P07_or_material_binding():
    packet,contract=scale_inputs()
    scale=packet['transformation_ledger']['contracts'][0]['scale']
    scale['SP0']=dict.fromkeys('AXTOCRINJ','unbound invented scope')
    scale['SP1']=deepcopy(scale['SP0'])
    with pytest.raises(ValueError,match='profile|P07|scope'):
        validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)


def test_world_run_identity_is_code_stamped_and_supplied_mismatch_is_rejected():
    packet,contract=dynamic_inputs()
    packet['local_world_model']['registered_state'].pop('run_id')
    packet['local_world_model']['event_records'][0].pop('authorization_status')
    result=validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)
    assert result['stage_results']['world_state']['result']['final_state']['run_id']==contract['run_id']
    assert 'run_id' not in packet['local_world_model']['registered_state']
    packet['local_world_model']['registered_state']['run_id']='OTHER-RUN'
    with pytest.raises(ValueError,match='identity'):
        validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)


def test_stage_replay_rejects_user_granted_event_authority():
    packet,contract=dynamic_inputs()
    packet['local_world_model']['event_records'][0]['authorization_status']='authorized'
    with pytest.raises(ValueError,match='permission registry'):
        validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)


def empirical_scale_inputs():
    from tests.test_causal_judgment_instances import root_contract,root_result
    packet,contract=scale_inputs()
    record=packet['transformation_ledger']['contracts'][0]
    transform=record['transformation']
    criterion='conditional_information_gain'
    transform.update(selected_operator_branch='cross_layer_causal',claim_mode='causal',root_instance_ids=['ROOT-CHAIN'],selected_subtype='G4a',selected_success_criterion=criterion,causal_bridge=['Synthetic frozen mapping and retained-variable comparison'])
    record['variables']['states']=['membership']
    identity=packet['local_world_model']['identity_records'][0]
    preregistration=root_contract()
    preregistration.update(instance_id='ROOT-CHAIN',root_id='G4',contract_version=record['identity']['version'],preregistration_timestamp='2026-09-29T00:00:00Z',candidate_object_id=identity['object_id'],object_contract_id='OBJECT-CONTRACT-CHAIN',scale_profile=record['scale']['SP0'],time_window=identity['window'],identity_criterion=identity['K'],target_variables=['membership'],selected_subtype='G4a',selected_success_criterion=criterion,evaluation_metric=criterion,candidate_specification={'mapping_id':'builtin:deep-identity','source_scale':record['scale']['SP0'],'target_scale':record['scale']['SP1'],'source_K':record['objects']['source_K'],'target_K':record['objects']['target_K'],'retained_variables':['membership'],'target_task':record['identity']['purpose'],'operator_ids':transform['operator_ids'],'selected_operator_branch':transform['selected_operator_branch'],'claim_mode':transform['claim_mode']})
    evaluation=root_result()
    evaluation.update(contract_version=preregistration['contract_version'],first_result_access_timestamp='2026-09-30T11:00:00Z',result_timestamp='2026-09-30T12:00:00Z',evidence_claim_ids=['CLAIM-OBJECT'],analysis_artifact_claim_ids=['CLAIM-OBJECT'],prerequisite_claim_ids={key:['CLAIM-OBJECT'] for key in ('D3_E5_mapping','comparison_model','retained_variable_conditioning')},null_gate_claim_ids={key:['CLAIM-OBJECT'] for key in ('equivalence','sensitivity','tolerance')},dimension_claim_ids={})
    evaluation['metrics'][criterion]=1
    packet['empirical_instances']=[{'preregistration':preregistration,'evaluation':evaluation}]
    packet['transformation_ledger']['object_contract_bindings']=[{'object_contract_id':'OBJECT-CONTRACT-CHAIN','object_id':identity['object_id']}]
    claim=next(row for row in packet['claim_mechanism_graph']['claims'] if row['claim_id']=='CLAIM-OBJECT')
    claim['claim_basis']['scope'].update(object=identity['object_id'],window=identity['window'],target='membership')
    return packet,contract


def test_public_scale_root_uses_actual_preregistration_evaluation_and_P07_identity():
    packet,contract=empirical_scale_inputs()
    result=validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)
    scale=result['stage_results']['transformation']['result']
    assert scale['root_results'][0]['ROOT-CHAIN']['eligibility_status']=='eligible'
    assert scale['root_results'][0]['ROOT-CHAIN']['result_state']=='supported'
    assert scale['steps'][0]['result_state']=='supported'
    assert scale['root_results'][0]['ROOT-CHAIN']['object_contract_sha256']==result['stage_results']['world_state']['result']['identity_bindings'][0]['binding_sha256']


def test_root_result_markers_cannot_replace_missing_actual_root_input():
    packet,contract=empirical_scale_inputs()
    packet['empirical_instances']=[{'qualification':'qualified','formal_result':'supported'}]
    with pytest.raises(ValueError,match='preregistration'):
        validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)


def test_root_scope_change_and_missing_P07_object_binding_are_rejected():
    packet,contract=empirical_scale_inputs()
    packet['transformation_ledger']['object_contract_bindings']=[]
    with pytest.raises(ValueError,match='P07 identity'):
        validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)


def test_real_instance_registry_reaches_forecast_and_choice_without_clearing_hard_edges():
    from tests.test_causal_judgment_instances import root_contract,root_result
    packet,contract=dynamic_inputs(choice=True)
    preregistration,evaluation=root_contract(),root_result()
    evaluation.update(evidence_claim_ids=['CLAIM-RULE'],analysis_artifact_claim_ids=['CLAIM-RULE'],prerequisite_claim_ids={key:['CLAIM-RULE'] for key in evaluation['prerequisite_claim_ids']},null_gate_claim_ids={key:['CLAIM-RULE'] for key in evaluation['null_gate_claim_ids']},dimension_claim_ids={'delay':['CLAIM-RULE']})
    packet['empirical_instances']=[{'preregistration':preregistration,'evaluation':evaluation}]
    graph=packet['claim_mechanism_graph']
    factual=next(row for row in graph['claims'] if row['claim_id']=='CLAIM-RULE')
    factual['claim_basis']['scope'].update(object=preregistration['candidate_object_id'],population=preregistration['generalization_unit'],window=preregistration['time_window'],target=preregistration['target_variables'][0])
    edge={'edge_id':'EDGE-NORM-REGISTERED-ROOT','from_id':'CLAIM-VALUE','to_ref':{'kind':'instance','id':preregistration['instance_id']},'role':'inferential_requires','source_refs':['V90-P00158'],'condition':'Registered empirical condition for this recommendation','scope':'This conditional recommendation only'}
    graph['dependency_edges'].append(edge)
    graph['dependency_targets']=[{'kind':'instance','id':preregistration['instance_id'],'status':'passed','reason':'This marker cannot replace the actual root registry'}]
    before=deepcopy(graph['dependency_edges'])
    result=validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)
    assert result['stage_results']['action_choice']['result']['comparison']['permission_effect']=='none'
    assert graph['dependency_edges']==before
    packet['empirical_instances'][0]['evaluation']['prerequisite_claim_ids']={}
    with pytest.raises(ValueError):
        validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)


def test_failed_branch_premise_blocks_dependent_next_author_and_all_downstream_orders():
    packet,contract=dynamic_inputs()
    packet.pop('forecast')
    for applicability in (packet['applicability'],packet['claim_mechanism_graph']['applicability'],packet['local_world_model']['applicability']):
        applicability['forecast']['status']='not_applicable'
    next(row for row in packet['claim_mechanism_graph']['evidence'] if row['evidence_id']=='CLAIM-NEXT-M')['support_status']='invalidated'
    result=validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)
    path=result['stage_results']['recursion']['result']['paths'][0]
    assert len(path['nodes'])==1
    assert path['nodes'][0]['status']=='stopped'
    assert path['terminal']['status']=='not_run'
    assert [row['order'] for row in path['terminal']['not_run_orders']]==[2,3]
    assert path['last_child_sha256'] is None


def test_governance_and_boundary_helpers_preserve_unsupported_qualification_and_no_transfer():
    packet,contract=dynamic_inputs(choice=True)
    packet['action_ranking']['governance_records']=[{'governance_id':'GOV-1','proposer':'proposer','reviewer':'reviewer','decision_members':['member'],'objections':[{'objection_id':'OBJ-1','reason':'Synthetic minority objection','disposition':'rejected','basis_claim_ids':['CLAIM-RULE']}],'governance_gate_claim_ids':{},'verified_evidence_refs':[],'approval_ref':None,'minority_objection_ids':['OBJ-1']}]
    packet['action_ranking']['boundary_records']=[{'boundary_id':'CORRECTION-1','kind':'correction_endpoints','record':{'safe_hearing_claim_ids':['CLAIM-RULE'],'evidence_understood_claim_ids':['CLAIM-NEXT'],'authorized_decision_changed_claim_ids':[],'resources_restored_claim_ids':[]}}]
    result=validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)
    action=result['stage_results']['action_choice']['result']
    assert action['governance'][0]['result']['status']=='nominal_only'
    assert action['governance'][0]['result']['adopted_change_ids']==[]
    assert action['boundaries'][0]['result']['resources_restored']=='unsupported_or_undecided'
    assert action['permission_effect']=='none'
    packet['action_ranking']['governance_records'][0]['status']='applied'
    with pytest.raises(ValueError):
        validate_stage_chain_v4(packet,run_contract=contract,repository_root=ROOT)


def test_fresh_process_rereads_disk_and_rejects_changed_semantic_delta(tmp_path):
    import os
    import subprocess
    packet,contract=dynamic_inputs()
    input_path=tmp_path/'stage-input.json'
    contract_path=tmp_path/'contract.json'
    input_path.write_text(json.dumps(packet),encoding='utf-8')
    contract_path.write_text(json.dumps(contract),encoding='utf-8')
    program="import json,sys; from pathlib import Path; from scripts.xi_kari_runtime.stage_consumers_v4 import validate_stage_chain_v4; print(json.dumps(validate_stage_chain_v4(json.loads(Path(sys.argv[1]).read_text()),run_contract=json.loads(Path(sys.argv[2]).read_text()),repository_root=Path.cwd())))"
    def fresh():
        return subprocess.run([sys.executable,'-B','-c',program,str(input_path),str(contract_path)],cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},text=True,capture_output=True)
    original=fresh()
    assert original.returncode==0
    result=json.loads(original.stdout)
    assert result['stage_results']['forecast']['validation_status']=='validated'
    packet['recursive_lineage']['paths'][0]['steps'][0]['event']['deltas'][0]['after']='unbound changed post-state'
    input_path.write_text(json.dumps(packet),encoding='utf-8')
    changed=fresh()
    assert changed.returncode!=0
    assert 'exact event delta' in changed.stderr
