"""Q2 contract tests against real canonical transactions and disposable Missions."""
import concurrent.futures
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills/tplan/scripts"
sys.path.insert(0, str(SCRIPTS))
import tplan_runtime as runtime
import tplan_commands as commands
from query_runtime import query


def snapshot(directory):
    return {str(p.relative_to(directory)): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in directory.rglob('*') if p.is_file() and p.name != '.execution_trace.lock'}


class CommandRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tplan-q2-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mission = self.create('command-mission', enable=True)
        self.request = {'protocol': commands.PROTOCOL, 'action': 'evidence.record',
                        'mission_id': 'command-mission', 'command_id': 'request-1',
                        'expected_build_hash': runtime.runtime_fingerprint()['build_hash'],
                        'payload': {'summary': 'Synthetic ordinary observation', 'task_id': 'T1',
                                    'data': {'value': 17}}}
        self.principal = 'test-host'

    def create(self, name, enable=False, scripts=SCRIPTS):
        directory = self.root / name
        tasks = self.root / (name + '-tasks.json')
        tasks.write_text(json.dumps([{'id':'T1','title':'Contract fixture','role':'success-critical',
            'mission_contribution':'Exercise local commands','acceptance_evidence':['A1']}]))
        args = ['--dir',str(directory),'--mission-id',name,'--title',name,
                '--objective','Verify command transactions','--acceptance-evidence','A1:Verified result',
                '--task-json',str(tasks)]
        if enable: args.append('--command-results')
        r = self.script('init_mission.py', *args, scripts=scripts)
        self.assertEqual(r.returncode,0,r.stderr)
        return directory

    def script(self, name, *args, scripts=SCRIPTS):
        return subprocess.run([sys.executable,'-B',str(scripts/name),*args], text=True,
                              capture_output=True,timeout=20)

    def run_command(self, request=None, principal=None):
        return commands.execute(self.mission, request or self.request,
                                principal=principal or self.principal)

    def cli(self, request=None):
        return self.script('command_runtime.py','--mission-dir',str(self.mission),
                           '--principal',self.principal,'--request-json',json.dumps(request or self.request))

    def result_query(self, action='command.get'):
        request = {k:v for k,v in self.request.items() if k != 'payload'}
        return {**request,'action':action}

    def read_query(self):
        return query(self.mission, {'protocol':'tplan.query.v1','action':'command.get',
            'request_id':'read-1','mission_id':self.request['mission_id'],'command_id':'request-1',
            'expected_build_hash':self.request['expected_build_hash']})

    def test_commit_and_read_command_share_same_canonical_result(self):
        result, code = self.run_command()
        self.assertEqual(code,0,result)
        self.assertEqual(result['status'],'committed')
        state = json.loads((self.mission/'mission.json').read_text())
        stored = state['command_results']['records']['request-1']
        events = runtime.read_events(self.mission)
        self.assertEqual(len(events),1)
        self.assertEqual(stored,result['data'])
        self.assertEqual(stored['evidence_id'],events[0]['id'])
        self.assertEqual(events[0]['event_type'],'observation')
        observed, code = self.read_query()
        self.assertEqual(code,0,observed)
        self.assertEqual(observed['data']['result'],stored)
        self.assertEqual(observed['data']['authority'],'historical_result_only')

    def test_same_request_replays_without_any_business_write(self):
        first, _ = self.run_command();before=snapshot(self.mission)
        replay, code = self.run_command()
        self.assertEqual((code,replay['status']),(0,'replayed'))
        self.assertEqual(first['data'],replay['data']);self.assertEqual(before,snapshot(self.mission))

    def test_same_id_different_payload_or_caller_conflicts(self):
        self.run_command();before=snapshot(self.mission)
        changed=copy.deepcopy(self.request);changed['payload']['summary']='Different'
        for req,actor in [(changed,self.principal),(self.request,'different-host')]:
            value,code=commands.execute(self.mission,req,principal=actor)
            self.assertEqual((code,value['code']),(13,'command_conflict'))
            self.assertEqual(before,snapshot(self.mission))

    def test_multiple_processes_same_command_commit_only_once(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            results=list(pool.map(lambda _:self.cli(),range(6)))
        for r in results:self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        statuses=[json.loads(r.stdout)['status'] for r in results]
        self.assertEqual(statuses.count('committed'),1)
        self.assertEqual(statuses.count('replayed'),5)
        self.assertEqual(len(runtime.read_events(self.mission)),1)

    def test_different_parallel_commands_keep_distinct_results(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(self.cli,[{**self.request,'command_id':f'request-{i}'} for i in range(4)]))
        for r in results:self.assertEqual(r.returncode,0,r.stdout)
        self.assertEqual(len({x['id'] for x in runtime.read_events(self.mission)}),4)
        self.assertEqual(len(json.loads((self.mission/'mission.json').read_text())['command_results']['records']),4)

    def test_explicit_opt_in_is_required_without_state_adoption(self):
        directory=self.create('default-mission')
        req={**self.request,'mission_id':'default-mission'};before=snapshot(directory)
        value,code=commands.execute(directory,req,principal=self.principal)
        self.assertEqual((code,value['code']),(3,'unsupported_capability'))
        self.assertEqual(before,snapshot(directory))
        path=self.mission/'mission.json';state=json.loads(path.read_text());state.pop('runtime_provenance')
        path.write_text(json.dumps(state));before=snapshot(self.mission)
        value,code=self.run_command();self.assertEqual(code,5,value)
        self.assertEqual(before,snapshot(self.mission))

    def test_expected_build_and_old_package_mismatch_reject_before_writes(self):
        before=snapshot(self.mission)
        value,code=self.run_command({**self.request,'expected_build_hash':'sha256:'+'0'*64})
        self.assertEqual((code,value['code']),(5,'runtime_mismatch'));self.assertEqual(before,snapshot(self.mission))
        old_root=os.environ.get('TPLAN_Q1_ROOT')
        if old_root:
            scripts=Path(old_root)/'skills/tplan/scripts'
            old=self.create('old-mission',scripts=scripts)
            before_old=snapshot(old)
            value,code=commands.execute(old,{**self.request,'mission_id':'old-mission'},principal=self.principal)
            self.assertEqual(code,5,value);self.assertEqual(before_old,snapshot(old))
            r=self.script('record_evidence.py',str(old),'--event-type','observation','--summary','Old writer',scripts=scripts)
            self.assertEqual(r.returncode,0,r.stderr)
            r=self.script('record_evidence.py',str(self.mission),'--event-type','observation','--summary','Wrong writer',scripts=scripts)
            self.assertNotEqual(r.returncode,0);self.assertEqual(before,snapshot(self.mission))

    def test_guard_blocks_new_write_but_not_historical_replay(self):
        self.run_command();runtime.begin_interaction_guard(self.mission,platform='codex',message_ref='synthetic')
        before=snapshot(self.mission)
        self.assertEqual(self.run_command()[0]['status'],'replayed')
        value,code=self.run_command({**self.request,'command_id':'another'})
        self.assertEqual((code,value['code']),(12,'guard_open'));self.assertEqual(before,snapshot(self.mission))

    def test_ordinary_commit_cannot_alter_or_remove_command_results(self):
        self.run_command();state=runtime.read_mission(self.mission)
        for operation in ['clear','remove']:
            after=copy.deepcopy(state)
            if operation=='clear':after['command_results']['records'].clear()
            else:after.pop('command_results')
            with self.assertRaisesRegex(runtime.TplanError,'command_results'):
                runtime.commit_mission_state(self.mission,state,after,source={'kind':'runtime_script','name':'fixture'})
        r=self.script('record_evidence.py',str(self.mission),'--event-type','observation','--summary','Legacy text')
        self.assertEqual(r.returncode,0,r.stderr);self.assertIn('recorded_evidence:',r.stdout)
        self.assertEqual(runtime.read_mission(self.mission)['command_results'],state['command_results'])

    def crash_worker(self, mode):
        script = '''import sys,json,os
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import tplan_runtime as r
from tplan_commands import execute
mission=Path(sys.argv[2]);request=json.loads(sys.argv[3]);mode=sys.argv[4]
if mode=='prepared':
    r._recover_pending_mission_transaction_unlocked=lambda *a,**k:os._exit(91)
elif mode=='middle':
    original=r.write_json
    def interrupted(path,*a,**k):
        if Path(path).name=='mission.json':os._exit(92)
        return original(path,*a,**k)
    r.write_json=interrupted
result,code=execute(mission,request,principal='test-host')
if mode=='response':os._exit(93)
raise SystemExit(code)
'''
        return subprocess.run([sys.executable,'-B','-c',script,str(SCRIPTS),str(self.mission),
                               json.dumps(self.request),mode],capture_output=True,text=True,timeout=20)

    def test_process_exit_after_prepare_requires_explicit_recovery(self):
        self.assertEqual(self.crash_worker('prepared').returncode,91)
        before=snapshot(self.mission)
        result,code=self.read_query();self.assertEqual(code,4,result);self.assertEqual(before,snapshot(self.mission))
        self.assertEqual(self.run_command()[1],4)
        recovered,code=self.run_command(self.result_query('runtime.recover'))
        self.assertEqual(code,0,recovered);self.assertTrue(recovered['data']['recovered'])
        self.assertEqual(self.run_command()[0]['status'],'replayed')
        self.assertEqual(len(runtime.read_events(self.mission)),1)

    def test_exit_in_replay_recovers_without_duplicate_evidence(self):
        self.assertEqual(self.crash_worker('middle').returncode,92)
        self.assertEqual(len((self.mission/'evidence.jsonl').read_text().splitlines()),1)
        result,code=self.run_command(self.result_query('runtime.recover'))
        self.assertEqual(code,0,result);self.assertTrue(result['data']['recovered'])
        self.assertEqual(len(runtime.read_events(self.mission)),1)
        self.assertEqual(self.run_command()[0]['status'],'replayed')

    def test_lost_response_queries_original_commit_without_repeating(self):
        self.assertEqual(self.crash_worker('response').returncode,93)
        before=snapshot(self.mission);observed,code=self.read_query()
        self.assertEqual(code,0,observed);self.assertEqual(self.run_command()[0]['status'],'replayed')
        self.assertEqual(before,snapshot(self.mission))

    def test_write_failure_before_durable_prepare_preserves_business_bytes(self):
        before=snapshot(self.mission)
        with patch.object(runtime,'write_json',side_effect=OSError('synthetic disk failure')):
            result,code=self.run_command()
        self.assertEqual((code,result['code']),(14,'outcome_unknown'))
        self.assertEqual(before,snapshot(self.mission))
        self.assertEqual(self.run_command()[0]['status'],'committed')

    def test_result_query_missing_and_pending_do_not_infer_non_execution(self):
        value,code=self.run_command(self.result_query());self.assertEqual(code,11,value)
        self.assertIn('does not prove',value['message'])
        (self.mission/'.mission-transaction.json').write_text('{"unfinished":true}')
        before=snapshot(self.mission);self.assertEqual(self.read_query()[1],4)
        self.assertEqual(before,snapshot(self.mission))

    def test_capacity_and_low_space_refuse_new_writes_not_replays(self):
        self.run_command();before=snapshot(self.mission)
        with patch.object(commands,'MAX_RECORDS',1):
            self.assertEqual(self.run_command()[0]['status'],'replayed')
            value,code=self.run_command({**self.request,'command_id':'next'})
            self.assertEqual(code,10,value)
        with patch.object(commands.shutil,'disk_usage',return_value=SimpleNamespace(free=1)):
            self.assertEqual(self.run_command()[0]['status'],'replayed')
            value,code=self.run_command({**self.request,'command_id':'next'})
            self.assertEqual(code,10,value)
        self.assertEqual(before,snapshot(self.mission))

    def test_no_acceptance_authority_or_arbitrary_actions(self):
        before=snapshot(self.mission)
        for req in [{**self.request,'action':'decision.apply'},
                    {**self.request,'payload':{**self.request['payload'],'event_type':'acceptance_passed'}},
                    {**self.request,'payload':{**self.request['payload'],'task_id':'missing'}}]:
            value,code=self.run_command(req);self.assertEqual(code,2,value)
        self.assertEqual(before,snapshot(self.mission))

    def test_invalid_json_and_unavailable_path_are_bounded(self):
        for raw in ['NaN','{"a":1,"a":2}','{broken']:
            with self.assertRaises(commands.CommandError):commands.parse_request(raw)
        missing=self.root/'missing';value,code=commands.execute(missing,self.request,principal=self.principal)
        self.assertEqual(code,6,value);self.assertFalse(missing.exists())
        alias=self.root/'alias';alias.symlink_to(self.mission,target_is_directory=True)
        self.assertEqual(commands.execute(alias,self.request,principal=self.principal)[1],6)

    def test_interrupted_explicit_recovery_can_be_retried(self):
        self.assertEqual(self.crash_worker('prepared').returncode,91)
        original = runtime.write_json
        def fail_mission(path,*args,**kwargs):
            if Path(path).name == 'mission.json':
                raise OSError('synthetic recovery interruption')
            return original(path,*args,**kwargs)
        with patch.object(runtime,'write_json',side_effect=fail_mission):
            result,code=self.run_command(self.result_query('runtime.recover'))
        self.assertEqual(code,14,result)
        self.assertTrue((self.mission/'.mission-transaction.json').exists())
        result,code=self.run_command(self.result_query('runtime.recover'))
        self.assertEqual(code,0,result)
        self.assertEqual(len(runtime.read_events(self.mission)),1)
        self.assertEqual(self.run_command()[0]['status'],'replayed')

    def test_same_evidence_id_with_changed_content_is_not_original_result(self):
        self.run_command();path=self.mission/'evidence.jsonl'
        event=json.loads(path.read_text());event['summary']='Changed after commit'
        path.write_text(json.dumps(event)+'\n');before=snapshot(self.mission)
        self.assertEqual(self.run_command()[1],7)
        self.assertEqual(self.read_query()[1],7)
        self.assertEqual(before,snapshot(self.mission))

    def test_bad_trace_or_guard_is_invalid_state_not_runtime_missing(self):
        for name in ('execution_trace.jsonl','.interaction-guard.json'):
            path=self.mission/name;original=path.read_bytes() if path.exists() else None
            path.write_text('{}\n');before=snapshot(self.mission)
            value,code=self.run_command()
            self.assertEqual((code,value['code']),(7,'invalid_state'))
            self.assertEqual(before,snapshot(self.mission))
            if original is None:path.unlink()
            else:path.write_bytes(original)

    def test_result_without_matching_evidence_is_not_reported_success(self):
        self.run_command();(self.mission/'evidence.jsonl').write_text('')
        before=snapshot(self.mission)
        self.assertEqual(self.run_command(self.result_query())[1],7)
        self.assertEqual(self.read_query()[1],7)
        self.assertEqual(before,snapshot(self.mission))


if __name__=='__main__':
    unittest.main()
