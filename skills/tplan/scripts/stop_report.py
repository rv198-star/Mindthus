#!/usr/bin/env python3
"""Record a concise Chinese stop report and request human intervention."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tplan_runtime import TplanError, format_stop_report, record_stop_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record a tplan stop report.")
    parser.add_argument("mission_dir")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--current-goal", required=True)
    parser.add_argument("--attempt", action="append", default=[])
    parser.add_argument("--blocking-issue", required=True)
    parser.add_argument("--why-cannot-continue-safely", required=True)
    parser.add_argument("--need-from-human", required=True)
    parser.add_argument("--resume-condition", required=True)
    return parser.parse_args()


def payload(args: argparse.Namespace) -> dict[str, object]:
    return {
        "current_goal": args.current_goal,
        "attempts": args.attempt,
        "blocking_issue": args.blocking_issue,
        "why_cannot_continue_safely": args.why_cannot_continue_safely,
        "need_from_human": args.need_from_human,
        "resume_condition": args.resume_condition,
    }


def main() -> int:
    args = parse_args()
    report_payload = payload(args)
    try:
        event = record_stop_report(Path(args.mission_dir), args.task_id, args.summary, report_payload)
    except (OSError, TplanError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(format_stop_report(report_payload))
    print()
    print(f"recorded_stop_report: {event['id']}")
    print("script_result: Mission requires human intervention; resume when the report condition is satisfied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
