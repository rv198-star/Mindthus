#!/usr/bin/env python3
"""Set the active tplan task after semantic selection has already been made."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tplan_runtime import TplanError, transition_task_status


def main() -> int:
    parser = argparse.ArgumentParser(description="Set a tplan task active.")
    parser.add_argument("mission_dir")
    parser.add_argument("--task-id", required=True)
    args = parser.parse_args()

    try:
        transition_task_status(Path(args.mission_dir), args.task_id, "active")
    except (OSError, ValueError, TplanError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"set_active_task: {args.task_id}")
    print("script_result: active task changed; semantic selection remains agentic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
