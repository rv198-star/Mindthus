#!/usr/bin/env python3
"""Explicit Q2 JSON interface for ordinary local observations and recovery."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tplan_commands import CommandError, EXITS, envelope, execute, parse_request


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CommandError("invalid_request", "Expected --mission-dir, --principal and --request-json")


def main() -> int:
    parser = Parser(description=__doc__)
    parser.add_argument("--mission-dir", required=True, type=Path)
    parser.add_argument("--principal", required=True)
    parser.add_argument("--request-json", required=True)
    try:
        args = parser.parse_args()
        request = parse_request(args.request_json)
        result, status = execute(args.mission_dir, request, principal=args.principal)
    except CommandError as exc:
        result = envelope({}, code=exc.code, message=str(exc))
        status = EXITS[exc.code]
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
