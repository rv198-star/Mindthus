#!/usr/bin/env python3
"""Zero-model G0 checks. Test outputs live only in temporary directories."""
import copy
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from jsonschema import validate
import cases
import oracle
import run

class OracleTests(unittest.TestCase):
    def test_references_both_policies(self):
        for ref in (oracle.REFERENCE,oracle.REFERENCE_2):
            for policy in ('READ_ONLY','EDIT_CURRENT'):
                r=oracle.check(ref,policy); self.assertEqual('pass',r['status'],r)
    def test_policies_are_behaviorally_different(self):
        a=oracle.suite('READ_ONLY'); b=oracle.suite('EDIT_CURRENT')
        self.assertNotEqual(a,b)
        for name in ('select-A-reader-working','ABA','failed-save'):
            self.assertEqual(next(t for t in a if t['name']==name),next(t for t in b if t['name']==name))
    def bad(self,old,new):
        self.assertIn(old,oracle.REFERENCE)
        r=oracle.check(oracle.REFERENCE.replace(old,new),'READ_ONLY')
        self.assertNotEqual(r['status'],'pass',r)
        return r
    def test_stale_epoch_rejected(self):
        self.bad("or p['epoch']!=state['epoch']",'')
    def test_corrupted_text_rejected(self):
        self.bad("or p['text']!=text",'')
    def test_other_record_rejected(self):
        self.bad("or p['record']!=key",'')
    def test_late_response_cannot_erase_current(self):
        self.bad("out['packet']=prior","out['packet']=None")
    def test_record_wide_badge_rejected(self):
        self.bad("approved=target==rec['approved']","approved=rec['approved'] is not None")
    def test_scope_shrink_rejected(self):
        self.bad("if kind=='select':","if kind=='discard':")
    def test_approval_mutation_rejected(self):
        self.bad("rec['current']=event['new_rev'];", "rec['current']=event['new_rev']; rec['approved']=event['new_rev'];")
    def test_failed_save_does_not_write(self):
        self.bad("elif not event['ok']:","elif False:")
    def test_permission_cannot_be_dropped(self):
        self.bad("if not screen(state,published_policy)['can_edit']:","if False:")
    def test_input_mutation_rejected(self):
        self.bad("out=copy_state(state);", "out=state;")
    def test_surface_truth_invariant(self):
        self.bad("result.update(status='ready'", "result.update(status='ready' if surface=='detail' else 'empty'")
    def test_public_distinct_from_hidden(self):
        public=oracle.suite('READ_ONLY',True); all_=oracle.suite('READ_ONLY')
        self.assertEqual(len(public),3); self.assertGreater(len(all_),len(public))
        self.assertNotIn('ABA',[x['name'] for x in public])
        self.assertEqual('pass',oracle.check(oracle.REFERENCE,'READ_ONLY',True)['status'])
    def test_imports_rejected(self):
        self.assertEqual('execution_error',oracle.check('import os\n'+oracle.REFERENCE,'READ_ONLY')['status'])
    def test_missing_policy_not_guessed(self):
        self.assertEqual('missing_owner_policy',oracle.check(oracle.REFERENCE,'')['status'])

