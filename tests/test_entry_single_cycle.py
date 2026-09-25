"""Counterexamples for the bounded repair. All providers/host texts are fixtures."""
from copy import deepcopy
from pathlib import Path
import hashlib
import tempfile
import unittest
from unittest.mock import patch

from experiments.typed_decision import comparison_v03 as cmp, evaluation_integrity as ev
from experiments.typed_decision import route_control_v03 as runtime, source_direct_v03 as sd
from experiments.typed_decision import relationship_assessment as rel
from experiments.typed_decision.contracts import ContractError, digest
from experiments.typed_decision.current_host import CurrentAgentHost, submit_response
from experiments.typed_decision.session import read_record, write_once
from tests import test_route_control_v03 as f

REPO = Path(__file__).resolve().parents[1]


class ScopedDeliveryTests(unittest.TestCase):
    setUp = f.V03Tests.setUp
    run_entry = f.V03Tests.run_entry
    submit = f.V03Tests.submit
    drive = f.V03Tests.drive
    edge = f.V03Tests.edge

    def limited_reply(self, reply, q, status='bounded_answer'):
        if not q.get('limited_response'):
            return
        reply.update(performed_methods=[], scope_status=status,
            text='The supplied source supports a limited answer; no named method has been committed.',
            objection={'route_id': q['route_id'], 'revision': q['revision'],
                'affected_issue_or_step': q['issue']['issue_id'], 'kind': 'method_boundary',
                'original_refs': [rel.quote(self.data['documents'][0])],
                'claimed_conflict': 'The method route remains uncertain; the answer must stay source-bounded.',
                'requested_change': 'Accept only the bounded answer, without claiming method execution.'})

    def test_global_missing_keeps_independent_committed_deliveries(self):
        self.data = f.packet(count=2)
        self.provider = f.Provider({'COVERAGE.global': 'missing'})
        result = self.drive()
        self.assertEqual(set(result['delivery']['accepted_outputs']), {'I1', 'I2'})
        self.assertEqual(result['delivery']['state'], 'partial')
        self.assertFalse(result['consumption_complete'])
        self.assertFalse(result['routing_complete'])

    def test_global_unclear_does_not_block_ready_scope(self):
        self.provider = f.Provider({'COVERAGE.global': 'unclear'})
        result = self.drive()
        self.assertIn('I1', result['outputs'])
        self.assertEqual(result['delivery']['unassigned_scope'], 'unclear')

    def test_global_missing_allows_independent_post_artifact_evaluation(self):
        self.edge()
        self.provider = f.Provider({'COVERAGE.global': 'missing', 'M02.I2.wae': .5},
                                   after={'M02.I2.wae': .95})
        result = self.drive()
        self.assertEqual(set(result['delivery']['accepted_outputs']), {'I1', 'I2'})
        self.assertFalse(result['consumption_complete'])

    def test_uncertain_single_method_can_deliver_without_route_commit(self):
        self.provider = f.Provider({'M02.I1.wae': .79})
        result = self.drive(self.limited_reply)
        self.assertIn('I1', result['delivery']['accepted_outputs'])
        self.assertEqual(result['outputs']['I1']['methods'], [])
        self.assertEqual(result['route']['per_issue'][0]['mode'], 'delegated_unresolved')
        self.assertFalse(result['routing_complete'])
        self.assertEqual(result['delivery']['accepted_outputs']['I1']['route_status'], 'limited_response')
        self.assertEqual(self.provider.overrides['M02.I1.wae'], .79)
        self.assertEqual(result, self.run_entry())

    def test_limited_response_can_remain_unresolved(self):
        self.provider = f.Provider({'M02.I1.wae': .77})
        result = self.drive(lambda r,q:self.limited_reply(r,q,'unresolved'))
        self.assertEqual(result['delivery']['accepted_outputs'], {})
        self.assertFalse(result['consumption_complete'])
        self.assertEqual(result['pending']['I1'], 'limited_host_unresolved')

    def test_limited_reply_requires_explicit_status_and_source(self):
        self.provider = f.Provider({'M02.I1.wae': .77})
        result = self.run_entry()
        with self.assertRaisesRegex(ContractError, 'limited_reply'):
            self.submit(result)
        def no_source(r,q):
            self.limited_reply(r,q);r['objection']['original_refs']=[]
        with self.assertRaises(ContractError):
            self.submit(result,no_source)

    def test_limited_response_cannot_claim_uncommitted_method(self):
        self.provider = f.Provider({'M02.I1.wae': .77})
        def claim(r,q):
            self.limited_reply(r,q);r['performed_methods']=['wae']
        with self.assertRaisesRegex(ContractError, 'limited_reply'):
            self.submit(self.run_entry(),claim)

    def test_limited_response_cannot_waive_permission(self):
        self.provider = f.Provider({'M02.I1.wae': .77})
        def permission(r,q):
            self.limited_reply(r,q);r['objection']['kind']='permission'
        with self.assertRaisesRegex(ContractError, 'method_boundary_only'):
            self.submit(self.run_entry(),permission)

    def test_explicit_obligations_disable_limited_exit(self):
        self.provider = f.Provider({'M02.I1.wae': .77})
        self.data['authority']['known_obligations']=['Required independent verification before release.']
        result=self.drive()
        self.assertFalse(result['outputs'])
        self.assertFalse(any(q.get('limited_response') for q in self.requests))

    def test_missing_local_coverage_cannot_be_disguised_as_method_ambiguity(self):
        self.provider=f.Provider({'M02.I1.wae':.77,'COVERAGE.I1':'missing'})
        self.assertFalse(self.drive()['outputs'])

    def test_dependency_cannot_be_waived_by_limited_response(self):
        self.edge();self.provider=f.Provider({'M02.I2.wae':.77},after={'M02.I2.wae':.77})
        result=self.drive()
        self.assertIn('I1',result['outputs']);self.assertNotIn('I2',result['outputs'])
        self.assertFalse(any(q.get('limited_response') for q in self.requests))

    def test_multiple_required_methods_do_not_silently_degrade(self):
        self.data=f.packet(candidates=('wae','tvg'))
        self.provider=f.Provider({'M02.I1.tvg':.5,'M03.I1.tvg':'support'})
        self.assertFalse(self.drive()['outputs'])

    def test_capacity_failure_precedes_any_judgment_or_host_call(self):
        self.data=f.packet(count=3);self.data['task_budget']['max_calls']=2
        result=self.run_entry()
        self.assertEqual(result['reason'],'insufficient_execution_capacity_before_inference')
        self.assertEqual(self.provider.batch_count,0)
        self.assertEqual(result['counts']['total'],0)

    def test_organizer_capacity_reserves_acceptance(self):
        _,_,bindings,_=runtime._bundle(REPO)
        self.data['task_budget']['max_calls']=2
        q=runtime._organize_request(self.data,bindings)
        self.assertEqual(q['max_issues'],1)
        self.assertIn('auxiliary unknowns',q['instruction'])

    def test_dispatch_and_s1_use_only_relevant_actual_material(self):
        result=self.drive()
        execute=next(q for q in self.requests if q['schema'].endswith('execution-request.v1'))
        self.assertEqual(set(execute['loaded_methods']),{'wae'})
        contexts=[ctx for _,ctx in self.provider.seen if 'assessment_targets' in ctx]
        self.assertEqual(set(contexts[0]['host_method_materials']),{'wae'})
        self.assertTrue(result['consumption_complete'])

    def test_global_missing_with_known_obligation_stays_blocked(self):
        self.data['authority']['known_obligations']=['Require owner approval before release.']
        self.provider=f.Provider({'COVERAGE.global':'missing'})
        result=self.drive();self.assertFalse(result['outputs'])
        self.assertEqual(result['pending']['I1'],'unresolved_shared_obligation')

    def test_limited_exit_rejects_other_reason_and_mandatory_read(self):
        self.provider=f.Provider({'M02.I1.wae':.77})
        result=self.run_entry();route=deepcopy(result['route']);row=route['per_issue'][0]
        route['mandatory_reads']=['sra']
        self.assertIsNone(runtime._limited_response(self.data,route,row))
        route['mandatory_reads']=[];row['reason']='shared_gate_unknown'
        self.assertIsNone(runtime._limited_response(self.data,route,row))

    def test_organizer_unassigned_gate_is_source_bound_and_blocks_only_affected(self):
        self.data=f.packet();self.data['issues']=[];self.data['host_inferences']['issue_views']={}
        self.hooks['organizer']=CurrentAgentHost(self.data['authority']['owner_ref'],role='organize')
        def omitted(r,q):
            if q['schema'].endswith('organize-request.v1'):
                r['coverage_disposition']={'status':'partial','unassigned':[{
                    'source_ref':rel.quote(self.data['documents'][0]),'kind':'shared_gate',
                    'affected_issues':['I1'],'reason':'Source-bound approval prerequisite needs resolution.'}]}
        result=self.drive(omitted)
        self.assertFalse(result['outputs']);self.assertFalse(result['consumption_complete'])
        self.assertEqual(result['pending']['I1'],'unassigned_shared_prerequisite')

    def test_stale_acceptance_hash_does_not_make_a_delivery(self):
        value=runtime.delivery_summary(None,{'I1':{'text':'actual','artifact_sha256':digest('actual')}},
                                       {'accepted':{'I1':{'accepted':True,'artifact_sha256':digest('other')}}},{})
        self.assertFalse(value['accepted_outputs'])


