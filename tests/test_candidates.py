import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'candidates.py'
EXAMPLE = ROOT / 'assets' / 'examples' / 'candidates-example.json'


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cand = load('candidates')
lint = load('lint_derived')


def base(identifier='B1', kind='observed', **extra):
    item = {'id': identifier, 'statement': f'起点 {identifier}', 'kind': kind}
    if kind in {'observed', 'supported', 'stated'}:
        item['source'] = '教学占位：记录'
    if kind == 'conditional':
        item['conditions'] = ['条件甲']
    if kind == 'definition':
        item['section'] = '3.3'
    item.update(extra)
    return item


def formal(identifier='C1', parents=('B1',), **extra):
    item = {'id': identifier, 'statement': f'推论 {identifier}', 'identity': 'formal', 'move': 'compose',
            'parents': list(parents), 'model': '有限模型', 'derivation': ['第一步'],
            'novelty': {'level': 'new_here', 'scope': '领域层未检索'}, 'changes': ['改变一项解释']}
    item.update(extra)
    return item


def empirical(identifier='C2', parents=('B1',), **extra):
    item = {'id': identifier, 'statement': f'候选 {identifier}', 'identity': 'empirical', 'move': 'invert',
            'parents': list(parents), 'novelty': {'level': 'new_here', 'scope': '领域层未检索'},
            'observables': ['应看到甲'], 'rivals': [{'statement': '竞争项', 'distinguishing': '看乙'}],
            'minimal_test': '比对已有记录', 'reject_conditions': ['出现丙'], 'changes': ['改变方案'],
            'strength': 'exploration'}
    item.update(extra)
    return item


def variable(identifier='C3', parents=('B1',), **extra):
    item = empirical(identifier, parents, identity='variable', move='residual', residual='预期与结果相差两成',
                     upgrade_conditions=['重复出现'], forbidden_uses=['不得用于评价个人'])
    item.update(extra)
    return item


ANALOGY = {'source_domain': '排队系统', 'target_domain': '申诉流程', 'shared': ['到达与服务'],
           'differences': ['申诉可撤回'], 'not_transferable': ['服务时间独立'], 'mapping': ['顾客→申诉'],
           'test': '比较积压随到达率的变化'}


