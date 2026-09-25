"""Committed-route engineering controls. Injected observations are not model accuracy."""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from experiments.typed_decision import entry, route_control as rc, relationship_runtime as rt, relationship_assessment as rel
from experiments.typed_decision.contracts import ContractError, DecisionResult, digest
from experiments.typed_decision.providers import FixtureProvider
from experiments.typed_decision.session import RecoveryRequired, read_record, write_once
from experiments.typed_decision.route_control_host import CPARouteHost
from experiments.typed_decision.relationship_live import CPAHost
from tests.test_relationship_runtime import Hook, Provider as RelationProvider, display_packet
from tests.test_relationship_assessment import packet as relation_packet, DEFAULT

REPO = Path(__file__).resolve().parents[1]


def packet(candidates=('wae',), *, count=1, handling='judge', attention=True):
    docs = [{'id': 'U', 'kind': 'user', 'revision': '1', 'text': '请分析给定 Agent 的 schema 门为什么把结构齐全错误地当作事实已验证；先分析，不发布。'},
            {'id': 'S', 'kind': 'source', 'revision': '1', 'text': '门只检查字段存在。两个语义相反的结果均被放行，尚未分析职责归属。'}]
    auth = {'owner_ref': 'original-host', 'risk': 'low', 'mode': 'read_only', 'known_obligations': []}
    resolution = lambda value: {'value': value, 'owner_ref': auth['owner_ref'], 'revision': '1', 'refs': [rel.quote(docs[0])]}
    return {'schema': 'mindthus.route-control-input.v1', 'episode_id': 'route-test', 'turn_id': '1', 'revision': '1',
            'documents': docs, 'authority': auth,
            'issues': [{'id': 'I' + str(i+1), 'request_ref': rel.quote(docs[0]), 'candidates': list(candidates),
                        'handling': resolution(handling) if handling else None, 'assessability': resolution(True),
                        'attention': attention} for i in range(count)],
            'dependencies': [], 'relationship': None, 'task_budget': {'max_calls': 6, 'max_seconds': 180}}


class Provider(FixtureProvider):
    def __init__(self, overrides=None, *, corrected_overrides=None):
        self.overrides = {k: asdict(v) if isinstance(v, DecisionResult) else deepcopy(v) for k, v in (overrides or {}).items()}
        self.corrected_overrides = corrected_overrides or {}
        super().__init__(self.overrides)
        self.batch_count = 0; self.seen = []

    def evaluate(self, specs, context, timeout):
        self.batch_count += 1; self.seen.append((list(specs), deepcopy(context)))
        answers = {}
        for s in specs:
            t = s.id.split('.')[0]
            if 'proposal_view' in context:
                value = self.overrides.get(s.id, self.overrides.get(t, DEFAULT[t]))
                if context['proposal_view']['candidate']['ref']['document_id'].startswith('R'):
                    value = self.corrected_overrides.get(s.id, self.corrected_overrides.get(t, DEFAULT[t]))
            else:
                value = self.overrides.get(s.id, self.overrides.get(t, {
                    'M02': .95, 'M03': 'primary_candidate', 'G03': 'judge', 'R02': 'same_scope',
                    'R03': 'right', 'R04': 'needed_to_begin', 'M05': .95, 'S01': .95, 'S02': 2.0}.get(t)))
                if s.kind == 'rate' and not isinstance(value, (DecisionResult, dict)):
                    value = DecisionResult('ok', value, {'source': 'provider_distribution',
                           'probabilities': {'0': 0.0, '1': 0.0, '2': 1.0, '3': 0.0}, 'confidence': 1.0})
            answers[s.id] = asdict(value) if isinstance(value, DecisionResult) else value
        old = self.answers; self.answers = answers
        try: return super().evaluate(specs, context, timeout)
        finally: self.answers = old


