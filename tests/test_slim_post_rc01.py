"""Only the new 40-path/120-call admission; simulated transport and clock."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_slim_batch import Clock, Fake, answer
from _slim_fixture import resources

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'docs/internal/optimization/sol61-slim-v0'
spec = importlib.util.spec_from_file_location('post_rc01_tests', HERE / 'post_rc01.py')
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)


class PostRC01Tests(unittest.TestCase):
    def setUp(self):
        self.adapter_root, self.binary = resources()
        self.enterContext(patch.object(r.m, "BINARY", self.binary))

    def fixture(self, td):
        root = Path(td).resolve(); previous = root / 'previous'; batch = root / 'new'
        parent = root / 'historical'; parent.mkdir()
        old = r.m.read(HERE / 'isolated-batch-r1/batch.json')
        old["adapter_root"] = self.adapter_root
        old["admission"]["binary"] = self.binary
        old['parent_receipt']['root'] = str(parent)
        r.m.write(previous / 'batch.json', old)
        r.m.write(previous / 'inputs.json', r.m.read(HERE / 'isolated-batch-r1/inputs.json'))
        receipt = dict(root=str(parent), previous_root=str(previous), logical_calls=98,
            previous_batch_sha256='OFFLINE_FIXTURE', evidence_sha256='OFFLINE_FIXTURE',
            historical_unknown=dict(status='risk_accepted_remote_unknown', remote_completion=None))
        return previous, batch, receipt

    def test_scope_identity_budget_and_no_second_allowance(self):
        with tempfile.TemporaryDirectory() as td:
            previous, batch, receipt = self.fixture(td)
            with patch.object(r, 'receipt', return_value=receipt):
                r.prepare(batch, previous); c = r.m.read(batch / 'batch.json')
                self.assertEqual((c['total_calls_max'], c['parent_receipt']['logical_calls']), (120, 98))
                self.assertEqual((c['baseline'], c['candidate']), (r.BASELINE, r.CANDIDATE))
                self.assertEqual(len(c['plan']), 40)
                self.assertEqual({p['case'] for p in c['plan'] if p['model']=='gpt-6-astra'}, {'F01','F02','W01','W02'})
                self.assertFalse(any(p['arm']=='bare' for p in c['plan']))
                self.assertNotIn('retry_000049', c); self.assertNotIn('prior_path_calls', c)
                with self.assertRaisesRegex(ValueError, 'already_bound'):
                    r.prepare(Path(td) / 'second', previous)
                with self.assertRaisesRegex(ValueError, 'root_or_binding_changed'):
                    r.validate(Path(td) / 'copy', c)
                with self.assertRaisesRegex(ValueError, 'configuration_changed'):
                    r.validate(batch, {**c, 'total_calls_max':121})
                identity = {k:c[k] for k in ('binary_sha256','cli_version')}
                for key, value in [('execution_authorized',False), ('new_calls_max',121), ('technical_retries_max',1), ('baseline',r.CANDIDATE)]:
                    with self.assertRaises(ValueError):
                        r.expected(previous, {**c['regression_admission'],key:value}, identity)

    def test_read_binding_cooldown_and_resume_without_regeneration(self):
        with tempfile.TemporaryDirectory() as td:
            previous, batch, receipt = self.fixture(td)
            with patch.object(r, 'receipt', return_value=receipt), patch.object(r.m, 'validate_successor', side_effect=r.validate), patch.object(r.m, 'inspect_bound_context', return_value={'simulation':True}):
                r.prepare(batch, previous)
                fake = Fake([dict(kind='read',text='SIMULATED READ',read_paths=['skills/wae/SKILL.md'],objection='simulation')]+[answer()]*40)
                fake.simulation=False; clock=Clock()
                r.m.drive(batch,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
                self.assertEqual(len(fake.prompts),41);self.assertEqual(clock.t,2460)
                self.assertEqual(len(list(batch.glob('runs/*/answer.txt'))),40)
                self.assertIn('--- skills/wae/SKILL.md ---',fake.prompts[1])
                self.assertNotIn('oracles.json',''.join(fake.prompts))
                intents=[r.m.read(p) for p in sorted(batch.glob('runs/*/call-*/intent.json'))]
                self.assertEqual([v['cumulative_call_ordinal'] for v in intents],list(range(99,140)))
                r.m.drive(batch,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
                self.assertEqual(len(fake.prompts),41)

    def test_unknown_still_stops_and_cannot_gain_new_allowance(self):
        with tempfile.TemporaryDirectory() as td:
            previous, batch, receipt = self.fixture(td)
            with patch.object(r, 'receipt', return_value=receipt), patch.object(r.m, 'validate_successor', side_effect=r.validate), patch.object(r.m, 'inspect_bound_context', return_value={'simulation':True}):
                r.prepare(batch, previous); fake=Fake([None,answer()]);fake.simulation=False;clock=Clock()
                r.m.drive(batch,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
                self.assertEqual(len(fake.prompts),1)
                self.assertEqual(r.m.read(batch/'STOP.json')['reason'],'unknown')
                self.assertEqual(list(batch.glob('scheduling/serial/[0-9]*/completion.json')),[])
                with self.assertRaisesRegex(ValueError,'stopped_no_resend'):r.m.drive(batch,adapter=fake)
                with self.assertRaisesRegex(ValueError,'already_bound'):r.prepare(Path(td)/'second',previous)

    def test_three_per_path_bounds_the_total_at_120(self):
        with tempfile.TemporaryDirectory() as td:
            previous, batch, receipt = self.fixture(td)
            with patch.object(r, 'receipt', return_value=receipt), patch.object(r.m, 'validate_successor', side_effect=r.validate), patch.object(r.m, 'inspect_bound_context', return_value={'simulation':True}):
                r.prepare(batch, previous)
                replies=[dict(kind='read',text='SIMULATED READ',read_paths=[p],objection='simulation') for p in ('skills/wae/SKILL.md','skills/wae/resources/methodology.md','skills/sra/SKILL.md')]*40
                fake=Fake(replies);fake.simulation=False;clock=Clock()
                r.m.drive(batch,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
                self.assertEqual(len(fake.prompts),120);self.assertEqual(clock.t,7200)
                self.assertEqual({r.m.read(p)['status'] for p in batch.glob('runs/*/result.json')},{'read_budget_exhausted'})
                self.assertEqual(r.m.read(sorted(batch.glob('runs/*/call-*/intent.json'))[-1])['cumulative_call_ordinal'],218)
                r.m.drive(batch,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
                self.assertEqual(len(fake.prompts),120)


if __name__=='__main__':unittest.main()
