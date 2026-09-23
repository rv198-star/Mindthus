"""Root-cause regression: mock wire data and host fixtures, never live model evidence."""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from experiments.typed_decision import entry, route_control as rc, relationship_runtime as rt
from experiments.typed_decision.contracts import ContractError, DecisionResult, DecisionSpec, digest
from experiments.typed_decision.providers import TypeSafeJevProvider, OpenRouterJevProvider, ProviderError
from experiments.typed_decision.session import Session, read_record, RecoveryRequired
from experiments.typed_decision.current_host import CurrentAgentHost, submit_response
from tests.test_route_control import Provider, Executor, Acceptor, packet
from experiments.typed_decision import relationship_assessment as rel

REPO = Path(__file__).resolve().parents[1]


def specs():
    return [DecisionSpec('n', 'Condition?', {'true': 'Met', 'false': 'Not met'}, ('text',), kind='assess_proposition'),
            DecisionSpec('c', 'Role?', {'primary': 'Primary', 'none': 'No role'}, ('text',)),
            DecisionSpec('s', 'Impact?', ['None', 'Local', 'Subtask', 'Core'], ('text',), kind='rate')]


def response():
    return {'model': 'jev-1.13.0', 'answers': {
        'n': {'type': 'noul', 'noul': .95},
        'c': {'type': 'choice', 'choice': 'primary', 'confidence': .8,
              'probabilities': {'primary': .9, 'none': .1}},
        's': {'type': 'score', 'score': 2.78, 'confidence': .8,
              'legend': dict(enumerate(['None', 'Local', 'Subtask', 'Core'])),
              'probabilities': {'0': .02, '1': .03, '2': .11, '3': .84}}},
        'usage': {'input_tokens': 123, 'output_tokens': 45, 'cost': .001}}


class ScopedWireTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = response()
        self.raw['answers']['s']['legend'] = {str(k): v for k, v in self.raw['answers']['s']['legend'].items()}
        self.calls = 0
        def transport(*_):
            self.calls += 1
            return deepcopy(self.raw)
        self.provider = TypeSafeJevProvider(transport=transport, choice_rounding=True)
        self.provider.is_live = False  # Injected transport; explicit offline test.
        p = patch.dict(os.environ, {'TYPESAFE_API_KEY': 'fixture-secret-key-123', 'OPENROUTER_API_KEY': 'fixture-secret-key-456'})
        p.start(); self.addCleanup(p.stop)

    def run_session(self):
        with Session(self.root / 'session', self.provider, scope='synthetic-root-cause-test') as s:
            return s.evaluate(specs(), {'text': 'Synthetic contract control, no business facts.'})

    def test_bad_score_does_not_erase_good_noul_choice(self):
        r = self.run_session()
        self.assertEqual([r[k].status for k in ('n','c','s')], ['ok','ok','provider_error'])
        self.assertTrue(r['s'].reason.startswith('answer_contract:'))
        self.assertIsNone(r['s'].value)

    def test_invalid_score_preserved_without_relaxing_tolerance(self):
        self.run_session()
        receipt = read_record(next((self.root/'session').glob('calls/*/provider-receipt.json')))['receipt']
        self.assertEqual(receipt['response'], self.raw)
        self.assertEqual(receipt['response']['answers']['s']['score'], 2.78)
        self.assertAlmostEqual(sum(int(k)*p for k,p in self.raw['answers']['s']['probabilities'].items()), 2.77)

    def test_valid_usage_and_runtime_survive_local_rejection(self):
        self.run_session()
        out = read_record(next((self.root/'session').glob('calls/*/outcome.json')))
        self.assertEqual(out['usage'], {'input_tokens':123,'output_tokens':45,'cost_usd':.001})
        self.assertEqual(out['resolved_runtime']['model'], 'jev-1.13.0')

    def test_score_probability_sum_error_is_local(self):
        self.raw['answers']['s']['probabilities']['3'] = .83
        r=self.run_session(); self.assertEqual(r['n'].status,'ok');self.assertEqual(r['s'].status,'provider_error')

    def test_exact_score_passes(self):
        self.raw['answers']['s']['score']=2.77
        self.assertTrue(all(r.status=='ok' for r in self.run_session().values()))

    def test_bad_choice_does_not_erase_noul_or_valid_score(self):
        self.raw['answers']['s']['score']=2.77;self.raw['answers']['c']['choice']='absent'
        r=self.run_session();self.assertEqual(r['c'].status,'provider_error');self.assertEqual(r['s'].status,'ok')

    def test_missing_question_id_is_global(self):
        del self.raw['answers']['c']
        r=self.run_session();self.assertTrue(all(x.status=='provider_error' for x in r.values()))
        self.assertFalse(r['n'].reason.startswith('answer_contract:'))

    def test_wrong_model_is_global_and_usage_kept(self):
        self.raw['model']='jev-9.99.0';r=self.run_session()
        self.assertTrue(all(x.status=='provider_error' for x in r.values()))
        out=read_record(next((self.root/'session').glob('calls/*/outcome.json')))
        self.assertIsNone(out['resolved_runtime']);self.assertEqual(out['usage']['input_tokens'],123)

    def test_answer_type_mismatch_is_local(self):
        self.raw['answers']['c']={'type':'noul','noul':.8}
        r=self.run_session();self.assertEqual(r['n'].status,'ok');self.assertEqual(r['c'].status,'provider_error')

    def test_redact_reflected_secrets_and_private_reasoning(self):
        self.raw['debug']='fixture-secret-key-123';self.raw['reasoning_content']='private trace never published'
        self.run_session();text=''.join(p.read_text() for p in self.root.rglob('*.json'))
        self.assertNotIn('fixture-secret-key-123',text);self.assertNotIn('private trace never published',text)

    def test_replay_zero_calls_and_byte_identical(self):
        first=self.run_session();saved={str(p):p.read_bytes() for p in self.root.rglob('*.json')}
        self.assertEqual(first,self.run_session());self.assertEqual(self.calls,1)
        self.assertEqual(saved,{str(p):p.read_bytes() for p in self.root.rglob('*.json')})

    def test_openrouter_has_same_local_error_scope(self):
        raw=deepcopy(self.raw);raw.update(model='typesafe/jev-1.13',provider='TypeSafe')
        p=OpenRouterJevProvider(transport=lambda *_:raw)
        b=p.evaluate(specs(),{'text':'fixture'},1)
        self.assertEqual(b.results['n'].status,'ok');self.assertEqual(b.results['s'].status,'provider_error')
        self.assertEqual(p.response_receipt()['response'],raw)

    def test_no_stale_receipt_after_transport_failure(self):
        self.provider.evaluate(specs(),{'text':'fixture'},1)
        def fail(*_):raise ProviderError('transport_failure')
        self.provider.transport=fail
        with self.assertRaises(ProviderError):self.provider.evaluate(specs(),{'text':'next'},1)
        self.assertIsNone(self.provider.response_receipt())