class Executor:
    is_live = False
    identity = 'original-host'
    configuration = {'kind': 'offline_execution_fixture', 'version': '1'}
    def __init__(self, mutate=None, object_once=False):
        self.calls = 0; self.requests = []; self.mutate = mutate; self.object_once = object_once
    def execute(self, request, timeout):
        self.calls += 1; self.requests.append(deepcopy(request))
        reply = {'route_id': request['route_id'], 'revision': request['revision'],
                 'issue_id': request['issue']['issue_id'], 'performed_methods': request['execute_methods'],
                 'text': '按已提交职责完成有界分析；结构校验不证明事实，仍保留原任务权限与未知。',
                 'objection': None, 'usage': deepcopy(rt.UNKNOWN_USAGE)}
        if self.object_once and self.calls == 1:
            reply.update(text='', performed_methods=[], objection={
                'route_id': request['route_id'], 'revision': request['revision'],
                'affected_issue_or_step': reply['issue_id'], 'kind': 'method_boundary',
                'original_refs': [rel.quote(request['original_input']['documents'][0])],
                'claimed_conflict': '给定对象是控制门，应按控制归属处理，而不是仅优化表述。',
                'requested_change': '只修正此事项主方法为WAE。'})
        if self.mutate: self.mutate(reply, request)
        return reply


class Arbitrator:
    is_live = False
    identity = 'original-host:route-arbitrator'
    configuration = {'kind': 'isolated_arbitration_fixture', 'version': '1'}
    def __init__(self, decision='amend', mutate=None): self.calls=0; self.decision=decision; self.mutate=mutate
    def arbitrate(self, request, timeout):
        self.calls += 1
        result = {'route_id': request['route_id'], 'revision': request['revision'], 'issue_id': request['issue_id'],
                  'decision': self.decision, 'replacement': {'primary': 'wae', 'supports': [], 'constraints': []}
                  if self.decision == 'amend' else None,
                  'original_refs': [rel.quote(request['original_input']['documents'][0])],
                  'reason': '给定记录讨论语义证据的控制者，按此范围处理。', 'usage': deepcopy(rt.UNKNOWN_USAGE)}
        if self.mutate: self.mutate(result)
        return result


