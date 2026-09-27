"""Local wiring only: fixture model replies and a simulated request clock."""
import json
import tempfile
import subprocess
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch
from experiments.jev_direct.serial import SerialRequests
from experiments.typed_decision.session import read_record, RecoveryRequired
from experiments.typed_decision.relationship_runtime import _locked
from experiments.typed_decision.contracts import ContractError
from tests import test_jev_direct_router as fixtures
from tests.test_jev_direct_router import Provider
from experiments.jev_direct import pilot as p, router as r
from tests.test_jev_direct_router import RAW, REPO


class Clock:
    def __init__(self): self.now=1000.0; self.waits=[]
    def time(self): return self.now
    def sleep(self,n): self.waits.append(n); self.now+=n


class SerialTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.clock=Clock()
        self.gate=SerialRequests(self.root,clock=self.clock.time,monotonic=self.clock.time,sleep=self.clock.sleep)
    def test_end_to_start_and_restart(self):
        def call():self.clock.now+=17;return 'done'
        self.gate.call('host',call)
        gate=SerialRequests(self.root,clock=self.clock.time,monotonic=self.clock.time,sleep=self.clock.sleep)
        gate.call('jev',call)
        self.assertEqual(read_record(self.root/'000001/intent.json')['actual_gap_seconds'],60)
        self.assertEqual(self.clock.waits,[60])
    def test_no_extra_wait_after_sixty_seconds(self):
        self.gate.call('host',lambda:None);self.clock.now+=75
        self.gate.call('jev',lambda:None);self.assertEqual(self.clock.waits,[])
    def test_concurrent_entry_rejected(self):
        with _locked(self.root/'.lock'):
            with self.assertRaises(RecoveryRequired):self.gate.call('host',lambda:self.fail('invoked'))
    def test_unknown_interrupt_blocks_all_later_requests(self):
        def interrupt():raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):self.gate.call('host',interrupt)
        with self.assertRaisesRegex(RecoveryRequired,'unknown_request'):
            self.gate.call('jev',lambda:self.fail('invoked'))
    def test_exception_is_not_claimed_remote_completion(self):
        with self.assertRaises(TimeoutError):self.gate.call('host',lambda:(_ for _ in ()).throw(TimeoutError()))
        self.assertFalse((self.root/'000000/completion.json').exists())
    def test_layer_cooldown_is_outside_inference_budget(self):
        self.gate.call('previous-host',lambda:None)
        provider=Provider({'READ.edsp':1})
        with patch('experiments.typed_decision.session.time.monotonic',side_effect=self.clock.time):
            out=r.route(self.root/'route',RAW,REPO,'0'*64,provider,scheduler=self.gate)
        self.assertEqual(out['rounds'],2)
        self.assertEqual(len(provider.states),2)
        self.assertEqual(self.clock.waits,[60,60])
    def test_live_without_completion_receipt_blocks_scheduler(self):
        provider=Provider();provider.is_live=True
        with self.assertRaisesRegex(RecoveryRequired,'completion_unknown'):
            r.route(self.root/'route',RAW,REPO,'0'*64,provider,scheduler=self.gate)
        with self.assertRaisesRegex(RecoveryRequired,'unknown_request'):
            self.gate.call('next',lambda:self.fail('invoked'))
    def test_corrupt_completed_intent_is_rejected(self):
        self.gate.call('host',lambda:None)
        (self.root/'000000/intent.json').write_text('{broken')
        with patch.object(p.wire,'_run_cli') as cli:
            with self.assertRaises(Exception):self.gate.call('jev',cli)
            cli.assert_not_called()
    def test_wall_jump_does_not_skip_monotonic_cooldown(self):
        wall=Clock();mono=Clock()
        gate=SerialRequests(self.root,clock=wall.time,monotonic=mono.time,sleep=mono.sleep)
        gate.call('host',lambda:None);mono.now+=1;wall.now+=120
        gate.call('jev',lambda:None)
        self.assertEqual(mono.waits,[59])
        self.assertEqual(read_record(self.root/'000001/intent.json')['actual_gap_seconds'],60)
    def test_restart_ignores_wall_and_monotonic_discontinuity(self):
        self.gate.call('host',lambda:None)
        wall=Clock();wall.now+=10000;mono=Clock();mono.now=1
        gate=SerialRequests(self.root,clock=wall.time,monotonic=mono.time,sleep=mono.sleep)
        gate.call('jev',lambda:None)
        self.assertEqual(mono.waits,[60])
        self.assertEqual(read_record(self.root/'000001/intent.json')['gap_basis'],'restart_conservative_lower_bound')


