"""v3.2 successor: deliver the concrete Jev finding to the constrained host."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_observation_v3 as base
import run_observation_v3_host_consumption as parent

from experiments.typed_decision import observation_assessment as obs
from experiments.typed_decision.contracts import require
from experiments.typed_decision.session import implementation_digest, read_record

ROOT = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-source-direct-v3-host-consumption-v2')
parent.ROOT = ROOT


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_commit() -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=base.REPO,
                                   text=True).strip()


def binding() -> dict:
    return {
        'schema': 'mindthus.source-direct-v3-host-consumption-v2-binding.v1',
        'source_commit': source_commit(), 'implementation': implementation_digest(),
        'runner_sha256': sha(Path(__file__)), 'parent_runner_sha256': sha(Path(parent.__file__)),
        'root': str(ROOT), 'consumption_policy': obs.CONSUMPTION_POLICY,
        'required_finding_fields': ['check_id', 'value', 'meaning', 'target_ref',
                                    'target_version', 'state_sha256'],
        'predecessor_host_freeze_sha256': sha(Path(
            '/Users/william/Documents/Codex/2026-09-25/'
            'mindthus-source-direct-v3-host-consumption-v1/host-freeze.json')),
        'purpose': ('Successor after independent review found v3.1 sent only a generic remedy. '
                    'v3.2 sends the candidate-bound Jev classification and meaning.'),
    }


def ensure_binding(create: bool = False) -> None:
    path = ROOT / 'successor-binding.json'
    value = binding()
    if create:
        base.save(path, value)
    else:
        require(path.exists() and read_record(path) == value,
                'host_consumption_v2_binding_changed')


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('freeze-host')
    host = sub.add_parser('host'); host.add_argument('--scenario', choices=parent.SCENARIOS,
                                                     required=True)
    sub.add_parser('freeze-recheck')
    recheck = sub.add_parser('recheck'); recheck.add_argument('--scenario',
                                                               choices=parent.SCENARIOS,
                                                               required=True)
    sub.add_parser('report')
    args = parser.parse_args()
    if args.command == 'freeze-host':
        ensure_binding(create=True)
        parent.freeze_host()
    else:
        ensure_binding()
        if args.command == 'host': parent.run_host(args.scenario)
        elif args.command == 'freeze-recheck': parent.freeze_recheck()
        elif args.command == 'recheck': parent.run_recheck(args.scenario)
        else: parent.report()


if __name__ == '__main__':
    main()
