"""Synthetic boundary inputs and file-backed deterministic author transport."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from tests.test_p04_v4_authoring import _authoring_input
from xi_kari_runtime import evidence, execution
from xi_kari_runtime.canonical_json import canonical_bytes, sha256_file
from xi_kari_runtime.ontology_read_trace import (
    build_ontology_read_plan, content_access_witness, read_ontology_item_bytes,
)
from xi_kari_runtime.problem_contract import contract_hash, stance_neutrality_key
from xi_kari_runtime.semantic_projection import semantic_atom_paths, substantive_semantic_atoms


BODY = [
    "本用例只解释合成条文中的补偿责任。条文写有补偿，不证明补偿已经执行，也不证明每位成员已经受益。",
    "反方可以指出合成条文没有写明支付时间；这一缺口限制执行判断，同时保留对条文内容的有限解释。",
    "继续调查需要读取支付记录并承担核验成本。当前没有这些材料，因此付款状态保持未知，不能用完整的字段代替实际证据。",
    "若条文版本、适用成员或证据窗口改变，应重新判断。当前分析只支持解释条文，不授予现实执行权限，也不要求生成递归未来。",
]
CLOSED_MATERIALS = [{
    "source_id": "SOURCE-1", "title": "合成补偿条文",
    "content": "合成条文：每次轮班后应支付补偿。条文没有付款日期与实际支付记录。",
    "published_at": "2026-09-01T00:00:00Z", "event_at": "2026-09-01T00:00:00Z",
}]


@lru_cache(maxsize=1)
def source_inputs():
    return _authoring_input()


def static_author_output(*, problem=None, run_id="synthetic-v4-e2e", challenge="b" * 64,
                         purpose="Synthetic program boundary verification", mode="open-world",
                         materials=None):
    value, default_problem, default_plan, lock, events = deepcopy(source_inputs())
    problem = deepcopy(problem or default_problem)
    if mode == "closed-input":
        problem["retrieval_profile"] = "closed-input"
    value["semantic_packet"]["problem_contract"] = deepcopy(problem)
    value["semantic_packet"]["answer"]["direct_answer"] = "合成条文包含补偿要求，实际执行情况仍未知。"
    value["semantic_packet"]["reader_sections"] = [{
        "section_id": "synthetic-clause", "heading": "合成条文与执行材料",
        "local_judgment": "条文解释不产生现实执行资格。",
        "paragraphs": list(BODY), "source_bindings": [],
    }]
    if (default_plan["run_id"] == run_id and default_plan["content_access_challenge"] == challenge
            and default_plan["problem_contract_sha256"] == contract_hash(problem)):
        plan = default_plan
    else:
        plan = build_ontology_read_plan(
            ROOT, run_id=run_id, problem_contract_sha256=contract_hash(problem),
            content_access_challenge=challenge, source_version="v9.0",
        )
        records = []
        for row in plan["records"]:
            content = read_ontology_item_bytes(ROOT, row).decode("utf-8")
            excerpt = next((line.strip() for line in content.splitlines()
                            if len(line.strip()) >= 50 and re.search(r"[\u4e00-\u9fff]{8}", line)),
                           max(content.splitlines(), key=len).strip())[:600]
            records.append({
                "item_id": row["item_id"], "read_status": "read", "content_excerpt": excerpt,
                "content_witness": content_access_witness(
                    challenge=challenge, problem_contract_sha256=contract_hash(problem),
                    item_id=row["item_id"], content_sha256=row["content_sha256"],
                ),
                "problem_relation": {"status": "boundary_only", "rationale":
                    f"{row['item_id']} supplies the observed source boundary {excerpt}; this synthetic transport example supplies no empirical instance or external action authorization."},
            })
        value["ontology_read_trace"]["records"] = records
    packet = value["semantic_packet"]
    if mode == "closed-input":
        material = deepcopy((materials or CLOSED_MATERIALS)[0])
        source = packet["retrieval"]["sources"][0]
        metadata = {key: source[key] for key in (
            "source_revision", "canonical_locator", "lineage_refs", "research_design",
            "read_extent", "provenance_refs", "independence_key", "availability_status",
            "visibility", "protected_review",
        )}
        source = {key: material[key] for key in ("source_id", "title", "content", "published_at", "event_at")}
        source.update(origin="user_material", **metadata)
        packet["retrieval"]["sources"] = [source]
        packet["retrieval"].update(mode="closed-input", saturation_status="source_internal_only")
        packet["claim_mechanism_graph"]["evidence"][0]["evidence_identity"]["content_sha256"] = hashlib.sha256(source["content"].encode()).hexdigest()
    packet["visibility_ledger"] = {"entries": [{
        "canonical_path": path, "classification": "public", "disclosure": "include",
        "purpose": purpose, "authority_refs": [], "protection_reason": None,
    } for path in semantic_atom_paths(packet)]}
    section = packet["reader_sections"][0]
    for atom in substantive_semantic_atoms(packet):
        excerpt = atom["public_text"]
        section["paragraphs"].append(
            f"本题的合成记录明确写明：{excerpt}。这一范围用于合成条文的程序验证，不能证明现实执行或正式实例成立。"
        )
        section["source_bindings"].append({
            "source_path": atom["canonical_path"], "paragraph_index": len(section["paragraphs"]),
            "excerpt": excerpt,
        })
    return value, problem, plan, lock, events


def synthetic_reader_finalization(packet, *, purpose):
    view = deepcopy(packet)
    declared = {row['canonical_path']: row for row in view.get('visibility_ledger', {}).get('entries', [])}
    view['visibility_ledger'] = {'entries': [
        {**deepcopy(declared[path]), 'purpose': purpose} if path in declared else
        {'canonical_path': path, 'classification': 'public', 'disclosure': 'include',
         'purpose': purpose, 'authority_refs': [], 'protection_reason': None}
        for path in semantic_atom_paths(view)
    ]}
    section = {'section_id': 'synthetic-final-reader', 'heading': '合成条文与执行材料',
        'local_judgment': '条文解释不产生现实执行资格。', 'paragraphs': list(BODY), 'source_bindings': []}
    for atom in substantive_semantic_atoms(view):
        excerpt = atom['public_text']
        section['paragraphs'].append('本题合成记录明确写明：' + excerpt + '。这一范围只用于合成条文程序验证，不证明现实执行或正式实例成立。')
        section['source_bindings'].append({'source_path': atom['canonical_path'], 'paragraph_index': len(section['paragraphs']), 'excerpt': excerpt})
    return {'reader_sections': [section], 'visibility_ledger': view['visibility_ledger']}


def synthetic_production_output(request, *, protected_content=None):
    if 'kind' in request:
        if request['kind'] != 'final_reader':
            raise ValueError('the static synthetic provider only implements final reader execution')
        response = synthetic_reader_finalization(request['task']['readonly_packet'], purpose=request['reader_requirements']['purpose'])
        graph = request['material_context']['claim_mechanism_graph']
        return {'semantic_response': response, 'source_bindings': [
            {'claim_id': row['claim_id'], 'material_refs': row['claim_basis']['material_refs']} for row in graph['claims']]}
    plan = request['source_inputs']['ontology_read_plan']
    value, _, _, _, _ = static_author_output(problem=request['problem_contract'],
        run_id=request['run_id'], challenge=plan['content_access_challenge'],
        purpose=request['privacy_contract']['purpose'], mode=request['mode'],
        materials=request['source_inputs'].get('closed_input_materials'))
    packet = value['semantic_packet']
    for assessment in packet['retrieval']['assessments']:
        assessment.update(cannot_prove=['该合成条文只供程序验证，不能证明现实执行、经验效果或正式实例资格。'],
            affected_positions=['补偿安排涉及者的具体身份没有在给定合成条文中说明。'],
            low_power_positions=['给定合成条文未提供识别具体低权力位置所需的事实。'])
    for claim in packet['evidence']['claims']:
        for support in claim['support']:
            if support.get('summary') == 'A source-scope fixture.':
                support['summary'] = '该合成记录用于验证条文解释的材料范围。'
    if protected_content:
        for entry in packet['visibility_ledger']['entries']:
            if entry['canonical_path'] == 'retrieval.sources[0].content':
                entry.update(classification='sensitive', disclosure='withhold',
                    authority_refs=['XK0-PRIVACY-CONTRACT-SYNTHETIC'],
                    protection_reason='The material body is protected for this audience')
        packet['evidence']['claims'][0]['support'][0]['support_checks']['source_exists']['status'] = 'invalid-schema-status'
    packet.update(synthetic_reader_finalization(packet, purpose=request['privacy_contract']['purpose']))
    return value


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value) + b"\n")


def packet_inputs(*, problem=None):
    value, problem, plan, lock, events = static_author_output(problem=problem)
    semantic, _, _ = execution.parse_base_authoring_output(
        canonical_bytes(value), problem_contract=problem, mode="open-world", repository_root=ROOT,
        ontology_read_plan=plan, source_lock=lock, source_events=events, contract_version=4,
    )
    retrieval = deepcopy(semantic["retrieval"])
    retrieval["run_id"] = "synthetic-v4-e2e"
    for source in retrieval["sources"]:
        source["assessment_verdict"] = "admitted"
        source["content_sha256"] = hashlib.sha256(source["content"].encode()).hexdigest()
    semantic["evidence"] = evidence.build_evidence_ledger(
        run_id="synthetic-v4-e2e", claims=semantic["evidence"]["claims"],
        retrieval_index=retrieval, contract_version=4,
    )
    semantic["retrieval"] = retrieval
    contract = {
        "run_id": "synthetic-v4-e2e", "question": problem["question"], "mode": "open-world",
        "evidence_cutoff": problem["evidence_cutoff"], "problem_contract": problem,
        "problem_contract_sha256": contract_hash(problem),
        "stance_neutrality_key": stance_neutrality_key(problem, mode="open-world"),
        "privacy_contract": None, "contract_profile": "production-authoring-v4",
    }
    semantic["visibility_ledger"] = public_visibility(semantic)
    return semantic, contract


def public_visibility(payload):
    return {"entries": [{
        "canonical_path": path, "classification": "public", "disclosure": "include",
        "purpose": "Synthetic program boundary verification", "authority_refs": [],
        "protection_reason": None,
    } for path in semantic_atom_paths(payload)]}


def fresh_boundary(directory, action, data, *, repository=ROOT):
    path = directory / (action + "-input.json")
    write_json(path, data)
    command = [sys.executable, "-B", "-m", "tests.test_v4_pipeline_e2e_fixtures",
               action, str(path), str(repository)]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
    environment["PYTHONPATH"] = os.pathsep.join((str(ROOT), str(ROOT / "scripts")))
    process = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True,
                             text=True, encoding="utf-8", timeout=60, check=False)
    write_json(directory / (action + "-process.json"), {
        "command": command, "exit_code": process.returncode, "parent_pid": os.getpid(),
        "stdout": process.stdout, "stderr": process.stderr, "actual_model_runs": 0,
    })
    return process


def domain_repository(directory):
    root = directory / "synthetic-domain-product"
    for relative in (
        "references/source/v9.0/source-manifest.json",
        "references/source/v9.0/indexes/anchors.json",
        "references/source/v9.0/indexes/body-blocks.json",
        "references/ontology/v9.0/authored/domain-identities.json",
    ):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    shutil.copytree(ROOT / "references/learning-packs/domains", root / "references/learning-packs/domains")
    catalog = json.loads((ROOT / "references/domains/index.json").read_text("utf-8"))
    for entry in catalog["entries"]:
        path = f"references/learning-packs/domains/{entry['domain_id']}.md"
        entry.update(content_status="available", content_path=path,
                     content_sha256=sha256_file(root / path), read_trace_status="requires_run_trace")
    write_json(root / "references/domains/index.json", catalog)
    return root


def boundary_main(action, path, repository):
    from xi_kari_runtime import claims, packet_v4, prose, recursion, transformations
    from xi_kari_runtime.semantic_projection import typed_semantic_atoms
    data = json.loads(path.read_text("utf-8"))
    if action == "packet":
        packet_v4.require_packet_contract_v4(data["packet"], mode="open-world",
                                            run_contract=data["contract"], repository_root=repository)
        body = prose.render_answer(data["packet"])
        (path.parent / "synthetic-reader.md").write_text(body, encoding="utf-8")
        result = {"atom_paths": [atom["canonical_path"] for atom in typed_semantic_atoms(data["packet"])],
                  "body": body, "formal_qualification": data["packet"]["claim_mechanism_graph"]["claims"][0]["formal_qualification"]}
    elif action == "world":
        result = packet_v4.validate_world_stage(data["world"], evidence_ledger=data["ledger"],
                                               retrieval_index=data["retrieval"], repository_root=repository)
    elif action == "causal":
        result = claims.validate_causal_assessments(data["assessments"], claim_mechanism_graph=data["graph"],
                                                  repository_root=repository)
    elif action == "formal":
        result = claims.claim_constraints(claims.validate_claim_graph(data["graph"], repository_root=repository))
    elif action == "scale":
        result = transformations.validate_scale_instance(data["record"], **data["registries"])
    elif action == "recursion":
        observations = []
        def author(request):
            observations.append(deepcopy(request))
            return {"possible_choice_ids": ["CHEAP"], "choice_basis": "Synthetic conditional resource use"}
        child = recursion.execute_recursive_step(
            data["parent"], data["event"], action_catalog=data["actions"], author=author,
            evidence_registry=data["evidence"], independent_question="Which choices remain after the conditional cost?",
            incremental_gain="The changed resource value excludes the expensive choice",
        )
        recursion.validate_registered_child(child, parent=data["parent"], event=data["event"],
                                             action_catalog=data["actions"], evidence_registry=data["evidence"])
        result = {"child": child, "observed_request": observations[0]}
    elif action == "domain":
        from xi_kari_runtime.domains import validate_domain_run
        result = validate_domain_run(repository, Path(data["run_dir"]),
                                     problem_contract_sha256=data["problem_hash"], run_id=data["run_id"])
    else:
        raise ValueError("Unknown synthetic boundary")
    print(json.dumps({"pid": os.getpid(), "result": result, "actual_model_runs": 0}, ensure_ascii=False))


def deterministic_provider(directory, *, protected_content=None):
    provider = directory / "synthetic_v4_author.py"
    observation = directory / "synthetic-author-observation.json"
    program = f"#!{Path(sys.executable).resolve()}\n" + f"ROOT = {str(ROOT)!r}\nOBSERVATION = {str(observation)!r}\nPROTECTED = {protected_content!r}\n" + '''import json, os, pathlib, sys
sys.path.insert(0, ROOT)
from tests.test_v4_pipeline_e2e_fixtures import synthetic_production_output
prompt = sys.stdin.buffer.read().decode("utf-8")
is_reader = "REQUEST_JSON\\n" in prompt
if is_reader:
    request = json.loads(prompt.split("REQUEST_JSON\\n", 1)[1])
else:
    marker = "运行时请求：\\n" if "运行时请求：\\n" in prompt else "运行时请求（只读绑定）：\\n"
    request = json.loads(prompt.rsplit(marker, 1)[1])
value = synthetic_production_output(request, protected_content=PROTECTED)
if not is_reader:
    pathlib.Path(OBSERVATION).write_text(json.dumps({"pid": os.getpid(),
        "source_version": request["source_inputs"]["source_version"],
        "contract_version": request.get("contract_version"),
        "synthetic": True, "actual_model_runs": 0}), encoding="utf-8")
pathlib.Path("semantic-output.json").write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
pathlib.Path(sys.argv[sys.argv.index("--output-last-message") + 1]).write_text("SEMANTIC_OUTPUT_READY", encoding="utf-8")
for event in ({"type": "thread.started", "thread_id": "synthetic-final-reader" if is_reader else "synthetic-v4-transport"},
              {"type": "turn.started"}, {"type": "turn.completed", "usage": {"input_tokens": 11, "output_tokens": 17}}):
    print(json.dumps(event), flush=True)
'''
    provider.write_text(program, encoding="utf-8", newline="\n")
    provider.chmod(0o755)
    return provider, observation


if __name__ == "__main__":
    boundary_main(sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]))