class DriverTests(unittest.TestCase):
    def trial(self,key='F2',arm='C'):
        return {'case':key,'arm':arm,'status':'pending','owner_calls':1,'owner_output_charged':0,
          'artifact':cases.CASES[key]['initial'],'policy':cases.CASES[key]['initial_policy'] or '',
          'owner_results':[],'observations':[],'actions':[]}
    def response(self,action='handoff',policy='READ_ONLY',probe=''):
        return dict(action=action,artifact='A real current plan.',reason='Bounded public obligations.',remaining=[],
          work_performed='Specified a relation.',published_policy=policy,probe_code=probe)
    def apply(self,t,p):
        with tempfile.TemporaryDirectory(prefix='wae-g0-') as d:
            out=Path(d); (out/'call').mkdir(); run.apply(out,t,p,'call')
    def test_no_case_labels_or_expected_routes_in_model_context(self):
        for c in cases.CASES:
            text=run.prompt(self.trial(c)); self.assertNotIn('expected_route',text); self.assertNotIn('RUBRIC',text)
            self.assertNotIn('REFERENCE =',text); self.assertNotIn('oracle.py',text)
    def test_equal_data_for_arms(self):
        for c in cases.CASES:
            b=run.prompt(self.trial(c,'B')); d=run.prompt(self.trial(c,'C'))
            self.assertEqual(b.split('ADMITTED TASK\n')[1],d.split('ADMITTED TASK\n')[1])
            self.assertNotEqual(b.split('ADMITTED TASK\n')[0],d.split('ADMITTED TASK\n')[0])
    def test_real_treatment_not_label_only(self):
        b=run.prompt(self.trial(arm='B')); c=run.prompt(self.trial(arm='C'))
        guide=(run.OLD/'candidate.md').read_text()
        self.assertIn(guide,c); self.assertNotIn(guide,b)
        self.assertNotIn('Both must hold',run.COMMON)
        self.assertIn('guidance-strategy',run.CONFIG['treatment'])
    def test_handoff_launches_real_recipient(self):
        t=self.trial(); self.apply(t,self.response()); self.assertEqual('receiver_pending',t['status'])
    def test_no_minimum_round(self):
        t=self.trial('F0'); p=self.response(); p['artifact']=t['artifact']; self.apply(t,p)
        self.assertFalse(t['actions'][0]['artifact_changed']); self.assertEqual('receiver_pending',t['status'])
    def test_need_input_never_launches_receiver(self):
        t=self.trial('F3'); self.apply(t,self.response('need_input','')); self.assertEqual('need_input',t['status'])
    def test_stop_preserves_partial(self):
        t=self.trial(); self.apply(t,self.response('stop')); self.assertEqual('stop',t['status'])
    def test_last_refine_is_unconverged(self):
        t=self.trial(); t['owner_calls']=3; self.apply(t,self.response('refine')); self.assertEqual('unconverged',t['status'])
    def test_terminal_with_probe_rejected(self):
        with self.assertRaises(ValueError): self.apply(self.trial(),self.response(probe=oracle.REFERENCE))
    def test_probe_binds_version_without_hidden_feedback(self):
        t=self.trial(); self.apply(t,self.response('refine',probe=oracle.REFERENCE))
        obs=t['observations'][0]; self.assertEqual('pass',obs['result']['status'])
        self.assertEqual(3,obs['result']['trace_count']); self.assertEqual(run.T.sha(oracle.REFERENCE.encode()),obs['candidate_sha256'])
    def test_empty_policy_handoff_rejected(self):
        with self.assertRaises(ValueError): self.apply(self.trial(),self.response(policy=''))
    def test_external_authority_truly_replaced(self):
        c=cases.CASES['F3']; self.assertNotIn('is a P2 choice',c['sources']['P1'])
        self.assertIn('reserved to the product owner',c['sources']['P1'])
        self.assertNotIn('Published policy is READ_ONLY.',c['initial'])
    def test_references_are_accessible(self):
        for key in ('F0','F1','F2'):
            c=cases.CASES[key]; self.assertEqual(c['sources'],c['receiver_sources'])
            for ref in ('P1','host','goals','api'): self.assertTrue(c['sources'][ref].strip())
    def test_recipient_does_not_see_trajectory_or_label(self):
        t=self.trial(); t['actions']=[{'reason':'PRIVATE_TRAJECTORY'}]
        text=run.receiver_prompt(t); self.assertNotIn('PRIVATE_TRAJECTORY',text); self.assertNotIn('WORKING GUIDANCE',text)
    def test_resource_bounds(self):
        good={'blocked':None,'calls':0,'client_seconds':0,'started_epoch':time.time(),'output_charged':0}
        run.T.check_budget(good,6000)
        for field,value in [('calls',27),('client_seconds',1800),('output_charged',200000),('started_epoch',0)]:
            bad={**good,field:value}
            with self.assertRaises(RuntimeError): run.T.check_budget(bad,6000)
    def test_write_once_preserves_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x'; run.T.once(p,b'original')
            with self.assertRaises(FileExistsError): run.T.once(p,b'new')
            self.assertEqual(b'original',p.read_bytes())
    def test_project_output_rejected(self):
        with self.assertRaises(ValueError): run.T.validate_out(run.REPO/'tmp-g0')
    def test_action_schema(self):
        p=self.response(); validate(p,cases.OWNER_SCHEMA)
        p['action']='auto_pass'
        with self.assertRaises(Exception): validate(p,cases.OWNER_SCHEMA)
    def test_freeze_detects_input_and_manifest_drift(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d); m={'inputs':run.T.identities(),'config':run.CONFIG,'slots':[{'case':c,'arm':a} for c,a in cases.SLOTS]}
            m['manifest_sha256']=run.T.sha(run.T.canonical(m)); run.T.once(out/'manifest.json',m)
            run.T.save_state(out,{'trials':[{'case':c,'arm':a} for c,a in cases.SLOTS]})
            run.validate_freeze(out)
            with patch.object(run.T,'identities',return_value={'different':'version'}):
                with self.assertRaises(ValueError): run.validate_freeze(out)
            m['manifest_sha256']='0'*64; (out/'manifest.json').write_text(json.dumps(m))
            with self.assertRaises(ValueError): run.validate_freeze(out)

if __name__=='__main__': unittest.main(verbosity=2)
