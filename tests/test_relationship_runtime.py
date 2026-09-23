"""Public-entry D2 recovery controls. Injected labels are NOT semantic model evidence."""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import fcntl
import json
import tempfile
import unittest
from unittest.mock import patch

from experiments.typed_decision import entry, relationship_assessment as rel, relationship_runtime as rt
from experiments.typed_decision.contracts import ContractError, DecisionResult, ResolvedRuntime, digest
from experiments.typed_decision.providers import FixtureProvider, ProviderError
from experiments.typed_decision.session import RecoveryRequired, read_record, write_once
from tests.test_relationship_assessment import packet, DEFAULT

REPO = Path(__file__).resolve().parents[1]


class Provider(FixtureProvider):
    def __init__(self, initial=None, revised=None):
        self.initial, self.revised = initial or {}, revised or {}
        super().__init__({'initial': self.initial, 'revised': self.revised})
        self.seen = []

    def evaluate(self, specs, context, timeout):
        self.seen.append(deepcopy(context))
        c = context['proposal_view']['candidate']
        new = c is not None and c['ref']['document_id'].startswith('R')
        overrides = self.revised if new else self.initial
        saved = self.answers
        self.answers = {s.id: overrides.get(s.id, overrides.get(s.id.split('.')[0],
                                      DEFAULT[s.id.split('.')[0]])) for s in specs}
        try:
            return super().evaluate(specs, context, timeout)
        finally:
            self.answers = saved


class Hook:
    is_live = False
    identity = 'original-host'

    def __init__(self, *, fail=None, mutate=None, text=None):
        self.text = text
        self.calls, self.requests = 0, []
        self.fail, self.mutate = fail, mutate

    def correct(self, request, timeout):
        self.calls += 1
        self.requests.append(deepcopy(request))
        if self.fail:
            raise self.fail
        text = self.text or '限定在当前对象：材料支持机制与任务约束共同控制结果，载体存在不等于整体解释充分。'
        version = 'revision-' + request['current_target']['version']
        document = {'id': request['revision_document_id'], 'revision': version, 'kind': 'candidate', 'text': text}
        old_id = request['original_input']['proposal']['candidate']['ref']['document_id']
        def rebind(x):
            if isinstance(x, dict):
                if set(x) == rel.REF_FIELDS and x['document_id'] == old_id:
                    return rel.quote(document)
                return {k: rebind(v) for k, v in x.items()}
            if isinstance(x, list):
                return [rebind(v) for v in x]
            return x
        proposal = rebind(request['original_input']['proposal'])
        proposal['candidate'] = {'ref': rel.quote(document), 'thesis_refs': [rel.quote(document)],
                                 'controller_refs': [rel.quote(document)], 'discriminator_refs': [rel.quote(document)]}
        reply = {'text': text, 'version': version, 'receipt_ref': 'fixture:host-revision',
                 'usage': deepcopy(rt.UNKNOWN_USAGE), 'proposal': proposal}
        if self.mutate:
            self.mutate(reply, request)
        return reply


class Organizer:
    is_live = False
    identity = 'original-host:organizer'

    def __init__(self, proposal):
        self.proposal = deepcopy(proposal)
        self.calls = 0

    def organize(self, request, timeout):
        self.calls += 1
        return {'proposal': deepcopy(self.proposal), 'receipt_ref': 'fixture:structure',
                'usage': deepcopy(rt.UNKNOWN_USAGE)}


