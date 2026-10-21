"""NONDEPLOYABLE test-only H1 keyring and signer. Never package under skills/."""
import copy
import hashlib
import hmac
import time
from unittest.mock import patch
from tplan_commands import canonical, digest

TEST_KEY = b'NONDEPLOYABLE synthetic H1 test fixture ONLY'
TEST_TRUST = {'issuer_id': 'test-host', 'key_id': 'test-key', 'key': TEST_KEY,
              'owner_subject_ref': 'test-owner', 'origin_binding_ref': 'test-origin',
              'origin_session_ref': 'test-session'}


def signed(value):
    result = copy.deepcopy(value)
    result['signature'] = hmac.new(TEST_KEY, canonical(value).encode(), hashlib.sha256).hexdigest()
    return result


def host_request(request):
    now = int(time.time())
    result = copy.deepcopy(request)
    result['host_receipt'] = signed({'issuer_id': 'test-host', 'key_id': 'test-key',
        'issued_at': now, 'expires_at': now + 120, 'nonce': 'host-' + request['command_id'],
        'request_digest': digest(request)})
    return result


def owner_receipt(mission, revision=1, choice='approve_current', candidate_sha256=None, nonce='owner-1', **changes):
    now = int(time.time())
    value = {'schema_version': 'tplan.owner_receipt.v0.1', 'issuer_id': 'test-host',
        'key_id': 'test-key', 'owner_subject_ref': 'test-owner', 'origin_binding_ref': 'test-origin',
        'mission_id': mission, 'request_id': 'HR1', 'expected_revision': revision,
        'choice': choice, 'candidate_sha256': candidate_sha256,
        'origin_session_ref': 'test-session', 'origin_event_ref': 'event-' + nonce,
        'issued_at': now, 'expires_at': now + 120, 'nonce': nonce}
    value.update(changes)
    return signed(value)


def isolated_test_host():
    return patch('tplan_h1_commands._trust_config', return_value=copy.deepcopy(TEST_TRUST))
