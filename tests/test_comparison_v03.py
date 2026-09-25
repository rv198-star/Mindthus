"""Experimental controls use declared synthetic callbacks; no model/network runs."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.typed_decision import comparison_v03 as cmp, route_control_v03 as runtime, source_direct_v03 as sd
from experiments.typed_decision import relationship_runtime as rt, relationship_assessment as rel
from experiments.typed_decision.current_host import CurrentAgentHost, submit_response
from experiments.typed_decision.contracts import ContractError, DecisionSpec, digest
from experiments.typed_decision.session import read_record
from tests.test_route_control_v03 import packet, FIT, Provider
from tests.test_route_control import Executor

REPO=Path(__file__).resolve().parents[1]


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()/'episode'
        p=patch.object(rt,'_registry',return_value=self.root.parent/'registry');p.start();self.addCleanup(p.stop)
        self.data=packet();self.calls=[];self.requests=[]
        self.executor=CurrentAgentHost('original-host')
        self.corrector=CurrentAgentHost('original-host',role='correction')
        self.arbitrator=CurrentAgentHost('original-host',role='arbitration')

    def observe(self,q,timeout):
        self.calls.append(deepcopy(q));answers={}
        for s in q['questions']:
            if s['id'].startswith('S1.'):v=FIT[s['id'].split('.')[-1]]
            elif s['id'].startswith('COVERAGE.'):v='covered'
            elif s['id'].startswith(('ROLE_SCOPE.','COMPANION_SCOPE.')):v='required'
            else:v={'M02':.95,'M03':'primary_candidate','G03':'judge','R02':'same_scope','R03':'right',
                    'M05':.95,'R04':'needed_to_begin','S01':.95,'S02':2.0}[s['id'].split('.')[0]]
            answers[s['id']]={'status':'ok','value':v}
        return {'request_id':q['request_id'],'context_ref':'observer-isolated','configuration':q['configuration'],
                'answers':answers,'usage':dict(rt.UNKNOWN_USAGE)}

    def provider(self):
        return cmp.CurrentAgentObserver(self.observe,model='synthetic-current-codex',
            host_context_ref='original-host-context',configuration={'reasoning_effort':'high','tools':'none'})

    def drive(self,condition,provider=None,admission=None,snapshot=None,dispute=False):
        for _ in range(12):
            result=cmp.run_condition(self.root,provider,self.data,REPO,condition=condition,
                executor=self.executor,corrector=self.corrector,arbitrator=self.arbitrator,
                live_admission=admission,candidate_snapshot=snapshot)
            if result.get('status')!='awaiting_current_agent':return result
            h=read_record(Path(result['host_request']));q=h['request'];self.requests.append(q)
            schema=q['schema']
            if schema.endswith('native-request.v1'):
                text='Natural fixture judgment.' if q['candidate'] is None else 'Reviewed fixture judgment.'
                d={'reason':'Source-bound disagreement needs independent resolution.',
                   'original_refs':[rel.quote(self.data['documents'][0])]} if dispute and q['candidate'] is not None else None
                reply={'schema':'mindthus.route-v03-native-reply.v1','request_id':q['request_id'],
                       'text':text,'version':digest(text),'performed_methods':[], 'artifact_action':'replace',
                       'decision_status':'disputed' if d else 'decided','dispute':d,'usage':dict(rt.UNKNOWN_USAGE)}
            elif schema.endswith('execution-request.v1'):
                reply=Executor().execute(q,45)
            elif schema.endswith('arbitration-request.v1'):
                reply={'schema':'mindthus.route-v03-arbitration-reply.v1','request_id':q['request_id'],
                    'decisions':[{'finding_id':f['finding_id'],'target_version':f['target_version'],'decision':'dismiss',
                        'reason':'The source supports the narrow decision.', 'original_refs':[rel.quote(self.data['documents'][0])]}
                        for f in q['findings']], 'usage':dict(rt.UNKNOWN_USAGE)}
            else:
                reply={'schema':'mindthus.route-v03-accept-reply.v1','request_id':q['request_id'],
                       'accepted':{iid:{'accepted':q['dispositions'][iid]=='resolved','artifact_sha256':sha,'reason':'Fixture acceptance.'}
                                   for iid,sha in q['candidates'].items()},'usage':dict(rt.UNKNOWN_USAGE)}
            submit_response(self.root,REPO,{'schema':'mindthus.current-host-response.v1','request_id':h['request_id'],
                'request_sha256':h['request_sha256'],'owner_ref':h['owner_ref'],
                'host_context_ref':'independent-arbitrator' if h['role']=='arbitration' else 'original-host-context',
                'elapsed_seconds':1.0,'reply':reply})
        self.fail('unexpected comparison loop')

    def test_pure_native_keeps_first_answer_and_review_no_observer(self):
        result=self.drive('pure_codex')
        self.assertTrue(result['consumption_complete']);self.assertFalse(self.calls)
        self.assertNotEqual(result['initial']['text'],result['reviewed']['text'])
        self.assertEqual(result['counts']['correction'],1);self.assertEqual(result['counts']['judgment'],0)
        self.assertEqual(result['counts']['execution'],2)
        original=self.requests[0]['condition_packet']['original_input']
        self.assertNotIn('host_inferences',original);self.assertNotIn('issues',original)

    def test_retention_binds_actual_candidate_not_acknowledgment(self):
        request={'request_id':'request', 'artifact_actions':['retain','replace'], 'candidate':'Original answer.',
                 'condition_packet':{'loaded_methods':{}}}
        reply={'schema':'mindthus.route-v03-native-reply.v1','request_id':'request','artifact_action':'retain',
               'text':'Original answer.','version':digest('Original answer.'),'performed_methods':[],
               'decision_status':'decided','dispute':None,'usage':dict(rt.UNKNOWN_USAGE)}
        cmp.validate_native_reply(reply,request)
        reply.update(text='Keep the original.',version=digest('Keep the original.'))
        with self.assertRaisesRegex(ContractError,'retained_version'):cmp.validate_native_reply(reply,request)
        request['candidate']=None;request['artifact_actions']=['replace']
        with self.assertRaisesRegex(ContractError,'artifact_action'):cmp.validate_native_reply(reply,request)

    def test_questions_only_receives_unfilled_questions(self):
        result=self.drive('questions_only');self.assertTrue(result['consumption_complete'])
        q=self.requests[0]['condition_packet']['question_contract']
        self.assertEqual(set(q),set(FIT));self.assertTrue(all(set(row)=={'question','criteria'} for row in q.values()))
        routing=self.requests[0]['condition_packet']['routing_questions']
        self.assertTrue({'G03','M02','R04','coverage_global','method_scope'}<=set(routing))

    def test_all_conditions_same_source_methods_and_budget(self):
        prepared=[cmp.prepare_condition(self.data,c,REPO) for c in cmp.CONDITIONS]
        self.assertEqual(len({p['source_identity'] for p in prepared}),1)
        self.assertEqual(len({p['method_identity'] for p in prepared}),1)
        self.assertTrue(all(p['host_work_limits']==prepared[0]['host_work_limits'] for p in prepared))

    def test_native_optional_arbitration_replays_to_acceptance(self):
        result=self.drive('pure_codex',dispute=True)
        self.assertTrue(result['consumption_complete']);self.assertEqual(result['counts']['arbitration'],1)
        self.assertTrue((next(self.root.glob('turns/*/inputs/*'))/'before-arbitration.json').exists())

    def test_codex_control_needs_explicit_experimental_admission(self):
        provider=self.provider();hooks=dict(executor=self.executor,corrector=self.corrector,arbitrator=self.arbitrator,organizer=None)
        with self.assertRaisesRegex(ContractError,'official_jev'):
            runtime.prepare_admission(self.root,provider,self.data,REPO,hooks,authorization_ref='synthetic-test')
        admission=runtime.prepare_admission(self.root,provider,self.data,REPO,hooks,authorization_ref='synthetic-test',
                                           experiment_condition='codex_observation_committed')
        result=self.drive('codex_observation_committed',provider,admission)
        self.assertTrue(result['consumption_complete']);self.assertEqual(len(self.calls),2)
        self.assertEqual(result['counts']['judgment'],2)
        row=result['s0']['observations']['M02.I1.wae'];self.assertIsNone(row['uncertainty'])
        self.assertEqual(row['reason'],'ordinary_llm_uncalibrated')

    def test_codex_observer_rejects_same_context(self):
        provider=self.provider();original=self.observe
        provider.observe=lambda q,t:{**original(q,t),'context_ref':'original-host-context'}
        spec=DecisionSpec('COVERAGE.I1','Select one.',{'covered':'supported','missing':'unsupported'},('text',))
        with self.assertRaisesRegex(ContractError,'observer_identity'):provider.evaluate([spec],{'text':'source'},1)

    def test_bad_single_observer_answer_keeps_valid_answer(self):
        provider=self.provider()
        def reply(q,t):
            return {'request_id':q['request_id'],'context_ref':'isolated','configuration':q['configuration'],
                'answers':{'one':{'status':'ok','value':'yes'},'two':{'status':'ok','value':'invalid'}},'usage':dict(rt.UNKNOWN_USAGE)}
        provider.observe=reply
        specs=[DecisionSpec(x,'Select one.',{'yes':'supported','no':'unsupported'},('text',)) for x in ('one','two')]
        batch=provider.evaluate(specs,{'text':'source'},1)
        self.assertEqual(batch.results['one'].value,'yes');self.assertEqual(batch.results['two'].status,'provider_error')
        self.assertEqual(provider.response_receipt()['response']['answers']['two']['value'],'invalid')
        self.assertEqual(provider.response_receipt()['validated_usage'],rt.UNKNOWN_USAGE)

    def test_declared_observer_host_must_match_actual_first_host_receipt(self):
        provider=self.provider();hooks=dict(executor=self.executor,corrector=self.corrector,arbitrator=self.arbitrator,organizer=None)
        admission=runtime.prepare_admission(self.root,provider,self.data,REPO,hooks,authorization_ref='synthetic-test',
                                           experiment_condition='codex_observation_committed')
        result=cmp.run_condition(self.root,provider,self.data,REPO,condition='codex_observation_committed',
                                executor=self.executor,corrector=self.corrector,arbitrator=self.arbitrator,
                                live_admission=admission)
        h=read_record(Path(result['host_request']));reply=Executor().execute(h['request'],45)
        with self.assertRaisesRegex(ContractError,'v03_observer_original_context_changed'):
            submit_response(self.root,REPO,dict(schema='mindthus.current-host-response.v1',request_id=h['request_id'],
                request_sha256=h['request_sha256'],owner_ref=h['owner_ref'],host_context_ref='undeclared-host',
                elapsed_seconds=1.,reply=reply))

    def test_observer_configuration_cannot_change_after_identity_freeze(self):
        provider=self.provider();provider.configuration['reasoning_effort']='low'
        with self.assertRaisesRegex(ContractError,'configuration_changed'):
            provider.evaluate([],{},1)

    def test_common_candidate_checks_without_regeneration_or_s0(self):
        snapshot=cmp.common_candidate(self.data,{'I1':'A supplied natural candidate.'},REPO,
            provenance={'author_ref':'historic-codex','context_ref':'source-context','source_ref':'synthetic:test'})
        result=self.drive('jev_committed',Provider(),snapshot=snapshot)
        self.assertTrue(result['consumption_complete']);self.assertIsNone(result['s0'])
        self.assertEqual(result['counts']['judgment'],1);self.assertEqual(result['counts']['execution'],1)
        self.assertEqual(result['outputs']['I1']['text'],'A supplied natural candidate.')

    def test_common_candidate_native_review_uses_same_candidate(self):
        snapshot=cmp.common_candidate(self.data,{'I1':'A supplied natural candidate.'},REPO,
            provenance={'author_ref':'historic-codex','context_ref':'source-context','source_ref':'synthetic:test'})
        result=self.drive('pure_codex',snapshot=snapshot)
        self.assertTrue(result['consumption_complete'])
        self.assertEqual(self.requests[0]['candidate'],'A supplied natural candidate.')
        self.assertEqual(result['counts']['execution'],1)

    def test_snapshot_rejects_mismatching_text_hash(self):
        snapshot=cmp.common_candidate(self.data,{'I1':'Original.'},REPO,
            provenance={'author_ref':'codex','context_ref':'source','source_ref':'synthetic:test'})
        snapshot['outputs']['I1']['text']='Changed.'
        with self.assertRaisesRegex(ContractError,'snapshot_changed'):cmp.validate_snapshot(snapshot,self.data,REPO)

    def test_campaign_separates_gold_and_keeps_synthetic_label(self):
        families=[]
        for i,scenario in enumerate('EEFFABCDEEFF'):
            data=packet();data['documents'][0]['text']+=str(i)
            data['issues'][0]['request_ref']=rel.quote(data['documents'][0])
            for k in ('handling','assessability'):data['issues'][0][k]['refs']=[rel.quote(data['documents'][0])]
            data['intervention']['history_sha256']=sd.history_identity(data)
            families.append(dict(family_id=f'family{i}',scenario=scenario,source_kind='synthetic',origin_ref=f'fixture:{i}',
                                 packet=data,acceptance={'private_gold_marker':'reviewer only'}))
        plan=cmp.prepare_campaign(families,REPO,host_configuration={'model':'declared','reasoning_effort':'high',
                                                                  'tools_sha256':'test','output_limit':2000})
        self.assertNotIn('private_gold_marker',str(plan['manifest']))
        self.assertIn('private_gold_marker',str(plan['reviewer_only']))
        self.assertEqual(plan['manifest']['source_qualification'],'development_only')
        self.assertTrue(all(x=='unrun' for x in plan['manifest']['source_results'].values()))
        families[-1]['origin_ref']=families[0]['origin_ref']
        with self.assertRaisesRegex(ContractError,'duplicate_source'):
            cmp.prepare_campaign(families,REPO,host_configuration=plan['manifest']['host_configuration'])


if __name__=='__main__':unittest.main()
