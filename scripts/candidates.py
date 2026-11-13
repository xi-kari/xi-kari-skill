#!/usr/bin/env python3
"""Keep the candidates of one generative task with their lineage, identity and status.

A candidate is something derived from stated starting points by a named move: a
consequence inside a declared model, a requirement a definition places on a claim,
an empirical or variable candidate still to be tested, a heuristic analogy, a new
question or a proposal. The ledger records where each one came from, what would
tell it apart from its rivals, and how far testing has gone.

It is an inventory. It never judges whether a candidate is true, new or worth
pursuing, and a candidate does not become a fact by being recorded, derived
further or counted.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from xikari_paths import require_external_output
finally:
    sys.path.pop(0)


FORMAT = 'xikari-candidates-1'
MARK = '<!-- xikari-candidates -->'
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z')
BASE_KINDS = {
    'observed': '观察',
    'supported': '已有支持的判断',
    'conditional': '条件结论',
    'definition': '所用定义',
    'assumption': '明示假设',
    'stated': '未核陈述',
}
IDENTITIES = {
    'formal': '模型内推论',
    'definitional': '定义要求',
    'empirical': '经验候选',
    'variable': '变量候选',
    'analogy': '启发性类比',
    'question': '新问题',
    'proposal': '构想',
}
MOVES = {
    'commit': '展开承诺',
    'compose': '核对组合',
    'task': '改换任务',
    'scale': '换尺度',
    'relation': '换关系',
    'representation': '换表示',
    'position': '换位置',
    'clock': '换时钟',
    'invert': '反过来问',
    'residual': '追残差',
    'transfer': '跨域借问',
    'association': '联想',
}
TRANSFORM_MOVES = {'scale', 'relation', 'representation', 'transfer'}
NOVELTY = {
    'restated': '重述',
    'known': '已有',
    'recalled': '可能已有',
    'new_here': '对本题新',
    'unseen_in_scope': '所查范围内未见',
}
STRENGTHS = {'expression': '表达级', 'exploration': '探索级', 'diagnostic': '诊断级'}
STATUSES = {
    'proposed': '提出',
    'testing': '检验中',
    'supported': '得到支持的候选',
    'rejected': '拒绝',
    'retired': '退役',
}
TRANSITIONS = {
    'proposed': {'testing', 'rejected', 'retired'},
    'testing': {'supported', 'rejected', 'retired'},
    'supported': {'testing', 'rejected', 'retired'},
    'rejected': set(),
    'retired': set(),
}
ACTIVE = {'proposed', 'testing', 'supported'}
TESTABLE = {'empirical', 'variable'}
GRADED = {'empirical', 'variable', 'analogy'}
HANDED_ON = {'question', 'proposal'}
DIRECTIONS = {'supports': '支持', 'undercuts': '削弱', 'context': '背景'}
RECORD_KEYS = ('kept', 'changed', 'lost')
RECORD_LABELS = {'kept': '保持', 'changed': '改变', 'lost': '丢失'}
ANALOGY_TEXT = ('source_domain', 'target_domain', 'test')
ANALOGY_LISTS = ('shared', 'differences', 'not_transferable', 'mapping')
ANALOGY_LABELS = {
    'source_domain': '源域',
    'target_domain': '目标域',
    'shared': '共享结构',
    'differences': '关键差异',
    'not_transferable': '不可迁移条件',
    'mapping': '变量映射',
    'test': '区分性检验',
}
BASE_KEYS = {'id', 'statement', 'kind', 'source', 'conditions', 'section'}
CANDIDATE_KEYS = {
    'id', 'statement', 'identity', 'move', 'parents', 'record', 'model', 'derivation', 'analogy',
    'residual', 'novelty', 'observables', 'rivals', 'minimal_test', 'risk', 'sensitive', 'necessity',
    'forbidden_uses', 'upgrade_conditions', 'reject_conditions', 'changes', 'strength',
    'post_outcome', 'theory', 'supersedes',
}
RUNTIME_KEYS = {'status', 'history', 'added_at', 'revisions'}
STEP_KEYS = {'from', 'to', 'at', 'note', 'evidence', 'strength'}
MAX_BYTES = 4 * 1024 * 1024
MAX_TEXT = 8000
MAX_LIST = 200
MAX_ITEMS = 2000
MAX_GENERATION = 3
SCOPE = ('仅核对账本结构、谱系与引用能否解析；不判断候选是否为真、是否真的新、'
         '区分观察是否有区分力，也不证明生成工作已经完成。')
NOTICE = ('本账本记录候选从哪些起点、经哪种走法得到，以及各自的身份、检验办法和当前状态。'
          '登记、续推和数量都不提高任何一项的支持；候选得到支持后仍须进入相应的对象、变量或机制合同。')


class CandidateError(ValueError):
    """Invalid candidate-ledger data."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def is_blank(text: str) -> bool:
    """True when nothing a reader could see is left: spaces, control and zero-width characters only."""
    return all(char.isspace() or unicodedata.category(char) in {'Cf', 'Cc', 'Zs', 'Zl', 'Zp'} for char in text)


def read_json(path: Path):
    def unique_pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise CandidateError(f'JSON含重复字段：{key}')
            result[key] = value
        return result

    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise CandidateError(f'无法读取 {path}: {exc}') from exc
    if len(data) > MAX_BYTES:
        raise CandidateError(f'{path} 超过4MiB，请拆分为多个账本或记录。')
    try:
        value = json.loads(data.decode('utf-8-sig'), object_pairs_hook=unique_pairs)
        json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')
    except UnicodeDecodeError as exc:
        raise CandidateError(f'{path} 不是UTF-8文本: {exc}') from exc
    except UnicodeEncodeError as exc:
        raise CandidateError(f'{path} 含无法以UTF-8保存的字符（如孤立的代理项）。') from exc
    except json.JSONDecodeError as exc:
        raise CandidateError(f'{path} 不是有效JSON: {exc}') from exc
    except RecursionError as exc:
        raise CandidateError(f'{path} 的JSON嵌套过深。') from exc
    except CandidateError:
        raise
    except ValueError as exc:
        raise CandidateError(f'{path} 含无法保存的数值（NaN、Infinity或过大的整数）。') from exc
    return value


