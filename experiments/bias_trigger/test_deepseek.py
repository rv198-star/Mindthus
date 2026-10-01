"""CPA boundary regressions; no credential, provider or CLI I/O."""
import copy
import json
import unittest
from . import run as r, deepseek as d
from .test_run import state


class CPAWire(unittest.TestCase):
    def setUp(self):
        self.adapter=d.CPAAdapters();self.s=state();self.item={'case_id':'case-01','input':'固定业务文本'}
        self.req=r.request(self.item,self.s,'A','draft',True,d.HOST)
        self.wire=self.adapter.outbound(self.req,{'host_configuration':d.HOST,'limits':{'logical':64,'host':56,'jev':8}})
    def reply(self,answer=None):
        answer=answer or {'kind':'answer','text':'首答','read_paths':[],'objection':''}
        return {'kind':'cpa_http_json','endpoint':d.ENDPOINT,'request_sha256':r.digest(self.wire['body']),
                'raw':{'model':d.HOST['model'],'choices':[{'finish_reason':'stop','message':{'content':json.dumps(answer)}}],'usage':{'prompt_tokens':10,'completion_tokens':5}}}
    def test_explicit_max_and_no_norm_or_other_answer(self):
        b=self.wire['body'];self.assertEqual(b['reasoning_effort'],'max');self.assertEqual(b['thinking'],{'type':'enabled'})
        self.assertFalse(b['stream']);self.assertEqual(b['model'],'deepseek-v4.1-flash')
        self.assertNotIn('norms',json.dumps(b));self.assertEqual(self.req,json.loads(json.dumps(self.req)))
    def test_complete_response_and_duplicate_local_contract(self):
        raw=self.reply();self.assertEqual(self.adapter.classify(self.req,raw)[0],'returned')
        bad=self.reply({'kind':'read','text':'','read_paths':['method','method'],'objection':''})
        self.assertEqual(self.adapter.classify(self.req,bad)[0],'failed')
        raw['raw']['model']='other';self.assertEqual(self.adapter.classify(self.req,raw)[3],'cpa_model_mismatch')
    def test_timeout_and_unbound_http_cannot_clear_unknown(self):
        err={'kind':'transport_error','code':'transport_failure','diagnostic':{'request_sha256':r.digest(self.wire['body']),'observed_stage':'response_body_read'}}
        self.assertEqual(self.adapter.classify(self.req,err)[0],'unknown')
        err['diagnostic'].update(http_response_received=True,http_status=403)
        self.assertEqual(self.adapter.classify(self.req,err)[0],'safety_refusal')
        err['diagnostic']['request_sha256']='another';self.assertEqual(self.adapter.classify(self.req,err)[0],'unknown')
    def test_b_c_use_same_host_and_candidates(self):
        r.consume(self.item,self.s,self.req,'returned',{'kind':'answer','text':'原始首答','read_paths':[],'objection':''},{})
        b=r.request(self.item,self.s,'B','detect',True,d.HOST);c=r.request(self.item,self.s,'C','detect',True,d.HOST)
        self.assertEqual(b['payload']['source'],c['payload']['source']);self.assertEqual(b['payload']['candidate'],c['payload']['candidate'])
        self.assertEqual(b['requested_configuration'],d.HOST)
        for arm in ('B','C'):
            self.s['arms'][arm]['atoms']={'Q_TARGET':{'semantic_state':'support'}}
            req=r.request(self.item,self.s,arm,'handling',True,d.HOST);self.assertEqual(req['requested_configuration'],d.HOST)
    def test_missing_terminal_and_refusal(self):
        raw=self.reply();raw['raw']['choices'][0].pop('finish_reason')
        self.assertEqual(self.adapter.classify(self.req,raw)[0],'unknown')
        raw=self.reply();raw['raw']['choices'][0]['finish_reason']='content_filter'
        self.assertEqual(self.adapter.classify(self.req,raw)[0],'safety_refusal')


if __name__=='__main__':unittest.main()
