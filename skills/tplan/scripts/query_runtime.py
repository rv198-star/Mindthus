#!/usr/bin/env python3
"""Versioned, observation-only TPlan queries. No mutation or recovery entrypoint.

The Q1 facade is a read client of the unchanged pinned runtime; its protocol is
not a new Mission writer capability. See docs/implementation/tplan-q1/CONTRACT.md.
"""
from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any

PROTOCOL = "tplan.query.v1"
MAX_REQUEST_BYTES = 16 * 1024
MAX_SOURCE_BYTES = 8 * 1024 * 1024
MAX_RESPONSE_BYTES = 128 * 1024
IDENTITY = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
BUILD = re.compile(r"sha256:[a-f0-9]{64}\Z")
EXITS = {
    "invalid_request": 2, "unsupported_protocol": 2, "unsupported_action": 2,
    "unsupported_capability": 3, "recovery_required": 4,
    "runtime_mismatch": 5, "mission_unavailable": 6, "invalid_state": 7,
    "runtime_unavailable": 8, "query_failed": 9, "snapshot_too_large": 10, "command_not_found": 11,
}


class QueryError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise QueryError("invalid_request", "Duplicate JSON keys are not supported")
        value[key] = item
    return value


def _constant(_value: str) -> None:
    raise QueryError("invalid_request", "Non-finite JSON constants are not supported")


def parse_request(raw: str) -> dict[str, Any]:
    if len(raw.encode("utf-8")) > MAX_REQUEST_BYTES:
        raise QueryError("invalid_request", "Request exceeds the 16 KiB limit")
    try:
        value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, RecursionError) as exc:
        raise QueryError("invalid_request", "Request is not a valid JSON object") from exc
    validate_request(value)
    return value


def validate_request(value: Any) -> None:
    if not isinstance(value, dict):
        raise QueryError("invalid_request", "Request must be a JSON object")
    required = {"protocol", "action", "request_id", "mission_id"}
    allowed = required | {"expected_build_hash", "command_id"}
    if not required.issubset(value) or set(value) - allowed:
        raise QueryError("invalid_request", "Missing or unsupported request fields")
    if value["protocol"] != PROTOCOL:
        raise QueryError("unsupported_protocol", "Select tplan.query.v1 explicitly")
    if value["action"] not in ("snapshot.get", "command.get"):
        raise QueryError("unsupported_action", "Q1 only supports read query actions")
    for name in ("request_id", "mission_id"):
        if not isinstance(value[name], str) or not IDENTITY.fullmatch(value[name]):
            raise QueryError("invalid_request", f"Invalid {name}")
    if "expected_build_hash" in value:
        if not isinstance(value["expected_build_hash"], str) or not BUILD.fullmatch(value["expected_build_hash"]):
            raise QueryError("invalid_request", "Invalid expected_build_hash")
    if value["action"] == "command.get":
        if not isinstance(value.get("command_id"), str) or not IDENTITY.fullmatch(value["command_id"]):
            raise QueryError("invalid_request", "command.get requires a valid command_id")
    elif "command_id" in value:
        raise QueryError("invalid_request", "command_id is only valid for command.get")


def _envelope(request: dict[str, Any], *, code: str | None = None,
              message: str = "Read-only snapshot; not an execution authorization",
              data: Any = None) -> dict[str, Any]:
    return {"protocol": PROTOCOL, "request_id": request.get("request_id"),
            "action": request.get("action"), "mission_id": request.get("mission_id"),
            "ok": code is None,
            "status": "read" if code is None else ("recovery_required" if code == "recovery_required" else "rejected"),
            "code": code, "message": message, "data": data}


def _runtime():
    # -I ignores environment import paths; explicitly select this package only.
    script_root = str(Path(__file__).resolve().parent)
    if script_root not in sys.path:
        sys.path.insert(0, script_root)
    try:
        return importlib.import_module("tplan_runtime")
    except (ImportError, OSError, RuntimeError) as exc:
        raise QueryError("runtime_unavailable", "The selected runtime package is incomplete") from exc


def _mission_dir(value: Path) -> Path:
    if value.is_symlink() or not value.is_dir():
        raise QueryError("mission_unavailable", "Select an existing non-symlink Mission directory")
    directory = value.resolve(strict=True)
    for name in ("mission.json", "evidence.jsonl", "execution_trace.jsonl",
                 ".interaction-guard.json", ".mission-transaction.json", ".execution_trace.lock"):
        path = directory / name
        if path.is_symlink():
            raise QueryError("mission_unavailable", "Mission state must not follow symlinks")
        if path.exists():
            if not path.is_file():
                raise QueryError("mission_unavailable", "Mission state is not a regular file")
            if path.stat().st_size > MAX_SOURCE_BYTES:
                raise QueryError("snapshot_too_large", "A source file exceeds the query limit")
    if not (directory / "mission.json").is_file():
        raise QueryError("mission_unavailable", "Mission state is not available")
    return directory


