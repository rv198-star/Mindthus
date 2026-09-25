"""Three case-local A/B/C holdout arms on the existing route-control entry."""
from __future__ import annotations

import argparse
import hashlib
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
PARENT = HERE.parent / 'abc-current-codex-v2' / 'run.py'
spec = importlib.util.spec_from_file_location('abc_v2_carrier', PARENT)
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)
base = v2.base

from experiments.typed_decision import entry, route_control as rc
from experiments.typed_decision.contracts import (
    BatchResult, ContractError, DecisionResult, ResolvedRuntime, ServingIdentity,
    canonical, digest, provider_configuration, require,
)
from experiments.typed_decision.current_host import CurrentAgentHost, submit_response
from experiments.typed_decision.providers import ProviderError, TypeSafeJevProvider
from experiments.typed_decision.relationship_live import deadline_post_json
from experiments.typed_decision.session import implementation_digest, read_record

IDS = ('HB', 'HC', 'HD')
EXTERNAL = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-formal-abc-v1')
SOURCE = HERE.parent / 'formal-holdout-source-v1' / 'evidence-20260925' / 'records' / 'codex-calls' / 'holdout-task-source' / 'last-message.txt'
AUTH = 'Owner directed completing #211 local tests, 2026-09-25; no CPA/OpenRouter'
INPUT_FILES = ('cases.json', 'A-prompt.txt', 'host-task-prompt.txt',
               'B-judge-prompt.txt', 'B-judge-schema.json')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configure(cid: str) -> None:
    require(cid in IDS, 'unknown_holdout_case')
    v2.HERE = HERE
    v2.EXTERNAL = EXTERNAL
    v2.IDS = IDS
    v2.AUTH = AUTH
    v2.FROZEN_FILES = INPUT_FILES
    v2.configure(cid)


def profile() -> dict:
    skill_files = {str(p.relative_to(REPO / 'skills')): sha(p)
                   for p in (REPO / 'skills').rglob('*') if p.is_file()}
    for arm in ('A', 'B'):
        home = base.home(arm)
        home.mkdir(parents=True, exist_ok=True)
        config = home / 'config.toml'
        expected = f'model = "{base.MODEL}"\n'
        if config.exists():
            require(config.read_text() == expected, 'formal_model_configuration_changed')
        else:
            config.write_text(expected)
        auth = home / 'auth.json'
        source = Path('/Users/william/.codex/auth.json')
        if not auth.exists():
            auth.symlink_to(source)
        require(auth.resolve() == source.resolve(), 'formal_auth_binding_changed')
    skill_home = base.home('A') / 'skills'
    if not skill_home.exists():
        shutil.copytree(REPO / 'skills', skill_home, symlinks=False)
    for name, value in skill_files.items():
        require(sha(skill_home / name) == value, 'A_native_skill_changed')
    other = base.home('B') / 'skills'
    if other.exists():
        require({p.name for p in other.iterdir()} <= {'.system'}, 'B_C_skill_leak')
    return skill_files


