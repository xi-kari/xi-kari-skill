import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def module():
    spec = importlib.util.spec_from_file_location('evaluation_costs', ROOT / 'scripts/evaluation_costs.py')
    target = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(target)
    return target


def event(kind, **fields):
    return {'type': 'event_msg', 'payload': {'type': kind, **fields}}


def usage(input_tokens, cached, output):
    return event('token_count', info={'total_token_usage': {
        'input_tokens': input_tokens, 'cached_input_tokens': cached,
        'output_tokens': output, 'total_tokens': input_tokens + output,
    }})


def sample():
    return [
        {'type': 'session_meta', 'payload': {'id': 'session-1', 'cli_version': 'host-1'}},
        event('task_started', turn_id='turn-1', started_at=100),
        {'type': 'turn_context', 'payload': {'turn_id': 'turn-1', 'model': 'actual-model', 'effort': 'ultra'}},
        usage(100, 80, 10), usage(300, 260, 30),
        event('task_complete', turn_id='turn-1', duration_ms=1200, started_at=100, completed_at=101),
    ]


def run_row(mode='full'):
    return {
        'run_id': mode, 'question_id': 'Q1', 'question_type': 'analysis', 'repetition': 1,
        'reading_mode': mode, 'input_sha256': 'input', 'packet_sha256': 'packet',
        'environment_sha256': 'environment', 'context_prefix_sha256': 'context',
        'cost': {**module().extract_costs(sample()), 'session_id': mode},
        'reading_verified': True,
    }


