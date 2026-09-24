"""One-case, preregistered A/B/C development carrier for current Codex.

This file is experiment-local. It reuses entry.run and the existing current-agent
handoff; it does not install a new product provider or touch old episodes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))

from experiments.typed_decision import entry, route_control as rc
from experiments.typed_decision.contracts import (
    BatchResult, DecisionResult, EngineIdentity, ResolvedRuntime, ServingIdentity,
    canonical, digest, provider_configuration, require,
)
from experiments.typed_decision.current_host import CurrentAgentHost, submit_response
from experiments.typed_decision.providers import ProviderError, TypeSafeJevProvider
from experiments.typed_decision.relationship_live import deadline_post_json
from experiments.typed_decision.session import implementation_digest, read_record, write_once

ROOT = Path('/Users/william/Documents/Codex/2026-09-24/mindthus-abc-current-codex-v1')
FREEZE = ROOT / 'freeze.json'
MODEL = 'gpt-6-sol'
CODEX = '/Applications/ChatGPT.app/Contents/Resources/codex'
AUTH = 'Owner started a new #211 A/B/C development batch in local Codex, 2026-09-24; no CPA/OpenRouter'
FILES = ('PLAN.md', 'cases.json', 'A-B2-prompt.txt', 'B-B2-judge-prompt.txt',
         'B-B2-judge-schema.json', 'run.py')
UNKNOWN = {'input_tokens': None, 'output_tokens': None, 'cost_usd': None}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: dict) -> None:
    if path.exists():
        require(read_record(path) == value, 'immutable_abc_record_changed')
    else:
        write_once(path, value)


def case() -> dict:
    obj = json.loads((HERE / 'cases.json').read_bytes())
    require(obj['schema'] == 'mindthus.abc-current-codex-development-cases.v1'
            and len(obj['cases']) == 1 and obj['cases'][0]['id'] == 'B2', 'abc_case_identity')
    return obj['cases'][0]


def packet(arm: str) -> dict:
    require(arm in ('B', 'C'), 'abc_arm')
    p = json.loads(canonical(case()['packet']))
    p['episode_id'] += '-' + arm
    return p


def home(arm: str) -> Path:
    return ROOT / ('codex-home' if arm == 'A' else 'codex-home-bc')


def codex_call(label: str, prompt: str, *, arm: str, timeout: float,
               schema: Path | None = None) -> tuple[str | None, dict]:
    """One Codex CLI request with its own immutable intent/outcome and no retry."""
    directory = ROOT / 'codex-calls' / label
    directory.mkdir(parents=True, exist_ok=True)
    workspace = ROOT / 'workspaces' / label
    workspace.mkdir(parents=True, exist_ok=True)
    intent = {'label': label, 'arm': arm, 'model': MODEL, 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
              'schema_sha256': sha(schema) if schema else None, 'timeout_seconds': timeout,
              'code_home': str(home(arm)), 'workspace': str(workspace), 'sandbox': 'read-only',
              'ephemeral': True, 'no_user_config': True}
    ip, op = directory / 'intent.json', directory / 'outcome.json'
    if op.exists():
        require(ip.exists() and read_record(ip) == intent, 'abc_codex_call_identity_changed')
        outcome = read_record(op)
        last = directory / 'last-message.txt'
        return (last.read_text() if last.exists() else None), outcome
    require(not ip.exists(), 'unknown_codex_call_do_not_retry')
    require(home(arm).is_dir() and (home(arm) / 'auth.json').exists(), 'codex_profile_unavailable')
    save(ip, intent)
    command = [CODEX, 'exec', '--ignore-user-config', '--ephemeral', '--skip-git-repo-check',
               '--sandbox', 'read-only', '-m', MODEL, '-C', str(workspace), '--json',
               '-o', str(directory / 'last-message.txt')]
    if schema:
        command += ['--output-schema', str(schema)]
    command += ['-']
    env = os.environ.copy()
    env['CODEX_HOME'] = str(home(arm))
    for key in ('TYPESAFE_API_KEY', 'MINDTHUS_HOST_API_KEY', 'OPENROUTER_API_KEY'):
        env.pop(key, None)
    begin = time.monotonic()
    status, output, error = 'failed', '', ''
    try:
        result = subprocess.run(command, input=prompt, text=True, capture_output=True,
                                timeout=timeout, env=env, cwd=workspace, check=False)
        output, error = result.stdout, result.stderr
        status = 'complete' if result.returncode == 0 and (directory / 'last-message.txt').exists() else 'failed'
        exit_code = result.returncode
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout.decode('utf-8', 'replace') if isinstance(exc.stdout, bytes) else (exc.stdout or '')
        error = exc.stderr.decode('utf-8', 'replace') if isinstance(exc.stderr, bytes) else (exc.stderr or '')
        status, exit_code = 'timeout_unknown_billing', None
    elapsed = time.monotonic() - begin
    # JSONL is the native CLI event record. It contains no API key supplied by this carrier.
    (directory / 'events.jsonl').write_text(output)
    usage = dict(UNKNOWN)
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        row = event.get('usage') if isinstance(event, dict) else None
        if isinstance(row, dict):
            for source, target in (('input_tokens', 'input_tokens'), ('output_tokens', 'output_tokens')):
                if type(row.get(source)) is int and row[source] >= 0:
                    usage[target] = row[source]
    outcome = {'status': status, 'exit_code': exit_code, 'elapsed_seconds': elapsed,
               'events_sha256': sha(directory / 'events.jsonl'),
               'stderr_sha256': hashlib.sha256(error.encode()).hexdigest(),
               'last_sha256': sha(directory / 'last-message.txt') if (directory / 'last-message.txt').exists() else None,
               'usage': usage, 'model_requested': MODEL, 'model_service_attestation': 'not_observed'}
    save(op, outcome)
    return ((directory / 'last-message.txt').read_text() if outcome['last_sha256'] else None), outcome


class CodexDecisionProvider:
    """One bounded ordinary-LLM adapter for the exact B2 question batch."""
    capabilities = frozenset({'select', 'assess_proposition', 'rate'})
    is_live = True
    engine_identity = EngineIdentity('structured_chat', 'codex_cli', MODEL)
    serving_identity = ServingIdentity('codex_cli', 'exec-json-schema-v1', MODEL,
                                       'local://codex-exec', 'abc-B2-v1')

    def __init__(self):
        self.receipt = None

    def clear_receipt(self):
        self.receipt = None

    def response_receipt(self):
        return self.receipt

    def validate_runtime(self, runtime: ResolvedRuntime):
        runtime.validate()
        require(runtime.model == MODEL and runtime.provider == 'codex-cli-configured-model',
                'codex_runtime_identity_changed')

    def evaluate(self, specs, context, timeout):
        require(len(specs) == 4 and {s.id for s in specs} ==
                {'M02.I1.tvg', 'M03.I1.tvg', 'S01.I1', 'S02.I1'}, 'abc_B_question_set_changed')
        questions = {s.id: {'kind': s.kind, 'question': s.question, 'criteria': s.criteria} for s in specs}
        prefix = (HERE / 'B-B2-judge-prompt.txt').read_text().split('\n\n', 1)[0]
        prompt = prefix + '\n\n' + canonical({'state': context, 'questions': questions}).decode() + '\n'
        require(prompt == (HERE / 'B-B2-judge-prompt.txt').read_text(), 'abc_B_prompt_drift')
        answer, call = codex_call('B2-B-judge', prompt, arm='B', timeout=min(timeout, 44),
                                  schema=HERE / 'B-B2-judge-schema.json')
        self.receipt = {'call_label': 'B2-B-judge', 'last_sha256': call['last_sha256'],
                        'events_sha256': call['events_sha256'], 'validated_usage': call['usage'],
                        'model_service_attestation': 'not_observed'}
        if call['status'] != 'complete' or not answer:
            raise ProviderError('codex_judge_' + call['status'])
        try:
            raw = json.loads(answer)
            require(isinstance(raw, dict) and set(raw) == {'answers'} and
                    set(raw['answers']) == {s.id for s in specs}, 'abc_B_answer_shape')
            results = {}
            for spec in specs:
                item = raw['answers'][spec.id]
                require(isinstance(item, dict) and set(item) == {'status', 'value'}, 'abc_B_item_shape')
                row = DecisionResult(item['status'], item['value'], None,
                                     'ordinary_llm_subjective_value_not_calibrated')
                row.validate(spec)
                results[spec.id] = row
        except (ValueError, KeyError, TypeError) as exc:
            raise ProviderError('codex_judge_invalid_json_or_contract') from None
        runtime = ResolvedRuntime(MODEL, 'codex-cli-configured-model')
        return BatchResult(results, runtime, call['usage'])


def objects(arm: str, p: dict):
    provider = CodexDecisionProvider() if arm == 'B' else TypeSafeJevProvider(
        model='jev-1.13.0', choice_rounding=True, transport=deadline_post_json)
    host = CurrentAgentHost(p['authority']['owner_ref'])
    return provider, host


def admission(arm: str, p: dict, bundle: dict):
    provider, host = objects(arm, p)
    a = {'schema': 'mindthus.route-control-live.v1', 'mode': rc.MODE,
         'root': str(ROOT / 'episodes' / arm), 'implementation': implementation_digest(),
         'source_bindings': bundle['sources'], 'provider': provider_configuration(provider),
         'packet_hashes': [digest(p)], 'authorization_ref': AUTH,
         'ceilings': {'judgments': 1, 'corrections': 0, 'organize': 0, 'arbitrations': 0,
                      'executions': 1, 'requests': 1, 'reserve_per_jev_usd': .02},
         'executor': host.configuration, 'arbitrator': None, 'corrector': None, 'organizer': None}
    rc._admission(a, ROOT / 'episodes' / arm, p, provider, bundle,
                  {'executor': host, 'arbitrator': None, 'corrector': None, 'organizer': None})
    return a


def prepare() -> dict:
    bundle, qs, bindings = rc.load_policy(REPO)
    identities, admissions = {}, {}
    for arm in ('B', 'C'):
        p = packet(arm)
        compiled = rc.compile_route(p, REPO, bundle, qs, bindings)
        require(len(compiled.specs) == 4, 'abc_question_count')
        identities[arm] = {'packet_sha256': digest(p),
                           'questions_sha256': digest([s.to_dict() for s in compiled.specs]),
                           'context_sha256': digest(compiled.context)}
        admissions[arm] = admission(arm, p, bundle)
    frozen = {'schema': 'mindthus.abc-current-codex-development-freeze.v1',
              'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO,
                                                       text=True).strip(),
              'implementation': implementation_digest(),
              'files': {name: sha(HERE / name) for name in FILES},
              'source_bindings': bundle['sources'], 'identities': identities,
              'admissions': admissions, 'model': MODEL, 'codex_cli': CODEX,
              'A_skill_root': str(home('A') / 'skills'),
              'B_C_skill_root': None, 'root': str(ROOT),
              'max_codex_cli_calls': 4, 'max_typesafe_calls': 1,
              'jev_reservation_usd': .02, 'automatic_retries': 0,
              'CPA_calls': 0, 'OpenRouter_calls': 0,
              'claim_ceiling': 'one exposed development case; no formal ABC quality or cost qualification'}
    save(FREEZE, frozen)
    return frozen


def verify() -> dict:
    frozen = read_record(FREEZE)
    require(frozen['implementation'] == implementation_digest(), 'abc_implementation_changed')
    require(all(sha(HERE / name) == value for name, value in frozen['files'].items()),
            'abc_frozen_file_changed')
    bundle, qs, bindings = rc.load_policy(REPO)
    require(bundle['sources'] == frozen['source_bindings'], 'abc_method_or_policy_changed')
    for arm in ('B', 'C'):
        p = packet(arm)
        compiled = rc.compile_route(p, REPO, bundle, qs, bindings)
        require(frozen['identities'][arm] == {'packet_sha256': digest(p),
                                              'questions_sha256': digest([s.to_dict() for s in compiled.specs]),
                                              'context_sha256': digest(compiled.context)}, 'abc_compilation_changed')
        require(frozen['admissions'][arm] == admission(arm, p, bundle), 'abc_admission_changed')
    return frozen


def run_a() -> dict:
    verify()
    answer, call = codex_call('B2-A-baseline', (HERE / 'A-B2-prompt.txt').read_text(),
                              arm='A', timeout=90)
    print(json.dumps({'arm': 'A', 'status': call['status'], 'answer_path':
                      str(ROOT / 'codex-calls/B2-A-baseline/last-message.txt') if answer else None,
                      'usage': call['usage']}, ensure_ascii=False))
    return call


def credential(path: Path) -> str:
    require(stat.S_IMODE(path.stat().st_mode) & 0o077 == 0, 'credential_file_not_private')
    values = {}
    for line in path.read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key, value = line.split('=', 1)
            values[key.strip()] = value.strip().strip('"\'')
    require(bool(values.get('TYPESAFE_API_KEY')), 'typesafe_credential_absent')
    return values['TYPESAFE_API_KEY']


def run_graph(arm: str, credential_file: Path | None = None) -> dict:
    frozen = verify()
    p = packet(arm)
    provider, host = objects(arm, p)
    previous = os.environ.get('TYPESAFE_API_KEY')
    if arm == 'C' and credential_file:
        os.environ['TYPESAFE_API_KEY'] = credential(credential_file)
    try:
        result = entry.run(ROOT / 'episodes' / arm, provider, p, REPO, mode=rc.MODE,
                           executor=host, live_admission=frozen['admissions'][arm])
    finally:
        if previous is None:
            os.environ.pop('TYPESAFE_API_KEY', None)
        else:
            os.environ['TYPESAFE_API_KEY'] = previous
    save(ROOT / 'snapshots' / (arm + '-' + digest(result) + '.json'), result)
    (ROOT / (arm + '-latest.json')).write_bytes(canonical(result) + b'\n')
    print(json.dumps({'arm': arm, 'status': result.get('status'), 'reason': result.get('reason'),
                      'counts': result.get('counts'), 'host_request': result.get('host_request'),
                      'route': result.get('route', {}).get('per_issue') if result.get('route') else None},
                     ensure_ascii=False))
    return result


def host_prompt(handoff: dict) -> str:
    return ('你是当前 Codex 宿主，执行已提交的范围。原始材料与加载的方法全文都在 request 中。'
            '只写实际完成的短备忘录，不添加未给定效果数字。'
            '如果完成，JSON 只包含 performed_methods（实际用过的全部方法名）和 text（备忘录正文）。'
            '若不能在已提交范围内完成，返回不能提交的错误文本，不要伪造完成。\n\n'
            + canonical({'instruction': handoff['instruction'], 'request': handoff['request']}).decode() + '\n')


def run_host(arm: str) -> dict:
    verify()
    prior = json.loads((ROOT / (arm + '-latest.json')).read_bytes())
    hp = prior.get('host_request')
    require(isinstance(hp, str) and hp, 'abc_no_pending_host_request')
    handoff = read_record(Path(hp))
    require(handoff['role'] == 'execution', 'abc_unexpected_host_role')
    prompt = host_prompt(handoff)
    answer, call = codex_call('B2-' + arm + '-host', prompt, arm=arm,
                              timeout=min(43, handoff['allowance_seconds']))
    if call['status'] != 'complete' or not answer:
        print(json.dumps({'arm': arm, 'host': call['status'], 'submission': 'unrun'}))
        return call
    try:
        raw = json.loads(answer)
        require(isinstance(raw, dict) and set(raw) == {'performed_methods', 'text'},
                'abc_host_reply_shape')
        reply = {**handoff['reply_shape'], 'performed_methods': raw['performed_methods'],
                 'text': raw['text'], 'usage': call['usage']}
        submission = {'schema': 'mindthus.current-host-response.v1',
                      'request_id': handoff['request_id'],
                      'request_sha256': handoff['request_sha256'],
                      'owner_ref': handoff['owner_ref'],
                      'host_context_ref': 'abc-current-codex-v1:B2:' + arm + ':gpt-6-sol',
                      'elapsed_seconds': call['elapsed_seconds'], 'reply': reply}
        source_ref = submit_response(ROOT / 'episodes' / arm, REPO, submission)
        print(json.dumps({'arm': arm, 'host': 'submitted', 'receipt': source_ref}, ensure_ascii=False))
    except (ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'arm': arm, 'host': 'invalid_reply', 'error': type(exc).__name__}))
        return call
    return run_graph(arm)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'verify', 'A', 'B', 'C', 'B-host', 'C-host'))
    parser.add_argument('--credential-file', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        print(json.dumps({'freeze': digest(prepare()), 'model_calls': 0}))
    elif args.action == 'verify':
        print(json.dumps({'verified': True, 'freeze': digest(verify())}))
    elif args.action == 'A':
        run_a()
    elif args.action in ('B', 'C'):
        run_graph(args.action, args.credential_file)
    else:
        run_host(args.action[0])


if __name__ == '__main__':
    main()