def text_of(item, field, where, required=False, limit=MAX_TEXT) -> str:
    value = item.get(field, '')
    if not isinstance(value, str) or len(value) > limit or (required and is_blank(value)):
        raise CandidateError(f'{where}.{field}须为{"非空" if required else ""}文本，不超过{limit}字符。')
    return value


def text_list(item, field, where, required=False) -> list:
    value = item.get(field, [])
    if (not isinstance(value, list) or len(value) > MAX_LIST
            or any(not isinstance(entry, str) or is_blank(entry) or len(entry) > MAX_TEXT for entry in value)):
        raise CandidateError(f'{where}.{field}应是文字列表：至多{MAX_LIST}项，每项非空且不超过{MAX_TEXT}字符。')
    if required and not value:
        raise CandidateError(f'{where}.{field}不能为空。')
    return value


def identifier_of(item, where) -> str:
    value = item.get('id')
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise CandidateError(f'{where}的id须以字母或数字开头，只含 A-Za-z0-9._-，不超过96字符: {value!r}')
    return value


def choice_of(item, field, options, where) -> str:
    value = item.get(field)
    if not isinstance(value, str) or value not in options:
        raise CandidateError(f'{where}.{field}须为 ' + '、'.join(options) + ' 之一。')
    return value


def validate_base(item, stored=False) -> None:
    if not isinstance(item, dict):
        raise CandidateError('起点须为JSON对象。')
    where = f'起点 {identifier_of(item, "起点")}'
    extra = set(item) - BASE_KEYS - ({'added_at'} if stored else set())
    if extra:
        raise CandidateError(f'{where}含未知字段，不能静默忽略: ' + ', '.join(sorted(extra)))
    text_of(item, 'statement', where, required=True)
    kind = choice_of(item, 'kind', BASE_KINDS, where)
    text_of(item, 'source', where, required=kind in {'observed', 'supported', 'stated'})
    text_list(item, 'conditions', where, required=kind == 'conditional')
    text_of(item, 'section', where, required=kind == 'definition', limit=32)


def validate_evidence(entries, where) -> list:
    if not isinstance(entries, list) or len(entries) > MAX_LIST:
        raise CandidateError(f'{where}的证据须为列表，至多{MAX_LIST}项。')
    for entry in entries:
        if not isinstance(entry, dict):
            raise CandidateError(f'{where}的证据每项须为对象。')
        extra = set(entry) - {'ref', 'direction', 'note'}
        if extra:
            raise CandidateError(f'{where}的证据含未知字段: ' + ', '.join(sorted(extra)))
        text_of(entry, 'ref', where + '.evidence', required=True)
        choice_of(entry, 'direction', DIRECTIONS, where + '.evidence')
        text_of(entry, 'note', where + '.evidence')
    return entries


def validate_history(item, where) -> None:
    """The stored trail must be one the tool could have written; anything else means a hand edit."""
    tampered = f'{where}的状态经过不是本工具能写出的；账本可能被直接改写。'
    identity = item['identity']
    status = choice_of(item, 'status', STATUSES, where)
    history = item.get('history')
    if not isinstance(history, list) or len(history) > MAX_LIST:
        raise CandidateError(f'{where}.history须为列表。')
    current = 'proposed'
    for step in history:
        if (not isinstance(step, dict) or set(step) - STEP_KEYS or step.get('from') != current
                or step.get('to') not in TRANSITIONS.get(current, set())
                or not isinstance(step.get('at'), str) or is_blank(step['at'])):
            raise CandidateError(tampered)
        target = step['to']
        note = text_of(step, 'note', where + '.history')
        evidence = validate_evidence(step.get('evidence', []), where)
        if identity in HANDED_ON and target != 'retired':
            raise CandidateError(tampered)
        if target == 'supported' and not any(entry['direction'] == 'supports' for entry in evidence):
            raise CandidateError(f'{where}标为得到支持的一步没有支持性证据；账本可能被直接改写。')
        if (target in {'rejected', 'retired'} or (current == 'supported' and target == 'testing')) and is_blank(note):
            raise CandidateError(tampered)
        if 'strength' in step:
            if (identity not in GRADED or step['strength'] not in STRENGTHS
                    or (step['strength'] == 'diagnostic' and target != 'supported')):
                raise CandidateError(tampered)
        current = target
    if current != status:
        raise CandidateError(f'{where}的当前状态与经过不一致；账本可能被直接改写。')
    if item.get('strength') == 'diagnostic' and status != 'supported':
        raise CandidateError(f'{where}: 诊断级须与“得到支持的候选”同时成立；账本可能被直接改写。')
    revisions = item.get('revisions', [])
    if not isinstance(revisions, list) or len(revisions) > MAX_LIST or any(
            not isinstance(entry, dict) or set(entry) != {'at', 'note', 'before'}
            or not isinstance(entry['at'], str) or is_blank(entry['at'])
            or not isinstance(entry['note'], str) or is_blank(entry['note'])
            or not isinstance(entry['before'], dict) for entry in revisions):
        raise CandidateError(f'{where}的修订记录不是本工具能写出的；账本可能被直接改写。')
    if 'added_at' in item and not isinstance(item['added_at'], str):
        raise CandidateError(tampered)


