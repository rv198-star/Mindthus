"""C01-next first-slice mechanics; fixtures do not establish semantic accuracy."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from experiments.typed_decision import assessment, entry
from experiments.typed_decision.contracts import ContractError, DecisionResult, canonical, digest
from experiments.typed_decision.providers import FixtureProvider, TypeSafeJevProvider
from experiments.typed_decision.session import Limits, RecoveryRequired, Session, read_record, write_once
from experiments.typed_decision.trace import validate_with_existing

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'experiments/typed_decision/fixtures/entry-correction.json').read_text())
FIT = {'explanatory_scope': 'scope_fit', 'premise_treatment': 'treatment_fit',
       'scope_preservation': 'within_scope'}


class AssessmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = deepcopy(FIXTURE['input'])

    def assess(self, answers=None, data=None, root=None):
        provider = FixtureProvider(FIT if answers is None else answers)
        with Session(root or self.root, provider, scope='assessment-test', limits=entry.CHECK_LIMITS) as s:
            report = assessment.assess(s, data or self.data, ROOT)
        return report, provider

    def test_three_checks_share_one_state_and_batch(self):
        report, p = self.assess()
        self.assertEqual(p.calls, [list(assessment.CHECKS)])
        self.assertEqual(report['result']['action'], 'continue_original')
        self.assertEqual(len(report['result']['matrix']), 3)
        self.assertEqual({r['phase'] for r in report['result']['matrix']}, {'S1'})
        self.assertFalse(report['result']['qualification'])
        self.assertEqual(report['result']['frame_status'], 'not_assessed')

    def test_rows_keep_object_version_sources_and_native_uncertainty(self):
        probs = {k: float(k == 'scope_fit') for k in assessment.CHECKS['explanatory_scope']['criteria']}
        answer = asdict(DecisionResult('ok', 'scope_fit',
                                      {'source': 'provider_distribution', 'confidence': .99, 'probabilities': probs}))
        report, _ = self.assess({**FIT, 'explanatory_scope': answer})
        row = report['result']['matrix'][0]
        self.assertEqual(row['uncertainty']['confidence'], .99)
        self.assertEqual(row['target_version'], self.data['target']['version'])
        self.assertEqual(row['object_scope'], self.data['decision_context'])
        self.assertEqual(row['state_sha256'], digest(self.data))
        self.assertEqual(row['origin'], 'offline_fixture')
        self.assertIn('whole', row['sources'])

    def test_inactive_is_unassessed_not_pass(self):
        self.data['activation']['frame_risk'] = False
        report, p = self.assess(data=self.data)
        self.assertFalse(p.calls)
        self.assertTrue(all(r['status'] == 'not_evaluated' for r in report['result']['matrix']))
        self.assertEqual(report['result']['reason'], 'not_activated')

    def test_no_execution_impact_skips_without_keyword_dispatch(self):
        self.data['activation']['execution_impact'] = False
        self.data['task']['request'] = '本质上其实就是 WAE SRA 系统问题。'
        report, p = self.assess(data=self.data)
        self.assertFalse(p.calls)
        self.assertEqual(report['result']['reason'], 'not_activated')

    def test_required_audit_is_never_waived_by_clear_checks(self):
        self.data['activation'].update(required=True, frame_risk=False)
        report, p = self.assess(data=self.data)
        self.assertEqual(len(p.calls), 1)
        self.assertEqual(report['result']['action'], 'return_original_owner')
        self.assertTrue(report['result']['required_audit_retained'])

    def test_known_obligations_retained_on_clear(self):
        self.data['task']['known_obligations'] = ['mandatory-review']
        report, _ = self.assess(data=self.data)
        self.assertEqual(report['result']['action'], 'return_original_owner')
        self.assertEqual(report['result']['obligations'], ['mandatory-review'])

    def test_no_candidate_no_answer_inspection(self):
        self.data['target'] = None
        report, p = self.assess(data=self.data)
        self.assertFalse(p.calls)
        self.assertEqual(report['result']['reason'], 'candidate_absent')
        self.assertTrue(all(r['target_ref'] is None for r in report['result']['matrix']))

    def test_s0_uses_actual_user_question_not_imaginary_answer(self):
        self.data['activation']['event'] = 'before-route'
        self.data['target'] = None
        report, p = self.assess(data=self.data)
        self.assertEqual(p.calls, [['explanatory_scope', 'premise_treatment']])
        self.assertEqual(report['result']['target']['text'], self.data['task']['request'])
        self.assertEqual(report['result']['matrix'][2]['status'], 'not_evaluated')
        self.assertEqual(report['result']['matrix'][2]['phase'], 'S0')

    def test_s0_frame_must_quote_original_request(self):
        self.data['activation']['event'] = 'before-route'
        self.data['target']['kind'] = 'user_frame'
        with self.assertRaises(ContractError):
            self.assess(data=self.data)
        self.assertFalse((self.root / 'calls').exists())

    def test_stale_input_d0_no_model(self):
        self.data['task']['freshness'] = 'stale'
        report, p = self.assess(data=self.data)
        self.assertFalse(p.calls)
        self.assertEqual(report['result']['action'], 'return_original_owner')

    def test_explicit_permission_outside_advisory_never_becomes_authority(self):
        self.data['task']['permission']['mode'] = 'execute'
        report, p = self.assess(data=self.data)
        self.assertFalse(p.calls)
        self.assertEqual(report['result']['reason'], 'permission_outside_advisory_scope')

    def test_high_risk_keeps_original_owner(self):
        self.data['task']['risk'] = 'high'
        report, _ = self.assess({'explanatory_scope':'local_overreach', **{k:v for k,v in FIT.items() if k != 'explanatory_scope'}}, self.data)
        self.assertEqual(report['result']['action'], 'return_original_owner')

    def test_unknown_not_applicable_and_not_evaluated_are_distinct(self):
        self.data['activation']['checks'] = ['explanatory_scope', 'premise_treatment']
        report, _ = self.assess({'explanatory_scope':'not_applicable', 'premise_treatment':'insufficient_context'}, self.data)
        rows = report['result']['matrix']
        self.assertEqual([(r['status'], r['value']) for r in rows],
                         [('ok','not_applicable'), ('ok','insufficient_context'), ('not_evaluated',None)])
        self.assertFalse(rows[0]['consumed'])
        self.assertTrue(rows[1]['consumed'])
        self.assertEqual(report['result']['action'], 'acquire_information')

    def test_sibling_failure_preserves_hit_but_does_not_start_correction(self):
        report, _ = self.assess({**FIT, 'explanatory_scope':'local_overreach',
                                'premise_treatment': asdict(DecisionResult('provider_error'))})
        self.assertEqual(report['result']['hits'], ['explanatory_scope'])
        self.assertEqual(report['result']['action'], 'return_original_owner')

    def test_simultaneous_p1_p3_are_not_majority_vote(self):
        report, _ = self.assess({**FIT, 'explanatory_scope':'local_overreach', 'scope_preservation':'scope_overridden'})
        request = assessment.correction_request(report, self.data, ROOT)
        self.assertEqual(len(request['instructions']), 2)
        self.assertTrue(request['instructions'][0].startswith('Restore the user'))
        self.assertEqual(request['original_task'], self.data['task'])
        self.assertNotIn('uncertainty', request)
        self.assertNotIn('matrix', request)

    def test_all_not_applicable_is_not_certification(self):
        report, _ = self.assess({k:'not_applicable' for k in FIT})
        self.assertFalse(report['result']['qualification'])
        self.assertTrue(all(not r['consumed'] for r in report['result']['matrix']))

    def test_same_snapshot_reentry_makes_no_new_call(self):
        first, p1 = self.assess()
        second, p2 = self.assess()
        self.assertEqual(len(p1.calls), 1)
        self.assertEqual(p2.calls, [])
        self.assertEqual(first['run_id'], second['run_id'])
        self.assertEqual(first['result'], second['result'])

    def test_changed_target_only_new_snapshot_no_old_outcome_mutation(self):
        first, _ = self.assess()
        old = {str(p):p.read_bytes() for p in self.root.rglob('*.json')}
        self.data['target'].update(text='新候选文本，依然只是待检查提案。', version='2')
        second, p = self.assess(data=self.data)
        self.assertNotEqual(first['run_id'], second['run_id'])
        self.assertEqual(len(p.calls), 1)
        for path, content in old.items(): self.assertEqual(Path(path).read_bytes(), content)

    def test_fixed_two_check_call_budget(self):
        self.assess()
        self.data['target']['version'] = '2'
        self.assess(data=self.data)
        self.data['target']['version'] = '3'
        report, p = self.assess(data=self.data)
        self.assertEqual(p.calls, [])
        self.assertEqual(report['result']['action'], 'return_original_owner')

    def test_invalid_activation_and_duplicate_checks_rejected(self):
        for changes in ({'required':'true'}, {'checks':['explanatory_scope','explanatory_scope']},
                        {'checks':['invented_check']}, {'event':'any-time'}):
            data = deepcopy(self.data); data['activation'].update(changes)
            with self.assertRaises(ContractError): self.assess(data=data)

    def test_unknown_call_does_not_repeat(self):
        class Interrupted(FixtureProvider):
            def evaluate(self, *args): raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            with Session(self.root, Interrupted(FIT), scope='assessment-test', limits=entry.CHECK_LIMITS) as s:
                assessment.assess(s, self.data, ROOT)
        with self.assertRaises(RecoveryRequired): self.assess()

    def test_original_task_not_candidate_is_evidence(self):
        class Recording(FixtureProvider):
            def evaluate(self, specs, state, timeout):
                self.state = deepcopy(state)
                return super().evaluate(specs, state, timeout)
        p = Recording(FIT)
        with Session(self.root, p, scope='capture') as s: assessment.assess(s, self.data, ROOT)
        self.assertEqual(p.state['original_task']['evidence'], self.data['task']['evidence'])
        self.assertEqual(p.state['assessment_target'], self.data['target'])
        self.assertNotIn('activation', p.state)
        self.assertNotIn('expected', p.state)


class EntryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'episode'
        self.fixture = deepcopy(FIXTURE)

    def run_entry(self, *, hook=True, route=False, root=None):
        provider = entry.EntryFixtureProvider(self.fixture['answers'])
        corrector = entry.ScriptedCorrection(self.fixture['correction']) if hook is True else hook or None
        report = entry.run(root or self.root, provider, self.fixture['input'], ROOT, corrector=corrector, route=route)
        return report, provider, corrector

    def test_closed_loop_revises_actual_target_once(self):
        report, p, h = self.run_entry()
        self.assertEqual(report['status'], 'corrected_rechecked')
        self.assertEqual(len(p.calls), 2)
        self.assertEqual(h.calls, 1)
        self.assertEqual(report['revised_target']['text'], self.fixture['correction']['text'])
        self.assertEqual(report['original_task'], self.fixture['input']['task'])
        self.assertEqual({r['phase'] for r in report['matrix']}, {'S2'})
        self.assertFalse(report['qualification'])

    def test_completed_reentry_zero_calls_including_correction(self):
        first, _, _ = self.run_entry()
        before = {str(p):p.read_bytes() for p in self.root.rglob('*.json')}
        second, p, h = self.run_entry()
        self.assertEqual(second, first)
        self.assertEqual(p.calls, [])
        self.assertEqual(h.calls, 0)
        self.assertEqual(before, {str(p):p.read_bytes() for p in self.root.rglob('*.json')})

    def test_pending_correction_can_resume_without_rechecking_original(self):
        pending, p, _ = self.run_entry(hook=False)
        self.assertEqual(pending['status'], 'awaiting_correction')
        finished, p, h = self.run_entry()
        self.assertEqual(finished['status'], 'corrected_rechecked')
        self.assertEqual(len(p.calls), 1)
        self.assertEqual(h.calls, 1)

    def test_recheck_failure_is_terminal_no_second_correction(self):
        self.fixture['answers']['by_target_version']['2']['explanatory_scope'] = 'local_overreach'
        report, p, h = self.run_entry()
        self.assertEqual(report['status'], 'returned_to_owner_after_one_recheck')
        self.assertEqual(h.calls, 1)
        again, p, h = self.run_entry()
        self.assertEqual(p.calls, [])
        self.assertEqual(h.calls, 0)
        self.assertEqual(again, report)

    def test_new_failure_dimension_on_recheck_is_not_ignored(self):
        self.fixture['answers']['by_target_version']['2']['scope_preservation'] = 'scope_overridden'
        report, _, _ = self.run_entry()
        self.assertEqual(report['status'], 'returned_to_owner_after_one_recheck')
        self.assertIn('scope_preservation', [r['check_id'] for r in report['matrix'] if r['value'] == 'scope_overridden'])

    def test_invalid_hook_reply_cannot_override_goals(self):
        self.fixture['correction']['task'] = {'request':'Replace user goal'}
        report, p, h = self.run_entry()
        self.assertEqual(report['status'], 'correction_failed')
        self.assertEqual(len(p.calls), 1)
        self.assertIsNone(report['revised_target'])
        self.assertEqual(report['original_task'], self.fixture['input']['task'])
        self.assertIsNone(read_record(self.root / 'correction/outcome.json')['reply'])

    def test_unchanged_revision_rejected(self):
        self.fixture['correction']['version'] = '1'
        report, _, _ = self.run_entry()
        self.assertEqual(report['status'], 'correction_failed')

    def test_hook_exception_terminal_and_secret_error_not_serialized(self):
        class Failed(entry.ScriptedCorrection):
            def correct(self, *args):
                self.calls += 1
                raise RuntimeError('NEVER_PERSIST_TEST_ERROR')
        hook = Failed(self.fixture['correction'])
        report, _, _ = self.run_entry(hook=hook)
        self.assertEqual(report['status'], 'correction_failed')
        report, p, _ = self.run_entry(hook=hook)
        self.assertEqual(hook.calls, 1)
        self.assertEqual(p.calls, [])
        self.assertNotIn('NEVER_PERSIST_TEST_ERROR', ''.join(p.read_text() for p in self.root.rglob('*.json')))

    def test_interrupted_correction_never_reissued(self):
        class Interrupted(entry.ScriptedCorrection):
            def correct(self, *args): raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt): self.run_entry(hook=Interrupted(self.fixture['correction']))
        self.assertTrue((self.root / 'correction/intent.json').exists())
        with self.assertRaises(RecoveryRequired): self.run_entry()
        with self.assertRaises(RecoveryRequired): self.run_entry(hook=False)

    def test_existing_route_called_only_after_clear_gate(self):
        self.fixture['answers']['initial'] = FIT
        self.fixture['answers']['routing'] = {'entry_mode':'mindthus_intervention','unresolved_obligation':'clear',
                                             'owner':'wae','applicable':'yes'}
        report, p, h = self.run_entry(route=True)
        self.assertEqual(report['status'], 'routed_proposal')
        self.assertEqual(report['routing']['result']['owner'], 'wae')
        self.assertEqual(report['handoff']['proposal']['owner'], 'wae')
        self.assertEqual(h.calls, 0)
        self.assertEqual(len(p.calls), 4)
        validate_with_existing(read_record(self.root / 'judgment-trace.json'), ROOT)
        self.assertEqual(report['native_skill_load'], 'not_observed')
        again, p, _ = self.run_entry(route=True)
        self.assertEqual(again, report)
        self.assertEqual(p.calls, [])

    def test_corrected_candidate_does_not_waive_original_audit(self):
        report, _, _ = self.run_entry(route=True)
        self.assertEqual(report['routing']['result']['route'], 'llm_fallback')
        self.assertIn('entry_correction_requires_original_owner_audit', report['handoff']['context']['known_obligations'])

    def test_failed_check_never_routes(self):
        self.fixture['answers']['initial']['premise_treatment'] = asdict(DecisionResult('provider_error'))
        report, p, h = self.run_entry(route=True)
        self.assertIsNone(report['routing'])
        self.assertEqual(h.calls, 0)
        self.assertEqual(len(p.calls), 1)

    def test_no_candidate_before_answer_does_not_generate_one(self):
        self.fixture['input']['target'] = None
        report, p, h = self.run_entry(route=True)
        self.assertEqual(report['status'], 'candidate_absent')
        self.assertEqual(p.calls, [])
        self.assertEqual(h.calls, 0)

    def test_s0_corrected_frame_keeps_original_request_and_checks_p3(self):
        self.fixture['input']['target'] = None
        self.fixture['input']['activation']['event'] = 'before-route'
        report, p, h = self.run_entry()
        self.assertEqual(p.calls[0], ['explanatory_scope','premise_treatment'])
        self.assertEqual(p.calls[1], list(FIT))
        self.assertEqual(report['revised_target']['kind'], 'candidate_frame')
        self.assertEqual(report['original_task']['request'], FIXTURE['input']['task']['request'])

    def test_changed_input_requires_distinct_episode_not_old_result(self):
        self.run_entry()
        self.fixture['input']['target']['text'] = 'Different candidate'
        with self.assertRaises(ContractError): self.run_entry()

    def test_changed_corrector_identity_is_rejected_before_call(self):
        hook = entry.ScriptedCorrection(self.fixture['correction'], identity='other-owner')
        with self.assertRaises(ContractError): self.run_entry(hook=hook)
        self.assertEqual(hook.calls, 0)
        self.assertFalse((self.root / 'correction/intent.json').exists())

    def test_live_driver_requires_its_own_campaign_admission(self):
        with self.assertRaisesRegex(ContractError, 'entry_live_campaign_not_preregistered'):
            entry.run(self.root, TypeSafeJevProvider(), self.fixture['input'], ROOT)
        self.assertFalse(self.root.exists())

    def test_corrupt_record_cannot_resume(self):
        self.run_entry()
        path = self.root / 'correction/outcome.json'
        raw = json.loads(path.read_text()); raw['payload']['reply']['text'] = 'tampered'
        path.write_text(json.dumps(raw))
        with self.assertRaises(ContractError): self.run_entry()

    def test_budgeted_provider_caps_child_timeout_by_shared_remaining(self):
        class Dummy(FixtureProvider):
            def evaluate(self, specs, state, timeout):
                self.timeout = timeout
                from experiments.typed_decision.contracts import BatchResult
                return BatchResult({})
        p = Dummy({})
        with patch.object(entry, '_remaining', return_value=1.25):
            entry._BudgetedProvider(p, self.root, 0).evaluate([], {}, 30)
        self.assertEqual(p.timeout, 1.25)

    def test_cross_stage_runtime_drift_blocks_before_handoff(self):
        self.fixture['answers']['initial'] = FIT
        self.fixture['answers']['routing'] = {'entry_mode':'mindthus_intervention',
            'unresolved_obligation':'clear', 'owner':'wae', 'applicable':'yes'}
        class Drifting(entry.EntryFixtureProvider):
            def validate_runtime(self, runtime): runtime.validate()
            def evaluate(self, specs, state, timeout):
                from experiments.typed_decision.contracts import ResolvedRuntime
                result = super().evaluate(specs, state, timeout)
                result.resolved_runtime = ResolvedRuntime(
                    'snapshot-one' if 'assessment_target' in state else 'snapshot-two', 'fixture')
                return result
        p = Drifting(self.fixture['answers'])
        report = entry.run(self.root, p, self.fixture['input'], ROOT, route=True)
        self.assertEqual(report['status'], 'routing_failed')
        self.assertIsNone(report['handoff'])
        self.assertEqual(len(p.calls), 2)  # No owner/applicability calls after runtime drift.

    def test_hook_mutation_cannot_change_original_context(self):
        class Mutating(entry.ScriptedCorrection):
            def correct(self, request, timeout):
                request['original_task']['request'] = 'malicious replacement'
                request['decision_context']['goal'] = 'different goal'
                return super().correct(request, timeout)
        result, _, _ = self.run_entry(hook=Mutating(self.fixture['correction']))
        self.assertEqual(result['original_task'], self.fixture['input']['task'])
        revision = read_record(self.root / 'revision.json')['input']
        self.assertEqual(revision['decision_context'], self.fixture['input']['decision_context'])

    def test_optional_checks_do_not_become_required_on_reentry(self):
        self.fixture['input']['activation']['checks'] = ['premise_treatment']
        self.fixture['answers']['initial'] = FIT
        result, p, hook = self.run_entry()
        self.assertEqual(p.calls, [['premise_treatment']])
        self.assertEqual(hook.calls, 0)
        self.assertEqual([r['status'] for r in result['matrix']], ['not_evaluated','ok','not_evaluated'])

    def test_source_change_is_detected_before_reusing_results(self):
        self.run_entry()
        original = assessment.source_contracts
        def changed(repo):
            rules, refs = original(repo)
            refs['whole']['sha256'] = 'f' * 64
            return rules, refs
        with patch.object(assessment, 'source_contracts', side_effect=changed), self.assertRaises(ContractError):
            self.run_entry()

    def test_cli_runs_and_replays_without_keys(self):
        cmd = [sys.executable, '-m', 'experiments.typed_decision.entry', '--state-root', str(self.root)]
        a = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=15)
        b = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=15)
        self.assertEqual(a.returncode, 0, a.stdout + a.stderr)
        self.assertEqual(b.returncode, 0, b.stdout + b.stderr)
        self.assertEqual(json.loads(a.stdout), json.loads(b.stdout))


if __name__ == '__main__':
    unittest.main()
