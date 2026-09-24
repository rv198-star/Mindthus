"""Local Codex carrier for the frozen R1 cases; never mutates the OCI freeze."""
from pathlib import Path
import argparse
import importlib.util
import io
import json
import os
import stat
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path('/Users/william/Documents/Codex/2026-09-24/mindthus-six-scenes-r1-local')
EPISODES = ROOT / 'episodes'
FREEZE = ROOT / 'freeze.json'
PARENT_FREEZE = HERE / 'freeze.json'

spec = importlib.util.spec_from_file_location('scoped_repair_r1_runner', HERE / 'run.py')
r1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r1)
r1.base.ROOT = EPISODES
r1.base.FREEZE = FREEZE
r1.base.AUTH = 'Owner requested local Codex takeover of #211 and bounded B1/C1/D1-R1; 2026-09-24'
r1.base.CONTEXT = 'current-local-Codex-conversation-20260924-shared-not-independent'


def credential(path: Path) -> str:
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise ValueError('credential file must not be group/world readable')
    values = {}
    for line in path.read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key, value = line.split('=', 1)
            values[key.strip()] = value.strip().strip('"\'')
    key = values.get('TYPESAFE_API_KEY', '')
    if not key:
        raise ValueError('TYPESAFE_API_KEY absent')
    return key


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'verify', 'run'))
    parser.add_argument('ids', nargs='*')
    parser.add_argument('--credential-file', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        if args.ids or args.credential_file:
            parser.error('prepare takes no cases or credential')
        ROOT.mkdir(parents=True, exist_ok=True)
        r1.prepare()
    elif args.action == 'verify':
        if args.ids or args.credential_file:
            parser.error('verify takes no cases or credential')
        print(json.dumps({'verified': True, 'freeze': r1.digest(r1.verify()),
                          'parent_freeze': r1.base.filesha(PARENT_FREEZE)}))
    else:
        ids = args.ids or ['B1', 'C1', 'D1']
        if not set(ids) <= {'B1', 'C1', 'D1'} or len(set(ids)) != len(ids):
            parser.error('only unique B1/C1/D1 cases are allowed')
        r1.verify()
        if args.credential_file:
            sys.stdin = io.StringIO(credential(args.credential_file) + '\n')
        else:
            sys.stdin = io.StringIO('\n')
        if os.environ.get('OPENROUTER_API_KEY') or os.environ.get('MINDTHUS_HOST_API_KEY'):
            raise ValueError('non-TypeSafe model credential is present')
        r1.base.execute(ids)


if __name__ == '__main__':
    main()
