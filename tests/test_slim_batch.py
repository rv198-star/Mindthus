"""Only new #220 wiring; no model calls or semantic algorithm re-audit."""
import importlib.util
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest.mock import patch
import shutil

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('slim_batch', ROOT/'docs/internal/optimization/sol61-slim-v0/run_batch.py')
m = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(m)
from _slim_fixture import resources


class Clock:
    def __init__(self): self.t = 0
    def now(self): return self.t
    def sleep(self, seconds): self.t += seconds


class Fake:
    simulation = True
    def __init__(self, replies): self.replies = iter(replies); self.prompts = []; self.directories=[]
    def invoke(self, req, wire, directory, config):
        self.prompts.append(wire['prompt'])
        self.directories.append(directory)
        reply = next(self.replies)
        if reply is None:
            return dict(kind='cli',events=[dict(type='thread.started',thread_id='sim-thread')],
                returncode=1,stdout='',stderr='simulated local timeout',reply_text=None)
        events = [dict(type='thread.started',thread_id='sim-thread'),dict(type='turn.started'),
            dict(type='turn.completed',usage=dict(input_tokens=10,output_tokens=10))]
        return dict(kind='cli',events=events,returncode=0,stdout='',stderr='',reply_text=json.dumps(reply))


def answer(text='SIMULATION ONLY'):
    return dict(kind='answer',text=text,read_paths=[],objection='simulation')