class Workspace(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.ledger = self.root / '候选.json'
        self.counter = 0

    def write(self, value, name=None):
        self.counter += 1
        path = self.root / (name or f'record-{self.counter}.json')
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
        return path

    def add(self, bases=(), candidates=(), question=None):
        record = {'base': list(bases), 'candidates': list(candidates)}
        if question is not None:
            record['question'] = question
        return cand.add_records(self.ledger, self.write(record))

    def rejects(self, candidate, fragment, bases=None):
        with self.assertRaises(ValueError) as caught:
            self.add([base()] if bases is None else bases, [candidate])
        self.assertIn(fragment, str(caught.exception))
        self.assertFalse(self.ledger.exists(), 'a refused record must not create or change the ledger')

    def stored(self):
        return json.loads(self.ledger.read_text(encoding='utf-8'))

    def candidate(self, identifier):
        return next(item for item in self.stored()['candidates'] if item['id'] == identifier)


class AddTests(Workspace):
    def test_new_candidates_start_as_proposed_with_empty_history(self):
        result = self.add([base()], [formal()], question='还能推出什么')
        self.assertEqual(result['added_base'], ['B1'])
        self.assertEqual(result['added_candidates'], ['C1'])
        ledger = self.stored()
        self.assertEqual(ledger['format'], cand.FORMAT)
        self.assertEqual(ledger['question'], '还能推出什么')
        self.assertEqual(ledger['candidates'][0]['status'], 'proposed')
        self.assertEqual(ledger['candidates'][0]['history'], [])

    def test_record_cannot_carry_runtime_fields(self):
        for field, value in (('status', 'supported'), ('history', []), ('added_at', '2026-01-01'),
                             ('revisions', [])):
            with self.subTest(field=field):
                self.rejects(formal(**{field: value}), '由工具写入')

    def test_unknown_fields_are_refused_everywhere(self):
        self.rejects(formal(confidence=0.9), '未知字段')
        with self.assertRaises(ValueError):
            self.add([base(score=1)], [])
        with self.assertRaises(ValueError):
            cand.add_records(self.ledger, self.write({'base': [base()], 'notes': 'x'}))
        self.assertFalse(self.ledger.exists())

    def test_record_needs_something_to_add(self):
        with self.assertRaises(ValueError):
            cand.add_records(self.ledger, self.write({'question': '只有问题'}))

    def test_a_ledger_holds_one_question(self):
        self.add([base()], [], question='问题甲')
        with self.assertRaises(ValueError) as caught:
            self.add([base('B2')], [], question='问题乙')
        self.assertIn('另建账本', str(caught.exception))
        self.add([base('B2')], [], question='问题甲')
        self.assertEqual(len(self.stored()['base']), 2)

    def test_duplicate_json_keys_and_nan_are_refused(self):
        path = self.root / 'dup.json'
        path.write_text('{"base": [], "base": []}', encoding='utf-8')
        with self.assertRaises(ValueError):
            cand.add_records(self.ledger, path)
        path.write_text('{"base": [{"id": "B1", "statement": "x", "kind": "assumption", "n": NaN}]}', encoding='utf-8')
        with self.assertRaises(ValueError):
            cand.add_records(self.ledger, path)

    def test_record_and_ledger_must_differ(self):
        self.ledger.write_text(json.dumps({'base': [base()]}), encoding='utf-8')
        with self.assertRaises(ValueError):
            cand.add_records(self.ledger, self.ledger)

    def test_ledger_inside_the_skill_is_refused(self):
        with self.assertRaises(OSError):
            cand.add_records(ROOT / 'assets' / 'ledger.json', self.write({'base': [base()]}))
        self.assertFalse((ROOT / 'assets' / 'ledger.json').exists())


class StartingPointTests(Workspace):
    def test_each_kind_keeps_what_makes_it_checkable(self):
        for kind, field in (('observed', 'source'), ('supported', 'source'), ('stated', 'source'),
                            ('conditional', 'conditions'), ('definition', 'section')):
            with self.subTest(kind=kind):
                item = base(kind=kind)
                del item[field]
                with self.assertRaises(ValueError):
                    self.add([item], [])
        self.add([base('A1', kind='assumption')], [])

    def test_unknown_kind_is_refused(self):
        with self.assertRaises(ValueError):
            self.add([base(kind='fact')], [])


class LineageTests(Workspace):
    def test_parent_must_exist(self):
        self.rejects(formal(parents=['B9']), '父项 B9 不存在')

    def test_identifiers_share_one_space(self):
        with self.assertRaises(ValueError) as caught:
            self.add([base('X1')], [formal('X1', parents=['X1'])])
        self.assertIn('自己为父项', str(caught.exception))
        with self.assertRaises(ValueError) as caught:
            self.add([base('X1'), base('X2')], [formal('X2', parents=['X1'])])
        self.assertIn('标识重复', str(caught.exception))

    def test_a_cycle_inside_one_batch_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            self.add([base()], [formal('C1', parents=['C2']), formal('C2', parents=['C1'])])
        self.assertIn('成环', str(caught.exception))

    def test_a_batch_may_derive_from_its_own_candidates(self):
        self.add([base()], [formal('C2', parents=['C1']), formal('C1')])
        ledger = cand.load_ledger(self.ledger)
        self.assertEqual(cand.generations(ledger), {'C2': 2, 'C1': 1})

    def test_moves_need_parents_and_associations_have_none(self):
        self.rejects(formal(parents=[]), '须有父项')
        self.rejects(empirical(move='association'), '联想没有父项')
        self.rejects(formal(move='association', parents=[]), '不能是模型内推论')

    def test_an_association_is_kept_but_never_called_derived(self):
        self.add([], [empirical('A1', parents=[], move='association')])
        report = cand.check_ledger(cand.load_ledger(self.ledger), {'3.3'})
        self.assertTrue(any('没有起点的联想' in line for line in report['warnings']))
        text = cand.render_markdown(cand.load_ledger(self.ledger))
        self.assertIn('## 联想', text)
        self.assertIn('不称推出', text)
        self.assertNotIn('## 谱系', text)

    def test_children_inherit_unsettled_conditions(self):
        self.add([base('B1', kind='stated'), base('B2'), base('B3', kind='conditional')],
                 [empirical('C1', parents=['B1']), formal('C2', parents=['C1', 'B2']),
                  formal('C3', parents=['C2', 'B3'])])
        trace = cand.lineage(cand.load_ledger(self.ledger), 'C3')
        self.assertEqual(trace['generation'], 3)
        self.assertEqual([row['id'] for row in trace['ancestors']], ['C2', 'B3', 'C1', 'B2', 'B1'])
        self.assertEqual([row['id'] for row in trace['conditional_on']], ['C2', 'B3', 'C1', 'B1'])
        self.assertEqual(trace['conditional_on'][1]['conditions'], ['条件甲'])

    def test_lineage_is_for_candidates_only(self):
        self.add([base()], [formal()])
        with self.assertRaises(ValueError):
            cand.lineage(cand.load_ledger(self.ledger), 'B1')
        with self.assertRaises(ValueError):
            cand.lineage(cand.load_ledger(self.ledger), 'C9')


class IdentityTests(Workspace):
    def test_a_formal_consequence_states_its_model_and_derivation(self):
        self.rejects(formal(model=''), 'model')
        self.rejects(formal(derivation=[]), 'derivation')

    def test_a_definitional_requirement_names_its_source_section(self):
        item = formal(identity='definitional', move='commit')
        self.rejects(item, '原文小节')
        self.add([base()], [dict(item, theory=[{'section': '3.3'}])])

    def test_an_empirical_candidate_never_stands_alone(self):
        for field, fragment in (('observables', 'observables'), ('rivals', '竞争项'),
                                ('minimal_test', 'minimal_test'), ('reject_conditions', 'reject_conditions'),
                                ('strength', 'strength')):
            with self.subTest(field=field):
                item = empirical()
                del item[field]
                self.rejects(item, fragment)
        self.rejects(empirical(rivals=[{'statement': '竞争项'}]), 'distinguishing')
        self.rejects(empirical(rivals=[{'statement': '竞争项', 'distinguishing': '  '}]), 'distinguishing')

    def test_a_variable_candidate_records_residual_upgrade_and_forbidden_uses(self):
        for field in ('residual', 'upgrade_conditions', 'forbidden_uses'):
            with self.subTest(field=field):
                item = variable()
                del item[field]
                self.rejects(item, field)
        self.add([base()], [variable()])

    def test_an_analogy_carries_all_seven_parts(self):
        item = empirical(identity='analogy', move='transfer', record={'kept': ['到达与服务的关系']},
                         analogy=copy.deepcopy(ANALOGY))
        for field in ANALOGY:
            with self.subTest(field=field):
                broken = copy.deepcopy(item)
                del broken['analogy'][field]
                self.rejects(broken, '七项')
        broken = copy.deepcopy(item)
        broken['analogy']['shared'] = []
        self.rejects(broken, 'shared')
        broken = copy.deepcopy(item)
        del broken['reject_conditions']
        self.rejects(broken, 'reject_conditions')
        self.add([base()], [item])

    def test_transfer_needs_the_analogy_even_when_stated_as_a_candidate(self):
        self.rejects(empirical(move='transfer', record={'lost': ['服务时间独立']}), '七项')

    def test_transforming_moves_record_what_was_kept_changed_or_lost(self):
        for move in ('scale', 'relation', 'representation'):
            with self.subTest(move=move):
                self.rejects(empirical(move=move), 'record')
                self.rejects(empirical(move=move, record={'kept': [], 'lost': []}), '不能预设无损')
        self.rejects(empirical(move='scale', record={'kept': ['总量'], 'gained': ['x']}), 'record')
        self.add([base()], [empirical(move='scale', record={'kept': ['总量'], 'lost': ['各站分布']})])

    def test_novelty_always_states_its_scope(self):
        self.rejects(formal(novelty={'level': 'new_here'}), 'scope')
        self.rejects(formal(novelty={'level': 'unseen_in_scope', 'scope': ' '}), 'scope')
        self.rejects(formal(novelty={'level': 'known', 'scope': '查过教材'}), 'prior')
        self.rejects(formal(novelty={'level': 'recalled', 'prior': ['记得有类似说法']}), 'scope')
        self.rejects(formal(novelty={'level': 'recalled', 'scope': '凭回忆，未检索'}), 'prior')
        self.rejects(formal(novelty={'level': 'first_ever', 'scope': 'x'}), 'level')
        item = formal()
        del item['novelty']
        self.rejects(item, 'novelty')

    def test_a_remembered_but_unverified_prior_claim_is_not_recorded_as_new(self):
        self.add([base()], [formal(novelty={'level': 'recalled', 'scope': '凭回忆，未检索',
                                            'prior': ['调查方法里常说的无应答偏差']})])
        text = cand.render_markdown(cand.load_ledger(self.ledger))
        self.assertIn('| C1 | 1 | 模型内推论 | 核对组合 | B1 | 可能已有 | 提出 |', text)
        self.assertIn('调查方法里常说的无应答偏差', text)
        self.assertEqual(list(cand.NOVELTY), ['restated', 'known', 'recalled', 'new_here', 'unseen_in_scope'])

    def test_sensitive_candidates_state_necessity_and_risk(self):
        self.rejects(empirical(sensitive=True, risk='可能暴露个人'), 'necessity')
        self.rejects(empirical(sensitive=True, necessity='判断依赖它'), 'risk')
        self.rejects(empirical(sensitive='yes'), 'sensitive')
        self.add([base()], [empirical(sensitive=True, necessity='判断依赖它', risk='可能暴露个人')])

    def test_strength_is_only_for_graded_identities_and_starts_low(self):
        self.rejects(formal(strength='exploration'), 'strength')
        self.rejects(empirical(strength='diagnostic'), '外部可观察材料')
        self.rejects(empirical(strength='strong'), 'strength')

    def test_questions_and_proposals_need_no_test(self):
        common = {'parents': ['B1'], 'novelty': {'level': 'new_here', 'scope': '领域层未检索'}}
        self.add([base()], [dict(common, id='Q1', statement='新问题', identity='question', move='task'),
                            dict(common, id='P1', statement='构想', identity='proposal', move='position',
                                 changes=['方案集多一项'])])


class AdvanceTests(Workspace):
    def setUp(self):
        super().setUp()
        self.add([base()], [empirical('E1'), formal('F1'),
                            {'id': 'P1', 'statement': '构想', 'identity': 'proposal', 'move': 'position',
                             'parents': ['B1'], 'novelty': {'level': 'new_here', 'scope': '未检索'}}])

    def evidence(self, direction='supports'):
        return self.write([{'ref': '教学占位：比对表', 'direction': direction, 'note': '说明'}])

    def test_testing_cannot_be_skipped(self):
        with self.assertRaises(ValueError) as caught:
            cand.advance(self.ledger, 'E1', 'supported', evidence_path=self.evidence())
        self.assertIn('不能跳过检验', str(caught.exception))
        self.assertEqual(self.candidate('E1')['status'], 'proposed')

    def test_support_needs_supporting_evidence_submitted_with_it(self):
        cand.advance(self.ledger, 'E1', 'testing')
        for path in (None, self.evidence('context'), self.evidence('undercuts')):
            with self.subTest(path=path), self.assertRaises(ValueError) as caught:
                cand.advance(self.ledger, 'E1', 'supported', evidence_path=path)
            self.assertIn('支持性证据', str(caught.exception))
        cand.advance(self.ledger, 'E1', 'supported', evidence_path=self.evidence())
        item = self.candidate('E1')
        self.assertEqual(item['status'], 'supported')
        self.assertEqual([step['to'] for step in item['history']], ['testing', 'supported'])
        self.assertEqual(item['history'][1]['evidence'][0]['direction'], 'supports')

    def test_a_formal_consequence_is_supported_the_same_way(self):
        cand.advance(self.ledger, 'F1', 'testing', note='独立复算')
        cand.advance(self.ledger, 'F1', 'supported', evidence_path=self.evidence())
        self.assertEqual(self.candidate('F1')['status'], 'supported')
        with self.assertRaises(ValueError):
            cand.advance(self.ledger, 'F1', 'testing', strength='exploration', note='重新打开')

    def test_rejecting_retiring_and_reopening_need_a_reason(self):
        for target in ('rejected', 'retired'):
            with self.subTest(target=target), self.assertRaises(ValueError):
                cand.advance(self.ledger, 'E1', target)
        cand.advance(self.ledger, 'E1', 'testing')
        cand.advance(self.ledger, 'E1', 'supported', evidence_path=self.evidence())
        with self.assertRaises(ValueError):
            cand.advance(self.ledger, 'E1', 'testing')
        cand.advance(self.ledger, 'E1', 'testing', note='出现反例')
        self.assertEqual(self.candidate('E1')['status'], 'testing')

    def test_rejected_and_retired_are_final(self):
        cand.advance(self.ledger, 'E1', 'rejected', note='出现丙')
        for target in ('testing', 'supported', 'retired'):
            with self.subTest(target=target), self.assertRaises(ValueError) as caught:
                cand.advance(self.ledger, 'E1', target, note='x', evidence_path=self.evidence())
            self.assertIn('终态', str(caught.exception))

    def test_proposals_are_handed_on_not_judged_here(self):
        for target in ('testing', 'rejected'):
            with self.subTest(target=target), self.assertRaises(ValueError) as caught:
                cand.advance(self.ledger, 'P1', target, note='x')
            self.assertIn('退役', str(caught.exception))
        cand.advance(self.ledger, 'P1', 'retired', note='交方案比较')
        self.assertEqual(self.candidate('P1')['history'][0]['note'], '交方案比较')

    def test_diagnostic_strength_exists_only_with_support(self):
        with self.assertRaises(ValueError):
            cand.advance(self.ledger, 'E1', 'testing', strength='diagnostic')
        cand.advance(self.ledger, 'E1', 'testing')
        cand.advance(self.ledger, 'E1', 'supported', evidence_path=self.evidence(), strength='diagnostic')
        self.assertEqual(self.candidate('E1')['strength'], 'diagnostic')
        cand.advance(self.ledger, 'E1', 'testing', note='出现反例')
        item = self.candidate('E1')
        self.assertEqual(item['strength'], 'exploration')
        self.assertEqual(item['history'][1]['strength'], 'diagnostic')
        self.assertEqual(item['history'][2]['strength'], 'exploration')

    def test_unknown_candidate_and_missing_ledger(self):
        with self.assertRaises(ValueError):
            cand.advance(self.ledger, 'E9', 'testing')
        with self.assertRaises(ValueError):
            cand.advance(self.root / 'none.json', 'E1', 'testing')

    def test_malformed_evidence_changes_nothing(self):
        cand.advance(self.ledger, 'E1', 'testing')
        before = self.ledger.read_bytes()
        for value in ({'ref': 'x'}, [{'ref': '', 'direction': 'supports'}], [{'ref': 'x', 'direction': 'proves'}],
                      [{'ref': 'x', 'direction': 'supports', 'weight': 3}]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                cand.advance(self.ledger, 'E1', 'supported', evidence_path=self.write(value))
        self.assertEqual(self.ledger.read_bytes(), before)


class WritingTests(Workspace):
    def test_a_leftover_lock_blocks_the_write_and_is_not_removed(self):
        self.add([base()], [])
        lock = self.ledger.with_name(self.ledger.name + '.lock')
        lock.write_text('', encoding='utf-8')
        before = self.ledger.read_bytes()
        with self.assertRaises(ValueError) as caught:
            self.add([base('B2')], [])
        self.assertIn('写锁', str(caught.exception))
        self.assertEqual(self.ledger.read_bytes(), before)
        self.assertTrue(lock.exists())
        self.assertEqual([path.name for path in self.root.glob('.candidates-*')], [])

    def test_a_ledger_changed_underneath_is_not_overwritten(self):
        self.add([base()], [])
        ledger = cand.load_ledger(self.ledger)
        stale = self.ledger.read_bytes()
        self.add([base('B2')], [])
        with self.assertRaises(ValueError) as caught:
            cand.save_ledger(self.ledger, ledger, stale)
        self.assertIn('已由其他工作改变', str(caught.exception))
        self.assertEqual(len(self.stored()['base']), 2)

    def test_a_foreign_json_file_is_not_taken_for_a_ledger(self):
        self.ledger.write_text(json.dumps({'schema_version': 1, 'claims': []}), encoding='utf-8')
        before = self.ledger.read_bytes()
        with self.assertRaises(ValueError) as caught:
            self.add([base()], [])
        self.assertIn('不是可识别的候选账本', str(caught.exception))
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_a_rewritten_status_is_noticed_on_load(self):
        self.add([base()], [empirical('E1')])
        ledger = self.stored()
        ledger['candidates'][0]['status'] = 'supported'
        self.ledger.write_text(json.dumps(ledger, ensure_ascii=False), encoding='utf-8')
        with self.assertRaises(ValueError) as caught:
            cand.load_ledger(self.ledger)
        self.assertIn('直接改写', str(caught.exception))

    def test_a_forged_support_step_is_refused_on_load(self):
        self.add([base()], [empirical('E1')])
        ledger = self.stored()
        item = ledger['candidates'][0]
        item['status'] = 'supported'
        item['history'] = [{'from': 'proposed', 'to': 'testing', 'at': 'x'},
                           {'from': 'testing', 'to': 'supported', 'at': 'x'}]
        self.ledger.write_text(json.dumps(ledger, ensure_ascii=False), encoding='utf-8')
        with self.assertRaises(ValueError) as caught:
            cand.load_ledger(self.ledger)
        self.assertIn('没有支持性证据', str(caught.exception))


class CheckTests(Workspace):
    def check(self):
        return cand.check_ledger(cand.load_ledger(self.ledger), cand.known_sections())

    def test_unresolvable_sections_are_errors(self):
        self.add([base('D1', kind='definition', section='99.9')], [formal(parents=['D1'], theory=[{'section': '88.8'}])])
        report = self.check()
        self.assertFalse(report['ok'])
        self.assertEqual(len(report['errors']), 2)

    def test_real_sections_resolve(self):
        self.add([base('D1', kind='definition', section='3.3')], [formal(parents=['D1'], theory=[{'section': 'C.12'}])])
        self.assertTrue(self.check()['ok'])

    def test_things_to_look_at_again_are_warnings_not_scores(self):
        self.add([base()], [
            formal('R1', novelty={'level': 'restated'}),
            formal('N1', changes=[]),
            empirical('S1', move='scale', record={'kept': ['总量']}),
            empirical('P1', post_outcome='季度结果公布之后'),
            empirical('H1', sensitive=True, necessity='判断依赖它', risk='可能暴露个人'),
        ])
        report = self.check()
        self.assertTrue(report['ok'])
        joined = '\n'.join(report['warnings'])
        for fragment in ('R1: 标为重述', 'N1: 未说明成立后改变什么', 'S1: 未记录丢失项',
                         'P1: 结果后提出', 'H1: 涉及隐私'):
            self.assertIn(fragment, joined)
        self.assertNotIn('score', json.dumps(report))
        self.assertIn('不判断候选是否为真', report['scope'])

    def test_a_fourth_generation_is_flagged(self):
        self.add([base()], [formal('C1'), formal('C2', parents=['C1']), formal('C3', parents=['C2']),
                            formal('C4', parents=['C3'])])
        warnings = self.check()['warnings']
        self.assertTrue(any(line.startswith('C4: 已是第 4 代') for line in warnings))
        self.assertFalse(any(line.startswith('C3: 已是第') for line in warnings))

    def test_children_of_a_dead_parent_must_be_reviewed(self):
        self.add([base()], [empirical('C1'), formal('C2', parents=['C1']), formal('C3', parents=['C2'])])
        cand.advance(self.ledger, 'C1', 'rejected', note='出现丙')
        warnings = self.check()['warnings']
        self.assertTrue(any(line.startswith('C2: 父项 C1 已拒绝或退役') for line in warnings))
        self.assertTrue(any(line.startswith('C3: 父项 C1 已拒绝或退役') for line in warnings))
        self.assertFalse(any(line.startswith('C1: 父项') for line in warnings))

    def test_support_does_not_erase_what_a_candidate_still_depends_on(self):
        self.add([base('B1', kind='assumption')], [empirical('C1')])
        cand.advance(self.ledger, 'C1', 'testing')
        cand.advance(self.ledger, 'C1', 'supported',
                     evidence_path=self.write([{'ref': '记录', 'direction': 'supports'}]))
        self.assertTrue(any('C1: 虽得到支持，仍条件于 B1' in line for line in self.check()['warnings']))

    def test_a_superseded_candidate_still_in_service_is_flagged(self):
        self.add([base()], [empirical('C1')])
        self.add([], [empirical('C2', supersedes='C1')])
        self.assertTrue(any(line.startswith('C1: 已被 C2 取代') for line in self.check()['warnings']))
        cand.advance(self.ledger, 'C1', 'retired', note='由 C2 取代')
        self.assertFalse(any(line.startswith('C1: 已被 C2 取代') for line in self.check()['warnings']))
        with self.assertRaises(ValueError):
            self.add([], [empirical('C3', supersedes='C9')])
        with self.assertRaises(ValueError):
            self.add([], [empirical('C4', supersedes='C4')])


class RenderTests(Workspace):
    def setUp(self):
        super().setUp()
        cand.add_records(self.ledger, EXAMPLE)
        self.output = self.root / '候选账本.md'

    def test_document_shows_lineage_identity_and_inherited_conditions(self):
        text = cand.render_markdown(cand.load_ledger(self.ledger))
        self.assertTrue(text.startswith(cand.MARK))
        for fragment in ('| C1 | 1 | 模型内推论 | 核对组合 | B1、B2 | 对本题新 | 提出 |',
                         '| C4 | 2 | 构想 | 核对组合 | C2、B4 | 对本题新 | 提出 |',
                         '- **条件于：** C2（定义要求，提出）；B3（未核陈述）',
                         '- C4 ← C2 ＋ B4；最终起点：B3、B4',
                         '- C1 ← B1 ＋ B2',
                         '- **所依据的原文小节：** §2.4.2、附录 C.12',
                         '不判断候选是否为真'):
            self.assertIn(fragment, text)

    def test_table_cells_cannot_break_the_table(self):
        self.add([base('B9', statement='含 | 竖线\n和换行')], [])
        row = next(line for line in cand.render_markdown(cand.load_ledger(self.ledger)).splitlines()
                   if line.startswith('| B9 '))
        self.assertIn('含 \\| 竖线 和换行', row)

    def test_only_its_own_output_is_overwritten(self):
        cand.write_document('x', self.output)
        with self.assertRaises(ValueError):
            cand.write_document(cand.render_markdown(cand.load_ledger(self.ledger)), self.output)
        with self.assertRaises(ValueError):
            cand.write_document(cand.render_markdown(cand.load_ledger(self.ledger)), self.output, force=True)
        self.assertEqual(self.output.read_text(encoding='utf-8'), 'x')
        mine = self.root / 'mine.md'
        text = cand.render_markdown(cand.load_ledger(self.ledger))
        cand.write_document(text, mine)
        cand.write_document(text, mine, force=True)
        self.assertEqual(mine.read_text(encoding='utf-8'), text)

    def test_output_inside_the_skill_is_refused(self):
        with self.assertRaises(OSError):
            cand.write_document('x', ROOT / 'assets' / 'out.md')
        self.assertFalse((ROOT / 'assets' / 'out.md').exists())


class CommandLineTests(Workspace):
    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), '--ledger', str(self.ledger), *args],
                              capture_output=True, text=True, encoding='utf-8')

    def test_exit_codes_separate_success_findings_and_failure(self):
        result = self.run_tool('list')
        self.assertEqual(result.returncode, 2)
        self.assertIn('候选账本不存在', result.stderr)
        self.assertEqual(self.run_tool('add', '--record', str(EXAMPLE)).returncode, 0)
        result = self.run_tool('check')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['ok'])
        self.assertEqual(json.loads(self.run_tool('show', 'C3').stdout)['identity'], 'empirical')
        self.assertEqual(json.loads(self.run_tool('lineage', 'C4').stdout)['generation'], 2)
        self.assertEqual(self.run_tool('show', 'C99').returncode, 2)
        output = self.root / 'out.md'
        self.assertEqual(self.run_tool('render', '--output', str(output)).returncode, 0)
        self.assertEqual(self.run_tool('render', '--output', str(output)).returncode, 2)
        self.assertEqual(self.run_tool('render', '--output', str(output), '--force').returncode, 0)
        self.assertEqual(self.run_tool('render', '--output', str(self.ledger)).returncode, 2)
        self.add([], [formal('X1', theory=[{'section': '77.7'}])])
        result = self.run_tool('check')
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)['ok'])

    def test_read_only_commands_leave_the_ledger_untouched(self):
        self.run_tool('add', '--record', str(EXAMPLE))
        before = self.ledger.read_bytes()
        for args in (('list',), ('show', 'C1'), ('lineage', 'C4'), ('check',)):
            with self.subTest(args=args):
                self.run_tool(*args)
                self.assertEqual(self.ledger.read_bytes(), before)
        self.assertEqual(sorted(path.name for path in self.root.iterdir()), ['候选.json'])


