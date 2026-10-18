"""Read isolated evaluation logs and compare paired reading costs."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys


TOKEN_FIELDS = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
                'output_tokens', 'reasoning_output_tokens', 'total_tokens')
COST_FIELDS = ('uncached_input_tokens', 'cached_input_tokens', 'output_tokens',
               'turn_count', 'wall_seconds')
CONTROL_FIELDS = ('input_sha256', 'packet_sha256', 'environment_sha256', 'context_prefix_sha256')


def _one(values):
    values = set(values)
    return next(iter(values)) if len(values) == 1 and None not in values else None


def extract_costs(rows):
    """Use the final cumulative counters once; missing measurements stay null."""
    sessions, hosts, contexts, starts, completions = [], [], [], {}, {}
    last, snapshots, activities = {}, [], []
    parent_ids, spawn_call_ids = set(), set()
    previous = {}
    for row in rows:
        payload = row.get('payload', {})
        if row.get('type') == 'session_meta':
            sessions.append(payload.get('id') or payload.get('session_id'))
            hosts.append(payload.get('cli_version'))
            if payload.get('parent_thread_id'):
                parent_ids.add(payload['parent_thread_id'])
            source = payload.get('source')
            if isinstance(source, dict):
                parent = source.get('subagent', {}).get('thread_spawn', {}).get('parent_thread_id')
                if parent:
                    parent_ids.add(parent)
        elif row.get('type') == 'response_item' and payload.get('type') == 'function_call':
            is_spawn = (payload.get('name') == 'spawn_agent' and payload.get('namespace') == 'collaboration'
                        or payload.get('name') == 'collaboration.spawn_agent')
            if is_spawn and payload.get('call_id'):
                spawn_call_ids.add(payload['call_id'])
        elif row.get('type') == 'turn_context':
            contexts.append(payload)
        elif row.get('type') == 'event_msg':
            kind = payload.get('type')
            if kind == 'task_started' and payload.get('turn_id'):
                starts[payload['turn_id']] = payload
            elif kind == 'task_complete' and payload.get('turn_id'):
                completions[payload['turn_id']] = payload
            elif kind == 'item_completed':
                item = payload.get('item', {})
                if item.get('type') == 'SubAgentActivity' and item.get('agent_thread_id'):
                    activities.append(item)
            elif kind == 'token_count':
                usage = (payload.get('info') or {}).get('total_token_usage')
                if not isinstance(usage, dict):
                    continue
                last = {key: usage.get(key) for key in TOKEN_FIELDS}
                for key, value in last.items():
                    if value is not None and (type(value) is not int or value < 0):
                        raise ValueError(f'{key} must be a nonnegative integer or null')
                    if value is not None and previous.get(key) is not None and value < previous[key]:
                        raise ValueError(f'cumulative {key} decreased; reconcile the source log')
                    if value is not None:
                        previous[key] = value
                total_input, cached = last.get('input_tokens'), last.get('cached_input_tokens')
                if total_input is not None and cached is not None and cached > total_input:
                    raise ValueError('cached_input_tokens exceeds input_tokens')
                output, total = last.get('output_tokens'), last.get('total_tokens')
                if all(value is not None for value in (total_input, output, total)) and total != total_input + output:
                    raise ValueError('total_tokens differs from input_tokens + output_tokens')
                signature = tuple(last.get(key) for key in TOKEN_FIELDS)
                if any(value for value in signature) and (not snapshots or signature != snapshots[-1]):
                    snapshots.append(signature)
    if len(set(sessions)) > 1:
        raise ValueError('multiple session IDs in one log')
    parent_id = _one(parent_ids)
    agent_ids = {item['agent_thread_id'] for item in activities}
    spawned_ids = {item['agent_thread_id'] for item in activities if item.get('id') in spawn_call_ids}
    child_ids = spawned_ids - {parent_id}
    parent_activity_ids = {parent_id} & agent_ids if parent_id not in spawned_ids else set()
    unresolved_ids = agent_ids - child_ids - parent_activity_ids
    turn_ids = set(starts) | {ctx['turn_id'] for ctx in contexts if ctx.get('turn_id')}
    completed = bool(turn_ids) and turn_ids <= set(completions)
    durations = [completions[turn_id].get('duration_ms') for turn_id in turn_ids] if completed else []
    wall_seconds = (sum(durations) / 1000
                    if durations and all(type(value) in (int, float) and value >= 0 for value in durations)
                    else None)
    total_input, cached = last.get('input_tokens'), last.get('cached_input_tokens')
    return {
        **{key: last.get(key) for key in TOKEN_FIELDS},
        'uncached_input_tokens': total_input - cached if total_input is not None and cached is not None else None,
        'session_id': _one(sessions), 'host_version': _one(hosts),
        'actual_model': _one(ctx.get('model') for ctx in contexts),
        'actual_effort': _one(ctx.get('effort') for ctx in contexts),
        'turn_count': len(turn_ids) if turn_ids else None,
        'usage_update_count': len(snapshots) if last else None,
        'usage_update_count_basis': 'distinct_nonzero_cumulative_usage_updates',
        'wall_seconds': wall_seconds, 'completed': completed,
        'parent_session_id': parent_id,
        'parent_activity_session_ids': sorted(parent_activity_ids),
        'child_session_ids': sorted(child_ids),
        'unresolved_agent_session_ids': sorted(unresolved_ids),
    }


def read_costs(path):
    path = Path(path)
    raw = path.read_bytes()
    rows = []
    for number, line in enumerate(raw.decode('utf-8-sig').splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f'{path}:{number}: {error.msg}') from error
    return {**extract_costs(rows), 'log_path': str(path.resolve()),
            'log_sha256': hashlib.sha256(raw).hexdigest()}


def compare_pairs(runs, quality=None, threshold_confirmed=False):
    """Retain incomplete or excluded pairs and keep unreviewed quality unknown."""
    groups = defaultdict(dict)
    session_counts = Counter(run.get('cost', {}).get('session_id') for run in runs)
    for run in runs:
        key = (run['question_id'], run.get('repetition', 1))
        mode = run['reading_mode']
        if mode not in ('full', 'layered'):
            raise ValueError(f'unknown reading_mode: {mode}')
        if mode in groups[key]:
            raise ValueError(f'duplicate {mode} run for {key}')
        groups[key][mode] = run
    result = []
    for (question_id, repetition), group in sorted(groups.items()):
        full, layered = group.get('full'), group.get('layered')
        item = {'question_id': question_id, 'question_type': (full or layered).get('question_type'),
                'repetition': repetition, 'full': full, 'layered': layered,
                'layered_over_full': {key: None for key in COST_FIELDS},
                'quality_verdict': None, 'replacement_supported': False, 'exclusions': []}
        if full is None or layered is None:
            item['status'] = 'incomplete'
            result.append(item)
            continue
        for field in CONTROL_FIELDS:
            if full.get(field) is None or full.get(field) != layered.get(field):
                item['exclusions'].append(field)
        first, second = full['cost'], layered['cost']
        for field in ('actual_model', 'actual_effort', 'host_version'):
            if first.get(field) is None or first.get(field) != second.get(field):
                item['exclusions'].append(field)
        if any(not cost.get('session_id') or session_counts[cost['session_id']] != 1 for cost in (first, second)):
            item['exclusions'].append('fresh_session')
        if first.get('turn_count') != 1 or second.get('turn_count') != 1:
            item['exclusions'].append('single_turn')
        if not first.get('completed') or not second.get('completed'):
            item['exclusions'].append('completed')
        if first.get('child_session_ids') or second.get('child_session_ids'):
            item['exclusions'].append('subagents')
        if first.get('unresolved_agent_session_ids') or second.get('unresolved_agent_session_ids'):
            item['exclusions'].append('unresolved_agent_activity')
        if full.get('reading_verified') is not True or layered.get('reading_verified') is not True:
            item['exclusions'].append('reading_verified')
        if any(cost.get(field) is None for cost in (first, second) for field in COST_FIELDS):
            item['exclusions'].append('cost_measurements')
        for field in COST_FIELDS:
            a, b = first.get(field), second.get(field)
            if a is not None and b is not None and a > 0:
                item['layered_over_full'][field] = b / a
        item['status'] = 'excluded' if item['exclusions'] else 'cost_only'
        reviewed = (quality or {}).get(f'{question_id}:{repetition}')
        if reviewed is not None:
            item['quality'] = reviewed
            known = (type(reviewed.get('hard_points_missed')) is int
                     and type(reviewed.get('new_errors')) is int
                     and reviewed.get('blind_preference') in ('full', 'tie', 'layered')
                     and bool(reviewed.get('reviewer')))
            acceptable = (known and reviewed['hard_points_missed'] == 0
                          and reviewed['new_errors'] == 0
                          and reviewed['blind_preference'] in ('tie', 'layered'))
            if known:
                item['quality_verdict'] = 'noninferior_on_this_pair' if acceptable else 'inferiority_or_error'
            item['replacement_supported'] = bool(acceptable and threshold_confirmed and not item['exclusions'])
            if not item['exclusions'] and known:
                item['status'] = 'reviewed' if threshold_confirmed else 'threshold_unconfirmed'
        result.append(item)
    return result


def markdown_table(pairs):
    lines = ['| 题目 | 阅读方式 | 未缓存输入 | 缓存输入 | 输出 | 轮数 | 耗时秒 | 质量 | 状态 |',
             '| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |']
    for pair in pairs:
        for mode in ('full', 'layered'):
            run = pair[mode]
            cost = run['cost'] if run else {}
            cells = [pair['question_id'], mode, *[cost.get(field) for field in COST_FIELDS],
                     pair.get('quality_verdict'), pair['status']]
            lines.append('| ' + ' | '.join('null' if value is None else str(value).replace('|', '\\|') for value in cells) + ' |')
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    extract = commands.add_parser('extract')
    extract.add_argument('log')
    compare = commands.add_parser('compare')
    compare.add_argument('manifest')
    compare.add_argument('--format', choices=('json', 'markdown'), default='json')
    args = parser.parse_args(argv)
    if args.command == 'extract':
        output = read_costs(args.log)
    else:
        path = Path(args.manifest)
        manifest = json.loads(path.read_text(encoding='utf-8-sig'))
        runs = manifest['runs']
        for run in runs:
            if run.get('log_path'):
                log = Path(run['log_path'])
                run['cost'] = read_costs(log if log.is_absolute() else path.parent / log)
        output = compare_pairs(runs, manifest.get('quality'), manifest.get('threshold_confirmed') is True)
        if args.format == 'markdown':
            print(markdown_table(output), end='')
            return 0
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
