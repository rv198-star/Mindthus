"""Offline engineering tests, not a semantic Jev benchmark or value qualification."""
import copy
from dataclasses import asdict
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.typed_decision import c01, c02, campaign, handoff, c01_host
from experiments.typed_decision.contracts import (
    BatchResult,
    ContractError,
    DecisionResult,
    DecisionSpec,
    EngineIdentity,
    ResolvedRuntime,
    ServingIdentity,
    canonical,
    digest,
    project_context,
    provider_configuration,
)
from experiments.typed_decision.providers import (
    ChatProvider,
    FixtureProvider,
    JevProvider,
    JevEngine,
    OpenRouterJevProvider,
    ProviderError,
    TypeSafeJevProvider,
    _NoRedirect,
)
from experiments.typed_decision.session import Limits, RecoveryRequired, Session, read_record, write_once, implementation_digest
from experiments.typed_decision.trace import from_c01, validate_with_existing

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'experiments/typed_decision/fixtures/c01-sra.json').read_text())


def spec(ident='test', kind='select', criteria=None, reads=('text',)):
    if criteria is None:
        criteria = {'yes': 'positive', 'no': 'negative'}
    return DecisionSpec(ident, 'Evaluate the named criterion.', criteria, reads, kind=kind)


class ChoiceRoundingTests(unittest.TestCase):
    def result(self, probs, choice='yes', enabled=True):
        s = spec(criteria={'yes': 'positive', 'no': 'negative', 'unclear': 'abstain'})
        answer = {'type': 'choice', 'choice': choice, 'confidence': .9, 'probabilities': probs}
        original = copy.deepcopy(answer)
        r = JevEngine('jev-1.13.0', choice_rounding=enabled).results([s], {'test': answer})['test']
        self.assertEqual(answer, original)
        r.validate(s)
        return r

    def test_bounded_decimal_sum_adjustment_preserves_choice_confidence_and_raw(self):
        for probs in [{'yes': .93, 'no': .05, 'unclear': .01},
                      {'yes': .93, 'no': .07, 'unclear': .01}]:
            r = self.result(probs)
            self.assertEqual(r.value, 'yes')
            self.assertEqual(r.uncertainty['confidence'], .9)
            self.assertAlmostEqual(sum(r.uncertainty['probabilities'].values()), 1)
            self.assertEqual(r.reason, 'choice_probability_sum_normalized_v1')

    def test_strict_default_and_shared_contract_unchanged(self):
        with self.assertRaisesRegex(ContractError, 'distribution not normalized'):
            self.result({'yes': .93, 'no': .05, 'unclear': .01}, enabled=False)
        self.assertEqual(self.result({'yes': .93, 'no': .06, 'unclear': .01}).reason, '')
        for cls in (TypeSafeJevProvider, OpenRouterJevProvider):
            self.assertNotEqual(provider_configuration(cls()),
                                provider_configuration(cls(choice_rounding=True)))

    def test_normalization_does_not_admit_other_invalid_results(self):
        for probs in [{'yes': .93, 'no': .04, 'unclear': .01},
                      {'yes': .931, 'no': .049, 'unclear': .01},
                      {'yes': .93, 'no': .06},
                      {'yes': .93, 'no': .05, 'unclear': .01, 'extra': 0},
                      {'yes': 1.01, 'no': -.03, 'unclear': .01},
                      {'yes': True, 'no': 0, 'unclear': 0},
                      {'yes': float('inf'), 'no': 0, 'unclear': 0}]:
            with self.subTest(probs=probs), self.assertRaises(ContractError):
                self.result(probs)
        with self.assertRaisesRegex(ContractError, 'argmax'):
            self.result({'yes': .93, 'no': .05, 'unclear': .01}, choice='no')

    def test_rate_is_not_normalized(self):
        s = spec(kind='rate', criteria=['low', 'high'])
        r = JevEngine('jev-1.13.0', choice_rounding=True).results([s], {'test': {
            'type': 'score', 'score': .05, 'confidence': .9,
            'probabilities': {'0': .94, '1': .05}, 'legend': {'0': 'low', '1': 'high'}}})['test']
        with self.assertRaisesRegex(ContractError, 'distribution not normalized'):
            r.validate(s)


class ContractTests(unittest.TestCase):
    def test_existing_numeric_leading_method_id_is_valid_option(self):
        spec(criteria={'3l5s': 'Problem definition', 'sra': 'Resource allocation'}).validate()

    def test_all_kinds_validate(self):
        for s in [spec(), spec(kind='assess_proposition', criteria={'true': 'Yes', 'false': 'No'}),
                  spec(kind='rate', criteria=['low', 'medium', 'high'])]:
            s.validate()

    def test_unknown_type_or_ambiguous_contract_rejected(self):
        for s in [spec(kind='code'), spec(criteria={'yes': 'only'}), spec(reads=('text', 'text')),
                  spec(kind='rate', criteria=['single']), spec(kind='assess_proposition')]:
            with self.subTest(s=s), self.assertRaises(ContractError):
                s.validate()

    def test_non_ok_never_contains_decision(self):
        for status in ('abstain', 'missing_context', 'unsupported', 'provider_error'):
            with self.subTest(status=status), self.assertRaises(ContractError):
                DecisionResult(status, 'yes').validate(spec())

    def test_invalid_numeric_values_rejected(self):
        s = spec(kind='assess_proposition', criteria={'true': 'Yes', 'false': 'No'})
        for value in (True, -0.1, 1.1, float('nan'), float('inf'), '0.9'):
            with self.subTest(value=value), self.assertRaises(ContractError):
                DecisionResult('ok', value).validate(s)

    def test_distribution_and_confidence_are_typed(self):
        good = {'source': 'provider_distribution', 'confidence': .8,
                'probabilities': {'yes': .9, 'no': .1}}
        DecisionResult('ok', 'yes', good).validate(spec())
        for uncertainty in [dict(good, confidence=1.1), dict(good, source='llm_self_report'),
                            dict(good, probabilities={'yes': .9}),
                            dict(good, probabilities={'yes': .2, 'no': .8}),
                            dict(good, probabilities={'yes': .8, 'no': .1})]:
            with self.subTest(uncertainty=uncertainty), self.assertRaises(ContractError):
                DecisionResult('ok', 'yes', uncertainty).validate(spec())

    def test_projected_context_is_minimal_and_detached(self):
        source = {'text': {'facts': [1]}, 'secret_not_requested': 'do-not-send'}
        projected = project_context([spec()], source)
        source['text']['facts'].append(2)
        self.assertEqual(projected, {'text': {'facts': [1]}})

    def test_distinct_read_sets_must_not_share_batch(self):
        with self.assertRaises(ContractError):
            project_context([spec(), spec('other', reads=('elsewhere',))], {'text': 1, 'elsewhere': 2})

    def test_missing_data_is_not_negative(self):
        with self.assertRaisesRegex(ContractError, 'missing_context'):
            project_context([spec()], {'text': None})


