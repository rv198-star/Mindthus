"""Apply saved clean Jev observations through the current Codex host, then recheck.

This exposed D successor answers a narrower question than the observation campaign:
does a source-bound Jev finding actually enter the constrained host correction and
produce a candidate that the same contract can release?  Initial Jev observations are
reused; only candidate-bound rechecks make new Jev requests.  Acceptance checklists are
kept outside every model prompt.
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
import run_observation_v3_clean as clean

from experiments.typed_decision import entry, observation_assessment as obs
from experiments.typed_decision.contracts import canonical, digest, provider_configuration, require
from experiments.typed_decision.providers import FixtureProvider
from experiments.typed_decision.session import Limits, Session, implementation_digest, read_record

ROOT = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-source-direct-v3-host-consumption-v1')
SCENARIOS = clean.SCENARIOS
HOST_TIMEOUT = 220
JEV_LIMITS = Limits(max_calls=1, max_seconds=60, max_request_bytes=98304)
AUTH = ('User requested correction of the #211 comparison so saved clean Jev observations '
        'are actually consumed by the current Codex host, with candidate-bound Jev rechecks. '
        'Official TypeSafe jev-1.13.0 and current local Codex only.')
HOST_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'properties': {
        'disposition': {'type': 'string', 'enum': ['corrected', 'objected']},
        'final_answer': {'type': 'string'},
        'objection': {'anyOf': [{'type': 'string'}, {'type': 'null'}]},
    },
    'required': ['disposition', 'final_answer', 'objection'],
}


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_commit() -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=base.REPO,
                                   text=True).strip()


def replay_initial(scenario: str) -> tuple[dict, dict, dict]:
    """Replay immutable clean Jev values through v3.1 without a model request."""
    require(scenario in SCENARIOS, 'host_consumption_scenario')
    source_path = clean.result_path('jev', scenario, 'x')
    source = read_record(source_path)
    answers = {row['check_id']: row['value'] for row in source['result']['matrix']
               if row['status'] == 'ok'}
    data = clean.neutral_input(scenario, 'x')
    provider = FixtureProvider(answers)
    trial = ROOT / 'initial-replay' / scenario
    with Session(trial, provider, scope='source-direct-v3.1-host-consumption-replay',
                 limits=entry.CHECK_LIMITS) as session:
        report = obs.assess(session, data, base.REPO)
    require(report['result']['action'] == 'request_correction',
            'saved_jev_observation_no_longer_actionable')
    request = obs.correction_request(report, data, base.REPO)
    require(request['instruction_checks'] == ['evidence_decision_fit'],
            'host_instruction_not_direct_evidence_only')
    return data, report, request


def host_prompt(scenario: str) -> str:
    _, _, request = replay_initial(scenario)
    return (
        'You are the current Codex host consuming one already committed constrained '
        'observation. Apply the correction request once to the current candidate. Use only '
        'the supplied original task, evidence, context and canonical rules. Preserve valid '
        'facts, distinctions, uncertainty, scope and permissions. Do not mention the '
        'assessment machinery. If the observation is wrong, return disposition=objected '
        'with a source-bound objection and leave final_answer as the best supported answer. '
        'Otherwise return disposition=corrected, objection=null, and a concise direct Chinese '
        'answer to the user. Return exactly the JSON schema.\n\n'
        + canonical({'correction_request': request}).decode() + '\n'
    )


def host_result_path(scenario: str) -> Path:
    return ROOT / 'results' / 'host' / (scenario + '.json')


def recheck_result_path(scenario: str) -> Path:
    return ROOT / 'results' / 'recheck' / (scenario + '.json')


def host_manifest() -> dict:
    prompts = {}
    for scenario, case_id in SCENARIOS.items():
        prompt = host_prompt(scenario)
        prompts[scenario] = {
            'case_id_sha256': digest({'case_id': case_id}),
            'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
            'initial_clean_result_sha256': sha(clean.result_path('jev', scenario, 'x')),
            'pure_codex_baseline_sha256': sha(base.ACCEPTED_ROOT / (case_id + '.json')),
        }
    return {
        'schema': 'mindthus.source-direct-v3-host-consumption-freeze.v1',
        'source_commit': source_commit(), 'implementation': implementation_digest(),
        'runner_sha256': sha(Path(__file__)),
        'clean_freeze_sha256': sha(clean.ROOT / 'freeze.json'),
        'clean_complete_sha256': sha(clean.ROOT / 'reports' / 'complete.json'),
        'consumption_policy': obs.CONSUMPTION_POLICY,
        'host_model_requested': base.MODEL_CODEX, 'host_timeout_seconds': HOST_TIMEOUT,
        'host_schema_sha256': digest(HOST_SCHEMA), 'max_host_calls': 6,
        'initial_jev_calls_reused': 6, 'prompts': prompts,
        'gate': {'scenario': 'A', 'must_complete_before_other_host_calls': True},
        'acceptance_not_model_visible': True, 'authorization_ref': AUTH,
        'evidence_limit': ('six exposed AI-synthetic bad candidates; pure Codex baseline is '
                           'historical same-source candidate correction, not natural first answer'),
    }


def freeze_host() -> None:
    value = host_manifest()
    base.save(ROOT / 'host-freeze.json', value)
    print(json.dumps({'frozen': True, 'source_commit': value['source_commit'],
                      'host_calls': value['max_host_calls']}, ensure_ascii=False))


def run_host(scenario: str) -> None:
    frozen = read_record(ROOT / 'host-freeze.json')
    require(frozen == host_manifest(), 'host_consumption_freeze_changed')
    if scenario != 'A':
        require(host_result_path('A').exists(), 'host_consumption_A_gate_not_completed')
    path = host_result_path(scenario)
    if path.exists():
        result = read_record(path)
        print(json.dumps({'scenario': scenario, 'reused_result': True,
                          'disposition': result['response']['disposition']}, ensure_ascii=False))
        return
    prompt = host_prompt(scenario)
    label = 'host-' + hashlib.sha256(prompt.encode()).hexdigest()[:24]
    message, call = base.codex_call(label, prompt, HOST_TIMEOUT, HOST_SCHEMA,
                                    root=ROOT, codex_home=clean.CODEX_HOME)
    require(call['status'] == 'complete' and message, 'host_consumption_codex_failed')
    response = json.loads(message)
    require(set(response) == {'disposition', 'final_answer', 'objection'}
            and isinstance(response['final_answer'], str) and response['final_answer'].strip(),
            'host_consumption_response_shape')
    require((response['disposition'] == 'corrected' and response['objection'] is None)
            or (response['disposition'] == 'objected'
                and isinstance(response['objection'], str) and response['objection'].strip()),
            'host_consumption_disposition_shape')
    _, report, request = replay_initial(scenario)
    base.save(path, {
        'scenario': scenario, 'response': response,
        'parent_observation_ref': report['source_ref'],
        'correction_request_id': request['request_id'],
        'instruction_checks': request['instruction_checks'],
        'call_ref': label, 'call_outcome_sha256': sha(ROOT / 'codex-calls' / label / 'outcome.json'),
        'seconds': call['elapsed_seconds'], 'usage': call['usage'],
        'model_requested': call['model_requested'],
        'model_service_attestation': call['model_service_attestation'],
    })
    print(json.dumps({'scenario': scenario, 'disposition': response['disposition'],
                      'seconds': call['elapsed_seconds'], 'instruction_checks': request['instruction_checks']},
                     ensure_ascii=False), flush=True)


def recheck_input(scenario: str) -> dict:
    host = read_record(host_result_path(scenario))
    text = host['response']['final_answer']
    data = clean.neutral_input(scenario, 'x')
    identity = digest({'candidate_text': text})
    data['state_version'] = 'source-direct-v3.1-host-recheck-v1'
    data['target'] = {'id': 'current-candidate', 'kind': 'candidate_answer',
                      'version': identity, 'source_ref': 'candidate:' + identity, 'text': text}
    data['activation']['source_ref'] = 'policy:' + digest({'policy': obs.POLICY,
                                                            'consumption': obs.CONSUMPTION_POLICY})
    data['activation']['reason'] = 'Candidate-bound recheck after constrained host correction'
    obs.validate_envelope(data)
    clean.assert_neutral_model_view(data)
    return data


def recheck_manifest() -> dict:
    host_freeze = read_record(ROOT / 'host-freeze.json')
    require(host_freeze == host_manifest(), 'host_freeze_changed_before_recheck')
    require(all(host_result_path(s).exists() for s in SCENARIOS), 'host_results_incomplete')
    p = base.jev_provider()
    rows = {}
    for scenario in SCENARIOS:
        data = recheck_input(scenario)
        rows[scenario] = {
            'host_result_sha256': sha(host_result_path(scenario)),
            'candidate_sha256': digest({'text': data['target']['text']}),
            'input_sha256': digest(data), 'request_key': clean.request_key(data),
        }
    binding = {'host_freeze_sha256': sha(ROOT / 'host-freeze.json'),
               'host_results': rows, 'implementation': implementation_digest(),
               'provider': provider_configuration(p), 'limits': asdict(JEV_LIMITS),
               'authorization_ref': AUTH, 'max_jev_calls': 6, 'technical_retries': 0}
    freeze_sha256 = digest(binding)
    admissions = {}
    for scenario, row in rows.items():
        admissions[scenario] = {
            'scope': 'source-direct-v3.1-host-recheck-' + scenario,
            'implementation': binding['implementation'],
            'provider_configuration': binding['provider'], 'limits': binding['limits'],
            'request_allowlist': [row['request_key']], 'max_cost_usd': .02,
            'reserve_per_call_usd': .02, 'authorization_ref': AUTH,
            'freeze_sha256': freeze_sha256,
        }
    return {'schema': 'mindthus.source-direct-v3-host-recheck-freeze.v1', **binding,
            'freeze_sha256': freeze_sha256, 'admissions': admissions}


def freeze_recheck() -> None:
    value = recheck_manifest()
    base.save(ROOT / 'recheck-freeze.json', value)
    print(json.dumps({'frozen': True, 'jev_calls': value['max_jev_calls'],
                      'freeze_sha256': value['freeze_sha256']}, ensure_ascii=False))


def run_recheck(scenario: str) -> None:
    frozen = read_record(ROOT / 'recheck-freeze.json')
    require(frozen == recheck_manifest(), 'host_recheck_freeze_changed')
    path = recheck_result_path(scenario)
    if path.exists():
        report = read_record(path)
        print(json.dumps({'scenario': scenario, 'reused_result': True,
                          'action': report['result']['action']}, ensure_ascii=False))
        return
    data = recheck_input(scenario)
    p = base.jev_provider()
    admission = frozen['admissions'][scenario]
    with Session(ROOT / 'trials' / 'recheck' / scenario, p,
                 scope=admission['scope'], limits=JEV_LIMITS,
                 live_admission=admission) as session:
        report = obs.assess(session, data, base.REPO)
    base.save(path, report)
    print(json.dumps({'scenario': scenario, 'action': report['result']['action'],
                      'hits': report['result']['hits'],
                      'seconds': report['trial_inference_seconds']}, ensure_ascii=False), flush=True)


def report() -> None:
    require((ROOT / 'host-freeze.json').exists(), 'host_freeze_missing')
    rows = []
    for scenario, case_id in SCENARIOS.items():
        host_path, recheck_path = host_result_path(scenario), recheck_result_path(scenario)
        host = read_record(host_path) if host_path.exists() else None
        recheck = read_record(recheck_path) if recheck_path.exists() else None
        baseline = read_record(base.ACCEPTED_ROOT / (case_id + '.json'))
        rows.append({
            'scenario': scenario, 'case_id': case_id,
            'host_complete': host is not None,
            'host_disposition': host['response']['disposition'] if host else None,
            'host_final_answer': host['response']['final_answer'] if host else None,
            'host_seconds': host['seconds'] if host else None,
            'host_usage': host['usage'] if host else None,
            'recheck_complete': recheck is not None,
            'recheck_action': recheck['result']['action'] if recheck else None,
            'recheck_hits': recheck['result']['hits'] if recheck else None,
            'recheck_seconds': recheck['trial_inference_seconds'] if recheck else None,
            'recheck_usage': recheck['trial_usage'] if recheck else None,
            'pure_codex_baseline_answer': baseline['final_answer'],
            'strict_acceptance': base.cases()[case_id]['acceptance'],
        })
    value = {'schema': 'mindthus.source-direct-v3-host-consumption-summary.v1',
             'complete': all(r['host_complete'] and r['recheck_complete'] for r in rows),
             'rows': rows, 'qualification': False,
             'acceptance_requires_post_run_review': True,
             'initial_jev_calls_reused': 6,
             'new_model_calls': {'codex_host_max': 6, 'jev_recheck_max': 6,
                                 'cpa': 0, 'openrouter': 0}}
    base.save(ROOT / 'summary.json', value)
    print(json.dumps({'complete': value['complete'],
                      'host_complete': sum(r['host_complete'] for r in rows),
                      'recheck_complete': sum(r['recheck_complete'] for r in rows)},
                     ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('freeze-host')
    host = sub.add_parser('host'); host.add_argument('--scenario', choices=SCENARIOS, required=True)
    sub.add_parser('freeze-recheck')
    recheck = sub.add_parser('recheck'); recheck.add_argument('--scenario', choices=SCENARIOS, required=True)
    sub.add_parser('report')
    args = parser.parse_args()
    if args.command == 'freeze-host': freeze_host()
    elif args.command == 'host': run_host(args.scenario)
    elif args.command == 'freeze-recheck': freeze_recheck()
    elif args.command == 'recheck': run_recheck(args.scenario)
    else: report()


if __name__ == '__main__':
    main()
