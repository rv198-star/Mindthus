"""Bounded observations on the existing urllib HTTPS transport, not retry authority."""
from datetime import datetime, timezone
import hashlib
import http.client
import socket
import ssl
import time
import urllib.error
import urllib.request
from .contracts import digest


def now():
    return datetime.now(timezone.utc).isoformat()


def exception_type(exc):
    # Never serialize repr/message or an arbitrary user-defined class name.
    for cls in (urllib.error.HTTPError, urllib.error.URLError, ssl.SSLCertVerificationError,
                ssl.SSLError, socket.gaierror, ConnectionRefusedError, ConnectionResetError,
                BrokenPipeError, TimeoutError, EOFError, UnicodeDecodeError, ValueError, OSError):
        if isinstance(exc, cls):return cls.__name__
    return 'OtherException' if exc is not None else None


def integer(value):
    return int(value) if isinstance(value,int) and not isinstance(value,bool) and -(2**31)<=value<2**31 else None


class Observation:
    def __init__(self, body):
        self.started_at=now();self.began=time.monotonic();self.request_sha256=digest(body)
        self.stage='http_open';self.events=[];self.pre_send=False
        self.response_received=False;self.http_status=None;self.ids={}

    def at(self, stage):
        self.stage=stage
        if len(self.events)<16:self.events.append(stage)

    def response(self, status, headers):
        self.response_received=True;self.http_status=integer(status)
        self.at('response_headers_received')
        # Hash allowlisted identifiers: neither arbitrary headers nor reflected secrets persist.
        for key in ('x-request-id','request-id','x-correlation-id','cf-ray'):
            value=headers.get(key) if headers is not None else None
            if isinstance(value,str) and 0<len(value)<=256:
                self.ids[key]={'sha256':hashlib.sha256(value.encode()).hexdigest()}

    def failure(self, exc):
        reason=exc.reason if isinstance(exc,urllib.error.URLError) else None
        inner=reason if isinstance(reason,BaseException) else exc
        return {'schema':'mindthus.transport-diagnostic.v1','request_sha256':self.request_sha256,
                'started_at':self.started_at,'ended_at':now(),'local_elapsed_seconds':time.monotonic()-self.began,
                'exception_type':exception_type(exc),'reason_type':exception_type(reason) if isinstance(reason,BaseException) else ('str' if isinstance(reason,str) else None),
                'errno':integer(getattr(inner,'errno',None)),
                'ssl_error_code':integer(getattr(inner,'errno',None)) if isinstance(inner,ssl.SSLError) else None,
                'ssl_verify_code':integer(getattr(inner,'verify_code',None)) if isinstance(inner,ssl.SSLCertVerificationError) else None,
                'observed_stage':self.stage,'stage_events':list(self.events),
                'http_response_received':self.response_received,'http_status':self.http_status,
                'response_identifiers_sha256':self.ids,
                'generation_send_status':'pre_send' if self.pre_send else 'unknown',
                'pre_send_basis':'HTTPSConnection.connect raised before generation HTTP write' if self.pre_send else None,
                'provider_acceptance':'unknown','remote_terminal':'unknown'}


class ObservedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, *args, observation, **kwargs):
        self.observation=observation
        super().__init__(*args,**kwargs)

    def connect(self):
        self.observation.at('connection_establishment')
        try:super().connect()
        except OSError:
            self.observation.pre_send=True
            self.observation.at('connection_establishment_failed')
            raise
        self.observation.at('connection_established')

    def send(self, data):
        # Establish before generation write; proxy CONNECT/TLS are connection setup.
        if self.sock is None and self.auto_open:self.connect()
        self.observation.at('request_write')
        super().send(data)
        self.observation.at('local_write_returned')  # not evidence of provider acceptance

    def getresponse(self):
        self.observation.at('response_headers_wait')
        return super().getresponse()


class ObservedHTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(self, observation):
        super().__init__();self.observation=observation

    def https_open(self, req):
        def connection(*args, **kwargs):
            return ObservedHTTPSConnection(*args,observation=self.observation,**kwargs)
        return self.do_open(connection,req,context=self._context)