class SlimBatchTests(unittest.TestCase):
    def setUp(self):
        self.adapter_root, binary = resources()
        self.enterContext(patch.object(m, "BINARY", binary))

    def batch(self, root):
        config = m.prepare(root, self.adapter_root, m.git(ROOT,'rev-parse','HEAD').decode().strip(), simulation=True)
        # Reduce only a simulated test plan, retaining the authorized hard caps.
        config['plan'] = config['plan'][:2]
        (root/'batch.json').write_text(json.dumps(config))
        (root/'batch-binding.json').write_text(json.dumps(dict(sha256=m.digest(config))))
        return config

    def test_plan_and_input_separation(self):
        cases = m.read(m.HERE/'cases.json')['business_cases']
        self.assertEqual(len(m.plan(cases)),44)
        self.assertEqual(sum(p['model']=='gpt-6-astra' for p in m.plan(cases)),8)
        self.assertEqual(sum(p['arm']=='bare' for p in m.plan(cases)),4)
        for c in cases:
            self.assertEqual(m.render(c),c['prompt']+('\n\n'+c['condition'] if c['condition'] else ''))

    def test_read_raw_terminal_import_and_cross_arm_cooldown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'batch'; self.batch(root)
            fake=Fake([dict(kind='read',text='need method',read_paths=['skills/wae/SKILL.md'],objection=''),answer(),answer()])
            clock=Clock();m.drive(root,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
            self.assertEqual(clock.t,120)
            self.assertIn('--- skills/wae/SKILL.md ---',fake.prompts[1])
            self.assertNotIn('oracles.json',''.join(fake.prompts))
            self.assertEqual(len(list(root.glob('runs/*/answer.txt'))),2)
            for raw in root.glob('runs/*/call-*/raw.json'):
                value=m.read(raw);terminal=m.read(raw.with_name('terminal.json'))
                self.assertTrue(value['binding']['simulation'])
                self.assertEqual(terminal['raw_sha256'],m.digest(value['transport']))
                self.assertEqual(terminal['binding'],value['binding'])

    def test_unknown_stops_without_completion_or_second_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'batch';self.batch(root);fake=Fake([None,answer()]);clock=Clock()
            m.drive(root,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
            self.assertEqual(len(fake.prompts),1)
            self.assertEqual(m.read(root/'STOP.json')['reason'],'unknown')
            self.assertEqual(list(root.glob('scheduling/serial/[0-9]*/completion.json')),[])
            with self.assertRaisesRegex(ValueError,'stopped_no_resend'):
                m.drive(root,adapter=fake)

    def test_simulation_cannot_dispatch_through_official_adapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'batch';self.batch(root)
            with self.assertRaisesRegex(ValueError,'adapter_mode_mismatch'): m.drive(root)
            self.assertEqual(list(root.glob('runs/*/call-*/intent.json')),[])

    def test_three_reads_stop_at_path_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'batch';self.batch(root)
            replies=[dict(kind='read',text='need relevant detail',read_paths=[p],objection='') for p in (
                'skills/wae/SKILL.md','skills/wae/resources/methodology.md','skills/sra/SKILL.md')]
            fake=Fake(replies+[answer()]);clock=Clock();m.drive(root,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
            first=sorted(root.glob('runs/*/result.json'))[0]
            self.assertEqual(m.read(first)['status'],'read_budget_exhausted')
            self.assertEqual(len(list(first.parent.glob('call-*/intent.json'))),3)

    def test_repository_ancestor_cannot_enter_transport_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            project=Path(tmp)/'project';project.mkdir();(project/'AGENTS.md').write_text('SENTINEL_REPO_INSTRUCTION')
            root=project/'.tplan'/'batch';self.batch(root);fake=Fake([answer(),answer()]);clock=Clock()
            m.drive(root,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
            for directory in fake.directories:
                self.assertFalse(directory.is_relative_to(project))
                self.assertTrue(all(not (p/'AGENTS.md').exists() for p in (directory,*directory.parents)))
            self.assertNotIn('SENTINEL_REPO_INSTRUCTION',''.join(fake.prompts))
            self.assertEqual(len(list(root.glob('runs/*/call-*/workspace-binding.json'))),2)

    def test_legacy_in_repository_batch_cannot_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'batch';c=self.batch(root);del c['workspace_mode']
            (root/'batch.json').write_text(json.dumps(c));(root/'batch-binding.json').write_text(json.dumps(dict(sha256=m.digest(c))))
            fake=Fake([answer()])
            with self.assertRaisesRegex(ValueError,'legacy_workspace_not_isolated'):m.drive(root,adapter=fake)
            self.assertEqual(fake.prompts,[])

    def test_pending_successor_authority_does_not_send_or_reset_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'batch';c=self.batch(root);c['simulation']=False
            c['successor_admission']=dict(execution_authorized=False,cumulative_call_limit=98)
            (root/'batch.json').write_text(json.dumps(c));(root/'batch-binding.json').write_text(json.dumps(dict(sha256=m.digest(c))))
            with self.assertRaisesRegex(ValueError,'successor_not_authorized'):m.drive(root)
            self.assertEqual(list(root.glob('runs/*/call-*/intent.json')),[])

    def test_old_34_calls_are_debited_not_restored(self):
        self.assertEqual(m.carry_budget(34,64),30)
        self.assertEqual(m.carry_budget(34,98),64)
        with self.assertRaisesRegex(ValueError,'successor_cumulative_limit'):m.carry_budget(34,99)

    def test_simulated_parent_cannot_supply_real_successor_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'batch';self.batch(root)
            with self.assertRaisesRegex(ValueError,'simulated_parent_not_real'):m.parent_receipt(root)

    def test_internal_recovery_stops_every_response_branch_and_restart(self):
        read_reply=dict(kind='read',text='need method',read_paths=['skills/wae/SKILL.md'],objection='')
        bad_read={**read_reply,'read_paths':['skills/using-mindthus/SKILL.md']}
        cases=[('bad_json',answer(),'failed'),('bad_read',bad_read,'returned'),
               ('answer',answer(),'returned'),('read',read_reply,'returned'),
               ('unknown',None,'unknown'),('safety_refusal',answer(),'safety_refusal')]
        for mode,reply,terminal_status in cases:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                class Recovering(Fake):
                    def invoke(self,*args):
                        raw=super().invoke(*args)
                        raw['stderr']='retrying sampling request'
                        if mode=='bad_json':raw['reply_text']='{'
                        if mode=='safety_refusal':
                            raw['events'][-1]={'type':'turn.failed','error':{'code':'permission_denied'}}
                        return raw
                root=Path(tmp)/'batch';self.batch(root);fake=Recovering([reply,answer()]);clock=Clock()
                m.drive(root,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
                self.assertEqual(len(fake.prompts),1)
                self.assertTrue((root/'transport-stop-v2.json').exists())
                terminal=next(root.glob('runs/*/call-*/terminal.json'))
                self.assertEqual(m.read(terminal)['status'],terminal_status)
                self.assertEqual(len(list(root.glob('scheduling/serial/[0-9]*/completion.json'))),0 if mode=='unknown' else 1)
                if mode=='answer':self.assertEqual(next(root.glob('runs/*/answer.txt')).read_text(),'SIMULATION ONLY')
                with self.assertRaisesRegex(ValueError,'batch_stopped_no_resend'):m.drive(root,adapter=fake)
                self.assertEqual(len(fake.prompts),1)

    def test_existing_transport_stop_alone_prevents_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'batch';self.batch(root);m.write(root/'transport-stop-v2.json',{'simulation':True})
            fake=Fake([answer()])
            with self.assertRaisesRegex(ValueError,'batch_stopped_no_resend'):m.drive(root,adapter=fake)
            self.assertEqual(fake.prompts,[])

    def test_empty_answers_preserve_terminal_without_delivery_or_retry(self):
        for text in ('',' \n\t'):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)/'batch';self.batch(root);fake=Fake([answer(text),answer()]);clock=Clock()
                m.drive(root,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
                first=sorted(root.glob('runs/*/result.json'))[0]
                self.assertEqual(m.read(first),dict(status='format_failure',answer=None,error='empty_answer'))
                self.assertFalse((first.parent/'answer.txt').exists())
                self.assertEqual(m.read(first.parent/'call-00/terminal.json')['status'],'returned')
                self.assertEqual(m.read(first.parent/'call-00/raw.json')['transport']['reply_text'],json.dumps(answer(text)))
                self.assertEqual(len(fake.prompts),2)  # Next independent path, never a retry.
                m.drive(root,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
                self.assertEqual(len(fake.prompts),2)

    def test_pending_prepare_cannot_claim_a_successor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'child';parent=Path(tmp)/'parent';parent.mkdir()
            with self.assertRaisesRegex(ValueError,'successor_not_authorized_no_prepare'):
                m.prepare(root,self.adapter_root,'HEAD',admission={'execution_authorized':False},parent_batch=parent)
            self.assertFalse(root.exists())
            self.assertEqual(list(parent.iterdir()),[])

    def test_successor_claim_is_exclusive_even_for_concurrent_preparations(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent=Path(tmp)/'parent';parent.mkdir();roots=[Path(tmp)/'one',Path(tmp)/'two']
            receipt={'root':str(parent),'logical_calls':34,'fixture':'offline only'}
            config={'simulation':False,'parent_receipt':receipt}
            locked=m.adapters(self.adapter_root)['_locked'];barrier=Barrier(2)
            def claim(root):
                barrier.wait()
                try:m.bind_successor(root,config,locked);return 'bound'
                except (ValueError,RuntimeError) as error:return str(error)
            with patch.object(m,'parent_receipt',return_value=receipt), ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(claim,roots))
                self.assertEqual(results.count('bound'),1)
                winner=roots[results.index('bound')];loser=next(r for r in roots if r!=winner)
                m.validate_successor(winner,config)
                with self.assertRaisesRegex(ValueError,'parent_successor_already_bound'):m.bind_successor(loser,config,locked)
                with self.assertRaisesRegex(ValueError,'successor_root_or_configuration_not_bound'):m.validate_successor(loser,config)
                self.assertEqual(m.driver_lock_path(winner,config),m.driver_lock_path(loser,config))

    def test_bound_successor_resumes_without_resend_and_rejects_copied_root(self):
        # The real-mode guards are exercised with a synthetic parent and Fake only.
        # No real parent registration, authentication or model transport is touched.
        with tempfile.TemporaryDirectory() as tmp:
            parent=Path(tmp)/'parent';parent.mkdir();root=Path(tmp)/'child';c=self.batch(root)
            receipt={'root':str(parent),'logical_calls':34,'fixture':'offline only'}
            c.update(simulation=False,parent_receipt=receipt,
                     successor_admission={'execution_authorized':True,'cumulative_call_limit':98})
            (root/'batch.json').write_text(json.dumps(c));(root/'batch-binding.json').write_text(json.dumps(dict(sha256=m.digest(c))))
            fake=Fake([answer(),answer()]);fake.simulation=False;clock=Clock()
            with patch.object(m,'parent_receipt',return_value=receipt), patch.object(m,'inspect_bound_context',return_value={'simulation':True}):
                m.bind_successor(root,c,m.adapters(self.adapter_root)['_locked'])
                m.drive(root,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
                self.assertEqual(clock.t,120)  # Parent cooling plus cross-arm cooling.
                self.assertEqual(len(fake.prompts),2)
                m.drive(root,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
                self.assertEqual(len(fake.prompts),2)
                copied=Path(tmp)/'copy';shutil.copytree(root,copied)
                with self.assertRaisesRegex(ValueError,'successor_root_or_configuration_not_bound'):
                    m.drive(copied,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
                self.assertEqual(len(fake.prompts),2)


if __name__ == '__main__': unittest.main()
