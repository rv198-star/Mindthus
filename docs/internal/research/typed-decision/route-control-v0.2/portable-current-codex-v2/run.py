"""Successor: freeze beside, never inside, the bound Episode root."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))
BASE_FILE = HERE.parent / 'portable-current-codex-v1' / 'run.py'
spec = importlib.util.spec_from_file_location('portable_current_codex_v1', BASE_FILE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

from experiments.typed_decision import entry, route_control as rc
from experiments.typed_decision.contracts import canonical, digest, require
from experiments.typed_decision.current_host import submit_response
from experiments.typed_decision.session import read_record, write_once


def freeze_path(root: Path) -> Path:
    return root.with_name(root.name + '-freeze.json')


def identity(root: Path) -> dict:
    value = base.identity(root)
    value.update(schema='mindthus.portable-current-codex-successor-freeze.v1',
                 parent='portable-current-codex-v1:pre_request_root_error',
                 source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                       cwd=REPO, text=True).strip())
    value['source_files'].update({'successor_PLAN.md': base.sha(HERE / 'PLAN.md'),
                                  'successor_run.py': base.sha(HERE / 'run.py')})
    return value


def freeze(root: Path) -> dict:
    root.parent.mkdir(parents=True, exist_ok=True)
    require(not root.exists() or not any(root.iterdir()), 'new_episode_root_must_be_empty')
    value = identity(root)
    path = freeze_path(root)
    if path.exists():
        require(read_record(path) == value, 'successor_freeze_changed')
    else:
        write_once(path, value)
    return value


def verify(root: Path) -> dict:
    frozen = read_record(freeze_path(root))
    expected = identity(root)
    expected['source_commit'] = frozen['source_commit']
    require(frozen == expected, 'successor_freeze_changed')
    return frozen


def run(root: Path, credential_file: Path | None) -> dict:
    frozen = verify(root)
    require(not os.environ.get('MINDTHUS_HOST_API_KEY') and
            not os.environ.get('OPENROUTER_API_KEY'), 'forbidden_provider_present')
    old = os.environ.get('TYPESAFE_API_KEY')
    if credential_file:
        os.environ['TYPESAFE_API_KEY'] = base.credential(credential_file)
    try:
        provider, host = base.objects()
        result = entry.run(root, provider, base.packet(), REPO, mode=rc.MODE,
                           executor=host, live_admission=frozen['admission'])
    finally:
        if old is None:
            os.environ.pop('TYPESAFE_API_KEY', None)
        else:
            os.environ['TYPESAFE_API_KEY'] = old
    root.with_name(root.name + '-latest.json').write_bytes(canonical(result) + b'\n')
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('freeze', 'verify', 'run', 'submit'))
    parser.add_argument('--state-root', type=Path, required=True)
    parser.add_argument('--credential-file', type=Path)
    parser.add_argument('--host-response', type=Path)
    args = parser.parse_args()
    root = args.state_root.resolve()
    if args.action == 'freeze':
        print(json.dumps({'freeze': digest(freeze(root)), 'model_calls': 0}))
        return
    verify(root)
    if args.action == 'verify':
        print(json.dumps({'verified': True, 'freeze': digest(read_record(freeze_path(root)))}))
        return
    if args.action == 'submit':
        require(args.host_response is not None, 'host_response_required')
        receipt = submit_response(root, REPO, json.loads(args.host_response.read_bytes()))
        print(json.dumps({'receipt': receipt}))
        return
    result = run(root, args.credential_file)
    print(json.dumps({'status': result.get('status'), 'reason': result.get('reason'),
                      'counts': result.get('counts'), 'host_request': result.get('host_request'),
                      'route': result.get('route', {}).get('per_issue') if result.get('route') else None},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
