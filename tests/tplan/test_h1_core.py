"""H1-B/C synthetic failure-first acceptance; no real Host certification."""
import base64
import copy
import json
import sys
import unittest
from pathlib import Path
from tests.tplan import test_h1_kernel_gate as fixtures
SCRIPTS = fixtures.SCRIPTS
sys.path.insert(0, str(SCRIPTS))
from tests.tplan.h1_test_host import host_request, owner_receipt, isolated_test_host
import tplan_runtime as runtime


class H1CoreTests(fixtures.H1KernelGateTests):
    # Reuse setup helpers, not the inherited H1-A test suite.
    def setUp(self):
        super().setUp()
        self.create()
        self.counter = 0
        import tplan_h1_commands
        self.api = tplan_h1_commands

    def request(self, action, payload, command_id=None):
        self.counter += 1
        return host_request({'protocol':'tplan.h1.command.v1', 'action':action,
            'mission_id':'h1-case', 'command_id':command_id or f'cmd-{self.counter}',
            'expected_build_hash':runtime.runtime_fingerprint()['build_hash'], 'payload':payload})

    def call(self, action, payload, command_id=None):
        request = self.request(action, payload, command_id)
        with isolated_test_host():
            result, code = self.api.execute(self.mission, request)
        self.assertEqual(code, 0, result)
        return result['data']

    def pending(self):
        candidate = self.call('candidate.submit', {'task_id':'A', 'attempt_ref':'A-1',
            'content_b64':base64.b64encode(b'actual immutable A v1').decode()})
        self.call('decision.open', {'request_id':'HR1','business_task_id':'A',
            'blocked_task_ids':['B'], 'candidate_id':candidate['candidate_id']})
        return candidate

    def approve(self, candidate, **kw):
        return self.call('decision.apply', {'receipt':owner_receipt('h1-case',
            candidate_sha256=candidate['content_sha256'], **kw)})

    def test_core_01_unconfigured_runtime_is_disabled_even_with_signed_fixture(self):
        request = self.request('decision.apply', {'receipt':{'principal':'owner','secret':'chosen'}})
        before = (self.mission/'mission.json').read_bytes()
        result, code = self.api.execute(self.mission, request)
        self.assertNotEqual(code, 0)
        self.assertEqual(result['code'], 'host_disabled')
        self.assertEqual(before, (self.mission/'mission.json').read_bytes())

    def test_core_02_local_wait_and_immutable_candidate_and_late_result(self):
        candidate = self.pending()
        with self.assertRaises(runtime.TplanError):
            runtime.transition_task_status(self.mission,'B','active')
        runtime.transition_task_status(self.mission,'C','active')
        runtime.append_event(self.mission,{'event_type':'observation','task_id':'C','summary':'C works'})
        self.approve(candidate)
        self.call('adoption.apply', {'request_id':'HR1','candidate_id':candidate['candidate_id']})
        late = self.call('candidate.submit', {'task_id':'A','attempt_ref':'A-2',
            'content_b64':base64.b64encode(b'late v2').decode()})
        before = runtime.read_mission(self.mission)
        with isolated_test_host():
            result, code = self.api.execute(self.mission, self.request('adoption.apply',
                {'request_id':'HR1','candidate_id':late['candidate_id']}))
        self.assertNotEqual(code,0,result)
        self.assertEqual(runtime.read_mission(self.mission),before)
        self.assertEqual((self.mission/candidate['bytes_ref']).read_bytes(),b'actual immutable A v1')

    def test_core_03_bad_signature_revision_and_nonce_do_not_mutate(self):
        candidate = self.pending()
        receipt = owner_receipt('h1-case',candidate_sha256=candidate['content_sha256'])
        bad = {**receipt, 'signature':'0'*64}
        before = runtime.read_mission(self.mission)
        with isolated_test_host():
            result, code = self.api.execute(self.mission,self.request('decision.apply',{'receipt':bad}))
        self.assertNotEqual(code,0,result)
        self.assertEqual(runtime.read_mission(self.mission),before)
        request = self.request('decision.apply',{'receipt':receipt})
        with isolated_test_host():
            first, code = self.api.execute(self.mission,request)
            again, code2 = self.api.execute(self.mission,request)
            replay, replay_code = self.api.execute(self.mission,self.request('decision.apply',{'receipt':receipt}))
        self.assertEqual((code,code2),(0,0))
        self.assertEqual(first['data'],again['data'])
        self.assertNotEqual(replay_code,0,replay)
        self.assertEqual(runtime.read_mission(self.mission)['human_control']['requests']['HR1']['revision'],2)

    def test_core_04_unique_claim_unknown_and_withdrawal_never_release(self):
        candidate = self.pending(); self.approve(candidate)
        self.call('adoption.apply', {'request_id':'HR1','candidate_id':candidate['candidate_id']})
        payload = {'task_id':'B','request_id':'HR1','expected_revision':2,'input_digest':'sha256:'+'a'*64}
        slot = self.call('execution.claim',payload)
        runtime.append_event(self.mission,{'event_type':'observation','task_id':'C','summary':'unrelated'})
        self.call('receipt.record',{'slot_id':slot['slot_id'],'status':'unknown','receipt_ref':'timeout-1'})
        self.approve(candidate,revision=2,choice='withdraw_change',nonce='owner-2')
        self.call('adoption.apply', {'request_id':'HR1','candidate_id':candidate['candidate_id']})
        with isolated_test_host():
            result, code = self.api.execute(self.mission,self.request('execution.claim',{**payload,'expected_revision':3}))
        self.assertNotEqual(code,0,result)
        existing = self.call('execution.get',{'slot_id':slot['slot_id']})
        self.assertEqual(existing['intent_id'],slot['intent_id'])
        self.assertEqual(len(runtime.read_mission(self.mission)['human_control']['execution_slots']),1)


    def test_core_05_signed_wrong_scope_time_and_self_selected_keys(self):
        candidate = self.pending()
        changes = [dict(owner_subject_ref='attacker'), dict(origin_session_ref='wrong'),
            dict(origin_binding_ref='wrong'), dict(mission_id='wrong'), dict(expected_revision=9),
            dict(candidate_sha256='sha256:'+'0'*64), dict(choice='tool_approval'),
            dict(issued_at=1,expires_at=2), dict(issued_at=9999999999,expires_at=10000000000),
            dict(secret='chosen'), dict(key_path='/tmp/attacker'), dict(issuer_id='unknown')]
        for change in changes:
            receipt = owner_receipt('h1-case',candidate_sha256=candidate['content_sha256'],**change)
            before = runtime.read_mission(self.mission)
            with isolated_test_host():
                result, code = self.api.execute(self.mission,self.request('decision.apply',{'receipt':receipt}))
            self.assertNotEqual(code,0,(change,result))
            self.assertEqual(runtime.read_mission(self.mission),before)

    def test_core_06_withdrawal_commits_even_if_bytes_are_unavailable(self):
        candidate = self.pending()
        self.approve(candidate,choice='request_changes')
        path = self.mission/candidate['bytes_ref']
        path.unlink()
        result = self.approve(candidate,revision=2,choice='withdraw_change',nonce='withdraw')
        self.assertTrue(result['adoption_blocked'])
        state = runtime.read_mission(self.mission)
        self.assertEqual(state['human_control']['requests']['HR1']['revision'],3)
        with isolated_test_host():
            result, code = self.api.execute(self.mission,self.request('execution.claim',
                {'task_id':'B','request_id':'HR1','expected_revision':3,'input_digest':'sha256:'+'a'*64}))
        self.assertNotEqual(code,0,result)

    def test_core_07_legacy_protection_remains_after_approval(self):
        candidate = self.pending(); self.approve(candidate)
        before = runtime.read_mission(self.mission)
        for mutate in (lambda s:s.pop('human_control'),
                       lambda s:s['tasks'][1].update(status='active'),
                       lambda s:s['tasks'][0].update(role='normal'),
                       lambda s:s['mission'].update(status='completed')):
            after = copy.deepcopy(before);mutate(after)
            with self.assertRaises(runtime.TplanError):
                runtime.commit_mission_state(self.mission,before,after,
                    source={'kind':'runtime_script','name':'bypass'})
        with self.assertRaises(runtime.TplanError):
            runtime.append_event(self.mission,{'event_type':'acceptance_passed','task_id':'B',
                'summary':'fake','payload':{'acceptance_ids':['A1']}})
        runtime.append_event(self.mission,{'event_type':'observation','task_id':'C','summary':'still allowed'})

# Avoid inheriting the baseline test_* methods (which create their own Missions).
for _name in dir(fixtures.H1KernelGateTests):
    if _name.startswith('test_'):
        setattr(H1CoreTests,_name,None)

if __name__ == '__main__':
    unittest.main()