def validate_candidate(item, stored=False) -> None:
    """Check one candidate's own fields. Lineage is checked against the ledger separately."""
    if not isinstance(item, dict):
        raise CandidateError('候选须为JSON对象。')
    where = f'候选 {identifier_of(item, "候选")}'
    runtime = set(item) & RUNTIME_KEYS
    if runtime and not stored:
        raise CandidateError(f'{where}: ' + ', '.join(sorted(runtime)) + ' 由工具写入，记录中不得自带；'
                             '新候选一律从“提出”开始，状态变化用 advance，改动用 revise。')
    extra = set(item) - CANDIDATE_KEYS - (RUNTIME_KEYS if stored else set())
    if extra:
        raise CandidateError(f'{where}含未知字段，不能静默忽略: ' + ', '.join(sorted(extra)))
    text_of(item, 'statement', where, required=True)
    identity = choice_of(item, 'identity', IDENTITIES, where)
    move = choice_of(item, 'move', MOVES, where)

    parents = item.get('parents', [])
    if (not isinstance(parents, list) or len(parents) > MAX_LIST
            or any(not isinstance(parent, str) or not ID.fullmatch(parent) for parent in parents)):
        raise CandidateError(f'{where}.parents须为标识列表。')
    if len(set(parents)) != len(parents):
        raise CandidateError(f'{where}.parents含重复标识。')
    if item['id'] in parents:
        raise CandidateError(f'{where}不能以自己为父项。')
    if move == 'association':
        if parents:
            raise CandidateError(f'{where}: 联想没有父项；有父项时写明实际走法。')
        if identity in {'formal', 'definitional'}:
            raise CandidateError(f'{where}: 没有起点的联想不能是{IDENTITIES[identity]}；推论与定义要求须有父项。')
    elif not parents:
        raise CandidateError(f'{where}: 走法“{MOVES[move]}”须有父项；没有起点的只能登记为联想 association。')

    if 'record' in item or move in TRANSFORM_MOVES:
        record = item.get('record')
        if not isinstance(record, dict) or set(record) - set(RECORD_KEYS):
            raise CandidateError(f'{where}.record须为对象，只含 kept、changed、lost。')
        filled = [key for key in RECORD_KEYS if text_list(record, key, where + '.record')]
        if not filled:
            raise CandidateError(f'{where}: 变换类走法须记录保持、改变或丢失中至少一项，不能预设无损。')

    text_of(item, 'model', where, required=identity == 'formal')
    text_list(item, 'derivation', where, required=identity in {'formal', 'definitional'})

    theory = item.get('theory', [])
    if not isinstance(theory, list) or len(theory) > MAX_LIST or any(
            not isinstance(entry, dict) or set(entry) != {'section'}
            or not isinstance(entry['section'], str) or is_blank(entry['section'])
            or len(entry['section']) > 32 for entry in theory):
        raise CandidateError(f'{where}.theory每项须为只含section的对象，如 {{"section": "2.6"}}。')
    if identity == 'definitional' and not theory:
        raise CandidateError(f'{where}: 定义要求须指出所依据的原文小节 theory。')

    if 'analogy' in item or identity == 'analogy' or move == 'transfer':
        analogy = item.get('analogy')
        if not isinstance(analogy, dict) or set(analogy) != set(ANALOGY_TEXT) | set(ANALOGY_LISTS):
            raise CandidateError(f'{where}.analogy须含且只含 source_domain、target_domain、shared、differences、'
                                 'not_transferable、mapping、test 七项。')
        for field in ANALOGY_TEXT:
            text_of(analogy, field, where + '.analogy', required=True)
        for field in ANALOGY_LISTS:
            text_list(analogy, field, where + '.analogy', required=True)

    text_of(item, 'residual', where, required=move == 'residual' or identity == 'variable')

    novelty = item.get('novelty')
    if not isinstance(novelty, dict) or set(novelty) - {'level', 'scope', 'prior'}:
        raise CandidateError(f'{where}.novelty须为对象，只含 level、scope、prior。')
    level = choice_of(novelty, 'level', NOVELTY, where + '.novelty')
    text_of(novelty, 'scope', where + '.novelty', required=level in {'recalled', 'new_here', 'unseen_in_scope'})
    text_list(novelty, 'prior', where + '.novelty', required=level in {'known', 'recalled'})

    testable = identity in TESTABLE
    text_list(item, 'observables', where, required=testable)
    rivals = item.get('rivals', [])
    if not isinstance(rivals, list) or len(rivals) > MAX_LIST:
        raise CandidateError(f'{where}.rivals须为列表。')
    for rival in rivals:
        if not isinstance(rival, dict) or set(rival) != {'statement', 'distinguishing'}:
            raise CandidateError(f'{where}.rivals每项须含且只含 statement 与 distinguishing。')
        text_of(rival, 'statement', where + '.rivals', required=True)
        text_of(rival, 'distinguishing', where + '.rivals', required=True)
    if testable and not rivals:
        raise CandidateError(f'{where}: {IDENTITIES[identity]}须至少并列一个竞争项及其区分观察。')
    text_of(item, 'minimal_test', where, required=testable)
    text_list(item, 'reject_conditions', where, required=testable or identity == 'analogy')
    text_list(item, 'upgrade_conditions', where, required=identity == 'variable')
    text_list(item, 'forbidden_uses', where, required=identity == 'variable')
    text_list(item, 'changes', where)

    sensitive = item.get('sensitive', False)
    if type(sensitive) is not bool:
        raise CandidateError(f'{where}.sensitive须为true或false。')
    text_of(item, 'risk', where, required=sensitive)
    text_of(item, 'necessity', where, required=sensitive)

    if identity in GRADED:
        strength = choice_of(item, 'strength', STRENGTHS, where)
        if strength == 'diagnostic' and not stored:
            raise CandidateError(f'{where}: 新候选没有外部可观察材料，强度只能是 expression 或 exploration；'
                                 '取得支持后用 advance 调整。')
    elif 'strength' in item:
        raise CandidateError(f'{where}.strength只用于经验候选、变量候选和启发性类比。')

    if 'post_outcome' in item:
        text_of(item, 'post_outcome', where, required=True)
    if 'supersedes' in item and (not isinstance(item['supersedes'], str) or not ID.fullmatch(item['supersedes'])
                                 or item['supersedes'] == item['id']):
        raise CandidateError(f'{where}.supersedes须指向另一条候选的标识。')

    if stored:
        validate_history(item, where)


def empty_ledger() -> dict:
    return {'schema_version': 1, 'format': FORMAT, 'question': '', 'base': [], 'candidates': []}


def parents_of(item: dict) -> list:
    return item.get('parents', [])


