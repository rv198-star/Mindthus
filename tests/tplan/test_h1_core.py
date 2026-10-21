"""H1-B/C synthetic failure-first acceptance; no real Host certification."""
import base64
import copy
import json
import sys
import subprocess
import os
from unittest.mock import patch
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

    def pending(self, source_state='completed', qualified=True, dependencies=('A',)):
        candidate = self.call('candidate.submit', {'task_id':'A', 'attempt_ref':'A-1',
            'content_b64':base64.b64encode(b'actual immutable A v1').decode()})
        if dependencies is not None:
            runtime.record_work_plan(self.mission,{'schema_version':'tplan.work_plan.v0.1',
                'coverage':'complete','scope_note':'Synthetic native A before B; C independent',
                'blocks':[{'task_id':'A','depends_on':[]},
                          {'task_id':'B','depends_on':list(dependencies)},
                          {'task_id':'C','depends_on':[]}]})
        if source_state != 'pending':
            runtime.transition_task_status(self.mission,'A',source_state)
        if qualified:
            self.accept_candidate(candidate)
        self.call('decision.open', {'request_id':'HR1','business_task_id':'A',
            'blocked_task_ids':['B'], 'candidate_id':candidate['candidate_id']})
        return candidate

    def accept_candidate(self, candidate):
        runtime.append_event(self.mission,{'event_type':'acceptance_passed','task_id':'A',
            'summary':'Synthetic reviewer checked actual produced bytes against A1',
            'payload':{'acceptance_ids':['A1'],'candidate_sha256':candidate['content_sha256'],
                       'attempt_ref':candidate['attempt_ref']}})

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
            receipt = owner_receipt('h1-case',**{'candidate_sha256':candidate['content_sha256'],**change})
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

    def claim_payload(self, revision=2):
        return {'task_id':'B','request_id':'HR1','expected_revision':revision,'input_digest':'sha256:'+'a'*64}

    def ready(self):
        candidate = self.pending(); self.approve(candidate)
        self.call('adoption.apply', {'request_id':'HR1','candidate_id':candidate['candidate_id']})
        return candidate

    def recover(self, command_id):
        from tplan_commands import execute
        return execute(self.mission,{'protocol':'tplan.command.v1','action':'runtime.recover',
            'mission_id':'h1-case','command_id':command_id,
            'expected_build_hash':runtime.runtime_fingerprint()['build_hash']},principal='ordinary-host')

    def spawn_worker(self, request, mode='normal'):
        program = """import sys,json,os
from pathlib import Path
sys.path.insert(0,sys.argv[1]);sys.path.insert(0,sys.argv[2])
import tplan_runtime as r
from tplan_h1_commands import execute
from tests.tplan.h1_test_host import isolated_test_host
request=json.loads(sys.argv[4]);mode=sys.argv[5]
if mode=='prepared':
    r._recover_pending_mission_transaction_unlocked=lambda *a,**k:os._exit(91)
elif mode=='middle':
    original=r.write_json
    def interrupted(path,*a,**k):
        if Path(path).name=='mission.json':os._exit(92)
        return original(path,*a,**k)
    r.write_json=interrupted
elif mode=='before':
    r.write_json=lambda *a,**k:os._exit(90)
with isolated_test_host():
    result,code=execute(Path(sys.argv[3]),request)
if mode=='response':os._exit(93)
print(json.dumps(result))
raise SystemExit(code)
"""
        return subprocess.Popen([sys.executable,'-B','-c',program,str(fixtures.REPO),str(SCRIPTS),
            str(self.mission),json.dumps(request),mode],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)

    def worker_result(self, worker):
        out, err = worker.communicate(timeout=20)
        self.assertFalse(err,err)
        return worker.returncode,json.loads(out) if out else None

    def test_core_08_prepared_decision_crash_recovery_and_response_loss(self):
        candidate = self.pending()
        request = self.request('decision.apply',{'receipt':owner_receipt('h1-case',candidate_sha256=candidate['content_sha256'])})
        self.assertEqual(self.worker_result(self.spawn_worker(request,'prepared'))[0],91)
        self.assertTrue((self.mission/'.mission-transaction.json').exists())
        from query_runtime import query
        snapshot = {'protocol':'tplan.query.v1','action':'snapshot.get','request_id':'no-recover',
            'mission_id':'h1-case','expected_build_hash':runtime.runtime_fingerprint()['build_hash']}
        self.assertEqual(query(self.mission,snapshot)[1],4)
        with isolated_test_host():
            self.assertEqual(self.api.execute(self.mission,request)[1],4)
        # Interrupt forward recovery again, then recover with the same original writer.
        original = runtime.write_json
        def fail_mission(path,*args,**kwargs):
            if Path(path).name == 'mission.json':raise OSError('synthetic recovery interruption')
            return original(path,*args,**kwargs)
        with patch.object(runtime,'write_json',side_effect=fail_mission):
            self.assertNotEqual(self.recover(request['command_id'])[1],0)
        self.assertEqual(self.recover(request['command_id'])[1],0)
        with isolated_test_host():
            result,code = self.api.execute(self.mission,request)
        self.assertEqual(code,0,result);self.assertEqual(result['status'],'replayed')
        state = runtime.read_mission(self.mission)['human_control']
        self.assertEqual(len(state['decisions']),1)
        self.assertEqual(state['requests']['HR1']['revision'],2)
        self.call('adoption.apply',{'request_id':'HR1','candidate_id':candidate['candidate_id']})
        claim = self.request('execution.claim',self.claim_payload())
        self.assertEqual(self.worker_result(self.spawn_worker(claim,'response'))[0],93)
        with isolated_test_host():
            replay,code = self.api.execute(self.mission,claim)
        self.assertEqual(code,0,replay);self.assertEqual(replay['status'],'replayed')
        self.assertEqual(len(runtime.read_mission(self.mission)['human_control']['execution_slots']),1)

    def test_core_09_concurrent_different_round_ids_claim_one_slot(self):
        self.ready()
        requests = [self.request('execution.claim',self.claim_payload(),f'host-round-{i}') for i in range(4)]
        workers = [self.spawn_worker(r) for r in requests]
        outcomes = [self.worker_result(w) for w in workers]
        self.assertEqual(sum(code == 0 for code,_ in outcomes),1,outcomes)
        self.assertTrue(all(code == 0 or result['code'] == 'slot_occupied' for code,result in outcomes),outcomes)
        slots = runtime.read_mission(self.mission)['human_control']['execution_slots']
        self.assertEqual(len(slots),1)
        slot = next(iter(slots.values()))
        self.assertEqual(slot['authorization_round'],1)

    def test_core_10_slow_preparation_uses_final_revision_and_no_not_sent_release(self):
        candidate = self.ready()
        stale = self.request('execution.claim',self.claim_payload())
        self.approve(candidate,revision=2,choice='withdraw_change',nonce='withdraw-before-claim')
        self.call('adoption.apply',{'request_id':'HR1','candidate_id':candidate['candidate_id']})
        with isolated_test_host():
            result,code = self.api.execute(self.mission,stale)
        self.assertNotEqual(code,0,result)
        slot = self.call('execution.claim',self.claim_payload(3))
        for status in ('not_sent','superseded','cancelled'):
            before = runtime.read_mission(self.mission)
            with isolated_test_host():
                result,code = self.api.execute(self.mission,self.request('receipt.record',
                    {'slot_id':slot['slot_id'],'status':status,'receipt_ref':'unproven'}))
            self.assertNotEqual(code,0,result);self.assertEqual(runtime.read_mission(self.mission),before)

    def test_core_11_tamper_no_new_adoption_but_terminal_receipts_are_facts(self):
        candidate = self.ready()
        slot = self.call('execution.claim',self.claim_payload())
        path = self.mission/candidate['bytes_ref']
        path.chmod(0o600);path.write_bytes(b'tampered')
        with isolated_test_host():
            result,code = self.api.execute(self.mission,self.request('adoption.apply',
                {'request_id':'HR1','candidate_id':candidate['candidate_id']}))
        self.assertNotEqual(code,0,result)
        before = runtime.read_mission(self.mission);after=copy.deepcopy(before)
        after['mission']['status']='abandoned'
        runtime.commit_mission_state(self.mission,before,after,source={'kind':'runtime_script','name':'terminal'})
        self.call('receipt.record',{'slot_id':slot['slot_id'],'status':'delivered','receipt_ref':'late-real-fact'})
        late = self.call('candidate.submit',{'task_id':'A','attempt_ref':'A-late',
            'content_b64':base64.b64encode(b'late completed v2').decode()})
        with isolated_test_host():
            result,code = self.api.execute(self.mission,self.request('adoption.apply',
                {'request_id':'HR1','candidate_id':late['candidate_id']}))
        self.assertNotEqual(code,0,result)
        self.assertEqual(runtime.read_mission(self.mission)['mission']['status'],'abandoned')

    def test_core_12_nonce_reuse_with_current_revision_and_expired_command_replay(self):
        candidate = self.pending()
        first = self.request('decision.apply',{'receipt':owner_receipt('h1-case',candidate_sha256=candidate['content_sha256'])})
        with isolated_test_host():
            self.assertEqual(self.api.execute(self.mission,first)[1],0)
            reuse = self.request('decision.apply',{'receipt':owner_receipt('h1-case',revision=2,
                candidate_sha256=candidate['content_sha256'])})
            result,code = self.api.execute(self.mission,reuse)
            self.assertNotEqual(code,0,result);self.assertEqual(result['code'],'replay')
            with patch.object(self.api.time,'time',return_value=9999999999):
                result,code = self.api.execute(self.mission,first)
        self.assertEqual(code,0,result);self.assertEqual(result['status'],'replayed')

    def test_core_13_q2_owner_principal_stays_observation_and_snapshot_redacts_receipts(self):
        candidate = self.pending()
        from tplan_commands import execute
        req = {'protocol':'tplan.command.v1','action':'evidence.record','mission_id':'h1-case',
            'command_id':'fake-owner','expected_build_hash':runtime.runtime_fingerprint()['build_hash'],
            'payload':{'summary':'owner approved','task_id':'B','data':{'principal':'owner','choice':'approve_current'}}}
        result,code = execute(self.mission,req,principal='owner')
        self.assertEqual(code,0,result)
        self.assertEqual(runtime.read_mission(self.mission)['human_control']['requests']['HR1']['status'],'pending')
        self.approve(candidate)
        from query_runtime import query
        result,code = query(self.mission,{'protocol':'tplan.query.v1','action':'snapshot.get',
            'mission_id':'h1-case','request_id':'summary','expected_build_hash':runtime.runtime_fingerprint()['build_hash']})
        self.assertEqual(code,0,result)
        self.assertEqual(result['data']['human_control']['requests']['HR1']['revision'],2)
        serialized = json.dumps(result)
        self.assertNotIn('signature',serialized);self.assertNotIn('test-owner',serialized)


    def test_core_14_owner_approval_cannot_replace_pending_source_delivery(self):
        candidate = self.pending(source_state='pending'); self.approve(candidate)
        self.call('adoption.apply',{'request_id':'HR1','candidate_id':candidate['candidate_id']})
        before = runtime.read_mission(self.mission)
        with isolated_test_host():
            result,code = self.api.execute(self.mission,self.request('execution.claim',self.claim_payload()))
        self.assertNotEqual(code,0,result)
        self.assertEqual(runtime.read_mission(self.mission),before)

    def test_core_15_completed_without_qualified_source_acceptance_is_not_ready(self):
        candidate = self.pending(qualified=False); self.approve(candidate)
        self.call('adoption.apply',{'request_id':'HR1','candidate_id':candidate['candidate_id']})
        with isolated_test_host():
            result,code = self.api.execute(self.mission,self.request('execution.claim',self.claim_payload()))
        self.assertNotEqual(code,0,result)

    def test_core_16_revision_v2_needs_fresh_owner_choice_and_qualified_input(self):
        v1 = self.pending(); self.approve(v1,choice='request_changes')
        v2 = self.call('candidate.submit',{'task_id':'A','attempt_ref':'A-2',
            'content_b64':base64.b64encode(b'reviewed v2 bytes').decode()})
        self.accept_candidate(v2)
        revision = self.call('request.revise',{'request_id':'HR1','expected_revision':2,
            'candidate_id':v2['candidate_id']})
        self.assertEqual(revision['revision'],3)
        self.assertEqual(revision['status'],'pending')
        with isolated_test_host():
            result,code = self.api.execute(self.mission,self.request('adoption.apply',
                {'request_id':'HR1','candidate_id':v2['candidate_id']}))
        self.assertNotEqual(code,0,result)
        self.approve(v2,revision=3,nonce='approve-v2')
        self.call('adoption.apply',{'request_id':'HR1','candidate_id':v2['candidate_id']})
        slot = self.call('execution.claim',self.claim_payload(4))
        self.assertEqual(slot['candidate_id'],v2['candidate_id'])
        self.assertEqual((self.mission/v1['bytes_ref']).read_bytes(),b'actual immutable A v1')

    def test_core_17_revised_pending_v2_can_withdraw_to_v1_without_v2_completion(self):
        v1 = self.pending(); self.approve(v1,choice='request_changes')
        old_card = self.request('decision.apply',{'receipt':owner_receipt('h1-case',revision=2,
            candidate_sha256=v1['content_sha256'],nonce='old-web-card')})
        v2 = self.call('candidate.submit',{'task_id':'A','attempt_ref':'A-2',
            'content_b64':base64.b64encode(b'not yet accepted v2').decode()})
        self.call('request.revise',{'request_id':'HR1','expected_revision':2,'candidate_id':v2['candidate_id']})
        with isolated_test_host():
            result,code = self.api.execute(self.mission,old_card)
        self.assertNotEqual(code,0,result)
        self.approve(v1,revision=3,choice='withdraw_change',nonce='withdraw-v2')
        self.call('adoption.apply',{'request_id':'HR1','candidate_id':v1['candidate_id']})
        slot = self.call('execution.claim',self.claim_payload(4))
        self.assertEqual(slot['candidate_id'],v1['candidate_id'])
        with isolated_test_host():
            result,code = self.api.execute(self.mission,self.request('request.revise',
                {'request_id':'HR1','expected_revision':4,'candidate_id':v2['candidate_id']}))
        self.assertNotEqual(code,0,result)

    def test_core_18_unknown_native_dependencies_cannot_be_replaced_by_owner(self):
        v1 = self.pending(dependencies=None);self.approve(v1)
        self.call('adoption.apply',{'request_id':'HR1','candidate_id':v1['candidate_id']})
        with isolated_test_host():
            result,code = self.api.execute(self.mission,self.request('execution.claim',self.claim_payload()))
        self.assertNotEqual(code,0,result)

    def test_core_19_additional_native_input_needs_its_own_proof(self):
        v1 = self.pending(dependencies=('A','C'));self.approve(v1)
        self.call('adoption.apply',{'request_id':'HR1','candidate_id':v1['candidate_id']})
        with isolated_test_host():
            result,code = self.api.execute(self.mission,self.request('execution.claim',self.claim_payload()))
        self.assertNotEqual(code,0,result)
        self.assertEqual(result['code'],'dependency_unverified')

    def test_core_20_active_source_is_not_completed_delivery(self):
        v1 = self.pending(source_state='active');self.approve(v1)
        self.call('adoption.apply',{'request_id':'HR1','candidate_id':v1['candidate_id']})
        with isolated_test_host():
            result,code = self.api.execute(self.mission,self.request('execution.claim',self.claim_payload()))
        self.assertNotEqual(code,0,result)

    def test_core_21_accepted_unapproved_v2_does_not_invalidate_retained_v1(self):
        v1 = self.pending();self.approve(v1,choice='request_changes')
        v2 = self.call('candidate.submit',{'task_id':'A','attempt_ref':'A-2',
            'content_b64':base64.b64encode(b'qualified but unapproved v2').decode()})
        self.accept_candidate(v2)
        self.call('request.revise',{'request_id':'HR1','expected_revision':2,'candidate_id':v2['candidate_id']})
        self.approve(v1,revision=3,choice='withdraw_change',nonce='retain-v1')
        self.call('adoption.apply',{'request_id':'HR1','candidate_id':v1['candidate_id']})
        self.assertEqual(self.call('execution.claim',self.claim_payload(4))['candidate_id'],v1['candidate_id'])

    def test_core_22_new_source_failure_and_plan_bypass_are_rejected(self):
        v1 = self.ready()
        plan = copy.deepcopy(runtime.read_mission(self.mission)['work_plan'])
        plan['blocks'][1]['depends_on']=[]
        with self.assertRaises(runtime.TplanError):
            runtime.record_work_plan(self.mission,plan)
        runtime.append_event(self.mission,{'event_type':'acceptance_failed','task_id':'A',
            'summary':'Reviewer invalidated v1 before final claim',
            'payload':{'acceptance_ids':['A1'],'candidate_sha256':v1['content_sha256'],'attempt_ref':'A-1'}})
        with isolated_test_host():
            result,code = self.api.execute(self.mission,self.request('execution.claim',self.claim_payload()))
        self.assertNotEqual(code,0,result)

    def test_core_23_node_and_python_canonical_receipt_hmac_agree(self):
        import shutil
        if not shutil.which('node'):self.skipTest('Node unavailable for cross-language synthetic MAC vector')
        from tests.tplan.h1_test_host import signed, TEST_KEY
        body = {'z':'中文','a':{'choice':'withdraw_change','revision':2},'b':[1,'utf-8']}
        program = """const crypto=require('node:crypto');
const sort=v=>Array.isArray(v)?v.map(sort):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,sort(v[k])])):v;
const body=JSON.parse(process.argv[1]);
process.stdout.write(crypto.createHmac('sha256',Buffer.from(process.argv[2],'hex')).update(JSON.stringify(sort(body)),'utf8').digest('hex'));
"""
        result = subprocess.run(['node','-e',program,json.dumps(body),TEST_KEY.hex()],
            capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout,signed(body)['signature'])

    def test_core_24_same_id_with_changed_scope_conflicts_and_revise_replay_is_historical(self):
        v1 = self.pending();self.approve(v1,choice='request_changes')
        v2 = self.call('candidate.submit',{'task_id':'A','attempt_ref':'A-2',
            'content_b64':base64.b64encode(b'v2 replay input').decode()})
        request = self.request('request.revise',{'request_id':'HR1','expected_revision':2,'candidate_id':v2['candidate_id']})
        with isolated_test_host():
            first,code = self.api.execute(self.mission,request)
            self.assertEqual(code,0,first)
            altered = copy.deepcopy(request);altered['payload']['expected_revision']=3
            result,code = self.api.execute(self.mission,altered)
            self.assertEqual(result['code'],'command_conflict')
            result,code = self.api.execute(self.mission,request)
            self.assertEqual(code,0,result);self.assertEqual(first['data'],result['data'])
        self.assertEqual(runtime.read_mission(self.mission)['human_control']['requests']['HR1']['status'],'pending')

    def test_core_25_slot_ids_are_native_dsh_ids_and_never_replaced(self):
        import uuid
        self.ready()
        request = self.request('execution.claim',self.claim_payload())
        with isolated_test_host():
            result,code = self.api.execute(self.mission,request)
        self.assertEqual(code,0,result)
        slot = result['data']
        self.assertTrue(slot['session_id'].startswith('session-'),slot)
        self.assertEqual(str(uuid.UUID(slot['session_id'][8:])),slot['session_id'][8:])
        self.assertEqual(str(uuid.UUID(slot['native_request_id'])),slot['native_request_id'])
        self.call('receipt.record',{'slot_id':slot['slot_id'],'status':'unknown','receipt_ref':'native-timeout'})
        with isolated_test_host():
            replay,code = self.api.execute(self.mission,request)
        self.assertEqual(code,0,replay)
        current = self.call('execution.get',{'slot_id':slot['slot_id']})
        for field in ('slot_id','intent_id','session_id','native_request_id'):
            self.assertEqual(slot[field],replay['data'][field])
            self.assertEqual(slot[field],current[field])

# Avoid inheriting the baseline test_* methods (which create their own Missions).
for _name in dir(fixtures.H1KernelGateTests):
    if _name.startswith('test_'):
        setattr(H1CoreTests,_name,None)

if __name__ == '__main__':
    unittest.main()
