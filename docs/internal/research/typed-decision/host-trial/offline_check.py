import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
s=importlib.util.spec_from_file_location('host_run',Path(__file__).with_name('run.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class HostChecks(unittest.TestCase):
    def simulate(self,fail=None):
        calls=[]
        def fake(url,headers,body,timeout):
            self.assertEqual(url,m.ENDPOINT);self.assertEqual(body['model'],'deepseek-v4.1-flash')
            self.assertNotIn('tools',body);self.assertLessEqual(timeout,60)
            self.assertEqual(body['max_tokens'],1600);calls.append(body)
            model='glm-5.3-flash' if fail=='model' and len(calls)==2 else m.MODEL
            return {'model':model,'choices':[{'finish_reason':'length' if fail=='length' else 'stop',
                    'message':{'content':'offline useful response','reasoning_content':'DO NOT PERSIST REASONING'}}],
                    'usage':{'prompt_tokens':100,'completion_tokens':20,'cost':.001}}
        with tempfile.TemporaryDirectory() as d,patch.object(m,'post_json',fake),contextlib.redirect_stdout(io.StringIO()):
            root=Path(d)/'trial';r=m.run(root,'offline-secret')
            with self.assertRaises(Exception):m.run(root,'offline-secret')
            for f in root.rglob('*.json'):
                self.assertNotIn('offline-secret',f.read_text());self.assertNotIn('DO NOT PERSIST REASONING',f.read_text())
            self.assertEqual(len(calls),r['attempts']);return r

    def test_complete_without_keys_reasoning_or_false_currency(self):
        r=self.simulate();self.assertTrue(r['complete']);self.assertEqual(r['attempts'],6)
        self.assertTrue(all(x['cost_usd'] is None for x in r['rows']))
        self.assertFalse(r['qualification'])

    def test_truncation_stops_without_pretending_answer_completed(self):
        r=self.simulate('length');self.assertFalse(r['complete']);self.assertEqual(r['attempts'],1)
        self.assertEqual(r['unrun'],5);self.assertIsNone(r['rows'][0]['answer'])

    def test_model_switch_is_failure_not_automatic_backup(self):
        r=self.simulate('model');self.assertEqual(r['attempts'],2)
        self.assertEqual(r['stop_reason'],'technical_failure');self.assertIsNone(r['rows'][-1]['answer'])

if __name__=='__main__':unittest.main()
