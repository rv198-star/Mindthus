"""One isolated Codex request for candidate tasks; no tested-arm inference."""
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
spec = importlib.util.spec_from_file_location('abc_v1_carrier', BASE_FILE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

from experiments.typed_decision.contracts import digest, require
from experiments.typed_decision.session import read_record

ROOT = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-holdout-candidate-source-v1')
FREEZE = ROOT / 'freeze.json'
MODEL = 'gpt-6-sol'
TIMEOUT = 120
IDS = ('A1', 'A2', 'B1', 'C1', 'D1', 'E1', 'E2', 'F1', 'F2')


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
        require(config.read_text() == expected, 'candidate_model_configuration_changed')
    else:
        config.write_text(expected)
    auth = home / 'auth.json'
    source = Path('/Users/william/.codex/auth.json')
    if not auth.exists():
        auth.symlink_to(source)
    require(auth.resolve() == source.resolve(), 'candidate_auth_binding_changed')
    skills = home / 'skills'
    if skills.exists():
        require({p.name for p in skills.iterdir()} <= {'.system'},
                'candidate_mindthus_skill_leak')


def source_files() -> dict:
    return {name: sha(HERE / name) for name in ('PLAN.md', 'prompt.txt', 'run.py')} | {
        'base_runner': sha(BASE_FILE)}


def freeze() -> dict:
    profile()
    value = {'schema': 'mindthus.holdout-candidate-source-freeze.v1',
             'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                      cwd=REPO, text=True).strip(),
             'source_files': source_files(), 'root': str(ROOT),
             'model_requested': MODEL, 'model_service_attestation': 'not_observed',
             'max_codex_calls': 1, 'timeout_seconds': TIMEOUT,
             'max_jev_calls': 0, 'automatic_retries': 0,
             'candidate_ids': list(IDS), 'claim_ceiling': 'candidate inputs only'}
    base.save(FREEZE, value)
    return value


def verify() -> dict:
    profile()
    old = read_record(FREEZE)
    require(old['schema'] == 'mindthus.holdout-candidate-source-freeze.v1'
            and old['source_files'] == source_files()
            and old['root'] == str(ROOT) and old['model_requested'] == MODEL
            and old['candidate_ids'] == list(IDS) and old['max_codex_calls'] == 1
            and old['timeout_seconds'] == TIMEOUT and old['max_jev_calls'] == 0,
            'candidate_freeze_changed')
    return old


def run() -> None:
    verify()
    answer, outcome = base.codex_call('task-candidates', (HERE / 'prompt.txt').read_text(),
                                      arm='B', timeout=TIMEOUT)
    status = outcome['status']
    if status == 'complete' and answer:
        try:
            obj = json.loads(answer)
            require(isinstance(obj, dict) and set(obj) == {'cases'} and
                    isinstance(obj['cases'], list) and len(obj['cases']) == len(IDS),
                    'candidate_json_shape')
            require([x.get('id') for x in obj['cases']] == list(IDS), 'candidate_ids_changed')
            for row in obj['cases']:
                require(set(row) == {'id', 'user_request', 'given_facts'} and
                        all(isinstance(row[k], str) and row[k].strip()
                            for k in ('user_request', 'given_facts')), 'candidate_item_shape')
        except (ValueError, TypeError, AttributeError):
            status = 'invalid_candidate_json'
    print(json.dumps({'status': status, 'exit_code': outcome['exit_code'],
                      'answer': bool(answer), 'elapsed_seconds': outcome['elapsed_seconds'],
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
