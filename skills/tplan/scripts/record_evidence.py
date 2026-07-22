#!/usr/bin/env python3
"""Append evidence to a tplan Mission JSONL stream.

Routine step-by-step process records belong in record_step_log.py.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tplan_runtime import TplanError, append_event


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a tplan evidence event.")
    parser.add_argument("mission_dir")
    parser.add_argument("--event-type", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--task-id")
    parser.add_argument("--payload-json", default="{}")
    args = parser.parse_args()

    try:
        payload = json.loads(args.payload_json)
        if not isinstance(payload, dict):
            raise ValueError("payload-json must decode to an object")
        event = append_event(
            Path(args.mission_dir),
            {
                "event_type": args.event_type,
                "summary": args.summary,
                "task_id": args.task_id,
                "payload": payload,
            },
        )
    except (OSError, TplanError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"recorded_evidence: {event['id']}")
    print("script_result: evidence recorded; semantic interpretation remains agentic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
