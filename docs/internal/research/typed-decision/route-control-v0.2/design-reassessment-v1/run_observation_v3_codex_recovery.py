"""Two-call technical recovery for the timed-out S1 Codex observation pair.

The original twelve 55-second failures remain immutable.  This preregistered
supplement repeats only the S1 bad/accepted requests with a longer local CLI deadline,
using the two Codex technical supplement slots allowed by TEST-PLAN.md.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
import time

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

ROOT = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-source-direct-v3-d/codex-recovery-v1')
ORIGINAL = base.ROOT
CASE_ID = 'S1'
CANDIDATES = ('bad', 'accepted')
LIMITS = Limits(max_calls=1, max_seconds=240, max_request_bytes=98304)
AUTH = ('User authorized timeout recovery comparison for issue #211; TEST-PLAN D permits '
        'at most two Codex technical supplement requests. Current local Codex only.')


class RecoveryCodexProvider(base.CodexProvider):
    engine_identity = EngineIdentity('structured_chat', 'codex_cli', base.MODEL_CODEX)
    serving_identity = ServingIdentity(
        'codex_cli', 'exec-json-schema-v1', base.MODEL_CODEX,
        'local://codex-exec', 'source-direct-observation-v3-recovery1')

    def evaluate(self, specs, context, timeout):
        question = {s.id: {'kind': s.kind, 'question': s.question,
                           'criteria': s.criteria} for s in specs}
        prompt = (
            'Independently answer the bound observation questions using only the supplied '
            'original task, evidence, decision context and canonical rules. The current candidate '
            'is an unverified target, not evidence. Evaluate each question separately; one unknown '
            'does not force another answer to be unknown. Return exactly the schema JSON.\n\n'
            + canonical({'state': context, 'questions': question}).decode() + '\n')
        label = self.case_id + '-' + self.candidate + '-codex-observation-v3-recovery-v1'
        answer, call = base.codex_call(label, prompt, min(timeout, 220),
                                       base.schema_for(specs), root=ROOT)
        self.receipt = {
            'call_label': label, 'last_sha256': call['last_sha256'],
            'events_sha256': call['events_sha256'], 'validated_usage': call['usage'],
            'model_service_attestation': 'not_observed',
            'original_timeout_result_ref': str(
                ORIGINAL / 'results/codex' / (self.case_id + '-' + self.candidate + '.json')),
        }
        if call['status'] != 'complete' or not answer:
            raise ProviderError('codex_observation_recovery_' + call['status'])
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
            raise ProviderError('codex_observation_recovery_invalid_json') from None
        return BatchResult(rows, ResolvedRuntime(base.MODEL_CODEX,
                           'codex-cli-configured-model'), call['usage'])


def original_failure(candidate: str) -> dict:
    result_path = ORIGINAL / 'results/codex' / (CASE_ID + '-' + candidate + '.json')
    call_path = ORIGINAL / 'codex-calls' / (
        CASE_ID + '-' + candidate + '-codex-observation-v3') / 'outcome.json'
    result, call = read_record(result_path), read_record(call_path)
    require(result['result']['action'] == 'return_original_owner'
            and all(row['status'] == 'provider_error' for row in result['result']['matrix'])
            and call['status'] == 'timeout_terminal' and call['last_sha256'] is None,
            'original_failure_is_not_recoverable_timeout')
    return {'result_path': str(result_path), 'result_sha256': base.sha(result_path),
            'call_path': str(call_path), 'call_sha256': base.sha(call_path),
            'elapsed_seconds': call['elapsed_seconds']}


def source_commit() -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=base.REPO, text=True).strip()


def request_key(candidate: str) -> str:
    compiled = obs.compile_observation(base.observation_input(CASE_ID, candidate), base.REPO)
    view = project_context(compiled['specs'], compiled['view'])
    return digest({'questions': [spec.to_dict() for spec in compiled['specs']],
                   'context_sha256': digest(view)})


def manifest() -> dict:
    binding = {
        'source_commit': source_commit(), 'implementation': implementation_digest(),
        'runner_sha256': base.sha(Path(__file__)),
        'base_runner_sha256': base.sha(Path(base.__file__)),
        'original_freeze_sha256': base.sha(ORIGINAL / 'freeze.json'),
        'original_failures': {candidate: original_failure(candidate)
                              for candidate in CANDIDATES},
    }
    freeze_sha256 = digest(binding)
    admissions = {}
    for candidate in CANDIDATES:
        p = RecoveryCodexProvider(CASE_ID, candidate)
        admissions[candidate] = {
            'scope': 'source-direct-v3-d1-codex-recovery1-S1-' + candidate,
            'implementation': implementation_digest(),
            'provider_configuration': provider_configuration(p),
            'limits': asdict(LIMITS), 'request_allowlist': [request_key(candidate)],
            'max_cost_usd': .02, 'reserve_per_call_usd': .02,
            'authorization_ref': AUTH, 'freeze_sha256': freeze_sha256,
        }
    return {
        'schema': 'mindthus.source-direct-observation-v3-codex-recovery-freeze.v1',
        **binding, 'case_id': CASE_ID, 'candidates': list(CANDIDATES),
        'admissions': admissions, 'max_codex_calls': 2, 'retries_per_request': 1,
        'timeout_seconds': 220,
        'purpose': 'technical timeout recovery only; diagnostic, not qualification',
    }


def freeze() -> None:
    value = manifest()
    base.save(ROOT / 'freeze.json', value)
    print(json.dumps({'frozen': True, 'source_commit': value['source_commit'],
                      'max_codex_calls': value['max_codex_calls'],
                      'timeout_seconds': value['timeout_seconds']}, ensure_ascii=False))


def run_one(candidate: str) -> None:
    frozen = read_record(ROOT / 'freeze.json')
    require(frozen == manifest(), 'codex_recovery_freeze_changed')
    result_path = ROOT / 'results' / (CASE_ID + '-' + candidate + '.json')
    if result_path.exists():
        result = read_record(result_path)
        print(json.dumps({'candidate': candidate, 'action': result['result']['action'],
                          'reused_result': True}, ensure_ascii=False), flush=True)
        return
    data = base.observation_input(CASE_ID, candidate)
    p = RecoveryCodexProvider(CASE_ID, candidate)
    admission = frozen['admissions'][candidate]
    with Session(ROOT / 'trials' / candidate, p, scope=admission['scope'], limits=LIMITS,
                 live_admission=admission) as session:
        report = obs.assess(session, data, base.REPO)
    base.save(result_path, report)
    print(json.dumps({'candidate': candidate, 'action': report['result']['action'],
                      'hits': report['result']['hits'],
                      'seconds': report['trial_inference_seconds']}, ensure_ascii=False), flush=True)


def report() -> None:
    frozen = read_record(ROOT / 'freeze.json')
    require(frozen == manifest(), 'codex_recovery_freeze_changed')
    rows = []
    for candidate in CANDIDATES:
        result = read_record(ROOT / 'results' / (CASE_ID + '-' + candidate + '.json'))
        expected = 'request_correction' if candidate == 'bad' else 'continue_original'
        rows.append({'candidate': candidate, 'expected_action': expected,
                     'observed_action': result['result']['action'],
                     'match': result['result']['action'] == expected,
                     'hits': result['result']['hits'],
                     'blocking_unresolved': result['result']['blocking_unresolved'],
                     'advisory_unresolved': result['result']['advisory_unresolved'],
                     'matrix': {row['check_id']: {'status': row['status'], 'value': row['value']}
                                for row in result['result']['matrix']},
                     'seconds': result['trial_inference_seconds'],
                     'usage': result['trial_usage'], 'run_id': result['run_id']})
    value = {
        'schema': 'mindthus.source-direct-observation-v3-codex-recovery-summary.v1',
        'rows': rows, 'complete': len(rows) == 2,
        'matched': sum(row['match'] for row in rows),
        'original_failures_preserved': frozen['original_failures'],
        'qualification': False,
    }
    base.save(ROOT / 'summary.json', value)
    print(json.dumps({'complete': value['complete'], 'matched': value['matched'],
                      'seconds': sum(row['seconds'] for row in rows)},
                     ensure_ascii=False), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('freeze', 'run', 'report'))
    parser.add_argument('--candidate', choices=CANDIDATES)
    args = parser.parse_args()
    if args.command == 'freeze':
        freeze()
    elif args.command == 'run':
        require(args.candidate is not None, 'candidate_required')
        run_one(args.candidate)
    else:
        report()


if __name__ == '__main__':
    main()