def display_packet(*, buying=False, candidate='双方都有道理。'):
    """Authored historical display context, not current product advice or measured behavior."""
    d = packet(kind='decision', candidate=candidate)
    d['documents'][0]['text'] = (
        '我正在选购27英寸显示器，用Mac写代码办公，看重文字锐度也在意预算。请按这个处境给出有条件的选择。'
        if buying else '我已拥有27英寸4K显示器，只评价momo给的缩放建议是否有助于当前可用性，不让我重新购买。')
    d['documents'][1]['text'] = ('本离线夹具给定的历史场景材料：软件不能改变面板像素数；所给缩放方案改善了'
        '字号配置的可用性。若购前选择，还需按已给的锐度偏好和预算取舍，而不预设赢家。')
    ur, sr = rel.quote(d['documents'][0]), rel.quote(d['documents'][1])
    values = ['当前提问者', '购前显示器选择' if buying else 'momo对现有4K的可用性建议',
              '购前' if buying else '使用现有设备', '按锐度与预算选择' if buying else '评价当前补救是否有用',
              '当前购前判断' if buying else '不换成购前推荐']
    for k, value in zip(rel.FRAME_FIELDS, values):
        d['proposal']['frames'][0][k] = {'text':value,'origin':'explicit','refs':[ur]}
    d['proposal']['scope_correction_refs'] = []
    for claim, value in zip(d['proposal']['claims'], ['物理像素限制仍成立', '当前材料支持可用性改进']):
        claim.update(text=value,refs=[sr])
    d['activation']['source_refs'] = [ur]
    return d


