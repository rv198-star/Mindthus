"""One successor advisory call; original B3 Jev/host records remain immutable."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))

BASE_FILE = HERE.parent / 'abc-current-codex-v1' / 'run.py'
OLD = HERE.parent / 'paired-current-codex-v1'
spec = importlib.util.spec_from_file_location('abc_v1_carrier', BASE_FILE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

from experiments.typed_decision.contracts import digest, require
from experiments.typed_decision.session import read_record

ROOT = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-paired-current-codex-v2')
FREEZE = ROOT / 'freeze.json'
TIMEOUT = 120
MODEL = 'gpt-6-sol'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configure() -> None:
    base.ROOT = ROOT
    base.MODEL = MODEL


def sources() -> dict:
    binding = json.loads((OLD / 'bindings.json').read_bytes())
    result = {'parent_bindings': sha(OLD / 'bindings.json'),
              'parent_plan': sha(OLD / 'PLAN.md'),
              'parent_advisory_prompt': sha(OLD / 'advisory-prompt.txt'),
              'parent_advisory_outcome': sha(OLD / 'evidence-20260924' / 'records' /
                                             'codex-calls' / 'B3-advisory' / 'outcome.json')}
    require(result['parent_advisory_prompt'] == binding['prompt_sha256'],
            'advisory_prompt_changed')
    for name in ('source_handoff', 'source_provider_receipt', 'committed_host_last'):
        path = Path(binding[name + '_path'])
        require(sha(path) == binding[name + '_sha256'], name + '_changed')
        result[name] = binding[name + '_sha256']
    return result


def profile() -> None:
    configure()
    home = base.home('B')
    home.mkdir(parents=True, exist_ok=True)
    config = home / 'config.toml'
    expected = f'model = "{MODEL}"\n'
    if config.exists():
        require(config.read_text() == expected, 'codex_model_configuration_changed')
    else:
        config.write_text(expected)
    auth = home / 'auth.json'
    source = Path('/Users/william/.codex/auth.json')
    if not auth.exists():
        auth.symlink_to(source)
    require(auth.resolve() == source.resolve(), 'codex_auth_binding_changed')


def frozen_value() -> dict:
    return {'schema': 'mindthus.paired-current-codex-successor-freeze.v1',
            'parent': 'paired-current-codex-v1',
            'source_commit': subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
            'source_files': {'PLAN.md': sha(HERE / 'PLAN.md'),
                             'run.py': sha(HERE / 'run.py'),
                             'base_runner': sha(BASE_FILE)},
            'parent_sources': sources(), 'root': str(ROOT),
            'requested_model': MODEL, 'model_service_attestation': 'not_observed',
            'timeout_seconds': TIMEOUT, 'max_codex_calls': 1, 'max_jev_calls': 0,
            'automatic_retries': 0, 'comparison': 'B3 exposed development ①/② only'}


def freeze() -> dict:
    profile()
    value = frozen_value()
    base.save(FREEZE, value)
    return value


def verify() -> dict:
    profile()
    old = read_record(FREEZE)
    require(old['schema'] == 'mindthus.paired-current-codex-successor-freeze.v1'
            and old['root'] == str(ROOT) and old['requested_model'] == MODEL
            and old['timeout_seconds'] == TIMEOUT and old['max_codex_calls'] == 1
            and old['max_jev_calls'] == 0, 'successor_freeze_identity_changed')
    require(old['source_files'] == {'PLAN.md': sha(HERE / 'PLAN.md'),
                                    'run.py': sha(HERE / 'run.py'),
                                    'base_runner': sha(BASE_FILE)}
            and old['parent_sources'] == sources(), 'successor_sources_changed')
    return old


def run() -> None:
    verify()
    prompt = (OLD / 'advisory-prompt.txt').read_text()
    answer, call = base.codex_call('B3-advisory-successor', prompt, arm='B', timeout=TIMEOUT)
    print(json.dumps({'status': call['status'], 'exit_code': call['exit_code'],
                      'answer': bool(answer), 'elapsed_seconds': call['elapsed_seconds'],
                      'usage': call['usage']}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('freeze', 'verify', 'run'))
    args = parser.parse_args()
    if args.action == 'freeze':
        print(json.dumps({'freeze': digest(freeze()), 'model_calls': 0}))
    elif args.action == 'verify':
        print(json.dumps({'freeze': digest(verify()), 'verified': True}))
    else:
        run()


if __name__ == '__main__':
    main()
