#!/usr/bin/env python3
"""Mark a tplan task blocked after a blocker has been identified."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tplan_runtime import TplanError, transition_task_status


def main() -> int:
    parser = argparse.ArgumentParser(description="Mark a tplan task blocked.")
    parser.add_argument("mission_dir")
    parser.add_argument("--task-id", required=True)
    args = parser.parse_args()

    try:
        transition_task_status(Path(args.mission_dir), args.task_id, "blocked")
    except (OSError, ValueError, TplanError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"block_task: {args.task_id}")
    print("script_result: task marked blocked; blocker interpretation remains agentic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