class ProviderTests(unittest.TestCase):
    def test_native_api_mapping_and_no_secret_in_identity(self):
        seen = []
        specs = [spec('select'), spec('probability', 'assess_proposition', {'true': 'yes', 'false': 'no'}),
                 spec('rate', 'rate', ['low', 'mid', 'high'])]
        def transport(url, headers, body, timeout):
            seen.append((url, body, timeout))
            return {'model': 'jev-1.13.0', 'answers': {
                'select': {'type': 'choice', 'choice': 'yes', 'probabilities': {'yes': .9, 'no': .1}, 'confidence': .8},
                'probability': {'type': 'noul', 'noul': .75},
                'rate': {'type': 'score', 'score': 1.05, 'probabilities': {'0': 0., '1': .95, '2': .05},
                         'legend': {'0': 'low', '1': 'mid', '2': 'high'}, 'confidence': .92}},
                'usage': {'input_tokens': 100, 'output_tokens': 20}}
        provider = JevProvider(transport=transport)
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'fixture-only-credential'}):
            batch = provider.evaluate(specs, {'text': 'fixture'}, 5)
        self.assertEqual(batch.results['rate'].value, 1.05)
        self.assertIsNone(batch.results['probability'].uncertainty)
        self.assertEqual(batch.resolved_runtime.model, 'jev-1.13.0')
        self.assertEqual(batch.resolved_runtime.provider, 'TypeSafe')
        self.assertIsNone(batch.usage['cost_usd'])
        self.assertEqual([v['type'] for v in seen[0][1]['questions'].values()], ['choice', 'noul', 'score'])
        config = provider_configuration(provider)
        self.assertEqual(config['engine']['model_family'], 'jev-1.13')
        self.assertEqual(config['serving']['provider'], 'typesafe')
        self.assertNotIn('fixture-only-credential', str(config))

    def test_native_missing_key_fails_without_transport(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ProviderError):
            JevProvider(transport=lambda *_: self.fail('network called')).evaluate([spec()], {'text': 1}, 3)

    def test_pin_aliases_rejected(self):
        for model in ('jev-latest', 'jev-preview'):
            with self.assertRaises(ContractError):
                JevProvider(model)

    def test_native_wrong_model_invalid_choices_and_missing_answers(self):
        valid = {'model': 'jev-1.13.0', 'answers': {'test': {'type': 'choice', 'choice': 'yes',
                  'probabilities': {'yes': .9, 'no': .1}, 'confidence': .8}}}
        malformed = [dict(valid, model='jev-new'), dict(valid, answers={}),
                     dict(valid, answers={'test': {'type': 'noul', 'noul': .8}})]
        for response in malformed:
            with self.subTest(response=response), patch.dict(os.environ, {'TYPESAFE_API_KEY': 'fixture'}), \
                    self.assertRaises(ContractError):
                JevProvider(transport=lambda *_, r=response: r).evaluate([spec()], {'text': 1}, 3)

    def test_openrouter_jev_mapping_accepts_resolved_snapshot_and_cost(self):
        seen = []
        specs = [spec('select'), spec('probability', 'assess_proposition', {'true': 'yes', 'false': 'no'}),
                 spec('rate', 'rate', ['low', 'mid', 'high'])]
        raw = {'model': 'typesafe/jev-1.13-20260917', 'provider': 'TypeSafe', 'answers': {
            'select': {'type': 'choice', 'choice': 'yes', 'probabilities': {'yes': .99, 'no': .01}, 'confidence': .98},
            'probability': {'type': 'noul', 'noul': .75},
            'rate': {'type': 'score', 'score': 1.05, 'probabilities': {'0': 0., '1': .95, '2': .05},
                     'legend': {'0': 'low', '1': 'mid', '2': 'high'}, 'confidence': .92}},
            'usage': {'input_tokens': 575, 'output_tokens': 91, 'cost': 2.415e-05}}
        def transport(url, headers, body, timeout):
            seen.append((url, headers, body, timeout))
            return raw
        provider = OpenRouterJevProvider(transport=transport)
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'fixture-only-credential'}):
            batch = provider.evaluate(specs, {'text': 'fixture'}, 5)
        self.assertEqual(batch.resolved_runtime.model, 'typesafe/jev-1.13-20260917')
        self.assertEqual(batch.resolved_runtime.provider, 'TypeSafe')
        self.assertEqual(batch.usage['cost_usd'], 2.415e-05)
        self.assertEqual(seen[0][0], 'https://openrouter.ai/api/alpha/decisions')
        self.assertEqual(seen[0][2]['model'], 'typesafe/jev-1.13')
        config = provider_configuration(provider)
        self.assertEqual(config['engine']['model_family'], 'jev-1.13')
        self.assertEqual(config['serving']['provider'], 'openrouter')
        self.assertNotIn('fixture-only-credential', str(config))

    def test_same_jev_engine_can_use_distinct_serving_paths(self):
        native = TypeSafeJevProvider()
        routed = OpenRouterJevProvider()
        self.assertEqual(native.engine_identity, routed.engine_identity)
        self.assertEqual(native.engine_identity, EngineIdentity(
            family='system_one',
            implementation='jev',
            model_family='jev-1.13',
        ))
        self.assertNotEqual(native.serving_identity, routed.serving_identity)
        self.assertEqual(native.serving_identity.provider, 'typesafe')
        self.assertEqual(routed.serving_identity.provider, 'openrouter')
        self.assertEqual(
            provider_configuration(native)['engine'],
            provider_configuration(routed)['engine'],
        )
        self.assertNotEqual(
            provider_configuration(native)['serving'],
            provider_configuration(routed)['serving'],
        )

    def test_openrouter_jev_rejects_alias_missing_key_and_wrong_family(self):
        with self.assertRaises(ContractError):
            OpenRouterJevProvider('~typesafe/jev-latest')
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ProviderError):
            OpenRouterJevProvider(transport=lambda *_: self.fail('network called')).evaluate([spec()], {'text': 1}, 3)
        raw = {'model': 'typesafe/jev-1.14-20260920', 'answers': {'test': {
            'type': 'choice', 'choice': 'yes', 'probabilities': {'yes': 1, 'no': 0}, 'confidence': 1}}}
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'fixture'}), self.assertRaises(ContractError):
            OpenRouterJevProvider(transport=lambda *_: raw).evaluate([spec()], {'text': 1}, 3)

    def test_llm_select_has_unknown_confidence_and_strict_schema(self):
        seen = []
        def transport(url, headers, body, timeout):
            seen.append(body)
            return {'model': 'test/fixed-model', 'choices': [{'finish_reason': 'stop', 'message': {
                'content': json.dumps({'answers': {'test': {'status': 'ok', 'value': 'yes'}}})}}],
                    'usage': {'prompt_tokens': 10, 'completion_tokens': 3, 'cost': .001}}
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'fixture'}):
            result = ChatProvider('test/fixed-model', transport=transport).evaluate([spec()], {'text': 1}, 3)
        self.assertIsNone(result.results['test'].uncertainty)
        self.assertTrue(seen[0]['provider']['require_parameters'])
        self.assertTrue(seen[0]['response_format']['json_schema']['strict'])

    def test_llm_does_not_fabricate_probability_support(self):
        p = ChatProvider('test/fixed-model', transport=lambda *_: self.fail('should not call'))
        result = p.evaluate([spec('p', 'assess_proposition', {'true': 'Yes', 'false': 'No'})], {'text': 1}, 2)
        self.assertEqual(result.results['p'].status, 'unsupported')

    def test_llm_abstain_preserved(self):
        raw = {'model': 'test/model', 'choices': [{'finish_reason': 'stop', 'message': {
            'content': '{"answers":{"test":{"status":"abstain","value":null}}}'}}]}
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'fixture'}):
            result = ChatProvider('test/model', transport=lambda *_: raw).evaluate([spec()], {'text': 1}, 2)
        self.assertEqual(result.results['test'].status, 'abstain')

    def test_llm_extra_fields_and_truncation_rejected(self):
        for finish, content in [('length', '{"answers":{}}'), ('stop',
                '{"answers":{"test":{"status":"ok","value":"yes","confidence":1}}}')]:
            raw = {'model': 'test/model', 'choices': [{'finish_reason': finish, 'message': {'content': content}}]}
            with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'fixture'}), self.assertRaises(ProviderError):
                ChatProvider('test/model', transport=lambda *_: raw).evaluate([spec()], {'text': 1}, 2)

    def test_malformed_top_level_or_usage_is_a_typed_error(self):
        valid = {'model': 'jev-1.13.0', 'answers': {'test': {'type': 'choice', 'choice': 'yes',
                 'probabilities': {'yes': 1, 'no': 0}, 'confidence': 1}}, 'usage': 'bad'}
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'fixture'}):
            for raw in [None, [], valid]:
                with self.subTest(raw=raw), self.assertRaises(ContractError):
                    JevProvider(transport=lambda *_, raw=raw: raw).evaluate([spec()], {'text': 'test'}, 2)

    def test_wire_body_budget_is_checked_before_network(self):
        from experiments.typed_decision.providers import post_json
        with self.assertRaisesRegex(ContractError, 'HTTP request exceeds'):
            post_json('https://api.typesafe.ai/v1/systemone', {}, {'data': 'x' * 262145}, 1)

    def test_redirect_rejected(self):
        with self.assertRaises(ProviderError):
            _NoRedirect().redirect_request(None, None, 302, '', {}, 'https://other.example/')


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.provider = FixtureProvider({'test': 'yes'})

    def tearDown(self):
        self.temp.cleanup()

    def test_live_is_disabled_until_campaign_preregistered(self):
        with self.assertRaisesRegex(ContractError, 'live_campaign_not_preregistered'):
            Session(self.root, JevProvider(), scope='test')

    def test_persisted_result_reused_after_new_session(self):
        for i in range(2):
            with Session(self.root, self.provider, scope='test') as run:
                result = run.evaluate([spec()], {'text': 'same'})
                self.assertEqual(result['test'].value, 'yes')
                self.assertEqual(run.calls_reused, i)
        self.assertEqual(len(self.provider.calls), 1)

    def test_unrelated_context_does_not_invalidate_batch(self):
        with Session(self.root, self.provider, scope='test') as run:
            run.evaluate([spec()], {'text': 'same', 'unused': 1})
            run.evaluate([spec()], {'text': 'same', 'unused': 2})
            self.assertEqual(run.calls_reused, 1)

    def test_relevant_context_does_invalidate(self):
        with Session(self.root, self.provider, scope='test') as run:
            run.evaluate([spec()], {'text': 'before'})
            run.evaluate([spec()], {'text': 'after'})
        self.assertEqual(len(self.provider.calls), 2)
        self.assertEqual(len(list((self.root / 'calls').glob('*/outcome.json'))), 2)

    def test_missing_context_calls_no_model(self):
        with Session(self.root, self.provider, scope='test') as run:
            result = run.evaluate([spec()], {})
        self.assertEqual(result['test'].status, 'missing_context')
        self.assertEqual(self.provider.calls, [])

    def test_budget_survives_restart(self):
        with Session(self.root, self.provider, scope='test', limits=Limits(max_calls=1)) as run:
            run.evaluate([spec()], {'text': 'first'})
        with Session(self.root, self.provider, scope='test', limits=Limits(max_calls=1)) as run:
            with self.assertRaisesRegex(ContractError, 'call budget'):
                run.evaluate([spec()], {'text': 'second'})

    def test_policy_cannot_expand_budget_on_resume(self):
        with Session(self.root, self.provider, scope='test', limits=Limits(max_calls=1)):
            pass
        with self.assertRaises(ContractError):
            with Session(self.root, self.provider, scope='test', limits=Limits(max_calls=3)):
                pass

    def test_byte_limit_applies_before_call(self):
        with Session(self.root, self.provider, scope='test', limits=Limits(max_request_bytes=1)) as run:
            with self.assertRaises(ContractError):
                run.evaluate([spec()], {'text': 'anything'})
        self.assertEqual(self.provider.calls, [])

    def test_interrupted_intent_is_not_reissued(self):
        class Interrupted(FixtureProvider):
            def evaluate(self, *_):
                raise KeyboardInterrupt()
        p = Interrupted({'test': 'yes'})
        with self.assertRaises(KeyboardInterrupt):
            with Session(self.root, p, scope='test') as run:
                run.evaluate([spec()], {'text': 'same'})
        with Session(self.root, self.provider, scope='test') as run:
            with self.assertRaises(RecoveryRequired):
                run.evaluate([spec()], {'text': 'same'})
            with self.assertRaises(RecoveryRequired):
                run.evaluate([spec()], {'text': 'another'})
        self.assertEqual(self.provider.calls, [])

    def test_single_writer_lock(self):
        with Session(self.root, self.provider, scope='test'):
            with self.assertRaises(RecoveryRequired):
                with Session(self.root, self.provider, scope='test'):
                    self.fail('second writer entered')

    def test_changed_provider_identity_requires_new_trial(self):
        with Session(self.root, self.provider, scope='test'):
            pass
        with self.assertRaises(ContractError):
            with Session(self.root, FixtureProvider({'test': 'no'}), scope='test'):
                pass

    def test_openrouter_resolved_snapshot_differs_from_requested_model_and_replays(self):
        class OfflineOpenRouter(OpenRouterJevProvider):
            is_live = False

        raw = {
            'model': 'typesafe/jev-1.13-20260917',
            'provider': 'TypeSafe',
            'answers': {
                'test': {
                    'type': 'choice',
                    'choice': 'yes',
                    'probabilities': {'yes': 1.0, 'no': 0.0},
                    'confidence': 1.0,
                },
            },
            'usage': {'input_tokens': 10, 'output_tokens': 1, 'cost': .000001},
        }
        calls = []
        def transport(*_):
            calls.append('network')
            return raw

        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'fixture'}):
            with Session(
                self.root,
                OfflineOpenRouter(transport=transport),
                scope='test',
            ) as run:
                result = run.evaluate([spec()], {'text': 'same'})
                report = run.finish(
                    {'id': 'probe'},
                    {'text': 'same'},
                    {'route': 'fixture'},
                )
            with Session(
                self.root,
                OfflineOpenRouter(
                    transport=lambda *_: self.fail('replay called transport')
                ),
                scope='test',
            ) as run:
                replay = run.evaluate([spec()], {'text': 'same'})

        self.assertEqual(result['test'].value, 'yes')
        self.assertEqual(replay['test'].value, 'yes')
        self.assertEqual(calls, ['network'])
        self.assertEqual(
            read_record(self.root / 'resolved-runtime.json'),
            {
                'model': 'typesafe/jev-1.13-20260917',
                'provider': 'TypeSafe',
            },
        )
        self.assertEqual(
            report['resolved_runtimes'],
            [{
                'model': 'typesafe/jev-1.13-20260917',
                'provider': 'TypeSafe',
            }],
        )
        policy = read_record(self.root / 'policy.json')
        self.assertEqual(
            policy['provider_configuration']['engine']['model_family'],
            'jev-1.13',
        )
        self.assertEqual(
            policy['provider_configuration']['serving']['requested_model'],
            'typesafe/jev-1.13',
        )

    def test_resolved_runtime_drift_fails_closed_within_trial(self):
        class OfflineOpenRouter(OpenRouterJevProvider):
            is_live = False

        snapshots = iter([
            'typesafe/jev-1.13-20260917',
            'typesafe/jev-1.13-20260918',
        ])
        def transport(*_):
            snapshot = next(snapshots)
            return {
                'model': snapshot,
                'provider': 'TypeSafe',
                'answers': {
                    'test': {
                        'type': 'choice',
                        'choice': 'yes',
                        'probabilities': {'yes': 1.0, 'no': 0.0},
                        'confidence': 1.0,
                    },
                },
            }

        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'fixture'}):
            with Session(
                self.root,
                OfflineOpenRouter(transport=transport),
                scope='test',
            ) as run:
                first = run.evaluate([spec()], {'text': 'first'})
                second = run.evaluate([spec()], {'text': 'second'})

        self.assertEqual(first['test'].value, 'yes')
        self.assertEqual(second['test'].status, 'provider_error')
        self.assertEqual(
            read_record(self.root / 'resolved-runtime.json')['model'],
            'typesafe/jev-1.13-20260917',
        )

    def test_corrupt_or_hash_correct_invalid_result_fails_closed(self):
        with Session(self.root, self.provider, scope='test') as run:
            run.evaluate([spec()], {'text': 'same'})
        path = next((self.root / 'calls').glob('*/outcome.json'))
        old = json.loads(path.read_text())
        for mutate in ('checksum', 'enum', 'runtime', 'extra'):
            broken = copy.deepcopy(old)
            if mutate == 'checksum':
                broken['sha256'] = 'wrong'
            elif mutate == 'enum':
                broken['payload']['results']['test']['value'] = 'foreign'
                broken['sha256'] = digest(broken['payload'])
            elif mutate == 'runtime':
                broken['payload']['resolved_runtime']['model'] = 'foreign-model'
                broken['sha256'] = digest(broken['payload'])
            else:
                broken['payload']['results']['unrequested'] = broken['payload']['results']['test']
                broken['sha256'] = digest(broken['payload'])
            path.write_text(json.dumps(broken))
            with self.subTest(mutate=mutate), Session(self.root, self.provider, scope='test') as run:
                with self.assertRaises(ContractError):
                    run.evaluate([spec()], {'text': 'same'})

    def test_aggregate_known_usage_does_not_double_count_replay(self):
        class Metered(FixtureProvider):
            def evaluate(self, specs, context, timeout):
                batch = super().evaluate(specs, context, timeout)
                batch.usage = {'input_tokens': 10, 'output_tokens': 2, 'cost_usd': .001}
                return batch
        provider = Metered({'test': 'yes'})
        for _ in range(2):
            with Session(self.root, provider, scope='test') as run:
                run.evaluate([spec()], {'text': 'same'})
                report = run.finish({'id': 'probe'}, {'text': 'same'}, {'route': 'fixture'})
                self.assertEqual(report['trial_usage'], {'input_tokens': 10, 'output_tokens': 2, 'cost_usd': .001})
        self.assertEqual(report['invocation'], {'new_calls': 0, 'reused_calls': 1})
        self.assertEqual(report['end_to_end_value'], 'unknown')

    def test_invalid_provider_batch_is_recorded_as_failure(self):
        class Invalid(FixtureProvider):
            def evaluate(self, *_):
                return None
        with Session(self.root, Invalid({'test': 'yes'}), scope='test') as run:
            result = run.evaluate([spec()], {'text': 'same'})
        self.assertEqual(result['test'].status, 'provider_error')
        self.assertEqual(len(list((self.root / 'calls').glob('*/outcome.json'))), 1)

    def test_provider_failure_does_not_leak_exception_text(self):
        class Failure(FixtureProvider):
            def evaluate(self, *_):
                raise ProviderError('Authorization secret-must-not-leak')
        p = Failure({'test': 'yes'})
        with Session(self.root, p, scope='test') as run:
            result = run.evaluate([spec()], {'text': 'same'})
        self.assertEqual(result['test'].status, 'provider_error')
        contents = next((self.root / 'calls').glob('*/outcome.json')).read_text()
        self.assertNotIn('secret-must-not-leak', contents)


