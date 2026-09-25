"""Exposed D diagnostic for the source-direct observation v3 contract.

Each case is one immutable bad -> accepted candidate pair.  TypeSafe Jev and the
current local Codex answer the same four questions.  This is development evidence,
not a holdout or #211 qualification run.  No CPA or OpenRouter path exists here.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))

from experiments.typed_decision import observation_assessment as obs
from experiments.typed_decision.contracts import (
    BatchResult, ContractError, DecisionResult, EngineIdentity, ResolvedRuntime,
    ServingIdentity, canonical, digest, project_context, provider_configuration, require,
)
from experiments.typed_decision.providers import ProviderError, TypeSafeJevProvider
from experiments.typed_decision.relationship_live import deadline_post_json
from experiments.typed_decision.session import (
    Limits, RecoveryRequired, Session, implementation_digest, read_record, write_once,
)

ROOT = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-source-direct-v3-d')
CASES_PATH = REPO / 'docs/internal/research/typed-decision/route-control-v0.2/hard-route-v1/cases.json'
ACCEPTED_ROOT = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-hard-route-v1/direct-baseline/results')
CASE_IDS = ('S1', 'S2', 'S3', 'K1', 'K2', 'K3')
CANDIDATES = ('bad', 'accepted')
BACKENDS = ('jev', 'codex')
MODEL_JEV = 'jev-1.13.0'
MODEL_CODEX = 'gpt-6-sol'
CODEX = Path('/Applications/ChatGPT.app/Contents/Resources/codex')
CODEX_HOME = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-hard-route-v1/codex-home')
LIMITS = Limits(max_calls=1, max_seconds=60, max_request_bytes=98304)
AUTH = ('User authorized minimum implementation, validation, and expansion after an effective '
        'S1 gate for issue #211 on 2026-09-25; TypeSafe Jev and current local Codex only.')


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path: Path, value: dict) -> None:
    path = Path(path)
    if path.exists():
        require(read_record(path) == value, 'immutable_observation_record_changed')
    else:
        write_once(path, value)


def save_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_text(encoding='utf8') == value, 'immutable_plain_record_changed')
    else:
        path.write_text(value, encoding='utf8')


def source_commit() -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()


def cases() -> dict:
    raw = json.loads(CASES_PATH.read_bytes())
    require(raw.get('schema') == 'mindthus.hard-route-cases-v1', 'case_schema_changed')
    found = {item['id']: item for item in raw['cases']}
    require(tuple(found) == CASE_IDS, 'case_population_changed')
    return found


def accepted_record(case_id: str) -> tuple[Path, dict]:
    path = ACCEPTED_ROOT / (case_id + '.json')
    record = read_record(path)
    require(record['case'] == case_id and record['verdict'] == 'revise'
            and isinstance(record['final_answer'], str) and record['final_answer'].strip(),
            'accepted_candidate_source_changed')
    return path, record


def candidate_text(case: dict, kind: str) -> tuple[str, str, str]:
    if kind == 'bad':
        document = next(d for d in case['packet']['documents'] if d['id'] == 'C')
        return document['text'], document['revision'], (
            'repo:' + str(CASES_PATH.relative_to(REPO)) + '#' + case['id'] + ':C')
    path, record = accepted_record(case['id'])
    return record['final_answer'], '2', (
        'legacy-current-codex:' + str(path) + '#payload.final_answer;record_sha256=' + sha(path))


def observation_input(case_id: str, kind: str) -> dict:
    require(case_id in CASE_IDS and kind in CANDIDATES, 'unadmitted_observation_input')
    case = cases()[case_id]
    docs = case['packet']['documents']
    users = [d for d in docs if d['kind'] == 'user']
    sources = [d for d in docs if d['kind'] == 'source']
    require(users and sources, 'source_direct_material_missing')
    frame = case['packet']['proposal']['frames'][0]
    text, version, source_ref = candidate_text(case, kind)
    data = {
        'state_version': 'source-direct-v3-d1',
        'task': {
            'request': '\n\n'.join(d['text'] for d in users),
            'constraints': [frame['scope']['text'], '只依据提供的用户消息和来源材料判断。'],
            'evidence': [{'source_ref': 'case:' + case_id + ':' + d['id'],
                          'summary': d['text']} for d in sources],
            'provenance': {'source_ref': 'repo:' + str(CASES_PATH.relative_to(REPO))
                           + '#' + case_id, 'revision': '1'},
            'known_obligations': [], 'explicit_method': None, 'risk': 'low',
            'freshness': 'current',
            'permission': {'mode': 'advisory', 'source_ref': 'current-user:#211'},
        },
        'decision_context': {
            'object': frame['object']['text'], 'goal': frame['goal']['text'],
            'scope': frame['scope']['text'],
            'source_ref': 'repo:' + str(CASES_PATH.relative_to(REPO)) + '#' + case_id + ':F0',
        },
        'target': {'id': case_id + '-' + kind, 'kind': 'candidate_answer',
                   'version': version, 'source_ref': source_ref, 'text': text},
        'activation': {
            'event': 'before-answer',
            'source_ref': 'repo:design-reassessment-v1/TEST-PLAN.md#D',
            'reason': 'Exposed bad-to-accepted source-direct D diagnostic',
            'frame_risk': True, 'execution_impact': True, 'required': False,
            'checks': list(obs.CHECKS),
        },
    }
    obs.validate_envelope(data)
    return data


def jev_provider():
    return TypeSafeJevProvider(model=MODEL_JEV, choice_rounding=True,
                               transport=deadline_post_json)


def schema_for(specs) -> dict:
    answers = {}
    for spec in specs:
        value = {'type': 'string', 'enum': sorted(spec.criteria)}
        answers[spec.id] = {
            'type': 'object', 'additionalProperties': False,
            'properties': {
                'status': {'type': 'string', 'enum': ['ok', 'abstain', 'missing_context']},
                'value': {'anyOf': [value, {'type': 'null'}]},
            },
            'required': ['status', 'value'],
        }
    return {
        'type': 'object', 'additionalProperties': False,
        'properties': {'answers': {
            'type': 'object', 'additionalProperties': False,
            'properties': answers, 'required': sorted(answers),
        }},
        'required': ['answers'],
    }


def codex_call(label: str, prompt: str, timeout: float, schema: dict, *,
               root: Path = ROOT, codex_home: Path = CODEX_HOME) -> tuple[str | None, dict]:
    directory = root / 'codex-calls' / label
    workspace = root / 'workspaces' / label
    directory.mkdir(parents=True, exist_ok=True)
    workspace.mkdir(parents=True, exist_ok=True)
    schema_path = root / 'schemas' / (label + '.json')
    schema_text = json.dumps(schema, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    save_text(schema_path, schema_text)
    intent = {
        'label': label, 'model': MODEL_CODEX,
        'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
        'schema_sha256': hashlib.sha256(schema_text.encode()).hexdigest(),
        'timeout_seconds': timeout, 'codex_home': str(codex_home),
        'workspace': str(workspace), 'sandbox': 'read-only', 'ephemeral': True,
        'no_user_config': True,
    }
    intent_path, outcome_path = directory / 'intent.json', directory / 'outcome.json'
    if outcome_path.exists():
        require(intent_path.exists() and read_record(intent_path) == intent,
                'codex_observation_identity_changed')
        outcome = read_record(outcome_path)
        last = directory / 'last-message.txt'
        return (last.read_text(encoding='utf8') if last.exists() else None), outcome
    if intent_path.exists():
        raise RecoveryRequired('unresolved prior Codex observation:' + label)
    require(CODEX.is_file() and (codex_home / 'auth.json').is_file(), 'codex_profile_unavailable')
    save(intent_path, intent)
    command = [str(CODEX), 'exec', '--ignore-user-config', '--ephemeral',
               '--skip-git-repo-check', '--sandbox', 'read-only', '-m', MODEL_CODEX,
               '-C', str(workspace), '--json', '-o', str(directory / 'last-message.txt'),
               '--output-schema', str(schema_path), '-']
    env = os.environ.copy()
    env['CODEX_HOME'] = str(codex_home)
    for key in ('TYPESAFE_API_KEY', 'MINDTHUS_HOST_API_KEY', 'OPENROUTER_API_KEY'):
        env.pop(key, None)
    start = time.monotonic()
    try:
        completed = subprocess.run(command, input=prompt, text=True, capture_output=True,
                                   timeout=timeout, cwd=workspace, env=env, check=False)
        stdout, stderr, code = completed.stdout, completed.stderr, completed.returncode
        status = ('complete' if code == 0 and (directory / 'last-message.txt').is_file()
                  else 'failed')
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout.decode('utf8', 'replace') if isinstance(exc.stdout, bytes)
                  else (exc.stdout or ''))
        stderr = (exc.stderr.decode('utf8', 'replace') if isinstance(exc.stderr, bytes)
                  else (exc.stderr or ''))
        status, code = 'timeout_terminal', None
    save_text(directory / 'events.jsonl', stdout)
    usage = {'input_tokens': None, 'output_tokens': None, 'cost_usd': None}
    for line in stdout.splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        row = item.get('usage') if isinstance(item, dict) else None
        if isinstance(row, dict):
            for key in ('input_tokens', 'output_tokens'):
                if type(row.get(key)) is int and row[key] >= 0:
                    usage[key] = row[key]
    outcome = {
        'status': status, 'exit_code': code, 'elapsed_seconds': time.monotonic() - start,
        'events_sha256': sha(directory / 'events.jsonl'),
        'stderr_sha256': hashlib.sha256(stderr.encode()).hexdigest(),
        'last_sha256': (sha(directory / 'last-message.txt')
                        if (directory / 'last-message.txt').is_file() else None),
        'usage': usage, 'model_requested': MODEL_CODEX,
        'model_service_attestation': 'not_observed',
    }
    save(outcome_path, outcome)
    last = directory / 'last-message.txt'
    return (last.read_text(encoding='utf8') if last.exists() else None), outcome


class CodexProvider:
    capabilities = frozenset({'select', 'assess_proposition', 'rate'})
    is_live = True
    engine_identity = EngineIdentity('structured_chat', 'codex_cli', MODEL_CODEX)
    serving_identity = ServingIdentity('codex_cli', 'exec-json-schema-v1', MODEL_CODEX,
                                       'local://codex-exec', 'source-direct-observation-v3')

    def __init__(self, case_id: str, candidate: str):
        self.case_id, self.candidate = case_id, candidate
        self.receipt = None

    def clear_receipt(self):
        self.receipt = None

    def response_receipt(self):
        return self.receipt

    def validate_runtime(self, runtime):
        runtime.validate()
        require(runtime.model == MODEL_CODEX
                and runtime.provider == 'codex-cli-configured-model', 'codex_runtime_drift')

    def evaluate(self, specs, context, timeout):
        question = {s.id: {'kind': s.kind, 'question': s.question,
                           'criteria': s.criteria} for s in specs}
        prompt = (
            'Independently answer the bound observation questions using only the supplied '
            'original task, evidence, decision context and canonical rules. The current candidate '
            'is an unverified target, not evidence. Evaluate each question separately; one unknown '
            'does not force another answer to be unknown. Return exactly the schema JSON.\n\n'
            + canonical({'state': context, 'questions': question}).decode() + '\n')
        label = self.case_id + '-' + self.candidate + '-codex-observation-v3'
        answer, call = codex_call(label, prompt, min(timeout, 55), schema_for(specs))
        self.receipt = {
            'call_label': label, 'last_sha256': call['last_sha256'],
            'events_sha256': call['events_sha256'], 'validated_usage': call['usage'],
            'model_service_attestation': 'not_observed',
        }
        if call['status'] != 'complete' or not answer:
            raise ProviderError('codex_observation_' + call['status'])
        try:
            raw = json.loads(answer)
            require(set(raw) == {'answers'}
                    and set(raw['answers']) == {s.id for s in specs}, 'codex_answer_shape')
            rows = {}
            for spec in specs:
                item = raw['answers'][spec.id]
                require(set(item) == {'status', 'value'}, 'codex_answer_item_shape')
                row = DecisionResult(item['status'], item['value'], None,
                                     'ordinary_llm_uncalibrated')
                row.validate(spec)
                rows[spec.id] = row
        except (ValueError, KeyError, TypeError):
            raise ProviderError('codex_observation_invalid_json') from None
        return BatchResult(rows, ResolvedRuntime(MODEL_CODEX,
                           'codex-cli-configured-model'), call['usage'])


def provider(backend: str, case_id: str, candidate: str):
    require(backend in BACKENDS, 'unadmitted_backend')
    return jev_provider() if backend == 'jev' else CodexProvider(case_id, candidate)


def request_key(data: dict) -> str:
    compiled = obs.compile_observation(data, REPO)
    view = project_context(compiled['specs'], compiled['view'])
    return digest({'questions': [spec.to_dict() for spec in compiled['specs']],
                   'context_sha256': digest(view)})


def manifest() -> dict:
    require(obs.VERSION == '3' and obs.POLICY == 'mindthus.source-direct-observation.v3',
            'observation_contract_changed')
    binding = {
        'source_commit': source_commit(), 'implementation': implementation_digest(),
        'runner_sha256': sha(Path(__file__)), 'cases_sha256': sha(CASES_PATH),
        'accepted_source_sha256': {case_id: sha(accepted_record(case_id)[0])
                                   for case_id in CASE_IDS},
    }
    freeze_sha256 = digest(binding)
    admissions = {}
    for backend in BACKENDS:
        admissions[backend] = {}
        for case_id in CASE_IDS:
            admissions[backend][case_id] = {}
            for candidate in CANDIDATES:
                p = provider(backend, case_id, candidate)
                scope = 'source-direct-v3-d1-' + backend + '-' + case_id + '-' + candidate
                admissions[backend][case_id][candidate] = {
                    'scope': scope, 'implementation': implementation_digest(),
                    'provider_configuration': provider_configuration(p),
                    'limits': asdict(LIMITS),
                    'request_allowlist': [request_key(observation_input(case_id, candidate))],
                    'max_cost_usd': .02, 'reserve_per_call_usd': .02,
                    'authorization_ref': AUTH, 'freeze_sha256': freeze_sha256,
                }
    return {
        'schema': 'mindthus.source-direct-observation-v3-d-freeze.v1', **binding,
        'contract': {'version': obs.VERSION, 'policy': obs.POLICY,
                     'checks': list(obs.CHECKS), 'unknown_policy': obs.UNKNOWN_POLICY},
        'case_ids': list(CASE_IDS), 'candidates': list(CANDIDATES),
        'backends': list(BACKENDS), 'admissions': admissions,
        'gate': {'backend': 'jev', 'case': 'S1',
                 'expected': {'bad': 'request_correction', 'accepted': 'continue_original'}},
        'expansion_condition': 'S1 Jev bad/accepted pair both match expected actions',
        'max_jev_calls': 12, 'max_codex_observation_calls': 12,
        'technical_retries': 0, 'reserve_usd_per_call': .02,
        'evidence_limit': ('six exposed AI-authored development cases and reused current-Codex '
                           'accepted answers; diagnostic only, not holdout or qualification'),
    }


def freeze() -> None:
    value = manifest()
    save(ROOT / 'freeze.json', value)
    print(json.dumps({'frozen': True, 'source_commit': value['source_commit'],
                      'implementation': value['implementation'],
                      'max_jev_calls': value['max_jev_calls'],
                      'max_codex_observation_calls': value['max_codex_observation_calls']},
                     ensure_ascii=False))


def run_one(backend: str, case_id: str, candidate: str) -> None:
    frozen = read_record(ROOT / 'freeze.json')
    require(frozen == manifest(), 'frozen_observation_campaign_changed')
    result_path = ROOT / 'results' / backend / (case_id + '-' + candidate + '.json')
    if result_path.exists():
        existing = read_record(result_path)
        print(json.dumps({'backend': backend, 'case': case_id, 'candidate': candidate,
                          'action': existing['result']['action'], 'reused_result': True},
                         ensure_ascii=False), flush=True)
        return
    data = observation_input(case_id, candidate)
    p = provider(backend, case_id, candidate)
    admission = frozen['admissions'][backend][case_id][candidate]
    root = ROOT / 'trials' / backend / case_id / candidate
    with Session(root, p, scope=admission['scope'], limits=LIMITS,
                 live_admission=admission) as session:
        report = obs.assess(session, data, REPO)
    save(result_path, report)
    print(json.dumps({'backend': backend, 'case': case_id, 'candidate': candidate,
                      'action': report['result']['action'], 'hits': report['result']['hits'],
                      'blocking': report['result']['blocking_unresolved'],
                      'advisory': report['result']['advisory_unresolved'],
                      'new_calls': report['invocation']['new_calls'],
                      'seconds': report['trial_inference_seconds']},
                     ensure_ascii=False), flush=True)


def summarize(label: str) -> None:
    frozen = read_record(ROOT / 'freeze.json')
    require(frozen == manifest(), 'frozen_observation_campaign_changed')
    rows = []
    for backend in BACKENDS:
        for case_id in CASE_IDS:
            for candidate in CANDIDATES:
                path = ROOT / 'results' / backend / (case_id + '-' + candidate + '.json')
                if not path.exists():
                    continue
                report = read_record(path)
                expected = 'request_correction' if candidate == 'bad' else 'continue_original'
                matrix = {row['check_id']: {'status': row['status'], 'value': row['value'],
                                             'effect': row['effect']}
                          for row in report['result']['matrix']}
                rows.append({'backend': backend, 'case': case_id, 'candidate': candidate,
                             'expected_action': expected,
                             'observed_action': report['result']['action'],
                             'match': report['result']['action'] == expected,
                             'hits': report['result']['hits'],
                             'blocking_unresolved': report['result']['blocking_unresolved'],
                             'advisory_unresolved': report['result']['advisory_unresolved'],
                             'matrix': matrix, 'usage': report['trial_usage'],
                             'inference_seconds': report['trial_inference_seconds'],
                             'run_id': report['run_id'], 'source_ref': report['source_ref']})
    gate = [r for r in rows if r['backend'] == 'jev' and r['case'] == 'S1']
    gate_pass = len(gate) == 2 and all(row['match'] for row in gate)
    totals = {}
    for backend in BACKENDS:
        selected = [r for r in rows if r['backend'] == backend]
        totals[backend] = {'completed': len(selected),
                           'matched': sum(r['match'] for r in selected),
                           'failed': len(selected) - sum(r['match'] for r in selected),
                           'seconds': sum(r['inference_seconds'] for r in selected)}
    summary = {
        'schema': 'mindthus.source-direct-observation-v3-d-summary.v1',
        'label': label, 'source_commit': frozen['source_commit'],
        'gate_pass': gate_pass, 'rows': rows, 'totals': totals,
        'complete': len(rows) == len(BACKENDS) * len(CASE_IDS) * len(CANDIDATES),
        'unrun': [{'backend': backend, 'case': case_id, 'candidate': candidate}
                  for backend in BACKENDS for case_id in CASE_IDS for candidate in CANDIDATES
                  if not any(r['backend'] == backend and r['case'] == case_id
                             and r['candidate'] == candidate for r in rows)],
        'qualification': False, 'holdout': 'not_run',
        'cost_policy': 'owner provisional zero; provider cost fields retained as observed/unknown',
    }
    save(ROOT / 'reports' / (label + '.json'), summary)
    print(json.dumps({'label': label, 'gate_pass': gate_pass,
                      'complete': summary['complete'], 'totals': totals,
                      'unrun': len(summary['unrun'])}, ensure_ascii=False), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('freeze')
    run = sub.add_parser('run')
    run.add_argument('--backend', choices=BACKENDS, required=True)
    run.add_argument('--case', choices=CASE_IDS, required=True)
    run.add_argument('--candidate', choices=CANDIDATES, required=True)
    report = sub.add_parser('report')
    report.add_argument('--label', required=True)
    args = parser.parse_args()
    if args.command == 'freeze':
        freeze()
    elif args.command == 'run':
        run_one(args.backend, args.case, args.candidate)
    else:
        summarize(args.label)


if __name__ == '__main__':
    main()
