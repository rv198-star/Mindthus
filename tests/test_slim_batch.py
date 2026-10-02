"""Only new #220 wiring; no model calls or semantic algorithm re-audit."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('slim_batch', ROOT/'docs/internal/optimization/sol61-slim-v0/run_batch.py')
m = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(m)
ADAPTER = '/Users/william/.codex/worktrees/jev-direct-continuation/Mindthus'


class Clock:
    def __init__(self): self.t = 0
    def now(self): return self.t
    def sleep(self, seconds): self.t += seconds


class Fake:
    simulation = True
    def __init__(self, replies): self.replies = iter(replies); self.prompts = []
    def invoke(self, req, wire, directory, config):
        self.prompts.append(wire['prompt'])
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
    def batch(self, root):
        config = m.prepare(root, ADAPTER, m.git(ROOT,'rev-parse','HEAD').decode().strip(), simulation=True)
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


if __name__ == '__main__': unittest.main()
