"""One frozen anonymous quality review, not a new product model dependency."""
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
BASE_FILE = HERE.parent.parent / 'abc-current-codex-v1' / 'run.py'
spec = importlib.util.spec_from_file_location('abc_carrier', BASE_FILE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

from experiments.typed_decision.contracts import digest, require
from experiments.typed_decision.session import read_record, write_once

ROOT = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-paired-blind-review-v1')
MODEL = 'gpt-6-sol'
TIMEOUT = 150


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
        require(config.read_text() == expected, 'review_model_configuration_changed')
    else:
        config.write_text(expected)
    auth = home / 'auth.json'
    source = Path('/Users/william/.codex/auth.json')
    if not auth.exists():
        auth.symlink_to(source)
    require(auth.resolve() == source.resolve(), 'review_auth_binding_changed')
    skills = home / 'skills'
    if skills.exists():
        require({p.name for p in skills.iterdir()} <= {'.system'}, 'review_skill_leak')


def source_files() -> dict:
    return {name: sha(HERE / name) for name in
            ('PLAN.md', 'pairs.json', 'review-schema.json', 'run.py')} | {'base_runner': sha(BASE_FILE)}


def freeze() -> dict:
    profile()
    value = {'schema': 'mindthus.paired-blind-review-freeze.v1',
             'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                      cwd=REPO, text=True).strip(),
             'source_files': source_files(), 'root': str(ROOT), 'model_requested': MODEL,
             'model_service_attestation': 'not_observed', 'timeout_seconds': TIMEOUT,
             'max_codex_calls': 1, 'max_jev_calls': 0, 'automatic_retries': 0,
             'case_ids': ['A1', 'A2', 'F1', 'B3'],
             'claim_ceiling': 'anonymous text review of four exposed development pairs'}
    path = ROOT / 'freeze.json'
    if path.exists():
        require(read_record(path) == value, 'review_freeze_changed')
    else:
        write_once(path, value)
    return value


def verify() -> dict:
    profile()
    old = read_record(ROOT / 'freeze.json')
    require(old['schema'] == 'mindthus.paired-blind-review-freeze.v1'
            and old['source_files'] == source_files() and old['root'] == str(ROOT)
            and old['model_requested'] == MODEL and old['timeout_seconds'] == TIMEOUT
            and old['max_codex_calls'] == 1, 'review_freeze_changed')
    return old


def run() -> None:
    verify()
    pairs = json.loads((HERE / 'pairs.json').read_text())
    prompt = ('你是匿名内容评阅者。只依据给定原任务、事实、必要性质、严重错误和左右两份文本判读。'
              '不得猜左右分别是哪种实验方式。若两边都可用且无实质差异，winner=tie。'
              '每项给出可核对的简短理由；不得调用外部工具。输出严格符合 JSON schema。\n\n'
              + json.dumps(pairs, ensure_ascii=False, sort_keys=True))
    answer, outcome = base.codex_call('blind-quality-review', prompt, arm='B',
                                      timeout=TIMEOUT, schema=HERE / 'review-schema.json')
    status = outcome['status']
    if status == 'complete' and answer:
        try:
            rows = json.loads(answer)['cases']
            require([x['id'] for x in rows] == ['A1', 'A2', 'F1', 'B3'], 'review_ids')
        except (ValueError, KeyError, TypeError):
            status = 'invalid_review_json'
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
