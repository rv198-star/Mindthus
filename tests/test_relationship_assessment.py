"""Relationship D1 controls: fixture labels test mechanics, not Jev accuracy."""
from dataclasses import asdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from experiments.typed_decision import relationship_assessment as m
from experiments.typed_decision.contracts import ContractError, DecisionResult, canonical
from experiments.typed_decision.providers import FixtureProvider
from experiments.typed_decision.session import Session, Limits

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/internal/research/typed-decision/entry-assessment/original-scenarios-design'


def packet(kind='definition', candidate='在这个对象内，所给机制和约束共同解释了目标结果。'):
    docs = [
        {'id':'U','revision':'1','kind':'user','text':'只讨论这个Skills的实际用途与解释，不扩大到Agent系统。'},
        {'id':'S','revision':'1','kind':'source','text':'给定记录：模板传递要求，独立任务约束改变同一模板下的结果。'},
        {'id':'C','revision':'1','kind':'candidate','text':candidate}]
    ur, sr, cr = (m.quote(x) for x in docs)
    fields = {key:{'text':value,'origin':'explicit','refs':[ur]} for key,value in
              zip(m.FRAME_FIELDS, ['用户','这个Skills','当前','解释实际用途','只讨论该对象'])}
    return {'schema':'relationship-input.v1','episode_id':'T1','turn_id':'2','revision':'1','stage':'S1',
            'documents':docs,'proposal':{
                'frames':[{'id':'F0','kind':kind,**fields}],
                'candidate':{'ref':cr,'thesis_refs':[cr],'controller_refs':[cr],'discriminator_refs':[cr]},
                'scope_correction_refs':[ur],
                'claims':[{'id':'K0','text':'模板传递要求','origin':'source_observation','refs':[sr]},
                          {'id':'K1','text':'约束影响结果','origin':'source_observation','refs':[sr]}],
                'edges':[], 'user_premise':None,'competitions':[]},
            'authority':{'owner_ref':'original-host','risk':'low','mode':'advisory','known_obligations':[]},
            'activation':{'enabled':True,'source_refs':[ur],'reason':'已有入口的局部判断需要核对'}}


DEFAULT = {'q0':'usable','q1':'frame.F0','scope_acceptance':'preserved','alignment':'aligned',
           'local_transfer':'supported_within_scope','user_adoption':'supported_or_qualified',
           'support':'source_supported','role':'decision_driver','joint':'joint_grounded',
           'readiness':'decide_now','delivery':'verdict_with_basis','definition':'grounded_object_account',
           'competition':'material_comparison'}


def response(compiled, overrides=None):
    values = overrides or {}
    out = {}
    for spec, binding in zip(compiled.specs, compiled.bindings):
        value = values.get(spec.id, values.get(binding['family'], DEFAULT[binding['family']]))
        result = value if isinstance(value, DecisionResult) else DecisionResult('ok', value)
        out[spec.id] = asdict(result)
    return {'identity':deepcopy(compiled.identity),'results':out}


