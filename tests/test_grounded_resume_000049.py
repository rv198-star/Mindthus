"""Only named SSE compensation wiring; synthetic transport and clock."""
import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from tests import test_grounded_resume_000047 as fixture47
from experiments.grounded_judgment import runtime as rt,resume_000047 as prior,resume_000049 as named
from experiments.grounded_judgment.resume_000007 import NamedSerial,guard
from experiments.typed_decision.contracts import digest
from experiments.typed_decision.session import RecoveryRequired,read_record


class Named49(unittest.TestCase):
    def fixture(self,root):
        config,clock=fixture47.Named47().fixture(root)
        with patch.object(prior,'BATCH',digest(config)):
            parent=prior.register(root)
            serial=NamedSerial(root/'serial',clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
            for i in (48,49):
                d=root/'calls'/f'{i:06d}';d.mkdir()
                key=named.KEY if i==49 else 'record-source-2-B:0'
                b={'call_key':key}
                req={'request_sha256':named.REQUEST,'role':'host','phase':'draft','payload':{'same_input':True}}
                raw={'kind':'cli','events':[{'type':'thread.started','thread_id':'synthetic-thread'},
                     {'type':'turn.started'},{'type':'turn.failed','error':{'message':'stream disconnected before completion: idle timeout waiting for SSE'}}],
                     'reply_text':None}
                t={'binding':b,'status':'unknown' if i==49 else 'returned','error':'unclassified_cli_failure' if i==49 else None}
                for n,v in [('request',req),('binding',b),('terminal',t),('raw',{'binding':b,'transport':raw}),('import',{})]:rt.write(d/(n+'.json'),v)
                if i==49:
                    with self.assertRaises(RecoveryRequired):serial.call(key,lambda:(_ for _ in ()).throw(RecoveryRequired('synthetic')))
                else:serial.call(key,lambda:None)
        run=root/'runs/record-source-2-B';s=rt.state(run)
        s.update(stopped='unknown',call_count=2,pending=req,phase='draft',draft=None)
        rt.append(run,'state',s)
        rt.write(root/'STOP-000049.json',{'call_key':named.KEY,'reason':'unknown','terminal_sha256':digest(t)})
        for p in ('experiments/grounded_judgment/dispatch.py','experiments/grounded_judgment/resume_000007.py'):parent['source_sha256'][p]='pre-repair-fixture'
        (root/prior.NAME).write_text(__import__('json').dumps(parent))
        # The original acceptance binds its exact parent identity.
        from experiments.typed_decision.relationship_runtime import save
        def replace_fixture(path,value):
            path.unlink();save(path,value)
        end=read_record(root/'serial/000047/accepted-unknown.json');end['successor_sha256']=digest(parent)
        replace_fixture(root/'serial/000047/accepted-unknown.json',end)
        replace_fixture(root/'serial/bindings/000047/accepted-unknown.json',{'sha256':digest(end)})
        # 48's serial chain must reference the unchanged disposition in this fixture.
        intent=read_record(root/'serial/000048/intent.json');intent['previous_disposition_sha256']=digest(end)
        replace_fixture(root/'serial/000048/intent.json',intent);replace_fixture(root/'serial/bindings/000048/intent.json',{'intent_sha256':digest(intent)})
        end48=read_record(root/'serial/000048/completion.json');end48['intent_sha256']=digest(intent)
        replace_fixture(root/'serial/000048/completion.json',end48);replace_fixture(root/'serial/bindings/000048/completion.json',{'completion_sha256':digest(end48)})
        intent49=read_record(root/'serial/000049/intent.json');intent49['previous_completion_sha256']=digest(end48)
        replace_fixture(root/'serial/000049/intent.json',intent49);replace_fixture(root/'serial/bindings/000049/intent.json',{'intent_sha256':digest(intent49)})
        return config,clock,s

    def test_exact_compensation_preserves_debits_atoms_and_serial_wait(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);config,clock,before=self.fixture(root)
            with patch.object(named,'BATCH',digest(config)),patch.object(prior,'BATCH',digest(config)):
                x=named.register(root);after=rt.state(root/'runs/record-source-2-B')
                self.assertEqual(after['call_count'],2);self.assertEqual(after['atoms'],before['atoms'])
                self.assertEqual(after['composition'],before['composition']);self.assertIsNone(after['pending'])
                self.assertEqual(x['limits'],config['admission']['total_limits']);self.assertEqual(x['retry_limit'],1)
                for slot in ('000047','000049'):self.assertFalse((root/'serial'/slot/'completion.json').exists())
                serial=NamedSerial(root/'serial',clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
                serial.call(x['retry_call_key'],lambda:None)
                intent=read_record(root/'serial/000050/intent.json')
                self.assertGreaterEqual(intent['actual_gap_seconds'],60)
                self.assertEqual(intent['gap_basis'],'monotonic_wait_after_risk_acceptance_not_remote_completion')
                with self.assertRaises(ValueError):named.register(root)
                with self.assertRaisesRegex(ValueError,'already_completed'):serial.call(x['retry_call_key'],lambda:None)

    def test_new_stop_and_history_change_block_dispatch(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);config,_,_=self.fixture(root)
            with patch.object(named,'BATCH',digest(config)),patch.object(prior,'BATCH',digest(config)):
                named.register(root);rt.write(root/'STOP-000050.json',{'reason':'unknown'})
                with self.assertRaisesRegex(ValueError,'new_stop'):guard(root)
                (root/'STOP-000050.json').unlink();p=root/'calls/000049/raw.json';p.write_text('{}')
                with self.assertRaisesRegex(ValueError,'history'):guard(root)

    def test_safety_or_wrong_identity_not_accepted(self):
        for field,value in [('status','safety_refusal'),('request_sha256','other')]:
            with self.subTest(field=field),tempfile.TemporaryDirectory() as t:
                root=Path(t);config,_,_=self.fixture(root)
                p=root/'calls/000049'/('terminal.json' if field=='status' else 'request.json')
                v=rt.read(p);v[field]=value;p.write_text(__import__('json').dumps(v))
                with patch.object(named,'BATCH',digest(config)),patch.object(prior,'BATCH',digest(config)):
                    with self.assertRaises(ValueError):named.register(root)
                self.assertFalse((root/named.NAME).exists())


if __name__=='__main__':unittest.main()