class Acceptor:
    identity = 'original-host'
    configuration = {'kind': 'host_owned_acceptance_fixture', 'version': '1'}
    def accept(self, edge, artifact, packet):
        return {'owner_ref': self.identity, 'dependency_id': edge['id'],
                'artifact_sha256': artifact['artifact_sha256'], 'accepted': True, 'source': 'test fixture, not semantic proof'}


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name); self.root = self.base / 'episode'
        self.patch = patch.object(rt, '_registry', return_value=self.base/'registry')
        self.patch.start(); self.addCleanup(self.patch.stop)
        self.data = packet(); self.provider = Provider(); self.host = Executor()
    def run_route(self, **kw):
        return entry.run(self.root, kw.pop('provider', self.provider), kw.pop('data', self.data), REPO,
                         mode=rc.MODE, executor=kw.pop('executor', self.host), **kw)
    def records(self): return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*.json')}
    def edge(self):
        return {'id': 'E1', 'producer': 'I1', 'consumer': 'I2', 'artifact': '控制边界结论',
                'condition': None, 'refs': [rel.quote(self.data['documents'][0])]}
    def test_public_entry_commits_loads_and_binds_execution(self):
        r=self.run_route(); self.assertEqual(r['route']['per_issue'][0]['primary'], 'wae')
        self.assertEqual(r['outputs']['I1']['methods'], ['wae']); self.assertEqual(self.host.calls,1)
        self.assertEqual(self.host.requests[0]['loaded_methods']['wae']['content'], (REPO/'skills/wae/SKILL.md').read_text())
        self.assertEqual(r['counts']['judgment'],1); self.assertEqual(r['counts']['execution'],1)
        self.assertFalse(r['task_complete']); self.assertEqual(r['native_plugin_activation'],'not_claimed')
    def test_mixed_three_types_share_one_batch(self):
        self.run_route(); self.assertEqual(self.provider.batch_count,1)
        self.assertEqual({s.kind for s in self.provider.seen[0][0]}, {'select','rate','assess_proposition'})
    def test_multi_method_support_not_forced_single(self):
        self.data=packet(('sela','mpg'))
        self.provider=Provider({'M03.I1.sela':'support'})
        r=self.run_route(); row=r['route']['per_issue'][0]
        self.assertEqual(row['primary'],'mpg');self.assertEqual(row['supports'],['sela'])
        self.assertEqual(r['outputs']['I1']['methods'],['mpg','sela'])
    def test_companion_is_actually_loaded_even_if_not_selected(self):
        self.data=packet(('mpg',));r=self.run_route()
        self.assertIn('sela',r['route']['mandatory_reads']);self.assertIn('sela',self.host.requests[0]['loaded_methods'])
    def test_missing_companion_signal_not_silently_waived(self):
        self.data=packet(('mpg',));self.provider=Provider({'M05': .5})
        r=self.run_route();self.assertEqual(self.host.calls,0);self.assertEqual(r['route']['per_issue'][0]['mode'],'delegated_unresolved')
    def test_independent_issues_keep_separate_primaries(self):
        self.data=packet(count=2);self.data['issues'][1]['candidates']=['tvg']
        r=self.run_route();self.assertEqual([x['primary'] for x in r['route']['per_issue']], ['wae','tvg'])
        self.assertEqual(len(r['outputs']),2)
    def test_partial_does_not_erase_unrelated_ready_issue(self):
        self.data=packet(count=2);self.provider=Provider({'M02.I2.wae': .5})
        r=self.run_route();self.assertIn('I1',r['outputs']);self.assertIn('I2',r['pending'])
        row=r['route']['per_issue'][1];self.assertIsNone(row['primary']);self.assertEqual(row['supports'],[])
    def test_unknown_score_is_not_zero_and_does_not_block_route(self):
        self.provider=Provider({'S02':DecisionResult('ok', 1.5)})
        r=self.run_route();self.assertEqual(r['route']['per_issue'][0]['attention'], {'status':'unknown'})
        self.assertIn('I1',r['outputs'])
    def test_unassessable_score_does_not_get_consumed(self):
        self.data['issues'][0]['assessability']['value']=False
        r=self.run_route();self.assertEqual(r['route']['per_issue'][0]['attention']['status'],'unknown')
    def test_native_score_is_guidance_not_route_winner(self):
        r=self.run_route();self.assertEqual(r['route']['per_issue'][0]['attention']['status'],'guidance_only')
    def test_explicit_direct_task_has_no_model_judgment(self):
        self.data=packet((),handling='direct_execute',attention=False)
        r=self.run_route();self.assertEqual(self.provider.batch_count,0);self.assertEqual(r['outputs']['I1']['methods'],[])
    def test_information_acquisition_has_no_method_execution(self):
        self.data=packet((),handling='acquire_fact',attention=False)
        r=self.run_route();self.assertEqual(self.host.calls,0);self.assertEqual(r['route']['per_issue'][0]['mode'],'acquire')
    def test_uncertain_handling_uses_actual_G03(self):
        self.data=packet(handling=None);r=self.run_route();self.assertIn('G03.I1',r['route']['source_observations'])
    def test_no_candidates_is_not_fake_unique_owner(self):
        self.data=packet((),attention=False);r=self.run_route();self.assertEqual(self.host.calls,0)
        self.assertIn('no_established_primary',r['pending']['I1'])
    def test_support_alone_cannot_invent_primary(self):
        self.provider=Provider({'M03':'support'});r=self.run_route();self.assertEqual(self.host.calls,0)
    def test_pairwise_winner_does_not_turn_loser_into_support(self):
        self.data=packet(('wae','tvg'));r=self.run_route();row=r['route']['per_issue'][0]
        self.assertEqual(row['primary'],'tvg');self.assertEqual(row['supports'],[])
    def test_disjoint_scopes_in_one_raw_issue_need_split_not_vote(self):
        self.data=packet(('wae','tvg'));self.provider=Provider({'R02':'disjoint_scopes'})
        r=self.run_route();self.assertEqual(self.host.calls,0)
    def test_silent_method_switch_is_not_accepted(self):
        self.host=Executor(mutate=lambda r,q:r.update(performed_methods=['edsp']))
        r=self.run_route();self.assertNotIn('I1',r['outputs']);self.assertIn('execution_failed',r['pending']['I1'])
    def test_stale_execution_revision_is_rejected(self):
        self.host=Executor(mutate=lambda r,q:r.update(revision=99));r=self.run_route();self.assertFalse(r['outputs'])
    def test_objector_cannot_self_approve(self):
        self.host.identity='original-host:route-arbitrator'
        with self.assertRaises(ContractError):self.run_route(arbitrator=self.host)
    def test_named_objection_is_locally_amended_by_separate_hook(self):
        self.data=packet(('tvg','wae'),count=2)
        self.provider=Provider({'R03':'left'});self.host=Executor(object_once=True);arb=Arbitrator()
        r=self.run_route(arbitrator=arb)
        self.assertEqual(r['route']['revision'],2);self.assertEqual(arb.calls,1)
        self.assertEqual(r['route']['per_issue'][0]['primary'],'wae')
        self.assertEqual(r['route']['per_issue'][1]['primary'],'tvg')
        self.assertEqual(r['counts']['arbitration'],1);self.assertEqual(r['counts']['execution'],3)
    def test_uphold_can_retry_executor_once_not_infinite(self):
        self.host=Executor(object_once=True);r=self.run_route(arbitrator=Arbitrator('uphold'))
        self.assertEqual(self.host.calls,2);self.assertIn('I1',r['outputs'])
    def test_unsupported_objection_is_not_override(self):
        self.host=Executor(object_once=True, mutate=lambda r,q:r['objection'].update(original_refs=[]) if r['objection'] else None)
        arb=Arbitrator();r=self.run_route(arbitrator=arb);self.assertEqual(arb.calls,0);self.assertEqual(r['route']['revision'],1)
    def test_arbitration_cannot_change_unrelated_scope(self):
        self.host=Executor(object_once=True);arb=Arbitrator(mutate=lambda r:r.update(issue_id='OTHER'))
        r=self.run_route(arbitrator=arb);self.assertEqual(r['route']['revision'],1)
    def test_arbitration_cannot_invent_new_candidate_method(self):
        self.host=Executor(object_once=True);arb=Arbitrator(mutate=lambda r:r['replacement'].update(primary='mpg'))
        r=self.run_route(arbitrator=arb);self.assertEqual(r['route']['revision'],1)
    def test_dependency_waits_for_host_acceptance_not_self_report(self):
        self.data=packet(count=2);self.data['dependencies']=[self.edge()]
        r=self.run_route();self.assertIn('I1',r['outputs']);self.assertNotIn('I2',r['outputs'])
    def test_actual_accepted_output_releases_consumer(self):
        self.data=packet(count=2);self.data['dependencies']=[self.edge()]
        r=self.run_route(artifact_acceptor=Acceptor());self.assertEqual(len(r['outputs']),2)
        self.assertIn('I1',self.host.requests[1]['prior_outputs'])
    def test_dependency_cycle_does_not_randomly_execute(self):
        self.data=packet(count=2);edge=self.edge();self.data['dependencies']=[edge,{**edge,'id':'E2','producer':'I2','consumer':'I1'}]
        r=self.run_route(artifact_acceptor=Acceptor());self.assertEqual(self.host.calls,0)
    def test_completed_reentry_zero_new_calls_and_unchanged_records(self):
        first=self.run_route();saved=self.records();second=self.run_route()
        self.assertEqual(first,second);self.assertEqual(self.provider.batch_count,1);self.assertEqual(self.host.calls,1)
        self.assertEqual(saved,self.records())
    def test_execution_outcome_recovered_without_resubmitting(self):
        self.run_route()
        for p in self.root.glob('turns/*/inputs/*/summary.json'):p.unlink()
        self.run_route();self.assertEqual(self.host.calls,1);self.assertEqual(self.provider.batch_count,1)
    def test_unknown_execution_intent_not_repeated(self):
        self.run_route()
        for p in self.root.glob('turns/*/inputs/*/steps/execution__*/outcome.json'):p.unlink()
        with self.assertRaises(RecoveryRequired):self.run_route()
        self.assertEqual(self.host.calls,1)
    def test_unknown_judgment_intent_not_repeated(self):
        self.run_route()
        for p in self.root.glob('turns/*/inputs/*/steps/route/calls/*/outcome.json'):p.unlink()
        with self.assertRaises(RecoveryRequired):self.run_route()
        self.assertEqual(self.provider.batch_count,1)
    def test_episode_cannot_move_root_to_reset_budget(self):
        self.run_route();self.root=self.base/'different'
        with self.assertRaisesRegex(ContractError,'episode_root_changed'):self.run_route()
    def test_budget_is_not_reset_by_new_turn(self):
        self.data['task_budget']['max_calls']=1;self.run_route();d=deepcopy(self.data);d['turn_id']='2'
        r=self.run_route(data=d);self.assertEqual(self.host.calls,1);self.assertIn('budget_exhausted',r['reason'])
    def test_high_risk_is_returned_without_models(self):
        self.data['authority']['risk']='high';r=self.run_route();self.assertEqual(self.provider.batch_count,0);self.assertEqual(self.host.calls,0)
    def test_authority_and_original_documents_survive(self):
        self.data['authority']['known_obligations']=['发布仍需Owner批准'];r=self.run_route()
        self.assertEqual(r['original_input'],self.data)
        self.assertEqual(self.host.requests[0]['authority'],self.data['authority'])
    def test_wrong_ref_rejected_before_network(self):
        self.data['issues'][0]['request_ref']['sha256']='0'*64
        with self.assertRaises(ContractError):self.run_route()
        self.assertEqual(self.provider.batch_count,0)
    def test_old_public_route_option_cannot_stack(self):
        with self.assertRaisesRegex(ContractError,'public_modes_exclusive'):self.run_route(route=True)
    def test_other_modes_reject_new_executor(self):
        with self.assertRaisesRegex(ContractError,'options_on_legacy_mode'):
            entry.run(self.root,self.provider,self.data,REPO,mode='relationship-frame.v1',executor=self.host)
    def test_missing_live_admission_rejected(self):
        self.provider.is_live=True
        with self.assertRaisesRegex(ContractError,'live_not_admitted'):self.run_route()
    def test_relationship_uses_same_episode_budget_and_existing_corrector(self):
        r=relation_packet(candidate='范围只谈Skills，本质仍然只是提示词。')
        d=packet();d.update(episode_id=r['episode_id'],turn_id=r['turn_id'],revision=r['revision'],documents=r['documents'],authority=r['authority'],relationship=r)
        d['issues'][0]['request_ref']=rel.quote(r['documents'][0])
        for key in ('handling','assessability'):
            d['issues'][0][key].update(owner_ref=r['authority']['owner_ref'],revision=r['revision'],refs=[rel.quote(r['documents'][0])])
        self.data=d;self.provider=Provider({'definition':'carrier_only_unjustified'})
        result=self.run_route(corrector=Hook())
        self.assertEqual(result['counts']['judgment'],3);self.assertEqual(result['counts']['correction'],1)
        self.assertIsNotNone(result['relationship']['revised']);self.assertEqual(result['original_input'],d)
        manifests=list(self.root.glob('manifest.json'));self.assertEqual(len(manifests),1)
    def test_display_correction_not_hardcoded_winner(self):
        r=display_packet();d=packet();d.update(episode_id=r['episode_id'],turn_id=r['turn_id'],revision=r['revision'],documents=r['documents'],authority=r['authority'],relationship=r)
        d['issues'][0]['request_ref']=rel.quote(r['documents'][0]);d['issues'][0]['handling']=None;d['issues'][0]['assessability']=None
        self.data=d;self.provider=Provider({'delivery':'list_only'})
        result=self.run_route(corrector=Hook(text='就当前已有设备的使用目标给出判断，同时保留物理限制；不预设购买某种设备。'))
        self.assertIsNotNone(result['relationship']['revised']);self.assertEqual(result['counts']['correction'],1)


    def test_source_bound_covered_result_is_reused_not_reanalyzed(self):
        self.data['issues'][0]['coverage']={'wae':deepcopy(self.data['issues'][0]['assessability'])}
        self.provider=Provider({'M03':'covered'})
        r=self.run_route();self.assertEqual(r['route']['per_issue'][0]['mode'],'direct')
        self.assertEqual(r['outputs']['I1']['methods'],[]);self.assertEqual(len(r['route']['reuse']),1)
    def test_covered_without_source_does_not_drop_required_work(self):
        self.provider=Provider({'M03':'covered'});r=self.run_route();self.assertFalse(r['outputs'])
        self.assertIn('coverage_needs_existing_output',r['pending']['I1'])
    def test_partial_parent_is_explicit(self):
        self.data=packet(count=2);self.provider=Provider({'M02.I2.wae': .5})
        r=self.run_route();self.assertEqual(r['route']['mode'],'partial')
    def test_unresolved_relationship_is_not_ignored(self):
        rp=relation_packet();d=packet();d.update(episode_id=rp['episode_id'],turn_id=rp['turn_id'],revision=rp['revision'],
            documents=rp['documents'],authority=rp['authority'],relationship=rp)
        d['issues'][0]['request_ref']=rel.quote(rp['documents'][0]);d['issues'][0]['handling']=None;d['issues'][0]['assessability']=None
        self.data=d;self.provider=Provider({'q0':'unsupported_mapping'})
        r=self.run_route();self.assertFalse(r['outputs']);self.assertIn('relationship_scope_unresolved',r['pending']['I1'])

    def relation_issues(self, count=2, affected='I1'):
        rp = relation_packet(candidate='只谈该 Skills，因此一定只是提示词。')
        data = packet(count=count)
        data.update(episode_id=rp['episode_id'], turn_id=rp['turn_id'], revision=rp['revision'],
                    documents=rp['documents'], authority=rp['authority'], relationship=rp,
                    relationship_issue=affected)
        for issue in data['issues']:
            issue.update(request_ref=rel.quote(rp['documents'][0]), handling=None, assessability=None)
        return data

    def test_recheck_still_requests_correction_keeps_scope_pending(self):
        self.data = self.relation_issues()
        self.provider = Provider({'definition': 'carrier_only_unjustified'},
                                 corrected_overrides={'definition': 'account_missing'})
        corrector = Hook()
        result = self.run_route(corrector=corrector)
        self.assertEqual(result['relationship']['recheck']['result']['action'], 'request_correction')
        self.assertEqual(set(result['outputs']), {'I2'})
        self.assertEqual(result['pending']['I1'], 'relationship_correction_unresolved')
        self.assertEqual(corrector.calls, 1)
        self.assertEqual(result['counts']['judgment'], 3)
        saved = self.records()
        self.assertEqual(self.run_route(corrector=corrector), result)
        self.assertEqual(self.records(), saved)
        self.assertEqual(corrector.calls, 1)

    def test_unverified_correction_is_not_consumed_as_cleared(self):
        self.data = self.relation_issues()
        self.provider = Provider({'definition': 'carrier_only_unjustified'})
        result = self.run_route(corrector=Hook(), recheck=False)
        self.assertIsNone(result['relationship']['recheck'])
        self.assertEqual(set(result['outputs']), {'I2'})
        self.assertEqual(result['pending']['I1'], 'relationship_correction_unverified')
        self.assertEqual(result['counts']['judgment'], 2)

    def test_accepted_predecessor_does_not_clear_unresolved_correction(self):
        self.data = self.relation_issues(affected='I2')
        self.data['dependencies'] = [self.edge()]
        self.provider = Provider({'definition': 'carrier_only_unjustified'},
                                 corrected_overrides={'definition': 'account_missing'})
        result = self.run_route(corrector=Hook(), artifact_acceptor=Acceptor())
        self.assertEqual(set(result['outputs']), {'I1'})
        self.assertTrue(result['outputs']['I1']['accepted_uses']['E1']['accepted'])
        self.assertEqual(result['pending']['I2'], 'relationship_correction_unresolved')
        self.assertEqual(result['counts']['judgment'], 3)
        self.assertNotIn('post_artifact_evaluations', result['route'])

    def test_accepted_predecessor_does_not_clear_relationship_return(self):
        self.data = self.relation_issues(affected='I2')
        self.data['dependencies'] = [self.edge()]
        self.provider = Provider({'q0': 'unsupported_mapping'})
        result = self.run_route(artifact_acceptor=Acceptor())
        self.assertEqual(set(result['outputs']), {'I1'})
        self.assertEqual(result['pending']['I2'], 'relationship_scope_unresolved')
        self.assertEqual(result['counts']['judgment'], 2)
    def test_public_cli_fixture_runs_new_mode_and_replays(self):
        import subprocess
        path=REPO/'experiments/typed_decision/fixtures/route-control.json'
        value=json.loads(path.read_text());value['input']['episode_id']='cli-'+self.base.name
        fp=self.base/'fixture.json';fp.write_text(json.dumps(value))
        command=['python3','-m','experiments.typed_decision.entry','--mode',rc.MODE,
                 '--fixture',str(fp),'--state-root',str(self.root),'--host','fixture']
        env=dict(__import__('os').environ,HOME=str(self.base))
        a=subprocess.run(command,cwd=REPO,env=env,text=True,capture_output=True,check=True)
        b=subprocess.run(command,cwd=REPO,env=env,text=True,capture_output=True,check=True)
        self.assertEqual(json.loads(a.stdout),json.loads(b.stdout))
        self.assertEqual(json.loads(a.stdout)['outputs']['I1']['methods'],['wae'])