class CostExtractionTests(unittest.TestCase):
    def test_last_cumulative_snapshot_is_counted_once(self):
        result = module().extract_costs(sample())
        self.assertEqual(result['input_tokens'], 300)
        self.assertEqual(result['cached_input_tokens'], 260)
        self.assertEqual(result['uncached_input_tokens'], 40)
        self.assertEqual(result['output_tokens'], 30)
        self.assertEqual(result['total_tokens'], 330)
        self.assertEqual(result['turn_count'], 1)
        self.assertEqual(result['usage_update_count'], 2)
        self.assertEqual(result['wall_seconds'], 1.2)
        self.assertEqual(result['actual_model'], 'actual-model')
        self.assertEqual(result['actual_effort'], 'ultra')
        self.assertTrue(result['completed'])

    def test_identical_snapshots_do_not_inflate_request_count(self):
        rows = sample()
        rows.insert(5, copy.deepcopy(rows[4]))
        self.assertEqual(module().extract_costs(rows)['usage_update_count'], 2)

    def test_missing_fields_remain_null(self):
        result = module().extract_costs([])
        for field in ('actual_model', 'actual_effort', 'turn_count', 'wall_seconds',
                      'input_tokens', 'cached_input_tokens', 'uncached_input_tokens',
                      'output_tokens', 'usage_update_count'):
            self.assertIsNone(result[field], field)
        self.assertFalse(result['completed'])

    def test_requested_model_is_not_actual_model(self):
        rows = sample()
        rows[2]['payload'].pop('model')
        rows[2]['payload']['collaboration_mode'] = {'settings': {'model': 'requested-model'}}
        self.assertIsNone(module().extract_costs(rows)['actual_model'])

    def test_cache_exceeding_input_is_invalid(self):
        rows = sample()
        rows[4] = usage(300, 301, 30)
        with self.assertRaisesRegex(ValueError, 'cached_input_tokens'):
            module().extract_costs(rows)

    def test_cumulative_reset_is_not_silently_undercounted(self):
        rows = sample()
        rows.insert(5, usage(50, 20, 5))
        with self.assertRaisesRegex(ValueError, 'decreased'):
            module().extract_costs(rows)

    def test_total_counter_inconsistency_is_rejected(self):
        rows = sample()
        rows[4]['payload']['info']['total_token_usage']['total_tokens'] = 999
        with self.assertRaisesRegex(ValueError, 'total_tokens'):
            module().extract_costs(rows)

    def test_multi_turn_log_is_identified(self):
        rows = sample() + [event('task_started', turn_id='turn-2'),
                          {'type': 'turn_context', 'payload': {'turn_id': 'turn-2', 'model': 'other', 'effort': 'high'}}]
        result = module().extract_costs(rows)
        self.assertEqual(result['turn_count'], 2)
        self.assertIsNone(result['actual_model'])
        self.assertIsNone(result['actual_effort'])
        self.assertFalse(result['completed'])
        self.assertIsNone(result['wall_seconds'])

    def test_unknown_agent_activity_remains_visible_without_claiming_child(self):
        rows = sample() + [event('item_completed', item={'type': 'SubAgentActivity', 'agent_thread_id': 'child-1'})]
        result = module().extract_costs(rows)
        self.assertEqual(result['child_session_ids'], [])
        self.assertEqual(result['unresolved_agent_session_ids'], ['child-1'])

    def test_message_to_confirmed_parent_is_not_a_spawned_child(self):
        rows = sample()
        rows[0]['payload'].update({
            'session_id': 'parent-1', 'parent_thread_id': 'parent-1',
            'source': {'subagent': {'thread_spawn': {'parent_thread_id': 'parent-1'}}},
        })
        rows.extend([
            {'type': 'response_item', 'payload': {'type': 'function_call', 'namespace': 'collaboration',
                                                'name': 'send_message', 'call_id': 'parent-message'}},
            event('item_completed', item={'type': 'SubAgentActivity', 'kind': 'interacted',
                                         'id': 'parent-message', 'agent_thread_id': 'parent-1'}),
        ])
        result = module().extract_costs(rows)
        self.assertEqual(result['session_id'], 'session-1')
        self.assertEqual(result['parent_session_id'], 'parent-1')
        self.assertEqual(result['parent_activity_session_ids'], ['parent-1'])
        self.assertEqual(result['child_session_ids'], [])
        self.assertEqual(result['unresolved_agent_session_ids'], [])

    def test_nested_parent_metadata_is_sufficient(self):
        rows = sample()
        rows[0]['payload']['source'] = {'subagent': {'thread_spawn': {'parent_thread_id': 'parent-1'}}}
        rows.append(event('item_completed', item={'type': 'SubAgentActivity', 'kind': 'interacted',
                                                  'agent_thread_id': 'parent-1'}))
        self.assertEqual(module().extract_costs(rows)['child_session_ids'], [])
        self.assertEqual(module().extract_costs(rows)['unresolved_agent_session_ids'], [])

    def test_inherited_session_id_is_not_parent_evidence(self):
        rows = sample()
        rows[0]['payload']['session_id'] = 'possible-parent'
        rows.append(event('item_completed', item={'type': 'SubAgentActivity', 'kind': 'interacted',
                                                  'agent_thread_id': 'possible-parent'}))
        result = module().extract_costs(rows)
        self.assertIsNone(result['parent_session_id'])
        self.assertEqual(result['unresolved_agent_session_ids'], ['possible-parent'])

    def test_spawn_call_link_preserves_a_real_child(self):
        rows = sample()
        rows[0]['payload']['parent_thread_id'] = 'parent-1'
        rows.extend([
            {'type': 'response_item', 'payload': {'type': 'function_call', 'namespace': 'collaboration',
                                                'name': 'spawn_agent', 'call_id': 'spawn-child'}},
            event('item_completed', item={'type': 'SubAgentActivity', 'kind': 'started',
                                         'id': 'spawn-child', 'agent_thread_id': 'child-1'}),
            event('item_completed', item={'type': 'SubAgentActivity', 'kind': 'interacted',
                                         'id': 'parent-message', 'agent_thread_id': 'parent-1'}),
        ])
        result = module().extract_costs(rows)
        self.assertEqual(result['child_session_ids'], ['child-1'])
        self.assertEqual(result['unresolved_agent_session_ids'], [])
        self.assertEqual(result['parent_activity_session_ids'], ['parent-1'])

    def test_conflicting_parent_metadata_does_not_suppress_activity(self):
        rows = sample()
        rows[0]['payload']['parent_thread_id'] = 'parent-1'
        rows[0]['payload']['source'] = {'subagent': {'thread_spawn': {'parent_thread_id': 'parent-2'}}}
        rows.append(event('item_completed', item={'type': 'SubAgentActivity', 'kind': 'interacted',
                                                  'agent_thread_id': 'parent-1'}))
        result = module().extract_costs(rows)
        self.assertIsNone(result['parent_session_id'])
        self.assertEqual(result['unresolved_agent_session_ids'], ['parent-1'])

    def test_parent_spawn_conflict_remains_unresolved(self):
        rows = sample()
        rows[0]['payload']['parent_thread_id'] = 'parent-1'
        rows.extend([
            {'type': 'response_item', 'payload': {'type': 'function_call', 'namespace': 'collaboration',
                                                'name': 'spawn_agent', 'call_id': 'conflict'}},
            event('item_completed', item={'type': 'SubAgentActivity', 'kind': 'started',
                                         'id': 'conflict', 'agent_thread_id': 'parent-1'}),
        ])
        result = module().extract_costs(rows)
        self.assertEqual(result['child_session_ids'], [])
        self.assertEqual(result['parent_activity_session_ids'], [])
        self.assertEqual(result['unresolved_agent_session_ids'], ['parent-1'])

    def test_effort_is_not_guessed_from_model(self):
        rows = sample()
        rows[2]['payload'].pop('effort')
        self.assertIsNone(module().extract_costs(rows)['actual_effort'])


