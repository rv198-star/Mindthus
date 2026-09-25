"""Label-neutral replacement D diagnostic for source-direct observation v3.

The first D campaign exposed candidate outcome labels in model-visible metadata and is
retained as contaminated evidence.  This replacement uses opaque content identities,
neutral Codex workspaces, a program-enforced S1 gate, six A-F scenarios for Jev, and
only the preregistered A pair for the slower same-question Codex observation.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_observation_v3 as base

from experiments.typed_decision import observation_assessment as obs
from experiments.typed_decision.contracts import (
    BatchResult, DecisionResult, EngineIdentity, ResolvedRuntime, ServingIdentity,
    canonical, digest, project_context, provider_configuration, require,
)
from experiments.typed_decision.providers import ProviderError
from experiments.typed_decision.session import Limits, Session, implementation_digest, read_record

ROOT = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-source-direct-v3-d-clean')
CODEX_HOME = ROOT / 'codex-home'
SCENARIOS = {'A': 'S1', 'B': 'S2', 'C': 'S3', 'D': 'K1', 'E': 'K2', 'F': 'K3'}
VARIANTS = ('x', 'y')
EXPECTED = {'x': 'request_correction', 'y': 'continue_original'}
JEV_LIMITS = Limits(max_calls=1, max_seconds=60, max_request_bytes=98304)
CODEX_LIMITS = Limits(max_calls=1, max_seconds=240, max_request_bytes=98304)
AUTH = ('User authorized issue #211 minimum implementation validation and expansion after '
        'an effective gate. This replacement removes independently found label leakage; '
        'TypeSafe Jev and current local Codex only.')
HEX = re.compile(r'^[0-9a-f]{64}$')


def source_commit() -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=base.REPO, text=True).strip()


def variant_text(scenario: str, variant: str) -> str:
    case = base.cases()[SCENARIOS[scenario]]
    condition = 'bad' if variant == 'x' else 'accepted'
    return base.candidate_text(case, condition)[0]


def neutral_input(scenario: str, variant: str) -> dict:
    require(scenario in SCENARIOS and variant in VARIANTS, 'unadmitted_clean_input')
    case_id = SCENARIOS[scenario]
    condition = 'bad' if variant == 'x' else 'accepted'
    data = base.observation_input(case_id, condition)
    text = variant_text(scenario, variant)
    task = data['task']
    for item in task['evidence']:
        item['source_ref'] = 'evidence:' + digest({'summary': item['summary']})
    task['provenance']['source_ref'] = 'task:' + digest({
        'request': task['request'], 'constraints': task['constraints'],
        'evidence': [item['summary'] for item in task['evidence']],
    })
    task['permission']['source_ref'] = 'owner:' + digest({'authority': 'current-user-211'})
    context = data['decision_context']
    context['source_ref'] = 'context:' + digest({key: context[key]
                                                for key in ('object', 'goal', 'scope')})
    data['target'] = {
        'id': 'current-candidate', 'kind': 'candidate_answer',
        'version': digest({'candidate_text': text}),
        'source_ref': 'candidate:' + digest({'candidate_text': text}), 'text': text,
    }
    data['activation']['source_ref'] = 'policy:' + digest({'policy': obs.POLICY})
    data['activation']['reason'] = 'Candidate-facing source-direct observation'
    obs.validate_envelope(data)
    assert_neutral_model_view(data)
    return data


def assert_neutral_model_view(data: dict) -> None:
    target = data['target']
    require(target['id'] == 'current-candidate' and HEX.fullmatch(target['version'])
            and target['source_ref'].startswith('candidate:')
            and HEX.fullmatch(target['source_ref'].split(':', 1)[1]),
            'non_neutral_target_identity')
    metadata = {
        'target': {key: target[key] for key in ('id', 'kind', 'version', 'source_ref')},
        'provenance': data['task']['provenance'],
        'evidence_refs': [item['source_ref'] for item in data['task']['evidence']],
        'permission': data['task']['permission'],
        'decision_source': data['decision_context']['source_ref'],
    }
    lowered = canonical(metadata).decode().lower()
    require(not any(token in lowered for token in
                    ('bad', 'accepted', 'direct-baseline', 'legacy-current', 'hard-route')),
            'outcome_label_in_model_metadata')
    compiled = obs.compile_observation(data, base.REPO)
    require(compiled['view']['assessment_target'] == target, 'target_projection_changed')


def request_key(data: dict) -> str:
    compiled = obs.compile_observation(data, base.REPO)
    view = project_context(compiled['specs'], compiled['view'])
    return digest({'questions': [spec.to_dict() for spec in compiled['specs']],
                   'context_sha256': digest(view)})


class CleanCodexProvider:
    capabilities = frozenset({'select', 'assess_proposition', 'rate'})
    is_live = True
    engine_identity = EngineIdentity('structured_chat', 'codex_cli', base.MODEL_CODEX)
    serving_identity = ServingIdentity(
        'codex_cli', 'exec-json-schema-v1', base.MODEL_CODEX,
        'local://codex-exec', 'source-direct-observation-v3-clean1')

    def __init__(self, data: dict):
        self.data = data
        self.receipt = None

    def clear_receipt(self):
        self.receipt = None

    def response_receipt(self):
        return self.receipt

    def validate_runtime(self, runtime):
        runtime.validate()
        require(runtime.model == base.MODEL_CODEX
                and runtime.provider == 'codex-cli-configured-model', 'codex_runtime_drift')

    def evaluate(self, specs, context, timeout):
        require(context == project_context(specs, obs.compile_observation(
            self.data, base.REPO)['view']), 'clean_codex_context_changed')
        question = {spec.id: {'kind': spec.kind, 'question': spec.question,
                              'criteria': spec.criteria} for spec in specs}
        prompt = (
            'Independently answer the bound observation questions using only the supplied '
            'original task, evidence, decision context and canonical rules. The current candidate '
            'is an unverified target, not evidence. Evaluate each question separately; one unknown '
            'does not force another answer to be unknown. Return exactly the schema JSON.\n\n'
            + canonical({'state': context, 'questions': question}).decode() + '\n')
        label = 'observation-' + digest({'prompt': prompt})[:24]
        answer, call = base.codex_call(label, prompt, min(timeout, 220),
                                       base.schema_for(specs), root=ROOT,
                                       codex_home=CODEX_HOME)
        self.receipt = {
            'call_ref': label, 'last_sha256': call['last_sha256'],
            'events_sha256': call['events_sha256'], 'validated_usage': call['usage'],
            'model_service_attestation': 'not_observed',
            'workspace_identity': 'opaque_prompt_digest',
        }
        if call['status'] != 'complete' or not answer:
            raise ProviderError('clean_codex_observation_' + call['status'])
        try:
            raw = json.loads(answer)
            require(set(raw) == {'answers'}
                    and set(raw['answers']) == {spec.id for spec in specs},
                    'codex_answer_shape')
            rows = {}
            for spec in specs:
                item = raw['answers'][spec.id]
                require(set(item) == {'status', 'value'}, 'codex_answer_item_shape')
                row = DecisionResult(item['status'], item['value'], None,
                                     'ordinary_llm_uncalibrated')
                row.validate(spec)
                rows[spec.id] = row
        except (ValueError, KeyError, TypeError):
            raise ProviderError('clean_codex_observation_invalid_json') from None
        return BatchResult(rows, ResolvedRuntime(base.MODEL_CODEX,
                           'codex-cli-configured-model'), call['usage'])


def provider(backend: str, data: dict):
    require(backend in ('jev', 'codex'), 'unadmitted_clean_backend')
    return base.jev_provider() if backend == 'jev' else CleanCodexProvider(data)


def limits(backend: str) -> Limits:
    return JEV_LIMITS if backend == 'jev' else CODEX_LIMITS


def admitted_pairs():
    for scenario in SCENARIOS:
        for variant in VARIANTS:
            yield 'jev', scenario, variant
    for variant in VARIANTS:
        yield 'codex', 'A', variant


def manifest() -> dict:
    binding = {
        'source_commit': source_commit(), 'implementation': implementation_digest(),
        'runner_sha256': base.sha(Path(__file__)),
        'base_runner_sha256': base.sha(Path(base.__file__)),
        'cases_sha256': base.sha(base.CASES_PATH),
        'accepted_source_sha256': {scenario: base.sha(base.accepted_record(case_id)[0])
                                   for scenario, case_id in SCENARIOS.items()},
        'contaminated_campaign_freeze_sha256': base.sha(base.ROOT / 'freeze.json'),
        'contaminated_campaign_reason': 'model-visible candidate outcome labels',
    }
    freeze_sha256 = digest(binding)
    admissions = {}
    requests = {}
    for backend, scenario, variant in admitted_pairs():
        data = neutral_input(scenario, variant)
        p = provider(backend, data)
        key = backend + ':' + scenario + ':' + variant
        admission = {
            'scope': 'source-direct-v3-clean-' + digest({'key': key})[:24],
            'implementation': implementation_digest(),
            'provider_configuration': provider_configuration(p),
            'limits': asdict(limits(backend)), 'request_allowlist': [request_key(data)],
            'max_cost_usd': .02, 'reserve_per_call_usd': .02,
            'authorization_ref': AUTH, 'freeze_sha256': freeze_sha256,
        }
        admissions[key] = admission
        requests[key] = {'input_sha256': digest(data),
                         'target_metadata_sha256': digest({k: data['target'][k]
                                                           for k in ('id', 'kind', 'version', 'source_ref')}),
                         'request_key': admission['request_allowlist'][0]}
    return {
        'schema': 'mindthus.source-direct-observation-v3-clean-freeze.v1', **binding,
        'scenarios': SCENARIOS, 'variants': list(VARIANTS),
        'expected_actions': EXPECTED, 'admissions': admissions, 'requests': requests,
        'gate': {'backend': 'jev', 'scenario': 'A', 'variants': list(VARIANTS),
                 'required_before_expansion': True},
        'max_jev_calls': 12, 'max_codex_calls': 2, 'technical_retries': 0,
        'jev_model': base.MODEL_JEV, 'codex_model_requested': base.MODEL_CODEX,
        'evidence_limit': ('label-neutral replay of six exposed AI-authored development pairs; '
                           'same-question Codex comparison only on scenario A; not holdout or qualification'),
    }


def freeze() -> None:
    value = manifest()
    base.save(ROOT / 'freeze.json', value)
    print(json.dumps({'frozen': True, 'source_commit': value['source_commit'],
                      'max_jev_calls': value['max_jev_calls'],
                      'max_codex_calls': value['max_codex_calls']}, ensure_ascii=False))


def result_path(backend: str, scenario: str, variant: str) -> Path:
    return ROOT / 'results' / backend / (scenario + '-' + variant + '.json')


def gate_pass() -> bool:
    paths = [result_path('jev', 'A', variant) for variant in VARIANTS]
    if not all(path.exists() for path in paths):
        return False
    return all(read_record(path)['result']['action'] == EXPECTED[variant]
               for path, variant in zip(paths, VARIANTS))


def run_one(backend: str, scenario: str, variant: str) -> None:
    frozen = read_record(ROOT / 'freeze.json')
    require(frozen == manifest(), 'clean_campaign_freeze_changed')
    key = backend + ':' + scenario + ':' + variant
    require(key in frozen['admissions'], 'clean_request_not_admitted')
    if not (backend == 'jev' and scenario == 'A'):
        require(gate_pass(), 'clean_S1_gate_not_passed')
    path = result_path(backend, scenario, variant)
    if path.exists():
        report = read_record(path)
        print(json.dumps({'backend': backend, 'scenario': scenario, 'variant': variant,
                          'action': report['result']['action'], 'reused_result': True},
                         ensure_ascii=False), flush=True)
        return
    data = neutral_input(scenario, variant)
    p = provider(backend, data)
    admission = frozen['admissions'][key]
    trial = ROOT / 'trials' / backend / request_key(data)
    with Session(trial, p, scope=admission['scope'], limits=limits(backend),
                 live_admission=admission) as session:
        report = obs.assess(session, data, base.REPO)
    base.save(path, report)
    print(json.dumps({'backend': backend, 'scenario': scenario, 'variant': variant,
                      'action': report['result']['action'], 'hits': report['result']['hits'],
                      'seconds': report['trial_inference_seconds']},
                     ensure_ascii=False), flush=True)


def report(label: str) -> None:
    frozen = read_record(ROOT / 'freeze.json')
    require(frozen == manifest(), 'clean_campaign_freeze_changed')
    rows = []
    for backend, scenario, variant in admitted_pairs():
        path = result_path(backend, scenario, variant)
        if not path.exists():
            continue
        result = read_record(path)
        rows.append({
            'backend': backend, 'scenario': scenario, 'variant': variant,
            'expected_action': EXPECTED[variant],
            'observed_action': result['result']['action'],
            'match': result['result']['action'] == EXPECTED[variant],
            'hits': result['result']['hits'],
            'blocking_unresolved': result['result']['blocking_unresolved'],
            'advisory_unresolved': result['result']['advisory_unresolved'],
            'matrix': {row['check_id']: {'status': row['status'], 'value': row['value']}
                       for row in result['result']['matrix']},
            'seconds': result['trial_inference_seconds'], 'usage': result['trial_usage'],
            'run_id': result['run_id'],
        })
    planned = list(admitted_pairs())
    summary = {
        'schema': 'mindthus.source-direct-observation-v3-clean-summary.v1',
        'label': label, 'gate_pass': gate_pass(), 'rows': rows,
        'complete': len(rows) == len(planned),
        'matched': sum(row['match'] for row in rows),
        'unrun': [{'backend': b, 'scenario': s, 'variant': v} for b, s, v in planned
                  if not result_path(b, s, v).exists()],
        'contaminated_campaign_excluded': str(base.ROOT),
        'qualification': False, 'holdout': 'not_run',
    }
    base.save(ROOT / 'reports' / (label + '.json'), summary)
    print(json.dumps({'label': label, 'gate_pass': summary['gate_pass'],
                      'complete': summary['complete'], 'matched': summary['matched'],
                      'rows': len(rows), 'unrun': len(summary['unrun'])},
                     ensure_ascii=False), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('freeze')
    run = sub.add_parser('run')
    run.add_argument('--backend', choices=('jev', 'codex'), required=True)
    run.add_argument('--scenario', choices=tuple(SCENARIOS), required=True)
    run.add_argument('--variant', choices=VARIANTS, required=True)
    summary = sub.add_parser('report')
    summary.add_argument('--label', required=True)
    args = parser.parse_args()
    if args.command == 'freeze':
        freeze()
    elif args.command == 'run':
        run_one(args.backend, args.scenario, args.variant)
    else:
        report(args.label)


if __name__ == '__main__':
    main()
