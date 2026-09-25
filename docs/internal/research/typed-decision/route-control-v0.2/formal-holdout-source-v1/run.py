"""One isolated source request for three untouched B/C/D holdout tasks."""
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
spec = importlib.util.spec_from_file_location('abc_carrier', BASE_FILE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

from experiments.typed_decision.contracts import digest, require
from experiments.typed_decision.session import read_record, write_once

ROOT = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-formal-holdout-source-v1')
MODEL = 'gpt-6-sol'
TIMEOUT = 150
IDS = ('HB', 'HC', 'HD')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def profile() -> None:
    base.ROOT = ROOT
    base.MODEL = MODEL
    home = base.home('B')
    home.mkdir(parents=True, exist_ok=True)
    config = home / 'config.toml'
    expected = f'model = "{MODEL}"\n'
    if config.exists():
        require(config.read_text() == expected, 'holdout_model_changed')
    else:
        config.write_text(expected)
    auth = home / 'auth.json'
    source = Path('/Users/william/.codex/auth.json')
    if not auth.exists():
        auth.symlink_to(source)
    require(auth.resolve() == source.resolve(), 'holdout_auth_binding_changed')
    skills = home / 'skills'
    if skills.exists():
        require({p.name for p in skills.iterdir()} <= {'.system'}, 'holdout_skill_leak')


def sources() -> dict:
    return {name: sha(HERE / name) for name in ('PLAN.md', 'prompt.txt', 'run.py')} | {
        'base_runner': sha(BASE_FILE)}


def freeze() -> dict:
    profile()
    value = {'schema': 'mindthus.formal-holdout-source-freeze.v1',
             'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                      cwd=REPO, text=True).strip(),
             'source_files': sources(), 'root': str(ROOT), 'model_requested': MODEL,
             'model_service_attestation': 'not_observed', 'timeout_seconds': TIMEOUT,
             'max_codex_calls': 1, 'automatic_retries': 0, 'max_jev_calls': 0,
             'candidate_ids': list(IDS), 'claim_ceiling': 'AI-synthetic untouched task source'}
    path = ROOT / 'freeze.json'
    if path.exists():
        require(read_record(path) == value, 'holdout_source_freeze_changed')
    else:
        write_once(path, value)
    return value


def verify() -> dict:
    profile()
    old = read_record(ROOT / 'freeze.json')
    require(old['schema'] == 'mindthus.formal-holdout-source-freeze.v1'
            and old['source_files'] == sources() and old['root'] == str(ROOT)
            and old['model_requested'] == MODEL and old['candidate_ids'] == list(IDS)
            and old['max_codex_calls'] == 1 and old['max_jev_calls'] == 0,
            'holdout_source_freeze_changed')
    return old


def run() -> None:
    verify()
    answer, outcome = base.codex_call('holdout-task-source', (HERE / 'prompt.txt').read_text(),
                                      arm='B', timeout=TIMEOUT)
    status = outcome['status']
    if status == 'complete' and answer:
        try:
            obj = json.loads(answer)
            require(set(obj) == {'cases'} and len(obj['cases']) == 3
                    and [x.get('id') for x in obj['cases']] == list(IDS),
                    'holdout_case_ids')
            for x in obj['cases']:
                require(set(x) == {'id', 'user_request', 'given_facts'}
                        and all(isinstance(x[k], str) and x[k].strip()
                                for k in ('user_request', 'given_facts')),
                        'holdout_case_shape')
        except (ValueError, TypeError, AttributeError):
            status = 'invalid_holdout_json'
    print(json.dumps({'status': status, 'exit_code': outcome['exit_code'],
                      'elapsed_seconds': outcome['elapsed_seconds'],
                      'usage': outcome['usage']}, ensure_ascii=False))


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
