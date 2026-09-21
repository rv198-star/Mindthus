"""Run the isolated, offline C01 probe; never calls a paid inference API."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from . import c01
from .contracts import ContractError
from .providers import FixtureProvider
from .session import Limits, RecoveryRequired, Session
from .trace import from_c01, validate_with_existing


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['c01'])
    parser.add_argument('--fixture', type=Path, default=Path(__file__).parent / 'fixtures/c01-sra.json')
    parser.add_argument('--state-root', type=Path, required=True, help='local trial directory outside source')
    parser.add_argument('--scope', default='offline-c01-v1')
    parser.add_argument('--read-selected-method', action='store_true')
    args = parser.parse_args(argv)
    repo = Path(__file__).resolve().parents[2]
    try:
        fixture = json.loads(args.fixture.read_text(encoding='utf8'))
        provider = FixtureProvider(fixture['answers'])
        with Session(args.state_root, provider, scope=args.scope) as session:
            report = c01.run(session, fixture['context'], repo)
        receipt = c01.read_selected_method(report, repo) if args.read_selected_method else None
        trace = from_c01(report, receipt)
        validate_with_existing(trace, repo)
        output = {'report': report, 'file_receipt': {k: v for k, v in receipt.items() if k != 'content'}
                  if receipt else None, 'judgment_trace': trace}
        print(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, KeyError, RecoveryRequired) as exc:
        print(json.dumps({'status': 'blocked', 'error_type': type(exc).__name__}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
