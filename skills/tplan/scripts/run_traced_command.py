#!/usr/bin/env python3
"""Run a command and record host-measured elapsed time without storing its arguments or output."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from tplan_runtime import (
    TplanError,
    find_task,
    read_mission,
    record_execution_span,
    start_execution_span,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a command and record a sanitized tplan cost span.")
    parser.add_argument("mission_dir")
    parser.add_argument("--task-id")
    parser.add_argument("--kind", choices=("script", "tool"), default="script")
    parser.add_argument("--label", required=True, help="Short safe operation label, not the command line.")
    parser.add_argument(
        "--attribution",
        choices=("exact", "shared", "mission_overhead", "unattributed"),
        default="exact",
    )
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--parent-span-id")
    parser.add_argument("--shared-task-id", action="append", default=[])
    raw_args = sys.argv[1:]
    try:
        separator = raw_args.index("--")
    except ValueError:
        parser.error("a command is required after --")
    args = parser.parse_args(raw_args[:separator])
    args.command = raw_args[separator + 1 :]
    if not args.command:
        parser.error("a command is required after --")
    return args


def main() -> int:
    args = parse_args()
    command = list(args.command)
    try:
        mission = read_mission(Path(args.mission_dir))
        if args.attribution == "exact":
            if not args.task_id:
                raise TplanError("exact attribution requires --task-id")
            find_task(mission, args.task_id)
        elif args.attribution == "shared":
            if args.task_id:
                raise TplanError("shared attribution uses --shared-task-id and does not accept --task-id")
            if len(set(args.shared_task_id)) < 2:
                raise TplanError("shared attribution requires at least two --shared-task-id values")
            for task_id in args.shared_task_id:
                find_task(mission, task_id)
        elif args.task_id:
            raise TplanError(f"{args.attribution} attribution does not accept --task-id")
    except (OSError, TplanError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    start_span: dict[str, object] = {
        "kind": args.kind,
        "label": args.label,
        "measurement_source": "host_measured",
        "attribution": args.attribution,
        "attempt": args.attempt,
        "parent_span_id": args.parent_span_id,
    }
    if args.shared_task_id:
        start_span["shared_task_ids"] = args.shared_task_id
    try:
        start_record = start_execution_span(
            Path(args.mission_dir),
            {"task_id": args.task_id, "span": start_span},
        )
    except (OSError, TplanError, ValueError) as exc:
        print(f"command was not started because its trace entry could not be recorded: {exc}", file=sys.stderr)
        return 2

    started_at = now_iso()
    started_clock = time.perf_counter_ns()
    try:
        completed = subprocess.run(command, check=False)
        returncode = completed.returncode
        span_status = "ok" if returncode == 0 else "error"
    except OSError as exc:
        returncode = 127
        span_status = "error"
        print(str(exc), file=sys.stderr)
    finished_clock = time.perf_counter_ns()
    finished_at = now_iso()
    duration_ms = max(0, round((finished_clock - started_clock) / 1_000_000))

    span: dict[str, object] = {
        "span_id": start_record["span"]["span_id"],
        "status": span_status,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": duration_ms,
    }
    try:
        record = record_execution_span(
            Path(args.mission_dir),
            {
                "span": span,
                "metadata": {"exit_code": returncode},
            },
        )
        print(
            f"recorded_execution_span: {record['span']['span_id']} "
            f"({args.label}, {duration_ms} ms, exit {returncode})"
        )
    except (OSError, TplanError, ValueError) as exc:
        print(f"command completed but execution span could not be recorded: {exc}", file=sys.stderr)
        return returncode if returncode != 0 else 1
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