class LocalPilotTests(fixtures.PilotTests):
    def setUp(self):
        super().setUp()
        self.root=Path(self.tmp.name)/'serial-trial'
        self.f=p.prepare(self.root,self.f['cases'],binary=self.f['binary'],serial_gap_seconds=60)
        self.clock=Clock();self.gate=SerialRequests(self.root/'serial',clock=self.clock.time,monotonic=self.clock.time,sleep=self.clock.sleep)
    def run_arm(self,arm='direct',provider=None):
        with patch.object(p.wire,'_run_cli',side_effect=self.cli):
            return p.run_case(self.root,'X',arm,provider or Provider(),scheduler=self.gate)
    def test_read_resume_and_two_arms_share_gap(self):
        self.read_first=True
        self.run_arm('native');self.read_first=False;self.run_arm('direct')
        intents=sorted((self.root/'serial').glob('*/intent.json'))
        self.assertEqual(len(intents),4)
        self.assertEqual([read_record(x)['actual_gap_seconds'] for x in intents],[None,60,60,60])
        self.assertEqual(self.clock.waits,[60,60,60])
    def test_live_injected_provider_cannot_bypass_gate(self):
        provider=Provider();provider.is_live=True
        with self.assertRaisesRegex(ContractError,'bypasses_serial'):
            self.run_arm('direct',provider)
        self.assertEqual(self.commands,[])
    def test_foreign_scheduler_rejected(self):
        with self.assertRaisesRegex(ContractError,'serial_root'):
            p.run_case(self.root,'X','native',Provider(),scheduler=SerialRequests(self.root/'wrong'))
    def test_cli_exit_without_terminal_event_remains_unknown(self):
        with patch.object(p.wire,'_run_cli',return_value=subprocess.CompletedProcess([],0,'','')):
            with self.assertRaisesRegex(RecoveryRequired,'completion_unknown'):
                p.run_case(self.root,'X','native',Provider(),scheduler=self.gate)
        with self.assertRaisesRegex(RecoveryRequired,'unknown_request'):
            self.gate.call('next',lambda:self.fail('invoked'))
    def test_lost_serial_directory_blocks_other_scenario(self):
        with patch.object(p.wire,'_run_cli',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                p.run_case(self.root,'X','native',Provider(),scheduler=self.gate)
        shutil.rmtree(self.root/'serial')
        with patch.object(p.wire,'_run_cli') as cli:
            with self.assertRaisesRegex(ContractError,'binding_missing'):self.run_arm('direct')
            cli.assert_not_called()
    def test_lost_serial_and_anchor_still_detected_from_business_intent(self):
        with patch.object(p.wire,'_run_cli',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                p.run_case(self.root,'X','native',Provider(),scheduler=self.gate)
        shutil.rmtree(self.root/'serial');shutil.rmtree(self.root/'serial-bindings')
        with self.assertRaisesRegex(ContractError,'business_binding_missing'):
            self.gate.call('unrelated-scenario',lambda:self.fail('invoked'))
    def test_cooldown_interrupt_has_no_host_send_intent_and_can_resume(self):
        self.gate.call('previous',lambda:None)
        with patch.object(self.gate,'sleep',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):self.run_arm('native')
        self.assertFalse((self.root/'runs/X/native/host/0/intent.json').exists())
        self.assertEqual(self.commands,[])
        self.assertEqual(self.run_arm('native')['status'],'delivered')
        self.assertEqual(len(self.commands),1)
    def test_direct_host_call_enforces_policy_without_explicit_scheduler(self):
        with _locked(self.root/'serial/.lock'),patch.object(p.wire,'_run_cli') as cli:
            with self.assertRaises(RecoveryRequired):
                p.host_call(self.root/'reviews/X','1',{},p.obj({}),self.f)
            cli.assert_not_called()
    def test_direct_review_style_call_blocks_unknown_business_request(self):
        with patch.object(p.wire,'_run_cli',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                p.run_case(self.root,'X','native',Provider(),scheduler=self.gate)
        with patch.object(p.wire,'_run_cli') as cli:
            with self.assertRaisesRegex(RecoveryRequired,'unknown_request'):
                p.host_call(self.root/'reviews/X','1',{},p.obj({}),self.f)
            cli.assert_not_called()
    def orphan_response_fixture(self,completed):
        self.root=Path(self.tmp.name)/'partial-restore'
        cases=self.f['cases']+[dict(self.f['cases'][0],id='Y')]
        self.f=p.prepare(self.root,cases,binary=self.f['binary'],serial_gap_seconds=60)
        self.gate=SerialRequests(self.root/'serial',clock=self.clock.time,monotonic=self.clock.time,sleep=self.clock.sleep)
        if completed:self.run_arm('native')
        else:
            def interrupted(cmd,prompt,env,timeout):
                self.cli(cmd,prompt,env,timeout)
                raise KeyboardInterrupt()
            with patch.object(p.wire,'_run_cli',side_effect=interrupted):
                with self.assertRaises(KeyboardInterrupt):
                    p.run_case(self.root,'X','native',Provider(),scheduler=self.gate)
        shutil.rmtree(self.root/'serial');shutil.rmtree(self.root/'serial-bindings')
        (self.root/'runs/X/native/host/0/intent.json').unlink()
        with patch.object(p.wire,'_run_cli') as cli:
            with self.assertRaisesRegex(ContractError,'orphan_response_evidence'):
                p.run_case(self.root,'Y','native',Provider(),scheduler=self.gate)
            cli.assert_not_called()
        self.assertFalse((self.root/'serial/000000/intent.json').exists())
    def test_orphan_outcome_from_completed_case_blocks_other_case(self):
        self.orphan_response_fixture(True)
        self.assertTrue((self.root/'runs/X/native/result.json').exists())
    def test_orphan_reply_after_interrupt_blocks_other_case(self):
        self.orphan_response_fixture(False)
        self.assertFalse((self.root/'runs/X/native/host/0/outcome.json').exists())
    def test_prepared_material_only_can_resume_as_first_send(self):
        with patch.object(self.gate,'call',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):self.run_arm('native')
        directory=self.root/'runs/X/native/host/0'
        self.assertTrue((directory/'request.json').exists())
        self.assertFalse((directory/'intent.json').exists())
        self.assertFalse((directory/'reply.json').exists())
        self.assertEqual(self.run_arm('native')['status'],'delivered')
        self.assertEqual(len(self.commands),1)

if __name__=='__main__':unittest.main()