class RelationshipTests(unittest.TestCase):
    def evaluate(self, data=None, values=None):
        c = m.compile_packet(data or packet(), ROOT)
        return m.consume(c, response(c, values), ROOT)

    def test_injection_fixture_has_no_truth_or_task_pass(self):
        r = self.evaluate()
        self.assertEqual(r['action'], 'continue_original')
        self.assertFalse(r['qualification']); self.assertFalse(r['task_complete'])
        self.assertNotIn('conclusion_acceptance', r)

    def test_scope_acceptance_does_not_concede_definition(self):
        r = self.evaluate(values={'definition':'carrier_only_unjustified'})
        self.assertTrue(r['scope_acceptance'])
        self.assertEqual(r['action'],'request_correction')
        self.assertEqual(r['plan']['repair_relations'][0]['kind'],'rebuild_same_object')

    def test_scope_acceptance_does_not_overrule_independent_alignment(self):
        r = self.evaluate(values={'alignment':'object_substituted'})
        self.assertTrue(r['scope_acceptance'])
        self.assertIn('restore_scope', [x['kind'] for x in r['plan']['repair_relations']])

    def test_missing_account_and_list_are_distinct_repairs(self):
        r = self.evaluate(values={'definition':'account_missing','delivery':'list_only',
                                  'joint':'joint_account_missing'})
        self.assertEqual({x['kind'] for x in r['plan']['repair_relations']},
                         {'rebuild_same_object','deliver_verdict','explain_joint_relation'})

    def test_supported_simple_mechanism_may_continue(self):
        r = self.evaluate(packet(candidate='这个有限实现仅注入固定模板；给定材料支持它完整解释所问功能。'))
        self.assertEqual(r['action'],'continue_original')

    def test_unsupported_alternative_is_retracted_not_rewarded(self):
        r = self.evaluate(values={'definition':'unsupported_alternative'})
        self.assertIn('retract_unsupported_alternative', [x['kind'] for x in r['plan']['repair_relations']])

    def test_definition_is_mandatory_without_competition(self):
        c = m.compile_packet(packet(), ROOT)
        self.assertIn('definition.F0', [s.id for s in c.specs])
        self.assertNotIn('competition.F0', [s.id for s in c.specs])

    def test_grounded_definition_missing_locations_returns_not_fake_evidence(self):
        p = packet(); p['proposal']['candidate']['controller_refs'] = []
        r = self.evaluate(p)
        self.assertEqual(r['reason'],'reference_gap'); self.assertNotIn('plan',r)

    def test_material_competition_requires_discriminator_location(self):
        p=packet(); cr=p['proposal']['candidate']['ref']
        p['proposal']['competitions']=[{'frame_id':'F0','left_refs':[cr],'right_refs':[cr]}]
        p['proposal']['candidate']['discriminator_refs']=[]
        self.assertEqual(self.evaluate(p)['reason'],'reference_gap')

    def test_joint_grounded_two_drivers_are_not_two_owners(self):
        r=self.evaluate(packet('decision'))
        self.assertEqual(r['action'],'continue_original')
        self.assertEqual(sum(x['value']=='decision_driver' and x['consumed'] for x in r['matrix']),2)

    def test_joint_unresolved_returns_without_a_plan(self):
        r=self.evaluate(packet('decision'),{'joint':'unresolved'})
        self.assertEqual(r['action'],'return_original_owner')
        self.assertNotIn('plan',r); self.assertNotIn('preserve_refs',r)

    def test_missing_joint_account_requests_only_named_repair(self):
        r=self.evaluate(packet('decision'),{'joint':'joint_account_missing'})
        self.assertEqual([x['kind'] for x in r['plan']['repair_relations']],['explain_joint_relation'])

    def test_user_tradeoff_allows_conditional_judgment(self):
        r=self.evaluate(packet('decision'),{'joint':'conditional_branching','readiness':'conditional_decision',
                                            'delivery':'conditional_verdict'})
        self.assertEqual(r['action'],'continue_original')

    def test_unconditional_verdict_when_tradeoff_open_requests_conditions(self):
        r=self.evaluate(packet('decision'),{'readiness':'conditional_decision'})
        self.assertEqual([x['kind'] for x in r['plan']['repair_relations']],['state_conditions'])

    def test_true_verdict_conflict_returns_original_owner(self):
        self.assertEqual(self.evaluate(values={'delivery':'conflicting_verdicts'})['action'],'return_original_owner')

    def test_all_mapping_failures_block_conditional_results(self):
        for value in ('material_omission','unsupported_mapping','both','uncertain'):
            with self.subTest(value=value):
                r=self.evaluate(values={'q0':value,'definition':'carrier_only_unjustified'})
                self.assertNotIn('plan',r)
                self.assertTrue(all(not x['consumed'] for x in r['matrix'] if x['id']!='q0'))

    def test_unselected_frame_unknown_is_not_veto(self):
        p=packet(); f=deepcopy(p['proposal']['frames'][0]); f['id']='F1';p['proposal']['frames'].append(f)
        r=self.evaluate(p,{'alignment.F1':'uncertain','definition.F1':'uncertain','joint.F1':'unresolved'})
        self.assertEqual(r['action'],'continue_original')
        for row in r['matrix']:
            if row['frame_id']=='F1':
                self.assertFalse(row['consumed']);self.assertIn('unconsumed_speculative',row['unconsumed_reason'])

    def test_non_unique_frame_never_creates_correction_plan(self):
        for v in ('none','ambiguous','multiple_requests'):
            r=self.evaluate(values={'q1':v});self.assertEqual(r['reason'],'frame_not_unique');self.assertNotIn('plan',r)

    def test_support_unknown_does_not_consume_speculative_role(self):
        r=self.evaluate(packet('decision'),{'support.K0':'not_established','role.F0.K0':'uncertain','joint':'unresolved'})
        self.assertEqual(r['action'],'continue_original')
        rows={x['id']:x for x in r['matrix']}
        self.assertFalse(rows['role.F0.K0']['consumed']);self.assertFalse(rows['joint.F0']['consumed'])

    def test_source_contradiction_returns_owner(self):
        r=self.evaluate(values={'support.K0':'source_contradicted'})
        self.assertEqual(r['reason'],'source_or_verdict_contradiction');self.assertNotIn('plan',r)

    def test_non_ok_is_not_false(self):
        for status in ('abstain','provider_error','unsupported','missing_context'):
            r=self.evaluate(values={'definition':DecisionResult(status)})
            self.assertEqual(r['action'],'return_original_owner')

    def test_low_confidence_preserved_without_invented_threshold(self):
        c=m.compile_packet(packet(),ROOT);r=response(c)
        r['results']['definition.F0']['uncertainty']={'source':'provider_distribution','confidence':.1}
        result=m.consume(c,r,ROOT)
        row=next(x for x in result['matrix'] if x['id']=='definition.F0')
        self.assertEqual(row['uncertainty']['confidence'],.1);self.assertFalse(result['qualification'])

    def test_known_obligations_never_discharged(self):
        p=packet();p['authority']['known_obligations']=['verify-original-notice']
        self.assertEqual(self.evaluate(p)['reason'],'known_obligation_retained')
        r=self.evaluate(p,{'definition':'carrier_only_unjustified'})
        self.assertEqual(r['plan']['known_obligations'],['verify-original-notice'])
        self.assertFalse(r['plan']['task_complete'])

    def test_named_fact_gap_retains_owner_not_task_success(self):
        self.assertEqual(self.evaluate(values={'readiness':'need_named_fact'})['reason'],
                         'named_fact_requires_original_owner')

    def test_s0_never_invents_candidate_questions(self):
        p=packet();p['stage']='S0';p['proposal']['candidate']=None
        c=m.compile_packet(p,ROOT)
        self.assertFalse(any(s.id.startswith(('definition.','delivery.','alignment.','joint.')) for s in c.specs))

    def test_no_activation_or_permission_generates_no_questions(self):
        for mut in ('disabled','high','none'):
            p=packet()
            if mut=='disabled':p['activation']['enabled']=False
            elif mut=='high':p['authority']['risk']='high'
            else:p['authority']['mode']='none'
            c=m.compile_packet(p,ROOT);self.assertEqual(c.specs,())
            self.assertEqual(m.consume(c,response(c),ROOT)['action'],'return_original_owner')

    def test_unicode_quote_and_stale_or_shifted_refs(self):
        doc={'id':'U','revision':'2','kind':'user','text':'甲🙂乙\r\n末'}
        ref=m.quote(doc,1,2);self.assertEqual(ref['sha256'],hashlib.sha256('🙂'.encode()).hexdigest())
        for field,value in [('revision','stale'),('sha256','0'*64),('start',True),('end',9999)]:
            p=packet();p['proposal']['candidate']['ref'][field]=value
            with self.assertRaises(ContractError):m.compile_packet(p,ROOT)

    def test_candidate_location_cannot_reference_source(self):
        p=packet();p['proposal']['candidate']['controller_refs']=[m.quote(p['documents'][1])]
        with self.assertRaises(ContractError):m.compile_packet(p,ROOT)

    def test_source_observation_cannot_be_candidate_self_evidence(self):
        p=packet();p['proposal']['claims'][0]['refs']=[p['proposal']['candidate']['ref']]
        with self.assertRaises(ContractError):m.compile_packet(p,ROOT)

    def test_expected_labels_rejected_at_structural_boundary(self):
        for target in ('packet','proposal','frame'):
            p=packet();obj=p if target=='packet' else p['proposal'] if target=='proposal' else p['proposal']['frames'][0]
            obj['expected_hits']=[]
            with self.assertRaises(ContractError):m.compile_packet(p,ROOT)

    def test_response_identity_and_option_shape_rejected(self):
        c=m.compile_packet(packet(),ROOT)
        for mutate in ('identity','missing','extra','option'):
            r=response(c)
            if mutate=='identity':r['identity']['packet_sha256']='0'*64
            elif mutate=='missing':del r['results']['q0']
            elif mutate=='extra':r['results']['other']=r['results']['q0']
            else:r['results']['q0']['value']='true'
            with self.assertRaises(ContractError):m.consume(c,r,ROOT)

    def test_compiled_context_mutation_rejected(self):
        c=m.compile_packet(packet(),ROOT);r=response(c);c.context['authority']['owner_ref']='other'
        with self.assertRaises(ContractError):m.consume(c,r,ROOT)

    def test_exact_byte_metrics_and_overflow(self):
        p=packet();c=m.compile_packet(p,ROOT);contract,rules=m.load_contract(ROOT)
        self.assertEqual(c.identity['projected_request_bytes'],len(canonical({'state':c.context,'questions':[s.to_dict() for s in c.specs]})))
        for metric,size in [('input_bytes',len(canonical(p))),('projected_request_bytes',c.identity['projected_request_bytes'])]:
            for delta in (-1,0,1):
                changed=deepcopy(contract);changed['budgets'][metric]=size+delta
                with patch.object(m,'load_contract',return_value=(changed,rules)):
                    if delta<0:
                        with self.assertRaisesRegex(ContractError,'coverage_overflow'):m.compile_packet(p,ROOT)
                    else:m.compile_packet(p,ROOT)

    def test_maximum_shape_is_24_questions_not_24_calls(self):
        p=packet(); f=deepcopy(p['proposal']['frames'][0]);f['id']='F1';p['proposal']['frames'].append(f)
        ur=m.quote(p['documents'][0]);cr=p['proposal']['candidate']['ref'];sr=m.quote(p['documents'][1])
        p['proposal']['edges']=[{'id':'E'+str(i),'frame_id':'F'+str(i),'premise_refs':[sr],'conclusion_refs':[cr]} for i in range(2)]
        p['proposal']['user_premise']={'premise_refs':[ur],'target_refs':[cr]}
        p['proposal']['competitions']=[{'frame_id':'F'+str(i),'left_refs':[cr],'right_refs':[cr]} for i in range(2)]
        c=m.compile_packet(p,ROOT);self.assertEqual(len(c.specs),24)
        f=deepcopy(f);f['id']='F2';p['proposal']['frames'].append(f)
        with self.assertRaisesRegex(ContractError,'coverage_overflow'):m.compile_packet(p,ROOT)

    def test_one_fixture_batch_and_cached_reentry_no_new_calls(self):
        p=packet();c=m.compile_packet(p,ROOT)
        answers={s.id:DEFAULT[b['family']] for s,b in zip(c.specs,c.bindings)}
        with tempfile.TemporaryDirectory() as tmp:
            provider=FixtureProvider(answers)
            with Session(Path(tmp),provider,scope='relationship-D1',limits=Limits(max_calls=1,max_seconds=30)) as s:
                first=m.assess_offline(s,p,ROOT)
                self.assertEqual(s.calls_made,1)
            with Session(Path(tmp),provider,scope='relationship-D1',limits=Limits(max_calls=1,max_seconds=30)) as s:
                second=m.assess_offline(s,p,ROOT)
                self.assertEqual(s.calls_made,0);self.assertEqual(s.calls_reused,1)
            self.assertEqual(first['result'],second['result'])

    def test_live_session_explicitly_rejected(self):
        class Live:
            is_live=True
        class FakeSession:
            provider=Live();evidence_kind='live_model';live_admission={}
        with self.assertRaisesRegex(ContractError,'live_not_admitted'):
            m.assess_offline(FakeSession(),packet(),ROOT)

    def test_unhashable_or_foreign_document_reference_rejected(self):
        for value in ([], {}, 'absent'):
            p=packet();p['proposal']['candidate']['ref']['document_id']=value
            with self.assertRaises(ContractError):m.compile_packet(p,ROOT)

    def test_explicit_frame_cannot_claim_candidate_as_user_source(self):
        p=packet();p['proposal']['frames'][0]['goal']['refs']=[p['proposal']['candidate']['ref']]
        with self.assertRaises(ContractError):m.compile_packet(p,ROOT)

    def test_repair_always_identifies_exact_candidate(self):
        p=packet();r=self.evaluate(p,{'definition':'carrier_only_unjustified'})
        for repair in r['plan']['repair_relations']:
            self.assertEqual(repair['target_ref'],p['proposal']['candidate']['ref'])

    def test_old_response_cannot_be_consumed_after_new_turn(self):
        p=packet();old=m.compile_packet(p,ROOT);p['turn_id']='3';current=m.compile_packet(p,ROOT)
        with self.assertRaises(ContractError):m.consume(current,response(old),ROOT)

    def test_canonical_source_and_contract_mutation_rejected(self):
        contract,_=m.load_contract(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp)
            for rel in [m.CONTRACT,*contract['sources']]:
                dst=repo/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,dst)
            p=packet();c=m.compile_packet(p,repo)
            file=repo/m.CONTRACT;changed=json.loads(file.read_text());changed['templates']['definition']['question']+='changed'
            file.write_text(json.dumps(changed,ensure_ascii=False))
            with self.assertRaises(ContractError):m.consume(c,response(c),repo)
            shutil.copy2(ROOT/m.CONTRACT,file)
            file=repo/next(iter(contract['sources']));file.write_bytes(file.read_bytes()+b'changed')
            with self.assertRaisesRegex(ContractError,'canonical_source_changed'):m.compile_packet(p,repo)

    def test_requested_question_budget_is_not_silently_truncated(self):
        p=packet();contract,rules=m.load_contract(ROOT);contract['budgets']['questions_per_batch']=1
        with patch.object(m,'load_contract',return_value=(contract,rules)):
            with self.assertRaisesRegex(ContractError,'coverage_overflow:questions'):m.compile_packet(p,ROOT)

    def test_fourteen_semantic_examples_use_injected_labels_only(self):
        examples=json.loads((BASE/'acceptance-v0.3.json').read_text())['semantic_examples']
        self.assertEqual(len(examples),14)
        for example in examples:
            with self.subTest(case=example['id']):
                p=packet(example['frame'],example['candidate'])
                # Authored source text is included for structural coverage only; judgments below remain injected.
                p['documents'][1]['text']=example['given']
                for claim in p['proposal']['claims']:
                    claim['refs']=[m.quote(p['documents'][1])]
                r=self.evaluate(p,example['expected'])
                self.assertEqual(r['action'],example['action'])
                actual={x['kind'] for x in r.get('plan',{}).get('repair_relations',[])}
                self.assertTrue(set(example['remedies'])<=actual)
                self.assertFalse(r['qualification'])


if __name__=='__main__':
    unittest.main()