class EntryMaterialTests(unittest.TestCase):
    setUp=f.V03Tests.setUp

    def native(self):
        return cmp.run_native(self.root,self.data,REPO,condition='pure_codex',
                              executor=self.hooks['executor'],corrector=self.hooks['corrector'])

    def submit_native(self,result,*,read=None):
        h=read_record(Path(result['host_request']));q=h['request'];self.requests.append(deepcopy(q))
        if q['schema'].endswith('accept-request.v1'):
            reply={'schema':'mindthus.route-v03-accept-reply.v1','request_id':q['request_id'],
                   'accepted':{iid:{'accepted':True,'artifact_sha256':sha,'reason':'Synthetic host accepts.'}
                               for iid,sha in q['candidates'].items()},'usage':deepcopy(f.rt.UNKNOWN_USAGE)}
        else:
            text=q['candidate'] or 'Fixture source-bounded answer.'
            reply={'schema':'mindthus.route-v03-native-reply.v1','request_id':q['request_id'],
                   'text':text,'version':digest(text),'performed_methods':['wae'] if 'wae' in q['condition_packet']['loaded_methods'] else [],
                   'decision_status':'decided','dispute':None,'usage':deepcopy(f.rt.UNKNOWN_USAGE),
                   'artifact_action':'retain' if q['candidate'] else 'replace'}
            if read is not None:
                reply.update(text='',version=digest(''),performed_methods=[],decision_status='unresolved',
                             artifact_action='read_methods',requested_methods=read)
        submit_response(self.root,REPO,{'schema':'mindthus.current-host-response.v1',
                        'request_id':h['request_id'],'request_sha256':h['request_sha256'],
                        'owner_ref':h['owner_ref'],'host_context_ref':'fixture-native-context',
                        'elapsed_seconds':1.0,'reply':reply})

    def test_both_branches_receive_identical_actual_entry_rules(self):
        _,_,bindings,_=runtime._bundle(REPO)
        native=cmp.prepare_condition(self.data,'pure_codex',REPO)
        organizer=runtime._organize_request(self.data,bindings)
        self.assertEqual(native['entry_skill'],organizer['entry_skill'])
        self.assertEqual(native['entry_skill']['sha256'],runtime._bundle(REPO)[0]['sources']['skills/using-mindthus/SKILL.md'])

    def test_default_preparation_loads_only_real_entry(self):
        with patch.object(cmp.rc,'_read_methods',side_effect=AssertionError('preloaded')):
            body=cmp.prepare_condition(self.data,'pure_codex',REPO)
        self.assertEqual(body['loaded_methods'],{})
        self.assertEqual(body['entry_skill']['content'],(REPO/'skills/using-mindthus/SKILL.md').read_text())
        self.assertEqual(len(body['method_catalog']),8)
        self.assertNotIn('question_contract',body)

    def test_preload_is_explicitly_diagnostic(self):
        body=cmp.prepare_condition(self.data,'pure_codex',REPO,material_policy='all_methods_diagnostic')
        self.assertEqual(len(body['loaded_methods']),8)
        self.assertIn('diagnostic',body['baseline_claim'])

    def test_actual_requested_read_then_answer_and_replay(self):
        self.data['task_budget']['max_calls']=4
        first=self.native();self.submit_native(first,read=['wae'])
        second=self.native()
        q=read_record(Path(second['host_request']))['request']
        self.assertEqual(set(q['condition_packet']['loaded_methods']),{'wae'})
        self.submit_native(second)
        for _ in range(3):
            result=self.native()
            if result.get('status')!='awaiting_current_agent':break
            self.submit_native(result)
        self.assertTrue(result['consumption_complete'])
        self.assertEqual(result['counts']['execution'],3)
        self.assertEqual(len(result['method_reads']),1)
        self.assertEqual(result['method_reads'][0]['loads']['wae']['content'],(REPO/'skills/wae/SKILL.md').read_text())
        self.assertEqual(result,self.native())

    def test_method_can_be_read_during_review_with_remaining_budget(self):
        self.data['task_budget']['max_calls']=4
        first=self.native();self.submit_native(first)
        review=self.native();q=read_record(Path(review['host_request']))['request']
        self.assertIsNotNone(q['candidate']);self.assertIn('read_methods',q['artifact_actions'])
        self.submit_native(review,read=['wae'])
        next_r=self.native();q=read_record(Path(next_r['host_request']))['request']
        self.assertEqual(set(q['condition_packet']['loaded_methods']),{'wae'})
        self.submit_native(next_r)
        accepted=self.native();self.submit_native(accepted)
        result=self.native();self.assertTrue(result['consumption_complete'])
        self.assertEqual(result['counts']['correction'],1)
        self.assertEqual(result['counts']['execution'],3)
        self.assertEqual(result,self.native())

    def test_unread_method_claim_rejected(self):
        with self.assertRaisesRegex(ContractError,'comparison_native_decision'):
            result=self.native();h=read_record(Path(result['host_request']));q=h['request']
            reply={**h['reply_shape'],'text':'False execution claim.','version':digest('False execution claim.'),
                   'performed_methods':['wae'],'decision_status':'decided','artifact_action':'replace'}
            cmp.validate_native_reply(reply,q)

    def test_method_outside_catalog_rejected(self):
        self.data['task_budget']['max_calls']=4
        with self.assertRaisesRegex(ContractError,'comparison_method_request'):
            self.submit_native(self.native(),read=['../private'])

    def test_read_cannot_consume_reserved_acceptance_slot(self):
        self.data['task_budget']['max_calls']=2
        r=self.native();q=read_record(Path(r['host_request']))['request']
        self.assertNotIn('read_methods',q['artifact_actions'])
        with self.assertRaises(ContractError):self.submit_native(r,read=['wae'])


