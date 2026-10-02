"""Only the newly authorized single-call continuation; Fake transport, no API."""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_slim_batch import Clock, Fake, answer

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'docs/internal/optimization/sol61-slim-v0'
spec=importlib.util.spec_from_file_location('scoped_retry',HERE/'retry_000049.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
AUTH=dict(execution_authorized=True,request_sha256=r.REQUEST_SHA,cumulative_call_limit=98,
    technical_retries_max=1,authorization_ref='OFFLINE FIXTURE ONLY')


class Retry000049Tests(unittest.TestCase):
    def fixture(self,directory):
        parent=(Path(directory)/'isolated').resolve();parent.mkdir()
        old=r.m.read(HERE/'isolated-batch-r1/batch.json')
        old['parent_receipt']['root']=str(Path(directory)/'earlier')
        r.m.write(parent/'batch.json',old)
        r.m.write(parent/'inputs.json',r.m.read(HERE/'isolated-batch-r1/inputs.json'))
        for arm in ('current','slim'):
            r.m.write(parent/'sources'/f'{arm}.json',r.m.materials(old['baseline' if arm=='current' else 'candidate']))
        receipt=dict(root=str(parent),batch_sha256=r.PARENT_SHA,logical_calls=50,earlier_calls=34,
            evidence_sha256='OFFLINE ONLY',spent_session_seconds=1113.8422797060193,request_sha256=r.REQUEST_SHA)
        return parent,receipt

    def test_exact_named_authority_remaining_budget_and_identity(self):
        with tempfile.TemporaryDirectory() as td:
            parent,receipt=self.fixture(td)
            with patch.object(r,'receipt',return_value=receipt):
                child=r.prepare(parent,AUTH);c=r.m.read(child/'batch.json')
                self.assertEqual(c['total_calls_max'],14)
                self.assertEqual(c['prior_path_calls'],{'31':1})
                self.assertEqual(c['plan_start_index'],31);self.assertEqual(len(c['plan']),13)
                self.assertEqual(c['plan'][0],dict(case='L02',arm='current',model='gpt-6.1-sol'))
                self.assertEqual(c['effort'],'medium');self.assertEqual(c['candidate'],'7fcaad8028bcf37156b9aea30e07f72d90bbb20d')
                self.assertEqual(r.m.read(parent/r.DISPOSITION)['status'],'risk_accepted_remote_unknown')
                self.assertFalse((parent/'scheduling/serial/000049/completion.json').exists())
                for bad in ({**AUTH,'request_sha256':'other'}, {**AUTH,'execution_authorized':False},
                            {**AUTH,'cumulative_call_limit':99}, {**AUTH,'technical_retries_max':2}):
                    with self.assertRaises(ValueError):r.expected(parent,bad,{k:c[k] for k in ('binary_sha256','cli_version')})
                with self.assertRaisesRegex(ValueError,'already_registered'):r.prepare(parent,AUTH)
                with self.assertRaisesRegex(ValueError,'root_changed'):r.validate(Path(td)/'copy',c)

    def test_fake_read_then_answer_and_remaining_paths_use_at_most14(self):
        with tempfile.TemporaryDirectory() as td:
            parent,receipt=self.fixture(td)
            with patch.object(r,'receipt',return_value=receipt),patch.object(r.m,'validate_successor',side_effect=r.validate),patch.object(r.m,'inspect_bound_context',return_value={'simulation':True}):
                child=r.prepare(parent,AUTH)
                replies=[dict(kind='read',text='need TPlan',read_paths=['skills/tplan/SKILL.md'],objection='simulation')]+[answer()]*13
                fake=Fake(replies);fake.simulation=False;clock=Clock()
                r.m.drive(child,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
                self.assertEqual(len(fake.prompts),14);self.assertEqual(clock.t,840)
                self.assertEqual(len(list(child.glob('runs/*/answer.txt'))),13)
                old=r.m.read(HERE/'isolated-batch-r1'/r.UNKNOWN/'wire.json')
                self.assertEqual(fake.prompts[0],old['prompt'])
                intents=[r.m.read(p) for p in sorted(child.glob('runs/*/call-*/intent.json'))]
                self.assertEqual(intents[0]['retry_of'],r.REQUEST_SHA)
                self.assertEqual([i['cumulative_call_ordinal'] for i in intents],list(range(85,99)))
                measurements=[r.m.read(p) for p in child.glob('runs/*/call-*/measurement.json')]
                self.assertEqual(sum(v['outer_retries'] for v in measurements),1)
                r.m.drive(child,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
                self.assertEqual(len(fake.prompts),14)
                c=r.m.read(child/'batch.json');c['total_calls_max']=15
                with self.assertRaisesRegex(ValueError,'config_changed'):r.validate(child,c)

    def test_new_unknown_stops_without_second_retry(self):
        with tempfile.TemporaryDirectory() as td:
            parent,receipt=self.fixture(td)
            with patch.object(r,'receipt',return_value=receipt),patch.object(r.m,'validate_successor',side_effect=r.validate),patch.object(r.m,'inspect_bound_context',return_value={'simulation':True}):
                child=r.prepare(parent,AUTH);fake=Fake([None,answer()]);fake.simulation=False;clock=Clock()
                r.m.drive(child,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
                self.assertEqual(len(fake.prompts),1)
                self.assertEqual(r.m.read(child/'STOP.json')['reason'],'unknown')
                self.assertEqual(list(child.glob('scheduling/serial/[0-9]*/completion.json')),[])
                with self.assertRaisesRegex(ValueError,'stopped_no_resend'):
                    r.m.drive(child,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
                self.assertEqual(len(fake.prompts),1)

if __name__=='__main__':unittest.main()
