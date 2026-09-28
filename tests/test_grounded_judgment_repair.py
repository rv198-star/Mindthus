"""GJ-01..04 counterexamples only; requests/replies remain offline."""
import copy
import tempfile
import unittest
from pathlib import Path
from experiments.grounded_judgment import core as c,runtime as rt
from experiments.grounded_judgment.development import cases,values,simulated,model_value
from experiments.grounded_judgment.exchange import jev_payload
from experiments.typed_decision.contracts import DecisionSpec,ContractError,project_context


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'run'
        self.case=cases()[1]
    def tearDown(self):self.tmp.cleanup()
    def until(self,phase,arm):
        rt.init(self.root,self.case['documents'],arm)
        while True:
            req=rt.request(self.root)
            if req['phase']==phase:return req
            raw=simulated(req,rt.state(self.root),self.case)
            if req['phase']=='draft':raw['text']='第一句是保留内容。第二句是需要核对的结论。'
            self.send(req,raw)
    def send(self,req,raw):
        return rt.accept(self.root,{'request_sha256':req['request_sha256'],'simulation':True,
                                   'status':'returned','response':raw})
    def lower(self,raw,choice):
        raw=copy.deepcopy(raw);p=raw['uncertainty']['probabilities'];other=next(k for k in p if k!=choice)
        raw['uncertainty']['probabilities']={k:.6 if k==choice else .4 if k==other else 0. for k in p}
        return raw
    def norm(self,a):return {k:a[k] for k in ('value','semantic_state','unresolved_reason','basis_refs')}

    def test_gj01_B_actual_next_contract_to_accept(self):
        req=self.until('atoms','B');v=values(self.case,rt.state(self.root)['source']);raw={}
        for q in req['payload']['questions']:
            contract=q['output_contract'];val=v[q['id']]
            self.assertIn(val,contract['value_enum'])
            state=val if contract['kind']=='assess_proposition' else 'support'
            basis=list(dict.fromkeys(v[k] for k in ('G','C','P')))
            raw[q['id']]=dict(zip(contract['fields'],[val,state,None,basis]))
        s=self.send(req,raw)
        self.assertIsNone(s['stopped']);self.assertEqual(s['phase'],'draft')
        self.assertEqual(s['atoms']['T']['semantic_state'],'support')
        self.assertEqual(s['atoms']['S']['semantic_state'],'deny')
        self.assertEqual(req['payload']['consumption_rules'],c.CONSUMPTION_RULES)
    def test_gj01_B_check_actual_contract_to_accept(self):
        req=self.until('check','B');src=req['payload']['draft_index'];loc=list(src['candidates'])[-1];raw={}
        for q,contract in req['payload']['output_contract'].items():
            val='deny' if contract['kind']=='assess_proposition' else loc
            self.assertIn(val,contract['value_enum'])
            raw[q]=dict(zip(contract['fields'],[val,'deny' if q.startswith('OK.') else 'support',None,[loc]]))
        self.assertEqual(self.send(req,raw)['phase'],'revision')
    def test_gj02_check_context_and_each_finding_wire(self):
        req=self.until('check','C');qs=[DecisionSpec(**q) for q in req['payload']['questions']]
        project_context(qs,req['payload']);wire=jev_payload(req)
        self.assertEqual(len(wire['questions']),2)
        f=req['payload']['findings']['findings'][0]
        for q in qs:
            self.assertIn('finding_id='+f['finding_id'],q.question)
            self.assertIn(f['keep_exact_text'],q.question)
            self.assertIn(f['uncertainty'],q.question)
        broken=copy.deepcopy(req);del broken['payload']['findings']
        with self.assertRaises(ContractError):jev_payload(broken)
    def test_gj02_C_last_window_is_post_return_link_not_first(self):
        req=self.until('check','C');src=req['payload']['draft_index'];last=list(src['candidates'])[-1]
        self.assertNotEqual(last,next(iter(src['candidates'])))
        raw={q['id']:model_value(DecisionSpec(**q),last if q['id'].startswith('LOC.') else 'deny',[],'C')
             for q in req['payload']['questions']}
        end=self.send(req,raw);ok=end['check']['OK.inference']
        self.assertEqual(ok['basis_refs'],[last]);self.assertEqual(ok['basis_origin'],'runtime_post_return_LOC_link')
        self.assertEqual(end['phase'],'revision')
    def test_gj02_B_disjoint_basis_does_not_revise(self):
        req=self.until('check','B');ids=list(req['payload']['draft_index']['candidates']);raw={}
        for q in rt.check_specs(rt.state(self.root)):
            raw[q.id]=model_value(q,ids[-1] if q.id.startswith('LOC.') else 'deny',
                                  [ids[-1]] if q.id.startswith('LOC.') else [ids[0]],'B')
        end=self.send(req,raw)
        self.assertEqual(end['phase'],'done');self.assertEqual(end['check']['OK.inference']['unresolved_reason'],'check_conflict')
    def test_gj02_omission_none_deny_still_revises(self):
        req=self.until('check','B')
        raw={q.id:model_value(q,'none' if q.id.startswith('LOC.') else 'deny',[],'B')
             for q in rt.check_specs(rt.state(self.root))}
        self.assertEqual(self.send(req,raw)['phase'],'revision')
    def test_gj02_unknown_locator_never_revises(self):
        req=self.until('check','C');raw=simulated(req,rt.state(self.root),self.case)
        q='LOC.inference';raw[q]=self.lower(raw[q],raw[q]['value'])
        end=self.send(req,raw);self.assertEqual(end['phase'],'done')
        self.assertEqual(end['check']['OK.inference']['unresolved_reason'],'check_conflict')
    def test_gj03_low_none_not_deterministic_absence(self):
        req=self.until('round2','C');raw=simulated(req,rt.state(self.root),self.case)
        raw['E']=self.lower(raw['E'],'none');self.send(req,raw)
        req=rt.request(self.root);s=self.send(req,simulated(req,rt.state(self.root),self.case))
        self.assertEqual(s['atoms']['E']['value'],'none')
        self.assertEqual(s['atoms']['E']['unresolved_reason'],'low_confidence')
        self.assertNotEqual(s['atoms']['ES']['provenance'],'deterministic_absence')
        self.assertEqual(s['composition']['relation'],'limit')
    def test_gj03_high_none_normal_absence(self):
        self.until('draft','C');s=rt.state(self.root)
        self.assertEqual(s['atoms']['ES']['provenance'],'deterministic_absence')
        self.assertEqual(s['atoms']['ES']['value'],'missing')
    def test_gj03_low_ES_preserved_but_not_adopted(self):
        self.case['documents'][0]['origin']='direct'
        req=self.until('round2','C');raw=simulated(req,rt.state(self.root),self.case)
        src=rt.state(self.root)['source'];v=values(self.case,src)
        q=next(DecisionSpec(**q) for q in req['payload']['questions'] if q['id']=='E')
        raw['E']=model_value(q,v['P'],[],'C');self.send(req,raw)
        req=rt.request(self.root);raw=simulated(req,rt.state(self.root),self.case)
        q=next(DecisionSpec(**q) for q in req['payload']['questions'] if q['id']=='ES')
        raw['ES']=self.lower(model_value(q,'direct',[],'C'),'direct')
        end=self.send(req,raw);self.assertEqual(end['atoms']['ES']['value'],'direct')
        self.assertEqual(end['atoms']['ES']['semantic_state'],'unresolved')
        self.assertIsNone(end['composition']['findings'][0]['evidence_origin'])
    def test_gj04_normative_absence_vs_missing_wrong_low_basis(self):
        src=c.index(self.case['documents']);q=c.specs(src,1)[0];ids=list(src['candidates'])
        raw=model_value(q,'none',[ids[0]],'B');a=c.adapt(src,q,raw,'B',{})
        norm=self.norm(a)
        self.assertEqual(a['unresolved_reason'],'source_absence')
        self.assertEqual(c.score_atom(a,norm)['success'],1)
        for basis in ([],[ids[-1]]):
            other=c.adapt(src,q,model_value(q,'none',basis,'B'),'B',{})
            self.assertEqual(c.score_atom(other,norm)['success'],0)
        low=c.adapt(src,q,self.lower(model_value(q,'none',[],'C'),'none'),'C',{})
        self.assertEqual(c.score_atom(low,self.norm(low))['success'],0)
        self.assertEqual(c.score_atom(low,self.norm(low))['denominator'],1)
    def test_gj04_C_none_scope_not_fabricated_model_citation(self):
        src=c.index(self.case['documents']);q=c.specs(src,1)[0]
        a=c.adapt(src,q,model_value(q,'none',[],'C'),'C',{})
        self.assertEqual(a['basis_origin'],'runtime_full_source_scope')
        self.assertEqual(a['basis_refs'],list(src['candidates']))
        self.assertEqual(c.score_atom(a,self.norm(a))['success'],1)

    def target_with_relation(self, low=False):
        req=self.until('round3','C');raw=simulated(req,rt.state(self.root),self.case)
        qs={q['id']:DecisionSpec(**q) for q in req['payload']['questions']}
        raw['T']=model_value(qs['T'],'deny',[],'C')
        raw['TB']=model_value(qs['TB'],'different_G_C',[],'C')
        if low:raw['R']=self.lower(raw['R'],'overreach')
        return self.send(req,raw)
    def test_gj03_target_keeps_low_R_only_in_raw_and_limitations(self):
        s=self.target_with_relation(low=True);before=copy.deepcopy(s['atoms'])
        got=c.compose(s['source'],s['atoms'])
        self.assertEqual(got['goal'],'reanchor')
        self.assertEqual(got['relation'],'unresolved')
        self.assertEqual(len(got['findings']),1)
        self.assertEqual(got['findings'][0]['action'],'reanchor')
        self.assertIsNone(got['findings'][0]['relation'])
        self.assertEqual(got['limitations']['R'],'low_confidence')
        self.assertEqual(s['atoms']['R']['value'],'overreach')
        self.assertEqual(s['atoms'],before)
    def test_gj03_target_never_promotes_missing_or_invalid_R(self):
        s=self.target_with_relation()
        for replacement in (None,{**s['atoms']['R'],'semantic_state':'invalid','unresolved_reason':'contract_error'}):
            with self.subTest(replacement=replacement):
                atoms=copy.deepcopy(s['atoms'])
                if replacement is None:atoms.pop('R')
                else:atoms['R']=replacement
                got=c.compose(s['source'],atoms)
                self.assertEqual(got['goal'],'reanchor')
                self.assertEqual(len(got['findings']),1)
                self.assertIsNone(got['findings'][0]['relation'])
                if replacement is not None:self.assertEqual(got['limitations']['R'],'contract_error')
    def test_gj03_adopted_R_retained_for_target_and_inference(self):
        s=self.target_with_relation()
        for relation,action in (('overreach','limit'),('contradicts','recheck'),('sufficient','retain')):
            with self.subTest(relation=relation):
                atoms=copy.deepcopy(s['atoms']);atoms['R']['value']=relation
                atoms['S']['semantic_state']='support' if relation=='sufficient' else 'deny'
                got=c.compose(s['source'],atoms)
                self.assertEqual(got['goal'],'reanchor');self.assertEqual(got['relation'],action)
                self.assertTrue(all(f['relation']==relation for f in got['findings']))
                self.assertEqual(len(got['findings']),1 if relation=='sufficient' else 2)

if __name__=='__main__':unittest.main()