class C01Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def run_graph(self, changes=None, context=None, root=None, repo=ROOT):
        answers = dict(FIXTURE['answers'], **(changes or {}))
        provider = FixtureProvider(answers)
        with Session(root or self.root, provider, scope='c01') as session:
            report = c01.run(session, context or copy.deepcopy(FIXTURE['context']), repo)
        return report, provider

    def test_real_dependency_order_and_selected_file_consumption(self):
        report, provider = self.run_graph()
        self.assertEqual(provider.calls, [['entry_mode', 'unresolved_obligation'], ['owner'], ['applicable']])
        self.assertEqual(report['result']['owner'], 'sra')
        receipt = c01.read_selected_method(report, ROOT)
        self.assertIn('Scarce Resource', receipt['content'])
        self.assertEqual(receipt['native_skill_load'], 'not_observed')
        trace = from_c01(report, receipt)
        self.assertEqual(trace['routing']['loaded_methods'], [])
        validate_with_existing(trace, ROOT)

    def test_completed_graph_resumes_without_reasking(self):
        first, p1 = self.run_graph()
        second, p2 = self.run_graph()
        self.assertEqual(second['invocation'], {'new_calls': 0, 'reused_calls': 3})
        self.assertEqual(first['run_id'], second['run_id'])
        self.assertEqual(p2.calls, [])
        self.assertIsNone(second['trial_usage']['cost_usd'])

    def test_specific_method_change_only_invalidates_dependent_stage(self):
        repo = self.root / 'source'
        (repo / 'skills/using-mindthus').mkdir(parents=True)
        (repo / 'skills/sra').mkdir(parents=True)
        (repo / 'skills/using-mindthus/SKILL.md').write_text((ROOT / 'skills/using-mindthus/SKILL.md').read_text())
        path = repo / 'skills/sra/SKILL.md'
        path.write_text('Version one method fixture.')
        first, _ = self.run_graph(root=self.root / 'trial', repo=repo)
        path.write_text('Version two method fixture.')
        second, provider = self.run_graph(root=self.root / 'trial', repo=repo)
        self.assertEqual(provider.calls, [['applicable']])
        self.assertEqual(second['invocation']['reused_calls'], 2)
        self.assertNotEqual(first['run_id'], second['run_id'])

    def test_method_change_after_judgment_prevents_consumption(self):
        report, _ = self.run_graph()
        report['identity']['graph']['selected_method_sha256'] = 'changed'
        with self.assertRaises(ContractError):
            c01.read_selected_method(report, ROOT)

    def test_fact_gap_direct_and_obligation_paths(self):
        cases = [({'entry_mode': 'acquire_information'}, 'acquire_information'),
                 ({'entry_mode': 'direct_execution'}, 'direct_execute'),
                 ({'unresolved_obligation': 'present'}, 'llm_fallback'),
                 ({'entry_mode': 'unclear'}, 'llm_fallback'),
                 ({'owner': 'unclear'}, 'llm_fallback'),
                 ({'applicable': 'no'}, 'llm_fallback')]
        for i, (changes, expected) in enumerate(cases):
            with self.subTest(changes=changes):
                report, _ = self.run_graph(changes, root=self.root / str(i))
                self.assertEqual(report['result']['route'], expected)

    def test_explicit_method_preserved_but_not_a_precondition_waiver(self):
        context = copy.deepcopy(FIXTURE['context']); context['explicit_method'] = 'wae'
        report, provider = self.run_graph({'entry_mode': 'mindthus_intervention', 'applicable': 'no'}, context)
        self.assertEqual(report['result']['route'], 'llm_fallback')
        self.assertEqual(provider.calls, [['entry_mode', 'unresolved_obligation'], ['applicable']])
        self.assertIsNone(report['result']['hard_judgment'])

    def test_rejected_applicability_still_binds_full_method_identity(self):
        repo = self.root / 'source'
        (repo / 'skills/using-mindthus').mkdir(parents=True)
        (repo / 'skills/sra').mkdir(parents=True)
        (repo / 'skills/using-mindthus/SKILL.md').write_text((ROOT / 'skills/using-mindthus/SKILL.md').read_text())
        path = repo / 'skills/sra/SKILL.md'
        path.write_text('First ineligible contract.')
        first, _ = self.run_graph({'applicable': 'no'}, root=self.root / 'trial', repo=repo)
        path.write_text('Second ineligible contract.')
        second, provider = self.run_graph({'applicable': 'no'}, root=self.root / 'trial', repo=repo)
        self.assertNotEqual(first['run_id'], second['run_id'])
        self.assertEqual(provider.calls, [['applicable']])

    def test_missing_selected_contract_is_information_gap_without_applicability_call(self):
        original = Path.read_text
        def read(path, *args, **kwargs):
            if path == ROOT / 'skills/sra/SKILL.md':
                raise FileNotFoundError('missing selected source')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', read):
            report, provider = self.run_graph()
        self.assertEqual(report['result']['reason'], 'selected_contract_unavailable')
        self.assertEqual(report['result']['status'], 'missing_context')
        self.assertEqual(provider.calls, [['entry_mode', 'unresolved_obligation'], ['owner']])

    def test_preexisting_obligations_cannot_be_cleared_by_model(self):
        context = copy.deepcopy(FIXTURE['context']); context['known_obligations'] = ['anti_spiral_required']
        report, _ = self.run_graph(context=context)
        self.assertEqual(report['result']['route'], 'llm_fallback')
        self.assertIn('anti_spiral_required', report['result']['obligations'])

    def test_stale_unknown_and_malformed_context_do_not_call_model(self):
        for i, changes in enumerate([{'freshness': 'stale'}, {'risk': None},
                                      {'explicit_method': []}, {'provenance': None}]):
            context = dict(FIXTURE['context'], **changes)
            with self.subTest(changes=changes):
                report, p = self.run_graph(context=context, root=self.root / str(i))
                self.assertEqual(report['result']['route'], 'original_path')
                self.assertEqual(p.calls, [])

    def test_high_risk_direct_path_falls_back(self):
        context = dict(FIXTURE['context'], risk='high')
        report, _ = self.run_graph({'entry_mode': 'direct_execution'}, context)
        self.assertEqual(report['result']['route'], 'llm_fallback')

    def test_all_entry_modes_and_obligation_combinations(self):
        for mode in ('direct_execution', 'acquire_information', 'mindthus_intervention', 'unclear'):
            for obligation in ('clear', 'present', 'unclear'):
                with self.subTest(mode=mode, obligation=obligation):
                    report, provider = self.run_graph(
                        {'entry_mode': mode, 'unresolved_obligation': obligation},
                        root=self.root / (mode + '-' + obligation))
                    expected = {'direct_execution': 'direct_execute',
                                'acquire_information': 'acquire_information',
                                'mindthus_intervention': 'intervene',
                                'unclear': 'llm_fallback'}[mode] if obligation == 'clear' else 'llm_fallback'
                    self.assertEqual(report['result']['route'], expected)
                    self.assertEqual(len(provider.calls), 3 if expected == 'intervene' else 1)
                    self.assertEqual(report['result']['consumption'], 'not_executed')
                    self.assertEqual(report['result']['hard_judgment'],
                                     {'direct_execution': False, 'mindthus_intervention': True}.get(mode))

    def test_same_state_contains_constraints_and_selected_full_contract_is_later(self):
        seen = []
        class Capture(FixtureProvider):
            def evaluate(self, specs, context, timeout):
                seen.append((specs, context))
                return super().evaluate(specs, context, timeout)
        with Session(self.root, Capture(FIXTURE['answers']), scope='c01') as session:
            c01.run(session, copy.deepcopy(FIXTURE['context']), ROOT)
        specs, state = seen[0]
        self.assertEqual([s.id for s in specs], ['entry_mode', 'unresolved_obligation'])
        self.assertEqual(specs[0].required_context, specs[1].required_context)
        self.assertEqual(state['known_obligations'], [])
        self.assertEqual(state['explicit_method'], 'not_requested')
        self.assertNotIn('method_contract', state)
        self.assertNotIn('method_contract', seen[1][1])
        self.assertEqual(seen[2][1]['method_contract'], (ROOT / 'skills/sra/SKILL.md').read_text())
        self.assertEqual(seen[2][1]['selected_owner'], 'sra')

    def test_d0_rejects_missing_fields_identity_evidence_and_permission_without_calls(self):
        contexts = []
        for field in ('request', 'constraints', 'evidence', 'provenance', 'known_obligations',
                      'risk', 'freshness', 'permission'):
            context = copy.deepcopy(FIXTURE['context'])
            del context[field]
            contexts.append(context)
        contexts += [dict(FIXTURE['context'], **change) for change in (
            {'provenance': {'source_ref': 'test', 'revision': ''}},
            {'evidence': [{'summary': 'no source'}]},
            {'permission': {'mode': 'advisory', 'source_ref': ''}},
            {'permission': {'mode': 'bounded_execution', 'source_ref': 'unsupported'}},
            {'permission': {'mode': 'denied', 'source_ref': 'host'}},
        )]
        for i, context in enumerate(contexts):
            with self.subTest(i=i):
                report, provider = self.run_graph(context=context, root=self.root / str(i))
                self.assertEqual(report['result']['route'], 'original_path')
                self.assertEqual(provider.calls, [])

    def test_empty_evidence_is_not_a_mechanical_information_gap(self):
        context = dict(FIXTURE['context'], request='把“周一”改为“周二”。', evidence=[])
        report, provider = self.run_graph({'entry_mode': 'direct_execution'}, context)
        self.assertEqual(report['result']['route'], 'direct_execute')
        self.assertEqual(len(provider.calls), 1)

    def test_explicit_method_cannot_be_erased_by_direct_choice(self):
        context = dict(FIXTURE['context'], explicit_method='sra')
        report, provider = self.run_graph({'entry_mode': 'direct_execution'}, context)
        self.assertEqual(report['result']['route'], 'intervene')
        self.assertEqual(report['result']['owner'], 'sra')
        self.assertEqual(report['result']['entry_mode'], 'mindthus_intervention')
        self.assertIsNone(report['result']['hard_judgment'])
        self.assertEqual(provider.calls, [['entry_mode', 'unresolved_obligation'], ['applicable']])
        self.assertEqual(report['result']['consumption'], 'not_executed')

    def test_explicit_direct_still_checks_complete_contract_and_rejects_inapplicability(self):
        context = dict(FIXTURE['context'], explicit_method='wae')
        seen = []
        class Capture(FixtureProvider):
            def evaluate(self, specs, state, timeout):
                seen.append(state)
                return super().evaluate(specs, state, timeout)
        provider = Capture(dict(FIXTURE['answers'], entry_mode='direct_execution', applicable='no'))
        with Session(self.root, provider, scope='c01') as session:
            report = c01.run(session, context, ROOT)
        self.assertEqual(report['result']['reason'], 'selected_owner_not_established')
        self.assertEqual(report['result']['route'], 'llm_fallback')
        self.assertIsNone(report['result']['owner'])
        self.assertEqual(seen[-1]['selected_owner'], 'wae')
        self.assertEqual(seen[-1]['method_contract'], (ROOT / 'skills/wae/SKILL.md').read_text())
        self.assertEqual(provider.calls, [['entry_mode', 'unresolved_obligation'], ['applicable']])

    def test_explicit_invocation_never_overrides_unknown_gap_failure_or_obligation(self):
        cases = [({'entry_mode': 'unclear'}, {}, 'llm_fallback'),
                 ({'entry_mode': 'acquire_information'}, {}, 'acquire_information'),
                 ({'entry_mode': asdict(DecisionResult('provider_error'))}, {}, 'llm_fallback'),
                 ({'entry_mode': 'direct_execution', 'unresolved_obligation': 'present'}, {}, 'llm_fallback'),
                 ({'entry_mode': 'direct_execution', 'unresolved_obligation': 'unclear'}, {}, 'llm_fallback'),
                 ({'entry_mode': 'direct_execution'}, {'known_obligations': ['required_review']}, 'llm_fallback')]
        for i, (answers, data, route) in enumerate(cases):
            with self.subTest(i=i):
                context = dict(FIXTURE['context'], explicit_method='sra', **data)
                report, provider = self.run_graph(answers, context, root=self.root / str(i))
                self.assertEqual(report['result']['route'], route)
                self.assertEqual(provider.calls, [['entry_mode', 'unresolved_obligation']])
                self.assertEqual(report['result']['consumption'], 'not_executed')
                self.assertTrue(set(data.get('known_obligations', [])) <= set(report['result']['obligations']))

    def test_known_obligation_change_invalidates_entry_state(self):
        self.run_graph()
        context = dict(FIXTURE['context'], known_obligations=['new_evidence_ceiling'])
        report, provider = self.run_graph(context=context)
        self.assertEqual(provider.calls, [['entry_mode', 'unresolved_obligation']])
        self.assertEqual(report['result']['route'], 'llm_fallback')
        self.assertIn('new_evidence_ceiling', report['result']['obligations'])

    def test_partial_batch_failure_keeps_successful_obligation(self):
        for status in ('missing_context', 'unsupported', 'provider_error', 'abstain'):
            report, provider = self.run_graph({
                'entry_mode': asdict(DecisionResult(status)),
                'unresolved_obligation': 'present'}, root=self.root / status)
            self.assertEqual(report['result']['status'], status)
            self.assertIn('unresolved_entry_obligation', report['result']['obligations'])
            self.assertEqual(len(provider.calls), 1)

    def test_high_confidence_cannot_override_obligation_or_grant_execution(self):
        report, provider = self.run_graph({'entry_mode': asdict(DecisionResult(
            'ok', 'direct_execution', {'source': 'provider_distribution', 'confidence': 1.0})),
            'unresolved_obligation': 'present'})
        self.assertEqual(report['result']['route'], 'llm_fallback')
        self.assertEqual(report['result']['consumption'], 'not_executed')
        self.assertEqual(report['result']['reason'], 'unresolved_or_conflicting_judgment')
        self.assertEqual(len(provider.calls), 1)

    def test_entry_no_match_and_transport_failure_have_distinct_reasons(self):
        no_match, _ = self.run_graph({'entry_mode': 'unclear'}, root=self.root / 'no-match')
        failure, _ = self.run_graph({'entry_mode': asdict(DecisionResult('provider_error'))},
                                    root=self.root / 'failed')
        self.assertEqual(no_match['result']['reason'], 'entry_mode_no_match')
        self.assertEqual(no_match['result']['status'], 'abstain')
        self.assertEqual(failure['result']['reason'], 'entry_mode:provider_error')
        self.assertEqual(failure['result']['status'], 'provider_error')

    def test_cycle_unknown_parent_rejected(self):
        for graph in [{'dependencies': {'a': ['b'], 'b': ['a']}}, {'dependencies': {'a': ['missing']}}]:
            with self.subTest(graph=graph), self.assertRaises(ContractError):
                c01.validate_graph(graph)



