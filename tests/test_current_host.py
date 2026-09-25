"""Current-Agent handoff tests. Judgment/text fixtures are not live accuracy evidence."""
from copy import deepcopy
from pathlib import Path
import json
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from experiments.typed_decision import entry, route_control as rc, relationship_runtime as rt
from experiments.typed_decision.current_host import CurrentAgentHost, submit_response
from experiments.typed_decision.contracts import ContractError, digest, provider_configuration
from experiments.typed_decision.session import RecoveryRequired, read_record, implementation_digest
from tests.test_route_control import Provider, Executor, Arbitrator, Acceptor, packet
from tests.test_relationship_runtime import Hook, display_packet
from tests.test_relationship_assessment import packet as relationship_packet
from experiments.typed_decision import relationship_assessment as rel

REPO = Path(__file__).resolve().parents[1]


class CurrentHostTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name); self.root = self.base / 'episode'
        p = patch.object(rt, '_registry', return_value=self.base/'registry')
        p.start(); self.addCleanup(p.stop)
        p = patch.dict(os.environ, {k:'' for k in ('MINDTHUS_HOST_API_KEY', 'TYPESAFE_API_KEY', 'OPENROUTER_API_KEY')})
        p.start(); self.addCleanup(p.stop)
        self.data = packet(); self.provider = Provider()
        self.owner = self.data['authority']['owner_ref']
        self.hooks = {'executor': CurrentAgentHost(self.owner),
                      'corrector': CurrentAgentHost(self.owner, role='correction'),
                      'arbitrator': CurrentAgentHost(self.owner, role='arbitration')}

    def run_entry(self, **kw):
        return entry.run(self.root, kw.pop('provider', self.provider), kw.pop('data', self.data), REPO,
                         mode=rc.MODE, **self.hooks, **kw)

    def handoff(self, result):
        self.assertEqual(result['status'], 'awaiting_current_agent')
        return read_record(Path(result['host_request']))

    def submission(self, h, reply=None, context='test-executor-context', elapsed=1.0):
        return {'schema':'mindthus.current-host-response.v1', 'request_id':h['request_id'],
                'request_sha256':h['request_sha256'], 'owner_ref':h['owner_ref'],
                'host_context_ref':context, 'elapsed_seconds':elapsed,
                'reply':reply if reply is not None else Executor().execute(h['request'],45)}

    def submit(self, h, **kw):
        return submit_response(self.root, REPO, self.submission(h, **kw))

    def records(self):
        return {str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*.json')}

    def test_waiting_loads_methods_without_any_CPA_key(self):
        r=self.run_entry(); h=self.handoff(r)
        self.assertEqual(h['role'],'execution'); self.assertEqual(r['counts']['execution'],0)
        self.assertEqual(r['reserved_counts']['execution'],1)
        self.assertEqual(h['request']['execute_methods'],['wae'])
        self.assertEqual(h['request']['loaded_methods']['wae']['content'],(REPO/'skills/wae/SKILL.md').read_text())
        self.assertFalse(list(self.root.rglob('summary.json')))
        self.assertEqual(self.provider.batch_count,1)

    def test_same_pending_request_reentry_does_not_repeat_or_change_it(self):
        a=self.run_entry(); old=self.records(); b=self.run_entry()
        self.assertEqual(a,b); self.assertEqual(old,self.records()); self.assertEqual(self.provider.batch_count,1)

    def test_response_completes_original_route_and_is_idempotent(self):
        h=self.handoff(self.run_entry()); self.submit(h)
        a=self.run_entry(); old=self.records(); b=self.run_entry()
        self.assertEqual(a,b); self.assertEqual(old,self.records()); self.assertEqual(self.provider.batch_count,1)
        self.assertEqual(a['outputs']['I1']['methods'],['wae'])
        self.assertEqual(a['counts']['execution'],1); self.assertFalse(a['pending_host_requests'])
        self.assertFalse(a['task_complete']); self.assertFalse(a['qualification'])
        out=read_record(next(self.root.glob('turns/*/inputs/*/steps/execution*/outcome.json')))
        self.assertEqual(out['host_evidence_kind'],'current_agent_submission')
        self.assertEqual(out['external_llm_requests'],0)

    def test_bad_method_receipt_rejected_without_poisoning_pending(self):
        h=self.handoff(self.run_entry()); s=self.submission(h); s['reply']['performed_methods']=['tvg']
        with self.assertRaisesRegex(ContractError,'silent_route_override'): submit_response(self.root,REPO,s)
        self.assertFalse(list(self.root.rglob('host-response.json')))
        self.submit(h); self.assertIn('I1',self.run_entry()['outputs'])

    def test_stale_route_revision_is_rejected(self):
        h=self.handoff(self.run_entry()); s=self.submission(h); s['reply']['revision']+=1
        with self.assertRaisesRegex(ContractError,'execution_route_revision'): submit_response(self.root,REPO,s)

    def test_hash_and_owner_binding_rejected(self):
        h=self.handoff(self.run_entry())
        for key,value in [('request_sha256','0'*64),('owner_ref','other')]:
            s=self.submission(h); s[key]=value
            with self.assertRaisesRegex(ContractError,'binding_mismatch'): submit_response(self.root,REPO,s)

    def test_response_unknown_request_rejected(self):
        h=self.handoff(self.run_entry()); s=self.submission(h); s['request_id']='0'*64
        with self.assertRaisesRegex(ContractError,'not_unique_or_absent'): submit_response(self.root,REPO,s)

    def test_accepted_response_is_immutable(self):
        h=self.handoff(self.run_entry()); self.submit(h); self.submit(h)
        s=self.submission(h); s['reply']['text']='changed'
        with self.assertRaisesRegex(ContractError,'response_immutable'): submit_response(self.root,REPO,s)

    def test_pending_input_cannot_be_abandoned_to_reset_budget(self):
        self.run_entry(); d=deepcopy(self.data); d['turn_id']='2'
        with self.assertRaisesRegex(ContractError,'pending_current_host_input'): self.run_entry(data=d)
        self.assertEqual(self.provider.batch_count,1)

    def test_pending_root_cannot_be_relocated(self):
        self.run_entry(); self.root=self.base/'other'
        with self.assertRaisesRegex(ContractError,'episode_root_changed'): self.run_entry()

    def test_new_episode_can_complete_in_another_state_root(self):
        first = self.handoff(self.run_entry()); self.submit(first)
        completed = self.run_entry()
        first_root = self.root
        self.root = self.base / 'another-host-root'
        self.data = deepcopy(self.data)
        self.data['episode_id'] += '-new'
        self.provider = Provider()
        second = self.handoff(self.run_entry()); self.submit(second)
        next_completed = self.run_entry()
        self.assertEqual(completed['counts']['execution'], 1)
        self.assertEqual(next_completed['counts']['execution'], 1)
        self.assertNotEqual(first['request_id'], second['request_id'])
        self.assertTrue((first_root / 'manifest.json').exists())
        self.assertTrue((self.root / 'manifest.json').exists())

    def test_pending_host_configuration_is_bound(self):
        self.run_entry(); self.hooks['executor'].configuration['adapter']='changed'
        with self.assertRaises(ContractError):self.run_entry()

    def test_missing_host_handoff_can_be_rebuilt_from_intent_without_invocation(self):
        r=self.run_entry(); hp=Path(r['host_request']); before=hp.read_bytes(); hp.unlink()
        self.run_entry(); self.assertEqual(hp.read_bytes(),before); self.assertEqual(self.provider.batch_count,1)

    def test_unknown_provider_intent_remains_non_resendable(self):
        self.run_entry(); op=next(self.root.glob('turns/*/inputs/*/steps/route/calls/*/outcome.json'));op.unlink()
        with self.assertRaises(RecoveryRequired):self.run_entry()
        self.assertEqual(self.provider.batch_count,1)

    def test_unknown_elapsed_is_not_faked_as_measured_or_free(self):
        h=self.handoff(self.run_entry());self.submit(h,elapsed=None);r=self.run_entry()
        out=read_record(next(self.root.glob('turns/*/inputs/*/steps/execution*/outcome.json')))
        self.assertIsNone(out['reported_elapsed_seconds']);self.assertIsNone(out['usage']['cost_usd'])
        self.assertEqual(out['elapsed_basis'],'reserved_ceiling_actual_unknown')
        self.assertEqual(r['method_request_seconds'],h['allowance_seconds'])

    def test_late_report_cannot_exceed_reserved_allowance(self):
        h=self.handoff(self.run_entry())
        with self.assertRaisesRegex(ContractError,'elapsed_exceeds'):self.submit(h,elapsed=46)

    def test_waiting_does_not_mean_host_was_executed(self):
        self.data['task_budget']['max_calls']=1
        h=self.handoff(self.run_entry());self.run_entry();self.submit(h)
        r=self.run_entry();self.assertEqual(r['counts']['execution'],1)
        d=deepcopy(self.data);d['turn_id']='2';r=self.run_entry(data=d)
        self.assertIn('budget_exhausted',r['reason']);self.assertEqual(r['counts']['execution'],1)

    def test_multi_method_support_survives_current_host_dispatch(self):
        self.data=packet(('sela','mpg'));self.provider=Provider({'M03.I1.sela':'support'})
        h=self.handoff(self.run_entry());self.assertEqual(h['request']['execute_methods'],['mpg','sela'])
        self.submit(h);r=self.run_entry();self.assertEqual(r['route']['per_issue'][0]['primary'],'mpg')
        self.assertEqual(r['route']['per_issue'][0]['supports'],['sela'])

    def test_local_unresolved_does_not_erase_completed_work(self):
        self.data=packet(count=2);self.provider=Provider({'M02.I2.wae':.5})
        h=self.handoff(self.run_entry());self.submit(h);r=self.run_entry()
        self.assertIn('I1',r['outputs']);self.assertIn('I2',r['pending'])

    def test_current_host_dependency_waits_for_original_host_acceptance(self):
        self.data=packet(count=2)
        self.data['dependencies']=[{'id':'D1','producer':'I1','consumer':'I2','artifact':'控制边界分析',
            'condition':None,'refs':[rel.quote(self.data['documents'][0])]}]
        h=self.handoff(self.run_entry(artifact_acceptor=Acceptor()));self.submit(h)
        second=self.handoff(self.run_entry(artifact_acceptor=Acceptor()))
        self.assertEqual(second['request']['issue']['issue_id'],'I2')
        self.assertIn('I1',second['request']['prior_outputs'])
        self.submit(second);r=self.run_entry(artifact_acceptor=Acceptor())
        self.assertEqual(set(r['outputs']),{'I1','I2'});self.assertEqual(self.provider.batch_count,1)

    def test_named_objection_requires_different_host_context(self):
        h=self.handoff(self.run_entry());self.submit(h,reply=Executor(object_once=True).execute(h['request'],45))
        a=self.handoff(self.run_entry());self.assertEqual(a['role'],'arbitration')
        reply=Arbitrator('uphold').arbitrate(a['request'],45)
        with self.assertRaisesRegex(ContractError,'independent_arbitration_context'):self.submit(a,reply=reply)
        self.submit(a,reply=reply,context='test-separate-arbitration-context')
        e=self.handoff(self.run_entry());self.assertEqual(e['request']['revision'],2)
        self.submit(e);r=self.run_entry();self.assertIn('I1',r['outputs'])
        self.assertEqual(r['counts']['arbitration'],1);self.assertEqual(self.provider.batch_count,1)

    def test_no_basis_objection_cannot_override(self):
        h=self.handoff(self.run_entry());s=self.submission(h,reply=Executor(object_once=True).execute(h['request'],45))
        s['reply']['objection']['original_refs']=[]
        with self.assertRaisesRegex(ContractError,'objection_evidence'):submit_response(self.root,REPO,s)

    def _relationship(self, display=False):
        r=display_packet() if display else relationship_packet(candidate='范围只谈Skills，本质仍然只是提示词。')
        self.data.update(episode_id=r['episode_id'],turn_id=r['turn_id'],revision=r['revision'],documents=r['documents'],authority=r['authority'],relationship=r)
        self.data['issues'][0]['request_ref']=rel.quote(r['documents'][0])
        for key in ('handling','assessability'):
            self.data['issues'][0][key].update(owner_ref=r['authority']['owner_ref'],revision=r['revision'],refs=[rel.quote(r['documents'][0])])
        self.provider=Provider({'delivery':'list_only'} if display else {'definition':'carrier_only_unjustified'})

    def test_skills_correction_and_recheck_share_the_route_episode(self):
        self._relationship();h=self.handoff(self.run_entry());self.assertEqual(h['role'],'correction')
        self.submit(h,reply=Hook().correct(h['request'],45))
        e=self.handoff(self.run_entry());self.assertEqual(e['role'],'execution');self.submit(e)
        r=self.run_entry();self.assertEqual(r['counts']['correction'],1);self.assertEqual(r['counts']['judgment'],3)
        self.assertEqual(r['original_input'],self.data);self.assertIsNotNone(r['relationship']['revised'])

    def test_display_correction_uses_same_host_without_CPA(self):
        self._relationship(display=True);h=self.handoff(self.run_entry());self.assertEqual(h['role'],'correction')
        self.submit(h,reply=Hook(text='按当前处境判断补救价值，物理限制仍保留，不改成购买建议。').correct(h['request'],45))
        e=self.handoff(self.run_entry());self.submit(e);r=self.run_entry()
        self.assertEqual(r['counts']['correction'],1);self.assertIn('I1',r['outputs'])

    def test_correction_cannot_rewrite_original_source(self):
        self._relationship();h=self.handoff(self.run_entry());reply=Hook().correct(h['request'],45)
        reply['proposal']['frames'][0]['object']['text']='changed object'
        with self.assertRaises(ContractError):self.submit(h,reply=reply)

    def test_live_decision_provider_accepts_local_host_without_external_llm(self):
        # The decision provider below is a TEST DOUBLE, not a real live API call.
        self.provider.is_live=True
        bundle,_,_=rc.load_policy(REPO)
        admission={'schema':'mindthus.route-control-live.v1','mode':rc.MODE,'root':str(self.root),
            'implementation':implementation_digest(),'source_bindings':bundle['sources'],
            'provider':provider_configuration(self.provider),'packet_hashes':[digest(self.data)],
            'authorization_ref':'test double only', 'organizer':None,
            **{k:h.configuration for k,h in self.hooks.items()},
            'ceilings':{'judgments':1,'corrections':0,'organize':0,'arbitrations':0,'requests':1,'executions':1,'reserve_per_jev_usd':.01}}
        h=self.handoff(self.run_entry(live_admission=admission));self.submit(h)
        self.assertIn('I1',self.run_entry(live_admission=admission)['outputs'])

    def test_CPA_is_never_constructed_in_default_CLI(self):
        fp=self.base/'fixture.json';value=json.loads((REPO/'experiments/typed_decision/fixtures/route-control.json').read_text())
        value['input']['episode_id']='cli-current-'+self.base.name;fp.write_text(json.dumps(value))
        import contextlib,io
        out=io.StringIO()
        with patch('experiments.typed_decision.route_control_host.CPARouteHost',side_effect=AssertionError('must not construct CPA')),contextlib.redirect_stdout(out):
            code=entry.main(['--mode',rc.MODE,'--fixture',str(fp),'--state-root',str(self.root)])
        self.assertEqual(code,0);self.handoff(json.loads(out.getvalue()))

    def test_CLI_default_exports_then_consumes_response(self):
        fp=self.base/'fixture.json';value=json.loads((REPO/'experiments/typed_decision/fixtures/route-control.json').read_text())
        value['input']['episode_id']='cli-current-'+self.base.name;fp.write_text(json.dumps(value))
        cmd=['python3','-m','experiments.typed_decision.entry','--mode',rc.MODE,'--fixture',str(fp),'--state-root',str(self.root)]
        env=dict(os.environ,HOME=str(self.base))
        run=lambda args:subprocess.run(args,cwd=REPO,env=env,text=True,capture_output=True,check=True)
        h=self.handoff(json.loads(run(cmd).stdout));rp=self.base/'reply.json';rp.write_text(json.dumps(self.submission(h)))
        r=json.loads(run(cmd+['--host-response',str(rp)]).stdout);self.assertIn('I1',r['outputs'])
        self.assertEqual(r,json.loads(run(cmd).stdout))

    def test_CPA_cannot_be_selected_for_unadmitted_fixture_execution(self):
        import contextlib,io
        out=io.StringIO()
        with contextlib.redirect_stdout(out):
            code=entry.main(['--mode',rc.MODE,'--fixture',str(REPO/'experiments/typed_decision/fixtures/route-control.json'),
                             '--state-root',str(self.root),'--host','cpa'])
        self.assertEqual(code,2);self.assertFalse((self.root/'manifest.json').exists())


if __name__=='__main__':unittest.main()
