#!/usr/bin/env python3
"""Initialize a tplan Mission directory.

This creates runtime files only. It does not judge Mission quality.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tplan_runtime import (
    TplanError,
    build_mission,
    load_task_json,
    mission_paths,
    parse_acceptance_evidence,
    render_mission_md,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize a tplan Mission directory.")
    parser.add_argument("--dir", required=True, help="Mission directory to create.")
    parser.add_argument("--mission-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--objective", required=True)
    parser.add_argument(
        "--acceptance-evidence",
        action="append",
        default=[],
        help="Acceptance evidence as ID:description. Repeat for multiple items.",
    )
    parser.add_argument("--task-json", help="JSON file containing initial Plan Tasks.")
    parser.add_argument("--human-in-loop", type=int, default=0)
    parser.add_argument("--risk-tolerance", type=int, default=50)
    parser.add_argument("--resource-sufficiency", type=int, default=50)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        mission_dir = Path(args.dir)
        paths = mission_paths(mission_dir)
        paths["dir"].mkdir(parents=True, exist_ok=True)
        paths["archive"].mkdir(parents=True, exist_ok=True)

        mission = build_mission(
            mission_id=args.mission_id,
            title=args.title,
            objective=args.objective,
            acceptance_evidence=parse_acceptance_evidence(args.acceptance_evidence),
            human_in_loop=args.human_in_loop,
            risk_tolerance=args.risk_tolerance,
            resource_sufficiency=args.resource_sufficiency,
            tasks=load_task_json(Path(args.task_json) if args.task_json else None),
        )
        write_json(paths["mission"], mission)
        paths["narrative"].write_text(render_mission_md(mission), encoding="utf-8")
        paths["evidence"].write_text("", encoding="utf-8")
        print(f"initialized_mission: {mission_dir}")
        print("script_result: runtime files created; agentic Mission judgment is still required")
        return 0
    except (KeyError, OSError, TplanError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