class C01HandoffTests(unittest.TestCase):
    """Host-boundary checks: preparing context is not execution evidence."""
    setUp = C01Tests.setUp
    tearDown = C01Tests.tearDown
    run_graph = C01Tests.run_graph

    def test_all_routes_prepare_without_inference_or_inventing_consumption(self):
        scenarios = [({}, {}, 'intervene'), ({'entry_mode': 'direct_execution'}, {}, 'direct_execute'),
                     ({'entry_mode': 'acquire_information'}, {}, 'acquire_information'),
                     ({'unresolved_obligation': 'present'}, {}, 'llm_fallback'),
                     ({}, {'freshness': 'stale'}, 'original_path')]
        for i, (answers, changes, route) in enumerate(scenarios):
            with self.subTest(route=route):
                root = self.root / str(i)
                context = dict(FIXTURE['context'], **changes)
                report, _ = self.run_graph(answers, context, root=root)
                before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
                with patch.object(FixtureProvider, 'evaluate', side_effect=AssertionError('no inference')):
                    bundle = handoff.prepare(root, report['run_id'], context, ROOT)
                self.assertEqual(bundle['proposal']['route'], route)
                self.assertEqual(bundle['context'], context)
                self.assertEqual(bundle['consumption'], 'not_executed')
                self.assertEqual(bundle['native_skill_load'], 'not_observed')
                self.assertEqual(bundle['task_acceptance'], 'not_evaluated')
                self.assertEqual(bundle['evidence_kind'], 'offline_fixture')
                if route == 'intervene':
                    self.assertEqual(bundle['selected_method']['content'], (ROOT / 'skills/sra/SKILL.md').read_text())
                else:
                    self.assertIsNone(bundle['selected_method'])
                self.assertTrue(handoff.host_prompt(bundle))
                self.assertEqual(before, {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_obligations_and_explicit_constraint_survive_handoff(self):
        context = dict(FIXTURE['context'], explicit_method='sra', known_obligations=['required_review'])
        report, _ = self.run_graph({'entry_mode': 'direct_execution'}, context)
        bundle = handoff.prepare(self.root, report['run_id'], context, ROOT)
        self.assertEqual(bundle['context']['explicit_method'], 'sra')
        self.assertIn('required_review', bundle['proposal']['obligations'])
        self.assertEqual(bundle['proposal']['route'], 'llm_fallback')
        self.assertIsNone(bundle['selected_method'])

    def test_changed_context_and_traversal_id_are_rejected(self):
        report, _ = self.run_graph()
        with self.assertRaises(ContractError):
            handoff.prepare(self.root, report['run_id'], dict(FIXTURE['context'], request='Another task'), ROOT)
        with self.assertRaises(ContractError):
            handoff.prepare(self.root, '../policy', FIXTURE['context'], ROOT)

    def test_resigned_final_result_cannot_override_recorded_decisions(self):
        report, _ = self.run_graph()
        path = self.root / 'runs' / (report['run_id'] + '.json')
        record = read_record(path)
        record['result']['owner'] = 'wae'
        path.write_bytes(canonical({'schema': 'mindthus.decision-record.v1', 'payload': record, 'sha256': digest(record)}))
        with self.assertRaises(handoff.ReplayMismatch):
            handoff.prepare(self.root, report['run_id'], FIXTURE['context'], ROOT)

    def test_changed_method_contract_blocks_handoff(self):
        report, _ = self.run_graph()
        original = Path.read_text
        def changed(path, *args, **kwargs):
            if path == ROOT / 'skills/sra/SKILL.md':
                return 'Changed full contract.'
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', changed), self.assertRaises(handoff.ReplayMismatch):
            handoff.prepare(self.root, report['run_id'], FIXTURE['context'], ROOT)

    def test_missing_outcome_cannot_turn_into_an_ordinary_fallback(self):
        report, _ = self.run_graph({'unresolved_obligation': 'present'})
        (self.root / 'calls' / report['call_keys'][0] / 'outcome.json').unlink()
        with self.assertRaises(ContractError):
            handoff.prepare(self.root, report['run_id'], FIXTURE['context'], ROOT)

    def test_runtime_lock_mismatch_blocks_handoff(self):
        report, _ = self.run_graph()
        path = self.root / 'resolved-runtime.json'
        record = read_record(path); record['model'] = 'different-model'
        path.write_bytes(canonical({'schema': 'mindthus.decision-record.v1', 'payload': record, 'sha256': digest(record)}))
        with self.assertRaises(handoff.ReplayMismatch):
            handoff.prepare(self.root, report['run_id'], FIXTURE['context'], ROOT)

    def test_active_writer_blocks_handoff_without_waiting_or_mutating(self):
        with Session(self.root, FixtureProvider(FIXTURE['answers']), scope='c01') as session:
            report = c01.run(session, FIXTURE['context'], ROOT)
            with self.assertRaises(handoff.ReplayMismatch):
                handoff.prepare(self.root, report['run_id'], FIXTURE['context'], ROOT)
        self.assertEqual(handoff.prepare(self.root, report['run_id'], FIXTURE['context'], ROOT)
                         ['proposal']['route'], 'intervene')

    def test_rejected_method_keeps_verified_contract_without_selecting_it(self):
        context = dict(FIXTURE['context'], explicit_method='wae')
        report, _ = self.run_graph({'entry_mode': 'direct_execution', 'applicable': 'no'}, context)
        bundle = handoff.prepare(self.root, report['run_id'], context, ROOT)
        self.assertEqual(bundle['proposal']['route'], 'llm_fallback')
        self.assertIsNone(bundle['proposal']['owner'])
        self.assertIsNone(bundle['selected_method'])
        check = bundle['fallback_method_check']
        self.assertEqual((check['owner'], check['status'], check['value']), ('wae', 'ok', 'no'))
        self.assertEqual(check['content'], (ROOT / 'skills/wae/SKILL.md').read_text())
        self.assertEqual(check['sha256'], report['identity']['graph']['selected_method_sha256'])
        self.assertEqual(bundle['consumption'], 'not_executed')

    def test_unclear_and_failed_checks_are_not_relabelled_as_rejection(self):
        for i, answer in enumerate(['unclear', asdict(DecisionResult('provider_error'))]):
            report, _ = self.run_graph({'applicable': answer}, root=self.root / str(i))
            bundle = handoff.prepare(self.root / str(i), report['run_id'], FIXTURE['context'], ROOT)
            check = bundle['fallback_method_check']
            self.assertEqual((check['status'], check['value']),
                             ('ok', 'unclear') if i == 0 else ('provider_error', None))
            self.assertIsNone(bundle['selected_method'])

    def test_entry_block_does_not_invent_a_method_check(self):
        report, _ = self.run_graph({'unresolved_obligation': 'present'})
        bundle = handoff.prepare(self.root, report['run_id'], FIXTURE['context'], ROOT)
        self.assertIsNone(bundle['fallback_method_check'])
        self.assertIsNone(bundle['selected_method'])



class C01HostTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'chain'
        self.env = patch.dict(os.environ, {'TYPESAFE_API_KEY': 'offline-fixture'})
        self.env.start(); self.addCleanup(self.env.stop)
        self.routing_calls = []; self.host_calls = []
        self.values = dict(FIXTURE['answers'])

    def native(self, url, headers, body, timeout):
        self.routing_calls.append(body)
        return {'model': body['model'], 'answers': {
            k: {'type': 'choice', 'choice': self.values[k], 'confidence': 1.,
                'probabilities': {o: float(o == self.values[k]) for o in q['criteria']}}
            for k, q in body['questions'].items()}, 'usage': {'input_tokens': 10, 'output_tokens': 2}}

    def host(self, url, headers, body, timeout):
        self.host_calls.append(body)
        self.assertEqual(url, c01_host.ENDPOINT)
        self.assertNotIn('tools', body)
        return {'model': body['model'], 'choices': [{'finish_reason': 'stop', 'message': {'content': 'Fixture answer'}}],
                'usage': {'prompt_tokens': 10, 'completion_tokens': 2}}

    def run_chain(self, context=None, host=None):
        manifest = c01_host.admission(context or FIXTURE['context'], ROOT, c01_host.MODELS[0], 'offline transport test')
        return c01_host.run(manifest, self.root, 'offline-host',
                            provider=TypeSafeJevProvider(transport=self.native, choice_rounding=True),
                            host_transport=host or self.host)

    def test_full_chain_and_completed_reentry_do_not_repay(self):
        first = self.run_chain()
        second = self.run_chain()
        self.assertEqual(first, second)
        self.assertEqual(first['status'], 'complete')
        self.assertEqual((len(self.routing_calls), len(self.host_calls)), (3, 1))
        prompt = self.host_calls[0]['messages'][1]['content']
        self.assertIn('Scarce Resource', prompt)
        self.assertEqual(first['routing']['result']['consumption'], 'not_executed')
        self.assertEqual(first['host']['native_skill_load'], 'not_observed')
        self.assertFalse(first['qualification'])

    def test_unknown_host_attempt_never_repeats(self):
        def interrupted(*args):
            self.host_calls.append('attempted')
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt): self.run_chain(host=interrupted)
        self.assertTrue((self.root / 'host/intent.json').exists())
        self.assertFalse((self.root / 'host/outcome.json').exists())
        with self.assertRaises(RecoveryRequired): self.run_chain()
        self.assertEqual((len(self.routing_calls), len(self.host_calls)), (3, 1))

    def test_model_drift_and_truncation_are_terminal_without_backup(self):
        for i, failure in enumerate(['model', 'length']):
            self.root = Path(self.temp.name) / str(i)
            def wrong(*args):
                raw = self.host(*args)
                if failure == 'model': raw['model'] = c01_host.MODELS[1]
                else: raw['choices'][0]['finish_reason'] = 'length'
                return raw
            result = self.run_chain(host=wrong)
            before = (len(self.routing_calls), len(self.host_calls))
            self.assertEqual(result['status'], 'host_failed')
            self.assertIsNone(result['host']['answer'])
            self.assertEqual(self.run_chain(), result)
            self.assertEqual((len(self.routing_calls), len(self.host_calls)), before)

    def test_rejected_method_reaches_host_as_evidence_not_selection(self):
        self.values.update(entry_mode='direct_execution', applicable='no')
        context = dict(FIXTURE['context'], explicit_method='wae')
        result = self.run_chain(context)
        bundle = read_record(self.root / 'handoff.json')
        self.assertIsNone(bundle['selected_method'])
        self.assertEqual(bundle['fallback_method_check']['value'], 'no')
        self.assertEqual(result['routing']['result']['route'], 'llm_fallback')
        self.assertEqual((len(self.routing_calls), len(self.host_calls)), (2, 1))

    def test_changed_frozen_input_blocks_all_calls(self):
        manifest = c01_host.admission(FIXTURE['context'], ROOT, c01_host.MODELS[0], 'offline transport test')
        manifest = copy.deepcopy(manifest); manifest['context']['request'] = 'changed'
        with self.assertRaises(ContractError):
            c01_host.run(manifest, self.root, 'offline-host', host_transport=self.host)
        self.assertEqual(self.host_calls, [])
        self.assertFalse(self.root.exists())

    def test_routing_failure_stops_before_host_and_does_not_retry(self):
        def failed(*args):
            self.routing_calls.append('failed'); raise ProviderError('transport_failure')
        self.native = failed
        result = self.run_chain()
        self.assertEqual(result['status'], 'routing_failed')
        self.assertIsNone(result['host'])
        self.run_chain()
        self.assertEqual((len(self.routing_calls), len(self.host_calls)), (1, 0))

    def test_d0_returns_to_host_without_native_inference(self):
        result = self.run_chain(dict(FIXTURE['context'], freshness='stale'))
        self.assertEqual(result['routing']['result']['route'], 'original_path')
        self.assertEqual((len(self.routing_calls), len(self.host_calls)), (0, 1))

    def test_missing_host_key_blocks_before_routing(self):
        manifest = c01_host.admission(FIXTURE['context'], ROOT, c01_host.MODELS[0], 'offline transport test')
        with self.assertRaises(ContractError):
            c01_host.run(manifest, self.root, '',
                        provider=TypeSafeJevProvider(transport=self.native, choice_rounding=True), host_transport=self.host)
        self.assertEqual((len(self.routing_calls), len(self.host_calls)), (0, 0))


class LiveCarrierTests(unittest.TestCase):
    """Injected native transport only; these tests produce no semantic evidence."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # Exercise the historical carrier mechanics with an explicitly synthetic
        # current-source freeze. Production FREEZE remains immutable and rejects v3.
        self.historical_freeze = campaign.FREEZE
        freeze = json.loads((ROOT / self.historical_freeze).read_text())
        freeze['graph'] = c01.GRAPH
        freeze['file_sha256'] = {name: campaign.sha(ROOT / name)
                                 for name in freeze['file_sha256']}
        test_freeze = self.root / 'test-only-freeze.json'
        test_freeze.write_text(json.dumps(freeze))
        self.freeze_patch = patch.object(campaign, 'FREEZE', test_freeze)
        self.freeze_patch.start()
        self.addCleanup(self.freeze_patch.stop)
        self.network = []
        self.env = patch.dict(os.environ, {'TYPESAFE_API_KEY': 'fixture-only-credential'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def native(self, choose, usage=None):
        def transport(url, headers, body, timeout):
            self.network.append(body)  # Deliberately exclude authorization headers.
            return {'model': 'jev-1.13.0', 'answers': {
                key: {'type': 'choice', 'choice': choose(key, body['state']),
                      'probabilities': {v: float(v == choose(key, body['state']))
                                        for v in question['criteria']}, 'confidence': 1.0}
                for key, question in body['questions'].items()},
                'usage': usage or {'input_tokens': 10, 'output_tokens': 1}}
        return TypeSafeJevProvider(transport=transport)

    def admission(self, provider, **delta):
        return dict({'scope': 'test', 'implementation': implementation_digest(),
                     'provider_configuration': provider_configuration(provider),
                     'limits': asdict(Limits()), 'request_allowlist': [
                         campaign.request_key([spec()], {'text': v}) for v in ('first', 'second')],
                     'max_cost_usd': .01, 'reserve_per_call_usd': .01,
                     'authorization_ref': 'Injected transport unit test only',
                     'freeze_sha256': 'a' * 64}, **delta)

    def test_live_admission_rejects_identity_changes_before_transport(self):
        provider = self.native(lambda *_: 'yes')
        for delta in ({'scope': 'other'}, {'implementation': 'b' * 64},
                      {'limits': asdict(Limits(max_calls=9))}, {'freeze_sha256': 'z' * 64},
                      {'max_cost_usd': 2}):
            with self.subTest(delta=delta), self.assertRaises(ContractError):
                Session(self.root, provider, scope='test', live_admission=self.admission(provider, **delta))
        self.assertEqual(self.network, [])

    def test_live_egress_and_input_admission_are_detached(self):
        provider = self.native(lambda *_: 'yes')
        admission = self.admission(provider)
        with Session(self.root, provider, scope='test', live_admission=admission) as session:
            admission['request_allowlist'].append(campaign.request_key([spec()], {'text': 'extra'}))
            with self.assertRaisesRegex(ContractError, 'outside frozen live egress'):
                session.evaluate([spec()], {'text': 'extra'})
        self.assertEqual(self.network, [])

    def test_reserved_cost_survives_resume_but_cache_is_free(self):
        provider = self.native(lambda *_: 'yes')
        admission = self.admission(provider)
        for index in range(2):
            with Session(self.root, provider, scope='test', live_admission=admission) as session:
                session.evaluate([spec()], {'text': 'first'})
                self.assertEqual(session.calls_reused, index)
                report = session.finish({'id': 'test'}, {'text': 'first'}, {'route': 'test'})
                self.assertEqual(report['evidence_kind'], 'live_model')
                with self.assertRaisesRegex(ContractError, 'cost reservation exhausted'):
                    session.evaluate([spec()], {'text': 'second'})
        self.assertEqual(len(self.network), 1)
        self.assertIsNone(report['trial_usage']['cost_usd'])

    def test_cost_policy_cannot_expand_after_restart(self):
        provider = self.native(lambda *_: 'yes')
        with Session(self.root, provider, scope='test', live_admission=self.admission(provider)):
            pass
        with self.assertRaises(ContractError):
            with Session(self.root, provider, scope='test',
                         live_admission=self.admission(provider, max_cost_usd=.02)):
                self.fail('budget expanded')

    def test_actual_cost_over_reserve_stops_next_call(self):
        provider = self.native(lambda *_: 'yes', {'input_tokens': 1, 'output_tokens': 1, 'cost': .02})
        with Session(self.root, provider, scope='test',
                     live_admission=self.admission(provider, max_cost_usd=.03)) as session:
            session.evaluate([spec()], {'text': 'first'})
            with self.assertRaisesRegex(ContractError, 'observed cost exceeds reserve'):
                session.evaluate([spec()], {'text': 'second'})
        self.assertEqual(len(self.network), 1)

    def test_prepare_frozen_egress_without_transport_or_label_access(self):
        provider = self.native(lambda *_: self.fail('preparation called transport'))
        manifest, cases = campaign.prepare(ROOT, provider)
        self.assertEqual(len(cases), 26)
        self.assertEqual(len(manifest['admission']['request_allowlist']), 225)
        self.assertNotIn('expected', canonical(manifest).decode())
        self.assertEqual(self.network, [])
        original = Path.read_text
        def poison_labels(path, *args, **kwargs):
            text = original(path, *args, **kwargs)
            if path == ROOT / campaign.DATA:
                data = json.loads(text)
                for case in data['cases']:
                    del case['expected']
                    del case['rationale']
                return json.dumps(data)
            return text
        with patch.object(Path, 'read_text', poison_labels):
            unlabeled, _ = campaign.prepare(ROOT, provider)
        self.assertEqual(unlabeled, manifest)

    def test_historical_c01_freeze_rejects_v3_without_transport(self):
        with patch.object(campaign, 'FREEZE', self.historical_freeze):
            with self.assertRaisesRegex(ContractError, 'frozen source/data changed'):
                campaign.prepare(ROOT, TypeSafeJevProvider())
        self.assertEqual(self.network, [])

    def test_prepare_rejects_changed_freeze_source(self):
        with patch.object(campaign, 'sha', return_value='b' * 64), self.assertRaises(ContractError):
            campaign.prepare(ROOT, TypeSafeJevProvider())

    def test_campaign_stops_dangerous_direct_once_and_refuses_rerun(self):
        provider = self.native(lambda key, _: {'entry_mode': 'direct_execution',
                                              'unresolved_obligation': 'clear'}[key])
        manifest, cases = campaign.prepare(ROOT, provider)
        write_once(self.root / 'campaign.json', manifest)
        result = campaign.run(ROOT, self.root, provider, manifest, cases)
        self.assertEqual(result['cases_completed'], 1)
        self.assertEqual(result['stop_reason'], 'hard_judgment_sent_to_direct')
        self.assertFalse(result['development_thresholds_met'])
        with self.assertRaisesRegex(ContractError, 'already finished'):
            campaign.run(ROOT, self.root, provider, manifest, cases)
        self.assertEqual(len(self.network), 1)

    def test_campaign_mocked_full_report_and_no_label_egress(self):
        # A keyed answer script verifies the evaluator, never model competence.
        cases = json.loads((ROOT / campaign.DATA).read_text())['cases']
        answers = {c['context']['provenance']['source_ref']: c['expected'] for c in cases}
        provider = self.native(lambda key, state: answers[state['provenance']['source_ref']][key])
        manifest, cases = campaign.prepare(ROOT, provider)
        write_once(self.root / 'campaign.json', manifest)
        result = campaign.run(ROOT, self.root, provider, manifest, cases)
        self.assertTrue(result['development_thresholds_met'])
        self.assertEqual((result['d0_matches'], result['entry_matches'], result['route_matches']), (26, 25, 25))
        self.assertEqual((result['owner_matches'], result['applicability_matches']), (12, 12))
        self.assertEqual(len(result['family_pairs']), 13)
        self.assertTrue(all(f['all_match'] for f in result['family_pairs'].values()))
        self.assertIsNone(result['trial_usage']['cost_usd'])
        self.assertEqual(result['unique_calls'], len(self.network))
        self.assertEqual(result['case_results'][22]['call_keys'], [])  # stale D23
        for body in self.network:
            self.assertFalse({'expected', 'rationale', 'family_group', 'cases'} & set(body['state']))
        self.assertEqual(result['case_results'][17]['observed']['selected_owner'], 'wae')
        self.assertEqual(result['case_results'][17]['observed']['applicable'], 'no')

    def test_campaign_transport_failure_is_recorded_without_retry(self):
        def fail(*_):
            self.network.append('attempt')
            raise ProviderError('untrusted remote text fixture-only-credential')
        provider = TypeSafeJevProvider(transport=fail)
        manifest, cases = campaign.prepare(ROOT, provider)
        write_once(self.root / 'campaign.json', manifest)
        result = campaign.run(ROOT, self.root, provider, manifest, cases)
        self.assertEqual(result['stop_reason'], 'provider_or_contract_failure')
        self.assertEqual(result['provider_status_failures'], ['D01'])
        self.assertEqual(len(self.network), 1)
        self.assertNotIn('fixture-only-credential', ''.join(p.read_text() for p in self.root.rglob('*.json')))

    def test_campaign_rejects_missing_key_before_any_intent(self):
        provider = self.native(lambda *_: self.fail('network called'))
        manifest, cases = campaign.prepare(ROOT, provider)
        write_once(self.root / 'campaign.json', manifest)
        with patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(ContractError, 'credential'):
            campaign.run(ROOT, self.root, provider, manifest, cases)
        self.assertFalse((self.root / 'calls').exists())


    def test_hidden_key_cli_removes_process_credential_after_failure(self):
        provider = TypeSafeJevProvider()
        manifest, _ = campaign.prepare(ROOT, provider)
        write_once(self.root / 'campaign.json', manifest)
        with patch.dict(os.environ, {}, clear=True), patch('sys.stdin.isatty', return_value=True), \
                patch.object(campaign.getpass, 'getpass', return_value='fixture-secret'), \
                patch.object(campaign, 'run', side_effect=RecoveryRequired('no retry')), \
                patch('builtins.print') as output:
            self.assertEqual(campaign.main(['run', '--state-root', str(self.root), '--prompt-key']), 2)
            self.assertNotIn('TYPESAFE_API_KEY', os.environ)
            self.assertNotIn('fixture-secret', str(output.call_args_list))

    def test_hidden_key_cli_rejects_nonterminal_before_prompt(self):
        manifest, _ = campaign.prepare(ROOT, TypeSafeJevProvider())
        write_once(self.root / 'campaign.json', manifest)
        with patch('sys.stdin.isatty', return_value=False), \
                patch.object(campaign.getpass, 'getpass') as prompt, patch('builtins.print'):
            self.assertEqual(campaign.main(['run', '--state-root', str(self.root), '--prompt-key']), 2)
            prompt.assert_not_called()


    def test_last_completed_call_over_reserve_stops_campaign(self):
        provider = self.native(lambda key, _: {'entry_mode': 'direct_execution',
                                              'unresolved_obligation': 'clear'}[key],
                               {'input_tokens': 10, 'output_tokens': 1, 'cost': .03})
        manifest, cases = campaign.prepare(ROOT, provider)
        # Isolate the D02 one-call path, so there is no later Session call to detect overspend.
        cases = [cases[1]]
        manifest['case_ids'] = [cases[0]['id']]
        write_once(self.root / 'campaign.json', manifest)
        result = campaign.run(ROOT, self.root, provider, manifest, cases)
        self.assertEqual(result['stop_reason'], 'reported_cost_exceeds_reserve')
        self.assertFalse(result['development_thresholds_met'])
        self.assertEqual(len(self.network), 1)


    def test_malformed_response_preserves_numeric_evidence_and_bounded_error(self):
        def transport(*_):
            return {'model': 'jev-1.13.0', 'answers': {
                key: {'type': 'choice', 'choice': value, 'confidence': .7,
                      'probabilities': probabilities, 'remote_text': 'fixture-secret'}
                for key, value, probabilities in [
                    ('entry_mode', 'mindthus_intervention', {'direct_execution': .1,
                     'acquire_information': .1, 'mindthus_intervention': .7, 'unclear': .09}),
                    ('unresolved_obligation', 'clear', {'clear': 1., 'present': 0., 'unclear': 0.})]},
                'usage': {'input_tokens': 123, 'output_tokens': 45}, 'debug': 'fixture-secret'}
        provider = TypeSafeJevProvider(transport=transport)
        manifest, cases = campaign.prepare(ROOT, provider)
        write_once(self.root / 'campaign.json', manifest)
        result = campaign.run(ROOT, self.root, provider, manifest, cases)
        outcome = read_record(next((self.root / 'calls').glob('*/outcome.json')))
        self.assertEqual(outcome['results']['entry_mode']['reason'],
                         'ContractError:distribution_not_normalized')
        wire = read_record(next((self.root / 'wire').glob('*.json')))
        self.assertEqual(wire['usage']['input_tokens'], 123)
        self.assertEqual(wire['answers']['entry_mode']['probabilities']['unclear'], .09)
        self.assertNotIn('fixture-secret', str(wire))
        self.assertEqual(result['cases_completed'], 1)

    def test_wire_observer_suppresses_remote_secret_values_and_extra_keys(self):
        raw = {'model': 'fixture-secret', 'answers': {'test': {
            'type': 'fixture-secret', 'choice': 'fixture-secret', 'confidence': 'fixture-secret',
            'probabilities': {'yes': 'fixture-secret', 'no': .5, 'fixture-secret': .1}},
            'fixture-secret': {}}, 'usage': {'input_tokens': 'fixture-secret'}}
        body = {'state': {'text': 'fixture'}, 'questions': {'test': {'criteria': spec().criteria}}}
        got = campaign.observed_transport(self.root, lambda *_: raw)('unused', {}, body, 1)
        self.assertIs(got, raw)  # observation never fixes/rewrites model output
        self.assertNotIn('fixture-secret', next((self.root / 'wire').glob('*.json')).read_text())

    def test_technical_recovery_keeps_failure_identity_and_cumulative_reserve(self):
        provider = self.native(lambda *_: 'yes')
        parent = self.root / 'parent'
        manifest, _ = campaign.prepare(ROOT, provider)
        manifest['admission']['implementation'] = 'a' * 64
        write_once(parent / 'campaign.json', manifest)
        write_once(parent / 'summary.json', {'stop_reason': 'provider_or_contract_failure'})
        for directory in ('calls/first', 'transport-diagnostic-1'):
            write_once(parent / directory / 'intent.json', {'attempt': True})
            write_once(parent / directory / 'outcome.json', {'completed': True})
        recovered, _ = campaign.prepare(ROOT, provider, parent, 'Add safe failure observation')
        self.assertEqual(recovered['technical_recovery']['ordinal'], 2)
        self.assertEqual(recovered['technical_recovery']['parent_root'], str(parent.resolve()))
        self.assertAlmostEqual(recovered['admission']['max_cost_usd'], manifest['admission']['max_cost_usd'] - 2 * campaign.RESERVE_PER_CALL)
        self.assertEqual(recovered['dataset_sha256'], manifest['dataset_sha256'])
        (parent / 'calls/first/outcome.json').unlink()
        with self.assertRaisesRegex(ContractError, 'unresolved parent call'):
            campaign.prepare(ROOT, provider, parent, 'Add safe failure observation')

    def test_technical_recovery_rejects_unchanged_source_or_semantic_failure(self):
        for index, reason in enumerate(('provider_or_contract_failure', 'hard_judgment_sent_to_direct')):
            parent = self.root / str(index)
            manifest, _ = campaign.prepare(ROOT, TypeSafeJevProvider())
            write_once(parent / 'campaign.json', manifest)
            write_once(parent / 'summary.json', {'stop_reason': reason})
            with self.assertRaises(ContractError):
                campaign.prepare(ROOT, TypeSafeJevProvider(), parent, 'No implementation delta')


class C02Tests(unittest.TestCase):
    def setUp(self):
        docs = ROOT / 'docs/internal/research/typed-decision'
        self.contract = json.loads((docs / 'review-remediation/c02-contract-v2.json').read_text())
        self.data = json.loads((docs / 'c02-zh-development.json').read_text())['cases'][0]['context']
        self.data['tvg_contract'] = (ROOT / 'skills/tvg/SKILL.md').read_text()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.answers = {'utility': 'deficit', 'support': 'sufficient', 'action': 'make_actionable',
                        'recheck_utility': 'adequate', 'recheck_fidelity': 'faithful'}

    def session(self, answers=None):
        return Session(self.root, FixtureProvider(answers or self.answers), scope='c02-offline')

    def test_independent_choices_share_one_batch(self):
        with self.session() as s:
            report = c02.plan(s, self.data, self.contract)
            self.assertEqual(s.provider.calls, [['utility', 'support', 'action']])
            self.assertEqual(report['result']['action'], 'make_actionable')
            self.assertEqual(report['result']['consumption'], 'not_executed')
            self.assertIsNone(report['result']['exit_state'])
            first = read_record(self.root / 'calls' / s.records[0]['call_key'] / 'intent.json')
            self.assertTrue(all('weaknesses' not in q['required_context']
                                for q in first['identity']['questions']))

    def test_missing_evidence_never_selects_rewrite(self):
        with self.session({**self.answers, 'support': 'missing'}) as s:
            report = c02.plan(s, self.data, self.contract)
            self.assertEqual(report['result']['route'], 'acquire_information')
            self.assertEqual(len(s.provider.calls), 1)
            with self.assertRaises(ContractError):
                c02.begin_rewrite(s, report, self.data, self.contract, 'test-generator')

    def test_scope_or_target_conflict_discards_speculative_action(self):
        for value in ('outside_scope', 'conflict', 'unclear'):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as root:
                with Session(Path(root), FixtureProvider({**self.answers, 'utility': value}), scope=value) as s:
                    report = c02.plan(s, self.data, self.contract)
                    self.assertEqual(report['result']['route'], 'original_exit_owner')
                    self.assertEqual(len(s.provider.calls), 1)

    def test_mechanical_admission_zero_calls(self):
        for change in ({'freshness': 'old'}, {'permission': {'mode': 'execute'}},
                       {'target': {**self.data['target'], 'source_ref': self.data['source_ref']}}):
            with self.subTest(change=change), self.session() as s:
                report = c02.plan(s, {**self.data, **change}, self.contract)
                self.assertEqual(report['result']['route'], 'original_exit_owner')
                self.assertEqual(s.calls_made, 0)

    def test_adequate_and_abstain_have_no_automatic_exit(self):
        for value in ('leave_unchanged', 'abstain'):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as root:
                with Session(Path(root), FixtureProvider({**self.answers, 'action': value}), scope=value) as s:
                    report = c02.plan(s, self.data, self.contract)
                    self.assertEqual(report['result']['route'], 'original_exit_owner')
                    self.assertIsNone(report['result']['exit_state'])

    def test_resume_reuses_planning_batch(self):
        with self.session() as s:
            original = c02.plan(s, self.data, self.contract)
        with self.session() as s:
            resumed = c02.plan(s, self.data, self.contract)
            self.assertEqual(original['run_id'], resumed['run_id'])
            self.assertEqual((s.calls_made, s.calls_reused), (0, 1))

    def test_generation_intent_blocks_blind_retry(self):
        with self.session() as s:
            report = c02.plan(s, self.data, self.contract)
            c02.begin_rewrite(s, report, self.data, self.contract, 'test-generator')
            with self.assertRaises(RecoveryRequired):
                c02.begin_rewrite(s, report, self.data, self.contract, 'test-generator')

    def test_one_actual_rewrite_then_one_recheck_and_replay(self):
        with self.session() as s:
            report = c02.plan(s, self.data, self.contract)
            c02.begin_rewrite(s, report, self.data, self.contract, 'test-generator')
            c02.record_rewrite(s, report['run_id'], 'fixture output, not semantic evidence',
                generation_evidence='offline-fixture', usage={'input_tokens': None, 'output_tokens': None, 'cost_usd': None})
            checked = c02.recheck(s, report, self.data, self.contract)
            self.assertEqual(s.calls_made, 2)
            self.assertEqual(checked['result']['route'], 'original_exit_owner')
            self.assertIsNone(checked['result']['exit_state'])
            again = c02.recheck(s, report, self.data, self.contract)
            self.assertEqual(again['run_id'], checked['run_id'])
            self.assertEqual(s.calls_made, 2)
            with self.assertRaisesRegex(ContractError, 'second rewrite'):
                c02.record_rewrite(s, report['run_id'], 'another output', generation_evidence='offline-fixture',
                    usage={'input_tokens': None, 'output_tokens': None, 'cost_usd': None})

    def test_changed_target_invalidates_rewrite_handoff(self):
        with self.session() as s:
            report = c02.plan(s, self.data, self.contract)
            changed = {**self.data, 'target': {**self.data['target'], 'standard': 'different'}}
            with self.assertRaisesRegex(ContractError, 'lineage'):
                c02.begin_rewrite(s, report, changed, self.contract, 'test-generator')

    def test_design_is_declarative_and_answer_policy_must_match(self):
        bad = copy.deepcopy(self.contract)
        bad['action']['criteria']['shell_command'] = 'arbitrary execution'
        with self.assertRaises(ContractError):
            c02.specs(bad)
        bad = copy.deepcopy(self.contract)
        del bad['utility']['criteria']['unclear']
        with self.assertRaises(ContractError):
            c02.specs(bad)

    def test_old_live_campaign_rejects_new_implementation(self):
        from experiments.typed_decision import c02_trial
        with self.assertRaisesRegex(ContractError, 'frozen source changed'):
            c02_trial.prepare(ROOT, TypeSafeJevProvider())

    def test_planning_projection_excludes_labels_and_upstream_answers(self):
        from experiments.typed_decision.contracts import project_context
        questions = c02.specs(self.contract)
        view = project_context(questions, self.data)
        poisoned = {**self.data, 'expected': 'secret-gold', 'rationale': 'secret-gold',
                    'weaknesses': {'utility': 'deficit'}}
        self.assertEqual(view, project_context(questions, poisoned))

    def test_rewrite_id_cannot_escape_journal(self):
        with self.assertRaises(ContractError):
            c02.rewrite_directory(self.root, '../' * 22)


if __name__ == '__main__':
    unittest.main()
