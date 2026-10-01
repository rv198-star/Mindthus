"""Only this minimal-message CPA boundary; no transport/model invocation."""
import importlib.util,json,unittest
from pathlib import Path
p=Path(__file__).with_name('EXECUTOR.py');spec=importlib.util.spec_from_file_location('sol56_cpa_entry',p)
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)

class EntryTests(unittest.TestCase):
    def make(self,second=False):
        state=e.a.initial();state['calls']['A']=int(second)
        messages=[{'role':'user','content':e.case()['user_messages'][0]}]
        if second:messages += [{'role':'assistant','content':'SIMULATED PRIOR TEXT'},{'role':'user','content':e.case()['user_messages'][1]}]
        req=e.r.request({'case_id':'offline','input':e.r.canonical(messages).decode()},state,'A','draft',False,e.HOST)
        return req,messages
    def test_exact_wire_excludes_all_context(self):
        for second in (False,True):
            req,messages=self.make(second);wire=e.Adapters().outbound(req,{'host_configuration':e.HOST,'limits':e.LIMITS})
            self.assertEqual(wire['body'],{'model':'gpt-5.6-sol','reasoning_effort':'medium','max_completion_tokens':8192,'stream':False,'messages':messages})
            self.assertNotIn('system',[m['role'] for m in wire['body']['messages']])
    def test_plain_answer_wrapped_only_after_return(self):
        req,_=self.make();adapter=e.Adapters();wire=adapter.outbound(req,{'host_configuration':e.HOST,'limits':e.LIMITS})
        raw={'kind':'cpa_http_json','endpoint':e.HOST['endpoint'],'request_sha256':e.r.digest(wire['body']),
             'raw':{'model':'gpt-5.6-sol','choices':[{'finish_reason':'stop','message':{'content':' raw text\n'}}]}}
        status,reply,_,_=adapter.classify(req,raw)
        self.assertEqual(status,'returned');self.assertEqual(reply['text'],' raw text\n')
        self.assertEqual(raw['raw']['choices'][0]['message']['content'],' raw text\n')
    def test_unknown_and_refusal_not_retryable(self):
        req,_=self.make();adapter=e.Adapters();sha=e.r.digest(adapter.outbound(req,{'host_configuration':e.HOST,'limits':e.LIMITS})['body'])
        self.assertEqual(adapter.classify(req,{'kind':'transport_error','code':'deadline_exceeded','diagnostic':{'request_sha256':sha}})[0],'unknown')
        self.assertEqual(adapter.classify(req,{'kind':'cpa_http_json','endpoint':e.HOST['endpoint'],'request_sha256':'other','raw':{}})[0],'unknown')
        raw={'kind':'cpa_http_json','endpoint':e.HOST['endpoint'],'request_sha256':sha,'raw':{'model':'gpt-5.6-sol','choices':[{'finish_reason':None,'message':{'content':'partial'}}]}}
        self.assertEqual(adapter.classify(req,raw)[0],'unknown')
        raw['raw']['choices'][0]['finish_reason']='content_filter'
        self.assertEqual(adapter.classify(req,raw)[0],'safety_refusal')
    def test_changed_question_or_context_rejected(self):
        req,_=self.make();req['payload']['readable_paths']=['anything']
        with self.assertRaises(ValueError):e.Adapters().outbound(req,{'host_configuration':e.HOST,'limits':e.LIMITS})
        req,_=self.make();req['payload']['source']['documents'][0]['text']=json.dumps([{'role':'user','content':'different question'}])
        with self.assertRaises(ValueError):e.Adapters().outbound(req,{'host_configuration':e.HOST,'limits':e.LIMITS})

if __name__=='__main__':unittest.main(verbosity=2)
