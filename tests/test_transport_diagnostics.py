"""Offline, real fork IPC; no network or business model requests."""
import errno
import http.client
import json
import os
from pathlib import Path
import ssl
import tempfile
import time
import unittest
import urllib.error
from unittest.mock import patch
from experiments.typed_decision import providers as p,relationship_live as live
from experiments.typed_decision import transport_diagnostics as d
from experiments.typed_decision.contracts import DecisionSpec,digest
from experiments.typed_decision.session import Session,read_record

SECRET='test-private-credential-do-not-persist'
BODY={'model':'jev-1.13.0','state':{'text':'fixture'},'questions':{}}
URL='https://example.invalid/v1/systemone'

class OfflineProvider(p.TypeSafeJevProvider):
    is_live=False
    def __init__(self):super().__init__(transport=live.deadline_post_json)

class DiagnosticTests(unittest.TestCase):
    def test_observed_connect_failure_retains_errno_without_secret(self):
        with patch.object(http.client.HTTPSConnection,'connect',side_effect=ConnectionRefusedError(errno.ECONNREFUSED,SECRET)):
            with self.assertRaises(p.ProviderError) as caught:p.post_json(URL,{'Authorization':'Bearer '+SECRET},BODY,1)
        self.assertEqual(str(caught.exception),'transport_failure')
        x=caught.exception.diagnostic
        self.assertEqual(x['exception_type'],'URLError');self.assertEqual(x['reason_type'],'ConnectionRefusedError')
        self.assertEqual(x['errno'],errno.ECONNREFUSED);self.assertEqual(x['generation_send_status'],'pre_send')
        self.assertEqual(x['observed_stage'],'connection_establishment_failed')
        self.assertEqual(x['provider_acceptance'],'unknown');self.assertNotIn(SECRET,json.dumps(x))

    def test_ssl_error_retains_numeric_code_without_message(self):
        error=ssl.SSLError(ssl.SSL_ERROR_SSL,SECRET)
        with patch.object(http.client.HTTPSConnection,'connect',side_effect=error):
            with self.assertRaises(p.ProviderError) as caught:p.post_json(URL,{},BODY,1)
        x=caught.exception.diagnostic
        self.assertEqual(x['ssl_error_code'],ssl.SSL_ERROR_SSL)
        self.assertEqual(x['reason_type'],'SSLError');self.assertNotIn(SECRET,json.dumps(x))

    def test_post_response_read_timeout_does_not_establish_remote_terminal(self):
        class Response:
            status=200
            headers={'x-request-id':SECRET,'Authorization':SECRET,'Set-Cookie':SECRET}
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,*args):raise TimeoutError(SECRET)
        class Opener:
            def open(self,*args,**kwargs):return Response()
        with patch.object(p.urllib.request,'build_opener',return_value=Opener()):
            with self.assertRaises(p.ProviderError) as caught:p.post_json(URL,{},BODY,1)
        x=caught.exception.diagnostic
        self.assertEqual(x['observed_stage'],'response_body_read');self.assertTrue(x['http_response_received'])
        self.assertEqual(x['generation_send_status'],'unknown');self.assertEqual(x['remote_terminal'],'unknown')
        self.assertEqual(set(x['response_identifiers_sha256']),{'x-request-id'})
        self.assertNotIn(SECRET,json.dumps(x));self.assertNotIn('Set-Cookie',json.dumps(x))

    def test_http_error_keeps_code_and_hashed_id_not_acceptance(self):
        class Opener:
            def open(self,*args,**kwargs):
                raise urllib.error.HTTPError(URL,401,SECRET,{'x-request-id':SECRET,'Cookie':SECRET},None)
        with patch.object(p.urllib.request,'build_opener',return_value=Opener()):
            with self.assertRaises(p.ProviderError) as caught:p.post_json(URL,{},BODY,1)
        self.assertEqual(str(caught.exception),'http_401')
        x=caught.exception.diagnostic
        self.assertEqual(x['http_status'],401);self.assertTrue(x['http_response_received'])
        self.assertEqual(x['provider_acceptance'],'unknown');self.assertNotIn(SECRET,json.dumps(x))

    def test_unobserved_urlerror_reason_cannot_claim_pre_send(self):
        class Opener:
            def open(self,*args,**kwargs):raise urllib.error.URLError(ConnectionRefusedError(errno.ECONNREFUSED,SECRET))
        with patch.object(p.urllib.request,'build_opener',return_value=Opener()):
            with self.assertRaises(p.ProviderError) as caught:p.post_json(URL,{},BODY,1)
        self.assertEqual(caught.exception.diagnostic['generation_send_status'],'unknown')

    def test_real_fork_preserves_diagnostic_and_session_binding_without_secrets(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'TYPESAFE_API_KEY':SECRET}),patch.object(http.client.HTTPSConnection,'connect',side_effect=ConnectionRefusedError(errno.ECONNREFUSED,SECRET)):
            root=Path(temp);spec=DecisionSpec('q','fixture',{'yes':'yes','no':'no'},('text',))
            with Session(root,OfflineProvider(),scope='offline-diagnostic') as session:
                result=session.evaluate([spec],{'text':'fixture'})
            self.assertEqual(result['q'].reason,'ProviderError:transport_failure')
            record=read_record(next(root.glob('calls/*/transport-diagnostic.json')))
            intent=read_record(next(root.glob('calls/*/intent.json')))
            self.assertEqual(record['call_key'],intent['call_key']);self.assertEqual(record['intent_sha256'],digest(intent))
            self.assertEqual(record['diagnostic']['errno'],errno.ECONNREFUSED)
            self.assertEqual(record['diagnostic']['generation_send_status'],'pre_send')
            self.assertLessEqual(record['diagnostic']['started_at'],record['diagnostic']['ended_at'])
            expected={'model':'jev-1.13.0','state':{'text':'fixture'},'questions':OfflineProvider().engine.questions([spec])}
            self.assertEqual(record['diagnostic']['request_sha256'],digest(expected))
            for file in root.rglob('*.json'):self.assertNotIn(SECRET,file.read_text())

    def test_worker_deadline_remains_unknown(self):
        def stall(*args):time.sleep(.3)
        with patch.object(live,'post_json',side_effect=stall):
            with self.assertRaises(p.ProviderError) as caught:live.deadline_post_json(URL,{},BODY,.03)
        self.assertEqual(str(caught.exception),'deadline_exceeded')
        self.assertEqual(caught.exception.diagnostic['observed_stage'],'parent_worker_wait')
        self.assertEqual(caught.exception.diagnostic['generation_send_status'],'unknown')

if __name__=='__main__':unittest.main()
