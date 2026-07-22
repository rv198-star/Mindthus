#!/usr/bin/env python3
"""Codex host adapter for TPlan interaction guards.

This is an event adapter, not a prompt convention. A host must call `message-arrived`
before any later mutable TPlan action, and `response-completed` on every normal, abort,
error, or compaction exit. The current desktop host must wire these commands to claim
mutation prevention; this script alone cannot observe chat messages by itself.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tplan_runtime import (
    TplanError,
    begin_interaction_guard,
    read_interaction_guard,
    resolve_interaction_guard,
    stop_interaction_guard,
)


PLATFORM = "codex"


def _safe_thread_id(value: str) -> str:
    if not value.strip() or "\n" in value or "\r" in value:
        raise TplanError("thread_id must be a non-empty single-line string")
    return value


def _load_json(path: str) -> dict[str, object]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TplanError(f"{path} must contain a JSON object")
    return value


def _resolve_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("mission_dir")
    parser.add_argument("--thread-id", required=True)
    parser.add_argument("--guard-id", required=True)
    parser.add_argument("--expected-revision", required=True, type=int)
    parser.add_argument("--message-ref", action="append", required=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Receive Codex lifecycle events for a TPlan Mission.")
    sub = parser.add_subparsers(dest="command", required=True)

    capabilities = sub.add_parser("capabilities", help="Print the host contract and truthfully scoped guarantees.")
    capabilities.add_argument("--format", choices=("json",), default="json")

    arrived = sub.add_parser("message-arrived", help="Persist guard before handling a user message.")
    arrived.add_argument("mission_dir")
    arrived.add_argument("--thread-id", required=True)
    arrived.add_argument("--message-ref", required=True)

    inspect = sub.add_parser("inspect", help="Read current guard for an explicitly bound Mission.")
    inspect.add_argument("mission_dir")
    inspect.add_argument("--thread-id", required=True)

    awaiting = sub.add_parser("response-awaiting-confirmation", help="Keep the Mission locked after proposing a change.")
    _resolve_args(awaiting)
    awaiting.add_argument("--proposal-id")
    awaiting.add_argument("--proposal-decision", help="JSON decision file for the exact proposed mutation.")

    resume = sub.add_parser("response-resume-original", help="Close only an unchanged read-only interaction.")
    _resolve_args(resume)

    stop = sub.add_parser("response-stop", help="Apply only the fixed graceful-stop delta.")
    _resolve_args(stop)
    stop.add_argument("--task-id", required=True)
    stop.add_argument("--summary", required=True)
    stop.add_argument("--payload", required=True)
    return parser.parse_args()


def _bound_guard(mission_dir: Path, thread_id: str) -> dict[str, object] | None:
    """Validate a host-supplied thread against the sidecar's immutable binding.

    The host remains responsible for resolving the initial thread-to-Mission mapping;
    this adapter merely refuses a later cross-thread completion.
    """

    guard = read_interaction_guard(mission_dir)
    if guard is None:
        return None
    if guard.get("platform") != PLATFORM or guard.get("binding_id") != thread_id:
        raise TplanError("thread_id does not match the Mission interaction guard binding")
    return guard


def main() -> int:
    args = parse_args()
    try:
        if args.command == "capabilities":
            result: object = {
                "adapter": "codex_interaction_adapter.v0.1",
                "enforcement_level_if_host_wired": "tplan_api_mutation_prevention",
                "current_desktop_claim": "advisory_only",
                "host_requirements": [
                    "Call message-arrived before any mutable TPlan action.",
                    "Resolve and protect the initial thread-to-mission binding; never guess mission_dir.",
                    "Call exactly one response completion disposition on normal, abort, error, and compaction exits.",
                    "Issue authority receipts through a host-only signer/IPC capability outside agent-controlled state.",
                    "Invoke apply_authorized_change only inside that trusted host boundary; this CLI does not expose it.",
                    "Sandbox Mission files to supported TPlan runtime writers if filesystem-bypass prevention is required.",
                ],
                "limitations": [
                    "This CLI cannot observe Codex Desktop messages itself.",
                    "thread_id is host context, not an authentication credential.",
                    "Raw filesystem access is outside the TPlan API guarantee.",
                ],
            }
        else:
            thread_id = _safe_thread_id(args.thread_id)
            mission_dir = Path(args.mission_dir)
            if args.command == "message-arrived":
                result = begin_interaction_guard(
                    mission_dir,
                    platform=PLATFORM,
                    message_ref=args.message_ref,
                    binding_id=thread_id,
                )
            elif args.command == "inspect":
                result = _bound_guard(mission_dir, thread_id)
            elif args.command == "response-awaiting-confirmation":
                _bound_guard(mission_dir, thread_id)
                result = resolve_interaction_guard(
                    mission_dir,
                    guard_id=args.guard_id,
                    expected_revision=args.expected_revision,
                    message_refs=args.message_ref,
                    disposition="await_clarification",
                    proposal_id=args.proposal_id,
                    proposal_decision=_load_json(args.proposal_decision) if args.proposal_decision else None,
                )
            elif args.command == "response-resume-original":
                _bound_guard(mission_dir, thread_id)
                result = resolve_interaction_guard(
                    mission_dir,
                    guard_id=args.guard_id,
                    expected_revision=args.expected_revision,
                    message_refs=args.message_ref,
                    disposition="resume_original",
                )
            else:
                _bound_guard(mission_dir, thread_id)
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