class D2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.root = self.home / 'episode'
        self.registry = self.home / 'registry'
        self.patcher = patch.object(rt, '_registry', return_value=self.registry)
        self.patcher.start(); self.addCleanup(self.patcher.stop)
        self.data = packet(candidate='范围只谈Skills，本质仍然只是提示词。')
        self.provider = Provider({'definition': 'carrier_only_unjustified'})
        self.hook = Hook()

    def invoke(self, data=None, provider=None, hook='default', **options):
        hook = self.hook if hook == 'default' else hook
        return entry.run(self.root, provider or self.provider, data or self.data, REPO,
                         mode=rt.MODE, corrector=hook, **options)

    def records(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*.json')}

    def next_turn(self):
        data = deepcopy(self.data)
        data['turn_id'] = '3'
        data['documents'].append({'id': 'U3', 'revision': '1', 'kind': 'user',
                                  'text': '我仍说的是同一Skills，请接受范围纠正，但按材料判断。'})
        return data

    def test_public_entry_executes_one_correction_and_revision_recheck(self):
        r = self.invoke()
        self.assertEqual(r['status'], 'corrected_rechecked')
        self.assertEqual(r['episode_counts'], {'judgment': 2, 'correction': 1, 'organize': 0, 'total': 3})
        self.assertEqual(self.hook.calls, 1)
        self.assertTrue(r['scope_acceptance'])
        self.assertFalse(r['task_complete']); self.assertFalse(r['qualification'])
        self.assertNotIn('conclusion_acceptance', r)
        self.assertEqual(r['original_input'], self.data)
        self.assertEqual(r['revised_input']['documents'][:-1], self.data['documents'])
        self.assertEqual(r['revised_input']['authority'], self.data['authority'])
        self.assertEqual(r['revised_input']['stage'], 'S2')
        self.assertEqual(self.provider.seen[1]['proposal_view']['candidate']['ref']['document_id'],
                         r['revised_input']['documents'][-1]['id'])
        self.assertNotEqual(self.provider.seen[0]['proposal_view']['candidate'],
                            self.provider.seen[1]['proposal_view']['candidate'])

    def test_two_turn_skills_uses_same_episode_budget(self):
        self.invoke()
        r = self.invoke(self.next_turn())
        self.assertEqual(r['episode_counts']['total'], 6)
        self.assertEqual(r['episode_counts']['judgment'], 4)
        self.assertEqual(r['episode_counts']['correction'], 2)
        self.assertEqual(r['turn_counts']['correction'], 1)
        self.assertTrue(r['scope_acceptance'])
        self.assertEqual(self.hook.calls, 2)

    def test_new_evidence_after_exhaustion_returns_current_raw_not_old_answer(self):
        self.invoke(); self.invoke(self.next_turn())
        d = self.next_turn(); d['turn_id'] = '4'
        d['documents'].append({'id': 'S4', 'revision': '1', 'kind': 'source', 'text': '新的来源反证已到达。'})
        r = self.invoke(d)
        self.assertIn('budget_exhausted', r['reason'])
        self.assertEqual(r['original_input'], d)
        self.assertIsNone(r['revised_input'])
        self.assertEqual(len(self.provider.calls), 4)
        self.assertEqual(self.hook.calls, 2)
        self.assertEqual(r['host_followup_cost'], 'unknown')

    def test_completed_reentry_is_byte_identical_and_has_zero_new_calls(self):
        r = self.invoke(); before = self.records()
        self.assertEqual(self.invoke(), r)
        self.assertEqual(self.records(), before)
        self.assertEqual(len(self.provider.calls), 2); self.assertEqual(self.hook.calls, 1)

    def test_new_input_revision_does_not_reset_same_turn(self):
        self.invoke()
        d = deepcopy(self.data); d['revision'] = '2'
        d['documents'].append({'id': 'U2', 'revision': '1', 'kind': 'user', 'text': '语气更强但还是同一个问题。'})
        r = self.invoke(d)
        self.assertEqual(r['reason'], 'turn_judgment_budget_exhausted')
        self.assertEqual(len(self.provider.calls), 2)

    def test_same_turn_revision_with_new_bytes_is_rejected(self):
        self.invoke()
        d = deepcopy(self.data); d['activation']['reason'] += 'changed'
        with self.assertRaises(ContractError): self.invoke(d)
        self.assertEqual(self.hook.calls, 1)

    def test_same_episode_in_new_directory_cannot_reset(self):
        self.invoke(); self.root = self.home / 'different-root'
        with self.assertRaisesRegex(ContractError, 'episode_root_changed'): self.invoke()
        self.assertEqual(self.hook.calls, 1)

    def test_registry_detects_deleted_episode_ledger(self):
        self.invoke(); (self.root / 'manifest.json').unlink()
        with self.assertRaisesRegex(ContractError, 'ledger_missing'): self.invoke()

    def test_recheck_option_is_bound_and_optional(self):
        r = self.invoke(recheck=False)
        self.assertEqual(r['status'], 'corrected_unverified')
        self.assertEqual(r['action'], 'return_original_owner')
        self.assertEqual(len(self.provider.calls), 1)
        with self.assertRaises(ContractError): self.invoke(recheck=True)

    def test_same_turn_second_revision_cannot_repeat_correction(self):
        self.invoke(recheck=False)
        d = deepcopy(self.data); d['revision'] = '2'
        r = self.invoke(d, recheck=False)
        self.assertEqual(r['reason'], 'turn_correction_budget_exhausted')
        self.assertEqual(self.hook.calls, 1)

    def test_completed_judgment_outcome_without_report_is_reused(self):
        r = self.invoke(hook=None)
        self.assertEqual(r['status'], 'awaiting_corrector')
        for path in self.root.glob('turns/*/inputs/*/steps/initial/report.json'): path.unlink()
        r = self.invoke()
        self.assertEqual(r['status'], 'corrected_rechecked')
        self.assertEqual(len(self.provider.calls), 2)

    def test_completed_host_outcome_without_revision_or_summary_is_reused(self):
        r = self.invoke(recheck=False)
        for pattern in ('turns/*/inputs/*/summary.json', 'turns/*/inputs/*/revision.json'):
            for p in self.root.glob(pattern): p.unlink()
        rebuilt = self.invoke(hook=None, recheck=False)
        self.assertEqual(rebuilt, r)
        self.assertEqual(self.hook.calls, 1)

    def test_unknown_host_intent_never_resubmitted(self):
        hook = Hook(fail=KeyboardInterrupt())
        with self.assertRaises(KeyboardInterrupt): self.invoke(hook=hook)
        with self.assertRaises(RecoveryRequired): self.invoke(hook=hook)
        self.assertEqual(hook.calls, 1)

    def test_unknown_judgment_intent_never_resubmitted(self):
        with patch.object(self.provider, 'evaluate', side_effect=KeyboardInterrupt()) as method:
            with self.assertRaises(KeyboardInterrupt): self.invoke()
            with self.assertRaises(RecoveryRequired): self.invoke()
            self.assertEqual(method.call_count, 1)

    def test_unknown_anywhere_blocks_new_turn(self):
        with self.assertRaises(KeyboardInterrupt): self.invoke(hook=Hook(fail=KeyboardInterrupt()))
        with self.assertRaises(RecoveryRequired): self.invoke(self.next_turn())

    def test_host_exception_terminal_and_arbitrary_error_not_persisted(self):
        marker = 'secret-like arbitrary remote output'
        r = self.invoke(hook=Hook(fail=ValueError(marker)))
        self.assertEqual(r['reason'], 'correction_failed')
        self.assertNotIn(marker.encode(), b''.join(self.records().values()))
        next_r = self.invoke(self.next_turn())
        self.assertEqual(next_r['reason'], 'terminal_technical_failure')
        self.assertEqual(len(self.provider.calls), 1)

    def test_provider_failure_terminal_no_retry(self):
        with patch.object(self.provider, 'evaluate', side_effect=ProviderError('fixture_failure')) as method:
            r = self.invoke()
            self.invoke(self.next_turn())
            self.assertEqual(method.call_count, 1)
            self.assertEqual(r['action'], 'return_original_owner')

    def test_provider_configuration_drift_rejected_before_reuse(self):
        self.invoke()
        with self.assertRaises(ContractError): self.invoke(provider=Provider({'definition': 'account_missing'}))

    def test_profile_drift_rejected(self):
        self.invoke()
        with patch.dict(rt.PROFILE, {'total_requests': 8}):
            with self.assertRaises(ContractError): self.invoke()

    def test_different_episode_cannot_use_old_root(self):
        self.invoke(); d = deepcopy(self.data); d['episode_id'] = 'new-task'
        with self.assertRaises(ContractError): self.invoke(d)

    def test_live_provider_and_live_hook_rejected_without_journal(self):
        self.provider.is_live = True
        with self.assertRaises(ContractError): self.invoke()
        self.assertFalse(self.root.exists())
        self.provider.is_live = False; self.hook.is_live = True
        with self.assertRaises(ContractError): self.invoke()
        self.assertFalse(self.root.exists())

    def test_owner_mismatch_rejected_before_model_calls(self):
        self.hook.identity = 'other-owner'
        with self.assertRaises(ContractError): self.invoke()
        self.assertFalse(self.root.exists())

    def test_old_router_not_stacked(self):
        with self.assertRaises(ContractError): self.invoke(route=True)
        self.assertFalse(self.provider.calls)

    def test_old_mode_refuses_relationship_root(self):
        self.invoke()
        fixture = json.loads((REPO / 'experiments/typed_decision/fixtures/entry-correction.json').read_text())
        with self.assertRaises(ContractError):
            entry.run(self.root, entry.EntryFixtureProvider(fixture['answers']), fixture['input'], REPO)
        self.assertEqual(self.hook.calls, 1)

    def test_legacy_root_not_consumed_as_relationship_episode(self):
        self.root.mkdir(); write_once(self.root / 'manifest.json', {'schema': 'legacy-profile'})
        with self.assertRaises(ContractError): self.invoke()
        self.assertFalse(self.provider.calls)

    def test_concurrency_lock_blocks_without_provider_call(self):
        self.root.mkdir()
        with (self.root / '.entry-lock').open('a+b') as f:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(RecoveryRequired): self.invoke()
        self.assertFalse(self.provider.calls)

    def test_inactive_and_high_risk_never_call_organizer_or_models(self):
        for index, change in enumerate(('inactive', 'high', 'none')):
            self.root = self.home / ('case-' + change)
            d = deepcopy(self.data); d['episode_id'] = change; d['proposal'] = None
            if change == 'inactive': d['activation']['enabled'] = False
            elif change == 'high': d['authority']['risk'] = 'high'
            else: d['authority']['mode'] = 'none'
            org = Organizer(self.data['proposal'])
            r = self.invoke(d, organizer=org)
            self.assertEqual(r['action'], 'return_original_owner'); self.assertEqual(org.calls, 0)
        self.assertFalse(self.provider.calls)

    def test_no_candidate_does_not_generate_or_correct_answer(self):
        d = deepcopy(self.data); d['stage'] = 'S0'; d['proposal']['candidate'] = None
        r = self.invoke(d)
        self.assertIsNone(r['revised_input']); self.assertEqual(self.hook.calls, 0)
        self.assertFalse(any(s.startswith(('alignment.', 'delivery.', 'definition.')) for s in self.provider.calls[0]))

    def test_no_hit_does_not_rewrite_good_answer(self):
        provider = Provider()
        r = self.invoke(provider=provider)
        self.assertEqual(r['status'], 'assessment_complete'); self.assertEqual(self.hook.calls, 0)
        self.assertIsNone(r['revised_input'])

    def test_mapping_unknown_does_not_trigger_correction(self):
        r = self.invoke(provider=Provider({'q0': 'uncertain'}))
        self.assertEqual(r['action'], 'return_original_owner'); self.assertEqual(self.hook.calls, 0)
        self.assertFalse(any(row['consumed'] for row in r['matrix'] if row['id'] != 'q0'))

    def test_source_conflict_returns_owner(self):
        r = self.invoke(provider=Provider({'support': 'source_contradicted'}))
        self.assertEqual(r['reason'], 'source_or_verdict_contradiction'); self.assertEqual(self.hook.calls, 0)

    def test_remaining_defect_after_recheck_does_not_loop(self):
        provider = Provider({'definition': 'account_missing'}, {'definition': 'account_missing'})
        r = self.invoke(provider=provider)
        self.assertEqual(r['status'], 'returned_to_owner_after_recheck')
        self.assertEqual(self.hook.calls, 1); self.assertEqual(len(provider.calls), 2)

    def test_existing_obligation_survives_correction_and_recheck(self):
        d = deepcopy(self.data); d['authority']['known_obligations'] = ['original-owner-evidence-duty']
        r = self.invoke(d)
        self.assertEqual(r['status'], 'returned_to_owner_after_recheck')
        self.assertEqual(r['known_obligations'], d['authority']['known_obligations'])
        self.assertFalse(r['task_complete'])

    def test_display_joint_relationship_request_is_not_fixed_winner(self):
        d = display_packet(candidate='双方都有道理。')
        self.hook.text = '针对现有设备的可用性，给定材料中的缩放建议有帮助；这不等于改变物理像素限制，也不改成购前推荐。'
        p = Provider({'joint': 'joint_account_missing'})
        self.invoke(d, provider=p)
        kinds = [x['kind'] for x in self.hook.requests[0]['plan']['repair_relations']]
        self.assertEqual(kinds, ['explain_joint_relation'])
        self.assertNotIn('winner', self.hook.requests[0]['plan'])

    def test_conditional_display_delivery_is_preserved(self):
        d = display_packet(buying=True, candidate='按给定取舍：预算紧选A，更看重锐度且愿付溢价选B。')
        p = Provider({'readiness': 'conditional_decision', 'delivery': 'conditional_verdict',
                      'joint': 'conditional_branching'})
        r = self.invoke(d, provider=p)
        self.assertEqual(r['action'], 'continue_original'); self.assertEqual(self.hook.calls, 0)

    def test_revision_cannot_remove_checking_relationship(self):
        d = deepcopy(self.data)
        d['proposal']['edges'] = [{'id': 'E', 'frame_id': 'F0', 'premise_refs': [rel.quote(d['documents'][1])],
                                  'conclusion_refs': [rel.quote(d['documents'][2])]}]
        h = Hook(mutate=lambda reply, req: reply['proposal'].update(edges=[]))
        r = self.invoke(d, hook=h)
        self.assertEqual(r['reason'], 'correction_failed')
        self.assertEqual(len(self.provider.calls), 1)

    def test_revision_rebinds_existing_edges_to_new_candidate(self):
        d = deepcopy(self.data)
        d['proposal']['edges'] = [{'id': 'E', 'frame_id': 'F0', 'premise_refs': [rel.quote(d['documents'][1])],
                                  'conclusion_refs': [rel.quote(d['documents'][2])]}]
        r = self.invoke(d)
        edge = r['revised_input']['proposal']['edges'][0]
        self.assertEqual(edge['premise_refs'], d['proposal']['edges'][0]['premise_refs'])
        self.assertEqual(edge['conclusion_refs'][0]['document_id'], r['revised_input']['documents'][-1]['id'])

    def test_host_stale_candidate_references_fail_before_recheck(self):
        h = Hook(mutate=lambda reply, req: reply.update(proposal=deepcopy(req['original_input']['proposal'])))
        r = self.invoke(hook=h)
        self.assertEqual(r['reason'], 'correction_failed'); self.assertEqual(len(self.provider.calls), 1)

    def test_host_cannot_change_original_frame_or_source_claims(self):
        h = Hook(mutate=lambda reply, req: reply['proposal']['frames'][0]['goal'].update(text='new goal'))
        r = self.invoke(hook=h)
        self.assertEqual(r['reason'], 'correction_failed')
        self.assertEqual(r['original_input'], self.data)

    def test_missing_candidate_positions_do_not_get_invented(self):
        h = Hook(mutate=lambda reply, req: reply['proposal']['candidate'].update(controller_refs=[]))
        r = self.invoke(hook=h)
        self.assertEqual(r['reason'], 'reference_gap')
        self.assertEqual(r['status'], 'returned_to_owner_after_recheck')

    def test_invalid_host_usage_is_terminal(self):
        h = Hook(mutate=lambda reply, req: reply['usage'].update(input_tokens=-1))
        r = self.invoke(hook=h)
        self.assertEqual(r['reason'], 'correction_failed')

    def test_host_extra_evidence_payload_is_rejected(self):
        h = Hook(mutate=lambda reply, req: reply.update(new_evidence='pretended source'))
        r = self.invoke(hook=h)
        self.assertEqual(r['reason'], 'correction_failed')

    def test_organizer_is_counted_once_then_same_path_assesses_and_corrects(self):
        d = deepcopy(self.data); d['proposal'] = None
        org = Organizer(self.data['proposal'])
        r = self.invoke(d, organizer=org)
        self.assertEqual(r['episode_counts']['total'], 4)
        self.assertEqual(r['episode_counts']['organize'], 1)
        self.assertEqual(org.calls, 1); self.assertEqual(r['original_input'], d)
        self.assertIsNone(r['original_input']['proposal'])
        self.assertEqual(r['prepared_input']['documents'], d['documents'])
        self.assertEqual(self.invoke(d, organizer=org), r); self.assertEqual(org.calls, 1)

    def test_organizer_missing_hook_is_pending_without_calls(self):
        d = deepcopy(self.data); d['proposal'] = None
        r = self.invoke(d)
        self.assertEqual(r['status'], 'awaiting_structure'); self.assertFalse(self.provider.calls)
        r = self.invoke(d, organizer=Organizer(self.data['proposal']))
        self.assertEqual(r['status'], 'corrected_rechecked')

    def test_organizer_allowance_shared_across_turns(self):
        d = deepcopy(self.data); d['proposal'] = None
        org = Organizer(self.data['proposal']); self.invoke(d, organizer=org)
        d['turn_id'] = '3'
        r = self.invoke(d, organizer=org)
        self.assertEqual(r['reason'], 'episode_organize_budget_exhausted'); self.assertEqual(org.calls, 1)

    def test_seven_requests_maximum_two_turns_with_one_organizer(self):
        d = deepcopy(self.data); d['proposal'] = None
        self.invoke(d, organizer=Organizer(self.data['proposal']))
        r = self.invoke(self.next_turn())
        self.assertEqual(r['episode_counts']['total'], 7)
        d = self.next_turn(); d['turn_id'] = '4'
        r = self.invoke(d)
        self.assertEqual(r['episode_counts']['total'], 7)
        self.assertIn('budget_exhausted', r['reason'])

    def test_organizer_cannot_submit_extra_answer_key(self):
        org = Organizer(self.data['proposal'])
        org.proposal['expected_answer'] = 'fixed winner'
        d = deepcopy(self.data); d['proposal'] = None
        r = self.invoke(d, organizer=org)
        self.assertEqual(r['reason'], 'organizer_failed'); self.assertFalse(self.provider.calls)

    def test_provider_unknown_status_retained_not_false_negative(self):
        p = Provider({'definition': asdict(DecisionResult('abstain', reason='fixture'))})
        r = self.invoke(provider=p)
        self.assertEqual(r['reason'], 'unresolved_evaluation'); self.assertEqual(self.hook.calls, 0)

    def test_raw_input_s2_cannot_bypass_turn_budget(self):
        d = deepcopy(self.data); d['stage'] = 'S2'
        with self.assertRaises(ContractError): self.invoke(d)

    def test_local_source_drift_is_rejected_before_resume(self):
        self.invoke()
        with patch.object(rel, 'load_contract', side_effect=ContractError('canonical_source_changed')):
            with self.assertRaises(ContractError): self.invoke()
        self.assertEqual(len(self.provider.calls), 2)

    def test_unknown_mode_and_legacy_relationship_options_rejected(self):
        with self.assertRaises(ContractError):
            entry.run(self.root, self.provider, self.data, REPO, mode='unknown')
        with self.assertRaises(ContractError):
            entry.run(self.root, self.provider, self.data, REPO, organizer=Organizer(self.data['proposal']))

    def test_late_host_return_is_terminal_and_time_is_charged(self):
        class Clock:
            now = 0.0
            @classmethod
            def monotonic(cls): return cls.now
        h = Hook(mutate=lambda reply, req: setattr(Clock, 'now', Clock.now + 46))
        with patch.object(rt, 'time', Clock):
            r = self.invoke(hook=h)
        self.assertEqual(r['reason'], 'correction_failed')
        self.assertGreaterEqual(r['recorded_request_seconds'], 46)
        self.assertEqual(len(self.provider.calls), 1)

    def test_cumulative_time_loaded_from_records_not_reset_on_reentry(self):
        self.invoke(recheck=False)
        op = next(self.root.glob('turns/*/inputs/*/steps/correction/outcome.json'))
        payload = read_record(op)
        payload['elapsed_seconds'] = 120.0  # Deliberate synthetic elapsed-time fault.
        op.unlink(); write_once(op, payload)
        r = self.invoke(self.next_turn())
        self.assertEqual(r['reason'], 'request_time_budget_exhausted')
        self.assertEqual(len(self.provider.calls), 1)
        self.assertEqual(self.hook.calls, 1)

    def test_recheck_unresolved_intent_is_not_sent_again(self):
        real = self.provider.evaluate
        def crash_on_revision(specs, context, timeout):
            if context['proposal_view']['candidate']['ref']['document_id'].startswith('R'):
                raise KeyboardInterrupt()
            return real(specs, context, timeout)
        with patch.object(self.provider, 'evaluate', side_effect=crash_on_revision) as method:
            with self.assertRaises(KeyboardInterrupt): self.invoke()
            with self.assertRaises(RecoveryRequired): self.invoke()
            self.assertEqual(method.call_count, 2)
        self.assertEqual(self.hook.calls, 1)

    def test_resolved_runtime_drift_is_terminal_across_turns(self):
        class Drift(Provider):
            def validate_runtime(self, runtime): runtime.validate()
            def evaluate(self, specs, context, timeout):
                b = super().evaluate(specs, context, timeout)
                if len(self.calls) > 2:
                    b.resolved_runtime = ResolvedRuntime('other-fixture', 'offline-fixture')
                return b
        p = Drift({'definition': 'account_missing'})
        self.invoke(provider=p)
        r = self.invoke(self.next_turn(), provider=p)
        self.assertEqual(r['action'], 'return_original_owner')
        self.assertEqual(self.hook.calls, 1)
        out = [read_record(x) for x in self.root.glob('turns/*/inputs/*/steps/initial/calls/*/outcome.json')]
        self.assertTrue(any(any(y['status']=='provider_error' for y in x['results'].values()) for x in out))

    def test_oversized_raw_input_returns_owner_without_any_invocation(self):
        d = deepcopy(self.data)
        d['documents'].append({'id':'Huge','revision':'1','kind':'source','text':'x' * 32768})
        r = self.invoke(d)
        self.assertEqual(r['reason'], 'coverage_overflow:input_bytes')
        self.assertEqual(r['original_input'], d)
        self.assertFalse(self.provider.calls); self.assertFalse(self.root.exists())

    def test_unknown_organizer_intent_not_retried(self):
        d = deepcopy(self.data); d['proposal'] = None
        o = Organizer(self.data['proposal'])
        with patch.object(o, 'organize', side_effect=KeyboardInterrupt()) as method:
            with self.assertRaises(KeyboardInterrupt): self.invoke(d, organizer=o)
            with self.assertRaises(RecoveryRequired): self.invoke(d, organizer=o)
            self.assertEqual(method.call_count, 1)
        self.assertFalse(self.provider.calls)

    def test_completed_organizer_outcome_without_prepared_report_is_reused(self):
        d = deepcopy(self.data); d['proposal'] = None
        o = Organizer(self.data['proposal'])
        self.invoke(d, organizer=o, hook=None)
        for p in self.root.glob('turns/*/inputs/*/prepared.json'): p.unlink()
        r = self.invoke(d, hook=self.hook)
        self.assertEqual(r['status'], 'corrected_rechecked'); self.assertEqual(o.calls, 1)

    def test_revised_source_declarations_cannot_upgrade_user_hypothesis(self):
        h = Hook(mutate=lambda reply, req: reply['proposal']['claims'][0].update(origin='host_interpretation'))
        r = self.invoke(hook=h)
        self.assertEqual(r['reason'], 'correction_failed')

    def test_missing_controller_refs_not_silently_filled_by_runtime(self):
        h = Hook(mutate=lambda reply, req: reply['proposal']['candidate'].update(controller_refs=[]))
        r = self.invoke(hook=h, recheck=False)
        self.assertEqual(r['status'], 'corrected_unverified')
        self.assertEqual(r['revised_input']['proposal']['candidate']['controller_refs'], [])

    def test_partial_candidate_span_preserves_original_document(self):
        d = deepcopy(self.data)
        doc = d['documents'][2]; doc['text'] = '前缀。' + doc['text'] + '后缀。'
        q = rel.quote(doc,3,len(doc['text'])-3)
        d['proposal']['candidate'] = {'ref':q,'thesis_refs':[q],'controller_refs':[q],'discriminator_refs':[q]}
        r = self.invoke(d)
        self.assertEqual(r['revised_input']['documents'][2], doc)
        self.assertEqual(self.hook.requests[0]['current_target']['text'], doc['text'][3:-3])

    def test_public_cli_relationship_mode_and_replay(self):
        import contextlib, io
        c = rel.compile_packet(self.data, REPO)
        original = {s.id:DEFAULT[s.id.split('.')[0]] for s in c.specs}
        original['definition.F0'] = 'carrier_only_unjustified'
        report = {'result':rel.consume(c, {'identity':c.identity,'results':{
            k:asdict(DecisionResult('ok',v)) for k,v in original.items()}}, REPO)}
        request = rt.correction_request(self.data, report)
        reply = Hook().correct(request,45)
        revised = rt.revision_packet(request, reply, REPO)
        c2 = rel.compile_packet(revised, REPO)
        fixture = {'input':self.data,'correction':reply,'answers':{'initial':original,
            'by_target_version':{reply['version']:{s.id:DEFAULT[s.id.split('.')[0]] for s in c2.specs}}}}
        file = self.home/'fixture.json'; file.write_text(json.dumps(fixture,ensure_ascii=False))
        args = ['--mode',rt.MODE,'--fixture',str(file),'--state-root',str(self.root)]
        buf=io.StringIO()
        with contextlib.redirect_stdout(buf): code=entry.main(args)
        self.assertEqual(code,0); output=json.loads(buf.getvalue())
        self.assertEqual(output['status'],'corrected_rechecked')
        before=self.records(); buf=io.StringIO()
        with contextlib.redirect_stdout(buf): self.assertEqual(entry.main(args),0)
        self.assertEqual(json.loads(buf.getvalue()),output); self.assertEqual(self.records(),before)

    def test_registry_shared_between_git_worktrees(self):
        common = '/tmp/shared-git-common-dir'
        self.patcher.stop()
        try:
            with patch.object(rt.subprocess,'check_output',return_value=common):
                self.assertEqual(rt._registry(Path('/repo/worktree-A')),rt._registry(Path('/repo/worktree-B')))
        finally:
            self.patcher.start()

    def test_original_task_and_constraint_change_remains_visible_after_exhaustion(self):
        self.invoke(); self.invoke(self.next_turn())
        d=self.next_turn(); d['turn_id']='4'; d['authority']['mode']='read_only'
        d['documents'].append({'id':'New','revision':'1','kind':'user','text':'仅检查，不作修改。'})
        r=self.invoke(d)
        self.assertEqual(r['original_input']['authority']['mode'],'read_only')
        self.assertIsNone(r['revised_input']); self.assertEqual(self.hook.calls,2)



if __name__ == '__main__':
    unittest.main()