def _snapshot(directory: Path, request: dict[str, Any]) -> dict[str, Any]:
    runtime = _runtime()
    try:
        current = runtime.runtime_fingerprint()
    except (runtime.TplanError, OSError, ValueError, TypeError) as exc:
        raise QueryError("runtime_unavailable", "The selected runtime fingerprint is unavailable") from exc
    if request.get("expected_build_hash", current["build_hash"]) != current["build_hash"]:
        raise QueryError("runtime_mismatch", "Selected runtime differs from the Host-pinned build")
    try:
        # Reuse the pinned runtime's no-recovery primitives under one lock.
        # Size/type checks must follow a writer that held the lock before us.
        with runtime.execution_trace_lock(directory):
            _mission_dir(directory)
            runtime._require_no_pending_mission_transaction_unlocked(directory, "querying a snapshot")
            mission = runtime._read_mission_unlocked(directory)
            events = runtime._read_events_unlocked(directory)
            trace = runtime._read_execution_trace_unlocked(directory)
            guard = runtime._interaction_guard_boundary_state_unlocked(directory)
            snapshot = {"mission": mission, "events": events, "trace": trace,
                        "interaction_guard_state": guard,
                        "mission_digest": runtime.mission_control_digest(mission),
                        "evidence_digest": runtime._evidence_boundary_digest_unlocked(directory),
                        "interaction_guard_digest": runtime._sha256_digest(guard)}
        errors = runtime.validate_mission(mission)
        if errors:
            raise QueryError("invalid_state", "Canonical Mission structure is invalid")
        if any(runtime.validate_evidence_event(mission, event, compatibility=True, internal=True)
               for event in events):
            raise QueryError("invalid_state", "Canonical evidence structure is invalid")
        if any(runtime.validate_execution_trace_record(mission, record) for record in trace):
            raise QueryError("invalid_state", "Canonical execution trace structure is invalid")
        if mission["mission"]["id"] != request["mission_id"]:
            raise QueryError("invalid_state", "Mission identity does not match the query")
        provenance = runtime.runtime_provenance_report(mission, current=current)
        if provenance["compatible"] is False:
            raise QueryError("runtime_mismatch", "Mission requires its original matching runtime")
        store = mission.get("command_results")
        if request["action"] == "command.get":
            if store is None:
                raise QueryError("unsupported_capability", "This Mission has no persistent result capability; absence does not prove non-execution")
            result = store["records"].get(request["command_id"])
            if result is None:
                raise QueryError("command_not_found", "No local recorded result; do not infer external non-execution")
            matching = [event for event in events if event["id"] == result["evidence_id"]]
            from tplan_commands import digest as command_digest
            if len(matching) != 1 or matching[0]["event_type"] != "observation" or command_digest(matching[0]) != result["evidence_digest"]:
                raise QueryError("invalid_state", "Command result has no matching observation")
            return {"schema": "tplan.command_result.v1", "authority": "historical_result_only",
                    "command_id": request["command_id"], "runtime_build_hash": current["build_hash"], "result": result}
        data = {
            "schema": "tplan.snapshot.v1", "authority": "observation_only",
            "mission": {key: mission["mission"][key] for key in ("id", "title", "status")},
            "focus_task_id": mission.get("active_task_id"),
            "tasks": [{key: task.get(key) for key in
                       ("id", "title", "status", "role", "acceptance_evidence")} for task in mission["tasks"]],
            "work_plan": mission.get("work_plan"),
            "evidence_count": len(snapshot["events"]), "trace_count": len(snapshot["trace"]),
            "interaction_guard": snapshot["interaction_guard_state"],
            "revision": {"mission": snapshot["mission_digest"],
                         "evidence": snapshot["evidence_digest"],
                         "guard": snapshot["interaction_guard_digest"]},
            "runtime": {**{key: current[key] for key in
                          ("package_version", "source_id", "build_hash", "capability_versions", "capabilities")},
                        "compatibility": provenance["status"], "compatible": provenance["compatible"],
                        "origin": provenance["origin"]},
            "query_capabilities": ["snapshot.get", "command.get"] if store is not None else ["snapshot.get"],
            "command_result_store": store is not None,
        }
        if "human_control" in mission:
            from tplan_h1 import completion_findings
            hc = mission["human_control"]
            data["human_control"] = {
                "authority": "observation_only", "owner_host_integration": "disabled_pending_isolation",
                "requests": {key: {field: req[field] for field in
                    ("business_task_id", "blocked_task_ids", "status", "revision", "current_candidate_id", "fallback_candidate_id", "current_decision_id")}
                    for key, req in hc["requests"].items()},
                "adoptions": hc["adoptions"], "execution_slots": hc["execution_slots"],
                "completion_blockers": completion_findings(mission),
            }
    except runtime.TplanError as exc:
        if str(exc).startswith("pending Mission transaction must be recovered"):
            raise QueryError("recovery_required", "Recover with the original writer; this query made no recovery changes") from exc
        raise QueryError("invalid_state", "Canonical state or guard is invalid") from exc
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise QueryError("invalid_state", "Canonical state cannot be represented safely") from exc
    return data


def query(mission_dir: Path, request: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """Observe a trusted local Mission; only the runtime lock metadata may change."""
    try:
        validate_request(request)
        directory = _mission_dir(mission_dir)
        result = _envelope(request, data=_snapshot(directory, request))
        if len(json.dumps(result, ensure_ascii=False, allow_nan=False).encode("utf-8")) > MAX_RESPONSE_BYTES:
            raise QueryError("snapshot_too_large", "Snapshot exceeds the 128 KiB response limit")
        return result, 0
    except QueryError as exc:
        return _envelope(request if isinstance(request, dict) else {}, code=exc.code, message=str(exc)), EXITS[exc.code]
    except OSError:
        return _envelope(request, code="mission_unavailable", message="Mission files are unavailable"), 6
    except Exception:
        # Do not leak paths, evidence text or tracebacks into a Host response.
        return _envelope(request, code="query_failed", message="Read query could not complete"), 9


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise QueryError("invalid_request", "Expected --mission-dir and --request-json")


def main() -> int:
    parser = Parser(description=__doc__)
    parser.add_argument("--mission-dir", required=True, type=Path)
    parser.add_argument("--request-json", required=True)
    try:
        args = parser.parse_args()
        request = parse_request(args.request_json)
        result, status = query(args.mission_dir, request)
    except QueryError as exc:
        result, status = _envelope({}, code=exc.code, message=str(exc)), EXITS[exc.code]
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, separators=(",", ":")))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
