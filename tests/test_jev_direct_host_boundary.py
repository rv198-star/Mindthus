"""Regression inputs are the actual A1 schema and bound format-error archive.

Temporary workspace paths are rebased only for isolated fixtures. No model calls.
"""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from experiments.jev_direct import host_boundary as h, pilot as p, technical_retry as t
from experiments.jev_direct.serial import SerialRequests
from experiments.typed_decision.contracts import digest, ContractError
from experiments.typed_decision.relationship_runtime import save
from experiments.typed_decision.session import read_record, RecoveryRequired
from tests.test_jev_direct_local import Clock

EVIDENCE = p.REPO/'docs/internal/research/typed-decision/jev-direct-v2/a1-native-live-2026-09-27/evidence'
FIXTURE = p.REPO/'tests/fixtures/jev_direct_schema_failure/archive-events.jsonl'
THREAD = '01a0e2ac-1892-7ad2-8174-46902011b269'


class HostBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = (Path(self.tmp.name)/'batch').resolve()
        cases = read_record(EVIDENCE/'freeze.json')['cases']
        self.f = p.prepare(self.root, cases, binary=shutil.which('codex'), serial_gap_seconds=60)
        self.old = self.root/'runs/A1/native/host/0'
        shutil.copytree(EVIDENCE/'runs/A1/native/host/0', self.old)
        shutil.copyfile(EVIDENCE/'operator.stderr.txt', self.root/'operator.stderr.txt')
        self.schema = json.loads((self.old/'schema.json').read_text())
        self.events = [json.loads(x) for x in FIXTURE.read_text().splitlines()]
        for e in self.events:
            if e['type'] in ('session_meta','turn_context'):
                e['payload']['cwd'] = str(self.old/'workspace')
        self.archive = Path(self.tmp.name)/'archive.jsonl'; self.write_archive()
        intent = read_record(EVIDENCE/'serial/000000/intent.json')
        intent['label'] = 'host:'+str(self.old)
        save(self.root/'serial/000000/intent.json', intent)
        save(self.root/'serial-bindings/000000/intent.json', {'intent_sha256': digest(intent)})
        self.clock = Clock(); self.clock.now = 1790509400
        self.gate = SerialRequests(self.root/'serial', clock=self.clock.time, monotonic=self.clock.time, sleep=self.clock.sleep)
        self.calls = []; self.reply = {'action':'answer','text':'fixture answer','read_paths':[], 'used_methods':[], 'route_objection':''}

    def write_archive(self):
        self.archive.write_text('\n'.join(json.dumps(e) for e in self.events)+'\n')

    def reconcile(self):
        return h.reconcile_schema_failure(self.root, self.old, self.archive, THREAD)

    def cli(self, cmd, prompt, env, timeout):
        self.calls.append(cmd)
        sent = json.loads(Path(cmd[cmd.index('--output-schema')+1]).read_text())
        self.assertEqual(sent, h.api_schema(self.schema))
        self.assertEqual(prompt, (self.old/'prompt.txt').read_text())
        self.assertEqual(cmd[cmd.index('-m')+1], 'gpt-6-sol')
        self.assertIn('model_reasoning_effort="xhigh"', cmd)
        self.assertEqual(timeout, 360)
        Path(cmd[cmd.index('-o')+1]).write_text(json.dumps(self.reply))
        return subprocess.CompletedProcess(cmd,0,'\n'.join(json.dumps(e) for e in [
            {'type':'thread.started','thread_id':'fixture-new'}, {'type':'turn.completed','usage':{}}]),'')

    def run_retry(self):
        with patch.object(p.wire, '_run_cli', side_effect=self.cli):
            return t.run_once(self.root, scheduler=self.gate)

    def test_real_schema_projection_keeps_full_contract_and_only_removes_two_constraints(self):
        original = deepcopy(self.schema); sent = h.api_schema(self.schema)
        expected = deepcopy(original)
        for key in ('read_paths','used_methods'):
            del expected['properties'][key]['uniqueItems']
        self.assertEqual(sent, expected); self.assertEqual(self.schema, original)
        sent['properties']['action']['enum'].append('mutation')
        self.assertEqual(self.schema, original)

    def test_only_schema_nodes_are_projected(self):
        contract = {'type':'object','properties':{'uniqueItems':{'type':'array','uniqueItems':True}},
                    'enum':[{'uniqueItems':True}], '$defs':{'nested':{'anyOf':[{'type':'array','uniqueItems':True}]}}}
        sent = h.api_schema(contract)
        self.assertIn('uniqueItems', sent['properties'])
        self.assertEqual(sent['enum'], [{'uniqueItems':True}])
        self.assertNotIn('uniqueItems', sent['$defs']['nested']['anyOf'][0])

    def test_duplicates_and_illegal_enums_still_fail_local_contract(self):
        for field, values in [('read_paths',['skills/edsp/SKILL.md']*2),('used_methods',['edsp']*2),
                              ('read_paths',['not/a/source']),('used_methods',['not-a-method'])]:
            reply = dict(self.reply, **{field:values})
            with self.subTest(field=field,values=values), self.assertRaises(ContractError):
                p.wire._wire_check(reply, self.schema)

    def test_real_failure_is_bound_and_reconciliation_is_append_only(self):
        before = p.exact_tree(self.root)
        self.reconcile(); self.reconcile(); self.gate.validate()
        self.assertTrue(all(p.r.file_hash(self.root/k) == v for k,v in before.items()))
        self.assertFalse((self.root/'serial/000000/completion.json').exists())
        self.assertFalse((self.old/'outcome.json').exists())
        receipt = h.validate_reconciliation(self.old)
        self.assertEqual(receipt['failure_kind'], 'invalid_json_schema')
        self.assertEqual(receipt['host_session_seconds'], 28.518)
        self.assertIsNone(receipt['http_seconds'])
        self.assertFalse(receipt['automatic_retry'])

    def test_wrong_thread_turn_prompt_missing_terminal_and_safety_error_cannot_unlock(self):
        mutations = [lambda a:a[0]['payload'].update(id='another-thread'),
                     lambda a:a[-1]['payload'].update(turn_id='another-turn'),
                     lambda a:a[3]['payload']['item']['content'][0].update(text='other request'),
                     lambda a:a.pop(),
                     lambda a:a[-1]['payload']['error'].update(message='safety refusal')]
        for mutate in mutations:
            events = deepcopy(self.events); mutate(events)
            with self.subTest(mutate=mutate), self.assertRaises(ContractError):
                h.bound_schema_failure(events, self.old, THREAD)
        with self.assertRaisesRegex(RecoveryRequired, 'unknown_request'):
            self.gate.validate()

    def test_reconciliation_does_not_clear_another_unknown_request(self):
        self.reconcile()
        last = read_record(self.root/'serial/000000/failure.json')
        intent = {'label':'unknown-other','started_at_epoch':1790509500,'previous_completion_sha256':digest(last),
                  'previous_end_epoch':last['ended_at_epoch'],'actual_gap_seconds':60,'gap_basis':'monotonic','wall_gap_seconds':100}
        save(self.root/'serial/000001/intent.json', intent)
        save(self.root/'serial-bindings/000001/intent.json', {'intent_sha256':digest(intent)})
        with self.assertRaisesRegex(RecoveryRequired, 'unknown_request'), patch.object(p.wire,'_run_cli') as cli:
            t.register(self.root)
        cli.assert_not_called()

    def test_single_retry_inherits_budget_same_request_and_reentry_never_sends(self):
        self.reconcile(); successor = t.register(self.root)
        self.assertEqual((successor['previous_attempts'],successor['remaining_attempts_before']), (1,3))
        out = self.run_retry(); cached = self.run_retry()
        self.assertEqual(out, cached); self.assertEqual(len(self.calls), 1)
        self.assertEqual(out['status'], 'delivered')
        self.assertEqual((out['total_host_attempts'],out['remaining_host_attempts']), (2,2))
        self.assertEqual(self.clock.waits, [60])
        self.assertEqual(len(list((self.root/'serial').glob('*/intent.json'))), 2)
        self.assertEqual(json.loads((self.old.parent/'1/schema.json').read_text()), self.schema)

    def test_read_request_stops_without_second_call(self):
        self.reconcile(); t.register(self.root)
        self.reply.update(action='read',text='',read_paths=['skills/edsp/SKILL.md'])
        self.assertEqual(self.run_retry()['status'], 'read_requested')
        self.assertEqual(len(self.calls), 1)

    def test_unloaded_method_claim_is_rejected(self):
        self.reconcile(); t.register(self.root); self.reply['used_methods'] = ['edsp']
        self.assertEqual(self.run_retry()['reason'], 'pilot_unread_method_claim')

    def test_new_bound_schema_failure_is_definite_and_reentry_does_not_resend(self):
        self.reconcile(); t.register(self.root)
        for e in self.events:
            if e['type'] in ('session_meta','turn_context'):
                e['payload']['cwd'] = str(self.old.parent/'1/workspace')
        self.write_archive()
        proc = subprocess.CompletedProcess([],1,json.dumps({'type':'thread.started','thread_id':THREAD}), 'schema error')
        def capture(directory, thread):
            return h.capture_schema_failure(directory,self.archive,thread)
        with patch.object(p.wire,'_run_cli',return_value=proc) as cli, patch.object(p,'cli_schema_failure',side_effect=capture):
            out = t.run_once(self.root,scheduler=self.gate)
            self.assertEqual(out['status'],'host_failed')
            self.assertEqual(out['outcome']['failure_kind'],'request_schema')
            self.assertEqual(t.run_once(self.root,scheduler=self.gate),out)
            self.assertEqual(cli.call_count,1)
        self.gate.validate()

    def test_timeout_missing_terminal_and_plain_error_remain_unknown(self):
        for effect in (subprocess.TimeoutExpired('codex',1), subprocess.CompletedProcess([],0,'',''),
                       subprocess.CompletedProcess([],1,'{"type":"error","message":"invalid_json_schema"}','failure')):
            with self.subTest(effect=effect):
                # Each subcase gets a distinct isolated batch, never a new live root.
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)/'batch'; f = p.prepare(root,self.f['cases'],binary=self.f['binary'],serial_gap_seconds=60)
                    kw = {'side_effect':effect} if isinstance(effect,Exception) else {'return_value':effect}
                    with patch.object(p.wire,'_run_cli',**kw):
                        with self.assertRaisesRegex(RecoveryRequired,'completion_unknown'):
                            p.host_call(root/'runs/A1/native/host','0',{},self.schema,f)
                    self.assertFalse((root/'serial/000000/completion.json').exists())
                    with self.assertRaises(RecoveryRequired), patch.object(p.wire,'_run_cli') as cli:
                        p.host_call(root/'runs/A1/native/host','0',{},self.schema,f)
                    cli.assert_not_called()

    def test_stdout_turn_failed_is_not_archive_task_complete(self):
        events = [{'type':'thread.started','thread_id':THREAD}, {'type':'turn.failed','error':self.events[-1]['payload']['error']}]
        with self.assertRaises(ContractError):h.bound_schema_failure(events,self.old,THREAD)


if __name__ == '__main__':
    unittest.main()
