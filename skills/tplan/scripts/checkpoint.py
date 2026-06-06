#!/usr/bin/env python3
"""Record a compact tplan checkpoint.

A checkpoint can combine a task-local log, optional sparse evidence, and a survey in
one call. It records state only; semantic interpretation remains agentic.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tplan_runtime import (
    TplanError,
    append_event,
    append_step_log,
    build_survey,
    find_task,
    read_mission,
    validate_mission,
)


def parse_object(raw: str, name: str) -> dict[str, Any]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{name} must decode to an object")
    return value


def validate_checkpoint_args(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    log_payload = parse_object(args.log_payload_json, "log-payload-json")
    evidence_payload = parse_object(args.evidence_payload_json, "evidence-payload-json")

    if args.log_summary and not args.task_id:
        raise TplanError("task-id is required when log-summary is provided")
    if args.evidence_type and not args.evidence_summary:
        raise TplanError("evidence summary is required when evidence-type is provided")
    if args.evidence_summary and not args.evidence_type:
        raise TplanError("evidence type is required when evidence-summary is provided")
    return log_payload, evidence_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a compact tplan checkpoint.")
    parser.add_argument("mission_dir")
    parser.add_argument("--task-id")
    parser.add_argument("--step-id", default="checkpoint")
    parser.add_argument("--log-summary")
    parser.add_argument("--log-payload-json", default="{}")
    parser.add_argument("--evidence-type")
    parser.add_argument("--evidence-summary")
    parser.add_argument("--evidence-task-id")
    parser.add_argument("--evidence-payload-json", default="{}")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    try:
        mission_dir = Path(args.mission_dir)
        log_payload, evidence_payload = validate_checkpoint_args(args)
        mission = read_mission(mission_dir)
        errors = validate_mission(mission)
        if errors:
            raise TplanError("; ".join(errors))

        if args.task_id:
            find_task(mission, args.task_id)
        evidence_task_id = args.evidence_task_id or args.task_id
        if evidence_task_id:
            find_task(mission, evidence_task_id)

        recorded_log = None
        if args.log_summary:
            recorded_log = append_step_log(
                mission_dir,
                {
                    "step_id": args.step_id,
                    "task_id": args.task_id,
                    "summary": args.log_summary,
                    "payload": log_payload,
                },
            )

        recorded_evidence = None
        if args.evidence_type:
            recorded_evidence = append_event(
                mission_dir,
                {
                    "event_type": args.evidence_type,
                    "summary": args.evidence_summary,
                    "task_id": evidence_task_id,
                    "payload": evidence_payload,
                },
            )

        result = {
            "recorded_log": recorded_log,
            "recorded_evidence": recorded_evidence,
            "survey": build_survey(mission_dir),
        }
    except (OSError, TplanError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if recorded_log:
            print(f"checkpoint_log: {recorded_log['id']}")
        if recorded_evidence:
            print(f"checkpoint_evidence: {recorded_evidence['id']}")
        active = result["survey"]["active_task"]["id"] if result["survey"]["active_task"] else "none"
        print(
            "checkpoint_survey: "
            f"mission={result['survey']['mission']['id']} "
            f"status={result['survey']['mission']['status']} "
            f"active_task={active} "
            f"events={result['survey']['event_count']}"
        )
        print("script_result: checkpoint recorded; semantic interpretation remains agentic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
