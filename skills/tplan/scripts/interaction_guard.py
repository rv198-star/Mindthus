#!/usr/bin/env python3
"""Manage a portable TPlan interaction guard.

Hosts call this before handling an interrupting user message and when the response has
one of the legal dispositions. The script validates runtime mechanics only; it does
not classify natural language.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tplan_runtime import (
    TplanError,
    begin_interaction_guard,
    orphan_interaction_guard,
    read_interaction_guard,
    resolve_interaction_guard,
    stop_interaction_guard,
)


def _load_json(path: str) -> dict[str, object]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TplanError(f"{path} must contain a JSON object")
    return value


def _base_resolve(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("mission_dir")
    parser.add_argument("--guard-id", required=True)
    parser.add_argument("--expected-revision", required=True, type=int)
    parser.add_argument("--message-ref", action="append", required=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage a TPlan interaction guard.")
    sub = parser.add_subparsers(dest="command", required=True)

    begin = sub.add_parser("begin", help="Open or extend an interruption guard.")
    begin.add_argument("mission_dir")
    begin.add_argument("--platform", required=True)
    begin.add_argument("--message-ref", required=True)
    begin.add_argument("--binding-id")

    inspect = sub.add_parser("inspect", help="Read the current guard without mutation.")
    inspect.add_argument("mission_dir")

    awaiting = sub.add_parser("await", help="Acknowledge a response and keep the guard locked.")
    _base_resolve(awaiting)
    awaiting.add_argument("--proposal-id")
    awaiting.add_argument("--proposal-decision", help="JSON decision file for the exact proposed mutation.")

    resume = sub.add_parser("resume", help="Resume the original path after a read-only response.")
    _base_resolve(resume)

    stop = sub.add_parser("stop", help="Apply the fixed graceful-stop delta and close the guard.")
    _base_resolve(stop)
    stop.add_argument("--task-id", required=True)
    stop.add_argument("--summary", required=True)
    stop.add_argument("--payload", required=True, help="JSON stop-report payload file.")

    orphan = sub.add_parser("orphan", help="Keep Mission writes locked after lifecycle ambiguity.")
    orphan.add_argument("mission_dir")
    orphan.add_argument("--reason", required=True)
    orphan.add_argument("--guard-id")
    orphan.add_argument("--expected-revision", type=int)

    stop_auto = sub.add_parser("stop-auto", help="Apply the fixed stop delta with a bounded generic report.")
    _base_resolve(stop_auto)
    stop_auto.add_argument("--task-id", required=True)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        mission_dir = Path(args.mission_dir)
        if args.command == "begin":
            result = begin_interaction_guard(
                mission_dir,
                platform=args.platform,
                message_ref=args.message_ref,
                binding_id=args.binding_id,
            )
        elif args.command == "inspect":
            result = read_interaction_guard(mission_dir)
        elif args.command == "await":
            result = resolve_interaction_guard(
                mission_dir,
                guard_id=args.guard_id,
                expected_revision=args.expected_revision,
                message_refs=args.message_ref,
                disposition="await_clarification",
                proposal_id=args.proposal_id,
                proposal_decision=_load_json(args.proposal_decision) if args.proposal_decision else None,
            )
        elif args.command == "resume":
            result = resolve_interaction_guard(
                mission_dir,
                guard_id=args.guard_id,
                expected_revision=args.expected_revision,
                message_refs=args.message_ref,
                disposition="resume_original",
            )
        elif args.command == "orphan":
            result = orphan_interaction_guard(
                mission_dir,
                reason=args.reason,
                guard_id=args.guard_id,
                expected_revision=args.expected_revision,
            )
        elif args.command == "stop-auto":
            result = stop_interaction_guard(
                mission_dir,
                guard_id=args.guard_id,
                expected_revision=args.expected_revision,
                message_refs=args.message_ref,
                task_id=args.task_id,
                summary="TPlan fixed-stop control action.",
                payload={
                    "current_goal": "Preserve the Mission until the user provides the next explicit direction.",
                    "attempts": ["Opened an interaction guard.", "Applied the fixed-stop control action."],
                    "blocking_issue": "A safe control action requested Mission stop.",
                    "why_cannot_continue_safely": "Any other mutation would exceed the fixed-stop boundary.",
                    "need_from_human": "Provide the next explicit Mission instruction.",
                    "resume_condition": "A new explicit Mission instruction is received.",
                },
            )
        else:
            result = stop_interaction_guard(
                mission_dir,
                guard_id=args.guard_id,
                expected_revision=args.expected_revision,
                message_refs=args.message_ref,
                task_id=args.task_id,
                summary=args.summary,
                payload=_load_json(args.payload),
            )
    except (OSError, ValueError, TplanError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
