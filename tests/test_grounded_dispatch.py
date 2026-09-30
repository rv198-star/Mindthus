import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from experiments.grounded_judgment import runtime as rt
from experiments.grounded_judgment.dispatch import Dispatcher, prepare, wire, classify, OfficialAdapters
from experiments.grounded_judgment.dispatch_demo import Clock, SimulatedAdapters, export
from experiments.grounded_judgment.development import cases
from experiments.typed_decision.providers import ProviderError
from experiments.typed_decision.contracts import digest
from experiments.typed_decision.relationship_runtime import _locked


class Wiring(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'batch';self.case=cases()[1];self.clock=Clock()
        prepare(self.root,{self.case['id']:{'documents':self.case['documents'],'materials':{'fixture-method':'mock'}}})
        self.adapter=SimulatedAdapters(self.clock,self.case)
        self.driver=Dispatcher(self.root,self.adapter,clock=self.clock.now,monotonic=self.clock.now,sleep=self.clock.sleep)
    def run_name(self,arm='C'):return self.case['id']+'-'+arm
    def test_complete_three_arms_wire_to_import(self):
        result=export(Path(self.tmp.name)/'full')
        self.assertEqual(result['real_model_calls'],0)
        for arm in 'ABC':
            self.assertEqual(result['arms'][arm]['phase'],'done')
            self.assertIsNone(result['arms'][arm]['stopped'])
            self.assertEqual(result['arms'][arm]['read_count'],1)
        c=result['arms']['C'];self.assertEqual((c['call_count'],c['check_count'],c['revision_count']),(7,1,1))
        self.assertEqual([x['phase'] for x in result['calls'][:7]],['round1','round2','round3','draft','draft','check','revision'])
        self.assertTrue(all(b['at']-a['at']>=62 for a,b in zip(result['calls'],result['calls'][1:])))
    def test_wire_contract_compatible_without_mutation(self):
        req=rt.request(self.root/'runs'/self.run_name('B'));before=copy.deepcopy(req)
        w=wire(req,self.driver.config)
        self.assertNotIn('uniqueItems',json.dumps(w['api_schema']))
        self.assertIn('uniqueItems',json.dumps(w['local_schema']))
        self.assertEqual(before,req)
        self.assertEqual(set(w['local_schema']['required']),{q['id'] for q in req['payload']['questions']})
    def test_new_batch_all_host_phases_use_sol61_and_jev_is_unchanged(self):
        result=export(Path(self.tmp.name)/'models')
        config=rt.read(Path(self.tmp.name)/'models/batch.json')
        self.assertEqual(config['host_configuration']['model'],'gpt-6.1-sol')
        roles=set();arms=set();phases=set()
        for directory in sorted((Path(self.tmp.name)/'models/calls').iterdir()):
            req=rt.read(directory/'request.json');out=rt.read(directory/'wire.json');roles.add(req['role'])
            if req['role']=='host':
                arms.add(req['arm']);phases.add(req['phase'])
                self.assertEqual(req['requested_configuration'],config['host_configuration'])
                self.assertEqual((out['model'],out['effort']),('gpt-6.1-sol','xhigh'))
            else:self.assertEqual(out['body']['model'],'jev-1.13.0')
        self.assertEqual(roles,{'host','jev'});self.assertEqual(arms,set('ABC'))
        self.assertTrue({'atoms','draft','check','revision'}<=phases)
        self.assertEqual(result['real_model_calls'],0)
    def test_legacy_run_and_pending_request_keep_old_model(self):
        legacy={'model':'gpt-6-sol','reasoning_effort':'xhigh','transport_profile':'mindthus_official_http'}
        root=Path(self.tmp.name)/'legacy';rt.init(root,self.case['documents'],'A')
        s=rt.state(root);s.pop('host_configuration');rt.append(root,'state',s)
        req=rt.request(root);before=copy.deepcopy(req)
        self.assertEqual(req['requested_configuration'],legacy)
        self.assertEqual(wire(req,{'overrides':[]})['model'],'gpt-6-sol')
        self.assertEqual(rt.request(root),before)
        self.assertEqual(digest({k:v for k,v in req.items() if k!='request_sha256'}),req['request_sha256'])
    def test_model_mismatch_rejected_before_transport(self):
        req=rt.request(self.root/'runs'/self.run_name('A'))
        config=copy.deepcopy(self.driver.config);config['host_configuration']['model']='gpt-6-sol'
        with self.assertRaisesRegex(ValueError,'host_configuration_mismatch'):wire(req,config)
        self.assertEqual(self.adapter.invocations,[])
    def test_binding_and_serial_evidence(self):
        self.driver.step(self.run_name())
        d=self.root/'calls/000000';b=rt.read(d/'binding.json');t=rt.read(d/'terminal.json')
        self.assertEqual(b,t['binding']);self.assertEqual(b,rt.read(d/'raw.json')['binding'])
        self.assertEqual(digest(rt.read(d/'raw.json')['transport']),t['raw_sha256'])
        self.assertEqual(digest(rt.read(d/'envelope.json')),rt.read(d/'import.json')['envelope_sha256'])
        self.assertTrue((self.root/'serial/000000/completion.json').exists())
    def test_cross_arm_and_restart_cooldown(self):
        self.driver.step(self.run_name());self.driver.step(self.run_name('A'))
        self.assertEqual(self.adapter.invocations[1]['at'],62)
        resumed=Dispatcher(self.root,self.adapter,clock=self.clock.now,monotonic=self.clock.now,sleep=self.clock.sleep)
        resumed.step(self.run_name('B'));self.assertEqual(self.adapter.invocations[2]['at'],124)
    def test_single_sender(self):
        with _locked(self.root/'.dispatch.lock'):
            with self.assertRaises((BlockingIOError,RuntimeError,ValueError)):self.driver.step(self.run_name())
        self.assertEqual(self.adapter.invocations,[])
    def test_unknown_stops_without_completion_or_retry(self):
        with patch.object(self.adapter,'invoke',side_effect=TimeoutError):
            s=self.driver.step(self.run_name());self.assertEqual(s['stopped'],'unknown')
        self.assertFalse((self.root/'serial/000000/completion.json').exists())
        with self.assertRaises(ValueError):self.driver.step(self.run_name('A'))
    def test_presend_failure_terminal_can_continue_other_arm(self):
        req=rt.request(self.root/'runs'/self.run_name())
        error=ProviderError('transport_failure',diagnostic={'request_sha256':digest(wire(req,self.driver.config)['body']),'generation_send_status':'pre_send','observed_stage':'connection_establishment_failed'})
        with patch.object(self.adapter,'invoke',side_effect=error):
            self.assertEqual(self.driver.step(self.run_name())['stopped'],'failed')
        self.assertTrue((self.root/'serial/000000/completion.json').exists())
        self.driver.step(self.run_name('A'));self.assertEqual(self.adapter.invocations[0]['at'],60)
    def test_permission_stops_batch(self):
        req=rt.request(self.root/'runs'/self.run_name())
        error=ProviderError('http_403',diagnostic={'request_sha256':digest(wire(req,self.driver.config)['body']),'http_response_received':True,'http_status':403})
        with patch.object(self.adapter,'invoke',side_effect=error):
            self.assertEqual(self.driver.step(self.run_name())['stopped'],'safety_refusal')
        with self.assertRaises(ValueError):self.driver.step(self.run_name('A'))
    def test_nonzero_timeout_and_wrong_thread_not_terminal(self):
        req=rt.request(self.root/'runs'/self.run_name('A'))
        for raw in [dict(kind='cli',returncode=1,events=[],reply=None),
          dict(kind='transport_error',code='TimeoutError',diagnostic=None),
          dict(kind='cli',events=[{'type':'thread.started','thread_id':'a'},{'type':'turn.completed','thread_id':'b'}])]:
            self.assertEqual(classify(req,raw)[0],'unknown')
    def test_wrong_turn_and_plain_error_remain_unknown(self):
        req=rt.request(self.root/'runs'/self.run_name('A'))
        prefix=[{'type':'thread.started','thread_id':'a'},{'type':'turn.started','turn_id':'1'}]
        for tail in [{'type':'turn.completed','turn_id':'2'}, {'type':'turn.failed','error':{'message':'invalid schema'}}]:
            self.assertEqual(classify(req,{'kind':'cli','events':prefix+[tail]})[0],'unknown')
    def test_explicit_failure_separate_from_success(self):
        req=rt.request(self.root/'runs'/self.run_name('A'))
        raw={'kind':'cli','events':[{'type':'thread.started','thread_id':'a'},
             {'type':'turn.failed','error':{'code':'invalid_json_schema'}}]}
        self.assertEqual(classify(req,raw)[0],'failed')
    def test_simulation_cannot_import_real(self):
        with self.assertRaises(ValueError):Dispatcher(self.root,OfficialAdapters())
        run=self.root/'runs'/self.run_name();req=rt.request(run)
        with self.assertRaises(ValueError):rt.accept(run,{'simulation':False,'request_sha256':req['request_sha256'],'status':'returned'})
    def test_real_admission_missing_no_transport(self):
        with self.assertRaises(ValueError):prepare(Path(self.tmp.name)/'real',{'x':{}},simulation=False)
        self.assertFalse((Path(self.tmp.name)/'real').exists())
    def test_budget_and_completed_no_extra_call(self):
        name=self.run_name('A')
        while self.driver.step(name)['phase']!='done':pass
        count=len(self.adapter.invocations);self.driver.step(name);self.assertEqual(len(self.adapter.invocations),count)
        at_limit=rt.state(self.root/'runs'/self.run_name());at_limit['call_count']=9
        with patch.object(rt,'state',return_value=at_limit):
            with self.assertRaisesRegex(ValueError,'call_budget_exhausted'):self.driver.step(self.run_name())
    def test_unclassified_recovery_preserves_result_stops_next(self):
        invoke=self.adapter.invoke
        def noisy(*args):
            raw=invoke(*args);raw['stderr']='retrying sampling request';return raw
        with patch.object(self.adapter,'invoke',side_effect=noisy):s=self.driver.step(self.run_name('A'))
        self.assertIsNone(s['stopped'])
        with self.assertRaises(ValueError):self.driver.step(self.run_name())
    def test_unimported_call_never_resent(self):
        d=self.root/'calls/000000';d.mkdir();rt.write(d/'request.json',{})
        with self.assertRaises(ValueError):self.driver.step(self.run_name())
        self.assertEqual(self.adapter.invocations,[])


class BoundaryTests(unittest.TestCase):
    setUp=Wiring.setUp
    run_name=Wiring.run_name
    def test_official_jev_adapter_with_mock_transport_only(self):
        req=rt.request(self.root/'runs'/self.run_name());out=wire(req,self.driver.config)
        d=Path(self.tmp.name)/'adapter';d.mkdir()
        with patch('os.environ',{'TYPESAFE_API_KEY':'synthetic-test-only'}), patch(
          'experiments.typed_decision.relationship_live.deadline_post_json',return_value={'model':'jev-1.13.0','answers':{}}) as send:
            result=OfficialAdapters().invoke(req,out,d,self.driver.config)
        self.assertEqual(result['kind'],'http_json')
        self.assertEqual(send.call_args.args[0],'https://api.typesafe.ai/v1/systemone')
        self.assertEqual(send.call_args.args[2],out['body'])
        self.assertNotIn('synthetic-test-only',json.dumps(result))
    def test_official_host_adapter_with_mock_cli_only(self):
        import subprocess
        from experiments.jev_direct.pilot import wire as existing
        req=rt.request(self.root/'runs'/self.run_name('A'));out=wire(req,self.driver.config)
        d=Path(self.tmp.name)/'adapter';d.mkdir();config=copy.deepcopy(self.driver.config)
        config['admission']={'binary':'mock-never-executed'}
        response={'kind':'answer','text':'mock','read_paths':[],'objection':''}
        def run(cmd,prompt,env,timeout):
            self.assertEqual(prompt,out['prompt']);self.assertEqual(env,{})
            for override in config['overrides']:self.assertIn(override,cmd)
            self.assertEqual(cmd[cmd.index('-m')+1],'gpt-6.1-sol');self.assertIn('model_reasoning_effort="xhigh"',cmd)
            rt.write(d/'reply.json',response)
            return subprocess.CompletedProcess(cmd,0,'\n'.join(json.dumps(e) for e in [
              {'type':'thread.started','thread_id':'t'},{'type':'turn.completed'}]),'')
        with patch('os.environ',{}),patch.object(existing,'_run_cli',side_effect=run) as execute:
            result=OfficialAdapters().invoke(req,out,d,config)
        self.assertEqual(execute.call_count,1);self.assertEqual(classify(req,result)[:2],('returned',response))
    def test_diagnostic_from_other_request_cannot_clear_unknown(self):
        req=rt.request(self.root/'runs'/self.run_name())
        raw={'kind':'transport_error','code':'transport_failure','diagnostic':{
          'request_sha256':'other','generation_send_status':'pre_send','observed_stage':'connection_establishment_failed'}}
        self.assertEqual(classify(req,raw)[0],'unknown')
    def test_local_write_is_not_pre_send(self):
        req=rt.request(self.root/'runs'/self.run_name())
        raw={'kind':'transport_error','code':'transport_failure','diagnostic':{
          'request_sha256':digest(wire(req,self.driver.config)['body']),
          'generation_send_status':'unknown','observed_stage':'response_headers_wait'}}
        self.assertEqual(classify(req,raw)[0],'unknown')
    def test_import_cannot_bypass_dispatch_receipt(self):
        run=self.root/'runs'/self.run_name();req=rt.request(run)
        with self.assertRaises(ValueError):rt.accept(run,{'request_sha256':req['request_sha256'],'simulation':True,'status':'returned','response':{}})
    def test_wire_digest_tamper_stops_import(self):
        invoke=self.adapter.invoke
        def tamper(req,w,d,c):
            result=invoke(req,w,d,c);(d/'wire.json').write_text('{}');return result
        with patch.object(self.adapter,'invoke',side_effect=tamper):
            with self.assertRaises(ValueError):self.driver.step(self.run_name())
        self.assertEqual(rt.state(self.root/'runs'/self.run_name())['call_count'],0)
        with self.assertRaises(ValueError):self.driver.step(self.run_name('A'))
    def test_duplicate_host_paths_are_failure_after_terminal(self):
        req=rt.request(self.root/'runs'/self.run_name('A'))
        raw={'kind':'cli','events':[{'type':'thread.started','thread_id':'t'},{'type':'turn.completed'}],
             'reply':{'kind':'read','text':'','read_paths':['fixture-method','fixture-method'],'objection':''}}
        self.assertEqual(classify(req,raw)[0],'failed')
    def test_materials_are_separate_and_dev_is_not_sealed(self):
        from experiments.grounded_judgment.materials import import_materials,verify_materials
        bundle={'inputs':{'dev':{'documents':self.case['documents']}},'norms':{'dev':{'private':'EVALUATION_ONLY'}},
                'provenance':'public_development','owner_seal_ref':None}
        root=Path(self.tmp.name)/'materials';m=import_materials(root,bundle)
        self.assertFalse(m['sealed_for_acceptance'])
        self.assertNotIn('EVALUATION_ONLY',(root/'inputs.json').read_text())
        with self.assertRaises(ValueError):verify_materials(root)
    def test_receipt_for_identical_input_other_case_rejected(self):
        from experiments.grounded_judgment.dispatch import validate_import
        root=Path(self.tmp.name)/'paired';packet={'documents':self.case['documents'],'materials':{'fixture-method':'mock'}}
        prepare(root,{self.case['id']:packet,'mirror':packet})
        d=Dispatcher(root,self.adapter,clock=self.clock.now,monotonic=self.clock.now,sleep=self.clock.sleep)
        d.step(self.run_name())
        other=root/'runs/mirror-C';req=rt.request(other)
        with self.assertRaises(ValueError):rt.accept(other,rt.read(root/'calls/000000/envelope.json'))
    def test_terminal_before_start_is_unknown(self):
        req=rt.request(self.root/'runs'/self.run_name('A'))
        self.assertEqual(classify(req,{'kind':'cli','events':[{'type':'turn.completed'},{'type':'thread.started','thread_id':'x'}]})[0],'unknown')
    def test_no_auth_or_transport_during_demo(self):
        with (patch('os.environ',{}),patch('experiments.typed_decision.relationship_live.deadline_post_json',side_effect=AssertionError('no network')),
             patch('experiments.jev_direct.pilot.wire._run_cli',side_effect=AssertionError('no CLI'))):
            result=export(Path(self.tmp.name)/'no-io')
        self.assertEqual(result['real_model_calls'],0)

if __name__=='__main__':unittest.main()
