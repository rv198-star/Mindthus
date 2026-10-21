"""H1-C2 failure-first synthetic Host tests. No real DSH/Web/IM authentication."""
import base64
import copy
import unittest
from unittest.mock import patch
from tests.tplan import test_h1_core as core
from tests.tplan.h1_test_host import acceptance_receipt, isolated_test_host, signed, host_request
from tests.tplan import test_h1_kernel_gate as fixtures
import tplan_runtime as runtime


class H1CompletionTests(core.H1CoreTests):
    def claim(self):
        self.source = self.ready()
        return self.call('execution.claim', self.claim_payload())

    def result_payload(self, slot, **changes):
        value = {'slot_id': slot['slot_id'], 'session_id': slot['session_id'],
                 'native_request_id': slot['native_request_id'], 'attempt_ref': slot['intent_id'],
                 'receipt_ref': 'native-delivered-1',
                 'content_b64': base64.b64encode(b'actual business result B').decode()}
        value.update(changes)
        return value

    def deliver(self, slot=None):
        slot = slot or self.claim()
        self.call('result.record', self.result_payload(slot))
        return self.call('execution.get', {'slot_id': slot['slot_id']})

    def review(self, slot, **changes):
        return acceptance_receipt(runtime.read_mission(self.mission), slot, **changes)

    def reject(self, action, payload, code=None):
        before = runtime.read_mission(self.mission)
        evidence = (self.mission / 'evidence.jsonl').read_bytes()
        with isolated_test_host():
            result, status = self.api.execute(self.mission, self.request(action, payload))
        self.assertNotEqual(status, 0, result)
        if code:
            self.assertEqual(result['code'], code, result)
        self.assertEqual(runtime.read_mission(self.mission), before)
        self.assertEqual((self.mission / 'evidence.jsonl').read_bytes(), evidence)
        return result

    def test_completion_01_delivered_is_not_accepted_and_C_continues(self):
        slot = self.claim()
        self.call('receipt.record', {'slot_id': slot['slot_id'], 'status': 'delivered',
                                    'receipt_ref': 'technical-delivery'})
        state = runtime.read_mission(self.mission)
        self.assertEqual(runtime.find_task(state, 'B')['status'], 'pending')
        self.assertTrue(runtime._mission_completion_findings(state, runtime.read_events(self.mission)))
        runtime.transition_task_status(self.mission, 'C', 'active')
        self.reject('task.complete', {'receipt': {'principal': 'reviewer', 'summary': 'looks good'}})
        with self.assertRaises(runtime.TplanError):
            runtime.transition_task_status(self.mission, 'B', 'completed')

    def test_completion_02_real_bytes_review_and_original_mission_close(self):
        slot = self.deliver()
        self.assertEqual(runtime.find_task(runtime.read_mission(self.mission), 'B')['status'], 'pending')
        result = self.call('task.complete', {'receipt': self.review(slot)})
        state = runtime.read_mission(self.mission)
        self.assertEqual(runtime.find_task(state, 'B')['status'], 'completed')
        self.assertEqual(runtime.find_task(state, 'C')['status'], 'pending')
        event = next(e for e in runtime.read_events(self.mission) if e['id'] == result['evidence_id'])
        self.assertEqual(event['event_type'], 'acceptance_passed')
        self.assertEqual(event['payload']['result_sha256'], slot['result_sha256'] if 'result_sha256' in slot else
                         state['human_control']['candidates'][slot['result']['candidate_id']]['content_sha256'])
        runtime.transition_task_status(self.mission, 'C', 'completed')
        before = runtime.read_mission(self.mission); after = copy.deepcopy(before)
        after['mission']['status'] = 'completed'
        runtime.commit_mission_state(self.mission, before, after,
                                    source={'kind': 'runtime_script', 'name': 'original-mission-close'})
        self.assertEqual(runtime.read_mission(self.mission)['mission']['status'], 'completed')

    def test_completion_03_replay_and_different_command_conflict(self):
        slot = self.deliver()
        request = self.request('task.complete', {'receipt': self.review(slot)})
        with isolated_test_host():
            first, code = self.api.execute(self.mission, request)
            self.assertEqual(code, 0, first)
            before = (self.mission / 'evidence.jsonl').read_bytes()
            replay, code = self.api.execute(self.mission, request)
            self.assertEqual(code, 0, replay)
            self.assertEqual(replay['status'], 'replayed')
            self.assertEqual(first['data'], replay['data'])
            changed = copy.deepcopy(request); changed['payload']['receipt']['summary'] = 'changed'
            self.assertEqual(self.api.execute(self.mission, changed)[0]['code'], 'command_conflict')
        self.reject('task.complete', request['payload'], 'command_conflict')
        self.assertEqual((self.mission / 'evidence.jsonl').read_bytes(), before)

    def test_completion_04_wrong_native_result_binding(self):
        slot = self.claim()
        for changes in ({'slot_id': 'wrong'}, {'session_id': 'wrong'},
                        {'native_request_id': 'wrong'}, {'attempt_ref': 'wrong'},
                        {'content_b64': '!!'}, {'content_b64': ''}):
            with self.subTest(changes=changes):
                self.reject('result.record', self.result_payload(slot, **changes))
        self.deliver(slot)
        self.reject('result.record', self.result_payload(slot), 'command_conflict')
        self.reject('result.record', self.result_payload(slot, content_b64=base64.b64encode(b'other').decode()),
                    'command_conflict')

    def test_completion_05_signed_wrong_scope_actor_criteria_and_evidence(self):
        slot = self.deliver()
        bad = [dict(task_id='C'), dict(slot_id='missing'), dict(session_id='wrong'),
               dict(native_request_id='wrong'), dict(attempt_ref='wrong'), dict(candidate_id='wrong'),
               dict(result_sha256='sha256:'+'0'*64), dict(expected_revision=9), dict(expected_revision=True),
               dict(decision_id='wrong'), dict(adopted_candidate_id='wrong'), dict(request_id='wrong'),
               dict(input_digest='sha256:'+'1'*64), dict(dependency_digest='sha256:'+'1'*64),
               dict(delivery_digest='sha256:'+'1'*64), dict(actor_subject_ref='model'),
               dict(origin_binding_ref='wrong'), dict(origin_session_ref='wrong'), dict(origin_event_ref=''),
               dict(acceptance_ids=[]), dict(acceptance_ids=['unknown']), dict(acceptance_ids=['A1','A1']),
               dict(acceptance_contract_digest='sha256:'+'0'*64), dict(evidence_refs=[]),
               dict(evidence_refs=['x','x']), dict(summary=''), dict(summary='review\nforged'),
               dict(issued_at=1, expires_at=2), dict(secret='chosen'), dict(key_path='/tmp/key'),
               dict(issuer_id='model'), dict(schema_version='owner')]
        for changes in bad:
            with self.subTest(changes=changes):
                self.reject('task.complete', {'receipt': self.review(slot, **changes)})
        receipt = self.review(slot); receipt['signature'] = '0'*64
        self.reject('task.complete', {'receipt': receipt}, 'unauthorized')
        # Review references a delivery that is not canonically recorded yet.
        state = runtime.read_mission(self.mission)
        before = copy.deepcopy(state)
        state['human_control']['execution_slots'][slot['slot_id']].pop('result')
        # Only a synthetic internal fixture may remove a protected fact.
        with runtime.execution_trace_lock(self.mission):
            runtime._commit_mission_state_unlocked(self.mission, before, state,
                source={'kind':'runtime_script','name':'missing-result-fixture'},
                h1_control_authority=runtime._H1_CONTROL_AUTHORITY)
        self.reject('task.complete', {'receipt': self.review(slot)})

    def test_completion_06_missing_or_tampered_result_bytes(self):
        slot = self.deliver()
        receipt = self.review(slot)
        state = runtime.read_mission(self.mission)
        candidate = state['human_control']['candidates'][slot['result']['candidate_id']]
        path = self.mission / candidate['bytes_ref']
        path.chmod(0o600); path.write_bytes(b'tampered')
        self.reject('task.complete', {'receipt': receipt}, 'candidate_unavailable')
        path.unlink()
        self.reject('task.complete', {'receipt': receipt}, 'candidate_unavailable')

    def test_completion_07_owner_revision_invalidates_old_slot_not_delivery(self):
        slot = self.deliver(); receipt = self.review(slot)
        self.approve(self.source, revision=2, choice='withdraw_change', nonce='changed-owner')
        self.call('adoption.apply', {'request_id':'HR1','candidate_id':self.source['candidate_id']})
        self.reject('task.complete', {'receipt': receipt}, 'stale_revision')
        current = self.call('execution.get', {'slot_id':slot['slot_id']})
        self.assertEqual(current['result'], slot['result'])

    def test_completion_08_source_failure_blocks_acceptance(self):
        slot = self.deliver(); receipt = self.review(slot)
        runtime.append_event(self.mission, {'event_type':'acceptance_failed','task_id':'A',
            'summary':'Source invalidated after native delivery',
            'payload':{'acceptance_ids':['A1'],'candidate_sha256':self.source['content_sha256']}})
        self.reject('task.complete', {'receipt':receipt})

    def test_completion_09_terminal_late_result_only(self):
        slot = self.claim()
        before = runtime.read_mission(self.mission); after = copy.deepcopy(before)
        after['mission']['status'] = 'abandoned'
        runtime.commit_mission_state(self.mission,before,after,
                                    source={'kind':'runtime_script','name':'terminal'})
        slot = self.deliver(slot)
        self.reject('task.complete', {'receipt':self.review(slot)}, 'terminal')
        state = runtime.read_mission(self.mission)
        self.assertEqual(state['mission']['status'],'abandoned')
        self.assertEqual(runtime.find_task(state,'B')['status'],'pending')

    def test_completion_10_prepared_crash_interrupted_recovery_and_response_loss(self):
        slot = self.deliver(); request = self.request('task.complete', {'receipt':self.review(slot)})
        self.assertEqual(self.worker_result(self.spawn_worker(request,'prepared'))[0],91)
        self.assertTrue((self.mission/'.mission-transaction.json').exists())
        with isolated_test_host():
            self.assertEqual(self.api.execute(self.mission,request)[1],4)
        original = runtime.write_json
        def interrupt(path,*args,**kwargs):
            if path.name == 'mission.json':
                raise OSError('synthetic interrupted recovery')
            return original(path,*args,**kwargs)
        with patch.object(runtime,'write_json',side_effect=interrupt):
            self.assertNotEqual(self.recover(request['command_id'])[1],0)
        self.assertEqual(self.recover(request['command_id'])[1],0)
        with isolated_test_host():
            replay,code = self.api.execute(self.mission,request)
        self.assertEqual(code,0,replay); self.assertEqual(replay['status'],'replayed')
        passes = [e for e in runtime.read_events(self.mission) if e['task_id']=='B' and e['event_type']=='acceptance_passed']
        self.assertEqual(len(passes),1)
        self.assertEqual(runtime.find_task(runtime.read_mission(self.mission),'B')['status'],'completed')
        self.assertEqual(self.worker_result(self.spawn_worker(request,'response'))[0],93)
        self.assertEqual(len([e for e in runtime.read_events(self.mission) if e['task_id']=='B']),1)

    def test_completion_11_legacy_and_reserved_evidence_cannot_bypass(self):
        slot = self.deliver()
        event = runtime.prepare_event(self.mission, {'event_type':'acceptance_passed','task_id':'B',
            'summary':'Model claims reviewer accepted','payload':{'acceptance_ids':['A1']}})
        before = runtime.read_mission(self.mission)
        for authority in (None, runtime._RESERVED_EVIDENCE_AUTHORITY):
            with self.subTest(authority=authority):
                with self.assertRaises(runtime.TplanError):
                    with runtime.execution_trace_lock(self.mission):
                        runtime._commit_mission_state_unlocked(self.mission,before,copy.deepcopy(before),
                            source={'kind':'runtime_script','name':'legacy-fake'},
                            prepared_evidence_events=[event], reserved_evidence_authority=authority)
        self.call('task.complete', {'receipt':self.review(slot)})
        with self.assertRaises(runtime.TplanError):
            runtime.append_event(self.mission,event)

    def test_completion_12_shipped_host_remains_disabled(self):
        slot = self.deliver(); request = self.request('task.complete', {'receipt':self.review(slot)})
        self.assertIsNone(self.api._trust_config())
        result,code = self.api.execute(self.mission,request)
        self.assertEqual(result['code'],'host_disabled'); self.assertNotEqual(code,0)

    def test_completion_13_failed_B_acceptance_blocks_mission_close(self):
        slot = self.deliver(); self.call('task.complete', {'receipt':self.review(slot)})
        runtime.append_event(self.mission, {'event_type':'acceptance_failed','task_id':'B',
            'summary':'Reviewer later invalidated B','payload':{'acceptance_ids':['A1']}})
        runtime.transition_task_status(self.mission,'C','completed')
        # Unrelated pass cannot hide B failure even when it shares the Mission AC.
        runtime.append_event(self.mission, {'event_type':'acceptance_passed','task_id':'C',
            'summary':'Independent C passes','payload':{'acceptance_ids':['A1']}})
        state = runtime.read_mission(self.mission)
        self.assertTrue(runtime._mission_completion_findings(state,runtime.read_events(self.mission)))


for _name in dir(core.H1CoreTests):
    if _name.startswith('test_'):
        setattr(H1CompletionTests, _name, None)

if __name__ == '__main__':
    unittest.main()
