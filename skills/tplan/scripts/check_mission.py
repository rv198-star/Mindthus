#!/usr/bin/env python3
"""Validate a tplan Mission runtime state.

This checks runtime shape and acceptance evidence coverage only. It does not judge
Mission value or semantic correctness.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tplan_runtime import read_mission, validate_mission


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a tplan Mission runtime state.")
    parser.add_argument("--dir", required=True, help="Mission directory containing mission.json.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        errors = validate_mission(read_mission(Path(args.dir)))
    except (OSError, json.JSONDecodeError) as exc:
        errors = [str(exc)]

    if errors:
        print("mission_check: failed")
        for error in errors:
            print(f"- {error}")
        print("script_result: runtime shape issues found; agentic judgment is still required after remediation")
        return 1

    print("mission_check: ok")
    print("script_result: no runtime schema violations detected; agentic judgment is still required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
