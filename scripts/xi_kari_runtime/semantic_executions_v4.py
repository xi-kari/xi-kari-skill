"""Source-bound provider executions and independently verifiable semantic receipts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import secrets
import stat
import subprocess
import sys
import uuid
from typing import Any

from .canonical_json import canonical_bytes, read_bounded_regular_file, read_json, read_json_text, sha256_bytes, sha256_file, sha256_json
from .formal_results import bind_formal_claim_results
from .output_transport import COMPLETION_NOTICE, parse_provider_events, read_semantic_output
from .stage_consumers_v4 import validate_stage_chain_v4
from .v4_contracts import repository_path, validate_versioned_schema, v4_authority
from .world_volume import _native_snapshot


MODEL='gpt-6.1-sol'
EFFORT='max'
KINDS={'next_author','red_team','stance_stability','sensitivity','final_reader'}
DOMAIN=b'xi-kari.v4.semantic-execution-receipt/v1'
MAX_BYTES=16*1024*1024
MAX_CAPTURE_BYTES=128*1024*1024


def _native(value: object) -> Any:
    return _native_snapshot(value,label='semantic execution input',error_type=ValueError)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _raw_file(path: Path,*,limit: int=MAX_BYTES) -> bytes:
    for candidate in (path,*path.parents):
        metadata=candidate.lstat()
        if stat.S_ISLNK(metadata.st_mode) or getattr(metadata,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400):raise ValueError('semantic execution refuses indirect file paths')
    initial=path.stat(follow_symlinks=False)
    if not stat.S_ISREG(initial.st_mode) or initial.st_size>limit:raise ValueError('semantic execution file size or regularity is invalid')
    with path.open('rb') as handle:
        opened=os.fstat(handle.fileno())
        raw=handle.read(limit+1)
        final=os.fstat(handle.fileno())
    if len(raw)>limit or final.st_size!=opened.st_size or len(raw)!=final.st_size or (initial.st_dev,initial.st_ino)!=(opened.st_dev,opened.st_ino):raise ValueError('semantic execution file changed during bounded binary read')
    return raw


def _source(root: Path) -> dict[str, Any]:
    _concepts,_anchors,dependencies=v4_authority(root)
    files=('references/source/v9.0/source-manifest.json','references/ontology/v9.0/concept-registry.json','references/ontology/v9.0/dependency-graph.json')
    return {'source_version':'v9.0','source_revision':dependencies['source_raw_sha256'],'files':{name:sha256_file(root/name) for name in files},'reader_root':str(root/'references/source/v9.0/reader'),'ontology_root':str(root/'references/ontology/v9.0')}


def _source_undefined(packet: Mapping[str, Any]) -> list[str]:
    results=[]
    def visit(value: object,path: str) -> None:
        if isinstance(value,dict):
            for key,item in value.items():
                child=f'{path}.{key}' if path else key
                if key=='source_undefined' and item not in (False,None,[],{}):results.append(child)
                if isinstance(item,str) and item in {'source_undefined','source_not_defined'}:results.append(child)
                visit(item,child)
        elif isinstance(value,list):
            for index,item in enumerate(value):visit(item,f'{path}[{index}]')
    visit(packet,'')
    return sorted(set(results))


def _snapshot_without_reader(packet: Mapping[str, Any]) -> dict[str, Any]:
    return {key:deepcopy(value) for key,value in packet.items() if key not in {'reader_sections','visibility_ledger','answer_delivery'}}


def _path_value(root: Any,path: str) -> Any:
    from .semantic_projection import _resolve_path_parent
    resolved=_resolve_path_parent(root,path)
    if resolved is None:raise ValueError('sensitivity change has no actual frozen semantic path')
    parent,key=resolved
    return parent[key]


def _changes(packet: Mapping[str, Any],changes: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result=_native(list(changes))
    seen=set()
    for row in result:
        if not isinstance(row,dict) or set(row)!={'path','before','after','reason'} or not isinstance(row['path'],str) or row['path'] in seen or not isinstance(row['reason'],str) or not row['reason'].strip():
            raise ValueError('sensitivity requires explicit distinct hypothetical changes')
        if row['path'].startswith(('problem_contract','claim_mechanism_graph','evidence','retrieval','runtime_binding','concept_disposition','formal_results')):
            raise ValueError('sensitivity cannot rewrite frozen problem, material, source or qualifications')
        if sha256_json(_path_value(packet,row['path']))!=sha256_json(row['before']) or sha256_json(row['before'])==sha256_json(row['after']):
            raise ValueError('sensitivity change differs from its actual frozen baseline')
        seen.add(row['path'])
    return result


def _fresh_controls(packet: Mapping[str, Any],controls: Mapping[str, Any],contract: Mapping[str, Any],root: Path) -> dict[str, Any]:
    fresh=validate_stage_chain_v4(packet,run_contract=contract,repository_root=root)
    if _native(controls)!=fresh:raise ValueError('semantic execution requires actual fresh stage controls')
    return fresh


def build_semantic_execution_request_v4(packet: Mapping[str, Any],stage_controls: Mapping[str, Any],*,run_contract: Mapping[str, Any],kind: str,author_request: Mapping[str, Any] | None=None,variant: str | None=None,sensitivity_changes: Sequence[Mapping[str, Any]]=(),computed_outcomes: Mapping[str, Any] | None=None,repository_root: Path | None=None) -> dict[str, Any]:
    root=repository_path(repository_root)
    packet=_native(packet)
    if kind not in KINDS:raise ValueError('semantic execution kind is not registered')
    controls=_fresh_controls(packet,stage_controls,run_contract,root)
    formal=bind_formal_claim_results(packet['claim_mechanism_graph'],empirical_instances=packet.get('empirical_instances',[]),derived_instances=packet.get('derived_instances',[]),evidence_mode=run_contract['mode'],repository_root=root)
    task={}
    context={'problem_contract':deepcopy(run_contract['problem_contract']),'claim_mechanism_graph':deepcopy(formal['claim_mechanism_graph']),'evidence':deepcopy(packet['evidence']),'retrieval':deepcopy(packet['retrieval']),'empirical_instances':deepcopy(packet.get('empirical_instances',[])),'derived_instances':deepcopy(packet.get('derived_instances',[]))}
    if kind=='next_author':
        requests=[node['author_request'] for path in (controls['stage_results']['recursion']['result'] or {}).get('paths',[]) for node in path['nodes'] if 'author_request' in node]
        value=_native(author_request)
        if not isinstance(value,dict) or value not in requests:raise ValueError('next author request differs from the actual replayed child input')
        task={'author_request':value}
        context['state']=deepcopy(value['input_state'])
        state_hash=sha256_json(value['input_state'])
    else:
        context['computed_packet']=_snapshot_without_reader(packet)
        context['stage_controls']=deepcopy(controls)
        context['formal_outcomes']=deepcopy(formal)
        state_hash=sha256_json(controls['stage_results'])
        if kind=='stance_stability':
            if variant not in {'support','oppose'}:raise ValueError('stance execution requires one code-owned comparison direction')
            task={'requested_stance':variant}
        elif kind=='sensitivity':
            if variant not in {'baseline','changed'}:raise ValueError('sensitivity requires baseline and changed executions')
            changes=_changes(packet,sensitivity_changes)
            if not changes:raise ValueError('sensitivity execution requires an actual registered hypothetical perturbation')
            task={'variant':variant,'sensitivity_changes':changes if variant=='changed' else []}
        elif kind=='final_reader':
            from .semantic_projection import typed_semantic_atoms
            task={'readonly_packet':deepcopy(packet)}
            if computed_outcomes is not None:
                expected={'formal_results':formal,'stage_controls':controls}
                if _native(computed_outcomes)!=expected:raise ValueError('final reader outcomes differ from actual runtime recomputation')
    purpose=(run_contract.get('privacy_contract') or {}).get('purpose')
    if not isinstance(purpose,str) or not purpose.strip():
        purposes={row['purpose'] for row in packet.get('visibility_ledger',{}).get('entries',[])}
        if len(purposes)!=1:raise ValueError('final semantic author needs one frozen disclosure purpose')
        purpose=next(iter(purposes))
    source=_source(root)
    request={'schema_id':'xi-kari.v4.xk.semantic-execution-request','schema_version':4,'kind':kind,'run_id':run_contract['run_id'],'source_inputs':source,'model':MODEL,'reasoning_effort':EFFORT,'evidence_mode':run_contract['mode'],'material_context':context,'task':task,'source_undefined_refs':_source_undefined(packet),'bindings':{'problem_contract_sha256':sha256_json(run_contract['problem_contract']),'parent_graph_sha256':sha256_json(formal['claim_mechanism_graph']),'materials_sha256':sha256_json({'evidence':packet['evidence'],'retrieval':packet['retrieval']}),'state_sha256':state_hash,'source_inputs_sha256':sha256_json(source),'base_information_sha256':sha256_json(context)},'reader_requirements':{'purpose':purpose,'atoms':[],'protected_constraints':[]}}
    request['reader_requirements']['protected_constraints']=[deepcopy(row) for row in packet.get('visibility_ledger',{}).get('entries',[]) if row['disclosure']=='withhold']
    if kind=='final_reader':
        from .semantic_projection import typed_semantic_atoms
        request['reader_requirements']['atoms']=typed_semantic_atoms(packet)
        classified={row['canonical_path'] for row in packet.get('visibility_ledger',{}).get('entries',[])}
        for atom in request['reader_requirements']['atoms']:
            if atom['canonical_path'] not in classified:
                atom['visibility']='undecided'
                atom['projection_status']='requires_visibility_decision'
    validate_versioned_schema('xk-v4-semantic-execution-request.schema.json',request,repository_root=root)
    return request


def bind_semantic_execution_provider_v4(executable_path: str | Path,*,repository_root: Path,timeout_seconds: int=1200) -> dict[str, Any]:
    from .authoring import bind_base_authoring_provider
    provider=bind_base_authoring_provider(executable_path,mode='closed-input',repository_root=repository_path(repository_root),timeout_seconds=timeout_seconds)
    if provider['model']!=MODEL or provider['reasoning_effort']!=EFFORT:raise ValueError('semantic execution requires gpt-6.1-sol/max')
    return {'kind':'codex_provider','provider':dict(provider)}


def bind_semantic_execution_fixture_v4(argv: Sequence[str],*,repository_root: Path,timeout_seconds: int=10) -> dict[str, Any]:
    from .authoring import _ordinary_executable
    command=list(argv)
    if not command or any(not isinstance(value,str) or not value for value in command) or type(timeout_seconds) is not int or not 1<=timeout_seconds<=120:
        raise ValueError('controlled fixture requires an exact bounded process command')
    selected=Path(command[0])
    if os.name=='nt' and selected.resolve()==Path(sys.executable).resolve():
        selected=Path(getattr(sys,'_base_executable',sys.executable))
    executable=_ordinary_executable(selected)
    command[0]=str(executable)
    files={str(Path(value).resolve()):sha256_file(Path(value)) for value in command[1:] if Path(value).is_file()}
    return {'kind':'controlled_process_fixture','repository_root':str(repository_path(repository_root)),'argv':command,'argv_sha256':sha256_json(command),'executable_path':str(executable),'executable_sha256':sha256_file(executable),'bound_files':files,'model':MODEL,'reasoning_effort':EFFORT,'timeout_seconds':timeout_seconds}


def _binding(binding: Mapping[str, Any] | None,root: Path) -> tuple[list[str],int,str]:
    from .authoring import require_base_authoring_provider
    if binding is None:raise ValueError('no runtime provider process is attached')
    if binding.get('kind')=='codex_provider':
        if set(binding)!={'kind','provider'}:raise ValueError('provider binding has unknown control fields')
        provider=require_base_authoring_provider(binding['provider'],mode='closed-input')
        if provider['model']!=MODEL or provider['reasoning_effort']!=EFFORT or Path(provider['repository_root'])!=root:raise ValueError('provider model, effort or source root differs')
        return list(provider['argv']),int(provider['timeout_seconds']),provider['executable_sha256']
    fields={'kind','repository_root','argv','argv_sha256','executable_path','executable_sha256','bound_files','model','reasoning_effort','timeout_seconds'}
    if binding.get('kind')!='controlled_process_fixture' or set(binding)!=fields or binding['model']!=MODEL or binding['reasoning_effort']!=EFFORT or Path(binding['repository_root'])!=root:
        raise ValueError('controlled fixture binding is invalid')
    if binding['argv_sha256']!=sha256_json(binding['argv']) or binding['argv'][0]!=binding['executable_path'] or sha256_file(Path(binding['executable_path']))!=binding['executable_sha256'] or any(sha256_file(Path(path))!=value for path,value in binding['bound_files'].items()):
        raise ValueError('controlled process executable or command content drifted')
    return list(binding['argv']),int(binding['timeout_seconds']),binding['executable_sha256']


def _prompt(request: Mapping[str, Any]) -> bytes:
    instructions=('Use only the exact frozen source-v9.0 material and scope in this request. Preserve observations, source assertions, inference, normative arguments, formal qualification outcomes and source_undefined. Do not grant authorization, qualify instances, execute external actions, or write receipts. Read source_inputs as readonly. Write one strict JSON object to semantic-output.json in the current private workspace, with exactly semantic_response and source_bindings. source_bindings cites each claim_id and its actual material_refs. For next_author, semantic_response has only possible_choice_ids and optional choice_basis/rationale, using the actual feasible actions in task.author_request. For probes, supply complete claim_assessments, concrete scoped counterarguments, and unchanged source_undefined_refs; never output a passed boolean. Claim assessments contain claim_id, semantic position (affirm/withhold/reject/source_undefined), original classification, concrete judgment, evidence_refs, limits and withdrawal_conditions. Counterarguments contain claim_id, evidence_refs, argument, defeat_condition, actual scope and costs. Sensitivity also contains exact changes_considered. For final_reader, semantic_response contains ONLY complete reader_sections and an explicit visibility_ledger for every typed atom, including new runtime outcomes. Follow the frozen disclosure purpose and protected constraints. Write full developed paragraphs with exact source_bindings; do not substitute a summary or invent missing analysis. Put SEMANTIC_OUTPUT_READY in completion-notice.txt and in the final message.\nREQUEST_JSON\n')
    exposed=deepcopy(request)
    for context in (exposed.get('material_context',{}).get('computed_packet'),exposed.get('task',{}).get('readonly_packet')):
        if isinstance(context,dict):
            for key in ('runtime_binding','concept_disposition'):context.pop(key,None)
    raw=instructions.encode('utf-8')+canonical_bytes(exposed)
    if request['kind']=='sensitivity':
        raw=b'For every changed path, also provide change_assessments with path, affected_claim_ids, actual evidence_refs, semantic impact (strengthens/weakens/changes_scope/unchanged/undetermined), a concrete explanation and limits. Preserve undetermined effects.\n'+raw
    if request['kind']=='final_reader':
        raw=b'Write the complete reader body in the language requested by the frozen question, using Chinese when no other language is requested. Every atom marked undecided requires your explicit disclosure decision; there are no default-public approvals.\n'+raw
    if len(raw)>MAX_BYTES:raise ValueError('semantic request exceeds bounded transport capacity')
    return raw


def _authority() -> tuple[list[list[bytes]],list[list[str]],str]:
    private=[[secrets.token_bytes(32),secrets.token_bytes(32)] for _ in range(256)]
    public=[[sha256_bytes(value) for value in pair] for pair in private]
    return private,public,sha256_json({'domain':DOMAIN.decode(),'public_key':public})


def _bits(payload: Mapping[str, Any]) -> list[int]:
    digest=hashlib.sha256(DOMAIN+b'\0'+canonical_bytes(payload)).digest()
    return [(byte>>shift)&1 for byte in digest for shift in range(7,-1,-1)]


def _sign(payload: dict[str, Any],private: list[list[bytes]],public: list[list[str]]) -> dict[str, Any]:
    return {'schema_id':'xi-kari.v4.xk.semantic-execution-attestation','schema_version':4,'algorithm':'lamport-sha256-v1','domain':DOMAIN.decode(),'public_key':public,'signed_payload':payload,'signature':[private[index][bit].hex() for index,bit in enumerate(_bits(payload))]}


def _verify_signature(receipt: Mapping[str, Any],commitment: str) -> dict[str, Any]:
    try:
        if set(receipt)!={'schema_id','schema_version','algorithm','domain','public_key','signed_payload','signature'} or receipt['schema_id']!='xi-kari.v4.xk.semantic-execution-attestation' or receipt['schema_version']!=4 or receipt['algorithm']!='lamport-sha256-v1' or receipt['domain']!=DOMAIN.decode():raise ValueError()
        public,signature=receipt['public_key'],receipt['signature']
        if len(public)!=256 or len(signature)!=256 or sha256_json({'domain':DOMAIN.decode(),'public_key':public})!=commitment:raise ValueError()
        for index,bit in enumerate(_bits(receipt['signed_payload'])):
            if len(public[index])!=2 or sha256_bytes(bytes.fromhex(signature[index]))!=public[index][bit]:raise ValueError()
        return dict(receipt['signed_payload'])
    except (ValueError,TypeError,KeyError,IndexError) as error:
        raise ValueError('semantic execution receipt signature or authority commitment is invalid') from error


def _repo_state(root: Path) -> dict[str, Any]:
    result={}
    for name,args in (('head',['rev-parse','HEAD']),('tree',['rev-parse','HEAD^{tree}']),('porcelain',['status','--porcelain=v1','--untracked-files=all'])):
        process=subprocess.run(['git','--no-optional-locks',*args],cwd=root,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False)
        result[name]=process.stdout.decode('utf-8',errors='strict').strip() if process.returncode==0 else None
    result['source_files']=_source(root)['files']
    return result


def _validate_output(request: Mapping[str, Any],payload: Mapping[str, Any],root: Path) -> dict[str, Any]:
    validate_versioned_schema('xk-v4-semantic-execution-response.schema.json',payload,repository_root=root)
    graph=request['material_context']['claim_mechanism_graph']
    claims={row['claim_id']:row for row in graph['claims']}
    bindings={row['claim_id']:row for row in payload['source_bindings']}
    if len(bindings)!=len(payload['source_bindings']) or set(bindings)!=set(claims) or any(set(bindings[identifier]['material_refs'])!=set(claims[identifier]['claim_basis']['material_refs']) for identifier in claims):
        raise ValueError('semantic response source bindings differ from actual frozen claims/materials')
    response=payload['semantic_response']
    kind=request['kind']
    if kind=='next_author':
        if set(response)-{'possible_choice_ids','choice_basis','rationale'} or 'possible_choice_ids' not in response:raise ValueError('next author supplied runtime authority or missing semantic choices')
        available={row['option_id'] for row in request['task']['author_request']['available_actions']}
        choices=response['possible_choice_ids']
        if not isinstance(choices,list) or len(choices)!=len(set(choices)) or not set(choices).issubset(available):raise ValueError('next author choices exceed the actual replayed action set')
    elif kind=='final_reader':
        if set(response)!={'reader_sections','visibility_ledger'}:raise ValueError('final reader may only author complete sections and visibility decisions')
        from .semantic_projection import validate_visibility_ledger,validate_reader_sections,validate_reader_section_privacy
        from .prose import render_reader_outputs,reader_contract_gaps
        view=deepcopy(request['task']['readonly_packet'])
        view.update(deepcopy(response))
        entries={row['canonical_path']:row for row in response['visibility_ledger']['entries']}
        for prior in request['reader_requirements']['protected_constraints']:
            current=entries.get(prior['canonical_path'])
            if current is None or current['disclosure']!='withhold' or current['classification']=='public':raise ValueError('final reader downgraded a frozen protected source classification')
        validate_visibility_ledger(view,expected_purpose=request['reader_requirements']['purpose'])
        validate_reader_section_privacy(view)
        if validate_reader_sections(view):raise ValueError('final reader is missing complete source-bound analysis')
        outputs=render_reader_outputs(view)
        if reader_contract_gaps(view,outputs['answer']):raise ValueError('final reader body fails its actual complete prose contract')
    else:
        required={'claim_assessments','counterarguments','source_undefined_refs'} | ({'changes_considered','change_assessments'} if kind=='sensitivity' else set())
        if set(response)!=required or response['source_undefined_refs']!=request['source_undefined_refs']:raise ValueError('probe response changed classification/source_undefined or supplied authority flags')
        assessments={row['claim_id']:row for row in response['claim_assessments']}
        if len(assessments)!=len(response['claim_assessments']) or set(assessments)!=set(claims):raise ValueError('probe must assess the actual frozen claim set')
        from .claims import claim_constraints
        from .formal_results import rebuild_instance_registry
        material=request['material_context']
        registry=rebuild_instance_registry(material['empirical_instances'],graph=graph,derived_instances=material['derived_instances'],evidence_mode=request['evidence_mode'],repository_root=root)
        constraints=claim_constraints(graph,verified_instance_results=registry)
        for identifier,row in assessments.items():
            claim=claims[identifier]
            if row['classification']!=claim['claim_basis']['kind'] or not row['evidence_refs'] or not set(row['evidence_refs']).issubset(claim['evidence_refs']) or constraints[identifier]['blocked'] and row['position']=='affirm':raise ValueError('probe overreaches its actual scoped evidence or classification')
        if not response['counterarguments']:raise ValueError('probe requires concrete evidence/claim-scoped counterarguments')
        for row in response['counterarguments']:
            claim=claims.get(row['claim_id'])
            if claim is None or row['scope']!=claim['claim_basis']['scope'] or not row['evidence_refs'] or not set(row['evidence_refs']).issubset(claim['evidence_refs']):raise ValueError('counterargument does not resolve its actual claim scope and material')
        if kind=='sensitivity' and response['changes_considered']!=request['task']['sensitivity_changes']:raise ValueError('sensitivity response omitted its actual registered change')
        if kind=='sensitivity':
            changes=request['task']['sensitivity_changes']
            impacts={row['path']:row for row in response['change_assessments']}
            if len(impacts)!=len(response['change_assessments']) or set(impacts)!={row['path'] for row in changes}:raise ValueError('sensitivity requires substantive reasoning for each actual changed path')
            for row in impacts.values():
                if not set(row['affected_claim_ids']).issubset(claims) or not set(row['evidence_refs']).issubset({ref for identifier in row['affected_claim_ids'] for ref in claims[identifier]['evidence_refs']}):raise ValueError('sensitivity impact does not resolve its actual claim/material scope')
        from .semantic_projection import validate_reader_section_privacy
        view=deepcopy(request['material_context'].get('computed_packet',{}))
        view['visibility_ledger']={'entries':deepcopy(request['reader_requirements']['protected_constraints'])}
        view['reader_sections']=[{'heading':'Probe evidence and scope','local_judgment':'Bounded probe output','paragraphs':[row['judgment'] for row in response['claim_assessments']]+[row['argument']+' '+row['defeat_condition'] for row in response['counterarguments']],'source_bindings':[]}]
        validate_reader_section_privacy(view)
    return deepcopy(response)


def _execution_directories(run: Path) -> tuple[Path, Path, Path]:
    attempt=run/'sem'/('attempt-'+uuid.uuid4().hex)
    capture,workspace=attempt/'capture',attempt/'provider'
    capture.mkdir(parents=True,mode=0o700)
    workspace.mkdir(mode=0o700)
    return attempt,capture,workspace


def execute_semantic_request_v4(request: Mapping[str, Any],*,binding: Mapping[str, Any] | None,run_directory: Path,repository_root: Path | None=None) -> dict[str, Any]:
    from .authoring import _communicate_limited,AuthoringCommunicationError
    from .materialization import _require_external_runs_root
    from .execution import _provider_launch_argv
    root=repository_path(repository_root)
    request=_native(request)
    validate_versioned_schema('xk-v4-semantic-execution-request.schema.json',request,repository_root=root)
    if request['source_inputs']!=_source(root) or request['model']!=MODEL or request['reasoning_effort']!=EFFORT:raise ValueError('semantic execution source or model drifted before launch')
    run=Path(run_directory).resolve()
    _require_external_runs_root(run,root)
    run.mkdir(parents=True,exist_ok=True)
    attempt,capture,workspace=_execution_directories(run)
    request_bytes=canonical_bytes(request)
    prompt=_prompt(request)
    (capture/'request.json').write_bytes(request_bytes)
    (capture/'stdin.bin').write_bytes(prompt)
    private,public,commitment=_authority()
    before=_repo_state(root)
    started=_now()
    stdout,stderr,output=b'',b'',b''
    notice=b''
    process=None
    command=[]
    status='not_run'
    errors=[]
    thread_id=None
    usage=None
    executable_sha=None
    response=None
    input_complete=False
    try:
        command,timeout,executable_sha=_binding(binding,root)
        if binding['kind']=='codex_provider':
            provider=binding['provider']
            command=[*command,'--json','--output-last-message',str(workspace/'completion-notice.txt'),'-']
            command=_provider_launch_argv(provider,command)
        kwargs={'start_new_session':True} if os.name=='posix' else {'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
        process=subprocess.Popen(command,cwd=workspace,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False,**kwargs)
        status='failed'
        try:
            stdout,stderr,input_complete=_communicate_limited(process,prompt,timeout_seconds=timeout,label='v4 semantic provider')
        except AuthoringCommunicationError as error:
            stdout,stderr,input_complete=error.stdout,error.stderr,error.input_complete
            raise ValueError('provider_communication_failed') from error
        if process.returncode!=0 or not input_complete:raise ValueError('provider_process_failed_or_input_incomplete')
        thread_id,events=parse_provider_events(stdout)
        if events[0].get('pid',process.pid)!=process.pid:raise ValueError('provider_event_PID_differs_from_actual_process')
        usage=events[-1].get('usage')
        if not isinstance(usage,dict) or not usage or any(type(value) is not int or value<0 for value in usage.values()):raise ValueError('provider_usage_provenance_unavailable')
        notice=_raw_file(workspace/'completion-notice.txt',limit=4096)
        read_semantic_output(workspace,notice=notice,limit=MAX_BYTES)
        output=_raw_file(workspace/'semantic-output.json')
        payload=read_json_text(output.decode('utf-8'))
        response=_validate_output(request,payload,root)
        _binding(binding,root)
        status='executed'
    except (ValueError,OSError,UnicodeError,KeyError,TypeError):
        errors.append('semantic_execution_not_verified' if process is not None else 'runtime_process_not_attached')
    after=_repo_state(root)
    if before!=after:
        status='failed'
        errors.append('readonly_source_repository_changed')
    (capture/'stdout.jsonl').write_bytes(stdout)
    (capture/'stderr.bin').write_bytes(stderr)
    (capture/'output.bin').write_bytes(output)
    (capture/'notice.bin').write_bytes(notice)
    payload={'schema_id':'xi-kari.v4.xk.semantic-execution-receipt','schema_version':4,'execution_id':attempt.name,'kind':request['kind'],'status':status,'parent_pid':os.getpid(),'child_pid':process.pid if process else None,'exit_status':process.returncode if process else None,'started_at':started,'completed_at':_now(),'input_complete':input_complete,'model':MODEL,'reasoning_effort':EFFORT,'served_model':'not_independently_reported','binding_kind':binding['kind'] if binding else None,'binding_sha256':sha256_json(binding),'executable_sha256':executable_sha,'argv':command,'argv_sha256':sha256_json(command),'request_sha256':sha256_bytes(request_bytes),'bindings':request['bindings'],'source_inputs':request['source_inputs'],'files':{name:{'sha256':sha256_file(capture/name),'bytes':(capture/name).stat().st_size} for name in ('request.json','stdin.bin','stdout.jsonl','stderr.bin','output.bin','notice.bin')},'thread_id':thread_id,'usage':usage,'usage_provenance':'captured_provider_JSONL' if usage else 'unavailable','semantic_response_sha256':sha256_json(response) if response is not None else None,'source_repository_before':before,'source_repository_after':after,'errors':errors,'permission_effect':'none','qualification_effect':'none','external_action_executed':False}
    validate_versioned_schema('xk-v4-semantic-execution-receipt.schema.json',payload,repository_root=root)
    receipt=_sign(payload,private,public)
    validate_versioned_schema('xk-v4-semantic-execution-attestation.schema.json',receipt,repository_root=root)
    (capture/'receipt.json').write_bytes(canonical_bytes(receipt))
    del private
    return {'status':status,'semantic_gate':'validated' if status=='executed' else 'failed' if process else 'not_evaluated','actual_model_execution':status=='executed' and binding['kind']=='codex_provider','attempt_directory':str(attempt),'authority_commitment_sha256':commitment,'receipt':receipt,'semantic_response':response,'errors':errors,'permission_effect':'none','qualification_effect':'none','external_action_executed':False}


def validate_semantic_execution_v4(execution: Mapping[str, Any],*,expected_request: Mapping[str, Any],binding: Mapping[str, Any] | None,repository_root: Path | None=None) -> dict[str, Any]:
    root=repository_path(repository_root)
    attempt=Path(execution['attempt_directory']).resolve()
    from .materialization import _require_external_runs_root
    _require_external_runs_root(attempt,root)
    capture=attempt/'capture'
    receipt=read_json_text(_raw_file(capture/'receipt.json').decode('utf-8'))
    validate_versioned_schema('xk-v4-semantic-execution-attestation.schema.json',receipt,repository_root=root)
    payload=_verify_signature(receipt,execution['authority_commitment_sha256'])
    validate_versioned_schema('xk-v4-semantic-execution-receipt.schema.json',payload,repository_root=root)
    if receipt!=execution['receipt'] or payload['binding_sha256']!=sha256_json(binding) or payload['request_sha256']!=sha256_json(expected_request) or payload['source_inputs']!=_source(root):raise ValueError('semantic execution receipt differs from expected runtime input')
    for name,record in payload['files'].items():
        raw=_raw_file(capture/name,limit=MAX_CAPTURE_BYTES if name=='request.json' else MAX_BYTES if name!='stdout.jsonl' else 64*1024*1024)
        if sha256_bytes(raw)!=record['sha256'] or len(raw)!=record['bytes']:raise ValueError('semantic execution captured bytes differ from signed receipt')
    request=read_json_text((capture/'request.json').read_text(encoding='utf-8'))
    if request!=_native(expected_request) or (capture/'stdin.bin').read_bytes()!=_prompt(expected_request):raise ValueError('semantic execution request/input bytes changed')
    if payload['source_repository_before']!=payload['source_repository_after']:raise ValueError('semantic execution altered its readonly source repository')
    if payload['status']!='executed':
        return {'status':payload['status'],'semantic_gate':'failed' if payload['child_pid'] else 'not_evaluated','actual_model_execution':False,'semantic_response':None,'receipt':receipt}
    argv,_timeout,executable_hash=_binding(binding,root)
    if type(payload['child_pid']) is not int or payload['child_pid']<1 or payload['child_pid']==payload['parent_pid'] or payload['exit_status']!=0 or not payload['input_complete'] or payload['executable_sha256']!=executable_hash:raise ValueError('semantic execution actual process/PID proof is invalid')
    thread,events=parse_provider_events((capture/'stdout.jsonl').read_bytes())
    if thread!=payload['thread_id'] or events[0].get('pid',payload['child_pid'])!=payload['child_pid'] or events[-1].get('usage')!=payload['usage']:raise ValueError('semantic execution provider lineage/usage differs from signed receipt')
    notice=_raw_file(attempt/'provider/completion-notice.txt',limit=4096)
    if notice!=(capture/'notice.bin').read_bytes():raise ValueError('semantic execution completion notice bytes changed')
    read_semantic_output(attempt/'provider',notice=notice,limit=MAX_BYTES)
    output=_raw_file(attempt/'provider/semantic-output.json')
    if output!=(capture/'output.bin').read_bytes():raise ValueError('semantic execution output file bytes differ from captured receipt')
    response=_validate_output(request,read_json_text(output.decode('utf-8')),root)
    if sha256_json(response)!=payload['semantic_response_sha256']:raise ValueError('semantic execution semantic output differs from runtime receipt')
    return {'status':'executed','semantic_gate':'validated','actual_model_execution':binding['kind']=='codex_provider','semantic_response':response,'receipt':receipt}


def execute_next_author_v4(packet: Mapping[str, Any],stage_controls: Mapping[str, Any],*,author_request: Mapping[str, Any],run_contract: Mapping[str, Any],binding: Mapping[str, Any] | None,run_directory: Path,repository_root: Path | None=None) -> dict[str, Any]:
    request=build_semantic_execution_request_v4(packet,stage_controls,run_contract=run_contract,kind='next_author',author_request=author_request,repository_root=repository_root)
    result=execute_semantic_request_v4(request,binding=binding,run_directory=run_directory,repository_root=repository_root)
    nodes=[node for path in (stage_controls['stage_results']['recursion']['result'] or {}).get('paths',[]) for node in path['nodes'] if node.get('author_request')==author_request]
    matched=result['semantic_response'] is not None and bool(nodes) and all(node['author_response']==result['semantic_response'] for node in nodes)
    result.update(matches_frozen_response=matched,continuation_gate='matched' if matched else 'needs_restaging' if result['status']=='executed' else 'failed')
    if result['status']=='executed' and not matched:result['errors']=[*result['errors'],'next_author_response_differs_from_frozen_continuation']
    return result


def execute_semantic_probes_v4(packet: Mapping[str, Any],stage_controls: Mapping[str, Any],*,run_contract: Mapping[str, Any],binding: Mapping[str, Any] | None,run_directory: Path,sensitivity_changes: Sequence[Mapping[str, Any]],repository_root: Path | None=None) -> dict[str, Any]:
    specs=[('red_team',None),('stance_stability','support'),('stance_stability','oppose'),('sensitivity','baseline'),('sensitivity','changed')]
    executions=[]
    requests=[]
    for kind,variant in specs:
        request=build_semantic_execution_request_v4(packet,stage_controls,run_contract=run_contract,kind=kind,variant=variant,sensitivity_changes=sensitivity_changes,repository_root=repository_root)
        requests.append(request)
        executions.append(execute_semantic_request_v4(request,binding=binding,run_directory=run_directory,repository_root=repository_root))
    def positions(index: int) -> dict[str, Any]:
        response=executions[index]['semantic_response']
        return {row['claim_id']:(row['position'],row['classification'],sorted(row['evidence_refs'])) for row in response['claim_assessments']} if response else {}
    good=all(row['status']=='executed' for row in executions)
    equal=requests[1]['bindings']['base_information_sha256']==requests[2]['bindings']['base_information_sha256']
    changed=[identifier for identifier,row in positions(3).items() if positions(4).get(identifier)!=row]
    impacts=(executions[4]['semantic_response'] or {}).get('change_assessments',[])
    unknown=any(row['impact']=='undetermined' for row in impacts)
    substantive_change=any(row['impact'] in {'strengthens','weakens','changes_scope'} for row in impacts)
    gates={'red_team':{'status':'examined' if executions[0]['status']=='executed' else 'failed','counterarguments':(executions[0]['semantic_response'] or {}).get('counterarguments',[])},'stance_stability':{'status':'stable' if good and equal and positions(1)==positions(2) else 'changed' if good and equal else 'failed','equal_information':equal,'different_claim_ids':[identifier for identifier,row in positions(1).items() if positions(2).get(identifier)!=row]},'sensitivity':{'status':'failed' if not good else 'changed' if changed or substantive_change else 'undetermined' if unknown else 'stable','changed_claim_ids':changed,'changes':_native(list(sensitivity_changes)),'change_assessments':impacts}}
    return {'executions':executions,'gates':gates,'actual_model_execution':all(row['actual_model_execution'] for row in executions),'permission_effect':'none','qualification_effect':'none','external_action_executed':False}


def execute_final_reader_v4(packet: Mapping[str, Any],stage_controls: Mapping[str, Any],*,run_contract: Mapping[str, Any],binding: Mapping[str, Any] | None,run_directory: Path,computed_outcomes: Mapping[str, Any] | None=None,repository_root: Path | None=None) -> dict[str, Any]:
    request=build_semantic_execution_request_v4(packet,stage_controls,run_contract=run_contract,kind='final_reader',computed_outcomes=computed_outcomes,repository_root=repository_root)
    result=execute_semantic_request_v4(request,binding=binding,run_directory=run_directory,repository_root=repository_root)
    result['reader_finalization']=result['semantic_response'] if result['status']=='executed' else None
    return result


__all__=('build_semantic_execution_request_v4','bind_semantic_execution_provider_v4','bind_semantic_execution_fixture_v4','execute_semantic_request_v4','validate_semantic_execution_v4','execute_next_author_v4','execute_semantic_probes_v4','execute_final_reader_v4')
