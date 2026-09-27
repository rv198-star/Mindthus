"""Local wiring only: fixture model replies and a simulated request clock."""
import json
import tempfile
import subprocess
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
        self.gate=SerialRequests(self.root,clock=self.clock.time,sleep=self.clock.sleep)
    def test_end_to_start_and_restart(self):
        def call():self.clock.now+=17;return 'done'
        self.gate.call('host',call)
        gate=SerialRequests(self.root,clock=self.clock.time,sleep=self.clock.sleep)
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


class LocalPilotTests(fixtures.PilotTests):
    def setUp(self):
        super().setUp()
        self.root=Path(self.tmp.name)/'serial-trial'
        self.f=p.prepare(self.root,self.f['cases'],binary=self.f['binary'],serial_gap_seconds=60)
        self.clock=Clock();self.gate=SerialRequests(self.root/'serial',clock=self.clock.time,sleep=self.clock.sleep)
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

if __name__=='__main__':unittest.main()