def lineage_order(candidates: list) -> list:
    """Candidate identifiers with every parent before its children; a cycle is an error."""
    by_id = {entry['id']: entry for entry in candidates}
    children = {identifier: [] for identifier in by_id}
    waiting = {}
    for entry in candidates:
        own = [parent for parent in parents_of(entry) if parent in by_id]
        waiting[entry['id']] = len(own)
        for parent in own:
            children[parent].append(entry['id'])
    ready = [identifier for identifier, count in waiting.items() if count == 0]
    position = 0
    while position < len(ready):
        for child in children[ready[position]]:
            waiting[child] -= 1
            if waiting[child] == 0:
                ready.append(child)
        position += 1
    if len(ready) != len(by_id):
        stuck = [identifier for identifier in by_id if waiting[identifier] > 0]
        raise CandidateError('谱系成环，涉及：' + '、'.join(stuck[:12]) + ('等' if len(stuck) > 12 else ''))
    return ready


def ancestors_in(by_id: dict, identifier: str) -> list:
    """All ancestors of one entry, nearest first, each listed once."""
    order, seen = [], set()
    queue = list(parents_of(by_id[identifier]))
    position = 0
    while position < len(queue):
        current = queue[position]
        position += 1
        if current in seen or current not in by_id:
            continue
        seen.add(current)
        order.append(current)
        queue.extend(parents_of(by_id[current]))
    return order


def check_lineage(base: list, candidates: list) -> None:
    """Identifiers are unique across both lists, every parent resolves, and neither lineage nor replacement loops."""
    if len(base) + len(candidates) > MAX_ITEMS:
        raise CandidateError(f'一份账本至多登记{MAX_ITEMS}项起点与候选；更多时按问题拆分账本。')
    seen = set()
    for entry in list(base) + list(candidates):
        if entry['id'] in seen:
            raise CandidateError(f'标识重复：{entry["id"]}；起点与候选共用一个标识空间。')
        seen.add(entry['id'])
    by_id = {entry['id']: entry for entry in candidates}
    for entry in candidates:
        for parent in parents_of(entry):
            if parent not in seen:
                raise CandidateError(f'候选 {entry["id"]} 的父项 {parent} 不存在。')
        if 'supersedes' in entry and entry['supersedes'] not in by_id:
            raise CandidateError(f'候选 {entry["id"]} 的 supersedes 所指候选不存在。')
    lineage_order(candidates)
    everything = {entry['id']: entry for entry in list(base) + list(candidates)}
    for entry in candidates:
        if 'supersedes' not in entry:
            continue
        chain = {entry['id']}
        current = entry
        while 'supersedes' in current:
            target = current['supersedes']
            if target in chain:
                raise CandidateError(f'候选 {entry["id"]} 的取代关系成环。')
            chain.add(target)
            current = by_id[target]
        if entry['supersedes'] in ancestors_in(everything, entry['id']):
            raise CandidateError(f'候选 {entry["id"]} 不能取代自己的父项或祖先；取代它的候选须从原来的起点重新推出。')


def load_ledger(path: Path) -> dict:
    if not Path(path).exists():
        return empty_ledger()
    ledger = read_json(path)
    if (not isinstance(ledger, dict) or type(ledger.get('schema_version')) is not int
            or ledger['schema_version'] != 1 or ledger.get('format') != FORMAT
            or not isinstance(ledger.get('base'), list) or not isinstance(ledger.get('candidates'), list)
            or not isinstance(ledger.get('question', ''), str)):
        raise CandidateError('目标不是可识别的候选账本，不会覆盖。')
    extra = set(ledger) - {'schema_version', 'format', 'question', 'base', 'candidates'}
    if extra:
        raise CandidateError('候选账本含未知字段: ' + ', '.join(sorted(extra)))
    ledger.setdefault('question', '')
    if len(ledger['question']) > MAX_TEXT:
        raise CandidateError(f'账本的question不超过{MAX_TEXT}字符。')
    if len(ledger['base']) + len(ledger['candidates']) > MAX_ITEMS:
        raise CandidateError(f'一份账本至多登记{MAX_ITEMS}项起点与候选；更多时按问题拆分账本。')
    for item in ledger['base']:
        validate_base(item, stored=True)
    for item in ledger['candidates']:
        validate_candidate(item, stored=True)
    check_lineage(ledger['base'], ledger['candidates'])
    return ledger