class AfterArtifactProvider(Provider):
    def __init__(self, remain_unresolved=False):
        super().__init__({'M02.I2.sra': .39})
        self.remain_unresolved = remain_unresolved
    def evaluate(self, specs, context, timeout):
        old = self.overrides
        if context.get('artifact_view') and not self.remain_unresolved:
            self.overrides = {**old, 'M02.I2.sra': .95}
        try:return super().evaluate(specs, context, timeout)
        finally:self.overrides=old


class StageRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.home=Path(self.temp.name);self.root=self.home/'episode'
        p=patch.object(rt,'_registry',return_value=self.home/'registry');p.start();self.addCleanup(p.stop)
        self.data=packet(count=2)
        self.data['issues'][0]['candidates']=['edsp'];self.data['issues'][1]['candidates']=['sra']
        self.data['dependencies']=[{'id':'P1','producer':'I1','consumer':'I2','artifact':'accepted bounded candidate structure',
                                    'condition':None,'refs':[rel.quote(self.data['documents'][0])]}]
        self.provider=AfterArtifactProvider();self.host=Executor()

    def invoke(self, **kw):
        return entry.run(self.root,self.provider,self.data,REPO,mode=rc.MODE,
                         executor=kw.pop('executor',self.host),artifact_acceptor=kw.pop('artifact_acceptor',Acceptor()),**kw)

    def test_accepted_predecessor_reopens_only_consumer(self):
        r=self.invoke();self.assertEqual(set(r['outputs']),{'I1','I2'});self.assertEqual(self.provider.batch_count,2)
        sp,ctx=self.provider.seen[1]
        self.assertTrue(all('.I2' in s.id for s in sp));self.assertTrue(all(s.id.split('.')[0]!='R04' for s in sp))
        self.assertEqual(ctx['original_documents'],self.data['documents'])
        self.assertEqual(ctx['artifact_view'][0]['text'],r['outputs']['I1']['text'])
        self.assertIn('not_independent_fact',ctx['artifact_view'][0]['provenance'])
        self.assertEqual(r['route']['revision'],2)
        self.assertEqual(r['outputs']['I1']['revision'],1);self.assertEqual(r['outputs']['I2']['revision'],2)

    def test_no_acceptance_no_new_judgment(self):
        r=self.invoke(artifact_acceptor=None)
        self.assertEqual(self.provider.batch_count,1);self.assertNotIn('I2',r['outputs'])

    def test_rejected_acceptance_no_new_judgment(self):
        class Reject(Acceptor):
            def accept(self,*args):return {**super().accept(*args),'accepted':False}
        r=self.invoke(artifact_acceptor=Reject());self.assertEqual(self.provider.batch_count,1);self.assertNotIn('I2',r['outputs'])

    def test_ready_consumer_does_not_need_redundant_recheck(self):
        self.provider=Provider();r=self.invoke()
        self.assertEqual(set(r['outputs']),{'I1','I2'});self.assertEqual(self.provider.batch_count,1)

    def test_still_uncertain_after_new_state_no_loop(self):
        self.provider=AfterArtifactProvider(remain_unresolved=True);r=self.invoke()
        self.assertEqual(self.provider.batch_count,2);self.assertEqual(self.host.calls,1);self.assertIn('I2',r['pending'])

    def test_same_episode_judgment_budget_applies(self):
        with patch.dict(rc.PROFILE,{'judgments_total':1,'judgments_per_turn':1}):r=self.invoke()
        self.assertEqual(self.provider.batch_count,1);self.assertEqual(set(r['outputs']),{'I1'})
        self.assertIn('budget_exhausted',r['reason'])

    def test_unaccepted_artifact_hash_rejected(self):
        class Bad(Acceptor):
            def accept(self,*args):return {**super().accept(*args),'artifact_sha256':'0'*64}
        with self.assertRaisesRegex(ContractError,'artifact_acceptance'):self.invoke(artifact_acceptor=Bad())
        self.assertEqual(self.provider.batch_count,1)

    def test_reentry_uses_both_completed_batches_and_outputs(self):
        first=self.invoke();before={str(p):p.read_bytes() for p in self.root.rglob('*.json')}
        again=self.invoke();self.assertEqual(first,again);self.assertEqual(self.provider.batch_count,2);self.assertEqual(self.host.calls,2)
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.root.rglob('*.json')})

    def test_invalid_score_allows_actual_executor_dispatch(self):
        self.data['dependencies']=[];self.data['issues']=self.data['issues'][:1]
        self.provider=Provider({'S02':DecisionResult('provider_error',reason='answer_contract:ContractError:weighted_rating/distribution_mismatch')})
        r=self.invoke();self.assertIn('I1',r['outputs']);self.assertEqual(r['route']['per_issue'][0]['attention'],{'status':'unknown'})

    def test_global_failure_still_stops_dispatch(self):
        self.provider=Provider({'S02':DecisionResult('provider_error',reason='ContractError:model_drift')})
        r=self.invoke();self.assertFalse(r['outputs']);self.assertEqual(self.host.calls,0)

    def test_resumes_current_agent_between_two_stages(self):
        host=CurrentAgentHost('original-host')
        for expected_iid in ('I1','I2'):
            result=self.invoke(executor=host);self.assertEqual(result['status'],'awaiting_current_agent')
            h=read_record(Path(result['host_request']));q=h['request'];self.assertEqual(q['issue']['issue_id'],expected_iid)
            reply={**h['reply_shape'],'performed_methods':q['execute_methods'],'text':'Fixture bounded '+expected_iid}
            submit_response(self.root,REPO,{'schema':'mindthus.current-host-response.v1','request_id':h['request_id'],
                'request_sha256':h['request_sha256'],'owner_ref':h['owner_ref'],'host_context_ref':'test-only-current-host',
                'elapsed_seconds':None,'reply':reply})
        result=self.invoke(executor=host)
        self.assertEqual(set(result['outputs']),{'I1','I2'});self.assertEqual(self.provider.batch_count,2)
        self.assertEqual(result['counts']['judgment'],2)
        self.assertFalse(result['pending_host_requests'])


if __name__=='__main__':unittest.main()
