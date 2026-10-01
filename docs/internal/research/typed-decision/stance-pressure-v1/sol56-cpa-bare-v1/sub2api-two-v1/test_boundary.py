"""Bounded error receipt and this successor wire only; no live transmission."""
import importlib.util,io,json,unittest,urllib.error
from unittest.mock import patch
from pathlib import Path
p=Path(__file__).with_name('EXECUTOR.py');spec=importlib.util.spec_from_file_location('sub2api_entry',p)
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
from experiments.typed_decision.providers import _http_error_receipt
from experiments.typed_decision.providers import ProviderError
from experiments.typed_decision.relationship_live import deadline_post_json

class BoundaryTests(unittest.TestCase):
    def make(self):
        s=e.old.a.initial();item={'case_id':'offline','input':e.r.canonical([{'role':'user','content':e.old.case()['user_messages'][0]}]).decode()}
        return e.r.request(item,s,'A','draft',False,e.HOST)
    def test_safe_bounded_HTTP_body(self):
        secret='TEST_CREDENTIAL_0123456789'
        data={'error':{'type':'invalid_request_error','code':'unsupported_parameter','param':'max_completion_tokens','message':'Unsupported max_completion_tokens; use max_tokens. '+secret,'unrelated':{'private':'not_saved'}}}
        error=urllib.error.HTTPError(e.HOST['endpoint'],400,'Bad Request',{},io.BytesIO(json.dumps(data).encode()))
        receipt=_http_error_receipt(error,{'Authorization':'Bearer '+secret})
        self.assertEqual(set(receipt),{'body_status','type','code','param','message'})
        self.assertNotIn(secret,json.dumps(receipt));self.assertIn('max_tokens',receipt['message'])
        error=urllib.error.HTTPError(e.HOST['endpoint'],400,'Bad Request',{},io.BytesIO(b'x'*9000))
        self.assertEqual(_http_error_receipt(error,{}),{'body_status':'over_limit'})
    def test_HTTP_error_survives_existing_subprocess(self):
        secret='TEST_AUTH_1234567890'
        body={'model':'gpt-5.6-sol','messages':[]}
        data={'error':{'type':'invalid_request_error','param':'max_completion_tokens','message':'Use max_tokens; '+secret}}
        error=urllib.error.HTTPError(e.HOST['endpoint'],400,'Bad Request',{},io.BytesIO(json.dumps(data).encode()))
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.side_effect=error
            with self.assertRaises(ProviderError) as caught:
                deadline_post_json(e.HOST['endpoint'],{'Authorization':'Bearer '+secret},body,2)
        self.assertEqual(str(caught.exception),'http_400')
        self.assertEqual(caught.exception.diagnostic['request_sha256'],e.r.digest(body))
        receipt=caught.exception.diagnostic['http_error_response']
        self.assertEqual(receipt['param'],'max_completion_tokens')
        self.assertNotIn(secret,json.dumps(receipt))
    def test_bound_explicit_failure_unknown_and_refusal(self):
        req=self.make();a=e.Adapters();wire=a.outbound(req,{'host_configuration':e.HOST,'limits':e.LIMITS})
        self.assertEqual([x['role'] for x in wire['body']['messages']],['user']);self.assertEqual(wire['endpoint'],'https://sub2api.72live.com/v1/chat/completions')
        diag={'request_sha256':e.r.digest(wire['body']),'http_response_received':True,'http_status':400,'http_error_response':{'body_status':'json_error_object','type':'invalid_request_error'}}
        raw={'kind':'transport_error','code':'http_400','diagnostic':diag}
        self.assertEqual(a.classify(req,raw)[0],'failed')
        diag['request_sha256']='another';self.assertEqual(a.classify(req,raw)[0],'unknown')
        diag['request_sha256']=e.r.digest(wire['body']);diag['http_error_response']={};self.assertEqual(a.classify(req,raw)[0],'unknown')
        diag['http_status']=403;self.assertEqual(a.classify(req,raw)[0],'safety_refusal')
    def test_success_has_plain_exact_text(self):
        req=self.make();a=e.Adapters();wire=a.outbound(req,{'host_configuration':e.HOST,'limits':e.LIMITS})
        raw={'kind':'cpa_http_json','endpoint':wire['endpoint'],'request_sha256':e.r.digest(wire['body']),'raw':{'model':'gpt-5.6-sol','choices':[{'finish_reason':'stop','message':{'content':' exact answer\n'}}]}}
        self.assertEqual(a.classify(req,raw)[1]['text'],' exact answer\n')
        raw['raw']['model']='gpt-6.1-sol';self.assertEqual(a.classify(req,raw)[0],'failed')
    def test_parameter_fix_keeps_budget_and_messages(self):
        req=self.make();a=e.Adapters();cfg={'host_configuration':e.HOST,'limits':e.LIMITS};before=a.outbound(req,cfg)
        a.token_field='max_tokens'
        with self.assertRaises(ValueError):a.outbound(req,cfg)
        a.correction={'terminal_sha256':'offline'};after=a.outbound(req,cfg)
        self.assertEqual(after['body']['max_tokens'],8192);self.assertNotIn('max_completion_tokens',after['body'])
        self.assertEqual(before['body']['messages'],after['body']['messages']);self.assertEqual(after['body']['reasoning_effort'],'medium')

if __name__=='__main__':unittest.main(verbosity=2)
