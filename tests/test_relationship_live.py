"""D3 controls: all transports here are scripted, never live-model quality evidence."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from experiments.typed_decision import entry, relationship_assessment as rel, relationship_runtime as rt, relationship_live as live
from experiments.typed_decision.contracts import ContractError, canonical, digest, provider_configuration
from experiments.typed_decision.providers import ProviderError
from experiments.typed_decision.session import RecoveryRequired, implementation_digest, read_record
from tests.test_relationship_runtime import Provider, packet

REPO = Path(__file__).resolve().parents[1]


class LiveFixture(Provider):
    is_live = True


def admission(root, data, provider, hook, organizer=None):
    contract, _ = rel.load_contract(REPO)
    return {'schema': live.SCHEMA, 'authorization_ref': 'offline-test-no-network',
            'source_commit': 'a69216415aaef8069f7449037ad4a64f8eaef32f',
            'implementation': implementation_digest(), 'contract_sha256': digest(contract),
            'profile_sha256': digest(rt.PROFILE), 'mode': rt.MODE, 'root': str(root),
            'episode_id': data['episode_id'], 'provider': provider_configuration(provider),
            'corrector': hook.configuration, 'organizer': organizer.configuration if organizer else None,
            'input_templates': {data['turn_id']: {'packet': deepcopy(data), 'previous': None}},
            'ceilings': {'requests': 7, 'judgments': 4, 'corrections': 2, 'organize': 1,
                         'reserve_per_jev_usd': .01}, 'recheck': True}


def fake_response(body):
    content = json.loads(body['messages'][1]['content'])
    text = '在当前对象内，模板负责传递要求，任务约束同样控制结果；不能只以载体概括全部作用。'
    result = {'text': text, 'thesis_quotes': [text], 'controller_quotes': [text],
              'discriminator_quotes': [text],
              'rebind': [{'id': k, 'quote': '__FULL__'} for k in content.get('target_bindings', {})]}
    return {'model': live.MODEL, 'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(result, ensure_ascii=False)}}],
            'usage': {'prompt_tokens': 200, 'completion_tokens': 80}}


class D3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name); self.root = self.base / 'episode'
        self.reg = patch.object(rt, '_registry', return_value=self.base / 'registry'); self.reg.start(); self.addCleanup(self.reg.stop)
        self.env = patch.dict(os.environ, {'MINDTHUS_HOST_API_KEY': 'offline-credential-not-real'}); self.env.start(); self.addCleanup(self.env.stop)
        self.provider = LiveFixture({'definition': 'carrier_only_unjustified'})
        self.transport_calls = []
        def transport(url, headers, body, timeout):
            self.transport_calls.append(deepcopy(body)); return fake_response(body)
        self.hook = live.CPAHost('original-host', REPO, transport=transport)
        self.data = packet()
        self.admission = admission(self.root, self.data, self.provider, self.hook)

    def run_entry(self, **kwargs):
        args = dict(corrector=self.hook, mode=rt.MODE, live_admission=self.admission)
        args.update(kwargs)
        return entry.run(self.root, self.provider, self.data, REPO, **args)

    def test_public_same_entry_live_fixture_path(self):
        r = self.run_entry()
        self.assertEqual(r['status'], 'corrected_rechecked')
        self.assertEqual(r['evidence_kind'], 'live_model')  # fixture only tests this classification path
        self.assertFalse(r['task_complete']); self.assertFalse(r['qualification'])
        self.assertEqual(len(self.provider.calls), 2); self.assertEqual(len(self.transport_calls), 1)
        self.assertEqual(r['revised_input']['documents'][:-1], self.data['documents'])
        self.assertEqual(r['revised_input']['authority'], self.data['authority'])
        self.assertEqual(self.run_entry(), r)
        self.assertEqual(len(self.transport_calls), 1); self.assertEqual(len(self.provider.calls), 2)

    def test_live_without_admission_blocked_before_io(self):
        with self.assertRaises(ContractError): self.run_entry(live_admission=None)
        self.assertFalse(self.provider.calls); self.assertFalse(self.root.exists())

    def test_no_legacy_live_escape(self):
        with self.assertRaises(ContractError): self.run_entry(mode='assessment-v2')
        self.assertFalse(self.root.exists())

    def test_source_profile_root_provider_changes_rejected(self):
        for field in ('implementation', 'contract_sha256', 'profile_sha256', 'root', 'episode_id', 'mode'):
            a = deepcopy(self.admission); a[field] = 'wrong'
            with self.subTest(field=field), self.assertRaises(ContractError): self.run_entry(live_admission=a)
        a = deepcopy(self.admission); a['provider']['serving']['requested_model'] = 'drift'
        with self.assertRaises(ContractError): self.run_entry(live_admission=a)
        self.assertFalse(self.provider.calls)

    def test_unadmitted_input_and_recheck_options_rejected(self):
        self.data['documents'][0]['text'] += '更强硬的要求'
        with self.assertRaises(ContractError): self.run_entry()
        self.data = packet()
        with self.assertRaises(ContractError): self.run_entry(recheck=False)

    def test_hook_configuration_mutation_rejected(self):
        self.hook.configuration['model'] = 'drift'  # admission must be a separate snapshot
        a = admission(self.root, self.data, self.provider, live.CPAHost('original-host', REPO))
        with self.assertRaises(ContractError): self.run_entry(live_admission=a)

    def test_admitted_cap_below_episode_cap_stops_recheck(self):
        self.admission['ceilings']['requests'] = 2
        r = self.run_entry()
        self.assertEqual(r['reason'], 'live_admission_budget_exhausted')
        self.assertEqual(r['episode_counts']['total'], 2)
        self.assertIsNotNone(r['revised_input'])

    def test_higher_cap_than_profile_rejected(self):
        for key in ('requests', 'judgments', 'corrections', 'organize'):
            a = deepcopy(self.admission); a['ceilings'][key] = 100
            with self.subTest(key=key), self.assertRaises(ContractError): self.run_entry(live_admission=a)

    def test_wire_request_record_matches_receipt(self):
        self.run_entry()
        step = next(self.root.glob('turns/*/inputs/*/steps/correction'))
        intent = read_record(step / 'intent.json'); out = read_record(step / 'outcome.json')
        self.assertEqual(intent['wire_request_sha256'], digest(read_record(step / 'wire-request.json')))
        self.assertEqual(intent['wire_request_sha256'], out['transport_receipt']['request_sha256'])
        self.assertEqual(out['usage']['output_tokens'], 80)
        self.assertNotIn('offline-credential-not-real', (step / 'outcome.json').read_text())

    def test_exact_session_allowlist_is_saved(self):
        self.run_entry()
        for path in self.root.glob('turns/*/inputs/*/steps/*/live-admission.json'):
            a = read_record(path)
            self.assertEqual(len(a['request_allowlist']), 1)
            self.assertEqual(a['freeze_sha256'], digest(self.admission))

    def test_unknown_host_intent_never_repeated(self):
        with patch.object(self.hook, 'correct', side_effect=KeyboardInterrupt()) as call:
            with self.assertRaises(KeyboardInterrupt): self.run_entry()
            with self.assertRaises(RecoveryRequired): self.run_entry()
            self.assertEqual(call.call_count, 1)

    def test_host_error_retains_content_and_usage(self):
        def malformed(url, headers, body, timeout):
            raw = fake_response(body); raw['choices'][0]['message']['content'] = '{invalid-json'
            return raw
        self.hook.transport = malformed
        r = self.run_entry()
        self.assertEqual(r['reason'], 'correction_failed')
        out = read_record(next(self.root.glob('turns/*/inputs/*/steps/correction/outcome.json')))
        self.assertEqual(out['transport_receipt']['content'], '{invalid-json')
        self.assertEqual(out['usage']['input_tokens'], 200)
        self.assertEqual(len(self.provider.calls), 1)
        self.assertEqual(self.run_entry(), r)

    def test_host_model_drift_is_terminal(self):
        def drift(url, headers, body, timeout):
            raw = fake_response(body); raw['model'] = 'other'; return raw
        self.hook.transport = drift
        self.assertEqual(self.run_entry()['reason'], 'correction_failed')

    def test_secret_reflection_never_persisted(self):
        def reflects(url, headers, body, timeout):
            raw = fake_response(body)
            raw['choices'][0]['message']['content'] = os.environ['MINDTHUS_HOST_API_KEY']
            return raw
        self.hook.transport = reflects
        self.assertEqual(self.run_entry()['reason'], 'correction_failed')
        for p in self.root.rglob('*.json'): self.assertNotIn(os.environ['MINDTHUS_HOST_API_KEY'], p.read_text())

    def test_deadline_transport_kills_stalled_worker_without_network(self):
        def stalled(*args): time.sleep(.3); return {}
        start = time.monotonic()
        with patch.object(live, 'post_json', side_effect=stalled):
            with self.assertRaises(ProviderError): live.deadline_post_json('https://example.invalid', {}, {}, .03)
        self.assertLess(time.monotonic() - start, 2)

    def test_completed_receipts_rebuild_report_without_network(self):
        self.run_entry()
        for p in self.root.glob('turns/*/inputs/*/summary.json'): p.unlink()
        for p in self.root.glob('turns/*/inputs/*/steps/*/report.json'): p.unlink()
        r = self.run_entry()
        self.assertEqual(r['status'], 'corrected_rechecked')
        self.assertEqual(len(self.provider.calls), 2); self.assertEqual(len(self.transport_calls), 1)

    def test_actual_previous_output_is_bound_not_authored_replacement(self):
        d2 = deepcopy(self.data); d2['turn_id'] = '3'
        d2['documents'].insert(0, {'id': 'Prev', 'revision': '1', 'kind': 'assistant', 'text': '[PREVIOUS_ACTUAL_OUTPUT]'})
        self.admission['input_templates']['3'] = {'packet': d2, 'previous': {'turn_id': self.data['turn_id'], 'document_id': 'Prev'}}
        with self.assertRaises(ContractError): live.resolve_input(self.admission, '3')
        first = self.run_entry()
        self.data = live.resolve_input(self.admission, '3')
        self.assertEqual(self.data['documents'][0]['text'], live.output_text(first))
        second = self.run_entry()
        self.assertEqual(second['episode_counts']['judgment'], 4)
        self.assertEqual(second['episode_counts']['correction'], 2)

    def test_quote_missing_ambiguous_and_full(self):
        d = {'id': 'C', 'revision': '1', 'text': '重复重复', 'kind': 'candidate'}
        with self.assertRaises(ContractError): live.locate(d, '重复')
        with self.assertRaises(ContractError): live.locate(d, '不存在')
        self.assertEqual(live.locate(d, '__FULL__'), rel.quote(d))

    def test_partial_target_edges_are_rebound_explicitly(self):
        c = self.data['proposal']['candidate']['ref']; s = rel.quote(self.data['documents'][1])
        self.data['proposal']['edges'] = [{'id': 'E0', 'frame_id': 'F0', 'premise_refs': [s], 'conclusion_refs': [c]}]
        self.admission = admission(self.root, self.data, self.provider, self.hook)
        r = self.run_entry()
        edge = r['revised_input']['proposal']['edges'][0]
        self.assertEqual(edge['premise_refs'], [s])
        self.assertNotEqual(edge['conclusion_refs'][0]['document_id'], c['document_id'])

    def test_raw_organizer_uses_original_entry_and_receipts(self):
        original = deepcopy(self.data['proposal']); docs = {d['id']: d for d in self.data['documents']}
        def symbolic(x):
            if isinstance(x, dict):
                if set(x) == rel.REF_FIELDS: return {'document_id': x['document_id'], 'full': True}
                return {k: symbolic(v) for k, v in x.items()}
            if isinstance(x, list): return [symbolic(v) for v in x]
            return x
        def transport(url, headers, body, timeout):
            return {'model': live.MODEL, 'usage': {'prompt_tokens': 100, 'completion_tokens': 200},
                    'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps({'proposal': symbolic(original)})}}]}
        org = live.CPAHost('original-host', REPO, organizer=True, transport=transport)
        self.data['proposal'] = None
        self.admission = admission(self.root, self.data, self.provider, self.hook, org)
        r = self.run_entry(organizer=org)
        self.assertEqual(r['episode_counts']['organize'], 1)
        self.assertEqual(r['prepared_input']['documents'], self.data['documents'])
        self.assertEqual(r['status'], 'corrected_rechecked')


class QuoteSelectionTests(unittest.TestCase):
    def setUp(self):
        self.doc = {'id': 'U', 'revision': '1', 'kind': 'user', 'text': '楼主先问。楼主后问。'}

    def test_explicit_repeated_quote_selects_exact_second_span(self):
        result = live.locate(self.doc, {'quote': '楼主', 'occurrence': 1})
        self.assertEqual(result, rel.quote(self.doc, 5, 7))

    def test_repeated_quote_without_selection_still_rejected(self):
        with self.assertRaises(ContractError): live.locate(self.doc, '楼主')

    def test_invalid_occurrence_cannot_fall_back(self):
        for n in [-1, 2, True, 1.0, '1', None]:
            with self.subTest(n=n), self.assertRaises(ContractError):
                live.locate(self.doc, {'quote': '楼主', 'occurrence': n})

    def test_overlapping_matches_counted_by_codepoint(self):
        d = dict(self.doc, text='aaa')
        self.assertEqual(live.locate(d, {'quote': 'aa', 'occurrence': 1}), rel.quote(d, 1, 3))

    def test_full_selector_and_normalization_never_guessed(self):
        with self.assertRaises(ContractError): live.locate(self.doc, {'quote': '__FULL__', 'occurrence': 0})
        with self.assertRaises(ContractError): live.locate(self.doc, {'quote': '楼 主', 'occurrence': 0})

    def test_organizer_and_corrector_publish_the_same_selector_rule(self):
        with patch.dict(os.environ, {'MINDTHUS_HOST_API_KEY': 'test-not-a-secret'}):
            raw = {'proposal': {'refs': [{'document_id': 'U', 'quote': '楼主', 'occurrence': 1}]}}
            def transport(*args):
                return {'model':live.MODEL, 'usage':{}, 'choices':[{'finish_reason':'stop',
                        'message':{'content':json.dumps(raw, ensure_ascii=False)}}]}
            org = live.CPAHost('owner', REPO, organizer=True, transport=transport)
            request = {'original_input': {'documents':[self.doc]}}
            result = org.organize(request, 1)
            self.assertEqual(result['proposal']['refs'][0], rel.quote(self.doc, 5, 7))
            self.assertIn('zero-based', org.wire_body(request)['messages'][0]['content'])
            self.assertEqual(org.configuration['adapter'], 'cpa-relationship-host.v1.3')


class RebindRequestTests(unittest.TestCase):
    def test_no_target_relations_explicitly_requires_zero_bindings(self):
        hook=live.CPAHost('original-host', REPO)
        from experiments.typed_decision.relationship_runtime import correction_request
        from tests.test_relationship_assessment import response
        p=packet();compiled=rel.compile_packet(p,REPO)
        r=rel.consume(compiled,response(compiled,{'definition':'account_missing'}),REPO)
        body=hook.wire_body(correction_request(p,{'result':r}))
        content=json.loads(body['messages'][1]['content'])
        self.assertEqual(content['reference_rebinding']['required_rebind_ids'],[])
        self.assertEqual(content['reference_rebinding']['required_count'],0)
        self.assertIn('never repair check_ref IDs',content['reference_rebinding']['rule'])


if __name__ == '__main__': unittest.main()
