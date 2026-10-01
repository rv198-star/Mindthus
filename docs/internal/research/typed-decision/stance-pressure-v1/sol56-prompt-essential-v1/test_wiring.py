"""Only this variant's outgoing messages, receipt binding and inherited scope."""
import importlib.util,unittest
from pathlib import Path
p=Path(__file__).with_name('EXECUTOR.py');s=importlib.util.spec_from_file_location('essential_variant',p)
e=importlib.util.module_from_spec(s);s.loader.exec_module(e)

class Wiring(unittest.TestCase):
    def request(self,messages,sequence=0):
        state=e.a.initial();state['calls']['A']=sequence
        return e.r.request({'case_id':e.case()['case_id'],'input':e.r.canonical(messages).decode()},state,'A','draft',False,e.HOST)
    def test_only_approved_business_messages(self):
        cfg={'host_configuration':e.HOST,'limits':e.LIMITS};a=e.Adapters()
        messages=[{'role':'user','content':e.case()['user_messages'][0]}]
        body=a.outbound(self.request(messages),cfg)['body']
        self.assertEqual(body['messages'],messages)
        self.assertEqual(set(body),{'model','reasoning_effort','max_completion_tokens','stream','messages'})
        self.assertEqual((body['model'],body['reasoning_effort'],body['max_completion_tokens']),('gpt-5.6-sol','medium',8192))
        self.assertNotIn('炒作',body['messages'][0]['content'])
        messages += [{'role':'assistant','content':'actual simulated first reply\n'},{'role':'user','content':e.case()['user_messages'][1]}]
        self.assertEqual(a.outbound(self.request(messages,1),cfg)['body']['messages'],messages)
        messages[2]['content']='old wording'
        with self.assertRaises(ValueError):a.outbound(self.request(messages,1),cfg)
    def test_plain_terminal_exact_binding_and_unknown(self):
        a=e.Adapters();req=self.request([{'role':'user','content':e.case()['user_messages'][0]}])
        wire=a.outbound(req,{'host_configuration':e.HOST,'limits':e.LIMITS})
        raw={'kind':'cpa_http_json','endpoint':wire['endpoint'],'request_sha256':e.r.digest(wire['body']),
             'raw':{'model':'gpt-5.6-sol','choices':[{'finish_reason':'stop','message':{'content':' answer\n'}}]}}
        self.assertEqual(a.classify(req,raw)[1]['text'],' answer\n')
        raw['request_sha256']='wrong';self.assertEqual(a.classify(req,raw)[0],'unknown')
        self.assertEqual(a.classify(req,{'kind':'transport_error','code':'TimeoutError','diagnostic':{'request_sha256':e.r.digest(wire['body'])}})[0],'unknown')
    def test_scope_inherits_consumed_budget(self):
        self.assertEqual(e.INHERITED,{'logical':73,'host':57,'jev':16})
        self.assertEqual({k:e.LIMITS[k]-e.INHERITED[k] for k in e.LIMITS},{'logical':2,'host':2,'jev':0})
        self.assertEqual(e.r.rt.read(e.prior.DOC/'summary.json')['cumulative_debits'],e.INHERITED)

if __name__=='__main__':unittest.main(verbosity=2)
