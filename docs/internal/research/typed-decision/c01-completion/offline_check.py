import contextlib
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
s=importlib.util.spec_from_file_location('completion',Path(__file__).with_name('run.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class DriverChecks(unittest.TestCase):
    def simulate(self,fail=False):
        host=[];native=[]
        def host_wire(url,headers,body,timeout):
            host.append(body)
            return {'model':body['model'],'choices':[{'finish_reason':'length' if fail and len(host)==2 else 'stop',
                    'message':{'content':'offline answer'}}],'usage':{'prompt_tokens':20,'completion_tokens':10}}
        def native_wire(url,headers,body,timeout):
            native.append(body);values={'entry_mode':'mindthus_intervention','unresolved_obligation':'clear','owner':'wae','applicable':'yes'}
            return {'model':body['model'],'answers':{k:{'type':'choice','choice':values[k],'confidence':1.,
                    'probabilities':{o:float(o==values[k]) for o in q['criteria']}} for k,q in body['questions'].items()},
                    'usage':{'input_tokens':20,'output_tokens':10}}
        original=m.c01_host.TypeSafeJevProvider
        consume=m.c01_host.consume
        def factory(*a,**kw):kw['transport']=native_wire;return original(*a,**kw)
        def fake_consume(bundle,root,model,key,**kw):return consume(bundle,root,model,key,transport=host_wire)
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'TYPESAFE_API_KEY':'offline-only'}),patch.object(m.c01_host,'TypeSafeJevProvider',factory),patch.object(m.c01_host,'consume',fake_consume),contextlib.redirect_stdout(io.StringIO()):
            root=Path(d)/'trial';r=m.run(root,'offline-host')
            with self.assertRaises(Exception):m.run(root,'offline-host')
            return r,host,native

    def test_full_fixed_batch_and_real_chain_orchestration(self):
        r,host,native=self.simulate()
        self.assertTrue(r['complete']);self.assertTrue(r['cached_reentry_verified'])
        self.assertEqual((len(host),len(native)),(5,3))
        self.assertEqual(r['new_host_attempts'],5);self.assertEqual(r['new_jev_attempts'],3)
        self.assertIn('fallback_method_check',host[0]['messages'][1]['content'])
        self.assertEqual(r['rows'][-1]['routing']['owner'],'wae')

    def test_technical_failure_stops_before_fresh_routing(self):
        r,host,native=self.simulate(True)
        self.assertFalse(r['complete']);self.assertEqual(r['stop_reason'],'host_failed')
        self.assertEqual((len(host),len(native)),(2,0));self.assertEqual(r['unrun'],3)

if __name__=='__main__':unittest.main()
