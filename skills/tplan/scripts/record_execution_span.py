#!/usr/bin/env python3
"""Record one sanitized model, agent, script, tool, wait, or runtime cost span."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tplan_runtime import TplanError, record_execution_span


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record a tplan execution-cost span.")
    parser.add_argument("mission_dir")
    parser.add_argument("--input", help="JSON object containing the complete span record input.")
    parser.add_argument("--task-id")
    parser.add_argument("--kind", choices=("model", "agent_turn", "script", "tool", "wait", "runtime"))
    parser.add_argument("--label", help="Short sanitized label; never include prompt, output, command args, or secrets.")
    parser.add_argument("--status", choices=("ok", "error", "cancelled", "unknown"), default="ok")
    parser.add_argument(
        "--measurement-source",
        choices=("platform_reported", "host_measured", "inferred", "unavailable"),
    )
    parser.add_argument(
        "--attribution",
        choices=("exact", "shared", "mission_overhead", "unattributed"),
        default="exact",
    )
    parser.add_argument("--started-at")
    parser.add_argument("--finished-at")
    parser.add_argument("--duration-ms", type=int)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--parent-span-id")
    parser.add_argument("--shared-task-id", action="append", default=[])
    parser.add_argument("--input-tokens", type=int)
    parser.add_argument("--cached-input-tokens", type=int)
    parser.add_argument("--output-tokens", type=int)
    parser.add_argument("--reasoning-output-tokens", type=int)
    parser.add_argument(
        "--usage-source",
        choices=("platform_reported", "host_measured", "inferred", "unavailable"),
        help="Token measurement source; defaults to --measurement-source when usage is present.",
    )
    parser.add_argument("--evidence-ref", action="append", default=[])
    parser.add_argument("--artifact-ref", action="append", default=[])
    return parser.parse_args()


def build_raw(args: argparse.Namespace) -> dict[str, object]:
    if args.input:
        return json.loads(Path(args.input).read_text(encoding="utf-8"))

    required = {
        "kind": args.kind,
        "measurement_source": args.measurement_source,
        "started_at": args.started_at,
        "finished_at": args.finished_at,
        "duration_ms": args.duration_ms,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise TplanError("missing span arguments: " + ", ".join(missing))

    span: dict[str, object] = {
        **required,
        "status": args.status,
        "attribution": args.attribution,
        "attempt": args.attempt,
        "parent_span_id": args.parent_span_id,
    }
    if args.label:
        span["label"] = args.label
    if args.shared_task_id:
        span["shared_task_ids"] = args.shared_task_id

    usage = {
        field: value
        for field, value in {
            "input_tokens": args.input_tokens,
            "cached_input_tokens": args.cached_input_tokens,
            "output_tokens": args.output_tokens,
            "reasoning_output_tokens": args.reasoning_output_tokens,
        }.items()
        if value is not None
    }
    raw: dict[str, object] = {
        "task_id": args.task_id,
        "span": span,
        "usage": usage,
        "refs": {
            "evidence_ids": args.evidence_ref,
            "artifact_refs": args.artifact_ref,
        },
    }
    if usage:
        raw["usage_source"] = args.usage_source or args.measurement_source
    return raw


def main() -> int:
    args = parse_args()
    try:
        record = record_execution_span(Path(args.mission_dir), build_raw(args))
    except (json.JSONDecodeError, OSError, TplanError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"recorded_execution_span: {record['span']['span_id']}")
    print("script_result: sanitized observed cost recorded; semantic evidence remains separate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
