"""Deterministic consumers of source-bound version-four semantic stage inputs."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import math
from pathlib import Path
from typing import Any

from .canonical_json import sha256_json
from .claims import claim_constraints, validate_claim_graph
from .formal_results import rebuild_instance_registry
from .v4_contracts import claim_graph_input, formal_claim_outcome, validate_applicability, validate_versioned_schema, v4_authority
from .world_volume import _native_snapshot, bind_registered_event_evidence, validate_registered_world_bundle


STAGE_FIELDS = {
    'world_state': 'local_world_model', 'transformation': 'transformation_ledger',
    'recursion': 'recursive_lineage', 'forecast': 'forecast', 'action_choice': 'action_ranking',
}


def _unique(rows: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    result = {}
    for row in rows:
        identifier = row.get(key)
        if not isinstance(identifier, str) or not identifier.strip() or identifier in result:
            raise ValueError(f'{label} requires distinct nonempty identities')
        result[identifier] = row
    return result


def _native(value: object, label: str) -> Any:
    return _native_snapshot(value, label=label, error_type=ValueError)


def _supported(refs: list[str], constraints: Mapping[str, Any]) -> bool:
    from .causality import claim_support
    return claim_support(refs, constraints) == 'supported'


def _artifact(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, 'artifact_sha256': sha256_json(payload)}


def _material_bindings(packet: Mapping[str, Any], graph: Mapping[str, Any]) -> None:
    from .evidence import validate_evidence_ledger
    errors = validate_evidence_ledger(dict(packet['evidence']), dict(packet['retrieval']))
    if errors:
        raise ValueError('stage material ledger failed its frozen P04 bindings')
    evidence = {row['evidence_id']: row for row in packet['evidence']['evidence']}
    for row in graph['evidence']:
        for ref in row['xk3_evidence_refs']:
            actual = evidence.get(ref)
            if actual is None or actual['source_id'] not in row['source_refs']:
                raise ValueError('stage graph material does not resolve its actual P04 ledger')
            for field in ('evidence_identity', 'support_checks', 'availability_status', 'visibility', 'protected_review'):
                if row[field] != actual[field]:
                    raise ValueError('stage graph material differs from its actual P04 ledger')


def _world_result(checked: Mapping[str, Any]) -> dict[str, Any]:
    fields = ('state_diff_id','source_state_sha256','result_state_sha256','event_id','event_role','evidence_identity','authorization_status','external_action_authorized','reported_content_status')
    return {
        'final_state': deepcopy(checked['final_state']), 'identity_bindings': deepcopy(checked['identity_bindings']),
        'transitions': [{field:getattr(row,field) for field in fields} for row in checked['transitions']],
        'source_revision': checked['source_revision'],
    }


def stage_input_target_hashes_v4(packet: Mapping[str, Any]) -> dict[str, str]:
    """Expose actual semantic targets for the P04 material ledger builder."""
    from .world_volume import registered_event_target_hashes
    snapshot=_native(packet,'stage target inputs')
    events=list((snapshot.get('local_world_model') or {}).get('event_records',[]))
    for path in (snapshot.get('recursive_lineage') or {}).get('paths',[]):
        events.extend(step['event'] for step in path['steps'])
    targets=registered_event_target_hashes(events) if events else {}
    transformation=snapshot.get('transformation_ledger') or {}
    for record in transformation.get('contracts',[]):
        identifier=record['identity']['contract_id']
        for key in ('source_object','target_object'):
            targets[f'transformations.{identifier}.{key}']=sha256_json(record['objects'][key])
        for key in ('SP0','SP1'):
            targets[f'transformations.{identifier}.{key}']=sha256_json(record['scale'][key])
    for kind,key in (('evaluations','evaluation_id'),('task_checks','check_id'),('representations','representation_id')):
        for row in transformation.get(kind,[]):
            targets[f'transformations.{row["contract_id"]}.{kind}.{row[key]}']=sha256_json({key:value for key,value in row.items() if key!='evidence_refs'})
    forecast=snapshot.get('forecast') or {}
    for index,row in enumerate(forecast.get('result_observations',[])):
        targets[f'forecasts.{forecast["contract"]["forecast_id"]}.observations[{index}]']=sha256_json(row)
    action=snapshot.get('action_ranking') or {}
    for row in action.get('governance_records',[]):
        targets[f'governance.{row["governance_id"]}']=sha256_json(row)
    return targets


def _normalize_inputs(packet: dict[str, Any], run_contract: Mapping[str, Any]) -> None:
    world=packet.get('local_world_model')
    if isinstance(world,dict) and isinstance(world.get('registered_state'),dict):
        state=world['registered_state']
        if state.get('run_id',run_contract['run_id'])!=run_contract['run_id']:
            raise ValueError('world state run identity differs from its runtime contract')
        state['run_id']=run_contract['run_id']
        if state.get('evidence_cutoff')!=run_contract['evidence_cutoff']:
            raise ValueError('world state cutoff differs from its frozen runtime contract')
    events=list(world.get('event_records',[])) if isinstance(world,dict) else []
    lineage=packet.get('recursive_lineage')
    if isinstance(lineage,dict):
        for path in lineage.get('paths',[]):
            events.extend(step['event'] for step in path.get('steps',[]) if isinstance(step,dict) and isinstance(step.get('event'),dict))
    for event in events:
        if not isinstance(event,dict):
            raise ValueError('stage events require actual semantic records')
        if event.get('authorization_status','unknown') not in {'unknown','unauthorized'} or event.get('authorization_ref') is not None:
            raise ValueError('authorized event requires an independent runtime permission registry')
        event.setdefault('authorization_status','unknown')


def _path_value(value: object, path: list[str | int]) -> Any:
    current = value
    for part in path:
        if isinstance(current, dict) and isinstance(part,str) and part in current:
            current = current[part]
        elif isinstance(current,list) and type(part) is int and 0 <= part < len(current):
            current = current[part]
        else:
            raise ValueError('registered predicate path does not resolve actual object content')
    return current


def _predicate(obj: Mapping[str, Any], criterion: Mapping[str, Any]) -> bool:
    definition = criterion.get('definition')
    if not isinstance(definition,dict) or set(definition) != {'path','operator','operand'} or not isinstance(definition['path'],list):
        raise ValueError('nontrivial K mapping requires a frozen typed predicate; natural-language K needs an independent evaluator')
    value,operand,operator = _path_value(obj,definition['path']),definition['operand'],definition['operator']
    if operator=='eq':
        return sha256_json(value)==sha256_json(operand)
    if operator in {'ge','le'} and type(value) in {int,float} and type(operand) in {int,float}:
        return value >= operand if operator=='ge' else value <= operand
    raise ValueError('K mapping predicate has no supported deterministic comparator')


def _scale_inputs(envelope: Mapping[str, Any], *, packet: Mapping[str, Any], graph: Mapping[str, Any],
                  world: Mapping[str, Any], constraints: Mapping[str, Any], repository_root: Path | None,
                  temporal_audit: object = None) -> dict[str, Any]:
    from .empirical_instances import freeze_empirical_instance
    from .transformations import bind_scale_root_instances, classify_scale_relations, evaluate_task_partition, validate_scale_chain
    contracts = deepcopy(envelope['contracts'])
    by_id = _unique([{'contract_id':row['identity']['contract_id'],'content':row} for row in contracts],'contract_id','scale contracts')
    frozen_identities={row['object_id']:row for row in world['identity_bindings']}
    for record in contracts:
        identity=frozen_identities.get(record['objects']['source_object']['object_id'])
        if identity is None or sha256_json(identity['K'])!=sha256_json(record['objects']['source_K']) or sha256_json(identity['SP'])!=sha256_json(record['scale']['SP0']):
            raise ValueError('scale source object/K/profile differs from its actual frozen P07 identity scope')
    for name,key in (('comparators','result_id'),('identity_mappings','mapping_id'),('evaluations','evaluation_id'),('task_checks','check_id'),('representations','representation_id'),('object_contract_bindings','object_contract_id')):
        _unique(envelope[name],key,'scale registry inputs')
    catalogs: dict[str, Any] = {}
    for identifier, row in by_id.items():
        record = row['content']
        for key in ('source_object','target_object'):
            catalogs[f'transformations.{identifier}.{key}'] = record['objects'][key]
        catalogs[f'transformations.{identifier}.SP0'] = record['scale']['SP0']
        catalogs[f'transformations.{identifier}.SP1'] = record['scale']['SP1']
    for kind,key in (('evaluations','evaluation_id'),('task_checks','check_id'),('representations','representation_id')):
        for row in envelope[kind]:
            catalogs[f'transformations.{row["contract_id"]}.{kind}.{row[key]}'] = {k:v for k,v in row.items() if k!='evidence_refs'}
    ledger = packet['evidence']
    materials = {row['evidence_id']:row for row in ledger['evidence']}
    claims = {row['claim_id']:row for row in ledger['claims']}
    evidence_registry: dict[str, Any] = {}
    for binding in envelope['material_bindings']:
        actual = materials.get(binding['xk3_evidence_id'])
        identifier,target = binding['evidence_id'],binding['target_path']
        if actual is None or identifier in evidence_registry or target not in catalogs:
            raise ValueError('scale material binding is duplicate or does not resolve actual stage inputs')
        claim = claims[actual['claim_id']]
        from .v4_contracts import evidence_supports_claim
        expected = {'target_path':target,'target_sha256':sha256_json(catalogs[target]),'relation':'descriptive'}
        if expected not in claim['world_targets'] or claim['claim_basis']['kind']!='domain_empirical' or not evidence_supports_claim(actual,claim):
            raise ValueError('scale material does not bind the actual frozen object/comparison/evaluation')
        evidence_registry[identifier] = {'evidence_id':identifier,'identity':'observed','source_refs':[actual['source_id']], 'object_sha256':sha256_json(catalogs[target]),'target_path':target,'material_identity':deepcopy(actual['evidence_identity'])}

    def refs(ids: list[str], *, target: str | None = None) -> None:
        if not ids or any(ref not in evidence_registry for ref in ids):
            raise ValueError('scale registry input requires actual material bindings')
        if target is not None and not any(evidence_registry[ref]['target_path']==target for ref in ids):
            raise ValueError('scale registry evidence is not bound to its actual input content')

    comparators, mappings, evaluations, checks, representations, verification = ({},{},{},{},{},{})
    for row in envelope['comparators']:
        record = by_id[row['contract_id']]['content']
        profile0,profile1 = record['scale']['SP0'],record['scale']['SP1']
        axis,method = row['axis_id'],row['method']
        source,target = profile0[axis],profile1[axis]
        refs(row['evidence_refs'])
        if sha256_json(profile0)!=sha256_json(profile1):
            refs(row['evidence_refs'],target=f'transformations.{row["contract_id"]}.SP1')
        if method=='equality':
            if sha256_json(source)!=sha256_json(target):
                raise ValueError('axis equality comparator differs from actual values')
            relation='equal'
        elif method=='numeric_order':
            if not isinstance(source,dict) or not isinstance(target,dict) or set(source)!= {'value','unit'} or set(target)!= {'value','unit'} or source['unit']!=target['unit'] or type(source['value']) not in {int,float} or type(target['value']) not in {int,float}:
                raise ValueError('numeric axis comparison requires matching registered units and finite quantities')
            relation='equal' if source['value']==target['value'] else 'expands' if source['value']<target['value'] else 'contracts'
        elif method=='set_inclusion':
            if not isinstance(source,list) or not isinstance(target,list):
                raise ValueError('set axis comparison requires two registered finite sets')
            left,right={sha256_json(value) for value in source},{sha256_json(value) for value in target}
            if len(left)!=len(source) or len(right)!=len(target):
                raise ValueError('set axis comparison cannot collapse duplicate typed members')
            relation='equal' if left==right else 'expands' if left<right else 'contracts' if right<left else 'incomparable'
        elif method=='unknown':
            continue
        else:
            raise ValueError('axis comparator method is not registered')
        payload={'result_id':row['result_id'],'axis_id':axis,'relation':relation,'valid':True,'source_profile_sha256':sha256_json(profile0),'target_profile_sha256':sha256_json(profile1),'task_sha256':sha256_json(record['identity']['purpose']),'contract_version':record['identity']['version'],'comparison_payload':{'source':source,'target':target,'witness':{'relation':relation,'method':method}},'evidence_refs':row['evidence_refs']}
        if row['result_id'] in comparators:
            raise ValueError('scale comparator identities must remain unique')
        comparators[row['result_id']]=_artifact(payload)
    for record in contracts:
        identifier=record['identity']['contract_id']
        rows=[row for row in envelope['comparators'] if row['contract_id']==identifier]
        if len(rows)!=9 or {row['axis_id'] for row in rows}!=set('AXTOCRINJ'):
            raise ValueError('applicable scale contract requires all nine comparator inputs')
        axis_rows=[]
        for row in rows:
            artifact=comparators.get(row['result_id'])
            axis_rows.append({'axis_id':row['axis_id'],'relation':artifact['relation'] if artifact else 'unknown','comparator_result_id':row['result_id'] if artifact else None,'artifact_sha256':artifact['artifact_sha256'] if artifact else None})
        record['scale'].update(axis_differences=axis_rows,unchanged_axes=[row['axis_id'] for row in axis_rows if row['relation']=='equal'],transformation_class=classify_scale_relations({row['relation'] for row in axis_rows}))
        mapping=record['objects']['identity_mapping']
        if mapping['mapping_id']=='builtin:deep-identity':
            mapping['classification']='same_object'
    for row in envelope['identity_mappings']:
        record=by_id[row['contract_id']]['content']
        obj=record['objects']
        refs(row['evidence_refs'])
        criterion_results={key:'passed' if _predicate(obj[side+'_object'],obj[k_side+'_K']) else 'failed' for key,side,k_side in (('source_under_source_K','source','source'),('source_under_target_K','source','target'),('target_under_source_K','target','source'),('target_under_target_K','target','target'))}
        directions={}
        for direction,source_side,target_side in (('forward','source','target'),('reverse','target','source')):
            pairs=row['field_pairs'][direction]
            if not pairs:
                raise ValueError('K mapping requires both substantive direction attempts')
            valid=all(sha256_json(_path_value(obj[source_side+'_object'],pair['source_path']))==sha256_json(_path_value(obj[target_side+'_object'],pair['target_path'])) for pair in pairs)
            directions[direction+'_mapping']={'status':'valid' if valid else 'invalid','evidence_refs':row['evidence_refs']}
        own=criterion_results['source_under_source_K']==criterion_results['target_under_target_K']=='passed'
        same=own and set(criterion_results.values())=={'passed'} and all(value['status']=='valid' for value in directions.values())
        classification='same_object' if same else 'converted_object' if own and criterion_results['target_under_source_K']=='failed' else 'incomparable' if own and 'invalid' in {value['status'] for value in directions.values()} else 'undetermined'
        if classification=='undetermined':
            criterion_results=dict.fromkeys(criterion_results,'undetermined')
        digests={key+'_sha256':sha256_json(obj[key]) for key in ('source_object','target_object','source_K','target_K')}
        proof_id=row['mapping_id']+':criteria'
        proof={'artifact_id':proof_id,'content':{'mapping_id':row['mapping_id'],'criterion_results':criterion_results,**digests}}
        verification[proof_id]=_artifact(proof)
        payload={'mapping_id':row['mapping_id'],'classification':classification,**digests,'criterion_results':criterion_results,**directions,'preserved_criteria':[key for key,value in criterion_results.items() if value=='passed'],'violated_criteria':[key for key,value in criterion_results.items() if value=='failed'],'preregistration':row['preregistration'],'verification_artifact_refs':[proof_id],'evidence_refs':row['evidence_refs']}
        if row['mapping_id'] in mappings:
            raise ValueError('scale K mapping identities must remain unique')
        mappings[row['mapping_id']]=_artifact(payload)
        obj['identity_mapping'].update(classification=classification,artifact_sha256=mappings[row['mapping_id']]['artifact_sha256'])
    for row in envelope['evaluations']:
        record=by_id[row['contract_id']]['content']
        refs(row['evidence_refs'],target=f'transformations.{row["contract_id"]}.evaluations.{row["evaluation_id"]}')
        value,threshold=row['observed_value'],row['threshold']
        if type(value) not in {int,float} or type(threshold) not in {int,float} or not all(math.isfinite(number) for number in (value,threshold)):
            raise ValueError('scale evaluation requires finite measured quantities')
        from .problem_contract import parse_instant
        if parse_instant(row['preregistered_at'],field='scale evaluation preregistration')>=parse_instant(row['result_accessed_at'],field='scale evaluation access'):
            raise ValueError('scale evaluation rule must precede its actual result access')
        transform=record['transformation']
        rule=transform['decision_rule'] if row['gate'] is None else transform['null_decision_rule']
        if not isinstance(rule,dict) or rule.get('preregistered_at')!=row['preregistered_at'] or rule.get('result_accessed_at')!=row['result_accessed_at']:
            raise ValueError('scale evaluation temporal scope differs from its frozen decision rule')
        if row['gate'] is None and (rule.get('evaluation_id')!=row['evaluation_id'] or transform['positive_threshold']!=threshold):
            raise ValueError('scale positive evaluation differs from the registered threshold and identity')
        if row['gate'] is not None and rule.get('evaluation_ids',{}).get(row['gate'])!=row['evaluation_id']:
            raise ValueError('scale null evaluation differs from its three independent registered gates')
        passed=value>=threshold if row['relation']=='ge' else value<=threshold
        evaluations[row['evaluation_id']]={'evaluation_id':row['evaluation_id'],'contract_id':row['contract_id'],'task_sha256':sha256_json(record['identity']['purpose']),'observed_value':value,'operator':row['relation'],'gate':row['gate'],'result':'passed' if passed else 'failed','evidence_refs':row['evidence_refs']}
    for row in envelope['task_checks']:
        record=by_id[row['contract_id']]['content']
        refs(row['evidence_refs'],target=f'transformations.{row["contract_id"]}.task_checks.{row["check_id"]}')
        tested=evaluate_task_partition(row['representation_by_source'],row['answer_by_source'])
        success=tested['reconstructable'] if row['scope']=='reconstruction' else tested['task_sufficient']
        checks[row['check_id']]=_artifact({'check_id':row['check_id'],'task_sha256':sha256_json(record['identity']['purpose']),'scope':row['scope'],'result':'supported' if success else 'unsupported_or_undecided','evidence_refs':row['evidence_refs'],'finite_partition':tested})
    for row in envelope['representations']:
        record=by_id[row['contract_id']]['content']
        refs(row['evidence_refs'],target=f'transformations.{row["contract_id"]}.representations.{row["representation_id"]}')
        representations[row['representation_id']]=_artifact({key:row[key] for key in ('representation_id','version','mapping_ref','reconstruction_method_ref','content')} | {'source_object_sha256':sha256_json(record['objects']['source_object']),'task_sha256':sha256_json(record['identity']['purpose'])})
    identities={row['object_id']:row for row in packet['local_world_model']['identity_records']}
    object_contracts={}
    for row in envelope['object_contract_bindings']:
        if row['object_id'] not in identities or row['object_contract_id'] in object_contracts:
            raise ValueError('scale root object contract does not resolve actual P07 identities')
        object_contracts[row['object_contract_id']]=identities[row['object_id']]
    instance_inputs=[{'frozen':freeze_empirical_instance(row['preregistration']),'evaluation':row['evaluation']} for row in packet.get('empirical_instances',[])]
    root_bundles=[]
    for record in contracts:
        transform=record['transformation']
        roots={}
        if transform['claim_mode']!='descriptive_mapping':
            bundle=bind_scale_root_instances(record,instance_inputs=instance_inputs,claim_mechanism_graph=claim_graph_input(graph),object_contracts=object_contracts,temporal_audit=temporal_audit)
            roots=bundle['root_instances']
            root_bundles.append(bundle)
            verification.update(bundle['verification_artifacts'])
            evidence_registry.update(bundle['evidence_registry'])
            outcomes={row['result_state'] for row in roots.values()}
            transform['result_state']=next(iter(outcomes)) if len(outcomes)==1 else 'unsupported_or_undecided'
        else:
            rule=transform['decision_rule']
            positive=evaluations.get(rule.get('evaluation_id')) if isinstance(rule,dict) else None
            null=transform['null_decision_rule']
            null_rows=[evaluations.get(ref) for ref in null.get('evaluation_ids',{}).values()] if isinstance(null,dict) else []
            transform['result_state']='supported' if positive and positive['result']=='passed' else 'null_supported' if len(null_rows)==3 and all(row and row['result']=='passed' for row in null_rows) else 'unsupported_or_undecided' if positive or null_rows else 'not_evaluated'
        parent=transform['parent_representation']
        if isinstance(parent,dict) and 'representation_id' in parent:
            registered=representations.get(parent['representation_id'])
            if registered is None:
                raise ValueError('scale parent representation does not resolve its source inputs')
            parent['content_hash']=sha256_json(registered['content'])
        task_rows=record['evidence']['task_checks']
        if isinstance(task_rows,list):
            for row in task_rows:
                row['result']=checks[row['check_id']]['result']
        if transform['claim_mode']!='descriptive_mapping':
            from .transformations import validate_scale_instance
            result=validate_scale_instance(record,comparator_results=comparators,identity_mapping_results=mappings,root_instances=roots,evidence_registry=evidence_registry,evaluation_results=evaluations,verification_artifacts=verification,representation_registry=representations,task_check_results=checks,repository_root=repository_root)
            root_bundles[-1]['checked']=result
    registries={'comparator_results':comparators,'identity_mapping_results':mappings,'root_instances':{},'evidence_registry':evidence_registry,'evaluation_results':evaluations,'verification_artifacts':verification,'representation_registry':representations,'task_check_results':checks,'repository_root':repository_root}
    if root_bundles:
        steps=[]
        for record in contracts:
            bundle=next((item for item in root_bundles if item['checked']['contract_id']==record['identity']['contract_id']),None)
            if bundle:
                steps.append(bundle['checked'])
            else:
                steps.append(validate_scale_chain([record],**registries)['steps'][0])
        for previous,current in zip(contracts,contracts[1:]):
            if any(sha256_json(left)!=sha256_json(right) for left,right in ((previous['objects']['target_object'],current['objects']['source_object']),(previous['objects']['target_K'],current['objects']['source_K']),(previous['scale']['SP1'],current['scale']['SP0']))):
                raise ValueError('scale chain does not preserve actual object/K/SP continuity')
        result={'steps':steps,'chain_sha256':sha256_json(contracts),'unresolved_contract_ids':[row['contract_id'] for row in steps if row['result_state'] in {'unsupported_or_undecided','not_evaluated'}]}
    else:
        result=validate_scale_chain(contracts,**registries)
    return {**result,'contracts':contracts,'root_input_sha256':sha256_json(packet.get('empirical_instances',[])),'root_results':[dict(bundle['root_instances']) for bundle in root_bundles]}


def _recursive_inputs(envelope: Mapping[str, Any], *, packet: Mapping[str, Any], graph: Mapping[str, Any], world: Mapping[str, Any], constraints: Mapping[str, Any]) -> tuple[dict[str, Any],dict[str, Any]]:
    from .recursion import execute_recursive_step, validate_branch_dispositions, validate_registered_child
    evidence_registry={row['evidence_id']:{'evidence_id':row['evidence_id'],'source_refs':row['source_refs']} for row in graph['evidence']}
    applicable=validate_branch_dispositions(envelope['branch_dispositions'],evidence_registry=evidence_registry)
    paths=envelope['paths']
    _unique(paths,'path_id','recursive paths')
    if {row['branch_kind'] for row in paths}!=set(applicable) or len(paths)!=len(applicable):
        raise ValueError('every applicable branch requires exactly one substantive replay path')
    completed,contexts=[],{}
    for path in paths:
        seed={'path_id':path['path_id'],'run_id':packet['evidence']['run_id'],'order':1,'status':'active','output_state':deepcopy(world['final_state']),'evidence_identity':'simulated','declared_evidence_grade':'low','model_version':world['final_state']['model_version'],'conditions':envelope['conditions'],'history':[],'dimensions':envelope['dimensions']}
        seed['node_id']='NODE-'+sha256_json(seed)[:20].upper()
        branch_refs=set(envelope['branch_dispositions'][path['branch_kind']]['evidence_refs'])
        mechanisms={row['mechanism_id']:row for row in graph['mechanisms']}
        premises=[claim['claim_id'] for claim in graph['claims'] if branch_refs.intersection(claim['evidence_refs']) or any(branch_refs.intersection(mechanisms[ref]['evidence_refs']) for ref in claim['mechanism_ids'])]
        if not premises:
            raise ValueError('recursive branch evidence lacks an actual registered claim responsibility')
        if not _supported(premises,constraints):
            seed.update(status='stopped',stop_reason='registered_branch_premise_unsupported')
            terminal=execute_recursive_step(seed,{},action_catalog=envelope['action_catalog'],author=lambda request:None,evidence_registry={},independent_question=path['steps'][0]['independent_question'],incremental_gain=path['steps'][0]['incremental_gain'])
            completed.append({'path_id':path['path_id'],'branch_kind':path['branch_kind'],'nodes':[seed],'terminal':terminal,'stop_reason':'registered_branch_premise_unsupported','blocked_claim_ids':premises,'last_child_sha256':None})
            continue
        parent=seed
        nodes=[seed]
        last=None
        for step in path['steps']:
            event=step['event']
            registry=bind_registered_event_evidence(parent['output_state'],[event],evidence_ledger=packet['evidence'],retrieval_index=packet['retrieval'],bindings=step['event_evidence_bindings'])
            response=step['next_author_response']
            child=execute_recursive_step(parent,event,action_catalog=envelope['action_catalog'],author=lambda request:deepcopy(response),evidence_registry=registry,independent_question=step['independent_question'],incremental_gain=step['incremental_gain'])
            if child.get('status')!='active':
                raise ValueError('recursive step lacks an independently substantive child; stop belongs in its terminal record')
            validate_registered_child(child,parent=parent,event=event,action_catalog=envelope['action_catalog'],evidence_registry=registry)
            last={'child':child,'parent':parent,'event':event,'action_catalog':envelope['action_catalog'],'evidence_registry':registry}
            nodes.append(child)
            parent=child
        if last is None:
            raise ValueError('applicable recursion requires an actual replayed next-author child')
        terminal=execute_recursive_step(parent,{},action_catalog=envelope['action_catalog'],author=lambda request:None,evidence_registry={},independent_question=path['stop']['independent_question'],incremental_gain=path['stop']['incremental_gain'])
        if terminal.get('status')!='completed':
            raise ValueError('recursive termination did not establish its bounded stop responsibility')
        completed.append({'path_id':path['path_id'],'branch_kind':path['branch_kind'],'nodes':nodes,'terminal':terminal,'stop_reason':path['stop']['reason'],'last_child_sha256':sha256_json(last['child'])})
        contexts[path['path_id']]=last
    return {'paths':completed,'branch_dispositions':deepcopy(envelope['branch_dispositions']),'author_delivery':'deterministic_replay_of_frozen_semantic_responses','evidence_identity':'simulated'},contexts


def _forecast_inputs(envelope: Mapping[str, Any], *, packet: Mapping[str, Any], contexts: Mapping[str, Any], graph: Mapping[str, Any], constraints: Mapping[str, Any], registry: Any, repository_root: Path | None, evidence_mode: str) -> tuple[dict[str, Any],dict[str, Any]]:
    from .stability import freeze_forecast_from_recursive_child
    from .forecasting import append_forecast_result
    context=contexts.get(envelope['path_id'])
    if context is None:
        raise ValueError('forecast requires an actual replayed recursive path')
    record=deepcopy(envelope['contract'])
    child=context['child']
    if record['input_cutoff']!=child['output_state']['evidence_cutoff']:
        raise ValueError('forecast cutoff differs from its actual frozen recursive input')
    record.update(order=child['order'],model_version=child['model_version'],parent_state_diff_id=child['state_diff_id'])
    kwargs={**context,'claim_mechanism_graph':graph,'repository_root':repository_root,'verified_instance_results':registry,'evidence_mode':evidence_mode}
    frozen=freeze_forecast_from_recursive_child(record,**kwargs)
    from .world_volume import apply_registered_event
    transition=apply_registered_event(context['parent']['output_state'],context['event'],evidence_registry=context['evidence_registry'])
    transition_record={'state_diff_id':transition.state_diff_id,'source_state_sha256':transition.source_state_sha256,'result_state_sha256':transition.result_state_sha256,'output_state':transition.output_state}
    graph_claims={row['claim_id']:row for row in graph['claims']}
    graph_evidence={row['evidence_id']:row for row in graph['evidence']}
    ledger_claims={row['claim_id']:row for row in packet['evidence']['claims']}
    ledger_evidence={row['evidence_id']:row for row in packet['evidence']['evidence']}
    for index,observation in enumerate(envelope['result_observations']):
        if any(key in observation for key in ('status','forecast_contract_sha256','result')):
            raise ValueError('forecast observations cannot supply runtime result controls')
        if observation['kind']=='observed':
            target={'target_path':f'forecasts.{record["forecast_id"]}.observations[{index}]','target_sha256':sha256_json(observation),'relation':'descriptive'}
            refs=observation['basis_claim_ids']
            if not refs or not all(graph_claims[ref]['claim_basis']['kind']=='domain_empirical' for ref in refs):
                raise ValueError('forecast result requires actual empirical observation claims')
            atoms={atom for ref in refs for evidence_ref in graph_claims[ref]['evidence_refs'] for atom in graph_evidence[evidence_ref]['xk3_evidence_refs']}
            if not any(target in ledger_claims[ledger_evidence[atom]['claim_id']]['world_targets'] for atom in atoms):
                raise ValueError('forecast result measurement does not bind its actual P04 material')
        frozen=append_forecast_result(frozen,observation,parent_state=child['output_state'],parent_transition=transition_record,claim_constraints=constraints)
    return frozen,kwargs


def _action_inputs(envelope: Mapping[str, Any], *, forecast: Mapping[str, Any], forecast_context: Mapping[str, Any], graph: Mapping[str, Any], constraints: Mapping[str, Any], registry: Any) -> dict[str, Any]:
    from .judgment import validate_decision_from_recursive_forecast
    from .governance import assess_governance_change
    from .judgment_boundaries import assess_hv_route, assess_correction_endpoints, assess_protected_opacity, assess_oversight, assess_compliance_risk
    comparison=deepcopy(envelope['comparison'])
    comparison['execution_status']='analysis_only'
    checked=validate_decision_from_recursive_forecast(comparison,forecast=forecast,**forecast_context)
    governance=[]
    for row in envelope['governance_records']:
        if any(key in row for key in ('status','permission_effect','applied','executed','adopted_change_ids')):
            raise ValueError('governance semantic record cannot supply runtime decisions')
        try:
            result=assess_governance_change(row,registries={},claim_constraints=constraints)
        except ValueError as error:
            raise ValueError('strong governance requires independent runtime actor/interest/approval/version-writeback registries') from error
        if any(not _supported(objection['basis_claim_ids'],constraints) for objection in row['objections']):
            result['ordinary_procedure_value']='unsupported_or_undecided'
        result['capability_gap']='Independent canonical actor, interest, source-integrity, approval and version-writeback registries have not been supplied by a runtime verifier'
        governance.append({'governance_id':row['governance_id'],'result':result})
    handlers={'hv_route':lambda row:assess_hv_route(row,claim_constraints=constraints,formal_results=registry),'correction_endpoints':lambda row:assess_correction_endpoints(row,claim_constraints=constraints),'protected_opacity':lambda row:assess_protected_opacity(row,claim_constraints=constraints,evaluated_at=forecast['contract']['registered_at']),'oversight':lambda row:assess_oversight(row,claim_constraints=constraints),'compliance_risk':lambda row:assess_compliance_risk(row,claim_constraints=constraints)}
    boundaries=[]
    for row in envelope['boundary_records']:
        record=row['record']
        if any(key in record for key in ('status','permission_effect','framework_diagnosis','malicious_intent','authorized','executed')):
            raise ValueError('judgment boundary input cannot supply its own runtime conclusions')
        if row['kind']=='oversight' and record.get('executor_effect_receipt'):
            raise ValueError('effective oversight requires an actual runtime executor receipt registry')
        boundaries.append({'boundary_id':row['boundary_id'],'kind':row['kind'],'result':handlers[row['kind']](record)})
    return {'comparison':checked,'governance':governance,'boundaries':boundaries,'external_selection_status':'not_evaluated','external_action_executed':False,'permission_effect':'none','capability_gap':'No independently verified atomic permission registry or physical executor is attached to this stage replay'}


def validate_stage_chain_v4(packet: Mapping[str, Any], *, run_contract: Mapping[str, Any], repository_root: Path | None = None, temporal_audit: object = None) -> dict[str, Any]:
    """Recompute stage results without consuming authored authority or cached results."""
    snapshot=_native(packet,'v4 stage packet')
    if not isinstance(snapshot,dict) or run_contract.get('contract_profile')!='production-authoring-v4':
        raise ValueError('version-four stage chain requires its frozen production contract')
    mode=run_contract['mode']
    if snapshot['evidence'].get('run_id')!=run_contract['run_id'] or snapshot['retrieval'].get('run_id')!=run_contract['run_id']:
        raise ValueError('stage inputs differ from the frozen run identity')
    _normalize_inputs(snapshot,run_contract)
    semantic_graph=claim_graph_input(snapshot['claim_mechanism_graph'])
    registry=rebuild_instance_registry(snapshot.get('empirical_instances',[]),graph=semantic_graph,derived_instances=snapshot.get('derived_instances',[]),evidence_mode=mode,repository_root=repository_root,temporal_audit=temporal_audit)
    concepts,anchors,dependencies=v4_authority(repository_root)
    resolved_graph=deepcopy(semantic_graph)
    for claim in resolved_graph['claims']:
        if claim['formal_qualification']['requested']:
            qualification=claim['formal_qualification']
            qualification['status'],qualification['result_status']=formal_claim_outcome(claim,concepts=concepts,verified_instance_results=registry)
    graph=validate_claim_graph(resolved_graph,evidence_mode=mode,repository_root=repository_root,verified_instance_results=registry)
    applicability=validate_applicability(snapshot['applicability'],claims=graph['claims'],anchors=anchors,repository_root=repository_root)
    if applicability!=graph['applicability']:
        raise ValueError('stage and claim responsibility maps differ')
    _material_bindings(snapshot,graph)
    constraints=claim_constraints(graph,verified_instance_results=registry)
    inputs={field:snapshot[field] for field in STAGE_FIELDS.values() if field in snapshot}
    validate_versioned_schema('xk-v4-stage-inputs.schema.json',inputs,repository_root=repository_root)
    results={}
    def result(stage: str,value: dict[str, Any],stage_input: Any) -> None:
        results[stage]={'applicability_status':'applicable','validation_status':'validated','input_sha256':sha256_json(stage_input),'result_sha256':sha256_json(value),'result':value}
    for stage,row in applicability.items():
        if row['status']!='applicable':
            field=STAGE_FIELDS.get(stage)
            if field and snapshot.get(field) is not None:
                raise ValueError(f'{stage} nonapplicability cannot carry an executable stage envelope')
            if row['status']=='undetermined' and any(claim['kind']==('prediction' if stage=='forecast' else 'mechanism') for claim in graph['claims']) and stage in {'mechanism','forecast'}:
                raise ValueError('a mechanism or prediction claim requires a substantive applicable consumer')
            results[stage]={'applicability_status':row['status'],'validation_status':row['status'],'input_sha256':None,'result_sha256':None,'result':None}
        elif stage in STAGE_FIELDS and (not isinstance(snapshot.get(STAGE_FIELDS[stage]),dict) or not snapshot[STAGE_FIELDS[stage]]):
            raise ValueError(f'{stage} consumer requires substantive {STAGE_FIELDS[stage]} inputs')
    world=None
    if applicability['world_state']['status']=='applicable':
        envelope=snapshot['local_world_model']
        if envelope['applicability']!=applicability:
            raise ValueError('world bundle and stage responsibility maps differ')
        checked=validate_registered_world_bundle(envelope,repository_root=repository_root,evidence_ledger=snapshot['evidence'],retrieval_index=snapshot['retrieval'],expected_run_id=run_contract['run_id'])
        world=_world_result(checked)
        result('world_state',world,envelope)
    if applicability['mechanism']['status']=='applicable':
        mechanisms=graph['mechanisms']
        if not mechanisms or not any(claim['kind']=='mechanism' for claim in graph['claims']):
            raise ValueError('applicable mechanism requires substantive claim and channel records')
        mechanism_results=[{'mechanism_id':row['mechanism_id'],'dependent_claim_results':{claim['claim_id']:constraints[claim['claim_id']] for claim in graph['claims'] if row['mechanism_id'] in claim['mechanism_ids']}} for row in mechanisms]
        if any(not row['dependent_claim_results'] for row in mechanism_results):
            raise ValueError('mechanism record lacks an actual dependent claim responsibility')
        result('mechanism',{'mechanisms':mechanism_results,'instance_results':dict(registry)},graph)
    if applicability['transformation']['status']=='applicable':
        if world is None:
            raise ValueError('scale transformations require actual P07 frozen identities')
        envelope=snapshot['transformation_ledger']
        result('transformation',_scale_inputs(envelope,packet=snapshot,graph=graph,world=world,constraints=constraints,repository_root=repository_root,temporal_audit=temporal_audit),envelope)
    contexts={}
    if applicability['recursion']['status']=='applicable':
        if world is None:
            raise ValueError('recursion requires an actual world-state consumer')
        envelope=snapshot['recursive_lineage']
        recursive,contexts=_recursive_inputs(envelope,packet=snapshot,graph=graph,world=world,constraints=constraints)
        result('recursion',recursive,envelope)
    forecast,forecast_context=None,None
    if applicability['forecast']['status']=='applicable':
        envelope=snapshot['forecast']
        forecast,forecast_context=_forecast_inputs(envelope,packet=snapshot,contexts=contexts,graph=graph,constraints=constraints,registry=registry,repository_root=repository_root,evidence_mode=mode)
        result('forecast',forecast,envelope)
    if applicability['action_choice']['status']=='applicable':
        if forecast is None or forecast_context is None:
            raise ValueError('action comparison requires an actual recursive forecast')
        envelope=snapshot['action_ranking']
        result('action_choice',_action_inputs(envelope,forecast=forecast,forecast_context=forecast_context,graph=graph,constraints=constraints,registry=registry),envelope)
    from .temporal_audit import TemporalAudit
    temporal_binding = {'status':'supplied','audit_sha256':temporal_audit.expected_audit_sha256,'evidence_scope':'isolated_runtime_reads'} if type(temporal_audit) is TemporalAudit else {'status':'unavailable','audit_sha256':None,'evidence_scope':'isolated_runtime_reads'}
    return {'source_version':'v9.0','source_revision':dependencies['source_raw_sha256'],'run_id':run_contract['run_id'],'input_sha256':sha256_json({'inputs':inputs,'graph':semantic_graph,'evidence':snapshot['evidence'],'retrieval':snapshot['retrieval'],'empirical_instances':snapshot.get('empirical_instances',[]),'derived_instances':snapshot.get('derived_instances',[]),'temporal_audit_binding':temporal_binding}),'temporal_audit_binding':temporal_binding,'stage_results':results,'permission_effect':'none','external_action_executed':False,'probe_boundary':{'status':'not_evaluated','required_for_runtime_seal':['red_team','stance_stability','sensitivity'],'reason':'Stage replay does not execute fresh semantic probe authors or establish physical action capability'}}


__all__ = ('validate_stage_chain_v4','stage_input_target_hashes_v4')
