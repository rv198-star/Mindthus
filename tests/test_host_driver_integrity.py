"""Offline regressions: schema aliasing, bad replies and exact interruption boundaries.

All new host replies are synthetic. Archived bad replies are inspected unchanged;
no fixture is claimed to demonstrate model quality or a recovered historical trial.
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tarfile
import unittest
from unittest.mock import patch

from experiments.typed_decision.contracts import ContractError, digest
from experiments.typed_decision.session import read_record, write_once, RecoveryRequired
from experiments.typed_decision import route_control_v03 as runtime
from tests import test_entry_single_cycle as single_cycle
from tests import test_route_control_v03 as f

REPO=Path(__file__).resolve().parents[1]

class Interrupted(BaseException): pass

class HostDriverIntegrityTests(unittest.TestCase):
    setUp=single_cycle.PortableDriverTests.setUp

    def native(self):
        from experiments.typed_decision import comparison_v03 as cmp
        return {'schema':'mindthus.route-v03-native-request.v1','request_id':'native',
                'condition_packet':cmp.prepare_condition(f.packet(),'pure_codex',REPO),
                'artifact_actions':['replace','retain','read_methods'],'candidate':'原始回答。'}

    def execute(self):
        return {'schema':'mindthus.route-v03-execution-request.v1','request_id':'execute',
                'route_id':'r','revision':1,'issue':{'issue_id':'I1'},'original_input':f.packet(),
                'loaded_methods':{},'limited_response':{'kind':'test'}}

    def organize(self):
        _,_,bindings,_=runtime._bundle(REPO)
        return runtime._organize_request(f.packet(),bindings)

    def response(self,q):
        return {'text':'根据原文作出有限判断，未认领尚未确定的方法。','performed_methods':[],
                'objection_reason':'方法尚未确定，答复只覆盖原文足以支持的部分。',
                'objection_kind':'method_boundary','requested_change':'保留未决的方法范围。',
                'source_ids':['U'],'scope_status':'bounded_answer'}

    def test_organization_fields_do_not_alias_id_or_global_string(self):
        before=deepcopy(self.driver.wire.STR)
        schema=self.driver.schema_for(self.organize())
        p=schema['properties']['issues']['items']['properties']
        self.assertIn('pattern',p['id'])
        for name in ('actor','goal','scope'):self.assertNotIn('pattern',p[name])
        self.assertEqual(self.driver.wire.STR,before)
        p['id']['enum']=['changed']
        self.assertNotIn('enum',p['goal'])
        self.assertNotIn('enum',self.driver.wire.STR)

    def test_all_mutable_nodes_are_independent(self):
        for q in (self.organize(),self.native(),self.execute()):
            ids=[]
            def visit(x):
                if isinstance(x,(dict,list)):
                    ids.append(id(x))
                    for v in (x.values() if isinstance(x,dict) else x):visit(v)
            visit(self.driver.schema_for(q))
            self.assertEqual(len(ids),len(set(ids)))

    def test_schema_is_order_independent_across_repeated_stages(self):
        expected=self.driver.schema_for(self.execute())
        for _ in range(3):
            self.driver.schema_for(self.organize())
            self.driver.schema_for(self.native())
        actual=self.driver.schema_for(self.execute())
        self.assertEqual(actual,expected)
        self.assertNotIn('pattern',actual['properties']['text'])
        self.driver._wire_check(self.response(self.execute()),actual)

    def test_chinese_prose_in_organization_is_legal(self):
        q=self.organize()
        raw={'issues':[{'id':'I1','candidates':['edsp'],'handling':'judge',
                       'actor':'当前用户','goal':'判断机制和整体职责的关系。','scope':'仅讨论技能。'}],
             'coverage_disposition':{'status':'complete','unassigned':[]}}
        self.driver._wire_check(raw,self.driver.schema_for(q))
        out=self.driver.normalize(raw,q,dict(f.rt.UNKNOWN_USAGE))
        self.assertEqual(out['host_inferences']['issue_views']['I1']['goal'],raw['issues'][0]['goal'])

    def test_organization_identifier_still_requires_identifier(self):
        q=self.organize()
        raw={'issues':[{'id':'不合法 空格','candidates':[],'handling':'direct_execute',
                       'actor':'用户','goal':'执行','scope':'当前'}],
             'coverage_disposition':{'status':'complete','unassigned':[]}}
        with self.assertRaisesRegex(ContractError,'pattern'):self.driver.normalize(raw,q,dict(f.rt.UNKNOWN_USAGE))

    def test_invalid_source_is_rejected_before_lookup(self):
        q=self.execute();raw=self.response(q);raw['source_ids']=['repo']
        before=deepcopy(raw)
        with self.assertRaisesRegex(ContractError,'source_ids.*enum'):self.driver.normalize(raw,q,dict(f.rt.UNKNOWN_USAGE))
        self.assertEqual(raw,before)

    def test_unused_invalid_source_is_also_rejected(self):
        q=self.execute();raw=self.response(q);raw['source_ids']=['repo'];raw['objection_reason']=''
        with self.assertRaises(ContractError):self.driver.normalize(raw,q,dict(f.rt.UNKNOWN_USAGE))

    def test_duplicate_source_rejected(self):
        q=self.execute();raw=self.response(q);raw['source_ids']=['U','U']
        with self.assertRaisesRegex(ContractError,'duplicate'):self.driver.normalize(raw,q,dict(f.rt.UNKNOWN_USAGE))

    def test_unread_method_claim_rejected(self):
        q=self.execute();raw=self.response(q);raw['performed_methods']=['edsp']
        with self.assertRaisesRegex(ContractError,'performed_methods'):self.driver.normalize(raw,q,dict(f.rt.UNKNOWN_USAGE))

    def test_duplicate_acceptance_cannot_collapse_to_one(self):
        q={'schema':'mindthus.route-v03-accept-request.v1','request_id':'accept','candidates':{'I1':'sha'}}
        raw={'accepted':[{'issue_id':'I1','accepted':False,'reason':'未完成'},
                         {'issue_id':'I1','accepted':True,'reason':'第二条'}]}
        with self.assertRaisesRegex(ContractError,'duplicate_identity'):self.driver.normalize(raw,q,dict(f.rt.UNKNOWN_USAGE))

    def test_duplicate_revision_cannot_overwrite(self):
        q={'schema':'mindthus.route-v03-advice-request.v1','request_id':'advice','candidates':{'I1':'sha'}}
        raw={'revisions':[{'issue_id':'I1','text':'A'},{'issue_id':'I1','text':'B'}]}
        with self.assertRaisesRegex(ContractError,'duplicate_identity'):self.driver.normalize(raw,q,dict(f.rt.UNKNOWN_USAGE))

    def test_unknown_wire_field_and_missing_field_rejected(self):
        q=self.execute();raw=self.response(q);raw['extra']='x'
        with self.assertRaisesRegex(ContractError,'extra_fields'):self.driver.normalize(raw,q,dict(f.rt.UNKNOWN_USAGE))
        raw=self.response(q);del raw['text']
        with self.assertRaisesRegex(ContractError,'required'):self.driver.normalize(raw,q,dict(f.rt.UNKNOWN_USAGE))

    def test_shape_checks_do_not_pretend_to_judge_answer_quality(self):
        q=self.execute();raw=self.response(q);raw['text']='v2'
        out=self.driver.normalize(raw,q,dict(f.rt.UNKNOWN_USAGE))
        self.assertEqual(out['text'],'v2')  # No keyword blacklist or invented semantic PASS.

    def test_actual_archived_bad_reply_remains_invalid_and_unchanged(self):
        p=REPO/'docs/internal/research/typed-decision/route-control-v0.2/single-cycle-repair-v1/official-return-v1/E-evidence.tar.gz'
        before=p.read_bytes()
        with tarfile.open(p) as t:
            replies=[n for n in t.getnames() if n.endswith('execution__i1__1/reply.json')]
            self.assertEqual(len(replies),1)
            raw=json.load(t.extractfile(replies[0]))
            # This is still the saved bad response, not a manufactured replacement.
            self.assertEqual(raw['text'],'v2');self.assertEqual(raw['source_ids'],['repo'])
            q=self.execute();q['original_input']['documents'][0]['id']='m0'
            with self.assertRaisesRegex(ContractError,'enum'):self.driver.normalize(raw,q,dict(f.rt.UNKNOWN_USAGE))
        self.assertEqual(p.read_bytes(),before)

    def prepare(self):
        self.source['documents'][-1]['id']='source-limit'
        p=self.root/'source.json';p.write_text(json.dumps(self.source))
        self.runroot=self.root/'run'
        self.driver.prepare(self.runroot,p,'E',0,'initial',[], 'fixture-host','high','/usr/bin/true','local://fixture')
        self.calls=[]

    def mock_cli(self,cmd,prompt,env,timeout):
        self.calls.append(cmd)
        q=json.loads(prompt.split('\n',1)[1])['request']
        if q['schema'].endswith('native-request.v1'):
            raw={'text':'' if q['candidate'] is not None else '原文足以支持这份有限回答。',
                 'artifact_action':'retain' if q['candidate'] is not None else 'replace',
                 'performed_methods':[],'decision_status':'decided','dispute_reason':'',
                 'source_ids':[],'requested_methods':[]}
        else:
            self.assertTrue(q['schema'].endswith('accept-request.v1'))
            raw={'accepted':[{'issue_id':i,'accepted':True,'reason':'确认当前原文对应答案。'} for i in q['candidates']]}
        if getattr(self,'mutate_raw',None):self.mutate_raw(raw,q)
        Path(cmd[cmd.index('-o')+1]).write_text(json.dumps(raw,ensure_ascii=False))
        context=getattr(self,'returned_context','fixture-independent-context')
        events=[{'type':'thread.started','thread_id':context},
                {'type':'turn.completed','usage':{'input_tokens':12,'output_tokens':8}}]
        events+=getattr(self,'extra_events',[])
        return subprocess.CompletedProcess(cmd,0,'\n'.join(json.dumps(x) for x in events),'')

    def run_driver(self):
        with patch.object(self.driver,'_run_cli',side_effect=self.mock_cli):
            return self.driver.drive(self.runroot,'pure_codex')

    def test_happy_path_and_completed_reentry_make_no_new_calls(self):
        self.prepare();result=self.run_driver()
        self.assertTrue(result['consumption_complete']);self.assertEqual(len(self.calls),3)
        self.assertEqual(self.run_driver(),result);self.assertEqual(len(self.calls),3)
        self.assertEqual(len(list(self.runroot.glob('host-calls/*/*/consumption.json'))),3)

    def test_known_bad_reply_is_terminal_and_preserves_usage(self):
        self.prepare()
        self.mutate_raw=lambda r,q:r.update(source_ids=['repo'])
        result=self.run_driver()
        self.assertEqual(result['status'],'host_reply_rejected')
        self.assertEqual(result['usage']['input_tokens'],12)
        self.assertFalse(result['consumption_complete']);self.assertEqual(len(self.calls),1)
        self.assertEqual(self.run_driver(),result);self.assertEqual(len(self.calls),1)
        self.assertEqual(len(list(self.runroot.glob('host-calls/*/*/outcome.json'))),1)
        self.assertFalse(list((self.runroot/'episodes').glob('*/turns/*/inputs/*/steps/*/host-response.json')))

    def crash_save(self,match):
        original=self.driver.save;triggered=[]
        def save(p,value):
            if match(p) and not triggered:
                triggered.append(True);raise Interrupted()
            return original(p,value)
        with patch.object(self.driver,'save',side_effect=save):
            with self.assertRaises(Interrupted):self.run_driver()
        self.assertTrue(triggered)

    def test_crash_after_outcome_before_session_recovers_without_new_first_call(self):
        self.prepare();self.crash_save(lambda p:p.parent.name=='sessions')
        self.assertEqual(len(self.calls),1)
        self.assertTrue(self.run_driver()['consumption_complete']);self.assertEqual(len(self.calls),3)
        self.assertIn('resume',self.calls[1])

    def test_crash_before_staging_reuses_recorded_physical_call(self):
        self.prepare()
        with patch.object(self.driver,'submit_response',side_effect=Interrupted()):
            with self.assertRaises(Interrupted):self.run_driver()
        self.assertTrue(self.run_driver()['consumption_complete']);self.assertEqual(len(self.calls),3)

    def test_crash_after_staging_before_consumption_does_not_regenerate(self):
        self.prepare();self.crash_save(lambda p:p.name=='consumption.json')
        self.assertTrue(self.run_driver()['consumption_complete']);self.assertEqual(len(self.calls),3)

    def test_crash_between_failure_record_and_terminal_result(self):
        self.prepare();self.mutate_raw=lambda r,q:r.update(source_ids=['repo'])
        self.crash_save(lambda p:p.parent.name=='results')
        result=self.run_driver();self.assertEqual(result['status'],'host_reply_rejected')
        self.assertEqual(len(self.calls),1)

    def test_unknown_inflight_is_not_reissued(self):
        self.prepare()
        with patch.object(self.driver,'_run_cli',side_effect=Interrupted()):
            with self.assertRaises(Interrupted):self.driver.drive(self.runroot,'pure_codex')
        with patch.object(self.driver,'_run_cli') as call:
            with self.assertRaisesRegex(RecoveryRequired,'unknown_do_not_repeat'):self.driver.drive(self.runroot,'pure_codex')
        call.assert_not_called()

    def test_changed_cached_reply_rejected_without_request(self):
        self.prepare();self.crash_save(lambda p:p.parent.name=='sessions')
        path=next(self.runroot.glob('host-calls/*/*/reply.json'));x=json.loads(path.read_text());x['text']='已篡改';path.write_text(json.dumps(x))
        with self.assertRaisesRegex(ContractError,'host_cache_reply_changed'):self.run_driver()
        self.assertEqual(len(self.calls),1)

    def test_changed_cached_schema_rejected_without_request(self):
        self.prepare();self.crash_save(lambda p:p.parent.name=='sessions')
        path=next(self.runroot.glob('host-calls/*/*/schema.json'));x=json.loads(path.read_text());x['properties']['text']['pattern']='x';path.write_text(json.dumps(x))
        with self.assertRaisesRegex(ContractError,'binding_changed'):self.run_driver()
        self.assertEqual(len(self.calls),1)

    def test_changed_cached_prompt_rejected_without_request(self):
        self.prepare();self.crash_save(lambda p:p.parent.name=='sessions')
        path=next(self.runroot.glob('host-calls/*/*/prompt.txt'));path.write_text('changed')
        with self.assertRaisesRegex(ContractError,'binding_changed'):self.run_driver()
        self.assertEqual(len(self.calls),1)

    def test_outcome_without_intent_cannot_be_replayed(self):
        self.prepare();self.crash_save(lambda p:p.parent.name=='sessions')
        next(self.runroot.glob('host-calls/*/*/intent.json')).unlink()
        with self.assertRaises(ContractError):self.run_driver()
        self.assertEqual(len(self.calls),1)

    def test_changed_context_in_same_branch_is_terminal(self):
        self.prepare();original=self.mock_cli
        def run(*args):
            self.returned_context='context-a' if not self.calls else 'context-b'
            return original(*args)
        with patch.object(self.driver,'_run_cli',side_effect=run):result=self.driver.drive(self.runroot,'pure_codex')
        self.assertEqual(result['reason'],'host_resume_context_changed');self.assertEqual(len(self.calls),2)
        self.assertEqual(self.run_driver(),result);self.assertEqual(len(self.calls),2)

    def test_timeout_is_recorded_and_not_retried(self):
        self.prepare()
        with patch.object(self.driver,'_run_cli',side_effect=subprocess.TimeoutExpired('fixture',1)) as call:
            result=self.driver.drive(self.runroot,'pure_codex');again=self.driver.drive(self.runroot,'pure_codex')
        self.assertEqual(result,again);self.assertEqual(call.call_count,1)
        self.assertEqual(result['failure_stage'],'transport');self.assertIsNone(result['usage']['cost_usd'])

    def test_tool_use_invalidates_transport_without_claiming_answer(self):
        self.prepare();self.extra_events=[{'type':'item.completed','item':{'type':'command_execution'}}]
        result=self.run_driver();self.assertEqual(result['reason'],'host_cli_failed_or_used_tools')
        self.assertFalse(result['consumption_complete']);self.assertEqual(len(self.calls),1)

    def test_missing_context_is_rejected(self):
        self.prepare();original=self.mock_cli
        def run(*args):
            p=original(*args);p.stdout=json.dumps({'type':'turn.completed','usage':{}});return p
        with patch.object(self.driver,'_run_cli',side_effect=run):result=self.driver.drive(self.runroot,'pure_codex')
        self.assertEqual(result['reason'],'host_context_missing_or_ambiguous')

    def test_malformed_reply_json_is_recorded_without_implicit_retry(self):
        self.prepare();original=self.mock_cli
        def run(cmd,*args):
            p=original(cmd,*args);Path(cmd[cmd.index('-o')+1]).write_text('{broken');return p
        with patch.object(self.driver,'_run_cli',side_effect=run):result=self.driver.drive(self.runroot,'pure_codex')
        self.assertEqual(result['reason'],'host_reply_invalid_json');self.assertEqual(result['usage']['input_tokens'],12)
        self.assertEqual(self.run_driver(),result);self.assertEqual(len(self.calls),1)

    def test_duplicate_json_keys_and_nonfinite_rejected(self):
        p=self.root/'reply.json'
        for text in ('{"text":"one","text":"two"}','{"text":NaN}'):
            p.write_text(text)
            with self.assertRaises(ContractError):self.driver._decode_reply(p,32768)

    def test_nonobject_and_oversized_replies_rejected(self):
        p=self.root/'reply.json';p.write_text('[]')
        with self.assertRaisesRegex(ContractError,'not_object'):self.driver._decode_reply(p,32768)
        p.write_text('{"text":"long"}')
        with self.assertRaisesRegex(ContractError,'size'):self.driver._decode_reply(p,2)

    def test_branch_concurrency_lock_prevents_second_driver(self):
        self.prepare()
        with self.driver.wire.rt._locked(self.runroot/'.host-driver.lock'):
            with patch.object(self.driver,'_run_cli') as call:
                with self.assertRaises(RecoveryRequired):self.driver.drive(self.runroot,'pure_codex')
            call.assert_not_called()

    def test_existing_staged_response_remains_byte_identical(self):
        self.prepare();self.crash_save(lambda p:p.name=='consumption.json')
        p=next((self.runroot/'episodes').glob('*/turns/*/inputs/*/steps/*/host-response.json'));before=p.read_bytes()
        self.run_driver();self.assertEqual(p.read_bytes(),before)

    def test_cached_submission_tampering_is_rejected(self):
        self.prepare()
        with patch.object(self.driver,'submit_response',side_effect=Interrupted()):
            with self.assertRaises(Interrupted):self.run_driver()
        p=next(self.runroot.glob('host-calls/*/*/submission.json'))
        x=json.loads(p.read_text());x['payload']['reply']['text']='修改';x['sha256']=digest(x['payload']);p.write_text(json.dumps(x))
        result=self.run_driver();self.assertEqual(result['status'],'host_reply_rejected');self.assertEqual(len(self.calls),1)


    def test_manual_step_uses_same_lock_as_driver(self):
        self.prepare()
        with self.driver.wire.rt._locked(self.runroot/'.host-driver.lock'):
            with patch.object(self.driver,'submit_response') as submit:
                with self.assertRaises(RecoveryRequired):self.driver.step(self.runroot,'pure_codex')
            submit.assert_not_called()

    def test_manual_reply_cannot_race_active_cli(self):
        self.prepare();seen=[];original=self.mock_cli
        def run(*args):
            with self.assertRaises(RecoveryRequired):self.driver.step(self.runroot,'pure_codex')
            seen.append(True);return original(*args)
        with patch.object(self.driver,'_run_cli',side_effect=run):
            result=self.driver.drive(self.runroot,'pure_codex')
        self.assertTrue(result['consumption_complete']);self.assertEqual(len(seen),3)

    def test_completed_terminal_checks_mutated_reply(self):
        self.prepare();self.assertTrue(self.run_driver()['consumption_complete'])
        p=next(self.runroot.glob('host-calls/*/*/reply.json'))
        x=json.loads(p.read_text());x['tampered']=True;p.write_text(json.dumps(x))
        for call in (lambda:self.run_driver(),lambda:self.driver.step(self.runroot,'pure_codex')):
            with self.assertRaisesRegex(ContractError,'reply_changed'):call()
        self.assertEqual(len(self.calls),3)

    def test_completed_terminal_checks_mutated_prompt(self):
        self.prepare();self.run_driver()
        p=next(self.runroot.glob('host-calls/*/*/prompt.txt'));p.write_text('changed')
        with self.assertRaisesRegex(ContractError,'binding_changed'):self.run_driver()
        self.assertEqual(len(self.calls),3)

    def test_completed_terminal_checks_staged_response(self):
        self.prepare();self.run_driver()
        p=next((self.runroot/'episodes').glob('*/turns/*/inputs/*/steps/*/host-response.json'))
        x=json.loads(p.read_text());x['payload']['submission']['reply']['text']='changed'
        x['sha256']=digest(x['payload']);p.write_text(json.dumps(x))
        with self.assertRaisesRegex(ContractError,'staged_reply_changed'):self.run_driver()
        self.assertEqual(len(self.calls),3)

    def test_returned_invalid_json_has_process_and_usage_receipt(self):
        self.prepare();original=self.mock_cli
        def run(cmd,*args):
            value=original(cmd,*args);Path(cmd[cmd.index('-o')+1]).write_text('{invalid');return value
        with patch.object(self.driver,'_run_cli',side_effect=run):r=self.driver.drive(self.runroot,'pure_codex')
        failure=read_record(Path(r['failure_record']))
        self.assertTrue(failure['process_returned']);self.assertTrue(failure['transport_completed'])
        self.assertFalse(failure['reply_validated']);self.assertEqual(failure['usage']['input_tokens'],12)
        self.assertEqual(self.run_driver(),r);self.assertEqual(len(self.calls),1)

    def test_failed_terminal_detects_changed_invalid_json(self):
        self.prepare();original=self.mock_cli
        def run(cmd,*args):
            value=original(cmd,*args);Path(cmd[cmd.index('-o')+1]).write_text('{invalid');return value
        with patch.object(self.driver,'_run_cli',side_effect=run):self.driver.drive(self.runroot,'pure_codex')
        next(self.runroot.glob('host-calls/*/*/reply.json')).write_text('{different')
        with self.assertRaisesRegex(ContractError,'failed_reply_changed'):self.run_driver()
        self.assertEqual(len(self.calls),1)


    def test_completed_terminal_detects_missing_entire_call_directory(self):
        import shutil
        self.prepare();self.run_driver()
        victim=next(self.runroot.glob('host-calls/*/*/outcome.json')).parent
        shutil.rmtree(victim)
        with self.assertRaisesRegex(ContractError,'call_set_changed'):self.run_driver()
        with self.assertRaisesRegex(ContractError,'call_set_changed'):self.driver.step(self.runroot,'pure_codex')
        self.assertEqual(len(self.calls),3)

    def test_completed_terminal_detects_missing_all_call_records(self):
        import shutil
        self.prepare();self.run_driver();shutil.rmtree(self.runroot/'host-calls')
        with self.assertRaisesRegex(ContractError,'call_set_changed'):self.run_driver()
        self.assertEqual(len(self.calls),3)

if __name__=='__main__':unittest.main()
