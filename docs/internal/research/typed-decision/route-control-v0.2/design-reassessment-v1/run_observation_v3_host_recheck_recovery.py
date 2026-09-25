"""Technical recovery for an unresolved host-consumption recheck.

The operator observed a missing local Jev key when the parent A recheck produced a
generic provider error.  Its ledger has no runtime, receipt or usage, which is consistent
with that diagnosis but does not independently prove that no upstream request occurred.
This successor preserves the outcome, binds the frozen host candidates, and admits one
fresh official TypeSafe recheck per A-F scenario.  It never retries an old intent.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_observation_v3 as base
import run_observation_v3_host_consumption as parent

from experiments.typed_decision import observation_assessment as obs
from experiments.typed_decision.contracts import digest, provider_configuration, require
from experiments.typed_decision.session import Limits, Session, implementation_digest, read_record

ROOT = parent.ROOT / 'recheck-recovery-v1'
SCENARIOS = parent.SCENARIOS
LIMITS = Limits(max_calls=1, max_seconds=60, max_request_bytes=98304)
AUTH = ('User authorized environment retry comparison for incomplete verification. The operator '
        'observed TYPESAFE_API_KEY absent at the parent A failure; the ledger records only a '
        'generic provider error and does not independently establish upstream delivery. Preserve '
        'the old intent and use official TypeSafe jev-1.13.0 only for new successor intents.')


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_commit() -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=base.REPO,
                                   text=True).strip()


def result_path(scenario: str) -> Path:
    return ROOT / 'results' / (scenario + '.json')


def manifest() -> dict:
    failed = parent.ROOT / 'trials/recheck/A/calls/38c2b5c4feec2bc272a7770a43f68b0ec2a771ab0b81d560f1122486dfdab56a/outcome.json'
    require(failed.exists(), 'parent_failed_outcome_missing')
    failure = read_record(failed)
    require(failure['resolved_runtime'] is None
            and all(row['status'] == 'provider_error' for row in failure['results'].values())
            and failure['usage'] == {'input_tokens': None, 'output_tokens': None, 'cost_usd': None},
            'parent_failure_not_unresolved_without_usage')
    p = base.jev_provider()
    rows = {}
    for scenario in SCENARIOS:
        data = parent.recheck_input(scenario)
        rows[scenario] = {
            'host_result_sha256': sha(parent.host_result_path(scenario)),
            'input_sha256': digest(data), 'request_key': parent.clean.request_key(data),
        }
    binding = {
        'source_commit': source_commit(), 'implementation': implementation_digest(),
        'runner_sha256': sha(Path(__file__)),
        'parent_host_freeze_sha256': sha(parent.ROOT / 'host-freeze.json'),
        'parent_recheck_freeze_sha256': sha(parent.ROOT / 'recheck-freeze.json'),
        'parent_failed_A_outcome_sha256': sha(failed),
        'parent_failure_class': 'generic_provider_error_without_runtime_receipt_or_usage',
        'operator_observation': 'TYPESAFE_API_KEY_missing_in_invoking_shell',
        'parent_upstream_delivery': 'not_independently_verifiable_from_ledger',
        'provider': provider_configuration(p), 'limits': asdict(LIMITS),
        'authorization_ref': AUTH, 'max_jev_calls': 6, 'technical_retries_per_new_intent': 0,
        'rows': rows,
    }
    freeze_sha256 = digest(binding)
    admissions = {}
    for scenario, row in rows.items():
        admissions[scenario] = {
            'scope': 'source-direct-v3.1-host-recheck-recovery-' + scenario,
            'implementation': binding['implementation'],
            'provider_configuration': binding['provider'], 'limits': binding['limits'],
            'request_allowlist': [row['request_key']], 'max_cost_usd': .02,
            'reserve_per_call_usd': .02, 'authorization_ref': AUTH,
            'freeze_sha256': freeze_sha256,
        }
    return {'schema': 'mindthus.source-direct-v3-host-recheck-recovery-freeze.v1',
            **binding, 'freeze_sha256': freeze_sha256, 'admissions': admissions}


def freeze() -> None:
    value = manifest()
    base.save(ROOT / 'freeze.json', value)
    print(json.dumps({'frozen': True, 'max_jev_calls': value['max_jev_calls'],
                      'freeze_sha256': value['freeze_sha256']}, ensure_ascii=False))


def run(scenario: str) -> None:
    frozen = read_record(ROOT / 'freeze.json')
    require(frozen == manifest(), 'host_recheck_recovery_freeze_changed')
    path = result_path(scenario)
    if path.exists():
        report = read_record(path)
        print(json.dumps({'scenario': scenario, 'reused_result': True,
                          'action': report['result']['action']}, ensure_ascii=False))
        return
    data = parent.recheck_input(scenario)
    p = base.jev_provider()
    admission = frozen['admissions'][scenario]
    with Session(ROOT / 'trials' / scenario, p, scope=admission['scope'],
                 limits=LIMITS, live_admission=admission) as session:
        report = obs.assess(session, data, base.REPO)
    base.save(path, report)
    print(json.dumps({'scenario': scenario, 'action': report['result']['action'],
                      'hits': report['result']['hits'],
                      'seconds': report['trial_inference_seconds']}, ensure_ascii=False), flush=True)


def summary() -> None:
    rows = []
    for scenario in SCENARIOS:
        path = result_path(scenario)
        report = read_record(path) if path.exists() else None
        rows.append({'scenario': scenario, 'complete': report is not None,
                     'action': report['result']['action'] if report else None,
                     'hits': report['result']['hits'] if report else None,
                     'seconds': report['trial_inference_seconds'] if report else None,
                     'usage': report['trial_usage'] if report else None})
    value = {'schema': 'mindthus.source-direct-v3-host-recheck-recovery-summary.v1',
             'complete': all(row['complete'] for row in rows), 'rows': rows,
             'parent_failure_preserved': True,
             'parent_upstream_delivery': 'not_independently_verifiable_from_ledger',
             'qualification': False}
    base.save(ROOT / 'summary.json', value)
    print(json.dumps({'complete': value['complete'],
                      'completed': sum(row['complete'] for row in rows)}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('freeze')
    one = sub.add_parser('run'); one.add_argument('--scenario', choices=SCENARIOS, required=True)
    sub.add_parser('summary')
    args = parser.parse_args()
    if args.command == 'freeze': freeze()
    elif args.command == 'run': run(args.scenario)
    else: summary()


if __name__ == '__main__':
    main()
