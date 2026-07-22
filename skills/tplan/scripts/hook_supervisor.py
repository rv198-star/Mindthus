#!/usr/bin/env python3
"""Run a hook adapter with an inner fail-closed timeout.

The outer platform may treat hook crashes and timeouts as non-blocking. This helper
finishes before the platform timeout and normalizes child startup errors, non-zero
exits, and inner timeouts to exit code 2, which the supported hosts treat as block.
"""

from __future__ import annotations

import argparse
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Supervise a fail-closed hook command.")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("hook supervisor requires a child command", file=sys.stderr)
        return 2
    try:
        completed = subprocess.run(
            command,
            input=sys.stdin.buffer.read(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=args.timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"hook child failed closed: {exc}", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(completed.stdout)
    sys.stderr.buffer.write(completed.stderr)
    return 0 if completed.returncode == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