def save_ledger(path: Path, ledger: dict, expected: bytes | None) -> None:
    require_external_output(path, __file__)
    path = Path(path).resolve()
    lock = path.with_name(path.name + '.lock')
    require_external_output(lock, __file__)
    payload = (json.dumps(ledger, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    if len(payload) > MAX_BYTES:
        raise CandidateError('写入后账本将超过4MiB，之后无法再读取；本次未提交，请按问题拆分账本。')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    owns_lock = False
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.candidates-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise CandidateError('候选账本有其他写入者或遗留写锁；本次未提交。确认写入结束并重读后再处理，'
                                 '不自动移除锁。') from error
        owns_lock = True
        os.close(descriptor)
        current = path.read_bytes() if path.exists() else None
        if current != expected:
            raise CandidateError('候选账本已由其他工作改变，请重读后再处理。')
        if expected is None:
            try:
                os.link(temporary, path)
            except FileExistsError as error:
                raise CandidateError('候选账本在首次提交前已出现；本次未覆盖，请重读后再处理。') from error
        else:
            os.replace(temporary, path)
            temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if owns_lock:
            lock.unlink(missing_ok=True)


def add_records(ledger_path: Path, record_path: Path) -> dict:
    require_external_output(ledger_path, __file__)
    if Path(ledger_path).resolve() == Path(record_path).resolve():
        raise CandidateError('记录和账本不能是同一文件。')
    expected = ledger_path.read_bytes() if ledger_path.exists() else None
    ledger = load_ledger(ledger_path)
    record = read_json(record_path)
    if not isinstance(record, dict) or set(record) - {'question', 'base', 'candidates'}:
        raise CandidateError('记录须为对象，只含 question、base、candidates。')
    base = record.get('base', [])
    candidates = record.get('candidates', [])
    if not isinstance(base, list) or not isinstance(candidates, list) or not (base or candidates):
        raise CandidateError('记录须至少含一项起点 base 或候选 candidates。')
    question = record.get('question', '')
    if not isinstance(question, str) or len(question) > MAX_TEXT:
        raise CandidateError(f'question须为不超过{MAX_TEXT}字符的文本。')
    if not is_blank(question):
        if not is_blank(ledger['question']) and ledger['question'] != question:
            raise CandidateError('账本已登记另一个问题；不同的问题另建账本。')
        ledger['question'] = question
    stamp = _now()
    for item in base:
        validate_base(item)
    for item in candidates:
        validate_candidate(item)
    new_base = [dict(item, added_at=stamp) for item in base]
    new_candidates = [dict({'parents': []}, **item, status='proposed', history=[], added_at=stamp)
                      for item in candidates]
    check_lineage(ledger['base'] + new_base, ledger['candidates'] + new_candidates)
    ledger['base'].extend(new_base)
    ledger['candidates'].extend(new_candidates)
    save_ledger(ledger_path, ledger, expected)
    return {'ledger': str(Path(ledger_path).resolve()),
            'added_base': [item['id'] for item in new_base],
            'added_candidates': [item['id'] for item in new_candidates],
            'scope': SCOPE}


def revise(ledger_path: Path, record_path: Path, note: str) -> dict:
    """Replace a candidate that is still only proposed, keeping what it said before and why it changed."""
    require_external_output(ledger_path, __file__)
    if not Path(ledger_path).exists():
        raise CandidateError('候选账本不存在。')
    if Path(ledger_path).resolve() == Path(record_path).resolve():
        raise CandidateError('记录和账本不能是同一文件。')
    if not isinstance(note, str) or is_blank(note) or len(note) > MAX_TEXT:
        raise CandidateError(f'修订须写明理由 --note，不超过{MAX_TEXT}字符。')
    expected = Path(ledger_path).read_bytes()
    ledger = load_ledger(ledger_path)
    record = read_json(record_path)
    if not isinstance(record, dict):
        raise CandidateError('候选须为JSON对象。')
    position = next((index for index, item in enumerate(ledger['candidates'])
                     if item['id'] == record.get('id')), None)
    if position is None:
        raise CandidateError(f'未找到候选 {record.get("id")!r}；修订只针对已登记的候选。')
    current = ledger['candidates'][position]
    if current['status'] != 'proposed':
        raise CandidateError(f'候选 {current["id"]} 已是“{STATUSES[current["status"]]}”：进入检验之后的改动'
                             '用新标识及 supersedes 登记，保留原记录。')
    validate_candidate(record)
    before = {key: value for key, value in current.items() if key not in RUNTIME_KEYS}
    revisions = list(current.get('revisions', [])) + [{'at': _now(), 'note': note, 'before': before}]
    replacement = dict({'parents': []}, **record, status='proposed', history=[],
                       added_at=current.get('added_at', ''), revisions=revisions)
    candidates = ledger['candidates'][:position] + [replacement] + ledger['candidates'][position + 1:]
    check_lineage(ledger['base'], candidates)
    ledger['candidates'] = candidates
    save_ledger(ledger_path, ledger, expected)
    return {'id': replacement['id'], 'revisions': len(revisions), 'scope': SCOPE}


def advance(ledger_path: Path, identifier: str, target: str, note: str = '',
            evidence_path: Path | None = None, strength: str | None = None) -> dict:
    require_external_output(ledger_path, __file__)
    if not ledger_path.exists():
        raise CandidateError('候选账本不存在。')
    expected = ledger_path.read_bytes()
    ledger = load_ledger(ledger_path)
    candidate = next((item for item in ledger['candidates'] if item['id'] == identifier), None)
    if candidate is None:
        raise CandidateError(f'未找到候选 {identifier}。')
    where = f'候选 {identifier}'
    if target not in STATUSES:
        raise CandidateError('目标状态须为 ' + '、'.join(STATUSES) + ' 之一。')
    current = candidate['status']
    identity = candidate['identity']
    if target not in TRANSITIONS[current]:
        if not TRANSITIONS[current]:
            raise CandidateError(f'{where}已{STATUSES[current]}，是终态；重新提出时用新标识及 supersedes。')
        raise CandidateError(f'{where}不能从“{STATUSES[current]}”直接到“{STATUSES[target]}”；'
                             '候选依次经过提出、检验中、得到支持的候选，不能跳过检验。')
    if identity in HANDED_ON and target != 'retired':
        raise CandidateError(f'{where}是{IDENTITIES[identity]}，只能在交给相应路线或不再使用时退役；'
                             '它的回答或比较不在本账本里判定。')
    if not isinstance(note, str) or len(note) > MAX_TEXT:
        raise CandidateError(f'note须为不超过{MAX_TEXT}字符的文本。')
    if target in {'rejected', 'retired'} or (current == 'supported' and target == 'testing'):
        if is_blank(note):
            raise CandidateError(f'{where}: 拒绝、退役或重新打开检验须写明理由 --note。')
    evidence = []
    if evidence_path is not None:
        evidence = validate_evidence(read_json(evidence_path), where)
    if target == 'supported' and not any(entry['direction'] == 'supports' for entry in evidence):
        raise CandidateError(f'{where}: 标为得到支持的候选须随本次提交至少一条支持性证据 --evidence；'
                             '续推、复述和模型一致不是证据。')
    step = {'from': current, 'to': target, 'at': _now()}
    if not is_blank(note):
        step['note'] = note
    if evidence:
        step['evidence'] = evidence
    if strength is not None:
        if identity not in GRADED:
            raise CandidateError(f'{where}: 强度只用于经验候选、变量候选和启发性类比。')
        if strength not in STRENGTHS:
            raise CandidateError('strength须为 ' + '、'.join(STRENGTHS) + ' 之一。')
        if strength == 'diagnostic' and target != 'supported':
            raise CandidateError(f'{where}: 诊断级须有外部可观察材料，只能随“得到支持的候选”一并登记。')
        step['strength'] = strength
        candidate['strength'] = strength
    elif candidate.get('strength') == 'diagnostic':
        candidate['strength'] = 'exploration'
        step['strength'] = 'exploration'
    candidate['history'].append(step)
    candidate['status'] = target
    save_ledger(ledger_path, ledger, expected)
    return {'id': identifier, 'from': current, 'to': target, 'scope': SCOPE}


def index_of(ledger: dict) -> dict:
    return {item['id']: item for item in ledger['base'] + ledger['candidates']}


def generations(ledger: dict) -> dict:
    by_id = {item['id']: item for item in ledger['candidates']}
    depth = {}
    for identifier in lineage_order(ledger['candidates']):
        depth[identifier] = 1 + max((depth[parent] for parent in parents_of(by_id[identifier]) if parent in by_id),
                                    default=0)
    return depth


def ancestors(ledger: dict, identifier: str) -> list:
    """All ancestors of one candidate, nearest first, each listed once."""
    return ancestors_in(index_of(ledger), identifier)


def inherited_conditions(ledger: dict, identifier: str) -> list:
    """What the candidate still depends on: unsupported ancestor candidates and non-settled starting points."""
    by_id = index_of(ledger)
    base_ids = {item['id'] for item in ledger['base']}
    result = []
    for ancestor in ancestors_in(by_id, identifier):
        item = by_id[ancestor]
        if ancestor in base_ids:
            if item['kind'] in {'conditional', 'assumption', 'stated'}:
                result.append({'id': ancestor, 'as': BASE_KINDS[item['kind']],
                               'conditions': item.get('conditions', [])})
        elif item['status'] != 'supported':
            result.append({'id': ancestor, 'as': IDENTITIES[item['identity']],
                           'status': STATUSES[item['status']]})
    return result


def lineage(ledger: dict, identifier: str) -> dict:
    by_id = index_of(ledger)
    base_ids = {item['id'] for item in ledger['base']}
    if identifier not in by_id or identifier in base_ids:
        raise CandidateError(f'未找到候选 {identifier}。')
    rows = []
    for ancestor in ancestors_in(by_id, identifier):
        item = by_id[ancestor]
        if ancestor in base_ids:
            rows.append({'id': ancestor, 'role': 'base', 'kind': item['kind'], 'statement': item['statement']})
        else:
            rows.append({'id': ancestor, 'role': 'candidate', 'identity': item['identity'],
                         'status': item['status'], 'move': item['move'], 'statement': item['statement']})
    return {'id': identifier, 'generation': generations(ledger)[identifier],
            'parents': parents_of(by_id[identifier]), 'ancestors': rows,
            'conditional_on': inherited_conditions(ledger, identifier), 'scope': SCOPE}


def known_sections() -> set:
    path = Path(__file__).resolve().with_name('read_source.py')
    spec = importlib.util.spec_from_file_location('xikari_candidates_read_source', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    lines = module.SOURCE.read_text(encoding='utf-8-sig').splitlines()
    sections, _ = module.build_index(lines)
    return set(sections)


def check_ledger(ledger: dict, sections: set) -> dict:
    """Report unresolved references and things an author should look at again. Never scores a candidate."""
    errors, warnings = [], []
    by_id = index_of(ledger)
    depth = generations(ledger)
    superseded = {}
    for item in ledger['candidates']:
        if 'supersedes' in item:
            superseded.setdefault(item['supersedes'], []).append(item['id'])
    for item in ledger['base']:
        if item['kind'] == 'definition' and item.get('section') not in sections:
            errors.append(f'{item["id"]}: 理论小节 {item.get("section")} 在原文索引中不存在')
    for item in ledger['candidates']:
        identifier = item['id']
        for entry in item.get('theory', []):
            if entry['section'] not in sections:
                errors.append(f'{identifier}: 理论小节 {entry["section"]} 在原文索引中不存在')
        active = item['status'] in ACTIVE
        if item['novelty']['level'] == 'restated' and active:
            warnings.append(f'{identifier}: 标为重述；重述并入原处，不作为新候选交付')
        if item['move'] == 'association' and active:
            warnings.append(f'{identifier}: 是没有起点的联想，交付时单列，不称推出')
        if item['identity'] != 'question' and not item.get('changes') and active:
            warnings.append(f'{identifier}: 未说明成立后改变什么；什么都不改变的不列为主要结果')
        if item['move'] in TRANSFORM_MOVES and not item['record'].get('lost'):
            warnings.append(f'{identifier}: 未记录丢失项；确认是核对后没有任务相关丢失，还是尚未核对')
        if depth[identifier] > MAX_GENERATION and active:
            warnings.append(f'{identifier}: 已是第 {depth[identifier]} 代；到第三代应停下，写清还能说什么')
        if item.get('sensitive') and active:
            warnings.append(f'{identifier}: 涉及隐私、健康、安全、法律地位或低权力位置；'
                            '信息价值盖不过风险时保留未知')
        if 'post_outcome' in item:
            warnings.append(f'{identifier}: 结果后提出，可以改进下一轮，不能回头支撑原判断')
        if identifier in superseded and active:
            warnings.append(f'{identifier}: 已被 {"、".join(superseded[identifier])} 取代但仍在役，'
                            '须退役或说明并存理由')
        if active:
            lineage_ids = ancestors_in(by_id, identifier)
            dead = [ancestor for ancestor in lineage_ids
                    if by_id[ancestor].get('status') in {'rejected', 'retired'}]
            if dead:
                warnings.append(f'{identifier}: 父项 {"、".join(dead)} 已拒绝或退役，依赖它的候选须复核')
            added = item.get('added_at', '')
            changed = [parent for parent in parents_of(item)
                       if any(entry['at'] > added for entry in by_id[parent].get('revisions', []))]
            if changed:
                warnings.append(f'{identifier}: 父项 {"、".join(changed)} 在它登记之后修订过，须复核')
        if item['status'] == 'supported':
            pending = [entry['id'] for entry in inherited_conditions(ledger, identifier)]
            if pending:
                warnings.append(f'{identifier}: 虽得到支持，仍条件于 {"、".join(pending)}')
    counts = {
        'base': len(ledger['base']),
        'candidates': len(ledger['candidates']),
        'by_identity': {key: sum(item['identity'] == key for item in ledger['candidates'])
                        for key in IDENTITIES if any(item['identity'] == key for item in ledger['candidates'])},
        'by_status': {key: sum(item['status'] == key for item in ledger['candidates'])
                      for key in STATUSES if any(item['status'] == key for item in ledger['candidates'])},
    }
    return {'ok': not errors, 'counts': counts, 'errors': errors, 'warnings': warnings, 'scope': SCOPE}


def section_label(section: str) -> str:
    return ('附录 ' if section[:1].isalpha() else '§') + section


def cell(text) -> str:
    return str(text).replace('\\', '\\\\').replace('|', '\\|').replace('\r', ' ').replace('\n', ' ').strip()


def bullets(lines: list, title: str, values) -> None:
    if not values:
        return
    lines.append(f'- **{title}：**')
    for value in values:
        lines.append(f'  - {value}')


def describe_novelty(novelty: dict) -> str:
    parts = [NOVELTY[novelty['level']]]
    if not is_blank(novelty.get('scope', '')):
        parts.append(f"查过的范围：{novelty['scope']}")
    return '；'.join(parts)


def trail_of(ledger: dict, identifier: str) -> str:
    """One line per candidate: its own parents, then the starting points everything above it rests on."""
    by_id = index_of(ledger)
    base_order = [item['id'] for item in ledger['base']]
    parents = parents_of(by_id[identifier])
    if not parents:
        return f'{identifier}（没有起点）'
    line = f'{identifier} ← ' + ' ＋ '.join(parents)
    if any(parent not in base_order for parent in parents):
        reached = set(ancestors_in(by_id, identifier))
        roots = [root for root in base_order if root in reached]
        line += '；最终起点：' + ('、'.join(roots) if roots else '无（上游是联想）')
    return line


def render_markdown(ledger: dict) -> str:
    depth = generations(ledger)
    derived = [item for item in ledger['candidates'] if item['move'] != 'association']
    loose = [item for item in ledger['candidates'] if item['move'] == 'association']
    lines = [MARK, '', '# 候选账本', '']
    if not is_blank(ledger['question']):
        lines += [f"**问题：** {ledger['question']}", '']
    lines += [NOTICE, '', '## 起点', '']
    if ledger['base']:
        lines += ['| 编号 | 身份 | 陈述 | 出处或条件 |', '| --- | --- | --- | --- |']
        for item in ledger['base']:
            basis = [item.get('source', '').strip(),
                     section_label(item['section']) if not is_blank(item.get('section', '')) else '',
                     '；'.join(item.get('conditions', []))]
            lines.append(f"| {cell(item['id'])} | {BASE_KINDS[item['kind']]} | {cell(item['statement'])} | "
                         f"{cell('；'.join(part for part in basis if part)) or '—'} |")
    else:
        lines.append('（尚未登记起点。）')
    lines += ['', '## 候选一览', '']
    if derived:
        lines += ['| 编号 | 代次 | 身份 | 走法 | 父项 | 新在哪里 | 状态 |', '| --- | --- | --- | --- | --- | --- | --- |']
        for item in sorted(derived, key=lambda entry: depth[entry['id']]):
            lines.append(f"| {cell(item['id'])} | {depth[item['id']]} | {IDENTITIES[item['identity']]} | "
                         f"{MOVES[item['move']]} | {cell('、'.join(parents_of(item)))} | "
                         f"{NOVELTY[item['novelty']['level']]} | {STATUSES[item['status']]} |")
    else:
        lines.append('（尚未登记有起点的候选。）')
    lines.append('')

    def detail(item):
        identifier = item['id']
        lines.append(f'### {identifier}')
        lines.append('')
        lines.append(item['statement'])
        lines.append('')
        head = f"- **身份：** {IDENTITIES[item['identity']]}　**走法：** {MOVES[item['move']]}"
        if parents_of(item):
            head += f"　**父项：** {'、'.join(parents_of(item))}　**代次：** {depth[identifier]}"
        lines.append(head)
        lines.append(f"- **当前状态：** {STATUSES[item['status']]}"
                     + (f"　**强度：** {STRENGTHS[item['strength']]}" if 'strength' in item else ''))
        conditions = inherited_conditions(ledger, identifier)
        if conditions:
            lines.append('- **条件于：** ' + '；'.join(
                f"{entry['id']}（{entry['as']}" + (f"，{entry['status']}" if 'status' in entry else '') + '）'
                for entry in conditions))
        if not is_blank(item.get('model', '')):
            lines.append(f"- **模型与前提：** {item['model']}")
        if item.get('derivation'):
            lines.append('- **推导：**')
            for number, step in enumerate(item['derivation'], 1):
                lines.append(f'  {number}. {step}')
        for key in RECORD_KEYS:
            bullets(lines, RECORD_LABELS[key], item.get('record', {}).get(key))
        if 'analogy' in item:
            lines.append('- **类比：**')
            for key in ('source_domain', 'target_domain', 'shared', 'differences',
                        'not_transferable', 'mapping', 'test'):
                value = item['analogy'][key]
                lines.append(f"  - {ANALOGY_LABELS[key]}：{value if isinstance(value, str) else '；'.join(value)}")
        if not is_blank(item.get('residual', '')):
            lines.append(f"- **来源残差：** {item['residual']}")
        lines.append(f"- **新在哪里：** {describe_novelty(item['novelty'])}")
        bullets(lines, '已有说法或所忆内容', item['novelty'].get('prior'))
        bullets(lines, '可观察含义', item.get('observables'))
        if item.get('rivals'):
            lines.append('- **竞争项与区分观察：**')
            for rival in item['rivals']:
                lines.append(f"  - {rival['statement']}——区分观察：{rival['distinguishing']}")
        if not is_blank(item.get('minimal_test', '')):
            lines.append(f"- **最小检验：** {item['minimal_test']}")
        if not is_blank(item.get('risk', '')):
            lines.append(f"- **隐私与风险：** {item['risk']}")
        if not is_blank(item.get('necessity', '')):
            lines.append(f"- **取得的必要性：** {item['necessity']}")
        bullets(lines, '禁止用途', item.get('forbidden_uses'))
        bullets(lines, '升级条件', item.get('upgrade_conditions'))
        bullets(lines, '否决条件', item.get('reject_conditions'))
        bullets(lines, '成立后改变什么', item.get('changes'))
        if item.get('theory'):
            lines.append('- **所依据的原文小节：** '
                         + '、'.join(section_label(entry['section']) for entry in item['theory']))
        if 'supersedes' in item:
            lines.append(f"- **取代：** {item['supersedes']}")
        if 'post_outcome' in item:
            lines.append(f"- **结果后提出：** {item['post_outcome']}。它可以改进下一轮，不能回头支撑原判断。")
        if item.get('revisions'):
            lines.append('- **修订：** 修订前的内容保留在账本文件里。')
            for entry in item['revisions']:
                lines.append(f"  - {entry['at']}　{entry['note']}")
        if item['history']:
            lines.append('- **经过：**')
            for step in item['history']:
                text = f"  - {step['at']}　{STATUSES[step['from']]} → {STATUSES[step['to']]}"
                if step.get('note'):
                    text += f"：{step['note']}"
                lines.append(text)
                for entry in step.get('evidence', []):
                    extra = f"，{entry['note']}" if entry.get('note') else ''
                    lines.append(f"    - 证据（{DIRECTIONS[entry['direction']]}）：{entry['ref']}{extra}")
        lines.append('')

    if derived:
        lines += ['## 逐条', '']
        for item in sorted(derived, key=lambda entry: depth[entry['id']]):
            detail(item)
    if loose:
        lines += ['## 联想', '', '以下各项没有起点，不称推出。', '']
        for item in loose:
            detail(item)
    if derived:
        lines += ['## 谱系', '']
        for item in sorted(derived, key=lambda entry: depth[entry['id']]):
            lines.append(f"- {trail_of(ledger, item['id'])}")
        lines.append('')
    lines += [f'> {SCOPE}', '']
    return '\n'.join(lines)


def owned_output(path: Path) -> bool:
    try:
        return MARK in path.read_text(encoding='utf-8')[:2048]
    except (OSError, UnicodeError):
        return False


def write_document(text: str, output: Path, force: bool = False) -> Path:
    require_external_output(output, __file__)
    output = Path(output)
    if output.exists() and (not force or not owned_output(output)):
        raise CandidateError(f'输出已存在且不属于本工具产物: {output}；使用新路径，或仅对本工具产物使用--force。')
    output.parent.mkdir(parents=True, exist_ok=True)
    lock = output.with_name(output.name + '.lock')
    require_external_output(lock, __file__)
    temporary = None
    owns_lock = False
    try:
        fd, name = tempfile.mkstemp(prefix='.candidates-', suffix='.tmp', dir=output.parent)
        temporary = Path(name)
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise CandidateError(f'输出位置有其他写入者或遗留锁: {lock}；未自动覆盖。') from error
        owns_lock = True
        os.close(descriptor)
        if output.exists() and (not force or not owned_output(output)):
            raise CandidateError(f'输出在取得写锁前已被其他写入者创建或改动: {output}；本次未覆盖。')
        os.replace(temporary, output)
        temporary = None
        return output
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if owns_lock:
            lock.unlink(missing_ok=True)


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--ledger', type=Path, required=True,
                        help='用户任务目录中的候选账本；不写入技能目录或全局记忆')
    commands = parser.add_subparsers(dest='command', required=True)
    add = commands.add_parser('add', help='登记一批起点与候选；新候选一律从“提出”开始')
    add.add_argument('--record', type=Path, required=True, help='含 base 与 candidates 的记录 JSON')
    change = commands.add_parser('revise', help='修订一条仍处在“提出”的候选，旧内容与理由留在账本里')
    change.add_argument('--record', type=Path, required=True, help='单条候选的完整记录 JSON，id 与原候选相同')
    change.add_argument('--note', required=True, help='为什么修订，例如自我攻击后补上的竞争项')
    move = commands.add_parser('advance', help='按顺序改变一条候选的状态，旧状态保留在经过里')
    move.add_argument('--id', required=True)
    move.add_argument('--to', required=True, choices=sorted(STATUSES))
    move.add_argument('--note', default='', help='理由；拒绝、退役或重新打开检验时必填')
    move.add_argument('--evidence', type=Path, help='证据列表 JSON；标为得到支持的候选时必填')
    move.add_argument('--strength', choices=sorted(STRENGTHS), help='调整强度；诊断级只能随得到支持一并登记')
    commands.add_parser('list', help='只读列出候选的身份、走法、代次与状态')
    show = commands.add_parser('show', help='只读显示一项起点或候选的全部字段')
    show.add_argument('id')
    trace = commands.add_parser('lineage', help='只读显示一条候选的全部来路与仍依赖的条件')
    trace.add_argument('id')
    commands.add_parser('check', help='只读核对谱系与引用，并提示需要再看的地方')
    render = commands.add_parser('render', help='生成可读的候选账本')
    render.add_argument('--output', '-o', type=Path, required=True, help='安装目录之外的输出文件')
    render.add_argument('--force', action='store_true', help='仅覆盖本工具先前生成的账本')
    args = parser.parse_args(argv)
    try:
        if args.command == 'add':
            result = add_records(args.ledger, args.record)
        elif args.command == 'revise':
            result = revise(args.ledger, args.record, args.note)
        elif args.command == 'advance':
            result = advance(args.ledger, args.id, args.to, args.note, args.evidence, args.strength)
        else:
            if not args.ledger.exists():
                raise CandidateError('候选账本不存在。')
            ledger = load_ledger(args.ledger)
            if args.command == 'list':
                depth = generations(ledger)
                result = {'question': ledger['question'], 'base': len(ledger['base']),
                          'candidates': [{'id': item['id'], 'identity': item['identity'], 'move': item['move'],
                                          'generation': depth[item['id']], 'parents': parents_of(item),
                                          'novelty': item['novelty']['level'], 'status': item['status']}
                                         for item in ledger['candidates']]}
            elif args.command == 'show':
                result = index_of(ledger).get(args.id)
                if result is None:
                    raise CandidateError('未找到该标识。')
            elif args.command == 'lineage':
                result = lineage(ledger, args.id)
            elif args.command == 'check':
                result = check_ledger(ledger, known_sections())
            else:
                if args.ledger.resolve() == args.output.resolve():
                    raise CandidateError('输出路径与账本是同一个文件；为避免覆盖账本，请改用其他路径。')
                target = write_document(render_markdown(ledger), args.output, args.force)
                result = {'output': str(target.resolve()), 'scope': SCOPE}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if isinstance(result, dict) and result.get('ok') is False else 0
    except (OSError, UnicodeError, CandidateError, ValueError, TypeError, RecursionError) as error:
        print(f'候选账本处理失败：{error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
