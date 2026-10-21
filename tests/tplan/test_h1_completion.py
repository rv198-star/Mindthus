"""H1-C2 failure-first synthetic Host tests. No real DSH/Web/IM authentication."""
import base64
import copy
import json
import unittest
from unittest.mock import patch
from tests.tplan import test_h1_core as core
from tests.tplan.h1_test_host import acceptance_receipt, isolated_test_host
import tplan_runtime as runtime


class H1CompletionTests(core.H1CoreTests):
    def setUp(self):
        super().setUp()
        before = runtime.read_mission(self.mission); after = copy.deepcopy(before)
        after['mission']['acceptance_evidence'] = [
            {'id':'A1','description':'Source A bytes verified'},
            {'id':'A2','description':'B delivers the required business result'},
            {'id':'A3','description':'Independent C is complete'}]
        for task_id, ac in [('A','A1'),('B','A2'),('C','A3')]:
            runtime.find_task(after,task_id)['acceptance_evidence'] = [ac]
        runtime.commit_mission_state(self.mission,before,after,
            source={'kind':'runtime_script','name':'synthetic-distinct-business-criteria'})

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
        self.assertEqual(event['payload']['result_sha256'], state['human_control']['candidates'][slot['result']['candidate_id']]['content_sha256'])
        self.assertEqual(event['payload']['acceptance_ids'], ['A2'])
        runtime.transition_task_status(self.mission, 'C', 'completed')
        runtime.append_event(self.mission, {'event_type':'acceptance_passed','task_id':'C',
            'summary':'Independent C meets its own criterion','payload':{'acceptance_ids':['A3']}})
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
               dict(acceptance_ids=[]), dict(acceptance_ids=['unknown']), dict(acceptance_ids=['A2','A2']),
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
            'summary':'Model claims reviewer accepted','payload':{'acceptance_ids':['A2']}})
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
            'summary':'Reviewer later invalidated B','payload':{'acceptance_ids':['A2']}})
        runtime.transition_task_status(self.mission,'C','completed')
        # Unrelated pass cannot hide B failure.
        runtime.append_event(self.mission, {'event_type':'acceptance_passed','task_id':'C',
            'summary':'Independent C passes','payload':{'acceptance_ids':['A3']}})
        state = runtime.read_mission(self.mission)
        self.assertTrue(runtime._mission_completion_findings(state,runtime.read_events(self.mission)))

    def test_completion_14_current_adoption_and_fixed_actor_required(self):
        slot = self.deliver(); receipt = self.review(slot)
        from tests.tplan.h1_test_host import TEST_TRUST
        trust = copy.deepcopy(TEST_TRUST); trust.pop('acceptance_actors')
        with patch.object(self.api,'_trust_config',return_value=trust):
            result,code = self.api.execute(self.mission,self.request('task.complete',{'receipt':receipt}))
        self.assertNotEqual(code,0,result); self.assertEqual(result['code'],'unauthorized')
        before = runtime.read_mission(self.mission); after = copy.deepcopy(before)
        after['human_control']['adoptions'].clear()
        with runtime.execution_trace_lock(self.mission):
            runtime._commit_mission_state_unlocked(self.mission,before,after,
                source={'kind':'runtime_script','name':'synthetic-current-adoption-removed'},
                h1_control_authority=runtime._H1_CONTROL_AUTHORITY)
        self.reject('task.complete', {'receipt':receipt}, 'waiting')

    def test_completion_15_consumed_review_event_or_nonce_cannot_be_reused(self):
        from tplan_commands import digest
        slot = self.deliver(); receipt = self.review(slot)
        before = runtime.read_mission(self.mission)
        for key in (self.api._nonce_key(receipt,'acceptance'),
                    digest({'kind':'acceptance_event','issuer':receipt['issuer_id'],
                            'event':receipt['origin_event_ref']})):
            after = copy.deepcopy(before)
            after['human_control']['used_nonces'][key] = 'cmd-1'
            current = runtime.read_mission(self.mission)
            with runtime.execution_trace_lock(self.mission):
                runtime._commit_mission_state_unlocked(self.mission,current,after,
                    source={'kind':'runtime_script','name':'synthetic-previous-review-event'},
                    h1_control_authority=runtime._H1_CONTROL_AUTHORITY)
            self.reject('task.complete', {'receipt':receipt}, 'replay')

    def test_completion_16_completion_evidence_integrity_at_original_close(self):
        slot = self.deliver(); result = self.call('task.complete', {'receipt':self.review(slot)})
        runtime.transition_task_status(self.mission,'C','completed')
        runtime.append_event(self.mission, {'event_type':'acceptance_passed','task_id':'C',
            'summary':'C passes','payload':{'acceptance_ids':['A3']}})
        state = runtime.read_mission(self.mission); events = runtime.read_events(self.mission)
        self.assertFalse(runtime._mission_completion_findings(state,events))
        missing = [e for e in events if e['id'] != result['evidence_id']]
        self.assertTrue(runtime._mission_completion_findings(state,missing))
        tampered = copy.deepcopy(events)
        next(e for e in tampered if e['id']==result['evidence_id'])['payload']['evidence_refs']=['forged']
        self.assertTrue(runtime._mission_completion_findings(state,tampered))
        duplicate = events + [next(e for e in events if e['id']==result['evidence_id'])]
        self.assertTrue(runtime._mission_completion_findings(state,duplicate))

    def completed_business_with_late_source(self):
        slot = self.deliver()
        self.call('task.complete', {'receipt':self.review(slot)})
        runtime.transition_task_status(self.mission,'C','completed')
        runtime.append_event(self.mission, {'event_type':'acceptance_passed','task_id':'C',
            'summary':'Independent C meets its own criterion','payload':{'acceptance_ids':['A3']}})
        return self.call('candidate.submit', {'task_id':'A','attempt_ref':'A-2',
            'content_b64':base64.b64encode(b'late unadopted A v2').decode()})

    def test_completion_17_adopted_source_failure_not_hidden_by_other_version_pass(self):
        v2 = self.completed_business_with_late_source()
        runtime.append_event(self.mission, {'event_type':'acceptance_failed','task_id':'A',
            'summary':'Adopted A v1 failed after B completed',
            'payload':{'acceptance_ids':['A1'],'candidate_sha256':self.source['content_sha256'],
                       'attempt_ref':self.source['attempt_ref']}})
        self.accept_candidate(v2)
        before = runtime.read_mission(self.mission)
        self.assertTrue(self.api._source_failure(self.mission,before,self.source,runtime))
        self.assertTrue(runtime._mission_completion_findings(before,runtime.read_events(self.mission)))
        after = copy.deepcopy(before); after['mission']['status'] = 'completed'
        with self.assertRaises(runtime.TplanError):
            runtime.commit_mission_state(self.mission,before,after,
                source={'kind':'runtime_script','name':'close-rejected-adopted-v1'})
        self.assertEqual(runtime.read_mission(self.mission),before)
        runtime.append_event(self.mission, {'event_type':'observation','task_id':'C',
            'summary':'C remains independently writable after rejected close'})
        self.assertEqual(runtime.find_task(runtime.read_mission(self.mission),'C')['status'],'completed')

    def test_completion_18_other_source_version_failure_does_not_invalidate_adoption(self):
        v2 = self.completed_business_with_late_source()
        self.accept_candidate(v2)
        runtime.append_event(self.mission, {'event_type':'acceptance_failed','task_id':'A',
            'summary':'Only unadopted A v2 failed after B completed',
            'payload':{'acceptance_ids':['A1'],'candidate_sha256':v2['content_sha256'],
                       'attempt_ref':v2['attempt_ref']}})
        before = runtime.read_mission(self.mission)
        self.assertIsNone(self.api._source_failure(self.mission,before,self.source,runtime))
        self.assertFalse(runtime._mission_completion_findings(before,runtime.read_events(self.mission)))
        after = copy.deepcopy(before); after['mission']['status'] = 'completed'
        runtime.commit_mission_state(self.mission,before,after,
            source={'kind':'runtime_script','name':'close-still-qualified-adopted-v1'})
        state = runtime.read_mission(self.mission)
        self.assertEqual(state['mission']['status'],'completed')
        self.assertEqual(state['human_control']['adoptions']['HR1']['candidate_id'],self.source['candidate_id'])
        self.assertEqual(runtime.find_task(state,'C')['status'],'completed')

    def test_completion_19_evidence_limit_rejects_without_consuming_authority(self):
        slot = self.deliver()
        request = self.request('task.complete', {'receipt':self.review(slot)})
        evidence_path = self.mission/'evidence.jsonl'
        padding = runtime.prepare_event(self.mission, {'id':'near-evidence-limit',
            'event_type':'observation','task_id':'C','summary':'Synthetic bounded capacity fixture',
            'payload':{'padding':''}})
        base_bytes = len(json.dumps(padding,ensure_ascii=False).encode()) + 1
        padding['payload']['padding'] = 'x' * (self.api.MAX_ARTIFACT - 1 - evidence_path.stat().st_size - base_bytes)
        runtime.append_event(self.mission,padding)
        self.assertEqual(evidence_path.stat().st_size,self.api.MAX_ARTIFACT - 1)
        before = {name:(self.mission/name).read_bytes()
                  for name in ('mission.json','evidence.jsonl','execution_trace.jsonl')}
        with isolated_test_host():
            result,code = self.api.execute(self.mission,request)
        self.assertEqual(result['code'],'capacity_exceeded',result)
        self.assertNotEqual(code,0,result)
        self.assertEqual({name:(self.mission/name).read_bytes() for name in before},before)
        state = json.loads(before['mission.json'])
        self.assertEqual(runtime.read_mission(self.mission),state)
        self.assertNotIn(request['command_id'],state['human_control']['commands'])
        for kind,receipt in [('host',request['host_receipt']),('acceptance',request['payload']['receipt'])]:
            self.assertNotIn(self.api._nonce_key(receipt,kind),state['human_control']['used_nonces'])
        self.assertFalse((self.mission/'.mission-transaction.json').exists())
        self.assertEqual(self.recover('capacity-recovery-check')[1],0)
        current = self.call('execution.get', {'slot_id':slot['slot_id']})
        self.assertNotIn('completion',current)

    def test_completion_20_source_projection_preserves_unrelated_shared_AC_failure(self):
        before = runtime.read_mission(self.mission); after = copy.deepcopy(before)
        runtime.find_task(after,'C')['acceptance_evidence'].append('A1')
        runtime.commit_mission_state(self.mission,before,after,
            source={'kind':'runtime_script','name':'synthetic-shared-source-C-criterion'})
        v2 = self.completed_business_with_late_source()
        self.accept_candidate(v2)
        runtime.append_event(self.mission, {'event_type':'acceptance_failed','task_id':'C',
            'summary':'Independent C failed its shared A1 criterion',
            'payload':{'acceptance_ids':['A1']}})
        state = runtime.read_mission(self.mission)
        self.assertIsNone(self.api._source_failure(self.mission,state,self.source,runtime))
        self.assertTrue(runtime._mission_completion_findings(state,runtime.read_events(self.mission)))


for _name in dir(core.H1CoreTests):
    if _name.startswith('test_'):
        setattr(H1CompletionTests, _name, None)

if __name__ == '__main__':
    unittest.main()
