"""Two frozen, case-local development comparisons; no production provider changes."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))
BASE_FILE = HERE.parent / 'abc-current-codex-v1' / 'run.py'
module_spec = importlib.util.spec_from_file_location('abc_v1_carrier', BASE_FILE)
base = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(base)

from experiments.typed_decision import entry, route_control as rc
from experiments.typed_decision.contracts import (
    BatchResult, ContractError, DecisionResult, ResolvedRuntime, ServingIdentity,
    canonical, digest, provider_configuration, require,
)
from experiments.typed_decision.current_host import CurrentAgentHost, submit_response
from experiments.typed_decision.providers import ProviderError, TypeSafeJevProvider
from experiments.typed_decision.relationship_live import deadline_post_json
from experiments.typed_decision.session import implementation_digest, read_record

IDS = ('B3', 'C2')
EXTERNAL = Path('/Users/william/Documents/Codex/2026-09-24/mindthus-abc-hard-dev-v1')
PROMPT_PREFIX = (HERE.parent / 'abc-current-codex-v1' / 'B-B2-judge-prompt.txt').read_text().split('\n\n', 1)[0]
AUTH = 'Owner continued #211 current-Codex ABC development on 2026-09-24; no CPA/OpenRouter'
FROZEN_FILES = ('cases.json', 'A-prompt.txt', 'B-judge-prompt.txt', 'B-judge-schema.json')


def configure(cid: str):
    require(cid in IDS, 'unknown_case')
    base.HERE = HERE / 'inputs' / cid
    base.ROOT = EXTERNAL / cid
    base.FREEZE = base.ROOT / 'freeze.json'
    base.AUTH = AUTH


def one_case() -> dict:
    data = json.loads((base.HERE / 'cases.json').read_bytes())
    require(data['schema'] == 'mindthus.abc-current-codex-development-cases.v1'
            and len(data['cases']) == 1 and data['cases'][0]['id'] == base.HERE.name,
            'case_identity_changed')
    return data['cases'][0]


def packet(arm: str) -> dict:
    p = json.loads(canonical(one_case()['packet']))
    p['episode_id'] += '-' + arm
    return p


def compile_case(arm='B'):
    bundle, qs, bindings = rc.load_policy(REPO)
    return rc.compile_route(packet(arm), REPO, bundle, qs, bindings), bundle


def make_schema(specs):
    properties = {}
    for spec in specs:
        if spec.kind == 'select':
            value = {'type': 'string', 'enum': sorted(spec.criteria)}
        else:
            value = {'type': 'number', 'minimum': 0,
                     'maximum': 1 if spec.kind == 'assess_proposition' else len(spec.criteria) - 1}
        properties[spec.id] = {'type': 'object', 'additionalProperties': False,
                               'properties': {'status': {'type': 'string', 'enum':
                                                         ['ok', 'abstain', 'missing_context']},
                                              'value': {'anyOf': [value, {'type': 'null'}]}},
                               'required': ['status', 'value']}
    return {'type': 'object', 'additionalProperties': False,
            'properties': {'answers': {'type': 'object', 'additionalProperties': False,
                                       'properties': properties, 'required': sorted(properties)}},
            'required': ['answers']}


def question_prompt(compiled):
    questions = {s.id: {'kind': s.kind, 'question': s.question, 'criteria': s.criteria}
                 for s in compiled.specs}
    return PROMPT_PREFIX + '\n\n' + canonical({'state': compiled.context,
                                                'questions': questions}).decode() + '\n'


def write_inputs():
    compiled, _ = compile_case()
    require(len(compiled.specs) >= 2, 'empty_judgment')
    (base.HERE / 'B-judge-prompt.txt').write_text(question_prompt(compiled))
    (base.HERE / 'B-judge-schema.json').write_text(
        json.dumps(make_schema(compiled.specs), ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'case': base.HERE.name, 'question_count': len(compiled.specs),
                      'question_ids': [s.id for s in compiled.specs]}))


class OrdinaryCodexProvider(base.CodexDecisionProvider):
    serving_identity = ServingIdentity('codex_cli', 'exec-json-schema-v1', base.MODEL,
                                       'local://codex-exec', 'abc-hard-dev-v1')

    def evaluate(self, specs, context, timeout):
        compiled, _ = compile_case()
        require([s.to_dict() for s in specs] == [s.to_dict() for s in compiled.specs]
                and context == compiled.context, 'ordinary_llm_compilation_changed')
        prompt = question_prompt(compiled)
        require(prompt == (base.HERE / 'B-judge-prompt.txt').read_text(), 'ordinary_llm_prompt_drift')
        label = base.HERE.name + '-B-judge'
        answer, call = base.codex_call(label, prompt, arm='B', timeout=min(timeout, 44),
                                       schema=base.HERE / 'B-judge-schema.json')
        self.receipt = {'call_label': label, 'last_sha256': call['last_sha256'],
                        'events_sha256': call['events_sha256'], 'validated_usage': call['usage'],
                        'model_service_attestation': 'not_observed'}
        if call['status'] != 'complete' or not answer:
            raise ProviderError('codex_judge_' + call['status'])
        try:
            raw = json.loads(answer)
            require(isinstance(raw, dict) and set(raw) == {'answers'} and
                    set(raw['answers']) == {s.id for s in specs}, 'ordinary_llm_answer_shape')
            results = {}
            for spec in specs:
                item = raw['answers'][spec.id]
                require(isinstance(item, dict) and set(item) == {'status', 'value'},
                        'ordinary_llm_item_shape')
                row = DecisionResult(item['status'], item['value'], None,
                                     'ordinary_llm_subjective_value_not_calibrated')
                row.validate(spec)
                results[spec.id] = row
        except (ValueError, KeyError, TypeError, ContractError):
            raise ProviderError('codex_judge_invalid_json_or_contract') from None
        return BatchResult(results, ResolvedRuntime(base.MODEL, 'codex-cli-configured-model'),
                           call['usage'])


def objects(arm: str, p: dict):
    provider = OrdinaryCodexProvider() if arm == 'B' else TypeSafeJevProvider(
        model='jev-1.13.0', choice_rounding=True, transport=deadline_post_json)
    return provider, CurrentAgentHost(p['authority']['owner_ref'])


def admission(arm: str, p: dict, bundle: dict):
    provider, host = objects(arm, p)
    a = {'schema': 'mindthus.route-control-live.v1', 'mode': rc.MODE,
         'root': str(base.ROOT / 'episodes' / arm), 'implementation': implementation_digest(),
         'source_bindings': bundle['sources'], 'provider': provider_configuration(provider),
         'packet_hashes': [digest(p)], 'authorization_ref': AUTH,
         'ceilings': {'judgments': 1, 'corrections': 0, 'organize': 0, 'arbitrations': 0,
                      'executions': 1, 'requests': 1, 'reserve_per_jev_usd': .02},
         'executor': host.configuration, 'arbitrator': None, 'corrector': None, 'organizer': None}
    rc._admission(a, base.ROOT / 'episodes' / arm, p, provider, bundle,
                  {'executor': host, 'arbitrator': None, 'corrector': None, 'organizer': None})
    return a


def profile_setup():
    for arm in ('A', 'B'):
        home = base.home(arm)
        home.mkdir(parents=True, exist_ok=True)
        config = home / 'config.toml'
        if config.exists():
            require(config.read_text() == 'model = "gpt-6-sol"\n', 'codex_config_changed')
        else:
            config.write_text('model = "gpt-6-sol"\n')
        auth = home / 'auth.json'
        if not auth.exists():
            auth.symlink_to(Path('/Users/william/.codex/auth.json'))
        require(auth.resolve() == Path('/Users/william/.codex/auth.json').resolve(),
                'codex_auth_binding_changed')
    skill_home = base.home('A') / 'skills'
    if not skill_home.exists():
        shutil.copytree(REPO / 'skills', skill_home, symlinks=False)
    require(not (base.home('B') / 'skills').exists(), 'B_C_skill_leak')


def freeze():
    profile_setup()
    compiled, bundle = compile_case()
    require((base.HERE / 'B-judge-prompt.txt').read_text() == question_prompt(compiled)
            and json.loads((base.HERE / 'B-judge-schema.json').read_text()) ==
            make_schema(compiled.specs), 'ordinary_llm_contract_changed')
    skill_files = {str(p.relative_to(REPO / 'skills')): base.sha(p)
                   for p in (REPO / 'skills').rglob('*') if p.is_file()}
    for name, value in skill_files.items():
        require(base.sha(base.home('A') / 'skills' / name) == value, 'A_skill_copy_changed')
    identities, admissions = {}, {}
    for arm in ('B', 'C'):
        c, _ = compile_case(arm)
        p = packet(arm)
        identities[arm] = {'packet': digest(p), 'questions': digest([s.to_dict() for s in c.specs]),
                           'context': digest(c.context)}
        admissions[arm] = admission(arm, p, bundle)
    record = {'schema': 'mindthus.abc-hard-development-freeze.v1',
              'case_id': base.HERE.name,
              'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                       cwd=REPO, text=True).strip(),
              'implementation': implementation_digest(), 'base_runner_sha256': base.sha(BASE_FILE),
              'runner_sha256': base.sha(HERE / 'run.py'),
              'files': {name: base.sha(base.HERE / name) for name in FROZEN_FILES},
              'skills': skill_files, 'source_bindings': bundle['sources'],
              'identities': identities, 'admissions': admissions,
              'model_requested': base.MODEL, 'jev_model': 'jev-1.13.0',
              'root': str(base.ROOT), 'max_codex_cli_calls': 4,
              'max_typesafe_calls': 1, 'jev_reservation_usd': .02,
              'automatic_retries': 0, 'CPA_calls': 0, 'OpenRouter_calls': 0,
              'claim_ceiling': 'exposed hard-judgment development; not formal ABC qualification'}
    base.save(base.FREEZE, record)
    return record


def verify():
    old = read_record(base.FREEZE)
    require(old == freeze(), 'hard_dev_freeze_changed')
    return old


def run_a():
    verify()
    label = base.HERE.name + '-A-baseline'
    answer, call = base.codex_call(label, (base.HERE / 'A-prompt.txt').read_text(),
                                   arm='A', timeout=90)
    print(json.dumps({'case': base.HERE.name, 'arm': 'A', 'status': call['status'],
                      'answer': bool(answer), 'usage': call['usage']}, ensure_ascii=False))


def run_graph(arm: str, credential_file: Path | None):
    frozen = verify()
    p = packet(arm)
    provider, host = objects(arm, p)
    old = os.environ.get('TYPESAFE_API_KEY')
    if arm == 'C' and credential_file is not None:
        os.environ['TYPESAFE_API_KEY'] = base.credential(credential_file)
    elif arm == 'C':
        require((base.ROOT / 'episodes' / arm).exists(), 'credential_file_required')
    try:
        result = entry.run(base.ROOT / 'episodes' / arm, provider, p, REPO, mode=rc.MODE,
                           executor=host, live_admission=frozen['admissions'][arm])
    finally:
        if old is None:
            os.environ.pop('TYPESAFE_API_KEY', None)
        else:
            os.environ['TYPESAFE_API_KEY'] = old
    base.save(base.ROOT / 'snapshots' / (arm + '-' + digest(result) + '.json'), result)
    (base.ROOT / (arm + '-latest.json')).write_bytes(canonical(result) + b'\n')
    print(json.dumps({'case': base.HERE.name, 'arm': arm, 'status': result.get('status'),
                      'reason': result.get('reason'), 'counts': result.get('counts'),
                      'host_request': result.get('host_request'),
                      'route': result.get('route', {}).get('per_issue') if result.get('route') else None},
                     ensure_ascii=False))


def run_host(arm: str):
    verify()
    prior = json.loads((base.ROOT / (arm + '-latest.json')).read_bytes())
    path = prior.get('host_request')
    require(isinstance(path, str) and path, 'no_pending_host_request')
    handoff = read_record(Path(path))
    require(handoff['role'] == 'execution', 'unexpected_host_role')
    prompt = ('你是当前 Codex 宿主。按照以下已提交范围，实际运用所需方法完成原始分析任务。'
              '不要补造效果、损失、报价或审批权。完成时只返回 JSON：performed_methods 是实际用过的全部方法名，text 是交付正文。'
              '无法在提交范围内完成时返回错误文本，不能伪造完成。\n\n'
              + canonical({'instruction': handoff['instruction'],
                           'request': handoff['request']}).decode() + '\n')
    answer, call = base.codex_call(base.HERE.name + '-' + arm + '-host', prompt,
                                   arm=arm, timeout=min(43, handoff['allowance_seconds']))
    if call['status'] != 'complete' or not answer:
        print(json.dumps({'case': base.HERE.name, 'arm': arm, 'host': call['status'],
                          'submission': 'unrun'}))
        return
    try:
        raw = json.loads(answer)
        require(isinstance(raw, dict) and set(raw) == {'performed_methods', 'text'},
                'invalid_host_reply_shape')
        reply = {**handoff['reply_shape'], 'performed_methods': raw['performed_methods'],
                 'text': raw['text'], 'usage': call['usage']}
        submission = {'schema': 'mindthus.current-host-response.v1',
                      'request_id': handoff['request_id'],
                      'request_sha256': handoff['request_sha256'],
                      'owner_ref': handoff['owner_ref'],
                      'host_context_ref': 'abc-hard-dev-v1:' + base.HERE.name + ':' + arm + ':gpt-6-sol',
                      'elapsed_seconds': call['elapsed_seconds'], 'reply': reply}
        source_ref = submit_response(base.ROOT / 'episodes' / arm, REPO, submission)
        print(json.dumps({'case': base.HERE.name, 'arm': arm, 'host': 'submitted',
                          'receipt': source_ref}, ensure_ascii=False))
    except (ValueError, KeyError, TypeError, ContractError) as exc:
        print(json.dumps({'case': base.HERE.name, 'arm': arm, 'host': 'invalid_reply',
                          'error': type(exc).__name__}))
        return
    run_graph(arm, None)


def fallback(arm: str):
    verify()
    latest = read_record(base.ROOT / (arm + '-latest.json'))
    require(not latest.get('host_request'), 'cannot_fallback_over_pending_handoff')
    answer, call = base.codex_call(base.HERE.name + '-' + arm + '-delegated-host',
                                   (base.HERE / 'A-prompt.txt').read_text(), arm=arm, timeout=90)
    print(json.dumps({'case': base.HERE.name, 'arm': arm, 'delegated_host': call['status'],
                      'answer': bool(answer), 'usage': call['usage']}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('case', choices=IDS)
    parser.add_argument('action', choices=('write-inputs', 'freeze', 'verify', 'A', 'B', 'C',
                                           'B-host', 'C-host', 'B-fallback', 'C-fallback'))
    parser.add_argument('--credential-file', type=Path)
    args = parser.parse_args()
    configure(args.case)
    if args.action == 'write-inputs':
        write_inputs()
    elif args.action == 'freeze':
        print(json.dumps({'case': args.case, 'freeze_digest': digest(freeze()), 'model_calls': 0}))
    elif args.action == 'verify':
        print(json.dumps({'case': args.case, 'freeze_digest': digest(verify()), 'verified': True}))
    elif args.action == 'A':
        run_a()
    elif args.action in ('B', 'C'):
        run_graph(args.action, args.credential_file)
    elif args.action.endswith('-host'):
        run_host(args.action[0])
    else:
        fallback(args.action[0])


if __name__ == '__main__':
    main()
