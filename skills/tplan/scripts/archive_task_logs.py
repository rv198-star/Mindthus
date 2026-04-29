#!/usr/bin/env python3
"""Archive step-local runtime logs and write a compressed node summary."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tplan_runtime import TplanError, archive_task_logs


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive tplan step-local runtime logs.")
    parser.add_argument("mission_dir")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()

    try:
        archive_task_logs(Path(args.mission_dir), args.task_id, args.summary)
    except (OSError, TplanError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"archived_task_logs: {args.task_id}")
    print("script_result: step logs archived; promote only the summary or key findings as evidence if needed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
