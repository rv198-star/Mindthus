"""Only the new named disposition wiring; all calls and clocks are synthetic."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from experiments.grounded_judgment import runtime as rt,resume_000047 as named
from experiments.grounded_judgment.resume_000007 import NamedSerial,guard
from experiments.grounded_judgment.development import cases
from experiments.grounded_judgment.dispatch_demo import Clock
from experiments.jev_direct.serial import SerialRequests
from experiments.typed_decision.session import RecoveryRequired,read_record
from experiments.typed_decision.contracts import digest


class Named47(unittest.TestCase):
    def fixture(self,root):
        config={'admission':{'total_limits':{'logical':176,'host':144,'jev':32}}}
        rt.write(root/'batch.json',config)
        rt.write(root/'STOP.json',{'reason':'technical_pause_read_contract_omission'})
        (root/'runs').mkdir();(root/'calls').mkdir()
        for name in named.PATHS+['record-source-1-B']:
            rt.init(root/'runs'/name,cases()[0]['documents'],name[-1])
        s=rt.state(root/'runs/record-source-1-B');s.update(stopped='unknown',call_count=2,draft=None)
        rt.append(root/'runs/record-source-1-B','state',s)
        clock=Clock();serial=SerialRequests(root/'serial',clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
        for i in range(48):
            d=root/'calls'/f'{i:06d}';d.mkdir()
            binding={'call_key':named.KEY if i==47 else 'fixture:'+str(i)}
            terminal={'binding':binding,'status':'unknown' if i==47 else 'returned','error':'TimeoutExpired' if i==47 else None}
            rt.write(d/'binding.json',binding);rt.write(d/'terminal.json',terminal)
            rt.write(d/'raw.json',{'binding':binding});rt.write(d/'import.json',{})
            rt.write(d/'request.json',{'request_sha256':named.REQUEST,'role':'host','phase':'draft'})
            if i==47:
                with self.assertRaises(RecoveryRequired):serial.call(named.KEY,lambda:(_ for _ in ()).throw(RecoveryRequired('synthetic')))
            else:serial.call('fixture:'+str(i),lambda:None)
        rt.write(root/'STOP-000047.json',{'call_key':named.KEY,'reason':'unknown','terminal_sha256':digest(terminal)})
        parent={'batch_sha256':digest(config),'kind':'read_contract_sending_clarification',
                'runner_sha256':digest((named.REPO/named.RUNNER).read_text()),'preserved':{},
                'source_sha256':{'experiments/grounded_judgment/'+p:'old-fixture' for p in ('dispatch.py','resume_000007.py')}}
        rt.write(root/'read-contract-successor.json',parent)
        return config,clock

    def test_preserve_unknown_no_replay_budget_and_serial_continuation(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);config,clock=self.fixture(root);before=rt.state(root/'runs/record-source-1-B')
            with patch.object(named,'BATCH',digest(config)):
                x=named.register(root)
                self.assertEqual(guard(root),x);self.assertIsNone(x['retry_call_key'])
                self.assertEqual(before,rt.state(root/'runs/record-source-1-B'))
                self.assertFalse((root/'serial/000047/completion.json').exists())
                self.assertEqual(x['limits'],config['admission']['total_limits'])
                serial=NamedSerial(root/'serial',clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
                serial.call(named.PATHS[0]+':0',lambda:None)
                intent=read_record(root/'serial/000048/intent.json')
                self.assertGreaterEqual(intent['actual_gap_seconds'],60)
                self.assertEqual(intent['gap_basis'],'monotonic_wait_after_risk_acceptance_not_remote_completion')

    def test_new_stop_and_changed_history_are_not_exempt(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);config,_=self.fixture(root)
            with patch.object(named,'BATCH',digest(config)):
                named.register(root)
                rt.write(root/'STOP-000048.json',{'reason':'unknown'})
                with self.assertRaisesRegex(ValueError,'new_stop'):guard(root)
                (root/'STOP-000048.json').unlink()
                (root/'calls/000047/terminal.json').write_text('{}')
                with self.assertRaisesRegex(ValueError,'history'):guard(root)

    def test_safety_or_other_unknown_cannot_receive_this_disposition(self):
        for n,status,error in [('000047','safety_refusal','permission_denied'),('000020','unknown','TimeoutExpired')]:
            with self.subTest(n=n),tempfile.TemporaryDirectory() as t:
                root=Path(t);config,_=self.fixture(root);p=root/'calls'/n/'terminal.json';v=rt.read(p)
                v.update(status=status,error=error);p.write_bytes(json.dumps(v).encode())
                with patch.object(named,'BATCH',digest(config)):
                    with self.assertRaises(ValueError):named.register(root)
                self.assertFalse((root/named.NAME).exists())


if __name__=='__main__':unittest.main()
