#!/usr/bin/env python3
"""Validate a tplan Mission runtime state.

This checks runtime shape and acceptance evidence coverage only. It does not judge
Mission value or semantic correctness.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tplan_runtime import (
    TplanError,
    read_execution_trace,
    read_mission,
    validate_execution_trace,
    validate_mission,
    validate_mission_directory_identity,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a tplan Mission runtime state.")
    parser.add_argument("mission_dir", help="Mission directory containing mission.json.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mission_dir = Path(args.mission_dir)
    try:
        mission = read_mission(mission_dir)
        errors = validate_mission(mission)
        errors.extend(validate_mission_directory_identity(mission, mission_dir))
        errors.extend(validate_execution_trace(mission, read_execution_trace(mission_dir)))
    except (OSError, json.JSONDecodeError, TplanError) as exc:
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
