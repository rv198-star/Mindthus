"""One frozen current-Codex advisory consumption of an existing Jev observation."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))
BASE_FILE = HERE.parent / 'abc-current-codex-v1' / 'run.py'
spec = importlib.util.spec_from_file_location('abc_v1_carrier', BASE_FILE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
from experiments.typed_decision.contracts import digest, require
from experiments.typed_decision.session import read_record

ROOT = Path('/Users/william/Documents/Codex/2026-09-24/mindthus-paired-current-codex-v1')
FREEZE = ROOT / 'freeze.json'
FILES = ('PLAN.md', 'advisory-prompt.txt', 'bindings.json', 'run.py')


def configure():
    base.HERE = HERE
    base.ROOT = ROOT


def prepare():
    configure()
    binding = json.loads((HERE / 'bindings.json').read_text())
    require(base.sha(HERE / 'advisory-prompt.txt') == binding['prompt_sha256'], 'prompt_changed')
    for kind in ('source_handoff', 'source_provider_receipt', 'committed_host_last'):
        require(base.sha(Path(binding[kind + '_path'])) == binding[kind + '_sha256'],
                kind + '_changed')
    home = base.home('B')
    home.mkdir(parents=True, exist_ok=True)
    config = home / 'config.toml'
    if config.exists():
        require(config.read_text() == 'model = "gpt-6-sol"\n', 'model_config_changed')
    else:
        config.write_text('model = "gpt-6-sol"\n')
    auth = home / 'auth.json'
    if not auth.exists():
        auth.symlink_to(Path('/Users/william/.codex/auth.json'))
    require(auth.resolve() == Path('/Users/william/.codex/auth.json').resolve(), 'auth_binding_changed')
    record = {'schema': 'mindthus.paired-current-codex-development-freeze.v1',
              'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                       cwd=REPO, text=True).strip(),
              'files': {name: base.sha(HERE / name) for name in FILES},
              'source_hashes': binding, 'root': str(ROOT),
              'model_requested': 'gpt-6-sol', 'model_service_attestation': 'not_observed',
              'max_codex_calls': 1, 'max_jev_calls': 0, 'timeout_seconds': 43,
              'automatic_retries': 0, 'claim_ceiling': 'one exposed same-host-development pair'}
    base.save(FREEZE, record)
    return record


def verify():
    old = read_record(FREEZE)
    current = prepare()
    require(old == current, 'paired_freeze_changed')
    return old


def run():
    verify()
    answer, call = base.codex_call('B3-advisory', (HERE / 'advisory-prompt.txt').read_text(),
                                   arm='B', timeout=43)
    print(json.dumps({'status': call['status'], 'answer': bool(answer),
                      'usage': call['usage']}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('freeze', 'verify', 'run'))
    args = parser.parse_args()
    if args.action == 'freeze':
        print(json.dumps({'freeze': digest(prepare()), 'model_calls': 0}))
    elif args.action == 'verify':
        print(json.dumps({'freeze': digest(verify()), 'verified': True}))
    else:
        run()


if __name__ == '__main__':
    main()
