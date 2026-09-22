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



class ReviewedTrialTests(unittest.TestCase):
    """Injected transport checks for the new frozen scorer, never live evidence."""
    def setUp(self):
        from unittest.mock import patch
        from experiments.typed_decision import review_trial
        from experiments.typed_decision.session import implementation_digest
        from experiments.typed_decision.campaign import sha
        self.trial = review_trial
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        freeze = self.root / 'test-freeze.json'
        freeze.write_text(json.dumps({'implementation':implementation_digest(),
            'file_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (
                DOCS/'cases.json',DOCS/'c02-contract-v2.json')}}))
        frozen = patch.object(review_trial,'FREEZE',freeze)
        frozen.start(); self.addCleanup(frozen.stop)
        env = patch.dict('os.environ',{'TYPESAFE_API_KEY':'fixture-only-credential'})
        env.start(); self.addCleanup(env.stop)
        self.network = []

    def provider(self, transform=None):
        from experiments.typed_decision.providers import TypeSafeJevProvider
        from experiments.typed_decision.contracts import digest
        contract, cases = self.trial.inputs(ROOT)
        entry = {c['context']['provenance']['source_ref']:c['contract_accepted'][0]
                 for c in cases['c01'] if c['contract_accepted'] is not None}
        planning = {digest(project_context(c02.specs(contract),c['context'])):c['accepted'][0]
                    for c in cases['c02']}
        fidelity = {digest(project_context(c02.specs(contract,recheck=True),c['context'])):
                    c['expected_fidelity'] for c in cases['fidelity_counterexamples']}
        def transport(url,headers,body,timeout):
            self.network.append(body)  # Excludes headers and keys.
            state = body['state']
            if 'provenance' in state:
                values = {**entry[state['provenance']['source_ref']],
                          'unresolved_obligation':'clear','applicable':'yes'}
            elif 'recheck_fidelity' in body['questions']:
                values = {'recheck_fidelity':fidelity[digest(state)],'recheck_utility':'adequate'}
            else:
                values = {k:v or 'unclear' for k,v in planning[digest(state)].items()}
            if transform: values = transform(values,body)
            return {'model':'jev-1.13.0','answers':{key:{'type':'choice','choice':values[key],
                'probabilities':{v:float(v==values[key]) for v in question['criteria']},'confidence':1.0}
                for key,question in body['questions'].items()},
                'usage':{'input_tokens':10,'output_tokens':1}}
        return TypeSafeJevProvider(transport=transport)

    def execute(self, provider):
        from experiments.typed_decision.session import write_once
        manifest, contract, cases = self.trial.prepare(ROOT,provider)
        root = self.root/'trial'
        write_once(root/'campaign.json',manifest)
        return self.trial.run(ROOT,root,provider,manifest,contract,cases)

    def test_union_of_fields_cannot_fake_joint_match(self):
        s=self.trial.score_joint({'x':'a','y':'d'},[{'x':'a','y':'b'},{'x':'c','y':'d'}])
        self.assertEqual(s['fields'],{'x':True,'y':True})
        self.assertFalse(s['joint'])

    def test_unknown_and_null_gold_are_not_positive_scores(self):
        self.assertIsNone(self.trial.score_joint({'x':'a'},None)['joint'])
        score=self.trial.score_joint({'owner':None,'support':'unclear'},
                [{'owner':None,'support':None}],unscored=('support',))
        self.assertTrue(score['fields']['owner'])
        self.assertIsNone(score['fields']['support'])
        self.assertEqual(score['abstentions'],['support'])
        total=self.trial.score_totals([{'case_id':'fixture','score':score}])
        self.assertEqual(total['fields']['support'],{'matched':0,'scored':0})

    def test_full_injected_run_scores_real_denominators_and_refuses_rerun(self):
        provider=self.provider()
        result=self.execute(provider)
        self.assertEqual(result['observed_cases'],17)
        self.assertEqual(result['attempts'],19)  # C01 1+1+3, C02 8, fidelity 6.
        self.assertEqual(result['totals']['c02']['fields']['support'],{'matched':7,'scored':7})
        self.assertTrue(all(result['local_gates'].values()))
        self.assertTrue(result['generation_eligible'])
        self.assertEqual(result['excluded'],[{'case_id':'N01','reason':'contract_gold_unadjudicated'}])
        for body in self.network:
            self.assertFalse({'accepted','rationale','canonical_accepted'} & set(body['state']))
        manifest,contract,cases=self.trial.prepare(ROOT,provider)
        with self.assertRaisesRegex(ContractError,'already finished'):
            self.trial.run(ROOT,self.root/'trial',provider,manifest,contract,cases)

    def test_safe_mismatch_collects_remaining_cases_but_blocks_generation(self):
        def mismatch(values,body):
            if values.get('utility')=='adequate' and 'action' in values:
                return {**values,'action':'make_actionable'}
            return values
        result=self.execute(self.provider(mismatch))
        self.assertEqual(result['observed_cases'],17)
        self.assertFalse(result['generation_eligible'])
        self.assertIsNone(result['stop_reason'])
        conflict = next(r for r in result['rows']['c02'] if r['case_id'] == 'N05')
        self.assertEqual(conflict['raw_action'], 'make_actionable')
        self.assertIsNone(conflict['rewrite_handoff_action'])
        self.assertEqual(conflict['consumption'], 'not_executed')

    def test_failure_is_terminal_without_retry_or_promotion(self):
        from experiments.typed_decision.providers import TypeSafeJevProvider,ProviderError
        def fail(*_):
            self.network.append('attempt')
            raise ProviderError('transport_failure')
        result=self.execute(TypeSafeJevProvider(transport=fail))
        self.assertEqual(result['stop_reason'],'technical_failure')
        self.assertEqual(len(self.network),1)
        self.assertEqual(len(result['unrun']),16)
        self.assertFalse(result['generation_eligible'])

    def test_mutated_labels_rejected_before_any_request(self):
        from experiments.typed_decision.session import write_once
        provider=self.provider()
        manifest,contract,cases=self.trial.prepare(ROOT,provider)
        root=self.root/'trial';write_once(root/'campaign.json',manifest)
        cases['c02'][0]['accepted'][0]['utility']='deficit'
        with self.assertRaisesRegex(ContractError,'inputs changed'):
            self.trial.run(ROOT,root,provider,manifest,contract,cases)
        self.assertEqual(self.network,[])

    def test_token_ceiling_stops_even_when_actual_cost_is_unknown(self):
        provider=self.provider()
        original=provider.transport
        def excessive(*args):
            response=original(*args)
            response['usage']['input_tokens']=64001
            return response
        provider.transport=excessive
        result=self.execute(provider)
        self.assertEqual(result['stop_reason'],'reported_input_tokens_exceed_reserve_assumption')
        self.assertEqual(len(self.network),1)
        self.assertIsNone(result['trial_usage']['cost_usd'])


if __name__ == '__main__':
    unittest.main()
