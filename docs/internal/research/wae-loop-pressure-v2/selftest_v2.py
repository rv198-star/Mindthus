"""Offline controls only. No network/model calls. No official Skill changes."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest
from cases import CASES,BOUNDARIES,SLOTS,SCHEMA
import evaluation_v2 as E
import pressure_runner as R
from jsonschema import validate,ValidationError


def packet(action='refine',paths=None,code='',artifact='Draft after bounded work'):
    return dict(action=action,read_paths=paths or [],probe_code=code,artifact=artifact,
      reason='Check current response admission against supplied source',remaining=[],work_performed='Requested relevant source or updated rule')


def trial(name='F',arm='C'):
    c=R.get_case(name)
    return {'case':name,'arm':arm,'status':'pending','owner_calls':1,'owner_output_charged':0,
      'artifact':c['initial'],'owner_response':None,'observed':copy.deepcopy(c['preloaded']),
      'observations':[],'actions':[],'read_bytes':0}

class OracleTests(unittest.TestCase):
    def test_two_semantically_distinct_f_policies(self):
        a=E.check_f(E.F_REF_READONLY); b=E.check_f(E.F_REF_ANY)
        self.assertEqual(a['accepted_policies'],['published_read_only'])
        self.assertEqual(b['accepted_policies'],['current_any_view'])
    def test_wave1_both_policies_accepted(self):
        a=E.W1.F_REFERENCE_1
        b=a.replace("editable=role == 'editor' and rid == record['current_revision']","editable=role == 'editor' and view == 'working' and rid == record['current_revision']")
        self.assertTrue(E.wave1_corrected(a)['accepted'])
        self.assertTrue(E.wave1_corrected(b)['accepted'])
        self.assertEqual(E.W1.f_check(b)['passed'],45)
    def test_record_wide_badge_fails(self):
        bad=E.F_REF_READONLY.replace("'approved':rid==r['approved_revision']","'approved':r['approved_revision'] is not None")
        self.assertEqual(E.check_f(bad)['status'],'fail')
    def test_stale_key_fails(self):
        bad=E.F_REF_READONLY.replace("(p['record_key'],p['request_id'],p['revision_id'],p['text']) != (state['active_key'],state['active_request'],rid,text)","(p['request_id'],p['revision_id'],p['text']) != (state['active_request'],rid,text)")
        self.assertEqual(E.check_f(bad)['status'],'fail')
    def test_old_epoch_fails(self):
        bad=E.F_REF_READONLY.replace("(p['record_key'],p['request_id'],p['revision_id'],p['text']) != (state['active_key'],state['active_request'],rid,text)","(p['record_key'],p['revision_id'],p['text']) != (state['active_key'],rid,text)")
        self.assertEqual(E.check_f(bad)['status'],'fail')
    def test_corrupt_text_fails(self):
        bad=E.F_REF_READONLY.replace("(p['record_key'],p['request_id'],p['revision_id'],p['text']) != (state['active_key'],state['active_request'],rid,text)","(p['record_key'],p['request_id'],p['revision_id']) != (state['active_key'],state['active_request'],rid)")
        self.assertEqual(E.check_f(bad)['status'],'fail')
    def test_input_mutation_fails(self):
        bad=E.F_REF_READONLY.replace("r=state['record']","r=state['record']; state['active_key']='CHANGED'")
        self.assertEqual(E.check_f(bad)['status'],'fail')
    def test_unsafe_import_rejected(self):
        self.assertEqual(E.check_f('import os\n'+E.F_REF_READONLY)['status'],'fail')
    def test_public_and_hidden_separate(self):
        self.assertLess(len(E.tests('published_read_only',True)),len(E.tests('published_read_only')))
        self.assertEqual(E.check_f(E.F_REF_ANY,True)['status'],'pass')
    def test_k_fixed_source_behavior(self):
        # Execute authored fixture code only, no generated code or deployed service.
        ns={}; exec(CASES['K']['sources']['store.py'],ns)
        store=ns['LeaseStore'](); key=('a','j')
        self.assertEqual(store.begin(key,'d',0),1)
        self.assertEqual(store.begin(key,'d',20),'busy')
        self.assertEqual(store.begin(key,'d',30),2)
        self.assertEqual(store.finish(key,1,'r1'),'superseded')
        self.assertEqual(store.finish(key,2,'r2'),'done')
        self.assertEqual(store.begin(key,'d',31),'done')
        self.assertEqual(store.begin(('b','j'),'d',31),1)
        with self.assertRaises(ValueError): store.begin(key,'changed',32)
    def test_s_arithmetic(self):
        import csv,io
        rows=list(csv.DictReader(io.StringIO(CASES['S']['sources']['observations.csv'])))
        vals={p:[r for r in rows if r['period']==p] for p in ('before','after')}
        ratios={p:sum(int(r['completed']) for r in v)/sum(int(r['opportunities']) for r in v) for p,v in vals.items()}
        self.assertEqual(ratios['before'],0.5); self.assertAlmostEqual(ratios['after'],135/350)
        for name in ('standard','complex'):
            b=next(r for r in vals['before'] if r['segment']==name); a=next(r for r in vals['after'] if r['segment']==name)
            self.assertGreater(int(a['completed'])/int(a['opportunities']),int(b['completed'])/int(b['opportunities']))
    def test_s_missing_agreement_is_replaced(self):
        c=BOUNDARIES['S-missing']; self.assertEqual(c['expected'],'need_input')
        self.assertNotEqual(c['startup']['purpose'],CASES['S']['startup']['purpose'])
        self.assertNotEqual(c['receiver_task'],CASES['S']['receiver_task'])
        self.assertFalse(c['catalogue']); self.assertNotIn('three-page',c['owner_task'])
    def test_simulated_is_evaluation_obligation(self):
        self.assertIn('simulated',E.S_RUBRIC['S1'].lower())

class DriverTests(unittest.TestCase):
    def test_shape(self):
        validate(packet(),SCHEMA)
        with self.assertRaises(ValidationError): validate(dict(packet(),extra=1),SCHEMA)
    def test_whole_catalogue_may_be_read(self):
        for c in CASES.values():
            p=packet(paths=list(c['sources'])); R.validate_output(p,c)
            self.assertLess(sum(len(x.encode()) for x in c['sources'].values()),R.CONFIG['max_read_bytes_per_trial'])
    def test_no_mandated_refine(self):
        R.validate_output(packet('handoff'),CASES['F'])
    def test_source_injection_cannot_read_other_path(self):
        with self.assertRaises(ValueError): R.validate_output(packet(paths=['../auth.json']),CASES['F'])
    def test_terminal_with_unexecuted_work_rejected(self):
        with self.assertRaises(ValueError): R.validate_output(packet('handoff',['p1.md']),CASES['F'])
    def test_probe_scope(self):
        with self.assertRaises(ValueError): R.validate_output(packet(code='anything'),CASES['K'])
    def test_duplicate_request_path_rejected(self):
        with self.assertRaises(ValueError): R.validate_output(packet(paths=['p1.md','p1.md']),CASES['F'])
    def test_all_arms_same_data_and_limits(self):
        for arm in ('A','B','C'):
            p=R.prompt(trial(arm=arm)); self.assertIn('maximum_owner_requests\":3',p)
            self.assertIn('client-observation.txt',p)
            self.assertNotIn('response epoch 3 should return loading',p)
        self.assertEqual(len(SLOTS),12)
    def test_hidden_material_not_in_prompt(self):
        p=R.prompt(trial()); self.assertNotIn('F_REF_',p); self.assertNotIn('accepted_policies',p)
        self.assertNotIn('oracle',p.lower())
    def test_boundary_single_call(self):
        self.assertIn('maximum_owner_requests\":1',R.prompt(trial('S-missing')))
    def test_read_creates_exact_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp); (out/'call').mkdir(); t=trial()
            R.apply_work(out,t,packet(paths=['p1.md'],artifact=t['artifact']),'call')
            self.assertEqual(t['observed']['p1.md'],CASES['F']['sources']['p1.md'])
            self.assertEqual(t['status'],'owner_pending'); self.assertFalse(t['actions'][0]['artifact_changed'])
            self.assertEqual(t['observations'][0]['sha256'],R.T.sha(CASES['F']['sources']['p1.md'].encode()))
    def test_read_budget_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp); (out/'call').mkdir(); t=trial(); t['read_bytes']=R.CONFIG['max_read_bytes_per_trial']
            before=copy.deepcopy(t)
            with self.assertRaises(ValueError): R.apply_work(out,t,packet(paths=['p1.md']),'call')
            self.assertEqual(t,before)
    def test_need_input_does_not_start_recipient(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp); (out/'call').mkdir(); t=trial('S-missing')
            R.apply_work(out,t,packet('need_input',artifact='Missing approved facts.'),'call')
            self.assertEqual(t['status'],'need_input')
    def test_last_refine_not_forced_to_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp); (out/'call').mkdir(); t=trial(); t['owner_calls']=3
            R.apply_work(out,t,packet(),'call'); self.assertEqual(t['status'],'unconverged')
    def test_receiver_has_no_owner_trajectory(self):
        t=trial('K'); t['artifact']='Allowed package'; t['actions']=[{'secret':'SECRET_PREVIOUS_WORK'}]
        p=R.receiver_prompt(t); self.assertNotIn('SECRET_PREVIOUS_WORK',p); self.assertNotIn('def begin',p)
    def test_budget_limits_unchanged_by_new_trial(self):
        s={'blocked':None,'calls':40,'client_seconds':0,'started_epoch':__import__('time').time(),'output_charged':0}
        with self.assertRaises(RuntimeError): R.T.check_budget(s,100)
    def test_output_inside_repo_rejected(self):
        with self.assertRaises(ValueError): R.T.validate_out(R.REPO/'tmp/new-experiment')

if __name__=='__main__': unittest.main(verbosity=2)
