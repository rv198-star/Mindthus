"""Scoped source-direct observation mechanics; fixtures are not accuracy evidence."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest

from experiments.typed_decision import entry, observation_assessment as obs
from experiments.typed_decision.contracts import ContractError, DecisionResult, digest
from experiments.typed_decision.providers import FixtureProvider
from experiments.typed_decision.session import Session

REPO = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((REPO / 'experiments/typed_decision/fixtures/entry-correction.json').read_text())
FIT = {'explanatory_scope': 'scope_fit', 'premise_treatment': 'treatment_fit',
       'scope_preservation': 'within_scope',
       'evidence_decision_fit': 'grounded_and_responsive'}


class ObservationAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = deepcopy(FIXTURE['input'])
        self.data['activation']['checks'] = list(obs.CHECKS)

    def assess(self, answers=None, *, stage='S1'):
        provider = FixtureProvider(FIT if answers is None else answers)
        with Session(self.root, provider, scope='source-direct-v3', limits=entry.CHECK_LIMITS) as session:
            report = obs.assess(session, self.data, REPO, stage=stage)
        return report, provider

    def test_one_batch_reads_original_task_and_candidate_without_proposal(self):
        report, provider = self.assess()
        self.assertEqual(provider.calls, [list(obs.CHECKS)])
        self.assertEqual(report['result']['action'], 'continue_original')
        self.assertNotIn('proposal', report['identity'])
        self.assertEqual(report['identity']['input_sha256'], digest(self.data))
        self.assertFalse(report['result']['qualification'])

    def test_advisory_unknown_does_not_block_independent_fit(self):
        answers = {**FIT, 'explanatory_scope': asdict(DecisionResult('provider_error')),
                   'premise_treatment': 'insufficient_context'}
        report, _ = self.assess(answers)
        self.assertEqual(report['result']['action'], 'continue_original')
        self.assertEqual(report['result']['advisory_unresolved'],
                         ['explanatory_scope', 'premise_treatment'])
        self.assertEqual(report['result']['blocking_unresolved'], [])

    def test_blocking_unknown_stays_unresolved(self):
        report, _ = self.assess({**FIT, 'evidence_decision_fit': 'insufficient_context'})
        self.assertEqual(report['result']['action'], 'acquire_information')
        self.assertEqual(report['result']['blocking_unresolved'], ['evidence_decision_fit'])

    def test_known_hit_can_request_one_repair_despite_advisory_failure(self):
        report, _ = self.assess({**FIT, 'evidence_decision_fit': 'material_source_omission',
                                 'explanatory_scope': asdict(DecisionResult('provider_error'))})
        self.assertEqual(report['result']['action'], 'request_correction')
        self.assertEqual(report['result']['hits'], ['evidence_decision_fit'])
        request = obs.correction_request(report, self.data, REPO)
        self.assertEqual(len(request['instructions']), 1)
        self.assertEqual(request['advisory_unresolved'], ['explanatory_scope'])

    def test_candidate_only_invention_is_a_named_hit(self):
        report, _ = self.assess({**FIT, 'evidence_decision_fit': 'unsupported_candidate_claim'})
        self.assertEqual(report['result']['action'], 'request_correction')

    def test_noisy_premise_attribution_cannot_drive_automatic_correction(self):
        report, _ = self.assess({**FIT, 'premise_treatment': 'unsupported_as_fact'})
        self.assertEqual(report['result']['action'], 'return_original_owner')
        self.assertEqual(report['result']['actionable_hits'], [])
        self.assertEqual(report['result']['advisory_hits'], ['premise_treatment'])
        row = next(x for x in report['result']['matrix']
                   if x['check_id'] == 'premise_treatment')
        self.assertEqual(row['effect']['hit'], 'advisory')

    def test_direct_evidence_finding_dominates_noisy_auxiliary_remedy(self):
        report, _ = self.assess({**FIT,
                                 'premise_treatment': 'unsupported_as_fact',
                                 'evidence_decision_fit': 'unsupported_candidate_claim'})
        self.assertEqual(report['result']['action'], 'request_correction')
        self.assertEqual(report['result']['advisory_hits'], ['premise_treatment'])
        request = obs.correction_request(report, self.data, REPO)
        self.assertEqual(request['instruction_checks'], ['evidence_decision_fit'])
        self.assertEqual(request['consumption_policy_ref'], obs.CONSUMPTION_POLICY)
        self.assertNotIn(obs.CHECKS['premise_treatment']['remedy'],
                         request['instructions'])

    def test_legacy_report_without_consumption_policy_is_rejected_cleanly(self):
        report, _ = self.assess({**FIT,
                                 'evidence_decision_fit': 'unsupported_candidate_claim'})
        del report['result']['consumption_policy_ref']
        with self.assertRaisesRegex(ContractError, 'source_direct_v3_contract_changed'):
            obs.correction_request(report, self.data, REPO)

    def test_high_risk_hit_returns_to_owner_before_any_correction(self):
        self.data['task']['risk'] = 'high'
        report, _ = self.assess({**FIT, 'evidence_decision_fit': 'unsupported_candidate_claim'})
        self.assertEqual(report['result']['action'], 'return_original_owner')
        self.assertEqual(report['result']['reason'], 'risk_outside_automatic_correction')
        with self.assertRaises(ContractError):
            obs.correction_request(report, self.data, REPO)

    def test_not_applicable_is_distinct_from_pass(self):
        report, _ = self.assess({**FIT, 'evidence_decision_fit': 'not_applicable'})
        row = next(x for x in report['result']['matrix']
                   if x['check_id'] == 'evidence_decision_fit')
        self.assertFalse(row['consumed'])
        self.assertEqual(report['result']['action'], 'continue_original')
        self.assertFalse(report['result']['qualification'])

    def test_candidate_change_invalidates_every_selected_observation(self):
        first, _ = self.assess()
        old_rows = first['result']['matrix']
        self.root = self.root / 'new'
        self.data['target'].update(version='2', text='新的当前候选。')
        second, _ = self.assess()
        self.assertNotEqual(first['run_id'], second['run_id'])
        for before, after in zip(old_rows, second['result']['matrix']):
            self.assertNotEqual(before['dependencies']['candidate_version'],
                                after['dependencies']['candidate_version'])

    def test_decision_context_change_invalidates_even_when_target_quote_is_same(self):
        first, _ = self.assess()
        self.root = self.root / 'new'
        self.data['decision_context']['goal'] = 'changed goal'
        second, _ = self.assess()
        self.assertNotEqual(first['run_id'], second['run_id'])
        self.assertNotEqual(first['result']['matrix'][0]['dependencies']['decision_context'],
                            second['result']['matrix'][0]['dependencies']['decision_context'])

    def test_s0_or_missing_candidate_is_rejected_before_provider(self):
        for change in ('s0', 'missing'):
            with self.subTest(change=change):
                self.data = deepcopy(FIXTURE['input'])
                self.data['activation']['checks'] = list(obs.CHECKS)
                if change == 's0':
                    self.data['activation']['event'] = 'before-route'
                    self.data['target']['kind'] = 'user_frame'
                    self.data['target']['text'] = self.data['task']['request']
                else:
                    self.data['target'] = None
                with self.assertRaises(ContractError): self.assess()


if __name__ == '__main__':
    unittest.main()
