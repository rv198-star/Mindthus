#!/usr/bin/env python3
"""Apply a deterministic task status transition."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tplan_runtime import TplanError, read_mission, set_task_status, write_mission


def main() -> int:
    parser = argparse.ArgumentParser(description="Transition a tplan task status.")
    parser.add_argument("mission_dir")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--status", required=True)
    args = parser.parse_args()

    mission_dir = Path(args.mission_dir)
    try:
        mission = read_mission(mission_dir)
        set_task_status(mission, args.task_id, args.status)
        write_mission(mission_dir, mission)
    except (OSError, ValueError, TplanError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"transitioned_task: {args.task_id} -> {args.status}")
    print("script_result: task state changed; semantic judgment remains agentic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
