#!/usr/bin/env python3
"""Build a read-only Mission Health Pulse route note."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tplan_runtime import build_mission_pulse


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a read-only tplan Mission Pulse.")
    parser.add_argument("mission_dir")
    parser.add_argument("--trigger", default="manual")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    try:
        pulse = build_mission_pulse(Path(args.mission_dir), trigger=args.trigger)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(pulse, ensure_ascii=False, indent=2))
    else:
        route = pulse["mission_pulse"]
        print(f"mission_pulse: next_gate={route['next_gate']} trigger={route['trigger']}")
        print(f"script_verdict: {pulse['script_verdict']}")
        print("script_result: pulse routed; semantic judgment remains with the selected Gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
