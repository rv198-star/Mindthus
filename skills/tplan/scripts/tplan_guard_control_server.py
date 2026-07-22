#!/usr/bin/env python3
"""Mission-bound MCP control surface for the bounded interaction guard.

The process is deliberately small and has no receipt or unlock operation.  Its
Mission path is fixed when the process starts, so an agent cannot point a safe
control call at a different Mission.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tplan_runtime import (
    TplanError,
    read_interaction_guard,
    read_mission,
    resolve_interaction_guard,
    stop_interaction_guard,
)


TOOLS = (
    {
        "name": "inspect",
        "description": "Read the Mission-bound interaction guard. This never changes Mission state.",
        "inputSchema": {"type": "object", "additionalProperties": False},
    },
    {
        "name": "await_proposal",
        "description": "Keep the guard locked while recording an exact proposal. It cannot apply or unlock it.",
        "inputSchema": {
            "type": "object",
            "required": ["guard_id", "expected_revision", "message_refs"],
            "additionalProperties": False,
            "properties": {
                "guard_id": {"type": "string"},
                "expected_revision": {"type": "integer", "minimum": 1},
                "message_refs": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                "proposal_id": {"type": "string"},
                "proposal_decision": {"type": "object"},
            },
        },
    },
    {
        "name": "stop_fixed",
        "description": "Apply only TPlan's fixed graceful-stop delta; it cannot change the plan.",
        "inputSchema": {
            "type": "object",
            "required": ["guard_id", "expected_revision", "message_refs", "task_id"],
            "additionalProperties": False,
            "properties": {
                "guard_id": {"type": "string"},
                "expected_revision": {"type": "integer", "minimum": 1},
                "message_refs": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                "task_id": {"type": "string"},
            },
        },
    },
)
TOOL_ARGUMENTS = {
    "inspect": set(),
    "await_proposal": {"guard_id", "expected_revision", "message_refs", "proposal_id", "proposal_decision"},
    "stop_fixed": {"guard_id", "expected_revision", "message_refs", "task_id"},
}


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TplanError(f"{label} must be an object")
    return value


def _guard_refs(args: dict[str, Any]) -> list[str]:
    refs = args.get("message_refs")
    if not isinstance(refs, list) or not refs or any(not isinstance(ref, str) for ref in refs):
        raise TplanError("message_refs must be a non-empty list of strings")
    return refs


def _fixed_stop_payload() -> dict[str, Any]:
    return {
        "current_goal": "Preserve the Mission until the user provides the next explicit direction.",
        "attempts": ["Opened an interaction guard.", "Applied the fixed-stop control action."],
        "blocking_issue": "A safe control action requested Mission stop.",
        "why_cannot_continue_safely": "Any other mutation would exceed the fixed-stop boundary.",
        "need_from_human": "Provide the next explicit Mission instruction.",
        "resume_condition": "A new explicit Mission instruction is received.",
    }


def call_tool(mission_dir: Path, name: str, arguments: Any) -> dict[str, Any]:
    """Execute one bounded tool; ``mission_dir`` never comes from tool arguments."""

    args = _require_object(arguments, "tool arguments")
    allowed = TOOL_ARGUMENTS.get(name)
    if allowed is None:
        raise TplanError(f"unsupported guard-control tool: {name}")
    unknown = set(args) - allowed
    if unknown:
        raise TplanError(f"{name} received unsupported arguments: {', '.join(sorted(unknown))}")
    if name == "inspect":
        if args:
            raise TplanError("inspect does not accept arguments")
        return {"guard": read_interaction_guard(mission_dir)}
    guard_id = args.get("guard_id")
    revision = args.get("expected_revision")
    if not isinstance(guard_id, str) or isinstance(revision, bool) or not isinstance(revision, int):
        raise TplanError("guard_id and expected_revision are required")
    refs = _guard_refs(args)
    if name == "await_proposal":
        proposal_id = args.get("proposal_id")
        proposal = args.get("proposal_decision")
        if proposal_id is not None and not isinstance(proposal_id, str):
            raise TplanError("proposal_id must be a string")
        if proposal is not None and not isinstance(proposal, dict):
            raise TplanError("proposal_decision must be an object")
        return resolve_interaction_guard(
            mission_dir,
            guard_id=guard_id,
            expected_revision=revision,
            message_refs=refs,
            disposition="await_clarification",
            proposal_id=proposal_id,
            proposal_decision=proposal,
        )
    if name == "stop_fixed":
        task_id = args.get("task_id")
        if not isinstance(task_id, str):
            raise TplanError("task_id is required")
        return stop_interaction_guard(
            mission_dir,
            guard_id=guard_id,
            expected_revision=revision,
            message_refs=refs,
            task_id=task_id,
            summary="TPlan fixed-stop control action.",
            payload=_fixed_stop_payload(),
        )
    raise AssertionError("bounded guard-control tool dispatch fell through")


def _response(message_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _error(message_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}


def dispatch(mission_dir: Path, request: Any) -> dict[str, Any] | None:
    request = _require_object(request, "MCP request")
    message_id = request.get("id")
    if request.get("jsonrpc") != "2.0":
        return _error(message_id, -32600, "MCP request jsonrpc must be 2.0")
    method = request.get("method")
    if not isinstance(method, str):
        return _error(message_id, -32600, "MCP request method must be a string")
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return _response(
            message_id,
            {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "tplan-guard-control", "version": "0.2"},
                "capabilities": {"tools": {}},
            },
        )
    if method == "tools/list":
        return _response(message_id, {"tools": list(TOOLS)})
    if method == "tools/call":
        params = _require_object(request.get("params"), "tools/call params")
        name = params.get("name")
        if not isinstance(name, str):
            return _error(message_id, -32602, "tools/call name must be a string")
        try:
            result = call_tool(mission_dir, name, params.get("arguments", {}))
        except TplanError as exc:
            return _response(message_id, {"content": [{"type": "text", "text": str(exc)}], "isError": True})
        return _response(
            message_id,
            {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, sort_keys=True)}]},
        )
    return _error(message_id, -32601, f"unsupported MCP method: {method}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Mission-bound TPlan guard MCP control server.")
    parser.add_argument("--mission-dir", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mission_dir = Path(args.mission_dir).resolve()
    try:
        read_mission(mission_dir)
    except (OSError, ValueError, TplanError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = dispatch(mission_dir, request)
            if response is not None:
                print(json.dumps(response, ensure_ascii=False), flush=True)
        except (json.JSONDecodeError, OSError, ValueError, TplanError) as exc:
            print(json.dumps(_error(None, -32600, str(exc)), ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
