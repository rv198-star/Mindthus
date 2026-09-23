"""Offline diagnosis only; no credentials, network, live execution, or journal mutation.

The scalar examples are synthetic counterexamples, not recovered Jev responses.
D1 replays saved observations and authored text in a temporary fixture namespace.
"""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / 'experiments/typed_decision').is_dir())
sys.path.insert(0, str(REPO))
from experiments.typed_decision import entry, relationship_runtime as rt, route_control as rc
from experiments.typed_decision.contracts import BatchResult, DecisionSpec, ResolvedRuntime, canonical, digest
from experiments.typed_decision.providers import FixtureProvider, JevEngine
from experiments.typed_decision.session import Limits, Session, implementation_digest, read_record

BATCH = Path('/srv/agentdock/tmp/mindthus-six-scenes-current-agent-v1')
PLAN = HERE.parent


def tree_hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


class SyntheticWire(FixtureProvider):
    """Same Jev decode/BatchResult validation called by the production adapter."""
    def __init__(self, wire):
        super().__init__({'explicit_offline_wire': wire})
        self.wire = wire
        self.engine = JevEngine('jev-1.13.0', choice_rounding=True)

    def evaluate(self, specs, context, timeout):
        self.calls.append([s.id for s in specs])
        batch = BatchResult(self.engine.results(specs, deepcopy(self.wire)),
                            ResolvedRuntime('fixture-v1', self.serving_identity.provider),
                            {'input_tokens': 123, 'output_tokens': 4, 'cost_usd': None})
        batch.validate(specs)
        return batch


def probability_probe(root, name, score_probs, score_value):
    specs = [DecisionSpec('M02', 'Synthetic proposition.', {'true': 'Yes.', 'false': 'No.'},
                          ('materials',), kind='assess_proposition'),
             DecisionSpec('M03', 'Synthetic role.', {'primary': 'Primary.', 'none': 'No role.'},
                          ('materials',)),
             DecisionSpec('S02', 'Synthetic impact.', ['None.', 'Local.', 'Subtask.', 'Core.'],
                          ('materials',), kind='rate')]
    wire = {'M02': {'type': 'noul', 'noul': .95},
            'M03': {'type': 'choice', 'choice': 'primary', 'confidence': .9,
                    'probabilities': {'primary': .95, 'none': .05}},
            'S02': {'type': 'score', 'score': score_value, 'confidence': .9,
                    'probabilities': score_probs,
                    'legend': {str(i): x for i, x in enumerate(specs[2].criteria)}}}
    provider = SyntheticWire(wire)
    with Session(root / name, provider, scope='diagnostic-' + name,
                 limits=Limits(max_calls=1, max_seconds=10, max_request_bytes=8192)) as session:
        result = session.evaluate(specs, {'materials': 'Explicit synthetic numerical probe only.'})
    record = read_record(next((root / name / 'calls').glob('*/outcome.json')))
    return {'input_kind': 'synthetic_not_historical_wire_response', 'wire': wire,
            'results': {k: asdict(v) for k, v in result.items()},
            'persisted_usage': record['usage'], 'synthetic_usage_before_decode': {'input_tokens': 123, 'output_tokens': 4},
            'displayed_sum': sum(score_probs.values()),
            'displayed_weighted_score': sum(int(k) * v for k, v in score_probs.items()),
            'external_model_calls': 0}


class SavedTextHost:
    is_live = False

    def __init__(self, owner, text):
        self.identity = owner
        self.text = text
        self.configuration = {'kind': 'offline_saved_D1_text', 'text_sha256': digest(text)}
        self.seen = []

    def execute(self, request, timeout):
        self.seen.append(request['issue']['issue_id'])
        return {'route_id': request['route_id'], 'revision': request['revision'],
                'issue_id': request['issue']['issue_id'], 'performed_methods': request['execute_methods'],
                'text': self.text, 'objection': None, 'usage': deepcopy(rt.UNKNOWN_USAGE)}


class FixtureAcceptance:
    def __init__(self, owner):
        self.identity = owner
        self.configuration = {'kind': 'explicit_offline_acceptance_counterexample'}
        self.called = []

    def accept(self, edge, artifact, packet):
        self.called.append(edge['id'])
        return {'owner_ref': self.identity, 'dependency_id': edge['id'],
                'artifact_sha256': artifact['artifact_sha256'], 'accepted': True,
                'basis': 'offline premise: the producer output was accepted; no live completion claim'}