class OrdinaryProvider(v2.OrdinaryCodexProvider):
    serving_identity = ServingIdentity('codex_cli', 'exec-json-schema-v1', base.MODEL,
                                       'local://codex-exec', 'formal-abc-v1')

    def evaluate(self, specs, context, timeout):
        compiled, _ = v2.compile_case()
        if ([s.to_dict() for s in specs] == [s.to_dict() for s in compiled.specs]
                and context == compiled.context):
            return super().evaluate(specs, context, timeout)
        # A post-artifact batch is determined by the accepted artifact, not known at freeze.
        questions = {s.id: {'kind': s.kind, 'question': s.question, 'criteria': s.criteria}
                     for s in specs}
        prompt = v2.PROMPT_PREFIX + '\n\n' + canonical({'state': context,
                                                        'questions': questions}).decode() + '\n'
        schema = v2.make_schema(specs)
        directory = base.ROOT / 'post-artifact-inputs'
        directory.mkdir(parents=True, exist_ok=True)
        key = digest([s.to_dict() for s in specs])
        prompt_file, schema_file = directory / (key + '-prompt.txt'), directory / (key + '-schema.json')
        if prompt_file.exists():
            require(prompt_file.read_text() == prompt, 'post_artifact_prompt_changed')
        else:
            prompt_file.write_text(prompt)
        encoded = json.dumps(schema, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
        if schema_file.exists():
            require(schema_file.read_text() == encoded, 'post_artifact_schema_changed')
        else:
            schema_file.write_text(encoded)
        answer, call = base.codex_call(base.HERE.name + '-B-post-' + key[:12], prompt,
                                       arm='B', timeout=min(timeout, 44), schema=schema_file)
        self.receipt = {'call_label': base.HERE.name + '-B-post-' + key[:12],
                        'last_sha256': call['last_sha256'], 'events_sha256': call['events_sha256'],
                        'validated_usage': call['usage'], 'model_service_attestation': 'not_observed'}
        if call['status'] != 'complete' or not answer:
            raise ProviderError('codex_post_' + call['status'])
        try:
            raw = json.loads(answer)
            require(set(raw) == {'answers'} and set(raw['answers']) == {s.id for s in specs},
                    'post_answers_shape')
            results = {}
            for s in specs:
                item = raw['answers'][s.id]
                row = DecisionResult(item['status'], item['value'], None,
                                     'ordinary_llm_subjective_value_not_calibrated')
                row.validate(s)
                results[s.id] = row
        except (ValueError, KeyError, TypeError, ContractError):
            raise ProviderError('invalid_post_answers') from None
        return BatchResult(results, ResolvedRuntime(base.MODEL, 'codex-cli-configured-model'),
                           call['usage'])


def objects(arm: str, packet: dict):
    provider = OrdinaryProvider() if arm == 'B' else TypeSafeJevProvider(
        model='jev-1.13.0', choice_rounding=True, transport=deadline_post_json)
    return provider, CurrentAgentHost(packet['authority']['owner_ref'])


class Acceptor:
    def __init__(self, root: Path, owner: str, arm: str):
        self.root, self.identity = root, owner
        self.configuration = {'kind': 'current-agent-source-checked-acceptance.v1',
                              'case_id': 'HD', 'arm': arm, 'owner': owner}

    def accept(self, edge, artifact, packet):
        path = self.root / 'host-acceptance' / (edge['id'] + '.json')
        if path.exists():
            value = json.loads(path.read_bytes())
            require(value['artifact_sha256'] == artifact['artifact_sha256']
                    and value['owner_ref'] == self.identity, 'formal_acceptance_changed')
            return value
        return {'owner_ref': self.identity, 'dependency_id': edge['id'],
                'artifact_sha256': artifact['artifact_sha256'],
                'accepted': False, 'reason': 'Original host has not accepted the candidate set'}


def admission(arm: str, packet: dict, bundle: dict):
    provider, host = objects(arm, packet)
    extra = 1 if base.HERE.name == 'HD' else 0
    a = {'schema': 'mindthus.route-control-live.v1', 'mode': rc.MODE,
         'root': str(base.ROOT / 'episodes' / arm),
         'implementation': implementation_digest(),
         'source_bindings': bundle['sources'], 'provider': provider_configuration(provider),
         'packet_hashes': [digest(packet)], 'authorization_ref': AUTH,
         'ceilings': {'judgments': 1 + extra, 'corrections': 0, 'organize': 0,
                      'arbitrations': 0, 'executions': 1 + extra, 'requests': 1 + extra,
                      'reserve_per_jev_usd': .02},
         'executor': host.configuration, 'arbitrator': None,
         'corrector': None, 'organizer': None}
    rc._admission(a, base.ROOT / 'episodes' / arm, packet, provider, bundle,
                  {'executor': host, 'arbitrator': None, 'corrector': None, 'organizer': None})
    return a


def identity() -> dict:
    skill_files = profile()
    compiled, bundle = v2.compile_case()
    require((base.HERE / 'B-judge-prompt.txt').read_text() == v2.question_prompt(compiled)
            and json.loads((base.HERE / 'B-judge-schema.json').read_text()) ==
            v2.make_schema(compiled.specs), 'B_question_contract_changed')
    identities, admissions = {}, {}
    for arm in ('B', 'C'):
        p = v2.packet(arm)
        c, _ = v2.compile_case(arm)
        identities[arm] = {'packet': digest(p),
                           'questions': digest([s.to_dict() for s in c.specs]),
                           'context': digest(c.context)}
        admissions[arm] = admission(arm, p, bundle)
    return {'schema': 'mindthus.formal-abc-three-family-freeze.v1',
            'case_id': base.HERE.name,
            'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                     cwd=REPO, text=True).strip(),
            'implementation': implementation_digest(),
            'source_files': {'PLAN.md': sha(HERE / 'PLAN.md'),
                             'host-schema.json': sha(HERE / 'host-schema.json'),
                             'run.py': sha(HERE / 'run.py'),
                             'parent_runner': sha(PARENT),
                             'base_runner': sha(v2.BASE_FILE),
                             'holdout_source': sha(SOURCE),
                             **{name: sha(base.HERE / name) for name in INPUT_FILES}},
            'skills': skill_files, 'source_bindings': bundle['sources'],
            'identities': identities, 'admissions': admissions,
            'root': str(base.ROOT), 'model_requested': base.MODEL,
            'jev_model': 'jev-1.13.0', 'max_jev_calls': 2 if base.HERE.name == 'HD' else 1,
            'reserve_per_jev_usd': .02, 'automatic_retries': 0,
            'CPA_calls': 0, 'OpenRouter_calls': 0,
            'claim_ceiling': 'AI-synthetic B/C/D holdout only; monetary cost unknown means no cost pass'}


def freeze() -> dict:
    value = identity()
    base.save(base.FREEZE, value)
    return value


def verify() -> dict:
    old = read_record(base.FREEZE)
    expected = identity()
    expected['source_commit'] = old['source_commit']
    require(old == expected, 'formal_abc_freeze_changed')
    return old


def run_a() -> None:
    verify()
    answer, call = base.codex_call(base.HERE.name + '-A-native',
                                   (base.HERE / 'A-prompt.txt').read_text(),
                                   arm='A', timeout=120)
    print(json.dumps({'case': base.HERE.name, 'arm': 'A', 'status': call['status'],
                      'answer': bool(answer), 'usage': call['usage']}, ensure_ascii=False))


def run_graph(arm: str, credential_file: Path | None = None) -> dict:
    frozen = verify()
    p = v2.packet(arm)
    provider, host = objects(arm, p)
    old = os.environ.get('TYPESAFE_API_KEY')
    if arm == 'C' and credential_file is not None:
        os.environ['TYPESAFE_API_KEY'] = base.credential(credential_file)
    elif arm == 'C':
        require((base.ROOT / 'episodes' / arm).exists(), 'credential_file_required')
    try:
        result = entry.run(base.ROOT / 'episodes' / arm, provider, p, REPO,
                           mode=rc.MODE, executor=host,
                           live_admission=frozen['admissions'][arm],
                           artifact_acceptor=Acceptor(base.ROOT / 'episodes' / arm,
                                                      p['authority']['owner_ref'], arm)
                           if base.HERE.name == 'HD' else None)
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
    return result


def run_host(arm: str) -> None:
    verify()
    latest = read_record(base.ROOT / (arm + '-latest.json'))
    path = latest.get('host_request')
    require(isinstance(path, str) and path, 'no_pending_host_request')
    handoff = read_record(Path(path))
    require(handoff['role'] == 'execution', 'unexpected_host_role')
    issue = handoff['request']['issue']['issue_id']
    prompt = ('你是当前 Codex 宿主。按已提交范围和加载的方法完成原任务，只返回 JSON：'
              'performed_methods 为实际用过的全部方法名，text 为可交付正文。'
              '不得编造缺失事实或权限；无法完成时不得伪造。\n\n'
              + canonical({'instruction': handoff['instruction'],
                           'request': handoff['request']}).decode() + '\n')
    answer, call = base.codex_call(base.HERE.name + '-' + arm + '-host-' + issue,
                                   prompt, arm=arm,
                                   timeout=min(43, handoff['allowance_seconds']),
                                   schema=HERE / 'host-schema.json')
    if call['status'] != 'complete' or not answer:
        print(json.dumps({'case': base.HERE.name, 'arm': arm, 'host': call['status']}))
        return
    try:
        raw = json.loads(answer)
        require(set(raw) == {'performed_methods', 'text'}, 'host_reply_shape')
        reply = {**handoff['reply_shape'], 'performed_methods': raw['performed_methods'],
                 'text': raw['text'], 'usage': call['usage']}
        submission = {'schema': 'mindthus.current-host-response.v1',
                      'request_id': handoff['request_id'],
                      'request_sha256': handoff['request_sha256'],
                      'owner_ref': handoff['owner_ref'],
                      'host_context_ref': 'formal-abc-v1:' + base.HERE.name + ':' + arm + ':' + issue,
                      'elapsed_seconds': call['elapsed_seconds'], 'reply': reply}
        receipt = submit_response(base.ROOT / 'episodes' / arm, REPO, submission)
        print(json.dumps({'case': base.HERE.name, 'arm': arm,
                          'host': 'submitted', 'receipt': receipt}, ensure_ascii=False))
    except (ValueError, KeyError, TypeError, ContractError) as exc:
        print(json.dumps({'case': base.HERE.name, 'arm': arm,
                          'host': 'invalid_reply', 'error': type(exc).__name__}))
        return
    run_graph(arm)


def fallback(arm: str) -> None:
    verify()
    latest = read_record(base.ROOT / (arm + '-latest.json'))
    require(not latest.get('host_request'), 'cannot_fallback_over_pending_handoff')
    answer, call = base.codex_call(base.HERE.name + '-' + arm + '-delegated-host',
                                   (base.HERE / 'host-task-prompt.txt').read_text(),
                                   arm=arm, timeout=120)
    print(json.dumps({'case': base.HERE.name, 'arm': arm,
                      'delegated_host': call['status'], 'answer': bool(answer),
                      'usage': call['usage']}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('case', choices=IDS)
    parser.add_argument('action', choices=('write-inputs', 'freeze', 'verify', 'A', 'B', 'C',
                                           'B-host', 'C-host', 'B-fallback', 'C-fallback'))
    parser.add_argument('--credential-file', type=Path)
    args = parser.parse_args()
    configure(args.case)
    if args.action == 'write-inputs':
        v2.write_inputs()
    elif args.action == 'freeze':
        print(json.dumps({'case': args.case, 'freeze': digest(freeze()), 'model_calls': 0}))
    elif args.action == 'verify':
        print(json.dumps({'case': args.case, 'freeze': digest(verify()), 'verified': True}))
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
