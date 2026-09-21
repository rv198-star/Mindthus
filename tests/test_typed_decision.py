"""Offline engineering tests, not a semantic Jev benchmark or value qualification."""
import copy
from dataclasses import asdict
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.typed_decision import c01
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
    OpenRouterJevProvider,
    ProviderError,
    TypeSafeJevProvider,
    _NoRedirect,
)
from experiments.typed_decision.session import Limits, RecoveryRequired, Session, read_record
from experiments.typed_decision.trace import from_c01, validate_with_existing

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'experiments/typed_decision/fixtures/c01-sra.json').read_text())


def spec(ident='test', kind='select', criteria=None, reads=('text',)):
    if criteria is None:
        criteria = {'yes': 'positive', 'no': 'negative'}
    return DecisionSpec(ident, 'Evaluate the named criterion.', criteria, reads, kind=kind)


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
        self.assertEqual(report['result']['reason'], 'explicit_method_conflicts_with_direct')
        self.assertEqual(len(provider.calls), 1)

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


if __name__ == '__main__':
    unittest.main()
