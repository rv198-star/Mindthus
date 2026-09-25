"""v0.3 public-entry counterexamples; all judgments and host texts are synthetic fixtures."""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import tempfile
import unittest
import json
import subprocess
import sys
from unittest.mock import patch

from experiments.typed_decision import entry, route_control_v03 as v03, source_direct_v03 as sd
from experiments.typed_decision import relationship_runtime as rt, relationship_assessment as rel
from experiments.typed_decision.current_host import CurrentAgentHost, submit_response
from experiments.typed_decision.contracts import ContractError, DecisionResult, digest
from experiments.typed_decision.session import read_record
from tests.test_route_control import packet as old_packet, Provider as OldProvider, Executor

REPO = Path(__file__).resolve().parents[1]
FIT = dict(scope_preservation='aligned', explanatory_scope='supported_scope',
           premise_treatment='properly_treated', evidence_decision_fit='grounded_action')


def packet(policy='committed', count=1, candidates=('wae',)):
    value = old_packet(candidates, count=count, attention=False)
    value.update(schema='mindthus.route-control-input.v2', consumption_policy=policy,
        conversation=[{'document_id': 'U', 'role': 'user', 'order': 0,
                       'author_ref': 'test-user', 'source_ref': 'synthetic:route-test'}],
        host_inferences={'provenance': 'host_inference', 'owner_ref': 'original-host',
                         'issue_views': {f'I{i+1}': {'actor': None, 'goal': None, 'scope': None,
                                                  'source_refs': []} for i in range(count)}})
    value['task_budget'] = {'max_calls': count + 1, 'max_seconds': 45 * (count + 1)}
    value['intervention'] = {'turn_id': value['turn_id'], 'history_sha256': sd.history_identity(value)}
    return value


class Provider(OldProvider):
    def __init__(self, overrides=None, revised=None, after=None):
        super().__init__(overrides)
        self.revised, self.after = revised or {}, after or {}

    def evaluate(self, specs, context, timeout):
        initial = self.overrides
        current = dict(initial)
        for spec in specs:
            if spec.id.startswith('COVERAGE.'):
                current.setdefault(spec.id, 'covered')
            if spec.id.startswith(('ROLE_SCOPE.', 'COMPANION_SCOPE.')):
                current.setdefault(spec.id, 'required')
            if spec.id.startswith('S1.'):
                current.setdefault(spec.id, FIT[spec.id.split('.')[-1]])
        if any('revised:' in v['text'] for v in context.get('assessment_targets', {}).values()):
            current.update(self.revised)
        if context.get('artifact_view'):
            current.update(self.after)
        self.overrides = current
        try:
            return super().evaluate(specs, context, timeout)
        finally:
            self.overrides = initial


