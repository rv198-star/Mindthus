"""NONDEPLOYABLE test-only H1 keyring and signer. Never package under skills/."""
import copy
import hashlib
import hmac
import time
from unittest.mock import patch
from tplan_commands import canonical, digest

TEST_KEY = b'NONDEPLOYABLE synthetic H1 test fixture ONLY'
TEST_TRUST = {'mission_id':'h1-case', 'issuer_id': 'test-host', 'key_id': 'test-key', 'key': TEST_KEY,
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

# Fixed test-only acceptance scope. Shipped Host remains unconfigured.
TEST_TRUST['acceptance_actors'] = {'B': {
    'actor_subject_ref': 'test-reviewer', 'origin_binding_ref': 'review-binding',
    'origin_session_ref': 'review-session'}}


def acceptance_receipt(state, slot, **changes):
    """Synthetic authenticated review event AFTER the committed native result."""
    import tplan_runtime as runtime
    now = int(time.time())
    candidate = state['human_control']['candidates'][slot['result']['candidate_id']]
    ids = sorted(runtime._acceptance_coverage_for_task(state, slot['task_id']))
    criteria = sorted([a for a in state['mission']['acceptance_evidence'] if a['id'] in ids],
                      key=lambda a: a['id'])
    value = {'schema_version': 'tplan.acceptance_receipt.v0.1', 'issuer_id': 'test-host',
        'key_id': 'test-key', 'mission_id': state['mission']['id'], 'task_id': slot['task_id'],
        'slot_id': slot['slot_id'], 'session_id': slot['session_id'],
        'native_request_id': slot['native_request_id'], 'attempt_ref': slot['intent_id'],
        'candidate_id': candidate['candidate_id'], 'result_sha256': candidate['content_sha256'],
        'request_id': slot['request_id'], 'expected_revision': slot['expected_revision'],
        'decision_id': slot['decision_id'], 'adopted_candidate_id': slot['candidate_id'],
        'input_digest': slot['input_digest'], 'dependency_digest': slot['dependency_digest'],
        'delivery_digest': digest(slot['result']), 'acceptance_ids': ids,
        'acceptance_contract_digest': digest(criteria), **TEST_TRUST['acceptance_actors']['B'],
        'origin_event_ref': 'review-event-1', 'evidence_refs': ['review-report-1'],
        'summary': 'Synthetic reviewer verified actual B bytes against all declared criteria',
        'issued_at': now, 'expires_at': now + 120, 'nonce': 'acceptance-1'}
    value.update(changes)
    return signed(value)
