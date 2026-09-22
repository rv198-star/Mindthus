"""Review-remediation control tests; fixtures do not establish engine competence."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from experiments.typed_decision import c01, c02
from experiments.typed_decision.contracts import ContractError, DecisionResult, project_context
from experiments.typed_decision.providers import FixtureProvider
from experiments.typed_decision.session import Session, read_record

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs/internal/research/typed-decision/review-remediation'


class ReviewRemediationTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((DOCS / 'c02-contract-v2.json').read_text())
        self.cases = json.loads((DOCS / 'cases.json').read_text())
        self.tvg = (ROOT / 'skills/tvg/SKILL.md').read_text()
        self.data = self.context('N07')
        self.answers = {'utility': 'deficit', 'support': 'sufficient', 'action': 'make_actionable',
                        'recheck_utility': 'adequate', 'recheck_fidelity': 'faithful'}

    def context(self, ident):
        data = copy.deepcopy(next(c['context'] for c in self.cases['c02'] if c['id'] == ident))
        return {**data, 'tvg_contract': self.tvg}

    def test_adequate_never_consumes_speculative_rewrite(self):
        for action in c02.REWRITES:
            with self.subTest(action=action), tempfile.TemporaryDirectory() as root:
                provider = FixtureProvider({**self.answers, 'utility': 'adequate', 'action': action})
                with Session(Path(root), provider, scope='review-fixture') as session:
                    report = c02.plan(session, self.context('N05'), self.contract)
                    self.assertEqual(report['result']['reason'], 'inconsistent_local_judgments')
                    self.assertEqual(report['result']['route'], 'original_exit_owner')
                    self.assertIsNone(report['result']['exit_state'])
                    with self.assertRaises(ContractError):
                        c02.begin_rewrite(session, report, self.context('N05'), self.contract, 'fixture')

    def test_deficit_leave_unchanged_returns_conflict_not_success(self):
        with tempfile.TemporaryDirectory() as root:
            with Session(Path(root), FixtureProvider({**self.answers, 'action': 'leave_unchanged'}),
                         scope='review-fixture') as session:
                report = c02.plan(session, self.data, self.contract)
                self.assertEqual(report['result']['reason'], 'inconsistent_local_judgments')

    def test_source_missing_and_conflict_have_different_recovery(self):
        for support, route, reason in [('missing', 'acquire_information', 'evidence_missing'),
                ('conflict', 'original_exit_owner', 'source_basis_unresolved'),
                ('unclear', 'original_exit_owner', 'source_basis_unresolved')]:
            with self.subTest(support=support), tempfile.TemporaryDirectory() as root:
                with Session(Path(root), FixtureProvider({**self.answers, 'support': support}),
                             scope='review-fixture') as session:
                    result = c02.plan(session, self.data, self.contract)['result']
                    self.assertEqual((result['route'], result['reason']), (route, reason))
                    self.assertEqual(result['judgments']['action'], 'make_actionable')
                    self.assertIsNone(result['action'])  # Speculation was not consumed.

    def test_failed_sibling_cannot_be_replaced_by_a_rewrite(self):
        for key in ('utility', 'support', 'action'):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as root:
                provider = FixtureProvider({**self.answers, key: {'status': 'provider_error',
                    'value': None, 'uncertainty': None, 'reason': 'fixture'}})
                with Session(Path(root), provider, scope='review-fixture') as session:
                    report = c02.plan(session, self.data, self.contract)
                    self.assertEqual(report['result']['reason'], 'local_judgment_unavailable')
                    self.assertEqual(report['result']['route'], 'original_exit_owner')
                    self.assertEqual(session.calls_made, 1)

    def test_recheck_replaces_support_with_fidelity_and_never_certifies(self):
        variants = [('faithful', 'adequate', 'one_rewrite_and_recheck_complete'),
                    ('violation', 'adequate', 'artifact_fidelity_violation'),
                    ('unclear', 'adequate', 'artifact_review_unresolved'),
                    ('faithful', 'deficit', 'artifact_target_not_met')]
        for fidelity, utility, reason in variants:
            with self.subTest(fidelity=fidelity, utility=utility), tempfile.TemporaryDirectory() as root:
                provider = FixtureProvider({**self.answers, 'recheck_fidelity': fidelity,
                                            'recheck_utility': utility})
                with Session(Path(root), provider, scope='review-fixture') as session:
                    report = c02.plan(session, self.data, self.contract)
                    c02.begin_rewrite(session, report, self.data, self.contract, 'offline-fixture')
                    c02.record_rewrite(session, report['run_id'], self.context('N05')['artifact'],
                        generation_evidence='injected output; no real generation',
                        usage={'input_tokens': None, 'output_tokens': None, 'cost_usd': None})
                    checked = c02.recheck(session, report, self.data, self.contract)
                    self.assertEqual(provider.calls, [['utility', 'support', 'action'],
                                                     ['recheck_utility', 'recheck_fidelity']])
                    self.assertEqual(checked['result']['reason'], reason)
                    self.assertEqual(checked['result']['route'], 'original_exit_owner')
                    self.assertIsNone(checked['result']['exit_state'])
                    self.assertEqual(c02.recheck(session, report, self.data, self.contract)['run_id'],
                                     checked['run_id'])
                    self.assertEqual(session.calls_made, 2)

    def test_unavailable_fidelity_is_not_clean_artifact(self):
        answers = {**self.answers, 'recheck_fidelity': {'status': 'provider_error',
                    'value': None, 'uncertainty': None, 'reason': 'fixture'}}
        with tempfile.TemporaryDirectory() as root:
            with Session(Path(root), FixtureProvider(answers), scope='review-fixture') as session:
                report = c02.plan(session, self.data, self.contract)
                c02.begin_rewrite(session, report, self.data, self.contract, 'offline-fixture')
                c02.record_rewrite(session, report['run_id'], 'fixture output',
                    generation_evidence='injected output',
                    usage={'input_tokens': None, 'output_tokens': None, 'cost_usd': None})
                result = c02.recheck(session, report, self.data, self.contract)['result']
                self.assertEqual(result['reason'], 'artifact_review_unavailable')
                self.assertIsNone(result['exit_state'])

    def test_counterexamples_change_artifact_only_not_source_sufficiency(self):
        self.assertEqual(len(self.cases['fidelity_counterexamples']), 6)
        for case in self.cases['fidelity_counterexamples']:
            parent = next(c['context'] for c in self.cases['c02'] if c['id'] == case['parent_case_id'])
            self.assertEqual({k: v for k, v in case['context'].items() if k != 'artifact'},
                             {k: v for k, v in parent.items() if k != 'artifact'})
            self.assertEqual(case['expected_source_support'], 'sufficient')
            self.assertEqual(case['context']['artifact'] == parent['artifact'],
                             case['expected_fidelity'] == 'faithful')

    def test_new_c02_fixture_acceptance_is_joint_and_labels_do_not_enter_state(self):
        for case in self.cases['c02']:
            with self.subTest(case=case['id']), tempfile.TemporaryDirectory() as root:
                expected = case['accepted'][0]
                # null is an explicitly unscored field, not a correct answer.
                answers = {k: expected[k] or 'unclear' for k in ('utility', 'support', 'action')}
                data = self.context(case['id'])
                with Session(Path(root), FixtureProvider(answers), scope='review-fixture') as session:
                    result = c02.plan(session, data, self.contract)['result']
                    self.assertEqual(result['route'], expected['route'])
                    if result['route'] == 'rewrite_candidate':
                        self.assertEqual(result['action'], expected['action'])
                    projected = project_context(c02.specs(self.contract), {**data, **{
                        k: case[k] for k in ('accepted', 'rationale', 'scoring_class')}})
                    self.assertFalse({'accepted', 'rationale', 'scoring_class'} & set(projected))
                    self.assertEqual(session.calls_made, 1)

    def test_new_c01_accepted_paths_are_control_fixtures_not_model_scores(self):
        for case in self.cases['c01']:
            for expected in case['canonical_accepted']:
                with self.subTest(case=case['id'], expected=expected), tempfile.TemporaryDirectory() as root:
                    answers = {'entry_mode': expected['entry_mode'], 'unresolved_obligation': 'clear',
                               'owner': expected['owner'], 'applicable': 'yes'}
                    with Session(Path(root), FixtureProvider(answers), scope='review-fixture') as session:
                        result = c01.run(session, case['context'], ROOT)['result']
                        self.assertEqual({k: result[k] for k in expected}, expected)
                        self.assertEqual(result['consumption'], 'not_executed')

    def test_satisfied_constraints_do_not_become_unresolved_duties(self):
        source = copy.deepcopy(self.cases['c01'][1]['context'])
        source['constraints'] = ['管理员已批准将门卫替换为服务台；其他文字保持不变。']
        for duties, expected_route in [([], 'direct_execute'), (['尚未取得发布许可'], 'llm_fallback')]:
            with self.subTest(duties=duties), tempfile.TemporaryDirectory() as root:
                data = {**source, 'known_obligations': duties}
                with Session(Path(root), FixtureProvider({'entry_mode': 'direct_execution',
                             'unresolved_obligation': 'clear'}), scope='review-fixture') as session:
                    result = c01.run(session, data, ROOT)['result']
                    self.assertEqual(result['route'], expected_route)
                    self.assertEqual(result['obligations'], duties)

    def test_case_sources_do_not_reuse_identity_for_opposite_facts(self):
        seen = {}
        for case in self.cases['c02']:
            for evidence in case['context']['evidence']:
                previous = seen.setdefault(evidence['source_ref'], evidence['text'])
                self.assertEqual(previous, evidence['text'])
        ambiguous = self.cases['c01'][0]
        self.assertEqual(len(ambiguous['canonical_accepted']), 2)
        self.assertIsNone(ambiguous['contract_accepted'])
        self.assertEqual(ambiguous['task_value'], 'not_observed')

    def test_old_contract_cannot_silently_acquire_new_graph_semantics(self):
        old = json.loads((DOCS.parent / 'c02-local-contract.json').read_text())
        with self.assertRaises(ContractError):
            c02.specs(old)


if __name__ == '__main__':
    unittest.main()
