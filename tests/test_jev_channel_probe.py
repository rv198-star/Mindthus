"""Offline tests for diagnostics only; no provider or business calls."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
import urllib.error

from experiments.diagnostics import jev_channel_probe as p
from experiments.typed_decision.contracts import ContractError
from experiments.typed_decision.session import read_record, write_once, RecoveryRequired
from experiments.typed_decision.providers import ProviderError


class ProbeTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / 'probe'
        self.key = 'fixture-credential-never-a-real-key'
        self.env = patch.dict(os.environ, {'TYPESAFE_API_KEY': self.key, 'OPENROUTER_API_KEY': self.key})
        self.env.start(); self.addCleanup(self.env.stop)
        p.prepare(self.root, 'typesafe', 'node-fixture')
        self.count = 0

    def valid(self, url, headers, request, timeout):
        self.count += 1
        self.assertEqual(headers['Authorization'], 'Bearer ' + self.key)
        return {'model': request['model'], 'provider': 'TypeSafe', 'usage': {'input_tokens': 15, 'output_tokens': 4},
                'echo': self.key, 'answers': {
                    'intent': {'type': 'choice', 'choice': 'thanks', 'confidence': 1,
                               'probabilities': {'thanks': 1, 'request': 0}},
                    'resolved': {'type': 'noul', 'noul': 1},
                    'urgency': {'type': 'score', 'score': 0, 'confidence': 1,
                                'probabilities': {'0': 1, '1': 0, '2': 0},
                                'legend': {str(i): x for i, x in enumerate(p.specs()[2].criteria)}},
                }}

    def test_plan_contains_exact_command_and_redacted_env(self):
        plan = read_record(self.root / 'typesafe/outer-plan.json')
        self.assertEqual(plan['outer_arguments_redacted']['workdir'], str(p.REPO))
        self.assertIn('--channel typesafe', plan['outer_arguments_redacted']['cmd'])
        self.assertEqual(list(plan['outer_arguments_redacted']['env']), ['TYPESAFE_API_KEY'])
        self.assertNotIn(self.key, json.dumps(plan))
        self.assertIn('stdin', plan['omitted_optional_outer_fields'])

    def test_both_probes_have_same_state_and_questions(self):
        p.prepare(self.root, 'openrouter', 'node-fixture')
        a = read_record(self.root / 'typesafe/request.json'); b = read_record(self.root / 'openrouter/request.json')
        self.assertEqual(a['state'], b['state']); self.assertEqual(a['questions'], b['questions'])
        self.assertNotEqual(a['model'], b['model'])

    def test_success_and_reentry_do_not_repeat(self):
        out = p.run(self.root, 'typesafe', transport_override=self.valid)
        self.assertEqual(out['http_status'], 200); self.assertTrue(out['all_three_contracts_valid'])
        self.assertEqual(out, p.run(self.root, 'typesafe', transport_override=self.valid))
        self.assertEqual(self.count, 1)

    def test_openrouter_independent_entry(self):
        p.prepare(self.root, 'openrouter', 'node-fixture')
        out = p.run(self.root, 'openrouter', transport_override=self.valid)
        self.assertEqual(out['resolved_runtime']['model'], 'typesafe/jev-1.13')
        self.assertFalse((self.root / 'typesafe/intent.json').exists())

    def test_no_secret_in_request_outcome_or_receipt(self):
        p.run(self.root, 'typesafe', transport_override=self.valid)
        for path in self.root.rglob('*.json'):
            self.assertNotIn(self.key, path.read_text())
        receipt = read_record(self.root / 'typesafe/provider-receipt.json')
        self.assertEqual(receipt['response']['echo'], '[REDACTED]')

    def test_missing_credential_makes_no_external_call(self):
        with patch.dict(os.environ, {}, clear=True):
            out = p.run(self.root, 'typesafe', transport_override=self.valid)
        self.assertEqual(out['external_attempts'], 0); self.assertEqual(self.count, 0)
        self.assertFalse((self.root / 'typesafe/intent.json').exists())

    def test_unknown_call_not_reissued(self):
        write_once(self.root / 'typesafe/intent.json', {'state': 'unknown'})
        with self.assertRaises(RecoveryRequired): p.run(self.root, 'typesafe', transport_override=self.valid)
        self.assertEqual(self.count, 0)

    def test_unauthorized_channel_rejected(self):
        with self.assertRaises(ContractError): p.prepare(self.root, 'other', 'node-fixture')

    def test_request_changed_is_rejected(self):
        path = self.root / 'typesafe/request.json'; body = read_record(path); body['state']['message'] = 'changed'
        path.unlink(); write_once(path, body)
        with self.assertRaises(ContractError): p.run(self.root, 'typesafe', transport_override=self.valid)
        self.assertEqual(self.count, 0)

    def test_http_error_recorded_and_no_fallback(self):
        opener = Mock(); opener.open.side_effect = urllib.error.HTTPError('https://api.typesafe.ai/v1/systemone', 403, 'denied', {}, None)
        with patch.object(p.urllib.request, 'build_opener', return_value=opener):
            out = p.run(self.root, 'typesafe')
        self.assertEqual(out['http_status'], 403); self.assertTrue(out['http_response_received'])
        self.assertFalse((self.root / 'openrouter').exists())

    def test_network_failure_not_http_failure(self):
        opener = Mock(); opener.open.side_effect = urllib.error.URLError('offline')
        with patch.object(p.urllib.request, 'build_opener', return_value=opener): out = p.run(self.root, 'typesafe')
        self.assertIsNone(out['http_status']); self.assertFalse(out['http_response_received'])

    def test_invalid_model_recorded_not_success(self):
        def bad(*args):
            raw = self.valid(*args); raw['model'] = 'other'; return raw
        out = p.run(self.root, 'typesafe', transport_override=bad)
        self.assertEqual(out['status'], 'provider_or_contract_error')
        self.assertEqual(out['http_status'], 200)

    def test_one_invalid_answer_does_not_erase_valid_return(self):
        def bad(*args):
            raw = self.valid(*args); raw['answers']['urgency']['score'] = 2; return raw
        out = p.run(self.root, 'typesafe', transport_override=bad)
        self.assertEqual(out['status'], 'inference_returned'); self.assertFalse(out['all_three_contracts_valid'])
        self.assertEqual(out['results']['intent']['status'], 'ok')


if __name__ == '__main__': unittest.main()
