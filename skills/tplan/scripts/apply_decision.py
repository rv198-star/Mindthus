#!/usr/bin/env python3
"""Apply or record a tplan decision hook output according to authority."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tplan_runtime import TplanError, apply_decision


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a tplan decision hook output.")
    parser.add_argument("mission_dir")
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()

    try:
        decision = json.loads(Path(args.decision).read_text(encoding="utf-8"))
        result = apply_decision(Path(args.mission_dir), decision)
    except (OSError, ValueError, TplanError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"{result}: {args.decision}")
    print("script_result: authority enforced; semantic correctness remains agentic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
