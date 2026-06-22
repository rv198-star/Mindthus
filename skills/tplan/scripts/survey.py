#!/usr/bin/env python3
"""Summarize a tplan Mission state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tplan_runtime import build_mission_pulse, build_survey


def main() -> int:
    parser = argparse.ArgumentParser(description="Survey a tplan Mission.")
    parser.add_argument("mission_dir")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--pulse", action="store_true", help="Include a read-only Mission Pulse route note.")
    parser.add_argument(
        "--pulse-trigger",
        default="manual",
        help="Trigger label passed to Mission Pulse when --pulse is set.",
    )
    args = parser.parse_args()

    try:
        mission_dir = Path(args.mission_dir)
        survey = build_survey(mission_dir)
        if args.pulse:
            survey["pulse"] = build_mission_pulse(mission_dir, trigger=args.pulse_trigger)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(survey, ensure_ascii=False, indent=2))
    else:
        print(f"mission: {survey['mission']['id']} {survey['mission']['status']}")
        active = survey["active_task"]["id"] if survey["active_task"] else "none"
        print(f"active_task: {active}")
        print(f"resource_sufficiency: {survey['resource_sufficiency']}")
        shared_context = survey["shared_context"]
        print(
            "active_risk_signals: "
            f"{shared_context['active_risk_signal_count']} "
            f"highest={shared_context['highest_active_severity'] or 'none'}"
        )
        if args.pulse:
            route = survey["pulse"]["mission_pulse"]
            print(f"mission_pulse: next_gate={route['next_gate']} trigger={route['trigger']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
