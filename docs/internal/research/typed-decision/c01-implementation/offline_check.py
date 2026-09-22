"""Verify targeted scoring and native-only bounded carrier without network."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
s=importlib.util.spec_from_file_location('targeted',Path(__file__).with_name('run.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class Checks(unittest.TestCase):
    def test_final_fallback_requires_observed_applicability_rejection(self):
        case={'accepted':[{'route':'llm_fallback','owner':None}],'node_checks':{'applicable':'no'}}
        report={'result':{'route':'llm_fallback','owner':None,'status':'abstain'}}
        self.assertFalse(m.score(case,report,[])['passed'])
        self.assertTrue(m.score(case,report,[{'results':{'applicable':{'status':'ok','value':'no'}}}])['passed'])
        self.assertFalse(m.score(case,report,[{'results':{'applicable':{'status':'provider_error','value':'no'}}}])['passed'])

    def simulate(self,drift=False):
        calls=[]
        def fake(url,headers,body,timeout):
            self.assertIn('typesafe',url)
            self.assertNotIn('messages',body)
            self.assertNotIn('accepted',body['state'])
            self.assertNotIn('node_checks',body['state'])
            self.assertGreater(timeout,0);self.assertLessEqual(timeout,60)
            calls.append(body)
            values={'entry_mode':'direct_execution','unresolved_obligation':'clear','applicable':'no'}
            return {'model':'jev-9.9.9' if drift and len(calls)>1 else body['model'],
                    'answers':{k:{'type':'choice','choice':values[k],'confidence':1.,
                        'probabilities':{o:float(o==values[k]) for o in q['criteria']}} for k,q in body['questions'].items()},
                    'usage':{'input_tokens':100,'output_tokens':20}}
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'TYPESAFE_API_KEY':'offline-fixture'}),patch.object(m,'post_json',fake),contextlib.redirect_stdout(io.StringIO()):
            root=Path(d)/'trial';r=m.run(root)
            with self.assertRaises(Exception):m.run(root)
            self.assertEqual(r['calls'],len(calls))
            return r

    def test_complete_fixed_plan_without_gold_egress_or_sonnet(self):
        r=self.simulate()
        self.assertTrue(r['complete']);self.assertEqual(len(r['rows']),14)
        self.assertLess(r['passed'],14)
        l27=next(x for x in r['rows'] if x['case_id']=='L27')
        self.assertEqual(l27['observed']['entry_mode'],'direct_execution')
        self.assertEqual(l27['result']['entry_mode'],'mindthus_intervention')
        self.assertEqual(l27['observed']['applicable'],'no')
        self.assertFalse(next(x for x in r['rows'] if x['case_id']=='N04')['passed'])

    def test_runtime_drift_stops_and_is_not_correct_fallback(self):
        r=self.simulate(True)
        self.assertFalse(r['complete']);self.assertEqual(r['calls'],2)
        self.assertEqual(r['stop_reason'],'technical_failure')
        self.assertFalse(r['rows'][-1]['passed'])

if __name__=='__main__':unittest.main()
