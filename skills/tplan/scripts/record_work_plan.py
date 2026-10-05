#!/usr/bin/env python3
"""Record optional TPlan planning metadata without changing task or acceptance state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tplan_runtime import TplanError, record_work_plan
from work_plan import load_work_plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mission_dir")
    parser.add_argument("--input", required=True, help="JSON object containing work_plan metadata.")
    parser.add_argument("--summary", default="Work plan metadata updated.")
    parser.add_argument("--json", action="store_true", help="Print the recorded metadata and event.")
    args = parser.parse_args()
    try:
        plan = load_work_plan(Path(args.input))
        result = record_work_plan(Path(args.mission_dir), plan, summary=args.summary)
    except (OSError, ValueError, TplanError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("work_plan: " + ("updated" if result["changed"] else "unchanged"))
        if result["event"] is not None:
            print("planning_metadata_event: " + result["event"]["id"])
        print("script_result: planning metadata recorded; Mission state and acceptance remain authoritative")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
