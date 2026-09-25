"""One isolated source generation call, frozen before inference."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
sys.path.insert(0, str(REPO))
BASE_FILE = HERE.parents[1] / 'abc-current-codex-v1' / 'run.py'
spec = importlib.util.spec_from_file_location('hard_route_cli', BASE_FILE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
from experiments.typed_decision.contracts import digest, require
from experiments.typed_decision.session import read_record, write_once

ROOT = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-hard-route-source-v1')
IDS = ('S1', 'S2', 'S3', 'K1', 'K2', 'K3')
MODEL = 'gpt-6-sol'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def setup():
    base.ROOT = ROOT
    base.MODEL = MODEL
    home = base.home('B')
    home.mkdir(parents=True, exist_ok=True)
    config = home / 'config.toml'
    expected = f'model = "{MODEL}"\n'
    if config.exists():
        require(config.read_text() == expected, 'source_model_changed')
    else:
        config.write_text(expected)
    auth = home / 'auth.json'
    source = Path('/Users/william/.codex/auth.json')
    if not auth.exists():
        auth.symlink_to(source)
    require(auth.resolve() == source.resolve(), 'source_auth_changed')


def identity():
    setup()
    return {'schema': 'mindthus.hard-route-source-v1',
            'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
            'source_files': {x: sha(HERE / x) for x in ('PLAN.md', 'prompt.txt', 'run.py')},
            'base_runner': sha(BASE_FILE), 'root': str(ROOT), 'model': MODEL,
            'ids': list(IDS), 'max_calls': 1, 'automatic_retries': 0,
            'claim_ceiling': 'AI-synthetic new source families; development only'}


def verify():
    old = read_record(ROOT / 'freeze.json')
    expected = identity()
    expected['source_commit'] = old['source_commit']
    require(old == expected, 'source_freeze_changed')
    return old


def run():
    verify()
    answer, outcome = base.codex_call('hard-route-task-source', (HERE / 'prompt.txt').read_text(),
                                      arm='B', timeout=150)
    status = outcome['status']
    if status == 'complete' and answer:
        try:
            obj = json.loads(answer)
            require(set(obj) == {'cases'} and len(obj['cases']) == len(IDS)
                    and [c['id'] for c in obj['cases']] == list(IDS), 'source_ids')
            for case in obj['cases']:
                require(set(case) == {'id', 'user_turn_1', 'user_turn_2', 'given_facts', 'candidate'}
                        and all(isinstance(v, str) and v.strip() for v in case.values()), 'source_shape')
        except (ValueError, TypeError, KeyError):
            status = 'invalid_source_json'
    print(json.dumps({'status': status, 'usage': outcome['usage'],
                      'elapsed_seconds': outcome['elapsed_seconds']}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=('freeze', 'verify', 'run'))
    args = p.parse_args()
    if args.action == 'freeze':
        value = identity()
        write_once(ROOT / 'freeze.json', value)
        print(json.dumps({'freeze': digest(value), 'calls': 0}))
    elif args.action == 'verify':
        print(json.dumps({'freeze': digest(verify()), 'verified': True}))
    else:
        run()
