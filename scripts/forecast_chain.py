"""Track registry writes with a hash chain and an optional external head anchor."""

from __future__ import annotations

import hashlib
import json
import math
import re


FORMAT = 'xikari-forecasts-1'
ENTRY_FIELDS = {'seq', 'kind', 'id', 'record_sha256', 'prev'}
ARRAYS = {'forecast': 'forecasts', 'resolution': 'resolutions'}


class ChainError(ValueError):
    """The registry chain is malformed or does not match its frozen records."""


def _canonical(value):
    try:
        _json_value(value)
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        raise ChainError('链数据须为有限数值组成的有效JSON') from error


def _json_value(value):
    if value is None or type(value) in {str, bool, int}:
        return
    if type(value) is float and math.isfinite(value):
        return
    if isinstance(value, list):
        for item in value:
            _json_value(item)
        return
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        for item in value.values():
            _json_value(item)
        return
    raise ChainError('链数据须为JSON类型，不能含非文本键、NaN或Infinity')


def _hash(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _identity(kind, record):
    if not isinstance(record, dict):
        raise ChainError('冻结记录须为JSON对象')
    field = 'id' if kind == 'forecast' else 'forecast_id'
    identifier = record.get(field)
    if not isinstance(identifier, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}', identifier):
        raise ChainError(f'冻结记录{field}须为合法前瞻标识')
    if kind == 'forecast':
        return identifier
    at = record.get('resolved_at')
    if not isinstance(at, str) or not at.strip():
        raise ChainError('结果记录resolved_at须为非空文本')
    return identifier + '@' + at


def _sha(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def _records(registry):
    if not isinstance(registry, dict):
        raise ChainError('注册表须为JSON对象')
    version = registry.get('schema_version')
    if type(version) is not int or version not in {1, 2}:
        raise ChainError('注册表schema_version须为整数1或2')
    expected = {'format', 'schema_version', 'forecasts', 'resolutions'}
    if version == 2:
        expected |= {'chain', 'legacy_prefix'}
    if set(registry) != expected or registry.get('format') != FORMAT:
        raise ChainError('注册表含缺失、未知字段或无效format')
    records = {}
    for kind, array in ARRAYS.items():
        if not isinstance(registry[array], list):
            raise ChainError(f'{array}须为记录列表')
        records[kind] = {}
        for record in registry[array]:
            identifier = _identity(kind, record)
            if identifier in records[kind]:
                raise ChainError(f'{kind}记录标识重复：{identifier}')
            checksum = record.get('record_sha256')
            if not _sha(checksum) or checksum != _hash({k: v for k, v in record.items() if k != 'record_sha256'}):
                raise ChainError('冻结记录散列不一致；不得改写已冻结内容')
            if kind == 'resolution' and record['forecast_id'] not in records['forecast']:
                raise ChainError('结果记录引用不存在的前瞻')
            records[kind][identifier] = record
    return records


def _entry(kind, record, sequence, previous):
    return {'seq': sequence, 'kind': kind, 'id': _identity(kind, record),
            'record_sha256': record['record_sha256'], 'prev': previous}


def validate(registry, expect_head=None):
    """Return a valid chain head, or None for an unchained legacy registry."""
    records = _records(registry)
    if registry['schema_version'] == 1:
        if expect_head is not None:
            raise ChainError('schema_version 1没有chain，无法核对expect_head；须先明确迁移补链')
        return None
    if expect_head is not None and not _sha(expect_head):
        raise ChainError('expect_head须为小写SHA-256链头')
    chain = registry['chain']
    prefix = registry['legacy_prefix']
    if not isinstance(chain, list) or type(prefix) is not int or not 0 <= prefix <= len(chain):
        raise ChainError('chain须为列表，legacy_prefix须为链长范围内的非负整数')
    previous = None
    offsets = {'forecast': 0, 'resolution': 0}
    seen_forecasts = set()
    legacy_resolution_seen = False
    for sequence, entry in enumerate(chain, 1):
        if not isinstance(entry, dict) or set(entry) != ENTRY_FIELDS:
            raise ChainError('chain项须恰含seq、kind、id、record_sha256、prev')
        if type(entry['seq']) is not int or entry['seq'] != sequence or entry['prev'] != previous:
            raise ChainError('注册表chain的字段、顺序或前项散列不一致')
        kind = entry['kind']
        if not isinstance(kind, str) or kind not in ARRAYS:
            raise ChainError('chain.kind须为forecast或resolution')
        ordered = registry[ARRAYS[kind]]
        offset = offsets[kind]
        if offset >= len(ordered):
            raise ChainError('chain含重复项或没有对应的冻结记录')
        record = ordered[offset]
        identifier = _identity(kind, record)
        if entry['id'] != identifier or entry['record_sha256'] != record['record_sha256']:
            raise ChainError('chain与冻结记录的标识、散列或相对顺序不一致')
        if kind == 'resolution' and record['forecast_id'] not in seen_forecasts:
            raise ChainError('结果链项必须晚于对应前瞻')
        if sequence <= prefix:
            if kind == 'forecast' and legacy_resolution_seen:
                raise ChainError('legacy_prefix须按前瞻数组后结果数组的顺序补链')
            legacy_resolution_seen |= kind == 'resolution'
        if kind == 'forecast':
            seen_forecasts.add(identifier)
        offsets[kind] += 1
        previous = _hash(entry)
    if any(offsets[kind] != len(records[kind]) for kind in ARRAYS):
        raise ChainError('冻结记录未被chain一一覆盖')
    if expect_head is not None and previous != expect_head:
        raise ChainError('实际链头与外部保存的expect_head不一致')
    return previous


def chain_head(registry):
    """Compute the head after validating the complete registry chain."""
    return validate(registry)


def append_entry(registry, kind, record):
    """Link one frozen record already appended to its corresponding array.

    Call upgrade before appending the first new record. Only the chain is
    changed here; the caller remains responsible for atomic file persistence.
    """
    if not isinstance(kind, str) or kind not in ARRAYS:
        raise ChainError('chain.kind须为forecast或resolution')
    _records(registry)
    if registry['schema_version'] != 2:
        raise ChainError('追加新记录之前须先upgrade旧注册表')
    array = ARRAYS[kind]
    if not registry[array] or _canonical(registry[array][-1]) != _canonical(record):
        raise ChainError('待补链记录须为对应数组的唯一新增末项')
    prior = {**registry, array: registry[array][:-1]}
    previous = validate(prior)
    entry = _entry(kind, record, len(registry['chain']) + 1, previous)
    chain = [*registry['chain'], entry]
    head = validate({**registry, 'chain': chain})
    registry['chain'] = chain
    return head


def upgrade(registry):
    """Migrate arrays in their stored order without changing existing records.

    The legacy prefix lists forecasts first, then resolutions. It does not
    reconstruct historical interleaving that schema version 1 never recorded.
    """
    validate(registry)
    if registry['schema_version'] == 2:
        return
    chain, previous = [], None
    for kind, array in ARRAYS.items():
        for record in registry[array]:
            entry = _entry(kind, record, len(chain) + 1, previous)
            chain.append(entry)
            previous = _hash(entry)
    registry.update(schema_version=2, chain=chain, legacy_prefix=len(chain))