class SourceWindowTests(unittest.TestCase):
    def setUp(self):
        self.source=f.packet()
        self.source['issues']=[];self.source['host_inferences']['issue_views']={}
        self.source['documents'] += [
            {'id':'A','revision':'1','kind':'assistant','text':'Historical answer.'},
            {'id':'U2','revision':'1','kind':'user','text':'Later explicit correction.'},
            {'id':'limit','revision':'1','kind':'source','text':'Original image unavailable.'}]
        self.source['conversation'] += [
            {'document_id':'A','role':'assistant','order':1,'author_ref':'old','source_ref':'archive:A'},
            {'document_id':'U2','role':'user','order':2,'author_ref':'user','source_ref':'archive:U2'}]
        self.source['intervention']['history_sha256']=sd.history_identity(self.source)

    def prefix(self):
        return ev.prepare_prefix(self.source,0,auxiliary_availability={'limit':0},phase='initial',
                                 missing_original=['image'])

    def test_initial_prefix_excludes_future_correction_and_assistant(self):
        result=self.prefix()
        self.assertEqual({d['id'] for d in result['packet']['documents']},{'U','limit'})
        self.assertNotIn('Later explicit correction',str(result))
        self.assertFalse(result['metadata']['original_failure_reproduction_eligible'])

    def test_late_cutoff_cannot_be_named_initial(self):
        with self.assertRaisesRegex(ContractError,'initial_contains_history'):
            ev.prepare_prefix(self.source,2,auxiliary_availability={},phase='initial')

    def test_assistant_cannot_be_smuggled_as_auxiliary_source(self):
        with self.assertRaisesRegex(ContractError,'auxiliary_source'):
            ev.prepare_prefix(self.source,0,auxiliary_availability={'A':0},phase='initial')

    def test_gold_field_in_source_rejected(self):
        self.source['expected_answer']='answer key'
        with self.assertRaisesRegex(ContractError,'source_fields'):self.prefix()

    def test_later_auxiliary_source_not_visible_early(self):
        result=ev.prepare_prefix(self.source,0,auxiliary_availability={'limit':2},phase='initial')
        self.assertEqual(len(result['packet']['documents']),1)

    def test_new_turn_requires_bound_realized_receipt(self):
        prefix=self.prefix();text='Actual fixture branch answer.'
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'outcome.json'
            request={'request_id':'request','original_input':prefix['packet']}
            write_once(path,{'status':'complete','host_context_ref':'ctx','reply':{'text':text}})
            write_once(path.with_name('request.json'),request)
            write_once(path.with_name('intent.json'),{'request_id':'request','request_sha256':digest(request)})
            assistant={'text':text,'artifact_sha256':digest(text),'author_ref':'fixture-host',
                       'context_ref':'ctx','receipt_ref':str(path),'acceptance_ref':str(Path(root)/'accept/outcome.json')}
            ap=Path(assistant['acceptance_ref']);ap.parent.mkdir()
            ar=sd.acceptance_request(prefix['packet'],{'route_id':'r','revision':1},
                {'I1':{'text':text,'artifact_sha256':digest(text)}},{'I1':'resolved'}, {})
            reply={'schema':'mindthus.route-v03-accept-reply.v1','request_id':ar['request_id'],
                   'accepted':{'I1':{'accepted':True,'artifact_sha256':digest(text),'reason':'Fixture accepted.'}},
                   'usage':deepcopy(f.rt.UNKNOWN_USAGE)}
            write_once(ap,{'status':'complete','host_context_ref':'ctx','reply':reply})
            write_once(ap.with_name('request.json'),ar)
            write_once(ap.with_name('intent.json'),{'request_id':ar['request_id'],'request_sha256':digest(ar)})
            user={'document':next(d for d in self.source['documents'] if d['id']=='U2'),'source_ref':'archive:U2'}
            result=ev.append_branch_turn(prefix,assistant=assistant,next_user=user,context_ref='ctx')
            self.assertEqual(result['metadata']['claim'],'new_realized_trajectory_not_original_failure_replay')
            self.assertNotIn('Historical answer.',str(result['packet']))
            assistant['text']='Forged replacement';assistant['artifact_sha256']=digest(assistant['text'])
            with self.assertRaisesRegex(ContractError,'receipt_mismatch'):
                ev.append_branch_turn(prefix,assistant=assistant,next_user=user,context_ref='ctx')

    def review_artifact(self,text,materials=None):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        path=Path(tmp.name)/'request.json'
        q={'request_id':'fixture-producing','loaded_methods':materials or {}}
        write_once(path,q)
        write_once(path.with_name('intent.json'),{'request_id':q['request_id'],'request_sha256':digest(q)})
        write_once(path.with_name('outcome.json'),{'status':'complete','reply':{'text':text}})
        return {'text':text,'artifact_sha256':digest(text),'actual_method_materials':materials or {},
                'producing_request_ref':str(path)}

    def test_review_requires_separate_target_dimensions_and_consequence(self):
        case=self.prefix();text='A bounded candidate.'
        request=ev.reviewer_packet(case,'F',{'X1':self.review_artifact(text)})
        self.assertNotIn('target_dimensions',case['packet'])
        self.assertIn('unwarranted_time_scope',request['target_dimensions'])
        value={'verdict':'pass','reason':'Supported by this synthetic source.',
               'source_refs':[rel.quote(case['packet']['documents'][0])],
               'answer_spans':[{'start':0,'end':len(text),'sha256':digest(text)}],'decision_consequence':''}
        reply={'artifacts':{'X1':{'overall_usable':'yes','dimensions':{k:deepcopy(value) for k in request['target_dimensions']}}}}
        self.assertTrue(ev.validate_review(reply,request))
        reply['artifacts']['X1']['dimensions']['unwarranted_time_scope']['verdict']='fail'
        with self.assertRaisesRegex(ContractError,'failure_consequence'):ev.validate_review(reply,request)

    def test_review_cannot_invent_candidate_or_method_material(self):
        a=self.review_artifact('old');a['text']='changed'
        with self.assertRaisesRegex(ContractError,'artifact_binding'):
            ev.reviewer_packet(self.prefix(),'E',{'X1':a})
        a=self.review_artifact('ok')
        a['actual_method_materials']={'wae':{'path':'skills/wae/SKILL.md',
            'sha256':hashlib.sha256(b'invented').hexdigest(),'content':'invented'}}
        with self.assertRaisesRegex(ContractError,'actual_load_mismatch'):
            ev.reviewer_packet(self.prefix(),'E',{'X1':a})

    def test_clean_prefix_is_not_original_failure_reproduction_proof(self):
        result=ev.prepare_prefix(self.source,0,auxiliary_availability={},phase='initial')
        self.assertFalse(result['metadata']['original_failure_reproduction_eligible'])