class V03Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name); self.root = self.base / 'episode'
        self.registry = patch.object(rt, '_registry', return_value=self.base / 'registry')
        self.registry.start(); self.addCleanup(self.registry.stop)
        self.data = packet(); self.provider = Provider(); self.requests = []
        owner = self.data['authority']['owner_ref']
        self.hooks = dict(executor=CurrentAgentHost(owner), corrector=CurrentAgentHost(owner, role='correction'),
                          arbitrator=CurrentAgentHost(owner, role='arbitration'))

    def run_entry(self):
        return entry.run(self.root, self.provider, self.data, REPO, mode=v03.MODE, **self.hooks)

    def submit(self, result, mutate=None):
        h = read_record(Path(result['host_request'])); q = h['request']; schema = q.get('schema', '')
        self.requests.append(deepcopy(q))
        if schema.endswith('execution-request.v1'):
            reply = Executor().execute(q, 45)
            reply['dependency_acceptance'] = {eid: {'accepted': True,
                'artifact_sha256': digest(reply['text']), 'reason': 'Accepted by the fixture host for this use.'}
                for eid in q['dependency_uses']}
        elif schema.endswith('accept-request.v1'):
            reply = dict(schema='mindthus.route-v03-accept-reply.v1', request_id=q['request_id'],
                accepted={iid: {'accepted': q['dispositions'][iid] == 'resolved', 'artifact_sha256': sha,
                                'reason': 'Fixture host final acceptance.'} for iid, sha in q['candidates'].items()},
                usage=deepcopy(rt.UNKNOWN_USAGE))
        elif schema.endswith('arbitration-request.v1'):
            reply = dict(schema='mindthus.route-v03-arbitration-reply.v1', request_id=q['request_id'],
                decisions=[{'finding_id': f['finding_id'], 'target_version': f['target_version'],
                            'decision': 'dismiss', 'reason': 'The source supports this bounded statement.',
                            'original_refs': [rel.quote(q['original_input']['documents'][0])]} for f in q['findings']],
                usage=deepcopy(rt.UNKNOWN_USAGE))
        elif schema.endswith('advice-request.v1'):
            reply = dict(schema='mindthus.route-v03-advice-reply.v1', request_id=q['request_id'],
                         revisions={}, usage=deepcopy(rt.UNKNOWN_USAGE))
        elif schema.endswith('organize-request.v1'):
            prepared = packet()
            reply = dict(schema='mindthus.route-v03-organize-reply.v1', request_id=q['request_id'],
                         issues=prepared['issues'], host_inferences=prepared['host_inferences'], usage=deepcopy(rt.UNKNOWN_USAGE))
        else:
            reply = dict(schema='mindthus.route-v03-correction-reply.v1', request_id=q['request_id'],
                         dispositions=[], revisions={}, usage=deepcopy(rt.UNKNOWN_USAGE))
            for f in q['findings']:
                reply['dispositions'].append({'finding_id': f['finding_id'], 'decision': 'corrected',
                    'reason': 'Revise the concrete unsupported assertion.', 'original_refs': []})
                revision = reply['revisions'].setdefault(f['issue_id'], {'text': 'revised: bounded evidence and decision.',
                                                                       'version': '', 'changes': []})
                revision['version'] = digest(revision['text'])
                revision['changes'].append({'finding_id': f['finding_id'], 'start': 0, 'end': len(revision['text']),
                                           'sha256': digest(revision['text'])})
        if mutate:
            mutate(reply, q)
        submission = dict(schema='mindthus.current-host-response.v1', request_id=h['request_id'],
            request_sha256=h['request_sha256'], owner_ref=h['owner_ref'],
            host_context_ref='isolated-reviewer' if h['role'] == 'arbitration' else 'original-host-context',
            elapsed_seconds=1.0, reply=reply)
        submit_response(self.root, REPO, submission)
        return q, reply

    def drive(self, mutate=None):
        for _ in range(12):
            result = self.run_entry()
            if result.get('status') != 'awaiting_current_agent':
                return result
            self.submit(result, mutate)
        self.fail('unexpected host loop')

    def edge(self):
        self.data = packet(count=2)
        self.data['dependencies'] = [{'id': 'D1', 'producer': 'I1', 'consumer': 'I2',
            'artifact': 'bounded control judgment', 'condition': None, 'refs': [rel.quote(self.data['documents'][0])]}]

    def hit(self, check='evidence_decision_fit', iid='I1'):
        key = f'S1.{iid}.{check}'
        value = {'evidence_decision_fit': 'material_omission', 'scope_preservation': 'scope_drift',
                 'explanatory_scope': 'overextended_local_truth', 'premise_treatment': 'unsupported_candidate_claim'}[check]
        self.provider = Provider({key: value}, {key: FIT[check]})

    def object_all(self, reply, q):
        if q['schema'].endswith('correction-request.v1'):
            reply['revisions'] = {}
            for d in reply['dispositions']:
                d.update(decision='objected', reason='The source explicitly permits the candidate scope.',
                         original_refs=[rel.quote(self.data['documents'][0])])

    def test_clean_public_entry_accepts_and_replays_zero_calls(self):
        result = self.drive()
        self.assertTrue(result['consumption_complete'])
        self.assertEqual(result['counts']['judgment'], 2)
        self.assertEqual(result['counts']['execution'], 2)
        before = {str(p): p.read_bytes() for p in self.root.rglob('*.json')}
        self.assertEqual(result, self.run_entry())
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*.json')})
        self.assertEqual(self.provider.batch_count, 2)

    def test_correction_recheck_and_final_acceptance(self):
        self.hit(); result = self.drive()
        self.assertTrue(result['consumption_complete'])
        self.assertEqual(result['issue_states']['I1']['state'], 'resolved_by_revision')
        self.assertEqual(result['counts']['judgment'], 3)
        self.assertEqual(result['counts']['correction'], 1)

    def test_all_three_findings_reach_host(self):
        self.provider = Provider({f'S1.I1.{k}': v for k, v in {
            'scope_preservation': 'scope_drift', 'explanatory_scope': 'overextended_local_truth',
            'evidence_decision_fit': 'material_omission'}.items()}, {f'S1.I1.{k}': v for k,v in FIT.items()})
        result = self.drive(); q = next(q for q in self.requests if q['schema'].endswith('correction-request.v1'))
        self.assertEqual(len(q['findings']), 3); self.assertTrue(result['consumption_complete'])

    def test_advice_can_retain_without_dispositions(self):
        self.data = packet('advisory'); self.hit(); result = self.drive()
        q = next(q for q in self.requests if q['schema'].endswith('advice-request.v1'))
        self.assertEqual(len(q['findings']), 1); self.assertEqual(len(q['observations']), 4)
        self.assertTrue(result['consumption_complete']); self.assertIsNone(result['recheck'])

    def test_advice_can_revise_once(self):
        self.data = packet('advisory'); self.hit()
        def revise(reply, q):
            if q['schema'].endswith('advice-request.v1'):
                reply['revisions'] = {'I1': {'text': 'revised: supported advice.', 'version': digest('revised: supported advice.')}}
        result = self.drive(revise)
        self.assertTrue(result['consumption_complete']); self.assertEqual(result['counts']['judgment'], 3)

    def test_arbitration_has_candidate_and_survives_acceptance_resume(self):
        self.hit(); result = self.drive(self.object_all)
        self.assertTrue(result['consumption_complete'])
        self.assertEqual(result['issue_states']['I1']['state'], 'resolved_by_objection')
        self.assertEqual(result['counts']['arbitration'], 1)
        q = next(q for q in self.requests if q['schema'].endswith('arbitration-request.v1'))
        self.assertEqual(q['candidates']['I1']['text'], result['outputs']['I1']['text'])

    def test_recheck_hit_keeps_unresolved(self):
        self.hit(); self.provider.revised = {}; result = self.drive()
        self.assertFalse(result['consumption_complete']); self.assertIn('I1', result['pending'])
        self.assertFalse(result['acceptance']['accepted']['I1']['accepted'])

    def test_host_declines_acceptance_has_pending_reason(self):
        def refuse(reply,q):
            if q['schema'].endswith('accept-request.v1'): reply['accepted']['I1']['accepted'] = False
        result = self.drive(refuse)
        self.assertEqual(result['pending']['I1'], 'owner_declined_acceptance')
        self.assertFalse(result['consumption_complete'])

    def test_missing_coverage_stops_only_affected_issue(self):
        self.data = packet(count=2); self.provider = Provider({'COVERAGE.I2': 'missing'})
        result = self.drive(); self.assertIn('I1', result['outputs']); self.assertNotIn('I2', result['outputs'])
        self.assertIn('I2', result['pending'])

    def test_global_omission_remains_unassigned(self):
        self.provider = Provider({'COVERAGE.global': 'missing'}); result = self.drive()
        self.assertEqual(result['route']['coverage']['unassigned_scope'], 'missing'); self.assertFalse(result['outputs'])

    def test_accepted_predecessor_cannot_clear_missing_coverage(self):
        self.edge(); self.provider = Provider({'COVERAGE.I2': 'missing'})
        result = self.drive(); self.assertNotIn('I2', result['outputs'])
        self.assertIn('candidate_coverage_missing', result['pending']['I2'])

    def test_cli_compatible_host_reply_accepts_predecessor(self):
        self.edge(); result = self.drive()
        self.assertTrue(result['consumption_complete'])
        self.assertEqual(result['counts']['execution'], 3)
        self.assertEqual(result['outputs']['I2']['input_artifacts']['D1'], result['outputs']['I1']['artifact_sha256'])

    def test_predecessor_revision_invalidates_consumer(self):
        self.edge(); self.hit(); result = self.drive()
        self.assertEqual(result['pending']['I2'], 'accepted_predecessor_version_changed')
        self.assertFalse(result['outputs']['I2']['valid_for_current_dependencies'])
        self.assertEqual(result['outputs']['I1']['accepted_uses'], {})
        self.assertIn('D1', result['outputs']['I1']['invalidated_accepted_uses'])

    def test_actual_artifact_rechecks_only_waiting_consumer(self):
        self.edge(); self.provider = Provider({'M02.I2.wae': .5}, after={'M02.I2.wae': .95})
        result = self.drive(); self.assertTrue(result['consumption_complete'])
        batches = [specs for specs,context in self.provider.seen if context.get('artifact_view')]
        self.assertEqual(len(batches), 1)
        self.assertTrue(all('.I1' not in spec.id for spec in batches[0]))

    def test_simultaneous_revision_does_not_accept_stale_dependency(self):
        self.edge()
        self.provider=Provider({f'S1.{iid}.evidence_decision_fit':'material_omission' for iid in ('I1','I2')},
                               {f'S1.{iid}.evidence_decision_fit':'grounded_action' for iid in ('I1','I2')})
        result=self.drive()
        self.assertEqual(set(result['correction']['revisions']),{'I1','I2'})
        self.assertFalse(result['consumption_complete'])
        self.assertEqual(result['pending']['I2'],'accepted_predecessor_version_changed')
        self.assertFalse(result['acceptance']['accepted']['I2']['accepted'])

    def test_optional_method_unknown_preserves_primary(self):
        self.data = packet(candidates=('wae','tvg'))
        self.provider = Provider({'M02.I1.tvg': .5, 'M03.I1.tvg': 'support', 'ROLE_SCOPE.I1.tvg': 'optional'})
        result = self.drive(); self.assertEqual(result['route']['per_issue'][0]['primary'],'wae')
        self.assertTrue(result['consumption_complete'])

    def test_required_method_unknown_keeps_issue_pending(self):
        self.data = packet(candidates=('wae','tvg'))
        self.provider = Provider({'M02.I1.tvg': .5, 'M03.I1.tvg': 'support'})
        self.assertFalse(self.drive()['outputs'])

    def test_optional_companion_unknown_preserves_primary(self):
        self.data = packet(candidates=('mpg',))
        self.provider = Provider({'M05.I1.mpg': .5, 'COMPANION_SCOPE.I1.mpg': 'optional'})
        result = self.drive(); self.assertEqual(result['route']['per_issue'][0]['primary'],'mpg')

    def test_same_method_material_for_both_policies(self):
        committed = read_record(Path(self.run_entry()['host_request']))['request']
        self.data = packet('advisory'); self.data['episode_id'] = 'advice-comparison'; self.root = self.base/'advice'
        advisory = read_record(Path(self.run_entry()['host_request']))['request']
        self.assertEqual(committed['loaded_methods'], advisory['loaded_methods'])
        self.assertEqual(committed['route_observations'], advisory['route_observations'])
        self.assertIn('coverage', advisory)

    def test_pending_reentry_preserves_request_and_reserved_budget(self):
        first = self.run_entry(); second = self.run_entry()
        self.assertEqual(first, second); self.assertEqual(self.provider.batch_count, 1)
        self.assertEqual(second['reserved_counts']['execution'], 1)

    def test_new_profile_accepts_measured_host_latency_over_45_seconds(self):
        self.data['task_budget']['max_seconds']=360
        result=self.run_entry();h=read_record(Path(result['host_request']));q=h['request']
        self.assertEqual(h['allowance_seconds'],240)
        reply=Executor().execute(q,180)
        submit_response(self.root,REPO,dict(schema='mindthus.current-host-response.v1',request_id=h['request_id'],
            request_sha256=h['request_sha256'],owner_ref=h['owner_ref'],host_context_ref='original-host-context',
            elapsed_seconds=90.,reply=reply))
        result=self.drive();self.assertTrue(result['consumption_complete'])
        self.assertEqual(result['method_request_seconds'],91.)

    def test_missing_issue_organizes_once_in_same_episode(self):
        self.data['issues'] = []; self.data['host_inferences']['issue_views'] = {}
        self.hooks['organizer'] = CurrentAgentHost('original-host', role='organize')
        result = self.drive(); self.assertTrue(result['consumption_complete'])
        self.assertEqual(result['counts']['organize'], 1)

    def test_history_text_changes_hash(self):
        old = self.data['intervention']['history_sha256']
        self.data['documents'][0]['text'] += ' Additional scope.'
        self.assertNotEqual(old, sd.history_identity(self.data))
        with self.assertRaisesRegex(ContractError, 'v03_intervention_changed'): self.run_entry()

    def test_new_intervention_cannot_reuse_episode(self):
        self.drive(); self.data['turn_id'] = '2'; self.data['intervention']['turn_id'] = '2'
        with self.assertRaisesRegex(ContractError, 'immutable_relationship_record_changed'): self.run_entry()

    def test_no_candidate_s1_rejected(self):
        with self.assertRaisesRegex(ContractError, 'requires_actual_candidate'):
            sd.compile_s1(self.data, {}, {}, REPO, sd.load_contract(REPO)[0])

    def test_candidate_change_invalidates_all_s1_checks(self):
        contract = sd.load_contract(REPO)[0]
        out = {'I1': dict(text='first', artifact_sha256=digest('first'), revision=1)}
        first = sd.compile_s1(self.data, {}, out, REPO, contract)
        out['I1'].update(text='second',artifact_sha256=digest('second'))
        second = sd.compile_s1(self.data, {}, out, REPO, contract)
        self.assertNotEqual(first.identity,second.identity)
        self.assertTrue(all(a.question != b.question for a,b in zip(first.specs,second.specs)))

    def test_multiple_finding_response_cannot_omit_one(self):
        self.provider = Provider({'S1.I1.scope_preservation':'scope_drift','S1.I1.evidence_decision_fit':'material_omission'})
        result=self.run_entry();self.submit(result);result=self.run_entry()
        with self.assertRaisesRegex(ContractError,'v03_disposition_count'):
            self.submit(result,lambda r,q:r['dispositions'].pop())
        self.assertEqual(self.run_entry()['host_request'],result['host_request'])

    def test_correction_requires_new_text_and_change_binding(self):
        self.hit();r=self.run_entry();self.submit(r);r=self.run_entry()
        def corrupt(reply,q): reply['revisions']['I1']['changes'][0]['sha256']='wrong'
        with self.assertRaisesRegex(ContractError,'v03_change_binding'):self.submit(r,corrupt)

    def test_acceptance_contains_observations_and_actual_text(self):
        result=self.drive();q=next(q for q in self.requests if q['schema'].endswith('accept-request.v1'))
        self.assertEqual(q['candidate_texts']['I1'],result['outputs']['I1']['text'])
        self.assertEqual(q['evidence_sha256'],digest(q['evidence']))
        self.assertEqual(len(q['evidence']['initial']['matrix']),4)

    def test_acceptance_budget_exhaustion_is_not_complete(self):
        self.data['task_budget']['max_calls']=1
        result=self.drive();self.assertFalse(result['consumption_complete'])
        self.assertEqual(result['pending']['I1'],'acceptance_budget_exhausted')

    def test_mixed_revision_and_objection_bind_current_candidate(self):
        self.provider = Provider({'S1.I1.scope_preservation':'scope_drift',
                                  'S1.I1.evidence_decision_fit':'material_omission'},
                                 {'S1.I1.scope_preservation':'aligned'})
        def mixed(reply,q):
            if q['schema'].endswith('correction-request.v1'):
                fid=next(f['finding_id'] for f in q['findings'] if f['check_id']=='evidence_decision_fit')
                for d in reply['dispositions']:
                    if d['finding_id']==fid:
                        d.update(decision='objected',original_refs=[rel.quote(self.data['documents'][0])])
                revision=reply['revisions']['I1']
                revision['changes']=[c for c in revision['changes'] if c['finding_id']!=fid]
        result=self.drive(mixed)
        q=next(q for q in self.requests if q['schema'].endswith('arbitration-request.v1'))
        self.assertTrue(result['consumption_complete'])
        self.assertNotEqual(q['original_candidates']['I1'],q['candidates']['I1'])
        self.assertEqual(q['findings'][0]['target_version'],result['outputs']['I1']['artifact_sha256'])

    def test_arbitration_rejects_stale_candidate_version(self):
        self.hit();r=self.run_entry();self.submit(r);r=self.run_entry();self.submit(r,self.object_all)
        r=self.run_entry()
        with self.assertRaisesRegex(ContractError,'v03_arbitration_target'):
            self.submit(r,lambda reply,q:reply['decisions'][0].update(target_version='old-candidate'))

    def test_objection_without_arbitrator_stays_unresolved(self):
        self.hit();self.hooks['arbitrator']=None;result=self.drive(self.object_all)
        self.assertFalse(result['consumption_complete']);self.assertEqual(result['counts']['arbitration'],0)
        self.assertIn('I1',result['pending'])

    def test_predecessor_revision_leaves_independent_work_accepted(self):
        self.edge();third=packet(count=3)
        self.data['issues'].append(third['issues'][2])
        self.data['host_inferences']['issue_views']['I3']=third['host_inferences']['issue_views']['I3']
        self.data['task_budget']=third['task_budget'];self.hit()
        result=self.drive();self.assertNotIn('I3',result['pending'])
        self.assertTrue(result['acceptance']['accepted']['I3']['accepted'])
        self.assertIn('I2',result['pending'])

    def test_candidate_answer_error_does_not_erase_other_issue(self):
        self.data=packet(count=2)
        self.provider=Provider({'S1.I1.evidence_decision_fit':DecisionResult('provider_error',reason='bad answer')})
        self.hooks['corrector']=None;result=self.drive()
        self.assertIn('I2',result['outputs'])
        rows=[r for r in result['s1']['matrix'] if r['issue_id']=='I2']
        self.assertTrue(all(r['status']=='ok' for r in rows))
        self.assertEqual(len(rows),4)

    def test_original_host_context_cannot_change_on_resume(self):
        r=self.run_entry();self.submit(r);r=self.run_entry()
        h=read_record(Path(r['host_request']));q=h['request']
        reply=dict(schema='mindthus.route-v03-accept-reply.v1',request_id=q['request_id'],
            accepted={iid:dict(accepted=True,artifact_sha256=sha,reason='fixture') for iid,sha in q['candidates'].items()},
            usage=deepcopy(rt.UNKNOWN_USAGE))
        with self.assertRaisesRegex(ContractError,'v03_original_host_context_changed'):
            submit_response(self.root,REPO,dict(schema='mindthus.current-host-response.v1',request_id=h['request_id'],
                request_sha256=h['request_sha256'],owner_ref=h['owner_ref'],host_context_ref='replacement-host',
                elapsed_seconds=1.,reply=reply))

    def test_a_to_f_synthetic_fixtures_keep_source_and_close_consumption(self):
        for path in sorted((REPO/'experiments/typed_decision/fixtures/route-v03').glob('*.json')):
            with self.subTest(case=path.stem):
                fixture=json.loads(path.read_text());self.data=fixture['input'];self.root=self.base/path.stem
                self.requests=[];self.provider=Provider(fixture['answers'],
                    {f'S1.{i["id"]}.{k}':v for i in self.data['issues'] for k,v in FIT.items()})
                result=self.drive()
                self.assertEqual(fixture['source_kind'],'synthetic')
                self.assertTrue(result['consumption_complete'],result['pending'])
                self.assertEqual(len(result['s1']['findings']),fixture['reviewer_only']['expected_finding_count'])
                self.assertNotIn('reviewer_only',str(self.requests))
                for q in self.requests:
                    self.assertEqual(q['original_input']['conversation'],self.data['conversation'])

    def test_v03_cli_fixture_creates_current_host_handoff(self):
        fixture=json.loads((REPO/'experiments/typed_decision/fixtures/route-v03/B-control.json').read_text())
        fixture['input']['episode_id']='cli-v03-'+self.base.name
        fp=self.base/'fixture.json';fp.write_text(json.dumps(fixture))
        p=subprocess.run([sys.executable,'-m','experiments.typed_decision.entry','--mode',v03.MODE,
            '--fixture',str(fp),
            '--state-root',str(self.root)],cwd=REPO,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr+p.stdout)
        result=json.loads(p.stdout);self.assertEqual(result['status'],'awaiting_current_agent')
        self.assertEqual(result['counts']['judgment'],1)


if __name__ == '__main__':
    unittest.main()
