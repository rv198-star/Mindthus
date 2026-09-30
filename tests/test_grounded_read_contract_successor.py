"""Sending clarification and known-ended continuation only; all transports synthetic."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from experiments.grounded_judgment import runtime as rt, read_contract_successor as repair
from experiments.grounded_judgment.dispatch_demo import Clock
from experiments.grounded_judgment.development import cases
from experiments.jev_direct.serial import SerialRequests
from experiments.typed_decision.contracts import digest


class ReadContract(unittest.TestCase):
    def test_outbound_contract_states_existing_read_conditions_for_all_arms(self):
        with tempfile.TemporaryDirectory() as t:
            for arm in 'ABC':
                root=Path(t)/arm;rt.init(root,cases()[0]['documents'],arm)
                s=rt.state(root);s['phase']='draft';s['composition']={'findings':[]};rt.append(root,'state',s)
                req=rt.request(root);contract=req['payload']['output_contract']
                self.assertIn('exactly empty string',contract['text'])
                self.assertIn('not already loaded',contract['read_paths'])
                self.assertIn('revision: answer only',contract['kind'])

    def fixture(self, root):
        changed=('runtime.py','dispatch.py','resume_000007.py')
        config={'source_sha256':{'experiments/grounded_judgment/'+p:'old-source-fixture' for p in changed}}
        rt.write(root/'batch.json',config);rt.write(root/'STOP.json',{'reason':'technical_pause_read_contract_omission'})
        (root/'calls').mkdir();(root/'runs').mkdir()
        rt.write(root/'runs/debit.json',{'prior_calls':34,'failed_paths':['display-goal-2-C','mechanism-object-2-A']})
        clock=Clock();serial=SerialRequests(root/'serial',clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
        for i in range(34):
            d=root/'calls'/f'{i:06d}';d.mkdir();binding={'call':i}
            rt.write(d/'terminal.json',{'status':'returned','binding':binding})
            rt.write(d/'raw.json',{'binding':binding});rt.write(d/'import.json',{})
            rt.write(d/'envelope.json',{'response':{'kind':'read' if i in (11,29) else 'answer', 'text':'synthetic'}})
            serial.call('fixture:'+str(i),lambda:{'status':'returned'})
        return config

    def test_exact_known_ended_continuation_preserves_debits_and_new_stops_block(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);config=self.fixture(root);before=(root/'runs/debit.json').read_bytes()
            with patch.object(repair,'BATCH',digest(config)):
                x=repair.register(root)
                self.assertIsNone(x['retry_call_key']);self.assertFalse(x['budgets_reset'])
                self.assertEqual(before,(root/'runs/debit.json').read_bytes())
                (root/'runs/events').mkdir()
                rt.write(root/'runs/events/next.json',{'new_event':True})
                self.assertEqual(repair.verified(root)['prior_calls'],x['prior_calls'])
                rt.write(root/'STOP-000034.json',{'reason':'unknown'})
                with self.assertRaisesRegex(ValueError,'no_new_stop'):repair.verified(root)

    def test_unknown_safety_and_wrong_batch_are_not_exempt(self):
        for status in ('unknown','safety_refusal'):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as t:
                root=Path(t);config=self.fixture(root)
                p=root/'calls/000033/terminal.json';p.write_text(json.dumps({'status':status,'binding':{'call':33}}))
                with patch.object(repair,'BATCH',digest(config)):
                    with self.assertRaisesRegex(ValueError,'no_unknown_or_unimported'):repair.register(root)
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root)
            with self.assertRaisesRegex(ValueError,'exact_batch'):repair.register(root)


if __name__=='__main__':unittest.main()