class MaxConfigurationTests(unittest.TestCase):
    def test_every_new_CPA_role_requests_max_and_enabled_thinking(self):
        for hook in (CPAHost('host',REPO),CPAHost('host',REPO,organizer=True),
                     CPARouteHost('host',REPO),CPARouteHost('host',REPO,arbitrator=True)):
            self.assertEqual(hook.configuration['reasoning_effort'],'max')
            self.assertEqual(hook.configuration['thinking'],{'type':'enabled'})
    def test_route_wire_body_binds_max_not_temperature_as_reasoning(self):
        hook=CPARouteHost('host',REPO);body=hook.wire_body({'route_id':'r','original_input':{},'relationship':None})
        self.assertEqual(body['reasoning_effort'],'max');self.assertEqual(body['thinking'],{'type':'enabled'})
        self.assertEqual(body['model'],'deepseek-v4.1-flash')
    def test_prompt_is_instruction_and_original_input_remains_data(self):
        body=CPARouteHost('host',REPO).wire_body({'original_input':{'text':'data'},'relationship':None})
        self.assertEqual(body['messages'][0]['role'],'system');self.assertIn('not factual evidence',body['messages'][0]['content'])
    def test_correction_wire_contains_max(self):
        h=CPAHost('host',REPO,organizer=True)
        body=h.wire_body({'original_input':{}})
        self.assertEqual(body['reasoning_effort'],'max')


if __name__=='__main__':unittest.main()
