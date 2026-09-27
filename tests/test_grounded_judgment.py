"""Contract-focused offline tests; no network, authentication or model probes."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from experiments.typed_decision.contracts import ContractError, DecisionSpec
from experiments.grounded_judgment import core as c, runtime as rt
from experiments.grounded_judgment.development import cases, values, model_value, simulated, export


class GroundedTests(unittest.TestCase):
    def setUp(self):
        self.case=cases()[1];self.src=c.index(self.case['documents']);self.v=values(self.case,self.src)
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'run'
    def tearDown(self):self.temp.cleanup()
    def atoms(self,arm='B',changes=None):
        v={**self.v,**(changes or {})};atoms={}
        for n in (1,2,3):
            for q in c.specs(self.src,n,atoms):
                basis=list(dict.fromkeys(v[k] for k in ('G','O','C','P') if v[k] in self.src['candidates']))
                raw=model_value(q,v[q.id],basis,arm)
                atoms[q.id]=c.adapt(self.src,q,raw,arm,atoms)
        return atoms
    def run_to(self,phase,arm='B'):
        rt.init(self.root,self.case['documents'],arm)
        while True:
            req=rt.request(self.root)
            if req is None or req['phase']==phase:return req
            self.reply(req,simulated(req,rt.state(self.root),self.case))
    def reply(self,req,response,status='returned'):
        return rt.accept(self.root,{'request_sha256':req['request_sha256'],'simulation':True,
                                   'status':status,'response':response})

    def test_offsets_unicode_pairs_and_context(self):
        d=copy.deepcopy(self.case['documents'][:1]);d[0]['text']='🙂甲。\n乙？ 丙。'
        src=c.index(d)
        for ref in src['candidates'].values():c.validate_ref(src,ref)
        self.assertTrue(any('甲。\n乙？' in r['exact_text'] for r in src['candidates'].values()))
        self.assertEqual(next(iter(src['candidates'].values()))['end'],3)
    def test_tampered_quote_revision_hash_and_offset(self):
        ref=next(iter(self.src['candidates'].values()))
        for k,val in [('exact_text','wrong'),('revision','99'),('sha256','0'),('end',10000)]:
            bad={**ref,k:val}
            with self.subTest(k=k),self.assertRaises(ContractError):c.validate_ref(self.src,bad)
    def test_overflow_no_truncation(self):
        ds=copy.deepcopy(self.case['documents'][:1]);ds[0]['text']='甲。'*130
        src=c.index(ds);self.assertEqual(src['coverage'],'coverage_miss')
        self.assertEqual(src['documents'],ds);self.assertEqual(c.specs(src,1),[])
    def test_duplicate_document_rejected(self):
        with self.assertRaises(ContractError):c.index([self.case['documents'][0]]*2)
    def test_exact_13_three_rounds_and_e_dependency(self):
        self.assertEqual(sum(map(len,c.ROUNDS)),13)
        self.assertEqual([q.id for q in c.specs(self.src,1)],['G','O','C'])
        a=self.atoms();qs=c.specs(self.src,2,a)
        self.assertEqual([q.id for q in qs],['P','E']);self.assertIn('不引用同轮P',qs[1].question)
        self.assertEqual(c.specs(self.src,2,{}),[])
    def test_jev_distribution_and_weighted_contract(self):
        a=self.atoms();q=next(q for q in c.specs(self.src,3,a) if q.id=='I_R')
        raw=model_value(q,1,[],'C');raw['value']=1.3
        self.assertEqual(c.adapt(self.src,q,raw,'C',a)['semantic_state'],'invalid')
    def test_agent_probability_not_accepted(self):
        q=c.specs(self.src,1)[0];raw=model_value(q,self.v['G'],[],'B');raw['confidence']=.99
        self.assertEqual(c.adapt(self.src,q,raw,'B',{})['semantic_state'],'invalid')
    def test_jev_low_choice_abstains(self):
        q=c.specs(self.src,1)[0];raw=model_value(q,self.v['G'],[],'C')
        others=[k for k in q.criteria if k!=self.v['G']]
        raw['uncertainty']['probabilities']={k:0. for k in q.criteria}
        raw['uncertainty']['probabilities'][self.v['G']]=.6
        raw['uncertainty']['probabilities'][others[0]]=.4
        got=c.adapt(self.src,q,raw,'C',{})
        self.assertEqual(got['unresolved_reason'],'low_confidence')
    def test_target_denial_alone_is_not_finding(self):
        a=self.atoms(changes={'T':'deny','TB':'insufficient','R':'sufficient','S':'support'})
        got=c.compose(self.src,a);self.assertEqual(got['goal'],'unresolved');self.assertEqual(got['findings'],[])
    def test_target_denial_with_refs(self):
        got=c.compose(self.src,self.atoms(changes={'T':'deny','TB':'different_G_C'}))
        self.assertEqual(len(got['findings']),2);self.assertEqual(got['findings'][0]['action'],'reanchor')
    def test_conflict_basis_missing_invalid(self):
        a=self.atoms();q=next(q for q in c.specs(self.src,3,a) if q.id=='TB')
        raw=model_value(q,'different_G_C',[self.v['P']],'B')
        self.assertEqual(c.adapt(self.src,q,raw,'B',a)['semantic_state'],'invalid')
    def test_sufficient_not_only_synonym(self):
        got=c.compose(self.src,self.atoms(changes={'R':'sufficient','S':'support'}))
        self.assertEqual(got['relation'],'retain');self.assertFalse(got['findings'])
    def test_contradiction_table(self):
        got=c.compose(self.src,self.atoms(changes={'R':'contradicts'}))
        self.assertEqual(got['relation'],'recheck')
    def test_incompatible_relation_s_is_unresolved(self):
        got=c.compose(self.src,self.atoms(changes={'R':'sufficient','S':'deny'}))
        self.assertEqual(got['relation'],'unresolved');self.assertFalse(got['findings'])
    def test_missing_e_keeps_conditional_reasoning(self):
        got=c.compose(self.src,self.atoms())
        self.assertEqual(got['relation'],'limit');self.assertEqual(got['premise_status'],'conditional_on_given')
        self.assertFalse(got['external_fact_verified'])
    def test_source_identity_not_support(self):
        ds=copy.deepcopy(self.case['documents']);ds[0]['origin']='direct';self.src=c.index(ds)
        a=self.atoms(changes={'E':self.v['P'],'ES':'direct','ER':'refutes'})
        got=c.compose(self.src,a);self.assertTrue(got['evidence_conflict'])
        self.assertEqual(got['premise_status'],'premise_unverified')
    def test_missing_image_cannot_be_direct(self):
        ds=copy.deepcopy(self.case['documents']);ds[0].update(origin='missing',available=False);self.src=c.index(ds)
        a=self.atoms(changes={'E':self.v['P'],'ES':'direct','ER':'supports'})
        self.assertEqual(a['ES']['semantic_state'],'invalid')
    def test_correct_uncertainty_counts_in_same_denominator(self):
        a=self.atoms(changes={'R':'insufficient','S':'unresolved'})['R']
        norm={k:a[k] for k in ('value','semantic_state','unresolved_reason','basis_refs')}
        self.assertEqual(c.score_atom(a,norm)['success'],1)
        low={**a,'unresolved_reason':'low_confidence'}
        low_norm={k:low[k] for k in norm}
        self.assertEqual(c.score_atom(low,low_norm),{'denominator':1,'success':0,'completed':False})
    def test_single_variable_pairs(self):
        cs=cases()
        for left,right in ((cs[0],cs[1]),(cs[2],cs[3])):
            diffs=[(a,b) for a,b in zip(left['documents'],right['documents']) if a!=b]
            self.assertEqual(len(diffs),1)
            self.assertEqual([k for k in diffs[0][0] if diffs[0][0][k]!=diffs[0][1][k]],['text'])
    def test_atomic_then_combine_then_draft(self):
        req=self.run_to('draft');self.assertEqual(req['phase'],'draft')
        kinds=[rt.read(p)['body']['kind'] for p in sorted((self.root/'events').glob('*.json'))]
        self.assertLess(kinds.index('response'),kinds.index('adapted'))
        self.assertLess(kinds.index('adapted'),kinds.index('combined'))
        self.assertNotIn('first_draft',kinds)
    def test_agent_cannot_smuggle_draft(self):
        req=self.run_to('atoms');raw=simulated(req,rt.state(self.root),self.case);raw['draft']='premature'
        self.assertEqual(self.reply(req,raw)['stopped'],'format_failure')
    def test_wrong_round_atoms_rejected(self):
        req=self.run_to('round1','C');raw=simulated(req,rt.state(self.root),self.case);raw['P']=raw['G']
        self.assertEqual(self.reply(req,raw)['stopped'],'format_failure')
    def test_one_check_one_revision(self):
        req=self.run_to('done')
        self.assertIsNone(req);s=rt.state(self.root)
        self.assertEqual((s['check_count'],s['revision_count']),(1,1))
        self.assertNotEqual(s['draft'],s['final'])
        self.assertIsNone(rt.request(self.root))
    def test_no_finding_no_jev_check(self):
        self.case=cases()[0];self.run_to('done','C');s=rt.state(self.root)
        self.assertEqual(s['call_count'],4);self.assertEqual(s['check_count'],0)
    def test_early_revision_disallowed(self):
        req=self.run_to('draft')
        self.assertEqual(self.reply(req,{'kind':'revision'})['stopped'],'format_failure')
    def test_request_is_idempotent(self):
        req=self.run_to('round1','C');self.assertEqual(req,rt.request(self.root))
        self.assertEqual(rt.state(self.root)['call_count'],0)
    def test_unknown_stops_without_retry(self):
        req=self.run_to('round1','C');self.reply(req,{},'unknown')
        self.assertIsNone(rt.request(self.root))
        with self.assertRaises(ContractError):self.reply(req,{},'returned')
    def test_safety_refusal_stops_without_form_change(self):
        req=self.run_to('round1','C');self.reply(req,{},'safety_refusal')
        self.assertIsNone(rt.request(self.root))
    def test_wrong_request_does_not_advance(self):
        req=self.run_to('round1','C')
        with self.assertRaises(ContractError):rt.accept(self.root,{'request_sha256':'wrong','simulation':True,'status':'returned'})
        self.assertEqual(rt.request(self.root),req)
    def test_simulation_cannot_fill_real_exchange(self):
        rt.init(self.root,self.case['documents'],'A',simulation=False,materials={'skills/using-mindthus/SKILL.md':'entry','method_catalog':'catalog'},initial_paths=['skills/using-mindthus/SKILL.md','method_catalog']);req=rt.request(self.root)
        with self.assertRaises(ContractError):self.reply(req,{})
    def test_tampered_event_stops(self):
        self.run_to('atoms');p=self.root/'events/0000.json';x=rt.read(p);x['body']['payload']['arm']='C';p.write_text(json.dumps(x))
        with self.assertRaises(ContractError):rt.state(self.root)
    def test_native_read_normal_resources_and_duplicate_rejected(self):
        rt.init(self.root,self.case['documents'],'A',materials={'entry':'entry','method':'method'},initial_paths=['entry'])
        req=rt.request(self.root);self.assertEqual(req['payload']['loaded_materials'],{'entry':'entry'})
        self.reply(req,{'kind':'read','text':'','read_paths':['method'],'objection':''})
        req=rt.request(self.root);self.assertEqual(req['payload']['loaded_materials']['method'],'method')
        s=self.reply(req,{'kind':'read','text':'','read_paths':['method'],'objection':''})
        self.assertEqual(s['stopped'],'format_failure')
    def test_all_public_traces_and_counts(self):
        out=export(Path(self.temp.name)/'demo');self.assertEqual(len(out),12)
        counts={(r['case'],r['arm']):r['calls'] for r in out}
        self.assertEqual(counts['skills-validator','C'],6)
        self.assertEqual(counts['skills-validator','B'],4)
        self.assertEqual(counts['skills-simple','A'],2)
        relations={r['case']:r['composition']['relation'] for r in out if r['arm']=='C'}
        self.assertEqual(relations,{'skills-simple':'retain','skills-validator':'limit','4k-size':'unresolved','4k-density':'retain'})

    def test_jev_wire_conversion_no_network(self):
        from experiments.grounded_judgment.exchange import jev_payload,jev_results
        req=self.run_to('round1','C');wire=jev_payload(req)
        self.assertEqual(wire['model'],'jev-1.13.0')
        answers={}
        for q in req['payload']['questions']:
            spec=DecisionSpec(**q);raw=model_value(spec,self.v[spec.id],[],'C')
            answers[spec.id]={'type':'choice','choice':raw['value'],'confidence':1.,
                             'probabilities':raw['uncertainty']['probabilities']}
        self.assertEqual(set(jev_results(req,answers)),{'G','O','C'})
    def test_pending_interrupted_transaction_is_not_replayed(self):
        self.run_to('atoms');rt.append(self.root,'response',{'unfinished':True})
        with self.assertRaises(ContractError):rt.request(self.root)
    def test_two_findings_check_is_four_questions(self):
        req=self.run_to('atoms');raw=simulated(req,rt.state(self.root),self.case)
        raw['T'].update(value='deny',semantic_state='deny')
        raw['TB']['value']='different_G_C';self.reply(req,raw)
        req=rt.request(self.root);self.reply(req,simulated(req,rt.state(self.root),self.case))
        req=rt.request(self.root);self.assertEqual(len(req['payload']['questions']),4)
    def test_score_failure_does_not_erase_finding(self):
        a=self.atoms();a['I_R']=c.blank('I_R','contract_error','invalid')
        self.assertEqual(c.compose(self.src,a)['findings'][0]['action'],'limit')
    def test_all_denominators_and_normative_uncertainty_pair(self):
        uncertain=self.atoms(changes={'R':'insufficient'})['R']
        certain=self.atoms(changes={'R':'sufficient','S':'support'})['R']
        def norm(a):return {k:a[k] for k in ('value','semantic_state','unresolved_reason','basis_refs')}
        samples=[{'id':'u','pair':'pair','atoms':{'R':uncertain},'norms':{'R':norm(uncertain)}},
                 {'id':'s','pair':'pair','atoms':{'R':certain},'norms':{'R':norm(certain)}}]
        self.assertEqual(c.score_samples(samples)['pair_success'],1)
        samples[0]['atoms']={}
        got=c.score_samples(samples)
        self.assertEqual((got['denominator'],got['pair_denominator'],got['pair_success']),(2,1,0))
    def test_check_support_with_no_location_is_unresolved(self):
        self.run_to('check');req=rt.request(self.root);s=rt.state(self.root)
        raw=simulated(req,s,self.case)
        raw['LOC.inference']['value']='none'
        raw['OK.inference'].update(value='support',semantic_state='support')
        end=self.reply(req,raw)
        self.assertEqual(end['revision_count'],0)
        self.assertEqual(end['check']['OK.inference']['unresolved_reason'],'check_conflict')
    def test_measurements_unknown_not_invented(self):
        self.run_to('done','C');s=rt.state(self.root)
        self.assertTrue(all(m['underlying_requests'] is None and m['usage'] is None for m in s['measurements']))
        self.assertTrue(all(m['simulation'] for m in s['measurements']))
    def test_no_method_material_preload(self):
        from experiments.grounded_judgment.exchange import prepare_input
        repo=Path(self.temp.name)/'repo';entry=repo/'skills/using-mindthus/SKILL.md'
        entry.parent.mkdir(parents=True);entry.write_text('original entry')
        method=repo/'skills/test/SKILL.md';method.parent.mkdir();method.write_text('method body')
        prepared=prepare_input(self.case['documents'],repo)
        self.assertIn('skills/test/SKILL.md',prepared['materials'])
        self.assertNotIn('skills/test/SKILL.md',prepared['initial_paths'])

if __name__=='__main__':unittest.main()