def stage_probe(root):
    specimen = next(x for x in json.loads((PLAN / 'cases.json').read_bytes())['cases'] if x['id'] == 'D1')
    packet = deepcopy(specimen['packet'])
    # Separate fixture namespace. Never touch/reidentify the real episode or its budget.
    packet['episode_id'] = 'offline-D1-post-artifact-diagnostic-' + root.name
    source = next((BATCH / 'D1').glob('turns/*/inputs/*/steps/route/calls/*/outcome.json'))
    observed = read_record(source)
    host_source = next((BATCH / 'D1').glob('turns/*/inputs/*/steps/execution__I1__1/host-response.json'))
    staged = read_record(host_source)['submission']['reply']
    provider = FixtureProvider(observed['results'])
    host = SavedTextHost(packet['authority']['owner_ref'], staged['text'])
    acceptor = FixtureAcceptance(host.identity)
    with patch.object(rt, '_registry', return_value=root / 'fixture-registry'):
        result = entry.run(root / 'fixture-episode', provider, packet, REPO, mode=rc.MODE,
                           executor=host, artifact_acceptor=acceptor)
    assert host.seen == ['I1'] and acceptor.called == ['P1']
    assert list(result['outputs']) == ['I1'] and 'I2' in result['pending']
    assert len(provider.calls) == 1
    return {'evidence_kind': 'offline_control_replay_not_new_Jev_or_host_trial',
            'observation_source': str(source), 'observation_file_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'host_source': str(host_source), 'executed_fixture_scopes': host.seen,
            'accepted_fixture_edges': acceptor.called, 'judgment_batches': len(provider.calls),
            'outputs': list(result['outputs']), 'pending': result['pending'],
            'route_roles': result['route']['per_issue'], 'external_model_calls': 0,
            'finding': 'Acceptance alone cannot activate I2: its role was set unresolved before dispatch; no post-artifact assessment exists in this run.'}


def main():
    before = tree_hashes(BATCH)
    impl = implementation_digest()
    with TemporaryDirectory(prefix='mindthus-diagnosis-') as tmp, \
         patch('urllib.request.urlopen', side_effect=AssertionError('NETWORK_FORBIDDEN')), \
         patch('urllib.request.build_opener', side_effect=AssertionError('NETWORK_FORBIDDEN')):
        root = Path(tmp)
        exact = probability_probe(root, 'exact', {'0': .02, '1': .03, '2': .11, '3': .84}, 2.77)
        assert all(v['status'] == 'ok' for v in exact['results'].values())
        rounded = probability_probe(root, 'separate_rounding', {'0': .02, '1': .03, '2': .11, '3': .84}, 2.78)
        assert all(v['status'] == 'provider_error' for v in rounded['results'].values())
        latent = [.018, .027, .111, .844]
        assert abs(sum(latent) - 1) < 1e-9
        assert [round(x, 2) for x in latent] == list(rounded['wire']['S02']['probabilities'].values())
        assert round(sum(i * x for i, x in enumerate(latent)), 2) == 2.78
        rounded['hypothetical_latent_distribution'] = latent
        rounded['causality_limit'] = 'Constructive example only: not proof these were the B1 wire values or that TypeSafe rounds this way.'
        mass = probability_probe(root, 'mass_099', {'0': .02, '1': .03, '2': .11, '3': .83}, 2.74)
        assert all(v['status'] == 'provider_error' for v in mass['results'].values())
        stage = stage_probe(root)
    assert tree_hashes(BATCH) == before, 'real records changed during offline diagnosis'
    assert implementation_digest() == impl
    report = {'scope': 'four_offline_diagnostic_controls_not_semantic_qualification',
              'checks_completed': 4, 'external_model_calls': 0, 'real_records_unchanged': True,
              'runtime_unchanged': True, 'implementation': impl,
              'exact_numeric_control': exact, 'separate_rounding_counterexample': rounded,
              'nonunit_score_mass_counterexample': mass, 'D1_post_artifact_replay': stage,
              'unproven': ['Actual discarded B1/C1 wire responses and rounding mechanism',
                           'Live correction rechecks', 'Advisory vs committed quality advantage']}
    path = HERE / 'diagnostics.json'
    if path.exists():
        assert json.loads(path.read_bytes()) == report
    else:
        path.write_bytes(canonical(report) + b'\n')
    print(json.dumps({'checks_completed': 4, 'network_calls': 0, 'old_runtime_and_records_unchanged': True,
                      'one_bad_score_invalidates_all': True, 'valid_usage_lost_on_batch_rejection': True,
                      'D1_accepted_predecessor_still_I2_pending': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