class PortableDriverTests(unittest.TestCase):
    def setUp(self):
        import importlib.util
        path=REPO/'docs/internal/research/typed-decision/route-control-v0.2/single-cycle-repair-v1/run.py'
        spec=importlib.util.spec_from_file_location('single_cycle_driver_tests',path)
        self.driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.driver)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        registry=patch.object(f.rt,'_registry',return_value=self.root/'registry')
        registry.start();self.addCleanup(registry.stop)
        source=SourceWindowTests();source.setUp();self.source=source.source

    def test_fresh_freeze_and_native_first_handoff_without_jev(self):
        import json
        source_path=self.root/'source.json';source_path.write_text(json.dumps(self.source))
        # The fixture has a source named limit; adapt only its explicit source ID.
        x=self.source['documents'][-1];x['id']='source-limit';source_path.write_text(json.dumps(self.source))
        target=self.root/'new-run'
        self.driver.prepare(target,source_path,'E',0,'initial',[], 'fixture-host','high','/usr/bin/true','local://fixture')
        result=self.driver.step(target,'pure_codex')
        self.assertEqual(result['status'],'awaiting_current_agent')
        h=read_record(Path(result['host_request']));q=h['request']
        self.assertEqual(q['condition_packet']['loaded_methods'],{})
        self.assertEqual(len(q['condition_packet']['original_input']['documents']),1)
        self.assertFalse(any('calls' in str(p) for p in (target/'episodes').rglob('intent.json')))
        self.assertEqual(self.driver.step(target,'pure_codex')['host_request'],result['host_request'])

    def test_native_read_schema_and_normalizer_preserve_choice(self):
        data=f.packet();prepared=cmp.prepare_condition(data,'pure_codex',REPO)
        q={'schema':'mindthus.route-v03-native-request.v1','request_id':'x',
           'condition_packet':prepared,'artifact_actions':['replace','read_methods'],'candidate':None}
        schema=self.driver.schema_for(q)
        self.assertIn('requested_methods',schema['required'])
        raw={'text':'','performed_methods':[],'decision_status':'unresolved','dispute_reason':'',
             'source_ids':[],'artifact_action':'read_methods','requested_methods':['wae']}
        out=self.driver.normalize(raw,q,deepcopy(f.rt.UNKNOWN_USAGE))
        cmp.validate_native_reply(out,q)
        self.assertEqual(out['requested_methods'],['wae'])

    def test_organizer_wire_omission_is_not_discarded(self):
        data=f.packet();_,_,bindings,_=runtime._bundle(REPO);q=runtime._organize_request(data,bindings)
        raw={'issues':[{'id':'I1','candidates':['wae'],'handling':'judge','actor':'owner','goal':'judge','scope':'U'}],
             'coverage_disposition':{'status':'partial','unassigned':[{'source_id':'U','kind':'shared_gate',
                                    'affected_issues':['I1'],'reason':'Need original approval.'}]}}
        out=self.driver.normalize(raw,q,deepcopy(f.rt.UNKNOWN_USAGE))
        runtime.validate_organized(out,q,bindings)
        self.assertEqual(out['coverage_disposition']['unassigned'][0]['kind'],'shared_gate')
        schema=self.driver.schema_for(q);self.assertEqual(schema['properties']['issues']['maxItems'],1)


if __name__=='__main__':
    unittest.main()
