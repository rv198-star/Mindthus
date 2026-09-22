"""No-network controls for boundary/ablation v2; fixtures are not semantic evidence."""
from contextlib import ExitStack, redirect_stdout
from copy import deepcopy
import ast
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ablation_v2', HERE / 'run.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
from experiments.typed_decision.providers import TypeSafeJevProvider, FixtureProvider, ProviderError
from experiments.typed_decision.session import Session
from experiments.typed_decision.contracts import ContractError


class Checks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(m, 'ROOT', self.path / 'run'))
        self.stack.enter_context(patch.object(m, 'FREEZE', self.path / 'freeze.json'))
        self.stack.enter_context(patch.dict(os.environ, {
            'TYPESAFE_API_KEY': 'fixture-ts-only', 'MINDTHUS_HOST_API_KEY': 'fixture-host-only'}))
        self.cases = {r['id']: r for r in m.load_cases()}
        self.frozen = m.prepare()
        m.FREEZE.write_bytes(m.canonical(self.frozen))
        self.calls, self.host_calls = [], []

    def provider(self):
        def transport(url, headers, body, timeout):
            task = body['state']['original_task']
            case = task['provenance']['source_ref'].split(':')[1]
            questions = body['questions']
            self.calls.append((case, tuple(questions)))
            expected = self.cases[case]['expected_hits']
            answers = {}
            for q, definition in questions.items():
                value = m.assessment.CHECKS[q]['hit' if q in expected else 'fit']
                answers[q] = {'type': 'choice', 'choice': value, 'confidence': 1.0,
                    'probabilities': {k: float(k == value) for k in definition['criteria']}}
            return {'model': 'jev-1.13.0', 'answers': answers,
                    'usage': {'input_tokens': 100, 'output_tokens': 10}}
        return TypeSafeJevProvider(choice_rounding=True, transport=transport)

    def host(self, url, headers, body, timeout):
        self.host_calls.append(body)
        return {'model': m.HOST, 'usage': {'prompt_tokens': 100, 'completion_tokens': 10},
                'choices': [{'finish_reason': 'stop', 'message': {'content': '测试修正文本。'}}]}

    def execute(self, provider=None, host=None):
        with patch.object(m, 'post_json', host or self.host), redirect_stdout(io.StringIO()):
            return m.run(m.ROOT, provider=provider or self.provider(), host_key='fixture-host-only')

    def test_version_and_p3_preservation(self):
        self.assertEqual(m.assessment.VERSION, '2')
        original = subprocess.check_output(['git', 'show',
            'c1500da7d4f051420f73ae323c341a9db34b6142:experiments/typed_decision/assessment.py'], cwd=m.REPO, text=True)
        defs = next(n.value for n in ast.parse(original).body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'CHECKS' for t in n.targets))
        old = ast.literal_eval(defs)
        self.assertEqual(old['scope_preservation'], m.assessment.CHECKS['scope_preservation'])
        self.assertNotEqual(old['explanatory_scope'], m.assessment.CHECKS['explanatory_scope'])
        self.assertNotEqual(old['premise_treatment'], m.assessment.CHECKS['premise_treatment'])

    def test_identical_state_and_no_labels(self):
        for row in self.cases.values():
            views = []
            for arm in m.ARMS:
                p = m.Capture()
                m.assessment.assess(p, m.envelope(row, arm), m.REPO)
                views.append(m.canonical(p.view))
                self.assertEqual([s.id for s in p.specs], list(m.ARMS[arm]))
                self.assertNotIn('expected_hits', str(p.view))
                self.assertNotIn('quality_criteria', str(p.view))
                self.assertNotIn(row['purpose'], str(p.view))
            self.assertEqual(len(set(views)), 1)

    def test_physical_deletion_and_correction_counts(self):
        r = self.execute()
        self.assertIsNone(r['stop_reason'])
        self.assertEqual(r['counts'], {'detector': 32, 'corrector': 13})
        self.assertEqual(len(self.calls), 32)
        self.assertEqual(sum(len(qs) for _, qs in self.calls), 72)
        self.assertEqual(len(self.host_calls), 13)
        self.assertEqual(len(r['policy_projections']), 32)
        for row in r['rows']:
            if row['case_id'] == 'E07':
                self.assertEqual(row['action'], 'return_original_owner')
                self.assertIsNone(row['correction'])
                self.assertTrue(row['obligations'])
        self.assertFalse(r['qualification'])

    def test_completed_reentry_is_zero_call(self):
        first = self.execute()
        snapshot = {str(p): p.read_bytes() for p in m.ROOT.rglob('*.json')}
        count = len(self.calls), len(self.host_calls)
        again = self.execute()
        self.assertEqual(again, first)
        self.assertEqual(count, (len(self.calls), len(self.host_calls)))
        self.assertEqual(snapshot, {str(p): p.read_bytes() for p in m.ROOT.rglob('*.json')})

    def test_unknown_intent_stops_without_call(self):
        m.write_once(m.ROOT / 'E01' / 'full' / 'correction' / 'intent.json', {'id': 'unknown'})
        result = self.execute()
        self.assertEqual(result['stop_reason'], 'RecoveryRequired')
        self.assertFalse(self.calls or self.host_calls)

    def test_detector_failure_is_terminal(self):
        def fail(*a):
            raise ProviderError('transport_failure')
        r = self.execute(TypeSafeJevProvider(choice_rounding=True, transport=fail))
        self.assertEqual(r['counts'], {'detector': 1, 'corrector': 0})
        self.assertIsNotNone(r['stop_reason'])
        self.assertEqual(sum(row['status'] == 'unrun' for row in r['rows']), 31)

    def test_host_failure_no_retry(self):
        def fail(*a):
            raise ProviderError('transport_failure')
        r = self.execute(host=fail)
        self.assertEqual(r['counts'], {'detector': 32, 'corrector': 1})
        self.assertIsNotNone(r['stop_reason'])
        self.assertEqual(r['rows'][0]['correction']['status'], 'failed')

    def test_source_tampering_blocks_before_network(self):
        self.frozen['budget']['host_calls'] = 100
        m.FREEZE.write_bytes(m.canonical(self.frozen))
        with self.assertRaises(ContractError):
            self.execute()
        self.assertFalse(self.calls)

    def test_old_version_or_changed_state_cannot_be_corrected(self):
        row = self.cases['E01']
        data = m.envelope(row, 'full')
        p = FixtureProvider({q: m.assessment.CHECKS[q]['hit' if q == m.KEYS[0] else 'fit'] for q in m.KEYS})
        with Session(self.path / 'fixture', p, scope='version-check') as session:
            report = m.assessment.assess(session, data, m.REPO)
        stale = deepcopy(report)
        stale['identity']['graph']['version'] = '1'
        with self.assertRaises(ContractError):
            m.assessment.correction_request(stale, data, m.REPO)
        changed = deepcopy(data)
        changed['target']['text'] += ' changed'
        with self.assertRaises(ContractError):
            m.assessment.correction_request(report, changed, m.REPO)
        self.assertTrue(m.assessment.correction_request(report, data, m.REPO)['instructions'])

    def test_secret_reflection_does_not_enter_record(self):
        def reflection(*a):
            return {'model': m.HOST, 'choices': [{'finish_reason': 'stop', 'message': {
                'content': os.environ['MINDTHUS_HOST_API_KEY']}}]}
        r = self.execute(host=reflection)
        self.assertIsNotNone(r['stop_reason'])
        self.assertEqual(r['counts']['corrector'], 1)
        for p in m.ROOT.rglob('*.json'):
            self.assertNotIn(b'fixture-host-only', p.read_bytes())


if __name__ == '__main__':
    unittest.main()
