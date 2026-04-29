#!/usr/bin/env python3
"""Append a step-local runtime log without promoting it to Mission evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tplan_runtime import TplanError, append_step_log


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a tplan step-local runtime log.")
    parser.add_argument("mission_dir")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--step-id", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--payload-json", default="{}")
    args = parser.parse_args()

    try:
        payload = json.loads(args.payload_json)
        if not isinstance(payload, dict):
            raise ValueError("payload-json must decode to an object")
        event = append_step_log(
            Path(args.mission_dir),
            {
                "step_id": args.step_id,
                "task_id": args.task_id,
                "summary": args.summary,
                "payload": payload,
            },
        )
    except (OSError, TplanError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"recorded_step_log: {event['id']}")
    print("script_result: step log recorded locally; no Mission evidence was created")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