class PairedCostsTests(unittest.TestCase):
    def test_pair_records_separate_token_costs_and_ratios(self):
        left, right = run_row(), run_row('layered')
        right['cost']['uncached_input_tokens'] = 20
        right['cost']['cached_input_tokens'] = 130
        right['cost']['input_tokens'] = 150
        result = module().compare_pairs([left, right])
        self.assertEqual(result[0]['status'], 'cost_only')
        self.assertEqual(result[0]['layered_over_full']['uncached_input_tokens'], 0.5)
        self.assertIsNone(result[0]['quality_verdict'])
        self.assertFalse(result[0]['replacement_supported'])

    def test_model_or_effort_mismatch_invalidates_pair(self):
        for field in ('actual_model', 'actual_effort'):
            left, right = run_row(), run_row('layered')
            right['cost'][field] = 'different'
            self.assertIn(field, module().compare_pairs([left, right])[0]['exclusions'])

    def test_unknown_or_different_controls_invalidate_pair(self):
        for field in ('input_sha256', 'packet_sha256', 'environment_sha256', 'context_prefix_sha256'):
            left, right = run_row(), run_row('layered')
            right[field] = None
            self.assertIn(field, module().compare_pairs([left, right])[0]['exclusions'])

    def test_same_session_or_multiple_turns_invalidate_pair(self):
        left, right = run_row(), run_row('layered')
        right['cost']['session_id'] = left['cost']['session_id']
        self.assertIn('fresh_session', module().compare_pairs([left, right])[0]['exclusions'])
        right['cost']['session_id'] = 'other'
        right['cost']['turn_count'] = 2
        self.assertIn('single_turn', module().compare_pairs([left, right])[0]['exclusions'])

    def test_session_reuse_across_questions_invalidates_pairs(self):
        first, second = run_row(), run_row('layered')
        third = copy.deepcopy(first)
        third['question_id'] = 'Q2'
        fourth = copy.deepcopy(second)
        fourth['question_id'] = 'Q2'
        result = module().compare_pairs([first, second, third, fourth])
        self.assertTrue(all('fresh_session' in pair['exclusions'] for pair in result))

    def test_unknown_costs_or_subagents_invalidate_pair(self):
        first, second = run_row(), run_row('layered')
        first['cost']['output_tokens'] = None
        first['cost']['child_session_ids'] = ['child']
        exclusions = module().compare_pairs([first, second])[0]['exclusions']
        self.assertIn('cost_measurements', exclusions)
        self.assertIn('subagents', exclusions)

    def test_unresolved_agent_relationship_is_excluded_without_labeling_spawn(self):
        first, second = run_row(), run_row('layered')
        first['cost']['unresolved_agent_session_ids'] = ['unknown-1']
        exclusions = module().compare_pairs([first, second])[0]['exclusions']
        self.assertIn('unresolved_agent_activity', exclusions)
        self.assertNotIn('subagents', exclusions)

    def test_quality_needs_frozen_predeclared_threshold(self):
        left, right = run_row(), run_row('layered')
        quality = {'Q1:1': {'hard_points_missed': 0, 'new_errors': 0, 'blind_preference': 'tie', 'reviewer': 'author'}}
        result = module().compare_pairs([left, right], quality=quality, threshold_confirmed=False)
        self.assertFalse(result[0]['replacement_supported'])
        result = module().compare_pairs([left, right], quality=quality, threshold_confirmed=True)
        self.assertEqual(result[0]['quality_verdict'], 'noninferior_on_this_pair')
        self.assertTrue(result[0]['replacement_supported'])

    def test_hard_point_loss_or_unblinded_review_blocks_replacement(self):
        for change in ({'hard_points_missed': 1}, {'new_errors': 1}, {'blind_preference': 'full'}, {'reviewer': None}):
            quality = {'hard_points_missed': 0, 'new_errors': 0, 'blind_preference': 'tie', 'reviewer': 'author'}
            quality.update(change)
            result = module().compare_pairs([run_row(), run_row('layered')], quality={'Q1:1': quality}, threshold_confirmed=True)
            self.assertFalse(result[0]['replacement_supported'])

    def test_missing_mode_stays_in_table(self):
        result = module().compare_pairs([run_row()])
        self.assertEqual(result[0]['status'], 'incomplete')
        self.assertIsNone(result[0]['layered'])

    def test_duplicate_mode_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            module().compare_pairs([run_row(), run_row()])

    def test_zero_denominator_yields_null(self):
        left, right = run_row(), run_row('layered')
        left['cost']['uncached_input_tokens'] = 0
        self.assertIsNone(module().compare_pairs([left, right])[0]['layered_over_full']['uncached_input_tokens'])

    def test_cli_reads_logs_and_preserves_raw_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            logfile = root / 'run.jsonl'
            raw = '\n'.join(json.dumps(row) for row in sample()) + '\n'
            logfile.write_text(raw, encoding='utf-8')
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/evaluation_costs.py'), 'extract', str(logfile)],
                                    capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['input_tokens'], 300)
            self.assertEqual(logfile.read_text(encoding='utf-8'), raw)


if __name__ == '__main__':
    unittest.main()