class SourceBindingTests(unittest.TestCase):
    """The tool's vocabulary is the source text's, not a second one."""

    @classmethod
    def setUpClass(cls):
        manifest = json.loads((ROOT / 'source/source-manifest.json').read_text(encoding='utf-8-sig'))
        cls.units = lint.source_units((ROOT / 'source' / manifest['source_file']).read_text(encoding='utf-8-sig'))

    def test_statuses_are_the_candidate_states_of_the_source(self):
        for label in cand.STATUSES.values():
            with self.subTest(label=label):
                self.assertIn(label, self.units['2.13'])
                self.assertIn(label, self.units['11.8'])

    def test_strengths_are_the_first_three_levels_of_the_source(self):
        for label in cand.STRENGTHS.values():
            with self.subTest(label=label):
                self.assertIn(label, self.units['16.5'])

    def test_analogy_parts_are_the_seven_named_by_the_analogy_contract(self):
        for label in cand.ANALOGY_LABELS.values():
            with self.subTest(label=label):
                self.assertIn(label, self.units['2.6'])

    def test_example_is_a_valid_record_whose_sections_resolve(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / 'c.json'
            cand.add_records(ledger, EXAMPLE)
            report = cand.check_ledger(cand.load_ledger(ledger), cand.known_sections())
            self.assertEqual((report['ok'], report['warnings']), (True, []))
        text = EXAMPLE.read_text(encoding='utf-8')
        self.assertGreaterEqual(text.count('教学占位'), 5)


if __name__ == '__main__':
    unittest.main()
