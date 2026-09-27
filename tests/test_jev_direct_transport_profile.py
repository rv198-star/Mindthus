"""Only new profile wiring and forward-only stopping boundaries; no live calls."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from experiments.jev_direct import pilot as p, transport_profile as t
from experiments.jev_direct.serial import SerialRequests
from experiments.typed_decision.contracts import digest
from experiments.typed_decision.relationship_runtime import save
from experiments.typed_decision.session import RecoveryRequired, read_record

class TransportProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.candidate=json.loads(t.CANDIDATE.read_text())
        self.profile={'overrides':self.candidate['candidate_overrides'],
                      'overrides_sha256':self.candidate['overrides_sha256'],'protocol_sha256':'protocol-fixture'}

    def test_both_arms_send_exact_candidate_without_mutating_contract(self):
        f={'root':str(self.root),'binary':'fixture','host_model':'gpt-6-sol','host_effort':'xhigh','host_timeout':360}
        schema=p.answer_schema(['skills/edsp/SKILL.md']);before=digest(schema);commands=[]
        def cli(cmd,prompt,env,timeout):
            commands.append(cmd)
            reply={'action':'answer','text':'fixture only','read_paths':[],'used_methods':[],'route_objection':''}
            Path(cmd[cmd.index('-o')+1]).write_text(json.dumps(reply))
            return subprocess.CompletedProcess(cmd,0,'{"type":"thread.started","thread_id":"fixture"}\n{"type":"turn.completed"}','')
        with patch.object(t,'active',return_value=self.profile),patch.object(p.wire,'_run_cli',side_effect=cli):
            for arm in ('native','direct'):
                reply,out=p.host_call(self.root/arm,'0',{'fixture':True},schema,f)
                self.assertEqual(out['status'],'complete')
                rec=read_record(self.root/arm/'0/effective-transport-config.json')
                self.assertEqual(rec['overrides'],self.candidate['candidate_overrides'])
        for cmd in commands:
            flags=[cmd[i+1] for i,v in enumerate(cmd) if v=='-c']
            self.assertEqual(flags[-7:],self.candidate['candidate_overrides'])
            self.assertNotIn('base_url',' '.join(flags))
            self.assertIn('--sandbox',cmd)
        self.assertEqual(digest(schema),before)

    def test_observed_unclassified_resubmit_preserves_return_and_blocks_next_dispatch(self):
        save(self.root/'freeze.json',{'fixture':True})
        proc=subprocess.CompletedProcess([],0,'{"type":"turn.completed"}','retrying sampling request (1/5): request timed out')
        x=t.observe(self.root,self.root/'host/0',proc,{'request_sha256':'request','transport_successor_sha256':'successor'})
        self.assertTrue(x['stop_subsequent_dispatch']);self.assertIsNone(x['actual_underlying_request_count'])
        with self.assertRaisesRegex(RecoveryRequired,'unclassified'):
            SerialRequests(self.root/'serial').call('never',lambda:self.fail('must not dispatch'))
        self.assertFalse((self.root/'serial/000000/intent.json').exists())

    def test_no_log_is_not_proof_zero_recovery_or_one_http_attempt(self):
        x=t.observe(self.root,self.root/'host/0',subprocess.CompletedProcess([],0,'',''),
                    {'request_sha256':'request','transport_successor_sha256':'successor'})
        self.assertEqual(x['observation'],'no_recovery_observed')
        self.assertIsNone(x['generation_attempt_count']);self.assertIsNone(x['actual_underlying_request_count'])
        self.assertFalse(x['stop_subsequent_dispatch'])

    def test_unbound_401_text_cannot_self_authorize_resend(self):
        x=t.observe(self.root,self.root/'host/0',subprocess.CompletedProcess([],0,'','401 recovery_succeeded'),
                    {'request_sha256':'request','transport_successor_sha256':'successor'})
        self.assertTrue(x['stop_subsequent_dispatch'])
        self.assertIsNone(x['authentication_recovery_seconds'])

    def test_protocol_preserves_timing_budget_and_refusal_boundary(self):
        x=json.loads(t.PROTOCOL.read_text())
        self.assertEqual(x['max_generation_work_in_flight'],1)
        self.assertEqual(x['gap_after_confirmed_generation_work_end_seconds'],60)
        self.assertIn('safety or permission refusal',x['not_exempt'])
        self.assertFalse(x['account_credentials_channel_switch_for_refusal'])
        self.assertIn('forward only',x['effective'])
        self.assertIn('2/4',x['history'])

if __name__=='__main__':unittest.main()
